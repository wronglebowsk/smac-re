#!/usr/bin/env python3
"""M382 mutation harness — every VERIFIED claim row names the mutant that reddens it.

Each mutant rewrites ONE instruction line in memory (M382_PATCH='addr|text') or flips
one algorithm law (M382_ALGO=n), re-runs the instrument, and requires (a) non-zero exit
and (b) the named failing check to appear in the output.  A mutant that stays green is a
hole in the acceptance, not a result.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "m382_treaty_readers.py")

MUTANTS = [
    # id, claim row, env
    ("MU1", "G1/G4 0x4ec9c3 asks 0xc30", {"M382_PATCH": "0x4ec9c3|test   DWORD PTR [edx*4+0x94d448],0x410"},
     "G1 five 0xc00-paired"),
    ("MU2", "G4 0x523a7c's extra 0x40000", {"M382_PATCH": "0x523a7c|test   DWORD PTR [ecx*4+0x94d448],0xc30"},
     "G4 paired-mask extras"),
    ("MU3", "G4 0x563165's extra 0x20", {"M382_PATCH": "0x563165|test   DWORD PTR [edi*4+0x94d448],0xc10"},
     "G4 paired-mask extras"),
    ("MU4", "G1 0x56a8a2 is a paired reader", {"M382_PATCH": "0x56a8a2|test   DWORD PTR [edi*4+0x94d448],0x810"},
     "G1 five 0xc00-paired"),
    ("MU5", "G4 0x5859ae's extra 0x1", {"M382_PATCH": "0x5859ae|test   DWORD PTR [ecx*4+0x94d448],0xc10"},
     "G4 paired-mask extras"),
    ("MU6", "G4 0x5567bb's mask is 0xc10", {"M382_PATCH": "0x5567bb|test   eax,0x810"},
     "G4 register masks equal the pinned"),
    ("MU7", "G3 0x5552ff is the sole 0x400-only reader",
     {"M382_PATCH": "0x5552ff|test   ah,0x2"}, "G2 register readers 8"),
    ("MU8", "G3 0x5468c7 asks bits 2|16, not 0xc00",
     {"M382_PATCH": "0x5468c7|test   ah,0x4"}, "G3 six of seven"),
    ("MU9", "G4 three single-bit register readers",
     {"M382_PATCH": "0x560b77|test   ah,0x8"}, "G4 register readers may ask one bit alone"),
    ("MU10", "G2 high-byte masks are shifted (algorithm)",
     {"M382_ALGO": "10"}, "G2 register readers 8"),
    ("MU11", "G5 polarity law: je falls through on zero (algorithm)",
     {"M382_ALGO": "15"}, "G8 digest pinned"),
    ("MU12", "G9 attribution law: the containing range is inclusive-left/exclusive-right (algorithm)",
     {"M382_ALGO": "13"}, "G9 every named site sits in its pinned function"),
    ("MU13", "G0 the field-ref count is 653 not 658 (algorithm)",
     {"M382_ALGO": "14"}, "G0 field refs 653"),
    ("MU14", "R2 the 2095 fold (0x4ec9c3)",
     {"M382_PATCH": "0x4ec9bc|shl    edx,0x3"}, "R2"),
    ("MU15", "R2 the 2095 fold (0x563165)",
     {"M382_PATCH": "0x56315e|shl    edi,0x2"}, "R2"),
    ("MU16", "G5/G8 branch polarity is part of the table",
     {"M382_PATCH": "0x523a87|jne    0x523b11"}, "G8 digest pinned"),
    ("MU17", "G6 the 0x810-only sites are not 0xc00",
     {"M382_PATCH": "0x558cbd|test   DWORD PTR [edx*4+0x94d448],0xc10"}, "G6 two 0x810-only"),
    ("MU19", "R2 the fold's seed mov A,B", {"M382_PATCH": "0x4ec9b2|mov    ecx,esi"}, "R2"),
    ("MU20", "G3 0x5468c7's first test is bit 2", {"M382_PATCH": "0x5468c7|test   al,0x8"},
     "G3 0x5468c7 tests al,0x4"),
    ("MU21", "G3 0x5468c7's second test is bit 16", {"M382_PATCH": "0x5468cb|test   eax,0x20000"},
     "G3 0x5468c7 then tests eax,0x10000"),
    ("MU22", "G4 one reader asks 0x400 alone", {"M382_PATCH": "0x560b77|test   ah,0x4"},
     "G4 exactly one reader asks 0x400 alone"),
    ("MU23", "G5 the jcc is adjacent to its test", {"M382_PATCH": "0x523a87|nop"},
     "G5 all 15 sites' jcc"),
    ("MU24", "G2 load count 144", {"M382_PATCH": "0x546cd8|mov    eax,DWORD PTR [ecx+0x94d44c]"},
     "G2 loads scanned 144"),
    ("MU18", "G1 nine dynamic-mask inline sites",
     {"M382_PATCH": "0x4db0f0|test   DWORD PTR [edx*4+0x94d448],edi"}, "G1 dynamic-mask inline sites 9"),
]


def run(env):
    e = dict(os.environ)
    e.pop("M382_PATCH", None)
    e.pop("M382_ALGO", None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def main():
    print("M382 mutants — %d claims" % len(MUTANTS))
    killed = 0
    rows = []
    for mid, claim, env, want in MUTANTS:
        rc, out = run(env)
        ok = rc != 0 and want in out and "Traceback" not in out
        line = out.strip().splitlines()[-1] if out.strip() else ""
        rows.append((mid, "KILL" if ok else "SURVIVED", claim, line[:70]))
        print("  %-5s %-8s %-58s %s" % (mid, "KILL" if ok else "SURVIVED", claim[:58], line[:70]))
        killed += ok
    base_rc, base_out = run({})
    base_ok = base_rc == 0 and "PASS M382: 35/35" in base_out
    print("\n  baseline %s" % ("PASS (35/35)" if base_ok else "BROKEN"))
    print("\n%s M382 harness: %d/%d killed, baseline %s"
          % ("PASS" if killed == len(MUTANTS) and base_ok else "FAIL",
             killed, len(MUTANTS), "green" if base_ok else "red"))
    return 0 if killed == len(MUTANTS) and base_ok else 1


if __name__ == "__main__":
    sys.exit(main())
