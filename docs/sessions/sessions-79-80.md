# Session notes archive — sessions 79-80

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 79 (2026-10-24) — M54b: **THE 40-TURN RUN PASSES FROM A LOADED SAVE — CLEAN-POINT SAVES RESUME LIVE; THE HUNG AUTOSAVES ARE A MID-END-TURN-SAVE ARTIFACT**
- **THE ACCEPTANCE IS MET.** One invocation, nobody at the keyboard, starting from a DEAD process:
  `python3 scripts/smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54b40b --load
  Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV --verbose`, checked with
  `python3 scripts/m54a_check_run.py evidence/trace_m54b40b_20261024_212833.jsonl --timeout 240` →
  `turns 40 records, header asked for 40`, **`advanced 40/40`, year deltas `{1: 40}`**,
  **`stuck 0 (turns [])`, max dt 51.5 s**, `PASS`, exit 0. The DRIVER answered the whole load:
  log shows `no window -> relaunching the game`, cdrom Return, title -> LOAD GAME row (610,344) ->
  blind browser (name box 406,527, OK bar 330,552) -> LOAD confirm OK (290,391) -> `HUD reached
  live=True`. Panes serviced inside the run: hive-bribe 5, dialog 17, confirm-after-press 36,
  base 6, close-bar 2, ai-phase 18 — no pane starved it, no bar clicked outside its pane.
  Session 78's wins stay green after every change: `test_classify.py` PASS 10/10,
  `check_classes.py` frames: 10 failures: 0.
- **THE CLEAN-SAVE TEST ANSWERS THE HUNG-RESUME QUESTION.** A save taken at a CLEAN point (live
  HUD, `turn_flags 0`, idle) reloads live: MENU (61,369) -> GAME (30,186) -> Save Game (200,331);
  the SAVE browser is TALLER than the LOAD browser (NAME 406,304, OK 330,327, CANCEL 482,327 — the
  LOAD browser's bars sit at y 552); typed the full `Z:\` path, the file landed (242,539 B, mission
  year 2150 @ +0x54), `m54a_load.py --relaunch` reached the HUD animating=True with
  `turn_flags 0` and a responsive MENU click. So session 78's eight hung autosaves are specific to
  saves taken WITH `turn_flags` bit1 set (mid-end-turn), not a save-format wall. The 2416 campaign
  exists only in such mid-round autosaves — resuming PAUL'S campaign still needs either a clean
  campaign save or the bit1-resume fix; parked in `references/open-leads.md`.
- **THE WEDGE GUARD EARNED ITS KEEP — AFTER ONE FALSE POSITIVE.** The first run reached 28/40,
  then `turn 28: WEDGE — screen byte-static 42s, MENU click changed nothing` — but the game was
  ALIVE (year 2178, `turn_flags 0`, one Escape closed the screen instantly): a OWN-PHASE BASE
  SCREEN, legitimately byte-static, sat under the `--no-escape 3000` gate that starved the
  base-Escape path (`evidence/px_wedge_t28.png`, `evidence/trace_m54b40_20261024_211436.jsonl`).
  Two fixes: the probe fires only on `hud` frames (the hung-resume signature), and `base` closes
  with Escape EVEN UNDER `--no-escape` (the class is unambiguous — quit-prompt/title classify
  first, the base test is positional since M54a). The round-aware budget slides the deadline with
  every changing capture, capped at 3x timeout; a static screen does not extend it.
- **State of the box:** pid 373089 alive at 2190 (n_bases 26) after the winning run;
  `programs/saves/m54b_clean.SAV` (2150, gitignored like all of `programs/`) is the reproducible
  start point for `--load`.
- **Next:** ROADMAP Phase 2 — **S3 (unit orders/combat)**: the unattended loop has never MOVED a
  unit; `give_order` exists but only runs via `--order`. Or close the mid-round-autosave question
  (why a save with bit1 set spins after load) to unlock Paul's 2416 campaign. Read ROADMAP.md
  before picking.

## Session 80 (2026-10-24) — M54c: **THE UNATTENDED LOOP NOW ORDERS UNITS — 31 MEMORY-VERIFIED ORDERS INSIDE A 40/40 RUN FROM THE SAVE**
- **THE ACCEPTANCE IS MET.** One invocation, nobody at the keyboard, from a dead process:
  `python3 scripts/smac_play.py --turns 40 --timeout 240 --no-escape 3000 --tag m54c40c --load
  Z:\home\n100\reverse\smac\programs\saves\m54b_clean.SAV --verbose`, checked with
  `python3 scripts/m54a_check_run.py evidence/trace_m54c40c_20261024_224606.jsonl --timeout 240
  --min-orders 5` → `turns 40 records, header asked for 40`, **`advanced 40/40`, year deltas
  `{1: 40}`**, **`stuck 0 (turns [])`, max dt 61.8 s**, **`orders 31 VERIFIED of 36 attempted`**
  on turns 0-3, 9-11, 14-16, 27-30, 37-39, `48.9 s spent ordering`, `PASS`, exit 0. Shape taken:
  the S3 harness-assertion half (orders + verification inside the loop); the combat half of the
  ROADMAP S3 row is still open — see Next.
