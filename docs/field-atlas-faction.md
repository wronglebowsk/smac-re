# docs/field-atlas-faction.md — the 20 most-referenced faction-block displacements (generated)

Regenerate with `python3 scripts/m143_m162_atlas.py`. Displacements are `[reg+0x94dXXX]`, i.e. fields of the
8,380-byte per-faction block (0x94d104 + f*8380, **and** the folded `[reg*4+..]` form where reg = f*2095).
M143-M162 are these 20 rows, in this order. `in NAMED?` only means the address TEXT appears in NAMED.md or an
archived block; it does NOT mean the field has a meaning — grep those places before re-deriving one, and
treat a `—` as genuinely unnamed rather than as a gap to fill by guessing.

| # | field | refs | writes | shape | consts written | tested vs | top functions | in NAMED? |
|---|---|---|---|---|---|---|---|---|
| M143 | `0x94d448` | 653 | 27 | read-write | — | 0x1/0x10/0x10000/0x1000000 | ?, FUN_0040e720, FUN_00411d00 | named |
| M144 | `0x94d650` | 261 | 34 | read-write | — | 0x3e8/0x7d/0xa/dword ptr [eax+0x94d650] | FUN_0040d7a0, FUN_00416730, FUN_00419c30 | named |
| M145 | `0x94d434` | 196 | 1 | read-write | — | 0x2/0x4/0x5/0x6 | ?, FUN_00440710, FUN_0045a920 | — |
| M146 | `0x94d430` | 168 | 18 | read-write | 0x0 | 0x10000/0x1000000/0x10000000/0x200 | ?, FUN_00429950, FUN_0046a610 | named |
| M147 | `0x94dc84` | 89 | 8 | read-write | 0x0 | 0x0/0x1/0x2 | ?, FUN_00435680, FUN_00438ad0 | named |
| M148 | `0x94d80c` | 78 | 6 | read-write | 0x0/0x1/0xffffffff | 0x0/0x1/ecx | FUN_0040b960, FUN_004a5eb0, FUN_004dc100 | — |
| M149 | `0x94d468` | 75 | 8 | read-write | — | 0x2/0x20/0x2000/0x2408 | FUN_004dac30, FUN_004dad40, FUN_004dadd0 | — |
| M150 | `0x94d438` | 72 | 2 | read-write | — | 0x0/0x1/0x2/0x3 | ?, FUN_00417ee0, FUN_004282d0 | named |
| M151 | `0x94d78c` | 72 | 6 | read-write | 0x1 | dword ptr [eax*4+0x94d78c]/dword ptr [eax+0x94d78c]/dword ptr [ebx+0x94d78c]/dword ptr [ecx+0x94d78c] | FUN_0045a920, FUN_0048b9a0, FUN_004dfc10 | named |
| M152 | `0x94d81c` | 62 | 6 | read-write | — | 0x0/edx | FUN_0040b960, FUN_0041f0e0, FUN_004a5eb0 | — |
| M153 | `0x94d554` | 57 | 6 | read-write | — | 0x2/0x3/0x4/0x5 | FUN_004404a0, FUN_0045a920, FUN_004da2c0 | — |
| M154 | `0x94d734` | 57 | 4 | read-write | — | dword ptr [eax+0x94d734]/dword ptr [ecx+0x94d734]/dword ptr [edx*4+0x94d734] | FUN_0045a920, FUN_004eaa10, FUN_00522b70 | — |
| M155 | `0x94d758` | 51 | 12 | read-write | 0x5 | 0x0/eax | FUN_00412b50, FUN_0045a920, FUN_004b2280 | — |
| M156 | `0x94d488` | 49 | 22 | read-write | — | 0xa | FUN_004404a0, FUN_004da2c0, FUN_0052a720 | — |
| M157 | `0x94d7fc` | 47 | 8 | read-write | 0xffffffff | 0x0/0x58/dword ptr [ebx+0x94d7fc]/dword ptr [ecx+0x94d7fc] | FUN_0045a920, FUN_00499e70, FUN_0049c070 | named |
| M158 | `0x94d818` | 46 | 6 | read-write | — | 0x0/edx | FUN_0040b960, FUN_0041f0e0, FUN_004a5eb0 | named |
| M159 | `0x94d754` | 44 | 8 | read-write | 0x0 | 0x2 | FUN_00412b50, FUN_0045a920, FUN_004b2280 | — |
| M160 | `0x94d814` | 42 | 6 | read-write | — | 0x0/edx | FUN_0040b960, FUN_0041f0e0, FUN_004a5eb0 | — |
| M161 | `0x94d4e8` | 40 | 17 | read-write | 0x0 | 0x1/0x2 | FUN_0052a720, FUN_00533e70, FUN_00534180 | — |
| M162 | `0x94d4a8` | 38 | 26 | read-write | — | — | FUN_00502cd0, FUN_00507460, FUN_005076d0 | — |

Reading the table: a **read-only** row with many refs and no writes is either load-time data (M121's law)
or a field this build never writes; a **const-only** row is a flag/config written by the game itself;
**read-write** rows are the live state the reconstruction must model. Shape is evidence; meaning is not
implied by it, and 0x94d448 (653 refs, 139 functions) is the faction flag word whose bit 0x8000000 M129
found gating FUN_00546800.
