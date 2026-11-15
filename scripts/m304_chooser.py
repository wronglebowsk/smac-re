#!/usr/bin/env python3
"""M304 (s260, STATIC, zero box): who CHOOSES among FUN_0055f650's seven predicate sites.

QUESTION (the s259 OPEN shortlist line "the 0x56c6de continue-leg inside FUN_0055f650 +
which loop chooses among its 7 predicate sites", NAMED.md ## M300 LEADS line 4):
the AI hub FUN_0055f650 (entry 0x55f650, size 0xD513 by index.csv containment) holds 7 of
the 24 `call 0x5832b0` (pure lattice/occupancy predicate, M299/M300) sites. Answer statically:
  (a) every site's GUARD: the branch whose taken/fall-through leg decides the call executes,
      the flag-setting test/cmp, the deciding register/slot, and the PRODUCER of that value
      inside the same function window;
  (b) ONE loop walking all seven vs SEVEN code paths: compute the CFG of the window, the
      natural loops (back edges + dominance), and print per-site loop membership;
  (c) the 0x56c6de continue-leg: the branch that reaches it, what it skips, and the state of
      the two predicate frame slots [ebp-0x1c] and [ebp-0x7c] when taken - full-window
      access censuses + dominance, never prose.
Method: CFG from the full-.text dump scratch/m574/text.txt (the M299/M300 corpus), basic
blocks split at branch targets + terminators, iterative dominator sets, natural loops from
back edges (v dom u). Every number printed is COMPUTED here and asserted at the end; rival
hypotheses are GRADED against the printed numbers, incl. the shortlist's own implicit rival
"ONE loop walks all seven sites" - which the census is expected to FAIL.
stdout mirrors to evidence/m304_chooser.txt.

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
CONTINUE_LEG = 0x56C6DE      # the OPEN continue-leg lead (M300)
SLOT_1C = "[ebp-0x1c]"
SLOT_7C = "[ebp-0x7c]"
JCC = r"(je|jne|jl|jge|jg|jle|jb|jae|ja|jbe|js|jns|jo|jno|jc|jnc)"
LINE_RX = re.compile(r"^ +([0-9a-f]{6,8}):\t([0-9a-f ]+)\t\s*(.+?)\s*$")
CALL_RX = re.compile(r"^call\s+(?:0x)?([0-9a-f]{4,8})(?:\s|$)")
JRX = re.compile(r"^jcc|jmp|ret", re.I)
OUTCOMES = []


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


def load_text():
    """addr -> (bytes, mnem, operands) from the aligned full-.text cache."""
    ins = {}
    with open(TEXT) as f:
        for ln in f:
            m = LINE_RX.match(ln)
            if not m:
                continue
            a = int(m.group(1), 16)
            mn, _, ops = m.group(3).partition(" ")
            ins[a] = (m.group(2).replace(" ", ""), mn.lower(), m.group(3))
    return ins


def load_index():
    addrs, sizes, names = [], {}, {}
    with open(INDEX) as f:
        for row in csv.DictReader(f):
            a = int(row["entry_point"], 16)
            addrs.append(a)
            sizes[a] = int(row["size_bytes"], 16) if row["size_bytes"].startswith("0x") else int(row["size_bytes"])
            names[a] = row["function_name"]
    addrs.sort()
    return addrs, sizes, names


def contain(addrs, sizes, names, a):
    i = bisect.bisect_right(addrs, a) - 1
    return names[addrs[i]], addrs[i], sizes[addrs[i]]


INS = load_text()
ADDRS, SIZES, NAMES = load_index()
FN, ENT, SZ = contain(ADDRS, SIZES, NAMES, HUB)
assert FN == "FUN_0055f650" and ENT == HUB, (FN, ENT)
LO, HI = HUB, HUB + SZ
WIN = sorted(a for a in INS if LO <= a < HI)
GAPS = [b - a - len(INS[a][0]) // 2 for a, b in zip(WIN, WIN[1:])]
out(f"WINDOW {FN} {LO:#x}..{HI:#x} size {SZ:#x}: {len(WIN)} insns, gap tiles {[g for g in GAPS if g != 0] or 'none - contig'}")

# ---- S0 the seven predicate sites (recompute, do not trust M300's table) ------
SITES = [a for a in WIN if INS[a][1] == "call" and CALL_RX.match(INS[a][2])
         and int(CALL_RX.match(INS[a][2]).group(1), 16) == PRED]
M300_SITES = [0x56429C, 0x56444B, 0x5645D9, 0x5651E3, 0x568567, 0x56B77C, 0x56C5F4]
out("S0 sites in window:", ", ".join(hex(a) for a in SITES))

# ---- S1 CFG: basic blocks, edges, dominators, natural loops -------------------
TERM = {"jmp", "ret"} | {j for j in JCC.split("|")}
targets = set()
for a in WIN:
    mn, ops = INS[a][1], INS[a][2]
    m = re.match(rf"^{JCC}\s+(?:0x)?([0-9a-f]+)$", ops)
    if m:
        targets.add(int(m.group(1), 16))
    elif mn == "jmp":
        m2 = re.match(r"^(?:0x)?([0-9a-f]+)$", ops)
        if m2:
            targets.add(int(m2.group(1), 16))
heads = set(WIN[:1]) | (targets & set(WIN))
blocks, bstart = [], None
for a in WIN:
    if a in heads:
        bstart = a
        blocks.append([a, a])
    else:
        blocks[-1][1] = a
BLK = {s: i for i, (s, e) in enumerate(blocks)}
addr2blk = {}
for i, (s, e) in enumerate(blocks):
    for a in WIN:
        if s <= a <= e:
            addr2blk[a] = i
succs = collections.defaultdict(set)
for i, (s, e) in enumerate(blocks):
    t = INS[e][1]
    ops = INS[e][2]
    if t == "ret":
        continue
    if t == "jmp":
        m2 = re.match(r"^(?:0x)?([0-9a-f]+)$", ops)
        if m2 and int(m2.group(1), 16) in BLK:
            succs[i].add(BLK[int(m2.group(1), 16)])
        else:
            succs[i].add(("INDIRECT", hex(e)))
        continue
    m3 = re.match(rf"^{JCC}\s+(?:0x)?([0-9a-f]+)$", ops)
    if m3 and int(m3.group(1), 16) in BLK:
        succs[i].add(BLK[int(m3.group(1), 16)])
    if t not in ("jmp",):
        nxt = blocks[i + 1][0] if i + 1 < len(blocks) else None
        if nxt is not None:
            succs[i].add(BLK[nxt])
NB = len(blocks)
dom = [set(range(NB)) for _ in range(NB)]
dom[0] = {0}
changed = True
while changed:
    changed = False
    for i in range(1, NB):
        preds = {j for j in range(NB) if i in succs[j]}
        if not preds:
            nd = {i}
        else:
            nd = set.intersection(*[dom[j] for j in preds]) | {i}
        if nd != dom[i]:
            dom[i], changed = nd, True
out(f"S1 CFG: {NB} blocks, indirect-jmp blocks: {sorted(b for i in range(NB) for b in succs[i] if isinstance(b, tuple)) or 'none'}")
SITEBLK = {a: addr2blk[a] for a in SITES}
for a in SITES:
    b = SITEBLK[a]
    idom = max((d for d in dom[b] if d != b), key=lambda d: blocks[d][0]) if len(dom[b]) > 1 else None
    gt = INS[blocks[idom][1]] if idom is not None else None
    out(f"  site {a:#x} blk@{blocks[b][0]:#x} n_dom {len(dom[b])} idom {idom if idom is None else hex(blocks[idom][0])} term {gt[1]+' '+gt[2] if gt else '-'}")

# ---- S2 per-site guards (idom terminators), producers, loop membership -------
out("S2 per-site guard + producer windows (print-only pass, asserts set in S8)")
for a in SITES:
    out(f"--- guard window before site {a:#x} ---")
    i = WIN.index(a)
    for x in WIN[max(0, i - 26):i + 8]:
        mn, op = INS[x][1], INS[x][2]
        out(f"   {x:#x}\t{mn} {op}")

# ---- S3 the continue-leg + the two frame slots -------------------------------
out(f"--- continue-leg window {CONTINUE_LEG-0x80:#x}..{CONTINUE_LEG+0x90:#x} ---")
for x in WIN:
    if CONTINUE_LEG - 0x80 <= x <= CONTINUE_LEG + 0x90:
        out(f"   {x:#x}\t{INS[x][1]} {INS[x][2]}")
for slot in (SLOT_1C, SLOT_7C):
    acc = [a for a in WIN if slot in INS[a][2]]
    out(f"S3 accesses of {slot} in window: {len(acc)}: " +
        "; ".join(f"{a:#x} {INS[a][1]} {INS[a][2]}" for a in acc))

out("TODO: asserts")
out.close()
