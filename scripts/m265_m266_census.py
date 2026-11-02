#!/usr/bin/env python3
"""M265: what the 7 allocated 0x22480 view-table blocks ARE.
M266: why FUN_00583c70 exists with ZERO references.

Instrument = three sources, one run, no box time:
  (a) the whole-image .text disassembly corpus scratch/m574/text.txt,
  (b) the raw PE image programs/terran.exe (section map from objdump -h),
  (c) ghidra_out/index.csv function containment (addr,name,size).

Acceptance: ONE real invocation prints `SUMMARY M265/M266: 11/11 gates PASS`.
"""
import os
import re
import struct
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(REPO, "scratch/m574/text.txt")
EXE = os.path.join(REPO, "programs/terran.exe")
INDEX = os.path.join(REPO, "ghidra_out/index.csv")

LINE = re.compile(r"^\s+([0-9a-f]{6,8}):\t((?:[0-9a-f]{2} ){0,7}[0-9a-f]{2} )?\t?(\S+) ?(.*)$")


def insns(lo, hi):
    """(pc, mnemonic, operands) for every corpus line in [lo,hi]."""
    out = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = LINE.match(line.replace("\\t", "\t"))
            if not m:
                continue
            a = int(m.group(1), 16)
            if a > hi:
                break
            if a >= lo:
                out.append((a, m.group(3).lower(), m.group(4).strip()))
    return out


# ---- helpers --------------------------------------------------------------------
import bisect
import csv

CODE_LO, CODE_HI = 0x401000, 0x6703F4  # .text span from objdump -h


def load_funcs():
    rows = []
    with open(INDEX) as f:
        for r in csv.DictReader(f):
            try:
                rows.append((int(r["addr"], 16), r["name"],
                             int(r["size_bytes"]), int(r["n_callers"]),
                             int(r["n_insns"])))
            except Exception:
                pass
    rows.sort()
    return rows


FUNCS = load_funcs()
FADDR = [a for a, _, _, _, _ in FUNCS]
IMG = open(EXE, "rb").read()


def load_secs():
    out = subprocess.run(["objdump", "-h", EXE], capture_output=True,
                         text=True).stdout
    secs = []
    for line in out.splitlines():
        m = re.match(r"\s*\d+\s+(\S*)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)",
                     line)
        if m:
            secs.append((m.group(1) or "(unnamed)", int(m.group(3), 16),
                         int(m.group(2), 16), int(m.group(4), 16)))
    return secs


SECS = load_secs()


def fn_of(addr):
    """(name, size) of the index.csv function containing addr, else (None, None)."""
    i = bisect.bisect_right(FADDR, addr) - 1
    if i < 0:
        return (None, None)
    a, n, s, _c, _i = FUNCS[i]
    return (n, s) if addr < a + s else (None, None)


def sec_of(off):
    for name, _vma, size, foff in SECS:
        if foff <= off < foff + size:
            return name
    return "?"


def dword_at(va):
    off = va - 0x400000  # every section here maps file_off = vma - 0x400000
    if 0 <= off <= len(IMG) - 4:
        return struct.unpack_from("<I", IMG, off)[0]
    return None


def raw_dword_hits(value):
    """Every file offset whose LE dword == value (imm32 in code, data pointers)."""
    pat = struct.pack("<I", value & 0xFFFFFFFF)
    offs, i = [], 0
    while True:
        i = IMG.find(pat, i)
        if i < 0:
            break
        offs.append(i)
        i += 1
    return offs, sorted({sec_of(o) for o in offs})


# ---- one pass over the corpus ---------------------------------------------------
TOKENS = {"583c70", "675964", "0x6725ac", "0x6725a4", "0x6763fc", "0x678458",
          "0x677dc4", "0x469650", "0x5e3b80", "0x5e3d74", "0x4017d0", "0x64bda0",
          "0x5cdd0a", "0x5cdf82", "0x8cc520", "0x22480", "0x679308", "0x679300",
          "0x582000", "0x92a378", "0x92a37c", "0x580260"}
