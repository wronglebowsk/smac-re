#!/usr/bin/env python3
"""M308 (STATIC, zero box): is the repaired gate actually load-bearing?

Greptile #281 returned four P2s on m308_site_list.py, all one shape: an assertion that could PASS
ON AN UNMEASURED STATE (a classifier blind to direct `ds:` operands; bounds/steps pre-filtered to
the expected constants; a max/evict rule tested by mnemonic presence; a "mirror" proved by
instruction proximity). Repairing an assertion proves nothing by itself - this harness mutates the
instrument back into each defect, and into vacuity states where the extraction returns nothing,
and reports which checks go RED on the REAL disassembly.

A mutation that reddens nothing means the check is decorative and the fix is a lie.

    python3 scripts/m308_mutate.py        # exit 0 only if every mutation reddens its target
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts/m308_site_list.py")
# the mutants must sit exactly ONE directory below ROOT: the instrument derives its data paths
# from dirname(dirname(__file__)), so a deeper copy cannot find scratch/m574/text.txt
TMP = os.path.join(ROOT, "scratch")

# (id, defect re-created, unique anchor in the instrument, replacement, checks that MUST go red)
# Each mutation perturbs a MEASURED fact so it is false on the real bytes; if a check does not
# notice, that check never read the fact and is decorative.
MUTATIONS = [
    ("M1", "P2a: the classifier cannot see a direct `ds:` operand (the debug-flag read inside "
           "FUN_0056d480 becomes invisible, and A4's window claim becomes an over-claim)",
     '                m4 = re.match(r"^(DWORD|WORD|BYTE) PTR ds:(0x[0-9a-f]+)$", tok) or \\\n'
     '                    re.match(r"^ds:(0x[0-9a-f]+)$", tok)',
     "                m4 = None",
     ["A4", "A4b"]),
    ("M2", "the classifier sees the direct global but FILES it inside the site window",
     'acc.append((a, mn, w, g, None, "ds:" + hex(g)[2:], "global", is_st))',
     'acc.append((a, mn, w, g, None, "ds:" + hex(g)[2:], "site", is_st))',
     ["A4", "A4b", "A5"]),
    ("M3", "P2b: a loop is any jcc, forward ones included, so the back-edge definition stops "
           "carrying information",
     "            if not (lo <= t <= a):\n                continue",
     "            if False:\n                continue",
     ["A12"]),
    ("M4", "P2c: the max law stops comparing the jg's TARGET with the instruction after the "
           "fallback move (off-by-one in the comparison, so the fact is measured but wrong)",
     '        "jg_target_is_just_past_fallback": bool(jc1[0] and fbk[0] and\n'
     '                                                int(jc1[2].strip(), 16) == succ(fbk[0])),',
     '        "jg_target_is_just_past_fallback": bool(jc1[0] and fbk[0] and\n'
     '                                                int(jc1[2].strip(), 16) == succ(fbk[0]) + 1),',
     ["A9"]),
    ("M5", "P2c: the eviction strictness is read as `jl` instead of `jle` (a tie would then replace "
           "the best index - the whole point of the law)",
     '        "strict_is_jle_not_jl": strict[1] == "jle",',
     '        "strict_is_jle_not_jl": strict[1] == "jl",',
     ["A10"]),
    ("M6", "the tie rule stops checking that the jle target is one past BOTH update stores",
     '        all(x[0] < tgt for x in upd) and succ(upd[-1][0]) == tgt,',
     '        all(x[0] < tgt for x in upd) and succ(upd[-1][0]) + 1 == tgt,',
     ["A10"]),
    ("M7", "A11 scans the wrong run for stores on the taken path (the found path, which does "
           "store) - i.e. the store-free-epilogue requirement is dropped",
     "        for a, m, o in window(tgt_nc, FUN_480[1]):",
     "        for a, m, o in window(0x56D59F, FUN_480[1]):",
     ["A11"]),
    ("M8", "P2d: the def-walk is replaced by the old proximity rule (whatever global sits within "
           "10 instructions becomes the source)",
     '        srcs, chain = def_globals(a, src_reg, lo, hi) if src_reg else ({"unparsed"}, [])',
     '        srcs, chain = {"proximity"}, [x for x in around(a)]',
     ["A27", "A28", "A28b", "A28c"]),
]


def checks_of(stdout):
    bad, total, inblk = set(), 0, False
    for line in stdout.splitlines():
        if line.strip() == "[CHECKS]":
            inblk = True
            continue
        if inblk:
            if line.startswith("   OK  ") or line.startswith("   FAIL"):
                total += 1
                if line.startswith("   FAIL"):
                    bad.add(line.split()[1])
            elif line.strip().startswith("table sha") or not line.strip():
                inblk = False
    return bad, total


def run(path):
    r = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                       timeout=600, cwd=ROOT)
    return r.stdout + r.stderr, r.returncode


def main():
    src = open(SRC).read()
    os.makedirs(TMP, exist_ok=True)
    base, rc = run(SRC)
    if rc != 0:
        print("BASELINE IS RED - nothing to compare against:")
        print(base[-1500:])
        return 1
    bbad, btot = checks_of(base)
    sha = re.search(r"table sha (\w+)", base)
    print("baseline: %d checks, %d red, table sha %s" % (btot, len(bbad), sha and sha.group(1)))
    if bbad:
        return 1
    rows = []
    for mid, name, old, new, must in MUTATIONS:
        if old not in src:
            print("\n%s ANCHOR MISSING - this mutation no longer describes the instrument: %r"
                  % (mid, old[:60]))
            return 1
        path = os.path.join(TMP, "%s.py" % mid)
        open(path, "w").write(src.replace(old, new, 1))
        out, rc2 = run(path)
        bad, _tot = checks_of(out)
        if rc2 != 0 and not bad:
            bad = {"(instrument crashed)"}
        red = sorted(bad)
        ok = bool(red) and all(m in bad for m in must)
        rows.append((mid, name, must, red, ok))
    print("\n[MUTATIONS: each must redden its named checks]")
    for mid, name, must, red, ok in rows:
        print("   %s %-3s %-72s\n        must redden %s -> actually red: %s"
              % ("OK  " if ok else "FAIL", mid, name[:72], must, red or "NOTHING"))
    n_ok = sum(1 for r in rows if r[4])
    print("\n%d/%d mutations reddened their target checks" % (n_ok, len(rows)))
    if n_ok != len(rows):
        print("RESULT: FAIL - a defect survived the repair (a decorative gate)")
        return 1
    print("RESULT: PASS M308 gates are load-bearing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
