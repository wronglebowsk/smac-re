#!/usr/bin/env python3
"""M343 -- WHO WRITES the dialog result cell `[obj+0xa40]` (the M339 OPEN).

M339 measured: the modal screen runner FUN_005f1394 returns `[obj+0xa40]`,
reads the cell ONCE and writes it 0x -- the writer was left OPEN.  This script
asks one question: which .text functions store into that cell on a DIALOG-class
receiver, and where does the stored value come from?

Measured (all numbers COMPUTED from scratch/m574/text.txt, the whole-image
disassembly, 781,379 insns, plus programs/terran.exe bytes; zero box time):

  CENSUS   every instruction naming displacement 0xa40: 97 refs.  25 are
           INDEXED (`[x+y*1+0xa40]`) -- an array element, not a field -- and are
           excluded with their function named; 72 are FIELD form (all dword:
           47 stores/RMW, 25 reads).  There is NO `lea reg,[...+0xa40]` site in
           the image, so the displacement census is COMPLETE for stores (the
           trap-3 copied-register evasion does not exist at this field).
  CLASS    the two vmethods that write the cell are vtable slots of the dialog
           family, read out of the image bytes: FUN_005f5759 at +0xa8 of
           0x67164c/0x6717cc/0x6728c0 (+0xb0 of the CPane subobject 0x671644)
           and FUN_005f58fa at +0x64 of all six family vtables.
  FINGER   the dialog receiver has a layout fingerprint: it touches both
           [base+0x21d0] (the item container) and [base+0x2350] (the state),
           out of the cluster {0x21d0, 0x2350, 0x30a8, 0x3100}.  Exactly FOUR
           functions with a +0xa40 ref carry the pair: FUN_005f1394 (runner,
           1 read), FUN_005f5759, FUN_005f58fa, FUN_005f5a11.  A looser
           ">=3 of the cluster" filter ADMITS two non-dialog functions.
  WRITERS  three functions, NINE dword stores: 5759 x4, 58fa x3, 5a11 x2.
           Zero in the dialog ctor FUN_00405ef0, zero in the runner.
  IDENTITY the runner publishes ITS OWN object: 0x5f13b2 saves ecx into
           [ebp-0x394], 0x5f3d70 stores that local to ds:0x9977f0, 0x5f3e02
           restores it, and 0x5f3f45 reads [ebp-0x394]+0xa40.  FUN_005f5a11's
           receiver is ds:0x9977f0 -> the same object.
  VALUE    each writer publishes the SELECTED item: the container's +0xec
           dword directly, or FUN_005fdcf7(container) (the resolver 12 other
           functions also call), plus a 0 reset (both vmethods) and one -1
           (5759 only, reached from arg == -2 with [this+0x30a8] & 0x40).

RIVALS measured on the printed numbers:
  R1 "the runner computes its own result" -> 0 stores in 2,235 insns, 1 read.
  R2 "the ctor seeds the result cell"      -> FUN_00405ef0: 0 refs to 0xa40.
  R3 "any +0xa40 field is the same cell"   -> 62/72 field refs fail the pair.
  R4 ">=3 of the cluster is the right filter" -> admits 5 functions (2 wrong).

    python3 -u scripts/m343_a40_writer.py        # acceptance: table then gates
"""
import bisect
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
EXE = os.path.join(ROOT, "programs", "terran.exe")
IDXC = os.path.join(ROOT, "ghidra_out", "index.csv")

DISP = "+0xa40]"
INSN = re.compile(r"^\s*([0-9a-f]{5,8}):\t[0-9a-f ]+\t(\w+)\s*(.*)$")

# dialog family vtables (M214 set + the CPane subobject installed by the ctor)
FAMILY_VT = [(0x67164C, "class 0x67164c"), (0x671644, "CPane subobj 0x671644"),
             (0x6717CC, "class 0x6717cc"), (0x6728C0, "class 0x6728c0"),
             (0x675CC4, "class 0x675cc4"), (0x6776C8, "class 0x6776c8")]