- **THE ORDER CONTRACT.** `order_step_in_loop()` runs once per player turn inside
  `service_turn`'s `hud` branch (the `cur_player`/`turn_flags & 2` gate has already proved it is
  OUR phase, the only window where a hotkey is an order and not a key sink): poke `0x91b5bc`,
  fire ONE real hotkey, service the pane the setter raises, then read `unit+17` back — an order
  counts only as a `+17` delta into the byte set that key may produce (ORDERS.md §4). A landing
  order verifies in ~0.0 s (the byte is read before any OCR); a dud costs one OCR + pane service.
  `--orders-per-turn` (2), `--order-budget` (35 s/turn), `ORDER_MAX_ATTEMPTS` (8 keys/turn), a
  key retired after 3 delta-less attempts and a type deprioritised after refusing every key keep
  the step from ever eating a turn. `--no-orders` restores the old behaviour.
- **WHAT THE POSITION ACTUALLY ALLOWS (measured, `evidence/m54c_probe.txt`).** The
  `m54b_clean.SAV` lineage owns SIX records that all decode `type 2` = `Scout Patrol` (class 3) —
  the HUD's own unit panel reads `Scout Patrol` — and no class-9 record at all, so
  `find_former()`'s class-9 filter ordered nothing and the first smoke run reported `orders:0`
  while silently trying zero candidates. The picker is now `find_actionable()`: the game's OWN
  select gate (owner, `+9` not frozen, `+40` movement unspent) with `cls` used to ORDER
  candidates, never to exclude them. Live key facts: `f` on records 0 and 20 changed neither
  `+17` nor energy (the `NEEDTERRAFORMERS` negative control); `l` took `+17` 0→1 on records 0 AND
  3 with no pane and no energy; `Up`/`Right` left `+17` 0 (arrows drive the MAP CURSOR — `Right`
  opened the base pane) and `shift+Up` raised a pane. So the loop's non-terraform plan is `g`
  (`0x18`), `l` (1), `h` (2), and every one of this run's 31 verified orders is `l` → byte 1.
  **No terraform order has ever landed in a Formerless position, and none will.**
- **THREE PANES THE DRIVER HAD TO LEARN.** (1) The BASE screen swallows the next keypress: the
  first smoke trace shows `l` failing behind a `base` pane and landing the moment the pane was
  Escaped, so the order step now closes `base` with Escape instead of leaning on Return. (2)
  **Escape at a clean HUD raises "Do you really want to quit?"** — the probe poisoned its own
  first run that way (12 keypresses went into the dialog and every frame read `quit-prompt`);
  inside the order step the prompt is answered with Escape, never Return, because Return there is
  "Yes, that's an order, mister!" and the process is gone. (3) A faction **COMMUNICATION**
  ("BELIEVERS - SEETHING" + a quoted demand + its own OK bar at y 347,
  `evidence/m54c/comm_pane.png`) classified `unknown`, so M54b's bottom-bar rule clicked the
  CONSOLE `DATALINKS` bar (333,560) 38 times in a row, each click opening the profiles browser
  and each EXIT click (525,344) landing back on the same communication: turn 35 of
  `evidence/trace_m54c40b_20261024_222039.jsonl` burned **735.2 s with the year stuck at 2185**.
  New class `comm` + `answer_communication()` (click the MIDPOINT of the y-347 bar row — its
  dithered ends read (266,347)/(534,347) and the label between them is not fill) fixed it: the
  winning run met 6 communications and answered all 6 (`comm-ok` x6, `stuck 0`).
- **SESSION 79'S WINS STAY GREEN, PLUS THE NEW ROWS.** `python3 scripts/test_classify.py` →
  **PASS 11/11 screen classifications**; `python3 scripts/check_classes.py` → **frames: 11
  failures: 0**. The new `comm` class is pinned in BOTH files against the saved frame before it
  went into the driver, and the 10 older rows still classify their own frames.
- **State of the box:** the winning run left the game at 2190 (n_bases 22, `cur_player 7`,
  `turn_flags 0x100002`); the driver process and the game were stopped cleanly at the end of the
  session, so the box is idle and `--load` relaunches from `m54b_clean.SAV`.
- **Next:** **S3's other half — orders that MOVE and FIGHT.** Every verified order this run could
  buy is `SENTRY` (byte 1, sticky: after six turns the game itself prints "No units need new
  orders"), because the reproducible position has no Former and `g` refuses to queue a MOVE for a
  unit standing on its base. The cheapest route to a real walk is a position that HAS class-9
  units: either the fresh-game start (2100, `scripts/m54a_newgame.py`) or a save we make after
  production turns up a Former, then verify `0x18`/`0x19` orders, execution (`EXEC`), and combat
  resolution (the ROADMAP S3 row: order → execution → combat → death/occupation). Secondary: the
  `comm` class should also be tried against the Council's "X - MOOD" panes, which share its
  banner style but print unquoted text — the discriminator is deliberate, but it has only one
  fixture behind it.
