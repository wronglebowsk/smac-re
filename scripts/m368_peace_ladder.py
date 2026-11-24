#!/usr/bin/env python3
"""M368 (chain-1, STATIC, zero box) — the NOUNS of faction-relations bits 0x2 and 0x4.

Question: M367's label table orders the four diplomacy states (Truce/Treaty/Pact/Vendetta), but the
bit *values* run the other way — 0x4, 0x2, 0x1.  Which bit is TRUCE and which is TREATY, on
evidence that does not rest on the label table alone?

Three independent axes, each measured from bytes:

  A  LABELS    — `programs/labels.txt` elements 643/644/645 = Truce/Treaty/Pact (M367's law:
                 element = line-10; the builder pairs bit 4/2/1 with those elements).
  B  BEHAVIOUR — the site that pushes mask 0x4 to the writer FUN_00551a20 posts the .data message
                 key `ENEMYTRUCE` in the same block; the 0x2 site posts `ENEMYTREATY`.  This is the
                 discriminating axis: a swapped reading needs the two keys swapped.
  C  ALGEBRA   — FUN_00551a20 upgrades mask 0x1 to 0x1|0x2 (pact implies treaty), its set-clear mask
                 0xffee7faf includes 0x4 and excludes 0x1/0x2 (a higher state supersedes truce), and
                 FUN_005076d0's same-state classifier tests 0x1, then 0x2, then 0x4.

Gates (each prints its numbers BEFORE asserting them; every gate has a mutant in
scripts/m368_mutate.py):
  G0  parse + the anchor instructions decode byte-exact.
  G1  writer call-site census and its mask histogram.
  G2  mask -> message-key pairing at FUN_005537d0's peace sites.
  G3  the pact-implies-treaty upgrade and the global negative census for the reverse.
  G4  the clear-mask arithmetic (0x4 clears, 0x1/0x2 survive; war clears all three).
  G5  labels.txt, re-read.
  G6  FUN_005076d0's same-state classifier (precedence 1,2,4; equality, not rank).
  G7  RIVALS, each killed by a named gate.
"""
import bisect
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M368_TEXT") or os.path.join(ROOT, "scratch/m574/text.txt")
EXE = os.environ.get("M368_EXE") or os.path.join(ROOT, "programs/terran.exe")
LABELS = os.environ.get("M368_LABELS") or os.path.join(ROOT, "programs/labels.txt")
INDEX = os.environ.get("M368_INDEX") or os.path.join(ROOT, "ghidra_out/index.csv")

WRITERS = {0x5518F0: "CLR_A", 0x5519C0: "SET_A2", 0x551A20: "SET_A", 0x551C40: "CLR_B",
           0x551CF0: "CLR_B2", 0x551D70: "SET_B"}
PEACE = (0x1, 0x2, 0x4)
EXPECT_KEYS = {0x4: "ENEMYTRUCE", 0x2: "ENEMYTREATY", 0x1: None}
LABEL_ELEM = {0x4: 643, 0x2: 644, 0x1: 645}
EXPECT_LABEL = {0x4: "Truce", 0x2: "Treaty", 0x1: "Pact"}
TRIO = (0x553C41, 0x553F10, 0x554165)
PEACE_AND = 0x551A88          # `and edx,<peace-clear>` in FUN_00551a20
WAR_AND = 0x551B17            # `and edx,<war-clear>` in FUN_00551a20, inside `test bl,0x10`
POSTER = 0x483470             # the message poster FUN_005076d0 uses for VENDETTAWARNING
CLEAR_A = None                # derived: `and edx,<imm>` at PEACE_AND, decoded from its own bytes
WAR_A = None                  # derived: `and edx,<imm>` at WAR_AND
REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp")


def base_reg(r):
    """bl/al/cl/dl/si/di -> ebx/eax/... : the byte form of a register names the same record."""
    for b in REGS:
        if r == b or (len(r) == 2 and r in ("al", "ah", "bl", "bh", "cl", "ch", "dl", "dh")
                      and b[1] == r[0] and b[2] == ("x" if r[1] == "l" else "h")):
            return b
        if r in ("si", "di", "bp", "sp") and b[:2] == r:
            return b
    return r


LINE = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+?)\s*\t(.*?)(?:\t;.*)?$")
INSN, TXT, BYTES, GATES, ROWS = [], {}, {}, [], []


