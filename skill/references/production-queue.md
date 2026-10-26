# Production queue: the gate, the completion chain, and the freezes it causes

The round boundary BUILDS from per-base queues. Field layout cites are to the base record at
`0x95da10` stride `0x130`; settled rules live in repo `NAMED.md` "M56 block"; the predictor +
boundary verifier is `scripts/m56_build.py`, its rule tests `scripts/test_m56_predict.py`.

## The gate (settled by a controlled poke, not by reading)

A queue head completes at the boundary iff:
- `pending` (`base+0x4c`) > 0, AND
- head (`base+0x50`) is an item id (`0xffffffda`/−38 = empty slot; ≥ 0 = unit type; < 0 =
  facility/project, `|q|` encodes the project), AND
- **mineral storage `base+0x40` >= price**, price = `0x4e40a0(owner,1,−1) × type_cost` — the
  type cost is the byte at `+41` of the type record `0x98ad88 + type*0x34`; the economic factor
  is 10 for in-mask owners (`0x985b10`), so `+41 = 1` means 10 minerals.

**The progress accumulator `+0x3c` and the rate `+0xcc` do NOT gate production.** The
`cost <= [base+0xcc]+[base+0x3c]` comparison inside `0x4ef6d0` is the out-mask race scan / display
path (`0x4ee8c7` accumulates it "display only"). Proof shape: a base with net income `+0xd0 = 0`,
rate 1, progress 32 produced on the very next boundary after storage was poked above the price —
an accumulation model predicts no. When docs and code disagree on which field gates, run the
one-variable poke (arm queue + storage, change nothing else) and let the arrival decide.

After the gate passes: pay `0x4f0ca6` (`storage −= price`) → **clamp B `0x4f0cc3-0x4f0ce9`**
re-caps storage to `max(0, min(10, net_income))` for in-mask owners — so a completed build on a
zero-income base reads as storage collapsing to 0, NOT as a giant cost; floor bookkeeping as
"storage decreased by at least the price", never as an exact delta. Then the POP `0x4ef5d0`
(pending −1, queue `+0x50..` left-shifts, faction queue counter `0x94dc84[head]` −1) and the unit
record is created on the base tile via `FUN_005ab650` (shard_012.c:20890, right after the debit).

## Where production runs in the round (there is no "production phase")

`0x5208f0(p)` upkeep → `0x520540(p)` → the per-owner base loop (`*pbVar8 == param_1`,
shard_013.c:11568) → `0x4f5a70(base)` pipeline → stage 6 `0x4ef6d0` (shard_012.c:24182). This
**runs for every base every round in solo**, ours last before the year flip. The
`faction+0x104 & 2` gate in `0x521070` guards only the AI upkeep step `0x574370` — reading
`+0x104`/`+0x108` (the production SPLIT sliders, recomputed by `0x51fe90`, consumed by `0x4eaa10`)
and finding them zero does NOT mean the queue processor is gated off. Do not conclude "nothing
can build" from the sliders; read the queues (`+0x4c`/`+0x50`) and storage (`+0x40`) per base.

## Why a map can sit building nothing for 100 rounds

Natural state on a late-game map: **pending 0 with head −38 on every base**, and net income
`+0xd0 = 0` on every base (mineral pipeline empty) — the storage gate can never fire. Both halves
must be checked: an armed queue with zero income still stalls (and what does get built is eaten —
see the support cliff).

## Two freezes a turn loop must handle after a build

