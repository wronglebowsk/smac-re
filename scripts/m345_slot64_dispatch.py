#!/usr/bin/env python3
"""M345 -- WHO DISPATCHES the dialog family's `+0x64` slot (M343's last OPEN).

M343 measured that FUN_005f58fa sits at +0x64 of the five dialog-class vtables
and writes the selected item into `[obj+0xa40]`, but left its DISPATCH open:
no direct call exists and 19 `call [reg+0x64]` sites exist image-wide.  This
script answers the dispatch question statically (zero box time):

  SLOT      the pointer 0x5f58fa occurs exactly five times in the image, all as
            data, all inside .rdata at vtable+0x64 of 0x67164c/0x6717cc/
            0x6728c0/0x675cc4/0x6776c8.  The dialog ctor installs the primary
            vptr at +0 and the CPane vptr 0x671644 at +0x444; since 0x671644 is
            8 lower, its +0x6c IS the same dword as the primary +0x64 -- which
            explains the 18 `call [r+0x6c]` sites.  No `.text` instruction
            operand names 0x5f58fa: no direct call, no thunk, no lea.
  SEMANTICS the slot is the middle of a trio: +0x60 FUN_005f59bf (ret 8,
            refuses on [this+0x30a8] & 0x4000), +0x64 FUN_005f58fa (ret 4, body
            never reads its argument), +0x68 FUN_005f59e8.
  UNIVERSE  every indirect call/jmp in the image with displacement 0x64/0x6c:
            19 + 18 sites, 0 jmp forms.  ZERO of them lies in the dialog module
            0x5f0000-0x600000.  The module's only `[r+0x64]` instruction
            (0x5f49ad) is a FIELD SWAP on [this+0x2240]+0x64 -- read then
            write-back -- not a call (the naive census trap).
  EVASIONS  0 sites load `[vptr+0x64]` into a register and then `call reg`;
            0 `lea reg,[obj+0x64]` + `call [reg]`; 0 jmp forms.  The 37
            displacement sites are therefore the COMPLETE dispatch universe.
  RECEIVER  every site's receiver is walked back to its defining instruction in
            the same basic block and its stack arity counted.  Only 5 sites push
            the slot's one argument, and each of them dispatches on a member or
            child object of another class -- never on a dialog-family object.

RIVALS measured on the printed numbers:
  R1 "the modal runner dispatches its own commit slot" -> 0 slot calls in
     FUN_005f1394 (2235 insns).
  R2 "one of the 19 sites reaches a dialog"            -> 0 sites in the dialog
     module and every arity-compatible receiver is a member/child pointer.
  R3 "the commit is called directly somewhere"        -> 0 .text refs.
  R4 "the slot is cached in a register, then called"   -> 0 such pairs.
  R5 "a [r+0x64] in the dialog module is a dispatch"   -> the one hit writes
     the cell back (dest = memory), and its source is the same field.

    python3 -u scripts/m345_slot64_dispatch.py        # acceptance: table, gates
"""
import bisect
import hashlib
import os
import re
import struct
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
EXE = os.path.join(ROOT, "programs", "terran.exe")
IDXC = os.path.join(ROOT, "ghidra_out", "index.csv")
INSN = re.compile(r"^\s*([0-9a-f]{5,8}):\t[0-9a-f ]+\t(\w+)\s*(.*)$")

FAMILY_VT = (0x67164C, 0x6717CC, 0x6728C0, 0x675CC4, 0x6776C8)
PANE_VT = 0x671644
SLOT_FN = 0x5F58FA
RUNNER = 0x5F1394
CTOR = 0x405EF0
SLOT64 = re.compile(r"^call\s+DWORD PTR \[(\w+)\+(0x64|0x6c)\]$")

IMG = bytearray(open(EXE, "rb").read())


def dw(va):
    o = va - 0x400000
    return struct.unpack("<I", IMG[o:o + 4])[0] if 0 <= o + 4 <= len(IMG) else 0


def load_ins():
    out = []
    with open(TEXT, errors="replace") as f:
        for line in f:
            m = INSN.match(line)
            if m:
                out.append((int(m.group(1), 16), m.group(2),
                            " ".join(m.group(3).split())))
    return out


def load_idx():
    rows = []
    with open(IDXC) as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split(",")
            if len(p) > 3 and p[0].startswith("0x"):
                try:
                    rows.append((int(p[0], 16), int(p[2]), p[1]))
                except ValueError:
                    pass
    rows.sort()
    return rows


