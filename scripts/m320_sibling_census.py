#!/usr/bin/env python3
# M320: SIBLING-FIELD census of the 8380-B faction block record.
# STATIC only (zero box). Cache: scratch/m574/text.txt (full .text objdump),
# owners: ghidra_out/index.csv. Law: table FIRST, then ASSERT; digests hash
# MEASURED detail values. Code mutants: M320_PATCH="addr|mn ops;...".
# Algorithm mutants: M320_ALGO=1 (fold evaluator shl->add), =2 (W/R swap).
#
# Footing (prior V laws, cited not re-derived):
#   base 0x94d430 stride 0x20bc x8 blocks (M295/M303; atlas 0x94d104 phrasing WRONG)
#   GOAL 75x16 @block+0x19f8 (M316), SITE 25x16 @+0x1ea8 (M308),
#   region-category 128B @+0x1978 (M251), visit MAX/CNT 2x128B @+0x1878 (M303).
# Sibling territory = block offsets OUTSIDE those four named structures.
import os, re, sys, csv, bisect, hashlib, collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")
IDX = os.path.join(REPO, "ghidra_out", "index.csv")

BASE = 0x94d430
STRIDE = 0x20bc
NBLK = 8
ARRAY_HI = BASE + NBLK * STRIDE          # 0x95da10
BLOCK0_HI = BASE + STRIDE                # 0x94f4ec
GOAL = (0x19f8, 0x1ea8)                  # 0x94ee28, 75*16 (M316)
SITE = (0x1ea8, 0x2038)                  # 0x94f2d8, 25*16 (M308)
REGION = (0x1978, 0x19f8)                # 0x94eda8, 128 (M251)
VISIT = (0x1878, 0x1978)                 # 0x94eca8 MAX + 0x94ed28 CNT, 2*128 (M303)
EXCL = [("GOAL", GOAL), ("SITE", SITE), ("REGION", REGION), ("VISIT", VISIT)]
ALGO = os.environ.get("M320_ALGO", "")

def load_ins():
    ins = {}
    lin = re.compile(r"^\s*([0-9a-f]{6,8}):\s[0-9a-f ]+\t(\w+)\s*(.*)$")
    for ln in open(TEXT):
        m = lin.match(ln)
        if m:
            ins[int(m.group(1), 16)] = (m.group(2), m.group(3).strip())
    p = os.environ.get("M320_PATCH")
    n = 0
    if p:
        for chunk in p.split(";"):
            chunk = chunk.strip()
            if not chunk: continue
            addr, rest = chunk.split("|", 1)
            mn, _, ops = rest.partition(" ")
            a = int(addr, 16)
            if a not in ins:
                raise SystemExit("M320_PATCH address not in .text cache: %s" % addr)
            if ins[a] == (mn, ops.strip()):
                raise SystemExit("M320_PATCH applied to nothing (already equal)")
            ins[a] = (mn, ops.strip()); n += 1
        if n == 0: raise SystemExit("M320_PATCH applied to nothing")
    return ins

INS = load_ins()
ADDRS = sorted(INS)
funcs = []
with open(IDX) as f:
    for r in csv.DictReader(f):
        funcs.append((int(r["addr"], 16), r["name"], int(r["size_bytes"] or 0)))
funcs.sort()
FSTARTS = [a for a, _, _ in funcs]
def owner(a):
    i = bisect.bisect_right(FSTARTS, a) - 1
    if i >= 0 and a < funcs[i][0] + max(funcs[i][2], 1):
        return funcs[i][1]
    return "?"

MEM_RE = re.compile(r"(?:(BYTE|WORD|DWORD|QWORD|FWORD)\s+PTR\s*)?\[([^\]]+)\]")
ABS_RE = re.compile(r"\bds:0x([0-9a-f]+)\b")
DISP_RE = re.compile(r"([+-])0x([0-9a-f]+)\s*$")
RMW = {"inc", "dec", "add", "sub", "and", "or", "xor", "not", "neg", "adc", "sbb",
       "rol", "ror", "shl", "shr", "sar", "btc", "btr", "bts"}
READ_FIRST = {"cmp", "test", "bt"}

def parse_mems(ops):
    out = []
    for m in MEM_RE.finditer(ops):
        size = (m.group(1) or "DWORD").lower()
        inner = m.group(2)
        d = DISP_RE.search(inner)
        disp = 0
        if d:
            disp = int(d.group(2), 16) * (-1 if d.group(1) == "-" else 1)
        scale = 1
        sm = re.search(r"\*(\d)", inner)
        if sm: scale = int(sm.group(1))
        out.append((size, disp, scale, sm is not None))
    if not out:
        for m in ABS_RE.finditer(ops):
            out.append(("dword", int(m.group(1), 16), 1, False))
    return out

