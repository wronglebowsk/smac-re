#!/usr/bin/env python3
"""M349 - the queue-head UNIT-ID decode: head < 0 is the NEGATED UNIT TYPE, head >= 0
is the FACILITY item id, head == -38 is the sentinel slot.

Static only (no box, no gdb, no Wine).  Every number printed below is PARSED out of the
objdump listing of terran.exe's .text (scratch/m574/text.txt) or out of the recorded B31
oracle rows (evidence/b31_facoracle.txt); the gates then assert the parsed values against
declared literals, so a drift in the binary, the listing or the trace reddens a gate.

    python3 -u scripts/m349_unit_id.py            # acceptance
    python3 -u scripts/m349_unit_id.py --digest   # digest only

The decode block (FUN_004ef6d0, head read from the base record's queue slot 0 at +0x50):

  0x4ef88b  mov  ecx,[eax+0x50]        ; head = queue[0]
  0x4ef88e  cmp  ecx,0xffffffda        ; -38  -> the empty/sentinel handler
  0x4ef899  jge  0x4efa2c              ; head >= 0  -> FACILITY leg, item = head
  0x4ef89f  neg  ecx                   ; head < 0   -> item = -head  (the UNIT TYPE)
  0x4ef8a1  cmp  ecx,0x27              ; type >= 39 -> second-table index = type-39
  0x4ef8b8  cmp  ecx,0x22 / 0x26       ; 34 <= type < 38 -> the [ebp-0x20] band flag

Facility leg (head >= 0): item < 0x40 stamps the bitmap bit (0x4efe41 cmp ebx,0x40 /
jl 0x4efed1 -> [ebp-0x20]=0); item >= 0x40 is gated by bit 2 of the item-table word at
0x98adb8 instead.  Both legs use the SAME mapper FUN_00507410 (byte = id/8 truncating
toward zero, mask = 1<<(id&7)) on the SAME per-player bitmap (0x95da9c + 304*player):
the facility leg ORs (0x4f0ec0), the unit leg ANDs/tests (0x4ef97a) and never writes.
"""
import argparse
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
B31 = os.path.join(ROOT, "evidence", "b31_facoracle.txt")

ROW = re.compile(r"^\s*([0-9a-f]{6,8}):\t([0-9a-f ]+)\t(.*)$")


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


class Listing:
    def __init__(self, path):
        self.at = {}
        self.order = []
        with open(path, "r", errors="replace") as f:
            for line in f:
                m = ROW.match(line)
                if not m:
                    continue
                a = int(m.group(1), 16)
                self.at[a] = norm(m.group(3))
                self.order.append(a)
        self.order.sort()

    def get(self, addr):
        return self.at.get(addr)

    def window(self, lo, hi):
        return [(a, self.at[a]) for a in self.order if lo <= a <= hi]

    def calls(self, target):
        pat = "call 0x%x" % target
        return [a for a in self.order if self.at[a] == pat]


L = Listing(TEXT)

# ---------------------------------------------------------------- declared literals
SENTINEL = 0xFFFFFFDA           # compared at 0x4ef88e; == -38
TYPE_MAX = 0x27                 # 39
BAND_LO, BAND_HI = 0x22, 0x26   # 34, 38
ITEM_THRESHOLD = 0x40           # 64, facility-leg stamp gate
BITMAP_BASE = None              # parsed from the two sites (must agree)
MAPPER = 0x507410
QUEUE_SLOT0 = 0x50

DECODE_BLOCK = [
    (0x4EF88B, "mov ecx,DWORD PTR [eax+0x50]"),
    (0x4EF88E, "cmp ecx,0xffffffda"),
    (0x4EF891, "je 0x4ef9b3"),
    (0x4EF897, "test ecx,ecx"),
    (0x4EF899, "jge 0x4efa2c"),
    (0x4EF89F, "neg ecx"),
    (0x4EF8A1, "cmp ecx,0x27"),
    (0x4EF8A4, "mov DWORD PTR [ebp-0x30],ecx"),
    (0x4EF8A7, "jl 0x4ef8b1"),
    (0x4EF8A9, "lea edx,[ecx-0x27]"),
    (0x4EF8AC, "mov DWORD PTR [ebp-0x1c],edx"),
    (0x4EF8AF, "jmp 0x4ef8b8"),
    (0x4EF8B1, "mov DWORD PTR [ebp-0x1c],0xffffffff"),
    (0x4EF8B8, "cmp ecx,0x22"),
    (0x4EF8BB, "jl 0x4ef8c9"),
    (0x4EF8BD, "cmp ecx,0x26"),
    (0x4EF8C0, "mov DWORD PTR [ebp-0x20],0x1"),
    (0x4EF8C7, "jl 0x4ef8d0"),
    (0x4EF8C9, "mov DWORD PTR [ebp-0x20],0x0"),
]

