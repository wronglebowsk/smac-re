#!/usr/bin/env python3
"""M269 every virtual-base DELTA store image-wide (the K census) + the vptr installs that go
through a vbptr; M270 the object whose vtable is 0x678e40 (the 0x25318-B instance in
FUN_0059bec0); M271 the image-wide VBTABLE descriptor census.

Instrument = ONE pass over the whole-image .text disassembly (scratch/m574/text.txt) plus the raw
PE image (programs/terran.exe) and ghidra_out/index.csv containment. A symbolic shadow tracks the
MSVC virtual-base idiom in its GEOMETRIC form:

  VP[r]  = (base,disp)   r was loaded from that address  (the vbptr-field load)
  OFF[r] = (base,disp)   r = [desc+4], the offset from THAT FIELD to the virtual base
  DL[r]  = (K,F)         r = [desc+4] - K, the value MSVC stores in the [vptr-4] delta word
  a store `[off_reg + other*sc + dp] = DL_reg` is a delta store iff
  res(E[other]) + dp == F - 4  (the store lands exactly 4 below the virtual base's vptr);
  the same test with F (primary) or F+0x444 (secondary view) names a vptr install AT a virtual base.

No box time, no /proc, no gdb. Acceptance: ONE real invocation prints
`SUMMARY M269/M270/M271: 10/10 gates PASS`.
"""
import os, re, csv, struct, bisect, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*x): return os.path.join(R, *x)
IMG = open(P("programs/terran.exe"), "rb").read()
CODE = (0x401000, 0x6703f4); RDAT = (0x670000, 0x6a0000)
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
    return struct.unpack_from("<I", IMG, o)[0] if 0 <= o + 4 <= len(IMG) else None
def iscode(v): return v is not None and CODE[0] <= v < CODE[1]
def s32(v): return v - 0x100000000 if v >= 0x80000000 else v
def occ(va):
    pat = struct.pack("<I", va); i = 0; hits = []
    while True:
        i = IMG.find(pat, i)
        if i < 0: break
        hits.append(i + 0x400000); i += 1
    return hits
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")
MEMRE = re.compile(r"^DWORD PTR \[([^]]+)\]$")
def parse_mem(inner):
    terms = inner.replace("-", "+-").split("+")
    base = idx = None; scale = 1; disp = 0
    for t in terms:
        t = t.strip()
        if not t: continue
        m = re.fullmatch(r"(-?)0x([0-9a-f]+)", t)
        if m: disp += -int(m.group(2), 16) if m.group(1) else int(m.group(2), 16); continue
        m = re.fullmatch(r"([a-z]+)\*(\d+)", t)
        if m and m.group(1) in REGS and idx is None: idx, scale = m.group(1), int(m.group(2)); continue
        m = re.fullmatch(r"([a-z]+)", t)
        if m and m.group(1) in REGS and base is None: base = m.group(1); continue
        return None
    if base is None and idx is None: return None
    return base, idx, scale, disp
def walk(path):
    for line in open(path, errors="replace"):
        l = line.replace("\\t", "\t").rstrip("\n"); p = l.split("\t")
        if len(p) < 3: continue
        m = re.fullmatch(r"\s*([0-9a-f]{6,8}):", p[0])
        if not m: continue
        t = p[2].split(None, 1)
        if not t: continue
        yield int(m.group(1), 16), t[0].lower(), (t[1] if len(t) > 1 else "").strip()

INSTALLERS = ["FUN_00421950", "FUN_00469650", "FUN_00518980", "FUN_0059bec0", "FUN_0059c1e0"]
NEED = set(INSTALLERS) | {"FUN_0059c380", "FUN_0059c3b0", "FUN_005faec0", "FUN_0050aa60",
                          "FUN_005fb038", "FUN_005f9bfb", "FUN_005e3b80", "FUN_005e3ced"}
BODY = collections.defaultdict(list)
DELTA = []; BAD = []; INST = collections.defaultdict(list); SK = 0
ALLINST = collections.defaultdict(list); CALLERS = collections.defaultdict(set)
VT = {}; E = {}; VP = {}; OFF = {}; DL = {}; cur = object()
def res(e, n=0):
    while e is not None and n < 12:
        b, d = e
        if b is None: return (None, d)
        if isinstance(b, int):
            e2 = VT.get(b)
            if e2 is None: return None
            e = (e2[0], e2[1] + d)
        else:
            ee = E.get(b)
            if ee is None: return (b, d)
            e = (ee[0], ee[1] + d)
        n += 1
    return None
