# Session notes archive — sessions 99-99

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
