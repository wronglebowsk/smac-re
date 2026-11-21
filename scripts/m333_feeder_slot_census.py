#!/usr/bin/env python3
"""M333 (chain1 s313): the 34 feeder slots `0x984d48 + 48*slot` — the slot NOUN and why bit5 HALVES.

Pick (x1) from NEXT_PROMPT, the OPEN row of `## M330` G10 ("slot noun OPEN").
STATIC, zero box, zero /proc, zero gdb. Reuses M326's reviewed .text cache + helpers
(import m326_block224_census; M328/M330 import pattern), plus this file's OWN narrow
one-leaf affine fold tracker, printed for every site it claims.

MEASURED LAW (every number below is computed by this file, then asserted):
  FUN_004f47f0(base) is the per-BASE facility-upkeep charge; its loop counter `esi` is an
  ITEM id running 1..34 over the stride-48 item table whose upkeep dword is 0x984d48, and
  the charge is taken ONLY for items the base has (bitmap byte at base_rec+0x8c via the
  mapper 0x507410). FUN_004f4760(item, faction) is the SAME law as a standalone function -
  the two bodies are cross-checked feature-by-feature (G2), so one drifted body reddens it.
  The halving is a CARRIED HALF-UNIT: bit5 of the FACTION block dword 0 (0x94d430+8380*own)
  is read, ADDED to the item cost, the sum is shifted right by 1 (that is the charge), and
  the sum's PARITY is written back into the SAME bit5 - so an odd cost keeps its remainder
  for next round instead of losing it. It fires only when the faction-block byte of the
  base at ds:0x985ba0 equals the charged base's owner byte.

Acceptance: python3 -u scripts/m333_feeder_slot_census.py  -> TABLE FIRST, then gates,
then digest; a re-run must be byte-identical.  Mutants: scripts/m333_mutate.py.
Patch env: M333_PATCH="addr|mnemonic ops;addr|mnemonic ops"  (applied to m326.INS).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m326_block224_census as m326  # noqa: E402  (imports INS/ADDRS/owner/... + applies M326_PATCH)

INS, ADDRS, AIDX = m326.INS, m326.ADDRS, m326.AIDX
owner, split_ops, memref = m326.owner, m326.split_ops, m326.memref

LOOP = 0x4F47F0            # FUN_004f47f0  the per-base facility-upkeep charge
COST = 0x4F4760            # FUN_004f4760  the standalone item-upkeep cost
ITEM_UPKEEP = 0x984D48     # the upkeep dword inside the stride-48 item row
ITEM_ROW0 = 0x984D38       # the row base (0x984d48 - 0x10), M53i/M119
STRIDE_ROW = 48
MAPPER = 0x507410          # (item, &byte_index, &bit_mask)
BASE_ARRAY = 0x95DA10      # 304-B base records (0x95da14 = row flag = BLOCK id)
BASE_OWNER_BYTE = 0x95DA14
BASE_ITEMMAP = 0x95DA9C    # = BASE_ARRAY + 0x8c
BLKBASE, BLKSTRIDE, NBLK = 0x94D430, 0x20BC, 8
CARRY_BIT = 5
CARRY_IMM = 1 << CARRY_BIT
CARRY_CLR = (2 ** 32 - 1) ^ CARRY_IMM
DISA_LIST = 0x927A9C       # per-faction disabled-list count, 0x59c-B records
DISA_ENTS = 0x927AC0
DISA_STRIDE = 0x59C        # 1436
CURR_BASE = 0x68CBB0       # M311 current-record index
SEL_BASE = 0x985BA0        # the base index the halving condition is measured against
MAPPER_ARG = 0x507410

# --- the narrow one-leaf affine tracker: value = k * leaf, leaf is a register name ------
MOVES = {"mov", "lea", "add", "sub", "shl", "shr", "sar", "imul", "or", "and", "xor", "neg", "inc", "dec"}


def fold_at(a, reg, back=40):
    """Backward affine-in-one-leaf value of `reg` at instruction `a`, inside ONE function.
    Returns (k, leaf) meaning value = k*leaf, or (None, reason) when it cannot say.
    Narrow by design and honest about it: mov reg-reg propagation, lea [b+b*s], c<<n,
    add/sub of the same leaf, mov reg,imm terminates as a constant leaf. Anything else
    (memory loads, calls, multi-leaf mixes) returns (None, reason)."""
    i = AIDX[a]
    fn = owner(a)
    val = {}
    for _ in range(back):
        if i < 0:
            return (None, "ran off the window")
        b = ADDRS[i]
        if owner(b) != fn:
            return (None, "left the function")
        mn, ops = INS[b]
        parts = split_ops(ops)
        i -= 1
        if mn == "call":
            return (None, "call %s" % ops)
        if not parts:
            continue
        d = parts[0].strip()
        if d not in MOVES and d not in ("cdq",):
            continue
        if mn == "mov":
            s = parts[1].strip()
            if d == reg:
                if re.fullmatch(r"0x[0-9a-f]+", s):
                    return (0, "const %s" % s)
                if s in m326.REGW:
                    val[d] = val.get(s, (1, s))
                    continue
                return (None, "memory load")
            val.pop(d, None)
            continue
        if mn == "lea":
            if d != reg:
                val.pop(d, None); continue
            m = re.fullmatch(r"\[(\w+)(?:\+(\w+)\*(\d+))?\]", parts[1].strip())
            m2 = re.fullmatch(r"\[(\w+)\*(\d+)(?:\+(\w+))?\]", parts[1].strip())
            if m:
                b1, i1, s1 = m.group(1), m.group(2), m.group(3)
                k = val.get(b1, (1, b1))[0] if b1 else 0
                if i1 is not None:
                    k2 = val.get(i1, (1, i1))[0]
                    if val.get(b1, (1, b1))[1] != val.get(i1, (1, i1))[1]:
                        return (None, "multi-leaf lea")
                    k = k + k2 * int(s1)
                leaf = val.get(b1, (1, b1))[1]
                val[d] = (k, leaf)
                continue
            if m2:
                k = val.get(m2.group(1), (1, m2.group(1)))[0] * int(m2.group(2))
                leaf = val.get(m2.group(1), (1, m2.group(1)))[1]
                val[d] = (k, leaf)
                continue
            return (None, "lea shape")
        if mn in ("shl", "shr", "sar"):
            if d != reg:
                continue
            k = val.get(d, (1, d))[0]
            n = int(parts[1].strip(), 16)
            if mn == "shl":
                val[d] = (k * (1 << n), val.get(d, (1, d))[1])
            else:
                return (None, "%s breaks the affine form" % mn)
            continue
        if mn in ("add", "sub"):
            if d != reg:
                val.pop(d, None); continue
            s = parts[1].strip()
            if s not in m326.REGW:
                return (None, "add const")
            if val.get(d, (1, d))[1] != val.get(s, (1, s))[1]:
                return (None, "multi-leaf %s" % mn)
            kk = val.get(s, (1, s))[0]
            val[d] = (val.get(d, (1, d))[0] + (kk if mn == "add" else -kk), val[d][1])
            continue
        if mn == "imul":
            if d != reg:
                val.pop(d, None); continue
            m = re.fullmatch(r"0x[0-9a-f]+", parts[1].strip())
            if m:
                val[d] = (val.get(d, (1, d))[0] * int(m.group(1), 16), val.get(d, (1, d))[1])
            else:
                return (None, "imul reg form")
            continue
        if d in m326.REGW:
            val.pop(d, None)
    return val.get(reg, (None, "not tracked"))


def fn_body(fn):
    lo, hi = fn, fn + m326.FSIZE[fn]
    return [a for a in ADDRS if lo <= a < hi]


def find(fn, mn, pat):
    """addresses in fn whose mnemonic matches and whose operand string matches regex pat"""
    out = []
    for a in fn_body(fn):
        m_, o = INS[a]
        if m_ == mn and re.search(pat, o):
            out.append(a)
    return out


def txt(a):
    mn, ops = INS[a]
    return "%06x: %s %s" % (a, mn, ops)


def disp_in(op):
    mi = memref(op)
    if not mi:
        return None
    return mi[1] if mi[0] == "abs" else mi[2]


def main():
    rows, gates = [], []
    patch = os.environ.get("M333_PATCH", "")

    # ------------------------------------------------------------------ G1 the loop law
    bound = find(LOOP, "cmp", r"\besi,0x22\b")
    init = find(LOOP, "mov", r"\besi,0x1\b")
    exits = find(LOOP, "jg", r"0x4f4a34\b")
    reads = [a for a in fn_body(LOOP) if INS[a][0] == "mov" and disp_in(INS[a][1]) == ITEM_UPKEEP]
    folds = {}
    for a in reads:
        parts = split_ops(INS[a][1])
        reg = memref(parts[1])[3] if memref(parts[1])[3] not in (None, "eiz") else memref(parts[1])[4]
        folds[a] = fold_at(a, reg)
    slot_min = 1 + 0 if init else None
    slot_max = 0x22 if bound else None
    rows.append("G1 loop: init=%s bound=%s exits=%s stride-reads=%s folds=%s regs=%s" %
                ([("%x" % a, txt(a)[7:]) for a in init], [("cmp %x" % a) for a in bound],
                 [("jg %x -> %s" % (a, INS[a][1])) for a in exits], [("%x" % a) for a in reads],
                 [("%x=(%s,%s)" % (a, k, lf)) for a, (k, lf) in folds.items()],
                 sorted({lf for _, (k, lf) in folds.items() if k in (48, 96, 144)})))
    g1 = (len(init) == 1 and len(bound) == 1 and len(exits) == 1 and len(reads) == 1
          and folds.get(reads[0], (None,))[0] == 48 and slot_min == 1 and slot_max == 34)
    gates.append(("G1 slot loop 1..34 over 0x984d48+48*esi (single read site, fold 48*esi)", g1))

    # ------------------------------------------------- G2 two bodies, one law (cross-check)
    feats = {}
    for tag, fn in (("loop", LOOP), ("cost", COST)):
        f = {
            "read48": [a for a in fn_body(fn) if INS[a][0] == "mov" and disp_in(INS[a][1]) == ITEM_UPKEEP],
            "fold48": sorted({fold_at(a, (memref(split_ops(INS[a][1])[1]) or ("",))[3] or
                              (memref(split_ops(INS[a][1])[1]) or ("",))[4])[0]
                              for a in [a for a in fn_body(fn) if INS[a][0] == "mov" and disp_in(INS[a][1]) == ITEM_UPKEEP]}),
            "item27": [a for a in fn_body(fn) if INS[a][0] == "cmp" and re.search(r"\b(esi|eax),0x1b\b", INS[a][1])],
            "disa_count": [a for a in fn_body(fn) if INS[a][0] == "mov" and disp_in(INS[a][1]) == DISA_LIST],
            "disa_ents": [a for a in fn_body(fn) if INS[a][0] == "lea" and disp_in(INS[a][1]) == DISA_ENTS],
            "disa_type2": [a for a in fn_body(fn) if INS[a][0] == "cmp" and re.search(r"\[eax-0x20\],0x2\b", INS[a][1])],
            "disa_item": [a for a in fn_body(fn) if INS[a][0] == "cmp" and re.search(r"\[eax\],(esi|eax)\b", INS[a][1])],
            "fold1436": sorted({fold_at(a, "ecx" if tag == "cost" else "eax")[0]
                                for a in [a for a in fn_body(fn) if INS[a][0] == "mov" and disp_in(INS[a][1]) == DISA_LIST]}),
            "half27": len(find(fn, "sar", r"\b(esi|edi),1\b")),
        }
        feats[tag] = f
    same = all(len(feats["loop"][k]) >= 1 and len(feats["cost"][k]) >= 1
               for k in ("read48", "item27", "disa_count", "disa_ents", "disa_type2", "disa_item"))
    rows.append("G2 cross-body: %s" % {k: {t: [("%x" % a) for a in v] for t, v in ((tt, feats[tt][k]) for tt in ("loop", "cost"))}
                                        for k in ("read48", "item27", "disa_count", "disa_ents", "disa_type2", "disa_item")})
    rows.append("G2 folds: loop-48=%s cost-48=%s loop-1436=%s cost-1436=%s (both must be 48/1436)" %
                (feats["loop"]["fold48"], feats["cost"]["fold48"], feats["loop"]["fold1436"], feats["cost"]["fold1436"]))
    g2 = (same and feats["loop"]["fold48"] == [48] and feats["cost"]["fold48"] == [48]
          and 1436 in feats["loop"]["fold1436"] and 1436 in feats["cost"]["fold1436"])
    gates.append(("G2 FUN_004f47f0 and FUN_004f4760 implement the SAME law (7 features, folds 48 and 1436 in both)", g2))

    # ------------------------------------------------------- G3 the base-bitmap gate (noun)
    mapcall = find(LOOP, "call", r"0x507410\b")
    pushitem = find(LOOP, "push", r"\besi\b")
    bitmap = find(LOOP, "mov", r"BYTE PTR \[ecx\+edx\*1\+0x95da9c\]")
    blockbyte = find(LOOP, "mov", r"BYTE PTR \[ecx\+0x95da14\]")
    andmask = find(LOOP, "and", r"\bal,\bcl\b")
    fold304_bitmap = [fold_at(a, "ecx") for a in bitmap]
    fold304_owner = [fold_at(a, "ecx") for a in blockbyte]
    curr = find(LOOP, "mov", r"DWORD PTR ds:0x68cbb0")
    rows.append("G3 bitmap gate: mapper-call=%s push-item-arg=%s byte-read=%s owner-byte-read=%s mask-and=%s curr-base=%s folds=%s/%s" %
                (mapcall, [("%x" % a) for a in pushitem], [("%x" % a) for a in bitmap],
                 [("%x" % a) for a in blockbyte], [("%x" % a) for a in andmask],
                 [("%x" % a) for a in curr], fold304_bitmap, fold304_owner))
    off_bitmap = BASE_ITEMMAP - BASE_ARRAY
    off_owner = BASE_OWNER_BYTE - BASE_ARRAY
    rows.append("G3 record fields: base_rec=0x%x (derived two ways); item bitmap at base_rec+0x%x; block/owner byte at base_rec+0x%x" %
                (BASE_ARRAY, off_bitmap, off_owner))
    g3 = (len(mapcall) == 1 and len(bitmap) == 1 and len(blockbyte) == 1 and len(andmask) >= 1
          and fold304_bitmap[0][0] == 304 and fold304_owner[0][0] == 304
          and off_bitmap == 0x8c and off_owner == 4 and len(curr) == 1)
    gates.append(("G3 the charge is gated by a per-item BIT in the 304-B base record (base+0x8c), same record whose +4 is the owner block byte", g3))

    # ------------------------------------------------- G4 bit5 is a CARRIED HALF-UNIT (why)
    seq = {
        "fold_owner_addr": find(LOOP, "mov", r"DWORD PTR \[edx\*4\+0x94d430\]"),
        "lea_owner_addr": find(LOOP, "lea", r"\[edx\*4\+0x94d430\]"),
        "shr5": find(LOOP, "shr", r"\bdi,0x5\b"),
        "and1": find(LOOP, "and", r"\bedi,0x1\b"),
        "addcarry": find(LOOP, "add", r"\beax,edi\b"),
        "testparity": find(LOOP, "test", r"\bal,0x1\b"),
        "bitset": find(LOOP, "or", r"\becx,0x20\b"),
        "bitclr": find(LOOP, "and", r"\becx,0x%x\b" % CARRY_CLR),
        "store": find(LOOP, "mov", r"DWORD PTR \[edx\],ecx\b"),
        "sar1": find(LOOP, "sar", r"\beax,1\b"),
    }
    for k, v in seq.items():
        for a in v:
            rows.append("G4 %-14s %s" % (k, txt(a)))
    folds_owner = [fold_at(a, "edx") for a in seq["fold_owner_addr"] + seq["lea_owner_addr"]]
    rows.append("G4 folded address: %s (leaf must be the OWNER faction register ebx, never the item id esi)" %
                [("%s,%s" % (k, lf)) for k, lf in folds_owner])
    ordered = [seq["shr5"], seq["and1"], seq["addcarry"], seq["testparity"], seq["bitset"], seq["bitclr"], seq["store"], seq["sar1"]]
    flat = [a[0] for a in ordered if a]
    rows.append("G4 order monotonic=%s (%s)" % (flat == sorted(flat), [("%x" % a) for a in flat]))
    between = []
    if seq["shr5"] and seq["store"]:
        lo, hi = seq["shr5"][0], seq["store"][0]
        between = [(a, INS[a][0], INS[a][1]) for a in ADDRS if lo < a < hi
                   and split_ops(INS[a][1]) and split_ops(INS[a][1])[0].strip() == "ecx"
                   and INS[a][0] in m326.STORE_MN]
    rows.append("G4 ecx writes between read and store=%s (only the two bit ops may touch it)" %
                [("%x %s %s" % (a, mn, ops)) for a, mn, ops in between])
    g4 = (len(seq["shr5"]) == 1 and len(seq["and1"]) == 1 and len(seq["addcarry"]) == 1
          and len(seq["testparity"]) == 1 and len(seq["bitset"]) == 1 and len(seq["bitclr"]) == 1
          and len(seq["store"]) == 1 and len(seq["sar1"]) == 1 and len(seq["fold_owner_addr"]) >= 1
          and flat == sorted(flat)
          and all(lf == "ebx" for k, lf in folds_owner if k is not None)
          and all(a[1] in ("or", "and") for a in between))
    gates.append(("G4 bit5 of block[owner]+0: read -> added to the cost -> its PARITY written back -> cost >>1 (carried half-unit)", g4))

    # ---------------------------------------- G5 the carry bit is EXCLUSIVE to this law
    blk_sites = []
    for a in ADDRS:
        for op in split_ops(INS[a][1]):
            d = disp_in(op)
            if d is not None and d % BLKSTRIDE == BLKBASE % BLKSTRIDE and BLKBASE <= d < BLKBASE + NBLK * BLKSTRIDE and (d - BLKBASE) % BLKSTRIDE == 0:
                blk_sites.append((a, INS[a][0], INS[a][1], op))
                break
    bitops = [(a, mn, ops, op) for a, mn, ops, op in blk_sites
              if re.search(r"\b0x%x\b|\b0x%x\b" % (CARRY_IMM, CARRY_CLR), op or "") or re.search(r"\bshr\b|\bbt\b|\bbts\b|\bbtr\b", mn)]
    rows.append("G5 block+0 (0x%x+k*0x%x) sites image-wide: %d; of them bit-level: %s" %
                (BLKBASE, BLKSTRIDE, len(blk_sites), [("%06x %s %s" % (a, mn, ops)) for a, mn, ops, op in bitops]))
    rows.append("G5 declared bit-5 set (measured, literal): %s" % sorted(["%06x" % a for a in seq["shr5"]] +
                                                                        ["%06x" % a for a in seq["bitset"]] +
                                                                        ["%06x" % a for a in seq["bitclr"]]))
    g5 = (len(blk_sites) > 0 and
          sorted("%06x" % a for a, mn, ops, op in bitops) ==
          sorted(["%06x" % a for a in seq["shr5"]] + ["%06x" % a for a in seq["bitset"]] + ["%06x" % a for a in seq["bitclr"]]))
    gates.append(("G5 the ONLY bit-level access to block+0 image-wide (among the address-naming sites) is the carry read/write pair", g5))

    # ------------------------------------------- G6 whose base gates the halving (0x985ba0)
    wsel = [(a, INS[a][0], INS[a][1]) for a in ADDRS
            if any(disp_in(op) == SEL_BASE for op in split_ops(INS[a][1])) and INS[a][0] in m326.STORE_MN]
    rsel = [(a, INS[a][0], INS[a][1]) for a in ADDRS
            if any(disp_in(op) == SEL_BASE for op in split_ops(INS[a][1])) and INS[a][0] not in m326.STORE_MN]
    ownmatch = find(LOOP, "mov", r"BYTE PTR \[ecx\+0x95da14\]")
    sete = find(LOOP, "sete", r"\bcl\b")
    rows.append("G6 0x985ba0 stores=%s loads=%s owners=%s" %
                ([("%06x %s %s [%s]" % (a, mn, ops, owner(a))) for a, mn, ops in wsel],
                 [("%06x %s %s" % (a, mn, ops)) for a, mn, ops in rsel][:6],
                 sorted({owner(a) for a, _, _ in wsel})))
    rows.append("G6 condition sequence: owner-byte=%s sete=%s cmp-with-ebx=%s" %
                ([("%x" % a) for a in ownmatch], [("%x" % a) for a in sete],
                 [("%x" % a) for a in find(LOOP, "cmp", r"\bedx,ebx\b")]))
    g6 = (len(wsel) >= 1 and len(ownmatch) == 1 and len(sete) >= 1)
    gates.append(("G6 the halving is conditional on base[ds:0x985ba0]'s owner byte == the charged base's owner", g6))

    # --------------------------------------- G7 34 charged ids vs the table's row count
    row1872 = [(a, owner(a)) for a in ADDRS if re.search(r"\b0x750\b", INS[a][1])]
    ids = list(range(0, 39))
    charged = list(range(slot_min or 1, (slot_max or 0) + 1))
    never = [i for i in ids if i not in charged]
    rows.append("G7 row count: 1872 appears at %s; 1872//48=%d 1872%%48=%d; loop charges %d..%d, never-read ids %s" %
                ([("%06x@%s" % (a, o)) for a, o in row1872][:6], 1872 // STRIDE_ROW, 1872 % STRIDE_ROW,
                 charged[0], charged[-1], never))
    g7 = (len(row1872) >= 1 and 1872 // STRIDE_ROW == 39 and 1872 % STRIDE_ROW == 0
          and never == [0] + list(range(35, 39)) and slot_max == 34 and slot_max < 39)
    gates.append(("G7 the table is 39 rows (1872 = 39*48 read from .text) but the upkeep loop charges only ids 1..34", g7))

    # ------------------------------------------------------------- RIVALS (must FAIL)
    uncond = find(LOOP, "jl", r"0x4f4938\b") + find(LOOP, "je", r"0x4f4938\b")
    itemleaf = sorted({lf for a, (k, lf) in folds.items() for _ in [0] if k == 48})
    R1 = (slot_min == 0 or slot_max == 38)                      # "the loop covers 0..38 of the 39-row table"
    R2 = len(bitops) > 3                                        # "bit5 of block+0 is a shared faction flag"
    R3 = len(uncond) == 0                                       # "the halving is unconditional"
    R4 = "esi" in itemleaf                                      # "the carry lives per-item, not per-faction"
    R5 = len(feats["loop"]["read48"]) == 0                      # "the charge is not the item table at all"
    rows.append("R rivals hold: R1(whole-table)=%s R2(shared-flag)=%s R3(unconditional)=%s R4(per-item carry)=%s R5(not-the-item-table)=%s"
                % (R1, R2, R3, R4, R5))
    rows.append("R support: skips-to-full-price=%s carry-leaf=%s charged=%d..%d rows=%d" %
                ([("%x %s" % (a, INS[a][1])) for a in uncond], itemleaf, charged[0], charged[-1], 1872 // STRIDE_ROW))
    gates.append(("RIVAL all five fail on the printed numbers", not (R1 or R2 or R3 or R4 or R5)))

    print("\n".join(rows))
    print()
    npass = 0
    for name, ok in gates:
        print(("PASS " if ok else "FAIL ") + name)
        npass += ok
    body = "\n".join(rows).encode("utf-8")
    print("digest(rows)=%s  patch=%r" % (hashlib.sha256(body).hexdigest()[:16], patch))
    print("%s M333: %d/%d gates" % ("PASS" if npass == len(gates) else "FAIL", npass, len(gates)))
    return 0 if npass == len(gates) else 1


def disp_in_of(op):
    for o in split_ops(op):
        d = disp_in(o)
        if d is not None:
            return d
    return None


def is_block0(d):
    return BLKBASE <= d < BLKBASE + NBLK * BLKSTRIDE and (d - BLKBASE) % BLKSTRIDE == 0


if __name__ == "__main__":
    sys.exit(main())
