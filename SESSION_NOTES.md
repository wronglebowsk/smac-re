

Older sessions: `docs/sessions/sessions-95-96.md` (2 sessions). Read it only when a question reaches back before session ## Session 97.

## Session 97 (2026-10-26) — M58: **THE PRICE IS NAMED — `0x4e40a0(owner,1,-1)` × type record `+41`, and the multiplier is live STATE, not 10: `[0x92ada8] == 1` makes it 9.** The M56 gate's price-10 was one game's difficulty. The acceptance never printed PASS, so **nothing was merged**.

**The call site (scratch/m574/text.txt, `objdump -d -M intel --section=.text`).**
`0x4efa2c mov ebx,[eax+0x50]` (eax = `DAT_0x8f0d60` = the base record, so ebx = the queue head),
`0x4efa31 mov cl,[eax+4]` (the base's owner byte — `base_dump.py`'s `fac`), `push -1; push 1; push
ecx; call 0x4e40a0` → `edi`; then `mov edx,ds:0x68cbb0` (the base index the visit is running),
`push 0; push edx; push ebx; call 0x5ac950` → `eax`, `0x4efa52 imul edi,eax`, `0x4efa5e cmp
[curbase+0x40],edi ; jge`. Ghidra agrees: `FUN_005ac950((int)*(short*)((int)&DAT_00933282 + …),
0xffffffff, …)` in `ghidra_out/shard_014.c:7994` proves its arg1 is a unit TYPE id.

**`0x4e40a0(owner, 1, -1)` is the per-owner cost factor in TENTHS** (`evidence/m53i_fn4e40a0.txt`,
`ghidra_out/shard_012.c:13825-13880`): mask `[0x985b10] & 0xff` tested bit-by-bit → 10 (`0x4e40c0`),
else the era table `[0x68cbb8 + era*4]` = {13,12,11,10,8,7} (sessions-64); rescale by `[0x92a294]`
(param_2 == 1 picks the +4 variant, `0x4e4119`); then `[0x92ada8]`: 1 → ×9/10, 0 → ×8/10, else
unchanged (`0x4e413b-0x4e4175`); then `switch` on the dword `[0x94d6a0 + owner*0x20bc]`
(sessions-56 calls it the faction government field; 0 = identity).

**`0x5ac950(type, DAT_0x68cbb0, 0)` is the type's cost**: the byte at `0x98ad88 + type*52 + 41`
(the M53b/M53f cost byte), clamped to ≥1 (and ≤999) ONLY when the plan byte `+42 == 8` and
param_2 > -1; type 2 has plan 3 → no clamp, and `type < 0x40` returns it straight out of the
`0x5ac993` branch (`ghidra_out/shard_015.c:23696-23745`).

**Live, read back:** mask `& 0xff` = 0x08 (owner 3 in), `[0x92a294]` = 10, `[0x92ada8]` = 1,
government field 0 → factor 9; type 2 `Scout Patrol` `+41` = 1 → **price 9**.
`python3 scripts/m58_price.py --owner 3 --type 2` -> `DERIVED price = factor_tenths 9 *
type_cost 1 = 9 … tracer-measured edi … MATCH`. **This is why sessions-56/64 saw 10**: they
measured `[0x92ada8] = 2` (no rescale) and M52b debited 10 — a different game's difficulty, not a
law. The scenario LOAD screen names the same scalar: this session's `m54a_load.py --relaunch`
printed `difficulty level: talent` on the loaded-game pane.

