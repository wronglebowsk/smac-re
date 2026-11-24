#!/usr/bin/env python3
"""m368_mutate.py — the mutant harness for scripts/m368_peace_ladder.py.

Every gate in the instrument must be able to FAIL on a real state.  Each mutant below patches a
CONSTANT or an EXPECTATION in a copy of the instrument (never the dump, never the exe), runs it,
and requires (a) the whole run to turn red and (b) the named gate to print FAIL.  The harness also
asserts that the union of the mutants' FAIL sets covers every gate the instrument prints, so no
gate ships without a mutant.

    python3 -u scripts/m368_mutate.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts/m368_peace_ladder.py")
OUT = os.path.join(ROOT, "scratch/m368_mut")

# (name, needle, replacement, gate that must redden)
MUTANTS = [
    ("MU1", 'BYTES.get(0x551ABC) == "83cb02"', 'BYTES.get(0x551ABC) == "83cb03"', "G0a"),
    ("MU2", r'r"and\s+edx,0xffee7faf$"', r'r"and\s+edx,0xffee7fae$"', "G0b"),
    ("MU3", '("push   0x1", "push   0x2", "push   0x4")',
     '("push   0x1", "push   0x2", "push   0x8")', "G0c"),
    ("MU4", "len(sites) == 169", "len(sites) == 168", "G1a"),
    ("MU5", "{m for a, t, m in peace} == {1, 2, 4}", "{m for a, t, m in peace} == {1, 2, 4, 8}",
     "G1b"),
    ("MU6", "0x5537D0 in fns", "0x5537D1 in fns", "G1c"),
    ("MU7", 'EXPECT_KEYS = {0x4: "ENEMYTRUCE", 0x2: "ENEMYTREATY", 0x1: None}',
     'EXPECT_KEYS = {0x4: "ENEMYTREATY", 0x2: "ENEMYTRUCE", 0x1: None}', "G2-553c41"),
    ("MU8", 'EXPECT_KEYS = {0x4: "ENEMYTRUCE", 0x2: "ENEMYTREATY", 0x1: None}',
     'EXPECT_KEYS = {0x4: "ENEMYTRUCE", 0x2: "ENEMYTREATY", 0x1: "ENEMYTREATY"}', "G2-554165"),
    ("MU9", "keys[4][-1] != keys[2][-1]", "keys[4][-1] == keys[2][-1]", "G2x"),
    ("MU10", "up == 1 and rev == 0", "up == 2 and rev == 0", "G3a"),
    ("MU11", "fn_of(0x551ABC) == 0x551A20", "fn_of(0x551ABC) == 0x551A21", "G3b"),
    ("MU12", "CLEAR_A = 0x00118050", "CLEAR_A = 0x00118040", "G4a"),
    ("MU13", "WAR_A = 0x05110C87", "WAR_A = 0x05110C86", "G4b"),
    ("MU14", "clr == [0x10, 0x40, 0x8000, 0x10000, 0x100000]",
     "clr == [0x10, 0x40, 0x8000, 0x10000]", "G4c"),
    ("MU15", "cnt == 1089", "cnt == 1090", "G5a"),
    ("MU16", 'EXPECT_LABEL = {0x4: "Truce", 0x2: "Treaty", 0x1: "Pact"}',
     'EXPECT_LABEL = {0x4: "Truce", 0x2: "Treaty", 0x1: "Truce"}', "G5-1"),
    ("MU17", 'EXPECT_LABEL = {0x4: "Truce", 0x2: "Treaty", 0x1: "Pact"}',
     'EXPECT_LABEL = {0x4: "Truce", 0x2: "Truce", 0x1: "Pact"}', "G5-2"),
    ("MU18", 'EXPECT_LABEL = {0x4: "Truce", 0x2: "Treaty", 0x1: "Pact"}',
     'EXPECT_LABEL = {0x4: "Treaty", 0x2: "Treaty", 0x1: "Pact"}', "G5-4"),
    ("MU19", '== "Diplomacy for"', '== "Diplomacy of"', "G5b"),
    ("MU20", "order == [0x1, 0x2, 0x4]", "order == [0x1, 0x4, 0x2]", "G6a"),
    ("MU21", "paired and len(tests) == 3", "paired and len(tests) == 4", "G6b"),
    ("MU22", "numeric == 0", "numeric == 1", "G6c"),
    ("MU23", 'gate("G7a", g2,', 'gate("G7a", not g2,', "G7a"),
    ("MU24", 'gate("G7b", ok3 and ok6,', 'gate("G7b", not (ok3 and ok6),', "G7b"),
    ("MU25", 'gate("G7c", g2,', 'gate("G7c", not g2,', "G7c"),
    ("MU26", 'gate("G7d", ok6,', 'gate("G7d", not ok6,', "G7d"),
    ("MU27", 'gate("G7e", ok4,', 'gate("G7e", not ok4,', "G7e"),
]
FAILGATE = re.compile(r"^\s+(\S+)\s+FAIL\s", re.M)


def run(path):
    env = dict(os.environ)
    # the copy lives under scratch/, so pin every input to the real checkout
    env.update({
        "M368_TEXT": os.path.join(ROOT, "scratch/m574/text.txt"),
        "M368_EXE": os.path.join(ROOT, "programs/terran.exe"),
        "M368_LABELS": os.path.join(ROOT, "programs/labels.txt"),
        "M368_INDEX": os.path.join(ROOT, "ghidra_out/index.csv"),
    })
    p = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                       env=env, timeout=300)
    return p.returncode, p.stdout


def main():
    src = open(SRC).read()
    os.makedirs(OUT, exist_ok=True)
    rc, base = run(SRC)
    pads = re.findall(r"^\s+(\S+)\s+PASS\s", base, re.M)
    print("baseline rc=%d gates PASS=%d" % (rc, len(pads)))
    if rc != 0:
        print("BASELINE RED — nothing to mutate")
        return 1
    covered, noop, bad = set(), [], []
    for name, old, new, target in MUTANTS:
        n = src.count(old)
        if n != 1:
            print("%-5s ANCHOR x%d — not a mutant" % (name, n))
            bad.append(name)
            continue
        path = os.path.join(OUT, name + ".py")
        with open(path, "w") as f:
            f.write(src.replace(old, new))
        rc, out = run(path)
        fails = set(FAILGATE.findall(out))
        covered |= fails
        hit = target in fails
        print("%-5s rc=%d reddens %-40s target %-9s %s"
              % (name, rc, ",".join(sorted(fails)) or "-", target, "OK" if hit else "NO-OP"))
        if not hit:
            noop.append(name)
    missing = sorted(set(pads) - covered)
    print("\ngates covered %d/%d; uncovered %s" % (len(covered & set(pads)), len(pads),
                                                  missing or "[]"))
    print("RUN %s %d mutants, NO-OP %s" % ("PASS" if not (noop or bad or missing) else "FAIL",
                                           len(MUTANTS), noop + bad))
    return 0 if not (noop or bad or missing) else 1


if __name__ == "__main__":
    raise SystemExit(main())
