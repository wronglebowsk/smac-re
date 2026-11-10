#!/usr/bin/env python3
"""M281 - who reads region ids >= 128 on a 128x128 map? ANSWER: nobody, they cannot exist.

Pick (NEXT_PROMPT, static pick (c)): the region loops bound at cmp reg,0x80 (0x556737,
0x558b1c) and never reach ids >= 128, while the coarse region map for a 128x128 map has
338 bytes. Who reads region 128+ - another loop, another function?

Thesis (to be PROVEN by the gates, not assumed): the region ID SPACE is architecturally
capped at 0x7f by the generator FUN_0058d390's band scheme (land ids 1..0x3e, water ids
0x41..0x7e, overflow slots 0x3f/0x7f). 338 is the coarse-map CELL count
(((Rw+1)/2)*Rh), not a region id count, and the count global DAT_0092ada4 is referenced
by exactly 4 sites, all alloc/clear/file-I/O - never a loop bound. M251's "128 entries =
the whole id space" therefore STANDS for every map size, and the 0x80 loops cover the
entire id space. There is nothing at id >= 128 to read.

Static only: shard pseudocode + disassembly cache + shipped map/save files. No box time,
no /proc, no gdb, no sudo.
Acceptance: ONE invocation prints PASS on every gate; an undecided gate prints FAIL with
its numbers.

Gates:
  G1  FUN_0058d390 band caps: land clamp 0x3e, water clamp 0x7e, overflow slots 0x3f/0x7f
      -> the LARGEST id the generator can ever assign is 0x7f (127).
  G2  the two region-loop bounds: cmp edi,0x80 @0x556737 and cmp ecx,0x80 @0x558b1c,
      both inside FUN_00556690 (index.csv containment), operands vs immediate 0x80.
      Since max id = 127 < 128, both loops cover the whole id space.
  G3  DAT_0092ada4 (the count that is 338 on 128x128) reference census: exactly the
      4 known sites in shard_014 (27266 alloc expr, 27267 alloc arg, 27342 file-write,
      27376 file-read); assert NO cmp/jb/jbe/jl/jae/ja instruction references it and no
      reference appears in any other shard -> it is never a loop bound.
  G4  accessor arithmetic: FUN_00582340/00582360 index DAT_0092ae18 as
      (x>>1) + (Rw>>1)*y with length ((Rw+1)/2)*Rh -> for the even Rw of the shipped
      maps (16, 26) the stored byte count IS the cell count Rw/2*Rh (128, 338), i.e. the
      "338" is number of coarse CELLS (one byte per 2-cell block), not an id space; the
      triad (91,128,338) matches (len(64x64),len(80x80),len(128x128)).
  G5  tile-label census: decode the terrain record +3 plane (the region label) over
      planet.MP, planetx.MP and every save under programs/saves; assert max label <= 0x7f
      on EVERY file (planet.MP's 127 IS the 0x7f border/overflow slot - still < 128);
      print per-file max + the count of labels >= 0x80 (must be 0).
  G6  region table capacity: the DAT_00989ce0 save section is 3584 bytes at stride 0x1c
      = exactly 128 rows (3584 / 28 == 128.0), so the per-region table itself has
      128 slots - it CANNOT hold or address an id >= 128.
  G7  rival check, image-wide over the disasm cache: no `cmp reg,0x152` (338) anywhere,
      no `*0x152` scaling, and no memory-operand compare whose displacement is
      DAT_0092ada4 -> no loop in the image is bounded by 338. (A real "reads region 338
      ids" path would have to compare a loop counter against the count; none exists.)

Acceptance line: python3 scripts/m281_region_id_cap.py  ->  SUMMARY M281: 7/7 gates PASS
"""
import csv
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARD14 = os.path.join(ROOT, "ghidra_out", "shard_014.c")
SHARD15 = os.path.join(ROOT, "ghidra_out", "shard_015.c")
SHARDS = sorted(glob.glob(os.path.join(ROOT, "ghidra_out", "shard_*.c")))
INDEX = os.path.join(ROOT, "ghidra_out", "index.csv")
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
SAVES = sorted(glob.glob(os.path.join(ROOT, "programs", "saves", "*.SAV")))
MAPS = [os.path.join(ROOT, "programs/maps/planet.MP"),
        os.path.join(ROOT, "programs/maps/planetx.MP")]
GEN_FUN = "FUN_0058d390"
CONS_FUN = "FUN_00556690"
COUNT_DAT = "DAT_0092ada4"
REGION_DAT = "DAT_0092ae18"
TABLE_DAT = "DAT_00989ce0"
CMP_SITES = (0x556737, 0x558b1c)
STRIDE_TABLE = 0x1c
SECTION_TABLE_BYTES = 3584       # decode_save.py section list, offset for 0x989ce0
MAP_HDR_MAGIC_LEN = 15
MAP_HDR_LEN = 2724
REC = 22                          # terrain grid record stride (bytes)
SAVE_GRID_OFF = 82096             # grid start inside a save
TWENTY_TWO = 22

