# SMAC headless harness (Xvfb + OCR + /proc memory)

How to drive and *measure* a Wine game deterministically: no vision model, no remembered
click coordinates. Two oracles — the mission year in memory decides whether a turn
advanced, OCR decides which screen is up and where the widget is.

## The two oracles

| what | how |
|---|---|
| did the turn advance? | `python3 scripts/smac_state.py --json` → `year` |
| what is on screen? | `tesseract --psm 6 tsv` on a **2×** nearest-neighbour upscale of an 800×600 `xwd`+`ffmpeg` crop |

```bash
xwd -root -silent -out /tmp/s.xwd && ffmpeg -hide_banner -loglevel error \
  -i /tmp/s.xwd -vf crop=800:600:0:0 -y /tmp/s.png
ffmpeg -i /tmp/s.png -vf "scale=1600:1200:flags=neighbor,format=gray" -y /tmp/s2x.png
tesseract /tmp/s2x.png stdout --psm 6 tsv     # divide box coords by 2
```

**2× is the sweet spot** (measured, 4 weak cores): 2× = 0.94 s and still reads `COMPLETE`,
captions and dialog bodies; 3× = 1.85 s for no extra information. Cropping to just the
dialog band + button and OCRing each separately is *slower* (two ffmpeg and two tesseract
spawns ≈ 1.9 s), and the small button strip is unreadable below 6×, so keep one full-frame
pass per decision. Budget two OCR passes per turn, not four.

## Live globals (32-bit VAs, image base 0x400000; BSS, so the file has no bytes)

| addr | meaning | how it was checked |
|---|---|---|
| `DAT_00985b00` | mission year | 2101 at start, +1/turn, agrees with HUD "Mission Year" |
| `DAT_0092bf68` / `DAT_0092bf6c` | scenario start year / limit | 2100 / 2600 |
| `DAT_00985dc8` | mode flags | 0 across every solo turn ⇒ bit 0x10 branch in `FUN_00522240` never taken |
| `DAT_00985ae8` | turn flags | 0 idle, 2 while the end-turn is in flight |
| `DAT_00985dcc` / `DAT_0091b5b4` | current / own player index | 3 = University |
| `DAT_00985b10` | active-player bitmask | 0xff08 |
| `DAT_0091f694` | MP-only turn counter | stays 0 for ~100 solo turns — do not read it as "turns elapsed" |
| `DAT_00985af4` | counter iterated with stride 0x130 | 7→26 over one game — not a faction count |

`/proc/<pid>/mem` needs `ptrace_scope=0`; open with mode 0 (`open(path, "rb", 0)`), seek, read.
If it raises EACCES, gdb is broken too — fix the sysctl rather than hunting the address.

## Screen taxonomy → action

| class | detected by | action |
|---|---|---|
| **quit prompt** ("Do you really want to quit?") | `reallywant`+`quit` **or** `oops`+`wait` in the squashed text — its banner IS the game title, so the naive `title` test fires on it (M54a) | **`Escape`** = "Oops, no, wait!". Clicking its OK exits the game; a 40-turn run died at turn 13 because the class did not exist and the driver correctly refused to click |
| **title / menu** | letter-squashed text contains `sidmeiersalphacentauri` or `reallywanttoquit` | **stop the run, click nothing** — see the escape pitfall below |
| HUD | OCR word `COMPLETE` with y in 380..450 | click it |
| units-not-moved confirm | the question itself: squashed text contains `endtheturn` plus `moved`/`reallywant` | click the `Yes, …` row, then the OK bar ~26 px below |
| CD-ROM boot nag | squashed text has `cdrom` + `detected` | `Return`. **Test before `title`**: its caption carries the game title, so the naive title test quits the session at boot |
| LOAD confirm (after LOAD GAME) | squashed text has `difficultylevel` (exclude `pick`/`choose` = the new-game wizard) | click OK at caption-row centre − 108, caption y + 194 (measured (287,390); (290,391) verified live) |
| advisory dialog (OPERATIONS DIRECTOR, PSYCH CHAPLAIN, NETFLASH, diplomacy, speech quotes) | ≥10 OCR words with x 180..620, y 55..180 **and** a flat panel behind them (`getcolors` of that box < ~45) **or** the same flatness inside the pane's text column `(350,90,630,320)` | `Return` (default button) |
| tech breakthrough ("OUR RESEARCHERS HAVE MADE…") | text `breakthrough`/`researchers` | `Escape` |
| base screen | `GOVERNOR` / `NUTRIENTS` / `CONQUER` / `DISCOVER` **at a position outside the HUD's own message strip (y ≥ 425)**, or with **no TURN COMPLETE row on screen at all** (M54a) | `Escape` |
| Secret Project movie, dark/few-words frame | <15 OCR words | wait — movies end on their own; one `Escape` only after ~20 s with no change |