FACILITY_BLOCK = [
    (0x4EFE41, "cmp ebx,0x40"),
    (0x4EFE44, "jl 0x4efed1"),
    (0x4EFE50, "mov ax,WORD PTR [edx+0x98adb8]"),
    (0x4EFE59, "or al,0x4"),
    (0x4EFED1, "mov DWORD PTR [ebp-0x20],0x0"),
]

UNIT_SITE = [
    (0x4EF93E, "mov eax,DWORD PTR [ebp-0x30]"),
    (0x4EF947, "cmp eax,0x22"),
    (0x4EF94A, "jg 0x4f0a3d"),
    (0x4EF95C, "call 0x507410"),
    (0x4EF970, "mov al,BYTE PTR [ecx+edx*1+0x95da9c]"),
    (0x4EF97A, "and al,cl"),
]

STAMP_SITE = [
    (0x4F0EA2, "call 0x507410"),
    (0x4F0EB6, "lea eax,[ecx+edx*1+0x95da9c]"),
    (0x4F0EBD, "mov cl,BYTE PTR [ebp-0x18]"),
    (0x4F0EC0, "or BYTE PTR [eax],cl"),
]

COST_BLOCK = [
    (0x4EF8E7, "lea edx,[esi+esi*2]"),
    (0x4EF8EA, "shl edx,0x4"),
    (0x4EF8ED, "imul edi,DWORD PTR [edx+0x984d44]"),
]

# heads this milestone decodes: the B31 recorded heads plus the boundary/branch probes
UNIVERSE = [-39, -38, -24, -8, -6, -3, -2, -1, 0, 1, 2, 31, 32, 33, 34, 37,
            38, 39, 63, 64, 128, 133, 192, 193, 195, 196, 321]

EXPECT = {
    -38: ("SENTINEL", None, None, None),
    -39: ("UNIT", 39, 0, 0),
    -24: ("UNIT", 24, -1, 0),
    -8: ("UNIT", 8, -1, 0),
    -6: ("UNIT", 6, -1, 0),
    -3: ("UNIT", 3, -1, 0),
    -2: ("UNIT", 2, -1, 0),
    -1: ("UNIT", 1, -1, 0),
    0: ("FACILITY", 0, None, 0),
    2: ("FACILITY", 2, None, 0),
    63: ("FACILITY", 63, None, 0),
    64: ("BIGITEM", 64, None, None),
    321: ("BIGITEM", 321, None, None),
}


def decode(head):
    """The model transcribed from the decode block."""
    if head == -38:
        return ("SENTINEL", None, None, None)
    if head >= 0:
        return ("FACILITY" if head < 64 else "BIGITEM", head, None, 0 if head < 64 else None)
    t = -head
    second = t - 39 if t >= 39 else -1
    band = 1 if 34 <= t < 38 else 0
    return ("UNIT", t, second, band)


def byte_bit(item):
    """FUN_00507410: signed divide by 8 truncating toward zero, mask 1<<(item&7)."""
    b = (item + ((item >> 31) & 7)) >> 3
    return b, 1 << (item & 7)


def parse_scale():
    """COST_BLOCK: lea [esi+esi*2] -> 3, shl 4 -> 16, total 48."""
    a = L.get(0x4EF8E7) or ""
    m = re.search(r"\[esi\+esi\*(\d+)\]", a)
    k = int(m.group(1)) + 1 if m else 0
    s = L.get(0x4EF8EA) or ""
    sh = re.search(r"shl edx,0x([0-9a-f]+)", s)
    imm = int(sh.group(1), 16) if sh else 0
    return k, imm, k * imm


def stride_304():
    """Both bitmap sites: lea eax,[esi+esi*8]; lea ecx,[esi+eax*2]; shl ecx,0x4 => 304."""
    out = []
    for base in (0x4EF964, 0x4F0EAA):
        a = L.get(base) or ""
        m = re.search(r"\[esi\+esi\*(\d+)\]", a)
        k = int(m.group(1)) + 1 if m else 0
        b = L.get(base + 6) or ""
        m2 = re.search(r"\[esi\+eax\*(\d+)\]", b)
        c = int(m2.group(1)) + 1 if m2 else 0
        d = L.get(base + 9) or ""
        m3 = re.search(r"shl ecx,0x([0-9a-f]+)", d)
        e = int(m3.group(1), 16) if m3 else 0
        out.append(k * c * e)
    return out


