# NAMED.md archive - M255-M258 (rotated VERBATIM at s307, the M329 headroom rotation)

Source: the `NAMED.md` block starting `## M255 (s201, PASS 8/8)` up to the next `## ` heading
(`## B7`): 36 lines, 6734 B, sha1 `9111d3b24758` - asserted byte-exact by `scripts/m329_named_rotate.py`.
`NAMED.md` keeps a one-line-per-claim stub with the same gates and cites.

## M255 (s201, PASS 8/8) — `FUN_0057ecf0` is the NEW GAME caller of the world generator

| claim | evidence | conf |
|---|---|---|
| `FUN_005b2970` has exactly 4 call sites, one per caller: `0x4e1151`, `0x4e122b`, `0x57d2a0`, `0x57f1ec` | G6, `evidence/m253_region_categories.txt:6` | V |
| gates: `FUN_0057c550`'s site is skipped by 2 branches targeting the return point (`je`/`jne 0x57d2a5`) on `ds:0x9264d8` (written only at `0x57e495`=1 and `0x57e900`=0, read only in `FUN_0057c550`/`FUN_0057e890`) and `bl & 2`; `FUN_0057ecf0`'s is ungated and preceded by 6 stores to the world-dimension globals `ds:0x92ad??`; `FUN_004e10c0` ORs `0x80` into `ds:0x985ae8` before its call, `FUN_004e11b0` ANDs `0x7f` | G6, `:6` | V |
| modes from the literals: `FUN_0057ecf0` = {FACTIONS, WORLDSIZE, SCENARIO, INTRO} + 2 calls to the alpha-section opener `FUN_005ea431`; `FUN_0057c550` = {RULES, USERULES, RELOADFAC, DIFFICULTY, CUSTOMNAMES, FACTION} + 0 such calls; the `0x80` pair has NO literals; callers: `FUN_00512b40` (BASE/MAP CHECKSUMS, EDITINTERLUDE) + `FUN_00516b80` (MENUDETAIL, REALLYQUIT, TECHRANDOM) for the pair, `FUN_0057e890` (MAPMENU, maps\planet.mp) + `FUN_0057f740` (TOPMENU/SCENARIOMENU) for `57c550`, `FUN_00522850` (movies\virtualWorld.wve, opening) + `FUN_0057f740` for `57ecf0` | G7, `:7` | V |
| **exactly ONE caller satisfies ungated + world-dim stores + alpha-section reads + scenario literals: `FUN_0057ecf0`** = new game (read #FACTIONS/#WORLDSIZE from alpha.txt, set the world size, generate). `FUN_0057c550` = the scenario/MAP-FILE load path; `FUN_004e10c0`/`FUN_004e11b0` = the menu/editor REGENERATE pair (accept vs retry-vote allowed) | G8, `:8` | V (discriminators), INFERRED (naming) |

**M256 (s202, `scripts/m256_worth_operands.py` G1-G3, PASS 8/8, static, no box):** the worth test whose boolean decides 7 vs 8 (M253), operands pinned.

| claim | evidence | conf |
|---|---|---|
| the test is `cmp edx,ecx` at `0x5584b4` with `jle 0x5584e3` -> 0; fall-through leg2 `cmp eax,ecx` at `0x5584d8` (`jge 0x5584e3` -> 0, else `mov ecx,0x1`); legs ANDed, then `or eax,ecx` at `0x5584eb` with the 4-bit reason word, and `test eax,eax` at `0x5584fe`/`0x558509` is the ZF `sete dl` (`0x55850e`) consumes | G1-G2, `evidence/m256_worth_operands.txt:5-6` | V |
| LHS = 2 * ((DWORD[block+0x94d810] - DWORD[block+0x94d818] + [ebp-0x60]) * [ebp-0x3c]) — loads `0x55848f`/`0x558495`, `0x55849b`, `imul edx,edi` `0x5584a2`, `shl edx,1` `0x5584a8`; [ebp-0x3c] = BYTE[block+region+0x94e5a8] (the M94 multiplier, loaded `0x558053`, published `0x55805d`) | G3/G5, `:7,9` | V |
| [ebp-0x60] has 4 stores in FUN_00556690 (`0x558010` loop-head reset, `0x5580b9` fold accumulate, `0x558424`, `0x558905`); the one live at `0x55849b` is `0x558424` = 3 + (ds:0x985afc > 75) + FUN_00531090(ds:0x985b30, 0) adjusted by ([block+0x94e488] > 4 ? -((ds:0x985ae8>>7)&2) : 0) + (BYTE[block+region+0x94eca8] < 4 ? 1 : 0) + the fold count [ebp-0x68] | G3, `:7` | V (chain), OPEN (why the fold sum is overwritten) |
| reason word [ebp-0x54] = bit3 of WORD[0x94e7a8+row] \| mult >= 0x14 \| WORD[0x94eaa8+row] - WORD[0x94eba8+row] < 4 \| (mult != 0 and the 0x94eca8 byte < 2), assembled `0x558469`-`0x55848c` over the `0x558439`/`0x558444` bit0 store | G4 window, `:8` | V |

**M257 (s202, same run G4-G5):** the RHS operand and the row address.

| claim | evidence | conf |
|---|---|---|
| RHS = WORD[0x94eaa8 + 2*region] (`0x5584aa`, region = [ebp-0x10]) + WORD[0x94eaa8 + esi] (`0x558452`), summed by `add ecx,eax` at `0x5584b2` after `xor ecx,ecx` at `0x5584a0` (eax unwritten from `0x558452` to `0x5584b2`) | G4, `:8` | V |
| esi = [ebp-0x18] = 2*region + 188*arg1: fold `0x558002`-`0x558026` (`add eax,edi; lea eax,[edi+eax*2]; shl eax,0x4; sub eax,edi; lea esi,[ecx+eax*2]; shl esi,1`), published `0x558038`; arg1 = the pushed faction (callers `0x52094f`, `0x59dd43`) | G4-G5, `:8-9` | V |
| region loop = [ebp-0x10] init 1 (`0x557f9e`), `inc ecx; cmp ecx,0x80; jl 0x557fb8` (`0x558b1b`-`0x558b25`) -> 128 regions; 0x94eaa8 refs image-wide = 4 (inc `0x51df61` FUN_0051dcb0, -10 `0x564ab1` FUN_0055f650, the two reads here) | G4-G5, `:8-9` | V |
| ~~OPEN: 188-byte rows vs 2 bytes/region means regions 94..127 pass the next row — a stride conflict the image cannot settle~~ **RESOLVED (M273, s213, live)**: the live region COUNT is 91 (== save-derived `((W+4)/5+1)/2×H`, pre AND post stable) < the 94-slot row, so on the live 64×64 map NO spill is reachable; 188 = 2×94 is a fixed capacity, NOT derived from the block stride (8380 mod 188 = 108, and the live row register advances by whole 8380 strides). **M274 (s214) CLOSED the migrated spill question statically**: the loop has ONE bound (the constant `cmp ecx,0x80` at 0x558b1c, no clamp to 94 anywhere in the body) and the SCALED reads of regions 94..127 (max 2×127=254 B) land INSIDE the sibling verdict array at 0x94eba8 (gap 256) - silent wrong data on big maps, not a crash. The row slot [ebp-0x18] has 15 writers in the body -> the cursor's origin is a def-use pick, NOT the fold (whose multiplier is E+edi, re-derived from bytes; 8380 mod 188 = 108). Sparse events explained: a nonzero verdict byte stores 0x8 at 0x557fdf and jmps 0x558b18, skipping BOTH read sites | G5, `:9` + `evidence/m273w3.gdblog`, `scripts/m273_rowstride_watch.py --replay` 7/7 | CLOSED (was OPEN) |

**M258 (s202, same run G6-G8):** the per-region array family and the 8-slot fold's sources.

| claim | evidence | conf |
|---|---|---|
| 0x94e4a8, 0x94e5a8, 0x94e628, 0x94e6a8, 0x94e7a8, 0x94e8a8, 0x94e9a8, 0x94eaa8, 0x94eba8, 0x94eca8, 0x94ed28, 0x94eda8 (end 0x94ee28) = 12 per-region arrays; every gap is 0x80 (byte per region: B=97, 10, 6, 2, 79) or 0x100 (word per region: W=23, 22, 13, 2, 2, 4, 5), ZERO DWORD accesses anywhere, 128 entries each from the region bound | G8, `:11` | V |
| **RETRACTION of the s201 row** "0x94e7a8 flag bytes": it is a per-region WORD array (whole-word ops `0x5577e9`/`0x5577f8`/`0x5580d6`/`0x5580ed`, 28 refs to the +1 high byte), gap 0x100 | G8, `:11` | V |
| the 8-slot fold (0x558075-0x5583ac) walks WORD[0x950764 + 2*region] and BYTE[0x950664 + region] stepped by the faction stride 0x20bc over 8 slots, doubling the pair per set bit of BYTE[block+0x94d44c]; accumulators [ebp-0x60] (`0x5580b2`-`0x5580b9`), [ebp-0x6c] (`0x5580aa`-`0x5580af`), count [ebp-0x68] (`0x5580be`-`0x5580c5`) | G6, `:10` | V |
| the fold's second row is 0x200 below (`mov bx,WORD PTR [eax-0x200]` `0x558082` = 0x950564 + 2*region) and 0x950564 is its own table base (`lea esi,[esi*2+0x950564]` `0x4f7a0a`); both tables lie past the file image (3,067,904 B -> ends at VA 0x6ed000), so their extents/row counts are not statically readable | G7, `:11` | V (pcs), OPEN (extents) |

