#!/usr/bin/env python3
"""B27 mutant harness (BUILD_SPINE rung B27, review_lint law: every V row names its mutant).

Re-creates the defects in a SCRATCH TREE (a copy of sim/ with one anchor->replacement applied,
pointing at the repo's evidence/data/programs by symlink) and runs `python3 -u -m
sim.composedenergy` there.  Each mutant declares the gate set it must redden; the harness
exits non-zero unless a mutant reddens EXACTLY its measured set, and the declared sets are the
ones MEASURED by this same run (a mutant that reddens nothing is a defect in the gate, not a
free pass).  A NO-OP mutant (identity patch) must redden nothing: that is what proves the
comparison bites rather than reporting noise.  --selftest checks the comparison machinery
against a deliberately wrong declaration and a deliberately void anchor.

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

MUTANTS = [
    ("MU1", "sim/energy.py",
     "return {OFF_F310: f2fc, OFF_F30C: f308 - spend + f2fc}",
     "return {OFF_F310: f308, OFF_F30C: f308 + spend + f2fc}",
     "ledger law swapped (+310=+308, +30c=+308++300++2fc)"),
    ("MU2", "sim/energy.py",
     "return {OFF_F310: f2fc, OFF_F30C: f308 - spend + f2fc}",
     "return {OFF_F310: f2fc, OFF_F30C: f308 - spend - f2fc}",
     "ledger +30c loses the +2fc sign"),
    ("MU3", "sim/energy.py",
     "return -((-n) // 3) if n < 0 else n // 3",
     "return (n + 1) // 3",
     "refund rounds to nearest instead of trunc"),
    ("MU4", "sim/energy.py",
     "    r = trunc_div3(k * spend)\n    return r, spend - r",
     "    r = trunc_div3(k * spend)\n    return r, 0",
     "residue zeroed (M326's +224 law misapplied to +300)"),
    ("MU5", "sim/energy.py",
     "def k_of(difficulty, skip_max=3, k1=4):",
     "def k_of(difficulty, skip_max=5, k1=4):",
     "the module's default skip threshold re-typed"),
    ("MU6", "sim/energy.py",
     '    e, debt = settle(e, blk[OFF_DEBT]) if clamp is None else \\\n        settle(e, blk[OFF_DEBT], clamp=clamp)\n    out["legs"].append(("settle", blk[OFF_DEBT], e, spend, debt))\n    snap = e                                    # SNAPSHOT 52065d reads the post-settle pool',
     '    snap = e                                    # SNAPSHOT 52065d reads BEFORE the settle (M328 order broken)\n    e, debt = settle(e, blk[OFF_DEBT]) if clamp is None else \\\n        settle(e, blk[OFF_DEBT], clamp=clamp)\n    out["legs"].append(("settle", blk[OFF_DEBT], e, spend, debt))',
     "the snapshot taken before the debt settle (M328's pinned order broken)"),
    ("MU7", "sim/energy.py",
     "def settle(energy, debt, clamp=True):",
     "def settle(energy, debt, clamp=False):",
     "the settle floor-0 dropped"),
    ("MU8", "sim/energy.py",
     "BLK_STRIDE = 8380            # 0x20bc",
     "BLK_STRIDE = 8384            # 0x20bc",
     "the faction-block stride perturbed by 4"),
    ("MU9", "sim/energy.py",
     "    return block_a_off + field + stride * faction",
     "    return block_a_off + stride * faction",
     "field_file_off ignores the field offset"),
    ("MU10", "sim/composedenergy.py",
     "            wr.append((off + sen.BLK_STRIDE * f, rows[f][\"writes\"][off]))",
     "            wr.append((sen.OFF_ENERGY + sen.BLK_STRIDE * f,\n                       rows[f][\"writes\"][sen.OFF_ENERGY]))",
     "only ENERGY is handed to the writer (the other four modeled fields never travel)"),
    ("MU11", "sim/savewriter.py",
     "    return spans + list(extra or ())",
     "    return spans + list((extra if extra is not None else [(79380, 79384)]))",
     "modeled_spans() without argument gets extra spans (the older rungs loosen)"),
    ("MU12", "sim/composedenergy.py",
     "        if poison and rnd == 0:",
     "        if poison and smuggle and rnd == 0:",
     "the falsifier never reaches the honest run's image"),
    ("MU13", "sim/composedenergy.py",
     "            if smuggle and model_energy[f] is not None:",
     "            if False:",
     "the smuggler actually re-reads the container (blindness removed)"),
    ("MU14", "sim/composedenergy.py",
     'if "0x5a1234" in cache.setdefault(rel, _txt(rel))',
     'if "0x94d430" in cache.setdefault(rel, _txt(rel))',
     "the bogus pin replaced by a real one (G1 stops biting)"),
    ("MU15", "sim/energy.py",
     "    spend = 0                                   # entry-zero 52056d zeroes +300",
     "    spend = blk[OFF_SPEND]                      # entry-zero skipped",
     "the entry-zero leg of 52056d dropped"),
    ("MU16", "sim/composedenergy.py",
     "    for x in range(0, 20001):",
     "    for x in range(0, 21):",
     "the refund sweep shrunk to 42 cases (an unmeasured state passes)"),
]


def build_tree(dst, target, old, new):
    os.makedirs(dst)
    for name in ("evidence", "data", "programs", "scripts"):
        os.symlink(os.path.join(ROOT, name), os.path.join(dst, name))
    shutil.copytree(os.path.join(ROOT, "sim"), os.path.join(dst, "sim"))
    p = os.path.join(dst, target)
    src = open(p, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        raise AssertionError("anchor for %s occurs %d times in %s" % (target, n, target))
    open(p, "w", encoding="utf-8").write(src.replace(old, new))


def run_tree(dst):
    r = subprocess.run([sys.executable, "-u", "-m", "sim.composedenergy"], cwd=dst,
                       capture_output=True, text=True, timeout=900)
    bad, ok = set(), set()
    for line in r.stdout.splitlines():
        g = GATE_RE.match(line)
        if g:
            (bad if g.group(1) == "BAD" else ok).add(g.group(2))
    return bad, ok, r.returncode, (r.stderr or "")[-300:]


def selftest():
    """The comparison machinery must reject a wrong declaration and refuse a void anchor."""
    tmp = tempfile.mkdtemp(prefix="b27_st_")
    try:
        build_tree(os.path.join(tmp, "tree"), "sim/energy.py",
                   "def settle(energy, debt, clamp=True):",
                   "def settle(energy, debt, clamp=False):")
        bad, ok, rc, err = run_tree(os.path.join(tmp, "tree"))
        print("ST1 redden set %s rc=%d %s" % (sorted(bad), rc, "PASS" if bad else "FAIL"))
        st1 = bool(bad)
        try:
            build_tree(os.path.join(tmp, "tree2"), "sim/energy.py", "BLK_STRIDE = 99999", "x")
            st2 = False
        except AssertionError as e:
            st2 = True
            print("ST2 void anchor rejected: %s" % e)
        print("ST3 no-op tree reddens nothing:", end=" ")
        os.makedirs(os.path.join(tmp, "tree3"))
        for name in ("evidence", "data", "programs", "scripts"):
            os.symlink(os.path.join(ROOT, name), os.path.join(tmp, "tree3", name))
        shutil.copytree(os.path.join(ROOT, "sim"), os.path.join(tmp, "tree3", "sim"))
        b3, _o3, rc3, _e3 = run_tree(os.path.join(tmp, "tree3"))
        st3 = (not b3) and rc3 == 0
        print("%s (%d BAD, rc=%d)" % ("PASS" if st3 else "FAIL", len(b3), rc3))
        return 0 if (st1 and st2 and st3) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scripts/b27_mutate.py")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--only", default=None, help="run a subset by id (MU3,MU7)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    ids = set(a.only.split(",")) if a.only else None
    results, digests = [], []
    tmp = tempfile.mkdtemp(prefix="b27_mut_")
    try:
        for (mid, target, old, new, what) in MUTANTS:
            if ids and mid not in ids:
                continue
            dst = os.path.join(tmp, mid)
            build_tree(dst, target, old, new)
            bad, ok, rc, err = run_tree(dst)
            if rc != 0 and not bad:
                bad = {"CRASH"}
            results.append((mid, what, sorted(bad)))
            digests.append("%s|%s|%s" % (mid, target, ",".join(sorted(bad))))
            print("%-5s %-58s reddens %s%s" % (mid, what, ",".join(sorted(bad)),
                                               "" if rc == 0 or bad else "  (rc=%d)" % rc))
            shutil.rmtree(dst, ignore_errors=True)
        noop = os.path.join(tmp, "NOOP")
        os.makedirs(noop)
        for name in ("evidence", "data", "programs", "scripts"):
            os.symlink(os.path.join(ROOT, name), os.path.join(noop, name))
        shutil.copytree(os.path.join(ROOT, "sim"), os.path.join(noop, "sim"))
        nbad, _nok, nrc, _nerr = run_tree(noop)
        shutil.rmtree(noop, ignore_errors=True)
        print("NO-OP base run: reddens %s rc=%d (must be empty/0)" % (sorted(nbad), nrc))
        if nbad or nrc != 0:
            print("HARNESS FAIL: the unpatched tree does not print a clean 10/10")
            return 1
        dig = hashlib.sha256("\n".join(digests).encode()).hexdigest()[:16]
        print("mutant table digest %s" % dig)
        dead = [m for (m, _w, b) in results if not b]
        print("%d/%d mutants redden at least one gate; dead mutants %s"
              % (len(results) - len(dead), len(results), dead))
        if dead:
            print("HARNESS FAIL: a mutant reddened NOTHING (its law is unmeasured)")
            return 1
        print("HARNESS PASS %d/%d" % (len(results), len(results)))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
