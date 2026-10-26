# Session notes archive — sessions 82-83

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 82b (2026-10-25) — M54e post-close audit: **THE RUN THAT PASSED ALSO LOST THE POSITION (bases_ours 0, our 8 records stacked at (47,47), flags stuck 0x100002), "OCCUPANCY" WAS THE WRONG CAUSE FOR M54d, AND THE TYPE BYTE IS +4 NOT +10 (that third claim was itself WRONG and is retracted in M54f — see item 1)** — `plugins` none; corrected `SESSION_NOTES.md` 82, `ORDERS.md §7`, `NEXT_PROMPT.md`, skill `references/terraforming-order-path.md`

Audit done after #44 merged, by re-reading the box and re-running the checker on every
milestone trace. Three claims that were wrong or unsupported, in order of how much they matter:

1. **RETRACTED in M54f (session 83): this finding was WRONG — the type IS `+10`.** I compared
   the two candidate offsets on the DEFEATED state (records in limbo after our faction lost
   everything) and let a doc line outvote working code: there `+4` scored 117/119 "plausible"
   only because `+4` is a flags byte that reads 0 on 79 of 119 records, and the Colony-Pod
   cross-check was worthless for the same reason. Measured properly on a healthy load, three
   independent reads agree on `+10`: (i) the panel, `SEL_G 0` -> "Scout Patrol (1-1-1)" at
   (28,42), and record 0 — the record on that tile — has `+10 = 2`; (ii) `data/alpha.json` type
   2 = Scout Patrol and class row 2 = cls 3 = Scout Patrol; (iii) the binary, which is what
   settles it: `shard_012.c:2150` `iVar8 = *(short *)((int)&DAT_00933282 + local_10) * 0x34;`
   then `(&DAT_0098adaf)[iVar8]` — the class table indexed by a SHORT at `UNIT_ARR + 0x0A + 52*i`
   (same shape at `shard_012.c:2117`, `:2148`, `shard_001.c:4153`, `:4312`, `:9466`).
   So every "class 9" line in M54c/M54d/M54e stands, and the `+10` type pokes really did change
   the type. What the detour did teach: **the unit panel is NOT a usable oracle on demand** — a
   `SEL_G` write does not redraw it (three different selections, byte-identical OCR text), so it
   is only trustworthy at load or after a real in-game selection. And `+10` values of 128/256/320
   on other factions' records are EMPTY STALE SLOTS, which is why `smac_state.counts()` now
   requires `type < 24` before counting a record as a unit.
2. **"The game will not path into a tile its own owner occupies" is not true.** The run's own
   trace refutes it: at turn 9, records 5 and 8 both walked ONTO (6,12) while records 0 and 2
   were already standing there (both turn-0 walkers read `still_at_start False`, and both
   turn-9 walks landed). The M54d failure most likely had another cause: its walker stood at
   (7,12), a half-tile offset that the even-x delta tables (`0x67850c` dx / `0x678990` dy) do
   not list as a neighbour, while every M54e walker stood on a real neighbour (4,12).
   `m54e_prep.py` changed two variables at once (emptied the base tile AND moved the walker
   from (7,12) to (4,12)) and the write-up blamed the occupancy one.
3. **The checker cannot see a defeat.** `m54a_check_run.py` asserts year deltas, STUCK and
   order/move counts; the trace's start/end snapshot carries `n_bases` for all factions but not
   how many bases WE own, so a run in which our faction loses every base still prints `PASS`.
   The M54e run did exactly that. The fix is small: put `bases_ours` (and `units_ours`) in the
   snapshot `smac_play` writes, and add a `--min-our-bases` floor (default 0 so old traces keep
   working) to the checker.

## Session 83 (2026-10-25) — M54f: **THE TYPE BYTE IS SETTLED (+10, FROM THE BINARY), THE BOX IS RESTORED FROM A CLEAN SAVE, AND THE RUN CHECKER CAN NO LONGER PASS A RUN THAT LOSES THE POSITION** — `plugins` none; changed `scripts/smac_state.py`, `scripts/smac_play.py`, `scripts/m54a_check_run.py`, `FOOTING.md`, `SAVE_FORMAT.md`, this file (82b item 1 retracted), skill `references/terraforming-order-path.md`

