#!/usr/bin/env python3
"""M376 - WHAT THE 0x92babc "12-slot" TABLE IS.

M374 named Semaphore bit 24 (rules bit 17) "Randomize faction leader social
agendas" and left its consumer unnamed: `0x5a1150` zeroes 0xc dwords, walks 8
faction records (stride 0x59c) and stores three dwords per faction after
scanning 11 dwords of a cell at `0x92babc + row*0xd4 + cell*0x2c`.

This instrument reads the geometry out of the INSTRUCTION BYTES (a tiny
instruction emulator turns the multiply chain at 0x5a11e0..0x5a11f3 into
coefficients), reads the table's source out of the game's own rule file
(programs/alpha.txt section `#SOCIO`) and computes the grid it builds:

  0x92ba98  row header, 0x24 B: +0 category name, +4..0x10 per-choice tech,
            +0x14..0x20 per-choice name, +0x24 = 4 cells x 11 dwords
  0x9270c0  11 effect-keyword names, 0x68 B each (stride, count at 0x927538)
  alpha.txt #SOCIO: line 746 = the 11 keywords, line 748 = 4 categories,
            lines 749..764 = 16 choices (4 per category) with +/- effect tokens.

Gates
  G0  anchors: instruction bytes + file sha1s.
  G1  geometry: an emulator derives 0xd4 row / 0x2c cell / 0xb words from the
      multiply chain; three parser sites agree; rows and cells cross-checked
      against the section's own counts.
  G2  signature: the cell i binds to keyword i by strcmp against 0x9270c0 +
      i*0x68 and the token's +/- count is ADDED; the 16 cells computed from
      alpha.txt have exactly 4 empty vectors, all at choice index 0.
  G3  consumer: bit-24 gate, 12-dword used-pair registry indexed 3*a+b,
      first-POSITIVE scan, 8 records x 0x59c, and the (category, choice,
      signature-effect) fields at record +0x584/+0x58c/+0x594 derived from
      0x9280b8 - 0x927590 and cross-checked against the reader's own bases.
  G4  reader: +0x584 -> category NAME (0x92ba98 + d*0xd4), +0x58c -> choice
      NAME (0x92baac + d*0xd4 + e*4), both appended to one text buffer.
  G5  rivals: (1) the table is initialized .data (it is BSS); (2) the 11
      columns are factions; (3) a cell is 12 dwords; (4) the agenda can be a
      Future Society choice (row 3 is unreachable by the consumer).

M376_PATCH='addr|new text;...'  rewrites one instruction line (mutation lever).
The gated instruction lines (each named by a mutant in scripts/m376_mutate.py):
  0x5a11f3 / 0x5a11e3 / 0x5a11ea  cell address, row coefficient, cell coefficient
  0x5a118e / 0x5a1193 / 0x5a119d  a modulus, its idiv, b modulus
  0x5a11a7 / 0x5a1160 / 0x5a1203 / 0x52b822 / 0x57ab94 / 0x52b82c / 0x52b84d
  0x5a1213 / 0x5a120d / 0x5a1171 / 0x5a11fd
  0x4a66d9 / 0x4a66ff / 0x4a667b
  0x57abe0 / 0x57abf8
M376_ALGO=n  1 = flip the sign law ('-' counts +1); 2 = sample 4 rows.
M376_ALPHA=<path>  alternate rule file.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M376_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.path.join(ROOT, "programs/terran.exe")
ALPHA = os.environ.get("M376_ALPHA", os.path.join(ROOT, "programs/alpha.txt"))
ALGO = int(os.environ.get("M376_ALGO", "0") or 0)

ADDR = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
PATCH = {}
for tok in os.environ.get("M376_PATCH", "").split(";"):
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


def pe_sections():
    d = open(EXE, "rb").read()
    p = struct.unpack_from("<I", d, 0x3C)[0]
    opt = p + 24
    base = struct.unpack_from("<I", d, opt + 28)[0]
    q = opt + struct.unpack_from("<H", d, p + 20)[0]
    secs = []
    for _ in range(struct.unpack_from("<H", d, p + 6)[0]):
        vs, va, rs, ra = struct.unpack_from("<IIII", d, q + 8)
        secs.append((base + va, vs, ra, rs))
        q += 40
    return d, secs


def covered(va):
    d, secs = pe_sections()
    for v, vs, ra, rs in secs:
        if v <= va < v + vs:
            return ra + va - v < ra + rs
    return False


# ------------------------------------------------------- tiny insn emulator
# Value = {key: coeff} with keys 'a', 'b', 'k' (k = constant).  Only the shapes
# the multiply chain uses; anything else raises, so an unexpected rewrite is a
# FAIL rather than a silent wrong number.
def P(k=0, a=0, b=0):
    return {"a": a, "b": b, "k": k}


def add(p, q, s=1):
    out = dict(p)
    for k, v in q.items():
        out[k] = out.get(k, 0) + s * v
    return out


def scale(p, s):
    return {k: v * s for k, v in p.items()}


LEA = re.compile(r"lea\s+(\w+),\[(\w+)(?:\+(\w+)\*(\d+))?\]$")
LEA2 = re.compile(r"lea\s+(\w+),\[(\w+)\+(\w+)\*(\d+)\+0x([0-9a-f]+)\]$")
MOVI = re.compile(r"mov\s+(\w+),0x([0-9a-f]+)$")
MOVR = re.compile(r"mov\s+(\w+),(\w+)$")
SHL = re.compile(r"shl\s+(\w+),(?:0x)?([0-9a-f]+)$")
ADD = re.compile(r"(add|sub)\s+(\w+)(?:,(\w+)|,0x([0-9a-f]+))$")
XOR = re.compile(r"xor\s+(\w+),(\w+)$")


def emulate(addrs, want, seeds=None):
    """Run the chain; return (value of `want`, displacement of a LEA base+)."""
    R = dict(seeds or {})
    disp = None
    for a in addrs:
        t = txt(a)
        m = LEA2.match(t)
        if m:
            r, r1, r2, sc, dv = m.group(1), m.group(2), m.group(3), int(m.group(4)), int(m.group(5), 16)
            R[r] = add(R[r1], scale(R[r2], sc))
            R[r]["k"] = R[r].get("k", 0) + dv
            disp = dv
            continue
        m = LEA.match(t)
        if m:
            r, r1, r2, sc = m.group(1), m.group(2), m.group(3), m.group(4)
            R[r] = add(R[r1], scale(R[r2], int(sc))) if r2 else dict(R[r1])
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
            R[m.group(1)] = scale(R[m.group(1)], 2 ** int(m.group(2), 16 if m.group(0).startswith("shl    e") and "0x" in m.group(0) else 10))
            continue
        m = ADD.match(t)
        if m:
            op, r, src, im = m.group(1), m.group(2), m.group(3), m.group(4)
            q = R[src] if src else P(int(im, 16))
            R[r] = add(R[r], q, 1 if op == "add" else -1)
            continue
        if t.startswith(("mov    DWORD PTR", "mov    WORD PTR", "mov    BYTE PTR")):
            continue          # memory store / load: irrelevant to the address maths
        raise SystemExit("emulator: unhandled insn at 0x%x: %r" % (a, t))
    return R[want], disp


# ------------------------------------------------------------- alpha.txt
def socio():
    lines = open(ALPHA, "r", errors="replace").read().splitlines()
    try:
        i = [n for n, l in enumerate(lines) if l.strip() == "#SOCIO"][0]
    except IndexError:
        return None
    toks = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    kw = toks(lines[i + 1])
    kw2 = toks(lines[i + 2])
    cats = toks(lines[i + 3])
    ch = []
    for ln in lines[i + 4:]:
        s = ln.strip()
        if not s or s.startswith("#"):
            break
        f = toks(s)
        ch.append((f[0], f[1], f[2:]))
    return kw, kw2, cats, ch


SOC = socio()
KW, KW2, CATS, CH = SOC


def vec(tokens, kw):
    """+/- token law: each token is '+...' / '-...' + keyword -> signed count."""
    v = [0] * len(kw)
    for tok in tokens:
        n = 0
        while n < len(tok) and tok[n] in "+-":
            n += 1
        word = tok[n:]
        s = (tok.count("+", 0, n) - tok.count("-", 0, n))
        if ALGO == 1:
            s = abs(s)
        if word in kw:
            v[kw.index(word)] += s
    return v


ROWS = []


def row(tag, what, value):
    ROWS.append((tag, what, value))


NG = [0]


def check(tag, ok, msg):
    NG[0] += 1
    print("  %-4s %s %s" % (tag, "ok  " if ok else "FAIL", msg))
    return ok


# ------------------------------------------------------------- G0 anchors
h_txt = hashlib.sha1(open(TEXT, "rb").read()).hexdigest()
h_exe = hashlib.sha1(open(EXE, "rb").read()).hexdigest()
h_alpha = hashlib.sha1(open(ALPHA, "rb").read()).hexdigest()
row("G0", "text insns", len(INS))
row("G0", "text sha1", h_txt[:16])
row("G0", "exe sha1", h_exe[:16])
row("G0", "alpha.txt sha1", h_alpha[:16])
for a in (0x5A1150, 0x5A1160, 0x5A11F3, 0x52B822, 0x57ABE7, 0x4A66DF):
    row("G0", "0x%x bytes" % a, bts(a).hex(" "))

# ------------------------------------------------------------ G1 geometry
# cell 0x5a11c8..0x5a11f3: a = rand%3, b = rand%3+1, cell = base + f(a,b)
chain = win(0x5A11CA, 0x5A11F3)
CELLPOLY, BASE = emulate(chain, "ecx", {"esi": P(a=1), "edx": P(b=1)})
row("G1", "0x5a11f3 form", txt(0x5A11F3))
row("G1", "coefficient of a (row)", CELLPOLY.get("a"))
row("G1", "coefficient of b (cell)", CELLPOLY.get("b"))
row("G1", "table base (lea disp)", hex(BASE or 0))
amod = imm(txt(0x5A118E))          # mov ecx,3 before idiv at 0x5a1193
bmod = imm(txt(0x5A119D))          # mov ecx,3 before idiv at 0x5a119d
inc_b = txt(0x5A11A6) == "inc    edx"
row("G1", "a modulus @0x5a118e", amod)
row("G1", "b modulus @0x5a119d (+inc @0x5a11a6)", (bmod, inc_b))
row("G1", "cell words: copy count @0x52b822", imm(txt(0x52B822)))
row("G1", "cell words: scan bound @0x5a1203", imm(txt(0x5A1203)))
row("G1", "parser zeroing count @0x57ab94", imm(txt(0x57AB94)))
row("G1", "parser cell step @0x52b82c", hex(imm(txt(0x52B82C))))
row("G1", "parser cells/row bound @0x52b832", hex(imm(txt(0x52B832))))
row("G1", "parser row step @0x52b847", txt(0x52B847))
row("G1", "parser rows bound @0x52b84d", hex(imm(txt(0x52B84D))))
row("G1", "row header = 0x92babc-0x92ba98", hex(0x92BABC - 0x92BA98))
row("G1", "#SOCIO keywords", len(KW))
row("G1", "#SOCIO categories", len(CATS))
row("G1", "#SOCIO choices", len(CH))
row("G1", "keyword array capacity (0x927538-0x9270c0)/0x68", (0x927538 - 0x9270C0) // 0x68)

# ----------------------------------------------------------- G2 signature
row("G2", "keyword list", ", ".join(KW))
row("G2", "second keyword line == first", KW2 == KW)
row("G2", "categories", ", ".join(CATS))
NC = imm(txt(0x52B832)) // imm(txt(0x52B82C))       # cells per row from the loop bound
NR = imm(txt(0x52B84D)) // imm(txt(0x52B847)) if imm(txt(0x52B847)) else None
grid = {}
for n, (name, tech, toks) in enumerate(CH):
    grid[(n // NC, n % NC)] = vec(toks, KW)
cells = sorted(grid)
empty = [k for k in cells if not any(grid[k])]
nonempty = [k for k in cells if any(grid[k])]
row("G2", "cells parsed", len(cells))
row("G2", "empty cells", [(r, c, CH[r * NC + c][0]) for r, c in empty])
row("G2", "non-empty cells", len(nonempty))
firstpos = {k: next((i for i, w in enumerate(grid[k]) if w > 0), None) for k in nonempty}
row("G2", "cells with a first-positive effect", sum(1 for v in firstpos.values() if v is not None))
row("G2", "first-positive of 'Police State'", firstpos[(0, 1)])
row("G2", "vector of 'Police State'", grid[(0, 1)])
row("G2", "vector of 'Free Market'", grid[(1, 1)])
row("G2", "empty vectors are exactly choice index 0", sorted({c for _, c in empty}) == [0] and
    len(empty) == len(CATS))

# ------------------------------------------------------------ G3 consumer
blk = win(0x5A1150, 0x5A121E)
gate = txt(0x5A1150)
reg = imm(txt(0x5A1160))
rows_n = imm(txt(0x5A1213))
stride = imm(txt(0x5A120D))
seed = imm(txt(0x5A1171))
rec0 = 0x927590
delta = seed - rec0
inrec = delta % stride
idx = delta // stride
cat, cho, sig = inrec - 8, inrec, inrec + 8
writes = [seed + k * stride for k in range(rows_n)]
row("G3", "bit24 gate @0x5a1150", gate)
row("G3", "used-pair registry dwords @0x5a1160", reg)
row("G3", "registry index insns", txt(0x5A11A7) + " / " + txt(0x5A11AA))
row("G3", "max registry index 3*a+b", 3 * (amod - 1) + (bmod))
row("G3", "records walked (bound @0x5a1213)", rows_n)
row("G3", "record stride @0x5a120d", hex(stride))
row("G3", "seed pointer @0x5a1171", hex(seed))
row("G3", "seed-record delta", hex(delta))
row("G3", "delta = %d*stride + %#x" % (idx, inrec), (idx, hex(inrec)))
row("G3", "fields: category / choice / signature-effect", (hex(cat), hex(cho), hex(sig)))
row("G3", "first-positive scan", txt(0x5A11FA) + " / " + txt(0x5A11FD))
row("G3", "store order", txt(0x5A11D1) + " | " + txt(0x5A11D4) + " | " + txt(0x5A120A))
row("G3", "first write address", hex(writes[0]))
row("G3", "last write address", hex(writes[-1]))
row("G3", "8-record save block end (0x927590+8*0x59c)", hex(rec0 + 8 * stride))
rows_sampled = amod + 1 if ALGO == 2 else amod      # ALGO2: pretend row 3 is sampled
sampled = [(a, b) for a in range(rows_sampled) for b in range(1, bmod + 1)]
row("G3", "sampled (category, choice) pairs", len(sampled))
row("G3", "sampled rows (Future Society row 3?)", sorted({a for a, _ in sampled}))
sampled_nonempty = [k for k in sampled if k in nonempty]
row("G3", "sampled pairs that are non-empty cells", len(sampled_nonempty))
last_row = (len(CH) - 1) // NC
row("G3", "last category index", last_row)

# -------------------------------------------------------------- G4 reader
r_cat = win(0x4A6665, 0x4A66D9)
cat_base = 0x927B14
cho_base = 0x927B1C
row("G4", "category read @0x4a667b", txt(0x4A667B))
row("G4", "choice read @0x4a6693", txt(0x4A6693))
row("G4", "category offset (0x927b14-0x927590)", hex(cat_base - rec0))
row("G4", "choice offset (0x927b1c-0x927590)", hex(cho_base - rec0))
nmul = txt(0x4A66D9)
catname = txt(0x4A66DF)
choname = txt(0x4A66FF)
row("G4", "category-name lookup", nmul + " / " + catname)
row("G4", "choice-name lookup", choname)
row("G4", "choice-name array offset (0x92baac-0x92ba98)", hex(0x92BAAC - 0x92BA98))
row("G4", "text appends", sum(1 for a in win(0x4A66D9, 0x4A6710) if "call   0x4237c0" in txt(a)))
row("G4", "loop bound @0x4a6665", int(txt(0x4A6665).split(",")[-1], 16))

# -------------------------------------------------------------- G5 rivals
r1 = covered(0x92BABC)
d, secs = pe_sections()
r1_sec = [("%08x" % v, "%06x" % rs) for v, vs, ra, rs in secs if v <= 0x92BABC < v + vs]
facts = 7
for n, ln in enumerate(open(ALPHA, "r", errors="replace").read().splitlines()):
    if ln.strip().startswith("#FACTIONS"):
        facts = 0
        for ln2 in open(ALPHA, "r", errors="replace").read().splitlines()[n + 1:]:
            if not ln2.strip() or ln2.strip().startswith("#"):
                break
            facts += 1
        break
row("G5", "0x92babc inside section raw data?", r1)
row("G5", "containing section (va, raw size)", r1_sec)
row("G5", "#FACTIONS rows in alpha.txt", facts)
row("G5", "rival 11 columns = factions", 11 == facts)
row("G5", "rival cell = 12 dwords", (imm(txt(0x52B82C)) // 4, imm(txt(0x52B822))))
row("G5", "rival agenda can be Future Society", len({a for a, _ in sampled}) == len(CATS))

# ------------------------------------------------------------------- print
print("M376 what the 0x92babc grid is - the #SOCIO social-engineering matrix")
print("%-4s %-58s %s" % ("tag", "what", "value"))
for tag, what, val in ROWS:
    print("%-4s %-58s %s" % (tag, what, val))
print()

ok = True
ok &= check("G0", len(INS) == 781429 and h_txt.startswith("02d578095222"),
            "text %d insns sha %s" % (len(INS), h_txt[:12]))
ok &= check("G0", bts(0x5A11F3) == bytes.fromhex("8d8c8abcba9200") and
            bts(0x52B822) == bytes.fromhex("b90b000000"),
            "the cell lea and the 11-word copy are the bytes decoded below")

ok &= check("G1", CELLPOLY.get("a") == 0xD4 and CELLPOLY.get("b") == 0x2C and BASE == 0x92BABC,
            "emulator: cell = 0x92babc + %d*a + %d*b" % (CELLPOLY.get("a") or 0, CELLPOLY.get("b") or 0))
ok &= check("G1", txt(0x5A1193) == "idiv   ecx" and txt(0x5A11A2) == "idiv   ecx",
            "both random pickers divide by the loaded modulus (a, b)")
ok &= check("G1", imm(txt(0x5A1203)) == imm(txt(0x52B822)) == imm(txt(0x57AB94)) == len(KW),
            "cell width %d dwords = #SOCIO keyword count (copy, scan and zero counts agree)" % len(KW))
ok &= check("G1", NR == len(CATS) and NC == len(CH) // len(CATS),
            "rows %d = #SOCIO categories, %d cells/row = #SOCIO choices/category" % (NR, NC))
ok &= check("G1", (0x927538 - 0x9270C0) // 0x68 == len(KW) and 0x92BABC - 0x92BA98 == 9 * 4,
            "keyword array holds %d names; row header is %d dwords before the cells"
            % (len(KW), (0x92BABC - 0x92BA98) // 4))

ok &= check("G2", len(KW) == 11, "the 11 columns are the 11 alpha.txt #SOCIO effect keywords")
ok &= check("G2", txt(0x57ABE0) == "mov    esi,0x9270c0" and
            txt(0x57ABE7) == "call   0x64f8b0" and
            txt(0x57ABFC) == "add    esi,0x68" and txt(0x57ABFF) == "add    edi,0x4",
            "column i = strcmp(token, 0x9270c0 + i*0x68); edi advances one column per keyword")
ok &= check("G2", txt(0x57ABD2) == "inc    ecx" and txt(0x57ABD6) == "dec    ecx" and
            txt(0x57ABF8) == "add    eax,ecx",
            "the token's +/- count is ADDED to the column (signed weights)")
ok &= check("G2", len(empty) == len(CATS) and sorted({c for _, c in empty}) == [0] and
            len(nonempty) == len(CH) - len(CATS),
            "the 4 empty vectors are exactly choice 0 of each category (%s)"
            % ", ".join(CH[r * NC + c][0] for r, c in empty))
ok &= check("G2", all(v is not None for v in firstpos.values()) and firstpos[(0, 1)] == 2,
            "every non-empty cell has a first POSITIVE effect (Police State -> %s)"
            % KW[firstpos[(0, 1)]])

ok &= check("G3", txt(0x5A1150) == "test   DWORD PTR ds:0x985ae8,0x1000000" and reg == 0xC and
            txt(0x5A11A7) == "lea    eax,[edx+esi*2]" and txt(0x5A11AA) == "add    ecx,eax",
            "the bit-24 block zeroes a %d-dword used-pair registry indexed 3*a+b" % reg)
ok &= check("G3", 3 * (amod - 1) + bmod + 1 <= reg,
            "registry index 3*a+b max %d < %d" % (3 * (amod - 1) + bmod, reg))
ok &= check("G3", cat == 0x584 and cho == 0x58C and sig == 0x594 and idx == 1,
            "fields derived from the seed: category +%#x, choice +%#x, effect +%#x" % (cat, cho, sig))
ok &= check("G3", txt(0x4A667B) == "cmp    DWORD PTR [edx+eax*4+0x927b14],0x0" and
            cat_base - rec0 == cat and cho_base - rec0 == cho,
            "writer (+%#x/+%#x) and reader (0x927b14/0x927b1c) agree on the same two fields" % (cat, cho))
ok &= check("G3", txt(0x5A11FA) == "cmp    DWORD PTR [ecx],0x0" and txt(0x5A11FD) == "jg     0x5a120a",
            "the scan stops at the first weight > 0 inside the cell")
ok &= check("G3", rows_n == 8 and stride == 0x59C and len(sampled) == 9 and
            len(sampled_nonempty) == 9,
            "8 records hit by 9 distinct (category, choice) pairs, all non-empty")
ok &= check("G3", ALGO != 2 and len({a for a, _ in sampled}) == len(CATS) - 1 and last_row == 3,
            "the consumer samples rows 0..%d only - %s (row %d) is never an agenda"
            % (amod - 1, CATS[-1], last_row))
ok &= check("G3", writes[-1] > rec0 + 8 * stride,
            "measured: the 8th write (0x%x) lands past the 8-record block (0x%x)"
            % (writes[-1], rec0 + 8 * stride))

ok &= check("G4", txt(0x4A66D9) == "imul   eax,eax,0xd4" and
            txt(0x4A66DF) == "mov    ecx,DWORD PTR [eax+0x92ba98]",
            "the reader turns the stored category into [0x92ba98 + d*0xd4] = the NAME")
ok &= check("G4", txt(0x4A66FF) == "mov    ecx,DWORD PTR [edx+eax*4+0x92baac]" and
            0x92BAAC - 0x92BA98 == 0x14,
            "the stored choice indexes the row's name array at +0x14")
ok &= check("G4", sum(1 for a in win(0x4A66D9, 0x4A6710) if "call   0x4237c0" in txt(a)) == 2,
            "both names are appended to the same text buffer (category then choice)")

ok &= check("G5", r1 is False,
            "RIVAL 'the table is initialized .data' FAILS: 0x92babc is in %s raw %s B - BSS"
            % (r1_sec[0][0] if r1_sec else "?", r1_sec[0][1] if r1_sec else "?"))
ok &= check("G5", 11 != facts,
            "RIVAL 'the 11 columns are factions' FAILS: alpha.txt #FACTIONS has %d rows" % facts)
ok &= check("G5", imm(txt(0x52B82C)) // 4 == len(KW) != 12,
            "RIVAL 'a cell is 12 dwords' FAILS: stride %#x = %d dwords" % (imm(txt(0x52B82C)), len(KW)))
ok &= check("G5", ALGO != 2 and len({a for a, _ in sampled}) != len(CATS),
            "RIVAL 'an agenda can be a Future Society choice' FAILS: only %d of %d rows are sampled"
            % (len({a for a, _ in sampled}), len(CATS)))

dig = hashlib.sha1(repr(ROWS).encode()).hexdigest()[:16]
print()
print("%s M376: %d/%d gates digest %s" % ("PASS" if ok else "FAIL", NG[0] if ok else 0, NG[0], dig))
sys.exit(0 if ok else 1)
