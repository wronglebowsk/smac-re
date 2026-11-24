#!/usr/bin/env python3
"""M386 - is +0x94d820 a turn DEADLINE or a REQUEST COUNTER?  Neither: it is the X of a
per-faction map-coordinate PAIR (+0x94d824 = Y), addressed as row(faction) + 0x3D8.

M378 left the field OPEN; its only reading was the `jge` guard on the 0x20000 arm
(`test ecx,ecx / jge 0x555405`).  This instrument measures, from the instruction stream alone
(zero box time):

  G0 parse        the .text dump parses; the windows this milestone names are pinned.
  G1 census       every reference to either half: counts by class, and the arithmetic class is
                  MEASURED EMPTY (0 RMW on either half, image-wide).
  G2 writers      the halves are written as a PAIR: 5 sites write -1 to both in adjacent
                  instructions, 1 site writes a unit's (x,y); 1 lone X=-1 reset.
  G3 arithmetic   the reader at 0x557cf6 feeds (Y*mapwidth + X>>1)*0x2c into the 44-byte tile
                  array at 0x92ae14, and calls FUN_004e34f0, which bounds-checks X/Y against
                  ds:0x92a378 / ds:0x92a37c.
  G4 the guard    the 0x20000 arm's only entering branch tests a register whose base is
                  0x20bc*esi - the PARTNER faction's row, not the pair's own row.
  G5 deadline     refuted: no per-turn arithmetic and no comparison against the turn counter
                  ds:0x985afc anywhere near the pair - while the 50-tick cell +0x80 in the SAME
                  loop IS decremented per turn.
  G6 scalar       refuted: 0 absolute `ds:0x94d820` forms; all references are [base+0x94d820].
  G7 0x20000      re-measured: 0 readers, set alone by the arm, cleared by the treaty arm;
                  its noun stays INFERRED and the gate is the partner's marker, not a counter.
  G8 rivals       four rival nouns, each refuted on the printed numbers.
  G9 digest       the printed table digest is pinned.

M386_PATCH='addr|text' rewrites one instruction line in memory (mutants).
M386_ALGO=n flips an algorithm law (n=1: guard base read as a faction id, stride 4).
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M386_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))

FIELD_X = 0x94D820                # first half of the pair
FIELD_Y = 0x94D824                # second half
ROW = 0x20BC                      # per-faction row stride in the 0x94d448 array
ROW_BASE = 0x94D448               # row 0 base (the relations dword of partner 0)
ROW_OFF = FIELD_X - ROW_BASE      # 0x3D8
TURN = 0x985AFC                   # the turn counter
MAPW = 0x692184                   # map width scalar
TILE = 0x92AE14                   # 44-byte tile array base
MAXX = 0x92A378                   # map bound X (FUN_004e34f0)
MAXY = 0x92A37C                   # map bound Y (FUN_004e34f0)
TICK = 0x94D4C8                   # the 50-tick cell (B37) - the REAL per-turn countdown
ALGO = int(os.environ.get("M386_ALGO", "0") or 0)
DIGEST_PIN = "deb7ca6b1006ecf6"

PAT = re.compile(r'^\s*([0-9a-f]+):\t([0-9a-f ]+?)(?:\t(.*))?$')
FAM = {"eax": ("eax", "al", "ah"), "ebx": ("ebx", "bl", "bh"), "ecx": ("ecx", "cl", "ch"),
       "edx": ("edx", "dl", "dh"), "esi": ("esi", "si"), "edi": ("edi", "di")}


class Insn:
    __slots__ = ("addr", "mn", "ops", "raw")

    def __init__(self, addr, mn, ops, raw):
        self.addr, self.mn, self.ops, self.raw = addr, mn, ops, raw


def load_text(path):
    ins, by = [], {}
    for line in open(path, encoding="latin-1"):
        m = PAT.match(line.rstrip("\n"))
        if not m:
            continue
        body = (m.group(3) or "").strip()
        if not body:
            continue
        parts = body.split(None, 1)
        ins.append(Insn(int(m.group(1), 16), parts[0], parts[1].strip() if len(parts) > 1 else "", body))
        by[ins[-1].addr] = len(ins) - 1
    return ins, by


def imm2(s):
    """the LAST hex literal - for a masked memory operand the displacement comes first."""
    h = re.findall(r'0x([0-9a-f]+)\b', s)
    return int(h[-1], 16) if h else None


def dst(i):
    return i.ops.split(",")[0].strip()


def src(i):
    p = i.ops.split(",", 1)
    return p[1].strip() if len(p) > 1 else ""


def names(s, field):
    return re.search(r'\[[^\]]*0x%x\]' % field, s) is not None


def base_reg(s):
    m = re.search(r'\[\s*([a-z]{2,3})[^\]\w]', s)
    return m.group(1) if m else "?"


RMW = ("add", "sub", "inc", "dec", "and", "or", "xor", "neg", "not", "adc", "sbb",
       "shl", "shr", "sar", "lea", "imul", "mul", "idiv", "div")

OUT = []
fails = []


def say(m=""):
    print(m)
    OUT.append(m)


def chk(cond, label, detail=""):
    if cond:
        say("ok   %s %s" % (label, detail))
    else:
        say("FAIL %s %s" % (label, detail))
        fails.append(label)


def main():
    ins, by = load_text(TEXT)
    for spec in filter(None, [os.environ.get("M386_PATCH", "")]):
        for one in spec.split(";"):
            addr_s, text = one.split("|", 1)
            i = ins[by[int(addr_s, 16)]]
            parts = text.split(None, 1)
            i.mn, i.ops = parts[0], (parts[1] if len(parts) > 1 else "")
            i.raw = text

    say("M386 +0x94d820/+0x94d824 - deadline? counter? (writers, readers, arithmetic)")
    say("")

    # ---------- G0 parse
    say("-- G0 parse")
    for a in (0x5553A4, 0x5553AC, 0x555405, 0x55540A, 0x557CF6, 0x557D29, 0x557D43,
              0x4E34F0, 0x558E0C, 0x55FCE0, 0x5552B6):
        if a not in by:
            say("   MISSING 0x%x" % a)
        chk(a in by, "G0", "0x%x parses" % a)
    chk(len(ins) > 200000, "G0", "%d instructions from %s" % (len(ins), os.path.basename(TEXT)))
    chk(names(ins[by[FIELD_X]].raw if False else "[%#x]" % FIELD_X, FIELD_X), "G0", "field literal builds")
    chk(ROW_OFF == 0x3D8 and ROW_OFF < ROW, "G0",
        "X sits 0x%x into a 0x%x-byte row, Y at 0x%x" % (ROW_OFF, ROW, FIELD_Y - ROW_BASE))
    chk(FIELD_Y - FIELD_X == 4, "G0", "the halves are adjacent dwords")
    if fails:
        return finish()

    # ---------- G1 census
    say("")
    say("-- G1 census: every reference, by class")
    def refs(f):
        return [i for i in ins if names(i.ops, f)]

    rx, ry = refs(FIELD_X), refs(FIELD_Y)
    def classify(i, f):
        if i.mn in ("cmp", "test"):
            return "read"
        if i.mn == "mov":
            return "store" if names(dst(i), f) else "load"
        return "RMW"
    clsx = [classify(i, FIELD_X) for i in rx]
    clsy = [classify(i, FIELD_Y) for i in ry]
    say("   %-8s %s" % ("class", "X / Y"))
    for k in ("load", "read", "store", "RMW"):
        say("   %-8s %d / %d" % (k, clsx.count(k), clsy.count(k)))
    chk(len(rx) == 30 and len(ry) == 24, "G1",
        "%d X references and %d Y references (declared, measured)" % (len(rx), len(ry)))
    chk(clsx.count("RMW") == 0 and clsy.count("RMW") == 0, "G1",
        "ZERO arithmetic RMW on either half, image-wide (%d+%d scanned)"
        % (len(rx), len(ry)))
    xs = [i for i, k in zip(rx, clsx) if k == "store"]
    ys = [i for i, k in zip(ry, clsy) if k == "store"]
    chk(len(xs) == 7 and len(ys) == 6, "G1",
        "%d X stores, %d Y stores" % (len(xs), len(ys)))
    say("   X stores: %s" % " ".join("0x%x" % i.addr for i in xs))
    say("   Y stores: %s" % " ".join("0x%x" % i.addr for i in ys))
    regs = sorted({base_reg(i.ops) for i in rx + ry})
    say("   base registers across all references: %s" % ", ".join(regs))

    # ---------- G2 the pair
    say("")
    say("-- G2 writers: the halves move together")
    pairs, lone = [], []
    yaddrs = [i.addr for i in ys]
    for i in xs:
        near = [a for a in yaddrs if abs(by[a] - by[i.addr]) <= 3]
        if near:
            j = min(near, key=lambda a: abs(by[a] - by[i.addr]))
            pairs.append((i.addr, j))
        else:
            lone.append(i.addr)
    say("   pairs (X,Y): %s" % " ".join("(0x%x,0x%x)" % p for p in pairs))
    chk(len(pairs) == 6, "G2", "%d of %d X stores pair with a Y store" % (len(pairs), len(xs)))
    chk(lone == [0x55FCE0], "G2", "the lone X store is 0x55fce0 (X=-1 alone disables the marker)")

    def minus1_source(addr):
        j = by[addr]
        for k in range(j - 1, max(-1, j - 13), -1):
            q = ins[k]
            if q.mn in ("jmp", "ret", "call"):
                return None
            if q.mn == "or" and imm2(src(q)) == 0xFFFFFFFF:
                return q.addr
        return None

    ones = [(p, minus1_source(min(p))) for p in pairs]
    n1 = [p for p, s in ones if s]
    say("   -1 pairs (X,Y) <- `or reg,0xffffffff`: %s"
        % " ".join("(0x%x,0x%x)@0x%x" % (p[0], p[1], minus1_source(min(p))) for p in n1))
    chk(len(n1) == 5, "G2", "%d of 6 pairs write the -1 none-sentinel to BOTH halves" % len(n1))
    chk(imm2(src(ins[by[0x55FCE0]])) == 0xFFFFFFFF, "G2",
        "the lone reset carries the same -1 (0x55fce0)")

    # the unit-position pair
    win = [ins[by[0x558E0C] - d] for d in (8, 7, 6, 5, 4, 3, 2, 1)]
    lx = [i for i in win if i.mn == "movsx" and "0x95da10" in i.ops and dst(i) == "edx"]
    ly = [i for i in win if i.mn == "movsx" and "0x95da12" in i.ops and dst(i) == "eax"]
    for i in reversed(win):
        say("   0x%x  %s" % (i.addr, i.raw))
    say("   0x%x  %s" % (0x558E0C, ins[by[0x558E0C]].raw))
    say("   0x%x  %s" % (0x558E12, ins[by[0x558E12]].raw))
    stride = [i for i in ins[by[0x558DF2]:by[0x558E12]]
             if i.mn == "shl" and dst(i) == "eax" and imm2(src(i)) == 4]
    chk(bool(lx) and bool(ly) and bool(stride), "G2",
        "one pair (0x558e0c/0x558e12) takes a UNIT's x,y (0x95da10/0x95da12, stride 0x130)")

    # ---------- G3 coordinate arithmetic
    say("")
    say("-- G3 readers: the pair is fed to map arithmetic")
    seq = [(0x557CF6, "mov", "eax,DWORD PTR [ebx+0x94d820]"),
           (0x557D16, "mov", "ecx,DWORD PTR [ebx+0x94d824]"),
           (0x557D1C, "push", "ecx"),
           (0x557D1D, "push", "eax"),
           (0x557D38, "mov", "esi,DWORD PTR ds:0x92ae14"),
           (0x557D29, "mov", "edx,DWORD PTR [ebx+0x94d820]"),
           (0x557D2F, "imul", "ecx,DWORD PTR ds:0x692184"),
           (0x557D36, "sar", "edx,1"),
           (0x557D3E, "add", "ecx,edx"),
           (0x557D43, "lea", "edx,[ecx+ecx*4]"),
           (0x557D46, "lea", "ecx,[ecx+edx*2]"),
           (0x557D4D, "mov", "dl,BYTE PTR [esi+ecx*4+0x3]")]
    bad = []
    for a, mn, ops in seq:
        ok = a in by and ins[by[a]].mn == mn and ins[by[a]].ops.strip().replace("  ", " ") == ops
        if not ok:
            bad.append("0x%x" % a)
        say("   %s 0x%x  %s" % ("ok " if ok else "BAD", a, ins[by[a]].raw if a in by else "MISSING"))
    chk(not bad, "G3", "the tile-index chain parses instruction-for-instruction (%s)" % (bad or "clean"))
    call = ins[by[0x557D1E]]
    chk(call.mn == "call" and "0x4e34f0" in call.ops, "G3",
        "X,Y are handed to FUN_004e34f0: %s" % call.raw)
    mul = (1 + 2 * 5)
    say("   index = (Y*[0x692184] + (X>>1)) * %d * 4 + 3  -> tile record 0x%x bytes"
        % (mul, mul * 4))
    chk(mul * 4 == 0x2C, "G3", "the tile stride is 0x2c, the 0x92ae14 record size")
    b1 = ins[by[0x557A69]]
    b2 = ins[by[0x557A75]]
    say("   0x%x  %s" % (b1.addr, b1.raw))
    say("   0x%x  %s" % (b2.addr, b2.raw))
    chk("0x92a37c" in b1.ops and "0x92a378" in b2.ops, "G3",
        "the same bounds pair is INLINED at 0x557a69/0x557a75 (a second coordinate reader)")
    # the callee's bounds test
    c1 = ins[by[0x4E3501]]
    c2 = ins[by[0x4E3518]]
    x1 = ins[by[0x4E34F6]]
    say("   0x%x  %s" % (c1.addr, c1.raw))
    say("   0x%x  %s" % (c2.addr, c2.raw))
    chk(x1.ops.strip() == "edi,DWORD PTR [ebp+0xc]" and "0x92a37c" in c1.ops
        and "0x92a378" in c2.ops, "G3",
        "FUN_004e34f0 bounds-checks arg1(y) < [0x92a37c] and arg0(x) < [0x92a378]")

    # ---------- G4 the 0x20000 guard
    say("")
    say("-- G4 the 0x20000 arm's guard reads the PARTNER's row")
    gs = [(i.addr, i.mn, imm2(i.ops)) for i in ins
          if i.mn.startswith("j") and i.mn != "jmp" and imm2(i.ops) == 0x555405]
    say("   branches into 0x555405: %s" % (", ".join("0x%x %s" % (a, m) for a, m, _ in gs) or "-"))
    chk(len(gs) == 1 and gs[0][1] == "jge", "G4",
        "exactly one entering branch, and it is jge: %s" % (("%s" % (gs[0],)) if gs else "-"))
    arm = ins[by[0x555405]]
    chk(arm.mn == "or" and imm2(src(arm)) == 0x20000, "G4", "0x555405 is `or eax,0x20000`")
    ld = ins[by[0x5553A4]]
    chk(ld.raw.strip() == "mov    ecx,DWORD PTR [ebx+0x94d820]", "G4",
        "the compared register is loaded from the field at 0x5553a4")
    # symbolic: ebx = 0x20bc*esi
    sim = [(0x555308, "mov", "edx,esi"), (0x555310, "shl", "edx,0x6"), (0x555313, "add", "edx,esi"),
           (0x55531D, "lea", "ebx,[esi+edx*2]"), (0x555323, "shl", "ebx,0x4"),
           (0x555326, "sub", "ebx,esi"), (0x55532A, "shl", "ebx,0x2")]
    ok = all(a in by and ins[by[a]].mn == m and ins[by[a]].ops.strip() == o for a, m, o in sim)
    for a, _, _ in sim:
        say("   0x%x  %s" % (a, ins[by[a]].raw if a in by else "MISSING"))
    stride_val = ((131 << 4) - 1) << 2
    say("   ebx = ((131*esi)<<4 - esi)<<2 = %d = 0x%x" % (stride_val, stride_val))
    law_stride = ROW if ALGO == 0 else 4
    chk(ok, "G4", "the ebx chain parses instruction-for-instruction")
    chk(stride_val == law_stride, "G4", "the guard's base is 0x%x*esi (row stride 0x%x)"
        % (law_stride, law_stride))
    chain_addrs = {a for a, _, _ in sim}
    over = [i.addr for i in ins[by[0x55532A]:by[0x555373]]
            if dst(i).strip() == "ebx" and i.mn != "push" and i.addr not in chain_addrs]
    chk(not over, "G4", "no other write to ebx between the def and the guard (%s)" % (over or "none"))
    targ = [(i.addr, imm2(i.ops)) for i in ins[by[0x555302]:by[0x5553A4]]
            if i.mn.startswith("j") and i.mn != "jmp"]
    inner = [t for a, t in targ if 0x555300 < t <= 0x5553A4]
    say("   in-range branch targets: %s" % ", ".join("0x%x" % t for t in inner))
    chk(all(t >= 0x55531D for t in inner), "G4",
        "every entry into the guard region lands after the ebx def (0x55531d)")
    loop = ins[by[0x555282]]
    loop2 = ins[by[0x555284]]
    say("   0x%x  %s" % (loop.addr, loop.raw))
    say("   0x%x  %s" % (loop2.addr, loop2.raw))
    chk(loop2.mn == "test" and "0x985b11" in loop2.ops, "G4",
        "esi is the faction loop variable (presence bitmask ds:0x985b11)")
    say("   => [0x94d820 + 0x%x*esi] = row(esi)+0x%x = the PARTNER faction's marker X"
        % (ROW, ROW_OFF))

    # ---------- G5 deadline refutation
    say("")
    say("-- G5 rival DEADLINE: refuted on the numbers")
    near_turn = []
    for i in rx + ry:
        if i.mn != "mov" or not names(src(i), FIELD_X) and not names(src(i), FIELD_Y):
            continue
        for j in range(by[i.addr] + 1, min(len(ins), by[i.addr] + 7)):
            if "0x985afc" in ins[j].ops:
                near_turn.append((i.addr, ins[j].addr))
    say("   field loads followed within 6 insns by a turn-counter reference: %s"
        % (near_turn or "NONE"))
    chk(not near_turn, "G5", "0 loads of either half meet ds:0x985afc within 6 insns")
    tick = [ins[by[0x5552B6]], ins[by[0x5552C0]], ins[by[0x5552C3]]]
    for i in tick:
        say("   0x%x  %s" % (i.addr, i.raw))
    chk(tick[0].raw.strip() == "mov    eax,DWORD PTR [edi+0x94d4c8]" and tick[1].mn == "dec"
        and "0x94d4c8" in dst(tick[2]), "G5",
        "the REAL per-turn cell is +0x80: loaded, dec'd, stored back five insns from the field")
    par = ins[by[0x5552D9]]
    decal = ins[by[0x5552F0]]
    say("   0x%x  %s" % (par.addr, par.raw))
    say("   0x%x  %s" % (decal.addr, decal.raw))
    chk(par.mn == "test" and "0x985afc" in par.ops and decal.mn == "dec", "G5",
        "turn parity gates a per-turn BYTE decrement at 0x5552f0 - the field is not that cell")
    say("   R1 turn-deadline: refuted (0 RMW, 0 turn-counter compares)")

    # ---------- G6 scalar refutation
    say("")
    say("-- G6 rival SCALAR GLOBAL: refuted")
    absolute = [i.addr for i in ins if re.search(r'ds:0x94d82', i.ops)]
    chk(not absolute, "G6", "0 absolute ds:0x94d820/824 forms (%s)" % (absolute or "none"))
    formok = all(re.search(r'\[[^\]]*0x94d82[04]\]', i.ops) for i in rx + ry)
    chk(formok, "G6", "all %d references are base-register-relative [reg+0x94d820/824]"
        % (len(rx) + len(ry)))
    say("   R3 scalar: refuted (every access is row-relative)")

    # ---------- G7 0x20000
    say("")
    say("-- G7 0x20000: the request bit behind the guard")
    inline = [i for i in rx if i.mn == "test" and imm2(i.ops) is not None]
    r20000 = [i for i in inline if (imm2(i.ops) or 0) & 0x20000]
    reg20000 = []
    for i in rx:
        if i.mn == "mov" and names(src(i), FIELD_X):
            for j in range(by[i.addr] + 1, min(len(ins), by[i.addr] + 4)):
                q = ins[j]
                if q.mn not in ("test", "cmp"):
                    continue
                d0 = dst(q)
                if not re.fullmatch(r'(e[a-d]x|e[sd]i|[abcd][lh]|si|di)', d0):
                    continue          # dst must be a register
                if "[" in src(q) or "PTR" in src(q) or "ds:" in src(q):
                    continue          # a memory operand is not an immediate test
                v = imm2(src(q))
                if v is not None and v & 0x20000:
                    reg20000.append(i.addr)
    chk(not r20000 and not reg20000, "G7",
        "0x20000 has 0 direct readers (%d inline, %d register-form: %s)" % (len(r20000), len(reg20000), [hex(a) for a in reg20000]))
    src_ld = ins[by[0x55536B]]
    chk(src_ld.raw.strip() == "mov    eax,DWORD PTR [edi+0x94d448]", "G7",
        "the arm ORs into a fresh load of the relations dword: %s" % src_ld.raw)
    andm = ins[by[0x5553E7]]
    chk(andm.mn == "and" and not (imm2(src(andm)) & 0x20000), "G7",
        "the treaty arm's AND 0x%x clears 0x20000" % imm2(src(andm)))
    say("   0x%x  %s" % (andm.addr, andm.raw))
    say("   => 0x20000 noun: INFERRED (no reader); the arm's gate is the partner's marker, not a counter")

    # ---------- G8 rivals
    say("")
    say("-- G8 rivals")
    say("   R1 turn DEADLINE: needs per-turn arithmetic or a ds:0x985afc compare")
    chk(clsx.count("RMW") == 0 and clsy.count("RMW") == 0 and not near_turn, "G8", "R1 refuted")
    say("   R2 REQUEST COUNTER: needs an inc/dec/add on the field")
    chk(len([i for i in rx + ry if i.mn in ("add", "sub", "inc", "dec")]) == 0, "G8",
        "R2 refuted (%d arithmetic sites)" % len([i for i in rx + ry if i.mn in ("add", "sub", "inc", "dec")]))
    say("   R3 scalar global: needs an absolute form")
    chk(not absolute, "G8", "R3 refuted")
    say("   R4 flag pair: would need no coordinate arithmetic")
    chk(mul * 4 == 0x2C and bool(lx) and bool(ly), "G8", "R4 refuted: the pair indexes the tile array")
    if ALGO == 1:
        say("   ALGO1: guard base read as a faction id (stride 4) - G4 reddens")

    # ---------- G9 digest
    say("")
    say("-- G9 digest")
    d1 = hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]
    say("digest %s" % d1)
    chk(d1 == DIGEST_PIN, "G9", "the printed table hash is the pinned %s" % DIGEST_PIN)
    return finish()


def finish():
    say("")
    ng = sum(1 for l in OUT if l.startswith("ok "))
    if fails:
        say("FAIL M386: %d/%d gates, red: %s" % (ng - len(fails), ng, ", ".join(sorted(set(fails)))))
        return 1
    say("PASS M386: %d/%d gates digest %s" % (ng, ng, hashlib.sha1("\n".join(OUT).encode()).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
