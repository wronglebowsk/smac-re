#!/usr/bin/env python3
"""scripts/b24_mutate.py - mutation harness for rung B24's instrument.

Law (NEXT_PROMPT trap 24, from Greptile #281): after repairing a gate, run a
mutation harness that re-creates each defect by anchor->replacement and exits
non-zero unless EVERY mutation reddens its named gate(s). A mutation false on
the real bytes must be used (never a dict entry an assert reads whole), and the
reddened gate SET must equal the declared set - extra reds are an undeclared
dependency, missing reds are a decorative assert.

FOUR OUTCOMES, and the set is MEASURED, never authored (this file's first pass
declared {G3,G7} for MU3 and two-gate sets for MU4/MU7; all three were wrong):
  (1) measured gate-set == declared            -> OK
  (2) measured set differs                     -> BAD (authored, not measured)
  (3) reddens NOTHING                          -> BAD, a NO-OP mutant
  (4) CRASH                                    -> BAD, UNLESS declared, and then
      only when the message matches CRASH_MARK. Measured reason (see MU8): a
      fold that addresses the visited record BY TILE does not answer the fit
      wrongly - it cannot answer at all. Every other crash is a harness defect.

Each mutant is a text patch of sim/composedlive.py, written as a sibling module
inside sim/ and executed in a FRESH subprocess (no module cache), relayed
through its own acceptance() exactly as `python3 -m sim.selftest --b24` does.
"""
import os
import re
import subprocess
import sys
import time

EXPECTED_CRASH = "CRASH"
# Whitespace-flexible: the engine formats the tile with str(tuple), so the
# message reads "tile (27, 29) not located" with a space (measured).
CRASH_MARK = r"tile\s*\(\s*27\s*,\s*29\s*\)\s+not\s+located"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(REPO, "sim")
CL = os.path.join(SIM, "composedlive.py")

