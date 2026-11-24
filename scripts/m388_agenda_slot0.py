#!/usr/bin/env python3
"""M388 - WHO WRITES SLOT 0'S AGENDA PAIR (+0x584 / +0x58c of the 0x927590 record block).

M376 showed the bit-24 "randomize social agendas" pass stores a (category, choice,
signature-effect) triple per faction record; M379 fixed its loop at 7 bodies and the
record stride at 0x59c.  The pick asked who writes slot 0's pair - the pair the
randomizer never seeds - on the guess that it is the human player's own SE choices.

This instrument answers it from the INSTRUCTION BYTES of terran.exe only:

  G0  anchors: image + disassembly sha1s, instruction count.
  G1  the randomizer's own loop: seed imm, stride, loop init and bound -> the 7 record
      bases it writes and the ONE record base it cannot reach; slot 0's pair address
      falls out of the arithmetic, never authored.
  G2  writer census, four independent store sets:
        (a) stores whose memory operand carries displacement 0x584/0x588/0x58c/0x590/0x594
        (b) stores whose disp32 lies INSIDE the block [0x927590,0x92a270)
        (c) stores in the compiler's folded form [idx*0x59c + 0x927b14/18/1c/20]
        (d) pointer seeds: mov reg,imm into the block, and every whole-block transfer
      Slot 0's pair is targeted by none of them.
  G3  the SE path: the dialog's key handlers -> the SE commit -> the LIVE grid
      (0x94d658 + faction*0x20bc + category*4).  The commit's own store set contains
      the grid and no block address: the grid is COMPARED to the agenda, never copied
      into it.
  G4  the sentinel: the randomizer can only produce choices 1..3 (idiv 3, inc), and
      every scorer bails on choice == 0 - so the unwritten slot 0 is a designed
      "no agenda" row, not an unseeded copy of anyone's SE choices.
  G5  rivals, each computed on the same numbers and each asserted to FAIL.

M388_PATCH='addr|text;addr|text'  rewrites one instruction line (mutation lever).
M388_ALGO=n  1 = the randomizer starts at record 0; 2 = every [reg+0x584] store is a
             record store.  Both must redden a gate (see scripts/m388_mutate.py).
M388_TEXT / M388_EXE  alternate inputs.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M388_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.environ.get("M388_EXE", os.path.join(ROOT, "programs/terran.exe"))
ALGO = int(os.environ.get("M388_ALGO", "0") or 0)

XVFER_SITE = 0x596ea4          # push of the block size (measured below)
TEXT_SHA1 = "02d578095222031ea4c84c1eb7406e20edcc5361"

NONSTORE = {"cmp", "test", "lea", "push", "call", "jmp", "je", "jne", "jz", "jnz",
            "jl", "jg", "jle", "jge", "jb", "ja", "jbe", "jae", "js", "jns", "jo",
            "jno", "jp", "jnp", "loop", "ret", "nop", "int3", "in", "out", "cdq",
            "cwde", "pop", "movzx", "movsx", "fld", "fst", "fstp", "fild", "fistp"}

checks = []
table = []


def say(tag, text):
    line = "%-4s %s" % (tag, text)
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
    patch = os.environ.get("M388_PATCH", "")
    for item in filter(None, patch.split(";")):
        a, _, t = item.partition("|")
        rows[int(a, 16)] = t.strip()
    if ALGO == 1:                       # the randomizer starts at record 0
        rows[0x5a116a] = "mov    ebx,0x0"
    return rows, sha.hexdigest(), len(raw)


INS, TXTSHA, TXTLEN = load()


def ins(a):
    return INS.get(a, "<missing>")


def imm(t, nth=0):
    xs = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]+)", t)]
    return xs[nth] if len(xs) > nth else None


def mem(t):
    i = t.find("[")
    return t[i:t.find("]", i) + 1] if i >= 0 else None


def disp(t):
    m = mem(t)
    if not m:
        return None
    neg = re.search(r"-0x([0-9a-fA-F]+)", m)
    if neg:
        return -int(neg.group(1), 16)
    xs = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]+)", m)]
    return xs[-1] if xs else 0


def dst(t):
    p = t.split(None, 1)
    return p[1].split(",")[0].strip() if len(p) > 1 else ""


def is_store(t):
    p = t.split(None, 1)
    if len(p) < 2 or p[0] in NONSTORE:
        return False
    return "[" in dst(t)


def win(lo, hi):
    return [(a, INS[a]) for a in sorted(INS) if lo <= a < hi]


def owner(a):
    import bisect
    global _STARTS
    try:
        _STARTS
    except NameError:
        import json
        _STARTS = sorted(json.load(open(os.path.join(ROOT, ".func_starts.json"))))
    return _STARTS[bisect.bisect_right(_STARTS, a) - 1]


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

# ---------------------------------------------------------------- G1 the randomizer loop
SEED_SITE, STRIDE_SITE, INIT_SITE, BOUND_SITE, STORE_SITES = 0x5a1171, 0x5a120d, 0x5a116a, 0x5a1213, (0x5a11d1, 0x5a11d4, 0x5a120a)
say("G1", "seed      @0x5a1171     %s" % ins(SEED_SITE))
say("G1", "stride    @0x5a120d     %s" % ins(STRIDE_SITE))
say("G1", "loop init @0x5a116a     %s" % ins(INIT_SITE))
say("G1", "loop bound@0x5a1213     %s" % ins(BOUND_SITE))
for a in STORE_SITES:
    say("G1", "pair store@0x%x       %s" % (a, ins(a)))

seed, stride = imm(ins(SEED_SITE)), imm(ins(STRIDE_SITE))
init, bound = imm(ins(INIT_SITE)), imm(ins(BOUND_SITE))
say("G1", "seed / stride           %#x / %#x" % (seed, stride))
say("G1", "loop index start/bound  %d / %d" % (init, bound))

nrec = bound - init
say("G1", "records walked          %d" % nrec)
writes = [seed + k * stride for k in range(nrec)]
bases = [w - 0x58c for w in writes]
say("G1", "first/last choice store %#x / %#x" % (writes[0], writes[-1]))
say("G1", "first/last record base  %#x / %#x" % (bases[0], bases[-1]))
block_end = bases[-1] + stride
say("G1", "walk block end          %#x" % block_end)
slot0 = bases[0] - stride

# the three stores that define the field layout, all displacements measured
field_base = seed - bases[0]                      # the field the walk pointer starts on
cat_off = field_base + disp(ins(0x5a11d1))        # the [edi-0x8] store
hi_off = field_base + disp(ins(0x5a120a))         # the [edi+0x8] store
lo_addr, hi_addr = slot0 + cat_off, slot0 + hi_off
AGENDA_WINDOW = tuple(sorted({cat_off, field_base, hi_off} |
                             {d - slot0 for _, t in INS.items()
                              for d in [disp(t)] if d is not None and lo_addr <= d <= hi_addr}))
FIELD_PAIR = (cat_off, field_base)
BLOCK_SIZE_IMM = imm(ins(XVFER_SITE))
say("G1", "store disps -8 / +8      %d / %d" % (disp(ins(0x5a11d1)), disp(ins(0x5a120a))))
say("G1", "field base / cat / hi    %#x / %#x / %#x" % (field_base, cat_off, hi_off))
say("G1", "agenda window            %s" % [hex(x) for x in AGENDA_WINDOW])
say("G1", "block size push @0x596ea4 %#x" % BLOCK_SIZE_IMM)
pair = (slot0 + FIELD_PAIR[0], slot0 + FIELD_PAIR[1])
say("G1", "slot 0 base             %#x" % slot0)
say("G1", "slot 0 CAT / CHOICE     %#x / %#x" % pair)

check("G1 seed imm", seed == 0x9280b8)
check("G1 stride", stride == 0x59c)
check("G1 loop starts at 1", init == 1)
check("G1 loop bound 8", bound == 0x8)
check("G1 7 records walked", nrec == 7)
check("G1 slot0 = base1 - stride", slot0 == 0x927590 and bases[0] == 0x927b2c)
check("G1 slot0 pair = 0x927b14/0x927b1c", pair == (0x927b14, 0x927b1c))
check("G1 slot0 pair below every write", pair[1] < min(writes) - 8)
check("G1 block = 8 rec (walk ends at its bound)", block_end == 0x92a270 and block_end - slot0 == (nrec + 1) * stride)
check("G1 block size imm = 8*stride", BLOCK_SIZE_IMM == (nrec + 1) * stride)

# ---------------------------------------------------------------- G2 writer census
stores = [(a, t) for a, t in sorted(INS.items()) if is_store(t)]
say("G2", "stores in image         %d" % len(stores))


def disp_store_set(want):
    out = []
    for a, t in stores:
        d = disp(t)
        if d is not None and d in want:
            out.append((a, t))
    return out


set_a = disp_store_set(set(AGENDA_WINDOW))
say("G2", "(a) stores with disp in agenda window %s" % sorted(hex(d) for d in AGENDA_WINDOW))
for a, t in set_a:
    say("G2", "    0x%x %s" % (a, t))
say("G2", "(a) count               %d" % len(set_a))

# a ctor store may only be a record store if its function can build a record address
set_a_rec = []
for a, t in set_a:
    body = " ".join(x for _, x in win(owner(a), owner(a + 1) if owner(a + 1) > owner(a) else owner(a) + 1))
    if "0x59c" in body or "0x927" in body:
        set_a_rec.append((a, t))
if ALGO == 2:                            # every [reg+0x584] store counts as a record store
    set_a_rec = list(set_a)
say("G2", "(a) of those inside a 0x59c/0x927 context   %d" % len(set_a_rec))

set_b = [(a, t) for a, t in stores if (disp(t) is not None and slot0 <= disp(t) < block_end)]
say("G2", "(b) stores with disp32 inside the block")
for a, t in set_b:
    say("G2", "    0x%x %s" % (a, t))
say("G2", "(b) count               %d" % len(set_b))
set_b_pair = [(a, t) for a, t in set_b if (disp(t) - slot0) in AGENDA_WINDOW]
say("G2", "(b) of those landing in the agenda window    %d" % len(set_b_pair))

fold = {slot0 + o for o in AGENDA_WINDOW}
set_c_st = [(a, t) for a, t in stores if disp(t) in fold]
set_c_all = [(a, t) for a, t in INS.items() if disp(t) in fold]
say("G2", "(c) folded disp [i*0x59c+0x927b14..20]: loads/cmp/lea %d, stores %d"
    % (len(set_c_all), len(set_c_st)))
for a, t in set_c_all:
    say("G2", "    0x%x %-8s %s" % (a, "STORE" if is_store(t) else "-", t))

seed_re = re.compile(r"^(mov|lea)\s+[a-z]{2,3},0x([0-9a-f]+)$")
seeds = []
for a, t in sorted(INS.items()):
    m = seed_re.match(t)
    if m:
        v = int(m.group(2), 16)
        if slot0 <= v < block_end:
            seeds.append((a, v, t))
say("G2", "(d) pointer seeds (plain reg <- imm into the block)   %d" % len(seeds))
for a, v, t in seeds:
    say("G2", "    0x%x -> %#x %s" % (a, v, t))
seed_pair = [(a, v, t) for a, v, t in seeds if v in pair]
say("G2", "(d) seeds landing on slot 0's pair               %d" % len(seed_pair))
slot0_seeds = [(a, v, t) for a, v, t in seeds if v == slot0]
skip_guards = []
for a, v, t in slot0_seeds:
    reg = t.split(None, 1)[1].split(",")[0]
    body = win(a + 1, a + 40)
    cmp_a = [x for x, tt in body if tt.startswith("cmp") and tt.replace(" ", "") == "cmp%s,0x927590" % reg]
    je_t = [imm(tt) for x, tt in body if tt.startswith("je") and x > (cmp_a[0] if cmp_a else a)]
    inc_a = [x for x, tt in body if tt.startswith("add") and "0x59c" in tt]
    target_ok = bool(je_t) and bool(inc_a) and je_t[0] == inc_a[0]
    skip_guards.append((a, bool(cmp_a), target_ok))
    say("G2", "(d) slot0 seed 0x%x: cmp %s,0x927590=%s je->loop-increment=%s"
        % (a, reg, bool(cmp_a), target_ok))

# whole-block transfer: push size imm + push block base
xfer = []
for a, t in sorted(INS.items()):
    if t.startswith("push") and imm(t) == BLOCK_SIZE_IMM:
        push_a = [x for x, tt in win(a - 6, a + 6) if tt.startswith("push") and imm(tt) == slot0]
        xfer.append((a, t, bool(push_a)))
say("G2", "whole-block transfers   %d" % len(xfer))
for a, t, ok in xfer:
    say("G2", "    0x%x %s  block-base push nearby=%s" % (a, t, ok))

check("G2 store population", len(stores) == 64494)
check("G2 (a) agenda-window stores are the 3 ctor stores", [a for a, _ in set_a] == [0x5bee99, 0x5bf5cd, 0x5c6173])
check("G2 (a) none of them sits in a record context", set_a_rec == [])
check("G2 (b) block stores are the 2 rec+0 stores", [a for a, _ in set_b] == [0x4dd996, 0x57efe4])
check("G2 (b) none lands in the agenda window", set_b_pair == [])
check("G2 (c) folded form has no store", set_c_st == [] and len(set_c_all) == 33)
check("G2 window is the 5-dword agenda block", list(AGENDA_WINDOW) == [0x584, 0x588, 0x58c, 0x590, 0x594])
check("G2 (d) no pointer seed on slot 0's pair", seed_pair == [])
check("G2 (d) the only slot0 seed is skip-guarded", slot0_seeds == [(0x579e9c, slot0, "mov    esi,0x927590")]
      and all(c and j for _, c, j in skip_guards))
check("G2 whole-block movers: 4 pushes of one block size", len(xfer) == 4 and all(imm(t) == BLOCK_SIZE_IMM for _, t, _ in xfer))
check("G2 two of them name the block, two a stack twin", sum(1 for _, _, ok in xfer if ok) == 2)

# ---------------------------------------------------------------- G3 the SE path
COMMIT = 0x4b2570
grid_store, grid_imul = 0x4b2715, (0x4b26ba, 0x4b26ff)
say("G3", "SE commit store @0x4b2715 %s" % ins(grid_store))
say("G3", "grid index imul @0x4b26ba/%#x  %s | %s" % (grid_imul[1], ins(grid_imul[0]), ins(grid_imul[1])))
say("G3", "pending source  @0x4b270e %s" % ins(0x4b270e))
src_off = disp(ins(0x4b270e))
src_ok = (ins(0x4b270e) == "mov    edx,DWORD PTR [esi+edx*4+0xcf8]")
grid_base = disp(ins(grid_store))
grid_stride = imm(ins(grid_imul[0]))
say("G3", "grid base / stride      %#x / %#x (%d)" % (grid_base, grid_stride, grid_stride))

commit_body = [(a, t) for a, t in win(COMMIT, COMMIT + 0x2a0) if is_store(t)]
say("G3", "commit body stores      %d" % len(commit_body))
cgrid, cblock = 0, 0
for a, t in commit_body:
    d = disp(t)
    if d == grid_base:            # the grid dword itself: base + category*4
        cgrid += 1
    if d == grid_base + 0x20:     # the same 0x20bc block's running counter
        cgrid += 0
    if d is not None and slot0 <= d < block_end:
        cblock += 1
for a, t in commit_body:
    say("G3", "    0x%x %s" % (a, t))
cgrid_field = [a for a, t in commit_body if disp(t) == grid_base + 0x20]
say("G3", "commit: 1 dword at 0x94d658+cat*4, %d at +0x20 (0x94d678), %d into the agenda block"
    % (len(cgrid_field), cblock))

callers = [a for a, t in sorted(INS.items()) if t.startswith("call") and imm(t) == COMMIT]
say("G3", "callers of the commit   %d" % len(callers))
for a in callers:
    say("G3", "    0x%x  in FUN_%06x   %s" % (a, owner(a), ins(a)))

# agenda-vs-grid comparisons: the record pair is READ against the grid
cmp_sites = [a for a, t in sorted(INS.items())
             if disp(t) in (grid_base,) and ("cmp" in t or t.startswith("mov"))]
say("G3", "grid access sites       %d" % len(cmp_sites))

check("G3 commit store base is the grid", grid_base == 0x94d658)
check("G3 grid stride", grid_stride == 0x20bc)
check("G3 commit writes the grid", cgrid >= 1)
check("G3 commit never writes the block", cblock == 0)
check("G3 dialog handlers call the commit", sorted({owner(a) for a in callers}) == [0x4b5530, 0x4b55d0] and len(callers) == 4)
check("G3 source operand is +0xcf8+cat*4", src_ok and src_off == 0xcf8)

# ---------------------------------------------------------------- G4 sentinel law
idiv_a, inc_a = 0x5a119d, 0x5a11a6
say("G4", "choice modulus @0x5a119d %s" % ins(idiv_a))
say("G4", "choice +1      @0x5a11a6 %s" % ins(inc_a))
modulus = imm(ins(idiv_a))
say("G4", "modulus / offset        %d / +1 -> choices 1..%d" % (modulus, modulus))

guards = []
for a, t in sorted(INS.items()):
    if t.startswith("mov") and disp(t) == 0x927b1c:
        nxt = [tt for x, tt in win(a + 1, a + 12)][:3]
        guards.append((a, t, nxt))
say("G4", "loads of +0x58c followed by a 0-test   %d" % len(guards))
for a, t, nxt in guards:
    say("G4", "    0x%x %-34s -> %s" % (a, t, " | ".join(nxt)))
guarded = [g for g in guards if any(x.startswith(("test", "cmp")) for x in g[2])]

check("G4 choice modulus is 3", modulus == 3)
check("G4 choice is b+1 (never 0)", ins(inc_a).startswith("inc"))
check("G4 every +0x58c load is 0-tested", len(guarded) == 5 and [g[0] for g in guarded] == [0x4a66c1, 0x531fcc, 0x546914, 0x555dc6, 0x5a1e74])
check("G4 9 loads, 4 not tested: 3 name-pushed + 1 compared to +0x590",
      len(guards) == 9 and [g[0] for g in guards if g not in guarded] == [0x522e78, 0x54bc03, 0x54de26, 0x54de93]
      and all("call   0x4237f0" in " ".join(g[2]) for g in guards if g[0] in (0x54bc03, 0x54de26, 0x54de93))
      and any("0x927b20" in x for x in [g for g in guards if g[0] == 0x522e78][0][2]))
check("G4 slot0 choice is not in the write set", pair[1] not in writes)

# ---------------------------------------------------------------- G5 rivals
r1 = len(set_a_rec) > 0            # "the human's SE choices write slot 0" needs a writer
say("RIVAL1", "a writer of slot 0 exists                                  -> %s (must FAIL)"
    % ("PASS" if r1 else "FAIL"))
r2 = nrec == 8
say("RIVAL2", "the randomizer covers all 8 records                        -> %s (must FAIL)"
    % ("PASS" if r2 else "FAIL"))
r3 = cblock > 0
say("RIVAL3", "the SE commit writes the agenda pair in the same pass      -> %s (must FAIL)"
    % ("PASS" if r3 else "FAIL"))
r4 = pair[1] in writes
say("RIVAL4", "slot 0's CHOICE address is inside the write set            -> %s (must FAIL)"
    % ("PASS" if r4 else "FAIL"))
check("G5 RIVAL1 fails (no writer)", not r1)
check("G5 RIVAL2 fails (7 not 8)", not r2)
check("G5 RIVAL3 fails (commit does not touch the block)", not r3)
check("G5 RIVAL4 fails (slot0 choice not written)", not r4)

# ---------------------------------------------------------------- verdict
bad = [n for n, ok in checks if not ok]
print()
for n, ok in checks:
    if not ok:
        print("FAIL %s" % n)
digest = hashlib.sha1("\n".join(table).encode()).hexdigest()[:16]
print("PASS M388: %d/%d  %s" % (len(checks) - len(bad), len(checks), digest))
sys.exit(1 if bad else 0)
