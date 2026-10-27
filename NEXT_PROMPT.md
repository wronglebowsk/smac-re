# NEXT_PROMPT.md — footing for the next session (session 111 close, 2026-10-27)

## THE LEDGER

Merged: **M54A-M54E** (#39-#44), **M54F-M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61**
(#59), **M62** (#60), **M62B** (#61), **M64** (#62), **M65** (#63), **M66** (#64), **M67**
(#65), **M69** (#66 — the enqueue writes `queue[cursor]`), **M70** (#67 — who writes the
cursor; a repaint does not rewrite the queue).

**M71 (this branch's PR) — THE COMPLETION'S POP, MEASURED LIVE. ACCEPTANCE PASS on one real
invocation and REPRODUCED** (`python3 scripts/m71_pop_watch.py --boundaries 2 --tag m71pop`
-> PASS; the same command `--tag m71pop3` on a reloaded save -> PASS). `test_m71_pop.py`
34/34. Details: NAMED.md's M71 block, SESSION_NOTES.md session 111.

**M68 is NOT merged — its acceptance FAILED.** `milestone/m68` carries the 212-rule key
identifier, its gate, `m68_key_run.py`, `m68_typebytes.py`, `m68_cellprobe.py` and
`test_m68_key_rules.py` (35/35). At round 51 the enqueue APPENDED five items in click order;
55 of 212 rules predict an append, so no key was named. M70's cursor mechanics explain the
appends; M67's three sorted read-backs came from a different state (confounded).

**M63 is NOT merged.** `milestone/m63` carries `scripts/m63_pop.py`, the `0x94de84`
queued-count correction, the 384/386 identity-crossing finding, the validators-are-predicates
finding and the `cur_base`-insufficiency proof, with **no PR**. M71 measured the pop live and
confirms its branch reading.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB of machine truth: verdict, both bases, the
   tagged CONFLICTs, the pick, the first commands. Exit 0 = READY. If it says BLOCKED, do the
   FIX it prints.
2. `python3 scripts/accept_ready.py` — the readiness oracle (17 unit cases:
   `scripts/test_accept_ready.py`). Screen, running gdb, evidence headroom, then per base
   `pending > 0`, `minerals < price`, `credit > 0`. **Re-read it immediately before you arm.**
   `--no-screen` skips the OCR. If the screen reads `dialog`, run
   `python3 scripts/m70_clear_dialog.py` (it presses Return until the dialog is gone and
   prints each look); a BUILD/base PANE needs Escape, not Return.
3. `python3 scripts/m71_pop_watch.py [--base-name NAME] [--boundaries 2] [--poke-minerals N]
   [--tag m71pop]` — **the completion/pop instrument, one invocation prints PASS or FAIL.**
   It pokes the base's minerals to the head's price and READS BACK before attaching (pokes lie
   under a tracer), arms 4 hw watchpoints (the cursor field `0x6e93dc` + queue slots 1..3) and
   10 silent conditional breakpoints (`0x4f5a93` visit marker; pop
   `0x4ef5e4/0x4ef61a/0x4ef61c/0x4ef642/0x4ef65d/0x4ef68b`; BOTH pay sites `0x4efed8` and
   `0x4f0ca1`; create `0x4eff4e`), drives real round boundaries with `smac_play`, detaches and
   reads pending/region/cursor/counts back from `/proc/pid/mem`. Its 8 gates refuse: a shape
   that cannot separate SINGLE from DRAIN, a window with no pop, a walk that ended for no
   logged reason, a pending or region read-back the logged writes do not explain, a queued
   count byte that moved by the wrong amount, ANY unmapped writer pc, and a base array that
   moved out from under the watchpoints. Logs `evidence/<tag>.gdblog` + `<tag>_seq.jsonl`.
4. `python3 scripts/m70_cursor_watch.py --arm / --stop / --acceptance` — the cursor
   instrument (same 4 hw watchpoints, the enqueue/row-click breakpoints), log
   `evidence/m70_cursor.gdblog`. `--acceptance` FAILs on any unmapped writer pc or an
   enqueue-only shape.
5. `python3 scripts/m66_insert_slot.py [--base-name NAME] [--item-a ID --item-b ID] [--slots
   12] [--trace $TMPDIR/f.jsonl]` — the two-id INSERT instrument (chooser read WITH it open,
   queue after every click). Proven pair on this save: `--item-a 193 --item-b 192`. Its own
   "layout rules that fit = []" FAIL line is NOT our acceptance — it means "no layout claim".
   `python3 scripts/m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1` is the simpler
   one-item enqueue.
6. `python3 scripts/m69_enqueue_gdb.py --arm|--stop|--parse` — the enqueue tracer.
7. `python3 scripts/test_hud_bar.py` — 26 cases, ~45 s quiet, **20+ min loaded**;
   `python3 scripts/m65_screen.py --samples 8 --save /tmp/m65` — READ-ONLY screen meter.
   `python3 scripts/m70_scan_writers.py` and `scripts/m70_type_sites.py` — static.
8. `python3 scripts/evidence.py audit [--delete]` / `... budget` — check BEFORE adding
   evidence (gate FAILs at 30 MB; **27.1 MB at this close**). `find evidence -name '*_3x.png'
   -delete` after any classifier test.
9. `python3 scratch/m71/dis.py 4ef5d0 4ef6c8` — an objdump window over `scratch/m574/text.txt`
   (small output; never read the whole dump). `m56_build.py --fixture X` writes to `$TMPDIR`.

## WHAT M71 SETTLED (NAMED.md M71 block, session 111)

- **A completion pops EXACTLY ONE item when the new head validates as available**: pending 2 ->
  1, region `[2,193,192,0...] -> [193,192,192,0...]` read back after detaching; the DRAIN
  candidate (`pending -> 0`, `[192,192,192,...]`) predicts a different region and lost.
- **The pop's shift touches `queue[k] = queue[k+1]` for k = 0..pending-1 ONLY** (store
  `0x4ef62c`, gdb reports `pc=0x4ef62e`); `queue[pending]` keeps its STALE id — so K shifts
  are NOT "shift left by K": index k is written `pending-k` times (`shift_predict` in the
  instrument, pinned by the test). The duplicate id in a read-back is a stale slot, not a copy.
- **The drain stops at the validator**: `POPRES head=193 r=1` -> `POPEXIT` (`0x4ef68b`), the
  new head still in the queue. `0x5a73f0` returns 0 iff type-record `+0x30` bit 0 is clear OR
  the owner-mask byte `+0x2c` lacks the faction bit; live records: 192 `+0x30=0x0001`,
  193 `0x0041`, 194 `0x0041`, `+0x2c = 0` for all three.
- **The completion does not touch the cursor field**: zero writes to `*0x6e93dc` across the
  whole armed window, twice; the `0x4194b3` handler (M70's zeroer) does not fire there. So the
  M67-vs-M68 difference is NOT produced by the completion — it left-shifts, it does not sort.
- **The pay that fires for a UI-queued base-type head is `0x4efedd` with `edi` = the head's
  PRICE** (`PAYA storage=9 edi=9`; run 3 `storage=10 edi=9` after the round's `+1` add at
  `0x4ef7f6`) while the base's INDEX is 0 — so `edi` is not the sweep-entry index here.
  `0x4f0ca1` never fired; `0x4f0ca6` is still unexamined, not refuted.
- The queued-count dec happens at the address the GAME computed (`0x94de84 + 8380*owner + head`
  = `0x9540ba` for owner 3 head 2); read back 1 -> 0 at `POPAFT`, and `de84[2]` read 0 after.

## STILL OPEN (in priority order)

1. **M72 pick — watch the completion GATE, not the pop.** `m71pop2` (head 193, a DESIGNED id,
   minerals poked to its price 18 and read back) FAILed its window gate: 2 boundaries, ONE
   `VISIT` with `min=18`, NO pay/pop/create; at the end `+0x3c` 5, `+0xcc` 0, `+0x30`
   `0x80007020`, `+0x98` 18. Arm `0x4f0a37` (`cmp [base+0x40], edi`), `0x4f0abb`, `0x4f0b4f`,
   `0x4f0b78` and `0x4efe41` (`cmp ebx,0x40`) and name which test sends the visit home without
   paying, and what `edi` holds at each. That explains `m71pop2` and closes the pay-site
   conflict for the designed branch. Do not re-litigate the pop — it is measured twice.
2. **Who calls the `0x4194b3` handler and what widget message `0x4d00` is** (it zeroes the
   cursor after a queue mutation; `0x584010` is the message sender, `0x4eb6b0` runs after it;
   it did NOT fire at a completion or a round boundary).
3. **M67's plan-descending LIST order still has no code behind it**: zero sites read the plan
   byte `+42`; the only 52-byte type-address computations (`0x40ad92`, `0x4164dd`, `0x4188f9`,
   `0x418932`) hand the record to the row's string builders `FUN_00626634` / `FUN_006265a2`.
4. **The `-3 / -6` formula** — the stride CONFLICT stands: `0x984d38 + (-v)*48` (`0x40adae`,
   `0x4164f5`) vs `+(-v)*16` (`0x418914`, `0x41894d`).
5. Open from 104/105: the `income 1` accrual case (every M64 PASS window had `gap_delta = 0`):
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`.
6. Keep green: `test_accept_ready` 17/17, `test_hud_bar` 26/26, `test_m56_predict` 19/19,
   `test_walk_diff` 37/37, `test_classify` 17/17, `test_m66_layouts` 10/10,
   `test_m67_sort_keys` 15/15, `test_m68_key_rules` 35/35, `test_m69_cursor` 15/15,
   `test_m70_cursor` 23/23, **`test_m71_pop` 34/34**, `check_classes.py` exit 0.

## LIVE FACTS / KIT

- **Box at session-111 close:** terran.exe alive, year 2153 round 53 `cur_player` varies;
  **University Base idx 0 (record `0x95da10`) pending 1** slots
  `[193, 192, 192, 0, 0, 0, 0, 0, 0, 0, 9225, 0]`, minerals 1, `+0xd0` 0, cursor field
  `0x6e93dc` = 0. `de84[2]` 0, `de84[192]` 1, `de84[193]` 1, `de84[194]` 0. Korolev Center
  does not exist in this instance (a fresh `m54g_prep`-style founding is needed for it).
- **Prices (`scripts/m56_build.py price_of`, multiplier 9 on this save):** head 2 Scout Patrol
  9, 192/193 (cost 2) 18, 194 Impact Infantry (cost 3) 27. **A head of type 2 completes the
  moment storage >= price; a head of type 193 did NOT complete in two boundaries** (open #1).
- Free chooser ids: 194 and 2 and 0 and 1; 195 -> -3, 196+ recordless -> negatives. Ids 192
  and 193 are queued now (their count bytes read 1). The enqueue refuses `pending >= 9`
  (`0x418b05`) and both gdb instruments FAIL rather than arm when `pending + 2 > 9`.
- **Reload recipe (used ten times, sessions 104-111, all clean):**
  `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename, ~35 s)
  -> `smac_play.py --turns 1 --timeout 200 --no-escape 3000 --orders-per-turn 1 --verbose
  --tag t` -> `accept_ready.py` (its FIX is "enqueue on University Base") ->
  `m66_insert_slot.py --base-name "University Base" --item-a 193 --item-b 192` (or
  `m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1`) -> the acceptance run.
- gdb: 4 hardware watchpoints and **10 clean silent breakpoints worked** (M71's arm; ~35 s per
  boundary under them). Conditional breakpoints (`if $esi+0x95da10 == $b`, `if $ecx == $b`)
  keep every other base out of the log. No `si` inside a breakpoint command list; stdout must
  be DRAINED to a file (`stdbuf -o0`, `stdout=<file>`); a printf newline in a generated gdb
  script is exactly TWO backslashes + `n`; **a watchpoint reports the pc AFTER the store**
  (map it back, window 16 bytes); `os.pread` on `/proc/<pid>/mem` EIOs — `seek`+`read`.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm —
  and it is a POINTER to the base record. Records are BYTES: a type record (stride 52, base
  `0x98ad88`) has name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0
  is the validator's first test); a base record has name `+19`, storage `+0x40`, pending
  `+0x4c`, queue `+0x50..+0x74`, `+0x98` = a copy of storage written by the pay epilogues.
- **Evidence 27.1 MB of the 30 MB FAIL line** (59 images = 12.0 MB): a pop/cursor run is a few
  KB. Prune with `evidence.py audit --delete`.

## TRAPS

- **A dialog swallows every click and every turn-end key, and the HUD status bar reads THROUGH
  it.** Proven again this session: a "the minerals output of University Base is not sufficient
  to support Scout" dialog made two different scripts' chooser clicks no-ops (guard stayed 0,
  pending unchanged); after `m70_clear_dialog.py` the identical click set guard 3 and the
  INSERT worked. Run it before blaming the chooser map. Return clears a dialog's default row;
  a BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt — never OK).
