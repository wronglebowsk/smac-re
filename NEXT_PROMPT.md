# NEXT_PROMPT.md — footing for the next session (session 100 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58). Session 100
**PASSED M61** (`python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400
--no-poke-hold` -> `PASS production prediction: 3 verified unit arrivals over 10 boundaries, every
prediction and every observed arrival accounted, queue bookkeeping exact — queue filled by the GAME's
BUILD UI (0 memory writes), paid by income at 2/round`, **56 checks / 0 bad**, trace
`evidence/trace_m56_build_20261026_162511.jsonl`); the M61 PR is the one this session submitted from
`milestone/m61` — read `git log --oneline -3` / `gh pr list` for its number before quoting it.

Session 101 shipped **M62 (instruments, not research)**: `accept_ready.py`, `session_brief.py`,
`evidence.py audit`, fixture traces out of `evidence/`, tagged conflicts, and a 22.8 MB evidence
budget (was 27.7). **No prediction-harness PASS was produced this session** — the one live run
FAILED (`1/2 positive predictions verified`) and the reason is now half-explained, see "THE PICK".

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — ≤4 KB of machine truth: verdict, both bases, the tagged
   CONFLICTs, the next pick, the first commands. `--write` regenerates `BRIEF.md`. Exit 0 = READY.
2. `python3 scripts/accept_ready.py` — the readiness oracle. Exit 0 = one of our bases can carry
   the UI-queued acceptance; exit 1 = BLOCKED with the single cheapest fix. It checks, in order:
   **screen class (a modal swallows every click AND every turn-end key)**, a running gdb, evidence
   headroom (29 MB), then per base `pending > 0`, `minerals < price`, `credit > 0` (the income add
   is gated `d0 > 0`, so `credit <= 0` can NEVER accrue). It also flags a TIGHT horizon when the
   gate is more than `boundaries-2` rounds away. 13 unit cases: `scripts/test_accept_ready.py`.
3. `python3 scripts/evidence.py audit [--delete]` — cites are taken from the docs AND from
   `scripts/*.py`, so classifier frames are safe. Note the fix: `load_cites()` never matched
   `.jsonl`, so before M62 no trace could ever count as cited (it now lists 10 files / 0.1 MB).
4. `python3 scripts/m56_build.py --fixture X` writes its trace to `$TMPDIR`, not `evidence/`.

## WHAT SESSIONS 100-101 SETTLED (detail lives in the skill: references/production-queue.md)

- **The round order** (measured, `evidence/m61a_seq.jsonl`): the year store `0x51f54f` fires while
  `cur_player` is 7 -> `cur_player` 0,1,2,3 -> our bases' visits in ARRAY order -> PAY `0x4efedd`
  (edi = the price) -> CREATE `0x4eff4e` -> `cur_player` 4..7. The pay and the create are ONE visit
  invocation (nothing in `.text` jumps into that block). **An arrival is never a round late; a
  snapshot can be early.**
- `ds:0x8f0d60` names the base being visited; `m56_build.py` logs it per window and refuses the F1
  deferral when it already named the predicted base (`scratch/m61/mkfix.py` proves both directions).
- `base+0x10` is NOT a field: the name starts at byte +19, so the dword straddles +16..+18 and
  `name[0]` (24/24 bases).
- Traps that cost real time: a modal voids every click; a produced unit zeroes `+0xd0` and the
  income add is gated `d0 > 0`, so credit 0 can never accrue again; the base array compacts
  mid-run, so locate bases BY NAME.
- Conflicts are tagged `CONFLICT:` in NAMED.md and printed by the brief.

## THE PICK — M63: WHAT WRITES 384/386 INTO `base+0x50`, AND WHAT THE POP DOES TO THE SLOTS

One milestone, then stop. Do not tune `predict()` to observations. **Reload the clean save before
anything else** (`m54a_load --relaunch` -> `m54g_prep` -> `smac_play --turns 1`): the box drifted —
`bases_ours` went 2 -> 1 and `units_ours` 9 -> 5 by year 2174 r74, so it can no longer host the
acceptance.

Session 101's one live run FAILED (`1/2 positive predictions verified`,
`evidence/trace_m56_build_20261026_165917.jsonl`) and left a sharp observation:

- r3: University `pending 1 -> 0` with the slot array `[2,2,0,0]` unchanged before and after — the
  pop decrements pending and does NOT visibly shift the slots (M61 saw the same at Korolev).
