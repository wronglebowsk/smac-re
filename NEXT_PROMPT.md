# NEXT_PROMPT.md — footing for the next session (written at the end of session 87, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A — the driver survives a full game unattended** (sessions 77-78, PR #39).
- **M54B — 40 turns from a saved position, unattended** (session 79, PR #40).
- **M54C — the unattended loop ORDERS units** (session 80, PR #41).
- **M54D — the loop queues a MOVE and checks it in memory** (session 81, PR #43).
- **M54E — the ordered WALK lands inside an unattended run** (session 82, PR #44).
- **M54F — the type byte is settled; the checker can see a defeat** (session 83, PR #47).
- **M54G — the founding is keyed and the loop FOUNDED a base** (session 84, PR #48).
- **M54h — chooser geometry + walk-evidence rules** (session 85, PR #49, merged as notes).
- **M54i — attribution by record DIFF works in the loop** (session 86, PR #50, merged as
  notes; the walk floor was not met there).
- **M54i2 — A LOOP-ORDERED WALK LANDED ON OUR OWN BASE; ACCEPTANCE PASSED** (session 87 —
  run4 `PASS`, 1 own-base arrival; the PR number is in `git log` / this branch's merge).
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold.

## WHAT SESSION 87 ESTABLISHED — do not re-learn these the hard way

1. **The step table preserves (x+y) parity — this WAS the walk problem.** `dx` at
   `0x67850c`, `dy` at `0x678990`, 21 int32 pairs (`while ((int)local_2c < 0x54)`,
   ghidra_out/shard_013.c:21868; live read 2159): `(1,-1) (2,0) (1,1) (0,2) (-1,1)
   (-2,0) (-1,-1) (0,-2) (±2,±2) (3,±1) (1,±3) (-3,±1) (-1,-3)` + `(0,0)`. A queued MOVE
   can ONLY arrive at tiles of its start tile's parity. University Base (28,42) sums 70
   (even); every walker sessions 84-87 stood at (29,42)/(28,43) (71, odd) — unreachable,
   the oscillations were geometry. The driver gates `g` on a same-parity own base
   (`walk_parity_ok`) and sorts candidates by "stands on a `table_neighbors` tile of such
   a base". `ORDERS.md` §12. Tests: `test_walk_diff.py` cases 21-24 -> `PASS 24/24`.
2. **A chooser-queued 0x18 executes on the game's own TURN COMPLETE cycle**
   (`scratch/m54i2_pump.py`): the sole actionable record at (28,43) with leg (28,42) came
   back at (29,42), order still 24, `+40` = 3 spent; every HELD record sat put at `+40` = 0.
   §7's "three TURN COMPLETEs moved nothing" holds for HAND-POKED bytes only — the chooser's
   OK REGISTERS the order. `+40` = mp SPENT this round, re-zeroed at the next phase start.
3. **The cursor is GAME-OWNED; do not position it by poke.** Three cursor variables, none
   sticks (`*(u32*)0x7cdecc+0x1dd9c/+0x1dda0` re-synced in ~3 s; `DAT_0091b5f0/670` in 1.5 s;
   `DAT_0091b5e8` is an append-counter). `g` is an ORDER only via the dispatcher pokes (SEL_G
   + `0x91b5b8`); otherwise it falls to the cursor-tile handler: base tile -> BASE SCREEN,
   else nothing (session 86 run5 t0 re-attributed). A poke-MOVED unit stops being found at
   its new tile by the game's occupancy. `ORDERS.md` §11.
4. **`sp.focus()` is a silent NO-OP while `sp.WIN` is None** — scratch scripts that press
   keys must do `sp.WIN = sp.find_window()` first or the keys land wherever X thinks.
5. **`mp_after` reads the ARRIVAL: max mp over same-type records on the destination tile,
   never `hits[0]`** (index order — in run3 it was a held garrison at mp 0 while the landed
   walker's spent mp sat in a later hit). Garrison/HELD units and base-PRODUCED units sit at
   mp 0 on the dest tile (measured), so a nonzero max IS the arrival. The count delta (same
   type UP at dest, DOWN at origin, against the PRE-PRESS baseline) still must fire.
6. **Bases PRODUCE units onto their own tile mid-run** (run3: dest_count 3->5 = arrival +
   produced unit; `units_ours 7 -> 10` across two runs). Produced units: order 0, mp 0, empty
   legs, flags `0x10` — they become actionable and the loop sentries them.
7. **The war is a variable:** University Base was TAKEN once between 2167-2187 (runs 3-4) and
   recovered by reloading `m54b_clean.SAV` (2150) + `m54g_prep.py` + a 2-turn founding. After
   a reload the quiet window is ~10-15 years: finish the acceptance run inside it.
8. Classifier gates unchanged since session 85: `test_classify.py` 17/17, `check_classes.py`
   17/0 (`_3x.png` siblings deleted right after). No new classes appeared in session 87.

## THE PICK — M54j: LAND A MULTI-LEG WALK (the pump walks it across TURN COMPLETEs)

Do exactly ONE milestone, then stop. Do not re-verify closed work.

Both landings so far are ONE step. The open claim is the pump CONTINUING a route: order the
record standing at (20,42) (sum 62, even — same parity as University Base (28,42)) to
University Base, and let the game walk it (22,42)->(24,42)->(26,42)->(28,42) across TURN
COMPLETEs until it ARRIVES on our own base. The `carried` pending-walk path
(`verify_pending_walks`) re-checks unfinished walks every turn — it has never reported a
landing yet.

Acceptance (the ONLY thing that prints PASS; floors fail CLOSED):
`python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1`
on ONE unattended 6-turn run: `advanced 6/6`, year deltas `{1: 6}`, `stuck 0`, a `g->byte24`
line in the order mix, `bases_ours >= 2` at the END, and a `landed` move whose `dest` is a
tile holding ONE OF OUR BASES, NOT the unit's start tile, whose ORDER turn is EARLIER than
the turn the trace reports it landed (a multi-turn arrival). Never weaken a floor. If terrain
blocks the route, report the negative WITH per-turn position read-backs of the walking record
(census each turn) and merge the notes; do not manufacture a walk.

**Shape:** the box is at **2171, 2 bases, 10 units, n_bases 21** (pid 1110005). Census
FIRST — if a base is gone, reload `m54b_clean.SAV` + `m54g_prep.py` + a 2-turn founding
(session 87 did exactly that, ~4 min). Then `scratch/m54i2_setup4.py`-style prep: cancel any
live 0x18, HOLD everything (byte 2) except the record standing at (20,42) — read back on a
second handle that it is the ONLY actionable record (if it moved/died, pick whatever unit
stands on a `table_neighbors` tile of a same-parity own base instead, or accept a multi-step
start and say so). Then `smac_play.py --turns 6 --timeout 240 --no-escape 3000
--orders-per-turn 1 --tag m54j_runN`. Between runs, `scratch/m54h_clear.py` until `HUD CLEAN`.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 86 and 87 are the recent work. Never read the whole
   file (~65 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start M54j` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 87 left the game LIVE at **2171**, pid
   1110005, `bases_ours 2`, `units_ours 10`, `n_bases 21`, our phase. If it reads impossibly
   (nonsense types, zero bases of ours, arrays that decode as garbage): do NOT build on it —
   `SMAC_SAVE='Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV'
   python3 scripts/m54a_load.py --relaunch` (one base at 2150 — rebuild the second with
   `m54g_prep.py` + a 2-turn run).
5. `python3 scripts/m54d_census.py` — where our records and both bases are, RIGHT NOW
   (indices lie across turns; content is identity). `python3 scratch/m54h_clear.py` if any
   pane is up.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing, §4 the byte table (`0x18` queued MOVE, legs `+20..+27` x /
  `+28..+35` y — a WAYPOINT; the chooser's pick is the destination), §6 the in-loop contract,
  §7 WHEN the queued MOVE runs, §8 THE FOUNDING, §9 the chooser's rows, §10 SENTRY/HOLD + the
  pre-press baseline + the diff/attribution rules, **§11 WHO OWNS THE CURSOR, §12 THE STEP
  TABLE AND PARITY + the TURN COMPLETE execution + the mp_after rule**.
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record (type u16@+10, owner@+14, order@+17,
  legs@+20..+35, mp-used@+40) and the 304-byte base record (x@0, y@2, faction LOW byte at +4).
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**; class
  table `0x98ADB2[type*52] & 0xff`. Class 8 = colonist (founding), class 3 = Scout Patrol.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md`.

## OPERATIONAL KIT

- Census / position: `m54d_census.py`; `scratch/m54i2_setup4.py [x y]` (cancel the live 0x18
  at (x,y), HOLD everything else, assert it is the ONLY actionable record and a same-parity
  table-neighbour of an own base — the ONLY clean setup for the walk checker);
  `scratch/m54i2_pump.py [x y]` (does the game run a live queued 0x18 at TURN COMPLETE);
  `scratch/m54i_hold.py [x y]` (HOLD all but the lone tile); `scratch/m54h_clear.py [N]`
  (panes -> clean HUD); `m54h_probe.py peek|legs|chooser N [--row K] [--ok] [--cancel]`;
  `m54g_prep.py`; `m54a_load.py --relaunch` (SMAC_SAVE env).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--orders-per-turn 1] [--load <Z:\path>] [--verbose]`. Turn records carry `orders` (with
  `dest`, `chooser_pick`, `walk_diff {attributed, confounded, claim, rivals, before_legs}`,
  `order_counts`, `attempts`) and `moves` (with `landed`, `dest_is_own_base`, `carried`,
  `dest_count`/`src_count`, `mp_after`). A 6-turn run is ~2.5-4 min: background it, poll
  `grep -c '"turn"'` on the trace. `--orders-per-turn 1` keeps exactly one mover in flight.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N] [--min-moves
  M] [--min-our-bases N] [--min-own-base-arrivals K]` — the ONLY thing that can print `PASS`;
  floors fail CLOSED.
- Attribution/geometry tests: `python3 scripts/test_walk_diff.py` -> `PASS 24/24 attribution
  cases`. Classifier gates: `scripts/test_classify.py` -> `PASS 17/17 screen classifications`;
  `scripts/check_classes.py` -> `frames: 17 failures: 0`; **delete `evidence/**/_3x.png` right
  after**. `evidence/` is near the 30 MB FAIL budget — check `python3 scripts/evidence.py
  budget` BEFORE adding frames; gzip an uncited big text file if you need room.
- Wine: prefix `./programs/prefix`, `wine 10.0` at `./programs/`, `DISPLAY=:99`, Xvfb :99
  800x600x16, window at 0,0. Launch = `m54a_load.relaunch()`. `pgrep -x terran.exe` (NEVER -f).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **Parity before anything else:** a walker can never reach a base of the other (x+y) parity
  (§12). Check it before blaming the cursor, the pump, or the chooser.
- **`sp.focus()` does nothing until `sp.WIN = sp.find_window()`** — scratch keypresses are
  otherwise invisible to the game and look like "keys don't land".
- **The cursor is game-owned and pokes do not stick**; `g` works via the dispatcher pokes
  (SEL_G + `0x91b5b8`), which the driver already does. Poke-MOVED units are invisible to the
  game's tile occupancy (fine for founding prep, wrong for "stand here and be found").
- **OCR is ~1-15 s a poll and LIES about legibility**: the same chooser frame reads
  `dest-chooser` once and `unknown` the next (then Return answers it by DEFAULT). Poll the
  oracle at 100 ms; OCR only when memory has not answered.
- **Indices lie across a turn** (the array reshuffles AND GROWS — bases produce units onto
  their own tile, order 0 mp 0 empty legs). Content is identity; snapshot and diff.
- **Attaching mid-round makes turn 0 advance the year by 3** (checker fails `{1: N}`): attach
  in OUR phase or burn a turn first; the box is often parked on a dialog — `m54h_clear.py`.
- **The pump eats the byte tens of ms after the OK** — sample THROUGH the click
  (`order_byte_watcher` with `recs=`); one read after the click is a coin flip.
- Sentries (byte 1) move on their own every round and rewrite their legs; HOLD (2) is inert.
- **`b` (and every order letter) is a MAP-level key while orders mode is off** (`0x91b5b8 == 0`).
- **The tile array is behind a POINTER and the pitch is LIVE**: `*(u32*)0x92ae14 +
  (DAT_00692184*y + x>>1)*0x2c`, pitch 32 on this 64x64 world.
- **Escape at a clean HUD raises "Do you really want to quit?"**; Return there ends the
  process; Escape on the title screen exits. Never click its OK.
- Arrows drive the MAP CURSOR; `space` neither queues nor pumps; blind map clicks SCROLL;
  mouse motion does not move the cursor. `--load` needs a Windows path.

## THE 10 RULES — condensed from sessions 75-87

1. One milestone per session, then stop. Do not re-verify closed milestones.
2. Commit early (a commit on the branch is the only thing that survives an overflow), then
   checkpoint-commit every few hundred lines.
3. Patch docs; never read-then-write a doc over 10 KB.
4. Keep tool results small: grep/sed windows, `evidence.py show`, tail. Never cat a log.
5. New screen classes go into `test_classify.py` AND `check_classes.py` with saved frames
   BEFORE they go into the driver.
6. Acceptance is a script printing `PASS` on one real invocation. Never weaken a gate to make a
   run pass; if it cannot pass, say so and merge nothing (a documented negative may merge).
7. Verify state by reading memory, never by trusting a screenshot or a keypress you sent.
8. Before `git add -A`, sync `skill/` from the live skill and commit it in the same commit.
9. `gate.py` needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated and every `path:NNN`
   citation you add must resolve. `gate.py` refuses `main`; submit/merge refuse a dirty tree.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
   produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session 88` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 89, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`
4. `git add -A && git commit -m '<ID>: checkpoint'`
5. `python3 scripts/gate.py --base main` (must be GREEN)
6. `python3 scripts/milestone.py submit --title "..."` -> note the PR number ->
   `gh pr checks <n>` -> `python3 scripts/milestone.py merge <n>`
Then STOP and report.

## IF YOU HIT "request exceeds the context window"

In your very next tool call run `git add -A && git commit -m '<ID>: checkpoint'`, then reply
with what is done and what is not. Do not try to compress and do not rewrite docs to recover.

## Never

commit to `main`; `Escape` on the title screen; `pkill -f`/`pgrep|kill` by name (matches this
shell); click OK on "Do you really want to quit?"; `--mode stop`; `file://` with `--load`; a
`clear`-prefixed command; backticks in a commit message; a `MEDIA:` line unless you attached a
file; `skill_manage delete`; `nohup`/`&` in a tracked terminal call (use background=true).

## Report style (what a finished session looks like)

One screen: what changed, the acceptance numbers WITH the command that produced them, what is
open, next pick. No narration.
