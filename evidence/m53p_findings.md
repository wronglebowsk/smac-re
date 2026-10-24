# M53p — the entire remaining model divergence is the MIDDLE PASS of FUN_004e78e0

Live state for every number here: pid 2124624, year 2381, cur_player 3, nb 76, era 2,
mask 0xff08, TracerPid 0, game idle on our turn. All reads via `/proc/pid/mem`, read-only.

## 1. Census (re-run of the M53o model over all 76 bases) [V]

`python3 scripts/m53o_recon.py $(seq 0 75)` -> `evidence/m53p_all76.txt` (381 lines, per-scan
tokens `scanN@T:+v`, `mp-swap-in@T`, `mp-swap-out@T`); deltas parsed to
`evidence/m53p_deltas.tsv` (cols: idx, fac, pop, field, model, obs, delta).

- 36/76 bases exact on all four fields (same as session 67).
- Per-field mismatches: **bc 20 (3 neg / 17 pos), c0 28 (3 / 25), c4 30 (14 / 16), c8 0**.
  (Session 67 reported bc 56/76 — its delta census silently dropped `bc` because the parser
  matched only `c[0-9]`; the true bc count is 56/76 exact-matching bases overall.)
- **Class A — model HIGH, 25 rows: for every mismatched field the delta equals the sum of that
  row's own `mp-swap-in`/`mp-swap-out` contributions** (checked programmatically over all 76
  rows: 25/25 swap-attributed rows match to the unit; e.g. idx 32 swap-in@47 bc+4 swap-out@49
  bc-1 -> delta bc +3, c0 +2 = swap-in c0 +2, c4 +2 = swap-in c4 +2; idx 2 c0 delta +4 =
  swap-in@48 c0 +4; idx 65 c4 delta +3 = swap-in@59 c4 +3). The excess is carried ENTIRELY by
  the middle-pass swap-in tile, i.e. **the model performs a middle-pass swap the game did not**.
  These rows are almost all faction 2 (24 of 25 c0-positive rows are fac 2) and all have
  skip-flag 1. => session 67's residual classes 5/7 ("fac-2 c0 class", pinned-inactive c0
  multipliers) are NOT a yield-function problem and NOT the c0 multipliers.
- **Class B — model LOW, 15 rows with NO middle-pass tokens at all**: 14 rows are c4-only
  negative (deltas -1..-5, factions 1,3,4,7, never 2/5/6 — includes our base idx 70, -1);
  3 of those rows (idx 3 fac4, idx 7 fac4, idx 16 fac7) are low on bc+c0+c4 together; the
  single c4-positive row idx 15 (fac 7, +1) is also token-free. Consistent with **the game
  performing a middle-pass add-best-gain/swap the model does not** (a swap whose net is
  (0,0,+1) leaves bc/c0 exact, exactly the shape of the 14 c4-only rows).
- Class B rows are the ONLY rows that touch the yield math at all, and section 3 below shows
  the model's `y2` implements every +1 site in `FUN_004e7070` -> the missing energy is not a
  missing yield branch.

Mismatch table (machine-generated from `evidence/m53p_all76.txt`; do not hand-edit):

Machine-generated mismatch table: `evidence/m53p_deltas.tsv` (cols idx, fac, pop, field, model, obs,
delta) plus `evidence/m53p_all76.txt` (per-scan contribution tokens). 40 of 76 bases carry at least
one delta; the exact bases are printed by the model's `full-match:` line.

## 2. Live scenario/economy globals that gate the +1 branches [V]

