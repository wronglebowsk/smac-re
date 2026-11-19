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
     # MEASURED {G10,G4,G5,G6,G9}: G5 too, because the split branch composes from the same
     # base_im and its pinned divergence counts move with it - and G10 (added for PR #328 F2)
     # because the writer's own record arithmetic moves with the rebase: not rebasing grows
     # the arrays from the SAVE's counts, so size_delta and the predicted growth part ways.
     # This set was CORRECTED FROM THE MEASUREMENT (sweep 1: G10 was not in the prose guess).
     {"G10", "G4", "G5", "G6", "G9"}),
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
     # MEASURED {G10,G2,G3,G9}, and the two extras are findings, not noise. G2: the
     # pre->post counts are now the LOG's own, so a skipped DESTROY moves them. G3 (NEW
     # since the field-wise ledger check, PR #328 F6): a ledger that never lost a base no
     # longer matches the image's base array record-for-record, so the carry census sees it
     # - the length-only check this replaced could not. G10: the arrays grow by a different
     # number of records than the round's size_delta says.
     {"G10", "G2", "G3", "G9"}),
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
    ("MU14", "the smuggler is put back behind the glass: never handed the poison "
     "(PR #328 F1's defect, reinstated)", CM,
     '            if mode != "late" and poison and parent_idx is not None:',
     '            if mode not in ("smuggle", "late") and poison and parent_idx is '
     'not None:',
     # Why this mutant exists: with the smuggler excluded from the falsifier's hand, the
     # old G6 "the smuggler is blind" was a tautology and no gate could see it. Re-adding
     # the exclusion must now redden the blindness half of G6 (SMUGGLE_SEES, the exposed
     # vs unexposed sha pair), which is exactly what the fix made measurable.
     {"G6"}),
    ("MU15", "the size law is decoration: the prediction uses a record size that is not "
     "sim/save.py's (PR #328 F2)", CM,
     '                    sosave.BASE_LEN * (r["n_bases_img"] - pb)',
     '                    (sosave.BASE_LEN + 1) * (r["n_bases_img"] - pb)',
     {"G10"}),
    ("MU16", "the owner census reads the FLAG word (+4), not the owner byte (+14) - the "
     "offset the first probe used (PR #328 F7)", CM,
     """        if (off + soprod.UNIT_OWNER < len(im.data)
                and im.data[off + soprod.UNIT_OWNER] == POISON_OWN4):""",
     """        if (off + 4 < len(im.data)
                and im.data[off + 4] == POISON_OWN4):""",
     {"G6"}),
    ("MU17", "the rebuilt ledger keeps the image's COUNT but not its ORDER - only the "
     "field-wise check pays (PR #328 F6)", CM,
     """                led = sobf.Ledger([{"own4": b["own4"], "fac": b["fac"], "x": b["x"],
                                    "y": b["y"]} for b in im.bases])""",
     """                led = sobf.Ledger([{"own4": b["own4"], "fac": b["fac"], "x": b["x"],
                                    "y": b["y"]} for b in im.bases][::-1])""",
     {"G3"}),
    ("MU18", "the mid-gesture reload's engine is built from an invented year, not the "
     "header's", CM,
     "            e2 = soturn.Engine(imn.year, human=imn.own_player)",
     "            e2 = soturn.Engine(imn.year + 1, human=imn.own_player)",
     {"G5"}),
    ("MU19", "the mid-gesture reload does NOT install the rebuilt engine (PR #328 F5's "
     "defect, reinstated)", CM,
     "            eng = e2               # the mid-gesture reload installs the rebuilt "
     "engine",
     "            pass                   # F5 reinstated: the pre-split engine stays in "
     "charge",
     # MEASURED 0 GATES - DECLARED NO-OP, and the number behind it is in the report: the
     # pre-split engine's state at the split is (3, 0, 2155) and the rebuilt one's is
     # (3, 0, 2155) too (table D, G5's engine clause). So the defect F5 reported was REAL
     # in the code and had NO magnitude on this fixture: the two engines coincide at that
     # point and advance identically afterwards. What is NOT decoration is the MEASUREMENT
     # - ENGINE_STATE pins both states and MU18 (rebuild the engine from an invented year)
     # reddens G5 alone - and the honest claim is "the install is verified to be a no-op
     # here", not "the install was fixed and therefore mattered".
     "NOOP"),
    ("MU20", "the SAVE-only refusal half counts every unit, so B25's equality is the "
     "arrival leak again (PR #328 F3)", CM,
     """                    if i < sv0.n_units:
                        ref_save += 1      # the SAVE-only half, for the B25 comparison""",
     "                    ref_save += 1    # every refusal, arrivals included",
     {"G1"}),
]


# ---------------------------------------------- PR #328 F9: the two entry points
ENTRY_CMDS = (("python3 -u -m sim.composedsave",
               [sys.executable, "-u", "-m", "sim.composedsave"]),
              ("python3 -u -m sim.selftest --b26",
               [sys.executable, "-u", "-m", "sim.selftest", "--b26"]))

