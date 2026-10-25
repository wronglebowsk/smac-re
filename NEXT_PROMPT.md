# NEXT_PROMPT.md — footing for the next session (written at the end of session 83, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A — the driver survives a full game unattended** (sessions 77-78, PR #39).
- **M54B — 40 turns from a saved position, unattended** (session 79, PR #40): `smac_play.py
  --turns 40 --timeout 240 --no-escape 3000 --tag m54b40 --load
  Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV --verbose` -> `advanced 40/40`,
  `stuck 0`, `PASS`; `scripts/m54b_clean_save.py` makes a resumable save from a hung autosave.
- **M54C — the unattended loop ORDERS units** (session 80, PR #41): same command, tag
  `m54c40c` -> `advanced 40/40`, `stuck 0`, **`orders 31 VERIFIED of 36`**, `PASS`.
- **M54D — the loop queues a MOVE and checks it in memory** (session 81, merged #43, closed by
  M54e's run): `g` lands `0x18`, the record carries the leg-array route, the `dest-chooser` and
  `artwork-close` panes are pinned.
- **M54E — THE ORDERED WALK LANDS INSIDE THE UNATTENDED RUN** (session 82, PR #44):
  `m54e_prep.py` empties our base tile and stands the garrison on the real neighbour (4,12);
  then at a turn boundary `smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54e40
  --verbose` -> `evidence/trace_m54e40_20261025_010855.jsonl` -> `m54a_check_run.py <trace>
  --timeout 240 --min-orders 31 --min-moves 5` -> `advanced 40/40`, `{1: 40}`, `stuck 0`,
  `orders 31 VERIFIED of 75`, **`moves 5 LANDED of 5 ordered walks, turns [0, 9, 12]`**,
  `PASS`. Mechanism in `ORDERS.md §7`: the pump runs `0x18` **as the chooser's OK is answered**,
  the byte window is tens of ms, and the walker must START on a real neighbour. **That run also
  lost the position (`bases_ours 0`) — read the audit at the end of Session 82.
- **M54F — the type byte is settled and the checker can see a defeat** (session 83): the unit
  TYPE is the **u16 at `+10`** (binary: `shard_012.c:2150` indexes the class table with the
  short at record `+0x0A`), so session 82b's "+4" finding is retracted and every class-9 line
  stands; `smac_state.py` now prints `bases_ours`/`units_ours`, every turn snapshot carries
  them, and `m54a_check_run.py --min-our-bases N` fails a run that loses the position (the M54e
  trace now FAILs that floor). The box was reloaded from `m54b_clean.SAV` after session 82 left
  a defeated faction.**
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold: a save with mid-round bit1 set spins after load.

## THE PICK — M54g: found a second base, so the loop has a destination it did not manufacture

Do exactly ONE milestone, then stop. Do not re-verify closed work (M54a #39, M54b #40, M54c #41,
M54d #43, M54e #44, M54f — the ledger). Do not open FOOTING.md wholesale: the 52-byte layout is
settled (type u16@+10, flags dword@+4, owner@+14, order@+17, legs@+20..+35, mp@+40).

Why: `g` only ever names OUR OWN base tile, so every walk M54e proved landed back on the tile a
poke had emptied. A second base gives a Former a reachable, unoccupied destination the loop can
aim at without manufacturing anything.
1. **The Former's settle / found-a-base order is unkeyed.** `NAMED.md` 120-146 lists the `param_3`
   menu chain; the unit panel's buttons sit in the bottom-right panel. Read both, then poke ONE
   key at a time and read `+17` (a settle byte will not be `0x18`). Do not guess a hotkey twice.
2. **Walk the Former to a tile it can ENTER**: `(bx-2, by)` or `(bx±1, by±1)`, never `(bx+1, by)`
   (half-tile offset, not a neighbour). A walk needs `+17`/`+40`/legs cleared and the walker
   standing on a real neighbour. **Occupancy is NOT a blocker** — that trap is retracted in
   Session 83; units stack on a destination tile.
3. **Prove it in the BASE ARRAY, not on the screen**: `0x95DA10` stride 304, x `+0`, y `+2`,
   faction = LOW byte `+4`, count `0x985AF4`. `smac_state.py` prints `bases_ours` directly.

Acceptance (one invocation, no human, checked by a script):
* `smac_state.py --json` -> `bases_ours 1` before and `2` after, inside ONE unattended run;
* the settle order verified by the `+17` delta in the loop, then the base array read back;
* `python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-our-bases 2` prints `PASS`
  with `advanced N/N`, `year deltas {1: N}`, `stuck 0` — **use the floor**: a run that loses the
  position must not pass;
* any new pane goes into `scripts/test_classify.py` AND `scripts/check_classes.py` with saved
  frames BEFORE the driver uses it.

**If the settle order cannot be keyed in this session, do not manufacture a base.** Report the
negative result (which keys were tried, what `+17` did), merge the notes, and leave M54g open.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 80, 81, 82 are the recent work. Never read the whole
   file (~60 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start <ID>` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 83 left the game LIVE at **2155**, pid
   645846, `bases_ours 1`, `units_ours 6` (all six on University Base (28,42)), `turn_flags 2`.
   Bit `0x2` latches after any driver run and does NOT clear on a TURN COMPLETE click; a reload
   clears it (load reads 0 at 2150). It is not a wedge — turns still flip. If the state reads
   impossibly: `SMAC_SAVE='Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV'
   python3 scripts/m54a_load.py --relaunch` (38 s to a live HUD, measured).

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing (arrows = cursor, Shift+arrows = pan; letters only reach the
  order dispatcher when orders mode is on AND a unit is selected), §2 the terraform family,
  §4 the byte table (`0x18` = queued MOVE, legs at `+20..+27` x / `+28..+35` y, last leg =
  destination; `0x19` = directional), §5 consequences, §6 the in-loop contract, **§7 when the
  queued MOVE actually runs** (the chooser's OK is the trigger, the ~tens-of-ms byte window,
  the occupied-destination refusal, why `(bx+1, by)` is not a neighbour, arrows queue nothing).
- The live skill's `references/terraforming-order-path.md` — the walking findings in
  operational form.
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record (`+0/+2` x/y, `+4` flags, `+9` frozen,
  `+10` type, `+14` owner, `+17` order, `+40` movement) and the 304-byte base record (`x@0`,
  `y@2`, faction = the LOW byte at `+4`), base count at `0x985AF4`.
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**: type 0 =
  Colony Pod (class 8), type 1 = Formers (class 9), type 2 = Scout Patrol (class 3). The class
  table is `0x98ADB2[type*52] & 0xff`.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md +
  `references/wine-operations.md` (launch, load, the order step, the panes — session 81 added
  the chooser and the scene CLOSE bar there).

## OPERATIONAL KIT

- Census / position: `m54d_census.py [--json f]` (class mix, `CLASS9` lines, `on_own_base`,
  legs, `bases_ours`), `m54e_prep.py` (empty our base tile, garrison onto the real neighbour
  `bx-2`), `m54d_prep.py` (older one-unit poke), `m54d_probe.py --unit N` (one key at a time,
  `+17`/legs/`x,y`/`+40` + the screen class), `m54e_probe.py chooser N` (answers the `g` chooser
  and samples the record at 100 ms across the OK click).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--load <Z:\\path>] [--verbose]`. Orders ON by default (`--orders-per-turn 2`,
  `--order-budget 35`, `--no-orders` off). Each turn record carries `orders` (with `dest`) and
  — `moves` (`frm`/`dest`/`landed`/`mp_after`/`on_dest_after_exec`/`walked_inphase`) +
  `moves_verified`. `order_byte_watcher` samples `+17` at ~5 ms through the chooser's OK, and
  `issue_order_for_unit` polls the record for `WALK_POLL` (3 s) after a queued MOVE is answered
  — the pump runs it THEN, not at EXEC.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N]
  [--min-moves M] [--min-our-bases N]` — the ONLY thing that can print `PASS`. `--min-our-bases`
  reads the new `bases_ours`/`units_ours` fields and fails CLOSED (a trace without them fails).
