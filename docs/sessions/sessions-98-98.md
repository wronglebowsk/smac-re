# Session notes archive — sessions 98-98

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 98 (2026-10-26) — M59: **THE QUEUE TRUTH IS THE HEAD SLOT, NOT PENDING.** `pending` gates only the POP; the pay block dominates the create, and a base with an EMPTY queue still buys the head's type every round it can pay. The acceptance printed **PASS** on one real invocation.

**Static, from the instruction bytes (scratch/m59/queue_census.py + scratch/m59/dom.py over
scratch/m574/text.txt).** In the per-base visit `FUN_004ef6d0`: income add `0x4ef7f6` → price gate
`0x4efa2c-0x4efa61` (`ebx = [base+0x50]` = the HEAD SLOT, `edi = 0x4e40a0(owner,1,-1) ×
0x5ac950(ebx, base, 0)`, `cmp [ecx+0x40], edi; jge 0x4efadc`) → pay `0x4efedd` → clamp
`0x4eff02-0x4eff23` → **create-unit call `0x5ab650(type, ?, x, y)` @ `0x4eff4e`**, guarded at
`0x4eff32` by `[base+0x10] == 0`. A dominance test (block-level CFG, pay block removed) prints
`entry->create: True / with the PAY block removed: False` and the same for gate→create: the pay
DOMINATES the create. Nothing between them reads `+0x4c`. The pop `FUN_004ef5d0` returns at
`0x4ef5f4` (`je 0x4ef684`) when pending == 0 and is called LATER in the same visit
(`0x4f037b`, `0x4f0f46`; the third site `0x4ef992` is NOT reachable from the pay) — it only
left-shifts the slots and decrements pending + the per-faction queued-count byte
`[0x94de84 + owner*0x20bc + type*4]` (`0x4ef613`, `dec BYTE PTR [ecx]`).

**NAMED.** `0x5a73f0(type, owner, base)` = "can this faction field this unit type here": needs
the type-record flag `[+0x30] & 1`, the owner NOT in the exclusion dword `[+0x2c]`, and the
required facility/project `[+0x32]` either −1 or researched-and-owned; types ≥ 0x40 are
faction-specific (`(type>>6) == owner`); the shared tail also rejects plan `[+42] == 8` when
`0x985ac4 & 0x400000`, and rejects when the class byte `[+0x24]` indexes `[0x92ae81] == 1` and
`0x4e4620(base_x, base_y, 0) == 0`. `0x5a6e70(-id, owner, base, 0)` is the same question for a
facility/project queue item (queue stores those NEGATIVE). `FUN_004e47d0` (called from
`0x4ccbdd`/`0x59d894`/`0x5a01f8`) initialises a base: zeroes `+0x30`, `+0x34`, `+0x3c`, `+0x40`,
`+0x4c`, sets `+0x38` from `[faction+0x94d600]`, then calls `FUN_004e46f0(base)` which picks the
cheapest-scored buildable unit type into the HEAD SLOT ONLY (`[+0x50]`, `0x4e471b`/`0x4e47bb`,
pending untouched — this is why a founding leaves head 2 with pending 0). `FUN_004e5560(base,
new_head)` writes the head and adjusts the per-faction queued-count byte (`dec` old at
`0x4e55b5`, `inc` new at `0x4e55dd`). `FUN_004e5ae0(base, 0)` — called SIX times from the visit,
first at `0x4ef87e` BEFORE the gate — refreshes the head through the chooser `0x4f6030` for any
owner not in the human mask, or when `+0x38`'s sign bit is clear, or (always, at this call site)
when param_2 == 0. Pending is written at only four absolute sites: `0x4e4982` (init), `0x4ef642`
(pop), `0x50890d`, `0x543b26` (clear).

