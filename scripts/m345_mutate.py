#!/usr/bin/env python3
"""M345 mutation harness -- every VERIFIED row of the NAMED block names the
mutant that reddens it.  Each mutant is one byte-level perturbation of the
measurement input (instruction operand text or an image dword) applied through
the acceptance script's own hooks; the harness asserts that the gate(s) that
carry that row flip to FAIL and that the rest of the run still executes.

    python3 -u scripts/m345_mutate.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m345_slot64_dispatch.py")

# (id, row it defends, env, gates that must redden)
MUTANTS = [
    ("MU0", "ACCEPT baseline (no mutation, must stay 12/12)", {}, set()),
    ("MU1", "slot census == 5 data dwords",
     {"M345_PATCH_IMG": "6716b0=404ed0"}, {"G1"}),
    ("MU2", "no .text operand names the slot",
     {"M345_PATCH_INS": "5f3f45=0x5f58fa"}, {"G2"}),
    ("MU3", "0x671644+0x6c aliases 0x67164c+0x64",
     {"M345_PATCH_IMG": "671830=404ed0"}, {"G3"}),
    ("MU4", "ctor installs the CPane vptr at +0x444",
     {"M345_PATCH_INS": "405f3a=DWORD PTR [ecx+0x448],0x671644"}, {"G4"}),
    ("MU5", "slot arity is one (ret 4)",
     {"M345_PATCH_INS": "5f59bc=0x8"}, {"G5"}),
    ("MU6", "19 x call [r+0x64]",
     {"M345_PATCH_INS": "432965=DWORD PTR [edx+0x68]"}, {"G6"}),
    ("MU7", "module [r+0x64] forms are 4 movs, none a dispatch",
     {"M345_PATCH_INS": "5fcc34=DWORD PTR [eax+0x60],0x0"}, {"G8"}),
    ("MU8", "no cached-slot -> call reg pair (evasion detector)",
     {"M345_PATCH_INS": "4b9085=eax,DWORD PTR [edx+0x64];4b9087=eax"}, {"G9"}),
    ("MU9", "arity/BB classifier (algorithm mutant: no block bounds)",
     {"M345_ALGO": "wide"}, {"G10"}),
    ("MU10", "the runner dispatches no +0x64 slot",
     {"M345_PATCH_INS": "5f3d05=DWORD PTR [ecx+0x64]"}, {"G11"}),
]


def run(env_extra):
    env = dict(os.environ)
    for k in ("M345_PATCH_INS", "M345_PATCH_IMG", "M345_ALGO"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True,
                       text=True, env=env, timeout=600)
    failed = set(re.findall(r"^FAIL (G\d+)", p.stdout, re.M))
    passed = set(re.findall(r"^PASS (G\d+)", p.stdout, re.M))
    tail = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "<no output>"
    return failed, passed, tail, p.stderr


def main():
    failed, passed, tail, err = run({})
    print("baseline: %s" % tail)
    if failed or "PASS M345" not in tail:
        print("HARNESS FAIL: baseline is not green")
        print(err[-800:])
        return 1
    base_gates = sorted(passed)
    print("baseline gates: %d PASS, 0 FAIL" % len(passed))
    print()
    print("  id    row defended                                        expected  reddened  verdict")
    bad = []
    for mid, row, env, expect in MUTANTS:
        f, p, tail2, err2 = run(env)
        if mid == "MU0":
            ok = (not f) and ("12/12" in tail2)
            if not ok:
                bad.append((mid, sorted(f), ["baseline red"]))
            print("  %-5s %-48s %-9s %-9s %s" % (mid, row, "-", ",".join(sorted(f)) or "-",
                                                  "BASELINE" if ok else "BAD"))
            continue
        ok = expect <= f and f
        # a surviving gate that was green at baseline must not silently vanish
        missing = set(base_gates) - set(p) - f
        verdict = "RED" if ok else "NO-OP"
        if not ok or missing:
            bad.append((mid, sorted(f), sorted(missing)))
        print("  %-5s %-48s %-9s %-9s %s"
              % (mid, row, ",".join(sorted(expect)), ",".join(sorted(f)) or "-", verdict))
    print()
    if bad:
        for mid, f, missing in bad:
            print("HARNESS FAIL %s: reddened=%s missing=%s" % (mid, f, missing))
        print("HARNESS FAIL M345: %d/%d scored" % (len(MUTANTS) - len(bad), len(MUTANTS)))
        return 1
    print("HARNESS PASS M345: %d/%d scored, NO-OP [], uncovered []"
          % (len(MUTANTS), len(MUTANTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
