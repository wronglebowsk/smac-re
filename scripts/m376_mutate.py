#!/usr/bin/env python3
"""M376 mutation harness - every VERIFIED row names the mutant that reddens it.

Levers: M376_PATCH='addr|new text' (rewrites one instruction line in memory),
M376_ALGO=n (flips a law), M376_ALPHA=<path> (a mutated alpha.txt copy).
G0 is the evidence anchor gate (dump sha1 + instruction bytes): declared NO-OP.

Declared gate sets are the gates a mutant MUST redden; the harness prints the
MEASURED set and refuses any mutant whose measured set misses its declaration.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m376_socio_grid.py")
BASE = os.path.join(ROOT, "programs/alpha.txt")

MUT = [
    # geometry (G1)
    ("MU1", "code", "0x5a11f3|lea    ecx,[edx+ecx*4+0x92bbc]", "G1"),
    ("MU2", "code", "0x5a11e3|lea    ecx,[ecx+ecx*7]", "G1"),
    ("MU3", "code", "0x5a11ea|lea    esi,[edx+edx*5]", "G1"),
    ("MU4", "code", "0x52b822|mov    ecx,0xa", "G1"),
    ("MU5", "code", "0x5a1203|cmp    eax,0xa", "G1"),
    ("MU6", "code", "0x57ab94|mov    ecx,0xc", "G1"),
    ("MU7", "code", "0x52b82c|add    eax,0x30", "G1"),
    ("MU8", "code", "0x52b84d|cmp    eax,0x2a0", "G1"),
    ("MU9", "code", "0x5a1193|idiv   ebx", "G1"),
    # signature (G2)
    ("MU10", "code", "0x57abe0|mov    esi,0x9270d8", "G2"),
    ("MU11", "code", "0x57abf8|sub    eax,ecx", "G2"),
    ("MU12", "algo", "1", "G2"),
    # consumer (G3)
    ("MU13", "code", "0x5a118e|mov    ecx,0x4", "G3"),
    ("MU14", "code", "0x5a119d|mov    ecx,0x2", "G3"),
    ("MU15", "code", "0x5a1160|mov    ecx,0xb", "G3"),
    ("MU16", "code", "0x5a11a7|lea    eax,[edx+esi*3]", "G3"),
    ("MU17", "code", "0x5a1213|cmp    ebx,0x7", "G3"),
    ("MU18", "code", "0x5a120d|add    edi,0x598", "G3"),
    ("MU19", "code", "0x5a1171|mov    edi,0x9280b0", "G3"),
    ("MU20", "code", "0x5a11fd|jge    0x5a120a", "G3"),
    ("MU21", "algo", "2", "G3"),
    # reader (G4)
    ("MU22", "code", "0x4a66d9|imul   eax,eax,0x2c", "G4"),
    ("MU23", "code", "0x4a66ff|mov    ecx,DWORD PTR [edx+eax*4+0x92ba98]", "G4"),
    ("MU24", "code", "0x4a667b|cmp    DWORD PTR [edx+eax*4+0x927b18],0x0", "G3"),
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
            env["M376_PATCH"] = payload
        elif kind == "algo":
            env["M376_ALGO"] = payload
        else:
            dst = os.path.join(tmpd, "alpha.txt")
            lines = open(BASE, "r", errors="replace").read().splitlines()
            i = lines.index("#SOCIO")
            lines[i + 5] = lines[i + 5].replace("++POLICE", "--POLICE")
            open(dst, "w").write("\n".join(lines) + "\n")
            env["M376_ALPHA"] = dst
        rc2, red2 = run(env)
        want = {g.strip() for g in gates.split(",")}
        good = rc2 != 0 and bool(red2) and want <= set(red2)
        print("%-5s %-52s expect=%-4s rc=%d red=%-10s %s" %
              (mu, payload[:52], gates, rc2, ",".join(red2) or "-",
               "KILLED" if good else "SURVIVED"))
        ok &= good
        if good:
            killed += 1
            covered |= set(red2)
    shutil.rmtree(tmpd, ignore_errors=True)
    cov = {"G1", "G2", "G3", "G4"} <= covered
    print()
    print("HARNESS %s %d/%d killed, cov=%s G1-G4, 1 declared NO-OP (G0 anchors)" %
          ("PASS" if ok and cov else "FAIL", killed, len(MUT), cov))
    sys.exit(0 if ok and cov else 1)


if __name__ == "__main__":
    main()
