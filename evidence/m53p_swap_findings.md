# M53p swap/middle-pass reimplementation findings
Cites `A:NNN` = evidence/m53o_fn4e78e0_asm.txt line NNN; VAs are ground truth.
State: pid 2124624 idle, rows.json snapshot (base_idx=70, spec_base=-1, seeds all 0).
Runs: run1=predecessor state, run2=+halving fix, run3=+wrap fix, run4=bidx=70 experiment, run5=final.

## Measurements (scripts/m53p_recon_a.py over idx 0..75, parse: evidence/m53p_swap_parse.py)
- m53o baseline: 36/76 full (bc 20 / c0 28 / c4 30 / c8 0 mismatched rows).
- run1 (predecessor: wrap_x in scan, spiral 1..20, dword m2): 50/76 full, bc 12 / c0 12 / c4 26 / c8 0.
- run2 (+halving-subtraction fix): 50/76, same field counts (only idx 23 deltas shift).
- run3 (+wrap_x in mp_best & tile_add): 50/76, same counts; model swap commits become reachable (26 bad rows, 13 carry mp-swap tokens).
- run4 (yield bidx = constant 70 experiment): 1/76 full — REVERTED (see §4).
- run5 (final): 50/76 full, bc 12 / c0 12 / c4 26 / c8 0. No regression of the 36 m53o-exact bases.

## 1. Parent-verified correction applied (main thread, 2026-10-24)
mpass_findings §5 "swap commit is DEAD CODE" is REFUTED. [ebp-0x54] = 1<<j (the candidate's
own ring bit; `test` does not modify eax, A:540-548), so the pair dispatch at 0x4e82bf-0x4e82ce
(A:770-778) = `mask_acc & (1<<j)` ? SWAP pair (strict <, init 0x270f/-1) : ADD pair (strict >,
init 0/0). Both pairs fill per iteration; swap branch reachable. Model already implements this
(mp_best `processed & bit` split + 3 guards `gidx>0 and lval<gmax and lidx>0`, A:1015-1030
0x4e8616/0x4e8626/0x4e8631 — re-verified in asm this session). Swap commit + undo-if-still-short
(A:1192-1197 0x4e8856-0x4e886a) implemented at rebuild() lines ~700-710.

## 2. Bugs found and fixed this session (VERIFIED against asm)
a. Halving rules, 0x4e817f-0x4e81b6 (A:681-697): when nutrient <= pop*(K+1) and F==0, M and E
   become ashr(2M - pop*(K+1), 1) (`sub eax,edx ; sar eax,1`, edx = pop + pop*K); F gets the
   same subtract-then-sar when post-correction M==0 and local_50==0. M53o/predator just halved.
   Fixed in mp_best. (mpass_findings §3 "halve M,E" wording missed the subtraction.)
b. wrap_x missing in mp_best candidate loop and tile_add commits (fold when 0x92a394 bit0 CLEAR,
   proven by scan body 0x4e7b51-0x4e7b62; middle pass uses same fold per predecessor's wrap_x
   docstring A:554-562/939-947). Fixed; this is what makes swap candidates/commits land correctly.

## 3. Verified-identical-to-model blocks (no change needed; mpass_findings corrections)
- DAT_008f0c68 IS the loop budget: stored pop+1 in prologue (A:15 0x4e7904), dec'd per scan tile
  (0x4e7c36) and per add commit (A:1004 0x4e85d8) => model `budget` in d1/shortage is faithful.
- Continuation 0x4e85d8-0x4e8611 (A:1004-1017): continue iff budget > c80+c7c OR nutrient >
  (pop+1)*K STRICTLY (`cmp eax,ecx; jle 0x4e8a47`). mpass_findings §6 wrote "<"; model is right.
- Score formula 0x4e81f9-0x4e82c2 matches final_score term-by-term, incl. n1 = clamp1_99(pop -
  a27) (0x4e8272 `sub ecx,ebx`, ebx=[ebp-0x38]=a27) — mpass_findings §3 "clamp199(base+0xc4-pop)"
  was a misread; model was already right. d2 sar-vs-sdiv immaterial (clamped to >=1).
- F-transform 0x4e812f-0x4e814e/0x4e81e7-0x4e81eb: F<0 -> 2F; 0<=F<=l50 -> 4F; F>l50 -> 2(F+l50)
  (register-vs-memory subtlety at 0x4e814c: dead `add ecx,eax`) — model matches.
- Faction-modifier block 0x4e7ed2-0x4e7fb9 matches model; latent bug NOT triggered: the bit31-
  set/all-bits-24..26-clear l18 read uses stride 8124 (0x1FB4) at 0x4e7f51, model frec() uses
  0x20bc; all 76 bases take inmask0 or zero path (d38 bit31 clear everywhere), so it never fires.
- Scan loop: s=0 processed unconditionally (0x4e7b1a je), mask-gated otherwise (0x4e7b2a je
  0x4e7c3d, no budget--), budget-- also for OOB tiles (js/jge/jl all land on 0x4e7c30),
  exit-to-0x4e8a47 iff budget == c80+c7c after loop (0x4e7c4d-60 je) = model jump_tail. VERIFIED.

## 4. DAT_0068cbb0 experiment (parent's pointer-scaling note) — REFUTED as constant-70
Scan (0x4e7be9-0x4e7bf9) and add-commit (0x4e8591-0x4e85a1) both push ecx = DAT_0068cbb0 as
FUN_004e75f0's base_idx; seed facility-0x1d test (0x4e79a8-0x4e79d0) reads record
DAT_0068cbb0*0x130+0x95da9c. Substituting the live constant 70 everywhere: 1/76 full-match,
uniform +1bc/+1c0/+2c4 (base 70 facility bits 1,3 set => mine-path bonuses) => REFUTED.
Conclusion (empirical, VERIFIED by A/B): at rebuild time DAT_0068cbb0 == index of the base being
rebuilt (caller sets it per base; live 70 = last processed). Model's bidx=idx is correct.
Also: all faction seed dwords are 0, so the seed-halving branch is moot this game.

## 5. Residual classes (26 rows; honest status)
- Class J, 13 rows (1,3,6,9,15,18,31,35,47,52,61,63,70): scan jumps straight to exit in model
  AND game (live budget==c80+c7c, 0x4e7c60 je), so no middle pass fired in either; deltas are
  c4-only (-5..-2, +1 on idx 15). Every y2 +1 branch is implemented (m53p_findings §3) and no
  y2 read of base+0x30 bit15 exists (grep of m53p_fn4e7070.txt) => INFERRED: the game's last
  rebuild ran with per-tile/per-base state that has since changed (pop or d78 at rebuild time),
  not with a missing rule; no machine-addressed branch found that separates model from game here.
- Class S, 13 fac-2 rows (2,19,23,38,41,43,45,53,58,59,60,62,65): model middle pass fires a
  swap/add the game's guards rejected (e.g. idx 41: model swap 19->11 with lval 1776 < gmax 4416;
  obs proves game committed nothing). Score formula verified term-by-term (§3) => INFERRED: the
  divergence is candidate-vec state at scoring time (cascade from an earlier divergent commit or
  from Class-J-like drift in the same faction's earlier bases), not a formula/guard difference.
- c8 field: 0 mismatches everywhere (nibble/facility tail + exit refill paths agree).

## 6. Files
- scripts/m53p_recon_a.py: halving fix, wrap fixes, debug hooks gated on G["dbg"] (inert default).
- evidence/m53p_swap_parse.py (report tool), m53p_swap_run1..5.txt, m53p_swap_probe2.txt (per-row
  jump_tail/MP-state dump).
