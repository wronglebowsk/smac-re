#!/usr/bin/env python3
"""M244 support: map the codec's four tail legs to file offsets by CONTENT.

Reads each leg's destination block out of /proc/<pid>/mem (sudo: yama ptrace_scope=1) and
searches the save for 16-byte windows taken from inside it. A window found at one offset
proves the leg's file span, because the restore is 1:1 inside a block (M114).

Usage: sudo -n python3 scripts/m244_tail_legmap.py [save]
"""
import os
import struct
import subprocess
import sys

SAVE = sys.argv[1] if len(sys.argv) > 1 else "programs/saves/auto/m242_probe_B.SAV"
LEGS = [("DAT_00991598", 0x991598, 256), ("DAT_00991698", 0x991698, 256),
        ("DAT_0092bf58", 0x92bf58, 152), ("DAT_0092d4a0", 0x92d4a0, 10144)]
pids = subprocess.run(["pgrep", "-f", "terran.exe"], capture_output=True, text=True).stdout.split()
pid = max((int(p) for p in pids), default=0)
tracer = open("/proc/%d/status" % pid).read()
tracer = [l for l in tracer.splitlines() if l.startswith("TracerPid")][0]
data = open(SAVE, "rb").read()
print("pid=%d %s  file=%s size=%d" % (pid, tracer, SAVE, len(data)))
fd = os.open("/proc/%d/mem" % pid, os.O_RDONLY)
for name, addr, size in LEGS:
    blob = os.pread(fd, size, addr)
    zeros = blob.count(0) == len(blob)
    print("== %s @%#x len %d  head=%s  all-zero=%s" % (name, addr, size, blob[:16].hex(), zeros))
    for probe in sorted({0, size // 4, size // 2, 3 * size // 4, max(0, size - 16)}):
        win = blob[probe:probe + 16]
        if win.count(0) == 16:
            print("   probe +%6d  (all-zero window, not identifying)" % probe)
            continue
        hits, j = [], 0
        while len(hits) < 4:
            j = data.find(win, j)
            if j < 0:
                break
            hits.append(j)
            j += 1
        k = [h - probe for h in hits]
        print("   probe +%6d hits=%s  implied dest-file k=%s" % (probe, hits, k))
print("== the 152-B leg's file start is the unique 9999-row; the 10,144-B leg's start is")
print("   dest-file k from its non-zero windows; the tail legs then sum 256+152+10144+20+216+8+4")
print("   = 10,800 = EOF - bases_end.")