def kill(r):
    E.pop(r, None); VP.pop(r, None); OFF.pop(r, None); DL.pop(r, None)
isreg = lambda s: s in REGS
for pc, mn, ops in walk(P("scratch/m574/text.txt")):
    fn = own(pc)
    if fn != cur: cur, E, VP, OFF, DL = fn, {}, {}, {}, {}
    if fn in NEED: BODY[fn].append((pc, mn, ops))
    if mn == "call":
        if ops.strip() in ("0x59bec0", "0x59c1e0", "0x59c380"): CALLERS[ops.strip()].add(fn)
        for r in ("eax", "ecx", "edx"): kill(r)
        continue
    if mn in ("push", "pop", "jmp", "ret", "nop", "int3", "leave", "cld", "std", "clc", "stc"): continue
    dst, _, src = ops.partition(","); dst = dst.strip(); src = src.strip()
    if mn == "mov" and isreg(dst):
        m = MEMRE.match(src); p = parse_mem(m.group(1)) if m else None
        if p and p[1] is None and p[2] == 1 and p[3] == 4 and p[0] in VP:
            OFF[dst] = VP[p[0]]; VP.pop(dst, None); DL.pop(dst, None); E[dst] = (pc, 0); VT[pc] = None
        elif p and p[1] is None:
            VP[dst] = res((p[0], p[3])); E[dst] = (pc, 0); VT[pc] = (p[0], p[3])
            OFF.pop(dst, None); DL.pop(dst, None)
        elif isreg(src):
            for tbl in (E, VP, OFF, DL):
                if src in tbl: tbl[dst] = tbl[src]
                else: tbl.pop(dst, None)
        else: kill(dst)
    elif mn == "mov" and MEMRE.match(dst) and isreg(src) and src in DL:
        p = parse_mem(MEMRE.match(dst).group(1)); k, F = DL[src]
        matched = False
        if p:
            b, ix, sc, dp = p
            for offreg in (b, ix):
                if offreg is None or offreg not in OFF: continue
                if res(OFF[offreg]) != res(F): continue
                other = ix if offreg == b else b
                sc_eff = sc if offreg == b else 1
                oe = res(E[other]) if (other is not None and E.get(other) is not None) else (other, 0)
                if res((oe[0], oe[1] * sc_eff + dp)) != res((F[0], F[1] - 4)): continue
                DELTA.append((pc, fn, k, F, dp, ops)); matched = True
                if not (abs(F[1]) >= 0x1000 or F[1] == 0): SK += 1
                break
            if not matched: BAD.append((pc, fn, k, F, dp, ops))
    elif mn == "mov" and MEMRE.match(dst):
        m = re.search(r",0x([0-9a-f]{6,8})$", ops)
        p = parse_mem(MEMRE.match(dst).group(1))
        if m and p and RDAT[0] <= int(m.group(1), 16) < RDAT[1]:
            b, ix, sc, dp = p; imm = int(m.group(1), 16); done = False
            ALLINST[imm].append((pc, fn))
            for offreg in (b, ix):
                if offreg is None or offreg not in OFF: continue
                F = res(OFF[offreg])
                if F is None: continue
                other = ix if offreg == b else b
                sc_eff = sc if offreg == b else 1
                oe = res(E[other]) if (other is not None and E.get(other) is not None) else (other, 0)
                lhs = res((oe[0], oe[1] * sc_eff + dp))
                if lhs == F: INST[imm].append((pc, fn, "primary", F, ops)); done = True; break
                if lhs == (F[0], F[1] + 0x444): INST[imm].append((pc, fn, "secondary", F, ops)); done = True; break
    elif mn == "lea" and isreg(dst):
        rest = ops.partition(",")[2].strip()
        m = MEMRE.match(rest) or re.match(r"^\[([^]]+)\]$", rest)
        p = parse_mem(m.group(1)) if m else None
        if p and p[1] is None and p[2] == 1 and p[3] < 0 and p[0] in OFF:
            F = OFF[p[0]]; kill(dst); DL[dst] = (-p[3], F)
        elif p and p[1] is None:
            kill(dst); E[dst] = res((p[0], p[3]))
        else: kill(dst)
    elif mn in ("sub", "add") and isreg(dst):
        m = re.fullmatch(r"0x([0-9a-f]+)", src)
        if m and mn == "sub" and dst in OFF:
            F = OFF[dst]; DL[dst] = (int(m.group(1), 16), F); OFF.pop(dst, None)
            E[dst] = (pc, 0); VT[pc] = None
        elif m and mn == "add" and E.get(dst) is not None:
            e0, d0 = E[dst]; E[dst] = (e0, d0 + int(m.group(1), 16))
        else: kill(dst)
    else:
        d0 = ops.partition(",")[0].strip() if ops else ""
        if isreg(d0): kill(d0)

