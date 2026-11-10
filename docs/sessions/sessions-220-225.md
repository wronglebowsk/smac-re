# Session notes archive — sessions 220-225

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 220 (2026-11-10, BUILD fire, B8 PASS 10/10) - the save-WRITE leg: a .SAV recomposed byte-exact from the state model
- track_mode printed BUILD -> rung B8 written into `BUILD_SPINE.md` FIRST (R2's save-WRITE leg
  chosen over the new-game leg: no recorded initial-state trace exists to parity-check against,
  and grading rule 2 forbids inventing expected values). ZERO box time; the box was never touched.
- `sim/savewriter.py`: `build_image(sv)` recomposes the container from the `sim.save` layout
  constants with the modeled classes composed from the model (version, counts, year@84,
  cur_player@800 via the M242 block identity, turn_flags@60 bit 1, own player@808, map dims,
  unit-record x/y) and declared pass-through bodies (blocks A/B, small table, 16,000 section,
  middles, grid, region map, tail/trailer, un-modeled record bytes).
- ACCEPTANCE: `python3 -m sim.selftest --b8 programs/saves/m54b_clean.SAV programs/maps/planet.MP
  --turns 5` -> **PASS B8: 10/10 gates** (`evidence/b8_savewrite.txt`). Numbers: identity
  round-trip byte-exact on 242,539 B; `decode_save.py --sections --anchors` tables identical;
  B3-pressed year 2150->2155 re-parses with the diff confined to modeled bytes (1 B, year low
  byte); move lands exactly in record 0's x-bytes at offset 222,783; RIVALS FAIL: pure re-emitter
  carries the old year, UNIT_LEN+4 breaks identity (242,807 B); two runs sha256 74d0f44ab9b9290b;
  `python3 -m sim.savewriter` exits 0.
- INVOCATION 1 FAILED ON THE GATE, not the writer: a cross-file map-dims equality vs planet.MP was
  a false premise - m54b_clean is a 64x64-map save while planet.MP is the 80x80 family (same
  pairing B6/B7 used; the .MP carries the rules, not the dims). Invocation 2 replaced it with a
  dims re-read against the save's own bytes; identity arbitrates the layout constants regardless.
- OPEN: R2 legs left: the new-game leg (needs the init-state rules - a census pick) and minimal
  UI; then R3 golden-trace parity. Static ANALYSE picks unchanged: (b) row-family layout
  0x94e8a8/0x94e5a8/0x94e7a8, (c) who reads regions >=128; box pick (dialog +0x4c dispatcher)
  unchanged. Next: `python3 scripts/track_mode.py` (3 ANALYSE fires, then B9).

## Session 221 (2026-11-10, ANALYSE static, M279 PASS 7/7) - the row-family layout: e8a8 rides the same fold as eaa8 (nested counter family), byte arrays index block*8380+region, e9a8 is read-only
- track_mode printed ANALYSE (analyse_since_build=0) -> pick (b): the row FAMILY
  layout (0x94e8a8 written 0x51df3d by the same fold + the e5a8/e7a8 arrays,
  whole per-block layout image-wide). ZERO box time; the box was not touched.
  `python3 scripts/m279_row_family_layout.py` -> **SUMMARY M279: 7/7 gates PASS**
  (`evidence/m279_row_family.txt`). Reuses the m276 evaluator via the m277 slice.
