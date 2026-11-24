#!/usr/bin/env python3
"""M352 mutation harness — every VERIFIED row of NAMED ## M352 names its mutant.

Two lever types, both exercised:
  * M352_PATCH='<addr>|<new instruction text>' rewrites ONE .text-cache line
    (a real code mutant: an indirect call, the IAT slot, a key, the stamp, the
    array bound, an instruction that becomes a store);
  * M352_ALGO=n mutates the SCANNER/CLASSIFIER law itself (mandatory for a
    tracer/classifier — this instrument has three):
      1 = the key slot for the 4-arg API is off by one (the app-name arg taken)
      2 = helper call sites are not attributed (the image's read census shrinks)
      3 = the byte-level 4-byte VA scan is disabled (the moffs text scan alone)
      4 = the 3-arg helper key slot is off by one (value/default taken as key)
      5 = every `call REG` counts as an indirect call (the call census is blind)

Each mutant must turn the named gate RED. A mutant that leaves the run green is a
harness failure, not a pass.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts/m352_persist_writeback.py")

# (name, env, gate that must redden, what it breaks)
MUTANTS = [
    ("MU1", {"M352_PATCH": "0x58f11b|call   eax"}, "G1",
     "one of the 8 `call edi` becomes `call eax` (targets no longer 1)"),
    ("MU2", {"M352_PATCH": "0x58f106|mov    edi,DWORD PTR ds:0x671100"}, "G2",
     "the persist's edi load re-pointed at GetPrivateProfileStringA"),
    ("MU3", {"M352_PATCH": "0x58f115|push   0x692828"}, "G3",
     "the stamp key swapped to Preferences (a duplicate key)"),
    ("MU4", {"M352_ALGO": "1"}, "G3",
     "ALGO 1: 4-arg key slot off by one -> app-name arg read as the key"),
    ("MU5", {"M352_PATCH": "0x58f306|push   0x692854"}, "G3",
     "a helper key push duplicated (Semaphore -> Announce)"),
    ("MU6", {"M352_PATCH": "0x58f0df|push   0xc"}, "G3",
     "the version stamp itoa'd from 0xc instead of 0xb"),
    ("MU7", {"M352_PATCH": "0x58f388|cmp    esi,0x92bf30"}, "G3",
     "the Custom World re-read bound stops one dword short"),
    ("MU8", {"M352_ALGO": "2"}, "G4",
     "ALGO 2: helper call sites unattributed -> the read census shrinks"),
    ("MU9", {"M352_PATCH": "0x58e9f3|push   0x692780"}, "G4",
     "the loader's first Laptop read re-pointed at Semaphore"),
    ("MU10", {"M352_PATCH": "0x58f3c0|mov    ds:0x6926ec,eax"}, "G6",
     "an epilogue pop becomes a STORE to ds:0x6926ec (the retraction dies)"),
    ("MU11", {"M352_ALGO": "3"}, "G6",
     "ALGO 3: the PE byte scan is blinded -> the 7 push sites go unseen"),
    ("MU12", {"M352_ALGO": "4"}, "G4",
     "ALGO 4: 3-arg helper key slot off by one -> defaults read as keys"),
    ("MU13", {"M352_ALGO": "5"}, "G1",
     "ALGO 5: every `call REG` counted as indirect -> the call census is blind"),
]

NO_OP = [{}, {"M352_ALGO": ""}]


def run(env):
    e = dict(os.environ)
    for k in ("M352_PATCH", "M352_ALGO"):
        e.pop(k, None)
    e.update({k: v for k, v in env.items() if v != ""})
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True, env=e)
    return p.returncode, p.stdout + p.stderr


def fails(out):
    return [l.strip() for l in out.splitlines() if "[FAIL]" in l]


def main():
    print("M352 mutation harness — %d mutants, %d no-ops" % (len(MUTANTS), len(NO_OP)))
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
        ok = rc == 0 and "RESULT: PASS M352: 7/7 gates" in out
        print("  NOOP%d %-4s baseline green | %s" % (n, "OK" if ok else "MISS", env))
        if not ok:
            bad += 1
    print()
    print("MUTANTS: %d/%d killed, no-op %s" % (len(MUTANTS) - bad if bad <= len(MUTANTS) else 0,
                                               len(MUTANTS), "green" if bad == 0 else "RED"))
    print("RESULT: %s" % ("PASS M352: harness %d/%d" % (len(MUTANTS), len(MUTANTS))
                          if bad == 0 else "FAIL"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
