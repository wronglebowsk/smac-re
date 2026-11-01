# `.MP` map format — decoded and verified

Two shipped maps, two different sizes, both decode with the *same* code path and the same
arithmetic. That is the evidence this is a format and not a coincidence:

| file | size | grid | records | 44 B/record | region map |
|---|---|---|---|---|---|
| `maps/planet.MP` | 143,667 | 80×80 | 3,200 = (W/2)·H | 140,800 | 128 B |
| `maps/planetx.MP` | 363,525 | 128×128 | 8,192 = (W/2)·H | 360,448 | 338 B |

```
0        15 B     b"TERRANMAP\0"  0x1A  u32 version (=5)
15     2724 B     header struct (see fields below)
2739   (W/2)*H*44 terrain RECORDS, row-major — the live 44-byte records, verbatim
+      var        coarse region map (128 B / 338 B), starts b"????????"
```

`15 + 2724 + (W/2)*H*44 + (((W+4)/5 + 1)/2 * ((H+4)/5)) == file size` exactly for both files — and
the last term is not arithmetic fitted to the file: it is `DAT_0092ada4`, computed by `FUN_00582000`
from the header's own width/height words (`evidence/m240_terrain_repack.txt:2-3`).

**M240 corrects the container.** The grid was read as `W*H` cells of 22 B because `W*H*22 ==
(W/2)*H*44` — the same bytes either way. The loader decides: `FUN_00582260` reads the grid into the
array `FUN_00582000` allocated as `((W/2)*H) * 0x2c` with NO transform loop, so the unit is the
**44-byte record**, the live grid is `(W/2) × H` tiles, and one record covers TWO adjacent map
columns (`record = base + ((W/2)*y + (x>>1))*0x2c`, `x` = file column). The "22-byte cell" is half a
record and is only a valid view of bytes 0..21.

Parser: `scripts/decode_map.py` still splits the grid into 22-byte cells (magic/dims/marker checks
are unaffected); `scripts/m240_terrain_repack.py` reads the same bytes as records.

## How it was established (not read off the decompiler)

A gdb breakpoint on the read wrapper `FUN_0064cc00` logged **caller, size, count and FILE\*** during
"THE MAP OF PLANET" on the game-setup screen:

```
caller=0x5822ac size=2724     -> FUN_00582260 reads the header struct
caller=0x5822f7 size=140800   -> the grid = 3200 records * 0x2c, into DAT_0092ae14 verbatim
caller=0x58231d size=128      -> the coarse region map, into DAT_0092ae18
```

2724 + 140800 + 128 = 143,652, i.e. the file minus its **15-byte prefix**. That closes the
"5,459 unaccounted bytes" from the earlier static reading of `FUN_00597a70`, which turned out to be
the *save/scenario* path, not the map path. The 140,800 is the record array itself — the same read
size the allocator asked for (`FUN_00582000`), so the load is a verbatim fill (M240).

Runtime corroboration of the dimensions: the setup screen offers "THE MAP OF PLANET" and "HUGE MAP
OF PLANET"; the two files are 80×80 and 128×128, and the game reads the 80×80 one when you pick the
first option.

## Header struct (2,724 B, at 15)

Read as u32 LE, first words:

| word | planet.MP (80×80) | planetx.MP (128×128) | note |
|---|---|---|---|
| 0 | 80 | 128 | **width** |
| 1 | 80 | 128 | **height** |
| 2 | 27,067 | 24,262 | unknown (map checksum/seed?) |
| 3,4 | 0 | 0 | unknown |
| 5 | **3,200** | **8,192** | **the record count `(W/2)·H`** — NOT "land cells" (M240): the loader recomputes that product from words 0/1 and never reads word 5, and the water/land split by the live rule is 1,826/1,374 and 5,143/3,049 |
| 6 | 56 | 90 | unknown, scales with size (landmark count? rainfall setting?) |
| 7 | 0 | 0 | unknown |
| 8 | 30 | 31 | unknown |
| 9 | 9 | 109 | unknown |
| 10 | 21 | 71 | unknown |
| 11 | (ASCII in both) | (ASCII) | word 11 upward is **text** (map name/description) |

