# What the SMAC install ships — parse vs RE

> Reconstructed 2026-10-22 after accidental skill deletion; canonical source:
> `~/reverse/smac/DATA_INVENTORY.md` (measured prose) + `SAVE_FORMAT.md` + `MAP_FORMAT.md`.

Measured on the GOG install (`programs/`, 618 files, 47 MB):

| ext | files | size | status |
|---|---|---|---|
| pcx | 378 | 20.5 MB | standard PCX (PIL opens them; 1024×768 mode P) |
| cvr | 113 | 7.7 MB | custom "Caviar" voxel models — **decoded, 113/113 validated** (`cvr_decode.py`) |
| flc | 21 | 5.9 MB | standard FLIC (ffprobe: `flic 105x87`) |
| exe | 2 | 3.7 MB | `terran.exe` (the code under RE) + helper |
| txt | 32 | 0.65 MB | **the game's data model** — `alpha.txt`, `Script.txt`, etc., plain text |
| mp | 2 | 0.48 MB | `maps/planet.MP`, `maps/planetx.MP` — map data, header partially decoded |

Key point: two of three graphic containers are industry-standard (PCX, FLIC), the custom one
(CVR) is decoded, and the rules/content layer is **plain text** — so most "data format" work is
parsing, not RE.

## Text layer

- `alpha.txt` — rules: `#UNITS`, `#FACILITIES`, `#CHASSIS`, `#TECHNOLOGY`, `#FACTIONS`, etc.
  Parsed into `data/alpha.json`.
- `Script.txt` — dialog-box scripts (council, faction leaders, advisors). Parsed by
  `parse_script.py` → `script_parsed.json`.
- Runtime index vs file line index differs: **runtime item idx = `#FACILITIES` line idx + 1**.

## Map / save

- Map header in `.MP` partially decoded — see `MAP_FORMAT.md`.
- `.SAV` — mission year is a `u16` at file offset `0x54`; autosave slots rotate **in place**,
  so read the year rather than trusting the slot number. See `SAVE_FORMAT.md`.
- **The .SAV chunk map is HARD-CODED — there is no (address,size) table in the file** (M107, `scripts/m107_chunkmap.py --tag m107c3` PASS 7/7): `FUN_00596850` [0x596850,0x597a6b] contains **30 `fread` legs**, 25 of them `push <size>` immediates + 5 counted, in file order; 0 of the 20 static destinations occur as u32 LE in any of 9 saves and 0 (dest,size) pairs are adjacent. Sizes come from code, so a save splits only by replaying the legs. **Block A (0x94d430) is gated on `[0x985dbc]` >= 3** (`cmp ds:0x985dbc,3` @0x596a43): live it is **9**, so the **static 0x105e0 leg runs** (r7: direct read 0x94e104+0xf000) — 0x985dbc is a RUNTIME field, **NOT** file offset 772, and the file's u32@772 = 0 must not be used to pick the branch (that inference was wrong once). The counted legs are sized by the **live unit/base counts**: `[0x985af0]` = units (52n at 0x933278) and `[0x985af4]` = bases (304m at 0x95da10) — measured live 67/18 → **52n = 3,484, 304m = 5,472**, both EXACT; the count-prefix leg was **176**. `0x59738b` (a 48·n leg) and the 0xe5e0 malloc leg **do not execute** on m54b_clean, and `0x5979f8` is a **4-byte** read, not a tail section — the legs are GATED (0x596a43 `ds:0x985dbc,3`, 0x5974b7 `ds:0x985dbc,0`, 0x5974d3 `[0x985af4]`), so a chunk map needs each gate, not just each size. **Read a fread SIZE from `*(int*)($esp+4)`**, never a register the block has clobbered.

## Map + save container formats (verified — repo docs MAP_FORMAT.md / SAVE_FORMAT.md are canonical)

`.MP` map — `15 + 2724 + W*H*22 + trailer == file size`, checked on both shipped maps:
```
0        15 B   b"TERRANMAP\0" 0x1A u32 version(=5)
15     2724 B   header struct: u32 width, u32 height, ... (word 5 = land cells = W*H/2)
2739    W*H*22  raw cell records, row-major (no XOR)
+      var      trailer, starts b"????????" (128 B @80x80, 338 B @128x128)
```
planet.MP 80x80 143,667 B; planetx.MP 128x128 363,525 B. Parser `scripts/decode_map.py`.

`.SAV` save — `b"TERRAN\0" 0x1A u32 version(=86)`, 796 B header, mission year u16 at **+0x54**; then
sections read in a fixed order. **`FUN_00597a70` is the save/scenario block loader, not the map loader**
(the map grid is read raw by `FUN_00582260`); `FUN_00598340` is the magic/version dispatcher.

`.SAV` section sizes (from the `push` sites in `FUN_00596850`): 796, 67,040, 11,488, 16,000, 3,584,
26,624, 4,096, 256, 152, 10,144 are immediates; three are computed — one raw count (`DAT_00927538`), one
**52 B/record** (`edx` records), one **304 B/record** (`DAT_00985af4` records). Two are skipped outright
under version/count conditions, so the section list is conditional; sizes shrink as the game progresses.
`.SAV` is fully splittable from the file alone — `scripts/decode_save.py --sections` sums to the byte.
Key facts: u32 **own player at file offset 808**; a **u32 count prefix immediately before** one variable
section; the other two variable sections are `n × 52 B` and `m × 304 B` records, split by solving
`52n + 304m = region` and choosing on zeros-fraction (304 B records ~80% zero, 52 B ~40%).
Caller-scoped gdb condition that makes small reads loggable without flooding:
`break *0x64cc00 if *(void**)$esp >= 0x596850 && *(void**)$esp <= 0x597a6b`.
Anchors that pin a save's layout byte-exact (verified on two saves of different ages): map dims
`50 00 00 00 50 00 00 00` at **79,372** and `????????` at **222,896**; gap 143,524 = 2,724 + 140,800.
`scripts/decode_save.py --anchors` checks it.
**Pitfall:** never validate an offset by "fraction of identical bytes" — these files are mostly zeros, so
the match rate is flat across wrong offsets. Use a unique content signature instead.

### Technique that cracked both: runtime read trace, not static reading
Break on the read wrapper and log the **caller** and size:
```
break *0x64cc00 if *(int*)($esp+8) >= 64      # 0x64c9a0 is the sibling wrapper
commands
silent
printf "R3 caller=%#x size=%d count=%d file=%#x\n", *(void**)$esp, *(int*)($esp+8), *(int*)($esp+12), *(void**)($esp+16)
continue
end
```
- Unconditional breakpoints here fire **34,000+ times** (the game reads 1-2 bytes constantly) and slow it
  to a crawl; the `>= 64` condition is what makes the run usable.
- The caller address maps each read to its function, so the section order falls out in one run.
- Then close the arithmetic against the file size: if `sum(reads) + known_prefix == filesize`, the layout
  is complete. That is the check that distinguishes a real format from a guess.

## Graphics

- CVR: `cvr_decode.py` (validates 113/113), renderer output in `png/` (gitignored, regenerable).
- FLIC: decoded with standard tools; frames in `flc_out/` (gitignored, regenerable).
