# NEXT_PROMPT.md — footing for the next session (session 99 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57). Session 99 **PASSED M60**
(`python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold` ->
`PASS production prediction: 1 verified unit arrivals over 10 boundaries ... 0 memory writes`,
**53 checks / 0 bad**, trace `evidence/trace_m56_build_20261026_153930.jsonl`); the M60 PR is the
one this session submitted from `milestone/m60` — read `git log --oneline -3` / `gh pr list` for its
number before quoting it.

## WHAT SESSION 99 SETTLED (do not re-learn)

**THE CREATE GUARD IS THE PROCESS-GLOBAL DWORD `0x8f0d70`, NOT `[base+0x10]`.** The bytes at the
guard are `4eff32: a1 70 0d 8f 00  mov eax,ds:0x8f0d70` / `4eff37: 85 c0  test eax,eax` /
`4eff39: 75 21  jne 0x4eff5c` (skip the create). Base record `+0x10` is NOT the guard: it holds
0x4b000000 on Korolev Center and 0x55000000 on University Base. `grep -c 0x8f0d70` over the whole
`.text` dump is **1** (that read); `0x8f0d60`, its neighbour, is the current-base POINTER (929
references). `scripts/m60_guard.py --stage watch --boundaries 2` -> `guard_writes: 0, writers: {},
visits: 53, guard_values_at_visits: ["0"]` — a hardware watchpoint saw no writer at runtime.
**Proven by poke, one variable, University as control:** guard 1 -> Korolev still PAYS (minerals
9 -> 0) and NO unit arrives (our units 10 -> 10, guard reads back 1 after the turn); guard 0 -> the
base pays and the unit ARRIVES (10 -> 11). A `m56_build` PASS run now asserts `guard == 0` in every
sampled row (5534 rows, values [0]) — an added check, nothing weakened.

**A READ CAN BE EARLY — M59's "snapshot GAP" was this, not a slow create.** The year flip is not the
end of the round: right after `smac_play --turns 1` printed `2189->2190`, Korolev held the poked 9
minerals, `+0x3c` unmoved, `cur_player 7`, and a 100 s poll changed NOTHING; the pay and the create
land later in the same round while the player walk comes home (then minerals 0, ours 10 -> 11,
`cur_player 3`). The store tracer only looked like a cause because it WAITS for the walk
(`m57_stores.py --tag m60c/m60d` -> `STORE#2 pc=0x4efedd site=visit.pay-minus-edi before=9 src=0`,
`per-boundary net ['2184->2185=-9']` PASS). `m56_build` closes each window on `cur_player` coming
home, so its windows are the valid ones; judge production only after the walk is ours again.

**`0x4f6030` = the production CHOOSER** (what a base builds next), called from `0x4e5ae0` and the
BUILD UI for the base in `*(0x8f0d60)`: scores candidates, keeps the MINIMUM against `local_124[0]`
seeded `0xf423f` (999999), score = cost × ~25 halve/double heuristics; a candidate is REJECTED
unless `[base+0x38]` carries the bits its category needs — switch on `record[+0x32]` at `0x4fb4xx`:
0->0x200, 1->0x1000, 2/3->0x1000 (0x400000 when `[base+0x38] & 0x1000` is clear or `record[+0x2c]
!= 0`), 4->0x2000, 5->0x800, 6->0x400, 7/10->0x800000, 8->0x20000, 9->0x8000, 0xb->0x100000, plus
0x80000 for types >= 0x40 whose `record[+0x38] & 4` is clear — and only for owners IN `0x985b10`.
Fallback `0x4fd6a0-0x4fd6e5`: scan the 512 type records at `0x98ad80` stride `0x34` (end `0x9915b2`),
keep `0x5a73f0`-buildable with category 1/2/3 and `record[+0x38] & 4`, take the lowest `record[+0x31]`.
Korolev `[base+0x38] = 0x00dfbe41` carries 0x1000 so Scout Patrol (category 3) passes. Enemy heads
stay REPORTED, never predicted: they are the argmin of that heuristic over the enemy's own plan mask.

