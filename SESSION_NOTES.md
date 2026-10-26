

Older sessions: `docs/sessions/sessions-82-82.md` (1 sessions). Read it only when a question reaches back before session ## Session 82b.

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

## Session 84 (2026-10-25) — M54g: **THE FOUNDING IS KEYED (`b`, ORDERS MODE ON): THE LOOP FOUNDED "KOROLEV CENTER" AND THE CHECKER PASSED THE `bases_ours 2` FLOOR** — changed `scripts/smac_play.py` (name-pane class, `tile_recs` deref + live pitch, `founding_gate`, `issue_found_for_unit`, the in-loop hook), `scripts/m54a_check_run.py` (a founding is labelled, not byte-keyed), `scripts/test_classify.py` + `scripts/check_classes.py` (16 frames), new `scripts/m54g_probe.py`, `scripts/m54g_prep.py`, this file, `NEXT_PROMPT.md`, skill `references/terraforming-order-path.md`

**Box first.** State read clean and matched the footing (year 2155, pid 645846,
`bases_ours 1`, `units_ours 6`). Two things the footing got wrong, both measured:

1. **The tile array was being read at the wrong address by the driver.** `0x92ae14` holds a
   POINTER (M35 said so) and the row pitch is `DAT_00692184`, which is **32** here — the map
   is **64x64**, not 80x80; `smac_play.tile_recs` indexed the slot itself with a hard-coded
   40 and returned all-zero "tiles" under a base that is visibly there. Fixed: deref + read
   the pitch live.
2. **We own six Scout Patrols (type 2, class 3) and no Former**, so the footing's "Former
   settle" premise had no subject. There is **no `SETTLE` string anywhere in the exports** and
   no settle row in `#TERRAIN`; base founding is the **`b`** handler `FUN_004d1280`, gated on
   **class 8** (`NEEDCOLONISTS`, `shard_012.c:2852`). The prep therefore pokes `+10` 2 -> 0
   (Colony Pod/Conestoga = class 8) on one record, as `m54e_prep` already poked `+10` -> 1
   for its Former.

**How the key was found (one variable per step, memory-first).** OCR is ~15 s a poll on this
box and a clean HUD sometimes classifies `unknown`, so the first OCR-paced probe loop spammed
Return at the HUD (Return at a HUD is TURN COMPLETE — the year moved 2155->2156) and its
"control" was confounded. Staged probe (`scripts/m54g_probe.py`):
* selection alone (`SEL_G` poke, no key) leaves the HUD (`scratch` run: kind `hud`) — the pane
  in the early controls was opened by the KEY, not the selection;
* `b` with **orders mode OFF** (`0x91b5b8 == 0`) opened the **BASE screen** of the base near
  the cursor — `b` is a MAP-level key in that state (`evidence/m54g/probe_c_control.json`);
* `b` with orders mode ON on a class-3 unit: dispatcher reached, nothing founded
  (`probe_omode.json`); class-8 unit on a rocky tile (26,42): nothing (`probe_offbase.json` —
  `founding_gate` predicts NOTONROCKY from `b5 = 0x83`); class-8 unit on a tile the gate model
  calls LEGAL (26,43): **NEWBASE up** — OCR "enter a name for your new base … korolev center"
  (`evidence/m54g/probe_found1.json`), and **Return founded it: a faction-3 base record appeared
  at (26,43) 0.1 s later, `bases_ours 1 -> 2`, and the founding unit's record compacted away**
  (index 11 then read x4,y4,type320). The gate model (`founding_gate()`, a line-by-line mirror
  of `FUN_004d1280`: NOTINTRIAD / FUNGUSDANGUS / NOTONMONOLITH / NOTONROCKY / BASETOONEAR over
  the 8 delta-table neighbours) predicted every live refusal and the one live acceptance.
* **NEWBASE classifies `hud`** (caption y 102, generated name at y 135, TURN COMPLETE still
  drawn under it) — the classic key sink. New class `name-pane` (caption-band test), pinned
  with a saved frame BEFORE the driver used it.

**ACCEPTANCE NUMBERS (MET).** Reloaded clean save (`m54a_load.py --relaunch`, HUD live 27 s),
`smac_state.py --json` -> year 2150, `turn_flags 0`, `bases_ours 1`, `units_ours 6`;
`m54g_prep.py` -> rec0 `+10 = 0` (class 8), `x,y = (29,42)` (nearest tile `founding_gate`
calls LEGAL), `+17 = 0`, all read back (`evidence/m54g/prep.json`). Then ONE unattended run:
`python3 scripts/smac_play.py --turns 6 --timeout 240 --no-escape 3000 --tag m54g --verbose`
-> `evidence/trace_m54g_20261025_084554.jsonl`, whose turn 0 carries
`FOUND rec0 (29,42) type 0 gates legal -> bases 1->2 at (29, 42) panes ['name-pane'] (5.6s)`.
`python3 scripts/m54a_check_run.py evidence/trace_m54g_20261025_084554.jsonl --timeout 240
--min-our-bases 2` -> `advanced 6/6`, `year deltas {1: 6}`, `stuck 0` (max dt 43.6 s),
`orders 11 VERIFIED of 11` with `order mix {"b->founded": 1, "l->byte1": 10}`,
`ours bases_ours 2 units_ours 7 floor 2`, **`PASS ... we still hold 2 bases`**.
Read back independently after the run: `smac_state.py --json` -> `n_bases 19 bases_ours 2`;
the census lists **idx 18 (29,42) faction 3 "Korolev Center"** beside University Base (28,42).
Classifier gates: `test_classify.py` -> `PASS 16/16`, `check_classes.py` -> `frames: 16
failures: 0` (the `_3x.png` siblings deleted right after).

**Open.** (a) The footing's premise is retracted: the founding is not a "Former settle" and it
writes **no order byte** — its oracle is the base array, so the acceptance line "verified by
the `+17` delta" was replaced by "verified by a new faction-3 base record at the unit's tile".
(b) The unit was POKE-positioned onto the founding tile (a garrisoned unit cannot be ordered
off its own base on this build: `g` refuses it, Shift+arrow queued nothing on a type-0 unit at
(28,42)) — so the M54g walk-then-found sequence is still unproven, and the second base sits on
the tile that visually belongs to University Base's footprint (the game's own BASETOONEAR scan
accepts it because the delta tables are parity-shifted). (c) Founding cost 0 energy here
(`energy_delta 0`) — the cost model for founding is unpinned. (d) The type poke makes the
DISPATCHER treat the record as a Conestoga; whether the pump's movement would follow the poked
type is untested. (e) 4 `unknown` panes in this run's trace (turns 1, 3, 4) still unpinned.

**Next (M54h):** found a base the loop REACHED, not one it was poked onto — give the loop a
second own-base tile to walk to (the `g` chooser now has two destinations: University Base and
Korolev Center), land a queued MOVE between them with `--min-moves`, then found a third base
off the garrison with no position poke at all.

## Session 85 (2026-10-25) — M54h: **THE CHOOSER CAN NAME THE OTHER OWN BASE (probe, memory-verified); THE LOOP'S WALK DID NOT LAND — M54h STAYS OPEN** — changed `scripts/smac_play.py` (chooser geometry: `bar_bands`/`chooser_rows`/`chooser_buttons`; `answer_dest_chooser` clicks a ROW; `order_counts` count-delta walk proof; `PENDING_WALKS`/`verify_pending_walks`; `HUD_BLIND_S` fallback; `modal_caption` guard; the M54c "skip `g` on our base" rule retracted), new `scripts/m54h_probe.py`, `scratch/m54h_clear.py`, `ORDERS.md` §9, `test_classify.py` + `check_classes.py` (17 frames), this file, `NEXT_PROMPT.md`

