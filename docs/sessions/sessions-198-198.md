# Session notes archive — sessions 198-198

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 198 (2026-11-01, M248/M249 ANALYSE — the region map's byte VALUES, and terrain record +3)

`python3 scripts/m248_region_values_census.py` -> `PASS M248: 5/5 gates` (2nd invocation, rc=0;
1st 3/5 on TWO instrument bugs, both fixed, no threshold moved) -> `evidence/m248_region_values.txt`.
Corpus = 17 saves + planet.MP + planetx.MP (19 files); zero box time, programs/terran.exe read for
rodata (file offset = VA - 0x400000).

**M248 — what the coarse region-map bytes mean.** `FUN_0058ce00` (shard_015.c:4690-4752) BUILDS the
map: for each region (x = row&1 step 2 < Rw, y < Rh) it samples 9 tiles at (x*5+dx, y*5+dy) with the
(dx,dy) pairs read from the image at 0x67850c/0x678990 = centre (0,0) then the 8 ring neighbours
(1,-1)(2,0)(1,1)(0,2)(-1,1)(-2,0)(-1,-1)(0,-2), x wrapped mod DAT_0092a378, y only bounds-checked
vs DAT_0092a37c, and stores **terrain record +3 of the first sample whose +0 & 0xe0 > 0x5f (land)**,
0 when no sample is land (G1 9/9 checks). The stored bytes are reproducible from the grid by that
rule **byte for byte: 19/19 files, 1809 written cells, 0 mismatches, 38 samples needed the x-wrap**
(G2). The array has exactly ONE reader function and ONE writer function: readers of FUN_00582340 =
`FUN_00556690` (shard_014.c:3450, 3469 — it uses the byte as a coarse label filter, then expands to
the fine grid with the same 9 offsets from 0x6784a0/0x6784c4, ring-first); writer of FUN_00582360 =
`FUN_0058ce00` (shard_015.c:4739); its other 17 direct refs are alloc/free/file-I/O/null-guards/
clears, all in shard_014.c (G3).

**M249 — what terrain record +3 is: the map's REGION LABEL, assigned at generation.** Its only
writer in the image is the byte setter `FUN_00582d00` (shard_014.c:27745,
`*(undefined1 *)(DAT_0092ae14 + 3 + (DAT_00692184*param_2 + (param_1>>1))*0x2c) = param_3`): of the
18 stores into the record array, exactly 1 covers byte 3 and it is that setter; the setter has 4
call sites, all in shard_015.c's map-generation code — :4862/:4892 in `FUN_0058d120`, :5086/:5097 in
`FUN_0058d390` (G4). The +3 plane is IDENTICAL across all 17 saves (1 distinct plane) which span 5
distinct turn values (file 80: 50,51,52,53,60) -> gameplay never rewrites it. Value semantics
(G5, 0 exceptions on 19/19 files): **+3 < 0x40 on every land tile, +3 >= 0x41 on every water tile,
0x40 never appears**; distinct land ids scale with map area — 18 at 64x64, 25 at 80x80 (planet.MP),
62 at 128x128 (planetx.MP); water ids are 6-8 values (41-48, 7f). Readers use it as an INDEX into a
per-faction byte array (`[param_2 * 0x20bc + (uint)*(byte *)(DAT_0092ae14 + 3 + ...)]`,
shard_012.c:2681-2683) and test `a < 0x40 == b < 0x40` (shard_012.c:7336). Ids are reused across
disconnected groups (planet.MP: 25 ids over 47 land components) and 130/16626 land adjacencies
differ, so it is a labelled partition, not a component id.

**RETRACTION:** my own first reading of G4 ("no store lands on +3") was wrong — the width parse
dropped the `*(type *)` cast (leading spaces), so every store got w=0 and `off<=3<off+0` is never
true; the byte setter at +3 was in the output all along. The 1st invocation also failed G1 (my
consumer-table comparison dropped the wrong centre) and G3 (4 `if (DAT_0092ae18 != 0)` null-guards
unclassified). Instrument bugs, not findings; gates re-ran whole.

**OPEN:** who calls the region builder / the two generators (FUN_0058d120, FUN_0058d390) and in what
order at NEW GAME; what the 0x20bc per-faction block at DAT_0094eda8 is (faction-known regions?);
what FUN_00556690's search is FOR (its callers: FUN_005208f0 shard_013.c:11666, FUN_0059ce10
shard_015.c:14862); whether +3 is ever re-assigned by terraforming (no store found outside the
generators, so no); the 7 mask copies at record +16..+43 still unnamed.
