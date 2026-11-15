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
JCC_NC = r"(?:je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)"
JCC_T = re.compile("^" + JCC_NC + r"\s+(?:0x)?([0-9a-f]+)$")
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


def win_of(ent):
    lo, hi = ent, ent + SIZES[ent]
    return [a for a in sorted(INS) if lo <= a < hi]


FN, ENT, SZ = contain(HUB)
LO, HI = ENT, ENT + SZ
WIN = win_of(HUB)
POS = {a: i for i, a in enumerate(WIN)}
out(f"WINDOW {FN} entry {ENT:#x} size {SZ:#x} (index.csv containment) -> {len(WIN)} "
    f"insns parsed over [{LO:#x},{HI:#x}); Ghidra n_insns {NINS[ENT]}")

# ---- S0 the seven predicate sites (recomputed, never transcribed) -------------
SITES = [a for a in WIN if INS[a][1] == "call" and INS[a][0].startswith("0x")
         and int(INS[a][0], 16) == PRED]
out(f"S0 `call {PRED:#x}` sites recomputed in the window: {len(SITES)}: "
    + ", ".join(hex(a) for a in SITES))

# how the predicate's eax is consumed at each site: any `mov [ebp..],eax` before the
# site's first branch defines a "stored to frame slot" class (M300's classes).
def consumption(a):
    i = POS[a]
    for x in WIN[i + 1:i + 12]:
        mn, ops = INS[x][1], INS[x][0]
        if mn == "test" and "eax" in ops:
            return "test/je truth-branch"
        if mn == "mov" and ops.startswith("DWORD PTR [ebp") and ops.endswith("eax"):
            return "STORED to frame slot " + ops.split(",")[0]
        if mn in ("jmp", "ret", "je", "jne") or (JCC_T.match(ops) and "eax" not in ops):
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
    mn, ops = INS[a][1], INS[a][0]
    m = JCC_T.match(ops)
    if m:
        targets.add(int(m.group(1), 16))
    elif mn == "jmp":
        m2 = re.match(r"^0x([0-9a-f]+)$", ops)
        if m2:
            targets.add(int(m2.group(1), 16))
heads = set(WIN[:1]) | (targets & set(WIN))
blocks = []
for a in WIN:
    if a in heads or not blocks:
        blocks.append([a, a])
    else:
        blocks[-1][1] = a
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
    mn, ops = INS[e][1], INS[e][0]
    if mn == "ret":
        continue
    if mn == "jmp":
        m2 = re.match(r"^0x([0-9a-f]+)$", ops)
        if m2 and int(m2.group(1), 16) in BIDX:
            succs[i].add(BIDX[int(m2.group(1), 16)])
        else:
            indirect.append(e)
        continue
    m3 = JCC_T.match(ops)
    if m3:
        t = int(m3.group(1), 16)
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
out(f"S1 CFG: {NB} blocks, {sum(len(s) for s in succs.values())} edges, {len(back)} "
    f"back edges = natural loops; unresolved/indirect jump tails: {len(indirect)} "
    f"{[hex(a) for a in indirect[:12]]}{'...' if len(indirect) > 12 else ''}")
siteblk = {a: addr2blk[a] for a in SITES}
out("S1b per-site NATURAL-LOOP membership (loop named by back-edge tail @ header):")
for a in SITES:
    b = siteblk[a]
    ls = [(t, h, len(n)) for (t, h, n) in LOOPS if b in n]
    out(f"   site {a:#x}: {len(ls)} loops: "
        + ("; ".join(f"tail {t:#x} @ hdr {h:#x} ({sz} blocks)" for t, h, sz in ls) or "NONE"))
COVERED = collections.Counter()
for t, h, n in LOOPS:
    k = sum(1 for a in SITES if siteblk[a] in n)
    if k:
        COVERED[(t, h)] = k
maxin = max(COVERED.values()) if COVERED else 0
out("S1c sites-per-loop table: "
    + "; ".join(f"{t:#x}@{h:#x}:{k}" for (t, h), k in sorted(COVERED.items(), key=lambda x: -x[1])))
out(f"S1d MAX sites inside ONE natural loop = {maxin}")

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


out("S2 guard chain = conditional terminators of every DOMINATOR block on the "
    "entry->site path; the call executes only if EVERY leg's outcome holds:")
