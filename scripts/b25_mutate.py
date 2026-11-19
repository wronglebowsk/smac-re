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

GATE IDS ARE STRUCTURAL, NOT SCRAPED (#319 review, f.7). The child prints one `BADGATE <id>`
line per failed row, taken from the row's own name field as gates() emitted it; the parent
scores the SET of those ids and refuses the run if their count ever disagrees with the child's
own BADCOUNT, with NGATES, or with the gate ids of the UNMUTATED shipped module (imported
here, measured once). No regex reads a failure message.

Each mutant is written as a sibling module inside sim/ and relayed through the module's own
acceptance() exactly as `python3 -u -m sim.selftest --b25` does, so the harness measures the
same text the acceptance command prints.

WHY G9 APPEARS IN MOST SETS (re-measured at harness 1.1, and the answer to #319 review f.1):
G9 now PINS the printed ACCEPT anchor to a literal, so any mutation that moves a single measured
row reddens it too - that is the pin doing its job, not padding. The set that proves the pin is
load-bearing on its own is MU9: a labels-only edit that changes no tile, no count and no rival,
and reddens G9 and nothing else.
"""
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(REPO, "sim")
CM = os.path.join(SIM, "composedmove.py")
sys.path.insert(0, REPO)
from sim import composedmove as somv  # noqa: E402  (the shipped, unmutated instrument)

# (id, description, target, anchor, replacement, declared red gates | "NOOP")
MUTANTS = [
    ("MU1", "the falsifier never fires (no image-only poison)", CM,
     """        if poison and r == POISON_ROUND:""",
     """        if False and r == POISON_ROUND:""",
     {"G6", "G8", "G9"}),
    ("MU2", "the rung reads its start tiles from the MODEL (B7's shape)", CM,
     """            start = {i: list(head[i]) for i in model}
            src = "image-at-round-head\"""",
     """            start = {i: list(model[i]) for i in model}
            src = "image-at-round-head\"""",
     {"G4", "G6", "G8", "G9"}),
    ("MU3", "the container is never refreshed between rounds (composes from the save)", CM,
     """        im_head = im_w""",
     """        im_head = im_head""",
     # MEASURED {G2,G4,G5,G6,G8,G9} at harness 1.1: G2 (the write's footprint stops matching the
     # tiles it claims to write, because the base image is the save again), G4 (now that the
     # read-back is compared against a FRESH DECODE of the bytes actually consumed, a stale cache
     # is visible - this is the mutant that gives #319 review f.4's fix its teeth), G5/G6/G8 (the
     # pinned coordinate numbers and the falsifier's bite), G9 (the rows themselves moved).
     {"G2", "G4", "G5", "G6", "G8", "G9"}),
    ("MU4", "the mover's tiles never reach the writer (positions stay model-only)", CM,
     """        mv = None if mode == "nowrite" else {i: tuple(model[i]) for i in model""",
     """        mv = None if True else {i: tuple(model[i]) for i in model""",
     # MEASURED {G2,G3,G4,G5,G6,G8,G9} - and G7 stays GREEN, honestly: the one unit-array byte
     # that still differs from the save is the FALSIFIER's own write, and G7 counts modeled
     # spans, not who wrote them.
     {"G2", "G3", "G4", "G5", "G6", "G8", "G9"}),
    ("MU5", "the writer no longer models the container's turn fields (year frozen)", CM,
     """        img_next = sow.build_image(im_head, year=eng.year, cur=eng.cur, tf=eng.tf, moves=mv,""",
     """        img_next = sow.build_image(im_head, moves=mv,""",
     {"G2", "G8", "G9"}),
    ("MU6", "the MP budget is 3, not 6 (one accepted press per round)", CM,
     """    budget = sounits.STEP_MP if mode == "budget3" else sounits.MP_PER_TURN""",
     """    budget = sounits.STEP_MP""",
     {"G1", "G4", "G5", "G8", "G9"}),
    ("MU7", "the falsifier poisons the MODEL instead of the CONTAINER", CM,
     """            mut = bytearray(img)
            struct.pack_into("<H", mut, off, POISON_X)""",
     """            mut = bytearray(img)
            model[POISON_UNIT] = [POISON_X, model[POISON_UNIT][1]]""",
     {"G6", "G8", "G9"}),
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
     # ... and this is the mutant that proves the DECODER CROSS-CHECK is read (#319 review f.5):
     # with the tile test moved onto the map file's grid it no longer reproduces the sets
     # sim/save._unit_ok rejects, so the round-by-round agreement clause in G5 goes red.
     {"G5", "G8"}),
    ("MU13", "B7's cross-check counts tiles outside the MAP FILE's grid, not the container's", CM,
     """    b7_out = sorted(int(i) for i, v in b7_final.items()
                    if v[0] >= sv0.width or v[1] >= sv0.height)""",
     """    b7_out = sorted(int(i) for i, v in b7_final.items()
                    if v[0] >= 80 or v[1] >= 80)""",
     # MEASURED {G5}: B7 wrapped x by the map file's own width, so judged against THAT grid it
     # leaves nothing outside - the "B7 ended outside the container" finding is carried by the
     # container's grid, and this is the mutant that says so.
     {"G5"}),
    ("MU10", "G4's read-back compares against the model instead of the fresh decode", CM,
     """            readback.append(1 if start[i] == recheck[i] else 0)""",
     """            readback.append(1 if start[i] == model[i] else 0)""",
     # MEASURED {G4, G8}: the falsifier's bite disappears from G4 too, so the rung's own row is
     # no longer distinguishable from a model-fed one - G8's control clause catches it as well.
     {"G4", "G8"}),
    ("MU14", "the previous round's WRITE is forgotten: every read carries the SAVE again", CM,
     """        img_written = img""",
     """        img_written = sv0.data""",
     # THE CARRY LAW'S OWN MUTANT (#319 review f.10): the round's start tiles still match a
     # fresh decode of what is being read, so every tile-level claim stays green - only the
     # byte-level law (table H: the head differs from the previous write by exactly the
     # falsifier's own bytes) sees that the run stopped carrying its own writes.
     {"G4"}),
    # ---- declared NO-OPs: measured decoration, stated as such -------------------------------
    ("MU11", "the write-side out-of-grid arm counts each (round,unit) twice (multiset)", CM,
     """            if wt[i][0] >= W_cont or wt[i][1] >= H_cont:
                out_written.append((r, i))""",
     """            if wt[i][0] >= W_cont or wt[i][1] >= H_cont:
                out_written.append((r, i))
                out_written.append((r, i))""",
     "NOOP"),
    ("MU9", "labels only: the read source's NAME changes, no tile and no count does", CM,
     """            src = "image-at-round-head\"""",
     """            src = "container-at-head\"""",
     # NOT a NO-OP any more, and that is the point of #319 review f.1: the label feeds the
     # measured rows, so the printed ACCEPT anchor moves and the PINNED anchor in G9 reddens.
     # Before this round's fix, this same edit changed a number the docs cite and NO gate read.
     {"G9"}),
    ("MU15", "the read-back compares the cached parser object with itself (the old shape)", CM,
     """        recheck = _tiles(soct.parse_image(head_bytes))""",
     """        recheck = head""",
     # DECLARED DECORATION, stated in the law's own vocabulary: with the container refreshed
     # every round (the shipped shape) a self-comparison measures nothing, and no gate notices
     # it. What makes f.4's fix load-bearing is MU3 - a stale cache is the state a fresh decode
     # can see and a self-comparison cannot.
     "NOOP"),
    ("MU16", "found_units is COPIED from the parser instead of recomputed from _unit_ok", CM,
     """        found_pred = 0
        while sosave._unit_ok(img, im_w.bases_off - sosave.UNIT_LEN * (found_pred + 1),
                              W_cont, H_cont):
            found_pred += 1""",
     """        found_pred = im_w.found_units""",
     # DECLARED DECORATION ON THIS SAVE: the recomputation reproduces the parser's number in
     # 44/44 probes, so replacing it with a copy changes nothing printed. The independent signal
     # that carries G5 is the record-SET comparison, and MU12/MU13 are the mutants that name it.
     "NOOP"),
]


