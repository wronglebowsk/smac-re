#!/usr/bin/env python3
"""M374 - the NOUNS of Semaphore cell 0x92bf0c bits 23/24.

M372 left the two in-game bits of the `Semaphore` pref cell unnamed.  This
instrument reads their provenance and their readers out of the instruction
BYTES and names them from the game's own dialog file:

  0x92bf0c bits 23/24  <-  0x985ae8 (runtime dword)
      <- FUN_004dc5f0: `test eax,0x10000/0x20000` / `or ecx,0x800000/0x1000000`
         where eax = ds:0x99aa38, the flag dword of the script record keyed
         "RULES" (0x68c824) -- i.e. bits 16/17 of an 18-bit rule word.
  #RULES in programs/Script.txt carries exactly 18 items; items 17 and 18 are
      "Randomize faction leader personalities." and
      "Randomize faction leader social agendas."
  Readers: bit 23 at 0x59ef11 seeds five faction-record personality fields and
      at 0x5a1446 sets the faction-pairing arm; bit 24 at 0x5a1150 runs the
      12-slot random assignment per faction.

Gates
  G0  image/text anchors (sha1, instruction windows).
  G1  bit map: record bit 16->cell 23, 17->24, both directions, + store mask.
  G2  the rule word is 18 bits: 16 Rules-cell bits (0..15) + the 2 semaphore
      bits (16/17); the other path clears 23/24 with 0xfe7fffff.
  G3  item<->bit contract: #RULES 18 items = 18 record bits, #AIEDITOR 11
      items = 11 record bits; the two Randomize items are the tail of #RULES.
  G4  readers: bit 23 = five rand-seeded personality fields (+pairing arm);
      bit 24 = 12-slot random assignment.
  G5  rivals: (a) INI loader as the writer; (b) the 0x41a9xx pack as the
      source of the semaphore bits (shared scratch, different consumer).

M374_PATCH='addr|new text' rewrites one instruction line (mutation lever).
M374_ALGO=n flips a law: 1 = 1-based item index, 2 = drop the 0xfe7fffff leg.
"""
import hashlib
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.environ.get("M374_TEXT", os.path.join(ROOT, "scratch/m574/text.txt"))
EXE = os.path.join(ROOT, "programs/terran.exe")
SCRIPT = os.environ.get("M374_SCRIPT", os.path.join(ROOT, "programs/Script.txt"))
INI = os.path.join(ROOT, "programs/Alpha Centauri.Ini")
ALGO = int(os.environ.get("M374_ALGO", "0") or 0)

ADDR = re.compile(r"^\s*([0-9a-f]{6,8}):\s+((?:[0-9a-f]{2} )+)\s*\t(.*)$")
PATCH = {}
for tok in os.environ.get("M374_PATCH", "").split(";"):
    if "|" in tok:
        a, t = tok.split("|", 1)
        PATCH[int(a, 16)] = t


def load_text():
    ins = {}
    order = []
    with open(TEXT, "r", errors="replace") as f:
        for line in f:
            m = ADDR.match(line.rstrip("\n"))
            if not m:
                continue
            a = int(m.group(1), 16)
            t = m.group(3).strip()
            ins[a] = (bytes.fromhex(m.group(2)), PATCH.get(a, t))
            order.append(a)
    order.sort()
    return ins, order


INS, ORDER = load_text()


def g(a):
    return INS[a]


def txt(a):
    return INS[a][1]


def bts(a):
    return INS[a][0]


def imm(text, which=0):
    v = re.findall(r"0x([0-9a-f]+)", text)
    if len(v) <= which:
        return None
    return int(v[which], 16)


def bitof(v):
    return v.bit_length() - 1 if v and (v & (v - 1)) == 0 else None


def win(lo, hi):
    return [a for a in ORDER if lo <= a <= hi]


ROWS = []


def row(tag, what, value):
    ROWS.append((tag, what, value))


def fail(msg):
    print("  FAIL", msg)
    return False


NG = [0]