def gate(name, cond, msg):
    GATES.append((name, bool(cond), msg))
    print("  %-7s %s  %s" % (name, "PASS" if cond else "FAIL", msg))
    return bool(cond)


def row(fmt, *a):
    line = fmt % a if a else fmt
    ROWS.append(line)
    print("      " + line)


def load():
    for line in open(TEXT, errors="replace"):
        m = LINE.match(line)
        if not m:
            continue
        a = int(m.group(1), 16)
        INSN.append(a)
        BYTES[a] = m.group(2).replace(" ", "")
        TXT[a] = m.group(3).strip()
    INSN.sort()


def fn_starts():
    out = []
    for line in open(INDEX):
        p = line.strip().split(",")
        if len(p) < 3 or not p[0].startswith("0x"):
            continue
        try:
            out.append((int(p[0], 16), int(p[2])))
        except ValueError:
            pass
    out.sort()
    return out


STARTS = []


def fn_of(a):
    i = bisect.bisect_right(STARTS, (a, 1 << 30)) - 1
    if i < 0:
        return None
    s, n = STARTS[i]
    return s if a < s + n else None


def imm(t):
    m = re.search(r"0x([0-9a-f]+)$", t)
    return int(m.group(1), 16) if m else None


def at(a):
    return TXT.get(a, "")


def around(a, k):
    i = bisect.bisect_left(INSN, a)
    return INSN[i + k] if 0 <= i + k < len(INSN) else None


def pushes_before(a, n=16):
    i = bisect.bisect_left(INSN, a)
    out = []
    for k in range(max(0, i - n), i):
        t = TXT[INSN[k]]
        if t.startswith("push") and imm(t) is not None:
            out.append((INSN[k], imm(t)))
    return out


def prev_call(a, maxn=12):
    """(addr, target) of the nearest call before a, and (None, None) if there is none."""
    for k in range(1, maxn):
        b = around(a, -k)
        if b is None:
            break
        m = re.match(r"call\s+0x([0-9a-f]+)$", at(b))
        if m:
            return b, int(m.group(1), 16)
    return None, None


def mask_of(a):
    """The mask arg of a 3-arg cdecl call, or None when the push shape is not (imm, reg, reg)."""
    p1, p2, p3 = around(a, -1), around(a, -2), around(a, -3)
    if p1 is None or p2 is None or p3 is None:
        return None
    if not (at(p1).startswith("push   e") and at(p2).startswith("push   e")):
        return None
    t = at(p3)
    return imm(t) if t.startswith("push   0x") else None


def call_sites():
    out = []
    for a in INSN:
        m = re.match(r"call\s+0x([0-9a-f]+)$", TXT[a])
        if m and int(m.group(1), 16) in WRITERS:
            out.append((a, int(m.group(1), 16)))
    return out


def img_dims():
    """[(name, va, vsize, raw_ptr, raw_size)] from the PE section table — never assume va-0x400000."""
    d = open(EXE, "rb").read()
    pe = int.from_bytes(d[0x3C:0x40], "little")
    nsec = int.from_bytes(d[pe + 6:pe + 8], "little")
    opt = int.from_bytes(d[pe + 20:pe + 22], "little")
    base = pe + 24 + opt
    out = []
    for i in range(nsec):
        b = base + i * 40
        name = d[b:b + 8].rstrip(b"\0").decode("latin-1")
        vs, va, rs, ro = (int.from_bytes(d[b + o:b + o + 4], "little")
                          for o in (8, 12, 16, 20))
        out.append((name, va, vs, ro, rs))
    return out


SECTIONS = []


def vma_off(vma):
    rva = vma - 0x400000
    for name, va, vs, ro, rs in SECTIONS:
        if va <= rva < va + max(vs, rs):
            return ro + (rva - va)
    raise KeyError(hex(vma))


def image_string(vma):
    with open(EXE, "rb") as f:
        f.seek(vma_off(vma))
        s = f.read(64).split(b"\0")[0].decode("latin-1")
    return s


def and_imm(a):
    """Decode `and <reg>,imm32` at a straight from the dump's own bytes."""
    b = BYTES.get(a, "")
    if not b.startswith("81e2") or len(b) < 10:
        raise ValueError("0x%x is not `and reg,imm32` (bytes %r)" % (a, b))
    return int.from_bytes(bytes.fromhex(b[4:]), "little")


def bits_cleared(mask):
    return [1 << b for b in range(32) if not (mask >> b) & 1]


