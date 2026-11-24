#!/usr/bin/env python3
"""M366 mutation harness - every gate must be reddened by a NAMED, single source mutation.

Each row is (mutant id, the gate it must turn red, old source text, new source text).
The harness writes the mutated copy to scratch/, runs it, and checks that the NAMED gate prints
FAIL and that at least one gate is red.  The first row is the NO-OP control: the unmutated
instrument must stay 26/26 PASS.  ALG1/ALG2 mutate an ALGORITHM (the backward argument scan and
the rule-block window), not a threshold.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts/m366_bitnouns.py")
SCRATCH = os.path.join(ROOT, "scratch")
GATE = re.compile(r"^  (G\d[a-z]?)\s+(PASS|FAIL)", re.M)

NOOP = "MU0"

MUTANTS = [
    ("MU1",  "G1a", 'len(sites) == 232 and len(cnt) == 35,', 'len(sites) == 232 and len(cnt) == 34,'),
    ("MU2",  "G1b", 'stats[0x10][:3] == (37, 52, 16)', 'stats[0x10][:3] == (37, 52, 15)'),
    ("MU3",  "G1c", 'b_bits == [0x8, 0x2000],', 'b_bits == [0x8],'),
    ("MU4",  "G1d", 'both == [0x30, 0x31, 0x40C31],', 'both == [0x30, 0x31],'),
    ("MU5",  "G1e", 'odd == [0x54C0BA, 0x54C963]', 'odd == [0x54C0BA]'),
    ("MU6",  "G2a", '(CLR_A, 0x10, "or", 0x8040) in named,\n', '(CLR_A, 0x10, "or", 0x8000) in named,\n'),
    ("MU7",  "G2b", 'gate("G2b", (CLR_A, 0x20, "and", 0xFFFFF3FF) in named,',
                    'gate("G2b", (CLR_A, 0x20, "and", 0xFFFFF3FF) in [],'),
    ("MU8",  "G2c", '(SET_A, 0x10, "or", 0x80000108) in named,',
                    '(SET_A, 0x10, "or", 0x8000010) in named,'),
    ("MU9",  "G2d", 'gate("G2d", (CLR_B, 0x20, "and", 0xFFFFFFBF) in named,',
                    'gate("G2d", (CLR_B, 0x20, "and", 0xFFFFFFBF0) in named,'),
    ("MU10", "G2e", 'touch20 = [r for r in sets if r[1] & 0x20]', 'touch20 = [r for r in sets if r[1] & 0x10]'),
    ("MU11", "G3a", '0x8010 in push,', '0x8000 in push,'),
    ("MU12", "G3b", 'tens.count(0x10) == 2 and len(tens) == 2,', 'tens.count(0x10) == 1 and len(tens) == 2,'),
    ("MU13", "G3c", 'lits[0x68D67C] == "INCITED"', 'lits[0x68D67C] == "INCITE"'),
    ("MU14", "G3d", '{0x68D67C, 0x68D684} <= pushed,', '{0x68D67C, 0x68D690} <= pushed,'),
    ("MU15", "G3e", 'branch["op"] == "je" and set_side and clr_side,', 'branch["op"] == "jne" and set_side and clr_side,'),
    ("MU16", "G3f", 'm_ == [0x20, 0x1]', 'm_ == [0x20, 0x2]'),
    ("MU17", "G4a", 'mask == 0x40020 and "0x94d448" in site["arg"],', 'mask == 0x40000 and "0x94d448" in site["arg"],'),
    ("MU18", "G4b", 'imm(br[0]["arg"]) == mild["a"] + 5,', 'imm(br[0]["arg"]) == mild["a"] + 7,'),
    ("MU19", "G4c", '"tiny cubicle" in body["ECONOMICLOSE2"],', '"cubicle" in body["ECONOMICLOSE"],'),
    ("MU20", "G4d", 'and want <= keys,', 'and want <= set(),'),
    ("MU21", "G4e", 'and len(fns20) == 3,', 'and len(fns20) == 4,'),
    ("MU22", "G5a", 'cnt[(0x20, "test")] == 37', 'cnt[(0x20, "test")] == 36'),
    ("MU23", "G5b", 'gate("G5b", (0x8010, "test") not in cnt,', 'gate("G5b", (0x8010, "test") in cnt,'),
    ("MU24", "G5c", 'len(bare8) >= 2 and any(w == SET_A for _, w in bare8),', 'len(bare8) >= 20 and any(w == SET_A for _, w in bare8),'),
    ("MU25", "G6a", 'r1 = (0x1 in cleared and 0x2 in cleared and 0x4 in cleared)',
                    'r1 = (0x1 in cleared and 0x2 in cleared and 0x40 in cleared)'),
    ("MU26", "G6b", 'diff_clear = (CLR_A, 0x10, "or", 0x8040) in named',
                    'diff_clear = (CLR_A, 0x10, "or", 0x8000) in named'),
    ("MU27", "G6c", 'r3 = bare8 != bare10 and', 'r3 = bare8 == bare10 and'),
    ("MU28", "G6d", 'r4 = "FUN_00442320" in mex', 'r4 = "FUN_00442320" not in mex'),
    ("MU29", "G6e", 'gate("G6e", len(both) == 3 and only20 == 18 and',
                    'gate("G6e", len(both) == 2 and only20 == 18 and'),
    # ALGORITHM mutants: the backward argument scan and the rule-block window
    ("ALG1", "G3b", 'for back in range(POS[i["a"]] - 1, POS[i["a"]] - 11, -1):',
                    'for back in range(POS[i["a"]] - 1, POS[i["a"]] - 3, -1):'),
    ("ALG2", "G2c", 'if cur is None or k - cur_k > 40:', 'if cur is None or k - cur_k > 12:'),
]


def run(text, tag):
    p = os.path.join(SCRATCH, f"m366_mut_{tag}.py")
    with open(p, "w") as f:
        f.write(text)
    r = subprocess.run([sys.executable, "-u", p], capture_output=True, text=True, env=os.environ)
    return r.stdout + r.stderr, r.returncode


def main():
    src = open(SRC).read()
    ok = bad = 0
    out, rc = run(src, "noop")
    red = {g for g, v in GATE.findall(out) if v == "FAIL"}
    noop = (rc == 0 and not red and "PASS M366: 29/29 gates" in out)
    print(f"{NOOP}   NO-OP rc={rc} red={sorted(red) or 'none'}  -> {'PASS' if noop else 'BAD'}")
    ok += noop
    bad += not noop
    for mid, gate, old, new in MUTANTS:
        if src.count(old) != 1:
            print(f"{mid:5s} BAD  anchor not unique ({src.count(old)} hits): {old[:60]}")
            bad += 1
            continue
        out, rc = run(src.replace(old, new, 1), mid)
        red = {g for g, v in GATE.findall(out) if v == "FAIL"}
        good = gate in red and rc == 1
        print(f"{mid:5s} {gate:4s} rc={rc} red={sorted(red)} -> {'RED as named' if good else 'BAD'}")
        ok += good
        bad += not good
    print(f"\nPASS M366-harness: {ok}/{ok + bad} ({len(MUTANTS)} mutants + 1 NO-OP, {bad} bad)")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
