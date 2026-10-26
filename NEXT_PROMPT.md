# NEXT_PROMPT.md — footing for the next session (session 103 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61** (#59),
**M62** (#60, instruments only — it merged with NO prediction PASS, honest in its title), **M62B**
(#61, doc fix).

Session 103 worked **M63** on branch `milestone/m63` (checkpoint commit `549e067`, branch pushed,
**no PR, no merge**): the queue pop `FUN_004ef5d0` is now measured instruction by instruction and
three standing claims were corrected, but **the acceptance never printed PASS** — three real
invocations of `scripts/m56_build.py --ui-queued <idx> --boundaries 10 --timeout 400 --no-poke-hold`
gave `3/3 verified but 1 BAD boundary check`, `1/2 verified`, `2/3 verified` (`ACCEPT_EXIT=1` each).
Read `SESSION_NOTES.md` Session 103: two of the three failures are the harness's own observation
races, and both are reproduced with the trace line that proves them.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — ≤4 KB of machine truth: verdict, both bases, the tagged
   CONFLICTs, the next pick, the first commands. `--write` regenerates `BRIEF.md`. Exit 0 = READY. If
   it says BLOCKED, do the FIX it prints before anything else.
2. `python3 scripts/accept_ready.py` — the readiness oracle. Exit 0 = one of our bases can carry the
   UI-queued acceptance; exit 1 = BLOCKED with the single cheapest fix. Checks in order: **screen
   class (a modal swallows every click AND every turn-end key)**, a running gdb, evidence headroom,
   then per base `pending > 0`, `minerals < price`, `credit > 0` (the income add is gated `d0 > 0`, so
   `credit <= 0` can NEVER accrue). Flags a TIGHT horizon when the gate is more than `boundaries-2`
   rounds away. 15 unit cases: `scripts/test_accept_ready.py`. **Re-read it immediately before you
   arm anything: the box auto-plays (below), so the index and the minerals you saw 60 s ago are
   stale.**
3. `python3 scripts/m63_pop.py --base "Korolev Center" --boundaries 2 --tag m63pop` — the session-103
   instrument: breakpoints at the pop's own instructions (`0x4ef5d0` entry, `0x4ef61a`/`0x4ef61c`
   around `dec BYTE PTR [ecx]`, `0x4ef62c` the shift store, `0x4ef642` the pending store,
   `0x4ef655`/`0x4ef66a`/`0x4ef65d` the validators) plus the pay `0x4efedd`, the create `0x4eff4e` and
   a hw watch on the base's `+0x50`. Writes `evidence/<tag>.gdblog` + `<tag>_seq.jsonl` (~12 KB).
   Poke and read back BEFORE attaching — pokes lie under a tracer.
4. `python3 scripts/evidence.py audit [--delete]` — cites come from the docs AND `scripts/*.py`
   (the `.jsonl` matching bug is fixed). `python3 scripts/evidence.py budget` before adding anything.
5. `python3 scripts/m56_build.py --fixture X` writes its trace to `$TMPDIR`, not `evidence/`.

## WHAT SESSION 103 SETTLED (detail lives in the skill: references/production-queue.md)

- **The pop `FUN_004ef5d0` drains the queue and it DOES shift.** Per step: decrement the per-faction
  queued-count byte at `0x94de84 + 8380*owner + head` (**head unscaled** — the skill's `+ type*4` was
  wrong), shift the slots left `pending` times (`0x4ef62c`), store `pending-1` (`0x4ef642`), validate
  the NEW head (`0x5a73f0` for `>= 0`, `0x5a6e70` for a negative code), loop while `[base+0x4c] != 0`.
  Measured: `POPSHIFT dest=0x95efc0 val=2 old=2` then `POPCNT newpend=0 s0=2 s1=2` — the store into
  `+0x50` is REAL and invisible only because the shifted value equals the head, so "pending decrements
  and the slots never move" was a **duplicate-value artifact**. `pending == 0` returns at `0x4ef5f4`
  without shifting, so the head never advances and the base re-builds the SAME head every round it can
  afford (which is what M61 measured).
- **The queued-count byte is `0x94de84`**, not `0x94dc84`: the game's own `$ecx` at `0x4ef613` was
  `0x9540ba` for owner 3 / head 2, and that byte read 3 at `0x4ef61a` and 2 at `0x4ef61c`; the
  sibling `0x94dc84` read 6 -> 7 in the same window (it went UP). CONFLICT closed in `NAMED.md`.
- **`0x5a73f0` / `0x5a6e70` are predicates, not builders**, and a nonzero pop result is a VALIDATION
  failure (`0x4ef68b`), not a failed build. The build is still the visit's pay `0x4efedd` +
  `call 0x5ab650` at `0x4eff4e`, and the pop runs AFTER them in the same visit.
- **The pop's argument is `DAT_0068cbb0`, a global base index, at all three call sites — and it is
  not necessarily the visited base** (`POPIN idx=8 ... owner=7 ... visit_addr=0x95ef70`).
- **384/386 is an IDENTITY CROSSING.** A captured base keeps its record, index, name AND coords; only
  the owner byte and the queue change (`trace_m56_build_20261026_165917.jsonl` r4: index 0 stayed
  `"University Base" (28,42)` while `faction 3 -> 6` and slots `[2,2,0,0] -> [384,2,0,0]`, `n_bases`
  unchanged). Pairing by name is NOT enough — assert the owner byte. The founding path
  (`0x4e48f6..0x4e4982`) never touches `+0x50..+0x74`, so a `pending 0` base's slots are whatever the
  reused record held.
- **`cur_base` (`ds:0x8f0d60`) naming the base does NOT prove the create had written the unit array.**
  `trace_m56_build_20261026_182354.jsonl` reads the SAME round twice: `round_after r7` is
  `y2159 rnd59 cp3 cur_base=Korolev Center`, minerals `7 -> 0` (paid 9), our units 7 with 2 on
  (29,42); `round_before r8` is `y2159 rnd59 cur_base=None`, our units 8 with **3** on the tile. The
  unit appeared between the two reads. M61's "refuse the deferral when `ds:0x8f0d60` already named the
  base" is therefore **not sufficient evidence** — it is the cause of session 103's run-3 FAIL.
- **The income accrual lands on either side of the before-snapshot** (`6/7`, `7/7`, `8/8`, `8/0` across
  one run's windows), so the predictor's `gate_minerals = minerals + income` double-counts whenever
  the accrual is already in the before value — session 103's run-2 FAIL. The harness can tell:
  `round_after rN` and `round_before rN+1` are the same round read twice.
- **A base's income is not constant**: Korolev's `income` field went 2 -> 1 -> 2 inside one run, twice.
- Still true from sessions 100-101: the round order (year store `0x51f54f` at `cur_player` 7 ->
  0..3 -> our base visits in ARRAY order -> PAY `0x4efedd` -> CREATE `0x4eff4e` -> 4..7); the name
  starts at byte +19 so `base+0x10` is not a field; a produced unit zeroes `+0xd0` and the income add
  is gated `d0 > 0`.

## THE PICK — M64: FIX THE TWO OBSERVATION RACES, THEN RE-RUN THE ACCEPTANCE

One milestone, then stop. **Neither fix is a threshold change** — do not widen the arrival window, do
not lower a floor, do not tune `predict()`'s economics; both fixes make the OBSERVATION correct.

1. **Arrival attribution (`m56_build.py`).** Stop treating "`cur_base` named the base" as proof the
   visit finished. Either re-read the unit array once `cur_base` is clear, or count arrivals in the
   between-window gap (the same-round double read above shows the create can land there). Keep the
   `scratch/m61/fixture_beat_visit.json` case failing (exit 1) and add a fixture for the new case: a
   paid window whose unit appears only in the NEXT read must verify, not FAIL.
2. **Accrual phase (`predict()` / the before-snapshot).** Decide, per base per window, whether the
   round's `+income` is already inside the before value, and add income only when it is not. The
   signal is the pair `round_after rN` vs `round_before rN+1` (same round, minerals differ by exactly
   `income`). Add a `test_m56_predict.py` case for the already-accrued before-snapshot; the existing
   17 cases must stay green.
3. Then `python3 scripts/accept_ready.py` (READY, exit 0) and ONE real
   `python3 scripts/m56_build.py --ui-queued <idx> --boundaries 10 --timeout 400 --no-poke-hold`
   must print **PASS**. If it cannot, record the negative and merge nothing.
4. Still open from M63, only if the two fixes come cheap: which slot the BUILD UI's INSERT writes
   (needs an enqueue with two DIFFERENT type ids — every value seen so far was 2, so the written index
   was unidentifiable); who writes `DAT_0068cbb0` and when it is stale; why `0x5a73f0(2, 3, Korolev)`
   returns 1.
5. Keep green: `scripts/test_accept_ready.py` (15/15), `scripts/test_m56_predict.py` (17/17),
   `--fixture scratch/m56_fixture_bad.json` (exit 1), `--fixture scratch/m61/fixture_defer_ok.json`
   (exit 0), `--fixture scratch/m61/fixture_beat_visit.json` (exit 1), `test_walk_diff.py` (37/37),
   `test_classify.py` (17/17), `check_classes.py` (17/0 — delete the untracked `*_3x.png` siblings).

## LIVE FACTS / KIT

- **Box at session-103 close:** terran.exe alive, year **2164** round 64, `cur_player 3`, Korolev
  Center idx **17** (29,42) minerals **0** credit **1** pending 0 head 2 price 9; University Base idx 0
  (28,42) minerals 0 credit **0** pending 0 head 2 — **neither base can carry the acceptance now**
  (`credit 0` cannot accrue; Korolev at income 1 needs ~9 rounds). **Preflight first:**
  `python3 scripts/smac_preflight.py` (read-only, exit 1 on FAIL).
- **The box AUTO-PLAYS while nothing drives it**: with every unit on HOLD the game ends our turns by
  itself (OCR `year 2163: no units need new orders`), the year moved **2151 -> 2164** in the ~10
  minutes I spent reading traces, and Korolev's index moved **18 -> 17 -> 18** across that drift. Arm
  and launch in the same breath; re-read indices BY NAME every step.
- **Reload recipe (proven again this session):** `SMAC_SAVE='m54b_clean.SAV' python3
  scripts/m54a_load.py --relaunch` (BARE filename; `difficulty level: talent`) -> `python3
  scripts/m54g_prep.py` -> `python3 scripts/smac_play.py --turns 1 --timeout 200 --no-escape 3000
  --orders-per-turn 1 --verbose --tag t` (`turn 0: 2150->2151 OK`) -> locate Korolev BY NAME
  (`m60_guard.py --stage read` prints `i`; it was 18 on the reload, 17 later) -> `python3
  scripts/m57_ui_enqueue.py --base-index <fresh idx> --cell-item 2 --inserts 1` (`pending=1 head=2
  slots=[2, 2, 0, 0, 0, 0] minerals=2 d0=2`; the chooser grid cell moved 4 -> 5 era-to-era, the script
  prints the candidate array) -> `accept_ready.py` -> the acceptance run WITH `--no-poke-hold`.
- `python3 scripts/m60_guard.py --stage read|poke --value N|watch --boundaries K --timeout T --tag t`
  (read/poke the create guard, print both our bases, or the ordered event stream; refuses if a gdb is
  already running — `scripts/m57_credit.py --stop` detaches one). `m59_head.py [--stage read|poke
  --base NAME --minerals N] [--hold]`, `m58_price.py [--owner 3] [--type 2]` (owner 3 type 2 -> 9 x 1
  = 9), `m57_stores.py --base "Korolev Center" --boundaries 3 --timeout 220 --tag t`. On the CREATE
  line `owner=` is `$eax` = `[ebp-0x28]` = the base OWNER byte; `guard=` reads the global.
- `scratch/m574/text.txt` (whole `.text` objdump, 40,900,318 B; regenerate: `objdump -d -M intel
  --section=.text programs/terran.exe > scratch/m574/text.txt`). Ghidra pseudocode `ghidra_out/
  shard_NNN.c`: `FUN_004f6030` shard_012.c 24338-29064, `FUN_004ef6d0` 20585-22298, `FUN_005ab650`
  shard_015.c 22934-23082 — parse with Python, never read whole. `scratch/` is gitignored.
- **Evidence 24.9 MB, the gate FAILs at 30** (warn band 20). A full `m56_build` run ~0.65 MB, a
  `m63_pop` run ~12 KB, a `--stage watch` run ~0.05 MB. `scripts/evidence.py audit --delete` removes
  only UNCITED files (it reports 0 now); `prune` only reclaims images. Session 103 added three
  acceptance traces and cited all of them.

## TRAPS

- **The box plays itself.** Unattended, our turns end on their own and the year runs; state you read a
  minute ago is stale. Re-read before arming, and never compare a snapshot to a state you did not read
  in the same window.
- **`cur_base` naming the base is NOT "the visit finished"** — measured above. Judge an arrival by the
  UNIT ARRAY, not by the pointer.
- **The income add is not phase-locked to the snapshot**, and **income is not constant** (2 -> 1 -> 2
  inside one run). `minerals + income` is a +-1 claim, so a "missed" arrival may be a phase error, and
  a "late" arrival may be real. Say which, with the window's numbers.
- The harness race is still real: a run that trips `rN boundary: player walk came home to us after the
  flip` makes the next window span two rounds. RE-RUN, do not edit the floor (session 103 run 1 died
  exactly here with 3/3 arrivals verified).
- A dialog/pane on screen swallows every click and every turn-end key. Check `classify()` before a UI
  enqueue; Return clears a dialog's default row, Escape closes a PANE (Escape on the bare map raises
  the quit prompt — never click OK on it). `m57_ui_enqueue` on a just-founded base can read an EMPTY
  chooser; a second attempt works. The base array compacts mid-run (18 -> 17 twice): locate bases BY
  NAME, and pair across windows by name AND owner byte (name+coords survive a capture).
- Producing a unit zeroes the base's `+0xd0` credit; with credit 0 storage cannot accrue, so a base
  that just produced cannot fund its next build — reload rather than poke into a UI-queued acceptance.
- gdb: no `si` inside a breakpoint command list; `set print frame-quiet` is not a command here; stdout
  must be DRAINED (redirect to a file). **In a generated gdb script a printf newline is exactly TWO
  backslashes + `n`** — four print a literal `\n` between every event (cost session 103 a detour). For
  a plain `mov [reg+disp],src` the source operand IS the after value. `os.pread` on `/proc/<pid>/mem`
  EIOs here — `seek`+`read`. Popup BARS ignore clicks (Return works on the default row); MENU click
  (75,369); TURN COMPLETE (650,410). Only 4 hardware watchpoints exist — budget them.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm. Records are
  BYTES: the name is at +19, so a dword at +16 straddles it.
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
