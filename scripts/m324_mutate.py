#!/usr/bin/env python3
# M324 mutation harness: every VERIFIED claim row names the mutant that reddens it.
# 21 code mutants rewrite the DISASSEMBLY via M324_PATCH (leg args + push positions,
# diamond glue, entry window, mode arg chain, feed fold + MAX shape, opener esi-0
# source, the M323 const-0 store shape); 3 algorithm mutants via M324_ALGO
# (1: push-order reversal, 2: read/write direction swap, 3: closure seeded from the
# codec only); 1 save-data mutant via M324_SAVE (round dword 50->51 in a temp copy);
# 2 evidence-data mutants via M324_EVIDENCE_ROOT (m302 live pin round 50->51; m272
# log + a fake writer event); 1 declared NO-OP. A crash is NOT a red gate (m319 MU6
# law): output without the 8-denominator summary scores CRASH and fails the harness.
# DIGEST (review #326 P1-2): hashes each mutant's MEASURED payload - the patch/data
# literal AND the acceptance digest of that mutant's run (itself a hash of the rich
# measured detail) - not just gate labels.
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
    # review #326 fixes: esi-0 source (P2-4), mode arg chain (P2-5), MAX shape
    # (P2-6), M272 full inventory (P2-8), entry window (P2-3), sibling dest (P1-1)
    ("MU19", "code", "0x5a0fd3|mov esi,0x1", {"G8"}),
    ("MU20", "code", "0x597f98|push eax", {"G7"}),
    ("MU21", "code", "0x442648|mov eax,ds:0x999fa8", {"G4"}),
    ("MU22", "evdata", ("evidence/m272w9.gdblog",
                        "[Inferior 1 (process 3780205) detached]",
                        "[Inferior 1 (process 3780205) detached]\n"
                        "M272C CTRL pc=0x5a0fa0 ret=0x5a1090 round=0 cp=0"),
     {"G7", "G8"}),
    ("MU23", "code", "0x596864|cmp eax,ecx", {"G7"}),
    ("MU24", "code", "0x5968cb|push 0x985bb8", {"G1", "G2"}),
    ("MU25", "code", "0x59685f|je 0x59688a", {"G7", "G8"}),   # branch in the entry window
    ("MU26", "code", "0x5968c6|push 0x44", {"G1", "G2"}),  # sibling size push
    ("MU27", "code", "0x596856|mov eax,DWORD PTR [ebp+0x8]", {"G7"}),  # param_2 load
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
    """(observed_red_set, crashed, run_digest); denominator must be the shipped 8"""
    m = re.search(r"^== M324: (\d+)/(\d+) == digest ([0-9a-f]{16})$", out, re.M)
    if not m or m.group(2) != "8":
        return set(), True, None
    red = set(re.findall(r"^(G\d) FAIL", out, re.M))
    return red, False, m.group(3)

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
    obs, crashed, _dig = score(out)
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
            obs, crashed, rdig = score(out)
            v = verdict(declared, obs, crashed)
            rows.append((mid, kind, payload, declared, obs, v, rdig))
            print("%-6s %-8s declared=%-28s observed=%-28s %-8s run=%s" %
                  (mid, kind, sorted(declared), sorted(obs), v, rdig))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    h = hashlib.sha256()
    for (mid, kind, payload, declared, obs, v, rdig) in rows:
        # MEASURED payload: the mutant literal + the run's acceptance digest
        h.update(("%s:%s:%s:%s:%s:%s:%s|" % (
            mid, kind, payload, sorted(declared), sorted(obs), v, rdig)).encode())
    nscore = sum(1 for r in rows if r[5] in ("OK", "NO-OP"))
    nnoop = sum(1 for r in rows if r[5] == "NO-OP")
    print("digest %s" % h.hexdigest()[:16])
    print("== M324 MUTATE: %d/%d scored + %d NO-OP ==" % (nscore, len(rows), nnoop))
    sys.exit(0 if nscore == len(rows) else 1)

if __name__ == "__main__":
    main()