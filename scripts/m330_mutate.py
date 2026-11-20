#!/usr/bin/env python3
"""M330 mutation harness (chain2 s9). Every VERIFIED gate of
m330_block300_census.py must be reddened by >=1 named mutant; declared sets
are MEASURED (harness asserts declared == measured, not the author's word).
MU19 is the ALGORITHM mutant (provenance filter off); MU20 is the declared
NO-OP; MU21 is an input mutant (different save). --selftest checks the
harness machinery itself (5 checks).

Usage: python3 -u scripts/m330_mutate.py [--selftest]
"""
import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = [sys.executable, "-u", os.path.join(ROOT, "scripts", "m330_block300_census.py")]
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12", "R"]

# (id, kind, payload, declared reddened set) — standard format (review_lint L2b
# parses "code" entries and checks each patch addr is literal-read by the instrument)
MUTANTS = [
    ("MU1",  "code", "0x52072d|mov eax,0x66666667", {"G4", "R"}),
    ("MU2",  "code", "0x520732|mov edx,ecx", {"G4", "R"}),
    ("MU3",  "code", "0x520758|mov ecx,ecx", {"G4", "R"}),
    ("MU4",  "code", "0x52078d|xor ecx,ecx", {"G4", "R"}),
    ("MU5",  "code", "0x520719|cmp eax,0x4", {"G5"}),
    ("MU6",  "code", "0x52071c|jle 0x520758", {"G5"}),
    ("MU7",  "code", "0x52062f|cmp ebx,0x95bc30", {"G6", "R"}),
    ("MU8",  "code", "0x52056d|mov DWORD PTR [esi+0x94d730],ecx", {"G2", "G7", "R"}),
    ("MU9",  "code", "0x4f495e|sub edx,eax", {"G10"}),
    ("MU10", "code", "0x4f4936|sar eax,0x2", {"G10"}),
    ("MU11", "code", "0x520838|add ecx,edi", {"G11"}),
    ("MU12", "code", "0x54b1e5|mov DWORD PTR [ebp+0x8],eax", {"G12"}),
    ("MU13", "code", "0x535cc3|mov DWORD PTR [ebp-0x14],ebx", {"G12"}),
    ("MU14", "code", "0x5791a6|lea ecx,[eax*4+0x94d430]", {"G12"}),
    ("MU15", "code", "0x596a91|call 0x64cc01", {"G8"}),
    ("MU16", "code", "0x51f53c|mov DWORD PTR [esi+0x94d730],eax", {"G1", "G9"}),
    ("MU17", "code", "0x5233fe|sub ebx,DWORD PTR [ecx+0x4]", {"G1"}),
    ("MU18", "code", "0x5233d0|mov ecx,0x94f7e8", {"G1"}),
    ("MU19", "algo", "1", {"G1", "G2", "G3"}),
    ("MU20", "algo", "2", set()),          # declared NO-OP: ALGO=2 = inert alias of 0
    ("MU21", "save", "programs/saves/m112auto1.SAV", {"G8"}),
    # review #340 round: input-law, liveness and operand pins
    ("MU22", "code", "0x4f48cb|shl eax,0x5", {"G10"}),
    ("MU23", "code", "0x4f4811|cmp esi,0x23", {"G10"}),
    ("MU24", "code", "0x4f4837|mov al,BYTE PTR [ecx+edx*1+0x95da9d]", {"G10"}),
    ("MU25", "code", "0x520635|mov DWORD PTR [ebp-0x4],ebx", {"G6"}),
    ("MU26", "code", "0x52065d|mov DWORD PTR [ebp-0x4],eax", {"G6"}),
    ("MU27", "code", "0x52055e|mov eax,esi", {"G1", "G2", "G3", "G7"}),
    ("MU28", "code", "0x5362b4|mov esi,DWORD PTR [ebp+0x8]", {"G12"}),
    ("MU29", "code", "0x535c93|mov edi,DWORD PTR [ebp+0x8]", {"G12"}),
    ("MU30", "code", "0x54b35f|mov edx,eax", {"G12"}),
    ("MU31", "code", "0x5233f3|mov ebx,DWORD PTR [edx+0x94d734]", {"G1", "G3"}),
    ("MU32", "code", "0x520769|shr ecx,0x1e", {"G4"}),
]

