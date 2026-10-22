# DATA INVENTORY — what the install actually ships (M10a, 2026-10-20)

Measured on `~/reverse/smac/programs` (the GOG install, 618 files, 47 MB).

```
find . -type f -printf '%s\t%p\n' | awk ... group by extension
```

| ext | files | size | status |
|---|---|---|---|
| pcx | 378 | 20.50 MB | **standard PCX** — verified: PIL opens `Cursor.pcx` as 1024×768 mode `P` |
| cvr | 113 | 7.69 MB | **decoded, 113/113 validated** (`cvr_decode.py`) |
| flc | 21 | 5.86 MB | **standard FLIC** — verified: ffprobe reports `flic 105x87` on the first one |
| exe | 2 | 3.72 MB | `terran.exe` (the code, analysed) + a helper |
| txt | 32 | 0.65 MB | **the game's data model** — see below |
| hlp | 1 | 0.62 MB | Windows help (low value) |
| ttf | 5 | 0.52 MB | fonts |
| mp | 2 | 0.48 MB | `maps/planet.MP` (143 KB) + `maps/planetx.MP` (363 KB) — map data, **header partially decoded, see below** |
| dll | 1 | 0.37 MB | support DLL |
| tmp | 26 | 0.14 MB | junk |

Takeaway for the roadmap: **G2 (data formats) is nearly done and was never the hard part.**
Two of the three graphic containers are industry-standard (PCX, FLIC), the custom one (CVR)
is already decoded, and the actual *rules and content* are plain text.

## Text files — the content layer (32 files, 0.65 MB)

| file | size | what it is (evidence) |
|---|---|---|
| `Script.txt` | 238 K | **dialog-box scripts** — header says "Dialog box scripts"; semicolon comments, plain text. The scripted-conversation layer (council, faction leaders, advisor). |
| `Blurbs.txt` | 54 K | unit/base/tech blurbs |
| `alpha.txt` | 50 K | **the rules file** — header: "Alpha Centauri User-Configurable Rules … reads the rules of the game from this file". `#SECTION` blocks of comma-separated values, each line commented. This is the balance data a reimplementation must load: `#RULES` has road movement, nutrient intake, artillery damage, tech discovery rate, etc. |
| `help.txt` | 50 K | in-game help text |
| `tutor.txt` | 47 K | tutorial script |
| `concepts.txt` | 39 K | concept entries |
| `Interlude.txt` | 32 K | interlude/narrative text |
| `TECHLONGS.TXT` | 31 K | long tech descriptions |
| `labels.txt` | 17 K | UI labels |
| `movlist.txt` | 11 K | movie list |
| `FACTION.TXT` | 9 K | faction table |
| `flavor.txt` | 8 K | AI flavour text |
| `UNIV.TXT`, `GAIANS.TXT`, `HIVE.TXT`, `MORGAN.TXT`, `PEACE.TXT`, `SPARTANS.TXT` | 3 K each | per-faction definitions (University, Gaians, Hive, Morgan, Peacekeepers, Spartans, Believers) |
| `TECHSHORTS.TXT` | 5 K | short tech names |
| `menu.txt`, `planets.txt`, `monument.txt`, `system.txt`, `SCENARIO.txt`, `facedit.txt`, `holobook.txt`, `jackal.txt`, `basename.txt` | 1–5 K | UI/menu, planet names, scenario + faction-editor config |
| `BELIEVE.TXT`, `CREDITS.TXT`, `readme.txt` | 3–10 K | docs |

## Why this matters for the reimplementation

1. **Rules are external** (`alpha.txt`) — do not reverse-engineer balance constants out of the
   exe. Parse the file; the exe merely loads it. Same for faction definitions and tech text.
2. **The map format is a file, not code** — decode `maps/planet.MP` and a reimplementation can
   load the shipped Planet map and the map generator's output.
3. **Scripts are a mini-language** (`Script.txt`, 238 K). If the reimplementation wants the
   same scripted dialogs, this is the grammar to implement — and it is *data*, so it can be
   validated against the original by diffing rendered strings.
