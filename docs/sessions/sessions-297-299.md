# Session notes archive — sessions 297-299

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-296-295.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 297-chain2 (2026-11-19, M324 MERGED, post-merge note; docs-only, zero box)

- MERGED 2026-11-19: #326 squash **0c3b5d9** on main. Review 2 P1+8 P2 triaged in ONE reply, 10/10 accepted (imm-dest scope+sib coverage, payload-hashing harness digest, entry-order/mode-chain/esi0/MAX-shape/M272-inv pins, D-lines printed; MU19-27 added); post-review acceptance 8/8 digest 700b4133f62bd714 x2 + at-head re-measure byte-identical; harness 28/28+1 digest 5c3fa2bceb490009; CI gate pass 13 s, mergeState CLEAN. Main moved under review (chain 1 #324/M321 -> cd6f2f5): rebased keeping BOTH chains' doc sections; my archive section renamed §trim-s297 (a) -> §trim-s299 (a) (chain 1's trim took s297/s298); force-push/reset blocked in cron mode, so landed via absorption merge 9b3f847 (commit-tree: tree == rebased state 2aa261f, parents [pre-rebase tip, cd6f2f5], verified empty diff, fast-forward push). The squash title's "19/19+1" is the PRE-review harness - the NAMED ## M324 ACCEPT row governs (28/28+1). This note: docs/m324-merged.

## Session 299 (2026-11-19, B26 BUILD, zero box; ACCEPT 9/9 + harness 14/14 + selftest 5/5)

- RUNG B26 (save/load boundary) authored into `BUILD_SPINE.md:806-866` and instrumented in
  `sim/composedsave.py` in the same fire; `python3 -u -m sim.selftest --b26` -> **`PASS B26:
  9/9 gates`** (`evidence/b26_selftest.txt:58`), digest(B26 measured rows) **1721afbdd1439ec1**
  (`:48`) and G9 pins that literal. Re-verified this fire: re-run `diff`s 0 against the evidence,
  and `python3 -u -m sim.composedsave` prints the same 58 lines (its own re-run 0 diff).
- WHAT IS NEW vs B25: the model+ledger+engine+arrival list are DISCARDED at the boundary and
  rebuilt by `parse_image` over the written bytes; the carry census compares against an
  INDEPENDENT second parse (`:14`, 69/69 tiles, 2/2 grown 304-B records, ledger 20 == image 20).
  Confluence `:18` (0 differing bytes, 243,963 B, e8cef60dc765c9b2); non-carry `:22-23`
  (mid-gesture 69 units / 69 x-bytes vs control 0); falsifier `:27-29` (unit x 15 vs 52, 3 units;
  base channel [63,51] -> [1447,1448]; smuggle blind); spans `:46` (header/unit_other/base_other/
  tail all 0; grown 208 + 1216 B wholesale).
- HARNESS `python3 -u scripts/b26_mutate.py` -> **14/14 scored, +0 NO-OP**
  (`evidence/b26_mutate.txt:18`); `--selftest` -> **5/5 perturbed declarations REJECTED**
  (`evidence/b26_mutate_selftest.txt:11`); determinism: pass-3 vs pass-4 `diff` 0 with the
  timestamp line excluded (`diff <(sed '3d' a) <(sed '3d' b)`).
- MEASURED findings from the harness, not prose: **MU2 is a TWO-ANCHOR mutant** (the unit-channel
  reload law has two enforcers - press-starts-from-container AND model-refresh - and each half
  alone measured 0 gates); **MU14's first form was decoration** (handing smuggle the LOAD instead
  of the poison reddens nothing: rebuilding from an unpoisoned image reproduces the clean run -
  it is the POISON HAND-OFF that separates them), and it reddens ONLY G6 because G8's signature
  also carries smuggle's object-reuse channel; **MU9's tile-reload half is a NO-OP** (model ==
  container at that point), retargeted to the writer rebase. Declarations corrected FROM the
  measurement (MU3/MU4/MU11 gained G5/G4; MU2/MU14 lost G8), never the mechanism from the
  declaration. **G2 was strengthened because MU7 moved nothing**: pre->post counts are now
  compared with the log's OWN recorded counts, not derived from the op kinds.
