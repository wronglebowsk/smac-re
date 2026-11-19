#!/usr/bin/env python3
# M328 mutation harness: every VERIFIED claim row names the mutant that reddens it.
# 24 code/PE mutants rewrite the DISASSEMBLY or the jump-table bytes via
# M328_PATCH / M328_PE_PATCH (A site/width/snapshot-fold/warning-chain/string,
# additions-only store, upkeep call order, B T-site role, planted B seed,
# sole-1 writer source, sole-def xor, lifecycle string push, switch-table case,
# menu call target, session-blob size/dest, 'multi' push, diplomacy branch
# polarity, HURRY gate load, planted bracket-form A access, planted arithmetic
# B writer, planted warning-fn A write); 3 algorithm mutants via M328_ALGO
# (1 immediate-only writer values, 3 cmp-blind classifier, 4 sole-def fallback
# off); 1 declared NO-OP (ALGO2 width-blind: the census is all-dw, forcing
# width=4 is unobservable - MEASURED identical digest). A crash is NOT a red
# gate (m319 MU6 law): output without the 14-denominator summary scores CRASH
# and fails the harness. DIGEST (M324 review law): hashes each mutant's
# MEASURED payload AND the acceptance digest of that mutant's run. Sets were
# MEASURED by a sweep (M328_MUT_MEASURE=1) then declared.
# --selftest: 2 patch-mechanism rejection checks + identity digest + sole-def
# fallback measurement (ALGO4 opaques) + seed-plant measurement (MU10 seeds=1).
import os, re, sys, subprocess, hashlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "m328_hurry_globals_census.py")
GATES = ["G%d" % i for i in range(1, 11)] + ["R1", "R2", "R3", "R4"]
BASE_DIGEST = "79deb5e6c5c501ff"
MEASURE = os.environ.get("M328_MUT_MEASURE") == "1"

# (id, kind, payload, declared gate set) - sets MEASURED by the sweep
MUTANTS = [
    ("MU1",  "code", "0x41a551|mov edx,DWORD PTR ds:0x91c650", {"G1"}),
    ("MU2",  "code", "0x51ff00|mov ecx,BYTE PTR ds:0x91c64c", {"G1"}),
    ("MU3",  "code", "0x52065d|mov ds:0x91c64c,ecx", {"G2"}),
    ("MU4",  "code", "0x520559|shl esi,0x3", {"G2"}),
    ("MU5",  "code", "0x51ff09|shl ecx,0x2", {"G3"}),
    ("MU6",  "code", "0x51ff3b|push 0x68e98d", {"G3"}),
    ("MU7",  "code", "0x520741|sub eax,edx", {"G4"}),
    ("MU8",  "code", "0x52091a|call 0x51fe90", {"G4"}),
    ("MU9",  "code", "0x546887|mov DWORD PTR ds:0x920434,ebx", {"G5", "G6", "R2"}),
    ("MU10", "code", "0x52054c|mov eax,0x920434", {"G2", "G5"}),
    ("MU11", "algo", "4", {"G6"}),
    ("MU12", "code", "0x57ed04|mov DWORD PTR ds:0x920434,esi", {"G6", "R2"}),
    ("MU13", "code", "0x512b63|mov ebx,0x1", {"G6"}),
    ("MU14", "code", "0x516ef4|push 0x692044", {"G7"}),
    ("MU15", "pe",   "0x580080|19fa5700", {"G8"}),
    ("MU16", "code", "0x57fcfa|call 0x57c550", {"G8"}),
    ("MU17", "code", "0x596920|push 0xce4", {"G9", "R3"}),
    ("MU18", "code", "0x5981c1|push 0x692fb9", {"G9"}),
    ("MU19", "code", "0x546c5a|jne 0x546c90", {"G10"}),
    ("MU20", "code", "0x41a530|mov eax,0x1", {"G5", "G10"}),
    ("MU21", "code", "0x41a551|mov edx,DWORD PTR [eax+0x91c64c]", {"G1", "R1"}),
    ("MU22", "code", "0x52280c|add DWORD PTR ds:0x920434,ebx", {"G6", "R2"}),
    ("MU23", "code", "0x596920|push 0x920434", {"G9", "R3"}),
    ("MU24", "code", "0x51ff00|mov DWORD PTR ds:0x91c64c,ecx", {"G1", "R4"}),
    ("MU25", "algo", "1", {"G2", "G6"}),
    ("MU26", "algo", "2", set()),  # declared NO-OP: all-dw census, width-blind unobservable
    ("MU27", "algo", "3", {"G5"}),
]

