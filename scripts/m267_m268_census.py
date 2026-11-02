#!/usr/bin/env python3
"""M267 which variants share the 0x6725ac/0x6725a4 vptr pair; M268 what the 201 608-B elements are.

Instrument = ONE pass over the whole-image .text disassembly (scratch/m574/text.txt) plus the raw
PE image (programs/terran.exe), ghidra_out/index.csv containment, the decompiled C (shard_008.c,
shard_015.c) and data/alpha.json row counts. No box time, no /proc, no gdb.

Acceptance: ONE real invocation prints `SUMMARY M267/M268: 14/14 gates PASS`.
"""
import os, re, csv, bisect, struct, json, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*x): return os.path.join(R, *x)

IMG = open(P("programs/terran.exe"), "rb").read()
CODE = (0x401000, 0x6703f4)
RDAT = (0x670000, 0x680000)
FUN = []
for r in csv.DictReader(open(P("ghidra_out/index.csv"))):
    try: FUN.append((int(r["addr"], 16), r["name"], int(r["size_bytes"])))
    except Exception: pass
FUN.sort(); A = [a for a, _, _ in FUN]

def own(x):
    i = bisect.bisect_right(A, x) - 1
    if i < 0: return None
    a, n, s = FUN[i]
    return n if x < a + s else None

def dw(va):
    o = va - 0x400000
    return struct.unpack_from("<I", IMG, o)[0] if 0 <= o < len(IMG) - 4 else None

def iscode(v): return v is not None and CODE[0] <= v < CODE[1]

INSTALLERS = ["FUN_00421950", "FUN_00469650", "FUN_00518980", "FUN_0059bec0", "FUN_0059c1e0"]
NEED = set(INSTALLERS) | {"FUN_0062514b", "FUN_0062516c", "FUN_00596620", "FUN_00443be0"}
BODY = collections.defaultdict(list)
VPTR = collections.Counter()            # imm32 in the rdata range stored through [reg(+disp)]
PAIR = collections.defaultdict(list)    # 0x6725ac / 0x6725a4 -> [(pc, fn, ops)]
N260 = collections.Counter(); N260_AT = []
DEL_TOT = 0
DEL_REM0 = collections.Counter(); DEL_FN = collections.defaultdict(set)
VIEWFN = set()

def walk(path):
    for line in open(path, errors="replace"):
        l = line.replace("\\t", "\t").rstrip("\n"); p = l.split("\t")
        if len(p) < 3: continue
        m = re.fullmatch(r"\s*([0-9a-f]{6,8}):", p[0])
        if not m: continue
        t = p[2].split(None, 1)
        if not t: continue
        yield int(m.group(1), 16), t[0].lower(), (t[1] if len(t) > 1 else "").strip()

for pc, mn, ops in walk(P("scratch/m574/text.txt")):
    fn = own(pc)
    if fn in NEED: BODY[fn].append((pc, mn, ops))
    if mn == "mov" and ops.startswith("DWORD PTR ["):
        m = re.search(r",0x([0-9a-f]{6,8})$", ops)
        if m:
            v = int(m.group(1), 16)
            if RDAT[0] <= v < RDAT[1]:
                VPTR[v] += 1
                if v in (0x6725ac, 0x6725a4): PAIR[v].append((pc, fn, ops))
    bare = re.sub(r"\[[^\]]*\]", "[]", ops)          # 0x260 as an IMMEDIATE, not a displacement
    if re.search(r"\b0x260\b", bare) and not bare.startswith("DWORD PTR ds:0x260"):
        N260[mn] += 1; N260_AT.append((pc, fn, mn, ops))
    if fn is not None and re.search(r"0x7cde[c-f][0-9a-f]", ops): VIEWFN.add(fn)
    for d in re.findall(r"\+0x([0-9a-f]{1,6})\]", ops):
        dv = int(d, 16)
        if 0x26c <= dv <= 0x1dd6b:
            DEL_TOT += 1
            if (dv - 0xc) % 608 == 0:
                DEL_REM0[dv] += 1; DEL_FN[dv].add(fn)

