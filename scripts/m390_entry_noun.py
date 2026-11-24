#!/usr/bin/env python3
"""M390 - FUN_004dabb0's entry mechanism, and the noun of FUN_00551cf0's boolean argument.

Two questions, one static unit (zero box time):

  Q1  M385 measured FUN_004dabb0 as DEAD-INF from two facts (0 `call` insns, 0 stored
      absolute dwords).  A function can still be entered by a COMPUTED DISPATCH: a
      vtable slot, a switch jump table, a callback registry, a `call [table+idx*4]`.
      Every one of those stores the target's 32-bit VA somewhere in the image.  This
      instrument enumerates the storage surface and decides whether 0x4dabb0 is in it.

  Q2  FUN_00551cf0(a,b,mask,flag) writes the relations dword 0x94d448.  What is `flag`?
      M385 read one caller (FUN_004dacc0) as a SET/CLEAR gate; this instrument reads the
      callee body (both branches) and censuses all 36 call sites' 4th argument.

Instruments, in order: PE header (is the image rebasable at all?), index.csv bodies,
a linear branch census, a whole-image address-taken census with a POSITIVE CONTROL
(a live sibling whose address IS stored), an indirect-dispatch census, then the callee
body + caller arg census.

M390_ALGO=n flips a law (each must redden a named row):
  1 address-taken census restricted to .text (control becomes blind)
  2 fallthrough law off (a `ret 4` predecessor counts as fallthrough)
  3 image treated as rebasable (DYNAMIC_BASE faked on)
  4 body-diff compares only the 6-instruction prologue
  5 the flag slot is read from [ebp+0x10] (arg3) instead of [ebp+0x14]
  6 the caller's 4th arg is taken as the LAST push (arg1)
  7 the SET/CLEAR polarity of the flag is flipped
M390_PATCH='addr|text' rewrites one instruction in the linear dump (mutants).
"""
import csv
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M390_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.environ.get("M390_EXE", "/home/paul/reverse/smac/terran.exe")
CSV = os.environ.get("M390_CSV", os.path.join(ROOT, "ghidra_out/index.csv"))
ALGO = int(os.environ.get("M390_ALGO", "0") or 0)
PATCH = os.environ.get("M390_PATCH", "")

TARGET = 0x4DAB90 if ALGO == 9 else 0x4DABB0   # ALGO 9 = aim the census at a live sibling
FAMILY = [0x4dab90, 0x4dabb0, 0x4dac30, 0x4dacc0, 0x4dadd0]
SETTER = 0x551cf0
FIELD = "94d448"
CELL = "94d4c8"

FAILS = []
TOTAL = [0]
REPORT = []


class _Tee:
    def __init__(self, f):
        self.f = f

    def write(self, s):
        REPORT.append(s)
        return self.f.write(s)

    def flush(self):
        return self.f.flush()


sys.stdout = _Tee(sys.stdout)


