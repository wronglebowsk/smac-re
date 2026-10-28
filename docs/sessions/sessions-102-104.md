# Session notes archive — sessions 102-104

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 102 (2026-10-26) — correction to Session 101

The readiness oracle has **15** unit cases, not 13: two horizon cases (`tight horizon is flagged`,
`roomy horizon is not`) were added after the session-101 notes were written, so the notes quoted a
stale count. `python3 scripts/test_accept_ready.py` -> `PASS 15/15 readiness cases` (re-run before
this commit). No code changed; `SESSION_NOTES.md` and `NEXT_PROMPT.md` now say 15/15.

## Session 104 (2026-10-26) — M64: THE ACCRUAL PHASE IS MEASURED AND AN ARRIVAL IS ATTRIBUTED BY THE PAYMENT, NOT BY `ds:0x8f0d60`. ACCEPTANCE PASS on two real invocations.

Branch `milestone/m64` off `origin/main` (`5c18670`, M62B #61). Session 103's M63 work is still
**unmerged** on `milestone/m63`, so this branch does not carry its instrument or its `NAMED.md`
edits; the two traces its findings rest on were copied forward (`git checkout milestone/m63 --
evidence/trace_m56_build_20261026_181701.jsonl evidence/trace_m56_build_20261026_182354.jsonl`)
because the gate's citation check requires cited paths to resolve in the tree.

### What changed (harness only — no threshold, floor or economic term moved)

`scripts/m56_build.py`:
- **`accrual_phase(bases_now, prev_after)`** — a window's after-snapshot and the next
  window's before-snapshot are the SAME ROUND read twice, and the engine plays in the gap, so a
  minerals delta of exactly `+0xd0` between them IS this round's add (0x4ef7f6). `predict()` now
  takes `accrued=` (names) and adds income only when the add has not already landed; every
  prediction row carries `income_added` / `accrued_already`, and every window logs an
  `accrual_phase` event with `prev_after / before / gap_delta / income / already_accrued`.
  This is the fix for session 103's run-2 FAIL (`8 + credit 1 - price 9 = 0, observed 8`): in
  `evidence/trace_m56_build_20261026_181701.jsonl` Korolev Center read 7 at r1-after and 8 at
  r2-before (income 1), so the old `income_first=True` double-counted and predicted a payment at
  r2 that never happened (storage 8 -> 8); r3 is where it really happened (8 + 1 - 9 = 0).
- **F1 attributes by the PAYMENT, not the pointer.** An arrival missing from the after-snapshot is
  accepted when this window's minerals show the payment (`after == before + credit - price`) AND
  the unit reads back — either from a same-round re-read of the unit array (new
  `arrival_reread` event, bounded 2 s, stops the instant the year changes) or from the next
  window's before-snapshot, which is that same round read later. `ds:0x8f0d60` is reported in the
  detail and used as evidence by nothing: it was measured insufficient (r7 of
  `evidence/trace_m56_build_20261026_182354.jsonl` paid 7 -> 0 with the pointer naming Korolev
  Center and 2 of our units on (29,42); r8's before-snapshot, same round y2159 rnd59, has 3).
  The re-read compares **counts**, not key presence — a garrison of the same `(x,y,type,owner)`
  already sits on the base tile, so "the key is in the snapshot" says nothing.
- **New floor, not a weakened one:** the gap between a window's after-snapshot and the next
  window's before-snapshot is now searched for unexplained ORDER-0 arrivals on our bases too
  (`rN gap to the next window: ...`), because F2 diffs before -> after only and the attribution
  above moves arrivals into that gap.
- `credit_of` is computed once per window (0 when already accrued) and shared by the attribution
  and the F3 mineral identity, so the two cannot disagree.

`scripts/test_m56_predict.py` -> **`PASS 19/19 production-prediction cases`**: case 18 is the
measured already-accrued snapshot (ONE variable, the accrued set: gate 8+1=9 ARRIVES vs gate 8
does not); case 19 pins `accrual_phase` on the measured pairs (7->8 with income 1 = the add;
8->8 = not yet; +1 with income 0 = not the add, the add is gated `d0 > 0`; +3 with income 2 =
unmeasured, so the income term stands rather than guessing).

`scripts/m64_mkfixture.py` (new) rebuilds the run-layer fixtures from committed traces:
`python3 scripts/m56_build.py --fixture scratch/m64/fixture_paid_readback.json` -> **exit 0**
(r7+r8 of the run-3 trace VERBATIM — the window pair session 103 failed on);
`--fixture scratch/m64/fixture_paid_no_readback.json` -> **exit 1** (same two windows, the paid
unit absent from every read: a paid window whose unit never reads back is the guard shape, not a
race); `--fixture scratch/m61/fixture_defer_ok.json` exit 0, `--fixture scratch/m56_fixture_bad.json`
exit 1, `test_walk_diff.py` 37/37, `test_classify.py` 17/17, `check_classes.py` 17/0.

### CONFLICT reported, not silently picked

The pick said "keep `scratch/m61/fixture_beat_visit.json` failing (exit 1)" AND "a paid window
whose unit appears only in the NEXT read must verify". Its own new rule makes that impossible:
the original beat_visit IS a paid window whose unit appears only in the next read (r0 minerals
8 -> 0 with income 1 and price 9, unit present at r1's before-snapshot) and its only discriminator
was the pointer, which session 103 measured insufficient. Under the new rule it **passes**
(`--fixture scratch/m61/fixture_beat_visit.json` -> exit 0 with the M61 file). Rather than keep a
green file named "must fail", `scripts/m64_mkfixture.py` rebuilds it in place — same path, same
expectation, new discriminator (the paid unit removed from every read) -> **exit 1**. The pointer
value is kept in the data and no longer means anything.

### The acceptance — two real invocations, both PASS, plus the read-backs

1. `python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold`
   (after `SMAC_SAVE='m54b_clean.SAV' scripts/m54a_load.py --relaunch` -> `m54g_prep.py` ->
   `smac_play.py --turns 1` -> `2150->2151 OK` (`evidence/trace_t_20261026_194949.jsonl`) ->
   `m57_ui_enqueue.py --base-index 18 --cell-item 2
   --inserts 1` -> `pending=1 head=2 slots=[2,2,0,0,0,0] minerals=2 d0=2`) ->
   **`PASS production prediction: 2 verified unit arrivals over 10 boundaries ... queue filled by
   the GAME's BUILD UI (0 memory writes), paid by income at 2/round`**, `ACCEPT_EXIT=0`,
   52 checks all ok, `positive predictions 2/2 verified; boundaries 10/10`,
   `evidence/trace_m56_build_20261026_195136.jsonl`. **Read back:** Korolev Center paid at r3
   (minerals 8 -> 1 = 8 + 2 - 9) and at r7 (7 -> 0 = 7 + 2 - 9); our units on (29,42) went 1 -> 2
   -> 3, and WHERE each reads back is the whole point: the r3 payment's unit is NOT in r3's
   after-snapshot (tile still 1, orders [2]) and IS at r4's before-snapshot (tile 2, orders
   [0, 2]), while the r7 payment's unit is already in r7's own after-snapshot (tile 3, orders
   [0, 2, 2]). **The r3 arrival is the session-103 failure shape and it was ATTRIBUTED, not
   tolerated:** the check detail reads
   `observed net 0 of that tuple on the base tile; ATTRIBUTED ... this window's minerals show the
   PAYMENT (8 + credit 2 - price 9 = 1, read back) ... ds:0x8f0d60 named Korolev Center at the
   after-snapshot and is not evidence either way (measured insufficient)`. Under M61's rule that
   window FAILED the run.
2. The same command after the re-read was changed to compare counts (the only code change after
   run 1, so the shipped code is the code that printed PASS; its reload turn is
   `evidence/trace_t_20261026_195910.jsonl`, `turn 0: 2150->2151 OK`): -> **`PASS ... 2 verified unit
   arrivals over 10 boundaries`, `ACCEPT_EXIT=0`**, 56 checks all ok,
   `evidence/trace_m56_build_20261026_200045.jsonl`. Read back: payments at r3 (8 -> 1) and r7
   (7 -> 0), tile counts 1 -> 2 (r3-after, order 0 present) -> 3 (r7-after, order 0 present); both
   arrivals were observed directly, so no `arrival_reread` event and no attribution was needed.

**Said plainly:** in BOTH PASS runs every `accrual_phase` row had `gap_delta = 0`
(`evidence/trace_m56_build_20261026_200045.jsonl`: r1..r9 all `prev_after == before`), so the
accrual fix was **inert live** this session — it is exercised by cases 18/19 and by the replayed
run-2 trace, not by the acceptance. The attribution fix was exercised live exactly once, at r3 of
`..._195136.jsonl`. Two clean PASSes with the fix inert are not proof the accrual fix is right on
a live box; they are proof it does no harm there.

### Also measured this session (cheap, load-bearing)

- The box **stalls rather than auto-plays when an actionable unit exists**: year 2162 round 62
  `cur_player 3` unchanged across three reads 4 s apart (`n_units` 67 all three); three `Return`
  presses moved it 2162 -> 2164 and Korolev bought (minerals 5 -> 0, credit 2 -> 1). Session 103's
  "the box auto-plays while nothing drives it" is true only while nothing needs orders.
- `accept_ready.py`'s screen gate **flaked**: 8 consecutive `classify() == 'unknown'` verdicts on a
  frame that `vision_analyze` shows as the plain tactical HUD (MENU / COMMLINK / TURN COMPLETE /
  unit panel / `Mission Year 2164`), and 3 of 6 samples of the same screen classified `hud`
  (`scripts/smac_play.classify(words, region_colors(png), png)`). The map labels OCR as garbage
  (`UniversitKBratziew Center`) whenever the map is animating. Not a modal. The run itself was
  unaffected (it presses Return every 2 s whatever the screen says).
- Korolev Center's array index moved 18 -> 17 -> 18 again across the session; both enqueue
  attempts located it BY NAME and the `--base-index` passed to `m56_build.py` was re-read every time.

### Open

- Whether the accrual fix is right on a live box (see "Said plainly"): needs a run whose windows
  actually straddle an accrual — `income 1` bases (the 2164 box) produce that shape, the `income 2`
  reload does not.
- `accept_ready.py`'s screen gate is an OCR coin-flip on animated HUD frames; it blocked 14 reads
  this session and all 14 were the plain HUD. Either re-freeze until a known token reads, or stop
  treating `unknown` as a modal.
- Still open from M63 (untouched): which slot the BUILD UI's INSERT writes (needs an enqueue with
  two DIFFERENT type ids — every chooser value seen so far was 2); who writes `DAT_0068cbb0` and
  when it is stale; why `0x5a73f0(2, 3, Korolev)` returns 1.
- `milestone/m63` still carries the pop instrument (`m63_pop.py`), the `0x94de84` count-byte
  correction and the 384/386 identity-crossing finding with no PR. M64 did not merge it.
- Evidence 25.5 MB of the 30 MB gate FAIL line (warn band 20).

### Next pick

M65, cheapest first: (a) make `accept_ready.py`'s screen read re-freeze until a HUD token lands
instead of trusting one OCR pass (measured flake above; no game time needed), then (b) one run on
an `income 1` base — the shape that produced the double-count — so the accrual fix gets its live
case, then (c) the two-enqueue DIFFERENT-type-id test that finally says which slot INSERT writes.