**GHIDRA GOTCHA (this is what wrote the old wrong note).** `DAT_008f0d60` is typed `short *`, so
pseudocode `*(uint *)(DAT_008f0d60 + 0x1c)` is BYTE offset **+0x38** — proved by `0x4fb293 mov ecx,
ds:0x8f0d60` / `0x4fb299 test DWORD PTR [ecx+0x38],0x80000000`. `+0x1c`->+0x38 (plan dword),
`+0x20`->+0x40 (storage), `DAT_008f0d60[0]/[1]` -> the x/y words. Double every offset printed
through that variable and check the disasm once per new site.

**CONFLICTS still on the record, unresolved:** queued-count byte `0x94dc84` (skill) vs `0x94de84`
(the pop instruction at `0x4ef613`); pay `0x4f0ca6` (old m56 docstring) vs `0x4efedd` (the gate's
pay store). A writer for `0x8f0d70` outside `.text` is NOT excluded (the watchpoint covers runtime).

## THE PICK — M61: WHERE THE CREATE SITS IN THE ROUND

One milestone, then stop. Do not tune `predict()` to observations.

1. Record `(cur_player, visit 0x4ef6d0, pay 0x4efedd, create 0x4eff4e, guard 0x8f0d70)` tuples across
   >= 2 boundaries — extend `scripts/m60_guard.py --stage watch` (it already stamps the guard at every
   visit) with conditioned breakpoints on the pay and the create. Cite the disasm lines you arm.
2. State the round sequence from the recorded tuples: where our base's visit sits relative to the
   year flip and to `cur_player` coming home. Then make `m56_build`'s F1 deferral branch ("verified
   by the next window's before-snapshot") a MEASURED position, not a tolerance — same floors, same or
   stricter checks. If the model cannot state the arrival round exactly, say so and leave F1 as is.
3. Say what base record `+0x10` is (0x4b000000-style on our bases; it is not the guard and not zero).
   Cite the census sites that write it (`scratch/m59/queue_census.py`).
4. Acceptance: `python3 scripts/m56_build.py --ui-queued <Korolev idx> --boundaries 10 --timeout
   400 --no-poke-hold` prints **PASS** on ONE real invocation. If it cannot, record the negative and
   merge nothing.
5. `python3 scripts/test_m56_predict.py` (17/17 today) and the bad fixture (exit 1) stay green; add
   cases for anything new.

## LIVE FACTS / KIT

- **Box at session-99 close:** terran.exe alive, year **2172**, round 72, `cur_player 3`, guard 0,
  Korolev Center idx 18 (29,42) minerals 8 income 1 pending 0 head 2, 4 units on its tile; University
  Base idx 0 (28,42) minerals 0 income 0 pending 0 head 2, 5 on tile; 9 ours units. **Preflight
  first:** `python3 scripts/smac_preflight.py` (read-only, exit 1 on FAIL).