Classifier order matters (current `classify()`): confirm → cdrom → loaded-game → **quit-prompt** → title →
breakthrough → help → comm → **dest-chooser** → **name-pane** → base → dialog → artwork-close → HUD →
movie → unknown. The dialog test needs the flat-panel check because map labels also produce words
in the upper band; colour counting alone fails on unexplored (black) map, text mass alone fails on
labelled map.

**A pane drawn OVER a still-visible HUD classifies as the screen underneath it.** TURN COMPLETE stays
drawn behind the `g` chooser, the NEWBASE name pane and most Script.txt dialogs, so anything tested after
the HUD test can never fire on them: both of those panes read `hud` — key sinks — until they got their own
**caption-band** tests (words squashed to letters inside a y/x band, e.g. `is_name_pane` requires `name`
AND `newbase` in y 90..128, x 150..650). Give a new pane a positional/caption-band test placed BEFORE the
base and HUD tests, never a frame-wide vocabulary test appended after them. The mirror-image trap is the
HUD impersonating a pane (message-pane news carrying base words) — both directions need positions, not words.

### Adding a screen class — four edits, in this order

1. A predicate helper beside the others (`is_dest_chooser`, `is_name_pane`, …): caption band +
   squashed-letter phrase, not whole-frame vocabulary.
2. A `classify()` branch **before** the base/HUD tests (see the rule above).
3. Save the frame to `evidence/<milestone>/<pane>.png`, then add a `CASES` row to
   `scripts/test_classify.py` **and** a `DEFAULT` row to `scripts/check_classes.py` — the expected
   totals are derived from the lists (`PASS N/N`, `frames: N failures: 0`), so both files must be
   edited or the new class ships untested. Run both, then delete the `_3x.png` siblings
   `check_classes.py` leaves next to every frame it OCRs.
4. Wire the driver's pane handlers to the class's answer, and re-check the answer against the same
   saved frame before launching anything.

Check `python3 scripts/evidence.py budget` BEFORE adding frames (gate FAILs at 30 MB). A live frame that
reads `unknown` while a pane is visibly up means the class is missing or too narrow: widen the test — do
not service `unknown` with keys, and never service it in a probe (a probe that answers `unknown` fires
keys at whatever is really there).

**The HUD's own message pane can impersonate another screen** (M54a, 2026-10-24). The news strip
below the TURN COMPLETE row prints sentences that carry base-screen vocabulary — `nutrients` at
(355,438) on `evidence/m54a/live_hud.png` — so the old frame-wide `any(w in t for w in BASE_WORDS)`
test read that plain HUD frame as `base`: TURN COMPLETE was never clicked and, with
`--no-escape > --timeout`, the clearing Escape was forbidden, giving two STUCK runs with zero year
hits. The test is positional now (`base_word_positions` + `in_msgpane`, `MSGPANE = (0,425,800,600)`):
base words count only outside that strip, or while the HUD button row is absent — a real base screen
has no TURN COMPLETE row at all (`evidence/m45a_post.png`: base words at y 16–45 and (279,273),
`btn=None`). Pin both sides without a game: `python3 scripts/test_classify.py` (6 fixtures, exit
code) and the `m54a/live_hud.png` / `m45a_post.png` / `m25_t7.png` rows of `scripts/check_classes.py`.

