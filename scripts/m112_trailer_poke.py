#!/usr/bin/env python3
"""M112 — is the last 156 B of a .SAV (the fixed trailer) CONSUMED on load? Poke, load, scan memory.

Why a poke and not a census: two census runs on two different saves over-ran their own file (+468 on
m54b_clean, +144 on an autosave) with no repeated (site,dest,size) group, so the size*count sum is not a
statement about the file, and the final read group's destination is a shared 4096-B CRT stdio buffer that
later reads overwrite. Identification has no such failure mode:

  * pattern reaches memory            -> the loader CONSUMED the trailer
  * pattern absent, load reaches HUD  -> the loader does NOT consume the trailer
  * the load is REFUSED               -> the trailer is VALIDATED (also conclusive)

    python3 scripts/m112_trailer_poke.py --tag m112p1 --relaunch

Pokes 0xCAFEBABE into the two zero dwords of each of the 5 trailer rows
(`[id,0,0,-6,32,32]` for id 3..7), leaving the row ids, the sentinels, the `[1,1,0x80000080,-14,32,32]` row
and the final (possibly checksum) dword untouched.
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

MAGIC = 0xCAFEBABE
TRAILER = 156
COUNT_U, COUNT_B = 0x985af0, 0x985af4


def build_poked(src, dst):
    data = bytearray(open(src, "rb").read())
    off = len(data) - TRAILER
    poked = []
    for row in range(5):                      # rows [id,0,0,-6,32,32]
        for field in (1, 2):                  # the two zeros at +4 and +8
            p = off + row * 24 + field * 4
            struct.pack_into("<I", data, p, MAGIC)
            poked.append(p)
    open(dst, "wb").write(bytes(data))
    return poked, len(data)


def counts(pid):
    fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
    try:
        return (struct.unpack("<I", os.pread(fd, 4, COUNT_U))[0],
                struct.unpack("<I", os.pread(fd, 4, COUNT_B))[0])
    finally:
        os.close(fd)


def scan(pid, needle):
    hits, scanned = [], 0
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
            i = buf.find(needle)
            while i != -1:
                hits.append(lo + i)
                i = buf.find(needle, i + 1)
    finally:
        os.close(fd)
    return hits, scanned


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="m112p1")
    ap.add_argument("--save", default="m54b_clean.SAV")
    ap.add_argument("--poked", default="m112poke.SAV")
    ap.add_argument("--relaunch", action="store_true")
    a = ap.parse_args()

    src = os.path.join(ROOT, "programs/saves", a.save)
    dst = os.path.join(ROOT, "programs/saves", a.poked)
    poked, size = build_poked(src, dst)
    print("poked %d dwords of 0x%08x into %s (file %d B, trailer at %d)"
          % (len(poked), MAGIC, a.poked, size, size - TRAILER), flush=True)

    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "m54a_load.py")]
                       + (["--relaunch"] if a.relaunch else []),
                       capture_output=True, text=True,
                       env=dict(os.environ,
                                SMAC_SAVE="Z:\\home\\n100\\reverse\\smac\\programs\\saves\\" + a.poked))
    for ln in (r.stdout or "").strip().splitlines()[-3:]:
        print("  load: " + ln[:120], flush=True)
    print("load rc=%d" % r.returncode, flush=True)

    pid = M.find_pid()
    nu, nb = counts(pid)
    hits, scanned = scan(pid, struct.pack("<I", MAGIC))
    lines = ["M112 trailer poke — %s -> %s, %d dwords of 0x%08x at trailer words 1,2 of rows 0..4" %
             (a.save, a.poked, len(poked), MAGIC),
             "  load rc=%d  counts %d/%d (m54b_clean = 67/18)  scanned %.1f MB" %
             (r.returncode, nu, nb, scanned / 1e6),
             "  MAGIC hits in memory: %d%s" % (len(hits), "" if not hits else
                                               "  at " + ", ".join("0x%x" % h for h in hits[:8]))]
    if r.returncode != 0:
        verdict = ("REFUSED/PARTIAL: the load did not reach a live HUD (rc=%d, counts %d/%d) — a poke in the "
                   "trailer changes the load outcome, so the trailer IS consumed (validated)" % (r.returncode, nu, nb))
    elif hits:
        verdict = ("CONSUMED: the load reached the HUD AND %d poked dwords are in memory — the loader reads "
                   "the 156-B trailer" % len(hits))
    else:
        verdict = ("NOT CONSUMED: the load reached a live HUD (counts %d/%d) with ZERO copies of the poked "
                   "pattern in %.1f MB of memory — the trailer is never loaded" % (nu, nb, scanned / 1e6))
    lines.append("  VERDICT " + verdict)
    out = "\n".join(lines)
    print(out, flush=True)
    with open(os.path.join(ROOT, "evidence", a.tag + ".log"), "w") as f:
        f.write(out + "\n")
    return 0 if (r.returncode == 0 and not hits) or (r.returncode != 0) or hits else 2


if __name__ == "__main__":
    sys.exit(main())
