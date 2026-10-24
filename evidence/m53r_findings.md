# M53r — the 11 fac-2 rows are POP-DRIFT BUDGET rows, not scan-order rows

Dump `evidence/m53o_mem/*.bin` refreshed 2026-10-24 (pid 2124624, idle, TracerPid 0, cur base 69).
Census `evidence/m53r_run1.txt` via `evidence/m53p_swap_parse.py --sc`. ASM cites =
`evidence/m53o_fn4e78e0_asm.txt` line numbers (window of FUN_004e78e0).

## 1. Middle-pass selection re-derived from asm — the scan-ORDER theory is dead (VERIFIED)
- Candidate loop j = 1..20: cursor `[ebp-0x2c]` 0→0x50 step 4, offsets `[ptr+0x678510]` = XOFF[j]
  (A:539, 551, 789-796 `cmp eax,0x50 / jl 0x4e800a`). Gate: candidate skipped iff
  `(1<<j) & ((swap?0:acc) | DAT_008f0d30)` (A:540-548); the swap-mode exclusion `[ebp-0x50]` is 0
  (neg/sbb/not idiom 0x4e7fe4-0x4e7fed, A:530-538).
- Pair dispatch (A:772-787): acc bit j set → SWAP pair, strict `<` (0x4e82cb `jge` skips); else ADD
  pair, strict `>` (0x4e82de `jle` skips). Ties keep the lowest j.
- Swap-branch guards (A:1018-1026), each exits UNCOMMITTED: best-add idx ≤ 0 (0x4e8616 `jle` —
  **polarity corrected**: production-rebuild.md listed "best-add index > 0" as the exit condition;
  it is the COMMIT precondition), best-add score ≤ best-swap score (0x4e8624 `cmp`/`jle`),
  best-swap idx ≤ 0 (0x4e862f `jle`). Commit (A:1027-1042): `acc = (acc & ~(1<<swap_idx)) |
  (1<<add_idx)` (swap-out = best-swap idx, swap-in = best-ADD idx), yields out then in.
- Undo gate (A:1192-1197): undo iff `base+0xbc < (pop+1)*K` (0x4e886a `jge` skips undo; acc
  rewrite 0x4e8870-0x4e888a). Model already matched.
- Facility tail gate (A:797-813): runs iff skip-flag ∧ pop≥5 ∧ (bc > pop*K ∨ `[ebp-0x3c]`==0) ∧
  `0x985afc`>100; entry gate `FUN_005a6cd0(techA)≠0 ∧ (techB)==0` (A:819-829); score
  `value0*64 + (l24+2)*pop*yieldX*64/clamp99(c4+c80) + (l14+2)*pop*yieldY*64/clamp99(c4+c80)`,
  strict `>` sets best-add to `-(k+1)` (A:877-882). Model m53p_recon_a.py:856-870 matches.
- Continuation after add commit (A:1005-1017): loop iff budget > c80+c7c ∨ bc > (pop+1)*K; swap
  branch always breaks. Exit publishes `base+0x78 = acc` (0x4e8b19) and `base+0x7c = DAT_008f0c68`
  RAW (A:1414 0x4e8b28).
All of the above already matched the model — no selection rule was missing.

## 2. Skip flag + budget (VERIFIED)
- Skip flag `[ebp-0x30]` = 1 iff **¬((1<<fac) & byte0(0x985b10)) ∨ (byte0(base+0x38)&0x40 ∧
  base+0x38 bit31)** (A:9-30, 0x4e790a-0x4e7933). The old note ("tile out-of-mask") was wrong.
  Live mask 0xff08 → flag = 1 for every faction except 3. Gates: pre-scan nibble repair
  (A:116-157), scan-0-special eviction part (A:273-275), facility tail (A:797-799).
- Scan-0 special runs only when the scan ended with `budget != c80+c7c` (A:264-269: 0x4e7c5e
  `je 0x4e8a47` skips special AND middle pass). Its tile scan is SKIPPED, without budget spend,
  iff acc bit 0 already set (A:368-369 `test BYTE [ebp-0x8],1 / jne 0x4e7ed2`); else it scans the
  base tile, acc|=1, budget-- (A:439-444).
- `DAT_008f0c68` has exactly **4 stores in all of .text**, all inside 4e78e0 (Ghidra
  shard_012.c:16023/16108/16229/16626; machine 0x4e7904 mov, 0x4e7c36 + 0x4e7ecd mov-after-dec,
  0x4e85d8 dec). Sole initializer: `movsx BYTE[base+6] + 1` = **pop+1 at visit time** (Ghidra's
  `(char)DAT_008f0d60[3]+1` is short*-scaled [3] = byte@6 — pointer-scale trap).

## 3. The finding (acceptance)
Plain replay (pop = dump byte@6) leaves 11 rows non-self-consistent; on ALL of them
**stored c7c == model budget_end + 1** (`evidence/m53r_sig.py`). Replaying with
`pop_visit = dump+1`: scan consumes pc(pool), ends with budget == c80+c7c → `je 0x4e8a47` →
special + middle pass SKIPPED → processed = pool = stored, vec = scan-only = stored vector,
published carry = stored c7c. **All three stored outputs reproduced simultaneously on 22/22
drift rows** — the 11 non-sc rows (37,40,42,44,52,55,58,61,64,70,72) plus 11 rows that were
mask-OK but carry-wrong (28,31,47,48,49,56,63,65,67,68,71). All 22 drift rows are fac 2; fac-2
idx 0/23 did NOT drift.
Census after recovery (run1): rows 76, **self-consistent 76 (was 65), exact 65 (was 54)**, 11
c4-only residuals UNCHANGED (1,3,5,8,30,34,46,51,60,62,69), cells bc 0 c0 0 c4 11 c8 0.
Implementation: `rebuild(pop_visit=)` + `recover_pop()` probe (accepts pop+1 only when it
reproduces stored mask AND stored carry; `--no-pop-recover` shows the plain view); header prints
`pop-drift=+1(pop a->b)`.
**INFERRED:** the extra budget unit = pop byte@6 was 1 higher at visit time, i.e. these bases
LOST a point after their rebuild visit (combat/attrition; cause open). Probe tries +1 only; no
row needs +2 (76/76 explains).
Open: why drift concentrates on fac 2; the c4-only residuals (saved c7c == budget_end → no
drift there); `c80_end != stored d80` on idx 24/35 (internal field, not published — eviction
accounting artifact).
