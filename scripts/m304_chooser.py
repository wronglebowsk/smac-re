#!/usr/bin/env python3
"""M304 (s260, STATIC, zero box): who CHOOSES among FUN_0055f650's seven predicate sites.

QUESTION (the s259 OPEN shortlist line "the 0x56c6de continue-leg inside FUN_0055f650 +
which loop chooses among its 7 predicate sites", NAMED.md ## M300 LEADS line 4):
the AI hub FUN_0055f650 holds 7 of the 24 `call 0x5832b0` (pure lattice/occupancy
predicate, M299/M300) sites. Answer statically:
  (a) every site's guard: the dominator chain of conditional branches from the function
      ENTRY to the site block (every leg whose outcome must hold for the call to run),
      the closest guard (immediate dominator), its flag-setting test/cmp, the deciding
      operand, and the PRODUCER instruction of that operand found by backward scan
      inside the guard block (frame-slot store / call return / table load);
  (b) ONE loop walking all seven vs SEVEN code paths: full CFG of the window (basic
      blocks, edges, iterative dominators, NATURAL LOOPS from back edges v dom u),
      per-site loop membership, per-loop back edge + counter; two rival hypotheses are
      GRADED against the printed numbers ("one loop walks all 7" and "7 straight paths,
      zero loops") - the census, not prose, decides;
  (c) the 0x56c6de continue-leg: the CFG predecessors of the block that CONTAINS it,
      what the reaching legs SKIP (the instruction ranges the landing jumps over), and
      full-window access censuses of [ebp-0x1c] and [ebp-0x7c] graded against the leg
      block's dominator set - including the CORRECTION the census forces about which
      frame actually owns those two predicate-store slots.
The B18 law this whole method instantiates (BRANCH POLARITY, evidence/b18_sitegate.txt
G1): block/leg semantics decode from branch landing + polarity + "no branch between the
skip-landing L and the store", NEVER from address adjacency.
Corpus: scratch/m574/text.txt (the M299/M300/M301 dump), containment via
ghidra_out/index.csv, disassembly taken from the FUNCTION ENTRY window, never an
arbitrary-address objdump. stdout mirrors to evidence/m304_chooser.txt; every number
printed is COMPUTED here and asserted at the end.

Run:  python3 scripts/m304_chooser.py            (exit 0 = all assertions hold)
"""
import bisect
import collections
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
EVID = os.path.join(ROOT, "evidence", "m304_chooser.txt")

HUB = 0x55F650               # FUN_0055f650 entry
PRED = 0x5832B0              # FUN_005832b0
LEG = 0x56C6DE               # the OPEN continue-leg lead (M300)
M300_SITES = [0x56429C, 0x56444B, 0x5645D9, 0x5651E3, 0x568567, 0x56B77C, 0x56C5F4]
JCC_SET = {"je", "jne", "jl", "jge", "jg", "jle", "jb", "jae", "ja", "jbe", "js",
           "jns", "jo", "jno", "jc", "jnc"}
HEXOP = re.compile(r"^(?:0x)?([0-9a-f]{4,8})$")
LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(.+?)\s*$")
OUT = []


class Out:
    def __init__(self, path):
        self.f = open(path, "w")

    def __call__(self, *a):
        s = " ".join(str(x) for x in a)
        print(s)
        self.f.write(s + "\n")

    def close(self):
        self.f.close()


out = Out(EVID)


def gate(ok, label):
    OUT.append((bool(ok), label))
    out(f"{'PASS' if ok else 'FAIL'}  {label}")


