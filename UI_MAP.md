# SMAC menus & game UI — recreation map (session 2026-10-19/20 night run)

Goal context: Paul wants to **play SMAC single-player with working AI** and
**recreate the full menus + game UI**. This file is the UI-side spec built
from `programs/` assets + `terran.exe` string/code evidence. All exe
addresses are image-space (base 0x400000).

## Headline finding: the UI is data-driven

`programs/Script.txt` (244 KB, 9,815 lines) is Firaxis's **"Dialog box
scripts"** file — a declarative UI description for essentially every menu
and dialog in the game. Parsed with `parse_script.py` →
`script_parsed.json`: **1,357 pane definitions**.

Directive grammar (documented in the file's own translator instructions,
lines 1–140):

| directive | meaning |
|---|---|
| `#NAME` (UPPER) | begin pane definition (id used by exe + by `$` refs) |
| `#xs N` | pane width (size) hint |
| `#x N` / `#y N` | position (often `-5` = anchored) |
| `#caption TEXT` | title text (continuation lines allowed) |
| `#button TEXT` | push button |
| `#itemlist` | literal option list follows (menu items) |
| `#listbox` | scrollable list widget |
| `#wave` | sound trigger (203 uses) |
| `^` / `^^` | newline / centered line |
| `{}` / `[]` | bold / italic spans |
| `$NAME123` | string substitution (id 123; `$NUMn` numeric, `$HEXn` hex) |
| `$<n:a:b>` / `$<n:m:f:ne:…>` | plurality/gender substitution from string n |
| `#END` | pane end (exe-side token table @0x68cbfc) |

Pane inventory highlights (from `script_parsed.json`): TOPMENU (main menu:
START GAME / QUICK START / SCENARIO / LOAD GAME / MULTIPLAYER / VIEW CREDITS
/ EXIT GAME), MAPMENU, MULTIMENU, SCENARIOMENU, world-gen dialogs
(WORLDSIZE/LAND/TIDES/ORBIT/CLOUDS/LIFE), DIFFICULTY, GENDER, FACTION, NAME,
CUSTOMNAMES, USERULES/RULES/SCENRULES/SCENPARAM, TIMECONTROLS, 103 TECH
panes, 64 SOCIAL panes, 49 BASE panes, 19 DIPLO panes, 9 COUNCIL panes,
16 PROBEMENU/probe panes, victory/defeat panes (ASCENT, DIPLOMATICVICTORY,
ECONOMICVICTORY, YOULOSE, CONQSING/CONQCOOP/WIPEOUT), 19 scenario-EDITOR
panes, intro/interlude panes (INTRONEW0–5, INTRO0–3, INTROMAD…).

Other data files:
- `alpha.txt` — **#RULES block = the entire game-balance parameter table**
  (movement rates, combat bonuses, psi ratios, pop limits, research rate…)
  — this is the AI/gameplay tuning surface, 93 directives.
- `BLURBS` (Blurbs.txt) — flavor/quote text keyed by `#TECHn`, `#OPENING`…
- `TECHSHORTS.TXT`, `concepts.txt` (70 `#CONCEPT`), `facedit.txt` (faction
  edit), `Interlude.txt` (72), `alpha.txt` help.
- Scenario system: `scenarios/<name>/<name>.SC` + per-scenario `scenario.txt`
  with `#INTRO`/`#OBJECTIVES`; scenario dir **overrides** main game files
  (documented in SCENARIO.txt header) — includes per-scenario art/text.

## Exe-side string evidence (widget/pane token table)

- Pane/widget token strings cluster at 0x692000–0x693c40: `MULTIMENU`
  (0x692018), `TOPMENU` (0x692024), `SCENARIOMENU`, `INTRO`, `SCENARIO`,
  `TECH`/`TECH2`/`TECHMIL`/`TECHINF`, `SOCIETY`, `SETUP1/2/3`, `WIPEOUT`,
  `YOULOSE`, `RANKINGS`, `Replay`, `WinsFileBox` (0x693008), `LOADGAME`,
  `SECURITY`, `IRONMAN`, `FRAME`/`FRAMEMENU`/`FRAMEFLOP`/`FRAMEEXCUSE`/
  `FRAMEJOB` (diplomacy "frame the leader" event panes), etc.
