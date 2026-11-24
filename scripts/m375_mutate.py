#!/usr/bin/env python3
"""M375 mutation harness - every gate must be reddened by a named mutant.

Each row rewrites ONE instruction (M375_PATCH='addr|text') or flips one algorithm law
(M375_ALGO=n), re-runs the acceptance instrument in a child process, and requires
(a) a non-zero exit, (b) a FAIL line naming the gate it is supposed to redden.
A mutant that leaves the named gate green is a HOLE and is reported as such.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m375_relation_bits.py")

MUT = [
    ("MU1", "patch", "552ce6|nop", "G0",
     "the 0x552ce6 store is the count the census pins"),
    ("MU2", "patch", "53f863|test DWORD PTR [eax*4+0x94d448],0x400000", "G1",
     "the only bit-23 reader"),
    ("MU3", "patch", "53bbed|test BYTE PTR [edi*4+0x94d448],0x80", "G1",
     "0x8000 is read only at byte +1; move the literal to +0 and the reader is lost"),
    ("MU4", "patch", "507d1a|push 0x10", "G2",
     "0x8000's only mask (0x8010) loses the bit"),
    ("MU5", "patch", "552cec|mov DWORD PTR [ebx+0x94d4c8],0x31", "G3",
     "the 50-tick arm on the 0x40 path"),
    ("MU6", "patch", "5552d1|and al,0xff", "G3",
     "the expiry clear of 0x40"),
    ("MU7", "patch", "551b98|and edx,0xffefffff", "G4",
     "the bit-23 clear in the 0x17 block (one direction)"),
    ("MU8", "patch", "547f37|push 0x690174", "G5",
     "one 'Sending TREATY ON' anchor becomes TREATY OFF"),
    ("MU9", "patch", "53fcbd|push 0x400000", "G2",
     "0x100000's only SET mask"),
    ("MU10", "algo", "1", "G4",
     "ALGO 1: treat 0x80000018 as if it carried bit 23 (the lookalike bug)"),
    ("MU11", "algo", "2", "G1",
     "ALGO 2: tracer law - return offset 0 for every 0x94d4xx literal"),
    ("MU12", "algo", "3", "G3",
     "ALGO 3: classifier law - count `and` as a bit setter"),
    ("MU13", "labels", "", "G6",
     "rewrite one diplomacy label line: the M367 anchor self-check can no longer align"),
]


def run(env_extra):
    env = dict(os.environ)
    env.pop("M375_PATCH", None)
    env.pop("M375_ALGO", None)
    env.pop("M375_LABELS", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True,
                       env=env, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def mutated_labels():
    """copy labels.txt with the 'Commlink' row (element 875) rewritten."""
    src = os.path.join(ROOT, "programs/labels.txt")
    dst = os.path.join(ROOT, "scratch/m375_labels_mut.txt")
    lines = open(src, "rb").read().split(b"\n")
    hdr = next(i for i, ln in enumerate(lines) if ln.strip() == b"#LABELS")
    el0 = hdr + 2
    lines[el0 + 0xDAC // 4] = b"NotACommlink"
    open(dst, "wb").write(b"\n".join(lines))
    return dst


base_rc, base_out = run({})
print(f"baseline: rc={base_rc} {base_out.strip().splitlines()[-1][:90]}")
if base_rc != 0:
    print("HARNESS CANNOT RUN: the baseline acceptance is already red")
    sys.exit(2)


killed = 0
holes = []
for mid, kind, arg, gate, why in MUT:
    if kind == "patch":
        env = {"M375_PATCH": arg}
    elif kind == "algo":
        env = {"M375_ALGO": arg}
    else:
        env = {"M375_LABELS": mutated_labels()}
    rc, out = run(env)
    fails = [ln for ln in out.splitlines() if ln.startswith("FAIL M375")]
    hit = bool(fails) and re.search(r'\b%s\b' % gate, fails[0])
    if rc != 0 and hit:
        killed += 1
        print(f"  ok   {mid:5s} {gate} red   {why}")
    else:
        holes.append(mid)
        print(f"  HOLE {mid:5s} {gate} still green  {why}")
        if fails:
            print(f"        (fail line: {fails[0][:110]})")
print(f"\nM375 mutants: {killed}/{len(MUT)} killed, {len(holes)} hole(s)"
      + ("  " + ",".join(holes) if holes else ""))
sys.exit(0 if not holes else 1)
