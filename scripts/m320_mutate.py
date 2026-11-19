#!/usr/bin/env python3
# M320 mutation harness: every VERIFIED claim row names the mutant that reddens it.
# 12 expectation (data) mutants rewrite MEASURED literals in a temp copy of the
# instrument; 11 code mutants rewrite the DISASSEMBLY via M320_PATCH; 2 algorithm
# mutants via M320_ALGO (1: fold evaluator shl->add, 2: W/R classifier swap);
# 1 declared NO-OP. A crash is NOT a red gate (m319 MU6 law): output without the
# summary line scores CRASH and fails the harness. --selftest: 3 synthetic scorer
# checks + 1 live NO-OP run.
import os, re, sys, subprocess, hashlib, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "m320_sibling_census.py")
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "R1", "R2"]

# (id, kind, payload, declared gate set)
MUTANTS = [
    ("MU1",  "data", ("len(hits) == 4111", "len(hits) == 4112"), {"G2"}),
    ("MU2",  "data", ("gz == 65", "gz == 64"), {"G3"}),
    ("MU3",  "data", ('0x59f018: ("cmp", "eax,0x80"),', '0x59f018: ("cmp", "eax,0x81"),'), {"G4"}),
    ("MU4",  "data", ('g5back == (0x51dd03, "jl", "0x51dcbd")', 'g5back == (0x51dd03, "jl", "0x51dcc1")'), {"G5"}),
    ("MU5",  "data", ('fold6 == {"edi": 4190, "eax": 1, "$": 0}', 'fold6 == {"edi": 4191, "eax": 1, "$": 0}'), {"G6"}),
    ("MU6",  "data", ('fold7 == {"ebx": 8380, "site": 2, "$": 0}', 'fold7 == {"ebx": 8380, "site": 3, "$": 0}'), {"G7"}),
    ("MU7",  "data", ("len(rw) == 114", "len(rw) == 113"), {"G8"}),
    ("MU8",  "data", ("len(imm_loads) == 61", "len(imm_loads) == 60"), {"G9"}),
    ("MU9",  "data", ('fw_tests.get("0x400000") == 7', 'fw_tests.get("0x400000") == 6'), {"G10"}),
    ("MU10", "data", ("dict(tdeltas) == {4: 28, 8: 2}", "dict(tdeltas) == {4: 27, 8: 3}"), {"R1"}),
    ("MU11", "data", ('INS[0x51dcef] == ("cmp", "ecx,0x80")', 'INS[0x51dcef] == ("cmp", "ecx,0x81")'), {"R2"}),
    ("MU12", "data", ("0x94ee28 + 75 * 16 == 0x94f2d8", "0x94ee28 + 74 * 16 == 0x94f2d8"), {"G1"}),
    ("MU13", "code", "0x429ab9|lea eax,[edx+0x94d430]", {"G2"}),
    ("MU14", "code", "0x59f018|cmp eax,0x81", {"G4"}),
    ("MU15", "code", "0x59effa|mov BYTE PTR [esi+eax*1+0x94e5a9],0x0", {"G2", "G4", "G8"}),
    ("MU16", "code", "0x51dcce|mov DWORD PTR [eax],esi", {"G5"}),
    ("MU17", "code", "0x51df3d|inc DWORD PTR [eax+0x94e8a8]", {"G7"}),
    ("MU18", "code", "0x59ed6c|mov DWORD PTR [ebx+0x94d600],0xdfbe42", {"G8"}),
    ("MU19", "code", "0x51dd52|mov eax,0x94f4f0", {"G7", "G9"}),
    ("MU20", "code", "0x59f1d5|cmp eax,0x201", {"G6", "R2"}),
    ("MU21", "code", "0x56dfd0|mov edx,DWORD PTR [ebx+0x94f464]", {"G2", "G3"}),
    ("MU22", "code", "0x5a04d7|or ch,0x2", {"G10"}),
    ("MU23", "code", "0x59f0ec|mov DWORD PTR [esi-0x80],0x1", {"G9"}),
    ("MU24", "algo", "1", {"G6", "G7"}),
    ("MU25", "algo", "2", {"G2", "G8"}),
    ("MU26", "noop", "0x40100c|mov DWORD PTR [ebp-0x8],0x1", set()),
]

def run_script(path, env_extra):
    env = dict(os.environ)
    env.pop("M320_PATCH", None)
    env.pop("M320_ALGO", None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", path], cwd=REPO, env=env,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr

def score(out):
    """returns (observed_red_set, crashed_bool)"""
    if not re.search(r"^== M320: \d+/\d+ ==$", out, re.M):
        return set(), True
    red = set(re.findall(r"^FAIL (\S+)", out, re.M))
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
    rc, out = run_script(SCRIPT, {"M320_PATCH": "40100c|mov DWORD PTR [ebp-0x8],0x1"})
    obs, crashed = score(out)
    res.append(("S4 live NO-OP", (not crashed) and obs == set() and rc == 0))
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
    tmp = os.path.join(REPO, "scripts", "_m320_mut_%d.py" % os.getpid())
    try:
        for (mid, kind, payload, declared) in MUTANTS:
            if kind == "data":
                old, new = payload
                if src.count(old) != 1:
                    raise SystemExit("%s: literal not unique (%d): %r" % (mid, src.count(old), old))
                open(tmp, "w").write(src.replace(old, new))
                rc, out = run_script(tmp, {})
            elif kind == "code":
                rc, out = run_script(SCRIPT, {"M320_PATCH": payload})
            elif kind == "algo":
                rc, out = run_script(SCRIPT, {"M320_ALGO": payload})
            else:
                rc, out = run_script(SCRIPT, {"M320_PATCH": payload})
            obs, crashed = score(out)
            v = verdict(declared, obs, crashed)
            rows.append((mid, kind, declared, obs, v))
            print("%-6s %-5s declared=%-18s observed=%-18s %s" %
                  (mid, kind, sorted(declared), sorted(obs), v))
    finally:
        if os.path.exists(tmp): os.remove(tmp)
    h = hashlib.sha256()
    for (mid, kind, declared, obs, v) in rows:
        h.update(("%s:%s:%s:%s:%s|" % (mid, kind, sorted(declared), sorted(obs), v)).encode())
    nscore = sum(1 for r in rows if r[4] in ("OK", "NO-OP"))
    nnoop = sum(1 for r in rows if r[4] == "NO-OP")
    print("digest %s" % h.hexdigest()[:16])
    print("== M320 MUTATE: %d/%d scored + %d NO-OP ==" % (nscore, len(rows), nnoop))
    sys.exit(0 if nscore == len(rows) else 1)

if __name__ == "__main__":
    main()