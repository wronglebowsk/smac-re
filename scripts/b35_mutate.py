#!/usr/bin/env python3
"""B35 mutant harness (review_lint law: every V row in NAMED ## B35 names its mutant).

Re-creates each defect in a COPY of sim/grantcall.py (one anchor -> replacement, installed
as sim/_b35_mut_<id>.py so the relative `from . import facoracle` still resolves) and runs
it against the same dump + recorded trace.  A mutant must redden EXACTLY its declared gate
set; the identity (NO-OP) mutant must redden nothing - that is what proves the comparison
bites.  An anchor that does not occur exactly once is a harness error, not a pass.

  python3 -u scripts/b35_mutate.py             # full run (~12 mutants x 1.5 s)
  python3 -u scripts/b35_mutate.py --selftest  # machinery only, no dump needed

Zero box, zero /proc, zero gdb.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sim", "grantcall.py")
SIM = os.path.dirname(SRC)
GATE_RE = re.compile(r"^(ok|BAD)\s+(G\d+)\b")

MUTANTS = [
    ("MU1", 'FOUNDER_SIG = {1, 3, 6, 7, 26}', 'FOUNDER_SIG = {3, 6, 7, 26}', ["G8"],
     "item 1 dropped from the founder's signature: the two discriminating births stop being explained"),
    ("MU2", 'NEWGAME_SET = {3, 4, 6, 7, 8, 27}', 'NEWGAME_SET = {1, 3, 4, 6, 7, 8, 27}', ["G8", "G11"],
     "bit 1 folded into the new-game set: the rival entry scores 3/3 and the two entries stop separating"),
    ("MU3", 'SITES_FOUNDER = [0x4CCBDD, 0x59D894, 0x5A01F8]', 'SITES_FOUNDER = [0x4CCBDD, 0x59D894]',
     ["G1"], "one founder call site deleted from the pinned list: the census mismatch goes unnoticed"),
    ("MU4", 'ITEMS_NEWGAME = [6, 3, 7, 27, 8, 4, 6, 3, 6, 3, 27]',
            'ITEMS_NEWGAME = [6, 3, 7, 27, 8, 4, 6, 3, 6, 3, 26]', ["G3"],
     "one decoded item changed: the push-to-arg decode would be taken on faith"),
    ("MU5", "and bool(ors) and min(ors) > ZERO_AT", "and bool(ors) and min(ors) < ZERO_AT", ["G6"],
     "the zero/OR ORDER inverted: an OR-then-zero init would read as the birth signature"),
    ("MU6", "            if si:\n                out.append", "            if True:\n                out.append",
     ["G7", "G8", "G9", "G10", "G11"], "the 19 bases present at sample 0 counted as births: the oracle is no longer mid-run"),
    ("MU7", "want=3, window=PUSH_WINDOW", "want=2, window=PUSH_WINDOW",
     ["G3", "G4", "G10"], "the arg decode keeps 2 pushes: the item stops being the last push"),
    ("MU8", "seq == INIT_SEQ and len(ors) == 7", "seq == INIT_SEQ and len(ors) == 8", ["G6"],
     "the OR-site count off by one: a changed founder body would still pass"),
    ("MU9", 'if len(args) == 3 and args[0] == "0x1" and re.fullmatch(r"[a-z]{2,3}", args[1])',
            'if len(args) == 3 and args[0] != "0x1" and re.fullmatch(r"[a-z]{2,3}", args[1])', ["G3"],
     "the set-flag comparison inverted: no site reads as a grant and the gate must bite"),
    ("MU11", "        hit = [x for x in bt if set(x[2]) <= sig]", "        hit = [x for x in bt if True]",
     ["G8", "G11"], "coverage made unconditional: both entries read 3/3 and stop separating"),
    ("MU12", 'DELTA_DIGEST = "5a5c124ccb32e35c"', 'DELTA_DIGEST = "0000000000000000"', ["G10"],
     "a digest unpinned: a change-shape drift would slip past"),
    ("MU13", 'apib = [(ins[i][0], ins[i][1], ins[i][2]) for i in fn_body(ins, owners, "FUN_004e44f0")]',
             'apib = [(ins[i][0], ins[i][1], ins[i][2]) for i in fn_body(ins, owners, "FUN_00507410")]', ["G5"],
     "the API body read from the MAPPER instead: the stride computation and the two stores go unmeasured"),
    ("MU14", "grant_ok = [c for c in ch if set(c[3]) <= FOUNDER_SIG]", "grant_ok = list(ch)", ["G9"],
     "every change counted as founder-compatible: the bit-identity count stops being measured"),
    ("MU15", 'HOSTS_FOUNDER = ["FUN_004cca50", "FUN_0059ce10", "FUN_0059ec90"]',
             'HOSTS_FOUNDER = ["FUN_004cca50", "FUN_0059ce10"]', ["G2"],
     "one host deleted from the pinned list: the attribution row would be taken on faith"),
    ("MU16", "and [_a for _a, _m in api_st] == [0x4E4528, 0x4E4546]",
             "and [_a for _a, _m in api_st] == [0x4E4529, 0x4E4546]", ["G5"],
     "a pinned store address off by one: the gate would accept a different store endpoint"),
    ("MU17", "overlap = [c for c in ch if c[0] in bset]", "overlap = list(ch)", ["G9", "G11"],
     "births and changes no longer tested for disjointness: 0/6 becomes 6/6"),
    ("MU18", "[(19, (1,), 5, 2), (20, (), 5, 2), (21, (1, 3), 19, 9)]",
             "[(19, (1,), 0, 0), (20, (), 0, 0), (21, (1, 3), 0, 0)]", ["G7"],
     "the birth SAMPLE/round unpinned: a birth at sample 0 would read as mid-run"),
    ("NOOP", 'ANCHOR = "fa541d0a2445cacf"', 'ANCHOR = "fa541d0a2445cacf"', [],
     "identity: nothing may redden"),
]


def run_one(mid, anchor, repl):
    src = open(SRC).read()
    n = src.count(anchor)
    if n != 1:
        return None, "ANCHOR appears %d times (want 1)" % n, ""
    path = os.path.join(SIM, "_b35_mut_%s.py" % mid)
    with open(path, "w") as fh:
        fh.write(src.replace(anchor, repl))
    try:
        r = subprocess.run([sys.executable, "-u", "-m", "sim._b35_mut_%s" % mid],
                           cwd=ROOT, capture_output=True, text=True, timeout=300)
    finally:
        if os.path.exists(path):
            os.remove(path)
    red = sorted({m.group(2) for ln in r.stdout.splitlines()
                  for m in [GATE_RE.match(ln)] if m and m.group(1) == "BAD"})
    return red, "", r.stdout


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        red, err, _ = run_one("SELF", 'FOUNDER_SIG = {1, 3, 6, 7, 26}', 'FOUNDER_SIG = {3, 6, 7, 26}')
        print("SELFTEST: anchor machinery %s, red = %s" % ("OK" if red is not None and not err else "FAIL", red))
        return 0 if red == ["G8", "G11"] else 1
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
