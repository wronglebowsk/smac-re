#!/usr/bin/env python3
"""scripts/b26_mutate.py - mutation harness for rung B26's instrument
(sim/composedsave.py).

Law (NEXT_PROMPT trap 24): every gate needs a NAMED mutant that reddens it, the sets are
MEASURED and then declared, and the fixes get mutated too. Each mutation re-creates one
defect by anchor->replacement in a sibling module inside sim/ and runs it in a FRESH
subprocess, relayed through the module's own acceptance() exactly as
`python3 -u -m sim.selftest --b26` does - so the harness measures the same text the
acceptance command prints.

FOUR OUTCOMES: (1) measured set == declared -> OK; (2) differs -> BAD (authored, not
measured); (3) reddens NOTHING -> BAD, a NO-OP mutant, unless declared NOOP; (4) CRASH ->
BAD unless declared and message-matched.

GATE IDS ARE STRUCTURAL, NOT SCRAPED (the #319 review's f.7 law, kept from B25): the child
prints one `BADGATE <id>` line per failed row, taken from the row's own name field as
gates() emitted it; the parent scores the SET and refuses the run if the count ever
disagrees with the child's own BADCOUNT, with NGATES, or with the gate ids of the
UNMUTATED shipped module. No regex reads a failure message.

AUTHORED-THEN-MEASURED, the honest way round: the first pass of this file declared the
sets below from the mechanism each mutant attacks; every set printed here was then
CONFIRMED by the harness run whose output is evidence/b26_mutate.txt, and the two entries
whose measured set differed from the prose guess were corrected from the measurement,
not from the guess.
"""
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(REPO, "sim")
CM = os.path.join(SIM, "composedsave.py")
sys.path.insert(0, REPO)
from sim import composedsave as scs  # noqa: E402  (the shipped, unmutated instrument)

