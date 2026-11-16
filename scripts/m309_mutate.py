#!/usr/bin/env python3
"""M309 (STATIC, zero box): are the m309_goal_sink.py gates load-bearing?

Trap 24 (s269, Greptile #281): a PASSING assertion is not a gate. m309_goal_sink.py prints 52/52
OK - which proves nothing about the 10 checks that run through EXTRACTION code (the push-group
walk, the block-window census, the affine trackers, the store classifier) until each defect that
those checks exist to catch is re-created and shown to redden its named check on the REAL dump.

Each mutation rewrites one anchor in a copy of the instrument; the copy runs against the same
scratch/m574/text.txt. A mutation that reddens nothing means the check never read the fact.

  M1 the arg6 selection is the reversed-index bug this instrument actually shipped with once
  M2 the block-window census filters to entry 0 only (vacuity)
  M3 the census's read/write polarity is decided on the wrong operand slot
  M4 the affine tracker stops treating `mov r,DWORD PTR [ebp+0x8]` as the symbolic parameter
  M5 a "loop" is any jcc, forward ones included (the back-edge definition stops carrying meaning)
  M6 the reader-of-+0C chain loses its seed, so no scale can be computed (vacuity)
  M7 a DIRECT `ds:` store stops counting as a write (the M308 P2a defect, re-created here)
  M8 the found-path store census scans past the found path's ret
  M9 vacuity of the whole instrument: an empty disassembly table

    python3 scripts/m309_mutate.py      # exit 0 only if EVERY mutation reddens its target
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts/m309_goal_sink.py")
# the mutants must sit NEXT TO m308_site_list.py: the instrument imports that engine by
# sys.path of its own directory, and a copy elsewhere cannot resolve it
TMP = os.path.join(ROOT, "scripts")

MUTATIONS = [
    ("M1", "arg6 is taken as the LAST push found instead of the FIRST of the group (the reversal "
           "bug: it silently reports arg1, the record index)",
     "        a6, a5, a4, a3, a2, a1 = [x[1] for x in ps]",
     "        a1, a2, a3, a4, a5, a6 = [x[1] for x in ps]",
     ["A32", "A33"]),
    ("M2", "the block-window census narrows to the first 16 bytes, so it measures almost nothing "
           "and A36's 'exactly 1 write / 1 read' becomes a claim about a filtered set",
     "                if not (GOAL_BASE <= dv < BLOCK_HI):",
     "                if not (GOAL_BASE <= dv < GOAL_BASE + 0x10):",
     # A43 is deliberately NOT expected here: both +0 writers name displacement 0x94ee28
     # exactly, so narrowing the range to the first 16 bytes cannot change them. A43's own
     # liveness proof is M3 (polarity), which does redden it.
     ["A37"]),
    ("M3", "the read/write decision looks at operand slot 1 instead of slot 0",
     '                is_w = idx == 0 and mn in ("mov", "movzx", "movbe", "xchg")',
     '                is_w = idx == 1 and mn in ("mov", "movzx", "movbe", "xchg")',
     ["A36", "A37", "A43"]),
    ("M4", "the affine engine stops recognising the callee's first argument, so the record stride "
           "is never derived (A3/A4 become unverifiable)",
     '                if mm and mm.group(2).strip("[]") == "ebp+0x8":',
     "                if False:",
     ["A3", "A4"]),
    ("M5", "a loop is any jcc whose operand is an immediate, forward ones included",
     '            if re.fullmatch(r"0x[0-9a-f]+", tgt) and int(tgt, 16) <= a:',
     '            if re.fullmatch(r"0x[0-9a-f]+", tgt):',
     ["A10"]),
    ("M6", "the +0C reader's multiplier chain loses its seed (no coefficient can be computed, so "
           "the 304-byte stride is asserted out of thin air)",
     '    seed = {"eax": (1, 0)}',
     "    seed = {}",
     ["A38"]),
    ("M7", "a DIRECT `ds:` store stops counting as a write (M308 P2a's defect) - 6 writers become 0",
     '            tgt = bool(M.MEM.match(head) and "0x68cbb0" in head) or bool(\n'
     '                re.match(r"^(DWORD|WORD|BYTE) PTR ds:0x68cbb0$", head) or\n'
     '                re.match(r"^ds:0x68cbb0$", head))',
     '            tgt = bool(M.MEM.match(head) and "0x68cbb0" in head)',
     ["A42"]),
    ("M8", "the found-path store census runs past the found path's ret into the insert block, so "
           "'exactly ONE store' stops describing the found path",
     "    fstores = [(a, mn, ops) for a, mn, ops in M.window(0x56D404, 0x56D422)",
     "    fstores = [(a, mn, ops) for a, mn, ops in M.window(0x56D404, 0x56D476)",
     ["A13"]),
    ("M9", "vacuity: an empty disassembly table (nothing can be measured at all)",
     "    M._INS, M._ORDER = M.parse_text()",
     "    M._INS, M._ORDER = {}, []",
     ["(instrument crashed)"]),
]


def reds_of(stdout):
    return set(re.findall(r"^\s+(\S+)\s+RED$", stdout, re.M))


def run(path):
    r = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                       timeout=900, cwd=ROOT)
    return r.stdout + r.stderr, r.returncode


def main():
    src = open(SRC).read()
    base, rc = run(SRC)
    bbad = reds_of(base)
    tot = re.search(r"(\d+)/(\d+) checks OK", base)
    print("baseline: %s checks, %d red, rc %d" % (tot and tot.group(2), len(bbad), rc))
    if rc != 0 or bbad:
        print("BASELINE IS RED - nothing to compare against")
        return 1
    rows, made = [], []
    try:
        for mid, name, old, new, must in MUTATIONS:
            n = src.count(old)
            if n != 1:
                print("\n%s ANCHOR NOT UNIQUE (%d) or MISSING - mutation stale: %r" % (mid, n,
                                                                                        old[:60]))
                return 1
            path = os.path.join(TMP, "_m309_mut_%s.py" % mid)
            open(path, "w").write(src.replace(old, new, 1))
            made.append(path)
            out, rc2 = run(path)
            bad = reds_of(out)
            if rc2 != 0 and not bad:
                bad = {"(instrument crashed)"}
            rows.append((mid, name, must, sorted(bad),
                         bool(bad) and all(m in bad for m in must)))
    finally:
        for p in made:
            os.remove(p)
    print("\n[MUTATIONS: each must redden its named checks]")
    for mid, name, must, red, ok in rows:
        print("   %s %-3s %-70s\n        must redden %s -> actually red: %s"
              % ("OK  " if ok else "FAIL", mid, name[:70], must, red or "NOTHING"))
    n_ok = sum(1 for r in rows if r[4])
    print("\n%d/%d mutations reddened their target checks" % (n_ok, len(rows)))
    if n_ok != len(rows):
        print("RESULT: FAIL - a defect survives the gate (a decorative check)")
        return 1
    print("RESULT: PASS M309 gates are load-bearing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
