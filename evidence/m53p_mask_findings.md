# M53p (session 68, second half) — the model's entry scan mask is PER-VISIT state; the honest residual collapses to 2 rows

Live state for every number here unless stated: pid 2124624, year 2382, cur_player 3, nb 76,
era 2, mask 0xff08, TracerPid 0, read-only `/proc/pid/mem`. Snapshots: `evidence/m53p_r2_all76.txt`
(08:52, year 2382, unpatched), `m53p_r3_all76.txt` (09:44, unpatched), `m53p_r4_all76.txt`
(09:47, patched). First half of this milestone = `evidence/m53p_findings.md` + `m53p_j_findings.md`.

## 1. Two-round stability test (VERIFIED, main thread)
Diff of the year-2381 census (`evidence/m53p_all76.txt`, 40 rows with deltas) against a fresh
year-2382 census (`m53p_r2_all76.txt`, 26 rows): of the 41 (idx,field) cells present in both,
18 identical, 23 changed value; 9 cells new, 36 gone.
- The 13 "Class J" c4-only rows: **12 of 13 deltas bit-identical across the two rounds**
  (1:-2, 6:-2, 9:-3, 15:+1, 18:-3, 31:-2, 35:-2, 47:-5, 52:-1, 61:-2, 63:-1, 70:-1); only idx 3
  changed (-5 -> -3).

## 2. Machine fix: the middle-pass score corrections are trunc(x/2), NOT subtract-then-sar (VERIFIED)
`evidence/m53o_fn4e78e0_asm.txt:658-683`. 0x4e817f `lea edx,[ecx+edi*1]` (= pop + k2) feeds ONLY
the 0x4e8182 `cmp ebx,edx` / `jg` guard (ebx = `mov ebx,[esi+0xbc]` at 0x4e8163 = base+0xbc). Each
of the three corrections is the canonical signed-div-by-2 idiom `cdq; sub eax,edx; sar eax,1`
(0x4e818d-90 on [ebp-0x18], 0x4e8198-9b on [ebp-0x1c], 0x4e81b1-b4 on [ebp-0x10]) and **cdq
overwrites that edx**, so the machine halves the already-DOUBLED value truncating toward 0 (i.e.
undoes the doubling). The model subtracted pop+k2 first. Patched `scripts/m53p_recon_a.py:796-801`
(`ashr(bb - pk1, 1)` -> `sdiv(bb, 2)` etc.). Effect on the 09:44 snapshot: **full-match 18 -> 19**
(idx 67 becomes exact), field cells unchanged bc 45 / c0 48 / c4 42 / c8 0 — a real machine fix,
not the residual rule.

## 3. LOAD-BEARING: DAT_008f0d30 (entry blocked-step mask) is recomputed at EVERY rebuild entry (VERIFIED)
- `FUN_004e63b0` is the FIRST call inside `FUN_004e78e0`: `0x4e78e9 call 0x4e63b0`
  (`evidence/m53o_fn4e78e0_asm.txt:7`).
- It writes the 21-entry table 0x8f0ccc..0x8f0d1c with flag values 0/1/2/4/8:
  `mov [ecx+0x8f0ccc],0x1` 0x4e63e8; `=0x2` 0x4e6442 and 0x4e6518; `=0x0` 0x4e6533; `=0x4`
  0x4e6563; `or [eax+0x8f0ccc],0x8` 0x4e659f and 0x4e6635 (cached `.text` lines
  298155/298184/298261/298269/298284/298305/298352).
- Then 0x4e6925-0x4e694f builds **`DAT_008f0d30 = {bit i : table[i] != 0}`**: `xor edx,edx;
  mov ds:0x8f0d30,edx` (0x4e6925/29), loop 0x4e6934-0x4e694b `cmp [eax],0 / je skip / mov esi,1 /
  shl esi,cl / or edx,esi / add eax,4 / inc ecx / cmp eax,0x8f0d20 / jl`, final `mov
  ds:0x8f0d30,edx` (0x4e694f). LIVE CHECK: table = {0:0xc, 8:0x8, others 0} -> derived 0x101 ==
  live `0x8f0d30` 0x101 (VERIFIED on this sample; the rule itself is read off the loop).
- Entry filter `base+0x78 &= (~DAT_008f0d30|1)` (0x4e796a-72) therefore clears from the scan pool
  exactly the steps whose table entry is nonzero, and the exit overwrites `base+0x78 = processed`
  (0x4e8b19). So base+0x78 is the *scanned* mask of the last rebuild and the pool for the next one.
- CONSEQUENCE (VERIFIED): the live global mask describes only the LAST-PROCESSED base — live
  `DAT_0068cbb0 = 0x46 = 70` (our base) and `DAT_0068cbb4 = 0x46` (the M53n "freshness marker",
  which is therefore NOT -1 while idle on our turn — correction to the standing kit). For any base
  whose stored base+0x78 still has bit 8 (live: idx 6 = 0xf2951, idx 47 = 0x9589), step 8 WAS
  scanned at its rebuild, which requires table[8] == 0 at that entry, while live table[8] = 8 ->
  the table changed after that rebuild -> the model's `mask_in` is provably not the game's mask.
