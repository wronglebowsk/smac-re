#!/usr/bin/env python3
"""M355 — what the two `Laptop`-derived masks at 0x58ea12 / 0x58eb2b SELECT
(M352's named OPEN: "Laptop is read and written nowhere, but its atoi feeds
masks at 0x58ea12/0x58eb2b").

PICK: run context 2026-11-24 (chain 3): "the `Laptop` pref mask semantics — the
`Laptop` key is read and written nowhere, but its `atoi` feeds masks at
0x58ea12/0x58eb2b; resolve what those masks select".

WHAT THE BYTES SAY (one line): `Laptop` is a legacy boolean whose ONLY effect is
the DEFAULT 32-bit preference bit-vector of two bit-string INI keys — `Preferences`
(cell ds:0x92befc) and `More Preferences` (cell ds:0x92bf00).  The mask is emitted
as a '1'/'0' character string (bits 31..0, leading zeros above bit 8 suppressed)
and pushed as lpDefault of the GetPrivateProfileStringA read; the same two
constants are returned by two getters (0x58e640 / 0x58e6c0) that the options
APPLY handler ORs into the two cells at 0x492464 / 0x49246f.  Laptop != 0 clears
Preferences bits {7,27,28} and More Preferences bit {19}; `Difficulty` < 2
(ds:0x92bde8, M332) additionally forces Preferences bit 5 — in the loader's INI
default ONLY, never in the getters.

GATES (tables printed FIRST, then asserted; every VERIFIED row names a mutant in
scripts/m355_mutate.py):
  G0  six function extents == ghidra_out/index.csv.
  G1  KEY + ARGUMENT attribution: image-wide exactly 4 pushes of the `Laptop`
      literal (2 VAs, both "Laptop"), 2 inside the loader FUN_0058e7f0 and 2 in
      the getters; both inline 6-push windows resolve (nearest-first) to
      app="Alpha Centauri", key=Preferences / More Preferences, default=the mask
      buffer 0x997120, out=ds:0x996a94, size=0x100, file=".\\Alpha Centauri.Ini";
      the API slot is KERNEL32!GetPrivateProfileStringA per the PE import dir.
  G2  MASK ARITHMETIC: `neg R`/`sbb R,R` -> 0/-1, `and R,imm`, `add R,imm`
      decoded from the ENCODINGS in 4 windows (loader A, loader B, getter A,
      getter B); the getters' imm pair == the loader's imm pair (agreement).
      Printed: both masks per group, set-bit lists, and the Laptop delta.
  G3  the DIFFICULTY gate exists in A only: `cmp eax,0x2` / `jge` / `or esi,0x20`
      after a load of ds:0x92bde8; B's window holds 0 references to 0x92bde8.
  G4  the EMIT loop decoded from the encodings (start bit 0x1f, suppression
      threshold 0x8, one='1' zero='0', mask reg = esi/after AND) and SIMULATED;
      the emitted strings re-parse to the masks under the image's own binary
      parser 0x628720 (`v = v*2 + (c-'0')`, '0'/'1' only — decoded from bytes).
  G5  CONSUMER: getter A 5 call sites, getter B 5 call sites, all in
      0x493b0b..0x493b79, stored in a decoded order to +0xa30..+0xa58; the APPLY
      handler's OR dataflow (simulated) puts the A-field +0xa30 into ds:0x92befc
      and the B-field +0xa34 into ds:0x92bf00.
  G6  RIVALS, each measured and each FAILING on the printed numbers.
"""
import bisect
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
IDXCSV = os.path.join(ROOT, "ghidra_out/index.csv")
EXE = os.path.join(ROOT, "programs/terran.exe")
if not os.path.exists(EXE):
    EXE = os.path.join(ROOT, "terran.exe")

LOADER = 0x58E7F0
GETTER_A = 0x58E640          # returns the Preferences default mask
GETTER_B = 0x58E6C0          # returns the More Preferences default mask
GETTER_C = 0x58E740          # returns 0x3c3a9 (a third group's default)
GETTER_D = 0x58E750          # returns 0x1a0e (Semaphore's default)
APPLY = 0x4923D0             # options APPLY handler (M350's APPLY site 0x492464)
PARSER = 0x628720            # binary string -> dword
IAT_R = 0x671100             # KERNEL32!GetPrivateProfileStringA
BUF = 0x997120               # the shared 0x100-byte default/build buffer
OUT = 0x996A94               # the out-buffer pointer cell (ds:0x996a94)
CELL_PREF, CELL_MORE = 0x92BEFC, 0x92BF00
DIFF = 0x92BDE8              # `Difficulty` master (M332)

# windows (byte-bounded, inclusive)
WIN = {
    "loaderA": (0x58E9F3, 0x58EA67),
    "loaderB": (0x58EB0C, 0x58EB7E),
    "getterA": (0x58E640, 0x58E6B8),
    "getterB": (0x58E6C0, 0x58E738),
    "emitA": (0x58EA26, 0x58EA67),
    "emitB": (0x58EB3E, 0x58EB7E),
    "applyOR": (0x4923E6, 0x492474),
}
API_CALLS = [0x58E9D3, 0x58EAF7, 0x58EBBE, 0x58EC0D]   # GetPrivateProfileStringA sites
TIER = 0x8                   # the `cmp ecx,0x8` suppression threshold
START = 0x1F

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")


