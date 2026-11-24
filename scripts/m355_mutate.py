#!/usr/bin/env python3
"""M355 mutation harness — every VERIFIED row of NAMED ## M355 names its mutant.

Two lever types, both exercised:
  * M355_PATCH='<addr>|<new instruction text>' rewrites ONE .text-cache line
    (a real code mutant: an immediate, a gate bit, a key push, a store target,
    a call target, the emit-loop bound);
  * M355_ALGO=n mutates the INSTRUMENT'S OWN law (mandatory for a tracer/
    classifier — this instrument has four such laws):
      1 = the emit loop walks bits 0..31 (order reversed)
      2 = the emit start bit is misread from the cmp immediate (8), not the mov (0x1f)
      3 = the 6-arg push roles are rotated by one (key read as default)
      4 = `sbb R,R` is ignored (the -1/0 selector collapses)
      5 = the getter dispatch store is not looked ahead (field map blind)

Each mutant must turn the NAMED gate RED. A mutant that leaves the run green is a
harness failure, not a pass. NO-OP controls must stay green.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m355_laptop_masks.py")

# (name, env, gate that must redden, what it breaks)
MUTANTS = [
    ("MU1", {"M355_PATCH": "0x58ea12|and    esi,0xfff80000"}, "G2",
     "the Preferences select-mask takes B's AND immediate (masks recompute)"),
    ("MU2", {"M355_PATCH": "0x58ea23|or     esi,0x40"}, "G3",
     "the Difficulty gate ORs bit 6 instead of bit 5"),
    ("MU3", {"M355_PATCH": "0x58ea1e|cmp    eax,0x3"}, "G3",
     "the Difficulty threshold moves from 2 to 3"),
    ("MU4", {"M355_PATCH": "0x58eaf1|push   0x692760"}, "G1",
     "the Preferences read requests the More Preferences key"),
    ("MU5", {"M355_PATCH": "0x58e688|push   0x6926e8"}, "G1",
     "getter A reads the literal '0' instead of `Laptop` (one read site leaves the set)"),
    ("MU6", {"M355_PATCH": "0x493b10|mov    DWORD PTR [esi+0xa60],eax"}, "G5",
     "getter A's mask is stored to +0xa60, outside the OR'd field set"),
    ("MU7", {"M355_PATCH": "0x492464|mov    ds:0x92bf00,eax"}, "G5",
     "the APPLY handler writes the Preferences OR into the More Preferences cell"),
    ("MU8", {"M355_PATCH": "0x58ea18|add    esi,0xbbe1dd97"}, "G2",
     "the Preferences addend moves by one (all four masks change)"),
    ("MU9", {"M355_PATCH": "0x493b79|call   0x58e640"}, "G5",
     "the last getter-B dispatch becomes getter A (census + field map)"),
    ("MU10", {"M355_PATCH": "0x58e6ab|and    eax,0xfff80000"}, "G2",
     "getter A's AND immediate no longer agrees with the loader's"),
    ("MU11", {"M355_PATCH": "0x493b68|mov    DWORD PTR [esi+0xa49],eax"}, "G5",
     "the constant-mask getter's store lands inside the +0xa48 field"),
    ("MU12", {"M355_ALGO": "1"}, "G4",
     "ALGO 1: the emit loop walks bits 0..31 -> the strings no longer re-parse"),
    ("MU13", {"M355_ALGO": "2"}, "G4",
     "ALGO 2: the emit start bit is read as 8 -> every default string truncates"),
    ("MU14", {"M355_ALGO": "3"}, "G1",
     "ALGO 3: 6-arg push roles rotated -> the key arg is read as the default"),
    ("MU15", {"M355_ALGO": "4"}, "G2",
     "ALGO 4: the -1/0 selector is ignored -> the two masks collapse into one"),
    ("MU16", {"M355_ALGO": "5"}, "G5",
     "ALGO 5: dispatch store look-ahead disabled -> the field map goes blind"),
]

NO_OP = [{}, {"M355_ALGO": ""}]


def run(env):
    e = dict(os.environ)
    for k in ("M355_PATCH", "M355_ALGO"):
        e.pop(k, None)
    e.update(env)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def gate_state(out, gate):
    """PASS/FAIL of one gate id (G2 covers G2a..d: red if ANY sub-gate is red)."""
    states = re.findall(r"^\[(PASS|FAIL)\] (%s\w*)" % re.escape(gate), out, re.M)
    if not states:
        return None
    return "FAIL" if any(st == "FAIL" for st, _ in states) else "PASS"


def main():
    fails = []
    print("== M355 mutation harness (16 mutants + 2 no-op controls) ==")
    for name, env, gate, why in MUTANTS:
        rc, out = run(env)
        st = gate_state(out, gate)
        killed = (st == "FAIL") and rc != 0
        for sub in re.findall(r"^\[FAIL\] (\w+)", out, re.M):
            break
        reds = ",".join(sorted({g for g in re.findall(r"^\[FAIL\] (\w+)", out, re.M)}))
        print("%-5s %-46s gate=%-3s rc=%d  state=%-4s reds=%-14s %s"
              % (name, env.get("M355_PATCH") or ("ALGO " + env.get("M355_ALGO", "")),
                 gate, rc, st, reds, "KILLED" if killed else "SURVIVED"))
        if not killed:
            fails.append(name)
    print("\n-- no-op controls (must stay GREEN) --")
    for i, env in enumerate(NO_OP, 1):
        rc, out = run(env)
        ok = rc == 0 and "PASS M355: 7/7 gates" in out
        print("NO-OP%d rc=%d %s %s" % (i, rc, "GREEN" if ok else "RED",
                                       re.search(r"M355: .*", out).group(0) if re.search(r"M355: .*", out) else ""))
        if not ok:
            fails.append("NO-OP%d" % i)
    print("\n%s M355 harness: %d/%d mutants killed, %d no-op green"
          % ("PASS" if not fails else "FAIL", len(MUTANTS) - len([f for f in fails if f.startswith("MU")]),
             len(MUTANTS), len(NO_OP) - len([f for f in fails if f.startswith("NO")])))
    if fails:
        print("survivors/red no-ops: %s" % fails)
    return 0 if not fails else 1


sys.exit(main())
