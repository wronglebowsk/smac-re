#!/usr/bin/env python3
"""M385 mutation harness - every VERIFIED row names the mutant that reddens it.

Each mutant rewrites ONE instruction line (M385_PATCH='addr|text') or flips one
algorithm law (M385_ALGO=n), re-runs the instrument, and requires (a) non-zero exit
and (b) the named failing check to appear in the output.  A green mutant is a hole.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "m385_mask_walk.py")

MUTANTS = [
    ("MU0", "G0 the nine-site population is a measurement",
     {"M385_PATCH": "0x574a66|test   DWORD PTR [edx*4+0x94d448],0x20"},
     "G0 nine dynamic sites"),
    ("MU1", "G1 four CONST masks: 0x4dafcf's literal is the reaching def",
     {"M385_PATCH": "0x4dafcf|mov    edi,DWORD PTR [ebp+0x8]"}, "G1 four CONST masks"),
    ("MU2", "G1 const set {0x1000 x2, 0x2000 x2}",
     {"M385_PATCH": "0x4db035|mov    edi,0x1000"}, "G1 const masks are"),
    ("MU3", "G1 four STACKARG sites in two functions",
     {"M385_PATCH": "0x4dacc5|mov    edi,0x800"}, "G1 four STACKARG"),
    ("MU4", "G1 one ORIMM site: `or al,imm` is the nearest def",
     {"M385_PATCH": "0x574a55|add    al,0x20"}, "G1 no UNKNOWN/NONE"),
    ("MU5", "G2 FUN_0x4dabb0 has ZERO direct callers",
     {"M385_PATCH": "0x4db095|call   0x4dabb0"}, "G2 FUN_0x4dabb0 has ZERO direct callers"),
    ("MU6", "G2 FUN_0x4dacc0 has 4 direct callers",
     {"M385_PATCH": "0x4db0a5|call   0x4dabb0"}, "G2 FUN_0x4dacc0 has 4 direct callers"),
    ("MU7", "G2 pushed arg set {0x20,0x400,0x40000,0x2000000}",
     {"M385_PATCH": "0x4db0aa|push   0x410"}, "G2 its pushed arg masks are"),
    ("MU8", "G2 the 0x400 push is what reaches the pair test",
     {"M385_PATCH": "0x4db0aa|push   0x410"}, "G2 the 0x400 mask reaches"),
    ("MU9", "G2 no pushed arg carries 0x800",
     {"M385_PATCH": "0x4db0b6|push   0x800"}, "G2 no pushed arg carries 0x800"),
    ("MU10", "G2/G4 no arg carries the 0xc00 PAIR",
     {"M385_PATCH": "0x4db0aa|push   0xc00"}, "G2 no pushed arg carries the 0xc00 PAIR"),
    ("MU11", "G3 two pre-OR candidates {0x0,0x10}",
     {"M385_PATCH": "0x574a4e|mov    eax,0x400"}, "G3 two pre-OR candidates"),
    ("MU12", "G3 composed set exactly {0x20,0x30}",
     {"M385_PATCH": "0x574a4a|xor    eax,0x8"}, "G3 composed set is exactly"),
    ("MU13", "R1 no mask is a runtime word (def kinds)",
     {"M385_PATCH": "0x4dacc5|mov    edi,DWORD PTR [edi+0x8]"},
     "R1 'some site's mask is a runtime pair word"),
    ("MU14", "R2 FUN_0x4dabb0 is not live",
     {"M385_PATCH": "0x4db0a5|call   0x4dabb0"},
     "R2 'FUN_0x4dabb0 is live"),
    ("MU15", "R3 0x4dadd0's literal sits after the arg load",
     {"M385_PATCH": "0x4dafcf|mov    edi,DWORD PTR [ebp+0x8]"},
     "R3 '0x4dadd0's 0x1000/0x2000 sites inherit the arg' refuted"),
    ("MU16", "R4 `or al` cannot smuggle 0xc00 high bytes",
     {"M385_PATCH": "0x574a4e|mov    eax,0xc00"}, "R4 '0x574a66's high eax bytes"),
    ("MU17", "R5 the wrapper's callers bound the mask",
     {"M385_PATCH": "0x4db0bd|push   0xc00"}, "R5 'the generic wrapper admits any mask' refuted"),
    ("MU18", "G4 NO site can contain 0x800 (bit classifier)",
     {"M385_PATCH": "0x4db09e|push   0x800"}, "G4 NO PROVEN site's mask can contain 0x800"),
    ("MU19", "G4 exactly TWO 0x400 sites",
     {"M385_PATCH": "0x4db0aa|push   0x800"}, "G4 exactly TWO PROVEN sites"),
    ("MU20", "G6 digest pins the verdict table",
     {"M385_PATCH": "0x4db035|mov    edi,0x3000"}, "G6 digest stable and pinned"),
    ("MA1", "ALGO: calls clobber callee-saved edi (def tracer)",
     {"M385_ALGO": "1"}, "G1 no UNKNOWN/NONE"),
    ("MA2", "ALGO: `or al` path join ignored (classifier)",
     {"M385_ALGO": "2"}, "G3 composed set is exactly"),
    ("MA3", "ALGO: 0x400 and 0x800 read as one bit (bit classifier)",
     {"M385_ALGO": "3"}, "G4 NO PROVEN site's mask can contain 0x800"),
    ("MA4", "ALGO: body bounded by the ebp frame, blind to the early ret (attribution)",
     {"M385_ALGO": "4"}, "G1 the four literal sites sit in FUN_0x4dadd0"),
    ("MA5", "ALGO: same attribution law, cross-checked against index.csv",
     {"M385_ALGO": "4"}, "G7 func_of agrees with index.csv"),
    ("MA6", "ALGO: every forward branch counts as an entry (dominance law)",
     {"M385_ALGO": "5"}, "G1 every reaching def DOMINATES"),
    ("MA7", "ALGO: a mis-derived bit column diverges between the two digests",
     {"M385_ALGO": "3"}, "G6 the two derivations agree"),
    ("MU21", "G1 dominance: a branch injected into the def-site gap",
     {"M385_PATCH": "0x4dabbb|jmp    0x4db003"}, "G1 every reaching def DOMINATES"),
    ("MU22", "G2 each call carries exactly one pushed argument",
     {"M385_PATCH": "0x4db0a3|push   eax"}, "G2 each call carries EXACTLY ONE"),
    ("MU23", "G2 the censused file is the pinned 3,067,904-B terran.exe",
     {"M385_TRUNC": "1"}, "G2 the censused file is the 3,067,904-B terran.exe"),
    ("MU24", "G8 the total 0x400-only reader count is counted, not asserted",
     {"M385_PATCH": "0x4db0aa|push   0x800"}, "G8 total 0x400-only readers is 3"),
    ("MU25", "G8 population 15 -> 17",
     {"M385_PATCH": "0x4db0aa|push   0x800"}, "G8 population 15 -> 17"),
]


def run(env):
    e = dict(os.environ)
    for k in ("M385_PATCH", "M385_ALGO", "M385_EXE"):
        e.pop(k, None)
    if env.get("M385_TRUNC"):
        import tempfile
        src = open("/home/paul/reverse/smac/terran.exe", "rb").read()[:1000000]
        fd, path = tempfile.mkstemp(suffix=".exe")
        os.write(fd, src)
        os.close(fd)
        e["M385_EXE"] = path
    e.update({k: v for k, v in env.items() if not k.startswith("M385_TRUNC")})
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


killed = 0
for mid, claim, env, needle in MUTANTS:
    rc, out = run(env)
    hit = needle in out
    ok = rc != 0 and hit
    killed += ok
    print("%-5s %-4s %-78s %s" % (mid, "KILLED" if ok else "ALIVE", claim[:78],
                                  ("" if ok else "rc=%d hit=%s" % (rc, hit))))
print("\n%d/%d mutants killed" % (killed, len(MUTANTS)))
if killed != len(MUTANTS):
    sys.exit(1)
print("PASS M385-mutate: %d/%d" % (killed, len(MUTANTS)))