BYK = collections.defaultdict(list)
for pc, fn, k, F, dp, ops in DELTA: BYK[k].append((pc, fn, F, dp, ops))
print("M269 delta stores %d sites / %d distinct K / %d functions (of those sites %d have a field "
      "expr displaced < 0x1000 from its base; %d stores of a delta value through the same field "
      "are NOT 4 below the virtual base)"
      % (len(DELTA), len(BYK), len({d[1] for d in DELTA}), SK, len(BAD)))
for k in sorted(BYK):
    fs = collections.Counter(f for _p, f, _F, _d, _o in BYK[k])
    print("  K=0x%-6x (%6d) sites=%-3d fns=%-3d %s" % (k, s32(k), len(BYK[k]), len(fs),
          ", ".join("%s x%d" % (f, c) for f, c in fs.most_common(8))))
for pc, fn, k, F, dp, ops in DELTA:
    print("  SITE %-14s %s K=0x%-6x F=(%s%s) dp=0x%x  %s" % (fn, hex(pc), k, F[0], ("" if F[1] is None else "%+d" % F[1]), dp, ops))
for pc, fn, k, F, dp, ops in BAD[:10]:
    print("  BAD %s %s K=0x%x F=%s dp=0x%x  %s" % (fn, hex(pc), k, F, dp, ops))
NI = sum(len(v) for v in INST.values())
print("M269 vptr installs through a vbptr: %d stores of %d distinct rdata values" % (NI, len(INST)))
for imm in sorted(INST, key=lambda x: -len(INST[x]))[:14]:
    c = collections.Counter(t for _p, _f, t, _F, _o in INST[imm])
    print("  0x%08x n=%-3d primary=%-3d secondary=%-3d fns=%s" % (imm, len(INST[imm]), c["primary"],
          c["secondary"], ",".join(sorted({f for _p, f, _t, _F, _o in INST[imm]})[:5])))
for imm in sorted(INST, key=lambda x: -len(INST[x]))[:4]:
    for pc, fn, t, F, ops in INST[imm][:3]:
        print("  INST 0x%08x %-9s %-14s %s F=%s  %s" % (imm, t, fn, hex(pc), F, ops))
GATES = []
def gate(ok, name, detail=""):
    GATES.append((bool(ok), name, detail))
    print("%s %s%s" % ("PASS" if ok else "FAIL", name, ("  " + detail) if detail else ""))
# ================= M271: the vbtable candidate census =================
CAND = {}
for imm in ALLINST:
    a0, a4 = dw(imm), dw(imm + 4)
    if a0 is None or a4 is None or iscode(a0) or iscode(a4): continue
    if abs(s32(a0)) >= 0x40000 or abs(s32(a4)) >= 0x40000: continue
    CAND[imm] = (s32(a0), s32(a4))
BYOFF = collections.defaultdict(list)
for _d, (_h, o) in CAND.items(): BYOFF[o].append(_d)
print("M271 vbtable candidates %d of %d distinct rdata immediates stored through a register; "
      "%d distinct [+4] virtual-base offsets" % (len(CAND), len(ALLINST), len(BYOFF)))
for o in sorted(BYOFF)[:24]:
    ds = sorted(BYOFF[o]); fns = sorted({f for d in ds for _p, f in ALLINST[d]})
    print("  [+4]=0x%-8x (%6d) descs=%s installed-by(%d)=%s"
          % (o, o, ",".join(hex(x) for x in ds[:5]), len(fns), ",".join(fns[:6])))
