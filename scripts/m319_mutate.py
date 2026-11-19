#!/usr/bin/env python3
"""M319 mutation harness: every gate the census ships must BITE, or it is decoration
(TRAP 24 / the s290 claim->mutant law).

Two families, as in M315 #301:
  (1) SOURCE mutants (MU1..MU9) - rewrite one classifier/bound/window in
      scripts/m319_guard_hoist.py so a claim becomes false on the real bytes.
  (2) CODE mutants (MU10..MU13) - run the instrument against a REWRITTEN
      DISASSEMBLY (env M319_PATCH="addr|mn ops"): change the CODE the census reads,
      including one mutant that BUILDS the rival it is supposed to reject (a hoisted
      memo guard in a real caller).

Every mutant must redden EXACTLY its declared gate SET: a missing red is a decorative
assert, an extra red is an undeclared dependency. A crash is not a red. The baseline
must be green or the run refuses. Declared sets are MEASURED, never authored.

PASS 1 (evidence/m319_mutate_pass1.txt) ran with every set EMPTY, to MEASURE the sets;
it also measured MU6 as a CRASH (KeyError) and MU8 as reddening NOTHING. The instrument
then gained two span-mismatch guards (fail a gate, never crash) and this file's sets were
filled from PASS 2 (evidence/m319_mutate.txt), i.e. measured on the shipped instrument:
MU6 now reddens G4 and prints the skip instead of dying. MU8 is declared NO-OP: the
NO-OP sentinel is itself an assertion (rc==0 AND zero reddened gates), so it reddens the
harness if thunk-following ever becomes load-bearing - a tripwire, not a deleted test.

  python3 -u scripts/m319_mutate.py            # full sweep
  python3 -u scripts/m319_mutate.py --only MU9,MU10 --tag b
"""
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "scripts", "m319_guard_hoist.py")
src = open(SRC).read()
env0 = dict(os.environ, PYTHONPATH=os.path.join(REPO, "scripts"))
GATE_RX = re.compile(r"^FAIL (G?\d+|\w+)", re.M)

DECIDED = """                if r in decided:
                    continue        # nearest event already decided it
"""


class NoOp(object):
    """A MEASURED empty load set: the mutant must exit 0 and redden NOTHING.
    This is an assertion, not an exemption - any red under it is a harness failure."""

    def __init__(self, reason):
        self.reason = reason

    def __repr__(self):
        return "NO-OP(%s)" % self.reason


NOOP_THUNK = NoOp("thunk-following is inert on THIS image: all 9 call arrivals of the "
                  "unguarded owners resolve directly, so no gate's printed number moves")

SRC_MUT = [
    # sets below are PASS-2 MEASUREMENTS (evidence/m319_mutate.txt), not authored pins
    ("MU1_pair_reach_16", "PAIR_REACH = 17", "PAIR_REACH = 16",
     {"G1", "G7"}),
    ("MU2_wrong_second_callee", "REFRESH = (0x4E8D60, 0x4E78E0)",
     "REFRESH = (0x4E8D60, 0x4E78E1)", {"G1", "G3", "G4", "G7"}),
    ("MU3_store_regex_narrow", 'r"(DWORD PTR )?ds:0x68cbb4,"', 'r"ds:0x68cbb4,"',
     {"G1", "G2", "G3", "G4", "G5", "G7"}),
    ("MU4_ref_ignores_cmp", 'return "0x68cbb4" in ops.strip() and not is_store(mn, ops)',
     'return "0x68cbb4" in ops.strip() and mn == "mov" and not is_store(mn, ops)',
     {"G2", "G5"}),
    ("MU5_copy_walk_bug", DECIDED, "", {"G1", "G4", "G7"}),
    # pass 1 CRASHED here (KeyError); with the instrument's span guards it is a red GATE.
    ("MU6_owner_unbounded", 'return n if s <= a < s + sz else "UNRANGED:%s" % n', "return n",
     {"G4"}),
    ("MU7_pair_window_tight", "order[js:js + 6]", "order[js:js + 2]", {"G1", "G7"}),
    ("MU8_thunk_resolve_off", "for _ in range(3):\n            j = ins.get(t)",
     "for _ in range(0):\n            j = ins.get(t)", NOOP_THUNK),
    ("MU9_classifier_blind_to_copy",
     '        if any(E.reg_norm(p) in live_copy(fs, BB4) for p in parts):\n'
     '            return "memo-copy|%s" % o[:34]\n', "", {"G7"}),
]
CODE_MUT = [
    # the RIVAL made real: a caller of an unguarded owner tests the MEMO before the call.
    ("MU10_hoisted_guard_built", "0x5206ce|cmp ecx,DWORD PTR ds:0x68cbb4",
     {"G2", "G3", "G5", "G6"}),
    # a guard that no longer consults the memo: the direct cmp at 0x4eb6bf compares edx/eax.
    ("MU11_direct_guard_blinded", "0x4eb6bf|cmp edx,eax",
     {"G1", "G2", "G3", "G4", "G5", "G7"}),
    # the only direct call to FUN_004f5a70 is erased: the caller census and the dead-code rival move.
    ("MU12_call_erased", "0x5206d3|nop", {"G3", "G4"}),
    # the guard's je stops skipping the store: it jumps ONTO it.
    ("MU13_guard_je_no_skip", "0x4f5c48|je 0x4f5c4a", {"G1"}),
]


