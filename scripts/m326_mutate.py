#!/usr/bin/env python3
# M326 mutation harness: every VERIFIED claim row names the mutant that reddens it.
# 16 code mutants rewrite the DISASSEMBLY via M326_PATCH (settle sub/clamp/zero,
# fold shl, add-leg shape/gate/pay-store, HURRY reader sub, cheat-cap jle, reset
# xor, byte-chain offset, turnfn planted block store, planted SIBLING-offset
# store through a 220-seed); 6 algorithm mutants via M326_ALGO (1 prov off,
# 2 disp widened, 3 seed-scan off, 4 shl-blind, 6 old pop pairing, 7 subreg-blind
# = the OLD resolver this round fixed); 2 save-data mutants (blk0+224 byte flip;
# a REAL second save m112poke.SAV); 2 PE-data mutants (HURRY first byte;
# unrelated .data byte NO-OP). A crash is NOT a red gate (m319 MU6 law): output
# without the 9-denominator summary scores CRASH and fails the harness. DIGEST
# (M324 review law): hashes each mutant's MEASURED payload - the patch/data
# literal AND the acceptance digest of that mutant's run. Sets were MEASURED by
# a sweep (M326_MUT_MEASURE=1) then declared. Sweep corrections: MU13's widened
# census also reddens G6 (reader-count pin) and G9 (writer-owner set intersects
# LOAN owners); MU23's planted [esi+4] store is INVISIBLE to the disp census
# (disp=4 matches no field form) - only the sibling seed scan catches it (G3
# alone), which is exactly the gap it exists to close.
# --selftest: 3 patch-mechanism rejection checks + 1 live PE-patch mechanism run.
import os, re, sys, shutil, subprocess, hashlib, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "m326_block224_census.py")
SAVE = os.path.join(REPO, "programs/saves/m54b_clean.SAV")
SAVE2 = os.path.join(REPO, "programs/saves/m112poke.SAV")
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9"]
TMPBASE = os.environ.get("TMPDIR") or os.path.join(REPO, "evidence")
MEASURE = os.environ.get("M326_MUT_MEASURE") == "1"
TMPDIRS = []

# (id, kind, payload, declared gate set) - sets MEASURED by the sweep, declared here
MUTANTS = [
    ("MU1",  "code", "0x520b1a|add edx,ecx", {"G4", "G6", "G9"}),
    ("MU2",  "code", "0x520b2e|jl 0x520b36", {"G4"}),
    ("MU3",  "code", "0x520b22|mov DWORD PTR [eax+0x94d654],edi", {"G4"}),
    ("MU4",  "code", "0x41a543|sub DWORD PTR [esi+0x94d654],edi", {"G5"}),
    ("MU5",  "code", "0x41a537|jne 0x41a54b", {"G5", "G9"}),
    ("MU6",  "pe", "0x689990|58", {"G5"}),
    ("MU7",  "code", "0x4169b2|add edx,ecx", {"G6"}),
    ("MU8",  "code", "0x59f0bf|mov eax,0x1", {"G7"}),
    ("MU9",  "code", "0x51f53c|mov DWORD PTR [eax+0x94d654],eax", {"G1", "G2", "G7", "G9"}),
    ("MU10", "savedata", ("blk0+224", 0x32c + 0x224, 11), {"G8"}),
    ("MU11", "savefile", SAVE2, {"G8"}),
    ("MU12", "algo", "1", {"G2"}),
    ("MU13", "algo", "2", {"G1", "G2", "G6", "G9"}),
    ("MU14", "algo", "3", {"G3"}),
    ("MU15", "algo", "4", {"G2", "G4"}),
    ("MU16", "algo", "6", set()),
    ("MU17", "algo", "7", {"G2"}),
    ("MU18", "code", "0x41a4f2|jg 0x41a4f9", {"G6"}),
    ("MU19", "code", "0x520b0b|shl eax,0x3", {"G2", "G4"}),
    ("MU20", "code", "0x419d91|mov al,BYTE PTR [edx+0x5]", {"G2"}),
    ("MU21", "pe", "0x999fa8|00", set()),  # declared NO-OP: unrelated .data byte
    ("MU22", "code", "0x41a55d|mov DWORD PTR [esi+0x94d650],edx", {"G5"}),
    ("MU23", "code", "0x4e0336|mov DWORD PTR [esi+0x4],eax", {"G3"}),
]