- r4: TWO bases' head slots read **384** and **386** in the same window while Korolev read `2`; the
  garbage head reached the bookkeeping comparison and produced "queue held — head 2->384".
- r2: University paid (minerals 6 -> 0) and no unit of that tuple appeared on the tile; the same
  run lost University Base. **CONFOUNDED** — base death and the queue anomaly are in the same
  windows; do not write "the base died because ...", and do not assume a dead record explains 384
  (two bases carried it at once).
- Measured over every trace: 38/303 of our rows and 2804 rows overall hold a slot outside `0..23`.
  Never assume a slot is a type id; a global "slots are types" floor would fail on the AI bases.

1. Settle the pop's operand from the bytes: `FUN_004ef5d0`, `0x4ef5f4 je 0x4ef684` (pending == 0),
   the shift and the pending store (`0x4ef613`, `0x4ef641`), the per-faction queued-count byte.
2. Extend `scripts/m60_guard.py --stage watch` with a breakpoint on the pop entry and a hardware
   watchpoint on ONE named base's `+0x50..+0x74` (`+0x4c` too), 2-3 boundaries, ONE variable per
   run, the other base the control. Print before/after per store.
3. Say what a dead/stale base record looks like (`n_bases` compaction, coords, owner byte) and
   whether a freed record's `+0x50` holds anything meaningful.
4. Whatever the answer, `accept_ready.py` must keep its contract: READY means *a positive
   prediction is possible*, not *the run will pass* — the support-disband path (Operations Director
   "minerals output ... not sufficient to support ... has been disbanded") can still eat a created
   unit, and that is not yet modelled.
5. Old sub-item, still open from M61/M62: cite the pop bytes and state the queue representation
   (head slot vs pending vs slot array), then re-check M59's "the head slot is the truth".
6. Acceptance: `python3 scripts/accept_ready.py` must print READY (exit 0) on the reloaded box and
   BLOCKED (exit 1) with the right fix on a dead one, and `python3 scripts/m56_build.py
   --ui-queued <idx> --boundaries 10 --timeout 400 --no-poke-hold` must print **PASS on ONE real
   invocation**. If it cannot, record the negative and merge nothing.
7. Keep green: `scripts/test_accept_ready.py` (13/13), `scripts/test_m56_predict.py` (17/17),
   `--fixture scratch/m56_fixture_bad.json` (exit 1), `--fixture scratch/m61/fixture_defer_ok.json`
   (exit 0), `--fixture scratch/m61/fixture_beat_visit.json` (exit 1); add cases for anything new.

## LIVE FACTS / KIT

- **Box at session-100 close:** terran.exe alive, year **2162**, round 62, `cur_player 3`, guard 0,
  Korolev Center idx 18 (29,42) minerals 3 income 2 pending 0 head 2, 3 units on tile; University
  Base idx 0 (28,42) minerals 0 income -1 pending 0 head 2, 6 on tile; 9 ours units. **Preflight
  first:** `python3 scripts/smac_preflight.py` (read-only, exit 1 on FAIL — evidence size is one of
  the invariants).
- **Reload recipe (the proven path, used for the M61 acceptance):** `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` (BARE filename; `difficulty level: talent`) -> `python3
  scripts/m54g_prep.py` -> `python3 scripts/smac_play.py --turns 1 --timeout 200 --no-escape 3000
  --orders-per-turn 1 --verbose --tag t` (`Korolev Center founded in 2150`, `turn 0: 2150->2151 OK`)
  -> locate Korolev **BY NAME** (`python3 scripts/m60_guard.py --stage read` prints `i`; it was 18
  after the reload) -> `python3 scripts/m57_ui_enqueue.py --base-index <fresh idx> --cell-item 2
  --inserts 1` (`pending=1 head=2 slots=[2, 2, 0, 0, 0, 0] minerals=2 d0=2`) -> `python3
  scripts/m59_head.py --stage read --hold` -> the acceptance run WITH `--no-poke-hold`.
- `python3 scripts/m60_guard.py --stage read|poke --value N|watch --boundaries K --timeout T --tag t`
  — read/poke the guard, print both our bases (minerals, income, pending, head, `+0x30`, `+0x38`,
  `+0x98`, `+0x10`, per-tile unit count, our unit total), or run the ordered event stream. The watch
  stage arms: hw watchpoints on `0x8f0d70` / `0x985b00` / `0x985dcc` (3 of the 4 DR slots) plus
  breakpoints at `0x4ef6d0`, `0x4efedd`, `0x4eff4e`; every command list is `silent` + printf +
  `continue` and gdb stdout goes straight to a file. It refuses if a gdb is already running
  (`scripts/m57_credit.py --stop` detaches one). NOTE: on the CREATE line `owner=` is `$eax`, which at
  `0x4eff47` holds `[ebp-0x28]` = the base OWNER byte; `guard=` reads the global.
