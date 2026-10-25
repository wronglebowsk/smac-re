# NEXT_PROMPT.md — footing for the next session (written at the end of session 80, 2026-10-24)

## THE LEDGER — read this first, it is the whole state of the project

Closed (PRs merged to `main`):
- **M54A — the driver survives a full game unattended** (session 77, PR #39). One invocation
  reached 2416 unattended, the year advanced 1 per record, zero stalls.
- **M54B — 40 turns from a saved position, unattended** (session 79, PR #40).
  `python3 scripts/smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54b40 --load
  Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV --verbose` → `advanced 40/40`, year
  deltas `{1: 40}`, `stuck 0`, max dt 34.4 s, `PASS`, exit 0. Session 79's own run stalled twice
  on the HELP browser and was NOT accepted; the fix (a `help` class + its EXIT bar) is what made
  the accepted run possible.
- **M54C — the unattended loop ORDERS units** (session 80, this PR). Same command, tag
  `m54c40c`, checked with `python3 scripts/m54a_check_run.py
  evidence/trace_m54c40c_20261024_224606.jsonl --timeout 240 --min-orders 5` → `advanced 40/40`,
  year deltas `{1: 40}`, `stuck 0` (max dt 61.8 s), **`orders 31 VERIFIED of 36 attempted`**,
  `48.9 s spent ordering`, `PASS`. `evidence/trace_m54c40c_20261024_224606.jsonl`.

Open:
- **S3's other half — orders that MOVE and FIGHT.** Every verified order M54c could buy in the
  reproducible position is `SENTRY` (byte 1): the position has no class-9 (Former) unit, and `g`
  refuses to queue a MOVE for a unit standing on its own base. Nothing has ever verified an
  `0x18`/`0x19` walk, an `EXEC` execution, or a combat resolution from the driver.
- **S1** (production rebuild: bases, items, units, tech, `0x420440`) and **S2** (win conditions,
  transit, `0x4202d0`) are open in ROADMAP.md and need the census model — bigger than a session.
- **M52** (Paul's 2416 campaign save) is on hold: a save with mid-round bit1 set spins forever
  after load. Session 79's clean-solve is `scripts/m54b_clean_save.py`.

## THE PICK — M54d: a position with class-9 units, and a MOVE that actually walks

Do exactly ONE milestone, then stop. Do not re-verify closed work.

The loop can order; it cannot yet prove a unit MOVED, because the position it can reproduce has
nothing to move. Two candidate positions, pick after you look at them:
1. **The fresh game** (year 2100, `scripts/m54a_newgame.py` starts it): every faction begins with
   Formers, so terraform and MOVE orders are available immediately. Cost: the first turns are
   slow (production panes, no bases) and the driver's HUD path differs.
2. **A save we make ourselves** after some production turns produce a Former (load
   `m54b_clean.SAV`, run N turns with orders, then save the live memory back with
   `scripts/smac_unitpos.py`'s write path or the M54b save tooling). Cost: you must first make the
   game PRODUCE a unit, which is S1 territory.

Acceptance shape (same discipline as M54b/M54c — one invocation, no human, checked by a script):
- a saved position that contains at least one class-9 unit owned by us (print the census line);
- inside one unattended run: order a unit `0x18`/`0x19` (or a terraform byte), verify `unit+17`
  inside the loop, then after `EXEC` verify `unit+0/+2` (x,y) changed to the ordered destination
  and `unit+40` (movement) was spent;
- `advanced N/N`, `stuck 0`, and the check script prints `PASS`;
- pin the new pane(s) you had to learn in `scripts/test_classify.py` and `scripts/check_classes.py`
  with saved frames BEFORE they go into the driver.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — the last three entries (77, 78, 79, 80) are the recent work.
   Never read the whole file (~49 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start <ID>` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — **no game is running** (session 80 ended with the box
   idle). Any `--turns` run relaunches; `--load Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV`
   gives the reproducible 2150 position (6 Scout Patrols, no Formers, 18 bases).

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — the order contract: §2 the `+17` verification oracle (a dropped keypress and a
  rejected order look identical from outside), §4 the byte table, §5 the harness, **§6 the
  in-loop contract added by session 80**.
- `SAVE_FORMAT.md` 155-182 — the 52-byte unit record (`+0/+2` x/y, `+4` flags, `+9` frozen, `+10`
  type, `+14` owner, `+17` order, `+40` mp-used). `NAMED.md` 120-146 — the select gate
  (`0x40c8d0`, `0x5acc00`: owner == current player, not frozen, mp unspent) the picker mirrors.
- `data/alpha.json` — `UNITS` names/classes; the class table is `0x98ADB2` (type*52, class byte at
  +0; class 9 = Former, class 3 = Scout Patrol). `scripts/check_classes.py` prints a census.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md +
  `references/wine-operations.md` (launch, load, the order step, the panes) +
  `references/production-rebuild.md` (M53 census model — only for S1).

## OPERATIONAL KIT

- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--load <Z:\\path>] [--verbose]`. Orders are ON by default: `--orders-per-turn 2`,
  `--order-budget 35`, `--no-orders` to turn them off. Trace →
  `evidence/trace_<tag>_<ts>.jsonl`; the header carries `orders_per_turn`/`order_budget`, each
  turn record carries `orders` (rec/x/y/type/class/key/byte_before/after/energy/seconds) and
  `order_seconds`.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N]` — the ONLY
  thing that can print `PASS`. It reports `advanced`, `stuck`, `pane hits`, `actions`,
  `orders ... VERIFIED of ... attempted`, `order mix`, `energy spent`.
- State: `python3 scripts/smac_state.py --json` (or `--watch`). Reads `/proc/<pid>/mem`; never
  pokes, never clicks.
- Classifier tests: `python3 scripts/test_classify.py` (must end `PASS 11/11 screen
  classifications`) and `python3 scripts/check_classes.py` (must end `frames: 11 failures: 0`).
  Both take `(words, region_colors(png), png)` and run on SAVED frames — no game needed.
- Evidence: `python3 scripts/evidence.py` — `frames`, `latest`, `shots`, `show <png>`,
  `trace <jsonl>`. A 40-turn trace is ~100 KB: parse it with a short python snippet, never cat.
- Wine: prefix `./programs/prefix`, `wine 10.0` at `./programs/wine-extract/wine-master-10.0`,
  `DISPLAY=:99`, Xvfb `:99` 800x600x16. `pgrep`/`pkill -x terran.exe` (NEVER `-f` — it matches
  this session's own shell and kills it).

## TRAPS THAT COST A SESSION HOURS (all measured, all in SESSION_NOTES)

- **The oracle is memory, not the screen.** A keypress that lands and one that is swallowed look
  identical in OCR. Verify `unit+17` (and after execution, `unit+0/+2`).
- **Escape at a clean HUD raises "Do you really want to quit?"**, and Return there is "Yes, that's
  an order, mister!" — the process is gone. Session 80's probe poisoned its own first run this way.
- **The BASE screen swallows the next keypress** (it is a key sink, like a modal): close it with
  Escape before firing an order key.
- **Arrows drive the MAP CURSOR, they do not order a unit.** `Right` opened the base pane;
  `shift+Up` raised a pane. Only the documented Shift+arrow combos in ORDERS.md §4 queue a move.
- **A faction COMMUNICATION is its own class (`comm`)**: banner `X - MOOD`, a QUOTED demand, its
  own OK bar at y 347. The console row at y 560 (DATALINKS 333 / PROFILE 467 / HQINFO 619) is
  still drawn under it and is NOT a close bar — clicking it 38 times burned 735 s of turn 35 in
  `evidence/trace_m54c40b_20261024_222039.jsonl`.
- **The help browser ignores Escape**; click its EXIT bar (rightmost of the BACK/EXIT row).
- **The game's own dialogs are modal for the game too**: while one is up, keypresses go into its
  bar list, not the map. Service panes before firing keys, and never fire an order key while a
  pane you opened is still up.
- **`--load` needs a Windows path** (`Z:\...`), never a `file://` URI — Wine resolves URIs against
  the prefix and the load fails silently.
- **A 40-turn run is 15-25 minutes**: start it backgrounded with a generous `timeout`, then poll
  the state reader or the log's `^turn N:` lines. Do not hold a foreground call open on it.

## THE 10 RULES — condensed from sessions 75-80 (see the entries for the incidents)

1. One milestone per session, then stop. Do not re-verify closed milestones.
2. Commit early (a commit on the branch is the only thing that survives an overflow), then
   checkpoint-commit every few hundred lines.
3. Patch docs; never read-then-write a doc over 10 KB.
4. Keep tool results small: grep/sed windows, `evidence.py show`, tail. Never cat a log.
5. New screen classes go into `test_classify.py` AND `check_classes.py` with saved frames BEFORE
   they go into the driver.
6. Acceptance is a script printing `PASS` on one real invocation. Never weaken a gate to make a
   run pass; if a run stalls, find the pane and pin it.
7. Verify state by reading memory (`smac_state.py`, `/proc/pid/mem`), never by trusting a
   screenshot, and never by assuming a keypress landed.
8. Before `git add -A`, sync `skill/` from the live skill
   (`~/.hermes/skills/smac-cvr-format/` → repo `skill/`) and commit it in the same commit as the
   docs. `gate.py` does not check the sync; a stale `skill/` is a silent failure.
9. `gate.py`'s checkpoint check needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated, and
   every `path:NNN` citation you add must resolve. `gate.py` refuses `main`; submit/merge refuse a
   dirty tree — commit FIRST, then gate, then submit.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
    produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session 81` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 82, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
3. `git add -A && git commit -m '<ID>: checkpoint'`
4. `python3 scripts/gate.py --base main` (must be GREEN)
5. `python3 scripts/milestone.py submit --title "..."` → note the PR number →
   `gh pr checks <n>` → `python3 scripts/milestone.py merge <n>`
Then STOP and report.

## IF YOU HIT "request exceeds the context window"

In your very next tool call run `git add -A && git commit -m '<ID>: checkpoint'`, then reply with
what is done and what is not. Do not try to compress and do not rewrite docs to recover — that is
what killed sessions 78 and 79.

## Never

- commit to `main`; `Escape` on the title screen (it exits); `pkill -f`/`pgrep|kill` by name
  (matches this shell); click OK on "Do you really want to quit?"; `--mode stop` (does not exist);
  `file://` with `--load`; a `clear`-prefixed command (gate refuses it); a `MEDIA:` line in your
  report unless you actually attached a file.

## Report style (what a finished session looks like)

One screen: what changed, the acceptance numbers with the command that produced them, what is
open, next pick. No narration of the journey.