# (id, description, target-file, anchor, replacement, declared red gates)
MUTANTS = [
    # Every declared set below is MEASURED, not assumed - see SESSION_NOTES and
    # the run this file's stdout archives.
    ("MU1", "no falsifier: the tile/owner poison block never runs", CL,
     '''        if (poison and mode in CONTAINER_READING_MODES and img is not None
                and seeding and visit_no is not None
                and visit_no >= POISON_FROM):''',
     '''        if (False and poison and mode in CONTAINER_READING_MODES
                and img is not None and seeding and visit_no is not None
                and visit_no >= POISON_FROM):''',
     {"G3", "G7"}),
    # (MU2's FIRST anchor - disabling the fold's read-side `seed_rec = bytearray(
    #  target_raw)` line - was measured to red NOTHING: the driver's per-turn
    #  write already re-composes the record from the container's bytes, so the
    #  model's tile constants never reached the image. A mutant that cannot
    #  redden a gate is a no-op, not a test: replaced by the write-side anchor.)
    ("MU2", "the WRITER re-composes the visited record from the founder's model "
     "bytes instead of the container's", CL,
     '''            if target_raw is not None:
                ent["raw"] = bytearray(target_raw)''',
     '''            if False:
                ent["raw"] = bytearray(target_raw)''',
     {"G3", "G7"}),
    ("MU3", "the queue span is carried from the model, never read from the image",
     CL,
     '''        elif cont_read is not None:
            target_raw = cont_read
            spx = soct.spans_of(cont_read)
            qspan = {"st": spx["st"], "pen": spx["pen"],
                     "slots": spx["slots"], "mirror": spx["mirror"]}''',
     '''        elif cont_read is not None:
            target_raw = cont_read
            qspan = visits[-1]["span_after"] if visits else {
                "st": SEED_ST, "pen": SEED_PEN, "slots": list(SEED_SLOTS),
                "mirror": SEED_ST}''',
     {"G7"}),
    # Measured {G7} only, NOT {G3,G7}: the span read-back moves the falsifier
    # gate and nothing else, because the span is the container's WEAK channel
    # (it is byte-identical to the model's chain at every turn that is read
    # back) - which is exactly the claim G7 now carries in its wording.
    ("MU4", "earlier arrivals are dropped from the next write (no prior_units)",
     CL, '''            prior_units=arrivals, start_img=img,''',
     '''            prior_units=None, start_img=img,''',
     {"G4", "G5", "G6", "G7"}),
    # MU4's set is MEASURED, and it is wide because the arrival list is load-
    # bearing four ways: with no prior_units the fold re-writes only its own
    # window's units, so G6 loses arrivals 2/3 (n_units 67->68, not 70), G5's
    # arrival table diverges from the model fold, G7's "arrival 3 is the image's
    # last unit record" and the storage-poison verdict shift both move, and G4's
    # per-turn unit count moves. G8 was in this set BEFORE review #307 and is not
    # any more: the frozenargs rival that compared against the true run's
    # arrival list was measured DEGENERATE and retired, and the locate rival is
    # now judged on its own tile-law message, so neither reading depends on the
    # prior-units channel - measured 4/9 red on the post-review head, and the
    # set is the measurement. An undeclared extra red is a dependency the author
    # did not know about; a missing red is a decorative assert - so the SET is
    # what is asserted, not just non-emptiness.
    ("MU5", "the storage-poison probe is disabled (read-back half decoration)",
     CL, '''        if (mode == "container" and st_poison and img is not None and seeding and
                visit_no is not None and visit_no == ST_POISON_VISIT):''',
     '''        if (False and mode == "container" and st_poison and img is not None
                and seeding and visit_no is not None
                and visit_no == ST_POISON_VISIT):''',
     {"G7"}),
    # MU6 ("the locate rival reads the container but is not shown the poison")
    # was MEASURED a NO-OP and then RETIRED with its rival: with the poison
    # withheld the locate rival still bails at every visit and completes 0
    # arrivals, so G8 stays green whether or not the poison reaches it - the
    # rival is degenerate (see sim/composedlive.py's G8 note and SESSION_NOTES
    # s287). The tile law is carried by MU8, which switches the fold's OWN
    # addressing law to tile: clean leg completes, poisoned leg dies. A mutant
    # with no gate to redden is not a test, so it goes with the rival.
    ("MU6b", "the nopop rival pops NORMALLY (a correct queue must not pass)",
     CL, '''    np_ = run(sv, ops, earliest, mode="nopop", poison=False)''',
     '''    np_ = run(sv, ops, earliest, mode="container", poison=False)''',
     {"G8"}),
    # MU6b is the review's own test case ("verify that restoring normal popping
    # makes this check fail"): with the rival run as a plain container fold it
    # produces 3 arrivals and a pending sequence identical to the clean run, so
    # BOTH halves of the repaired nopop condition go false and G8 reddens alone.
    ("MU7", "the fold addresses the LAST grown slot, not the visited one", CL,
     '''            seed_rec=seed_rec, tile_at=lambda: TARGET, slot_i=target_idx,''',
     '''            seed_rec=seed_rec, tile_at=lambda: TARGET, slot_i=None,''',
     {"G5", "G6", "G7", "G8"}),
    # MU7's set is MEASURED. slot_i=None means "the slot grown this window"
    # (rung B23's law, sv.n_bases) - B24's visited record sits MID-array at
    # position 22 with a later-logged op appended after it, so the fold starts
    # writing somebody else's record: G5's span/arrival equality with the model
    # fold breaks, G6's n_units law reads the wrong container, G7 loses the
    # poison carry (it lands on a clean record the gates never inspect), and
    # G8's locate rival stops failing for the reason claimed.
    ("MU8", "the fold ADDRESSES its record by tile (mode=locate as its law)", CL,
     '''            sv, bnds, mode=mode,
            pos=True, overrides_fn=ovs, d0s=[D0_DECL], price=price,''',
     '''            sv, bnds, mode="locate",
            pos=True, overrides_fn=ovs, d0s=[D0_DECL], price=price,''',
     EXPECTED_CRASH),
    # MU8 is the EXPECTED_CRASH shape, and the crash IS the finding. NOTE what
    # "address by tile" means HERE, measured: `pos=False` is NOT it - the engine
    # then falls back to _find_kor, rung B23's Korolev locator, and dies with
    # "Korolev (29,42) not located" (that tile is not in this save at all),
    # saying nothing about B24's record. The tile law is mode="locate"
    # (`idx = _find_tile(im, tile_at())`, composedturn.py:194): the fold looks
    # its OWN record's tile up in the image every boundary instead of naming a
    # slot. Measured with this mutant: the unpoisoned leg runs (the tile is
    # (27,29) at position 22, exactly the slot pos=True names - so tile-vs-
    # position cannot be settled on an uncorrupted run), and the poisoned leg
    # dies raising "tile (27, 29) not located in the image": once the container's
    # tile bytes for that slot are rewritten, a tile-addressing fold cannot
    # address the record at all - no verdict, span or arrival is ever produced
    # for it. The harness matches the message text, not just "something died" -
    # a crash with any other message is still a defect.
    ("MU9", "G9 compares LABELS+VERDICTS only (a details-blind repeat check)",
     CL, '''    det = (sha2 == sha and rows2 == rows and d2 == d1)''',
     '''    det = (sha2 == sha and [(l, o) for l, o, _ in rows2]
           == [(l, o) for l, o, _ in rows] and d2 == d1)''',
     "NOOP"),
    # Measured: reddens NOTHING (the two runs of this instrument agree on labels
    # and verdicts, so weakening this half is a NO-OP here) - and it is KEPT and
    # declared as a NO-OP, because that is the honest state of the half: the
    # load-bearing halves of G9 are the MEASUREMENT DIGEST (d2 == d1, mutated by
    # MU10) and the final-image sha. A declared no-op teaches the next reader
    # which half of a compound condition is decoration; an undeclared one hides
    # it. Re-measure this if the two runs ever disagree on a detail string.
    ("MU10", "the SECOND run's per-visit table is corrupted (mirror field), so "
     "G9 must notice via the measurement digest alone", CL,
     '''    rows2, sha2, clean2, pois2, mem2, _ = compute(sav_path, log_path, trace_path,
                                                  line)''',
     '''    rows2, sha2, clean2, pois2, mem2, _ = compute(sav_path, log_path, trace_path,
                                                  line)
    clean2["visits"][1]["span_after"]["mirror"] ^= 1''',
     {"G9"}),
    # MU10 was a WEAKENING (`det = ... and rows2 == rows`), and a weakening is
    # not a mutation test: deleting a term from a conjunction can only make the
    # gate MORE likely to pass, so it can never redden - measured 0/9 red, a
    # NO-OP by construction (skill: instrument-laws, mutation must be FALSE on
    # the real bytes). Re-shaped to corrupt the DATA instead: the second run's
    # visit 1 `mirror` is flipped AFTER compute(), a per-visit field no gate
    # DETAIL prints and which the final image sha does not cover, so rows and
    # sha still agree and ONLY the digest over the per-visit tables can catch
    # it. Measured red: G9 alone - which is what makes the digest load-bearing
    # rather than decorative.
]


