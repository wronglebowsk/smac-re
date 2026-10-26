# NEXT_PROMPT.md — footing for the next session (session 95 close, 2026-10-25)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53), **M54k2**
(#54), **M55** (#55), **M56** (#56, the production gate = mineral storage; `test_m56_predict.py`
11/11). **M57 is OPEN and UNMERGED on `milestone/m57` (local only — a pre-receive hook refused the
push).**

Session 93: the GAME's own BUILD UI fills the queue (0 memory writes). Session 94: the credit is not
a per-round constant. **Session 95: the gate ran on a real game-filled queue and got 1/2 — the model
premise is FALSIFIED. Nothing merges.**

## WHAT SESSION 95 MEASURED (do not re-learn)

`python3 scripts/m56_build.py --ui-queued 18 --boundaries 8 --timeout 240` on a fresh box (2154),
Korolev Center [18] (29,42), queue filled by the game (pending 1, head 2, minerals 2, income 2, zero
writes): **FAIL, exit 1**.
- **r3 predicted arrival (8 + 2 = 10 >= price 10) and storage stayed 8 -> 8, pend 1** — the visit
  added nothing while the round-start income field read 2. **r4, identical round-start numbers,
  arrived: 8 -> 3, pend 0.** Same inputs, different outcomes one round apart.
- r4 debit was **-5** (-7 from the post-add 10), not the price 10.
- **r7: storage 5 -> 0 with pending 0** and a new unit — a pay with an empty pending count. The queue
  slots never left-shifted (`[2,2,0]` for the whole run). ONE queued item produced TWICE.
- `m57_credit.py --base Korolev --boundaries 3 --tag m57k`: 2 ADD hits, no GATE/PAY/CLMP; an add of
  +1 while the field read 1 and +2 while it read 2 — **the add uses the d0 current at the visit,
  which moves inside the round.** Register side-values at the sites remain garbage (the "d0" printed
  18 = the base INDEX); only the storage fragments and the sampler are evidence.
Therefore an exact-round prediction from the round-start snapshot is impossible, and the gate's
"debited by >= price" + "bookkeeping exact" floors cannot be met by the present model. **No floor was
weakened.**

## THE PICK — M57-4: ENUMERATE EVERY WRITE TO `base+0x40` IN ONE VISIT

One milestone, then stop. Do NOT tune `predict()` to the observations.

