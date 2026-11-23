#!/usr/bin/env python3
"""M333 (chain1 s313): the 34 feeder slots `0x984d48 + 48*slot` — the slot NOUN, and why bit5 HALVES.

Pick (x1) from NEXT_PROMPT, the OPEN row of `## M330` G10 ("slot noun OPEN").
STATIC, zero box, zero /proc, zero gdb. Reuses M326's reviewed .text cache, its helpers,
plus (a) a SHAPE-pin for the loop-counter fold and (b) a def-use bit-5 census of block+0.

WHY a shape-pin instead of the value-walker for the fold: `value_of(0x4f48ce,'eax')` answers
`('const', 48)` — its LINEAR backward walk finds `mov esi,0x1` and never sees the `inc esi`
at the loop bottom, so it over-proves 48*1 (the "PASS on an unmeasured state" defect).
The item index is pinned by SHAPE: the two instructions above the read must be
`lea r,[i+i*2]` + `shl r,0x4` (r == shl dest, base == index), and `i` must be the SAME
register the charge bound tests and the disabled-item list compares against.

LOOP STRUCTURE (measured, G1/G7): FUN_004f47f0's loop top is 0x4f480b, bottom 0x4f4a34.
`esi` = ITEM id: init 1; the TOP test `cmp esi,0x22 / jg 0x4f4a34` SKIPS the charge body for
ids 35..38 (it is NOT the loop exit); the bottom `inc esi / cmp esi,0x27 / jl 0x4f480b` is
the back-edge, so the loop VISITS ids 1..38 and CHARGES ids 1..34. The table is 39 rows
(0x750 = 1872 = 39*48 read out of .text); id 0 is never visited.

MEASURED LAW (every number is computed here, printed, then asserted):
  FUN_004f47f0(cur_base) is the per-BASE facility-upkeep charge. The cost is the stride-48
  item table's dword at 0x984d48+48*item; the charge is taken ONLY for items the base
  actually has (a bit in the 304-B base record at base+0x8c, addressed as 304*[ds:0x68cbb0],
  mapped by FUN_00507410). FUN_004f4760(item, faction) is the SAME law as a standalone
  function and is cross-checked against the loop feature-by-feature.
  The halving is a CARRIED HALF-UNIT: bit5 of the owner FACTION block's dword 0
  (0x94d430 + 8380*own, own = BYTE[[ds:0x8f0d60]+4], computed once in the prologue) is read
  (shr 5 + and 1), ADDED to the item cost, the sum is arithmetic-shifted right by 1 (that
  quotient is the charge), and the sum's PARITY is written back into that SAME bit5 — the
  odd remainder survives to next round instead of being truncated away. It fires only when
  the base indexed by ds:0x985ba0 has the same owner byte; otherwise the FULL cost is
  charged and bit5 is untouched. ds:0x985ba0 has NO writer in .text (2 loads, 0 stores
  image-wide) — its writer is outside .text (BSS bulk copy / save restore); noun INFERRED.
  G5 census: FUN_004f47f0 is the ONLY function image-wide that READS bit5 of a block+0
  value and the ONLY one that WRITES it (def-use scan, path-insensitive, stops at calls and
  function boundaries). FUN_004dc390 is the near-miss: it mirrors block+0 bits 30/29/20 into
  bits 4/5/6 of a DERIVED dword — its `or ecx,0x20` is not block+0's bit5.
  NEW FINDING (row-printed, not gated): the same loop body also carries a REMOVAL path
  (second mapper call 0x4f49b6, bitmap bit CLEAR 0x4f49e1, store to block+0x220 0x4f4a0b,
  calls 0x4e40a0/0x6265a2/0x48f100) — open lead for the next fire.

Acceptance: python3 -u scripts/m333_feeder_slot_census.py -> TABLE FIRST, then gates, digest;
a re-run must be byte-identical.  Mutants: scripts/m333_mutate.py (--selftest runs them).
Patch env: M333_PATCH="addr|mnemonic ops;addr|mnemonic ops" applied to m326.INS after import
(the instrument prints `patches applied: n/m` as contact proof).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326  # noqa: E402

INS, ADDRS, AIDX = m326.INS, m326.ADDRS, m326.AIDX
owner, split_ops, memref = m326.owner, m326.split_ops, m326.memref
value_of = m326.value_of

LOOP, COST = 0x4F47F0, 0x4F4760     # FUN_004f47f0 upkeep charge / FUN_004f4760 item cost
LOOP_TOP, LOOP_BOTTOM, LOOP_END = 0x4F480B, 0x4F4A34, 0x4F4A3C
CHARGE_END = 0x4F4938               # the two halving-skip targets land here
ITEM_UPKEEP, ITEM_ROW0, ROW = 0x984D48, 0x984D38, 48
MAPPER = 0x507410                   # FUN_00507410(item, &byte_index, &bit_mask)
BASE_ARRAY, BASE_OWNER_BYTE, BASE_ITEMMAP = 0x95DA10, 0x95DA14, 0x95DA9C
BLKBASE, BLKSTRIDE, NBLK = 0x94D430, 0x20BC, 8
CBIT, CIMM, CCLR = 5, 0x20, 0xFFFFFFDF
DISA_COUNT, DISA_ENTS, DISA_STRIDE = 0x927A9C, 0x927AC0, 0x59C
CURR_BASE, SEL_BASE, CURR_REC = 0x68CBB0, 0x985BA0, 0x8F0D60
ITEM27, TABLE_ROWS = 0x1B, 39
EVID = os.environ.get("M333_EVIDENCE_ROOT", ROOT)

_npatch = 0


def apply_patch():
    """M333_PATCH='addr|mn ops;addr|mn ops' -> rewrite INS entries (contact proof printed)."""
    global _npatch
    spec = os.environ.get("M333_PATCH", "")
    if not spec:
        return
    total = 0
    for part in spec.split(";"):
        if not part.strip():
            continue
        total += 1
        addr, _, rest = part.partition("|")
        a = int(addr.strip(), 16)
        if a not in INS:
            raise SystemExit("M333_PATCH: target %06x not in .text cache (vacuous mutant)" % a)
        mn, _, ops = rest.strip().partition(" ")
        INS[a] = (mn, ops)
        _npatch += 1
    if _npatch != total:
        raise SystemExit("M333_PATCH: applied %d of %d" % (_npatch, total))


def wbody(fn, lo=None, hi=None):
    a, b = fn, fn + m326.FSIZE[fn]
    return [x for x in ADDRS if max(a, lo or a) <= x < min(b, hi or b)]


def find(body, mn, pat):
    return [a for a in body if INS[a][0] == mn and re.search(pat, INS[a][1])]


def reads_at(body, disp):
    """(addr, operand-text) for every instruction in body with a memory operand at `disp`."""
    out = []
    for a in body:
        for op in split_ops(INS[a][1]):
            mi = memref(op)
            if mi and ((mi[1] if mi[0] == "abs" else mi[2]) == disp):
                out.append((a, op))
    return out


def txt(a):
    return "%06x: %s %s" % (a, INS[a][0], INS[a][1])


def fold48(a):
    """The item-index fold above an item-table read: `lea r,[i+i*2]` then `shl r,0x4`.
    Returns (leaf_reg, [(addr, text)...]) or (None, why-not). Shape-checked on purpose,
    not value-walked: the value-walker over-proves this one through the loop back-edge."""
    i = AIDX[a]
    for _ in range(6):
        i -= 1
        if i < 0:
            break
        b = ADDRS[i]
        if owner(b) != owner(a):
            break
        mn, ops = INS[b]
        parts = split_ops(ops)
        if mn == "call":
            return (None, "call before the fold: %s" % txt(b))
        if mn == "shl" and len(parts) == 2 and parts[1].strip() == "0x4":
            for j in range(i - 1, max(-1, i - 4), -1):
                c = ADDRS[j]
                cmn, cops = INS[c]
                if cmn == "nop":
                    continue
                if cmn == "lea":
                    m = re.fullmatch(r"(\w+),\[(\w+)\+(\w+)\*(\d)\]", cops)
                    if m and m.group(2) == m.group(3) and int(m.group(4)) == 2 \
                            and m.group(1) == parts[0].strip():
                        return (m.group(2), [(c, txt(c)), (b, txt(b))])
                    return (None, "lea is not 3*i into the shl dest: %s" % txt(c))
                return (None, "unexpected above the shl: %s" % txt(c))
            return (None, "no lea above the shl")
    return (None, "no shl ,0x4 within 6 instructions")


def aff(a, reg):
    return value_of(a, reg)


def block0_disp(d):
    return d is not None and BLKBASE <= d < BLKBASE + NBLK * BLKSTRIDE and (d - BLKBASE) % BLKSTRIDE == 0


def disp_of(op):
    m = memref(op)
    return (m[1] if m[0] == "abs" else m[2]) if m else None


def holds_blk0(a, reg, depth=0):
    """Path-insensitive def-walk: is reg's last writer before `a` a load/copy of a block+0 value?
    Stops at calls and at the function boundary (documented approximation)."""
    if depth > 3:
        return False
    i = AIDX[a]
    while i > 0:
        i -= 1
        b = ADDRS[i]
        if owner(b) != owner(a):
            return False
        mn = INS[b][0]
        ops = split_ops(INS[b][1])
        if not ops:
            continue
        if mn == "call":
            return False
        if ops[0].strip() == reg:
            if mn in ("mov", "lea") and any(block0_disp(disp_of(o)) for o in ops[1:]):
                return True
            if mn == "mov" and re.fullmatch(r"\w+", ops[1].strip()) and holds_blk0(b, ops[1].strip(), depth + 1):
                return True
            return False
    return False


def bit5_census(fnwith):
    """(readfns, writefns, readhits, writehits): who READS / WRITES bit5 of a block+0 VALUE.
    READ  = test/bt reg,0x20|0x5 or (shr reg,0x5 immediately followed by and reg,0x1) on a
            register holding a block+0 value.
    WRITE = or/and/xor reg,0x20|0xffffffdf on such a register AND a later store of reg back
            to block+0 (direct disp or via a lea'd pointer); or a direct memory op."""
    readfns, writefns, readhits, writehits = set(), set(), [], []
    for fn in sorted(fnwith):
        body = [a for a in ADDRS if owner(a) == fn]
        for a in body:
            mn = INS[a][0]
            ops = split_ops(INS[a][1])
            if not ops:
                continue
            r = ops[0].strip()
            if mn in ("test", "bt") and (re.search(r",0x20\b", INS[a][1]) or re.search(r",0x5\b", INS[a][1])) \
                    and holds_blk0(a, r):
                readfns.add(fn)
                readhits.append((a, txt(a)))
            if mn == "shr" and re.search(r",0x5\b", INS[a][1]) and holds_blk0(a, r):
                nxt = [x for x in body if x > a][:1]
                if nxt and INS[nxt[0]][0] == "and" and re.search(r",0x1\b", INS[nxt[0]][1]) \
                        and split_ops(INS[nxt[0]][1])[0].strip() == r:
                    readfns.add(fn)
                    readhits.append((a, txt(a) + " + " + txt(nxt[0])))
            if block0_disp(disp_of(ops[0])) and re.search(r",0x(20|ffffffdf)\b", INS[a][1]):
                writefns.add(fn)
                writehits.append((a, txt(a) + " (direct memory)"))
                continue
            if mn in ("or", "and", "xor") and (re.search(r",0x20\b", INS[a][1]) or re.search(r",0xffffffdf\b", INS[a][1])) \
                    and holds_blk0(a, r):
                stored = False
                for c in body:
                    if c <= a:
                        continue
                    cmn = INS[c][0]
                    cops = split_ops(INS[c][1])
                    if not cops:
                        continue
                    if cmn == "mov" and cops[1].strip() == r:
                        if block0_disp(disp_of(cops[0])):
                            stored = True
                            break
                        pm = re.fullmatch(r"(?:DWORD PTR )?\[(\w+)\]", cops[0].strip())
                        if pm:
                            p = pm.group(1)
                            j = AIDX[c]
                            while j > 0:
                                j -= 1
                                d = ADDRS[j]
                                if owner(d) != owner(a):
                                    break
                                dm = INS[d][0]
                                dop = split_ops(INS[d][1])
                                if dop and dop[0].strip() == p:
                                    if dm == "lea" and any(block0_disp(disp_of(o)) for o in dop[1:]):
                                        stored = True
                                    break
                        if stored:
                            break
                    if cmn == "call":
                        break
                if stored:
                    writefns.add(fn)
                    writehits.append((a, txt(a) + " -> stored back to block+0"))
    return sorted(readfns), sorted(writefns), readhits, writehits


def main():
    apply_patch()
    rows, gates = [], []
    fnbody = wbody(LOOP)
    p1 = wbody(LOOP, lo=LOOP_TOP, hi=LOOP_END)      # loop body incl. the bottom block
    p1c = wbody(LOOP, lo=LOOP_TOP, hi=CHARGE_END)   # the charge path (halving included)
    cb = wbody(COST)

    # ---------------------------------------------------------- G1 the loop = an ITEM id
    init = find(fnbody, "mov", r"\besi,0x1\b")   # prologue: the counter is initialised once, before the loop top
    bound = find(p1, "cmp", r"\besi,0x22\b")
    skipj = find(p1, "jg", r"0x4f4a34\b")
    incs = find(p1, "inc", r"\besi\b")
    rng = find(p1, "cmp", r"\besi,0x27\b")
    back = find(p1, "jl", r"0x4f480b\b")
    reads = reads_at(p1, ITEM_UPKEEP)
    fold = [(a, fold48(a)) for a, op in reads]
    leaves = sorted({lf for a, (lf, det) in fold if lf})
    disa_cmp = find(p1, "cmp", r"\[eax\],esi\b")
    rows.append("G1 loop top=%x bottom=%x body insns=%d (exit = fall-through past the jl)" %
                (LOOP_TOP, LOOP_BOTTOM, len(p1)))
    rows.append("G1 counter: init=%s charge-bound=%s skip-to-bottom=%s incs=%s range-bound=%s back-edge=%s" %
                ([txt(a) for a in init], [txt(a) for a in bound], [txt(a) for a in skipj],
                 [txt(a) for a in incs], [txt(a) for a in rng], [txt(a) for a in back]))
    rows.append("G1 item-table reads=%s fold=%s leaves=%s" %
                ([("%x %s" % (a, op)) for a, op in reads],
                 [("%x -> %s" % (a, lf if lf else det)) for a, (lf, det) in fold], leaves))
    for a, (lf, det) in fold:
        if lf:
            for c, t in det:
                rows.append("G1   fold step %s" % t)
    rows.append("G1 the SAME counter is compared against the per-faction disabled-item list: %s" %
                [txt(a) for a in disa_cmp])
    g1 = (len(init) == 1 and len(bound) == 1 and len(skipj) == 1 and len(incs) == 1
          and len(rng) == 1 and len(back) == 1
          and len(reads) == 1 and leaves == ["esi"] and len(disa_cmp) == 1)
    gates.append(("G1 the loop counter (esi: init 1, charge bound 0x22 skips 35..38, one inc, range bound 0x27 back to the top) is the ITEM id - it folds x48 into the item table AND is the value compared against the disabled-item list", g1))

    # ------------------------------------------------ G2 two bodies, one law (cross-check)
    FEAT = {
        "read48": lambda b: [a for a, op in reads_at(b, ITEM_UPKEEP)],
        "item27": lambda b: find(b, "cmp", r"\besi,0x1b\b"),
        "disa_count": lambda b: [a for a, op in reads_at(b, DISA_COUNT)],
        "disa_ents": lambda b: [a for a, op in reads_at(b, DISA_ENTS)],
        "disa_type2": lambda b: find(b, "cmp", r"\[eax-0x20\],0x2\b"),
        "disa_item": lambda b: find(b, "cmp", r"\[eax\],(esi|eax)\b"),
        "half27sar": lambda b: find(b, "sar", r"\b(esi|edi),1\b"),
    }
    feat = {tag: {k: f(b) for k, f in FEAT.items()} for tag, b in (("loop", p1), ("cost", cb))}
    for k in FEAT:
        rows.append("G2 %-11s loop=%s cost=%s" % (k, [("%x" % a) for a in feat["loop"][k]],
                                                  [("%x" % a) for a in feat["cost"][k]]))
    f2 = fold48(feat["cost"]["read48"][0]) if feat["cost"]["read48"] else (None, "no read")
    aff1436 = [(tag, aff(feat[tag]["disa_count"][0], "eax")) for tag in ("loop", "cost") if feat[tag]["disa_count"]]
    rows.append("G2 cost-body fold48-leaf=%s; disabled-list record folds value_of=%s (%d = 0x%x B)" %
                (f2[0] if f2[0] else f2[1], [(t, v) for t, v in aff1436], DISA_STRIDE, DISA_STRIDE))
    g2 = (all(len(feat["loop"][k]) == 1 and len(feat["cost"][k]) == 1
             for k in ("read48", "item27", "disa_count", "disa_ents", "disa_type2", "disa_item"))
          and f2[0] == "esi" and all(v[1] == DISA_STRIDE for t, v in aff1436))
    gates.append(("G2 FUN_004f47f0's loop body and FUN_004f4760 are the SAME law: 6 features present in both, the same 48-fold on esi, and both fold the faction record to 1436 B", g2))

    # --------------------------------------------------- G3 what makes a slot COUNT (noun)
    mapcall = find(p1c, "call", r"0x507410\b")
    pushitem = [a for a in find(p1c, "push", r"\besi\b") if mapcall and a < mapcall[0]]
    bmap = reads_at(p1c, BASE_ITEMMAP)
    ownb = reads_at(p1c, BASE_OWNER_BYTE)
    andm = find(p1c, "and", r"\bal,\bcl\b")
    exitnomap = find(p1c, "je", r"0x4f4a34\b")
    f_bitmap = [(a, aff(a, (memref(op) or (0, 0, 0, "ecx"))[3] or (memref(op) or (0, 0, 0, "ecx"))[4])) for a, op in bmap]
    f_owner = [(a, aff(a, (memref(op) or (0, 0, 0, "ecx"))[3] or (memref(op) or (0, 0, 0, "ecx"))[4])) for a, op in ownb]
    rows.append("G3 charge-path window=[%x,%x): mapper-call=%s counter-push-before-it=%s bitmap-byte-read=%s owner-byte-read=%s mask-and=%s not-having-skip=%s" %
                (LOOP_TOP, CHARGE_END, [txt(a) for a in mapcall], [txt(a) for a in pushitem],
                 [("%x %s" % (a, op)) for a, op in bmap],
                 [("%x %s" % (a, op)) for a, op in ownb], [txt(a) for a in andm], [txt(a) for a in exitnomap]))
    rows.append("G3 folds value_of: bitmap %s | owner-byte %s" % (f_bitmap, f_owner))
    rows.append("G3 record base derived two ways: 0x%x-0x8c=0x%x and 0x%x-4=0x%x; item bitmap at base+0x%x, owner byte at base+0x4, stride 304" %
                (BASE_ITEMMAP, BASE_ITEMMAP - 0x8C, BASE_OWNER_BYTE, BASE_ARRAY, BASE_ITEMMAP - BASE_ARRAY))
    g3 = (len(mapcall) == 1 and len(pushitem) == 1 and len(bmap) == 1 and len(ownb) == 1
          and len(andm) == 1 and len(exitnomap) == 1
          and f_bitmap and f_bitmap[0][1][1] == 304 and f_owner and f_owner[0][1][1] == 304
          and BASE_ITEMMAP - BASE_ARRAY == 0x8C and BASE_OWNER_BYTE - BASE_ARRAY == 4)
    gates.append(("G3 a slot is charged only when its BIT is set in the current base's 304-B record (304*[ds:0x68cbb0] + 0x8c) - the slot is a facility the base HAS, not a queue position", g3))

    # ------------------------------------------- G4 bit5 of the owner block's dword 0 = carry
    seq = {
        "own_src": find(fnbody, "mov", r"\beax,ds:0x%x\b" % CURR_REC),
        "own_byte": find(fnbody, "mov", r"\bbl,BYTE PTR \[eax\+0x4\]"),
        "load_blk0": [(a, op) for a, op in reads_at(p1c, BLKBASE) if INS[a][0] == "mov"],
        "lea_blk0": [(a, op) for a, op in reads_at(p1c, BLKBASE) if INS[a][0] == "lea"],
        "shr5": find(p1c, "shr", r"\bedi,0x5\b"),
        "and1": find(p1c, "and", r"\bedi,0x1\b"),
        "addcarry": find(p1c, "add", r"\beax,edi\b"),
        "parity": find(p1c, "test", r"\bal,0x1\b"),
        "bitset": find(p1c, "or", r"\becx,0x%x\b" % CIMM),
        "bitclr": find(p1c, "and", r"\becx,0x%x\b" % CCLR),
        "store": find(p1c, "mov", r"DWORD PTR \[edx\],ecx\b"),
        "quot": find(p1c, "sar", r"\beax,1\b"),
    }
    for k in ("own_src", "own_byte", "shr5", "and1", "addcarry", "parity", "bitset", "bitclr", "store", "quot"):
        for a in seq[k]:
            rows.append("G4 %-10s %s" % (k, txt(a)))
    foldvals = {}
    for k in ("load_blk0", "lea_blk0"):
        for a, op in seq[k]:
            foldvals[a] = aff(a, "edx")
            rows.append("G4 %-10s %s   value_of(edx)=%s" % (k, txt(a), foldvals[a]))
    between = []
    if seq["shr5"] and seq["store"]:
        lo, hi = seq["shr5"][0], seq["store"][0]
        between = [(a, INS[a][0], INS[a][1]) for a in ADDRS if lo < a < hi
                   and split_ops(INS[a][1]) and split_ops(INS[a][1])[0].strip() == "ecx"
                   and INS[a][0] in m326.STORE_MN]
    rows.append("G4 ecx writes between the bit-5 read and the store=%s (only the parity pair may touch ecx)" %
                [("%06x %s %s" % (a, mn, ops)) for a, mn, ops in between])
    foldleaf = sorted({v[3][1] for v in foldvals.values() if v[0] == "lin" and v[3][0] == "arg"})
    order = [seq[k][0] for k in ("shr5", "and1", "addcarry", "parity", "bitset", "bitclr", "store", "quot") if seq[k]]
    rows.append("G4 sequence monotonic=%s %s" % (order == sorted(order), [("%x" % a) for a in order]))
    g4 = (len(seq["own_src"]) == 1 and len(seq["own_byte"]) == 1
          and all(len(seq[k]) == 1 for k in ("shr5", "and1", "addcarry", "parity", "bitset", "bitclr", "store", "quot"))
          and len(seq["load_blk0"]) == 1 and len(seq["lea_blk0"]) == 1
          and order == sorted(order) and all(x[1] in ("or", "and") for x in between)
          and all(v[1] == BLKSTRIDE // 4 and v[3] == ("arg", "ebx") for v in foldvals.values())
          and foldleaf == ["ebx"])
    gates.append(("G4 the carry address folds 2095*ebx (x4 = 8380*ebx) onto block[owner]+0 with the OWNER from BYTE[[ds:0x8f0d60]+4] (prologue, once) - never the item id - and the order is read-bit5, add, test-parity, set/clear-bit5, store, quotient", g4))

    # --------------------------------------- G5 that bit-5 pair is exclusive to this function
    blk = set()
    for a in ADDRS:
        for op in split_ops(INS[a][1]):
            if block0_disp(disp_of(op)):
                blk.add(a)
                break
    blk = sorted(blk)
    fnwith = {}
    for a in blk:
        fnwith.setdefault(owner(a), []).append(a)
    readfns, writefns, readhits, writehits = bit5_census(fnwith)
    stores = [a for a in blk if any(mn in m326.STORE_MN and split_ops(INS[a][1]) and memref(split_ops(INS[a][1])[0])
                                    and block0_disp(disp_of(split_ops(INS[a][1])[0]))
                                    for mn in [INS[a][0]])]
    rows.append("G5 block+0 sites image-wide that NAME the address: %d (of them %d store the dword) in %d functions" % (len(blk), len(stores), len(fnwith)))
    for a, t in readhits:
        rows.append("G5   bit5 READ  %s" % t)
    for a, t in writehits:
        rows.append("G5   bit5 WRITE %s" % t)
    rows.append("G5 readfns=%s writefns=%s" % (readfns, writefns))
    near = [fn for fn in sorted(fnwith) if fn not in set(readfns) | set(writefns)
            and any(INS[a][0] in ("or", "and") and (re.search(r",0x20\b", INS[a][1]) or re.search(r",0xffffffdf\b", INS[a][1]))
                    for a in ADDRS if owner(a) == fn)]
    rows.append("G5 near-miss (0x20/0xffffffdf ops NOT on a block+0 value - e.g. FUN_004dc390 mirrors block+0 bits 30/29/20 into bits 4/5/6 of a DERIVED dword): %s" % near)
    g5 = (len(blk) > 20 and len(stores) >= 1 and readfns == ["FUN_004f47f0"] and writefns == ["FUN_004f47f0"])
    gates.append(("G5 of the %d image-wide sites that name block+0, the ONLY function that reads bit5 of a block+0 value AND the only one that writes it is FUN_004f47f0 - block+0 bit5 is a DEDICATED carry, not a shared flag" % len(blk), g5))

    # ------------------------------------------------ G6 whose base decides (ds:0x985ba0)
    wsel, rsel = [], []
    for a in ADDRS:
        parts = split_ops(INS[a][1])
        if not parts:
            continue
        d = memref(parts[0])
        dd = (d[1] if d[0] == "abs" else d[2]) if d else None
        if dd == SEL_BASE and INS[a][0] in m326.STORE_MN:
            wsel.append(a)
            continue
        for op in parts:
            e = memref(op)
            ee = (e[1] if e[0] == "abs" else e[2]) if e else None
            if ee == SEL_BASE:
                rsel.append(a)
                break
    cond = {"sel_load": [a for a, op in reads_at(p1c, SEL_BASE)],
            "ownerbyte_of_sel": [a for a, op in reads_at(p1c, BASE_OWNER_BYTE)],
            "cmp_owner": find(p1c, "cmp", r"\bedx,ebx\b"),
            "sete": find(p1c, "sete", r"\bcl\b"),
            "skip_owner": find(p1c, "je", r"0x4f4938\b"),
            "skip_sign": find(p1c, "jl", r"0x4f4938\b")}
    rows.append("G6 0x%x image-wide: stores=%d loads=%s owners=%s" %
                (SEL_BASE, len(wsel), [txt(a) for a in rsel], sorted({owner(a) for a in rsel})))
    for k, v in cond.items():
        rows.append("G6 %-16s %s" % (k, [txt(a) for a in v]))
    selaff = [aff(a, "ecx") for a in cond["ownerbyte_of_sel"]]
    rows.append("G6 selected-base record fold value_of=%s -> 304 * [ds:0x%x] is the SAME 304-B base record type" % (selaff, SEL_BASE))
    g6 = (len(wsel) == 0 and len(rsel) == 2 and all(len(cond[k]) == 1 for k in cond)
          and selaff and selaff[0][1] == 304)
    gates.append(("G6 ds:0x%x is READ-ONLY in .text (2 loads, 0 stores image-wide; writer outside .text) and the halving is gated on that base's owner byte == the charged base's owner (cmp/sete/je) plus a sign test (jl) - 2 distinct skips out of the halving" % SEL_BASE, g6))

    # -------------------------------------------------- G7 the loop range vs the table rows
    row1872 = [a for a in ADDRS if re.search(r"\b0x750\b", INS[a][1])]
    visited = list(range(1, TABLE_ROWS))
    charged = list(range(1, 0x22 + 1))
    never = [i for i in range(TABLE_ROWS) if i not in charged]
    rowdiff = ITEM_UPKEEP - ITEM_ROW0
    rows.append("G7 0x750 (=1872) occurs %d times in .text (first %s); 1872//%d=%d 1872%%%d=%d; loop VISITS ids 1..38 (bottom bound 0x27), CHARGES ids 1..34 (top bound 0x22 skips 35..38); never charged %s; upkeep dword at row+0x%x" %
                (len(row1872), ["%06x@%s" % (a, owner(a)) for a in row1872[:4]], ROW, 1872 // ROW, ROW, 1872 % ROW, never, rowdiff))
    g7 = (len(row1872) >= 1 and 1872 // ROW == TABLE_ROWS and 1872 % ROW == 0
          and 0x27 == TABLE_ROWS and never == [0] + list(range(35, TABLE_ROWS)) and rowdiff == 0x10)
    gates.append(("G7 the table is %d rows (1872 = 39*48 read out of .text); the loop visits ids 1..38 but ids 35..38 skip the charge body at the top bound and id 0 is never visited: only ids 1..34 are charged" % TABLE_ROWS, g7))

    # ------------------------------------------------ NEW FINDING (printed, not gated)
    rem = {"mapper2": find(wbody(LOOP, lo=CHARGE_END), "call", r"0x507410\b"),
           "bitclear": find(wbody(LOOP, lo=CHARGE_END), "mov", r"BYTE PTR \[eax\],cl\b"),
           "store_block220": find(wbody(LOOP, lo=CHARGE_END), "mov", r"DWORD PTR \[edi\+0x94d650\],eax\b")}
    rows.append("NF removal path inside the same loop (OPEN LEAD, not gated): %s" %
                {k: [txt(a) for a in v] for k, v in rem.items()})

    # ------------------------------------------------------------------- RIVALS (must fail)
    skips = cond["skip_owner"] + cond["skip_sign"]
    R1 = not (len(init) == 1 and INS[init[0]][1] == "esi,0x1")   # "the counter is 0-based over the whole table"
    R2 = len(set(readfns) | set(writefns)) > 1                    # "bit5 of block+0 is a shared faction flag"
    R3 = len(skips) == 0                                          # "the halving is unconditional"
    R4 = "esi" in foldleaf                                        # "the carry is per-item, not per-faction"
    R5 = len([a for a, op in reads_at(p1c, ITEM_UPKEEP)]) == 0    # "the cost does not come from the item table"
    rows.append("R rivals hold: R1(0-based-whole-table)=%s R2(bit5-shared-flag)=%s R3(unconditional-halving)=%s R4(per-item-carry)=%s R5(cost-not-from-item-table)=%s" % (R1, R2, R3, R4, R5))
    rows.append("R support: skips-to-full-price=%s carry-leaf=%s charged=1..34 rows=%d bit5-fns=%d table-reads=%d" %
                ([("%06x %s %s" % (a, INS[a][0], INS[a][1])) for a in skips], foldleaf, TABLE_ROWS,
                 len(set(readfns) | set(writefns)), len(reads)))
    gates.append(("RIVAL all five rivals FAIL on the printed numbers", not (R1 or R2 or R3 or R4 or R5)))

    print("\n".join(rows))
    print()
    npass = sum(1 for _, ok in gates if ok)
    for name, ok in gates:
        print(("PASS " if ok else "FAIL ") + name)
    print("digest(rows)=%s patch=%r patches_applied=%d" % (hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:16],
                                                           os.environ.get("M333_PATCH", ""), _npatch))
    print("%s M333: %d/%d gates" % ("PASS" if npass == len(gates) else "FAIL", npass, len(gates)))
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
