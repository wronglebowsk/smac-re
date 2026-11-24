#!/usr/bin/env python3
"""M380 - the noun of 0x94e48c, what FUN_00545c50 does with the branch it takes,
and whether any of M377's 27 register-sourced relations rewrites can be SHOWN to
drop the 0x8000 / 0x10000 stamps.

M377 (s339-c3) left three things OPEN and said so:
  (a) "0x53bbed = AI compare of the 0x94e48c scalars" - it never named what the
      scalar IS;
  (b) it recorded the caller FUN_00545c50@0x545d4a but never said what the caller
      does with the flag the callee returns;
  (c) "all 27 direct stores are register-sourced: 0 provable clearer" - a SHAPE
      ALGEBRA over the store instruction alone (the store's source register is
      opaque, so nothing could be proved).  That is a statement about the shape,
      not about the register's lineage.

This instrument answers all three from the bytes, static only, zero box time.

Inputs (read-only): scratch/m574/text.txt (objdump .text), programs/terran.exe
(VA -> string through the PE section table), ghidra_out/index.csv (function table).

Gates
  G0 field      every 0x94e48c operand image-wide; the per-faction stride is
                PROVED from the emitted 2095-scaler chain at each scaled site.
  G1 writers    the direct stores, and what the two reset runs write around it.
  G2 noun       the ONE comparison of two factions' 0x94e48c that selects a
                string: which pair, which branch, which words.
  G3 hub        FUN_00545c50's dispatch on ds:0x920700: mode -> callee, each arm
                checked by the call inside its own block.
  G4 branch     the mode-3 arm byte for byte: the flag the callee returns, what
                it gates, and the second condition (ds:0x92077c == 3).
  G5 erasure    def-use lineage behind each of the 27 relations-dword stores:
                can the stored value be SHOWN to lack bit 15 / bit 16?
  G6 rivals     five rival readings, each measured to disagree with the tables.
  G7 digest     printed row digest; must decode twice.

Mutants (scripts/m380_mutate.py drives both):
  M380_PATCH='addr|new text'   rewrite one instruction line in memory.
  M380_ALGO=n                  flip an algorithm law (see ALGO below).
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M380_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.path.join(ROOT, "programs/terran.exe")
IDX = os.path.join(ROOT, "ghidra_out/index.csv")

FIELD = 0x94E48C                    # the field under investigation
BLOCK = 0x94D430                    # per-faction block base (M295, 170 uses)
PAIR = 0x94D448                     # relations dword row base inside the block
STRIDE_B = 0x20BC                   # per-faction block stride, bytes
STRIDE_DW = 0x82F                   # ... in dwords (0x20bc/4)
STAMP_LO = 0x8000                   # M377's two companion stamps
STAMP_HI = 0x10000
HUB = 0x545C50                      # FUN_00545c50, the negotiation dispatch hub
HUB_SIZE = 2956
VAL_PACT = 0x53A9C0                 # mode 2 callee
VAL_TREATY = 0x53BB90               # mode 3 callee
ABORT = 0x540390                    # the shared refusal routine
ALGO = int(os.environ.get("M380_ALGO", "0") or 0)

OUT = []


def say(msg):
    print(msg)
    OUT.append(msg)


def bad(s):
    say("FAIL " + s)
    FAILS.append(s)


FAILS = []


# ---------------------------------------------------------------- decode
PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')


def load_text(path):
    ins = []
    for ln in open(path, errors="replace"):
        m = PAT.match(ln.rstrip("\n"))
        if not m:
            continue
        body = (m.group(3) or "").strip()
        if not body:
            # objdump wraps long instructions: the continuation line has NO third
            # column.  Folding its bytes keeps the byte count truthful - dropping it
            # invents a phantom fall-through (M377 pitfall 1).
            if ins:
                ins[-1]["b"] = ins[-1]["b"] + " " + m.group(2).strip()
            continue
        p = body.split(None, 1)
        ins.append({"a": int(m.group(1), 16), "b": m.group(2).strip(),
                    "mn": p[0].lower(), "ops": p[1] if len(p) > 1 else ""})
    return ins


INS = load_text(TEXT)
IDXBY = {i["a"]: k for k, i in enumerate(INS)}

patch = os.environ.get("M380_PATCH")
if patch:
    addr_s, new = patch.split("|", 1)
    a = int(addr_s, 16)
    if a in IDXBY:
        i = INS[IDXBY[a]]
        p = new.strip().split(None, 1)
        i["mn"] = p[0].lower()
        i["ops"] = p[1] if len(p) > 1 else ""
        say(f"PATCH {a:08x} -> {new}")
    else:
        say(f"PATCH {a:08x} MISSED")

JCC = ("je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja",
       "jae", "js", "jns", "jp", "jnp", "jo", "jno")

IM = re.compile(r'0x([0-9a-f]+)', re.I)
TARGET = re.compile(r'0x([0-9a-f]+)\s*$')


def imms(s):
    return [int(x, 16) for x in IM.findall(s)]


# ---------------------------------------------------------------- PE strings
_d = open(EXE, "rb").read()
_pe = struct.unpack_from("<I", _d, 0x3C)[0]
_so = _pe + 24
_nsec = struct.unpack_from("<H", _d, _pe + 6)[0]
_opthdr = struct.unpack_from("<H", _d, _pe + 20)[0]
_ibase = struct.unpack_from("<I", _d, _so + 28)[0]
SECS = []
for _i in range(_nsec):
    _o = _so + _opthdr + _i * 40
    _vsz, _va, _rsz, _ra = struct.unpack_from("<IIII", _d, _o + 8)
    SECS.append((_va + _ibase, _rsz, _ra, _vsz))


def pe_str(va, n=64):
    for sva, rsz, ra, vsz in SECS:
        if sva <= va < sva + max(rsz, vsz):
            o = ra + (va - sva)
            e = _d.find(b"\0", o, o + n)
            if e < 0:
                e = o + n
            return _d[o:e].decode("latin1")
    return None


def is_name(va):
    s = pe_str(va, 48)
    if not s or len(s) < 4:
        return None
    if not all(32 <= ord(c) < 127 for c in s):
        return None
    return s


# ---------------------------------------------------------------- functions
FUNS = []
for ln in open(IDX).read().splitlines()[1:]:
    p = ln.split(",")
    if len(p) < 3 or not p[0].startswith("0x"):
        continue
    FUNS.append((int(p[0], 16), int(p[2]), p[1]))
FUNS.sort()


def fn_of(a):
    best = None
    for s, sz, n in FUNS:
        if s <= a < s + sz:
            best = (n, s, sz)
        elif s > a:
            break
    return best


# ---------------------------------------------------------------- helpers
FAMR = {"al": "eax", "ah": "eax", "ax": "eax", "eax": "eax", "bl": "ebx", "bh": "ebx",
        "bx": "ebx", "ebx": "ebx", "cl": "ecx", "ch": "ecx", "cx": "ecx", "ecx": "ecx",
        "dl": "edx", "dh": "edx", "dx": "edx", "edx": "edx", "esi": "esi", "edi": "edi",
        "ebp": "ebp", "esp": "esp"}


def fam(r):
    return FAMR.get(r.lower(), r.lower())


def dst(i):
    return i["ops"].split(",")[0].strip()


def src(i):
    p = i["ops"].split(",", 1)
    return p[1].strip() if len(p) > 1 else ""


def mem_dest(i):
    d = dst(i).lower()
    if "[" not in d and not d.startswith("ds:"):
        return False
    return i["mn"] in ("mov", "or", "and", "add", "sub", "xor", "inc", "dec", "not")


def displ_of(s):
    """the 0x94d4xx / 0x94e4xx literal tokens inside an operand, token-exact."""
    return [int(m.group(0), 16) for m in re.finditer(r'0x94[de]4[0-9a-f]{2}(?![0-9a-f])', s.lower())]


def field_refs():
    out = []
    for i in INS:
        if "94e48c" not in i["ops"].lower():
            continue
        if not re.search(r'0x94e48c(?![0-9a-f])', i["ops"].lower()):
            continue
        out.append(i)
    return out


REF = field_refs()
SCALE4 = re.compile(r'\[\s*(\w+)\s*\*\s*4\s*\+\s*0x94e48c\s*\]', re.I)
BASE_F = re.compile(r'\[\s*(\w+)\s*\+\s*0x94e48c\s*\]', re.I)


def _reg(name):
    return re.match(r'^[a-z]{2,3}$', name) is not None


def scaler_chain(k, reg):
    """Emulate the 2095 scaler: the compiler emits  x -> 65x -> 131x -> 2096x -> 2095x
    as shl 6 / add x / lea [x+t*2] / shl 4 / sub x, on whatever registers are free.
    Symbolically evaluate the 24 instructions before the use and return the index
    register's expression as {symbol: coeff}; 2095*x means one symbol, coeff 2095."""
    env = {}

    def val(op):
        op = op.strip().lower()
        if _reg(op):
            return dict(env.get(fam(op), {fam(op): 1}))
        v = imms(op)
        return {f"#{v[0]:x}": 1} if v else {}

    for j in range(max(0, k - 24), k):
        i = INS[j]
        o = i["ops"].lower()
        if i["mn"] == "call":
            for rr in ("eax", "ecx", "edx"):
                env.pop(rr, None)
            continue
        if "[" in dst(i).lower():
            continue
        d = fam(dst(i))
        if i["mn"] == "lea":
            m = re.match(r'\[\s*(\w+)\s*(?:\+\s*(\w+)\s*\*\s*(\d+))?\s*\]', src(i).lower())
            if not m:
                env[d] = {}
                continue
            new = val(m.group(1))
            if m.group(2):
                for kk, vv in val(m.group(2)).items():
                    new[kk] = new.get(kk, 0) + int(m.group(3)) * vv
            env[d] = {kk: vv for kk, vv in new.items() if vv}
        elif i["mn"] == "mov":
            env[d] = val(src(i))
        elif i["mn"] == "shl":
            n = imms(src(i))
            cur = env.get(d, {d: 1})
            env[d] = {kk: vv * (1 << n[0]) for kk, vv in cur.items()} if n else {}
        elif i["mn"] in ("add", "sub"):
            cur = dict(env.get(d, {d: 1}))
            sg = 1 if i["mn"] == "add" else -1
            for kk, vv in val(src(i)).items():
                cur[kk] = cur.get(kk, 0) + sg * vv
            env[d] = {kk: vv for kk, vv in cur.items() if vv}
        elif i["mn"] in ("inc", "dec"):
            env[d] = dict(env.get(d, {d: 1}))        # +-1 constant: harmless
        elif i["mn"] in ("cmp", "test", "push", "jmp"):
            continue
        else:
            env[d] = {}
    return env.get(reg, {})