def run(env_extra):
    env = dict(os.environ)
    env.pop("M328_PATCH", None); env.pop("M328_PE_PATCH", None)
    env.pop("M328_ALGO", None)
    env.update(env_extra)
    r = subprocess.run([sys.executable, "-u", SCRIPT], env=env,
                       capture_output=True, text=True, timeout=600)
    return r.returncode, r.stdout + r.stderr

def redset(out):
    return {g for g in GATES if re.search(r"^%s FAIL" % g, out, re.M)}

def digest_of(out):
    m = re.search(r"^digest ([0-9a-f]{16})$", out, re.M)
    return m.group(1) if m else None

def summary_ok(out):
    return re.search(r"^== M328: \d+/14 ==$", out, re.M) is not None

def env_for(kind, payload):
    if kind == "code": return {"M328_PATCH": payload}
    if kind == "pe": return {"M328_PE_PATCH": payload}
    return {"M328_ALGO": payload}

def main():
    rows, det = [], []
    rc0, out0 = run({})
    d0 = digest_of(out0)
    print("baseline rc=%d digest=%s (committed %s)" % (rc0, d0, BASE_DIGEST))
    for mid, kind, payload, declared in MUTANTS:
        rc, out = run(env_for(kind, payload))
        if not summary_ok(out):
            rows.append((mid, kind, "CRASH", declared)); continue
        red = redset(out)
        md = digest_of(out)
        det.append("%s|%s|%s|%s" % (mid, kind, payload, md))
        rows.append((mid, kind, red, declared))
        if MEASURE:
            print("%-5s %-5s red=%s" % (mid, kind, ",".join(sorted(red)) or "NO-OP"))
    if MEASURE:
        print("== sweep done (measure mode, no assertions) ==")
        return 0
    print("%-5s %-5s %-22s %-22s %s" % ("id", "kind", "measured-red", "declared", "verdict"))
    ok = 0
    for mid, kind, red, declared in rows:
        if red == "CRASH":
            verdict = "CRASH"
        elif red == declared:
            verdict = "OK"; ok += 1
        else:
            verdict = "MISMATCH"
        print("%-5s %-5s %-22s %-22s %s" %
              (mid, kind, ",".join(sorted(red)) if isinstance(red, set) else red,
               ",".join(sorted(declared)) or "NO-OP", verdict))
    scored = sum(1 for _, _, red, _ in rows if red != "NO-OP" and isinstance(red, set))
    noop = sum(1 for _, _, red, _ in rows if red == set())
    bad = len(rows) - ok
    print("HARNESS %d/%d scored OK, %d NO-OP, %d MISMATCH/CRASH" % (ok, len(rows), noop, bad))
    dig = hashlib.sha256(("\n".join(det) + "\nbase|" + str(d0)).encode()).hexdigest()[:16]
    print("digest %s" % dig)
    assert rc0 == 0 and d0 == BASE_DIGEST, "baseline drifted"
    assert bad == 0, "mutant set mismatch"
    print("== M328 mutate: %d/%d ==" % (ok, len(rows)))
    return 0

def selftest():
    print("== M328 mutate selftest ==")
    checks = []
    rc, out = run({"M328_PATCH": "0x520540|push ebp"})
    checks.append(("S1 no-op patch rejected", rc != 0 and "already equal" in out))
    rc, out = run({"M328_PATCH": "0xdeadbeef|nop"})
    checks.append(("S2 unknown address rejected", rc != 0 and "not in .text cache" in out))
    rc, out = run({})
    checks.append(("S3 identity digest", rc == 0 and digest_of(out) == BASE_DIGEST))
    rc, out = run({"M328_ALGO": "4"})
    checks.append(("S4 sole-def fallback measured (ALGO4 opaques the 512b40 pair)",
                   out.count("('opaque', 'ebx')") >= 2))
    rc, out = run({"M328_PATCH": "0x52054c|mov eax,0x920434"})
    checks.append(("S5 seed plant measured (seeds=1 on B)",
                   bool(re.search(r"B 0x920434:.*seeds=1", out))))
    for name, ok in checks:
        print("%s %s" % ("PASS" if ok else "FAIL", name))
    print("== selftest: %d/%d ==" % (sum(ok for _, ok in checks), len(checks)))
    return 0 if all(ok for _, ok in checks) else 1

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())