#!/usr/bin/env python3
"""Fixtures for review_lint (s291 review-round hardened): every check must
BITE on a bad fixture and PASS on the compliant one."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_lint import block_for, lint_block

HARNESS = ('MUTANTS = [\n'
           ' ("MU1", "exp", "a", "b", "x"),\n'
           ' ("MU2", "code", "0x4e8d60|push eax", None, "y"),\n'
           ' ("MU3", "noop", "0x4e8d60|push ebx", None, None),\n'
           ' ("MU4", "code", "0xdeadbe|push eax", None, "z"),\n'
           ']')
ISRC = "PINS = {0x4E8D60: ('push', 'ebp'), 0x4e78e0: ('call', '0x4e63b0')}"
EVID = {"evidence/m999_x.txt": "line1\n== digest: 0123456789abcdef ==\n",
        "evidence/m999_mutate.txt": "== M999 mutate: 2/2 scored, digest fedcba9876543210 ==\n",
        "evidence/m999_other.txt": "unrelated tail 0123456789abcdef\n"}

GOOD = """## M999 (s999) - test block

| claim | evidence | conf |
|---|---|---|
| FACT ONE: something measured | C1 (`evidence/m999_x.txt:2`), MU1 | V |
| FACT TWO: another measured thing, MU2-MU3 | C2 (`evidence/m999_x.txt:1-2`) | V (bytes) |
| ACCEPT: digest 0123456789abcdef (`evidence/m999_x.txt:2`); harness fedcba9876543210 (`evidence/m999_mutate.txt:1`) | as cited | V |
| OPEN: something unmeasured | - | lead |
"""

def run(name, block, want, harness=HARNESS, evid=EVID, isrc=ISRC):
    fails = lint_block(block, harness, evid, isrc)
    ok = (not fails) if want is None else any(want in f for f in fails)
    print("%-32s %s  %s" % (name, "OK" if ok else "BAD", fails if fails else "clean"))
    return ok

def main():
    r = []
    r.append(run("compliant block", GOOD, None))
    b = GOOD.replace("C1 (`evidence/m999_x.txt:2`), MU1", "C1 (`evidence/m999_x.txt:2`)")
    r.append(run("L1 missing mutant", b, "L1 no mutant cited"))
    b = GOOD.replace("MU1 |", "MU9 |")
    r.append(run("L2 unknown mutant", b, "L2 mutant MU9 not in harness"))
    b = GOOD.replace("MU2-MU3", "MU2-MU5")
    r.append(run("L2 range expansion", b, "L2 mutant MU5 not in harness"))
    # L1 bypass attempt: factual claim prefixed ACCEPT, no harness/digest marker, no MU
    b = GOOD.replace("FACT ONE: something measured | C1 (`evidence/m999_x.txt:2`), MU1",
                     "ACCEPTANCE OF FOO: a factual claim | C1 (`evidence/m999_x.txt:2`)")
    r.append(run("L1 prefix bypass blocked", b, "L1 no mutant cited"))
    # L2b: cited code mutant whose address the instrument never reads
    b = GOOD.replace("MU2-MU3", "MU3-MU4")
    r.append(run("L2b addr not in instrument", b, "L2b MU4 patch addr 0xdeadbe"))
    # L3: digest's row cites only files that do NOT print it; the file that does
    # print it is cited elsewhere in the block (row-scoping must still fail)
    b = ("## M999 (s999) - test block\n\n| claim | evidence | conf |\n|---|---|---|\n"
         "| FACT ONE: x | C1 (`evidence/m999_mutate.txt:1`), MU1 | V |\n"
         "| ACCEPT: digest 0123456789abcdef (`evidence/m999_mutate.txt:1`) | as cited | V |\n"
         "| FACT TWO: y | C2 (`evidence/m999_other.txt:1`), MU2-MU3 | V |\n")
    r.append(run("L3 row-scoped digest", b, "L3 digest 0123456789abcdef"))
    # L3 prose fallback: a bare digest line resolves to the last cited file
    b = GOOD + "\nAcceptance re-run: digest fedcba9876543210 (same harness).\n"
    r.append(run("L3 prose last-file fallback", b, None))
    # L3: digest quoted but printed nowhere
    b = GOOD.replace("0123456789abcdef", "aaaaaaaaaaaaaaaa")
    r.append(run("L3 unprinted digest", b, "L3 digest aaaaaaaaaaaaaaaa"))
    # L4: citation without line
    b = GOOD.replace("`evidence/m999_x.txt:2`), MU1", "`evidence/m999_x.txt`), MU1")
    r.append(run("L4 cite without line", b, "L4 citation without :line"))
    # L4: directory-shaped citation is not matched (no crash, no false cite)
    b = GOOD.replace("(`evidence/m999_x.txt:2`), MU1", "(`evidence/m999_x.txt:2`, evidence/ai_review/), MU1")
    r.append(run("L4 directory not a citation", b, None))
    blk = block_for("## M998 ...\n\n" + GOOD + "\n## M997 ...\n", "m999")
    ok = blk is not None and blk.startswith("## M999") and "M997" not in blk
    print("%-32s %s" % ("block extraction", "OK" if ok else "BAD"))
    r.append(ok)
    n = sum(r)
    print("\n== test_review_lint: %d/%d ==" % (n, len(r)))
    return 0 if n == len(r) else 1

if __name__ == "__main__":
    sys.exit(main())