# Session notes archive — sessions 105-105

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 105 (2026-10-26) — M65: THE SCREEN READ IS A LOOK LOOP, NOT AN OCR COIN-FLIP. The HUD has two rows and only the bottom one is stable.

### What changed (harness only — no threshold, floor or prediction term moved; `classify()` itself is UNTOUCHED, so the driver classifies exactly as before)

- `smac_play.hud_status_bar(words)` — a NEW pure function, `HUD_BAR = (548, 592)`: >= 3 tokens in
  the band AND (`mission` or a `ssion|sslon|sston|ismon|sshon` fragment or `year`/`tear`) AND (a
  4-digit 2000-2500 number or `year`/`tear` or `energy`). It returns its components
  (`nbar/mission/year/nums/energy/fire`) so a caller can print WHY it believed a frame.
- `accept_ready.py`: `look()` (one freeze: classify + the bar), `verdict(looks, confirm)` (PURE —
  the whole screen decision, unit-tested with no game and no OCR) and `screen_class(samples=4,
  confirm=2, gap=0.8)` which re-freezes until a verdict lands. `decide()` is unchanged except that
  an unresolved `unknown` now prints "freeze and look at the frame" instead of "press Return until
  it reads hud" — a frame with neither row is not a KNOWN modal and a blind keypress on it is a
  gamble. `--samples/--confirm` are CLI knobs; the read's evidence prints as a `SCREEN <class>:`
  line and as `screen_evidence` in `--json`. `session_brief.py` needed no edit (it calls
  `AR.screen_class()[0]` and `AR.decide`), and it inherits both fixes.
- New instruments: `scripts/m65_screen.py` (N freezes of the live screen, per-sample class +
  per-band tokens + load1; writes frames + `samples.json`, deletes its own `_3x` siblings),
  `scripts/m65_anchor.py` and `scripts/m65_signals.py` (candidate HUD signals measured over the
  saved classifier frames).

### The measurement that chose the fix

`python3 scripts/m65_screen.py --samples 8 --save /tmp/m65a` on ONE unchanged screen (terran.exe
alive, year 2161 round 61 `cur_player 3`, nothing clicked, no key pressed) printed
`CLASSES SEEN {"unknown": 5, "hud": 3} of 8 samples`. In the saved records
(`evidence/m65/before_8looks_samples.json`, frames `evidence/m65/sample_00_unknown.png:1`,
`sample_02_unknown.png:1`, `sample_04_unknown.png:1`, `sample_07_unknown.png:1` and the control
`sample_05_hud.png:1`): `TURN@416 COMPLETE@416` in samples 1, 5, 6 ONLY, while
`Mission@567 Year@567 2161@567` (+ the score row `1-1-1@581`, `Energy:@582`) is in all EIGHT.
The bar fragments too, differently: `evidence/m25_t7.png` OCRs the whole row as
`sisson@573 tear@573 zie@573` with NO year number, and `evidence/m54a/live_hud.png` as
`[esston@572 2388@572` — so the signal is written against the fragments, not the clean words.

### The pin — `python3 scripts/test_hud_bar.py` -> `PASS 26/26 hud-bar cases`, exit 0

18 frames + 8 look sequences. Fires on all 3 saved HUD frames and on the 4 live `unknown` frames;
**silent** on the base screen (4 bar tokens, none of them Mission/Year/number/Energy), the cdrom
nag (0 bar tokens), the LOAD confirm (14 bar tokens, none of them), the HELP browser (234 tokens in
the frame), the COMM pane and the artwork panel. On the 4 modals drawn OVER a still-drawn HUD
(quit prompt, `m54e/chooser_live.png`, `m54h/chooser_g60b.png`, `m54g/newbase_pane.png`) the bar
DOES fire — the case asserts the classify() NAME as well, because that is the only thing keeping a
chooser from being called `hud`: the signal is consulted only on a frame classify() already called
`unknown`, and every modal detector runs before classify() reaches that fall-through.
`verdict()` cases pin the semantics: a named modal in ANY look decides the screen and beats a
pending bar promotion; `hud` on any look is believed as before; the bar must fire in 2 of the 4
looks (consecutive or not) to promote an `unknown`; one bar-only look is NOT believed; 4 looks with
no row and no bar is still `unknown` and still BLOCKED — **the check was not weakened, the screen is
re-read.**

