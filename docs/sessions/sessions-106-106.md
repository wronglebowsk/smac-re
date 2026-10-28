# Session notes archive — sessions 106-106

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
