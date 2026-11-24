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
    """Backward scan inside the body; returns (addr, body) of the first write."""
    lo = func_of(i)[1]
    for j in range(i - 1, lo - 1, -1):
        a, b = INS[j]
        if writes(b, reg):
            return a, b
        if is_call(b) and ALGO != 1 and reg in CALLEE_SAVED:
            continue                       # callee-saved: a call cannot redefine it
        if is_call(b) and ALGO == 1:
            return a, b                    # law mutant: calls clobber
        if is_call(b) and reg not in CALLEE_SAVED:
            return a, b
    return None, None


def caller_census(fn):
    """All direct calls to fn: (call_addr, arg_text) with the pushed stack argument."""
    out = []
    pat = "0x%x" % fn
    for i, (a, b) in enumerate(INS):
        if not b.startswith("call") or pat not in b:
            continue
        arg = None
        for j in range(i - 1, max(-1, i - 8), -1):
            bb = INS[j][1]
            if bb.startswith("push"):
                arg = bb.split(None, 1)[1].strip()
                break
            if bb.startswith(("add    esp", "sub    esp", "call", "pop", "ret")):
                arg = "STACK-BROKEN"
                break
        out.append((a, arg))
    return out


def dword_occ(fn):
    data = open(EXE, "rb").read()
    pat = fn.to_bytes(4, "little")
    if ALGO == 4:
        data = data[:0x100000]
    return data.count(pat)


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
    da, db = reaching_def(i, reg)
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
                 "deftxt": db, "kind": kind, "val": val})
    print("  0x%-8x reg=%-3s func=0x%-8x def=0x%-8x %-8s %s"
          % (a, reg, fa, da if da else 0, kind, db))

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

# ---------------- G2 -----------------------------------------------------------
print("\nG2  STACKARG functions: call census + address-taken census (whole exe)")
mask_sets = {}
for fn in argfns:
    calls = caller_census(fn)
    occ = dword_occ(fn)
    print("  FUN_0x%x  call-site-insns=%d  absolute-dword-occurrences=%d" % (fn, len(calls), occ))
    for ca, arg in calls:
        print("    call @0x%-8x arg=%s" % (ca, arg))
    vals = set()
    for _, arg in calls:
        if arg and re.match(r"^0x[0-9a-f]+$", arg):
            vals.add(int(arg, 16))
        elif arg and re.match(r"^0x[0-9a-f]+$", str(arg)):
            vals.add(int(arg, 16))
    mask_sets[fn] = vals
    check("G2 FUN_0x%x address-taken occurrences 0" % fn, occ == 0, str(occ))
    if fn == 0x4DABB0:
        check("G2 FUN_0x4dabb0 has ZERO direct callers", len(calls) == 0, str(len(calls)))
    else:
        check("G2 FUN_0x4dacc0 has 4 direct callers", len(calls) == 4, str(len(calls)))
        check("G2 its pushed arg masks are {0x20,0x400,0x40000,0x2000000}",
              vals == {0x20, 0x400, 0x40000, 0x2000000},
              str(sorted(hex(v) for v in vals)))
        check("G2 every arg is a literal push (no register arg)",
              all(re.match(r"^0x[0-9a-f]+$", a or "") for _, a in calls),
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
            s = set(int(a, 16) for _, a in caller_census(r["func"])
                    if a and re.match(r"^0x[0-9a-f]+$", a))
        why = "4 caller pushes; no other reference to the function"
    b400 = sorted(v for v in s if v & 0x400)
    b800 = sorted(v for v in s if (v & (CORE if ALGO == 3 else 0x800)))
    pair = sorted(v for v in s if (v & CORE) == CORE)
    verdict.append((r["site"], r["func"], r["kind"], s, b400, b800, pair, why))
    print("  0x%-8x func=0x%-8x %-8s masks=%-28s 0x400:%-5s 0x800:%-5s 0xc00-pair:%-5s (%s)"
          % (r["site"], r["func"], r["kind"],
             ",".join(hex(v) for v in sorted(s)) or "-",
             ",".join(hex(v) for v in b400) or "no",
             ",".join(hex(v) for v in b800) or "no",
             ",".join(hex(v) for v in pair) or "no", why))
live = [v for v in verdict if v[3]]
check("G4 all nine masks decided (no unknown set)", len(verdict) == 9 and
      all(v[2] != "UNKNOWN" for v in verdict), str(len(verdict)))
check("G4 NO site's mask can contain 0x800", all(not v[5] for v in verdict),
      str([hex(v[0]) for v in verdict if v[5]]))
check("G4 NO site's mask can contain the 0xc00 PAIR", all(not v[6] for v in verdict),
      str([hex(v[0]) for v in verdict if v[6]]))
check("G4 exactly TWO sites can ask 0x400 alone (0x4dacf7 0x4dad22)",
      [v[0] for v in verdict if v[4]] == [0x4DACF7, 0x4DAD22],
      str([hex(v[0]) for v in verdict if v[4]]))
check("G4 the 0x400 sites are the SAME logical test, two je paths of FUN_0x4dacc0",
      verdict[2][1] == 0x4DACC0 and verdict[3][1] == 0x4DACC0, "func 0x4dacc0")

# ---------------- G5 -----------------------------------------------------------
print("\nG5  rivals (each must be refuted by the printed numbers)")
r1 = any(r["kind"] in ("UNKNOWN", "NONE") for r in rows) or \
    any(a is None or not re.match(r"^0x[0-9a-f]+$", a or "")
        for r in rows if r["kind"] == "STACKARG" for _, a in caller_census(r["func"]))
check("R1 'some site's mask is a runtime pair word loaded from memory' refuted", not r1,
      "every mask is a literal, or an arg pushed as a literal")
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

# ---------------- G6 -----------------------------------------------------------
print("\nG6  digest")
tbl = "\n".join("0x%x|0x%x|%s|%s|%s|%s|%s" % (v[0], v[1], v[2],
                                             ",".join("%x" % x for x in sorted(v[3])),
                                             ",".join("%x" % x for x in v[4]),
                                             ",".join("%x" % x for x in v[5]),
                                             ",".join("%x" % x for x in v[6])) for v in verdict)
h1 = hashlib.sha1(tbl.encode()).hexdigest()[:16]
h2 = hashlib.sha1("\n".join(tbl.split("\n")).encode()).hexdigest()[:16]
print("  digest=%s  recomputed=%s" % (h1, h2))
check("G6 digest stable and pinned", h1 == h2 and h1 == DIGEST_PIN, h1)

print("\nM385: %d/%d checks passed" % (TOTAL[0] - len(FAILS), TOTAL[0]))
if FAILS:
    print("FAIL: " + "; ".join(FAILS))
    sys.exit(1)
print("PASS M385: %d/%d  %s" % (TOTAL[0], TOTAL[0], h1))
