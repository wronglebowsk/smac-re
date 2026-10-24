# M53o — FUN_004e78e0 rebuild of base+0xbc/0xc0/0xc4/0xc8

Model `scripts/m53o_recon.py` (read-only; reads `m53o_mem/*.bin`); `python3 scripts/m53o_recon.py [idx ...]` (default = 7 pinned rows), `--legacy` = pre-fix variant (mask `base+0x78 & ~(d30|1)`). **[V]** verified vs machine code/live memory, **[I]** inferred. asm:N = `evidence/m53o_fn4e78e0_asm.txt` (1602 lines, corrected); pN = line N of `m53o_fn4e78e0.txt`.

## 1. Named sums [V]

`FUN_004e75f0(field,fac,bidx,x,y)`: field0→`4e6960` nutrient, field1→`4e6d40` mineral,
field2→`4e7070` energy, field3→returns 0 and clears `DAT_008f0cc8` ⇒ no tile term for 0xc8. The
vector has **exactly 7** add sites, all `mov DWORD PTR [edi+ecx*1-0x4],edx` (edi walks 0xbc step
4; all 7 lines checked; `grep 'add    DWORD PTR'` = 0 hits ⇒ each store is a MOV of a
computed sum): 249/0x4e7c15 scan-loop **+**; 433/0x4e7ea3 scan-0 special **+**; 998/0x4e85bd swap
sub-loss **−**; 1108/0x4e8739 swap add-gain **+**; 1186/0x4e883b undo sub-gain **−**;
1273/0x4e8951 undo add-loss **+**; 1343/0x4e8a32 non-swap add-gain **+**.

For F ∈ {0xbc→y0, 0xc0→y1, 0xc4→y2, 0xc8→0}: `base+F = seedF + Σ_scan yF + yF(scan0special) +
[−yF(loss)+yF(gain) −yF(gain)+yF(loss)] + Σ_nonswap yF(gain)`. Seed store 0x4e79a5 (asm:59) from
`0x94dc34+(fac*0x82f+field)*4`, live all-zero ⇒ seed 0. Tail loop 0x4e8b6f-0x4e8d48 writes only
`[base+0x48]` (0x4e8b60, 0x4e8d32), not the vector. Downstream (strip before comparing): bc +=
`DAT_008f0c6c` at 0x4e9344 (crawler; live 1 = the stale add baked into base 70 ⇒ its bc target is
12−1 = 11); c0 += `DAT_008f0c70` at 0x4e9459 (live 0); c0×2 gated on special-base owner
(`0x985ba8` = −1 ⇒ inactive); c0×(esi+2)/2 ×1.0; 0xc4/0xc8 have no downstream writers [V pinned].

## 2. Control flow [V]

* Entry: `base+0x30 &= 0xffff7fff` (0x4e7940); `base+0x80 = 0` (0x4e7952); `base+0x78 &=
  (~DAT_008f0d30|1)` (0x4e7968-72). Flag `[ebp-0x30]` = 1 iff `((1<<fac)&byte@0x985b10)==0` **or** (bit6
  **and** bit31 of `base+0x38`); live 0x08 ⇒ only fac 3 is flag 0. Gate `FUN_00507440(base+0x78) <= budget` (p94-97), budget = pop+1.
* Scan loop s=0..20 (cap `cmp eax,0x15` asm:261): s=0 always plus every mask bit in increasing s;
  budget-- per scan (OOB costs budget, adds nothing); break at 0. Then `if (budget == base+0x80 +
  base+0x7c) goto LAB_004e8a47` (p139) skips the scan-0 special case *and* the middle pass (needed:
  else base 70 overshoots c0 by 2).
* Middle pass (p298-655): swap mode iff `budget <= c80+c7c` (p299) = one attempt (needs
  `gidx>0 && lval<gmax && lidx>0`, p465) then **unconditional break** (the `break` at p601 sits
  inside `if (local_5c != 0)`). Non-swap: add best-gain tile, budget-- (asm:1343); or if the
  AI-table candidate won (`gidx<0`) write nibble `(-1-gidx)` to `base+0x84[c80]`, c80++ (p603-617);
  or break if no candidate. Continue while `(c80+c7c < budget) || ((pop+1)*2 < base+0xbc)` (p654).
* Candidate loop s=1..79 (p417), XOFF@0x67850c / YOFF@0x678990; exclusion `bit &
  (local_54|DAT_008f0d30)`, local_54 = processed (non-swap) or 0 (swap); mask bit `1<<(s&0x1f)` ⇒
  offsets 32..79 alias bits 0..15.
* Exit: `base+0x78 = processed` (0x4e8b19), `base+0x7c = DAT_008f0c68` (0x4e8b28), `base+0x30 &=
  ~0xfe00` (0x4e8b33), history shift 0xac←0xbc←… (0x4e8b39-54).

* `base+0x84` (16 nibbles) is **model output**: stores 0x4e7d5a/0x4e7d73 (340/345), 0x4e8497/0x4e84af (915/920),
  0x4e8ae2/0x4e8af8 (1399/1403); model feeds the observed post-state as input.

## 3. Yield functions [V]

