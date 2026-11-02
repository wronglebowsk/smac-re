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
`SUMMARY M269/M270/M271: 12/12 gates PASS`.
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
            for offreg in (b, ix):
                if offreg is None or offreg not in OFF: continue
                F = res(OFF[offreg])
                if F is None: continue
                other = ix if offreg == b else b
                sc_eff = sc if offreg == b else 1
                oe = res(E[other]) if (other is not None and E.get(other) is not None) else (other, 0)
                lhs = res((oe[0], oe[1] * sc_eff + dp))
                if lhs == F: INST[imm].append((pc, fn, "primary", F)); done = True; break
                if lhs == (F[0], F[1] + 0x444): INST[imm].append((pc, fn, "secondary", F)); done = True; break
    elif mn == "lea" and isreg(dst):
        rest = ops.partition(",")[2].strip(); m = MEMRE.match(rest); p = parse_mem(m.group(1)) if m else None
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
for pc, fn, k, F, dp, ops in BAD[:10]:
    print("  BAD %s %s K=0x%x F=%s dp=0x%x  %s" % (fn, hex(pc), k, F, dp, ops))
NI = sum(len(v) for v in INST.values())
print("M269 vptr installs through a vbptr: %d stores of %d distinct rdata values" % (NI, len(INST)))
for imm in sorted(INST, key=lambda x: -len(INST[x]))[:14]:
    c = collections.Counter(t for _p, _f, t, _F in INST[imm])
    print("  0x%08x n=%-3d primary=%-3d secondary=%-3d fns=%s" % (imm, len(INST[imm]), c["primary"],
          c["secondary"], ",".join(sorted({f for _p, f, _t, _F in INST[imm]})[:5])))
GATES = []
def gate(ok, name, detail=""):
    GATES.append((bool(ok), name, detail))
    print("%s %s%s" % ("PASS" if ok else "FAIL", name, ("  " + detail) if detail else ""))
print("GATE-PLACEHOLDER")
print("SUMMARY M269/M270/M271: %d/%d gates PASS" % (sum(1 for g in GATES if g[0]), len(GATES)))