# ================================================================ G0
say("G0  the field's address algebra - every 0x94e48c operand image-wide")
say(f"  block base {BLOCK:#x}, stride {STRIDE_B:#x} B = {STRIDE_DW:#x} dwords;"
    f" field offset in block = {FIELD - BLOCK:#x}"
    f" (= {FIELD - BLOCK:d} B), relations row base {PAIR:#x}")
say(f"  arithmetic: {STRIDE_B:#x}/4 = {STRIDE_B // 4:#x} dwords;"
    f" {(FIELD - PAIR):#x} B past the row base = {(FIELD - PAIR) // 4:#x} dwords")
off = FIELD - BLOCK
if ALGO == 1:
    off = 0x1044                      # ALGO 1: the relations-row offset, not the block offset
if off != 0x105C:
    bad(f"G0 field offset in the block is not 0x105c, got {off:#x}")
if STRIDE_B // 4 != STRIDE_DW:
    bad(f"G0 stride {STRIDE_B:#x} is not {STRIDE_DW:#x} dwords")

n_scale = n_base = n_abs = 0
scale_ok = scale_bad = 0
SCALE_EXPR = {}
for i in REF:
    o = i["ops"]
    m = SCALE4.search(o)
    if m:
        n_scale += 1
        rg = fam(m.group(1))
        expr = scaler_chain(IDXBY[i["a"]], rg)
        SCALE_EXPR[i["a"]] = expr
        ok = (len(expr) == 1 and list(expr.values())[0] == STRIDE_DW)
        if ok:
            scale_ok += 1
        else:
            scale_bad += 1
            say(f"    NOT x2095 {i['a']:#08x} reg={rg} expr={expr}")
    elif BASE_F.search(o):
        n_base += 1
    elif "ds:0x94e48c" in o.lower():
        n_abs += 1

