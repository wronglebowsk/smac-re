#!/usr/bin/env python3
# M324 mutation harness: every VERIFIED claim row names the mutant that reddens it.
# 14 code mutants rewrite the DISASSEMBLY via M324_PATCH (leg args, diamond glue,
# feed fold, opener mode chain, the M323 const-0 store shape); 3 algorithm mutants
# via M324_ALGO (1: push-order reversal, 2: read/write direction swap, 3: closure
# seeded from the codec only); 1 save-data mutant via M324_SAVE (round dword 50->51
# in a temp copy); 1 evidence-data mutant via M324_EVIDENCE_ROOT (m302 live pin
# round 50->51); 1 declared NO-OP. A crash is NOT a red gate (m319 MU6 law): output
# without the 8-denominator summary scores CRASH and fails the harness.
# --selftest: 3 synthetic scorer checks + 1 live NO-OP run.
import os, re, sys, shutil, struct, subprocess, hashlib, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "m324_save_carry.py")
SAVE = os.path.join(REPO, "programs/saves/m54b_clean.SAV")
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"]
EVFILES = ["evidence/m302_livepins.txt", "evidence/m272w9.gdblog"]
TMPBASE = os.environ.get("TMPDIR", os.path.join(REPO, "scratch"))

# (id, kind, payload, declared gate set) - sets MEASURED by the run, declared here
MUTANTS = [
    ("MU1",  "code", "0x59687c|push 0x985bb8", {"G1", "G2", "G8"}),
    ("MU2",  "code", "0x596866|push 0x44", {"G1", "G2", "G8"}),
    ("MU3",  "code", "0x59688a|call 0x64c9a0", {"G1", "G2", "G8"}),
    ("MU4",  "code", "0x596a7e|push 0x220", {"G1", "G3"}),
    ("MU4b", "code", "0x596a83|push 0x94d530", {"G1"}),  # +0x100 shift: G3 coverage survives
    ("MU5",  "code", "0x596ec3|push 0x100", {"G1", "G3"}),
    ("MU6",  "code", "0x44263c|mov edx,DWORD PTR [ecx+0x94d654]", {"G4"}),
    ("MU7",  "code", "0x597fad|call 0x4e0350", {"G6", "G7", "G8"}),
    ("MU8",  "savedata", ("round", 0x50, 51), {"G5", "G8"}),
    ("MU9",  "evdata", ("evidence/m302_livepins.txt", "round 50", "round 51"), {"G5"}),
    ("MU10", "algo", "1", {"G1", "G2", "G3", "G8"}),
    ("MU11", "algo", "2", {"G1", "G2", "G3", "G8"}),
    ("MU12", "code", "0x596881|je 0x596883", {"G7"}),
    ("MU13", "code", "0x59689a|cmp DWORD PTR ds:0x985dbc,0x5", {"G7"}),
    ("MU14", "code", "0x44262b|jle 0x442642", {"G4"}),
    ("MU15", "algo", "3", {"G6"}),
    ("MU16", "code", "0x626fd7|mov ds:0x999fa8,eax", {"G4"}),
    ("MU17", "code", "0x5a108b|mov DWORD PTR ds:0x985afc,edx", {"G8"}),
    ("MU18", "noop", "0x597f9a|mov DWORD PTR ds:0x91b5cc,ebx", set()),
]

def run_script(env_extra):
    env = dict(os.environ)
    for k in ("M324_PATCH", "M324_ALGO", "M324_EVIDENCE_ROOT", "M324_SAVE"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-u", SCRIPT], cwd=REPO, env=env,
                       capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr

def score(out):
    """(observed_red_set, crashed); denominator must be the shipped 8"""
    m = re.search(r"^== M324: (\d+)/(\d+) == digest [0-9a-f]{16}$", out, re.M)
    if not m or m.group(2) != "8":
        return set(), True
    red = set(re.findall(r"^(G\d) FAIL", out, re.M))
    return red, False

def verdict(declared, observed, crashed):
    if crashed: return "CRASH"
    if observed == declared: return "OK" if declared else "NO-OP"
    return "MISMATCH"

def selftest():
    res = []
    res.append(("S1 scorer match", verdict({"G4"}, {"G4"}, False) == "OK"))
    res.append(("S2 scorer mismatch", verdict({"G4"}, {"G5"}, False) == "MISMATCH"))
    res.append(("S3 scorer crash", verdict({"G4"}, set(), True) == "CRASH"))
    rc, out = run_script({"M324_PATCH": "0x597f9a|mov DWORD PTR ds:0x91b5cc,ebx"})
    obs, crashed = score(out)
    res.append(("S4 live NO-OP", (not crashed) and obs == set() and rc == 0
                and "== M324: 8/8 ==" in out))
    for nm, ok in res:
        print(("OK  " if ok else "FAIL") + " " + nm)
    n = sum(1 for _, ok in res if ok)
    print("selftest %d/%d" % (n, len(res)))
    return n == len(res)

def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    rows = []
    tmp = tempfile.mkdtemp(prefix="m324_mut_", dir=TMPBASE)
    evtmp = os.path.join(tmp, "ev")
    try:
        for (mid, kind, payload, declared) in MUTANTS:
            if kind == "code":
                rc, out = run_script({"M324_PATCH": payload})
            elif kind == "algo":
                rc, out = run_script({"M324_ALGO": payload})
            elif kind == "savedata":
                _, off, val = payload
                b = bytearray(open(SAVE, "rb").read())
                struct.pack_into("<I", b, off, val)
                sp = os.path.join(tmp, "mut_%s.SAV" % mid)
                open(sp, "wb").write(b)
                rc, out = run_script({"M324_SAVE": sp})
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
                rc, out = run_script({"M324_EVIDENCE_ROOT": evtmp})
            else:  # noop
                rc, out = run_script({"M324_PATCH": payload})
            obs, crashed = score(out)
            v = verdict(declared, obs, crashed)
            rows.append((mid, kind, declared, obs, v))
            print("%-6s %-8s declared=%-28s observed=%-28s %s" %
                  (mid, kind, sorted(declared), sorted(obs), v))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    h = hashlib.sha256()
    for (mid, kind, declared, obs, v) in rows:
        h.update(("%s:%s:%s:%s:%s|" % (mid, kind, sorted(declared), sorted(obs), v)).encode())
    nscore = sum(1 for r in rows if r[4] in ("OK", "NO-OP"))
    nnoop = sum(1 for r in rows if r[4] == "NO-OP")
    print("digest %s" % h.hexdigest()[:16])
    print("== M324 MUTATE: %d/%d scored + %d NO-OP ==" % (nscore, len(rows), nnoop))
    sys.exit(0 if nscore == len(rows) else 1)

if __name__ == "__main__":
    main()