# NEXT_PROMPT.md — footing for the next session (written at the end of session 81, 2026-10-24)

## THE LEDGER — read this first, it is the whole state of the project

Closed (PRs merged to `main`):
- **M54A — the driver survives a full game unattended** (sessions 77-78, PR #39).
- **M54B — 40 turns from a saved position, unattended** (session 79, PR #40):
  `python3 scripts/smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54b40 --load
  Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV --verbose` -> `advanced 40/40`,
  `stuck 0`, `PASS`. `scripts/m54b_clean_save.py` makes a resumable save out of a hung autosave.
- **M54C — the unattended loop ORDERS units** (session 80, PR #41): same command, tag
  `m54c40c` -> `advanced 40/40`, `stuck 0`, **`orders 31 VERIFIED of 36 attempted`**, `PASS`.
  Every one of those orders is `SENTRY` (byte 1). Nothing has ever MOVED.
- **M54D — session 81, merged as a PARTIAL (see Session 81 in SESSION_NOTES.md)**: the loop can
  now queue a MOVE and check it in memory, two new panes are pinned, and the census tooling
  exists. **No walk has executed yet.** Its acceptance line — "after EXEC verify `unit+0/+2`
  changed to the ordered destination and `+40` was spent" — is still unmet, so M54d is NOT
  closed; the numbers are in the Session 81 entry (`moves 0 LANDED of 0 ordered walks`).
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold: a save with mid-round bit1 set spins after load.

## THE PICK — M54e: make the ordered walk LAND

Do exactly ONE milestone, then stop. Do not re-verify closed work.

The machinery is built and waiting (`evidence/trace_m54d40c_20261024_234229.jsonl` proves the
loop queues `0x18` and the census proves the byte + leg land: `rec 7 ... order 24 ...
legs=[6,...] legs_y=[12,...]`). What is missing is a destination the unit can ENTER. Measured
facts to build on:

1. **`g` offers only OUR OWN base tile, and four units already sit on it.** The SELECT
   DESTINATION chooser lists bases with `Distance: N`; we have one base and it is occupied.
2. **The chooser's destination tracks the MAP CURSOR, not the listed row**: the synth run's OK
   wrote leg `(9,11)` while the highlighted row was University Base `(6,12)`
   (`evidence/m54d/synth_after_ok.png`). Arrows drive the cursor; blind map CLICKS scroll the
   view instead (`evidence/m54d/clickcal_last.png`, UI_MAP.md 275).
3. **Mouse MOTION does nothing** — 10 mousemove positions left the tile readout at (6,12).
4. A unit standing ON one of our bases cannot be ordered `g` at all (M54c) — the loop now skips
   that case instead of wasting the keypress.

Pick ONE of these, in this order of preference, and prove it:
- **(a) cursor destination**: put the cursor on an EMPTY tile adjacent to a unit that has
  movement, answer the chooser, verify `+17 = 0x18` with that tile as its last leg, EXEC, and
  verify `x,y == leg` and `+40` spent. Learn how the cursor moves (arrows while the chooser is
  up? after `select`?) — the HUD's bottom-left panel prints a tile as `(x,y)` and is a
  readable oracle, though session 81 could not tell whether it follows the cursor or the
  selected unit.
- **(b) a second base** so a unit 1-3 tiles away has a reachable, unoccupied destination.
  Founding one is a Former order nobody has keyed yet (check the `param_3` menu chain,
  NAMED.md 120-146, and the unit panel's buttons).
- **(c) clear the base tile** (move the garrison off it) and walk the Former back onto it.

Acceptance shape (same discipline as M54b/M54c — one invocation, no human, checked by a script):
- a position with at least one class-9 unit we own, printed by `scripts/m54d_census.py`
  (`CLASS9` line, `on_own_base=False`);
- inside ONE unattended run: `g` lands `0x18` (or `0x19`/a terraform byte) verified by `+17`
  in the loop, then after EXEC the record sits on the tile its own leg named with `+40` spent;
- `python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-orders N --min-moves M`
  prints `PASS` with `advanced N/N`, year deltas `{1: N}` and `stuck 0`;
- any new pane goes into `scripts/test_classify.py` AND `scripts/check_classes.py` with saved
  frames BEFORE the driver uses it.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 79, 80, 81 are the recent work. Never read the whole
   file (~57 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start <ID>` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 81 ended with the game RUNNING at 2151,
   `cur_player 2`, holding the made position (a class-9 Former one tile off University Base,
   a parked `0x18` order on it). `python3 scripts/m54d_census.py` prints what is really there.
   A fresh game is `scripts/m54a_newgame.py` (after `m54a_load.relaunch()`), and
   `scripts/m54d_prep.py` re-makes the class-9 off-base unit.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing (arrows = cursor, Shift+arrows = pan; letters only reach the
  order dispatcher when orders mode is on AND a unit is selected), §2 the terraform family,
  §4 the byte table (`0x18` = queued MOVE, legs at `+20..+27` x / `+28..+35` y, last leg =
  destination; `0x19` = directional), §5 consequences, §6 the in-loop contract.
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
  `on_own_base`, legs), `python3 scripts/m54d_prep.py` (poke one record to a class-9 Former
  one tile off our base), `python3 scripts/m54d_probe.py --unit N` (one key at a time, reads
  `+17`/legs/`x,y`/`+40` + the screen class after each).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--load <Z:\\path>] [--verbose]`. Orders ON by default (`--orders-per-turn 2`,
  `--order-budget 35`, `--no-orders` off). Each turn record carries `orders` (with `dest`) and
  — new in session 81 — `moves` (`frm`/`dest`/`landed`/`mp_after`) + `moves_verified`.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N]
  [--min-moves M]` — the ONLY thing that can print `PASS`.
- State: `python3 scripts/smac_state.py --json` (or `--watch`). Reads `/proc/<pid>/mem`; never
  pokes, never clicks.
- Classifier tests: `python3 scripts/test_classify.py` (must end `PASS 14/14 screen
  classifications`) and `python3 scripts/check_classes.py` (must end `frames: 14 failures: 0`).
  Both run on SAVED frames — no game needed.
- Evidence: `python3 scripts/evidence.py` — `frames`, `latest`, `shots`, `show <png>`,
  `trace <jsonl>`. A 40-turn trace is ~100 KB: parse it with a short python snippet, never cat.
- Wine: prefix `./programs/prefix`, `wine 10.0` bits at `./programs/`, `DISPLAY=:99`, Xvfb
  `:99` 800x600x16, window 800x600 at 0,0. Launch = `m54a_load.relaunch()`. `pgrep -x
  terran.exe` (NEVER `-f` — it matches this session's own shell and kills it).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **The oracle is memory, not the screen.** A dropped keypress and a rejected order look
  identical in OCR. Verify `unit+17`, and after execution `unit+0/+2` and `+40`.
- **The setter writes the order byte LATE** — only after its pane is answered. Session 81's
  `g` attempt recorded `order_after 0` while memory ended up holding `0x18`: re-read the byte
  AFTER the pane service, and do not let 4 pane frames end the attempt early.
- **Panes that classify as something else are key sinks.** The `g` chooser read `hud` (10 keys,
  0 bytes); the scene panel read `movie` (two runs frozen because Escape is gated by
  `--no-escape`); a live chooser frame in `trace_m54d40c` read `unknown` even though the saved
  frames read `dest-chooser` — widen the test when you catch that frame.
- **Escape at a clean HUD raises "Do you really want to quit?"**, and Return there is "Yes,
  that's an order, mister!" — the process is gone.
- **Arrows drive the MAP CURSOR, they do not order a unit.** Only the documented combos in
  ORDERS.md §4 queue anything. Blind map clicks SCROLL the view (drag/scroll path).
- **Mouse motion does not move the cursor.**
- **A faction COMMUNICATION is its own class (`comm`)**: click its own OK bar (y 347), never the
  console row under it.
- **`--load` needs a Windows path** (`Z:\...`), never a `file://` URI.
- **A 40-turn run is 15-25 minutes**: start it backgrounded with a generous `timeout`, then
  poll the state reader or the log's `^turn N:` lines. Do not hold a foreground call open.
- **Attaching mid-round makes turn 0 advance the year by more than 1** (`{3: 1, 1: 39}` in
  `trace_m54d40c`) and the `+1 per record` gate fails on turn 0. Start a run at a turn boundary
  or expect the gate to bite.

## THE 10 RULES — condensed from sessions 75-81

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

1. Patch a `## Session 82` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 83, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
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

One screen: what changed, the acceptance numbers with the command that produced them, what is
open, next pick. No narration of the journey.