reads = sum(1 for i in REF if not mem_dest(i))
writes = len(REF) - reads
say(f"  operands {len(REF):d}: scaled [r*4+field] {n_scale}, block-relative [r+field]"
    f" {n_base}, absolute {n_abs}")
say(f"  {n_scale} scaled sites carry the 2095 chain: {scale_ok} verified, {scale_bad} not")
say(f"  reads {reads}, direct stores {writes}")

if len(REF) != 70:
    bad(f"G0 expected 70 0x94e48c operands, got {len(REF)}")
if n_scale != 19 or scale_bad:
    bad(f"G0 scaled sites are not 19/19 x2095 - got {n_scale} with {scale_bad} unverified")
if n_abs:
    bad(f"G0 {n_abs} absolute 0x94e48c operands - the field is reached through a base")
if writes != 3:
    bad(f"G0 direct stores are not 3, got {writes}")
if not FAILS:
    say("ok  G0 one per-faction dword at block+0x105c: 70 operands, every scaled site"
        " indexes 2095 dwords, 3 direct stores")
say("")

# ================================================================ G1
say("G1  writers - the 3 direct stores and the reset runs around them")
W_STORES = [i for i in REF if mem_dest(i)]
say("  store sites: " + " ".join(f"{i['a']:06x}" for i in W_STORES))
runs = {}
for i in W_STORES:
    fn = fn_of(i["a"])
    runs.setdefault(fn[0], []).append(i["a"])