- Text-file loader tokens at 0x693bbc–0x693bfc: `ALPHA`, `SCRIPT`,
  `EDITOR`, `HELP`, `TUTOR`, `WIZARD`, `BLURBS`, `MENU`, `INTERLUDE` —
  the named text resources the engine opens (script.txt @0x676bf0).
- `Arial` font string @0x693c18 + shipped `.ttf` files → TTF text rendering.
- Corner-notification system: event tokens paired with small PCX icons in
  the string table (e.g. `CORNERNOHQ`+`econwin_sm.pcx` @0x68ca08,
  `BEGINPROJECT`+`secproj_sm.pcx` @0x68cc94, `RIOT`+`drone_sm.pcx`,
  `FRAMED`+`capture_sm.pcx` @0x692f4c) — the little pop-up icons at the
  map edge.
- Voice clips: `voices\fac…` + `.mp3` strings (@0x68cfb0) and the
  UPPER_CASE token region 0x68b000–0x691600 = voice/sound clip names
  (KILLFACTION, TREATY… are clip names, not netcode opcodes).
- Save/load paths: `saves\`, `auto\`, `scenarios\`, `maps\*.` ,
  `Alpha Centauri Autosave 1/10/20/30.SAV` (@0x693158–), `Latest Save`/
  `Latest Scenario`/`Latest Map` labels, `WinsFileBox` (custom Win32 file
  chooser wrapper).
- Console/help: `console.pcx`, `console_x.pcx`, `iface_up/down(.pcx)`
  (@0x6756e8–) + `fx\main menu.wav` — the slide-up console bar UI.

## Asset inventory (extracted, viewable)

- 378 `.pcx` UI bitmaps → `png/` (all converted; contact sheets in
  `sheets/`: sheet_techs.png 90 tech icons, sheet_projs.png 33 project
  icons, sheet_facs.png 39 faction/unit icons — clean vector-style icons on
  the purple UI palette, sheet_main.png all 378).
- Core chrome: `frame.pcx` (window frames), `TEXTURE.PCX`/`texture.pcx`
  (tile textures), `ICONS.PCX` (800×600 master icon atlas), `Cursor.pcx`,
  `Holobook.pcx`, `Jackal.pcx`, `multi.pcx`, `credits2.pcx`, `openinga.pcx`,
  `monzoom1/2.pcx` (moon zoom views).
- 112+1 `.cvr` voxel models — decoded + rendered earlier (see FINDINGS.md).
- 21 `.flc` animations — **NOT standard Autodesk FLIC** despite `af12`
  magic at offset 4; custom SMAC header (128-byte header: filesize, af12,
  frame count, dims, FILETIME stamps) + palette-delta + index-frame body;
  chunk scan finds no standard FLIC chunk opcodes. Decoder TBD (open
  puzzle). Used for: intro movies (`univ.flc`, `faction.flc`), faction
  filmings (`gaians/hive/spartans/morgan/believe/peace.flc`), diplomacy
  movies (`dip_f_*.flc`, `dip_m_*.flc`), UI effects (`turn.flc` 320×192
  20f, `openitem.flc`, `satellite.flc`, `buster.flc`, `monument.flc`,
  `drop_pod.flc`+`drop_smoke.flc`).

### FLIC format — EXE-VERIFIED (FUN_0062ad73 loader, FUN_0062bdeb chunk parser)

- `FUN_0062ad73` (called with `"turn.flc"` etc. from pane code e.g.
  `FUN_0045ed90`): opens file (`FUN_0063c610`), reads 0x80-byte header
  (`FUN_0064cc00` = fread wrapper), validates **main magic u16 @+4 ==
  0xAF12** (`cmp ecx,0xaf12` @0x62ae23), stores **W=u16 @+8, H=u16 @+10**
  (my w4/w5 = correct), then reads **16-byte frame headers** per frame.
- **Chunk parser `FUN_0062bdeb`**: chunk = u32 LE size + u16 LE type;
  type 0xF1FA (=-0xe06 as short) = container → recurse over sub-chunks
  (6-byte headers). Leaf dispatch on type (two tables: normal vs
  flag|2 second pass):
  - **type 7** → `FUN_0062b68e`: **16-bit pixel small-brun RLE**:
    u16 rowcount; per row: skip-words while `(u16 & 0xC000)==0xC000`
    (advance rows by (val&0x3FFF)×stride); u16 npackets; packets =
    u8 count + u8 value — **value ≥ 1: copy `count` u16 pixels raw;
    value < 1: RLE, next u16 = (cnt, word) where color =
    ((word hi+ref)&0xFF<<8)|((word lo+ref)&0xFF)** (palette-delta ref
    @this+0x5a4); `0x8000` flag word before packets sets transparency
    baseline; bbox tracked into this+0x58c..0x598.
  - **type 0xf** → `FUN_0062b3da`: 8-bit row RLE (classic BRUN: u8
    count, literal copy / negative = RLE with next byte, +ref variant).
  - **type 0x10** → `FUN_0062bc1d`: **raw 8-bit rows** (read `width`
    bytes/row; if ref!=0 stored bytes are offset by ref) — i.e. an
    8-bit indexed bitmap.  - **type 0xd** → `FUN_0062bb73`: clear rect
    (`FUN_005c02b5`).  Delta table (flag|2): 7→`FUN_0062c36f` (160 ln),
    0xf→`FUN_0062c06c`, 0x10→`FUN_0062cac7`, 0xd→`FUN_0062ca09`.
  - types 4/0xb/0xc/0x12 (`FUN_0062b683`/`0062bb68`/`0062bb5d`/
    `0062bde0`) are 8-line no-op stubs — **unused in shipped files**.
  - default: seek forward `size-6` (skip unknown chunk).
- turn.flc frame0 = 16-B frame header (size=1081, F1FA, subchunk-count=2)
  + **type-4 chunk 772 B** (color table; exe handler is a no-op — the
  engine keeps its own palette) + **type-0xf chunk 281 B** (8-bit indexed
  BRUN rows). Frames 1..19 = 196-B single type-7 (16-bit) delta chunks.
  Surface dims come from main header u16 @+8/+10 (turn.flc = 233×23 —
  the turn-indicator strip; monument.flc = 1024×768 ✓). Row grammar of
  type-0xf payload still being pinned (width byte per row + packets).
- Frame header fields: u32 size @0, u16 0xF1FA @4, u16 subchunk-count
  @6, bbox/flags @+8..; main header W/H @+8/+10 confirmed by exe reads.

- Missing from ISO extraction (referenced by exe, not shipped on disc or in
  another archive): voice WAVs (`cpu *.wav`, `amenu2.wav` … 76 names),
  `fx\main menu.wav`; music/sfx likely on the second CD/`music` dir.
  All 235 referenced art/text files ARE present.

## PCX format quirk (open puzzle, logged)

SMAC `.pcx` files start `0A 05 01 08` (not classic `01 05 …`): an 8-byte
prefixed PCX variant. Pillow 12 (magic `0A` accepted) decodes them to
visually coherent images (verified: Icons.pcx = full game screen with unit
button grid; fac*.pcx = clean icons). A hand-rolled classic per-row RLE
decoder matches Pillow exactly on some files (Dot0) but not others
(Icons/Airdp_sm) — the exact SMAC encoding (possibly multi-frame/atlas or
altered RLE) is unresolved. **Use Pillow as reference decoder** for now.

## FLIC decoder — WORKING (flc_decode3.py, 2026-10-20 ~02:20)

Byte-exact validation, not just eyeballs:

- **turn.flc frame0** (type-0xf 8-bit rows): my packet decoder consumes
  **exactly 281/281 payload bytes** and renders a clean 233×23 UI bar
  (teal stripes + tan border) → 8-bit indexed, 1 byte/px, per row:
  1 leading byte (read+discarded by the exe), then while remaining>0:
  `s8 c; c>=1 → RLE with next byte as index; c<=0 → literal -c bytes`.
  Width 466 (16-bit) does NOT fit (overruns) → 8-bit confirmed.
- **turn.flc frame1** (type-7 delta): a brute-force search over packet
  interpretations found **exactly one** that consumes 174/174 payload
  bytes: literal runs are **2×val bytes** (matches the exe's
  `(char)val << 1`), RLE reads a u16 word. Skip-words advance
  `-(s16)` rows (matches `CALL 0x64b870` negate in FUN_0062c36f).
- With those semantics all 20 turn.flc frames render and the bar **cycles
  color frame to frame** (teal→pale blue→yellow→green→pink→orange→blue…)
  = the turn-complete pulse. faction.flc (105×87, 28 frames) now decodes
  into a recognizable **portrait animation** (a face is clear in frame 2).

**Still open (narrow):** the type-7 RLE word's color semantics (two
palette indices alternating vs a 16-bit 5-5-5 color) and the per-object
`ref` byte (`this+0x5a4`) + transparency index (`*this`) — neither is set
in FUN_0062ad73; they come from the animation/palette manager. A constant
ref sweep (0–255) and trans sweep don't collapse the residual dither, so
they're per-file/per-faction values (SMAC has per-faction color schemes).
Best next move: confirm at runtime (game under Wine / glsmac) or trace
writes to anim+0x5a4.

## Wine / runnability status (2026-10-20 ~01:20)

- Kron4ek **wine-10.20-amd64** (last build w/ i386-unix 32-bit engine) at
  `~/tools/wine-10.20-amd64`; i386 multiarch installed (libc6:i386,
  libgl1:i386, libasound2:i386, libgnutls30t64:i386, libgcrypt20:i386).
- terran.exe **launches** (window appears on Xvfb :99; ffmpeg x11grab
  screenshots show black window + Wine toast), but the 32-bit side fails:
  `wine: could not load kernel32.dll, status c0000135` — Kron4ek WoW64
  32-bit kernel32 can't load on this host (missing i386 host libs beyond
  libc; wineboot leaves a PE32+-only prefix). Next options: install more
  i386 libs (libvulkan/libopencl-i386?), try wine-staging-tkg-x86 (pure
  32-bit build + WINE_MONOWOW64), or accept that native playback needs
  glsmac/nGage/dgVoodoo-on-Windows.
- Xvfb :99 still running; kill with `pkill -f '[X]vfb :99'`.

## Recreation plan (UI track)

1. ✅ Asset pipeline: PCX→PNG + contact sheets (done this session).
2. ✅ Pane inventory: Script.txt parsed (done) → this map.
3. TODO: FLIC-format decoder for the 21 animations (needs exe-side loader
   analysis — xref `faction.flc` @0x673a40 / `turn.flc` @0x675708).
4. TODO: map Script directives → exe parser (xref `SCRIPT` @0x693bc4,
   `#END` tokens @0x68cbfc) to confirm widget set & semantics (esp. `#xs`,
   `#x/#y`, `#wave`, `$`-substitution engine).