**Code.** `scripts/m56_build.py`: `price_of()` now goes through a new `cost_multiplier(owner)`
that re-implements `0x4e40a0` line-for-line and reads mask / era / `[0x92a294]` / `[0x92ada8]` /
the government field from the SAME snapshot the gate runs on — no constant chosen to fit an
observation. `scripts/test_m56_predict.py`: `MockMem` now serves those inputs (defaults = the
session-56 state, so every pre-M58 case keeps its numbers) and two cases were added —
`python3 scripts/test_m56_predict.py` -> **`PASS 13/13 production-prediction cases`** (case 12
ada8 1 → price 9; case 13 ada8 0 → 8 vs ada8 2 → 10 on an identical base, one variable).
`python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit **1** (unchanged).

**The bookkeeping was rebuilt on two measurements.** (a) `evidence/m58pop.gdblog` (Korolev Center
0x95ee40, queue UI-filled, minerals poked to 9 and read back): `VISIT#1 storage=9 pend=1 |
0x4ef7f6 add +0 (d0 0) | 0x4efedd pay 9->0 with pend STILL 1 | VISIT#2 storage=0 pend=0` — the pop
store `0x4ef641` (in `FUN_004ef5d0`, whose unit-path calls are `0x4f037b`/`0x4f0f46`) runs
STRICTLY AFTER the pay store, so a boundary after-snapshot can land on either side of it. Session
96's "pending 1 -> 0 in the same visit" is therefore not a rule: the 2177-box run read 1->1 then 0,
the 2151-box run read 1->0 in the pay window. (b) the mineral identity
`storage_after == storage_before + credit - price` is EXACT — measured 8+1-9 = 0 (2177 box),
8+2-9 = 1 (2151 box r2), 8+1-9 = 0 (evidence/trace_m56_build_20261026_142139.jsonl r8). The old
`storage_before - storage_after >= price` ignored the credit the model itself predicts
(`income_first`) and only ever passed because the armed run had income 0.

**ACCEPTANCE — three real invocations, none printed PASS (so nothing merged).**
1. `python3 scripts/m56_build.py --ui-queued 17 --boundaries 10 --timeout 300` (2177 box, queue
   GAME-filled, `memory writes: 0`) -> `FAIL production prediction accounting`: positive
   **1/1 verified**, **10/10** boundaries flipped, provenance + storage-below-price (2 < 9) ok;
   BAD `pending decremented` (1->1 in the pay window) and `minerals debited by >= price`
   (8->0, delta 8 vs the then-price 10). Those two BADs are what forced the rewrite above.
2. After the reload (`SMAC_SAVE='m54b_clean.SAV' m54a_load.py --relaunch` → HUD 2150 →
   `m54g_prep.py` → one `smac_play.py --turns 1` turn founds Korolev Center at (29,42) in 2151 →
   `m57_ui_enqueue.py --base-index 18`): `--ui-queued 18 --boundaries 12 --timeout 420` ->
   `FAIL`: positive **1/1** (r2, 8 + 2 - 9 = 1 exact), **12/12** boundaries, provenance ok; BAD the
   brand-new "no pop in the pay window" (r2 popped in-window) and `r11 unexplained ORDER-0 arrival
   on OUR base 17` — minerals 7 -> 0 (7 + 2 = 9 = the derived price) with a unit appearing while
   **pending read 0**.
3. `--ui-queued 17 --boundaries 10 --timeout 400` (`evidence/trace_m56_build_20261026_142139.jsonl`)
   -> `FAIL`: positive **1/1** (r8: 8 + 1 - 9 = 0 exact, unit +1 on (29,42)), **10/10** boundaries,
   provenance ok, 0 < 9 ok; BAD r0 walk-home race (`cur_player 6` at the after-snapshot), r9
   queue-held firing on the deferred pop (fixed after the run, NOT re-run), and r9 an unexplained
   +1 type-2 unit on University Base (28,42) with minerals 0 and pending 0.

**THE NEW FINDING — M59's target: pending is NOT the queue truth.** Korolev paid the derived price
twice more at **pending 0** (run 2: r6 minerals 7->0 with no unit appearing — confounded with a
disband — and r11 minerals 7->0 with a unit appearing), and a second Scout Patrol appeared on
University Base at minerals 0, pending 0 (run 3 r9). A base whose head SLOT holds a unit type keeps
buying it whenever `storage + income >= price`; M57-4's "pending is the only queue truth" is wrong.

**Trap.** `m57_ui_enqueue.py` on a just-founded base can read an EMPTY chooser
(`FAIL: item 2 not in candidate array []`); a second attempt works. Do not conclude the item is
unresearchable from the first attempt.

**Open.** (1) the acceptance has never printed PASS with the derived price — the blockers are the
queue-truth gap above and the r0 walk-home race, not the price; (2) the deferred-pop fix in the
`else` branch is written but not exercised by a real run; (3) `milestone/m58` (local, unpushed)
carries M57 merged in plus all of M58; (4) the r6-style "paid, no unit" windows are unexplained.