def classify(mn, ops, mem_is_first):
    if mn == "lea": return "lea"
    if mn in RMW: return "RW"
    if mem_is_first and mn not in READ_FIRST:
        return "R" if ALGO == "2" else "W"
    return "W" if (ALGO == "2" and mem_is_first is False and mn == "mov") else "R"

hits = []
for a in ADDRS:
    mn, ops = INS[a]
    mems = parse_mems(ops)
    if not mems: continue
    first_is_mem = bool(MEM_RE.match(ops.split(",")[0])) or ops.split(",")[0].strip().startswith("ds:")
    for (size, disp, scale, has_index) in mems:
        if not (BASE <= disp < ARRAY_HI): continue
        rel = disp - BASE
        blk, off = divmod(rel, STRIDE)
        kind = classify(mn, ops, first_is_mem)
        hits.append((a, mn, ops, blk, off, size, kind, scale, has_index, owner(a)))

def zone(off):
    for nm, (lo, hi) in EXCL:
        if lo <= off < hi: return nm
    return "SIBLING"

agg = {}
for (a, mn, ops, blk, off, size, kind, scale, has_index, own) in hits:
    e = agg.setdefault(off, {"refs": 0, "R": 0, "W": 0, "RW": 0, "lea": 0,
                             "sizes": collections.Counter(), "funcs": collections.Counter(),
                             "scales": collections.Counter(), "consts": collections.Counter(),
                             "tests": collections.Counter(), "sites": []})
    e["refs"] += 1; e[kind] += 1
    e["sizes"][size] += 1; e["funcs"][own] += 1
    if has_index: e["scales"][scale] += 1
    e["sites"].append((a, blk, mn, ops, kind))
    if kind in ("W", "RW"):
        cm = re.search(r",\s*(0x[0-9a-f]+|-?\d+)\s*$", ops)
        if cm and mn in ("mov", "add", "sub", "and", "or", "xor"):
            e["consts"][cm.group(1)] += 1
    if mn in ("cmp", "test"):
        cm = re.search(r",\s*(0x[0-9a-f]+|-?\d+)\s*$", ops)
        if cm: e["tests"][cm.group(1)] += 1

sib = {o: e for o, e in agg.items() if zone(o) == "SIBLING"}
exc = {o: e for o, e in agg.items() if zone(o) != "SIBLING"}

# ---------- TABLE FIRST ----------
print("== M320 sibling census: block base 0x%x stride 0x%x x%d, window [0x%x,0x%x) ==" %
      (BASE, STRIDE, NBLK, BASE, ARRAY_HI))
print("hits total=%d  distinct offsets=%d  sibling offsets=%d  excluded offsets=%d" %
      (len(hits), len(agg), len(sib), len(exc)))
print("kind partition: R=%d W=%d RW=%d lea=%d" %
      tuple(sum(e[k] for e in agg.values()) for k in ("R", "W", "RW", "lea")))
print()
print("-- SIBLING offsets (outside GOAL/SITE/REGION/VISIT) --")
print("off     abs0      refs   R   W  RW lea  sizes        scales  top funcs")
for off in sorted(sib):
    e = sib[off]
    sz = ",".join("%s:%d" % (s, n) for s, n in e["sizes"].most_common())
    sc = ",".join("*%d:%d" % (s, n) for s, n in e["scales"].most_common()) or "-"
    tf = ",".join("%s:%d" % (f, n) for f, n in e["funcs"].most_common(3))
    print("+0x%04x 0x%06x %5d %3d %3d %3d %3d  %-12s %-7s %s" %
          (off, BASE + off, e["refs"], e["R"], e["W"], e["RW"], e["lea"], sz, sc, tf))
print()
print("-- sibling consts written / tested-against (naming material) --")
for off in sorted(sib):
    e = sib[off]
    if e["consts"] or e["tests"]:
        print("+0x%04x  W-consts %s | cmp/test %s" %
              (off, dict(e["consts"].most_common(8)), dict(e["tests"].most_common(8))))
print()
print("-- excluded-zone offsets (sanity: named structures only) --")
for off in sorted(exc):
    print("+0x%04x %-6s refs=%d" % (off, zone(off), exc[off]["refs"]))
