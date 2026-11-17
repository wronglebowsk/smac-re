#!/usr/bin/env python3
"""M310 mutation harness: prove every repaired gate is LOAD-BEARING (skill law, TRAP 24).

Copies scripts/m310_goal_invalidator.py into a temp file, re-creates by anchor->replacement the
defect each named gate exists to catch, runs the mutant, and REQUIRES that mutant to exit
non-zero with that gate's own id printed RED. A mutation that reddens nothing (or that crashes
the instrument instead of failing the check) is reported. Mutation ids are M1..M9 - deliberately
outside the instrument's A-number namespace (m308_mutate.py precedent).

    python3 -u scripts/m310_mutate.py      # stdout -> evidence/m310_mutate.txt
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTR = os.path.join(ROOT, "scripts/m310_goal_invalidator.py")

MUTATIONS = [
    ("M1 block-loop bound set (block 0 admitted)",
     'cmp8 = [a for a, m_, o_ in win(FUN_LO, FUN_HI) if m_ == "cmp" and o_.endswith(",0x8")]',
     'cmp8 = [0x470BCB]', ["A5"]),
    ("M2 entry-scan bound 0x4b -> 0x19 (SITE bound)",
     'endswith(",0x4b")', 'endswith(",0x19")', ["A7"]),
    ("M3 outer-scan exit target (-> the log tail)",
     'ops(0x470C1A) == "0x470f7e"', 'ops(0x470C1A) == "0x470d86"', ["A14"]),
    ("M4 kind-pair fold seeds swapped (the i==i Ghidra mis-parse)",
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
    for name, anchor, repl, gates in MUTATIONS:
        if src.count(anchor) < 1:
            print("%-58s ANCHOR-MISS %r" % (name, anchor[:40]))
            bad += 1
            continue
        msrc = _inject_path(src.replace(anchor, repl, 1))
        path = os.path.join(tmpdir, "mut.py")
        open(path, "w").write(msrc)
        p = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                           timeout=600, cwd=ROOT)
        reds = red_ids(p.stdout)
        crashed = p.returncode not in (0, 1)
        hit = [g for g in gates if g in reds]
        ok = (p.returncode == 1 and not crashed and hit and
              all(g in reds for g in gates))
        print("%-58s %s rc=%d reddened=%s%s" %
              (name, "OK " if ok else "WEAK", p.returncode,
               ",".join(sorted(reds)) or "-",
               "" if ok else "  (want %s red, rc==1)" % ",".join(gates)))
        if not ok:
            bad += 1
    print("\n%d/%d mutations reddened their target checks" % (len(MUTATIONS) - bad, len(MUTATIONS)))
    if bad:
        print("RESULT: FAIL", file=sys.stderr)
        return 1
    print("RESULT: PASS M310 gates are load-bearing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
