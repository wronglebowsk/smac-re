# NEXT_PROMPT.md — footing for the next session (written at the end of session 85, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A — the driver survives a full game unattended** (sessions 77-78, PR #39).
- **M54B — 40 turns from a saved position, unattended** (session 79, PR #40).
- **M54C — the unattended loop ORDERS units** (session 80, PR #41).
- **M54D — the loop queues a MOVE and checks it in memory** (session 81, PR #43).
- **M54E — the ordered WALK lands inside an unattended run** (session 82, PR #44): `moves 5
  LANDED of 5`. Mechanism `ORDERS.md` §7: the pump runs `0x18` as the chooser's OK is answered.
- **M54F — the type byte is settled and the checker can see a defeat** (session 83, PR #47ish).
- **M54G — the founding is keyed and the loop FOUNDED a base** (session 84, PR #48): `b` with
  orders mode ON, class 8 + legal tile, `#NEWBASE` (`name-pane` class), Return founds, no order
  byte, the unit is consumed, oracle = the base array. Live: "Korolev Center" at (29,42),
  `bases_ours 1 -> 2`, `PASS` under `--min-our-bases 2`. Mechanism `ORDERS.md` §8.
- **Session 85 (M54h, merged as notes + fixes, MILESTONE STILL OPEN).** See "THE RETRACTIONS".
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold.

## THE RETRACTIONS session 85 wrote into `ORDERS.md` §9 — do not re-learn them the hard way

1. **`g` does NOT refuse a unit garrisoned on our own base** (M54c said it does; its evidence
   was a one-base position). With two own bases the chooser draws TWO rows: full-width periwinkle
   bars at y 125-139 and 144-158 (19 px pitch), fill 159..638, and its five-button row
   (Sort: Name / Sort: Size / Sort: Dist / OK / CANCEL at 209/305/401/497/593) sits at **y 181
   with two rows, y 162 with one** — any hard-coded OK row is a coin flip on a two-row pane.
   `bar_bands()` / `chooser_rows()` / `chooser_buttons()` in `smac_play.py` derive both (a row
   band's groups merge to a ~480 px span; a button band is >=4 groups of one width on one pitch
   — the merged span alone cannot tell them apart: five buttons span 163..638 like a row).
2. **A row click is a selection, not an order** (`+17` and legs unchanged 0.9 s after it). OK is
   what lands it: `+17` 0 -> 0x18 87 ms after the click, legs `[28,42]`, pump stepped the unit
   (29,42) -> (28,43) with `+40` = 3 spent (`evidence/m54h/probe_chooser_walk1.json`). CANCEL
   (5th button) closes the pane and writes NOTHING (`probe_chooser_cancel67.json`).
3. **The `Distance:` column is the CURSOR's, not the unit's — it read 0 for BOTH rows.** Useless
   for choosing. Whether the row order is Sort: Name or nearest-first is **unmeasured** (both
   frames so far fit either); the driver text-matches the row to the base name first and falls
   back to the alphabetical mapping.
4. **Record INDEX is not identity, and the array GROWS mid-run**: `units_ours 9 -> 10` inside
   the 6-turn run (University Base builds Scout Patrols) and the ordered unit was index 67 at
   order time and index 52 one turn later. Snapshot-and-diff, never carry an index across a turn.
5. **A clean HUD can classify `unknown`** because 2x OCR cannot read the TURN COMPLETE row
   (MENU read at (61,369), COMMLINK read, `region_colors 167`). With `--no-escape` the loop idled
   a WHOLE turn budget at it (521 s, year unmoved, our phase). Fallback now in `service_turn`:
   our phase + chrome present + no bar band at y 145-200 + `HUD_BLIND_S` (25 s) elapsed -> click
   the button at its measured coordinates. Proven: `trace_m54h2_20261025_094339` turn 0
   `2160 -> 2161 OK (36.7s)`.
6. **An advisor dialog wearing HUD chrome classifies `hud`**: the OPERATIONS DIRECTOR
   "Investigate pod beacon?" pane ate a whole turn of TURN COMPLETE clicks landing BEHIND it
   (`trace_m54h3`). `modal_caption(words)` (one word >=6 chars, or >=2 words >=4 chars, at
   y 90-118) now answers such a frame with Return before anything else in the `hud` branch.
   Next run cleared it in one press and all 6 turns advanced.
7. `turn_flags` bit `0x2` cleared by itself when a BREAKTHROUGH panel + its dialog were dismissed
   (Escape, then Return) — it is not only the "a driver ran here" latch session 84 described.

## THE PICK — M54i: make a walk's DESTINATION attributable to the ORDER

Do exactly ONE milestone, then stop. Do not re-verify closed work.

Session 85 proved the chooser can name a base the unit is NOT standing on, and that OK on that
row queues 0x18 with legs naming the base — **in a probe**. In the LOOP it did not reproduce:
three `g` orders whose row click the trace records against the University Base row put legs
naming (14,56) = House of Martyrs (a Believer base), (17,55) (not a base) and (12,14) = Gaia's
Landing into the record — never (28,42) — and `moves 0 LANDED of 3 ordered walks`. The leading
suspect is #4 above: the legs were read 0.35 s after the OK from ONE index, and the array
reshuffles (a base was building units during that very run).

1. **Diff, don't index.** In `issue_order_for_unit`, snapshot EVERY record we own (type, x, y,
   +17, legs) before the keypress; after the OK, find the record whose `+17` became 0x18 and
   whose legs CHANGED, and take the destination from THAT record. Report the number of records
   that changed — if two changed, the run is confounded and must say so.
2. **Land one.** One unattended run, `m54a_check_run.py <trace> --timeout 240 --min-our-bases 2
   --min-moves 1` printing `PASS` with `advanced 6/6`, year deltas `{1: 6}`, `stuck 0`, a
   `g->byte24` line in the mix, and a `landed` move whose `dest` equals a base WE own and is
   NOT the tile the unit started on. `verify_moves` already requires the count delta
   (`order_counts`: same-type count UP at the destination, DOWN at the origin) and
   `PENDING_WALKS` re-reads an unfinished walk on later turns — use them, do not weaken them.
3. **Only then** the walk-then-found sequence (a class-8 unit that WALKED to its founding tile).

**If it still will not land, report the negative with the record diff** (what changed, what each
changed record's legs say) and merge the notes. Do not manufacture a walk.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 84 and 85 are the recent work. Never read the whole
   file (~78 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start M54i` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 85 left the game LIVE at **2167**, pid
   914329, `bases_ours 2`, `units_ours 10`, `turn_flags 2`. `scripts/m54d_census.py` last saw:
   five records at (28,42) with `order 1`, two parked decoys (rec36 (28,43), rec39 (29,42),
   `order 1` — parked by POKING `+17 = 1` so exactly one walk is in flight; they are not
   actionable), rec47 (28,43), **two live 0x18 orders** (rec49 at (29,43) legs (29,42); rec57 at
   (29,42) legs (28,42)) that the next pump will keep walking, and one new unit built by the
   base. Indices have already moved once since that census — re-read it, do not trust these.
   If the state reads impossibly: `SMAC_SAVE='Z:\\home\\n100\\reverse\\smac\\programs\\saves\\m54b_clean.SAV'
   python3 scripts/m54a_load.py --relaunch` — but that save PREDATES Korolev Center (one base),
   so rebuilding the two-base position costs `m54g_prep.py` + a run turn. Reload only if the
   state is truly unreadable.
5. `python3 scripts/m54d_census.py` — where our records and both bases are, right now.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing, §4 the byte table (`0x18` queued MOVE, legs `+20..+27` x /
  `+28..+35` y), §6 the in-loop contract, §7 WHEN the queued MOVE runs, §8 THE FOUNDING,
  **§9 THE CHOOSER'S ROWS + what a walk's evidence has to be + what is UNRESOLVED**.
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record (type u16@+10, flags dword@+4, owner@+14,
  order@+17, legs@+20..+35, mp@+40) and the 304-byte base record (x@0, y@2, faction = LOW byte
  at +4, name at +19..51, count `0x985AF4`).
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**; class table
  `0x98ADB2[type*52] & 0xff`. Class 8 = colonist (founding), class 3 = Scout Patrol here.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md`.

## OPERATIONAL KIT

- Census / position: `m54d_census.py [--json]`; `m54h_probe.py peek|legs|chooser N [--row K]
  [--ok] [--cancel] [--tag T] [--save-frame]` — staged chooser probe, memory-first, writes
  `evidence/m54h/probe_*.json`; `scratch/m54h_clear.py [N]` — Escape/Return a stack of panes away
  until the HUD reads clean; `m54g_prep.py`, `m54d_probe.py --unit N`, `m54g_probe.py --unit N`.
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--load <Z:\\path>] [--verbose]`. Each turn record carries `orders` (with `dest`,
  `chooser_pick`, `order_counts`), `moves` (with `dest_count`/`src_count`, `carried`),
  `moves_verified`, `founds`. A 6-turn run is 3-8 minutes: background it, poll `^turn N:` lines.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N]
  [--min-moves M] [--min-our-bases N]` — the ONLY thing that can print `PASS`; floors fail CLOSED.
- Classifier gates: `scripts/test_classify.py` must end `PASS 17/17 screen classifications` (was
  16/16 — session 85 added the two-row chooser, `evidence/m54h/chooser_g60b.png`) and
  `scripts/check_classes.py` must end `frames: 17 failures: 0`. `check_classes.py` leaves
  `_3x.png` siblings: **delete `evidence/**/_3x.png` right after**. `evidence/` is at
  **~28.9 MB of a 30 MB FAIL budget** — check `python3 scripts/evidence.py budget` BEFORE adding
  any frame, and gzip an uncited big text file if you need room.
- Wine: prefix `./programs/prefix`, `wine 10.0` at `./programs/`, `DISPLAY=:99`, Xvfb :99
  800x600x16, window at 0,0. Launch = `m54a_load.relaunch()`. `pgrep -x terran.exe` (NEVER `-f`).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **OCR is ~1-15 s a poll here and it LIES about legibility**: the same chooser frame read
  "University Base" on one capture and nothing on the next; a clean HUD reads `unknown` when the
  TURN COMPLETE row fails to OCR. Poll the oracle at 100 ms (records, base array) and OCR only
  when memory has not answered.
- **Index identity is a lie across a turn** (the array reshuffles and GROWS — a base building a
  unit shifts every index after it). Snapshot and diff.
- **Attaching mid-round makes turn 0 advance the year by 3** (`trace_m54h...093424` turn 0:
  2156 -> 2159) and the checker fails `{1: N}`. Attach right after a year flip, or burn one turn
  first and start the acceptance run after it.
- **The box can be parked on a BREAKTHROUGH panel / advisor dialog when you attach** — run
  `scratch/m54h_clear.py` before ordering anything.
- **Panes that classify as something else are key sinks** (chooser -> `hud`, scene panel ->
  `movie`, NEWBASE -> `hud`, advisor dialog -> `hud`). Widen the test first: new classes/frames
  go into `test_classify.py` AND `check_classes.py` with saved frames BEFORE the driver uses them.
- **The chooser's OK stores the byte and the pump eats it tens of ms later** — sample THROUGH the
  click (`order_byte_watcher`); one read after the click is a coin flip.
- **A walk needs the walker to START on a real neighbour** of the named tile (delta tables
  `0x67850c` dx / `0x678990` dy); occupancy is NOT a blocker (units stack).
- **`b` (and every order letter) is a MAP-level key while orders mode is off** (`0x91b5b8 == 0`).
- **The tile array is behind a POINTER and the pitch is LIVE**: `*(u32*)0x92ae14 +
  (DAT_00692184*y + x>>1)*0x2c`, pitch 32 on this 64x64 world.
- **Escape at a clean HUD raises "Do you really want to quit?"**; Return there ends the process;
  Escape on the title screen exits. Never click its OK.
- Arrows drive the MAP CURSOR, they do not order a unit; `space` neither queues nor pumps; blind
  map clicks SCROLL; mouse motion does not move the cursor. `--load` needs a Windows path.

## THE 10 RULES — condensed from sessions 75-85

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

1. Patch a `## Session 86` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 87, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
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