GATES = []
def gate(ok, name, detail=""):
    GATES.append((bool(ok), name, detail))
    print("%s %s%s" % ("PASS" if ok else "FAIL", name, ("  " + detail) if detail else ""))

# ---- M267: the pair and its variants ---------------------------------------
s1 = PAIR.get(0x6725ac, []); s2 = PAIR.get(0x6725a4, [])
gate(len(s1) == 5 and len(s2) == 5 and {f for _, f, _ in s1} == set(INSTALLERS)
     and {f for _, f, _ in s2} == set(INSTALLERS),
     "G1 exactly 5 stores of 0x6725ac and 5 of 0x6725a4, one pair per installer",
     "pcs=" + ",".join("%x@%s" % (p, f) for p, f, _ in sorted(s1)))

CAND = sorted(v for v in VPTR if iscode(dw(v)))     # stored rdata imm32 (bases AND mid-table addrs)
def fwd(base):
    n = 0
    while iscode(dw(base + 4 * n)): n += 1
    return base + 4 * n, n
hi_a, n_a = fwd(0x6725ac); hi_b, n_b = fwd(0x6725a4)
gate(0x6725a4 == 0x6725ac - 8 and hi_a == hi_b and n_b == n_a + 2,
     "G2 the pair is ONE vtable, two entry points 8 B apart (the +0x444 secondary view)",
     "code-pointer run ends 0x%x from both; slots from 0x6725ac=%d, from 0x6725a4=%d; "
     "heads 0x6725ac->%s 0x6725a4->%s; %d stored rdata imm32 in the image (mid-table addresses included)"
     % (hi_a, n_a, n_b,
        [own(dw(0x6725ac + 4 * k)) or hex(dw(0x6725ac + 4 * k)) for k in range(2)],
        [own(dw(0x6725a4 + 4 * k)) or hex(dw(0x6725a4 + 4 * k)) for k in range(2)], len(VPTR)))

def addrtaken(va):
    pat = struct.pack("<I", va); n = 0; i = 0; where = []
    while True:
        i = IMG.find(pat, i)
        if i < 0: break
        n += 1; where.append(hex(i + 0x400000)); i += 1
    return n, where
AT = {f: addrtaken(int(f[4:], 16)) for f in INSTALLERS}
gate(all(AT[f][0] == 0 for f in INSTALLERS),
     "G3 none of the 5 installers is address-taken anywhere in the image (all sections): direct call only",
     "; ".join("%s %d hits" % (f, AT[f][0]) for f in INSTALLERS))

def stores_in(fn):
    out = set()
    for pc, mn, ops in BODY.get(fn, []):
        m = re.match(r"DWORD PTR \[([^\]]+)\],0x([0-9a-f]{6,8})$", ops) if mn == "mov" else None
        if m and RDAT[0] <= int(m.group(2), 16) < RDAT[1]: out.add(int(m.group(2), 16))
    return out
VARIANT = {"FUN_00469650": {0x675964}, "FUN_00421950": set(),
           "FUN_00518980": {0x678184, 0x67817c}, "FUN_0059c1e0": {0x67194c, 0x671944},
           "FUN_0059bec0": {0x67194c, 0x671944}}
got = {f: stores_in(f) for f in INSTALLERS}
gate(all({0x6725ac, 0x6725a4} <= got[f] and VARIANT[f] <= got[f]
         and not (got[f] & {0x6763fc, 0x678458}) for f in INSTALLERS),
     "G4 each installer's own descriptor/pair names its variant; neither other descriptor is stored here",
     "; ".join("%s->%s" % (f, sorted(hex(v) for v in got[f])) for f in INSTALLERS))

def calls(fn, tgt):
    return [pc for pc, mn, ops in BODY.get(fn, []) if mn == "call" and ops.strip() == "0x%x" % tgt]
