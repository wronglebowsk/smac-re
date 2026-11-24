#!/usr/bin/env python3
"""B34 mutant harness (review_lint law: every V row in NAMED ## B34 names its mutant).

Re-creates each defect in a COPY of sim/facstamp.py (one anchor->replacement, installed as
sim/_b34_mut_<id>.py so the relative `from . import facoracle` still resolves) and runs it
against the same dump + recorded trace.  A mutant must redden EXACTLY its declared gate set;
the identity (NO-OP) mutant must redden nothing - that is what proves the comparison bites.
An anchor that does not occur exactly once is a harness error, not a pass.

  python3 -u scripts/b34_mutate.py             # full run (~10 gates x 11 runs)
  python3 -u scripts/b34_mutate.py --selftest  # machinery only, no dump needed

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
SRC = os.path.join(ROOT, "sim", "facstamp.py")
SIM = os.path.dirname(SRC)
GATE_RE = re.compile(r"^(ok|BAD)\s+(G\d+)\b")

MUTANTS = [
    ("MU1", "if stb + fo.ADD >= PRICE and sta < stb:\n                    paid.append(row)",
            "if stb >= PRICE and sta < stb:\n                    paid.append(row)", ["G6", "G8", "G10"],
     "the recorded PAY test drops the per-round addition: Korolev/Virgin Soil completions vanish"),
    ("MU2", "FAC_LO, FAC_HI = 1, 0x40", "FAC_LO, FAC_HI = 0, 0x40", ["G6", "G10"],
     "head 0 (an EMPTY queue) counted as a facility completion"),
    ("MU3", 'ANCHOR = "5296fdad6d26caa3"', 'ANCHOR = "0000000000000000"', ["G1", "G10"],
     "the dump digest anchor unpinned: any census drift would go unnoticed"),
    ("MU4", "pop_body = body_of(ins, fns, POP)", "pop_body = []", ["G3"],
     "the pop's body never read: writer-free passes on an UNMEASURED state"),
    ("MU5", "pop_hosts = {SCREEN_NAME}", "pop_hosts = set(hosts)", ["G4"],
     "the pop's host set widened to the API's hosts: disjointness becomes vacuous"),
    ("MU6", 'if mnem == "mov":\n        return "COPY"', 'if mnem == "mov" and False:\n        return "COPY"', ["G2", "G5", "G10"],
     "whole-word copies folded into the grant family: the LOSS-capable writer disappears"),
    ("MU7", "vac = hb in fo.bits_of(p)", "vac = False", ["G6", "G8", "G10"],
     "every completion called DISCRIMINATING: the byte diff no longer matches the vacuous rows"),
    ("MU8", "gain_offwin = [x for x in gain_at_paid if not (FAC_LO <= x[5] < FAC_HI)]",
            "gain_offwin = [x for x in gain_at_paid if not (x[5] < FAC_HI)]", ["G7"],
     "the facility window's LOWER bound dropped: a unit-encoded negative head reads as in-window"),
    ("MU9", "gain_at_paid = [x for x in gains if x[7] + fo.ADD >= PRICE and x[8] < x[7]]",
            "gain_at_paid = list(gains)", ["G7", "G9"],
     "every gain counted as a paid boundary: the no-pay copy signature is scored as a completion"),
    ("MU11", "                    leas.append((a, a2, ms.group(1), b2, container(fns, starts, a2)))",
             "                    leas.append((a, a2, ms.group(1), b2, container(fns, starts, a2))) if container(fns, starts, a2)[2] != \"HOLE\" else None",
             ["G2", "G5", "G10"],
     "the unnamed-region writers dropped from the census: the COPY distribution loses its 3 HOLE sites"),
    ("MU12", 'STORES_ANCHOR = "6e9336d6bc27b5c8"', 'STORES_ANCHOR = "0000000000000000"', ["G10"],
     "the store-census digest unpinned: a family-shape drift would go unnoticed"),
    ("MU10", "        if m and mem_touches_bitmap(m.group(2)):\n            const.append",
             "        if m:\n            const.append", ["G2", "G5", "G10"],
     "the bitmap filter dropped: every BYTE store in .text counted as a bitmap writer"),
    ("NOOP", "ANCHOR = \"5296fdad6d26caa3\"", "ANCHOR = \"5296fdad6d26caa3\"", [],
     "identity tree - must redden nothing"),
]


def run(module):
    p = subprocess.run([sys.executable, "-u", "-m", module], cwd=ROOT,
                       capture_output=True, text=True, timeout=900)
    out = p.stdout + p.stderr
    red = {m.group(2) for m in (GATE_RE.match(l) for l in out.splitlines()) if m and m.group(1) == "BAD"}
    oks = {m.group(2) for m in (GATE_RE.match(l) for l in out.splitlines()) if m and m.group(1) == "ok"}
    return p.returncode, red, oks, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        tmp = tempfile.mkdtemp(prefix="b34st_")
        try:
            bad = os.path.join(tmp, "bad.py")
            open(bad, "w").write("print('BAD  G1 x')\nprint('ok   G2 y')\n")
            rc, red, oks, _ = run(os.path.relpath(bad, ROOT))
            assert red == {"G1"} and oks == {"G2"}, (red, oks)
            print("SELFTEST ok: gate parsing reads BAD/ok from stdout")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return 0

    print("B34 mutant harness: %d mutants against %s" % (len(MUTANTS), os.path.basename(SRC)))
    rc, red, oks, out = run("sim.facstamp")
    if rc != 0 or red or len(oks) != 10:
        print("FAIL: baseline is not green (rc=%d red=%s ok=%s)" % (rc, sorted(red), sorted(oks)))
        print(out[-2000:])
        return 2
    print("baseline green: %d/10 gates, no BAD" % len(oks))

    src = open(SRC, encoding="utf-8").read()
    bad_rows = []
    installed = []
    try:
        for mid, old, new, want, why in MUTANTS:
            n = src.count(old)
            if n != 1:
                print("HARNESS ERROR %s: anchor occurs %d times" % (mid, n))
                return 3
            name = "_b34_mut_%s" % mid
            path = os.path.join(SIM, name + ".py")
            open(path, "w", encoding="utf-8").write(src.replace(old, new))
            installed.append(path)
            rc, red, oks, out = run("sim." + name)
            got = sorted(red)
            verdict = "PASS" if got == sorted(want) else "FAIL"
            if "Traceback" in out:
                verdict = "FAIL(traceback)"
            if verdict != "PASS":
                bad_rows.append((mid, want, got, out[-900:]))
            print("  %-4s %-6s reddens %-9s %s" % (mid, verdict, ",".join(got) or "[]", why))
        if bad_rows:
            for mid, want, got, tail in bad_rows:
                print("\n== %s wanted %s got %s\n%s" % (mid, want, got, tail))
            print("\nFAIL HARNESS B34: %d/%d mutants misbehaved" % (len(bad_rows), len(MUTANTS)))
            return 1
    finally:
        for p in installed:
            try:
                os.unlink(p)
            except OSError:
                pass
    dig = hashlib.sha256(open(SRC, "rb").read()).hexdigest()[:16]
    print("PASS HARNESS B34: %d/%d mutants redden exactly their declared sets, NO-OP [], script %s"
          % (len(MUTANTS), len(MUTANTS), dig))
    return 0


if __name__ == "__main__":
    sys.exit(main())