def check(tag, ok, msg):
    NG[0] += 1
    print("  %-4s %s %s" % (tag, "ok  " if ok else "FAIL", msg))
    return ok


# ---------------------------------------------------------------- G0 anchors
h_txt = hashlib.sha1(open(TEXT, "rb").read()).hexdigest()
h_exe = hashlib.sha1(open(EXE, "rb").read()).hexdigest()
row("G0", "text insns", len(INS))
row("G0", "text sha1", h_txt[:16])
row("G0", "exe sha1", h_exe[:16])
row("G0", "0x59ef11 bytes", bts(0x59ef11).hex(" "))
row("G0", "0x5a1150 bytes", bts(0x5a1150).hex(" "))
row("G0", "0x4dc88b bytes", bts(0x4dc88b).hex(" "))

# ------------------------------------------------------- G1 the bit map
CELL = 0x92BF0C
RUNTIME = 0x985AE8
STAGE = 0x99AA38
legs = []
for ta, oa, sa, stores in ((0x4DC88B, 0x4DC892, 0x4DC898, 23),
                           (0x4DC89E, 0x4DC8A5, 0x4DC8AB, 24)):
    vm = imm(txt(ta))
    vo = imm(txt(oa))
    legs.append((bitof(vm), bitof(vo), stores, ta, oa, sa))
    row("G1", "unpack %x: test %#x -> or %#x (@%x) -> sem bit %d (rec bit %d)"
        % (ta, vm, vo, sa, bitof(vo), bitof(vm)), stores)
mask = imm(txt(0x4DC8B7))
row("G1", "cell store mask @0x4dc8b7", hex(mask))
row("G1", "cell store @0x4dc8c3 target", hex(imm(txt(0x4DC8C3), 0)))
pack = []
for ta, oa, which in ((0x4DC6CF, 0x4DC6D7, 0), (0x4DC6E3, 0x4DC6EB, 0)):
    pack.append((bitof(imm(txt(oa))), bitof(imm(txt(ta))), ta, oa))
    row("G1", "pack %x: test stage %#x -> or stage %#x" %
        (ta, imm(txt(ta)), imm(txt(oa))), None)

# ------------------------------------------------------- G2 the 18-bit word
rules_bits = set()
for a in win(0x4DC616, 0x4DC6CC):
    t = txt(a)
    m = re.match(r"test\s+(cl|ch|dl|dh|al|ah|bh),0x([0-9a-f]+)$", t)
    if m:
        v = int(m.group(2), 16) * (256 if m.group(1)[1] == "h" else 1)
        rules_bits.add(bitof(v))
shr11 = txt(0x4DC60A) == "shr    eax,0xb" and txt(0x4DC60D).startswith("and    eax,0x1")
if shr11:
    rules_bits.add(11)
rown = sorted(rules_bits)
row("G2", "Rules-cell bits the pack reads", len(rown))
row("G2", "their positions", ",".join(str(x) for x in rown))
rec_bits = set(x[0] for x in legs)
row("G2", "record bits the 2 semaphore legs add", sorted(rec_bits))
allbits = sorted(rules_bits | rec_bits)
row("G2", "union", allbits)
row("G2", "other-path clear mask @0x4dc604", hex(imm(txt(0x4DC604))))

# ------------------------------------------------------- G3 item<->bit law
def items(startkey):
    lines = open(SCRIPT, "r", errors="replace").read().splitlines()
    try:
        i = lines.index(startkey)
    except ValueError:
        return None
    j = i
    while j < len(lines) and lines[j].strip() != "#itemlist":
        j += 1
    out = []
    for ln in lines[j + 1:]:
        s = ln.strip()
        if not s or s.startswith("#"):
            break
        out.append(s)
    return out