Words 3+ are not yet named; the point is the struct is fixed-size 2,724 B and its first two fields
are the dimensions.

## Terrain record (44 B) — what the live code reads

The record IS the file bytes, and the accessor family `0x582390..0x583c70` names the fields. The
distinct-value column counts the 3,200 records of `planet.MP`; `evidence/m240_terrain_repack.txt:10-11`
carries both maps (`:10` planet, `:11` planetx).

| off | distinct | shape | field |
|---|---|---|---|
| 0 | 39 | `cat<<5 \| low5` | **category** in bits 5-7 — `FUN_005823c0` writes `& 0x1f \| (char)param_3 << 5`; cats 0..6 only, 7 never. `FUN_005831a0` branches on `cat<2`, `cat<3`, `2<cat`, and the pressure-recycle site tests `(rec[0]&0xe0) < 0x60` on the base's tile (`shard_001.c:3515-3517`, `:3546-3549`) ⇒ **cat 0-2 = water, 3-6 = land**: 1,826 water / 1,374 land on planet.MP, 5,143 / 3,049 on planetx.MP. B1's "cats 1-6 are 100 % land, cat 0 is 59/3259" was the 22-byte view mixing record byte 0 with record byte 22 (cat 0 in 100 % of records) |
| 1 | 120 | numeric | unnamed; `FUN_00582390` writes the byte, `FUN_00582a10`/`0x582a60` read and modify it |
| 2 | 33 | **two nibbles** | high = **terrain type** (`FUN_00582cc0`: `& 0xf \| param_3 << 4`; 0..15 all used in both maps, no gaps), low = **owner** (`FUN_00582c80` modifies the low nibble with `& 0xf`; only {0..7, 0xf} ever appear, `0xf` = unowned) |
| 3 | 31 | enum | unnamed; `FUN_00582d00` writes the whole byte |
| 4-7 | 1 / 3 / 6 / **1** | dword | seen bits (FOOTING.md). In the file byte 4 is 0 everywhere and **byte 7 is the CONSTANT 0xff in every record of both maps (3,200 + 8,192 = 11,392)** — B1's "land marker" and FOOTING's "+7 = owner byte" are both RETRACTED (M240) |
| 8-11 | 4 / 6 / 6 / 6 | dword | **mask** (`FUN_00582ea0` writes it, `FUN_00582ed0` read-modify-writes it, 78 callers); file values sit on bits 5, 7, 8, 20, 30 |
| 12-15 | 9 / 4 / 1 / **141** | dword | list head / uc; `FUN_00582f70` writes the byte at +15 (`& 0xffffff \| param_3 << 0x18`); +15 is the only field with 141 values |
| 16-43 | 32-34 per slot | **7 dwords** at +16,+20,+24,+28,+32,+36,+40 | **copies of the record's own mask dword**: all seven slots equal in 3,145/3,200 (planet) and 8,192/8,192 (planetx) records; each equals `+8` in 8,191/8,192 fresh-map records, and in planet.MP 1,100 records hold a strict SUBSET of the mask (bit 5 cleared 814×, bit 20 344×, bit 30 101×). `FUN_0051c750` (kelp/forest growth spawn) takes `iVar5 + 0x10`, walks dword slots 4..7 and sets/clears in slot 4 the same bits it clears in the tile's own `+8` (`shard_013.c:9451-9465`). No other reference to bytes ≥ 0x10 exists in the image (census lines `:14-17` of the evidence). Meaning OPEN |

Not yet named: the meaning of 1, 3, 4-7 and 12-15, and what the seven mask copies are for. The
container is complete; the fields are a separate, smaller job (see `MILESTONES.md` F1b).

## The coarse region map (128 B / 338 B) — not a trailer

