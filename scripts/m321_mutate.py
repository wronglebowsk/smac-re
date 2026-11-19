#!/usr/bin/env python3
"""M321 mutation harness (TRAP 24 / the s290 claim->mutant law): every gate the census
ships must BITE on a real state, or it is decoration.

Two families, as in M319 #317:
  (1) SOURCE mutants MU1-MU4 - rewrite one classifier/bound/clobber-rule in
      scripts/m321_memo_owners.py so a printed claim becomes false on the real bytes.
      MU1 is the defect actually found and fixed while writing this census (a store
      detector that only read the `mov DWORD PTR ds:X,reg` face and silently missed the
      a3-encoded `mov ds:X,reg` stores); MU4 is the caller-saved-clobber rule.
  (2) CODE mutants MU5-MU13 - run the census against a REWRITTEN DISASSEMBLY
      (env M321_PATCH="addr|mnemonic ops;..."), i.e. change the CODE the census reads,
      including mutants that BUILD the rival it must reject (a unit-array fold, a
      look-alike arrival test on the neighbouring field, a second setter of bit 0x40).

Every mutant must redden EXACTLY its declared gate set: a missing red is a decorative
assert, an extra red is an undeclared dependency, a crash is not a red. The baseline must
be green or the run refuses. DECLARED SETS ARE MEASURED (PASS 1 ran with every set EMPTY),
never authored.

  python3 -u scripts/m321_mutate.py            # full sweep (sets as declared below)
  python3 -u scripts/m321_mutate.py --measure  # print measured sets, assert nothing
  python3 -u scripts/m321_mutate.py --only MU3,MU9
"""
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "scripts", "m321_memo_owners.py")
TEXT = os.path.join(REPO, "scratch", "m574", "text.txt")
EXE = os.path.join(REPO, "programs", "terran.exe")
IDXCSV = os.path.join(REPO, "ghidra_out", "index.csv")
GATE_RX = re.compile(r"^FAIL (G\d+)", re.M)
src = open(SRC).read()

# (id, what it breaks, kind, source-old, source-new, code-patch, declared reddened set)
MUT = [
    ("MU1", "store detector reads only the long `mov DWORD PTR ds:X,reg` face -> misses "
            "every a3-encoded store (the pre-fix defect)", "src",
     '    first = op.split(",")[0].strip()\n    if first.startswith("ds:"):\n'
     '        return ds_of(first) == target\n    return first.startswith',
     '    first = op.split(",")[0].strip()\n    return first.startswith', "", ("G2", "G7")),
    ("MU2", "the refresh pair is accepted in EITHER order (M318's order law is decoration)",
     "src", "and hits[0][1] < hits[1][1])", "and hits[1][1] < hits[0][1])", "", ("G2",)),
    ("MU3", "the arrival matcher accepts any test on [reg+0x38], not the 0x40 mask (the "
            "'shared arrival test' claim becomes a shape match)", "src",
     'if d == 0x38 and r and "BYTE" in m[1] and m[1].rstrip().endswith(",0x40"):',
     "if d == 0x38 and r:", "", ("G4", "G7")),
    # MU4 is a DECLARED HARNESS NO-OP: measured (PASS 1) to redden nothing, i.e. the
    # caller-saved clobber rule is not load-bearing on this corpus (every one of the 108
    # [reg+0x38] sites finds its def before any call). The NO-OP is asserted, not deleted:
    # the declared set is EMPTY, so the day it reddens anything the harness FAILS.
    ("MU4", "back_def ignores that a CALL kills eax/ecx/edx (caller-saved clobber)", "src",
     '        if mn == "call":\n            if reg in CLOBBER:\n'
     "                return None\n            continue\n",
     '        if mn == "call":\n            continue\n', "", ()),
    ("MU5", "ds:0x8f0d60 is fed by the UNIT array base, not base_array", "code", None, None,
     "4e3484|add edx,0x933278", ("G1",)),
    ("MU6", "the fold multiplies by 608, not 304 (shl 0x4 -> 0x5)", "code", None, None,
     "4e3481|shl edx,0x5", ("G1",)),
    ("MU7", "FUN_004f41f0's second memo store is really an index store (a3 form)", "code",
     None, None, "4f44a8|mov ds:0x68cbb0,eax", ("G2", "G7")),
    ("MU8", "the refresh pair at 0x4ee6c9 runs in the wrong order", "code", None, None,
     "4ee6cf|call 0x4e92c0", ("G2",)),
    ("MU9", "one arrival test is on the NEIGHBOURING field +0x30 (a look-alike rival)",
     "code", None, None, "416f32|test BYTE PTR [eax+0x30],0x40", ("G4", "G7")),
    ("MU10", "the arrival test's register is loaded from an unrelated global", "code",
     None, None, "416f2a|mov eax,ds:0x8f0c64", ("G4",)),
    ("MU11", "bit 0x40 has no setter (the OR writes 0x41 instead)", "code", None, None,
     "41ac34|or DWORD PTR [eax+0x38],0x41", ("G5",)),
    ("MU12", "the callee's own gate is on a different bit", "code", None, None,
     "4f43a0|test cl,0x20", ("G6",)),
    ("MU13", "FUN_004ee410's STARVE label is really the talent label (the families would "
             "be the same routine's)", "code", None, None, "4ee4fc|push 0x68d228", ("G3",)),
]


