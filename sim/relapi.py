"""sim.relapi - rung B39: the RELATIONS API FAMILY (four entry points, two words).

Every rung from M364 to M388 mapped ONE dword, 0x94d448. M368's open peace host (0x523f4c) calls
three APIs in a row and 0x551c40's stores land at 0x94d468 - eight dwords deeper in the same
2095-dword faction block (M297's identity). This module censuses the four API bodies out of the
`scratch/m574/text.txt` disassembly dump, prints their field homes / index algebra / arg guards /
verbs, and EXECUTES the peace host's own three-call sequence over a constructed pair of words.

  python3 -u -m sim.relapi          # the acceptance: PASS B39 n/n

Zero box, zero /proc, zero gdb. Every number printed here is computed from the dump; every
assertion is a gate that a named mutant in scripts/b39_mutate.py reddens.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("B39_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.environ.get("B39_EXE") or os.path.join(ROOT, "programs/terran.exe")

WORD_A = 0x94D448          # the word every earlier rung mapped
WORD_B = 0x94D468          # the sibling the peace host actually writes
LEASE = 0x94D4C8           # B37's 50-tick cell
BLOCK_DWORDS = 2095        # M297: the per-faction block is f*2095 dwords
APIS = [0x551A20, 0x551C40, 0x551CF0, 0x551D70]
EXTENTS = {0x551A20: 161, 0x551C40: 57, 0x551CF0: 41, 0x551D70: 37}
HOST_SITE = 0x523F4C       # M368's open peace writer
HOST_BLOCK = 0x523F23      # the guarded block inside the host that carries the three calls
FIELDS = {WORD_A: "A", WORD_B: "B", LEASE: "L"}
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi")

# the host's guard chain, pinned:  (addr, "mnem operands", jcc mnemonic, jcc target)
HOST_GUARDS = [
    (0x523F2D, "test al,0x1", "je", 0x523F38),           # bit0 SET -> consult 0x2000000
    (0x523F31, "test eax,0x2000000", "jne", 0x523F7A),   # 0x2000000 set -> skip the whole block
    (0x523F44, "cmp esi,edi", "je", 0x523F60),           # self-pair -> skip the 0x1 and 0x2000 writes
]

OK = []
FAIL = []


def gate(gid, cond, msg):
    print("%s %s %s" % ("ok  " if cond else "BAD ", gid, msg))
    (OK if cond else FAIL).append(gid)


def sha16(rows):
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()[:16]


def load(path=TEXT):
    from . import relations as _R          # the proven INSN parser (bytes field stripped)
    return [tuple(r) for r in _R.load(path)]


def index(ins):
    return {a: i for i, (a, _, _) in enumerate(ins)}


def extent(ins, idx, entry, cap=0x300):
    """The function body: entry .. the first `ret` whose successor is padding or a new prologue."""
    i = idx[entry]
    j = i
    while j < len(ins) and ins[j][0] - entry < cap:
        addr, mn, op = ins[j]
        if mn == "ret":
            nxt = ins[j + 1] if j + 1 < len(ins) else None
            if nxt is None or nxt[1] in ("nop", "int3") or nxt[0] - addr > 8:
                return list(ins[i:j + 1])
        j += 1
    return list(ins[i:j])


def regs_of(op):
    return [s.strip() for s in op.split(",")] if op else []


FIELD_RE = re.compile(r"0x94d4[0-9a-f]{2}")
MEM_RE = re.compile(r"\[([^\]]+)\]")


def row_scale(body):
    """The f*2095 row scale, decoded from the fixed shl6/add/lea/shl4/sub chain.

    (((f<<6)+f)*2+f)<<4 - f  =  ((64+1)*2+1)<<4 - 1 = 2095.
    """
    for k, (addr, mn, op) in enumerate(body):
        p = regs_of(op)
        if not (mn == "shl" and len(p) == 2 and p[1] == "0x6"):
            continue
        x = p[0]
        win = [w for w in body[k + 1:k + 9] if w[1] in ("add", "lea", "shl", "sub")]
        if len(win) >= 4:
            a = regs_of(win[0][2])
            l = regs_of(win[1][2])
            s4 = regs_of(win[2][2])
            sb = regs_of(win[3][2])
            if a[0] == x and l[1].startswith("[" + a[1] + "+" + x + "*2") \
               and s4[0] == l[0] and s4[1] == "0x4" and sb == [l[0], a[1]]:
                return ((((1 << 6) + 1) * 2 + 1) << 4) - 1
    return 0


def stores(body):
    """[(addr, field, verb, imm, partner_reg)] - every write whose destination is a relation field.

    The field is either a literal displacement in the store operand or (the common form here) a
    literal displacement folded into a pointer by a preceding `lea`; the pointer map is invalidated
    the moment the register is re-defined without a relation displacement.  The VERB is adopted
    only from an RMW that writes THE REGISTER THE STORE STORES, or from the store's own immediate -
    a neighbouring `or` of some other register is not evidence about this store.  The partner
    register is the register last `add`ed into the store's row base, which is what makes the two
    directions of a symmetric API measurable instead of assumed.
    """
    out = []
    ptr = {}
    verb = {}
    prev = []
    for addr, mn, op in body:
        parts = regs_of(op)
        if not parts:
            prev.append((addr, mn, op))
            continue
        if mn in ("or", "and") and len(parts) == 2:
            verb[parts[0]] = (mn.upper(), parts[1])
        if mn == "lea" and len(parts) == 2:
            f = FIELD_RE.findall(parts[1])
            if f:
                base = parts[1].strip("[]").split("*")[0].split("+")[0].strip()
                partner = None
                for paddr, pmn, pop in reversed(prev[-6:]):
                    q = regs_of(pop)
                    if pmn == "add" and len(q) == 2 and q[0] == base and q[1] != base:
                        partner = q[1]
                        break
                ptr[parts[0]] = (int(f[0], 16), partner)
            else:
                ptr.pop(parts[0], None)
        elif mn in ("mov", "add", "sub") and len(parts) == 2 and parts[0] in ptr:
            if FIELD_RE.findall(parts[1]):
                ptr[parts[0]] = (int(FIELD_RE.findall(parts[1])[0], 16), ptr[parts[0]][1])
            else:
                ptr.pop(parts[0], None)
        if mn in ("mov", "or", "and") and "[" in parts[0]:
            m = MEM_RE.search(parts[0])
            field = partner = None
            if m:
                fs = FIELD_RE.findall(m.group(1))
                if fs:
                    field = int(fs[0], 16)
                else:
                    base = m.group(1).split("*")[0].split("+")[0].strip()
                    if base in ptr:
                        field, partner = ptr[base]
            if field:
                src = parts[1] if len(parts) > 1 else "?"
                if src in verb:
                    v, imm = verb[src]
                elif re.match(r"^0x[0-9a-f]+$", src):
                    v, imm = "SETI", src
                else:
                    v, imm = "COPY", src
                out.append((addr, field, v, imm, partner))
        prev.append((addr, mn, op))
    return out


def guards(body):
    """[(addr, operand0, operand1)] for every `test` whose second operand is an immediate."""
    out = []
    for addr, mn, op in body:
        if mn != "test":
            continue
        p = regs_of(op)
        if len(p) == 2 and p[1] not in REGS:
            out.append((addr, p[0], p[1]))
        elif len(p) == 1:
            out.append((addr, p[0], "MODE"))
    return out


def find_host(ins, idx):
    """The function containing HOST_SITE: scan back to the nearest push ebp / mov ebp,esp."""
    i = idx[HOST_SITE]
    while i > 0:
        if ins[i][1] == "push" and ins[i][2] == "ebp" and i + 1 < len(ins) \
           and "ebp,esp" in ins[i + 1][2].replace(" ", ""):
            break
        i -= 1
    return extent(ins, idx, ins[i][0], cap=0x900)


CALL_RE = re.compile(r"0x([0-9a-f]+)")


def call_sites(body, targets):
    """[(addr, api, [push operands in address order])] for calls into the API family."""
    out = []
    for k, (addr, mn, op) in enumerate(body):
        if mn != "call":
            continue
        m = CALL_RE.search(op)
        if not m or int(m.group(1), 16) not in targets:
            continue
        pushes = [p[2] for p in body[max(0, k - 3):k] if p[1] == "push"]
        out.append((addr, int(m.group(1), 16), pushes))
    return out


# ---------------------------------------------------------------- the model (measured verbs)

def blank(n=8):
    return [[0] * n for _ in range(n)]


def api_551c40(B, f, p, mask):
    """0x551c40: symmetric write on word B; a mask carrying 0x20 selects the AND ~0x40 arm."""
    if mask & 0x20:
        B[f][p] &= ~0x40 & 0xFFFFFFFF
        B[p][f] &= ~0x40 & 0xFFFFFFFF
    else:
        B[f][p] |= mask
        B[p][f] |= mask


def api_551cf0(A, cell, f, p, mask, mode=1, lease_imm=0x32):
    """0x551cf0: OR the mask into word A; a mask carrying 0x40 arms the lease cell."""
    if mode:
        A[f][p] |= mask
        if mask & 0x40:
            cell[f][p] = lease_imm


def api_551d70(B, f, p, mask, mode=1):
    """0x551d70: mode!=0 ORs the mask into B[f][p]; mode==0 ANDs its complement."""
    if mode:
        B[f][p] |= mask
    else:
        B[f][p] &= ~mask & 0xFFFFFFFF


def peace_host(A, B, cell, cur=0, partner=1, arow=0x1, lease_imm=0x32):
    """0x523f23's block, executed exactly as the pinned guard chain reads it.

    bit0 SET -> consult 0x2000000 (set = skip the whole block, clear = run it); bit0 CLEAR -> run it
    without consulting 0x2000000; a self-pair skips the 0x1 and 0x2000 writes only.
    """
    if (arow & 0x1) and (arow & 0x2000000):
        return "skipped: A-row bit0 set and 0x2000000 set"
    if cur != partner:
        A[cur][partner] |= 0x1            # 0x551a20(cur, partner, 0x1): ladder, body UNMODELLED
        api_551c40(B, cur, partner, 0x2000)
    return "ok"


def peace_host_naive(B, cur=0, partner=1):
    """RIVAL: the pair-equality guard ignored - a self-pair still gets both writes."""
    api_551c40(B, cur, partner, 0x2000)
    return "ok"


def accept(quiet=False):
    ins = load()
    idx = index(ins)
    print("B39  relations API family - four entry points, two words")
    print("dump %s sha1 %s" % (os.path.basename(TEXT), sha16([str(x) for x in ins])))
    print("exe  %s sha1 %s" % (os.path.basename(EXE), hashlib.sha1(open(EXE, "rb").read()).hexdigest()))

    print()
    print("G1  store census per API body")
    print("    api       len  rowscale  fields          stores")
    api = {}
    for entry in APIS:
        body = extent(ins, idx, entry)
        st = stores(body)
        api[entry] = {"body": body, "stores": st, "scale": row_scale(body), "guards": guards(body)}
        print("    %08x  %3d  %5d     %-14s  %d" % (
            entry, len(body), row_scale(body),
            ",".join(sorted(FIELDS.get(s[1], hex(s[1])) for s in st)), len(st)))
        for s in st:
            print("        %07x -> %s %s %s partner=%s" % s)

    # G0 - pins: four bodies, prologue..ret, extents pinned
    pin_ok = all(api[a]["body"] and api[a]["body"][0][1] == "push" and api[a]["body"][0][2] == "ebp"
                 and api[a]["body"][-1][1] == "ret" and len(api[a]["body"]) == EXTENTS[a] for a in APIS)
    gate("G0", len(ins) > 100000 and pin_ok,
         "pins: %d dump rows; four bodies push-ebp..ret at pinned extents %s" %
         (len(ins), [len(api[a]["body"]) for a in APIS]))

    # G1 - field homes, store counts, and the two directions of 0x551c40 from the operands
    homes = {a: sorted(set(s[1] for s in api[a]["stores"])) for a in APIS}
    counts = {a: len(api[a]["stores"]) for a in APIS}
    or_partners = [s[4] for s in api[0x551C40]["stores"] if s[2] == "OR"]
    sym = len(or_partners) == 2 and or_partners[0] != or_partners[1] \
        and all(p in ("eax", "ecx") for p in or_partners)
    gate("G1", homes[0x551A20] == [WORD_A] and homes[0x551CF0] == sorted([WORD_A, LEASE])
         and homes[0x551C40] == [WORD_B] and homes[0x551D70] == [WORD_B]
         and counts == {0x551A20: 8, 0x551C40: 4, 0x551CF0: 3, 0x551D70: 2} and sym,
         "homes %s counts %s; 0x551c40's OR stores take partner registers %s" %
         ({hex(k): [FIELDS.get(v, hex(v)) for v in homes[k]] for k in APIS},
          [counts[a] for a in APIS], or_partners))

    # G2 - index algebra
    scales = {a: api[a]["scale"] for a in APIS}
    off = WORD_B - WORD_A
    gate("G2", all(v == BLOCK_DWORDS for v in scales.values()) and off == 0x20,
         "row scale %s == %d dwords; WORD_B-WORD_A = 0x%x = %d dwords" %
         (sorted(set(scales.values())), BLOCK_DWORDS, off, off // 4))

    # G3 - API arg guards
    g = {a: [(p0, imm) for _, p0, imm in api[a]["guards"]] for a in APIS}
    mode_arg = any("ebp+0x14" in op for _, _, op in api[0x551D70]["body"])
    gate("G3", ("bl", "0x7") in g[0x551A20] and ("bl", "0x20") in g[0x551C40]
         and ("cl", "0x40") in g[0x551CF0] and mode_arg,
         "guards 551a20=%s 551c40=%s 551cf0=%s 551d70 4th-arg mode=%s" %
         (g[0x551A20], g[0x551C40], g[0x551CF0], mode_arg))

    # G3b - the lease constant and the mask arm's AND constant, both READ OUT of the census above
    lease_imm = [int(s[3], 16) for s in api[0x551CF0]["stores"] if s[1] == LEASE]
    and_verbs = [s[3] for s in api[0x551C40]["stores"] if s[2] == "AND"]
    gate("G3b", lease_imm == [0x32] and set(and_verbs) == {"0xffffffbf"},
         "the lease store's own immediate = %s; the 0x20 arm's AND constant = %s (dump bytes, "
         "not the model)" % ([hex(v) for v in lease_imm], sorted(set(and_verbs))))

    # G4 - the model executes the measured verbs
    A, B, cell = blank(), blank(), blank()
    api_551c40(B, 0, 1, 0x2000)
    B[2][3] = 0x2050
    api_551c40(B, 2, 3, 0x2020)
    api_551cf0(A, cell, 0, 1, 0x40, lease_imm=lease_imm[0])
    api_551d70(B, 4, 5, 0x800, mode=1)
    api_551d70(B, 4, 5, 0x800, mode=0)
    print()
    print("    exec 551c40(0x2000) B[0][1]=%#x B[1][0]=%#x | 551c40(0x2020) on seeded 0x2050 -> B[2][3]=%#x "
          "(clears 0x40, does NOT set 0x20) | 551cf0(0x40) A[0][1]=%#x cell=%#x | "
          "551d70 set-then-clear B[4][5]=%#x" % (B[0][1], B[1][0], B[2][3], A[0][1], cell[0][1], B[4][5]))
    gate("G4", B[0][1] == 0x2000 and B[1][0] == 0x2000 and B[2][3] == 0x2010
         and A[0][1] == 0x40 and cell[0][1] == lease_imm[0] and B[4][5] == 0,
         "verbs: 551c40 sets BOTH directions; the 0x20 arm clears 0x40; 551cf0 arms cell %#x "
         "(the census immediate); 551d70 mode 0 clears" % lease_imm[0])

    # G5 - the peace host
    host = find_host(ins, idx)
    sites = [s for s in call_sites(host, set(APIS)) if s[0] >= HOST_BLOCK]
    print()
    print("    host %07x..%07x  block calls %s" %
          (host[0][0], host[-1][0], [(hex(a), hex(p), m) for a, p, m in sites]))
    seq = [(p, m[0]) for a, p, m in sites[:3]]
    gate("G5a", seq == [(0x551A20, "0x50"), (0x551A20, "0x1"), (0x551C40, "0x2000")],
         "peace block call sequence %s (mask = the FIRST push byte, i.e. the last argument written)" %
         [(hex(p), m) for p, m in seq])

    # G5d - the three guards, pinned by address and target and read from the bytes
    gd = []
    for addr, want_op, jmn, jtgt in HOST_GUARDS:
        i = idx[addr]
        cur = "%s %s" % (ins[i][1], ins[i][2])
        nxt = ins[i + 1]
        gd.append((hex(addr), cur, nxt[1], hex(int(nxt[2], 16))))
        if not (cur == want_op and nxt[1] == jmn and int(nxt[2], 16) == jtgt):
            gd.append("MISMATCH")
    print("    guards %s" % gd[:3])
    gate("G5d", "MISMATCH" not in gd,
         "host guard chain: `test al,0x1 / je 0x523f38`, `test eax,0x2000000 / jne 0x523f7a`, "
         "`cmp esi,edi / je 0x523f60`")

    je = [x for x in host if x[1] == "je" and HOST_BLOCK <= x[0] <= 0x523F50 and int(x[2], 16) == 0x523F60]
    gate("G5b", len(je) == 1 and ins[idx[je[0][0]] - 1][1] == "cmp",
         "the `je` at %s (preceded by `%s %s`) skips BOTH the 0x1 call (%s) and the 0x2000 call (%s)" %
         (hex(je[0][0]) if je else "?", ins[idx[je[0][0]] - 1][1] if je else "?",
          ins[idx[je[0][0]] - 1][2] if je else "?", hex(0x523F4C), hex(0x523F58)))

    def run(arow, cur=0, partner=1):
        A2, B2, c2 = blank(), blank(), blank()
        r = peace_host(A2, B2, c2, cur=cur, partner=partner, arow=arow, lease_imm=lease_imm[0])
        return r, A2, B2

    r_pair, A_pair, B_pair = run(0x1, 0, 1)
    r_self, A_self, B_self = run(0x1, 1, 1)
    r_nobit, A_nobit, B_nobit = run(0x0, 0, 1)
    r_skip, A_skip, B_skip = run(0x2000001, 0, 1)
    r_skip0, A_skip0, B_skip0 = run(0x2000000, 0, 1)
    print("    exec pair B=%#x/%#x | self-pair B=%#x/%#x | bit0 clear B=%#x/%#x | bit0+0x2000000 -> %s | "
          "0x2000000 WITHOUT bit0 B=%#x/%#x" %
          (B_pair[0][1], B_pair[1][0], B_self[1][0], B_self[1][1], B_nobit[0][1], B_nobit[1][0],
           r_skip, B_skip0[0][1], B_skip0[1][0]))
    gate("G5c", r_pair == "ok" and B_pair[0][1] == 0x2000 and B_pair[1][0] == 0x2000
         and B_self[1][0] == 0 and B_self[1][1] == 0
         and B_nobit[0][1] == 0x2000 and B_nobit[1][0] == 0x2000
         and r_skip.startswith("skipped") and B_skip[0][1] == 0
         and B_skip0[0][1] == 0x2000,
         "host execution: pair 0x2000 both ways; self-pair none; bit0 clear still writes; "
         "0x2000000 skips ONLY when bit0 is set")

    # G6 - rivals, each executed and compared to the measured numbers
    r1 = homes[0x551C40] == [WORD_A]
    r2 = any(s[1] == WORD_A for s in api[0x551C40]["stores"])
    Bn = blank()
    peace_host_naive(Bn, cur=1, partner=1)
    r3 = Bn[1][1] == B_self[1][1]
    r4 = counts[0x551C40] == 0 or counts[0x551D70] == 0
    r5 = any(s[1] == WORD_A and s[3].lower() == "0x2000" for a in APIS for s in api[a]["stores"])
    gate("G6", not r1 and not r2 and not r3 and not r4 and not r5,
         "rivals fail: one-matrix=%s B-is-mirror=%s unconditional-0x1(self-pair B %#x vs measured %#x)=%s "
         "padding=%s peace-on-A=%s" % (r1, r2, Bn[1][1], B_self[1][1], r3, r4, r5))

    # G7 - digests twice
    d1 = sha16(["%x:%s:%s" % (a, m, o) for a, m, o in ins] + ["%s" % (s,) for s in api[0x551C40]["stores"]])
    ins2 = load()
    d2 = sha16(["%x:%s:%s" % (a, m, o) for a, m, o in ins2] +
               ["%s" % (s,) for s in stores(extent(ins2, index(ins2), 0x551C40))])
    print()
    print("digest %s / %s" % (d1, d2))
    gate("G7", d1 == d2, "two decodes of the dump agree (%s)" % d1)

    n_ok, n_all = len(OK), len(OK) + len(FAIL)
    if FAIL:
        print("FAIL B39: %d/%d gates  red: %s" % (n_ok, n_all, sorted(set(FAIL))))
        return 1
    print("PASS B39: %d/%d gates  digest %s" % (n_ok, n_all, d1))
    return 0


def main(argv=None):
    return accept()


if __name__ == "__main__":
    sys.exit(main())
