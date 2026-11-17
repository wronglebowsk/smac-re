#!/usr/bin/env python3
"""M311 mutation harness - prove each gate of scripts/m311_recidx.py is LOAD-BEARING.

Each mutant re-introduces the exact defect the assertion exists to catch, by corrupting the
UNDERLYING FACT (the parsed instruction, the fold arithmetic, the address constant, the store
list), never a literal the prose happens to mention.  Scoring rules (s272/s273 law):
  0. the UNMUTATED instrument must exit 0 first, or nothing is scored;
  1. a mutant that dies with a traceback gets NO credit even though it exits 1;
  2. the FAIL summary is searched in stdout AND stderr (instruments print PASS to stdout and
     the FAIL line to stderr).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "m311_recidx.py")
OUT = os.path.join(HERE, "..", "scratch", "m311_mut")

# (id, what defect it re-introduces, which gate must go red, old, new)
MUTS = [
    ("MU1", "the fold shift is a different width (0x4 -> 0x5): the stride stops being 304",
     "A3", "fold_val = lambda n: (((n + (n + n * 8) * 2) << 4))",
     "fold_val = lambda n: (((n + (n + n * 8) * 2) << 5))"),
    ("MU2", "the transcribed pointer-store list omits a real store (the s274 mis-count)",
     "A2", '    (0x4f21f9, "FUN_004ef6d0", "ecx"),   # this fire re-found it: the census print scrolled past\n',
     "")
    ("MU3", "the census under-counts a store site: 6 stores become 5",
     "A1", '    (0x4e4dd0, "FUN_004e47d0", "esi"),\n]', ']\n'),
    ("MU4", "the fold matcher stops attributing a fold to its site (distance cap 24 -> 4096 B)",
     "A3", "and a3 - a1 <= 24:", "and a3 - a1 <= 4096:"),
    ("MU12", "the fold matcher accepts a different shift width as the third step",
     "A3", 'if m3 == "shl" and o3.endswith(",0x4")', 'if m3 == "shl" and o3.endswith(",0x5")'),
    ("MU5", "the array base is mis-stated (0x95da10 -> 0x95da40): the +48 identity dies",
     "A4", "REC_BASE = 0x95da10   # the 304-B array whose element the pointer is",
     "REC_BASE = 0x95da40   # the 304-B array whose element the pointer is"),
    ("MU6", "the fold's second lea is not a lea: the encoding no longer says *2",
     "A3", '    (0x4efe8e, "FUN_004ef6d0", "esi"),',
     '    (0x4efe8e, "FUN_004ef6d0", "esi"),\n# MU6 rewrites the encoding below'),
    ("MU7", "the pointer global is given the wrong address: the store census finds nothing",
     "A2", "PTR = 0x8f0d60        # the record pointer this fire names",
     "PTR = 0x8f0d64        # the record pointer this fire names"),
    ("MU8", "the adjacent dword's store count is asserted high (the decoration this gate REFUSES)",
     "A7", "a7 = (len(last_stores) == 22 and len(in_window) == 3",
     "a7 = (len(last_stores) == 6 and len(in_window) == 6"),
    ("MU9", "the census constant is decoration: assert 999 refs instead of the measured 340",
     "A5", "N_IDX_REFS = 340      # printed by name_global.py", "N_IDX_REFS = 999      # printed by name_global.py"),
    ("MU10", "write-detection is blind: the index would read as a write-only-once field",
     "A5", '    if mn.startswith("mov") and ("ds:0x%x" % IDX) in head:',
     '    if mn.startswith("mov") and ("ds:0x%x" % IDX) in head and False:'),
    ("MU11", "the setter's recorded caller count is asserted as 58 (index.csv says 57)",
     "A6", "and c_setter == 57", "and c_setter == 58"),
]


# MU6's real edit: rewrite one parsed instruction so the fold is incomplete
MU6_PATCH = ('MU6: rewrite the parsed instruction at 0x4f5a87 so the *2 step is a plain mov',
             'def main():\n    ins, order, rows = load()',
             'def main():\n    ins, order, rows = load()\n'
             '    ins[0x4f5a87] = ("mov", "eax,ebx")   # MU6: break the fold\'s second lea')


def run(text, tag):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "m311_%s.py" % tag)
    # The copy lives outside scripts/, so it must be told where the shared engine is or it
    # dies on ModuleNotFoundError - and a traceback baseline is exactly what the scoring
    # rules refuse to credit.
    text = text.replace('sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))',
                        'sys.path.insert(0, %r)' % HERE)
    with open(path, "w") as f:
        f.write(text)
    r = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                       timeout=300, cwd=os.path.dirname(SRC))
    combined = r.stdout + r.stderr
    trace = "Traceback (most recent call last)" in combined
    red = re.search(r"RESULT: FAIL \((\d+)/(\d+) gates bad", combined)
    bad_ids = re.findall(r"\n  BAD  (A\d+)", combined)
    return r.returncode, trace, bool(red), sorted(set(bad_ids)), combined


def main():
    src = open(SRC).read()
    rc, trace, red, bad, out = run(src, "base")
    print("M0 unmutated instrument: rc=%d trace=%s -> %s"
          % (rc, trace, "baseline green" if (rc == 0 and not trace) else "NOT GREEN"))
    if rc != 0 or trace:
        print("REFUSING TO SCORE: the baseline instrument is not green.")
        print(out[-1500:])
        return 1

    hits = 0
    for mid, why, gate, old, new in MUTS:
        text = src.replace(old, new, 1)
        if mid == "MU6":
            _, anchor, repl = MU6_PATCH
            assert anchor in src, "MU6 anchor missing"
            text = text.replace(anchor, repl, 1)
        if text == src:
            print("%s %-70s NO-OP ANCHOR - not counted" % (mid, why))
            continue
        rc, trace, red, bad, out = run(text, mid)
        ok = (rc != 0 and not trace and red and gate in bad)
        hits += 1 if ok else 0
        print("%s %-70s %s rc=%d trace=%s red=%s"
              % (mid, why, "LOAD-BEARING (reddens %s)" % ",".join(bad) if ok
                 else "WEAK - gate %s stayed green" % gate, rc, trace, bad))
    print("\n%d/%d mutations load-bearing" % (hits, len(MUTS)))
    return 0 if hits == len(MUTS) else 1


if __name__ == "__main__":
    sys.exit(main())
