# Reading the screen (M65) — why one OCR pass is not a screen read

`scripts/smac_play.py` classifies a frame from ONE tesseract pass (`ocr_fast`, ~1 s at 2x,
`--psm 6` tsv) plus two colour tests (`region_colors`, `close_bar`). Everything the driver
does — click, Return, Escape, answer a pane — is decided by that one verdict.

## The HUD has two rows and only one of them is stable

`classify()` names the tactical HUD off **one row**: the word `complete` at 380 < y < 450
(the TURN COMPLETE button, centre y~416). Measured 2026-10-26 with
`scripts/m65_screen.py --samples 8` on ONE unchanged screen (terran.exe alive, year 2161,
round 61, `cur_player 3`, nothing clicked, no key pressed):

- `complete` in the button row: **3 of 8** passes (samples 1, 5, 6 —
  `TURN@416 COMPLETE@416`).
- the HUD's **bottom status bar** (`HUD_BAR = (548, 592)`): **8 of 8** — `Mission@567`,
  `Year@567`, `2161@567`, the faction score row at y~581 (`1-1-1`, `111`, `141`) and
  `Energy:@582`.

So `classify() == 'unknown'` on this box means *the button row fragmented*, not *a modal is
on screen*: 5 of 8 freezes of a plain HUD read `unknown`, and session 104 recorded 14
consecutive `unknown` reads that `vision_analyze` showed to be the plain HUD. The map
animation and the OCR feed each other; the bar row is the stable one.

The bar fragments too, differently — the shipped signal (`smac_play.hud_status_bar`) is
designed on the fragments actually seen, not on clean words:

| frame | what the bar OCRs to | what fires |
|---|---|---|
| `evidence/m25_t7.png` | `sisson@573 tear@573 zie@573`, `Energy:@582`, no year number | `ssion` fragment + `Year`-as-`tear` + `energy` |
| `evidence/m54a/live_hud.png` | `[esston@572`, `2388@572` | `sston` fragment + the 4-digit year number |
| `evidence/m37_recovered.png` | `Mission@567 Year@567 2275@567 Energy:@582` | clean |
| `evidence/m65/sample_0[0,2,4,7]_unknown.png` | `Mission Year 2161` (+ `||Il)||Mission`) | clean, while the button row is garbage |

Predicate (`hud_status_bar`, returns its components so a caller can print WHY): >= 3 tokens
in `HUD_BAR` **and** (`mission` or a `ssion|sslon|sston|ismon|sshon` fragment or `year`/`tear`)
**and** (a 4-digit 2000-2500 number or `year`/`tear` or `energy`).

Measured on the 17 saved classifier frames (`scripts/m65_anchor.py`, `scripts/m65_signals.py`,
pinned by `scripts/test_hud_bar.py`): fires on all 3 saved HUD frames and on the 4 live
`unknown` frames; **silent** on the base screen (`m45a_post.png`, 4 bar tokens, none of them
Mission/Year/number/Energy), the cdrom nag (`m15_boot.png`, 0 bar tokens), the LOAD confirm
(`m15_loaded_words.png`, 14 bar tokens, none of them), the HELP browser
(`m54a/live_now2.png`, 234 tokens in the frame), the COMM pane (`m54c/comm_pane.png`) and the
full-screen artwork panel (`m54d/peek_stuck.png`).

## Modals drawn OVER a still-drawn HUD

The bar is HUD chrome, so it is still readable under anything drawn on top of it: it FIRES on
`m37_screen0.png` (quit prompt), `m54e/chooser_live.png`, `m54h/chooser_g60b.png` (the `g`
chooser) and `m54g/newbase_pane.png` (NEWBASE name entry). That is harmless only because
classify() runs `is_quit_prompt` / `is_dest_chooser` / `is_name_pane` / `is_help_page` /
`is_communication` / `close_bar` / the dialog-band tests **before** it ever reaches the HUD
fall-through — and the bar signal is consulted ONLY on a frame classify() already called
`unknown`. `test_hud_bar.py` asserts the NAME on each of those frames for exactly that reason:
if a modal detector is ever weakened, the bar will start calling a chooser `hud`.

`classify()` itself is unchanged by M65 — the driver still sees exactly the classes it saw
before. The second look lives in the consumer (`accept_ready.look/verdict/screen_class`).

## What N looks mean (`accept_ready.verdict`, pure, pinned without OCR)

- a **named modal class in ANY look decides the screen** — a modal sits there until something
  answers it, so one sighting is enough, and it beats a pending bar promotion;
- `classify() == 'hud'` on any look → `hud`, as before;
- `unknown` is **not** a modal: it is re-frozen, and the screen is called `hud` only once the
  status bar has fired in `--confirm` (default 2) of the `--samples` (default 4) looks —
  consecutive or not. One bar-only look is not believed;
- no button row, no bar, no modal name in 4 looks → still `unknown`, still BLOCKED. The check
  was not weakened, the screen is re-read; the FIX line changed from "press Return until it
  reads hud" to "freeze and look at the frame" because a frame that shows neither row is not a
  *known* modal and a blind keypress on it is a gamble.

## Load is a confound, and a big one

The 8-sample measurement ran while `top` showed 79.6% user / 0.0% idle on **4 cores**, load
average 13-15: `jellyfin` 85% and `winedevice` 38%, with tesseract itself at ~200%. Under
that load a single OCR pass went from ~1 s (the figure in `smac_play.ocr_fast`'s comment) to
~70 s, and `scripts/test_classify.py`'s "~40 s for 17 frames" stretches past 20 min. Per-sample
load was NOT recorded in the first run (`evidence/m65/before_8looks_samples.json` has no
`load1`; `m65_screen.py` records it now), so **"the flake rate rises with load" is a
hypothesis, not a measurement** — both were extreme at the same time, that is all that was
shown. Do not read a screen verdict as a fact without re-freezing on a loaded box.
