# M53p — session J findings (energy-only Class-J hunt)

Snapshot used: `evidence/m53o_mem/*` refreshed 09:06 (live pread cross-check `/tmp/j_snap2.py`:
year 2382, pid 2124624, TracerPid 0, DAT_008f0d30 = 257, DAT_0091c628 = 1, DAT_008f0c4c = 7,
DAT_00985b10 = 0xff08, DAT_0068cbb0 = 70, DAT_008f0d64 = 9841968).  The parent's census
(50/76, 12 energy-only rows) was measured on the EARLIER state (git HEAD copy in
`/tmp/old_mem/rows.json`: d30 = 1, g91c628 = 0, c4c = 6, c30 = 1, c6c = 1, k85afc = 281).
The live state has advanced since; the model's honest baseline on the current state is
18/76 (bc 45, c0 48, c4 42, c8 0) — see `evidence/m53p_j_count.py`.

## V1 (VERIFIED) — middle-pass scoring corrections: machine halves, model subtracted
`evidence/m53o_fn4e78e0_asm.txt` lines 648-676 (VA 0x4e815d-0x4e81b6):

    4e817f: lea edx,[ecx+edi*1]   ; edx = pop + pop*DAT_0092a27c  (pk1)
    4e8182: cmp ebx,edx / 4e8184: jg 0x4e81a0      ; ebx = [esi+0xbc] = vec[0]
    4e8186: test eax,eax / 4e8188: jne 0x4e81a0    ; eax = doubled nutrient
    4e818a: mov eax,[ebp-0x18]; 4e818d cdq; 4e818e sub eax,edx; 4e8190 sar eax,1
    4e8195: mov eax,[ebp-0x1c]; 4e8198 cdq; 4e8199 sub eax,edx; 4e819b sar eax,1
    4e81a0: test m / 4e81a7: test [ebp-0x4c] (local_50) / 4e81ae-4e81b6 same triple on [ebp-0x10]

`cdq` (0x4e818d/98/b1) OVERWRITES edx with the sign-extension mask (0 / -1) of eax, so
`sub eax,edx; sar eax,1` is C's truncate-toward-zero division by 2 of the value itself —
it is NOT `sar((value - pk1), 1)`.  The model (`scripts/m53p_recon_a.py` lines 796-801,
comment at 792-795) subtracted pk1.  Fixed copy: `scripts/m53p_j_fix.py`
(`ashr(bb - pk1,1)` → `sdiv(bb,2)`, same for cc and aa).  Effect on the current snapshot:
full-match 18 → 19 (idx 67 becomes exact), bc/c0/c4/c8 mismatch counts unchanged
(45/48/42/0 → 45/48/42/0); idx 53 c4 -7 → -1, idx 18 -4 → -3, idx 43 -2 → +3, idx 28 0 → +5.

## V2 (VERIFIED) — the model's FUN_004e7070 is faithful to the machine
Independent reimplementation written straight from `scripts/fn.py 0x4e7070` pseudocode
(`/tmp/fn7070.txt`, 233 lines, saved in this dir as `m53p_j_fn4e7070_pseudo.txt`) vs
`M.disp(2,...)` over every set bit of all 76 live masks: **0 tile-level disagreements**
(`/tmp/j_i.py`).  Same for the shared tail: `+1 if base+0x34 & 0x2000`, `-1 if (base+0x34 &
0x4000) and v != 0` (`/tmp/fn7070.txt` lines 209-216 vs model lines 392-394), the
`DAT_00985db8` -1, and the `DAT_0091c628 ? (DAT_00985dc4&2) : (&1)` ×3 selector (dead:
DAT_00985dc4 = 0).  Dispatcher `FUN_004e75f0` (`/tmp/fn5f0.txt`) is a pure 4-way switch,
case 3 only clears DAT_008f0cc8.

## V3 (VERIFIED) — middle pass cannot produce an energy-only delta
`/tmp/fn.txt` (fresh `scripts/fn.py 0x4e78e0` dump, saved as `m53p_j_fn4e78e0_pseudo.txt`):
every vector mutation is a 4-field loop `iVar3 = 0xbc … while (iVar15 < 0xcc)` through
`FUN_004e75f0(field, fac, DAT_0068cbb0, x, y)`: scan loop (pseudo lines 123-132), scan-0
fallback (243-252), swap-out subtract (491-500), swap-in add (524-533), undo subtract (557-566),
undo restore (589-597), middle-pass add (641-650).  All are inside the same bounds check that
gates the score (321 vs 481/514/548), so mask and vector stay consistent; a swap/add can
therefore never change only field 2.  Candidate loop = steps 1..20 only (pointer arithmetic:
`local_30 < 0x50` with `local_30 += 1` on an `undefined4*` = 20 iterations; XOFF read
`local_30[0x19e144]` = 0x678510+4i = XOFF[i+1]) — the model's `range(1,21)` is right, and the
"steps 21..79 alias inner bits" theory is dead.

