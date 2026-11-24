#!/usr/bin/env python3
"""M342 mutant harness (review_lint law: every V row in NAMED ## M342 names its mutant).

Re-creates each defect in a COPY of scripts/m342_completion_setter.py (one anchor->replacement)
and runs it against the same dump/index.  A mutant must redden EXACTLY its declared gate set;
the identity (NO-OP) mutant must redden nothing - that is what proves the comparison bites.
A mutant whose anchor does not occur exactly once is a harness error, not a pass.

  python3 -u scripts/m342_mutate.py            # full run
  python3 -u scripts/m342_mutate.py --selftest # machinery only, no dump needed

Zero box, zero /proc, zero gdb.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "scripts/m342_completion_setter.py")
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
GATE_RE = re.compile(r"^(ok|BAD)\s+(G\d+)\b")

MUTANTS = [
    ("MU1", "REC_BASE = 0x95da10", "REC_BASE = 0x95da14", ["G1"],
     "the field arithmetic taken from the WRONG anchor (array base = the +4 byte) -> +0x88"),
    ("MU2", "in direct if o == 0x95da9c]", "in direct if o != 0x95da9c]", ["G2"],
     "the bitmap constant inverted: the census counts every OTHER byte of the record"),
    ("MU3", 'api_lines.get(0x4e451b, "")', 'api_lines.get(0x4e4518, "")', ["G3"],
     "the mask slot read from the INDEX reload site (out1/out2 provenance swapped)"),
    ("MU4", "if len(pushes) == 3:", "if len(pushes) == 2:", ["G4"],
     "the argument scan truncated at two pushes: the set flag is never parsed"),
    ("MU5", "pop_body = body(ins, pop_fn[0], pop_fn[1])", "pop_body = body(ins, pop_fn[0], pop_fn[1] + 3000)", ["G5"],
     "the pop's body span widened into the base screen: the screen's copy counted as a pop write"),
    ("MU6", 'if any(re.search(r"call +0x%x$" % MAPPER, w) for w in win):', "if False:", ["G6"],
     "the mask-slot provenance check disabled: OR stores no longer tied to the mapper"),
    ("NOOP", "REC_BASE = 0x95da10", "REC_BASE = 0x95da10", [],
     "identity tree - must redden nothing"),
]


def run(script, extra=()):
    p = subprocess.run([sys.executable, "-u", script, "--text", TEXT, "--index", INDEX] + list(extra),
                       capture_output=True, text=True, timeout=600)
    out = p.stdout + p.stderr
    red = {m.group(2) for m in (GATE_RE.match(l) for l in out.splitlines()) if m and m.group(1) == "BAD"}
    oks = {m.group(2) for m in (GATE_RE.match(l) for l in out.splitlines()) if m and m.group(1) == "ok"}
    return p.returncode, red, oks, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        tmp = tempfile.mkdtemp(prefix="m342st_")
        try:
            bad = os.path.join(tmp, "bad.py")
            open(bad, "w").write("print('BAD  G1 x')\nprint('ok   G2 y')\n")
            rc, red, oks, _ = run(bad)
            assert red == {"G1"} and oks == {"G2"}, (red, oks)
            print("SELFTEST ok: gate parsing reads BAD/ok from stdout")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return 0

    print("M342 mutant harness: %d mutants against %s" % (len(MUTANTS), os.path.basename(SRC)))
    # GUARD 0: the unmutated script must be green, or "a mutant reddens G<n>" measures nothing
    rc, red, oks, out = run(SRC)
    if rc != 0 or red or len(oks) != 6:
        print("FAIL: baseline is not green (rc=%d red=%s ok=%s)" % (rc, sorted(red), sorted(oks)))
        print(out[-2000:])
        return 2
    print("baseline green: %d/6 gates, no BAD" % len(oks))

    tmp = tempfile.mkdtemp(prefix="m342m_")
    bad_rows = []
    try:
        for mid, old, new, want, why in MUTANTS:
            src = open(SRC).read()
            n = src.count(old)
            if n != 1:
                print("HARNESS ERROR %s: anchor occurs %d times" % (mid, n))
                return 3
            path = os.path.join(tmp, "%s.py" % mid)
            open(path, "w").write(src.replace(old, new))
            rc, red, oks, out = run(path)
            got = sorted(red)
            verdict = "PASS" if got == sorted(want) else "FAIL"
            if "Traceback" in out:
                verdict = "FAIL(traceback)"
            if verdict != "PASS":
                bad_rows.append((mid, want, got, out[-800:]))
            print("  %-5s %-6s reddens %-8s %s" % (mid, verdict, ",".join(got) or "[]", why))
        if bad_rows:
            for mid, want, got, tail in bad_rows:
                print("\n== %s wanted %s got %s\n%s" % (mid, want, got, tail))
            print("\nFAIL HARNESS M342: %d/%d mutants misbehaved" % (len(bad_rows), len(MUTANTS)))
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    import hashlib
    dig = hashlib.sha256(open(SRC, "rb").read()).hexdigest()[:16]
    print("PASS HARNESS M342: %d/%d mutants redden exactly their declared sets, NO-OP [] , script %s"
          % (len(MUTANTS), len(MUTANTS), dig))
    return 0


if __name__ == "__main__":
    sys.exit(main())
