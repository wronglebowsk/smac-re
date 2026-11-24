#!/usr/bin/env python3
"""m381_mutate.py - mutation harness for M381.  Each mutant rewrites one instruction of the
parsed dump (or flips an algorithm law) and must redden at least the gate it names; the
identity run must redden none.  `want` is a gate subset: a mutant may redden MORE, never
fewer.

    python3 scripts/m381_mutate.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "m381_bit13_noun.py")

MUTANTS = [
    ("MU1", {"M381_PATCH": "50393d|push   0x1000"}, {"G0", "G5"},
     "the stamp's mask moved 0x2000 -> 0x1000"),
    ("MU2", {"M381_PATCH": "503938|jl     0x50396a"}, {"G4"},
     "jle -> jl: equality would now stamp"),
    ("MU3", {"M381_PATCH": "503936|cmp    eax,0x3e8"}, {"G4"},
     "the threshold replaced by a constant - the peer operand disappears"),
    ("MU4", {"M381_PATCH": "50392d|add    eax,ecx"}, {"G2"},
     "the strength chain's sub -> add: 2095 folds to 2097"),
    ("MU5", {"M381_PATCH": "5038b0|lea    ebx,[ebx*4+0x94f500]"}, {"G6"},
     "the follow-on stat shifted off +0x94f504"),
    ("MU6", {"M381_PATCH": "503944|call   0x551a24"}, {"G0", "G5"},
     "the stamp's call target moved one byte"),
    ("MU7", {"M381_PATCH": "555747|test   ah,0x40"}, {"G7"},
     "one byte-form reader re-pointed one bit up: the census drops to 4"),
    ("MU8", {"M381_PATCH": "5038f4|add    eax,ecx"}, {"G2"},
     "the relations chain loses its +esi - the contrast G2 measures disappears"),
    ("MU9", {"M381_ALGO": "1"}, {"G4"},
     "the strictness law flipped: >= would stamp"),
    ("MU10", {"M381_PATCH": "4db30b|and    eax,0x1000"}, {"G7"},
     "the one dword-form reader re-pointed: the dword census empties"),
    ("MU11", {"M381_PATCH": "503911|mov    eax,DWORD PTR [eax*4+0x94d44c]"}, {"G1"},
     "the acting-row load re-pointed at the next dword: the pinned window breaks"),
    ("MU12", {"M381_PATCH": "50396a|add    edi,0x20b8"}, {"G3"},
     "the walk step off by one dword: 7 iterations become a non-integral count"),
    ("NOOP", {}, set(), "identity: nothing may redden"),
]


def run(env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=env)
    out = p.stdout
    m = re.search(r"^FAIL M381: .*?red: (.+)$", out, re.M)
    if m:
        red = {g.strip() for g in m.group(1).split(",")}
    elif "PASS M381:" in out:
        red = set()
    else:
        red = {"NOPARSE"}
    return red, p.returncode


def main():
    bad = 0
    for name, env, want, text in MUTANTS:
        red, rc = run(env)
        ok = (want <= red) if want else (red == set())
        if not ok:
            bad += 1
        print("%-5s %s  red=%-28s want=%-14s %s"
              % (name, "ok  " if ok else "FAIL", sorted(red), sorted(want), text))
    print("")
    print("%s %d mutants, %d unexpected" %
          ("RUN PASS" if bad == 0 else "RUN FAIL", len(MUTANTS), bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