def insns():
    patch = os.environ.get("M355_PATCH")
    pa = pt = None
    if patch:
        paddr, _, pt = patch.partition("|")
        pa = int(paddr.strip(), 16)
    out, hit = [], False
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line)
            if not m:
                continue
            a = int(m.group(1), 16)
            txt = m.group(3).strip()
            if a == pa:
                if txt == pt:
                    sys.stderr.write("M355_PATCH already equal at %s\n" % patch)
                    raise SystemExit(3)
                txt, hit = pt, True
            mo = OPS.match(txt)
            out.append({"a": a, "by": m.group(2).split(), "t": txt,
                        "op": mo.group(1) if mo else txt.split()[0],
                        "arg": mo.group(2) if mo else ""})
    if patch and not hit:
        sys.stderr.write("M355_PATCH %s not in .text cache\n" % patch)
        raise SystemExit(2)
    return out


INS = insns()
ADDRS = [i["a"] for i in INS]
POS = {a: n for n, a in enumerate(ADDRS)}


def load_index():
    rows, head = [], None
    for line in open(IDXCSV):
        if head is None:
            head = line.strip().split(",")
            continue
        if not line.strip() or line.startswith("#"):
            continue
        d = dict(zip(head, line.strip().split(",")))
        try:
            rows.append((int(d["addr"], 16), d["name"], int(d["size_bytes"])))
        except ValueError:
            pass
    rows.sort()
    return rows


ROWS = load_index()
STARTS = [r[0] for r in ROWS]


def fnof(a):
    i = bisect.bisect_right(STARTS, a) - 1
    if i < 0:
        return ("?", 0, 0)
    return ROWS[i][1], ROWS[i][0], ROWS[i][2]


def body(lo_va):
    nm, s, z = fnof(lo_va)
    return [i for i in INS if s <= i["a"] < s + z], nm, s, z


def win(lo_hi):
    lo, hi = lo_hi
    return [i for i in INS if lo <= i["a"] <= hi]


PE = open(EXE, "rb").read()
pe = struct.unpack_from("<I", PE, 0x3C)[0]
OPT = pe + 24
BASE = struct.unpack_from("<I", PE, OPT + 28)[0]
SECS = []
_hp = OPT + struct.unpack_from("<H", PE, pe + 20)[0]
for _i in range(struct.unpack_from("<H", PE, pe + 6)[0]):
    _nm = PE[_hp:_hp + 8].rstrip(b"\0").decode("latin1")
    _vs, _va, _rs, _ra = struct.unpack_from("<IIII", PE, _hp + 8)
    _ch = struct.unpack_from("<I", PE, _hp + 36)[0]
    SECS.append((_nm, BASE + _va, _vs, _ra, _rs, _ch))
    _hp += 40


def va2off(va):
    for n, v, vs, ra, rs, ch in SECS:
        # bound by the RAW size: .data's virtual extent (0x316284) runs past
        # its file image (0x20000), and the tail is BSS (0x996a94/0x997120 live there).
        if v <= va < v + rs:
            return ra + (va - v)
    return None


def cstr(va):
    o = va2off(va)
    if o is None:
        return None
    e = PE.find(b"\0", o, o + 64)
    if e < 0:
        return None
    b = PE[o:e]
    if not b or len(b) > 40 or any(not (32 <= c < 127) for c in b):
        return None
    return b.decode("ascii")


def dword(va):
    o = va2off(va)
    if o is None:
        return None
    return struct.unpack_from("<I", PE, o)[0]


def imports():
    rva, _sz = struct.unpack_from("<II", PE, OPT + 96 + 8)
    o = va2off(BASE + rva)
    out = {}
    while True:
        oft, ts, fc, nr, ft = struct.unpack_from("<IIIII", PE, o)
        if nr == 0:
            break
        no = va2off(BASE + nr)
        dll = PE[no:PE.index(b"\0", no)].decode()
        t = va2off(BASE + (oft or ft))
        k = 0
        while True:
            th = struct.unpack_from("<I", PE, t + 4 * k)[0]
            if th == 0:
                break
            if th & 0x80000000:
                nm = "ord#%d" % (th & 0xFFFF)
            else:
                ao = va2off(BASE + (th & 0x7FFFFFFF))
                nm = PE[ao + 2:PE.index(b"\0", ao + 2)].decode()
            out[BASE + ft + 4 * k] = (dll, nm)
            k += 1
        o += 20
    return out


IMPORTS = imports()
TABLES = []
FAILED = []


def row(*cols):
    line = " | ".join(str(c) for c in cols)
    TABLES.append(line)
    print(line)


def chk(gate, ok, msg):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", gate, msg))
    if not ok:
        FAILED.append(gate)