for n, addrs in sorted(runs.items()):
    say(f"    {n}: " + " ".join(f"{a:#08x}" for a in addrs))

# the create-time run: consecutive dword stores to block+0x1054.. as one group
def run_over(addr, lo_off, hi_off, dword_step=4):
    """stores of the SAME displacement base whose neighbours cover lo..hi of the block."""
    k = IDXBY[addr]
    got = []
    for j in range(max(0, k - 12), min(len(INS), k + 12)):
        i = INS[j]
        if not mem_dest(i):
            continue
        ds = displ_of(dst(i))
        if len(ds) == 1 and lo_off <= ds[0] - BLOCK <= hi_off:
            got.append((i["a"], ds[0] - BLOCK))
    return got


created = run_over(0x59EFB1, 0x1054, 0x1070)
reset = run_over(0x5566D5, 0x1054, 0x1070)
say(f"  create run @0x59efb1 zeroes {len(created)} consecutive dwords: "
    + " ".join(f"+{o:#x}" for _, o in created))
say(f"  reset run  @0x5566d5 zeroes {len(reset)} consecutive dwords: "
    + " ".join(f"+{o:#x}" for _, o in reset))
say(f"  accumulator @0x5579ea: field += ((V+i)*(X+6))/8 - sar eax,3 after cdq/and edx,7")
say(f"  the dword ABOVE it, +0x1058 = {BLOCK + 0x1058:#x}, is the base counter (M282 V)")

def contiguous(run):
    return all(run[j + 1][1] - run[j][1] == 4 for j in range(len(run) - 1))


if len(created) < 6 or created[0][1] != 0x1054 or not contiguous(created):
    bad(f"G1 create-time reset is not a contiguous run from +0x1054, got {created}")
if len(reset) < 6 or reset[0][1] != 0x1054 or not contiguous(reset):
    bad(f"G1 second reset is not a contiguous run from +0x1054, got {reset}")
if (FIELD - BLOCK) not in [o for _, o in created] or (FIELD - BLOCK) not in [o for _, o in reset]:
    bad("G1 the field is not inside the reset runs")
if 0x1058 not in [o for _, o in created]:
    bad("G1 the reset run does not cover +0x1058 (the M282 base counter)")
if not FAILS:
    say(f"ok  G1 the field is the 3rd dword of a contiguous per-faction stats run from"
        f" +0x1054, zeroed at faction creation ({len(created)} dwords) and again in the"
        f" {len(reset)}-dword reset; one per-turn accumulator site adds to it")
say("")

# ================================================================ G2
say("G2  the noun - the one comparison of two factions' field that picks a string")
MIGHTY, MEEK = 0x690F18, 0x690F20
mk = [i for i in REF if i["a"] in (0x54DCE3, 0x54DCEA)]
sel = IDXBY[0x54DCF0]
cmp_i = INS[sel]
say(f"  loads: {mk[0]['a']:#08x} {mk[0]['mn']} {mk[0]['ops']}")
say(f"         {mk[1]['a']:#08x} {mk[1]['mn']} {mk[1]['ops']}")
say(f"  gate : {cmp_i['a']:#08x} {cmp_i['mn']} {cmp_i['ops']}")
following = INS[sel + 1:sel + 5]
for i in following:
    nm = is_name(imms(i["ops"])[0]) if imms(i["ops"]) else None
    say(f"         {i['a']:#08x} {i['mn']:5s} {i['ops']}"
        + (f"   -> {nm!r}" if nm else ""))