- ANSWERS: (G1) e8a8's ONLY writer 0x51df3d (FUN_0051dcb0) is reached through the
  SAME fold chain as the eaa8 store - eax = 8380*b + 2*s at both, eax untouched
  between them (0 intervening writers). (G2) the three stores are a NESTED counter
  family: e8a8 UNCONDITIONAL (every walked tile), eaa8 behind {cl&0x18==0} +
  {[edi+5]&0xc0<0x80} + {[edi+8]&0x20==0}, eba8 behind those PLUS {ch&0x10} - 4
  branches 0x51df49/59/5f/6e all target 0x51df77. (G3) e8a8's ONLY reader
  0x45c088 (FUN_0045a920) computes 8380*[ebp-0x34] + 2*[ebp-0x64] via
  `imul eax,eax,0x20bc` - the per-block fold form, rival "block-0-only read"
  refuted (no 8380 term needed there). (G4) the FUN_00556690 ENTRY fold
  (0x556699-0x5566bc) evaluates to edx = 8380*arg and is stored to [ebp-0xc] -
  the BYTE-lane base: e5a8/e628/eca8/ed28/eda8 index block*8380 + region*1, NOT
  the 2*region word form. (G5) image-wide census: 13 bases 0x94e4a8..0x94ee28,
  12 gaps all in {0x80,0x100}; 7 pure-WORD bases (e4a8,e6a8,e8a8,e9a8,eaa8,eba8,
  ee28), 5 pure-BYTE (e5a8,e628,eca8,ed28,eda8), e7a8 mixed 14B/13W = WORD with
  byte sub-accesses (M256's "e7a8 is WORD" stands). (G6) e9a8: 2 sites, ZERO
  writers, both readers; 0x568038's chain evaluates to (30,64,0) NOT (8380,2,0) -
  read-only, different index idiom (OPEN lead, not forced into the fold family).
- ACCEPTANCE: `python3 scripts/m279_row_family_layout.py` -> `SUMMARY M279: 7/7
  gates PASS` (`evidence/m279_row_family.txt`). Registry: NAMED.md M279.
- OPEN LEAD (new, from G6): e9a8's readers 0x568038/0x5a9fd5 - two more chains
  with the SAME shape (15*X + 32*Y fold base) that are NOT the (8380,2,0) row
  fold; what walks them. Static pick (c) (who reads regions >=128) and the box
  pick (dialog +0x4c dispatcher) unchanged.

## Session 222 (2026-11-10, ANALYSE static, M280 PASS 7/7) - the e9a8 readers RIDE the block fold; M279 G6's "(30,64,0)" was a mid-chain window artifact
- Footing collision resolved: the s222 kickoff said "M279 committed NOTHING" - STALE. The
  s221 fire recovered after composing it: M279 committed a497fbf, PR #223, MERGED 05:06:52Z
  (commit 9067fc8). The repo decided: M279 was already merged; track_mode printed ANALYSE,
  and the repo's live pick was the s221 G6 open lead - the e9a8 reader chains. That became
  M280 (verified not-merged before start).
- ANSWER: e9a8 is NOT a "different index idiom". BOTH readers evaluate to the per-block
  WORD fold 8380*block + 2*region:
  - 0x568038 (FUN_0055f650, AI hub): edi = [ebp-0xc] = OWNER byte (sole writer 0x55f71d,
    BYTE[52*edi+0x933286] = unit+14 owner, M278). Chain: mov edx,edi; shl edx,6; add edx,edi
    = 65*edi; lea ecx,[edi+edx*2] = 131*edi; shl 4 = 2096*edi; sub = 2095*edi; lea
    edx,[eax+ecx*2] = eax + 4190*edi; load [edx*2+0x94e9a8] -> 8380*block + 2*region.
  - 0x5a9fd5 (FUN_005a90a0): edi = [ebp+0xc] (arg) = block; edx = region loop counter
    (mov edx,1 @0x5a9f85; inc @0x5a9fe6; back-edge @0x5a9fed); ecx = edx + 4190*edi -> same.
  - G4 COMPUTES the artifact: M279's window [0x56802b,0x568035) with FREE atoms gives
    edx = (30,64,0); substituting the excluded seed (edx := 65*edi) yields 4190*edi = the
    same 8380 stride. M279 G6 opened its window INSIDE the chain, after the fold seeds.
- ACCEPTANCE: `python3 scripts/m280_e9a8_fold.py` -> `SUMMARY M280: 7/7 gates PASS`
  (`evidence/m280_e9a8_fold.txt`). Registry: NAMED.md M280; M279's e9a8 row patched in
  place (OBSERVED -> V (bytes), cites M280).
- OPEN: static pick (c) who reads regions >=128 (loop bound 0x80 vs counts to 338); box
  pick (dialog +0x4c dispatch) unchanged. Chain: exactly one pending smac-re job = s223.

## Session 223 (2026-11-10, BUILD fire, B9 PASS 7/7) - R3's golden-trace pairing: the original exe's own 40-turn m54b_clean.SAV run pairs 41/41 snapshots through the B3 engine
- track_mode printed BUILD (analyse_since_build=4) -> B9 rung written into `BUILD_SPINE.md` FIRST (chose
  R3's golden-trace pairing over R2's new-game leg: exactly the "no recorded initial-state trace" problem
  B8 already flagged - the new-game leg has nothing to parity against, and grading rule 2 forbids inventing
  expected values. What R3 needs exists: evidence/trace_m54b40b_20261024_212833.jsonl is the ORIGINAL
  terran.exe running m54b_clean.SAV itself, 40 TURN-COMPLETE presses, per-turn state_before/state_after
  snapshots of (year, cur_player, turn_flags, n_bases); the sibling m54b40 wedged at 30 rows).
- `sim/parity.py`: load the save, press the B3 engine the trace's OWN 40 turns, pair every recorded
  snapshot against the emitted state sequence as an ordered subsequence - zero tolerance on the recorded
  side (the m30 law). Gates: trace shape (40 consecutive rows), pair-chain (before(0)==save start,
  before(t)==after(t-1) all 40), snapshots-covered (41/41, 0 missing), year-before == 2150+turn all 40,
  BOTH RIVALS FAIL (reversed-order walk and year_after=0 edge each miss the (2190,7,2) year-fire witness
  - the same snapshot pins the walk direction AND the year edge), frontier-declared, two-runs sha256.
- ACCEPTANCE: `python3 -m sim.selftest --b9 programs/saves/m54b_clean.SAV` -> **PASS B9: 7/7 gates**
  (`evidence/b9_golden_parity.txt`); `python3 -m sim.parity --sav programs/saves/m54b_clean.SAV
  --out /tmp/b9_report.json` -> exit 0, report blob sha256 5af9cb48f597a0b7. Final engine state
  (3, 0, 2190) = the human phase after 40 presses, matching the recorded last year 2190.
- FINDING (declared, not a gate input): n_bases. The sim has no AI base-founder, so the model holds the
  save's constant 18 while the recorded game grows to 26 (delta +8 over 40 turns). Frontier recorded in
  the report + evidence; open as a census pick (who writes the base array / founds AI bases).
- Trap dodged: the first subsequence prototype double-counted boundary states (before(t)==after(t-1)
  appeared at 80 keys) - the paired sequence is before(0) + the 40 afters, 41 distinct states. tf masked
  to bit 0x2 (recorded turn 39 reads 0x100002 - the engine models only TF_CYCLE). One gate em-dash'd at
  the sanity pass - cleaned before commit.
- OPEN: static pick (c) who reads regions >=128; box pick (dialog +0x4c dispatcher) unchanged; new:
  the AI base-founder census (n_bases 18->26). Chain: exactly one pending smac-re job = s224.

## Session 224 (2026-11-10, ANALYSE static, M281 PASS 7/7) - nobody reads region ids >=128 because the generator caps the id space at 0x7f; the 338 is the coarse-map CELL count, not an id space
- track_mode printed ANALYSE (analyse_since_build=0) -> static pick (c): "the loop bound 0x80 never
  reaches regions >=128 while counts go to 338 - what reads region 128+?". ZERO box time; box not
  touched (terran.exe pid 3820435, no gdb, state read via pgrep only).
  `python3 scripts/m281_region_id_cap.py` -> **SUMMARY M281: 7/7 gates PASS**
  (`evidence/m281_region_id_cap.txt`).
- ANSWER: NOTHING reads a region id >=128 because such an id CANNOT EXIST. The region generator
  FUN_0058d390 uses two band counters (shard_015.c): land ids 1..0x3e (clamp uVar12=0x3e), water ids
  0x41..0x7e (clamp uVar12=0x7e), and when a band fills, the smallest region is relocated to the
  overflow slot uVar12+1 = 0x3f/0x7f (G1: clamps + `uVar12 + 1` idiom + the 0x5f border formula all
  in the body). Largest assignable id = 0x7f (127) < 0x80, so the `cmp e?x,0x80` loops at 0x556737/
  0x558b1c (both FUN_00556690) cover the WHOLE id space on every map size - M251's "128 entries =
  the whole id space" STANDS.
- The "338" that seeded the pick is the COARSE MAP's byte count, ((W+4)/5+1)/2 * (H+4)/5 = 91/128/338
  for 64/80/128 (G4, triad computed from the accesses FUN_00582340/2360 `(x>>1) + (Rw>>1)*y`), i.e.
  the number of coarse CELLS, not region ids. The count global DAT_0092ada4 has exactly 4 refs and
  they are alloc (x2) + file-write + file-read in shard_014 (G3), and an image-wide scan finds NO
  cmp against 0x152 (338), NO *0x152 scale, NO cmp against DAT_0092ada4 (G7) - no loop in the image
  is bounded by the cell count. The per-region table DAT_00989ce0 save section is 3584 B at stride
  0x1c = EXACTLY 128 rows (G6), consistent with a 128-slot id space. Tile-label census over 2 maps +
  4 saves: max labels 0x7f (planet.MP's border band!), 0x48 (planetx), 0x46 (saves); zero labels
  >= 0x80 in any file (G5).
- ACCEPTANCE: `python3 scripts/m281_region_id_cap.py` -> `SUMMARY M281: 7/7 gates PASS`
  (`evidence/m281_region_id_cap.txt`). Registry: NAMED.md M281.
- Corrections to prior footing: the s213-era "region counts 128/338 EXCEED the 94-slot row" framing
  conflated the coarse-map CELL count with the region ID space; M274's answer (the loop is never
  clamped, bound is constant 0x80) plus M281's (the id space itself is capped below 0x80) together
  fully close the row-cap question - the scaled-read overflow M274 measured (regions 94..127 read
  the sibling array) is the ONLY big-map artifact, and it is the 0x80 loop walking ids that DO exist.
- OPEN: static pick (c) CLOSED. Remaining: box pick (dialog +0x4c dispatcher), the AI base-founder
  census (B9 frontier, n_bases 18->26), the 64x64 odd-Rw accessor stride quirk (M247's Rw>>1 vs
  (Rw+1)/2 asymmetry is a live edge on 64x64, unreachable bytes are the file's 0xCD slack).
  Next fire: BUILD (analyse_since_build=1) = B10, R2's new-game leg - write the rung into
  BUILD_SPINE.md FIRST, then build it (sim/, runnable acceptance, no box time).

## Session 225 (2026-11-10, ANALYSE static, M282 PASS 7/7) - AI bases are founded by the SAME function as the player's: FUN_004e47d0, the only live count-incrementer; the sim has no founder because it has no action-dispatch leg
- track_mode printed ANALYSE (analyse_since_build=1) -> NEW pick (B9 frontier): "who writes the
  base array / founds AI bases (n_bases 18->26 over 40 turns)" - census pick, static-friendly.
  ZERO box time; box untouched (terran.exe pid 3820435, TracerPid 0, state read via pgrep only).
  `python3 scripts/m282_base_founder.py` -> **SUMMARY M282: 7/7 gates PASS**
  (`evidence/m282_base_founder.txt`).
- ANSWER: the base array is DAT_0095da10 (record stride 0x130 = 304 B = the .SAV 304-B stride),
  count DAT_00985af4, cap 0x200 = 512 slots. **FUN_004e47d0(faction,x,y) is THE founder and the
  ONLY live-game record creator**: guard `DAT_00985af4 < 0x200` (G1), `DAT_00985af4 = count+1`
  @0x4e484a, new record at &DAT_0095da10 + old_count*0x130 (x short +0, y +2, faction bytes
  +4/+5; G2), faction base counter DAT_0094e488[faction*0x82f] += 1 (0x82f*4 = 0x20bc = the
  M280 faction-record stride - the founder is where per-faction base counts come from).
  Exactly 3 callers (G3): FUN_004cca50 (the ONLY live vector), FUN_0059ce10 (sole caller
  FUN_005a0fa0 = new-game/scenario placement), FUN_0059ec90 (faction-create; called by
  FUN_005a0aa0, itself called by the AI mover FUN_00585720, the step executor FUN_00502cd0,
  faction-energy FUN_005208f0, ...).
- The LIVE entry splits into three same-founder legs (G5): player 'b' hotkey (FUN_00512450
  case 0x62 -> FUN_004d1280 -> FUN_004cca50 -> founder), the in-game ACTION DISPATCHER
  FUN_0052bce0 case **0x4408** -> FUN_004cca50 (the AI's founding rides this - the same
  dispatcher that drains the unit-action queues FUN_005262e0/FUN_00526e10 and executes the
  player's own move steps at case 0x4402), and the AI hub FUN_0055f650 -> FUN_004cca50
  (shard_014; first-base placement for a faction). So there is NO separate AI founder: the
  AI reaches the exact same FUN_004e47d0 through the same unit-action plumbing as the human.
- Count-global census (G4): DAT_00985af4 has EXACTLY 12 writer sites / 11 functions - the
  `+1` idiom exists ONLY in FUN_004e47d0 (0x4e484a) and in FUN_0059b830's scenario-table
  rebuild loop (0x59b842/0x59b8c3, a load-time 0x200-entry array reconstruction, not live
  play); the only decrement is 0x4e515d in FUN_004e4e10 (base destruction + compaction);
  every other site stores 0 (init/reset families) - 0x52283f is a bare store whose exe
  prelude `xor eax,eax; mov 0x985af0,eax; mov 0x985af4,eax` is verified from terran.exe
  bytes (Ghidra text drops it). Cap consistency (G6): founder guard 0x200 AND loader loop
  0x200 => 512 slots * 0x130 = 0x26000 bytes; the destruction compaction moves the LAST
  record into the freed slot (the m46e "base array reorders during a watch" observation).
- SIM GAP, now explained (G7): sim/ has no reference to the founder or case 0x4408; the B9
  frontier line stays DECLARED (model const 18 vs recorded 18->26). The B3 engine replays
  TURN-COMPLETE presses and never instantiates unit actions, so the founding leg that grows
  n_bases in the real game simply does not exist in the model. A future BUILD rung can add a
  minimal founder leg (colony-pod action -> new base record) if parity of n_bases is wanted.
- ACCEPTANCE: `python3 scripts/m282_base_founder.py` -> `SUMMARY M282: 7/7 gates PASS`
  (`evidence/m282_base_founder.txt`). Registry: NAMED.md M282.
- OPEN (unchanged): box pick (dialog +0x4c dispatcher, box UP m54b_clean); the 64x64 odd-Rw
  accessor stride quirk (M247's Rw>>1 vs (Rw+1)/2, live edge worth a census). New: which of
  the three founder vectors (0x4408 dispatcher vs hub FUN_0055f650 vs the FUN_005a0aa0
  chain) the recorded AI actually uses per founding event - a live-dispatch question, only
  reachability is proven statically. Next fire: ANALYSE (analyse_since_build=2).
