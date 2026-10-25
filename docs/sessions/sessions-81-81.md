# Session notes archive — sessions 81-81

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 81 (2026-10-24) — M54d: **THE LOOP CAN NOW QUEUE A WALK AND CHECK IT IN MEMORY; NO WALK HAS EXECUTED YET — THE ONLY DESTINATION `g` OFFERS IS OUR OWN, OCCUPIED BASE TILE** — `scripts/m54d_census.py`, `scripts/m54d_prep.py`, `scripts/m54d_probe.py`, `evidence/m54d/`

- **THE FOOTING'S PREMISE IS FALSE (measured).** `scripts/m54d_census.py` on the fresh game
  the wizard starts prints `units_ours=2 class9=0 class_mix={"3": 1, "8": 1}`: a Colony Pod
  (type 0, class 8) and a Scout Patrol (type 2, class 3), both standing on the faction's one
  base at (6,12), and **zero class-9 records anywhere in the game** — all 300 records decode
  `by (owner,cls)` to one pod + one scout per faction. NEXT_PROMPT's "every faction begins
  with Formers" is wrong: Formers (type 1, class 9) come from production, and the base's
  starting queue turns out Scout Patrols ("University Base builds ScoutPatrol",
  `evidence/m54d/base_pane.png`). So the class-9 position is MADE by `scripts/m54d_prep.py`:
  one record poked type 2->1 and one tile off the base, order and movement cleared. The
  census line the milestone asks for then reads
  `CENSUS pid=484088 year=2109 ... units_ours=3 class9=1 ... CLASS9 rec 8 type 1 cls 9 ( 7,12)
  order 0 mp 0 ... on_own_base=False`.
- **THE `g` CHOOSER WAS A KEY SINK HIDING AS `hud`.** `g` ("Move to") raises SELECT
  DESTINATION (caption y~102, a base row with `Distance: N` at y~132, its own OK/CANCEL bar
  row at y~162). OCR reads the caption and the row but never the bar labels, and only 5 words
  fall in the dialog band, so `classify` returned `hud` and the driver pressed TURN COMPLETE
  at a pane: `evidence/m54d/probe_unit0.json` fired 10 keys at a selected unit and got **zero
  order bytes**. New class `dest-chooser` + `answer_dest_chooser` (click the MERGED OK row
  centre (497,162): the two fill segments centred (474,162)/(521,162) are ONE bar split by
  the "OK" label — the same rule as the communication's OK bar). Pinned in
  `test_classify.py` and `check_classes.py` against `evidence/m54d/m54d_move_afterg.png` and
  `synth_chooser.png` BEFORE the driver used it.
- **THE SCENE PANEL FROZE TWO RUNS AS `movie`.** A full-screen Secret-Project artwork panel
  has a red CLOSE bar bottom-right (fill (94,10,9)/(73,9,8), y 579-599, x 596-799); OCR reads
  ~7 tokens off the whole frame, so it fell through to `movie`, whose only answer is Escape —
  and Escape is gated by `--no-escape 3000`, so turns 0 of the first two runs of this milestone
  (tags `m54d40`, `m54d40b`; their traces pruned at the end of the session for the evidence
  budget, the third run's is kept) sat with the year frozen. New class `artwork-close` + `close_bar(png)` (colour test on the
  bottom-right strip; the bar's red is told from the terrain's red by the GREEN channel,
  g<30 vs ~50); fixture `evidence/m54d/peek_stuck.png`, pinned in both test files.
- **THE WALK MACHINERY, AND WHERE IT STOPS.** `order_step_in_loop` now fires `g` FIRST (a
  Former that gets `f` first lands a terraform byte and `landed` stops the plan — that is how
  M54c ordered 31 units and moved none) and skips it for a unit standing on one of our bases
  (`own_base_tiles`, 0x95DA10 x 304, faction = the low byte at +4), because that is the case
  the game refuses and three refusals retire the key. A landed 0x18's route is read from the
  record (`+20..+27` x / `+28..+35` y, last leg = the ordered destination); `service_turn`
  snapshots our records before TURN COMPLETE and `verify_moves` re-reads them after the year
  flips, requiring the record to sit ON the ordered tile with `+40` spent;
  `m54a_check_run.py` grew `--min-moves`. Live proof the queue works: mid-run the census read
  `rec 7 ... order 24 ... legs=[6,...] legs_y=[12,...]` — byte 0x18 with destination (6,12).
  It never executed: the only destination the chooser offers is our own base tile, which the
  other four units occupy, and the loop's own read missed the byte (it lands only after the
  pane is answered, so the trace recorded `order_after 0`).
- **ACCEPTANCE NUMBERS OF THE 40-TURN RUN (NOT MET).**
  `python3 scripts/m54a_check_run.py evidence/trace_m54d40c_20261024_234229.jsonl --timeout
  240 --min-orders 5 --min-moves 1` -> `advanced 40/40` but year deltas `{3: 1, 1: 39}` (turn
  0 attached mid-round, so the year jumped 3), `stuck 0`, max dt 44.2 s, `orders 2 VERIFIED of
  8 attempted` (both `l`->byte1), **`moves 0 LANDED of 0 ordered walks`**, `FAIL` — M54d stays
  open. `python3 scripts/test_classify.py` -> `PASS 14/14 screen classifications`;
  `python3 scripts/check_classes.py` -> `frames: 14 failures: 0`.
- **State of the box:** the run left the game at 2151 (`cur_player 2`), the driver exited
  normally; the box still holds the made position (a class-9 Former one tile off University
  Base) with a 0x18 order parked on it.
- **Next (M54e):** make the walk land. The destination must be a tile the unit can ENTER:
  either (a) answer the chooser with the CURSOR on an empty tile — the synth run's OK wrote
  leg (9,11), not the listed base, so the chooser's destination tracks the map cursor, and
  the cursor is movable (arrows drive it; blind map clicks scroll the view —
  `evidence/m54d/clickcal_last.png`); or (b) get a second base so a unit 1-3 tiles from it has
  an unoccupied, reachable destination (founding one is a Former order nobody has keyed yet);
  or (c) clear the base tile. Secondary: the live chooser frame classified `unknown` in
  `trace_m54d40c` turn 0 even though the two saved frames classify `dest-chooser` — capture
  that live frame and widen `is_dest_chooser`; and `verify_moves` should read the byte again
  after the pane is answered, since the setter writes it late.
