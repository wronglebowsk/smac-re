# NEXT_PROMPT.md — footing for the next session (session 106 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56), **M57+M58+M59** (#57), **M60** (#58), **M61** (#59),
**M62** (#60), **M62B** (#61), **M64** (#62), **M65** (#63), **M66** (#64 — the BUILD UI's INSERT
inserts by DESCENDING COST; the head slot `+0x50` is not a queued entry; the queued-count byte is
`0x94de84`, settled from the enqueue side).

**M63 is NOT merged.** `milestone/m63` carries the pop instrument `scripts/m63_pop.py`, the
`0x94de84` queued-count correction (head unscaled), the 384/386 identity-crossing finding, the
validators-are-predicates finding and the `cur_base`-insufficiency proof, with **no PR**. Its
queued-count half is now independently confirmed from the enqueue side by M66.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB of machine truth: verdict, both bases, the tagged
   CONFLICTs, the pick, the first commands. Exit 0 = READY. If it says BLOCKED, do the FIX it prints.
2. `python3 scripts/accept_ready.py` — the readiness oracle (**17** unit cases:
   `scripts/test_accept_ready.py`). Screen, running gdb, evidence headroom, then per base
   `pending > 0`, `minerals < price`, `credit > 0`; flags a TIGHT horizon. Its screen read re-freezes
   (4 looks) and prints a `SCREEN <class>:` line with WHY (M65). **Re-read it immediately before you
   arm anything** — indices and minerals go stale.
3. `python3 scripts/m66_insert_slot.py [--base-name NAME] [--item-a ID --item-b ID] [--trace F]` —
   the INSERT instrument: enqueues TWO different ids in one open chooser, re-reads the chooser's
   candidate array WITH the chooser open, reads the queue + both count arrays after every click, and
   scores the read-backs against SIX layouts written down before the run (each a transformation rule
   with the stored id as a free variable). PASS needs exactly ONE rule to fit plus the integrity
   checks. `python3 scripts/test_m66_layouts.py` pins the scorer (**10/10**).
4. `python3 scripts/test_hud_bar.py` — **26 cases** (18 frames + 8 look sequences). ~45 s quiet,
   **20+ min loaded**. `python3 scripts/m65_screen.py --samples 8 --save /tmp/m65` — the screen-read
   meter, READ-ONLY (never clicks), records `load1`. Use both before believing an `unknown` or a
   changed read RATE.
5. `python3 scripts/m63_pop.py --base "Korolev Center" --boundaries 2 --tag m63pop` (on
   `milestone/m63`) — the pop tracer: `0x4ef5d0` and its shift/pending stores, the pay `0x4efedd`,
   the create `0x4eff4e`, an hw watch on `+0x50`. Poke and read back BEFORE attaching.
6. `python3 scripts/evidence.py audit [--delete]` / `... budget` — check the budget BEFORE adding
   evidence (gate FAILs at 30 MB; **26.4 MB at this close**). `audit --delete` removes only UNCITED
   files; `find evidence -name '*_3x.png' -delete` after any classifier test.
7. `python3 scripts/m56_build.py --fixture X` writes its trace to `$TMPDIR`, not `evidence/`;
   `m64_mkfixture.py` rebuilds the run-layer fixtures from committed traces.

## WHAT M66 SETTLED (detail lives in the skill: references/production-queue.md)

- **INSERT does not write a slot index — it inserts by cost.** The queue REGION is
  `base+0x54 ..` = slots `1 .. pending` (`+0x4c`); the new item goes at the first region slot whose
  type-record cost byte (`0x98ad88 + type*52 + 41`, the byte `m58_price.py` prices from) is strictly
  BELOW its own cost, else at `pending + 1`; everything from there shifts right by one; entries
  already at the same cost stay ahead. **The head slot `+0x50` is never written by INSERT** — it read
  2 before and after in all four enqueues. The M57 doc line "INSERT writes head `+0x50`, pending
  `+0x4c`, slot `+0x54`" was a duplicate-value artifact (id 2 enqueued behind a head that was
  already 2). `evidence/m66_insert_slot_cost_order.jsonl:6-7` (cost 3 landed at index 2 of a queue
  holding a 3 and three 2s; cost 2 landed at index 6, after the 2-run),
  `evidence/m66_insert_slot_third_fourth.jsonl:6` (cost 3 landed at index 1 while pending was 2 —
  the row that refutes "writes `4*pending`"), costs in `evidence/m66_insert_slot_cost_order.jsonl:5`.
