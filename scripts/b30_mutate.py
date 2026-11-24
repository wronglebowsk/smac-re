#!/usr/bin/env python3
"""B30 mutant harness (BUILD_SPINE rung B30, review_lint law: every V row names its mutant).

Re-creates the defects in a SCRATCH TREE (a copy of sim/ with one anchor->replacement applied,
pointing at the repo's evidence/data/programs by symlink) and runs
`python3 -u -m sim.composedfacility` there.  Each mutant declares the gate set it must redden;
the harness exits non-zero unless a mutant reddens EXACTLY its declared (MEASURED) set.  A NO-OP
mutant (identity tree) must redden nothing: that is what proves the comparison bites.
--selftest checks the comparison machinery against a deliberately wrong declaration and a
deliberately void anchor.

CODE mutants break the LAW (the bit orientation, the id guard, the writer's target record, the
disabled-list rule, the writer's inertness) and the INSTRUMENT (the queue-count assert, the
misread source, the rival scoring, the bill's after-side).

Zero box, zero /proc, zero gdb.
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GATE_RE = re.compile(r"^\s*(ok|BAD)\s+(G\d+)\b")
NGATES = 6

MUTANTS = [
    # ---- the law: sim/composedfacility.py ------------------------------------------------
    ("MU1", "sim/composedfacility.py",
     "    out[FAC_OFF + (item >> 3)] |= 1 << (item & 7)",
     "    out[FAC_OFF + (item & 7)] |= 1 << ((item >> 3) & 7)",
     "the setter's orientation SWAPPED (byte item&7, bit item>>3) - the reader's inverse broken"),
    ("MU2", "sim/composedfacility.py",
     "    if not 0 <= item < FAC_BYTES * 8:",
     "    if not 0 <= item < 2 * FAC_BYTES * 8:",
     "the id guard widened to 64 ids (id 39 stamped into an unmeasured byte)"),
    ("MU3", "sim/composedfacility.py",
     "                           base_writes=[(wrong, FAC_OFF + (item >> 3),",
     "                           base_writes=[(idx, FAC_OFF + (item >> 3),",
     "the WRONG-BASE rival aimed at the target record (the rival starts to agree)"),
    ("MU4", "sim/composedfacility.py",
     "    return soco.item_upkeep(table, item, disabled)",
     "    return table[item]",
     "the rule drops M46's disabled list (the bill is repriced without item 8's zeroing)"),
    ("MU5", "sim/composedfacility.py",
     "    m[\"identity_sha_ok\"] = (sow.build_image(sv, bases_override=ov) == sv.data)",
     "    m[\"identity_sha_ok\"] = (sow.build_image(sv, bases_override=ov) == sv.data[:64])",
     "the writer's inertness check made trivially false (the hook's no-write leg unchecked)"),
    # ---- the instrument: EXPECT mutants --------------------------------------------------
    ("MU6", "sim/composedfacility.py",
     "    m[\"n_eligible\"] = sum(1 for r in qrows if r[6])",
     "    m[\"n_eligible\"] = sum(1 for r in qrows if not r[6])",
     "the eligible count inverted (G1's container assert reads the complement)"),
    ("ME2", "sim/composedfacility.py",
     "    m[\"misread_id\"] = tgt[4]",
     "    m[\"misread_id\"] = tgt[3]",
     "the +0x4c misread rival fed the CORRECT id (the rival stops being a rival)"),
    ("ME3", "sim/composedfacility.py",
     "    m[\"rival_constant\"] = [r for r in per_id if r[1] != table[r[0]]]",
     "    m[\"rival_constant\"] = [r for r in per_id if r[1] == table[r[0]]]",
     "the 'table value' rival scored on its AGREEMENTS (the disabled id vanishes)"),
    ("ME4", "sim/composedfacility.py",
     "    m[\"bill_after\"] = bill(reload_b)",
     "    m[\"bill_after\"] = bill(orig)",
     "the bill's AFTER side read off the UNCHANGED record (the delta is structurally 0)"),
    # ---- the NO-OP control ---------------------------------------------------------------
    ("MU9", "sim/composedfacility.py",
     "ITEM_LO, ITEM_HI = 1, 31             # the four PINNED bitmap bytes (ids 0..31); 32..38 are",
     "ITEM_LO, ITEM_HI = 1, 31             # the four PINNED bitmap bytes (ids 0..31; no-op mutant); 32..38 are",
     "identity mutant: the tree must redden NOTHING"),
]

# Filled from `--measure` (s321): the sets this harness MEASURED, not the ones hoped for.
# Every gate G1..G6 is reddened by at least one mutant; MU9 (identity) reddens nothing.
DECLARED = {
    "MU1": {"G2", "G3", "G4", "G5", "G6"},
    "MU2": {"G2", "G6"},
    "MU3": {"G4", "G6"},
    "MU4": {"G5", "G6"},
    "MU5": {"G4", "G6"},
    "MU6": {"G1", "G6"},
    "ME2": {"G6"},
    "ME3": {"G5", "G6"},
    "ME4": {"G5", "G6"},
    "MU9": set(),
}


def decl_complaints(mid, measured, declared):
    """Pure comparison: every declared-but-unmeasured and measured-but-undeclared gate."""
    out = []
    for g in sorted(declared - measured):
        out.append("%s declares %s but it did not redden it" % (mid, g))
    for g in sorted(measured - declared):
        out.append("%s reddened %s, which it does not declare" % (mid, g))
    return out


def build_tree(dst, target, old, new):
    os.makedirs(dst)
    for name in ("evidence", "data", "programs", "scripts", "docs", "BUILD_SPINE.md"):
        src = os.path.join(ROOT, name)
        if os.path.exists(src):
            os.symlink(src, os.path.join(dst, name))
    shutil.copytree(os.path.join(ROOT, "sim"), os.path.join(dst, "sim"))
    p = os.path.join(dst, target)
    src = open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        raise AssertionError("anchor for %s occurs %d times in %s" % (target, n, target))
    open(p, "w", encoding="utf-8").write(src.replace(old, new))


def run_tree(dst):
    r = subprocess.run([sys.executable, "-u", "-m", "sim.composedfacility"], cwd=dst,
                       capture_output=True, text=True, timeout=900)
    bad, ok = set(), set()
    for line in r.stdout.splitlines():
        g = GATE_RE.match(line)
        if g:
            (bad if g.group(1) == "BAD" else ok).add(g.group(2))
    return bad, ok, r.returncode, (r.stderr or "")[-300:]


def selftest():
    """The comparison machinery must reject a wrong declaration and refuse a void anchor."""
    tmp = tempfile.mkdtemp(prefix="b30_st_")
    try:
        build_tree(os.path.join(tmp, "tree"), "sim/composedfacility.py",
                   "    out[FAC_OFF + (item >> 3)] |= 1 << (item & 7)",
                   "    out[FAC_OFF + (item & 7)] |= 1 << ((item >> 3) & 7)")
        bad, ok, rc, err = run_tree(os.path.join(tmp, "tree"))
        print("ST1 redden set %s rc=%d %s" % (sorted(bad), rc, "PASS" if bad else "FAIL"))
        st1 = bool(bad)
        try:
            build_tree(os.path.join(tmp, "tree2"), "sim/composedfacility.py",
                       "ITEM_LO, ITEM_HI = 7, 9", "x")
            st2 = False
        except AssertionError as e:
            st2 = True
            print("ST2 void anchor rejected: %s" % e)
        wrong = decl_complaints("MU3", {"G4"}, {"G4", "G5"})
        right = decl_complaints("MU3", {"G4"}, {"G4"})
        print("ST4 exact-set comparison rejects a wrong declaration (%d complaints) and "
              "accepts the true one (%d): %s"
              % (len(wrong), len(right), "PASS" if wrong and not right else "FAIL"))
        st4 = bool(wrong) and not right
        print("ST3 no-op tree reddens nothing:", end=" ")
        os.makedirs(os.path.join(tmp, "tree3"))
        for name in ("evidence", "data", "programs", "scripts", "docs"):
            os.symlink(os.path.join(ROOT, name), os.path.join(tmp, "tree3", name))
        shutil.copytree(os.path.join(ROOT, "sim"), os.path.join(tmp, "tree3", "sim"))
        b3, _o3, rc3, _e3 = run_tree(os.path.join(tmp, "tree3"))
        st3 = (not b3) and rc3 == 0
        print("%s (%d BAD, rc=%d)" % ("PASS" if st3 else "FAIL", len(b3), rc3))
        return 0 if (st1 and st2 and st3 and st4) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scripts/b30_mutate.py")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--only", default=None, help="run a subset by id (MU1,ME2)")
    ap.add_argument("--measure", action="store_true",
                    help="print the MEASURED sets as a DECLARED literal and exit 0 (no asserts)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    ids = set(a.only.split(",")) if a.only else None
    results, digests = [], []
    tmp = tempfile.mkdtemp(prefix="b30_mut_")
    guards = []
    try:
        # GUARD 0: an UNMUTATED tree must run green, or "a mutant reddens G<n>" measures nothing
        base = os.path.join(tmp, "BASE")
        build_tree(base, "sim/composedfacility.py",
                   "ITEM_LO, ITEM_HI = 1, 31             # the four PINNED bitmap bytes (ids 0..31); 32..38 are",
                   "ITEM_LO, ITEM_HI = 1, 31             # the four PINNED bitmap bytes (no-op baseline); 32..38 are")
        bbad, _bok, brc, berr = run_tree(base)
        if brc != 0 or bbad:
            guards.append("the unmutated tree is not green (rc=%d, BAD %s)" % (brc, sorted(bbad)))
        print("BASE unmutated tree rc=%d BAD %s" % (brc, sorted(bbad) or "none"))
        for (mid, target, old, new, why) in MUTANTS:
            if ids and mid not in ids:
                continue
            dst = os.path.join(tmp, mid)
            build_tree(dst, target, old, new)
            bad, ok, rc, err = run_tree(dst)
            results.append((mid, why, bad, rc, err))
            if "Traceback" in (err or ""):
                guards.append("%s CRASHED (a crash is not a reddened gate)" % mid)
            if mid != "MU9" and not bad:
                guards.append("%s reddened nothing and is not the declared NO-OP" % mid)
            digests.append(hashlib.sha256(("%s|%s" % (mid, ",".join(sorted(bad))))
                                          .encode()).hexdigest())
            print("%s reddens %s rc=%d %s" % (mid, sorted(bad) or "nothing", rc,
                                              "" if bad or mid == "MU9" else err.strip()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if a.measure:
        print("DECLARED = {")
        for (mid, why, bad, rc, err) in results:
            print('    "%s": {%s},   # %s' % (mid, ", ".join('"%s"' % g for g in sorted(bad)),
                                              why))
        print("}")
        return 0
    complaints = list(guards)
    for (mid, why, bad, rc, err) in results:
        if mid not in DECLARED:
            complaints.append("%s has no declared set" % mid)
            continue
        complaints += decl_complaints(mid, bad, set(DECLARED[mid]))
    for c in complaints:
        print("BAD  " + c)
    total_reddened = set()
    for (mid, why, bad, rc, err) in results:
        total_reddened |= bad
    unseen = {"G%d" % i for i in range(1, NGATES + 1)} - total_reddened
    if unseen:
        complaints.append("no mutant reddens %s" % sorted(unseen))
    digest = hashlib.sha256("|".join(digests).encode()).hexdigest()[:16]
    if complaints:
        for c in complaints:
            print("BAD  " + c)
        print("FAIL HARNESS B30: %d complaints, digest %s" % (len(complaints), digest))
        return 1
    print("PASS HARNESS B30: %d/%d mutants redden exactly their declared sets, digest %s"
          % (len(results), len(results), digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
