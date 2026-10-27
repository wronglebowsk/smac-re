# NEXT_PROMPT.md — footing for the next session (session 104 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61** (#59),
**M62** (#60), **M62B** (#61), **M64** (#62 — two PASS invocations: the accrual phase is measured
and an arrival is attributed by the PAYMENT, not by `ds:0x8f0d60`).

**M63 is NOT merged.** `milestone/m63` carries the pop instrument `scripts/m63_pop.py`, the
`0x94de84` queued-count correction (head unscaled), the 384/386 identity-crossing finding, the
validators-are-predicates finding and the `cur_base`-insufficiency proof, with **no PR**. M64 copied
its two acceptance traces onto main (`evidence/trace_m56_build_20261026_181701.jsonl`,
`..._182354.jsonl`) so the citations resolve; the rest of its docs work is still only on that branch.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB of machine truth: verdict, both bases, the tagged
   CONFLICTs, the pick, the first commands. Exit 0 = READY. If it says BLOCKED, do the FIX it prints.
2. `python3 scripts/accept_ready.py` — the readiness oracle (15 unit cases:
   `scripts/test_accept_ready.py`). Checks, in order: screen class, a running gdb, evidence
   headroom, then per base `pending > 0`, `minerals < price`, `credit > 0`; flags a TIGHT horizon
   when the gate is more than `boundaries-2` rounds away. **Its screen read is an OCR coin-flip on
   an animating map**: session 104 got 14 consecutive `classify() == 'unknown'` verdicts on frames
   that `vision_analyze` shows as the plain tactical HUD (MENU / COMMLINK / TURN COMPLETE / unit
   panel / `Mission Year 2164`), while 3 of 6 samples of the same screen read `hud`. Re-run it a few
   times, and freeze + look before you let it stop you. **Re-read it immediately before you arm
   anything** — indices and minerals go stale.
3. `python3 scripts/m63_pop.py --base "Korolev Center" --boundaries 2 --tag m63pop` (on
   `milestone/m63`) — the pop tracer: breakpoints at `0x4ef5d0`, `0x4ef61a`/`0x4ef61c`, `0x4ef62c`,
   `0x4ef642`, `0x4ef655`/`0x4ef66a`/`0x4ef65d`, the pay `0x4efedd`, the create `0x4eff4e`, an hw
   watch on `+0x50`. Poke and read back BEFORE attaching.
4. `python3 scripts/evidence.py audit [--delete]` / `... budget` — check the budget BEFORE adding
   evidence (the gate FAILs at 30 MB; 25.5 MB at this close).
5. `python3 scripts/m56_build.py --fixture X` writes its trace to `$TMPDIR`, not `evidence/`.
6. `python3 scripts/m64_mkfixture.py` — rebuilds the run-layer fixtures from committed traces
   (`scratch/m64/fixture_paid_readback.json` exit 0, `scratch/m64/fixture_paid_no_readback.json`
   exit 1, and it REBUILDS `scratch/m61/fixture_beat_visit.json` in place — see the CONFLICT note in
   `SESSION_NOTES.md` Session 104: its old discriminator was the pointer, and the pointer is not
   evidence).

## WHAT M64 SETTLED (detail lives in the skill: references/production-queue.md)

- **The income add is not phase-locked to the before-snapshot, and the harness can tell.** A
  window's after-snapshot and the NEXT window's before-snapshot are the SAME ROUND read twice
  (`round_after r7` and `round_before r8` are both y2159 rnd59 in
  `evidence/trace_m56_build_20261026_182354.jsonl`), and the engine plays in that gap, so the
  round's `+0xd0` can already be inside the before value. A gap delta equal to `income` IS that add
  (the add is exactly `+0xd0` at `0x4ef7f6`; `scripts/m57_stores.py`, `evidence/trace_m574c.jsonl`
  show the only `+0x40` stores a visit reaches are that add and the pay). Measured double-count:
  `evidence/trace_m56_build_20261026_181701.jsonl`, Korolev Center, income 1 — r1-after 7 ->
  r2-before 8 (add landed in the gap), r2-after 8 -> r3-before 8 (it did not); the old
  `predict(..., income_first=True)` added the income both times, so r2 predicted a payment that
  never happened (storage 8 -> 8) and the identity printed `8 + credit 1 - price 9 = 0, observed 8`.
  `accrual_phase()` measures it; `predict(..., accrued=names)` adds income only when it has not
  landed; `credit_of` (0 when already accrued) is shared by the identity and the attribution, so the
  two cannot disagree.