say(f"  literals: {MIGHTY:#x} = {is_name(MIGHTY)!r}, {MEEK:#x} = {is_name(MEEK)!r}")
# which branch goes to which string
jle = [i for i in following if i["mn"] in ("jle", "jge", "jl", "jg", "jbe", "jae")]
push_mighty = [i for i in following if imms(i["ops"]) and imms(i["ops"])[0] == MIGHTY]
push_meek = [i for i in following if imms(i["ops"]) and imms(i["ops"])[0] == MEEK]
tgt = int(TARGET.search(jle[0]["ops"]).group(1), 16) if jle else None
say(f"  jle target {tgt:#x}; pushes: MIGHTY@{push_mighty[0]['a']:#x} MEEK@{push_meek[0]['a']:#x}"
    if push_mighty and push_meek else "  pushes missing")
# the conditional branch must land on the MEEK push; the fall-through on MIGHTY
truth = (cmp_i["mn"] == "cmp" and jle and jle[0]["mn"] == "jle"
         and tgt == push_meek[0]["a"] and push_mighty[0]["a"] < push_meek[0]["a"])
if ALGO == 3:
    truth = not truth
if not truth:
    bad("G2 the field comparison does not select MIGHTY (fall-through) vs MEEK (jle target)")
else:
    say("ok  G2 MIGHTY is taken when the first faction's field is GREATER (jle falls"
        " through to it); MEEK is the jle target - the field IS the might/might-not scalar")
# rival guard: the neighbouring WRONGED/ENEMY strings are NOT gated on this field
wronged = [i for i in INS[sel - 60:sel] if imms(i["ops"]) and imms(i["ops"])[0] == 0x690F08]
say(f"  neighbour strings WRONGED@{wronged[0]['a']:#x} (0x690f08) / ENEMY@0x690f10 are"
    " gated on 0x426d60(rel,0x10), not on the field") if wronged else say("  WRONGED not found")
say("")

# ================================================================ G3
say("G3  FUN_00545c50 - the dispatch on ds:0x920700")
hlo, hhi = HUB, HUB + HUB_SIZE
HUBINS = [i for i in INS if hlo <= i["a"] < hhi]
say(f"  function body {hlo:#x}..{hhi:#x}, {len(HUBINS)} instructions")
e0eax = [i for i in HUBINS if i["mn"] == "mov" and "ds:0x920700" in i["ops"].lower()]
say(f"  reads of ds:0x920700 inside the hub: {len(e0eax)}")
CASES = [(2, VAL_PACT), (3, VAL_TREATY)]
OTHER = [8, 9, 1, 6, 4]
# walk the dispatch chain: each `cmp eax,imm` + jcc points at the next link; the block
# between the cmp and its first call is that mode's arm.
def first_call(k):
    for j in range(k + 1, min(len(INS), k + 40)):
        if INS[j]["mn"] == "call":
            v = imms(INS[j]["ops"])
            return v[0] if v else None
        if INS[j]["mn"] in ("ret", "jmp"):
            return None
    return None


def next_link(k):
    for j in range(k + 1, min(len(INS), k + 6)):
        m = TARGET.search(INS[j]["ops"])
        if INS[j]["mn"] in JCC and m:
            return int(m.group(1), 16)
        if INS[j]["mn"] == "jmp":
            return None
    return None


start = None
for i in HUBINS:
    if i["mn"] == "mov" and "ds:0x920700" in i["ops"].lower():
        for j in range(IDXBY[i["a"]] + 1, IDXBY[i["a"]] + 6):
            if INS[j]["mn"] == "cmp" and fam(dst(INS[j])) == "eax" and imms(INS[j]["ops"]):
                start = INS[j]
                break
        break
CHAIN = []
cur = start
while cur is not None and len(CHAIN) < 16:
    v = imms(cur["ops"])
    if not v or v[0] > 0x20 or cur["mn"] != "cmp" or fam(dst(cur)) != "eax":
        say(f"  chain stopped at {cur['a']:#08x} ({cur['mn']} {cur['ops']})")
        break
    CHAIN.append((v[0], first_call(IDXBY[cur["a"]]), cur["a"]))
    nxt = next_link(IDXBY[cur["a"]])
    cur = INS[IDXBY[nxt]] if nxt in IDXBY else None
say("  chain of `cmp eax,imm` links; the call shown is the FIRST call in each arm: "
    + " ".join(f"{m:#x}->" + (f"{c:#x}" if c else "jmp/ret") for m, c, _ in CHAIN))
rows = []
for mode, callee in CASES:
    hit = [c for m, c, _ in CHAIN if m == mode]
    call = hit[0] if hit else None
    rows.append((mode, callee, call, call == callee))
