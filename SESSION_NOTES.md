

Older sessions: `docs/sessions/sessions-100-100.md` (1 sessions). Read it only when a question reaches back before session ## Session 101.

## Session 101 (2026-10-26) — M62: **INSTRUMENTS, NOT RESEARCH. The box's dead shapes are now decided in one read, the brief is generated, and the evidence audit found that no trace could ever count as cited. NO prediction PASS this session — the one live run FAILED and the reason is now half-explained.**

**THE READINESS ORACLE (`scripts/accept_ready.py`, 15/15 unit cases).** Read-only; exit 0 = one of
our bases can carry the UI-queued acceptance, exit 1 = BLOCKED with the single cheapest fix, in
this order: screen class (a modal swallows every click AND every turn-end key) -> running gdb ->
evidence headroom (29 MB) -> per base `pending > 0`, `minerals < price`, `credit > 0` (the income
add is gated `d0 > 0`, so `credit <= 0` never accrues) -> TIGHT horizon when the gate is more than
`boundaries-2` rounds away. Proven on the live box in three states, one command each:
`BLOCKED … FIX: screen is 'dialog': press Return …` (an Operations Director "…not sufficient to
support Scout Patrol…" modal was up and had just swallowed two enqueues) -> `BLOCKED … FIX: enqueue
on University Base (idx 0)` -> after `m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1`
(`after INSERT 1 (try 1): pending=1 head=2 minerals=1 d0=1`) -> **`READY … RUN: scripts/m56_build.py
--ui-queued 0 --boundaries 10 …`, exit 0**. Rule cases: `python3 scripts/test_accept_ready.py` ->
**`PASS 15/15 readiness cases`**.

**THE LIVE RUN FAILED — recorded, not hidden.** `python3 scripts/m56_build.py --ui-queued 0
--boundaries 10 --timeout 400 --no-poke-hold` -> **FAIL**, `positive predictions 1/2 verified;
boundaries 10/10`, exit 1 (`evidence/trace_m56_build_20261026_165917.jsonl`). Three rows carry it:
r2 "predicted … observed net 0 of that tuple on the base tile"; r3 `pending 1 -> 0` with the slot
array `[2,2,0,0]` unchanged; r4 "queue held — head 2->384" while a second base read `386` in the
same window. Across every trace, **38/303** of our rows and **2804** rows overall hold a slot
outside `0..23` — so a queue slot is NOT reliably a type id and no global floor may demand it. The
run also lost University Base (`bases_ours` 2 -> 1, `units_ours` 9 -> 5); base death and the queue
anomaly share the same windows, so this is **CONFOUNDED**, written as such in NAMED.md.

**A LATENT BUG IN THE GATE'S CITATION CHECKER.** `evidence.load_cites()` matched
`png|log|gdb|txt|json|csv` — not `.jsonl` — so **no trace could ever count as cited**, and the
alternation order (`json` before `jsonl`) hid the first fix. After both fixes the audit reports
10 uncited files / 0.1 MB where it had claimed 578 files / 12.7 MB. New command
`python3 scripts/evidence.py audit [--delete]` (cites = docs AND `scripts/*.py`, so classifier
frames are safe): **deleted 396 uncited files, 27.7 -> 22.8 MB**, and `test_classify.py` still
**PASS 17/17** afterwards.

**FIXTURE TRACES NO LONGER POLLUTE EVIDENCE.** `m56_build.py --fixture X` writes to `$TMPDIR`
(`scratch/fixture_trace_*.jsonl`); evidence jsonl count 174 before and after the three fixture
cases (`defer_ok` 0, `beat_visit` 1, `bad` 1).

**THE BRIEF IS GENERATED (`scripts/session_brief.py`, ≤4 KB, `--write` -> `BRIEF.md`).** Verdict +
both bases + the tagged CONFLICTs + next pick + first commands + uncited evidence. `NAMED.md` now
carries three **`CONFLICT:`** lines (year store `0x51f554` vs `0x51f54f`; queued-count byte
`0x94dc84` vs `0x94de84`; pay `0x4f0ca6` vs the measured `0x4efedd`) which the brief prints
verbatim. Measured on the 125B for the fixed-cost argument: **596 tok -> 1.83 s prefill, 44,446 tok
-> 15.4 s** (0.345 ms/token) — the footing's size is not the problem, stumbling is.

**Open.** (1) What writes 384/386 into `+0x50` (two bases in one window). (2) Whether a dead/stale
base record is what those reads are. (3) The pop's real operand — pending decrements, slots do not
move, in two independent sessions now. (4) The support-disband path can eat a created unit, so
READY ≠ PASS (not modelled). (5) Box drifted: 1 base, 5 units, year 2174 r74 — reload before the
next acceptance. (6) `session_brief.py` prints only the FIRST line of each multi-line CONFLICT (the
wrapped continuation lines are not joined).

**Next pick (M63):** what writes 384/386 into `base+0x50`, and what the pop does to the slots —
reload first, then pop breakpoint + a watchpoint on one named base's `+0x50..+0x74`, two-three
boundaries, one variable per run.

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

## Session 105 (2026-10-26) — M65: THE SCREEN READ IS A LOOK LOOP, NOT AN OCR COIN-FLIP. The HUD has two rows and only the bottom one is stable.

### What changed (harness only — no threshold, floor or prediction term moved; `classify()` itself is UNTOUCHED, so the driver classifies exactly as before)

- `smac_play.hud_status_bar(words)` — a NEW pure function, `HUD_BAR = (548, 592)`: >= 3 tokens in
  the band AND (`mission` or a `ssion|sslon|sston|ismon|sshon` fragment or `year`/`tear`) AND (a
  4-digit 2000-2500 number or `year`/`tear` or `energy`). It returns its components
  (`nbar/mission/year/nums/energy/fire`) so a caller can print WHY it believed a frame.
- `accept_ready.py`: `look()` (one freeze: classify + the bar), `verdict(looks, confirm)` (PURE —
  the whole screen decision, unit-tested with no game and no OCR) and `screen_class(samples=4,
  confirm=2, gap=0.8)` which re-freezes until a verdict lands. `decide()` is unchanged except that
  an unresolved `unknown` now prints "freeze and look at the frame" instead of "press Return until
  it reads hud" — a frame with neither row is not a KNOWN modal and a blind keypress on it is a
  gamble. `--samples/--confirm` are CLI knobs; the read's evidence prints as a `SCREEN <class>:`
  line and as `screen_evidence` in `--json`. `session_brief.py` needed no edit (it calls
  `AR.screen_class()[0]` and `AR.decide`), and it inherits both fixes.
- New instruments: `scripts/m65_screen.py` (N freezes of the live screen, per-sample class +
  per-band tokens + load1; writes frames + `samples.json`, deletes its own `_3x` siblings),
  `scripts/m65_anchor.py` and `scripts/m65_signals.py` (candidate HUD signals measured over the
  saved classifier frames).

### The measurement that chose the fix

`python3 scripts/m65_screen.py --samples 8 --save /tmp/m65a` on ONE unchanged screen (terran.exe
alive, year 2161 round 61 `cur_player 3`, nothing clicked, no key pressed) printed
`CLASSES SEEN {"unknown": 5, "hud": 3} of 8 samples`. In the saved records
(`evidence/m65/before_8looks_samples.json`, frames `evidence/m65/sample_00_unknown.png:1`,
`sample_02_unknown.png:1`, `sample_04_unknown.png:1`, `sample_07_unknown.png:1` and the control
`sample_05_hud.png:1`): `TURN@416 COMPLETE@416` in samples 1, 5, 6 ONLY, while
`Mission@567 Year@567 2161@567` (+ the score row `1-1-1@581`, `Energy:@582`) is in all EIGHT.
The bar fragments too, differently: `evidence/m25_t7.png` OCRs the whole row as
`sisson@573 tear@573 zie@573` with NO year number, and `evidence/m54a/live_hud.png` as
`[esston@572 2388@572` — so the signal is written against the fragments, not the clean words.

### The pin — `python3 scripts/test_hud_bar.py` -> `PASS 26/26 hud-bar cases`, exit 0

18 frames + 8 look sequences. Fires on all 3 saved HUD frames and on the 4 live `unknown` frames;
**silent** on the base screen (4 bar tokens, none of them Mission/Year/number/Energy), the cdrom
nag (0 bar tokens), the LOAD confirm (14 bar tokens, none of them), the HELP browser (234 tokens in
the frame), the COMM pane and the artwork panel. On the 4 modals drawn OVER a still-drawn HUD
(quit prompt, `m54e/chooser_live.png`, `m54h/chooser_g60b.png`, `m54g/newbase_pane.png`) the bar
DOES fire — the case asserts the classify() NAME as well, because that is the only thing keeping a
chooser from being called `hud`: the signal is consulted only on a frame classify() already called
`unknown`, and every modal detector runs before classify() reaches that fall-through.
`verdict()` cases pin the semantics: a named modal in ANY look decides the screen and beats a
pending bar promotion; `hud` on any look is believed as before; the bar must fire in 2 of the 4
looks (consecutive or not) to promote an `unknown`; one bar-only look is NOT believed; 4 looks with
no row and no bar is still `unknown` and still BLOCKED — **the check was not weakened, the screen is
re-read.**

### The live read-back — the oracle no longer blocks a playable box on its screen

`python3 scripts/accept_ready.py` three times, 20:55:45 -> 20:56:46 (year 2161 round 61, both bases
pending 0, so the verdict stays BLOCKED on `pending 0 — not UI-queued` and the FIX line is the
enqueue): run 1 `SCREEN hud: look 1: classify() == hud (the TURN COMPLETE row read)` (21 s),
run 2 same (9 s), run 3 **`SCREEN hud: look 1: classify() == unknown, but the HUD's bottom status
bar read in 2 of 2 look(s)`** (31 s) — the promotion path exercised live: neither look read the
button row and the oracle still said `hud`. `python3 scripts/session_brief.py` at 20:56 prints
`screen hud` (the same script printed `screen unknown` and "press Return until it reads 'hud'" at
20:16 this session) and its FIX is now the enqueue.

### Still green (all with the command)

`test_accept_ready.py` **PASS 17/17** (two new cases: unresolved `unknown` blocks, a crashed screen
read blocks, both needle `m65_screen.py`); `test_classify.py` **PASS 17/17**; `check_classes.py`
exit 0 with **14 PASS + 3 SKIP** — `m15_hud.png`, `m15_mainmenu.png`, `m15_autolist.png` are gone
from `evidence/` (deleted in #3 `214f982`, pre-existing, not this session); `test_m56_predict.py`
**PASS 19/19**; `test_walk_diff.py` **PASS 37/37**; `m56_build.py --fixture` bad=1,
`m61/fixture_defer_ok`=0, `m61/fixture_beat_visit`=1, `m64/fixture_paid_readback`=0,
`m64/fixture_paid_no_readback`=1.

### Confounded, and said so

The 8-sample measurement ran while `top` showed 79.6% user / 0.0 idle on **4 cores**, load average
13-15 (`jellyfin` 85%, `winedevice` 38%, tesseract ~200%): one OCR pass went from the ~1 s in
`ocr_fast`'s own comment to ~70 s, and the classifier suites stretched from ~40 s to >20 min. When
jellyfin finished the same suites ran in ~3 min and all three `accept_ready` runs finished in 61 s.
**Per-sample load was not recorded in the first run** (`m65_screen.py` records `load1` now), so
"the flake rate rises with CPU contention" is a HYPOTHESIS — the flake and the load were both
extreme at the same time, and the read rate improved in the low-load window, which is not the same
measurement. Do not read one OCR pass as a fact on a loaded box.

### Open

- Whether the accrual fix is right on a LIVE box (unchanged from session 104): needs an `income 1`
  base whose windows straddle the add; the `income 2` reload makes both PASS runs `gap_delta = 0`.
- Which slot the BUILD UI's INSERT writes (needs one enqueue with two DIFFERENT type ids).
- Still open from M63, and `milestone/m63` still carries the pop instrument, the `0x94de84`
  count-byte correction and the 384/386 identity-crossing finding with **no PR**.
- `check_classes.py`'s default list names three frames that no longer exist; either restore them or
  drop them from DEFAULT (nobody has done either).
- The load hypothesis above: re-run `m65_screen.py` (it records `load1` now) at two different loads.
- Evidence 26.3 MB of the 30 MB gate FAIL line (warn band 20) — the 5 new `evidence/m65/` frames are
  0.8 MB of it.

### Next pick

M66, cheapest first: (a) the `income 1` live accrual case — `scripts/m56_build.py --ui-queued <fresh
idx> --boundaries 10 --timeout 400 --no-poke-hold` on a base whose windows straddle the add, and
report the `accrual_phase` rows; (b) the two-enqueue DIFFERENT-type-id test that finally says which
slot INSERT writes; (c) cheap: re-measure the screen read at a quiet load and at a loaded one.

## Session 106 (2026-10-26) — M66: WHICH QUEUE SLOT THE BUILD UI'S INSERT WRITES. ACCEPTANCE PASS on ONE real invocation — and the answer is not a slot index, it is a SORT.

### The acceptance (one invocation, exit 0)

`python3 scripts/m66_insert_slot.py --base-name "University Base" --item-a 194 --item-b 1 --trace
evidence/m66_insert_slot_cost_order.jsonl` -> **`PASS: exactly one layout explains both read-backs
— sorted_descending_cost (pending 4->5->6, ids stored (194, 1))`**, exit 0. University Base idx 0,
year 2161 round 61, minerals 1, `+0xd0` 0, chooser open on the same base the whole time:

| moment | pending `+0x4c` | slots `+0x50 ..` | evidence |
|---|---|---|---|
| baseline | 4 | `[2, 194, 193, 195, 192, 0, 0, 0]` | `evidence/m66_insert_slot_cost_order.jsonl:1` |
| after INSERT 194 (cost 3) | 5 | `[2, 194, 194, 193, 195, 192, 0, 0]` — landed at index **2** | `evidence/m66_insert_slot_cost_order.jsonl:6` |
| after INSERT 1 Formers (cost 2) | 6 | `[2, 194, 194, 193, 195, 192, 1, 0]` — landed at index **6** | `evidence/m66_insert_slot_cost_order.jsonl:7` |

Type-record cost bytes (`+41`, the byte `m58_price.py` prices from) read in the same run: 194 = 3,
193 = 2, 195 = 2, 192 = 2, 1 = 2, 2 = 1 (`evidence/m66_insert_slot_cost_order.jsonl:5`). The cost-3
item went AFTER the cost-3 entry already in the queue and BEFORE the cost-2 run; the second cost-2
item went AFTER the three cost-2 entries, not before them.

**THE ANSWER: INSERT does not write a slot index — it inserts into the queue REGION (slots 1 ..
`pending`, i.e. `base+0x54 ..`) by DESCENDING cost (type record `+41`), ties going after the
entries already at that cost, shifting everything from the insertion point right by one. The head
slot `base+0x50` is not a queued entry and INSERT never writes it — it read 2 before and after in
all four runs. `pending` (`+0x4c`) is the count of the region, so a queued entry `k` lives at
`+0x50 + 4k` for `k = 1 .. pending` and `+0x50` itself is never a queued entry.** The M57 doc line
"INSERT writes head `+0x50`, pending `+0x4c`,
slot `+0x54`" was a duplicate-value artifact: that run enqueued id 2 into a queue whose head was
already 2, so a head that was never written looked like a head that was.

### The run that refuted the rule the previous run had "passed" on

Four runs, one variable at a time (the item id and the queue state), same instrument:

- Korolev Center idx 17, pending 0, `[2, 2, 0, ...]` -> INSERT 194 -> pending 1 `[2, 194, 2, 0, ...]`
  -> INSERT 195 -> pending 2 `[2, 194, 195, 2, ...]`
  (`evidence/m66_insert_slot_run1_korolev.jsonl:6-7`). It printed **FAIL** then
  (`:11 matched: []`): the layout set written down that evening did not contain the rule that was
  actually happening. A FAIL that names no layout is the honest output; nothing was claimed.
- University, pending 0, `[2, 0, 0, ...]` -> 193 -> `[2, 193, 0, ...]` -> 195 -> `[2, 193, 195, 0,
  ...]` (`evidence/m66_insert_slot_university.jsonl:6-7`) — PASS on the five-rule set, but an EMPTY
  region makes "insert at the new pending index" and "insert by descending cost" predict the SAME
  array, so that PASS never could have established the rule. `scripts/test_m66_layouts.py` pins both
  of those cases (`measured_korolev_pending0`, `measured_university_pending0`) as two-match shapes.
- University, pending 2, `[2, 193, 195, 0, ...]` -> INSERT 194 (cost 3) -> pending 3,
  `[2, 194, 193, 195, 0, ...]`: the new entry went to index **1**, not to the new-pending index 3
  (`evidence/m66_insert_slot_third_fourth.jsonl:6`); then INSERT 192 (cost 2) went to index 4
  (`:7`). **This shape fits the sort rule and refutes the pending-index rule**, which is why the
  scorer now carries six rules and why the acceptance run was built to have a populated region.

### The chooser list moves under you (the reason cell -> id must be read with the chooser OPEN)

The same box, the same faction: the candidate array `DAT_009267e4` read `[192, 194, 193, 2, 0, 1,
195, 196, ...]` before the chooser was opened and `[192, 195, 194, 193, 2, 0, 1]` with it open
(`evidence/m66_insert_slot_cost_order.jsonl:6`, `cand_at_click`) — `0x596000` rebuilds and re-sorts
all 128 entries on every paint (NAMED). In all four runs the id the game stored equalled the array
entry at the CLICKED cell read at click time (`cell_entry` == the stored id), so there is no +1
shift; the session-105-era "cell 3 = Scout Patrol" mapping is only valid for the frame it was read
from. The instrument now refuses to map a cell from a pre-open read.

### The contested queued-count byte: settled, enqueue-side

`evidence/m66_insert_slot_cost_order.jsonl:10` — the per-faction byte entries that MOVED between
the before-snapshot and after OK: `de84[194] 2->3` and `de84[1] 0->1`, i.e. +1 at
`0x94de84 + 8380*owner + tid` for each type enqueued, and nothing at the same index in the sibling
array 512 B lower (`dc84[194]` and `dc84[1]` are absent from the diff; the `dc84[513]`/`dc84[706]`
entries in that diff ARE the same addresses, since `0x94de84 - 0x94dc84 = 0x200`). The Korolev run
shows the same pair from the other side: after OK there, `de84[194] 0->1` while `dc84[194]` stayed 0
and `dc84[2]` stayed 8 (`evidence/m66_insert_slot_run1_korolev.jsonl:8` — that run sampled only ids
193/194/2, so the 195 it also enqueued was never read). **`0x94de84` is the per-faction QUEUED
count**
(the pop decrements it at `0x4ef613`, M63's branch; the UI enqueue increments it, measured here);
`0x94dc84` is a different counter and the NAMED CONFLICT line about which one the pop touches is
gone. Mid-click the whole row reads one LOWER for every queued id (`:6` `row_delta`) and by OK it
is back with the new id added — read the settled state, not the click instant.

### Harness, and what it cost

`scripts/m66_insert_slot.py` (new) enqueues TWO different ids in one open chooser, re-reads the
candidate array with the chooser open, refuses an id that is 0 (unused slots read 0) or that the
queue already holds twice, prints the four byte-array row diffs, and scores the read-backs against
SIX rules each written down before the run, each a transformation rule with the stored id as a free
variable. `python3 scripts/test_m66_layouts.py` -> **PASS 10/10 m66-layout cases**, exit 0: the
three measured shapes, the acceptance shape, the four refuted layouts, the no-slot-moved shape, and
the single-id shape that two rules explain (the reason for the twice-held-id guard). Nothing was
weakened to pass: the first run FAILED by design, the second PASSed on a rule the third run
refuted, and the acceptance run is the one whose shape separates all six rules. Four enqueues left
the box UI-queued (University pending 6, Korolev pending 2) — no threshold, floor or economic term
moved, and the only memory writes are the M57 recipe's three enabling pokes.

### Confounded, and said so

The 194-into-University insert landed at index 2 under BOTH "descending cost, ties after" and
"ascending cost, ties before" for a duplicate id — the array `[2,194,194,193,...]` is the same for
both stories, so the tie direction is NOT established by that insert. It is established by the
cost-2 Formers insert (index 6, after the cost-2 run; ties-before would have put it at index 3) and
by the 192 insert in `third_fourth.jsonl:7`. Cost is the only key measured so far; the type-record
`+42` plan byte happens to order the same four ids in this faction, so "cost" and "plan" are not
separated by these runs — a base whose queue holds two ids with equal cost and different plan would
separate them, and none was available (only 192/193/195 share cost 2 and they differ in plan, so
their relative order does discriminate: it matches cost-ties-after and does not by itself rule out
plan-order).

### Open

- Whether the sort key is the cost byte `+41` or something that happens to order with it (the plan
  byte `+42`, or the chooser's own score). Not separated yet — see the confound above.
- Who writes the head slot `+0x50`, and what the disasm's `esi == 0` head store at `0x418b57` is for
  (it did not fire in any of the four enqueues; `pending` cannot be 0 after the increment at
  `0x418b0a`). The pending cap 9 (`0x418b05 cmp ecx,0x9 / jge`) is STATIC — read from
  `scratch/m574/text.txt`, never poked.
- `0x94dc84` is incremented somewhere (`0x4d2a25`, `0x4d2fa7` in the whole-`.text` dump) and the
  enqueue never touched it: what IS it?
- The type-name rows: live `+0` strings now read 193 `Synthmetal Garrison`, 194 `Impact Infantry`,
  195 `Impact Battery`, 192 `Impact Squad`; NAMED's M33-era rows say 193 Scout Rover, 194 Synthmetal
  Garrison, 195 Laser Squad. Tagged in NAMED, unresolved.
- Session 105's picks (a) the `income 1` live accrual case and (c) the quiet-vs-loaded screen
  re-measure: untouched.

### Next pick

M67, cheapest first: (a) separate the sort key — one enqueue pair with equal cost and different plan
(e.g. 192 vs 193, both cost 2, plan 0 vs 2) into a queue that already holds one of them, which
decides cost-vs-plan and the tie direction in one run; (b) the `income 1` live accrual case from
session 105; (c) cheap: the quiet-vs-loaded `m65_screen.py` re-measure.

## Session 107 (2026-10-26) — M67: THE QUEUE'S SORT KEY IS THE PLAN BYTE `+42`, NOT COST. ACCEPTANCE PASS on ONE real invocation.

### The acceptance (one real invocation, exit 0)

`python3 scripts/m66_insert_slot.py --base-name "Korolev Center" --item-a 193 --item-b 192
--rules sort_key --slots 12 --trace evidence/m67_sort_key_accept.jsonl` printed

    PASS: exactly one sort-key rule explains both read-backs — plan_desc_after
          (pending 4->5->6, ids stored (193, 192))

* baseline read first (`before` row): pending 4, slots `[2, 193, 194, 195, 192, 2, 0, 0, 0, 0,
  545, 0]`, minerals 3, `+0xd0` 2; plans 193→2, 194→1, 195→0, 192→0, costs 193→2, 194→3, 195→2,
  192→2 (type-record bytes `+42` / `+41`, read live).
* `shape_gate` row, computed from the BASELINE before any click: the eight rules predict slots
  `{1, 2, 5}` — `{1: cost_desc_before, cost_asc_before, plan_desc_before, plan_asc_before}`,
  `{2: cost_asc_after, plan_desc_after}`, `{5: cost_desc_after, plan_asc_after}`. The script
  refuses to run a shape whose eight predictions all agree, so the discrimination is earned
  before the first click, not claimed after the last one.
* INSERT 193 landed at region slot **2**, in front of 194 (plan 1): `plan_desc_after` predicted 2,
  `cost_desc_after` predicted 5 (`insert_a` row, `after 193` line).
* INSERT 192 (plan 0) landed at slot **6**, behind 195 (plan 0) — ties stay ahead
  (`plan_desc_after` predicted 6; `plan_desc_before` predicted 1).
* read back after OK: pending 6, slots `[2, 193, 193, 194, 195, 192, 192, 2, 0, 0, 545, 0]`, and
  the per-faction queued-count bytes moved exactly +1 for the two types enqueued
  (`de84[192] 3->4`, `de84[193] 3->4`; `dc84[704]/[705]` are the same addresses, 0x94de84 -
  0x94dc84 = 0x200). Cell -> id was resolved with the chooser OPEN (`cand_at_click [192, 195, 194,
  193]`, `cell_entry` 193 at cell 3 and 192 at cell 0, the selection guard matched both clicks).

### Two earlier runs the same instrument made (both real, both kept, both printed FAIL at the time)

1. **University Base, pending 6 -> 7 -> 8** (`evidence/m67_sort_key.jsonl`): 193 (plan 2, cost 2)
   landed at slot **1**, IN FRONT of two 194s (plan 1, cost 3), while `cost_desc_after` predicted
   7 and `plan_desc_after` predicted 1. Then 192 went to the end. This is the live refutation of
   M66's cost claim: a cost-2 item jumped over two cost-3 entries.
2. **Korolev Center, pending 2 -> 3 -> 4** (`evidence/m67_sort_key_korolev.jsonl`): 193 landed at
   slot 1 ahead of 194 (plan 1) and 192 went to slot 4 behind 195 (plan 0) — the same verdict as
   the acceptance, on a different base and a different shape.

Re-scored under the corrected shift model (below), each of the three runs' arrays explains exactly
one rule, and it is `plan_desc_after` in all three. No threshold, floor or economic term was moved
between the FAILs and the PASS; the rule set was written down before the first run and never
touched after it.

### The harness finding that made the PASS possible (a READ model, not a hypothesis)

The INSERT shift is **capped to the 10-slot queue array `base+0x50 .. base+0x74`** = head + 9
region slots — the same 9 the enqueue refuses to exceed (`0x418b05 cmp ecx,0x9 / jge`, static from
`scratch/m574/text.txt`). Stale ids inside the array are pushed ALONG with the shift, the value in
slot 9 is pushed out of the array, and the dword at queue slot 10 (`+0x78`) does not move: it read
**545** on Korolev Center in every row of both Korolev traces and **9225** on University Base in
every row of the University trace, while slots 1..8 shifted right by one around it. Korolev's
stale id 2 at slot 3 moved to slot 4 on the first INSERT and to slot 5 on the second.

My first model (shift the whole read window) predicted slot 10 moving; my second model (shift only
slots 1..pending) predicted the stale 2 being overwritten instead of pushed. Both made the same
measured arrays explain NOTHING, which is what the two FAILs actually said.
`scripts/m66_insert_slot.py` now scores with the capped model (`QUEUE_CAP = 10`) and forces
`--slots >= 10` in `sort_key` mode so the boundary is visible; the M66 layout rules keep the
uncapped model, because with an 8-slot window and a zero tail the two forms are indistinguishable
— which is exactly why session 106 could not see this. The only memory writes in all three runs
are the M57 recipe's three enabling pokes (cursor home, `SEL_G`, orders mode).

### Pinned

* `python3 scripts/test_m67_sort_keys.py` -> **PASS 15/15 m67 sort-key cases**: each of the eight
  rules is the UNIQUE explanation of a shape it produced; one shape no rule explains selects
  none; both measured read-backs are pinned; three shape-gate cases (the University baseline, the
  Korolev acceptance shape, and the empty region, whose eight predictions all land in slot 1 and
  which the gate therefore refuses).
* `python3 scripts/test_m66_layouts.py` -> PASS 10/10 unchanged. `test_accept_ready.py` 17/17,
  `test_m56_predict.py`, `test_walk_diff.py`, `test_classify.py` untouched.

### Scope, said plainly

This separates COST from PLAN and refutes cost. It does NOT separate `+42` from the type-record
bytes that happen to rank ids 192/193/194/195/2 the same way: several name bytes
(`+0,+1,+3,+4,+6,+15,+16,+17,+18`), `+37`, and `+43` read ASCENDING all predict the same two
landing slots. It DOES refute `+7, +9..+14, +33, +38, +41 (cost), +45, +48, +50, +51`. Live type
records (stride 52, `+0` name): 192 Impact Squad cost 2 plan 0, 193 Synthmetal Garrison 2/2,
194 Impact Infantry 3/1, 195 Impact Battery 2/0, 1 Formers 2/9, 2 Scout Patrol 1/3, 0 Colony Pod
3/8; ids 196+ read all-zero.

### Confounded, and said so

Nothing in the acceptance changed two things at once. The three runs differ from each other in
base AND in queue contents, so they are three observations of the same rule, not one observation
three times; and the University/Korolev "FAIL -> explains one rule" change is a re-reading of the
SAME bytes under a corrected read model, not a new observation — which is why the acceptance is
the third run, on a shape neither earlier run had used.

### Open

* plan-vs-name-order is NOT separated (see Scope). Id 1 `Formers` (plan 9, name `F`) against 194
  `Impact Infantry` (plan 1, name `I`) separates them in one enqueue.
* who writes the head slot `+0x50`, and what the disasm's `esi == 0` head store `0x418b57` is for
  (it did not fire in any of the seven enqueues; the head read 2 every time).
* what `0x94dc84` IS — the enqueues never touched it at its own indexing (only `dc84[704]/[705]`,
  which are `de84[192]/[193]` under another name); still incremented at `0x4d2a25`/`0x4d2fa7`.
* the `income 1` live accrual case (every M64 PASS window had `gap_delta = 0`); the quiet-vs-loaded
  `m65_screen.py` re-measure; `check_classes.py` still names three frames deleted back in #3;
  the type-name CONFLICT in NAMED.md.
* **M63 is still NOT merged** (no PR; `milestone/m63` carries the pop instrument and four findings,
  its queued-count half confirmed by M66).

### Box at close

`python3 scripts/session_brief.py` -> READY, year 2161 round 61 `cur_player 3`, screen hud,
**evidence 26.3 MB** (632 files, budget 20 warn / 30 FAIL). University Base idx 0 pending 8,
minerals 1, `+0xd0` 0; Korolev Center idx 17 pending 6, minerals 3, income 2 — both queues are
deep now (cap 9), so the next enqueue run must pick a base with room or reload.

### Next pick

M68, cheapest first: (a) **separate plan from name-order** — one enqueue of id 1 (plan 9, name
`Formers`) into a queue holding 194 (plan 1, name `Impact Infantry`): plan-descending says in
front, name-descending says behind, and it re-tests the tie direction for free; (b) who writes
head `+0x50` — an hw watch on `+0x50` across one boundary (`milestone/m63` has the pop
instrument); (c) the `income 1` live accrual case; (d) cheap: `m65_screen.py` at a quiet AND a
loaded load, and settle `check_classes.py`.

## Session 108 (2026-10-26) — M68: THE 212-RULE KEY IDENTIFIER IS BUILT, ITS GATE IS GREEN, AND THE ACCEPTANCE **FAILED** — INSERT APPENDED. NOTHING MERGED.

**What changed.** Nothing in the game's model is claimed. Tooling only:
- `scripts/m66_insert_slot.py`: the full candidate set is now machine-readable — `BYTE_KEY_SPECS`
  (52 offsets x desc/asc x ties after/before = 208) + `NAME_STR_SPECS` (4 whole-name rules) =
  `SORT_KEY_RULES` (212), `score_key_sequence(steps, keyf, direction, tie)` (scores a whole
  sequence of write read-backs, returns `None` when the read-back is not a legal shift),
  `key_rule_specs()` -> `(name, off, d, t)` tuples, `key_shape_predictions()`, and a
  `key_shape_gate()` that returns a **5-tuple** whose last element is the set of KEYS (byte
  offsets; `None` = the name string) predicting the landing sequence.
- `scripts/m68_typebytes.py` (read-only, `/proc/<pid>/mem`, clicks nothing): dumps every live
  52-byte type record for the chooser + queue ids and reports per-offset co-ordering.
- `scripts/m68_key_run.py`: the acceptance run. Pre-click shape gate from the baseline alone,
  one click per id, pending polled, landing extracted by `_shift_index`, all 212 rules scored,
  PASS only if exactly ONE key explains every write, `--trace` + `bail()` so every FAIL leaves
  evidence behind.
- `scripts/m68_cellprobe.py`: one click + INSERT, prints exactly what the queue received
  (guard field, clicked cell entry, shift pattern, stored id) and writes a jsonl trace.
- `scripts/test_m68_key_rules.py`: 35 pinned cases — `PASS 35/35 m68 key-identifier cases`.
  The three M67 read-backs fit **11, 17 and 15** of the 212 rules across **4-6 different keys**,
  which is the quantified proof that M67's two-item shapes could not identify a byte.

**The run, with its numbers.**
`python3 scripts/m68_key_run.py --base-name "University Base" --items 2,1,194,192,193
--trace evidence/m68_key_run.jsonl` -> **exit 1**, after `SMAC_SAVE='m54b_clean.SAV' python3
scripts/m54a_load.py --relaunch` + `python3 scripts/smac_play.py --turns 1 --timeout 200
--no-escape 3000 --orders-per-turn 1 --verbose --tag m68t2` (round 51 -> 52, year 2151 -> 2152,
60 s) + `python3 scripts/accept_ready.py` (READY, University Base idx 0, minerals 0, `+0xd0` 0,
pending 0, head slot 2).
- The gate accepted the shape: only `+42` predicts the plan-descending landing `1,1,3,4,3`
  (`key_gate` row) — 12 of the 53 keys were decidable on it at all.
- The engine wrote slots **1,2,3,4,5** — one append per click. Integrity True: every click
  verified `guard == cell`, cell entry == intended id, stored id == intended id, pending +1.
- **55 of 212 rules** predict `[1,2,3,4,5]` for this shape: every byte constant over these five
  ids, plus `+45` (0xff, 0xff, 8, 8, 8) and `+50` (0xff, 6, 0, 0, 0), whose values are monotone
  in click order. So the run cannot name a key — and nothing else is claimed.

**The conflict (recorded, not resolved).** M67 measured sorted landings with this same driver and
this same INSERT button; M68 measured appends. The runs differ in base (Korolev Center and a
round-60 University Base vs the save's round-51 University Base), minerals (3 and 1 vs 0), queue
occupancy at start (2/4/6 vs 0) and the chooser's candidate list (4-7 entries vs 67). One
variable at a time was not achieved here: the reload changed all of them together. **Confounded —
not "because".** M67's read-backs remain real and unexplained.

**Two live rules found on the way.**
- The engine **refuses to enqueue an id the queue already holds**: a second INSERT of 193 left
  pending 5 and every slot unchanged (`evidence/m68_cellprobe_193.jsonl:4`).
- The driver's chooser cell -> pixel mapping (5 columns) is **unreliable past the first row**:
  cell 6 (255,160) and cell 4 (636,60) failed to register in three probes (guard stayed on the
  previous selection, INSERT did nothing), and the one time the cell-6 click registered the queue
  received **-3 (0xfffffffd)** instead of 195, after which the next INSERT appended a plan-9 item
  at the end of the region.

**Open.** (1) Why the enqueue sorts in one state and appends in another — the cheapest decisive
instrument is a gdb breakpoint on the enqueue (`0x418afd-0x418b29`) printing the index and the
value the engine stores, plus a watchpoint on `base+0x54`: it answers "sorted scan or
`pending + 1`" and "where does -3 come from" in one run, without guessing. (2) The chooser cell
mapping. (3) Whether a deferred paint/round-boundary sort rewrites the region (read the region
again minutes later with the queue widget provably open).

**Next pick.** S109 = instrument the enqueue with gdb (the `m63_pop.py` recipe), not another
click-order search: the click-only method has now told us all it can — on THIS state the engine
appends, and no click shape can identify a key an append engine does not use.

## Session 109 (2026-10-27) — M69: THE ENQUEUE WRITES AT THE QUEUE WIDGET'S CURSOR. ACCEPTANCE PASS on one real invocation.

**What changed / what is now known.** The BUILD-pane INSERT is not a sort and it does not read a
type-record byte. It is `queue[pos] = item`, `pos = *(int *)(0x6a9480 + 0x3ff5c)` — the widget's
cursor row — with the region shifted up from `pos` and pending bumped (capped 9).

- gdb instrument `scripts/m69_enqueue_gdb.py` (`--arm|--stop|--parse`, TracerPid + ptrace_scope
  guards, drained log). Breakpoints `0x417dbf` / `0x417e04` / the `0x417dd3` shift loop, hw
  watchpoints on slots 1..3, plus the old `0x418a99` dispatch as a control.
- Live log (`evidence/m69_enqueue.gdblog`): **one continuous click flow** produced
  `ENQUEUE obj=0x6a9480 pos=1 pending=2` -> `STORE queue[1]=192` and then
  `ENQUEUE obj=0x6a9480 pos=4 pending=3` -> `STORE queue[4]=193`. Front insert, then end insert,
  same button, same session: the cursor moved.
- The `0x418a99` block (jump table `0x419c20`, case 0 writes `base+0x40`, case 1 shifts+bumps)
  **never fired** in four INSERTs — it is a different handler, and the M67 note that treated the
  `0x418bxx` block as the insert path is superseded.

**Acceptance (one real invocation).**
`python3 scripts/m69_cursor_run.py --cursor 2 --item 193 --trace evidence/m69_cursor3.jsonl`
-> **PASS**, region `[2,192,194]` -> `[2,192,193,194]`, pending 2->3, cursor read back as 2
before the click, `plan_sorted_index 1`. The instrument refuses a shape where the cursor and the
plan index agree (`--cursor 1` -> `FAIL: non-discriminating shape`), so the PASS discriminates.
`python3 scripts/test_m69_cursor.py` -> `PASS 15/15 m69 cursor cases` (offline; pins the store
arithmetic, the plan-vs-cursor disagreement, the M68 appends and both negative stores).

**Correction to session 108.** `-3` was recorded as probably a bad click. It is not: with the
click verified (`guard == cell`) and the cursor poked, item 196 (all-zero record) stored **-6**,
and 195 stored **-3** on a guarded click. A type with no real record is stored as a negative
value; two different negatives, so not one sentinel. Do not use 195/196/197+ in a shape.
Also: the M68 `-3` claim that a poisoned entry makes the next INSERT "append a plan-9 item at the
END" is re-read here as "the cursor had moved to the end", not as a fault.

**Open.**
1. What sets the cursor (`[widget+0x3ff5c]`)? The writers are `0x40b018-0x40b081` (arrow/move
   handler, clamps to `[1, pending]`), `0x4163b6/0x41650e`, `0x417e3b-0x417e7b` (post-insert).
   The chooser click is what a user expects to set it; the log shows it moving on its own
   (2 -> 4 after one insert). An hw watchpoint on the field across ONE insert would name the
   writer and settle whether the widget sorts by plan when it refreshes the list.
2. The widget's LIST order (what M67 measured) — is it recomputed on paint from the plan byte?
   `0x40axxxx` is the queue-widget paint code; that is where the plan comparison should live.
3. `-3 / -6` for recordless types: what is the formula? (two points only.)

**Next pick.** M70 = watch `[0x6a9480+0x3ff5c]` across one INSERT and one queue-list repaint,
then read the widget's paint loop (`0x40axxxx`) for the plan-byte comparison. That closes the
last link: the widget sorts (or not), the user-visible order is that list, and the enqueue just
obeys the cursor.

## Session 110 (2026-10-27) — M70: WHO WRITES THE CURSOR. ACCEPTANCE PASS on one real invocation.

**What changed / what is now known.** The queue widget's cursor field is
`[0x6a9480 + 0x3ff5c] = 0x6e93dc`, and there are exactly **18 instructions in .text that write
it** (`scripts/m70_scan_writers.py` over `scratch/m574/text.txt`). Three of them fired in one
real click flow, and every logged write is now attributed:

- **`0x40aae5`** `mov [edi+0x3ff5c],eax` inside the queue-LIST row handler `FUN_0040a990`
  (read at `0x40aa22`): `cursor = min(clicked_row, [[0x8f0d60]+0x4c] + 1)`. **A click on a queue
  row DOES set the cursor** — the user's cursor-setter is the row click, not the enqueue.
- **`0x417e3b`** `mov [ecx+0x3ff5c],eax` — the enqueue tail: `eax = [[0x8f0d60]+0x4c] + 1`
  (`0x417e2d` load, `0x417e3a` inc), i.e. after an INSERT the cursor parks at rows+1.
- **`0x4194b3`** `mov [ebx+0x3ff5c],0x0` — a handler that sends the widget message `0x4d00`
  (`push 0x4d00; call 0x584010` at `0x4194a4`, with `eax = 0xffffffd9 - edi` and
  `edx = 0xffffffd9 - ecx`, the -39 sentinel) and then **zeroes the cursor unconditionally**.
  This is why the cursor read back 0 after the run.
- Reads (not writes) at `0x40aa22` (row handler), `0x41650e`, `0x417d25/417dbf/417ddb/417e0e/
  417e62/417eb3` (the enqueue and the move helper), `0x4185ea/418714/41876e`, `0x41e25f`.

**The enqueue arithmetic, pinned to the M69 log** (`test_m70_cursor.py` reproduces all four real
transitions): the shift runs from `min(9, max(pending+1, cursor))` down to `cursor+1` — so the
slot AT `pending+1` moves and slots above it keep their stale values; the store uses the
ORIGINAL cursor (the clamp at `0x417ddb` feeds only the `cmp` at `0x417e17`/`0x417df3`);
`pending++` only when `pending < 9`; `cursor = pending+1` after an insert.

**The cursor is clamped/advanced against the WIDGET'S OWN row count `[[0x8f0d60]+0x4c]`**
(`0x40aa22`, `0x417e14`), not against the base record's pending that `--stop` reads back.
`DAT_008f0d60` is a POINTER to the base record (`0x40ad6c`/`0x40b00a` load it and index `+0x4c`,
`+0x50+4k`); Ghidra flattens it. Reading base pending after the run is not a model check.

**Acceptance (one real invocation).**
`python3 scripts/m70_cursor_watch.py --arm --base-name "University Base"` (cursor 0, pending 0)
-> `m66_insert_slot.py --base-name "University Base" --item-a 193 --item-b 192 --slots 12`
-> `--stop` -> `--acceptance` -> **PASS**: 4 cursor writes, all attributed
(`0x40aae5`, `0x417e3b` x2, `0x4194b3`), values `[1, 2, 3, 0]` each equal to the model's
prediction (row click on row 3 with widget rows 0 -> `min(3, 1) = 1`; tails -> 2 then 3; the
`0x4194b3` handler -> 0); region `[2,0,0,...] -> [2,193,192,...]`, pending 0 -> 2.
`python3 scripts/test_m70_cursor.py` -> **PASS 23/23** (parser against the measured M69 log
lines, the gate's discriminating power, the pc attribution, and the REAL M70 log).

**A PASS is not an outcome — read back.** The queue region was written ONLY by the two enqueue
stores (`SLOT1WRITE/SLOT2WRITE pc=0x417e08`): no paint-time rewrite of the region happened in
the armed window (arm -> 2 INSERTs -> OK -> Escape -> detach). And the row handler indexes
`[[0x8f0d60] + 4*clicked + 0x54]` at `0x40b041-0x40b04c`, i.e. a list row IS a queue slot —
there is no separate row list to sort.

**CONFLICTS reported, not resolved.**
1. **The negative-id table stride disagrees between sites.** `0x40ada8-0x40adae` and
   `0x4164ef-0x4164f5` compute `0x984d38 + (-v)*48` (`lea [r+r*2]; shl 4`), while
   `0x41890a-0x418914` and `0x418943-0x41894d` compute `0x984d38 + (-v)*16` (`shl 4` alone).
   -3 -> `0x984dc8` or `0x9852b8`; -6 -> `0x984e58` or `0x985348`. Not poked, not resolved.
2. **M67's plan-descending LIST order is still unexplained by code.** No site in .text reads the
   plan byte `+42` (`m70_scan_writers.py` finds zero type-record reads with the 52-byte idiom
   except four that just pass the record pointer to `FUN_00626634`/`FUN_006265a2` for the row's
   string). The four type-address sites are `0x40ad92`, `0x4164dd`, `0x4188f9`, `0x418932`.
3. The brief's three standing CONFLICTs (year store `0x51f554`, the pay site, the faction-3 type
   names) were not touched this session.

**Open.** (1) Who calls the `0x4194b3` handler and what message `0x4d00` is (it zeroes the cursor
after a queue mutation — the cheapest candidate explanation for M67-vs-M68 state differences).
(2) The `-3 / -6` formula (two points, three candidate tables). (3) Whether a POP/completion or a
round boundary rewrites the region — the armed watchpoints see it, this run says a repaint does
not. (4) `m66_insert_slot --rules layout` scored `fit = []` on this shape (both inserts landed in
click order at slots 1,2 — the layout rules need a shape where one rule fits and the others do
not); no layout claim was made, and none was needed for M70.

**Next pick.** M71 = arm `m70_cursor_watch` across ONE POP (unit completion) and one round
boundary: the cursor field plus slots 1..3 watchpoints will show whether the engine rewrites or
reorders the region at completion (the M67/M68 discriminator) and whether the `0x4194b3` handler
fires there. Do not click-hunt for a sort key again.

## Session 111 (2026-10-27) — M71: WHAT THE COMPLETION'S POP DOES TO THE QUEUE REGION AND THE CURSOR. ACCEPTANCE PASS on one real invocation, reproduced.

**What changed.** New instrument `scripts/m71_pop_watch.py` (pokes minerals and reads it back
BEFORE attaching, arms 4 hw watchpoints — the cursor field `0x6e93dc` + slots 1..3 — and 10
breakpoints on the pop/pay/create/visit sites, drives real round boundaries itself, detaches,
then reads the region back from `/proc/pid/mem`), `scripts/test_m71_pop.py` (**PASS 34/34**:
the shift composition, the parser, both committed real logs, and 10 negative fixtures that
must and do fail), and the NAMED.md M71 block. No threshold, floor or economic term moved;
the only post-run edit to the acceptance was to make gate 2 test the ROUND counter alone
(year is derived from it), which is STRICTER, and both committed logs still pass it.

**Acceptance (one real invocation).** `python3 scripts/m71_pop_watch.py --boundaries 2 --tag
m71pop` -> **PASS** (exit 0). Shape at arm: pending 2, slots `[2,193,192,0,...]`, minerals
poked 0 -> 9 read back, head price 9, cursor field 0, round 51. The window logged, in order:
`VISIT idx=0` -> `PAYA base=0x95da10 storage=9 edi=9` -> `CREATE id=2` -> `POPIN idx=0 pend=2`
-> `POPDEC count=0x9540ba byte=1 head=2` -> `POPAFT byte=0` -> `SLOT1WRITE pc=0x4ef62e` (the
pop shift store `0x4ef62c`) `now=192` -> `POPCNT newpend=1 s0=193 s1=192 s2=192` ->
`POPRES head=193 r=1` -> `POPEXIT`. Round 51 -> 53. READ BACK after detach: pending 2 -> 1,
region `[2,193,192,0,...] -> [193,192,192,0,...]`, cursor 0 -> 0, minerals 9 -> 0, `de84[2]`
1 -> 0. K = 1 = the SINGLE model; the DRAIN candidate predicted `[192,192,192,...]` with
pending 0 — a different region, so the shape discriminated and the read-back chose SINGLE.
**Reproduced**: the same command with `--tag m71pop3` on a freshly reloaded save
(`SMAC_SAVE='m54b_clean.SAV' scripts/m54a_load.py --relaunch` -> `smac_play.py --turns 1` ->
`m66_insert_slot.py --item-a 193 --item-b 192`) -> **PASS**, identical except `PAYA storage=10
edi=9` (the round's `+1` add at `0x4ef7f6` landed before the gate) and minerals 9 -> 1.

**A PASS is not an outcome — read back.** The armed region was written by exactly ONE store
in the window, the pop shift at `0x4ef62c`; `queue[pending]` (slot 2) kept its stale 192
rather than being written, which is why the read-back shows a duplicate. ZERO cursor writes
happened across the whole window, so the completion neither moves the widget's cursor nor
reorders the queue — it left-shifts it, and the `0x4194b3` handler does not fire there. The
queued-count byte was read back at the address the game itself computed (`0x9540ba`).

**The third run is an honest FAIL.** `--tag m71pop2` (head 193, a DESIGNED id, minerals poked
to its price 18 and read back) FAILed its window gate: two boundaries (round 53 -> 55) gave
ONE `VISIT` of the base with `min=18` and NO `PAY`/`POP`/`CREATE`; at the end `+0x3c` = 5,
`+0xcc` (rate) = 0, `+0x30` = `0x80007020`, `+0x98` = 18. Confounded (head id 2 vs 193,
progress, rate) — no mechanism claimed, nothing merged on it.

**Side observations (not gated).** A "the minerals output of University Base is not sufficient
to support Scout" dialog was swallowing chooser clicks: two scripts each clicked cell 1 (194)
and cell 3 (2) and read guard 0 with pending unchanged; after `scripts/m70_clear_dialog.py`
the same cell-3 click read guard 3 and the INSERT worked. Type records read live: `+0x30` =
192 `0x0001`, 193 `0x0041`, 194 `0x0041`; `+0x2c` (owner mask) = 0 for all three — which is
exactly the shape that makes `0x5a73f0` return nonzero and stops the pop's drain.

**Open.** (1) why a designed head did not complete at storage == price; (2) who calls the
`0x4194b3` handler and what widget message `0x4d00` is (it did NOT fire at a completion);
(3) M67's plan-descending LIST order still has no code behind it; (4) the `-3 / -6` table
stride conflict; (5) the pay-site conflict is narrowed, not closed — `0x4efedd` with `edi` =
price is what fires for a UI-queued base-type head at index 0, `0x4f0ca6` is still unexamined.

**Next pick.** M72 = watch the completion GATE, not the pop: arm `0x4f0a37` (`cmp
[base+0x40], edi`), `0x4f0abb`, `0x4f0b4f`, `0x4f0b78` and `0x4efe41` (`cmp ebx,0x40`) on a
base whose head is a DESIGNED id with storage >= its price, and name which test sends the
visit home without paying and what `edi` holds at each. That explains `m71pop2` and closes the
pay-site conflict for the designed branch. Do not re-litigate the pop: it is measured twice.
