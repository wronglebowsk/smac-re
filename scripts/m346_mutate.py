#!/usr/bin/env python3
"""M346 mutation harness -- every VERIFIED row of the NAMED block names the mutant
that reddens it.  Each mutant perturbs one measurement input (an instruction
operand, the literal block at 0x69911c, or the classifier) through the acceptance
script's own hooks; the harness asserts the named gate(s) flip to FAIL, that the
run still executes, and that no OTHER gate is silently the one that caught it.

    python3 -u scripts/m346_mutate.py
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "m346_alert_raiser.py")

# (id, row it defends, env, gates that must redden)
MUTANTS = [
    ("MU0", "baseline (no mutation, must stay 17/17)", {}, set()),
    ("MU1", "completion posts kinds 1 then 2", {"M346_PATCH_INS": "4f0f76=push 0x3"}, {"G2"}),
    ("MU2", "kind-1 payload reads the item table 0x984d38",
     {"M346_PATCH_INS": "4f0f6f=mov edx,DWORD PTR [ecx+0x984d40]"}, {"G3"}),
    ("MU3", "kind-2 payload base array 0x927894",
     {"M346_PATCH_INS": "4f0f8c=lea ecx,[eax*4+0x927898]"}, {"G4"}),
    ("MU4", "both posters share the payload array 0x999ff4",
     {"M346_PATCH_INS": "6265d2=mov DWORD PTR [edx*4+0x999fe4],eax"}, {"G5"}),
    ("MU5", "bound k <= 9 in poster FUN_006265a2",
     {"M346_PATCH_INS": "6265a8=cmp DWORD PTR [ebp+0x8],0x8"}, {"G6"}),
    ("MU6", "text-buffer stride is 0x100", {"M346_PATCH_INS": "626600=shl edx,0x7"}, {"G7"}),
    ("MU7", "expander reads the numeric array 0x999fa4 at 4 sites",
     {"M346_PATCH_INS": "625c2c=mov ecx,DWORD PTR [eax*4+0x999fa8]"}, {"G8"}),
    ("MU8", "text slots are addressed 0x99a01c + (k<<8)",
     {"M346_PATCH_INS": "625dac=add eax,0x99a020"}, {"G8", "G9"}),
    ("MU9", "token vocabulary at 0x69911c",
     {"M346_TOK_FILE": "__TOKF__"}, {"G10"}),
    ("MU10", "drainer clears slot1 0x99a11c",
     {"M346_PATCH_INS": "637315=mov BYTE PTR ds:0x99a11d,0x0"}, {"G11"}),
    ("MU11", "drainer calls the modal runner 0x5f1394 at 0x63732d",
     {"M346_PATCH_INS": "63732d=call 0x5f1395"}, {"G12"}),
    ("MU12", "drainer reads slot2 0x99a21c",
     {"M346_PATCH_INS": "637388=push 0x99a31c"}, {"G13"}),
    ("MU13", "0x985b10 absent from the whole alert chain",
     {"M346_PATCH_INS": "625b29=mov DWORD PTR [ebp-0x10],DWORD PTR ds:0x985b10"}, {"G14"}),
    ("MU14", "0x985b10 absent from the post window",
     {"M346_PATCH_INS": "4f0f40=mov al,ds:0x985b10"}, {"G15"}),
    ("MU15", "no head/tail/count: only the publishers and the drainer clear a slot",
     {"M346_ALGO": "drop_drain"}, {"G16"}),
    ("MU16", "drainer has 0 direct .text callers",
     {"M346_PATCH_INS": "4f0f40=call 0x636b1e"}, {"G17"}),
]


def run(env_extra, tokfile=None):
    env = dict(os.environ)
    for k in ("M346_PATCH_INS", "M346_ALGO", "M346_TOK_FILE"):
        env.pop(k, None)
    e = dict(env_extra)
    if tokfile:
        e["M346_TOK_FILE"] = tokfile
    env.update(e)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True,
                       text=True, env=env, timeout=900)
    failed = set(re.findall(r"^FAIL (G\d+)", p.stdout, re.M))
    passed = set(re.findall(r"^PASS (G\d+)", p.stdout, re.M))
    tail = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "<no output>"
    return failed, passed, tail, p.stderr


def main():
    failed, passed, tail, err = run({})
    print("baseline: %s" % tail)
    if failed or "PASS M346" not in tail:
        print("HARNESS ABORT -- baseline is not green")
        print(err[-800:])
        return 1
    ok = 0
    rows = []
    tf = os.path.join(tempfile.mkdtemp(), "tok.txt")
    with open(tf, "wb") as f:
        f.write(b"$NUM\x00$NUMBER\x00")      # no $HEX, no $LINK<
    for mid, row, env, want in MUTANTS:
        tok = tf if env.get("M346_TOK_FILE") == "__TOKF__" else None
        f2, p2, t2, e2 = run(env, tokfile=tok)
        if mid == "MU0":
            good = not f2 and "PASS M346" in t2
        else:
            good = bool(want) and want <= f2 and not (want & p2)
        rows.append((mid, sorted(f2), t2))
        print("%-5s %-4s %s   red=%s" % (mid, "OK" if good else "BAD", row, sorted(f2)))
        ok += 1 if good else 0
        if not good:
            print("      tail: %s" % t2)
            if e2.strip():
                print("      err : %s" % e2.strip()[-300:])
    print()
    print("%s HARNESS M346: %d/%d" % ("PASS" if ok == len(MUTANTS) else "FAIL", ok, len(MUTANTS)))
    return 0 if ok == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
