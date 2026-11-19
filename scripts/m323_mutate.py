#!/usr/bin/env python3
# M323 mutation harness: every VERIFIED claim row names the mutant that reddens it.
# 12 expectation (data) mutants rewrite MEASURED literals in a temp copy of the
# instrument; 9 code mutants rewrite the DISASSEMBLY via M323_PATCH; 2 algorithm
# mutants via M323_ALGO (1: direct-test-only gate tracer, 2: W/R classifier swap);
# 2 evidence-data mutants rewrite the PRIOR evidence under M323_EVIDENCE_ROOT;
# 1 declared NO-OP. A crash is NOT a red gate (m319 MU6 law): output without the
# summary line scores CRASH and fails the harness. --selftest: 3 synthetic scorer
# checks + 1 live NO-OP run.
import os, re, sys, shutil, subprocess, hashlib, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "m323_round_census.py")
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "R1", "R2", "R3"]
EVFILES = ["evidence/m302_livepins.txt", "evidence/m175_m177_full.txt",
           "evidence/m320_sibling_census.txt", "evidence/m305_identity.txt"]

# (id, kind, payload, declared gate set)
MUTANTS = [
    ("MU1",  "data", ("P_TOTAL = 336", "P_TOTAL = 337"), {"G1"}),
    ("MU2",  "data", ('(0x51f53c, "W", "round+1")', '(0x51f53c, "W", "round+2")'), {"G2"}),
    ("MU3",  "data", ("0x520ca3", "0x520ca4"), {"G3"}),
    ("MU4",  "data", ("0x45dd66: 50", "0x45dd66: 51"), {"G4"}),
    ("MU5",  "data", ('P_BL = "const(0x1)"', 'P_BL = "const(0x2)"'), {"G5"}),
    ("MU6",  "data", ("0x51da30: (0x51da25, 0x51db40)", "0x51da30: (0x51da26, 0x51db40)"), {"G6"}),
    ("MU7",  "data", ('"round": 50', '"round": 51'), {"G7"}),
    ("MU8",  "data", ("0x533eec: 0x533ecc", "0x533eec: 0x533ecd"), {"G8"}),
    ("MU9",  "data", ("[0x5552d9, 0x555da0]", "[0x5552d9, 0x555da1]"), {"G9"}),
    ("MU10", "data", ('("add", "eax,ecx")', '("sub", "eax,ecx")'), {"G10", "R1"}),
    ("MU11", "data", ("P_NREG = 111", "P_NREG = 112"), {"G5"}),
    ("MU12", "data", ('P_R3 = ("FUN_0051f320", 2)', 'P_R3 = ("FUN_0051f320", 3)'), {"R3"}),
    ("MU13", "code", "0x51f53a|dec eax", {"G2", "G10", "R1", "R2", "R3"}),
    ("MU14", "code", "0x59f19c|mov edx,0x1", {"G5"}),
    ("MU15", "code", "0x55840d|cmp DWORD PTR ds:0x985afc,0x4c", {"G4", "G5"}),
    ("MU16", "code", "0x533eec|mov DWORD PTR [edx*4+0x94d4a9],eax", {"G8", "R2"}),
    ("MU17", "code", "0x5b2c0c|sub eax,ecx", {"G10", "R1"}),
    ("MU18", "code", "0x5a108b|mov DWORD PTR ds:0x985af0,esi", {"G1", "G2", "G3", "R2"}),
    ("MU19", "code", "0x5552d9|test BYTE PTR ds:0x985b00,0x1", {"G1", "G4", "G9", "G10", "R1", "R3"}),
    ("MU20", "code", "0x59ce42|mov DWORD PTR [ebp-0x48],0x51", {"G2", "G10"}),
    ("MU21", "code", "0x51f32b|mov ebx,0x2", {"G5"}),
    ("MU22", "algo", "1", {"G5"}),
    ("MU23", "algo", "2", {"G1", "G2", "G3", "G5", "R2", "R3"}),
    ("MU24", "evdata", ("evidence/m302_livepins.txt", "round 50", "round 51"), {"G7"}),
    ("MU25", "evdata", ("evidence/m175_m177_full.txt", "0x533eec", "0x533eed"), {"G8"}),
    ("MU26", "noop", "0x40100c|mov DWORD PTR [ebp-0x8],0x1", set()),
    # review #323 fixes: max-flow (P1-2), bl def-set/pair (P1-3/P2-6), year arg chain
    # (P2-7), word width (P2-4)
    ("MU27", "code", "0x4e038c|jmp 0x4e0398", {"G2"}),
    ("MU28", "code", "0x4e0384|cmp eax,0x2", {"G2"}),
    ("MU29", "code", "0x51f525|push ecx", {"G5"}),
    ("MU30", "code", "0x51f535|mov eax,0x0", {"G1", "G2", "G10", "R1", "R2", "R3"}),
    ("MU31", "code", "0x59c18a|mov eax,ds:0x985afc", {"G1", "G9"}),
]

