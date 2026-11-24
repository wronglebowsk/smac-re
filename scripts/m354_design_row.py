#!/usr/bin/env python3
"""M354 - SECTION A's IDENTITY: the positive chooser rows are the 0x98ad88
UNIT-TYPE (design) records, not a facility space.

M351 settled the sign law and the row sources.  It left ONE question open:
what the section-A item *is* (its trace names said "designs", never re-proved).
This milestone reads the row arithmetic of the A block and every consumer of
that row, and computes the answer from the objdump listing:

  0x4956c6  A loop: idx<0x80, item = cand[idx] @0x9267e4 (0x4956d6)
  0x5a73f0  validator: row flags bit0 set, owner mask bit clear, chassis domain,
            and (item>=0x40) row band item>>6 must equal the owner
  0x49571b  imul edx,edx,0x34 / add edx,0x98ad88  -> the row's +0x00 NAME
  0x4957e2  imul ecx,ecx,0x34  / [ecx+0x98adb1]   -> +0x29 WEIGHT (cost)
  0x4959be  imul ecx,ecx,0x34  / [ecx+0x98adb2]   -> +0x2a CLASS (cmp 8)
  0x496050  A's flags fn reads EXACTLY +0x2a and +0x30; B's (0x4960f0) reads
            NO memory at all -> the two sections are different row spaces.

  Field atlas (every offset below is computed from a literal, not authored):
    +0x00 name (appended through std::string @0x404010), +0x20 ability dword,
    +0x24 domain, +0x25..+0x28 component bytes (nouns INFERRED), +0x29 weight,
    +0x2a class, +0x2c owner mask, +0x30 flags word (bit0 valid, bit2 design),
    +0x32 pre-req tech (WORD -> tech record 0x92fdd4, stride 0xb).

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
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("SMAC_M354_TEXT") or os.path.join(ROOT, "scratch", "m574", "text.txt")
STARTS = os.environ.get("SMAC_M354_STARTS") or os.path.join(ROOT, ".func_starts.json")
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
    def __init__(self, path, patch=None):
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
        if patch:
            self.apply_patch(patch)

    def apply_patch(self, spec):
        """spec = '0xADDR|old|new' - one instruction edited in the parsed text.
        The harness uses this instead of rewriting the 40 MB listing; a mutant
        that does not match exactly one instruction raises, never passes."""
        ad, old, new = spec.split("|")
        ad = int(ad, 16)
        t = self.at.get(ad)
        if t is None or old not in t or t.count(old) != 1:
            raise SystemExit("PATCH REJECTED: 0x%x %r not unique in %r" % (ad, old, t))
        self.at[ad] = t.replace(old, new, 1)

    def get(self, a):
        return self.at.get(a)

    def window(self, lo, hi):
        return [(a, self.at[a]) for a in self.order if lo <= a < hi]

    def prev(self, a):
        i = self.order.index(a)
        return self.order[i - 1] if i else None

    def refs(self, lo, hi, base, stride):
        """Every hex literal of an operand inside [base, base+stride)."""
        out = []
        for a, t in self.window(lo, hi):
            for h in HEX.findall(t):
                v = int(h, 16)
                if base <= v < base + stride:
                    out.append((a, t, v - base))
        return out

    def strides(self, lo, hi, imm=None):
        out = []
        for a, t in self.window(lo, hi):
            m = IMUL.search(t)
            if m and (imm is None or int(m.group(2), 16) == imm):
                out.append((a, int(m.group(2), 16)))
        return out

    def extent(self, start, starts):
        """[start, end): the LAST `ret` inside [start, next Ghidra start) - a
        parsed bound, not a hand-picked window width.  Multi-exit functions keep
        all their exits; a trailing embedded jump table stays outside."""
        nxt = min([s for s in starts if s > start] or [start + 0x800])
        last = None
        for a, t in self.window(start, nxt):
            if t.startswith("ret"):
                last = a + (3 if " 0x" in t else 1)
        return start, (last or nxt)


def digest_table(rows):
    s = "\n".join("|".join(str(x) for x in r) for r in rows)
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    a = ap.parse_args()
    L = Listing(TEXT, os.environ.get("SMAC_M354_PATCH") or None)
    starts = json.load(open(STARTS))
    fails, gates = [], []

    def gate(gid, ok, msg):
        print("%s %-4s %s" % ("ok  " if ok else "FAIL", gid, msg))
        gates.append(gid)
        if not ok:
            fails.append(gid)

    pin = []

    # ------------------------------------------------------------------ TABLE 1
    a_imul = L.strides(A_LO, A_HI, 0x34)
    a_all = L.strides(A_LO, A_HI)
    a_row = L.refs(A_LO, A_HI, ROW_BASE, ROW_STRIDE)
    print("TABLE 1  section A (0x%x..0x%x): the item is a 0x%x-stride row index"
          % (A_LO, A_HI, ROW_STRIDE))
    print("  item load            %s" % L.get(0x4956D6))
    print("  all imul-immediates  %s" % [(hex(s), hex(v)) for s, v in a_all])
    for ad, st in a_imul:
        print("  0x%06x  %s" % (ad, L.get(ad)))
    print("  row-field reads      %s"
          % ", ".join("0x%02x@0x%06x" % (o, ad) for ad, _t, o in a_row))
    triples = []
    for s, _st in a_imul:
        nxt = [(ad, o) for ad, _t, o in a_row if 0 <= ad - s <= 12]
        triples.append((s, nxt[0][1] if nxt else None))
    triples = sorted(triples)
    print("  (imul site, field)   %s" % triples)
    pin.append(("A", tuple(a_imul), tuple(triples)))

    # ------------------------------------------------------------------ TABLE 2
    print()
    print("TABLE 2  who reads which field of the 0x98ad88 row (computed offsets;")
    print("         extents parsed from .func_starts.json + the last ret before the next start)")
    fns = [("A flags   0x496050", F_A), ("B flags   0x4960f0", F_B),
           ("validator 0x5a73f0", F_VAL), ("weight    0x5ac950", F_W),
           ("info      0x570e90", F_INFO)]
    ext = {}
    sets = {}
    for name, (lo, hi) in fns:
        e = L.extent(lo, starts)
        ext[name] = e
        r = L.refs(*e, ROW_BASE, ROW_STRIDE)
        st = L.strides(*e, 0x34)
        sets[name] = (sorted({o for _a, _t, o in r}), len(r), len(st))
        print("  %-18s extent 0x%x..0x%x  refs=%d offsets=%s stride-0x34 imuls=%d"
              % (name, e[0], e[1], len(r), ["0x%02x" % o for o in sets[name][0]], len(st)))
    union = sorted({o for v in sets.values() for o in v[0]} | {o for _a, _t, o in a_row})
    print("  union offsets        %s" % ["0x%02x" % o for o in union])
    print("  any 0x98ad literal in B flags fn: %s"
          % [t for _a, t in L.window(*F_B) if "0x98ad" in t])
    pin.append(("F", tuple((k, tuple(v[0]), v[1], v[2]) for k, v in sets.items()),
                tuple(union)))

    # ------------------------------------------------------------------ TABLE 3
    print()
    print("TABLE 3  the candidate builder 0x596000: owner bands in the item space")
    for ad in (0x596017, 0x59601F, 0x596028, 0x596037):
        print("  0x%06x %s" % (ad, L.get(ad)))
    band_shift = 6 if (L.get(0x59601F) or "").endswith("0x6") else None
    m = re.match(r"cmp ecx,0x([0-9a-f]+)$", L.get(0x596017) or "")
    split = int(m.group(1), 16) if m else None
    if MUT == "band":                      # classifier mutant: read the band as 5 bits
        band_shift = 5
        print("  [mutant band] classifier reads the owner band as %d bits" % band_shift)
    maps = {}
    for own in range(8):
        maps[own] = [(k & 0x3F) + ((own << (band_shift or 0)) if split and k >= split else 0)
                     for k in range(0x80)]
    print("  owner 3 band set     %s" % sorted({v >> (band_shift or 0) for v in maps[3]}))
    for own in range(8):
        print("  owner %d: first/mid/last %d/%d/%d  bands %s"
              % (own, maps[own][0], maps[own][0x40], maps[own][-1],
                 sorted({v >> (band_shift or 0) for v in maps[own]})))
    shared = sum(1 for k in range(0x80) if maps[3][k] < 0x40) if band_shift else -1
    print("  owner 3: %d entries < 0x40 (shared band), %d in band 3"
          % (shared, 0x80 - shared))
    b_chain = [L.get(x) or "" for x in (0x59603E, 0x596041, 0x596044)]
    print("  row-stride chain      %s" % " ; ".join(b_chain))
    print("  0x596047 %s" % L.get(0x596047))
    pin.append(("B", band_shift, tuple(maps[3]), tuple(b_chain)))

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
    print("  head<0  row refs=%d facility refs=%d %s"
          % (len(neg_row), len(neg_fac),
             [(hex(ad), "0x%02x" % o) for ad, _t, o in neg_fac]))
    print("  head>=0 row refs=%d stamps/flags %s"
          % (len(pos_row), [(hex(ad), "0x%02x" % o) for ad, _t, o in pos_row if o == 0x30]))
    for ad in (0x4EF88B, 0x4EF897, 0x4EF899, 0x4EF89F, 0x4EF8ED,
               0x4EFE41, 0x4EFE44, 0x4EFE50, 0x4EFE60):
        print("  0x%06x %s" % (ad, L.get(ad)))
    pin.append(("D", len(neg_row), len(neg_fac), len(pos_row)))

    # ------------------------------------------------------------------ TABLE 6
    print()
    print("TABLE 6  the field atlas as CONSUMERS read it (offset -> use)")
    atlas = [
        (0x00, "name string, appended via 0x404010 (std::string, 130 callers)"),
        (0x20, "ability dword, info builder 0x570e90"),
        (0x24, "chassis DOMAIN byte (validator + info)"),
        (0x25, "component byte (validator path / info) - noun OPEN"),
        (0x26, "component byte (info) - noun OPEN"),
        (0x27, "component byte (info) - noun OPEN"),
        (0x28, "component byte (info) - noun OPEN"),
        (0x29, "production WEIGHT -> cost via 0x4e40a0(base+4)"),
        (0x2A, "CLASS byte (==8 colony-pod display rule)"),
        (0x2C, "owner MASK byte, tested 1<<owner by 0x5a73f0"),
        (0x30, "flags WORD: bit0 valid, bit2 design stamped"),
        (0x32, "pre-req tech id (WORD) -> 0x92fdd4 stride 0xb"),
    ]
    print("  %-6s %-52s %s" % ("off", "use", "ref-in-window"))
    for off, use in atlas:
        has = off in [o for _a, _t, o in L.refs(*F_INFO, ROW_BASE, ROW_STRIDE)] \
            or off in [o for _a, _t, o in a_row] \
            or off in [o for _a, _t, o in L.refs(*F_A, ROW_BASE, ROW_STRIDE)] \
            or off in [o for _a, _t, o in L.refs(*F_VAL, ROW_BASE, ROW_STRIDE)] \
            or off in [o for _a, _t, o in L.refs(*F_W, ROW_BASE, ROW_STRIDE)]
        print("  +0x%02x  %-52s %s" % (off, use, has))
    pin.append(("T", tuple(o for o, _u in atlas)))

    if a.digest:
        print()
        print("digest=%s" % digest_table(pin))
        return 0 if not fails else 1

    # ------------------------------------------------------------------ GATES
    print()
    print("GATES")
    gate("G1", a_imul == [(0x49571B, 0x34), (0x4957E2, 0x34), (0x4959BE, 0x34)]
         and triples == [(0x49571B, 0x00), (0x4957E2, 0x29), (0x4959BE, 0x2A)],
         "3 imul-by-0x34 sites, fields +0x00/+0x29/+0x2a  %s"
         % ([(hex(s), None if o is None else "0x%02x" % o) for s, o in triples],))

    prov = []
    for s, _st in a_imul:
        reg = re.match(r"imul\s+(\w+)", L.get(s) or "").group(1)
        p = L.get(L.prev(s)) or ""
        prov.append(p == "mov %s,DWORD PTR [ebp-0x2c]" % reg)
    gate("G2", bool(a_imul) and all(prov) and "0x9267e4" in (L.get(0x4956D6) or "")
         and "[ebp-0x2c],edx" in (L.get(0x4956DD) or ""),
         "every row index is loaded from [ebp-0x2c], filled from [..*4+0x%x]  %s"
         % (CAND_BASE, prov))

    fa_off, fa_n, fa_st = sets["A flags   0x496050"]
    ext_a = ext["A flags   0x496050"]
    gate("G3", fa_off == [0x2A, 0x30] and fa_n == 2 and fa_st == 2
         and ext_a == (0x496050, 0x4960C7)
         and "cmp DWORD PTR [ebp+0x8],0x40" in (L.get(0x49605C) or "")
         and "and ecx,0x4" in (L.get(0x49606F) or ""),
         "A flags fn over its PARSED extent 0x%x..0x%x: %d refs at %s, %d stride sites, "
         "guard 0x40, flags&4 (bit 2)" % (ext_a[0], ext_a[1], fa_n,
                                          ["0x%02x" % o for o in fa_off], fa_st))

    fb_off, fb_n, _fb_st = sets["B flags   0x4960f0"]
    ext_b = ext["B flags   0x4960f0"]
    mem = [t for _a, t in L.window(*ext_b) if "PTR [" in t]
    stack_or_own = [t for t in mem if "[ebp" in t or "0x4961" in t]
    calls = [t for _a, t in L.window(*ext_b) if t.startswith("call ")]
    fb_rets = sorted({int(m.group(1), 16) for _ad, t in L.window(*ext_b)
                      for m in [re.match(r"mov eax,0x([0-9a-f]+)$", t)] if m})
    gate("G4", fb_n == 0 and ext_b == (0x4960F0, 0x496150)
         and len(stack_or_own) == len(mem) and not calls
         and fb_rets == [1, 2, 3]
         and any(t.startswith("xor eax,eax") for _a, t in L.window(*ext_b)),
         "B flags fn over 0x%x..0x%x: ALL %d PTR operands are stack slots or its own "
         "0x4961xx tables (0 data reads, %d calls), returns %s + xor"
         % (ext_b[0], ext_b[1], len(mem), len(calls), fb_rets))

    gate("G5", "or al,0x20" in (L.get(0x495A8D) or "")
         and "or al,0x10" in (L.get(0x495DFF) or "")
         and "and eax,0x20" in (L.get(0x49772A) or "")
         and (L.get(0x49777C) or "").startswith("neg "),
         "A rows 0x20 (-> +item), B rows 0x10 (-> -item): %s / %s"
         % (L.get(0x495A8D), L.get(0x495DFF)))

    ok6 = (band_shift == 6 and split == 0x40 and shared == 0x40 and maps[3][0] == 0
           and maps[3][0x40] == 0xC0 and maps[3][-1] == 0xFF
           and all((v >> 6) == o for o in range(8) for k, v in enumerate(maps[o]) if k >= 0x40)
           and all(v < 0x40 for o in range(8) for v in maps[o][:0x40])
           and "and ebx,0x8000003f" in (L.get(0x596028) or "")
           and "mov DWORD PTR [ecx*4+0x9267e4],ebx" in (L.get(0x596037) or "")
           and (0x8000003F & 0x3F) == 0x3F)
    gate("G6", ok6,
         "builder: cmp 0x%x, shl 6, mask 0x8000003f (&0x3f==0x3f), store to 0x%x; "
         "64 shared + 64 owner" % (split or 0, CAND_BASE))

    stride_ok = ("lea eax,[ebx+ebx*2]" in b_chain[0] and "lea edi,[ebx+eax*4]" in b_chain[1]
                 and "shl edi,0x2" in b_chain[2] and 13 * 4 == ROW_STRIDE)
    gate("G6b", stride_ok, "row stride chain 13*i then <<2 == 0x34*i  %s" % (b_chain,))

    fv_off, fv_n, fv_st = sets["validator 0x5a73f0"]
    v30 = [ad for ad, _t, o in L.refs(*F_VAL, ROW_BASE, ROW_STRIDE) if o == 0x30]
    v2a = [ad for ad, _t, o in L.refs(*F_VAL, ROW_BASE, ROW_STRIDE) if o == 0x2A]
    vch = [L.get(x) or "" for x in (0x5A73F9, 0x5A73FC, 0x5A73FF)]
    gate("G7", fv_off == [0x24, 0x2A, 0x2C, 0x30, 0x32] and fv_st == 0
         and v30 == [0x5A7402] and v2a == [0x5A748B]
         and "test BYTE PTR [edx+0x98adb8],0x1" in (L.get(0x5A7402) or "")
         and "lea eax,[edi+edi*2]" in vch[0] and "lea edx,[edi+eax*4]" in vch[1]
         and "shl edx,0x2" in vch[2]
         and "shl ebx,cl" in (L.get(0x5A7422) or "")
         and "test bl,al" in (L.get(0x5A7424) or ""),
         "validator refs %s; stride lea/lea/shl; flags bit0 @%s; class @%s; mask 1<<owner"
         % (["0x%02x" % o for o in fv_off],
            ["0x%x" % x for x in v30], ["0x%x" % x for x in v2a]))

    gate("G8", union == [0x00, 0x20, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2C, 0x30, 0x32],
         "the 12 consumed fields of the 0x34 row  %s" % (["0x%02x" % o for o in union],))

    pos_offs = [o for _a, _t, o in pos_row]
    gate("G9", len(neg_row) == 0 and len(neg_fac) == 1 and len(pos_row) == 5
         and [o for _a, _t, o in neg_fac] == [0x0C]
         and pos_offs.count(0x30) == 2 and 0x2C not in pos_offs
         and "test ecx,ecx" in (L.get(0x4EF897) or "")
         and "jge 0x4efa2c" in (L.get(0x4EF899) or "")
         and (L.get(0x4EF89F) or "").startswith("neg ")
         and "mov ax,WORD PTR [edx+0x98adb8]" in (L.get(0x4EFE50) or "")
         and "mov WORD PTR [esi+0x98adb8],ax" in (L.get(0x4EFE60) or "")
         and "cmp ebx,0x40" in (L.get(0x4EFE41) or ""),
         "decoder: test/jge/neg pinned; head<0 -> facility cost +0x0c (%d ref, 0 row); "
         "head>=0 -> row LOAD+STORE at +0x30 (%d refs)" % (len(neg_fac), len(pos_row)))

    # G10: the atlas SEMANTICS that are gated (the rest stay INFERRED)
    wtxt = [L.get(x) or "" for x in (0x495724, 0x49572C, 0x4957E7, 0x4957FE,
                                    0x495806, 0x4959C9)]
    probe = {
        "name +0x00 -> std::string": ("push edx" in wtxt[0]
                                      and "call 0x404010" in wtxt[1]
                                      and "call 0x64b9e0" in (L.get(0x404021) or "")),
        "weight +0x29 x 0x4e40a0": ("[ecx+0x98adb1]" in wtxt[2]
                                    and "call 0x4e40a0" in wtxt[3]
                                    and "imul esi,eax" in wtxt[4]),
        "class +0x2a == 8": "cmp edx,0x8" in wtxt[5],
        "pre-req +0x32 WORD -> 0x92fdd4": any(o == 0x32 for _a, _t, o in L.refs(ext["validator 0x5a73f0"][0], ext["validator 0x5a73f0"][1], ROW_BASE, ROW_STRIDE))
                                          and any("0x92fdd4" in t for _a, t in L.window(ext["validator 0x5a73f0"][0], ext["validator 0x5a73f0"][1])),
    }
    print()
    print("TABLE 7  gated atlas semantics (the rest of TABLE 6 stays INFERRED)")
    for k, v in probe.items():
        print("  %-32s %s" % (k, v))
    pin.append(("X", tuple((name, ext[name]) for name in ext), tuple(probe.values())))
    gate("G10", all(probe.values()),
         "semantic probes: %d/%d gated (name, weight, class, pre-req tech)"
         % (sum(probe.values()), len(probe)))
    dg = digest_table(pin)
    print()
    print("digest=%s" % dg)
    if fails:
        print("FAIL M354: %d/%d gates red %s" % (len(fails), len(gates), fails))
        return 1
    print("PASS M354: %d/%d gates  digest=%s" % (len(gates), len(gates), dg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