**A pane can contain ARTWORK, which breaks the flat-panel test** (M14): an OPERATIONS DIRECTOR
quote panel with the Morgan "Centauri Monopoly" pyramid measured 148 colours in the old sample
box (≥45 ⇒ not `dialog`) while TURN COMPLETE stayed drawn underneath ⇒ it classified `hud`, the
driver clicked the map 11× and the turn stalled 156 s. The same panel is flat (6 colours) in its
**text column** `(350,90,630,320)`, where a plain HUD gives 90 — that second box is the fix. A
wide-flat-`OK`-bar detector does NOT work: the panes dither (runs alternate `(0,0,0)`/`(13,23,36)`)
and the "OK" glyph splits the bar.

Prove a class change offline before launching: `scripts/check_classes.py` runs `classify()` over
saved evidence frames (tesseract on a PNG is deterministic) and `scripts/smac_probe.py` prints the
verdict for the live screen **without touching the game** — that is how you tell "the classifier
doesn't know this screen" from "the game crashed".

## Driver design rule

A turn is not one click. Press TURN COMPLETE, then **keep servicing the screen until the
mission year changes**: confirm → Yes row + OK bar, dialog → `Return`, base/movie → wait or
one Escape, HUD still unflipped after ~6 s → press again. Poll memory every ~0.15 s instead of
sleeping a fixed interval; a fat `sleep(2)` per loop iteration is most of a turn's wall time.
One-shot "click, wait, screenshot" always times out on the first interruption and gets
misdiagnosed as a game hang.

**Service a modal by its EFFECT, not by screenshots.** Poll the field the action changes — order byte
`+17`, the base array, the unit's x/y — at ~100 ms, and OCR only when memory has not answered: the game's
reaction is milliseconds (a founding's base record exists 0.1 s after the name pane is accepted; a chooser
OK is consumed by the order pump within tens of ms) while an OCR pass is seconds, so a screenshot-paced
pane loop keeps pressing keys at what it believes is a clean HUD — and `Return` at a HUD is TURN COMPLETE,
which means the probe silently advances the game it is measuring. When a probe's result depends on which
pane opened, add a no-key stage first (poke selection alone, read the class) so the pane is attributed to
the key and not to the selection. With this loop a turn costs 8–12 s on a 4-core N100, two OCR
passes included.

## Pitfalls that cost real time

- **img crop args are (x, y, w, h), not edges.** Passing `(520,375,800,465)` to `crop=800:465:520:375`
  makes ffmpeg clamp silently — no error at all — and every OCR coordinate then comes back
  ~2× too large, so clicks land in the wrong half of the screen. Compare a known word's
y  coordinate against the crop offset before trusting the pipeline.
- **Never substring-match short targets.** `find(["yes"])` matches the unit panel's `Moves:`
  OCR'd as `Moyes:`, and `"ok"` matches `Prokhor` — the driver then clicks the map forever and
  the dialog looks undismissable. Require ≥4 characters *and* a plausible region (row y in
  160..220, x ≤ 660) for dialog rows.
- **Dialog phrase matching must not use a similarity ratio.** difflib against the confirm
  sentence fires on title text and map labels. Strip everything but `a-z` from the joined OCR
  words and require the question body: `endtheturn` + (`moved` | `reallywant`). The dialog
  caption alone is not a signal — OPERATIONS DIRECTOR titles both the confirm and a speech
  quote dialog.
- **Row-select race: click the OK bar at least ~1.2 s after the row.** Confirm becomes the
  *previous* selection ("No, let me move them"), the same question reappears, and it reads
  exactly like a hang. 1.2 s is the verified floor; 0.35–0.7 s fails.
