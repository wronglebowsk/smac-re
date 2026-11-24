#!/usr/bin/env python3
"""M374 mutation harness - every VERIFIED row names the mutant that reddens it.

Levers: M374_PATCH='addr|new text' (rewrites one instruction line in memory),
M374_ALGO=n (flips a law), M374_SCRIPT=<path> (a mutated Script.txt copy).
G0 is the evidence-file anchor gate (dump sha1 + instruction bytes) and is a
declared NO-OP under text levers.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m374_semaphore_bits.py")
BASE = os.path.join(ROOT, "programs/Script.txt")

MUT = [
    ("MU1", "code", "0x4dc892|or     ecx,0x400000", "G1,G5"),
    ("MU2", "code", "0x4dc89e|test   eax,0x40000", "G1"),
    ("MU3", "code", "0x4dc8b7|and    ecx,0x1800001", "G1"),
    ("MU4", "code", "0x4dc6cf|test   edx,0x1000000", "G1"),
    ("MU5", "code", "0x4dc604|and    edx,0xffffffff", "G2"),
    ("MU6", "script", "", "G3"),
    ("MU7", "code", "0x59ef11|test   eax,0x1000000", "G4"),
    ("MU8", "code", "0x59eedc|mov    eax,ds:0x985ac4", "G4"),
    ("MU9", "code", "0x5a1150|test   DWORD PTR ds:0x985ae8,0x800000", "G4"),
    ("MU10", "code", "0x5a1160|mov    ecx,0x10", "G4"),
    ("MU11", "code", "0x4dc8c3|mov    DWORD PTR ds:0x92bf08,ecx", "G1"),
    ("MU12", "code", "0x4dc786|mov    eax,ds:0x99aa3c", "G5"),
    ("ALGO1", "algo", "1", "G3"),
    ("ALGO2", "algo", "2", "G2"),
]


def run(env):
    e = dict(os.environ)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", SCRIPT], env=e,
                       capture_output=True, text=True)
    red = sorted(set(re.findall(r"^\s+(G\d)\s+FAIL", p.stdout, re.M)))
    return p.returncode, red


def main():
    rc, red = run({})
    print("base rc=%d red=%s" % (rc, red))
    ok = rc == 0 and not red
    tmpd = tempfile.mkdtemp()
    killed = 0
    covered = set()
    for mu, kind, payload, gates in MUT:
        env = {}
        if kind == "code":
            env["M374_PATCH"] = payload
        elif kind == "algo":
            env["M374_ALGO"] = payload
        else:
            dst = os.path.join(tmpd, "Script.txt")
            lines = open(BASE, "r", errors="replace").read().splitlines()
            i = lines.index("#RULES")
            j = lines.index("#itemlist", i)
            lines[j + 17] = "Randomize faction leader widgets."
            open(dst, "w").write("\n".join(lines))
            env["M374_SCRIPT"] = dst
        rc2, red2 = run(env)
        good = rc2 != 0 and bool(red2)
        print("%-6s %-34s expect=%-6s rc=%d red=%-10s %s" %
              (mu, payload[:34], gates, rc2, ",".join(red2) or "-",
               "KILLED" if good else "SURVIVED"))
        ok &= good
        if good:
            killed += 1
            covered |= set(red2)
    shutil.rmtree(tmpd, ignore_errors=True)
    cov = {"G1", "G2", "G3", "G4", "G5"} <= covered
    print()
    print("HARNESS %s %d/%d killed, cov=%s, 1 declared NO-OP (G0 anchors)" %
          ("PASS" if ok and cov else "FAIL", killed, len(MUT), cov))
    sys.exit(0 if ok and cov else 1)


if __name__ == "__main__":
    main()
