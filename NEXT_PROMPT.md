# NEXT_PROMPT.md — footing for the next session (written at the end of session 90, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A–M54E** — the driver survives a full game / 40 saved turns / ORDERS / queues a MOVE /
  the ordered WALK lands (sessions 77-82, PRs #39-#44).
- **M54F** type byte settled + checker sees defeat (#47). **M54G** founding keyed + loop FOUNDED
  (#48). **M54h** chooser geometry (#49). **M54i** attribution by record DIFF (#50).
- **M54i2** a loop-ordered walk landed on our own base (#51-ish; sessions 87). **M54j** a
  MULTI-LEG walk landed across TURN COMPLETEs (#88). **M54k** the PRE_ARM hook path,
  DOCUMENTED NEGATIVE (#89).
- **M54k2 — THE HOOK-SHAPE RUN PRINTED PASS** (session 90): setup read back `actionable: []`,
  `pre-arm:rec12` armed the walker at (35,36), the loop's `g` verified 0->24 (rescan path),
  the watcher read the walk (35,36)->(34,37)->(33,38)->(32,39)->(30,39)->(30,41)->**(29,42)**
  byte 24 the whole way, ordered turn 1 LANDED turn 5, `bases_ours 2` at 2204, year deltas
  {1:6}. PR number in `git log`. **The walking arc (M54i2 -> M54k2) is CLOSED.**
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (ROADMAP line 86: the SOLO TURN
  ADVANCE heartbeat — TURN COMPLETE -> upkeep -> production -> research -> AI -> events -> next
  player; the footing used to call S2 "win conditions, transit" — the ROADMAP row is the
  authority, read it before committing). **M52** (Paul's 2416 campaign save) on hold.

## WHAT SESSION 90 ESTABLISHED — do not re-learn these the hard way

1. **The pump can execute a queued MOVE entirely INSIDE our phase**: after the chooser OK,
   `turn_flags & 2` stays set with `cur_player` OURS and the year flips every ~4.6 s while the
   unit steps (run1: the whole 4-step route inside ONE turn record, deltas {1:5, 5:1}). Each
   flip COMPACTS THE ARRAY, so `UNIT_ARR + idx*52 + 17` (the slot oracle) reads a DIFFERENT
   record mid-burst. `queued_rescan` (`scripts/smac_play.py`, ORDERS §14) reads the queue off
   CONTENT: exactly ONE of our records newly wearing a wanted byte, NONE wearing it in the
   pre-press snapshot, last leg naming OUR base. Queue-time legs name the DESTINATION;
   mid-walk rewrites name waypoint garbage ((61,9), (61,10)) — a waypoint is not evidence.
   Wired into `_issue_order_once` after the blind Return; tests 34-37.
2. **After the turn's order is spent and nothing is actionable the game AUTO-ADVANCES ~8
   s/round — and can flip TWO rounds inside one slow OCR iteration** (run2 turn 5: {1:5, 2:1},
   checker `FAIL year did not move +1 on turns [5]`). Both order-step exits now poll
   `year() != y0` at 0.2 s (20 s cap) before continuing; the turn closes on the flip. run3:
   {1:6}. Cheap memory polls beat OCR iterations — the general heartbeat lesson.
3. **`turn_flags` gained a persistent 0x100000 bit around 2196** (1048578 = 0x100002 at 2204).
   The driver's `tf & 2` gates are unaffected (run3 passed with it set). Nobody knows what sets
   it; an S2 inventory should find out. Do not treat it as nonsense state.
4. **Screen every walker target with `scratch/m54k2_scan.py <rootx> <rooty> <maxBFS>
   <minEnemyDist>`** — live step-table BFS + the tile flag byte (+3 even x / +7 odd x, bit 0x40
   impassable) + occupancy + Chebyshev enemy distance + parity. The quiet window around the
   bases closes FAST: best enemy distance near Korolev fell 13 (2191) -> 9 (2198). Targets used:
   (34,37) run1, (36,39) run2, (35,36) run3 (a tile session 89's run6 walker crossed).
5. **The acceptance command, unchanged, is the ONLY thing that prints PASS**:
   `python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-our-bases 2 --min-moves 1
   --min-own-base-arrivals 1` — an own-base arrival must be MULTI-TURN (`ordered_turn < landing
   turn`), year deltas must be {1: N}. Never weaken a floor; strengthening gates is allowed.
6. Session 89's facts still hold: impassable-flag geometry, `g` auto-targets the
   alphabetically-first own base (odd-parity starts only), comm-in-order-window is a key sink
   (byte 88), produced garrisons steal the order tiebreak, the reload recipe
   (`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` — BARE filename —
   then `m54g_prep.py` + a founding turn) works first try.

## THE PICK — M55: S2 begins — INVENTORY THE ROUND BOUNDARY FROM MEMORY

Do exactly ONE milestone, then stop. Do not re-verify closed work.

S2 (ROADMAP line 86) is the game's heartbeat. Session 90 measured its outer shell (auto-advance
cadence, the pump burst, the 0x100000 bit, production dropping `+17 = 0` units on base tiles at
every round boundary). The milestone: **read one round boundary END TO END from memory** —
before/after samples around one flip while everything is HELD — and account for what moved:
newly produced records (which bases, which type), the upkeep deltas (energy is already sampled
per order: `energy_before/after` in the trace — find the research/production analogue in
memory), which `turn_flags` bits flip (including the 0x100000 one — does it survive a reload?
does founding set it?), and where research progress lives (ghidra hunt: the research spend
setter; correlate with a live read). Acceptance: a NEW script (e.g. `scripts/m55_boundary.py`)
printing `PASS` on ONE real invocation, with honest floors (it must FAIL on a hand-typed
fixture — prove that too in the trace/notes). A documented negative may merge (sessions 86, 89)
if the reads are complete and the conclusion is memory-verified.

Shape: the box is at **~2204, `bases_ours 2`, units_ours 11, n_bases 28, enemies within 9 tiles
of Korolev** — the war may take a base before you start: census FIRST; if a base is gone, reload
(item 6 recipe) and re-found before measuring. With everything HELD the game advances itself —
`scratch/m54k_watch.py` + a before/after `our_rows` + `smac_state` diff around a flip is the
instrument; add the energy/research pointers as you find them. Keep the driver OUT of it unless
you need a founding; the boundary needs no input.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 89 and 90 are the recent work. Never read the whole
   file (~80 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start M55` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 90 left the game LIVE near **2204**, pid
   1329211, `bases_ours 2`, `turn_flags 1048578`. If it reads impossibly, or a base is gone:
   reload per item 6 above (bare filename!).
5. `python3 scripts/m54d_census.py` — where our records and both bases are RIGHT NOW.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each; line 86 is S2. Read the row.
- `ORDERS.md` §1 key routing, §4 the byte table (0x18 queued MOVE, legs +20..+27 x / +28..+35 y
  — a WAYPOINT the pump rewrites; QUEUE-TIME legs name the destination), §5 modal = key sink,
  §6 the in-loop contract, §7 WHEN the queued MOVE runs, §8 THE FOUNDING, §9 the chooser's rows,
  §10 SENTRY/HOLD + attribution rules, §11 WHO OWNS THE CURSOR, §12 THE STEP TABLE AND PARITY,
  §13 THE AUTO-SENTRY + reactivation contract + opposite-parity bases, **§14 THE IN-PHASE PUMP
  BURST + queued_rescan + the year-poll + the 0x100000 bit**.
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record (type u16@+10, owner@+14, order@+17,
  legs@+20..+35, mp-used@+40, flag dword@+4) and the 304-byte base record (x@0, y@2, faction
  LOW byte at +4).
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**; class 8 =
  colonist (founding), class 3 = Scout Patrol.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md` (now incl. M54k2).

## OPERATIONAL KIT

- Census / prep: `m54d_census.py`; `scratch/m54k2_scan.py` (target screening); `scratch/
  m54k_setup.py [fx fy tx ty]` (all-held prep + read-back); `scratch/m54k_watch.py [secs x y]`
  (0.5 s memory diff watcher); `scratch/m54h_clear.py [N]` (careful: garbled HUD OCR classifies
  `unknown` and the loop Escapes anyway — it raised the quit prompt in session 90; peek with
  `sp.WIN = sp.find_window()` + freeze/classify instead); `m54g_prep.py`; `m54a_load.py
  --relaunch` (SMAC_SAVE env = the BARE filename).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000
  --orders-per-turn 1 --verbose --tag <t>`. Turn records carry `orders` (with `dest`,
  `chooser_pick`, `walk_diff {attributed, confounded, claim, rivals, n_samples, before_legs}` —
  **n_samples 0 = the rescan verified it**, `order_counts`, `attempts[].panes`) and `moves`
  (with `landed`, `carried`, `ordered_turn`, `dest_is_own_base`, `dest_count`/`src_count`,
  `mp_after`). A 6-turn run is ~1.5-3 min: background it, poll `grep -c '"turn"'` on the trace.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N] [--min-moves
  M] [--min-our-bases N] [--min-own-base-arrivals K]` — the ONLY thing that prints `PASS`.
- Tests: `python3 scripts/test_walk_diff.py` -> `PASS 37/37 attribution cases`. Classifier
  gates: `scripts/test_classify.py` -> `PASS 17/17`; `scripts/check_classes.py` -> `frames: 17
  failures: 0`; **delete `evidence/**/_3x.png` right after**. `evidence/` is ~29.4/30 MB —
  check `python3 scripts/evidence.py budget` BEFORE adding frames; the sanctioned big artifact
  is `m53j_text.txt.gz` (keep; it is cited).
- Wine: prefix `./programs/prefix` == `~/.wine-smac32`, wine 10.20-staging-tkg at
  `~/tools/wine-10.20-staging-tkg-x86/bin/wine`, `DISPLAY=:99`, Xvfb :99 800x600x16.
  `pgrep -x terran.exe` (NEVER -f). Kill a driver run by the PID read from /proc cmdlines.

## TRAPS THAT COST A SESSION HOURS (all measured)

- **The slot oracle goes stale during a pump burst** (item 1): read WHO wears the byte, not who
  sits at `idx`. Waypoint garbage in legs ((61,9)/(61,10)) is not a destination.
- **An all-HELD position auto-advances ~8 s/round and can double-flip inside one slow OCR
  iteration** (item 2): poll `year()` from memory at 0.2 s when you need a boundary.
- **Check the flag byte before parking a unit anywhere** (§89 item 1): impassable tiles swallow
  units whole. Check parity sums mechanically (opposite-parity bases: every tile matches one).
- **`g` targets Korolev Center first** (§89 item 2): odd-parity starts only, or read the chooser.
- **A comm/pane mid-order eats the keys** (byte 88) and a +2 year delta means the turn record
  spanned two rounds — reroll, do not reinterpret. Reroll triggers: comm in the order window, a
  +2 delta, or the chooser never seen with a wrong-parity leg.
- **A same-type headcount is not an arrival**; **indices lie across a turn** (the array
  reshuffles AND GROWS — bases produce `+17 = 0` units); content is identity; snapshot and diff.
- **OCR is ~1-15 s a poll and LIES about legibility**: the production-banner HUD and the `g`
  chooser both classify `unknown`/`dialog`. Memory + "nothing drawn in the modal band" is the
  clean-HUD oracle. `scratch/m54h_clear.py` Escapes on `unknown` — it can RAISE the quit prompt
  at a clean-but-garbled HUD (session 90); Escape closes the prompt (never click its OK).
- **The pump eats the byte tens of ms after the OK** — sample THROUGH the click. Sentries (byte
  1) move on their own every round; HOLD (2) is inert. `b` (and every order letter) is a
  MAP-level key while orders mode is off. `sp.focus()` is a no-op until `sp.WIN` is set.
- **Escape at a clean HUD raises "Do you really want to quit?"**; never click its OK. Escape on
  the title screen exits. Arrows drive the MAP CURSOR; blind map clicks SCROLL. `--load` needs a
  Windows path.

## THE 10 RULES — condensed from sessions 75-90

1. One milestone per session, then stop. Do not re-verify closed milestones.
2. Commit early (a commit on the branch is the only thing that survives an overflow).
3. Patch docs; never read-then-write a doc over 10 KB.
4. Keep tool results small: grep/sed windows, `evidence.py show`, tail. Never cat a log.
5. New screen classes go into `test_classify.py` AND `check_classes.py` with saved frames
   BEFORE they go into the driver. A new BEHAVIOR on an existing class is a driver change.
6. Acceptance is a script printing `PASS` on one real invocation. Never weaken a gate to make a
   run pass; strengthening gates is allowed. A documented negative may merge (sessions 86, 89).
7. Verify state by reading memory, never by trusting a screenshot or a keypress you sent.
8. Before `git add -A`, sync `skill/` from the live skill and commit it in the same commit.
9. `gate.py` needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated and every `path:NNN`
   citation you add must resolve. `gate.py` refuses `main`; submit/merge refuse a dirty tree.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
    produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session 91` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 92, then `wc -c NEXT_PROMPT.md` (must be <= 15,500).
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
file; `skill_manage delete`; `nohup`/`&` in a tracked terminal call (use background=true);
hand-computed parity sums; parking a unit on an unchecked tile.

## Report style (what a finished session looks like)

One screen: what changed, the acceptance numbers WITH the command that produced them, what is
open, next pick. No narration.
