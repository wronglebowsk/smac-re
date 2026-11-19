#!/usr/bin/env python3
# M325 mutation harness: every VERIFIED claim row names the mutant that reddens it.
# 17 code mutants rewrite the DISASSEMBLY via M325_PATCH (turnfn ROUND/YEAR sites +
# a planted block store, writer disp, editor lea/store/push, clamp caps, -1000 imm,
# reset-0 source, feed cmp/jle, cheat chain, pump caller, reader disp); 5 algorithm
# mutants via M325_ALGO (1 provenance off, 2 disp-match widened, 3 forward-scan off,
# 4 shl-blind affine, 5 feed-direction flipped); 1 save-data mutant via M325_SAVE
# (block0+0x220 value 10->11 in a temp copy); 1 PE-data mutant via M325_PE_PATCH
# (EDITORENERGY first byte); 1 declared NO-OP (unrelated .data byte). A crash is NOT
# a red gate (m319 MU6 law): output without the 8-denominator summary scores CRASH
# and fails the harness. DIGEST (M324 review #326 law): hashes each mutant's MEASURED
# payload - the patch/data literal AND the acceptance digest of that mutant's run.
# Sets were MEASURED by a sweep (M325_MUT_MEASURE=1) then declared below.
# --selftest: 3 patch-mechanism rejection checks + 1 live PE-patch mechanism run.
import os, re, sys, shutil, struct, subprocess, hashlib, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "m325_block220_census.py")
SAVE = os.path.join(REPO, "programs/saves/m54b_clean.SAV")
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]
TMPBASE = os.environ.get("TMPDIR", os.path.join(REPO, "scratch"))
MEASURE = os.environ.get("M325_MUT_MEASURE") == "1"

# (id, kind, payload, declared gate set) - sets MEASURED by the sweep, declared here
MUTANTS = [
    ("MU1",  "code", "0x51f53c|mov ds:0x985b00,eax", {"G4"}),
    ("MU2",  "code", "0x41a55d|mov DWORD PTR [esi+0x94d654],ecx", {"G1", "G2", "G3"}),
    ("MU3",  "code", "0x4e0311|lea esi,[ecx*4+0x94d654]", {"G3"}),
    ("MU4",  "code", "0x4e0336|mov DWORD PTR [esi+0x4],eax", {"G3"}),
    ("MU5",  "code", "0x4e0319|push 0x68c948", {"G5"}),
    ("MU6",  "code", "0x5087ae|cmp eax,0x989680", {"G5"}),
    ("MU7",  "code", "0x5085c0|add DWORD PTR [eax+0x94d650],0xfffffc19", {"G5"}),
    ("MU8",  "code", "0x59ee73|xor ecx,ecx", {"G5"}),
    ("MU9",  "code", "0x44262b|jg 0x442648", {"G6"}),
    ("MU10", "code", "0x442625|cmp edx,DWORD PTR [ecx+0x94d654]", {"G1", "G6"}),
    ("MU11", "code", "0x626fd7|mov ds:0x999fa8,eax", {"G6"}),
    ("MU12", "code", "0x626fca|push 0x99a020", {"G6"}),
    ("MU13", "code", "0x514ebf|call 0x4e0350", {"G6"}),
    ("MU14", "algo", "1", {"G2", "G3"}),
    ("MU15", "algo", "2", {"G1", "G2", "G3"}),
    ("MU16", "algo", "3", {"G3"}),
    ("MU17", "algo", "4", {"G2", "G3"}),
    ("MU18", "algo", "5", {"G6", "G8"}),
    ("MU19", "savedata", ("blk0+220", 0x32c + 0x220, 11), {"G7"}),
    ("MU20", "code", "0x51f324|mov DWORD PTR [ebx+0x94d650],eax", {"G1", "G2", "G3", "G4", "G8"}),
    ("MU21", "code", "0x51f54f|mov ds:0x985afc,eax", {"G4"}),
    ("MU22", "code", "0x44263c|mov edx,DWORD PTR [ecx+0x94d654]", {"G1"}),
    ("MU23", "pe", "0x68c938|58", {"G5"}),
    ("MU24", "pe", "0x999fa8|00", set()),  # declared NO-OP: unrelated .data byte
]