Starts with eight `0x3F` bytes (`????????` in ASCII), then small values in the 0x0B-0x3F range. Its
length is not a file-side mystery: `FUN_00582000` computes `DAT_0092ada4 = ((DAT_0092ad9c + 1)/2) *
DAT_0092ada0` with `DAT_0092ad9c = (W+4)/5` and `DAT_0092ada0 = (H+4)/5` (`shard_014.c:27263-27266`),
which is 128 for 80×80 and 338 for 128×128, and `FUN_00582260`'s third read puts it in `DAT_0092ae18`
(allocated with the same expression). So it is a second array sized from the dimensions — a
`(W+4)/5 × (H+4)/5` region grid, ~1 byte per 25 tiles — not a trailer and not a sparse per-cell list.
`FUN_00582340`/`FUN_00582360` are its accessor pair. Not yet decoded beyond that.

## Functions

| addr | name | evidence |
|---|---|---|
| `0x598340` | `file_open_and_dispatch(file)` | magic dispatch, version ≥5 (map) / ≥86 (save) |
| `0x582000` | `terrain_alloc_arrays` | `DAT_00692184 = W/2`, `DAT_0092a38c = (W/2)*H`, `DAT_0092ae14 = FUN_005be090(count*0x2c)`, `DAT_0092ae18 = FUN_005be090(region)` (`shard_014.c:27258-27266`) |
| `0x582170` | `terrain_default_records` | per record `+0=0x20, +1=0x14, +2=0xf, +3..+7=0, +8=0, +0xc..+0x1f=0` over `DAT_0092a38c` records; `DAT_0092a380 = rand+1` (`shard_014.c:27290-27322`) |
| `0x5821e0` | `map_write_arrays(file)` | the save-side mirror: writes 2724 + `count*0x2c` + region (`shard_014.c:27326-27338`) |
| `0x582260` | `map_load_arrays(file)` | three sized reads, verbatim, allocator between #1 and #2, no loop/goto in the body (`evidence/m240_terrain_repack.txt:4-5`) |
| `0x583a70` | `terrain_post_load` | copies five 113-B terrain-type tables from `.rdata` into `0x7cdd08/0x7cde04/0x7f0778/0x7f07ec/0x7f0860`, then walks every tile clearing 5 rows of two of them where the tile's `+0xf` byte is negative and `+8` has bit 1 or bit 0 (`shard_014.c:28435-28530`) |
| `0x597a70` | `load_save_or_scenario(file, mode, is_map)` | 796-byte header + XOR blocks — **not** the map path |

## Correction to earlier notes

`FUN_00597a70`'s 67,040 / 58,848 / 11,488 / 32 blocks and the XOR decoder `FUN_00596540` belong to
the **save/scenario** path. The `.MP` map grid is read raw, with no decoder and — M240 — no repack.
The earlier "5,459 bytes unaccounted" figure came from adding those blocks against the map file size;
it is not a gap in the map format, it was a gap in my reading.

## The file cell vs the live terrain record — ANSWERED (M240, s191)

`python3 scripts/m240_terrain_repack.py` → `PASS M240: 6/6 gates on planet.MP, planetx.MP`
(`evidence/m240_terrain_repack.txt`). B1's two findings stand in corrected form: byte 2 IS two nibbles
(terrain type / owner, both live-confirmed by `FUN_00582cc0` and `FUN_00582c80`); the category question
was an artifact.

1. **There is no transform.** `FUN_00582260` reads `count*0x2c` bytes of grid directly into the array
   `FUN_00582000` just allocated (`count = (W/2)*H`, stride `0x2c`); its body has no loop and no goto.
   The 44-byte record and the 22-byte "cell" are the same bytes; only bytes 0..21 are the tile's fields.
2. **The category mismatch was the 22-byte view mixing halves.** Record byte 22 is the third byte of a
   mask copy and carries cat 0 in 100 % of records, so "cat 0 = 59/3259 cells" was 3,200 fake cats plus
   the 59 real ones. The file's cat field IS the live `rec[0]&0xe0` category, and cat<3 = water
   (`shard_001.c:3515-3517`): 1,826 water / 1,374 land on planet.MP, 5,143 / 3,049 on planetx.MP.
3. **Header word 5 is the record count** `(W/2)*H`, not the land count — and the loader never reads it.
4. Still OPEN: what the seven mask copies at +16..+43 mean and who fills them when a map is GENERATED
   (the load path only reads them in); the meaning of record bytes 1, 3, 4-7 and 12-15; whether the
   half-width indexing changes B2's save/parity test.
