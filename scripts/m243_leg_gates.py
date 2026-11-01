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
LO, HI = 0x596850, 0x597a6b          # FUN_00596850 is 4,637 B: 0x596850 + 0x121d
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
    lead = {a for a in lead if a in idx}
    order = sorted(lead)
    blocks = []
    for bi, start in enumerate(order):
        end = order[bi + 1] if bi + 1 < len(order) else None
        ins = I[idx[start]:(idx[end] if end in idx else len(I))]
        a, mn, ops = ins[-1]
        try:
            t = int(ops.split()[0].replace("0x", ""), 16) if ops.split() else None
        except ValueError:
            t = None                                   # indirect jmp/jcc: target unknown
        succ = ()
        if mn == "jmp":
            succ = (t,)
        elif mn in TAKEN:
            succ = ((end, t) if end in idx else (t,))      # (fallthrough, taken)
        elif mn != "ret":
            succ = ((end,) if end in idx else ())
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
    j = i - 1                                          # an instruction USES its own operands
    while j >= 0:
        a, mn, ops = I[j]
        o = ops.split(",")
        if mn == "call":
            if op in ("ebx", "esi", "edi", "ebp"):
                j -= 1
                continue                               # cdecl: these survive a call
            return None
        if mn in JMPISH or mn == "ret":
            return None
        if mn == "xor" and len(o) == 2 and norm(o[0]) == op and norm(o[1]) == op:
            return 0
        if mn == "mov" and len(o) == 2 and norm(o[0]) == op:
            return resolve(o[1].strip(), I, M, j, depth + 1)
        if mn == "movzx" and len(o) == 2 and norm(o[0]) == op and "ds:0x" in o[1]:
            return M.dword(int(o[1].split("ds:0x")[1].split("]")[0], 16)) & 0xff
        if mn in ("lea", "add", "sub", "and", "or", "shl", "shr", "imul", "inc", "dec", "movsx",
                  "sbb", "adc", "neg", "not", "pop", "xchg") and len(o) >= 1 and norm(o[0]) == op:
            return None
        j -= 1
    return None


def eval_cc(mn, op, lhs, rhs):
    """Is the jcc `mn` TAKEN, given the flags left by `op lhs, rhs`?  None when the condition
    needs a flag (CF/OF/SF) that this operation cannot pin down from the resolved operands."""
    if op in ("cmp", "sub"):                       # ordered compare of lhs vs rhs
        return TAKEN.get(mn, lambda a, b: None)(lhs, rhs) if mn in TAKEN else None
    if op in ("test", "and", "or", "xor", "add"):
        if mn not in ("je", "jz", "jne", "jnz"):
            return None
        r = {"test": lhs & rhs, "and": lhs & rhs, "or": lhs | rhs, "xor": lhs ^ rhs,
             "add": (lhs + rhs)}[op] & 0xffffffff
        hit = r != 0
        return (not hit) if mn in ("je", "jz") else hit
    if op in ("inc", "dec", "neg", "not", "shl"):
        if mn not in ("je", "jz", "jne", "jnz"):
            return None
        r = {"inc": lhs + 1, "dec": lhs - 1, "neg": -lhs, "not": ~lhs, "shl": lhs}[op] & 0xffffffff
        hit = r != 0
        return (not hit) if mn in ("je", "jz") else hit
    return None


CTX = {}                                          # blocks / I / reach / zeroed, for provably_zero
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")
WRITEMN = ("mov", "lea", "pop", "inc", "dec", "add", "sub", "and", "or", "xor", "shl", "shr",
           "sar", "movzx", "movsx", "sbb", "adc", "neg", "not", "xchg")


def writes_blocks(I, blocks, reg):
    out = set()
    for a, mn, ops in I:
        o = [x.strip().lower() for x in ops.split(",")]
        if o and mn in WRITEMN and norm(o[0]) == reg:
            b = blockof(blocks, a)
            if b is not None:
                out.add(b)
    return out


