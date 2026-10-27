# NEXT_PROMPT.md — footing for the next session (session 108 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61** (#59),
**M62** (#60), **M62B** (#61), **M64** (#62), **M65** (#63), **M66** (#64), **M67** (#65 — the
queue's SORT KEY is the type-record PLAN byte `+42` descending, ties after; the COST byte `+41` is
refuted live; the INSERT shift is capped to the 10-slot queue array).

**M69 (this branch's PR) — the enqueue writes at the QUEUE WIDGET'S CURSOR, not at a sorted
slot; acceptance PASS on one real invocation** (`scripts/m69_cursor_run.py --cursor 2 --item 193`
-> `queue[2]=193`, plan rule says 1). M67's plan-descending order is the widget's LIST order, not
an INSERT comparison. M68's `-3` is a recordless TYPE stored as a negative (196 -> -6), not a bad
click. Details: NAMED.md's M69 block, SESSION_NOTES.md session 109.

**M68 is NOT merged — its acceptance FAILED.** `milestone/m68` carries the 212-rule key
identifier, its key-level gate, `m68_key_run.py`, the read-only `m68_typebytes.py`, the one-click
`m68_cellprobe.py` and `test_m68_key_rules.py` (35/35). At round 51 on the save's University Base
the enqueue **APPENDED** five items in click order (slots 1,2,3,4,5; the gate had certified only
`+42` predicted 1,1,3,4,3); 55 of 212 rules predict an append, so no key was named. That CONFLICTS
with M67's three sorted read-backs, and the difference is confounded (base, round, minerals, queue
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
   `pending > 0`, `minerals < price`, `credit > 0`; flags a TIGHT horizon. Its screen read re-freezes
   (4 looks) and prints a `SCREEN <class>:` line with WHY (M65). **Re-read it immediately before you
   arm anything** — indices and minerals go stale.
3. `python3 scripts/m66_insert_slot.py [--base-name NAME] [--item-a ID --item-b ID]
   [--rules layout|sort_key] [--slots 12] [--trace F]` — the INSERT instrument. It enqueues TWO
   different ids in one open chooser, re-reads the chooser's candidate array WITH the chooser open,
   reads the queue + both count arrays after every click, and scores the read-backs against rules
   written down before the run. `--rules layout` = the six M66 slot-layout rules (merged #64,
   unchanged). `--rules sort_key` = the eight M67 type-record-key rules (cost `+41` / plan `+42` x
   descending/ascending x ties after/before); it computes all eight predictions from the BASELINE
   before clicking and **refuses to run a shape where they all agree** (`shape_gate` row), and it
   forces `--slots >= 10` so the queue array's end is visible. PASS needs exactly ONE rule to fit
   plus the integrity checks. Pinned by `scripts/test_m67_sort_keys.py` (**15/15**) and
   `scripts/test_m66_layouts.py` (**10/10**).
4. `python3 scripts/test_hud_bar.py` — 26 cases (18 frames + 8 look sequences). ~45 s quiet,
   **20+ min loaded**. `python3 scripts/m65_screen.py --samples 8 --save /tmp/m65` — the screen-read
   meter, READ-ONLY (never clicks), records `load1`. Use both before believing an `unknown` or a
   changed read RATE.
5. `python3 scripts/m63_pop.py --base "Korolev Center" --boundaries 2 --tag m63pop` (on
   `milestone/m63`) — the pop tracer: `0x4ef5d0` and its shift/pending stores, the pay `0x4efedd`,
   the create `0x4eff4e`, an hw watch on `+0x50`. Poke and read back BEFORE attaching.
6. `python3 scripts/evidence.py audit [--delete]` / `... budget` — check the budget BEFORE adding
   evidence (gate FAILs at 30 MB; **26.3 MB at this close**). `audit --delete` removes only UNCITED
   files; `find evidence -name '*_3x.png' -delete` after any classifier test.
7. `python3 scripts/m56_build.py --fixture X` writes its trace to `$TMPDIR`, not `evidence/`;
   `m64_mkfixture.py` rebuilds the run-layer fixtures from committed traces.

## WHAT M67 SETTLED (re-scoped by M69: the SORT is in the WIDGET, not in the enqueue)

- **M67's live claim: INSERT sorts by the type-record PLAN byte `0x98ad88 + type*52 + 42`
  DESCENDING, ties after** — first region slot (`+0x50 + 4k`, `k = 1..pending`) whose plan is
  STRICTLY below the newcomer's, else at `k = pending + 1`. Not the cost byte `+41` (M66's confound
  note: its ids ordered the same by both). **Qualify it: M68 measured APPENDS in a different state
  (below) — the sort is not universal.**
- **The shift is capped to the 10-slot array `+0x50..+0x74`**: stale ids move along, slot 9 is
  pushed out, `+0x78` never moves. **Read 12 slots, not 8** — an 8-slot window with a zero tail
  makes a correct insert score as NO rule (two M67 runs failed that way).
- **Not separated from `+42`**: name bytes `+0,+1,+3,+4,+6,+15..+18`, `+37`, `+43` read ASCENDING
  rank the same ids identically. Refuted there: `+7, +9..+14, +33, +38, +41, +45, +48, +50, +51`.