def run(env_extra):
    env = dict(os.environ)
    env.pop("M325_PATCH", None); env.pop("M325_ALGO", None)
    env.pop("M325_SAVE", None); env.pop("M325_PE_PATCH", None)
    env.pop("M325_TRACE", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True,
                       env=env, cwd=REPO, timeout=600)
    out = p.stdout + p.stderr  # SystemExit rejection messages land on stderr
    gates = {}
    for g in GATES:
        m = re.search(r"^%s (PASS|FAIL)" % g, out, re.M)
        gates[g] = m.group(1) if m else None
    m = re.search(r"^== M325: (\d)/(\d) ==", out, re.M)
    summ = (int(m.group(1)), int(m.group(2))) if m else None
    m = re.search(r"^DIGEST ([0-9a-f]{16})", out, re.M)
    dig = m.group(1) if m else None
    return gates, summ, dig, out, p.returncode

def env_for(kind, payload):
    if kind == "code":
        return {"M325_PATCH": payload}
    if kind == "algo":
        return {"M325_ALGO": payload}
    if kind == "pe":
        return {"M325_PE_PATCH": payload}
    if kind == "savedata":
        label, off, val = payload
        tmp = tempfile.mkdtemp(prefix="m325mut_", dir=TMPBASE)
        path = os.path.join(tmp, "mut.SAV")
        data = bytearray(open(SAVE, "rb").read())
        data[off] = val
        open(path, "wb").write(bytes(data))
        return {"M325_SAVE": path}
    raise SystemExit("bad kind %s" % kind)

def main():
    if "--selftest" in sys.argv:
        return selftest()
    print("== M325 mutation harness ==")
    g0, s0, d0, _, rc0 = run({})
    print("BASELINE %s digest=%s rc=%d" % (s0, d0, rc0))
    if s0 != (8, 8):
        print("BASELINE NOT 8/8 - harness aborts (fix the instrument first)")
        return 1
    rows, bad = [], 0
    d = hashlib.sha256()
    d.update(repr(("baseline", s0, d0)).encode())
    for mid, kind, payload, declared in MUTANTS:
        env = env_for(kind, payload)
        gates, summ, dig, out, rc = run(env)
        if summ is None or summ[1] != 8:
            red = "CRASH"
            ok = False
        else:
            redset = set(g for g in GATES if gates[g] == "FAIL")
            red = ",".join(sorted(redset)) if redset else "NO-OP"
            ok = (redset == declared)
        rows.append((mid, kind, red, ok))
        d.update(repr((mid, kind, payload, red, dig)).encode())
        print("  %-5s %-8s red=%-16s declared=%-16s %s digest=%s" % (
            mid, kind, red, ",".join(sorted(declared)) or "NO-OP",
            "OK" if ok else "MISMATCH", dig))
        if not ok: bad += 1
        if MEASURE:
            print("    MEASURED %s: %s" % (mid, sorted(
                g for g in GATES if gates[g] == "FAIL") if summ else "CRASH"))
    noop = sum(1 for _, _, red, _ in rows if red == "NO-OP")
    scored = len(rows) - noop
    passed = sum(1 for _, _, _, ok in rows if ok)
    print("HARNESS %d/%d scored OK, %d NO-OP, %d MISMATCH/CRASH" % (
        passed - noop, scored, noop, bad))
    print("DIGEST %s" % d.hexdigest()[:16])
    print("== M325 mutate: %d/%d ==" % (passed, len(rows)))
    return 0 if bad == 0 else 1

def selftest():
    print("== M325 mutate selftest ==")
    checks = []
    # S1: address outside .text cache rejected
    _, _, _, out, rc = run({"M325_PATCH": "0xdeadbeef|nop"})
    checks.append(("S1 bad-addr rejected", rc != 0 and "not in .text cache" in out))
    # S2: no-op patch (already equal) rejected
    _, _, _, out, rc = run({"M325_PATCH": "0x51f53c|mov ds:0x985afc,eax"})
    checks.append(("S2 equal-patch rejected", rc != 0 and "already equal" in out))
    # S3: empty patch rejected
    _, _, _, out, rc = run({"M325_PATCH": " ; "})
    checks.append(("S3 empty-patch rejected", rc != 0 and "applied to nothing" in out))
    # S4: live PE-patch mechanism: EDITORENERGY -> XDITORENERGY reddens G5 only
    gates, summ, dig, out, rc = run({"M325_PE_PATCH": "0x68c938|58"})
    checks.append(("S4 pe-patch live", summ == (7, 8) and gates["G5"] == "FAIL"
                   and b"XDITORENERGY" in out.encode()))
    for name, ok in checks:
        print("  %s %s" % ("PASS" if ok else "FAIL", name))
    print("== selftest: %d/%d ==" % (sum(ok for _, ok in checks), len(checks)))
    return 0 if all(ok for _, ok in checks) else 1

if __name__ == "__main__":
    sys.exit(main())