rules_items = items("#RULES")
ai_items = items("#AIEDITOR")
row("G3", "#RULES items", len(rules_items or []))
row("G3", "#AIEDITOR items", len(ai_items or []))
row("G3", "#RULES tail item 17", (rules_items or [None] * 18)[16])
row("G3", "#RULES tail item 18", (rules_items or [None] * 18)[17])
ai_bits = set()
for a in win(0x4DC1B9, 0x4DC26B):
    t = txt(a)
    m = re.match(r"(test|or|and)\s+(al|ah|cl|ch),0x([0-9a-f]+)$", t)
    if m:
        v = int(m.group(3), 16) * (256 if m.group(2)[1] == "h" else 1)
        b = bitof(v)
        if b is not None:
            ai_bits.add(b)
row("G3", "AIEDITOR record bits (pack block)", len(ai_bits))
idx = 1 if ALGO == 1 else 0
row("G3", "ALGO item-index base", idx)

# ------------------------------------------------------- G4 the two readers
rA = win(0x59EF22, 0x59EF8C)
n_randA = sum(1 for a in rA if "call   0x64c6f0" in txt(a))
fieldsA = [x for x in (0x94D80C, 0x94D810, 0x94D814, 0x94D818, 0x94D81C)]
n_fieldstores = 0
for a in win(0x59EF22, 0x59EF92):
    for f in fieldsA:
        if ("[esi+%#x]" % f) in txt(a).replace("0x94d8", "0x94d8") and "mov" in txt(a):
            n_fieldstores += 1
row("G4", "bit23 gate @0x59ef11", txt(0x59EF11))
row("G4", "its eax source @0x59eedc", txt(0x59EEDC))
row("G4", "rand calls in the gated block", n_randA)
row("G4", "stores into the five fields", n_fieldstores)
row("G4", "idiv 3 present", any("idiv   ecx" in txt(a) for a in rA))
row("G4", "&0x80000001 sign-fix count", sum(1 for a in rA if imm(txt(a)) == 0x80000001))
arm = win(0x5A1446, 0x5A1492)
n_pair = sum(1 for a in arm if "call   0x551c40" in txt(a))
row("G4", "bit23 pairing arm calls", n_pair)
row("G4", "bit24 gate @0x5a1150", txt(0x5A1150))
blk = win(0x5A1150, 0x5A121E)
row("G4", "bit24 block zeroes N dwords", imm(txt(0x5A1160)))
row("G4", "bit24 stride insn", txt(0x5A120D))
row("G4", "bit24 loop bound", imm(txt(0x5A1213)))
row("G4", "bit24 rand calls", sum(1 for a in blk if "call   0x64c6f0" in txt(a)))

# ------------------------------------------------------- G5 rivals + keys
orimm = []
for a in ORDER:
    if re.match(r"or\s+ecx,0x[0-9a-f]+$", txt(a)) and imm(txt(a), 0) in (0x800000, 0x1000000):
        nxt = [b for b in ORDER if a < b <= a + 12]
        if any("mov    DWORD PTR ds:0x985ae8" in txt(b) for b in nxt):
            orimm.append((a, imm(txt(a), 0)))
row("G5", "or ecx,bit23/24 sites", ["%x:%#x" % (a, v) for a, v in orimm])
row("G5", "eax source @0x4dc786", txt(0x4DC786))
row("G5", "0x41a9xx leg 16 @0x41ab1c", txt(0x41AB1C) + " / " + txt(0x41AB21))
row("G5", "0x41a9xx leg 18 @0x41ab36", txt(0x41AB36))
ini = open(INI, "r", errors="replace").read()
m = re.search(r"^Semaphore=(.*)$", ini, re.M)
row("G5", "shipped INI Semaphore", m.group(1) if m else None)
keys = []
for va in (0x68C824, 0x68C80C, 0x68C818, 0x68C82C):
    keys.append((va, None))
row("G5", "script keys (RULES/AIEDITOR/AIEDITOR2/SCENRULES) @", " ".join("%x" % k for k, _ in keys))
row("G5", "0x4dc8b7 mask (=~0x1800000?)", hex(mask ^ 0xFFFFFFFF))

# ------------------------------------------------------------------- print
print("M374 cell 0x92bf0c bits 23/24 - nouns")
print("%-4s %-62s %s" % ("tag", "what", "value"))
for tag, what, val in ROWS:
    print("%-4s %-62s %s" % (tag, what, val))
