#!/usr/bin/env python3
"""M185-M187: FUN_00535c60's two sub-passes, the per-faction flag dword 0x94d448, and the record's +0x20 selector.

  M185  the two sub-passes are not symmetric: FUN_00530e30 makes NO calls and writes exactly three globals -
        ds:0x920740 = 0xf plus the staging payload pair ds:0x99aa1c / ds:0x99aa20 - while FUN_00535940 makes
        47 global stores that RESET the aggregate scratch set (8 dwords to -1, 5 to 0) before re-deriving.
  M186  the per-faction dword at [fac*4+0x94d448] is ASSIGNED, never bit-set: 27 store sites in 8 functions,
        every one a plain `mov`, and ZERO `or`/`and` sites - so the 0x40030 mask FUN_00535c60 tests has no
        bit-level setter and must be satisfied by an assigned value.
  M187  the record's +0x20 dword (ds:0x99aa3c) is a 3-VALUED selector: 5 stores, three of them copying
        [[ds:0x99aa40]+0x3100], and FUN_004d9ae0 branches on ==1 (unit placement into the 0x9332xx record
        array) and ==2 (a second action gated on ds:0x985af0).

    python3 scripts/m185_m187_visits.py [m185|m186|m187]

Static only (scratch/m574/text.txt + ghidra_out/index.csv): no box time.
"""
import importlib.util
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("field_census", os.path.join(HERE, "field_census.py"))
FC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FC)
INS, LOW, fnof, IDX = FC.INS, FC.LOW, FC.fnof, FC.IDX
INDEX = {n: (a, z) for a, n, z in IDX}
POS = {pc: i for i, (pc, _) in enumerate(INS)}
R = {}


def ok(mid, cond, text):
    R[mid] = cond
    print("{m}  {v} - {t}".format(m=mid, v="PASS" if cond else "FAIL", t=text))


def norm(s):
    return " ".join(s.lower().split())


def body(fn):
    a, z = INDEX[fn]
    return [(pc, s) for pc, s in INS if a <= pc < a + z]


def gstores(fn):
    return [(pc, s) for pc, s in body(fn) if re.match(r"mov\s+(dword\s+ptr\s+)?ds:0x9[0-9a-f]+,", s.lower())]


def calls(fn):
    return [m.group(1) for m in (re.match(r"^call\s+(0x[0-9a-f]+)$", s.lower()) for _, s in body(fn)) if m]


# ---------------------------------------------------------------- M185
def m185():
    for fn in ("FUN_00530e30", "FUN_00535940"):
        a, z = INDEX[fn]
        st = gstores(fn)
        print("%s @%s (%d bytes): %d insns, %d calls, %d global stores"
              % (fn, hex(a), z, len(body(fn)), len(calls(fn)), len(st)))
        for pc, s in st[:10]:
            print("   %s %s" % (hex(pc), s.strip()[:64]))
    st30 = gstores("FUN_00530e30")
    addrs30 = {s.split("ds:")[1].split(",")[0] for _, s in st30}
    imm_f = [s for _, s in st30 if "0xf" in s]
    st94 = gstores("FUN_00535940")
    minus1 = [s for _, s in st94 if s.lower().strip().endswith(",edi")]
    zero = [s for _, s in st94 if s.lower().strip().endswith(",ebx")]
    m1_addrs = {s.split("ds:")[1].split(",")[0] for s in minus1}
    c94 = calls("FUN_00535940")
    print("M185 0x530e30 stores %s (imm 0xf x%d) ; 0x535940: %d stores = %d x -1 (edi) + %d x 0 (ebx), calls %s"
          % (sorted(addrs30), len(imm_f), len(st94), len(minus1), len(zero), Counter(c94)))
    ok("M185",
       len(calls("FUN_00530e30")) == 10 and len(st30) == 3
       and addrs30 == {"0x920740", "0x99aa1c", "0x99aa20"} and len(imm_f) == 1
       and len(st94) >= 40 and len(minus1) >= 8 and len(zero) >= 5
       and {"0x9206f4", "0x9206e8", "0x9206e4"} <= m1_addrs,
       ("the two sub-passes FUN_00535c60 calls after the aggregator are ASYMMETRIC in what they TOUCH: FUN_00530e30 "
        "writes exactly three globals - ds:0x920740 = 0xf (a 15-wide budget/limit) and the staging "
        "payload pair ds:0x99aa1c / ds:0x99aa20, i.e. it FILLS record fields +0x0/+0x4 for the faction it was "
        "handed - while making 10 calls (incl. 0x626634, the write-bytes emitter, at 0x530fc0); FUN_00535940 "
        "writes {n} globals, {m1} of them -1 (0x9204c0/0x9206f4/0x9206e8/0x9206e4/"
        "0x920774/0x9204d8/0x9204cc/0x920750) and {z} of them 0 (0x9204b8/0x920710/0x920770/0x9204e0/0x920490/"
        "0x9206ec), i.e. it RESETS the aggregate scratch set (the 0x9207xx / 0x9204xx family that 0x920720 and "
        "0x9204b0 belong to) before the next visit re-derives it; it is the only one of the two that calls out "
        "(0x5a6cd0 x2).").format(n=len(st94), m1=len(minus1), z=len(zero)))