def run(text, patch=None, tag=""):
    fd, path = tempfile.mkstemp(suffix="_m319mut%s.py" % tag, dir=os.path.join(REPO, "scripts"))
    os.write(fd, text.encode())
    os.close(fd)
    env = dict(env0, M319_PATCH=patch) if patch else env0
    try:
        p = subprocess.run([sys.executable, "-u", path], capture_output=True,
                           text=True, env=env, cwd=REPO, timeout=900)
        return p.returncode, p.stdout + p.stderr
    finally:
        os.unlink(path)


def gates(out):
    return sorted(set(GATE_RX.findall(out)))


def verdict(want, rc, fails):
    """The ONE scoring rule, shared by the sweep and the selftest, so the selftest
    perturbs the REAL verdict and not a paraphrase of it."""
    if isinstance(want, NoOp):
        return rc == 0 and not fails
    return bool(want) and rc != 0 and set(fails) == set(want)


def find(table, mid):
    for t in table:
        if t[0] == mid:
            return t
    raise KeyError(mid)


def selftest():
    """THE HARNESS ITSELF MUST BE ABLE TO FAIL (TRAP 24 applies to the harness too).
    Three PERTURBATIONS of an already-measured declared set must each be REJECTED by
    `verdict` - if any is accepted, the scoring rule is decorative:
      P1 declare an EMPTY set for a mutant that reddens G7  (the pass-1 state);
      P2 declare a SUPERSET for a mutant whose real set is {G1,G7};
      P3 declare a GATE for the measured NO-OP (thunk-following), i.e. claim a bite
         this image does not produce.
    Only the DECLARATION is perturbed - the mutants and the bytes are untouched."""
    caught = 0
    for mid, perturbed, note in (
            ("MU9_classifier_blind_to_copy", set(), "declare-EMPTY"),
            ("MU1_pair_reach_16", {"G1", "G7", "G2"}, "declare-SUPERSET"),
            ("MU8_thunk_resolve_off", {"G1"}, "gate-DECLARE the NO-OP")):
        t = find(SRC_MUT, mid)
        rc, out = run(src.replace(t[1], t[2]))
        f = gates(out)
        accepted = verdict(perturbed, rc, f)
        print("%s %s for %s: real=%s perturbed=%s measured_gates=%s accepted=%s"
              % ("OK  " if not accepted else "BAD ", note, mid,
                 repr(t[3]) if isinstance(t[3], NoOp) else sorted(t[3]),
                 sorted(perturbed), f, accepted))
        caught += 0 if accepted else 1
    print("== m319-mutate selftest: %d/3 declared-set perturbations reddened the harness =="
          % caught)
    return 0 if caught == 3 else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    only = []
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else ""
    rc, out = run(src, tag=tag)
    if rc != 0:
        print("BASELINE NOT GREEN - refusing:\n" + out[-1200:])
        return 2
    print("baseline green:", out.strip().splitlines()[-1])
    bad = bad_noop = 0
    for mid, old, new, want in SRC_MUT:
        if only and not any(o in mid for o in only):
            continue
        n = src.count(old)
        if n != 1:
            print("BAD  %s anchor count %d (not 1) - HARNESS BUG" % (mid, n))
            bad += 1
            continue
        rc, out = run(src.replace(old, new), tag=tag)
        fails = gates(out)
        if "Traceback" in out:
            print("BAD  %s CRASHED - rejected per law (a crash is not a red gate)" % mid)
            print("     measured=%s" % fails)
            bad += 1
            continue
        want_txt = repr(want) if isinstance(want, NoOp) else (sorted(want) or "(unset)")
        hit = verdict(want, rc, fails)
        print("%s %s measured_gates=%s declared=%s"
              % ("OK  " if hit else "BAD ", mid, fails, want_txt))
        if isinstance(want, NoOp):
            bad_noop += 0 if hit else 1
        elif not hit:
            bad += 1
    for mid, patch, want in CODE_MUT:
        if only and not any(o in mid for o in only):
            continue
        rc, out = run(src, patch=patch, tag=tag)
        fails = gates(out)
        if "Traceback" in out:
            print("BAD  %s CRASHED - rejected per law" % mid)
            bad += 1
            continue
        if "M319_PATCH" in out and "patches" not in out:
            print("BAD  %s patch applied to nothing - vacuous" % mid)
            bad += 1
            continue
        want_txt = repr(want) if isinstance(want, NoOp) else (sorted(want) or "(unset)")
        hit = verdict(want, rc, fails)
        print("%s %s [%s] measured_gates=%s declared=%s"
              % ("OK  " if hit else "BAD ", mid, patch, fails, want_txt))
        if isinstance(want, NoOp):
            bad_noop += 0 if hit else 1
        else:
            bad += 0 if hit else 1
    noop_total = sum(1 for m in SRC_MUT + CODE_MUT if isinstance(m[-1], NoOp))
    print("== m319-mutate: %d/%d scored mutants reddened EXACTLY their declared gate sets "
          "+ %d/%d declared NO-OP held green (%d source + %d code total) =="
          % (len(SRC_MUT) + len(CODE_MUT) - noop_total - bad,
             len(SRC_MUT) + len(CODE_MUT) - noop_total,
             noop_total - bad_noop, noop_total, len(SRC_MUT), len(CODE_MUT)))
    return 0 if bad + bad_noop == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
