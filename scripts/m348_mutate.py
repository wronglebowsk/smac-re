#!/usr/bin/env python3
"""M348 mutation harness -- every VERIFIED row of the NAMED block names the mutant
that reddens it.  Each mutant perturbs ONE input (a byte in terran.exe, an
instruction line in the .text dump, or the Script.txt record) and the harness
asserts the named gate flips to FAIL, the run still executes, and no gate other
than the declared side effects turns red.

    python3 -u scripts/m348_mutate.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m348_slot_template.py")

# (id, row it defends, env, expected failing gates)
MUTANTS = [
    ("MU0", "baseline (no mutation, must stay 12/12)", {}, set()),
    ("MU1", "slot text stride is k<<8", {"M348_PATCH_INS": "626600=shl edx,0x7"}, {"G1"}),
    ("MU2", "setter A returns 3 above k=9", {"M348_PATCH_INS": "6265ae=mov eax,0x2"}, {"G2"}),
    ("MU3", "setter A resolves through the label table 0x997b28",
     {"M348_PATCH_INS": "62660e=mov ecx,0x997b2c"}, {"G3"}),
    ("MU4", "the second post is the literal setter 0x626634",
     {"M348_PATCH_INS": "4f0f96=call 0x6265a2"}, {"G4"}),
    ("MU5", "slot-1 reads the item table at 0x984d38",
     {"M348_PATCH_INS": "4f0f6f=mov edx,DWORD PTR [ecx+0x984d40]"}, {"G5"}),
    ("MU6", "slot-2 stride is ebx*1436 (shl 3 in the chain)",
     {"M348_PATCH_INS": "4f0f87=shl eax,0x2"}, {"G6"}),
    ("MU7", "the key literal is PRODUCEX", {"M348_PATCH_BIN": "0x68cfcb=59"}, {"G7"}),
    ("MU8", "FUN_0048f100 sets slot 0 from [0x8f0d60]+0x13",
     {"M348_PATCH_INS": "48f209=add edx,0x14"}, {"G8"}),
    ("MU9", "#PRODUCEXQ consumes slot 1 via $ITEM1",
     {"M348_SCRIPT_EDIT": "PRODUCEXQ:$BASENAME0 builds $ITEM2."}, {"G9"}),
    ("MU10", "no .rdata string carries a $< token",
     {"M348_PATCH_BIN": "0x682000=24 3c 31 3a 78 3e 00"}, {"G10"}),
    ("MU11", "the expander's slot-text address is k<<8 + 0x99a01c",
     {"M348_PATCH_INS": "625da9=shl ecx,0x7"}, {"G11"}),
    ("MU12", "FUN_00636b1e draws the session-field labels",
     {"M348_PATCH_BIN": "0x6998bc=3f"}, {"G12"}),
]


def run(env_extra):
    env = dict(os.environ)
    for k in ("M348_PATCH_BIN", "M348_PATCH_INS", "M348_SCRIPT_EDIT"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=120)
    red = set(re.findall(r"^  (G\d+)\s+FAIL", p.stdout, re.M))
    m = re.search(r"^RESULT (PASS|FAIL): (\d+)/(\d+) gates", p.stdout, re.M)
    return p.returncode, red, (m.group(1), int(m.group(2)), int(m.group(3))) if m else None


ok = 0
for mid, row, env, want in MUTANTS:
    rc, red, res = run(env)
    if mid == "MU0":
        good = rc == 0 and res and res[0] == "PASS" and not red
    else:
        good = rc != 0 and want <= red and red <= want
    print("%-5s %-4s %-62s red=%s result=%s" % (
        mid, "PASS" if good else "FAIL", row[:62], sorted(red) or "-", res))
    ok += good
print("HARNESS %s: %d/%d" % ("PASS" if ok == len(MUTANTS) else "FAIL", ok, len(MUTANTS)))
sys.exit(0 if ok == len(MUTANTS) else 1)
