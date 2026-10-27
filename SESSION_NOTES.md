

Older sessions: `docs/sessions/sessions-91-92.md` (2 sessions). Read it only when a question reaches back before session ## Session 93.

## Session 93 (2026-10-25) — M57: **THE GAME'S OWN BUILD UI WROTE THE QUEUE (proven, 0 memory writes) AND THE QUEUED UNIT WAS PAID FOR BY INCOME — BUT THE EXACT-ROUND PREDICTION FAILED 1/2, SO NOTHING MERGES** — changed `scripts/m56_build.py` (`--ui-queued N` mode: no poke of any kind, `writes` counter, queue-provenance floor, "storage below price at run start" precondition/floor, `predict(..., income_first=)`), `scripts/test_m56_predict.py` (8 -> 11 cases), this file, `NEXT_PROMPT.md`

**ACCEPTANCE: NOT MET.** `python3 scripts/m56_build.py --ui-queued 18 --boundaries 5 --timeout 120` -> exit 1, `FAIL production prediction accounting`; trace `evidence/trace_m56_build_20261025_212402.jsonl`. Floors that PASSED: 5/5 boundaries flipped +1 (2152->2157, walk [0,2,3,5,6,7]), `queue provenance: GAME-filled, zero memory writes by this script` (pending 2 head 2 base 18 Korolev Center, `memory writes: 0`), `completion NOT armed: storage below price at run start` (minerals 4 < price 10), and 1 of 2 positive predictions verified. Floors that FAILED: `r2 prediction ... observed net 0` and `at least 1 POSITIVE prediction verified — 1/2`. Nothing was weakened to hide it.

**What was PROVEN (read back from memory, not inferred).** (1) **The queue can be filled by the GAME, not by us**: with the cursor poked to (29,42), `SEL=-1`, orders mode OFF, `b` opens the base display; the right arrow at (523,433) switches the QUEUE widget to Korolev; clicking queue row 1 at (185,437) opens the item chooser (bar pixel (160,343) = (103,91,181)); the candidate array `DAT_009267e4`/count `0x9267e0` maps 5-col grid order -> cell, Scout Patrol (id 2) at cell 3 -> (509,60), `[sub+0xa774]` reads 3; `INSERT` at (497,343) -> **pending 0->1, head +0x50 = 2, slot +0x54 = 2**; `OK` at (285,343) = mode 0 commits and does not restore. A second INSERT took pending to 2. (2) **The completion was paid from income**: at 2155->2156 the queued Scout Patrol arrived with **pre-boundary storage 8 < price 10**, pending 2->1, queue left-shifted. (3) `base+0xd0` reads 2 but the ACTUAL storage deltas across those five boundaries were **0, +4, 0, -5, +2** — `+0xd0` is NOT the per-round mineral credit, which is why `income_first` over-predicted r2 (8+2 >= 10, no arrival) and only r3 landed. That is the open question, and it is a base-field finding, not a threshold to relax.

**Traps that cost this session (all measured).** (a) **Escape on the map raises the quit prompt, and once that prompt is dismissed the game stops accepting KEYS entirely** — `h`/Return left `cur_player 3`, `turn_flags 0`, order bytes unchanged for 150 s while mouse clicks on the HUD still worked (MENU opened); the map area rendered black. A 172 s run burned on this. Reload is the only recovery. (b) **`orders_mode` (`0x91b5b8`) silently at 0 disables every order key** — `h` falls through to the cursor-tile handler and nothing happens; the `h`-escalation therefore depends on orders mode being ON. (c) **Clicks on popup bars do not register** (obliterate OK, hint Close/"Don't Show Again"), but Return on the default row and Escape do; the obliterate prompt's NO is the default and Return spares the base (verified twice: both bases still ours). (d) **`/tmp` hit its quota and `P.freeze()` failed silently**, returning a path to a file that did not exist (`classify` then said `movie`) — check `df /tmp` before trusting a frame. (e) A first `INSERT` read `pending 0` immediately after the click and had in fact landed; re-read after ~1 s.

**Next (M57-2):** find the true mineral credit. Watch `base+0x40` at 2 ms across one boundary with an EMPTY queue on an income base (`scripts/m55_boundary.py` sampler + `scratch/m56_dump.py`), record the credit sequence, and locate the writer that adds to `+0x40` (candidates: `0x4ef7f6` in the base visit, `FUN_004e9557` recompute). Then re-run `--ui-queued 18 --boundaries 5` unchanged: the acceptance floors stay exactly as they are, including 1/1 positive predictions.

## Session 94 (2026-10-25) — M57-2: **THE CREDIT IS NOT A PER-ROUND CONSTANT AND THE UNCHANGED GATE RE-RUN PRINTED FAIL — so NOTHING MERGES; the measured answer: storage moves through SEVERAL stores inside one base visit (income add, a second unnamed movement, the pay, the pop) and the net per-round delta is event-dependent** — changed `scripts/m57_credit.py` (NEW: gdb breakpoints at the store sites conditioned on the base pointer + a fast sampler + m56_build's Return/h/OK escalation), `scripts/m57_ui_enqueue.py` (NEW: scripted BUILD-UI enqueue, read-back after every click, queue-widget cycling + INSERT retry + cell located by CONTENT), `scripts/m57_uiwatch.py` (NEW: gdb on the enqueue dispatch printing `*(0x8f0d60)` at every hit), `evidence/m57c_q.log` + `trace_m57c_q3.jsonl` (the boundary store sequence), `evidence/trace_m56_build_20261025_215056.jsonl` (the FAIL acceptance run), this file, `NEXT_PROMPT.md`, skill `references/production-queue.md`