- **An arrival is attributed by the PAYMENT, never by `ds:0x8f0d60`.** PAY `0x4efedd` and CREATE
  `0x4eff4e` are ONE visit invocation (`evidence/m61a_seq.jsonl`: PAY->CREATE adjacent, at
  `cur_player 3`, four player switches after the year store), so a window whose minerals show the
  payment made the unit. The pointer named Korolev Center at the after-snapshot of r7 of
  `evidence/trace_m56_build_20261026_182354.jsonl` — which had just paid 7 -> 0 — while the unit
  Korolev paid for appears only in the next read of the SAME round; M61's rule called that a model
  gap and M64 measured it wrong. An arrival missing from the after-snapshot is now accepted when
  the payment is visible AND the unit READS BACK (a same-round re-read of the unit array — the
  `arrival_reread` event, bounded 2 s, stops the instant the year changes — or the next window's
  before-snapshot). The re-read compares **counts**, not key presence: a garrison of the same
  `(x,y,type,owner)` already sits on the base tile, so "the key is in the snapshot" says nothing.
- **`idx` is not identity and `order` is not identity.** In that same trace the two Korolev garrisons
  read idx 54/62 at r7-before, 53/61 at r7-after and 52/60/73 at r8-after (7 records died in the
  round — the unit array compacts), and the driver's `h` re-orders a produced unit from 0 to 2.
  Pair units by `(x,y,type,owner)` COUNTS.
- **The box stalls rather than auto-plays when an actionable unit exists**: year 2162 round 62
  `cur_player 3` unchanged across three reads 4 s apart (`n_units` 67 all three); three `Return`
  presses moved it to 2164 and Korolev bought (minerals 5 -> 0, credit 2 -> 1). Session 103's "it
  auto-plays while nothing drives it" holds only while nothing needs orders.
- Still true from M61/M62 and unchanged by M64: the round order (year store `0x51f54f` while
  `cur_player` is still 7 -> 0..3 -> our base visits in ARRAY order -> PAY -> CREATE -> 4..7); the
  name starts at byte +19 so `base+0x10` is not a field; a produced unit zeroes the base's `+0xd0`
  and the income add is gated `d0 > 0`, so a base that just produced cannot fund its next build;
  **a base's income is not constant** (Korolev's went 2 -> 1 -> 2 inside one round cycle).