def shipped_gate_ids():
    """The gate ids of the UNMUTATED shipped module, read from gates() itself. Every mutant's
    measured set is scored against these; a name that is not one of them is a harness defect."""
    mm = somv.measure(somv.DEFAULT_SAV, somv.DEFAULT_MAP)
    return [name.split()[0] for name, _ in somv.gates(mm)]


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
        "for _nm, _ok in res:\n"
        "    if not _ok:\n"
        "        print('BADGATE', _nm.split()[0])\n"
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
    nbad = int([ln for ln in p.stdout.splitlines()
                if ln.startswith("BADCOUNT ")][0].split()[1])
    ng = int([ln for ln in p.stdout.splitlines()
              if ln.startswith("NGATES ")][0].split()[1])
    # STRUCTURAL: one line per failed row, id taken from the row's own name field. No regex
    # reads a message; the sets are only accepted if they agree with the child's own counts.
    ids = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("BADGATE ")]
    if len(ids) != nbad:
        return None, "STRUCTURAL: %d BADGATE lines but BADCOUNT %d" % (len(ids), nbad)
    if len(set(ids)) != len(ids):
        return None, "STRUCTURAL: duplicate gate ids in %s" % ids
    if ng != NGATES_EXPECT:
        return None, "STRUCTURAL: %d gates reported, shipped module has %d" % (ng,
                                                                                NGATES_EXPECT)
    unknown = [i for i in ids if i not in VALID_IDS]
    if unknown:
        return None, "STRUCTURAL: gate ids not in the shipped gates(): %s" % unknown
    return set(ids), "%d/%d gates red" % (nbad, ng)


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
    ("MU14", {"G4", "G8"}, "an added gate: only the byte-level carry law sees MU14"),
    ("MU9", {"G6"}, "a gate MU9 does not red: it moves the ACCEPT anchor, so only G9"),
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
    global VALID_IDS, NGATES_EXPECT
    args = sys.argv[1:]
    VALID_IDS = shipped_gate_ids()
    NGATES_EXPECT = len(VALID_IDS)
    print("shipped gates(): %d rows %s" % (NGATES_EXPECT, ",".join(VALID_IDS)))
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