# ---------------- decode helpers ----------------
def pushes_before(idx, n):
    got = []
    i = idx - 1
    while i >= 0 and len(got) < n and idx - i <= 16:
        if INS[i]["op"] == "push":
            got.append((INS[i]["a"], INS[i]["arg"].strip()))
        i -= 1
    return got


def reg_source(reg, idx, span=10):
    i = idx - 1
    seen = 0
    while i >= 0 and seen < span:
        op, arg = INS[i]["op"], INS[i]["arg"]
        dst = arg.split(",")[0].strip()
        if op in ("mov", "lea", "xor", "add", "sub", "or", "and") and dst == reg:
            src = arg.split(",", 1)[1].strip() if "," in arg else ""
            m = re.fullmatch(r"0x([0-9a-f]+)", src)
            if m:
                return ("imm", int(m.group(1), 16))
            m = re.search(r"ds:0x([0-9a-f]+)", src)
            if m:
                return ("global", int(m.group(1), 16))
            return ("unknown", INS[i]["t"])
        i -= 1
        seen += 1
    return ("unknown", "no write")


def push_value(p):
    a, arg = p
    m = re.fullmatch(r"0x([0-9a-f]+)", arg)
    if m:
        return ("imm", int(m.group(1), 16))
    if re.fullmatch(r"[a-z]{3}", arg):
        return reg_source(arg, POS[a])
    return ("unknown", arg)


def mask_arith(window, algo=""):
    """Decode neg/sbb/and/add in a window; return (and_imm, add_imm, reg)."""
    neg = sbb = and_i = add_i = None
    reg = None
    for ins in window:
        op, arg = ins["op"], ins["arg"]
        if op == "neg":
            reg = arg.strip()
            neg = ins
        elif op == "sbb" and not sbb:
            sbb = ins
        elif op == "and" and reg and arg.split(",")[0].strip() == reg and not and_i:
            m = re.fullmatch(r"0x([0-9a-f]+)", arg.split(",", 1)[1].strip())
            if m:
                and_i = int(m.group(1), 16)
                if algo == "4":
                    and_i = 0xFFFFFFFF
        elif op == "add" and reg and arg.split(",")[0].strip() == reg and not add_i:
            m = re.fullmatch(r"0x([0-9a-f]+)", arg.split(",", 1)[1].strip())
            if m:
                add_i = int(m.group(1), 16)
    return and_i, add_i, reg, (neg is not None and sbb is not None)


def masks(and_i, add_i):
    m_nz = (and_i + add_i) & 0xFFFFFFFF
    m_zero = add_i & 0xFFFFFFFF
    return m_zero, m_nz          # (Laptop==0, Laptop!=0)


def bits(x):
    return [i for i in range(32) if (x >> i) & 1]


def emit(m, start=START, tier=TIER, one="1", zero="0", algo=""):
    if algo == "2":          # ALGO 2: the start bit misread from the cmp immediate
        start = tier
    out, started = [], False
    order = range(start, -1, -1) if algo != "1" else range(0, start + 1)
    for i in order:
        if (m >> i) & 1:
            started = True
            out.append(one)
        else:
            if not started and i >= tier:
                continue
            out.append(zero)
    return "".join(out)


def parse_bin(s):
    v = 0
    for ch in s:
        if ch in ("0", "1"):
            v = (v << 1) + (ord(ch) - 0x30)
        else:
            break
    return v & 0xFFFFFFFF


# =============================== G0 ===============================
print("== M355  Laptop -> the Preferences / More Preferences default bit-vectors ==")
SIG = {LOADER: 2066, GETTER_A: 149, GETTER_B: 149, APPLY: 0, PARSER: 0}
ext = {}
orow = ["func", "start", "size", "name"]
row(*orow)
for f in (LOADER, GETTER_A, GETTER_B, GETTER_C, GETTER_D, APPLY, PARSER):
    nm, s, z = fnof(f)
    ext[f] = (nm, s, z)
    row(hex(f), hex(s), z, nm)
chk("G0", all(ext[f][0] != "?" and ext[f][1] == f for f in ext),
    "all 7 entry addresses are function starts in ghidra_out/index.csv")

# =============================== G1 ===============================
print("\n-- G1  key literals and argument attribution --")
lap = []
for ins in INS:
    if ins["op"] == "push":
        m = re.fullmatch(r"0x([0-9a-f]+)", ins["arg"].strip())
        if m and cstr(int(m.group(1), 16)) == "Laptop":
            lap.append((ins["a"], int(m.group(1), 16)))
row("Laptop push sites", len(lap), " ".join(hex(a) for a, _ in lap), "VAs",
    sorted({hex(v) for _, v in lap}))
row("literals", "0x6926fc=" + str(cstr(0x6926FC)), "0x692704=" + str(cstr(0x692704)))
in_loader = [a for a, _ in lap if ext[LOADER][1] <= a < ext[LOADER][1] + ext[LOADER][2]]
in_get = [a for a, _ in lap if a < ext[LOADER][1]]


def in_fn(a, f):
    nm, st, z = ext[f]
    return st <= a < st + z


