# m53p partial-vector hypothesis — VERDICT: REFUTED (model already scores on the partial vector)

## 1. What the asm actually reads (VERIFIED, evidence/m53o_fn4e78e0_asm.txt)
- Score block 0x4e81f9-0x4e82c2 reads the base record IN PLACE:
  A:720 0x4e821f `mov eax,[esi+0xc0]` (mineral divisor term, clamped 1..99 at 0x4e8233-0x4e824b, idiv at 0x4e826f);
  A:756 0x4e828c `mov ebx,[esi+0xc4]` (energy divisor term, clamped 0x4e8292-0x4e82a3, idiv at 0x4e82bd);
  nutrient factor ecx = [esi+0xbc] loaded A:621 0x4e810c (used `imul ecx` 0x4e8264).
- [esi+0xc8] is read NOWHERE in the function (grep 0 hits); psi enters only via stack locals.
- Shortage test: A:805 0x4e8328 `cmp [esi+0xbc],ecx` — record read.
- No snapshot copy: only 8 record-field reads exist in the whole function (0x4e810c/163/21f/28c/328/3ab/5fc/85b);
  [ebp-0x24] is written from ecx/edi (0x4e7f15/f72/f9e), never from [esi+0xc0..0xc8].
- Writes to [esi+0xbc..0xc8] are only the seed store (0x4e79a5), scan-loop add (0x4e7c15),
  add-commit (0x4e85bd) and swap stores (0x4e8739/83b/951/a32) — all strictly before or after scoring.
  => the game-side premise is TRUE: at score time the record holds seed + scan contributions + earlier commits.

## 2. What the model does (VERIFIED, scripts/m53p_recon_a.py)
- vec = seed (recon_a.py:566-576) mutated by scan via add4 (recon_a.py:605 -> :589) and by mp commits via tile_add (:675-679).
- mp_best (:753, called :684) and final_score (:814) receive that running vec:
  d1=vec[0] (:816), d2=clamp99(sdiv(vec[1]-G["c4c"]+1,2)) (:822), d3=clamp99(vec[2]) (:824) — mirrors 0x4e821f-0x4e8231 / 0x4e828c-0x4e82a3;
  swap branch (:689-714) uses vec[0]/vec[2] too. R["x"]/R["y"] are tile coords only; R["vec"] (live /proc record)
  is used ONLY as the comparison target in the report (:745). The model never scores against live values.
=> The hypothesis change is a NO-OP; there was nothing to patch.

## 3. Measurement (VERIFIED, evidence/m53p_b_run.txt, game idle pid 2124624)
- scripts/m53p_recon_b.py = recon_a + a docstring note (no semantic change); run over idx 0..75.
- Result: bc 12 / c0 12 / c4 26 / c8 0 mismatch rows, 50/76 exact — IDENTICAL to the stated baseline;
  the 13 fac-2 bases {2,19,23,38,41,43,45,53,58,59,60,62,65} (37 rows) and the c4-only rows are unchanged;
  all shared rows have byte-identical model/obs/delta vs evidence/m53p_a_deltas2382.tsv.
- Note: that tsv holds 49 rows (c4=25, 25 mismatch-bases); the run adds (idx1 fac1 c4), matching the
  parent-stated 50-row census — the tsv is stale by one row (INFERRED, not investigated).

## 4. Implication (INFERRED)
The residuals (fac-2 swap rows, c4-only rows) are NOT a live-vs-partial operand problem; the next
candidates must look elsewhere (e.g. score-term inputs like l50/k2 gating or the swap-guard tie order).