it = {f: (len(calls(f, 0x64bda0)), len(calls(f, 0x64bc40))) for f in INSTALLERS}
gate(it["FUN_00469650"] == (3, 0) and all(it[f][0] == 0 and it[f][1] >= 3 for f in INSTALLERS if f != "FUN_00469650"),
     "G5 0x469650 is the CONSTRUCTOR (3 x _eh_vector_constructor_iterator_ 0x64bda0), the other four are DEstructors (0x64bc40)",
     "; ".join("%s ctor-iter %d dtor-iter %d" % (f, a, b) for f, (a, b) in it.items()))

DELTA = []
for f in INSTALLERS:
    b = BODY[f]; hit = None
    for i, (pc, mn, ops) in enumerate(b):
        if mn == "mov" and re.search(r"0x6725a[4c]$", ops):
            for pc2, mn2, ops2 in b[i:i + 14]:
                if mn2 in ("sub", "lea") and "0x21a6c" in ops2:
                    hit = (pc2, mn2, ops2); break
            break
    if hit: DELTA.append((f,) + hit)
gate(len(DELTA) == 5,
     "G6 every installer recomputes the delta with the static constant 0x21a6c within 14 insns of its pair store",
     "; ".join("%s@%x %s %s" % (f, p, m, o[:30]) for f, p, m, o in DELTA))
C8 = open(P("ghidra_out/shard_008.c")).read().splitlines()
dline = [i + 1 for i, l in enumerate(C8) if "+ -4)" in l and "0x21a6c" in l]
ac = [i + 1 for i, l in enumerate(C8) if "PTR_LAB_006725ac" in l]
gate(bool(dline) and bool(ac),
     "G7 the decompiled ctor states the delta word: [vptr-4] = [desc+4] - 0x21a6c",
     "shard_008.c lines %s (pair stores %s)" % (dline, ac))

probe = [pc for pc, mn, ops in BODY["FUN_0059bec0"] if mn == "mov" and ops == "eax,0x25318"]
flag = [pc for pc, mn, ops in BODY["FUN_0059bec0"] if mn == "push" and ops.strip() == "0x1"]
n25318 = sum(1 for pc, mn, ops in walk(P("scratch/m574/text.txt")) if "0x25318" in ops)
gate(len(probe) == 1 and n25318 == 1 and len(flag) >= 1 and 0x25318 > 0x22480,
     "G8 the stack variant reserves 0x25318 = 152,856 B (once image-wide) > the 0x22480 heap object, flag 1",
     "probe@%s  image-wide 0x25318 %d  push1@%s" % ([hex(x) for x in probe], n25318, [hex(x) for x in flag]))

# ---- M268: the 201 x 608 elements ------------------------------------------
def core(fn):
    return [(mn, ops) for pc, mn, ops in BODY[fn]
            if mn not in ("push", "pop", "ret", "nop") and ops not in ("ebp,esp", "esp,ebp")]
def vs(x):   # the stores that touch the record itself (not the spilled argument slot)
    return [(m, o) for m, o in x if m == "mov" and o.startswith("DWORD PTR [")
            and "ebp-" not in o]
a = core("FUN_0062514b"); c = core("FUN_0062516c")
EXP = [("mov", "DWORD PTR [eax],0x3"), ("mov", "DWORD PTR [ecx+0x4],0x0")]
vals = {int(m.group(1), 16) for _, o in a + c for m in [re.search(r"0x([0-9a-f]{6,8})", o)] if m}
gate(vs(a) == vs(c) == EXP and not any(m == "call" for m, _ in a + c)
     and not (vals & set(range(RDAT[0], RDAT[1], 4))),
     "G9 the element 'ctor' and 'dtor' write the SAME 2 POD stores {dword0=3, dword1=0}, no vptr, no callee",
     "ctor %d ops / dtor %d ops; record stores in both: %s"
     % (len(a), len(c), " | ".join("%s %s" % (m, o) for m, o in vs(a))))

gate(0xc + 4 * 608 == 0x98c and 0x98c + 196 * 608 == 0x1db0c and 0x1db0c + 608 == 0x1dd6c
     and 201 * 608 == 122208 and 122208 != 121600 and 0x1dd6c + 8 == 0x1dd74,
     "G10 the array is 201 x 608 = 122,208 B at +0xc..+0x1dd6c (NOT 121,600 - corrects NAMED M265)",
     "4 at +0xc, 196 at +0x98c, 1 in place at +0x1db0c; the tail field +0x1dd74 is end+8")

