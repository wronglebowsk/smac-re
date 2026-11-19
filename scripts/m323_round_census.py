#!/usr/bin/env python3
# M323: NAME ds:0x985afc — the run-state global that gates M320's 512-word init (==0),
# the M305 rebuild cadence (&3), M317's strategy term (>75) and M177's per-faction stamps.
# STATIC census: every image-wide reference (read/write/test/address-taken), widths,
# writers + what they compute + their callers, direct and register-copy gates, and
# cross-checks against committed prior evidence (m302 live pins, M177 stamps, M320 G6).
# Law: table FIRST, then ASSERT; >=1 RIVAL that FAILS on the printed numbers; digest
# hashes the MEASURED detail. Prior evidence: evidence/m302_livepins.txt:3,8 (year 2150
# @0x985b00, round 50 @0x985afc), evidence/m175_m177_full.txt:42 (stamp primes),
# evidence/m320_sibling_census.txt:411 (word-init gate), evidence/m305_identity.txt:125.
# Mutation: M323_PATCH rewrites disassembly; M323_ALGO 1=direct-test-only gate tracer,
# 2=W/R classifier swap; M323_EVIDENCE_ROOT redirects prior-evidence reads (data mutants).
# Resolver limit (DECLARED): reg_defs_back is a LINEAR static walk (<=40 defs, owning
# function only), not a CFG dataflow proof; where a pinned value depends on it (bl at
# the cadence gate), G5 ALSO pins the complete register-def set + push/pop pair of the
# function, so any def mutation reddens; M305's live bl==1 corroborates the path.
import bisect, csv, hashlib, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")
EV = os.environ.get("M323_EVIDENCE_ROOT", ROOT)
ALGO = os.environ.get("M323_ALGO", "0")
TGT = 0x985afc
ABS = re.compile(r"ds:0x985afc(?![0-9a-f])")
WIDTH = re.compile(r"(BYTE|WORD|DWORD)\s+PTR\s+ds:0x985afc(?![0-9a-f])")
RMW = {"inc", "dec", "add", "sub", "and", "or", "xor", "not", "neg", "adc", "sbb"}
TESTS = {"cmp", "test", "bt"}