- From M66: region is `+0x54..` = slots `1..pending` (`+0x4c`); head `+0x50` is never written by
  INSERT; per-faction QUEUED count is `0x94de84 + 0x20bc*owner + type`; the chooser's candidate
  array `DAT_009267e4` re-sorts between paints, so read cell -> id with the chooser OPEN.
- From M64/M65: the accrual phase (an arrival is attributed by the PAYMENT `0x4efedd` + read-back,
  never by `ds:0x8f0d60`); the screen read is a look loop, `unknown` is not a modal, the bottom
  status bar is the stable row; income is not constant.

## WHAT M69 SETTLED (NAMED.md M69 block, session 109)

- **The INSERT writes `queue[pos] = item`, `pos = *(int *)(0x6a9480 + 0x3ff5c)` — the queue
  widget's CURSOR ROW.** `0x417dbf` reads the field, `0x417dd3-0x417deb` shifts slots `pos..`,
  `0x417e04` stores, pending++ (cap 9). **No type-record byte is read on that path.**
- **So there is no sort in the enqueue.** ONE click flow wrote at slot 1 then slot 4
  (`evidence/m69_enqueue.gdblog`); M67's plan-descending order is the WIDGET's list order.
- **ACCEPTANCE PASS:** `m69_cursor_run.py --cursor 2 --item 193` -> wrote `queue[2]` where the
  plan rule says 1, and the instrument REFUSES a shape where cursor and plan index agree.
  `test_m69_cursor.py` -> 15/15.
- **A negative queue value belongs to the TYPE**, not to a bad click: 196 (recordless) -> -6,
  195 -> -3, both on clicks whose guard verified. Never put 195/196+ in a shape.
- The `0x418a99` dispatch (jump table `0x419c20`) is NOT the enqueue — it never fired.

## THE PICK — M70

One milestone, then stop. The instrument exists (`scripts/m69_enqueue_gdb.py --arm|--stop|--parse`):

1. **Watch `[0x6a9480+0x3ff5c]` across one INSERT and one repaint** — names the writer of the
   cursor and says whether the widget re-sorts its list on paint (the writers are
   `0x40b018-0x40b081`, `0x4163b6/0x41650e`, `0x417e3b-0x417e7b`).
2. **Read the queue-widget paint loop `0x40axxxx`** for the plan-byte comparison. That is where
   M67's order must live; NAMED.md's M67 row needs re-scoping to "the widget's list" when it is
   found, not left saying the INSERT sorts.
