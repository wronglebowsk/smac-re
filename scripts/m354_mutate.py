#!/usr/bin/env python3
"""M354 mutation harness - every VERIFIED row of `## M354` names a mutant that
REDDENS its gate.  A mutant edits ONE instruction of the parsed listing through
SMAC_M354_PATCH (`0xADDR|old|new`); the acceptance script is not modified.
PATCH REJECTED (exit) counts as a harness failure, never a pass.

    python3 -u scripts/m354_mutate.py        # writes evidence/m354_mutate.txt

Scoring: SCORED = acceptance exits non-zero AND the declared gate is in the
FAIL set.  NO-OP mutants must stay green.  Coverage = the gates actually
reddened, measured.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "scratch", "m574", "text.txt")
SCRIPT = os.path.join(ROOT, "scripts", "m354_design_row.py")
OUT = os.path.join(ROOT, "evidence", "m354_mutate.txt")
BASELINE = "MU0"                     # the unmutated run every claim's rows ride on

# (id, addr, old, new, gate, why)
MUTANTS = [
    ("MU1", 0x49571B, "imul edx,edx,0x34", "imul edx,edx,0x30", "G1", "A row stride 0x34 -> 0x30"),
    ("MU2", 0x49571E, "add edx,0x98ad88", "add edx,0x98ad89", "G1", "name field off +0 by one"),
    ("MU3", 0x4957E7, "[ecx+0x98adb1]", "[ecx+0x98adb3]", "G1", "weight field +0x29 -> +0x2b"),
    ("MU4", 0x496065, "imul eax,eax,0x34", "imul eax,eax,0x30", "G3", "A flags fn row stride"),
    ("MU5", 0x496085, "[edx+0x98adb2]", "[edx+0x98adb1]", "G3", "class field +0x2a -> +0x29"),
    ("MU6", 0x49605C, "cmp DWORD PTR [ebp+0x8],0x40", "cmp DWORD PTR [ebp+0x8],0x50", "G3", "band guard 0x40 -> 0x50"),
    ("MU7", 0x49606F, "and ecx,0x4", "and ecx,0x8", "G3", "design flag bit 4 -> 8"),
    ("MU8", 0x495A8D, "or al,0x20", "or al,0x10", "G5", "A section loses the +bit"),
    ("MU9", 0x495DFF, "or al,0x10", "or al,0x20", "G5", "B section gains the +bit"),
    ("MU10", 0x49772A, "and eax,0x20", "and eax,0x10", "G5", "modal sign test bit"),
    ("MU11", 0x596017, "cmp ecx,0x40", "cmp ecx,0x30", "G6", "builder band split 0x40 -> 0x30"),
    ("MU12", 0x59601F, "shl eax,0x6", "shl eax,0x5", "G6", "owner tag 6 bits -> 5"),
    ("MU13", 0x5A7402, "[edx+0x98adb8],0x1", "[edx+0x98adb8],0x2", "G7", "valid bit 0 -> bit 1"),
    ("MU14", 0x5A748B, "[edx+0x98adb2]", "[edx+0x98adb3]", "G7", "validator class field"),
    ("MU15", 0x4EF8ED, "[edx+0x984d44]", "[edx+0x984d40]", "G9", "negative leg cost field"),
    ("MU16", 0x4EFE50, "[edx+0x98adb8]", "[edx+0x98adb4]", "G9", "positive leg stamps the mask byte"),
]
NOOP = ("MU17", 0x4956F9, "add esp,0xc", "add esp,0x10", "NOOP", "an instruction no gate pins")
MODEL = ("MU18", "band", "G6", "classifier: read the owner band as 5 bits")


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True,
                       text=True, env=env)
    red = sorted(set(re.findall(r"^FAIL (G\d+b?)", p.stdout, re.M)),
                 key=lambda s: int(s[1:].rstrip("b")))
    return p.returncode, red, p.stdout + p.stderr


def main():
    rows, cov = [], set()
    rc0, red0, _ = run({})
    print("M354 mutation harness - %d declared mutants" % (len(MUTANTS) + 2))
    print("%-5s baseline: exit %d reds %s" % (BASELINE, rc0, red0 or "[]"))
    ok_base = rc0 == 0 and not red0
    for mid, addr, old, new, gate, why in MUTANTS + [NOOP]:
        rc, red, out = run({"SMAC_M354_PATCH": "0x%x|%s|%s" % (addr, old, new)})
        if "PATCH REJECTED" in out:
            score = "PATCH-FAIL"
        elif gate == "NOOP":
            score = "NO-OP " if (rc == 0 and not red) else "BAD-NOOP"
        else:
            score = "SCORED" if (rc != 0 and gate in red) else "MISSED"
            if score == "SCORED":
                cov.add(gate)
        print("%-5s 0x%06x %-28s -> %-30s gate %-4s %s  reds=%s"
              % (mid, addr, old, new, gate, score, red or "[]"))
        rows.append((mid, gate, score, why, tuple(red)))
    mid, kind, gate, why = MODEL
    rc, red, out = run({"SMAC_M354_MUTANT": kind})
    score = "SCORED" if (rc != 0 and gate in red) else "MISSED"
    if score == "SCORED":
        cov.add(gate)
    print("%-5s model %-24s gate %-4s %s  reds=%s" % (mid, kind, gate, score, red or "[]"))
    rows.append((mid, gate, score, why, tuple(red)))

    bad = [r for r in rows if r[2] not in ("SCORED", "NO-OP ")]
    print()
    print("covered gates (measured): %s" % sorted(cov))
    print("scored %d/%d, NO-OP %s, bad %s"
          % (sum(1 for r in rows if r[2] == "SCORED"), len(rows),
             [r[0] for r in rows if r[2] == "NO-OP "], [r[0] for r in bad]))
    if ok_base and not bad:
        print("PASS HARNESS M354: %d/%d scored, NO-OP %s, covered %s"
              % (sum(1 for r in rows if r[2] == "SCORED"), len(rows),
                 [r[0] for r in rows if r[2] == "NO-OP "], sorted(cov)))
        return 0
    print("FAIL HARNESS M354: %s" % ([r[0] for r in bad],))
    return 1


if __name__ == "__main__":
    sys.exit(main())
