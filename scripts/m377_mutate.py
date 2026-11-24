#!/usr/bin/env python3
"""M377 mutation harness - every VERIFIED row of the M377 block names the mutant that
reddens it.  Each mutant runs scripts/m377_companion_bits.py in a child process with
M377_PATCH or M377_ALGO set and must produce the NAMED gate's FAIL line.

Coverage map (gate <- mutant):
  G0 carriers      MU1 / MU2 / MU3 (drop a mask) / MU4 (mask slot off by one)
  G1 hosts         MU5 (an argument push becomes an immediate)
  G2 reach         MU6 (a gate jump becomes unconditional) / MU7 (jcc is not a gate)
                   MU16 (the status-clear call before the stamp is retargeted)
  G3 readers       MU8 (the byte test tests another bit) / MU9 (only dword tests count)
                   MU18 (the lifted register is clobbered before its test)
  G4 reader act    MU10 (the logged string is rewritten) / MU15 (the 0x94e48c compare
                   vanishes) / MU17 (the reader host's caller is retargeted)
  G5 callers       MU11 (a call site is retargeted)
  G6 erasure       MU12 (the store-shape algebra is forced to find a clearer)
  G7 rivals        MU13 (rel&0x8 becomes rel&0x4 -> the contact rival would HOLD)
  G8 digest        MU14 (a row is dropped from the digest)
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTR = os.path.join(ROOT, "scripts/m377_companion_bits.py")

MUTANTS = [
    ("MU1", {"M377_PATCH": "0x507d1a|push 0x10"}, "FAIL G0 carrier table",
     "the war host's mask loses its companion bit 0x8000"),
    ("MU2", {"M377_PATCH": "0x5526b3|push 0x4"}, "FAIL G0 carrier table",
     "the contact host's setter call loses 0x10000"),
    ("MU3", {"M377_PATCH": "0x54d2e5|push 0x10000"}, "FAIL G0 carrier table",
     "the dialogue variant's mask loses the truce bit"),
    ("MU4", {"M377_ALGO": "3"}, "FAIL G0 carrier table",
     "the mask is read one push off the (a,b,mask) slot"),
    ("MU5", {"M377_PATCH": "0x552687|push 0x7"}, "FAIL G1",
     "one pair argument is pushed as an immediate"),
    ("MU6", {"M377_PATCH": "0x5526b1|jmp 0x5526c2"}, "FAIL G2",
     "the rel&0x8 gate becomes an unconditional skip"),
    ("MU7", {"M377_ALGO": "1"}, "FAIL G2",
     "conditional jumps are treated as non-gates"),
    ("MU8", {"M377_PATCH": "0x53bbed|test BYTE PTR [edi*4+0x94d449],0x40"}, "FAIL G3",
     "the byte reader tests bit 14 instead of bit 15"),
    ("MU9", {"M377_ALGO": "5"}, "FAIL G3",
     "only dword tests count, so byte +1 readers vanish"),
    ("MU10", {"M377_PATCH": "0x54738d|push 0x690160"}, "FAIL G4",
     "the skipped block logs a different string"),
    ("MU11", {"M377_PATCH": "0x5543e6|call 0x552860"}, "FAIL G5",
     "one of the two contact-host call sites is retargeted"),
    ("MU12", {"M377_ALGO": "6"}, "FAIL G6",
     "the store-shape algebra is forced to claim a provable clearer"),
    ("MU13", {"M377_PATCH": "0x55261a|and edx,0x4"}, "FAIL G7",
     "the gate's source becomes rel&0x4, so the no-contact rival would hold"),
    ("MU14", {"M377_ALGO": "8"}, "FAIL G8",
     "one digest row is dropped"),
    ("MU15", {"M377_PATCH": "0x53bc1c|cmp edi,edi"}, "FAIL G4",
     "the 0x53bbed bit-set path loses its 0x94e48c compare"),
    ("MU16", {"M377_PATCH": "0x507d0d|call 0x5076e0"}, "FAIL G2",
     "FUN_00507ce0's status-clear call is retargeted"),
    ("MU17", {"M377_PATCH": "0x545d4a|call 0x53bba0"}, "FAIL G4",
     "the 0x53bbed host's only caller is retargeted"),
    ("MU18", {"M377_PATCH": "0x532fad|mov al,0x7"}, "FAIL G3",
     "the lift reader's register is clobbered between load and test"),
]


def run(env):
    e = dict(os.environ)
    e.pop("M377_PATCH", None)
    e.pop("M377_ALGO", None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", INSTR], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


killed = 0
for mid, env, sig, why in MUTANTS:
    rc, out = run(env)
    hit = sig in out
    gate = sig.replace("FAIL ", "").split()[0].rstrip(":")
    print(f"{mid:5s} {gate:4s} {'KILLED' if hit else 'SURVIVED':9s} rc={rc}  {why}")
    if hit:
        killed += 1
    else:
        print("      expected signature:", sig)
        for ln in out.splitlines():
            if ln.startswith("FAIL"):
                print("      got:", ln)
                break
print(f"\nM377 mutate: {killed}/{len(MUTANTS)} killed")
sys.exit(0 if killed == len(MUTANTS) else 1)
