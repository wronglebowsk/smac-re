

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