hitA = [a for a in in_get if in_fn(a, GETTER_A)]
hitB = [a for a in in_get if in_fn(a, GETTER_B)]
row("Laptop sites in loader", len(in_loader), " ".join(hex(a) for a in in_loader))
row("Laptop sites in GETTER_A / GETTER_B", len(hitA), [hex(x) for x in hitA],
    len(hitB), [hex(x) for x in hitB])
chk("G1a", len(lap) == 4 and len(in_loader) == 2 and len(in_get) == 2 and
    len(hitA) == 1 and len(hitB) == 1 and len(hitA) + len(hitB) == len(in_get) and
    {v for _, v in lap} == {0x6926FC, 0x692704},
    "image-wide `Laptop` literal pushes = 4: 2 in FUN_0058e7f0 and 1 inside EACH of "
    "FUN_0058e640 / FUN_0058e6c0 (no other function pushes it); 2 VAs, both 'Laptop'")

ROLES = ["app", "key", "default", "out", "size", "file"]
ALGO = os.environ.get("M355_ALGO", "")
KEYS = {0x58E9D3: "Faction", 0x58EAF7: "Preferences", 0x58EBBE: "Prefs Format",
        0x58EC0D: "More Preferences"}
row("api site", *ROLES)
keys_ok = True
for site in API_CALLS:
    ps = pushes_before(POS[site], 6)
    vals = [push_value(p) for p in ps]          # nearest-first
    roles = ROLES[1:] + ROLES[:1] if ALGO == "3" else ROLES
    disp = []
    for role, (kind, v) in zip(roles, vals):
        if kind == "imm":
            s = cstr(v)
            disp.append("%s=0x%x%s" % (role, v, "('" + s + "')" if s else ""))
        elif kind == "global":
            ptr = dword(v)
            s = cstr(ptr) if ptr else None
            disp.append("%s=ds:0x%x%s" % (role, v, "->'" + s + "'" if s else ""))
        else:
            disp.append("%s=?%s" % (role, v))
            keys_ok = False
    row(hex(site), *disp)
    by = {r: vals[n] for n, r in enumerate(roles)}
    ki = roles.index("key")
    kname = cstr(vals[ki][1]) if vals[ki][0] == "imm" else None
    if kname != KEYS[site]:
        keys_ok = False
        row("  !! key mismatch", site, kname, KEYS[site])

    def gstr(role):
        k, v = by[role]
        return cstr(dword(v)) if k == "global" and dword(v) else None

    app_s, file_s = gstr("app"), gstr("file")
    role_ok = (by["out"] == ("global", OUT) and by["size"] == ("imm", 0x100)
               and app_s == "Alpha Centauri"
               and file_s == ".\\Alpha Centauri.Ini"
               and by["default"] == (("imm", 0x6926E8) if site == 0x58EBBE
                                     else ("imm", BUF)))
    row("  roles", "app", app_s, "file", file_s, "out", by["out"], "size", by["size"],
        "default", by["default"], "OK" if role_ok else "MISMATCH")
    if not role_ok:
        keys_ok = False
chk("G1b", keys_ok, "4 API sites' nearest-first 6-push windows resolve app/file/key/default/out/size; "
    "the key arg of 0x58eaf7='Preferences' and of 0x58ec0d='More Preferences'")

iap = IMPORTS.get(IAT_R)
row("IAT 0x671100", iap)
chk("G1c", iap is not None and iap[1] == "GetPrivateProfileStringA",
    "the api slot is KERNEL32!GetPrivateProfileStringA (PE import directory)")

# default arg of the getters = the cleared build buffer -> absent == "0"
gA, gB = [i for i in INS if ext[GETTER_A][1] <= i["a"] < ext[GETTER_A][1] + ext[GETTER_A][2]], \
         [i for i in INS if ext[GETTER_B][1] <= i["a"] < ext[GETTER_B][1] + ext[GETTER_B][2]]
new_default = []
for g in (gA, gB):
    for n, i in enumerate(g):
        if i["op"] != "call":
            continue
        a = g[n]["a"]
        tgt = i["arg"].strip()
        is_api = "0x671100" in tgt
        if not is_api and re.fullmatch(r"(edi|esi)", tgt):
            is_api = reg_source(tgt, POS[a]) == ("global", IAT_R)
        if not is_api:
            continue
        ps = pushes_before(POS[a], 6)
        vals = [push_value(p) for p in ps]
        zero = [i["a"] for i in g if i["op"] == "mov"
                and i["arg"].startswith("BYTE PTR ds:0x997120,0x0")]
        before = [z for z in zero if z < a]
        new_default.append((hex(a), [d[1] for d in vals],
                            bool(before), before[-1] if before else None))
row("getter default arg", [(a, hex(v[2]) if isinstance(v[2], int) else v[2], z,
                            hex(y) if y else "-")
                           for a, v, z, y in new_default])
chk("G1d", len(new_default) == 2 and all(v[2] == 0x997120 and z
                                         for a, v, z, y in new_default),
    "both getters push the zeroed buffer 0x997120 as lpDefault AND zero it "
    "(`mov BYTE PTR ds:0x997120,0x0`) at an address BEFORE the call, so an ABSENT key and "
    "an explicit 0 take the same path")

