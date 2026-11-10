# Session notes archive — sessions 200-200

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 200 (2026-11-01, M250/M251/M252 ANALYSE — who assigns the region labels, in what order, and who reads them)

`python3 scripts/m250_region_generation.py` → `SUMMARY PASS: 7/7 gates on terran.exe (static image,
no box)`, rc=0, 2.7 s, ONE invocation → `evidence/m250_region_generation.txt`. Static only: objdump
of `programs/terran.exe` (regenerated, 40 MB, kept in `scratch/`, not tracked) + `ghidra_out`. No
preflight, no `/proc`, no gdb; terran.exe untouched.

**M250 — the region generator and its ORDER.** `FUN_0058d390` (0x58d390, 1293 B) has exactly 3 call
sites, image-wide (G1): `0x5add8f` in `FUN_005add30`, `0x5af0c7` in `FUN_005af0c0`, `0x5b09e3` in
`FUN_005b09b0`; the generator driver `FUN_005b2970` (shard_015.c:28040-28115) calls the first two
and has 4 call sites (`FUN_004e10c0`, `FUN_004e11b0`, `FUN_0057c550`, `FUN_0057ecf0`). In the driver
the order is `FUN_00582170` (default records) → placement loop (`FUN_005ad970` ×, `FUN_005adbc0(4)`)
→ `FUN_005add30` → **`FUN_0058d390`** → `FUN_005aef40` → the while-condition `FUN_005af0c0()` which
re-runs `FUN_0058d390` and returns "retry" (up to 4 attempts while `DAT_00985ae8 & 0x80 == 0`); the
third caller `FUN_005b09b0` is the "ADJUSTING WORLD CLIMATE" stage (22 call sites) that re-runs the
generator after the climate pass. Inside `FUN_0058d390` (G2/G3/G4): clear `+3` over every record
(store `0x58d3b8`, step `add ecx,0x2c`, back edge `0x58d3c7→0x58d3b8`) → parity-2 tile scan whose
back edges `0x58d5fa→0x58d3f9` and `0x58d60c→0x58d3e2` both enclose the flood-fill call
`0x58d47e` → the two border-ring calls `0x58d649`/`0x58d6c3` → stats + adjacency → and
**`FUN_0058ce00` (the coarse label map) is the LAST call before the free `FUN_005e9e0d`
(`0x58d88c`, `0x58d891`): no back edge encloses it**, so the coarse map is built after every id is
assigned. Id bands from the body's immediates (G4): land `1..0x3e`, water `0x41..0x7e`
(`0x40` never assigned — the counter is pre-incremented), and when a band is exhausted the smallest
region in it is relocated to the overflow slot `0x3f`/`0x7f` (shard_015.c:5007-5073), which is why
M249 saw "25 ids / 47 components". Region table `DAT_00989ce0`, stride `0x1c` = 7 dwords reached
through the `lea [r*8+0]` + `sub r` fold (8 sites), dword 0 = tile count, `+0x14` = an 8-byte bitmap
of adjacent opposite-class regions written by the land/water border pass (`FUN_00507410` bit index).

**M251 — `DAT_0094eda8` is the per-faction, per-REGION category byte** (G5): 79 refs in 18
functions, **6 store sites in 2 writers** (`FUN_00556690` ×5 at 0x557fdf/0x558516/0x558549/0x55855e/
0x55856b, `FUN_0055f650` ×1 at 0x564ad7), values written exactly `{0, 2, 7, 8}`; addressed
`[region + faction*0x20bc]` (shard_014.c:2159/2217/2220 spell it out) and the stage's region loop is
`cmp reg,0x80` at 0x556737/0x558b1c → **128 entries = the whole id space**. Sibling arrays in the
same block, same index: `0x94e4a8` (short ×128, ends exactly at `0x94e5a8`), `0x94e5a8` (the byte
SCORE the pick loop compares), `0x94e628` (cleared per region each pass), `0x94e7a8` (flag bytes).
Effects pinned, NAMES OPEN: `< 2` is a preferred expansion candidate (+1000 bonus,
shard_014.c:3409-3411), `== 7` is accepted at its face score (:3429), `== 8` only when the region is
small (`DAT_00989ce0[region] < 0x96` = 150 tiles, :3439) and it also raises `FUN_00556370`'s divisor
2→4 and decrements `FUN_00556150`'s 1..10 score; `== 2` blocks the pick and forces `FUN_00556370` to
1. At the top of each pass the four reserved ids (`id & 0x3f` ∈ {0, 0x3f} → 0, 0x3f, 0x40, 0x7f) with
score 0 are stamped 8 (:3188-3191) and every water id ends the pass at 7 (:3583).

**M252 — what the coarse label search is FOR** (G6/G7): the coarse accessor `FUN_00582340` is
called at exactly 2 sites in the whole image, both inside `FUN_00556690` (`0x55878a`, `0x558812`) —
the coarse region map has ONE consumer. `FUN_00556690` (14 349 B, called only from `FUN_005208f0`
`0x52094f` and `FUN_0059ce10` `0x59dd43`, G7) walks the coarse grid by its own dimensions
(`DAT_0092ad9c` × `DAT_0092ada0`, 7 refs), keeps the cells whose label equals the candidate region,
turns a coarse cell into terrain coordinates (`x = cell*5`, `local_68 = local_44*5`), scans the
neighbour footprints for land tiles and scores them, then gates the best site by the terraform cost
`FUN_004cc7b0` (2 calls) against the faction's budget and issues
`FUN_0056d350(faction, 0x29, 2, x, y, -1)` — the 2 `push 0x29` sites (`0x556a47`, `0x558ad9`) each
reach a `call 0x56d350` 3 instructions later. So the coarse map is the spatial index by which the AI
finds where a region IS; the per-faction category/score arrays say whether it wants it.

**OPEN.** The names of categories 0/2/7/8 (only their effects are pinned); the internal order of the
M249 {4,5,6} question and every earlier pick's OPEN item stand. `FUN_005b2970`'s 4 call sites are
counted but not attributed to modes. No retraction.