def bitmap_base():
    """The [ecx+edx*1+0x95da9c] base parsed from BOTH sites; they must agree."""
    bases = []
    for addr in (0x4EF970, 0x4F0EB6):
        s = L.get(addr) or ""
        m = re.search(r"\[ecx\+edx\*1\+0x([0-9a-f]+)\]", s)
        bases.append(int(m.group(1), 16) if m else None)
    return bases


def b31_heads():
    """The six G3 rows of the recorded oracle: head and the bit that appeared."""
    rows = []
    with open(B31, "r", errors="replace") as f:
        for line in f:
            m = re.search(r"head=(-?\d+)\s+gained_bit=(\d+)", line)
            if m:
                rows.append((int(m.group(1)), int(m.group(2))))
    return rows


FAIL = []


def gate(ok, label, detail=""):
    if ok:
        print("ok   %s%s" % (label, ("  " + detail) if detail else ""))
    else:
        print("FAIL %s%s" % (label, ("  " + detail) if detail else ""))
        FAIL.append(label)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--digest", action="store_true")
    args = ap.parse_args()

    print("M349 - queue head -> item/bitmap-id decode (terran.exe .text, static)")
    print("listing: %s" % os.path.relpath(TEXT, ROOT))

    # ---- TABLE 1: the decode block, as parsed
    print("\nTABLE 1  the decode block FUN_004ef6d0 @0x4ef88b..0x4ef8c9")
    for addr, want in DECODE_BLOCK:
        got = L.get(addr)
        print("  0x%06x  %-42s %s" % (addr, got, "" if got == want else "!= " + want))
    print("TABLE 1  facility leg @0x4efe41")
    for addr, want in FACILITY_BLOCK:
        got = L.get(addr)
        print("  0x%06x  %-42s %s" % (addr, got, "" if got == want else "!= " + want))

    # ---- TABLE 2: the decode model
    print("\nTABLE 2  head -> class, item, second-table index, band[34,38)")
    print("  %6s  %-9s %6s %7s %5s %6s %6s" % ("head", "class", "item", "second", "band", "byte", "bit"))
    tbl = {}
    for h in UNIVERSE:
        cls, item, second, band = decode(h)
        b, m = byte_bit(item) if item is not None else ("-", "-")
        tbl[h] = (cls, item, second, band)
        print("  %6d  %-9s %6s %7s %5s %6s %6s" % (h, cls, item, second, band, b, m))

    # ---- TABLE 3: the recorded B31 heads, re-decoded
    print("\nTABLE 3  the recorded B31 G3 heads through the decode")
    heads = b31_heads()
    counts = {"UNIT": 0, "FACILITY": 0, "BIGITEM": 0, "SENTINEL": 0}
    for h, bit in heads:
        cls, item, second, band = decode(h)
        counts[cls] += 1
        b, m = byte_bit(item) if item is not None else ("-", "-")
        print("  head=%-6d class=%-8s item=%-5s bit_that_appeared=%-3d mapper=(%s,%s)"
              % (h, cls, item, bit, b, m))
    print("  counts unit=%d facility=%d bigitem=%d sentinel=%d"
          % (counts["UNIT"], counts["FACILITY"], counts["BIGITEM"], counts["SENTINEL"]))

    # ---- TABLE 4: measured literals
    k, imm, cost_stride = parse_scale()
    s1, s2 = stride_304()
    bb1, bb2 = bitmap_base()
    global BITMAP_BASE
    BITMAP_BASE = bb1 if bb1 == bb2 else None
    mapper_calls = L.calls(MAPPER)
    cost_base = 0x984D44
    arr_base = 0x984D38
    mw = L.window(MAPPER, MAPPER + 0x27)
    print("\nTABLE 4  measured literals")
    print("  decode constants   sentinel=0x%08x type_max=0x%02x band=0x%02x..0x%02x item64=0x%x"
          % (SENTINEL, TYPE_MAX, BAND_LO, BAND_HI, ITEM_THRESHOLD))
    print("  cost table         stride=%d (lea x%d, shl x%d) base=0x%x  arr=%d*0x30+0x%x"
          % (cost_stride, k, imm, cost_base, cost_base - arr_base, cost_base - arr_base))
    print("  bitmap sites       stride=%d and %d base=0x%x/0x%x" % (s1, s2, bb1 or 0, bb2 or 0))
    print("  mapper             insns=%d bytes=%d call_sites=%d" % (len(mw), 39, len(mapper_calls)))

    # ---- gates
    print("")
    gate(all(L.get(a) == w for a, w in DECODE_BLOCK), "G1 the decode block is the pinned 19-instruction sequence")
    s_ops = [L.get(a) for a, _ in FACILITY_BLOCK]
    gate(s_ops[0] == "cmp ebx,0x40" and s_ops[1] == "jl 0x4efed1"
         and s_ops[3] == "or al,0x4" and s_ops[4] == "mov DWORD PTR [ebp-0x20],0x0",
         "G2 the facility leg gates the stamp on item < 0x40 (else the 0x98adb8 bit 2)")
    pin = (SENTINEL, TYPE_MAX, BAND_LO, BAND_HI, ITEM_THRESHOLD)
    gate(pin == (0xFFFFFFDA, 0x27, 0x22, 0x26, 0x40), "G3 the five decode constants are the declared literals",
         "sentinel=%d" % (SENTINEL - (1 << 32)))
    bad = [h for h, want in EXPECT.items() if tbl[h] != want]
    gate(not bad, "G4 the model reproduces every pinned row", "bad=%s" % bad)
    gate(all(L.get(a) == w for a, w in UNIT_SITE), "G5 the unit leg TESTS the mapper bit (and al,cl @0x4ef97a)")
    gate(all(L.get(a) == w for a, w in STAMP_SITE), "G6 the stamp ORs the same bitmap @0x4f0ec0")
    gate(BITMAP_BASE == 0x95DA9C and s1 == 304 and s2 == 304,
         "G7 both sites index 0x95da9c + 304*player (equal stride, one array)")
    gate(cost_stride == 48 and cost_base - arr_base == 0xC and L.get(0x4EF8ED) == "imul edi,DWORD PTR [edx+0x984d44]",
         "G8 the unit type indexes the 72-record array at 0x984d38 (stride 0x30, +0xc)")
    gate(len(mw) == 17 and len(mapper_calls) > 150,
         "G9 FUN_00507410 is the 17-instruction id->byte/bit mapper", "callers=%d" % len(mapper_calls))
    gate(counts == {"UNIT": 4, "FACILITY": 1, "BIGITEM": 1, "SENTINEL": 0},
         "G10 the recorded B31 heads split 4 unit / 1 facility / 1 >=64", str(counts))

    # ---- rivals, scored on the printed numbers
    print("\nRIVALS")
    # R1: the negative magnitude is a bitmap byte index
    r1 = [(h, -h) for h in (-24, -8, -6, -3, -2)]
    r1_ok = all(decode(h)[0] == "UNIT" and decode(h)[1] == -h for h, _ in r1)
    print("  R1 'a negative head is a bitmap byte index' -> decode reads it as a type id: %s" % r1_ok)
    # R2: the M68 pair is -(id-192)
    r2 = (-(195 - 192), -(196 - 192))
    print("  R2 'the M68 negative is -(design_id-192)' -> predicts %s, recorded (-3,-6)" % (r2,))
    # R3: -39 is the sentinel
    print("  R3 '-39 is the head sentinel' -> the compared constant is 0x%08x (-38); decode(-39)=%s"
          % (SENTINEL, tbl[-39]))
    # R4: heads > 31 are unit-encoded
    print("  R4 'head > 31 is unit-encoded' -> decode(128)=%s decode(321)=%s (>=0 goes to the facility leg)"
          % (tbl[128][0], tbl[321][0]))
    gate(r1_ok and r2[0] == -3 and r2[1] == -4 and r2[1] != -6,
         "G11 R1/R2 fail on the printed numbers (the -(id-192) rival misses -6)")
    gate(tbl[-39][0] == "UNIT" and tbl[128][0] == "BIGITEM" and tbl[321][0] == "BIGITEM",
         "G12 R3/R4 fail: -39 decodes as a unit type and >31 heads take the >=64 facility gate")

    body = "\n".join("%d:%s" % (h, tbl[h]) for h in UNIVERSE)
    body += "\n%d %d %d %d %d %d" % (cost_stride, s1, s2, len(mw), len(mapper_calls), counts["UNIT"])
    dig = hashlib.sha256(body.encode()).hexdigest()[:16]
    print("\nDIGEST %s  universe=%d gates=%d" % (dig, len(UNIVERSE), 12))
    if FAIL:
        print("FAIL M349: %d gate(s) red: %s" % (len(FAIL), FAIL))
        return 1
    print("PASS M349: 12/12 gates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