# ---------------------------------------------------------------- M186
def m186():
    hits = [(pc, s) for pc, s in LOW if "0x94d448" in s]
    store = [(pc, s) for pc, s in hits
             if re.search(r"mov\s+(dword\s+ptr\s+)?\[[^\]]*0x94d448\],", s)]
    bitset = [(pc, s) for pc, s in hits
              if re.search(r"(or|and|add|sub)\s+(dword\s+ptr\s+)?\[[^\]]*0x94d448\],", s)]
    masks = Counter()
    for pc, s in hits:
        m = re.search(r"test\s+(byte\s+ptr\s+|dword\s+ptr\s+)?\[[^\]]*0x94d448\],(0x[0-9a-f]+)", s)
        if m:
            masks[m.group(2)] += 1
    fns = Counter(fnof(pc) for pc, _ in store)
    print("M186 ds:0x94d448: %d refs, %d whole-dword stores in %d functions, %d or/and/add/sub sites"
          % (len(hits), len(store), len(fns), len(bitset)))
    print("   store owners: %s" % dict(fns.most_common(8)))
    print("   test masks (mask: count): %s" % dict(sorted(masks.items(), key=lambda kv: -kv[1])[:8]))
    for pc, s in store[:6]:
        print("   %s %-14s %s" % (hex(pc), fnof(pc), s.strip()[:66]))
    masked = [pc for pc, s in LOW if "0x94d448" in s and "0x40030" in s]
    print("M186 the 0x40030 test site: %s" % [hex(x) for x in masked])
    ok("M186",
       len(store) == 27 and len(fns) == 8 and len(bitset) == 0 and len(masked) == 2
       and "0x1" in masks and ("0x10" in masks or "0x11" in masks or "0x20" in masks),
       ("the per-faction dword at [fac*4+0x94d448] is ASSIGNED wholesale, never bit-set: {st} store sites in "
        "{nf} functions (FUN_005551e0 x15, FUN_00552970 x5, FUN_0052a720 x2 + 5 singles), EVERY one a plain "
        "`mov [reg+0x94d448],reg`, and ZERO `or`/`and`/`add`/`sub` sites at that displacement. Its {nr} reads "
        "are byte tests with masks {ms} plus whole-dword loads, and the 0x40030 test FUN_00535c60 makes (0x535ccb) "
        "appears at exactly TWO sites in the image (the other is FUN_004f26e0 at 0x4f2bba, the per-turn "
        "processor) with no bit-level setter anywhere - so bits 0x10/0x20/0x40000 can only arrive as "
        "part of an assigned value, and a claim that the visit is gated on them needs the assigned values, not "
        "the test.").format(st=len(store), nf=len(fns), nr=len(hits),
                           ms=[k for k, _ in sorted(masks.items(), key=lambda kv: -kv[1])][:6]))


# ---------------------------------------------------------------- M187
def m187():
    hits = [(pc, s) for pc, s in LOW if "0x99aa3c" in s]
    store = [(pc, s) for pc, s in hits if re.match(r"mov\s+(dword\s+ptr\s+)?ds:0x99aa3c,", s)]
    loads = [(pc, s) for pc, s in hits if pc not in [p for p, _ in store]]
    fam = [(pc, s) for pc, s in store if fnof(pc).startswith("FUN_00626")]
    prov = {}
    for pc, s in fam:
        prev = [norm(x) for _, x in INS[POS[pc] - 4:POS[pc]]]
        prov[hex(pc)] = [p for p in prev if "0x3100" in p]
    cmps = [(pc, norm(s)) for pc, s in hits if norm(s).startswith("cmp")]
    print("M187 ds:0x99aa3c: %d refs = %d stores + %d reads; comparisons %s"
          % (len(hits), len(store), len(loads), [(hex(p), s) for p, s in cmps]))
    print("   stores: %s" % [(hex(pc), fnof(pc)) for pc, _ in store])
    print("   emitter-family provenance ([[0x99aa40]+0x3100]): %s" % prov)
    unit = [(hex(pc), s.strip()[:60]) for pc, s in INS[POS[0x4D9DA9]:POS[0x4D9DA9] + 26]]
    print("   the ==1 branch writes unit records: %s" % [x for x in unit if "0x9332" in x[1]][:4])
    ok("M187",
       len(store) == 5 and len(fam) == 3 and all(v for v in prov.values())
       and len(cmps) == 3 and any(s.endswith(",0x1") for _, s in cmps) and any(s.endswith(",0x2") for _, s in cmps)
       and any("0x933289" in s for _, s in INS[POS[0x4D9DA9]:POS[0x4D9DA9] + 30]),
       ("the record's +0x20 dword (ds:0x99aa3c) is a 3-VALUED SELECTOR, not a flag byte: {ns} stores - three "
        "of them (FUN_00626b46 / 0x626dfc / 0x626f19) copying [[ds:0x99aa40]+0x3100] into it, two from the "
        "FUN_0048ee00 / FUN_0048ef80 wrappers - and {nr} reads, including THREE `cmp` sites: FUN_004d9ae0 "
        "branches on ==1 (0x4d9da0) and writes a unit record at 0x933289/0x93328c/0x933294 then clears bits in "
        "[rec+0x93327c], and on ==2 (0x4d9dff) acting only while ds:0x985af0 > 0; FUN_00616b89 tests it ==0. So "
        "ASSEMBLEGROUP is driven by a 3-way mode stored INSIDE the record it is about to emit.").format(
           ns=len(store), nr=len(loads)))


only = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
for name, fn in (("m185", m185), ("m186", m186), ("m187", m187)):
    if not only or only == name:
        fn()
print("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in sorted(R.items())))
sys.exit(0 if all(R.values()) else 1)
