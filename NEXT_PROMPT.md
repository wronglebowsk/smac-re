# NEXT_PROMPT.md — footing for the next session (session 96 close, 2026-10-26)

## THE LEDGER

Merged: **M54A–M54E** (#39-#44), **M54F–M54i** (#47-#50), **M54i2/M54j/M54k** (#51-#53), **M54k2**
(#54), **M55** (#55), **M56** (#56, the production gate = mineral storage). **M57 is UNMERGED on
`milestone/m57` (local only — a pre-receive hook refused the push).**

Session 96 ran **M57-4 and it PASSED its own acceptance**: `scripts/m57_stores.py` put a breakpoint
at every one of the 23 stores to `[reg+0x40]` that a base visit can reach, and over 3 consecutive
boundaries every store was attributed to a named site, every memory-observed value was reproduced by
replaying the stores from the run-start value, and every per-boundary sum equalled the observed net
change (zero unattributed deltas). The M56 gate was then re-run **unchanged** and still FAILs, so
per the footing **M57 stays unmerged** — the merge condition is the M56 production-prediction gate,
and what blocks it is now a NAMED thing (the price constant), not a missing mechanism.

## WHAT SESSION 96 MEASURED (do not re-learn)

**The visit.** One base's visit is `FUN_004f5a70(base_index)` (single caller `FUN_00520540`): it
computes `lea ecx,[index*304 + 0x95da10]`, stores it to the current-base global `DAT_0x8f0d60` at
**0x4f5a99** (that instruction is the per-visit marker — `$ecx` IS the record address), and calls
0x4e8d60, 0x4e78e0, 0x4e92c0, 0x4e93f0, 0x4eaa10, **0x4ef6d0** (the production/mineral visit) and
**0x4f26e0**.

**The census.** `objdump -d -M intel --section=.text` -> 65 stores to `[reg+0x40]` in the image;
mapped through `ghidra_out/index.csv` and filtered by call-graph reachability (depth 4) from
`FUN_004f5a70` / `FUN_00417ee0` / `FUN_004f6030` -> **23 sites** (`python3 scripts/m57_stores.py
--sites` prints the table with each site's base register and its source operand). The
`lea reg,[reg2+0x40]` pointer-arithmetic shape was censused too: no store runs through such a
register in those sets, so the list is complete for a visit.

**What actually fires in a visit (read back at the sites, Korolev Center):**
- `0x4ef7f6` **ADD**: `edx = [base+0x40] + [base+0xd0]`; the delta EQUALS the `+0xd0` field as it
  reads **at the visit** (+2 with d0 2, +1 with d0 1 twice — d0 moves when the garrison changes),
  gated `d0 >= 0 && head != -38 && !([base+0x30] & 2)` (0x4ef7db-0x4ef7f9).
- the completion gate is **`cmp [curbase+0x40], edi ; jge` at 0x4efa5e**, where `edi` is built at
  0x4efa4b-0x4efa52: `edi = eax` from `call 0x4e40a0` (item cost for the faction) then
  `imul edi, eax` from `call 0x5ac950` (a factor). **edi measured 9 twice** (10->1 and 9->0) for a
  queued Scout Patrol — **not the 10 the M56 model deducts**.
- `0x4efedd` **PAY**: `esi = [ecx+0x40] - edi` (ecx = `DAT_0x8f0d60`), with pending 1 -> 0 in the
  same visit. Session 94's unnamed "second movement inside one visit" (7->9 then 9->0) is now NAMED:
  the add at 0x4ef7f6 and the pay at 0x4efedd.
- the clamp sites `0x4eff20` / `0x4f0ce9` (store `max(0, min([0x92a370], d0))` only when storage >
  that limit) and `0x4f2d7d` (the distribution store in `FUN_004f26e0`) **never fired** for our base.

**Acceptance (the PASS).** `python3 scripts/m57_stores.py --boundaries 3 --timeout 200 --tag m574c`
-> `PASS store-sequence enumeration: 4 stores over 3 boundaries, every store attributed to a named
census site, every sampler value reproduced by the replay, per-boundary sums equal the observed net
changes` — Korolev Center idx 17 (0x95ee40), queue filled by the GAME's BUILD UI (pending 1, harness
wrote nothing), 3 visits, boundaries 2163->2166, sampler values [7, 0, 1, 2], sums 0/-7/+1/+1 ==
observed nets; `evidence/trace_m574c.jsonl`, `evidence/m574c.gdblog`.

**The M56 gate, re-run unchanged.** `python3 scripts/m56_build.py --ui-queued 17 --boundaries 10
--timeout 300` (UI-filled queue, `memory writes: 0`, start minerals 2 < price 10) ->
**`FAIL production prediction accounting`**: `BAD at least 1 POSITIVE prediction verified — 0/0`,
`BAD r7 bookkeeping base 17: NOT predicted to arrive -> queue held — pending 1->0 ... (minerals 0
vs price 10)` — the arrival came at minerals 8 (8 + income 1 = 9 >= the measured price 9). 10/10
boundaries flipped, provenance + storage-below-price floors ok. **Nothing was weakened.**

## THE PICK — M58: NAME THE PRICE (why `edi` is 9)

One milestone, then stop. Do NOT tune `predict()` to observations; DERIVE the price.

1. Read the two calls that build `edi` (disasm windows, not whole functions): `0x4e40a0` — already
   exported at `evidence/m52a_fn4e40a0_disasm.txt` — and `0x5ac950` — exported at
   `evidence/m52b_fn5ac950_disasm.txt`. Find what each returns for (item id 2 = Scout Patrol, our
   faction 3, `DAT_0x68cbb0` = the base index, and the `-1`, `1`, `faction` pushed at
   0x4efa34-0x4efa38).
2. Reproduce **9** statically (alpha.txt / the tables those two functions read) and say what the
   factor multiplies (era? difficulty? quantity?). Cite the disasm lines you read, per the skill's
   audit rule: re-read every store site and the guard before believing a decode.
3. Make `m56_build.py` take the price from that derivation (a named constant WITH a cite, not a
   tweak), leave every floor and threshold EXACTLY where it is, and re-run
   `python3 scripts/m56_build.py --ui-queued <Korolev idx> --boundaries 10 --timeout 300`.
4. Acceptance: `m56_build.py` prints PASS with every floor intact (>= 1 POSITIVE prediction
   verified) on ONE real invocation. If it does, merge the branch that carries it. If it cannot,
   record the negative and merge nothing.
5. `python3 scripts/test_m56_predict.py` and the bad-fixture negative must stay green.

## LIVE FACTS / KIT

- **Preflight FIRST:** `python3 scripts/smac_preflight.py` (read-only, exit 1 on FAIL) — prints our
  bases BY NAME with index/coords/pending/head/minerals/income, tracer state, /tmp, evidence budget.
  `SMAC_PID=<pid>` overrides pgrep (it is also the negative test).
- **Box at session-96 close:** year 2177, n_bases 23, ours 2 — University Base (28,42) min 0 income
  0 and **Korolev Center (29,42) idx 17 min 2 income 1**, pending 0 head 2 (stale), 11 units ours,
  0 actionable. Korolev's income is thin because the garrison's upkeep eats the yield: expect to
  reload for a clean economy — `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch`
  (BARE filename, HUD at 2150) -> `python3 scripts/m54g_prep.py` -> one `python3 scripts/smac_play.py
  --turns 1 --timeout 200 --no-escape 3000 --orders-per-turn 1 --verbose --tag <t>` founds Korolev
  -> preflight. Locate the base BY NAME afterwards; indices drift.
- **Store harness:** `python3 scripts/m57_stores.py [--base "Korolev Center"] [--boundaries 3]
  [--timeout 200] [--tag t] [--tail 3] [--stall 90] [--sites]`. It arms 23 conditioned breakpoints +
  the visit marker, samples at 2 ms, drives the turn itself (Return / OCR for the units-not-moved
  confirm / `h` / OK click), and prints the store table, the per-boundary accounting and PASS/FAIL.
  `--sites` prints the census table. `python3 scripts/m57_credit.py --stop` detaches a leftover gdb
  (the store harness refuses to arm while any gdb is running).
- **Fill the queue with the GAME, not memory:** `python3 scripts/m57_ui_enqueue.py --base-index <idx>
  --cell-item 2 --inserts 1` (picks the chooser cell BY CONTENT, reads pending after every click,
  restores orders mode, and NOW closes the base display it opened, verifying the class).
- **Before any boundary watch, HOLD everything:** poke `+17 = 2` on every one of our records
  (`UNIT_ARR 0x933278`, stride 52, owner byte +14, type u16 at +10 < 24) and read it back — with any
  actionable unit the auto-end never fires and a 90 s watch sits parked on `cur_player 3`.
- Rule cases: `test_m56_predict.py` -> PASS 11/11; `m56_build.py --fixture
  scratch/m56_fixture_bad.json` -> exit 1; `test_walk_diff.py` 37/37; `test_classify.py` 17/17;
  `check_classes.py` 17/0 (delete the UNTRACKED `*_3x.png` siblings right after).
- Census regeneration (scratch is gitignored): `objdump -d -M intel --section=.text
  programs/terran.exe > scratch/m574/text.txt` then `python3 scratch/m574/census.py` — it prints the
  union site list, the owner of each store and the `lea +0x40` audit. If `scratch/m574/` is gone,
  start from the table baked into `scripts/m57_stores.py` and re-derive only if it disagrees.
- `python3 scripts/evidence.py budget` BEFORE adding frames — 26.4 MB now, the gate FAILs at 30. The
  14 `*_3x.png` upscales were `git rm`'d this session (`evidence/m574_prune_manifest.tsv`).

## TRAPS

- **`si` inside a breakpoint commands list ENDS `gdb -batch`**: the first hit printed the step
  location then `[Inferior 1 ... detached]` and the watch died after one store. For a plain
  `mov [reg+0x40],src` the store's own source operand IS the after value — print it and let the
  memory sampler prove it. `set print frame-quiet` is not a command in this gdb and aborts the whole
  command file.
- **The base array reorders/compacts DURING a watch**: Korolev walked index 18 -> 17 (0x95ef70 ->
  0x95ee40) mid-run; after that the baked address held ANOTHER faction's record (storage 19, head
  -27) and conditioned breakpoints would credit that base's stores to ours. `m57_stores.py` verifies
  the NAME at the address every sample and ends the watch at the move. Locate bases BY NAME every
  step; never carry an index across a run.
- **A base display left open swallows every turn-end key** (class `base`, parked `cur_player 3`
  through Return/h/OK for 90 s). Escape closes a PANE safely; Escape on the bare map raises the quit
  prompt and after it the game takes no keys — reload only. Never click OK on the quit prompt.
- **The units-not-moved confirm takes NO Return**: click the YES row then the OK bar 26 px below
  (`smac_play.answer_confirm`); a driver that only presses Return sits on it with the year frozen.
- **orders mode `0x91b5b8` at 0 makes every order key a no-op** and the turn never ends.
- A hardware watchpoint on `+0x40` crawls the game (the field is read constantly) — breakpoints at
  the write sites only. Register side-values away from the store itself are not evidence; read the
  fields from the baked base address, and keep verifying that address still holds YOUR base.
- `os.pread` on `/proc/<pid>/mem` EIOs here — use `seek`+`read`. Pokes lie under a tracer.
- gdb's stdout must be DRAINED (non-blocking `os.read`, wall-stamp each line) or 64 KB of hit lines
  stalls the inferior at the next printf.
- Popup BARS ignore clicks; Return works on the default row; MENU click (75,369) works; TURN COMPLETE
  is at (650,410). Never `pkill -f`/`pgrep|kill` by name; no `--mode stop`; no `file://` with
  `--load`; no backticks in a commit message; `skill_manage delete` is banned.
- One variable at a time: if a position AND a tile changed, write "confounded".

## CLOSING ORDER (exactly)

1. `## Session <N>` in `SESSION_NOTES.md` (what changed, numbers WITH the command, open, next pick).
2. Rewrite this file; `wc -c NEXT_PROMPT.md` <= 15,500.
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`.
4. `git add -A && git commit -m '<ID>: checkpoint'`.
5. `python3 scripts/gate.py --base main` — GREEN.
6. Submit/merge ONLY on a real PASS: `python3 scripts/milestone.py submit --title "..."` ->
   `gh pr checks <n>` -> `python3 scripts/milestone.py merge <n>`. Otherwise say so and merge nothing.

## Report

One screen: what changed, the acceptance numbers WITH the command, what is open, the next pick.
