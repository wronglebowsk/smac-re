

## Session 72 (2026-10-24) — M53Q3: **THE SEMANTIC INDEX NOW CONTAINS OUR FINDINGS — `note_chunks()` used to hold only SESSION_NOTES + rotated archives (42 chunks vs 2,790 decompiled functions) and truncated every section at 1500 chars, so `index.py search` could not find a single evidence note; it now chunks every `evidence/*.md`, `skill/references/*.md` and `NAMED.md` row (2,832 -> 3,465 chunks) with a +0.02 note prior, and the two queries that used to fail now return the right hits at rank 1-2** — `scripts/index.py`, `docs/SEARCH.md`
- **Diagnosis (VERIFIED).** `index/meta.json` had 2,790 functions / 42 notes; `note_chunks()` read only
  `SESSION_NOTES.md` + `docs/sessions/*.md` and did `text[:MAX_CHARS]`, so long session sections lost
  their tail citations and no `evidence/*.md` was indexed at all. `source_fingerprint()` hashed only
  SESSION_NOTES + Ghidra shards, so editing a finding never marked the index stale. Measured failure:
  `search "unit chain link field +48 +50 livelock"` returned 8 unrelated functions (FUN_005ab130 and
  FUN_005a6330 absent); `search "energy-only residual in the middle pass c4"` ranked our own note 7th at
  0.722 vs 0.734 for noise (0.012 spread over 2,832 candidates). Only consumer: `scripts/index.py`
  (grep over `~`), so the 258v GPU was idle ~all day.
- **Fix (VERIFIED by rebuild + acceptance test).** `_note_sources()` = SESSION_NOTES + NAMED + every
  `evidence/*.md` + every `skill/references/*.md` + `docs/sessions/*.md`; `_pack()` splits sections into
  <=1400-char windows (no truncation); one chunk per NAMED row (`named:<line>`); `source_fingerprint()`
  covers all of them; `NOTE_PRIOR = 0.02` added to note cosine scores. Rebuild: **3,465 chunks
  (2,790 functions, 675 notes), 409-693 chunks embedded in 16-24 s**; full rebuild stays cheap because
  the digest cache only re-embeds changed chunks.
- **Acceptance test (the point of the milestone).** `search "unit chain link +48 +50 livelock"` ->
  `NAMED.md:485` (`0x5a6330`, walks `+48`) rank 1, `NAMED.md:484` (`0x5ab130`, walks `+50`) rank 2.
  `search "energy-only residual in the middle pass c4"` -> `evidence/m53p_j_findings.md:75` rank 1,
  `evidence/m53p_partial_findings.md:32` rank 2, `evidence/m53p_swap_findings.md:58` rank 6. Before the
  fix: zero on-point hits in either.
- Caveat: `skill/references/wine-operations.md` (moved verbatim from the old SKILL.md) also contains the
  7-vector-add-site digest, so it competes with `production-rebuild.md` for production questions — worth
  splitting when that file is next touched.
- **Next:** `NEXT_PROMPT.md` — M53q unchanged (implement `build_table`); `index.py search` is now the
  first look-up step before grepping.

## Session 73 (2026-10-24) — M53q: **`build_table()` IS IMPLEMENTED — the per-visit scan pool is recomputed per base, and the entry filter turns out to be a NO-OP (pool∩fresh = {bit 0} on 76/76 rows); the M53p 'stale-global contamination' framing is superseded** — `scripts/m53p_recon_a.py::build_table`, `evidence/m53q_findings.md`
- **Implementation (VERIFIED vs the live cur base).** `build_table(idx) -> (table[25], mask21)` transcribes
  `FUN_004e63b0` (asm 298136-298619): loop A per-step reason codes (2 off-map/unseen, 0 scannable, 4 terrain
  test `tile[8]&1 ∧ 0<=tile[2]&0xf<8`, |=8 unit order-3 / foreign-stack test, |=0x20 foreign territory), loop
  B/C the |=0x10 other-base overlap (hex-dist<=5 bases, their `+0x78` bits, tile hex-dist<=2), mask =
  {bit i: table[i]!=0}. On the live base 69 the computed table matches the live `0x8f0ccc` on **20/21 slots**;
  the mask rule is VERIFIED (computed-from-live == live 0x101; `DAT_008f0d30` has exactly 2 stores in .text,
  both inside 4e63b0). **The single disagreement is bit 8** (step 8, tile (45,9), foreign-stack test): live 8,
  computed 0 — the transit stack (units 106..147, order 0, `w18=0xffff`, `b25=0xff`) satisfies the |=8 test
  only in a pre-move state (INFERRED). Reported per protocol before touching residual theory.