BODY_NAMES = {"FUN_00469650", "FUN_00583c70", "FUN_00583c20", "FUN_004412a0",
              "FUN_00479e90", "FUN_005e3b80", "FUN_00518820", "FUN_00518980",
              "FUN_00580260"}
DESCRIPTORS = (0x675964, 0x6763fc, 0x678458)
# seed with whatever functions hold each descriptor's imm32 (found in the raw
# image, so their bodies land in the same single corpus pass)
for _d in DESCRIPTORS:
    for _o in raw_dword_hits(_d)[0]:
        _va = _o + 0x400000
        _i = bisect.bisect_right(FADDR, _va) - 1
        if _i >= 0 and _va < FUNCS[_i][0] + FUNCS[_i][2]:
            BODY_NAMES.add(FUNCS[_i][1])
BODY_OF = {n: [] for n in BODY_NAMES}

HITS = {t: [] for t in TOKENS}
SIG = {}          # function name -> list of mnemonics
cur = [None, 0, 0]  # (name, start, end)


def owner(addr):
    if cur[0] is not None and cur[1] <= addr < cur[2]:
        return cur[0]
    i = bisect.bisect_right(FADDR, addr) - 1
    if i < 0:
        return None
    a, n, s, _c, _i = FUNCS[i]
    if addr < a + s:
        cur[0], cur[1], cur[2] = n, a, a + s
        return n
    cur[0] = None
    return None


with open(TEXT, "r", errors="replace") as _f:
    for _line in _f:
        if "\t" not in _line and "\\t" in _line:
            _line = _line.replace("\\t", "\t")
        _p = _line.rstrip("\n").split("\t")
        if len(_p) < 3:
            continue
        _m = re.fullmatch(r"\s*([0-9a-f]{6,8}):", _p[0])
        if not _m:
            continue
        _pc = int(_m.group(1), 16)
        _tail = _p[2].split(None, 1)
        if not _tail:
            continue
        _mn, _ops = _tail[0].lower(), (_tail[1] if len(_tail) > 1 else "")
        _fn = owner(_pc)
        if _fn is not None:
            SIG.setdefault(_fn, []).append(_mn)
            if _fn in BODY_OF:
                BODY_OF[_fn].append((_pc, _mn, _ops))
        for _t in TOKENS:
            if _t in _ops:
                HITS[_t].append((_pc, _mn, _ops))


def body(name):
    return BODY_OF.get(name, [])


def find(name, pc):
    for i, (a, m, o) in enumerate(body(name)):
        if a == pc:
            return i
    return -1


def call_sites(target):
    """(pc, caller_name) for every `call <target>` in the corpus."""
    t = "0x%x" % target
    return [(pc, owner_at(pc)) for pc, mn, _o in HITS.get(t, []) if mn == "call"]


def owner_at(pc):
    i = bisect.bisect_right(FADDR, pc) - 1
    if i < 0:
        return None
    a, n, s, _c, _i = FUNCS[i]
    return n if pc < a + s else None


def pushes_before(rows, i, want=6, back=18):
    """Operands of the nearest `want` pushes walking back from rows[i]."""
    out = []
    for j in range(i - 1, max(i - back, -1), -1):
        if rows[j][1] == "push":
            out.append(rows[j][2])
            if len(out) >= want:
                break
    return out          # nearest push first: buffer, size, count, ctor, dtor


def reg_offset_added(rows, i, reg):
    """The immediate added to `reg` by the last add/lea before rows[i]."""
    for j in range(i - 1, max(i - 14, -1), -1):
        _pc, mn, ops = rows[j]
        if not ops.startswith(reg + ","):
            continue
        if mn == "add":
            m = re.fullmatch(r"%s,(0x[0-9a-f]+)" % reg, ops)
            if m:
                return int(m.group(1), 16)
        if mn == "lea":
            m = re.match(r"%s,\[([a-z0-9]+)\+(0x[0-9a-f]+)\]" % reg, ops)
            if m:
                return int(m.group(2), 16)
    return None