3. The `-3 / -6` formula for recordless types (two points only, do not guess).
4. Open from 104/105: the `income 1` accrual case (every M64 PASS window had `gap_delta = 0`):
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`.
5. Keep green: `test_accept_ready` 17/17, `test_hud_bar` 26/26, `test_m56_predict` 19/19,
   `test_walk_diff` 37/37, `test_classify` 17/17, `test_m66_layouts` 10/10,
   `test_m67_sort_keys` 15/15, `test_m68_key_rules` 35/35, `test_m69_cursor` 15/15,
   `check_classes.py` exit 0.

## LIVE FACTS / KIT

- **Box at session-109 close:** terran.exe alive, year 2151 round 51 `cur_player 3`; **University
  Base idx 0 pending 3** (minerals 0, `+0xd0` 0, slot 10 9225) slots
  `[2, 192, 193, 194, 0, 0, 0, 0, 0, 0, 9225, 0]` — the M69 run's write. Korolev Center does not
  exist in this instance, so M67's Korolev state needs a fresh `m54g_prep`-style founding.
  **Free chooser ids are nearly gone: 195 -> -3, 196+ recordless -> negatives; reload before a
  shape that needs a fresh id.** The enqueue refuses
  `pending >= 9` (`0x418b05`, static) and the instrument FAILs rather than arming when
  `pending + 2 > 9`. Live type records (stride 52, name at `+0`): 194 Impact Infantry cost 3/plan 1,
  0 Colony Pod 3/8, 192 Impact Squad 2/0, 195 Impact Battery 2/0, 193 Synthmetal Garrison 2/2,
  1 Formers 2/9, 2 Scout Patrol 1/3; ids 196+ read all-zero.
- **Reload recipe (used seven times, sessions 104-108, all clean):** `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` (BARE filename) -> `smac_play.py --turns 1 --timeout 200
  --no-escape 3000 --orders-per-turn 1 --verbose --tag t` -> `accept_ready.py` -> the acceptance
  run. (`m60_guard.py --stage read` after a reload fails to resolve base names on this save; use
  `accept_ready.py` to locate University Base and read the record offsets directly.)
- `m60_guard.py --stage read|poke --value N|watch --boundaries K --timeout T --tag t` (refuses if a
  gdb is running — `m57_credit.py --stop` detaches one), `m59_head.py [--stage read|poke --base
  NAME --minerals N] [--hold]`, `m58_price.py [--owner 3] [--type 2]`, `m57_stores.py --base NAME
  --boundaries 3 --timeout 220 --tag t`. On a CREATE line `owner=` is `$eax` (the owner byte).
- `scratch/m574/text.txt` = whole `.text` objdump (40,900,318 B; `objdump -d -M intel
  --section=.text programs/terran.exe > scratch/m574/text.txt`); Ghidra pseudocode is `ghidra_out/
  shard_NNN.c` (`FUN_00417ee0` = the UI dispatch, shard_001.c:8941, size 7459; `FUN_004f6030`
  shard_012.c 24338-29064) — parse with Python, never read whole. `scratch/` is gitignored.
- **Evidence 28.1 MB of the 30 MB FAIL line** (68 images = 13.1 MB): `m56_build` ~0.65 MB,
  `m63_pop`/watch ~0.05 MB, an enqueue run ~4 KB. Prune with `evidence.py audit --delete`.

## TRAPS

- **OCR COST IS LOAD, NOT CODE.** With jellyfin/winedevice busy (load 13-15 on 4 cores) one
  `ocr_fast` pass took ~70 s and the classifier suites ran >20 min; the same suites took ~3 min
  when the box quieted. Check `uptime`/`top` first; never claim a read RATE changed across loads.
- **A dialog/pane swallows every click and every turn-end key**, and the HUD status bar reads
  THROUGH it — the modal detectors save you, not the bar. Return clears a dialog's default row;
  Escape closes a PANE (Escape on the bare map raises the quit prompt — never click OK).
  `m57_ui_enqueue` on a just-founded base can read an EMPTY chooser; retry once. The base array
  compacts mid-run (18 -> 17 twice): locate bases BY NAME, pair windows by name AND owner byte,
  pair UNITS by `(x,y,type,owner)` counts.
- **The queue tail holds STALE ids and the shift PUSHES THEM ALONG instead of overwriting them**
  (M67: Korolev's stale 2 went slot 3 -> 4 -> 5 across two inserts). Unused slots read 0 on
  our bases; the queue sentinel is `0xffffffd9` = **-39** (`0x418b5f`), not -38. Never read a queue
  by "first empty slot", never treat slot 10 (`+0x78`, 9225/545 here) as a queue entry, and never
  plan on a duplicate: **the engine itself refuses an id the queue already holds** (M68: pending and
  every slot unchanged) — a duplicate is a no-op, not merely unidentifiable. Id 0 is both the Colony
  Pod and the empty marker.
- **The per-faction count arrays read one LOWER for every queued id mid-click** and settle by OK;
  and `0x94dc84 + 0x20bc*owner + (512 + tid)` is the SAME byte as `0x94de84 + 0x20bc*owner + tid`
  (`0x94de84 - 0x94dc84 = 0x200`) — diff whole rows, do not sample two indices and assume they are
  different arrays.
- **An APPEND engine is consistent with ~55 rules.** Five appends in click order (M68) were
  "predicted" by 55 of 212 rules (every byte constant over those ids, plus monotone ones), so a
  FAIL there means "no key claim", not "the key is wrong" — and it does NOT overrule a live sorted
  read-back from another state: name the state, write "confounded", gdb it.
- **The chooser cell -> pixel map is unreliable past row 0** (`(128+127*(cell%5), 60+100*(cell//5))`):
  cells 6 and 4 failed to register in three probes (guard stayed on the previous selection, INSERT
  did nothing) and the one registering cell-6 click made the queue store **-3 (0xfffffffd)**. Verify
  `guard == cell` AND the cell entry before clicking INSERT; treat a write of -3 as a bad click,
  not a game rule, until a gdb run says otherwise.
- **A PASS on a shape that cannot discriminate is not a PASS of the rule.** M66 proved this with an
  empty region; M67 proves it with cost-vs-plan: the same arrays can be explained by two rules that
  happen to co-order. Compute the candidate predictions from the BASELINE first and refuse the
  shape if they all agree (`shape_gate`).
- The harness race is still real: a run that trips `rN boundary: player walk came home to us after
  the flip` makes the next window span two rounds. RE-RUN, do not edit the floor. Reload rather
  than poke into a UI-queued acceptance (a base that just produced has `+0xd0` zeroed and cannot
  accrue).
- gdb: no `si` inside a breakpoint command list; stdout must be DRAINED to a file; **a printf
  newline in a generated gdb script is exactly TWO backslashes + `n`**; for a plain
  `mov [reg+disp],src` the source operand IS the after value; `os.pread` on `/proc/<pid>/mem` EIOs
  — `seek`+`read`; only 4 hardware watchpoints exist. Popup BARS ignore clicks (Return works on the
  default row); MENU click (75,369); TURN COMPLETE (650,410).
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm. Records
  are BYTES: a type record's name is at `+0` (34 bytes) and a base record's name is at `+19`, so a
  dword can straddle it.
- A background shell waiting on `pgrep -f <name>` matches its OWN command line and never exits —
  wait on a PID or chain the job.
- One variable at a time; if two things moved together write "confounded". Documents lose to
  instruction bytes only after a poke — until then REPORT the conflict. A read MODEL (how a
  read-back is interpreted) is not a hypothesis about the game: when the measured bytes contradict
  it, fix the model and say which shapes each version predicted.
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
