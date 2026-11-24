#!/usr/bin/env python3
"""M349 mutation harness - every VERIFIED row of the NAMED block names the mutant that reddens it.

Each mutant is a textual substitution in a copy of scripts/m349_unit_id.py.  A mutant SCORES
only if the copy exits non-zero AND the gate the row names is in the red list.  The covered set
is COMPUTED from the runs, never authored.  The NO-OP mutant (an identity substitution) must stay
green - it proves the harness can tell a real mutant from a no-op.

    python3 -u scripts/m349_mutate.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts", "m349_unit_id.py")

# (mutant, old, new, the gate the row names)
MUTANTS = [
    ("MU1", "sentinel -38 -> -39", "SENTINEL = 0xFFFFFFDA", "SENTINEL = 0xFFFFFFD9", "G3"),
    ("MU2", "type max 39 -> 38 in the model", "second = t - 39 if t >= 39 else -1",
     "second = t - 38 if t >= 38 else -1", "G4"),
    ("MU3", "band lo 34 -> 33", "band = 1 if 34 <= t < 38 else 0", "band = 1 if 33 <= t < 38 else 0", "G4"),
    ("MU4", "cost stride <- raw shift imm", "k * (1 << imm)", "k * imm", "G8"),
    ("MU5", "bitmap base +2", "bases.append(int(m.group(1), 16) if m else None)",
     "bases.append((int(m.group(1), 16) + 2) if m else None)", "G7"),
    ("MU6", "item threshold 0x40 -> 0x1f", "ITEM_THRESHOLD = 0x40", "ITEM_THRESHOLD = 0x1F", "G3"),
    ("MU7", "head>=0 becomes UNIT", '"FACILITY" if head < 64 else "BIGITEM"', '"UNIT"', "G4"),
    ("MU8", "M68 rival pinned to -6", "-(196 - 192)", "-6", "G11"),
    ("MU9", "B31 regex drops negatives", r"head=(-?\d+)", r"head=(\d+)", "G10"),
    ("MU10", "mapper window +0x30", "MAPPER + 0x26", "MAPPER + 0x30", "G9"),
    ("MU11", "mask &7 -> &0xf", "1 << (item & 7)", "1 << (item & 0xf)", "G13"),
    ("MU12", "signed truncating divide -> arithmetic shift", "(item + ((item >> 31) & 7)) >> 3",
     "item >> 3", "G13"),
    ("MU13", "decode block holds an or, not the neg", '(0x4EF89F, "neg ecx")', '(0x4EF89F, "pop ecx")', "G1"),
    ("MU14", "unit leg AND -> OR", '(0x4EF97A, "and al,cl")', '(0x4EF97A, "or al,cl")', "G5"),
    ("MU15", "stamp OR -> AND", '(0x4F0EC0, "or BYTE PTR [eax],cl")',
     '(0x4F0EC0, "and BYTE PTR [eax],cl")', "G6"),
    ("MU16", "facility gate 0x40 -> 0x3f", '(0x4EFE41, "cmp ebx,0x40")', '(0x4EFE41, "cmp ebx,0x3f")', "G2"),
    ("MU17", "sentinel compare -38 -> -39", "if head == -38:", "if head == -39:", "G12"),
    ("MU18", "R1 read without the negation", "decode(h)[1] == -h", "decode(h)[1] == h", "G11"),
]

RED = re.compile(r"^FAIL (G\d+)", re.M)


def run(src_text, tag):
    d = tempfile.mkdtemp(prefix="m349_%s_" % tag)
    p = os.path.join(d, "m349_unit_id.py")
    with open(p, "w") as f:
        f.write(src_text)
    env = dict(os.environ, PYTHONPATH="",
               SMAC_M349_TEXT=os.path.join(ROOT, "scratch", "m574", "text.txt"),
               SMAC_M349_B31=os.path.join(ROOT, "evidence", "b31_facoracle.txt"))
    r = subprocess.run([sys.executable, "-u", p], capture_output=True, text=True, env=env)
    red = sorted(set(RED.findall(r.stdout)))
    shutil.rmtree(d, ignore_errors=True)
    return r.returncode, red, r.stdout


def main():
    with open(SRC) as f:
        base = f.read()

    print("M349 mutation harness - %d declared mutants (baseline row %s)"
          % (len(MUTANTS), "MU0"))
    rc, red, out = run(base, "MU0")
    baseline_ok = rc == 0 and not red
    print("  baseline rc=%d red=%s -> %s" % (rc, red, "GREEN" if baseline_ok else "RED"))

    rc, red, _ = run(base, "noop")   # identity: same text, different directory
    noop = [] if (rc == 0 and not red) else ["NO-OP-NOT-GREEN"]
    print("  NO-OP rc=%d red=%s" % (rc, red))

    scored, missed = [], []
    covered = set()
    print("\n  %-4s %-50s %-5s %-5s %s" % ("id", "mutant", "rc", "gate", "red gates"))
    for mu, name, old, new, gate in MUTANTS:
        if old not in base:
            print("  %-4s %-50s  --   %-5s SUBSTITUTION NOT FOUND" % (mu, name, gate))
            missed.append(mu + " " + name + " (not found)")
            continue
        rc, red, _ = run(base.replace(old, new, 1), mu.lower())
        ok = rc != 0 and gate in red
        if ok:
            scored.append(mu)
            covered |= set(red)
        else:
            missed.append(mu)
        print("  %-4s %-50s %-5s %-5s %s  %s" % (mu, name, rc, gate, ",".join(red) or "-",
                                            "SCORED" if ok else "MISSED"))

    declared = {"G%d" % i for i in range(1, 14)}
    uncovered = sorted(declared - covered, key=lambda g: int(g[1:]))
    print("\n  scored %d/%d  covered %d/%d %s  NO-OP %s  uncovered %s"
          % (len(scored), len(MUTANTS), len(covered), len(declared), sorted(covered, key=lambda g: int(g[1:])),
             noop, uncovered))
    if not baseline_ok or noop or missed or uncovered:
        print("HARNESS FAIL M349: missed=%s uncovered=%s" % (missed, uncovered))
        return 1
    print("HARNESS PASS M349: %d/%d scored, NO-OP [], uncovered [] (covered %d/%d)"
          % (len(scored), len(MUTANTS), len(covered), len(declared)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
