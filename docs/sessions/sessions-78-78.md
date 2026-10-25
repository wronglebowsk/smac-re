# Session notes archive — sessions 78-78

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 78 (2026-10-24) — M54a: **THE 40-TURN RUN PASSES — ON A FRESH GAME; EVERY SAVE SESSION 77 LEFT RESUMES HUNG**
- **THE ACCEPTANCE IS MET.** One invocation, nobody at the keyboard:
  `python3 scripts/smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54a40p --verbose`
  checked with `python3 scripts/m54a_check_run.py evidence/trace_m54a40p_20261024_204555.jsonl
  --timeout 240` → `turns 40 records, header asked for 40`, **`advanced 40/40`, year deltas
  `{1: 40}`** (the year moves +1 on every turn), **`stuck 0 (turns [])`, max dt 109.0 s, none over
  2×240 s**, per-turn state deltas present, `PASS …`, exit 0. Position 2110 → 2150, n_bases 13 → 18.
  Session 77's best single invocation was 12 turns; the gap was endurance, and the endurance blocker
  was a screen the driver refused to close (next bullet), not the classifier.
- **One driver fix made it possible: Secret Project movies do not have a detectable Close bar.**
  The Oracle clip (`evidence/m54a/movie_oracle.png`) draws a **red** Close bar at (690,577);
  `pane_bars` looks for the purple push-bar fill (103,91,181), reports no bars, `handle_pane`
  returned False, and the run sat 150 s on `movie` frames at 2109. `Return` closes the clip —
  verified live (the frame changed over the whole 800x600 on Return and the driver resumed) — so
  `handle_pane` now presses Return on a bar-less `movie` frame; the battle REPLAY keeps its own
  bottom-bar path (it has a purple bar `pane_bars` sees). Classification is untouched:
  `python3 scripts/test_classify.py` → **PASS 10/10 screen classifications**;
  `python3 scripts/check_classes.py` → **frames: 10 failures: 0**.
- **THE CAMPAIGN POSITION IS UNRESUMABLE — that is M54b's real blocker.** Every save session 77
  left (all eight `programs/saves/auto/` autosaves, years 2390-2415, and
  `programs/Alpha Centauri Autosave 1.SAV`, 2416) loads and then HANGS: `turn_flags` bit1 (0x2)
  set, the main thread `R` at ~90 % CPU with the llvmpipe workers idle and every other thread in
  `futex_do_wait`, the screen pixel-identical for 9+ min, and **no input reaches the game** — MENU
  clicks, Return, Escape, `xdotool click --window` and `key --window` all produce zero pixel
  change. `sema_done`/`sema_mp` read 0, so it is not the MP semaphore; the load itself does finish
  (n_bases settles 79 → 75 after loading the 2390 slot) and then the turn loop spins. The 40-turn
  proof therefore had to run on a NEW game: `scripts/m54a_newgame.py` walks START (580,111) →
  MAKE RANDOM MAP → SMALL planet → TALENT → STANDARD rules → intro text (Return) → faction → HUD
  at 2100. Fresh games are FAST (~10-30 s per turn at 2110-2150) and threw no pane the driver
  could not answer (`pane hits {}`; actions were hud 61, unknown 25, ai-phase 31,
  confirm-after-press 40, close-bar 5, dialog 2, base 1).
- **LOAD browser geometry, measured live** (`evidence/m54a/load_browser.png`): NAME field
  (406,527), OK bar (330,552), CANCEL bar (482,552). The browser opens at the last-used directory
  with the last filename pre-filled even in a fresh process (registry), and **Return in the name
  box only SELECTS the file — the load needs the OK bar clicked**. OCR reads neither the LOAD
  banner nor the bars (dithered, label inside), so `scripts/m54a_load.py` walks the browser blind;
  `m48d_boot.py`'s `"load game" in body and "name" in body` test never fires on this build, which
  is why session 77's boot sat 240 s at the title. Title rows: START (580,111), SCENARIO (610,269),
  LOAD (579,344). `find()` matches ONE OCR token, so phrase probes (`['turn complete']`,
  `['make random']`) return None even when the words are on screen.
- **State of the box:** the game is a FRESH TALENT/STANDARD game at ~2150 (n_bases 18), live and
  responsive, still up on win 10485761. Session 77's 2416 campaign exists only on those hung saves.
- **Next:** **M54b.** The 40-turn assertion is green on a fresh game; what is left is a resumed
campaign (load at the title, then check `turn_flags & 2` and treat a spinning main thread as a
bad slot rather than a stall), pane-scoped clicks (session 77's run ended in the HELP then LOAD
browsers), and the round-aware turn budget.
