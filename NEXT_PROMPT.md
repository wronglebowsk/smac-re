# NEXT_PROMPT — SMAC RE, session 77

Read IN FULL: this file. Open `FOOTING.md` ONLY if the milestone touches the production-vector
model — M54a does not. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53s, **M53t (done, session 76: the vector model is CLOSED
at 74/76 exact — do not reopen it)**. Open: **M54a (THE PICK)**. Roadmap position: Phase 1, spine S2
(solo turn advance); its exit is "the harness plays 40 turns unattended".

## First actions

1. `tail -60 ~/reverse/smac/SESSION_NOTES.md` — Session 76 is the latest milestone.
2. `git status`; `git branch` (never commit to main); `python3 scripts/milestone.py start M54a`.
3. Skill `smac-cvr-format`: `SKILL.md` whole (~19 KB). Open ONLY
   `references/wine-headless-harness.md` (turn automation, OCR/dialog state machine) and
   `references/wine-operations.md` (panes, coordinates, watchpoints). Skip `production-rebuild.md`.
4. Preflight: `pgrep -x terran.exe` (pid 2124624 at handoff), `/proc/<pid>/status` `TracerPid: 0`,
   `python3 scripts/smac_state.py --json` (year 2385, turn_no 0, idle, player 3).

## THE MILESTONE (M54a) — the driver must survive its own HUD

The bug, VERIFIED in session 75: `scripts/smac_play.py:230` returns `base` for ANY screen whose OCR
text contains a BASE_WORD (`"governor", "nutrients", "conquer", "discover"`, line 36), and it does so
BEFORE the dialog geometry tests. The HUD message pane prints news lines containing "nutrients", so
every frame of that position classified `base`; with `--no-escape N` > `--timeout` the Escape that
would clear it is forbidden → two STUCK runs, zero hits. Session 75 hand-drove the round instead
(recipe in `evidence/m53s_findings.md`, "Driving" bullet; `evidence/m53s_endturn.py`,
`evidence/m53s_barclick.py`).

Acceptance, all three:

- A HUD-only screen (message-pane text, TURN COMPLETE visible at y≈416) classifies `hud`, and a real
  base screen still classifies `base`. Pin BOTH as a unit-level test on saved screenshots — the
  classifier test needs no live game.
- `--turns 40` advances 40 turns with no human and no vision in the loop: no STUCK longer than
  2×timeout, the state reader's year advances exactly once per turn, and a trace file is written per
  run (seed, action log, per-turn state deltas).
- The panes that blocked the round are handled by the driver, not by hand: "Do you really want to end
  the turn now?" (Yes), the Council PROPOSAL vote (bars x=311/400/489, y≈498 — find them by COLOUR
  GEOMETRY; `tesseract tsv` returns nothing for those labels on this build), and the HIVE bribe pane
  (Escape closes it, Return advances).

Traps that cost sessions: NEVER press Escape on the title screen (it selects "Exit"); the "Do you
really want to quit?" dialog's Escape returns to "Oops, no, wait!", its OK exits the game and the
process vanishes silently, and its banner IS the game title so a naive classifier calls it `title`.

## Operational kit

- `scripts/smac_play.py --turns N --timeout S --no-escape S --tag <id> [--verbose]`. `--no-escape N`
  = "never press Escape during the first N seconds". Bound a backgrounded run with a shell `timeout`;
  this checkout has NO `--mode stop`. Never signal by name (`pkill -f` matches your own argv):
  `ps -p <pid>`, kill that exact pid.
- Capture: `xwd -display :99 -root -silent` (`DISPLAY=:0` is blank), `ffmpeg -i f.xwd -vf
  crop=800:600:0:0 -y f.png`. Window is 10485761, 800x600 at root 0,0 ⇒ root-capture pixels ARE
  window coords. `tesseract <png> tsv` and `--psm 6` return nothing here — use
  `smac_play.ocr_fast()`. Dark-labelled bars: colour geometry (b>120, r,g>90, |r-g|<40, b-r>25,
  run > 55 px over >= 12 scanlines), not OCR.
- State: `scripts/smac_state.py --json` reads `/proc/<pid>/mem`, so a passing turn needs no
  screenshot. Watchpoints: 4 hw slots, fire on VALUE CHANGE and name the NEXT instruction, bake
  addresses in code, `stdbuf -o0`, drive + snapshot in ONE backgrounded job (`scripts/m53n_drive.py`).
- Stalled round? `python3 scripts/m53q_livelock.py` (turn_flags + `+48`/`+50` chain census, `--fix`).
  Session 75 read CLEAN — those stalls were UI modals, not livelock.

## Rules

- ONE milestone, then stop. Ending the turn is the deliverable.
- Order the ending exactly: gate GREEN → `SESSION_NOTES.md` entry (patch, never a rewrite) →
  **checkpoint commit** → `NEXT_PROMPT.md` rewrite then `wc -c` (<=15,500 B) → `submit --title …` →
  `gh pr checks` → `merge`. The commit goes BEFORE the prompt rewrite: that rewrite is the largest
  generation of a turn and its arguments re-enter the prompt.
- `python3 scripts/gate.py --base main` must be GREEN before submit. After editing the live skill,
  copy `SKILL.md` and `references/` into `skill/` or the sync check fails.
- Keep tool results small: `scripts/evidence.py show <file>:<line>`, `tail` not whole files,
  `scripts/index.py search "<question>"` before any grep across the corpus.

## Milestone options (pick ONE)

- **M54a — classifier fix + the three panes + 40 unattended turns (THE PICK).** The classifier test is
  cheap; the pane state machine is the body of the work; 40 turns is the assertion.
- If the panes turn out to be a second system, split: M54a (classifier + HUD test) then M54b (pane
  automation) — and say so in the notes instead of relabelling a partial as done.
- After M54a: ROADMAP Phase 2 spines — S3 unit orders/combat, then S4 tech — toward G1.
- **Background, NOT a queue** (`references/open-leads.md` → "Parked"): the two open M53 rows (idx 6,
  51; two-pass `FUN_004f5a70`), `DAT_008f0d40` consumers, `unit+24/25`, `base+0x84`, etc. Reopen only
  if a milestone needs the bit-exact vector. Retired premises: `FOOTING.md` → "Retired premises".

## Report style

One screen: what changed, the acceptance numbers with the exact command that produced them, what is
still open, and the next pick. Cite `evidence/<file>:<line>`.