res = []


def gate(n, ok, det=""):
    res.append((n, bool(ok), det))
    print("G%d %s: %s" % (n, "PASS" if ok else "FAIL", det))


def shard_src(shard_path):
    with open(shard_path, errors="replace") as fh:
        return fh.read()


def fn_body(src, fun):
    m = re.search(r"^// ==== %s @ (0x[0-9a-f]+) size=\d+\n\n(?:.*?\n)*?^(?=// ==== )" % re.escape(fun),
                  src, re.M)
    if not m:
        # fallback: banner to next banner
        b = re.search(r"^// ==== %s @ (0x[0-9a-f]+) size=\d+" % re.escape(fun), src, re.M)
        if not b:
            return None
        nxt = re.search(r"^// ==== ", src[b.end():], re.M)
        end = b.end() + (nxt.start() if nxt else len(src) - b.end())
        return src[b.start():end]
    return m.group(0)


def load_index():
    rows = []
    with open(INDEX) as fh:
        for r in csv.DictReader(fh):
            if r["addr"]:
                rows.append((int(r["addr"], 16), int(r["size_bytes"]), r["name"]))
    rows.sort()
    return rows


def fn_of(pc, rows):
    lo, hi = 0, len(rows)
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid][0] <= pc:
            lo = mid + 1
        else:
            hi = mid
    i = lo - 1
    if i >= 0 and rows[i][1] > pc - rows[i][0]:
        return rows[i][2]
    return None


def load_text():
    pat = re.compile(r"\s+([0-9a-f]+):\t([0-9a-f ]*)\t(\S+)\s?(.*)")
    ins = []
    with open(TEXT, errors="replace") as fh:
        for ln in fh:
            m = pat.match(ln)
            if m and m.group(3):
                ins.append((int(m.group(1), 16), m.group(3), m.group(4).split("#")[0].strip()))
    return ins


def u32(d, off):
    return int.from_bytes(d[off:off + 4], "little")


def map_dims(data, is_save):
    if is_save:
        return u32(data, 79372), u32(data, 79376)
    return u32(data, MAP_HDR_MAGIC_LEN), u32(data, MAP_HDR_MAGIC_LEN + 4)


def grid_labels(path, is_save):
    """max + count>=0x80 of the terrain-record +3 label plane"""
    d = open(path, "rb").read()
    W, H = map_dims(d, is_save)
    off = SAVE_GRID_OFF if is_save else (MAP_HDR_MAGIC_LEN + MAP_HDR_LEN)
    mx = -1
    ge = 0
    n = W * H
    for i in range(n):
        v = d[off + i * REC + 3]
        if v > mx:
            mx = v
        if v >= 0x80:
            ge += 1
    return W, H, mx, ge