`evidence/m53p_globals.txt` (read-only pread, pid 2124624) has the full dump; the load-bearing
values: `0x985b48 = 4`, `0x985bc0 = 2`, `0x985db8 = 0`, `0x985dc4 = 0`, `0x91c628 = 0`,
`0x926be0 = 0`, `0x926bf0 = 1`, `0x926c00 = 2`, `0x926c10 = 1`, `0x926c20 = 1`, `0x926c40 = 3`,
`0x926c50 = 2`, `0x926c60 = 6`, `0x92a2cc = 59`, `0x92a27c = 2`, `0x92a2a4 = 5`,
`0x92a378 = 0x92a37c = 80`, `0x92a394 = 0`, `0x692184 = 40`, `0x8f0c44 = 3`, `0x8f0cc8 = 0`,
`0x8f0c68 = 0`, `0x8f0d30 = 1`, `0x985afc = 281`, `0x68cbb0 = 70`.
- `0x985dc4 & 1 == 0` with `0x91c628 == 0` => the energy x3 multiplier at
  `evidence/m53p_fn4e7070.txt:226` is DEAD this game; `0x985db8 == 0` => the -1 at :218 dead.
- **`0x985bc0` has exactly ONE store in the whole cached `.text`: `0x425fc3`
  `mov DWORD PTR ds:0x985bc0,ecx` (line 48223 of `evidence/m53j_text.txt.gz`); `0x985b48`
  has NO store at all — its only `.text` reference is the `cmp` at `0x4e74e9` inside
  `FUN_004e7070` (line 299619).** => both are scenario/save-loaded constants, invariant across
  a round, so they cannot explain a per-visit difference. [V: exhaustive
  `zgrep -n '0x985bc0'` / `'0x985b48'` of the 790702-line cached disassembly.]
- Faction records base = **0x94ae14** + fac*0x20bc (verified by the DAT arithmetic:
  0x94ae14+0x2880 = 0x94d694, +0x2e18 = 0x94dc2c production total, +0x2e20 = 0x94dc34 = the
  4 seed dwords) — NEXT_PROMPT's "faction records 0x92ae14+f*0x20bc" is a typo; 0x92ae14 is
  the terrain-array POINTER [V].
- `facrec[+0x868]` = `*(int*)(&DAT_0094d67c + fac*0x20bc)` (the nutrient-support value the two
  `1 < facrec + i10` tests use) = {fac0 0, 1 0, 2 -2, 3 0, 4 1, 5 0, 6 0, 7 0}. With i10 in
  {0,1} the test at `evidence/m53p_fn4e7070.txt:187` can ONLY fire for faction 4 on a base with
  `base+0x30` bit 2 set; it is dead for every other faction [V].

## 3. `FUN_004e7070` +1 inventory vs the model's `y2` [V]

`evidence/m53p_fn4e7070.txt` (233 lines, args = (fac, bidx, x, y, flag5)); asm window
`evidence/m53p_fn4e7070_asm.txt` (475 lines). Every `+1`/multiplier site, with the model line
that implements it in `scripts/m53o_recon.py`:

| pseudocode line | guard | model line |
|---|---|---|
| :93 | `u9 & 0x40` neighbor loop: 8 offsets, neighbour `rec+8 & 0x800000` and `rec+7 == owner byte of cur base` | 448-460 |
| :123 | mineable path, base facility bit 1 -> `DAT_00926bf0 + 1` | 470 |
| :140 | mineable path, facility bit 3 OR bit 0x1a -> `+ DAT_00926c20` | 474-475 |
| :163-164 | `DAT_00985bc0 == fac` (live 2 => faction 2 gets +1 per mineable tile) | 486-487 |
| :167-168 | `u9 & 0x80` and tile is land | 402-403 |
| :170-171 | `FUN_005831a0(x,y) == 3` -> `+ DAT_00926c00` (= 2) | 404-405 |
| :173-174 | `bVar3`: terrain `rec+0xc` bits — `(uc&0x80000002)==2 && (uc>>0x18)<9`, or bit 3, or bit 10, or bit 11 | 385-386, 406-407 |
| :181-182 | `DAT_00985b48 == bidx` (live 4 => base idx 4, per tile) | 411-412 |
| :187-188 | `1 < facrec[0x94d67c] + (base+0x30 bit 2)` | 414-415 |
| :191-193 | cap-2 spill `DAT_008f0cc8 += local-2` (no-yield tiles, `FUN_005a6cd0(59,fac)==0`, `iVar7 != 3`) | 416-419 |
| :210-214 | `LAB_004e7586`: +1 if `base+0x34 & 0x2000`, -1 if `& 0x4000` and value != 0 | 390-395 |
| :218 | -1 if `DAT_00985db8` (live 0 => dead) | 396-397 |
| :226 | x3 if `DAT_00985dc4 & (0x91c628 ? 2 : 1)` (live 0 => dead) | 398-399 |

