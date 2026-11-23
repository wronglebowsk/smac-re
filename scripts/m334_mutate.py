#!/usr/bin/env python3
"""M334 mutation harness: prove every gate of m334_powershort_census.py is LOAD-BEARING.

Two families (skill instrument-laws):
  CODE mutants  - M334_PATCH="addr|mn ops" corrupts real .text instructions the instrument
                  must read; contact proof = the instrument's own `patches applied: 1/1`.
  EXPECT mutants- rewrite ONE literal in a scratch copy of the instrument; the gate must
                  still go red on the REAL bytes (proves the EXPECTATION, not the bytes,
                  is what was load-bearing).

Scoring: a mutant PASSES iff set(red items) == its DECLARED set, where the declared set is
AUTHORED HERE and the observed set is MEASURED — both directions are enforced (extra red =
UNDECLARED dependency, missing red = WEAK mutant). An empty set is a NO-OP, a Traceback is a
CRASH, and a missing contact line means the patch never reached the instrument.
Baseline precondition: the UNMUTATED instrument must exit 0 or nothing is scored.
--selftest: perturb only the DECLARED sets (empty / superset / partial) against a real
mutant's observed reds and require rejection; plus a genuine NO-OP mutant (patch to the
identical instruction) that must be rejected as reddening nothing.

Run: python3 -u scripts/m334_mutate.py          -> PASS HARNESS n/n + digest
     python3 -u scripts/m334_mutate.py --selftest
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTR = os.path.join(ROOT, "scripts", "m334_powershort_census.py")
SCRATCH = os.path.join(ROOT, "scratch")
GATE_RE = re.compile(r"^(PASS|FAIL) (G[1-7]|RIVAL[1-3])\b", re.M)

# (id, kind, spec, declared item set)
MUTANTS = [
    # ---- CODE family: corrupt the real instructions the instrument measures
    ("MU1", "code", "4f48cb|shl eax,0x3", {"G1"}),                    # upkeep fold 24 != 48
    ("MU2", "code", "4f4942|shl edi,0x3", {"G1"}),                     # block fold 4188 != 8380
    ("MU3", "code", "4f4950|add ecx,eax", {"G1"}),                      # ENERGY RMW becomes add
    ("MU4", "code", "4f4970|jle 0x4f4a34", {"G2"}),                     # negative-test polarity
    ("MU5", "code", "4f4976|cmp DWORD PTR [edi+0x94d43c],0x1", {"G2"}),  # branch A gates +0xc
    ("MU6", "code", "4f4992|nop ", {"G2"}),                             # branch B loses neg(item)
    ("MU7", "code", "59eed1|mov eax,0x4", {"G3"}),                      # AI difficulty 3 -> 4
    ("MU8", "code", "59eeca|mov eax,ds:0x985aee", {"G3"}),              # create reads another global
    ("MU9", "code", "57ef39|mov edx,DWORD PTR [ebx]", {"G3"}),          # save/load stops being a byte
    ("MU10", "code", "4f4834|shl ecx,0x3", {"G4"}),                     # charge map fold 152
    ("MU11", "code", "4f49cb|shl eax,0x3", {"G4"}),                     # removal map fold 152
    ("MU12", "code", "4f49d8|neg dl", {"G4"}),                          # clear loses its `not`
    ("MU13", "code", "4f49d1|lea eax,[eax+ecx*1+0x927ac0]", {"G4", "G7", "RIVAL2"}),  # clears the DISABLED LIST instead
    ("MU14", "code", "4f49ef|shl esi,0x3", {"G5"}),                     # price fold 24*item
    ("MU15", "code", "4f49f7|add eax,DWORD PTR [esi+0x984d44]", {"G5"}),  # price stops being a product
    ("MU16", "code", "4f4a0b|add DWORD PTR [edi+0x94d650],eax", {"G5", "RIVAL1"}),  # the store BECOMES a refund
    ("MU17", "code", "4f49f2|call 0x4e40a4", {"G5"}),                   # factor callee retargeted
    ("MU18", "code", "4f4a24|push 0x68d258", {"G6"}),                   # memo label VA moved
    ("MU19", "code", "4f4a18|push 0x68d264", {"G6"}),                   # memo icon VA moved
    ("MU20", "code", "4f4a09|push 0x2", {"G6"}),                        # slot-setter param_1 != 1
    ("MU21", "code", "4f4a3b|jl 0x4f4a41", {"G7"}),                     # back-edge retargeted
    ("MU22", "code", "4f49e1|mov BYTE PTR [ebx],cl", {"G4", "G7"}),     # clear stores through another reg
    ("MU23", "code", "4f49da|mov cl,BYTE PTR [ebx]", {"G4"}),           # clear reads another reg
    ("MU24", "code", "4f4837|mov al,BYTE PTR [ecx+edx*1+0x95da98]", {"G4", "G7"}),  # charge tests another table
    ("MU25", "code", "4f4a16|push 0x984d38", {"RIVAL3"}),               # memo gains a facility operand
    ("MU26", "code", "4f4931|mov DWORD PTR [edx+0x8],ecx", {"G3"}),     # a FOLDED block-pointer store to +0x8 appears
    # ---- EXPECT family: rewrite ONE literal in the instrument
    ("ME1", "expect", ("BLKBASE, BLKSTRIDE = 0x94D430, 0x20BC", "BLKBASE, BLKSTRIDE = 0x94D430, 0x20B0"),
     {"G1", "G3"}),                                                     # wrong block stride
    ("ME2", "expect", ("ENERGY_OFF, SPEND_OFF, DIFF_OFF = 0x220, 0x300, 0x8",
                       "ENERGY_OFF, SPEND_OFF, DIFF_OFF = 0x224, 0x300, 0x8"),
     {"G1", "G2"}),                                                     # ENERGY off another field
    ("ME3", "expect", ("BASEMAP, BASE_STRIDE = 0x95DA9C, 304", "BASEMAP, BASE_STRIDE = 0x95DA98, 304"),
     {"G4", "G7", "RIVAL2"}),                                          # wrong facility-map base (RIVAL2's death
                                                                        # condition reads BASEMAP too - measured)
    ("ME4", "expect", ("QUEUE_HEAD_OFF = 0x50", "QUEUE_HEAD_OFF = 0x54"), {"G2", "G7"}),  # not the queue head
    ("ME5", "expect", ("AI_DIFF = 3", "AI_DIFF = 4"), {"G3"}),          # AI difficulty authored wrong
    ("ME6", "expect", ("STR_LABEL, STR_ICON = 0x68D24C, 0x68D238", "STR_LABEL, STR_ICON = 0x68D258, 0x68D238"),
     {"G6"}),                                                           # label VA pinned to the wrong string
]

GATES = {f"G{i}" for i in range(1, 8)} | {"RIVAL1", "RIVAL2", "RIVAL3"}


def run_instrument(patch=None, src_copy=None):
    env = dict(os.environ)
    if patch is not None:
        env["M334_PATCH"] = patch
    path = INSTR
    if src_copy is not None:
        os.makedirs(SCRATCH, exist_ok=True)
        path = os.path.join(SCRATCH, "m334_mutate_copy.py")
        with open(path, "w") as f:
            f.write(src_copy)
    p = subprocess.run([sys.executable, "-u", path], capture_output=True, text=True,
                       env=env, timeout=600, cwd=ROOT)
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
    print("baseline: PASS, digest=%s" % re.search(r"digest ([0-9a-f]{16})", out).group(1))

    rows = []
    allok = True
    npass = 0
    if selftest:
        _, mout = run_instrument(patch=MUTANTS[0][2])
        obs = observed_reds(mout)
        if obs != {"G1"}:
            print("selftest precondition broken: MU1 observed %s" % sorted(obs))
            return 1
        st = [("ST1 empty declared", verdict(set(), obs, False, True)),
              ("ST2 superset declared", verdict({"G1", "G7"}, obs, False, True)),
              ("ST3 partial declared", verdict({"G1"}, {"G1", "G2"}, False, True)),
              ("ST4 crash class", verdict({"G1"}, obs, True, True)),
              ("ST5 no-contact class", verdict({"G1"}, obs, False, False))]
        rcn, outn = run_instrument(patch="4f4802|mov esi,0x1")   # the IDENTICAL instruction
        obsn = observed_reds(outn)
        contactn = "patches applied: 1/1" in outn
        st.append(("ST6 real NO-OP mutant", verdict({"G1"}, obsn, "Traceback" in outn, contactn)))
        nok = 0
        for name, (ok, why) in st:
            rejected = not ok
            print("%s %s (%s)" % ("PASS" if rejected else "FAIL", name, why))
            nok += rejected
            rows.append("ST %s %s" % (name, why))
        print("%s selftest: %d/%d" % ("PASS" if nok == len(st) else "FAIL", nok, len(st)))
        return 0 if nok == len(st) else 1

    covered = set()
    for mid, kind, spec, declared in MUTANTS:
        if kind == "code":
            rcx, outx = run_instrument(patch=spec)
            contact = "patches applied: 1/1" in outx
        else:
            src = open(INSTR).read()
            if src.count(spec[0]) != 1:
                rows.append("%s FAIL expect literal not unique (%d)" % (mid, src.count(spec[0])))
                allok = False
                continue
            rcx, outx = run_instrument(src_copy=src.replace(spec[0], spec[1]))
            contact = "patches applied: 0/0" in outx   # the copy ran, unpatched
        obs = observed_reds(outx)
        ok, why = verdict(declared, obs, "Traceback" in outx, contact)
        print("%s %s declared=%s observed=%s (%s)" % ("PASS" if ok else "FAIL", mid,
                                                      sorted(declared), sorted(obs), why))
        rows.append("%s %s %s %s" % (mid, sorted(declared), sorted(obs), why))
        allok = allok and ok
        npass += ok
        covered |= obs

    uncov = GATES - covered
    if uncov:
        print("FAIL COVERAGE: no mutant reddens %s" % sorted(uncov))
        allok = False
    else:
        print("coverage: every gate and rival reddened by >=1 mutant (%d items)" % len(GATES))
    print("digest(harness)=%s" % hashlib.sha256("\n".join(rows).encode()).hexdigest()[:16])
    print("%s HARNESS %d/%d" % ("PASS" if allok else "FAIL", npass, len(MUTANTS)))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
