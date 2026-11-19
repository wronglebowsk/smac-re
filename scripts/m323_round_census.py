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

def classify(mn, ops):
    w = WIDTH.search(ops)
    width = w.group(1).lower() if w else "dword"
    first = ops.split(",")[0]
    mem_first = bool(ABS.search(first))
    if mn == "lea": kind = "A"
    elif mem_first and mn in RMW: kind = "RW"
    elif mem_first and mn == "mov": kind = "W"
    elif mem_first: kind = "W?"
    elif mn in TESTS: kind = "T"
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
def reg_defs_back(a, reg, limit=40):
    """Yield (addr, mn, ops) of instructions defining reg, walking back within owner."""
    o = owner(a)
    i = ADDRS.index(a)
    seen = 0
    while i > 0 and seen < limit:
        i -= 1
        b = ADDRS[i]
        if owner(b) != o: break
        mn, ops = INS[b]
        first = ops.split(",")[0].strip()
        if first == reg or first in ("al", "cl", "dl", "bl") and reg in ("eax", "ecx", "edx", "ebx"):
            yield b, mn, ops
            seen += 1

def value_expr(a, mn, ops):
    if mn in RMW:  # inc/dec/add... ds:0x985afc[, imm]
        parts = ops.split(",")
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
    base, delta, note = None, 0, []
    for b, mn2, ops2 in reg_defs_back(a, src):
        p2 = ops2.split(",")
        if mn2 in ("inc", "dec") and p2[0].strip() == src:
            delta += 1 if mn2 == "inc" else -1; continue
        if mn2 in ("add", "sub") and p2[0].strip() == src and len(p2) > 1 and re.fullmatch(r"0x[0-9a-f]+|\d+", p2[1].strip()):
            delta += int(p2[1].strip(), 0) * (1 if mn2 == "add" else -1); continue
        if mn2 == "mov":
            s2 = p2[1].strip() if len(p2) > 1 else ""
            if ABS.search(s2): base = "round"
            elif re.fullmatch(r"0x[0-9a-f]+|\d+", s2): base = "const(%s)" % s2
            else: base = "src(%s)" % s2
        elif mn2 == "xor" and len(p2) > 1 and p2[0].strip() == p2[1].strip():
            base = "const(0)"
        elif mn2 == "call":
            base = "ret(%s)" % ops2
        else:
            base = "%s(%s)" % (mn2, ops2)
        break
    if base is None: base = "undef"
    return base + ("%+d" % delta if delta else "")

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
    mask, cmpimm, cmpops, jcc, call = None, None, None, None, None
    for b, mn2, ops2 in fwd(a):
        p2 = [x.strip() for x in ops2.split(",")]
        if mn2 == "and" and p2[0] in (dst, dst[1:]) and len(p2) > 1:
            mask = p2[1]
        elif mn2 in ("cmp", "test") and p2[0] in (dst, dst[0] + "l", dst[0] + "x"):
            cmpops = ops2
            if len(p2) > 1 and re.fullmatch(r"0x[0-9a-f]+|\d+", p2[1]):
                cmpimm = int(p2[1], 0)
            break
        elif mn2.startswith("j"):
            jcc = (b, mn2, ops2); break
        elif mn2 == "call":
            call = (b, ops2); break
        elif mn2 == "mov" and p2[0] == dst:
            break  # dst redefined before any test
    if cmpops is not None or mask is not None:
        REGGATES.append((a, dst, mask, cmpops, cmpimm, jcc, call, o))
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
    isread = any(h[0] == pa and h[1] == "R" for h in hits)
    store = None
    if isread:
        for b, mn2, ops2 in fwd(pa, 15):
            if mn2 == "mov" and re.search(r"\[.*0x94d4a8\]", ops2.split(",")[0]):
                store = b; break
    prime_ok[pa] = (isread, store)
AGE = (0x569401, INS.get(0x569401), INS.get(0x569404) if 0x569404 in INS else None)
_age_mn, _age_ops = INS.get(0x569401, ("", ""))
age_ok = _age_mn == "sub" and _age_ops.startswith("edx,") and "0x94d4a8" in _age_ops

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
print("T4 register-copy gates (read site, dst, mask, cmp, imm, jcc, call):")
for a, dst, mask, cmpops, cmpimm, jcc, call, o in REGGATES:
    print("  0x%06x %-3s mask=%-4s cmp=%-18s imm=%-5s jcc=%s call=%s %s" % (
        a, dst, mask, cmpops, cmpimm,
        "0x%06x:%s" % (jcc[0], jcc[1]) if jcc else None,
        "0x%06x:%s" % (call[0], call[1]) if call else None, o))
print("T5 address-taken:")
for a, dst, callee, o in ADDRUSE:
    print("  0x%06x %-3s callee=%s %s" % (a, dst, "0x%06x:%s" % callee if callee else None, o))
print("T6 prior pins: LIVE=%s primes=%s age@0x569401=%s" % (LIVE, prime_ok, AGE[1]))

# ---- gates ------------------------------------------------------------------------
BAD = []
def ck(name, ok, detail):
    print("%-4s %-4s %s" % ("OK" if ok else "BADGATE", name, detail))
    if not ok: BAD.append(name)

def unpinned(name, detail):
    print("%-4s %-4s %s" % ("BADGATE", name, "UNPINNED " + detail))
    BAD.append(name)

# G1 census shape (pins measured at first probe; UNPINNED in skeleton)
P_TOTAL = None      # pin: total refs
P_KINDS = None      # pin: kind histogram
P_WIDTHS = None     # pin: width histogram
if P_TOTAL is None:
    unpinned("G1", "total/kinds/widths")