### The live read-back — the oracle no longer blocks a playable box on its screen

`python3 scripts/accept_ready.py` three times, 20:55:45 -> 20:56:46 (year 2161 round 61, both bases
pending 0, so the verdict stays BLOCKED on `pending 0 — not UI-queued` and the FIX line is the
enqueue): run 1 `SCREEN hud: look 1: classify() == hud (the TURN COMPLETE row read)` (21 s),
run 2 same (9 s), run 3 **`SCREEN hud: look 1: classify() == unknown, but the HUD's bottom status
bar read in 2 of 2 look(s)`** (31 s) — the promotion path exercised live: neither look read the
button row and the oracle still said `hud`. `python3 scripts/session_brief.py` at 20:56 prints
`screen hud` (the same script printed `screen unknown` and "press Return until it reads 'hud'" at
20:16 this session) and its FIX is now the enqueue.

### Still green (all with the command)

`test_accept_ready.py` **PASS 17/17** (two new cases: unresolved `unknown` blocks, a crashed screen
read blocks, both needle `m65_screen.py`); `test_classify.py` **PASS 17/17**; `check_classes.py`
exit 0 with **14 PASS + 3 SKIP** — `m15_hud.png`, `m15_mainmenu.png`, `m15_autolist.png` are gone
from `evidence/` (deleted in #3 `214f982`, pre-existing, not this session); `test_m56_predict.py`
**PASS 19/19**; `test_walk_diff.py` **PASS 37/37**; `m56_build.py --fixture` bad=1,
`m61/fixture_defer_ok`=0, `m61/fixture_beat_visit`=1, `m64/fixture_paid_readback`=0,
`m64/fixture_paid_no_readback`=1.

### Confounded, and said so

The 8-sample measurement ran while `top` showed 79.6% user / 0.0 idle on **4 cores**, load average
13-15 (`jellyfin` 85%, `winedevice` 38%, tesseract ~200%): one OCR pass went from the ~1 s in
`ocr_fast`'s own comment to ~70 s, and the classifier suites stretched from ~40 s to >20 min. When
jellyfin finished the same suites ran in ~3 min and all three `accept_ready` runs finished in 61 s.
**Per-sample load was not recorded in the first run** (`m65_screen.py` records `load1` now), so
"the flake rate rises with CPU contention" is a HYPOTHESIS — the flake and the load were both
extreme at the same time, and the read rate improved in the low-load window, which is not the same
measurement. Do not read one OCR pass as a fact on a loaded box.

### Open

- Whether the accrual fix is right on a LIVE box (unchanged from session 104): needs an `income 1`
  base whose windows straddle the add; the `income 2` reload makes both PASS runs `gap_delta = 0`.
- Which slot the BUILD UI's INSERT writes (needs one enqueue with two DIFFERENT type ids).
- Still open from M63, and `milestone/m63` still carries the pop instrument, the `0x94de84`
  count-byte correction and the 384/386 identity-crossing finding with **no PR**.
- `check_classes.py`'s default list names three frames that no longer exist; either restore them or
  drop them from DEFAULT (nobody has done either).
- The load hypothesis above: re-run `m65_screen.py` (it records `load1` now) at two different loads.
- Evidence 26.3 MB of the 30 MB gate FAIL line (warn band 20) — the 5 new `evidence/m65/` frames are
  0.8 MB of it.

### Next pick

M66, cheapest first: (a) the `income 1` live accrual case — `scripts/m56_build.py --ui-queued <fresh
idx> --boundaries 10 --timeout 400 --no-poke-hold` on a base whose windows straddle the add, and
report the `accrual_phase` rows; (b) the two-enqueue DIFFERENT-type-id test that finally says which
slot INSERT writes; (c) cheap: re-measure the screen read at a quiet load and at a loaded one.