RUNNER, CLICK, SIB64, CALLBACK = (0x5F1394, 0x5F5759, 0x5F58FA, 0x5F5A11)
CTOR = 0x405EF0
RESOLVER = 0x5FDCF7
CLUSTER = ("+0x21d0]", "+0x2350]", "+0x30a8]", "+0x3100]")
REGNAMES = ("eax", "ecx", "edx", "esi", "edi", "ebx")

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
# --- mutation hooks (driven by scripts/m343_mutate.py; empty in the acceptance run) ---
if os.environ.get("M343_PATCH_INS"):
    _pat = {}
    for _pair in os.environ["M343_PATCH_INS"].split(";"):
        _a, _o = _pair.split("=", 1)
        _pat[int(_a, 16)] = _o
    INS = [(_a, _m, _pat.get(_a, _o)) for _a, _m, _o in INS]
if os.environ.get("M343_PATCH_VT"):
    for _pair in os.environ["M343_PATCH_VT"].split(";"):
        _a, _v = _pair.split("=", 1)
        struct.pack_into("<I", IMG, int(_a, 16) - 0x400000, int(_v, 16))
IDX = load_idx()
POS = {r[0]: i for i, r in enumerate(INS)}
PCS = [r[0] for r in INS]
STARTS = [r[0] for r in IDX]
BYADDR = {r[0]: r for r in INS}


def extent(pc):
    i = bisect.bisect_right(STARTS, pc) - 1
    if i >= 0 and IDX[i][0] <= pc < IDX[i][0] + IDX[i][1]:
        return IDX[i]
    return None


def body(ext):
    lo = bisect.bisect_left(PCS, ext[0])
    hi = bisect.bisect_left(PCS, ext[0] + ext[1])
    return INS[lo:hi]


def inner(ops):
    m = re.search(r"\[([^\]]*\+0xa40)\]", ops)
    return m.group(1) if m else ""


def role(mn, ops):
    """objdump is dest-first: is the +0xa40 memory operand the DESTINATION?"""
    mem_first = re.match(r"^(BYTE|WORD|DWORD) PTR \[[^\]]*\+0xa40\]", ops) is not None
    if not mem_first or mn in ("cmp", "test"):
        return "READ"
    if mn in ("or", "and", "xor", "add", "sub", "inc", "dec", "not"):
        return "RMW"
    if mn == "mov":
        return "STORE"
    return "OTHER"


def width(ops):
    if "DWORD PTR" in ops:      # must precede WORD: "DWORD PTR" contains "WORD PTR"
        return 4
    if "WORD PTR" in ops:
        return 2
    if "BYTE PTR" in ops:
        return 1
    return 0


REFS = [(a, m, o) for (a, m, o) in INS if DISP in o]
FIELD = [(a, m, o) for (a, m, o) in REFS if "*" not in inner(o)]
SCALED = [(a, m, o) for (a, m, o) in REFS if "*" in inner(o)]
LEA = [(a, m, o) for (a, m, o) in REFS if m == "lea"]
IMMS = [(a, m, o) for (a, m, o) in INS if re.search(r",0xa40$", o)]  # `add reg,0xa40` evasion
DSTORES = [(a, m, o) for (a, m, o) in FIELD
           if role(m, o) in ("STORE", "RMW") and width(o) == 4]
DLOADS = [(a, m, o) for (a, m, o) in FIELD
          if role(m, o) == "READ" and width(o) == 4]


def fn_name(a):
    e = extent(a)
    return e[2] if e else "?"


# ---------------- receiver attribution ----------------
BY_FN = {}
for a, m, o in FIELD:
    BY_FN.setdefault(fn_name(a), []).append((a, m, o, role(m, o)))
FN_EXT = {fn: extent(lst[0][0]) for fn, lst in BY_FN.items()}


def fp_of(ext):
    b = body(ext)
    return tuple(any(cl in o for _a, _m, o in b) for cl in CLUSTER)


FP = {fn: fp_of(e) for fn, e in FN_EXT.items()}
PAIR = {fn: (fp[0] and fp[1]) for fn, fp in FP.items()}
WRITER_FNS = sorted(fn for fn in BY_FN if PAIR[fn] and any(r in ("STORE", "RMW")
                                                         for *_x, r in BY_FN[fn]))
LOOSE = sorted(fn for fn, fp in FP.items() if sum(fp) >= 3
               and any(r in ("STORE", "RMW") for *_x, r in BY_FN[fn]))