1. **A produced unit arrives order 0 and FREEZES the auto-end.** The auto-advance ("No units need
   new orders") only fires when NOTHING is actionable; a unit built at the boundary is actionable,
   the cursor parks on it, and Return every 2 s for 150 s does nothing (`cur_player` stays ours,
   `turn_flags` 0, year unmoved). ONE `h` on the cursor unit (→ HOLD) closes the turn at once.
   Cadence: Return every 2 s; if parked on our turn past ~8 s with no flip, press `h` every 4 s;
   if still parked past ~15 s, click the popup OK. Verify each keypress by reading the field it
   should move (`turn_flags`, `cur_player`, the year) — a pressed key that changes nothing is not
   an input, it is noise.
2. **A popup whose DEFAULT row is not OK does not close on Return — Return CYCLES its options.**
   The Operations Director popup defaults to "Zoom to Base Control"; a blind Return loop cycles
   the option rows forever. Click OK (Operations Director: window coords ≈ (630,247)). Before
   trusting Return as a universal dismisser, look once at what is drawn: read the popup's default
   row, and dismiss by clicking OK. The quit prompt's OK remains banned; its default ("Oops, no,
   wait!") IS Return-safe.

## The support cliff

A produced unit at a base with no mineral income is DISBANDED by upkeep (Operations Director:
"The minerals output of <base> is not sufficient to support <unit>. The unit has been
disbanded."). Production that survives needs `+0xd0 > 0` at the base. Census our-unit counts
across the boundaries when testing production at our own base — a PASS arrival can be followed by
a disband two rounds later.

## Accounting rules for production verification

- **Count arrivals as a multiset delta on (x, y, type, owner)** — never record index (compaction
  rewrites slots) and never order (an idle order-0 unit becomes order 1 at the boundary, which
  looks like a new record). A produced unit arrives order 0 ON its base tile; a nonzero order at
  an arrival means cargo/unload or an order reset, not production.
- **Check the whole map, not just our side.** Enemy bases produce even while ours sits empty; a
  boundary inventory that counts only our-side arrivals records a false "zero production".
  Enemy-side queues refill inside the enemy's own AI turn, so a queue read taken during OUR turn
  does not predict their arrivals — floor predictions on in-mask/our bases, report enemy-side
  arrivals as observations.
- The out-mask price model (era table `0x68cbb8` factor, can be 0) is unmodeled — do not predict
  out-mask owners.

## Who fills the queue head (why a human queue sits empty)

The chooser `0x4f6030` (sole caller `0x4e5ae0`) both forces the economy recompute and returns a
chosen item id: with no candidate passing the filters it returns the sentinel **99999 = nothing**
when the base is human-owned (faction absent from the AI mask `0x985b10`) AND the base's auto-mode
flag `base+0x1c & 0x1000` is clear; for an AI-owned base, or with that flag set, a fallback scan
over the type table picks a real item instead. `0x4e5ae0` hands the result to `0x4e5560`, which
returns immediately on 99999; otherwise it sets the queue head slot (`base+0x50` view,
`DAT_0095da60`), ±1s the faction item counts (`DAT_0094de84`), and recomputes the cost field — and
it is called from INSIDE the queue processor when the queue is empty or blocked. Consequence: a
human base only ever gets a queue item through the BUILD UI path (`0x417ee0` dispatch) or with
auto-mode on; "the game queued nothing for us" is the designed behavior, not a bug.

**A freshly founded base can have real minerals and income** (`+0x40` storage > 0, `+0xd0` income
per round): after a reload + re-found, read both fields before deciding a storage poke is needed —
if income is positive, the storage gate reaches the cheapest unit's price on its own within a few
rounds and the arrival is a natural (non-poked) verification.

## Testing a predictor without the live box (mock /proc/mem)

`scripts/test_m56_predict.py` serves the reader functions offline from a sparse
`{addr: bytes}` map. Rules that make the mock honest:
- Build the blob dict object BEFORE filling it (`self.blob = blob` then fill; rebinding
  `self.blob` after the loop discards everything stored through it).
- Store each record under its exact `ARR + i*STRIDE` key, and let `read(n)` walk byte-by-byte:
  a stored chunk yields its whole length, a gap yields one `\0` and advances one byte — a naive
  "chunk-at-seek-or-all-zeros" read silently returns zeros for a multi-byte read that starts on
  a stored dword.
- Queue slots must be read SIGNED (`0xffffffda` is −38; `struct.pack('<i', 0xffffffda)` raises
  `struct.error` — pack markers unsigned, read signed).
- Make the fixture FAIL a floor on purpose: take a real PASS trace, mutate the after-snapshot
  (delete the predicted arrival), and require exit 1 naming the failed floor. A gate that never
  fails on a hand-typed trace is vacuous.

## M57 (session 93) — the queue can be filled by the GAME's BUILD UI

Verified end to end with a memory read-back after every click; the run that verified it made **0
memory writes** and the queued unit completed at a boundary where storage (8) was **below** price
(10) — paid by income, not by an armed poke.

1. Open the base display: poke the map cursor to the base tile (window `*(0x7cdecc)+0x1dd9c/+0x1dda0`
   and the handler cell `0x91b5f0/0x91b670` at index `0x91b5e8`), `SEL_G 0x91b5bc` = -1, orders mode
   `0x91b5b8` = 0, then `b`. With orders mode ON, `b` raises the OBLITERATE prompt instead (its
   "No, let them live" is the default; Return spares the base).
2. Right arrow **(523,433)** switches the QUEUE widget's base; queue row 1 **(185,437)** opens the
   chooser (open test: pixel (160,343) == (103,91,181)); the grid is 5 columns, cell k at
   x = 128 + 127*(k%5), y = 60 + 100*(k//5); the display order is the candidate array
   `DAT_009267e4` / count `0x9267e0`; the selection field `[pane+0xa1c+0xa774]` holds the CELL INDEX.
3. **INSERT (497,343)** writes head `+0x50`, pending `+0x4c`, slot `+0x54`; **OK (285,343)** commits
   (mode 0, no restore); CANCEL restores from the stack snapshot. Re-read pending ~1 s later.
4. `base+0xd0` is NOT the per-round mineral credit (measured deltas 0/+4/0/-5/+2 while it read 2),
   so a per-round arrival prediction built on it over-predicts. Watch `base+0x40` at 2 ms to get the
   real credit sequence.
5. Escape on the map raises the quit prompt; once dismissed the game stops taking KEYS (clicks still
   work). Reload is the only recovery.

## M57-2/M57-3 (session 94) — what the mineral credit ACTUALLY is

- Storage `base+0x40` is NOT `+= base+0xd0` once per round. Inside ONE base visit at the flip there
  are SEVERAL stores; measured boundary sequence (2 ms sampler, `evidence/trace_m57c_q3.jsonl`):
  `store 7->9, store 9->0 (pay), pending 1->0 (pop)`. The income add is gated
  `d0 > 0 && head != -38 && !(flag30 & 2)` (disasm 0x4ef7db-0x4ef7f9) and **fires even with pending
  0 while the head slot is stale** — the pop left-shifts the queue but leaves stale item ids in the
  tail, so an "empty" (pending 0) base still accrues.
- `base+0xd0` is recomputed EVERY visit (`FUN_004e93f0`) and moves with the garrison: measured walk
  1->3->0->1->2->3->4 while produced units arrived and were support-disbanded. A per-round arrival
  prediction is exact only while `+0xd0` is stable.
- The pay at 0x4efed8 deducts `$edi` = the PRICE (m52a live: `SPENDA old=200 new=190 edi=10` at
  price 10 — supersedes the old "edi = sweep-entry index" note). Clamp B (0x4eff20) stores only when
  storage > min(`*0x92a370` = 10, d0).
- The gate at 0x4f0a3d (`cmp [edx+0x40], edi`) is on the `*0x8f0d60`-current-base branch (reached via
  the 0x4ef985 AND-test), NOT the per-base path — it does not fire for a base whose queue the UI
  filled. The per-base completion runs through the loop-end pay block.
- **gdb register side-values lie**: conditional breakpoints (`if $eax == <base addr>`) filter the
  visit correctly and baked-base field reads match the sampler, but `$ecx`-as-d0 / `$edi`-as-price at
  the sites printed garbage. Evidence = sampler + field read-backs. A hardware watchpoint on `+0x40`
  is unusable for cadence (field read constantly → inferior crawls, year never moves).
- Pokes lie while a tracer is attached: poke BEFORE attaching, verify after `kill -CONT`.
- **The queue widget's base is INDEPENDENT of the display's base**: the right arrow (523,433) moves
  the field `0x6a9480+0x3ff3c`; INSERT (497,343) lands on whichever base the widget holds. Cycle the
  arrow until `+0x3ff3c` == the target index, then row 1 (185,437), cell, INSERT, OK (285,343),
  reading pending after every click. The chooser grid position is ERA-DEPENDENT (Scout Patrol id 2
  was cell 3 at 2152, cell 4 at 2168 — `DAT_009267e4` = [192,195,194,193,2,...]): locate the cell by
  CONTENT. `scripts/m57_ui_enqueue.py` scripts all of it with read-backs.
- The enqueue dispatch `0x417ee0` fires with `*0x8f0d60` = the target base (proved live), but
  m53g_drive's static store addresses (`0x418b57/0x418ad3/0x418ac7/0x418b24`) did NOT hit on the
  INSERT write — re-derive before trusting them.
- The base array compacts mid-game: Korolev Center's index walked 17->18->17 within one session
  (n_bases 29->19->23->25). Locate bases by NAME/(x,y), never by remembered index.
- The acceptance run `m56_build.py --ui-queued 17 --boundaries 8 --timeout 240` FAILED
  (`evidence/trace_m56_build_20261025_215056.jsonl`): 0/0 positive predictions (income read 1/round,
  completion landed at minerals 7 + a fresh recompute), r4 bookkeeping BAD, r6/r7 walk-home BAD (the
  after-snapshot at `--settle 0.3` caught cur_player mid-walk — use `--settle 2.5`; a sampling fix,
  not a floor change). Nothing weakened; nothing merged.

## M57-3/M57-4 (session 95) — the per-round model is falsified; enumerate the stores

- **A round-start snapshot cannot predict the arrival round.** Same base, same fields (minerals 8,
  income 2, pending 1, price 10): round 3 predicted arrival and storage stayed 8 -> 8 (the visit's
  add was skipped); round 4 predicted the same and arrived (8 -> 3, pending 0). The add uses the d0
  CURRENT AT THE VISIT (measured +1 while the field read 1, +2 while it read 2), and that number moves
  inside the round. Recorded: `evidence/trace_m56_build_20261025_222122.jsonl`.
- The pay at 0x4efed8 is NOT the price: 8 -> 3 (net -5) and, with pending 0, 5 -> 0. One game-queued
  Scout Patrol produced TWICE (r4 and r7) while the slot array never left-shifted ([2,2,0] all run) —
  so `pending` is not the queue truth; the slot array is.
- **The units-not-moved confirm takes NO Return.** Click the YES row then the OK bar 26 px below
  (`smac_play.answer_confirm`); a run sat 240 s with the year frozen on that dialog. Diagnose with one
  frame + classify -> `confirm`.
- **orders mode 0x91b5b8 must be restored to 1 after any base-display recipe**; at 0 every order key
  is a no-op and a turn with an actionable unit never ends.
- The boundary watch must break when the walk is HOME, not after a fixed settle: with everything held
  the next round flips 1-2 s later, so a fixed sleep either misses the walk (floor fails) or swallows
  the next flip (year delta 2).
- `scripts/smac_preflight.py` is the orientation tool: one read-only command, exit 1 on FAIL, prints
  our bases BY NAME with index/coords/pending/head/minerals/income, the address table, tracer state,
  /tmp and the evidence budget.