def run(env_extra):
    env = dict(os.environ)
    for k in ("M326_PATCH", "M326_ALGO", "M326_SAVE", "M326_PE_PATCH",
              "M325_PATCH", "M325_ALGO", "M325_SAVE", "M325_PE_PATCH"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], capture_output=True, text=True,
                       env=env, cwd=REPO, timeout=600)
    out = p.stdout + p.stderr
    gates = {}
    for g in GATES:
        m = re.search(r"^%s (PASS|FAIL)" % g, out, re.M)
        gates[g] = m.group(1) if m else None
    m = re.search(r"^== M326: (\d)/(\d) ==", out, re.M)
    summ = (int(m.group(1)), int(m.group(2))) if m else None
    m = re.search(r"^DIGEST ([0-9a-f]{16})", out, re.M)
    dig = m.group(1) if m else None
    return gates, summ, dig, out, p.returncode

def env_for(kind, payload):
    if kind == "code":
        return {"M326_PATCH": payload}
    if kind == "algo":
        return {"M326_ALGO": payload}
    if kind == "pe":
        return {"M326_PE_PATCH": payload}
    if kind == "savefile":
        return {"M326_SAVE": payload}
    if kind == "savedata":
        label, off, val = payload
        tmp = tempfile.mkdtemp(prefix="m326mut_", dir=TMPBASE)
        TMPDIRS.append(tmp)
        path = os.path.join(tmp, "mut.SAV")
        data = bytearray(open(SAVE, "rb").read())
        data[off] = val
        open(path, "wb").write(bytes(data))
        return {"M326_SAVE": path}
    raise SystemExit("bad kind %s" % kind)

def main():
    if "--selftest" in sys.argv:
        return selftest()
    print("== M326 mutation harness ==")
    try:
        g0, s0, d0, _, rc0 = run({})
        print("BASELINE %s digest=%s rc=%d" % (s0, d0, rc0))
        if s0 != (9, 9):
            print("BASELINE NOT 9/9 - harness aborts (fix the instrument first)")
            return 1
        rows, bad = [], 0
        d = hashlib.sha256()
        d.update(repr(("baseline", s0, d0)).encode())
        for mid, kind, payload, declared in MUTANTS:
            env = env_for(kind, payload)
            gates, summ, dig, out, rc = run(env)
            if summ is None or summ[1] != 9:
                red = "CRASH"
                ok = False
            else:
                redset = set(g for g in GATES if gates[g] == "FAIL")
                red = ",".join(sorted(redset)) if redset else "NO-OP"
                ok = (redset == declared)
            rows.append((mid, kind, red, ok))
            d.update(repr((mid, kind, payload, red, dig)).encode())
            print("  %-5s %-8s red=%-20s declared=%-20s %s digest=%s" % (
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
        print("== M326 mutate: %d/%d ==" % (passed, len(rows)))
        return 0 if bad == 0 else 1
    finally:
        for t in TMPDIRS:
            shutil.rmtree(t, ignore_errors=True)

def selftest():
    print("== M326 mutate selftest ==")
    checks = []
    # S1: address outside .text cache rejected
    _, _, _, out, rc = run({"M326_PATCH": "0xdeadbeef|nop"})
    checks.append(("S1 bad-addr rejected", rc != 0 and "not in .text cache" in out))
    # S2: no-op patch (already equal) rejected
    _, _, _, out, rc = run({"M326_PATCH": "0x520b1a|sub edx,ecx"})
    checks.append(("S2 equal-patch rejected", rc != 0 and "already equal" in out))
    # S3: empty patch rejected
    _, _, _, out, rc = run({"M326_PATCH": " ; "})
    checks.append(("S3 empty-patch rejected", rc != 0 and "applied to nothing" in out))
    # S4: live PE-patch mechanism: HURRY -> XURRY reddens G5 ONLY, and the output
    # must show the mutated string WITH the intact addleg/phase pins (the failure
    # is caused by the string mutation, not collateral damage)
    gates, summ, dig, out, rc = run({"M326_PE_PATCH": "0x689990|58"})
    checks.append(("S4 pe-patch live", summ == (8, 9) and gates["G5"] == "FAIL"
                   and "b'XURRY'" in out and "addleg=True phase=True" in out
                   and all(gates[g] == "PASS" for g in GATES if g != "G5")))
    for name, ok in checks:
        print("  %s %s" % ("PASS" if ok else "FAIL", name))
    print("== selftest: %d/%d ==" % (sum(ok for _, ok in checks), len(checks)))
    return 0 if all(ok for _, ok in checks) else 1

if __name__ == "__main__":
    sys.exit(main())