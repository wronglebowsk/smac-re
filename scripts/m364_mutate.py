#!/usr/bin/env python3
"""M364 mutation harness - every gate must be reddened by a NAMED, single source mutation.

Each row is (mutant id, the gate it must turn red, old source text, new source text).
The harness writes the mutated copy to scratch/, runs it, and checks:
  * the NAMED gate prints FAIL, and
  * at least one gate is red (a mutant that changes nothing is a NO-OP and is itself a defect).
The final row is the NO-OP control: the unmutated script must stay 24/24 PASS.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts/m364_bitnouns.py")
SCRATCH = os.path.join(ROOT, "scratch")
GATE = re.compile(r"^  (G\d[a-z]?)\s+(PASS|FAIL)", re.M)

MUTANTS = [
    ("MU1",  "G1a", 'and all(h[2] == (h[1] & 0x7FFFFFFF) for h in hits),',
                    'and all(h[2] == h[1] for h in hits),'),
    ("MU2",  "G1b", 'all(h[4] - 0x94D430 in (REC_OFF_A, REC_OFF_B) for h in hits)',
                    'all(h[4] - 0x94D430 in (REC_OFF_A,) for h in hits)'),
    ("MU3",  "G1d", 'gate("G1d", dup == [0x8, 0x2000],',
                    'gate("G1d", dup == [0x2000],'),
    ("MU4",  "G1e", 'gate("G1e", STRIDE_DW * 4 == STRIDE_B and 0x82F == STRIDE_B // 4,',
                    'gate("G1e", STRIDE_DW * 2 == STRIDE_B and 0x82F == STRIDE_B // 4,'),
    ("MU5",  "G2a", 'gate("G2a", imul and imm(imul[0]["arg"].split(",")[-1]) == STRIDE_B,',
                    'gate("G2a", imul and imm(imul[0]["arg"].split(",")[-1]) == 0x20B0,'),
    ("MU6",  "G2b", 'and "[" in i["arg"].split(",")[0]',
                    'and len(i["arg"]) > 0'),
    ("MU7",  "G3a", 'gate("G3a", len(out) == 232 and sum(const.values()) == 214,',
                    'gate("G3a", len(out) == 232 and sum(const.values()) == 148,'),
    ("MU8",  "G3b", 'and lone == {0x800},', 'and lone == set(),'),
    ("MU9",  "G3c", '0x8000, 0x10000, 0x40000,', '0x8000, 0x40, 0x40000,'),
    ("MU10", "G4a", '0x1: ("pact in force", ["REALLYENDPACT", "DONTHAVEPACT"]),',
                    '0x1: ("pact in force", ["REALLYENDPACTS", "DONTHAVEPACT"]),'),
    ("MU11", "G4c", 'gate("G4c", set(casew.get(0x1, ())) .isdisjoint(casew.get(0x8, ())),',
                    'gate("G4c", not set(casew.get(0x1, ())).isdisjoint(casew.get(0x8, ())),'),
    ("MU12", "G4d", 'gate("G4d", len(ask[0x1]) == 14 and len(ask[0x8]) == 9,',
                    'gate("G4d", len(ask[0x1]) == 15 and len(ask[0x8]) == 9,'),
    ("MU13", "G5a", 'gate("G5a", (0x5518F0, 0x7, "or", 0x1100000) in rules,',
                    'gate("G5a", (0x5518F0, 0x7, "or", 0x1000000) in rules,'),
    ("MU14", "G5c", 'bulk.get(0x1F89) == {0x1, 0x8, 0x400, 0x1000}',
                    'bulk.get(0x1F89) == {0x1, 0x8, 0x1000}'),
    ("MU15", "G6a", 'gate("G6a", kinds["test"] == 388 and kinds["mov"] == 300 and kinds["lea"] == 39,',
                    'gate("G6a", kinds["test"] == 387 and kinds["mov"] == 300 and kinds["lea"] == 39,'),
    ("MU16", "G7a", 'gate("G7a", len(outside) == 16,', 'gate("G7a", len(outside) == 12,'),
    ("MU17", "G7c", 'gate("G7c", not flip,', 'gate("G7c", flip,'),
    # ALGORITHM mutant 2: the case-block splitter collapses, so every ask inherits the whole
    # function's literal set and the two nouns stop being discriminated
    ("ALG2", "G4a", 'if re.match(r"^\\s*case\\s+[-0-9a-fx]+:", line):',
                     'if False:'),
    # ALGORITHM mutant: the push-scan window collapses, so the interleaved arg movs lose the mask
    ("ALG",  "G3a", "for back in range(n - 1, max(-1, n - 14), -1):",
                     "for back in range(n - 1, max(-1, n - 4), -1):"),
]


def run(text, tag):
    p = os.path.join(SCRATCH, f"m364_mut_{tag}.py")
    with open(p, "w") as f:
        f.write(text)
    r = subprocess.run([sys.executable, "-u", p], capture_output=True, text=True,
                       env={**os.environ, "M364_FAULT": ""})
    return r.stdout + r.stderr, r.returncode


def main():
    src = open(SRC).read()
    ok = bad = 0
    out, rc = run(src, "noop")
    red = {g for g, v in GATE.findall(out) if v == "FAIL"}
    noop = (rc == 0 and not red and "PASS  M364: 24/24 gates" in out)
    print(f"NO-OP  rc={rc} red={sorted(red) or 'none'}  -> {'PASS' if noop else 'BAD'}")
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
    print(f"\nPASS M364-harness: {ok}/{ok + bad} ({len(MUTANTS)} gate mutants + 1 NO-OP, "
          f"{bad} bad)")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