print()
print("-- literal block-k witnesses (blk>0, same field at 0x%x+k*0x%x) --" % (BASE, STRIDE))
wit = collections.defaultdict(list)
for (a, mn, ops, blk, off, size, kind, scale, has_index, own) in hits:
    if blk > 0: wit[(off, blk)].append((a, mn, ops, kind, own))
for (off, blk) in sorted(wit):
    for (a, mn, ops, kind, own) in wit[(off, blk)]:
        print("+0x%04x blk%d 0x%06x: %-4s %s %s  [%s]" % (off, blk, a, kind, mn, ops, own))

# ---------- measurement helpers for the gates ----------
def pin(a):
    return (a, INS[a][0], INS[a][1])

def backdef_bx(lo, hi):
    """last direct write to ebx/bx/bl before hi, within [lo,hi); cdecl: calls preserve ebx."""
    last = None
    for a in ADDRS:
        if not (lo <= a < hi): continue
        mn, ops = INS[a]
        d = ops.split(",")[0].strip()
        if d in ("ebx", "bx", "bl") and mn in ("mov", "movzx", "movsx", "xor", "pop", "lea",
                                               "add", "sub", "and", "or", "inc", "dec"):
            last = (a, mn, ops)
    return last

# linear symbolic fold evaluator: value = {reg: coeff} + {"$": const}
def ladd(x, y, s=1):
    z = dict(x)
    for k, v in y.items(): z[k] = z.get(k, 0) + s * v
    return z
def lmul(x, n):
    return {k: v * n for k, v in x.items()}
def lea_val(inner, env):
    v = {"$": 0}
    for term in re.findall(r"[+-]?[^+-]+", inner):
        term = term.strip()
        sign = -1 if term.startswith("-") else 1
        t = term.lstrip("+-")
        m = re.match(r"^(e[a-d]x|esi|edi|ebp)\*(\d)$", t)
        if m: v = ladd(v, lmul(env[m.group(1)], int(m.group(2))), sign); continue
        m = re.match(r"^0x([0-9a-f]+)$", t)
        if m: v["$"] = v.get("$", 0) + sign * int(m.group(1), 16); continue
        if t in env: v = ladd(v, env[t], sign); continue
        raise SystemExit("fold: unhandled term %r" % t)
    return v
def eval_fold(seq, env, mem_map=None):
    """seq = list of (mn, ops); env = {reg: linear value}. Returns env.
    mem_map: operand-text -> symbol name for memory loads (named inputs)."""
    env = dict(env)
    mem_map = mem_map or {}
    for mn, ops in seq:
        d, _, s = ops.partition(",")
        d, s = d.strip(), s.strip()
        if mn == "mov":
            if re.match(r"^0x[0-9a-f]+$", s): env[d] = {"$": int(s, 16)}
            elif s in env: env[d] = dict(env[s])
            elif s in mem_map: env[d] = {mem_map[s]: 1}
            else: raise SystemExit("fold: mov src %r" % s)
        elif mn == "xor" and d == s: env[d] = {"$": 0}
        elif mn == "shl":
            n = int(s, 16) if s.startswith("0x") else int(s)
            env[d] = ladd(env[d], env[d], (2 ** n) - 1) if ALGO != "1" else ladd(env[d], {"$": n})
        elif mn == "add": env[d] = ladd(env[d], env[s])
        elif mn == "sub": env[d] = ladd(env[d], env[s], -1)
        elif mn == "inc": env[d] = ladd(env[d], {"$": 1})
        elif mn == "lea":
            m = re.match(r"^\[([^\]]+)\]$", s)
            if not m: raise SystemExit("fold: lea src %r" % s)
            env[d] = lea_val(m.group(1), env)
        else: raise SystemExit("fold: unhandled %s %s" % (mn, ops))
    return env
def fseq(lo, hi):
    return [(INS[a][0], INS[a][1]) for a in ADDRS if lo <= a < hi]

