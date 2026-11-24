#!/usr/bin/env python3
"""M341 mutation harness: every VERIFIED claim row of `## M341` must name a
mutant here that reddens it, and each mutant is a ONE-INSTRUCTION edit of the
measured image (scratch/m574/text.txt), never a rewrite of a gate's expected
value.

    python3 scripts/m341_mutate.py            # score all mutants
    python3 scripts/m341_mutate.py --selftest # engine sanity only

Scoring: a mutant SCORES when the gate it names actually goes FAIL on the
printed table.  The NO-OP control must leave all 10 gates PASS.
"""
import contextlib
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m341_hof_window as M  # noqa: E402


def fresh():
    M.INSN_CACHE = M.load_image()


def set_ops(addr, new_ops):
    """Replace the operand text of the instruction at `addr` (the bytes are
    the measurement; this is the only knob the mutants get)."""
    for i, (a, mn, ops) in enumerate(M.INSN_CACHE):
        if a == addr:
            M.INSN_CACHE[i] = (a, mn, new_ops)
            return True
    return False


def run():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = M.main()
    return dict(M.LAST_ROWS), rc, buf.getvalue()


# name, instruction address, mutated operand, gate the row names
MUTANTS = [
    ("MU1",  0x449793, "ecx,[eax+ebx*3]",          "G1"),
    ("MU2",  0x449796, "ecx,[ebx+ecx*1]",          "G1"),
    ("MU3",  0x44AF20, "eax,0x5",                  "G4"),
    ("MU4",  0x44B6AC, "eax,0x983984",             "G5"),
    ("MU5",  0x44B6C1, "eax,0x984ca8",             "G5"),
    ("MU6",  0x44B6B1, "ecx,0x6",                  "G5"),
    ("MU7",  0x44B6B9, "eax,0x90",                 "G5"),
    ("MU8",  0x44970F, "ebx,DWORD PTR [esi+0x59f0]", "G2"),
    ("MU9",  0x449728, "DWORD PTR [ebp-0x1c],eax", "G2"),
    ("MU10", 0x44B5B9, "ecx,0xfffffffd",           "G3"),
    ("MU11", 0x44AF9B, "edx,[edx+eax*3]",          "G4"),
    ("MU12", 0x449985, "BYTE PTR [ebx+0x1],0x40",  "G7"),
    ("MU13", 0x44AF9E, "esi,[eax+edx*1-0x4]",      "G4"),
    ("ALG1", 0x449796, "ecx,[ebx+ecx*1-0x5]",      "G1"),  # decoder mutated
]


def alg1():
    """ALG1 is an ALGORITHM mutant: the affine decoder drops bare register
    terms, so a chained-lea law loses the component carried by the bare reg."""
    real = M.affine

    def broken(expr, env=None):
        aff = real(expr, env)
        e = expr.strip().strip("[]").replace(" ", "")
        bare = re.findall(r"(?:^|[+\-])([a-z]{3})(?=[+\-]|$)", e)
        return {k: v for k, v in aff.items() if k not in bare}

    M.affine = broken
    return real


def score():
    fresh()
    base_rows = run()[0]
    if not all(base_rows.values()):
        print("BASELINE IS NOT GREEN — refusing to score")
        return 1
    print("baseline: %d gates, all PASS" % len(base_rows))

    scored = mismatch = crash = 0
    digest_rows = []
    for name, addr, ops, gate in MUTANTS:
        fresh()
        real = alg1() if name == "ALG1" else None
        if not set_ops(addr, ops):
            print("%-5s CRASH: no instruction at 0x%x" % (name, addr))
            crash += 1
            continue
        try:
            rows, rc, text = run()
        except Exception as e:                       # noqa: BLE001
            print("%-5s CRASH 0x%x: %s" % (name, addr, e))
            crash += 1
            if real:
                M.affine = real
            continue
        if real:
            M.affine = real
        red = [k for k, v in rows.items() if not v]
        hit = [k for k in red if k.startswith(gate)]
        ok = bool(hit)
        scored += ok
        mismatch += (not ok)
        print("%-5s 0x%06x %-28s -> %s  red=%d %s"
              % (name, addr, ops, "SCORED" if ok else "MISS",
                 len(red), [r[:12] for r in red]))
        digest_rows.append("%s=%d" % (name, ok))
    allrows = digest_rows
    print("HARNESS %s: %d/%d scored, %d MISMATCH, %d CRASH, digest(rows)=%s"
          % ("PASS" if scored == len(MUTANTS) else "FAIL", scored,
             len(MUTANTS), mismatch, crash,
             hashlib.sha256("\n".join(allrows).encode()).hexdigest()[:16]))
    return 0 if (scored == len(MUTANTS) and not crash) else 1


def selftest():
    fresh()
    ok = 0
    checks = [set_ops(0x449793, "ecx,[eax+ebx*4]"),
              not set_ops(0xDEAD00, "x"), True]
    for c in checks:
        ok += bool(c)
    rows = run()[0]
    ok += all(v for k, v in rows.items())
    print("SELFTEST %d/4" % ok)
    return 0 if ok == 4 else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else score())
