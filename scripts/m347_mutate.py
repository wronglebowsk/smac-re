#!/usr/bin/env python3
"""M347 mutation harness -- every VERIFIED row of NAMED ## M347 names the
mutant that reddens it.  Each mutant perturbs one operand/mnemonic/image dword
through the acceptance script's own hooks and the harness asserts the carrying
gate flips to FAIL.

    python3 -u scripts/m347_mutate.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m347_page_writer.py")

# (id, row defended, env, gates that must redden)
MUTANTS = [
    ("MU0", "ACCEPT baseline (must stay 12/12)", {}, set()),
    ("MU1", "G1 field = sub+0x84 (ctor lea moved)", {"M347_PATCH_INS": "44ba97=ecx,[esi+0x5974]"}, {"G1"}),
    ("MU2", "G1 vtable +0x30 = reader method", {"M347_PATCH_IMG": "674c8c=404ed0"}, {"G1"}),
    ("MU3", "G2 ctor leaves +0x84 untouched", {"M347_PATCH_INS": "6290bc=DWORD PTR [eax+0x84],0x0"}, {"G2", "R1"}),
    ("MU4", "G3 the four stores (id store moved off +0x84)", {"M347_PATCH_INS": "629363=DWORD PTR [ecx+0x88],edx"}, {"G3"}),
    ("MU5", "G3 no lea-alias store evasion", {"M347_PATCH_MN": "62935d=lea", "M347_PATCH_INS": "62935d=ecx,[ecx+0x84]"}, {"G3"}),
    ("MU6", "G4 absolute receiver 0x74df70", {"M347_PATCH_INS": "44b726=ecx,0x74df74"}, {"G4"}),
    ("MU7", "G5 child count 7 (algorithm: trip+1)", {"M347_ALGO": "trip"}, {"G5", "R4"}),
    ("MU8", "G5 reload AFTER the counter inc", {"M347_PATCH_INS": "4493e1=DWORD PTR [ebp-0x18],edx"}, {"G5"}),
    ("MU9", "G5 Init stores arg2 at +0xa78", {"M347_PATCH_INS": "5f9f72=DWORD PTR [edx+0xa7c],eax"}, {"G5"}),
    ("MU10", "G5 ids are 1..7 (algorithm: 0-based)", {"M347_ALGO": "id0"}, {"G5", "R3"}),
    ("MU11", "G6 block id = counter+1", {"M347_PATCH_INS": "44ae62=eax,DWORD PTR [ebp+0xc]"}, {"G6"}),
    ("MU12", "G6 player id is the SITE B cell", {"M347_PATCH_INS": "44aed9=DWORD PTR [esi+0xa50],eax"}, {"G6"}),
    ("MU13", "G7 sentinel lands BEFORE the buffer (algorithm)", {"M347_ALGO": "sentinel_abs"}, {"G7"}),
    ("MU14", "R2 textual census would claim all 13", {"M347_ALGO": "census"}, {"R2"}),
    ("MU15", "R5 receiver-blind census", {"M347_ALGO": "recv"}, {"R5"}),
]


def run(env_extra):
    env = dict(os.environ)
    for k in ("M347_PATCH_INS", "M347_PATCH_IMG", "M347_PATCH_MN", "M347_ALGO"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True,
                       text=True, env=env, timeout=900)
    failed = set(re.findall(r"^FAIL (G\d+|R\d+)", p.stdout, re.M))
    passed = set(re.findall(r"^PASS (G\d+|R\d+)", p.stdout, re.M))
    tail = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "<no output>"
    return failed, passed, tail, p.stderr


def main():
    failed, passed, tail, err = run({})
    print("baseline: %s" % tail)
    if failed or "PASS M347" not in tail:
        print("HARNESS FAIL: baseline is not green")
        print(err[-800:])
        return 1
    base_gates = sorted(passed)
    print("baseline gates: %d PASS, 0 FAIL" % len(passed))
    print()
    print("  id    row defended                                          expected   reddened   verdict")
    bad = []
    for mid, row, env, expect in MUTANTS:
        f, p, tail2, err2 = run(env)
        if mid == "MU0":
            ok = (not f) and ("12/12" in tail2)
            if not ok:
                bad.append((mid, sorted(f), ["baseline red"]))
            print("  %-5s %-52s %-10s %-10s %s" % (mid, row, "-", ",".join(sorted(f)) or "-",
                                                  "BASELINE" if ok else "BAD"))
            continue
        ok = expect <= f and f
        missing = set(base_gates) - set(p) - f
        verdict = "RED" if ok else "NO-OP"
        if not ok or missing:
            bad.append((mid, sorted(f), sorted(missing)))
        print("  %-5s %-52s %-10s %-10s %s"
              % (mid, row, ",".join(sorted(expect)), ",".join(sorted(f)) or "-", verdict))
    print()
    if bad:
        for mid, f, missing in bad:
            print("HARNESS FAIL %s: reddened=%s missing=%s" % (mid, f, missing))
        print("HARNESS FAIL M347: %d/%d scored" % (len(MUTANTS) - len(bad), len(MUTANTS)))
        return 1
    print("HARNESS PASS M347: %d/%d scored, NO-OP [], uncovered []"
          % (len(MUTANTS), len(MUTANTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
