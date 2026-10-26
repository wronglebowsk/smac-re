# NEXT_PROMPT.md — footing for the next session (written at the M56 close, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A–M54E** (#39-#44): driver survives a full game / 40 saved turns / ORDERS / queues a MOVE
  / the ordered WALK lands. **M54F-M54i** (#47-#50): type byte settled, founding keyed, chooser
  geometry, attribution by record DIFF.
- **M54i2 / M54j / M54k** (#51-#53) + **M54k2** (#54): own-base walks, MULTI-LEG walks across
  TURN COMPLETEs, the PRE_ARM hook, the hook-shape PASS. **The walking arc is CLOSED.**
- **M55 — the solo round boundary read end to end and accounted** (#55, session 91).
  `scripts/m55_boundary.py` prints PASS on a real invocation, FAILs on a hand-typed fixture.
- **M56 — WHY NOTHING GETS BUILT: the gate is MINERAL STORAGE, natural queues are EMPTY on every
  base, session 91's "zero production" was a false negative** (session 92 + close addendum in
  `SESSION_NOTES.md`; `m56_build.py` PASS, `test_m56_predict.py` 8/8, fixture exit 1; mechanics in
  `NAMED.md:489` "M56 block").
- Open spines (`ROADMAP.md:86` is S2, the solo turn advance): **S1** (production rebuild), **S2**
  (heartbeat — M55 opened the boundary, M56 settled its production step, M57 continues),
  S3/S4/S5 untouched as spines.

## WHAT SESSIONS 91-92 ESTABLISHED — do not re-learn these the hard way

1. **The solo heartbeat is the player WALK in `FUN_00520c10`**, not the MP stage machine; it
   ROTATES (starts after our id): `[0,2,3,5,6,7]` at 2229-2232. `DAT_0091c630` (stage) stayed 0 in
   every solo sample — never floor on stage in solo.
2. **PRODUCTION, settled by controlled poke (M56)** — this SUPERSEDES session 91 items 2/6:
   - Queue processor `0x4ef6d0` (pipeline stage 6 of `0x4f5a70`, `ghidra_out/shard_012.c:24182`)
     completes a queue head iff **mineral storage `base+0x40` >= price**, price =
     `0x4e40a0(owner,1,-1) x type_cost(+41)` = 10 x cost in-mask. Pay -> **clamp B
     `max(0,min(10,d0))`** (`0x4f0cc3-0x4f0ce9` re-caps storage after the debit) -> POP `0x4ef5d0`
     (pending `+0x4c` −1, queue `+0x50..` left-shift, `faction[head]−1` at `0x94dc84`) ->
     `FUN_005ab650` creates the unit ON the base tile, order 0.
   - Per-round chain: `0x5208f0(p)` -> `0x520540(p)` -> per-owner base loop
     (`ghidra_out/shard_013.c:11568`) -> `0x4f5a70(base)` -> `0x4ef6d0` — **every base every round
     in solo; there is no separate production phase**. The `faction+0x104 & 2` gate at `0x521070`
     guards only the AI upkeep step `0x574370` — session 91's "sliders +0x104 = 0 -> nothing can
     build" read the wrong step.
   - **`+0x3c` progress / `+0xcc` rate do NOT gate**: the armed base had income 0, rate 1, progress
     32 and produced on the very next boundary. M53i's `cost <= +0xcc + +0x3c` completion test is
     the OUT-mask race scan / display path (`0x4ee8c7` "display only"), not the queue.
   - **Why nothing builds naturally**: pending 0 + head −38 (`0xffffffda` = empty) on ALL bases,
     net income `+0xd0` = 0 everywhere — the gate can never fire. Session 90 was RIGHT (produced
     units arrive order 0 on base tiles); session 91 counted only OUR-side -> false negative.
     Enemy bases produce every boundary (queues refill inside their AI turn — enemy predictions
     are REPORTED only).
3. **A produced unit FREEZES the auto-end.** Auto-advance ("No units need orders Press ENTER",
   `FUN_00520c10(2)` gated on `DAT_0091f69c & 1`) only fires when NOTHING is actionable; a fresh
   order-0 garrison is actionable, the cursor parks on it, Return for 150 s does nothing. ONE `h`
   on the cursor unit closes the turn at once (`tf 0->2`, walk resumes) — `m56_build.py` escalates
   Return -> `h` every 4 s past 8 s. Best candidate explanation for session 91's 2204 90 s stall.
4. **Modal event dialogs FREEZE the walk** (eradication/tech/lost-unit popups; Return every 2 s
   dismisses; the chain can open the PLANET display, which eats Enter). **The Operations Director
   popup does NOT close on Return** — default row "Zoom to Base Control", Return CYCLES options;
   click OK at window coords ~(630,247). **Never press Escape on the tactical map** — quit prompt
   (its OK banned; "Oops, no, wait!" is the default, Return takes it).
5. **The support cliff**: produced units DIE at upkeep when their base has no mineral income
   (popup "...not sufficient to support...has been disbanded"; our units 7->3 at 2221-2222). Do
   not read a disband as "never produced": the arrival is verified at the boundary, death later.
6. **Record bytes are rewritten in place at the boundary**: u16 +28 (legs_y[0]), +48, +50 each
   decrement by 1 per round while dead units compact out. Identity for accounting is
   **(x, y, type, owner, order)** — never 52-byte equality, never the record index.
7. **Order semantics at the boundary**: transient AI orders (9, 14, 24, 27, 88) reset to 0 IN
   PLACE; order 24 = cargo/unload materialisation; produced units arrive **order 0 on a base tile
   of their own faction**. Floor only OUR side; label enemy-side attribution confounded.
8. **Research completes live** (M55 captures). Our `labcnt` reads 229 while others read 5-137 and
   p0 reads −1 — **`LAB_ARR` indexing is unverified after player 1 (Gaians) died** (active_mask
   0xFF -> 0xFD, now 253). Read the array around the record before trusting lab counts.
9. **We are LOSING**: University Base captured at 2214->2215; box at M56 close: **year 2232, 1
   base (Korolev Center 29,42), units_ours 2, n_bases 29, pid 1329211**. Reload recipe:
   `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename) -> HUD at
   2150; `m54g_prep.py` + a founding turn re-creates Korolev Center. Expect to reload BEFORE
   measuring.
10. **`turn_flags` 0x100000 is set by Enter and cleared at the boundary**; with auto-end no flip
    appears. Energy deltas readable for 7-8 factions every round; spending ledger `faction+4` zero
    after upkeep; energy never negative.

## THE PICK — M57: GIVE THE LOOP AN ECONOMY (S2, production)

Do exactly ONE milestone, then stop. Do not re-verify closed work.

M56 proved the gate but only with a MINERALS POKE arming the queue (pending 0->1, head −38->2,
minerals 0->100). The loop cannot yet get anything built the way the GAME does it. M57 must close
one of these two shapes, from memory:

(a) **A real (non-poked) positive prediction**: reload `m54b_clean.SAV` + re-found; get one
arrival predicted + verified where the QUEUE was filled by the GAME, not our poke. The AI chooser
`0x4f6030` fills enemy queues; ours needs the BUILD UI (`0x417ee0` queue-edit dispatch) or a
mineral-yielding facility (`+0xd0` > 0) so storage >= price fires naturally.
(b) **The facility side**: queue a facility (negative queue head) at an armed base and floor the
`+0x8c` facility-bitmap delta + the `0x417ee0` dispatch from memory.

Acceptance: `scripts/m56_build.py` (extended) prints PASS on ONE real invocation with a positive
completion **not armed by a minerals poke**; a hand-typed fixture must still FAIL. A DOCUMENTED
NEGATIVE merges only with base-field evidence (which field says why the game never queued anything).

Do:
1. Read `NAMED.md:489` (M56 block) + `ghidra_out/shard_012.c` around `0x417ee0` (queue edit) and
   `0x4f6030` (AI queue fill). Name what fills a queue and what the BUILD UI writes.
2. Decide shape (a) or (b) from what the code says; state reload + re-found FIRST if the box is
   below ~5 units (it is: 2).
3. Extend `scripts/m56_build.py` (or a sibling) for the chosen shape; add rule cases to
   `scripts/test_m56_predict.py`; the fixture in `scratch/` must FAIL the extended verifier.
4. Do not weaken floors to make a run pass. Strengthening is allowed.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — Session 92 + its close addendum are the recent work. Never read
   the whole file.
3. `git status`; `git branch --show-current` (never `main`); `python3 scripts/milestone.py start M57`
   FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` + `scripts/m54d_census.py` — box at M56 close: 1 base,
   2 units, year 2232. If a base is gone or the state reads impossibly, reload (item 9 recipe).
5. Only then touch Ghidra exports / the production script.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md:86` — the S2 row (turn advance, solo). Read the row before committing to shape.
- `SAVE_FORMAT.md:141` — the 304-byte base record (x@0, y@2, faction LOW byte @+4, name@19..51);
  `SAVE_FORMAT.md:159` — the 52-byte unit record (type u16@+10, owner@+14, order@+17, legs
  @+20..+35, mp@+40, flag dword@+4). Queue/accumulator fields settled in `NAMED.md:489`.
- `ORDERS.md:543` §15 — production at the boundary: the gate, the two freezes, the acceptance cmds.
- `scripts/m56_build.py` — **the instrument to extend**: natural-state snapshot, `--arm N` poke +
  read-back, per-base predictor (pending/head/minerals/price), arrival + bookkeeping verifier,
  Return->`h` escalation, Operations Director OK click, `--fixture` mode.
- `scripts/test_m56_predict.py` — mock-/proc/mem rule cases (8 today): extend alongside the rule.
- `scripts/m55_boundary.py` — the boundary sampler/accountant (`G`, `FFIELDS`, `snapshot()`,
  `poke_hold()`, `account()`, the 2 s Return dismisser) — reuse for any new boundary script.
- `ghidra_out/shard_012.c` — queue pipeline `0x4f5a70`/`0x4ef6d0`/`0x4f0a3d`, pop `0x4ef5d0`,
  unit creation `FUN_005ab650` (:20890 area), stage-6 call (:24182 area); `shard_013.c` — solo
  round machine `FUN_00520c10`, upkeep `FUN_005208f0`, per-owner base loop (:11568 area).
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/production-queue.md` (NEW, M56), `references/wine-operations.md`,
  `references/terraforming-order-path.md`, `references/production-rebuild.md` (S1 notes).

## OPERATIONAL KIT

- Production: `python3 scripts/m56_build.py [--arm N] [--boundaries N] [--timeout 120]
  [--fixture FILE]` — snapshots queues, arms one base (poke + read-back), predicts, presses
  Return/`h` to close turns, verifies arrivals + bookkeeping per boundary; exit 0 only when every
  floor is `ok`. Trace JSONL to `evidence/`.
- Boundary: `python3 scripts/m55_boundary.py [--timeout 300] [--poll 0.002] [--settle 0.3]
  [--no-poke] [--no-enter] [--fixture FILE] [--trace PATH]`.
- State / census: `scripts/smac_state.py --json`, `scripts/m54d_census.py`,
  `scratch/m54k_watch.py [secs x y]` (0.5 s memory diff watcher), `scratch/m56_dump.py` (queues).
- Driver (reload+refound): `scripts/smac_play.py --turns N --timeout 240 --no-escape 3000
  --orders-per-turn 1 --verbose --tag <t>`; check: `scripts/m54a_check_run.py <trace> --timeout
  240 --min-own-base-arrivals 1`.
- Tests: `test_m56_predict.py` 8/8, `test_walk_diff.py` 37/37, `test_classify.py` 17/17,
  `check_classes.py` failures: 0; delete `evidence/**/_3x.png` after classifier runs. Check
  `evidence.py budget` BEFORE adding frames/traces (gate FAILs at 30 MB; a trace is ~50 KB).
- Wine: prefix `./programs/prefix` == `~/.wine-smac32`, `DISPLAY=:99`, Xvfb :99 800x600x16, window
  "Sid Meier" (xdotool). `pgrep -x terran.exe` (NEVER `-f`).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **A modal dialog is invisible to memory reads** — `cur_player` stops moving, every semaphore 0.
  Suspect one whenever the walk stalls > 30 s. The Operations Director popup needs the OK CLICK
  (~(630,247)), not Return. A produced unit needs ONE `h`, not Return.
- **Never press Escape on the map** — quit prompt (its OK is banned).
- **Record indices lie across a boundary** (compaction rewrites +28/+48/+50, reshuffles slots);
  content is identity. A same-type headcount is not an arrival.
- **A disband is not a non-production** — verify the arrival AT the boundary; upkeep kills the
  unit later if the base has no income (support cliff).
- **One variable at a time.** A unit that vanished while an identical one appeared elsewhere is a
  MOVE (or production+death pair) — write "confounded", never "because".
- **`LAB_ARR` may not be indexed by player id** after a faction died. Read around the record.
- **With everything HELD the game auto-advances ~8 s/round** — a turn record can span two year
  flips; keep the "exactly two distinct years" floor + the 0.2 s year poll.
- OCR is 1-15 s a poll and LIES; memory + "nothing drawn in the modal band" is the clean-HUD
  oracle (the production banner garbles OCR, session 89).
- Reload recipe: BARE filename (`m54b_clean.SAV`); LOAD browser opens IN the saves dir; dismiss
  the error, type the filename, OK, click (290,391).

## THE 10 RULES — condensed from sessions 75-92

1. One milestone per session, then stop. Do not re-verify closed milestones.
2. Commit early (a commit on the branch is the only thing that survives an overflow).
3. Patch docs; never read-then-write a doc over 10 KB.
4. Keep tool results small: grep/sed windows, `evidence.py show`, tail. Never cat a log.
5. New screen classes go into `test_classify.py` AND `check_classes.py` with saved frames BEFORE
   they go into the driver.
6. Acceptance is a script printing `PASS` on one real invocation; prove it FAILs on a hand-typed
   fixture. Never weaken a gate; strengthening is allowed. Documented negatives may merge.
7. Verify state by reading memory, never by trusting a screenshot or a keypress you sent.
8. Before `git add -A`, sync `skill/` from the live skill and commit it in the same commit.
9. `gate.py` needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated and every
   `evidence/<file>:<line>` citation you add must resolve. It refuses `main`; submit/merge refuse
   a dirty tree.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
    produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session <N>` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for the next session, then `wc -c NEXT_PROMPT.md` (must be <= 15,500).
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`
4. `git add -A && git commit -m 'M57: checkpoint'`
5. `python3 scripts/gate.py --base main` (must be GREEN)
6. `python3 scripts/milestone.py submit --title "..."` -> note the PR number ->
   `gh pr checks <n>` -> `python3 scripts/milestone.py merge <n>`
Then STOP and report.

## IF YOU HIT "request exceeds the context window"

In your very next tool call run `git add -A && git commit -m 'M57: checkpoint'`, then reply with
what is done and what is not. Do not compress and do not rewrite docs to recover.

## Never

commit to `main`; `Escape` on the title screen OR on the tactical map; `pkill -f`/`pgrep|kill` by
name (matches this shell); click OK on "Do you really want to quit?"; `--mode stop`; `file://` with
`--load`; a `clear`-prefixed command; backticks in a commit message; a `MEDIA:` line unless you
attached a file; `skill_manage delete`; `nohup`/`&` in a tracked terminal call (use
background=true); hand-computed parity sums; parking a unit on an unchecked tile.

## Report style (what a finished session looks like)

One screen: what changed, the acceptance numbers WITH the command that produced them, what is
open, next pick. No narration.