# =============================== G2 ===============================
print("\n-- G2  mask arithmetic from the encodings --")
algo = ALGO
M = {}
row("window", "neg", "sbb", "and imm", "add imm", "reg", "Laptop=0", "Laptop!=0")
for name in ("loaderA", "loaderB", "getterA", "getterB"):
    and_i, add_i, reg, ok = mask_arith(win(WIN[name]), algo)
    m0, m1 = masks(and_i or 0, add_i or 0)
    M[name] = (m0, m1, and_i, add_i, reg, ok)
    row(name, ok and "-1/0", "-1/0", hex(and_i or 0), hex(add_i or 0), reg,
        hex(m0), hex(m1))
chk("G2a", all(v[5] and v[2] and v[3] for v in M.values()),
    "all 4 windows carry the neg/sbb(-1/0) + and + add idiom with explicit immediates")
chk("G2b", M["loaderA"][2:4] == M["getterA"][2:4] and M["loaderB"][2:4] == M["getterB"][2:4],
    "getter A/B immediates == loader A/B immediates (the two sides compute the SAME mask)")

# ---- G2e: the CAUSAL link read -> atoi -> neg/sbb -> and/add -> (loader) test ----
def read_to_mask(name):
    ws = win(WIN[name])
    reg = M[name][4]
    if name.startswith("loader"):
        reads = [i["a"] for i in ws if i["op"] == "call" and i["arg"].strip() == "0x58e760"]
        if not reads:
            return ("no read call", None)
        a = reads[0]
        nxt = INS[POS[a] + 1]
        m = re.fullmatch(r"([a-z]{3}),eax", nxt["arg"])
        link = ("mov %s,eax" % reg) if (m and m.group(1) == reg) else None
        return (link, a)
    atois = [i["a"] for i in ws if i["op"] == "call" and i["arg"].strip() == "0x64c460"]
    if not atois:
        return ("no atoi", None)
    a = atois[0]
    for k in (1, 2, 3):
        nxt = INS[POS[a] + k]
        if nxt["op"] == "neg":
            return (nxt["arg"].strip() if nxt["arg"].strip() == reg else None, a)
    return (None, a)

causal = {n: read_to_mask(n) for n in M}
row("causal link", {k: v[0] for k, v in causal.items()})
# the register the emit loop tests must be the mask register
test_reg = {}
for nm, w in (("loaderA", "emitA"), ("loaderB", "emitB")):
    t = [i["arg"] for i in win(WIN[w]) if i["op"] == "test"]
    test_reg[nm] = t[0].split(",")[0].strip() if t else None
row("emit test register", test_reg)
chk("G2e", causal["loaderA"][0] == "mov esi,eax" and causal["getterA"][0] == "eax" and
    causal["getterB"][0] == "eax" and test_reg["loaderA"] == M["loaderA"][4] and
    test_reg["loaderB"] == M["loaderB"][4],
    "each window's `neg`/`sbb`/`and`/`add` register IS the register that received the "
    "`Laptop` read's atoi result (loader: `mov esi,eax` after call 0x58e760; getters: "
    "`neg eax` right after call 0x64c460) and it is the register the emit loop tests")

A0, A1 = M["loaderA"][0], M["loaderA"][1]
B0, B1 = M["loaderB"][0], M["loaderB"][1]
row("Preferences  Laptop=0 ", hex(A0), "bits", bits(A0), "n=%d" % len(bits(A0)))
row("Preferences  Laptop!=0", hex(A1), "bits", bits(A1), "n=%d" % len(bits(A1)))
row("MorePrefs    Laptop=0 ", hex(B0), "bits", bits(B0), "n=%d" % len(bits(B0)))
row("MorePrefs    Laptop!=0", hex(B1), "bits", bits(B1), "n=%d" % len(bits(B1)))
row("delta Preferences", hex(A0 ^ A1), "bits", bits(A0 ^ A1), "cleared", bits(A0 & ~A1))
row("delta MorePrefs", hex(B0 ^ B1), "bits", bits(B0 ^ B1), "cleared", bits(B0 & ~B1))
chk("G2c", (A0, A1, B0, B1) == (0xBBE1DD96, 0xA3E1DD16, 0x3A7168, 0x327168),
    "the four masks are 0xbbe1dd96 / 0xa3e1dd16 (Preferences) and 0x3a7168 / 0x327168 (More Preferences)")
chk("G2d", (A0 & ~A1) == (1 << 7) | (1 << 27) | (1 << 28) and (B0 & ~B1) == (1 << 19),
    "Laptop!=0 CLEARS bits {7,27,28} of Preferences and {19} of More Preferences (nothing is added)")

# =============================== G3 ===============================
print("\n-- G3  the Difficulty gate (Preferences block only) --")
wa, wb = win(WIN["loaderA"]), win(WIN["loaderB"])
def gate_scan(ws):
    d = "0x%x" % DIFF
    out = {"load": [i["a"] for i in ws if d in i["arg"]],
           "cmp": [(i["a"], i["arg"]) for i in ws if i["op"] == "cmp" and d in str(i["arg"])],
           "cmp_imm": [(i["a"], i["arg"]) for i in ws
                       if i["op"] == "cmp" and re.fullmatch(r"eax,0x[0-9a-f]+", i["arg"])],
           "jcc": [(i["a"], i["t"]) for i in ws if i["op"].startswith("j")],
           "orimm": [(i["a"], i["arg"]) for i in ws if i["op"] == "or" and i["arg"].startswith("esi,")]}
    return out