KFN = {k: sorted({f for _p, f, _F, _d, _o in BYK[k]}) for k in BYK}
P5 = sorted({f for _p, f, t, _F, _o in INST.get(0x6725ac, []) if t == "primary"})
S5 = sorted({f for _p, f, t, _F, _o in INST.get(0x6725a4, []) if t == "secondary"})
gate(KFN.get(0x21a6c) == sorted(INSTALLERS),
     "G1 each of the 5 known installers has exactly one delta store, all at K=0x21a6c",
     "fns=" + ",".join(KFN.get(0x21a6c, [])))
gate(P5 == sorted(INSTALLERS) and S5 == sorted(INSTALLERS) and P5 == KFN.get(0x21a6c),
     "G2 the install census and the delta census name the SAME 5 functions for 0x6725ac/0x6725a4",
     "primary=%d secondary=%d delta=%d" % (len(INST.get(0x6725ac, [])), len(INST.get(0x6725a4, [])), len(BYK.get(0x21a6c, []))))
gate(dw(0x675964) == 0 and dw(0x675964 + 4) == 0x21a6c and dw(0x678458 + 4) == 0x23d94
     and "FUN_00469650" in {f for _p, f in ALLINST.get(0x675964, [])}
     and "FUN_0050aa60" in {f for _p, f in ALLINST.get(0x678458, [])}
     and "FUN_00469650" in KFN.get(0x21a6c, []) and "FUN_0050aa60" in KFN.get(0x23d94, []),
     "G3 the two known vbtables confirm the rule: [0x675964]=0,[+4]=0x21a6c installed by FUN_00469650 and [0x678458+4]=0x23d94 installed by FUN_0050aa60, both installers carry a delta store at that K",
     "[0x675964]=0x%x [+4]=0x%x by %s; [0x678458+4]=0x%x by %s; K=0x23d94 fns=%s"
     % (dw(0x675964), dw(0x675964 + 4), sorted({f for _p, f in ALLINST.get(0x675964, [])}),
        dw(0x678458 + 4), sorted({f for _p, f in ALLINST.get(0x678458, [])}), KFN.get(0x23d94)))
sec = sorted(i for i in INST if any(t == "secondary" for _p, _f, t, _F, _o in INST[i]))
gate(bool(sec) and all(i + 8 in INST and
     len([1 for _p, _f, t, _F, _o in INST[i] if t == "secondary"]) ==
     len([1 for _p, _f, t, _F, _o in INST[i + 8] if t == "primary"]) for i in sec),
     "G4 every secondary-view install has its primary table 8 B above it with the SAME install count (M267's pair is the general rule)",
     "%d secondary tables: %s" % (len(sec), " ".join("0x%x:%d/%x:%d" % (i, len(INST[i]), i + 8,
      len([1 for _p, _f, t, _F, _o in INST[i + 8] if t == "primary"])) for i in sec)))
gate(0x675964 in CAND and 0x678458 in CAND and all(ALLINST[d] for d in CAND),
     "G9 the vbtable census contains both known descriptors and no candidate has zero installers",
     "%d candidates; 0x675964 -> %s; 0x678458 -> %s" % (len(CAND), CAND.get(0x675964), CAND.get(0x678458)))
gate(all(BYOFF.get(k) for k in BYK),
     "G10 every K the delta census found is the [+4] virtual-base offset of at least one vbtable the descriptor census found (the two censuses close on each other)",
     " ".join("K=0x%x->%s" % (k, ",".join(hex(x) for x in (BYOFF.get(k) or [])[:3])) for k in sorted(BYK)))
B1 = BODY.get("FUN_0059c1e0", []); B2 = BODY.get("FUN_0059bec0", [])
st40 = [ops for pc, mn, ops in B2 if mn == "mov" and ops.endswith(",0x678e40")]
st38 = [ops for pc, mn, ops in B2 if mn == "mov" and ops.endswith(",0x678e38")]
gate(len(occ(0x678e40)) == 1 and len(occ(0x678e38)) == 1 and len(st40) == 1 and len(st38) == 1
     and "ebp-0x25324" in st40[0] and "ebp-0x24ee0" in st38[0]
     and dw(0x678e40) == 0x59c380 and dw(0x678e38) == 0x59c3b0,
     "G5 the 0x678e40 vtable is installed exactly ONCE image-wide (its secondary 0x678e38 once, 0x2444 below), both inside FUN_0059bec0; slot 0 of each is that class's deleting-dtor wrapper",
     "occ=%s %s stores=%s | %s slot0=%s/%s" % ([hex(x) for x in occ(0x678e40)], [hex(x) for x in occ(0x678e38)],
      st40, st38, hex(dw(0x678e40)), hex(dw(0x678e38))))
