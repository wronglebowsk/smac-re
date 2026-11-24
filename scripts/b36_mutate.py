#!/usr/bin/env python3
"""B36 mutant harness (review_lint law: every V row in NAMED ## B36 names its mutant).

Re-creates each defect in a COPY of sim/relations.py (one anchor -> replacement, installed as
sim/_b36_mut_<id>.py so the relative imports still resolve) and runs it against the same dump.
A mutant must redden EXACTLY its declared gate set; the identity (NO-OP) mutant must redden
nothing - that is what proves the comparison bites.  An anchor that does not occur exactly once
is a harness error, not a pass.

  python3 -u scripts/b36_mutate.py             # full run (11 mutants)
  python3 -u scripts/b36_mutate.py --selftest  # machinery only

Zero box, zero /proc, zero gdb.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sim", "relations.py")
SIM = os.path.dirname(SRC)
GATE_RE = re.compile(r"^(ok|BAD)\s+(G\d+)\b")

MUTANTS = [
    ("MU1", "len(win) == 161 and stores == 8", "len(win) == 161 and stores == 9", ["G0"],
     "the store count unpinned: a changed writer body would still read as the same function"),
    ("MU2", "PEACE_CLEAR = 0xEE7FAF | 0xFF000000", "PEACE_CLEAR = 0xEE7FAF | 0xFF000040", ["G1", "G2"],
     "0x40 folded into the peace clear mask: the AND would stop clearing it"),
    ("MU3", "            wba &= PEACE_CLEAR", "            wba &= 0xFFFFFFFF", ["G2", "G4", "G5"],
     "the peace pre-clear applied to one direction only: the pair goes asymmetric"),
    ("MU4", "(0, PACT | AT_WAR, 0x8000011B)]:", "(0, PACT | AT_WAR, 0x8000011A)]:", ["G3"],
     "the one-call combined-mask word unpinned: a dropped commlink would slide by"),
    ("MU5", "            if kind == \"mask_or\":\n                ebx |= imm",
            "            if kind == \"mask_or\":\n                ebx |= 0", ["G2", "G3", "G4"],
     "the pact=>treaty upgrade dropped from the program: sim and dump disagree on every pact"),
    ("MU6", "        wba |= eff\n", "        wba |= eff & ~TREATY\n", ["G2", "G4", "G5"],
     "the OR applied to one direction only: symmetry dies"),
    ("MU7", "        for bit in LADDER:\n            if cl & bit:", "        for bit in (TRUCE, TREATY, PACT):\n            if cl & bit:",
     ["G6"], "the classifier precedence reversed: the dump chain says 1 then 2 then 4"),
    ("MU8", 'POSTER = {TRUCE: "ENEMYTRUCE", TREATY: "ENEMYTREATY", PACT: None}',
            'POSTER = {TRUCE: "ENEMYTREATY", TREATY: "ENEMYTRUCE", PACT: None}', ["G7"],
     "the two poster keys swapped: the action layer would name the wrong state"),
    ("MU9", "        if kind == \"war_plain\":\n            return w0 | eff, w0 | eff",
            "        if kind == \"war_plain\":\n            return run_program(prog, w0, w0, m)[:2]", ["G8"],
     "a rival made equal to the truth: the rival sweep stops falsifying anything"),
    ("MU10", 'ANCHOR = "b20f5818dee2d861"', 'ANCHOR = "0000000000000000"', ["G9"],
     "the window digest unpinned: a dump drift would slip past"),
    ("MU11", "        if t not in starts and t <= win[-1][0]:", "        if False:",
     ["G1", "G2", "G3", "G4"], "tail detection disabled: the unconditional OR is gated on 0x17 "
     "and contact becomes a no-op"),
    ("MU12", 'elif mn == "and" and re.match(r"^edx,0x[0-9a-f]+$", ops):',
             'elif mn == "and" and re.match(r"^edx,0x[0-9a-f]+$", ops) and a < 0x551B50:',
     ["G0", "G1", "G2"], "the extractor's clear window truncated: the 0x800000 clear disappears "
     "from the pinned op table and the store count no longer equals the stored ops"),
    ("MU13", "len(cwin) == 16 and len(tests) == 3", "len(cwin) == 17 and len(tests) == 3", ["G6"],
     "the classifier window unpinned: a wider chain would still pass"),
    ("NOOP", 'ANCHOR = "b20f5818dee2d861"', 'ANCHOR = "b20f5818dee2d861"', [],
     "identity: nothing may redden"),
]


def run_one(mid, anchor, repl):
    src = open(SRC).read()
    n = src.count(anchor)
    if n != 1:
        return None, "ANCHOR appears %d times (want 1)" % n, ""
    path = os.path.join(SIM, "_b36_mut_%s.py" % mid)
    with open(path, "w") as fh:
        fh.write(src.replace(anchor, repl))
    try:
        r = subprocess.run([sys.executable, "-u", "-m", "sim._b36_mut_%s" % mid],
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
        red, err, _ = run_one("SELF", "PEACE_CLEAR = 0xEE7FAF | 0xFF000000",
                              "PEACE_CLEAR = 0xEE7FAF | 0xFF000040")
        print("SELFTEST: anchor machinery %s, red = %s"
              % ("OK" if red is not None and not err else "FAIL", red))
        return 0 if red == ["G1", "G2"] else 1
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
