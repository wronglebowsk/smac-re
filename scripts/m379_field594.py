#!/usr/bin/env python3
"""M379 - WHO READS record +0x594, and the 9-slot question behind the
agenda randomizer's "8th write".

M376 named the `0x927590` faction-record array (stride 0x59c) and the bit-24
agenda randomizer, and left two OPENs: (1) who consumes the third stored dword
at record +0x594 (the "first positive effect" index), (2) the 8th write at
0x92a7fc landing 0x58c past the 8-record block end 0x92a270.

This instrument answers both from the instruction bytes alone:

  * whole-image sweep for operands with positive displacement +0x594 and for
    the indexed form [k*0x59c + 0x927b24] = record k + 0x594.  Exactly one
    +0x594 site exists (0x4ffff2) and it is a DIFFERENT heap dword array
    (ds:0x997b20 = malloc(count*4)); exactly two indexed readers exist
    (0x5a1eac in FUN_005a1ad0, 0x54696c in FUN_00546800), both AI social-
    engineering evaluators that index the 11-entry per-faction effect vector.
  * the agenda loop's real iteration count: ebx starts at 1, is incremented in
    the body, and the bound `cmp ebx,8 / jl` is tested AFTER the increment, so
    the body runs 7 times (slots 1..7).  The last store is 0x92a268 < 0x92a270.
    0x92a7fc is the loop's terminal POINTER value, never dereferenced; it does
    not occur as an immediate anywhere in .text.  M376's OPEN premise is
    RETRACTED.
  * the block is exactly 8 records: the save/load path pushes size 0x2ce0 with
    base 0x927590 (twice), two independent walks bound at 0x92a270, and the
    globals past the end have no record-0 mirror - no 9th slot.

M379_PATCH='addr|new text;...' rewrites one instruction line (mutation lever).
M379_ALGO=3 counts the bound as an inclusive iteration count (the 8-write law).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M379_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.environ.get("M379_EXE", os.path.join(ROOT, "programs/terran.exe"))
ALPHA = os.environ.get("M379_ALPHA", os.path.join(ROOT, "programs/alpha.txt"))
ALGO = int(os.environ.get("M379_ALGO", "0") or 0)

ADDR = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
PATCH = {}
for tok in os.environ.get("M379_PATCH", "").split(";"):
    if "|" in tok:
        a, t = tok.split("|", 1)
        PATCH[int(a, 16)] = t


def load_text():
    ins, order = {}, []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = ADDR.match(line.rstrip("\n"))
            if not m:
                continue
            a = int(m.group(1), 16)
            ins[a] = (bytes.fromhex(m.group(2)), PATCH.get(a, m.group(3).strip()))
            order.append(a)
    order.sort()
    return ins, order


INS, ORDER = load_text()
PREV = {}
_p = None
for _a in ORDER:
    if INS[_a][1]:
        PREV[_a] = _p
        _p = _a


def txt(a):
    return INS[a][1]


def bts(a):
    return INS[a][0]


def imm(t, which=0):
    v = re.findall(r"0x([0-9a-f]+)", t)
    if len(v) <= which:
        return None
    return int(v[which], 16)


def win(lo, hi):
    return [a for a in ORDER if lo <= a <= hi]


RAW = open(TEXT, errors="replace").read()


def occ(needle):
    return sum(txt(a).count(needle) for a in ORDER)
ROWS = []
NG = [0]


def row(tag, what, value):
    ROWS.append((tag, what, value))


def check(tag, ok, msg):
    NG[0] += 1
    print("  %-4s %s %s" % (tag, "ok  " if ok else "FAIL", msg))
    return ok


# ------------------------------------------------------- tiny insn emulator
def P(k=0, a=0):
    return {"a": a, "k": k}


def add(p, q, s=1):
    out = dict(p)
    for k, v in q.items():
        out[k] = out.get(k, 0) + s * v
    return out


LEA = re.compile(r"lea\s+(\w+),\[(\w+)\+(\w+)\*(\d+)\]$")
LEA2 = re.compile(r"lea\s+(\w+),\[(\w+)\+(\w+)\*(\d+)\+0x([0-9a-f]+)\]$")
LEA1 = re.compile(r"lea\s+(\w+),\[(\w+)\]$")
MOVI = re.compile(r"mov\s+(\w+),0x([0-9a-f]+)$")
MOVR = re.compile(r"mov\s+(\w+),(\w+)$")
SHL = re.compile(r"shl\s+(\w+),(?:0x)?([0-9a-f]+)$")
ADD = re.compile(r"(add|sub)\s+(\w+),(?:(\w+)|0x([0-9a-f]+))$")
XOR = re.compile(r"xor\s+(\w+),(\w+)$")


def emulate(addrs, want, seeds=None):
    R = {k: dict(v) for k, v in (seeds or {}).items()}
    for a in addrs:
        t = txt(a)
        if not t:
            continue
        m = LEA2.match(t)
        if m:
            r, r1, r2, sc, dv = m.group(1), m.group(2), m.group(3), int(m.group(4)), int(m.group(5), 16)
            R[r] = add(R[r1], {"a": R[r2].get("a", 0) * sc, "k": R[r2].get("k", 0) * sc})
            R[r]["k"] = R[r].get("k", 0) + dv
            continue
        m = LEA.match(t)
        if m:
            r, r1, r2, sc = m.group(1), m.group(2), m.group(3), int(m.group(4))
            q = {k: v * sc for k, v in R[r2].items()}
            R[r] = add(R[r1], q)
            continue
        m = LEA1.match(t)
        if m:
            R[m.group(1)] = dict(R[m.group(2)])
            continue
        m = MOVI.match(t)
        if m:
            R[m.group(1)] = P(int(m.group(2), 16))
            continue
        m = MOVR.match(t)
        if m:
            if m.group(2) not in R:
                raise SystemExit("emulator: unseeded %r at 0x%x" % (t, a))
            R[m.group(1)] = dict(R[m.group(2)])
            continue
        m = XOR.match(t)
        if m:
            R[m.group(1)] = P(0)
            continue
        m = SHL.match(t)
        if m:
            sh = int(m.group(2), 16) if "0x" in m.group(0) else int(m.group(2))
            R[m.group(1)] = {k: v * (2 ** sh) for k, v in R[m.group(1)].items()}
            continue
        m = ADD.match(t)
        if m:
            op, r, src, im = m.group(1), m.group(2), m.group(3), m.group(4)
            q = R[src] if src else P(int(im, 16))
            R[r] = add(R[r], q, 1 if op == "add" else -1)
            continue
        if " PTR " in t:
            continue                      # memory load/store: not address maths
        raise SystemExit("emulator: unhandled insn at 0x%x: %r" % (a, t))
    return R[want]


# ------------------------------------------------------ loop control-flow interpreter
# Executes the agenda block's real instructions (0x5a1160..0x5a121c) with a tiny
# register/memory model and follows the decoded branch targets, so the body count,
# the store addresses and the terminal edi are EXECUTED, not modelled.  Unknown
# instructions raise, so a rewrite the model cannot follow is a FAIL, not a guess.
NEXT = {}
_n = None
for _a in reversed(ORDER):
    if INS[_a][1]:
        NEXT[_a] = _n
        _n = _a


def _ea(expr, R):
    expr = expr.replace("es:", "").strip()
    m = re.match(r"^\[(\w+)(?:\+(\w+)\*(\d+))?(?:([+-])0x([0-9a-f]+))?\]$", expr)
    if not m:
        raise SystemExit("interp: bad operand %r" % expr)
    v = R.get(m.group(1), 0)
    if m.group(2):
        v += R.get(m.group(2), 0) * int(m.group(3))
    if m.group(5):
        v += (-1 if m.group(4) == "-" else 1) * int(m.group(5), 16)
    return v


def _flags(d):
    return {"zf": d == 0, "sf": d < 0, "of": False}


def exec_block(entry=0x5A1160, stop=0x5A121C, limit=4000):
    R = {"ebp": 0x100000, "esp": 0, "esi": 0}   # esi is inherited on the first body
    M = {0x985AE8: 0x1000000}
    for i in range(int(imm(txt(0x5A1203)))):
        M[0x92BABC + 4 * i] = 1          # the grid's first positive cell: the scan stops
    F = {}
    rnd = [1, 4] * 400
    ri = 0
    pc = entry
    bodies, bases, stores, back = 0, [], [], 0
    terminated = False
    steps = 0
    while steps < limit:
        if pc == stop:
            terminated = True
            break
        if pc == 0x5A1180:              # the body's first store: one body, one seed
            bodies += 1
            bases.append(R.get("edi"))
        t = txt(pc)
        steps += 1
        if not t:
            pc = NEXT[pc]
            continue
        op = t.split()[0]
        args = t[len(op):].strip()
        nxt = NEXT[pc]

        if op == "rep":
            # rep stos DWORD PTR es:[edi],eax
            m = re.match(r"stos DWORD PTR es:\[(\w+)\],(\w+)$", args)
            if not m:
                raise SystemExit("interp: bad rep at 0x%x" % pc)
            while R["ecx"] > 0:
                M[R[m.group(1)]] = R[m.group(2)]
                R[m.group(1)] += 4
                R["ecx"] -= 1
            pc = nxt
            continue
        if op in ("test", "cmp"):
            m = re.match(r"DWORD PTR (\[[^\]]+\]|ds:0x[0-9a-f]+),(?:(\w+)|0x([0-9a-f]+))$", args)
            if m:
                a = M.get(int(m.group(1)[5:], 16), 0) if m.group(1).startswith("ds:") \
                    else M.get(_ea(m.group(1), R), 0)
                tok = m.group(2) or m.group(3)
                b = R[tok] if tok in R else int(tok, 16)
            else:
                m = re.match(r"(\w+),(?:(\w+)|0x([0-9a-f]+))$", args)
                if not m:
                    raise SystemExit("interp: bad %s at 0x%x: %r" % (op, pc, t))
                a = R[m.group(1)]
                tok = m.group(2) or m.group(3)
                b = R[tok] if tok in R else int(tok, 16)
            F = _flags((a & b) if op == "test" else (a - b))
            pc = nxt
            continue
        if op.startswith("j") and op != "jmp":
            tgt = int(re.search(r"0x([0-9a-f]+)$", args).group(1), 16)
            zf, sf = F.get("zf"), F.get("sf")
            cond = {"je": zf, "jne": not zf, "jl": sf, "jge": not sf,
                    "jg": (not zf) and (not sf), "jle": zf or sf}[op]
            if ALGO == 1 and op == "jl":       # ALGORITHM mutant: inverted branch
                cond = not cond
            if ALGO == 2 and pc == 0x5A1216:    # ALGORITHM mutant: inclusive bound
                cond = F.get("zf") or F.get("sf")
            if cond:
                if pc == 0x5A1216:
                    back += 1
                pc = tgt
                continue
            pc = nxt
            continue
        if op == "jmp":
            pc = int(re.search(r"0x([0-9a-f]+)$", args).group(1), 16)
            continue
        if op == "call":
            R["eax"] = rnd[ri % len(rnd)] if "0x64c6f0" in args else 0
            ri += 1
            pc = nxt
            continue
        if op == "cdq":
            R["edx"] = -1 if R["eax"] < 0 else 0
            pc = nxt
            continue
        if op == "idiv":
            m = re.match(r"(\w+)$", args)
            d = R[m.group(1)]
            a = R["eax"]
            R["eax"], R["edx"] = int(a / d), a - int(a / d) * d
            pc = nxt
            continue
        m = re.match(r"mov\s+(\w+),DWORD PTR (ds:0x[0-9a-f]+|\[[^\]]+\])$", t)
        if m:
            src = int(m.group(2)[5:], 16) if m.group(2).startswith("ds:") else _ea(m.group(2), R)
            if 0x92BABC <= src < 0x92BABC + 0x350:
                R[m.group(1)] = M.get(src, 1)
            else:
                R[m.group(1)] = M.get(src, 0)
            pc = nxt
            continue
        m = re.match(r"mov\s+DWORD PTR (\[[^\]]+\]),(?:(\w+)|0x([0-9a-f]+))$", t)
        if m:
            addr = _ea(m.group(1), R)
            tok = m.group(2) or m.group(3)
            M[addr] = R[tok] if tok in R else int(tok, 16)
            if REC0 <= addr < 0x92B400:
                stores.append(addr)
            pc = nxt
            continue
        m = re.match(r"mov\s+(\w+),(?:(\w+)|0x([0-9a-f]+))$", t)
        if m:
            tok = m.group(2) or m.group(3)
            R[m.group(1)] = R[tok] if tok in R else int(tok, 16)
            pc = nxt
            continue
        m = re.match(r"lea\s+(\w+),(\[[^\]]+\])$", t)
        if m:
            expr = m.group(2)
            lm = re.match(r"^\[(\w+)(?:\+(\w+)\*(\d+))?(?:([+-])0x([0-9a-f]+))?\]$", expr)
            if lm and not lm.group(2) and not lm.group(5):
                R[m.group(1)] = R[lm.group(1)]
            else:
                R[m.group(1)] = _ea(expr, R)
            pc = nxt
            continue
        m = re.match(r"(add|sub)\s+(\w+),(?!0x)(\w+)$", t)
        if m:
            R[m.group(2)] += R[m.group(3)] * (1 if m.group(1) == "add" else -1)
            pc = nxt
            continue
        m = re.match(r"(add|sub)\s+(\w+),0x([0-9a-f]+)$", t)
        if m:
            R[m.group(2)] += int(m.group(3), 16) * (1 if m.group(1) == "add" else -1)
            pc = nxt
            continue
        m = re.match(r"(inc|dec)\s+(\w+)$", t)
        if m:
            R[m.group(2)] += 1 if m.group(1) == "inc" else -1
            pc = nxt
            continue
        m = re.match(r"(xor|or)\s+(\w+),(\w+|0x[0-9a-f]+)$", t)
        if m:
            tok = m.group(3)
            v = int(tok, 16) if tok.startswith("0x") else R.get(tok, 0)
            cur = R.get(m.group(2), 0)
            R[m.group(2)] = (cur ^ v) if m.group(1) == "xor" else (cur | v)
            pc = nxt
            continue
        m = re.match(r"shl\s+(\w+),(?:0x)?([0-9a-f]+)$", t)
        if m:
            R[m.group(1)] <<= int(m.group(2), 16)
            pc = nxt
            continue
        raise SystemExit("interp: unhandled insn at 0x%x: %r" % (pc, t))

    return {"bodies": bodies, "bases": bases, "stores": stores, "terminal": R.get("edi"),
            "terminated": terminated, "steps": steps, "back": back}



STORE_OPS = ("mov", "add", "sub", "and", "or", "xor", "adc", "sbb", "inc", "dec",
             "neg", "not", "xchg", "pop", "stos", "cmpxchg", "xadd")


def is_store(t):
    """Memory as the FIRST operand of a writing/RMW mnemonic = store (or RMW)."""
    m = re.match(r"(\w+)\s+(BYTE|WORD|DWORD) PTR \[", t)
    return bool(m) and m.group(1) in STORE_OPS


def sweep():
    """Every operand with a POSITIVE displacement; (addr, text, disp, store?)."""
    out = []
    for a in ORDER:
        t = txt(a)
        if not t:
            continue
        for mem in re.findall(r"\[([^\]]+)\]", t):
            for h in re.findall(r"\+(0x[0-9a-f]+)", mem):
                out.append((a, t, int(h, 16), is_store(t)))
    return out


SW = sweep()


def hits(disp):
    return [h for h in SW if h[2] == disp]


# ---------------------------------------------------------------- constants
REC0 = 0x927590
STRIDE = 0x59C
STR = 0x82F                     # per-faction dword stride in the 0x94d430 block
TRUE_READERS = [0x5A1EAC, 0x54696C]
SEED = int(imm(txt(0x5A1171)))
START = int(imm(txt(0x5A116A)))
BOUND = int(imm(txt(0x5A1213)))
END = REC0 + 8 * STRIDE

# ------------------------------------------------------------- G0 anchors
h_txt = hashlib.sha1(open(TEXT, "rb").read()).hexdigest()
h_exe = hashlib.sha1(open(EXE, "rb").read()).hexdigest()
row("G0", "text insns", len(INS))
row("G0", "text sha1", h_txt[:16])
row("G0", "exe sha1", h_exe[:16])
for a in (0x5A116A, 0x5A1171, 0x5A11C5, 0x5A120D, 0x5A1213, 0x5A1216, 0x5A1EAC, 0x54696C):
    row("G0", "0x%x bytes" % a, bts(a).hex(" "))

# ------------------------------------------------------------ G1 geometry
# reader A: eax = faction * 0x59c, then [eax+0x927b14]
chainA = win(0x5A1E5A, 0x5A1E67)
PA = emulate(chainA, "eax", {"ebx": P(a=1)})
dispA = imm(txt(0x5A1E6A), 0)
# reader B: eax = faction * 0x59c spilled to [ebp+0xc], then [eax+0x927b14]
chainB = win(0x5468F6, 0x546904)
PB = emulate(chainB, "eax", {"esi": P(a=1)})
dispB = imm(txt(0x546907), 0)
row("G1", "reader A stride chain 0x5a1e5a..0x5a1e67", PA)
row("G1", "reader A category load @0x5a1e6a", hex(dispA))
row("G1", "reader B stride chain 0x5468f6..0x546904", PB)
row("G1", "reader B category load @0x546907", hex(dispB))
row("G1", "field offsets from the three loads", (0x584, 0x58C, 0x594))
row("G1", "record base = 0x927b24 - 0x594", hex(0x927B24 - 0x594))

# per-faction weight stride 0x82f (dwords) in both readers
WA = emulate(win(0x5A1EBE, 0x5A1ECB), "edx", {"ebx": P(a=1)})
WB = emulate(win(0x54689B, 0x5468B5), "ebx", {"edi": P(a=1)})
row("G1", "reader A weight index chain -> edx", WA)
row("G1", "reader B weight index chain -> ebx", WB)

# ------------------------------------------------------------- G2 readers
h594 = hits(0x594)
h924 = hits(0x927B24)
row("G2", "operands with +0x594", [(hex(a), t, "STORE" if s else "load") for a, t, _, s in h594])
row("G2", "operands with +0x927b24", [(hex(a), t) for a, t, _, _ in h924])
row("G2", "reads of +0x927b14 (category)", [hex(a) for a, t, _, s in hits(0x927B14)])
row("G2", "reads of +0x927b1c (choice)", [hex(a) for a, t, _, s in hits(0x927B1C)])
row("G2", "seq after reader A 0x5a1eb2..0x5a1edb",
    [txt(a) for a in win(0x5A1EB2, 0x5A1EDB) if txt(a)])
row("G2", "seq after reader B 0x546972..0x546983",
    [txt(a) for a in win(0x546972, 0x546983) if txt(a)])

# rival: the lone [edx+0x594] at 0x4ffff2 is a heap dword array, not the record
malloc_store = txt(0x6146C7)
count_shl = txt(0x6146BB)
n997 = sum(1 for a in ORDER if "0x997b20" in txt(a))
row("G2", "0x4ffff2 owner base", txt(0x4FFFE9))
row("G2", "ds:0x997b20 producer", (count_shl, malloc_store))
row("G2", "loads of ds:0x997b20", n997)

# ------------------------------------------------------------- G3 the loop
def loop_bodies(start, bound, seed, stride):
    """The arithmetic cross-check (bound - start bodies, one stride each)."""
    n, edi, bases = 0, seed, []
    while True:
        n += 1
        bases.append(edi)
        if n > 1000:
            raise SystemExit("loop law did not terminate")
        if not (start + n < bound):
            return n, bases
        edi += stride


RES = exec_block()                       # execute 0x5a1160..0x5a121c for real
iters = RES["bodies"]
writes = RES["bases"]
stores = RES["stores"]
lo_store, hi_store = min(stores), max(stores)
terminal = RES["terminal"]
model_n, model_bases = loop_bodies(START, BOUND, SEED, STRIDE)
rows = None
row("G3", "seed pointer @0x5a1171", hex(SEED))
row("G3", "loop start/step/bound", (START, txt(0x5A11C5), BOUND, txt(0x5A1216)))
row("G3", "stride @0x5a120d", hex(imm(txt(0x5A120D))))
row("G3", "executed bodies", iters)
row("G3", "executed body seeds", [hex(w) for w in writes])
row("G3", "back-edges taken (jl @0x5a1216)", RES["back"])
row("G3", "record stores executed", (len(stores), hex(lo_store), hex(hi_store)))
row("G3", "terminal edi at exit / terminated / steps", (hex(terminal), RES["terminated"], RES["steps"]))
row("G3", "arithmetic cross-check (bound-start)", (model_n, model_bases == writes))
row("G3", "block end rec0+8*stride", hex(END))
row("G3", "occurrences of 0x92a7fc in .text", occ("0x92a7fc"))

# ---------------------------------------------------------- G4 block extent
push_base = [a for a in ORDER if txt(a) == "push   0x927590"]
sizes = []
for a in push_base:
    p = PREV.get(a)
    sizes.append((hex(a), txt(p) if p else None))
row("G4", "push 0x927590 sites + preceding push", sizes)
row("G4", "0x2ce0 / stride", (0x2CE0, 0x2CE0 // STRIDE))
row("G4", "walk bounds", (txt(0x523E1A), txt(0x44947F)))
mirrors = {hex(x): occ("0x%x" % x)
           for x in (0x9275FC, 0x927608, 0x927618, 0x9276BC)}
past = {hex(x): occ("0x%x" % x)
        for x in (0x92A2DC, 0x92A2E8, 0x92A2F8, 0x92A39C)}
row("G4", "globals past the end (occurrences)", past)
row("G4", "their would-be record-0 mirrors (occurrences)", mirrors)
rec8 = (0x92A7F4, 0x92A7FC, 0x92A804, 0x92A80C)   # rec8 +0x584/+0x58c/+0x594/+0x59c
past_hits = [h for h in SW if 0x92A270 < h[2] < 0x92B400]
row("G4", "static operands past the block (count/distinct)",
    (len(past_hits), len({h[2] for h in past_hits})))
row("G4", "hypothetical rec-8 field addresses (occurrences)",
    {hex(x): occ("0x%x" % x) for x in rec8})
row("G4", "0x92a270 occurrences", occ("0x92a270"))
end_bounds = [a for a in ORDER if re.search(r"cmp\s+\w+,0x92a270$", txt(a))]
row("G4", "walk bounds at 0x92a270", [hex(a) for a in end_bounds])
row("G4", "0x92a270 as a scalar global", (txt(0x57907D), txt(0x5790EE)))

# ------------------------------------------------------------------- print
print("M379 who reads record +0x594, and the agenda loop's real write count")
print("%-4s %-56s %s" % ("tag", "what", "value"))
for tag, what, val in ROWS:
    print("%-4s %-56s %s" % (tag, what, val))
print()

ok = True
ok &= check("G0", len(INS) > 780000 and h_txt.startswith("02d578095222"),
            "text %d insns sha %s" % (len(INS), h_txt[:12]))
ok &= check("G0", h_exe.startswith("a889fd11be2fc4cc"),
            "the disassembly cache is tied to the pinned terran.exe (%s)" % h_exe[:12])
ok &= check("G0", bts(0x5A1171) == bytes.fromhex("bfb8809200") and
            bts(0x5A1213) == bytes.fromhex("83fb08"),
            "the seed mov and the bound cmp are the bytes decoded below")

ok &= check("G1", PA.get("a") == STRIDE and dispA == 0x927B14,
            "reader A computes faction*%#x and reads the category at 0x927b14" % STRIDE)
ok &= check("G1", PB.get("a") == STRIDE and dispB == 0x927B14,
            "reader B computes faction*%#x and reads the category at 0x927b14" % STRIDE)
ok &= check("G1", 0x927B1C - 0x927B14 == 8 and 0x927B24 - 0x927B1C == 8 and
            0x927B24 - 0x594 == REC0,
            "the three loads are 8 B apart: +0x584/+0x58c/+0x594 over base %#x" % REC0)
ok &= check("G1", WA.get("a") == STR and WB.get("a") == STR,
            "both readers scale the faction by %#x dwords (= 0x20bc B block stride)" % STR)

ok &= check("G2", len(h594) == 1 and not h594[0][3],
            "exactly %d static +0x594 operand, a load: 0x%x" % (len(h594), h594[0][0]))
ok &= check("G2", h594[0][0] == 0x4FFFF2 and "ds:0x997b20" in txt(0x4FFFE9),
            "RIVAL '0x4ffff2 reads the faction field' FAILS: its base is ds:0x997b20")
ok &= check("G2", count_shl == "shl    eax,0x2" and malloc_store == "mov    ds:0x997b20,eax",
            "ds:0x997b20 is malloc(count*4) - a heap dword array (%d loads), not the BSS record" % n997)
ok &= check("G2", sorted(h[0] for h in h924) == sorted(TRUE_READERS) and not any(h[3] for h in h924),
            "exactly %d indexed readers of record+0x594, both loads: %s"
            % (len(h924), [hex(a) for a in TRUE_READERS]))
ok &= check("G2", txt(0x5A1EB2) == "test   eax,eax" and txt(0x5A1EB4).startswith("jl") and
            txt(0x5A1EB6) == "mov    eax,DWORD PTR [ebp+eax*4-0x7c]" and
            txt(0x5A1ECD) == "add    ecx,DWORD PTR [edx*4+0x94e488]" and
            txt(0x5A1EDB) == "mov    edi,0x1",
            "reader A: skip if <0, else index the local effect vector; >0 adds the faction "
            "weight, <0 sets the reject flag")
ok &= check("G2", txt(0x546976) == "add    eax,ebx" and
            txt(0x546978) == "mov    ecx,DWORD PTR [eax*4+0x94d67c]" and
            txt(0x546981).startswith("jge"),
            "reader B: index the per-faction effect table at 0x94d67c; a negative value "
            "enters the message block at 0x546983")

ok &= check("G2", "[eax+0x927b14]" in txt(0x5A1E6A) and "[eax+0x927b1c]" in txt(0x5A1E74)
            and "[eax+0x927b24]" in txt(0x5A1EAC) and PA.get("a") == STRIDE,
            "reader A: the emulated eax (faction*0x59c) is the base of all three loads")
ok &= check("G2", txt(0x546904) == "mov    DWORD PTR [ebp+0xc],eax" and
            "[eax+0x927b14]" in txt(0x546907) and
            txt(0x546969) == "mov    edx,DWORD PTR [ebp+0xc]" and
            "[edx+0x927b24]" in txt(0x54696C),
            "reader B: eax spills to [ebp+0xc] and the +0x594 load reaches it via edx")
ok &= check("G2", "[edx*4+0x94e488]" in txt(0x5A1ECD) and WA.get("a") == STR and
            txt(0x546976) == "add    eax,ebx" and WB.get("a") == STR,
            "the weight-chain registers (A: edx, B: ebx) feed the per-faction effect access")
ok &= check("G2", txt(0x5A1EB4) == "jl     0x5a1ee0" and txt(0x5A1ED9) == "jge    0x5a1ee0",
            "reader A's negative-field skip and negative-effect flag both branch to 0x5a1ee0")
ok &= check("G2", txt(0x546974) == "jl     0x5469ba" and txt(0x546981) == "jge    0x5469ba" and
            txt(0x546983) == "mov    ebx,DWORD PTR [ebp-0x2c]",
            "reader B's non-negative path skips to 0x5469ba; the fall-through 0x546983 is the "
            "message block")
ok &= check("G2", txt(0x5A1203) == "cmp    eax,0xb" and
            open(ALPHA, errors="replace").read().split("#SOCIO")[1].splitlines()[1].count(",") == 10,
            "the stored index is the scan counter 0..0xa: 11 dwords = the #SOCIO keyword count")

ok &= check("G3", RES["terminated"] and RES["steps"] < 4000 and iters == 7,
            "EXECUTED: the block terminates at 0x5a121c after %d bodies (%d steps)"
            % (iters, RES["steps"]))
ok &= check("G3", writes[0] == 0x9280B8 and writes[-1] == 0x92A260 and RES["back"] == 6,
            "the jl back-edge is taken %d times; body seeds %#x..%#x"
            % (RES["back"], writes[0], writes[-1]))
ok &= check("G3", lo_store == 0x9280B0 and hi_store == 0x92A268 and hi_store < END,
            "all %d record stores lie in %#x..%#x, highest < block end %#x"
            % (len(stores), lo_store, hi_store, END))
ok &= check("G3", terminal == 0x92A7FC and occ("0x92a7fc") == 0,
            "RETRACTION: executed terminal edi is 0x92a7fc (seed+7*stride); it is never "
            "dereferenced and never an immediate")
ok &= check("G3", iters == 7,
            "RIVAL 'the loop writes 8 records / overruns 0x92a270' FAILS: it writes %d" % iters)
ok &= check("G3", model_n == iters and model_bases == writes,
            "the executed body seeds equal the independent bound-start arithmetic (%d)" % model_n)
ok &= check("G3", txt(0x5A1180) == "mov    DWORD PTR [edi-0x8],eax" and
            txt(0x5A1183) == "mov    DWORD PTR [edi],esi" and
            txt(0x5A1185) == "mov    DWORD PTR [edi+0x8],eax" and
            txt(0x5A120A) == "mov    DWORD PTR [edi+0x8],eax",
            "the three stores are edi-8/+0/+8, so the initialised fields are 0x584/0x58c/0x594")
ok &= check("G3", writes[0] != REC0 + 0x58C,
            "slot 0 (%#x) is skipped: the randomizer only seeds slots 1..%d" % (REC0, iters))

ok &= check("G4", [s[1] for s in sizes] == ["push   0x2ce0", "push   0x2ce0"] and
            len(push_base) == 2,
            "the save/load path pushes size 0x2ce0 with base 0x927590 twice")
ok &= check("G4", 0x2CE0 % STRIDE == 0 and 0x2CE0 // STRIDE == 8 and END == 0x92A270,
            "%#x = %d records x %#x; base+block = %#x" % (0x2CE0, 8, STRIDE, END))
ok &= check("G4", txt(0x523E1A) == "cmp    esi,0x92a270" and
            txt(0x44947F) == "cmp    ebx,0x92a270",
            "two independent walks stop exactly at 0x92a270")
ok &= check("G4", all(v > 0 for v in past.values()) and all(v == 0 for v in mirrors.values()) and
            all(occ("0x%x" % x) == 0 for x in rec8) and len(end_bounds) >= 5 and
            txt(0x57907D) == "mov    ds:0x92a270,eax" and
            txt(0x5790EE) == "mov    edx,DWORD PTR ds:0x92a270",
            "RIVAL 'a 9th record exists' FAILS: no static operand addresses a rec-8 field; "
            "0x92a270 is the first scalar global past the block (ds: store/load) and "
            "the bound of %d walks, not a record base" % len(end_bounds))

dig = hashlib.sha1(repr(ROWS).encode()).hexdigest()[:16]
print()
print("%s M379: %d/%d gates digest %s" % ("PASS" if ok else "FAIL", NG[0] if ok else 0, NG[0], dig))
sys.exit(0 if ok else 1)