- Inherited from M63 (unmerged — treat as that branch's claims until it merges): the pop
  `FUN_004ef5d0` DOES shift the slots and "the slots never move" was a duplicate-value artifact; the
  per-faction queued-count byte is `0x94de84 + 8380*owner + head` with head UNSCALED; `0x5a73f0` /
  `0x5a6e70` are predicates, not builders, and a nonzero pop result is a validation failure
  (`0x4ef68b`); the pop's argument is the global `DAT_0068cbb0`, not necessarily the visited base;
  384/386 is an IDENTITY CROSSING (a captured base keeps its record, index, name and coords).

## THE PICK — M65

One milestone, then stop. Cheapest first, and none of them is a threshold change:

1. **Fix the readiness oracle's screen read** (`scripts/accept_ready.py`): re-freeze until a known
   HUD token lands (TURN COMPLETE / COMMLINK / Mission Year) instead of trusting one OCR pass, or
   stop treating `unknown` as a modal. Pin it with `scripts/test_accept_ready.py` cases on saved
   frames; any NEW screen class goes into the classifier tests with saved frames before a driver
   uses it. No game time needed.
2. **Give the accrual fix its live case.** Both M64 PASS runs had `gap_delta = 0` in every window
   (`evidence/trace_m56_build_20261026_200045.jsonl`), so the fix was INERT live — proved not to
   harm, not proved right. The shape needs an `income 1` base (the 2164-era box), not the `income 2`
   reload. Run `python3 scripts/m56_build.py --ui-queued <idx> --boundaries 10 --timeout 400
   --no-poke-hold` on a base whose windows straddle the add, and report the `accrual_phase` rows.
3. **Which slot does the BUILD UI's INSERT write?** Needs one enqueue with two DIFFERENT type ids —
   every chooser value seen so far was 2, so the written index was unidentifiable.
4. Still open from M63, only if the above come cheap: who writes `DAT_0068cbb0` and when it is
   stale; why `0x5a73f0(2, 3, Korolev)` returns 1.
5. Keep green: `scripts/test_accept_ready.py` (15/15), `scripts/test_m56_predict.py` (**19/19**),
   `--fixture scratch/m56_fixture_bad.json` (exit 1),
   `--fixture scratch/m61/fixture_defer_ok.json` (exit 0),
   `--fixture scratch/m61/fixture_beat_visit.json` (exit 1, as rebuilt by `m64_mkfixture.py`),
   `--fixture scratch/m64/fixture_paid_readback.json` (exit 0),
   `--fixture scratch/m64/fixture_paid_no_readback.json` (exit 1), `test_walk_diff.py` (37/37),
   `test_classify.py` (17/17), `check_classes.py` (17/0 — delete the untracked `*_3x.png` siblings
   right after running the classifier tests).

## LIVE FACTS / KIT

- **Box at session-104 close:** terran.exe alive, year 2161, Korolev Center idx 18 (29,42) minerals 3
  credit 1 pending 0 head 2 price 9 income 2; University Base idx 0 (28,42) minerals 1 credit 0
  pending 0 — **neither base is UI-queued**, so expect `session_brief.py` to print the enqueue FIX.
  `python3 scripts/smac_preflight.py` (read-only) first.
- **Reload recipe (used twice this session, both clean):** `SMAC_SAVE='m54b_clean.SAV' python3
  scripts/m54a_load.py --relaunch` (BARE filename; `difficulty level: talent`) -> `python3
  scripts/m54g_prep.py` -> `python3 scripts/smac_play.py --turns 1 --timeout 200 --no-escape 3000
  --orders-per-turn 1 --verbose --tag t` (`turn 0: 2150->2151 OK`) -> `python3
  scripts/m60_guard.py --stage read` prints the bases BY NAME with their fresh indices -> `python3
  scripts/m57_ui_enqueue.py --base-index <fresh idx> --cell-item 2 --inserts 1` (`pending=1 head=2
  minerals=2 d0=2`; the chooser cell moved 3 -> 4 -> 5 era to era and the script prints the candidate
  array) -> `accept_ready.py` -> the acceptance run WITH `--no-poke-hold`. After the reload Korolev
  sits at minerals 2 income 2, so the gate is ~4 rounds away — comfortable in 10 boundaries; the
  2164-era box at income 1 is ~9 and `accept_ready.py` calls that TIGHT.
- `python3 scripts/m60_guard.py --stage read|poke --value N|watch --boundaries K --timeout T --tag t`
  (read/poke the create guard `ds:0x8f0d70`, print both our bases, or the ordered event stream;
  refuses if a gdb is already running — `scripts/m57_credit.py --stop` detaches one),
  `m59_head.py [--stage read|poke --base NAME --minerals N] [--hold]`, `m58_price.py [--owner 3]
  [--type 2]` (owner 3 type 2 -> 9), `m57_stores.py --base "Korolev Center" --boundaries 3 --timeout
  220 --tag t`. On the CREATE line `owner=` is `$eax` = the base OWNER byte; `guard=` reads the global.
- `scratch/m574/text.txt` (whole `.text` objdump, 40,900,318 B; regenerate: `objdump -d -M intel
  --section=.text programs/terran.exe > scratch/m574/text.txt`). Ghidra pseudocode `ghidra_out/
  shard_NNN.c`: `FUN_004f6030` shard_012.c 24338-29064, `FUN_004ef6d0` 20585-22298, `FUN_005ab650`
  shard_015.c 22934-23082 — parse with Python, never read whole. `scratch/` is gitignored, so
  fixtures are regenerated by a committed script, never committed themselves.
- **Evidence 25.5 MB; the gate FAILs at 30** (warn band 20). A full `m56_build` run ~0.65 MB, an
  `m63_pop` run ~12 KB, a `--stage watch` run ~0.05 MB. `audit --delete` removes only UNCITED files;
  `prune` only reclaims images. Delete the `*_3x.png` siblings `check_classes.py` writes.

## TRAPS

- **`cur_base` naming the base is NOT "the visit finished" and NOT "the create wrote the unit
  array"** — measured twice now. Judge an arrival by the mineral payment and by reading the unit
  array back.
- **The income add is not phase-locked to the snapshot, and income is not constant.** A "missed"
  arrival may be a phase error and a "late" arrival may be real; say which, with the window's
  numbers and its `accrual_phase` row.
- The harness race is still real: a run that trips `rN boundary: player walk came home to us after
  the flip` makes the next window span two rounds. RE-RUN, do not edit the floor.
- **A dialog/pane on screen swallows every click and every turn-end key**, but `classify()` can be
  wrong about it (see the instruments). Return clears a dialog's default row; Escape closes a PANE
  (Escape on the bare map raises the quit prompt — never click OK on it). `m57_ui_enqueue` on a
  just-founded base can read an EMPTY chooser; a second attempt works. The base array compacts
  mid-run (18 -> 17 twice more this session): locate bases BY NAME, pair across windows by name AND
  owner byte (name+coords survive a capture), and pair UNITS by `(x,y,type,owner)` counts.
- Producing a unit zeroes the base's `+0xd0`; with credit 0 storage cannot accrue, so a base that
  just produced cannot fund its next build — reload rather than poke into a UI-queued acceptance.
- gdb: no `si` inside a breakpoint command list; `set print frame-quiet` is not a command here;
  stdout must be DRAINED (redirect to a file). **In a generated gdb script a printf newline is
  exactly TWO backslashes + `n`.** For a plain `mov [reg+disp],src` the source operand IS the after
  value. `os.pread` on `/proc/<pid>/mem` EIOs here — `seek`+`read`. Popup BARS ignore clicks (Return
  works on the default row); MENU click (75,369); TURN COMPLETE (650,410). Only 4 hardware
  watchpoints exist.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm. Records
  are BYTES: the name is at +19, so a dword at +16 straddles it.
- One variable at a time; if two things moved together write "confounded". Documents lose to
  instruction bytes only after a poke — until then REPORT the conflict.
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
