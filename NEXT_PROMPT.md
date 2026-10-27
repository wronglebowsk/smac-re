# NEXT_PROMPT.md — footing for the next session (session 110 close, 2026-10-27)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61** (#59),
**M62** (#60), **M62B** (#61), **M64** (#62), **M65** (#63), **M66** (#64), **M67** (#65),
**M69** (#66 — the enqueue writes `queue[cursor]`; the widget's cursor, not a sort).

**M70 (this branch's PR) — WHO WRITES THE CURSOR. ACCEPTANCE PASS on one real invocation**
(`m70_cursor_watch.py --arm` -> one `m66_insert_slot` flow -> `--stop` -> `--acceptance` -> PASS:
4 cursor writes, all attributed `0x40aae5` (row click) / `0x417e3b` x2 (enqueue tail) /
`0x4194b3` (zeroes it), values `[1,2,3,0]` all matching the static model). `test_m70_cursor.py`
23/23. Details: NAMED.md's M70 block, SESSION_NOTES.md session 110.

**M68 is NOT merged — its acceptance FAILED.** `milestone/m68` carries the 212-rule key
identifier, its gate, `m68_key_run.py`, `m68_typebytes.py`, `m68_cellprobe.py` and
`test_m68_key_rules.py` (35/35). At round 51 on the save's University Base the enqueue APPENDED
five items in click order; 55 of 212 rules predict an append, so no key was named. That CONFLICTS
with M67's three sorted read-backs and the difference is confounded (base, round, minerals, queue
occupancy, chooser size).

**M63 is NOT merged.** `milestone/m63` carries the pop instrument `scripts/m63_pop.py`, the
`0x94de84` queued-count correction (head unscaled), the 384/386 identity-crossing finding, the
validators-are-predicates finding and the `cur_base`-insufficiency proof, with **no PR**. Its
queued-count half is independently confirmed from the enqueue side by M66.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB of machine truth: verdict, both bases, the tagged
   CONFLICTs, the pick, the first commands. Exit 0 = READY. If it says BLOCKED, do the FIX it prints.
2. `python3 scripts/accept_ready.py` — the readiness oracle (17 unit cases:
   `scripts/test_accept_ready.py`). Screen, running gdb, evidence headroom, then per base
   `pending > 0`, `minerals < price`, `credit > 0`. **Re-read it immediately before you arm
   anything.** `--no-screen` skips the OCR for a memory-only read.
   *If the screen reads `dialog`*: press Return until it stops being a dialog
   (`scripts/m70_clear_dialog.py` does exactly that and prints each look); a BUILD/base PANE needs
   Escape, not Return — the script stops rather than spamming keys.
3. `python3 scripts/m70_cursor_watch.py --arm --base-name NAME` / `--stop` / `--acceptance` — the
   cursor instrument: hw watchpoint on `*(int *)0x6e93dc` (`0x6a9480+0x3ff5c`) + slots 1..3, 8
   breakpoints (`0x40aa22/0x40b02c/0x40b081/0x417dbf/0x417e04/0x417e3b/0x417e6b/0x417e7b`), log to
   `evidence/m70_cursor.gdblog`. `--acceptance` FAILs on any unmapped writer pc, on an
   enqueue-only shape, and on any logged value the model does not predict. Do the click flow
   between `--arm` and `--stop` with the proven UI scripts.
4. `python3 scripts/m66_insert_slot.py [--base-name NAME] [--item-a ID --item-b ID]
   [--rules layout|sort_key] [--slots 12] [--trace F]` — the INSERT instrument (two ids in one open
   chooser, chooser read WITH it open, queue + count arrays after every click, rules written down
   before the run, `shape_gate` refuses an all-agree shape, `--slots >= 10` forced for sort_key).
   Pinned by `test_m67_sort_keys.py` (15/15) and `test_m66_layouts.py` (10/10). NOTE: on the
   session-110 shape it scored `layout fit = []` (both inserts landed in click order) — that is "no
   layout claim", not a failure of the mechanism.
5. `python3 scripts/m69_enqueue_gdb.py --arm|--stop|--parse` — the enqueue tracer (breakpoints
   `0x417dbf/0x417e04` + the shift loop + the dead `0x418a99` dispatch, watch slots 1..3).
6. `python3 scripts/test_hud_bar.py` — 26 cases (18 frames + 8 look sequences). ~45 s quiet,
   **20+ min loaded**. `python3 scripts/m65_screen.py --samples 8 --save /tmp/m65` — the screen-read
   meter, READ-ONLY. Use both before believing an `unknown` or a changed read RATE.
7. `python3 scripts/m70_scan_writers.py` (every read/write of the cursor field, and every
   scale-0x34 type-byte read) and `python3 scripts/m70_type_sites.py` (the 52-byte type-address
   idiom and what each site does with the record) — static, over `scratch/m574/text.txt`.
8. `python3 scripts/evidence.py audit [--delete]` / `... budget` — check the budget BEFORE adding
   evidence (gate FAILs at 30 MB; **26.4 MB at this close**). `find evidence -name '*_3x.png'
   -delete` after any classifier test.
9. `python3 scripts/m56_build.py --fixture X` writes its trace to `$TMPDIR`, not `evidence/`;
   `m64_mkfixture.py` rebuilds the run-layer fixtures from committed traces.

## WHAT M70 SETTLED (NAMED.md M70 block, session 110)

- **Three writers of `[0x6a9480+0x3ff5c]` fired in one real flow**: `0x40aae5` (the queue-LIST row
  handler `FUN_0040a990`: `cursor = min(clicked_row, [[0x8f0d60]+0x4c] + 1)`) — **a row click sets
  the cursor**; `0x417e3b` (enqueue tail: `cursor = widget_rows + 1`); `0x4194b3` (after
  `push 0x4d00; call 0x584010`, **zeroes** the cursor — that is why a post-run cursor reads 0).
- **The clamp/advance uses the WIDGET's own row count `[[0x8f0d60]+0x4c]`, not the base's pending.**
  `DAT_008f0d60` is a POINTER to the base record (`0x40ad6c`/`0x40b00a`/`0x417d44` load it then index
  `+0x4c`, `+0x50+4k`); Ghidra flattens the deref.
- **A list row IS a queue slot** (`0x40b041-0x40b04c` indexes `[[0x8f0d60] + 4*row + 0x54]`) — there
  is no separate row array. And with slots 1..3 watched across the whole flow, **only the two enqueue
  stores (`pc=0x417e08`) wrote the region: a repaint does not rewrite the queue.**
- **The enqueue's arithmetic, pinned to the M69 log**: shift from `min(9, max(pending+1, cursor))`
  down to `cursor+1`; the store uses the ORIGINAL cursor (the `0x417ddb` clamp feeds only the `cmp`
  at `0x417e17`/`0x417df3`); `pending++` only when `pending < 9`; then `cursor = pending + 1`.
- **A gdb watchpoint reports the pc AFTER the store** (already noted in the M69 recipe): the run
  logged `0x40aaeb`/`0x417e41`/`0x4194bd` for stores at `0x40aae5`/`0x417e3b`/`0x4194b3`. Map pcs
  back to the 18-store table (`attribute_store`, 16-byte window) before naming a writer.

## STILL OPEN (in priority order)

1. **M71 pick — arm `m70_cursor_watch` across ONE POP (unit completion) and one round boundary.**
   The cursor field + slots 1..3 watchpoints will show whether the engine rewrites/reorders the
   region at completion (the M67-vs-M68 discriminator) and whether the `0x4194b3` handler fires
   there. `m63_pop.py` (on `milestone/m63`) names the pop/pay/create sites if you need them.
2. **Who calls the `0x4194b3` handler and what message `0x4d00` is** (it zeroes the cursor after a
   queue mutation; `0x584010` is the widget message sender, `0x4eb6b0` runs right after).
3. **The `-3 / -6` formula** — two points only, and the table stride is in CONFLICT:
   `0x984d38 + (-v)*48` (`0x40adae`, `0x4164f5`) vs `+(-v)*16` (`0x418914`, `0x41894d`).
4. **M67's plan-descending LIST order still has no code behind it**: zero sites read the plan byte
   `+42`; the only 52-byte type-address computations (`0x40ad92`, `0x4164dd`, `0x4188f9`, `0x418932`)
   hand the record to the row's string builder `FUN_00626634` / `FUN_006265a2`.
5. Open from 104/105: the `income 1` accrual case (every M64 PASS window had `gap_delta = 0`):
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`.
6. Keep green: `test_accept_ready` 17/17, `test_hud_bar` 26/26, `test_m56_predict` 19/19,
   `test_walk_diff` 37/37, `test_classify` 17/17, `test_m66_layouts` 10/10,
   `test_m67_sort_keys` 15/15, `test_m68_key_rules` 35/35, `test_m69_cursor` 15/15,
   `test_m70_cursor` 23/23, `check_classes.py` exit 0.

## LIVE FACTS / KIT

- **Box at session-110 close:** terran.exe alive, year 2151 round 51 `cur_player 3`; **University
  Base idx 0 pending 2** minerals 0 `+0xd0` 0, slots
  `[2, 193, 192, 0, 0, 0, 0, 0, 0, 0, 9225, 0]`, cursor field `0x6e93dc` = 0. Korolev Center does
  not exist in this instance (a fresh `m54g_prep`-style founding is needed for M67's Korolev state).
  **Free chooser ids are nearly gone: 195 -> -3, 196+ recordless -> negatives; reload before a shape
  that needs a fresh id.** The enqueue refuses `pending >= 9` (`0x418b05`, static) and both gdb
  instruments FAIL rather than arm when `pending + 2 > 9`. Live type records (stride 52, name at
  `+0`): 194 Impact Infantry cost 3/plan 1, 0 Colony Pod 3/8, 192 Impact Squad 2/0, 195 Impact
  Battery 2/0, 193 Synthmetal Garrison 2/2, 1 Formers 2/9, 2 Scout Patrol 1/3; ids 196+ read all-zero.
- **Reload recipe (used eight times, sessions 104-110, all clean):** `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` (BARE filename, ~35 s) -> `smac_play.py --turns 1
  --timeout 200 --no-escape 3000 --orders-per-turn 1 --verbose --tag t` -> `accept_ready.py` (its
  FIX will be "enqueue on University Base") -> `m57_ui_enqueue.py --base-index 0 --cell-item 2
  --inserts 1` -> the acceptance run. (`m60_guard.py --stage read` fails to resolve base names on
  this save; use `accept_ready.py`.)
- gdb: only **4 hardware watchpoints** and ~8 clean breakpoints. `m70_cursor_watch.py --arm` refuses
  if a gdb is running (`m57_credit.py --stop`, `m69_enqueue_gdb.py --stop`, or
  `m70_cursor_watch.py --stop` detach one), if `TracerPid != 0` or `ptrace_scope != 0`. No `si`
  inside a breakpoint command list; stdout must be DRAINED to a file; a printf newline in a
  generated gdb script is exactly TWO backslashes + `n`; for a plain `mov [reg+disp],src` the source
  operand IS the after value; `os.pread` on `/proc/<pid>/mem` EIOs — `seek`+`read`.
- `scratch/m574/text.txt` = whole `.text` objdump (40,900,318 B; addresses printed WITHOUT leading
  zeros, e.g. `40aae5:`, so grep `40aae5:` not `0040aae5:`); Ghidra pseudocode is `ghidra_out/
  shard_NNN.c` (`FUN_0040a990` = the queue-LIST row handler, shard_001.c:2080). Parse with Python,
  never read whole. `scratch/` is gitignored.
- **Evidence 26.4 MB of the 30 MB FAIL line** (54 images = 11.3 MB): an enqueue/cursor run ~3 KB.
  Prune with `evidence.py audit --delete`.

## TRAPS

- **OCR COST IS LOAD, NOT CODE.** With jellyfin/winedevice busy (load 13-15 on 4 cores) one
  `ocr_fast` pass took ~70 s and the classifier suites ran >20 min; the same suites took ~3 min
  quiet. Check `uptime` first; never claim a read RATE changed across loads.
- **A dialog/pane swallows every click and every turn-end key**, and the HUD status bar reads
  THROUGH it. Return clears a dialog's default row; a BUILD/base PANE needs Escape (Escape on the
  bare map raises the quit prompt — never click OK). `m57_ui_enqueue` on a just-founded base can
  read an EMPTY chooser; retry once. The base array compacts mid-run (18 -> 17 twice): locate bases
  **BY NAME**, pair windows by name AND owner byte, pair UNITS by `(x,y,type,owner)` counts.
- **The queue tail holds STALE ids and the shift PUSHES THEM ALONG instead of overwriting them** —
  and the shift only reaches `min(9, max(pending+1, cursor))`, so slots above that keep their stale
  values (M70). Unused slots read 0 on our bases; the queue sentinel is `0xffffffd9` = **-39**
  (`0x418b5f`, and `0x41949a` computes `0xffffffd9 - cursor`), not -38. Never read a queue by "first
  empty slot", never treat slot 10 (`+0x78`, 9225/545 here) as a queue entry, and never plan on a
  duplicate: **the engine itself refuses an id the queue already holds** — a duplicate is a no-op.
  Id 0 is both the Colony Pod and the empty marker.
- **A negative queue value belongs to the TYPE, not to a bad click**: 196 (recordless) -> -6,
  195 -> -3, both on guarded clicks. Never put 195/196+ in a shape.
- **The per-faction count arrays read one LOWER for every queued id mid-click** and settle by OK;
  and `0x94dc84 + 0x20bc*owner + (512 + tid)` is the SAME byte as `0x94de84 + 0x20bc*owner + tid`.
  Diff whole rows; do not sample two indices and assume two arrays.
- **An APPEND engine is consistent with ~55 rules.** Five appends in click order (M68) were
  "predicted" by 55 of 212 rules, so a FAIL there means "no key claim", not "the key is wrong" — and
  it does NOT overrule a live sorted read-back from another state: name the state, write
  "confounded", gdb it. M70 adds the mechanism: **consecutive INSERTs append by default**, because
  the enqueue parks the cursor at rows+1; only a row click moves it elsewhere.
- **The chooser cell -> pixel map is unreliable past row 0** (`(128+127*(cell%5), 60+100*(cell//5))`).
  Verify `guard == cell` AND the cell entry before clicking INSERT.
- **A PASS on a shape that cannot discriminate is not a PASS of the rule.** Compute candidate
  predictions from the BASELINE first and refuse the shape if they all agree. M70's version: an
  enqueue-only cursor trace proves nothing (the enqueue always moves its own cursor), so
  `m70_cursor_watch.py --acceptance` FAILs unless a NON-enqueue writer appears.
- The harness race is still real: a run that trips `rN boundary: player walk came home to us after
  the flip` makes the next window span two rounds. RE-RUN, do not edit the floor. Reload rather than
  poke into a UI-queued acceptance (a base that just produced has `+0xd0` zeroed and cannot accrue).
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm — and
  `DAT_008f0d60` is a POINTER to the base record, so `[DAT_008f0d60+0x4c]` means `[[0x8f0d60]]+0x4c`.
  Records are BYTES: a type record's name is at `+0` (34 bytes), a base record's name at `+19`.
- A background shell waiting on `pgrep -f <name>` matches its OWN command line and never exits.
- One variable at a time; if two things moved together write "confounded". Documents lose to
  instruction bytes only after a poke — until then REPORT the conflict. A read MODEL (how a read-back
  is interpreted) is not a hypothesis about the game: when the measured bytes contradict it, fix the
  model and say which shapes each version predicted.
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