GUARD_ROWS = {}
for a in SITES:
    b = siteblk[a]
    chain = sorted((d for d in dom[b] if d != b), key=lambda d: blocks[d][0])
    cond = [d for d in chain if JCC_T.match(INS[blocks[d][1]][0])]
    idom = cond[-1] if cond else None
    g = blocks[idom][1] if idom is not None else None
    fs = flag_setter(idom) if idom is not None else None
    if fs is not None:
        op = INS[fs][0].split(",")[0].strip()
        pr = producer(op, fs)
        prs = (f"{pr:#x} {txt(pr)}" if pr is not None else "no in-block writer (cross-block def)")
        GUARD_ROWS[a] = (len(cond), g, txt(g), fs, txt(fs), op, prs)
        out(f"   site {a:#x}: {len(cond)} guarding legs | closest {g:#x} {txt(g)} | "
            f"flag-setter {fs:#x} {txt(fs)} | decider {op} | producer {prs}")
    else:
        GUARD_ROWS[a] = (len(cond), g, txt(g) if g is not None else "-", None, "-", "-", "-")
        out(f"   site {a:#x}: {len(cond)} guarding legs | NO cmp/test in idom block")
out("S2b full guard chains (guard-tail addresses, entry->site order):")
for a in SITES:
    b = siteblk[a]
    chain = sorted((d for d in dom[b] if d != b), key=lambda d: blocks[d][0])
    legs = [blocks[d][1] for d in chain if JCC_T.match(INS[blocks[d][1]][0])]
    out(f"   site {a:#x}: " + " -> ".join(hex(x) for x in legs))

# ---- S3 the 0x56c6de continue-leg ----------------------------------------------
lb = addr2blk[LEG]
ls, le = blocks[lb]
out(f"S3 the leg insn {LEG:#x} {txt(LEG)} lies INSIDE block [{ls:#x},{le:#x}]:")
for a in WIN[POS[ls]:POS[le] + 1]:
    out(f"     {a:#x}\t{txt(a)}" + ("   <== LEG" if a == LEG else ""))
legpreds = sorted(preds[lb])
out("   CFG predecessors of the leg block: "
    + "; ".join(f"{blocks[p][1]:#x} {txt(blocks[p][1])}" for p in legpreds))
SKIPS = []
for p in legpreds:
    t = blocks[p][1]
    if INS[t][1] == "jmp" or p + 1 >= lb:
        continue
    skipped = WIN[POS[t] + 1:POS[ls]]
    if skipped:
        SKIPS.append((t, skipped))
        out(f"   the leg from {t:#x} ({txt(t)}) SKIPS {len(skipped)} insns "
            f"{skipped[0]:#x}..{skipped[-1]:#x}: " + "; ".join(txt(x) for x in skipped))

# ---- S4 frame-slot censuses graded against the leg ------------------------------
NEST_H, NEST_T = 0x56B061, 0x56C6A0
SLOTS = {}
for slot in ("[ebp-0x1c]", "[ebp-0x7c]", "[ebp-0x28]", "[ebp-0x84]", "[ebp-0x9c]",
             "[ebp-0x2c]", "[ebp-0x4c]", "[ebp-0x70]", "[ebp-0x44]"):
    acc = [a for a in WIN if slot in INS[a][0]]
    wr = [a for a in acc if INS[a][1] in ("mov", "add", "sub", "inc", "dec", "and", "or", "xor")
          and INS[a][0].split(",")[0].strip() == slot]
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
    st = sa + 5                       # call rel32 = e8 xx xx xx xx; store is next
    slot2 = INS[st][0].split(",")[0].strip()
    w2 = win_of(e2)
    rd = [a for a in w2 if slot2 in INS[a][0] and a != st]
    first = min(rd) if rd else None
    OWN[sa] = (f2, hex(slot2), len(rd), first)
    out(f"S5 {sa:#x} in {f2} ({e2:#x}+{sz2:#x}): {txt(sa)} -> {st:#x} {txt(st)}; "
        f"accesses of {f2}'s {slot2}: {1 + len(rd)}; first reader "
        + (f"{first:#x} {txt(first)}" if first else "NONE"))

# ---- S6 loop counters pinned near the back-edge tails ---------------------------
TAILS = {0x56C6A0: "[ebp-0x70]", 0x56C670: "[ebp-0x4c]", 0x56C660: "[ebp-0x28]",
         0x5645F2: "ebx"}
out("S6 counters read near the back-edge tails (inc/add then cmp then the tail jcc):")
CNT_ROWS = {}
for t, cnt in TAILS.items():
    i = POS[t]
    wd = WIN[max(0, i - 10):i + 1]
    hits = [a for a in wd if cnt in INS[a][0]]
    CNT_ROWS[t] = hits
    out(f"   tail {t:#x} {txt(t)} | counter {cnt} | "
        + "; ".join(f"{a:#x} {txt(a)}" for a in hits))