- State: `python3 scripts/smac_state.py --json` (or `--watch`). Reads `/proc/<pid>/mem`; never
  pokes, never clicks. Now also prints `bases_ours` and `units_ours` (unit records counted only
  when `type < 24` and x/y in range — 128/256/320 "types" are empty stale slots).
- Classifier tests: `python3 scripts/test_classify.py` (must end `PASS 15/15 screen
  classifications`) and `python3 scripts/check_classes.py` (must end `frames: 15 failures: 0`).
  Both run on SAVED frames — no game needed. **`check_classes.py` OCRs each frame at 3x and
  leaves a `_3x.png` sibling next to it: delete `evidence/**/_3x.png` right after running it**
  (session 82: that litter alone put `evidence/` over the 30 MB gate).
- Evidence: `scripts/evidence.py` — `frames`, `latest`, `shots`, `show <png>`,
  `trace <jsonl>`, `budget`. A 40-turn trace is ~55 KB: parse with a short python snippet,
  never cat.
- Wine: prefix `./programs/prefix`, `wine 10.0` bits at `./programs/`, `DISPLAY=:99`, Xvfb
  `:99` 800x600x16, window at 0,0. Launch = `m54a_load.relaunch()`. `pgrep -x terran.exe`
  (NEVER `-f` — it matches this shell and kills it).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **The oracle is memory, not the screen.** A dropped keypress and a rejected order look
  identical in OCR. Verify `unit+17`, and after execution `unit+0/+2` and `+40`.
