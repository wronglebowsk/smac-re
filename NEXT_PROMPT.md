# NEXT_PROMPT.md — footing for the next session (written at the end of session 89, 2026-10-25)

## THE LEDGER — read this first: the whole state of the project

Closed (PRs merged to `main`):
- **M54A–M54E** — the driver survives a full game / 40 saved turns / ORDERS / queues a MOVE /
  the ordered WALK lands (sessions 77-82, PRs #39-#44).
- **M54F** type byte settled + checker sees defeat (#47). **M54G** founding keyed + loop FOUNDED
  (#48). **M54h** chooser geometry (#49). **M54i** attribution by record DIFF (#50).
- **M54i2 — a loop-ordered walk landed on our own base; PASS** (session 87: the step table
  preserves (x+y) parity — every earlier walker stood on the wrong parity).
- **M54j — A MULTI-LEG WALK LANDED ON OUR OWN BASE ACROSS TURN COMPLETEs; PASS** (session 88).
- **M54k — the PRE_ARM hook path, DOCUMENTED NEGATIVE** (session 89): the hook armed a
  zero-actionable position (`pre-arm:recN` in the trace), the `g` order landed
  (`g->byte24`, `attributed True, confounded False`), the walker walked 6-7 positions read from
  memory and **arrived on our own base in run5** — but no run printed PASS: run6's checker line
  was `advanced 6/6 / {1: 6} / stuck 0 / bases_ours 2 / moves 0 LANDED of 5 ordered walks`
  (the walker stood ONE legal step from Korolev Center when the 6 turns ran out), run5's arrival
  was unscoreable (press-time leg drift + University captured at 2193). PR number in `git log`.
- Open in ROADMAP.md: **S1** (production rebuild) and **S2** (win conditions, transit).
  **M52** (Paul's 2416 campaign save) on hold.

## WHAT SESSION 89 ESTABLISHED — do not re-learn these the hard way

1. **The map's per-tile impassable flag.** In the 2-column tile record
   (`*(u32*)0x92ae14 + (DAT_00692184*y + x>>1)*0x2c`) the flag byte is at record **+3 for EVEN
   x** and **+7 for ODD x**; bit **0x40 set = impassable**. Validated against 98 live unit
   tiles (one exception: a faction-6 unit at (45,39)). A poke that parks a unit on an
   impassable tile makes it VANISH within seconds — runs 3-4 lost the walker at (28,34)
   (flag 0x41) that way, and the watcher caught it (`-(28, 34, 2, 0) +[]`). The y=42 corridor is
   passable from x=20 eastward; (18,42)/(19,42) are water. `scratch/m54k_watch.py` is the tool
   that reads this kind of disappearance.
2. **`g` queues the alphabetically-first own base regardless of parity.** The game wrote leg
   (29,42) — Korolev Center, parity 71 ODD — for a unit at (22,42) (parity 64, even =
   University's parity): an impossible route by §12, and it oscillated all 6 turns. The chooser
   never classified `dest-chooser` that turn (`panes ['unknown']`, `chooser_pick None`), so the
   driver's parity-gated row pick never ran and accepted the leg the game wrote. **Start the
   walker on the parity of Korolev Center (odd) and the base the game auto-targets is legal.**
3. **The pump REWRITES the leg array while it walks.** run5: the leg sampled in the press burst
   read (61,10); the record that ARRIVED at Korolev wore [(29,42)] — the ordered destination.
   `walker_on_dest` now accepts either signature (tests 32-33); a third leg, or no leg (a
   garrison), is still not the walker.
4. **A COMMUNICATION that lands inside the order step is a key sink** (ORDERS §5): run8 pressed
   `g` with comm panes up and the order byte went 0 -> **88** -> 2 (HOLD) — unverified, and the
   turn record spanned TWO year flips. `order_step_in_loop` does not re-check the screen
   between its own keypresses (open item).
5. **A produced garrison used to steal the turn's single order on the record-index tiebreak**
   (run3: `l` five turns, `g` zero, the armed walker auto-sentried waiting). Fixed: the
   candidate sort puts a unit that CAN reach an own base first (`_can_walk`). Note production:
   every round boundary drops new `+17 = 0` units on our base tiles, so "setup left zero
   actionable" is only true at the instant the setup read back.
6. **With everything HELD the game advances rounds with NO input** (~8 s/round; the year moved
   2164->2166 between two of my probes). That is why a turn record occasionally spans two
   flips (`{1: 4, 2: 2}`) and why the blind gates must not depend on OCR chrome: the map HUD
   with the production line in the message box OCRs as garbage — no MENU, no COMMLINK
   (`evidence/px_m54k_banner_probe.png`) — and the our-phase blind gates now read memory +
   "nothing drawn in the modal band" instead.
7. **Reload recipe re-verified (worked first try):** `SMAC_SAVE='m54b_clean.SAV' python3
   scripts/m54a_load.py --relaunch` — the browser opens IN the saves dir, so a bare filename
   has no backslashes to mangle -> HUD live at 2150, 1 base, 6 units; then
   `python3 scripts/m54g_prep.py` + one `smac_play.py --turns 2` loop turn ->
   `FOUND rec0 (29,42) ... bases 1->2`, `bases_ours 2` at 2151.
8. Session 88's facts still hold: the step table's 21 entries all preserve (x+y) parity; the
   two bases are OPPOSITE parity (University 70 even, Korolev 71 odd); the game AUTO-SENTRIES an
   order-0 unit across a round boundary (byte 2 HOLD is inert and survives); the cursor is
   game-owned; `sp.focus()` is a no-op until `sp.WIN` is set; indices lie across a turn —
   content is identity.

## THE PICK — M54k': the hook-shape run that PRINTS PASS

Do exactly ONE milestone, then stop. Do not re-verify closed work.

Acceptance (the ONLY thing that prints PASS; floors fail CLOSED):
`python3 scripts/m54a_check_run.py <trace> --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1`
on ONE unattended 6-turn run: `advanced 6/6`, year deltas `{1: 6}`, `stuck 0`, a `g->byte24`
line in the order mix, `bases_ours >= 2` at the END, and a `landed` carried move onto our own
base with `ordered_turn < landing turn` — AND the trace's `actions` contains `pre-arm:recN`
(setup read back `actionable: []`). Never weaken a floor. If it cannot pass, say so and merge
the documented negative with per-turn position read-backs (the watcher log).

**Shape (all four blockers removed):** an ODD-parity start tile (the game auto-targets Korolev
Center), **2-3 BFS steps** from it under the step table so it ARRIVES inside 6 turns yet still
multi-turn (`ordered_turn < landing turn`), passable per the flag byte, enemies 12+ tiles out.
From the 2152-2160 quiet window (22,41)/(21,41)/(20,41) qualified (man 7-9, BFS 3); re-census
first — the box is at **~2174, `bases_ours 2`** and the war is eating units.
`scratch/m54k_setup.py <from-tile> <target-tile>` pokes everything HELD, moves one unit to the
target, and reads back `actionable: []` + exactly one eligible held walker (it keys the walker
by TILE — record indices reshuffle mid-prep). Run the flag/parity/enemy scan (the snippet is
in SESSION_NOTES 89 / `scratch/m54k_watch.py` header) BEFORE picking the tile. Launch:
`smac_play.py --turns 6 --timeout 240 --no-escape 3000 --orders-per-turn 1 --verbose --tag
m54k_runN`; start `python3 scratch/m54k_watch.py 220 <x> <y>` alongside it (background=true) —
the watcher is what proves a walk, not the trace's prints. Reroll (a fresh setup + run) if a
comm lands in the order window (byte 88), if a turn record shows a +2 delta, or if the chooser
is never seen and the leg names a wrong-parity base.

## FIRST (nothing else)

1. Read `NEXT_PROMPT.md` in full — it is this file; it IS the footing.
2. `tail -90 SESSION_NOTES.md` — sessions 88 and 89 are the recent work. Never read the whole
   file (~75 KB).
3. `git status`; `git branch --show-current` (must be a branch, never `main`);
   `python3 scripts/milestone.py start M54k2` FIRST — it creates the branch off `origin/main`.
4. `python3 scripts/smac_state.py --json` — session 89 left the game LIVE near **2174**, pid
   1329211, `bases_ours 2`. If it reads impossibly, or a base is gone: reload per item 7 above.
5. `python3 scripts/m54d_census.py` — where our records and both bases are RIGHT NOW;
   `python3 scratch/m54h_clear.py` if any pane is up (Escape on `unknown`, Return on dialogs;
   never Escape twice at a clean HUD).

## WHERE THE KNOWLEDGE LIVES

- `ROADMAP.md` — S1..S7 with the exact acceptance for each. Read the row before committing.
- `ORDERS.md` — §1 key routing, §4 the byte table (`0x18` queued MOVE, legs `+20..+27` x /
  `+28..+35` y — a WAYPOINT the pump rewrites; the chooser's pick is the destination), §5 modal
  = key sink, §6 the in-loop contract, §7 WHEN the queued MOVE runs, §8 THE FOUNDING, §9 the
  chooser's rows, §10 SENTRY/HOLD + the diff/attribution rules, §11 WHO OWNS THE CURSOR, §12 THE
  STEP TABLE AND PARITY, **§13 THE AUTO-SENTRY + the in-phase reactivation contract + the
  opposite-parity-bases fact**. Session 89's four blockers are in SESSION_NOTES (an ORDERS §14
  is welcome).
- `SAVE_FORMAT.md` 150-182 — the 52-byte unit record (type u16@+10, owner@+14, order@+17,
  legs@+20..+35, mp-used@+40, flag dword@+4) and the 304-byte base record (x@0, y@2, faction
  LOW byte at +4).
- `data/alpha.json` — `UNITS` row 0 is a count, so **memory type = alpha index - 1**; class 8 =
  colonist (founding), class 3 = Scout Patrol.
- The live skill `~/.hermes/skills/smac-cvr-format/` (repo copy `skill/`): SKILL.md,
  `references/wine-operations.md`, `references/terraforming-order-path.md` (now incl. M54k).

## OPERATIONAL KIT

- Census / position: `m54d_census.py`; `scratch/m54k_setup.py [fx fy tx ty]` (all-held prep +
  read-back); `scratch/m54k_watch.py [secs x y]` (memory watcher, prints only changed
  (x,y,order,mp) multisets); `scratch/m54j_setup2.py` / `m54j_setup3.py` (the older shapes);
  `scratch/m54h_clear.py [N]`; `m54g_prep.py`; `m54a_load.py --relaunch` (SMAC_SAVE env = the
  BARE filename, item 7).
- Driver: `python3 scripts/smac_play.py --turns N --timeout 240 --no-escape 3000 --orders-per-turn 1 --verbose --tag <t>`.
  Turn records carry `orders` (with `dest`, `chooser_pick`, `walk_diff {attributed, confounded,
  claim, rivals, before_legs}`, `order_counts`, `attempts[].panes`) and `moves` (with `landed`,
  `carried`, `ordered_turn`, `dest_is_own_base`, `dest_count`/`src_count`, `mp_after`). A 6-turn
  run is ~1.5-4 min: background it, poll `grep -c '"turn"'` on the trace.
- Check: `python3 scripts/m54a_check_run.py <trace> --timeout 240 [--min-orders N] [--min-moves M]
  [--min-our-bases N] [--min-own-base-arrivals K]` — the ONLY thing that can print `PASS`; an
  own-base arrival MUST be multi-turn (`ordered_turn < landing turn`).
- Tests: `python3 scripts/test_walk_diff.py` -> `PASS 33/33 attribution cases`. Classifier
  gates: `scripts/test_classify.py` -> `PASS 17/17`; `scripts/check_classes.py` -> `frames: 17
  failures: 0`; **delete `evidence/**/_3x.png` right after**. `evidence/` is ~29.4/30 MB —
  check `python3 scripts/evidence.py budget` BEFORE adding frames; the sanctioned big artifact
  is `m53j_text.txt.gz` (keep; it is cited).
- Wine: prefix `./programs/prefix` == `~/.wine-smac32`, wine 10.20-staging-tkg at
  `~/tools/wine-10.20-staging-tkg-x86/bin/wine`, `DISPLAY=:99`, Xvfb :99 800x600x16.
  `pgrep -x terran.exe` (NEVER -f). Kill a driver run by the PID read from /proc cmdlines.

## TRAPS THAT COST A SESSION HOURS (all measured)

- **Check the flag byte before parking a unit anywhere** (item 1): impassable tiles swallow
  units whole. Check parity sums mechanically (opposite-parity bases: every tile matches one).
- **`g` targets Korolev Center first** (item 2): odd-parity starts only, or read the chooser.
- **A comm/pane mid-order eats the keys** (item 4) and a +2 year delta means the turn record
  spanned two rounds — reroll, do not reinterpret.
- **Auto-sentry + auto-advance** (§88 item 1, §89 item 6): order-0 units do NOT wait between
  rounds, and an all-HELD position advances itself at ~8 s/round.
- **A same-type headcount is not an arrival** (§88 item 3): our bases are crowded with
  identical units; identity is the leg worn.
- **Indices lie across a turn** (the array reshuffles AND GROWS — bases produce `+17 = 0` units
  onto their own tile). Content is identity; snapshot and diff.
- **OCR is ~1-15 s a poll and LIES about legibility** (item 6); poll the oracle (memory) at
  100 ms. The production-banner HUD frame classifies `unknown` — the blind gate handles it.
- **The pump eats the byte tens of ms after the OK** — sample THROUGH the click. Sentries
  (byte 1) move on their own every round and rewrite their legs; HOLD (2) is inert. `b` (and
  every order letter) is a MAP-level key while orders mode is off.
- **Escape at a clean HUD raises "Do you really want to quit?"**; never click its OK. Escape on
  the title screen exits. Arrows drive the MAP CURSOR; blind map clicks SCROLL. `--load` needs
  a Windows path. `sp.focus()` needs `sp.WIN = sp.find_window()` first.

## THE 10 RULES — condensed from sessions 75-89

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

1. Patch a `## Session 90` entry into `SESSION_NOTES.md` (acceptance numbers + the command that
   produced them + Next).
2. Rewrite `NEXT_PROMPT.md` for session 91, then `wc -c NEXT_PROMPT.md` (must be <= 15,500).
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