**Next pick (M59): the queue truth.** Instrument `FUN_004ef5d0`'s affordability call
`0x5a73f0(head, owner, base_index)` and the slot array (`+0x50..+0x74`) against `pending`
(`+0x4c`), and answer what actually gates the next production; only then can the gate's
arrival/queue floors be stated so that a 10-boundary UI-queued run passes.

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

## Session 99 (2026-10-26) — M60: **THE CREATE GUARD IS A PROCESS GLOBAL, NOT A BASE FIELD — and a nonzero guard really does make a paid window produce no unit. The chooser is named. The "snapshot GAP" was an EARLY READ, not a slow create. ACCEPTANCE PASS on one real invocation.**

changed `scripts/m60_guard.py` (NEW: read / poke / hw-watchpoint on `0x8f0d70`, plus our bases'
minerals, `+0x98` mirror, `+0x30` flags, `+0x38` plan dword and per-tile unit count),
`scripts/m56_build.py` (every sampled timeline row now carries `guard = [0x8f0d70]`; PASS asserts it
stayed 0 — a check ADDED, none weakened), `evidence/m60w_watch.gdblog` + `evidence/m60c.gdblog` +
`evidence/m60d.gdblog` (watchpoint and store-tracer transcripts),
`evidence/trace_m56_build_20261026_153930.jsonl` (the PASS run), this file, `NEXT_PROMPT.md`,
skill `references/production-queue.md`.

**THE GUARD — the footing was wrong twice.** 0x4eff32 is `a1 70 0d 8f 00` = `mov eax,ds:0x8f0d70`,
then `85 c0` / `75 21` = `test eax,eax; jne 0x4eff5c` — a process-global read, NOT `[base+0x10]`.
Base record `+0x10` holds 0x4b000000 (Korolev) / 0x55000000 (University): not a flag.
`grep -c 0x8f0d70` over the whole `.text` dump (40,900,318 B) is **1** — this read — while its
neighbour 0x8f0d60 (the current-base pointer) has 929 references and 0x8f0d64/68/6c are written.
`python3 scripts/m60_guard.py --stage watch --boundaries 2 --timeout 180 --tag m60w` ->
`"guard_writes": 0, "writers": {}, "visits": 53, "guard_values_at_visits": ["0"]` — a hardware
watchpoint saw no writer across 2 boundaries, value 0 at every one of the 53 base visits.

**POKE, one variable, University as control (minerals 4 < price 9, so it cannot pay).**
- guard 1: `python3 scripts/m60_guard.py --stage poke --value 1` -> `POKE 0x8f0d70 (create guard):
  0 -> 1 (read back 1) OK`; `python3 scripts/m59_head.py --stage poke --base 'Korolev Center'
  --minerals 9 --hold` -> `+0x40: 0 -> 9 (read back 9) OK` (`poke_hold: 0 units poked,
  all_held=True` — all 10 were already order 2); `python3 scripts/smac_play.py --turns 1 --timeout
  200 --no-escape 3000 --orders-per-turn 1 --verbose --tag m60a` -> `turn 0: 2182->2183 OK`;
  read back: Korolev minerals **9 -> 0 (the pay ran)**, our unit count **10 -> 10 (no unit)**,
  guard reads 1, University 4 -> 4.
- guard 0: `--stage poke --value 0` -> `POKE 0x8f0d70: 1 -> 0 (read back 0) OK` (it had stayed 1
  through the whole previous turn — nothing wrote it); minerals re-poked 0 -> 9; `smac_play ...
  --tag m60f` -> `turn 0: 2190->2191 OK`; once the player walk came home: Korolev minerals **0**,
  our units **10 -> 11 (the unit arrived)**, guard 0, `cur_player 3`.
The two runs differ in the guard value and in nothing else (same base, same minerals poke, all
units held). They are 8 rounds apart; the reads between them are the timing lesson below, not a
state effect.

