# NEXT_PROMPT.md — footing for the next session (session 97 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56, the production gate = mineral storage). **M57 and M58
are UNMERGED and local-only on `milestone/m58`** — M57's 13 commits were merged INTO that branch
locally (its acceptance command is the `--ui-queued` mode it added), and nothing on it has been
pushed (session 96's push of `milestone/m57` was refused by a pre-receive hook; expect the same
here, so plan for it before any submit).

Session 97 ran **M58 and NAMED THE PRICE** (below, verified three ways), but `m56_build.py` never
printed PASS — the blockers are the queue-truth gap below and one harness race, NOT the price — so
per the footing **nothing was merged**. `milestone/m58` holds everything.

## WHAT SESSION 97 MEASURED (do not re-learn)

**The price is `0x4e40a0(owner,1,-1) × type_record[+41]`, and the multiplier is live STATE.**
Call site (`scratch/m574/text.txt`): `0x4efa2c mov ebx,[eax+0x50]` (eax = `DAT_0x8f0d60` = the base
record → ebx = the queue head), `0x4efa31 mov cl,[eax+4]` (the base's owner byte), `push -1; push 1;
push ecx; call 0x4e40a0` → `edi`; `mov edx,ds:0x68cbb0` (the base index being visited), `push 0;
push edx; push ebx; call 0x5ac950` → `eax`; `0x4efa52 imul edi,eax`; `0x4efa5e cmp [curbase+0x40],edi
; jge`. Ghidra corroborates that arg1 of `0x5ac950` is a unit TYPE id (`shard_014.c:7994`).

- `0x4e40a0(owner,1,-1)` = the per-owner cost factor in TENTHS: mask `[0x985b10]&0xff` bit → 10
  (`0x4e40c0`), else the era table `[0x68cbb8+era*4]` = {13,12,11,10,8,7}; rescale `[0x92a294]`
  (param_2==1 picks the +4 variant, `0x4e4119`); then `[0x92ada8]`: **1 → ×9/10, 0 → ×8/10, else
  unchanged** (`0x4e413b-0x4e4175`); then `switch` on `[0x94d6a0 + owner*0x20bc]` (sessions-56 call
  it the faction government field; 0 = identity).
- `0x5ac950(type, DAT_0x68cbb0, 0)` = the byte at `0x98ad88 + type*52 + 41` (M53b/M53f cost byte),
  clamped to ≥1 (≤999) ONLY when plan `+42 == 8` and param_2 > -1; type 2 `Scout Patrol` has plan 3
  and `+41 = 1`, and `type < 0x40` returns it straight away (`shard_015.c:23696-23745`).
- Live: mask `&0xff` = 0x08 (owner 3 in), `[0x92a294]` = 10, `[0x92ada8]` = 1, gov 0 → **9 × 1 = 9**.
  `python3 scripts/m58_price.py [--owner 3] [--type 2]` prints the whole chain from live memory.
  **Sessions 56/64 measured `[0x92ada8] = 2` → 10, and M52b debited 10 — that was that game's
  difficulty, not a law.** The scenario LOAD pane names the scalar: `m54a_load.py --relaunch` printed
  `difficulty level: talent` on the loaded-game row. `m56_build.py` now DERIVES the price
  (`cost_multiplier()` reads mask/era/`0x92a294`/`0x92ada8`/gov from the run's own snapshot).
- Verified at the gate three times, EXACT: `8 + 1 - 9 = 0` (2177 box r6), `8 + 2 - 9 = 1` (2151 box
  r2), `8 + 1 - 9 = 0` (`evidence/trace_m56_build_20261026_142139.jsonl` r8). The engine pays when
  `storage + income == 9`; 10 was never reached.

**The pop is strictly after the pay.** `evidence/m58pop.gdblog`: `VISIT#1 storage=9 pend=1 | 0x4ef7f6
add +0 (d0 0) | 0x4efedd pay 9->0 with pend STILL 1 | VISIT#2 storage=0 pend=0`. The pop store is
`0x4ef641` in `FUN_004ef5d0` (reached from the unit path at `0x4f037b`/`0x4f0f46`). Session 96's
"pending 1 -> 0 in the same visit" is NOT a rule — both orders relative to a boundary snapshot are
real (2151-box r2 popped in-window, 2177-box r6 next window), which is what the pending check now
encodes as an explicit either/or.

**PENDING IS NOT THE QUEUE TRUTH — M59's whole point.** In the 12-boundary run Korolev paid the
derived price twice more at **pending 0**: r6 minerals 7→0 with NO unit appearing (confounded with a
disband) and r11 minerals 7→0 WITH a unit appearing; in run 3 (`..._142139`) a second Scout Patrol
appeared on University Base at minerals 0, pending 0. A base whose head SLOT holds a unit type keeps
buying it whenever `storage + income >= price`. That is what fails the gate today (the F2
"unexplained ORDER-0 arrival on OUR base" floor fires correctly — the model missed the arrival).

**Acceptance numbers (three real invocations, all FAIL, no floor weakened).** Positive predictions
**1/1 verified in all three**; boundaries flipped 10/10, 12/12, 10/10; provenance `ui`,
`memory writes: 0`; storage-below-price ok (2 < 9, 4 < 9, 0 < 9). Run 3's other two BADs: an r0
walk-home race (`cur_player 6` at the after-snapshot) and the r9 queue-held check firing on the
deferred pop — the latter was fixed AFTER the run and has NOT been exercised by a real run yet.
`python3 scripts/test_m56_predict.py` -> **PASS 13/13**; `python3 scripts/m56_build.py --fixture
scratch/m56_fixture_bad.json` -> exit **1**.

## THE PICK — M59: WHAT ACTUALLY GATES THE NEXT PRODUCTION

One milestone, then stop. Do NOT tune `predict()` to observations.

1. Read `FUN_004ef5d0` (`0x4ef5d0-0x4ef6c3`): it pops the head (left-shifts `+0x50..`, decrements
   `+0x4c` at `0x4ef641`), decrements a byte at `[0x94de84 + owner*0x20bc + head*4]`, then calls
   `0x5a73f0(new_head, owner, base_index)` and loops while pending != 0; a nonzero return goes to
   `0x4ef68b` (push 0x24 → `0x446250`, then `0x473760(x, y, 2, 2)` at the base tile). The head<0
   (facility/project) variant calls `0x5a6e70(-head, owner, 0, index)`.
2. NAME `0x5a73f0`, `0x5a6e70` and the `[0x94de84 + owner*0x20bc]` byte array, reading the tables
   live (`scripts/m58_price.py` shows the idiom). Explain the measured fact that a base with
   **pending 0** and minerals 7 + income 2 buys another copy of the head slot's type — cite disasm
   lines, and re-read every store site and guard before believing a decode.
3. Decide what the queue's truth actually is (slots `+0x50..+0x74`? the per-faction byte? something
   else?) and restate `predict()`'s arrival rule. **Do not touch** the mineral identity
   `storage + credit - price == storage_after`, the `ui` provenance / zero-writes floor, the
   storage-below-price floor, or the `>= 1 POSITIVE prediction verified` floor.