ga, gb = gate_scan(wa), gate_scan(wb)
row("loaderA gate", ga)
row("loaderB gate", gb)
or_bit = None
if ga["orimm"]:
    or_bit = int(ga["orimm"][0][1].split(",")[1], 16)
row("gate bit", hex(or_bit or 0), "bit", bits(or_bit or 0))
gate_cmp = int(ga["cmp_imm"][0][1].split(",")[1], 16) if ga["cmp_imm"] else None
row("gate threshold", hex(gate_cmp) if gate_cmp is not None else "none")
# control flow: the jcc must sit between the cmp and the `or`, and jump PAST the or
geo = None
if ga["cmp_imm"] and ga["orimm"] and ga["jcc"]:
    ca = ga["cmp_imm"][0][0]
    oa = ga["orimm"][0][0]
    jc = [x for x in ga["jcc"] if x[0] > ca]
    if jc:
        ja, jt = jc[0]
        m = re.search(r"0x([0-9a-f]+)", jt)
        tgt = int(m.group(1), 16) if m else None
        geo = (ca < ja < oa and tgt is not None and oa < tgt and not jt.startswith("jmp"))
        row("gate geometry", "cmp", hex(ca), "jcc", hex(ja), jt, "or", hex(oa),
            "guarded" if geo else "NOT guarded")
chk("G3a", ga["load"] and gate_cmp == 0x2 and ga["jcc"] and bool(geo) and
    (or_bit is not None and bits(or_bit) == [5]),
    "A: a load of ds:0x92bde8 -> `cmp eax,0x2` -> a CONDITIONAL jcc that jumps PAST the "
    "`or esi,0x20` (bit 5), i.e. the or runs only on the fall-through (Difficulty<2)")
chk("G3b", len(gb["load"]) == 0 and not gb["orimm"],
    "B (More Preferences) holds 0 references to ds:0x92bde8 and no OR immediate: no difficulty gate")
A0g, A1g = A0 | 0x20, A1 | 0x20
row("Preferences default with Difficulty<2", hex(A0g), hex(A1g), "bits",
    bits(A0g), bits(A1g))

# =============================== G4 ===============================
print("\n-- G4  the emit loop and the round-trip through the image's parser --")
ea, eb = win(WIN["emitA"]), win(WIN["emitB"])
def emit_decode(ws):
    start = tier = None
    one = zero = None
    shift = testreg = None
    for i in ws:
        if i["op"] == "mov" and re.fullmatch(r"(ecx|ebx),0x[0-9a-f]+", i["arg"]):
            v = int(i["arg"].split(",")[1], 16)
            if v == 0x1F:
                start = v
        if i["op"] == "cmp" and re.fullmatch(r"(ecx|ebx),0x[0-9a-f]+", i["arg"]):
            tier = int(i["arg"].split(",")[1], 16)
        if i["op"] == "push":
            m = re.fullmatch(r"0x([0-9a-f]+)", i["arg"].strip())
            if m:
                s = cstr(int(m.group(1), 16))
                if s == "1" and one is None:
                    one = s
                elif s == "0" and zero is None:
                    zero = s
        if i["op"] == "shl":
            shift = i["arg"]
        if i["op"] == "test":
            testreg = i["arg"]
    return start, tier, one, zero, shift, testreg
def loop_law(ws, maskreg):
    """The loop must: shift a 1 by the COUNTER (cl), test the MASK reg, dec the counter,
    and jump back (jns) to the loop head -- i.e. walk bits start..0, not 0..start."""
    shl = [i for i in ws if i["op"] == "shl"]
    test = [i for i in ws if i["op"] == "test"]
    dec = [i for i in ws if i["op"] == "dec"]
    jns = [i for i in ws if i["op"] == "jns"]
    out = {"shl": shl[0]["arg"] if shl else None,
           "test": test[0]["arg"] if test else None,
           "dec": dec[0]["arg"] if dec else None,
           "jns": jns[0]["t"] if jns else None}
    out["ok"] = bool(shl and test and dec and jns) and \
        re.fullmatch(r"edx,cl", out["shl"] or "") is not None and \
        (out["test"] or "").split(",")[0].strip() == maskreg and \
        (out["dec"] or "").strip() in ("ecx", "ebx") and \
        re.search(r"0x([0-9a-f]+)", out["jns"] or "") is not None
    if out["ok"]:
        tgt = int(re.search(r"0x([0-9a-f]+)", out["jns"]).group(1), 16)
        head = min(i["a"] for i in ws if i["op"] in ("shl", "test"))
        out["head"] = hex(head)
        out["ok"] = tgt <= head
    return out
