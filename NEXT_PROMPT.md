# NEXT_PROMPT.md — footing for the next session (written at the end of session 88, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A–M54E** — the driver survives a full game / 40 saved turns / ORDERS / queues a MOVE /
  the ordered WALK lands (sessions 77-82, PRs #39-#44).
- **M54F** type byte settled + checker sees defeat (#47). **M54G** founding keyed + loop FOUNDED
  (#48). **M54h** chooser geometry (#49). **M54i** attribution by record DIFF (#50).
- **M54i2 — a loop-ordered walk landed on our own base; PASS** (session 87; the step table
  preserves (x+y) parity — every earlier walker stood on the wrong parity).
- **M54j — A MULTI-LEG WALK LANDED ON OUR OWN BASE ACROSS TURN COMPLETEs; PASS** (session 88 —
  run6 `PASS`, ordered t0 (20,42) -> carried t1 -> landed t2 (28,42); PR number in `git log`).
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold.

## WHAT SESSION 88 ESTABLISHED — do not re-learn these the hard way

1. **The game AUTO-SENTRIES an order-0 unit that waits across the round boundary** (`+17` 0 -> 1,
   then it patrols on its own and leaves). A setup that leaves the chosen walker actionable BEFORE
   the run is gone by our phase (run1). Byte 2 (HOLD) survives the round; an order-0 poked DURING
   the AI round is still 0 and unmoved at phase open (`scratch/m54j_probe2.py`). Driver contract:
   the `PRE_ARM` hook arms the best held walker mid-AI-round; `pick_reactivation`
   (`held_walk_records` + eligibility: off own-base tiles, a same-parity own base off its tile,
   one-steppers LAST) re-activates in-phase when nothing is actionable. `ORDERS.md` §13.
2. **An all-HELD human phase AUTO-ADVANCES unseen**: "Year NNNN: No units need new orders. Press
   ENTER" ends the phase in seconds; TURN COMPLETE stops OCR-ing, frames classify `unknown`, and
   the order step (which lived only in the `hud` branch) never ran — run2/run3 burned 4-6 of 6
   turns with 0 orders. The order step now fires on the FIRST memory-verified our-phase frame
   (the blind-HUD gate; `blind-orders` action). Do not blame "keys don't land" before checking
   whether the phase was even open.
3. **Arrival = THE WALKER on the destination, identified by its ROUTE** (the record wearing the
   ordered leg array — it survives the pump), + mp spent + origin tile empty of that type. Six
   identical garrisons on the destination made run4 print ARRIVED for a 2-tile step
   (`evidence/trace_m54j_run4_20261025_160625.jsonl`); the "no baseline -> believe" count fallback
   is retired; for CARRIED walks the pre-press count baseline is stale by design (identity +
   origin-vacated + mp is the rule; same-turn landings keep the count delta). `walker_on_dest`.
   Tests: `test_walk_diff.py` 31/31 (cases 25-31 pin the picker and the identity rule).
4. **The checker now demands a MULTI-TURN own-base arrival**: `ordered_turn < landing turn` on the
   carried move. A walk that completes inside the order turn (run5: 4 clear tiles — the pump ate
   the whole route in one cycle) is a landing, not a route, and FAILs `--min-own-base-arrivals`.
   **The pump's appetite is terrain-dependent**: 4 tiles/1 round (run5), 8 tiles/2 rounds (run6),
   ~2 tiles/round over 4+ rounds on the long diagonal (run4). A queued unit stays byte 24, is NOT
   actionable mid-walk, needs no new orders, and arrives on its own.
5. **Our two bases are OPPOSITE parity** (University 28+42=70 even, Korolev 29+42=71 odd): every
   tile matches exactly ONE base; "wrong parity for every base" only happens when a base is gone.
   `pick_reactivation` drops own-base garrisons. NEVER hand-compute parity sums — three fixtures
   failed on arithmetic; check sums mechanically.
6. **LOAD browser (wine 10.20-staging)**: `m54a_load.py --relaunch` blind path-typing MANGLES
   (`\h`->`Eh`, backslashes dropped -> "unable to find file"). The LOAD browser OPENS IN THE
   SAVES DIR: dismiss the LOADING ERROR (Return), clear NAME, type just the FILENAME
   (`m54b_clean.SAV`), OK bar (330,552), then difficulty confirm (290,391). Verified: HUD at 2150,
   1 base, 6 units, then `m54g_prep.py` + a 2-turn founding -> Korolev Center in the base array.
7. Classifier gates unchanged: `test_classify.py` 17/17, `check_classes.py` 17/0 (`_3x.png`
   siblings deleted right after). No new classes in session 88 — the banner frame classifies
   `unknown` and the DRIVER handles it; a new behavior on an existing class is not a new class.

## THE PICK — M54k: CLOSE THE PRE_ARM LOOP (a PASS run whose ONLY mover came from the hook)

Do exactly ONE milestone, then stop. Do not re-verify closed work.

Run5/run6 armed the walker from setup (actionable before the run). The hook path — everything
HELD at run start, `PRE_ARM` poking the best held walker to 0 mid-AI-round — is probe-verified but
has never produced a PASS. Close it.

Acceptance (the ONLY thing that prints PASS; floors fail CLOSED):
`python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1`
on ONE unattended 6-turn run: `advanced 6/6`, year deltas `{1: 6}`, `stuck 0`, a `g->byte24` line
in the order mix, `bases_ours >= 2` at the END, a `landed` carried move onto our own base with
`ordered_turn < landing turn` — AND the trace's `actions` contains `pre-arm:recN` (the hook armed
it; setup left ZERO actionable). Never weaken a floor. If the hook arms but the walk never lands,
report the negative WITH per-turn position read-backs (census each turn) and merge the notes.

**Shape:** the box is at **2164, 2 bases, 8 units, n_bases 18** (pid 1271556), quiet window open
(~10-15 yr from the 2152 founding; the war took University once at 2177-2198 while the loop sat
passive — if a base is gone at census, reload `m54b_clean.SAV` + `m54g_prep.py` + a 2-turn
founding, item 6). Setup: `scratch/m54j_setup2.py` (HOLD everything; reads back the eligible held
walkers + man distances — point it at / pick a same-parity tile 6-8 tiles from a same-parity own
base; the west corridor along y=42 is proven passable, the (49,33) diagonal walkable but slow).
Launch: `smac_play.py --turns 6 --timeout 240 --no-escape 3000 --orders-per-turn 1 --verbose
--tag m54k_runN`. Between runs `scratch/m54h_clear.py` until `HUD CLEAN`.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 87 and 88 are the recent work. Never read the whole
   file (~68 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start M54k` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 88 left the game LIVE at **2164**, pid
   1271556, `bases_ours 2`, `units_ours 8`. If it reads impossibly (nonsense types, zero bases of
   ours, arrays that decode as garbage): do NOT build on it — reload per §88 item 6.
5. `python3 scripts/m54d_census.py` — where our records and both bases are, RIGHT NOW (indices
   lie across turns; content is identity). `python3 scratch/m54h_clear.py` if any pane is up.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing, §4 the byte table (`0x18` queued MOVE, legs `+20..+27` x /
  `+28..+35` y — a WAYPOINT; the chooser's pick is the destination), §6 the in-loop contract,
  §7 WHEN the queued MOVE runs, §8 THE FOUNDING, §9 the chooser's rows, §10 SENTRY/HOLD + the
  pre-press baseline + the diff/attribution rules, §11 WHO OWNS THE CURSOR, §12 THE STEP TABLE AND
  PARITY + the TURN COMPLETE execution + the mp_after rule, **§13 THE AUTO-SENTRY + the in-phase
  reactivation contract + the opposite-parity-bases fact**.
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record (type u16@+10, owner@+14, order@+17,
  legs@+20..+35, mp-used@+40) and the 304-byte base record (x@0, y@2, faction LOW byte at +4).
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**; class table
  `0x98ADB2[type*52] & 0xff`. Class 8 = colonist (founding), class 3 = Scout Patrol.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md` (now incl. M54j).

## OPERATIONAL KIT

- Census / position: `m54d_census.py`; `scratch/m54j_setup2.py [x y]` (HOLD everything, report the
  eligible held walkers + man — the reactivation-shape setup); `scratch/m54j_setup3.py [fx fy tx
  ty]` (poke a garrison unit to a target tile actionable + HELD rest — the actionable-from-setup
  shape); `scratch/m54j_setup.py` (order-0 single actionable); `scratch/m54j_probe2.py` (mid-round
  poke timeline); `scratch/m54i2_pump.py`; `scratch/m54h_clear.py [N]`; `m54g_prep.py`;
  `m54a_load.py --relaunch` (SMAC_SAVE env; if the blind path-typing mangles, the filename recipe
  in §88 item 6).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--orders-per-turn 1] [--load <Z:\\path>] [--verbose]`. Turn records carry `orders` (with `dest`,
  `chooser_pick`, `walk_diff {attributed, confounded, claim, rivals, before_legs}`, `order_counts`,
  `attempts`) and `moves` (with `landed`, `carried`, `ordered_turn`, `dest_is_own_base`,
  `dest_count`/`src_count`, `mp_after`). A 6-turn run is ~2-4 min: background it, poll
  `grep -c '"turn"'` on the trace. `--orders-per-turn 1` keeps exactly one mover in flight.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N] [--min-moves M]
  [--min-our-bases N] [--min-own-base-arrivals K]` — the ONLY thing that can print `PASS`; floors
  fail CLOSED; an own-base arrival MUST be multi-turn (`ordered_turn < landing turn`).
- Tests: `python3 scripts/test_walk_diff.py` -> `PASS 31/31 attribution cases`. Classifier gates:
  `scripts/test_classify.py` -> `PASS 17/17`; `scripts/check_classes.py` -> `frames: 17 failures:
  0`; **delete `evidence/**/_3x.png` right after**. `evidence/` is at ~29/30 MB — check
  `python3 scripts/evidence.py budget` BEFORE adding frames; the sanctioned big artifact is
  `m53j_text.txt.gz` (keep; it is cited).
- Wine: prefix `./programs/prefix` == `~/.wine-smac32`, wine 10.20-staging-tkg at
  `~/tools/wine-10.20-staging-tkg-x86/bin/wine`, `DISPLAY=:99`, Xvfb :99 800x600x16, window at
  0,0. Launch = `m54a_load.relaunch()`. `pgrep -x terran.exe` (NEVER -f).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **Auto-sentry + auto-advance before anything else** (§88 items 1-2): order-0 units do NOT wait
  between rounds, and an all-HELD phase does not wait for you at all. Arm mid-round or in-phase.
- **Parity before anything else** (§12, §13): check sums mechanically; with opposite-parity bases
  every tile matches exactly one base.
- **A same-type headcount is not an arrival** (item 3): our bases are crowded with identical
  units. Identity = the route worn.
- **`sp.focus()` does nothing until `sp.WIN = sp.find_window()`**; the cursor is game-owned and
  pokes do not stick; poke-MOVED units are invisible to tile occupancy (fine for prep — the
  dispatcher pokes do the ordering; wrong for "stand here and be found").
- **OCR is ~1-15 s a poll and LIES about legibility**; poll the oracle (memory) at 100 ms; the
  HELD-banner frame classifies `unknown` — the blind gate handles it.
- **Indices lie across a turn** (the array reshuffles AND GROWS — bases produce units onto their
  own tile, order 0 mp 0 empty legs). Content is identity; snapshot and diff.
- **Attaching mid-round makes turn 0 advance the year by 3** (checker fails `{1: N}`): attach in
  OUR phase or burn a turn first; the box is often parked on a dialog — `m54h_clear.py`.
- **The pump eats the byte tens of ms after the OK** — sample THROUGH the click; one read after
  the click is a coin flip. Sentries (byte 1) move on their own every round and rewrite their
  legs; HOLD (2) is inert. `b` (and every order letter) is a MAP-level key while orders mode is
  off. The tile array is behind a POINTER and the pitch is LIVE: `*(u32*)0x92ae14 +
  (DAT_00692184*y + x>>1)*0x2c`, pitch 32 on this 64x64 world.
- **Escape at a clean HUD raises "Do you really want to quit?"**; Return there ends the process;
  Escape on the title screen exits. Never click its OK. Arrows drive the MAP CURSOR; `space`
  neither queues nor pumps; blind map clicks SCROLL. `--load` needs a Windows path.

## THE 10 RULES — condensed from sessions 75-88

1. One milestone per session, then stop. Do not re-verify closed milestones.
2. Commit early (a commit on the branch is the only thing that survives an overflow), then
   checkpoint-commit every few hundred lines.
3. Patch docs; never read-then-write a doc over 10 KB.
4. Keep tool results small: grep/sed windows, `evidence.py show`, tail. Never cat a log.
5. New screen classes go into `test_classify.py` AND `check_classes.py` with saved frames BEFORE
   they go into the driver. A new BEHAVIOR on an existing class is a driver change, not a class.
6. Acceptance is a script printing `PASS` on one real invocation. Never weaken a gate to make a
   run pass; strengthening gates mid-session is allowed and good (session 88 did it three times).
   If it cannot pass, say so and merge nothing (a documented negative may merge).
7. Verify state by reading memory, never by trusting a screenshot or a keypress you sent.
8. Before `git add -A`, sync `skill/` from the live skill and commit it in the same commit.
9. `gate.py` needs BOTH `SESSION_NOTES.md` and `NEXT_PROMPT.md` updated and every `path:NNN`
   citation you add must resolve. `gate.py` refuses `main`; submit/merge refuse a dirty tree.
10. Report in the established style: what changed, the acceptance numbers WITH the command that
   produced them, what is open, next pick.

## CLOSING ORDER (exactly)

1. Patch a `## Session 89` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 90, then `wc -c NEXT_PROMPT.md` (must be <= 15,500).
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
hand-computed parity sums.

## Report style (what a finished session looks like)

One screen: what changed, the acceptance numbers WITH the command that produced them, what is
open, next pick. No narration.