1. Reload a clean box and get an income base with a game-filled queue:
   `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename, HUD at 2150)
   -> `python3 scripts/m54g_prep.py` -> `python3 scripts/smac_play.py --turns 1 --timeout 200
   --no-escape 3000 --orders-per-turn 1 --verbose --tag <t>` -> `FOUND rec<N> (29,42) ... bases 1->2`
   (the founder is whatever record prep selected — do not assume rec0). Preflight; then
   `python3 scripts/m57_ui_enqueue.py --base-index <Korolev idx> --cell-item 2 --inserts 1`.
2. **Instrument every write site, not four:** `0x4ef7f6` (add), `0x4eff20` (clamp B), `0x4efed8`
   (pay), `0x4f0cc3` (clamp after pay), plus the two candidate store instructions the disasm shows
   inside `FUN_004ef6d0` and `FUN_00417ee0`'s queue tail. For each hit single-step once (`si`) and
   print, from the BAKED base address (never a register): `pending, head, d0, +0x3c, +0xcc, +0x30,
   value_at_(base+0x40)` BEFORE and AFTER, plus `$pc`. Condition every breakpoint on the base
   pointer.
3. Run 3-4 boundaries and read the store sequence per visit. Required output: for one visit, an
   ordered list `(site, before, after, pending, head, d0)`; then say plainly which store produced the
   r7 pay with pending 0 and whether the add's amount equals the d0 field or a recomputed value.
4. Acceptance for M57-4 (`scripts/m57_stores.py`): prints a table and PASSes only when every store to
   `+0x40` in 3 consecutive boundaries is attributed to a named site and the sum of the deltas equals
   the observed net change for each base, with zero unattributed deltas. That is the honest gate; it
   does not touch `m56_build.py`.
5. Only AFTER the sequence is proven, revisit the M56 gate: if the proven semantics still cannot make
   `m56_build.py --ui-queued` pass with every floor intact, record the negative and leave M57
   unmerged.

## LIVE FACTS / KIT

- **PREFLIGHT FIRST:** `python3 scripts/smac_preflight.py` (read-only; exit 1 on FAIL). Prints our
  bases BY NAME with index/coords/pending/head/minerals/income, unit decode, /tmp, evidence budget.
  `SMAC_PID=<pid>` overrides pgrep.
- Gate: `python3 scripts/m56_build.py [--arm N|--ui-queued N] [--boundaries N] [--timeout S]
  [--settle S] [--fixture FILE]`; prints the credit arithmetic before a --ui-queued run; answers the
  units-not-moved confirm itself; breaks the watch when the walk is home.
- Rule cases: `test_m56_predict.py` -> PASS 11/11; `m56_build.py --fixture
  scratch/m56_fixture_bad.json` -> exit 1; `test_walk_diff.py` 37/37; `test_classify.py` 17/17;
  `check_classes.py` 17/0 (delete UNTRACKED `evidence/**/_3x.png` after).
- UI queue: `scripts/m57_ui_enqueue.py --base-index N --cell-item 2 --inserts 1` (cycles the queue
  widget's base, picks the chooser cell BY CONTENT, reads pending after every click, restores orders
  mode). Chooser grid: `x=128+127*(k%5), y=60+100*(k//5)`; guard `[0x6a9e9c+0xa774]` = cell index;
  candidates at `0x9267e4`, count `0x9267e0` (Scout Patrol id 2 was cell 3 at 2152-2154).
- Credit harness: `scripts/m57_credit.py --base <NAME> [--boundaries N] [--timeout S] [--tag T]
  [--wp]` (name, NOT an index). `--stop` detaches a leftover gdb.
- Reload: `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> 2150; `m54g_prep.py`
  (pokes the founder's tile to (29,42) and clears its order); one `smac_play.py --turns 1` founds
  Korolev. Base indices drift: locate by NAME/(x,y) every step.
- `python3 scripts/evidence.py budget` BEFORE adding frames (~26 MB used, FAIL at 30 MB).

## TRAPS

- **The units-not-moved confirm takes NO Return** ("SOME OF OUR UNITS HAVE NOT YET MOVED ... do you
  really want to end the turn now?"): click the YES row (400, find_yes_row) then the OK bar 26 px
  below, 1.2 s apart = `smac_play.answer_confirm`. A run sat 240 s on it with the year frozen.
  Diagnose any "year never moves" with one frame + `classify` (it returns `confirm`).
- **orders mode (`0x91b5b8`) at 0 makes every order key a no-op**; the turn then never ends. The UI
  enqueue sets it to 0 to open the base display — it now restores 1; if you script the display
  yourself, restore it.
- Pokes lie under a tracer; poke before attaching, verify after `kill -CONT`.
- A hardware watchpoint on `+0x40` crawls the game (the field is read constantly). Breakpoints only.
- gdb register side-values at the production sites are unreliable (`$ecx` printed an index as d0);
  read fields from the base pointer instead, and single-step to get before/after.
- Popup BARS ignore clicks; Return works on the default row; MENU click (75,369) works.
- TURN COMPLETE is at (650,410); the confirm dialog's YES row comes from OCR, never a fixed y.
- Escape on the map raises the quit prompt and after it the game takes no keys — reload only.
- Never `pkill -f`/`pgrep|kill` by name; never click OK on the quit prompt; no `--mode stop`; no
  `file://` with `--load`; no backticks in a commit message; `skill_manage delete` is banned.
- One variable at a time: if a position AND a tile changed, write "confounded".

## CLOSING ORDER (exactly)

1. `## Session <N>` in `SESSION_NOTES.md` (what changed, numbers WITH the command, open, next pick).
2. Rewrite this file; `wc -c NEXT_PROMPT.md` <= 15,500.
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`.
4. `git add -A && git commit -m '<ID>: checkpoint'`.
5. `python3 scripts/gate.py --base main` — GREEN.
6. Submit/merge ONLY on a real PASS: `python3 scripts/milestone.py submit --title "..."` ->
   `gh pr checks <n>` -> `python3 scripts/milestone.py merge <n>`. Otherwise say so and merge nothing.

## Report

One screen: what changed, the acceptance numbers WITH the command, what is open, the next pick.