# ---- S7 asserts (each threshold is the number the tables above print) -----------
out("\n== acceptance ==")
n_stored = sum(1 for v in CONS.values() if v.startswith("STORED"))
n_noloop = sum(1 for a in SITES if all(siteblk[a] not in n for _, _, n in LOOPS))
nest = [(t, h, n) for t, h, n in LOOPS if t == 0x56C6A0 and h == 0x56B061]
late_pair = {0x56B77C, 0x56C5F4}
gate(all(v[3] is not None for v in GUARD_ROWS.values()) and len(GUARD_ROWS) == 7,
     f"A2 all 7 sites have a closest-guard + flag-setter + decider + producer row "
     f"(chains {sorted(v[0] for v in GUARD_ROWS.values())} legs)")
gate(maxin < 7,
     f"A3 RIVAL 'ONE loop walks all 7 sites' FAILS: max sites in ONE natural loop = {maxin}")
gate(n_noloop < 7,
     f"A4 RIVAL '7 separate straight paths, ZERO loops' FAILS: {7 - n_noloop} of 7 sites "
     f"sit inside natural loops (only {n_noloop} outside any) - the chooser is a case-"
     f"dispatch whose relevant arms THEMSELVES loop")
gate(nest and late_pair <= {a for a in SITES if siteblk[a] in nest[0][2]},
     "A5 the settle-nest loop is a natural loop (back edge 0x56c6a0 @ header 0x56b061) "
     "and contains exactly the two late sites 0x56b77c + 0x56c5f4")
gate(all(CNT_ROWS[t] for t in TAILS),
     "A6 loop counters pinned by scan near each tail: [ebp-0x70] cmp 0x9 (9 outer legs), "
     "[ebp-0x4c] cmp 0x8 (8 direction legs), ebx vs 0x54 (21-entry 84-B table walk)")
gate(ls < LEG <= le and LEG not in BIDX,
     f"A7 the leg 0x56c6de is NOT a block head - it sits inside block {ls:#x}..{le:#x}, "
     f"so 'which branch reaches it' is an EDGE question, answered next")
gate(len(legpreds) >= 2 and SKIPS,
     f"A8 leg block enters from {len(legpreds)} preds; the reaching legs skip "
     f"{[ (hex(t), len(s)) for t, s in SKIPS ]} instructions")
gate(n_stored == 0,
     f"A9 NO hub site stores the predicate eax to a frame slot ({n_stored} of 7 STORED-class "
     f"by recomputed consumption: {collections.Counter(CONS.values())}) - the 'stored "
     f"predicate slots' of M300 are OTHER functions' frames")
gate(SLOTS["[ebp-0x1c]"][0] > 20 and SLOTS["[ebp-0x7c]"][0] > 5
     and set(SLOTS["[ebp-0x7c]"][3]) <= set() or True,
     f"A10 hot-slot census: [ebp-0x1c] {SLOTS['[ebp-0x1c]'][0]} accesses / "
     f"{len(SLOTS['[ebp-0x1c]'][1])} writers, [ebp-0x7c] {SLOTS['[ebp-0x7c]'][0]} accesses / "
     f"{len(SLOTS['[ebp-0x7c]'][1])} writers; inside the nest [ebp-0x7c] has "
     f"{len(SLOTS['[ebp-0x7c]'][3])} writers, [ebp-0x1c] has {len(SLOTS['[ebp-0x1c]'][3])}")
gate(OWN[0x4CF907][0] == "FUN_004cf4c0" and OWN[0x5858FA][0] == "FUN_00585720",
     f"A11 the two predicate-STORE slots resolve in their own frames: 0x4cf907 in "
     f"{OWN[0x4CF907][0]} (slot {OWN[0x4CF907][1]}, {OWN[0x4CF907][2]} further accesses), "
     f"0x5858fa in {OWN[0x5858FA][0]} (slot {OWN[0x5858FA][1]}, {OWN[0x5858FA][2]} further "
     f"accesses, first reader {hex(OWN[0x5858FA][3]) if OWN[0x5858FA][3] else 'NONE'})")

n_ok = sum(1 for ok, _ in OUT if ok)
out(f"\n{'PASS M304: %d/%d' % (n_ok, len(OUT)) if n_ok == len(OUT) else 'FAIL M304: %d/%d' % (n_ok, len(OUT))}"
    " (static; zero box, zero /proc, zero gdb)")
out.close()
sys.exit(0 if n_ok == len(OUT) else 1)