**THE ROUND TIMING.** A read taken the instant the year flips can be EARLY. Runs `--tag m60c` and
`--tag m60e` poked 9, ran one turn and read immediately: minerals still 9, `+0x3c` unmoved,
`cur_player 7`, and a 100 s poll changed nothing; the pay and the create landed later in the same
round while the walk came home (`m60f`: minerals 0, ours 11, `cur_player 3`). The store tracer only
appeared to "cause" the pay by WAITING: `python3 scripts/m57_stores.py --base 'Korolev Center'
--boundaries 2 --timeout 220 --tag m60c` -> `VISIT#1 storage=9 pend=0 head=2` /
`STORE#1 pc=0x4ef7f6 site=visit.income-add before=9 src=9` /
`STORE#2 pc=0x4efedd site=visit.pay-minus-edi before=9 src=0` and
`per-boundary net changes: ['2184->2185=-9', '2185->2186=0']` PASS (same shape for `--tag m60d`).
`m56_build` already closes every window on `cur_player` coming home, so its windows are the valid
ones; M59's "the create landed in the snapshot GAP" is this effect, named.

**THE CHOOSER NAMED.** `0x4f6030` = what a base builds next: it scores candidates and keeps the
MINIMUM against `local_124[0]` (seeded `0xf423f` = 999999, tie broken by a secondary key), score =
cost × ~25 halve/double heuristics, and it REJECTS a candidate unless `[base+0x38]` carries the bits
its category requires — the switch on `record[+0x32]` at `0x4fb4xx`: 0 -> 0x200, 1 -> 0x1000, 2 and
3 -> 0x1000 (0x400000 when `[base+0x38] & 0x1000` is clear or `record[+0x2c] != 0`), 4 -> 0x2000,
5 -> 0x800, 6 -> 0x400, 7 and 10 -> 0x800000, 8 -> 0x20000, 9 -> 0x8000, 0xb -> 0x100000, plus
0x80000 for faction-specific types (>= 0x40) whose `record[+0x38] & 4` is clear — and that gate runs
only for owners IN `0x985b10`. Fallback `0x4fd6a0-0x4fd6e5`: scan the 512 type records at `0x98ad80`
stride `0x34` (end `0x9915b2`), keep the `0x5a73f0`-buildable ones with category 1/2/3 and
`record[+0x38] & 4`, take the lowest `record[+0x31]`. Korolev's `[base+0x38] = 0x00dfbe41` carries
0x1000, so Scout Patrol (category 3) passes. **The Ghidra gotcha that caused the old wrong note:**
`DAT_008f0d60` is typed `short *`, so pseudocode `+0x1c` is BYTE `+0x38` — proved by `0x4fb293 mov
ecx,ds:0x8f0d60` / `0x4fb299 test DWORD PTR [ecx+0x38],0x80000000`.

**ACCEPTANCE — PASS on one real invocation.** Setup: `SMAC_SAVE='m54b_clean.SAV' python3
scripts/m54a_load.py --relaunch` (HUD reached, `difficulty level: talent`) -> `python3
scripts/m54g_prep.py` -> `python3 scripts/smac_play.py --turns 1 ... --tag t` (`Korolev Center
founded in 2150`) -> `python3 scripts/m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1`
(`after INSERT 1 (try 1): pending=1 head=2 slots=[2, 2, 2, 0, 0, 0] minerals=5 d0=2`) -> `python3
scripts/m59_head.py --stage read --hold` (`poke_hold: 6 units poked, all_held=True`) ->
`python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold` ->
`PASS production prediction: 1 verified unit arrivals over 10 boundaries, every prediction and every
observed arrival accounted, queue bookkeeping exact — queue filled by the GAME's BUILD UI (0 memory
writes), paid by income at 2/round`; **53 checks, 0 bad**; `boundaries observed >= 2 — 10 of 10
rounds flipped`; `at least 1 POSITIVE prediction verified — 1/1`; `create guard ds:0x8f0d70 read 0
in every sampled row — 5534 sampled rows, values [0]`; `memory writes: 0`. Trace
`evidence/trace_m56_build_20261026_153930.jsonl`. Rule cases `python3 scripts/test_m56_predict.py`
-> `PASS 17/17 production-prediction cases`; bad fixture `python3 scripts/m56_build.py --fixture
scratch/m56_fixture_bad.json` -> exit 1.