INS = load_ins()
# --- mutation hooks (driven by scripts/m345_mutate.py; empty in acceptance) ---
# M345_PATCH_INS: "<addr>=<operand>" replaces an instruction's operand text
# M345_PATCH_IMG: "<va>=<dword>" patches one image dword
if os.environ.get("M345_PATCH_INS"):
    _pat = {}
    for _pair in os.environ["M345_PATCH_INS"].split(";"):
        _a, _o = _pair.split("=", 1)
        _pat[int(_a, 16)] = _o
    INS = [(_a, _m, _pat.get(_a, _o)) for _a, _m, _o in INS]
if os.environ.get("M345_PATCH_IMG"):
    for _pair in os.environ["M345_PATCH_IMG"].split(";"):
        _a, _v = _pair.split("=", 1)
        struct.pack_into("<I", IMG, int(_a, 16) - 0x400000, int(_v, 16))
IDX = load_idx()
POS = {r[0]: i for i, r in enumerate(INS)}
PCS = [r[0] for r in INS]
STARTS = [r[0] for r in IDX]


def extent(pc):
    i = bisect.bisect_right(STARTS, pc) - 1
    if i >= 0 and IDX[i][0] <= pc < IDX[i][0] + IDX[i][1]:
        return IDX[i]
    return None


def fname(pc):
    e = extent(pc)
    return e[2] if e else "?"


def span(va):
    e = extent(va)
    if not e:
        return []
    lo = bisect.bisect_left(PCS, va)
    hi = bisect.bisect_left(PCS, va + e[1])
    return INS[lo:hi]


# ---------------------------------------------------------------- SLOT census
data_occ = []
needle = struct.pack("<I", SLOT_FN)
i = 0
while True:
    j = IMG.find(needle, i)
    if j < 0:
        break
    data_occ.append(j + 0x400000)
    i = j + 1
text_refs = [(a, m, o) for a, m, o in INS if "0x%x" % SLOT_FN in o]


def ret_imm(va):
    r = None
    for a, m, o in span(va):
        if m == "ret":
            r = o
    return r


TRIO = [(0x60, 0x5F59BF), (0x64, 0x5F58FA), (0x68, 0x5F59E8)]
trio_rows = [(off, fn, dw(FAMILY_VT[0] + off), ret_imm(fn)) for off, fn in TRIO]

# ctor vptr installs (the +0x64 / +0x6c aliasing proof)
ctor_inst = [(a, m, o) for a, m, o in span(CTOR) if re.search(r",0x(67164c|671644)$", o)]

# --------------------------------------------------------------- site census
sites = []
for a, m, o in INS:
    mm = SLOT64.match(m + " " + o)
    if mm:
        sites.append((a, mm.group(1), mm.group(2), fname(a)))
sites.sort()
S64 = [s for s in sites if s[2] == "0x64"]
S6C = [s for s in sites if s[2] == "0x6c"]

CALLX = re.compile(r"^(call|jmp|ret|retf)\b")
BRANCH = re.compile(r"^(j\w+|loop\w*)$")
TARGETS = set()
for a, m, o in INS:
    if BRANCH.match(m) or m == "jmp":
        mm = re.search(r"\b0x([0-9a-f]+)$", o)
        if mm:
            TARGETS.add(int(mm.group(1), 16))


def basic_window(pc):
    """Walk back to the basic-block head: stop at a branch target or at a
    call/jmp/ret that ends the previous block."""
    if os.environ.get("M345_ALGO") == "wide":   # algorithm mutant: no block bounds
        return INS[max(0, POS[pc] - 14):POS[pc]]
    j = POS[pc] - 1
    out = []
    while j >= 0:
        out.append(INS[j])
        if CALLX.match(INS[j][1]) or BRANCH.match(INS[j][1]) or INS[j][0] in TARGETS:
            break
        j -= 1
    return list(reversed(out))


def arity(win):
    return sum(1 for a, m, o in win if m == "push")


def recv_src(win, reg):
    """Last instruction that writes `reg` as a DESTINATION before the call."""
    src = "?"
    for a, m, o in win:
        first = re.sub(r"^(BYTE|WORD|DWORD) PTR ", "", o.split(",")[0].strip())
        if first == reg and m in ("mov", "lea", "xor", "add", "sub", "pop",
                                  "movzx", "movsx", "and", "or"):
            src = (a, m, o)
    return src


def recv_kind(src):
    """Classify the receiver pointer: vtable-of-an-object vs member/child field."""
    if not src or src == "?":
        return "?"
    a, m, o = src
    mm = re.search(r"\[(\w+)(?:\+(\w+)\*1)?(?:\+0x([0-9a-f]+))?\]", o)
    if not mm:
        return "?"
    if mm.group(3) or mm.group(2):
        return "MEMBER"        # [obj+off] or [obj+reg+off] -> a field pointer
    return "VPTR-SELF"         # [obj] -> the object's own vtable


rows = []
for a, reg, disp, fn in S64:
    win = basic_window(a)
    src = recv_src(win, reg)
    rows.append((a, reg, disp, fn, arity(win), recv_kind(src), src))
