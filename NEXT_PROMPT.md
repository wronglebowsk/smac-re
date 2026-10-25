# NEXT_PROMPT.md — footing for the next session (written at the end of session 86, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A — the driver survives a full game unattended** (sessions 77-78, PR #39).
- **M54B — 40 turns from a saved position, unattended** (session 79, PR #40).
- **M54C — the unattended loop ORDERS units** (session 80, PR #41).
- **M54D — the loop queues a MOVE and checks it in memory** (session 81, PR #43).
- **M54E — the ordered WALK lands inside an unattended run** (session 82, PR #44). Mechanism
  `ORDERS.md` §7: the pump runs `0x18` as the chooser's OK is answered.
- **M54F — the type byte is settled; the checker can see a defeat** (session 83, PR #47).
- **M54G — the founding is keyed and the loop FOUNDED a base** (session 84, PR #48): `b`,
  class 8 + legal tile, Return founds, unit consumed, oracle = the base array (`ORDERS.md` §8;
  session 86 re-did it live from a reloaded save).
- **M54h — chooser geometry + walk-evidence rules** (session 85, PR #49, merged as notes; the
  walk floor was NOT met there either).
- **Session 86 (M54i, OPEN).** Attribution WORKS in the loop (§10 wins below); a loop-ordered
  walk has STILL not landed on our own base — three failure modes measured, two fixed. Session
  86 merges the fixes + a documented negative.
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold.

## WHAT SESSIONS 85-86 ESTABLISHED — do not re-learn these the hard way

1. **`g` does NOT refuse a unit garrisoned on our own base** (session 85 retraction). With two
   own bases the chooser draws TWO rows and OK is the FOURTH button centre of the measured
   button band (the merged bar-band midpoint is `Sort: Dist` — session 86 fix);
   `bar_bands()/chooser_rows()/chooser_buttons()` derive both. A row click is a selection
   (invisible in memory); OK lands `0x18` + legs; CANCEL writes nothing; the `Distance:` column
   is the CURSOR's (0 for every row); row order (Sort: Name vs nearest-first) is **unmeasured**.
2. **`+17 = 1` is SENTRY, not "no order"** — a sentry PATROLS ON ITS OWN every round: sessions
   84-85's "parked decoys" migrated (28,42)->(28,43) across run3's rounds and their leg arrays
   rewrote turn after turn. They are why every count-delta proof session 85 ran fired blind.
   The inert byte is **2 (HOLD)**: pump skips it, `find_actionable` skips it, the unit sits put
   — `scratch/m54i_hold.py [x y]` holds everything except the record alone at (x,y), read back
   on a second handle. `scratch/m54i_park.py` parks with 1 = sentry-ify, not inert.
3. **Attribution by DIFF, never by index** (`diff_order_records`, `scripts/test_walk_diff.py`
   -> `PASS 13/13`): a fresh order is a 0 -> byte transition with CHANGED legs on the watched
   record slot — watcher samples carry the whole 52-byte record; when the chooser was answered
   by its DEFAULT button (Return on an `unknown`-classifying pane) the two reads BRACKETING the
   press are the samples. Stale legs (arrays survive the pump) claim nothing; a row at ANOTHER
   index wearing the watched byte+route is a TWIN -> confounded; a signature row on our own slot
   is our record only if the start tile is VACATED of our pre-press record (session 85's "legs
   naming bases nobody ordered" = a look-alike wearing the slot while our unit stays put).
   Confounded -> `dest` stays None in the trace. Live proof: `evidence/trace_m54i_run4_*.jsonl`
   turns 0-2 `g` verified `walk_diff {attributed: True, confounded: False}`.
4. **The count baseline is the PRE-PRESS snapshot** (`snap_before`): the pump runs as the OK is
   answered (ORDERS §7), so any post-OK baseline sees the origin ALREADY vacated
   (`{dest 4, src 0}` run4 t0) and "origin count falls" can never fire. Fixed in
   `issue_order_for_unit`.
5. **The war is a variable:** 2167 -> 2187 (runs 3-4) other factions founded 7 bases, TOOK
   University Base (`bases_ours 2 -> 1`) and killed 5 of our 10 units mid-run while the floor
   still read 2. `n_bases` 19 at 2152 -> 21 at 2158: after a save reload the quiet window is
   ~10-15 years wide — finish the acceptance run inside it.
6. **Cursor placement after a fresh load is UNVERIFIED and it bit us:** run5 turn 0 `g` on a
   unit garrisoned at Korolev Center opened the **BASE SCREEN** (panes
   `[unknown,unknown,base,base]`, byte never moved) — right after a load the map cursor is
   nowhere the driver thinks. Session 85's probe worked because the cursor was placed by hand.
   NOT YET FIXED.
7. **A chooser OK can land `+17 = 24` with LEGS STILL EMPTY** (run5 t3, new unit at (29,42):
   `claim None, rivals 0, attributed False` — a MOVE with no route, honestly unattributed).
   Whether the row click lands the selection before OK is invisible in memory (session 85); the
   legs-empty OK says it sometimes doesn't take. NOT YET FIXED.
8. A clean HUD whose TURN COMPLETE row fails to OCR classifies `unknown` (HUD_BLIND_S fallback
   proven); `modal_caption` catches advisor dialogs wearing HUD chrome; `turn_flags` bit `0x2`
   clears when a panel + its dialog are dismissed (not only the "driver ran here" latch).

## THE PICK — M54i': LAND ONE loop-ordered walk on our own base

Do exactly ONE milestone, then stop. Do not re-verify closed work.

Acceptance (the ONLY thing that prints PASS; floors fail CLOSED):
`python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1`
on ONE unattended 6-turn run: `advanced 6/6`, year deltas `{1: 6}`, `stuck 0`, a `g->byte24`
line in the order mix, `bases_ours >= 2` at the END, and a `landed` move whose `dest` is a tile
holding ONE OF OUR BASES and is NOT the unit's start tile. Never weaken a floor. If it cannot
pass, report the negative WITH the record diff (what changed, what each changed record's legs
say) and merge the notes; do not manufacture a walk.

**The proven clean shape** (session 86 built it): load `m54b_clean.SAV` -> `m54g_prep.py` -> a
2-turn founding run (loop re-founds Korolev Center: `bases_ours 2`, quiet) ->
`scratch/m54i_hold.py <x> <y>` so EXACTLY ONE unit is actionable, ALONE on its tile ->
`smac_play.py --turns 6 --timeout 240 --no-escape 3000 --orders-per-turn 1 --tag m54i_runN`.
The box is ALREADY near that shape: **2158, pid 1053556, 2 bases, 7 units, `n_bases 21`** —
census first; reload only if the state reads impossibly (then redo the founding, ~4 min).

**Fix the two open failure modes BEFORE spending the acceptance run** (one change each; verify
by reading memory, not screenshots):
- **Cursor:** find the map cursor's cell — press one arrow key and diff candidate (x,y) int
  pairs across a wide scan of the map globals until you find the pair that moved; then have
  `issue_order_for_unit` VERIFY the cursor reads on the candidate tile before pressing `g`
  (arrow-nudge until right; give up after N tries and report, never press blind).
- **Legs-empty OK:** in the chooser branch, if the byte landed but the claim died on
  unchanged/empty legs, RE-OPEN (`g`) and answer once more — a second OK after a row click may
  write the route; cap at 2 retries and record every attempt in the trace.
Extend `scripts/test_walk_diff.py` for the retry shape BEFORE the driver uses it. No new screen
classes expected; if one appears it goes into `test_classify.py` AND `check_classes.py` with
saved frames first.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -80 SESSION_NOTES.md` — sessions 85 and 86 are the recent work. Never read the whole
   file (~90 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start M54i2` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 86 left the game LIVE at **2158**, pid
   1053556, `bases_ours 2`, `units_ours 7`, `n_bases 21`, `turn_flags 2`, our phase. If it
   reads impossibly: `SMAC_SAVE='Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV'
   python3 scripts/m54a_load.py --relaunch` (one base at 2150 — rebuild the second with
   `m54g_prep.py` + a 2-turn run; session 86 did exactly that).
5. `python3 scripts/m54d_census.py` — where our records and both bases are, RIGHT NOW (indices
   lie across turns; content is identity). `python3 scratch/m54h_clear.py` if any pane is up.

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing, §4 the byte table (`0x18` queued MOVE, legs `+20..+27` x /
  `+28..+35` y), §6 the in-loop contract, §7 WHEN the queued MOVE runs, §8 THE FOUNDING, §9 the
  chooser's rows, **§10 SENTRY/HOLD, the pre-press baseline, and the diff/attribution rules**.
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record (type u16@+10, owner@+14, order@+17,
  legs@+20..+35, mp@+40) and the 304-byte base record (x@0, y@2, faction LOW byte at +4).
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**; class
  table `0x98ADB2[type*52] & 0xff`. Class 8 = colonist (founding), class 3 = Scout Patrol.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md`.

## OPERATIONAL KIT

- Census / position: `m54d_census.py [--json]`; `scratch/m54i_hold.py [x y]` (HOLD all but the
  lone tile — the ONLY clean setup for the walk checker); `scratch/m54h_clear.py [N]` (panes ->
  clean HUD); `m54h_probe.py peek|legs|chooser N [--row K] [--ok] [--cancel]`; `m54g_prep.py`;
  `m54a_load.py --relaunch` (SMAC_SAVE env).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --tag <t>
  [--orders-per-turn 1] [--load <Z:\path>] [--verbose]`. Turn records carry `orders` (with
  `dest`, `walk_diff {attributed, confounded, claim, rivals, before_legs}`, `order_counts`) and
  `moves` (with `dest_is_own_base`, `dest_count`/`src_count`, `carried`). A 6-turn run is 3-8
  min: background it, poll `^turn N:` lines. `--orders-per-turn 1` keeps exactly one mover in
  flight — USE IT for the acceptance run.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N] [--min-moves
  M] [--min-our-bases N] [--min-own-base-arrivals K]` — the ONLY thing that can print `PASS`;
  floors fail CLOSED.
- Attribution tests: `python3 scripts/test_walk_diff.py` -> `PASS 13/13 attribution cases`.
  Classifier gates: `scripts/test_classify.py` -> `PASS 17/17 screen classifications`;
  `scripts/check_classes.py` -> `frames: 17 failures: 0`; **delete `evidence/**/_3x.png` right
  after**. `evidence/` is near the 30 MB FAIL budget — check `python3 scripts/evidence.py
  budget` BEFORE adding frames; gzip an uncited big text file if you need room.
- Wine: prefix `./programs/prefix`, `wine 10.0` at `./programs/`, `DISPLAY=:99`, Xvfb :99
  800x600x16, window at 0,0. Launch = `m54a_load.relaunch()`. `pgrep -x terran.exe` (NEVER -f).

## TRAPS THAT COST A SESSION HOURS (all measured)

- **OCR is ~1-15 s a poll and LIES about legibility**: the same chooser frame reads
  `dest-chooser` once and `unknown` the next (then Return answers it by DEFAULT — failure mode
  7). Poll the oracle at 100 ms; OCR only when memory has not answered.
- **Indices lie across a turn** (the array reshuffles AND GROWS — bases build units). Content is
  identity; snapshot and diff (`snap_before`).
- **Attaching mid-round makes turn 0 advance the year by 3** (checker fails `{1: N}`): attach
  in OUR phase or burn a turn first; the box is often parked on a dialog — `m54h_clear.py`.
- **The pump eats the byte tens of ms after the OK** — sample THROUGH the click
  (`order_byte_watcher` with `recs=`); one read after the click is a coin flip.
- Sentries (byte 1) move on their own every round and rewrite their legs; HOLD (2) is inert.
- **A walk needs the walker to START on a real neighbour** of the named tile (delta tables
  `0x67850c` dx / `0x678990` dy); occupancy is NOT a blocker (units stack).
- **`b` (and every order letter) is a MAP-level key while orders mode is off** (`0x91b5b8 == 0`).
- **The tile array is behind a POINTER and the pitch is LIVE**: `*(u32*)0x92ae14 +
  (DAT_00692184*y + x>>1)*0x2c`, pitch 32 on this 64x64 world.
- **Escape at a clean HUD raises "Do you really want to quit?"**; Return there ends the process;
  Escape on the title screen exits. Never click its OK.
- Arrows drive the MAP CURSOR (and after a load the cursor is NOT where you think — failure
  mode 6); `space` neither queues nor pumps; blind map clicks SCROLL; mouse motion does not move
  the cursor. `--load` needs a Windows path.

## THE 10 RULES — condensed from sessions 75-86

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

1. Patch a `## Session 87` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 88, then `wc -c NEXT_PROMPT.md` (must be ≤ 15,500).
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
