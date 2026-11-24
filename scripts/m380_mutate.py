#!/usr/bin/env python3
"""M380 mutation harness - one mutant per VERIFIED row of scripts/m380_diplo_power.py.

Every row the milestone calls VERIFIED must name a mutant that REDDENS it.  A mutant is
`killed` only when the instrument exits non-zero AND prints the failure the row predicts;
a mutant that merely crashes counts as killed only if the crash is the predicted FAIL line
(no traceback is accepted as a kill).

    python3 scripts/m380_mutate.py            # run all
    python3 scripts/m380_mutate.py -v         # also echo each mutant's FAIL line
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = os.path.join(ROOT, "scripts", "m380_diplo_power.py")

# (id, gate, env, the FAIL text the mutant must produce)
MUTANTS = [
    ("MU1", "G0", {"M380_PATCH": "0x4f9e35|shl edx,0x5"},
     "scaled sites are not 19/19"),
    ("MU2", "G0", {"M380_ALGO": "1"},
     "field offset in the block is not 0x105c"),
    ("MU3", "G1", {"M380_PATCH": "0x59efb1|mov DWORD PTR [esi+0x94e490],ebx"},
     "field is not inside the reset runs"),
    ("MU4", "G2", {"M380_PATCH": "0x54dcf2|jg 0x54dcfb"},
     "does not select MIGHTY"),
    ("MU5", "G2", {"M380_ALGO": "3"},
     "does not select MIGHTY"),
    ("MU6", "G3", {"M380_PATCH": "0x545d4a|call 0x53a9c0"},
     "dispatch arms do not all resolve"),
    ("MU7", "G3", {"M380_ALGO": "7"},
     "dispatch arms do not all resolve"),
    ("MU8", "G3", {"M380_PATCH": "0x53bf57|push 0x6905a8"},
     "does not push REJTREATYMEEK"),
    ("MU9", "G4", {"M380_PATCH": "0x545d58|jne 0x545d64"},
     "edi test does not go straight to the tail"),
    ("MU10", "G4", {"M380_ALGO": "4"},
     "mode-3 arm is not"),
    ("MU11", "G5", {"M380_PATCH": "0x55542d|and ah,0xff"},
     "expected 2 provable stamp droppers"),
    ("MU12", "G5", {"M380_PATCH": "0x551b17|and edx,0xfaeff378"},
     "expected 2 provable stamp droppers"),
    ("MU13", "G5", {"M380_ALGO": "5"},
     "expected 2 provable stamp droppers"),
    ("MU14", "G5", {"M380_ALGO": "6"},
     "store population is not 27"),
    ("MU15", "G1", {"M380_PATCH": "0x5579e0|sar eax,0x2"},
     "accumulator shape is incomplete"),
    ("MU16", "G1", {"M380_PATCH": "0x59efb1|mov DWORD PTR [esi+0x94e48c],eax"},
     "create run is not entirely ZEROING"),
    ("MU17", "G4", {"M380_PATCH": "0x545cd4|mov edx,DWORD PTR ds:0x920780"},
     "edi is not provably sete"),
    ("MU18", "G0", {"M380_ALGO": "2"},
     "emitted multiplier"),
    ("MU19", "G2", {"M380_ALGO": "8"},
     "do not decode to MIGHTY/MEEK"),
]


def run(env):
    e = dict(os.environ)
    e.pop("M380_PATCH", None)
    e.pop("M380_ALGO", None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", INST], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def main():
    verbose = "-v" in sys.argv
    rc, out = run({})
    base_ok = rc == 0 and "PASS M380: 7/7" in out
    print(f"BASELINE {'PASS' if base_ok else 'FAIL'} rc={rc}")
    if not base_ok:
        print(out[-2000:])
        return 1
    print(f"{'id':6s} {'gate':5s} {'result':8s} detail")
    killed = 0
    bad = []
    for mid, gate, env, want in MUTANTS:
        rc, out = run(env)
        hit = want in out
        ok = rc != 0 and hit and "Traceback" not in out
        killed += ok
        if ok:
            print(f"{mid:6s} {gate:5s} {'killed':8s} {want!r}")
        else:
            bad.append(mid)
            print(f"{mid:6s} {gate:5s} {'MISSED':8s} want {want!r} rc={rc} hit={hit}")
            if verbose or not hit:
                tail = [ln for ln in out.splitlines() if ln.startswith(("FAIL", "PASS"))]
                print("        " + " | ".join(tail[-3:]) or "        (no FAIL line)")
    print(f"\nSUMMARY M380: {killed}/{len(MUTANTS)} killed"
          + ("" if not bad else f"; alive: {','.join(bad)}"))
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