else:
    ck("G1", len(hits) == P_TOTAL and KINDS == P_KINDS and WIDTHS == P_WIDTHS,
       "total=%d kinds=%s widths=%s" % (len(hits), KINDS, WIDTHS))

# G2 writer set + value exprs
P_WRITERS = None    # pin: {owner: [(addr, kind, expr)]}
if P_WRITERS is None:
    unpinned("G2", "writer set")
else:
    got = {o: [(a, k, e) for a, k, e, _ in sorted(v)] for o, v in WRITERS.items()}
    ck("G2", got == P_WRITERS, "writers=%s" % got)

# G3 writer callers
P_CALLERS = None    # pin: {owner: [caller addrs]}
if P_CALLERS is None:
    unpinned("G3", "writer callers")
else:
    got = {o: sorted(a for a, _ in callers_of(o)) for o in WRITERS}
    ck("G3", got == P_CALLERS, "callers=%s" % got)

# G4 direct tests: prior-known sites must be present with their immediates
prior_direct = {0x45dd2c: 0, 0x45dd66: 0x32, 0x45dd76: 0x64, 0x5552d9: 1}
dmap = {a: imm for a, mn, imm, w, o, ops in DIRECT}
ok4 = all(dmap.get(a) == i for a, i in prior_direct.items())
P_DIRECT = None     # pin: full direct-test map
if P_DIRECT is None:
    unpinned("G4", "full direct map (prior 4 present=%s)" % ok4)
else:
    ck("G4", dmap == P_DIRECT and ok4, "direct=%s" % dmap)

# G5 register-copy gates: the three known gates must be recovered
g51 = [g for g in REGGATES if g[0] == 0x51f711]
ok51 = bool(g51) and g51[0][2] == "0x3" and g51[0][3] == "cl,bl"
g59 = [g for g in REGGATES if g[7] == "FUN_0059ec90"]
P_G5 = None         # pin: measured gate shapes (59ec90 read addr, 558 setg chain)
if P_G5 is None:
    unpinned("G5", "reg-gates (51f711 ok=%s, 59ec90 reads=%s)" % (ok51, [hex(g[0]) for g in g59]))
else:
    ck("G5", ok51 and P_G5(REGGATES), "reg-gates=%d" % len(REGGATES))

# G6 address-taken set
P_ADDR = None       # pin: [(addr, callee)]
if P_ADDR is None:
    unpinned("G6", "addr-taken")
else:
    got = [(a, c[1] if c else None) for a, d, c, o in ADDRUSE]
    ck("G6", got == P_ADDR, "addr=%s" % got)

# G7 live pins parsed (m302): round=50 year=2150, distinct addresses
ck("G7", LIVE == {"year_addr": 0x985b00, "round_addr": 0x985afc, "year": 2150, "round": 50},
   "LIVE=%s" % LIVE)

# G8 M177 stamp primes: each prime is a census READ and stores into +0x94d4a8 within 15
ok8 = all(prime_ok[p][0] and prime_ok[p][1] is not None for p in PRIMES)
ck("G8", ok8 and age_ok, "primes=%s age_ok=%s" % (prime_ok, age_ok))

# G9 widths/blind spots: exactly 2 byte accesses, no word; byte sites pinned
byte_sites = sorted(h[0] for h in hits if h[2] == "byte")
ck("G9", byte_sites == [0x5552d9, 0x555da0] and WIDTHS.get("word", 0) == 0,
   "byte=%s word=%d" % ([hex(a) for a in byte_sites], WIDTHS.get("word", 0)))

# R1 YEAR rival: 0x985afc holds the year -> must FAIL on the live pins
r1 = LIVE is not None and LIVE["round_addr"] == TGT and LIVE["round"] != LIVE["year"] \
     and LIVE["year_addr"] != TGT
ck("R1", r1, "YEAR rival dead: round=%s@0x985afc vs year=%s@0x%x" % (
    LIVE and LIVE["round"], LIVE and LIVE["year"], LIVE and LIVE["year_addr"]))

# R2 MODE-ENUM rival: many writers, no monotonic +1 -> must FAIL
plus1 = [(o, a) for o, v in WRITERS.items() for a, k, e, _ in v if e == "round+1"]
r2 = len(WRITERS) <= 3 and len(plus1) >= 1 and ok8
ck("R2", r2, "MODE-ENUM rival dead: writers=%d plus1=%s stamps=%s" % (len(WRITERS), plus1, ok8))

# R3 LOAD-CONSTANT rival: written only at load -> must FAIL (+1 writer w/ callers)
P_R3 = None         # pin: the +1 writer owner + caller count measured
if P_R3 is None:
    unpinned("R3", "load-constant rival (needs writer/caller pins)")
else:
    o, nmin = P_R3
    cs = callers_of(o)
    ck("R3", o in WRITERS and any(e == "round+1" for _, _, e, _ in WRITERS[o]) and len(cs) >= nmin,
       "LOAD-CONSTANT rival dead: %s +1 writer, %d callers" % (o, len(cs)))

# ---- digest over MEASURED detail ---------------------------------------------------
det = repr((KINDS, WIDTHS,
            tuple((a, k, w, mn, ops, o) for a, k, w, mn, ops, o in hits),
            tuple(sorted((o, tuple(sorted((a, k, e) for a, k, e, _ in v))) for o, v in WRITERS.items())),
            tuple(sorted((o, tuple(sorted(a for a, _ in callers_of(o)))) for o in WRITERS)),
            tuple((a, mn, imm) for a, mn, imm, w, o, ops in DIRECT),
            tuple(REGGATES), tuple(ADDRUSE), LIVE, prime_ok, age_ok))
h = hashlib.sha256(det.encode()).hexdigest()[:16]
print("digest %s" % h)
print("== M323: %d/%d ==" % (12 - len(BAD), 12))
sys.exit(1 if BAD else 0)