def main():
    load()
    global STARTS
    STARTS = fn_starts()
    SECTIONS[:] = img_dims()
    print("M368 — nouns of the faction-relations bits 0x2 and 0x4 (%d insns parsed)" % len(INSN))
    row("PE sections: %s", " ".join("%s va=0x%x raw=0x%x" % (n, va, ro) for n, va, vs, ro, rs in SECTIONS))

    # ---------------- G0 ----------------
    print("\nG0 anchor instructions")
    row("0x551ab7 %-16s | 0x551abc %-14s | bytes %s", at(0x551AB7), at(0x551ABC),
        BYTES.get(0x551ABC))
    row("0x551a88 %-26s bytes %s", at(0x551A88), BYTES.get(0x551A88))
    for s in TRIO:
        row("%s %-12s | %s | %s", hex(around(s, -3)), at(around(s, -3)), at(around(s, -2)),
            at(around(s, -1)))
    ok0 = gate("G0a", BYTES.get(0x551ABC) == "83cb02" and at(0x551AB7) == "test   bl,0x1",
               "0x551abc is 83 cb 02 = `or ebx,0x2`, entered on `test bl,0x1`")
    ok0 &= gate("G0b", re.match(r"and\s+edx,0xffee7faf$", at(0x551A88)) is not None,
                "0x551a88 is `%s`" % at(0x551A88))
    ok0 &= gate("G0c", all(at(around(s, -3)) in ("push   0x1", "push   0x2", "push   0x4") and
                           at(around(s, -1)).startswith("push   e") for s in TRIO),
                "each of the three peace sites pushes (mask, reg, reg) in cdecl order")

    # ---------------- G1 ----------------
    print("\nG1 writer call-site census")
    sites = [(a, t, mask_of(a)) for a, t in call_sites()]
    hist = {}
    for a, t, m in sites:
        if m is not None:
            hist[(t, m)] = hist.get((t, m), 0) + 1
    row("call sites %d across %d writer fns; call sites with a literal mask %d",
        len(sites), len(WRITERS), sum(hist.values()))
    for (t, m), n in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[:8]:
        row("%-7s mask %-6s x%d", WRITERS[t], hex(m), n)
    peace = [(a, t, m) for a, t, m in sites if m in PEACE]
    row("bare peace-mask sites %d: %s", len(peace),
        " ".join("%s(%s)" % (hex(a), hex(m)) for a, t, m in peace))
    fns = sorted({fn_of(a) for a, t, m in peace})
    row("their hosts: %s", " ".join(hex(f) for f in fns))
    ok1 = gate("G1a", len(sites) == 169, "169 call sites reach the six relation writers")
    ok1 &= gate("G1b", {m for a, t, m in peace} == {1, 2, 4},
                "the bare peace masks that reach a writer are exactly {1,2,4}")
    ok1 &= gate("G1c", 0x5537D0 in fns and all(fn_of(a) == 0x5537D0 for a in TRIO),
                "FUN_005537d0 hosts a 0x4 site and a 0x2 site")
    ok1 &= gate("G1d", len(peace) == 8 and fns == [0x4DADD0, 0x523B20, 0x53F9F0, 0x5537D0],
                "exactly 8 bare-peace sites over exactly those 4 hosts")

    # ---------------- G2 ----------------
    print("\nG2 mask vs the message key posted in the same block")
    g2 = True
    for a, t, m in peace:
        key = None
        kv = None
        pc, pct = prev_call(a)
        ppc, _ = prev_call(pc) if pc is not None else (None, None)
        for pa, v in reversed(pushes_before(a, 20)):
            if 0x68F000 <= v < 0x692000 and pc is not None and ppc is not None and ppc < pa < pc:
                kv, key = v, image_string(v)
                break
        row("%s mask %s key %s -> %-12s host %s  prev-call %s",
            hex(a), hex(m), "None" if kv is None else hex(kv), key, hex(fn_of(a)),
            "none" if pc is None else hex(pct))
        if a in TRIO:
            g2 &= gate("G2-%x" % a, key == EXPECT_KEYS[m],
                       "trio site mask 0x%x carries `%s` (expected `%s`)"
                       % (m, key, EXPECT_KEYS[m]))
            if m in (2, 4):
                g2 &= gate("G2b-%x" % a, pct == POSTER and kv is not None,
                           "the key is an argument of the POSTER call 0x483470 that precedes the writer")
    keys = {}
    for a, t, m in peace:
        if a in TRIO:
            pc, pct = prev_call(a)
            ppc, _ = prev_call(pc) if pc is not None else (None, None)
            keys[m] = [image_string(v) for pa, v in pushes_before(a, 20)
                       if 0x68F000 <= v < 0x692000 and pc is not None and ppc is not None
                       and ppc < pa < pc]
    row("trio keys: 0x4 -> %s ; 0x2 -> %s", keys.get(4), keys.get(2))
    g2 &= gate("G2x", keys.get(4) and keys.get(2) and keys[4][-1] != keys[2][-1],
               "the 0x4 and 0x2 sites post DIFFERENT .data keys (a swap would redden G2-*)")

    # ---------------- G3 ----------------
    print("\nG3 implication 0x1 -> 0x2, and the reverse census")
    up = rev = 0
    for a in INSN:
        m = re.match(r"test\s+(\w+),0x([0-9a-f]+)$", TXT[a])
        if not m:
            continue
        reg, v = m.group(1), int(m.group(2), 16)
        if v not in (1, 2):
            continue
        want = 2 if v == 1 else 1
        for k in range(1, 5):
            b = around(a, k)
            if b is None:
                break
            m2 = re.match(r"or\s+(\w+),0x([0-9a-f]+)$", at(b))
            if m2 and base_reg(m2.group(1)) == base_reg(reg) and int(m2.group(2), 16) == want:
                if v == 1:
                    up += 1
                else:
                    rev += 1
                break
    row("`test r,0x1 -> or r,0x2`: %d site(s); `test r,0x2 -> or r,0x1`: %d site(s)", up, rev)
    ok3 = gate("G3a", up == 1 and rev == 0, "the pact->treaty upgrade exists once; the reverse never")
    ok3 &= gate("G3b", fn_of(0x551ABC) == 0x551A20,
                "that upgrade sits in the writer FUN_00551a20 (host %s)" % hex(fn_of(0x551ABC)))

    # ---------------- G4 ----------------
    print("\nG4 exclusion arithmetic, decoded from the two `and` instructions")
    peace_mask = and_imm(PEACE_AND)
    war_mask = and_imm(WAR_AND)
    # the war `and` must sit inside the `test bl,0x10` branch of the same writer
    war_test = None
    for k in range(1, 40):
        a = around(WAR_AND, -k)
        if a and at(a) == "test   bl,0x10":
            war_test = a
            break
    row("0x%x bytes %s -> mask 0x%08x (peace); 0x%x bytes %s -> mask 0x%08x (war)",
        PEACE_AND, BYTES[PEACE_AND], peace_mask, WAR_AND, BYTES[WAR_AND], war_mask)
    row("the war mask's branch head: %s = %s", "-" if war_test is None else hex(war_test),
        at(war_test) if war_test else "-")
    clr = bits_cleared(peace_mask)
    war = bits_cleared(war_mask)
    row("`and 0x%08x` (any peace mask) clears %s", peace_mask, " ".join(hex(b) for b in clr))
    row("`and 0x%08x` (mask 0x10, war) clears %s", war_mask, " ".join(hex(b) for b in war))
    ok4 = gate("G4a", 0x10 in clr and 0x1 not in clr and 0x2 not in clr and 0x4 not in clr,
               "a peace write ENDS war (clears 0x10) and spares every peace bit")
    ok4 &= gate("G4b", {0x1, 0x2, 0x4} <= set(war) and war_test is not None,
                "the war write ends all three peace bits, and it sits under `test bl,0x10`")
    ok4 &= gate("G4c", clr == [0x10, 0x40, 0x8000, 0x10000, 0x100000],
                "the decoded peace-clear set is exactly those 5 bits")

    # ---------------- G5 ----------------
    print("\nG5 labels.txt, re-read")
    lines = open(LABELS, "rb").read().decode("latin-1").splitlines()
    cnt = int(lines[9].strip())
    row("count line 9 = %d; lines 652-655 = %s", cnt,
        " / ".join(l.strip() for l in lines[651:655]))
    g5 = gate("G5a", cnt == 1089, "header count = 1089")
    for bit, elem in sorted(LABEL_ELEM.items()):
        s = lines[10 + elem].strip()
        row("bit 0x%x <-> element %d <-> line %d = `%s`", bit, elem, 10 + elem, s)
        g5 &= gate("G5-%x" % bit, s == EXPECT_LABEL[bit],
                   "bit 0x%x's label element reads `%s`" % (bit, s))
    g5 &= gate("G5b", lines[10 + 866].strip() == "Diplomacy for",
               "control: element 866 = `Diplomacy for` (the page title)")
    elems = [LABEL_ELEM[b] for b in (0x4, 0x2, 0x1)]
    row("bit->element map (M367, V: evidence/m367_label_index.txt:30-32) = %s; neighbours `%s`",
        elems, "/".join(lines[10 + e].strip() for e in range(elems[0] - 1, elems[-1] + 2)))
    g5 &= gate("G5c", elems == list(range(elems[0], elems[0] + 3)) and
               lines[10 + elems[0] - 1].strip() == "Clock",
               "the three elements are consecutive and sit after the `Clock` line")

    # ---------------- G6 ----------------
    print("\nG6 FUN_005076d0 same-state classifier")
    tests = [(a, imm(TXT[a])) for a in INSN
             if 0x50796F <= a <= 0x507998 and re.match(r"test\s+cl,0x[0-9a-f]+$", TXT[a])]
    tests.sort()
    je_t, jne_t, jumps = [], [], []
    for a, v in tests:
        je, pair, jne = around(a, 1), around(a, 2), around(a, 3)
        je_t.append(imm(at(je)))
        jne_t.append(imm(at(jne)) if at(jne).startswith("jne") else None)
        jumps.append(imm(at(around(a, 4))) if at(around(a, 4)).startswith("jmp") else None)
        row("0x%x test cl,0x%x -> %s %s -> %s -> %s", a, v, at(je), "0x%x" % imm(at(je)),
            at(pair), at(jne))
    order = [v for a, v in tests]
    paired = all(re.match(r"test\s+BYTE PTR \[ebp-0xc\],0x[0-9a-f]+$", at(around(a, 2)))
                 and imm(at(around(a, 2))) == v for a, v in tests)
    NUMOP = ("cmp", "sub", "add", "jg", "jge", "jl", "jle", "ja", "jae", "jb", "jbe",
             "inc", "dec", "shl", "sar", "imul")
    numeric = [a for a in INSN if 0x50796F <= a <= 0x507998 and TXT[a].split()[0] in NUMOP]
    hx = lambda x: "-" if x is None else ("0x%x" % x)
    row("tested %s; je targets %s; jne targets %s; jmp-to-mismatch %s",
        order, [hx(x) for x in je_t], [hx(x) for x in jne_t], [hx(x) for x in jumps])
    row("numeric opcodes inside the window: %d %s", len(numeric),
        [("%s@%x" % (TXT[a].split()[0], a)) for a in numeric])
    ok6 = gate("G6a", order == [0x1, 0x2, 0x4], "the classifier's precedence is 0x1, 0x2, 0x4")
    ok6 &= gate("G6b", paired and len(tests) == 3,
                "3 tests, each paired with the SAME mask on the other record")
    ok6 &= gate("G6c", not numeric, "no numeric opcode in the window: EQUALITY, not a rank")
    ok6 &= gate("G6d", je_t == [0x507982, 0x50798F, 0x5079A1] and
                set(jne_t) == {0x5079A1} and jumps[:2] == [0x50799A, 0x50799A],
                "the chain runs test->je(next test)->pair->jne(match)->jmp(mismatch 0x50799a)")
    ok6 &= gate("G6e", at(0x50799A) == "mov    DWORD PTR [ebp-0x8],0x1",
                "0x50799a is the mismatch store `%s`" % at(0x50799A))

    # ---------------- G7 ----------------
    print("\nG7 RIVALS")
    g7 = True
    g7 &= gate("G7a", g2, "R1 the bits are SWAPPED (0x2=Truce, 0x4=Treaty)      killed by G2-*")
    g7 &= gate("G7b", ok3 and ok6, "R2 they are INDEPENDENT flags, not a ladder    killed by G3a+G6a")
    g7 &= gate("G7c", g2, "R3 the nouns are label text only, no behaviour     killed by G2-*")
    g7 &= gate("G7d", ok6, "R4 the classifier is a numeric >= rank            killed by G6c")
    g7 &= gate("G7e", ok4, "R5 the three bits are not a family (war is unrelated) killed by G4a+G4b")

    npass = sum(1 for g, c, m in GATES if c)
    dig = hashlib.sha1(("\n".join(ROWS)).encode()).hexdigest()[:16]
    ok = npass == len(GATES)
    print("\n%s M368: %d/%d gates  digest %s"
          % ("PASS" if ok else "FAIL", npass, len(GATES), dig))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
