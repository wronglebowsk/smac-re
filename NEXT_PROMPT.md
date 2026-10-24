# NEXT_PROMPT — SMAC RE, session 78

Read IN FULL: this file. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this), STOP.
Open `FOOTING.md` or `skill/references/production-rebuild.md` only if the milestone touches the
production-vector model — M54b does not.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53t (**vector model CLOSED at 74/76 exact — do not
reopen**), **M54a (done, session 77: the classifier survives its own HUD and the driver answers the
round's panes)**. Open: **M54b (THE PICK) — the 40 unattended turns.** Roadmap position: Phase 1,
spine S2 (solo turn advance); its exit is "the harness plays 40 turns unattended".

## ⚠ FIRST: the game is NOT in a session

pid 2124624 is alive (win 10485761, 800x600 at root 0,0, `xwd -display :99`) but session 77's last
run left it at the **title menu** — `scripts/smac_state.py --json` reads `n_bases: 0`,
`cur_player: 0`, `turn_flags: 0` there, and `year` is meaningless until a game is loaded.
`evidence/m54a/after_cancel.png` is that screen (`start game / scenario / load game / …`).
The position is NOT lost: the game autosaves to `programs/saves/auto/Alpha Centauri Autosave N.SAV`
(newest 19:05, 2416-era) and `programs/Alpha Centauri Autosave 1.SAV` (19:08).

**Load it before driving anything**: `scripts/m48d_boot.py` is the proven boot + LOAD path (its
post-load modal is a row at ~(400,307) then OK (400,362)); the LOAD file browser is the pane with
OK (299,560-ish row) and CANCEL (478,560) — clicking its OK on a folder does nothing and the driver
will happily click it 20×. Expect `scripts/smac_state.py --json` to show a real year, `player 3`
and `n_bases ~79` before you call the load done. Say in the notes what year you resumed at.

## First actions

1. `tail -60 ~/reverse/smac/SESSION_NOTES.md` — Session 77 is the latest milestone.
2. `git status`; `git branch` (never commit to main); `python3 scripts/milestone.py start M54b`.
3. Skill `smac-cvr-format`: `SKILL.md` whole. Open ONLY `references/wine-headless-harness.md`
   (the screen-class table, updated with M54a's positional base test) and
   `references/wine-operations.md` (panes, coordinates, the M54a bar-geometry bullet). Skip
   `production-rebuild.md`.
4. `pgrep -x terran.exe` + `/proc/<pid>/status` `TracerPid: 0`, then the load step above.

## THE MILESTONE (M54b) — the driver plays 40 turns with nobody at the keyboard

Acceptance, all three:

- `--turns 40` in ONE invocation advances 40 turns: the state reader's year moves +1 per turn, no
  STUCK longer than 2× the per-turn timeout, and the run's trace file carries the seed header, the
  action log and the per-turn state delta. Check it with
  `python3 scripts/m54a_check_run.py evidence/trace_<tag>_<ts>.jsonl --timeout <S>` — it prints the
  numbers and exits non-zero. Session 77's best single invocation was 12 turns
  (`evidence/trace_m54a40c_20261024_173521.jsonl` era, `evidence/m54a/run40h.log:1`); 29 turns
  advanced across 9 invocations, so the gap is endurance, not classification.
- The stall causes session 77 actually hit must be fixed, not papered over: (a) the two-consecutive
  stall abort fires while a legitimate long round (Council deliberation, battle **Replay**, Secret
  Project movie) is still running — the turn loop must keep servicing until the round flips, not
  give up at a fixed wall clock; (b) the driver clicked a bar that did not belong to the pane it was
  answering and ended up in the HELP browser and then the LOAD browser at the title — a click must
  be inside the pane's own panel; (c) OCR latency: never run a second OCR/ffmpeg job while a driven
  run is live (one turn burned 355 s on ~1 OCR pass per iteration when the box was shared).
- Keep session 77's wins: `python3 scripts/test_classify.py` stays **PASS 10/10** and
  `python3 scripts/check_classes.py` stays **frames: 10 failures: 0** after every change. Any new
  screen class gets a saved-screenshot row in BOTH files before it goes in the driver.

## Operational kit

- `scripts/smac_play.py --turns N --timeout S --no-escape S --tag <id> [--verbose]`; bound a
  backgrounded run with a shell `timeout`; the run is 40-70 minutes at this position, so budget the
  wall clock and poll the state reader — do not hold a foreground call open on it. This checkout has
  NO `--mode stop`. Never signal by name: `ps -p <pid>`, kill that exact pid.
- Capture: `xwd -display :99 -root -silent` (`DISPLAY=:0` is blank) + `ffmpeg -vf crop=800:600:0:0`.
  Root pixels ARE window coords. `tesseract tsv`/`--psm 6` return nothing useful — use
  `smac_play.ocr_fast()` (~1-8 s per frame, load-dependent). `smac_play.ocr()` writes its 2× sibling
  NEXT TO the input: OCR evidence PNGs from a scratch copy or you litter `evidence/` (see
  `scripts/m54a_ocrscan.py` and `scripts/test_classify.py` for the pattern).
- Bars: **band + column density, never a run** (`pane_bars`) — the fill (103,91,181) is dithered on
  every other scanline and the label sits inside the bar. A 3-bar row is a VOTE only in y 460-520
  (Council YEA/NAY/ABSTAIN at 311/400/489, y 498); advisory panes' bar rows are y 219-310 and take
  `Return`; a bottom bar at y ≥ 560 on a `movie`/`unknown` frame is a Replay/Close bar.
- Classes the driver must never confuse (all pinned in `scripts/test_classify.py`): the quit dialog
  is `quit-prompt` (Escape = "Oops, no, wait!"), NOT `title`; the HELP browser is `help` (only its
  EXIT bar (525,344) closes it); the HUD's message pane may print `nutrients` — that is still `hud`.
- Traps: NEVER press Escape on the title screen (it selects "Exit"); the quit dialog's OK exits the
  game and the process vanishes; `pkill -f`/kill-by-name matches your own argv; Escape on the
  "Do you really want to quit?" is safe, OK is not.
- Stalled round? `python3 scripts/m53q_livelock.py` (session 75 read CLEAN — those stalls were UI
  modals). `scripts/smac_state.py --json` reads `/proc/<pid>/mem`, so a passing turn needs no
  screenshot.

## Rules

- ONE milestone, then stop. Ending the turn is the deliverable.
- Order the ending exactly: `python3 scripts/gate.py --base main` GREEN → `SESSION_NOTES.md` entry
  (patch, never a rewrite) → **checkpoint commit** → `NEXT_PROMPT.md` rewrite then `wc -c`
  (<=15,500 B) → `milestone.py submit --title …` → `gh pr checks` → `milestone.py merge`.
- After editing the live skill, copy `SKILL.md` and `references/` into `skill/` or the sync check
  fails (`cp ~/.hermes/skills/smac-cvr-format/SKILL.md skill/ && cp ~/.hermes/skills/smac-cvr-format/references/*.md skill/references/`).
- Keep tool results small: `scripts/evidence.py show <file>:<line>`, `tail` not whole files,
  `scripts/index.py search "<question>"` before any grep across the corpus. Commit early — a commit
  on the branch is the only thing that survives a context overflow.
- Gate citations: any `evidence/<file>:<line>` in changed Markdown must resolve, so only cite line
  numbers you have verified; plain paths (no `:line`) are always safe.

## Milestone options (pick ONE)

- **M54b — 40 unattended turns (THE PICK).** Body: the round-aware turn budget (service the round
  until the year flips instead of aborting at a fixed timeout), pane-scoped clicks (a click must
  land inside the modal being answered), and a driver load/title-screen guard. Acceptance is the
  `m54a_check_run.py` line above, green on a single 40-turn trace.
- If 40 turns still will not close, M54b may be delivered as "N turns in one invocation, zero human
  input, and the specific blocker named" — say so in the notes instead of relabelling a partial.
- After M54b: ROADMAP Phase 2 spines — S3 unit orders/combat, then S4 tech — toward G1.
- **Background, NOT a queue** (`references/open-leads.md` → "Parked"): the two open M53 rows (idx 6,
  51; two-pass `FUN_004f5a70`), `DAT_008f0d40` consumers, `unit+24/25`, `base+0x84`. Reopen only if
  a milestone needs the bit-exact vector. Retired premises: `FOOTING.md` → "Retired premises".

## Report style

One screen: what changed, the acceptance numbers with the exact command that produced them, what is
still open, and the next pick. Cite `evidence/<file>:<line>`.
