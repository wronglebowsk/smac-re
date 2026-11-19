#!/usr/bin/env python3
"""Fixtures for review_lint: every check must BITE on a bad fixture and
PASS on the compliant one (the lint is itself a gate — decorate nothing)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_lint import block_for, lint_block, cited_mus

HARNESS = 'MUTANTS = [\n ("MU1", "exp", "a", "b", "x"),\n ("MU2", "code", "c", None, "y"),\n ("MU3", "noop", "d", None, None),\n]'
EVID = {"evidence/m999_x.txt": "line1\n== digest: 0123456789abcdef ==\n",
        "evidence/m999_mutate.txt": "== M999 mutate: 2/2 scored, digest fedcba9876543210 ==\n"}

GOOD = """## M999 (s999) - test block

| claim | evidence | conf |
|---|---|---|
| FACT ONE: something measured | C1 (`evidence/m999_x.txt:2`), MU1 | V |
| FACT TWO: another measured thing, MU2-MU3 | C2 (`evidence/m999_x.txt:1-2`) | V (bytes) |
| ACCEPT: digest 0123456789abcdef (`evidence/m999_x.txt:2`); harness fedcba9876543210 (`evidence/m999_mutate.txt:1`) | as cited | V |
| OPEN: something unmeasured | - | lead |
"""

def run(name, block, harness, evid, want_fail_substr):
    fails = lint_block(block, harness, evid)
    if want_fail_substr is None:
        ok = not fails
    else:
        ok = any(want_fail_substr in f for f in fails)
    print("%-28s %s  %s" % (name, "OK" if ok else "BAD", fails if fails else "clean"))
    return ok

def main():
    results = []
    results.append(run("compliant block", GOOD, HARNESS, EVID, None))
    # L1: a V row with no mutant
    b = GOOD.replace("C1 (`evidence/m999_x.txt:2`), MU1", "C1 (`evidence/m999_x.txt:2`)")
    results.append(run("L1 missing mutant", b, HARNESS, EVID, "L1 no mutant cited"))
    # L2: cites a mutant the harness does not have
    b = GOOD.replace("MU1 |", "MU9 |")
    results.append(run("L2 unknown mutant", b, HARNESS, EVID, "L2 mutant MU9 not in harness"))
    # L3: digest quoted but never printed in cited evidence
    b = GOOD.replace("0123456789abcdef", "aaaaaaaaaaaaaaaa")
    results.append(run("L3 unprinted digest", b, HARNESS, EVID, "L3 digest aaaaaaaaaaaaaaaa"))
    # L4: evidence citation without a line number
    b = GOOD.replace("`evidence/m999_x.txt:2`), MU1", "`evidence/m999_x.txt`), MU1")
    results.append(run("L4 cite without line", b, HARNESS, EVID, "L4 citation without :line"))
    # range expansion: MU2-MU3 covers both; a range reaching MU4 must fail L2
    b = GOOD.replace("MU2-MU3", "MU2-MU4")
    results.append(run("L2 range expansion", b, HARNESS, EVID, "L2 mutant MU4 not in harness"))
    # block extraction
    named = "## M998 ...\n\n" + GOOD + "\n## M997 ...\n"
    blk = block_for(named, "m999")
    ok = blk is not None and blk.startswith("## M999") and "M997" not in blk
    print("%-28s %s" % ("block extraction", "OK" if ok else "BAD"))
    results.append(ok)
    n = sum(results)
    print("\n== test_review_lint: %d/%d ==" % (n, len(results)))
    return 0 if n == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())