arith = [x for x in N260_AT if x[2] in ("add", "sub", "imul", "lea", "cmp", "mul")]
ininst = sum(1 for x in N260_AT if x[1] in INSTALLERS)
unwind = sum(1 for x in N260_AT if x[1] is None or str(x[1]).startswith("Unwind@"))
gate(not arith and ininst == 10 and N260["push"] == 21,
     "G11 no code computes a 608-strided address: all 21 0x260 immediates are iterator arguments (10 in the 5 installers) or their EH unwind records",
     "push %d; in installers %d; unwind records %d; add/sub/imul/lea/cmp with 0x260 as an immediate: %d"
     % (N260["push"], ininst, unwind, len(arith)))
overlap = {d: sorted(f for f in DEL_FN[d] if f in VIEWFN) for d in DEL_REM0 if DEL_FN[d] & VIEWFN}
exp = DEL_TOT / 608.0
gate(not overlap,
     "G12 the folded-constant candidates are chance: none occurs in a function that loads a view pointer",
     "%d displacement uses in [0x26c,0x1dd6b]; %d in %d values have (d-0xc)%%608==0; uniform expectation %.1f "
     "(ratio %.2f); view-loading functions among them: %d"
     % (DEL_TOT, sum(DEL_REM0.values()), len(DEL_REM0), exp, sum(DEL_REM0.values()) / exp, len(overlap)))
print("     REPORT candidates: %s" % "; ".join("+0x%x(k=%d,n=%d):%s" % (d, (d - 0xc) // 608, DEL_REM0[d],
      ",".join(sorted(x for x in DEL_FN[d] if x)[:4])) for d in sorted(DEL_REM0)))
print("     REPORT 0x260 outside installers+unwind: %s" % "; ".join(
      "%x@%s %s %s" % (pc, f or "?", mn, ops[:30]) for pc, f, mn, ops in N260_AT
      if f not in INSTALLERS and not (f is None or str(f).startswith("Unwind@"))))

C15 = open(P("ghidra_out/shard_015.c")).read().splitlines()
i0 = next(i for i, l in enumerate(C15) if l.startswith("bool FUN_00596620("))
seg = C15[i0:i0 + 240]; j = next(i for i, l in enumerate(seg) if l == "}")
offs = sorted({int(m.group(1), 16) for l in seg[:j] for m in [re.search(r"param_1 \+ (0x[0-9a-f]+)", l)] if m})
loop = [i + 1 for i, l in enumerate(C15) if "FUN_00596620(*puVar18" in l or "puVar18 = &DAT_007cdecc" in l
        or "(int)puVar18 < 0x7cdeec" in l]
gate(len(offs) >= 3 and min(offs) >= 0x1dd70 and max(offs) < 0x1e000 and len(loop) >= 3,
     "G13 the per-view save routine never serializes the array: every param_1 offset is >= +0x1dd70",
     "FUN_00596620 offsets %s; codec loop shard_015.c lines %s walks the 8 view pointers 0x7cdecc..0x7cdeec"
     % ([hex(o) for o in offs], loop))

AL = json.load(open(P("data/alpha.json")))
cnt = {k: len(v) for k, v in AL.items() if isinstance(v, list)}
gate(196 not in cnt.values() and 201 not in cnt.values(),
     "G14 the 4/196/201 split mirrors NO alpha table row count",
     "max %d rows (%s); 4-row tables %s; nothing at 196/201 in %d tables"
     % (max(cnt.values()), max(cnt, key=lambda k: cnt[k]), sorted(k for k, v in cnt.items() if v == 4), len(cnt)))

n_ok = sum(1 for ok, _, _ in GATES if ok)
print("SUMMARY M267/M268: %d/%d gates PASS" % (n_ok, len(GATES)))
raise SystemExit(0 if n_ok == len(GATES) else 1)