5. TODO: map the always-on game HUD (console bar, unit button grid from
   ICONS.PCX, minimap, resource bar) — this is CPane code, not Script.txt;
   start from `console.pcx`/`iface_*.pcx` xrefs and the CPane builders
   (`FUN_00444140`, `FUN_0047c0e0`).
6. TODO: text pipeline — ALPHA.TXT/BLURBS/TECHSHORTS section keys → in-game
   text lookups; `$`-substitution id space → game string table.
7. Build: HTML/canvas prototype rendering Script.txt panes with frame.pcx
   chrome + TTF (Arial) + the icon atlases → clickable menu mock.

## Single-player/AI track notes (from same night)

- `alpha.txt` #RULES = editable balance/AI parameter table (the game ships
  its own tuning file — moddable without RE).
- AI diplomacy hub `FUN_00546800` (3,924 lines) still to decompose.
- Runnability: testing Wine (Kron4ek staging build) on this Linux box;
  game needs dgVoodoo2 or DX7-era wrapper for DDRAW/DPLAYX/DSOUND on modern
  Windows; community port **nGage** supports SMAC.

## Runtime validation under Wine (2026-10-20, session 5/6)

terran.exe boots all the way to a **live, interactive single-player game**
under **wine-10.20-staging-tkg-x86** on this headless box (Xvfb :99, llvmpipe
software GL). Verified boot chain (screenshots in `~/reverse/smac/`):
Firaxis splash → **"CD-ROM not detected" check** (Retry/OK) → main menu
`menu4.png` (START GAME / QUICK START / SCENARIO / LOAD GAME / MULTIPLAYER /
VIEW CREDITS / EXIT GAME) → QUICK START picks **University (Zakharov)** →
**"PLANETFALL!"** intro dialog `game_start.png` → "ENTER A NAME FOR YOUR
FIRST BASE" (`ingame1.png`) → live isometric HUD `ingame3.png` (MENU/COMMLINK/
TURN COMPLETE, unit panel Scout Patrol [1-1-1] Moves:1, Econ/Psych/Lab, minimap).

