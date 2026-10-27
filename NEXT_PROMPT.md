# NEXT_PROMPT.md — footing for the next session (session 107 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61** (#59),
**M62** (#60), **M62B** (#61), **M64** (#62), **M65** (#63), **M66** (#64), **M67** (#65 — the
queue's SORT KEY is the type-record PLAN byte `+42` descending, ties after; the COST byte `+41` is
refuted live; the INSERT shift is capped to the 10-slot queue array).

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

## WHAT M67 SETTLED (detail lives in the skill: references/production-queue.md)

- **INSERT sorts by the type-record PLAN byte `0x98ad88 + type*52 + 42` DESCENDING, ties after.**
  The item goes at the first region slot (`base+0x50 + 4k`, `k = 1 .. pending`) whose plan byte is
  STRICTLY below its own, else after the region at `k = pending + 1`; equal-plan entries stay ahead.
  **It is not the cost byte `+41`** — M66 said cost because every id it had measured orders the same
  way by both bytes (its own confound note). Live: 193 (plan 2, cost 2) went to region slot 1 IN
  FRONT of two 194s (plan 1, cost 3) on University Base (`evidence/m67_sort_key.jsonl:6`), and to
  slot 2 in front of 194 on Korolev Center while `cost_desc_after` predicted 5
  (`evidence/m67_sort_key_accept.jsonl:6`). Three runs, three shapes, one rule fits each.
