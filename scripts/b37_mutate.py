#!/usr/bin/env python3
"""B37 mutant harness (review_lint law: every V row in NAMED ## B37 names its mutant).

Re-creates each defect in a COPY of sim/treaty.py (one anchor -> replacement, installed as
sim/_b37_mut_<id>.py so `-m` resolution still works) and runs it against the same dump.  A mutant
must redden EXACTLY its declared gate set; the identity (NO-OP) mutant must redden nothing - that
is what proves the comparison bites.  An anchor that does not occur exactly once is a harness
error, not a pass.

  python3 -u scripts/b37_mutate.py             # full run (13 mutants)
  python3 -u scripts/b37_mutate.py --selftest  # machinery only

Zero box, zero /proc, zero gdb.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sim", "treaty.py")
SIM = os.path.dirname(SRC)
GATE_RE = re.compile(r"^(ok|BAD)\s+(G\d+)\b")

MUTANTS = [
    ("MU1", "TICK_LO, TICK_HI = 0x5552B6, 0x5552D4", "TICK_LO, TICK_HI = 0x5552B6, 0x5552C4", ["G0", "G2", "G4", "G7"],
     "the window truncated before the word store: a dump drift that dropped the expiry would read as the block"),
    ("MU2", "TICK_LO, TICK_HI = 0x5552B6, 0x5552D4", "TICK_LO, TICK_HI = 0x5552BC, 0x5552D4", ["G0", "G2", "G4", "G7"],
     "the window started after the cell load: the block still parses but no longer reads the cell"),
    ("MU3", 'if mn == "test" and op in ("cl,0x40", "dl,0x40", "al,0x40"):',
            'if False and mn == "test" and op in ("cl,0x40", "dl,0x40", "al,0x40"):', ["G1", "G7"],
     "the caller-mask guard unread: the 0x551d2a arm loses its 0x40 predecessor and G1 reddens"),
    ("MU4", '            return ("conditional" if g["ok"] else "unguarded", a, None, g)',
            '            return ("literal", a, 0x40, None)', ["G1", "G7"],
     "the caller-mask arm read as a literal: the arm table and its digest both shift"),
    ("MU5", "ARM_CELL_VALUE = 0x32", "ARM_CELL_VALUE = 0x31", ["G1", "G2", "G3", "G6", "G7"],
     "the lease is 49 ticks: expiry moves to 49 and the re-arm rival stops differing"),
    ("MU6", "        self.cell -= 1", "        self.cell -= 2", ["G2", "G3", "G4", "G7"],
     "the countdown runs two ticks per pass: parity and every expiry tick move"),
    ("MU7", "        if t == 30:\n            lc.arm(); ev = \"arm\"",
            "        if t == 31:\n            lc.arm(); ev = \"arm\"", ["G3", "G7"],
     "the transcript's re-arm moved a tick: t30/t79 checkpoints and the no-rearm rival move"),
    ("MU8", "and nul[0x2] == 49 and nul[0x10] == 0,", "and nul[0x2] == 49 and nul[0x10] == 49,",
     ["G4"], "the war asymmetry dropped from the gate: a war-cleared lease would pass as a null write"),
    ("MU9", 'SET_TREATY, TREATY_ON = 0x40, 0x800000', 'SET_TREATY, TREATY_ON = 0x40, 0x400000',
     ["G5"], "TREATY ON re-pointed one bit down: the 0x17 clears no longer reach it and G5 reddens"),
    ("MU10", "        r1 += int(run_seq(0, ARM_CELL_VALUE, 50, status_at=st, status_mask=0x2,",
             "        r1 += 0 * int(run_seq(0, ARM_CELL_VALUE, 50, status_at=st, status_mask=0x2,",
     ["G6"], "a rival made equal to the truth: the status-disarms the cell reading stops falsifying"),
    ("MU13", '"ok": mn2 in ("je", "jz") and tgt > arm_addr,', '"ok": False,', ["G1", "G7"],
     "the guard's direction inverted: the 0x551d2a arm reads as unguarded and G1 must redden"),
    ("MU11", 'ANCHOR = "5dd4119bd1882d1d"', 'ANCHOR = "0000000000000000"', ["G7"],
     "the block digest unpinned: a dump drift would slip past"),
    ("MU12", "        if lc.cell == 0 and expire_tick is None:", "        if False:", ["G2"],
     "the expiry-tick measurement removed: the gate can no longer say WHEN the lease ends"),
    ("NOOP", 'ANCHOR = "5dd4119bd1882d1d"', 'ANCHOR = "5dd4119bd1882d1d"', [],
     "identity: nothing may redden"),
]


def run_one(mid, anchor, repl):
    src = open(SRC).read()
    n = src.count(anchor)
    if n != 1:
        return None, "ANCHOR appears %d times (want 1)" % n, ""
    path = os.path.join(SIM, "_b37_mut_%s.py" % mid)
    with open(path, "w") as fh:
        fh.write(src.replace(anchor, repl))
    try:
        r = subprocess.run([sys.executable, "-u", "-m", "sim._b37_mut_%s" % mid],
                           cwd=ROOT, capture_output=True, text=True, timeout=300)
    finally:
        if os.path.exists(path):
            os.remove(path)
    red = sorted({m.group(2) for ln in r.stdout.splitlines()
                  for m in [GATE_RE.match(ln)] if m and m.group(1) == "BAD"})
    return red, "", r.stdout + r.stderr


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        red, err, _ = run_one("SELF", "ARM_CELL_VALUE = 0x32", "ARM_CELL_VALUE = 0x31")
        print("SELFTEST: anchor machinery %s, red = %s"
              % ("OK" if red is not None and not err else "FAIL", red))
        return 0 if red == ["G1", "G2", "G3", "G6", "G7"] else 1
    fails, noop = [], []
    for mid, anchor, repl, want, why in MUTANTS:
        red, err, out = run_one(mid, anchor, repl)
        if err:
            print("%-5s HARNESS-ERROR %s" % (mid, err))
            fails.append(mid)
            continue
        ok = red == sorted(want)
        print("%-5s %s red=%s want=%s  %s" % (mid, "ok  " if ok else "BAD ", red, sorted(want), why))
        if not ok:
            fails.append(mid)
            print("      tail: %s" % " | ".join(l for l in out.splitlines() if l.startswith("BAD"))[:400])
        if mid == "NOOP" and red:
            noop.append(red)
    print("")
    if fails:
        print("RUN FAIL %d/%d mutants misbehaved: %s" % (len(fails), len(MUTANTS), fails))
        return 1
    print("RUN PASS %d mutants, NO-OP %s" % (len(MUTANTS), noop))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