- **Predicate fixes found by hand-tracing the live stack (VERIFIED):** the +50 walk at 0x4e663c starts from
  the **+48 terminus** (esi carries over; asm 298346-52), not the head; the |=8 gate polarity is foreign ∧
  ¬transport(0x440) ∧ **+25-bit-CLEAR** (x86 `test/je` fires when the bit IS set — 0x4e6612); `FUN_005a5c00`
  is identity only when `0x920434 != 0` (live 0 — full body runs); `FUN_005ab130` returns the tile list head
  iff record `+8` bit 1 else the linear-scan +50-head. Hex dist = `mx - ((manhattan>>1 - mn +1)>>1)` wrapped.
- **The no-op discovery (VERIFIED, 76/76).** `pool(d78) & fresh_mask == {bit 0}` for every base ⇒
  `d78 & (~fresh|1) == d78` everywhere; the fresh mask differs from the stale global 0x101 on 76/76 rows yet
  the censuses of `--stale-mask` and the fresh path are byte-identical. Tie-break: stored processed for idx
  1/69 KEEPS bit 8 ⇒ the game's filter allowed step 8 ⇒ the filter mask is the per-base fresh mask (code
  order: 4e63b0 at 0x4e78e9 runs before the filter at 0x4e796a), and the stale global never filtered anything.
- **Re-measured census (fresh dump `evidence/m53q_dump4.txt`, pid 2124624, cur base 69):** 76 rows, **65
  self-consistent, 54 exact, 11 residual** (was 46/7 when session 68 wrote NEXT_PROMPT); cells bc 11 c0 9 c4
  21 c8 0. Residuals all c4-only: idx 1,3,5,8,30,34,46,51,60,62,69 (facs {1,3,4,7}, was {1,3,4}); **session
  68's idx-31 'fac2 bc -1' residual collapsed to EXACT**. The 11 non-sc rows are ALL fac 2 (37,40,42,44,52,
  55,58,61,64,70,72) and are same-cardinality step-SET mismatches (idx 44: model drops step 4, game kept it
  and dropped step 2) — a scan-ORDER question, not a mask question.
- Kit: `scripts/m53o_mem.py` units blob 0x200->0x4600 + `nunit` key; `--legacy` renamed `--stale-mask`;
  probes `evidence/m53q_probe.py` (live read of everything 4e63b0 reads), `m53q_maskcmp.py`, `m53q_nonsc.py`.
- **Next:** M53r — the fac-2 scan-order/selection rule (11 rows) and the c4-only residuals (11 rows).

## Session 74 (2026-10-24) — M53r: **THE 11 FAC-2 ROWS ARE POP-DRIFT BUDGET ROWS, NOT SCAN-ORDER ROWS — the model now runs 76/76 self-consistent, 65 exact (was 65/54); `DAT_008f0c68` = pop+1 AT VISIT TIME and 22 rows drift-recover to exact** — `scripts/m53p_recon_a.py::recover_pop`, `evidence/m53r_findings.md`
- **Scan-order theory dead (VERIFIED).** The whole middle-pass selection was re-derived from the asm
  window and the model already matched every gate: candidate loop j=1..20 (cursor 0→0x50 step 4,
  A:789-796), pair dispatch strict `<`/`>` (A:772-787), swap-branch guards commit-require
  best-add idx > 0 / best-add score > best-swap score / best-swap idx > 0 (A:1018-1026 — the old
  reference listed "best-add index > 0" as an EXIT condition: polarity flipped, fixed), undo gate
  `bc < (pop+1)*K` (A:1192-1197), facility gate/score, continuation, exit stores
  `0x78 = acc` / `0x7c = budget` RAW (0x4e8b19/0x4e8b28). dbg traces (`evidence/m53r_dbg.txt`)
  showed the model firing swaps (e.g. idx 44: out 2 in 1, guards all pass) that the game never
  committed — stored mask == pool AND stored vec == scan-only vec on all 11 rows.
