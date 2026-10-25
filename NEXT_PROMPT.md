# NEXT_PROMPT.md — footing for the next session (written at the end of session 84, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A — the driver survives a full game unattended** (sessions 77-78, PR #39).
- **M54B — 40 turns from a saved position, unattended** (session 79, PR #40);
  `scripts/m54b_clean_save.py` makes a resumable save from a hung autosave.
- **M54C — the unattended loop ORDERS units** (session 80, PR #41): `orders 31 VERIFIED of 36`.
- **M54D — the loop queues a MOVE and checks it in memory** (session 81, merged #43): `g` lands
  `0x18`, the record carries the leg-array route, the `dest-chooser`/`artwork-close` panes pinned.
- **M54E — THE ORDERED WALK LANDS INSIDE THE UNATTENDED RUN** (session 82, PR #44): `moves 5
  LANDED of 5 ordered walks`; mechanism in `ORDERS.md §7` (the pump runs `0x18` as the chooser's
  OK is answered; the walker must START on a real neighbour). That run lost the position.
- **M54F — the type byte is settled (+10, from the binary) and the checker can see a defeat**
  (session 83): `--min-our-bases` fails a run that loses the position, fail-closed.
- **M54G — THE FOUNDING IS KEYED AND THE LOOP FOUNDED A BASE** (session 84): `b` (BUILD BASE)
  reaches the dispatcher ONLY with **orders mode on** (`0x91b5b8 != 0`; with it off `b` is a
  map-level key that opens the base screen); `FUN_004d1280` gates **class 8** then the tile; on
  a legal tile it raises **#NEWBASE**, which classifies `hud` (new `name-pane` class, tests
  16/16), and **Return accepts the generated name — the base record exists 0.1 s later**. The
  founding writes **no order byte** and **consumes the unit**; its oracle is the base array.
  One unattended run (`smac_play.py --turns 6 --timeout 240 --no-escape 3000 --tag m54g
  --verbose` -> `evidence/trace_m54g_20261025_084554.jsonl`) founded **"Korolev Center"** at
  (29,42): `advanced 6/6`, `{1: 6}`, `stuck 0`, `orders 11 VERIFIED` mix
  `{"b->founded": 1, "l->byte1": 10}`, `bases_ours 1 -> 2`, `PASS` under
  `m54a_check_run.py ... --min-our-bases 2`. Mechanism: `ORDERS.md §8`.
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold: a save with mid-round bit1 set spins after load.

## THE PICK — M54h: a destination the loop REACHED, not one it was poked onto

Do exactly ONE milestone, then stop. Do not re-verify closed work (M54a-g — the ledger).
Do not open FOOTING.md wholesale: the 52-byte layout is settled (type u16@+10, flags dword@+4,
owner@+14, order@+17, legs@+20..+35, mp@+40).

Why: M54g proved the founding but the unit was **poked** onto its founding tile (a garrisoned
unit cannot be ordered off its own base on this build: `g` refuses it and Shift+arrow queued
nothing — `scratch/m54g_walk.py`, `+17` stayed 0). We now own **two base tiles**, University
Base (28,42) and Korolev Center (29,42), with actionable units on each, so `g` can name a
destination that is not the tile the unit is standing on.

1. **Does `g` still refuse a unit standing on AN own base when a DIFFERENT own base exists?**
   Test on rec60 or rec67 (at (29,42), `order 0 mp 0`): press `g`, read `+17`/legs THROUGH the
   chooser OK (`order_byte_watcher`), then the record. The chooser is `dest-chooser` (pinned).
   If it lists only the unit's own base (M54d measured "Distance: 0" = the CURSOR's distance),
   find the pane's list-selection path: click the OTHER base's row, then OK. One click at a
   time, read `+20/+28` (the ordered destination) after each.
2. **Land the walk inside one unattended run** and prove it the M54e way: the record sits on
   the leg it named with `+40` spent (`--min-moves 1`), year deltas `{1: N}`, `stuck 0`.
3. **Only then** attempt a THIRD founding with no position poke: a class-8 unit that WALKED to
   its founding tile. If the type-poked record will not walk (the pump may follow the poked
   type's movement), report that — it is a real finding, not a nuisance.

Acceptance (one invocation, no human, checked by a script):
* `m54a_check_run.py <trace> --timeout 240 --min-our-bases 2 --min-moves 1` prints `PASS` with
  `advanced N/N`, `{1: N}`, `stuck 0`, and a `b->founded` or `g->byte24` line in the mix;
* the destination is named by the game (a base record we own that the unit was NOT standing
  on), not by a poke — say which;
* any new pane goes into `scripts/test_classify.py` AND `scripts/check_classes.py` with saved
  frames BEFORE the driver uses it.

**If the chooser cannot name the other base, report the negative** (what it lists, what
`+17`/legs did after each click) and merge the notes; do not manufacture a walk.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 83 and 84 are the recent work. Never read the whole
   file (~75 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start <ID>` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 84 left the game LIVE at **2156**, pid
   914329, `bases_ours 2`, `units_ours 7`: five Scout Patrols at (28,42) carrying `order 1`
   (SENTRY, from the loop) and **two fresh Scouts at Korolev Center (29,42), `order 0 mp 0`** —
   those two are the M54h subjects. `turn_flags 2` latches after any driver run and does NOT
   clear on TURN COMPLETE; a reload clears it. It is not a wedge — turns still flip.
   If the state reads impossibly: `SMAC_SAVE='Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV'
   python3 scripts/m54a_load.py --relaunch` (~38 s to a live HUD) — but that save PREDATES
   Korolev Center, and rebuilding it costs `m54g_prep.py` + one run turn, so reload only if the
   state is truly unreadable.
5. `python3 scripts/m54d_census.py` — where our records and both bases are, right now.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing, §2 terraform family, §4 the byte table (`0x18` queued MOVE,
  legs `+20..+27` x / `+28..+35` y, last leg = destination), §6 the in-loop contract, §7 WHEN
  the queued MOVE runs (the chooser's OK is the trigger; tens-of-ms byte window; arrows queue
  nothing), **§8 THE FOUNDING: `b` needs orders mode on, gates class 8 + tile, raises NEWBASE,
  Return founds, no order byte, consumes the unit, `founding_gate()` mirrors the tile gates**.
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record and the 304-byte base record
  (`x@0, y@2`, faction = LOW byte at `+4`, **name at `+19..51`**, count `0x985AF4`).
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**: type 0 =
  Colony Pod (class 8), type 1 = Formers (class 9), type 2 = Scout Patrol (class 3). Class
  table `0x98ADB2[type*52] & 0xff`.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md` (now carries the
  founding, the tile-pointer/pitch fact and the memory-first rule).

## OPERATIONAL KIT

- Census / position: `m54d_census.py [--json f]`; `m54g_prep.py` (poke one record: `+10`->0
  class 8, x/y onto the nearest tile `founding_gate` calls LEGAL, `+17`->0, all read back);
  `m54e_prep.py` (older: empty our base tile, walker to `bx-2`); `m54d_probe.py --unit N`
  (one key at a time, `+17`/legs/x,y/`+40` + screen class); `m54g_probe.py --unit N
  [--orders-mode 1] [--poke-type T] [--poke-x X --poke-y Y] [--clear-order]` — STAGED,
  memory-first (see traps); `m54e_probe.py chooser N`.
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--load <Z:\\path>] [--verbose]`. Orders ON by default (`--orders-per-turn 2`,
  `--order-budget 35`). Each turn record carries `orders` (with `dest`), `moves`,
  `moves_verified`, and — when a founding fires — `founds`
  (`bases_before/after`, `base_at`, `gate_reasons`, `panes`, `answered`). The founding fires
  once per run (`FOUND_DONE`), at most `FOUND_TRIES[0]` keypresses, BEFORE the move plan, and
  the turn's order step returns as soon as it lands (the record list compacts under the index).
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N]
  [--min-moves M] [--min-our-bases N]` — the ONLY thing that can print `PASS`; floors fail
  CLOSED (a trace without the fields fails).
- State: `python3 scripts/smac_state.py --json` (or `--watch`) — reads `/proc/<pid>/mem`,
  never pokes; prints `bases_ours`/`units_ours` (unit records counted only when `type < 24`
  and x/y in range).
- Classifier tests: `python3 scripts/test_classify.py` (must end `PASS 16/16 screen
  classifications`) and `python3 scripts/check_classes.py` (must end `frames: 16 failures: 0`).
  `check_classes.py` OCRs at 3x and leaves `_3x.png` siblings: **delete `evidence/**/_3x.png`
  right after**. `evidence/` is at ~29.4 MB of a 30 MB FAIL budget — check
  `python3 scripts/evidence.py budget` BEFORE adding any frame.
- Evidence: `scripts/evidence.py` — `frames`, `latest`, `shots`, `show <png>`, `trace <jsonl>`,
  `budget`, `prune --dry-run`. A 6-turn trace is ~55 KB; parse with a short python snippet.
- Wine: prefix `./programs/prefix`, `wine 10.0` bits at `./programs/`, `DISPLAY=:99`, Xvfb
  `:99` 800x600x16, window at 0,0. Launch = `m54a_load.relaunch()`. `pgrep -x terran.exe`
  (NEVER `-f` — it matches this shell and kills it).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **OCR is ~15 s a poll here.** A pane-servicing loop paced on OCR spams keys at what it thinks
  is a clean HUD — and `Return` at a HUD is TURN COMPLETE (session 84's first probe advanced
  the year by itself). **Poll the oracle at 100 ms (base array, `+17`) and OCR only when memory
  has not answered.**
- **A clean HUD sometimes classifies `unknown`** (news-pane text). Do not service `unknown`
  with keys in a probe; widen the test when a live frame reads `unknown`.
- **`b` (and every order letter) is a MAP-level key while orders mode is off** (`0x91b5b8 ==
  0`): it opens the base screen near the cursor and the dispatcher never sees it. The loop's
  `issue_found_for_unit` reads the global and pokes it on only if 0.
- **The tile array is behind a POINTER and the pitch is LIVE**: `*(u32*)0x92ae14 +
  (DAT_00692184*y + x>>1)*0x2c`; DAT_00692184 = 32 on this 64x64 world (40 was an 80-wide map).
  `tile_recs()` now derefs; anything that indexed `0x92ae14` itself read pointer slots.
- **The founding consumes the unit and writes no order byte**: record indices are NOT ids (the
  list compacts). Verify the base array, not `+17`.
- **The `g` chooser's OK stores the byte and the pump eats it a tick later** — tens of ms, so
  ONE read after the click is a coin flip; sample THROUGH the click (`order_byte_watcher`).
  `order_final 0` after EXEC proves nothing (a hand-parked `0x18` survived three TURN COMPLETEs).
- **A walk needs the walker to START on a real neighbour** of the named tile (delta tables
  `0x67850c` dx / `0x678990` dy; `(bx+1, by)` is a half-tile offset, not a neighbour).
  **Occupancy is NOT a blocker** — units stack on a destination tile (retracted session 83).
- **Panes that classify as something else are key sinks**: the `g` chooser once read `hud`; the
  scene panel read `movie`; NEWBASE reads `hud` (now `name-pane`). Widen the test first.
- **Escape at a clean HUD raises "Do you really want to quit?"**; Return there ends the process.
- **Arrows drive the MAP CURSOR, they do not order a unit**; `space` neither queues nor pumps.
  Blind map clicks SCROLL the view. Mouse motion does not move the cursor.
- **A faction COMMUNICATION is its own class (`comm`)**: click its own OK bar (y 347).
- **`--load` needs a Windows path** (`Z:\...`), never a `file://` URI.
- **A 40-turn run is 15-25 minutes; a 6-turn run ~3 minutes**: background it with a generous
  `timeout` and poll the log's `^turn N:` lines. Do not hold a foreground call open.
- **Attaching mid-round makes turn 0 advance the year by more than 1** — start at a turn
  boundary or expect the `{1: N}` gate to bite.

## THE 10 RULES — condensed from sessions 75-84

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
   (`~/.hermes/skills/smac-cvr-format/` -> repo `skill/`) and commit it in the same commit.
9. `gate.py`'s checkpoint check needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated, and
   every `path:NNN` citation you add must resolve. `gate.py` refuses `main`; submit/merge refuse
   a dirty tree — commit FIRST, then gate, then submit.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
    produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session 85` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 86, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`
4. `git add -A && git commit -m '<ID>: checkpoint'`
5. `python3 scripts/gate.py --base main` (must be GREEN)
6. `python3 scripts/milestone.py submit --title "..."` -> note the PR number ->
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
  a commit message (the shell eats them); a `MEDIA:` line in your report unless you actually
  attached a file; `skill_manage delete` (it has wiped a skill twice).

## Report style (what a finished session looks like)

One screen: what changed, the acceptance numbers WITH the command that produced them, what is
open, next pick. No narration.
