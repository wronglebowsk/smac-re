#!/usr/bin/env python3
"""M331 mutation harness (chain2 s10). Every VERIFIED gate of
m331_ledger_census.py must be reddened by >=1 named mutant; declared sets
are MEASURED (harness asserts declared == measured, not the author's word).
MU30 is the ALGORITHM mutant (provenance filter off); MU31 is the declared
NO-OP; MU32 is an input mutant (different save). --selftest checks the
harness machinery itself (5 checks).

Usage: python3 -u scripts/m331_mutate.py [--selftest]
"""
import hashlib, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = [sys.executable, "-u", os.path.join(ROOT, "scripts", "m331_ledger_census.py")]
GATES = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11",
         "G12", "G13", "R"]

# (id, kind, payload, declared reddened set) — standard format (review_lint L2b
# parses "code" entries and checks each patch addr is literal-read by the instrument)
MUTANTS = [
    ("MU1",  "code", "0x520567|mov DWORD PTR [esi+0x94d72c],ecx", {"G3", "G4", "R"}),
    ("MU2",  "code", "0x4eacd9|mov DWORD PTR [ecx],edx", {"G3"}),
    ("MU3",  "code", "0x4eac9b|cmp eax,0x2", {"G5"}),
    ("MU4",  "code", "0x4eacaa|cmp eax,0x1869e", {"G5"}),
    ("MU5",  "code", "0x4eacc9|mov esi,DWORD PTR [ecx*4+0x94d730]", {"G1", "G3"}),
    ("MU6",  "code", "0x4f5cb0|add DWORD PTR [esi+0x94d730],ecx", {"G2", "G3", "G6"}),
    ("MU7",  "code", "0x4f5c92|mov eax,0x94f5b0", {"G6"}),
    ("MU8",  "code", "0x4f5cbf|cmp eax,0x95dad4", {"G6"}),
    ("MU9",  "code", "0x4f5b2c|mov DWORD PTR ds:0x8f0d64,edx", {"G5"}),
    ("MU10", "code", "0x52080c|mov DWORD PTR [esi+0x94d730],edx", {"G1", "G3", "G7"}),
    ("MU11", "code", "0x5207c6|mov eax,0x51eb851e", {"G7"}),
    ("MU12", "code", "0x52083f|sub ecx,edx", {"G8", "R"}),
    ("MU13", "code", "0x54b375|lea ecx,[ecx+ecx*8]", {"G9", "R"}),
    ("MU14", "code", "0x54b384|cmp eax,0x33", {"G9"}),
    ("MU15", "code", "0x5362e3|mov edx,DWORD PTR [eax+0x94e48c]", {"G10"}),
    ("MU16", "code", "0x536313|mov eax,0x66666666", {"G10"}),
    ("MU17", "code", "0x5233f9|add edi,ebx", {"G11"}),
    ("MU18", "code", "0x532876|mov eax,DWORD PTR [edi+0x94d730]", {"G1", "G3", "G11"}),
    ("MU19", "code", "0x45b23f|mov ecx,DWORD PTR [eax+0x94d73c]", {"G2", "G3", "G11"}),
    ("MU20", "code", "0x596a91|call 0x64cc01", {"G12"}),
    ("MU21", "code", "0x51f53c|mov DWORD PTR [esi+0x94d72c],eax", {"G1", "G12"}),
    ("MU22", "code", "0x59f264|mov DWORD PTR [ebx+0x94d730],edx", {"G1", "G3", "G12"}),
    ("MU23", "code", "0x5791a6|lea ecx,[eax*4+0x94d430]", {"G13"}),
    ("MU24", "code", "0x54b1e5|mov DWORD PTR [ebp+0x8],eax", {"G9"}),
    ("MU25", "code", "0x535cc3|mov DWORD PTR [ebp-0x14],ebx", {"G10"}),
    ("MU26", "code", "0x4eaa5f|call 0x4e9881", {"G5"}),
    ("MU27", "code", "0x4f5b8b|shl esi,0x3", {"G6"}),
    ("MU28", "code", "0x531e78|mov DWORD PTR [ebp-0xc],eax", {"G11"}),
    ("MU29", "code", "0x54d3ca|shl ebx,0x3", {"G9"}),
    ("MU30", "algo", "1", {"G1", "G2"}),
    ("MU31", "algo", "2", set()),          # declared NO-OP: ALGO=2 = inert alias of 0
    ("MU32", "save", "programs/saves/m112auto1.SAV", {"G8", "G12"}),
    ("MU33", "code", "0x4f4962|mov DWORD PTR [edi+0x94d72c],edx", {"G1", "R"}),
    ("MU34", "code", "0x5207d9|mov DWORD PTR [esi+0x94d738],edx", {"G2", "G7", "R"}),
]

def env_for(kind, payload):
    if kind == "code": return {"M331_PATCH": payload}
    if kind == "save": return {"M326_SAVE": os.path.join(ROOT, payload)}
    return {"M331_ALGO": payload}

def run(env_extra):
    env = dict(os.environ)
    for k in ("M331_PATCH", "M331_ALGO", "M326_SAVE", "M326_PATCH", "M326_ALGO"):
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
    rc, g, out, err = run({"M331_PATCH": "deadbeef|mov eax,0x1"})
    st1 = rc != 0 and "not in .text cache" in err
    rows.append(("ST1 bad-address rejected", st1)); ok &= st1
    rc, g, out, err = run({"M331_PATCH": "52083f|add ecx,edx"})
    st2 = rc != 0 and "already equal" in err
    rows.append(("ST2 equal-patch rejected", st2)); ok &= st2
    union = set().union(*[d for _, _, _, d in MUTANTS])
    st3 = union >= set(GATES)
    rows.append(("ST3 coverage: every gate has a mutant", st3)); ok &= st3
    noops = [i for i, _, _, d in MUTANTS if not d]
    st4 = noops == ["MU31"]
    rows.append(("ST4 exactly one declared NO-OP (MU31)", st4)); ok &= st4
    rc, g, out, err = run({})
    st5 = rc == 0 and len(g) == len(GATES) and all(g.values())
    rows.append(("ST5 base run 14/14 PASS", st5)); ok &= st5
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
    rows.append(("BASE", "-", "-", "all 14 PASS" if base_ok else "BASE BROKEN", base_ok))
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
        print("%s %s %s | %s | %s" % ("PASS" if good else "FAIL", mid, d, m, v))
    union = set().union(*[d for _, _, _, d in MUTANTS])
    cov = union >= set(GATES)
    print("coverage %s (union=%s)" % (cov, sorted(union)))
    h = hashlib.sha256("\n".join(str(r) for r in rows).encode()).hexdigest()[:16]
    print("digest %s" % h)
    total_ok = scored + noop
    print("HARNESS %d/%d scored OK + %d/%d NO-OP, %d MISMATCH/%d CRASH"
          % (scored, len(MUTANTS) - 1, noop, 1, mismatch, crash))
    print("== M331 mutate: %d/%d ==" % (total_ok + (1 if base_ok else 0) + (1 if cov else 0),
                                        len(MUTANTS) + 2))
    return 0 if (mismatch == 0 and crash == 0 and base_ok and cov) else 1

if __name__ == "__main__":
    sys.exit(main())