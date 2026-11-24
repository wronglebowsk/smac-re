#!/usr/bin/env python3
"""M383 mutation harness - one mutant per VERIFIED row of scripts/m383_composition.py.

A mutant is `killed` only when the instrument exits non-zero AND prints the FAIL text the
row predicts (an incidental traceback is not a kill).

    python3 scripts/m383_mutate.py       # run all
    python3 scripts/m383_mutate.py -v    # echo the failing lines
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = os.path.join(ROOT, "scripts", "m383_composition.py")

# (id, gate, env, the FAIL text the mutant must produce)
MUTANTS = [
    # -- the composition (K) rows: ("id", "code", "addr|new text", gate, the FAIL text)
    ("MU1", "code", "0x5579ea|mov DWORD PTR [ebx+0x94e490],edx", "K0", "K0 not 3 stores"),
    ("MU2", "code", "0x5579ce|imul eax,ebx", "K1", "K1 term is not"),
    ("MU3", "code", "0x5579c9|add ecx,0x7", "K1", "K1 term is not"),
    ("MU4", "code", "0x5579e0|sar eax,0x2", "K1", "K1 term is not"),
    ("MU5", "code", "0x557985|mov al,BYTE PTR [edx*4+0x98adb0]", "K2",
     "do not read the type record"),
    ("MU6", "code", "0x5579a7|mov cl,BYTE PTR [eax*4+0x98adad]", "K2",
     "do not read the type record"),
    ("MU7", "code", "0x557a03|imul eax,ecx", "K4",
     "K4 the sibling accumulator does not take A alone"),
    ("MU8", "code", "0x556c95|shl esi,0x3", "K5", "K5 [ebp-8] is not the 52*unit"),
    ("MU9", "code", "0x5706c6|shl eax,0x3", "K3",
     "does not index a 0x10-stride byte table"),
    # -- the relations (R) rows
    ("MU10", "code", "0x55542d|or ah,0x7f", "R0", "R0 the provable droppers are not the 2"),
    ("MU11", "code", "0x555a38|mov eax,DWORD PTR [ebx+0x94d468]", "R0",
     "R0 the unresolved set changed"),
    ("MU12", "code", "0x552cb7|mov ecx,0xffff3fff", "R0",
     "R0 the provable droppers are not the 2"),
    ("MU13", "code", "0x551d1d|and edx,0xefff", "R0",
     "R0 the provable droppers are not the 2"),
    # -- the classifier's algorithm laws
    ("A1", "algo", "1", "K0", "K0 not 3 stores"),
    ("A2", "algo", "2", "K1", "K1 the stored value does not parse"),
    ("A3", "algo", "3", "K1", "K1 the stored value does not parse"),
    ("A4", "algo", "4", "K1", "K1 the stored value does not parse"),
    ("A5", "algo", "5", "K1", "K1 term is not"),
    ("A6", "algo", "6", "K2", "the type index is not 52*type"),
    ("A7", "algo", "7", "K4", "K4 the sibling accumulator does not take A alone"),
    ("A8", "algo", "8", "K5", "K5 [ebp-8] is not the 52*unit"),
    ("A9", "algo", "9", "R0", "R0 the unresolved set changed"),
    ("A10", "algo", "10", "R1", "R1 resolved"),
    ("A11", "algo", "11", "R0", "R0 the provable droppers are not the 2"),
]


def envfor(kind, spec):
    return {"M383_PATCH": spec} if kind == "code" else {"M383_ALGO": spec}


def run(env):
    e = dict(os.environ)
    for k in ("M383_PATCH", "M383_ALGO"):
        e.pop(k, None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", INST], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def main():
    verbose = "-v" in sys.argv
    rc, out = run({})
    base_ok = rc == 0 and "PASS M383: 9/9" in out
    print(f"BASELINE {'PASS' if base_ok else 'FAIL'} rc={rc}")
    if not base_ok:
        print(out[-2000:])
        return 1
    print(f"{'id':5s} {'kind':5s} {'gate':5s} {'result':8s} detail")
    killed = 0
    bad = []
    for mid, kind, spec, gate, want in MUTANTS:
        rc, out = run(envfor(kind, spec))
        hit = want in out
        ok = rc != 0 and hit and "Traceback" not in out
        killed += ok
        if ok:
            print(f"{mid:5s} {kind:5s} {gate:5s} {'killed':8s} {want!r}")
        else:
            bad.append(mid)
            print(f"{mid:5s} {kind:5s} {gate:5s} {'MISSED':8s} want {want!r} rc={rc} hit={hit}")
            if verbose or not hit:
                tail = [ln for ln in out.splitlines() if ln.startswith(("FAIL", "PASS"))]
                print("        " + (" | ".join(tail[-3:]) or "(no FAIL line)"))
    print(f"\nSUMMARY M383: {killed}/{len(MUTANTS)} killed"
          + ("" if not bad else f"; alive: {','.join(bad)}"))
    return 0 if killed == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
