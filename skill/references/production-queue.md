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