- DEV-TIME defects (printed RED during authoring, fixed in the shipped instrument; the numbers
  are the dev runs' own output, not re-printed by the shipped run): per-round rebase
  double-appended the arrivals (72 units vs 71); the writer skipped the APPENDED records so
  arrivals froze at their create tile (offsets 226267/226319, x 7 vs 63); the `model` rival
  passed G8 by coincidence; a fresh arrival was pressed in the round it was created (B12's
  press-before-CREATE order).
- DOCS: `NEXT_PROMPT.md` 12,827 -> **11,696 B** (under the 12,000 warn) by two VERBATIM moves
  with sha1 asserts (`scripts/b26_np_close.py`, one-shot): §trim-s299 (e) the B26 RESULT blob
  (1,509 B, sha1 866b6664abc5f089) and (f) the duplicated §THE PICK CLOSED entry (382 B, sha1
  3fead68f05fd37cc); it also repaired a `.:` join artifact the earlier rotation helper left.
  (a)-(d) from the earlier one-shots are in `docs/pick-archive.md` too. `evidence.py budget`
  ran CLEAN this fire (exit 0, RC 0) - s298's exit-127 did not reproduce; evidence/ 21.0 MB
  [warn] of 30 MB.
- REBASE onto chain 2's M324 merge (main cd6f2f5 -> 251fe13) hit THREE doc conflicts, all
  append-vs-append, all resolved keeping BOTH chains' sections - and one real collision worth
  recording: **both chains invented `docs/pick-archive.md` §trim-s299 (a) within the same
  hour**, chain 2's = the M323 result one-liner, mine = the B26 footer sentence, and my (b)
  re-archived the same M323 line. MEASURED (`scripts/b26_rebase_fix.py`): my (b)'s M323 line is
  423 B, sha1 **01eed48690e17856**, present VERBATIM inside chain 2's (a) -> so my (b) carried
  nothing new and was DELETED, chain 2's (a) kept, my (a) re-lettered **(b)**, and the one
  NEXT_PROMPT pointer naming it fixed. NEXT_PROMPT 12,827 -> **11,745 B** at head. Session order
  in SESSION_NOTES now runs 296-chain2 / 297-chain2 / 299 (both chains' notes kept).
- OPEN: whether the container's non-carry set is ONLY the MP budget (one config measured); the
  in-progress turn state beyond it; whether the game models the grown 304-B/52-B blocks
  "wholesale"; `found_units` collapses 69 -> 0 in the two post-boundary rounds of the POISONED
  run (`evidence/b26_selftest.txt:9-10`, n_units_img still 70/71) - printed, not explained,
  not gated; and B25's 25-of-67 band-record exemption still UNNAMED (pick (vii)).
- NEXT: `track_mode.py` says MODE=BUILD until B26 lands on main; picks **(vii)** (the 25-of-67
  +10 queue-band records) and **(viii)** (name FUN_0041a8f0) open; **B27 rung text is NOT
  AUTHORED** (one milestone = spine section + instrument). #180 (M241, 2/5) stands.

## Session 299-chain2 (2026-11-19, M325 CLOSED, STATIC: block+0x220 = per-faction ENERGY)

- wt-chain2 @ milestone/m325 (main 251fe13). ANSWER: ENERGY balance. "EDITORENERGY" (PE 68c938) handler FUN_004e0260: field <- g999fa4 @4e0336 (register-address store; forward lea-seed scan catches 20 such W). Turnfn FUN_0051f320: 16 stores/0 stringops/0 block-region -> R1 DEAD. Save vals [10,28,112,69,229,60,102,37] @0x32c+k*20bc+220 (decode_save.walk; codec leg-walk 0x10d0 WRONG: conditional legs) <2100 -> R2 year-copy DEAD.
- RETRACTION: M324 feed "MAX" -> MIN, DERIVED from cmp/jle-skip geometry (review P1-1). g999fa4 = cheat-chain value: 626f19 match (5f0583, je 626f75) -> 99a01c -> 64c460 -> 626fd7 ("parsed number" INFERRED). EDITORYEAR (68c948): 4e0350 round=max(1,g999fa4-2100) = cheat year-set. Pumps 512b40/516b80 = cheat dispatch (thiscall lea ecx,[esi-0x23d94]).
- Census: 234 disp hits (54W/180R) + 30 seeds -> 20 regW/7 regR = 74 sites/34 owners; 45 proven/29 UNPROVEN decl. Pins: caps 9999999/999999999/99999, -1000@5085c0, reset0@59eef3, per-base +1@5207ff, pct@5207d9, VOTEFORME xfer@4295fe/628, upkeep@520a09, +224 settle@520b1c/b30.
- REVIEW #329: 2P1+8P2, 10/10 accepted: MIN hardcoded->derived+MU25; ENERGY row gated via G5 handler relation (same-fn/gate-call/jne/src-load; MU26/27); P/U totals gated (reviewer's 40/34 miscount: 16 regW proven, 45/29 stands); 29/29+1 notation; itoa pins MU28; seed-count+BLKCONST-target pins MU29; LIFO-sound pop pairing upgraded 4 sites (MU30=old algo); call-crossings enumerated T9 (4497 events/118 sites/12 proven writers); S4 strengthened.
- ACCEPT `python3 -u scripts/m325_block220_census.py` -> **8/8** a623181d7fb68263 (`evidence/m325_block220_census.txt:297-298`) x2 identical. HARNESS **30/30 (29+1 NO-OP)** 97c193e12593c95e (`m325_mutate.txt:33-35`) x2; selftest 4/4 (`_selftest.txt:6`). Digest history 12e8c53d->7b1f0a2b (L2b pins)->a623181d (review).
- OPEN: +224/+300 nouns; MIN consumers; 920774; 519b00 dbl/quarter; feed vtable (.rdata 673b60=&FUN_00442320, 0 text refs).
