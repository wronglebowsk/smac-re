#!/usr/bin/env python3
"""B39 mutant harness (review_lint law: every V row in NAMED ## B39 names its mutant).

Re-creates each defect in a COPY of sim/relapi.py (one anchor -> replacement, installed as
sim/_b39_mut_<id>.py so `-m` resolution still works) and runs it against the same dump.  A mutant
must redden EXACTLY its declared gate set; the NO-OP mutant must redden nothing - that is what
proves the comparison bites.  An anchor that does not occur exactly once is a harness error.

  python3 -u scripts/b39_mutate.py             # full run
  python3 -u scripts/b39_mutate.py --selftest  # machinery only

Zero box, zero /proc, zero gdb.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sim", "relapi.py")
SIM = os.path.dirname(SRC)
GATE_RE = re.compile(r"^\s*(ok|BAD)\s+(G\d+\w*)\b", re.M)

MUTANTS = [
    ("MU1", 'WORD_B = 0x94D468', 'WORD_B = 0x94D448', ["G1", "G2"],
     "the one-matrix rival made real: the sibling displacement IS 0x94d448, so the two words "
     "collapse in the homes table and the row offset"),
    ("MU2", '                    if base in ptr:\n                        field, partner = ptr[base]',
            '                    field = None', ["G1", "G3b", "G6"],
     "the folded-pointer census switched off: 0x551c40 and 0x551d70 store through a register the "
     "preceding `lea` set, so their homes read empty and the padding rival comes back to life"),
    ("MU3", "    if mask & 0x20:", "    if mask & 0x40:", ["G4"],
     "the 0x20 arm tested against 0x40 instead: the seeded 0x2050 keeps 0x40 and G4's 0x2010 "
     "expectation reddens"),
    ("MU4", 'and int(x[2], 16) == 0x523F60]', 'and int(x[2], 16) == 0x523F38]', ["G5b"],
     "the skip target mistyped: the bit0 `je 0x523f38` is selected instead of `je 0x523f60`, and "
     "its predecessor is a `test`, not the pair-equality `cmp`"),
    ("MU5", "    if cur != partner:", "    if True:", ["G5c", "G6"],
     "the pair-equality guard removed: a self-pair now gets the 0x1 and 0x2000 writes, and the "
     "naive rival stops differing from the measurement"),
    ("MU6", "return ((((1 << 6) + 1) * 2 + 1) << 4) - 1", "return 2096", ["G2"],
     "the row scale off by one: the 2095-dword identity from M297 is no longer reproduced"),
    ("MU7", '        if len(p) == 2 and p[1] not in REGS:', '        if False:', ["G3"],
     "the arg-guard extractor switched off: test bl,0x7 / bl,0x20 / cl,0x40 all vanish"),
    ("MU8", '    d1 = sha16(["%x:%s:%s" % (a, m, o) for a, m, o in ins]',
            '    d1 = sha16(["seed"] + ["%x:%s:%s" % (a, m, o) for a, m, o in ins]', ["G7"],
     "the first digest's input gets a constant the second decode does not: the two decodes no "
     "longer agree"),
    ("MU10", '    seq = [(p, m[0]) for a, p, m in sites[:3]]',
             '    seq = [(p, m[-1]) for a, p, m in sites[:3]]', ["G5a"],
     "the argument position flipped: the decoded masks become the destination registers, so the "
     "call sequence no longer reads 0x50 / 0x1 / 0x2000"),
    ("MU11", "    if (arow & 0x1) and (arow & 0x2000000):", "    if (arow & 0x2000000):", ["G5c"],
     "the bit0 precondition dropped: 0x2000000 now skips the block even for an uncontacted pair, "
     "and the 'WITHOUT bit0' scenario reddens"),
    ("MU12", '(0x523F2D, "test al,0x1", "je", 0x523F38)', '(0x523F2D, "test al,0x2", "je", 0x523F38)', ["G5d"],
     "a guard immediate mistyped: the bit0 test is pinned as al,0x2, which the bytes do not carry"),
    ("MU9", '"""sim.relapi - rung B39', '"""sim.relapi - rung B39 ', [],
     "NO-OP: a docstring space changes nothing, so every gate must stay green"),
]


def run(path, mod):
    env = dict(os.environ)
    return subprocess.run([sys.executable, "-u", "-m", mod], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    src = open(SRC).read()
    fails = []
    noop = None
    for mid, anchor, repl, want, why in MUTANTS:
        n = src.count(anchor)
        if n != 1:
            print("HARNESS ERROR %s anchor occurs %d times" % (mid, n))
            return 2
        if args.selftest:
            print("%s anchor ok" % mid)
            continue
        mod = "_b39_mut_%s" % mid
        path = os.path.join(SIM, mod + ".py")
        if '"""sim.relapi - rung B39 ' in repl:
            body = src.replace(anchor, repl, 1)
        else:
            body = src.replace(anchor, repl, 1)
        open(path, "w").write(body)
        try:
            res = run(path, "sim." + mod)
        finally:
            os.unlink(path)
        out = res.stdout.decode("utf-8", "replace")
        red = sorted(set(m for s, m in GATE_RE.findall(out) if s == "BAD"))
        if "PASS B39" in out and not want:
            noop = mid
            print("ok   %s NO-OP   %s" % (mid, why))
            continue
        if red == sorted(want):
            print("ok   %s reddens %s   %s" % (mid, red, why))
        else:
            fails.append(mid)
            print("BAD  %s expected %s got %s" % (mid, sorted(want), red))

    if args.selftest:
        print("RUN PASS %d anchors unique" % len(MUTANTS))
        return 0
    if fails or noop is None:
        print("RUN FAIL %d/%d mutants misbehaved: %s (noop=%s)" % (len(fails), len(MUTANTS), fails, noop))
        return 1
    print("RUN PASS %d mutants, NO-OP %s" % (len(MUTANTS), noop))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
