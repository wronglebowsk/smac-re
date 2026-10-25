# NEXT_PROMPT.md — footing for the next session (written at the end of session 91, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A–M54E** — the driver survives a full game / 40 saved turns / ORDERS / queues a MOVE /
  the ordered WALK lands (sessions 77-82, PRs #39-#44).
- **M54F** type byte settled + checker sees defeat (#47). **M54G** founding keyed + loop FOUNDED
  (#48). **M54h** chooser geometry (#49). **M54i** attribution by record DIFF (#50).
- **M54i2 / M54j / M54k** (#51-#53): an own-base walk, a MULTI-LEG walk across TURN COMPLETEs,
  the PRE_ARM hook path (a DOCUMENTED NEGATIVE). **M54k2** — the hook-shape run PASSED (#54).
  **The walking arc is CLOSED.**
- **M55 — THE SOLO ROUND BOUNDARY IS READ END TO END AND ACCOUNTED** (session 91):
  `scripts/m55_boundary.py` prints PASS on a real invocation and FAILs on a hand-typed fixture.
  See `SESSION_NOTES.md` "Session 91" for the numbers.
- Open spines (`ROADMAP.md:86` is S2, the solo turn advance): **S1** (production rebuild), **S2**
  (heartbeat — M55 opened it, M56 continues), S3/S4/S5 untouched as spines.

## WHAT SESSIONS 90-91 ESTABLISHED — do not re-learn these the hard way

1. **The solo heartbeat is the player WALK in `FUN_00520c10`**, not the MP stage machine. The
   walk ROTATES (starts after our id): observed `[3,3,4,5,6,6,7,0,2,2,3]`, `[7,3,4,5,6,7,2,3]`.
   `DAT_0091c630` (stage) stayed 0 in every solo sample — never floor on stage in solo.
2. **The boundary may need NO key, or may need one — and nobody knows the condition.**
   Rounds ran 2206->2208 with zero input (auto-end fires 1-2 s after our turn opens when every
   unit is HELD); at 2204 the SAME hold-all state stalled 90 s. Gate text: "No units need orders
   Press ENTER" -> `FUN_00520c10(2)` gated on `DAT_0091f69c & 1`. **Confounded/unknown.** An S2
   inventory should find what sets that bit; until then, wait for `cur_player == ours` and press
   Return — never refuse because it is not our phase.
3. **Modal event dialogs FREEZE the walk** (eradication/tech/lost-unit popups). One held
   `cur_player = 2` for 90 s with every semaphore zero; the chain then opened the PLANET display,
   which swallowed a single Enter. Return every 2 s while `cur_player != ours` and while mid-walk
   is safe (Return is only consumed as turn-end inside the human loop). **Never press Escape on
   the tactical map — it raises "Do you really want to quit?"** (its OK is banned).
4. **Record bytes are rewritten in place at the boundary**: u16 +28 (legs_y[0]), +48, +50 each
   decrement by 1 per round while dead units compact out. Identity for accounting is
   **(x, y, type, owner, order)** — never 52-byte equality, never the record index.
5. **Order semantics at the boundary**: transient AI orders (9, 14, 24, 27, 88) reset to 0 IN
   PLACE; order 24 = cargo/unload materialisation; produced units arrive **order 0 on a base tile
   of their own faction**. Enemy-side attribution is confounded by moves + resets + cargo — label
   it, floor only OUR side.
6. **ZERO production was measured in ~7 boundaries this session** — no net-new order-0 arrival on
   ANY base of any faction. That contradicts session 90's "production drops `+17 = 0` units on
   base tiles at every round boundary". Faction sliders read `+0x104 = 0`, `+0x108 = 5..6` for all
   eight; Korolev's base `+0x3c` ticks +2/round (shield-style accumulator) while `+0x34`/`+0x38`
   are static. **M56 = resolve this contradiction.**
7. **Research completes live** (three captures: p2 161->0 / rtech 12->46; p6 -119 / 22->72;
   p2 -190 / 46->44). Ours advanced +2..+12 most rounds; ONE round sat flat at 8->8 with
   `labcnt 229`. Our `labcnt` reads 229 while other factions read 5-137 and p0 reads -1 —
   `LAB_ARR` (parallel to the faction array) is suspicious after player 1 (Gaians) died and
   `active_mask` went 0xFF -> 0xFD. Verify `LAB_ARR` indexing before trusting lab counts.
8. **We are LOSING the game**: garrison at (28,42) attrited 11->10->6->5 (deaths, cause
   unattributed), then **University Base was CAPTURED by faction 6** at 2214->2215 (base record
   survives with `faction 6`; 28 bases before and after). C6 floors "no base VANISHES", not "we
   never lose a base". State at session end: **year 2218, pid 1329211, 1 base (Korolev Center
   29,42), 5 units** — reload with item 6 of the old recipe (`SMAC_SAVE='m54b_clean.SAV'
   python3 scripts/m54a_load.py --relaunch`, BARE filename) before measuring if the base falls.
9. **`turn_flags` 0x100000 is set by Enter and cleared at the boundary** (`0x100002 -> 0x2` at
   +0.073 s — the only flip observed). With auto-end closing the turn no flip appears at all.
10. Energy deltas readable for 7-8 factions every round; the spending ledger `faction+4` is zero
    for every player after upkeep in every run; energy never negative (clamp holds).

## THE PICK — M56: WHY DOES NOTHING GET BUILT? (S2, production)

Do exactly ONE milestone, then stop. Do not re-verify closed work.

The contradiction is concrete and it is memory-checkable: session 90 saw produced units arriving
on base tiles at a boundary; session 91 saw **seven boundaries with zero net-new order-0 records
on any base of any faction**. One of the two readings is wrong and the save format knows which.
M56 must decide, from memory, whether ANY base is building, and prove it.

Do:
1. Read the base record's production fields out of `SAVE_FORMAT.md` (304-byte record; the queue and
   the shield/cost accumulators) and dump them for all 28 bases across two boundaries, plus the
   faction slider words `+0x104`/`+0x108` and the base `+0x3c`/`+0x34`/`+0x38` dwords.
2. Ghidra: find the code that ADDS a unit record (`FUN_00522240`/`FUN_00520c10` callers — who
   calls the unit-creation path and under what basefield condition), and the code that advances a
   base's build accumulator. Name the base field that gates production.
3. Build a script that PREDICTS, per base, whether a unit arrives at the next boundary (queue
   non-empty AND accumulator >= cost) and then verifies the prediction after the flip.
   Acceptance: PASS on ONE real invocation over 2-3 boundaries; a hand-typed trace must FAIL.
   A DOCUMENTED NEGATIVE merges if it proves with base-field evidence that no base was building
   (queue empty / cost not reached / slider zero) — that also settles session 90's claim.
4. Do not weaken floors to make a run pass. Strengthening is allowed.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 90 and 91 are the recent work. Never read the whole file.
3. `git status`; `git branch --show-current` (never `main`); `python3 scripts/milestone.py start M56`
   FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` and `python3 scripts/m54d_census.py` — the box may now
   have ONE base and five units. If a base is gone or the state reads impossibly, reload (item 8).
5. Only then touch Ghidra / the boundary script.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md:86` — the S2 row (turn advance, solo). Read the row before committing to shape.
- `SAVE_FORMAT.md:150` — the 52-byte unit record (type u16@+10, owner@+14, order@+17,
  legs@+20..+35, mp@+40, flag dword@+4) and the 304-byte base record (x@0, y@2, faction LOW byte
  at +4, name@19..51); the production-queue fields are what M56 must pin down.
- `scripts/m55_boundary.py` — **the instrument to extend**: `G` (globals table), `FFIELDS`
  (faction dword indices), `snapshot()`, `timeline_row()`, `poke_hold()`, `account()` (10 floors),
  the wait-for-our-turn loop, the 2 s Return dismisser, `--fixture` mode. Reuse all of it.
- `ORDERS.md` §14 (in-phase pump burst, queued_rescan, year-poll, the 0x100000 bit); §4 the byte
  table; §5 modal = key sink; §10 SENTRY/HOLD + attribution; §12 step table and parity.
- `ghidra_out/shard_013.c` — the solo round machine `FUN_00520c10`, upkeep `FUN_005208f0`,
  research `FUN_0051fe90`/`FUN_005aaa20`/`FUN_005aa880`, year `FUN_0051f320`/`FUN_005b2c00`.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md`.

## OPERATIONAL KIT

- Boundary: `python3 scripts/m55_boundary.py [--timeout 300] [--poll 0.002] [--settle 0.3]
  [--no-poke] [--no-enter] [--fixture FILE] [--trace PATH]` — prints one line per floor plus the
  inventory reports; exit 0 only when every floor is `ok`. It pokes our records to HOLD(2),
  waits for our turn, presses Return, samples at 2 ms, snapshots after `cur_player` returns.
- State / census: `scripts/smac_state.py --json`, `scripts/m54d_census.py`,
  `scratch/m54k_watch.py [secs x y]` (0.5 s memory diff watcher).
- Driver (only if a reload+refound is needed): `python3 scripts/smac_play.py --turns N --timeout
  240 --no-escape 3000 --orders-per-turn 1 --verbose --tag <t>`; check with
  `scripts/m54a_check_run.py <trace> --timeout 240 --min-own-base-arrivals 1`.
- Tests: `python3 scripts/test_walk_diff.py` -> `PASS 37/37`; `scripts/test_classify.py` ->
  `PASS 17/17`; `scripts/check_classes.py` -> `failures: 0`; delete `evidence/**/_3x.png` after.
  `evidence/` is **28 MB of 30** — check `python3 scripts/evidence.py budget` BEFORE adding frames
  or traces; a boundary trace is ~50 KB (3 full snapshots), so a 3-boundary run is fine but do not
  leave a dozen of them.
- Wine: prefix `./programs/prefix` == `~/.wine-smac32`, `DISPLAY=:99`, Xvfb :99 800x600x16,
  window "Sid Meier" (xdotool). `pgrep -x terran.exe` (NEVER `-f`).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **A modal dialog is invisible to memory reads** — `cur_player` simply stops moving and every
  semaphore reads 0. Suspect a dialog whenever the walk stalls > 30 s; Return dismisses it. The
  event chain can also open the PLANET display, which eats Enter.
- **Never press Escape on the map** — it raises the quit prompt (its OK is banned). If the prompt
  is up, "Oops, no, wait!" is the highlighted default; Return takes it.
- **Do not floor on stage, do not floor on a second boundary**: with auto-end the walk can close
  TWO rounds inside a 1.5 s settle window (measured: `year +2` in one run). Keep `--settle 0.3`
  and the "exactly two distinct years" floor — it catches the double flip.
- **Record indices lie across a boundary** (array compaction rewrites +28/+48/+50 and reshuffles
  slots); content is identity. A same-type headcount is not an arrival.
- **One variable at a time.** A unit that vanished while an identical one appeared elsewhere is a
  MOVE (or a production+death pair) — write "confounded", never "because".
- **`LAB_ARR` may not be indexed by player id** after a faction dies (our 229 vs others 5-137).
  Read the array around the record before interpreting `labcnt`.
- OCR is 1-15 s a poll and LIES about legibility; memory + "nothing drawn in the modal band" is
  the clean-HUD oracle. `scratch/m54h_clear.py` can raise the quit prompt.

## THE 10 RULES — condensed from sessions 75-91

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
9. `gate.py` needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated and every `path:NNN`
   citation you add must resolve. It refuses `main`; submit/merge refuse a dirty tree.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
    produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session 92` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 93, then `wc -c NEXT_PROMPT.md` (must be <= 15,500).
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`
4. `git add -A && git commit -m 'M56: checkpoint'`
5. `python3 scripts/gate.py --base main` (must be GREEN)
6. `python3 scripts/milestone.py submit --title "..."` -> note the PR number ->
   `gh pr checks <n>` -> `python3 scripts/milestone.py merge <n>`
Then STOP and report.

## IF YOU HIT "request exceeds the context window"

In your very next tool call run `git add -A && git commit -m 'M56: checkpoint'`, then reply with
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