**ACCEPTANCE: NOT MET.** `python3 scripts/m56_build.py --ui-queued 17 --boundaries 8 --timeout 240` -> exit 1, `FAIL production prediction accounting`; trace `evidence/trace_m56_build_20261025_215056.jsonl`. The queue was GAME-written (UI enqueue read back `pending 0->1, head 2, slot4 0->2`, `memory writes: 0`) and the run start satisfied the precondition (`minerals 4 < price 10`). Floors: 8/8 boundaries flipped +1 (2168->2176, walks home in 6 of 8); provenance + storage-below-price floors `ok`; but **`BAD at least 1 POSITIVE prediction verified — 0/0`** (the model never predicted the completion: it read income 1/round; the visit completed at minerals 7), `BAD r4 bookkeeping base 17: NOT predicted to arrive -> queue held — pending 1->0` and `BAD r4 unexplained ORDER-0 arrival on OUR base 17` (the produced Scout Patrol), plus `BAD r6/r7 player walk came home after the flip` (the after-snapshot at `--settle 0.3` caught cur_player MID-WALK — a sampling artifact). Nothing was weakened. Rule/fixture/classifier gates stay green: `python3 scripts/test_m56_predict.py` -> `PASS 11/11 production-prediction cases`; `python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit 1 `FAIL production prediction accounting`; `test_classify.py` 17/17, `check_classes.py` 17/0 (no new classes, no new frames).

**THE CREDIT, measured (all read from memory, `evidence/trace_m57c_q3.jsonl` + `evidence/m57c_q.log`).** Korolev Center (29,42), queued by the game's UI at minerals 4 < price 10. Korolev storage round start -> after: `4->5, 5->5, 5->6, 6->7, 7->0` with the income field reading 1,1,1,1,1 then 0 after the produced unit's upkeep landed. The completion fired in the round whose round-start income read 1, i.e. when minerals+income = 8 < 10 — the visit's NET delta is not the round-start `+0xd0`. The 2 ms boundary sequence: `store 7->9, store 9->0, pending 1->0` (income add, then a SECOND movement, then the pay, then the pop, all inside one base visit at the flip). `+0xd0` itself walked 1 -> 3 -> 0 -> 1 -> 2 -> 3 -> 4 across the run as produced units arrived and were DISBANDED (the support popup: "the minerals output of Korolev Center is not sufficient to support Scout Patrol") — upkeep tracks the garrison, so the credit is recomputed EVERY visit and is event-dependent. Confirmed against the disasm + m52a: the income add is gated `d0 > 0 && head != -38 && !(flag30 & 2)` (0x4ef7db-0x4ef7f9) and **DOES fire with pending 0 while the head slot is stale** (the pop left-shifts but leaves stale ids in the tail — measured: adds landed with pending 0, storage 0->1->2); the pay at 0x4efed8 deducts `$edi` (9 observed at storage 9); clamp B at 0x4eff20 stores only when storage > min(cap `0x92a370`=10, d0) — and m52a's live line (`SPENDA ... old=200 new=190 edi=10` at price 10) supersedes NAMED's "edi = the sweep-entry index" row: **edi is the price**.

**gdb findings (the harness works; several of ITS prints did not mean what I assumed).** (a) The conditional breakpoints (`break *0x4ef7db if $eax == <base addr>`) DID filter to the Korolev visit — the printed `+0x40` (via the baked base pointer) matched the sampler transition for transition — but the REGISTER side-values printed garbage relative to the fields (`$ecx` as d0 read 4/5/6/18 where the field read 1-3; the clamp pair read cap=11 d0=104) and the GATE at `0x4f0a3d` never fired for Korolev in any run (it sits on the `*0x8f0d60`-current-base branch reached only via the 0x4ef985 AND-test, not on the per-base path). **Treat pc-tagged register prints as UNVERIFIED; only the sampler + field read-backs are evidence.** (b) The hardware watchpoint on `+0x40` is unusable for cadence work: the field is READ constantly, the inferior crawled (1 round in 45 s, year never moved) — use breakpoints at the write sites. (c) `m57_uiwatch` proved the enqueue dispatch `0x417ee0` fires with `curbase = 0x95ef70` = Korolev's record (param1=1 param2=1) on the INSERT click, but the static store addresses m53g_drive lists (`0x418b57/0x418ad3/0x418ac7/0x418b24`) did NOT hit on that write — the enqueue store addresses need re-derivation.

**UI findings (all read back).** (a) The QUEUE widget's base is INDEPENDENT of the display's base (both orders observed: `b` opened on Korolev with the widget on University, and the reverse); the right arrow (523,433) moves the field `0x6a9480+0x3ff3c` and INSERT lands on whichever base the widget holds — recipe: cycle the arrow until `+0x3ff3c` == the target index, then row 1 (185,437), cell, INSERT (497,343), OK (285,343), reading pending after every click. (b) The chooser grid position is ERA-DEPENDENT: Scout Patrol (id 2) is cell **4** now (`DAT_009267e4` = [192,195,194,193,2,...], count 67) where session 93 measured cell 3 — locate the cell by CONTENT. (c) The base array compacts: Korolev's index walked 17 -> 18 -> 17 within this session (n_bases 29 -> 19 -> 23 -> 25); locate bases by NAME/(x,y), never by remembered index. (d) The box at close: **2176, Korolev minerals 0, income 0, pending 0 with stale head 2, 10 units all HELD, 2 bases, pid 1538414** — Korolev's income is now ZERO (the garrison's upkeep eats the yield), so nothing more accrues there without an economy change or a reload.

**Open.** (1) Name the SECOND store: enumerate every write to `+0x40` inside one visit (the 7->9->0 middle movement is unnamed; candidates: a second income site, the upkeep/spend path, the recompute through another field) with breakpoints at ALL disasm write sites, not a hw watchpoint. (2) Whether `+0xd0` at round start can be predicted from garrison + facility bitmap (the disband/upkeep chain). (3) The r6/r7 walk-home FAIL is a settle artifact — `--settle` must exceed the walk (~1-2 s) or the floor must read the timeline's final cur_player. (4) The enqueue store addresses inside `0x417ee0`. (5) Whether a documented negative merges — per the rule ("merge ONLY on a PASS") the branch holds UNMERGED; no PR was opened.

**Next (M57-3):** give the loop an income-STABLE base: reload `m54b_clean.SAV` + re-found (`m54g_prep.py`, 2 founding turns) exactly as session 93 did (that box had Korolev income 2 and produced the r3 completion), UI-enqueue ONE Scout Patrol at minerals < 10, then `python3 scripts/m56_build.py --ui-queued <index> --boundaries <enough for the accrual, ~6-10 at ~20 s/round> --timeout 240 --settle 2.5` (settle only moves WHEN the after-snapshot is taken, so the walk-home floor sees the walk finished — the floor semantics are unchanged). Acceptance unchanged: every floor as it stands + >= 1 verified positive prediction. If income is stable the model predicts the exact round; if the visit's second store still breaks it, the documented negative stands and the next step is Open (1), the full store enumeration.

**Addendum (same session, after the close): why the session was slow, and two fixes.** The time went to *stale remembered facts*, not to hard problems: (a) a retyped `cur_player` address (`0x91c634` instead of `0x985dcc`) burned a 45 s smoke run and an OCR classification detour; (b) the UI recipe's arrow/cell/index facts had drifted (queue-widget base vs display base; Scout Patrol cell 3 -> 4; base index 17 -> 18 -> 17), so two enqueues silently landed on University Base; (c) a hardware watchpoint on a constantly-READ field made the inferior crawl (1 round/45 s) — breakpoints at the write sites are the tool; (d) the sampler ran unthrottled and wrote 1.4 GB of traces (gate RED until downsampled); (e) the 8-boundary acceptance was launched without first doing the credit arithmetic. Fixes added and tested: **`scripts/smac_preflight.py`** (read-only, exit 1 on any FAIL: the one authoritative address table, game alive, TracerPid=0, no gdb, our bases located BY NAME with index/coords/pending/head/minerals/income, unit decode, /tmp room, evidence budget; `SMAC_PID` override is the negative test — `SMAC_PID=999999` -> exit 1) and a **credit-arithmetic line in `m56_build.py --ui-queued`** printed BEFORE the run (`needs 4 more minerals at 1/round -> ~4 round(s) to the gate`, recorded as a trace event; a diagnostic, no floor touched). Verified live: preflight PASS on the real box; `python3 scripts/m56_build.py --ui-queued 0 --boundaries 1 --timeout 60` -> `credit arithmetic: needs 4 more minerals at 1/round -> ~4 round(s) to the gate`. Also observed by the preflight: the two failed enqueues left **University Base pending 2 (minerals 6, income 1)** — a GAME-written queue sitting there, which is a candidate for M57-3 as well.

## Session 95 (2026-10-25) — M57-3: the gate ran on a GAME-filled queue and got 1/2 — the model premise is falsified, nothing merges

**What changed.** `scripts/smac_preflight.py` (NEW, read-only orientation: authoritative address
table, game alive, TracerPid/gdb, our bases BY NAME with index/coords/pending/head/minerals/income,
unit decode, /tmp + evidence budget; `SMAC_PID` override is the negative test). `m56_build.py`:
credit arithmetic printed BEFORE a --ui-queued run; the boundary watch now breaks when the walk is
HOME (was a fixed settle, which either missed the walk or swallowed the next flip); and it answers
the "SOME OF OUR UNITS HAVE NOT YET MOVED" confirm via `smac_play.answer_confirm` (that dialog takes
NO Return — a 240 s run sat on it, year frozen). `m57_ui_enqueue.py` restores orders mode (0 makes
every order key a no-op and the turn never ends). Sampler throttled to 2 ms + the 1.4 GB of traces
downsampled to ~10 KB (the gate's 30 MB budget). Skill synced.

**The acceptance, unchanged.** `python3 scripts/m56_build.py --ui-queued 18 --boundaries 8 --timeout
240` on a fresh `m54b_clean.SAV` box (2154), Korolev Center [18] (29,42), queue filled by the GAME's
BUILD UI (pending 1, head 2, minerals 2, income 2, **0 memory writes**): **FAIL, exit 1**. Floors that
passed: 8/8 boundaries flipped +1 with the walk home, provenance GAME-filled/0 writes, storage below
price at start, per-round bookkeeping on r0-r2 (2->4->6->8, pend 1). Floors that failed:
- `1/2 positive predictions verified`. r3 predicted arrival (8 + income 2 = 10 >= price 10) and
  storage stayed **8 -> 8, pend 1**: the visit added NOTHING while the round-start income field read
  2. r4, with the identical round-start numbers, arrived: **8 -> 3, pend 0**.
- `r4 minerals debited by >= price` — net -5 from 8 (or -7 from the post-add 10), not -10.
- `r7 unexplained ORDER-0 arrival on OUR base 18` — storage **5 -> 0 with pending 0** and a new unit,
  i.e. a pay with an empty pending count (the queue slots never left-shifted: `[2,2,0]` all run).
So ONE queued Scout Patrol produced TWICE (r4 and r7) and the second production was paid at 5 < 10.

**Measured support (`m57_credit.py --base Korolev --boundaries 3 --tag m57k`).** 3 flips (2162->2165,
rounds 8.2/10.1/12.1 s — instant when everything is held), only 2 ADD hits and no GATE/PAY/CLMP for
the base; the register side-values are the known trap (the "d0" printed 18 = the base INDEX) but the
storage deltas agree with the sampler: an add of +1 while the field read 1, +2 while it read 2. **The
add uses the d0 current at the visit, which moves inside the round** — that is why an exact-round
prediction from the round-start snapshot is impossible, and why the same numbers produced no-arrival
then arrival one round later. The pay amount is also not the price at 0x4efed8 (5 paid, 8 paid) and a
produced unit's support is debited from the same field.

**Conclusion: NOTHING MERGES.** The M57 gate asserts a model the engine contradicts (one add per
round at the round-start income, one pay of exactly the price, pending as the queue truth). The
observed positive (1/2) is real but not enough, and no floor was weakened. Branch `milestone/m57`
holds: preflight, the arithmetic line, the confirm answer, the walk-home break, orders-mode restore,
2 ms sampler, and `scripts/m57_ui_enqueue.py` (UI queue fill with read-backs).

**Next pick (M57-4, the honest one): enumerate EVERY write to `base+0x40` inside one visit** —
breakpoints at all disasm write sites (0x4ef7f6 add, 0x4eff20 clamp B, 0x4efee3/0x4efeec pay,
0x4f0cc3 clamp-after-pay) over 3 boundaries on Korolev, with the queue filled by the UI, and record
(value_before, value_after, site, pending, head, d0) for each store. Only then can the gate's debit
floor and the second production be explained. Do NOT tune predict() to the observations.

## Session 96 (2026-10-26) — M57-4: **THE STORE ENUMERATION PASSES — every write to `base+0x40` in a 3-boundary window is attributed to a NAMED census site — and the engine's price is 9, not 10, which is why the M56 gate still FAILS with every floor intact**

**What changed.** `scripts/m57_stores.py` (NEW — 23 conditioned breakpoints + the visit marker +
a 2 ms sampler + the replay acceptance), `scripts/m57_ui_enqueue.py` (now closes the base display
it leaves open and verifies the class), scratch `scratch/m574/census.py` (the whole-image store
census + call-graph filter that GENERATED the site table), skill `references/production-queue.md`
and `references/wine-operations.md`, `NEXT_PROMPT.md`, this file.

**ACCEPTANCE MET (M57-4's own gate).** `python3 scripts/m57_stores.py --boundaries 3 --timeout 200
--tag m574c` -> `PASS store-sequence enumeration: 4 stores over 3 boundaries, every store
attributed to a named census site, every sampler value reproduced by the replay, per-boundary sums
equal the observed net changes` — Korolev Center idx 17 (0x95ee40), queue filled by the GAME's
BUILD UI (pending 1, the harness itself wrote nothing), 3 visits, 3 boundaries 2163->2166, sampler
value sequence [7, 0, 1, 2], per-boundary sums 0/-7/+1/+1 == the observed nets, zero unattributed
deltas. Trace `evidence/trace_m574c.jsonl`, gdb log `evidence/m574c.gdblog`.

**The enumeration (read back at the sites, each breakpoint conditioned on the store's OWN base
register == our record).** A visit is `FUN_004f5a70(index)`: it computes
`lea ecx,[index*304+0x95da10]`, stores it to the current-base global `DAT_0x8f0d60` at **0x4f5a99**
(the per-visit marker), and calls 0x4e8d60, 0x4e78e0, 0x4e92c0, 0x4e93f0, 0x4eaa10, **0x4ef6d0**
(the production visit) and **0x4f26e0**. Whole-image census: **65 stores to `[reg+0x40]` in
`.text`, 23 reachable** from the visit driver / the queue edit / the AI chooser; the
`lea reg,[reg2+0x40]` pointer-arithmetic shape has no store through it in those sets. In the
measured windows only two sites ever fire:
- **`0x4ef7f6` ADD** — the delta EQUALS the `+0xd0` field as it reads AT THE VISIT (+2 with d0 2;
  +1 with d0 1 twice; d0 itself moves with the garrison), gated `d0>=0 && head!=-38 &&
  !([base+0x30]&2)` at 0x4ef7db-0x4ef7f9.
- **`0x4efedd` PAY** — 9 -> 0 with pending 1 -> 0 in the same visit. The completion gate is
  `cmp [curbase+0x40], edi ; jge` at **0x4efa5e**, where `edi` is built at 0x4efa4b-0x4efa52:
  `edi = eax` from `call 0x4e40a0` (item cost for the faction) then `imul edi, eax` from
  `call 0x5ac950` (a factor). **edi measured 9 twice** (10->1 in `m574b`, 9->0 in `m574c`) — the
  deduction is 9, NOT the 10 the M56 model assumes.
- the clamp sites `0x4eff20`/`0x4f0ce9` (store `max(0, min([0x92a370], d0))` only when storage >
  that limit) NEVER fired; `0x4f2d7d` (the distribution store in `FUN_004f26e0`) never fired for
  our base. Session 94's unnamed "second movement inside one visit" (7->9 then 9->0) is now NAMED:
  the add at 0x4ef7f6 and the pay at 0x4efedd.

**The M56 gate, re-run unchanged per the footing.** `python3 scripts/m56_build.py --ui-queued 17
--boundaries 10 --timeout 300` on the UI-filled queue (pending 1 head 2, `memory writes: 0`, start
minerals 2 < price 10) -> **`FAIL production prediction accounting`**: `BAD at least 1 POSITIVE
prediction verified (non-vacuous) — 0/0` and `BAD r7 bookkeeping base 17: NOT predicted to arrive
-> queue held — pending 1->0 ... (minerals 0 vs price 10)` — the arrival came at minerals 8
(8 + income 1 = 9 >= the measured 9). 10/10 boundaries flipped; the provenance and
storage-below-price floors passed. Nothing was weakened.

**Traps found (all measured, all recorded in the skill).** (a) **`si` inside a breakpoint commands
list ends `gdb -batch`** — the first hit printed the step location then `[Inferior 1 ... detached]`
and the watch died after one store; the store's own source operand IS the after value for a plain
`mov [reg+0x40],src`. (b) **the base array reorders mid-watch**: Korolev walked index 18 -> 17
(0x95ef70 -> 0x95ee40) during a run, after which the baked address held ANOTHER faction's record
(storage 19, head -27) — the sampler now checks the NAME at the address every sample and ends the
watch at the move (the closing anchor is the last good sample, never a post-detach read-back: the
game keeps playing after the last flip). (c) **the enqueue recipe leaves the base display open and a
modal pane swallows every turn-end key** — a 90 s watch sat parked on `cur_player 3` through
Return/h/OK; Escape closes the pane (safe there, unlike the bare map). (d) `set print frame-quiet`
is not a command in this gdb and aborts the whole command file. (e) `os.pread` on `/proc/<pid>/mem`
EIOs here; seek+read works. (f) all our units must be HOLD (poke `+17`=2, read back) or the auto-end
never fires and a boundary watch burns its whole budget parked on our turn.

**Open.** (1) **The price**: name `0x4e40a0` (the cost) and `0x5ac950` (the factor) and reproduce
edi = 9 for a queued Scout Patrol — the M56 model's price constant is what is wrong, not its
floors. (2) Session 95's pay-with-pending-0 (its r7) was NOT reproduced in any measured window;
every pay seen had pending 1 at the store and popped in the same visit. (3) Whether a pay can fire
in a visit whose income add did not run (the `d0 > 0` guard). (4) The clamp sites' live behaviour
is still unmeasured. (5) **M57 stays UNMERGED** per the footing (the M56 gate is the merge
condition); `milestone/m57` holds everything, still unpushed (a pre-receive hook refused it earlier).

**Next pick (M58): the price.** Disassemble `0x4e40a0` and `0x5ac950`, reproduce `edi` for the
queued Scout Patrol from static tables, and re-run `m56_build.py --ui-queued` with the price
DERIVED rather than assumed. The floors do not move.

## Session 97 (2026-10-26) — M58: **THE PRICE IS NAMED — `0x4e40a0(owner,1,-1)` × type record `+41`, and the multiplier is live STATE, not 10: `[0x92ada8] == 1` makes it 9.** The M56 gate's price-10 was one game's difficulty. The acceptance never printed PASS, so **nothing was merged**.

**The call site (scratch/m574/text.txt, `objdump -d -M intel --section=.text`).**
`0x4efa2c mov ebx,[eax+0x50]` (eax = `DAT_0x8f0d60` = the base record, so ebx = the queue head),
`0x4efa31 mov cl,[eax+4]` (the base's owner byte — `base_dump.py`'s `fac`), `push -1; push 1; push
ecx; call 0x4e40a0` → `edi`; then `mov edx,ds:0x68cbb0` (the base index the visit is running),
`push 0; push edx; push ebx; call 0x5ac950` → `eax`, `0x4efa52 imul edi,eax`, `0x4efa5e cmp
[curbase+0x40],edi ; jge`. Ghidra agrees: `FUN_005ac950((int)*(short*)((int)&DAT_00933282 + …),
0xffffffff, …)` in `ghidra_out/shard_014.c:7994` proves its arg1 is a unit TYPE id.

**`0x4e40a0(owner, 1, -1)` is the per-owner cost factor in TENTHS** (`evidence/m53i_fn4e40a0.txt`,
`ghidra_out/shard_012.c:13825-13880`): mask `[0x985b10] & 0xff` tested bit-by-bit → 10 (`0x4e40c0`),
else the era table `[0x68cbb8 + era*4]` = {13,12,11,10,8,7} (sessions-64); rescale by `[0x92a294]`
(param_2 == 1 picks the +4 variant, `0x4e4119`); then `[0x92ada8]`: 1 → ×9/10, 0 → ×8/10, else
unchanged (`0x4e413b-0x4e4175`); then `switch` on the dword `[0x94d6a0 + owner*0x20bc]`
(sessions-56 calls it the faction government field; 0 = identity).

**`0x5ac950(type, DAT_0x68cbb0, 0)` is the type's cost**: the byte at `0x98ad88 + type*52 + 41`
(the M53b/M53f cost byte), clamped to ≥1 (and ≤999) ONLY when the plan byte `+42 == 8` and
param_2 > -1; type 2 has plan 3 → no clamp, and `type < 0x40` returns it straight out of the
`0x5ac993` branch (`ghidra_out/shard_015.c:23696-23745`).

**Live, read back:** mask `& 0xff` = 0x08 (owner 3 in), `[0x92a294]` = 10, `[0x92ada8]` = 1,
government field 0 → factor 9; type 2 `Scout Patrol` `+41` = 1 → **price 9**.
`python3 scripts/m58_price.py --owner 3 --type 2` -> `DERIVED price = factor_tenths 9 *
type_cost 1 = 9 … tracer-measured edi … MATCH`. **This is why sessions-56/64 saw 10**: they
measured `[0x92ada8] = 2` (no rescale) and M52b debited 10 — a different game's difficulty, not a
law. The scenario LOAD screen names the same scalar: this session's `m54a_load.py --relaunch`
printed `difficulty level: talent` on the loaded-game pane.

**Code.** `scripts/m56_build.py`: `price_of()` now goes through a new `cost_multiplier(owner)`
that re-implements `0x4e40a0` line-for-line and reads mask / era / `[0x92a294]` / `[0x92ada8]` /
the government field from the SAME snapshot the gate runs on — no constant chosen to fit an
observation. `scripts/test_m56_predict.py`: `MockMem` now serves those inputs (defaults = the
session-56 state, so every pre-M58 case keeps its numbers) and two cases were added —
`python3 scripts/test_m56_predict.py` -> **`PASS 13/13 production-prediction cases`** (case 12
ada8 1 → price 9; case 13 ada8 0 → 8 vs ada8 2 → 10 on an identical base, one variable).
`python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit **1** (unchanged).