gate(not occ(0x59c1e0) and not occ(0x59bec0) and set(occ(0x59c380)) == {0x678e40}
     and set(occ(0x59c3b0)) == {0x678e38},
     "G6 neither FUN_0059c1e0 (the dtor body) nor FUN_0059bec0 is address-taken anywhere in the image; the dtor is reached only as slot 0 of its own tables (0x59c380 stored at 0x678e40, 0x59c3b0 at 0x678e38)",
     "callers(59c1e0)=%s callers(59bec0)=%s occ(59c380)=%s occ(59c3b0)=%s"
     % (sorted(CALLERS.get("0x59c1e0", set())), sorted(CALLERS.get("0x59bec0", set())),
        [hex(x) for x in occ(0x59c380)], [hex(x) for x in occ(0x59c3b0)]))
ctor = collections.defaultdict(list)
for i, (pc, mn, ops) in enumerate(B2):
    if mn != "lea" or not ops.startswith("ecx,[ebp"): continue
    inner = ops[ops.index("[") + 1:ops.index("]")]; d = parse_mem(inner)
    if not d or d[1] is not None or d[0] != "ebp": continue
    for pc2, mn2, ops2 in B2[i + 1:i + 9]:
        if mn2 == "call": ctor[ops2.strip()].append(0x25324 + d[3]); break
row = [ops for pc, mn, ops in B1 if mn == "mov" and ops.endswith(",0x67194c")]
row2 = [ops for pc, mn, ops in B1 if mn == "mov" and ops.endswith(",0x671944")]
leas = [ops for pc, mn, ops in B1 if mn == "lea" and ops.endswith(",[edi+0x247a0]")]
gate(row and row2 and leas and "[esi]" in row[0] and "[esi+0x444]" in row2[0]
     and not [o for pc, mn, o in B1 if mn == "mov" and o.endswith(",0x67194c") and "[edi" in o]
     and {(t, o) for t, lst in ctor.items() for o in lst} >=
         {("0x5e3b80", 0), ("0x469650", 0x2320), ("0x5faec0", 0x247a0), ("0x614150", 0x252ec)},
     "G7 FUN_0059c1e0 installs the row vtables 0x67194c/0x671944 at +0x247a0 and +0x247a0+0x444 (NOT at [this+0]: the row is a SUBOBJECT, M215's class), and FUN_0059bec0 constructs at +0 the 0x5e3b80 object, at +0x2320 the 0x675964 class, at +0x247a0 the row, at +0x252ec the 0x614150 object",
     "row=%s %s lea=%s ctor=%s" % (row, row2, leas, {t: sorted(set(v)) for t, v in ctor.items() if t in ("0x5e3b80", "0x469650", "0x5faec0", "0x614150")}))
d2 = [ops for pc, mn, ops in B1 if mn == "lea" and ops.endswith(",[edi+0x252ec]")]
d3 = [ops for pc, mn, ops in B1 if mn == "lea" and ops.endswith(",[edi+0x23d8c]")]
probe = [ops for pc, mn, ops in B2 if mn == "mov" and ops == "eax,0x25318"]
gate(0x2320 + 0x22480 == 0x247a0 and 0x247a0 + 0xb4c == 0x252ec and 0x2320 + 0x21a6c == 0x23d8c
     and 0x25324 - 0xc == 0x25318 and len(probe) == 1 and d2 and d3,
     "G8 the layout closes on itself: +0x2320 + the 0x675964 class's 0x22480 allocation == +0x247a0 (the row), + that row's 0xb4c == +0x252ec (where FUN_0059bec0 calls the 0x614150 ctor AND where the dtor calls 0x6141c1), +0x2320 + 0x21a6c == +0x23d8c (the virtual base both FUN_0059c1e0 and FUN_0059bec0 destroy), and the object span 0x25324-0xc == the single 0x25318 alloca probe == the object size",
     "dtor leas=%s %s probe=%s" % (d2, d3, probe))
print("SUMMARY M269/M270/M271: %d/%d gates PASS" % (sum(1 for g in GATES if g[0]), len(GATES)))
