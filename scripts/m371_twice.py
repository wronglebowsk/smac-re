#!/usr/bin/env python3
"""M371 twice-run assertion: the acceptance output must be byte-identical on a second run.

    python3 scripts/m371_twice.py        # runs scripts/m371_war_contact.py twice, diffs stdout
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "scripts/m371_war_contact.py")


def run():
    p = subprocess.run([sys.executable, "-u", TOOL], capture_output=True, text=True)
    return p.stdout, p.returncode


a, ra = run()
b, rb = run()
ha, hb = hashlib.sha256(a.encode()).hexdigest(), hashlib.sha256(b.encode()).hexdigest()
line = next((l for l in a.splitlines() if l.startswith("PASS M371") or l.startswith("FAIL M371")), "?")
print("run1 rc=%d sha256=%s" % (ra, ha[:16]))
print("run2 rc=%d sha256=%s" % (rb, hb[:16]))
print("stdout identical: %s" % (a == b))
if a == b and ra == 0 and rb == 0 and "PASS M371" in a:
    print("PASS M371-TWICE: byte-identical (%s)" % line)
    sys.exit(0)
print("FAIL M371-TWICE")
sys.exit(1)