**The bookkeeping was rebuilt on two measurements.** (a) `evidence/m58pop.gdblog` (Korolev Center
0x95ee40, queue UI-filled, minerals poked to 9 and read back): `VISIT#1 storage=9 pend=1 |
0x4ef7f6 add +0 (d0 0) | 0x4efedd pay 9->0 with pend STILL 1 | VISIT#2 storage=0 pend=0` — the pop
store `0x4ef641` (in `FUN_004ef5d0`, whose unit-path calls are `0x4f037b`/`0x4f0f46`) runs
STRICTLY AFTER the pay store, so a boundary after-snapshot can land on either side of it. Session
96's "pending 1 -> 0 in the same visit" is therefore not a rule: the 2177-box run read 1->1 then 0,
the 2151-box run read 1->0 in the pay window. (b) the mineral identity
`storage_after == storage_before + credit - price` is EXACT — measured 8+1-9 = 0 (2177 box),
8+2-9 = 1 (2151 box r2), 8+1-9 = 0 (evidence/trace_m56_build_20261026_142139.jsonl r8). The old
`storage_before - storage_after >= price` ignored the credit the model itself predicts
(`income_first`) and only ever passed because the armed run had income 0.

**ACCEPTANCE — three real invocations, none printed PASS (so nothing merged).**
1. `python3 scripts/m56_build.py --ui-queued 17 --boundaries 10 --timeout 300` (2177 box, queue
   GAME-filled, `memory writes: 0`) -> `FAIL production prediction accounting`: positive
   **1/1 verified**, **10/10** boundaries flipped, provenance + storage-below-price (2 < 9) ok;
   BAD `pending decremented` (1->1 in the pay window) and `minerals debited by >= price`
   (8->0, delta 8 vs the then-price 10). Those two BADs are what forced the rewrite above.