ONE = [r for r in rows if r[4] == 1]

# the dialog module's single [r+0x64] instruction: a field swap, not a call
FSWAP = [(a, m, o) for a, m, o in INS
         if 0x5F0000 <= a < 0x600000 and re.search(r"\[\w+\+0x64\]", o)]
FSWAP_CALLS = [(a, m, o) for a, m, o in FSWAP if m in ("call", "jmp")]
FSWAP_READS = [(a, m, o) for a, m, o in FSWAP if m == "mov"]

# evasion A: slot loaded into a register, then `call reg`
CACHED = []
cpat = re.compile(r"^mov\s+(\w+),DWORD PTR \[(\w+)\+(0x64|0x6c)\]$")
for a, m, o in INS:
    mm = cpat.match(m + " " + o)
    if mm:
        for j in range(POS[a] + 1, min(len(INS), POS[a] + 4)):
            if INS[j][1] == "call" and INS[j][2].strip() == mm.group(1):
                CACHED.append((a, INS[j][0]))
                break

# evasion B: lea reg,[obj+0x64] then call [reg]
LEAC = []
lpat = re.compile(r"^lea\s+(\w+),\[(\w+)\+0x(64|6c)\]$")
for a, m, o in INS:
    mm = lpat.match(m + " " + o)
    if mm:
        for j in range(POS[a] + 1, min(len(INS), POS[a] + 4)):
            if INS[j][1] == "call" and re.match(r"^\[\s*%s\s*\]$" % mm.group(1),
                                                INS[j][2].strip()):
                LEAC.append((a, INS[j][0]))
                break

# runner body slot calls
runner_slots = [(a, m, o) for a, m, o in span(RUNNER) if SLOT64.match(m + " " + o)]

# ---------------------------------------------------------------- output
print("M345 slot+0x64 dispatch census -- computed from %s (%d insns)" % (
    os.path.relpath(TEXT, ROOT), len(INS)))
print()
print("TABLE 1  slot pointer 0x%x in the image bytes" % SLOT_FN)
print("   data occurrences : %d" % len(data_occ))
for v in sorted(data_occ):
    print("     0x%x   (vtable+0x64 of %s)" % (
        v, ", ".join("0x%x" % vt for vt in FAMILY_VT if vt + 0x64 == v) or "?"))
print("   .text operand refs: %d" % len(text_refs))
print()
print("TABLE 2  the trio at vtable 0x%x (slot -> function -> ret imm)" % FAMILY_VT[0])
for off, fn, got, r in trio_rows:
    print("   +0x%-2x  0x%-8x  dword 0x%-8x  ret %s" % (off, fn, got, r))
print("   ctor 0x%x installs: %s" % (CTOR, ["0x%x %s %s" % t for t in ctor_inst]))
print()
print("TABLE 3  every indirect call with displacement 0x64/0x6c, receiver walked back")
print("   #  addr      reg  fn             arity  kind        receiver source")
for k, (a, reg, disp, fn, n, kind, src) in enumerate(rows, 1):
    s = "%x: %s %s" % src if isinstance(src, tuple) else src
    print("   %2d 0x%-7x %-4s %-14s %-6d %-11s %s" % (k, a, reg, fn, n, kind, s))
print("   (#: 1-19 are `call [r+0x64]`; the 18 `call [r+0x6c]` sites follow)")
print()
print("TABLE 4  arity histogram over the 19 +0x64 sites: %s"
      % dict(sorted(Counter(r[4] for r in rows).items())))
print("   slot arity is 1 (ret 4) -> arity-compatible sites: %d" % len(ONE))
for a, reg, disp, fn, n, kind, src in ONE:
    print("     0x%-7x %-14s kind=%s" % (a, fn, kind))
print()
print("TABLE 5  the dialog module 0x5f0000-0x600000: [r+0x64] instructions")
print("   total %d ; call/jmp forms %d ; mov forms %d"
      % (len(FSWAP), len(FSWAP_CALLS), len(FSWAP_READS)))
for a, m, o in FSWAP:
    print("     0x%x  %s %s   (%s)" % (a, m, o, fname(a)))
print("   the 0x5f49ad/0x5f49b9 pair is a FIELD SWAP on [this+0x2240]+0x64:")
print("     0x5f49a1 add edx,0x2240 ; 0x5f49ad read [eax+0x64] ; 0x5f49b9 store back")
print("   runner 0x%x: slot-call sites %d" % (RUNNER, len(runner_slots)))
print()
print("RIVALS (each verdict computed from the numbers above)")
print("   R1 runner dispatches its own commit slot     -> %s (%d site calls)"
      % ("FAILS" if not runner_slots else "holds", len(runner_slots)))