**Box first.** State read clean and matched the footing (year 2156, pid 914329, `bases_ours 2`,
`units_ours 7`); the census put five Scout Patrols on University Base (28,42) with `order 1` and
two fresh ones (`order 0 mp 0`) on Korolev Center (29,42). Two things the footing got wrong:
the box was parked on a **BREAKTHROUGH panel** (class `unknown`) with an OPERATIONS DIRECTOR
dialog behind it (Escape closed both; `turn_flags` bit 0x2 cleared when they went away — it is
not only a "driver ran" latch), and a clean HUD over our own base classifies `unknown` because
2x OCR cannot read the TURN COMPLETE row.

**The chooser, measured (`scripts/m54h_probe.py`, `evidence/m54h/probe_chooser_walk1.json`).**
`g` on a unit GARRISONED on its own base opens the chooser and it lists **both** own bases —
rows are full-width bars at y 132 and y 151 (19 px pitch), the five-button row (Sort: Name /
Sort: Size / Sort: Dist / OK / CANCEL at 209/305/401/497/593) sits at y 181 with two rows and
y 162 with one, so M54d's hard-coded OK row was a coin flip on a two-row pane. Clicking a row
changes NOTHING in memory (`+17` and legs unchanged 0.9 s after the click); OK landed `+17`
0 -> **0x18 87 ms after the click** with legs `[28,42]` (University Base) and the pump stepped
the unit **(29,42) -> (28,43) with `+40` = 3 spent**; CANCEL (5th button) closed the pane with
60 samples of `+17`, all 0. **M54c's "the game refuses `g` on our own base" is retracted** (its
evidence was a one-base position). The `Distance:` column is 0 for both rows — the cursor's,
not the unit's (M54d), so it cannot drive the pick.

**ACCEPTANCE: NOT MET.** `python3 scripts/m54a_check_run.py
evidence/trace_m54h4_20261025_095308.jsonl --timeout 240 --min-our-bases 2 --min-moves 1` ->
`advanced 6/6`, year deltas `{1: 6}`, `stuck 0` (max dt 28.9 s), `orders 1 VERIFIED of 1`
(`{"g->byte24": 1}`, energy 3), `ours bases_ours 2` floor 2, **`FAIL only 0 VERIFIED walks,
milestone wants 1`** — `moves 0 LANDED of 3 ordered walks`. Nothing was weakened; the run that
would have to PASS does not.

**Why it did not land (measured, cause not settled).** In the loop, three `g` orders whose row
click the trace records against the University Base row (turn 1 of `trace_m54h...093424`, turn 3
of `trace_m54h4`) put legs naming **(14,56) = House of Martyrs (a BELIEVER base)**,
**(17,55)** and **(12,14) = Gaia's Landing** into the record — never (28,42) — while the
identical click in the probe put (28,42) in the same field. The leading explanation is index
identity: `units_ours` went 9 -> 10 during the run (University Base builds Scout Patrols) and
the record array reshuffled between turns twice (the unit ordered at (29,42) was index 67 at
order time and index 52 a turn later), so the legs read 0.35 s after the OK may belong to a
different record than the one that was ordered. After the run, records DO carry legs (28,42)
and (29,42) and one unit sits at (29,43) one step from Korolev Center — walking happens;
nobody arrived at a destination the trace can attribute to the loop.

**Two driver bugs found and fixed (verified).** (a) A clean HUD whose TURN COMPLETE row fails
to OCR classifies `unknown` (MENU at (61,369) + COMMLINK read, `region_colors 167`): with
`--no-escape` the loop idled a WHOLE turn budget (trace_m54h...093424 turn 2 burned 521 s with
the year unmoved in our phase) — fallback added (our phase + chrome + no bar band at y 145-200
+ 25 s -> click the button at its measured coordinates), proven: `evidence/trace_m54h2_...
094339.jsonl` turn 0 `2160 -> 2161 OK (36.7s)` after `turn-complete-blind`. (b) An OPERATIONS
DIRECTOR "Investigate pod beacon?" pane wearing HUD chrome classified `hud` and ate turn 0 of
trace_m54h3 (the driver clicked TURN COMPLETE behind it every 6 s) — `modal_caption` guard
added; the next run cleared it in one press (`hud-with-caption: 1` in the m54h4 action log) and
all 6 turns advanced. Classifier gates: `test_classify.py` -> `PASS 17/17` (was 16/16; the new
frame is the two-row chooser, `evidence/m54h/chooser_g60b.png`), `check_classes.py` ->
`frames: 17 failures: 0`, `_3x.png` siblings deleted.

**Open.** (1) What the leg array actually holds, and whether the loop can be made to read the
destination of THE record it ordered (read all our records before/after and diff, rather than
trusting one index). (2) Whether the chooser's row order is Sort: Name or nearest-first — both
frames seen so far are consistent with either; the driver's pick is text-matched first.
(3) `l` (SENTRY) on a unit carrying a pending 0x18 landed nothing (cause confounded with an
`unknown` HUD frame; decoys were parked by poking `+17 = 1` instead, read back). (4) The
position is now 10 units / 2 bases at 2167 with `turn_flags 2` and two live 0x18 orders in it.

**Next (M54i):** make the walk's destination attributable to the order — snapshot every one of
our records before the keypress and diff after (never trust one index), land ONE loop-ordered
walk on the base its own legs name with `--min-moves 1`, and only then re-attack the
walk-then-found sequence.

## Session 86 (2026-10-25) — M54i (open): **ATTRIBUTION WORKS IN THE LOOP (memory-verified); A WALK STILL HAS NOT LANDED — three failure modes measured, two fixed; M54i STAYS OPEN** — changed `scripts/smac_play.py` (`diff_order_records` + `legs_of` + `own_base_tiles` in the walk checks; bracket-read diff for the default-button path; start-vacated rival rule; `counts0` baseline moved to the pre-press snapshot; `seen_recs` crash fix; OK clicked at the FOURTH measured button centre, not the merged band midpoint), `scripts/m54a_check_run.py` (`--min-own-base-arrivals`), new `scripts/test_walk_diff.py` (13 cases), `scratch/m54i_unpark.py`, `scratch/m54i_park.py`, `scratch/m54i_hold.py`, `ORDERS.md` §10, this file, `NEXT_PROMPT.md`

