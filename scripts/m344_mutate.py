#!/usr/bin/env python3
"""M344 mutant harness (review_lint law: every V row in NAMED ## M344 names its mutant).

Each entry re-creates ONE defect in a copy of scripts/m344_completion_caller.py (an anchor ->
replacement that must occur exactly once) and runs it against the same dump/index.  A mutant
must redden EXACTLY its declared gate set; the identity (NO-OP) mutant must redden nothing -
that is what proves the comparison bites.

  python3 -u scripts/m344_mutate.py             # full run
  python3 -u scripts/m344_mutate.py --selftest  # machinery only, no dump needed

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
SRC = os.path.join(ROOT, "scripts/m344_completion_caller.py")
TEXT = os.path.join(ROOT, "scratch/m574/text.txt")
INDEX = os.path.join(ROOT, "ghidra_out/index.csv")
GATE_RE = re.compile(r"^(ok|BAD)\s+(G\d+)\b")

MUTANTS = [
    ("MU1", "len(set0) == 8", "len(set0) == 7", ["G1"],
     "M342's shipped split (16/7/4) trusted instead of re-derived -> the 0x40dd3c row is lost"),
    ("MU2", 'and [d[0] for d in diverged] == [0x40dd3c]', 'and [d[0] for d in diverged] == []', ["G1"],
     "the M342-window divergence check disabled: the retraction would go unnoticed"),
    ("MU3", 'known = {"imm", "callret", "param", "clamped", "loopctr", "QUEUE", "mem", "computed", "global"}',
     'known = {"imm", "callret", "clamped", "loopctr", "QUEUE", "mem", "computed", "global"}', ["G2"],
     "a legitimate item source (function parameter) declared unknown -> the exhaustiveness gate bites"),
    ("MU4", 'qch = [r for r in rows if "QUEUE" in r["term"]]',
     'qch = [r for r in rows if feats[r["fn"]]["q"] > 0]', ["G3"],
     "queue-provenance confused with 'the function touches the queue' -> the negative dies"),
    ("MU5", "want = {0x41c6f8, 0x41d8fc, 0x508c85, 0x508cee}",
     "want = {0x41c6f8, 0x508c85, 0x508cee}", ["G4"],
     "one register-item grant dropped from the pinned set: G4 would pass on an incomplete census"),
    ("MU6", '"4f0ec0 or     BYTE PTR [eax],cl"', '"4f0ec0 mov    BYTE PTR [eax],cl"', ["G5"],
     "the stamp pinned as a plain store instead of the OR: the set semantic is not gated"),
    ("MU7", "0x4f0f6f) == \"mov    edx,DWORD PTR [ecx+0x984d38]\"",
     "0x4f0f6f) == \"mov    edx,DWORD PTR [ecx+0x984d3c]\"", ["G6"],
     "the item-table row offset shifted by one dword: the consume site is not gated"),
    ("MU8", "gate(\"G7\", dist == 0x86", "gate(\"G7\", dist == 0x84", ["G7"],
     "the stamp->pop distance loosened: any nearby or-pop pair would pass"),
    ("MU9", 'DIGEST_EXPECT = "7586ab28a3974104"', 'DIGEST_EXPECT = "0000000000000000"', ["G8"],
     "the ACCEPT digest anchor unpinned (table drift would go unnoticed)"),
    ("NOOP", "REC = 0", "REC = 0", [],
     "identity tree - must redden nothing"),
]
MUTANTS[-1] = ("NOOP", 'DIGEST_EXPECT = "7586ab28a3974104"', 'DIGEST_EXPECT = "7586ab28a3974104"', [],
               "identity tree - must redden nothing")


def run(script, extra=()):
    p = subprocess.run([sys.executable, "-u", script, "--text", TEXT, "--index", INDEX] + list(extra),
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
        tmp = tempfile.mkdtemp(prefix="m344st_")
        try:
            bad = os.path.join(tmp, "bad.py")
            open(bad, "w").write("print('BAD  G1 x')\nprint('ok   G2 y')\n")
            rc, red, oks, _ = run(bad)
            assert red == {"G1"} and oks == {"G2"}, (red, oks)
            print("SELFTEST ok: gate parsing reads BAD/ok from stdout")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return 0

    src = open(SRC).read()
    print("M344 mutant harness: %d mutants against %s" % (len(MUTANTS), os.path.basename(SRC)))
    # GUARD 0: the unmutated script must be green, or "a mutant reddens G<n>" measures nothing
    rc, red, oks, out = run(SRC)
    if rc != 0 or red or len(oks) != 8:
        print("FAIL: baseline is not green (rc=%d red=%s ok=%s)" % (rc, sorted(red), sorted(oks)))
        print(out[-2000:])
        return 1
    print("baseline 8/8 green (digest %s)" % (re.search(r"digest ([0-9a-f]{16})", out).group(1)))

    tmp = tempfile.mkdtemp(prefix="m344mut_")
    bad = 0
    seen = set()
    try:
        for mid, old, new, want, why in MUTANTS:
            n = src.count(old)
            if n != 1:
                print("HARNESS ERROR %s: anchor occurs %d times: %r" % (mid, n, old[:60]))
                bad += 1
                continue
            p = os.path.join(tmp, mid + ".py")
            open(p, "w").write(src.replace(old, new))
            rc, mred, moks, mout = run(p)
            ok = (mred == set(want))
            print("%s %s expected %s got %s  (%s)" % ("ok  " if ok else "BAD ",
                                                      mid, sorted(want), sorted(mred), why[:70]))
            for g in want:
                seen.add((g, mid))
            if not ok:
                bad += 1
                print(mout[-600:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    covered = {g for g, _ in seen}
    missing = [g for g in ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"] if g not in covered]
    if missing:
        print("FAIL: gates with no mutant: %s" % missing)
        bad += 1
    if bad:
        print("\nFAIL HARNESS M344: %d problems" % bad)
        return 1
    print("\nPASS HARNESS M344: %d/%d mutants redden exactly their set; NO-OP [] ; gates covered %s"
          % (len(MUTANTS), len(MUTANTS), sorted(covered)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
