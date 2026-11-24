#!/usr/bin/env python3
"""M393 - WHO WRITES THE SECOND AGENDA PAIR (+0x588 / +0x590 of the 0x927590 record block).

M388 showed slot 0's FIRST pair (+0x584/+0x58c) has no writer and left a lead: the
record carries a SECOND (category, choice) pair at +0x588/+0x590 that FUN_00522b70
reads against the live SE grid, with 0 stores in the image.  Dead layout, or a writer
behind a copy / an indirect store?

This instrument answers it from the INSTRUCTION BYTES of terran.exe plus the PE header:

  G0  anchors: image + disassembly sha1s, instruction count, PE section table.
  G1  geometry, measured from the two READERS' own arithmetic: the 0x59c stride, the
      four field anchors 0x927b14/18/1c/20, the 8-slot block and slot k's pair-2 address.
  G2  naive store census: every store whose displacement is 0x588/0x590 or whose disp32
      lands inside the block.
  G3  offset-folded store census: a per-function forward pass that tracks each base
      register's constant delta (mov imm / lea / add / sub) and reports the AGGREGATE
      displacement.  It is validated by a POSITIVE CONTROL - it must find the
      randomizer's own +0x584/+0x58c store pair, which the naive census cannot see
      (their displacements are -8 / 0 / +8 off a register).
  G4  immediate-class census over every reference into the block: stores, pushes,
      pointer seeds (mov/lea reg,imm).
  G5  the image: the block lies past .data's raw extent, so the loader zero-fills it -
      there is no static initialiser.  The only byte-level writer is the save/load
      mover (FUN_00596540), a transport, measured by its own store.
  G6  the readers: 8 references (4 per field), all loads, 0 stores; the three
      consumers and what each one needs to fire.  Under the measured invariant
      pair2 == (0,0) two of them cannot fire at all and the third reduces to
      "A's FIRST pair == (0,0)".
  G7  rivals, each computed on the same numbers and each asserted to FAIL.

M393_PATCH='addr|text;addr|text'  rewrites one instruction line (mutation lever).
M393_ALGO=n  1 = field map shifted (the randomizer's +8 store lands on +0x590);
             2 = the block byte copy counts as a producer;
             3 = naive census only (no offset folding);
             4 = the image is treated as statically initialised;
             5 = the randomizer's roll is rand%3 with no +1 (choice1 0..2);
             6 = the picker's candidate skip is taken as firing.
M393_TEXT / M393_EXE  alternate inputs.
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M393_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.environ.get("M393_EXE", os.path.join(ROOT, "programs/terran.exe"))
ALGO = int(os.environ.get("M393_ALGO", "0") or 0)

TEXT_SHA1 = "02d578095222031ea4c84c1eb7406e20edcc5361"
BLOCK_LO, BLOCK_HI = 0x927590, 0x92a270          # measured below from the save/load push
ANCHORS = (0x927b14, 0x927b18, 0x927b1c, 0x927b20)   # measured below from the readers
CAT2_OFF, CHOICE2_OFF = 0x588, 0x590

NONSTORE = {"cmp", "test", "lea", "push", "call", "jmp", "je", "jne", "jz", "jnz",
            "jl", "jg", "jle", "jge", "jb", "ja", "jbe", "jae", "js", "jns", "jo",
            "jno", "jp", "jnp", "loop", "ret", "nop", "int3", "in", "out", "cdq",
            "cwde", "pop", "movzx", "movsx", "fld", "fst", "fstp", "fild", "fistp",
            "seta", "setb", "setne", "sete", "setl", "setg", "sbb", "adc", "neg",
            "not", "shl", "shr", "sar", "xor", "and", "or", "imul", "idiv", "mul",
            "div", "inc", "dec", "rep", "stos", "movs", "xchg"}
W16 = {"ax": "eax", "bx": "ebx", "cx": "ecx", "dx": "edx", "si": "esi", "di": "edi",
       "bp": "ebp", "sp": "esp"}
W8 = {"al": "eax", "bl": "ebx", "cl": "ecx", "dl": "edx", "ah": "eax", "bh": "ebx",
      "ch": "ecx", "dh": "edx"}

checks = []
table = []


def say(tag, text):
    line = "%-3s %s" % (tag, text)
    table.append(line)
    print(line)


def check(name, ok):
    checks.append((name, bool(ok)))
    return bool(ok)


# ---------------------------------------------------------------- instruction image
def load():
    rows = {}
    sha = hashlib.sha1()
    with open(TEXT, "rb") as f:
        raw = f.read()
    sha.update(raw)
    for line in raw.decode("latin-1").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        try:
            a = int(parts[0].strip().rstrip(":"), 16)
        except ValueError:
            continue
        rows[a] = parts[2].strip()
    patch = os.environ.get("M393_PATCH", "")
    for item in filter(None, patch.split(";")):
        a, _, t = item.partition("|")
        rows[int(a, 16)] = t.strip()
    if ALGO == 5:                       # the roll loses its +1
        rows[0x5a11a6] = "dec    edx"
    return rows, sha.hexdigest(), len(raw)


INS, TXTSHA, TXTLEN = load()
ORDER = sorted(INS)


def ins(a):
    return INS.get(a, "<missing>")


def imm(t, nth=0):
    xs = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]+)", t)]
    return xs[nth] if len(xs) > nth else None


def split_op(t):
    p = t.split(None, 1)
    if len(p) < 2:
        return p[0], None
    ops, depth, cur = [], 0, ""
    for ch in p[1]:
        if ch == "[":
            depth += 1
        if ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            ops.append(cur)
            cur = ""
        else:
            cur += ch
    ops.append(cur)
    return p[0], [o.strip() for o in ops]


def membody(x):
    m = re.search(r"\[([^\]]*)\]", x)
    return m.group(1) if m else None


def disp_of(body):
    v = 0
    for sign, hx in re.findall(r"([+-]?)\s*0x([0-9a-fA-F]+)", body):
        v += -int(hx, 16) if sign == "-" else int(hx, 16)
    return v


def base_of(body):
    m = re.search(r"(?<![a-z0-9])(e[a-ds][xip])(?!\s*\*)", body)
    return m.group(1) if m else None


def reg_of(x):
    x = x.strip()
    if x in W16:
        return W16[x]
    if x in W8:
        return W8[x]
    return x if x in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp") else None


def is_store(op, ops):
    return ops is not None and op not in NONSTORE and "[" in ops[0]


_S = None


def own(a):
    global _S
    import bisect
    if _S is None:
        _S = sorted(json.load(open(os.path.join(ROOT, ".func_starts.json"))))
    return _S[bisect.bisect_right(_S, a) - 1]


def exe_sha1():
    h = hashlib.sha1()
    with open(EXE, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- G0 anchors
say("G0", "exe sha1                %s" % exe_sha1())
say("G0", "disassembly sha1        %s  (%d B, %d instructions)" % (TXTSHA, TXTLEN, len(INS)))
check("G0 exe present", os.path.getsize(EXE) > 1 << 20)
check("G0 text sha pinned", TXTSHA == TEXT_SHA1)
check("G0 instruction count", len(INS) > 700000)

# PE header: which bytes the image actually carries
with open(EXE, "rb") as f:
    pe = f.read(0x400)
e_lfanew = int.from_bytes(pe[0x3c:0x40], "little")
nsect = int.from_bytes(pe[e_lfanew + 6:e_lfanew + 8], "little")
optsz = int.from_bytes(pe[e_lfanew + 20:e_lfanew + 22], "little")
imgbase = int.from_bytes(pe[e_lfanew + 24 + 28:e_lfanew + 24 + 32], "little")
secoff = e_lfanew + 24 + optsz
sects = []
for i in range(nsect):
    s = pe[secoff + i * 40:secoff + i * 40 + 40]
    name = s[:8].rstrip(b"\0").decode("latin-1")
    vs, va, rs, ro = (int.from_bytes(s[8 + 4 * k:12 + 4 * k], "little") for k in range(4))
    sects.append((name, imgbase + va, imgbase + va + rs, imgbase + va + vs, ro))
say("G0", "image base              %#x" % imgbase)
for nm, vlo, vraw, vhi, ro in sects:
    say("G0", "section %-8s  VA %#010x  file-backed %#010x  vsize-end %#010x" %
        (nm, vlo, vraw, vhi))
dot = [s for s in sects if s[0] == ".data"][0]
say("G0", ".data raw/file-backed end %#x  virtual end %#x  block %#x..%#x" %
    (dot[2], dot[3], BLOCK_LO, BLOCK_HI))
block_past_raw = BLOCK_LO >= dot[2]
if ALGO == 4:      # the image is claimed to carry static initial bytes for the block
    block_past_raw = False
say("G0", "block past .data file-backed end   %s" % block_past_raw)

# ---------------------------------------------------------------- G1 geometry
SITES = [(0x522de1, "cat1"), (0x522e23, "cat2"), (0x522e07, "choice1"), (0x522e49, "choice2")]
for a, nm in SITES:
    say("G1", "reader %-7s @0x%x  %s" % (nm, a, ins(a)))
anchors = sorted({imm(ins(a)) for a, _ in SITES})
say("G1", "field anchors           %s" % [hex(x) for x in anchors])

# the reader's own record-index multiply: 0x522dd3..0x522dde
seq = [ins(a) for a in range(0x522dd3, 0x522ddf)]
mul = 1
for t in seq:
    m = re.search(r"lea\s+\w+,\[\w+\+\w+\*(\d)\]", t)
    if m:
        mul *= 1 + int(m.group(1))
    m = re.search(r"shl\s+\w+,0x([0-9a-f]+)", t)
    if m:
        mul *= 1 << int(m.group(1), 16)
    m = re.search(r"\bsub\s+\w+,(\w+)$", t)
    if m:
        mul -= 1
say("G1", "reader stride (0x522dd3..de) %#x" % mul)
pair2_abs = sorted({ANC[1] + k * mul for ANC in [(0, 0x927b18)] for k in range(8)} |
                   {0x927b20 + k * mul for k in range(8)})
say("G1", "slot0 cat2 / choice2    %#x / %#x" % (0x927b18, 0x927b20))
say("G1", "7 more slots, last      %#x / %#x" % (pair2_abs[-2], pair2_abs[-1]))
slots = [BLOCK_LO + k * mul for k in range(8)]
say("G1", "slot0 base              %#x  (block push @0x596ea9)" % BLOCK_LO)
say("G1", "block size push @0x596ea4 %#x  == 8*stride %s" % (imm(ins(0x596ea4)), imm(ins(0x596ea4)) == 8 * mul))
check("G1 stride from reader", mul == 0x59c)
check("G1 four field anchors", anchors == list(ANCHORS))
check("G1 block size 8*stride", imm(ins(0x596ea4)) == 8 * mul and slots[-1] + mul == BLOCK_HI)

# ---------------------------------------------------------------- G2 naive census
naive_pair, naive_block = [], []
for a in ORDER:
    op, ops = split_op(INS[a])
    if not ops or not is_store(op, ops):
        continue
    b = membody(ops[0])
    if b is None:
        continue
    d = disp_of(b)
    if d in (CAT2_OFF, CHOICE2_OFF):
        naive_pair.append((a, INS[a]))
    if BLOCK_LO <= d < BLOCK_HI:
        naive_block.append((a, INS[a], d))
say("G2", "stores with disp 0x588/0x590        %d" % len(naive_pair))
for a, t in naive_pair:
    say("G2", "   0x%x %s" % (a, t))
say("G2", "stores with disp32 inside the block  %d" % len(naive_block))
for a, t, d in naive_block:
    say("G2", "   0x%x %-44s -> slot off %#x" % (a, t, d - BLOCK_LO))
check("G2 naive pair stores == 0", len(naive_pair) == 0)
check("G2 naive block stores == 2 at +0", len(naive_block) == 2 and
      all(d == BLOCK_LO for _, _, d in naive_block))

# ---------------------------------------------------------------- G3 offset-folded census
def folded():
    deltas, abs_hits, agg_w = {}, [], []
    for a in ORDER:
        op, ops = split_op(INS[a])
        if not ops:
            continue
        if is_store(op, ops):
            b = membody(ops[0])
            if b is not None:
                base, d = base_of(b), disp_of(b)
                dl = deltas.get(base)
                agg = (dl or 0) + d
                if dl is not None and BLOCK_LO <= agg < BLOCK_HI:
                    rel = agg - BLOCK_LO
                    abs_hits.append((a, INS[a], base, dl, agg, rel // mul, rel % mul))
                # an OBJECT base only: ebp/esp are stack frames, not objects
                if 0x580 <= agg < 0x59c and base not in ("esp", "ebp"):
                    agg_w.append((a, INS[a], base, dl, agg))
        d0 = reg_of(ops[0]) if ops[0] else None
        if op == "lea" and d0 and "[" in ops[0]:
            b = membody(ops[0])
            src = base_of(b) if b else None
            if b and "*" not in b and src:
                deltas[d0] = deltas.get(src, 0) + disp_of(b)
            else:
                deltas[d0] = 0
        elif op in ("add", "sub") and d0 and len(ops) > 1:
            v = imm(ops[1])
            if v is not None:
                deltas[d0] = deltas.get(d0, 0) + (v if op == "add" else -v)
            else:
                deltas[d0] = 0
        elif op == "mov" and d0 and len(ops) > 1:
            t2 = ops[1].strip()
            v = imm(t2) if re.match(r"^0x[0-9a-fA-F]+$", t2) else None
            deltas[d0] = v if v is not None else 0
        elif d0:
            deltas[d0] = 0
    return abs_hits, agg_w


ABS_HITS, AGGW = folded()
if ALGO == 1:      # the randomizer's +8 store is claimed to land on +0x590
    ABS_HITS = [(a, t, b, d, g, s, (o + 4) % mul) for a, t, b, d, g, s, o in ABS_HITS]
if ALGO == 3:      # no offset folding at all
    ABS_HITS = []
ctrl = [h for h in ABS_HITS if h[6] in (0x584, 0x58C, 0x594)]
say("G3", "offset-folded absolute hits in block %d" % len(ABS_HITS))
for a, t, b, dl, agg, slot, off in ABS_HITS:
    say("G3", "   0x%x %-42s %s+%#x -> slot %d +%#x" % (a, t, b, dl, slot, off))
say("G3", "  of those on +0x584/+0x58c/+0x594 (ctrl) %d" % len(ctrl))
for a, t, b, dl, agg, slot, off in ctrl:
    say("G3", "     ctrl 0x%x slot %d +%#x" % (a, slot, off))
pair_hits = [h for h in ABS_HITS if h[6] in (CAT2_OFF, CHOICE2_OFF)]
say("G3", "  of those on any slot's cat2/choice2 %d" % len(pair_hits))
say("G3", "aggregate-disp stores in [0x580,0x59c) %d" % len(AGGW))
for a, t, b, dl, agg in AGGW:
    say("G3", "   0x%x %-42s base=%s delta=%s agg=%#x" % (a, t, b, dl, agg))
agg_pair = [w for w in AGGW if w[4] in (CAT2_OFF, CHOICE2_OFF)]
say("G3", "  of those at aggregate disp 0x588/0x590 %d" % len(agg_pair))
check("G3 control finds the first-pair writer", len(ctrl) == 6 and
      sorted({h[6] for h in ctrl}) == [0x584, 0x58C, 0x594] and
      {0x5A11D1, 0x5A11D4, 0x5A120A} <= {h[0] for h in ctrl})
check("G3 no folded store on cat2/choice2", len(pair_hits) == 0)
check("G3 no aggregate store at 0x588/0x590", len(agg_pair) == 0)

# each of the 12 window candidates belongs to a function with no block reference
def owner_block_refs(a):
    f = own(a)
    ls = ORDER
    import bisect
    i = bisect.bisect_left(ls, f)
    n = 0
    while i < len(ls) and own(ls[i]) == f:
        t = INS[ls[i]]
        if any(int(x, 16) == BLOCK_LO for x in re.findall(r"0x([0-9a-fA-F]+)", t)):
            n += 1
        i += 1
    return n


win_owners = sorted({w[0] and own(w[0]) for w in AGGW})
win_refs = {hex(f): owner_block_refs(f) for f in win_owners}
say("G3", "window candidates' owners  %s" % json.dumps(win_refs))
check("G3 window candidates are other objects",
      all(v == 0 for v in win_refs.values()))

# ---------------------------------------------------------------- G4 immediate census
cls, seeds, pushes = {}, [], []
for a in ORDER:
    op, ops = split_op(INS[a])
    if not ops:
        continue
    t = INS[a]
    hit = None
    for m in re.findall(r"0x([0-9a-fA-F]+)", t):
        v = int(m, 16)
        if BLOCK_LO <= v < BLOCK_HI:
            hit = v
            break
    if hit is None:
        continue
    cls[op] = cls.get(op, 0) + 1
    if op == "push":
        pushes.append((a, hit))
    # a POINTER SEED carries the address as its VALUE: mov reg,imm, or lea reg,[imm]
    is_imm = (op == "mov" and len(ops) > 1 and re.match(r"^0x[0-9a-fA-F]+$", ops[1].strip())
              and imm(ops[1]) == hit)
    if op == "lea" and len(ops) > 1:
        b = membody(ops[1]) or ""
        is_imm = base_of(b) is None and imm(ops[1]) == hit
    if is_imm and any(hit in (0x927b18 + k * mul, 0x927b20 + k * mul) for k in range(8)):
        seeds.append((a, t, hit))
say("G4", "immediate refs into block %d  by op %s" % (sum(cls.values()), sorted(cls.items(), key=lambda x: -x[1])))
say("G4", "  pushes  %s" % [(hex(a), hex(v)) for a, v in pushes])
say("G4", "  pointer seeds on a pair address %d" % len(seeds))
for a, t, v in seeds:
    say("G4", "   0x%x %s" % (a, t))
check("G4 no pair pointer seed", len(seeds) == 0)
check("G4 pushes are the transfer entries", len(pushes) == 5 and
      [hex(v) for _, v in pushes] == [hex(BLOCK_LO), hex(BLOCK_LO), "0x927914", "0x927874", "0x927894"])

# ---------------------------------------------------------------- G5 image + transport
# transport: FUN_00596540 (read) de-obfuscates into its first argument
say("G5", "loader FUN_00596540 store @0x5965de  %s" % ins(0x5965de))
say("G5", "  its destination                   %s" % ins(0x596598))
say("G5", "  its file read @0x596578           %s" % ins(0x596578))
say("G5", "transfer calls @0x596ecf/0x596ed6  %s  /  %s" % (ins(0x596ecf), ins(0x596ed6)))
say("G5", "transfer calls @0x596eb0/0x596eb7  %s  /  %s" % (ins(0x596eb0), ins(0x596eb7)))
say("G5", "transfer args  @0x596ec3/0x596ec8  %s %s" % (ins(0x596ec3), ins(0x596ec8)))
transport_ok = ("BYTE PTR [edi],al" in ins(0x5965DE) and
                "edi,DWORD PTR [ebp+0x8]" in ins(0x596598) and
                imm(ins(0x596578)) == 0x64CC00 and          # the read path is fread
                imm(ins(0x596ED6)) == 0x64CC00 and
                imm(ins(0x596ECF)) == 0x64C9A0 and
                imm(ins(0x596EB7)) == 0x596540 and
                imm(ins(0x596EB0)) == 0x596470 and
                imm(ins(0x596EC8)) == BLOCK_LO and
                imm(ins(0x596EC3)) == 8 * mul)
if ALGO == 2:                       # the copy is accepted as a producer
    say("G5", "ALGO=2: the byte copy is counted as a PRODUCER")
check("G5 block is loader-zero (no static init)", block_past_raw)
check("G5 only byte writer is the load transport", transport_ok)
producers = len(pair_hits) + len(agg_pair) + len(seeds)
if ALGO == 2:
    producers += 1
say("G5", "producers of cat2/choice2         %d" % producers)
check("G5 zero producers", producers == 0)

# ---------------------------------------------------------------- G6 readers
refs = {}
for a in ORDER:
    t = INS[a]
    for m in re.findall(r"0x([0-9a-fA-F]+)", t):
        v = int(m, 16)
        if v in (0x927b18, 0x927b20):
            refs.setdefault(v, []).append((a, t))
            break
say("G6", "references to cat2  %d" % len(refs.get(0x927b18, [])))
for a, t in refs.get(0x927b18, []):
    say("G6", "   0x%x %s" % (a, t))
say("G6", "references to choice2 %d" % len(refs.get(0x927b20, [])))
for a, t in refs.get(0x927b20, []):
    say("G6", "   0x%x %s" % (a, t))
all_refs = refs.get(0x927b18, []) + refs.get(0x927b20, [])
is_load = [1 for a, t in all_refs if re.match(r"^(mov|cmp)\b", t)]
st_sites = [a for a, t in all_refs if (split_op(t)[1] and is_store(*split_op(t)))]
say("G6", "of them loads/cmp %d, stores %d" % (len(is_load), len(st_sites)))
# the randomizer's roll: two idiv 3, the second +1
say("G6", "roll 1 @0x5a118e %s ; roll 2 @0x5a11a2 %s ; +1 @0x5a11a6 %s ; store @0x5a11d1 %s" %
    (ins(0x5a118e), ins(0x5a11a2), ins(0x5a11a6), ins(0x5a11d1)))
say("G6", "sentinel presets @0x5a1180/83/85 %s / %s / %s" %
    (ins(0x5a1180), ins(0x5a1183), ins(0x5a1185)))
lo_choice = 1 if ("inc" in ins(0x5a11a6)) else 0
say("G6", "choice1 range                     %d..3" % lo_choice)
# candidate skip guard in the picker
cand_mask = imm(ins(0x5a1dbc))
skip_zero = "je" in ins(0x5a1dc1)
say("G6", "picker candidate mask @0x5a1dbc   %s  (choice = idx & %s)" % (ins(0x5a1dbc), cand_mask))
say("G6", "picker zero-choice skip @0x5a1dc1 %s  -> skip=%s" % (ins(0x5a1dc1), skip_zero))
say("G6", "scorer zero-cell guard @0x522e45 %s / %s" % (ins(0x522e45), ins(0x522e47)))
say("G6", "predicate FUN_005a1a70 callers    %s" %
    [hex(a) for a in ORDER if re.search(r"call\s+0x5a1a70$", INS[a])])
check("G6 eight references, 4 per field", len(refs.get(0x927b18, [])) == 4 and
      len(refs.get(0x927b20, [])) == 4)
check("G6 every reference is a load/cmp", len(st_sites) == 0 and len(is_load) == 8)
check("G6 choice1 is 1..3", lo_choice == 1)
check("G6 scorer guard skips a zero grid cell", "je" in ins(0x522e47) and "test" in ins(0x522e45))

# ---------------------------------------------------------------- G7 inertness + rivals
choice2 = 0 if producers == 0 else None          # the producer census sets it
cand_choices = [c for c in range((cand_mask or 0) + 1) if not (skip_zero and c == 0)]
if ALGO == 6:                                    # the zero-choice skip is dropped
    cand_choices = [c for c in range((cand_mask or 0) + 1)]
if ALGO == 7:                                    # choice2 inherits pair1's range
    choice2 = lo_choice
say("G7", "measured: choice2=%s  candidate choices=%s  zero-cell guard=%s" %
    (choice2, cand_choices, "je" in ins(0x522e47)))
# R1: the predicate is true only for the pair it is handed
r1 = (choice2 == 0)
# R2: the picker skips candidate == pair2 -> needs a comparable candidate choice == 0
r2_fires = choice2 in cand_choices
# R3: the scorer's match needs a NONZERO grid cell equal to choice2
r3_fires = (not ("je" in ins(0x522e47))) or (choice2 != 0)
# R4: the mirror branch (A.pair1 == B.pair2) reduces to A.pair1 == (0,0)
r4_reduces_to = "A.pair1 == (0,0)" if choice2 == 0 else "not reduced"
say("G7", "R1 predicate  fires only on the pair (0,0)      -> %s" % r1)
say("G7", "R2 picker     skip fires when %s in %s           -> %s" % (choice2, cand_choices, r2_fires))
say("G7", "R3 scorer     nonzero grid cell == choice2       -> %s" % r3_fires)
say("G7", "R4 mirror     B.pair2==(0,0) => %s" % r4_reduces_to)

rivals = [
    ("RIVAL-1 the +8 store seeds the pair", [h for h in ctrl if h[6] == CHOICE2_OFF], False),
    ("RIVAL-2 a static init sets the pair", [1 for _ in [0] if not block_past_raw], False),
    ("RIVAL-3 a window store hits a 0x59c record", [v for v in win_refs.values() if v], False),
]
for name, found, want in rivals:
    say("G7", "%-46s found=%d  rival holds=%s" % (name, len(found), bool(found) == want))
check("G7 RIVAL-1 fails", len([h for h in ctrl if h[6] == CHOICE2_OFF]) == 0)
check("G7 RIVAL-2 fails", block_past_raw)
check("G7 RIVAL-3 fails", all(v == 0 for v in win_refs.values()))
check("G7 R2 cannot fire", r2_fires is False)
check("G7 R3 cannot fire", r3_fires is False)

failed = [n for n, ok in checks if not ok]
digest = hashlib.sha1(("\n".join(table) + "|" + ",".join(n for n, _ in checks)).encode()).hexdigest()[:16]
print("")
if failed:
    print("FAIL M393: %d/%d failed: %s" % (len(failed), len(checks), "; ".join(failed[:6])))
    sys.exit(1)
print("PASS M393: %d/%d  %s" % (len(checks), len(checks), digest))