def load_ins():
    ins = {}
    lin = re.compile(r"^\s*([0-9a-f]{6,8}):\s[0-9a-f ]+\t(\w+)\s*(.*)$")
    for ln in open(TEXT):
        m = lin.match(ln)
        if m:
            ins[int(m.group(1), 16)] = (m.group(2), m.group(3).strip())
    p = os.environ.get("M323_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in ins:
                raise SystemExit("M323_PATCH address not in .text cache: %s" % addr)
            if ins[a] == (mn, ops.strip()):
                raise SystemExit("M323_PATCH applied to nothing (already equal)")
            ins[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M323_PATCH applied to nothing")
    return ins

INS = load_ins()
ADDRS = sorted(INS)
funcs = []
with open(IDX) as f:
    for r in csv.DictReader(f):
        funcs.append((int(r["addr"], 16), r["name"], int(r["size_bytes"] or 0)))
funcs.sort()
FSTARTS = [a for a, _, _ in funcs]
FNAME = {a: n for a, n, _ in funcs}

def owner(a):
    i = bisect.bisect_right(FSTARTS, a) - 1
    if i >= 0 and a < funcs[i][0] + max(funcs[i][2], 1):
        return funcs[i][1]
    return "?"

def fstart(name):
    for a, n, _ in funcs:
        if n == name: return a
    return None

REG16 = {"ax", "cx", "dx", "bx", "sp", "bp", "si", "di"}
REG8 = {"al", "cl", "dl", "bl", "ah", "ch", "dh", "bh"}

def classify(mn, ops):
    w = WIDTH.search(ops)
    if w:
        width = w.group(1).lower()
    else:
        # unqualified forms: operand-size comes from the register (66-prefix mov ax,ds:...)
        parts = [p.strip() for p in ops.split(",")]
        if any(p in REG16 for p in parts): width = "word"
        elif any(p in REG8 for p in parts): width = "byte"
        else: width = "dword"
    first = ops.split(",")[0]
    mem_first = bool(ABS.search(first))
    if mn == "lea": kind = "A"
    elif mn in TESTS: kind = "T"
    elif mn in ("imul", "mul") and "," not in ops: kind = "R"  # one-operand: edx:eax = eax*mem
    elif mem_first and mn in RMW: kind = "RW"
    elif mem_first and mn == "mov": kind = "W"
    elif mem_first: kind = "W?"
    else: kind = "R"
    if ALGO == "2":  # classifier swap mutant
        kind = {"W": "R", "R": "W", "RW": "R"}.get(kind, kind)
    return kind, width

hits = []
for a in ADDRS:
    mn, ops = INS[a]
    if not ABS.search(ops): continue
    kind, width = classify(mn, ops)
    hits.append((a, kind, width, mn, ops, owner(a)))

BY = {k: [h for h in hits if h[1] == k] for k in ("W", "RW", "T", "R", "A", "W?")}
WIDTHS = {}
for h in hits: WIDTHS[h[2]] = WIDTHS.get(h[2], 0) + 1
KINDS = {k: len(v) for k, v in BY.items()}

# ---- writers: value expression via backward register-def chain -----------------
NONDEF = {"cmp", "test", "push", "bt"}
LOWB = {"eax": "al", "ecx": "cl", "edx": "dl", "ebx": "bl", "esi": "sil", "edi": "dil"}
LOWB_INV = {v: k for k, v in LOWB.items()}
CALLDEF = {"eax", "ecx", "edx", "al", "cl", "dl"}  # cdecl caller-saved

def reg_defs_back(a, reg, limit=40):
    """Yield (addr, mn, ops) of instructions DEFINING reg, walking back within owner."""
    o = owner(a)
    i = ADDRS.index(a)
    seen = 0
    while i > 0 and seen < limit:
        i -= 1
        b = ADDRS[i]
        if owner(b) != o: break
        mn, ops = INS[b]
        if mn in NONDEF or mn.startswith("j"): continue
        if mn == "call" and reg in CALLDEF:
            yield b, mn, ops  # call defines the caller-saved regs
            seen += 1
            continue
        first = ops.split(",")[0].strip()
        if first == reg or first == LOWB.get(reg) or first == LOWB_INV.get(reg):
            yield b, mn, ops
            seen += 1

def local_consts(a, memop):
    """Set of constant stores to a stack local within the owning function."""
    o = owner(a)
    i = ADDRS.index(a)
    vals = []
    while i > 0:
        i -= 1
        b = ADDRS[i]
        if owner(b) != o: break
        mn, ops = INS[b]
        if mn == "mov":
            p = [x.strip() for x in ops.split(",")]
            if p[0] == memop and len(p) > 1 and re.fullmatch(r"0x[0-9a-f]+|\d+", p[1]):
                vals.append((b, p[1]))
    if not vals: return "src(%s)" % memop
    return "local(%s){%s}" % (memop[len("DWORD PTR ["):-1], ",".join(v for _, v in sorted(vals)))

def find_push(a, reg):
    """Matching push for a pop, walking back within the owner (nesting-aware)."""
    o = owner(a)
    i = ADDRS.index(a)
    depth = 0
    while i > 0:
        i -= 1
        b = ADDRS[i]
        if owner(b) != o: break
        mn, ops = INS[b]
        p = ops.split(",")[0].strip()
        if mn == "pop" and p == reg: depth += 1
        elif mn == "push" and p == reg:
            if depth == 0: return b
            depth -= 1
    return None

def resolve_reg(a, reg, depth=0):
    """Value of reg at instruction a (exclusive), as an expression string."""
    if depth > 3: return "depth(%s)" % reg
    base, pieces = None, []  # pieces collected back-to-front; reversed at the end
    for b, mn2, ops2 in reg_defs_back(a, reg):
        p2 = [x.strip() for x in ops2.split(",")]
        if mn2 in ("inc", "dec") and p2[0] in (reg, LOWB.get(reg)):
            pieces.append("+1" if mn2 == "inc" else "-1"); continue
        if mn2 in ("add", "sub") and p2[0] == reg and len(p2) > 1:
            if re.fullmatch(r"0x[0-9a-f]+|\d+", p2[1]):
                pieces.append("%s%s" % ("+" if mn2 == "add" else "-", p2[1])); continue
            if re.fullmatch(r"[a-z]{2,3}", p2[1]):
                pieces.append("%s%s" % ("+" if mn2 == "add" else "-", resolve_reg(b, p2[1], depth + 1)))
                continue
        if mn2 == "mov":
            s2 = p2[1] if len(p2) > 1 else ""
            s2 = re.sub(r"^(BYTE|WORD|DWORD) PTR ", "", s2)
            if ABS.search(s2): base = "round"
            elif re.fullmatch(r"ds:0x[0-9a-f]+", s2): base = "g(%s)" % s2[3:]
            elif re.fullmatch(r"0x[0-9a-f]+|\d+", s2): base = "const(%s)" % s2
            elif re.fullmatch(r"[a-z]{2,3}", s2): base = resolve_reg(b, s2, depth + 1)
            elif re.fullmatch(r"\[ebp-0x[0-9a-f]+\]", s2): base = local_consts(b, "DWORD PTR " + s2)
            else: base = "src(%s)" % s2
        elif mn2 == "pop" and p2[0] in (reg, LOWB_INV.get(reg)):
            pa = find_push(b, LOWB_INV.get(reg, reg))
            base = resolve_reg(pa, reg, depth + 1) if pa else "pop(%s)" % reg
        elif mn2 == "xor" and len(p2) > 1 and p2[0] == p2[1]:
            base = "const(0)"
        elif mn2 == "call":
            base = "ret(%s)" % ops2
        elif mn2 in ("movzx", "movsx"):
            base = resolve_reg(b, p2[1], depth + 1) if len(p2) > 1 and re.fullmatch(r"[a-z]{2,3}", p2[1]) else "src(%s)" % ops2
        else:
            base = "%s(%s)" % (mn2, ops2)
        break
    if base is None: base = "undef"
    return base + "".join(reversed(pieces))

def value_expr(a, mn, ops):
    parts = ops.split(",")
    if len(parts) < 2:
        return "unary(%s)" % mn  # e.g. one-operand imul (a READ, not a store)
    if mn in RMW:  # inc/dec/add... ds:0x985afc[, imm]
        d = {"inc": 1, "dec": -1}.get(mn)
        if d is not None: return "round%+d" % d
        if len(parts) > 1 and re.fullmatch(r"0x[0-9a-f]+|\d+", parts[1].strip()):
            v = int(parts[1].strip(), 0)
            return "round%s%d" % ("+" if mn == "add" else "-", v) if mn in ("add", "sub") else "round?%s" % mn
        return "round?%s" % mn
    src = ops.split(",")[1].strip()
    if re.fullmatch(r"0x[0-9a-f]+|\d+", src):
        return "const(%s)" % src
    if not re.fullmatch(r"[a-z]{2,3}", src):
        return "src(%s)" % src
    return resolve_reg(a, src)

WRITERS = {}
for h in BY["W"] + BY["RW"]:
    a, kind, width, mn, ops, o = h
    WRITERS.setdefault(o, []).append((a, kind, value_expr(a, mn, ops), ops))

def callers_of(name):
    fs = fstart(name)
    if fs is None: return []
    lit = "0x%x" % fs
    return [(a, owner(a)) for a in ADDRS if INS[a][0] == "call" and INS[a][1].strip() == lit]

# ---- direct tests ---------------------------------------------------------------
DIRECT = []
for a, kind, width, mn, ops, o in BY["T"]:
    m = re.search(r",\s*(0x[0-9a-f]+|\d+)\s*$", ops)
    imm = int(m.group(1), 0) if m else None
    DIRECT.append((a, mn, imm, width, o, ops))

# ---- register-copy gates: READ -> (and mask) -> cmp/test -> jcc ------------------
def fwd(a, n=8):
    i = ADDRS.index(a)
    return [(ADDRS[j],) + INS[ADDRS[j]] for j in range(i + 1, min(i + 1 + n, len(ADDRS)))]

def back(a, n=12):
    i = ADDRS.index(a)
    return [(ADDRS[j],) + INS[ADDRS[j]] for j in range(max(0, i - n), i)][::-1]

REGGATES = []
for a, kind, width, mn, ops, o in BY["R"]:
    if mn not in ("mov", "movzx"): continue
    dst = ops.split(",")[0].strip()
    if not re.fullmatch(r"[a-z]{2,3}", dst): continue
    mask, cmpimm, cmpops, cmpaddr, jcc, call = None, None, None, None, None, None
    for b, mn2, ops2 in fwd(a):
        p2 = [x.strip() for x in ops2.split(",")]
        if mn2 == "and" and cmpops is None and p2[0] in (dst, dst[1:]) and len(p2) > 1:
            mask = p2[1]
        elif mn2 in ("cmp", "test") and cmpops is None and p2[0] in (dst, LOWB.get(dst), dst[1:]):
            cmpops, cmpaddr = ops2, b
            if len(p2) > 1 and re.fullmatch(r"0x[0-9a-f]+|\d+", p2[1]):
                cmpimm = int(p2[1], 0)
            elif len(p2) > 1 and p2[1] == p2[0]:
                cmpimm = "self"  # cmp reg,reg == zero test on the round value
        elif mn2.startswith("j"):
            jcc = (b, mn2, ops2); break
        elif mn2 == "call":
            call = (b, ops2); break
        elif mn2 == "mov" and p2[0] == dst:
            break  # dst redefined before any test
    cmpval = None
    if cmpops is not None and cmpimm is None:
        r2 = cmpops.split(",")[1].strip()
        if re.fullmatch(r"[a-z]{2,3}", r2):
            cmpval = resolve_reg(cmpaddr, r2)
    if cmpops is not None or mask is not None:
        REGGATES.append((a, dst, mask, cmpops, cmpimm, cmpval, jcc, call, o))
if ALGO == "1":
    REGGATES = []  # direct-test-only tracer mutant: register-copy gates vanish

# ---- address-taken sites: where does the pointer go? -----------------------------
ADDRUSE = []
for a, kind, width, mn, ops, o in BY["A"]:
    dst = ops.split(",")[0].strip()
    callee = None
    for b, mn2, ops2 in fwd(a, 12):
        if mn2 == "call": callee = (b, ops2); break
        if mn2 == "mov" and ops2.split(",")[0].strip() == dst: break
    ADDRUSE.append((a, dst, callee, o))

# ---- prior evidence cross-checks --------------------------------------------------
def evread(rel):
    return open(os.path.join(EV, rel), encoding="utf-8", errors="replace").read()

m302 = evread("evidence/m302_livepins.txt")
pm = re.search(r"year 0x([0-9a-f]+) round 0x([0-9a-f]+)", m302)
vm = re.search(r"year (\d+) \(0x[0-9a-f]+\)  round (\d+)", m302)
LIVE = {"year_addr": int(pm.group(1), 16), "round_addr": int(pm.group(2), 16),
        "year": int(vm.group(1)), "round": int(vm.group(2))} if pm and vm else None

m177 = evread("evidence/m175_m177_full.txt")
PRIMES = [0x533eec, 0x53420e, 0x534522]
prime_ok = {}
for pa in PRIMES:
    mn0, ops0 = INS.get(pa, ("", ""))
    p0 = [x.strip() for x in ops0.split(",")]
    src = p0[-1] if p0 else ""
    isstore = bool(mn0 == "mov" and "0x94d4a8" in p0[0] and re.fullmatch(r"[a-z]{2,3}", src))
    read = None
    if isstore:
        for b, mn2, ops2 in back(pa, 15):
            if mn2 == "mov" and ops2 in (src + ",ds:0x985afc", src + ",DWORD PTR ds:0x985afc"):
                read = b; break
    prime_ok[pa] = (isstore, read)
m177_src_ok = all(("0x%x" % p) in m177 for p in PRIMES) and "0x94d4a8" in m177
AGE = (0x569401, INS.get(0x569401))
_age_mn, _age_ops = INS.get(0x569401, ("", ""))
age_cmp = None
for b, mn2, ops2 in fwd(0x569401, 4):
    if (mn2, ops2) == ("cmp", "edx,0x10"): age_cmp = b; break
age_ok = (_age_mn == "sub" and _age_ops == "edx,DWORD PTR [eax*4+0x94d4a8]"
          and age_cmp is not None)
m320ev = evread("evidence/m320_sibling_census.txt")
m305ev = evread("evidence/m305_identity.txt")
prior5_ok = ("0x985afc" in m320ev and "59f19c" in m320ev
             and "0x51f71e" in m305ev and "985afc & 3" in m305ev)

# ---- tables FIRST -----------------------------------------------------------------
print("== M323 census of ds:0x985afc (STATIC, scratch/m574/text.txt + ghidra_out/index.csv) ==")
print("T1 all references: %d  kinds=%s widths=%s" % (len(hits), KINDS, WIDTHS))
for a, kind, width, mn, ops, o in hits:
    print("  0x%06x %-2s %-5s %-6s %-42s %s" % (a, kind, width, mn, ops, o))
print("T2 writers (function: sites with value expr):")
for o in sorted(WRITERS):
    for a, kind, expr, ops in sorted(WRITERS[o]):
        print("  %s 0x%06x %-2s %-24s %s" % (o, a, kind, expr, ops))
    cs = callers_of(o)
    print("    callers(%d): %s" % (len(cs), ["0x%06x@%s" % (a, co) for a, co in cs]))
print("T3 direct tests:")
for a, mn, imm, width, o, ops in DIRECT:
    print("  0x%06x %-4s imm=%-5s %-5s %s" % (a, mn, imm, width, o))
print("T4 register-copy gates (read site, dst, mask, cmp, imm, cmpval, jcc, call):")
for a, dst, mask, cmpops, cmpimm, cmpval, jcc, call, o in REGGATES:
    print("  0x%06x %-3s mask=%-4s cmp=%-18s imm=%-5s val=%-12s jcc=%s call=%s %s" % (
        a, dst, mask, cmpops, cmpimm, cmpval,
        "0x%06x:%s" % (jcc[0], jcc[1]) if jcc else None,
        "0x%06x:%s" % (call[0], call[1]) if call else None, o))
print("T5 address-taken:")
for a, dst, callee, o in ADDRUSE:
    print("  0x%06x %-3s callee=%s %s" % (a, dst, "0x%06x:%s" % callee if callee else None, o))
print("T6 prior pins: LIVE=%s primes=%s age@0x569401=%s" % (LIVE, prime_ok, AGE[1]))

# ---- lifecycle computations (year derivation, new-game cluster, rand-start) --------
YEAR = 0x985b00
YABS = re.compile(r"ds:0x985b00(?![0-9a-f])")
year_writers = []
for a in ADDRS:
    mn, ops = INS[a]
    first = ops.split(",")[0]
    if YABS.search(first):  # ANY memory-first form (mov/RMW/xchg/...), not a filtered subset
        year_writers.append((a, mn, owner(a)))
year_expr = value_expr(0x51f54f, *INS[0x51f54f]) if 0x51f54f in INS else None
SYW = [(a, owner(a)) for a in ADDRS
       if INS[a] == ("mov", "DWORD PTR ds:0x92bf68,0x834")]
RANDS = [(a, INS[a][1].split(",")[1]) for a in ADDRS
         if owner(a) == "FUN_0059ce10" and INS[a][0] == "mov"
         and INS[a][1].startswith("DWORD PTR [ebp-0x48],")]
UNK = sorted(h[0] for h in hits if h[5] == "?")
GAPS = {}
for u in UNK:
    i = bisect.bisect_right(FSTARTS, u) - 1
    GAPS[u] = (funcs[i][0] + funcs[i][2], FSTARTS[i + 1] if i + 1 < len(FSTARTS) else None)
# bl reaching-def census: EVERY ebx/bl def in FUN_0051f320 before the cadence gate,
# plus the push/pop pair and any jump INTO the cadence call site (review #323 P1-3/P2-6)
EBXDEFS = [(a, INS[a][0], INS[a][1]) for a in ADDRS
           if 0x51f320 <= a < 0x51f71a and owner(a) == "FUN_0051f320"
           and INS[a][0] not in NONDEF and not INS[a][0].startswith("j")
           and INS[a][1].split(",")[0].strip() in ("ebx", "bl")]
JTGT = [a for a in ADDRS if INS[a][0].startswith("j") and INS[a][1].strip() == "0x51f71e"]

# ---- gates ------------------------------------------------------------------------
BAD = []
def ck(name, ok, detail):
    print("%-4s %-4s %s" % ("OK" if ok else "BADGATE", name, detail))
    if not ok: BAD.append(name)

def unpinned(name, detail):
    print("%-4s %-4s %s" % ("BADGATE", name, "UNPINNED " + detail))
    BAD.append(name)

# G1 census shape
P_TOTAL = 336
P_KINDS = {"W": 5, "RW": 0, "T": 59, "R": 272, "A": 0, "W?": 0}
P_WIDTHS = {"dword": 333, "byte": 2, "word": 1}  # word = 66-prefix mov ax @59c18a (review #323 P2-4)
ck("G1", len(hits) == P_TOTAL and KINDS == P_KINDS and WIDTHS == P_WIDTHS,
   "total=%d kinds=%s widths=%s" % (len(hits), KINDS, WIDTHS))

# G2 writer set + value exprs (4 functions, 5 sites: init0 / year-sync / rand-start / +1)
P_WRITERS = {
    "FUN_004e0350": [(0x4e0387, "W", "g(0x999fa4)-g(0x92bf68)"), (0x4e038e, "W", "const(0x1)")],
    "FUN_0051f320": [(0x51f53c, "W", "round+1")],
    "FUN_0059ce10": [(0x59e2b1, "W", "local(ebp-0x48){0x50,0x3c,0x1e}")],
    "FUN_005a0fa0": [(0x5a108b, "W", "const(0)")],
}
got = {o: [(a, k, e) for a, k, e, _ in sorted(v)] for o, v in WRITERS.items()}
# max(1, diff) flow: cmp eax,1 -> diff store -> jge over the const-1 fallback store
ok2flow = (INS.get(0x4e0384) == ("cmp", "eax,0x1") and INS.get(0x4e038c) == ("jge", "0x4e0398"))
ck("G2", got == P_WRITERS and ok2flow, "writers=%s maxflow=%s" % (got, ok2flow))

# G3 writer callers (direct call sites image-wide)
P_CALLERS = {
    "FUN_004e0350": [0x514ecf, 0x517e3a],
    "FUN_0051f320": [0x520ca3, 0x522371],
    "FUN_0059ce10": [0x5a1579],
    "FUN_005a0fa0": [0x522963, 0x57d2ae, 0x57f20f, 0x57fae4, 0x57fd52],
}
got = {o: sorted(a for a, _ in callers_of(o)) for o in WRITERS}
ck("G3", got == P_CALLERS, "callers=%s" % got)

# G4 direct tests: full map pinned (59 sites; thresholds 0..250 + 5 register-cmps)
prior_direct = {0x45dd2c: 0, 0x45dd66: 0x32, 0x45dd76: 0x64, 0x5552d9: 1}
dmap = {a: imm for a, mn, imm, w, o, ops in DIRECT}
P_DIRECT = {
    0x45c7b5: None, 0x45dd2c: 0, 0x45dd66: 50, 0x45dd76: 100, 0x45ddb8: 50,
    0x45de37: 20, 0x48ba64: 11, 0x48bab8: None, 0x4bdbfc: 0, 0x4bf34f: 0,
    0x4bf3a4: 0, 0x4c0a1f: 0, 0x4c58b2: 1, 0x4e833b: 100, 0x4edd83: 200,
    0x4edeac: 200, 0x4edfd4: None, 0x4f5c13: 5, 0x4f5cc6: 1, 0x4f9043: 100,
    0x4f9440: 100, 0x4fc1d7: 100, 0x503c5d: 50, 0x503cc5: 15, 0x50d208: 25,
    0x50d2d4: 40, 0x50de98: 20, 0x51a946: 75, 0x51b148: 75, 0x51b5cf: 75,
    0x51da30: 75, 0x51e7a1: None, 0x5223c3: None, 0x523315: 200, 0x531ecd: 200,
    0x53acc6: 50, 0x53cf29: 50, 0x5496d0: 25, 0x54babf: 200, 0x551fbc: 100,
    0x5552d9: 1, 0x555ce4: 200, 0x555e52: 100, 0x555f20: 200, 0x55840d: 75,
    0x55b3ed: 50, 0x55c35f: 50, 0x5650d3: 100, 0x56843f: 100, 0x568d22: 50,
    0x56dd51: 100, 0x56e156: 40, 0x56e29c: 50, 0x56f441: 50, 0x56fece: 15,
    0x5a069d: 60, 0x5a06bc: 80, 0x5a06db: 100, 0x5a9c68: 250,
}
ok4 = all(dmap.get(a) == i for a, i in prior_direct.items())
ck("G4", dmap == P_DIRECT and ok4, "direct n=%d prior4=%s" % (len(dmap), ok4))

# G5 register-copy gates: M305 cadence (&3), M320 word-init (==0), M317 (>75 -> setg)
g51 = [g for g in REGGATES if g[0] == 0x51f711]
g59 = [g for g in REGGATES if g[0] == 0x59f1a0]
ok51 = (bool(g51) and g51[0][2] == "0x3" and g51[0][3] == "cl,bl"
        and g51[0][6] == (0x51f71c, "jne", "0x51f723")
        and INS.get(0x51f71e) == ("call", "0x51dcb0")
        and EBXDEFS == [(0x51f32b, "mov", "ebx,0x1"), (0x51f5a2, "pop", "ebx")]
        and INS.get(0x51f525) == ("push", "ebx") and JTGT == [])
ok59 = (bool(g59) and g59[0][3] == "ecx,edx" and g59[0][5] == "const(0)"
        and g59[0][6] == (0x59f1b8, "jne", "0x59f1d4"))
ok55 = (dmap.get(0x55840d) == 75 and INS.get(0x558414) == ("setg", "cl"))
P_BL = "const(0x1)"  # bl via mov ebx,0x1 @51f32b (entry); pop ebx @51f5a2 is the alt
                     # path - M305 live-measured bl==1 on the reaching path
P_NREG = 111
if P_BL is None or P_NREG is None:
    unpinned("G5", "ok51=%s ok59=%s ok55=%s prior5=%s bl=%s nreg=%d" % (
        ok51, ok59, ok55, prior5_ok, g51[0][5] if g51 else None, len(REGGATES)))
else:
    ck("G5", ok51 and ok59 and ok55 and prior5_ok and g51[0][5] == P_BL
       and len(REGGATES) == P_NREG,
       "ok51=%s ok59=%s ok55=%s prior5=%s bl=%s nreg=%d" % (
           ok51, ok59, ok55, prior5_ok, g51[0][5] if g51 else None, len(REGGATES)))

# G6 no address-taken, no unclassified stores; the two '?' owners are index gaps
# (0x4f3a91 = M306's absorbed FUN_004f4060 body; 0x51da30 = 11 B past FUN_0051d3f0)
ck("G6", ADDRUSE == [] and KINDS["W?"] == 0 and KINDS["A"] == 0
   and UNK == [0x4f3a91, 0x51da30]
   and GAPS == {0x4f3a91: (0x4f35da, 0x4f4060), 0x51da30: (0x51da25, 0x51db40)},
   "addr=%d W?=%d unk=%s gaps=%s" % (len(ADDRUSE), KINDS["W?"], [hex(a) for a in UNK], GAPS))

# G7 live pins parsed (m302): round=50 year=2150, distinct addresses
ck("G7", LIVE == {"year_addr": 0x985b00, "round_addr": 0x985afc, "year": 2150, "round": 50},
   "LIVE=%s" % LIVE)

# G8 M177 stamp primes: store into +0x94d4a8 fed by a round READ within 15 insns;
# the age consumer subtracts the stamp and compares < 16 (monotonic-counter semantics)
P_PRIME_READS = {0x533eec: 0x533ecc, 0x53420e: 0x5341ee, 0x534522: 0x534509}
P_AGECMP = 0x569408
ok8 = all(prime_ok[p][0] and prime_ok[p][1] is not None for p in PRIMES)
if P_PRIME_READS is None or P_AGECMP is None:
    unpinned("G8", "primes=%s age_cmp=%s src=%s" % (prime_ok, age_cmp and hex(age_cmp), m177_src_ok))
else:
    ck("G8", ok8 and age_ok and m177_src_ok
       and {p: prime_ok[p][1] for p in PRIMES} == P_PRIME_READS and age_cmp == P_AGECMP,
       "primes=%s age_cmp=%s src=%s" % (prime_ok, age_cmp and hex(age_cmp), m177_src_ok))

# G9 widths/blind spots: 2 byte + 1 word (66-prefix mov ax, unqualified - register-sized);
# byte sites and the word site pinned
byte_sites = sorted(h[0] for h in hits if h[2] == "byte")
word_sites = sorted(h[0] for h in hits if h[2] == "word")
ck("G9", byte_sites == [0x5552d9, 0x555da0] and word_sites == [0x59c18a],
   "byte=%s word=%s" % ([hex(a) for a in byte_sites], [hex(a) for a in word_sites]))

# G10 lifecycle: year = FUN_005b2c00(round+1) = round + start_year(2100); new-game
# cluster zeroes round+unit/base counts; rand-start {30,60,80} gated on 0x985ac4 bit 7
ok10a = (year_writers == [(0x51f54f, "mov", "FUN_0051f320")] and year_expr == "ret(0x5b2c00)"
         and INS.get(0x51f535) == ("mov", "eax,ds:0x985afc")
         and INS.get(0x51f53a) == ("inc", "eax")
         and INS.get(0x51f53b) == ("push", "eax") and INS.get(0x51f541) == ("call", "0x5b2c00"))
ok10b = (INS.get(0x5b2c03) == ("mov", "eax,DWORD PTR [ebp+0x8]")
         and INS.get(0x5b2c06) == ("mov", "ecx,DWORD PTR ds:0x92bf68")
         and INS.get(0x5b2c0c) == ("add", "eax,ecx") and INS.get(0x5b2c0f) == ("ret", ""))
ok10c = SYW == [(0x5a0f88, "FUN_005a0f60"), (0x5a1042, "FUN_005a0fa0")]
ok10d = (INS.get(0x5a1098) == ("mov", "DWORD PTR ds:0x985af4,esi")
         and INS.get(0x5a109e) == ("mov", "DWORD PTR ds:0x985af0,esi"))
ok10e = (INS.get(0x5a1570) == ("test", "BYTE PTR ds:0x985ac4,0x80")
         and INS.get(0x5a1577) == ("je", "0x5a1585") and INS.get(0x5a1579) == ("call", "0x59ce10"))
ok10f = (RANDS == [(0x59ce42, "0x50"), (0x59ce5b, "0x3c"), (0x59ce74, "0x1e")]
         and INS.get(0x59ce19) == ("call", "0x64c6f0") and INS.get(0x59ce1e) == ("mov", "esi,0x3")
         and INS.get(0x59ce2b) == ("idiv", "ecx"))
ck("G10", all((ok10a, ok10b, ok10c, ok10d, ok10e, ok10f)),
   "year=%s callee=%s syw=%s cluster=%s gate=%s rand=%s sites=%s" % (
       ok10a, ok10b, ok10c, ok10d, ok10e, ok10f,
       [(hex(a), v) for a, v in RANDS]))

# R1 YEAR rival: 0x985afc holds the year -> must FAIL on the live pins + derivation
r1 = (LIVE is not None and LIVE["round_addr"] == TGT and LIVE["round"] != LIVE["year"]
      and LIVE["year_addr"] != TGT and ok10a and ok10b)
ck("R1", r1, "YEAR rival dead: round=%s@0x985afc vs year=%s@0x%x, year=round+2100 derived" % (
    LIVE and LIVE["round"], LIVE and LIVE["year"], LIVE and LIVE["year_addr"]))

# R2 MODE-ENUM rival: many writers, no monotonic +1 -> must FAIL on the writer structure
plus1 = [(o, a) for o, v in WRITERS.items() for a, k, e, _ in v if e == "round+1"]
others = [e for o, v in WRITERS.items() for a, k, e, _ in v if e != "round+1"]
r2 = (len(WRITERS) == 4 and plus1 == [("FUN_0051f320", 0x51f53c)] and ok8
      and all(e.startswith(("const(", "g(", "local(")) for e in others))
ck("R2", r2, "MODE-ENUM rival dead: writers=%d plus1=%s others=%s stamps=%s" % (
    len(WRITERS), plus1, others, ok8))

# R3 LOAD-CONSTANT rival: written only at load -> must FAIL (+1 writer, 2 callers,
# and the year store re-derived from it every advance)
P_R3 = ("FUN_0051f320", 2)
o, nmin = P_R3
cs = callers_of(o)
ck("R3", o in WRITERS and any(e == "round+1" for _, _, e, _ in WRITERS[o])
   and len(cs) >= nmin and ok10a and INS.get(0x51f53a) == ("inc", "eax"),
   "LOAD-CONSTANT rival dead: %s +1 writer, %d callers, year re-derived" % (o, len(cs)))

# ---- digest over MEASURED detail ---------------------------------------------------
det = repr((KINDS, WIDTHS,
            tuple((a, k, w, mn, ops, o) for a, k, w, mn, ops, o in hits),
            tuple(sorted((o, tuple(sorted((a, k, e) for a, k, e, _ in v))) for o, v in WRITERS.items())),
            tuple(sorted((o, tuple(sorted(a for a, _ in callers_of(o)))) for o in WRITERS)),
            tuple((a, mn, imm) for a, mn, imm, w, o, ops in DIRECT),
            tuple(REGGATES), tuple(ADDRUSE), LIVE, prime_ok, age_ok, age_cmp,
            tuple(year_writers), year_expr, tuple(SYW), tuple(RANDS), UNK, GAPS,
            tuple(EBXDEFS), tuple(JTGT)))
h = hashlib.sha256(det.encode()).hexdigest()[:16]
print("digest %s" % h)
print("== M323: %d/%d ==" % (13 - len(BAD), 13))
sys.exit(1 if BAD else 0)