def run_mutant(mid, path, anchor, repl, tag=""):
    src = open(path, encoding="utf-8").read()
    if src.count(anchor) != 1:
        return None, "ANCHOR NOT UNIQUE (%d) in %s" % (src.count(anchor), path)
    # tag keeps parallel runs from clobbering each other's temp module
    name = "_b24mut_%s%s.py" % (mid.lower(), tag)
    out = os.path.join(SIM, name)
    open(out, "w", encoding="utf-8").write(src.replace(anchor, repl))
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from sim import %s as m\n"
        "res = []\n"
        "m.acceptance(m.DEFAULT_SAV, res)\n"
        "print('BADCOUNT', sum(1 for r in res if not r[1]))\n"
        "print('NGATES', len(res))\n"
        "print('BAD:', ' | '.join(sorted({r[0] for r in res if not r[1]})))\n"
        % (REPO, name[:-3]))
    try:
        p = subprocess.run([sys.executable, "-u", "-c", code], cwd=REPO,
                           capture_output=True, text=True, timeout=1200)
    finally:
        for junk in (out, os.path.join(SIM, "__pycache__",
                                       name.replace(".py", ".pyc"))):
            try:
                os.unlink(junk)
            except OSError:
                pass
    if "BADCOUNT" not in p.stdout:
        # a crash is NOT a red gate: the harness must say so and fail loudly
        last = (p.stderr.strip().splitlines() or ["(no stderr)"])[-1]
        return None, "CRASH: %s" % last[:110]
    nbad = int(re.search(r"BADCOUNT (\d+)", p.stdout).group(1))
    ng = int(re.search(r"NGATES (\d+)", p.stdout).group(1))
    bad = re.search(r"BAD: (.*)", p.stdout, re.S).group(1).strip()
    gates = set(re.findall(r"rung B24 (G\d+)", bad))
    return gates, "%d/%d gates red" % (nbad, ng)


