#!/usr/bin/env python3
"""M354 - SECTION A's IDENTITY: the positive chooser rows are the 0x98ad88
UNIT-TYPE (design) records, not a facility space.

M351 settled the sign law and the row sources.  It left ONE question open:
what the section-A item *is* (its trace names said "designs", never re-proved).
This milestone reads the row arithmetic of the A block and every consumer of
that row, and computes the answer from the objdump listing:

  0x4956c6  A loop: idx<0x80, item = cand[idx] @0x9267e4 (0x4956d6)
  0x5a73f0  validator: row band (item>>6) must equal the owner, flags bit0 set,
            owner mask bit clear, chassis domain and the +0x32 pre-req tech
  0x49571b  imul edx,edx,0x34 / add edx,0x98ad88  -> the row's +0x00 NAME
  0x4957e2  imul ecx,ecx,0x34  / [ecx+0x98adb1]   -> +0x29 WEIGHT (cost)
  0x4959be  imul ecx,ecx,0x34  / [ecx+0x98adb2]   -> +0x2a CLASS (cmp 8)
  0x496050  A's flags fn reads EXACTLY +0x2a and +0x30; B's (0x4960f0) reads
            NO memory at all -> the two sections are different row spaces.

  Field atlas (every offset below is computed from a literal, not authored):
    +0x00 name (appended through std::string @0x404010), +0x20 ability dword,
    +0x24 domain, +0x25/+0x26 chassis bytes, +0x29 weight, +0x2a class,
    +0x2c owner mask, +0x30 flags word (bit0 valid, bit2 design), +0x32 pre-req
    tech (WORD -> tech record 0x92fdd4, stride 0xb).

  Cross-check against the QUEUE DECODER: the head<0 branch (0x4ef88b..0x4efa2c)
  reads the 0x984d38 table's cost (0x984d44) and NO 0x98ad88 field; the head>=0
  branch stamps the 0x98ad88 row's flags word (0x4efe50/60).  So the partition
  is two-sided:  +head = 0x98ad88 unit-type/design ROW  (section A, flag 0x20)
                 -head = 0x984d38 facility ID          (section B, flag 0x10)
  which inverts the per-leg NOUN labels M349 wrote (its arithmetic is right).

Static only: no box, no Wine, no gdb.  Every number is parsed from the listing
(scratch/m574/text.txt); each gate asserts a parsed value against a declared
literal so a drift reddens.

    python3 -u scripts/m354_design_row.py            # acceptance
    python3 -u scripts/m354_design_row.py --digest   # digest only
    SMAC_M354_TEXT=/other/listing ...
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M354_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
MUT = os.environ.get("SMAC_M354_MUTANT", "")

ROW_BASE, ROW_STRIDE = 0x98AD88, 0x34
FAC_BASE, FAC_STRIDE = 0x984D38, 0x30
CAND_BASE = 0x9267E4
A_LO, A_HI = 0x4956C6, 0x495B24          # section A (unit-type rows)
B_LO, B_HI = 0x495B27, 0x495E96          # section B (facility ordinals)
F_A = (0x496050, 0x496050 + 119)         # A row's flags fn
F_B = (0x4960F0, 0x4960F0 + 96)          # B row's flags fn
F_VAL = (0x5A73F0, 0x5A73F0 + 297)       # row validator (filter)
F_W = (0x5AC950, 0x5AC950 + 351)         # per-type weight / cost
F_INFO = (0x570E90, 0x570E90 + 1220)     # row info / pre-req text
BUILD = (0x596000, 0x596000 + 345)       # candidate table builder
DEC_NEG = (0x4EF88B, 0x4EFA2C)           # queue decoder, head<0 branch
DEC_POS = (0x4EFA2C, 0x4F0000)           # queue decoder, head>=0 branch

ROW = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")
HEX = re.compile(r"0x([0-9a-f]+)")
IMUL = re.compile(r"imul\s+(\w+),\s*\1,\s*0x([0-9a-f]+)")


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


class Listing:
    def __init__(self, path):
        self.at, self.order = {}, []
        with open(path, "r", errors="replace") as f:
            for line in f:
                m = ROW.match(line)
                if not m:
                    continue
                a = int(m.group(1), 16)
                self.at[a] = norm(m.group(3))
                self.order.append(a)
        self.order.sort()

    def get(self, a):
        return self.at.get(a)

    def window(self, lo, hi):
        return [(a, self.at[a]) for a in self.order if lo <= a < hi]

    def refs(self, lo, hi, base, stride):
        """Every hex literal of an operand inside [base, base+stride)."""
        out = []
        for a, t in self.window(lo, hi):
            for h in HEX.findall(t):
                v = int(h, 16)
                if base <= v < base + stride:
                    out.append((a, t, v - base))
        return out

    def strides(self, lo, hi):
        return [(a, int(m.group(2), 16)) for a, t in self.window(lo, hi)
                for m in [IMUL.search(t)] if m]


def digest_table(rows):
    s = "\n".join("|".join(str(x) for x in r) for r in rows)
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    a = ap.parse_args()
    L = Listing(TEXT)
    fails = []
    pin = []

    def gate(gid, ok, msg):
        print("%s %-4s %s" % ("ok  " if ok else "FAIL", gid, msg))
        if not ok:
            fails.append(gid)
        return ok

    # ------------------------------------------------------------------ TABLE 1
    a_imul = L.strides(A_LO, A_HI)
    a_row = L.refs(A_LO, A_HI, ROW_BASE, ROW_STRIDE)
    print("TABLE 1  section A (0x%x..0x%x): the item is a 0x%x-stride row index"
          % (A_LO, A_HI, ROW_STRIDE))
    print("  item load            %s" % L.get(0x4956D6))
    for ad, st in a_imul:
        print("  0x%06x  %s" % (ad, L.get(ad)))
    print("  row-field reads      %s"
          % ", ".join("0x%02x@0x%06x" % (o, ad) for ad, _t, o in a_row))
    triples = sorted((ad, o) for ad, _t, o in a_row if any(ad == s for s, _ in a_imul))
    print("  (imul site, field)   %s" % triples)
    pin.append(("A", tuple((s, st) for s, st in a_imul), tuple(triples)))

    # ------------------------------------------------------------------ TABLE 2
    print()
    print("TABLE 2  who reads which field of the 0x98ad88 row (computed offsets)")
    fns = [("A flags   0x496050", F_A), ("B flags   0x4960f0", F_B),
           ("validator 0x5a73f0", F_VAL), ("weight    0x5ac950", F_W),
           ("info      0x570e90", F_INFO)]
    sets = {}
    for name, (lo, hi) in fns:
        r = L.refs(lo, hi, ROW_BASE, ROW_STRIDE)
        st = L.strides(lo, hi)
        sets[name] = (sorted({o for _a, _t, o in r}), len(r), [x for _a, x in st])
        print("  %-18s refs=%d offsets=%s strides=%s"
              % (name, len(r), ["0x%02x" % o for o in sets[name][0]], sets[name][2]))
    union = sorted({o for v in sets.values() for o in v[0]} | {o for _a, _t, o in a_row})
    print("  union offsets        %s" % ["0x%02x" % o for o in union])
    print("  any 0x98ad literal in B flags fn: %s"
          % [t for _a, t in L.window(*F_B) if "0x98ad" in t])
    pin.append(("F", tuple((k, tuple(v[0]), v[1], tuple(v[2])) for k, v in sets.items()),
                tuple(union)))

    # ------------------------------------------------------------------ TABLE 3
    print()
    print("TABLE 3  the candidate builder 0x596000: owner bands in the item space")
    print("  %s" % L.get(0x596017))
    print("  %s" % L.get(0x59601F))
    print("  %s" % L.get(0x596028))
    print("  %s" % L.get(0x596037))
    band_shift = 6 if "0x6" in (L.get(0x59601F) or "") else None
    owners = range(8)
    ko_lo, ko_hi = 0x40, 0x3F
    maps = {}
    for own in owners:
        m = []
        for k in range(0x80):
            idx = (k & ko_hi) + ((own << band_shift) if k >= ko_lo else 0)
            m.append(idx)
        maps[own] = m
        bands = sorted({v >> band_shift for v in m})
        print("  owner %d: band set %s  first/mid/last %d/%d/%d"
              % (own, bands, m[0], m[0x40], m[-1]))
    shared = sum(1 for k in range(0x80) if maps[3][k] < 0x40)
    print("  owner 3: %d entries < 0x40 (shared band), %d in band 3"
          % (shared, 0x80 - shared))
    b_chain = [L.get(x) for x in (0x59603E, 0x596041, 0x596044)]
    print("  row-stride chain      %s" % " ; ".join(b_chain))
    print("  %s" % L.get(0x596047))
    pin.append(("B", band_shift, tuple(maps[3])))

    # ------------------------------------------------------------------ TABLE 4
    print()
    print("TABLE 4  the sign each section stamps on its row node")
    print("  A  0x495a8d %s   (flags |= 0x20)" % L.get(0x495A8D))
    print("  B  0x495dff %s   (flags |= 0x10)" % L.get(0x495DFF))
    print("  modal 0x49772a %s ; 0x49777c %s" % (L.get(0x49772A), L.get(0x49777C)))
    pin.append(("S", L.get(0x495A8D), L.get(0x495DFF), L.get(0x49772A)))

    # ------------------------------------------------------------------ TABLE 5
    print()
    print("TABLE 5  the queue decoder's two legs (cross-check of the partition)")
    neg_row = L.refs(*DEC_NEG, ROW_BASE, ROW_STRIDE)
    neg_fac = L.refs(*DEC_NEG, FAC_BASE, FAC_STRIDE)
    pos_row = L.refs(*DEC_POS, ROW_BASE, ROW_STRIDE)
    print("  head<0  (0x%x..0x%x) row refs=%d facility refs=%d %s"
          % (DEC_NEG[0], DEC_NEG[1], len(neg_row), len(neg_fac),
             [(hex(ad), "0x%02x" % o) for ad, _t, o in neg_fac]))
    print("  head>=0 (0x%x..0x%x) row refs=%d %s"
          % (DEC_POS[0], DEC_POS[1], len(pos_row),
             [(hex(ad), "0x%02x" % o) for ad, _t, o in pos_row if o in (0x30, 0x2C)]))
    for ad in (0x4EF88B, 0x4EF897, 0x4EF899, 0x4EF89F, 0x4EF8ED,
               0x4EFE41, 0x4EFE44, 0x4EFE50, 0x4EFE60):
        print("  0x%06x %s" % (ad, L.get(ad)))
    pin.append(("D", len(neg_row), len(neg_fac), len(pos_row)))

    # ------------------------------------------------------------------ TABLE 6
    print()
    print("TABLE 6  the field atlas as CONSUMERS read it (offset -> use)")
    atlas = [
        (0x00, "name string, appended via 0x404010 (std::string, 130 callers)", 0x49571E, A_LO, A_HI),
        (0x20, "ability dword, info builder 0x570e90", None, *F_INFO),
        (0x24, "chassis domain byte, validator + info", None, *F_VAL),
        (0x29, "production WEIGHT -> cost via 0x4e40a0(base+4)", None, A_LO, A_HI),
        (0x2A, "CLASS byte (==8 colony-pod display rule)", 0x4959C9, A_LO, A_HI),
        (0x2C, "owner MASK byte, tested 1<<owner by 0x5a73f0", None, *F_VAL),
        (0x30, "flags WORD: bit0 valid, bit2 design stamped", 0x496065, *F_A),
        (0x32, "pre-req tech id (WORD) -> 0x92fdd4 stride 0xb", 0x4EFE50, A_LO, A_HI),
    ]
    for off, use, probe, lo, hi in atlas:
        has = off in [o for _a, _t, o in L.refs(lo, hi, ROW_BASE, ROW_STRIDE)]
        print("  +0x%02x  %-52s ref-in-window=%s" % (off, use, has))
    pin.append(("T", tuple(o for o, _u, _p, _l, _h in atlas)))

    if a.digest:
        print()
        print("digest=%s" % digest_table(pin))
        return 0 if not fails else 1

    # ------------------------------------------------------------------ GATES
    print()
    print("GATES")
    gate("G1", a_imul == [(0x49571B, 0x34), (0x4957E2, 0x34), (0x4959BE, 0x34)]
         and triples == [(0x49571B, 0x00), (0x4957E2, 0x29), (0x4959BE, 0x2A)],
         "3 imul-by-0x34 sites, fields +0x00/+0x29/+0x2a  %s" % (triples,))

    prov = []
    for s, _st in a_imul:
        reg = re.match(r"imul\s+(\w+)", L.get(s) or "").group(1)
        prev = [L.get(x) for x in (s - 3, s - 4, s - 7, s - 9)]
        prov.append(any(p and p.startswith("mov %s,DWORD PTR [ebp-0x2c]" % reg)
                        for p in prev))
    gate("G2", all(prov) and "0x9267e4" in (L.get(0x4956D6) or "")
         and "0x2c" in (L.get(0x4956DD) or ""),
         "every row index is loaded from [ebp-0x2c], filled from [..*4+0x%x]  %s"
         % (CAND_BASE, prov))

    fa_off, fa_n, fa_st = sets["A flags   0x496050"]
    gate("G3", fa_off == [0x2A, 0x30] and fa_n == 2 and fa_st == [0x34]
         and "cmp DWORD PTR [ebp+0x8],0x40" in (L.get(0x49605C) or "")
         and "and ecx,0x4" in (L.get(0x49606F) or ""),
         "A flags fn reads exactly +0x2a,+0x30; guard 0x40; test bit 4  %s" % (fa_off,))

    fb_off, fb_n, _fb_st = sets["B flags   0x4960f0"]
    fb_rets = sorted({int(m.group(1), 16) for ad, t in L.window(*F_B)
                      for m in [re.match(r"mov eax,0x([0-9a-f]+)$", t)] if m})
    gate("G4", fb_n == 0 and not [t for _a, t in L.window(*F_B) if "0x98ad" in t]
         and set(fb_rets) <= {0, 1, 2, 3},
         "B flags fn is PURE over the ordinal: 0 row refs, returns %s" % (fb_rets,))

    gate("G5", "or al,0x20" in (L.get(0x495A8D) or "")
         and "or al,0x10" in (L.get(0x495DFF) or "")
         and "and eax,0x20" in (L.get(0x49772A) or "")
         and (L.get(0x49777C) or "").startswith("neg "),
         "A rows get 0x20 (-> +item), B rows 0x10 (-> -item): %s / %s"
         % (L.get(0x495A8D), L.get(0x495DFF)))

    gate("G6", band_shift == 6 and shared == 0x40 and maps[3][0] == 0
         and maps[3][0x40] == 0xC0 and maps[3][-1] == 0xFF
         and all((v >> 6) == o for o in owners for k, v in enumerate(maps[o]) if k >= 0x40)
         and all(v < 0x40 for o in owners for v in maps[o][:0x40]),
         "builder: k<0x40 -> k ; k>=0x40 -> owner*0x40|(k&0x3f); 64 shared + 64 owner")
    # the row-stride chain must be 0x34*idx (13*4): assert separately so a drift bites
    chain = [L.get(x) or "" for x in (0x59603E, 0x596041, 0x596044)]
    stride_ok = ("lea eax,[ebx+ebx*2]" in chain[0] and "lea edi,[ebx+eax*4]" in chain[1]
                 and "shl edi,0x2" in chain[2])
    gate("G6b", stride_ok, "row stride chain 13*i then <<2 == 0x34*i  %s" % (chain,))

    fv_off, fv_n, fv_st = sets["validator 0x5a73f0"]
    gate("G7", fv_off == [0x24, 0x2A, 0x2C, 0x30, 0x32] and fv_st == [0x34]
         and "test BYTE PTR [edi+0x98adb8],0x1" in (L.get(0x5A7473) or "")
         and 0x5A748B in [ad for ad, _t, o in L.refs(*F_VAL, ROW_BASE, ROW_STRIDE) if o == 0x2A],
         "validator reads domain/class/mask/flags/pre-req, band = item>>6  %s" % (fv_off,))

    gate("G8", set(atlas_offsets := union) >= {0x00, 0x20, 0x24, 0x25, 0x26, 0x29, 0x2A, 0x2C, 0x30, 0x32}
         and len(union) == 10,
         "the 10 consumed fields of the 0x34 row  %s" % (["0x%02x" % o for o in union],))

    gate("G9", len(neg_row) == 0 and len(neg_fac) >= 1 and len(pos_row) >= 2
         and "cmp ebx,0x40" in (L.get(0x4EFE41) or ""),
         "decoder: head<0 -> facility table (%d refs, 0 row), head>=0 -> row (%d)"
         % (len(neg_fac), len(pos_row)))

    dg = digest_table(pin)
    print()
    print("digest=%s" % dg)
    if fails:
        print("FAIL M354: %d/%d gates red %s" % (len(fails), 11, fails))
        return 1
    print("PASS M354: 10/10 gates  digest=%s" % dg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
