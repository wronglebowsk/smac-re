#!/usr/bin/env python3
"""B38 mutant harness (review_lint law: every V row in NAMED ## B38 names its mutant).

Re-creates each defect in a COPY of sim/socio.py (one anchor -> replacement, installed as
sim/_b38_mut_<id>.py so `-m` resolution still works) and runs it against the same rules file and
dump.  A mutant must redden EXACTLY its declared gate set; the NOOP mutant must redden nothing -
that is what proves the comparison bites.  An anchor that does not occur exactly once is a
harness error, not a pass.

  python3 -u scripts/b38_mutate.py             # full run
  python3 -u scripts/b38_mutate.py --selftest  # machinery only

Zero box, zero /proc, zero gdb.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sim", "socio.py")
SIM = os.path.dirname(SRC)
GATE_RE = re.compile(r"^\s*(ok|BAD)\s+(G\d+)\b")
KW = 'self.keywords = [s.strip() for s in recs[0]["fields"]]'

MUTANTS = [
    ("MU1", 'GRID_DIGEST = "e0bb2deb53ecb96c"', 'GRID_DIGEST = "0000000000000000"', ["G8"],
     "the pinned digest is not the digest: G8's second-decode identity alone no longer pins it"),
    ("MU2", "rows = rows_bound // row_step", "rows = rows_bound // cell_step", ["G1"],
     "the row bound divided by the CELL stride: 19 rows, and G1's shape equality reddens"),
    ("MU3", "                v[self.keywords.index(kw)] += val",
            "                v[len(self.keywords) - 1 - self.keywords.index(kw)] += val",
     ["G2", "G4", "G5", "G7", "G8"],
     "the column index mirrored (the alphabetical-order rival made real): the vectors, the "
     "totals and the signatures all move while the keyword list stays correct"),
    ("MU4", "        for i, v in enumerate(self.vec):\n            if v > 0:", "        for i, v in enumerate(self.vec):\n            if v != 0:",
     ["G2", "G5"], "first-NON-ZERO instead of first-positive: a cell's signature lands on its "
     "penalty column (Police State -> 1, EFFIC -2)"),
    ("MU5", "                out[i] += v", "                out[i] += sum(c.vec[i] for c in self.rows[r])",
     ["G4", "G7"], "the category's 4 choices accumulated instead of the selected one: the printed "
     "totals and the sweep differ from the reference, and the all-cells rival stops differing"),
    ("MU6", 'and "DWORD PTR [ebx+0x94e48c]," in ins[a]', 'and "DWORD PTR [ebx+0x94e48c]" in ins[a]',
     ["G6"], "the store classifier stops distinguishing a LOAD from a STORE: 0x5579da joins the "
     "store list and the 'one store' claim reddens"),
    ("MU7", "                acc[kw] = acc.get(kw, 0) + val", "                acc[kw] = acc.get(kw, 0) + (1 if val > 0 else -1)",
     ["G4"], "the dict reference counts signs: the sweep finds disagreements the model does not "
     "have and G4 reddens on a rival that is now wrong"),
    ("MU8", "for r in range(3)) for i in range(len(kw)))", "for r in range(4)) for i in range(len(kw)))",
     ["G7"], "the 'Future Society dropped' rival made complete: it becomes the model and stops failing"),
    ("MU9", '         and ev.get("keyword list") == ", ".join(kw)\n',
            '         and ev.get("keyword list") == ", ".join(kw)[:-1]\n',
     ["G0"], "the evidence comparison off by one: the keyword line no longer matches and G0 reddens"),
    ("MU10", "                v[self.keywords.index(kw)] += val",
             "                v[self.keywords.index(kw)] += 2 * val",
     ["G2", "G3", "G4", "G8"], "every effect doubled: the parity vectors, the 5 magnitude bound, "
     "the totals and the grid digest all move"),
    ("MU11", "MIL_LO, MIL_HI = 0x557980, 0x5579EA", "MIL_LO, MIL_HI = 0x557980, 0x5579E9",
     ["G6"], "the military window truncated before the store: the 'one store at 0x5579ea' claim "
     "reddens on a dump drift"),
    ("NOOP", 'GRID_DIGEST = "e0bb2deb53ecb96c"', 'GRID_DIGEST = "e0bb2deb53ecb96c"', [],
     "the identity: nothing may redden"),
]


def run_one(mid, anchor, repl):
    src = open(SRC).read()
    n = src.count(anchor)
    if n != 1:
        return None, "ANCHOR appears %d times (want 1)" % n, ""
    path = os.path.join(SIM, "_b38_mut_%s.py" % mid)
    with open(path, "w") as fh:
        fh.write(src.replace(anchor, repl))
    try:
        r = subprocess.run([sys.executable, "-u", "-m", "sim._b38_mut_%s" % mid],
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
        red, err, _ = run_one("SELF", 'GRID_DIGEST = "e0bb2deb53ecb96c"', 'GRID_DIGEST = "0000000000000000"')
        print("SELFTEST: anchor machinery %s, red = %s"
              % ("OK" if red is not None and not err else "FAIL", red))
        return 0 if red == ["G8"] else 1
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
            print("      tail: %s" % " | ".join(l.strip() for l in out.splitlines()
                                                if "BAD" in l or "FAIL" in l)[:400])
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
