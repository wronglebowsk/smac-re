#!/usr/bin/env python3
"""scripts/b25_mutate.py - mutation harness for rung B25's instrument (sim/composedmove.py).

Law (NEXT_PROMPT trap 24): after a gate is repaired, run a harness that re-creates each
defect by anchor->replacement in a FRESH subprocess and exits non-zero unless EVERY mutation
reddens exactly its declared gate SET. A mutation must falsify a MEASURED fact (never a dict
entry an assert reads whole), and the sets are MEASURED - the first pass of this file declared
sets from prose and they were wrong, exactly as B24's did.

FOUR OUTCOMES: (1) measured set == declared -> OK; (2) differs -> BAD (authored, not
measured); (3) reddens NOTHING -> BAD, a NO-OP mutant, unless declared NOOP (a declared
NO-OP is not scored and says "this half is decoration"); (4) CRASH -> BAD unless declared and
message-matched.

Each mutant is written as a sibling module inside sim/ and relayed through the module's own
acceptance() exactly as `python3 -u -m sim.selftest --b25` does, so the harness measures the
same text the acceptance command prints.
"""
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(REPO, "sim")
CM = os.path.join(SIM, "composedmove.py")

# (id, description, target, anchor, replacement, declared red gates | "NOOP")
MUTANTS = [
    ("MU1", "the falsifier never fires (no image-only poison)", CM,
     """        if poison and r == POISON_ROUND:""",
     """        if False and r == POISON_ROUND:""",
     {"G6", "G8"}),
    ("MU2", "the rung reads its start tiles from the MODEL (B7's shape)", CM,
     """            start = {i: list(head[i]) for i in model}
            src = "image-at-round-head\"""",
     """            start = {i: list(model[i]) for i in model}
            src = "image-at-round-head\"""",
     {"G4", "G6", "G8"}),
    ("MU3", "the container is never refreshed between rounds (composes from the save)", CM,
     """        im_head = im_w""",
     """        im_head = im_head""",
     # MEASURED {G2,G6,G8}: G2 reddens first (the write's footprint stops matching the tiles it
     # claims to write, because the base image is the save again), G6's shift degenerates, G8's
     # "rung != its rivals" clause sees the rung collapse into nowrite's footprint.
     {"G2", "G6", "G8"}),
    ("MU4", "the mover's tiles never reach the writer (positions stay model-only)", CM,
     """        mv = None if mode == "nowrite" else {i: tuple(model[i]) for i in model""",
     """        mv = None if True else {i: tuple(model[i]) for i in model""",
     # MEASURED {G2,G3,G4,G5,G6,G8} - and G7 stays GREEN, honestly: the one unit-array byte that
     # still differs from the save is the FALSIFIER's own write, and G7 counts modeled spans,
     # not who wrote them.
     {"G2", "G3", "G4", "G5", "G6", "G8"}),
    ("MU5", "the writer no longer models the container's turn fields (year frozen)", CM,
     """        img_next = sow.build_image(im_head, year=eng.year, cur=eng.cur, tf=eng.tf, moves=mv,""",
     """        img_next = sow.build_image(im_head, moves=mv,""",
     {"G2", "G8"}),
    ("MU6", "the MP budget is 3, not 6 (one accepted press per round)", CM,
     """    budget = sounits.STEP_MP if mode == "budget3" else sounits.MP_PER_TURN""",
     """    budget = sounits.STEP_MP""",
     {"G1", "G4", "G8"}),
    ("MU7", "the falsifier poisons the MODEL instead of the CONTAINER", CM,
     """            mut = bytearray(img)
            struct.pack_into("<H", mut, off, POISON_X)
            img = bytes(mut)""",
     """            mut = bytearray(img)
            model[POISON_UNIT] = [POISON_X, model[POISON_UNIT][1]]
            img = bytes(mut)""",
     {"G6", "G8"}),
    ("MU8", "the READ side's out-of-grid test uses the map file's grid, not the container's", CM,
     """            if start[i][0] >= W_cont or start[i][1] >= H_cont:
                out_head.append((r, i))""",
     """            if start[i][0] >= mp.width or start[i][1] >= mp.height:
                out_head.append((r, i))""",
     # MEASURED {G5, G8}: the write side still sees the rival's out-of-grid records, so only the
     # read-side claim ("the bad tile comes back") dies with this arm.
     {"G5", "G8"}),
    ("MU12", "the WRITE side's out-of-grid test uses the map file's grid", CM,
     """            if wt[i][0] >= W_cont or wt[i][1] >= H_cont:
                out_written.append((r, i))""",
     """            if wt[i][0] >= mp.width or wt[i][1] >= mp.height:
                out_written.append((r, i))""",
     {"G5", "G8"}),
    ("MU10", "G4's read-back compares against the model instead of the container head", CM,
     """            readback.append(1 if start[i] == head[i] else 0)""",
     """            readback.append(1 if start[i] == model[i] else 0)""",
     # MEASURED {G4, G8}: the falsifier's bite disappears from G4 too, so the rung's own row is
     # no longer distinguishable from a model-fed one - G8's control clause catches it as well.
     {"G4", "G8"}),
    ("MU11", "the write-side out-of-grid arm counts each (round,unit) twice (multiset)", CM,
     """            if wt[i][0] >= W_cont or wt[i][1] >= H_cont:
                out_written.append((r, i))""",
     """            if wt[i][0] >= W_cont or wt[i][1] >= H_cont:
                out_written.append((r, i))
                out_written.append((r, i))""",
     "NOOP"),
    ("MU9", "labels only: the read source's name changes, no measured value does", CM,
     """            src = "image-at-round-head\"""",
     """            src = "container-at-head\"""",
     "NOOP"),
]