- **The queued-count byte is `0x94de84 + 0x20bc*owner + type_id`**: the UI enqueue adds 1 per item of
  that type (settled state, read after OK) and the pop subtracts 1 (M63's branch). The sibling
  `0x94dc84` (512 B lower) was untouched at its own indexing (`evidence/m66_insert_slot_cost_order.jsonl:10`,
  `evidence/m66_insert_slot_run1_korolev.jsonl:8`). The NAMED CONFLICT line is deleted; what `0x94dc84`
  IS remains open (it is incremented at `0x4d2a25`/`0x4d2fa7`).
- **A PASS on a shape that cannot discriminate is not a PASS of the rule.** With an EMPTY region,
  "insert at the new pending index" and "insert by descending cost" predict the same array: the
  session's second run passed on the first rule and the third run refuted it. Pin the discriminating
  shape (`scripts/test_m66_layouts.py` names the two-match shapes explicitly) and build the
  acceptance run so its region is POPULATED with unequal costs.
- **The chooser's candidate array re-sorts between reads** (`0x596000` rebuilds all 128 entries per
  paint): the same box read `[192,194,193,2,0,1,195,...]` before the chooser opened and
  `[192,195,194,193,2,0,1]` with it open. Resolve cell -> id with the chooser OPEN; the id the game
  stores equals the entry at the clicked cell read at click time (no +1).
