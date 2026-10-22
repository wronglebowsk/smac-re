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

## Graphics

- CVR: `cvr_decode.py` (validates 113/113), renderer output in `png/` (gitignored, regenerable).
- FLIC: decoded with standard tools; frames in `flc_out/` (gitignored, regenerable).
