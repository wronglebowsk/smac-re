# Session notes archive — sessions 82-82

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 82 (2026-10-25) — M54e: **THE ORDERED WALK LANDS INSIDE THE UNATTENDED RUN — 5 WALKS EXECUTED IN A 40/40 RUN, THE BYTE CAUGHT AT THE CHOOSER, THE RECORD LEFT ON THE TILE ITS OWN LEG NAMED** — `scripts/m54e_prep.py`, `scripts/m54e_probe.py`, `scripts/smac_play.py` (`order_byte_watcher`, in-phase walk poll), `evidence/m54e/census_pre_run.txt`, `ORDERS.md §7` (PR #44, merged)

- **THE PUMP IS THE CHOOSER'S OK, NOT EXEC (measured).** `scripts/m54e_probe.py chooser 2`
  sampled `+17` and the whole 52-byte record at 100 ms across the OK click: `+0 ms order 24
  xy (4,12) mp 0 legs 6,12` -> `+100 ms order 0 xy (6,12) mp 3`. The click handler stores the
  byte and the game's own order pump (`FUN_004ce4a0` -> `FUN_00529e70` -> `FUN_004d1200`) eats
  it on the next tick. The year flip is NOT the pump: three TURN COMPLETEs with a hand-parked
  `0x18` re-aimed at an empty adjacent tile (6,13) moved nothing. So `order_final 0` after EXEC
  proves nothing — the byte has to be caught at the pane.
- **THE BYTE WINDOW IS TENS OF MILLISECONDS; ONE READ IS A COIN FLIP.** The first fix (one read
  after the pane answer) still missed it in a 2-turn smoke run: the trace said `order_after 0`
  while turn 1's attempts read `ux 6 uy 12` — the walk had already landed.
  `smac_play.order_byte_watcher` now samples `+17` at ~5 ms from a second `/proc/pid/mem` handle
  *through* the click, so the delta the acceptance asks for is the byte itself. The leg arrays
  survive execution (`order 0`, legs still `6/12` after the arrival), so the loop reads the
  route even when the byte was already consumed by the pump.
- **THE GAME WILL NOT PATH INTO A TILE ITS OWN OWNER OCCUPIES — that is M54d's blocker.** With
  four of ours standing on University Base (6,12) the walker oscillated (6,13)<->(7,12) across
  three EXECs and never arrived; the same order landed within one tick the moment the base tile
  was emptied. `g` can only ever name a BASE tile (§1/§4: the 0x18 branch copies
  `base[piVar21].x/y` into `+20/+28`), so an ordered walk needs our own base tile FREE.
- **`(base.x+1, base.y)` IS NOT A NEIGHBOUR — M54d's prep stood its Former on a non-neighbour.**
  The map packs two columns per tile record (`DAT_0092ae14 + (mapw/2*y + x>>1)*0x2c`, even x at
  `+0`, odd at `+3`) and `FUN_00502c40`'s even-x delta tables (`0x67850c` dx, `0x678990` dy)
  step `(±2,0)` and `(±1,±1)`. Live in both directions: one `Left` moved a Scout Patrol
  (6,12)->(4,12); one `g` walked the made Formers record (4,12)->(6,12).
- **THE FOOTING'S ROUTE (a) IS DEAD — ARROWS QUEUE NOTHING.** `Left`/`Right`/`Up`/`Down` (plain
  and Shift) left `+17` at 0 on five records, with and without the `0x10000` "has moved" bit
  cleared; `space` neither queues nor pumps. Route (c) — clear the base tile — is what works and
  needs no game change: `scripts/m54e_prep.py` pokes every unit of ours off the base tile onto
  the real neighbour (bx-2, by) and converts one of them (`+10` type 2->1 = class 9, order,
  `+40` and the legs cleared). Everything the run then claims is the game's own: the keypress,
  the chooser, the byte, the route and the walk.
