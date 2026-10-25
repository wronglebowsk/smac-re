# Session notes archive — sessions 73-74

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
