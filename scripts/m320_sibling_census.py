#!/usr/bin/env python3
# M320: SIBLING-FIELD census of the 8380-B faction block record.
# STATIC only (zero box). Cache: scratch/m574/text.txt (full .text objdump),
# owners: ghidra_out/index.csv. Law: table FIRST, then ASSERT; digests hash
# MEASURED detail values. Code mutants via M320_PATCH="addr|mn ops;...".
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
# named structures, block-relative [lo, hi)
GOAL = (0x19f8, 0x1ea8)                  # 0x94ee28, 75*16 (M316)
SITE = (0x1ea8, 0x2038)                  # 0x94f2d8, 25*16 (M308)
REGION = (0x1978, 0x19f8)                # 0x94eda8, 128 (M251)
VISIT = (0x1878, 0x1978)                 # 0x94eca8 MAX + 0x94ed28 CNT, 2*128 (M303)
EXCL = [("GOAL", GOAL), ("SITE", SITE), ("REGION", REGION), ("VISIT", VISIT)]

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

# ---------- operand parsing ----------
MEM_RE = re.compile(r"(?:(BYTE|WORD|DWORD|QWORD|FWORD)\s+PTR\s*)?\[([^\]]+)\]")
ABS_RE = re.compile(r"\bds:0x([0-9a-f]+)\b")
DISP_RE = re.compile(r"([+-])0x([0-9a-f]+)\s*$")
RMW = {"inc", "dec", "add", "sub", "and", "or", "xor", "not", "neg", "adc", "sbb",
       "rol", "ror", "shl", "shr", "sar", "btc", "btr", "bts"}
READ_FIRST = {"cmp", "test", "bt"}

def parse_mems(ops):
    """yield (size, disp, sib_scale, has_index) for each memory operand."""
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
        has_index = sm is not None
        out.append((size, disp, scale, has_index))
    if not out:
        for m in ABS_RE.finditer(ops):
            out.append(("dword", int(m.group(1), 16), 1, False))
    return out

def classify(mn, ops, mem_is_first):
    if mn == "lea": return "lea"
    if mn in RMW: return "RW"
    if mem_is_first and mn not in READ_FIRST: return "W"
    return "R"

# ---------- census ----------
hits = []          # (addr, mn, ops, blk, off, size, kind, scale, has_index, owner)
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

# ---------- gates (filled after measurement; skeleton carries structural pins) ----------
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
# G2: partition completeness - every hit lands in exactly one kind and one zone
tot = sum(e[k] for e in agg.values() for k in ("R", "W", "RW", "lea"))
ck("G2", tot == len(hits) and len(sib) + len(exc) == len(agg),
   "kinds sum %d == hits %d; zones %d+%d == offsets %d" %
   (tot, len(hits), len(sib), len(exc), len(agg)))

# digest over MEASURED detail (per-offset counts + witness sites)
h = hashlib.sha256()
for off in sorted(agg):
    e = agg[off]
    h.update(("%d:%d:%d:%d:%d:%d|" % (off, e["refs"], e["R"], e["W"], e["RW"], e["lea"])).encode())
    for (a, blk, mn, ops, kind) in e["sites"]:
        h.update(("%x:%d:%s:%s:%s|" % (a, blk, mn, ops, kind)).encode())
digest = h.hexdigest()[:16]
npass = sum(1 for _, ok, _ in results if ok)
print("digest %s" % digest)
print("== M320: %d/%d ==" % (npass, len(results)))
sys.exit(0 if npass == len(results) else 1)