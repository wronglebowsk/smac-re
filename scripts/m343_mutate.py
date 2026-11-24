#!/usr/bin/env python3
"""M343 mutation harness -- every VERIFIED row of `## M343` names a mutant here
that reddens it, and every mutant is a ONE-INSTRUCTION edit of the measured
bytes (the image disassembly) or of one vtable dword in terran.exe -- never a
rewrite of a gate's expected value.

    python3 scripts/m343_mutate.py            # score all mutants
    python3 scripts/m343_mutate.py --selftest # engine sanity only

Scoring: a mutant SCORES when the gate it NAMES actually prints FAIL.  MU0 is
the declared NO-OP control and must leave all 9 gates PASS.  The covered set is
MEASURED (which mutant reddened which gate), then asserted: every gate G1..G9
must be covered by at least one mutant.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "m343_a40_writer.py")
GATES = ["G%d" % i for i in range(1, 10)]

# (tag, gate it must redden, INS patch "addr=operands", VT patch "va=dword")
MUTANTS = [
    ("MU0", None, None, None),
    ("MU1", "G1", "5e7bbe=BYTE PTR [eax+0xa40],0x0", None),          # indexed -> field
    ("MU2", "G2", None, "6716f4=0x402120"),                                # 0x67164c+0xa8 slot
    ("MU3", "G3", "5ee3b8=edx,DWORD PTR [eax+0x2350]", None),          # panel ctor gains state
    ("MU4", "G4", "405f3a=DWORD PTR [eax+0xa40],0x0", None),           # dialog ctor gains a ref
    ("MU5", "G5", "5f3f45=DWORD PTR [eax+0xa40],ecx", None),           # runner read -> store
    ("MU6", "G6", "5f57b1=eax,0x1234", None),                          # break the value chain
    ("MU7", "G7", "5f3d70=DWORD PTR ds:0x9977f4,ecx", None),           # break ds:0x9977f0
    ("MU8", "G8", "5f57e6=DWORD PTR [ebp-0x10],0xffffffff", None),     # -2 -> -1
    ("MU9", "G9", "5f6c85=DWORD PTR [ecx+0xa44],edx", None),           # drop one field ref
    ("MU10", "G7", "5f3d6a=ecx,DWORD PTR [ebp-0x398]", None),            # break the identity link
    ("MU11", "G6", "5f5790=edx,0x222c", None),                           # break the 0x2228 chain
]


def run(tag, ins, vt):
    env = dict(os.environ)
    env.pop("M343_PATCH_INS", None)
    env.pop("M343_PATCH_VT", None)
    if ins:
        env["M343_PATCH_INS"] = ins
    if vt:
        env["M343_PATCH_VT"] = vt
    out = subprocess.run([sys.executable, "-u", SCRIPT], env=env,
                         capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        m = re.match(r"^(G\d) (PASS|FAIL)", line)
        if m:
            res[m.group(1)] = m.group(2)
    total = re.search(r"^PASS M343: (\d+)/(\d+)", out, re.M)
    return res, out, (total.groups() if total else None)


def covered_by(res):
    return sorted(g for g, v in res.items() if v == "FAIL")


def main():
    selftest = "--selftest" in sys.argv
    scored, bad, cover = [], [], {g: [] for g in GATES}
    for tag, gate, ins, vt in MUTANTS:
        res, out, total = run(tag, ins, vt)
        if tag == "MU0":
            ok = total == ("9", "9") and not covered_by(res)
            print("%-5s NO-OP  gates=%s total=%s  %s" % (tag, len(res), total,
                                                         "SCORE" if ok else "BAD"))
            if ok:
                scored.append(tag)
            else:
                bad.append(tag)
            continue
        red = covered_by(res)
        ok = res.get(gate) == "FAIL"
        for g in red:
            cover[g].append(tag)
        print("%-5s names %s  reddened=%-18s %s" % (tag, gate, ",".join(red) or "-",
                                                    "SCORE" if ok else "BAD"))
        (scored if ok else bad).append(tag)
    if selftest:
        print("SELFTEST: engine ran %d mutants, %d scored, %d bad"
              % (len(MUTANTS), len(scored), len(bad)))
        return 0 if not bad else 1
    print()
    print("covered set (measured):")
    uncovered = []
    for g in GATES:
        print("  %s <- %s (%d)" % (g, ",".join(cover[g]) or "-", len(cover[g])))
        if not cover[g]:
            uncovered.append(g)
    ok = not bad and not uncovered
    print()
    print("HARNESS %s M343: %d/%d scored, NO-OP %s, uncovered %s"
          % ("PASS" if ok else "FAIL", len(scored), len(MUTANTS),
             "[]" if "MU0" in scored else "BAD", uncovered or "[]"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
