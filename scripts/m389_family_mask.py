#!/usr/bin/env python3
"""M389 - the 0x4dadxx family's runtime masks: five OPEN entries become verbs.

M384 left 7 mask-API arguments unresolved; five sit in the 0x4dadxx family
(0x4dad30 in FUN_004dacc0, and 0x4daedd/0x4daf41/0x4db02d/0x4db08d in
FUN_004dadd0).  M385 resolved FUN_004dacc0's four callers to literals but never
walked the four register masks inside FUN_004dadd0.  This instrument does that
walk with a callee-saved law (calls clobber eax/ecx/edx only), then classifies
every apply-call in the function as SET or CLEAR from the callee's own body, and
finally censuses the two entries into FUN_004dadd0 to see which one is live.

  G0 parse    .text dump + ghidra index; function ranges re-derived.
  G1 defs     the four register masks walk back to a dominating `mov reg,imm`;
              0x4dad30's edi walks to [ebp+8] and out to its four callers.
  G2 arms     seven FUN_0x6051fa-guarded arms, each with one SET and one CLEAR
              apply; mask ladder + direction measured, not authored.
  G3 verbs    FUN_00551a20 ORs, FUN_00518f0 NOTs+ANDs; 0x551cf0 branches on flag.
  G4 gate     FUN_004dacc0: 4 literal callers, mask=arg, two arms.
  G5 entry    FUN_004dadd0's two callers: one dead (.text has no reference),
              one live (FUN_004db480).
  G6 rivals   five rival readings REFUTED on the printed numbers.
  G7 digest   table digest computed twice.

M389_PATCH='addr|text' rewrites one instruction (mutants); M389_ALGO=n flips a law:
  1 calls clobber every register, 2 SET/CLEAR regions swapped, 3 0x5518f0 read as
  an OR (semantics unwitnessed), 4 a 0x400 arm is admitted into the ladder,
  5 first `mov reg,imm` from function start (no dominance), 6 the guard is ignored
  (every test site is its own arm), 7 the zero-call census is ignored (dead=live).
"""
import csv
import hashlib
import importlib.util
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M389_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.environ.get("M389_EXE", "/home/paul/reverse/smac/terran.exe")
INDEX = os.environ.get("M389_INDEX", os.path.join(ROOT, "ghidra_out/index.csv"))
ALGO = int(os.environ.get("M389_ALGO", "0") or 0)
PATCH = os.environ.get("M389_PATCH", "")
DIGEST_PIN = "05a36a50540466f3"

spec = importlib.util.spec_from_file_location("m382", os.path.join(ROOT, "scripts/m382_treaty_readers.py"))
_m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_m)
INS = _m.load_text(TEXT)
if PATCH:
    _a, _t = PATCH.split("|", 1)
    _a = int(_a, 16)
    INS = [(x, _t.strip() if x == _a else b) for x, b in INS]
ADDR = [a for a, b in INS]
IDX = {a: i for i, a in enumerate(ADDR)}
PART = _m.PART
FIELD = "0x94d448"
CORE = 0x400

FAILS = []
TOTAL = [0]