def run(patchenv=None, src_text=None):
    env = dict(os.environ, M321_TEXT=TEXT, M321_EXE=EXE, M321_INDEX=IDXCSV, PYTHONUNBUFFERED="1")
    if patchenv:
        env["M321_PATCH"] = patchenv
    path = SRC
    tmp = None
    if src_text is not None:
        fd, tmp = tempfile.mkstemp(prefix="m321_", suffix=".py", dir=os.path.join(REPO, "scripts"))
        with os.fdopen(fd, "w") as f:
            f.write(src_text)
        path = tmp
    try:
        p = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                           env=env, timeout=600)
    finally:
        if tmp:
            os.unlink(tmp)
    out = p.stdout + p.stderr
    if p.returncode not in (0, 1):
        return "CRASH", out
    return sorted(set(GATE_RX.findall(out))), out


def main():
    measure = "--measure" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    base, out = run()
    if base != []:
        print("BASELINE IS NOT GREEN - refusing to sweep. Fails: %s" % base)
        print(out[-2000:])
        return 2
    print("baseline: PASS (7/7 gates) - every mutant below must redden exactly its set")
    bad = []
    for mid, what, kind, sold, snew, patch, declared in MUT:
        if only and mid not in only:
            continue
        if kind == "src":
            if sold not in src:
                print("%s %s BADANCHOR (the source mutant no longer applies)" % (mid, what))
                bad.append(mid)
                continue
            got, o = run(src_text=src.replace(sold, snew, 1))
        else:
            got, o = run(patchenv=patch)
        if got == "CRASH":
            print("%s %s CRASH (a crash is not a red)" % (mid, what))
            print("   " + o.strip().splitlines()[-1][:160])
            bad.append(mid)
            continue
        if measure:
            print("%s measured=%s :: %s" % (mid, got, what))
            continue
        if tuple(got) != tuple(declared):
            print("%s WRONG SET: declared %s measured %s :: %s"
                  % (mid, list(declared), got, what))
            bad.append(mid)
            continue
        print("%s redden %s OK :: %s" % (mid, got or "NOTHING", what))
    if measure:
        print("-- M321_MUTATE: measure pass (asserts nothing) --")
        return 0
    if bad:
        print("FAIL M321_MUTATE: %d/%d mutants wrong" % (len(bad), len(MUT)))
        return 1
    print("PASS M321_MUTATE: %d/%d mutants each redden exactly their declared gate set"
          % (len(MUT), len(MUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
