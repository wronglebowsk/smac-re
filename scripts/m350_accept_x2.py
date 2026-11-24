#!/usr/bin/env python3
"""M350 — the "x2 identical" acceptance evidence, made into an instrument.

WHY: review #373 finding 4 caught that NAMED cited `x2` while the shipped
evidence held ONE run.  This script performs the second invocation and asserts
byte-equality of stdout, so the claim costs a printed number instead of a memory.

It does NOT re-implement any measurement: it shells the acceptance twice, hashes
what came back, and writes
  evidence/m350_pref_cowriters.txt  = invocation 1's stdout, verbatim
  evidence/m350_x2.txt              = both sha1s, the equality verdict, the
                                      RESULT lines and any diff
Exit 0 only when the two stdouts are byte-identical AND both carry the PASS line.
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCEPT = os.path.join(ROOT, "scripts", "m350_pref_cowriters.py")
EV1 = os.path.join(ROOT, "evidence", "m350_pref_cowriters.txt")
EV2 = os.path.join(ROOT, "evidence", "m350_x2.txt")
PASS = "RESULT: PASS M350: 6/6 gates"


def run():
    p = subprocess.run([sys.executable, "-u", ACCEPT], capture_output=True, text=True,
                       cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def main():
    rc1, a = run()
    rc2, b = run()
    ha = hashlib.sha1(a.encode()).hexdigest()
    hb = hashlib.sha1(b.encode()).hexdigest()
    la = [l for l in a.splitlines() if l.startswith("RESULT")]
    lb = [l for l in b.splitlines() if l.startswith("RESULT")]
    print("run1 rc=%d sha1=%s result=%s" % (rc1, ha, la[-1] if la else "-"))
    print("run2 rc=%d sha1=%s result=%s" % (rc2, hb, lb[-1] if lb else "-"))
    same = a == b
    print("stdout byte-identical: %s" % same)
    print("both carry `%s`: %s" % (PASS, PASS in la and PASS in lb))
    open(EV1, "w").write(a)
    with open(EV2, "w") as f:
        f.write("M350 x2 — two invocations of `python3 -u scripts/m350_pref_cowriters.py`\n")
        f.write("run1 rc=%d sha1=%s %s\n" % (rc1, ha, la[-1] if la else "-"))
        f.write("run2 rc=%d sha1=%s %s\n" % (rc2, hb, lb[-1] if lb else "-"))
        f.write("stdout byte-identical: %s ; diff lines: %d\n" % (
            same, sum(1 for x, y in zip(a.splitlines(), b.splitlines()) if x != y)
            + abs(len(a.splitlines()) - len(b.splitlines()))))
    print("evidence: %s (run 1), %s (verdict)" % (
        os.path.relpath(EV1, ROOT), os.path.relpath(EV2, ROOT)))
    good = same and PASS in la and PASS in lb and rc1 == 0 and rc2 == 0
    print("RESULT: %s" % ("PASS M350 x2" if good else "FAIL M350 x2"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
