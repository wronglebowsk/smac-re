#!/usr/bin/env python3
"""M385 - can the nine `test [mem],reg` masks in the 0xc00 cluster ever name 0xc00?

M382 measured the population (15 immediate/register readers) but left the nine
DYNAMIC-mask inline sites (`test DWORD PTR [pair*4+0x94d448],reg`) unread: a
runtime mask could, in principle, contain 0x400 or 0x800.  This instrument walks
each site's mask register to its reaching definition, then walks STACK-COPIES
([ebp+8]) out to the callers' pushed arguments, and decides per site whether
0xc00 is in the attainable mask set.

  G0 parse     .text dump parses; the nine dynamic sites are re-derived, not authored.
  G1 def       backward def-use within the containing function: CONST imm / STACKARG.
  G2 callers   for STACKARG functions: every `call`, its pushed arg; plus a whole-file
               dword search for the function's absolute address (address-taken census).
  G3 or-compose the one register site whose mask is built by `or al,imm` (path set).
  G4 verdict   nine rows: attainable mask set, does it meet 0xc00, why not.
  G5 rivals    five rival readings, each REFUTED on the printed numbers.
  G6 digest    table digest computed twice.

M385_PATCH='addr|text' rewrites one instruction (mutants); M385_ALGO=n flips a law:
  1 calls clobber edi (ABI law off), 2 the `or al` path join is ignored (mask = imm),
  3 0x400 and 0x800 are read as one bit, 4 the body is bounded by the ebp frame
  (blind to the early ret that separates FUN_0x4dad40 from FUN_0x4dadd0).
"""
import hashlib
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M385_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.environ.get("M385_EXE", "/home/paul/reverse/smac/terran.exe")
FIELD = "94d448"
CORE = 0xC00
ALGO = int(os.environ.get("M385_ALGO", "0") or 0)
PATCH = os.environ.get("M385_PATCH", "")
DIGEST_PIN = "0103209f070e60f7"

spec = importlib.util.spec_from_file_location("m382", os.path.join(ROOT, "scripts/m382_treaty_readers.py"))
_m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_m)
INS = _m.apply_patch(_m.load_text(TEXT))
if PATCH:                                    # keep m382's parser, apply ours
    _a, _t = PATCH.split("|", 1)
    _a = int(_a, 16)
    INS = [(x, _t.strip() if x == _a else b) for x, b in INS]
ADDR = [a for a, b in INS]
CALLEE_SAVED = {"ebx", "esi", "edi", "ebp"}

FAILS = []
TOTAL = [0]