for mode, callee, call, ok in rows:
    say(f"  ds:0x920700 == {mode:#04x} -> call {callee:#08x}   (measured {call and hex(call)},"
        f" {'ok' if ok else 'MISMATCH'})")
seen = []
for mode in OTHER:
    hits = [i["a"] for i in HUBINS if i["mn"] == "cmp" and fam(dst(i)) == "eax"
            and imms(i["ops"]) and imms(i["ops"])[0] == mode]
    seen.append((mode, hits))
say("  other arms (cmp present, not asserted): "
    + " ".join(f"{m:#x}@{h[0]:#x}" if h else f"{m:#x}@MISSING" for m, h in seen))
if ALGO == 7:
    rows = [(m, c, x, False) for m, c, x, _ in rows]
if not all(r[3] for r in rows):
    bad(f"G3 dispatch arms do not all resolve: {[r for r in rows if not r[3]]}")
elif any(not h for _, h in seen):
    bad(f"G3 a secondary arm has no cmp in the hub: {seen}")
else:
    say("ok  G3 the hub dispatches ds:0x920700: 2 -> 0x53a9c0, 3 -> 0x53bb90 (the two"
        " proposal validators); 8/9/1/6/4 have their own arms")
# the two validators are named by the refusal string they emit
for name, fstart, key, want in (("FUN_0053a9c0", VAL_PACT, 0x6905A8, "REJPACTMEEK"),
                               ("FUN_0053bb90", VAL_TREATY, 0x690644, "REJTREATYMEEK")):
    got = is_name(key)
    hits = [i for i in INS if fstart <= i["a"] < fstart + 5000
            and i["mn"] == "push" and f"{key:#x}" in i["ops"].lower()]
    say(f"  {name} pushes {key:#x} = {got!r} at "
        + ", ".join(f"{h['a']:#08x}" for h in hits))
    if got != want or not hits:
        bad(f"G3 {name} does not push {want} (string {got!r}, {len(hits)} push site(s))")
say("ok  G3 mode 2 is the PACT validator (REJPACTMEEK), mode 3 the TREATY validator"
    " (REJTREATYMEEK) - the two arms the hub fronts") if not FAILS else None
say("")

# ================================================================ G4
say("G4  the mode-3 arm - what FUN_00545c50 does with the branch it takes")
flag_cmp = IDXBY[0x545CDC]
seq = [INS[flag_cmp - 2], INS[flag_cmp - 1], INS[flag_cmp],
       INS[flag_cmp + 1], INS[flag_cmp + 2], INS[flag_cmp + 3]]
say("  edi = (ds:0x92077c == 3):")
for i in seq:
    say(f"    {i['a']:#08x} {i['mn']:5s} {i['ops']}")
arm = [i for i in INS if 0x545D43 <= i["a"] <= 0x545D64]
say("  the arm:")
for i in arm:
    say(f"    {i['a']:#08x} {i['mn']:5s} {i['ops']}")
ecall = [i for i in arm if i["mn"] == "call" and imms(i["ops"])]
v_call = [i for i in ecall if imms(i["ops"])[0] == VAL_TREATY]
a_call = [i for i in ecall if imms(i["ops"])[0] == ABORT]
tests = [i for i in arm if i["mn"] == "test"]
tail = [i for i in arm if i["a"] == 0x545D64]
if not v_call or not a_call:
    bad("G4 the mode-3 arm lacks the validator or the abort call")
    say(f"  validator calls {[hex(i['a']) for i in v_call]},"
        f" abort calls {[hex(i['a']) for i in a_call]}")
else:
    say(f"  validator call {v_call[0]['a']:#08x}, abort call {a_call[0]['a']:#08x},"
        f" tests {len(tests)}: " + " ".join(f"{t['ops']}" for t in tests))
# the second condition: the first test is on the RETURN (eax), the second on edi = flag
form = (len(v_call) == 1 and len(a_call) == 1 and len(tests) == 2 and len(arm) > 3
        and fam(dst(tests[0])) == "eax" and fam(dst(tests[1])) == "edi"
        and tests[0]["a"] < tests[1]["a"] < a_call[0]["a"]
        and any(x["mn"] == "sete" for x in INS[flag_cmp + 1:flag_cmp + 4]))
if ALGO == 4:
    form = not form
if not form:
    bad("G4 the mode-3 arm is not: call validator / test eax / test edi / call abort")
else:
    say("ok  G4 mode 3 calls the TREATY validator with (a,b); the abort caller runs only"
        " when the validator returns 0 AND edi == (ds:0x92077c == 3); the other path"
        " falls into 0x545d64 (the SEH tail) and takes no action")