- **The tell (VERIFIED).** `DAT_008f0c68` has exactly 4 stores in `.text`, all in 4e78e0 (Ghidra
  shard_012.c:16023/16108/16229/16626 = machine 0x4e7904/0x4e7c36/0x4e7ecd/0x4e85d8); sole
  initializer = `movsx BYTE[base+6]+1` = pop+1 at visit time (Ghidra `[3]` = short*-scaled byte@6).
  Exit publishes `base+0x7c` = budget RAW, so the stored carry re-measures the game's budget. On
  all 11 rows stored c7c == model budget_end **+ 1** (`evidence/m53r_sig.py`, all 76 rows).
  Skip flag re-decoded too: `1 iff NOT((1<<fac)&byte0(0x985b10)) ∨ (byte0(+0x38)&0x40 ∧ bit31)` —
  live 0xff08 ⇒ flag=1 for all facs but 3 (the "tile out-of-mask" note was wrong); scan-0 special's
  tile scan self-skips without budget spend when acc bit 0 is already set (A:368).
- **Mechanism.** With budget0 = pop_dump+1 the scan ends with budget == c80+c7c → `je 0x4e8a47`
  (0x4e7c5e) skips the scan-0 special AND the middle pass — the phantom-swap territory is never
  entered. Replaying with pop_visit = dump+1 reproduces ALL THREE stored outputs simultaneously
  (mask, carry, vector) on **22/76 rows — all fac 2**: the 11 non-sc rows (37,40,42,44,52,55,58,61,
  64,70,72) plus 11 that were mask-OK but carry-wrong (28,31,47,48,49,56,63,65,67,68,71). INFERRED:
  those bases LOST a pop point after their rebuild visit (cause open; idx 0/23 fac-2 did not drift).
- **Acceptance (fresh dump 2026-10-24, pid 2124624, `evidence/m53r_run1.txt`):** rows 76,
  **self-consistent 76, exact 65, residual 11 c4-only UNCHANGED** (1,3,5,8,30,34,46,51,60,62,69),
  cells bc 0 c0 0 c4 11 c8 0. `recover_pop` accepts pop+1 only when stored mask AND stored carry
  reproduce; `--no-pop-recover` shows the plain view; header prints `pop-drift=+1(pop a->b)`.
- Kit: `evidence/m53r_sig.py` (per-row saved-carry vs replay-budget signature); skill
  `references/production-rebuild.md` corrected (guards polarity, skip-flag formula, scan-0 acc-bit-0
  gate, budget-at-visit-time + drift signature, exit clears bit 17 of +0x30 not bit 8).
