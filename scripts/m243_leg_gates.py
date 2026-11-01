#!/usr/bin/env python3
"""M243: which 7 of FUN_00596850's 30 write legs are dead on a save, and BY WHICH GATE.

Static: build the codec's CFG from the objdump dump (scratch/m574/text.txt), forward-interpret it
under the LIVE save state (every guard operand that is a global is read from /proc/<pid>/mem), and
report the legs the state makes unreachable.  Cross-checked against two committed box logs:
evidence/m242_b.gdblog (a save: 23 of 30 write sites hit) and evidence/m109c4.log (a load: 21 of
the 28 armed read sites hit).  The model must explain the dead set AND must not prune any leg the
box measured hot (trap 8: a PASS on a non-discriminating shape is no PASS).

    sudo -n python3 scripts/m243_leg_gates.py            # accept
    sudo -n python3 scripts/m243_leg_gates.py --dump     # also print the CFG verdict per leg
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
LO, HI = 0x596850, 0x597a0d
TAB = chr(9)
WSITES = [0x596883, 0x596927, 0x596976, 0x5969CB, 0x596A03, 0x596A8A, 0x596AF5, 0x596ECF, 0x596F1E,
          0x597026, 0x59707D, 0x5970DD, 0x59713A, 0x5971A5, 0x597203, 0x59728D, 0x597312, 0x597384,
          0x597518, 0x59762F, 0x597697, 0x59770F, 0x59777A, 0x5977D6, 0x59782D, 0x59788B, 0x5978E8,
          0x597948, 0x5979BA, 0x5979DC]
RSITES = [0x59688A, 0x59692E, 0x59697D, 0x5969D2, 0x596A33, 0x596A91, 0x596AFC, 0x596ED6, 0x596F25,
          0x59702D, 0x597084, 0x5970E4, 0x597141, 0x5971AC, 0x59720A, 0x597294, 0x597319, 0x59738B,
          0x59751F, 0x597636, 0x59769E, 0x597716, 0x597781, 0x5977DD, 0x597834, 0x597892, 0x5978EF,
          0x59794F]

JMPISH = ("jmp", "je", "jne", "jz", "jnz", "ja", "jae", "jb", "jbe", "jg", "jge", "jl", "jle", "jo",
          "jno", "jc", "jnc", "jp", "js", "jns")
TAKEN = {"je": lambda a, b: a == b, "jz": lambda a, b: a == b, "jne": lambda a, b: a != b,
         "jnz": lambda a, b: a != b, "ja": lambda a, b: a > b, "jae": lambda a, b: a >= b,
         "jb": lambda a, b: a < b, "jbe": lambda a, b: a <= b, "jg": lambda a, b: s(a) > s(b),
         "jge": lambda a, b: s(a) >= s(b), "jl": lambda a, b: s(a) < s(b),
         "jle": lambda a, b: s(a) <= s(b)}


def s(v):                                   # 32-bit signed view
    return v - 0x100000000 if v >= 0x80000000 else v


def insns():
    out = []
    for line in open(TEXT, errors="replace"):
        p = line.split(TAB)
        if len(p) < 3:
            continue
        head = p[0].strip()
        if not head.endswith(":"):
            continue
        a = int(head[:-1], 16)
        if a > HI:
            break
        if a < LO:
            continue
        f2 = p[2].strip().split(None, 1)
        out.append((a, f2[0].lower() if f2 else "", f2[1].strip() if len(f2) > 1 else ""))
    return out


def build(I):
    """Basic blocks: addr -> (first, last, successors, jcc-name-or-None).  Successors are
    (fallthrough, taken) for a jcc, (target,) for a jmp, () for a ret."""
    idx = {a: i for i, (a, _, _) in enumerate(I)}
    lead = {I[0][0]}
    for i, (a, mn, ops) in enumerate(I):
        if mn in JMPISH or mn == "ret":
            t = ops.split()[0] if ops.split() else ""
            try:
                ta = int(t.replace("0x", ""), 16)
            except ValueError:
                ta = None
            if ta is not None and LO <= ta <= HI and ta not in idx:
                ta = None
            if ta is not None:
                lead.add(ta)
            if i + 1 < len(I):
                lead.add(I[i + 1][0])
    order = sorted(lead)
    blocks = []
    for bi, start in enumerate(order):
        end = order[bi + 1] if bi + 1 < len(order) else HI + 1
        ins = [I[i] for i in range(idx[start], idx[end])]
        a, mn, ops = ins[-1]
        succ = ()
        if mn == "jmp":
            t = int(ops.split()[0].replace("0x", ""), 16)
            succ = (t,)
        elif mn in TAKEN:
            t = int(ops.split()[0].replace("0x", ""), 16)
            succ = (ins[-2][0] + 0 if False else end, t)     # (fallthrough, taken)
        elif mn == "ret":
            succ = ()
        else:
            succ = (end,) if end <= HI else ()
        blocks.append((start, a, succ, mn if mn in TAKEN else None))
    return {b[0]: b for b in blocks}, idx


class Live:
    def __init__(self, pid):
        self.fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
        self.c = {}

    def dword(self, a):
        if a not in self.c:
            self.c[a] = int.from_bytes(os.pread(self.fd, 4, a), "little")
        return self.c[a]


def norm(op):
    for pre in ("dword ptr ", "word ptr ", "byte ptr "):
        if op.startswith(pre):
            return op[len(pre):].strip()
    return op.strip()


def resolve(op, I, M, i, depth=0):
    """Value of an operand at instruction index i, or None.  Conservative: any call / branch /
    unresolvable arithmetic upstream makes it unknown."""
    op = norm(op.lower())
    if op.startswith("ds:0x"):
        return M.dword(int(op[3:], 16))
    if op.startswith("0x"):
        return int(op, 16)
    if op.isdigit() or (op[0] == "-" and op[1:].isdigit()):
        return int(op) & 0xffffffff
    if depth > 6 or op not in ("eax", "ebx", "ecx", "edx", "esi", "edi"):
        return None
    j = i
    while j >= 0:
        a, mn, ops = I[j]
        o = ops.split(",")
        if mn == "call" or mn in JMPISH or mn == "ret":
            return None
        if mn == "xor" and len(o) == 2 and norm(o[0]) == op and norm(o[1]) == op:
            return 0
        if mn == "mov" and len(o) == 2 and norm(o[0]) == op:
            return resolve(o[1].strip(), I, M, j, depth + 1)
        if mn == "movzx" and len(o) == 2 and norm(o[0]) == op and "ds:0x" in o[1]:
            return M.dword(int(o[1].split("ds:0x")[1].split("]")[0], 16)) & 0xff
        if mn in ("lea", "add", "sub", "and", "or", "shl", "shr", "imul", "inc", "dec", "movsx",
                  "sbb", "adc", "neg", "not") and len(o) >= 1 and norm(o[0]) == op:
            return None
        j -= 1
    return None


def decide(baddr, mn, I, idx, M):
    """(taken, text) for the jcc at baddr, searching back for the cmp/test that sets its flags.
    Any flag-modifying instruction or call between it and the jcc makes the guard unknown."""
    FLAGMOD = ("add", "sub", "and", "or", "xor", "inc", "dec", "shl", "shr", "neg", "adc", "sbb",
               "sar", "not", "rol", "ror")
    back = idx[baddr] - 1
    while back >= 0 and I[back][0] >= (baddr - 0x40):
        a, m2, ops = I[back]
        o = ops.split(",")
        if m2 == "call":
            return None, "flags set by a call at 0x%x" % a
        if m2 in FLAGMOD:
            return None, "flags modified by %s at 0x%x" % (m2, a)
        if m2 in ("cmp", "test") and len(o) == 2:
            lhs, rhs = resolve(o[0], I, M, back), resolve(o[1], I, M, back)
            txt = "%s %s, %s" % (m2, norm(o[0].lower()), norm(o[1].lower()))
            if lhs is None or rhs is None:
                return None, txt + " [unresolved]"
            if m2 == "test":
                return (bool(lhs & rhs)), "%s  0x%x & 0x%x" % (txt, lhs, rhs)
            return TAKEN[mn](lhs, rhs), "%s  0x%x vs 0x%x" % (txt, lhs, rhs)
        back -= 1
    return None, "no guard in window"


def run(blocks, entry, I, idx, M, force=()):
    reach, pruned = {entry}, []
    stack = [entry]
    while stack:
        b = stack.pop()
        blk = blocks.get(b)
        if not blk:
            continue
        _, a, succ, mn = blk
        if mn:
            taken, txt = decide(a, mn, I, idx, M)
            nxt = succ if (taken is None or a in force) else ((succ[1],) if taken else (succ[0],))
            if taken is not None and a not in force:
                for d in succ:
                    if d not in nxt:
                        pruned.append((a, txt, d))
        else:
            nxt = succ
        for t in nxt:
            if t in blocks and t not in reach:
                reach.add(t)
                stack.append(t)
    return reach, pruned


def blockof(blocks, addr):
    got = None
    for b in blocks:
        if b <= addr and (got is None or b > got):
            got = b
    return got


def args_at(I, idx, site):
    """The pushes before a wrapper call, in ARG order: [dest, size, count, handle]."""
    i, got = idx[site], []
    while i >= 0 and len(got) < 4:
        a, mn, ops = I[i]
        if mn == "push":
            got.append(ops)
        elif mn == "call":
            break
        i -= 1
    return got


def logs():
    """hotW: write sites that hit on the M242 save (with dst/sz/n); hotR: read sites the M109c4
    load executed; plus both file sizes.  All from committed evidence, no box time."""
    hotW, save_sz = [], None
    for l in open(os.path.join(ROOT, "evidence/m242_b.gdblog"), errors="replace"):
        p = l.split()
        if len(p) >= 6 and p[0] == "W":
            hotW.append((int(p[1], 16), {k: (int(v, 16) if k == "dst" else int(v))
                                         for k, v in (x.split("=") for x in p[2:])}))
    for l in open(os.path.join(ROOT, "evidence/m242_save_write.txt"), errors="replace"):
        if "B file" in l and "m242_probe_B" in l:
            save_sz = int(next(t for t in l.split() if t.isdigit()))
    hotR, load_sz, load_sum = [], None, 0
    for l in open(os.path.join(ROOT, "evidence/m109c4.log"), errors="replace"):
        if l.startswith("  site="):
            d = {k: (int(v, 16) if k == "site" or v.startswith("0x") else int(v))
                 for k, v in (x.split("=") for x in l.split()[1:])}
            hotR.append(d)
            load_sum += d["size"] * d["cnt"]
        elif "vs file" in l:
            load_sz = int(l.split("vs file")[1].split()[0].replace(",", ""))
    return hotW, hotR, save_sz, load_sz, load_sum


def main():
    pid = int(subprocess.check_output(["pgrep", "-x", "terran.exe"]).split()[0])
    M, I = Live(pid), insns()
    blocks, idx = build(I)
    hotW, hotR, save_sz, load_sz, load_sum = logs()
    gates = []

    def gr(ok, name, detail):
        gates.append((ok, name))
        print("%s %s  %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)

    print("codec 0x%x-0x%x: %d insns, %d blocks; live mode ds:0x926a0c=%d swap ds:0x926a14=%d "
          "ds:0x985dbc=%d ds:0x985af0=%d ds:0x985af4=%d" %
          (LO, HI, len(I), len(blocks), M.dword(0x926A0C), M.dword(0x926A14), M.dword(0x985DBC),
           M.dword(0x985AF0), M.dword(0x985AF4)), flush=True)
    hs = set(h for h, _ in hotW)
    deadW = [x for x in WSITES if x not in hs]
    hr = set(d["site"] for d in hotR)
    deadR = [x for x in RSITES if x not in hr]
    deadset_from_read = set(RSITES[i] for i in range(28) if WSITES[i] in deadW)
    print("logs: save hot %d/%d write sites (file %s B); load hot %d read sites sum %d (file %s B)"
          % (len(hs), len(WSITES), save_sz, len(hotR), load_sum, load_sz), flush=True)
    gr(len(deadW) == 7 and set(deadR) == deadset_from_read,
       "G1 the two box logs agree on the SAME 7 legs (write sites and their read twins)",
       "dead W %s | dead R %s" % (" ".join("%x" % x for x in deadW), " ".join("%x" % x for x in deadR)))
    reach, pruned = run(blocks, LO, I, idx, M)
    mdead = [x for x in WSITES if blockof(blocks, x) not in reach]
    gr(mdead == deadW, "G2 the CFG read under the LIVE state makes exactly those 7 unreachable and "
       "reaches all 23 the box measured hot",
       "model dead %s ; pruned edges %d" % (" ".join("%x" % x for x in mdead), len(pruned)))
    perleg = {}
    for site in mdead:
        need = []
        for (a, txt, d) in pruned:
            r2, _ = run(blocks, LO, I, idx, M, force=(a,))
            if blockof(blocks, site) in r2:
                need.append((a, txt))
        perleg[site] = need
        print("  DEAD 0x%x args %s gates %s" % (site, " ".join(args_at(I, idx, site)),
              "; ".join("0x%x %s" % (a, t) for a, t in need) or "NONE"), flush=True)
    gr(all(perleg[s] for s in mdead) and len(mdead) == 7,
       "G3 every dead leg has a NAMED gate: a real branch whose guard is false in the live state",
       "legs with >=1 gate %d/7" % sum(1 for s in mdead if perleg[s]))
    tail_s = save_sz - sum(v["sz"] * v["n"] for _, v in hotW)
    gr(tail_s == load_sz - load_sum == 93159,
       "G4 the arithmetic closes both ways: what the codec does NOT move is 93,159 B on a save AND "
       "on a load, so the dead legs are not hidden bytes",
       "save %d-%d=%d ; load %d-%d=%d" % (save_sz, sum(v["sz"] * v["n"] for _, v in hotW), tail_s,
                                          load_sz, load_sum, load_sz - load_sum))
    n = sum(1 for ok, _ in gates if ok)
    print("SUMMARY %s M243: %d/%d gates" % ("PASS" if n == len(gates) else "FAIL", n, len(gates)),
          flush=True)
    return 0 if n == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
