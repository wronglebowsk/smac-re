# `.MP` map format — decoded and verified

Two shipped maps, two different sizes, both decode with the *same* code path and the same
arithmetic. That is the evidence this is a format and not a coincidence:

| file | size | grid | cells | 22 B/cell | trailer |
|---|---|---|---|---|---|
| `maps/planet.MP` | 143,667 | 80×80 | 6,400 | 140,800 | 128 B |
| `maps/planetx.MP` | 363,525 | 128×128 | 16,384 | 360,448 | 338 B |

```
0        15 B     b"TERRANMAP\0"  0x1A  u32 version (=5)
15     2724 B     header struct (see fields below)
2739    W*H*22    cell records, row-major
+      var        trailer, starts b"????????"
```

`15 + 2724 + W*H*22 + len(trailer) == file size` exactly for both files.

Parser: `scripts/decode_map.py` (validates magic, dims, grid end and trailer marker; emits JSON).

## How it was established (not read off the decompiler)

A gdb breakpoint on the read wrapper `FUN_0064cc00` logged **caller, size, count and FILE\*** during
"THE MAP OF PLANET" on the game-setup screen:

```
caller=0x5822ac size=2724     -> FUN_00582260 reads the header struct
caller=0x5822f7 size=140800   -> the grid, 6400 * 22
caller=0x58231d size=128      -> the trailer
```

2724 + 140800 + 128 = 143,652, i.e. the file minus its **15-byte prefix**. That closes the
"5,459 unaccounted bytes" from the earlier static reading of `FUN_00597a70`, which turned out to be
the *save/scenario* path, not the map path.

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
| 5 | **3,200** | **8,192** | **land cells** — exactly half the grid in both files |
| 6 | 56 | 90 | unknown, scales with size (landmark count? rainfall setting?) |
| 7 | 0 | 0 | unknown |
| 8 | 30 | 31 | unknown |
| 9 | 9 | 109 | unknown |
| 10 | 21 | 71 | unknown |
| 11 | (ASCII in both) | (ASCII) | word 11 upward is **text** (map name/description) |

Words 3+ are not yet named; the point is the struct is fixed-size 2,724 B and its first two fields
are the dimensions.

## Cell record (22 B)

Per-offset statistics over all 6,400 cells of `planet.MP`. Bytes that take only power-of-two values
are flag bytes; bytes with many distinct values are numeric fields.

| off | distinct | shape | working name |
|---|---|---|---|
| 0-1 | 42 / 120 | numeric | elevation / altitude (u16?) |
| 2 | 38 | small enum | terrain type |
| 3 | 33 | enum | terrain subtype / vegetation |
| 4 | 6 | `00 10 12 02` | flags (rocky?) |
| 5 | 6 | `00 40 80 10` | flags (road?) |
| 6 | 7 | `00 80 20 a0` | flags |
| 7 | **6** | `ff`×3,200 / `00`×3,180 | **river / border mask** — half the map |
| 8 | 9 | `00 20 10 80` | flags |
| 9-14 | 8-11 | flags | bonus-resource / supply-pod / landmark ids |
| 15 | **141** | `ff`×2,728 | **ownership or landmark index** (only one with 141 values) |
| 16-21 | 8-10 | three u16s (`+16/+17`, `+18/+19`, `+20/+21`) | per-cell counters (nutrients/minerals/energy or morale) |

Not yet named: the exact bit meaning of 4-14 and the semantics of 16-21. The container is complete;
the fields are a separate, smaller job (see `MILESTONES.md` F1b).

## Trailer (variable: 128 B / 338 B)

Starts with eight `0x3F` bytes (`????????` in ASCII — this is a marker, not text), then small values
in the 0x0B-0x3F range. Length scales with map area (128/338 against 6,400/16,384 cells), so it is a
sparse per-cell list rather than a fixed struct. Consumers: the third read in `FUN_00582260`
(`size` comes from a global, i.e. it is computed from the file). Not yet decoded.

## Functions

| addr | name | evidence |
|---|---|---|
| `0x598340` | `file_open_and_dispatch(file)` | magic dispatch, version ≥5 (map) / ≥86 (save) |
| `0x582260` | `map_load_arrays(file)` | reads 2724 + 140800 + 128 from one FILE\* (gdb trace above) |
| `0x5821e0` | sibling of the above (mode≠0 path) | called instead when `DAT_00926a0c` != 0 |
| `0x597a70` | `load_save_or_scenario(file, mode, is_map)` | 796-byte header + XOR blocks — **not** the map path |

## Correction to earlier notes

`FUN_00597a70`'s 67,040 / 58,848 / 11,488 / 32 blocks and the XOR decoder `FUN_00596540` belong to
the **save/scenario** path. The `.MP` map grid is read raw, 22 bytes per cell, with no decoder.
The earlier "5,459 bytes unaccounted" figure came from adding those blocks against the map file size;
it is not a gap in the map format, it was a gap in my reading.