def env_for(kind, payload):
    if kind == "code": return {"M330_PATCH": payload}
    if kind == "save": return {"M326_SAVE": os.path.join(ROOT, payload)}
    return {"M330_ALGO": payload}

def run(env_extra):
    env = dict(os.environ)
    for k in ("M330_PATCH", "M330_ALGO", "M326_SAVE", "M326_PATCH", "M326_ALGO"):
        env.pop(k, None)
    env.update(env_extra)
    p = subprocess.run(CENSUS, env=env, capture_output=True, text=True, timeout=600)
    gates = {}
    for line in p.stdout.splitlines():
        m = re.match(r"^(PASS|FAIL) (\w+):", line)
        if m:
            gates[m.group(2)] = (m.group(1) == "PASS")
    return p.returncode, gates, p.stdout, p.stderr

def selftest():
    rows = []
    ok = True
    rc, g, out, err = run({"M330_PATCH": "deadbeef|mov eax,0x1"})
    st1 = rc != 0 and "not in .text cache" in err
    rows.append(("ST1 bad-address rejected", st1)); ok &= st1
    rc, g, out, err = run({"M330_PATCH": "52072d|mov eax,0x55555556"})
    st2 = rc != 0 and "already equal" in err
    rows.append(("ST2 equal-patch rejected", st2)); ok &= st2
    union = set().union(*[d for _, _, _, d in MUTANTS])
    st3 = union >= set(GATES)
    rows.append(("ST3 coverage: every gate has a mutant", st3)); ok &= st3
    noops = [i for i, _, _, d in MUTANTS if not d]
    st4 = noops == ["MU20"]
    rows.append(("ST4 exactly one declared NO-OP (MU20)", st4)); ok &= st4
    rc, g, out, err = run({})
    st5 = rc == 0 and len(g) == len(GATES) and all(g.values())
    rows.append(("ST5 base run 13/13 PASS", st5)); ok &= st5
    for name, good in rows:
        print("%s %s" % ("PASS" if good else "FAIL", name))
    print("== selftest: %d/%d ==" % (sum(1 for _, x in rows if x), len(rows)))
    return 0 if ok else 1

def main():
    if "--selftest" in sys.argv:
        return selftest()
    rows = []
    rc, g, out, err = run({})
    base_ok = rc == 0 and len(g) == len(GATES) and all(g.values())
    rows.append(("BASE", "-", "-", "all 13 PASS" if base_ok else "BASE BROKEN", base_ok))
    scored = noop = mismatch = crash = 0
    for mid, kind, payload, declared in MUTANTS:
        rc, g, out, err = run(env_for(kind, payload))
        if len(g) != len(GATES):
            measured = None
            verdict = "CRASH"
            crash += 1
            good = False
        else:
            measured = {x for x, v in g.items() if not v}
            if not declared:
                good = measured == set() and rc == 0
                verdict = "NO-OP-OK" if good else "MISMATCH"
                noop += 1 if good else 0
                mismatch += 0 if good else 1
            else:
                good = measured == declared
                verdict = "OK" if good else "MISMATCH"
                scored += 1 if good else 0
                mismatch += 0 if good else 1
        rows.append((mid, sorted(declared), sorted(measured) if measured is not None else "CRASH",
                     verdict, good))
    print("mutant | declared | measured | verdict")
    for mid, d, m, v, good in rows:
        print("%s %s | %s | %s | %s" % ("PASS" if good else "FAIL", mid, d, m, v))
    union = set().union(*[d for _, _, _, d in MUTANTS])
    cov = union >= set(GATES)
    print("coverage %s (union=%s)" % (cov, sorted(union)))
    h = hashlib.sha256("\n".join(str(r) for r in rows).encode()).hexdigest()[:16]
    print("digest %s" % h)
    total_ok = scored + noop
    print("HARNESS %d/%d scored OK + %d/%d NO-OP, %d MISMATCH/%d CRASH"
          % (scored, len(MUTANTS) - 1, noop, 1, mismatch, crash))
    print("== M330 mutate: %d/%d ==" % (total_ok + (1 if base_ok else 0) + (1 if cov else 0),
                                        len(MUTANTS) + 2))
    return 0 if (mismatch == 0 and crash == 0 and base_ok and cov) else 1

if __name__ == "__main__":
    sys.exit(main())