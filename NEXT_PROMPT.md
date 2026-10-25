# NEXT_PROMPT — SMAC RE, session 79

Read IN FULL: this file. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this), STOP.
Open `FOOTING.md` or `skill/references/production-rebuild.md` only if the milestone touches the
production-vector model — M54b does not.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53t (**vector model CLOSED at 74/76 exact — do not
reopen**), **M54a (CLOSED, sessions 77+78: the classifier survives its own HUD, the driver answers
the round's panes, and ONE `--turns 40` invocation advanced 40 turns with the year +1 on each and
zero stalls — `evidence/trace_m54a40p_20261024_204555.jsonl`, checked by
`scripts/m54a_check_run.py` → `advanced 40/40`, `stuck 0`, max dt 109 s, PASS/exit 0)**. Open:
**M54b (THE PICK) — the same 40 turns on a RESUMED campaign.** Roadmap position: Phase 1, spine S2
(solo turn advance); its exit is "the harness plays 40 turns unattended", which is now green on a
fresh game and blocked on a loadable position.

## ⚠ FIRST: the position on the box is a FRESH game, not Paul's campaign

`python3 scripts/smac_state.py --json` reads a live, responsive game: **year ~2150, n_bases 18,
player 3, cur_player 3**, win 10485761 (800x600 at root 0,0, `xwd -display :99`). It is a
TALENT/STANDARD/SMALL game session 78 started at 2100 to get the 40-turn proof.

Session 77's campaign (2416, 79 bases) exists ONLY in save files, and **every one of them resumes
HUNG**: all eight `programs/saves/auto/Alpha Centauri Autosave N.SAV` (years 2390-2415) and
`programs/Alpha Centauri Autosave 1.SAV` (2416). Symptom, measured three times on session 78:
`turn_flags` bit1 (0x2) set, the terran.exe main thread `R` at ~90 % CPU with the llvmpipe workers
idle and every other thread in `futex_do_wait`, the screen pixel-identical for 9+ minutes, and NO
input reaching the game (MENU clicks, Return, Escape, `xdotool click --window`, `key --window` all
give zero pixel change). `sema_done`/`sema_mp` read 0, so it is not the MP semaphore. The load
itself completes (n_bases settles 79 → 75 on the 2390 slot) and then the turn loop spins.

**Decide M54b's shape in your first 20 tool calls** by testing whether a save written at a CLEAN
point reloads live: from the live HUD open the menu, save the game, reload it with
`scripts/m54a_load.py`, and check `turn_flags & 2` + a 5 s pixel-diff + a MENU click. If a clean
save reloads live, the finding is "autosaves taken mid-end-turn resume hung; save at a clean point"
and M54b is the 40 turns on the resumed campaign. If even a clean save hangs, M54b is the driver's
load/title guard plus pane-scoped clicks, and the campaign resume goes to `references/open-leads.md`
as a background lead — say which one it is in the notes, do not relabel a partial.

## First actions

1. `tail -60 ~/reverse/smac/SESSION_NOTES.md` — Session 78 is the latest milestone.
2. `git status`; `git branch` (never commit to main); `python3 scripts/milestone.py start M54b`
   (it refuses a dirty worktree — commit or stash first).
3. Skill `smac-cvr-format`: `SKILL.md` whole. Open ONLY `references/wine-headless-harness.md`
   (the screen-class table) and `references/wine-operations.md` (panes, coordinates). Skip
   `production-rebuild.md`.
4. `pgrep -x terran.exe` + `/proc/<pid>/status` `TracerPid: 0`, then the clean-save test above.

## THE MILESTONE (M54b) — 40 unattended turns on a RESUMED game

Acceptance, all three:

- `--turns 40` in ONE invocation advances 40 turns from a LOADED save: check with
  `python3 scripts/m54a_check_run.py evidence/trace_<tag>_<ts>.jsonl --timeout <S>` — it prints
  `turns / advanced / year deltas / stuck / max dt` and exits non-zero on any failure. Session 78's
  green run is the template: 40/40, `{1: 40}`, `stuck 0`, max dt 109 s.
- The load is answered by the DRIVER, not by a human: a `load` step that clicks the browser's OK
  bar (Return in the name box only SELECTS the file), the LOAD-confirm OK, the ops-director modal,
  and a **wedge guard** — two captures 5 s apart with no change plus a MENU click that changes
  nothing means a bad slot, so the driver must report it and stop, not burn the turn budget.
  `scripts/m54a_load.py` already implements all of this outside the driver; fold it in or call it.
- Session 78's wins stay green after every change: `python3 scripts/test_classify.py` →
  **PASS 10/10 screen classifications** and `python3 scripts/check_classes.py` →
  **frames: 10 failures: 0**. Any new screen class gets a saved-screenshot row in BOTH files
  before it goes in the driver.

## Operational kit

- `scripts/smac_play.py --turns N --timeout S --no-escape S --tag <id> [--verbose]`; bound a
  backgrounded run with a shell `timeout` and poll `scripts/smac_state.py --json` (it reads
  `/proc/<pid>/mem`, so a passing turn needs no screenshot). Session 78's pace on a fresh game was
  10-30 s per turn; the campaign pace is slower. This checkout has NO `--mode stop`. Never signal
  by name: `ps -p <pid>`, kill that exact pid.
