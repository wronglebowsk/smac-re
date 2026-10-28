# Session notes archive — sessions 107-107

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