def run_script(path, env_extra):
    env = dict(os.environ)
    for k in ("M323_PATCH", "M323_ALGO", "M323_EVIDENCE_ROOT"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", path], cwd=REPO, env=env,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr

def score(out):
    """returns (observed_red_set, crashed_bool); denominator must be the shipped 13"""
    m = re.search(r"^== M323: (\d+)/(\d+) ==$", out, re.M)
    if not m or m.group(2) != "13":
        return set(), True
    red = set(re.findall(r"^BADGATE (\S+)", out, re.M))
    return red, False

def verdict(declared, observed, crashed):
    if crashed: return "CRASH"
    if observed == declared: return "OK" if declared else "NO-OP"
    return "MISMATCH"

def selftest():
    res = []
    ok1 = verdict({"G4"}, {"G4"}, False) == "OK"
    ok2 = verdict({"G4"}, {"G5"}, False) == "MISMATCH"
    ok3 = verdict({"G4"}, set(), True) == "CRASH"
    res += [("S1 scorer match", ok1), ("S2 scorer mismatch", ok2), ("S3 scorer crash", ok3)]
    rc, out = run_script(SCRIPT, {"M323_PATCH": "40100c|mov DWORD PTR [ebp-0x8],0x1"})
    obs, crashed = score(out)
    res.append(("S4 live NO-OP", (not crashed) and obs == set() and rc == 0
                and "== M323: 13/13 ==" in out))
    for nm, ok in res:
        print(("OK  " if ok else "FAIL") + " " + nm)
    n = sum(1 for _, ok in res if ok)
    print("selftest %d/%d" % (n, len(res)))
    return n == len(res)

def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    src = open(SCRIPT).read()
    rows = []
    tmp = os.path.join(REPO, "scripts", "_m323_mut_%d.py" % os.getpid())
    evtmp = tempfile.mkdtemp(prefix="m323_ev_", dir=os.path.join(REPO, "scratch"))
    try:
        for (mid, kind, payload, declared) in MUTANTS:
            if kind == "data":
                old, new = payload
                if src.count(old) != 1:
                    raise SystemExit("%s: literal not unique (%d): %r" % (mid, src.count(old), old))
                open(tmp, "w").write(src.replace(old, new))
                rc, out = run_script(tmp, {})
            elif kind == "code":
                rc, out = run_script(SCRIPT, {"M323_PATCH": payload})
            elif kind == "algo":
                rc, out = run_script(SCRIPT, {"M323_ALGO": payload})
            elif kind == "evdata":
                rel, old, new = payload
                for f in EVFILES:
                    dst = os.path.join(evtmp, f)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy(os.path.join(REPO, f), dst)
                tgt = os.path.join(evtmp, rel)
                txt = open(tgt, encoding="utf-8").read()
                if old not in txt:
                    raise SystemExit("%s: evidence literal absent: %r" % (mid, old))
                open(tgt, "w", encoding="utf-8").write(txt.replace(old, new))
                rc, out = run_script(SCRIPT, {"M323_EVIDENCE_ROOT": evtmp})
            else:
                rc, out = run_script(SCRIPT, {"M323_PATCH": payload})
            obs, crashed = score(out)
            v = verdict(declared, obs, crashed)
            rows.append((mid, kind, declared, obs, v))
            print("%-6s %-6s declared=%-24s observed=%-24s %s" %
                  (mid, kind, sorted(declared), sorted(obs), v))
    finally:
        if os.path.exists(tmp): os.remove(tmp)
        shutil.rmtree(evtmp, ignore_errors=True)
    h = hashlib.sha256()
    for (mid, kind, declared, obs, v) in rows:
        h.update(("%s:%s:%s:%s:%s|" % (mid, kind, sorted(declared), sorted(obs), v)).encode())
    nscore = sum(1 for r in rows if r[4] in ("OK", "NO-OP"))
    nnoop = sum(1 for r in rows if r[4] == "NO-OP")
    print("digest %s" % h.hexdigest()[:16])
    print("== M323 MUTATE: %d/%d scored + %d NO-OP ==" % (nscore, len(rows), nnoop))
    sys.exit(0 if nscore == len(rows) else 1)

if __name__ == "__main__":
    main()
