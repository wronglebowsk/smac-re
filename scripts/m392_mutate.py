#!/usr/bin/env python3
"""M392 mutation harness - one mutant per VERIFIED row of scripts/m392_uninit_census.py.

A mutant is `killed` only when the instrument exits non-zero AND prints the FAIL text the
row predicts (an incidental traceback is not a kill).

    python3 scripts/m392_mutate.py       # run all
    python3 scripts/m392_mutate.py -v    # echo the failing lines
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = os.path.join(ROOT, "scripts", "m392_uninit_census.py")

# (id, kind, spec, gate, the FAIL text the mutant must produce)
MUTANTS = [
    # -- G0 population: the 65th site and the indirect-call proof
    ("MU0", "code", "0x5844b6|call 0x52a721", "G0", "G0 population != 65"),
    ("MU0b", "algo", "4", "G0", "G0 population != 65"),
    # -- G1 the frame
    ("MU1", "code", "0x52b889|ret 0x18", "G1", "G1 frame != ret 0x1c"),
    ("MU9", "code", "0x52a741|mov ecx,DWORD PTR [ebp+0x18]", "G1", "G1 frame != ret 0x1c"),
    # -- G2 decode: a stack-form argument
    ("MU2", "code", "0x5262f8|mov DWORD PTR [esp],0x0", "G2",
     "G2 1 sites did not decode"),
    # -- G3 the guard census
    ("MU3", "code", "0x5262ec|push 0x0", "G3", "G3 guard census != 1 zero"),
    ("MU5", "code", "0x52d855|push 0x1", "G7", "G7 verdict counts != 64/0/1"),
    ("MU1b", "algo", "1", "G3", "G3 guard census != 1 zero"),
    # -- G4 the message census
    ("MU4", "code", "0x584596|push 0x17", "G4", "G4 msg census != 49 literals"),
    ("MU4b", "algo", "3", "G4", "G4 msg census != 49 literals"),
    # -- G5 the joint
    ("MU6", "code", "0x52d86a|mov eax,0x16", "G5", "G5 joint != 0 closed"),
    # -- G6 the open site's lineage and the block's entries
    ("MU7", "code", "0x52bd33|mov edi,DWORD PTR [ebp+0x8]", "G6",
     "G6 ebx lineage != single def"),
    ("MU8", "code", "0x52be38|je 0x52c423", "G6", "G6 entries into 52d840 changed"),
    ("MU10", "code", "0x52d849|cmp DWORD PTR [ebx+0x10],0x1", "G6",
     "G6 the block now filters +0x10"),
    # -- G8 the rival classifier
    ("MU11", "algo", "6", "G8", "G8 every rival survived"),
]


def envfor(kind, spec):
    return {"M392_PATCH": spec} if kind == "code" else {"M392_ALGO": spec}


def run(env):
    e = dict(os.environ)
    for k in ("M392_PATCH", "M392_ALGO"):
        e.pop(k, None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", INST], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def main():
    verbose = "-v" in sys.argv
    rc, out = run({})
    base_ok = rc == 0 and "PASS M392: 10/10" in out
    print(f"BASELINE {'PASS' if base_ok else 'FAIL'} rc={rc}")
    if not base_ok:
        print(out[-2000:])
        return 1
    print(f"{'id':5s} {'kind':5s} {'gate':5s} {'result':8s} detail")
    killed, bad = 0, []
    for mid, kind, spec, gate, want in MUTANTS:
        rc, out = run(envfor(kind, spec))
        hit = want in out
        good = rc != 0 and hit and "Traceback" not in out
        killed += good
        if good:
            print(f"{mid:5s} {kind:5s} {gate:5s} {'killed':8s} {want!r}")
        else:
            bad.append(mid)
            print(f"{mid:5s} {kind:5s} {gate:5s} {'MISSED':8s} want {want!r} rc={rc} hit={hit}")
            if verbose or not hit:
                tail = [ln for ln in out.splitlines() if ln.startswith(("FAIL", "PASS", "PATCH"))]
                print("        " + (" | ".join(tail[-3:]) or "(no FAIL line)"))
    print(f"\nSUMMARY M392: {killed}/{len(MUTANTS)} killed"
          + ("" if not bad else f"; alive: {','.join(bad)}"))
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
