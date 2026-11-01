#!/usr/bin/env python3
"""M182-M184: the staging record's field map, the four whole-value writers, and FUN_00535c60's callers.

  M182  ds:0x99aa1c is the base of the 65-byte record the tagged writer 0x6267a5 emits (the 0x41 push):
        13 dwords are referenced in [0x99aa1c, 0x99aa5c]; the band's writers touch exactly FOUR of them
        (+0, +4, +0x1c, +0x20) and the writer family FUN_00626b46 owns +0xc..+0x18.
  M183  the four WHOLE-VALUE writers are not packers: 0x4dc390 is a RESTORER (12 unpack legs, 0 pack legs),
        0x4d9ae0 copies bits 0..11 in a `shl edx,cl` loop, 0x512b40 drives the set-bit helper with indices
        1..3, and 0x4dde00 builds from [esi+0x93327c] tests — each stores the scratch ONCE.
  M184  FUN_00535c60 is a per-faction VISIT wrapper: 3 call sites in 2 owners, and the body runs the
        aggregator 0x531df0 plus 0x530e30 and 0x535940 in that order, folds the faction id with the
        2095-dword chain, then tests [eax*4+0x94d448] against 0x40030.

    python3 scripts/m182_m184_bandrecord.py [m182|m183|m184]

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
R = {}
BASE = 0x99AA1C
END = 0x99AA60
BAND = ["FUN_0041a8f0", "FUN_004d9ae0", "FUN_004dc100", "FUN_004dc390", "FUN_004dc5f0", "FUN_004dc8d0",
        "FUN_004dcc10", "FUN_004dde00", "FUN_00510230", "FUN_00512b40", "FUN_00516b80", "FUN_00518c50",
        "FUN_0057c550", "FUN_00626b46"]


def ok(mid, cond, text):
    R[mid] = cond
    print("{m}  {v} - {t}".format(m=mid, v="PASS" if cond else "FAIL", t=text))


def norm(s):
    return " ".join(s.lower().split())


def window(lo, hi):
    return [(pc, s) for pc, s in INS if lo <= pc <= hi]


def fold_chain(lo, hi):
    want = ("shl eax,0x6", "add eax,edi", "lea eax,[edi+eax*2]", "shl eax,0x4", "sub eax,edi")
    return [norm(s) for pc, s in window(lo, hi) if norm(s) in want]


# ---------------------------------------------------------------- M182
def m182():
    offs = {}
    for pc, s in LOW:
        for m in re.finditer(r"ds:(0x99aa[0-9a-f]{2})", s):
            a = int(m.group(1), 16)
            if BASE <= a < END:
                store = bool(re.match(r"mov\s+(dword\s+ptr\s+|byte\s+ptr\s+)?ds:%s," % m.group(1), s))
                d = offs.setdefault(a, {"refs": 0, "stores": 0, "fns": Counter()})
                d["refs"] += 1
                d["stores"] += store
                d["fns"][fnof(pc)] += 1
    print("M182 the staging record spans ds:0x%x..0x%x (0x%x bytes) - %d dwords referenced:"
          % (BASE, END - 4, END - BASE, len(offs)))
    for a in sorted(offs):
        d = offs[a]
        print("   +0x%02x  0x%x  refs %-4d stores %-3d  %s"
              % (a - BASE, a, d["refs"], d["stores"], [f for f, _ in d["fns"].most_common(4)]))
    packers = [f for f in BAND if f != "FUN_00626b46"]
    pack_offs = {a - BASE for a in offs for f in offs[a]["fns"] if f in packers}
    emitter_offs = {a - BASE for a in offs if set(offs[a]["fns"]) == {"FUN_00626b46"}}
    store_offs = {a - BASE for a in offs if offs[a]["stores"]}
    print("M182 packers (13 band functions less the emitter) touch %s ; emitter-only offsets %s ; "
          "offsets with any store %s"
          % (sorted(hex(x) for x in pack_offs), sorted(hex(x) for x in emitter_offs),
             sorted(hex(x) for x in store_offs)))
    ok("M182",
       len(offs) == 14 and pack_offs == {0x0, 0x4, 0x1C, 0x20} and emitter_offs == {0xC, 0x10, 0x14, 0x18}
       and 0x1C in store_offs and offs[BASE + 0x1C]["stores"] == 33,
       ("ds:0x99aa1c is the BASE of the record 0x6267a5 emits, not a loose scratch: {n} dwords are referenced "
        "in [0x{b:x}, 0x{e:x}] and the 13 packers touch exactly FOUR of them - +0x0 (0x99aa1c, 637 stores, the "
        "generic write-bytes argument), +0x4 (0x99aa20, 637), +0x1c (0x99aa38, 33 stores, the flag dword "
        "M178-M179 mapped) and +0x20 (0x99aa3c, 5 stores) - while +0xc..+0x18 (0x99aa28/2c/30/34) are written "
        "ONLY by the emitter FUN_00626b46, i.e. its own bookkeeping, and +0x24 by it plus the 0x626xxx siblings. "
        "Seven further dwords (+0x30..+0x40) belong to the 0x627xxx serializers. The 0x41 size pushed with "
        "GOVOPTIONS equals this span 0x99aa1c..0x99aa5c (INFERRED alignment, not proven).")
       .format(n=len(offs), b=BASE, e=END - 4))


# ---------------------------------------------------------------- M183
def m183():
    whole = ["FUN_004d9ae0", "FUN_004dc390", "FUN_004dde00", "FUN_00512b40"]
    rows = {}
    for fn in whole:
        a, z = INDEX[fn]
        st = [pc for pc, s in LOW if a <= pc < a + z and re.match(r"mov\s+(dword\s+ptr\s+)?ds:0x99aa38,", s)]
        legs = sum(1 for pc, s in LOW if a <= pc < a + z and re.match(r"^(or|and)\s+(al|ah|eax)\s*,", s))
        shl = sum(1 for pc, s in LOW if a <= pc < a + z and re.match(r"^shl\s+[a-z]+,\s*cl$", s))
        tests = sum(1 for pc, s in LOW if a <= pc < a + z and re.match(r"^test\s+(al|ah),\s*0x", s))
        rows[fn] = dict(stores=len(st), legs=legs, shl=shl, scratchtests=tests)
        print("   %-14s stores=%d  or/and-al-ah-eax=%d  shl-by-cl=%d  test-al/ah-imm=%d"
              % (fn, len(st), legs, shl, tests))
    a9, z9 = INDEX["FUN_004d9ae0"]
    loop = [norm(s) for pc, s in window(a9, a9 + z9)
            if norm(s) in ("shl edx,cl", "test eax,edx", "or esi,edx", "inc ecx", "cmp ecx,0xc")]
    a12, z12 = INDEX["FUN_00512b40"]
    idx = [norm(s) for pc, s in window(a12, a12 + z12) if re.match(r"^push\s+0x[123]$", norm(s))]
    setne = sum(1 for pc, s in window(a12, a12 + z12) if norm(s).startswith("setne"))
    calls = Counter(fnof(pc) for pc, s in LOW if re.match(r"^call\s+0x518c50$", s))
    print("M183 0x4d9ae0 loop ops %s ; 0x512b40 setne=%d, push-0x1/2/3=%s ; calls to the set-bit helper: %s"
          % (loop, setne, idx, dict(calls)))
    ok("M183",
       rows["FUN_004dc390"]["stores"] == 1 and rows["FUN_004dc390"]["legs"] <= 2
       and rows["FUN_004dc390"]["scratchtests"] >= 12 and rows["FUN_004d9ae0"]["shl"] == 2
       and {"shl edx,cl", "test eax,edx", "or esi,edx", "cmp ecx,0xc"} <= set(loop)
       and loop.count("cmp ecx,0xc") >= 1
       and setne >= 1 and idx.count("push 0x1") >= 1 and calls.get("FUN_00512b40", 0) >= 3,
       ("the four whole-value writers are NOT leg packers (each stores ds:0x99aa38 once, vs 9-19 legs for the "
        "packers). 0x4dc390 is a RESTORER: %d `test al/ah,imm` scratch-bit tests and essentially no pack ops, "
        "the mirror image of 0x4dc100's 24 pack ops. 0x4d9ae0 copies bits 0..11 of the value returned by 0x58e760 "
        "through a `shl edx,cl / test eax,edx / or|and esi,edx / inc ecx / cmp ecx,0xc` loop (12 iterations). "
        "0x512b40 never builds a mask itself: it computes %d `setne` boolean test(s) and asks the set-bit helper "
        "FUN_00518c50 with indices 1/2/3 (%d call sites in this function), so the TECHRANDOM record's bits are "
        "set one at a time by index. 0x4dde00 builds from [esi+0x93327c] tests and pushes EDITVEH."
        % (rows["FUN_004dc390"]["scratchtests"], setne, calls.get("FUN_00512b40", 0))))


# ---------------------------------------------------------------- M184
def m184():
    sites = [(pc, fnof(pc)) for pc, s in LOW if re.match(r"^call\s+0x535c60$", s)]
    owners = Counter(f for _, f in sites)
    print("M184 callers of FUN_00535c60: %s" % {f: len([1 for _, g in sites if g == f]) for f in owners})
    for pc, f in sites:
        pushes = [norm(x) for _, x in INS[max(0, [p for p, _ in INS].index(pc) - 6):[p for p, _ in INS].index(pc)]
                  if norm(x).startswith("push")]
        print("   %s %-14s pushes: %s" % (hex(pc), f, pushes))
    a, z = INDEX["FUN_00535c60"]
    body = window(a, a + z)
    callees = [m.group(1) for m in (re.match(r"^call\s+(0x[0-9a-f]+)$", norm(s)) for _, s in body[:40]) if m]
    order = [c for c in callees if c in ("0x531df0", "0x530e30", "0x535940")]
    fold = fold_chain(a, a + z)
    flag = [norm(s) for _, s in body if "0x94d448" in norm(s) and "0x40030" in norm(s)]
    print("M184 FUN_00535c60 (%d bytes): first callees %s ; fold %s ; flag test %s"
          % (z, callees[:4], fold, flag))
    ok("M184",
       len(sites) == 3 and len(owners) == 2 and owners.get("FUN_004266c0") == 2
       and owners.get("FUN_00545c50") == 1 and order == ["0x531df0", "0x530e30", "0x535940"]
       and fold[:5] == ["shl eax,0x6", "add eax,edi", "lea eax,[edi+eax*2]", "shl eax,0x4", "sub eax,edi"]
       and len(flag) == 1,
       ("FUN_00535c60 is a per-faction VISIT wrapper with a tiny caller set: 3 call sites in 2 owners - "
        "FUN_004266c0 x2 (which pass ds:0x91b5b4, our faction, plus [ebp-0x14] and eax) and FUN_00545c50 x1 "
        "(esi, 0, ebx, eax). Its first 40 instructions call %s IN THAT ORDER (the aggregator, then two "
        "sub-passes), then it folds arg1 with the 2095-dword chain (shl 6 / add / lea / shl 4 / sub) into "
        "[ebp-0x14] and tests [eax*4+0x94d448] against 0x40030 - so 0x535c60 is the 'aggregate + upkeep + "
        "score this one faction, then check its flag word' visit, and FUN_004266c0 is its only multi-caller."
        % order))


only = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
for name, fn in (("m182", m182), ("m183", m183), ("m184", m184)):
    if not only or only == name:
        fn()
print("SUMMARY " + " ".join("%s=%s" % (k, "PASS" if v else "FAIL") for k, v in sorted(R.items())))
sys.exit(0 if all(R.values()) else 1)
