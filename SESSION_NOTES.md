

Older sessions: `docs/sessions/sessions-84-89.md` (6 sessions). Read it only when a question reaches back before session ## Session 90.

## Session 90 (2026-10-25) — M54k2: **THE HOOK-SHAPE RUN PRINTED PASS — and the two fixes it took: `queued_rescan` (the pump ran the WHOLE route inside our phase while the slot oracle read a stale record) and a year-poll after the order step (the auto-advance race recorded a +2 turn)** — changed `scripts/smac_play.py` (`queued_rescan` + wired into `_issue_order_once`'s pane loop after the blind Return; both order-step exits poll `year() != y0` at 0.2 s / 20 s cap before continuing), `scripts/test_walk_diff.py` (33 -> 37 cases), `ORDERS.md` §14, this file, `NEXT_PROMPT.md`, skill `references/terraforming-order-path.md`; new scratch (untracked): `m54k2_scan.py` (BFS-from-base tile scan: flag byte, parity, occupancy, enemy distance)

**ACCEPTANCE MET.** `python3 scripts/m54a_check_run.py evidence/trace_m54k2_run3_20261025_185036.jsonl --timeout 240 --min-our-bases 2 --min-moves 1 --min-own-base-arrivals 1` -> `PASS 6 turns advanced, year +1 each, no STUCK over 480s, per-turn state deltas present, 1 verified walks, 1 onto our own base, we still hold 2 bases` — `advanced 6/6`, year deltas `{1: 6}`, `stuck 0` (max dt 52.8 s), `actions {"pre-arm": 1, "orders": 2, ...}`, order mix `{"g->byte24": 1, "l->byte1": 1}`, `moves 1 LANDED of 5 ordered walks`, `t[35,36]->[29,42] mp+6` **ordered turn 1, LANDED turn 5**, `dest_is_own_base True`, counts [4,5]/[1,0], `bases_ours 2` at end (2204). Setup read back `actionable: []` + exactly one eligible held walker (`scratch/m54k_setup.py 29 42 35 36`); the HOOK armed it (`pre-arm:rec12`). Watcher (`scratch/m54k_watch.py 330 35 36`): (35,36) armed 2->0 at 2198 -> (34,37,24,6) -> mp re-zeroed 2200 -> (33,38) -> (32,39) -> (30,39) -> (30,41), byte 24 the whole way -> **(29,42) byte 0 at 2204** — Korolev Center. Nothing weakened; same floors as session 89.

**run1 was the documented negative INSIDE the milestone (fixed, not merged as-is).** The pane the `g` raised classified `unknown` x5, the blind Return answered the chooser, and the pump executed the whole 4-step route (34,37)->(32,39)->(30,39)->(30,41)->(29,42), byte 24 the whole way, `cur_player 3 tf2` — INSIDE turn 1's record: year deltas {1:5, 5:1}. Each flip compacted the array, so the modal loop's byte oracle (`UNIT_ARR + idx*52+17`) read a DIFFERENT record (byte 2) and the order recorded unverified -> `moves []` -> the checker could not score the arrival. `queued_rescan` now reads the queue off CONTENT: exactly one of ours newly wearing a wanted byte, none wearing it pre-press, its last leg naming OUR base (queue-time legs are the destination; a mid-walk rewrite names waypoint garbage — (61,9) in run1, (61,10) in session 89 — and a waypoint is not evidence). Tests 34-37 pin unique/fresh/base-leg; two fresh wearers, a prior wearer, a waypoint leg and a legs-less queue all say NOTHING. run3's `g` verified through exactly this path (pane `dialog`, `n_samples 0`, attributed True, confounded False, claim frm (35,36) to (34,37)).

**run2 proved the shape end-to-end and failed ONLY the cadence:** `g` verified 0->24 (chooser classified), carried turns 1-3, `landed True` turn 4 on our own base with the count delta firing — but turn 5 (post-arrival, everything HELD/SENTRY) recorded 2196->2198: the game AUTO-ADVANCES ~8 s/round once nothing is actionable, and the turn loop's next iteration costs a freeze+OCR (2-15 s), so TWO rounds flipped between its year checks. Checker: `FAIL year did not move +1 on turns [5]`. Fix: both order-step exits poll `year() != y0` at 0.2 s (20 s cap) before continuing — the flip is cheap to watch from memory. run3: {1: 6}.

