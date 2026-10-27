# NEXT_PROMPT.md — footing for the next session (session 105 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61** (#59),
**M62** (#60), **M62B** (#61), **M64** (#62 — accrual phase measured; an arrival is attributed by the
PAYMENT, not by `ds:0x8f0d60`), **M65** (#63 — the screen read is a LOOK LOOP, not an OCR coin-flip;
harness only: `PASS 26/26` + three live `SCREEN hud` reads, no prediction run).

**M63 is NOT merged.** `milestone/m63` carries the pop instrument `scripts/m63_pop.py`, the
`0x94de84` queued-count correction (head unscaled), the 384/386 identity-crossing finding, the
validators-are-predicates finding and the `cur_base`-insufficiency proof, with **no PR**.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB of machine truth: verdict, both bases, the tagged
   CONFLICTs, the pick, the first commands. Exit 0 = READY. If it says BLOCKED, do the FIX it prints.
2. `python3 scripts/accept_ready.py` — the readiness oracle (**17** unit cases:
   `scripts/test_accept_ready.py`). In order: the screen, a running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0`; flags a TIGHT horizon when the gate is more
   than `boundaries-2` rounds away. **Since M65 its screen read re-freezes (4 looks) instead of
   trusting one OCR pass** (see WHAT M65 SETTLED) and prints a `SCREEN <class>:` line with WHY.
   **Re-read it immediately before you arm anything** — indices and minerals go stale.
3. `python3 scripts/test_hud_bar.py` — **26 cases** (18 saved frames + 8 look sequences) pinning the
   bar signal and the look semantics. ~45 s quiet, **20+ min loaded**.
4. `python3 scripts/m65_screen.py --samples 8 --save /tmp/m65` — the screen-read meter: per-sample
   class, per-band tokens (`buttonrow` 380-450, `console` 500-600) and `load1`. READ-ONLY: never
   clicks, never presses a key. Use it before believing an `unknown`, and before believing that a fix
   changed a read RATE.
5. `python3 scripts/m63_pop.py --base "Korolev Center" --boundaries 2 --tag m63pop` (on
   `milestone/m63`) — the pop tracer: breakpoints at `0x4ef5d0` and its shift/pending stores, the pay
   `0x4efedd`, the create `0x4eff4e`, an hw watch on `+0x50`. Poke and read back BEFORE attaching.
6. `python3 scripts/evidence.py audit [--delete]` / `... budget` — check the budget BEFORE adding
   evidence (gate FAILs at 30 MB; **26.3 MB at this close**). `audit --delete` removes only UNCITED
   files, `prune` only images; `find evidence -name '*_3x.png' -delete` after any classifier test.
7. `python3 scripts/m56_build.py --fixture X` writes its trace to `$TMPDIR`, not `evidence/`;
   `m64_mkfixture.py` rebuilds the run-layer fixtures from committed traces.

## WHAT M65 SETTLED (detail lives in the skill: references/screen-read.md)

- **The HUD has two rows and classify() trusts the unstable one.** Its only HUD evidence is the word
  `complete` at 380 < y < 450. `scripts/m65_screen.py --samples 8` on ONE unchanged live HUD (year
  2161, nothing clicked) printed `{"unknown": 5, "hud": 3}`: `TURN@416 COMPLETE@416` landed in
  samples 1/5/6 only, while the HUD's **bottom status bar** (`Mission@567 Year@567 2161@567`, the
  faction score row at y~581, `Energy:@582`) landed in all 8 (`evidence/m65/before_8looks_samples.json`,
  frames `evidence/m65/sample_00_unknown.png:1` … `sample_07_unknown.png:1`). Session 104's 14
  consecutive `unknown` reads were all the plain HUD. **`unknown` is not a modal** — the button row
  fragmented.
- **`smac_play.hud_status_bar(words)`** (new, pure) reads that bar: >= 3 tokens in `HUD_BAR = (548,
  592)` AND (`mission` or a `ssion|sslon|sston|ismon|sshon` fragment or `year`/`tear`) AND (a 4-digit
  2000-2500 number or `year`/`tear` or `energy`). Written against the fragments actually seen
  (`sisson tear zie` with NO year number on `evidence/m25_t7.png`, `[esston 2388` on
  `evidence/m54a/live_hud.png`); it returns its components so the caller prints WHY.
- **`classify()` is UNCHANGED** — the driver classifies exactly as before; the second look is in the
  consumer (`accept_ready.look()` + the pure `accept_ready.verdict(looks, confirm)`): a **named modal in
  ANY look decides the screen** and beats a pending promotion; `hud` on any look is believed as before;
  an `unknown` promotes only once the bar fired in **2 of 4** looks; 4 looks with neither row is still
  `unknown` and still BLOCKED — the check was NOT weakened, the screen is re-read. An unresolved
  `unknown`'s FIX now says "freeze and look at the frame", not "press Return until it reads hud".
- **The bar is HUD chrome, so it reads THROUGH anything drawn over the HUD** (quit prompt, both `g`
  choosers, NEWBASE name pane). Safe only because every modal detector runs before classify() reaches
  the HUD fall-through and the bar is consulted only on a frame classify() already called `unknown`;
  `test_hud_bar.py` asserts the NAME on those frames — weaken a modal detector and the bar starts
  calling a chooser `hud`.
- Live read-back: three `accept_ready.py` runs (20:55:45-20:56:46, year 2161 round 61, both bases
  pending 0) printed `SCREEN hud`, the third via **`classify() == unknown, but the HUD's bottom status
  bar read in 2 of 2 look(s)`**; `session_brief.py` printed `screen hud` where it printed `screen
  unknown` four hours earlier.

## WHAT M64 SETTLED (all of it is in the skill: references/production-queue.md)

- **The income add is not phase-locked to the before-snapshot, and the harness can tell.** A window's
  after-snapshot and the NEXT window's before-snapshot are the SAME ROUND read twice
  (`evidence/trace_m56_build_20261026_182354.jsonl`: `round_after r7` and `round_before r8` are both
  y2159 rnd59) and the engine plays in that gap, so the round's `+0xd0` (the add at `0x4ef7f6`) can
  already be inside the before value. `accrual_phase()` measures it; `predict(..., accrued=names)`
  adds income only when it has not landed; `credit_of` (0 when already accrued) is shared by the
  identity and the attribution, so the two cannot disagree. The double-count it replaced — r1-after 7
  -> r2-before 8, r2-after 8 -> r3-before 8, income 1 — is
  `evidence/trace_m56_build_20261026_181701.jsonl`.
- **An arrival is attributed by the PAYMENT, never by `ds:0x8f0d60`.** PAY `0x4efedd` and CREATE
  `0x4eff4e` are ONE visit invocation, so a window whose minerals show the payment made the unit; an
  arrival missing from the after-snapshot is accepted only when the payment is visible AND the unit
  READS BACK (the bounded 2 s `arrival_reread`, or the next window's before-snapshot). Compare unit
  `(x,y,type,owner)` COUNTS: `idx`/`order` are not identity (54/62 -> 53/61 -> 52/60/73 in one round —
  the array compacts) and a garrison of the same tuple already sits on the base tile.
- **The box stalls rather than auto-plays when an actionable unit exists** (year 2162 round 62
  `cur_player 3` unchanged across three reads 4 s apart, `n_units` 67 all three). Session 103's "it
  auto-plays while nothing drives it" holds only while nothing needs orders.
- Still true from M61/M62: the round order (year store `0x51f54f` while `cur_player` is still 7 ->
  0..3 -> our base visits in ARRAY order -> PAY -> CREATE -> 4..7); the name starts at byte +19, so
  `base+0x10` is not a field; a produced unit zeroes `+0xd0` and the add is gated `d0 > 0`; **income is
  not constant** (Korolev 2 -> 1 -> 2 in one round cycle).
- From unmerged **M63** (that branch's claims until it merges): the pop `FUN_004ef5d0` DOES shift the
  slots ("the slots never move" was a duplicate-value artifact); the queued-count byte is
  `0x94de84 + 8380*owner + head`, head UNSCALED; `0x5a73f0` / `0x5a6e70` are predicates, not builders,
  and a nonzero pop result is a validation failure (`0x4ef68b`); the pop's argument is the global
  `DAT_0068cbb0`, not necessarily the visited base; 384/386 is an IDENTITY CROSSING (a captured base
  keeps its record, index, name and coords).

## THE PICK — M66

One milestone, then stop. Cheapest first, and none of them is a threshold change:

1. **Give the accrual fix its live case.** Both M64 PASS runs had `gap_delta = 0` in every window
   (`evidence/trace_m56_build_20261026_200045.jsonl`) — the fix was INERT live: proved not to harm, not
   proved right. The shape needs an `income 1` base (the 2164-era box), not the `income 2` reload:
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400 --no-poke-hold`
   on a base whose windows straddle the add; report the `accrual_phase` rows.
2. **Which slot does the BUILD UI's INSERT write?** Needs one enqueue with two DIFFERENT type ids —
   every chooser value seen so far was 2, so the written index was unidentifiable.
3. Still open from M63, only if the above come cheap: who writes `DAT_0068cbb0` and when it is
   stale; why `0x5a73f0(2, 3, Korolev)` returns 1.
4. Cheap side-quests: run `scripts/m65_screen.py` at a quiet AND a loaded load (it records `load1`
   now — session 105 measured the flake and the load at the same time and called that confounded); and
   settle `check_classes.py`, whose DEFAULT names three frames deleted back in #3, so it reports
   14 PASS + 3 SKIP.
5. Keep green: `scripts/test_accept_ready.py` (**17/17**), `scripts/test_hud_bar.py` (**26/26**),
   `scripts/test_m56_predict.py` (**19/19**), `test_walk_diff.py` (37/37), `test_classify.py` (17/17),
   `check_classes.py` (exit 0), and `m56_build.py --fixture` bad=1,
   `scratch/m61/fixture_defer_ok.json`=0, `scratch/m61/fixture_beat_visit.json`=1,
   `scratch/m64/fixture_paid_readback.json`=0, `scratch/m64/fixture_paid_no_readback.json`=1.

## LIVE FACTS / KIT

- **Box at session-105 close:** terran.exe alive, year 2161 round 61 `cur_player 3`; University Base
  idx 0 minerals 1 credit 0 pending 0; Korolev Center idx 17 minerals 3 credit 2 pending 0 head 2
  price 9 — **neither base is UI-queued**, so `accept_ready.py` prints the enqueue FIX. `python3
  scripts/smac_preflight.py` (read-only) first.
- **Reload recipe (used four times across sessions 104-105, all clean):** `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` (BARE filename; `difficulty level: talent`) -> `python3
  scripts/m54g_prep.py` -> `smac_play.py --turns 1 --timeout 200 --no-escape 3000
  --orders-per-turn 1 --verbose --tag t` (`turn 0: 2150->2151 OK`) -> `m60_guard.py --stage read`
  (bases BY NAME, fresh indices) -> `m57_ui_enqueue.py --base-index <fresh idx> --cell-item 2
  --inserts 1` (`pending=1 head=2 minerals=2 d0=2`; the chooser cell moved 3 -> 4 -> 5 era to era) ->
  `accept_ready.py` -> the acceptance run WITH `--no-poke-hold`. Post-reload Korolev is minerals 2
  income 2: the gate is ~4 rounds off (roomy in 10); the 2164-era box at income 1 reads TIGHT.
- `python3 scripts/m60_guard.py --stage read|poke --value N|watch --boundaries K --timeout T --tag t`
  (refuses if a gdb is already running — `scripts/m57_credit.py --stop` detaches one), `m59_head.py
  [--stage read|poke --base NAME --minerals N] [--hold]`, `m58_price.py [--owner 3] [--type 2]`,
  `m57_stores.py --base NAME --boundaries 3 --timeout 220 --tag t`. On a CREATE line `owner=` is
  `$eax` = the base OWNER byte; `guard=` reads the global.
- `scratch/m574/text.txt` = whole `.text` objdump (40,900,318 B; `objdump -d -M intel
  --section=.text programs/terran.exe > scratch/m574/text.txt`); Ghidra pseudocode is `ghidra_out/
  shard_NNN.c` (`FUN_004f6030` shard_012.c 24338-29064, `FUN_004ef6d0` 20585-22298) — parse with
  Python, never read whole. `scratch/` is gitignored: fixtures are regenerated by a committed
  script, never committed.
- **Evidence 26.3 MB; the gate FAILs at 30** (warn band 20). A full `m56_build` run ~0.65 MB, an
  `m63_pop` or `--stage watch` run ~0.05 MB, `evidence/m65/` 0.8 MB.

## TRAPS

- **OCR COST IS LOAD, NOT CODE.** On 4 cores with `jellyfin` at 85% and load average 13-15, one
  `ocr_fast` pass took ~70 s (its own comment says ~1 s) and the classifier suites ran >20 min; the
  same suites took ~3 min once the box quieted. A slow suite is not a broken suite: check `uptime` /
  `top` first, and never claim a read RATE changed across different loads (session 105's confound).
- **A dialog/pane swallows every click and every turn-end key**, and the HUD status bar reads THROUGH
  it — the modal detectors save you, not the bar. Return clears a dialog's default row; Escape closes a
  PANE (Escape on the bare map raises the quit prompt — never click OK). `m57_ui_enqueue` on a
  just-founded base can read an EMPTY chooser; retry once. The base array compacts mid-run (18 -> 17
  twice): locate bases BY NAME, pair windows by name AND owner byte, pair UNITS by `(x,y,type,owner)`
  counts.
- **`cur_base` naming the base is NOT "the visit finished"** and **the income add is not phase-locked
  to the snapshot, and income is not constant.** Judge an arrival by the mineral payment and by reading
  the unit array back; say which shape you saw, with the window's numbers and its `accrual_phase` row.
- The harness race is still real: a run that trips `rN boundary: player walk came home to us after the
  flip` makes the next window span two rounds. RE-RUN, do not edit the floor. Reload rather than poke
  into a UI-queued acceptance (a base that just produced has `+0xd0` zeroed and cannot accrue).
- gdb: no `si` inside a breakpoint command list; stdout must be DRAINED to a file; **a printf
  newline in a generated gdb script is exactly TWO backslashes + `n`**; for a plain
  `mov [reg+disp],src` the source operand IS the after value; `os.pread` on `/proc/<pid>/mem` EIOs —
  `seek`+`read`; only 4 hardware watchpoints exist. Popup BARS ignore clicks (Return works on the
  default row); MENU click (75,369); TURN COMPLETE (650,410).
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm. Records
  are BYTES: the name is at +19, so a dword at +16 straddles it.
- A background shell waiting on `pgrep -f <name>` matches its OWN command line and never exits —
  wait on a PID or chain the job.
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