- The model reads a DUMP, not live memory: `scripts/m53p_recon_a.py` consumes `evidence/m53o_mem/*.bin`
  written by `scripts/m53o_mem.py`. Name the refresh in every report — the SAME script gave 50/76 on the
  year-2381 dump and 18/76 on the year-2382 dump.
- Volatility WITHOUT a year advance (VERIFIED by direct `/proc` pread): between the two snapshots of the
  SAME year-2382 idle turn, `0x8f0d30` 1 -> 0x101, `0x91c628` 0 -> 1, `0x985afc` (unit count) 281 -> 282,
  `0x8f0c4c` 6 -> 7. INFERRED: the game's own idle/UI pump re-ran 4e78e0 (hence 4e63b0) on base 70 while
  we sat idle.

## 4. Honest baseline on the 09:44 snapshot, patched model (VERIFIED)
19/76 exact; mismatch cells bc 45, c0 48, c4 42, c8 0.
- Self-consistent rows (`mask_in == processed`), 19: [4,10,13,17,22,26,30,33,39,40,44,46,51,61,
  67,70,71,74,75]. **17 of them are exact**; the only two genuine residuals are **idx 61 (fac 4,
  c4 -2)** and **idx 70 (fac 3, our base, c4 -1)**, both energy-only (bc/c0/c8 exact).
- The other 57 rows have `mask_in != processed` -> their deltas are contamination, not evidence of
  a rule gap. (Two exact rows, idx 55 and 69, are mask-inconsistent yet field-exact: coincidental
  agreement, the model scanned steps the game did not.)
- => the session-68-first-half picture ("26 residual rows in Class S + Class J") collapses to
  **2 rows** once the mask-contamination filter is applied.

## 5. Verified negatives (child `evidence/m53p_j_*`, main thread re-checked the machine cites)
- An independent reimplementation of `FUN_004e7070` from pseudocode disagrees with the model's
  per-tile energy on **0 of the mask tiles of all 76 bases** (`evidence/m53p_j_tilecmp.py`) -> the
  per-tile energy function is faithful; the missing energy is not a yield branch.
- Every vector write in 4e78e0 goes through the 4-field 0xbc..0xcc loop via `FUN_004e75f0` (scan
  0x4e7be9/0x4e7ea3, mp-add, swap-out 0x4e8739, swap-in 0x4e883b, undo 0x4e8951/0x4e8a32), so a
  swap can change field 2 alone ONLY if swap-in and swap-out tiles have equal nutrient AND equal
  mineral (Base 2,1,1 vs ImprovedSea 2,1,3 -> net (0,0,+2) is the only such category pair).
  The candidate loop is steps 1..20 only -> the "steps 21..79 alias and double-add" theory is dead.

## 6. Open -> M53q
- **Decode the table writers inside `FUN_004e63b0`** (0x4e63e8 / 0x4e6442 / 0x4e6518 / 0x4e6533 /
  0x4e6563 / 0x4e659f / 0x4e6635 — which terrain / facility / claim / ownership condition sets
  entry i to 1, 2, 4, 8) so the model can RECOMPUTE each base's scan pool instead of reading one
  stale global. Until then only the last-processed base's row is interpretable.
- The 2-row energy residue (idx 61 -2, idx 70 -1): post-rebuild input change (tile level / u9 / uc
  / owner byte 7, facility bitmap base+0x8c, base+0x30 bit 2, base+0x34 0x2000/0x4000) or a
  different `DAT_0068cbb0` during that base's rebuild [INFERRED; no machine branch found].
- `DAT_008f0c4c` (live 7, was 6) is used by the score denominators at 0x4e821f-0x4e8231 — same
  per-visit-state problem, needs the same treatment.

## 7. Fresh DRIVEN round (VERIFIED — 2382 -> 2383 after clearing the livelock, see `m53p_livelock_findings.md`)
Dump refreshed with `scripts/m53o_mem.py` before each run. Pre = `m53p_r4_all76.txt` (year 2382),
post = `m53p_r5_all76.txt` (year 2383, cur_player 3):
- exact 19 -> **40/76**; cells bc 45->27, c0 48->23, c4 42->29, c8 0->0; self-consistent rows 19 -> **46**.
- self-consistent residuals after the driven round (7): idx 3 fac4 c4 -3, idx 30 fac4 c4 -2, idx 51
  fac1 c4 -3, idx 60 fac4 c4 -2, idx 62 fac1 c4 -1, idx 69 fac3 c4 -1 (all c4-ONLY) plus idx 31 fac2
  bc -1. The pre-drive residuals are gone: idx 70 is now exact, idx 61 is no longer self-consistent.
- => the c4-only-negative class is stable in CHARACTER and in faction set {1,3,4} across a driven
  round, but its MEMBERSHIP moves with the round. The model's absolute accuracy depends on how
  coherent the per-visit mask state is at snapshot time (19 vs 40 exact one round apart) — the
  self-consistency filter, not the exact-match count, is the honest progress metric.