STORE_FNS = sorted(fn for fn in BY_FN if any(r in ("STORE", "RMW") for *_x, r in BY_FN[fn]))


def slot_of(vt, target, cap=400):
    for i in range(cap):
        if dw(vt + 4 * i) == target:
            return 4 * i
    return None


SLOTS = {fn: [(vt, n, slot_of(vt, fn)) for vt, n in FAMILY_VT] for fn in (CLICK, SIB64)}
for fn in SLOTS:
    SLOTS[fn] = [x for x in SLOTS[fn] if x[2] is not None]


# ---------------- value provenance ----------------
def chase(pc, tok, depth=0):
    if depth > 6 or pc not in POS:
        return "UNRESOLVED"
    if re.fullmatch(r"-?0x[0-9a-f]+|-?\d+", tok):
        return "IMM %s" % tok
    i = POS[pc] - 1
    while i >= 0 and POS[pc] - i <= 40:
        a, m, o = INS[i]
        dst = o.split(",")[0].strip()
        if m == "call":
            return "RESOLVER" if o.split()[0] == hex(RESOLVER) else "CALL %s" % o
        if dst == tok:
            if m == "mov":
                src = o.split(",", 1)[1].strip()
                if src.startswith("DWORD PTR [ebp-"):
                    slot = src[len("DWORD PTR "):]
                    j = POS[a] - 1
                    while j >= 0 and POS[a] - j <= 60:
                        if INS[j][1] == "mov" and INS[j][2].startswith("DWORD PTR " + slot + ","):
                            return chase(INS[j][0], INS[j][2].split(",", 1)[1].strip(), depth + 1)
                        j -= 1
                    return "STACK %s" % slot
                if src.startswith("DWORD PTR ["):
                    if "+0xec]" in src or "+0x229c]" in src:
                        return "SELECTED %s" % src.split("[", 1)[1].rstrip("]")
                    return "MEM %s" % src
                if src in REGNAMES:
                    return chase(a, src, depth + 1)
                return "OTHER %s" % src
            return "OTHER %s %s" % (m, o)
        i -= 1
    return "UNRESOLVED"


STORE_DETAIL = []
for fn in WRITER_FNS:
    for a, m, o, r in BY_FN[fn]:
        if r not in ("STORE", "RMW"):
            continue
        STORE_DETAIL.append((a, fn, m, o, chase(a, o.split(",", 1)[1].strip())))
STORE_DETAIL.sort()

# ---------------- TABLE (printed FIRST) ----------------
LINES = []


def p(s=""):
    LINES.append(s)


p("M343 -- the [obj+0xa40] result cell: census, class, writers")
p("image: %d insns parsed; refs naming displacement 0xa40 = %d" % (len(INS), len(REFS)))
p("")
p("A. SHAPE CENSUS")
p("  %-24s %4s" % ("class", "n"))
p("  %-24s %4d" % ("indexed [x+y*1+0xa40]", len(SCALED)))
p("  %-24s %4d  (dword stores %d / reads %d)" % ("field [x+0xa40]", len(FIELD),
                                                 len(DSTORES), len(DLOADS)))
p("  %-24s %4d  (no lea form exists -> store census complete)" % ("lea reg,[x+0xa40]", len(LEA)))
p("")
p("  indexed refs by function (array elements, excluded from the field set):")
idxfn = {}
for a, m, o in SCALED:
    idxfn.setdefault(fn_name(a), []).append(a)
for fn in sorted(idxfn):
    p("    %-14s x%d  @%s" % (fn, len(idxfn[fn]), " ".join("%x" % x for x in idxfn[fn])))
p("")
p("B. CLASS ATTRIBUTION (vtable slots read from the image bytes)")
for fn in (CLICK, SIB64):
    p("  0x%x = %s" % (fn, ", ".join("+0x%x of %s" % (s, n) for _v, n, s in SLOTS[fn])))
p("")
p("C. RECEIVER FINGERPRINT  cluster {+0x21d0 container, +0x2350 state, +0x30a8 flags, +0x3100 stage}")
p("  %-14s %-6s %-6s %-6s %-6s %-4s %5s %5s" % ("function", "21d0", "2350", "30a8", "3100",
                                                "pair", "store", "read"))
