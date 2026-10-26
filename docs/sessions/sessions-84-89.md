# Session notes archive — sessions 84-89

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