# the relay is patched in a COPY of sim/ in a temp tree: --b26 prints one line the
# module does not, which is exactly the bug the identity check must not sleep through
# It is a MUTANT in every sense the claim-law asks of the word: a real defect re-created
# by anchor->replacement, with a declared effect, measured on every harness run. It is
# MU21, and it reddens the harness's own ENTRY-POINT IDENTITY check rather than an
# instrument gate, because the claim it protects is about the relay, not about the run.
RELAY_MU = "MU21"
RELAY_ANCHOR = "    m = scs.measure(sav_path, map_path, log_path, trace_path)\n"
RELAY_REPL = (RELAY_ANCHOR +
              '    print("THE RELAY IS NO LONGER ONLY A RELAY")\n')


def entrypoints():
    """F9 (PR #328): 'so --b26 and `python3 -m sim.composedsave` can never print
    different text' is cited as an ACCEPT fact, so the harness re-enters BOTH entry
    points and compares their stdout - and then PROVES THE COMPARISON BITES by running
    the second entry point again with its relay patched (in a throwaway copy of sim/,
    never in the shipped tree) and requiring the outputs to differ."""
    import hashlib
    import shutil
    import tempfile
    outs = []
    for label, cmd in ENTRY_CMDS:
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=900)
        dig = hashlib.sha256(p.stdout.encode()).hexdigest()[:16]
        print("%-34s rc=%d %4d lines sha256(stdout) %s"
              % (label, p.returncode, len(p.stdout.splitlines()), dig))
        outs.append(p.stdout)
    same = outs[0] == outs[1]
    tmp = tempfile.mkdtemp(prefix="b26_relay_")
    try:
        shutil.copytree(SIM, os.path.join(tmp, "sim"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        # symlink every top-level directory the shipped tree has except the sim/ we just
        # copied: sim/rules.py reads data/alpha.json, the run reads programs/ and evidence/,
        # and selftest imports scripts/decode_map - a temp tree that cannot run the entry
        # point is not a test, it is a crash dressed up as one
        for entry in sorted(os.listdir(REPO)):
            src = os.path.join(REPO, entry)
            dst = os.path.join(tmp, entry)
            if (entry == "sim" or entry.startswith(".") or not os.path.isdir(src)
                    or os.path.exists(dst)):
                continue
            os.symlink(src, dst)
        stp = os.path.join(tmp, "sim", "selftest.py")
        src = open(stp, encoding="utf-8").read()
        if src.count(RELAY_ANCHOR) != 1:
            print("BAD entry-point check: relay anchor matches %d times"
                  % src.count(RELAY_ANCHOR))
            return 1
        open(stp, "w", encoding="utf-8").write(src.replace(RELAY_ANCHOR, RELAY_REPL, 1))
        p = subprocess.run(ENTRY_CMDS[1][1], cwd=tmp, capture_output=True,
                           text=True, timeout=900)
        dig = hashlib.sha256(p.stdout.encode()).hexdigest()[:16]
        marker = p.stdout.count("THE RELAY IS NO LONGER ONLY A RELAY")
        print("%-34s rc=%d %4d lines sha256(stdout) %s relay-marker %dx"
              % ("  [relay patched in a temp tree]", p.returncode,
                 len(p.stdout.splitlines()), dig, marker))
        if p.returncode != 0:
            print("   stderr tail: %s"
                  % ((p.stderr.strip().splitlines() or ["(none)"])[-1][:120],))
        # A CRASH IS NOT A BITE: the patched relay has to finish, print the marker, and
        # still differ - otherwise the check would pass on a broken temp tree
        bites = (p.returncode == 0 and marker == 1 and p.stdout != outs[1]
                 and len(p.stdout.splitlines()) == len(outs[1].splitlines()) + 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("stdout identical across the two entry points: %s | the check BITES (a patched "
          "relay prints different text): %s" % (same, bites))
    print("%-6s %-52s declared=%-14s measured=%-14s %s"
          % (RELAY_MU, "the --b26 relay prints text the module does not (F9)",
             "IDENTITY", "IDENTITY" if bites else "nothing",
             "OK" if bites else "BAD"))
    if same and bites:
        print("PASS B26 ENTRY-POINT IDENTITY: 2/2 checks (%s scored)" % RELAY_MU)
        return 0
    print("FAIL B26 ENTRY-POINT IDENTITY")
    return 1


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
    ("MU15", {"G6"}, "a gate MU15 never touches: the size law is read by G10 alone"),
    ("MU20", {"G1", "G9"}, "an added gate: ref_save is deliberately OUT of SIGKEYS, so "
                           "the row digest cannot move for MU20"),
    ("MU16", {"G3"}, "the wrong gate entirely: the owner census is G6's, not the carry"),
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
    if args and args[0] == "--entrypoints":
        # the F9 check on its own, for re-checking the temp-tree kit without paying for a
        # full 20-mutant sweep. The SHIPPED acceptance command is still the plain run,
        # which executes this same function after the mutants.
        return entrypoints()
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
    rc = 1 if fails else 0
    rc |= entrypoints()
    return rc


if __name__ == "__main__":
    sys.exit(main())