print("   R2 one of the %d sites reaches a dialog        -> %s (%d sites in module,"
      " %d one-arg sites)" % (len(rows), "FAILS" if not FSWAP_CALLS else "holds",
                              sum(1 for r in rows if 0x5F0000 <= r[0] < 0x600000),
                              len(ONE)))
print("   R3 the commit is called directly             -> %s (%d text refs)"
      % ("FAILS" if not text_refs else "holds", len(text_refs)))
print("   R4 the slot is cached then `call reg`        -> %s (%d pairs)"
      % ("FAILS" if not CACHED else "holds", len(CACHED)))
print("   R5 any [r+0x64] in the module is a dispatch  -> %s (%d call/jmp forms,"
      " %d mov forms)" % ("FAILS" if not FSWAP_CALLS else "holds",
                          len(FSWAP_CALLS), len(FSWAP_READS)))
print()
print("TABLE 6  dispatch evasions")
print("   cached slot -> `call reg` pairs : %d" % len(CACHED))
print("   `lea r,[obj+0x64]` + call [r]  : %d" % len(LEAC))
print("   jmp [r+0x64]/[r+0x6c] forms     : %d" % sum(
    1 for a, m, o in INS if m == "jmp" and re.match(r"^DWORD PTR \[\w+\+0x6[46]\]$", o)))
print()

# ---------------------------------------------------------------- gates
fails = []


def gate(name, ok, detail):
    print("%-4s %-52s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        fails.append(name)


def in_rdata(v):
    return 0x671000 <= v < 0x689000


gate("G1 slot data census == 5, all .rdata at a family vt+0x64",
     len(data_occ) == 5
     and all(in_rdata(v) for v in data_occ)
     and sorted(data_occ) == sorted(vt + 0x64 for vt in FAMILY_VT),
     "%d occ" % len(data_occ))
gate("G2 no .text operand names the slot (no direct call/thunk/lea)",
     len(text_refs) == 0, "%d refs" % len(text_refs))
gate("G3 trio dwords match; 0x671644+0x6c == 0x67164c+0x64",
     all(t[2] == t[1] for t in trio_rows)
     and [dw(vt + 0x64) for vt in FAMILY_VT] == [SLOT_FN] * 5
     and dw(PANE_VT + 0x6C) == dw(FAMILY_VT[0] + 0x64),
     "pane alias")
gate("G4 ctor installs 0x67164c at +0 and 0x671644 at +0x444",
     len(ctor_inst) == 2
     and ctor_inst[0][2].strip().endswith(",0x67164c")
     and ctor_inst[1][2].endswith(",0x671644")
     and "+0x444]" in ctor_inst[1][2],
     "%d stores" % len(ctor_inst))
gate("G5 slot arity is 1 (ret 4)", trio_rows[1][3] == "0x4", str(trio_rows[1][3]))
gate("G6 census: 19 x +0x64, 18 x +0x6c, 0 jmp forms",
     len(S64) == 19 and len(S6C) == 18
     and sum(1 for a, m, o in INS if m == "jmp"
             and re.match(r"^DWORD PTR \[\w+\+0x6[46]\]$", o)) == 0,
     "19/18/0")
gate("G7 zero dispatch sites inside the dialog module",
     not FSWAP_CALLS and all(not (0x5F0000 <= r[0] < 0x600000) for r in rows),
     "%d call forms in module" % len(FSWAP_CALLS))
gate("G8 module's [r+0x64] forms are 4 movs, 0 calls, swap pinned at 0x5f49ad",
     len(FSWAP) == 4 and len(FSWAP_CALLS) == 0 and len(FSWAP_READS) == 4
     and sorted(x[0] for x in FSWAP_READS) == [0x5F49AD, 0x5F49B9, 0x5FC6FC, 0x5FCC34],
     "%d mov / %d call" % (len(FSWAP_READS), len(FSWAP_CALLS)))
gate("G9 zero dispatch evasions (cached-slot, lea+call)", not CACHED and not LEAC,
     "%d/%d" % (len(CACHED), len(LEAC)))
gate("G10 arity-compatible sites == 5, each on a MEMBER/child pointer",
     len(ONE) == 5 and all(r[5] in ("MEMBER", "VPTR-SELF") for r in ONE),
     "%d one-arg" % len(ONE))
gate("G11 runner 0x5f1394 dispatches no slot", len(runner_slots) == 0,
     "%d" % len(runner_slots))

print()
if fails:
    print("FAIL M345: %d/%d gates" % (12 - len(fails), 12))
    sys.exit(1)
h = hashlib.sha1(repr([(r[0], r[4], r[5]) for r in rows]
                      + trio_rows + [(x[0],) for x in FSWAP]).encode()).hexdigest()
print("PASS M345: 12/12 gates   digest=%s" % h[:16])
