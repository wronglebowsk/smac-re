#!/usr/bin/env python3
"""M387 mutation harness - one mutant per VERIFIED row of scripts/m387_last_two.py.

A mutant is `killed` only when the instrument exits non-zero AND prints the FAIL text the
row predicts (an incidental traceback is not a kill).

    python3 scripts/m387_mutate.py       # run all
    python3 scripts/m387_mutate.py -v    # echo the failing lines
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = os.path.join(ROOT, "scripts", "m387_last_two.py")

# (id, kind, spec, gate, the FAIL text the mutant must produce)
MUTANTS = [
    # -- G0/G1 population and frame
    ("MU10", "code", "0x551b1d|mov DWORD PTR [eax+0x94d44c],edx", "G0",
     "G0 the population is not the 27"),
    ("MU11", "code", "0x52ad64|jmp DWORD PTR [eax*4+0x52ba1c]", "G1",
     "G1 the jump-table set changed"),
    # -- G2 lineage
    ("MU1", "code", "0x52affb|mov DWORD PTR [ebp-0x48],edx", "G2",
     "G2 -0x50: lineage changed"),
    ("MU2", "code", "0x52b004|mov DWORD PTR [ebp-0x48],edx", "G2",
     "G2 -0x4c: lineage changed"),
    ("MU6", "code", "0x52aff5|mov edx,DWORD PTR [eax+0x94d488]", "G2",
     "G2 -0x50: lineage changed"),
    ("MU7", "code", "0x52b9c4|mov edx,DWORD PTR [ebp-0x48]", "G2",
     "G2 -0x50: lineage changed"),
    # -- G3 the witness guard shapes
    ("MU12", "code", "0x52a759|jl 0x52aadb", "G3",
     "G3 the witness guards changed shape"),
    # -- G4 the parameter
    ("MU4", "code", "0x52a752|movsx eax,WORD PTR [ebp+0xc]", "G4",
     "G4 [ebp+0x8] is not a read-only invariant"),
    ("MU5", "code", "0x52ad45|movsx eax,WORD PTR [ebp+0xc]", "G4",
     "G4 [ebp+0x8] is not a read-only invariant"),
    # -- G5 pinned reachability
    ("MU3", "code", "0x52b904|je 0x52ba03", "G5",
     "G5 the store is not reachable for exactly message 0x16"),
    # -- G6 the avoiding set
    ("MU13", "code", "0x52af30|je 0x52b205", "G6", "pass NEITHER guard"),
    # -- G7 the loop count
    ("MU8", "code", "0x52a9e7|mov esi,0x0", "G7",
     "G7 the count for m=0x16 is not 1"),
    # -- G8 the arg7 guard shape
    ("MU9", "code", "0x52af21|test ecx,ecx", "G8",
     "G8 the arg7 guard changed shape"),
    # -- G9 bit 0x20
    ("MU14", "code", "0x52aff5|test BYTE PTR [eax+0x94d449],0x20", "G9",
     "G9 a bit-0x20 test exists in this function"),
    # -- the classifier's algorithm laws
    ("MU20", "algo", "1", "G4", "G4 [ebp+0x8] is not a read-only invariant"),
    ("MU21", "algo", "2", "G5", "G5 the store is not reachable for exactly message 0x16"),
    ("MU22", "algo", "3", "G7", "G7 the count for m=0x16 is not 1"),
    ("MU23", "algo", "4", "G8", "G8 the epilogue DOES read [ebp+0x1c]"),
    ("MU24", "algo", "5", "G5", "G5 the store is not reachable for exactly message 0x16"),
    ("MU25", "algo", "6", "G1", "G1 the CFG is not closed"),
]


def envfor(kind, spec):
    return {"M387_PATCH": spec} if kind == "code" else {"M387_ALGO": spec}


def run(env):
    e = dict(os.environ)
    for k in ("M387_PATCH", "M387_ALGO"):
        e.pop(k, None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", INST], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def main():
    verbose = "-v" in sys.argv
    rc, out = run({})
    base_ok = rc == 0 and "PASS M387: 11/11" in out
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
                tail = [ln for ln in out.splitlines() if ln.startswith(("FAIL", "PASS"))]
                print("        " + (" | ".join(tail[-3:]) or "(no FAIL line)"))
    print(f"\nSUMMARY M387: {killed}/{len(MUTANTS)} killed"
          + ("" if not bad else f"; alive: {','.join(bad)}"))
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
