# M53Q2 — main-thread audit of the `0x8f0ccc` writer decode

Independent check of `evidence/m53q_8f0ccc_writers.md` (child-produced) against the cached disassembly
`evidence/m53j_text.txt.gz` (line numbers below are `zgrep -n` line numbers in that file).
Scope: I verified the INSTRUCTION STREAM and the address arithmetic only. The SEMANTICS of each bit
(why visibility/order/stance mean what they mean) are the child's reading and stay INFERRED here.

## Verified store sites into the 21-dword table (9 sites, `[reg+0x8f0ccc]`, reg = 4*step)
| VA | asm line | instruction | value |
|---|---|---|---|
| 0x4e63e8 | 298155 | `mov [ecx+0x8f0ccc],0x1` | 1 (DECOY, see below) |
| 0x4e6442 | 298184 | `mov [ecx+0x8f0ccc],0x2` | 2 |
| 0x4e6518 | 298261 | `mov [eax+0x8f0ccc],0x2` | 2 |
| 0x4e6533 | 298269 | `mov [ecx+0x8f0ccc],0x0` | 0 |
| 0x4e6563 | 298284 | `mov [ecx+0x8f0ccc],0x4` | 4 |
| 0x4e659f | 298305 | `or  [eax+0x8f0ccc],0x8` | |=8 |
| 0x4e6635 | 298352 | `or  [eax+0x8f0ccc],0x8` | |=8 |
| 0x4e6699 | 298388 | `or  [eax+0x8f0ccc],0x20` | |=0x20 |
| 0x4e68de | 298575 | `mov eax,[ecx+0x8f0ccc]` / `or al,0x10` (0x4e68dc, line 298574) / `mov [ecx+0x8f0ccc],eax` | |=0x10 |

## Corrections to what NEXT_PROMPT/skill said before this milestone (VERIFIED)
1. **The mask build is INSIDE `FUN_004e63b0`, not in `FUN_004e78e0`.** 0x4e6925 (`xor edx,edx`, line
   298595) … 0x4e6946 (`cmp eax,0x8f0d20`, line 298606) are followed by **`ret` at 0x4e6959** (line
   298614). Consequence: `DAT_008f0d30` is built AFTER both passes, so the `|0x10` bits (other-base step
   overlap, written 0x4e68de) DO enter the mask; the entry filter therefore sees the fully-populated table.
2. **Value 1 never lands in the table.** At 0x4e63e3/0x4e63e6 the store is guarded `cmp ecx,0x54 / jl
   0x4e63f7` (line 298153-154), and `ecx` is the BYTE offset (proof: `add ecx,4 / cmp ecx,0x54`
   at 0x4e68e4-0x4e68e7). So 0x4e63e8 only fires for byte offsets >= 0x54 = index >= 21, writing
   0x8f0d20+ — outside the 21-dword window. Nothing reads those slots (only the `cmp eax,0x8f0d20`
   bound). Entries are therefore only ever {0,2,4,8,0x10,0x20} combinations.
3. **`DAT_008f0c68` is set in the CALLER**: 0x4e7904 `mov ds:0x8f0c68,ecx` (line 300041), immediately
   after `call 0x4e63b0` at 0x4e78e9 (line 300033, `e8 c2 ea ff ff` = rel32 to 0x4e63b0, no args pushed
   — the callee reads its base from `*(0x8f0d60)`).
4. `DAT_008f0c4c` is NOT written by either function (child's negative; consistent with `0x8f0c4c` being a
   score denominator set elsewhere: 0x4e8dbc / 0x4e90e0 / 0x4f3063 / 0x4f3110 — NOT re-verified here).

## Still INFERRED (not checked by me)
Which predicate each 2/4/8/0x20 branch actually tests (tile visibility bit, order 3, hostile stance
`&3==0`, the dist<=5/<=2 loops) — that rests on the child's reading of the branch bodies, which I did not
re-read. Treat those as INFERRED until a live dump confirms a mask against a computed one.