- Still true from M64/M65: the accrual phase (`accrual_phase()`, an arrival is attributed by the
  PAYMENT `0x4efedd` + a read-back, never by `ds:0x8f0d60`); the screen read is a look loop and
  `unknown` is not a modal (the HUD's bottom status bar is the stable row); income is not constant;
  the round order and the `+0x10`-is-not-a-field rule from M61/M62.

## THE PICK — M67

One milestone, then stop. Cheapest first, and none of them is a threshold change:

1. **Separate the sort key.** Cost (`+41`) and plan (`+42`) happen to order the ids measured so far
   the same way, and the tie direction was only established by the equal-cost cases. One enqueue pair
   with EQUAL cost and DIFFERENT plan into a queue that already holds one of them (e.g. 192 vs 193,
   both cost 2, plan 0 vs 2) decides cost-vs-plan and the tie direction in one run.
2. **Who writes the head slot `+0x50`, and what is the `esi == 0` head store `0x418b57` for?** It
   never fired in four enqueues; the pop consumes the head, so something refreshes it. An hw watch on
   `+0x50` across one boundary is the cheap shape (`milestone/m63` already has the pop instrument).
3. The `income 1` live accrual case still open from session 104/105: every M64 PASS window had
   `gap_delta = 0` (the fix was INERT live). Needs an `income 1` base whose windows straddle the add:
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`, and report the `accrual_phase` rows.
4. Cheap side-quests: re-measure `scripts/m65_screen.py` at a quiet AND a loaded load (it records
   `load1` now; session 105's flake-vs-load measurement was confounded); settle `check_classes.py`,
   whose DEFAULT names three frames deleted back in #3 (it reports 14 PASS + 3 SKIP).
5. Keep green: `test_accept_ready.py` (17/17), `test_hud_bar.py` (26/26), `test_m56_predict.py`
   (19/19), `test_walk_diff.py` (37/37), `test_classify.py` (17/17), `test_m66_layouts.py` (10/10),
   `check_classes.py` (exit 0), `m56_build.py --fixture` bad=1, `scratch/m61/fixture_defer_ok.json`=0,
   `scratch/m61/fixture_beat_visit.json`=1, `scratch/m64/fixture_paid_readback.json`=0,
   `scratch/m64/fixture_paid_no_readback.json`=1.

## LIVE FACTS / KIT

- **Box at session-106 close:** terran.exe alive, year 2161 round 61 `cur_player 3`; **University
  Base idx 0 pending 6, slots `[2, 194, 194, 193, 195, 192, 1, 0]`, minerals 1, `+0xd0` 0** (it is
  UI-queued but its income add is gated `d0 > 0`, so storage cannot accrue); **Korolev Center idx 17
  pending 2, slots `[2, 194, 195, 2, 0, ...]`, minerals 3, income 2** — reaches its gate in ~3 rounds,
  so `accept_ready.py` prints `RUN: scripts/m56_build.py --ui-queued 17 ...`. Listed buildable ids
  and their cost(+41)/plan(+42) bytes: 194 Impact Infantry 3/1, 0 Colony Pod 3/8, 192 Impact Squad
  2/0, 195 Impact Battery 2/0, 193 Synthmetal Garrison 2/2, 1 Formers 2/9, 2 Scout Patrol 1/3; ids
  196+ in the array are empty records (cost 0).
- **Reload recipe (used five times across sessions 104-106, all clean):** `SMAC_SAVE='m54b_clean.SAV'
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
- **Evidence 26.4 MB of the 30 MB gate FAIL line** (warn band 20). A full `m56_build` run ~0.65 MB,
  an `m63_pop` or `--stage watch` run ~0.05 MB, an `m66_insert_slot` run ~4 KB.

## TRAPS

- **OCR COST IS LOAD, NOT CODE.** With jellyfin/winedevice busy (load 13-15 on 4 cores) one
  `ocr_fast` pass took ~70 s and the classifier suites ran >20 min; the same suites took ~3 min when
  the box quieted. Check `uptime`/`top` first; never claim a read RATE changed across loads.
- **A dialog/pane swallows every click and every turn-end key**, and the HUD status bar reads THROUGH
  it — the modal detectors save you, not the bar. Return clears a dialog's default row; Escape closes
  a PANE (Escape on the bare map raises the quit prompt — never click OK). `m57_ui_enqueue` on a
  just-founded base can read an EMPTY chooser; retry once. The base array compacts mid-run (18 -> 17
  twice): locate bases BY NAME, pair windows by name AND owner byte, pair UNITS by `(x,y,type,owner)`
  counts.
- **The queue tail holds STALE ids the pop left behind** and unused slots read 0 (not -38) on our
  bases: never read a queue by "first empty slot", and never enqueue an id the queue already holds
  twice — the written slot becomes unidentifiable (`scripts/test_m66_layouts.py` pins that shape).
  Id 0 is both the Colony Pod and the empty marker.
- **The per-faction count arrays read one LOWER for every queued id mid-click** and settle by OK;
  and `0x94dc84 + 0x20bc*owner + (512 + tid)` is the SAME byte as `0x94de84 + 0x20bc*owner + tid`
  (`0x94de84 - 0x94dc84 = 0x200`) — diff whole rows, do not sample two indices and assume they are
  different arrays.
- The harness race is still real: a run that trips `rN boundary: player walk came home to us after
  the flip` makes the next window span two rounds. RE-RUN, do not edit the floor. Reload rather than
  poke into a UI-queued acceptance (a base that just produced has `+0xd0` zeroed and cannot accrue).
- gdb: no `si` inside a breakpoint command list; stdout must be DRAINED to a file; **a printf newline
  in a generated gdb script is exactly TWO backslashes + `n`**; for a plain `mov [reg+disp],src` the
  source operand IS the after value; `os.pread` on `/proc/<pid>/mem` EIOs — `seek`+`read`; only 4
  hardware watchpoints exist. Popup BARS ignore clicks (Return works on the default row); MENU click
  (75,369); TURN COMPLETE (650,410).
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