- **Reload recipe (the proven path):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py
  --relaunch` (BARE filename; prints `difficulty level: talent`) -> `python3 scripts/m54g_prep.py` ->
  `python3 scripts/smac_play.py --turns 1 --timeout 200 --no-escape 3000 --orders-per-turn 1
  --verbose --tag t` (prints "Korolev Center founded in 2150") -> locate Korolev **BY NAME**
  (`python3 scripts/m60_guard.py --stage read` prints `i`) -> `python3 scripts/m57_ui_enqueue.py
  --base-index <fresh idx> --cell-item 2 --inserts 1` (prints `pending=1 head=2 ... minerals=5 d0=2`)
  -> `python3 scripts/m59_head.py --stage read --hold` -> the acceptance run WITH `--no-poke-hold`.
- `python3 scripts/m60_guard.py --stage read|poke --value N|watch --boundaries K --timeout T --tag t`
  — read/poke the guard global, print both our bases (minerals, income, pending, head, `+0x30` flags,
  `+0x38` plan dword, `+0x98` mirror, per-tile unit count, our unit total), or run the hw watchpoint.
  `--stage watch` refuses if a gdb is already running (`scripts/m57_credit.py --stop` detaches one).
- `python3 scripts/m59_head.py [--stage read|poke --base NAME --minerals N] [--hold]`,
  `python3 scripts/m58_price.py [--owner 3] [--type 2]`, `python3 scripts/m57_stores.py --base
  "Korolev Center" --boundaries 3 --timeout 220 --tag t` (the `+0x40` store tracer; arm only when no
  gdb runs; poke and read back BEFORE attaching — pokes lie under a tracer).
- `scratch/m574/text.txt` (whole `.text` objdump, 40,900,318 B; regenerate: `objdump -d -M intel
  --section=.text programs/terran.exe > scratch/m574/text.txt`), `scratch/m59/queue_census.py`,
  `scratch/m59/cfg.py`, `scratch/m59/dom.py` — gitignored. Ghidra pseudocode is in
  `ghidra_out/shard_NNN.c`; `FUN_004f6030` is shard_012.c lines 24338-29064 (4727 lines — parse it
  with Python, never read it whole), `FUN_004ef6d0` 20585-22298, `FUN_005ab650` shard_015.c
  22934-23082 (151 lines, ONE negative return: `n_units > 0x7ff`).
- Rule cases today: `test_m56_predict.py` 17/17; `m56_build.py --fixture scratch/m56_fixture_bad.json`
  exit 1; `test_walk_diff.py` 37/37; `test_classify.py` 17/17; `check_classes.py` 17/0 (delete the
  untracked `*_3x.png` siblings right after).
- **Evidence 29.7 MB, the gate FAILs at 30.** `python3 scripts/evidence.py budget` before adding
  anything; a full `m56_build` run costs ~0.65 MB. `prune` only reclaims images, so delete the traces
  of runs you are NOT citing (record their numbers in SESSION_NOTES first) and any `*_3x.png`.

## TRAPS

- **Judge production only after `cur_player` is ours again** — a read the instant the year flips can
  be a whole visit early (see above). A `m57_stores` tracer run "fixes" it only by waiting.
- The harness race is real: `r1 boundary: player walk came home to us after the flip — cur_player
  before 3 after 0` burned run `..._153623` (58 checks, 3 bad) and made the next window span two
  rounds (`6 + 2 + 2 - 9 = 1`). RE-RUN, do not edit the floor.
- `m57_ui_enqueue.py` on a just-founded base can read an EMPTY chooser (`FAIL: item 2 not in
  candidate array []`); a second attempt works. The base array compacts mid-run (18 -> 17 twice):
  locate bases BY NAME every step; `--ui-queued <idx>` is only the START index.
- A base display left open swallows every turn-end key (Escape closes a PANE safely; Escape on the
  bare map raises the quit prompt — never click OK on it). The units-not-moved confirm takes NO
  Return (`m56_build` clicks YES then the OK bar 26 px below). Orders mode `0x91b5b8 == 0` makes every
  order key a no-op; `m57_ui_enqueue` restores it after the enqueue.
- gdb: no `si` inside a breakpoint command list; `set print frame-quiet` is not a command here;
  stdout must be DRAINED. For a plain `mov [reg+disp],src` the source operand IS the after value.
  `os.pread` on `/proc/<pid>/mem` EIOs here — `seek`+`read`. Popup BARS ignore clicks (Return works on
  the default row); MENU click (75,369); TURN COMPLETE (650,410).
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm.
- One variable at a time; if two things moved together write "confounded". Documents lose to
  instruction bytes only after a poke — until then REPORT the conflict.
- Never: commit to main; `pkill -f` / `pgrep|kill` by name; Escape on the title screen; OK on the quit
  prompt; `--mode stop`; `file://` with `--load`; a clear-prefixed command; backticks in a commit
  message; `skill_manage delete`.

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