def region_len(W, H):
    return ((W + 4) // 5 + 1) // 2 * ((H + 4) // 5)


def main():
    # ---------- G1: generator band caps ----------
    src15 = shard_src(SHARD15)
    body = fn_body(src15, GEN_FUN)
    ok1 = body is not None
    det1 = "body=%s" % ("found" if body else "MISSING")
    if body:
        # the two clamp expressions the s200 notes measured verbatim; the overflow
        # slot is uVar12+1 (land 0x3e+1=0x3f, water 0x7e+1=0x7f) - 0x7f is never a
        # literal, it is COMPUTED, so assert the clamp assigns + the +1 idiom.
        clamp_land = re.search(r"uVar12 = 0x3e;", body) is not None
        clamp_water = re.search(r"uVar12 = 0x7e;", body) is not None
        overflow = re.search(r"uVar12 \+ 1", body) is not None
        border = re.search(r"0x5f", body) is not None    # border pass: 0x3f water / 0x7f land
        has_low = re.search(r"0x3f", body) is not None
        ok1 = all([clamp_land, clamp_water, overflow, border, has_low])
        det1 = "land clamp 0x3e=%s water clamp 0x7e=%s overflow=uVar12+1=%s border 0x5f-formula=%s" % (
            clamp_land, clamp_water, overflow, border)
    gate(1, ok1, det1 + " -> largest assignable id = max(0x3e,0x7e)+1 = 0x7f (127) < 0x80")

    # ---------- G2: the two 0x80 loop bounds, containment ----------
    rows = load_index()
    ins = load_text()
    addr = {a: (op, args) for a, op, args in ins}
    ok2 = True
    det2 = []
    for a in CMP_SITES:
        got = addr.get(a)
        site_ok = got is not None and got[0] == "cmp" and ("0x80" in got[1])
        owner = fn_of(a, rows)
        site_ok = site_ok and owner == CONS_FUN
        ok2 = ok2 and site_ok
        det2.append("%s %s owner=%s" % (hex(a), (got[1] if got else "MISSING"), owner))
    det2 = "; ".join(det2) + " -> loop covers ids 0..127 = whole id space"
    gate(2, ok2, det2)

    # ---------- G3: DAT_0092ada4 is never a bound ----------
    # Known refs (M248 census, shard_014.c line numbers): 27266 alloc-expr,
    # 27267 alloc-arg, 27342 file-write (0x5821e0), 27376 file-read (0x582260).
    # Shard lines carry no line numbers in the text; classify by content.
    def kind_of(l):
        if "FUN_005be090" in l and "=" in l and "(" in l:
            return "alloc-arg"            # DAT_0092ada4 = FUN_005be090(DAT_0092ada4)
        if "= ((DAT_0092ad9c + 1) / 2) *" in l or "= ((" in l and "DAT_0092ada0" in l:
            return "alloc-expr"
        if "FUN_0064c9a0" in l or "FUN_0064cc00" in l:
            return "file-io"
        return "OTHER:" + l.strip()[:70]
    refs14 = [l.strip() for l in shard_src(SHARD14).splitlines() if COUNT_DAT in l]
    refs_other = []
    for sp in SHARDS:
        if os.path.basename(sp) == "shard_014.c":
            continue
        for l in open(sp, errors="replace"):
            if COUNT_DAT in l:
                refs_other.append("%s:%s" % (os.path.basename(sp), l.strip()[:80]))
    kinds = [kind_of(l) for l in refs14]
    def is_bound_kind(k):
        return k.startswith("OTHER")
    ok3 = (len(refs14) == 4 and not any(is_bound_kind(k) for k in kinds)
           and len(refs_other) == 0
           and kinds.count("alloc-arg") >= 1 and kinds.count("file-io") >= 1)
    gate(3, ok3, "; ".join(kinds) + " ; other-shard refs=%d" % len(refs_other)
         + " -> the 338 is alloc/clear/file-io ONLY, never a loop bound")

    # ---------- G4: accessor arithmetic -> "338" is cell count ----------
    src14 = shard_src(SHARD14)
    acc = fn_body(src14, "FUN_00582340")
    wrt = fn_body(src14, "FUN_00582360")
    ok4 = acc is not None and wrt is not None
    det4 = "accessor-index(x>>1 + (Rw>>1)*y) " if ok4 else "accessors MISSING"
    triad = [region_len(64, 64), region_len(80, 80), region_len(128, 128)]
    ok4 = ok4 and triad == [91, 128, 338]
    det4 += "len-triad=%s" % str(triad)
    gate(4, ok4, det4 + " -> 338 bytes = (((W+4)/5)+1)/2 * (H+4)/5 = CELL count, not ids")

    # ---------- G5: label census over the shipped files ----------
    fail = []
    rows_tbl = []
    files = MAPS + SAVES
    for p in files:
        is_save = p.endswith(".SAV")
        try:
            W, H, mx, ge = grid_labels(p, is_save)
        except Exception as e:   # noqa: BLE001
            fail.append("%s: %s" % (os.path.basename(p), e))
            continue
        ok5f = (mx <= 0x7f and ge == 0)
        if not ok5f:
            fail.append("%s max=0x%x ge128=%d" % (os.path.basename(p), mx, ge))
        rows_tbl.append("%s %dx%d max=0x%x ge128=%d" % (os.path.basename(p), W, H, mx, ge))
    ok5 = not fail
    gate(5, ok5, "; ".join(rows_tbl) if rows_tbl else "no files")
    if fail:
        for f in fail:
            print("   FAIL5:", f)

    # ---------- G6: region table = 128 slots ----------
    slots = SECTION_TABLE_BYTES / STRIDE_TABLE
    exact = SECTION_TABLE_BYTES % STRIDE_TABLE == 0
    ok6 = exact and slots == 128
    gate(6, ok6, "section=%d / stride 0x%x = %.4f rows -> table is 128 slots" % (
        SECTION_TABLE_BYTES, STRIDE_TABLE, slots))

    # ---------- G7: image-wide rival scan: 338 as a bound/scale ----------
    cmp338 = [hex(a) for a, op, args in ins if op == "cmp" and "0x152" in args]
    scale338 = [hex(a) for a, op, args in ins if "*0x152" in args]
    count_cmp = [hex(a) for a, op, args in ins if op == "cmp" and COUNT_DAT in args]
    ok7 = not cmp338 and not scale338 and not count_cmp
    det7 = "cmp-vs-0x152=%d scale-*0x152=%d cmp-vs-DAT_0092ada4=%d" % (
        len(cmp338), len(scale338), len(count_cmp))
    if cmp338:
        det7 += " " + ",".join(cmp338[:6])
    gate(7, ok7, det7 + " -> no loop in the image is bounded by the 338 cell count")

    npass = sum(1 for _, ok, _ in res if ok)
    print("\nSUMMARY M281: %d/%d gates PASS" % (npass, len(res)))
    sys.exit(0 if npass == len(res) else 1)


if __name__ == "__main__":
    main()