**What the milestone asked and got.** Every order now names WHICH record the keypress changed:
the watcher's samples carry the whole 52-byte record, and `diff_order_records` claims a
destination only when the watched slot went 0 -> byte with legs that CHANGED and no rival
wears the signature; otherwise `dest` stays None and the trace says so. Live proof:
`evidence/trace_m54i_run4_*.jsonl` turns 0-2 — `g` verified, `walk_diff {attributed: True,
confounded: False}`, dest read from the changed legs of the record the press changed.
`scripts/test_walk_diff.py` -> `PASS 13/13 attribution cases` (bracket shape, own-moved-record
is not its own rival, look-alike-wearing-the-slot IS one — session 85's exact failure).

**ACCEPTANCE: NOT MET.** `python3 scripts/m54a_check_run.py
evidence/trace_m54i_run5_20261025_112259.jsonl --timeout 240 --min-our-bases 2 --min-moves 1
--min-own-base-arrivals 1` -> `advanced 6/6`, year deltas `{1: 6}`, `stuck 0` (max dt 33.2 s),
`orders 2 VERIFIED of 3` (`{"g->byte24": 1, "l->byte1": 1}`), `ours bases_ours 2` floor 2,
**`moves 0 LANDED of 0 ordered walks`**, `FAIL only 0 VERIFIED walks` / `only 0 walks LANDED
ON OUR OWN BASE`. Nothing weakened; a documented negative merges.

**Three failure modes, all measured.** (1) **`+17 = 1` is SENTRY, not parked** — the byte table
always said so; sessions 84-85's "parked decoys" patrol on their own every round (run3's five
"parked" records migrated (28,42) -> (28,43) and their leg arrays rewrote turn after turn),
which is what made every count-delta proof fire blind. The inert byte is 2 (HOLD,
`scratch/m54i_hold.py`). (2) **the count baseline was read AFTER the in-phase pump** — the OK
hands the unit to the pump in the same tick (ORDERS §7), so the post-OK baseline saw the origin
already vacated (`order_counts {dest 4, src 0}`, run4 turn 0) and "origin count falls" could
never fire; fixed to the pre-press snapshot. (3) **the clean-shape runs still miss the ORDER
itself**: run5 turn 0 `g` on a unit garrisoned at Korolev Center opened the **BASE SCREEN**
(panes `[unknown, unknown, base, base]`, byte never moved) — after a fresh load the map cursor
is nowhere the driver thinks it is; turn 3's chooser OK landed `+17 = 24` with **legs still
empty** (`claim None, rivals 0` — honestly unattributed) — a MOVE queued with no route, cause
unresolved. The loop's fallback then turned the lone candidate into a SENTRY (`l` verified,
attributed — the bracket diff working exactly as designed).

**The war is a variable.** From 2167 to 2187 (runs 3-4) other factions founded 7 bases, TOOK
University Base (`bases_ours 2 -> 1`) and killed 5 of our 10 units while the checker floor was
still reading 2 at run start. Recovered by reloading `m54b_clean.SAV` (2150) and letting the
loop re-found Korolev Center (`m54g_prep` + 2 turns, `evidence/trace_m54i_found_*.jsonl`,
`bases_ours 2` at 2152, `n_bases 19` — the quiet window).

**Also.** run2 died mid-turn-1: the WIP unpacked 3-tuples from the 2-tuple `seen_bytes`
(fixed to `seen_recs`); run1 had `orders 0` on 6/6 turns because every record we owned was a
sentry or mid-walk. The chooser's OK is now clicked at the fourth measured button centre
(`chooser_buttons`), not the merged bar-band midpoint (which is the `Sort: Dist` button on a
two-row pane). Classifier gates untouched (no new classes): `test_classify.py` 17/17,
`check_classes.py` 17/0 as in session 85.

**Open.** (1) A loop-ordered walk landing on our own base — STILL zero across sessions 84-86;
the remaining blockers are cursor placement after load (g -> base screen) and the legs-empty
chooser OK. (2) Whether the chooser's row click lands the selection before OK (memory shows
nothing either way — session 85; the legs-empty OK suggests it sometimes doesn't). (3) The box
after run5: 2158, 2 bases, 7 units, one live legs-less 0x18, sentries loose.