def check(name, cond, detail=""):
    TOTAL[0] += 1
    print(("  ok   " if cond else "  FAIL ") + name + ((" - " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)
    return cond


PARTS = {"al": "eax", "ah": "eax", "ax": "eax", "bl": "ebx", "bh": "ebx", "bx": "ebx",
         "cl": "ecx", "ch": "ecx", "cx": "ecx", "dl": "edx", "dh": "edx", "dx": "edx"}


def dest_of(body):
    m = re.match(r"[a-z]+\s+(\w+),", body)
    if not m:
        return None
    return m.group(1)


def writes(body, reg):
    d = dest_of(body)
    if d is None:
        return False
    return PARTS.get(d, d) == reg


def is_call(body):
    return body.startswith("call")


CALL_TARGETS = sorted(set(int(x, 16) for _, b in INS if b.startswith("call")
                          for x in re.findall(r"call\s+0x([0-9a-f]+)$", b)))
FRAME_STARTS = sorted(INS[j][0] for j in range(len(INS) - 1)
                      if INS[j][1].strip() == "push   ebp"
                      and INS[j + 1][1].strip().startswith("mov    ebp,esp"))
ENTRIES = sorted(set(CALL_TARGETS) | set(FRAME_STARTS))


def frame_start(i):
    for j in range(i, -1, -1):
        if INS[j][1].strip() == "push   ebp" and j + 1 < len(INS) \
                and INS[j + 1][1].strip().startswith("mov    ebp,esp"):
            return j
    return 0


def func_of(i):
    """Containing body = the greatest ENTRY at or below the site.

    The dump is a flat .text (no symbols), and these bodies have EARLY rets, so a
    `ret` boundary is unsound.  Entries are the addresses a `call` reaches PLUS the
    ebp-frame prologues: FUN_0x4dabb0 has no caller at all, so only its own prologue
    marks it (a call-target-only rule silently folds it into the prior body).
    """
    a = INS[i][0]
    if ALGO == 4:                        # law mutant: frame start alone (misses frameless bodies)
        j = frame_start(i)
        return INS[j][0], j
    cand = [t for t in ENTRIES if t <= a]
    if cand:
        t = cand[-1]
        return t, ADDR.index(t)
    j = frame_start(i)
    return INS[j][0], j


def dynamic_sites():
    out = []
    for a, b in INS:
        if b.startswith("test ") and "DWORD PTR" in b and FIELD in b \
                and not re.search(r",(0x[0-9a-f]+)$", b):
            out.append((a, b))
    return out


def reaching_def(i, reg):
    """Backward scan inside the body; returns (addr, body, bypass) of the first write.

    `bypass` is True when some branch/jump whose SOURCE lies outside [def, site]
    targets an address inside (def, site): then a path reaches the site without
    executing the def, and the nearest linear write is not the only reaching def.
    """
    lo = func_of(i)[1]
    da, db = None, None
    for j in range(i - 1, lo - 1, -1):
        a, b = INS[j]
        if writes(b, reg):
            da, db = a, b
            break
        if is_call(b) and ALGO != 1 and reg in CALLEE_SAVED:
            continue                       # callee-saved: a call cannot redefine it
        if is_call(b) and ALGO == 1:
            return a, b, True              # law mutant: calls clobber
        if is_call(b) and reg not in CALLEE_SAVED:
            return a, b, True
    if db is None:
        return None, None, True
    if ALGO == 5:                          # law mutant: every forward branch counts as an entry
        return da, db, any(da < int(m.group(1), 16) <= INS[i][0]
                           for k in range(0, i + 1)
                           for m in [re.search(r"(?:j\w+|loop)\s+0x([0-9a-f]+)$", INS[k][1])] if m)
    bypass = False
    for k in range(0, i + 1):
        bb = INS[k][1]
        if not (bb.startswith("j") or bb.startswith("loop")):
            continue
        m = re.search(r"(?:j\w+|loop)\s+0x([0-9a-f]+)$", bb)
        if not m:
            continue
        t = int(m.group(1), 16)
        if da < t <= INS[i][0] and not (da <= INS[k][0] <= INS[i][0]):
            bypass = True
    return da, db, bypass


def callee_argc(fn):
    """(n_ret4, n_other_ret) over the callee's entry body - the `ret 0x4` shape."""
    lo = ADDR.index(fn)
    hi = len(INS)
    for k in range(lo + 1, len(INS)):
        if INS[k][0] in ENTRIES and k > lo + 1:
            hi = k
            break
    n4 = sum(1 for k in range(lo, hi) if INS[k][1].startswith("ret    0x4"))
    no = sum(1 for k in range(lo, hi) if INS[k][1].startswith("ret")
             and not INS[k][1].startswith("ret    0x4"))
    return n4, no


def caller_census(fn):
    """All EXACT direct calls to fn: (call_addr, arg_text, n_pushes_before_call)."""
    out = []
    pat = re.compile(r"call\s+0x%x$" % fn)
    for i, (a, b) in enumerate(INS):
        if not pat.match(b):
            continue
        arg, npush = None, 0
        for j in range(i - 1, max(-1, i - 8), -1):
            bb = INS[j][1]
            if bb.startswith("push"):
                npush += 1
                if arg is None:
                    arg = bb.split(None, 1)[1].strip()
                continue
            if bb.startswith(("add    esp", "sub    esp", "pop", "ret", "call")):
                break
        if arg is None:
            arg = "STACK-BROKEN"
        out.append((a, arg, npush))
    return out


EXEDATA = open(EXE, "rb").read()


def dword_occ(fn):
    data = EXEDATA
    if ALGO == 4:
        data = data[:0x100000]
    return data.count(fn.to_bytes(4, "little"))


print("M385 nine dynamic-mask sites - field = DWORD [pair*4 + 0x%s]" % FIELD)

# ---------------- G0 -----------------------------------------------------------
print("\nG0  parse / population")
sites = dynamic_sites()
print("  insns=%d  dynamic-mask inline sites=%d" % (len(INS), len(sites)))
for a, b in sites:
    print("  0x%-8x %s" % (a, b))
check("G0 insn count 781429", len(INS) == 781429, str(len(INS)))
check("G0 nine dynamic sites", len(sites) == 9, str(len(sites)))

# ---------------- G1 -----------------------------------------------------------
print("\nG1  mask register -> reaching definition (inside the containing function)")
rows = []
for a, b in sites:
    i = ADDR.index(a)
    reg = b.rsplit(",", 1)[1].strip()
    fa, _lo = func_of(i)
    da, db, bypass = reaching_def(i, reg)
    if db is None:
        kind, val = "NONE", None
    elif re.match(r"mov\s+%s,(0x[0-9a-f]+)$" % reg, db):
        kind, val = "CONST", int(db.rsplit(",", 1)[1], 16)
    elif re.match(r"mov\s+%s,DWORD PTR \[ebp\+0x[0-9a-f]+\]$" % reg, db):
        kind, val = "STACKARG", db.rsplit("[", 1)[1].rstrip("]")
    elif db.startswith("or") and db.startswith("or     "):
        kind, val = "ORIMM", db
    else:
        kind, val = "UNKNOWN", db
    rows.append({"site": a, "text": b, "reg": reg, "func": fa, "def": da,
                 "deftxt": db, "kind": kind, "val": val, "bypass": bypass})
    print("  0x%-8x reg=%-3s func=0x%-8x def=0x%-8x %-8s %-9s %s"
          % (a, reg, fa, da if da else 0, kind, "BYPASS" if bypass else "dominates", db))

consts = [(r["site"], r["val"]) for r in rows if r["kind"] == "CONST"]
argfns = sorted(set(r["func"] for r in rows if r["kind"] == "STACKARG"))
print("  CONST sites: %s" % ", ".join("0x%x=0x%x" % c for c in consts))
print("  STACKARG functions: %s" % ", ".join("0x%x" % f for f in argfns))
check("G1 four CONST masks", len(consts) == 4, str(len(consts)))
check("G1 const masks are {0x1000 x2, 0x2000 x2}",
      sorted(v for _, v in consts) == [0x1000, 0x1000, 0x2000, 0x2000],
      str(sorted(hex(v) for _, v in consts)))
check("G1 four STACKARG sites in two functions", len([r for r in rows if r["kind"] == "STACKARG"]) == 4
      and argfns == [0x4DABB0, 0x4DACC0], str(argfns))
check("G1 one ORIMM site 0x%x" % 0x574A66,
      [r["site"] for r in rows if r["kind"] == "ORIMM"] == [0x574A66],
      str([hex(r["site"]) for r in rows if r["kind"] == "ORIMM"]))
check("G1 the four literal sites sit in FUN_0x4dadd0 (an early ret ends 0x4dad40)",
      [r["func"] for r in rows if r["kind"] == "CONST"] == [0x4DADD0] * 4,
      str([hex(r["func"]) for r in rows if r["kind"] == "CONST"]))
check("G1 no UNKNOWN/NONE row", not any(r["kind"] in ("UNKNOWN", "NONE") for r in rows),
      str([hex(r["site"]) for r in rows if r["kind"] in ("UNKNOWN", "NONE")]))
check("G1 every reaching def DOMINATES its site (no branch enters the def-site gap)",
      not any(r["bypass"] for r in rows),
      str([hex(r["site"]) for r in rows if r["bypass"]]))

# ---------------- G2 -----------------------------------------------------------
print("\nG2  STACKARG functions: call census + address-taken census (whole exe)")
print("  exe: %s  size=%d B" % (EXE, len(EXEDATA)))
check("G2 the censused file is the 3,067,904-B terran.exe", len(EXEDATA) == 3067904, str(len(EXEDATA)))
mask_sets = {}
for fn in argfns:
    calls = caller_census(fn)
    occ = dword_occ(fn)
    n4, no = callee_argc(fn)
    print("  FUN_0x%x  call-site-insns=%d  absolute-dword-occurrences=%d  ret4=%d other-ret=%d"
          % (fn, len(calls), occ, n4, no))
    for ca, arg, np in calls:
        print("    call @0x%-8x arg=%-10s pushes=%d" % (ca, arg, np))
    vals = set()
    for _, arg, _np in calls:
        if arg and re.match(r"^0x[0-9a-f]+$", str(arg)):
            vals.add(int(arg, 16))
    mask_sets[fn] = vals
    check("G2 FUN_0x%x address-taken occurrences 0" % fn, occ == 0, str(occ))
    check("G2 FUN_0x%x has the `ret 0x4` one-arg shape" % fn, n4 >= 1 and no == 0,
          "ret4=%d other=%d" % (n4, no))
    if fn == 0x4DABB0:
        check("G2 FUN_0x4dabb0 has ZERO direct callers", len(calls) == 0, str(len(calls)))
    else:
        check("G2 FUN_0x4dacc0 has 4 direct callers", len(calls) == 4, str(len(calls)))
        check("G2 each call carries EXACTLY ONE pushed argument",
              all(np == 1 for _, _, np in calls), str(calls))
        check("G2 its pushed arg masks are {0x20,0x400,0x40000,0x2000000}",
              vals == {0x20, 0x400, 0x40000, 0x2000000},
              str(sorted(hex(v) for v in vals)))
        check("G2 every arg is a literal push (no register arg)",
              all(re.match(r"^0x[0-9a-f]+$", a or "") for _, a, _ in calls),
              str(calls))
        check("G2 the 0x400 mask reaches the pair test: a NEW 0x400-only reader",
              0x400 in vals, "push 0x400 @0x4db0aa")
        check("G2 no pushed arg carries 0x800", not any(v & 0x800 for v in vals),
              str(sorted(hex(v) for v in vals)))
        check("G2 no pushed arg carries the 0xc00 PAIR", not any((v & CORE) == CORE for v in vals),
              str(sorted(hex(v) for v in vals)))

# ---------------- G3 -----------------------------------------------------------
print("\nG3  site 0x574a66: mask built by `or al,imm` on two converging paths")
i = ADDR.index(0x574A66)
win = [(a, b) for a, b in INS[max(0, i - 20):i]]
for a, b in win:
    print("  0x%-8x %s" % (a, b))
vals = set()
for a, b in win:
    if re.match(r"xor\s+eax,eax$", b):
        vals.add(0)
    if re.match(r"mov\s+eax,(0x[0-9a-f]+)$", b):
        vals.add(int(b.rsplit(",", 1)[1], 16))
print("  pre-OR eax candidates: %s" % sorted(hex(v) for v in vals))
orm = [int(x, 16) for a, b in win for x in re.findall(r"or\s+al,(0x[0-9a-f]+)", b)]
print("  `or al` immediates: %s" % [hex(v) for v in orm])
if ALGO == 2:
    composed = set(orm[:1])                    # law mutant: the join is ignored
else:
    composed = set((v & ~0xFF) | ((v & 0xFF) | (orm[0] if orm else 0)) for v in vals)
print("  attainable mask set: %s" % sorted(hex(v) for v in composed))
check("G3 two pre-OR candidates {0x0,0x10}", vals == {0, 0x10}, str(sorted(hex(v) for v in vals)))
check("G3 composed set is exactly {0x20,0x30}", composed == {0x20, 0x30},
      str(sorted(hex(v) for v in composed)))
mask_sets[0x574A66] = composed

# ---------------- G4 -----------------------------------------------------------
print("\nG4  VERDICT - attainable mask per site, per 0xc00 bit")
verdict = []
for r in rows:
    if r["kind"] == "CONST":
        s = {r["val"]}
        why = "literal imm in the same function"
    elif r["kind"] == "ORIMM":
        s = composed
        why = "xor/mov + `or al,imm` path set"
    elif r["func"] == 0x4DABB0:
        s = set()
        why = "zero callers + not address-taken -> never invoked"
    else:
        s = mask_sets.get(r["func"])
        if s is None:                    # function missed the STACKARG census: derive here
            s = set(int(a, 16) for _, a, _n in caller_census(r["func"])
                    if a and re.match(r"^0x[0-9a-f]+$", a))
        why = "4 caller pushes; no other reference to the function"
    b400 = sorted(v for v in s if v == 0x400)          # "0x400 ALONE" == the mask
    b400x = sorted(v for v in s if (v & 0x400) and v != 0x400)
    b800 = sorted(v for v in s if (v & (CORE if ALGO == 3 else 0x800)))
    pair = sorted(v for v in s if (v & CORE) == CORE)
    status = "DEAD-INF" if r["func"] == 0x4DABB0 else "PROVEN"
    verdict.append((r["site"], r["func"], r["kind"], s, b400, b800, pair, status, why, b400x))
    print("  0x%-8x func=0x%-8x %-8s %-8s masks=%-28s 0x400-only:%-5s 0x800:%-5s 0xc00-pair:%-5s"
          % (r["site"], r["func"], r["kind"], status,
             ",".join(hex(v) for v in sorted(s)) or "-",
             ",".join(hex(v) for v in b400) or "no",
             ",".join(hex(v) for v in b800) or "no",
             ",".join(hex(v) for v in pair) or "no"))
live = [v for v in verdict if v[7] == "PROVEN"]
check("G4 seven sites are PROVEN from a dominating def; two are DEAD-INF (no static entry)",
      len(live) == 7 and sum(1 for v in verdict if v[7] == "DEAD-INF") == 2,
      str([(hex(v[0]), v[7]) for v in verdict]))
check("G4 NO PROVEN site's mask can contain 0x800",
      all(not v[5] for v in verdict if v[7] == "PROVEN"),
      str([hex(v[0]) for v in verdict if v[7] == "PROVEN" and v[5]]))
check("G4 NO PROVEN site's mask can contain the 0xc00 PAIR",
      all(not v[6] for v in verdict if v[7] == "PROVEN"),
      str([hex(v[0]) for v in verdict if v[7] == "PROVEN" and v[6]]))
check("G4 exactly TWO PROVEN sites can ask 0x400 ALONE (0x4dacf7 0x4dad22)",
      [v[0] for v in verdict if v[4]] == [0x4DACF7, 0x4DAD22],
      str([hex(v[0]) for v in verdict if v[4]]))
check("G4 no mask mixes 0x400 with another bit at any site",
      not any(v[9] for v in verdict), str([hex(x) for v in verdict for x in v[9]]))
check("G4 the 0x400 sites are the SAME logical test, two je paths of FUN_0x4dacc0",
      verdict[2][1] == 0x4DACC0 and verdict[3][1] == 0x4DACC0, "func 0x4dacc0")

# ---------------- G5 -----------------------------------------------------------
print("\nG5  rivals (each must be refuted by the printed numbers)")
r1 = any(r["kind"] in ("UNKNOWN", "NONE") for r in rows) or \
    any(r["bypass"] for r in rows) or \
    any(a is None or not re.match(r"^0x[0-9a-f]+$", a or "")
        for r in rows if r["kind"] == "STACKARG" for _, a, _n in caller_census(r["func"]))
check("R1 'some site's mask is a runtime pair word loaded from memory' refuted", not r1,
      "every def dominates its site and is a literal or an arg pushed as a literal")
r2 = (dword_occ(0x4DABB0) > 0) or (len(caller_census(0x4DABB0)) > 0)
check("R2 'FUN_0x4dabb0 is live and gets 0xc00 from an unseen caller' refuted", not r2,
      "0 calls, 0 dword occurrences in 3067904 B")
r3 = any(r["kind"] == "STACKARG" for r in rows if r["func"] == 0x4DADD0)
check("R3 '0x4dadd0's 0x1000/0x2000 sites inherit the arg' refuted", not r3,
      "nearest def is the literal, after the prologue's [ebp+8]")
r4 = any(v & 0xFFFFFF00 for v in composed)
check("R4 '0x574a66's high eax bytes could carry 0xc00' refuted", not r4,
      "xor eax,eax / mov eax,0x10 write the whole dword")
r5 = any((v & CORE) == CORE for v in set().union(*mask_sets.values()))
check("R5 'the generic wrapper admits any mask' refuted", not r5,
      str(sorted(hex(v) for v in set().union(*mask_sets.values()))))

# ---------------- G7 -----------------------------------------------------------
print("\nG7  attribution cross-check against ghidra_out/index.csv")
import csv
IDX = os.environ.get("M385_INDEX", os.path.expanduser("~/reverse/smac/ghidra_out/index.csv"))
FNS = []
with open(IDX) as f:
    for d in csv.DictReader(l for l in f if not l.startswith("#")):
        FNS.append((int(d["addr"], 16), int(d["size_bytes"]), d["name"]))
FNS.sort()


def owner(a):
    best = None
    for addr, size, name in FNS:
        if addr <= a < addr + size:
            best = (addr, name)
        elif addr > a:
            break
    return best or (0, "?")


attr_ok = 0
for v in verdict:
    oa, on = owner(v[0])
    print("  0x%-8x func_of=0x%-8x index=%s" % (v[0], v[1], on))
    attr_ok += (oa == v[1])
check("G7 func_of agrees with index.csv on all nine sites", attr_ok == 9, str(attr_ok))
names = {v[0]: owner(v[0])[1] for v in verdict}
check("G7 hosts are FUN_004dabb0 / 004dacc0 / 004dadd0 / 00574370",
      names == {0x4DABE7: "FUN_004dabb0", 0x4DAC10: "FUN_004dabb0",
                0x4DACF7: "FUN_004dacc0", 0x4DAD22: "FUN_004dacc0",
                0x4DB003: "FUN_004dadd0", 0x4DB01F: "FUN_004dadd0",
                0x4DB063: "FUN_004dadd0", 0x4DB07F: "FUN_004dadd0",
                0x574A66: "FUN_00574370"}, str(names))
check("G7 index.csv sizes split the neighbours (0x4dad40 ends before 0x4dadd0)",
      owner(0x4DADD0)[1] == "FUN_004dadd0" and owner(0x4DB003)[1] == "FUN_004dadd0",
      "0x4dadd0")

# ---------------- G8 -----------------------------------------------------------
print("\nG8  cross-milestone population (reads M382's own PASS evidence)")
M382EV = os.environ.get("M385_M382EV", os.path.join(ROOT, "evidence/m382_treaty_readers.txt"))
ev_lines = open(M382EV, encoding="utf-8", errors="replace").read().splitlines()
m382_pass = any(l.startswith("PASS M382:") for l in ev_lines)
m382_400 = [l for l in ev_lines if re.search(r"test 0x[0-9a-f]+\s+mask=0x400(\s|$)", l)]
print("  M382 PASS line present: %s" % m382_pass)
print("  M382 0x400-only register readers: %d" % len(m382_400))
for l in m382_400:
    print("   %s" % l.strip())
new400 = [v[0] for v in verdict if v[4]]
print("  M385 0x400-only sites: %d" % len(new400))
check("G8 M382's evidence is a passing run", m382_pass, M382EV)
check("G8 M382 had exactly ONE 0x400-only register reader (0x5552ff)", len(m382_400) == 1,
      str(len(m382_400)))
check("G8 total 0x400-only readers is 3 (1 + 2 here) - the retraction is COUNTED",
      len(m382_400) + len(new400) == 3, str(len(m382_400) + len(new400)))
check("G8 population 15 -> 17", 15 + len(new400) == 17, str(15 + len(new400)))

# ---------------- G6 -----------------------------------------------------------
print("\nG6  digest (second derivation from the parsed rows)")
import json


def recompute_set(r):
    if r["kind"] == "CONST":
        m = re.match(r"mov\s+\w+,(0x[0-9a-f]+)$", r["deftxt"] or "")
        return {int(m.group(1), 16)} if m else set()
    if r["kind"] == "ORIMM":
        return composed
    if r["func"] == 0x4DABB0:
        return set()
    return set(int(a, 16) for _, a, _n in caller_census(r["func"])
               if a and re.match(r"^0x[0-9a-f]+$", a))


tbl = "\n".join("0x%x|0x%x|%s|%s|%s|%s|%s" % (v[0], v[1], v[2],
                                             ",".join("%x" % x for x in sorted(v[3])),
                                             ",".join("%x" % x for x in v[4]),
                                             ",".join("%x" % x for x in v[5]),
                                             ",".join("%x" % x for x in v[6])) for v in verdict)
tbl2 = "\n".join("0x%x|0x%x|%s|%s|%s|%s|%s" % (v[0], v[1], v[2],
                                               ",".join("%x" % x for x in sorted(recompute_set(r))),
                                               ",".join("%x" % x for x in sorted(x for x in recompute_set(r) if x == 0x400)),
                                               ",".join("%x" % x for x in sorted(x for x in recompute_set(r) if x & 0x800)),
                                               ",".join("%x" % x for x in sorted(x for x in recompute_set(r) if (x & CORE) == CORE)))
                for v, r in zip(verdict, rows))
h1 = hashlib.sha1(tbl.encode()).hexdigest()[:16]
h2 = hashlib.sha1(tbl2.encode()).hexdigest()[:16]
print("  digest=%s  recomputed=%s  tables_equal=%s" % (h1, h2, tbl == tbl2))
check("G6 the two derivations agree", tbl == tbl2 and h1 == h2, h1 + "/" + h2)
check("G6 digest stable and pinned", h1 == DIGEST_PIN, h1)

print("\nM385: %d/%d checks passed" % (TOTAL[0] - len(FAILS), TOTAL[0]))
if FAILS:
    print("FAIL: " + "; ".join(FAILS))
    sys.exit(1)
print("PASS M385: %d/%d  %s" % (TOTAL[0], TOTAL[0], h1))