# (id, description, target, anchor, replacement, measured-and-declared red gates | "NOOP")
MUTANTS = [
    ("MU1", "the falsifier's hand never fires (no image-only poison)", CM,
     "                img, edits = _poison_hand(img, parent_idx)",
     "                img, edits = img, []",
     {"G3", "G6", "G8", "G9"}),
    ("MU2", "the resumed run keeps the MODEL's tiles through the load (BOTH paths)", CM,
     "unused - see the pair list",
     [("                model = _tiles(im)\n",
       "                pass   # the load leaves the model's tiles alone\n"),
      ("            m = socev._Mover(i, start[i][0], start[i][1], budget, wrap=True)",
       "            m = socev._Mover(i, model[i][0], model[i][1], budget, wrap=True)")],
     # MEASURED {G6,G9}, and NOT G4 nor G8 - both honestly so. G4: in the unpoisoned run
     # the model and the container hold the same tiles, so confluence cannot see this
     # defect at all. G8: the 'model' rival still differs from the container run because
     # it never re-bases its WRITER (base_im stays the save) - the tile channel is not the
     # only thing keeping the rival a rival. EACH HALF ALONE measured 0 gates (NO-OP
     # twice), which is why this mutant is a pair: the reload law has two enforcers and
     # only breaking both proves the gate is watching the right thing.
     {"G6", "G9"}),
    ("MU3", "the writer is never rebased onto the loaded container (composes from the save)",
     CM,
     """                arrivals = []
                base_im = im""",
     """                arrivals = []
                base_im = sv0""",
     # MEASURED {G4,G5,G6,G9}: G5 too, because the split branch composes from the same
     # base_im and its pinned divergence counts move with it.
     {"G4", "G5", "G6", "G9"}),
    ("MU4", "the mover's tiles never reach the writer (positions stay model-only)", CM,
     """    mv = {i: tuple(model[i]) for i in model
          if i < base_im.n_units and list(model[i]) != bt.get(i, [None])}""",
     "    mv = {}",
     # MEASURED {G4,G5,G6,G9}: G4 because the APPENDED arrivals still carry the model's
     # tiles (fix6) while the rebased container's records stop moving - the two write
     # paths diverge, which is exactly what confluence is there to catch.
     {"G4", "G5", "G6", "G9"}),
    ("MU5", "the 'model' rival is fed the container at the boundary too (rival coincidence)",
     CM,
     '            elif mode == "model":',
     "            elif False:",
     {"G8"}),
    ("MU6", "the arrival's parent tile is read from the ORIGINAL save, not the load", CM,
     """                pread = cont.data[cont.bases_off + sosave.BASE_LEN * parent_idx:
                                  cont.bases_off + sosave.BASE_LEN * (parent_idx + 1)]""",
     """                _sv0 = soct.parse_image(sv0.data)
                pread = _sv0.data[_sv0.bases_off + sosave.BASE_LEN * parent_idx:
                                  _sv0.bases_off + sosave.BASE_LEN * (parent_idx + 1)]""",
     # MEASURED {G6,G9}: the base channel of the falsifier stops reaching the arrival.
     # (The first anchor here - "locate the parent BY TILE" - was a NO-OP and said so:
     # a tile search that falls back to the same index is not a rival.)
     {"G6", "G9"}),
    ("MU7", "the recorded stream's DESTROY never runs (op fidelity is decoration)", CM,
     "        landed = led.destroy(len(led) - 1) is not None   # B13's last-slot law",
     "        landed = True   # the destroy is skipped",
     {"G2", "G9"}),
    ("MU8", "the mid-gesture split refreshes the budget for BOTH branches (control collapses)",
     CM,
     '            sp2 = dict(spent) if mode == "budgetcarry" else {}',
     '            sp2 = dict(spent) if mode in ("budgetcarry", "split") else {}',
     {"G5"}),
    ("MU9", "the mid-gesture reload leaves the writer based on the pre-load container", CM,
     "            base_im, model, led, arrivals = imn, md, led2, []",
     "            base_im, model, led, arrivals = base_im, md, led2, []",
     # MEASURED {G5}: the split run's second write loses the arrivals' moves, so the
     # pinned divergence counts (69 units / 69 bytes) stop matching. The first anchor
     # here (the split's TILE reload) was a NO-OP: at that point the model and the
     # container hold the same tiles, so nothing printed can tell them apart - declared
     # here rather than hidden, because it is the split branch's decoration-free half.
     {"G5"}),
    ("MU10", "a write clobbers an UNMODELED byte (a unit's flag word)", CM,
     """    im_w = soct.parse_image(nxt)
    u_lo, u_hi = im_w.units_off, im_w.bases_off""",
     """    _mut = bytearray(nxt)
    _mut[soct.parse_image(nxt).units_off + 4] = 0x20     # not a modeled field
    nxt = bytes(_mut)
    im_w = soct.parse_image(nxt)
    u_lo, u_hi = im_w.units_off, im_w.bases_off""",
     {"G7", "G9"}),
    ("MU11", "the resumed engine is not read from the header (year invented, not carried)", CM,
     "                eng = soturn.Engine(im.year, human=im.own_player)",
     "                eng = soturn.Engine(im.year + 1, human=im.own_player)",
     # MEASURED {G4,G5,G6,G9}: the invented year reaches the header, so the control run
     # (which rebuilds the same way) diverges from the uninterrupted one as well.
     {"G4", "G5", "G6", "G9"}),
    ("MU12", "the ACCEPT anchor stops covering the printed rows (the pin becomes decoration)",
     CM,
     '    names = ",".join(sorted(runs))',
     '    names = ""',
     {"G9"}),
    ("MU13", "the identity round-trip is asserted instead of computed", CM,
     '        "identity": sow.build_image(sv) == sv.data, "sv": sv}',
     '        "identity": sow.build_image(sv, year=sv.year + 1) == sv.data, "sv": sv}',
     {"G2"}),
    ("MU14", "the smuggle rival is handed the edited container (blindness not enforced)", CM,
     '            if mode not in ("smuggle", "late") and poison and parent_idx is not None:',
     '            if mode not in ("late",) and poison and parent_idx is not None:',
     # MEASURED {G6} ONLY, and the reason is a finding: handing smuggle the edited
     # container does collapse its TRAJECTORY onto the honest run's (which is what G6
     # detects - smuggle must still reproduce the CLEAN run), but G8 stays green because
     # smuggle's signature also carries the object-reuse channel (its ledger/engine are the
     # pre-boundary ones), so it remains a distinct rival. The first version of this mutant
     # gave the smuggle branch the LOAD instead and measured 0 red: rebuilding from an
     # UNPOISONED image reproduces the clean run exactly, so that half was decoration. It
     # is the poison hand-off, not the rebuild, that keeps the two runs apart.
     {"G6"}),
]


