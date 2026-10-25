# NEXT_PROMPT — SMAC RE, session 80

Read IN FULL: this file. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this), STOP.
Open `FOOTING.md` or `skill/references/production-rebuild.md` only if the milestone touches the
production-vector model.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53t (**vector model CLOSED at 74/76 exact — do not
reopen**), M54a (CLOSED, sessions 77+78), **M54b (CLOSED, session 79: ONE `--turns 40` invocation
relaunched the game, LOADED `programs/saves/m54b_clean.SAV` (2150) with zero human input, and
advanced 40 turns with the year +1 on each and zero stalls — `evidence/trace_m54b40b_20261024_212833.jsonl`,
checked by `scripts/m54a_check_run.py` → `advanced 40/40`, `{1: 40}`, `stuck 0`, max dt 51.5 s,
PASS/exit 0)**. Also settled in session 79: **a save written at a CLEAN point resumes LIVE**
(animating HUD, `turn_flags 0`, responsive MENU), so session 78's eight hung autosaves are
artifacts of saving while `turn_flags` bit1 is set — mid-end-turn saves, not a format wall.
Open: **S3 (THE PICK) — unit orders + combat in the unattended loop.** Spine S2 ("harness plays
40 turns unattended") is GREEN on a loaded save; Phase 2 starts at S3.

## ⚠ FIRST: the position on the box

`python3 scripts/smac_state.py --json` reads a live, responsive game — last seen **year 2190,
n_bases 26, player 3, cur_player 7 (AI mid-round), turn_flags 0x100002**, pid 373089 (800x600 at
root 0,0, `xwd -display :99`). It is the FRESH TALENT/STANDARD lineage session 78 started; the
reproducible start point is `programs/saves/m54b_clean.SAV` (2150, 18 bases), which the driver
loads itself via `--load`. Paul's 2416 campaign exists ONLY in mid-end-turn autosaves that resume
hung — a parked lead (see Rules), not a milestone unless you pick the alternative below.

## First actions

1. `tail -60 ~/reverse/smac/SESSION_NOTES.md` — Session 79 is the latest milestone.
2. `git status`; `git branch` (never commit to main); `python3 scripts/milestone.py start <ID>`
   (it refuses a dirty worktree — commit or stash first).
3. Skill `smac-cvr-format`: `SKILL.md` whole. Open ONLY `references/wine-headless-harness.md`
   (the screen-class table) and `references/wine-operations.md` (panes, coordinates — now incl.
   the M54b menu/save geometry). Skip `production-rebuild.md` unless the pick touches combat math.
4. `ROADMAP.md` — the S3 exit gate and the Phase 2 gates. **Decide the milestone shape in your
   first 20 tool calls**, and say in the notes which shape you took.
5. `pgrep -x terran.exe` + `/proc/<pid>/status` `TracerPid: 0`.

## THE MILESTONE (pick ONE)

- **S3 — orders + combat in the unattended loop (THE PICK).** The 40-turn driver never MOVES a
  unit: `give_order()` (verified M32-M33 — poke the selection global, issue a REAL hotkey, service
  the payment modal, verify the `unit+17` write) runs only via `--order`. Body: fold a per-turn
  order step into `service_turn`'s own-phase window — pick a waiting unit from
  `scripts/smac_unitpos.py` snapshots, issue a keyboard order, and VERIFY the write by memory diff
  (never claim an order without the +17/position delta; the record list compacts, identity is not
  record index). Acceptance: ONE `--turns 40` invocation (fresh or `--load`) where the trace shows
  a handful of VERIFIED orders (records carrying the memory-confirmed delta) and the year still
  advances every turn with `stuck 0` per `scripts/m54a_check_run.py` — or whatever sharper exit
  gate `ROADMAP.md` gives S3; do not weaken it. Session 79's wins stay green after every change:
  `python3 scripts/test_classify.py` → **PASS 10/10** and `python3 scripts/check_classes.py` →
  **frames: 10 failures: 0**. Any new screen class gets a saved-screenshot row in BOTH files
  before it goes in the driver.
- Alternative (smaller): close the mid-end-turn autosave question — instrument why a save with
  bit1 set spins after load (`scripts/m53q_livelock.py` census first; the `unit+48/50` chain lead),
  then either make one 2390-2416 slot resume live or write the verdict into
  `references/open-leads.md`.
- After S3: S4 tech — toward G1.

## Operational kit

- `scripts/smac_play.py --turns N --timeout S --no-escape S --tag <id> [--verbose] [--load 'Z:\path.SAV']`.
  `--load` = relaunch if no window, then walk title -> LOAD GAME row -> blind browser -> LOAD
  confirm -> ops-director itself (via `scripts/m54a_load.py`); a resume that is HUD-static AND
  MENU-dead exits 5 as **WEDGE (bad slot), not stalled**. `--no-escape N` suppresses Escape for
  the first N s — EXCEPT quit-prompt and base, which Escape unconditionally (M54b). Bound a
  backgrounded run with a shell `timeout` (40 turns ≈ 10-20 min at 2150-2190), then poll
  `scripts/smac_state.py --json` — it reads `/proc/<pid>/mem`, so a passing turn needs no
  screenshot. This checkout has NO `--mode stop`. Never signal by name: `ps -p <pid>` or
  `pgrep -x terran.exe`, kill that exact pid.
- Capture: `xwd -display :99 -root -silent` (`DISPLAY=:0` is blank) + `ffmpeg -vf crop=800:600:0:0`.
  Root pixels ARE window coords (the game window is 800x600 at 0,0). `tesseract tsv`/`--psm 6`
  return little on raw frames — use `smac_play.ocr_fast()` (~1-8 s/frame, much worse under load);
  `smac_play.ocr()` writes its 3x sibling NEXT TO the input file. **White-on-dark menus OCR as
  garbage — read them with vision on the capture** (session 79 did).
- **`find()` matches ONE OCR token.** Phrase probes (`['turn complete']`) return None even when
  the words are on screen; probe `('turn','make','ok')`.
- Geometry (all measured live): console MENU (61,369) -> dropdown GAME (30,186) -> submenu
  Save Game (200,331), Load Game (200,353), Quit Ctrl+Q (170,428). SAVE browser NAME (406,304),
  OK (330,327), CANCEL (482,327); LOAD browser NAME (406,527), OK (330,552), CANCEL (482,552) —
  Return in a name box only SELECTS, click OK; saves land in the browser's last-used dir unless
  you type the full `Z:\` path. Title rows START (580,111), SCENARIO (610,269), LOAD (579,344);
  TURN COMPLETE region (520,375,280,90); LOAD-confirm OK (290,391); ops-director row (400,307)
  then OK (400,362).
- Bars: **band + column density, never a run** (`pane_bars`) — the purple fill (103,91,181) is
  dithered every other scanline and the label sits inside the bar. A 3-bar row is a VOTE only in
  y 460-520 (Council YEA/NAY/ABSTAIN at 311/400/489, y 498); advisory panes' bar rows are y
  219-310 and take `Return`; a bottom bar at y ≥ 560 on a `movie`/`unknown` frame is a
  Replay/Close bar — `dialog` frames are NOT bar-clicked (M54b pane-scoping). A `movie` frame
  with NO detectable bar is a Secret Project clip: it takes `Return`.
- Classes the driver must never confuse (pinned in `scripts/test_classify.py`): the quit dialog
  is `quit-prompt` (Escape = "Oops, no, wait!"), NOT `title`; the HELP browser is `help` (only
  its EXIT bar (525,344) closes it); the HUD's message pane may print `nutrients` — that is still
  `hud` (positional test, MSGPANE (0,425,800,600)); **`base` closes with Escape even under
  `--no-escape`** — it is legitimately byte-static, never a wedge.
- Wedge vs stall: HUD byte-static 15 s+ with a dead MENU click = WEDGE (the driver exits 5 and
  says so). Static modals are normal. A stalled round? `python3 scripts/m53q_livelock.py`.
- Traps: NEVER press Escape on the title screen (it selects "Exit"); the quit dialog's OK exits
  the game; `pkill -f`/kill-by-name matches your own argv (bracket form `terran.ex[e]` only);
  never run a second OCR/ffmpeg job while a driven run is live; img crop args are (x, y, w, h).

## Rules

- ONE milestone, then stop. Ending the turn is the deliverable.
- Order the ending exactly: `SESSION_NOTES.md` entry (patch, never a rewrite) + `NEXT_PROMPT.md`
  rewrite (then `wc -c` — **<=15,500 bytes**) → **checkpoint commit** → `python3 scripts/gate.py
  --base main` GREEN (its checkpoint check needs BOTH docs updated) → `milestone.py submit
  --title …` → `gh pr checks <n>` → `milestone.py merge <n>`. Commit EARLY: as soon as the
  milestone's test passes (and no later than ~60 tool calls). A commit on the branch is the only
  thing that survives a context overflow.
- After editing the LIVE skill, copy `SKILL.md` **and** `references/` into `skill/` or the sync
  check fails (`cp ~/.hermes/skills/smac-cvr-format/SKILL.md skill/ && cp ~/.hermes/skills/smac-cvr-format/references/*.md skill/references/`).
- Keep tool results small: `scripts/evidence.py show <file>:<line>`, `tail` not whole files,
  `scripts/index.py search "<question>"` before any grep across the corpus.
- Gate citations: any `evidence/<file>:<line>` in changed Markdown must resolve, so only cite
  line numbers you have verified; plain paths (no `:line`) are always safe.

## Report style

One screen: what changed, the acceptance numbers with the exact command that produced them, what is
still open, and the next pick. Cite `evidence/<file>:<line>`.