- **The `g` chooser's OK stores the byte and the game's order pump eats it a tick later** — the
  window is tens of ms, so ONE read after the click is a coin flip (two sessions read
  `order_after 0` on walks that had already landed). Sample THROUGH the click
  (`order_byte_watcher`). `order_final 0` after EXEC proves nothing either: a hand-parked `0x18`
  survived three TURN COMPLETEs, because the year flip is not the pump. Full detail: `§7`.
- **A walk needs the walker to START on a real neighbour of the named base tile.** M54d's
  walker stood at `(bx+1, by)` — a half-tile offset the even-x delta tables (`0x67850c` dx /
  `0x678990` dy) do not list — and oscillated between two neighbours; every walker at `(bx-2, by)`
  landed first tick. **Occupancy is NOT a blocker**: at turn 9 of `trace_m54e40` records 5 and 8
  walked onto `(6,12)` while records 0 and 2 stood there. (An earlier version of this bullet
  claimed pathing refused an occupied tile — session 83 retracted it.)
- **Panes that classify as something else are key sinks.** The `g` chooser once read `hud` (10
  keys, 0 bytes); the scene panel read `movie` (two runs frozen — Escape is gated). Widen the
  test whenever a live frame reads `unknown`.
- **Escape at a clean HUD raises "Do you really want to quit?"**, and Return there is "Yes,
  that's an order, mister!" — the process is gone.
- **Arrows drive the MAP CURSOR, they do not order a unit** — re-measured in M54e on five
  records (plain and Shift, with and without the `0x10000` moved-bit cleared): `+17` stayed 0.
  `space` neither queues nor pumps. Blind map clicks SCROLL the view.
- **Mouse motion does not move the cursor.**
- **A faction COMMUNICATION is its own class (`comm`)**: click its own OK bar (y 347), never the
  console row under it.
- **`--load` needs a Windows path** (`Z:\...`), never a `file://` URI.
- **A 40-turn run is 15-25 minutes**: start it backgrounded with a generous `timeout`, then
  poll the state reader or the log's `^turn N:` lines. Do not hold a foreground call open.
- **Attaching mid-round makes turn 0 advance the year by more than 1** (`{3: 1, 1: 39}` in
  `trace_m54d40c`) and the `+1 per record` gate fails on turn 0. Start a run at a turn boundary
  or expect the gate to bite.

## THE 10 RULES — condensed from sessions 75-82

1. One milestone per session, then stop. Do not re-verify closed milestones.
2. Commit early (a commit on the branch is the only thing that survives an overflow), then
   checkpoint-commit every few hundred lines.
3. Patch docs; never read-then-write a doc over 10 KB.
4. Keep tool results small: grep/sed windows, `evidence.py show`, tail. Never cat a log.
5. New screen classes go into `test_classify.py` AND `check_classes.py` with saved frames
   BEFORE they go into the driver.
6. Acceptance is a script printing `PASS` on one real invocation. Never weaken a gate to make a
   run pass; if a run stalls, find the pane and pin it.
7. Verify state by reading memory (`smac_state.py`, `/proc/pid/mem`), never by trusting a
   screenshot, and never by assuming a keypress landed.
8. Before `git add -A`, sync `skill/` from the live skill
   (`~/.hermes/skills/smac-cvr-format/` -> repo `skill/`) and commit it in the same commit as
   the docs.
9. `gate.py`'s checkpoint check needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated, and
   every `path:NNN` citation you add must resolve. `gate.py` refuses `main`; submit/merge refuse
   a dirty tree — commit FIRST, then gate, then submit.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
    produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session 84` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 85, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
3. `git add -A && git commit -m '<ID>: checkpoint'`
4. `python3 scripts/gate.py --base main` (must be GREEN)
5. `python3 scripts/milestone.py submit --title "..."` -> note the PR number ->
   `gh pr checks <n>` -> `python3 scripts/milestone.py merge <n>`
Then STOP and report.

## IF YOU HIT "request exceeds the context window"

In your very next tool call run `git add -A && git commit -m '<ID>: checkpoint'`, then reply
with what is done and what is not. Do not try to compress and do not rewrite docs to recover —
that is what killed sessions 78 and 79.

## Never

- commit to `main`; `Escape` on the title screen (it exits); `pkill -f`/`pgrep|kill` by name
  (matches this shell); click OK on "Do you really want to quit?"; `--mode stop` (does not
  exist); `file://` with `--load`; a `clear`-prefixed command (gate refuses it); backticks in
  a commit message (the shell eats them — session 81 lost half its message that way); a
  `MEDIA:` line in your report unless you actually attached a file.

## Report style (what a finished session looks like)

One screen: what changed, the acceptance numbers WITH the command that produced them, what is
open, next pick. No narration.
