#!/usr/bin/env python3
"""M333 mutation harness: prove every gate of m333_feeder_slot_census.py is LOAD-BEARING.

Two families (skill instrument-laws):
  CODE mutants  - M333_PATCH="addr|mn ops" corrupts real .text instructions the instrument
                  must read; contact proof = the instrument's own `patches applied: 1/1`.
  EXPECT mutants- rewrite ONE literal in a scratch copy of the instrument; the gate must
                  still go red on the REAL bytes (proves the expectation, not the bytes,
                  is what was load-bearing).

Scoring (four outcomes, classified): a mutant PASSES iff set(red gates) == its DECLARED set.
  extra reds = undeclared dependency; missing reds = WEAK; empty = NO-OP; a Traceback in
  the output is a CRASH (rc==1 alone is ambiguous - RED lines print before the death).
Baseline precondition: the UNMUTATED instrument must exit 0 or nothing is scored.
--selftest: perturb only the DECLARED sets (empty / superset / partial) against a real
mutant's observed reds and require rejection; plus a genuine NO-OP mutant (patch to the
identical instruction) that must be rejected as reddening nothing.

Run: python3 -u scripts/m333_mutate.py          -> PASS HARNESS n/n + digest
     python3 -u scripts/m333_mutate.py --selftest
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTR = os.path.join(ROOT, "scripts", "m333_feeder_slot_census.py")
SCRATCH = os.path.join(ROOT, "scratch")
GATE_RE = re.compile(r"^(PASS|FAIL) (G[1-7]|RIVAL)\b", re.M)

# (id, kind, spec, declared gate set)
MUTANTS = [
    # ---- CODE family: corrupt the real instructions the instrument measures
    ("MU1", "code", "4f4802|mov esi,0x0", {"G1", "RIVAL"}),          # counter 0-based -> R1 holds
    ("MU2", "code", "4f48c8|lea eax,[eax+eax*2]", {"G1"}),           # loop fold leaf != esi
    ("MU3", "code", "4f491c|nop ", {"G4", "G5"}),                    # drop and 1 -> no bit5 extract
    ("MU4", "code", "4f4931|mov DWORD PTR [edx],eax", {"G4", "G5"}), # store wrong reg -> no RMW back
    ("MU5", "code", "4f4a35|cmp esi,0x22", {"G1"}),                  # range bound moved
    ("MU6", "code", "4f4a3b|jl 0x4f4a41", {"G1"}),                   # back-edge target moved
    ("MU7", "code", "4f48f3|sete dl", {"G6"}),                       # owner-match sete retargeted
    ("MU8", "code", "4f4823|call 0x407410", {"G3"}),                 # mapper call retargeted
    ("MU9", "code", "4f47dc|lea eax,[eax+eax*2]", {"G2"}),           # cost-body fold leaf != esi
    ("MU10", "code", "4f47f6|mov eax,ds:0x8f0d61", {"G4"}),          # owner source retargeted
    # ---- EXPECT family: rewrite ONE literal in the instrument
    ("ME1", "expect", ("ITEM_UPKEEP, ITEM_ROW0, ROW = 0x984D48,", "ITEM_UPKEEP, ITEM_ROW0, ROW = 0x984D4C,"),
     {"G1", "G2", "G7", "RIVAL"}),                                     # wrong table address (G7's rowdiff reads it too - measured, s314)
    ("ME2", "expect", ("CBIT, CIMM, CCLR = 5, 0x20, 0xFFFFFFDF", "CBIT, CIMM, CCLR = 5, 0x20, 0xFFFFFFBF"),
     {"G4"}),                                                         # wrong clear mask
    ("ME3", "expect", ("BLKBASE, BLKSTRIDE, NBLK = 0x94D430, 0x20BC, 8", "BLKBASE, BLKSTRIDE, NBLK = 0x94D430, 0x20B0, 8"),
     {"G4"}),                                                         # stride 2092 != the measured 2095 fold (0x20BD was a NO-OP: //4 lands on 2095 and offset 0 matches ANY stride)
    ("ME4", "expect", ("BLKBASE, BLKSTRIDE, NBLK = 0x94D430, 0x20BC, 8", "BLKBASE, BLKSTRIDE, NBLK = 0x94D431, 0x20BC, 8"),
     {"G4", "G5"}),                                                   # block base off by one -> no site names block+0
]


def run_instrument(patch=None, src_copy=None):
    env = dict(os.environ)
    if patch is not None:
        env["M333_PATCH"] = patch
    path = INSTR
    if src_copy is not None:
        os.makedirs(SCRATCH, exist_ok=True)
        path = os.path.join(SCRATCH, "m333_mutate_copy.py")
        with open(path, "w") as f:
            f.write(src_copy)
    p = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True, env=env, timeout=600)
    return p.returncode, p.stdout + p.stderr


def observed_reds(out):
    return {m.group(2) for m in GATE_RE.finditer(out) if m.group(1) == "FAIL"}


def verdict(declared, observed, crashed, contact):
    """Classify one mutant. Returns (ok, why)."""
    if crashed:
        return False, "CRASH (traceback in output)"
    if not contact:
        return False, "NO CONTACT (patch not applied / copy not used)"
    if not observed:
        return False, "NO-OP (reddened nothing)"
    if observed == set(declared):
        return True, "ok"
    extra = observed - set(declared)
    missing = set(declared) - observed
    if extra and missing:
        return False, "WRONG SET (extra=%s missing=%s)" % (sorted(extra), sorted(missing))
    if extra:
        return False, "UNDECLARED RED %s" % sorted(extra)
    return False, "WEAK (missing %s)" % sorted(missing)


def main():
    selftest = "--selftest" in sys.argv
    rc, out = run_instrument()
    if rc != 0:
        print("BASELINE NOT GREEN (rc=%d) - refusing to score" % rc)
        return 1
    print("baseline: PASS, digest=%s" % re.search(r"digest\(rows\)=([0-9a-f]+)", out).group(1))

    rows = []
    allok = True
    npass = 0
    if selftest:
        # perturb ONLY the declared sets against MU1's real observed reds
        _, mout = run_instrument(patch=MUTANTS[0][2])
        obs = observed_reds(mout)
        if obs != {"G1", "RIVAL"}:
            print("selftest precondition broken: MU1 observed %s" % sorted(obs))
            return 1
        st = [("ST1 empty declared", verdict(set(), obs, False, True)),
              ("ST2 superset declared", verdict({"G1", "RIVAL", "G7"}, obs, False, True)),
              ("ST3 partial declared", verdict({"G1"}, obs, False, True)),
              ("ST4 crash class", verdict({"G1", "RIVAL"}, obs, True, True)),
              ("ST5 no-contact class", verdict({"G1", "RIVAL"}, obs, False, False))]
        # a genuine NO-OP mutant: patch to the IDENTICAL instruction
        rcn, outn = run_instrument(patch="4f4802|mov esi,0x1")
        obsn = observed_reds(outn)
        contactn = "patches_applied=1" in outn
        st.append(("ST6 real NO-OP mutant", verdict({"G1"}, obsn, "Traceback" in outn, contactn)))
        nok = 0
        for name, (ok, why) in st:
            rejected = not ok
            print("%s %s (%s)" % ("PASS" if rejected else "FAIL", name, why))
            nok += rejected
            rows.append("%s %s %s" % ("ST", name, why))
        print("%s selftest: %d/%d" % ("PASS" if nok == len(st) else "FAIL", nok, len(st)))
        return 0 if nok == len(st) else 1

    for mid, kind, spec, declared in MUTANTS:
        if kind == "code":
            rcx, outx = run_instrument(patch=spec)
            contact = "patches_applied=1" in outx
        else:
            src = open(INSTR).read()
            if src.count(spec[0]) != 1:
                rows.append("%s FAIL expect literal not unique (%d)" % (mid, src.count(spec[0])))
                allok = False
                continue
            rcx, outx = run_instrument(src_copy=src.replace(spec[0], spec[1]))
            contact = "patches_applied=0" in outx  # the copy ran, unpatched
        obs = observed_reds(outx)
        ok, why = verdict(declared, obs, "Traceback" in outx, contact)
        print("%s %s declared=%s observed=%s (%s)" % ("PASS" if ok else "FAIL", mid,
                                                      sorted(declared), sorted(obs), why))
        rows.append("%s %s %s %s" % (mid, sorted(declared), sorted(obs), why))
        allok = allok and ok
        npass += ok

    print("digest(harness)=%s" % hashlib.sha256("\n".join(rows).encode()).hexdigest()[:16])
    print("%s HARNESS %d/%d" % ("PASS" if allok else "FAIL", npass, len(MUTANTS)))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
