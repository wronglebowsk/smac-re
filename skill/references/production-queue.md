# Production queue: the gate, the completion chain, and the freezes it causes

The round boundary BUILDS from per-base queues. Field layout cites are to the base record at
`0x95da10` stride `0x130`; settled rules live in repo `NAMED.md` "M56 block"; the predictor +
boundary verifier is `scripts/m56_build.py`, its rule tests `scripts/test_m56_predict.py`.

## The gate (settled by a controlled poke, not by reading)

A queue head completes at the boundary iff:
- head (`base+0x50`) is a unit type id (0..0x3f; `0xffffffda`/−38 = empty slot; < 0 =
  facility/project, `|q|` encodes the project), AND
- **mineral storage `base+0x40` (+ this round's income, the add is inside the same visit)
  >= price**, price = `0x4e40a0(owner,1,−1) × type_cost` — the type cost is the byte at
  `+41` of the type record `0x98ad88 + type*52`; the economic factor is 10 only when the
  difficulty scalar `0x92ada8 >= 2`, else 9 (or 8) — see the M58 block in repo NAMED.md.

**M59: `pending` (`base+0x4c`) is NOT a term of the gate.** The gate `0x4efa5e`
`cmp [ecx+0x40], edi; jge 0x4efadc` prices whatever sits in the head slot; the pay store
`0x4efedd` dominates the create-unit call `0x5ab650 @ 0x4eff4e` (removing the pay block makes
the create unreachable from both the entry and the gate — `scratch/m59/dom.py`), and nothing
between them reads `+0x4c`. Pending gates only the POP `0x4ef5d0`, which returns at `0x4ef5f4`
when pending == 0; so with pending 0 the head is never consumed and the base **re-buys the same
type every round it can pay**. Measured one-variable, one control (`scripts/m59_head.py`):
Korolev Center pending 0 head 2, minerals poked 0→9, University Base untouched at 0 → one turn
later Korolev minerals 0, income 0→−1 (the new unit's upkeep), pending still 0, base tile
5→6 units of (type 2, ours); control base unchanged. Acceptance run
`evidence/trace_m56_build_20261026_145157.jsonl` PASSes 10 boundaries with pending-0 arrivals
predicted and observed.

**The progress accumulator `+0x3c` and the rate `+0xcc` do NOT gate production.** The
`cost <= [base+0xcc]+[base+0x3c]` comparison inside `0x4ef6d0` is the out-mask race scan / display
path (`0x4ee8c7` accumulates it "display only"). Proof shape: a base with net income `+0xd0 = 0`,
rate 1, progress 32 produced on the very next boundary after storage was poked above the price —
an accumulation model predicts no. When docs and code disagree on which field gates, run the
one-variable poke (arm queue + storage, change nothing else) and let the arrival decide.

After the gate passes: pay `0x4efedd` (`storage −= price`) → the clamp at `0x4eff02-0x4eff23`
re-caps storage for in-mask owners when it exceeds `max(0x92a370, income)` → the create-unit call
`0x5ab650(type, ?, x, y) @ 0x4eff4e`, guarded at `0x4eff32` by the PROCESS-GLOBAL dword at
`0x8f0d70` (`a1 70 0d 8f 00` = `mov eax,ds:0x8f0d70`; `test eax,eax; jne 0x4eff5c` skips the create).
M60 fixed the old claim here (`[base+0x10] == 0`): base record `+0x10` holds 0x4b000000 / 0x55000000
on our two bases (not a flag), `grep -c 0x8f0d70` over the whole `.text` dump is 1 — this read — and
an hw watchpoint on it stayed silent over 2 boundaries with 53 base visits, value 0 at every visit
(`scripts/m60_guard.py --stage watch`, evidence/m60w_watch.gdblog). Proven by poke, one variable, the
other base as control: guard 1 -> the base still PAYS (storage 9 -> 0) and NO unit arrives (our unit
count 10 -> 10, guard reads back 1 after the turn); guard 0 -> the base pays and the unit ARRIVES
(10 -> 11). The chooser `0x4f6030` uses the neighbours `0x8f0d74..0x8f0d90` as its best-pick scratch.
The POP `0x4ef5d0` — M63 measured it instruction by instruction
(`scripts/m63_pop.py`, `evidence/m63pop.gdblog`): it WALKS the queue while `[base+0x4c] != 0`
(`0x4ef5f4 je 0x4ef684` returns untouched when pending is 0), and per step it (1) decrements the
per-faction queued-count byte at `[0x94de84 + owner*0x20bc + head]` — the head value is added
UNSCALED, not `*4`: for owner 3 / head 2 the address the game itself computed at `0x4ef613` was
`0x9540ba` = `0x94de84 + 8380*3 + 2`, and that byte read 3 at `0x4ef61a` and 2 at `0x4ef61c`, so
the M62 conflict is CLOSED in favour of `0x94de84` and the sibling `0x94dc84` (512 B lower, same
stride) is a DIFFERENT counter — it went 6 -> 7 in the same window in which a unit was produced
(M66 measured the other side of the same byte: the BUILD UI's INSERT adds 1 to
`0x94de84 + owner*0x20bc + type` for the type it queues and never touches `0x94dc84` at its own
indexing — `scripts/m66_insert_slot.py`, settled state read after OK);
(2) left-shifts the slots `pending` times (`0x4ef62c`, seen live writing Korolev `+0x50` with the
value that was at `+0x54`); (3) stores `pending-1` (`0x4ef642`); (4) hands the NEW head to a
validator — `0x5a73f0(head, owner, idx)` for `head >= 0` (type record `+0x38` bit 0 / `+0x34` bit
owner; returns 0 = fine) or `0x5a6e70(-head, owner, idx, 0)` for a negative code (tests the
availability globals `0x985aec`, `0x985ac4`, `0x985bb8`) — and takes its error path `0x4ef68b` on a
nonzero return (measured: `POPVAL item=2 owner=3 idx=18` then `POPRES result=1`). They are
PREDICATES, not builders: the build is still the visit's pay `0x4efedd` + `call 0x5ab650` at
`0x4eff4e`, and the pop runs LATER in the same visit (order measured: PAY -> CREATE -> POPDEC ->
POPSHIFT -> POPCNT -> POPVAL) and only ADVANCES + VALIDATES the queue; a boundary
snapshot can land on either side of it, and the create itself can land in the gap between one
window's after-snapshot and the next window's before-snapshot (measured: pay 8→1 with pending
still 1, unit 6→7 across the snapshot gap).

## Ghidra's `DAT_008f0d60` is a `short *` — double every offset it prints

`0x8f0d60` holds a POINTER to the base record being processed (`DAT_008f0d60 = &DAT_0095da10 +
idx*0x98` shorts = `idx*0x130` bytes; written at `0x4e3470`, `0x4e47d0`, twice in `0x4ef6d0`, twice
in `0x4f5a70`). Ghidra types it `short *`, so pseudocode `*(uint *)(DAT_008f0d60 + 0x1c)` is BYTE
offset **+0x38** — verified against the bytes (`0x4fb293 mov ecx,ds:0x8f0d60` then `0x4fb299 test
DWORD PTR [ecx+0x38],0x80000000`). So in that pseudocode: `+0x1c` = the plan-flag dword `+0x38`,
`+0x20` = mineral storage `+0x40`, `DAT_008f0d60[0]/[1]` = the x/y words at `+0x0/+0x2`. Double every
offset printed through this variable before believing it, and check the disasm once per new site.

## `0x4f6030` = the production CHOOSER (what a base builds next)

Called by `0x4e5ae0` (and by the BUILD UI) for the base in `*(0x8f0d60)`; returns the chosen item id
and can write the winning score through `param_4`. It scores candidates and keeps the MINIMUM
(compare against `local_124[0]`, seeded `0xf423f` = 999999; tie broken by a secondary key), score =
`base_cost * multiplier`, the multiplier halved/doubled by ~25 conditions (terrain table `0x92b950`,
the flat category table `0x98adb2` indexed `item*0x34`, the affordability reshape through
`0x4e4450` × `0x5ac950` × `0x4e40a0` at `0x4fb271-0x4fb2c9`). Before scoring, a candidate is REJECTED
unless the base's plan dword `[base+0x38]` contains the bits its category requires — the switch at
`0x4fb4xx` on `record[+0x32]`: cat 0 -> 0x200, 1 -> 0x1000, 2 and 3 -> 0x1000 (but 0x400000 when
`[base+0x38] & 0x1000` is clear or `record[+0x2c] != 0`), 4 -> 0x2000, 5 -> 0x800, 6 -> 0x400,
7 and 10 -> 0x800000, 8 -> 0x20000, 9 -> 0x8000, 0xb -> 0x100000, plus 0x80000 more for
faction-specific types (>= 0x40) whose `record[+0x38] & 4` is clear. That gate runs only when the
owner is IN the human mask `0x985b10` (for our Korolev Center, `[base+0x38] = 0x00dfbe41` carries
0x1000, so Scout Patrol, category 3, passes). Fallback when the main pick is invalid
(`0x4fd6a0-0x4fd6e5`): scan all 512 type records (`0x98ad80`, stride `0x34`, end `0x9915b2`), keep
those `0x5a73f0`-buildable with category 1/2/3 and `record[+0x38] & 4`, take the lowest `record[+0x31]`.
Consequence: an enemy base's next head is the argmin of that heuristic over ITS plan mask and ITS
budget, so enemy production stays REPORTED, not predicted.

## When our base's visit lands in the round (a read can be early, not the create slow)

The year flip is NOT the end of the round's processing. Measured 2026-10-26: after
`smac_play --turns 1` printed `2189->2190`, Korolev Center held storage 9 with `+0x3c` unmoved and
`cur_player 7`, and NOTHING changed for 100 s; the pay and the create landed later, while the player
walk came home (storage 9 -> 0, our units 10 -> 11, `cur_player 3`). Judge a base's production only
after `cur_player` is ours again — `m56_build` closes every window on exactly that condition, which
is why its windows see the pay while a hand-read taken the instant the flip prints does not. What M59
called the snapshot GAP is this: the read was early, not the create slow.

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

## Running the acceptance (`m56_build.py --ui-queued <index> … --no-poke-hold`)

- Its provenance floor is `writes == 0`, and the harness counts its own `poke_hold` as a write: HOLD
every one of our records BEFORE the run (`scripts/m59_head.py --stage read --hold`, read-back verified)
and pass `--no-poke-hold`. Holding inside the run fails the floor the run exists to prove.
- The `--ui-queued <index>` argument is only the START index. Pair each base across snapshots **BY
NAME** — the 304-byte base array compacts mid-run, so an index carried across a boundary names another
faction's record and the bookkeeping silently checks the wrong base. **Name alone is not enough
either (M63):** a base that changes hands keeps its record, its index, its name AND its coords, and
only the owner byte plus the queue change — measured in
`evidence/trace_m56_build_20261026_165917.jsonl` r4, index 0 stayed `"University Base" (28,42)` while
`faction 3 -> 6` and the slots went `[2,2,0,0] -> [384,2,0,0]` with `n_bases` 21 unchanged. So a
cross-window pairing must assert the OWNER byte too; the M62 `queue held — head 2->384` failure was
this identity crossing, not a queue anomaly.
- The queue precondition is the GAME's UI (`scripts/m57_ui_enqueue.py`), and the storage precondition is
`minerals < price` at start — never arm minerals for this mode, or the completion is indistinguishable
from an armed one.
- When a floor fails ONLY because the effect lands after the after-snapshot (pay visible, pending
unchanged, the new record already present at the next window's before-snapshot), widen the OBSERVATION
window using snapshots the run already recorded — this window's before → next window's before — rather
than adding sleeps: a fixed settle either misses the player walk or swallows the next year flip. Keep
the mineral identity exact in the pay window and label the arrival as deferred.

## Accounting rules for production verification

- **Count arrivals as a multiset delta on (x, y, type, owner)** — never record index (compaction
  rewrites slots) and never order (an idle order-0 unit becomes order 1 at the boundary, which
  looks like a new record). A produced unit arrives order 0 ON its base tile; a nonzero order at
  an arrival means cargo/unload or an order reset, not production.
- **Check the whole map, not just our side.** Enemy bases produce even while ours sits empty; a
  boundary inventory that counts only our-side arrivals records a false "zero production".
  Enemy-side queues refill inside the enemy's own AI turn, so a queue read taken during OUR turn
  does not predict their arrivals — floor predictions on in-mask/our bases, report enemy-side
  arrivals as observations. The mechanism is concrete: the visit refreshes the head slot through
  `0x4e5ae0 -> 0x4f6030 -> 0x4e5560` at `0x4ef87e`, BEFORE the price gate (`push 0; push base`, so
  param_2 == 0 and the auto-pick branch is taken), so for any owner outside the human mask the head at
  our snapshot is not the head its own visit will price. Scope the predictor to bases the visit cannot
  rewrite, and say out loud in the code why the others are excluded.
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
3. **INSERT (497,343) does not write a slot index — it INSERTS BY PLAN** (M66 four enqueues with
   two DIFFERENT ids + M67 three more with a cost/plan discriminator:
   `scripts/m66_insert_slot.py --rules sort_key --slots 12`, queue read back after every click).
   The item lands at the first queue slot (`base+0x50 + 4k`, `k = 1 .. pending`) whose type-record
   PLAN byte (`0x98ad88 + type*52 + 42`, the alpha `#UNITS` Plan column) is STRICTLY below the new
   item's plan, else after the region at `k = pending + 1`; everything from that slot rightward
   shifts one slot, and entries already at the same plan stay ahead of the newcomer. **It is NOT
   the cost byte `+41`** — M66 thought it was because every id it measured happens to order the
   same way by cost and by plan; M67 enqueued 193 (plan 2, cost 2) into queues holding 194 (plan 1,
   cost 3) and the item went IN FRONT of the cost-3 entries, twice, in two different bases
   (`evidence/m67_sort_key.jsonl`, `evidence/m67_sort_key_accept.jsonl`). The shift is capped to
   the 10-slot queue array `+0x50..+0x74` (head + 9 region slots): stale ids inside it are pushed
   ALONG with the shift and the dword at `+0x78` (queue slot 10) never moves — read 12 slots, not
   8, or the cap is invisible and a correct insert scores as no rule at all. `pending` `+0x4c`
   rises by 1 (cap 9 at `0x418b05`) and **the head slot `+0x50` is never written by INSERT** — it
   read 2 before and after in all seven runs. The M57 claim "INSERT writes head `+0x50`, pending `+0x4c`,
   slot `+0x54`" was a duplicate-value artifact: that run enqueued id 2 behind a head that was
   already 2. **OK (285,343)** commits (mode 0, no restore); CANCEL restores from the stack
   snapshot. Re-read pending ~1 s later. The enqueue also adds 1 to the per-faction queued byte
   `0x94de84 + 0x20bc*owner + type` (read the SETTLED state after OK: mid-click the whole row reads
   one lower for every queued id).
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
- The pay at 0x4efed8 takes a value that is NOT reliably the price: 10 was deducted at price 10 in an
  armed run (`SPENDA old=200 new=190 edi=10`), but live game-queued builds paid 9 (storage 7 -> 9 ->
  0), 5 (5 -> 0) and netted -5 from 8 at price 10. Treat `$edi` there as MEASURED-ONLY, and do not
  floor an acceptance on "storage delta >= price" until a store sequence names the amount. Clamp B
  (0x4eff20) stores only when storage > min(`*0x92a370` = 10, d0).
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
  CONTENT, and by content read **with the chooser OPEN** — `0x596000` rebuilds and re-sorts all 128
  entries on every paint, so the array read before opening the chooser is already stale (M66, the
  same box: `[192,194,193,2,0,1,195,...]` pre-open vs `[192,195,194,193,2,0,1]` open; the id the
  game stored always equalled the entry at the clicked cell read at click time).
  `scripts/m57_ui_enqueue.py` and `scripts/m66_insert_slot.py` script all of it with read-backs.
- The enqueue dispatch `0x417ee0` fires with `*0x8f0d60` = the target base (proved live), but
  m53g_drive's static store addresses (`0x418b57/0x418ad3/0x418ac7/0x418b24`) did NOT hit on the
  INSERT write — re-derive before trusting them. M66 read that window of the whole-`.text` dump:
  `0x418b0a-0x418b0b` increments `*0x8f0d60 + 0x4c` (pending) with a cap of 9 at `0x418b05`,
  `0x418b32` reads the slot at index = the NEW pending and pushes it into `0x62732a` with the buffer
  `0x689974`, and `0x418b57` (`mov [edx+0x50],eax`, the head store) is gated on `esi == 0` at
  `0x418b46`, which cannot hold after the increment — so none of these is the store that moved the
  queue in the four measured enqueues. Which branch INSERT takes is still unassigned (STATIC, never
  traced).
- The base array compacts mid-game: Korolev Center's index walked 17->18->17 within one session
  (n_bases 29->19->23->25). Locate bases by NAME/(x,y), never by remembered index.
- The acceptance run `m56_build.py --ui-queued 17 --boundaries 8 --timeout 240` FAILED
  (`evidence/trace_m56_build_20261025_215056.jsonl`): 0/0 positive predictions (income read 1/round,
  completion landed at minerals 7 + a fresh recompute), r4 bookkeeping BAD, r6/r7 walk-home BAD (the
  after-snapshot at `--settle 0.3` caught cur_player mid-walk — use `--settle 2.5`; a sampling fix,
  not a floor change). Nothing weakened; nothing merged.

## Enumerating every write to `base+0x40` (the only way to settle the credit)

Boundary sampling ranks hypotheses; it cannot attribute a delta to an instruction. To settle the
credit, log the stores themselves:

1. Break at EVERY candidate write site, each conditioned on the base pointer: `0x4ef7f6` (income add),
   `0x4eff20` (clamp B), `0x4efed8` (pay), `0x4f0cc3` (clamp after pay), plus any store inside
   `FUN_004ef6d0` / the queue tail of `FUN_00417ee0`. A site you did not instrument is a delta you
   cannot explain.
2. Per hit, read the fields from the BAKED base address (pending `+0x4c`, head `+0x50`, d0 `+0xd0`,
   progress `+0x3c`, rate `+0xcc`, flags `+0x30`, storage `+0x40`) BEFORE the instruction, `si` once,
   and read them AFTER. Never report a register as a field value.
3. Order the hits by time into one sequence per visit and close the arithmetic: sum of the deltas must
   equal the observed net change for that visit. Any leftover is an unattributed store — go find it
   rather than fitting the model to the difference.
4. Gate on "every delta in N consecutive boundaries attributed to a named site, zero unattributed":
   that gate can pass, whereas "predict the arrival round from the round-start snapshot" cannot while
   the visit recomputes `+0xd0`.

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

## M57-4 (session 96) — every store to `base+0x40` in one visit, NAMED (PASS)

The visit is `FUN_004f5a70(base_index)` (one caller, `FUN_00520540`): it computes
`lea ecx,[index*304 + 0x95da10]` and stores it to the current-base global `DAT_0x8f0d60` at
**0x4f5a99** — that instruction is the per-visit marker, since `$ecx` IS the record address —
then calls 0x4e8d60, 0x4e78e0, 0x4e92c0, 0x4e93f0, 0x4eaa10, **0x4ef6d0** (the production
visit) and **0x4f26e0**. A whole-image store census (`objdump -d -M intel --section=.text`,
every `... DWORD PTR [reg+0x40]` store mapped to its function through `ghidra_out/index.csv`,
kept only if the function is call-graph reachable from 0x4f5a70 / 0x417ee0 / 0x4f6030, depth 4)
yields **23 sites**; the `lea reg,[reg2+0x40]` pointer-arithmetic shape has no store through
such a register in those sets, so the list is complete for a visit. Harness:
`scripts/m57_stores.py --base "Korolev Center" --boundaries 3` — 23 breakpoints each conditioned
on the store's OWN base register == our record, plus the visit marker and a 2 ms sampler.
Acceptance is the replay: every store's `before` must equal the replayed current value, every
sampler-observed value must be reproduced by the replay, per-boundary sums must equal the observed
net changes, and the run must record >= 1 store with >= 1 non-zero net boundary. PASS 2026-10-26:
4 stores / 3 visits / 3 boundaries, zero unattributed deltas.

What one visit actually does to `+0x40` (all read back at Korolev Center):
- **ADD `0x4ef7f6`**: `edx = [base+0x40] + [base+0xd0]`; the delta EQUALS the `d0` field as it
  reads AT THE VISIT (measured +2 with d0 2, and +1 with d0 1 twice — d0 moves when the garrison
  changes), gated `d0 >= 0 && head != -38 && !([base+0x30] & 2)` (0x4ef7db-0x4ef7f9).
- **the completion gate is `cmp [curbase+0x40], edi ; jge` at 0x4efa5e**, with `edi` built at
  0x4efa4b-0x4efa52: `edi = eax` from `call 0x4e40a0` (item cost for the faction) then
  `imul edi, eax` from `call 0x5ac950` (a factor). Measured `edi = 9` for a queued Scout Patrol,
  in two separate runs — **not the 10 the M56 model deducts**.
- **PAY `0x4efedd`**: `esi = [ecx+0x40] - edi` (ecx = `DAT_0x8f0d60`). Measured 9 -> 0 and
  10 -> 1: the deduction is the computed 9. So the arrival round is the one where
  `storage + d0 >= 9`, which is exactly how the price-10 model fails live (arrival measured at
  minerals 8 while the gate printed "queue held — minerals 8 vs price 10").
- **CLAMP `0x4eff20` / `0x4f0ce9`** store `max(0, min(cap `[0x92a370]`, d0))` and only when
  `storage >` that limit; they never fired in any measured window (storage after the pay is 0-1).
- **`0x4f2d7d`** in `FUN_004f26e0` (the driver's post-visit call) is a division-based distribution
  store — instrumented, never hit for our base in the measured windows.
- the pop leaves stale ids in the slot tail: slots read `[2,2,2,2,2,0]` after four completions,
  so `pending` is the only queue truth and a stale head still passes the add's `head != -38` guard.
- **the M56 gate still fails with every floor intact** (`m56_build.py --ui-queued 17
  --boundaries 10 --timeout 300` -> `FAIL production prediction accounting`, 0/0 positive
  predictions, arrival at 8+1 >= 9 vs price 10). The next RE target is the price itself:
  `0x4e40a0` (cost) x `0x5ac950` (factor).

## M58 (session 97): the price IS named, and it is live STATE, not a constant

`0x4efa2c-0x4efa52` (whole-`.text` dump): `ebx = [curbase+0x50]` (the queue head), `cl = byte
[curbase+4]` (the owner), `push -1; push 1; push ecx; call 0x4e40a0` -> `edi` = the per-owner cost
factor **in tenths**; then `push 0; push [0x68cbb0]; push ebx; call 0x5ac950` -> `eax` = the type's
cost; `imul edi,eax` is the price the `0x4efa5e` gate compares.

- `0x4e40a0(owner,1,-1)`: mask `[0x985b10]&0xff` bit(owner) -> 10, else the era table
  `[0x68cbb8+era*4]` = {13,12,11,10,8,7}; rescale `[0x92a294]` (param_2==1 picks the +4 variant);
  then **`[0x92ada8]`: 1 -> x9/10, 0 -> x8/10, else unchanged** (it is the difficulty scalar — the
  scenario LOAD pane literally prints `difficulty level: talent`); then `switch` on
  `[0x94d6a0 + owner*0x20bc]` (the government field; 0 = identity).
- `0x5ac950(type, [0x68cbb0], 0)` = byte `0x98ad88 + type*52 + 41`, clamped to >=1 (<=999) ONLY when
  plan byte `+42 == 8` and param_2 > -1; `type < 0x40` returns it immediately.
- Live University-faction game: mask 0x08 (owner 3 in), a294 10, **ada8 1**, gov 0, type 2
  `Scout Patrol` `+41 = 1` -> **price 9**. Sessions 56/64 measured ada8 = 2 -> price 10 and M52b
  debited 10: **the price is per-game difficulty state**. `scripts/m58_price.py` prints the chain
  from live memory; `m56_build.py cost_multiplier()` re-derives it per run.
- **The pop is strictly after the pay** (`evidence/m58pop.gdblog`): the `0x4efedd` pay store executes
  with pending STILL 1; pending reads 0 at the NEXT visit. The pop store is `0x4ef641` in
  `FUN_004ef5d0` (called from the unit path at `0x4f037b`/`0x4f0f46`). A boundary after-snapshot can
  land on either side — never assert a same-window pop.
- **pending is NOT the queue truth**: a base paid the derived price twice more at **pending 0**
  (minerals 7 + income 2 = 9: once with no unit appearing — confounded with a disband — once with a
  unit appearing), and a second Scout Patrol appeared on a base with minerals 0 and pending 0. A
  head SLOT holding a unit type keeps being bought whenever `storage + income >= price`. M59's job:
  `FUN_004ef5d0`'s affordability call `0x5a73f0(head, owner, index)`, the `0x94de84 + owner*0x20bc`
  byte array, and the slot array vs `+0x4c`.
- Mineral bookkeeping is an IDENTITY, not a `>=`: `storage_after == storage_before + credit - price`
  with credit = `+0xd0` when positive (the add at `0x4ef7f6` is gated `d0 >= 0`); measured
  8+1-9=0, 8+2-9=1, 8+1-9=0. The old `storage_before - storage_after >= price` ignored the credit
  the model itself predicts and only passed because the armed run had income 0.

## M61 (session 100): where the create sits in the round; `base+0x10` is the NAME, not a field

Measured with `scripts/m60_guard.py --stage watch --boundaries K` — conditioned breakpoints on the
visit `0x4ef6d0`, the pay store `0x4efedd` and the create call `0x4eff4e`, plus hardware watchpoints
on the guard `0x8f0d70`, the year `0x985b00` and `cur_player 0x985dcc`, every command list `silent`
+ tagged printf + `continue`, gdb stdout straight to a file (nothing to drain). Ordered log:
`evidence/m61a_seq.jsonl`.

- **The round order.** The year store `0x51f54f` (`a3 00 5b 98`, right after the round store
  `0x51f53c`) fires while `cur_player` is STILL 7 -> `cur_player` 0 -> 1 -> 2 -> 3 -> our bases'
  visits in ARRAY order (University idx 0, then Korolev idx 18) -> PAY `0x4efedd` (storage - `edi`,
  `edi` = the price) -> CREATE `0x4eff4e` -> `cur_player` 4 -> 5 -> 6 -> 7 -> next year store. Our
  production is therefore four player switches AFTER the flip, inside our own slot, and the pay and
  the create are ONE visit invocation: nothing in `.text` jumps to `0x4efedd`, `0x4eff32` or
  `0x4eff4e` (grep finds only the instruction addresses plus the `jne 0x4eff5c`), and the live log
  prints PAY and CREATE adjacent with nothing between. NAMED.md calls the year store `0x51f554`;
  that is the `call 0x478530` AFTER the store — the bytes win.
- **An arrival is never a round late; a SNAPSHOT can be early.** `ds:0x8f0d60` names the record the
  round processor is visiting (it is stored per base before the pipeline that reaches `0x4ef6d0`),
  so it says which base has been reached. A window's after-snapshot that still names ANOTHER base
  was taken before this base's visit, and an arrival missing from it says nothing about the create.
  `m56_build.py` logs `cur_base` at every after-snapshot and REFUSES the F1 deferral when the
  pointer already named the predicted base (`scratch/m61/fixture_beat_visit.json` exit 1 vs
  `fixture_defer_ok.json` exit 0 — the two differ in that one field).
- **`base+0x10` is not a field.** The base NAME starts at record byte +19, so a dword read at +0x10
  is bytes +16, +17, +18 (three small unnamed bytes) plus the name's FIRST CHARACTER in the top
  byte: 24/24 bases have top byte == name[0] (`scratch/m61/census10.py`) — Korolev Center
  `0x4b000000` = 'K', University Base `0x55000000` = 'U', both with +16..+18 zero. Never read
  `[base+0x10]` as a flag or a guard: the old note was wrong twice over (Ghidra `short *` offsets,
  then this straddle). Check a record's BYTE layout before believing any dword-level claim about it.
- **A dialog on screen swallows every UI click.** `m57_ui_enqueue`'s "INSERT never landed" was an
  Operations Director "the minerals output of Korolev Center is not sufficient to support Scout
  Patrol ... the unit has been disbanded" dialog (`classify()` == `dialog`) sitting over the BUILD
  pane; the chooser guard updated, the INSERT clicks did nothing. Clear dialogs (Return on the
  default row) and close panes (Escape) and re-check `classify()` == `hud` BEFORE a UI enqueue.
- **Producing a unit zeroes the base's mineral credit** (`+0xd0` 1 -> 0, or -1), and the income add
  is gated `d0 > 0`, so storage cannot accrue again until the credit turns positive: a base that
  just produced cannot fund its own next build. A UI-queued acceptance needs `minerals < price`
  AND `minerals + credit >= price` in the same window, i.e. credit >= 1 — after two productions
  both our bases sat at minerals 0 / credit 0 and only a reload (`m54a_load --relaunch` ->
  `m54g_prep` -> one turn -> enqueue) restored that shape.

## M62 (session 101): open a session with the instruments, not with prose

Run these before touching the game; they exist because M61/M62's losses were *state* failures,
not knowledge failures.

- `python3 scripts/session_brief.py` — <= 4 KB of machine truth: verdict, our bases, the tagged
  `CONFLICT:` lines from NAMED.md, next pick, first commands. Exit 0 = READY, 1 = blocked.
- `python3 scripts/accept_ready.py` — the readiness oracle. **`READY` means a positive prediction
  is possible, NOT that the run will pass** (a support-disband can eat the created unit). Order:
  screen class -> running gdb -> evidence headroom -> per base `pending > 0`, `minerals < price`,
  `credit > 0`. It prints ONE fix, not a list.
- `python3 scripts/evidence.py audit [--delete]` — cites come from the docs AND `scripts/*.py`
  (classifier frames are safe). **`load_cites()` used to omit `.jsonl`** (and putting `json`
  before `jsonl` hides a naive fix), so no trace could ever be cited and the audit called 12.7 MB
  of live evidence garbage. Verify a citation checker against a file you KNOW is referenced.

Rules that came out of it:

- A modal on screen voids every click and every turn-end key. `classify()` before any UI enqueue;
  Return clears a dialog's default row, Escape closes a pane. Two enqueues clicked into an
  Operations Director popup before anyone noticed.
- Fixture replays are reproductions, not evidence: `m56_build.py --fixture` now writes its trace to
  `$TMPDIR`, so `evidence/` only holds runs meant to be cited.
- **A queue slot is NOT reliably a type id**: 38/303 of our-base rows and 2804 rows across all
  traces hold a value outside `0..23` (`-41`, `-3`, `384`, `386`, ...). Never add a global "slots
  are types" floor (it fails on AI bases every run) and never let a garbage head reach a prediction.
- When a base dies mid-run, its record fields and the queue anomaly land in the SAME windows:
  write "confounded", keep both hypotheses, do not narrate a cause.

## M64 (session 104): the accrual phase is MEASURABLE, and an arrival is attributed by the PAYMENT

Rules for any round-boundary harness that predicts per-base production from memory:

- **Never add this round's income to a before-snapshot without measuring whether it is already
  inside it.** A window's after-snapshot and the NEXT window's before-snapshot are the same round
  read twice (the loop breaks the instant `cur_player` comes home, then re-reads a few ms later),
  and the engine plays in that gap, so a base's visit — and its `+0xd0` add at `0x4ef7f6` — can run
  between the two reads. The pair itself is the tell: a minerals delta equal to the income IS that
  add (the add is exactly `+0xd0`, gated `d0 > 0`). Measured, Korolev Center, income 1, price 9:
  r1-after 7 -> r2-before 8 (add landed in the gap, so the gate is 8, not 9) and r2-after 8 ->
  r3-before 8 (not yet, so the gate is 9). Adding the income both times predicts the payment one
  window early and breaks the mineral identity.
- **Attribute an arrival by the payment, never by the current-base pointer.** PAY `0x4efedd` and
  CREATE `0x4eff4e` are one visit invocation, so a window whose minerals show
  `after == before + credit - price` DID make the unit even when the unit-array read inside the
  same snapshot missed the write. `ds:0x8f0d60` naming the base proves neither: it named Korolev
  Center at the after-snapshot of a window that had just paid 7 -> 0 with no new unit on the tile,
  and that unit was there in the next read of the SAME round.
- **Read the arrival back, and compare COUNTS of `(x,y,type,owner)`, not key presence.** A garrison
  of the same key already sits on the base tile, so "the key is in the snapshot" says nothing about
  an arrival. The unit array compacts (records die, indices shift down: the same two garrisons read
  54/62, then 53/61, then 52/60/73 across one round) and a produced unit's `order` goes 0 -> 2 the
  moment anything orders it, so neither `idx` nor `order` is an identity across reads.
- **Account for the snapshot gap explicitly.** A before->after diff cannot see anything that lands
  between one window's after-snapshot and the next window's before-snapshot; if you attribute
  arrivals into that gap, add a matching gap floor or an unexplained arrival hides there.
- A screen gate built on ONE OCR pass is a coin-flip while the map animates: 14 straight
  `classify() == 'unknown'` verdicts on frames that are visibly the plain HUD (MENU / COMMLINK / TURN
  COMPLETE / unit panel / `Mission Year`). Re-freeze until a known token lands, and look at the
  frame before believing a modal.
- The box does **not** auto-play while one of our units needs orders: `cur_player 3` sat unchanged
  across three reads 4 s apart and three Return presses moved the year two rounds (and the base
  bought: minerals 5 -> 0, credit 2 -> 1). "It auto-plays while nothing drives it" is true only with
  everything on Hold.

## M68 (session 108): the enqueue may APPEND — a sorted read-back does not make the sort universal

**Rule that matters more than any single finding: a live sorted landing does not prove a sort
key.** On the save's University Base at round 51 (minerals 0, region empty, 67-entry chooser) five
INSERTs of ids 2, 1, 194, 192, 193 wrote region slots **1, 2, 3, 4, 5** — one append per click —
while a pre-click gate had certified that only the plan byte `+42` predicted the landing sequence
1,1,3,4,3 that M67's rule implies. An append is predicted by **55 of 212** candidate rules (every
byte constant across those ids, plus `+45` and `+50`, whose values are monotone in that click
order), so the run names no key. M67's three sorted read-backs (Korolev Center, and a University
Base built up over 60 rounds, minerals 3 and 1, pending 2/4/6) remain real and unexplained — the
difference is CONFOUNDED with base, round, minerals, queue occupancy and chooser size, because one
reload changed all of them at once.

**How to spend a session here.** Do not search click orders again while the engine demonstrably
appends: score all 212 rules (52 offsets x desc/asc x ties after/before, plus four whole-name
rules) against the WHOLE write sequence, gate on KEYS not conventions (`42:desc:after` and
`42:desc:before` agreeing means the tie direction went untested, not that a rival agreed), and
when the writes are an append, stop clicking and gdb the enqueue (`0x418afd` entry, `esi` at
`0x418b29`, watch `base+0x54`). The identifier and the gate are `scripts/m68_key_run.py` +
`scripts/test_m68_key_rules.py` (35 pinned cases); the read-only record dump that defines the
candidate set is `scripts/m68_typebytes.py`.

**Three live facts the clicks produced, worth more than the FAIL:**
- The engine **refuses to enqueue a type the queue already holds** — a second INSERT of 193 left
  pending and every slot unchanged. A duplicate is a no-op, not just an unreadable shift.
- The chooser cell -> pixel map `(128+127*(cell%5), 60+100*(cell//5))` is **unreliable past row 0**:
  cells 6 and 4 failed to register in three probes (the driver's `guard` field stayed on the previous
  selection and INSERT did nothing). One cell-6 click that DID register made the queue store **-3
  (0xfffffffd)**; the next INSERT then appended a plan-9 item at the END of the region. Verify
  `guard == cell` AND the cell's entry before clicking INSERT; treat -3 as a bad click until gdb
  says otherwise.
- Static confirmation of M67's cap: `0x418ab3-0x418acb` copies `[base+0x74]` down to `[base+0x54]`
  up one slot and never touches `+0x78`. The head-slot sentinel compared at `0x418b5f` is
  `0xffffffd9` = **-39**, not the -38 earlier notes quoted.