**Also measured.** `turn_flags` gained a persistent 0x100000 bit around 2196 (1048578 at run3's end at 2204; the driver's `tf & 2` gates are unaffected — ORDERS §14). The tile scan (`scratch/m54k2_scan.py`) re-screens the target EVERY setup: the war closed the quiet window hard — best enemy distance near Korolev fell from 13 (2191) to 9 (2198); targets used: (34,37) bfs-3 edist 10 (run1), (36,39) bfs-3 edist 12 (run2), (35,36) bfs-3 edist 9 (run3, a tile session 89's run6 walker actually crossed). The box after run3: 2204, bases_ours 2, units_ours 11, n_bases 28, the arrived walker at Korolev, the war at our doorstep (enemy units within 9 tiles). Tests: `test_walk_diff.py` -> `PASS 37/37 attribution cases`; classifier gates untouched: `test_classify.py` 17/17, `check_classes.py` 17/0 (no new classes; `_3x.png` deleted; no new evidence frames — budget unchanged).

**Open.** (1) The 0x100000 turn_flags bit is unexplained. (2) A pump burst can still outrun the turn boundary if one loop iteration exceeds the ~8 s round (the rescan shortens the order step, the poll closes the turn on the flip — but OCR garbage at 15 s/iteration remains a risk; run1's shape was never FORCED after the fixes). (3) `queued_rescan` attributes only through uniqueness — two of ours queued in one window says nothing (conservative by design). (4) The quiet window is nearly gone: expect to reload `m54b_clean.SAV` + re-found before the next walking experiment.

**Next:** the walking arc (M54i2 -> M54j -> M54k -> M54k2) is CLOSED — a hook-armed, loop-ordered, multi-turn walk onto our own base, PASS with the checker's own instrumentation. The footing's open spines are S1 (production rebuild) and S2; ROADMAP line 86 defines S2 as the **solo turn advance** — TURN COMPLETE -> upkeep -> production -> research -> AI -> events -> next player — and this session's burst/auto-advance/0x100000 findings are heartbeat facts. Pick: an S2 milestone that INVENTORIES the round boundary from memory (what is produced on our base tiles, what upkeep moves — energy deltas are already in the trace, where research progress lives, which turn_flags bits flip when), acceptance = a script printing PASS on one real read. Re-read the ROADMAP S2 row before committing.

## Session 91 (2026-10-25) — M55: **THE SOLO ROUND BOUNDARY IS READ END TO END FROM MEMORY AND EVERY DIFF IS ACCOUNTED — `scripts/m55_boundary.py` prints PASS on a real invocation (2217->2218, 10/10 floors); a hand-typed fixture FAILs (5 floors) and the no-poke dry probe FAILs (no flip in 4 s)** — changed `scripts/m55_boundary.py` (NEW: reads one boundary from /proc/<pid>/mem, samples cur_player/year/round/stage/turn_flags at 2 ms, accounts every unit/base/faction diff), `scratch/m55_fixture_bad.json` (hand-typed negative), `NEXT_PROMPT.md`, this file, skill `references/wine-operations.md`

**Acceptance — the exact commands and what they printed:**
- `python3 scripts/m55_boundary.py` -> exit 0, `PASS boundary 2217->2218: player walk observed (cur_player [0, 2, 3, 5, 6, 7]), upkeep income read for 7 factions, research advanced, production: no net-new order-0 arrivals this round`, all 10 floors `ok`, trace `evidence/trace_m55_boundary_20261025_194440.jsonl`. An earlier identical PASS: 2215->2216, `evidence/trace_m55_boundary_20261025_194200.jsonl`.
- `python3 scripts/m55_boundary.py --fixture scratch/m55_fixture_bad.json` -> exit 1, `FAIL boundary accounting`, 5 BAD (walk only 4,5; our unit moved (10,10)->(11,10); production arrived order 2; ledger {4: 7}; research flat for every faction).
- `python3 scripts/m55_boundary.py --no-poke --no-enter --timeout 4` -> exit 1, `FAIL no round boundary (year never moved) within 4.0s` (the gate is not vacuous).

**What the boundary actually is (all read from memory, this session):**
1. **Solo heartbeat = the player WALK in `FUN_00520c10`.** `cur_player` walks every active player and ends at ours: observed sequences `[3,3,4,5,6,6,7,0,2,2,3]`, `[7,3,4,5,6,7,2,3]`, `[3,3,5,6,7,0,2,3]` — the walk ROTATES (starts after our id, not at 0). The MP 7-stage counter `DAT_0091c630` stayed 0 in every sample (15-40 samples/run) — never floor on stage in solo.
2. **The boundary needs no key when every unit is HELD: the engine auto-ends our turn.** Rounds ran 2206->2208 with zero input; at 2210+ rounds closed 1-2 s after our turn opened. BUT at 2204 the same hold-all state stalled 90 s (`stage 0`, all semaphores 0) — the auto-end gate (`DAT_0091f69c & 1`, "No units need orders Press ENTER") is CONDITIONAL and the trigger condition is still unidentified. **Confounded/unknown — do not claim "idle never advances" (session 90) nor "idle always advances" (this session).**
3. **Modal event dialogs FREEZE the walk.** "The Hive has eradicated the Gaians" held `cur_player = 2` for 90 s with every semaphore zero; the event chain then opened the PLANET display, which swallowed one Enter. Fix in the script: Return every 2 s while `cur_player != ours` (and while mid-walk) — safe, because Return is only consumed as turn-end when the human loop is running. `Escape` on the tactical map raises "Do you really want to quit?" — never press Escape (the footing already bans its OK; now ban the key).
4. **The boundary REWRITES bytes inside records that did not move.** Our 11 held records changed at u16 +28 (legs_y[0]), +48, +50 — each **decrements by 1 per round** while dying units are compacted out (a 2205 boundary with ~20 enemy deaths moved all three; a quiet boundary moved only +28). Identity for accounting is therefore **(x, y, type, owner, order)**, not 52-byte equality.
5. **Per-turn order resets and cargo.** AI units' transient orders (9, 14, 24, 27, 88) reset to 0 **in place**; order 24 = cargo/unload materialisation (two Settlers appeared at (12,50) with order 24, mp 3). Produced units arrive **order 0 on a base tile of their own faction**. Attribution across a boundary is confounded by moves + resets + cargo, so the floor is scoped to OUR side; enemy-side arrivals are labelled `production / cargo-or-order-reset / order-reset-in-place / move / unattributed`.
6. **ZERO production was measured in every round of this session** (~7 boundaries): no net-new order-0 arrival on any base of any faction. Session 90's claim that "production drops `+17 = 0` units on base tiles at every round boundary" did NOT reproduce. Faction sliders read `+0x104 = 0, +0x108 = 5..6` for all 8; base record `+0x3c` ticked 23->25 on Korolev (+2/round, a shield-style accumulator), `+0x34`/`+0x38` static. **This contradiction is M56.**
7. **Research is measured and it completes.** Three live completions: p2 rpoints 161->0 rtech 12->46; p6 -119 rtech 22->72; p2 190 pts rtech 46->44. Our points advanced +6, +12, +12, +3, +2 in most rounds — EXCEPT one boundary where ours stayed 8->8 with `labcnt 229->229` and `rtech 13->13`; ours had completed tech 36 at an earlier boundary (108->8). Our `labcnt` reads 229 while other factions read 5-137 and p0 reads -1 — **the `LAB_ARR` parallel array is suspicious after player 1 (Gaians) died** (faction slot 1 left the active mask 0xFF -> 0xFD); verify its indexing before trusting per-faction lab counts.
8. **Our side took real losses.** Garrison at University Base attrited 11 -> 10 -> 6 -> 5 units at (28,42) with no arrival of the same class (deaths, cause unattributed); then **University Base (28,42) was CAPTURED by faction 6** at the 2214->2215 boundary — the base record survived with `faction 6` (28 bases before and after). C6's floor is therefore "no base of ours VANISHES; a capture is reported", not "we never lose a base".
9. **`turn_flags` 0x100000 is set by Enter and cleared at the boundary** (observed `0x100002 -> 0x2` at +0.073 s, the only flip seen). With auto-end closing the turn, no flip appears at all (`0x2 -> 0x2`) — a flip is expected only when a key ends the turn.
10. Energy deltas were read for 7-8 factions every round (e.g. `{0:0, 2:-11, 3:0, 4:3, 5:3, 6:-24, 7:-23}`), the spending ledger `faction+4` was zero for every player after upkeep in all runs, and energy never went negative (code clamp holds).

**Open:** the production contradiction (#6) and why the whole map builds nothing; our flat-research round and the `LAB_ARR` shift (#7); death-cause attribution (#8); the auto-end gate condition (#2); enemy-side production attribution (confounded, #5). **The game is nearly lost: 1 base (Korolev Center 29,42), 5 units, year 2218, pid 1329211** — a future run may need the reload recipe before it can measure anything.

**Next:** M56 — resolve the production contradiction: prove from memory whether ANY base builds (base queue/cost fields + faction sliders + the +0x3c accumulator) across 2-3 boundaries, with a floor that FAILs on a hand-typed production trace.

## Session 92 (2026-10-25) — M56: **WHY NOTHING GETS BUILT — the gate is MINERAL STORAGE, the natural queues are EMPTY on all 28 bases, and session 91's "zero production" was a false negative (enemy bases produced in every boundary)** — changed `scripts/m56_build.py` (NEW: per-base production predictor + boundary verifier), `scripts/test_m56_predict.py` (NEW: 8 rule cases vs a mock /proc/mem), `NAMED.md` "M56 block", `ORDERS.md` §15, `scratch/m56_dump.py` + `scratch/m56_fixture_bad.json` (untracked), `evidence/m56/` (3 frames), this file, `NEXT_PROMPT.md`, skill `references/production-queue.md`

**ACCEPTANCE MET.** `python3 scripts/m56_build.py --arm 17 --boundaries 3 --timeout 120` -> `PASS production prediction: 1 verified unit arrivals over 3 boundaries, every prediction and every observed arrival accounted, queue bookkeeping exact` — `evidence/trace_m56_build_20261025_201353.jsonl`: **3/3 boundaries flipped +1** (2226->2227->2228->2229, walks [0,2,3,5,6,7] each, home to us), **1 POSITIVE prediction verified**: base 17 Korolev Center (29,42) armed by the controlled poke (pending 0->1, head -38->2 Scout Patrol, minerals 0->100, read back) -> predicted (minerals 100 >= price 10 = 10 x type_cost +41=1) -> a (29,42,type2,fac3) record appeared on the base tile, `pending 1->0`, `queue [2,-38,-38]->[-38,-38,-38]`, `minerals 100->0` (the pay -10 then **clamp B `max(0,min(10,d0))=0`** re-caps storage — M53k §D, not a 100-cost). Fixture: `python3 scripts/m56_build.py --fixture scratch/m56_fixture_bad.json` -> **exit 1**, `BAD at least 1 POSITIVE prediction verified — 0/1` (the after-units mutated: the predicted arrival removed). Rule tests: `python3 scripts/test_m56_predict.py` -> `PASS 8/8 production-prediction cases` (empty queues predict nothing; minerals 9 < 10 no / 10 = 10 yes; progress 99 with minerals 9 does NOT predict; head -30 predicts no unit; out-mask owner not predicted; price scales with +41). Classifier gates untouched: `test_classify.py` 17/17, `check_classes.py` 17/0 (no new classes; untracked `_3x.png` deleted, tracked ones restored).

**THE ANSWER TO THE MILESTONE (all read from memory).** (1) **The gate**: the queue processor `0x4ef6d0` (pipeline stage 6 of `0x4f5a70`, shard_012.c:24182) completes a queue head iff **mineral storage `base+0x40` >= price** (`0x4f0a3d cmp minerals,edi; jl return`), price = `0x4e40a0(owner,1,-1) x type_cost(+41)` = 10 x cost in-mask; pay `0x4f0ca6` -> clamp B -> POP `0x4ef5d0` (pending `+0x4c` -1, queue `+0x50..` left-shift, `faction[head]-1` at `0x94dc84`) -> `FUN_005ab650` creates the unit on the base tile (shard_012.c:20890, right after the debit). Per-round chain: `0x5208f0(p)` -> `0x520540(p)` -> the per-owner base loop (shard_013.c:11568) -> `0x4f5a70(base)` -> `0x4ef6d0` — **every base every round in solo; no "production phase" gate** (the `faction+0x104 & 2` gate at `0x521070` guards only the AI upkeep step `0x574370`; session 91's "sliders +0x104 = 0 for all 8 -> nothing can build" read the AI step, not the queue). (2) **`+0x3c` progress / `+0xcc` rate do NOT gate** — the armed base had income 0, rate 1, progress 32 and produced on the very next boundary; an accumulation model says no. Docs vs code: M53i's `cost <= +0xcc + +0x3c` completion test is the OUT-mask race scan / display path (`0x4ee8c7` "display only", M53k); the storage gate wins, proven by the poke. (3) **Why nothing builds**: natural state (read before any poke): **pending 0 + head -38 on ALL 28 bases**, every base net income `+0xd0` = 0 — the gate can never fire. (4) **The session 90/91 contradiction**: session 90 was RIGHT — enemy-side order-0 arrivals on enemy base tiles in EVERY M56 boundary ((20,24) fac 2 at 2223, base 22 fac 6 at 2226, base 24 fac 7, base 14 fac 2 at 2228); session 91 counted only OUR-side arrivals -> false negative.

**Two freezes found the hard way (both in the script now).** (a) **A produced unit arrives order 0 and FREEZES the auto-end**: `cur_player` 3, `turn_flags` 0, Return every 2 s for 150 s does nothing (run r1 died twice); ONE `h` on the cursor unit -> HOLD closed the turn at once (`tf 0->2`, walk resumed) — the script escalates Return -> `h` every 4 s past 8 s parked on our turn. (b) **The Operations Director popup does not close on Return** — default row "Zoom to Base Control", Return CYCLES options; click OK at ~(630,247). The popup text is also the **support cliff**: "The minerals output of Korolev Center is not sufficient to support Scout Patrol unit. The unit has been disbanded." — produced units die to upkeep when the base has no mineral income (our units 7->3 at 2221-2222). Escape on the map raised the quit prompt AGAIN (`evidence/m56/quit_prompt_2220.png`; "Oops, no, wait!" default, Return takes it).

**Open.** (1) Enemy-side predictions are REPORTED not floored (queues refill inside their AI turn — read them mid-turn for a real enemy-side floor). (2) The out-mask price model (era table `0x68cbb8` factor) is unmodeled. (3) Facility/project (negative-head) completions are not floored (bitmap `+0x8c` deltas). (4) The `h`-escalation assumes the cursor parks ON the actionable unit; if it parks elsewhere the loop falls back to the OK click. (5) The box after the acceptance run: **~2229, 1 base (Korolev), ~3 units, queue re-armed each run (pending 1 head 2 minerals poked 100)** — the support cliff eats every produced unit; the game is nearly lost and a reload (`m54b_clean.SAV` + re-found) may be needed before the next measurement.

**Next (M57):** give the loop an ECONOMY: either (a) reload `m54b_clean.SAV` + re-found and get a real (non-poked) positive prediction — a base whose queue the game itself filled (AI chooser at `0x4f6030` fills enemy queues; ours needs the BUILD UI `0x417ee0` or a facility that yields minerals `+0xd0 > 0` so storage >= price naturally), or (b) prove the facility side: queue a facility (negative head) at an armed base and floor the `+0x8c` bitmap delta + the `0x417ee0` queue-edit dispatch from memory. Acceptance: `scripts/m56_build.py` (extended) prints PASS on ONE real invocation with a positive arrival **not** armed by a minerals poke. Re-read `NAMED.md` M56 block + `0x417ee0` (queue edit) before shaping.

**Close addendum (follow-up session, 2026-10-25).** M56 was CLOSED in a follow-up session (the session-92 context died before the close sequence). Fresh deterministic re-verification: `test_m56_predict.py` -> `PASS 8/8 production-prediction cases`; `m56_build.py --fixture scratch/m56_fixture_bad.json` -> **exit 1** `FAIL production prediction accounting`; `test_classify.py` 17/17, `check_classes.py` 17/0, `test_walk_diff.py` 37/37. Fresh LIVE acceptance in that session: `python3 scripts/m56_build.py --arm 17 --boundaries 3 --timeout 120` -> `PASS production prediction: 1 verified unit arrivals over 3 boundaries, every prediction and every observed arrival accounted, queue bookkeeping exact` — 3/3 boundaries flipped +1 (2229->2230->2231->2232, walk [0,2,3,5,6,7] home to us each), 1/1 POSITIVE prediction verified (base 17 Korolev Center 29,42 type 2: pending 1->0, minerals 100->0 clamp B, queue left-shifted), trace `evidence/trace_m56_build_20261025_203513.jsonl`; the session-92 acceptance trace `..._201353.jsonl` was also re-parsed: 15/15 checks ok, `positive_verified 1`. Box at close: **year 2232, 1 base (Korolev Center 29,42), units_ours 2, n_bases 29, pid 1329211** — M57 should expect the reload recipe.

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