**One earlier run did NOT pass and no floor was weakened:** `..._153623` (58 checks, 3 bad) failed
on `r1 boundary: player walk came home to us after the flip — cur_player before 3 after 0` (the
known harness race — the footing says RE-RUN, do not edit the floor), which made the r2 window span
TWO rounds (`kor: 6 -> 1` = 6 + 2 + 2 − 9), so r2's "unexplained ORDER-0 arrival" and
`pending 1->0` were the missed round's events, not a model gap. Its trace was deleted after the
numbers were recorded here (evidence is 29.7 MB of the 30 MB gate).

**Open.** (1) the chooser's ~25 score terms are named as a SHAPE, not enumerated — an enemy base's
head is still reported, never predicted; (2) base record `+0x10` (0x4b000000-style) is still
unexplained — it is NOT the guard; (3) the failure path `0x4eff5c` (shared by a guard-skip and by a
negative return from `0x5ab650`; prints through `0x406720`) and its effect on the rest of the visit
is unread — note `0x5ab650` has exactly ONE negative return, the `n_units > 0x7ff` cap, and n_units
was 96-108, so our paid windows were never cap-blocked; (4) the older reported conflicts
(`0x94dc84` vs `0x94de84`; pay `0x4f0ca6` vs `0x4efedd`) stay unresolved; (5) a writer for
`0x8f0d70` outside `.text` (a save loader, another section) is not excluded — the watchpoint covers
runtime only.

**Next pick (M61): pin the create's place in the round sequence and drop the deferral fudge.**
Record `(cur_player, visit, pay, create)` tuples across boundaries — `m60_guard --stage watch`
already prints the guard at every visit; extend it to stamp the walk position, the `0x4efedd` pay
and the `0x4eff4e` create — so the round sequence says exactly where our visit sits relative to the
year flip and to walk-home, `m56_build`'s F1 "OR by the next window's before-snapshot" branch
becomes a measured position instead of a tolerance, and `predict()` can state the arrival round
exactly. Second half of M61: say what base record `+0x10` is (it is not the guard, and it is not
zero).

## Session 100 (2026-10-26) — M61: **THE CREATE IS IN THE SAME VISIT AS THE PAY, THE ROUND ORDER IS MEASURED, AND `base+0x10` IS THE BASE NAME. ACCEPTANCE PASS on one real invocation.**

**THE ROUND ORDER, read out of one ordered stream.** `python3 scripts/m60_guard.py --stage watch
--boundaries 2 --timeout 400 --tag m61a` (the watch stage was extended this session: conditioned
breakpoints on the visit `0x4ef6d0`, the pay store `0x4efedd` and the create call `0x4eff4e`,
hardware watchpoints on the guard `0x8f0d70`, the year `0x985b00` and `cur_player` `0x985dcc`, each
command list `silent` + tagged printf + `continue`, gdb stdout straight to a file) ->
`events {"YEARW": 2, "PLAYERW": 16, "VISIT": 52, "PAY": 8, "CREATE": 8, "GUARDWRITE": 0}`,
`events_at_our_bases {"Korolev Center/VISIT": 2, "Korolev Center/PAY": 1, "Korolev Center/CREATE": 1,
"University Base/VISIT": 2}`, `visits 52`, `guard_values_at_visits ["0"]`, `guard_writes 0`,
`turn_rcs [0, 0]`. One round of `evidence/m61a_seq.jsonl` (`evidence/m61a_watch.gdblog`):

```
== YEAR FLIP to 2183 (round 83) while cur_player=7
   cur_player -> 0 -> 1 -> 2 -> 3
y2183 r83 cp3 VISIT  University Base   min=6 pend=0 head=2 guard=0
y2183 r83 cp3 VISIT  Korolev Center    min=9 pend=0 head=2 guard=0
y2183 r83 cp3 PAY    Korolev Center    9->0 (edi=9)
y2183 r83 cp3 CREATE Korolev Center    min=0
   cur_player -> 4 -> 5 -> 6 -> 7
== YEAR FLIP to 2184 (round 84) while cur_player=7
```