- **THE LIVE CHOOSER FRAME IS PINNED.** `evidence/m54e/chooser_live.png` — the chooser with the
  HUD news pane and the Mission Year row still drawn under it, the frame session 81 classified
  `unknown` — went into `scripts/test_classify.py` AND `scripts/check_classes.py` before the
  driver used it: `PASS 15/15 screen classifications`, `frames: 15 failures: 0`.
- **ACCEPTANCE NUMBERS (MET).** `python3 scripts/m54e_prep.py` -> `POKE base (6,12) -> empty;
  garrison [0, 2, 5] -> (4,12)` / `POKE rec0: type -> 1 (cls 9) at (4,12), order 0, mp 0, legs
  cleared`. `python3 scripts/m54d_census.py` -> `CENSUS pid=484088 year=2160 turn_no=0
  player=3 cur_player=3 units_ours=5 class9=2 bases_total=21 bases_ours=1 class_mix={"3": 3,
  "9": 2}` plus two `CLASS9` lines (rec 0, rec 2, both `( 4,12) order 0 mp 0 ...
  on_own_base=False`) — `evidence/m54e/census_pre_run.txt`. Started at a turn boundary
  (`cur_player 3`, `turn_flags 0`):
  `python3 scripts/smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54e40
  --verbose` -> `evidence/trace_m54e40_20261025_010855.jsonl`, then
  `python3 scripts/m54a_check_run.py evidence/trace_m54e40_20261025_010855.jsonl --timeout 240
  --min-orders 31 --min-moves 5` -> `advanced 40/40`, `year deltas {1: 40}`, `stuck 0` (max dt
  85.1 s), `orders 31 VERIFIED of 75 attempted`, mix `{"g->byte24": 5, "l->byte1": 24,
  "h->byte2": 2}`, **`moves 5 LANDED of 5 ordered walks (record on the tile its own leg named,
  +40 movement spent), on turns [0, 9, 12]`**, `PASS`. Every landed walk reads `(4,12) ->
  (6,12) mp+3` with `on_dest_after_exec True` and `walked_inphase True`.
- **State of the box (AUDITED after the merge — the original sentence here was WRONG).** The
  driver exited normally, but the run did not leave us holding University Base: at 2201
  `bases_ours 0` — the base array holds 30 bases and faction 3 owns none (factions {5:14, 1:6,
  6:5, 7:3, 2:1, 4:1}) — and our 8 surviving records are all stacked on one tile, (47,47),
  order 1 (SENTRY). The screen at that moment shows a `Colony Pod (0-1-1)` at (47,47), which is
  the cross-check that this is a real read and not stale memory: the unit the game has centred
  IS one of those records. `turn_flags` sits at `0x100002` and survives a year flip (one TURN
  COMPLETE moved 2200 -> 2201, flags unchanged). So the box holds a defeated faction stuck
  "mid-round", not the tidy garrison this bullet first claimed ("our two class-9 records and
  three scouts back on University (6,12)" was inferred from the pre-run census plus the walk
  destinations — never read back — and it is false). **The M54e walk evidence is unaffected:**
  it is index-addressed `+17`/`+20..+35`/`+40`/`x,y` on records 0, 2, 5, 8, 11 at turns 0, 9,
  12, all before the base was lost.
- **`evidence/` is 29.3 MB** (`budget 20/30 [warn]`): the `_3x.png` OCR siblings
  `check_classes.py` writes next to every frame it OCRs were deleted — that litter alone pushed
  the tree over the gate (precedent for the prune: the same deletion list in
  `evidence/.git/PR_BODY.md`).
- **Next (M54f):** the walk only ever lands ON our own base tile, and only because a poke emptied
  it. Give the loop a destination it does not have to manufacture: key the Former's
  settle/found-a-base order — the unkeyed `param_3` menu chain (NAMED.md 120-146) and the unit
  panel's buttons — walk a Former to a tile, found, and verify a NEW base record in the base
  array (`0x95DA10` x 304, faction = low byte at `+4`) with the census printing `bases_ours=2`
  inside one unattended run. Secondary: 26 `unknown` pane hits in `trace_m54e40` still to pin,
  and the raise-footprint refusal that makes every terraform key a dud on this map.
