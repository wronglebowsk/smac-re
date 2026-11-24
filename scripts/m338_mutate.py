#!/usr/bin/env python3
"""M338 mutation harness: every VERIFIED row of `NAMED ## M338` names the mutant
that reddens it, and the declared gate sets are MEASURED.

Each mutant is applied by `scripts/m338_diff_readers.py` itself (env M338_MUT,
byte-faithful: bytes AND disassembly text change together; M338_ALG=ALG1 is the
algorithm mutant). The harness runs the acceptance script once per mutant, parses
the per-gate rows, and requires declared == measured in BOTH directions.

    python3 -u scripts/m338_mutate.py            # score
    python3 -u scripts/m338_mutate.py --selftest # parser/patch checks
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACC = os.path.join(ROOT, "scripts/m338_diff_readers.py")

# mutant -> gates it MUST redden (declared); measured must equal this exactly
DECL = {
    "MU1": {"G2"},          # cmp esi,6 -> 5 (loop bound)
    "MU2": {"G1", "G3"},    # reader's table displacement 0x94d2ac -> 0x94d2b0
    "MU3": {"G3"},          # field +0x20 -> +0x24
    "MU4": {"G4"},          # the record pointer goes to [ebp-0x20]
    "MU5": {"G4"},          # buffer base 0x983a10 -> 0x983a14
    "MU6": {"G5"},          # read size 0x1324 -> 0x1320
    "MU7": {"G5"},          # zero-init stride 0x8c -> 0x90
    "MU8": {"G6"},          # source cell 0x94d438 -> 0x94d43c
    "MU9": {"G6"},          # fold shl 4 -> shl 3 (8380 -> 4190)
    "MU10": {"G7"},         # AI default 3 -> 4
    "MU11": {"G1"},         # INSERTION: a second 0x94d2ac load appears
    "MU12": {"G1"},         # REMOVAL: a declared load leaves the set
    "ALG1": {"G1"},         # ALGORITHM: count base materialisations as readers
}
ROW = re.compile(r"^(G\d)\s+(PASS|FAIL)\b")


def run(mut):
    env = dict(os.environ)
    env.pop("M338_MUT", None)
    env.pop("M338_ALG", None)
    if mut == "ALG1":
        env["M338_ALG"] = "ALG1"
    else:
        env["M338_MUT"] = mut
    p = subprocess.run([sys.executable, "-u", ACC], capture_output=True,
                       text=True, env=env, cwd=ROOT)
    out = p.stdout
    rows = {}
    for line in out.splitlines():
        m = ROW.match(line)
        if m:
            rows[m.group(1)] = m.group(2)
    dig = re.search(r"^digest=(\S+)", out, re.M)
    verdict = "PASS" if "PASS M338:" in out else ("FAIL" if "FAIL M338:" in out else "CRASH")
    return verdict, rows, (dig.group(1) if dig else "-"), p.returncode


def main():
    base_v, base_rows, base_dig, base_rc = run("")
    print("baseline: %s gates=%d digest=%s" % (base_v, len(base_rows), base_dig))
    ok = base_v == "PASS" and base_rc == 0
    scored = crashes = mismatch = 0
    for mut in DECL:
        v, rows, dig, rc = run(mut)
        red = {g for g, s in rows.items() if s == "FAIL"}
        if v == "CRASH" or (not rows and rc not in (0, 1)):
            crashes += 1
            print("%-5s CRASH rc=%s" % (mut, rc))
            ok = False
            continue
        good = (v == "FAIL" and red == DECL[mut])
        scored += good
        if not good:
            mismatch += 1
            print("%-5s MISMATCH verdict=%s declared=%s measured=%s" %
                  (mut, v, sorted(DECL[mut]), sorted(red)))
        else:
            print("%-5s FAIL declared=measured=%s digest=%s" %
                  (mut, sorted(red), dig))
    print("HARNESS %s: %d/%d scored, %d MISMATCH, %d CRASH, digest(rows)=%s" %
          ("PASS" if (ok and mismatch == 0 and crashes == 0 and scored == len(DECL)) else "FAIL",
           scored, len(DECL), mismatch, crashes,
           __import__("hashlib").sha256(
               "|".join("%s:%s" % (m, ",".join(sorted(DECL[m])))
                        for m in sorted(DECL)).encode()).hexdigest()[:16]))
    return 0 if ok else 1


def selftest():
    import importlib.util
    spec = importlib.util.spec_from_file_location("acc", ACC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ins = mod.load()
    t1 = len(ins) > 100000
    print("ST1 instruction stream parsed: %d insns -> %s" % (len(ins), t1))
    t2 = False
    try:
        mod.patch(ins, 0x1234, "90", "90", "nop", "nop")
    except KeyError:
        t2 = True
    print("ST2 a patch at a non-code address raises -> %s" % t2)
    t3 = all(len(mod.site(ins, a)["bs"]) == 7
             for a in (0x44A1C8, 0x484CC9, 0x485426, 0x48678F, 0x486F40,
                       0x57C606, 0x599405))
    print("ST3 all seven declared table loads are 7-byte encodings -> %s" % t3)
    print("SELFTEST %d/3" % sum((t1, t2, t3)))
    return 0 if all((t1, t2, t3)) else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
