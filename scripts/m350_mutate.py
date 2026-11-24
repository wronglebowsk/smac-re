#!/usr/bin/env python3
"""M350 mutation harness — every VERIFIED row of NAMED ## M350 names its mutant.

Two lever types, both exercised:
  * M350_PATCH='<addr>|<new instruction text>' rewrites ONE .text-cache line
    (a real code mutant: an address, a key, a loop bound, a call, a stored global);
  * M350_ALGO=n mutates the SCANNER/CLASSIFIER law itself (mandatory for a
    tracer/classifier — this instrument is one):
      1 = the pointer store `mov [esi],eax` is not a store (extent law off)
      2 = the sub-register alias table is dropped (self-RMW classifier off)
      3 = the commit walker ignores control flow, window 8 -> 400 insns (commit classifier off)
      4 = the profile-read probe answers True everywhere (R2's probe blinded)

Each mutant must turn the named gate RED. A mutant that leaves the run green is a
harness failure, not a pass.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m350_pref_cowriters.py")

# (name, env, gate that must redden, what it breaks)
MUTANTS = [
    ("MU1", {"M350_PATCH": "0x58e8a1|push   0x692724"}, "G1",
     "Difficulty's key push swapped to the Map Type string"),
    ("MU2", {"M350_PATCH": "0x58e922|mov    ds:0x92bdf8,eax"}, "G1",
     "the Map Type store redirected into Top Menu (cell set no longer 11)"),
    ("MU3", {"M350_PATCH": "0x58efd9|cmp    esi,0x92bf18"}, "G2",
     "the Custom World loop bound collapsed to 0 iterations"),
    ("MU4", {"M350_PATCH": "0x58efd6|add    esi,0x0"}, "G2",
     "the Custom World pointer never advances (7 stores -> 1)"),
    ("MU5", {"M350_ALGO": "1"}, "G2",
     "ALGO 1: the pointer store is not counted as a store"),
    ("MU6", {"M350_ALGO": "2"}, "G4",
     "ALGO 2: the alias table is dropped -> the self-RMW sites read EXTERNAL"),
    ("MU7", {"M350_ALGO": "3"}, "G4",
     "ALGO 3: no ret/jmp stop + 400-insn window -> TAIL-NONE becomes COMMIT"),
    ("MU8", {"M350_PATCH": "0x57c5a9|mov    esi,DWORD PTR ds:0x92bde8"}, "G3",
     "a Faction co-ref re-pointed at Difficulty (per-cell census wrong)"),
    ("MU9", {"M350_PATCH": "0x5109ad|nop"}, "G4",
     "the PERSIST call after the Laptop commit deleted"),
    ("MU10", {"M350_PATCH": "0x58f3e1|mov    ds:0x985ab4,eax"}, "G5",
     "the publisher's first target global moved off 0x985ab8"),
    ("MU11", {"M350_PATCH": "0x57e6cc|mov    ds:0x92bf1c,eax"}, "G3",
     "the Custom World[0] co-writer moved to slot 1"),
    ("MU12", {"M350_PATCH": "0x57ab57|cmp    esi,0x92bdf8"}, "G3",
     "a 0x92bde8 sentinel comparison re-pointed (materialised-address census wrong)"),
    ("MU13", {"M350_BYTEPATCH": "0x58f11f|e9bd9200"}, "G3",
     "one PE displacement byte changed: image and objdump now disagree (equivalence off)"),
    ("MU14", {"M350_ALGO": "4"}, "G6",
     "ALGO 4: the profile-read probe answers True for every site -> R2 decorative"),
    ("MU15", {"M350_ALGO": "5"}, "G6",
     "ALGO 5: calls made transparent -> the loader's parse-return stores count as locally defined"),
]

NO_OP = [{}, {"M350_ALGO": ""}]


def run(env):
    e = dict(os.environ)
    for k in ("M350_PATCH", "M350_ALGO", "M350_BYTEPATCH"):
        e.pop(k, None)
    e.update({k: v for k, v in env.items() if v != ""})
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def fails(out):
    return [l.strip() for l in out.splitlines() if "[FAIL]" in l]


def main():
    print("M350 mutation harness — %d mutants, %d no-ops" % (len(MUTANTS), len(NO_OP)))
    bad = 0
    for name, env, gate, why in MUTANTS:
        rc, out = run(env)
        fl = fails(out)
        hit = [l for l in fl if ("%s " % gate) in l or l.startswith("[FAIL] %s " % gate)]
        ok = rc != 0 and bool(hit)
        print("  %-5s %-4s %s | %s" % (name, "KILL" if ok else "MISS", gate, why))
        if not ok:
            bad += 1
            print("        rc=%s fails=%s" % (rc, fl[:3]))
        else:
            print("        %s" % hit[0])
    for n, env in enumerate(NO_OP):
        rc, out = run(env)
        ok = rc == 0 and "RESULT: PASS M350: 6/6 gates" in out
        print("  NOOP%d %-4s baseline green | %s" % (n, "OK" if ok else "MISS", env))
        if not ok:
            bad += 1
    print()
    print("MUTANTS: %d/%d killed, no-op %s" % (len(MUTANTS) - bad if bad <= len(MUTANTS) else 0,
                                               len(MUTANTS), "green" if bad == 0 else "RED"))
    print("RESULT: %s" % ("PASS M350: harness %d/%d" % (len(MUTANTS), len(MUTANTS))
                          if bad == 0 else "FAIL"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