The year store is `0x51f54f` (`a3 00 5b 98`, right after the round store `0x51f53c`); NAMED.md's
"the year store `0x51f554`" is the `call 0x478530` AFTER the store — reported conflict, bytes win.
Our bases are visited while `cur_player == 3`, in ARRAY order (University idx 0, then Korolev idx
18), four player switches after the flip, in the round whose year has just flipped. The pay and the
create are ONE visit invocation: `grep -n '0x4efedd\|0x4eff32\|0x4eff4e' scratch/m574/text.txt`
returns only the three instruction addresses plus the `jne 0x4eff5c`, so no control flow enters
that block from elsewhere, and the log prints PAY then CREATE with nothing between. **An arrival is
never a round late — a snapshot can be early.** Setup for that run was ONE variable:
`m59_head.py --stage poke --base "Korolev Center" --minerals 9 --hold` -> `POKE ... +0x40: 0 -> 9
(read back 9) OK`, `poke_hold: 0 units poked, all_held=True`, armed before attaching. The first
run's CREATE line printed `guard=3`: at `0x4eff47` eax holds `[ebp-0x28]`, which `0x4ef71a` set
from `BYTE [eax+4]` — the base OWNER byte, not the guard; the printf now reads the global and
prints `owner=` separately.

**F1 IS ATTRIBUTED, NOT TOLERATED.** `ds:0x8f0d60` names the record the round processor is visiting
(`0x4f5a70` stores it per base before the pipeline that reaches `0x4ef6d0`), so it says which base
has been reached. `m56_build.py` now reads it at every after-snapshot (`cur_base()`, logged as
`cur_base` in the `round_after` event and carried in `rounds[r]["cur_base_after"]`) and REFUSES the
deferral when that pointer already named the predicted base — the visit had run, so a still-missing
arrival is a model gap. Run-layer fixtures built from the real PASS trace by
`scratch/m61/mkfix.py` (they differ in that ONE field): `python3 scripts/m56_build.py --fixture
scratch/m61/fixture_defer_ok.json` -> **exit 0**, `PASS production prediction: 1 verified unit
arrivals over 2 boundaries ...`; `python3 scripts/m56_build.py --fixture
scratch/m61/fixture_beat_visit.json` -> **exit 1**, `BAD r0 prediction base 18 (29,42) type 2 —
... NOT deferred: at the after-snapshot ds:0x8f0d60 already named this base, so its visit had run
and the predicted arrival really was absent`. Fixture timelines now also replay the guard samples
(the guard floor cannot be vacuously true on a replayed run).