- Open: the 11 c4-only residuals (no budget drift there — saved c7c == budget_end; suspect
  visit-time state drift in 4e7070's unit/ownership inputs or `0x8f0c4c`); why drift is fac-2-only;
  `c80_end != stored d80` on idx 24/35 (internal field, unpublished); bit-8 live-table disagreement
  at (45,9); unit+24/25 + 38 semantics.

## Session 75 (2026-10-24) — M53s: **THE 11 c4 RESIDUALS ARE NOT A SCAN PROBLEM AT ALL — the rebuild model matches the game's own visit-time snapshot on 76/76, and the delta is an ALLIANCE ENERGY SHARE that FUN_004eaa10 folds into base+0xc4 at 0x4eac57-0x4eac62 after 4e78e0's history shift** — `evidence/m53s_findings.md`, `scripts/m53s_c4watch.py`, `scripts/m53s_c74_watch.py`, `evidence/m53s_probe.py`
- **The leverage nobody had used (VERIFIED):** `4e78e0`'s exit shifts a history window
  (`0xac<-0xbc, 0xb0<-0xc0, 0xb4<-0xc4, 0xb8<-0xc8`, asm 0x4e8b39-0x4e8b54), so
  `base+0xac/0xb0/0xb4/0xb8` is the vector **at the visit's exit**, immune to every later
  writer. `evidence/m53s_probe.py`: model == that snapshot on **76/76 rows, all four fields**.
  The 11 residuals were therefore never a yield/neighbour/`0x8f0c4c` question — the rebuild is
  complete; the model just stops where the game's rebuild stops.
- **Energy-only, post-snapshot (VERIFIED):** `c4_now - c4_prev == -delta` on exactly the 11
  rows (gains 1,3,2,2,2,2,5,3,2,1,1) while `+0xbc/+0xc0` change on **0/76** rows visit->visit.
- **Writer, caught live (VERIFIED):** hw watchpoints on base46+0xc4 (0x961174) and base3+0xc4
  (0x95de64) across the driven round 2384->2385 (`scripts/m53s_c4watch.py`): base 46's writes
  end at **17** from 0x4e85c1 (= model = `base+0xb4`), then **0x4eac68 writes 20 then 22**; base
  3 ends at **12**, then **0x4eac68 writes 15**. Site = `mov ecx,[eax+0xc4] / add ecx,esi /
  mov [eax+0xc4],ecx` at 0x4eac57/5d/62 in **FUN_004eaa10** (eax = DAT_008f0d60), which runs
  right after 4e78e0 in every pass of the per-base turn processor FUN_004f5a70 (0x4f5ac8->
  0x4f5ad7, 0x4f5b3c->0x4f5b4b, 0x4f5c55->0x4f5c64).
- **The obvious candidate is dead (VERIFIED):** the sibling fold `base+0xc4 += DAT_008f0c74`
  (0x4eaa2e/0x4eaa30) fired **211 times over 74 bases with add = 0 on every one**
  (`scripts/m53s_c74_watch.py`). `DAT_008f0c74/78` are only ever written by `4e8d60`'s entry
  reset (0x4e8d86/0x4e8d92) and accumulate via `inc [eax*4+0x8f0c6c]` (0x4e8e82) /
  `add [ecx*4+0x8f0c6c],eax` (0x4e8f35) — the same slot family that feeds `bc` (0x4e9336/44) and
  `c0` (0x4e944b/59), which is why those two fields show no residual either.
- **Single-writer protocol:** Ghidra `grep '0xc4) ='` over all shards gives, for game records,
  only shard_012.c:17952 (`+= DAT_008f0c74`) and :18010 (`+= iVar5`); machine scan finds **no
  `add [reg+0xc4]` anywhere in .text** and only 7 displacement stores to `+0xc4` total (2 of
  them in 4eaa10; the rest are ctor/UI sites — disproofs in `evidence/m53s_writer_scan.md`).
- **Semantics (INFERRED, cited) + a dump-visible confirmation:** the fold runs once per OTHER
  faction that is allied with the owner (stance bit 2 either direction, `0x94d448+fac*0x20bc+o*4`),
  adds `n = ceil((ally-base energy + my energy)/8)` scaled by `[0x94d734+fac*0x20bc]+1` over
  `DAT_0092a274+1`, halved without stance bit 1, +1 if `DAT_00985bc0 == owner`. In the dump the
  factions with any bit-2 ally are exactly **{1,3,4,7}** — exactly the gain-bearing factions —
  and base 46 (fac 1, allies {4,7}) took **two** increments (+3, +2) while base 3 (fac 4, ally
  {1}) took one (+3). Gains reproduce across a driven round (same 11 bases, +idx 6, idx 51 3->2),
  so this is rule behaviour, not visit-time drift.
- **Driving (this position stalls the stock driver):** the HUD message pane says "nutrients", a
  BASE_WORD, so every frame classifies `base` and `--no-escape > timeout` forbids the clearing
  Escape -> two STUCK runs with zero hits. Worked instead: click the OCR'd `COMPLETE` word
  (697,416) -> "Do you really want to end the turn now?" -> `answer_confirm`; then the Council
  blocks the round (PROTOCOL DIRECTOR OK bar, PROPOSAL vote bars x=311/400/489 y~498 found by
  colour geometry because `tesseract tsv` yields nothing for those labels here, then the HIVE
  bribe pane — Escape closes it, Return advances). Post-drive dump censuses at only 31
  self-consistent rows (fresh-mask/pop have moved on — the M53r signature), so the 76/76
  self-consistency claim belongs to the pre-drive dump (`evidence/m53s_dump1/`).
- **Next:** implement the fold in `m53p_recon_a.py` (read the ally base via `FUN_004ea940`'s
  k-th-nearest rule + the stance/`0x94d4f0`/`[fac-0x244]` zero-gates) and re-run the census —
  the 11 residuals should collapse to exact. Then: why idx 6 joined and idx 51 changed by 1;
  `DAT_008f0d40[other]` consumers; the still-open M53r items.

## Session 76 (2026-10-24) — M53t: **THE FOLD IS IMPLEMENTED AND 10 OF THE 11 RESIDUALS CLOSE EXACTLY (74/76)** — `evidence/m53t_fold.md`, `scripts/m53p_recon_a.py` (`alliance_fold`, `census`, `--mem-dir`)
- **What the share actually is (VERIFIED, full decode 0x4eab02-0x4eac8a):** per allied OTHER
  faction, `n = (E[ally k-th] + E[me] + 7) >> 3` on `base+0xb4`, `s = ((faction[owner].+0 + 1)*n
  + D/2) / D` with `D = [0x92a274]+1`, halved unless `stance[owner][other]` bit 1, `+1` when
  `[0x985bc0] == owner`, then zeroed if `[0x94d4f0 + fac*0x20bc]` is set for owner or other.
  Gate A is the stance bit 2 **in both directions** (the second read is the transpose at
  `0x94f504 + owner*4`, advanced `+0x20bc`). Published to `DAT_008f0d40[other-1]` *before* the
  zero-gate, so the published copy keeps the ungated value.
- **`FUN_004ea940` is not "k-th nearest" — it is k-th by ENERGY** (key `E<<9 | idx`, bubble sort
  desc, `-1` when `k >= count`); no distance is computed in it. Rank `k` = number of the owner's
  bases above `(E_me<<9 | [0x68cbb0])`, and `0x68cbb0` is set to the base's OWN index at
  `0x4f5a7c` — using the dump's global (the last base visited, 69) mis-ranks ties and was the one
  real bug in the first implementation (idx 1 came out +1 too high).
- **Acceptance (pre-drive dump `evidence/m53s_dump1`, pid 2124624):** before 76 sc / 65 exact /
  11 c4-only; after **76 sc / 74 exact**, residuals `{6: +2, 51: -1}` —
  `evidence/m53t_run_before.txt:1-12`, `evidence/m53t_run_after.txt:1-3`, per-row ally detail
  `evidence/m53t_probe.txt:1-24`. Closed: idx 1, 3, 5, 8, 30, 34, 46, 60, 62, 69.
- **The two stragglers are NOT formula errors (INFERRED):** idx 6 and idx 30 have identical
  (fac, energy, rank) yet +0 vs +2 observed (`probe:7-8` vs `:11-12`), and idx 51 wants one more
  than the formula gives. Prime suspect: `FUN_004f5a70` runs the whole
  `4e8d60/4e78e0/4e92c0/4e93f0/4eaa10` sequence **twice** — second pass gated on `[0x985afc] > 1`
  (284 here) with `[0x8f0d64] = 1` (`0x4f5b14-0x4f5b2c`), and `4eaa10` reads d64 at `0x4eac95`.
  `+0xb4` is byte-identical across the two dumps while `+0xc4` moves, so pass 2 sees a different
  record. Do NOT close this by fitting constants.
- **Kit:** `--census` (all 76 rows, exactness before/after the fold), `--no-fold`, `--mem-dir`
  (the post-drive `evidence/m53o_mem` has only 31 self-consistent rows — never use it for the
  exactness claim), and `show()` now prints the fold line.
- **Next:** the M53 thread is CLOSED as a model; the two rows above are a background probe
  (watchpoint at 0x4eac57 + a pass counter at 0x4f5b2c over one driven turn), not a queue. Next
  session is the harness/G1 switch — see `NEXT_PROMPT.md`.

## Session 77 (2026-10-24) — M54a: **THE HUD NO LONGER TRICKS THE CLASSIFIER, THE DRIVER ANSWERS THE PANES — THE 40-TURN RUN IS STILL OPEN (→ M54b)**
- **The bug, fixed and pinned.** `classify()` returned `base` for ANY frame whose OCR text held a
  BASE_WORD, and the HUD's own message pane prints news lines that do: `nutrients` at (355,438)
  with TURN COMPLETE at (628,419) on `evidence/m54a/live_hud.png` (the session-75 stall position,
  captured first this session). The test is positional now — `base_word_positions` +
  `in_msgpane`, `MSGPANE = (0,425,800,600)`: base words count only outside that strip, or while
  the HUD button row is absent (a real base screen has no TURN COMPLETE row: `m45a_post.png`,
  words at y 16-45 + (279,273), `btn=None`). Acceptance numbers, no game needed:
  `python3 scripts/test_classify.py` → **PASS 10/10 screen classifications**; the same frames
  through the older suite `python3 scripts/check_classes.py` → **frames: 10 failures: 0**.
  `scripts/m54a_ocrscan.py` re-OCRs every evidence PNG into `evidence/m54a/ocrscan.json:1`
  (base-word coords, button centre, flatness, the OLD classify label) — that is where the
  "was `base` / was `title`" claims come from.
- **Three screen classes the driver had wrong.** (1) `quit-prompt`: the "Do you really want to
  quit?" dialog wears the game title as its banner, so `title` fired on it and a 40-turn run
  STOPPED at turn 13 refusing to answer it (`evidence/m54a/quit_prompt.png`; m37_screen0.png and
  m15_title_now.png are the same dialog, not title screens). Escape = "Oops, no, wait!" is the
  safe answer; OK exits. (2) `help`: the HELP browser (FACTION PROFILES/CONCEPTS) contains base
  words, ignores Escape entirely, and closes only on its EXIT bar (BACK (275,344), EXIT (525,344)
  on `evidence/m54a/live_now2.png`). (3) the battle **Replay** screen ("Replay: 2415" + a Close bar
  at (400,587), `evidence/m54a/movie_stuck.png`) OCRs to 5 words → `movie` → the driver waited;
  now a `movie`/`unknown` frame with a bar at y ≥ 560 gets clicked.
- **Bar geometry: a horizontal RUN does not work on this build.** The push-bars are DITHERED —
  fill (103,91,181) on every OTHER scanline, (28,80,99) between (measured band y 489-507 on the
  PROPOSAL vote, `evidence/m54a/stuck2.png`) — and their labels are drawn INSIDE them, so
  session 75's `run > 55 px` test finds ZERO bars exactly where the vote is. `pane_bars` is now
  band + column density: rows bar-filled over 100 px, grouped across 1-row dither gaps, then
  per-column fill inside the band; 30% duty splits YEA/NAY/ABSTAIN at centres 311/400/489 = the
  YEA(310,495) NAY(398,495) ABSTAIN(485,495) row hand-measured in session 75. 40% duty cuts a
  labelled bar in half; 15% merges the row and you click NAY.
- **The driver now answers the round's modals itself** (`handle_pane`, ahead of the generic
  dialog/Escape paths in `service_turn`, both phases): Council PROPOSAL vote → click YEA
  (`vote-yea@311,498/council`, 6 hits live); Council "Have you any further business?" → top option
  row then the MERGED OK bar (the label splits it into (266,347)+(534,347); click the centre
  (400,347)) — 4 hits, the turn advanced right after; HIVE bribe → Escape then Return (11 hits);
  quit dialog → Escape (2); help browser → EXIT (1); replay → Close (89). Live totals across the
  9 runs: **45 turn-records, 29 turns advanced with the year +1 on each, 16 stalls**, position
  2385 → 2416, n_bases 75 → 79. `Return` is still the right answer for advisory panes — the
  PSYCH CHAPLAIN "Our citizens are starving" alert has a highlighted `Zoom to Base Control` row
  that `pane_bars` reports at (310,221) and clicking it does NOT clear it
  (`evidence/m54a/stuck_pane.png`; turn 0 STUCK 277.8 s on two identical clicks).
