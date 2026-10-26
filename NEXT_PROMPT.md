# NEXT_PROMPT.md — footing for the next session (session 98 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53),
**M54k2** (#54), **M55** (#55), **M56** (#56). Session 98 **PASSED M59**
(`python3 scripts/m56_build.py --ui-queued 17 --boundaries 10 --timeout 400 --no-poke-hold`
-> `PASS production prediction: 1 verified unit arrivals over 10 boundaries ... 0 memory writes`,
50 ok checks / 0 BAD, trace `evidence/trace_m56_build_20261026_145157.jsonl`), so **M57 + M58 +
M59 merge together** on `milestone/m59` (that branch carries M57's 13 commits and all of M58,
which session 97 left unmerged because its acceptance never printed PASS — M57's acceptance
command is the same `--ui-queued` mode, and it has now printed PASS). The submit is ONE PR
covering all three; say so in the report.

## WHAT SESSION 98 SETTLED (do not re-learn)

**PENDING IS NOT THE QUEUE TRUTH — the HEAD SLOT is.** In the per-base visit `FUN_004ef6d0`
(12 KB, called from `FUN_004f5a70@0x4f5adc`): income add `0x4ef7f6` → price gate
`0x4efa2c-0x4efa61` (`ebx = [base+0x50]` = HEAD SLOT; `edi = 0x4e40a0(owner,1,-1) ×
0x5ac950(ebx, base, 0)`; `cmp [ecx+0x40], edi; jge 0x4efadc`) → pay `0x4efedd` (`esi = [ecx+0x40];
esi -= edi; [ecx+0x40] = esi`) → clamp `0x4eff02-0x4eff23` → **create-unit `0x5ab650(type, ?, x, y)`
@ `0x4eff4e`**, guarded at `0x4eff32` by `[base+0x10] == 0`. Block-level CFG (`scratch/m59/dom.py`):
with the pay block removed, `0x4eff4e` is unreachable from the entry AND from the gate — **the pay
DOMINATES the create**, and nothing between them reads `+0x4c`. The pop `FUN_004ef5d0` returns at
`0x4ef5f4` when pending == 0, is called later (`0x4f037b`, `0x4f0f46`; `0x4ef992` is NOT reachable
from the pay) and only left-shifts `+0x50..` and decrements pending (`0x4ef642`) plus the
per-faction queued-count byte `[0x94de84 + owner*0x20bc + type*4]` (`0x4ef613 dec BYTE PTR [ecx]`).

**Measured one-variable with an internal control** (`scripts/m59_head.py`): Korolev Center pending
0 head 2, minerals poked `0 -> 9` (read back), all our units held, University Base untouched at 0
→ one turn later Korolev minerals `9 -> 0` (= the derived price 9), income `0 -> -1` (the new
unit's upkeep), **pending 0 -> 0**, head 2 -> 2, tile 5 → 6 units of (type 2, ours); control base
unchanged. **A base with an EMPTY queue re-buys the head's type every round it can pay.**

**NAMED.** `0x5a73f0(type, owner, base)` = buildable-here: needs type-record `[+0x30] & 1`, owner
NOT in the exclusion dword `[+0x2c]`, required facility/project `[+0x32]` == -1 or
researched-and-owned; `type >= 0x40` is faction-specific (`(type>>6) == owner`); also rejects
plan `[+42] == 8` when `0x985ac4 & 0x400000` and rejects when class byte `[+0x24]` indexes
`[0x92ae81] == 1` while `0x4e4620(x, y, 0) == 0`. `0x5a6e70(-id, owner, base, 0)` = the same for
a facility/project item (the queue keeps those NEGATIVE). `FUN_004e47d0` (from `0x4ccbdd`,
`0x59d894`, `0x5a01f8`) initialises a base: zeroes `+0x30 +0x34 +0x3c +0x40 +0x4c`, sets `+0x38`
from `[faction+0x94d600]`, then `FUN_004e46f0(base)` scores every buildable type
(`[+38]<<4` → table `0x92fd18`, ×32, ×4/×3/×2 by `[+43]`, `+ ([+40]*0x90 → [0x92ae81])`, `>>2`,
minus the `+41` cost) and writes the winner to the HEAD SLOT ONLY. `FUN_004e5560(base, new_head)`
writes the head + adjusts the queued-count byte (`dec` old `0x4e55b5`, `inc` new `0x4e55dd`).
`FUN_004e5ae0(base, 0)` — called SIX times from the visit, first at **`0x4ef87e`, BEFORE the gate**
— refreshes the head via chooser `0x4f6030` for owners outside `0x985b10`, or when `+0x38` sign is
clear, or whenever param_2 == 0 (which is the case at `0x4ef87e`: `push 0; push base`). Pending is
written at only four absolute sites: `0x4e4982`, `0x4ef642`, `0x50890d`, `0x543b26`.

**The rule** (`predict()`): OUR bases only (`0x91b5b4`; other owners' heads are re-picked by their
own visit at `0x4ef87e` before their gate — enemy arrivals stay REPORTED, never floored) ∧ head is
a unit type (0..0x3f) ∧ owner in `0x985b10` ∧ `storage (+ income) >= price`, price =
`0x4e40a0(owner,1,-1) × type_record[+41]` (M58: `[0x92ada8] == 1` → factor 9 in this box; the LOAD
pane says `difficulty level: talent`). `pop_expected = arrive and pending > 0`.

**Two timing facts the harness now encodes (both MEASURED, neither a loosened threshold).**
(a) Bookkeeping pairs bases BY NAME — the array compacted Korolev 18 → 17 mid-run again.
(b) A paid window can show no unit: `..._144801` r2 paid `8 -> 1` with pending still 1 at BOTH
snapshots, our unit total went 6 (r2-after) → 7 (r3-before) with r3's own window adding nothing —
the create landed in the snapshot GAP. F1 therefore verifies an arrival in the pay window OR by the
next window's before-snapshot (same tuple, same tile, mineral identity still exact).

**CONFLICTS on the record (not silently picked).** The skill's `production-queue.md` said the
queued-count byte lives at `0x94dc84`; the pop instruction reads `0x94de84` (`0x4ef613`). The old
m56 docstring called the pay `0x4f0ca6`; the gate's pay store is `0x4efedd` (there IS another
`+0x40` store at `0x4eff20` in the same function). Both are reported in the skill and in
SESSION_NOTES; neither is resolved by a poke.

## THE PICK — M60: THE CHOOSER AND THE CREATE GUARD

One milestone, then stop. Do not tune `predict()` to observations.

1. NAME `FUN_004f6030(base, 0, 0, &budget)` — the chooser `FUN_004e5ae0` calls before the gate
   (its scratch is record `+0x14..+0x30` = `0x8f0d74..0x8f0d90`, seeded to 0 / 999999 by
   `0x4e5ae0`; the `+0x38` bits `0x1000000/0x2000000/0x4000000/0x8000000` select which pick it is
   on). Cite disasm lines; re-read every store before believing a decode.
2. Explain what writes `[base+0x10]` (the create guard at `0x4eff32`) and prove BY POKE whether a
   nonzero value is what makes a paid window produce no unit. One variable, control base untouched,
   read back.
3. Only then decide whether another faction's next production is predictable at all; if it is,
   extend the rule and add rule cases; if it is not, say so and leave the scope as is.
4. Acceptance: `python3 scripts/m56_build.py --ui-queued <Korolev idx> --boundaries 10 --timeout
   400 --no-poke-hold` prints **PASS** on ONE real invocation. If it cannot, record the negative
   and merge nothing.
5. `python3 scripts/test_m56_predict.py` (17/17 today) and the bad fixture (exit 1) stay green;
   add cases for anything new.

## LIVE FACTS / KIT

- **Box at session-98 close:** terran.exe alive, year **2182**, n_bases 22, ours 2 — University
  Base (28,42) idx 0 min 4 income 0 pend 0 head 2; Korolev Center (29,42) idx 17 min 0 income 0
  pend 0 head 2; 10 ours units, 0 actionable (all held). **Preflight first:**
  `python3 scripts/smac_preflight.py` (read-only, exit 1 on FAIL).
- **Reload when the bases stop accruing** (they do — upkeep eats the yield):
  `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` (BARE filename; prints
  `difficulty level: talent`) → `python3 scripts/m54g_prep.py` → `python3 scripts/smac_play.py
  --turns 1 --timeout 200 --no-escape 3000 --orders-per-turn 1 --verbose --tag t` (founds Korolev
  at (29,42), prints "Korolev Center founded") → locate Korolev **BY NAME**
  (`python3 scripts/m59_head.py --stage read`) → `python3 scripts/m57_ui_enqueue.py --base-index
  <fresh idx> --cell-item 2 --inserts 1` → `python3 scripts/m59_head.py --stage read --hold` → the
  acceptance run WITH `--no-poke-hold` (any write, including the run's own `poke_hold`, fails the
  provenance floor).
- `python3 scripts/m59_head.py [--stage read|poke --base NAME --minerals N] [--hold]` — the M59
  instrument: minerals/income/pending/head/`rec10`/derived price/per-tile unit multiset for both
  our bases; `--hold` pokes every one of ours to order 2 and reads back.
- `python3 scripts/m58_price.py [--owner 3] [--type 2]` — the price chain from live memory.
- `python3 scripts/m57_stores.py --base "Korolev Center" --boundaries 3 --timeout 220 --tag t` —
  the `+0x40` store tracer (arm only when no gdb runs; `python3 scripts/m57_credit.py --stop`
  detaches a leftover). Pokes LIE under a tracer: poke and read back before attaching.
- `scratch/m574/text.txt` (whole `.text` objdump), `scratch/m59/queue_census.py` (every store to
  the base array `0x95da10+i*0x130` and to the faction array `0x94de84`, grouped by record offset,
  plus the pop call sites) and `scratch/m59/cfg.py` + `scratch/m59/dom.py` (block-level CFG and
  the "must-reach-through" test for `FUN_004ef6d0`) are on disk, gitignored. Regenerate the dump:
  `objdump -d -M intel --section=.text programs/terran.exe > scratch/m574/text.txt`.
- Rule cases today: `test_m56_predict.py` 17/17; `m56_build.py --fixture
  scratch/m56_fixture_bad.json` exit 1; `test_walk_diff.py` 37/37; `test_classify.py` 17/17;
  `check_classes.py` 17/0 (delete the untracked `*_3x.png` siblings right after).
- **Evidence 28.9 MB, the gate FAILs at 30.** `python3 scripts/evidence.py budget` before adding
  anything; delete `trace_m56_build_*` files that `--fixture` runs leave and any `*_3x.png`.

## TRAPS

- `m57_ui_enqueue.py` on a just-founded base can read an EMPTY chooser (`FAIL: item 2 not in
  candidate array []`); a second attempt works. Do not conclude the item is unresearchable.
- The after-snapshot can catch the player walk mid-round (`cur_player 6` at the snapshot) — that
  burned run `..._145103` at r2. It is a harness race: RE-RUN, do not edit the floor.
- The base array compacts mid-run (18 → 17 twice now): locate bases BY NAME every step; the
  bookkeeping pairs by name, and the `--ui-queued` index is only the START index.
- A base display left open swallows every turn-end key (Escape closes a PANE safely; Escape on the
  bare map raises the quit prompt — never click OK on it). The units-not-moved confirm takes NO
  Return (`m56_build` clicks YES then the OK bar 26 px below). Orders mode `0x91b5b8 == 0` makes
  every order key a no-op; `m57_ui_enqueue` restores it after the enqueue.
- gdb: no `si` inside a breakpoint command list; `set print frame-quiet` is not a command in this
  gdb; stdout must be DRAINED. For a plain `mov [reg+disp],src` the source operand IS the after
  value. `os.pread` on `/proc/<pid>/mem` EIOs here — `seek`+`read`. Popup BARS ignore clicks
  (Return works on the default row); MENU click (75,369); TURN COMPLETE (650,410).
- One variable at a time; if two things moved together write "confounded". Documents lose to
  instruction bytes only after a poke — until then REPORT the conflict (this session reported two:
  `0x94dc84` vs `0x94de84`, pay `0x4f0ca6` vs `0x4efedd`).
- Never: commit to main; `pkill -f` / `pgrep|kill` by name; Escape on the title screen; OK on the
  quit prompt; `--mode stop`; `file://` with `--load`; a clear-prefixed command; backticks in a
  commit message; `skill_manage delete`.

## CLOSING ORDER (exactly)

1. `## Session <N>` in `SESSION_NOTES.md` (what changed, numbers WITH the command, open, next pick).
2. Rewrite this file; `wc -c NEXT_PROMPT.md` <= 15,500.
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/` (the gate checks the sync).
4. `git add -A && git commit -m '<ID>: checkpoint'`.
5. `python3 scripts/gate.py --base main` — GREEN.
6. Submit/merge ONLY on a real PASS: `python3 scripts/milestone.py submit --title "..."` →
   `gh pr checks <n>` → `python3 scripts/milestone.py merge <n>`. Otherwise say so and merge nothing.

## Report

One screen: what changed, the acceptance numbers WITH the command, what is open, the next pick.
