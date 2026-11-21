# Session notes archive — sessions 296-295

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-293-294.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 296 (2026-11-19, post-merge hygiene for #319; zero box)

- B25 MERGED: #319 squashed to **main 1556ce9** (the sha is found by SUBJECT on `origin/main`, not asserted:
  `evidence/b25_merge_state.txt:2`), CI `gate` = SUCCESS on head 5ed5d93 (13 s). The
  squash title carries the POST-review numbers (9/9, anchor 901a286332960a10 pinned by G9, harness
  13/13 + 3 NO-OP, selftest 5/5) - the #317 wart, where a squash title kept the pre-review counts and
  needed a NAMED note to correct it, does NOT repeat here.
- The closeout claims are now MEASURED, not narrated: `python3 -u scripts/b25_merge_state.py` ->
  **`PASS b25_merge_state: 15/15 checks`** (`evidence/b25_merge_state.txt:17`, re-run byte-identical).
  It finds the merge by SUBJECT on `origin/main` (`(#319)` -> 1556ce9), requires that sha to be the one
  both `NAMED ## B25` and these notes quote, requires NEXT_PROMPT's own measured size (11764 B) to be
  under the 12,000 warn AND to be the number written here, and audits EVERY `§trim-sNNN` VERBATIM block
  from s292 on (7 of them): each must be byte-for-byte in the NEWEST `origin/main` history blob of
  NEXT_PROMPT.md that still carries it - so the pre-move state is found in history, not asserted, and
  each row PRINTS the sha it matched (`6394107` = the #319 merge's PARENT for the two s295 blocks,
  `93c25fe` = chain 2's #321 for §trim-s296 (b)) - AND must be ABSENT from the hot doc, which is the
  COPIED-not-MOVED rival, and it fails. §trim-s295 (a) at `docs/pick-archive.md:1023`, (b) at `:1035`.
  Rotation faithfulness: 17 lines byte-identical to the pre-rotation blob `1556ce9:SESSION_NOTES.md`,
  1 additively annotated, 0 lost/mangled, sections gone from the hot file (`evidence/b25_merge_state.txt:15`).
- CAP, again: chain 2's #322 append-only M320 line put NEXT_PROMPT at **12,333 B, 333 B OVER the
  12,000 warn** - the instrument's size row went RED on the rebase, honestly, before any doc was
  touched. Fixed by MOVING, not deleting: TRAP 24's 7-line text -> `docs/pick-archive.md` §trim-s296 (a)
  at `:1046`, and chain 2's M320 footing line VERBATIM -> §trim-s296 (b) at `:1062`, each replaced in the
  hot doc by a short pointer. Measured after: **11,764 B** (236 B of headroom; the next fire must pair
  its additions with deletions). Chain 2's session text is untouched in `SESSION_NOTES`
  (`## Session 294-chain2`) and its `NAMED ## M320` block stands.
- TWO DEFECTS THE INSTRUMENT FOUND IN ITS OWN FIRST DRAFT, both real, both fixed here: (1) it picked the
  rotated archives by a LEXICOGRAPHIC sort, so it measured sessions-97/98/99 and never the file this
  branch had just rotated - a gate passing on an unmeasured state; now numeric (275 / 276-277 / 278-279),
  and the cite pattern accepts BARE text as well as backticks (276-277 cites backticked, 278-279 bare, so the
  old pattern left the bare line - the one with the stale digest - unmeasured) - 5/5 resolve
  (`evidence/b25_merge_state.txt:14`).
  (2) The new digest rule REDDENED on first run: `docs/sessions/sessions-278-279.md:18` cited
  `evidence/m313_event_map.txt` with digest 3fee30fcd74735ad, which the tracked blob does NOT carry (that
  file is the post-#294-review run: `== M313: 21/21 ==` at `:23`, digest 5e14170de426d127 at `:22`); the
  FAIL read `b25_merge_state: 1/10 checks failed: ... unexplained: ['sessions-278-279.md:18
  3fee30fcd74735ad']`. The archive line now states both digests with anchors: a superseded digest must
  share its line with its replacement or the row fails.
  NEXT: B26 (spine text NOT authored) or picks (vi)/(vii).

## Session 297 (2026-11-19, M321 = pick (vi), STATIC, zero box; 7/7 gates + 13/13 mutants)

- Both still-unnamed memo-site owners are BASE-PANEL STATUS-ICON emitters, named from the labels at their
  `call 0x48f100` sites (strings read as BYTES from `programs/terran.exe` via the PE section table; zero
  box): FUN_004ee410 7x STARVE, POPULATIONLIMIT, LOWNUTRIENT{FARMS,FORMERS,SPEC1,SPEC2} +
  starv_sm/pop_sm.pcx @0x4ee501-0x4eec1b (`evidence/m321_memo_owners.txt:21-27`) = FOOD/POPULATION status;
  FUN_004f41f0 1x PSYCHREQUEST + talent_sm.pcx @0x4f46a9 (`:28`) = TALENT/PSYCH-REQUEST; DISJOINT (G3;
  MU13 -> red).
- 4 memo sites as M319 listed, each fed by `mov R,ds:0x68cbb0` + the refresh pair IN ORDER within 25 B
  (`:18-19`; MU2/MU7/MU8 -> G2). DEFECT FOUND WHILE WRITING: 0x4f44a8 (and M311's 0x4e3476, 0x4f5c3c) are
  the SHORT a3 form `mov ds:X,reg`; a `mov DWORD PTR ds:X,reg`-only detector sees 3 memo sites and 5/6
  stores. MU1 mutates the fix back -> G2+G7 red; `:9-16` prints 6+6 stores, 1:1 +-64 B.
- THE ARRIVAL TEST: EXACTLY 3 `test BYTE PTR [r+0x38],0x40` image-wide (0x416f32/0x417057/0x41ade4); r's
  nearest def is `mov r,ds:0x8f0d60` 3/3, the `je` target lies PAST `call 0x4f41f0` (so it gates the call),
  and the caller zeroes +0x78/+0x7c/+0x80 between (`:30-33`; MU3/MU9/MU10 -> G4/G7).
- THE FIELD: fold PARSED (lea 9x, lea 19x, shl 4 = 304*idx + 0x95da10 = base_array); 646 304-chains vs 565
  52-chains (unit array) kills the unit rival on the printed histogram (G1; MU5/MU6); 0x95da48-0x95da10=56.
  Bit 6's only OR-setter image-wide is 0x41ac34 (`:61`, MU11), inside FUN_0041a8f0's round trip via the
  scratch ds:0x99aa38 (field 0x40 <-> scratch 0x08 both ways: extract @0x41aa03, write-back @0x41ac26,
  `:63-67`); the callee re-tests it @0x4f43a0 (`:69`, G6, MU12).
- OPEN: 47 whole-dword field stores (record view) untraced to sources; the game nouns; 14/21 extraction
  lanes lack the `or al` arm; back_def's clobber rule reddens NOTHING here -> MU4 declared NO-OP (an empty
  set IS the asserted tripwire).

## Session 295-chain2 (2026-11-19, M323 CLOSED, chain 2 second fire, STATIC: ds:0x985afc = ROUND counter)

- Chain 2 in wt-chain2 @ milestone/m323 (from main 53a2553); chain 1 owns main/sim/picks(vi)/(vii).
- ANSWER: ds:0x985afc = global ROUND counter. 336 refs W5/T59/R272/A0; dw333+word1 (mov ax @59c18a)+byte2. WRITERS: FUN_005a0fa0 round=0 @5a108b (new-game, counts 985af0/af4 zeroed); FUN_0051f320 round+1 @51f53c (advance); FUN_004e0350 max(1,g999fa4-g92bf68) @4e0387/8e (callers = M314 pumps); FUN_0059ce10 rand()%3 {30,60,80} @59e2b1 gated 985ac4.7. YEAR: sole 985b00 writer @51f54f = FUN_005b2c00(round+1) = arg+g92bf68; g92bf68=2100 -> year=round+2100.
- GATES re-derived: M320 ==0 (59f1a0/59f19c/jne 59f1d4); M305 &3==bl(1) @51f711-71e; M317 >75 @55840d->setg; M177 stamps 533eec/53420e/534522 + age<16 @569401/8. Rivals YEAR/MODE-ENUM/LOAD-CONST dead.
- ACCEPT `python3 -u scripts/m323_round_census.py` -> **13/13** digest **136841406b5bee5b** (`evidence/m323_round_census.txt:536-537`), x2 identical post-review (`_rerun.txt:537`; pre-review e112a4260e3c1722 x3). HARNESS `python3 -u scripts/m323_mutate.py` -> **31/31+1 NO-OP** digest a25f4b5f2af8bb8a (`evidence/m323_mutate.txt:32-33`); selftest 4/4 (`_selftest.txt:5`). MU23 crash fixed (unary-imul guard); sets re-measured.
- REVIEW #323 (3 P1+7 P2): 9 accepted, 1 dismissed (P2-5 ACCEPT meta row: review_lint.py:85-86 + M320 precedent). RETRACTED "no word": 66-prefix mov ax @59c18a (FUN_0059c150) is a WORD read (G1/G9 re-pinned, MU31). Added: max-flow cmp/jge pins (MU27/28); bl full ebx def-set+push/pop pair+no-jump-in (MU29); year arg chain in G10 (MU13/30); year scan all memory-first forms; score() /13 + S4 13/13. MU13/19/30 sets re-measured.
- OPEN: rand-start noun; g999fa4 (fed block+0x220 @442642); save-carry (no loader writer; re-derive-from-year unproven); gaps 4f3a91/51da30; resolver linear-static (declared).
- TRAP: worktree info/exclude lives in the COMMON git dir - used trap-15 stash/start/pop.
- MERGED 2026-11-19: #323 squash **9c716f8** on main. Review 3 P1+7 P2 triaged in ONE reply (9 accepted incl. the word-width RETRACTION, 1 dismissed per review_lint.py:85-86 meta-row rule); post-review acceptance 13/13 digest 136841406b5bee5b x2 + at-head re-measure byte-identical; harness 31/31+1 digest a25f4b5f2af8bb8a; CI gate pass 15 s, mergeState CLEAN. Main moved under review (chain 1 #320 -> a2e226b): rebased keeping BOTH chains' doc sections; force-push/reset blocked in cron mode, so landed via a `-s ours` absorption merge 25ad19a (tree == rebased state, verified empty diff, fast-forward push). The squash title's "26/26+1" is the PRE-review harness - the NAMED ## M323 ACCEPT row governs (31/31+1). NEXT_PROMPT sits at 12,188 B with the M323 line (chain 1's trim-s296 rotation pattern applies next fire). This note: docs/m323-merged.