- **THE 40-TURN ACCEPTANCE IS NOT MET — that is M54b.** Best single invocation: 12 turn-records /
  12 advanced / 1 stall, max dt 164 s (`evidence/trace_m54a40c_20261024_174316.jsonl:14`); the
  longest run after the pane fixes: 12 records / 10 advanced (`evidence/m54a/run40h.log:1`).
  Runs die on 2 consecutive stalls, and the stalls were: OCR starvation when another job shared
  the box (one turn burned 355 s on ~1 OCR pass per iteration), the help browser, the replay, and
  finally the game falling back to the TITLE screen mid-round (the driver clicked into the LOAD
  file browser and clicked its OK bar 20×). No STUCK ever exceeded 2× the per-turn timeout.
- **State of the box:** pid 2124624 is alive but at the title menu (I clicked CANCEL on the LOAD
  browser — `evidence/m54a/after_cancel.png` reads `start game / scenario / load game / …`). The
  position is NOT lost: the game autosaves into `programs/saves/auto/` (newest 19:05) and
  `programs/Alpha Centauri Autosave 1.SAV` (19:08). Next session: load the autosave (the
  `scripts/m48d_boot.py` load path) before driving anything.
- **Next:** **M54b** — the 40-turn unattended assertion: a boot/load wizard step for the driver,
  a per-turn budget that survives a long Council/replay round (the 2-stall abort is too eager),
  and never clicking a bar outside the pane we own.