da, db = emit_decode(ea), emit_decode(eb)
la, lb = loop_law(ea, M["loaderA"][4]), loop_law(eb, M["loaderB"][4])
row("emitA decode", da, la)
row("emitB decode", db, lb)
chk("G4a", da[:4] == (0x1F, 0x8, "1", "0") and db[:4] == (0x1F, 0x8, "1", "0") and
    da[4] and db[4] and la["ok"] and lb["ok"],
    "both loops: start bit 0x1f, suppression `cmp <counter>,0x8`, chars '1'/'0', `shl edx,cl` "
    "off the COUNTER, `test <mask>,edx` on the mask register, `dec <counter>` + backward `jns` "
    "to the head = a downward walk over bits 31..0")

# parser 0x628720 decoded from BYTES (ALGO 6 reads the base-16 sibling 0x62876b instead:
# the classifier law itself is the thing under test)
PARSER_VA = 0x62876B if algo == "6" else PARSER
po = va2off(PARSER_VA)
pb = PE[po:po + 0x60]
row("parser bytes head", hex(PARSER_VA), pb[:24].hex(" "))
p_cmp30 = b"\x83\xf9\x30" in pb
p_cmp31 = b"\x83\xf8\x31" in pb
p_shl1 = b"\xd1\xe1" in pb
p_lea = b"\x8d\x54\x01\xd0" in pb
row("parser law", "cmp 0x30", p_cmp30, "cmp 0x31", p_cmp31, "shl 1", p_shl1, "lea +c-0x30", p_lea)
chk("G4b", p_cmp30 and p_cmp31 and p_shl1 and p_lea,
    "0x628720 accepts ONLY '0'/'1' and accumulates v=v*2+(c-0x30) (decoded from bytes)")

row("group", "mask", "emitted default string", "len", "re-parse", "match")
emit_ok = True
for name, m in (("Pref0", A0), ("Pref1", A1), ("More0", B0), ("More1", B1),
                ("Semaphore", 0x1A0E), ("group@0x3c3a9", 0x3C3A9)):
    s = emit(m, algo=algo)
    rp = parse_bin(s)
    emit_ok = emit_ok and rp == m
    row(name, hex(m), s, len(s), hex(rp), "OK" if rp == m else "MISMATCH")
chk("G4c", emit_ok, "every emitted default string re-parses to its mask under 0x628720's law (6/6)")

# =============================== G5 ===============================
print("\n-- G5  consumer: the options dialog fields and the APPLY OR --")
CALLERS = {GETTER_A: [], GETTER_B: [], GETTER_C: []}
for n, i in enumerate(INS):
    if i["op"] == "call":
        m = re.fullmatch(r"0x([0-9a-f]+)", i["arg"].strip())
        if m and int(m.group(1), 16) in CALLERS:
            CALLERS[int(m.group(1), 16)].append(i["a"])
row("getter", "call sites", "dispatch")
disp_rows = []
for n, i in enumerate(INS):
    for g in CALLERS:
        if i["a"] in CALLERS[g]:
            for k in (range(1, 6) if ALGO != "5" else ()):
                nxt = INS[POS[i["a"]] + k]
                if nxt["op"] == "mov" and re.fullmatch(
                        r"DWORD PTR \[esi\+0x[0-9a-f]+\],eax", nxt["arg"]):
                    disp_rows.append((i["a"], g, nxt["op"], nxt["arg"], k))
                    break
            else:
                disp_rows.append((i["a"], g, "NO-STORE", "", 0))
for a, g, op, arg, k in disp_rows:
    row(hex(a), "->0x%x" % g, "+%d" % k, op, arg)
sets_ok = (len(CALLERS[GETTER_A]) == 5 and len(CALLERS[GETTER_B]) == 5 and
           all(0x493B0B <= a <= 0x493B79 for a in CALLERS[GETTER_A] + CALLERS[GETTER_B] +
               [x[0] for x in disp_rows]))
chk("G5a", sets_ok, "getter A 5 sites, getter B 5 sites, ALL 11 dispatches inside 0x493b0b..0x493b79")
FIELD = {}
ORDER = []
for a, g, op, arg, k in disp_rows:
    m = re.search(r"\[esi\+0x([0-9a-f]+)\]", arg)
    if m and op == "mov":
        FIELD[int(m.group(1), 16)] = g
        ORDER.append((int(m.group(1), 16), g))
row("field map", {hex(k): hex(v) for k, v in sorted(FIELD.items())})
# DECLARED order (measured once, then asserted in both directions)
DECL = [(0xA30, GETTER_A), (0xA34, GETTER_B), (0xA38, GETTER_A), (0xA3C, GETTER_B),
        (0xA40, GETTER_A), (0xA44, GETTER_B), (0xA4C, GETTER_A), (0xA50, GETTER_B),
        (0xA48, GETTER_C), (0xA54, GETTER_A), (0xA58, GETTER_B)]