def run_mutant(mid, path, anchor, repl, tag):
    src = open(path, encoding="utf-8").read()
    if src.count(anchor) != 1:
        return None, "ANCHOR NOT UNIQUE (%d matches)" % src.count(anchor)
    name = "_b25mut_%s%s.py" % (mid.lower(), tag)
    out = os.path.join(SIM, name)
    open(out, "w", encoding="utf-8").write(src.replace(anchor, repl))
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from sim import %s as m\n"
        "mm = m.measure(m.DEFAULT_SAV, m.DEFAULT_MAP)\n"
        "res = []\n"
        "m.acceptance(mm, res)\n"
        "print('BADCOUNT', sum(1 for r in res if not r[1]))\n"
        "print('NGATES', len(res))\n"
        "print('BAD:', ' | '.join(sorted({r[0].split()[0] for r in res if not r[1]})))\n"
        % (REPO, name[:-3]))
    try:
        p = subprocess.run([sys.executable, "-u", "-c", code], cwd=REPO,
                           capture_output=True, text=True, timeout=900)
    finally:
        for junk in (out, os.path.join(SIM, "__pycache__", name.replace(".py", ".pyc"))):
            try:
                os.unlink(junk)
            except OSError:
                pass
    if "BADCOUNT" not in p.stdout:
        last = (p.stderr.strip().splitlines() or ["(no stderr)"])[-1]
        return None, "CRASH: %s" % last[:110]
    nbad = int(re.search(r"BADCOUNT (\d+)", p.stdout).group(1))
    ng = int(re.search(r"NGATES (\d+)", p.stdout).group(1))
    bad = re.search(r"BAD: (.*)", p.stdout, re.S).group(1).strip()
    gates = set(re.findall(r"G\d+", bad)) - {""}
    return gates, "%d/%d gates red" % (nbad, ng)


def evaluate(todo, tag, label):
    """Run each mutant and score it against its declared effect. Shared by the plain run and
    --selftest, so a selftest that passes cannot be passing on different logic."""
    fails = []
    noop = []
    for mid, desc, path, anchor, repl, declared in todo:
        gates, info = run_mutant(mid, path, anchor, repl, tag)
        if declared == "NOOP":
            ok = gates is not None and not gates
            if ok:
                noop.append(mid)
                info += " [declared NO-OP: this half is decoration]"
        else:
            if gates is not None and not gates:
                info += " [NO-OP: reddened nothing]"
            ok = gates is not None and gates == declared and bool(gates)
        want_s = (",".join(sorted(declared)) if isinstance(declared, set) else declared)
        got_s = (",".join(sorted(gates)) if gates else ("nothing" if gates is not None
                                                        else "crash"))
        print("%-6s %-52s declared=%-26s measured=%-22s %s  (%s)"
              % (mid, desc[:52], want_s, got_s, "OK" if ok else "BAD", info))
        if not ok:
            fails.append(mid)
    scored = len(todo) - len(noop)
    print("== %s: %d/%d scored mutants matched their declared gate sets "
          "(+%d declared NO-OP: %s) ==" % (label, scored - len(fails), scored, len(noop),
                                           ",".join(noop) or "-"))
    if fails:
        print("BAD mutants (did NOT match their declared effect): %s" % ", ".join(fails))
    return fails


# (mutant id, perturbed declaration, why it must be rejected)
SELFTEST = [
    ("MU1", {"G6"}, "a dropped gate: the declared set must be EXACT, not a subset"),
    ("MU1", {"G1", "G6", "G8"}, "an added gate the mutant does not actually red"),
    ("MU4", {"G2"}, "a subset: MU4 reddens six gates and the harness must say so"),
    ("MU9", {"G6"}, "a REAL set on a decoration mutant: labels cannot redden anything"),
]


def selftest(tag):
    """The harness itself must reject a wrong declaration - otherwise a green harness run says
    nothing about whether the declared sets are right."""
    by_id = {m[0]: m for m in MUTANTS}
    todo = []
    for mid, decl, why in SELFTEST:
        m = list(by_id[mid])
        m[5] = decl
        m[1] = "%s [SELFTEST: %s]" % (m[1][:30], why)
        todo.append(tuple(m))
    print("== B25 harness self-test: %d PERTURBED declarations, every one must be REJECTED =="
          % len(todo))
    bad = evaluate(todo, tag, "selftest")
    if len(bad) != len(todo):
        print("SELFTEST BAD: %d/%d perturbations were accepted (should be %d rejected)"
              % (len(bad), len(todo), len(todo)))
        return 1
    print("selftest %d/%d perturbed declarations REJECTED" % (len(bad), len(todo)))
    return 0


def main():
    args = sys.argv[1:]
    if args and args[0] == "--list":
        for mid, desc, _p, _a, _r, declared in MUTANTS:
            print("%s\t%s\t%s" % (mid, ",".join(sorted(declared)) if isinstance(declared, set)
                                   else declared, desc))
        return 0
    want = {m[0] for m in MUTANTS}
    todo = MUTANTS
    if args and args[0] == "--only":
        want = set(args[1].split(","))
        todo = [m for m in MUTANTS if m[0] in want]
        if len(todo) != len(want):
            print("unknown mutant ids: %s" % (want - {m[0] for m in todo}))
            return 2
    tag = ""
    if "--tag" in args:
        tag = "_" + args[args.index("--tag") + 1]
    if "--selftest" in args:
        print("-- harness %s --" % time.strftime("%Y-%m-%d %H:%M:%S %Z"))
        return selftest(tag)
    print("== B25 mutation harness: %d mutants (each must match its declared effect: an EXACT "
          "gate set, a declared message-matched CRASH, or a declared NO-OP) ==" % len(todo))
    print("-- harness %s --" % time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    fails = evaluate(todo, tag, "harness")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