**Box first.** Session 82 left a defeated faction (`bases_ours 0`, 8 records stacked at (47,47),
`turn_flags 0x100002`). That state is not a base to build on, so step 5 of the footing applied:
`SMAC_SAVE='Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV' python3
scripts/m54a_load.py --relaunch` -> `HUD reached live=True` in 38 s, and
`python3 scripts/smac_state.py --json` -> `year 2150  turn_flags 0  n_bases 18  bases_ours 1
units_ours 6`, with `m54d_census.py` showing all six of ours on `University Base` at (28,42).

**The milestone: settle the type byte (the footing's blocking item) and give the checker eyes.**
1. **Type = the u16 at `+10`. Proven three independent ways, not correlated.** (i) Panel at load:
   `SEL_G 0` -> OCR reads "Scout Patrol (1-1-1)" and the location `(28,42)`; record 0 — the
   record on that tile — has `+10 = 2`. (ii) `data/alpha.json` type 2 = Scout Patrol, and class
   row 2 = cls 3 = Scout Patrol. (iii) **The binary decides it**: `shard_012.c:2150`
   `iVar8 = *(short *)((int)&DAT_00933282 + local_10) * 0x34;` then `(&DAT_0098adaf)[iVar8]` —
   `DAT_00933282` IS `UNIT_ARR + 0x0A`, the element is a SHORT, and it indexes the class table;
   same shape at `shard_012.c:2117`, `:2148`, `shard_001.c:4153`, `:4312`, `:9466`. So the code
   was right, `FOOTING.md` ("type byte@4") and `SAVE_FORMAT.md` ("`+10` is a flag word") were
   wrong, and **session 82b's finding 1 is retracted in place** — it compared the two offsets on
   the limbo records and let `+4` (a flags byte that reads 0 on 79/119 records) look plausible.
   All "class 9" lines in M54c/M54d/M54e stand.
2. **The unit panel is not an oracle on demand.** Poking `+10` 2 -> 0 and back changed nothing
   on screen, and three different `SEL_G` writes produced byte-identical OCR: the panel is a
   cached widget that only rebuilds on a real in-game selection. Worth knowing before anyone
   tries the "poke and read the panel" test again.
3. **The checker can now see a defeat.** `smac_state.snapshot()` gained `bases_ours` and
   `units_ours` (base array faction byte, unit records with `type < 24` and in-range x/y — the
   128/256/320 "types" on other factions' records are EMPTY STALE SLOTS), `smac_play` carries
   both in every per-turn `state_before`/`state_after`, and `m54a_check_run.py` gained
   `--min-our-bases` (default 0, fail-closed: a missing field is a failure).

**ACCEPTANCE NUMBERS (MET).**
`python3 scripts/smac_play.py --turns 4 --timeout 240 --no-escape 3000 --tag m54f` ->
`evidence/trace_m54f_20261025_015637.jsonl` -> `python3 scripts/m54a_check_run.py
evidence/trace_m54f_20261025_015637.jsonl --timeout 240 --min-our-bases 1` ->
`advanced 4/4`, `year deltas {1: 4}`, `stuck 0` (max dt 39.7 s), `orders 6 VERIFIED of 6`,
`ours bases_ours 1 units_ours 6 floor 1`, `PASS ... we still hold 1 bases`.
The floor is not vacuous: the same command on `trace_m54e40_20261025_010855.jsonl` now prints
`FAIL our faction holds None bases at the end, floor is 1`.

**Open.** (a) The footing's pick (a) — **found a second base** — was not attempted; the type-byte
settle and the checker floor came first by the footing's own order and took the session.
(b) `turn_flags` bit `0x2` is set after any driver run and does NOT clear on a TURN COMPLETE
click (year 2154 -> 2155 with the bit still set); a reload clears it (load reads `0`). Not a
wedge — turns still flip — but do not read bit `0x2` as "the run is stuck".
(c) 26 `unknown` panes in `trace_m54e40` are still unpinned; today's 4-turn run hit 4 `unknown`.

**Next (M54g):** found a second base — key the Former settle order (NAMED.md 120-146 +
the unit panel buttons), walk a Former to a tile it can enter, and prove `bases_ours 1 -> 2` in
one unattended run with `--min-our-bases 2`.
