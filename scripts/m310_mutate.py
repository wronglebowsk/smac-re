#!/usr/bin/env python3
"""M310 mutation harness: prove every repaired gate is LOAD-BEARING (skill law, TRAP 24).

Copies scripts/m310_goal_invalidator.py into a temp file, re-creates by anchor->replacement the
defect each named gate exists to catch, runs the mutant, and REQUIRES that mutant to exit
non-zero with that gate's own id printed RED. A mutation that reddens nothing (or that crashes
the instrument instead of failing the check) is reported. Mutation ids are M1..M9 - deliberately
outside the instrument's A-number namespace (m308_mutate.py precedent).

The unmutated instrument is run FIRST and must exit 0, or nothing is scored; a mutant only
earns credit if it exits 1, prints its named gate RED, prints the 'RESULT: FAIL (n red)' summary,
and prints NO traceback (an uncaught exception also exits 1, and the RED lines print before dying).
M12-M14 mutate the ENGINE's parsed instruction (M._INS), not a literal in the source - that is how
the instruction-by-instruction hit-test gate A10/A24 is shown to be load-bearing.

    python3 -u scripts/m310_mutate.py      # stdout -> evidence/m310_mutate.txt
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTR = os.path.join(ROOT, "scripts/m310_goal_invalidator.py")

# Anchor = the FIRST line of the instrument's hit-chain comparison (a full line, so the leading
# four spaces of indentation survive the replacement - anchoring mid-line dedents the mutant and
# it dies with an IndentationError, which the harness correctly refuses to credit).
ANCHOR12 = '    bad = [(hex(a), "%s %s" % (mn(a), ops(a)), "%s %s" % (mm, oo))'
# Rewrite = corrupt the ENGINE'S PARSED INSTRUCTION before that comparison runs, i.e. the mutation
# is the defect the gate exists to catch, not an edit of a literal the gate happens to read.
def rewrite(addr, mo, ops_expr):
    # The anchor INCLUDES the four-space indent, and str.replace consumes it, so the injected line
    # must carry its own indent or the mutant dies on an IndentationError (which is correctly
    # scored WEAK, not OK).
    return '    M._INS[%s] = ("%s", %s)\n' % (addr, mo, ops_expr) + ANCHOR12


MUTATIONS = [
    ("M1 block-loop bound set (block 0 admitted)",
     'cmp8 = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "cmp" and o_.endswith(",0x8")]',
     'cmp8 = [0x470BCB]', ["A5"]),
    ("M2 entry-scan bound 0x4b -> 0x19 (SITE bound)",
     'endswith(",0x4b")', 'endswith(",0x19")', ["A7"]),
    ("M3 outer-scan exit target (-> the log tail)",
     'ops(0x470C1A) == "0x470f7e"', 'ops(0x470C1A) == "0x470d86"', ["A14"]),
    ("M4 kind-pair fold seeds swapped (one index for both kinds)",
     'inner_fold_seed == [("0x470d36", "ecx,DWORD PTR [ebp-0x10]")]',
     'inner_fold_seed == [("0x470d1f", "ecx,DWORD PTR [ebp-0xc]")]', ["A14"]),
    ("M5b store-target fold re-seeded from the INNER index (writes j, not i)",
     'store_fold_seed == [("0x470d56", "edx,DWORD PTR [ebp-0xc]")]',
     'store_fold_seed == [("0x470d56", "edx,DWORD PTR [ebp-0x10]")]', ["A14"]),
    ("M6 gate bit 0x2000 -> 0x80 (gates on the wrong flag)",
     "and2000 = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == \"and\" and o_.endswith(\"0x2000\")]",
     "and2000 = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == \"and\" and o_.endswith(\"0x80\")]",
     ["A4"]),
    ("M7 default-table entries 7 -> 0 (unvalidated byte index)",
     "btab = list(JT_BYTES[32:74])",
     "btab = [0 if v == 7 else v for v in list(JT_BYTES[32:74])]", ["A17"]),
    ("M8 argument order read reversed (arg1 became arg2 - the m309 bug)",
     'ops(0x470BBB) == "ecx,DWORD PTR [ebp+0xc]"',
     'ops(0x470BBB) == "ecx,DWORD PTR [ebp+0x8]"', ["A11"]),
    ("M9 inner-sites counted as outer (one index variable for both scans)",
     're.match(r"\\w+,DWORD PTR " + re.escape(slot) + r"$", o_)]',
     're.match(r"\\w+,DWORD PTR \\[ebp-0x[0-9a-f]+\\]", o_)]', ["A8"]),
    ("M11 sentinel value read wrong (0xffff -> 0x0000)",
     'word_stores == [(hex(SENT_STORE), "WORD PTR [ecx+edx*1+0x94ee28],0xffff")]',
     'word_stores == [(hex(SENT_STORE), "WORD PTR [ecx+edx*1+0x94ee28],0x0")]', ["A13"]),
    ("M10 forwarded slots changed (the site-5 unpacked-pair law)",
     'sorted(["[ebp-0x18]", "[ebp-0x1c]"])', 'sorted(["[ebp-0x18]", "[ebp-0x14]"])', ["A12"]),
    ("M12 prio==0 test flipped to jle (zero-prio entries reach the duplicate path)",
     ANCHOR12, rewrite("0x470C90", "jle", "M._INS[0x470C90][1]"), ["A10"]),
    ("M13 free-slot skip flipped to jle (kind=-1 admitted)",
     ANCHOR12, rewrite("0x470C73", "jle", "M._INS[0x470C73][1]"), ["A10"]),
    ("M14 reject edge retargeted into the log tail (skeleton, not condition)",
     ANCHOR12, rewrite("0x470C92", "jmp", '"0x470d86"'), ["A24"]),
]


def _inject_path(src):
    return src.replace(
        'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))',
        'sys.path.insert(0, %r)' % os.path.join(ROOT, "scripts"))


def red_ids(text):
    ids = set()
    for line in text.splitlines():
        m = re.match(r"\s+(A\d+b?|RIVALS-\S+)\s+RED\s*$", line)
        if m:
            ids.add(m.group(1))
        m2 = re.match(r"\s+(A\d+b?)\s+RED ", line)
        if m2:
            ids.add(m2.group(1))
    return ids


def main():
    src = open(INSTR).read()
    tmpdir = tempfile.mkdtemp(prefix="m310mut_")
    bad = 0
    # BASELINE FIRST (Greptile P2, s272): a mutant whose target check was ALREADY red earns
    # unearned credit. Refuse to score anything unless the unmodified instrument passes.
    b = subprocess.run([sys.executable, "-u", _materialise(tmpdir, src, "base")],
                       capture_output=True, text=True, timeout=600, cwd=ROOT)
    if b.returncode != 0:
        print("BASELINE instrument EXIT=%d - refusing to score mutations" % b.returncode)
        print("RESULT: FAIL (baseline not green)", file=sys.stderr)
        return 1
    print("%-58s baseline green rc=0" % "M0 unmutated instrument")
    for name, anchor, repl, gates in MUTATIONS:
        if src.count(anchor) < 1:
            print("%-58s ANCHOR-MISS %r" % (name, anchor[:40]))
            bad += 1
            continue
        msrc = _inject_path(src.replace(anchor, repl, 1))
        path = _materialise(tmpdir, msrc, "mut")
        p = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                           timeout=600, cwd=ROOT)
        reds = red_ids(p.stdout)
        # A crash is NOT a failure (Greptile P2, s272): an uncaught exception also exits rc=1, and
        # the instrument prints its RED lines before dying, so rc==1 alone credits a broken mutant.
        # The failure SUMMARY goes to stderr while the PASS line goes to stdout - check both.
        trace = "Traceback (most recent call last)" in (p.stderr or "")
        combined = (p.stdout or "") + (p.stderr or "")
        summary_ok = bool(re.search(r"RESULT: FAIL \(\d+ checks? red\)", combined)) and bool(reds)
        crashed = p.returncode not in (0, 1) or trace
        ok = (p.returncode == 1 and not crashed and summary_ok and
              all(g in reds for g in gates))
        print("%-58s %s rc=%d reddened=%s%s" %
              (name, "OK " if ok else "WEAK", p.returncode,
               ",".join(sorted(reds)) or "-",
               "" if ok else "  (want %s red + a 'RESULT: FAIL (n red)' summary, no traceback)"
                             % ",".join(gates)))
        if not ok:
            bad += 1
    print("\n%d/%d mutations reddened their target checks" % (len(MUTATIONS) - bad, len(MUTATIONS)))
    if bad:
        print("RESULT: FAIL", file=sys.stderr)
        return 1
    print("RESULT: PASS M310 gates are load-bearing")
    return 0


def _materialise(tmpdir, msrc, tag):
    path = os.path.join(tmpdir, tag + ".py")
    open(path, "w").write(_inject_path(msrc) if "sys.path.insert" in msrc else msrc)
    return path


if __name__ == "__main__":
    sys.exit(main())
