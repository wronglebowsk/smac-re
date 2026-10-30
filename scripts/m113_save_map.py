#!/usr/bin/env python3
"""M113 — extract the .SAV offset -> memory map by POKING markers and finding where they land.

Why this instrument: the read census over-runs its own file (+468, +144) so its cumulative `file_off` column is
not a statement about the file, and a subset-sum over the candidate legs is underdetermined (181,769 exact
decompositions of m54b_clean's 242,539 B). Identification does not have either failure mode: a 4-byte marker
written at a known FILE OFFSET and later found at a known DESTINATION is one exact (offset -> address) anchor.

    python3 scripts/m113_save_map.py --tag m113map1 --relaunch

Plants 0xC0DE000i markers every --step bytes (default 8,192) plus at each supplied --boundary, loads the copy,
and prints every anchor found, sorted by file offset. Anchors chain into the layout: two consecutive anchors
bracket a section, and a marker that is MISSING marks an offset the loader never consumes.
"""
import argparse
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import m55_boundary as M

BASE_MARK = 0xC0DE0000
# candidate section starts from the leg list (sizes from the push immediates in FUN_00596850)
CANDS = [796 + 4 + 67040 + 11488 + 32 + 2724 + 90112 + 91,   # first section after the 64x64 map
         172291 + 16000, 172291 + 16000 + 176, 172291 + 16000 + 176 + 3584,
         172291 + 16000 + 176 + 3584 + 26624, 172291 + 16000 + 176 + 3584 + 26624 + 4096]
COUNT_U, COUNT_B = 0x985af0, 0x985af4


def build(src, dst, step, extra, bands=()):
    """bands: (lo, hi, step) triples — mark only inside them, so a refinement run does not scatter
    100+ pokes through fields the loader parses (a poke in a count or pointer can abort the load)."""
    data = bytearray(open(src, "rb").read())
    size = len(data)
    offs = set()
    if not bands:
        o = step
        while o < size - TRAILER_GUARD:
            offs.add(o - (o % 4))
            o += step
    for lo, hi, st in bands:
        o = lo
        while o < min(hi, size - TRAILER_GUARD):
            offs.add(o - (o % 4))
            o += st
    for b in extra:
        if 16 <= b < size - TRAILER_GUARD:
            offs.add(b)
    if len(offs) > 60:
        raise SystemExit("refusing %d markers — narrow the bands (a load with 60+ pokes is not a map, it is a mutilation)" % len(offs))
    marks = {}
    for i, off in enumerate(sorted(offs)):
        val = BASE_MARK | (i + 1)
        struct.pack_into("<I", data, off, val)
        marks[off] = val
    open(dst, "wb").write(bytes(data))
    return marks, size


TRAILER_GUARD = 200   # keep the last 156-B trailer + 44 B untouched


def counts(pid):
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        return (struct.unpack("<I", os.pread(fd, 4, COUNT_U))[0],
                struct.unpack("<I", os.pread(fd, 4, COUNT_B))[0])
    finally:
        os.close(fd)


def scan_all(pid, wanted):
    """One pass over readable memory; return {value: [addresses]}."""
    found = {v: [] for v in wanted}
    scanned = 0
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        for line in open("/proc/%d/maps" % pid):
            m = re.match(r"([0-9a-f]+)-([0-9a-f]+) (\S{4})", line)
            if not m or "r" not in m.group(3):
                continue
            lo, hi = int(m.group(1), 16), int(m.group(2), 16)
            if hi - lo <= 0 or hi - lo > 512 * 1024 * 1024:
                continue
            try:
                buf = os.pread(fd, hi - lo, lo)
            except OSError:
                continue
            scanned += len(buf)
            for v in wanted:
                pos = buf.find(struct.pack("<I", v))
                while pos != -1:
                    found[v].append(lo + pos)
                    pos = buf.find(struct.pack("<I", v), pos + 1)
    finally:
        os.close(fd)
    return found, scanned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m113map1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--poked", default="m113map.SAV")
    ap.add_argument("--step", type=int, default=8192)
    ap.add_argument("--boundary", action="append", type=int, default=None)
    ap.add_argument("--band", action="append", default=None,
                    help="lo-hi[:step] band to refine inside (decimal or 0x hex); repeatable")
    ap.add_argument("--relaunch", action="store_true")
    a = ap.parse_args()

    src = os.path.join(ROOT, "programs/saves", a.save)
    dst = os.path.join(ROOT, "programs/saves", a.poked)
    bands = []
    for spec in (a.band or []):
        rng, _, st = spec.partition(":")
        lo, _, hi = rng.partition("-")
        bands.append((int(lo, 0), int(hi, 0), int(st, 0) if st else a.step))
    marks, size = build(src, dst, a.step, (a.boundary or []) + ([] if bands else CANDS), bands)
    print("planted %d markers (step %d) in %s, file %d B" % (len(marks), a.step, a.poked, size), flush=True)

    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py")]
                       + (["--relaunch"] if a.relaunch else []),
                       capture_output=True, text=True,
                       env=dict(os.environ,
                                SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\" + a.poked))
    for ln in (r.stdout or "").strip().splitlines()[-2:]:
        print("  load: " + ln[:110], flush=True)
    print("load rc=%d" % r.returncode, flush=True)

    pid = M.find_pid()
    nu, nb = counts(pid)
    found, scanned = scan_all(pid, set(marks.values()))
    lines = ["M113 .SAV map by poke — %s -> %s, %d markers of 0x%08x|x, step %d" %
             (a.save, a.poked, len(marks), BASE_MARK, a.step),
             "  load rc=%d  counts %d/%d (m54b_clean = 67/18)  scanned %.1f MB" %
             (r.returncode, nu, nb, scanned / 1e6),
             "  file_offset   marker       destinations",
             "  -----------   ----------   ------------"]
    hit_off = missing = 0
    for off in sorted(marks):
        v = marks[off]
        hits = found[v]
        if hits:
            hit_off += 1
            lines.append("  %11d   0x%08x   %s" % (off, v, " ".join("0x%x" % h for h in hits[:4])))
        else:
            missing += 1
            lines.append("  %11d   0x%08x   (absent)" % (off, v))
    verdict = ("%d/%d marker offsets found in memory; %d absent%s" %
               (hit_off, len(marks), missing,
                "" if not missing else " — absent offsets are file regions the loader never restores"))
    lines.append("  VERDICT " + verdict)
    out = "\n".join(lines)
    print(out, flush=True)
    with open(os.path.join(ROOT, "evidence", a.tag + ".log"), "w") as f:
        f.write(out + "\n")
    # m54a_load.py: 0 = HUD reached AND live, 4 = HUD reached but its liveness check failed. A poke map is
    # decided by the anchors and the counts, not by that liveness probe (m113map3: rc=4 with counts 67/18 and
    # 19/20 anchors was a good run that the old exit code reported as a failure). Only a load that did NOT
    # reach the HUD (1 timeout, 3 no window) is a harness failure.
    if r.returncode in (0, 4):
        return 0
    return 6


if __name__ == "__main__":
    sys.exit(main())