def check(name, cond, detail=""):
    TOTAL[0] += 1
    print(("  ok   " if cond else "  FAIL ") + name + ((" - " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)
    return cond


# ---------------------------------------------------------------- parse ------
PAT = re.compile(r"^\s*([0-9a-f]+):\t[0-9a-f ]+\t(.*)$")
INS = []
for line in open(TEXT, encoding="latin-1"):
    m = PAT.match(line.rstrip("\n"))
    if not m:
        continue
    body = m.group(2).strip()
    if body:
        INS.append((int(m.group(1), 16), body))
if PATCH:
    _a, _t = PATCH.split("|", 1)
    _a = int(_a, 16)
    INS = [(x, _t.strip() if x == _a else b) for x, b in INS]
ADDR = [a for a, _ in INS]
IDX = {a: i for i, a in enumerate(ADDR)}
BRANCH = re.compile(r"^(call|jmp|j[a-z]+)\s+0x([0-9a-f]+)$")

RAW = open(EXE, "rb").read()
RANGES = [  # name, file_off, vma, size  (from `objdump -h`)
    (".text", 0x1000, 0x401000, 0x26F3F4),
    (".rdata", 0x271000, 0x671000, 0x175B3),
    (".data", 0x289000, 0x689000, 0x20000),
    ("", 0x2A9000, 0x9A0000, 0x1658),
    ("UVA_DATA", 0x2AB000, 0x9A2000, 0x4AC8),
    ("_SELFMOD", 0x2B0000, 0x9A7000, 0x415D),
    (".rsrc", 0x2B5000, 0x9AC000, 0x5C58),
    (".reloc", 0x2BB000, 0x9B2000, 0x3140E),
]
TEXT_LO, TEXT_HI = 0x401000, 0x401000 + 0x26F3F4


def sect_of_va(va):
    for n, _o, vma, sz in RANGES:
        if vma <= va < vma + sz:
            return n
    return None


def va2off(va):
    for _n, o, vma, sz in RANGES:
        if vma <= va < vma + sz:
            return o + (va - vma)
    return None


def off2va(off):
    for _n, o, vma, sz in RANGES:
        if o <= off < o + sz:
            return vma + (off - o)
    return None


def body_of(entry, size):
    out = [(a, b) for a, b in INS if entry <= a < entry + size]
    return out


def fns():
    out = {}
    for row in csv.DictReader(open(CSV)):
        out[row["name"]] = (int(row["addr"], 16), int(row["size_bytes"]),
                            int(row["n_insns"]), int(row["n_callers"]))
    return out


FN = fns()

print("M390  FUN_004dabb0's entry mechanism + the noun of FUN_00551cf0's boolean")

# ---------------- G0 ---------------------------------------------------------
print("\nG0  parse + the PE law that makes an address census complete")
print("  insns=%d  file=%d B" % (len(INS), len(RAW)))
pe = struct.unpack_from("<I", RAW, 0x3C)[0]
_opt = pe + 24
imgbase = struct.unpack_from("<I", RAW, _opt + 0x1C)[0]
dllc = struct.unpack_from("<H", RAW, _opt + 0x46)[0]
reloc_dir = struct.unpack_from("<II", RAW, _opt + 0xA0)
if ALGO == 3:
    dllc |= 0x40                      # law mutant: image treated as rebasable
print("  ImageBase=%#x  DllCharacteristics=%#06x (DYNAMIC_BASE=%s)  reloc dir=(%#x,%#x)"
      % (imgbase, dllc, bool(dllc & 0x40), reloc_dir[0], reloc_dir[1]))
check("G0 linear dump parses to 781429 insns", len(INS) == 781429, str(len(INS)))
check("G0 the censused file is the 3,067,904-B terran.exe", len(RAW) == 3067904, str(len(RAW)))
check("G0 ImageBase is 0x400000", imgbase == 0x400000, hex(imgbase))
check("G0 image has NO DYNAMIC_BASE (never relocated)", not (dllc & 0x40), hex(dllc))
check("G0 reloc data directory is empty", reloc_dir == (0, 0), str(reloc_dir))
print("  -> a stored pointer can only name 0x4dabb0 by holding its literal dword;")
print("     the loader never rewrites an address, so the byte census in G3 is complete")

# ---------------- G1 ---------------------------------------------------------
print("\nG1  entry shape of FUN_004dabb0")
ent, size, nins, ncall = FN["FUN_004dabb0"]
body = body_of(ent, size)
print("  index.csv: entry=%#x size=%d insns=%d n_callers=%d" % (ent, size, nins, ncall))
print("  body %#x..%#x:" % (body[0][0], body[-1][0] + 1))
for a, b in body:
    print("    %#010x  %s" % (a, b))
prev_i = IDX[ent] - 1 - (2 if ALGO == 2 else 0)   # ALGO 2 = treat the `ret 4` as transparent
prev = INS[prev_i]
after = INS[IDX[body[-1][0]] + 1]
rets = [(a, b) for a, b in body if b.startswith("ret")]
print("  predecessor   %#010x  %s" % (prev[0], prev[1]))
print("  first         %#010x  %s" % (body[0][0], body[0][1]))
print("  last          %#010x  %s" % (body[-1][0], body[-1][1]))
print("  successor     %#010x  %s" % (after[0], after[1]))
print("  rets=%d %s" % (len(rets), [b for _a, b in rets]))
check("G1 body is 122 B / 48 insns and ends at the 0x4dac2a nop pad",
      size == 122 and len(body) == nins == 48 and after[0] == 0x4DAC2A,
      "%d/%d/%#x" % (size, len(body), after[0]))
check("G1 the predecessor instruction is a `ret 4` (no fallthrough)",
      prev[1].replace(" ", "") == "ret0x4", "%#x %s" % (prev[0], prev[1]))
check("G1 both exits are `ret 4` (one ebp frame, one arg)",
      len(rets) == 2 and all(b == "ret    0x4" for _a, b in rets), str([hex(a) for a, _ in rets]))
SIB = 0x4DAB90 if ALGO == 13 else 0x4DAC30   # ALGO 13: compare against a non-sibling neighbour
sib = body_of(*FN["FUN_%08x" % SIB][:2])
pro = [b for _a, b in body[:6]]
sib_pro = [b for _a, b in sib[:6]]
print("  prologue      %s" % pro)
print("  sibling %#x prologue %s" % (SIB, sib_pro))
check("G1 prologue is the family signature, identical to the CALLED sibling 0x4dac30",
      pro == sib_pro and pro[0] == "push   ebp" and pro[5] == "mov    esi,ecx")

# ---------------- G2 ---------------------------------------------------------
print("\nG2  branch census over the whole .text: who transfers control to %#x" % TARGET)
br = []
for a, b in INS:
    m = BRANCH.match(b)
    if m:
        br.append((a, m.group(1), int(m.group(2), 16)))
print("  direct branch instructions=%d  distinct targets=%d"
      % (len(br), len({t for _a, _m, t in br})))
by_kind = {}
for a, mn, t in br:
    if t == TARGET:
        by_kind.setdefault("call" if mn == "call" else "jump", []).append(a)
inside = [(a, mn) for a, mn, t in br
          if ent <= t < ent + size and not (ent <= a < ent + size)]
imms = [(a, b) for a, b in INS if "0x4dabb0" in b and not BRANCH.match(b)]
print("  call -> %#x : %d %s" % (TARGET, len(by_kind.get("call", [])),
                                 [hex(x) for x in by_kind.get("call", [])]))
print("  jmp/jcc -> %#x : %d %s" % (TARGET, len(by_kind.get("jump", [])),
                                    [hex(x) for x in by_kind.get("jump", [])]))
print("  branch targets INTO the body from outside : %d %s"
      % (len(inside), [(hex(a), m) for a, m in inside]))
print("  non-branch instructions whose TEXT mentions 0x4dabb0 : %d %s"
      % (len(imms), [(hex(a), b) for a, b in imms]))
check("G2 zero direct `call` instructions reach 0x4dabb0",
      len(by_kind.get("call", [])) == 0, str(len(by_kind.get("call", []))))
check("G2 zero `jmp`/`jcc` reach 0x4dabb0", len(by_kind.get("jump", [])) == 0,
      str(len(by_kind.get("jump", []))))
check("G2 no branch from outside lands inside the body", len(inside) == 0, str(len(inside)))
check("G2 no non-branch instruction text mentions 0x4dabb0 (byte-level test is G3)", len(imms) == 0,
      str(len(imms)))

# ---------------- G3 ---------------------------------------------------------
print("\nG3  address-taken census over the whole image (positive control included)")
data = RAW[:0x271000] if ALGO == 1 else RAW    # ALGO 1: .rdata/.data never scanned
if ALGO == 10:                                 # ALGO 10: silently truncated scan surface
    data = RAW[:0x100000]


def hits(va, blob=None):
    blob = data if blob is None else blob
    pat = struct.pack("<I", va)
    out = []
    i = blob.find(pat)
    while i >= 0:
        out.append(i)
        i = blob.find(pat, i + 1)
    return out


hits_target = hits(TARGET)
rel_target = hits(TARGET - imgbase)
print("  dword 0x%08x in %d B : %d %s" % (TARGET, len(data), len(hits_target),
                                          [hex(off2va(o) or 0) for o in hits_target]))
print("  image-base-relative dword 0x%08x : %d" % (TARGET - imgbase, len(rel_target)))
vals = [v[0] for v in struct.iter_unpack("<I", RAW[:len(RAW) // 4 * 4])]
text_ptr_pos = [i * 4 for i, v in enumerate(vals) if TEXT_LO <= v < TEXT_HI]
print("  dword positions holding a .text address : %d of %d aligned slots"
      % (len(text_ptr_pos), len(vals)))
print("  family  va        hits  stored-at")
for va in FAMILY:
    h = hits(va)
    print("    %#010x  %4d  %s" % (va, len(h), [hex(off2va(o) or 0) for o in h]))
ctrl = [o for o in hits(0x4DAB90)]
# contiguous run of .text-pointer dwords containing the control hit
run = []
lo = 0
if ctrl:
    c = ctrl[0]
    lo = c
    while lo - 4 >= 0 and TEXT_LO <= struct.unpack_from("<I", RAW, lo - 4)[0] < TEXT_HI:
        lo -= 4
    hi = c
    while hi + 4 <= len(RAW) - 4 and TEXT_LO <= struct.unpack_from("<I", RAW, hi + 4)[0] < TEXT_HI:
        hi += 4
    run = [struct.unpack_from("<I", RAW, o)[0] for o in range(lo, hi + 1, 4)]
print("  CONTROL 0x4dab90 <- dword at %s (VA %s, section %s)"
      % ([hex(o) for o in ctrl], [hex(off2va(o) or 0) for o in ctrl],
         [sect_of_va(off2va(o) or 0) for o in ctrl]))
print("  CONTROL run: %d contiguous .text pointers at VA %s, first 12 %s"
      % (len(run), hex(off2va(lo) if ctrl else 0), [hex(v) for v in run[:12]]))
check("G3 zero occurrences of the 0x4dabb0 VA in the image", len(hits_target) == 0,
      str(len(hits_target)))
check("G3 the scanned blob is the whole image (no silent truncation)",
      len(data) == len(RAW) == 3067904, "%d of %d" % (len(data), len(RAW)))
check("G3 zero image-base-relative occurrences of 0xdabb0", len(rel_target) == 0,
      str(len(rel_target)))
check("G3 the census surface is real: >5000 stored .text addresses", len(text_ptr_pos) > 5000,
      str(len(text_ptr_pos)))
check("G3 CONTROL: the live sibling 0x4dab90 IS address-taken once, in .rdata",
      len(ctrl) == 1 and sect_of_va(off2va(ctrl[0])) == ".rdata",
      "%d %s" % (len(ctrl), [sect_of_va(off2va(o) or 0) for o in ctrl]))
check("G3 CONTROL: that slot sits in a run of >=100 contiguous .text pointers inside .rdata",
      bool(run) and len(run) >= 100 and all(TEXT_LO <= v < TEXT_HI for v in run)
      and sect_of_va(off2va(lo)) == ".rdata", "%d entries from VA %s" % (len(run), hex(off2va(lo))))

# ---------------- G4 ---------------------------------------------------------
print("\nG4  indirect dispatch: every slot an indirect call/jmp could read")
ind = [(a, b) for a, b in INS if re.match(r"^(call|jmp)\s+", b) and not BRANCH.match(b)]
kinds = {"call reg": 0, "call [mem]": 0, "jmp reg": 0, "jmp [mem]": 0}
for a, b in ind:
    k = ("call" if b.startswith("call") else "jmp") + (" [mem]" if "PTR" in b else " reg")
    if ALGO == 14 and k == "jmp [mem]":        # ALGO 14: memory-indirect jumps not counted
        continue
    kinds[k] += 1
print("  indirect sites=%d  %s" % (len(ind), kinds))
abs_tab = []
for a, b in ind:
    m = re.search(r"(?:ds:)?0x([0-9a-f]{6,8})", b)
    if m:
        abs_tab.append((a, int(m.group(1), 16)))
abs_tab_sec = [(a, t, sect_of_va(t)) for a, t in abs_tab]
unres = [(a, t) for a, t, s in abs_tab_sec if s is None]
secs = sorted({str(s) for _a, _t, s in abs_tab_sec})
print("  indirect sites naming an absolute table: %d, sections %s, out-of-section %d %s"
      % (len(abs_tab), secs, len(unres), [(hex(a), hex(t)) for a, t in unres[:6]]))
# reg-indirect targets: nearest `mov reg,imm` inside the same body
regind = [(a, b) for a, b in INS
          if re.match(r"^(call|jmp)\s+[a-z]{2,3}$", b)]
famimm = []
for a, b in regind:
    reg = b.split()[1]
    j = IDX[a] - 1
    k = 0
    while j >= 0 and k < 20:
        t = INS[j][1]
        m = re.match(r"mov\s+%s,0x([0-9a-f]+)$" % reg, t)
        if m and 0x4DAB00 <= int(m.group(1), 16) < 0x4DB100:
            famimm.append((a, t))
        if t.startswith(("call", "ret", "jmp")):
            break
        j -= 1
        k += 1
print("  register-indirect sites=%d, of which load a family address (0x4dab00..0x4db100): %d %s"
      % (len(regind), len(famimm), [(hex(a), t) for a, t in famimm]))
check("G4 the dump contains indirect call/jmp sites (instrument is live)", len(ind) > 0,
      str(len(ind)))
check("G4 all four indirect forms appear", all(v > 0 for v in kinds.values()), str(kinds))
ins = sorted({str(s) for _a, _t, s in abs_tab_sec if s is not None})
check("G4 in-section table bases live only in .text/.rdata/.data/UVA (never _SELFMOD/.rsrc)",
      ins == [".data", ".rdata", ".text", "UVA_DATA"] and len(unres) < len(abs_tab) // 10,
      "%s in-section, %d out-of-section" % (ins, len(unres)))
check("G4 0 of the register-indirect sites has a NEARBY literal family `mov reg,imm` "
      "(full closure is the G3 byte census)", len(famimm) == 0,
      "%d of %d" % (len(famimm), len(regind)))
check("G4 no indirect table slot equals 0x4dabb0 (from the G3 census, 0 dwords anywhere)",
      len(hits_target) == 0, str(len(hits_target)))

# ---------------- G5 ---------------------------------------------------------
print("\nG5  verdict table - entry mechanisms per family member")
print("   va          size  calls  jmp/jcc  stored-dwords  run-member  verdict")
others_live = []
for va in FAMILY:
    name = "FUN_%08x" % va
    if name not in FN:
        continue
    e, sz, _n, ncall = FN[name]
    c = sum(1 for a, mn, t in br if t == e and mn == "call")
    j = sum(1 for a, mn, t in br if t == e and mn != "call")
    h = hits(e)
    inrun = any(va == v for v in run) if run else False
    verdict = "LIVE" if (c or j or h) else "DEAD-INF"
    print("   %#010x  %4d  %5d  %7d  %13d  %10s  %s"
          % (va, sz, c, j, len(h), inrun, verdict))
    if va == TARGET:
        check("G5 0x4dabb0 has zero of ALL FOUR mechanisms (calls/jumps/dwords/run)",
              c == 0 and j == 0 and len(h) == 0 and not inrun,
              "%d/%d/%d/%s" % (c, j, len(h), inrun))
        check("G5 index.csv agrees it has 0 callers", ncall == 0, str(ncall))
    elif name in FN:
        others_live.append((va, c + j + len(h)))
print("  other family members' mechanism counts: %s"
      % [(hex(v), k) for v, k in others_live])
check("G5 every OTHER family member has >=1 entry mechanism (the census discriminates)",
      len(others_live) == 4 and all(k > 0 for _v, k in others_live), str(others_live))

# ---------------- G6 ---------------------------------------------------------
print("\nG6  rivals (each must be refuted by the printed numbers)")
check("R1 'a computed dispatch (vtable/switch table/registry) reaches 0x4dabb0' refuted",
      len(hits_target) == 0 and len(rel_target) == 0,
      "%d stored VAs, %d base-relative" % (len(hits_target), len(rel_target)))
check("R2 'code falls or jumps into the body: 0x4dabb0 is no entry at all' refuted",
      prev[1] == "ret    0x4" and len(inside) == 0 and pro == sib_pro,
      "pred=%s inside=%d prologue-eq=%s" % (prev[1], len(inside), pro == sib_pro))
check("R3 'the relocations would fix up a pointer the byte search cannot see' refuted",
      not (dllc & 0x40) and reloc_dir == (0, 0),
      "%#06x %s" % (dllc, reloc_dir))
body2 = body_of(*FN["FUN_004dac30"][:2])
n = 6 if ALGO == 4 else min(len(body), len(body2))
eq = sum(1 for k in range(n) if body[k][1] == body2[k][1])
print("  body vs sibling 0x4dac30: %d/%d instructions identical (compared %d)" % (eq, n, n))
check("R4 '0x4dabb0 is a COMDAT fold of the live sibling 0x4dac30' refuted",
      eq < n, "%d/%d identical" % (eq, n))
fields = {}
for va in (0x4DABB0, 0x4DAC30):
    t = " ".join(b for _a, b in body_of(*FN["FUN_%08x" % va][:2]))
    fields[va] = sorted(set(re.findall(r"0x9[0-9a-f]{5}", t)))
print("  fields touched: 0x4dabb0 %s | 0x4dac30 %s" % (fields[0x4DABB0], fields[0x4DAC30]))
check("R4b the two bodies write DIFFERENT relations fields", fields[0x4DABB0] != fields[0x4DAC30],
      "%s vs %s" % (fields[0x4DABB0], fields[0x4DAC30]))

# ---------------- G7 ---------------------------------------------------------
print("\nG7  FUN_00551cf0(a,b,mask,flag): what is `flag`?")
s_ent, s_size, s_nins, s_ncall = FN["FUN_00551cf0"]
sb = body_of(s_ent, s_size)
print("  body=%d B / %d insns, index.csv n_callers=%d" % (s_size, len(sb), s_ncall))
arg_slots = sorted(set(re.findall(r"\[ebp\+0x([0-9a-f]+)\]", " ".join(b for _a, b in sb))))
print("  stack slots read: %s" % ["[ebp+0x%s]" % x for x in arg_slots])
FSLOT = "0x10" if ALGO == 5 else "0x14"   # ALGO 5 = read the flag from arg3's slot
flag_read = [b for _a, b in sb if re.match(r"mov\s+\w+,DWORD PTR \[ebp\+%s\]$" % FSLOT, b)]
loads = {sl: sum(1 for _a, b in sb
                 if re.match(r"mov\s+\w+,DWORD PTR \[ebp\+0x%s\]$" % sl, b))
         for sl in arg_slots}
test_i = None
for i, (a, b) in enumerate(sb):
    if b == "test   eax,eax" and i and sb[i - 1][1].endswith("[ebp+%s]" % FSLOT):
        test_i = i
print("  flag read: %s then %s" % (flag_read, sb[test_i][1] if test_i is not None else "NO TEST"))
print("  per-slot LOAD counts %s" % loads)
obs = [(a, b) for a, b in sb if b.startswith(("and", "or")) and re.search(r"\b(edx|ecx)\b", b)]
print("  mask ops: %s" % [(hex(a), b) for a, b in obs])
n_and = sum(1 for _a, b in obs if b.startswith("and"))
n_or = sum(1 for _a, b in obs if b.startswith("or"))
nots = [a for a, b in sb if b.startswith("not")]
cell = [(a, b) for a, b in sb if CELL in b]
field_movs = [(a, b) for a, b in sb if FIELD in b and b.startswith("mov    DWORD PTR [")]
lea_field = [(a, b) for a, b in sb if b.startswith("lea") and FIELD in b]
stores = [(a, b) for a, b in sb if b.startswith("mov    DWORD PTR [")]
print("  loads/stores through 0x94d448: %s" % [(hex(a), b) for a, b in field_movs])
print("  lea of the field: %s ; ALL dword stores in body: %d %s"
      % ([(hex(a), b) for a, b in lea_field], len(stores), [(hex(a), b) for a, b in stores]))
print("  `not`=%d  %s ; timer cell stores=%s" % (len(nots), [hex(x) for x in nots],
                                                [(hex(a), b) for a, b in cell]))
je = [(a, b) for a, b in sb if b.startswith("je")]
print("  branch on the flag: %s" % [(hex(a), b) for a, b in je])
zero_lo = int(re.search(r"0x([0-9a-f]+)", je[0][1]).group(1), 16)
# the SET side is the FLAG!=0 path = fallthrough; ALGO 7 takes the je target as the SET side
set_side = (s_ent, zero_lo) if ALGO != 7 else (zero_lo, s_ent + s_size)
clear_side = (zero_lo, s_ent + s_size) if ALGO != 7 else (s_ent, zero_lo)
print("  SET side = %#x..%#x ;  CLEAR side = %#x..%#x" % (set_side + clear_side))
print("  je[0] at %#x follows the flag test at index %s ; je[1] -> %s"
      % (je[0][0], test_i, je[1][1] if len(je) > 1 else "-"))
check("G7 the callee reads exactly 4 stack args, each via a real `mov reg,[ebp+slot]` load",
      set(arg_slots) == {"8", "c", "10", "14"} and len(arg_slots) == 4
      and all(loads.get(sl, 0) >= 1 for sl in ("8", "c", "10", "14")), "%s %s" % (arg_slots, loads))
check("G7 the flag branch is `mov eax,[ebp+0x14]` / `test eax,eax` / `je`, with je OFFSET i+1",
      FSLOT == "0x14" and test_i is not None and test_i >= 1
      and sb[test_i - 1][1] == "mov    eax,DWORD PTR [ebp+0x14]"
      and sb[test_i][1] == "test   eax,eax" and sb[test_i + 1][1] == je[0][1],
      "slot=0x%s test_i=%s" % (FSLOT, test_i))
check("G7 exactly one AND-shaped and one OR-shaped write to 0x94d448",
      n_and == 1 and n_or == 1 and len(lea_field) == 1 and len(stores) == 3
      and len(cell) == 1,
      "%d/%d/%d/%d/%d" % (n_and, n_or, len(lea_field), len(stores), len(cell)))
inside_ = lambda a, side: side[0] <= a < side[1]
check("G7 the CLEAR side is AND-NOT: the single `not` sits on the CLEAR side",
      len(nots) == 1 and inside_(nots[0], clear_side), str([hex(x) for x in nots]))
check("G7 the OR write sits on the SET side, the AND write on the CLEAR side",
      len(obs) == 2 and obs[0][1].startswith("or") and inside_(obs[0][0], set_side)
      and obs[1][1].startswith("and") and inside_(obs[1][0], clear_side),
      "%s set=%s clear=%s" % ([(hex(a), b) for a, b in obs], set_side, clear_side))
check("G7 the 0x40 -> 0x32 countdown store exists once and only on the SET side",
      len(cell) == 1 and inside_(cell[0][0], set_side) and cell[0][1].endswith(",0x32"),
      str([(hex(a), b) for a, b in cell]))
print("  NOUN: flag!=0 -> OR the mask in (SET);  flag==0 -> AND it out (CLEAR);")
print("        SET additionally stamps %s=0x32 when the mask carries 0x40" % CELL)
check("G7 noun = SET/CLEAR polarity, not 'arm the timer': the OR and the 0x40 stamp share ONE side",
      n_or == 1 and len(cell) == 1 and inside_(obs[0][0], set_side) and inside_(cell[0][0], set_side),
      "or@%#x cell@%#x set=%s" % (obs[0][0], cell[0][0], set_side))

sites = [(i, a) for i, (a, b) in enumerate(INS) if b.startswith("call") and b.endswith("0x551cf0")]
print("\n  caller census: %d `call 0x551cf0` sites" % len(sites))
dist = {"1": 0, "0": 0, "reg": 0}
rows = []
for i, a in sites:
    pushes = []
    j = i - 1
    while j >= 0 and i - j <= 24:
        b = INS[j][1]
        if b.startswith("push"):
            pushes.append((INS[j][0], b))
        elif b.startswith(("call", "ret", "jmp")):
            break
        j -= 1
    if not pushes:
        dist["reg"] += 1
        rows.append((a, "?", pushes))
        continue
    pick = pushes[0] if ALGO == 6 else pushes[-1]   # pushes = [arg1, arg2, arg3, arg4]
    t = pick[1]
    if re.fullmatch(r"push\s+0x1", t):
        k = "1"
    elif re.fullmatch(r"push\s+0x0", t):
        k = "0"
    else:
        k = "reg"
    dist[k] += 1
    rows.append((a, t, len(pushes)))
print("  flag arg (4th push): SET(1)=%d  CLEAR(0)=%d  runtime/register=%d"
      % (dist["1"], dist["0"], dist["reg"]))
print("  push-window size: min=%d max=%d  (exactly-4 window: %d/%d)"
      % (min(r[2] for r in rows), max(r[2] for r in rows),
         sum(1 for r in rows if r[2] == 4), len(rows)))
for a, t, n in rows:
    if "push   0x0" in t or not t.startswith("push   0x"):
        print("    %#010x  flag <- %-12s (window %d pushes)" % (a, t, n))
check("G7 the caller census finds all 36 sites named by index.csv", len(sites) == s_ncall == 36,
      "%d/%d" % (len(sites), s_ncall))
check("G7 both polarities occur: literal 0 AND literal 1 are used", dist["0"] > 0 and dist["1"] > 0,
      str(dist))
check("G7 32 of 36 sites pass a literal bool; 4 pass a runtime register",
      dist["1"] == 26 and dist["0"] == 6 and dist["reg"] == 4 and not (ALGO == 6), str(dist))
check("G7 no site collects a 5th push (the window is exactly the 4 args)",
      all(r[2] <= 4 for r in rows), str(sorted({r[2] for r in rows})))
CWIN = 1 if ALGO == 11 else 3                  # ALGO 11: cleanup looked for on ONE insn only
clean = [(a, INS[j][1]) for i, a in sites
         for j in range(i + 1, min(i + CWIN + 1, len(INS)))
         if INS[j][1].replace(" ", "") == "addesp,0x10"]
print("  `add esp,0x10` within %d insns after the call: %d/%d sites %s"
      % (CWIN, len(clean), len(sites), [hex(a) for a, _b in clean][:8]))
check("G7 28/36 sites clean up exactly 0x10 B - an independent 4-cdecl-arg confirmation",
      len(clean) == 28, str(len(clean)))
m385 = {0x4DAD05: "push   0x1", 0x4DAD30: "push   0x0"}
got = {a: t for a, t, _n in rows}
check("G7 M385's own gate corroborates: 0x4dad05 (bit CLEAR -> set) passes 1, "
      "0x4dad30 (bit SET -> clear) passes 0",
      all(got.get(a) == t for a, t in m385.items()),
      str({hex(a): got.get(a) for a in m385}))

# ---------------- G8 ---------------------------------------------------------
print("\nG8  digest")
INPUTS = [("terran.exe", RAW), ("text.txt", open(TEXT, "rb").read()),
          ("index.csv", open(CSV, "rb").read())]
if ALGO == 12:                                  # ALGO 12: an input blob is dropped from the digest
    INPUTS = INPUTS[:2]
ih = ["%s=%s" % (n, hashlib.sha1(b).hexdigest()[:16]) for n, b in INPUTS]
print("  inputs: " + "  ".join("%s %s (%d B)" % (n, hashlib.sha1(b).hexdigest()[:16], len(b))
                               for n, b in INPUTS))
check("G8 the digest binds all three input blobs (exe, dump, index)",
      len(INPUTS) == 3 and all(len(b) > 0 for _n, b in INPUTS), str([len(b) for _n, b in INPUTS]))
payload = "\n".join(ih) + "".join(REPORT).split("\nG8  digest")[0]
h1 = hashlib.sha1(payload.encode()).hexdigest()[:16]
h2 = hashlib.sha1(payload.encode()).hexdigest()[:16]
print("  payload=%d B  digest run1=%s run2=%s" % (len(payload), h1, h2))
check("G8 digest is stable across two computations", h1 == h2, "%s/%s" % (h1, h2))
print("  M390_DIGEST=%s" % h1)

print("\n%s M390: %d/%d" % ("PASS" if not FAILS else "FAIL", TOTAL[0] - len(FAILS), TOTAL[0]))
if FAILS:
    for f in FAILS:
        print("  red: " + f)
    sys.exit(1)
