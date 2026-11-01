#!/usr/bin/env python3
"""M240: how the .MP grid becomes the live 44-byte terrain record array.

The claim under test: FUN_00582260 (map_load_arrays) reads the grid VERBATIM into
the array FUN_00582000 allocates - so the MAP_FORMAT.md "22-byte cell" is HALF a
live record, the record covers TWO map columns, and no transform loop exists.

Acceptance: python3 scripts/m240_terrain_repack.py  ->  PASS M240: n/n gates
Writes evidence/m240_terrain_repack.txt. Static only: no box, no /proc, no gdb.
"""
import os, re, struct, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = ["planet.MP", "planetx.MP"]
PRE, HDR, REC = 15, 2724, 0x2C
SHARD = None  # set lazily; shard 014 holds the loader + accessor family


def text(n="014"):
    p = os.path.join(ROOT, "ghidra_out", "shard_%s.c" % n)
    return open(p, encoding="utf-8", errors="replace").read()


def body(fn, n="014"):
    m = re.search(r"^// ==== %s @ [^\n]*\n(.*?)(?=^// ==== |\Z)" % fn,
                  text(n), re.S | re.M)
    return m.group(1) if m else ""


def read_map(name):
    d = open(os.path.join(ROOT, "programs", "maps", name), "rb").read()
    w, h = struct.unpack_from("<II", d, PRE)
    hdr = struct.unpack_from("<8I", d, PRE)
    grid = d[PRE + HDR:]
    n = (w // 2) * h
    recs = [grid[i * REC:(i + 1) * REC] for i in range(n)]
    return d, w, h, hdr, recs, len(grid) - n * REC


def g_accounting():
    """Loader's three read sizes must add up to the whole file, both maps."""
    det = []
    for name in MAPS:
        d, w, h, hdr, recs, tail = read_map(name)
        n = (w // 2) * h
        region = (((w + 4) // 5 + 1) // 2) * ((h + 4) // 5)
        tot = PRE + HDR + n * REC + region
        det.append("%s %dx%d: 15+2724+%d*44+%d=%d vs size %d, word5=%d vs n=%d" %
                   (name, w, h, n, region, tot, len(d), hdr[5], n))
        if tot != len(d) or hdr[5] != n:
            return False, det
    return True, det


def g_verbatim_loader():
    """FUN_00582260: three sized reads, allocator between #1 and #2, NO loop."""
    b = body("FUN_00582260")
    calls = re.findall(r"FUN_0064cc00\(([^)]*)\)", b)
    want = ["&DAT_0092a378,0xaa4", "DAT_0092ae14,DAT_0092a38c * 0x2c",
            "DAT_0092ae18,DAT_0092ada4"]
    ok = len(calls) == 3 and all(w in c for w, c in zip(want, calls))
    loop = re.search(r"\bdo\b|\bfor \(|\bwhile \(|goto ", b)
    return ok and loop is None, ["reads=%s loops=%s" % (calls, bool(loop))]


def g_allocator():
    """FUN_00582000: stride = w/2, count = (w/2)*h, alloc = count * 0x2c."""
    b = body("FUN_00582000")
    want = ["DAT_00692184 = DAT_0092a378 / 2",
            "DAT_0092a38c = DAT_00692184 * DAT_0092a37c",
            "DAT_0092ae14 = FUN_005be090(DAT_0092a38c * 0x2c)"]
    miss = [w for w in want if w not in b]
    return not miss, ["missing=%s" % (miss or "none")]


def g_record_fields():
    """Record byte 7 is the CONSTANT 0xff (B1's 'land marker' is a cell/record
    artifact); byte 22 is never a category; nibbles behave as the accessors say."""
    det, ok = [], True
    for name in MAPS:
        _, _, _, _, recs, _ = read_map(name)
        n = len(recs)
        c7 = sum(1 for r in recs if r[7] == 0xFF)
        c29 = sum(1 for r in recs if r[29] == 0xFF)
        cats = Counter(r[0] >> 5 for r in recs)
        oddcat = set(r[22] >> 5 for r in recs)
        terr = set(r[2] >> 4 for r in recs)
        own = set(r[2] & 0xF for r in recs)
        sea = sum(v for k, v in cats.items() if k < 3)
        det.append("%s: recs=%d +7==ff:%d +29==ff:%d cats=%s odd-half cats=%s "
                   "terr=%s own=%s sea(cat<3)=%d land=%d" %
                   (name, n, c7, c29, sorted(cats.items()), sorted(oddcat),
                    sorted(terr), sorted(own), sea, n - sea))
        if not (c7 == n and c29 == 0 and oddcat == {0} and max(cats) < 7
                and len(cats) == 7 and terr == set(range(16))
                and own <= set(range(8)) | {0xF}):
            ok = False
    return ok, det


def g_accessor_bits():
    """Each named accessor must write exactly the field the file cell carries.
    Gate is per-function presence, not a corpus-wide count."""
    want = [("FUN_005823c0", "& 0x1f | (char)param_3 << 5", "byte 0 bits 5-7 = category"),
            ("FUN_00582cc0", "& 0xf | param_3 << 4", "byte 2 HIGH nibble = terrain type"),
            ("FUN_00582c80", "^ (*(byte *)(DAT_0092ae14 + 2 + ", "byte 2 LOW nibble = owner"),
            ("FUN_00582f70", "& 0xffffff | param_3 << 0x18", "dword +0xc, byte at +0xf"),
            ("FUN_00582ea0", "ae14 + 8 + (DAT_00692184 * param_2 + (param_1 >> 1)) * 0x2c", "dword +8 = mask"),
            ("FUN_00582390", "ae14 + 1 + (DAT_00692184 * param_2 + (param_1 >> 1)) * 0x2c", "byte +1"),
            ("FUN_00582d00", "ae14 + 3 + (DAT_00692184 * param_2 + (param_1 >> 1)) * 0x2c", "byte +3")]
    miss = []
    for fn, pat, what in want:
        if pat not in body(fn):
            miss.append("%s lacks %r (%s)" % (fn, pat, what))
    return not miss, ["missing=%s" % (miss or "none (%d accessors verified)" % len(want))]


def ptr_offsets():
    """INFO: offsets applied to a VARIABLE holding a terrain record pointer
    (Ghidra idiom: v = DAT_0092ae14 [+ idx * 0x2c]; later *(v + 0xNN)). The var
    stops counting as soon as it is reassigned; each function starts clean."""
    terr = re.compile(r"^(\w+) = \(?\w*\)? ?DAT_0092ae14\b")
    asg = re.compile(r"^(\w+) = ")
    hist, cache = Counter(), {}
    for n in sorted(f for f in os.listdir(os.path.join(ROOT, "ghidra_out"))
                    if f.startswith("shard_")):
        tracked = set()
        for line in text(n[6:9]).splitlines():
            s = line.strip()
            if s.startswith("// ===="):
                tracked = set()
                continue
            m = terr.match(s)
            if m:
                v = m.group(1)
                tracked.add(v)
                hist.update(int(x, 0) for x in re.findall(
                    r"\b%s \+ (0x[0-9a-fA-F]{1,2}|\d{1,2})\b" % v, s))
                continue
            a = asg.match(s)
            if a and a.group(1) in tracked:
                tracked.discard(a.group(1))
                continue
            for v in tracked:
                rx = cache.setdefault(v, re.compile(
                    r"\b%s \+ (0x[0-9a-fA-F]{1,2}|\d{1,2})\b" % v))
                for mm in rx.finditer(s):
                    hist[int(mm.group(1), 0)] += 1
    return hist


def g_offset_census():
    """Every DIRECT offset applied to the terrain base is < 0x10: the live tile
    fields live in record bytes 0..15; bytes 16..43 are never touched directly."""
    hist = Counter()
    for n in sorted(os.listdir(os.path.join(ROOT, "ghidra_out"))):
        if not n.startswith("shard_"):
            continue
        for m in re.finditer(r"DAT_0092ae14 \+ (0x[0-9a-fA-F]{1,2}|\d{1,2})\b",
                             text(n[6:9])):
            hist[int(m.group(1), 0)] += 1
    mx = max(hist) if hist else -1
    return (mx <= 0x0E and sum(hist.values()) > 100), \
        ["refs=%d max_off=0x%x hist=%s" % (sum(hist.values()), mx,
                                           sorted(hist.items()))]


def dword_info():
    """INFO: record bytes 16..43 are 7 dwords (+16,+20,...,+40). Census them."""
    det = []
    for name in MAPS:
        _, _, _, _, recs, _ = read_map(name)
        slots = [[struct.unpack_from("<I", r, o)[0] for r in recs]
                 for o in range(16, 44, 4)]
        allsame = sum(1 for s in zip(*slots) if len(set(s)) == 1)
        det.append("%s: slots=%d distinct=%s all7equal=%d/%d" %
                   (name, len(slots), [len(set(s)) for s in slots],
                    allsame, len(recs)))
    return "; ".join(det)


def main():
    gates = [g_accounting(), g_verbatim_loader(), g_allocator(),
             g_record_fields(), g_accessor_bits(), g_offset_census()]
    out = ["M240 - the .MP grid IS the live terrain record array (verbatim read)"]
    npass = 0
    for i, (ok, det) in enumerate(gates, 1):
        npass += ok
        out.append("G%d %s" % (i, "PASS" if ok else "FAIL"))
        out += ["    " + d for d in det]
    out.append("INFO record-pointer offsets (vars holding a record): %s"
               % sorted(ptr_offsets().items()))
    out.append("INFO %s" % dword_info())
    out.append("SUMMARY %s M240: %d/%d gates on %s" %
               ("PASS" if npass == len(gates) else "FAIL", npass, len(gates),
                ", ".join(MAPS)))
    txt = "\n".join(out) + "\n"
    ev = os.path.join(ROOT, "evidence", "m240_terrain_repack.txt")
    open(ev, "w").write(txt)
    print(txt)
    print("evidence:", ev)
    return 0 if npass == len(gates) else 1


if __name__ == "__main__":
    sys.exit(main())