**Audio FIXED:** host has no soundcard (`aplay -l` → none) and the i386
alsa-lib plugin dir is empty; Wine 10.x defaults to the **winepulse** backend
which needs i386 `libpulse.so.0` (absent) → `mmdevapi:load_driver … c0000135`.
Fix = `sudo apt-get install -y libpulse0:i386` (pipewire-pulse is already
running, so winepulse connects to it). After install the mmdevapi error is
**gone** from the run log (`/tmp/wine_run7.log`). A null `~/.asoundrc` alone
does NOT help (i386 libasound core present but winepulse is the default path).

**Input routing (exe-verified):** window proc `FUN_005d0c33` dispatches
WM_LBUTTONDOWN(0x201)→`FUN_005d1dcf`, LBUTTONUP(0x202)→`FUN_005d1ec5`,
LBUTTONDBLCLK(0x203)→`FUN_005d1dcf(…,1)`, RBUTTON*, WM_MOUSEMOVE(0x200)→
`FUN_005d1cf3`, WM_PAINT(0xf)→`FUN_005d13c7`, WM_ACTIVATE(0x6)→`FUN_005d1505`,
WM_WINDOWPOSCHANGED(0x47)/0x30f→`FUN_005d1231`. `FUN_005d1dcf` hit-tests the
widget tree via `FUN_005d711a`→recursive `FUN_005d6a80` (children at
`w+0x69*4`, count `w+0xff`, flags `w+0x26`/child`+0x98`, contains-point via
vtable+0xec, transparent sentinel color `DAT_00698be8`, active-control flag
`DAT_00993988`). On hit it calls the widget's **vtable+0x124** "press-test";
return 2 or **10–17 ⇒ DRAG/SCROLL** mode (stores `DAT_0099398c/90/94/98` and
returns) — this is exactly why a click on the map **pans the view instead of
issuing a unit order**; otherwise **vtable+0x138** = the real press/click
action. Global hooks `DAT_00993974(x,y)`/`DAT_0099396c()` fire after.