def shipped_gate_ids():
    """The gate ids of the UNMUTATED shipped module, read from gates() itself. Every
    mutant's measured set is scored against these; a name that is not one of them is a
    harness defect."""
    mm = scs.measure(scs.DEFAULT_SAV, scs.DEFAULT_MAP, scs.DEFAULT_LOG, scs.DEFAULT_TRACE)
    return [name.split()[0] for name, _ in scs.gates(mm)]


def run_mutant(mid, path, anchor, repl, tag):
    """`repl` is either a string (one anchor) or a LIST of (anchor, replacement) pairs
    applied in order. MU2 needs the list form, and that is a finding rather than a
    convenience: the unit-channel reload law is enforced by TWO redundant paths (the press
    starts from the freshly-parsed container AND the model is refreshed from it), so a
    one-sided mutation measures 0 gates. A mutant that must break both is the honest
    statement of what the gate actually protects."""
    src = open(path, encoding="utf-8").read()
    pairs = repl if isinstance(repl, list) else [(anchor, repl)]
    for a, _r in pairs:
        if src.count(a) != 1:
            return None, "ANCHOR NOT UNIQUE (%d matches): %r" % (src.count(a), a[:48])
    for a, r in pairs:
        src = src.replace(a, r, 1)
    name = "_b26mut_%s%s.py" % (mid.lower(), tag)
    out = os.path.join(SIM, name)
    open(out, "w", encoding="utf-8").write(src)
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from sim import %s as m\n"
        "mm = m.measure(m.DEFAULT_SAV, m.DEFAULT_MAP, m.DEFAULT_LOG, m.DEFAULT_TRACE)\n"
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
    """Run each mutant and score it against its declared effect. Shared by the plain run
    and --selftest, so a selftest that passes cannot be passing on different logic."""
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
        print("%-6s %-54s declared=%-22s measured=%-20s %s  (%s)"
              % (mid, desc[:54], want_s, got_s, "OK" if ok else "BAD", info))
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
    ("MU5", {"G6", "G8"}, "an added gate MU5 does not actually red"),
    ("MU3", {"G6", "G9"}, "a subset: MU3 also breaks confluence and the harness must say so"),
    ("MU12", {"G6"}, "a gate MU12 does not red: it moves only the printed anchor"),
    ("MU8", {"G5", "G9"}, "an added gate: the container rows never move for MU8"),
]


def selftest(tag):
    """The harness itself must reject a wrong declaration - otherwise a green harness run
    says nothing about whether the declared sets are right."""
    by_id = {m[0]: m for m in MUTANTS}
    todo = []
    for mid, decl, why in SELFTEST:
        m = list(by_id[mid])
        m[5] = decl
        m[1] = "%s [SELFTEST: %s]" % (m[1][:30], why)
        todo.append(tuple(m))
    print("== B26 harness self-test: %d PERTURBED declarations, every one must be REJECTED =="
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
    print("== B26 mutation harness: %d mutants (each must match its declared effect: an "
          "EXACT gate set, a declared message-matched CRASH, or a declared NO-OP) =="
          % len(todo))
    print("-- harness %s --" % time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    fails = evaluate(todo, tag, "harness")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