GATES = []


def gate(name, ok, detail):
    GATES.append((name, ok, detail))
    print("%s %s | %s" % ("PASS" if ok else "FAIL", name, detail))


# ---- M265 ----------------------------------------------------------------------
# G1 the ctor is shared by 7 sites; one of them is the view-table alloc loop
sites = sorted(call_sites(0x469650))
gate("G1", len(sites) == 7 and (0x5803b2, "FUN_00580260") in sites,
     "call 0x469650: %d sites = %s" % (len(sites),
     ", ".join("%x@%s" % (p, c) for p, c in sites)))

rows = body("FUN_00469650")
i_desc = find("FUN_00469650", 0x469681)
pre = rows[max(0, i_desc - 12):i_desc]
has_cmp = any(m == "cmp" and o == "DWORD PTR [ebp+0x8],0x0" for _p, m, o in pre)
has_je = any(m == "je" and o and int(o.split()[-1], 16) > 0x469681 for _p, m, o in pre)
gate("G2", i_desc >= 0 and has_cmp and has_je and len(HITS["675964"]) == 1,
     "[eax],0x675964 at 0x469681 behind cmp[ebp+8],0=%s je-past=%s; 0x675964 named %dx"
     % (has_cmp, has_je, len(HITS["675964"])))

# G3 the three 0x64bda0 array constructs inside the ctor
EXP = [(0xc, [0x260, 4, 0x62514b, 0x62516c]),
       (0x98c, [0x260, 0xc4, 0x62514b, 0x62516c]),
       (0x1ef54, [0xabc, 4, 0x6251d0, 0x625209])]
got = []
for i, (pc, m, o) in enumerate(rows):
    if m == "call" and o == "0x64bda0":
        ps = pushes_before(rows, i, 5)
        reg = re.fullmatch(r"([a-z]+)", ps[0]) if ps else None
        off = reg_offset_added(rows, i, reg.group(1)) if reg else None
        imm = [int(x, 16) for x in ps[1:] if re.fullmatch(r"0x[0-9a-f]+", x or "")]
        got.append((off, imm))
i_el = -1
for i, (pc, m, o) in enumerate(rows):
    if m == "call" and o == "0x62514b":
        i_el = i
        break
el_off = reg_offset_added(rows, i_el, "ecx") if i_el >= 0 else None
arith = (0xc + 200 * 0x260 == 0x1db0c and 0x98c + 196 * 0x260 == 0x1db0c
         and el_off is not None and el_off + 0x260 == 0x1dd6c)
gate("G3", got == EXP and el_off == 0x1db0c and arith,
     "arrays(off,size,count,ctor,dtor)=%s in-place elem ctor 0x62514b at %s; "
     "200 elems +0xc..+0x1db0c contiguous, 201st +0x1db0c..+0x1dd6c=%s"
     % ([(hex(a), [hex(y) for y in b]) for a, b in got], hex(el_off or -1), arith))

# G4 the vtable pair on the base subobject
st_ac = [h for h in HITS["0x6725ac"] if h[1] == "mov"]
st_a4 = [h for h in HITS["0x6725a4"] if h[1] == "mov"]
fns = sorted({owner_at(p) or "?" for p, _m, _o in st_ac})
code_vt = all(CODE_LO <= (dword_at(v) or 0) <= CODE_HI for v in (0x6725ac, 0x6725a4))
pair444 = any("+0x444]" in o for _p, _m, o in st_a4)
gate("G4", len(st_ac) == 5 and len(st_a4) == 5 and len(fns) == 5 and code_vt
     and pair444,
     "0x6725ac stored %dx in %d fns %s; 0x6725a4 stored %dx delta+0x444=%s; "
     "slot0 %s/%s code=%s"
     % (len(st_ac), len(fns), ",".join(str(f) for f in fns), len(st_a4), pair444,
        hex(dword_at(0x6725ac) or 0), hex(dword_at(0x6725a4) or 0), code_vt))

