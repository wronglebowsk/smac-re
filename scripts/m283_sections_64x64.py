#!/usr/bin/env python3
"""M283 (s227): decode_save --sections walks 64x64 saves.

The MAP branch hardcoded the 80x80 coarse-region-map length (128 B). The region map
is ((W+4)/5 + 1)/2 * (H+4)/5 bytes (shard_014.c:27263-27265, sim/save.py region_len):
128 for 80x80, 91 for 64x64, 338 for 128x128. With 128 hardcoded, a 64x64 save's
count u32 was read 37 bytes early (garbage -> c=67108869) and the record region
solved to 0 B -> "no 52/304 split of a 0-byte region", rc=1 on every 64x64 save.

Gates: every programs/saves/**/*.SAV walks with the dims-derived region length,
the section table sums to the file size, the count u32 sits at the sim-verified
188,299 on all 17 64x64 saves, and 80x80/128x128 dims map to 128/338.
"""
import contextlib
import glob
import io
import struct
import sys
from os.path import basename, dirname

REPO = dirname(dirname(__file__))

def region_len(w, h):
    return (((w + 4) // 5 + 1) // 2) * ((h + 4) // 5)

def main():
    sys.path.insert(0, REPO + "/scripts")
    import decode_save
    saves = sorted(glob.glob(REPO + "/programs/saves/**/*.SAV", recursive=True))
    assert saves, "no saves found"
    res, n64 = [], 0
    for p in saves:
        d = open(p, "rb").read()
        w, h = struct.unpack_from("<II", d, decode_save.DIMS_OFF)
        rl = region_len(w, h)
        if min(w, h) == 64:
            n64 += 1
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rows, notes = decode_save.walk(d)
        except SystemExit as exc:
            res.append((False, "%s: walk raised %s" % (basename(p), exc)))
            continue
        total = sum(sz for _, sz, _, _ in rows) + 12
        row_region = [sz for _, sz, lab, _ in rows if lab == "coarse region map"]
        fatal = [n for n in notes if n.startswith("walk ended")]
        ok = (total == len(d) and row_region == [rl] and not fatal
              and next((sz for _, sz, lab, _ in rows if lab == "map grid (W*H*22)"),
                       None) == w * h * 22)
        res.append((ok, "%s %dx%d region=%d sum=%d%s" % (basename(p), w, h, rl, total,
                   " [%d notes]" % len(notes) if notes else "")))
    n_total = len(res)
    n_pass = sum(ok for ok, _ in res)
    # count u32 position: sim/save.py claims the count u32 sits at 188,299 on all
    # 17 64x64 saves; the walk's own table must carry it there (value is save-dependent).
    cnt_ok, cnt_bad = 0, []
    for p in saves:
        d = open(p, "rb").read()
        w, h = struct.unpack_from("<II", d, decode_save.DIMS_OFF)
        if min(w, h) != 64:
            continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rows, _ = decode_save.walk(d)
        pos = next((off for off, sz, lab, _ in rows if lab == "u32 count prefix"), None)
        if pos == 188299:
            cnt_ok += 1
        else:
            cnt_bad.append("%s:%s" % (basename(p), pos))
    formula = {80: 128, 128: 338}
    f_ok = all(region_len(k, k) == v for k, v in formula.items())
    print("M283: decode_save --sections on 64x64 saves")
    for ok, row in res:
        print("   %s %s" % ("PASS" if ok else "FAIL", row))
    print("   count u32 @188,299 in the walk table: %d/17%s" % (cnt_ok,
          (" BAD: " + ", ".join(cnt_bad)) if cnt_bad else ""))
    print("   region_len formula 80x80->128, 128x128->338: %s" % ("PASS" if f_ok else "FAIL"))
    print("SUMMARY M283: %d/%d section gates, count %d/17, formula %s"
          % (n_pass, n_total, cnt_ok, f_ok))
    return 0 if (n_pass == n_total and cnt_ok == 17 and f_ok) else 1

if __name__ == "__main__":
    sys.exit(main())