**Dialog geometry gotchas (Script.txt panes, live):** the OPERATIONS DIRECTOR
"units have not moved" confirm (`ops_director.png`/`dlg_before_ok.png`) has
Cancel row y≈181, "Yes, end the turn." row y≈233 (bar 224–242), and the **OK
bar at y≈257** (bar 248–268) — there is a DEAD GAP at y≈243–247 between the
Yes row and OK; clicking there is a no-op. The QUIT confirm has its OK bar far
below at y≈312. The center info panel **types its text char-by-char** on every
selection change, so screenshots catch it mid-render ("Lab: 5…", "Misis").

**OPEN — turn cycle not confirmed via automation:** confirming "Yes, end the
turn" (row-click, OK-bar@257, or Enter) closes the dialog but the turn does
**not** advance — research counter stays "Lab: 50% (6 turns)", Mission Year
stays 2101, Energy stays 11 across many attempts, with and without the audio
fix. Unit-move clicks get eaten by the drag/scroll path above. UI stays
responsive (every dialog responds) so the game is not hung; terran.exe sits at
~60% CPU which is just llvmpipe redrawing the 800×600 view continuously.
**Leading hypothesis:** SMAC's turn sync runs over the DirectPlay "jackal"
local client/server loopback (DPLAYX, imported; Wine ships dplayx.dll +
dplaysvr.exe and it inits without logged errors). If Wine's dplayx loopback
does not deliver the client DONE-TURN(0x8301)→server EXEC DONE/NEXT TURN
(0x1240/0x1501/0x4301/0x4303) messages, the turn stalls while the UI (Direct-
Draw/GDI) works fine — matching what is observed. Next: instrument the receive
thread `FUN_00638ddd`/dispatcher `FUN_0052bce0` (case 0x4404 action-exec) at
runtime, or try a real display / dgVoodoo2 / nGage / glsmac to complete a turn.
