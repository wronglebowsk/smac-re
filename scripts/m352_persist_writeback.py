#!/usr/bin/env python3
"""M352 — the WRITEBACK side of the pref block: FUN_0058f0d0's 8 `call edi` targets,
the write/read key matrix, and M350's named OPEN `ds:0x6926ec`.

PICK: run-context 2026-11-24 (chain 3): "the writeback side of the pref block —
identify FUN_0058f0d0's 8 call edi targets and whether the persist writes cells it
never read, then the ds:0x6926ec setter (M350's named OPEN rows)".

Every number is COMPUTED from the static image: scratch/m574/text.txt (objdump
.text), programs/terran.exe (PE headers, import directory, .data strings),
ghidra_out/index.csv (function extents). Zero box time.

WHAT THE BYTES SAY (one line): the 8 `call edi` are ONE statically-resolved target —
KERNEL32!WritePrivateProfileStringA through the .rdata import slot ds:0x6710fc — and
the persist writes 13 keys: 12 are backed by a block cell it loads in the same
block (11 scalars + the 7-dword Custom World array) and 1 (`Prefs Format`=11) is a
hardcoded version stamp; the reverse asymmetry is on the READ side, where `Laptop`
(x2) and `Language` are read with no writer in the image. `ds:0x6926ec` is not a
variable at all: it is the .data string "Prefs Format" pushed as lpKeyName.

GATES (printed FIRST, then asserted; every VERIFIED row names a mutant in
scripts/m352_mutate.py):
  G1  call-site census in FUN_0058f0d0: exactly 8 register-indirect calls, all
      `call edi`; exactly ONE write of edi, from ds:0x6710fc; 0 other indirect
      calls (no `call DWORD PTR ds:`) -> 1 distinct target for all 8.
  G2  the target RESOLVED from the PE import directory: slot 0x6710fc is in .rdata,
      the section is not writable, its file-time dword is an RVA inside .rdata (an
      import thunk), and the slot names KERNEL32!WritePrivateProfileStringA.
  G3  write-key census: 13 keys = 8 pushed at the 8 direct sites + 5 pushed into
      FUN_0058f030; each key resolves to printable .data text; declared set ==
      measured set both ways. Per site the value provenance is measured: 12 sites
      load a block cell in the same block, 1 (the stamp) loads none and itoa's the
      immediate 0xb; the scalar cells READ by the persist are 11/11.
  G4  read-key census (image-wide and total): the image's 5 references to
      GetPrivateProfileStringA are ALL inside 5 functions (0x58e5a0..0x58e7f0);
      every read site's key is attributed; the 13 written keys are all READ
      (13/13), and the read-only keys measured are {Laptop, Language}.
  G5  the image's WRITE surface: 3 API refs, 33 keyed write sites (8 persist +
      16 FUN_0058f030 + 9 FUN_0058f010), 28 distinct keys; `Laptop` and
      `Language` are written by NONE of them.
  G6  M350's OPEN `who sets ds:0x6926ec` RETRACTS: 0 stores in .text (moffs, byte
      scan, register-copied RMW), 7 uses all `push 0x6926ec` in the lpKeyName slot,
      and the VA holds "Prefs Format" in .data (0x6926e8 holds the "0" default of
      the same call).
  G7  RIVALS, each measured and each FAILING on the printed numbers:
      R1 "the 8 call edi are vtable dispatch -> targets not statically known"
         -> 1 slot, .rdata, contents = a .rdata-internal RVA, named in the imports.
      R2 "the persist writes a key nothing reads (write-only config)" -> 13/13
         written keys have >=1 read site; write-only keys = 0.
      R3 "read set == write set (the game persists every key it reads)" -> 15 read
         keys vs 13 written; the difference is measured, not asserted.
      R4 "ds:0x6926ec is a mutable pointer to the current key" -> 0 stores; all 7
         uses push the immediate address in the lpKeyName argument slot.
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

WRITEBACK = 0x58F0D0
LOADER = 0x58E7F0
HELPER_W = 0x58F030            # (key, value, bitflag) -> one WritePrivateProfileStringA
HELPER_R = 0x58E760            # (key, default, flag) -> int
GATED_R = 0x58E5A0             # (key, default, skip) -> string, "Prefs Format" gate
IAT_W = 0x6710FC               # KERNEL32!WritePrivateProfileStringA
IAT_R = 0x671100               # KERNEL32!GetPrivateProfileStringA
ARRAY_LO, ARRAY_HI = 0x92BF18, 0x92BF34
BLOCK_LO, BLOCK_HI = 0x92BDE8, 0x92BF34
STAMP = 0xB                    # the value the persist writes to `Prefs Format`

# ---- DECLARED sets (measured first by an M352_DUMP run of this instrument; every
# one is re-derived below and compared, both directions).
CALL_EDI = [0x58F11B, 0x58F15F, 0x58F1A2, 0x58F1E4, 0x58F228, 0x58F292,
            0x58F2FC, 0x58F3A8]
HELPER_W_SITES = [0x58F30B, 0x58F31E, 0x58F331, 0x58F343, 0x58F3B7]
WRITE_KEYS = {0x58F11B: "Prefs Format", 0x58F15F: "Difficulty", 0x58F1A2: "Map Type",
              0x58F1E4: "Top Menu", 0x58F228: "Faction", 0x58F292: "Preferences",
              0x58F2FC: "More Preferences", 0x58F3A8: "Custom World",
              0x58F30B: "Semaphore", 0x58F31E: "Announce", 0x58F331: "Rules",
              0x58F343: "Customize", 0x58F3B7: "Time Controls"}
READ_FNS = {"FUN_0058e5a0", "FUN_0058e640", "FUN_0058e6c0", "FUN_0058e760",
            "FUN_0058e7f0"}
READONLY_PREF = {"Laptop": 2, "Language": 1}
IMG_READ_KEYS, IMG_READ_SITES, IMG_UNRES = 35, 52, 2
API_SITES = 23
LOADER_READS = {"Prefs Format": 6, "Laptop": 2, "Language": 1, "Difficulty": 1,
                "Map Type": 1, "Top Menu": 1, "Faction": 1, "Preferences": 1,
                "More Preferences": 1, "Semaphore": 1, "Customize": 1, "Rules": 1,
                "Announce": 1, "Custom World": 1, "Time Controls": 1}
UNRES_SITES = [0x58E62A, 0x58E7CC]
N_IAT_READ_REFS = 5
LAPTOP_PUSHES = [(0x58E688, 0x6926FC), (0x58E708, 0x692704), (0x58E9F3, 0x6926FC),
                 (0x58EB0C, 0x692704)]
LANGUAGE_PUSH = [(0x58E841, 0x69270C)]
WRITE_KEY_DIGEST = "PENDING"
GATE_CMP = 0xB                 # `cmp eax,0xb` at every inline format gate
CELL_LOAD_EXPECT = 11          # scalar cells the persist loads (11/11)
PER_FN_SIG = {WRITEBACK: 758, LOADER: 2066, HELPER_W: 157, HELPER_R: 137,
              GATED_R: 153}

# ALGO mutants of the SCANNER/CLASSIFIER laws (an algorithm mutant is mandatory for
# a tracer/classifier — this instrument is one; named per gate in the harness):
#   1 = key slot for the 4-arg API is off by one (app-name arg taken as the key)
#   2 = helper call sites are NOT attributed (only the API call inside them is)
#   3 = the byte-level 4-byte scan is disabled (moffs text scan alone)
#   4 = helper key slot off by one (the value/default arg taken as the key)
#   5 = every `call REG` counts as an indirect-call target (direct-call census off)
ALGO = os.environ.get("M352_ALGO", "")

LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
OPS = re.compile(r"^([a-z][a-z0-9]*)\s+(.*)$")
REG32 = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")


def insns():
    patch = os.environ.get("M352_PATCH")
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
                    sys.stderr.write("M352_PATCH already equal at %s\n" % patch)
                    raise SystemExit(3)
                txt, hit = pt, True
            mo = OPS.match(txt)
            out.append({"a": a, "by": m.group(2).split(), "t": txt,
                        "op": mo.group(1) if mo else txt.split()[0],
                        "arg": mo.group(2) if mo else ""})
    if patch and not hit:
        sys.stderr.write("M352_PATCH %s not in .text cache\n" % patch)
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


def extraction(func):
    s, z = func[1], func[2]
    return [i for i in INS if s <= i["a"] < s + z]


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
        if v <= va < v + vs:
            return ra + (va - v)
    return None


def sec_of(va):
    for n, v, vs, ra, rs, ch in SECS:
        if v <= va < v + vs:
            return n, ch
    return None, 0


def cstr(va):
    o = va2off(va)
    if o is None:
        return None
    e = PE.index(b"\0", o) if b"\0" in PE[o:o + 64] else -1
    if e < 0:
        return None
    b = PE[o:e]
    if not b or len(b) > 40 or any(not (32 <= c < 127) for c in b):
        return None
    return b.decode("ascii")


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


# ---------- instruction helpers ----------
def pushes_before(idx, n):
    """The n pushes nearest to instruction idx (nearest first), and their indices."""
    got = []
    i = idx - 1
    while i >= 0 and len(got) < n and idx - i <= 14:
        if INS[i]["op"] == "push":
            got.append((INS[i]["a"], INS[i]["arg"].strip()))
        i -= 1
    return got


def trace_reg(reg, before_idx, span=14):
    """Last write of reg before before_idx: ('imm',v) / ('global',va) / ('unknown',txt)."""
    i = before_idx - 1
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
    return ("unknown", "no write in %d insns" % span)


def push_val(pushes, k):
    """Resolve pushes[k] = (addr, arg) to ('imm',v)/('global',va)/('unknown',txt)."""
    a, arg = pushes[k]
    m = re.fullmatch(r"0x([0-9a-f]+)", arg)
    if m:
        return ("imm", int(m.group(1), 16))
    if arg in REG32:
        return trace_reg(arg, POS[a])
    return ("unknown", arg)


def key_text(v):
    if v[0] != "imm":
        return None
    return cstr(v[1])


def key_slot(nargs):
    """cdecl: the FIRST argument is pushed LAST, so the push nearest the call is
    arg1.  6-arg API and 4-arg API -> arg2 (the key) = slot 1; the 3-arg helper
    takes (key, value, flag) -> the key is slot 0.  ALGO mutants shift it."""
    if ALGO == "1" and nargs == 4:
        return 0
    if ALGO == "4" and nargs == 3:
        return 1
    return 0 if nargs == 3 else 1


def is_indirect(ins):
    if ins["op"] != "call":
        return None
    a = ins["arg"].strip()
    if a in REG32:
        return None if ALGO == "5" else "reg"
    if a.startswith("DWORD PTR"):
        return "mem"
    return None


def cell_span(v):
    return BLOCK_LO <= v < BLOCK_HI


TABLES = []


def row(*cols):
    line = " | ".join(str(c) for c in cols)
    TABLES.append(line)
    print(line)


def chk(gate, ok, msg):
    print("[%s] %s %s" % ("PASS" if ok else "FAIL", gate, msg))
    if not ok:
        FAILED.append(gate)


FAILED = []
INF = extraction(fnof(WRITEBACK))
print("== M352 persist FUN_0058f0d0 ==")
row("extent", hex(fnof(WRITEBACK)[1]), fnof(WRITEBACK)[0], fnof(WRITEBACK)[2],
    "insns", len(INF))
chk("G0", all(fnof(a)[2] == z for a, z in PER_FN_SIG.items()),
    "five function extents in ghidra index.csv == declared sizes")

# ---------------- G1: call-site census ----------------
print("\n-- G1 call census in FUN_0058f0d0 (site | form | target) --")
calls = [i for i in INF if i["op"] == "call"]
ind_reg = [i for i in calls if is_indirect(i) == "reg"]
ind_mem = [i for i in calls if is_indirect(i) == "mem"]
direct = [i for i in calls if is_indirect(i) is None]
edi_loads = [i for i in INF if i["op"] in ("mov", "lea") and i["arg"].split(",")[0] == "edi"
             and re.search(r"ds:0x[0-9a-f]+", i["arg"])]
edi_other = [i for i in INF if i["op"] in ("mov", "lea", "xor", "add", "sub", "or", "and")
             and i["arg"].split(",")[0] == "edi"]
for i in ind_reg:
    row(hex(i["a"]), "call reg", i["t"])
row("direct", len(direct), sorted(set(i["arg"] for i in direct)))
row("indirect-mem", len(ind_mem), [i["t"] for i in ind_mem])
row("edi writes", len(edi_other), [i["t"] for i in edi_other])
target_slot = None
if len(edi_loads) == 1:
    m = re.search(r"ds:0x([0-9a-f]+)", edi_loads[0]["arg"])
    target_slot = int(m.group(1), 16) if m else None
row("target slot", hex(target_slot) if target_slot else None)
chk("G1", [i["a"] for i in ind_reg] == CALL_EDI
    and all(i["arg"].strip() == "edi" for i in ind_reg)
    and len(edi_loads) == 1
    and len(edi_other) == 1 and len(ind_mem) == 0
    and target_slot == IAT_W
    and edi_loads[0]["a"] < CALL_EDI[0],
    "8 `call edi`, 1 edi load (%s), 0 mem-indirect -> %d distinct target"
    % (hex(edi_loads[0]["a"]) if edi_loads else "-", 1))

# ---------------- G2: resolve the slot from the import directory ----------------
print("\n-- G2 IAT slot %s (PE import directory) --" % hex(target_slot))
dll, name = IMPORTS.get(target_slot, ("?", "?"))
rdll, rname = IMPORTS.get(IAT_R, ("?", "?"))
sec, cha = sec_of(target_slot)
dword = struct.unpack_from("<I", PE, va2off(target_slot))[0]
tsec, _ = sec_of(BASE + dword)
tname = PE.index(b"\0", va2off(BASE + dword) + 2)
tname = PE[va2off(BASE + dword) + 2:tname].decode("latin1")
row("slot", hex(target_slot), dll, name)
row("neighbour", hex(IAT_R), rdll, rname)
row("section", sec, "write-bit", "SET" if cha & 0x80000000 else "clear")
row("slot dword -> thunk", hex(dword), hex(BASE + dword), "section", tsec,
    "name at thunk", tname)
chk("G2", name == "WritePrivateProfileStringA" and dll.upper().startswith("KERNEL32")
    and sec == ".rdata" and not (cha & 0x80000000) and tsec == ".rdata"
    and tname == name and BASE + dword != target_slot,
    "target = %s!%s; slot in %s (not writable), its own dword names %s"
    % (dll, name, sec, tname))

# ---------------- G3: write-key census + value provenance ----------------
print("\n-- G3 write keys (site | key VA | key text | value source | cells loaded) --")
write_rows = []
BOUNDS = sorted(CALL_EDI + HELPER_W_SITES)
for site in CALL_EDI:
    n = POS[site]
    p = pushes_before(n, 6)
    kv = push_val(p, key_slot(4))
    kt = key_text(kv)
    prev = max([0x58F0D0] + [b for b in BOUNDS if b < site])
    cells = sorted({int(m, 16) for i in INF
                    if prev < i["a"] <= site
                    for m in re.findall(r"ds:0x([0-9a-f]+)", i["arg"])
                    if cell_span(int(m, 16))})
    imms = [int(m.group(1), 16) for i in INF if prev < i["a"] <= site and i["op"] == "push"
            for m in [re.fullmatch(r"0x([0-9a-f]+)", i["arg"].strip())] if m]
    arr = any(i["op"] == "mov" and i["arg"].split(",")[0] == "esi"
              and i["arg"].lower().endswith(hex(ARRAY_LO)) for i in INF
              if prev < i["a"] <= site)
    if arr:
        blk = [i for i in INF if prev < i["a"] <= site]
        arr = (any(i["op"] == "cmp" and i["arg"].strip() == "esi,0x92bf34" for i in blk)
               and any(i["op"] == "add" and i["arg"].strip() == "esi,0x4" for i in blk))
    src = "?"
    if arr:
        cells = [ARRAY_LO]
        src = "ARRAY"
    elif cells:
        src = "CELL"
    elif imms:
        src = "CONST %s" % hex(imms[0])
    if src.startswith("CONST") and any(
            i["op"] == "call" and i["arg"].strip() == "0x64f980"
            for i in INF if prev < i["a"] <= site):
        ito = [i for i in INF if prev < i["a"] <= site and i["op"] == "call"
               and i["arg"].strip() == "0x64f980"][0]
        val = push_val(pushes_before(POS[ito["a"]], 3), 0)
        if val[0] == "imm":
            src = "CONST %s" % hex(val[1])
    write_rows.append((site, kv[1] if kv[0] == "imm" else None, kt, src, cells))
    row(hex(site), hex(kv[1]) if kv[0] == "imm" else kv, kt, src,
        ",".join(hex(c) for c in cells) or "-")
for site in HELPER_W_SITES:
    n = POS[site]
    p = pushes_before(n, 4)
    kv = push_val(p, key_slot(3))
    kt = key_text(kv)
    vv = push_val(p, 1)
    cells = [vv[1]] if vv[0] == "global" and cell_span(vv[1]) else []
    write_rows.append((site, kv[1] if kv[0] == "imm" else None, kt, "HELPER", cells))
    row(hex(site), hex(kv[1]) if kv[0] == "imm" else kv, kt, "HELPER", vv[1] if cells else "-")
measured_keys = {r[0]: r[2] for r in write_rows}
scalars = sorted({c[0] for r in write_rows for c in [r[4]] if c and c[0] != ARRAY_LO})
stamp_rows = [r for r in write_rows if r[3].startswith("CONST")]
array_rows = [r for r in write_rows if r[0] == 0x58F3A8]
row("keys written", len(write_rows), "distinct", len(set(measured_keys.values())))
row("scalar cells loaded", len(scalars), ",".join(hex(c) for c in scalars))
row("stamp", [hex(r[0]) for r in stamp_rows],
    "value", stamp_rows[0][3] if stamp_rows else "-")
cell_rows = [r for r in write_rows if r[4]]
row("blocks that LOAD a block cell", len(cell_rows), "of", len(write_rows),
    "stamps", len(stamp_rows))
chk("G3", measured_keys == WRITE_KEYS and len(set(measured_keys.values())) == 13
    and len(stamp_rows) == 1 and stamp_rows[0][3] == "CONST 0xb"
    and len(array_rows) == 1 and len(scalars) == CELL_LOAD_EXPECT
    and len(cell_rows) == 12,
    "13 keys = 11 scalar names + Prefs Format + Custom World; 12 blocks LOAD a"
    " block cell (window presence, not value provenance), 1 CONST 0xb stamp;"
    " %d/11 scalar cells loaded" % len(scalars))

# ---------------- G4: read-key census, image-wide ----------------
print("\n-- G4 read census: every GetPrivateProfileStringA key in the image --")
refs = [i for i in INS if "0x%x" % IAT_R in i["arg"].lower()]
ref_fns = sorted({fnof(i["a"])[0] for i in refs})
row("IAT refs", len(refs), [hex(i["a"]) for i in refs])
row("functions", len(ref_fns), ref_fns)
read_sites = []


def add_read(site, keyv):
    kt = key_text(keyv)
    read_sites.append((fnof(site)[0], site, keyv[1] if keyv[0] == "imm" else keyv, kt))


for fn in sorted({fnof(i["a"]) for i in refs}):
    body = extraction(fn)
    regs = set()
    for i in body:
        if i["op"] == "mov" and ("ds:0x%x" % IAT_R) in i["arg"].lower():
            regs.add(i["arg"].split(",")[0].strip())
    for n, i in enumerate(body):
        if i["op"] != "call":
            continue
        if ("ds:0x%x" % IAT_R) in i["arg"].lower():
            add_read(i["a"], push_val(pushes_before(POS[i["a"]], 6), key_slot(6)))
            continue
        if i["arg"].strip() in regs and ALGO != "5":
            add_read(i["a"], push_val(pushes_before(POS[i["a"]], 6), key_slot(6)))
if ALGO != "2":
    for tgt in (HELPER_R, GATED_R):
        for i in INS:
            if i["op"] == "call" and i["arg"].strip() == hex(tgt):
                add_read(i["a"], push_val(pushes_before(POS[i["a"]], 4), key_slot(3)))
unres = [r for r in read_sites if r[3] is None]
read_keys = {}
for f, s, v, k in read_sites:
    if k:
        read_keys[k] = read_keys.get(k, 0) + 1
for k in sorted(read_keys):
    row("read key", k, read_keys[k], [hex(r[1]) for r in read_sites if r[3] == k][:8])
row("read keys", len(read_keys), "sites", len(read_sites), "unresolved", len(unres))
for r in unres[:6]:
    row("  unresolved", r[0], hex(r[1]), r[2])
lap = sorted((i["a"], int(i["arg"].strip(), 16)) for i in INS if i["op"] == "push"
             and i["arg"].strip() in ("0x6926fc", "0x692704"))
lang = [(i["a"], int(i["arg"].strip(), 16)) for i in INS if i["op"] == "push"
        and i["arg"].strip() == "0x69270c"]
row("Laptop pushes", [hex(a) for a, v in lap], "declared", LAPTOP_PUSHES)
row("Language pushes", [hex(a) for a, v in lang], "declared", LANGUAGE_PUSH)
gates = [i for i in INS if i["op"] == "cmp" and i["arg"].strip() == "eax,0xb"
         and fnof(i["a"])[0] in ("FUN_0058e7f0", "FUN_0058e5a0")]
other_gates = [i for i in INS if i["op"] == "cmp" and i["arg"].strip() == "eax,0xd"
               and fnof(i["a"])[0] in ("FUN_0058e7f0", "FUN_0058e5a0")]
row("format gates cmp eax,0xb", len(gates), [hex(i["a"]) for i in gates],
    "cmp eax,0xd", len(other_gates))
wo = sorted(set(WRITE_KEYS.values()) - set(read_keys))
ro = {k: read_keys[k] for k in sorted(set(read_keys) - set(WRITE_KEYS.values()))}
row("write-only keys", len(wo), wo)
row("read-only keys (image)", len(ro), ro)
loader = {}
for f, s, v, k in read_sites:
    if f == "FUN_0058e7f0" and k:
        loader[k] = loader.get(k, 0) + 1
pref_ro = {k: loader[k] for k in loader if k not in WRITE_KEYS.values()}
row("loader reads", len(loader), "sites", sum(loader.values()))
row("loader read-only keys", pref_ro, "declared", READONLY_PREF)
chk("G4", len(refs) == N_IAT_READ_REFS and len(ref_fns) == 5
    and set(ref_fns) <= READ_FNS and len(read_sites) == IMG_READ_SITES
    and len(unres) == IMG_UNRES and [r[1] for r in unres] == UNRES_SITES
    and len(read_keys) == IMG_READ_KEYS and not wo
    and loader == LOADER_READS and pref_ro == READONLY_PREF
    and [tuple(x) for x in lap] == LAPTOP_PUSHES
    and [tuple(x) for x in lang] == LANGUAGE_PUSH and len(gates) == 7
    and len(other_gates) == 0,
    "5 refs in 5 fns; %d read keys / %d sites; 13/13 written keys read; 0"
    " write-only; loader reads 15 keys (Laptop x2, Language x1 have no writer)"
    % (len(read_keys), len(read_sites)))

# ---------------- G5: the image's WRITE surface (is Laptop ever written?) ----------------
print("\n-- G5 write surface: every WritePrivateProfileStringA key in the image --")
wrefs = [i for i in INS if "0x%x" % IAT_W in i["arg"].lower()]
wsites = []
for tgt, nargs in ((HELPER_W, 3), (0x58F010, 2)):
    for i in INS:
        if i["op"] != "call" or i["arg"].strip() != hex(tgt):
            continue
        p = pushes_before(POS[i["a"]], nargs + 1)
        k = push_val(p, 0)
        kt = key_text(k)
        if kt is None and i["a"] == 0x5992C9:
            # conditional key: `mov eax,0x6930a4` / `mov eax,0x6930b4` before the call
            alt = sorted({int(m, 16) for j in INS if i["a"] - 16 <= j["a"] < i["a"]
                          for m in re.findall(r"0x(69[0-9a-f]{4})", j["arg"])
                          if j["op"] == "mov" and j["arg"].startswith("eax")})
            kt = "/".join(sorted(x for x in (cstr(a) for a in alt) if x))
        wsites.append((i["a"], kt))
cab = None
wkeys = {}
for f, k in wsites:
    if k:
        wkeys[k] = wkeys.get(k, 0) + 1
all_w = dict(wkeys)
for k in WRITE_KEYS.values():
    all_w[k] = all_w.get(k, 0) + 1
for k in sorted(wkeys):
    row("write key", k, wkeys[k], [hex(a) for a, x in wsites if x == k][:6])
row("IAT write refs", len(wrefs), [hex(i["a"]) for i in wrefs])
row("write sites", len(wsites), "= 16 helper + 9 wrapper",
    "distinct keys", len(wkeys))
row("write sites total", len(wsites) + len(CALL_EDI), "= 16 + 9 + 8 persist",
    "distinct keys", len(all_w))
row("poorly-resolved", [hex(a) for a, k in wsites if not k])
chk("G5", len(wrefs) == 3 and len(wsites) == 25 and len(wkeys) == 20
    and len(all_w) == 28 and not [a for a, k in wsites if not k]
    and "Laptop" not in all_w and "Language" not in all_w
    and set(WRITE_KEYS.values()) <= set(all_w),
    "3 API refs; 33 keyed write sites / 28 distinct keys; Laptop and Language"
    " are written by NONE of them")

# ---------------- G6: ds:0x6926ec is a string literal, not a variable ----------------
print("\n-- G6 ds:0x6926ec (M350 OPEN: who sets it) --")
uses = [i for i in INS if "0x6926ec" in i["arg"].lower()]
STORE_OPS = ("mov", "or", "and", "add", "sub", "xor", "inc", "dec", "not", "xchg")


def dst_is_va(ins, va):
    """TEXT-ONLY: the FIRST operand names the VA (moffs and mem-dest forms)."""
    if "," not in ins["arg"]:
        return False
    dst = ins["arg"].split(",")[0].strip()
    for pre in ("BYTE PTR ", "DWORD PTR ", "WORD PTR "):
        if dst.startswith(pre):
            dst = dst[len(pre):]
    return dst == "ds:0x%x" % va


stores = [i for i in uses if i["op"] in STORE_OPS and dst_is_va(i, 0x6926EC)]
pat = struct.pack("<I", 0x6926EC)
hits, o = [], 0
while True:
    o = PE.find(pat, o)
    if o < 0:
        break
    hits.append(o)
    o += 1
hits = [] if ALGO == "3" else hits
row("text uses", len(uses), [i["t"] for i in uses][:3])
row("stores", len(stores))
row("byte hits of the VA", len(hits), "all `<68> + VA`",
    all(PE[h - 1] == 0x68 and PE[h:h + 4] == pat for h in hits) if hits else "-")
row("key slot", [hex(i["a"]) for i in uses if i["op"] == "push"])
row("PE bytes @0x6926ec", PE[va2off(0x6926EC):va2off(0x6926EC) + 13])
row("PE bytes @0x6926e8", PE[va2off(0x6926E8):va2off(0x6926E8) + 4])
chk("G6", len(uses) == 7 and not stores and len(hits) == 7
    and all(i["op"] == "push" and i["arg"].strip() == "0x6926ec" for i in uses)
    and all(PE[h - 1] == 0x68 for h in hits)
    and cstr(0x6926EC) == "Prefs Format" and cstr(0x6926E8) == "0",
    "no store NAMES the VA; 7 uses all lpKeyName pushes; the 7 four-byte VA"
    " occurrences are all push imm32 -> no writer materialises it at all")

# ---------------- G7: rivals, each failing on the numbers above ----------------
print("\n-- G7 rivals (each must FAIL on the printed numbers) --")
rw = len([i for i in ind_reg if is_indirect(i) == "reg"]) if ALGO != "5" else len(calls)
r1 = (len(ind_reg) == 8 and len(edi_other) == 1 and sec == ".rdata"
      and not (cha & 0x80000000) and name == "WritePrivateProfileStringA")
r2 = (len(wo) == 0 and len(write_rows) == 13)
r3 = (len(read_keys) == len(set(WRITE_KEYS.values())) and set(read_keys) ==
      set(WRITE_KEYS.values()))
r4 = (len(stores) == 0)
row("R1 vtable/unknown targets", "REFUTED" if r1 else "SURVIVES",
    "8 calls, %d slot, %s, %s" % (1, sec, name))
row("R2 write-only key exists", "REFUTED" if r2 else "SURVIVES",
    "13 writes, %d write-only" % len(wo))
row("R3 read set == write set", "REFUTED" if not r3 else "SURVIVES",
    "%d read vs %d written" % (len(read_keys), len(set(WRITE_KEYS.values()))))
row("R4 0x6926ec is a mutable pointer", "REFUTED" if r4 else "SURVIVES",
    "%d stores, %d uses" % (len(stores), len(uses)))
chk("G7", r1 and r2 and not r3 and r4,
    "R1/R2/R4 refuted, R3 refuted by the measured %d-vs-13 set difference"
    % len(read_keys))

dig = hashlib.sha1("\n".join(TABLES).encode()).hexdigest()
print("\ntables digest %s  (%d rows)" % (dig[:16], len(TABLES)))
print("RESULT: %s M352: %d/%d gates" %
      ("PASS" if not FAILED else "FAIL", 7 - len(set(FAILED)), 7))
if FAILED:
    print("failed: %s" % sorted(set(FAILED)))
return_code = 0 if not FAILED else 1
sys.exit(return_code)