Record = `*(0x92ae14)` (live 0x40a6ba8) + `(40*y+(x>>1))*0x2c`; u9=rec+8, uc=rec+12, cat=rec[0]&
0xe0, ocean = cat<0x60 (`bVar2`, 0x4e70b4). Constants 0x926bd8..0x926c64 = 9 groups x
(nutrient,mineral,energy,0), live: Ocean 1,0,0/Base 2,1,1/Bonus 2,2,2/Forest 1,2,1/Recycling
1,1,1/ImpLand 1,0,0/ImpSea 2,1,3/Monolith 2,2,2/Borehole 0,6,6.
Improved-square path (all 3 yields): `t = clamp(facrec[0x94d698+fac*0x20bc], -3..0)`,
`v = clamp0..99(facrec[0x94d744|748|74c][fac] + t)` — 0x4e6f0a/0x4e6f26 pin field 1; the clamp is
**0..99, not 1..99**. Facility bits = bytes at base+0x8c via `FUN_00507410`; base-index arg `DAT_0068cbb0` (live 0x46 = 70). y2 extras: +1 if `DAT_00985b48==bidx` (live 4 ⇒ base 4 gets +1/tile,
(needed for base 4's c4); +1 if `DAT_00985bc0==fac` (live 2, base-square branch only); +2 if `FUN_005831a0==3` (0x926c00); +1 if `u9&0x80 && cat>=0x60`; +1 if b3 (uc tests 0x4e711a-58, incl. `(uc>>24)<9` via `sar edi,0x18`@0x4e70b1); +1 if `1 <
facrec[0x94d67c][fac] + ((base+0x30&4)?1:0)` (0x4e7215 `test BYTE PTR [ebx+0x95da40],4`, ebx =
304*idx); cap 2 when `u6<0 && v>2 && !tech_avail(0x92a2cc=59) && code!=3`, excess → `DAT_008f0cc8`
(cleared by the field-3 call ⇒ never reaches 0xc8); LAB_004e7586: +1 if base+0x34&0x2000, −1 if
&0x4000, −1 if `DAT_00985db8`, ×3 if `DAT_00985dc4 & (0x91c628?2:1)` (live 0 ⇒ ×1).

## 4. Model vs observed (7 pinned rows; idx 70 bc target = 12 − stale crawler 1)

```
idx fac pop flag| bc   | c0   | c4   | c8
 70   3   7   0  | 11/11 |  7/7  |  3/4✗ | 0/0
  0   2   4   1  |  8/8  |  8/8  |  5/5  | 0/0
  3   4   4   1  |  8/10 |  6/8  | 10/15✗ | 0/0
  4   5   3   1  |  6/6  |  8/8  | 10/10 | 0/0
  6   7   9   1  | 25/25 | 12/12 | 17/19✗ | 0/0
 10   6   5   1  | 10/10 |  3/3  |  7/7  | 0/0
 23   2  12   1  | 30/27✗| 21/19✗| 14/12✗| 0/0
```
Full matches: **0 (fac2), 4 (fac5), 10 (fac6)** — 3 bases, 3 factions ✓. All 76 live bases: exact
per field **bc 56/76, c0 48/76, c4 46/76, c8 76/76**; **36/76 full matches, factions
{2,4,5,6,7}** [V].

## 5. Residual attribution

1. idx 70 (fac3 flag0, c4 −1): tile set forced by the observed mask (8 tiles, budget 8→0 ⇒
   jump-to-tail); no tile or swap pair over all 79 offsets has 4-vector (0,0,+1,0) ⇒ a
   FUN_004e7070 branch, not a missing add site [V-negative].
2. idx 6 (fac7, c4 −2): 6 swap pairs reproduce it (loss s=10 (10,66) → gain s=11 (6,66)), each
   needing an input mask ≠ the observed one ⇒ [I] swap on stale input.
3. idx 23 (fac2, +3/+2/+2): model swap fires, output mask ≠ observed, exit budget 1 ≠ observed
   `base+0x7c` 2 ⇒ pop 12 ≠ visit-time pop (13 reproduces c7c=2); 3 tiles carry exactly
   (3,2,2,0): (40,50),(43,53),(37,43) ⇒ [I] stale input state.
4. idx 3 (fac4, −2/−2/−5): no swap pair reproduces the triple; only row low on all 3 fields ⇒
   [I] visit-time tile set ≠ observed mask set.
5. Dominant class over all 76: **c4-only negative**, 12 rows, deltas −1…−5, factions 1,3,4,7
   (never 2/5/6) ⇒ [I] a +1 branch of FUN_004e7070 fires on a tile subset there; not the improved
   addend (0x94d74c ≠ 0 only for facs 1,4).
6. Only positive c4 row (idx 15, `base+0x30` bit2 set, +1) fits `1 < facrec[0x94d67c]+i10`
   tracking base+0x30 bit 2 at visit time [I].
7. 28 c0 mismatches, concentrated in fac 2 (model high +2…+5): unattributed; the pinned-inactive
   c0 multipliers are first suspects [I].
8. 0/76 rows fail the scan gate ⇒ the flag==1 else-branch nibble blocks (p142-256) are untested.

## 6. Corrections to evidence/m53o_findings.md

`base+0x78` entry mask is `& (~DAT_008f0d30|1)` (live 1; 0x4e6929/0x4e694f write it), not
`~(pop|1)`: bit 0 survives [V]. Vector-region cites drift ~10 low: use asm
249/433/998/1108/1186/1273/1343 [V]. Seed-loop gate = `facility bit 0x1d clear AND (special base <
0 OR its owner byte ≠ fac)`, owner read `(&DAT_0095da14)[spec*0x130]` byte 4 [V]. Improved path
clamps 0..99, not 1..99 (§3) [V].

## 7. Open

Identify the FUN_004e7070 branch behind the 12 c4-only rows (incl. base 70). Visit-time vs
live-time input state (pop, base+0x30 bit2, base+0x34, facility bitmap, input mask): the model is a
pure function of entry state, so post-visit mutations show as residuals (idx 3/23). flag==1
else-branch (scan skipped) nibble blocks unimplemented, unexercised. Whether `DAT_00985b48 == bidx`
is a real per-tile +1 or absorbed by idx 4. `0x8f0c30/c44/cc8` modelled as writes only.