**Next (M54i'):** from the quiet 2158 position — census, hold everything, unpark ONE unit onto
a tile where it sits ALONE; fix cursor placement first (read the map cursor's memory cell or
verify the chooser opens before spending the key); if a chooser OK lands 0x18 with empty legs,
re-open and answer again; then the acceptance command above on a 6-turn run.

## Session 87 (2026-10-25) — M54i2: **A LOOP-ORDERED WALK LANDED ON OUR OWN BASE AND THE ACCEPTANCE PASSED — the cause of every earlier non-landing is the step table: all 21 steps preserve (x+y) parity, and every walker so far stood on the WRONG PARITY for its destination** — changed `scripts/smac_play.py` (`move_order_needs_retry` + `MOVE_ORDER_RETRIES`; `resolve_move_dest`; `delta_table`/`table_neighbors`/`walk_parity_ok` + the parity gate in `answer_dest_chooser`'s target pick and in `can_walk`; neighbor-first candidate sort; `mp_after` = max mp over dest-tile hits in `verify_moves` and `verify_pending_walks`), `scripts/test_walk_diff.py` (18 -> 24 cases), `ORDERS.md` §11-§12, new `scratch/m54i2_pump.py`/`m54i2_setup.py`/`m54i2_setup4.py` (+ the §11 probe scripts), this file, `NEXT_PROMPT.md`, skill `references/terraforming-order-path.md`

**First half (its own overflow; the commits are 391cd9a..d39b481).** THE CURSOR IS GAME-OWNED: three cursor variables, no poke sticks on any (`*(u32*)0x7cdecc + 0x1dd9c/+0x1dda0` — the info-panel window fields, re-synced within ~3 s; `DAT_0091b5f0/670` at `+0x91b5e8` — re-synced in 1.5 s; `DAT_0091b5e8/+0x91b5ec` climb on their own — the cells are a history, not a slot). Session 86 run5 t0's "cursor placement" failure RE-ATTRIBUTED: `g` is an ORDER only via the dispatcher pokes (SEL_G + `0x91b5b8`); otherwise it falls to the cursor-tile handler (`FUN_00511960`): base tile -> BASE SCREEN, else nothing. `sp.focus()` is a SILENT NO-OP while `sp.WIN` is None — scratch scripts must `sp.WIN = sp.find_window()` first (ate an hour: "keys don't land"). A poke-MOVED unit stops being found at its new tile by the game's occupancy. `resolve_move_dest`: the leg array is a WAYPOINT, the chooser's named base is the ordered destination (run1 t3: OK named (28,42), legs held (11,17)).

**The pump experiment (`scratch/m54i2_pump.py`, 2158, one actionable record, everything else HELD, read on second handles):** a CHOOSER-QUEUED 0x18 executes on the game's own TURN COMPLETE cycle — the record at (28,43) with leg (28,42) came back at (29,42), order still 24, `+40` = 3 spent, while every HELD record sat put at `+40` = 0. §7's "three TURN COMPLETEs moved nothing" holds for HAND-POKED bytes only. `+40` = mp SPENT this round, re-zeroed at the next phase start for units that did not move.

**THE STEP TABLE.** `dx` 0x67850c / `dy` 0x678990, 21 int32 pairs (`while ((int)local_2c < 0x54)`, ghidra_out/shard_013.c:21868; live read at 2159): every pair preserves (x+y) parity. University Base (28,42) sums 70, even — every walker sessions 84-87 stood at (29,42) or (28,43) (71, odd): UNREACHABLE, forever. The oscillations were geometry. Real neighbours of (28,42): (29,41),(27,41),(27,43),(29,43),(26,42),(30,42),(28,40),(28,44)... Driver: `g` only when a same-parity own base other than the unit's tile exists; neighbor-first candidates. Tests first: `python3 scripts/test_walk_diff.py` -> `PASS 24/24 attribution cases` (cases 21-24 are the table, the oscillation tiles, the gate, and the measured (28,43)->(29,42) step).

**run3 (`evidence/trace_m54i2_run3_20261025_131730.jsonl`, 2159->2164).** Loop ordered the record at (29,41) to University Base: `g` verified, `walk_diff {attributed: True, confounded: False}`, legs [(28,42)], chooser row "University Base Distance: 1". THE WALK LANDED IN MEMORY — census 2165: that record at (28,42), order 0 (consumed), moved bit set — but the checker scored `landed false`: `mp_after` read `hits[0]["mp"]`, a held garrison (mp 0), while the arrival's spent mp sat in a LATER hit; dest_count [3,5] (arrival + a unit PRODUCED on the base tile that turn), src [1,0]. Fixed `mp_after` to the max over dest-tile same-type hits (the floor is unchanged — garrisons and produced units sit at mp 0 there, measured; the count delta still must fire).

**ACCEPTANCE MET.** `python3 scripts/m54a_check_run.py evidence/trace_m54i2_run4_20261025_132218.jsonl --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1` -> `PASS 6 turns advanced, year +1 each, no STUCK over 480s, per-turn state deltas present, 1 verified walks, 1 onto our own base, we still hold 2 bases` — `advanced 6/6`, year deltas `{1: 6}`, `stuck 0` (max dt 26.2 s), order mix `{"g->byte24": 1, "l->byte1": 1}`, `moves 1 LANDED of 1 ordered walks`, `t[28,43]->[29,42] mp+3`, `1 landed on a tile holding ONE OF OUR BASES and not the unit's start tile (floor 1)`, `bases_ours 2` at end (2171). Setup (`scratch/m54i2_setup4.py`): cancelled the impossible University order on the record at (28,43), HELD everything else — exactly one actionable, a table-neighbour of Korolev Center (29,42), same parity (71, odd). Memory verification: watched slot 0->24 with legs [(28,42)] -> [(29,42)] (chooser named Korolev Center), rivals []; census 2171: the moved-bit record sits at (29,42). Classifier gates untouched (no new classes): `test_classify.py` 17/17, `check_classes.py` 17/0.

**Open.** (1) A MULTI-LEG route has never landed — both landings so far are one step; the pump's continuation across TURN COMPLETEs is only proven for one step at a time. (2) The route from (20,42) to University Base is unproven terrain. (3) `mp_after` max-over-hits cannot NAME which hit is the walker — a wandering same-type sentry with spent mp on the dest tile would satisfy it (the count delta must still fire). (4) The box at 2171: 10 units, 2 bases, n_bases 21, run3's sentries loose; the quiet window closed once around 2167-2187 for runs 3-4 (University was taken then). (5) SENTRY (`l`) on a unit with a pending 0x18 still unproven (session 86 item).

**Next (M54j):** the MULTI-LEG walk — from the 2171 position: census, `scratch/m54i2_setup4.py`-style prep that leaves the record at (20,42) actionable (parity 62, even — same as University Base) and HELD everywhere else; the loop orders it to University Base; the pump must walk it (22,42)->(24,42)->(26,42)->(28,42) across TURN COMPLETEs until it ARRIVES. Acceptance: the same checker command on ONE 6-turn run (`--min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1`), and in the trace the landed move's ORDER turn is earlier than the turn its `carried` pending walk reports `landed` — a multi-turn arrival on our own base. If terrain blocks the route, report the negative with per-turn position read-backs; reload `m54b_clean.SAV` + re-found if the war took a base first.

## Session 88 (2026-10-25) — M54j: **A MULTI-LEG WALK LANDED ON OUR OWN BASE ACROSS TURN COMPLETEs AND THE ACCEPTANCE PASSED — and the three things that hid it: the game AUTO-SENTRIES order-0 units across the round boundary, an all-HELD human phase AUTO-ADVANCES unseen, and six garrisons on the destination tile made a 2-tile step print ARRIVED** — changed `scripts/smac_play.py` (`pick_reactivation`/`held_walk_records`/`walker_on_dest`; the `PRE_ARM` mid-AI-round hook; the blind-HUD order step; `landed` = walker-on-dest by ROUTE + origin-vacated + mp spent in `verify_pending_walks`, + identity + mandatory count baseline in `verify_moves`), `scripts/m54a_check_run.py` (an own-base arrival must be MULTI-TURN: `ordered_turn < landing turn`), `scripts/test_walk_diff.py` (24 -> 31 cases), `ORDERS.md` §13, this file, `NEXT_PROMPT.md`, skill `references/terraforming-order-path.md`

**ACCEPTANCE MET.** `python3 scripts/m54a_check_run.py evidence/trace_m54j_run6_20261025_161917.jsonl --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1` -> `PASS 6 turns advanced, year +1 each, no STUCK over 480s, per-turn state deltas present, 1 verified walks, 1 onto our own base, we still hold 2 bases` — `advanced 6/6`, year deltas `{1: 6}`, `stuck 0` (max dt 16.2 s), order mix `{"g->byte24": 1, "l->byte1": 2}`, `moves 1 LANDED of 3 ordered walks`, `t[20,42]->[28,42] mp+3` **ordered turn 0, carried turn 1 (`not yet`), LANDED turn 2** (`evidence/trace_m54j_run6_20261025_161917.jsonl:4` — `carried True, ordered_turn 0, dest_is_own_base True`), `bases_ours 2` at end (2164). Memory chain: setup poked rec1 (28,42)->(20,42) actionable + HELD the rest (read back: the ONLY actionable); the press moved it (20,42)->(22,42) with legs [(28,42)] (attributed True, rivals []); census 2164: the unit sits at (28,42) University Base wearing byte 1. Nothing weakened; the checker was STRENGTHENED this session (multi-turn filter + walker identity + retired count fallback).

**The three blockers, all measured.** (1) **AUTO-SENTRY:** an order-0 unit that waits across the round boundary comes back byte 1 (SENTRY) and patrols away — run1's sole actionable at (20,42) was gone by our phase (`scratch/m54j_setup.py` read-back vs run1 turn 1: `g`/`l`/`h` all pressed on a byte already 1); byte 2 (HOLD) survives, and an order-0 poked DURING the AI round is still 0 and unmoved at phase open (`scratch/m54j_probe2.py`: poked mid-round, byte 0 across two flips). Driver: `PRE_ARM` hook pokes the best held walker to 0 in the AI round; `pick_reactivation` re-activates in-phase when nothing is actionable. (2) **AUTO-ADVANCE:** with nothing actionable the game draws "Year NNNN: No units need new orders. Press ENTER" and ends our phase in seconds — TURN COMPLETE stops OCR-ing, frames classify `unknown`, and run2/run3 burned 4-6 of 6 turns with the order step NEVER running (it lived only in the `hud` branch). The order step now fires on the FIRST memory-verified our-phase frame (`blind-orders` action). (3) **FALSE ARRIVAL:** run4 `evidence/trace_m54j_run4_20261025_160625.jsonl` — the order moved (49,33)->(47,33), 2 of 21 tiles, and `verify_moves` printed ARRIVED: University Base holds six identical Scout Patrols, `bool(hits)` was true before the walk and the count fallback passed on the delta. `walker_on_dest` identifies the WALKER by the ROUTE it wears (the ordered leg array survives the pump — run4 watched the same record carry [(28,42)] through (47,33) and (43,35)); carried-walk arrival = identity + origin-vacated + mp spent (the pre-press count baseline is stale by design for multi-turn walks; same-turn landings keep the count delta).

**The pump's appetite is a variable, not a constant.** run5 (4 tiles, clear corridor): the WHOLE walk ran inside the order turn's cycle — landed same-turn, and the new multi-turn filter honestly refused it (`FAIL only 0 walks LANDED ON OUR OWN BASE` — the milestone wants a multi-TURN arrival). run6 (8 tiles west along y=42): (20,42)->(22,42) on the press round, ARRIVED on the destination at turn 2. run4 (16,18 tiles diagonal): ~2 tiles/round over 4+ rounds. Which round the game finishes a route in is terrain-dependent; the walk itself is hands-off after the order — the unit stays byte 24, is NOT actionable mid-walk, and needs no new orders.

**Also.** The two bases are OPPOSITE parity (70/71), so every tile matches exactly one base — "wrong parity for every own base" only happens when a base is gone; `pick_reactivation` drops own-base garrisons (cases 25-28; three fixtures failed first on MY parity arithmetic — verify sums mechanically). The war ate University Base between 2177-2198 while run2/run3 sat passive (units_ours 11->5, n_bases 27); recovered by reloading `m54b_clean.SAV` (2150 — the blind `--relaunch` path-typing MANGLES on wine 10.20-staging: `\h`->`Eh`, "unable to find file"; the LOAD browser opens IN the saves dir — dismiss the error, type just the FILENAME, OK, then (290,391)) + `m54g_prep` + a 2-turn founding (Korolev Center re-verified in the base array at 2152). Tests: `python3 scripts/test_walk_diff.py` -> `PASS 31/31 attribution cases`; classifier gates untouched: `test_classify.py` 17/17, `check_classes.py` 17/0.

**Open.** (1) `PRE_ARM` (mid-round arming) is measured at the probe level but was not exercised in a PASS run (run5/run6 used the actionable-from-setup path; the hook found nothing to arm). (2) The auto-sentry trigger is behavioral, not found in the binary — idle order-0 units convert, exact window unknown. (3) run4's walker (the (49,33) veteran) died in the war before arrival; a LONG terrain-varied route arriving via `carried` is proven only at 8 tiles. (4) The box at 2164: 2 bases, 8 units, quiet window open (~10-15 yr), two sentries loose, one `l` order landed on the arrived walker. (5) `mp_after` max-over-hits still cannot NAME which hit spent the mp (the identity rule now covers the tile; a wandering same-type sentry with spent mp ON the dest tile could still satisfy mp_after).

**Next (M54k):** from the 2164 quiet window — the footing's S2 thread (win conditions / transit) OR close the PRE_ARM loop: a PASS run where the ONLY armed unit comes from `pick_reactivation`/`PRE_ARM` (everything HELD at run start, the hook arms mid-round — the exact shape run2/run3 had, now with the fix). Acceptance: the same checker command on ONE 6-turn run with `--min-own-base-arrivals 1` AND a `pre-arm:recN` line in the trace's actions. If the quiet window closes first (base lost), reload `m54b_clean.SAV` + re-found (the filename-typed browser recipe above).

## Session 89 (2026-10-25) — M54k: **THE HOOK PATH IS PROVEN END TO END AND NO RUN PRINTED PASS — the documented negative merges: the hook armed, the `g` order landed attributed, the walker walked six positions read from memory, and every acceptance floor held except `min-moves`/`min-own-base-arrivals`** — changed `scripts/smac_play.py` (the blind our-phase gates read memory + the modal band, not the OCR chrome read; the candidate sort prefers a unit that CAN walk; `walker_on_dest` accepts the ordered-dest leg as a route signature), `scripts/test_walk_diff.py` (31 -> 33 cases), new `scratch/m54k_setup.py` (all-held prep; the read-back keys the walker by TILE, not record index) and `scratch/m54k_watch.py` (0.5 s memory watcher printing only changed (x,y,order,mp) multisets), this file, `NEXT_PROMPT.md`, skill `references/terraforming-order-path.md`

**ACCEPTANCE: NOT MET (documented negative merges, as session 86).** `python3 scripts/m54a_check_run.py evidence/trace_m54k_run6_20261025_17130*.jsonl --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1` -> `advanced 6/6`, year deltas `{1: 6}`, `stuck 0` (max dt 22.2 s), `actions {"pre-arm": 1, "orders": 2, ...}`, order mix `{"g->byte24": 1, "l->byte1": 1}`, `bases_ours 2` at end (2159), **`moves 0 LANDED of 5 ordered walks`** -> `FAIL only 0 VERIFIED walks, milestone wants 1; only 0 walks LANDED ON OUR OWN BASE (not the start tile), milestone wants 1`. Nothing weakened: the walker needed ONE more turn than the 6-turn budget — `scratch/m54k_watch.py` read (36,33)->(36,35)->(35,36)->(34,37)->(33,38)->(32,39)->(30,39) across 2153-2159, byte 24 the whole way, legs [(29,42)] — one legal step (−1,+3) from Korolev Center when the run ended. The setup read back on a second handle `actionable: []` + `eligible held: [(66, 36, 33, 9, False)]`, so the HOOK armed it (`PRE-ARM rec66 (36,33) +17 2->0 in the AI round`), not the setup.

**THE HOOK ARMED AND A WALK LANDED ON OUR OWN BASE — just not inside a scored run.** run5 (`evidence/trace_m54k_run5_20261025_170317.jsonl`, 2186-2193): `pre-arm:rec13`, `g` verified 0->24 naming Korolev Center, and the watcher read the ARRIVAL — (20,41)->(22,41)->(23,42)->(25,42)->(27,42)->**(29,42)** at 2192, ordered turn 1, arrived five turns later. The checker could not score it: the leg SAMPLED in the press burst had drifted to (61,10) while the record that arrived wore [(29,42)] — the pump REWRITES the leg array as it walks — and University Base was captured at 2193 (`bases_ours 1`). Fixed: `walker_on_dest` accepts either signature (tests 32-33 pin it; a third leg, or no leg, is still not the walker).

**Four measured blockers, all read back.** (1) **The map's per-tile impassable flag**: in the 2-column tile record the flag byte is at record +3 for EVEN x and +7 for ODD x, and bit 0x40 set = impassable (validated against 98 live unit tiles; one exception, a faction-6 unit at (45,39)). Runs 3-4 poked the walker onto (28,34) (flag 0x41) and it VANISHED within seconds (`watch4` first change line `-[(28, 34, 2, 0)] +[]`); the y=42 corridor is passable from x=20 east (x 18-19 are water — why (20,42) worked). (2) **`g` queues the alphabetically-first own base regardless of parity**: run7's unit at (22,42) (parity 64, even = University) got leg (29,42) — Korolev Center, parity 71 ODD — an impossible route by §12, and it oscillated all 6 turns; the chooser never classified `dest-chooser` (attempt `panes ['unknown']`, `chooser_pick None`) so the driver's parity-gated row pick never ran and accepted the leg the game wrote. An ODD-parity start matches the base the game auto-targets (run5/run6: legal routes, real walking). (3) **A COMMUNICATION landing inside the order step is a key sink**: run8 turn 1 pressed `g` with comm panes up (`panes ['unknown','unknown','dialog','comm','comm']`) — the order byte went 0 -> **88** -> 2 (HOLD), the order was unverified, and that turn record spanned TWO year flips (`{1: 4, 2: 2}`). (4) **A produced garrison steals the turn's single order on the record-index tiebreak**: run3 pressed `l` five turns and `g` zero while the hook-armed walker waited (and got auto-sentried); fixed — the sort now puts a candidate that CAN reach an own base first (`_can_walk`), which is what made run6/run7 order the walker on turn 1.

**Also measured.** The session-88 blind gates still starved a turn: the map HUD with the production line in the message box ("Korolev Center builds ScoutPatrol.") OCRs as GARBAGE — no MENU, no COMMLINK (`evidence/px_m54k_banner_probe.png`, 2173) — so `hud_chrome` was false while memory said OUR phase (`cur_player 3, turn_flags 0`) and 240 s passed with NO key sent; the our-phase blind gates now read memory + "nothing drawn in the modal band". With everything HELD the game advances rounds with no input at all (~8 s/round; 2164 -> 2166 by itself between two of my probes) — that is what makes a turn record occasionally span two years. Reload recipe re-verified: `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (bare filename, nothing to mangle) -> HUD live at 2150, 1 base; `m54g_prep.py` + one loop turn -> `FOUND rec0 (29,42) ... bases 1->2`, `bases_ours 2` at 2151. Tests: `python3 scripts/test_walk_diff.py` -> `PASS 33/33 attribution cases`; classifier gates untouched: `test_classify.py` 17/17, `check_classes.py` 17/0 (`_3x.png` deleted).

**Open.** (1) A PASS run of the hook shape — never produced. (2) `order_step_in_loop` presses keys without re-checking the screen between them: a comm/pane arriving mid-step turns the order into garbage bytes (run8's `88`). (3) Year cadence: with everything HELD the game runs ~8 s rounds and a turn record can span two flips (run5 t1, run8 t1/t4). (4) `walker_on_dest`'s ordered-dest signature could be worn by a wandering same-type unit that also spent mp. (5) The box after run9: ~2174, `bases_ours 2`, one HELD unit at (30,39) wearing legs [(29,42)], the run8 walker gone from (22,41) after the byte-88 mess.

**Next (M54k'):** one more hook-shape run with the four blockers removed — an ODD-parity start tile (the game auto-targets Korolev Center), 2-3 BFS steps from it (so it ARRIVES inside the 6 turns), enemies 12+ tiles out (census + the flag byte first), reroll if a comm lands in the order window or a turn record shows a +2 delta. Acceptance unchanged: `python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1` on ONE unattended 6-turn run, `pre-arm:recN` in the trace's actions, setup read-back printing `actionable: []`.

## Session 90 (2026-10-25) — M54k2: **THE HOOK-SHAPE RUN PRINTED PASS — and the two fixes it took: `queued_rescan` (the pump ran the WHOLE route inside our phase while the slot oracle read a stale record) and a year-poll after the order step (the auto-advance race recorded a +2 turn)** — changed `scripts/smac_play.py` (`queued_rescan` + wired into `_issue_order_once`'s pane loop after the blind Return; both order-step exits poll `year() != y0` at 0.2 s / 20 s cap before continuing), `scripts/test_walk_diff.py` (33 -> 37 cases), `ORDERS.md` §14, this file, `NEXT_PROMPT.md`, skill `references/terraforming-order-path.md`; new scratch (untracked): `m54k2_scan.py` (BFS-from-base tile scan: flag byte, parity, occupancy, enemy distance)

**ACCEPTANCE MET.** `python3 scripts/m54a_check_run.py evidence/trace_m54k2_run3_20261025_185036.jsonl --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1` -> `PASS 6 turns advanced, year +1 each, no STUCK over 480s, per-turn state deltas present, 1 verified walks, 1 onto our own base, we still hold 2 bases` — `advanced 6/6`, year deltas `{1: 6}`, `stuck 0` (max dt 52.8 s), `actions {"pre-arm": 1, "orders": 2, ...}`, order mix `{"g->byte24": 1, "l->byte1": 1}`, `moves 1 LANDED of 5 ordered walks`, `t[35,36]->[29,42] mp+6` **ordered turn 1, LANDED turn 5**, `dest_is_own_base True`, counts [4,5]/[1,0], `bases_ours 2` at end (2204). Setup read back `actionable: []` + exactly one eligible held walker (`scratch/m54k_setup.py 29 42 35 36`); the HOOK armed it (`pre-arm:rec12`). Watcher (`scratch/m54k_watch.py 330 35 36`): (35,36) armed 2->0 at 2198 -> (34,37,24,6) -> mp re-zeroed 2200 -> (33,38) -> (32,39) -> (30,39) -> (30,41), byte 24 the whole way -> **(29,42) byte 0 at 2204** — Korolev Center. Nothing weakened; same floors as session 89.

**run1 was the documented negative INSIDE the milestone (fixed, not merged as-is).** The pane the `g` raised classified `unknown` x5, the blind Return answered the chooser, and the pump executed the whole 4-step route (34,37)->(32,39)->(30,39)->(30,41)->(29,42), byte 24 the whole way, `cur_player 3 tf2` — INSIDE turn 1's record: year deltas {1:5, 5:1}. Each flip compacted the array, so the modal loop's byte oracle (`UNIT_ARR + idx*52+17`) read a DIFFERENT record (byte 2) and the order recorded unverified -> `moves []` -> the checker could not score the arrival. `queued_rescan` now reads the queue off CONTENT: exactly one of ours newly wearing a wanted byte, none wearing it pre-press, its last leg naming OUR base (queue-time legs are the destination; a mid-walk rewrite names waypoint garbage — (61,9) in run1, (61,10) in session 89 — and a waypoint is not evidence). Tests 34-37 pin unique/fresh/base-leg; two fresh wearers, a prior wearer, a waypoint leg and a legs-less queue all say NOTHING. run3's `g` verified through exactly this path (pane `dialog`, `n_samples 0`, attributed True, confounded False, claim frm (35,36) to (34,37)).

**run2 proved the shape end-to-end and failed ONLY the cadence:** `g` verified 0->24 (chooser classified), carried turns 1-3, `landed True` turn 4 on our own base with the count delta firing — but turn 5 (post-arrival, everything HELD/SENTRY) recorded 2196->2198: the game AUTO-ADVANCES ~8 s/round once nothing is actionable, and the turn loop's next iteration costs a freeze+OCR (2-15 s), so TWO rounds flipped between its year checks. Checker: `FAIL year did not move +1 on turns [5]`. Fix: both order-step exits poll `year() != y0` at 0.2 s (20 s cap) before continuing — the flip is cheap to watch from memory. run3: {1: 6}.

**Also measured.** `turn_flags` gained a persistent 0x100000 bit around 2196 (1048578 at run3's end at 2204; the driver's `tf & 2` gates are unaffected — ORDERS §14). The tile scan (`scratch/m54k2_scan.py`) re-screens the target EVERY setup: the war closed the quiet window hard — best enemy distance near Korolev fell from 13 (2191) to 9 (2198); targets used: (34,37) bfs-3 edist 10 (run1), (36,39) bfs-3 edist 12 (run2), (35,36) bfs-3 edist 9 (run3, a tile session 89's run6 walker actually crossed). The box after run3: 2204, bases_ours 2, units_ours 11, n_bases 28, the arrived walker at Korolev, the war at our doorstep (enemy units within 9 tiles). Tests: `test_walk_diff.py` -> `PASS 37/37 attribution cases`; classifier gates untouched: `test_classify.py` 17/17, `check_classes.py` 17/0 (no new classes; `_3x.png` deleted; no new evidence frames — budget unchanged).

**Open.** (1) The 0x100000 turn_flags bit is unexplained. (2) A pump burst can still outrun the turn boundary if one loop iteration exceeds the ~8 s round (the rescan shortens the order step, the poll closes the turn on the flip — but OCR garbage at 15 s/iteration remains a risk; run1's shape was never FORCED after the fixes). (3) `queued_rescan` attributes only through uniqueness — two of ours queued in one window says nothing (conservative by design). (4) The quiet window is nearly gone: expect to reload `m54b_clean.SAV` + re-found before the next walking experiment.

**Next:** the walking arc (M54i2 -> M54j -> M54k -> M54k2) is CLOSED — a hook-armed, loop-ordered, multi-turn walk onto our own base, PASS with the checker's own instrumentation. The footing's open spines are S1 (production rebuild) and S2; ROADMAP line 86 defines S2 as the **solo turn advance** — TURN COMPLETE -> upkeep -> production -> research -> AI -> events -> next player — and this session's burst/auto-advance/0x100000 findings are heartbeat facts. Pick: an S2 milestone that INVENTORIES the round boundary from memory (what is produced on our base tiles, what upkeep moves — energy deltas are already in the trace, where research progress lives, which turn_flags bits flip when), acceptance = a script printing PASS on one real read. Re-read the ROADMAP S2 row before committing.

## Session 91 (2026-10-25) — M55: **THE SOLO ROUND BOUNDARY IS READ END TO END FROM MEMORY AND EVERY DIFF IS ACCOUNTED — `scripts/m55_boundary.py` prints PASS on a real invocation (2217->2218, 10/10 floors); a hand-typed fixture FAILs (5 floors) and the no-poke dry probe FAILs (no flip in 4 s)** — changed `scripts/m55_boundary.py` (NEW: reads one boundary from /proc/<pid>/mem, samples cur_player/year/round/stage/turn_flags at 2 ms, accounts every unit/base/faction diff), `scratch/m55_fixture_bad.json` (hand-typed negative), `NEXT_PROMPT.md`, this file, skill `references/wine-operations.md`

**Acceptance — the exact commands and what they printed:**
- `python3 scripts/m55_boundary.py` -> exit 0, `PASS boundary 2217->2218: player walk observed (cur_player [0, 2, 3, 5, 6, 7]), upkeep income read for 7 factions, research advanced, production: no net-new order-0 arrivals this round`, all 10 floors `ok`, trace `evidence/trace_m55_boundary_20261025_194440.jsonl`. An earlier identical PASS: 2215->2216, `evidence/trace_m55_boundary_20261025_194200.jsonl`.
- `python3 scripts/m55_boundary.py --fixture scratch/m55_fixture_bad.json` -> exit 1, `FAIL boundary accounting`, 5 BAD (walk only 4,5; our unit moved (10,10)->(11,10); production arrived order 2; ledger {4: 7}; research flat for every faction).
- `python3 scripts/m55_boundary.py --no-poke --no-enter --timeout 4` -> exit 1, `FAIL no round boundary (year never moved) within 4.0s` (the gate is not vacuous).

**What the boundary actually is (all read from memory, this session):**
1. **Solo heartbeat = the player WALK in `FUN_00520c10`.** `cur_player` walks every active player and ends at ours: observed sequences `[3,3,4,5,6,6,7,0,2,2,3]`, `[7,3,4,5,6,7,2,3]`, `[3,3,5,6,7,0,2,3]` — the walk ROTATES (starts after our id, not at 0). The MP 7-stage counter `DAT_0091c630` stayed 0 in every sample (15-40 samples/run) — never floor on stage in solo.
2. **The boundary needs no key when every unit is HELD: the engine auto-ends our turn.** Rounds ran 2206->2208 with zero input; at 2210+ rounds closed 1-2 s after our turn opened. BUT at 2204 the same hold-all state stalled 90 s (`stage 0`, all semaphores 0) — the auto-end gate (`DAT_0091f69c & 1`, "No units need orders Press ENTER") is CONDITIONAL and the trigger condition is still unidentified. **Confounded/unknown — do not claim "idle never advances" (session 90) nor "idle always advances" (this session).**
3. **Modal event dialogs FREEZE the walk.** "The Hive has eradicated the Gaians" held `cur_player = 2` for 90 s with every semaphore zero; the event chain then opened the PLANET display, which swallowed one Enter. Fix in the script: Return every 2 s while `cur_player != ours` (and while mid-walk) — safe, because Return is only consumed as turn-end when the human loop is running. `Escape` on the tactical map raises "Do you really want to quit?" — never press Escape (the footing already bans its OK; now ban the key).
4. **The boundary REWRITES bytes inside records that did not move.** Our 11 held records changed at u16 +28 (legs_y[0]), +48, +50 — each **decrements by 1 per round** while dying units are compacted out (a 2205 boundary with ~20 enemy deaths moved all three; a quiet boundary moved only +28). Identity for accounting is therefore **(x, y, type, owner, order)**, not 52-byte equality.
5. **Per-turn order resets and cargo.** AI units' transient orders (9, 14, 24, 27, 88) reset to 0 **in place**; order 24 = cargo/unload materialisation (two Settlers appeared at (12,50) with order 24, mp 3). Produced units arrive **order 0 on a base tile of their own faction**. Attribution across a boundary is confounded by moves + resets + cargo, so the floor is scoped to OUR side; enemy-side arrivals are labelled `production / cargo-or-order-reset / order-reset-in-place / move / unattributed`.
6. **ZERO production was measured in every round of this session** (~7 boundaries): no net-new order-0 arrival on any base of any faction. Session 90's claim that "production drops `+17 = 0` units on base tiles at every round boundary" did NOT reproduce. Faction sliders read `+0x104 = 0, +0x108 = 5..6` for all 8; base record `+0x3c` ticked 23->25 on Korolev (+2/round, a shield-style accumulator), `+0x34`/`+0x38` static. **This contradiction is M56.**
7. **Research is measured and it completes.** Three live completions: p2 rpoints 161->0 rtech 12->46; p6 -119 rtech 22->72; p2 190 pts rtech 46->44. Our points advanced +6, +12, +12, +3, +2 in most rounds — EXCEPT one boundary where ours stayed 8->8 with `labcnt 229->229` and `rtech 13->13`; ours had completed tech 36 at an earlier boundary (108->8). Our `labcnt` reads 229 while other factions read 5-137 and p0 reads -1 — **the `LAB_ARR` parallel array is suspicious after player 1 (Gaians) died** (faction slot 1 left the active mask 0xFF -> 0xFD); verify its indexing before trusting per-faction lab counts.
8. **Our side took real losses.** Garrison at University Base attrited 11 -> 10 -> 6 -> 5 units at (28,42) with no arrival of the same class (deaths, cause unattributed); then **University Base (28,42) was CAPTURED by faction 6** at the 2214->2215 boundary — the base record survived with `faction 6` (28 bases before and after). C6's floor is therefore "no base of ours VANISHES; a capture is reported", not "we never lose a base".
9. **`turn_flags` 0x100000 is set by Enter and cleared at the boundary** (observed `0x100002 -> 0x2` at +0.073 s, the only flip seen). With auto-end closing the turn, no flip appears at all (`0x2 -> 0x2`) — a flip is expected only when a key ends the turn.
10. Energy deltas were read for 7-8 factions every round (e.g. `{0:0, 2:-11, 3:0, 4:3, 5:3, 6:-24, 7:-23}`), the spending ledger `faction+4` was zero for every player after upkeep in all runs, and energy never went negative (code clamp holds).

**Open:** the production contradiction (#6) and why the whole map builds nothing; our flat-research round and the `LAB_ARR` shift (#7); death-cause attribution (#8); the auto-end gate condition (#2); enemy-side production attribution (confounded, #5). **The game is nearly lost: 1 base (Korolev Center 29,42), 5 units, year 2218, pid 1329211** — a future run may need the reload recipe before it can measure anything.

**Next:** M56 — resolve the production contradiction: prove from memory whether ANY base builds (base queue/cost fields + faction sliders + the +0x3c accumulator) across 2-3 boundaries, with a floor that FAILs on a hand-typed production trace.

## Session 92 (2026-10-25) — M56: **WHY NOTHING GETS BUILT — the gate is MINERAL STORAGE, the natural queues are EMPTY on all 28 bases, and session 91's "zero production" was a false negative (enemy bases produced in every boundary)** — changed `scripts/m56_build.py` (NEW: per-base production predictor + boundary verifier), `scripts/test_m56_predict.py` (NEW: 8 rule cases vs a mock /proc/mem), `NAMED.md` "M56 block", `ORDERS.md` §15, `scratch/m56_dump.py` + `scratch/m56_fixture_bad.json` (untracked), `evidence/m56/` (3 frames), this file, `NEXT_PROMPT.md`, skill `references/production-queue.md`

**ACCEPTANCE MET.** `python3 scripts/m56_build.py --arm 17 --boundaries 3 --timeout 120` -> `PASS production prediction: 1 verified unit arrivals over 3 boundaries, every prediction and every observed arrival accounted, queue bookkeeping exact` — `evidence/trace_m56_build_20261025_201353.jsonl`: **3/3 boundaries flipped +1** (2226->2227->2228->2229, walks [0,2,3,5,6,7] each, home to us), **1 POSITIVE prediction verified**: base 17 Korolev Center (29,42) armed by the controlled poke (pending 0->1, head -38->2 Scout Patrol, minerals 0->100, read back) -> predicted (minerals 100 >= price 10 = 10 x type_cost +41=1) -> a (29,42,type2,fac3) record appeared on the base tile, `pending 1->0`, `queue [2,-38,-38]->[-38,-38,-38]`, `minerals 100->0` (the pay -10 then **clamp B `max(0,min(10,d0))=0`** re-caps storage — M53k §D, not a 100-cost). Fixture: `python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> **exit 1**, `BAD at least 1 POSITIVE prediction verified — 0/1` (the after-units mutated: the predicted arrival removed). Rule tests: `python3 scripts/test_m56_predict.py` -> `PASS 8/8 production-prediction cases` (empty queues predict nothing; minerals 9 < 10 no / 10 = 10 yes; progress 99 with minerals 9 does NOT predict; head -30 predicts no unit; out-mask owner not predicted; price scales with +41). Classifier gates untouched: `test_classify.py` 17/17, `check_classes.py` 17/0 (no new classes; untracked `_3x.png` deleted, tracked ones restored).

**THE ANSWER TO THE MILESTONE (all read from memory).** (1) **The gate**: the queue processor `0x4ef6d0` (pipeline stage 6 of `0x4f5a70`, shard_012.c:24182) completes a queue head iff **mineral storage `base+0x40` >= price** (`0x4f0a3d cmp minerals,edi; jl return`), price = `0x4e40a0(owner,1,-1) x type_cost(+41)` = 10 x cost in-mask; pay `0x4f0ca6` -> clamp B -> POP `0x4ef5d0` (pending `+0x4c` -1, queue `+0x50..` left-shift, `faction[head]-1` at `0x94dc84`) -> `FUN_005ab650` creates the unit on the base tile (shard_012.c:20890, right after the debit). Per-round chain: `0x5208f0(p)` -> `0x520540(p)` -> the per-owner base loop (shard_013.c:11568) -> `0x4f5a70(base)` -> `0x4ef6d0` — **every base every round in solo; no "production phase" gate** (the `faction+0x104 & 2` gate at `0x521070` guards only the AI upkeep step `0x574370`; session 91's "sliders +0x104 = 0 for all 8 -> nothing can build" read the AI step, not the queue). (2) **`+0x3c` progress / `+0xcc` rate do NOT gate** — the armed base had income 0, rate 1, progress 32 and produced on the very next boundary; an accumulation model says no. Docs vs code: M53i's `cost <= +0xcc + +0x3c` completion test is the OUT-mask race scan / display path (`0x4ee8c7` "display only", M53k); the storage gate wins, proven by the poke. (3) **Why nothing builds**: natural state (read before any poke): **pending 0 + head -38 on ALL 28 bases**, every base net income `+0xd0` = 0 — the gate can never fire. (4) **The session 90/91 contradiction**: session 90 was RIGHT — enemy-side order-0 arrivals on enemy base tiles in EVERY M56 boundary ((20,24) fac 2 at 2223, base 22 fac 6 at 2226, base 24 fac 7, base 14 fac 2 at 2228); session 91 counted only OUR-side arrivals -> false negative.

**Two freezes found the hard way (both in the script now).** (a) **A produced unit arrives order 0 and FREEZES the auto-end**: `cur_player` 3, `turn_flags` 0, Return every 2 s for 150 s does nothing (run r1 died twice); ONE `h` on the cursor unit -> HOLD closed the turn at once (`tf 0->2`, walk resumed) — the script escalates Return -> `h` every 4 s past 8 s parked on our turn. (b) **The Operations Director popup does not close on Return** — default row "Zoom to Base Control", Return CYCLES options; click OK at ~(630,247). The popup text is also the **support cliff**: "The minerals output of Korolev Center is not sufficient to support Scout Patrol unit. The unit has been disbanded." — produced units die to upkeep when the base has no mineral income (our units 7->3 at 2221-2222). Escape on the map raised the quit prompt AGAIN (`evidence/m56/quit_prompt_2220.png`; "Oops, no, wait!" default, Return takes it).

**Open.** (1) Enemy-side predictions are REPORTED not floored (queues refill inside their AI turn — read them mid-turn for a real enemy-side floor). (2) The out-mask price model (era table `0x68cbb8` factor) is unmodeled. (3) Facility/project (negative-head) completions are not floored (bitmap `+0x8c` deltas). (4) The `h`-escalation assumes the cursor parks ON the actionable unit; if it parks elsewhere the loop falls back to the OK click. (5) The box after the acceptance run: **~2229, 1 base (Korolev), ~3 units, queue re-armed each run (pending 1 head 2 minerals poked 100)** — the support cliff eats every produced unit; the game is nearly lost and a reload (`m54b_clean.SAV` + re-found) may be needed before the next measurement.

**Next (M57):** give the loop an ECONOMY: either (a) reload `m54b_clean.SAV` + re-found and get a real (non-poked) positive prediction — a base whose queue the game itself filled (AI chooser at `0x4f6030` fills enemy queues; ours needs the BUILD UI `0x417ee0` or a facility that yields minerals `+0xd0 > 0` so storage >= price naturally), or (b) prove the facility side: queue a facility (negative head) at an armed base and floor the `+0x8c` bitmap delta + the `0x417ee0` queue-edit dispatch from memory. Acceptance: `scripts/m56_build.py` (extended) prints PASS on ONE real invocation with a positive arrival **not** armed by a minerals poke. Re-read `NAMED.md` M56 block + `0x417ee0` (queue edit) before shaping.

**Close addendum (follow-up session, 2026-10-25).** M56 was CLOSED in a follow-up session (the session-92 context died before the close sequence). Fresh deterministic re-verification: `test_m56_predict.py` -> `PASS 8/8 production-prediction cases`; `m56_build.py --fixture scratch/m56_fixture_bad.json` -> **exit 1** `FAIL production prediction accounting`; `test_classify.py` 17/17, `check_classes.py` 17/0, `test_walk_diff.py` 37/37. Fresh LIVE acceptance in that session: `python3 scripts/m56_build.py --arm 17 --boundaries 3 --timeout 120` -> `PASS production prediction: 1 verified unit arrivals over 3 boundaries, every prediction and every observed arrival accounted, queue bookkeeping exact` — 3/3 boundaries flipped +1 (2229->2230->2231->2232, walk [0,2,3,5,6,7] home to us each), 1/1 POSITIVE prediction verified (base 17 Korolev Center 29,42 type 2: pending 1->0, minerals 100->0 clamp B, queue left-shifted), trace `evidence/trace_m56_build_20261025_203513.jsonl`; the session-92 acceptance trace `..._201353.jsonl` was also re-parsed: 15/15 checks ok, `positive_verified 1`. Box at close: **year 2232, 1 base (Korolev Center 29,42), units_ours 2, n_bases 29, pid 1329211** — M57 should expect the reload recipe.
