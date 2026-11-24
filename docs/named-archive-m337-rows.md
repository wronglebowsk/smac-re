# NAMED archive — M337 rotation

Verbatim rows moved out of `NAMED.md` to keep it under the 250,000 B fail line.
Each region keeps its original `## <id>` heading and table bytes.


§rotation-1 (M277, s318-chain1 headroom rotation)
## M277 (s218, PASS 6/6) - the scaled read is the permanent block-0 view; M274 G2's spill landing is arithmetically dead

| fact | evidence | status |
|---|---|---|
| the two read sites of +0x94eaa8 are fed by DIFFERENT frame slots: UNSCALED 0x558452 `mov ax,[edi+0x94eaa8]` with 0x55844b `edi=[ebp-0x18]` (the fold 8380*arg+2*region) = block arg's row; SCALED 0x5584aa `mov cx,[edi*2+0x94eaa8]` with 0x5584a5 `edi=[ebp-0x10]` (region counter) = NO block term | `scripts/m277_scaled_row_ownership.py` G1, `evidence/m277_scaled_row.txt` | V (bytes) |
| the region-loop domain is i in [1,127] (init 1 at 0x557f9e, one in-loop store 0x558b22, tail `inc ecx; cmp ecx,0x80; jl 0x557fb8`) so the scaled byte offset range is [2,254] and the last byte touched is +255 | G3 | V (bytes) |
| the sibling verdict array 0x94eba8 starts +256 past 0x94eaa8 (= slot index 128), so regions 94..127 land in +188..+255 = 68 B of rows 94..127 INSIDE the row's own cell, NEVER the sibling: **M274 G2's "reads the sibling's [0..66] band" is refuted** (that band is offsets 256..322, unreachable) - M274's own printed max 254 < 256 | G4 | V, CORRECTS M274 G2 |
| live replay, 7/7 recorded SCALED events: 2*edi in [2,2] = block 0 for all while s18 = 2*s10+8380*cp walks blocks 1..7 with cp=1..7 - rival "scaled carries 8380*cp" refuted 7/7 | G5, `evidence/m273w3.gdblog` | V (live log, offline) |
| image-wide referrer census of +0x94eaa8 = exactly 4 sites (0x51df61, 0x558452, 0x5584aa, 0x564ab1); the ONLY two WRITERS (`inc WORD`, `add WORD,0xfff6`) both evaluate to eax = 8380*block + 2*slot -> per-faction-block live row, and the auto-manager's scaled read is the only block-free accessor = permanent faction-0 view | G6 (m276 evaluator reused) | V (bytes) |
| M278 REFINEMENT (s219): the permanent faction-0 view above is the **player-index-0 row** - the writers' block atoms are owner-player bytes (base+4 / unit+14, M43 identity) - AND it doubles as the landing cell for FUN_0051dcb0's unowned-tile clamp (-1 sentinel -> block 0, sign-test at 0x51df1d); it is NOT a neutral slot and NOT the player's slot (the recorded human is index 3). 0x94e8a8 (0x51df3d) still shares the same fold shape - the row family is wider than 0x94eaa8 (still OPEN) | `scripts/m278_block0_semantics.py` G1-G6, `evidence/m278_block0.txt` | V, block-0 question CLOSED by M278 |

Acceptance: `python3 scripts/m277_scaled_row_ownership.py` -> `SUMMARY M277: 6/6 gates PASS`; zero box time.

(§rotation-1 ends; nothing below it belongs to this region.)