print()

ok = True
ok &= check("G0", h_txt.startswith("02d578095222") and len(INS) == 781429,
            "text %d insns sha %s" % (len(INS), h_txt[:12]))
ok &= check("G0", bts(0x59EF11) == bytes.fromhex("a900008000") and
            bts(0x5A1150) == bytes.fromhex("f705e85a980000") and
            bts(0x4DC88B) == bytes.fromhex("a900000100"),
            "the three anchor instructions are the bytes the claims decode")

ok &= check("G1", sorted((x[0], x[1]) for x in legs) == [(16, 23), (17, 24)],
            "record bit 16 -> cell bit 23, record bit 17 -> cell bit 24 (both decoded)")
ok &= check("G1", sorted((x[0], x[1]) for x in pack) == [(16, 23), (17, 24)],
            "the pack direction is the same map (round trip)")
ok &= check("G1", mask == 0x1800000 and imm(txt(0x4DC8C3), 0) == CELL,
            "the cell store keeps ONLY bits 23/24 (mask %#x) -> 0x92bf0c" % mask)

ok &= check("G2", allbits == list(range(18)) and len(rules_bits) == 16,
            "the RULES record is an 18-bit word: Rules-cell bits 0..15 + semaphore bits 16/17")
if ALGO == 2:
    ok &= check("G2", False, "ALGO2: the other-path clear-mask leg is ignored")
else:
    ok &= check("G2", imm(txt(0x4DC604)) == 0xFE7FFFFF,
                "the non-record path clears bits 23/24 with 0xfe7fffff")

ok &= check("G3", len(rules_items) == 18,
            "#RULES in Script.txt has 18 items = the record's 18 bits")
ok &= check("G3", len(ai_items) == 11 and len(ai_bits) == 11,
            "#AIEDITOR has 11 items and its pack touches 11 bits (contract holds for a 2nd key)")
tail = (rules_items or [])[16 + idx:18 + idx]
ok &= check("G3", tail == ["Randomize faction leader personalities.",
                           "Randomize faction leader social agendas."],
            "bits 16/17 = the two tail items: %r" % (tail,))

ok &= check("G4", txt(0x59EF11) == "test   eax,0x800000" and
            txt(0x59EEDC) == "mov    eax,ds:0x985ae8",
            "bit 23 reader tests ds:0x985ae8 bit 23 directly")
ok &= check("G4", n_randA == 5 and n_fieldstores == 5,
            "the gated block seeds FIVE faction fields (%d rand calls, %d stores)" % (n_randA, n_fieldstores))
ok &= check("G4", n_pair == 4, "the same bit's pairing arm makes 4 fixed calls")
ok &= check("G4", txt(0x5A1150) == "test   DWORD PTR ds:0x985ae8,0x1000000",
            "bit 24 reader tests ds:0x985ae8 bit 24 directly")
ok &= check("G4", imm(txt(0x5A1160)) == 0xC and "rep stos" in txt(0x5A116F),
            "the gated block is the 12-slot assignment (zeroes 0xc dwords)")

ok &= check("G5", orimm == [(0x4DC892, 0x800000), (0x4DC8A5, 0x1000000),
                            (0x57CC35, 0x800000), (0x57CC48, 0x1000000)],
            "only TWO blocks write each bit (4 or-sites, all from the record's 16/17)")
ok &= check("G5", txt(0x4DC786) == "mov    eax,ds:0x99aa38",
            "the writer's eax is the script record's staging dword, not a 0x41a9xx read")
ok &= check("G5", m is not None and m.group(1).strip() == "00000000",
            "shipped INI Semaphore=00000000 -> the loader alone sets neither bit")

dig = hashlib.sha1(repr(ROWS).encode()).hexdigest()[:16]
print()
print("%s M374: %d/%d gates digest %s" % ("PASS" if ok else "FAIL", NG[0] if ok else 0, NG[0], dig))
sys.exit(0 if ok else 1)
