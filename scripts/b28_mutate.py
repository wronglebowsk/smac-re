#!/usr/bin/env python3
"""B28 mutant harness (BUILD_SPINE rung B28, review_lint law: every V row names its mutant).

Re-creates the defects in a SCRATCH TREE (a copy of sim/ with one anchor->replacement applied,
pointing at the repo's evidence/data/programs by symlink) and runs `python3 -u -m
sim.composedfeeder` there.  Each mutant declares the gate set it must redden; the harness exits
non-zero unless a mutant reddens EXACTLY its measured set, and the declared sets are the ones
MEASURED by this same run.  A NO-OP mutant (identity tree) must redden nothing: that is what
proves the comparison bites rather than reporting noise.  --selftest checks the comparison
machinery against a deliberately wrong declaration and a deliberately void anchor.

CODE mutants break the LAW (sim/feeder.py, sim/composedfeeder.py's run); EXPECT mutants break
the INSTRUMENT (the grep, the parse, the field offset, the round the bit is read back from) -
the four defects this rung actually hit while it was being written.

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
NGATES = 8

MUTANTS = [
    # ---- the law: sim/feeder.py -------------------------------------------------------
    ("MU1", "sim/feeder.py",
     "    return (x - (-1 if x < 0 else 0)) >> 1        # cdq, then sub, then sar (Python >> floors)",
     "    return x >> 1                                 # mutant: a bare sar (floors)",
     "the cdq/sub/sar trunc-toward-zero halving replaced by a plain shift"),
    ("MU2", "sim/feeder.py",
     "    if not halve:\n        return cost, carry",
     "    if not halve:\n        return cost, 0",
     "the full-price path clears the carry (4f4938 never touches block+0)"),
    ("MU3", "sim/feeder.py",
     "    return trunc_div2(s), s & 1           # 4f4936 / 4f4921->4f4931",
     "    return trunc_div2(s), 0               # mutant: the parity is never written back",
     "the carried half-unit dropped at the write-back"),
    ("MU4", "sim/feeder.py",
     "        if item > charge_hi:                       # 4f4811 / 4f4814",
     "        if item > visit_hi + 4:                    # mutant: the top bound never skips",
     "the charge bound 0x22 ignored (ids 35..38 charged too)"),
    ("MU5", "sim/feeder.py",
     "        if not fac_bit(bitmap_bytes, item):        # 4f4837 / 4f484c\n            continue",
     "        if False:                                  # mutant: the base need not HAVE it\n            continue",
     "the base-has-facility gate dropped (every row charged)"),
    ("MU6", "sim/feeder.py",
     "    if sel < 0:\n        return False, \"sign\"",
     "    if False:\n        return False, \"sign\"",
     "the sign skip at 4f48dc dropped (halving unconditional on the sign leg)"),
    ("MU7", "sim/feeder.py",
     "    if owner_bytes[sel] != own:\n        return False, \"owner\"",
     "    if False:\n        return False, \"owner\"",
     "the owner-byte skip at 4f48f8 dropped (any selected base halves)"),
    ("MU8", "sim/feeder.py",
     "    return (v | (1 << BIT5)) if b else (v & ~(1 << BIT5))",
     "    return v                                       # mutant: bit5 never changes",
     "the bit5 set/clear pair made a no-op"),
    ("MU9", "sim/feeder.py",
     "    by, bi = item >> 3, item & 7",
     "    by, bi = item & 7, item >> 3                   # mutant: mapper halves swapped",
     "the mapper's byte/bit split swapped"),
    # ---- the run: sim/composedfeeder.py ----------------------------------------------
    ("MU10", "sim/composedfeeder.py",
     "                                               disabled.get(f, ()), visit_lo, charge_hi, visit_hi)",
     "                                               (), visit_lo, charge_hi, visit_hi)",
     "the faction's disabled list never consulted in the run"),
    ("MU11", "sim/composedfeeder.py",
     "        wr.append((sf.BLK0 + sf.BLK_STRIDE * f, sf.set_bit5(b0[f], carry)) if touched\n"
     "                  else (sf.BLK0 + sf.BLK_STRIDE * f, b0[f]))",
     "        wr.append((sf.BLK0 + sf.BLK_STRIDE * f, b0[f]))   # mutant: block+0 lifted as-is",
     "the carry not handed to the writer (block+0 pass-through)"),
    ("MU12", "sim/composedfeeder.py",
     "            wr = [(o, sf.set_bit5(v, 0)) for (o, v) in wr if o % sf.BLK_STRIDE == sf.BLK0] + \\",
     "            wr = [(o, v) for (o, v) in wr if o % sf.BLK_STRIDE == sf.BLK0] + \\",
     "the zero-carry RIVAL stops being a rival (it persists the carry too)"),
    # ---- the instrument: EXPECT mutants ----------------------------------------------
    ("ME1", "sim/composedfeeder.py",
     "        if addr in ln and token in ln:\n            n += 1",
     "        n += 1                                     # mutant: the grep always hits",
     "the pin grep made unfalsifiable (a hit for every pin, bogus included)"),
    ("ME2", "sim/composedfeeder.py",
     "    m[\"range_imm\"] = int(_re1(r\"range-bound=\\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\\]\", cl,",
     "    m[\"range_imm\"] = int(_re1(r\"charge-bound=\\['[0-9a-f]+: cmp esi,0x([0-9a-f]+)'\\]\", cl,",
     "the range bound parsed off the WRONG census field"),
    ("ME3", "sim/composedfeeder.py",
     "    m[\"spend_oct\"] = [struct.unpack_from(\"<i\", sv.data, so.BLOCK_A_OFF + sf.BLK_STRIDE * f\n"
     "                                         + sf.OFF_SPEND)[0] for f in range(NFACTION)]",
     "    m[\"spend_oct\"] = [struct.unpack_from(\"<i\", sv.data, so.BLOCK_A_OFF + sf.BLK_STRIDE * f\n"
     "                                         + sf.OFF_ENERGY)[0] for f in range(NFACTION)]",
     "the recorded accumulator read from ENERGY instead of +300"),
    ("ME4", "sim/composedfeeder.py",
     "                      \"<i\", imgs_f[0], so.BLOCK_A_OFF + sf.BLK_STRIDE * f)[0]),",
     "                      \"<i\", imgf, so.BLOCK_A_OFF + sf.BLK_STRIDE * f)[0]),",
     "bit5 read back from the FINAL image, not the round that wrote it (the s316 defect)"),
]

# Filled from `--measure`: the sets this harness MEASURED, not the ones hoped for.
DECLARED = {}


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
    r = subprocess.run([sys.executable, "-u", "-m", "sim.composedfeeder"], cwd=dst,
                       capture_output=True, text=True, timeout=900)
    bad, ok = set(), set()
    for line in r.stdout.splitlines():
        g = GATE_RE.match(line)
        if g:
            (bad if g.group(1) == "BAD" else ok).add(g.group(2))
    return bad, ok, r.returncode, (r.stderr or "")[-300:]


def selftest():
    """The comparison machinery must reject a wrong declaration and refuse a void anchor."""
    tmp = tempfile.mkdtemp(prefix="b28_st_")
    try:
        build_tree(os.path.join(tmp, "tree"), "sim/feeder.py",
                   "    return trunc_div2(s), s & 1           # 4f4936 / 4f4921->4f4931",
                   "    return trunc_div2(s), 0")
        bad, ok, rc, err = run_tree(os.path.join(tmp, "tree"))
        print("ST1 redden set %s rc=%d %s" % (sorted(bad), rc, "PASS" if bad else "FAIL"))
        st1 = bool(bad)
        try:
            build_tree(os.path.join(tmp, "tree2"), "sim/feeder.py", "BLK_STRIDE = 99999", "x")
            st2 = False
        except AssertionError as e:
            st2 = True
            print("ST2 void anchor rejected: %s" % e)
        wrong = decl_complaints("MU3", {"G5"}, {"G5", "G9"})
        right = decl_complaints("MU3", {"G5"}, {"G5"})
        print("ST4 exact-set comparison rejects a wrong declaration (%d complaints) and "
              "accepts the true one (%d): %s"
              % (len(wrong), len(right), "PASS" if wrong and not right else "FAIL"))
        st4 = bool(wrong) and not right
        print("ST3 no-op tree reddens nothing:", end=" ")
        os.makedirs(os.path.join(tmp, "tree3"))
        for name in ("evidence", "data", "programs", "scripts"):
            os.symlink(os.path.join(ROOT, name), os.path.join(tmp, "tree3", name))
        shutil.copytree(os.path.join(ROOT, "sim"), os.path.join(tmp, "tree3", "sim"))
        b3, _o3, rc3, _e3 = run_tree(os.path.join(tmp, "tree3"))
        st3 = (not b3) and rc3 == 0
        print("%s (%d BAD, rc=%d)" % ("PASS" if st3 else "FAIL", len(b3), rc3))
        return 0 if (st1 and st2 and st3 and st4) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scripts/b28_mutate.py")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--only", default=None, help="run a subset by id (MU3,MU7)")
    ap.add_argument("--measure", action="store_true",
                    help="print the MEASURED sets as a DECLARED literal and exit 0 (no asserts)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    ids = set(a.only.split(",")) if a.only else None
    results, digests = [], []
    tmp = tempfile.mkdtemp(prefix="b28_mut_")
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
            print("HARNESS FAIL: the unpatched tree does not print a clean %d/%d"
                  % (NGATES, NGATES))
            return 1
        dig = hashlib.sha256("\n".join(digests).encode()).hexdigest()[:16]
        print("mutant table digest %s" % dig)
        if a.measure:
            print("DECLARED = {")
            for (mid, _w, b) in results:
                print("    %r: {%s}," % (mid, ", ".join(repr(x) for x in b)))
            print("}")
            print("gate coverage %s / %d"
                  % (sorted({g for (_m, _w, b) in results for g in b}), NGATES))
            print("--measure: nothing asserted, declarations not checked")
            return 0
        complaints = []
        for (mid, _w, measured) in results:
            if mid not in DECLARED:
                complaints.append("%s has NO declared gate set" % mid)
                continue
            complaints += decl_complaints(mid, set(measured), set(DECLARED[mid]))
        covered = {g for (_m, _w, b) in results for g in b}
        for g in ["G%d" % i for i in range(1, NGATES + 1)]:
            if g not in covered:
                complaints.append("gate %s is reddened by NO mutant (unmeasured law)" % g)
        for c in complaints:
            print("MISMATCH: %s" % c)
        print("exact-set check: %d mutant(s), %d complaint(s), gates reddened %d/%d"
              % (len(results), len(complaints),
                 len(covered & set("G%d" % i for i in range(1, NGATES + 1))), NGATES))
        if complaints:
            print("HARNESS FAIL: a measured gate set does not equal its declaration")
            return 1
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
