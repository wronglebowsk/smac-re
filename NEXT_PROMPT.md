# NEXT_PROMPT.md — footing for the next session (session 113 close, 2026-10-27)

## THE LEDGER

Merged: **M54A-M54E** (#39-#44), **M54F-M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61**
(#59), **M62** (#60), **M62B** (#61), **M64** (#62), **M65** (#63), **M66** (#64), **M67**
(#65), **M69** (#66 — the enqueue writes `queue[cursor]`), **M70** (#67 — who writes the
cursor; a repaint does not rewrite the queue).

**M71 merged (#68) — the completion's pop pops ONE item, shifts `0..pending-1` only, never writes
the cursor.**

**M72 (this branch's PR) — WHICH TEST SENDS THE VISIT HOME WITHOUT PAYING. ACCEPTANCE PASS on two
real invocations that differ in ONE variable**: `python3 scripts/m72_gate_watch.py --boundaries 2
--tag m72gate4` -> PASS (storage 18: `POSAFF` -> `BAILAFF` `0x4efa63`, nothing paid); the same
state with `--poke-minerals 27 --boundaries 1 --tag m72gate5` -> PASS (`PAYA` + `CREATE`). Head 193
wants **`edi` 27 where `price_of` says 18**, which explains M71's `m71pop2` FAIL. `test_m72_gate.py`
21/21. Details: NAMED.md's M72 block, SESSION_NOTES.md session 113.

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
3. `python3 scripts/m71_pop_watch.py [--base-name N] [--boundaries 2] [--poke-minerals N] [--tag m71pop]`
   — the POP instrument (4 hw watchpoints on the cursor field `0x6e93dc` + slots 1..3, 10 silent
   breakpoints on the pop/pay/create sites, drives real boundaries, reads the region back, 8 gates).
   Only needed to REPRODUCE M71; the gate question is M72's instrument.
3b. `python3 scripts/m72_gate_watch.py [--base-name NAME] [--boundaries 2] [--poke-minerals N]
   [--tag m72gate]` — the VISIT-GATE instrument: 12 conditional breakpoints (entry `0x4ef6d0`,
   head `0x4ef88e`, unit affordability `0x4efa5e`/bail `0x4efa63`, `0x4efe41`, pay `0x4efed8`,
   create `0x4eff4e`, facility path `0x4f0a3d`/`0x4f0a42`/`0x4f0b4f`/`0x4f0b86`/`0x4f0c28`,
   visit `0x4f5a93`), storage poked and READ BACK before attaching, drives real boundaries
   itself, detaches, 8 gates, one-line PASS/FAIL. **Its `edi` is the visit's requirement — not
   `price_of`** (193: 27 vs 18).
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

## WHAT M71/M72 SETTLED (NAMED.md blocks, sessions 111 + 113)

- **A completion pops EXACTLY ONE item when the new head validates as available**, and the shift
  writes `queue[k] = queue[k+1]` for k = 0..pending-1 ONLY (store `0x4ef62c`), so index k is
  written `pending-k` times and `queue[pending]` keeps a STALE id. The drain stops at the
  validator (`0x5a73f0`: type `+0x30` bit 0 clear OR owner-mask `+0x2c` lacks the bit -> 0).
  The completion writes the cursor field ZERO times.
- **The pay that fires is `0x4efed8` (`storage -= edi`)**, and `edi` is the VISIT'S OWN
  requirement, not `price_of`: **head 193 -> `edi` 27 while `price_of` says 18** (head 2 -> 9,
  where both agree). `edi = FUN_004e40a0(owner,1,-1) * FUN_005ac950(head,base,0)` (`0x4efa3c`,
  `0x4efa4d`, `imul 0x4efa52`); product MEASURED, factor split INFERRED.
- **The unaffordable turn-around is `0x4efa63`** (the `cmp [base+0x40],edi` at `0x4efa5e` on the
  unit path) -> message pair `0x67164c/0x671644` -> epilogue `0x4f0bfa`. Storage 18: `POSAFF` ->
  `BAILAFF`, nothing paid, queue untouched; storage 27: `POSAFF` -> `CMP40` -> `PAYA` -> `CREATE`.
- **The visitor runs 2-3x per two boundaries with identical operands** — repeated bail rows are
  ONE answer; two different bail KINDS in one window is the refusal case.
- **The facility (negative-head) path's three no-pay exits are ARMED BUT UNEXERCISED**:
  `0x4f0a42` (storage < edi), `0x4f0b86` (`-head <= 0`), `0x4f0c28` (another base already holds
  the head). A NEGATIVE head is needed to exercise them; no claim is made.

## STILL OPEN (in priority order)

1. **M73 pick — split `edi` = 27 for head 193.** Read `FUN_005ac950`'s `0x94d438`/`0x927a98`
   guards and `FUN_00595ad0` to say whether 27 is cost 3x9 or 1.5x18, and log `edi` for a SECOND
   designed id (194, `price_of` 27) to see whether it tracks cost or a derived value. Then exercise
   the facility path with a NEGATIVE head: the three exits `0x4f0a42`/`0x4f0b86`/`0x4f0c28` are
   armed in `m72_gate_watch.py` and have never fired.
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
   `test_m70_cursor` 23/23, `test_m71_pop` 34/34, **`test_m72_gate` 21/21**, `check_classes.py` exit 0.

## LIVE FACTS / KIT

- **Box at session-113 close:** round 60; University Base idx 0 (`0x95da10`) head 192, pending 0,
  storage 0 after M72's pay+create; unit 193 exists. RELOAD before any acceptance.
  Korolev Center does not exist in this instance (a fresh `m54g_prep`-style founding is needed).
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
  **To put head 193 on top** (M72's shape): enqueue the 193+192 pair, poke storage to 9 and read
  it back, then ONE boundary lets head 2 complete+pop -> head 193, pending 1, `[193,192,192,...]`.
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
