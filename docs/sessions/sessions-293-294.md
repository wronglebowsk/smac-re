# Session notes archive — sessions 293-294

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-291-293.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 293-merged (2026-11-19, hygiene after #317)

- #317 MERGED -> main `147e66a` (gate GREEN, `review_lint --id m319` PASS 7 V rows, review 1 P1 + 9 P2 triaged in one reply). Cursor rewritten for the next fire; `NAMED ## M319` gains a `lead` governance row saying the squash title's 459f47e3178f439d / 12-12+1 are the PRE-REVIEW harness and the ACCEPT row governs (same defect as M314's "20/20" note).
- LAW RE-LEARNED: a meta/governance sentence in NAMED belongs at conf `lead`, not `V` - #318's own review returned 4 P1s on exactly that, because a `V` row must name a mutant that reddens it, and a process note has none.

## Session 294 (2026-11-19, B25 BUILD - the MOVE leg made persistent; zero box)

> SUPERSEDED IN PART by Session 295 (same day, #319 review triage): every `evidence/b25_*.txt`
> here was REGENERATED, so the line cites point one or more lines off (the anchor is now `:59`,
> the banner `:69`); the harness count is 13/13 + 3 declared NO-OP (was 11/11 + 2) and the
> selftest 5/5 (was 4/4). The numbers themselves (9/9, 268/268, 37/27/4, 39 mod 64) stand.

- Track said BUILD (last_build=B24) and `BUILD_SPINE.md` ENDED at B24, so the rung text was AUTHORED
  FIRST (one milestone = spine section + instrument), then built. `sim/composedmove.py`, `--b25` relays.
- ACCEPT `python3 -u -m sim.selftest --b25` -> **PASS B25: 9/9 gates**, digest **901a286332960a10**
  (`evidence/b25_selftest.txt:41`, banner `:51`), second run byte-identical; `python3 -u -m
  sim.composedmove` prints the SAME 9 gate lines (`evidence/b25_movepersist.txt`). HARNESS
  `python3 -u scripts/b25_mutate.py` -> **11/11 scored mutants matched their declared gate sets + 2
  declared NO-OP** (MU9 labels-only, MU11 multiset-only) (`evidence/b25_mutate.txt:16`); `--selftest`
  -> **4/4 perturbed declarations REJECTED** (`evidence/b25_mutate_selftest.txt:9`).
- ANSWER 1, the rung: the mover's start tile IS the container's. **268/268** (round,unit) reads equal
  the container at the round head, **0** divergences, and the container still holds the SAVE's tile for
  67 records in round 0 and **0** in every later round, so the read cannot be vacuous (G4 `:45`).
  Rewriting unit 0's tile IN THE IMAGE ONLY at round 1 shifts its whole later trajectory by **39 mod
  64** and it reaches the final container ([19,42] vs clean [44,42]); **0 of 67** other units move;
  the model-fed and read-after-write movers rebuild the CLEAN image byte-for-byte - blindness proved,
  not asserted (G6 `:47`, sightings `:21-23`). Footprint: **67** unit-array bytes == **67** tiles
  written per round, all at record offset **+0** (x only), plus the **1-B** year step 2151->2154; the
  final image is **68 B** from the save, **0 B** outside a modeled span (G2 `:43`, G7 `:48`).
- ANSWER 2, a correction (§B7 patched in place): **`m54b_clean.SAV` is 64x64 by its own header** -
  `scripts/decode_save.py --sections` prints "map header struct (64x64)" and grid 90,112 = 64*64*22 -
  while `planet.MP` is 80x80 and no repo map is 64. B7 wrapped x by the MAP FILE's width. Run here as
  a rival: **37** records land outside the container at the write and **27** come back as a later
  read, and the parser's own `found_units` drops **67 -> 4** (G5 `:46`, rows `:33-34`). B7's own
  4-round slice ends with **10 of 67** units outside the container grid (**4 of 67** at its accepted
  --turns 5; the end-state count is sampling-dependent - the written/read-back counts are the
  load-bearing ones, and MU13 reddens G5 if the cross-check is judged against the wrong grid).
- MUTATION TAUGHT THIS ONE TOO (sets MEASURED, first declares wrong): MU3 (container never refreshed -
  the defect this instrument HAD, caught by G2's byte-vs-tiles equality) {G2,G6,G8} not {G4,G6}; MU4
  (tiles never reach the writer) {G2,G3,G4,G5,G6,G8} - G7 stays green honestly, the one unit byte left
  is the FALSIFIER's own write and G7 counts modeled spans, not authors; MU8 was a NO-OP until the
  read/write out-of-grid arms were SPLIT into separate counters (as one union the write arm subsumed
  the read arm = decoration). G8 gained a `not_rival` clause so the rung cannot pass by quietly
  becoming one of its rivals.
- UNMODELED (declared in the spine text): MP/spent is model state, never persisted (B7's ASSUMED line
  about the 0x51f730 per-round refresh unchanged); per-terrain cost and the second move's source (B5);
  blocking/zone-of-control and every refusal cause but exhausted MP; y is never moved (dir=1, dy=0) so
  the y-bound law is NOT exercised; WHICH unit the game moves is not claimed (the gesture hits every
  unit, exactly as B7 declared). NEXT: B26, spine text NOT authored. #180 still stands (2/5).

## Session 295 (2026-11-19, B25 #319 review triage - 10 findings, all accepted; zero box)

- Clean start, not a repair: `git checkout -- sim/composedmove.py scripts/b25_mutate.py` back to the
  green head (the WIP is saved at `~/reverse/wip/b25_wip_20261119.patch`), then the findings
  re-implemented as a minimal delta. ACCEPT anchor UNCHANGED at **901a286332960a10** (digest_rows
  untouched), so every prior doc cite of it still holds; only evidence LINE NUMBERS moved.
- f.1 (P1): `render()` now prints the anchor `measure()` computed and **G9 pins it to a literal**
  `ACCEPT_PIN` (`evidence/b25_selftest.txt:59`). The mutant that names it alone: **MU9**
  (labels-only edit, no tile/count moves) -> measured `{G9}`.
- f.4/f.10: G4's law is now **byte-level carry** (table H `:40-43`): head bytes vs the previous
  round's WRITE bytes, difference == exactly the falsifier's own edits ([0,1,0,0] vs [0,1,0,0]);
  the read-back compares against a **FRESH DECODE** of the consumed bytes, 268/268 (`:63`). Re-
  measured sets: MU3 grew to {G2,G4,G5,G6,G8,G9} (a stale cache is what the fresh decode sees);
  new **MU14** (forget the previous write) = {G4} alone; new **MU15** (compare cache to itself,
  the old shape) = DECLARED NO-OP - it measures nothing when the cache is refreshed.
- f.5/f.6 (the round's real find): G5 now PINS 37/27/4 for both rivals and cross-checks the
  instrument's `tile >= width` set against `sim/save._unit_ok` on the same bytes over **44 probes**
  (11 runs x 4 rounds, table I `:45-56`). **They disagree raw: 36/44.** The 8 differers are exactly
  the records the decoder itself exempts - **25 of the 67** records of m54b_clean.SAV carry +10 in
  128/130/131/256/320/321/322/323 (>= 64), so its acceptance test coord-checks only **42**. With
  the decoder's own rule applied: 44/44, and `found_units` recomputed from `_unit_ok` == the
  parser's 44/44. On this save the exemption is INVISIBLE to coordinates (all 67 pristine +0/+2
  in-grid), so it splits the array by FIELD, not by tile sanity - which qualifies B7's and B25's
  "67 units": the model presses 25 records the decoder never coord-checks. **MU16** (copy the
  parser's number instead of recomputing) = declared NO-OP, i.e. that half is decoration HERE.
- f.8: G8's "matches none of its rivals" is now the FULL table-E signature vs all **5 RIVAL** rows
  (`:67`); the 3 `:clean` twins coincide by construction - table E carries no per-unit delta, G6
  reads the falsifier - and that is now stated instead of hidden by a hand-picked subset.
- f.9: the controls are blind **to the falsifier, not to writing** (still 268 unit bytes each; G6
  reads mdl_w/late_w > 0 itself). f.2: §B7 row split into (a) B7's own in-memory tiles and (b) the
  mpwidth rival's parse - a parser result had been claimed for a run that was never parsed.
  f.3: cursor said 10/10 at `:15`; measured 13/13 at `b25_mutate.txt:20`.
- f.7: the harness prints one `BADGATE <id>` line per failed row (id from gates()'s own name
  field), scored against the SHIPPED `gates()` with BADCOUNT/NGATES/dup cross-checks; no regex
  reads a message. Sets re-measured from scratch: **13/13 + 3 declared NO-OP**
  (`b25_mutate.txt:20`), `--selftest` **5/5 rejected** (`b25_mutate_selftest.txt:11`).
- TRAP LEARNED: a pinned global anchor reddens on nearly every mutant (7 of 13 gained G9). That is
  the pin working, but the discriminating information moves into the other gates - say so in the
  harness docstring or a reader scores the pin as padding.
- STILL OPEN: what the .exe does with a +10 >= 64 record's +0/+2; whether the wrap or the
  `_unit_ok` rejection fires first in the engine; which grid the shipped game gives a mover when
  the container and `planet.MP` disagree. #180 still stands (2/5).

## Session 294-chain2 (2026-11-19, M320 CLOSED, chain 2 first fire, STATIC: 8380-B block siblings)

- Chain 2 in wt-chain2 @ milestone/m320; chain 1 owns main/sim/NEXT_PROMPT/pick(vi).
- ANSWER: outside GOAL/SITE/REGION/VISIT: (a) LADDER of nine 128-entry per-region arrays +1078..+1878 (word x6, byte 1178/11f8, pair 1378) + CNT 18f8; (b) three 512-entry arrays (byte +854/+a54, word +c54); (c) SCALAR tail +2038..20bc (31 dwords, span 0x84, %16=4 - rival "third record array" DEAD); (d) flagword +0, enum +4 {2,4,5,6,7}, pair-flags +18 (M295).
- OWNERS: FUN_0059ec90 = block RESET: 114 W/RW, 92 offsets, blk0 only; callers 5a0b39/5a123e/5a1277; ladder loop 59efeb-59f01d (cmp 0x80), 512 loop 59f19c-59f1da (cmp 0x200; word store gated ds:0x985afc==0); magic 0xdfbe41/0xc0dfbe41 +1d0, -999 +3fc, defaults +328=5/+2050=1. FUN_0051dcb0 (M305 rebuild): init 51dcb8-51dd03 zeroes word {1478,1578,1678,1778}+MAX/CNT x128 x8 blocks (end 0x95f288); incs +1478 all-tile/+1678 class-filtered/+1778 +bit12 @51df3d/61/70; +1578 = per-region faction count, blocks 1..7 (0x94f4ec->0x95da10).
- ACCEPT `python3 -u scripts/m320_sibling_census.py` -> **12/12**, digest **12e247bdbc0f77ef** (`evidence/m320_sibling_census.txt:418-419`), 2 runs byte-identical (sha256 9b4c9ee106c1f3d6, +`_rerun.txt:418`). 4111 hits/208 offsets/196 sibling; reproduces M316 GOAL 65/M308 SITE 17; M303's 11th mention = end cmp @51dcfd.
- HARNESS `python3 -u scripts/m320_mutate.py` -> **26/26 + 1 NO-OP**, digest 0d18a3d23b3e94b4 (`evidence/m320_mutate.txt:27-28`); selftest 4/4 (`evidence/m320_mutate_selftest.txt:5`). 12 data + 11 code + 2 algo + NO-OP. MU21 retarget: 0x2034 = last SITE owner -> {G2,G3}. 1 crashed debug run (fold eval) fixed; 2+2 clean invocations (pre/post review).
- BLIND: 61 imm loads (6x blk1+0), 3293 neg-disp<=20bc (lea-pairs +1e0/+18/+1478 pinned). OPEN: game nouns; ds:0x985afc; 0xdfbe41; tail semantics; save-carry. Skill session-discipline.md rsynced from live (chain 1 edit). Review #321 triaged in PR reply; digest re-measured.
- MERGED 2026-11-19: #321 squash **93c25fe** on main. Land commit b8f71af = append-only NEXT_PROMPT result line (parallel-protocol fix) + tracked ai_review JSON; gate GREEN 0 warn, CI gate pass 14 s, review_lint PASS (7 V rows); acceptance 3rd invocation byte-identical pre-merge. Strata review 4 P1+4 P2 triaged in one reply (3 P1 dismissals independently re-verified by orchestrator). This note: docs/m320-merged.