## V4 (VERIFIED) — DAT_008f0cc8 is write-only in this path
All three yield functions only accumulate into it: nutrient 0x4e6cf5-0x4e6d03,
mineral 0x4e6ff4-0x4e7000 + 0x4e702a-0x4e7039 (`acc = cc8; cc8 = acc + v - cap; v = cap`),
energy 0x4e7571-0x4e7580.  Nothing adds it back into a yield, and `FUN_004e75f0` case 3
clears it after every committed tile, so it cannot carry energy across tiles.

## V5 (VERIFIED, decisive for the baseline shift) — DAT_008f0d30 is stale relative to the vectors
`FUN_004e63b0` (called at the very top of `FUN_004e78e0`, pseudo line 47) recomputes a
21-entry per-step table at 0x8f0ccc (writes 1/2/4/8/0x10/0x20 at 0x4e63e8, 0x4e6442,
0x4e6518, 0x4e6533, 0x4e6563, 0x4e659f, 0x4e6635, 0x4e6699, 0x4e68d6) and then
`DAT_008f0d30 = OR of nonzero entries` (0x4e6925-0x4e694f).  So the live value reflects
"now", not "then".  Proof it changed after the vectors were built: live `base+0x78` still
HAS bit 8 set (idx 6 d78 = 0xf2951, idx 47 = 0x9589, live pread), but 4e78e0 writes
`base+0x78 = local_c` at exit (pseudo line 692) and a bit can only enter `local_c` for step 8
if step 8 was scannable, i.e. if bit 8 was NOT in DAT_008f0d30 at that entry
(`base+0x78 &= ~DAT_008f0d30 | 1`, asm 0x4e796a-0x4e7972).  Live DAT_008f0d30 = 0x101 has
bit 8 → the blocked-step mask changed after the production pass, so the model's
`mask_in = live_mask & (~d30|1)` feeds a mask the game never used.  Consequence: for most
rows the model's own `processed` mask no longer equals the live mask (e.g. idx 47 mask_in
0x9489 → processed 0x12a089; idx 6 0xf2851 → 0xf2c51), i.e. the reproduction is not
self-consistent and the bc/c0 deltas on those rows are contaminated, not Class-J.
Self-consistent rows (mask reproduced exactly) on the current snapshot: 4, 10, 13, 17, 22,
26, 30, 33, 39, 40, 44, 46, 51, 55, 61, 67, 69, 70, 71, 74, 75.

## Class-J residue on the current snapshot (fixed model)
Energy-only rows (bc/c0/c8 exact, c4 off): {6: -3, 35: -2, 61: -2, 70: -1}
(`evidence/m53p_j_rows.txt`).  61 and 70 have `mask_in == processed` (self-consistent), so
their gap is a genuine per-tile energy shortfall; by V2 the per-tile function equals the
machine pseudocode evaluated on live memory, so the only remaining explanations are inputs
that changed between the rebuild and the snapshot (tile record level/u9/uc/owner byte 7,
facility bitmap at base+0x8c, base+0x30 bit 2, base+0x34 bits 0x2000/0x4000) or a different
DAT_0068cbb0 during that base's rebuild.  None is reachable from read-only preads of the
current state, and no machine-addressed branch in 0x4e7070/0x4e75f0/0x4e78e0 produces an
energy-only delta (V3, V4).  Ruled out this session: aliasing double-add (V3), cc8 carry
(V4), the ×3 selector and DAT_00985db8/DAT_00985dc4 (live 0), the seed block (halving
`(seed+1)/2` on missing facility 0x1d + `min(seed,pop)` — implemented, model lines 568-576,
and it cannot be energy-only), the fin 0x2000/0x4000 pair (implemented), the
`DAT_00985b48 == bidx` / `DAT_00985bc0 == fac` bonuses (implemented), the special-square
`improved(fac,2)` path, and the middle-pass candidate range.