- `python3 scripts/m59_head.py [--stage read|poke --base NAME --minerals N] [--hold]`,
  `python3 scripts/m58_price.py [--owner 3] [--type 2]` (price = factor_tenths x type_cost; owner 3
  type 2 -> 9 x 1 = 9), `python3 scripts/m57_stores.py --base "Korolev Center" --boundaries 3
  --timeout 220 --tag t` (the `+0x40` store tracer; arm only when no gdb runs; poke and read back
  BEFORE attaching — pokes lie under a tracer).
- `scratch/m574/text.txt` (whole `.text` objdump, 40,900,318 B; regenerate: `objdump -d -M intel
  --section=.text programs/terran.exe > scratch/m574/text.txt`), `scratch/m61/census10.py`,
  `scratch/m61/mkfix.py`, `scratch/m59/queue_census.py`, `scratch/m59/cfg.py`, `scratch/m59/dom.py` —
  gitignored. Ghidra pseudocode in `ghidra_out/shard_NNN.c`: `FUN_004f6030` shard_012.c 24338-29064
  (4727 lines — parse with Python, never read whole), `FUN_004ef6d0` 20585-22298, `FUN_005ab650`
  shard_015.c 22934-23082 (151 lines, ONE negative return: `n_units > 0x7ff`).
- Rule cases today: `test_m56_predict.py` 17/17; `m56_fixture_bad.json` exit 1;
  `m61/fixture_defer_ok.json` exit 0; `m61/fixture_beat_visit.json` exit 1; `test_walk_diff.py`
  37/37; `test_classify.py` 17/17; `check_classes.py` 17/0 (delete the untracked `*_3x.png` siblings
  right after).
- **Evidence 27.1 MB, the gate FAILs at 30.** `python3 scripts/evidence.py budget` before adding
  anything; a full `m56_build` run costs ~0.65 MB, a `--stage watch` run ~0.05 MB. `prune` only
  reclaims images, so delete the traces of runs you are NOT citing (record their numbers in
  SESSION_NOTES first) and any `*_3x.png`. Session 100 deleted 17 uncited `trace_m56_build_*` files
  (29.7 -> 25.7 MB) to get preflight green.

## TRAPS

- **Production runs inside our own slot, AFTER `cur_player` is written to 3.** A snapshot the instant
  `cur_player` becomes 3 can be before the upkeep; `ds:0x8f0d60` says which base has been reached.
  Judge production only after the walk is ours AND the pointer has reached the base.
- The harness race is real: a run that trips `r1 boundary: player walk came home to us after the flip
  — cur_player before 3 after 0` makes the next window span two rounds. RE-RUN, do not edit the floor.
- A dialog/pane on screen swallows every click and every turn-end key. Check `classify()` before a UI
  enqueue; Return clears a dialog's default row, Escape closes a PANE (Escape on the bare map raises
  the quit prompt — never click OK on it). `m57_ui_enqueue` on a just-founded base can read an EMPTY
  chooser (`FAIL: item 2 not in candidate array []`); a second attempt works. The base array compacts
  mid-run (18 -> 17 twice): locate bases BY NAME every step; `--ui-queued <idx>` is only the START
  index.
- Producing a unit zeroes the base's `+0xd0` credit; with credit 0 storage cannot accrue (the add is
  gated `d0 > 0`), so a base that just produced cannot fund its next build — reload rather than poke
  your way into a UI-queued acceptance.
- gdb: no `si` inside a breakpoint command list; `set print frame-quiet` is not a command here;
  stdout must be DRAINED (the watch stage redirects it to a file). For a plain `mov [reg+disp],src`
  the source operand IS the after value. `os.pread` on `/proc/<pid>/mem` EIOs here — `seek`+`read`.
  Popup BARS ignore clicks (Return works on the default row); MENU click (75,369); TURN COMPLETE
  (650,410). Only 4 hardware watchpoints exist — budget them.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm. And
  record fields are BYTES: the name is at +19, so a dword at +16 straddles it.
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
