# Session notes archive — sessions 273-273

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-272-272.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 273 (2026-11-17, BUILD, zero box) - B22: both save record arrays grown in ONE writer call, CREATE leg fed by the RELOADED base record
- THE PICK from `track_mode.py` (`MODE=BUILD next_rung=B22`); B22 was UNAUTHORED (no rung in
  `BUILD_SPINE.md`, no NAMED row, no commit) so this fire authored it, the way B14-B21 did.
- MEASURED, three claims of mine were FALSE before the bytes answered:
  1. the rung text asserted "the region `units_off`..EOF is the original lifted by ONE amount" -
     wrong: `savewriter.build_image` emits originals then grown bases and re-anchors the tail there,
     so only the tail lifts by the full 1572 B and the base originals lift by 52. The gate now
     compares FIVE bands (`unit originals 3484 | the ONE new unit 52 | base originals 5472 |
     the grown bases 1520 | tail 10800`), each against its own source.
  2. `r["new_recs"]` are 3-byte `(fac,x,y)` tuples, not 304-B records - a gate comparing them to
     image bytes could never pass. `basefound.record_bytes(led.records[-5+k])` is the right object.
  3. the header diff is 3 bytes, not 4 ("one per modeled field" was decoration; cur/tf already
     hold their recorded values in this save;
  4. and the loudest one, caught by GREPTILE (P1 on #286) rather than by my own gates: the G5 claim that
     the header counts and the shape scan "DISAGREE by exactly the unit growth". It came from applying
     image A's count arithmetic (`units_off + 52*(n_units+1)`) to image B's scan anchor. `sim/save`
     derives `units_off` FROM `bases_off`, so measured per-image (`bases_pred = units_pred + 52*n_units`)
     the two methods AGREE byte-for-byte and `closes` is True on orig/B21/B22. The gate now carries its
     own retraction in its printed text instead of the false claim.
- FOUND: `sim/save`'s shape locator CONFIRMS ONLY THE 18 NAMED bases of the grown container -
  M282's founders write an empty name span and `_base_ok` wants `[ -~]{3,30}\x00` at +19. A grown
  base is locatable by COUNT, never by SHAPE, and on a container that grew only ONE array the
  count position and the shape anchor DISAGREE by exactly that growth (226319 vs 226267).
- ACCEPTANCE: `python3 -m sim.selftest --b22 programs/saves/m54b_clean.SAV` -> **PASS B22: 11/11**;
  `python3 -u -m sim.composedgrowth` prints the same 11 labels; two runs byte-identical
  (digest a7ec6d38ba67cbe9, image sha256 f7d90eb77ca7abac); evidence file == fresh rerun.
- SELF-FOUND DEFECT, kept visible: `sim/composedgrowth.py` carried a STALE `acceptance()` draft
  BELOW the good one (truncating labels to 64 chars, printing the report itself, recomputing a
  third time). Python let the later `def` win, so `--b22` silently ran the shadowed version and
  the PASS line still read 11/11 - a green result from the wrong code path. Duplicate deleted.

- POST-REVIEW on #286 (1 P1 + 3 P2; all four accepted, none argued with):
  * G5 retracted as above (the P1). It is a repeat of s272's lesson in a new costume: a comparison built
    from two different objects, asserted as a property of one.
  * G9's falsifier (P2) re-read the corrupted image at its OWN call site, so a regression that made the
    real leg read the MODEL stayed green. Now: ONE shared producer `record_from_image(image, idx, head)`
    used by both the clean and the corrupted case; the perturbation covers tile AND faction; the gate
    asserts the created unit CARRIES the bad bytes (x/y span + owner byte), not merely that it differs.
  * NEW G12 (P2, my design) runs the MUTATION EXPERIMENT in-process every run: rebind the shared leg to
    read the model, restore in `finally`, and assert the mutant's SIGNATURE - G9's record collapses back
    onto G3's (the model's own (27,29) fac 1) while the real leg carries (1447,1448) fac 5A. G3 is
    DECLARED blind to it (the fixture's model tuple equals the container tuple), so the honest framing
    replaced a gate that could not fail. Acceptance is now **PASS B22: 12/12**, two runs byte-identical
    (report digest 06dd4ac599fd0..., written image sha256 f7d90eb77ca7abac unchanged).
  * NAMED citations (P2) were one line off after the evidence regenerated; the block was rewritten and a
    resolver now checks every cited line actually contains the gate label its row names - CITATIONS_RESOLVED.
  * A skill law I wrote THIS fire was false too: I claimed `milestone.py start` can branch from the
    worktree's stray tip. `cmd_start` does `git checkout main` + `git pull --ff-only` and only THEN
    `git checkout -b`, so it never can. Law rewritten: never assert a stray commit's fate either way
    without `git merge-base --is-ancestor` (its exit code, not my memory).
  * Process slip worth keeping: my docs-patch script aborted on a stale multi-line anchor (the `submit`
    step had re-wrapped SESSION_NOTES.md), and `git add -A && git commit` ran anyway - so commit b2b357d
    shipped corrected code with stale docs. Anchors that span wrapped prose must be matched by line
    number or single unique line, and a commit that follows a failed patch step is a FAILED step, not a
    clean one.
- LANDED: #286 merged as `3f645e1`; cursor handoff #287 merged as `138182c`. `track_mode.py` then reads
  `MODE=ANALYSE analyse_since_build=0 last_build=B22 next_rung=B23` - the flip lands on the fire right after
  a build merge, so the handoff must be written AFTER merging (my first cursor draft told the next fire to
  author B23, which is wrong: B23 is queued behind an ANALYSE fire). Law added to the loop template.
  Final B22 numbers to quote: **12/12 gates**, written image sha256 `f7d90eb77ca7abac`, five-band layout
  3484 + 52 + 5472 + 1520 + 10800 B, header diff 3 B (`0x44`, `0x48`, `0x54`).
