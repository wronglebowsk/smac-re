# NEXT_PROMPT.md — footing for the next session (written at the end of session 82, 2026-10-25)

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
- **M54E — THE ORDERED WALK LANDS INSIDE THE UNATTENDED RUN** (session 82, PR #44, numbers in
  Session 82 of `SESSION_NOTES.md`): `scripts/m54e_prep.py` empties
  our base tile, pokes the garrison onto the REAL neighbour (4,12) and makes one record class 9;
  then at a turn boundary `smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54e40
  --verbose` -> `evidence/trace_m54e40_20261025_010855.jsonl` -> `m54a_check_run.py <that trace>
  --timeout 240 --min-orders 31 --min-moves 5` -> `advanced 40/40`, `{1: 40}`, `stuck 0`,
  `orders 31 VERIFIED of 75` (`g->24` x5, `l->1` x24, `h->2` x2), **`moves 5 LANDED of 5
  ordered walks, on turns [0, 9, 12]`**, `PASS`. Why it had never landed (`ORDERS.md §7`): the
  pump runs `0x18` **as the chooser's OK is answered**, not at EXEC; the byte window is tens of
  ms; **the game will not path into a tile its own owner occupies**; `(base.x+1, base.y)` is
  **not a neighbour**.
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold: a save with mid-round bit1 set spins after load.

## THE PICK — M54f: give the loop a destination it did not have to manufacture