2. After the reload (`SMAC_SAVE='m54b_clean.SAV' m54a_load.py --relaunch` → HUD 2150 →
   `m54g_prep.py` → one `smac_play.py --turns 1` turn founds Korolev Center at (29,42) in 2151 →
   `m57_ui_enqueue.py --base-index 18`): `--ui-queued 18 --boundaries 12 --timeout 420` ->
   `FAIL`: positive **1/1** (r2, 8 + 2 - 9 = 1 exact), **12/12** boundaries, provenance ok; BAD the
   brand-new "no pop in the pay window" (r2 popped in-window) and `r11 unexplained ORDER-0 arrival
   on OUR base 17` — minerals 7 -> 0 (7 + 2 = 9 = the derived price) with a unit appearing while
   **pending read 0**.
3. `--ui-queued 17 --boundaries 10 --timeout 400` (`evidence/trace_m56_build_20261026_142139.jsonl`)
   -> `FAIL`: positive **1/1** (r8: 8 + 1 - 9 = 0 exact, unit +1 on (29,42)), **10/10** boundaries,
   provenance ok, 0 < 9 ok; BAD r0 walk-home race (`cur_player 6` at the after-snapshot), r9
   queue-held firing on the deferred pop (fixed after the run, NOT re-run), and r9 an unexplained
   +1 type-2 unit on University Base (28,42) with minerals 0 and pending 0.

**THE NEW FINDING — M59's target: pending is NOT the queue truth.** Korolev paid the derived price
twice more at **pending 0** (run 2: r6 minerals 7->0 with no unit appearing — confounded with a
disband — and r11 minerals 7->0 with a unit appearing), and a second Scout Patrol appeared on
University Base at minerals 0, pending 0 (run 3 r9). A base whose head SLOT holds a unit type keeps
buying it whenever `storage + income >= price`; M57-4's "pending is the only queue truth" is wrong.

**Trap.** `m57_ui_enqueue.py` on a just-founded base can read an EMPTY chooser
(`FAIL: item 2 not in candidate array []`); a second attempt works. Do not conclude the item is
unresearchable from the first attempt.

**Open.** (1) the acceptance has never printed PASS with the derived price — the blockers are the
queue-truth gap above and the r0 walk-home race, not the price; (2) the deferred-pop fix in the
`else` branch is written but not exercised by a real run; (3) `milestone/m58` (local, unpushed)
carries M57 merged in plus all of M58; (4) the r6-style "paid, no unit" windows are unexplained.

**Next pick (M59): the queue truth.** Instrument `FUN_004ef5d0`'s affordability call
`0x5a73f0(head, owner, base_index)` and the slot array (`+0x50..+0x74`) against `pending`
(`+0x4c`), and answer what actually gates the next production; only then can the gate's
arrival/queue floors be stated so that a 10-boundary UI-queued run passes.

## Session 98 (2026-10-26) — M59: **THE QUEUE TRUTH IS THE HEAD SLOT, NOT PENDING.** `pending` gates only the POP; the pay block dominates the create, and a base with an EMPTY queue still buys the head's type every round it can pay. The acceptance printed **PASS** on one real invocation.

**Static, from the instruction bytes (scratch/m59/queue_census.py + scratch/m59/dom.py over
scratch/m574/text.txt).** In the per-base visit `FUN_004ef6d0`: income add `0x4ef7f6` → price gate
`0x4efa2c-0x4efa61` (`ebx = [base+0x50]` = the HEAD SLOT, `edi = 0x4e40a0(owner,1,-1) ×
0x5ac950(ebx, base, 0)`, `cmp [ecx+0x40], edi; jge 0x4efadc`) → pay `0x4efedd` → clamp
`0x4eff02-0x4eff23` → **create-unit call `0x5ab650(type, ?, x, y)` @ `0x4eff4e`**, guarded at
`0x4eff32` by `[base+0x10] == 0`. A dominance test (block-level CFG, pay block removed) prints
`entry->create: True / with the PAY block removed: False` and the same for gate→create: the pay
DOMINATES the create. Nothing between them reads `+0x4c`. The pop `FUN_004ef5d0` returns at
`0x4ef5f4` (`je 0x4ef684`) when pending == 0 and is called LATER in the same visit
(`0x4f037b`, `0x4f0f46`; the third site `0x4ef992` is NOT reachable from the pay) — it only
left-shifts the slots and decrements pending + the per-faction queued-count byte
`[0x94de84 + owner*0x20bc + type*4]` (`0x4ef613`, `dec BYTE PTR [ecx]`).

**NAMED.** `0x5a73f0(type, owner, base)` = "can this faction field this unit type here": needs
the type-record flag `[+0x30] & 1`, the owner NOT in the exclusion dword `[+0x2c]`, and the
required facility/project `[+0x32]` either −1 or researched-and-owned; types ≥ 0x40 are
faction-specific (`(type>>6) == owner`); the shared tail also rejects plan `[+42] == 8` when
`0x985ac4 & 0x400000`, and rejects when the class byte `[+0x24]` indexes `[0x92ae81] == 1` and
`0x4e4620(base_x, base_y, 0) == 0`. `0x5a6e70(-id, owner, base, 0)` is the same question for a
facility/project queue item (queue stores those NEGATIVE). `FUN_004e47d0` (called from
`0x4ccbdd`/`0x59d894`/`0x5a01f8`) initialises a base: zeroes `+0x30`, `+0x34`, `+0x3c`, `+0x40`,
`+0x4c`, sets `+0x38` from `[faction+0x94d600]`, then calls `FUN_004e46f0(base)` which picks the
cheapest-scored buildable unit type into the HEAD SLOT ONLY (`[+0x50]`, `0x4e471b`/`0x4e47bb`,
pending untouched — this is why a founding leaves head 2 with pending 0). `FUN_004e5560(base,
new_head)` writes the head and adjusts the per-faction queued-count byte (`dec` old at
`0x4e55b5`, `inc` new at `0x4e55dd`). `FUN_004e5ae0(base, 0)` — called SIX times from the visit,
first at `0x4ef87e` BEFORE the gate — refreshes the head through the chooser `0x4f6030` for any
owner not in the human mask, or when `+0x38`'s sign bit is clear, or (always, at this call site)
when param_2 == 0. Pending is written at only four absolute sites: `0x4e4982` (init), `0x4ef642`
(pop), `0x50890d`, `0x543b26` (clear).