**Measured in memory, one variable, internal control (`scripts/m59_head.py`, box at 2174, no
tracer, all our units held first):** `POKE 'Korolev Center' idx 17 +0x40: 0 -> 9 (read back 9)
OK`; one turn later Korolev minerals `9 -> 0` (exactly the derived price 9), income `0 -> -1`
(the new unit's upkeep), **pending 0 -> 0**, head 2 -> 2, and the base tile went 5 -> 6 units of
(type 2, owner 3); control University Base idx 0 (minerals 0, gate not passed) stayed 0 minerals
and 6 -> 6 units. A base with an EMPTY queue buys the head slot's type.

**Rule restated** (`predict()` in `scripts/m56_build.py`): arrival iff the base is OURS
(`0x91b5b4`; another faction's head is re-picked by its own visit at `0x4ef87e` before its gate,
so it is not predictable — enemy arrivals are still REPORTED by F2) AND the head is a unit type
(0..0x3f) AND the owner is in the mask AND `storage (+ income) >= price`. Pending is not a term;
`pop_expected` replaces it as the pop predictor. Bookkeeping now covers pending-0 bases (a paid
pending-0 base must leave pending 0 and the slots unchanged — the pop cannot fire) and PAIRS BY
NAME, not index (mid-run the array compacted Korolev 18 -> 17 again). F1 verifies an arrival in
the pay window OR by the next window's before-snapshot, because the create was measured landing
in the snapshot gap (run `..._144801` r2: pay 8 -> 1 with pending still 1 at both snapshots, our
unit total 6 at r2-after -> 7 at r3-before, r3's own window adding nothing).

**ACCEPTANCE — PASS on one real invocation.**
`python3 scripts/m56_build.py --ui-queued 17 --boundaries 10 --timeout 400 --no-poke-hold`
(queue filled by the GAME's BUILD UI via `scripts/m57_ui_enqueue.py --base-index 17 --cell-item 2
--inserts 1`, units held by `m59_head.py --stage read --hold` first, minerals 8 < price 9 at
start) -> `PASS production prediction: 1 verified unit arrivals over 10 boundaries, every
prediction and every observed arrival accounted, queue bookkeeping exact — queue filled by the
GAME's BUILD UI (0 memory writes), paid by income at 1/round`; 50 `ok` checks, 0 BAD;
`r0 prediction base 17 (29,42) type 2 — predicted (pending 1, minerals 8 >= price 9); observed
net 1`; `boundaries observed >= 2 — 10 of 10 rounds flipped`; `POSITIVE prediction verified —
1/1`; `memory writes: 0`. Trace `evidence/trace_m56_build_20261026_145157.jsonl`. Rule cases
`python3 scripts/test_m56_predict.py` -> `PASS 17/17` (cases 5/6 restated for the new scoping,
14-17 added for the pending-is-not-the-gate rule); bad fixture
`python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit 1 (BAD minerals
identity 100 + 0 - 10).

**Two runs did NOT pass before it, and no floor was weakened:** `..._144801` (10/10 boundaries,
2 positive predictions, 1 verified — the r2 deferral above, which is what forced the F1 window
change) and `..._145103` (1/1 positive verified, 10/10 boundaries, single BAD = the known r2
walk-home race `cur_player before 3 after 6`, which the footing says to re-run rather than
edit).

**Open.** (1) the create guard `[base+0x10] == 0` at `0x4eff32` is unread — what writes it, and
whether it is the reason a paid window can show no unit; (2) `FUN_004f6030` (the chooser, called
with a budget argument from `0x4e5ae0`) is unnamed — it decides what an AI base builds next and
therefore what its head slot will be; (3) the deferral window is a snapshot-timing fact, not yet
a timed model (the create's exact place in the round sequence is still inferred); (4) the older
skill note `0x94dc84` vs the disasm `0x94de84` for the queued-count byte is REPORTED, unresolved;
(5) enemy-base production is reported, never predicted.

**Next pick (M60): name `0x4f6030` and the `[base+0x10]` create guard.** With those two, the
arrival rule can be stated for other factions too (their head is whatever `0x4f6030` picks) and
the "paid, no unit" windows get a mechanism instead of a deferral.