The model's `y2` (scripts/m53o_recon.py:375-489) covers every row of that table, and section 1
shows the c4 deltas are carried by middle-pass tokens, not by tile values: **the session-67
hypothesis "a +1 branch inside FUN_004e7070 explains the 12 c4-only rows" is REFUTED** [V by
the swap-token attribution + this inventory]. The c4-only shape is what a swap with net
(0,0,+1) produces.

## 4. Parent-verified correction to `evidence/m53p_mpass_findings.md` (main thread)

The child static read's headline — "the swap-commit block is DEAD CODE" — rests on the premise
`[ebp-0x54] == local_50 == (swap ? 0 : mask_acc)`. That premise is wrong: `test` does not modify
`eax`. `evidence/m53o_fn4e78e0_asm.txt` A:538-548 = 0x4e800a-0x4e8024 reads
`mov ecx,[ebp-0x4]` (j) / `mov ebx,ds:0x8f0d30` / `mov eax,1; shl eax,cl` (= 1<<j) /
`mov ecx,[ebp-0x50]` (= swap?0:mask_acc, stored at 0x4e8004) / `or ecx,ebx` / `test eax,ecx`
(the gate) / **`mov [ebp-0x54],eax` — stores eax, still 1<<j** / `jne 0x4e82ef` (excluded
candidates jump away). So A:770-778 (0x4e82bf-0x4e82ce) `mov ecx,[ebp-0x8]` (mask_acc) /
`mov eax,[ebp-0x54]` (= 1<<j) / `test ecx,eax; je 0x4e82db` means: **a candidate whose ring bit
is ALREADY in mask_acc (claimed by this visit's scan or by an earlier add) updates the SWAP pair
(strict `<`; swap idx [ebp-0x48] starts -1, swap score [ebp-0x44] starts 0x270f); every other
candidate updates the ADD pair (strict `>`; add idx [ebp-0xc] starts 0, add score [ebp-0x28]
starts 0)** [V]. Both pairs fill in one iteration, so the swap commit IS reachable: dispatch
0x4e8458 (A:894-899) sends flag != 0 to 0x4e8616, whose three guards each exit to 0x4e8a47
uncommitted — add idx > 0 (0x4e8618 `jle`), **add score > swap score, strictly** (0x4e8624
`cmp ecx,eax`, 0x4e8626 `jle`), swap idx > 0 (0x4e8631 `jle`) [V].
Frame map pinned from the disassembly [V]: [ebp-0x8] mask_acc (0 at A:32; reaches base+0x78 only
at exit A:1411), [ebp-0xc] best-add idx, [ebp-0x28] best-add score, [ebp-0x44] best-swap score,
[ebp-0x48] best-swap idx, [ebp-0x50] swap?0:mask_acc, [ebp-0x54] per-candidate 1<<j,
[ebp-0x58] swap flag, [ebp-0x4] j, [ebp-0x2c] loop counter (reads 0x678510+4*(j-1) = XOFF[j]).
Swap flag 0x4e7fd1-0x4e7fd6: `cmp edi,eax` with **edi = DAT_008f0c68, the budget global**, eax =
base+0x80 + base+0x7c, `setle bl` => swap mode iff `DAT_008f0c68 <= c80 + c7c` [V].
