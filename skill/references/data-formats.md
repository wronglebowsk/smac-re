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
- **The .SAV chunk map is HARD-CODED — there is no (address,size) table in the file** (M107, `scripts/m107_chunkmap.py --tag m107c3` PASS 7/7): `FUN_00596850` [0x596850,0x597a6b] contains **30 `fread` legs**, 25 of them `push <size>` immediates + 5 counted, in file order; 0 of the 20 static destinations occur as u32 LE in any of 9 saves and 0 (dest,size) pairs are adjacent. Sizes come from code, so a save splits only by replaying the legs. **Block A (0x94d430) is gated on `[0x985dbc]` >= 3** (`cmp ds:0x985dbc,3` @0x596a43): live it is **9**, so the **static 0x105e0 leg runs** (r7: direct read 0x94e104+0xf000) — 0x985dbc is a RUNTIME field, **NOT** file offset 772, and the file's u32@772 = 0 must not be used to pick the branch (that inference was wrong once). The counted legs are sized by the **live unit/base counts**: `[0x985af0]` = units (52n at 0x933278) and `[0x985af4]` = bases (304m at 0x95da10) — measured live 67/18 → **52n = 3,484, 304m = 5,472**, both EXACT; the count-prefix leg was **176**. `0x59738b` (a 48·n leg) and the 0xe5e0 malloc leg **do not execute** on m54b_clean, and `0x5979f8` is a **4-byte** read, not a tail section — the legs are GATED (0x596a43 `ds:0x985dbc,3`, 0x5974b7 `ds:0x985dbc,0`, 0x5974d3 `[0x985af4]`), so a chunk map needs each gate, not just each size. **Read a fread SIZE from `*(int*)($esp+4)`**, never a register the block has clobbered. **The loader alone cannot close the map**: a live census of its 116 read sites (`scripts/m109_leg_census.py --tag m109c4`) executes **23 sites = Σ(size×count) 149,380 B of 242,539 (61.6%)**; the other **93,159 B is read by callers outside [0x596850,0x597a6b]** (105 reader sites; the 86,016-B heap read is one). Instruments: a breakpoint **conditioned on `*($esp)` freezes the game** (gdb stops on an undereferenceable register; the load driver then never gets past the menu — that is how four runs logged 0 loads) — use STATIC bps at the loader's own call instructions; and gdb printf needs the two chars `\`+`n` built in code (`chr(92)+"n"`), `%#x` for addresses (a bare `%x` gives `break *596883` → Invalid number), and no leftover `%%` from Python formatting.

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
`.SAV` splits from the file alone, but **`decode_save.py --sections` sums to the byte only for 128×128 saves**:
its `MAP_SECTIONS = 2724 + 140800` hard-codes that grid, while a 64×64 save's map is `2,724 + 90,112 + 91 =
92,927` (`FUN_00582260`), so the constant over-runs the file and every later offset is wrong — on this box it
dies with `no 52/304 split of a 0-byte region` on all nine saves. Derive the map size from the header dims
(`MAP_FORMAT.md`'s `15 + 2724 + W*H*22 + trailer`) before believing any offset after it.
**Never close a save layout by subset-sum.** With the map corrected and `52n + 304m` free, m54b_clean's
242,539 B admits **181,769** exact decompositions of the candidate legs (auto1 182,718, auto30 184,074) — an
answer set that size names nothing. Constrain with content (anchors, per-stride zeros-fraction) or with pokes
(`references/instrument-laws.md` §Identify bytes).
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

### `.SAV` trailer — the last 156 B (s171, M111/M112)

Every save on this box ends with a **fixed trailer**: the last **152 B are byte-identical** across m54b_clean
(242,539 B) and the 8 autosaves (242,815 / 242,875 / 242,919 / 242,927 / 242,971 / 243,483 / 243,691 B) — only
the FINAL dword differs (365,402,425 / 766,622,009 / 746,214,987 ...). Layout: 5 x `[id,0,0,-6,32,32]` for
id 3..7, then `[1,1,0x80000080,-14,32,32]`, then `[800,387,X]`. The file size varies, so the trailer's OFFSET
varies per save: no hard-coded leg can index it, and any "reads the last 156 B" claim has to be a per-file seek.
It is **not** the loader's 152-B immediate leg — `0x597716` pushes 152 but its destination `0x92bf58` holds
`[9999,9999,0,0,2100,2600]`, not the trailer rows. After a load the 156 B is absent verbatim from 523 MB of
memory; its 12-B row signature (`fa ff ff ff 20 00 00 00 20 00 00 00`) sits 6x in ONE heap block (0x34f0000)
and in 0 of the 24 files in programs/, i.e. the rows reach memory as records, not as a block read.
**The reader is the 6-site per-entity loop** (`0x59666d`, `0x5966c1`, `0x596715`, `0x596769`, `0x5967bd`,
`0x59683b`), which restores each `[id,0,0,-6,32,32]` row (id 3..7) into heap records at `0x915758`,
`0x3b7d7a8`, `0x3b9fc60`, `0x3bc2118`, `0x3be45d0`, `0x3c06a88`, `0x3c28f40`, `0x3c4b3f8` (stride `0x224B8`)
and `0x8eb7c4`. Proved by identification, not arithmetic: `scripts/m112_trailer_poke.py --tag m112p1` plants
`0xCAFEBABE` in the rows of a save copy, loads it, and finds the pattern 41x in /proc memory (load rc=0,
counts 67/18); the structural hits are those loop destinations minus 8. **A census sum over-runs the file
(+468 on m54b_clean, +144 on an autosave) because its cumulative `file_off` assumes file order while these bytes
are touched twice — bulk and per row.** So "the last 156 B are unread" is wrong; do not gate on a byte sum.

### `.SAV` offset -> memory anchors (s171, m113map1 — pokes, 20/20 found)

`scripts/m113_save_map.py --tag m113map1 --relaunch --step 16384` plants `0xC0DE000i` at 16 KB offsets and at
candidate section starts in a save copy, loads it, and searches memory for each marker: 20/20 found, 0 absent,
load rc=0, counts 67/18, 522.7 MB scanned. Inside a section the mapping is 1:1 (three slope-1 runs):
```
16,384..65,536  -> 0x951104..0x95d104        block A
81,920          -> 0x92ad6c                  map header
98,304..163,840 -> 0x40aa5b0..0x40ba5b0      the 90,112-B grid at 0x40a6660
172,287         -> 0x15e2baf                 map trailer region
180,224         -> 0x987d51
188,291/188,467 -> 0x989cd4 / 0x930e20       176 B apart = the 0x930d7c count prefix
196,608..212,992-> 0x98bf49..0x98ff49        slope 1
218,675/222,771 -> 0x99157c / 0x92cfe4       4,096 B apart
229,376         -> 0x95e635
```
Region boundaries are where the destination JUMPS. A band refinement (`--band lo-hi[:step]`, 25 markers at
2 KB: `--tag m113map2`) brackets them: block A -> block B between **66,048 (0x95d304)** and **68,096
(0x927684)** — the 67,840 split falls inside; grid -> next section between **171,192 (0x40bc268)** and
**173,240 (0x986209)**, with the 91-B map trailer (file 172,200..172,291) inside that bracket; 174,000..180,144
-> 0x986501..0x987d01 at step 0x800. The 52-byte record array maps 1:1 with an odd base: **file 222,783 -> 0x933278** (222,896 -> 0x9332E9,
223,024 -> 0x933369, every +128 B giving +0x80, to the byte). One offset reads ABSENT and **the absent one
MOVES**: 223,048 (dest 0x933351 = record 4 byte 9) in m113map2, 223,152 (0x9333E9 = record 7 byte 5) in
m113map3, each with present neighbours 128 B away — so it is NOT an unread region: individual dwords in the 52-B
records are rewritten by post-load processing (which is also why a read census over-ran). **Restore fidelity (s171, M114 + correction):** diff the loaded game against the save with the mapping
`dest = off + k`, where **k is per region**. With per-region k the file is CLEAN: block A 66,048..67,840
(k=0x94D104) 0 diffs; block B 67,852..79,328 (k=0x916C84) 0 diffs; map header 79,364..82,088 (k=0x916D6C) 2 bytes,
both at the first offset; grid 82,088..172,200 (k=0x40925B0) 10 bytes, starting at the first offset. So the save is
restored **1:1**; only the leading bytes of the header/grid and the 52-record array's 2 dwords diverge. **A diff
window that straddles a region boundary compared with one region's k manufactures diffs that look exactly like
rewriting** — an earlier version of this note claimed two "rewritten tails" that were only that artifact. Use
`scripts/save_diff.py`: it derives the regions from the anchors, refuses a range that crosses a known boundary
(67,852 / 82,088 / 172,200 / 172,291 / 222,783) and names it (`test_save_diff.py` PASS 7/7). `m54a_load.py` returns
**4** when the HUD is reached but its liveness probe fails — with counts correct that is a GOOD load; judge a map
run on the anchors and counts, not on that probe (`m113_save_map.py` accepts rc 0 and 4, fails only 1/3). The harness
refuses 60+ markers on purpose: that many pokes mutilate counts and pointers and the load stops meaning anything. This is the only
instrument that has held on this file: a read census over-ran its own file (+468, +144) and a subset-sum over the
legs admits 181,769 exact decompositions, while an anchor is an exact (offset, address) pair.