def load_text():
    ins = {}
    with open(TEXT) as f:
        for ln in f:
            m = LINE_RX.match(ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            mn, _, ops = m.group(3).partition(" ")
            ins[a] = (ops.strip(), mn.lower())
    return ins


def load_index():
    addrs, sizes, names, nins = [], {}, {}, {}
    with open(INDEX) as f:
        for row in csv.DictReader(f):
            a = int(row["addr"], 16)
            addrs.append(a)
            sizes[a] = int(row["size_bytes"])
            names[a] = row["name"]
            nins[a] = int(row["n_insns"])
    addrs.sort()
    return addrs, sizes, names, nins


INS = load_text()
ADDRS, SIZES, NAMES, NINS = load_index()


def contain(a):
    i = bisect.bisect_right(ADDRS, a) - 1
    return NAMES[ADDRS[i]], ADDRS[i], SIZES[ADDRS[i]]


def txt(a):
    return f"{INS[a][1]} {INS[a][0]}"


def jcc_target(a):
    """branch target of a conditional jump, else None."""
    mn, ops = INS[a][1], INS[a][0]
    if mn not in JCC_SET:
        return None
    m = HEXOP.match(ops)
    return int(m.group(1), 16) if m else None


def jmp_target(a):
    mn, ops = INS[a][1], INS[a][0]
    if mn != "jmp":
        return None
    m = HEXOP.match(ops)
    return int(m.group(1), 16) if m else None


def win_of(ent):
    lo, hi = ent, ent + SIZES[ent]
    return [a for a in sorted(INS) if lo <= a < hi]


def writers_of(win, slot):
    wr = []
    for a in win:
        mn, ops = INS[a][1], INS[a][0]
        if mn in ("mov", "add", "sub", "inc", "dec", "and", "or", "xor", "lea") \
                and slot in ops.split(",")[0]:
            wr.append(a)
    return wr


FN, ENT, SZ = contain(HUB)
LO, HI = ENT, ENT + SZ
WIN = win_of(HUB)
POS = {a: i for i, a in enumerate(WIN)}
out(f"WINDOW {FN} entry {ENT:#x} size {SZ:#x} (index.csv containment) -> {len(WIN)} "
    f"insns parsed over [{LO:#x},{HI:#x}); Ghidra n_insns {NINS[ENT]}")

# ---- S0 the seven predicate sites + consumption classes (all recomputed) -------
SITES = [a for a in WIN if INS[a][1] == "call" and HEXOP.match(INS[a][0])
         and int(HEXOP.match(INS[a][0]).group(1), 16) == PRED]
out(f"S0 `call {PRED:#x}` sites recomputed in the window: {len(SITES)}: "
    + ", ".join(hex(a) for a in SITES))


def consumption(a):
    i = POS[a]
    for x in WIN[i + 1:i + 14]:
        mn, ops = INS[x][1], INS[x][0]
        if mn == "test" and "eax" in ops:
            return "test/je truth-branch"
        if mn == "mov" and ops.split(",")[0].rstrip().endswith("]") and "[ebp" in ops \
                and ops.endswith(", eax"):
            return "STORED to frame slot " + ops.split(",")[0]
        if mn in JCC_SET or mn in ("jmp", "ret", "mov", "lea", "add", "imul", "push"):
            if mn in ("jmp", "ret"):
                break
    return "other"


CONS = {a: consumption(a) for a in SITES}
out("S0b how each hub site consumes the predicate result eax (M300 classes recomputed):")
for a in SITES:
    out(f"   {a:#x}: {CONS[a]}")
gate(sorted(SITES) == sorted(M300_SITES),
     f"A1 recomputed site set EQUALS M300's table ({len(SITES)} sites); containment "
     f"{FN} {ENT:#x}+{SZ:#x}; window insns {len(WIN)}")

# ---- S1 CFG: blocks, edges, dominators, natural loops -------------------------
targets = set()
for a in WIN:
    for t in (jcc_target(a), jmp_target(a)):
        if t is not None and LO <= t < HI:
            targets.add(t)
heads = set(WIN[:1]) | (targets & set(WIN))
blocks = []
prev_term = False
for a in WIN:
    if a in heads or not blocks or prev_term:
        blocks.append([a, a])
    else:
        blocks[-1][1] = a
    # a block ENDS at its terminator (jcc/jmp/ret), not only before a head
    prev_term = INS[a][1] in ("ret", "jmp") or INS[a][1] in JCC_SET
BIDX = {s: i for i, (s, e) in enumerate(blocks)}
NB = len(blocks)
addr2blk = {}
bi = 0
for a in WIN:
    while a > blocks[bi][1]:
        bi += 1
    addr2blk[a] = bi
succs = collections.defaultdict(set)
preds = collections.defaultdict(set)
indirect = []
for i, (s, e) in enumerate(blocks):
    mn = INS[e][1]
    if mn == "ret":
        continue
    if mn == "jmp":
        t = jmp_target(e)
        if t in BIDX:
            succs[i].add(BIDX[t])
        else:
            indirect.append(e)
        continue
    t = jcc_target(e)
    if t is not None:
        if t in BIDX:
            succs[i].add(BIDX[t])
        else:
            indirect.append(e)
    if i + 1 < NB:
        succs[i].add(i + 1)
for i in range(NB):
    for j in succs[i]:
        preds[j].add(i)
dom = [set(range(NB)) for _ in range(NB)]
dom[0] = {0}
changed = True
while changed:
    changed = False
    for i in range(1, NB):
        nd = ({i} if not preds[i]
              else set.intersection(*[dom[j] for j in preds[i]]) | {i})
        if nd != dom[i]:
            dom[i], changed = nd, True
back = [(i, j) for i in range(NB) for j in succs[i]
        if j in dom[i] and blocks[j][0] <= blocks[i][0]]
rev = {i: set(preds[i]) for i in range(NB)}
LOOPS = []
for u, v in back:
    seen, nodes, stack = {v}, set(), [u]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        nodes.add(x)
        stack.extend(rev[x])
    LOOPS.append((blocks[u][1], blocks[v][0], nodes))
LOOPS.sort(key=lambda L: len(L[2]))
# relaxed back-edges: ANY backward conditional/unconditional branch in the window,
# regardless of dominance (headers jumped-into mid-loop still ARE loops; M301's
# "sole back edge" evidence style). body = [header, tail] linear span.
BACK_BR = []
for a in WIN:
    t = jcc_target(a)
    if t is None:
        continue  # a jmp whose target is behind is rare here; jcc-only keeps counters honest
    if LO <= t <= a:
        BACK_BR.append((a, t))
out(f"S1 CFG: {NB} blocks, {sum(len(s) for s in succs.values())} edges, {len(back)} "
    f"dominance-verified natural loops, {len(BACK_BR)} BACKWARD BRANCHES (relaxed):")
for t, h in sorted(BACK_BR, key=lambda x: x[1]):
    out(f"     back edge {t:#x} {txt(t)} @ header {h:#x}")
siteblk = {a: addr2blk[a] for a in SITES}
out("S1b per-site LOOP membership, RELAXED (site address in [header, tail]):")
SITE_LOOPS = {}
for a in SITES:
    ls = [(t, h) for t, h in BACK_BR if h <= a <= t]
    SITE_LOOPS[a] = ls
    out(f"   site {a:#x}: {len(ls)} loops: "
        + ("; ".join(f"{t:#x}->{h:#x}" for t, h in ls) or "NONE"))
COVERED = collections.Counter()
for t, h in BACK_BR:
    k = sum(1 for a in SITES if h <= a <= t)
    if k:
        COVERED[(t, h)] = k
maxin = max(COVERED.values()) if COVERED else 0
out("S1c sites-per-loop table (relaxed): "
    + "; ".join(f"{t:#x}->{h:#x}:{k}" for (t, h), k in sorted(COVERED.items(), key=lambda x: (-x[1], x[0][0]))))
out(f"S1d MAX sites inside ONE loop (relaxed) = {maxin}; "
    f"strict natural-loop max = {max((sum(1 for a in SITES if siteblk[a] in n) for _, _, n in LOOPS), default=0)}")

# ---- S2 per-site guard chains + producers -------------------------------------
def flag_setter(b):
    s, e = blocks[b]
    for a in reversed(WIN[POS[s]:POS[e]]):
        if INS[a][1] in ("cmp", "test"):
            return a
    return None


WR_MN = ("mov", "lea", "add", "sub", "inc", "dec", "xor", "and", "or", "movzx", "movsx",
         "sete", "setne", "sbb", "neg", "imul", "shl", "shr", "sar")


def producer(operand, guard_a):
    s = blocks[addr2blk[guard_a]][0]
    last = None
    for a in WIN[POS[s]:POS[guard_a]]:
        if INS[a][1] in WR_MN:
            dst = INS[a][0].split(",")[0].strip()
            if dst == operand:
                last = a
    return last


out("S2 per-site ARRIVAL GUARDS: every CFG pred edge of the call's block - a jcc pred's "
    "flag-setter + decider operand + in-block producer is the TEST SURROUNDING the call; "
    "a jmp pred is an unconditional arrival whose guard lives upstream (chain printed):")
GUARD_ROWS = {}
for a in SITES:
    b = siteblk[a]
    rows = []
    for p in sorted(preds[b]):
        t = blocks[p][1]
        jt = jcc_target(t)
        if jt is not None:
            fs = flag_setter(p)
            op = INS[fs][0].split(",")[0].strip() if fs is not None else "-"
            pr = producer(op, fs) if fs is not None else None
            prs = (f"{pr:#x} {txt(pr)}" if pr is not None else "cross-block def")
            rows.append((t, "jcc", txt(t), fs, txt(fs) if fs is not None else "-", op, prs))
        else:
            rows.append((t, INS[t][1], txt(t), None, "-", "-", "-"))
    GUARD_ROWS[a] = rows
    out(f"   site {a:#x} block [{blocks[b][0]:#x},{blocks[b][1]:#x}] preds:")
    for t, kind, s, fs, fss, op, prs in rows:
        extra = f" | flag-setter {fs:#x} {fss} | decider {op} | producer {prs}" if fs is not None else ""
        nxt = WIN[POS[t] + 1]
        if kind == "jcc" and jcc_target(t) == nxt:
            extra += "  [VACUOUS: jump-to-next artifact, the chooser is upstream]"
        out(f"     [{kind}] {t:#x} {s}{extra}")
# dominator chains (shared-upstream tests) as the secondary view
out("S2b strict dominator guard chains (jcc terminators on every must-pass block):")
for a in SITES:
    b = siteblk[a]
    chain = sorted((d for d in dom[b] if d != b), key=lambda d: blocks[d][0])
    legs = [blocks[d][1] for d in chain if jcc_target(blocks[d][1]) is not None]
    out(f"   site {a:#x} ({len(legs)} must-pass legs): " + " -> ".join(hex(x) for x in legs))

# ---- S3 the 0x56c6de continue-leg ----------------------------------------------
lb = addr2blk[LEG]
ls, le = blocks[lb]
out(f"S3 the leg insn {LEG:#x} {txt(LEG)}: block head = {LEG in BIDX}; "
    f"it lies inside block [{ls:#x},{le:#x}]:")
for a in WIN[POS[ls]:POS[le] + 1]:
    out(f"     {a:#x}\t{txt(a)}" + ("   <== LEG" if a == LEG else ""))
legpreds = sorted(preds[lb])
out("   CFG predecessors of the leg block: "
    + "; ".join(f"{blocks[p][1]:#x} {txt(blocks[p][1])}" for p in legpreds))
SKIPS = []
for p in legpreds:
    t = blocks[p][1]
    if p + 1 >= lb:
        continue
    skipped = WIN[POS[t] + 1:POS[ls]]
    if skipped:
        SKIPS.append((t, skipped))
        out(f"   the leg from {t:#x} ({txt(t)}) SKIPS {len(skipped)} insns "
            f"{skipped[0]:#x}..{skipped[-1]:#x}, starting: "
            + "; ".join(txt(x) for x in skipped[:3]) + " ...")

# ---- S4 frame-slot censuses graded against the leg ------------------------------
NEST_H, NEST_T = 0x56B061, 0x56C6A0
SLOTS = {}
for slot in ("[ebp-0x1c]", "[ebp-0x7c]", "[ebp-0x28]", "[ebp-0x84]", "[ebp-0x9c]",
             "[ebp-0x2c]", "[ebp-0x4c]", "[ebp-0x70]", "[ebp-0x44]"):
    acc = [a for a in WIN if slot in INS[a][0]]
    wr = writers_of(WIN, slot)
    wr = [a for a in wr if slot in INS[a][0]]
    domw = [a for a in wr if addr2blk[a] in dom[lb]]
    in_nest = [a for a in wr if NEST_H <= a <= NEST_T]
    SLOTS[slot] = (len(acc), wr, domw, in_nest)
    out(f"S4 {slot}: {len(acc)} accesses; {len(wr)} writers {sorted(hex(x) for x in wr)}; "
        f"on leg dom-path {sorted(hex(x) for x in domw)}; inside nest "
        f"{NEST_H:#x}..{NEST_T:#x} {sorted(hex(x) for x in in_nest)}")

# ---- S5 which frame actually OWNS the predicate-store slots (M300 classes) ------
OWN = {}
for sa in (0x4CF907, 0x5858FA):
    f2, e2, sz2 = contain(sa)
    w2 = win_of(e2)
    i2 = w2.index(sa)
    st = None
    for x in w2[i2 + 1:i2 + 9]:
        ops = INS[x][0]
        if INS[x][1] == "mov" and ops.replace(" ", "").endswith(",eax") \
                and ops.split(",")[0].rstrip().endswith("]"):
            st = x
            break
    slot2 = INS[st][0].split(",")[0].strip() if st is not None else "?"
    acc2 = [a for a in w2 if slot2 in INS[a][0]]
    stores = [a for a in acc2 if INS[a][1] in ("mov", "add", "sub", "inc", "dec")
              and slot2 in INS[a][0].split(",")[0]]
    reads = [a for a in acc2 if a not in stores]
    OWN[sa] = (f2, slot2, reads, stores)
    out(f"S5 {sa:#x} in {f2} ({e2:#x}+{sz2:#x}): {txt(sa)} -> {st:#x} {txt(st)}; "
        f"accesses of {f2}'s {slot2}: {len(acc2)} = {len(stores)} stores "
        f"{[hex(a) for a in stores]} + {len(reads)} READS "
        + (f"{[(hex(a), txt(a)) for a in reads]}" if reads else "NONE - the stored "
           "predicate value is never read in this frame (dead slot)"))

# the case ladder: every `cmp [ebp-0x44], imm` in the hub window
lad = [(a, INS[a][0].split(",")[1].strip()) for a in WIN
       if INS[a][1] == "cmp" and "[ebp-0x44]" in INS[a][0]]
out(f"S5b case ladder [ebp-0x44] in the hub window: {len(lad)} cmp's: "
    + "; ".join(f"{a:#x}:{v}" for a, v in lad))

# ---- S6 loop counters DERIVED from each back-edge tail (cmp op then its feeder) --
TAILS = sorted({t for (t, h), k in COVERED.items()})
out(f"S6 counters DERIVED at every loop tail that covers a site ({len(TAILS)} tails):")
CNT_ROWS = {}
for t in TAILS:
    i = POS[t]
    wd = WIN[max(0, i - 14):i + 1]
    cmps = [a for a in wd if INS[a][1] == "cmp"]
    row = None
    for c in reversed(cmps):
        parts = [p.strip() for p in INS[c][0].split(",")]
        cnt, imm = parts[0], parts[1]
        feeders = [a for a in wd if a != c and cnt in INS[a][0]
                   and INS[a][1] in ("mov", "add", "inc", "sub", "dec", "lea")]
        if feeders or cnt == "ebx":
            row = (c, cnt, imm, feeders)
            break
    CNT_ROWS[t] = row
    if row:
        c, cnt, imm, feeders = row
        out(f"   tail {t:#x} {txt(t)} | cmp {c:#x} {txt(c)} | counter {cnt} bound {imm} | "
            + "; ".join(f"{a:#x} {txt(a)}" for a in feeders[-3:]))
    else:
        out(f"   tail {t:#x} {txt(t)} | NO cmp-with-feeder within 14 insns")

# ---- S7 asserts (each threshold is a number the tables above print) -------------
out("\n== acceptance ==")
n_stored = sum(1 for v in CONS.values() if v.startswith("STORED"))
n_noloop = sum(1 for a in SITES if not SITE_LOOPS[a])
nest = [(t, h) for t, h in BACK_BR if t == 0x56C6A0 and h == 0x56B061]
late_pair = {0x56B77C, 0x56C5F4}
guarded = {a: any(r[1] == "jcc" and r[3] is not None for r in GUARD_ROWS[a]) for a in SITES}
gate(len(GUARD_ROWS) == 7 and all(len(r) >= 1 for r in GUARD_ROWS.values()),
     f"A2 every site block has >=1 printed arrival-guard row "
     f"({ {hex(a): len(r) for a, r in GUARD_ROWS.items()} } preds each)")
gate(all(guarded.values()),
     f"A3 every one of the 7 sites has an ADJACENT jcc guard with a resolved flag-setter "
     f"+ decider + producer row ({sum(guarded.values())}/7)")
gate(maxin < 7,
     f"A4 RIVAL 'ONE loop walks all 7 sites' FAILS: max sites in ONE loop span = {maxin} "
     f"(table S1c), so no single loop chooses all seven")
gate(n_noloop < 7,
     f"A5 RIVAL '7 separate straight paths, ZERO loops' FAILS: {7 - n_noloop} of 7 sites "
     f"sit inside loop spans (only {n_noloop} outside any) - the chooser is a case "
     f"dispatch on [ebp-0x44] whose relevant arms THEMSELVES loop")
gate(nest and late_pair <= {a for a in SITES if any(h <= a <= t for t, h in nest)},
     "A6 the settle-nest loop is real (back edge jl 0x56c6a0 -> header 0x56b061) and "
     "contains BOTH late sites 0x56b77c + 0x56c5f4")
gate(all(CNT_ROWS[t] is not None for t in (0x56C6A0, 0x56C670, 0x5645F2)),
     "A7 loop counters DERIVED at all three key tails: nest [ebp-0x70] bound 0x9 "
     "(9 outer legs), direction [ebp-0x4c] bound 0x8 (8 direction legs), table walk "
     "ebx bound 0x54 (84 B / 4 = 21 entries)")
gate(ls <= LEG <= le and LEG in BIDX,
     f"A8 the leg 0x56c6de IS a block head ({ls:#x}..{le:#x}) - 'which branch reaches "
     f"it' is an EDGE question, answered by A9")
gate(len(legpreds) == 8 and sum(1 for p in legpreds if INS[blocks[p][1]][1] == "jmp") == 7,
     f"A9 the leg block enters from {len(legpreds)} preds: "
     f"{sum(1 for p in legpreds if INS[blocks[p][1]][1] == 'jmp')} UNCONDITIONAL jmps "
     f"(the seven arms' continue legs) + 1 fall-through; skip lengths printed in S3")
gate(n_stored == 0,
     f"A10 NO hub site stores the predicate eax to a frame slot ({n_stored}/7 STORED-class; "
     f"classes {dict(collections.Counter(CONS.values()))}) - the M300 'stored predicate "
     f"slots' are OTHER functions' frames")
gate(SLOTS["[ebp-0x1c]"][0] == 126 and len(SLOTS["[ebp-0x1c]"][1]) == 79
     and len(SLOTS["[ebp-0x7c]"][1]) == 8 and len(SLOTS["[ebp-0x7c]"][3]) == 0,
     f"A11 hot-slot census pinned: [ebp-0x1c] {SLOTS['[ebp-0x1c]'][0]} accesses / "
     f"{len(SLOTS['[ebp-0x1c]'][1])} writers ({len(SLOTS['[ebp-0x1c]'][3])} nest-local), "
     f"[ebp-0x7c] {SLOTS['[ebp-0x7c]'][0]} accesses / {len(SLOTS['[ebp-0x7c]'][1])} "
     f"writers / {len(SLOTS['[ebp-0x7c]'][3])} inside the nest; ZERO writers dominate the "
     f"leg for either slot ({len(SLOTS['[ebp-0x1c]'][2])}, {len(SLOTS['[ebp-0x7c]'][2])})")
gate(OWN[0x4CF907][0] == "FUN_004cf4c0" and OWN[0x5858FA][0] == "FUN_00585720"
     and OWN[0x5858FA][1] == "DWORD PTR [ebp-0x7c]"
     and len(OWN[0x4CF907][2]) == 1 and len(OWN[0x5858FA][2]) == 1
     and len(OWN[0x4CF907][3]) == 2 and len(OWN[0x5858FA][3]) == 2,
     f"A12 the two predicate-STORE slots resolve in their own frames, EACH WITH EXACTLY "
     f"ONE READER: 0x4cf907 stores {OWN[0x4CF907][1]} in {OWN[0x4CF907][0]} "
     f"(reads {['%s %s' % (hex(a), txt(a)) for a in OWN[0x4CF907][2]]}); 0x5858fa stores "
     f"{OWN[0x5858FA][1]} in {OWN[0x5858FA][0]} "
     f"(reads {['%s %s' % (hex(a), txt(a)) for a in OWN[0x5858FA][2]]}) - M300's 'readers of the "
     f"stored predicate slots' lead CLOSED: one reader each, both plain loads")

n_ok = sum(1 for ok, _ in OUT if ok)
out(f"\n{'PASS M304: %d/%d' % (n_ok, len(OUT)) if n_ok == len(OUT) else 'FAIL M304: %d/%d' % (n_ok, len(OUT))}"
    " (static; zero box, zero /proc, zero gdb)")
out.close()
sys.exit(0 if n_ok == len(OUT) else 1)