# blind-spot classes (MEASURED, declared)
imm_loads = []
for a in ADDRS:
    mn, ops = INS[a]
    if mn == "mov":
        m = re.match(r"^(e[a-d]x|esi|edi|ebp),\s*0x(9[45][0-9a-f]{4})$", ops)
        if m and BASE <= int(m.group(2), 16) < ARRAY_HI:
            rel = int(m.group(2), 16) - BASE
            imm_loads.append((a, rel // STRIDE, rel % STRIDE, ops))
neg_nonstack = 0
for a in ADDRS:
    mn, ops = INS[a]
    for m in MEM_RE.finditer(ops):
        d = DISP_RE.search(m.group(2))
        if d and d.group(1) == "-" and 0 < int(d.group(2), 16) <= STRIDE \
           and not re.match(r"^(ebp|esp|rbp|rsp)", m.group(2)):
            neg_nonstack += 1
            break
print()
print("-- blind spots (MEASURED): immediate block-pointer loads=%d, non-stack negative disp<=%d =%d --" %
      (len(imm_loads), STRIDE, neg_nonstack))
for (a, blk, off, ops) in imm_loads:
    print("imm 0x%06x: blk%d +0x%04x  mov %s" % (a, blk, off, ops))

# ---------- gates ----------
results = []
def ck(name, ok, detail):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + " " + name + "  " + detail)

# G1: named-structure arithmetic (M316/M308/M251/M303 constants)
ck("G1", BASE + GOAL[0] == 0x94ee28 and 0x94ee28 + 75 * 16 == 0x94f2d8
   and 0x94f2d8 + 25 * 16 == BASE + SITE[1] and SITE[1] - SITE[0] == 25 * 16
   and GOAL[1] - GOAL[0] == 75 * 16 and REGION[1] - REGION[0] == 128
   and VISIT[1] - VISIT[0] == 256 and ARRAY_HI == 0x95da10,
   "bands: GOAL 75x16 @+0x19f8, SITE 25x16 @+0x1ea8, tail=0x%x B, array end 0x%x" %
   (STRIDE - SITE[1], ARRAY_HI))

# G2: census partition (MEASURED pass-1 literals)
tot = {k: sum(e[k] for e in agg.values()) for k in ("R", "W", "RW", "lea")}
ck("G2", len(hits) == 4111 and len(agg) == 208 and len(sib) == 196 and len(exc) == 12
   and tot == {"R": 3029, "W": 579, "RW": 195, "lea": 308}
   and sum(tot.values()) == len(hits),
   "hits=%d offsets=%d sib=%d exc=%d kinds=%s" % (len(hits), len(agg), len(sib), len(exc), tot))

# G3: prior-census cross-checks (M316's 65 GOAL refs, M308's 17 SITE refs, M303's 11th mention)
gz = sum(e["refs"] for o, e in agg.items() if zone(o) == "GOAL")
sz = sum(e["refs"] for o, e in agg.items() if zone(o) == "SITE")
vz = sum(e["refs"] for o, e in agg.items() if zone(o) == "VISIT")
endm = [a for a in ADDRS if "0x95f288" in INS[a][1]]
ck("G3", gz == 65 and sz == 17 and vz == 10 and endm == [0x51dcfd],
   "GOAL refs=%d (M316:65), SITE refs=%d (M308:17), VISIT disp-refs=%d + end-sentinel 0x95f288 @%s (M303's 11th)" %
   (gz, sz, vz, [hex(a) for a in endm]))

# G4: reset LADDER loop - 5 arrays x 128, instruction-exact (FUN_0059ec90)
G4PINS = {
    0x59efeb: ("xor", "eax,eax"),
    0x59efed: ("lea", "ecx,[esi+0x94e6a8]"),
    0x59eff3: ("mov", "WORD PTR [ecx-0x200],bx"),
    0x59effa: ("mov", "BYTE PTR [esi+eax*1+0x94e5a8],0x0"),
    0x59f002: ("mov", "BYTE PTR [esi+eax*1+0x94e628],0x0"),
    0x59f00a: ("mov", "WORD PTR [ecx],bx"),
    0x59f00d: ("mov", "WORD PTR [ecx+0x100],bx"),
    0x59f014: ("inc", "eax"),
    0x59f015: ("add", "ecx,0x2"),
    0x59f018: ("cmp", "eax,0x80"),
    0x59f01d: ("jl", "0x59eff3"),
}
g4ok = all(pin(a) == (a, m, o) for a, (m, o) in G4PINS.items())
bxdef = backdef_bx(0x59ec90, 0x59efeb)
g4ok = g4ok and bxdef == (0x59ee73, "xor", "ebx,ebx")
# derived array set: ecx base +0x1278; [ecx-0x200]=+0x1078, [ecx]=+0x1278, [ecx+0x100]=+0x1378
g4arrays = {0x1078, 0x1178, 0x11f8, 0x1278, 0x1378}
ck("G4", g4ok and g4arrays == {0x1278 - 0x200, 0x1178, 0x11f8, 0x1278, 0x1278 + 0x100},
   "reset ladder loop 59efeb-59f01d: 5 arrays {1078,1178,11f8,1278,1378} x128 (cmp 0x80, jl 59eff3, add ecx,2); bx=0 via xor ebx,ebx @59ee73; pins=%d/%d bxdef=%s" %
   (sum(1 for a, (m, o) in G4PINS.items() if pin(a) == (a, m, o)), len(G4PINS),
    ("0x%x" % bxdef[0], bxdef[1], bxdef[2]) if bxdef else None))

# G5: rebuild INIT loop - 4 word arrays + MAX/CNT x 128 x 8 blocks (FUN_0051dcb0 head)
G5PINS = {
    0x51dcb8: ("mov", "edx,0x94eca8"),
    0x51dcbd: ("xor", "esi,esi"),
    0x51dcbf: ("xor", "ecx,ecx"),
    0x51dcc1: ("lea", "eax,[edx-0x400]"),
    0x51dcc7: ("mov", "WORD PTR [eax+0x200],si"),
    0x51dcce: ("mov", "WORD PTR [eax],si"),
    0x51dcd1: ("mov", "WORD PTR [eax+0x100],si"),
    0x51dcd8: ("mov", "WORD PTR [eax+0x300],si"),
    0x51dcdf: ("mov", "BYTE PTR [edx+ecx*1+0x80],0x0"),
    0x51dce7: ("mov", "BYTE PTR [edx+ecx*1],0x0"),
    0x51dceb: ("inc", "ecx"),
    0x51dcec: ("add", "eax,0x2"),
    0x51dcef: ("cmp", "ecx,0x80"),
    0x51dcf5: ("jl", "0x51dcc7"),
    0x51dcf7: ("add", "edx,0x20bc"),
    0x51dcfd: ("cmp", "edx,0x95f288"),
}
g5ok = all(pin(a) == (a, m, o) for a, (m, o) in G5PINS.items())
g5back = pin(0x51dd03)
g5ok = g5ok and g5back == (0x51dd03, "jl", "0x51dcbd")
g5arrays = {0x1478, 0x1578, 0x1678, 0x1778, 0x1878, 0x18f8}
ck("G5", g5ok and g5arrays == {0x1878 - 0x400, 0x1878 - 0x300, 0x1878 - 0x200, 0x1878 - 0x100, 0x1878, 0x1878 + 0x80}
   and (0x95f288 - 0x94eca8) // STRIDE == 8,
   "rebuild init 51dcb8-51dd03: word {1478,1578,1678,1778} + MAX/CNT {1878,18f8} x128 (cmp ecx,0x80) x8 blocks (end 0x95f288); lea [edx-0x400] resolves 0x94eca8-0x400=0x94e8a8; pins=%d/%d backedge=%s" %
   (sum(1 for a, (m, o) in G5PINS.items() if pin(a) == (a, m, o)), len(G5PINS),
    ("0x%x" % g5back[0], g5back[1], g5back[2])))

# G6: 512-entry init - byte {854,a54} + word c54, fold 8380*edi+2*eax (FUN_0059ec90)
G6PINS = {
    0x59f19c: ("xor", "edx,edx"),
    0x59f19e: ("xor", "eax,eax"),
    0x59f1a0: ("mov", "ecx,DWORD PTR ds:0x985afc"),
    0x59f1a6: ("mov", "BYTE PTR [ebx+eax*1+0x94dc84],0x0"),
    0x59f1ae: ("cmp", "ecx,edx"),
    0x59f1b0: ("mov", "BYTE PTR [ebx+eax*1+0x94de84],0x0"),
    0x59f1b8: ("jne", "0x59f1d4"),
    0x59f1cc: ("mov", "WORD PTR [esi*2+0x94e084],dx"),
    0x59f1d4: ("inc", "eax"),
    0x59f1d5: ("cmp", "eax,0x200"),
    0x59f1da: ("jl", "0x59f1a0"),
}
g6ok = all(pin(a) == (a, m, o) for a, (m, o) in G6PINS.items())
env6 = eval_fold(fseq(0x59f1ba, 0x59f1cc), {"edi": {"edi": 1}, "eax": {"eax": 1}})
fold6 = env6["esi"]
# M303 law: the width multiplier can live in the STORE's SIB scale, not the fold.
store6_m = re.search(r"\*(\d)", G6PINS[0x59f1cc][1])
if not store6_m: raise SystemExit("G6: store scale not found in pin")
store6_scale = int(store6_m.group(1))
eff6 = {k: v * store6_scale for k, v in fold6.items()}
edx_writes = [a for a in ADDRS if 0x59f1a0 <= a < 0x59f1da
              and INS[a][1].split(",")[0].strip() in ("edx", "dx", "dl")
              and INS[a][0] in ("mov", "movzx", "movsx", "xor", "pop", "lea", "add", "sub", "and", "or", "inc", "dec")]
g6ok = g6ok and fold6 == {"edi": 4190, "eax": 1, "$": 0} and store6_scale == 2 \
       and eff6 == {"edi": 8380, "eax": 2, "$": 0} and edx_writes == []
ck("G6", g6ok,
   "512-init 59f19c-59f1da: byte {854,a54} + word c54 x512 (cmp eax,0x200, jl 59f1a0); fold esi=%s, store scale *%d -> addr coeff %s (want edi*8380+eax*2); word store gated cmp ecx,edx w/ ecx=ds:0x985afc, edx untouched in loop (%d writes); pins=%d/%d" %
   (fold6, store6_scale, eff6, len(edx_writes), sum(1 for a, (m, o) in G6PINS.items() if pin(a) == (a, m, o)), len(G6PINS)))

# G7: rebuild COUNTERS - 3 conditional incs + the 7-block faction walk (FUN_0051dcb0)
G7PINS = {
    0x51df3d: ("inc", "WORD PTR [eax+0x94e8a8]"),
    0x51df46: ("test", "cl,0x18"),
    0x51df50: ("and", "edx,0xffffffc0"),
    0x51df53: ("cmp", "edx,0x80"),
    0x51df5b: ("test", "BYTE PTR [edi+0x8],0x20"),
    0x51df61: ("inc", "WORD PTR [eax+0x94eaa8]"),
    0x51df6b: ("test", "ch,0x10"),
    0x51df70: ("inc", "WORD PTR [eax+0x94eba8]"),
    0x51dd4a: ("mov", "esi,0x1"),
    0x51dd52: ("mov", "eax,0x94f4ec"),
    0x51dd5a: ("lea", "ebx,[ecx*2+0x950a64]"),
    0x51dd89: ("inc", "WORD PTR [ebx]"),
    0x51dd8c: ("add", "eax,0x20bc"),
    0x51dd92: ("add", "ebx,0x20bc"),
    0x51dd98: ("cmp", "eax,0x95da10"),
    0x51dd9d: ("jl", "0x51dd61"),
}
g7ok = all(pin(a) == (a, m, o) for a, (m, o) in G7PINS.items())
# [ebp-0xc] = site = BYTE[tile_record+3] (M303 S3, V) - named symbolic input
env7 = eval_fold(fseq(0x51df26, 0x51df3d), {"ebx": {"ebx": 1}, "ecx": {"ecx": 1}},
                 mem_map={"DWORD PTR [ebp-0xc]": "site"})
fold7 = env7["eax"]
g7ok = g7ok and fold7 == {"ebx": 8380, "site": 2, "$": 0} and (0x95da10 - 0x94f4ec) // STRIDE == 7
ck("G7", g7ok,
   "counters: inc WORD +1478 @51df3d (unconditional), +1678 @51df61 (test cl,0x18 + (BYTE[tile+5]&0xc0)<0x80 + ~bit 0x20[tile+8]), +1778 @51df70 (+bit12 [tile+8]); fold eax=%s (want ebx*8380+site*2, site=BYTE[tile+3] per M303); +1578 walk: start 0x94f4ec=blk1, esi=1, bound 0x95da10 -> 7 blocks, inc WORD [ebx] @51dd89; pins=%d/%d" %
   (fold7, sum(1 for a, (m, o) in G7PINS.items() if pin(a) == (a, m, o)), len(G7PINS)))

# G8: FUN_0059ec90 = the block RESET: 114 W/RW sites, 93 sibling offsets, all blk0
RESET_OFFS = {0x0,0x8,0xc,0x10,0x14,0xb8,0xc0,0x124,0x128,0x1cc,0x1d0,0x1d4,0x1d8,0x1dc,
              0x220,0x224,0x248,0x2d0,0x2fc,0x300,0x304,0x308,0x30c,0x310,0x314,0x318,0x31c,
              0x320,0x324,0x328,0x35c,0x360,0x364,0x368,0x3c8,0x3cc,0x3d0,0x3d4,0x3d8,0x3dc,
              0x3e0,0x3e4,0x3e8,0x3ec,0x3f0,0x3f4,0x3f8,0x3fc,0x458,0x45c,0x460,0x464,0x468,
              0x804,0x808,0x80c,0x810,0x814,0x818,0x81c,0x820,0x824,0x828,0x82c,0x830,0x834,
              0x838,0x854,0xa54,0xc54,0x1054,0x1058,0x105c,0x1060,0x1064,0x1068,0x1178,0x11f8,
              0x2038,0x203c,0x2040,0x2044,0x2048,0x204c,0x2050,0x2058,0x205c,0x2060,0x2064,
              0x2068,0x2078,0x2080}
rw = [h for h in hits if h[9] == "FUN_0059ec90" and h[6] in ("W", "RW")]
rw_offs = set(h[4] for h in rw)
G8PINS = {
    0x59ed62: ("mov", "DWORD PTR [ebx+0x94d430],0x0"),
    0x59ed6c: ("mov", "DWORD PTR [ebx+0x94d600],0xdfbe41"),
    0x59ed7a: ("mov", "DWORD PTR [ebx+0x94d600],0xc0dfbe41"),
    0x59ef16: ("mov", "DWORD PTR [esi+0x94d82c],0xfffffc19"),
    0x59f06e: ("mov", "DWORD PTR [esi+0x94f480],0x1"),
    0x59fda6: ("mov", "DWORD PTR [eax+0x94d758],0x5"),
    0x59fdb0: ("mov", "DWORD PTR [eax+0x94d754],0x0"),
}
callers = sorted(a for a in ADDRS if INS[a][0] == "call" and INS[a][1].strip() == "0x59ec90")
g8ok = (len(rw) == 114 and rw_offs == RESET_OFFS and all(h[3] == 0 for h in rw)
        and all(pin(a) == (a, m, o) for a, (m, o) in G8PINS.items())
        and callers == [0x5a0b39, 0x5a123e, 0x5a1277]
        and [owner(a) for a in callers] == ["FUN_005a0aa0", "FUN_005a0fa0", "FUN_005a0fa0"])
ck("G8", g8ok,
   "reset FUN_0059ec90: W/RW=%d (want 114), offsets=%d (want 92), all blk0=%s; flagword clear @59ed62, magic 0xdfbe41/0xc0dfbe41 @+1d0, -999 @+3fc, tail +2050=1, +328=5/+324=0; callers=%s" %
   (len(rw), len(rw_offs), all(h[3] == 0 for h in rw), [hex(a) for a in callers]))

# G9: blind spots MEASURED + the three lea-pair resolutions pinned
G9PINS = {
    0x59efcf: ("lea", "eax,[esi+0x94d630]"),
    0x59efd5: ("mov", "ecx,0x8"),
    0x59efda: ("mov", "DWORD PTR [eax-0x20],ebx"),
    0x59efdd: ("mov", "DWORD PTR [eax],ebx"),
    0x59efdf: ("add", "eax,0x4"),
    0x59f08f: ("lea", "esi,[ebx+0x94d4c8]"),
    0x59f0ec: ("mov", "DWORD PTR [esi-0x80],0x0"),
}
g9ok = (len(imm_loads) == 61 and neg_nonstack == 3293
        and sum(1 for (a, b, o, ops) in imm_loads if b == 1 and o == 0) == 6
        and all(pin(a) == (a, m, o) for a, (m, o) in G9PINS.items())
        and 0x94d630 - 0x20 - BASE == 0x1e0 and 0x94d4c8 - 0x80 - BASE == 0x18)
ck("G9", g9ok,
   "blind spots: imm block-pointer loads=%d (want 61; incl 6x 0x94f4ec=blk1+0, measured=%d), non-stack neg-disp=%d (want 3293, out of scope); lea-pairs: [eax-0x20]@59efda=+1e0 (8-pair dword loop, ecx=8), [esi-0x80]@59f0ec=+18 pair-array clear; pins=%d/%d" %
   (len(imm_loads), sum(1 for (a, b, o, ops) in imm_loads if b == 1 and o == 0), neg_nonstack,
    sum(1 for a, (m, o) in G9PINS.items() if pin(a) == (a, m, o)), len(G9PINS)))

# G10: flagword +0x0 bit census
fw = agg.get(0, {})
fw_tests = dict(fw.get("tests", {}))
G10_OR = {0x59ff21: "0x1000000", 0x59ff3e: "0x2000000", 0x59ff77: "0x4000000",
          0x59ffaa: "0x8000000", 0x59ffc7: "0x10000000"}
g10ok = (fw_tests.get("0x400000") == 7 and fw_tests.get("0x20000000") == 6
         and fw_tests.get("0x1000000") == 5 and fw_tests.get("0x200") == 4
         and fw_tests.get("0x80000") == 4 and fw_tests.get("0x40000000") == 3
         and fw_tests.get("0x200000") == 3 and fw_tests.get("0x10000000") == 1
         and all(INS[a] == ("or", "DWORD PTR [edi+0x94d430],%s" % v) for a, v in G10_OR.items())
         and pin(0x5a04d1) == (0x5a04d1, "mov", "ecx,DWORD PTR [eax+0x94d430]")
         and pin(0x5a04d7) == (0x5a04d7, "or", "ch,0x1")
         and pin(0x5a04da) == (0x5a04da, "mov", "DWORD PTR [eax+0x94d430],ecx"))
ck("G10", g10ok,
   "flagword +0x0: tests {400000:7, 20000000:6, 1000000:5, 200:4, 80000:4(bit19, M317 prio), 40000000:3, 200000:3, 10000000:1}; OR bits 24-28 @59ff21-59ffc7; bit8 via or ch,1 RMW triple 5a04d1/d7/da; measured=%s" %
   {k: fw_tests.get(k) for k in ("0x400000", "0x20000000", "0x1000000", "0x200", "0x80000")})

# R1 RIVAL: "the +0x2038 tail is a third 16-B record array (like GOAL/SITE)" - must FAIL
tail = sorted(o for o in sib if o >= 0x2038)
tspan = (tail[-1] + 4) - tail[0]
tdeltas = collections.Counter(tail[i + 1] - tail[i] for i in range(len(tail) - 1))
tword = sum(e["sizes"].get("word", 0) for o, e in sib.items() if o >= 0x2038)
tstride = []
for nm, lo, hi in (("FUN_0056df40", 0x56df40, 0x5701e7), ("FUN_0059ec90", 0x59ec90, 0x5a0a9d)):
    tstride += [a for a in ADDRS if lo <= a < hi and INS[a][0] == "add"
                and re.match(r"^(eax|ebx|ecx|edx|esi|edi),0x10$", INS[a][1])]
r1_falsified = (len(tail) == 31 and tspan == 0x84 and tspan % 16 == 4
                and dict(tdeltas) == {4: 28, 8: 2} and tword == 0 and tstride == [])
ck("R1", r1_falsified,
   "RIVAL tail=16B-record-array FAILS: %d offsets span 0x%x (%%16=%d, not tileable), deltas=%s, word-refs=%d, stride-0x10 adds in tail owners=%d" %
   (len(tail), tspan, tspan % 16, dict(tdeltas), tword, len(tstride)))

# R2 RIVAL: "the +0x1478 word array is 512-entry like +0xc54" - must FAIL
r2_falsified = (INS[0x51dcef] == ("cmp", "ecx,0x80") and INS[0x59f1d5] == ("cmp", "eax,0x200")
                and (0x1578 - 0x1478) // 2 == 128 and (0x1054 - 0xc54) // 2 == 512)
ck("R2", r2_falsified,
   "RIVAL +1478=512-entry FAILS: its init bound is cmp ecx,0x80 @51dcef (128) vs cmp eax,0x200 @59f1d5 (512) for +c54; span 0x100/2=128 entries")

# digest over MEASURED detail
h = hashlib.sha256()
for off in sorted(agg):
    e = agg[off]
    h.update(("%d:%d:%d:%d:%d:%d|" % (off, e["refs"], e["R"], e["W"], e["RW"], e["lea"])).encode())
    for (a, blk, mn, ops, kind) in e["sites"]:
        h.update(("%x:%d:%s:%s:%s|" % (a, blk, mn, ops, kind)).encode())
for (a, blk, off, ops) in imm_loads:
    h.update(("imm:%x:%d:%d:%s|" % (a, blk, off, ops)).encode())
h.update(("neg:%d|" % neg_nonstack).encode())
h.update(("fold6:%s|fold7:%s|" % (sorted(fold6.items()), sorted(fold7.items()))).encode())
for (nm, ok, detail) in results:
    h.update(("%s:%s|" % (nm, detail)).encode())
digest = h.hexdigest()[:16]
npass = sum(1 for _, ok, _ in results if ok)
print("digest %s" % digest)
print("== M320: %d/%d ==" % (npass, len(results)))
sys.exit(0 if npass == len(results) else 1)