4. Acceptance: `python3 scripts/m56_build.py --ui-queued <Korolev idx> --boundaries 10 --timeout 400`
   prints **PASS** on ONE real invocation. If it cannot, record the negative and merge nothing.
5. `python3 scripts/test_m56_predict.py` (13/13 today) and the bad fixture (exit 1) stay green; add
   rule cases for whatever new rule you add.

## LIVE FACTS / KIT

- **Preflight FIRST:** `python3 scripts/smac_preflight.py` (read-only, exit 1 on FAIL) prints our
  bases BY NAME with index/coords/pending/head/minerals/income, tracer state, /tmp and evidence
  budget. `SMAC_PID=<pid>` overrides pgrep.
- **Box at session-97 close:** year 2164 (last flip in `..._142139`), n_bases 22, ours 2 — University
  Base (28,42) idx 0 min 0 income 0 and Korolev Center (29,42) idx 17 min 0 income 0, pending 0,
  head 2 (stale slots), 11 units ours, 1 actionable. **Neither base accrues** (the produced units'
  upkeep eats the yield), so a gate run needs a reload:
  `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename, HUD at 2150)
  → `python3 scripts/m54g_prep.py` → one `python3 scripts/smac_play.py --turns 1 --timeout 200
  --no-escape 3000 --orders-per-turn 1 --verbose --tag t` founds Korolev at (29,42) →
  `python3 scripts/m57_ui_enqueue.py --base-index <fresh idx> --cell-item 2 --inserts 1` →
  preflight. After the reload Korolev had minerals 2 and income 2 and the derived price was still 9.
  Locate bases **BY NAME** every step — Korolev walked index 18 → 17 mid-run in session 97.
- `python3 scripts/m58_price.py [--owner 3] [--type 2]` — the price chain from live memory.
  `python3 scripts/m57_stores.py --base "Korolev Center" --boundaries 3 --timeout 220 --tag t` —
  arms the visit marker `0x4f5a99` + the 23 `+0x40` sites and prints storage/pending/head/d0 at
  every hit (this is how the pay/pop order was proven; its own PASS is about `+0x40` stores only).
  `python3 scripts/m57_credit.py --stop` detaches a leftover gdb (the store harness refuses to arm
  while any gdb runs).
- **Hold our units before a boundary watch** (`m55_boundary.poke_hold` pokes `+17 = 2` and reads
  back): the `--ui-queued` run makes no writes of its own, so hold BEFORE it or the auto-end never
  fires. Poke and read back BEFORE attaching gdb — pokes lie under a tracer.
- `python3 scripts/evidence.py budget` BEFORE adding frames — **27.1 MB now, the gate FAILs at 30**.
  Delete the untracked `trace_m56_build_*` files that `--fixture` runs leave behind.
- `scratch/m574/text.txt` (whole `.text` objdump) and `scratch/m574/census.py` are on disk
  (gitignored). Regenerate: `objdump -d -M intel --section=.text programs/terran.exe >
  scratch/m574/text.txt`.
- Rule cases today: `test_m56_predict.py` 13/13; `m56_build.py --fixture
  scratch/m56_fixture_bad.json` exit 1; `test_walk_diff.py` 37/37; `test_classify.py` 17/17;
  `check_classes.py` 17/0 (delete the untracked `*_3x.png` siblings right after).

## TRAPS

- **`m57_ui_enqueue.py` on a just-founded base can read an EMPTY chooser** (`FAIL: item 2 not in
  candidate array []`); a second attempt works. Do not conclude the item is unresearchable.
- **The after-snapshot can catch the player walk mid-round** (run 3 r0: `cur_player 6`), which fails
  the M55 walk-home check. It is a harness race, not a game bug — if it burns a check, note it and
  re-run rather than editing the floor.
- **The base array reorders/compacts mid-run** (Korolev 18 → 17): locate by NAME every step; a baked
  index can name another faction's record.
- A base display left open swallows every turn-end key (Escape closes a PANE safely; Escape on the
  bare map raises the quit prompt, and after it the game takes no keys — reload only; never click OK
  on the quit prompt). The units-not-moved confirm takes NO Return (click YES then the OK bar 26 px
  below). Orders mode `0x91b5b8 == 0` makes every order key a no-op.
- gdb: no `si` inside a breakpoint commands list (it ENDS `gdb -batch`); `set print frame-quiet` is
  not a command in this gdb and aborts the file; stdout must be DRAINED or 64 KB of hit lines stalls
  the inferior. For a plain `mov [reg+0x40],src` the source operand IS the after value.
- `os.pread` on `/proc/<pid>/mem` EIOs here — `seek`+`read`. A hardware watchpoint on `+0x40` crawls
  the game; breakpoints at write sites only. Popup BARS ignore clicks (Return works on the default
  row); MENU click (75,369); TURN COMPLETE (650,410).
- One variable at a time: if a position AND a tile changed, write "confounded". When docs and code
  disagree, the documents win until a controlled poke proves otherwise — and say so out loud (this
  session overturned two session-96 claims with reads: the same-visit pop, and pending as the queue
  truth).
- Never: commit to main; `pkill -f` / `pgrep|kill` by name; Escape on the title screen; OK on the
  quit prompt; `--mode stop`; `file://` with `--load`; a clear-prefixed command; backticks in a
  commit message; `skill_manage delete`.

## CLOSING ORDER (exactly)

1. `## Session <N>` in `SESSION_NOTES.md` (what changed, numbers WITH the command, open, next pick).
2. Rewrite this file; `wc -c NEXT_PROMPT.md` <= 15,500.
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/` (the gate checks the sync).
4. `git add -A && git commit -m '<ID>: checkpoint'`.
5. `python3 scripts/gate.py --base main` — GREEN.
6. Submit/merge ONLY on a real PASS: `python3 scripts/milestone.py submit --title "..."` ->
   `gh pr checks <n>` -> `python3 scripts/milestone.py merge <n>`. Otherwise say so and merge nothing.

## Report

One screen: what changed, the acceptance numbers WITH the command, what is open, the next pick.