**`base+0x10` IS THE NAME, NOT A FLAG.** The base name starts at record byte **+19** (NAMED.md
`base_array` row, `M.parse_base`), so a dword read at `+0x10` is bytes +16, +17, +18 (three small
unnamed bytes) plus the name's FIRST CHARACTER in the top byte. Census
`python3 scratch/m61/census10.py` over all 24 live bases: `topbyte==name[0]: 24 / 24` — Korolev
Center `0x4b000000` = 'K', University Base `0x55000000` = 'U', both with +16..+18 = 0; the other 22
have small values there (e.g. People's Endeavor +16=1 +17=5 +18=2, Fallow Time +16=4). +17 == 1 on
all 8 faction-6 bases and +18 is nonzero on several faction-2/7 bases — an OBSERVATION, unnamed.
The old `[base+0x10] == 0` guard note was wrong twice over: Ghidra's `short *` offsets, and this
straddle.

**THE PAY SITE CONFLICT RESOLVES TO `0x4efedd` for this shape.** The live PAY stamp reads
`before=9 edi=9 after=0` with the derived price 9 (`m58_price.py --owner 3 --type 2` -> `DERIVED
price = factor_tenths 9 * type_cost 1 = 9`), immediately before the create. The `0x4f0ca1/0x4f0ca6`
site in NAMED.md's "completion path" is a different branch of the same function and is still unread.

**ACCEPTANCE — PASS on one real invocation, with the PATCHED script.** Reload recipe
(`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> HUD, `difficulty level:
talent`) -> `m54g_prep.py` -> `smac_play.py --turns 1 ... --tag m61t` (`Korolev Center founded in
2150`, `turn 0: 2150->2151 OK`) -> Korolev located BY NAME (idx 18, minerals 2, income 2) ->
`m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1` (`after INSERT 1 (try 1): pending=1
head=2 slots=[2, 2, 0, 0, 0, 0] minerals=2 d0=2`) -> `m59_head.py --stage read --hold` (`poke_hold:
6 units poked, all_held=True`) ->

`python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold` ->
**`PASS production prediction: 3 verified unit arrivals over 10 boundaries, every prediction and
every observed arrival accounted, queue bookkeeping exact — queue filled by the GAME's BUILD UI (0
memory writes), paid by income at 2/round`**, **56 checks, 0 bad**; `boundaries observed >= 2 — 10
of 10 rounds flipped`; `at least 1 POSITIVE prediction verified — 3/3`; `create guard ds:0x8f0d70
read 0 in every sampled row — 18619 sampled rows, values [0]`; `memory writes: 0`; `completion NOT
armed: minerals 4 < price 9`. Trace `evidence/trace_m56_build_20261026_162511.jsonl`. Read back in
memory after the run: ours **6 -> 9**, Korolev minerals 3, pending 0, head 2, guard 0. No deferral
was needed (no `ATTRIBUTED` line in the log). An earlier PASS the same session, with the
pre-patch script and the same UI shape, printed `PASS ... 1 verified unit arrivals over 10
boundaries` with **51 checks, 0 bad** (`evidence/trace_m56_build_20261026_160325.jsonl`): in that
trace the arrival is inside window r0 (ours 9 -> 10, Korolev tile 4 -> 5) — F1's deferral was not
exercised there either.

**Rule cases.** `python3 scripts/test_m56_predict.py` -> `PASS 17/17 production-prediction cases`;
`python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit 1; plus the two new
fixtures above.

**Open.** (1) The pop did NOT visibly left-shift Korolev's slot array while pending went 1 -> 0
(`slots [2, 2, 2, 2]` at r0 and at r1 of `trace_m56_build_20261026_160325.jsonl`) — the documented
"left-shift + pending--" is unverified for the slot array. (2) What writes base bytes +16/+17/+18
is unknown (no runtime watchpoint was armed on them); the dword-level answer is settled. (3) The
failure path `0x4eff5c` (guard-skip and the `0x5ab650` cap share it) is unread. (4) The chooser's
~25 score terms are still a shape, not an enumeration — enemy heads stay REPORTED. (5) The harness
could close its window deterministically after our upkeep (the walk leaving our slot, or
`ds:0x8f0d60` naming our last base) instead of polling on `cur_player == 3`; the deferral is now
attributed but the window race itself is still open. (6) A writer for `0x8f0d70` outside `.text` is
still not excluded. (7) The queued-count byte conflict (`0x94dc84` vs `0x94de84`) is untouched.

**Harness lessons.** A dialog left on screen swallows every UI click: `m57_ui_enqueue` failed twice
on University Base with `INSERT never landed` because an Operations Director "the minerals output of
Korolev Center is not sufficient to support Scout Patrol ... the unit has been disbanded" dialog
(`classify()` == `dialog`) was over the BUILD pane; Return cleared it, one Escape closed the pane.
And producing a unit zeroes the base's mineral credit (`+0xd0` 1 -> 0 or -1) while the income add is
gated `d0 > 0`, so both our bases sat at minerals 0 / credit 0 and no positive prediction was
possible — the reload was the fix, not a poke.

**Next pick (M62): what the POP actually does to the queue slots.** Pending went 1 -> 0 with the
slot array unchanged; arm `m60_guard --stage watch`-style breakpoints on the pop `FUN_004ef5d0`
(`0x4ef5f4` gates pending == 0, the shift/pending store, the `0x4ef613/0x4ef641 stores) and on the
slot dwords `base+0x50..0x74`, run over 2-3 boundaries with a queued base, and state from the
stores what the queue's representation really is — then re-check M59's "the head slot is the truth"
against it. Acceptance stays `m56_build.py --ui-queued <idx> --boundaries 10 --timeout 400
--no-poke-hold` printing PASS on one real invocation.

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