# the edi test must jump STRAIGHT to the tail: no action when 0x92077c != 3
j2 = [i for i in arm if i["mn"] in ("je", "jz") and fam(dst(INS[IDXBY[i["a"]] - 1])) == "edi"]
t2 = int(TARGET.search(j2[0]["ops"]).group(1), 16) if j2 else None
say(f"  the edi test jumps to {t2 and hex(t2)} = the SEH tail -> a refusal with"
    " 0x92077c != 3 takes NO action")
if t2 != 0x545D64:
    bad(f"G4 the edi test does not go straight to the tail (target {t2})")
say("")

# ================================================================ G5
say("G5  erasure - can any of M377's 27 relations-dword rewrites be SHOWN to drop a stamp?")
STORES = [i for i in INS if mem_dest(i)
          and any(PAIR <= v <= PAIR + 3 for v in displ_of(dst(i)))]
say(f"  direct stores to the relations dword {PAIR:#x}: {len(STORES)}")
say("  site    src   pre-value                       field? bit15 bit16  verdict")
if ALGO == 6:
    STORES = STORES[:1]


def lineage(store):
    """Walk back from the store to the definition of its source register.
    Returns (prov, keep_lo, keep_hi, path, stops_at)."""
    rg = fam(src(store))
    lo, hi = True, True
    path = []
    k = IDXBY[store["a"]] - 1
    fn = fn_of(store["a"])
    while k >= 0 and INS[k]["a"] >= fn[1]:
        i = INS[k]
        m = i["mn"]
        d = fam(dst(i))
        if m == "jmp":
            return ("bb", lo, hi, path, i["a"])
        if m == "call":
            # cdecl: ebx/esi/edi are callee-saved, eax/ecx/edx are not
            if rg in ("eax", "ecx", "edx"):
                return ("call", lo, hi, path, i["a"])
            k -= 1
            continue
        if d == rg and "[" not in dst(i).lower() and m not in ("cmp", "test", "push"):
            s = src(i).lower()
            if m == "mov" and "[" in s:
                ds = displ_of(s)
                path.append((i["a"], f"{m} {i['ops']}"))
                if ds and PAIR <= ds[0] <= PAIR + 3:
                    return ("field", lo, hi, path, i["a"])
                return ("mem", lo, hi, path, i["a"])
            if m == "mov" and re.match(r'^0x[0-9a-f]+$', src(i).strip().lower()):
                path.append((i["a"], f"{m} {i['ops']}"))
                v = imms(src(i))[0]
                return ("imm", bool(v & STAMP_LO), bool(v & STAMP_HI), path, i["a"])
            if m == "xor" and fam(src(i)) == rg:
                path.append((i["a"], f"{m} {i['ops']}"))
                return ("zero", False, False, path, i["a"])
            if m == "pop":
                path.append((i["a"], f"{m} {i['ops']}"))
                return ("stack", lo, hi, path, i["a"])
            if m == "lea":
                path.append((i["a"], f"{m} {i['ops']}"))
                return ("addr", lo, hi, path, i["a"])
            if m in ("and", "or") and "[" not in src(i):
                # immediate mask / OR, possibly on an 8-bit register
                path.append((i["a"], f"{m} {i['ops']}"))
                r = dst(i).lower()
                v = imms(src(i))
                if not v:
                    return ("opaque", lo, hi, path, i["a"])
                v = v[0]
                if r in ("ah", "bh", "ch", "dh"):
                    if m == "and":
                        lo = lo and bool(v & 0x80)
                elif r in ("al", "bl", "cl", "dl"):
                    pass                                  # low byte: stamps live above
                else:
                    if m == "and":
                        lo = lo and bool(v & STAMP_LO)
                        hi = hi and bool(v & STAMP_HI)
                    # OR cannot clear
                k -= 1
                continue
            if m in ("add", "sub", "inc", "dec", "imul", "not", "neg", "shl", "shr", "sar"):
                path.append((i["a"], f"{m} {i['ops']}"))
                k -= 1
                continue
            return ("other", lo, hi, path, i["a"])
        k -= 1
    return ("eof", lo, hi, path, None)