# G5 [obj+0] is a class descriptor: its +4 IS the 0x5e3b80 subobject offset
law = []
for d in DESCRIPTORS:
    offs = raw_dword_hits(d)[0]
    fn = owner_at(offs[0] + 0x400000) if offs else None
    k = dword_at(d + 4)
    seen = []
    for i, (pc, m, o) in enumerate(body(fn) if fn else []):
        if m == "call" and o == "0x5e3b80":
            v = reg_offset_added(body(fn), i, "ecx")
            if v is not None:
                seen.append((pc, v))
    law.append((d, fn, k, seen, len(offs)))
gate("G5", len(law) == 3 and all(k is not None and k in [v for _p, v in s]
     and not CODE_LO <= k <= CODE_HI for _d, _f, k, s, _n in law),
     " ".join("desc %s@%s[+4]=%s in 0x5e3b80-ecx offsets %s imms=%d" %
              (hex(d), f, hex(k) if k is not None else "-",
               ",".join("%s:%s" % (hex(p), hex(v)) for p, v in s), n)
              for d, f, k, s, n in law))

# G6 size proof
disps = [int(x, 16) for _p, m, o in body("FUN_005e3b80") if m == "mov"
         for x in re.findall(r"\+(0x[0-9a-f]+)", o)]
maxd = max(disps) if disps else -1
n22480 = len([h for h in HITS["0x22480"] if h[1] == "push"])
gate("G6", maxd == 0xa10 and 0x21a6c + maxd + 4 == 0x22480 and n22480 == 1,
     "subobject ctor FUN_005e3b80 tops out at +0x%x; 0x21a6c+0x%x+4=0x%x=the "
     "allocation %s, pushed %d time(s)"
     % (maxd, maxd + 4, 0x21a6c + maxd + 4, hex(0x22480), n22480))

# G7 teardown + dispatch law
tb = body("FUN_00479e90")
need = [("cmp", "DWORD PTR [eax+0x4],0x0"), ("call", "0x4017d0"),
        ("mov", "DWORD PTR [eax+0x4],0x0"), ("mov", "edx,DWORD PTR [ecx]"),
        ("add", "ecx,DWORD PTR [edx+0x4]"), ("call", "0x5e3d74")]
start, order = 0, []
for mn, o in need:
    j = next((k for k in range(start, len(tb))
              if tb[k][1] == mn and tb[k][2] == o), -1)
    order.append(j)
    start = j + 1 if j >= 0 else start
rb = body("FUN_004412a0")
desc_read = any(m == "mov" and o.endswith("DWORD PTR [eax+0x4]") for _p, m, o in rb)
vcalls = [o for _p, m, o in rb if m == "call"
          and o in ("DWORD PTR [edx+0x8]", "DWORD PTR [eax+0x4]")]
pairs = []
for i, (pc, m, o) in enumerate(rb):
    if m == "call" and o in ("0x5cdd0a", "0x5cdf82") and i:
        if rb[i - 1][1] == "mov" and rb[i - 1][2] == "ecx,0x8cc520":
            pairs.append((hex(pc), o))
slots = (dword_at(0x6725ac + 4), dword_at(0x6725ac + 8))
gate("G7", all(j >= 0 for j in order) and order == sorted(order) and desc_read
     and len(vcalls) == 2 and len(pairs) == 2 and slots == (0x5cdd0a, 0x5cdf82),
     "FUN_00479e90 insn order %s = free [this+4] via 0x4017d0 then "
     "this+=[desc+4] -> 0x5e3d74; FUN_004412a0 desc+4=%s virtual calls %s; "
     "slots+4/+8=%s/%s also called on 0x8cc520 at %s"
     % (order, desc_read, vcalls, hex(slots[0] or 0), hex(slots[1] or 0),
        ",".join("%s>%s" % (a, b) for a, b in pairs)))