row("store order measured", [(hex(a), hex(g)) for a, g in ORDER])
row("store order declared", [(hex(a), hex(g)) for a, g in DECL])
chk("G5b", ORDER == DECL and len(FIELD) == 11 and
    sorted(ORDER) == sorted(DECL),
    "all 11 dispatch sites match the declared order both ways: +0xa30/+0xa38/+0xa40/+0xa4c/+0xa54 <- "
    "getterA, +0xa34/+0xa3c/+0xa44/+0xa50/+0xa58 <- getterB, +0xa48 <- getterC (0x3c3a9)")

# OR dataflow over the APPLY window: registers + [esi+disp] cells (accumulators)
regs = {r: frozenset() for r in ("eax", "ebx", "ecx", "edx", "esi", "edi")}
fields = {}
final = {}
final_site = {}
for i in win(WIN["applyOR"]):
    a = i["a"]
    op, arg = i["op"], i["arg"]
    if op == "mov" and "," in arg:
        dst, src = [x.strip() for x in arg.split(",", 1)]
        ml = re.fullmatch(r"dword ptr \[esi\+0x([0-9a-f]+)\]", src.lower())
        ms = re.fullmatch(r"dword ptr \[esi\+0x([0-9a-f]+)\]", dst.lower())
        if ms and src in regs:                      # store: reg -> cell
            fields[int(ms.group(1), 16)] = regs[src]
        elif dst in regs and ml:                    # load: cell -> reg
            d = int(ml.group(1), 16)
            regs[dst] = fields.get(d, frozenset({d}))
        elif dst.startswith("ds:0x"):
            final[int(dst[5:], 16)] = regs.get(src, frozenset())
            final_site[int(dst[5:], 16)] = a
        elif dst in regs:
            regs[dst] = regs.get(src, frozenset()) if src in regs else frozenset()
    elif op == "or" and "," in arg:
        dst, src = [x.strip() for x in arg.split(",", 1)]
        if dst in regs:
            regs[dst] = regs[dst] | regs.get(src, frozenset())
row("APPLY final stores", {hex(k): (sorted(hex(x) for x in v), "@" + hex(final_site[k]))
                           for k, v in final.items()})
P = final.get(CELL_PREF, frozenset())
Q = final.get(CELL_MORE, frozenset())
row("Preferences  <-", hex(CELL_PREF), sorted(hex(x) for x in P))
row("MorePrefs    <-", hex(CELL_MORE), sorted(hex(x) for x in Q))
chk("G5c", bool(P) and bool(Q) and 0xA30 in P and 0xA34 in Q and
    0xA30 not in Q and 0xA34 not in P and
    final_site.get(CELL_PREF) == 0x492464 and final_site.get(CELL_MORE) == 0x49246F,
    "APPLY: the store at 0x492464 writes ds:0x92befc from an OR incl. the getter-A field "
    "+0xa30 and the store at 0x49246f writes ds:0x92bf00 from an OR incl. the getter-B field "
    "+0xa34 (disjoint sets; the OR chain is measured by dataflow, not by name)")

# =============================== G6 ===============================
print("\n-- G6  rivals (each must FAIL on the printed numbers) --")
RIV = []
RIV.append(("R1 Laptop only toggles the difficulty bit 0x20",
            (A0 ^ A1) == 0x20 and (B0 ^ B1) == 0x20, hex(A0 ^ A1) + " / " + hex(B0 ^ B1)))
RIV.append(("R2 one Laptop delta serves both groups",
            (A0 ^ A1) == (B0 ^ B1), hex(A0 ^ A1) + " vs " + hex(B0 ^ B1)))
RIV.append(("R3 Laptop!=0 is a superset (adds options)",
            (A1 & ~A0) != 0 and (B1 & ~B0) != 0,
            "added P=%s added M=%s" % (bits(A1 & ~A0), bits(B1 & ~B0))))
RIV.append(("R4 the default string is a fixed 32 chars",
            len(emit(A0)) == len(emit(B0)) == 32,
            "lens %d / %d" % (len(emit(A0)), len(emit(B0)))))
RIV.append(("R5 the getters apply the same Difficulty gate",
            (M["getterA"][0] | 0x20) == M["getterA"][0] and 0x20 in bits(M["getterA"][0]),
            "getterA=%s gate bit present=%s" % (hex(M["getterA"][0]), 0x20 in bits(M["getterA"][0]))))
RIV.append(("R6 Laptop is read once and forwarded",
            len(lap) == 1, "read sites %d" % len(lap)))
RIV.append(("R7 the emitted string is the value stored to the cell as text",
            parse_bin(emit(A0)) != A0, "re-parse %s == mask %s" % (hex(parse_bin(emit(A0))), hex(A0))))
for name, holds, num in RIV:
    print("%-52s holds=%-5s  %s" % (name, holds, num))
chk("G6", not any(h for _, h, _ in RIV), "7/7 rivals FALSIFIED by the printed numbers")

dig = hashlib.sha1("\n".join(TABLES).encode()).hexdigest()
print("\ntables digest %s  (%d rows)" % (dig[:16], len(TABLES)))
print("%s M355: %d/7 gates" % ("PASS" if not FAILED else "FAIL", 7 - len(set(FAILED))))
if FAILED:
    print("failed: %s" % sorted(set(FAILED)))
sys.exit(0 if not FAILED else 1)