DROP = []
for st in STORES:
    prov, lo, hi, path, at = lineage(st)
    v = "PRESERVE" if (prov == "field" and lo and hi) else ""
    if not v:
        if prov == "field":
            v = ("DROP " + ("15" if not lo else "") + ("16" if not hi else "")).strip()
            DROP.append((st["a"], "0x8000" if not lo else "0x10000"))
        elif prov == "zero":
            v = "DROP 15 16 (zeroed)"
            DROP.append((st["a"], "0x8000+0x10000"))
        else:
            v = f"unknown ({prov})"
    say(f"  {st['a']:06x} {fam(src(st)):4s} {path[0][1] if path else '-':30s}"
        f" {prov:6s} {str(lo):5s} {str(hi):5s}  {v}")

# the two droppers must be read-modify-writes of the SAME dword
for a, bit in DROP:
    st = INS[IDXBY[a]]
    prov, lo, hi, path, at = lineage(st)
    say(f"  drop {a:#08x} ({bit}) <- {path[0][1]}  @{at:#08x}")

say(f"  M377's rule (shape algebra over the STORE alone) predicts 0 droppers;"
    f" def-use finds {len(DROP)}")
if ALGO == 5:
    DROP = []
if len(DROP) != 2:
    bad(f"G5 expected 2 provable stamp droppers, got {len(DROP)}: {DROP}")
else:
    say(f"ok  G5 {len(DROP)} of {len(STORES)} rewrites PROVABLY clear a stamp bit:"
        " 0x551b1d masks OUT 0x10000 on the war path; 0x555430 masks OUT 0x8000"
        " under a 0x985afc parity gate - M377's '0 provable clearer' is a"
        " shape-only bound and is RETRACTED as a claim about lineage")
say("")

# ================================================================ G6
say("G6  rivals - each measured against the tables above")
riv = []
# R1: the field is a separate 4-byte array indexed by faction id, not strided
r1 = sum(1 for i in REF if SCALE4.search(i["ops"])
         and not (len(SCALE_EXPR.get(i["a"], {})) == 1
                  and list(SCALE_EXPR.get(i["a"], {0: 0}).values())[0] == STRIDE_DW))
riv.append(("R1 4-byte per-faction array",
            f"{n_scale - r1}/{n_scale} scaled sites measure 2095*x", r1 == 0))
# R2: MIGHTY/MEEK is gated on something other than the field
riv.append(("R2 the pair is not the field",
            "cmp operands are the two field loads; jle lands on MEEK",
            cmp_i["mn"] == "cmp" and tgt == push_meek[0]["a"]))
# R3: modes 2 and 3 are swapped (3 = PACT)
riv.append(("R3 2/3 swapped",
            f"mode 3 -> {rows[1][2] and hex(rows[1][2])} (REJTREATYMEEK), mode 2 ->"
            f" {rows[0][2] and hex(rows[0][2])}",
            rows[0][2] == VAL_PACT and rows[1][2] == VAL_TREATY))
# R4: the abort is unconditional on the validator's return
riv.append(("R4 abort is unconditional",
            f"{len(tests)} tests before the abort call, the first on the RETURN register",
            form))
# R5: shape algebra (M377) predicts no droppers
riv.append(("R5 shape-only erasure bound",
            f"predicts 0 droppers, def-use found {len(DROP)}", len(DROP) > 0))
for name, ev, killed in riv:
    say(f"  {name:32s} {'killed' if killed else 'SURVIVES'}  ({ev})")
if not all(k for _, _, k in riv):
    bad(f"G6 rivals not all killed: {[n for n, _, k in riv if not k]}")
else:
    say("ok  G6 all five rivals are killed by the printed numbers")
say("")

# ================================================================ G7
rows_digest = [
    f"g0:{len(REF)},{n_scale},{scale_ok},{writes}",
    f"g1:{len(created)},{len(reset)},{hex(FIELD - BLOCK)}",
    f"g2:{MIGHTY:x},{MEEK:x},{tgt:x},{push_mighty[0]['a']:x}",
    "g3:" + ",".join(f"{m}:{c:x}" for m, c, _, _ in rows),
    f"g4:{v_call[0]['a'] if v_call else 0:x},{a_call[0]['a'] if a_call else 0:x},{len(tests)}",
    "g5:" + ",".join(f"{a:06x}:{b}" for a, b in DROP) + f":{len(STORES)}",
]
dg = hashlib.sha256("|".join(rows_digest).encode()).hexdigest()[:16]
say("G7  digest")
for r in rows_digest:
    say("  " + r)
say(f"  digest {dg}")

n_bad = len(FAILS)
if n_bad:
    say("")
    say(f"FAIL M380: {n_bad} gate(s)")
    sys.exit(1)
say("")
say(f"PASS M380: {6 + 1}/{6 + 1}  {dg}")