**Measured in memory, one variable, internal control (`scripts/m59_head.py`, box at 2174, no
tracer, all our units held first):** `POKE 'Korolev Center' idx 17 +0x40: 0 -> 9 (read back 9)
OK`; one turn later Korolev minerals `9 -> 0` (exactly the derived price 9), income `0 -> -1`
(the new unit's upkeep), **pending 0 -> 0**, head 2 -> 2, and the base tile went 5 -> 6 units of
(type 2, owner 3); control University Base idx 0 (minerals 0, gate not passed) stayed 0 minerals
and 6 -> 6 units. A base with an EMPTY queue buys the head slot's type.

**Rule restated** (`predict()` in `scripts/m56_build.py`): arrival iff the base is OURS
(`0x91b5b4`; another faction's head is re-picked by its own visit at `0x4ef87e` before its gate,
so it is not predictable — enemy arrivals are still REPORTED by F2) AND the head is a unit type
(0..0x3f) AND the owner is in the mask AND `storage (+ income) >= price`. Pending is not a term;
`pop_expected` replaces it as the pop predictor. Bookkeeping now covers pending-0 bases (a paid
pending-0 base must leave pending 0 and the slots unchanged — the pop cannot fire) and PAIRS BY
NAME, not index (mid-run the array compacted Korolev 18 -> 17 again). F1 verifies an arrival in
the pay window OR by the next window's before-snapshot, because the create was measured landing
in the snapshot gap (run `..._144801` r2: pay 8 -> 1 with pending still 1 at both snapshots, our
unit total 6 at r2-after -> 7 at r3-before, r3's own window adding nothing).

**ACCEPTANCE — PASS on one real invocation.**
`python3 scripts/m56_build.py --ui-queued 17 --boundaries 10 --timeout 400 --no-poke-hold`
(queue filled by the GAME's BUILD UI via `scripts/m57_ui_enqueue.py --base-index 17 --cell-item 2
--inserts 1`, units held by `m59_head.py --stage read --hold` first, minerals 8 < price 9 at
start) -> `PASS production prediction: 1 verified unit arrivals over 10 boundaries, every
prediction and every observed arrival accounted, queue bookkeeping exact — queue filled by the
GAME's BUILD UI (0 memory writes), paid by income at 1/round`; 50 `ok` checks, 0 BAD;
`r0 prediction base 17 (29,42) type 2 — predicted (pending 1, minerals 8 >= price 9); observed
net 1`; `boundaries observed >= 2 — 10 of 10 rounds flipped`; `POSITIVE prediction verified —
1/1`; `memory writes: 0`. Trace `evidence/trace_m56_build_20261026_145157.jsonl`. Rule cases
`python3 scripts/test_m56_predict.py` -> `PASS 17/17` (cases 5/6 restated for the new scoping,
14-17 added for the pending-is-not-the-gate rule); bad fixture
`python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit 1 (BAD minerals
identity 100 + 0 - 10).

**Two runs did NOT pass before it, and no floor was weakened:** `..._144801` (10/10 boundaries,
2 positive predictions, 1 verified — the r2 deferral above, which is what forced the F1 window
change) and `..._145103` (1/1 positive verified, 10/10 boundaries, single BAD = the known r2
walk-home race `cur_player before 3 after 6`, which the footing says to re-run rather than
edit).

**Open.** (1) the create guard `[base+0x10] == 0` at `0x4eff32` is unread — what writes it, and
whether it is the reason a paid window can show no unit; (2) `FUN_004f6030` (the chooser, called
with a budget argument from `0x4e5ae0`) is unnamed — it decides what an AI base builds next and
therefore what its head slot will be; (3) the deferral window is a snapshot-timing fact, not yet
a timed model (the create's exact place in the round sequence is still inferred); (4) the older
skill note `0x94dc84` vs the disasm `0x94de84` for the queued-count byte is REPORTED, unresolved;
(5) enemy-base production is reported, never predicted.

**Next pick (M60): name `0x4f6030` and the `[base+0x10]` create guard.** With those two, the
arrival rule can be stated for other factions too (their head is whatever `0x4f6030` picks) and
the "paid, no unit" windows get a mechanism instead of a deferral.

## Session 99 (2026-10-26) — M60: **THE CREATE GUARD IS A PROCESS GLOBAL, NOT A BASE FIELD — and a nonzero guard really does make a paid window produce no unit. The chooser is named. The "snapshot GAP" was an EARLY READ, not a slow create. ACCEPTANCE PASS on one real invocation.**

changed `scripts/m60_guard.py` (NEW: read / poke / hw-watchpoint on `0x8f0d70`, plus our bases'
minerals, `+0x98` mirror, `+0x30` flags, `+0x38` plan dword and per-tile unit count),
`scripts/m56_build.py` (every sampled timeline row now carries `guard = [0x8f0d70]`; PASS asserts it
stayed 0 — a check ADDED, none weakened), `evidence/m60w_watch.gdblog` + `evidence/m60c.gdblog` +
`evidence/m60d.gdblog` (watchpoint and store-tracer transcripts),
`evidence/trace_m56_build_20261026_153930.jsonl` (the PASS run), this file, `NEXT_PROMPT.md`,
skill `references/production-queue.md`.

**THE GUARD — the footing was wrong twice.** 0x4eff32 is `a1 70 0d 8f 00` = `mov eax,ds:0x8f0d70`,
then `85 c0` / `75 21` = `test eax,eax; jne 0x4eff5c` — a process-global read, NOT `[base+0x10]`.
Base record `+0x10` holds 0x4b000000 (Korolev) / 0x55000000 (University): not a flag.
`grep -c 0x8f0d70` over the whole `.text` dump (40,900,318 B) is **1** — this read — while its
neighbour 0x8f0d60 (the current-base pointer) has 929 references and 0x8f0d64/68/6c are written.
`python3 scripts/m60_guard.py --stage watch --boundaries 2 --timeout 180 --tag m60w` ->
`"guard_writes": 0, "writers": {}, "visits": 53, "guard_values_at_visits": ["0"]` — a hardware
watchpoint saw no writer across 2 boundaries, value 0 at every one of the 53 base visits.

**POKE, one variable, University as control (minerals 4 < price 9, so it cannot pay).**
- guard 1: `python3 scripts/m60_guard.py --stage poke --value 1` -> `POKE 0x8f0d70 (create guard):
  0 -> 1 (read back 1) OK`; `python3 scripts/m59_head.py --stage poke --base 'Korolev Center'
  --minerals 9 --hold` -> `+0x40: 0 -> 9 (read back 9) OK` (`poke_hold: 0 units poked,
  all_held=True` — all 10 were already order 2); `python3 scripts/smac_play.py --turns 1 --timeout
  200 --no-escape 3000 --orders-per-turn 1 --verbose --tag m60a` -> `turn 0: 2182->2183 OK`;
  read back: Korolev minerals **9 -> 0 (the pay ran)**, our unit count **10 -> 10 (no unit)**,
  guard reads 1, University 4 -> 4.
- guard 0: `--stage poke --value 0` -> `POKE 0x8f0d70: 1 -> 0 (read back 0) OK` (it had stayed 1
  through the whole previous turn — nothing wrote it); minerals re-poked 0 -> 9; `smac_play ...
  --tag m60f` -> `turn 0: 2190->2191 OK`; once the player walk came home: Korolev minerals **0**,
  our units **10 -> 11 (the unit arrived)**, guard 0, `cur_player 3`.
The two runs differ in the guard value and in nothing else (same base, same minerals poke, all
units held). They are 8 rounds apart; the reads between them are the timing lesson below, not a
state effect.

**THE ROUND TIMING.** A read taken the instant the year flips can be EARLY. Runs `--tag m60c` and
`--tag m60e` poked 9, ran one turn and read immediately: minerals still 9, `+0x3c` unmoved,
`cur_player 7`, and a 100 s poll changed nothing; the pay and the create landed later in the same
round while the walk came home (`m60f`: minerals 0, ours 11, `cur_player 3`). The store tracer only
appeared to "cause" the pay by WAITING: `python3 scripts/m57_stores.py --base 'Korolev Center'
--boundaries 2 --timeout 220 --tag m60c` -> `VISIT#1 storage=9 pend=0 head=2` /
`STORE#1 pc=0x4ef7f6 site=visit.income-add before=9 src=9` /
`STORE#2 pc=0x4efedd site=visit.pay-minus-edi before=9 src=0` and
`per-boundary net changes: ['2184->2185=-9', '2185->2186=0']` PASS (same shape for `--tag m60d`).
`m56_build` already closes every window on `cur_player` coming home, so its windows are the valid
ones; M59's "the create landed in the snapshot GAP" is this effect, named.

**THE CHOOSER NAMED.** `0x4f6030` = what a base builds next: it scores candidates and keeps the
MINIMUM against `local_124[0]` (seeded `0xf423f` = 999999, tie broken by a secondary key), score =
cost × ~25 halve/double heuristics, and it REJECTS a candidate unless `[base+0x38]` carries the bits
its category requires — the switch on `record[+0x32]` at `0x4fb4xx`: 0 -> 0x200, 1 -> 0x1000, 2 and
3 -> 0x1000 (0x400000 when `[base+0x38] & 0x1000` is clear or `record[+0x2c] != 0`), 4 -> 0x2000,
5 -> 0x800, 6 -> 0x400, 7 and 10 -> 0x800000, 8 -> 0x20000, 9 -> 0x8000, 0xb -> 0x100000, plus
0x80000 for faction-specific types (>= 0x40) whose `record[+0x38] & 4` is clear — and that gate runs
only for owners IN `0x985b10`. Fallback `0x4fd6a0-0x4fd6e5`: scan the 512 type records at `0x98ad80`
stride `0x34` (end `0x9915b2`), keep the `0x5a73f0`-buildable ones with category 1/2/3 and
`record[+0x38] & 4`, take the lowest `record[+0x31]`. Korolev's `[base+0x38] = 0x00dfbe41` carries
0x1000, so Scout Patrol (category 3) passes. **The Ghidra gotcha that caused the old wrong note:**
`DAT_008f0d60` is typed `short *`, so pseudocode `+0x1c` is BYTE `+0x38` — proved by `0x4fb293 mov
ecx,ds:0x8f0d60` / `0x4fb299 test DWORD PTR [ecx+0x38],0x80000000`.

**ACCEPTANCE — PASS on one real invocation.** Setup: `SMAC_SAVE='m54b_clean.SAV' python3
scripts/m54a_load.py --relaunch` (HUD reached, `difficulty level: talent`) -> `python3
scripts/m54g_prep.py` -> `python3 scripts/smac_play.py --turns 1 ... --tag t` (`Korolev Center
founded in 2150`) -> `python3 scripts/m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1`
(`after INSERT 1 (try 1): pending=1 head=2 slots=[2, 2, 2, 0, 0, 0] minerals=5 d0=2`) -> `python3
scripts/m59_head.py --stage read --hold` (`poke_hold: 6 units poked, all_held=True`) ->
`python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold` ->
`PASS production prediction: 1 verified unit arrivals over 10 boundaries, every prediction and every
observed arrival accounted, queue bookkeeping exact — queue filled by the GAME's BUILD UI (0 memory
writes), paid by income at 2/round`; **53 checks, 0 bad**; `boundaries observed >= 2 — 10 of 10
rounds flipped`; `at least 1 POSITIVE prediction verified — 1/1`; `create guard ds:0x8f0d70 read 0
in every sampled row — 5534 sampled rows, values [0]`; `memory writes: 0`. Trace
`evidence/trace_m56_build_20261026_153930.jsonl`. Rule cases `python3 scripts/test_m56_predict.py`
-> `PASS 17/17 production-prediction cases`; bad fixture `python3 scripts/m56_build.py --fixture
scratch/m56_fixture_bad.json` -> exit 1.

**One earlier run did NOT pass and no floor was weakened:** `..._153623` (58 checks, 3 bad) failed
on `r1 boundary: player walk came home to us after the flip — cur_player before 3 after 0` (the
known harness race — the footing says RE-RUN, do not edit the floor), which made the r2 window span
TWO rounds (`kor: 6 -> 1` = 6 + 2 + 2 − 9), so r2's "unexplained ORDER-0 arrival" and
`pending 1->0` were the missed round's events, not a model gap. Its trace was deleted after the
numbers were recorded here (evidence is 29.7 MB of the 30 MB gate).

**Open.** (1) the chooser's ~25 score terms are named as a SHAPE, not enumerated — an enemy base's
head is still reported, never predicted; (2) base record `+0x10` (0x4b000000-style) is still
unexplained — it is NOT the guard; (3) the failure path `0x4eff5c` (shared by a guard-skip and by a
negative return from `0x5ab650`; prints through `0x406720`) and its effect on the rest of the visit
is unread — note `0x5ab650` has exactly ONE negative return, the `n_units > 0x7ff` cap, and n_units
was 96-108, so our paid windows were never cap-blocked; (4) the older reported conflicts
(`0x94dc84` vs `0x94de84`; pay `0x4f0ca6` vs `0x4efedd`) stay unresolved; (5) a writer for
`0x8f0d70` outside `.text` (a save loader, another section) is not excluded — the watchpoint covers
runtime only.

**Next pick (M61): pin the create's place in the round sequence and drop the deferral fudge.**
Record `(cur_player, visit, pay, create)` tuples across boundaries — `m60_guard --stage watch`
already prints the guard at every visit; extend it to stamp the walk position, the `0x4efedd` pay
and the `0x4eff4e` create — so the round sequence says exactly where our visit sits relative to the
year flip and to walk-home, `m56_build`'s F1 "OR by the next window's before-snapshot" branch
becomes a measured position instead of a tolerance, and `predict()` can state the arrival round
exactly. Second half of M61: say what base record `+0x10` is (it is not the guard, and it is not
zero).

## Session 100 (2026-10-26) — M61: **THE CREATE IS IN THE SAME VISIT AS THE PAY, THE ROUND ORDER IS MEASURED, AND `base+0x10` IS THE BASE NAME. ACCEPTANCE PASS on one real invocation.**

**THE ROUND ORDER, read out of one ordered stream.** `python3 scripts/m60_guard.py --stage watch
--boundaries 2 --timeout 400 --tag m61a` (the watch stage was extended this session: conditioned
breakpoints on the visit `0x4ef6d0`, the pay store `0x4efedd` and the create call `0x4eff4e`,
hardware watchpoints on the guard `0x8f0d70`, the year `0x985b00` and `cur_player` `0x985dcc`, each
command list `silent` + tagged printf + `continue`, gdb stdout straight to a file) ->
`events {"YEARW": 2, "PLAYERW": 16, "VISIT": 52, "PAY": 8, "CREATE": 8, "GUARDWRITE": 0}`,
`events_at_our_bases {"Korolev Center/VISIT": 2, "Korolev Center/PAY": 1, "Korolev Center/CREATE": 1,
"University Base/VISIT": 2}`, `visits 52`, `guard_values_at_visits ["0"]`, `guard_writes 0`,
`turn_rcs [0, 0]`. One round of `evidence/m61a_seq.jsonl` (`evidence/m61a_watch.gdblog`):

```
== YEAR FLIP to 2183 (round 83) while cur_player=7
   cur_player -> 0 -> 1 -> 2 -> 3
y2183 r83 cp3 VISIT  University Base   min=6 pend=0 head=2 guard=0
y2183 r83 cp3 VISIT  Korolev Center    min=9 pend=0 head=2 guard=0
y2183 r83 cp3 PAY    Korolev Center    9->0 (edi=9)
y2183 r83 cp3 CREATE Korolev Center    min=0
   cur_player -> 4 -> 5 -> 6 -> 7
== YEAR FLIP to 2184 (round 84) while cur_player=7
```

The year store is `0x51f54f` (`a3 00 5b 98`, right after the round store `0x51f53c`); NAMED.md's
"the year store `0x51f554`" is the `call 0x478530` AFTER the store — reported conflict, bytes win.
Our bases are visited while `cur_player == 3`, in ARRAY order (University idx 0, then Korolev idx
18), four player switches after the flip, in the round whose year has just flipped. The pay and the
create are ONE visit invocation: `grep -n '0x4efedd\|0x4eff32\|0x4eff4e' scratch/m574/text.txt`
returns only the three instruction addresses plus the `jne 0x4eff5c`, so no control flow enters
that block from elsewhere, and the log prints PAY then CREATE with nothing between. **An arrival is
never a round late — a snapshot can be early.** Setup for that run was ONE variable:
`m59_head.py --stage poke --base "Korolev Center" --minerals 9 --hold` -> `POKE ... +0x40: 0 -> 9
(read back 9) OK`, `poke_hold: 0 units poked, all_held=True`, armed before attaching. The first
run's CREATE line printed `guard=3`: at `0x4eff47` eax holds `[ebp-0x28]`, which `0x4ef71a` set
from `BYTE [eax+4]` — the base OWNER byte, not the guard; the printf now reads the global and
prints `owner=` separately.

**F1 IS ATTRIBUTED, NOT TOLERATED.** `ds:0x8f0d60` names the record the round processor is visiting
(`0x4f5a70` stores it per base before the pipeline that reaches `0x4ef6d0`), so it says which base
has been reached. `m56_build.py` now reads it at every after-snapshot (`cur_base()`, logged as
`cur_base` in the `round_after` event and carried in `rounds[r]["cur_base_after"]`) and REFUSES the
deferral when that pointer already named the predicted base — the visit had run, so a still-missing
arrival is a model gap. Run-layer fixtures built from the real PASS trace by
`scratch/m61/mkfix.py` (they differ in that ONE field): `python3 scripts/m56_build.py --fixture
scratch/m61/fixture_defer_ok.json` -> **exit 0**, `PASS production prediction: 1 verified unit
arrivals over 2 boundaries ...`; `python3 scripts/m56_build.py --fixture
scratch/m61/fixture_beat_visit.json` -> **exit 1**, `BAD r0 prediction base 18 (29,42) type 2 —
... NOT deferred: at the after-snapshot ds:0x8f0d60 already named this base, so its visit had run
and the predicted arrival really was absent`. Fixture timelines now also replay the guard samples
(the guard floor cannot be vacuously true on a replayed run).

**`base+0x10` IS THE NAME, NOT A FLAG.** The base name starts at record byte **+19** (NAMED.md
`base_array` row, `M.parse_base`), so a dword read at `+0x10` is bytes +16, +17, +18 (three small
unnamed bytes) plus the name's FIRST CHARACTER in the top byte. Census
`python3 scratch/m61/census10.py` over all 24 live bases: `topbyte==name[0]: 24 / 24` — Korolev
Center `0x4b000000` = 'K', University Base `0x55000000` = 'U', both with +16..+18 = 0; the other 22
have small values there (e.g. People's Endeavor +16=1 +17=5 +18=2, Fallow Time +16=4). +17 == 1 on
all 8 faction-6 bases and +18 is nonzero on several faction-2/7 bases — an OBSERVATION, unnamed.
The old `[base+0x10] == 0` guard note was wrong twice over: Ghidra's `short *` offsets, and this
straddle.

**THE PAY SITE CONFLICT RESOLVES TO `0x4efedd` for this shape.** The live PAY stamp reads
`before=9 edi=9 after=0` with the derived price 9 (`m58_price.py --owner 3 --type 2` -> `DERIVED
price = factor_tenths 9 * type_cost 1 = 9`), immediately before the create. The `0x4f0ca1/0x4f0ca6`
site in NAMED.md's "completion path" is a different branch of the same function and is still unread.

**ACCEPTANCE — PASS on one real invocation, with the PATCHED script.** Reload recipe
(`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> HUD, `difficulty level:
talent`) -> `m54g_prep.py` -> `smac_play.py --turns 1 ... --tag m61t` (`Korolev Center founded in
2150`, `turn 0: 2150->2151 OK`) -> Korolev located BY NAME (idx 18, minerals 2, income 2) ->
`m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1` (`after INSERT 1 (try 1): pending=1
head=2 slots=[2, 2, 0, 0, 0, 0] minerals=2 d0=2`) -> `m59_head.py --stage read --hold` (`poke_hold:
6 units poked, all_held=True`) ->

`python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold` ->
**`PASS production prediction: 3 verified unit arrivals over 10 boundaries, every prediction and
every observed arrival accounted, queue bookkeeping exact — queue filled by the GAME's BUILD UI (0
memory writes), paid by income at 2/round`**, **56 checks, 0 bad**; `boundaries observed >= 2 — 10
of 10 rounds flipped`; `at least 1 POSITIVE prediction verified — 3/3`; `create guard ds:0x8f0d70
read 0 in every sampled row — 18619 sampled rows, values [0]`; `memory writes: 0`; `completion NOT
armed: minerals 4 < price 9`. Trace `evidence/trace_m56_build_20261026_162511.jsonl`. Read back in
memory after the run: ours **6 -> 9**, Korolev minerals 3, pending 0, head 2, guard 0. No deferral
was needed (no `ATTRIBUTED` line in the log). An earlier PASS the same session, with the
pre-patch script and the same UI shape, printed `PASS ... 1 verified unit arrivals over 10
boundaries` with **51 checks, 0 bad** (`evidence/trace_m56_build_20261026_160325.jsonl`): in that
trace the arrival is inside window r0 (ours 9 -> 10, Korolev tile 4 -> 5) — F1's deferral was not
exercised there either.

**Rule cases.** `python3 scripts/test_m56_predict.py` -> `PASS 17/17 production-prediction cases`;
`python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> exit 1; plus the two new
fixtures above.

**Open.** (1) The pop did NOT visibly left-shift Korolev's slot array while pending went 1 -> 0
(`slots [2, 2, 2, 2]` at r0 and at r1 of `trace_m56_build_20261026_160325.jsonl`) — the documented
"left-shift + pending--" is unverified for the slot array. (2) What writes base bytes +16/+17/+18
is unknown (no runtime watchpoint was armed on them); the dword-level answer is settled. (3) The
failure path `0x4eff5c` (guard-skip and the `0x5ab650` cap share it) is unread. (4) The chooser's
~25 score terms are still a shape, not an enumeration — enemy heads stay REPORTED. (5) The harness
could close its window deterministically after our upkeep (the walk leaving our slot, or
`ds:0x8f0d60` naming our last base) instead of polling on `cur_player == 3`; the deferral is now
attributed but the window race itself is still open. (6) A writer for `0x8f0d70` outside `.text` is
still not excluded. (7) The queued-count byte conflict (`0x94dc84` vs `0x94de84`) is untouched.

**Harness lessons.** A dialog left on screen swallows every UI click: `m57_ui_enqueue` failed twice
on University Base with `INSERT never landed` because an Operations Director "the minerals output of
Korolev Center is not sufficient to support Scout Patrol ... the unit has been disbanded" dialog
(`classify()` == `dialog`) was over the BUILD pane; Return cleared it, one Escape closed the pane.
And producing a unit zeroes the base's mineral credit (`+0xd0` 1 -> 0 or -1) while the income add is
gated `d0 > 0`, so both our bases sat at minerals 0 / credit 0 and no positive prediction was
possible — the reload was the fix, not a poke.

**Next pick (M62): what the POP actually does to the queue slots.** Pending went 1 -> 0 with the
slot array unchanged; arm `m60_guard --stage watch`-style breakpoints on the pop `FUN_004ef5d0`
(`0x4ef5f4` gates pending == 0, the shift/pending store, the `0x4ef613/0x4ef641 stores) and on the
slot dwords `base+0x50..0x74`, run over 2-3 boundaries with a queued base, and state from the
stores what the queue's representation really is — then re-check M59's "the head slot is the truth"
against it. Acceptance stays `m56_build.py --ui-queued <idx> --boundaries 10 --timeout 400
--no-poke-hold` printing PASS on one real invocation.

## Session 101 (2026-10-26) — M62: **INSTRUMENTS, NOT RESEARCH. The box's dead shapes are now decided in one read, the brief is generated, and the evidence audit found that no trace could ever count as cited. NO prediction PASS this session — the one live run FAILED and the reason is now half-explained.**

**THE READINESS ORACLE (`scripts/accept_ready.py`, 15/15 unit cases).** Read-only; exit 0 = one of
our bases can carry the UI-queued acceptance, exit 1 = BLOCKED with the single cheapest fix, in
this order: screen class (a modal swallows every click AND every turn-end key) -> running gdb ->
evidence headroom (29 MB) -> per base `pending > 0`, `minerals < price`, `credit > 0` (the income
add is gated `d0 > 0`, so `credit <= 0` never accrues) -> TIGHT horizon when the gate is more than
`boundaries-2` rounds away. Proven on the live box in three states, one command each:
`BLOCKED … FIX: screen is 'dialog': press Return …` (an Operations Director "…not sufficient to
support Scout Patrol…" modal was up and had just swallowed two enqueues) -> `BLOCKED … FIX: enqueue
on University Base (idx 0)` -> after `m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1`
(`after INSERT 1 (try 1): pending=1 head=2 minerals=1 d0=1`) -> **`READY … RUN: scripts/m56_build.py
--ui-queued 0 --boundaries 10 …`, exit 0**. Rule cases: `python3 scripts/test_accept_ready.py` ->
**`PASS 15/15 readiness cases`**.

**THE LIVE RUN FAILED — recorded, not hidden.** `python3 scripts/m56_build.py --ui-queued 0
--boundaries 10 --timeout 400 --no-poke-hold` -> **FAIL**, `positive predictions 1/2 verified;
boundaries 10/10`, exit 1 (`evidence/trace_m56_build_20261026_165917.jsonl`). Three rows carry it:
r2 "predicted … observed net 0 of that tuple on the base tile"; r3 `pending 1 -> 0` with the slot
array `[2,2,0,0]` unchanged; r4 "queue held — head 2->384" while a second base read `386` in the
same window. Across every trace, **38/303** of our rows and **2804** rows overall hold a slot
outside `0..23` — so a queue slot is NOT reliably a type id and no global floor may demand it. The
run also lost University Base (`bases_ours` 2 -> 1, `units_ours` 9 -> 5); base death and the queue
anomaly share the same windows, so this is **CONFOUNDED**, written as such in NAMED.md.

**A LATENT BUG IN THE GATE'S CITATION CHECKER.** `evidence.load_cites()` matched
`png|log|gdb|txt|json|csv` — not `.jsonl` — so **no trace could ever count as cited**, and the
alternation order (`json` before `jsonl`) hid the first fix. After both fixes the audit reports
10 uncited files / 0.1 MB where it had claimed 578 files / 12.7 MB. New command
`python3 scripts/evidence.py audit [--delete]` (cites = docs AND `scripts/*.py`, so classifier
frames are safe): **deleted 396 uncited files, 27.7 -> 22.8 MB**, and `test_classify.py` still
**PASS 17/17** afterwards.

**FIXTURE TRACES NO LONGER POLLUTE EVIDENCE.** `m56_build.py --fixture X` writes to `$TMPDIR`
(`scratch/fixture_trace_*.jsonl`); evidence jsonl count 174 before and after the three fixture
cases (`defer_ok` 0, `beat_visit` 1, `bad` 1).

**THE BRIEF IS GENERATED (`scripts/session_brief.py`, ≤4 KB, `--write` -> `BRIEF.md`).** Verdict +
both bases + the tagged CONFLICTs + next pick + first commands + uncited evidence. `NAMED.md` now
carries three **`CONFLICT:`** lines (year store `0x51f554` vs `0x51f54f`; queued-count byte
`0x94dc84` vs `0x94de84`; pay `0x4f0ca6` vs the measured `0x4efedd`) which the brief prints
verbatim. Measured on the 125B for the fixed-cost argument: **596 tok -> 1.83 s prefill, 44,446 tok
-> 15.4 s** (0.345 ms/token) — the footing's size is not the problem, stumbling is.

**Open.** (1) What writes 384/386 into `+0x50` (two bases in one window). (2) Whether a dead/stale
base record is what those reads are. (3) The pop's real operand — pending decrements, slots do not
move, in two independent sessions now. (4) The support-disband path can eat a created unit, so
READY ≠ PASS (not modelled). (5) Box drifted: 1 base, 5 units, year 2174 r74 — reload before the
next acceptance. (6) `session_brief.py` prints only the FIRST line of each multi-line CONFLICT (the
wrapped continuation lines are not joined).

**Next pick (M63):** what writes 384/386 into `base+0x50`, and what the pop does to the slots —
reload first, then pop breakpoint + a watchpoint on one named base's `+0x50..+0x74`, two-three
boundaries, one variable per run.

## Session 102 (2026-10-26) — correction to Session 101

The readiness oracle has **15** unit cases, not 13: two horizon cases (`tight horizon is flagged`,
`roomy horizon is not`) were added after the session-101 notes were written, so the notes quoted a
stale count. `python3 scripts/test_accept_ready.py` -> `PASS 15/15 readiness cases` (re-run before
this commit). No code changed; `SESSION_NOTES.md` and `NEXT_PROMPT.md` now say 15/15.

## Session 104 (2026-10-26) — M64: THE ACCRUAL PHASE IS MEASURED AND AN ARRIVAL IS ATTRIBUTED BY THE PAYMENT, NOT BY `ds:0x8f0d60`. ACCEPTANCE PASS on two real invocations.

Branch `milestone/m64` off `origin/main` (`5c18670`, M62B #61). Session 103's M63 work is still
**unmerged** on `milestone/m63`, so this branch does not carry its instrument or its `NAMED.md`
edits; the two traces its findings rest on were copied forward (`git checkout milestone/m63 --
evidence/trace_m56_build_20261026_181701.jsonl evidence/trace_m56_build_20261026_182354.jsonl`)
because the gate's citation check requires cited paths to resolve in the tree.

### What changed (harness only — no threshold, floor or economic term moved)

`scripts/m56_build.py`:
- **`accrual_phase(bases_now, prev_after)`** — a window's after-snapshot and the next
  window's before-snapshot are the SAME ROUND read twice, and the engine plays in the gap, so a
  minerals delta of exactly `+0xd0` between them IS this round's add (0x4ef7f6). `predict()` now
  takes `accrued=` (names) and adds income only when the add has not already landed; every
  prediction row carries `income_added` / `accrued_already`, and every window logs an
  `accrual_phase` event with `prev_after / before / gap_delta / income / already_accrued`.
  This is the fix for session 103's run-2 FAIL (`8 + credit 1 - price 9 = 0, observed 8`): in
  `evidence/trace_m56_build_20261026_181701.jsonl` Korolev Center read 7 at r1-after and 8 at
  r2-before (income 1), so the old `income_first=True` double-counted and predicted a payment at
  r2 that never happened (storage 8 -> 8); r3 is where it really happened (8 + 1 - 9 = 0).
- **F1 attributes by the PAYMENT, not the pointer.** An arrival missing from the after-snapshot is
  accepted when this window's minerals show the payment (`after == before + credit - price`) AND
  the unit reads back — either from a same-round re-read of the unit array (new
  `arrival_reread` event, bounded 2 s, stops the instant the year changes) or from the next
  window's before-snapshot, which is that same round read later. `ds:0x8f0d60` is reported in the
  detail and used as evidence by nothing: it was measured insufficient (r7 of
  `evidence/trace_m56_build_20261026_182354.jsonl` paid 7 -> 0 with the pointer naming Korolev
  Center and 2 of our units on (29,42); r8's before-snapshot, same round y2159 rnd59, has 3).
  The re-read compares **counts**, not key presence — a garrison of the same `(x,y,type,owner)`
  already sits on the base tile, so "the key is in the snapshot" says nothing.
- **New floor, not a weakened one:** the gap between a window's after-snapshot and the next
  window's before-snapshot is now searched for unexplained ORDER-0 arrivals on our bases too
  (`rN gap to the next window: ...`), because F2 diffs before -> after only and the attribution
  above moves arrivals into that gap.
- `credit_of` is computed once per window (0 when already accrued) and shared by the attribution
  and the F3 mineral identity, so the two cannot disagree.

`scripts/test_m56_predict.py` -> **`PASS 19/19 production-prediction cases`**: case 18 is the
measured already-accrued snapshot (ONE variable, the accrued set: gate 8+1=9 ARRIVES vs gate 8
does not); case 19 pins `accrual_phase` on the measured pairs (7->8 with income 1 = the add;
8->8 = not yet; +1 with income 0 = not the add, the add is gated `d0 > 0`; +3 with income 2 =
unmeasured, so the income term stands rather than guessing).

`scripts/m64_mkfixture.py` (new) rebuilds the run-layer fixtures from committed traces:
`python3 scripts/m56_build.py --fixture scratch/m64/fixture_paid_readback.json` -> **exit 0**
(r7+r8 of the run-3 trace VERBATIM — the window pair session 103 failed on);
`--fixture scratch/m64/fixture_paid_no_readback.json` -> **exit 1** (same two windows, the paid
unit absent from every read: a paid window whose unit never reads back is the guard shape, not a
race); `--fixture scratch/m61/fixture_defer_ok.json` exit 0, `--fixture scratch/m56_fixture_bad.json`
exit 1, `test_walk_diff.py` 37/37, `test_classify.py` 17/17, `check_classes.py` 17/0.

### CONFLICT reported, not silently picked

The pick said "keep `scratch/m61/fixture_beat_visit.json` failing (exit 1)" AND "a paid window
whose unit appears only in the NEXT read must verify". Its own new rule makes that impossible:
the original beat_visit IS a paid window whose unit appears only in the next read (r0 minerals
8 -> 0 with income 1 and price 9, unit present at r1's before-snapshot) and its only discriminator
was the pointer, which session 103 measured insufficient. Under the new rule it **passes**
(`--fixture scratch/m61/fixture_beat_visit.json` -> exit 0 with the M61 file). Rather than keep a
green file named "must fail", `scripts/m64_mkfixture.py` rebuilds it in place — same path, same
expectation, new discriminator (the paid unit removed from every read) -> **exit 1**. The pointer
value is kept in the data and no longer means anything.

### The acceptance — two real invocations, both PASS, plus the read-backs

1. `python3 scripts/m56_build.py --ui-queued 18 --boundaries 10 --timeout 400 --no-poke-hold`
   (after `SMAC_SAVE='m54b_clean.SAV' scripts/m54a_load.py --relaunch` -> `m54g_prep.py` ->
   `smac_play.py --turns 1` -> `2150->2151 OK` (`evidence/trace_t_20261026_194949.jsonl`) ->
   `m57_ui_enqueue.py --base-index 18 --cell-item 2
   --inserts 1` -> `pending=1 head=2 slots=[2,2,0,0,0,0] minerals=2 d0=2`) ->
   **`PASS production prediction: 2 verified unit arrivals over 10 boundaries ... queue filled by
   the GAME's BUILD UI (0 memory writes), paid by income at 2/round`**, `ACCEPT_EXIT=0`,
   52 checks all ok, `positive predictions 2/2 verified; boundaries 10/10`,
   `evidence/trace_m56_build_20261026_195136.jsonl`. **Read back:** Korolev Center paid at r3
   (minerals 8 -> 1 = 8 + 2 - 9) and at r7 (7 -> 0 = 7 + 2 - 9); our units on (29,42) went 1 -> 2
   -> 3, and WHERE each reads back is the whole point: the r3 payment's unit is NOT in r3's
   after-snapshot (tile still 1, orders [2]) and IS at r4's before-snapshot (tile 2, orders
   [0, 2]), while the r7 payment's unit is already in r7's own after-snapshot (tile 3, orders
   [0, 2, 2]). **The r3 arrival is the session-103 failure shape and it was ATTRIBUTED, not
   tolerated:** the check detail reads
   `observed net 0 of that tuple on the base tile; ATTRIBUTED ... this window's minerals show the
   PAYMENT (8 + credit 2 - price 9 = 1, read back) ... ds:0x8f0d60 named Korolev Center at the
   after-snapshot and is not evidence either way (measured insufficient)`. Under M61's rule that
   window FAILED the run.
2. The same command after the re-read was changed to compare counts (the only code change after
   run 1, so the shipped code is the code that printed PASS; its reload turn is
   `evidence/trace_t_20261026_195910.jsonl`, `turn 0: 2150->2151 OK`): -> **`PASS ... 2 verified unit
   arrivals over 10 boundaries`, `ACCEPT_EXIT=0`**, 56 checks all ok,
   `evidence/trace_m56_build_20261026_200045.jsonl`. Read back: payments at r3 (8 -> 1) and r7
   (7 -> 0), tile counts 1 -> 2 (r3-after, order 0 present) -> 3 (r7-after, order 0 present); both
   arrivals were observed directly, so no `arrival_reread` event and no attribution was needed.

**Said plainly:** in BOTH PASS runs every `accrual_phase` row had `gap_delta = 0`
(`evidence/trace_m56_build_20261026_200045.jsonl`: r1..r9 all `prev_after == before`), so the
accrual fix was **inert live** this session — it is exercised by cases 18/19 and by the replayed
run-2 trace, not by the acceptance. The attribution fix was exercised live exactly once, at r3 of
`..._195136.jsonl`. Two clean PASSes with the fix inert are not proof the accrual fix is right on
a live box; they are proof it does no harm there.

### Also measured this session (cheap, load-bearing)

- The box **stalls rather than auto-plays when an actionable unit exists**: year 2162 round 62
  `cur_player 3` unchanged across three reads 4 s apart (`n_units` 67 all three); three `Return`
  presses moved it 2162 -> 2164 and Korolev bought (minerals 5 -> 0, credit 2 -> 1). Session 103's
  "the box auto-plays while nothing drives it" is true only while nothing needs orders.
- `accept_ready.py`'s screen gate **flaked**: 8 consecutive `classify() == 'unknown'` verdicts on a
  frame that `vision_analyze` shows as the plain tactical HUD (MENU / COMMLINK / TURN COMPLETE /
  unit panel / `Mission Year 2164`), and 3 of 6 samples of the same screen classified `hud`
  (`scripts/smac_play.classify(words, region_colors(png), png)`). The map labels OCR as garbage
  (`UniversitKBratziew Center`) whenever the map is animating. Not a modal. The run itself was
  unaffected (it presses Return every 2 s whatever the screen says).
- Korolev Center's array index moved 18 -> 17 -> 18 again across the session; both enqueue
  attempts located it BY NAME and the `--base-index` passed to `m56_build.py` was re-read every time.

### Open

- Whether the accrual fix is right on a live box (see "Said plainly"): needs a run whose windows
  actually straddle an accrual — `income 1` bases (the 2164 box) produce that shape, the `income 2`
  reload does not.
- `accept_ready.py`'s screen gate is an OCR coin-flip on animated HUD frames; it blocked 14 reads
  this session and all 14 were the plain HUD. Either re-freeze until a known token reads, or stop
  treating `unknown` as a modal.
- Still open from M63 (untouched): which slot the BUILD UI's INSERT writes (needs an enqueue with
  two DIFFERENT type ids — every chooser value seen so far was 2); who writes `DAT_0068cbb0` and
  when it is stale; why `0x5a73f0(2, 3, Korolev)` returns 1.
- `milestone/m63` still carries the pop instrument (`m63_pop.py`), the `0x94de84` count-byte
  correction and the 384/386 identity-crossing finding with no PR. M64 did not merge it.
- Evidence 25.5 MB of the 30 MB gate FAIL line (warn band 20).

### Next pick

M65, cheapest first: (a) make `accept_ready.py`'s screen read re-freeze until a HUD token lands
instead of trusting one OCR pass (measured flake above; no game time needed), then (b) one run on
an `income 1` base — the shape that produced the double-count — so the accrual fix gets its live
case, then (c) the two-enqueue DIFFERENT-type-id test that finally says which slot INSERT writes.
