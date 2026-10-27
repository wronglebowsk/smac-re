# Session notes archive — sessions 97-97

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