for fn in sorted(BY_FN):
    f = FP[fn]
    st = sum(1 for *_x, r in BY_FN[fn] if r in ("STORE", "RMW"))
    rd = sum(1 for *_x, r in BY_FN[fn] if r == "READ")
    p("  %-14s %-6s %-6s %-6s %-6s %-4s %5d %5d" % (fn, f[0], f[1], f[2], f[3],
                                                    "YES" if PAIR[fn] else "no", st, rd))
p("  functions carrying the PAIR: %s" % ", ".join(sorted(k for k in PAIR if PAIR[k])))
p("  WRITERS under the pair: %s" % ", ".join(WRITER_FNS))
p("  WRITERS under '>=3 of cluster': %s (%d)" % (", ".join(LOOSE), len(LOOSE)))
p("")
p("D. THE WRITER SET (every store, with value provenance)")
p("  %-10s %-14s %-5s %-40s %s" % ("addr", "function", "mn", "operand", "value"))
for a, fn, m, o, src in STORE_DETAIL:
    p("  %08x %-14s %-5s %-40s %s" % (a, fn, m, o, src))
p("  total dword stores on the dialog receiver: %d" % len(STORE_DETAIL))
p("")
p("E. RECEIVER IDENTITY (runner frame local -> ds:0x9977f0 -> callback receiver -> read)")
for addr in (0x5F13B2, 0x5F3D3B, 0x5F3D47, 0x5F3D70, 0x5F3E02, 0x5F3F3F, 0x5F3F45, 0x5F5A17):
    if addr in BYADDR:
        m, o = BYADDR[addr][1], BYADDR[addr][2]
        p("  0x%08x %-6s %s" % (addr, m, o))
p("")
p("F. CANCEL CHAIN in FUN_005f5759 (arg = [ebp+0x8])")
for addr in (0x5F57E0, 0x5F57E6, 0x5F57EA, 0x5F57EC, 0x5F57F0, 0x5F57F4, 0x5F57F7,
             0x5F57FD, 0x5F5800, 0x5F581C):
    if addr in BYADDR:
        m, o = BYADDR[addr][1], BYADDR[addr][2]
        p("  0x%08x %-6s %s" % (addr, m, o))
p("")
TABLE = "\n".join(LINES)
print(TABLE)

# ---------------- GATES ----------------
GATES = []


def gate(tag, cond, text, mutant):
    GATES.append((tag, bool(cond), mutant))
    print("%s %s  %s   [mutant %s]" % (tag, "PASS" if cond else "FAIL", text, mutant))


idx_fns = len(set(fn_name(a) for a, _m, _o in SCALED))
gate("G1", len(REFS) == 97 and len(SCALED) == 25 and len(FIELD) == 72
     and len(DSTORES) == 47 and len(DLOADS) == 25 and len(LEA) == 0
     and len(IMMS) == 0 and idx_fns == 12,
     "census: 97 refs = 25 indexed (12 fns) + 72 field (47 stores / 25 reads); 0 lea and 0 `,0xa40` immediate",
     "MU1 (treat the indexed forms as fields)")

slot_ok = ([v for v, _n, _s in SLOTS[CLICK]] == [0x67164C, 0x671644, 0x6717CC, 0x6728C0]
           and [v for v, _n, _s in SLOTS[SIB64]] == [0x67164C, 0x671644, 0x6717CC,
                                                     0x6728C0, 0x675CC4, 0x6776C8]
           and [s for _v, _n, s in SLOTS[CLICK]] == [0xA8, 0xB0, 0xA8, 0xA8]
           and [s for _v, _n, s in SLOTS[SIB64]] == [0x64, 0x6C, 0x64, 0x64, 0x64, 0x64])
gate("G2", slot_ok,
     "class: 0x5f5759 = +0xa8 of the three class vtables (0x671644 carries it at +0xb0); "
     "0x5f58fa = +0x64 of the five class vtables (0x671644 at +0x6c)",
     "MU2 (slot_of returns an off-by-one slot)")