def main():
    # --only MU2,MU3 runs a subset (a mutant takes ~60-100 s; the unattended
    # runner batches them), --list prints the table without running anything.
    args = sys.argv[1:]
    todo = MUTANTS
    want = {m[0] for m in MUTANTS}
    if args and args[0] == "--list":
        for m in MUTANTS:
            declared = m[5]
            print("%s\t%s\t%s" % (m[0], ",".join(sorted(declared))
                                   if isinstance(declared, set) else declared,
                                   m[1]))
        return 0
    if args and args[0] == "--only":
        want = set(args[1].split(","))
        todo = [m for m in MUTANTS if m[0] in want]
    tag = ""
    if "--tag" in args:
        tag = "_" + args[args.index("--tag") + 1]
    if args and args[0] == "--only":
        if len(todo) != len(want):
            print("unknown mutant ids: %s" % (want - {m[0] for m in todo}))
            return 2
    print("== B24 mutation harness: %d mutants (each must match its declared "
          "effect: an EXACT gate set, a declared message-matched CRASH, or a "
          "declared NO-OP) ==" % len(todo))
    print("-- harness %s --" % time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    fails = []
    declared_noop = []
    for mid, desc, path, anchor, repl, declared in todo:
        gates, info = run_mutant(mid, path, anchor, repl, tag)
        want_noop = declared == "NOOP"
        if declared == EXPECTED_CRASH:
            ok = (gates is None and "CRASH:" in info and
                  re.search(CRASH_MARK, info) is not None)
            if ok:
                info = info + " [declared: tile-addressing cannot run]"
        elif want_noop:
            ok = gates is not None and not gates
            if ok:
                declared_noop.append(mid)
                info = info + " [declared NO-OP: this half is decoration]"
        else:
            if gates is not None and not gates:
                info = info + " [NO-OP: reddened nothing]"
            ok = gates is not None and gates == declared and bool(gates)
        want = (declared if isinstance(declared, set)
                else declared if declared in (EXPECTED_CRASH, "NOOP")
                else "BAD-DECL")
        got = (",".join(sorted(gates)) if gates else
               ("CRASH " + info.split("CRASH:", 1)[1].strip()
                if gates is None and "CRASH:" in info else "nothing"))
        print("%-6s %-46s declared=%-18s measured=%-44s %s  (%s)"
              % (mid, desc[:46], ",".join(sorted(want)) if isinstance(want, set)
                 else want, got[:44], "OK" if ok else "BAD", info))
        if not ok:
            fails.append(mid)
    scored = len(todo) - len(declared_noop)
    print("== %d/%d mutants matched their declared effect "
          "(+%d declared NO-OP, not scored: %s) =="
          % (scored - len(fails), scored, len(declared_noop),
             ",".join(declared_noop) or "-"))
    if fails:
        print("BAD mutants (did NOT match their declared effect): %s"
              % ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