# ---- M266 ----------------------------------------------------------------------
# G8 the address appears in no operand of .text and in no dword of the image
ops_hits = HITS["583c70"]
offs70, secs70 = raw_dword_hits(0x583c70)
gate("G8", len(ops_hits) == 0 and len(offs70) == 0,
     "0x583c70 in .text operands: %d %s | as an LE dword anywhere in the file "
     "image (all %d sections): %d hits %s"
     % (len(ops_hits), [(hex(p), m, o) for p, m, o in ops_hits[:4]], len(SECS),
        len(offs70), secs70))

# G9 no fallthrough: the predecessor rets, then 4 NOPs, then a real prologue
b70 = body("FUN_00583c70")
pad = IMG[0x583c6c - 0x400000:0x583c70 - 0x400000]
prev_ret = any(p == 0x583c6b and m == "ret" for p, m, _o in body("FUN_00583c20"))
prologue = (len(b70) >= 2 and b70[0][1] == "push" and b70[0][2] == "ebp"
            and b70[1][1] == "mov" and b70[1][2] == "ebp,esp")
gate("G9", pad == b"\x90" * 4 and prev_ret and prologue,
     "bytes 0x583c6c..0x583c6f=%s, 0x583c6b is a ret of FUN_00583c20=%s, "
     "0x583c70 prologue push ebp/mov esp,ebp=%s" % (pad.hex(), prev_ret, prologue))

# G10 the dead cluster this function sits in
INSNS = {n: i for _a, n, _s, _c, i in FUNCS}
cluster = []
for a, n, s, c, i in FUNCS:
    if 0x583000 <= a < 0x584300 and c == 0:
        h, _sec = raw_dword_hits(a)
        cluster.append((n, a, i, len(h)))
dead = [x for x in cluster if x[3] == 0]
gate("G10", ("FUN_00583c70", 0x583c70, 159, 0) in cluster and len(dead) == len(cluster),
     "functions in 0x583000..0x584300 with n_callers==0: %d, of which 0 "
     "address-taken dwords: %d -> %s"
     % (len(cluster), len(dead), ", ".join("%s@%s(%d insns,%d hits)"
        % (n, hex(a), i, h) for n, a, i, h in cluster)))

# G11 what it is: a terrain-record helper of the same family as its 1-caller sibling
cal70 = sorted({int(o, 16) for _p, m, o in b70
                if m == "call" and re.fullmatch(r"0x[0-9a-f]+", o)})
gl70 = sorted({x for _p, _m, o in b70 for x in re.findall(r"ds:(0x[0-9a-f]{6})", o)})
gl20 = sorted({x for _p, _m, o in body("FUN_00583c20")
               for x in re.findall(r"ds:(0x[0-9a-f]{6})", o)})
stride = any(m == "add" and o == "ecx,0x2c" for _p, m, o in body("FUN_00583c20"))
gate("G11", 0x582000 in cal70 and "0x92a378" in gl70 and "0x92a37c" in gl70
     and "0x92a378" in gl20 and "0x92a37c" in gl20 and stride,
     "FUN_00583c70 callees %s; globals %s; sibling FUN_00583c20 (1 caller, "
     "stride-0x2c record walk=%s) globals %s"
     % ([hex(x) for x in cal70], gl70, stride, gl20))

# G12 duplicate test: is it a kept-alive copy of a wired function?
sig70 = " ".join(SIG.get("FUN_00583c70", []))
dupes = [n for n, toks in SIG.items()
         if n != "FUN_00583c70" and len(toks) >= 40 and " ".join(toks) == sig70]
gate("G12", len(sig70.split()) == INSNS.get("FUN_00583c70"),
     "mnemonic signature %d tokens == index.csv n_insns=%d; other functions "
     ">=40 insns with the SAME signature: %d %s"
     % (len(sig70.split()), INSNS.get("FUN_00583c70"), len(dupes), dupes[:5]))

print("SUMMARY M265/M266: %d/%d gates PASS" % (sum(1 for g in GATES if g[1]), len(GATES)))