PAIRSET = sorted(k for k in PAIR if PAIR[k])
gate("G3", WRITER_FNS == ["FUN_005f5759", "FUN_005f58fa", "FUN_005f5a11"]
     and PAIRSET == ["FUN_005f1394", "FUN_005f5759", "FUN_005f58fa", "FUN_005f5a11"]
     and len(PAIRSET) == 4
     and len(LOOSE) == 5 and "FUN_005ee350" in LOOSE and "FUN_005eede6" in LOOSE
     and len(STORE_FNS) == 22,
     "fingerprint: the pair admits exactly 3 writers; '>=3 of cluster' wrongly admits 2 more",
     "MU3 (use >=3 of the cluster instead of the pair)")

gate("G4", len(STORE_DETAIL) == 9
     and sum(1 for d in STORE_DETAIL if d[1] == "FUN_005f5759") == 4
     and sum(1 for d in STORE_DETAIL if d[1] == "FUN_005f58fa") == 3
     and sum(1 for d in STORE_DETAIL if d[1] == "FUN_005f5a11") == 2
     and "FUN_00405ef0" not in BY_FN
     and not any(fn_name(a) == "FUN_00405ef0" for a, _m, _o in REFS),
     "writers: 9 stores = 5759 x4 + 58fa x3 + 5a11 x2; the dialog ctor FUN_00405ef0 has 0 refs (ALL 97)",
     "MU4 (count the indexed refs as field stores)")

rrall = [(a, m, o) for a, m, o in REFS if fn_name(a) == "FUN_005f1394"]
rr = BY_FN.get("FUN_005f1394", [])
gate("G5", len(rrall) == 1 and rrall[0][0] == 0x5F3F45
     and role(rrall[0][1], rrall[0][2]) == "READ" and len(rr) == 1,
     "runner FUN_005f1394: 1 ref among ALL 97, a READ at 0x5f3f45, 0 stores",
     "MU5 (role() reads the dest-first mov as a source)")

law = {}
chain_ok = True
for a, fn, m, o, src in STORE_DETAIL:
    law.setdefault(fn, []).append(src.split()[0])
    if src.startswith("SELECTED"):
        w = " | ".join(x[2] for x in INS[POS[a] - 14:POS[a]])
        chain_ok = chain_ok and "+0x8]" in w and "+0xec]" in w and any(
            x[1] in ("add", "lea") and x[2].rstrip().endswith(",0x2228") for x in INS[POS[a] - 14:POS[a]])
    elif src.startswith("RESOLVER"):
        prev, prev2 = INS[POS[a] - 1], INS[POS[a] - 2]
        base = o.split("[", 1)[1].split("+")[0]           # the store's receiver register
        chain_ok = chain_ok and prev2[1] == "call" and prev2[2].split()[0] == hex(RESOLVER)
        chain_ok = chain_ok and prev[2].split(",")[0] == base
        w = " | ".join(x[2] for x in INS[POS[a] - 8:POS[a]])
        chain_ok = chain_ok and "+0x21d0]" in w
gate("G6", law.get("FUN_005f5759") == ["IMM", "SELECTED", "RESOLVER", "IMM"]
     and law.get("FUN_005f58fa") == ["IMM", "SELECTED", "RESOLVER"]
     and law.get("FUN_005f5a11") == ["SELECTED", "RESOLVER"]
     and [s for _a, _f, _m, _o, s in STORE_DETAIL] ==
     ["IMM 0x0", "SELECTED eax+edx*1+0xec", "RESOLVER", "IMM 0xffffffff",
      "IMM 0x0", "SELECTED edx+ecx*1+0xec", "RESOLVER",
      "SELECTED eax+edx*1+0xec", "RESOLVER"]
     and chain_ok,
     "value law: both vmethods publish {0, selected, resolver}; the callback {selected, resolver}; "
     "one -1; every SELECTED store's [this+0x2228] -> [+8] -> +0xec chain and every RESOLVER call adjacency",
     "MU6 (chase stops at the stack slot -> 3 UNRESOLVED)")