- **OCR COST IS LOAD, NOT CODE.** With jellyfin/winedevice busy, one `ocr_fast` pass took ~70 s
  and the classifier suites >20 min; the same suites took ~3 min quiet. Check `uptime` first.
- The base array compacts mid-run: locate bases **BY NAME**, pair windows by name AND owner
  byte, pair UNITS by `(x,y,type,owner)` counts. M71's gate 8 exists because a moved record
  would mean the watchpoints watched someone else's queue.
- **The queue tail holds STALE ids and the shift only reaches `0..pending-1`** (M71), so
  `queue[pending]` survives a pop with its old value — never read a queue by "first empty
  slot", never treat slot 10 (`+0x78`, 9225 here) as a queue entry, and never plan on a
  duplicate: **the engine refuses an id the queue already holds**. Id 0 is both Colony Pod and
  the empty marker. The queue sentinel is `-39` (`0xffffffd9`), not -38.
- A negative queue value belongs to the TYPE, not to a bad click (196 -> -6, 195 -> -3). Never
  put 195/196+ in a shape.
- The per-faction count arrays read one LOWER for every queued id mid-click and settle by OK;
  `0x94dc84 + 0x20bc*owner + (512 + tid)` IS the same byte as `0x94de84 + 0x20bc*owner + tid`.
  Diff whole rows.
- **A PASS on a shape that cannot discriminate is not a PASS of the rule.** Compute the
  candidate predictions from the baseline first and refuse the shape if they all agree (M71's
  version: SINGLE vs DRAIN must predict different regions). An APPEND engine is consistent
  with ~55 rules — a FAIL there means "no key claim", not "the key is wrong".
- The harness race is real: a run that trips `rN boundary: player walk came home to us after
  the flip` makes the next window span two rounds. RE-RUN, do not edit the floor. Reload
  rather than poke into a UI-queued accrual acceptance (a base that just produced has `+0xd0`
  zeroed and cannot accrue) — but poking minerals and reading back BEFORE attaching is exactly
  right for a completion acceptance, and the poke must be read back.
- One variable at a time; if two things moved together write "confounded", not "because".
  Documents lose to instruction bytes only after a poke — until then REPORT the conflict.
- Never: commit to main; `pkill -f` / `pgrep|kill` by name; Escape on the title screen; OK on
  the quit prompt; `--mode stop`; `file://` with `--load`; a clear-prefixed command; backticks
  in a commit message; `skill_manage delete`.

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