- Capture: `xwd -display :99 -root -silent` (`DISPLAY=:0` is blank) + `ffmpeg -vf crop=800:600:0:0`.
  Root pixels ARE window coords (the game window is 800x600 at 0,0 inside the Wine desktop window).
  `tesseract tsv`/`--psm 6` return nothing useful — use `smac_play.ocr_fast()` (~1-8 s per frame,
  load-dependent, and much worse under load). `smac_play.ocr()` writes its 2× sibling NEXT TO the
  input: OCR evidence PNGs from a scratch copy or you litter `evidence/`.
- **`find()` matches ONE OCR token.** Phrase probes (`['turn complete']`, `['make random']`,
  `['load game']`) return None even when the words are on screen; probe `('turn','make','ok')`.
- Bars: **band + column density, never a run** (`pane_bars`) — the purple fill (103,91,181) is
  dithered every other scanline and the label sits inside the bar. A 3-bar row is a VOTE only in
  y 460-520 (Council YEA/NAY/ABSTAIN at 311/400/489, y 498); advisory panes' bar rows are y 219-310
  and take `Return`; a bottom bar at y ≥ 560 on a `movie`/`unknown` frame is a Replay/Close bar.
  **A `movie` frame with NO detectable bar is a Secret Project clip** (red Close bar, e.g. (690,577)
  on `evidence/m54a/movie_oracle.png`): it takes `Return`, and `handle_pane` now sends it.
- Measured geometry: LOAD browser NAME field (406,527), OK (330,552), CANCEL (482,552); title rows
  START (580,111), SCENARIO (610,269), LOAD (579,344); TURN COMPLETE button region (520,375,280,90);
  LOAD-confirm OK (290,391); ops-director row (400,307) then OK (400,362).
- Classes the driver must never confuse (all pinned in `scripts/test_classify.py`): the quit dialog
  is `quit-prompt` (Escape = "Oops, no, wait!"), NOT `title`; the HELP browser is `help` (only its
  EXIT bar (525,344) closes it); the HUD's message pane may print `nutrients` — that is still `hud`.
- Traps: NEVER press Escape on the title screen (it selects "Exit"); the quit dialog's OK exits the
  game and the process vanishes; `pkill -f`/kill-by-name matches your own argv (use the
  `terran.ex[e]` bracket form); never run a second OCR/ffmpeg job while a driven run is live.
- Stalled round? `python3 scripts/m53q_livelock.py`. A spin with a static screen and dead input is
  a WEDGED GAME, not a stall — check it before spending a turn timeout on it.

## Rules

- ONE milestone, then stop. Ending the turn is the deliverable.
- Order the ending exactly: `python3 scripts/gate.py --base main` GREEN → `SESSION_NOTES.md` entry
  (patch, never a rewrite) → **checkpoint commit** → `NEXT_PROMPT.md` rewrite then `wc -c`
  (<=15,500 B) → `milestone.py submit --title …` → `gh pr checks` → `milestone.py merge`.
- Commit EARLY: as soon as the milestone's test passes (and no later than ~60 tool calls). A commit
  on the branch is the only thing that survives a context overflow.
- After editing the live skill, copy `SKILL.md` and `references/` into `skill/` or the sync check
  fails (`cp ~/.hermes/skills/smac-cvr-format/SKILL.md skill/ && cp ~/.hermes/skills/smac-cvr-format/references/*.md skill/references/`).
- Keep tool results small: `scripts/evidence.py show <file>:<line>`, `tail` not whole files,
  `scripts/index.py search "<question>"` before any grep across the corpus.
- Gate citations: any `evidence/<file>:<line>` in changed Markdown must resolve, so only cite line
  numbers you have verified; plain paths (no `:line`) are always safe.

## Milestone options (pick ONE)

- **M54b — 40 unattended turns on a resumed game (THE PICK).** Body: the driver's load step +
  wedge guard, pane-scoped clicks (a click must land inside the modal being answered — session 77's
  run ended in the HELP then LOAD browsers), and the round-aware turn budget (service the round
  until the year flips instead of aborting at 2 consecutive stalls). If the clean-save test says a
  resumed game still wedges, deliver M54b as "the driver loads and plays N turns from a save, zero
  human input, and the blocker named" — say so in the notes instead of relabelling a partial.
- After M54b: ROADMAP Phase 2 spines — S3 unit orders/combat, then S4 tech — toward G1.
- **Background, NOT a queue** (`references/open-leads.md` → "Parked"): the two open M53 rows (idx 6,
  51; two-pass `FUN_004f5a70`), `DAT_008f0d40` consumers, `unit+24/25`, `base+0x84`, and now the
  hung-resume question (why a save with `turn_flags` bit1 set spins after load). Reopen only if a
  milestone needs the bit-exact vector. Retired premises: `FOOTING.md` → "Retired premises".

## Report style

One screen: what changed, the acceptance numbers with the exact command that produced them, what is
still open, and the next pick. Cite `evidence/<file>:<line>`.