4. **Art is cheap to support**: PCX + FLIC via existing libraries; CVR via `cvr_decode.py`.

## Revised format priorities (replaces the guesswork in ROADMAP §Phase 0.4)

| priority | target | why | next step |
|---|---|---|---|
| 1 | `alpha.txt` grammar | complete rules table, human-readable | write `parse_alpha.py` → JSON; cross-check 3 values against runtime globals |
| 2 | `maps/planet.MP` | only unknown binary that is *content*, not art | **magic + loader found** (`FUN_00598340` → `FUN_00597a70`, 796-byte header then a 58 848-byte block); next: dump the header at runtime |
| 3 | `FACTION.TXT` / `UNIV.TXT` etc. | faction wiring for a playable reimplementation | parse; map fields to exe globals |
| 4 | `Script.txt` | dialog scripting language | extract statement keywords to a grammar sketch |
| 5 | `flc` / `pcx` | art | use existing decoders; no RE needed |
| 6 | exe-internal tables | anything not in alpha.txt | covered by the Ghidra export (index.csv) |

## `maps/*.MP` — DECODED (2026-10-20, verified on both shipped maps)

Full write-up: **`MAP_FORMAT.md`**. Parser: `scripts/decode_map.py`.

```
0        15 B     b"TERRANMAP\0"  0x1A  u32 version (=5)
15     2724 B     header struct; u32 width, u32 height, ... (land cells at word 5)
2739    W*H*22    cell records, row-major
+      var        trailer starting b"????????"  (128 B for 80x80, 338 B for 128x128)
```

- `planet.MP` = **80×80**, 143,667 B, trailer 128 B. `planetx.MP` = **128×128**, 363,525 B,
  trailer 338 B. `15 + 2724 + W*H*22 + trailer == file size` exactly for both.
- Established by a **runtime read trace** (gdb on `FUN_0064cc00`, logging caller/size/FILE*):
  `0x5822ac` 2,724 · `0x5822f7` 140,800 · `0x58231d` 128, from one FILE* = 143,652 = file − 15.
- Corroboration: header word 5 = 3,200 (planet) and 8,192 (planetx) = exactly half of each grid;
  the setup screen's "THE MAP OF PLANET" loads the 80×80 file.
- The grid is **raw** — 22 bytes per cell, no XOR. The XOR decoder `FUN_00596540` belongs to the
  save/scenario path.

### Corrections to the earlier reading of this section

- `FUN_00597a70` is **not** the map loader. Its 796 + 4 + 67,040 + 58,848 + 11,488 + 32 blocks are
  the **save/scenario** path. The "5,459 bytes unaccounted" figure came from comparing those block
  sizes against the map file; it was a reading error, not a gap in the format.
- The "odd alignment" puzzle (80s at 0x0F/0x13) is resolved: those bytes are inside the 2,724-byte
  header struct, whose first two u32s are width and height. Nothing is misaligned.
- The 796-byte buffer that `FUN_00596850` reads is the **save header** (`DAT_00985ab8`), not a map
  header. See `SAVE_FORMAT.md`.

## `saves/*.SAV` — header parsed, section skeleton known

See `SAVE_FORMAT.md` and `scripts/decode_save.py`. Header: `TERRAN\0` + `0x1A` + u32 version 86,
796 B, mission year at +0x54. Section read order recovered from a runtime trace and closed to the
byte on a 301,896-byte save. Per-section size formulas still unknown, so arbitrary saves cannot yet
be split.

## Provenance

- Counts: `find . -type f -printf '%s\t%p\n'` grouped by extension, 2026-10-20.
- PCX: `PIL.Image.open('Cursor.pcx')` → `(1024, 768) P`.
- FLIC: `ffprobe -show_entries stream=codec_name,width,height` → `flic,105,87`.
- `alpha.txt` sample: `sed -n '20,34p'` shows the `#RULES` block with per-line comments.
- `Script.txt` sample: first 10 lines — Firaxis copyright + "Dialog box scripts".