LINK = [(0x5F13B2, "DWORD PTR [ebp-0x394],ecx"),     # this saved to the frame local
        (0x5F3D6A, "ecx,DWORD PTR [ebp-0x394]"),     # that local reloaded into ecx
        (0x5F3D70, "DWORD PTR ds:0x9977f0,ecx"),     # and PUBLISHED
        (0x5F3E02, "ds:0x9977f0,eax"),               # restore
        (0x5F3F3F, "eax,DWORD PTR [ebp-0x394]"),     # the read uses the same local
        (0x5F3F45, "eax,DWORD PTR [eax+0xa40]"),
        (0x5F5A17, "eax,ds:0x9977f0"),               # callback receiver
        (0x5F5A1C, "DWORD PTR [ebp-0x4],eax"),       # bound to the callback's local
        (0x5F5A9F, "edx,DWORD PTR [ebp-0x4]"),       # and reloaded before each store
        (0x5F5AC8, "edx,DWORD PTR [ebp-0x4]")]
ident = all(a in BYADDR and BYADDR[a][2] == t for a, t in LINK)
ident = ident and POS[0x5F3D6A] == POS[0x5F3D70] - 1 and POS[0x5F5A1C] == POS[0x5F5A17] + 1
ident = ident and POS[0x5F5AC8] == POS[0x5F5ACB] - 1
ident = ident and all(any(x[2] == "edx,DWORD PTR [ebp-0x4]" for x in INS[POS[st] - 3:POS[st]])
                      for st in (0x5F5AA5, 0x5F5ACB))
gate("G7", ident,
     "identity chain (10 links, adjacency included): this -> [ebp-0x394] -> ds:0x9977f0 -> "
     "callback local -> both callback stores; the read uses the same local",
     "MU7 (drop the identity chain -> 5a11's receiver unexplained)")

cancel = (BYADDR[0x5F581C][2] == "DWORD PTR [edx+0xa40],0xffffffff"
          and BYADDR[0x5F57E6][2] == "DWORD PTR [ebp-0x10],0xfffffffe"
          and BYADDR[0x5F57EA][2] == "0x5f57f4"
          and BYADDR[0x5F57F7][2] == "edx,DWORD PTR [ecx+0x30a8]"
          and BYADDR[0x5F57FD][2] == "edx,0x40")
gate("G8", cancel,
     "cancel law: the only -1 store (0x5f581c) is reached from arg == -2 with ([this+0x30a8] & 0x40)",
     "MU8 (compare the arg with -1 instead of -2)")

print("")
RIV = [
    ("R1", "the runner computes its own result",
     "%d stores in the runner's %d refs" % (sum(1 for r in rr if r[3] != "READ"), len(rr)), "KILLED"),
    ("R2", "the dialog ctor seeds the result cell",
     "%d refs in FUN_00405ef0" % len(BY_FN.get("FUN_00405ef0", [])), "KILLED"),
    ("R3", "any +0xa40 field is the same cell",
     "%d/%d field refs fail the pair" % (len(FIELD) - sum(len(BY_FN[fn]) for fn in WRITER_FNS)
                                         - len(rr), len(FIELD)), "KILLED"),
    ("R4", ">=3 of the cluster is the right filter",
     "%d functions admitted, 2 of them non-dialog" % len(LOOSE), "KILLED"),
]
for tag, claim, number, verdict in RIV:
    print("%s %-42s %-46s -> %s" % (tag, claim, number, verdict))

rival_ok = (sum(1 for r in rr if r[3] != "READ") == 0
            and len(BY_FN.get("FUN_00405ef0", [])) == 0
            and (len(FIELD) - sum(len(BY_FN[fn]) for fn in WRITER_FNS) - len(rr)) == 62
            and len(LOOSE) == 5)
print("")
gate("G9", rival_ok, "rivals R1-R4 all die on the printed numbers",
     "MU9 (print R3's excluded count as 0)")

print("")
print("table_sha256=%s" % hashlib.sha256(TABLE.encode()).hexdigest()[:16])
npass = sum(1 for g in GATES if g[1])
digest = hashlib.sha256(("\n".join("%s:%s" % (g[0], g[1]) for g in GATES)
                         + TABLE).encode()).hexdigest()[:16]
if npass == len(GATES):
    print("PASS M343: %d/%d gates  digest=%s" % (npass, len(GATES), digest))
else:
    print("FAIL M343: %d/%d gates  digest=%s" % (npass, len(GATES), digest))
    sys.exit(1)