- **The 3-row COMM OFFICER pane ignores row clicks — use the keyboard.** "I have Colonel X on
  Channel 9. Shall I put her through?" has three rows (switch / close / leader profile). A click
  only highlights a row, and the bar cycle then drifts onto "Display faction leader profile" →
  University Intelligence Files, an 8-minute drain (39 OCR passes, 0 rounds, verified M50b).
  Selection opens on row 1, so `windowfocus` → `key Down` → 0.4 s → `key Return` closes the
  channel deterministically.
- **A gdb `-x` script must end with `continue`.** Without it gdb runs off the end of the script and
  detaches the moment the breakpoints are set; the run then looks exactly like "the instrumented code
  never executed" (M50b: 15 minutes, zero hits).
- **Never spam Escape on an unrecognized/dark screen.** On the title it opens `Do you really
  want to quit?`, and the next OK is `Yes, that's an order, mister!` — the process exits with
  nothing in the Wine log. Give dark screens ~20 s of grace (movies end themselves), check the
  window still exists before each key, and stop rather than click a title screen. **The same quit
  confirm also appears in-game** (M14: drawn over a live HUD at 2185, rows *Oops, no, wait!* /
  *Yes, that's an order, mister!*, OK bar y~305) — keep `title` a stop, and OK with "Oops" already
  selected restores a clean HUD. `smac_play.py --no-escape 60` suppresses Escape entirely for the
  first N seconds so a startup mis-classification cannot end a run.
- **The live unit array is a linked list, so record index is NOT unit identity.** Records are
  threaded by **+48/+50** (prev/next record indices); `unit_remove_from_map` writes the 0xffff
  sentinel into x/y/+48/+50 in place and a later compaction pass slides records down. Diffing
  `scripts/smac_unitpos.py` snapshots across turns showed 108/119 records "moved" while most also
  changed *owner* — that was the compaction, not movement. Match on an identity field (none pinned
  yet) before claiming a unit moved. Byte-level diffing the whole array (`0x933278 .. +52*119`)
  is the oracle that catches order writes (`+17`, `+28`) a position diff misses.
- **Clicks DO land on visible map features** (M16: a click on University Base's tile opened its
  display). A null click result usually means the map had panned and the click hit black void —
  re-derive the target pixel from a fresh screenshot every time, and prefer keyboard orders (see
  the watchpoint section: `h` = HOLD is verified) over click-to-order.
- **Keyboard needs `xdotool windowfocus <win>`**; without a WM on Xvfb, focus is never granted and
  every key press is dropped silently — every dialog then looks undismissable.
- **Zoom in on the HUD's own words, not the map**: the game view can be almost entirely unexplored
  (black) terrain, so colour-count "is a dialog open?" heuristics are worthless there — OCR text
  geometry is the only reliable signal.
- **No hardware GL under Xvfb.** `glxinfo -B` on the Xvfb display reports `llvmpipe` even when the
  user is in `render`/`video` and the launcher runs under `sg render` — the GLX implementation
  belongs to the X server, not the process. Real iGPU use needs Xorg on the Intel driver or
  weston `--backend=headless --renderer=gl` + Xwayland; group membership alone changes nothing.
- Pausing gdb leaves `terran.exe` in state `T`; `kill -CONT <pid>` resumes it.

## gdb hardware watchpoints under Wine (verified twice, M17–M18)

They **do** work: gdb 17.1 on x86-64 attaches to the 32-bit Wine process and reports
`Hardware watchpoint 1: *(unsigned short*)0x93351c`, with `Old value = 67 / New value = 65535`.
That old/new pair is what converts a "who touched this address" hit into a semantic finding.

```bash
cd ~/reverse/smac
timeout 300 gdb -batch -nx -x scripts/m18_watch.gdb -p $(pgrep -x terran.exe) \
        > evidence/m18_watch.log 2>&1 &
sleep 7            # wait for the "Hardware watchpoint N:" lines, THEN drive the game
```

- Script shape (`scripts/m17_watch.gdb`, `scripts/m18_watch.gdb`): `set pagination off` /
  `set confirm off` / N × `watch *(unsigned short*)ADDR` / `continue` / post-hit `printf $pc`,
  `bt 14`, `x/14i $pc-20`, `info registers` / **`detach` + `quit`**.
- **Only 4 watchpoints** (DR0–DR3). Spend them on the fields the experiment is about.
- The script must finish with `detach`/`quit`; a *killed* gdb leaves the inferior stopped.
- The game keeps running while attached — `smac_play.py --turns 3` advanced 2185→2188 with four
  watchpoints armed, and the hit landed mid-round.
- **A unit's x watchpoint is captured by the array compaction while a turn resolves**: all 6 hits in
  `evidence/m19_watch.log` stopped at `0x64bfa3` (`rep movsl %ds:(%esi),%es:(%edi)`, both pointers inside
  `0x9332xx`) with return `0x5abc4b` in `FUN_005abb40` — records sliding down, not units moving. Same trap
  as the purge, one layer deeper. While a turn resolves prefer **store-site breakpoints** (next section).
- **gdb has no `silent` command.** Two of three first attempts aborted with `Undefined command: "silent"`
  after 1–2 hits. A `commands` block is `printf` … `continue` … `end`, nothing else.
- **Only one tracer at a time.** While a gdb is attached, a second prints `process N is already traced by
  process M` → `ptrace: Inappropriate ioctl for device` → `The program is not being run`, then exits: the
  log reads like "zero writes happened" when nothing was armed. Check `grep TracerPid /proc/<pid>/status`
  before arming, and again before believing a null result.

## Store-site breakpoints — the oracle that named the move machinery

`objdump` over the runtime `.text` (0x401000..0x689000) finds every instruction that stores to a field of
a global array; breakpoint those and log the base register (`== index * stride`) plus the value register.
`scripts/m19c_writesites.gdb` / `scripts/m23_writesites.gdb` do it for unit x (`+0` of the 52 B record at
`0x933278`): sites `0x476aa9`, `0x4d728c`, `0x5ab355`, `0x5ab4bc`, `0x5ab573` (purge store `0x5ab2f1`
excluded). 739 hits in one soak named the whole move chain — `~/reverse/smac/turn_driver.md` §M19–M23.
Unlike watchpoints it survives the compaction; unlike a position diff it catches every writer.

## What the live game does with input (verified 2026-10-21, year 2198)

- Arrow keys move a **cursor**, not the selected unit: the terrain readout went `(41,11) Flat & Arid` →
  `(43,11) Rocky & Arid` (Δ(+2,0)) while the sprite stayed put and no x-store fired. The game draws a
  dashed line from the selected unit to the cursor.
- `v` is the game's own "switch back to moving pieces" (`programs/tutor.txt` #TOUR1B). It and the **Select
  unit to activate** dialog (rows y 154/194/234/274/314/354/394/434, OK (307,486), CANCEL (512,486)) each
  fire the *re-stack* (`FUN_005a5a80`: scratch `x=-3`, then back) — activation is not movement.
- A map click **pans** the view (widget vtable+0x124 drag branch), so sprite coordinates drift between
  clicks: re-measure the unit's white marker with PIL (`r,g,b > 190` in the map band) after every click,
  and derive neighbour pixels from the tile lattice (diamond ≈96×72 px: Δx±2 → ±96 px, Δy±2 → ±72 px,
  Δx±1 with Δy±1 → ±48,±36).
- `Return`, `Space`, `g`, `f` and tile clicks have produced **no** x-write with a new coordinate — the
  player move gesture is still unidentified. `programs/tutor.txt` #TOUR2: "You can use the arrow keys or
  the mouse to move units. The SPACE bar tells a unit to stay where it is for now."
- **A click on a tile that holds a unit STACK raises the SELECT UNIT TO ACTIVATE modal for either mouse
  button** (`FUN_004d3f70` → `FUN_0048f8b0(idx, s_PICKUNIT, 1)`), and after row+OK it only re-stacks. If
  all your units are garrisoned on one tile, no blind click sequence can reach the "one unit selected,
  awaiting a destination" state. Geometry re-measured 2026-10-21: rows y ≈ 160..440 step ~40,
  OK ≈ (295,483), CANCEL ≈ (500,483).
- **Pointer grab can kill ALL clicks (M26):** `xdotool getmouselocation` / `XQueryPointer` reporting window `0x400004` ("smac - Wine Desktop", explorer.exe) means a grab sits on the Wine desktop window and pointer clicks never reach the game (keys via `xdotool key --window` still work — the classic 'keys land, clicks die' signature). The FIRST real click breaks the grab; fire one throwaway click first, then verify delivery with a `MAPH` breakpoint hit, never with 'screen unchanged'. `xdotool windowraise` does NOT fix it.
- **Fresh loads open the base screen with an OPERATIONS DIRECTOR modal on top** (M26): dismiss the row (~400,307), wait ≥1.2 s, OK (400,362), then one Escape closes the base screen to the HUD. The LOAD pane is a game file browser that may open at host root (Z:): click the name box (~410,532), clear, type `home/n100/reverse/smac/programs/saves/auto`, OK (345,555); saves live in `<game>/saves/auto/`; a `.SAV`'s mission year is a u16 at file offset `0x54` — read it before trusting a slot name (autosave slots are overwritten in place).
- **Calibrate pixels with gdb, not with remembered sprites**: breakpoint `0x476580` (the map-widget click
  handler — stack args at `esp+4/+8` are the raw **pixel** x/y) and `0x4d3f70` (the ACTIVATE handler —
  its args are the resolved **tile** x/y). The pair gives the pixel→tile map for the *current* pan, which
  drifts between clicks: tile (41,11) sat at (387,172) and later at (382,212) in one session.
- **The `in_ECX` singleton is the global block based at `0x8f79e0`** (verified: `+0x23bd4 = 0x91b5b4` =
  own player). So `DAT_0091b5bc` = selected unit index, `0x91b5b8` = orders-mode flag, `0x91b5c4` =
  order-menu-pending, `0x91b5e8` + the u32 lists `0x91b5f0` (x) / `0x91b670` (y) = cursor/destination
  candidates. Reading `0x91b5bc` straight out of `/proc/<pid>/mem` says which unit a hotkey will act on
  — no OCR, no tracer. Keys route through `FUN_00512450` (acts on the selected unit) or `FUN_00511960`
  (acts on the cursor tile); `FUN_00512b40` picks between them and remaps `b c d f g h i` to the
  8-value directional cluster `0x21..0x28`.
- **gdb's `printf` is block-buffered when its stdout is redirected to a file**: hits appear only after
  ~4 KB or when gdb exits. Judge a run by the log read *after* `kill -TERM gdb` (then `kill -CONT
  <terran pid>`) — a mid-run `tail` that shows nothing does **not** mean nothing fired.
- **The unit array grows past the save's count**: 166 live records at year 2198 where the save said 119.
  Filter `x != 0xffff && owner < 8 && x < 128 && y < 128` over a wide window instead of trusting a count.
- **Faction index → name**, read off the base array `0x95da10` by base name: 1 Gaia's Garden, 2 Hive,
  3 University ("The Rapture"), 4 Morgan, 5 Sparta, 6 Circle of Mother, 7 U.N.

- Cross-reference the hit with `scripts/fn.py <addr>` / `grep -rn 'ADDR' ghidra_out/*.c`; Ghidra
  VAs equal runtime addresses, so `0x4d3888` maps straight to its function, and the live
  instructions can be matched one-for-one against the decompiled body (that is how `FUN_004d3770`
  was confirmed as the order setter: `mov %bl,0x933289(%ecx)` == `(&DAT_00933289)[i*0x34] = 2`).