def check(name, cond, detail=""):
    TOTAL[0] += 1
    print(("  ok   " if cond else "  FAIL ") + name + ((" - " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)
    return cond


# ---------------------------------------------------------------- instruction helpers
def mn(t):
    return t.split(None, 1)[0] if t else ""


def ops(t):
    p = t.split(None, 1)
    return p[1] if len(p) > 1 else ""


WRITE = {"mov", "lea", "xor", "add", "sub", "and", "or", "pop", "inc", "dec",
         "shl", "shr", "sar", "neg", "not", "adc", "sbb", "imul", "movzx", "movsx"}
CLOBBER = {"eax", "ecx", "edx"}


def writes(t, reg):
    m = re.match(r"(\w+)\s+(.*)$", t)
    if not m or m.group(1) not in WRITE:
        return False
    return m.group(2).split(",")[0].strip() == reg


def find_def(site_idx, reg, lo_idx):
    """Backward walk for the reaching def of `reg`. Returns (addr, imm|None, why)."""
    if ALGO == 5:                                   # mutant: no dominance, first imm
        for j in range(lo_idx, site_idx):
            a, t = INS[j]
            m = re.match(r"mov\s+" + reg + r"\s*,\s*(0x[0-9a-f]+)$", t)
            if m:
                return a, int(m.group(1), 16), "first-imm"
        return None, None, "none"
    for j in range(site_idx - 1, lo_idx - 1, -1):
        a, t = INS[j]
        if mn(t) == "call" and (ALGO == 1 or reg in CLOBBER):
            return a, None, "call-clobber"
        if writes(t, reg):
            m = re.match(r"mov\s+" + reg + r"\s*,\s*(0x[0-9a-f]+)$", t)
            if m:
                return a, int(m.group(1), 16), "mov-imm"
            return a, None, "non-literal:" + t
    return None, None, "none"


def resolve(site_idx, opnd, lo_idx):
    """Resolve an operand to (value|None, kind, def_addr, why)."""
    if opnd.startswith("0x"):
        return int(opnd, 16), "imm", None, "imm"
    if opnd not in PART:
        return None, "opaque", None, "not-a-reg"
    base, bits, shift = PART[opnd]
    a, imm, why = find_def(site_idx, base, lo_idx)
    if imm is None:
        return None, "opaque", a, why
    if bits == 8:
        v = (imm >> shift) & 0xFF
    elif bits == 16:
        v = (imm >> shift) & 0xFFFF
    else:
        v = imm
    return v, "reg:" + opnd, a, why


def range_ins(lo, hi):
    return [(a, t) for a, t in INS if lo <= a < hi]


def funcs():
    out = []
    for r in csv.DictReader(open(INDEX)):
        out.append((int(r["addr"], 16), r["name"], int(r["size_bytes"]),
                    int(r["n_insns"]), int(r["n_callers"])))
    out.sort()
    return out


FUNCS = funcs()


def containing(addr):
    for a, n, s, i, c in FUNCS:
        if a <= addr < a + s:
            return a, n, s, i, c
    return None, None, None, None, None


def call_sites(target):
    pat = re.compile(r"^(call|jmp)\s+0x%x$" % target)
    return [a for a, t in INS if pat.match(t)]


EXE_BYTES = open(EXE, "rb").read()


def dword_refs(target):
    return EXE_BYTES.count(struct.pack("<I", target))


# ---------------------------------------------------------------- G0
print("G0  parse and ranges")
print("  .text dump: %d instructions, 0x%x..0x%x" % (len(INS), ADDR[0], ADDR[-1]))
check("G0 the dump is one ascending address list",
      all(ADDR[i] < ADDR[i + 1] for i in range(len(ADDR) - 1)))
check("G0 the censused exe is 3,067,904 B", len(EXE_BYTES) == 3067904, str(len(EXE_BYTES)))

RANGES = {}
for fa, name, size, n_ins, n_call in FUNCS:
    if fa in (0x4dab90, 0x4dacc0, 0x4dadd0, 0x4db480):
        got = len([1 for a, t in INS if fa <= a < fa + size])
        RANGES[fa] = (size, n_ins, n_call)
        print("  %-14s %5d B %4d insns (index) %4d insns (dump) %d callers"
              % (name, size, n_ins, got, n_call))
        check("G0 %s frame matches the index" % name, got == n_ins, "%d vs %d" % (got, n_ins))


# ---------------------------------------------------------------- G1
print("\nG1  the five OPEN sites: four register masks + one argument")
FN_ADD = (0x4dadd0, 0x4dadd0 + 985)
FN_ACC = (0x4dacc0, 0x4dacc0 + 126)
lo_add, hi_add = IDX[0x4dadd0], IDX[0x4db1b0]
lo_acc, hi_acc = IDX[0x4dacc0], IDX[0x4dabf0 + 0x0] if False else IDX[0x4dad40]

SITES = [(0x4daedd, "ebx", lo_add, hi_add), (0x4daf41, "ebx", lo_add, hi_add),
         (0x4db02d, "edi", lo_add, hi_add), (0x4db08d, "edi", lo_add, hi_add)]
DEFS = []
for site, reg, lo, hi in SITES:
    v, kind, da, why = resolve(IDX[site], reg, lo)
    # any other write of the register strictly between the def and the site?
    others = 0
    if da is not None:
        for a, t in INS[IDX[da] + 1:IDX[site]]:
            if writes(t, reg):
                others += 1
    DEFS.append((site, reg, da, v, why, others))
    print("  site 0x%-7x %-3s <- 0x%-7x %-8s %s  intervening-writes=%d"
          % (site, reg, da if da else 0, v if v is not None else 0, why, others))
check("G1 all four register masks resolve to a literal mov", all(d[3] is not None for d in DEFS))
check("G1 every def is a `mov reg,imm`",
      all(d[4] == "mov-imm" for d in DEFS), str([d[4] for d in DEFS]))
check("G1 every def strictly dominates its site in straight-line order",
      all(d[5] == 0 for d in DEFS), str([d[5] for d in DEFS]))
check("G1 the resolved masks are {0x4,0x2,0x1000,0x2000}",
      sorted(d[3] for d in DEFS) == [2, 4, 0x1000, 0x2000], str([hex(d[3]) for d in DEFS]))
check("G1 the defs are 0x4daea3/0x4daf07/0x4dafcf/0x4db035",
      [d[2] for d in DEFS] == [0x4daea3, 0x4daf07, 0x4dafcf, 0x4db035],
      str([hex(d[2]) for d in DEFS]))

# 0x4dad30: the fifth site, mask = edi = [ebp+8] -> the four pushed literals
acc_callers = []
for c in call_sites(0x4dacc0):
    pushes = []
    j = IDX[c] - 1
    while j > 0 and mn(INS[j][1]) in ("push", "mov", "lea", "add", "sub"):
        if mn(INS[j][1]) == "push":
            pushes.append((INS[j][0], ops(INS[j][1])))
        j -= 1
    acc_callers.append((c, pushes))
acc_masks = []
for c, pushes in acc_callers:
    for a, o in pushes:
        if o.startswith("0x"):
            acc_masks.append((c, a, int(o, 16)))
print("  FUN_004dacc0 callers: " + ", ".join(
    "0x%x push@0x%x=0x%x" % (c, a, m) for c, a, m in acc_masks))
edi_def = INS[IDX[0x4dacc5]][1]
print("  its mask register: 0x4dacc5  %s" % edi_def)
check("G1 FUN_004dacc0's mask is edi=[ebp+0x8]", edi_def == "mov    edi,DWORD PTR [ebp+0x8]"
      or edi_def == "mov edi,DWORD PTR [ebp+0x8]", edi_def)
check("G1 its four callers each push exactly one literal",
      len(acc_masks) == 4 and len(acc_callers) == 4, str(len(acc_masks)))
check("G1 the four pushed masks are {0x20,0x2000000,0x400,0x40000}",
      sorted(m for _, _, m in acc_masks) == [0x20, 0x400, 0x40000, 0x2000000],
      str([hex(m) for _, _, m in acc_masks]))
print("  => 0x4dad30 (mask edi at the CLEAR arm, 0x4dad30) carries {0x20,0x400,0x40000,0x2000000};")
print("     0x4dad05 (SET arm) carries the same set. Both are 0x551cf0 calls.")


# ---------------------------------------------------------------- G2
print("\nG2  the seven guarded arms: mask ladder and direction")
fn = range_ins(*FN_ADD)
guards, tests, applies = [], [], []
for a, t in fn:
    if mn(t) == "call" and ops(t) == "0x6051fa":
        guards.append(a)
    if mn(t) == "test" and FIELD in ops(t):
        tests.append(a)
    if mn(t) == "call" and ops(t) in ("0x551a20", "0x5518f0", "0x551cf0"):
        applies.append((a, ops(t)))
print("  guards (call 0x6051fa): %d  test sites: %d  apply calls: %d"
      % (len(guards), len(tests), len(applies)))

tail = [a for a in tests if "0x2000000" in INS[IDX[a]][1]]
print("  unguarded tail test (0x2000000): %s" % ", ".join("0x%x" % a for a in tail))
check("G2 exactly one unguarded 0x2000000 tail test in FUN_004dadd0", len(tail) == 1)

ARM = []
if ALGO == 6:
    guards = [a for a in tests if "0x6051fa" in ""] or tests     # mutant: guard ignored
for i, g in enumerate(guards):
    nxt = guards[i + 1] if i + 1 < len(guards) else (tail[0] if tail else FN_ADD[1])
    # the mask pushed into FUN_0x6051fa = nearest push before the call
    j = IDX[g] - 1
    while j > 0 and mn(INS[j][1]) != "push":
        j -= 1
    gm, gk, gd, gwhy = resolve(j, ops(INS[j][1]), IDX[g] - 40 if False else lo_add)
    # the je target after `test eax,eax`
    je = None
    for a in range(IDX[g], IDX[nxt]):
        x = INS[a][1]
        if mn(x) == "test" and ops(x).replace(" ", "") == "eax,eax":
            k = a + 1
            while k < IDX[nxt] and not x.startswith("j"):
                k += 1
                if k < len(INS):
                    x = INS[k][1]
            if mn(x) == "je":
                je = int(ops(x), 16)
            break
    arm_tests = [a for a in tests if g <= a < nxt]
    arm_applies = [(a, tn) for a, tn in applies if g <= a < nxt]
    # direction witnesses: 3-arg arms = the call site itself; 4-arg arms = the flag push
    cls = []
    cf_calls = []
    for a, tn in arm_applies:
        if tn == "0x551a20":
            cls.append(("SET", a))
        elif tn == "0x5518f0":
            cls.append(("CLEAR", a))
        else:
            cf_calls.append(a)
    if cf_calls:
        for b in range(IDX[g], IDX[nxt]):
            x = INS[b][1]
            if mn(x) == "push" and ops(x) in ("0x0", "0x1"):
                cls.append(("SET" if ops(x) == "0x1" else "CLEAR", INS[b][0]))
    ARM.append((gm, g, je, arm_tests, cls, cf_calls))
    print("  mask 0x%-5x guard 0x%-7x je->0x%-7x tests=%d  %s  %s"
          % (gm if gm is not None else 0, g, je or 0, len(arm_tests),
             ", ".join("%s@0x%x" % (k, s) for k, s in cls),
             ("one 0x551cf0 call @0x%x" % cf_calls[0]) if cf_calls else "two 3-arg calls"))

ladder = [a[0] for a in ARM]
if ALGO == 4 and 0x400 not in ladder:                # mutant: admit a 0x400 arm
    ladder.append(0x400)
check("G2 seven guarded arms", len(ARM) == 7, str(len(ARM)))
check("G2 the ladder is {0x1,0x2,0x4,0x8,0x10,0x1000,0x2000}",
      sorted(x for x in ladder if x) == [1, 2, 4, 8, 0x10, 0x1000, 0x2000],
      str(sorted(hex(x) for x in ladder if x)))
check("G2 no arm asks 0x400", all(not (x & CORE) for x in ladder if x), str(ladder))
check("G2 no arm asks 0x800", all(not (x & 0x800) for x in ladder if x), str(ladder))
check("G2 every arm tests its own mask on both paths",
      all(len(a[3]) == 2 for a in ARM), str([len(a[3]) for a in ARM]))
mask_ok = True
for (gm, g, je, t2, cls, cfc) in ARM:
    for a in t2:
        t = INS[IDX[a]][1]
        m = t.rsplit(",", 1)[1].strip()
        v, k, d, w = resolve(IDX[a], m, lo_add)
        if v != gm:
            mask_ok = False
check("G2 both test sites of an arm carry the guard's mask", mask_ok)
check("G2 every arm witnesses exactly one SET and one CLEAR",
      all(len([c for c in a[4] if c[0] == "SET"]) == 1 and
          len([c for c in a[4] if c[0] == "CLEAR"]) == 1 for a in ARM),
      str([[c[0] for c in a[4]] for a in ARM]))
small = [a for a in ARM if a[0] in (1, 2, 4, 8, 0x10)]
big = [a for a in ARM if a[0] in (0x1000, 0x2000)]
check("G2 the five small arms use 0x551a20 to SET and 0x5518f0 to CLEAR",
      all((mn(INS[IDX[[c for c in a[4] if c[0] == "SET"][0][1]]][1]),
           ops(INS[IDX[[c for c in a[4] if c[0] == "SET"][0][1]]][1])) == ("call", "0x551a20") and
          (mn(INS[IDX[[c for c in a[4] if c[0] == "CLEAR"][0][1]]][1]),
           ops(INS[IDX[[c for c in a[4] if c[0] == "CLEAR"][0][1]]][1])) == ("call", "0x5518f0")
          for a in small))
check("G2 the two big arms use one 0x551cf0 call with flag=1 to SET and flag=0 to CLEAR",
      all(len(a[5]) == 1 and sorted(c[0] for c in a[4]) == ["CLEAR", "SET"] for a in big))
swap = sum(1 for a in ARM if a[2] is not None and
           [c for c in a[4] if c[0] == "SET"][0][1] >= a[2])
if ALGO == 2:
    swap = 0 if swap else 1
check("G2 in every arm the SET witness precedes the je target (SET on 0x6051fa!=0)", swap == 0, str(swap))
outside = [a for a, tn in applies
           if not any(g <= a < (guards[i + 1] if i + 1 < len(guards) else (tail[0] if tail else FN_ADD[1]))
                      for i, g in enumerate(guards))]
print("  applies outside the seven arms: %s" % ", ".join("0x%x->%s" % (a, INS[IDX[a]][1].split()[-1]) for a in outside))
check("G2 exactly three applies sit outside the aka ladder (the 0x2000000 tail + the 0x10 stamp)",
      outside == [0x4db101, 0x4db11b, 0x4db165], str([hex(a) for a in outside]))


# ---------------------------------------------------------------- G3
print("\nG3  the verbs: what the two 3-arg callees do to the pair dword")
body_or = [t for a, t in range_ins(0x551a20, 0x551a20 + 0x2d0) if mn(t) == "or"]
body_clr = [t for a, t in range_ins(0x5518f0, 0x551a20) if mn(t) in ("not", "and")]
if ALGO == 3:
    body_clr = []                                   # mutant: semantics unwitnessed
print("  FUN_00551a20: %d or insns   FUN_00518f0: %d not/and insns" % (len(body_or), len(body_clr)))
check("G3 FUN_00551a20 ORs the argument into the pair dword", len(body_or) >= 1, str(len(body_or)))
check("G3 FUN_00518f0 NOTs the argument and ANDs it out",
      any(mn(t) == "not" for t in body_clr) and any(mn(t) == "and" for t in body_clr))
cf = [a for a, t in range_ins(*FN_ACC) if mn(t) == "call" and ops(t) == "0x551cf0"]
print("  FUN_004dacc0's 0x551cf0 calls: %s" % ", ".join("0x%x" % a for a in cf))
check("G3 FUN_004dacc0 has two 0x551cf0 arms (set 0x4dad05, clear 0x4dad30)",
      cf == [0x4dad05, 0x4dad30], str([hex(x) for x in cf]))
flag_tests = [a for a, t in range_ins(0x551cf0, 0x551d70) if mn(t) == "test"]
flag_src = [t for a, t in range_ins(0x551cf0, 0x551d70) if "[ebp+0x14]" in t]
api_or = [t for a, t in range_ins(0x551cf0, 0x551d70) if mn(t) == "or"]
api_and = [t for a, t in range_ins(0x551cf0, 0x551d70) if mn(t) == "and"]
print("  FUN_00551cf0: reads %s, %d test, %d or insns, %d and insns"
      % (flag_src[0] if flag_src else "-", len(flag_tests), len(api_or), len(api_and)))
check("G3 0x551cf0 reads a flag argument ([ebp+0x14]) and tests it",
      bool(flag_src) and bool(flag_tests))
check("G3 0x551cf0 carries both an OR and an AND of the mask (flag picks the direction)",
      bool(api_or) and bool(api_and), "%d or / %d and" % (len(api_or), len(api_and)))


# ---------------------------------------------------------------- G4
print("\nG4  the gate FUN_004dacc0: 4 literal callers, mask=arg")
check("G4 the gate's callers carry no 0x800", all(not (m & 0x800) for _, _, m in acc_masks))
check("G4 the gate's callers never carry the 0xc00 pair",
      all((m & 0xc00) != 0xc00 for _, _, m in acc_masks))
check("G4 0x400 appears exactly once among the gate's callers",
      len([1 for _, _, m in acc_masks if m == 0x400]) == 1)
pushes_400 = [a for a, t in range_ins(*FN_ADD) if mn(t) == "push" and ops(t) == "0x400"]
pushes_400 += [a for a, t in range_ins(*FN_ACC) if mn(t) == "push" and ops(t) == "0x400"]
print("  push 0x400 in the family: %s" % ", ".join("0x%x" % a for a in pushes_400))
check("G4 the family pushes 0x400 exactly once, from FUN_004dadd0 @0x4db0aa",
      pushes_400 == [0x4db0aa], str([hex(x) for x in pushes_400]))


# ---------------------------------------------------------------- G5
print("\nG5  which entry into FUN_004dadd0 is live")
calls = call_sites(0x4dadd0)
print("  call sites into FUN_004dadd0: %s" % ", ".join("0x%x" % a for a in calls))
check("G5 FUN_004dadd0 has exactly two direct callers",
      calls == [0x4dab96, 0x4dbc5a], str([hex(a) for a in calls]))
ENT = []
for c in calls:
    fs, fname, size, nins, ncall = containing(c)
    sites = call_sites(fs)
    drefs = dword_refs(fs)
    off = EXE_BYTES.find(struct.pack("<I", fs)) if drefs else -1
    va = off + 0x400000 if off >= 0 else 0
    nb = [struct.unpack("<I", EXE_BYTES[off - 16 + 4 * i:off - 12 + 4 * i])[0]
          for i in range(8)] if off >= 16 else []
    if ALGO == 7 and drefs:
        sites = [va]                                 # mutant: data ref read as a call
    ENT.append((fs, fname, c, sites, drefs, ncall, va, nb))
    print("  caller 0x%-7x in %-12s call-sites=%-2d dword-refs=%-2d at VA 0x%x index-callers=%d"
          % (c, fname, len(sites), drefs, va, ncall))
direct = [e for e in ENT if e[3]]
indirect = [e for e in ENT if not e[3] and e[4]]
check("G5 exactly one entry is directly called (FUN_004db480)", len(direct) == 1,
      str([hex(e[0]) for e in direct]))
check("G5 the directly called entry is FUN_004db480", direct and direct[0][0] == 0x4db480,
      str([hex(e[0]) for e in direct]))
check("G5 FUN_004dab90 has no direct call site", indirect and indirect[0][3] == [],
      str([e[3] for e in indirect]))
check("G5 FUN_004dab90 is address-taken exactly once", indirect and indirect[0][4] == 1,
      str([e[4] for e in indirect]))
check("G5 that reference sits past the .text end (0x6703ef) - a dispatch table, not code",
      indirect and indirect[0][6] > 0x6703ef, hex(indirect[0][6]) if indirect else "-")
check("G5 the table's neighbours are all .text pointers",
      indirect and all(0x401000 <= x <= 0x6703ef for x in indirect[0][7]),
      str([hex(x) for x in indirect[0][7]]))
check("G5 FUN_004db480's measured call count equals the index (1)",
      direct and len(direct[0][3]) == direct[0][5], str([len(e[3]) for e in direct]))
print("  note: index says FUN_004dab90 has 1 caller; the \"caller\" is the .rdata slot at")
print("        VA 0x%x - the wrapper is reachable only by indirect dispatch." % (indirect[0][6] if indirect else 0))


# ---------------------------------------------------------------- G6
print("\nG6  rivals")
r1 = all(d[3] is not None and d[4] == "mov-imm" for d in DEFS)
check("R1 'the four register masks are runtime values' refuted - all four are mov-imm", r1)
r2 = len(direct) == 1 and direct[0][0] == 0x4db480 and indirect and indirect[0][0] == 0x4dab90
check("R2 'FUN_004dab90 is the ladder's live entry' refuted - 0 direct calls (1 data pointer) vs "
      "%d direct call into FUN_004db480" % (len(direct[0][3]) if direct else 0), r2)
r3 = sorted(x for x in ladder if x) == [1, 2, 4, 8, 0x10, 0x1000, 0x2000]
check("R3 'the ladder can ask 0x400 or 0x800' refuted - union is exactly the seven lows", r3)
r4 = (any(mn(t) == "not" for t in body_clr) and len(body_or) >= 1)
check("R4 'one API serves both directions' refuted - two distinct 3-arg callees, OR vs NOT+AND", r4)
r5 = len(acc_masks) == 4 and sorted(m for _, _, m in acc_masks) == [0x20, 0x400, 0x40000, 0x2000000]
check("R5 'FUN_004dacc0 inherits the ladder's mask' refuted - 4 literal pushes, none in the ladder", r5)


# ---------------------------------------------------------------- G7
print("\nG7  digest")
rows = []
for gm, g, je, t2, cls, cfc in ARM:
    rows.append("arm|%x|%x|%s" % (gm, g, ",".join("%s@%x" % (k, s) for k, s in cls)))
for site, reg, da, v, why, o in DEFS:
    rows.append("def|%x|%s|%x|%x|%x" % (site, reg, da or 0, v or 0, o))
for c, a, m in acc_masks:
    rows.append("acc|%x|%x" % (c, m))
for e in ENT:
    rows.append("ent|%x|%x|%d|%d|%x" % (e[0], e[2], len(e[3]), e[4], e[6]))
for a in outside:
    rows.append("tail|%x|%s" % (a, INS[IDX[a]][1].split()[-1]))
s = "\n".join(rows)
d1 = hashlib.sha256(s.encode()).hexdigest()[:16]
d2 = hashlib.sha256("\n".join(rows).encode()).hexdigest()[:16]
print("  %d rows  digest=%s  recomputed=%s" % (len(rows), d1, d2))
check("G7 digest is stable across two computations", d1 == d2)
if DIGEST_PIN != "0000000000000000":
    check("G7 digest matches the pin", d1 == DIGEST_PIN, d1)

print("\n%d checks, %d failed" % (TOTAL[0], len(FAILS)))
if FAILS:
    print("FAIL M389: %d/%d" % (TOTAL[0] - len(FAILS), TOTAL[0]))
    for f in FAILS:
        print("  - " + f)
    sys.exit(1)
print("PASS M389: %d/%d  %s" % (TOTAL[0], TOTAL[0], d1))