def const_at(reg, gaddr):
    """Constant propagation for ONE register over the reachable subgraph: the value of `reg` at
    gaddr, or None when no single constant reaches it.  A block's transfer keeps the incoming value
    unless the block writes reg (then: the constant it writes, else unknown)."""
    blocks, reach, I, idx = CTX["blocks"], CTX["reach"], CTX["I"], CTX["idx"]
    key = (reg, id(reach))
    if key in CTX.setdefault("flow", {}):
        vals = CTX["flow"][key]
    else:
        def transfer(b, inv):
            out = inv
            st, last = blocks[b][0], blocks[b][1]
            for a, m2, ops in I[idx[st]:idx[last] + 1]:
                o = [x.strip().lower() for x in ops.split(",")]
                if not o or m2 not in WRITEMN or norm(o[0]) != reg:
                    continue
                out = None
                if len(o) == 2 and m2 == "xor" and norm(o[1]) == reg:
                    out = 0
                elif len(o) == 2 and m2 == "mov" and (o[1].startswith("0x") or o[1].isdigit()):
                    out = int(o[1], 16) if o[1].startswith("0x") else int(o[1])
            return out
        preds = {b: [] for b in reach}
        for b in reach:
            for s in blocks[b][2]:
                sb = blockof(blocks, s)
                if sb in preds:
                    preds[sb].append(b)
        vals = {b: None for b in reach}
        for _ in range(len(reach) + 2):
            changed = False
            for b in sorted(preds):
                vs = [transfer(p, vals[p]) for p in preds[b]]
                inv = None if any(v is None for v in vs) else (vs[0] if vs else None)
                if b == blocks[min(blocks)][0] and not preds[b]:
                    inv = None                          # the caller's value is unknown
                if inv != vals[b]:
                    vals[b], changed = inv, True
            if not changed:
                break
        CTX.setdefault("flow", {})[key] = vals
    b = blockof(blocks, gaddr)
    v = vals.get(b)
    if v is None:
        return None
    for a, m2, ops in I[idx[b]:idx[idx and gaddr]]:
        o = [x.strip().lower() for x in ops.split(",")]
        if not o or m2 not in WRITEMN or norm(o[0]) != reg:
            continue
        v = None
        if len(o) == 2 and m2 == "xor" and norm(o[1]) == reg:
            v = 0
        elif len(o) == 2 and m2 == "mov" and (o[1].startswith("0x") or o[1].isdigit()):
            v = int(o[1], 16) if o[1].startswith("0x") else int(o[1])
        if v is None:
            return None
    return v


def decide(baddr, mn, I, idx, M):
    """(taken, text) for the jcc at baddr: find the nearest upstream instruction that SETS the
    flags (cmp/test/and/or/sub/add/inc/dec/neg/not/shl — a mov or a push does not) and evaluate it.
    A call in between makes the guard unknown."""
    FLAGS = ("cmp", "test", "and", "or", "xor", "sub", "add", "inc", "dec", "neg", "not", "shl",
             "adc", "sbb", "shr", "sar", "rol", "ror")
    back = idx[baddr] - 1
    while back >= 0 and I[back][0] >= (baddr - 0x60):
        a, m2, ops = I[back]
        o = [x.strip() for x in ops.split(",")]
        if m2 == "call":
            return None, "flags set by a call at 0x%x" % a
        if m2 in FLAGS and len(o) in (1, 2):
            lhs = resolve(o[0], I, M, back)
            rhs = resolve(o[1], I, M, back) if len(o) == 2 else 0
            if lhs is None:
                r0 = norm(o[0].lower())
                if r0 in REGS:
                    lhs = const_at(r0, baddr)
            if rhs is None and len(o) == 2:
                r1n = norm(o[1].lower())
                if r1n in REGS:
                    rhs = const_at(r1n, baddr)
            txt = "%s %s%s" % (m2, norm(o[0].lower()), ", " + norm(o[1].lower()) if len(o) == 2 else "")
            if lhs is None or rhs is None:
                return None, txt + " [unresolved]"
            taken = eval_cc(mn, m2, lhs, rhs)
            if taken is None:
                return None, "%s 0x%x vs 0x%x: %s needs a flag this op cannot pin" % (txt, lhs, rhs, mn)
            return taken, "%s  0x%x vs 0x%x" % (txt, lhs, rhs)
        back -= 1
    return None, "no guard in window"


def _once(blocks, entry, I, idx, M, force):
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


def run(blocks, entry, I, idx, M, force=()):
    """Iterate: pruning shrinks the reachable set, which makes more registers provably 0, which
    prunes more.  Start optimistic (everything reachable) and settle."""
    CTX["blocks"], CTX["I"], CTX["idx"] = blocks, I, idx
    CTX["flow"] = {}
    CTX["reach"] = set(blocks)
    reach, pruned = _once(blocks, entry, I, idx, M, force)
    for _ in range(4):
        r2, p2 = _once(blocks, entry, I, idx, M, force)
        if r2 == CTX["reach"]:
            break
        CTX["reach"] = r2
        reach, pruned = r2, p2
    CTX["reach"] = reach
    return reach, pruned


def blockof(blocks, addr):
    got = None
    for b in blocks:
        if b <= addr and (got is None or b > got):
            got = b
    return got


def args_at(I, idx, site):
    """The pushes before a wrapper call, in ARG order: [dest, size, count, handle]."""
    i, got = idx[site] - 1, []
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
        if "site=0x" in l and "dest=" in l:
            d = {k: (int(v, 16) if k == "site" or v.startswith("0x") else int(v))
                 for k, v in (x.split("=") for x in l.split() if "=" in x)}
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
    last2blk = {blocks[b][1]: b for b in blocks}
    cut = [(last2blk.get(a, a), d) for (a, txt, d) in pruned]

    def reach_without(a, d):
        """Blocks reachable from the entry in the FULL CFG with the single edge a->d removed:
        if the leg is not in it, that pruned edge is a NECESSARY gate for the leg."""
        seen, stack = {LO}, [LO]
        while stack:
            b = stack.pop()
            for s in blocks[b][2]:
                if (b, s) == (a, d) or s not in blocks or s in seen:
                    continue
                seen.add(s)
                stack.append(s)
        return seen

    perleg = {}
    for site in mdead:
        lb = blockof(blocks, site)
        need = [(a, txt) for (a, txt, d) in pruned if lb not in reach_without(last2blk.get(a, a), d)]
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