- **The INSERT shift is capped to the 10-slot queue array `+0x50 .. +0x74`** (head + 9 region
  slots, the same 9 the enqueue cap at `0x418b05` refuses to exceed). Stale ids inside the array
  are pushed ALONG with the shift, the value in slot 9 is pushed out, and the dword at `+0x78`
  (queue slot 10 — 9225 on University, 545 on Korolev) never moved in seven writes
  (`evidence/m67_sort_key_korolev.jsonl:6-7`). **Read 12 slots, not 8**: with an 8-slot window and
  a zero tail the capped and uncapped shifts are indistinguishable, and the uncapped model makes a
  correct insert score as NO rule at all (that is how two of this session's runs failed).
- **Scope of the claim:** cost vs plan, decided. NOT separated from `+42`: the type-record bytes
  that happen to rank ids 192/193/194/195/2 identically — several name bytes
  (`+0,+1,+3,+4,+6,+15..+18`), `+37`, and `+43` read ASCENDING. Refuted: `+7, +9..+14, +33, +38,
  +41, +45, +48, +50, +51`.
- Still true from M66: the queue REGION is `+0x54 ..` = slots `1 .. pending` (`+0x4c`); the head
  slot `+0x50` is not a queued entry and INSERT never writes it (it read 2 in all seven enqueues);
  the per-faction QUEUED count is `0x94de84 + 0x20bc*owner + type` (enqueue +1 read after OK, pop
  -1); the chooser's candidate array `DAT_009267e4` re-sorts between paints, so cell -> id must be
  read WITH the chooser open (the stored id equals the entry at the clicked cell at click time).
- Still true from M64/M65: the accrual phase (`accrual_phase()`, an arrival is attributed by the
  PAYMENT `0x4efedd` + a read-back, never by `ds:0x8f0d60`); the screen read is a look loop and
  `unknown` is not a modal (the HUD's bottom status bar is the stable row); income is not constant;
  the round order and the `+0x10`-is-not-a-field rule from M61/M62.

## THE PICK — M68

One milestone, then stop. Cheapest first, and none of them is a threshold change:

1. **Separate plan from name-order.** One enqueue of id 1 `Formers` (plan 9, name starts `F`) into
   a queue holding 194 `Impact Infantry` (plan 1, name starts `I`): plan-descending says IN FRONT,
   name-descending says BEHIND, and the same run re-tests the tie direction. Both bases are near
   the cap (see LIVE FACTS) — reload first, or use a base with room.
2. **Who writes the head slot `+0x50`, and what is the `esi == 0` head store `0x418b57` for?** It
   never fired in seven enqueues; the pop consumes the head, so something refreshes it. An hw watch
   on `+0x50` across one boundary is the cheap shape (`milestone/m63` already has the pop
   instrument).
3. The `income 1` live accrual case still open from 104/105: every M64 PASS window had
   `gap_delta = 0` (the fix was INERT live). Needs an `income 1` base whose windows straddle the
   add: `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`, and report the `accrual_phase` rows.
4. Cheap side-quests: re-measure `scripts/m65_screen.py` at a quiet AND a loaded load (it records
   `load1`; session 105's flake-vs-load measurement was confounded); settle `check_classes.py`,
   which names three frames deleted back in #3 (it reports 14 PASS + 3 SKIP).
5. Keep green: `test_accept_ready.py` (17/17), `test_hud_bar.py` (26/26), `test_m56_predict.py`
   (19/19), `test_walk_diff.py` (37/37), `test_classify.py` (17/17), `test_m66_layouts.py` (10/10),
   `test_m67_sort_keys.py` (15/15), `check_classes.py` (exit 0), `m56_build.py --fixture` bad=1,
   `scratch/m61/fixture_defer_ok.json`=0, `scratch/m61/fixture_beat_visit.json`=1,
   `scratch/m64/fixture_paid_readback.json`=0, `scratch/m64/fixture_paid_no_readback.json`=1.

## LIVE FACTS / KIT

- **Box at session-107 close:** terran.exe alive, year 2161 round 61 `cur_player 3`; **University
  Base idx 0 pending 8** (minerals 1, `+0xd0` 0 — UI-queued, its income add is gated `d0 > 0` so
  storage cannot accrue), slots `[2, 193, 194, 194, 193, 195, 192, 1, 192, 0, 9225, 0]`;
  **Korolev Center idx 17 pending 6** (minerals 3, income 2, `+0xd0` 2), slots
  `[2, 193, 193, 194, 195, 192, 192, 2, 0, 0, 545, 0]`. **Both queues are near the cap**: the
  enqueue refuses `pending >= 9` (`0x418b05`, static), and the instrument FAILs rather than
  arming when `pending + 2 > 9`. So an enqueue milestone now needs a reload, or a base with room.
  Live type records (stride 52, name at `+0`): 194 Impact Infantry cost 3/plan 1, 0 Colony Pod 3/8,
  192 Impact Squad 2/0, 195 Impact Battery 2/0, 193 Synthmetal Garrison 2/2, 1 Formers 2/9,
  2 Scout Patrol 1/3; ids 196+ read all-zero (cost 0, plan 0, name empty).
- **Reload recipe (used six times across sessions 104-107, all clean):** `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` (BARE filename; difficulty talent) -> `m54g_prep.py` ->
  `smac_play.py --turns 1 --timeout 200 --no-escape 3000 --orders-per-turn 1 --verbose --tag t` ->
  `m60_guard.py --stage read` (bases BY NAME, fresh indices) -> an enqueue (`m57_ui_enqueue.py` or
  `m66_insert_slot.py`) -> `accept_ready.py` -> the acceptance run WITH `--no-poke-hold`.
- `python3 scripts/m60_guard.py --stage read|poke --value N|watch --boundaries K --timeout T --tag t`
  (refuses if a gdb is running — `m57_credit.py --stop` detaches one), `m59_head.py [--stage
  read|poke --base NAME --minerals N] [--hold]`, `m58_price.py [--owner 3] [--type 2]`,
  `m57_stores.py --base NAME --boundaries 3 --timeout 220 --tag t`. On a CREATE line `owner=` is
  `$eax` = the base OWNER byte; `guard=` reads the global.
- `scratch/m574/text.txt` = whole `.text` objdump (40,900,318 B; `objdump -d -M intel
  --section=.text programs/terran.exe > scratch/m574/text.txt`); Ghidra pseudocode is `ghidra_out/
  shard_NNN.c` (`FUN_00417ee0` = the UI dispatch, shard_001.c:8941, size 7459; `FUN_004f6030`
  shard_012.c 24338-29064) — parse with Python, never read whole. `scratch/` is gitignored.
- **Evidence 26.3 MB of the 30 MB gate FAIL line** (warn band 20). A full `m56_build` run ~0.65 MB,
  an `m63_pop` or `--stage watch` run ~0.05 MB, an `m66_insert_slot` run ~4 KB.

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
  (M67: Korolev's stale 2 went slot 3 -> 4 -> 5 across two inserts). Unused slots read 0 (not -38)
  on our bases. Never read a queue by "first empty slot", never enqueue an id the queue already
  holds twice (the written slot becomes unidentifiable), and never treat queue slot 10 (`+0x78`,
  9225/545 here) as a queue entry — it is a different field that never moves. Id 0 is both the
  Colony Pod and the empty marker.
- **The per-faction count arrays read one LOWER for every queued id mid-click** and settle by OK;
  and `0x94dc84 + 0x20bc*owner + (512 + tid)` is the SAME byte as `0x94de84 + 0x20bc*owner + tid`
  (`0x94de84 - 0x94dc84 = 0x200`) — diff whole rows, do not sample two indices and assume they are
  different arrays.
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
