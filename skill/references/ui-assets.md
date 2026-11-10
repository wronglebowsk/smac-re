# ui assets

Depth reference for `skill/SKILL.md` (smac-cvr-format) - moved whole at s242;
the hot core in SKILL.md keeps the summary and the pointer.

## UI / asset pipeline

- **Script.txt IS the UI**: `programs/Script.txt` declaratively defines
  1,357 dialog panes (`parse_script.py` → `script_parsed.json`). Grammar:
  `#NAME` pane start (UPPER id), `#xs` width, `#x/#y`, `#caption`,
  `#button`, `#itemlist`, `#listbox`, `#wave N` sound, `^`/`^^` newline/
  center, `{}` bold `[]` italic, `$NAME123` substitution, `$<n:a:b>` gender.
  Menu trees (TOPMENU/MAPMENU/MULTIMENU/SCENARIOMENU/setup chain/RULES/
  SCENRULES/victory/editor/intro) verified. Spec: `~/reverse/smac/UI_MAP.md`.
- **alpha.txt = the rules file the exe loads** ("reads the rules of the game from this
  file"): 45 `#SECTION`s / 650 comma-separated records (`#RULES`, `#TERRAIN`, `#TECHNOLOGY`,
  `#CHASSIS`, `#WEAPONS`, `#UNITS`, `#FACILITIES`, `#SOC*`, `#DIFF`, `#FACTIONS`…). Parse it
  (`scripts/parse_alpha.py` → `data/alpha.json`, section map in `ALPHA_RULES.md`) rather than
  RE-ing balance constants. Field names are recoverable from the trailing `;` comments for only
  4/45 sections — `#CHASSIS`/`#UNITS` etc. are bare data, so their semantics must come from the
  exe's parser, not from guesswork.
- **`maps/*.MP` = the map format** — now fully decoded, see "Map + save container formats"
  above and `~/reverse/smac/MAP_FORMAT.md`. (This bullet used to claim the loader was
  `FUN_00597a70` and that the 796-byte header's offsets were unresolved; both were wrong —
  that function is the save path and the map header is a 2,724-byte struct at offset 15.)
  `FUN_00598340` is still the magic/version dispatcher.
- **PCX**: SMAC variant starts `0A 05 01 08`; Pillow 12 decodes all 378
  correctly (`assets.py pcx programs png`; sheets in `sheets/`). Hand RLE
  decoder unsolved; glsmac hits same wall (SDL_image + procedural fixes).
- **FLIC format cracked** (not standard Autodesk): 128-B header u16
  words: w2=0xAF12, W=u16@+8, H=u16@+10 (monument.flc 1024×768 ✓),
  w6=8; frame chain @128 = `u32 LE size` + u16 0xF1FA + u16 subchunk
  count, sizes tile to EOF (turn.flc 1081+18×196+16=4473 ✓). Exe:
  loader FUN_0062ad73, dispatch FUN_0062bdeb (chunk=u32 size+u16 type;
  F1FA=container recurse; types 4/0xb/0xc/0x12 no-op stubs incl. the
  772-B color table; 7=16-bit small-brun FUN_0062b68e; 0xf=8-bit brun
  FUN_0062b3da: per row u8 width then s8 packets (>=1 literal, <0 RLE
  w/ next byte, +ref variant); 0x10=raw rows FUN_0062bc1d; 0xd=clear;
  delta table flag|2: 7→FUN_0062c36f (copies unchanged runs from prev
  buffer @this+0x4ac when run color == transparency)). Decoder scripts
  `flc_decode*.py`; type-7 RLE word color semantics + per-object ref/trans
  still being pinned. See UI_MAP.md.
- **glsmac** (afwbkbc/glsmac, cloned at `~/reverse/smac/glsmac`): working
  SDL2/GL SMAC reimplementation; hardcodes UI (does NOT parse Script.txt);
  resource enum names master atlases (palette/interface 750×900/icons/
  units/console_x/moon1-3/S{s}L{l}C{c}/arialn.ttf). Useful reference.