Do exactly ONE milestone, then stop. Do not re-verify closed work (M54a #39, M54b #40,
M54c #41, M54d #43, M54e — see the ledger and Session 82). Do not open FOOTING.md, do not
re-run the M53 census.

What M54e proved, and what it left open:
1. **`g` can only name OUR OWN base tile, and the walk only lands when that tile is empty.**
   The loop walks a unit back onto its own base after `scripts/m54e_prep.py` pokes the garrison
   off it — it has no destination it can reach on its own terms.
2. **The Former's settle / found-a-base order is unkeyed.** `NAMED.md` 120-146 lists the
   `param_3` menu chain; the unit panel's buttons are readable in the bottom-right panel. Read
   both before guessing a hotkey.
3. **Terraform keys are duds on this map** — `trace_m54e40` mixed `{"l->1": 24, "g->24": 5,
   "h->2": 2}` out of 75 attempts and spent 385 s ordering: the base tile is level 5 with a max
   of 4, so a nominal raise is refused (the raise-footprint question is the "Open" list in the
   skill's `references/terraforming-order-path.md`).

Pick ONE, in this order of preference, and prove it in memory:
- **(a) FOUND A SECOND BASE.** Key the settle order, walk a Former to a tile it can ENTER
  (`(bx-2, by)` or `(bx±1, by±1)`), issue it, and verify a NEW record in the base array
  (`0x95DA10` x 304, x `+0`, y `+2`, faction = LOW byte at `+4`, count `0x985AF4`) with
  `m54d_census.py` printing `bases_ours=2` inside ONE unattended run.
- **(b) The CURSOR destination.** The chooser's OK wrote leg `(9,11)` once while the listed
  base was `(6,12)` (`evidence/m54d/synth_after_ok.png`), so the destination may track the map
  cursor. Settle first what the HUD's bottom-left `(x,y)` panel follows (cursor or selected unit
  — session 81 could not tell), then drive the cursor with arrows while the chooser is up and
  order a walk to an empty non-base tile. Arrows queue nothing by themselves (M54e).
- **(c) Make a terraform LAND.** Prove a verified terraform byte changes the TILE record, not
  just `+17`. Oracle: the tile array (`DAT_0092ae14 + (mapw/2*y + x>>1)*0x2c`, even x `+0`, odd
  `+3`), never the screen.

Fix these in the same pass — known and cheap:
* **26 `unknown` pane hits** in `trace_m54e40` (`actions {"hud": 48, "ai-phase": 46,
  "unknown": 26}`): capture the frames, pin any new class in BOTH test files first.
* **44 dud keypresses cost ~385 s of a 40-turn run** — retire known-dead keys by type up
  front instead of rediscovering them three times per turn.

Acceptance shape (same discipline — one invocation, no human, checked by a script):
* a census line before and after: `bases_ours 1 -> 2` (for (c): the tile's level byte changed);
* inside ONE unattended run: the order byte verified by the `+17` delta in the loop, then the
  consequence read in memory after the pump ran it (for a MOVE: `x,y == last leg`, `+40` spent
  — `moves LANDED`);
* `python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-orders N --min-moves M`
  prints `PASS` with `advanced N/N`, year deltas `{1: N}` and `stuck 0`;
* any new pane goes into `scripts/test_classify.py` AND `scripts/check_classes.py` with saved
  frames BEFORE the driver uses it.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 80, 81, 82 are the recent work. Never read the whole
   file (~60 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start <ID>` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 82 ended with the game RUNNING at year
   2200, pid 484088, `cur_player 3`, 30 bases, our two class-9 records and three scouts
   garrisoned on University Base (6,12). `scripts/m54d_census.py` prints what is really there;
   `scripts/m54e_prep.py` re-arms a walk (empties our base tile, stands the garrison on the real
   neighbour (4,12), makes one record class 9). A fresh game is `scripts/m54a_newgame.py` (after
   `m54a_load.relaunch()`).

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing (arrows = cursor, Shift+arrows = pan; letters only reach the
  order dispatcher when orders mode is on AND a unit is selected), §2 the terraform family,
  §4 the byte table (`0x18` = queued MOVE, legs at `+20..+27` x / `+28..+35` y, last leg =
  destination; `0x19` = directional), §5 consequences, §6 the in-loop contract, **§7 when the
  queued MOVE actually runs** (the chooser's OK is the trigger, the ~tens-of-ms byte window,
  the occupied-destination refusal, why `(bx+1, by)` is not a neighbour, arrows queue nothing).
- The live skill's `references/terraforming-order-path.md` — same walking findings in
  operational form (what to poke, what to sample, what the pump does).
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

- Census / position: `python3 scripts/m54d_census.py [--json f]` (class mix, `CLASS9` lines,
  `on_own_base`, legs, `bases_ours`), `python3 scripts/m54e_prep.py` (empty our base tile, poke
  the garrison onto the REAL neighbour `bx-2`, make one record a class-9 Former),
  `python3 scripts/m54d_prep.py` (the older one-unit poke), `python3 scripts/m54d_probe.py
  --unit N` (one key at a time, reads `+17`/legs/`x,y`/`+40` + the screen class after each),
  `python3 scripts/m54e_probe.py peek|ours|prep|key|exec|chooser N` (the M54e tool: `chooser N`
  answers the `g` chooser and samples the record at 100 ms across the OK click).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--load <Z:\\path>] [--verbose]`. Orders ON by default (`--orders-per-turn 2`,
  `--order-budget 35`, `--no-orders` off). Each turn record carries `orders` (with `dest`) and
  — `moves` (`frm`/`dest`/`landed`/`mp_after`/`on_dest_after_exec`/`walked_inphase`) +
  `moves_verified`. `order_byte_watcher` samples `+17` at ~5 ms through the chooser's OK, and
  `issue_order_for_unit` polls the record for `WALK_POLL` (3 s) after a queued MOVE is answered
  — the pump runs it THEN, not at EXEC.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N]
  [--min-moves M]` — the ONLY thing that can print `PASS`.
- State: `python3 scripts/smac_state.py --json` (or `--watch`). Reads `/proc/<pid>/mem`; never
  pokes, never clicks.
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
- **A destination our own owner occupies is unreachable** — pathing refuses it and the unit
  oscillates between two neighbours. `g` only ever names a BASE tile, so a walk needs our own
  base tile FREE. And **`(base.x+1, base.y)` is not a neighbour** (two columns per tile record,
  even-x delta `(±2,0)`): use `(bx-2, by)` or `(bx±1, by±1)`.
- **Panes that classify as something else are key sinks.** The `g` chooser read `hud` (10 keys,
  0 bytes); the scene panel read `movie` (two runs frozen because Escape is gated by
  `--no-escape`); a live chooser frame in `trace_m54d40c` read `unknown` even though the saved
  frames read `dest-chooser` — widen the test when you catch that frame.
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

1. Patch a `## Session 83` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 84, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
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
