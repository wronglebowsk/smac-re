# SMAC under Wine — headless turn driver + live state reader (M9, 2026-10-20)

Purpose: replace "click blindly, screenshot, look at it" with two deterministic oracles:

1. **Memory** — the mission year, so "did the turn advance?" is a number, not a judgement.
2. **OCR** — which screen is up, so clicks go to widgets found by *text*, not remembered pixels.

Result: **2101 → 2116 (15/15) from a cold boot, `evidence/soak3_freshboot.log`, and 2101 → 2181 (80 turns)
in total across runs** — advanced unattended, no vision model in the loop,
`mode_flags` bit 0x10 clear the whole time (i.e. solo the entire way).

## Tooling

| file | what |
|---|---|
| `scripts/smac_state.py` | `/proc/<pid>/mem` reader; `--json`, `--watch`, `--read 0xADDR` |
| `scripts/smac_play.py` | turn servicer: OCR classifies the screen, acts, waits on the year |
| `evidence/trace_*.jsonl` | one record per turn: year before/after, screens handled, dt |
| `evidence/soak1.log`, `soak2.log` | run logs, incl. the two failure modes below |

## Verified runtime globals (32-bit VAs, base 0x400000; BSS, so file has no bytes)

| addr | meaning | evidence |
|---|---|---|
| `DAT_00985b00` | **mission year** | 2101 at start, +1 per turn, matches HUD "Mission Year" |
| `DAT_0092bf68` | year_start | 2100 |
| `DAT_0092bf6c` | year limit (compared in `FUN_0051e700`) | 2600 |
| `DAT_00985dc8` | mode flags | **0 in solo** ⇒ bit 0x10 branch in `FUN_00522240` is never taken (confirms M6b/M8) |
| `DAT_00985ae8` | turn flags | 0 idle, **2** while the end-turn is in flight |
| `DAT_00985dcc` | current player index | 3 = University (own faction) |
| `DAT_0091b5b4` | own player index | 3 |
| `DAT_00985b10` | active player bitmask | 0xff08 |
| `DAT_0091f694` | **MP-only turn counter** | stays 0 through 80 solo turns ⇒ retracts my earlier "turns elapsed" label |
| `DAT_00985af4` | counter iterated with stride 0x130 | 7 → 26 over 80 turns ⇒ **not** a faction count (own label retracted) |

## Boot / environment facts that cost sessions

- **`kernel.yama.ptrace_scope` resets to 1 on every boot.** Then both `gdb -p` and
  `/proc/<pid>/mem` fail (EACCES). Fix: `sudo sysctl -w kernel.yama.ptrace_scope=0`.
  Earlier sessions' "ptrace ok" was true only because some prior session had set it
  to 0 and the host had not rebooted since. **Put it in preflight.**
- **The host rebooted mid-project and `/tmp` was wiped** — every M8 gdb log and
  screenshot is gone. Evidence now goes to `~/reverse/smac/evidence/` (durable).
- **Keyboard is dead unless the window has focus**: `xdotool windowfocus <win>` first.
  Without it every `xdotool key` is silently dropped — this is why "Return/Escape
  did nothing" in M8 and why `answer_confirm` must be mouse-only unless focus is set.
- Screenshots: `xwd -root` + `ffmpeg -vf crop=800:600:0:0`. The window is at 0,0 so
  screenshot px == click px. `tesseract --psm 6 tsv` on a 3× nearest-neighbour upscale
  reads the pixel font well enough `1-1-1`/`Mission Year`/`TURN COMPLETE`.

## The screen taxonomy (all seen in one 80-turn run)

| class | detected by | action |
|---|---|---|
| HUD | OCR word `COMPLETE` with y in 380..450 | click it |
| units-not-moved confirm | phrase `end the turn` / `moved this turn` / `really want` (fuzzy; OCR reads "units" as "unite") | click `Yes, end the turn.` row, then the OK bar ~26 px below |
| advisory dialog (OPERATIONS DIRECTOR, PSYCH CHAPLAIN, NETFLASH, diplomacy) | ≥10 OCR words centred in y 55..180 | `Return` (default button) |
| speech/news dialog over a live HUD | same upper-block test — **must be tested before the HUD test**, the TURN COMPLETE button is visible but unreachable behind the overlay | `Return` |
| tech breakthrough ("OUR RESEARCHERS HAVE MADE…") | text `breakthrough`/`researchers` | `Escape` (verified closes it) |
| base screen | `GOVERNOR` / `NUTRIENTS` / `CONQUER` / `DISCOVER` | `Escape` |
| Secret Project movie | <15 OCR words, dark frame | `Escape` |

## Why the M4–M7 "turn stall" was never a game bug

Every stall reproduced in this run was a blocking UI element that a one-shot
"click TURN COMPLETE, wait, screenshot" loop cannot answer:

- units-not-moved confirm (appears every turn while units are unmoved),
- OPERATIONS DIRECTOR speech + NETFLASH news (one per turn, sometimes two),
- tech breakthrough screen after each discovery,
- Secret Project movies (5–30 s each under llvmpipe),
- base screens opened by stray map clicks.

With the servicer loop the year advanced on 78/80 turns; the 2 failures were the
run ending, not the game hanging.

## M9b — host reconfig + driver speed pass (2026-10-20 17:25)

### Host
- `sudo usermod -aG render,video n100` done (iGPU access for future logins). **It does not
  help yet**: even running under `sg render -c`, `glxinfo -B` on `:99` still reports
  `llvmpipe`. Xvfb has no hardware GLX — the software renderer belongs to the X server,
  not to the process. Real iGPU use needs a hardware-backed X server (Xorg on the Intel
  driver, or weston `--backend=headless --renderer=gl` + Xwayland). Deferred: it only
  buys movie/boot speed, not turn throughput.
- Boot wizard discovered (all OCR-drivable): Return advances
  difficulty → planet size → random map → "ENTER A NAME" → game start; Escape walks back.
  `QUICK START` exists only on the main menu, not inside the wizard.

### Driver changes (measured on the N100, 4 cores)
| change | before | after |
|---|---|---|
| OCR scale | 3× full frame 1.85 s | **2× full frame 0.94 s** (still reads COMPLETE/captions) |
| OCR calls per turn | 3–4 | 2 (one classify + one confirm check) |
| wait for year | `sleep(2.0)` per loop | in-memory year poll (0.15 s ticks) |
| region crops | — | tried, **slower** (2 ffmpeg + 2 tesseract spawns = 1.9 s) and the button
  strip is unreadable below 6×; abandoned in favour of one 2× full-frame pass |
| typical turn | 10–16 s | **8–12 s**, 12/12 turns advanced (2101→2112) |

### Three real bugs found while doing it (all were silently costing turns)
1. **Crop arguments were edges, not sizes.** `BTN = (520,375,800,465)` fed to
   `crop=800:465:520:375`; ffmpeg clamps silently, so OCR ran on a mis-scaled region and
   reported word coordinates 2× too large. No error ever surfaced.
2. **Substring matching on short words.** `find(words,["yes"])` matched the unit panel's
   OCR of `Moves:` as **`Moyes:`** (y=521) → the driver clicked the map instead of the
   dialog, forever. Same class: `"ok"` matched **`Prokhor`**. Fix: `find_yes_row()`
   requires 160≤y≤220 and x≤660; never match targets shorter than 4 chars.
3. **Row-select race.** Clicking the OK bar sooner than ~1 s after clicking
   `Yes, end the turn.` confirms the *previous* selection ("No, let me move them") and the
   same dialog reopens — it looks exactly like a hang. 1.2 s is the verified floor.

### Destructive lesson (120 turns of play lost twice)
`Escape` on the title screen walks into `Do you really want to quit?`; one more click on
the OK bar is `Yes, that's an order, mister!` and **the process exits**. The driver now
classifies `SID MEIER'S ALPHA CENTAURI` / `really want to quit?` as `title`, refuses to
click anything and stops with a saved screenshot; unrecognized/dark screens get a **20 s**
grace period (movies end by themselves) before a single Escape.

## Open problems (M10)

1. **(fixed in M9b: `title` class + 20 s grace; see above)** Escape-spam can end the session. On the unrecognized/movie class the driver
   holds `Escape`; at year 2181 the process disappeared (no crash text in the Wine
   log, window gone) — most likely an Escape on the title/menu screen selecting
   "Exit". Fix: never `Escape` a `movie`/blank screen more than once per ~10 s;
   prefer waiting, and verify the window still exists before each press.
2. **`movie` vs `title screen` are not distinguishable yet** (both are dark, few
   words). OCR the whole frame at 2× and look for `NEW GAME`/`LOAD GAME` to detect a
   fall-back-to-menu.
3. The driver does not *play*: it never gives unit orders, so the AI never fights and
   the research tree stalls at the same few techs. G1 (unattended playthrough)
   needs Script.txt-driven unit/base actions (roadmap 0.3).
4. Dialog answers are policy-free (always "Yes, end the turn", always dismiss).
   Diplomacy, base production and tech choice still need real decisions.

## Cold-boot reproduction check (2026-10-20 16:45)

`soak3_freshboot.log`: fresh launch → one `Return` past the "colony pod has crash landed"
narrative → 15/15 turns advanced, 2101→2116, 8.8–47.8 s/turn, every turn a HUD press plus
one units-not-moved confirm; turns 5 and 8 also required base-screen/movie escapes.
After hardening (window-alive check + Escape throttled to 1/8 s): `soak4_hardened.log` 3/3,
2116→2119, incl. one turn that needed six unrecognized-screen escapes (63.8 s).

## Reproduction

```
sudo sysctl -w kernel.yama.ptrace_scope=0
cd ~/reverse/smac/programs && WINEPREFIX=~/.wine-smac32 DISPLAY=:99 \
  WINEDLLOVERRIDES='mscoree,msxml=' ~/tools/wine-10.20-staging-tkg-x86/bin/wine \
  explorer /desktop=smac,800x600 terran.exe &      # then skip intro, QUICK START
cd ~/reverse/smac && python3 scripts/smac_state.py                     # year=2101 ...
python3 scripts/smac_play.py --turns 20 --timeout 60                   # soak
```

## M14 — why a *loaded* save killed the driver, and what else it exposed (2026-10-20 23:15–23:30)

Falsification test from session 20b, run against a fresh boot + `Autosave 30` (year 2180):
**load the save, print `classify()`'s verdict before the driver touches anything.**
Verdict = `unknown` ⇒ the 20b explanation (mis-classification, not a Wine crash) is confirmed,
and the frame itself says why — `evidence/m15_loaded_words.png`:

```
LOAD confirm pane, drawn OVER the still-visible title art:
  "DIFFICULTY LEVEL: TALENT"   caption bar, y~197   (OCR reads it; "Mission Year 2180" it does NOT)
  portrait + "Provost Zakharov of the University"   y~224
  OK bar centre (290,391)   CANCEL (505,391)
```
It is not `title` (OCR mangles the big title letters behind the pane, so
`sidmeiersalphacentauri` never appears in the squashed text), not `hud` (no TURN COMPLETE
yet), not `dialog` (its caption is at y~196, OUTSIDE the 55..180 dialog band, and its
ncolors=148 ≥ 45) ⇒ it fell to `unknown` ⇒ 20 s grace ⇒ one Escape ⇒ quit ⇒ process gone.

Three classifier fixes, each pinned by a saved frame in `scripts/check_classes.py` (6/6 PASS):

| new/changed class | trigger | evidence frame | action |
|---|---|---|---|
| `cdrom` (new) | `cdrom` + `detected` in squashed text | `m15_boot.png` (was **`title`** — the nag's caption carries the game title, so the driver would have quit at boot) | `Return` |
| `loaded-game` (new) | `difficultylevel` (and not `pick`/`choose`, which is the new-game wizard) | `m15_loaded_words.png` (was `unknown`) | click OK at caption_centre−108, caption_y+194 → derives (287,390) vs the (290,391) that worked live |
| `dialog` (extended) | old flat-panel test **OR** `region_colors(png, TEXTCOL=(350,90,630,320)) < 45` | `m15_stuck_screen.png` (was **`hud`**) | `Return` |

The `dialog` extension is the one that mattered for play: an OPERATIONS DIRECTOR pane that
contains **artwork** (the Morgan "Centauri Monopoly" pyramid) is *not* flat in the old sample
box — 148 colours there, 6 in the text column, where a plain HUD gives 90 — so it read as `hud`
(TURN COMPLETE is still drawn under the pane), the driver hammered the map 11 times and the turn
stalled 156 s at year 2184. With the fix the same situation cleared in **18.6 s**
(`dialog,dialog,dialog` → 2184→2185). A wide-flat-`OK`-bar detector was tried and rejected: the
panes dither (runs alternate `(0,0,0)`/`(13,23,36)`) and the "OK" glyph splits the bar, so no
frame produced a ≥300 px single-colour run.

### Survival + effect on a loaded save

`scripts/smac_play.py --turns 4 --no-escape 60` on the loaded Autosave 30: **4/4 turns,
2180→2184, process alive (pid 370597)** — the 20b failure mode is gone. `--no-escape N` is new:
Escape is never pressed during the first N seconds of a run, so a mis-classified startup screen
cannot quit the game out from under a test.

`scripts/smac_unitpos.py` (new) reads the two arrays verified in session 20 (units
`0x933278`, 119 × 52 B, x@+0 y@+2 flags@+10 owner@+14; bases `0x95da10`, `DAT_00985af4` × 304 B,
name@+19) and snapshots/diffs them. Live on this save: 119/119 unit records inside 0..79,
9 of them on `University Base`'s tile (20,50), 37 named bases.

**Caveat found the hard way: the unit array is packed, so record index is NOT unit identity.**
The first before/after diff claimed 108/119 "moved" but most rows also changed *owner* — records
shift down when units die. Do not report per-index movement without an identity field (none
found yet; candidate: the u16 near +34 that goes `(f<<8)|f' → (0<<8)|f'` after a turn).

**Escape is destructive in-game too, not just at the title.** After 2185 the driver met a dark
screen, escaped after its 20 s grace, and got `Do you really want to quit?` (rows *Oops, no,
wait!* / *Yes, that's an order, mister!*, OK bar y~305) drawn over the live HUD at 2185/Energy 170
(`evidence/m15_title_now.png`). The `title` class refused to click and stopped the run — the game
survived; clicking `400,305` (OK with "Oops, no, wait!" already selected) returned to a clean HUD
(`turn_flags 0`, `cur_player 3`).

**Map clicks still issue no order — measured, not inferred.** With the Scout Patrol selected
(all 9 player units parked on (20,50) after 85 unplayed turns), one click at (75,255) on visible
terrain left **119/119 unit records byte-identical**. That is the positive-control version of the
old vtable+0x124 drag/scroll claim, and it is what stands between the driver and C2.

Also visible in state while the AI round ran: `cur_player` cycles away from 3 mid-round and
`n_bases` grew 37→40 — the year flips only when the whole round finishes, so a late-game round
costs far more than the 8–12 s/turn measured on a fresh 2101 game.

## M15–M18 — watchpoints under Wine, and the first order verified in memory (2026-10-20 23:45–23:55)

### The harness (reproducible, and it does work under Wine)

```bash
cd ~/reverse/smac
timeout 300 gdb -batch -nx -x scripts/m18_watch.gdb -p $(pgrep -x terran.exe) \
        > evidence/m18_watch.log 2>&1 &
sleep 7            # wait for the "Hardware watchpoint N: ..." lines, THEN act on the game
```

`gdb 17.1` on x86-64 attaches to the 32-bit Wine process and **hardware watchpoints fire**
(`Hardware watchpoint 1: *(unsigned short*)0x93351c` …). Limits and rules learned:

- **4 hardware watchpoints, no more** (DR0–DR3). Pick targets deliberately.
- The script must end `detach` + `quit`. A *killed* gdb (M14's note) leaves terran.exe stopped —
  a script that finishes cleanly does not; the game was verified running right after each run.
- The game keeps playing while gdb is attached: `smac_play.py --turns 3` advanced **2185→2188**
  with four watchpoints armed, and the hit landed mid-round.
- gdb prints `Old value = … / New value = …`, which is what turned a location hit into a semantic
  one (67 → 65535).
- Scripts kept: `scripts/m17_watch.gdb` (unit x fields), `scripts/m18_watch.gdb` (order bytes).

### Hit 1 — a purge, not a move (and the fix to session 21's "108/119 moved")

Watched x of four AI-owned records; the first thing that fired was
`Thread 1 hit Hardware watchpoint 4: *(unsigned short*)0x934014 — Old value = 67, New value = 65535`
at `0x5ab2f8`, inside **FUN_005ab240** (`0x5ab240`, 223 B, `shard_015.c:22729`):

```c
sVar1 = (&DAT_009332aa)[param_1 * 0x1a];              // unit+50 = next index
if (-1 < sVar1) (&DAT_009332a8)[sVar1 * 0x1a] = …;    // unit+48 = prev index  → unlink
…
(&DAT_00933278)[param_1 * 0x1a] = 0xffff;             // x  (+0)
(&DAT_0093327a)[param_1 * 0x1a] = 0xffff;             // y  (+2)
(&DAT_009332a8)[param_1 * 0x1a] = 0xffff;             // +48
(&DAT_009332aa)[param_1 * 0x1a] = 0xffff;             // +50
DAT_00991798 = old_x;  DAT_009917a0 = param_1;  DAT_009917a4 = old_y;
```

So the unit array is a **list threaded through +48/+50** (prev/next record indices), removal writes
the 0xffff sentinel in place, and a later compaction pass slides records down — which is exactly
what session 21 misread as "108/119 units moved". Call chain (deepest first):
`0x5ab2f8 ← 0x5a6291 ← 0x588e0b ← 0x4ce54f ← 0x4d124f ← 0x56d027 ← 0x56d2be ← 0x520e1e ← 0x522a1b ← 0x64dd06`.

### Hit 2 — the order byte, found by letting the game tell us the hotkey

The advisor pane said: *"Perhaps this Scout Patrol unit should 'stay home' to defend University
Base from potential danger. **Press the 'H' key** to tell it to 'HOLD' here."* — i.e. a unit was
selected and the game named its own hotkey. `smac_probe.py --key h` (xdotool to the Wine window)
and the selected unit's record changed:

```
unit 0 @ 0x933278  +17: 00 -> 02      +28: ff -> 00      +29: ff -> 00
unit 3 @ 0x933314  +07: 00 -> 04
```

Armed a watch on `+17` of the four records sharing tile (20,50) and pressed `h` again:

```
Thread 1 hit Hardware watchpoint 2: *(unsigned char*)0x933325
pc = 0x4d3888   mov %bl,0x933289(%ecx)     ecx = 0x9c = 3*52   ebx = 2
#1 0x512644  #2 0x516134  #3 0x5cf400  #4 0x5d64cc  #5 0x5d15fd  #6 0x5d0ee6   ← WNDPROC chain
#7 0x7a9fa548  (wine user32 message loop)
```

`0x4d3888` is inside **FUN_004d3770** (`0x4d3770`, 471 B, `shard_012.c:3927`) and the decompiled
body matches the live instructions one-for-one:

```c
void FUN_004d3770(int param_1 /*unit index*/, undefined2 param_2)
{
  if (FUN_00528930(&param_1,0,0xffffffff,0xffffffff,0) == 0) {      // "may this unit act?"
     … tile guard: pbVar1 = DAT_0092ae14 + (DAT_00692184*y + x/2)*0x2c …
     (&DAT_00933294)[param_1 * 0x1a] = param_2;     // unit+28  = live: mov 0xc(%ebp),%ax; mov %ax,0x933294(%ecx)
     (&DAT_00933289)[param_1 * 0x34] = 2;           // unit+17  = live: mov %bl,0x933289(%ecx)  (ebx=2)
     FUN_00584350(param_1);                          // live: call 0x584350  ← the instruction at pc
     FUN_00528d90(); FUN_00528a00(); FUN_0041b710(param_1); FUN_004737e0(x, y, 1);
  }
}
```

`FUN_00584350` is a 34-byte thunk: `FUN_0052a720(0x11, idx, 0, 0, 0, 1, 0x2101)` — the event
broadcast, so **an order is "write unit+17 (+ unit+28), then broadcast event 0x2101 for that unit
index"**. Other writers of the same byte set `2` and `0x18` (`shard_001.c:3334`, `:3365`), and
`FUN_004d3770` itself is called with `10` and `0` as `param_2` (`shard_013.c:4349`, `:4417`,
`:7024`, inside FUN_00512450) — so `+17` is an order enum, not a bitfield, and `+28` travels with
it. **The order enum is not enumerated yet.**

### What this changes for the driver

- **Keyboard orders beat map clicks**: one `xdotool` keypress produced a verified state change,
  where three click attempts (M14, and the M16 production tries) produced none.
- The advisor pane re-shows whenever the selected unit is idle-in-danger; `Close` at (297,430),
  `Don't Show Again` to its left. It does *not* change the screen class (still `hud`).
- Selection **auto-advances** to the next unit after an order executes: the first `h` wrote unit 0,
  the second wrote unit 3.

### Retractions and falsifications this session

- `base record +80` (`0x95da60`) is **the displayed tab**, not the production queue: EXPLORE → 06,
  BUILD → 0xc2, GOVERNOR → 0xc2, and it moved 0xc2→00 when the build chooser closed.
- Three CHANGE→item→OK production attempts changed **no candidate field** anywhere in
  `0x680000..0x9A0000` (2,921 bytes changed, all of them palette/vertex/DP-object churn —
  `0x6b3xxx`, `0x995xxx` `01→02`, `0x99d5xx–0x99ddxx`). C3's queue is either elsewhere or the
  click never took; do not build on it until proven with a different oracle.
- M14's "map clicks issue no order" is **half retracted**: clicks DO land on visible features
  (a click at (585,180) opened University Base's display). The (75,255) null result was a click on
  black void because the map had been panned.

## M19–M23 — the MOVE machinery named; the UI path for a player move still open (2026-10-21)

Session 22b (un-noted, artifacts only) and session 23 together. The oracle that worked is **not** the
hardware watchpoint (see the pitfall below) but a **breakpoint on every instruction that stores to a
unit's x field** — `scripts/m19c_writesites.gdb`, `scripts/m23_writesites.gdb`, log
`evidence/m19c_writesites2.log` (4,463 lines, **739 x-writes**) and `evidence/m23_ws.log` /
`evidence/m23_ws3.log`.

### Where the x-stores are (objdump over the runtime `.text` 0x401000..0x689000)

Only 12 instructions store to `[reg+0x933278]` (x) or `[reg+0x93327a]` (y); 5 of them are reachable
enough to breakpoint: `0x476aa9` (FUN_00476580), `0x4d728c` (FUN_004d6fb0), `0x5ab355` (the setter),
`0x5ab4bc`, `0x5ab573`. The purge store `0x5ab2f1` (writes 0xffff) is deliberately excluded.

### The chain, named (see `NAMED.md` for the per-function evidence)

```
FUN_00502c40(unit_idx, dir, parity, …)            step ONE tile, 8 directions   [0x502c40, 139 B]
   └─ FUN_00502cd0(unit_idx, ?, dest_x, dest_y, …) "move this unit to (x,y)"    [0x502cd0, 18,238 B]
        ├─ FUN_004c1260(…) → FUN_004bf1e0(…)      the mover / re-stacker caller [0x4bf1e0, 8,212 B]
        │     └─ FUN_005a5a80(idx)                re-stack at a tile            [0x5a5a80, 378 B]
        │           └─ FUN_005ab320(idx, x, y)    THE POSITION SETTER           [0x5ab320, 251 B]
        └─ FUN_005a58e0(idx, x, y)                move the WHOLE STACK to (x,y) [0x5a5a8e0 → 0x5a58e0, 109 B]
              └─ FUN_005ab320(idx, x, y)
```
Reached in play from `FUN_00585720` (22,283 B, 6,347 insns — the per-unit action executor; its call of
the stack mover returns at `0x5893a8`, of the parker at `0x588e0b`), from `FUN_0055f650` (the AI hub,
return `0x56890f`), from `FUN_0055c920` (AI move *scoring* — it calls the executor with candidate
destinations read straight out of the unit array: `FUN_00502cd0(param_1,0,(int)psVar25[-1],(int)*psVar25,0,0,0)`
at `shard_014.c:5928`), and from the dispatcher `FUN_0052bce0` **case 0x4402 → `FUN_00502c40()`**
(`shard_013.c:19519`), i.e. the action-packet path solo and MP share.

`FUN_005ab320(idx,x,y)` is the single writer of a unit's tile: it writes `+0`/`+2`, sets `+50 = 0xffff`
and `+48 = FUN_005ab130(x,y)` (the *new tile's* list head), clears the old head, and if the tile is
empty calls `FUN_00582c80(x, y, unit+10)` on the tile record at
`DAT_0092ae14 + (DAT_00692184*y + x/2)*0x2c`. **That is the move-exec function.**

### The 8-direction neighbour table (read out of the file, `.rdata`, matches `FUN_00502c40`'s body)

Two parity variants because a column pair holds two tiles (`x/2` selects the 44 B record, `x&1` the half):

| table | VA | 8 int32 entries |
|---|---|---|
| x-delta, parity≠0 | `0x6784a0` | `+1 +2 +1 0 -1 -2 -1 0` |
| y-delta, parity≠0 | `0x6784c4` | `-1 0 +1 +2 +1 0 -1 -2` |
| x-delta, parity=0 | `0x67850c` | `0 +1 +2 +1 0 -1 -2 -1` |
| y-delta, parity=0 | `0x678990` | `0 -1 0 +1 +2 +1 0 -1` |

So a step east from odd `x` is `dir 1` (+2,0) and from even `x` is `dir 2` (+2,0); `FUN_00502c40` wraps
x by `DAT_0092a378` (map width) unless `DAT_0092a394 & 1`. Cross-checked against the live cursor: an
arrow-Right press moved the inspector readout `(41,11) → (43,11)` = Δ(+2,0), exactly `dir 1` at odd x.

### What the live game did (and did not) do

* **AI turns**: 274 of the 739 x-writes carry real coordinates and come from
  `FUN_005a58e0 ← FUN_00585720` (`0x5a593f ← 0x5893a8`); 274 more write `x = -2` from
  `FUN_005a5cd0 ← FUN_00585720` (parking), 53 write `x = -3` from `FUN_005a5a80`'s scratch pass.
  **These are genuine moves** — the machinery above is what the AI uses.
* **Our units**: pressing `v` (the game's own "switch back to moving pieces", `programs/tutor.txt`
  #TOUR1B) and picking a row in the **Select unit to activate** dialog (`programs/Script.txt`
  #SELECTUNITSELECT area; rows y = 154,194,234,274,314,354,394,434, OK bar (307,486), CANCEL (512,486))
  each fire **8 re-stack writes** (`FUN_005a5a80` → scratch `x=-3` → back to `x=41`) — activation, not movement.
* Arrow keys move a **cursor**, not the selected unit: the terrain panel readout changed
  `(41,11) Flat & Arid` → `(43,11) Rocky & Arid` while the sprite did not move and no x-store fired.
* `Return`, `Space`, `g`, `f`, `Down`, `Right` and clicks at (396,240) and (480,246) produced **zero**
  x-writes with a new coordinate; a tile click only refreshed the centre info panel (it showed
  "Commodities: 1 … NET INCOME: 0/turn" for the clicked tile). Records 117..124 all still read
  `(41,11) owner 3 order 0 +28 0xffff` afterwards.
* ⇒ **C2's move is still open, but the blocker is now narrowed**: the executor and the setter are named;
  what is missing is the UI gesture that calls `FUN_00502cd0`/`FUN_00502c40` for the *activated* unit.
  Next session's cheapest test: breakpoint `0x502cd0` entry and `0x502c40` entry (log args + caller,
  auto-continue) and then try the gestures — the dashed cursor line means the game keeps a cursor
  separate from the selection, so "cursor to destination, then a commit key" is the hypothesis to test.

### New runtime facts (this save, year 2198)

* **The unit array is bigger than the save said**: 166 live records (0..165), records 166+ all zero.
  Session 21/22's "119 records" was the count at load time — a fixed 119-record window silently misses
  every unit created later (our own stack lives at 117..124). Read a window and filter on
  `x != 0xffff && owner < 8 && x < 128 && y < 128` instead of trusting a count.
* Our 8 surviving units are **all stacked on tile (41,11)**, owner 3, threaded by +48/+50 with head 118:
  `118 → 120 → 121 → 123 → 122 → 124 → 117 → 119`. The HUD calls them "Independent", Moves 1, No Order.
* **Faction index → name**, read off the base array `0x95da10` (46 records now) by base name:
  1 = Gaia's Garden ("Gaia's Landing", "Song of Planet"), 2 = Hive ("The Hive", "Social Artery"),
  3 = University ("The Rapture"), 4 = Morgan ("Morgan Construction"), 5 = Sparta ("Sparta Command",
  "Fort Survivalist"), 6 = Circle of Mother ("New Jerusalem", "The Holy Fire"), 7 = U.N.
  ("U.N. Headquarters"). **No base now reports faction 3 as owner** — record 0, "The Rapture" at
  (20,50), reads `+4 = 0x306` where every other record is `(f<<8)|f`; the low byte 6 is read as
  "changed hands to faction 6", which is an inference, not a proof.
  Open contradiction to file: the activate dialog prefixes our units as **"Green"**, and the earlier
  note said own player 3 = University. Unresolved.

### Pitfalls paid for this session

* **gdb has no `silent` command** — it is a `commands`-block word in some other tool. Two of session
  22b's three gdb runs aborted with `Undefined command: "silent"` after only 1–2 hits.
* **Hardware watchpoints on a unit's x are useless while a turn resolves**: all 6 hits in
  `evidence/m19_watch.log` were `rep movsl %ds:(%esi),%es:(%edi)` at `0x64bfa3` ← `0x5abc4b`
  (`FUN_005abb40`, the array compaction) sliding records down — the same trap as the purge, one layer
  deeper. Use store-site breakpoints, or a watchpoint with `Old/New` you can read.
* **Two gdb cannot attach**: while one is attached a second prints `process N is already traced by
  process M` / `ptrace: Inappropriate ioctl for device`, then `The program is not being run` and exits
  — silently leaving you thinking your breakpoints are live. Check
  `grep TracerPid /proc/<pid>/status` before arming, and again before trusting a zero-hit log.
* A map click **pans the view** (widget vtable+0x124 drag branch), so sprite coordinates move between
  clicks: re-measure the white-marker bbox with PIL (`r,g,b > 190` in the map band) after every click.

## M24 — the order plumbing is named end-to-end; the missing piece is a *destination-picking mode*, not a key (session 24, 2026-10-21)

Same live process (pid 370597, year 2198, `cur_player` 3 = our turn, 8 survivors stacked on (41,11),
records 117..124, `selected = 119`). Evidence: `evidence/m24_hot.log`, `m24b_hot.log`,
`m24c_move.log`, screenshots `m24_start.png` (HUD, cursor readout `(41,11)`), `m24_a.png` +
`m24_rc.png` (the SELECT UNIT TO ACTIVATE modal), `m24b_screen.png` (clean HUD, unit panel
"Colony Pod (41,11) Independent Moves: 1 No Order"). Scripts: `scripts/m24_hot.gdb`,
`m24b_hot.gdb`, `m24c_move.gdb`.

### The `in_ECX` singleton base is 0x8f79e0 (exact cross-check)

`FUN_00512450` and `FUN_004d3f70` touch state through `ECX`, which Ghidra prints as `in_ECX`. Live
`$ecx` at both breakpoints = **0x8f79e0**, and the cross-check is exact:
`0x8f79e0 + 0x23bd4 = 0x91b5b4` = the known own-player global. That turns every
`in_ECX + 0x23xxx` reference in `ghidra_out/` into a plain address:

| VA | Ghidra offset | role | live value |
|---|---|---|---|
| `0x91b5b8` | +0x23bd8 | orders-mode flag: non-zero while a unit is selected (`FUN_004d3f70`, `FUN_00476580`, `FUN_00511960` all branch on it) | 1 |
| `0x91b5bc` | +0x23bdc | **selected unit index** — written by `FUN_004d3f70`, read by every hotkey case | 119 |
| `0x91b5c4` | +0x23be4 | order-menu-pending flag; `FUN_00476580` clears it after dispatching | 1 |
| `0x91b5cc` | +0x23bec | set to 1 together with `FUN_0050cab0(1)` on select | 0 |
| `0x91b5e8` | +0x23c08 | index into the cursor/destination lists below | 13 |
| `0x91b5f0` | +0x23c10 | u32 **x-list** of cursor/destination candidates | all 41 |
| `0x91b670` | +0x23c90 | u32 **y-list** (same index) | all 11 |
| `0x91b6fc` | — | mode flag consulted by `FUN_00476580` (its "place a unit here" branch) | 0 |

### Two hotkey dispatchers, both keyed on ASCII key codes (the table M18 left open)

* **`FUN_00512450(code, ?, ?)` — acts on the selected unit** (`ghidra_out/shard_013.c`):
  `0x42 'B'`→u=0xe, `0x45 'E'`→u=0xd, `0x46 'F'`→u=4, `0x47 'G'`→`FUN_004d8b20`,
  **`0x48 'H'`→`FUN_004d3770(sel,10)`**, `0x49 'I'`→`FUN_004d6fb0(sel,-3)`,
  `0x4c 'L'`→`FUN_004d9120(sel,0xb)`, `0x55 'U'`→`FUN_004d1f20`, `0x61 'a'`→
  `FUN_004d3f70(sel.x, sel.y, 1)`, `0x66 'f'`→`FUN_004d9690`, `0x67 'g'`→`FUN_004d6fb0(sel,0x18)`,
  **`0x68 'h'`→`FUN_004d3770(sel,0)`** = the proven HOLD of M18, `0x6c 'l'`→`FUN_004d3510(sel,0)`,
  `0x69 'i'`→…, `0x6f 'o'`→…. Uppercase ≠ lowercase: `'H'` is mode 10, `'h'` is mode 0 (mode is the
  u16 written to `+28`; `+17` is set to 2 by `FUN_004d3770`).
* **`FUN_00511960(?, code)` — acts on the cursor tile** `xlist[DAT_0091b5e8] / ylist[...]`:
  `0x20 Space` → resolve a base at the cursor (`FUN_004e34f0`) then `FUN_0041b780`;
  `0x61 'a'` → `FUN_004d3f70(cursor_x, cursor_y, 1)`; `0x62 'b'` →
  `FUN_004e3700(cursor_x, cursor_y, own player)`.
* The key handler **`FUN_00512b40`** chooses between the two dispatchers and remaps
  `b c d f g h i` → `0x28 0x22 0x25 0x27 0x24 0x26 0x21` — an 8-value directional cluster, i.e.
  **the cursor-movement keys** (matches M23's arrow-key cursor observation).

### The click path, named

* **`FUN_004d3f70(tile_x, tile_y, flag)` = ACTIVATE at a tile** (`s_Console_ACTIVATE`). Proven live:
  a click at pixel (382,212) logged `ACT x=41 y=11 flag=0 sel=119`. It resolves the tile's unit head
  with `FUN_005ab130`, and **when the tile holds a stack it calls `FUN_0048f8b0(idx, s_PICKUNIT, 1)`
  — that is the SELECT UNIT TO ACTIVATE modal**. After a row+OK it re-stacks (4 × `SETTER newx=-3`
  then 4 × `newx=41`, i.e. `FUN_005a5a80`) and calls `FUN_0050cab0(1)`.
* **`FUN_00476580(pixel_x, pixel_y, flag)` = the map widget's click handler** — proven live:
  `MAPH p1=0x1de p2=0xd4` for a click at (478,212), i.e. its params are **raw pixels**. Inside, a
  chosen order code dispatches on the selected unit: `case 4 → FUN_00529a40`, `case 8 → FUN_004d08b0`,
  **`case 10 → FUN_004cffa0` (MOVE)**, `case 0xb → FUN_004d9380`, then `DAT_0091b5c4 = 0`. Its other
  branch is the direct write: **`unit[+17] = 0x18`, `unit[+20] = dest_x`, `unit[+28] = dest_y`**
  (§M25 correction — this read `+24` when the section was first written; see the indexing proof there)
  (u16 each), clear `unit[+18]/[+19]`, `FUN_00584350(idx)` (M18's 0x2101 broadcast), `FUN_00528a00()`,
  `FUN_0050cab0(1)`. A `0x2000000` flag bit selects a multi-waypoint variant that appends the
  destination at `+20 + unit[+18]`.
* **`FUN_004cffa0(unit, dest_x, dest_y)` = issue a move**: ours-and-already-moved → `s_UNITMOVED`;
  otherwise resolve the destination with `FUN_005ab130` + `FUN_005a5c00`, then
  * **solo (`DAT_00920434 == 0`) → `FUN_004cdc70(unit, 0, dest_x, dest_y)`**;
  * netplay → `FUN_00528930(&unit, 4, dest_x, dest_y, 0)` + broadcast
    `FUN_00584010(0x2413, 0, unit, dest_x, dest_y, 0)` + `FUN_00528c10(1)`.
* **`FUN_00528930(int* punit, mode, x, y, flag)` → `FUN_00527f70(mode, unit.x, unit.y, flag, x, y)`**;
  returns 1 with `s_ALREADYDONE` when the unit is spent. Mode **4** = the move order — consistent
  with `FUN_004d3f70`'s `VEH_ORDERS` branch, which treats order bytes **4..0x17** as orders indexed
  `order - 4`.

### What the live game did NOT do (positive controls in the same run)

`scripts/m24c_move.gdb` armed 3 hardware watchpoints (record 119's `+16`, `+20`, `+24` dwords =
`0x934ab4/8/1c`) plus entries for `FUN_00476580`, `FUN_004cffa0`, `FUN_004cdc70`, `FUN_005ab320`'s
store and `FUN_004d3f70`. In that armed state:

* left-click (478,212) with `sel=119, b5b8=1` → **1 `MAPH` hit, 0 `ISSUE_MOVE`, 0 `SOLO_MOVE`,
  0 watchpoint hits** — the click reaches the map handler and stops there;
* right-click (478,212) → the SELECT UNIT TO ACTIVATE modal again (activate path, not a context menu);
* a click on the bottom unit strip → only the 8 re-stack stores.

**Why our clicks cannot land:** all 8 survivors are stacked on one tile, so *every* click on or near
(41,11) raises the picker, and the game never rests in the "one unit selected, awaiting a destination
click" state. Corroboration from the UI spec: `programs/Script.txt:1103 #UNITCLICK` (*All done. /
Cancel orders. / Activate $UNITTYPE3. / Support from $BASENAME2. / Zoom to $BASENAME1. /
Sleep/Board transport. / Hold. / Disband $UNITTYPE3.*) contains **no Move item**, while `#GOTO` is a
caption-only pane "Select Destination" — the move is issued by a *destination-picking mode*, not by a
menu row. **Inference, not proof:** the mode is entered by something we have not fired yet.

Next cheapest test (one launch, same gdb): activate ONE unit out of the picker, then move the cursor
with the `b c d f g h i` cluster (or arrows) and watch `DAT_0091b5e8` / the `0x91b5f0`/`0x91b670`
lists change, then fire `FUN_00511960`'s codes (`'a'`, `Space`) watching `ISSUE_MOVE`/`SOLO_MOVE` and
the +17/+20/+24 watchpoints.

### Pitfalls paid for this session

* **gdb's `printf` is block-buffered when stdout is redirected** — hits appear in the log only after
  ~4 KB or when gdb exits. "No new line yet" ≠ "no hit": read the log *after* `kill -TERM gdb` (this
  run's only `MAPH` line surfaced only after the kill).
* A click on a tile holding a **unit stack** always raises SELECT UNIT TO ACTIVATE, for **either**
  mouse button. Geometry re-measured: rows y ≈ 160..440 step ~40, OK ≈ (295,483), CANCEL ≈ (500,483).
* `MAPH` logs raw click **pixels**, `ACT` logs the resolved **tile** — use that pair as the pixel→tile
  calibration instead of trusting remembered sprite positions: the same tile (41,11) sat at (387,172)
  and later at (382,212) within one session because the view panned.

## M25 — writing the order fields is not the trigger; the issuer is callable but half-executes (session 25, 2026-10-21)

### Correction to §M24 (retraction)

`FUN_00476580`'s direct-write branch stores the destination at **`+20` (x) and `+28` (y)** — not `+24`.
Proof from Ghidra's array indexing: the two writes are `(&DAT_0093328c)[i*0x1a]` and
`(&DAT_00933294)[i*0x1a]`, u16 arrays with `0x1a × 2 = 52` = the record stride, so the byte offsets are
`0x93328c − 0x933278 = 0x14 = 20` and `0x933294 − 0x933278 = 0x1c = **28**`. Independent corroboration
from a freshly loaded save: units of other factions arrive with `+17 = 0x18`, `+20 = 54`, `+28 = 52`
(a far destination) and **`+24 = −1` in every one of them**, while HOLD units carry `+17 = 2` with stale
`+20/+28`. So the record is `{+17 order, +18/+19 waypoint cursor, +20 order-x, +28 order-y}` — and `+28`
is the same field M18 saw `FUN_004d3770` write as the order parameter.

### The solo switch: `DAT_00920434 == 0` (read live)

Live: `DAT_00920434 = 0`, `DAT_0091b5b4 = 3`, map size `0x92a378 / 0x92a37c = 80 × 80`. That one byte is
what makes `FUN_00528930` return 0 without acting (`if (DAT_00920434 == 0) return 0;`) and routes
`FUN_004cffa0` to the solo `FUN_004cdc70` branch — the source-level reason M6b/M7/M8 saw zero netcode
hits in solo.

### Experiment 1 — poke the order fields (no tracer): persisted, not executed

New tool **`scripts/m25_calibrate.py`**: click a pixel (or press a key), then read the HUD tile readout
**and** the M24 globals (`0x91b5bc/b8/c4/e8` + the `0x91b5f0/0x91b670` lists + the selected unit's
record) in one shot — no tracer, no modal-free gdb.

* Four spread clicks and four "adjacent tile" clicks (±48,±36 / ±72 px from the sprite) changed
  nothing: readout, globals and unit records all identical.
* Poked `+17 = 0x18, +18/19 = 0, +20 = 43, +28 = 11` into a unit at (41,11) through `/proc/<pid>/mem`
  (opened `r+b` — writable, no tracer needed). It stuck.
* `scripts/smac_play.py --turns 1` advanced **2194 → 2195 in 18.5 s**; afterwards the order is still on
  the record, which had **slid from index 127 to 124** under the compaction pass. All 8 of our units are
  still at (41,11).

**Verdict: the engine trusts those fields (they survive compaction and a turn boundary) but writing them
does not trigger execution.** The trigger lives in the code path, not the record.

### Experiment 2 — call the issuer from gdb

* Attempt 1 (`scripts/m25_issue_move.gdb`, fired **while the SELECT UNIT TO ACTIVATE modal was up**): the
  call got to `FUN_004cdc70`'s second statement — `unit+4 |= 0x40` appeared in memory — then
  **SIGSEGV**. After gdb quit, the process was alive but the **UI was dead**: clicks on CANCEL (500,483),
  on row+OK, and on TURN COMPLETE changed nothing while the main thread stayed `R` with climbing `utime`
  (+53 jiffies / 2 s). Only a relaunch recovered it.
* Attempt 2 (`/tmp/m25b_call.gdb`, clean HUD, `$ecx = 0x8f79e0` preset): `Breakpoint 1 at 0x4cdc70` fired
  *inside* the injected call, so gdb abandoned the expression ("The program being debugged stopped while
  in a function called from GDB") and detached; the game finished the call on its own. Again
  `unit+4 |= 0x40`, again **no move and no order byte written**.

**Inference, not proof:** `FUN_004cffa0`'s empty-destination branch hands off to `FUN_004cdc70`, which
first validates the target tile through `DAT_0092ae14 + (DAT_00692184*y + x/2)*0x2c` (read live: tile
array pointer `0x40a6660`, row stride 40, 44 B records; no base sits on (41,11) or (43,11) among the 44
bases) and whose visible head is artillery-bomb logic (`_rand()`, `s_ARTYBOMBFAILED`) — so mode 0 for a
move-capable unit must take a branch further down the 2 KB function that we have not read. **Open: which
precondition our injected call failed** (movement points? `FUN_005acc00`/`FUN_005acab0`? the
`unit+4 |= 0x40` marker meaning "action in flight"?).

### Recovery: relaunch + load — and one save-format fact

`evidence/m25_wine.log`, `m25_boot.png`, `m25_t2.png`, `m25_t3.png`, `m25_t7.png`:
* kill terran + its `winedevice.exe`, relaunch (`~/tools/wine-10.20-staging-tkg-x86/bin/wine`,
  `WINEPREFIX=~/.wine-smac32`, `DISPLAY=:99`) → nag `Return` → main menu (START GAME / SCENARIO /
  **LOAD GAME (610,344)** / MULTIPLAYER / CREDITS) → LOAD list → **a single click selects a row and
  fills the filename box; OK is at (343,491)**, CANCEL (511,491); rows at y 264/288/312/336/360/**384**/
  408/432 in lexicographic order (1, 10, 2, 20, 3, **30**, 4, 5) → confirm dialog → OK (290,391) → HUD.
* **`Autosave 30.SAV` loaded at year 2194, not 2180** — the soak overwrote it in place. "Autosave N"
  is not a stable snapshot; pin a copy before relying on it.

### Pitfalls paid for this session

* **Never inject a gdb `call` while a modal dialog is up** — the call runs inside the dialog's own
  message loop; here it segfaulted and left a live-but-unresponsive game.
* A gdb `call` into game code is unsafe in general: breakpoints firing inside the called function make
  gdb abandon the expression and detach, and the inferior then returns to gdb's dummy frame.
* `/proc/<pid>/mem` opened `r+b` pokes values with no tracer at all (and no ptrace-stop).
* `smac_probe.py --save` is silently ignored when `--quiet` is also passed (the copy happens in
  `show()`); copy `/tmp/<tag>.png` yourself.

---

## §M26 (session 26, 2026-10-21): the 0x18 order is MOVE; `FUN_004cffa0`/`FUN_004cdc70` are the ATTACK path

Static (all from `ghidra_out/`, no re-derivation needed):

1. **`FUN_004cdc70(unit, mode, x, y)` is NOT a move branch — it is the bombard/arrival resolver.**
   Its 11 strings are `ARTYBOMBFAILED`, `BOMBFAILED`, `BOMB_SUCCEEDED`… `Arty Failed the Hard Way`,
   `ATEFOREST`, `ATESTUFF`, `HAVEDESTROYED(1)`; body: `FUN_005acdb0(unit)` then `unit+4 |= 0x40`,
   terrain/ownership checks on the destination tile record (`DAT_0092ae14 + (40*y + x/2)*0x2c`),
   a `_rand()` 50% coin (fail → advisor `ARTYBOMBFAILED`), a second 25% roll for movement-class-2
   types, then a 19-class facility-destruction loop over the tile's `+8` mask (`FUN_00582ed0`,
   `FUN_00582fc0` ownership, `FUN_0056d350(unit,0,5,ax,ay,-1)` attack) — every path ends
   `FUN_00585720(unit, -1, 3)`. This is why the M25 injected call "reached `FUN_004cdc70`, wrote
   `unit+4 |= 0x40`, and did not move the unit": it was bombing, not walking.
2. **`FUN_004cffa0(unit, x, y)` = issue attack/engage toward a tile.** Gate: `FUN_005acc00(unit)`;
   0 → advisor `s_UNITMOVED` ("already moved") + return. Empty destination (`FUN_005a5c00` on
   `FUN_005ab130(x,y)` < 0) → solo: `FUN_004cdc70(unit,0,x,y)` (bombard); netplay: `FUN_00528930` +
   packet `0x2413`. Destination occupied by a non-friendly unit → `FUN_00596360(fromx,fromy,x,y,·)`
   computes the direction → solo: `DAT_0091f6dc = 3;` `FUN_00502c40(unit, dir, 1, 1, 0)` = step one
   tile toward it. Neither branch ever writes `+17`.
3. **`FUN_005acc00(unit)` = "can this unit still act?"** (the gate NEXT_PROMPT queued): on-map ∧
   owner == own (`0x91b5b4`) ∧ not busy (`+10` bits `0x40`&`0x400` not both) ∧ `unit+4 & 0x4200 == 0`
   ∧ order ∈ {0,1,2,3} passes the order test (0 and ≥4 pass) ∧ **movement points**: `FUN_005ac650(unit,0)`
   (total) − byte `+40` (used) > 0. Sibling `FUN_005acab0(unit)` = idle check (on-map, own, not busy,
   `FUN_005accd0(unit) == 0`). `FUN_005acdb0(unit)` = `+40 = FUN_005ac650(unit,0)` = **consume all
   movement / "done moving"** — called by the bombard resolver head and the executor tail.
4. **`0x18` in `+17` IS the queued MOVE order** (enumerated every store site in the corpus):
   written by the click handler direct branch (`FUN_00476580` lines 222–225: `+17 = 0x18`,
   `+20/+28 = dest`, `+4 = 0`; variant at 261–267: `+4 |= 0x2000200`, dest indexed by waypoint
   byte `+18`), by the hotkey order-issuer `FUN_004d6fb0(unit, param_2, …)` (`+17 = param_2`;
   `0x18` branch writes `+20/+28` from the target record and clears `+4` bit 16; then
   `FUN_00584350()` = broadcast `0x2101`), by the AI hubs (`FUN_0055f650` writes 0/2/3/4/6/7/9/0xb/
   0xd/0xe/0x14/0x18/0x1b/0x1c/0x58; `FUN_0055c920` move scoring writes 0x18 ~15×), and by the
   executor itself (waypoint advance). `FUN_004cce50(unit, k)` writes `order = k + 4` (named-order
   setter; readers subtract 4). HUD order-icon renderer `FUN_004bd3d0` distinguishes `0x03`,
   `& 0x3f == 0x18`, `0x19`, `0x1b/0x1c`. Netplay dispatcher `FUN_0052bce0` copies packet field
   `+0xc` into `+17`. Watchdog inside the executor: counter `+42` increments whenever own-player
   unit has order `0x18` or flags `+4 & 0x4200` and made no progress; `> 0x1f` → advisor
   `s_KEEPMOVING` + cancel (`+17 = 0`, `+4 &= ~0x4200`… mask `0xfcffbdff`). Waypoints: `+18` = leg
   count, `+19` = current leg, `+20`(x)/`+28`(y) arrays indexed by leg; `+41` = last direction,
   `+40` = movement used. Key router `FUN_00512b40` converts a `0x18` order to `0x19` on a
   directional-cluster key and calls `FUN_00529090(unit, dir, 0)`.
5. **Solo orders execute SYNCHRONOUSLY through `FUN_00529090(unit, dir, mode)`:**
   `if (DAT_00920434 == 0) return FUN_00585720(unit, dir, 3);` — its callers are the HOLD setter
   `FUN_004d3770(unit,-1,0)` (the proven `h` path — that is why `h` lands instantly), the key router
   `FUN_00512b40(unit, dir, 0)`, `FUN_004d1e90(unit,-1,0)`, `FUN_004ce4a0/0x4ce710(unit, dir, 1)`,
   and the netplay dispatcher. In netplay mode 0 first tries `FUN_00528930` and can print
   `s_MOVEPENDING`. `FUN_0050cab0(flag)` = selection-refresh state machine (reads `DAT_0091b5bc` via
   `in_ECX+0x23bdc`, calls `FUN_005acab0`, arms move UI via `FUN_005a3470` when `+40 == 0`).

Live (game relaunched: pid 882970, **Autosave 30 on disk is now year 2110** — autosave slots are
overwritten in place, newest = Autosave 2 @ 2198; M25's warning reconfirmed):

* **Clicks were DEAD, not the gestures:** `XQueryPointer` reports the pointer under the Wine
  *desktop* window `0x400004` ("smac - Wine Desktop", explorer.exe) — a pointer grab; the first real
  click breaks it and every click after lands (`MAPH p1=0x106 p2=0xfb` logged 2/2 clicks after the
  break). Keys always arrived (`KEYROUTE a1=0x68/0x67/0x64/0x1b` for h/g/d/Esc) but `KEYSEL`/
  `SOLOWRAP` fired **0×** — `FUN_00512b40` swallows hotkeys while `b5c4 = 1` (order-menu-pending)
  and `b5b8 = 0`; `v` *clears* `b5b8` (1→0); arrow keys and clicks only move the cursor candidate
  list `0x91b5f0/0x91b670` (history: (17,7)→(19,7)→(15,9)→(11,11)→(8,14)).
* **Load flow gotchas:** a fresh load opens the base screen with an OPERATIONS DIRECTOR modal on
  top (it ate the first key round; dismiss row (400,307)→OK (400,362), then Escape closes the base
  screen). The LOAD pane is a file browser that opened at host root (Z:) — type
  `home/n100/reverse/smac/programs/saves/auto` into the name box (row click + OK navigates); saves
  live in `programs/saves/auto/`, 8 files, save-30 row y 384, OK (345,555), CANCEL (490,555).
* **Test A (poke + injected call):** poked rec0 (`sel=0` live) `+17=0x18, +20=19, +28=7, +4=0,
  +40=0`, then `call (int)0x529090(0, -1, 0)` with `$ecx = 0x8f79e0`, no breakpoints armed. The
  executor RAN (`mpused 0→3` appeared, `b5c4` cleared 1→0) then **SIGSEGV'd at PC `0xe921da34`**
  (Wine stack/guard region, not mapped in the final maps — the call corrupted its own return path);
  gdb abandoned the expression, detached; **the unit did not move** (x stayed 17). Game survived
  healthy (state R, keys responsive, class=hud). So M25's "call reaches but no move" is now pinned:
  the injected executor call SEGVs before the walk, in Wine space — a calling-convention/frame
  problem, not a semantic gate.
* Positive controls: 14 breakpoints + 3 watchpoints armed and logged (log `evidence/m26_live2.log`,
  call log `evidence/m26_call.log`); `m26_arm.py` initially emitted `0x0x933288` (double prefix) and
  gdb died at line 3 — a zero-hit log meant "nothing armed" (the known pitfall, biting again).

**Open for M27:** (a) find what sets `b5c4`/`b5b8` (order-menu arming; writes of 1:
`shard_013.c:2657/2802/3029/12709` — functions unattributed); (b) the gesture is probably: arm
order mode (click unit sprite or picker) → click destination → `FUN_00476580` direct branch writes
`0x18` + broadcast — never yet fired because arming never stuck; (c) the injected-call SEGV: try
`call FUN_00529090` with `set $esi/$edi` from a live game context, or better, break *inside* the
game's own SOLOWRAP hit and inspect a real (unit, dir) pair; (d) unit record 0 still carries
`order=0x18 mpused=3` — harmless, the watchdog/turn will clear it.

## §M27 (session 27, 2026-10-21): the player MOVE gesture is an ARROW KEY — live-proven through the game's own `FUN_00529090` call

**Retraction of the M23–M26 line "arrow keys only move a cursor".** They move the cursor only when
no unit is active. With a unit selected (`DAT_0091b5bc` ≥ 0) and orders mode on (`DAT_0091b5b8 != 0`),
an arrow key **moves that unit one tile, synchronously** — the M24–M26 "missing gesture" was the
arrow key all along; the failure was that every earlier arrow test ran with no unit selected (or
while `b5c4=1 ∧ b5b8=0` swallowed hotkeys).

### Static path (all from `ghidra_out/`)

`FUN_00512b40(param_1, param_2)` — after the modal/Escape shortcuts it reaches the directional
dispatch (≈ lines 1774–1815 of the C dump):

```
case 0x21 → dir 0 ; 0x22 → 2 ; 0x23 → 4 ; 0x24 → 6
case 0x25 → 5 ; 0x26 → 7 ; 0x27 → 1 ; 0x28 → 3        // 8-way dir index
...
if (DAT_0091b5b8 != 0) {                              // orders mode
  if (FUN_004e1f90() == 0 && selected >= 0) {
    if (FUN_005255e0() == 0) {
      if (FUN_005acc00(selected) == 0)                 // can-act gate (MP remaining)
          FUN_00483470(s_UNITMOVED_0068df64, 5000, 0, 0);
      else FUN_00529090(selected, dir, 0);             // ← the solo synchronous wrapper
    } else FUN_00483470(s_SIMULNO_0068df5c, 5000, 0, 0);
  }
}
```

and the `param_2 & 0x10000` (Shift) variant of the same block writes a **queued** order instead:
`+17 = 0x19`, `+20 = dir`, `+22 = unit x`, `+30 = unit y` (`DAT_00933289/8c/8e/96`), i.e. Shift+arrow
sets a one-leg directional order rather than stepping on the spot.

### Live (pid 914079, Autosave 2 = year 2198/2199, our turn)

1. Unit rec117 at (41,11), `order=0 mpused=0`. One `Right` key → **(43,11)**, `dir=1`, `mpused 0→6`
   (a single direction-1 step at odd x is Δ(+2,0); `+40` counts movement points in thirds — one step
   = 3, total 6, so a fresh unit gets **two** steps/turn).
2. End turn (2198→2199) stalls in the AI phase with `cur_player` = an AI faction and `turn_flags & 2`:
   two modal popups hold it — a PSI-COMBAT **DATALINKS** page (dismiss with `Return`) and an
   **OPERATIONS DIRECTOR** pane (dismiss with a single `Escape`, which closes the pane, not the game).
   After both, `cur_player = 3`, `turn_flags = 0x100000`.
3. Armed `scripts/m27_solowrap.gdb` (3 entry breakpoints, no watchpoints) and pressed `Right` three
   times through `scripts/m27_run.sh` (records gdb's PID; see pitfall). The log
   `evidence/m27_solowrap2.log` is the milestone's proof — the **game's own** calls:

```
SOLOWRAP idx=117 dir=1 mode=0 → EXEC idx=117 dir=1 mode=3 → SETTILE idx=117 x=-2 y=-2 ; SETTILE idx=117 x=45 y=11
SOLOWRAP idx=118 dir=1 mode=0 → EXEC idx=118 dir=1 mode=3 → SETTILE idx=118 x=-2 y=-2 ; SETTILE idx=118 x=45 y=11
SOLOWRAP idx=120 dir=1 mode=0 → EXEC idx=120 dir=1 mode=3 → SETTILE idx=120 x=-2 y=-2 ; SETTILE idx=120 x=43 y=11
```

   i.e. **key → `FUN_00529090(unit, dir, 0)` → `FUN_00585720(unit, dir, 3)` → `FUN_005ab320` writes the
   new tile**, with the selection rolling to the next unit that still has movement points. No
   injection, no poke: this is the game issuing its own order.
4. Post-state (all 8 survivors, `/proc/<pid>/mem`): 117 (45,11) `mpused=3`; 118 (45,11) `mpused=3`;
   119 (43,11) `mpused=6`; 120 (43,11) `mpused=6`; 121–123 still (41,11) `mpused=0`; order byte 0 on
   every one (a stepped move completes and clears the order — `0x18` is only for multi-tile
   destinations). Screenshot `evidence/m27_after_move.png`.

### Consequences for the reimplementation (C2)

* Movement input is **direction-based**, not destination-based: `dir` 0..7 indexes the parity-split
  delta tables already named in M19 (`0x6784a0/0x6784c4/0x67850c/0x678990`), and one call moves
  exactly one tile and spends 3 movement points.
* Destination moves (`+17 = 0x18`) and Shift+arrow quads (`+17 = 0x19`) both resolve through the same
  `FUN_00585720(unit, dir_or_waypoint, 3)` executor; only the *issuer* differs.
* The can-act gate (`FUN_005acc00`) is what prints `UNITMOVED`; refusing a move is a normal, visible
  game response — useful as a negative control in the driver.

### Pitfalls paid for this session

* **`pkill -f <gdb-script-name>` inside the same shell command kills that shell** (the pattern matches
  the command line; shell exits with −15 and the sequence after it never runs). Capture gdb's PID
  (`gdb … & GPID=$!`) and `kill -TERM $GPID` instead — `scripts/m27_run.sh` does exactly this.
* **Loading by hand: the LOAD dialog's name box keeps whatever was in it.** `ctrl+a`/`Delete` do not
  clear it; a typed unix path is prefixed by the dialog and yields `LOAD ERROR — FAILED TO OPEN FILE`.
  Working sequence: click the name box at **(400,252)**, `End`, ~200 `BackSpace`, type the **Windows**
  path `Z:\home\n100\reverse\smac\programs\saves\auto\Alpha Centauri Autosave 2.SAV`, `Return`.
  Then the load-confirm OK is (290,391).
* **The title screen still classifies as `unknown`** (`ncolors=165`, "START GAME"/"LOAD GAME" legible
  to OCR) — `m26_load.py` therefore times out in phase 0 and its repeated `Return` presses are what
  bounce you back to the menu. Drive the title by coordinates, not by the classifier.
* An AI-phase stall is not a freeze: read `cur_player` + `turn_flags` and dismiss the modal that is
  up (DATALINKS → `Return`, OPERATIONS DIRECTOR → one `Escape`).

## §M28 (session 28, 2026-10-21): a map click can only order a move when the map pane is in *mode 9*

**Question.** M24 saw `FUN_00476580`'s "direct-write" branch set `+17 = 0x18` with `+20/+28` from the
click, yet no live click ever produced it. Why?

**Answer (live-proven): the branch is gated on the map pane's mode pointer, which is null on the normal HUD.**

* `FUN_00476580(pixel_x, pixel_y, button)` opens with `local_2c = ([this+0x1ef4c] == &DAT_0091cae4)`,
  where `this = [0x7cdecc] = 0x8f79e0` (the same singleton M24 identified). Mode 9 of the pane's mode
  table is `&DAT_0091cae4`.
* Live at click time: `this=0x8f79e0`, **`[this+0x1ef4c] = 0`** ⇒ the destination branch is skipped.
  Clicks at (480,250) and (470,300) fired the entry `MAPH p1=0x1e0 p2=0xfa p3=0` only; breakpoints on
  all three `mov BYTE PTR [..+0x933289],0x18` stores inside the handler — `0x476ac7`, `0x476bae`,
  `0x476c39` — fired **0 times**, and none of the three early-return gates fired
  (`0x47674d` `FUN_0046a310 != 0`, `0x476778` `FUN_00469060 == 0`, `0x4767ab` `[this+0x1dd8c] != 0`).
  The click therefore falls through to the base/`DESTTRIAD` branch and issues nothing. Artifacts:
  `evidence/m28_gates.log`, `evidence/m28_gates2.log`, `evidence/m28_clickgate.txt`.
* Mode table: `FUN_0050ba00(idx)` / `FUN_0050ba90(idx, …)` store `[this+0x1ef4c] = &DAT_0091c958 + idx*0x2c`.
  Corpus callers set only **8, 0xb, 10** (`FUN_004d8c20`, `FUN_004d9120`, `FUN_004d9690`). **No corpus
  caller passes 9**, so "the next click is a destination" is entered from a site the decompiler did not
  attribute (indirect call). That unattributed setter is the remaining lead for click-to-destination.
* Order-menu dispatcher `FUN_00512450(command_id, key, …)` is the other half: case `0x67` calls
  `FUN_004d6fb0(selected, 0x18, 0)`, and the key router's `case 0x6a` (`j`) calls
  `FUN_004d6fb0(selected, 0x18, 1)`. **Correction to the M27 write-up: that 0x18 is a *base-targeted*
  move, not a tile move** — the destination is `(&DAT_0095da10)[base*0x98]` / `(&DAT_0095da12)[base*0x98]`
  (base x/y), and the routine no-ops when the unit already stands on that tile. So the two 0x18 issuers
  are different features: pane-mode-9 click = move to an arbitrary tile; `FUN_004d6fb0` = "move to base N".

**Consequence for the harness.** Arrow-key stepping (M27) is still the only *drivable* player move.
A click cannot move a unit while the pane mode is null, so "click the unit, then click the destination"
is not reproducible until a way into mode 9 is found (watch `[0x8f79e0+0x1ef4c]` for `0x91cae4` while
driving the order menu, the unit action buttons, and the right-click menu).

## §M29 (session 29, 2026-10-21): the turn driver asks memory whose turn it is — 11/11 turns clean

**Problem.** M27's 2198→2199 stall was not a deadlock: during the **AI phase** the HUD is still drawn
and TURN COMPLETE is still clickable, so an OCR-only driver clicks it into a half-finished AI turn and
then parks in whatever modal the AI raised until the timeout expires.

**Fix.** `scripts/smac_play.py::service_turn` now reads state each loop and computes
`ai_phase = (cur_player != player) or (turn_flags & 2)`. In that state it services modals only:

* `Return` for DATALINKS / PSI-COMBAT / event pages (full-screen text, default button = OK);
* **one** `Escape` for an OPERATIONS DIRECTOR or base pane (closes the pane, not the game);
* a plain HUD is left alone (no TURN COMPLETE click), just polled.

Recognizers added: `is_datalinks()` (datalinks / psicombat), `is_ops_director()` (operations).

**Live proof.** Two runs back to back, `evidence/m29_3turn.log` (2202→2205) then `evidence/m29_8turn.log`
(2205→2213): **11 consecutive turns, 0 stalls**, 7.4–12.9 s each. Turn 5 of the second run is the case
that used to hang it — `[dialog] t CHIEF PLANETOLOGIST … Hercules has receded from perihelion` during the
AI phase → `ai-phase:dialog` → `hud` → year flipped in 12.3 s
(`evidence/trace_20261021_130418.jsonl`, turn 5).

## §M30 (session 30, 2026-10-21): what a turn IS — 20-turn state trace and the loop model

**Method.** `scripts/turn_trace.py` samples `year` (0x985B00), `cur_player` (0x985DCC), `turn_flags`
(0x985AE8) and the base count every 0.2 s while `smac_play.py` drives 20 turns, logging only changes.

**Model (evidence: 67 state changes, `evidence/m30_turn_trace.jsonl`).**

1. Our phase is `turn_flags == 0` with `cur_player == player` (3). This is the only state in which input
   (arrow keys, TURN COMPLETE) does anything.
2. Pressing TURN COMPLETE sets `turn_flags |= 2` (0x2) and the engine walks the AI factions, writing each
   one's index into `cur_player` as it runs that faction's phase. Observed indices during the walk:
   **0, 1, 2, 4, 5, 6, 7** — every active faction *except* 3.
3. `cur_player` is **never 3 while `turn_flags & 2`**: the year increments as the walk completes, and only
   then does the state become `cur == 3, tf == 0`. So "year changed but `cur_player != player`" means the
   cycle is mid-flight, not hung.
4. Years advance exactly 1 per cycle in this period.

**Cost split (201.2 s for 20 turns, 2213→2233).** 34.9 s (17 %) inside AI phases, 166.4 s (83 %) in our
phase — but the game is idle for most of our phase; the driver's OCR + click loop (~8–9 s/turn) is the
real cost, so a reimplementation's turn latency budget belongs almost entirely to us, not the AI.
Sampling at 0.2 s catches 1–5 distinct AI players per cycle (short phases can be skipped entirely between
samples), so treat 8 faction phases as the structure and the visible count as a sampling artifact.

**Artifacts:** `evidence/m30_turn_trace.jsonl` (state changes), `evidence/m30_summary.txt` (driver log +
per-year player sequences), `evidence/trace_20261021_131002.jsonl` (20 turn records).

**Consequence for R1 (headless sim).** The loop needs: 8 faction slots, a per-faction phase, a single
year counter incremented once per full cycle, and a `cycle_in_progress` flag that gates input to the human
faction — i.e. `turn_flags & 2` is a real gate, not decoration.

## §M31 (session 30/31, 2026-10-21): base record map v1 — population, growth, and the mineral accumulator

**Method.** `scripts/base_trace.py` snapshots the whole 304-byte base array once per year-change while the
driver runs (10 + 8 turns, 2233→2251), writes `evidence/m31_bases_<year>.bin`, then diffs every u16 of a
tracked base. Analysis is by **name**, not index.

**Lesson paid for: a base index is not an identity.** Records slide in the array (a new base is founded or
one is destroyed), so tracking index 0 renamed itself to another base mid-run and index 1 jumped three
fields at once. Track bases by the name at **+19**.

**Layout (verified):**

| off | field | evidence |
|---|---|---|
| +0 / +2 | x / y | 0..79 on an 80×80 map, matches the base's tile |
| +4 | flag byte | 0x06 on most bases |
| **+5** | **faction byte** | distribution {1:10, 2:19, 4:6, 5:8, 6:10, 7:8, 3:1..0}; the u16 at +4 is `flag \| faction<<8` — **the old "faction at +4" was wrong** |
| +6 | **population** | 3–7 across 62 bases, correlates with base importance (Gaia's Landing 7, Sparta Command 3) |
| +7 | **growth countdown** | counted 6→0 one per year for our base, then sat at 0 |
| +19 | name (NUL-terminated) | unchanged |
| +48 / +50 | flag words | +48 alternates 16514↔16546 (bit 0x20), +50 jumps 768→896/2816 |
| +60 | per-base turn counter | +1 or +2 per year, resets on a spend (Gaia 51→77 then 2) |
| **+64** | **mineral accumulator** | +5..+9 per turn, resets on production completion **with a ~1/4 carry** (54 → 5, 73 → 0); **+152 mirrors it exactly in all 62 bases** |
| +68 | small signed value (u16 −6 … 458) | moves by a few per turn; energy-like, not yet proven |
| +120 / +122 | large pair | 169–33k; scales with faction size; unnamed |
| +132 / +140 | medium counters | 0–218; unnamed |

**Measured deltas (Gaia's Landing, 19 consecutive years).** `+64`: 40 → 0 → 4 → 8 → 13 → 18 → 18 → 28 →
33 → 38 → 43 → 48 → 54 → 5 → 11 → 20 → 25 → 30 → 35 — i.e. **≈5–10 minerals/turn**, completing an item at
~54 and keeping 5 (SMAC's quarter-carryover rule). U.N. Headquarters ran 15 → 2 → 8 → … → 73 → 0 at
**≈6–8/turn**. This is the first base-economy number measured out of the live game.

**Not in this record.** Only 5 of 152 u16 lanes changed for our own base over 11 years, and 15–31 lanes for
large AI bases — the per-tile worker assignment and the tech/energy ledgers are elsewhere. The 304-byte
record is base *state*, not base *accounting*.

**Artifacts:** `evidence/m31_bases_2233.bin … m31_bases_2251.bin`, `evidence/m31_bases.json`,
`evidence/trace_20261021_131512.jsonl` (10-turn run).

## §M32 (session 32, 2026-10-21): the order menu is mapped — every hotkey → setter → order byte, live-proven

**Full table: `ORDERS.md`.** Summary of what was proven and how:

* **Key model (live):** `FUN_00512b40(param_1 = typed char, param_2 = VK code | modifier
  bits` — Shift = 0x10000, Ctrl = 0x20000). Letters arrive as VK-uppercase (`h` → VK 0x48),
  punctuation as OEM VKs (`/` → 0xbf). Numpad VKs 0x60–0x69 zero `param_1` (the "b c d f
  g h i" remap M24 saw is the **numpad** direction cluster, not letters). With orders mode
  on ∧ `FUN_004e1f90() == 0` ∧ selected ≥ 0, non-directional keys go to
  **`FUN_00512450(char, FUN_0064d300(char), VK|flags)`**, where **`FUN_0064d300` = tolower**
  (live: `M`→0x6d, `G`→0x67). Menu rows reuse the handler with `param_2 = (menu<<8)|char`.
* **`FUN_004d44d0(unit, mode)` = issue_terraform_order**: `mode` indexes alpha.txt
  **#TERRAIN** (20 rows, hotkey strings included — `data/alpha.json`), and the issued order
  byte is **`+17 = mode + 4`** (matches the order−4 indexing rule). Class gate: unit class
  must be 9 (Former) else advisor `NEEDTERRAFORMERS`. Payment path debits faction energy
  **`DAT_0094d650[player*0x82f]`** (`Want_to_terraform`/`TERRACOST`/`TERRAPAY` dialogs).
  Mode rewrites: 5→6 Road→MagTube when a road exists; 0→1 Farm→Soil Enricher; 0→0xa
  Farm→remove-Fungus. Live-verified modes: 0,2,3,5,7,8,9,0xc,0xd,0xe,0xf,0x10,0x11,0x12.
* **Named orders (all live through the game's own calls):** `h` HOLD 2 (rec56 order 0→2
  end-to-end); `l` Sentry 1 via `FUN_005ab420`; `o` Sensor (mode 9) or `CONVOY` 3 on class-10
  units (`FUN_004d94d0`); `g` queued 0x18 move to own base; `G` join-base garrison
  (`FUN_004d8b20`: `+46` = base idx + roster re-count); `U` unload toggle; `r` Road (mode 5);
  `d` bombard family (`FUN_004d6100` → `FUN_004cdc70` tail); `p` clear waypoints + pane mode
  8; menu 'R'/'T' → `FUN_004d8920` → orders **0x1b/0x1c = road/tube-to-base** (`+20` = base
  *index*; `#ROADTO`/`#TUBETO` pickers); menu 'D' → designate toggle `+4 ^= 0x80`; menu 'U'
  → upgrade chooser; 0x30055 → give-unit.
* **`/` = clear + EXPLORE** (not just cancel): `FUN_004d9470` cancels, writes `+17 = 0`,
  sets `+4 |= 0x4000`, and the broadcast makes the dispatcher walk the unit toward the
  nearest unexplored tile (`EXEC idx=56 dir=7 mode=3 → SETTILE (43,9)`). In run 1 unit 57
  explored onto an **alien artifact** at (42,12) → OPERATIONS DIRECTOR modal.
* **Modal = key sink (mechanism):** while a modal is up the pump never calls
  `FUN_00512b40` — 19 keys after the artifact modal produced **zero** `KEY` hits. Screen
  class check before key sequences is mandatory (M29 rule, now mechanistically explained).
* **Proof:** `evidence/m32_keys.log` (run 1: `h`→`HOLD idx=56 mode=0`, `/`→`CLEAR`),
  `evidence/m32_keys2.log` (run 2: 19 keys, every predicted setter fired with the predicted
  mode arg), `evidence/m32_keys{,2}_state.txt` (per-key record snapshots). Scripts
  `scripts/m32_keys.gdb` (29 bps) + `scripts/m32_run.sh` (`M32_KEYS=…`).
* **Left running:** pid 914079, year 2251, our turn, HUD clean, TracerPid 0. rec56 explored
  to (43,9) (mp=3, flags 0x4014004), rec57 on the artifact (42,12) order 0x18 done, rec58
  (43,11) selected. The explore orders will walk 56/57 further on the next turn — either
  let them (free exploration) or poke `+17 = 0` / clear `+4 & ~0x4000` first.

## §M33 (session 33, 2026-10-21): the driver issues a real order — C2 closes

**The chain, live-proven in one run (`evidence/m33_try5.log`):** driver pokes the
selected-unit global `0x91b5bc` → presses `f` via xdotool → game pump dispatches
`KEY p1=0x66 p2=0x46` (`FUN_00512b40`) → `DISP p1=0x66 p2=0x66 p3=0x46` (`FUN_00512450`)
→ `TERRAF idx=53 mode=0x0` (`FUN_004d44d0`, the M32 setter) → unit record `+17` 0→**4**
(Farm = #TERRAIN mode 0 + 4). **The order byte then persisted across two full turn
advances (2252→2253→2254) and a compaction slide (rec53→rec52) — read purely through
`/proc/pid/mem` (`evidence/m33_turns.jsonl`, `evidence/m33_final_pre.json`/`_post.json`).**
C2's gate ("driver issues one real order + state reader proves the effect", effect =
order byte persists) is met.

* **Assembly-verified order-store tail** (`objdump` of the same bytes): `0x4d5bb0 mov
  0x8(%ebp),%eax` (unit idx) / `0x4d5bb3 mov %bl,%cl; add $0x4,%cl` (mode+4) /
  **`0x4d5bbf mov %cl,0x933289(,%edx,4)`** (the `+17` store) / **`0x4d5bc6 call 0x584350`**
  (broadcast 0x2101) / `0x4d5bda` pushes `s_TERRAFORM` tutor hint via `FUN_0062732a`.
  Payment path: TERRAPAY pane shown at **`0x4d55a8`** (`push 0x68c44c` → `FUN_005f0583`),
  debit **`0x4d561a`** (`mov %edx,(%eax)`, eax = `0x94d650 + player*0x82f*4`), refund at
  `0x4d5908`/`0x4d59f3`. Harness: `scripts/m33_order.gdb` (7 bps: KEY/DISP/TERRAF/
  TERRAPAY/DEBIT/STORE/BCAST) + `scripts/m33_run.sh` (pre-state → poke → arm → driver
  `--order` → kill gdb → CONT → post-state).
* **The setter runs synchronously inside the key handler** and *blocks on the payment
  picker* (`Want_to_terraform` → `FUN_005a6330` picker; `TERRACOST` message; `TERRAPAY`
  itemlist "Cancel action. / Expend $NUM0 credits.") — the order byte only lands after
  the player answers. Farm/Road/Sensor apparently **defer payment to execution** (no pane
  fired; `energy 40` unchanged). Advisor rejections (`That square already has a road...`)
  appear as transient panes and abort before the store.
* **Tile record layout pinned** (asm at `0x4d5b25`: `imul` stride, ×11 dwords): tile addr
  = `DAT_0092ae14 + (40*y + x>>1)*0x2c` (`DAT_00692184` = 40 read live; map 80×80 at
  `0x92a378/0x92a37c`); `+0` byte: height = `>>5` (elevation m ≈ h*~100), `+8` dword =
  improvement/eligibility mask read by every gate (`pbVar1[8]&1` base, `&0x10` road,
  `&0x20` farm, `&0x8000` fungus, `&0x1000000` neighbor-borehole). The `+4/+8` values look
  pointer-like (0x020ff…) — **semantics of the mask dword still open** (no executed
  improvement observed yet, see open items).
* **Unit class = low byte of the dword at `0x98adb2 + type*52`** (live: type 1 →
  `0xff002909` class 9 = Former; matches alpha.txt `#UNITS` field 5). Runtime type ids ≥ 64
  are per-faction built variants that **preserve the class byte** (type 194 →
  `0x9000202` class 2). Reader: `scripts/m33_scan.py` (unit array + class + energy + tiles).

### M33 pitfalls (paid for the second time — retracts/qualifies earlier notes)

* **`/proc/<pid>/mem` pokes are UNRELIABLE while a tracer (gdb) is attached.** Readbacks
  lie (poke reads back the new value, the game never sees it, or a later attach reverts
  it: observed poke 55 → readback 55 → post-attach value 58). Rule: **poke only with
  TracerPid 0; arm gdb AFTER the poke; verify state after `kill -CONT`.** M25's poke
  results stand (no tracer); M33's first three runs were ghosts.
* **Selection is game-owned.** `0x91b5bc`/`0x91b5c4` revert to the cycle's choice within
  ~1 pump iteration when the poked unit fails revalidation (already-moved units, units
  with certain orders). The keypress itself also advances the selection cycle (after
  `h`/`r` the selection rolled to the next unit). **A poke is a race, not a control**:
  press the key IMMEDIATELY after the poke (no sleep) — that is the only configuration
  where the order landed on the poked unit. The clean paths are the game's own select
  routine `FUN_0040c8d0(idx,...)` (owner + `FUN_005acab0` can-act gates; called from the
  click handlers `FUN_00499e70`/`FUN_0049af50` "Reports left/right_click garrison") and
  the PICKUNIT/UNITCLICK pickers.
* **Advisor panes are transient modals** (auto-dismiss in ~1–2 s, faster than one OCR
  poll) and while up they **swallow the next input event**, which echoes as menu code
  `0x20011` through `FUN_00512b40`. A rejected order therefore looks exactly like a
  dropped keypress (zero `KEY` hits for the pressed key). gdb attach can also drop X
  events — re-press after attach.
* **Pixel↔tile mapping is not the naive lattice**: observed clicks at (438,183) and
  (486,255) both read tile (43,11) info; camera offset unknown. The HUD tile-info panel
  OCRs the cursor tile `(x,y)` and `Elev:` — calibrate via clicks + panel readout, not
  formula. (M27's "48×36 px lattice" is the *tile pitch*, not the screen mapping.)

### Open (M34 candidates)

1. **Execution trigger**: the Farm order (byte 4) persisted but never executed across two
   turns — the cycle never selected the Former (already-moved / order-4 units are skipped
   by the cycle), and Space (`FUN_004d1e90` → `SOLOWRAP idx=<cycle unit> dir=-1`) always
   ran the *cycle's* unit instead. Next: give the order to a Former the cycle actually
   selects (fresh turn, mp full, or native click-select via PICKUNIT), then observe the
   tile `+8` mask change + energy debit (the improvement half of C2's "effect").
2. Improvement-mask dword semantics (why `+8` at (43,11) = `0x00050105` while (45,11) =
   `0x020ffaf3` — the high bytes smell like a packed pointer, not flags).
3. Picker servicing: UNITCLICK "Activate $UNITTYPE3" row → native select; calibrate map
   click coordinates via the tile-info panel.

## §M34 (session 34, 2026-10-21): the execution trigger hunt — orders cancel at end-of-turn

Goal: watch the stored Farm order EXECUTE (tile `+8` improvement + energy debit). Result:
**no execution observed; the order instead CLEARS at end-of-turn with no debit and no tile
change.** Two solid static findings + a set of live negatives explain why every attempt died,
and one old claim about tile (45,11)'s mask semantics is retracted.

### Static (ghidra_out, high confidence — code read, not guessed)

* **The setter `FUN_004d44d0(unit, mode)` eligibility remap explains the (45,11) rejections.**
  For Farm (mode 0), shard_012.c:108-113: `if ((tile+8 & 0x20) == 0 || terrain < 4)` → fungus
  fallback (`mode = 1` when `+8 & 0x8000`); **`else mode = 0xa`** (a special farm variant). Then
  line 182: `if (improvement_capable(terrain, mode) && (mode != 0xa || unit_ability & 0x2000))`
  — a plain Former (type 1, ability dword at `0x98ada8[type*52]` = `0xff002909`) **lacks ability
  0x2000**, so mode-0xa falls into the picker branch `FUN_005a7520` and aborts with the
  HASFARM advisor (`s_HASFARM_0068c308`) **before the store** (0x4d5bbf). Live signature
  matches exactly: `m34_try2_gdb.log` = 5× `KEY 0x66 → TERRAF idx=46 mode=0`, zero
  STORE/BCAST/DEBIT, `0x20011` echo after each hit (the transient advisor pane).
* **Space IS the execute-order key** (untraced before): `FUN_00512450` (the order-command
  dispatcher) `switch(param_2) case 0x20: FUN_004d1e90(selected)` (shard_013.c:4451);
  `FUN_004d1e90(u)` = `if (can-act(u) && sim-mode()==0) FUN_00529090(u, -1, 0)` → solo
  `FUN_00585720(u, dir -1→0x8 sentinel, 3)` = "run your stored order" (dir<0→8 at
  shard_015.c:~120). Second caller: `FUN_00516b80` menu id 0x323. The broadcast path
  `FUN_00584350 → FUN_0052a720(queue, idx, 0,0,0, 1, 0x2101)` (shard_014.c:28982+) shows
  order-set broadcasts are **enqueued**, then drained by `FUN_005262e0` → dispatcher
  `FUN_0052bce0`.
* Selection-cycle internals: pump `FUN_0050cab0` revalidates `0x91b5bc` via
  `FUN_005acab0` (idle = on-map ∧ own ∧ not-busy ∧ `FUN_005accd0==0`; **no order-byte test**)
  and re-picks via `FUN_0050c550`; `FUN_0040c8d0` (native select) gates on the same idle check
  plus `+9` frozen. The candidate list `auStack_534` (count `FUN_005dacb1()`, entries
  `list[i*5]`, `switch` case 1/2 → select) feeds both `FUN_0040c8d0` and the picker inside the
  terraform setter (`FUN_005a7520`) — the picker IS the candidate list, untraced semantics open.

### Live (evidence/m34_*; pid 914079, years 2254→2266)

1. **`/proc/<pid>/mem` writes are DEAD, not ghostly, while a tracer is attached** (try3:
   `m34_try3_gdb.log` — poked `0x91b5bc=46`, `TERRAF idx=50` hit on the cycle's unit; poke
   readback said 46). Corollary: with gdb armed you cannot steer selection at all.
2. **Selection is 100 % game-owned and inert between actions**: idle pump and every key we
   pressed (Return/plus/Tab/arrows while no unit actionable) never moved `0x91b5bc` (try4: 30 s
   wait, zero NATIVESEL hits; v7_run2: 40 s, sel=-1). The cycle advances only when the selected
   unit *completes an action* — two `h` HOLDs walked it 50→233→**46** (`m34v6_run1_watch.json`),
   the only observed selection arrival on our Former.
3. **Order issue via the game's own selection works**: at sel=46, `f` → `TERRAF idx=46` →
   order byte 4 landed (v6: read 0 at +0.8 s, 4 at next turn boundary — the setter completed
   after our poll; the picker/pane blocked it inside the setter, M33 mechanism).
4. **End-of-turn CANCELS the pending order without executing it**: v6 turns — order 4 persisted
   through 2261, cleared 4→0 at the 2262 turn boundary; **energy 40→40, tile `+8` unchanged**.
   (Former mp was 3/6 remaining — the can-act gate would have passed; the cancel is not an
   mp-gated refusal. Cancel write-site not yet pinned.)
5. **Space never executed the ordered Former**: after the order landed, Space produced no
   `SPACEH`/`SOLOWRAP` (try2/try3 logs; v6 sel had already rolled). With panes up the router
   swallows events (`0x20011` echo) — the clean window needed for the Space chain was never hit.
6. **RETRACTION (M33 tile-mask semantics at (45,11))**: the (45,7) tile record read **all zeros**
   in `m34_try2_pre` (no tracer) yet showed `+8=0x020ffaf3`-era content in `m33_final_pre` for
   the same address, and flipped back to zeros after the traced v7 runs. The `0x20ff…` "mask"
   content is not stable tile state — treat the M33 `+8` bit-reading (`&0x20` farm-eligible etc.)
   as **unverified** until re-derived from a settled no-tracer snapshot. (The setter's own math
   `tile = 0x92ae14 + (40*y + x>>1)*0x2c` stands — it is asm-pinned; the *content* reading moved.)

### Net

C2's "issue" half stands (M33). The "improvement appears on the tile" half is **not yet
observed**: orders land, persist within a turn, and are cancelled at end-of-turn. The execution
trigger (Space on the selected ordered unit, or the picker answering inside the setter) is
statically pinned but never caught live because (a) selection can't be steered under a tracer,
(b) the cycle won't re-select a unit once it has acted, and (c) panes swallow the follow-up key.

Harnesses added: `scripts/m34_exec.gdb` (10 bps) + `scripts/m34_run.sh` (poke→arm→race),
`scripts/m34_chain.gdb` (12 bps, store→bcast→enqueue→drain→dispatch→executor) +
`scripts/m34_chase.sh` (wait-game-select variant), `scripts/m34_exec_watch.py`,
`scripts/m34_cycle_issue.py` (HOLD-walk the cycle; the one that landed the order).
**gdb pitfall (new):** breakpoint *conditions* must cast — `if $esp[1] == N` throws
"Attempt to dereference a generic pointer" at first hit and **kills the whole batch script**
(try1, v7_run1 both died this way); use `if *(int *)($esp+4) == N`.

## §M35 (session 35, 2026-10-21): the PAY picker is caught — answering it debits, the order store is skipped

Goal (M34 option 1): catch the TERRAPAY picker answering **inside** `FUN_004d44d0` and see
whether STORE→BCAST→ENQ→DRAIN→DISP→EXEC fires synchronously. Result: **picker caught,
answered live (`PAYTAKEN`), the energy debit fires synchronously — and the order store is
then skipped.** Two static corrections came out of it, one of them big (tile array base).

### Static (asm-pinned this session; scr/pt notes)

* **The pay path is Raise/Lower-only.** Every xref to `LAB_004d5496` (payment entry) is
  inside `case 0x10/0x11` — `0x4d5277`, `0x4d5313`, `0x4d53d8`, `0x4d53f4`, `0x4d53f9`
  (objdump `terran.exe` 0x4d5244–0x4d5493). `case 0x10` (raise): level ≥ 3 → `0x4d530e`;
  `< 0xc0` (level < 6) → pay; level 3 → pay via `0x4d5274`; level 2 and 6/7 → advisor.
  `case 0x11` (lower): level ≥ 4 → pay, level 3 → TOOLOW, level 0 → SEATOOLOW + pay.
  Farm/Road/Sensor/Condenser never show a pane — **M33's "the setter blocks on a picker
  until answered" holds only for raise/lower**; the other modes defer payment (unchanged).
* **`FUN_005a7520(mode, domain, player)` is the TECH-UNLOCK test, not a picker** (M34
  mislabel). Required tech id = `*(int*)(0x6938e8 + (mode*8 + domain)*4)` (−1 = none,
  < −1 = mode impossible there); researched = bit `(player & 0x1f)` of byte
  `0x985c1c + tech_id` (asm 0x5a7523–0x5a7559 + 0x5a75xx bit test). Live decode of the
  runtime table matches alpha.txt exactly: mode 0→−1, 1→62 AdvEcoEng, 2/3/5/9/0x12→−1,
  4→−1(sea −2), 6→18 Monopole Magnets, 7→17 AdvMilAlg, 8→39 DocAir, 0xa→−1,
  0xb–0xf→60 EcoEng, **0x10/0x11→59 EnvEcon**, 0x13→−2. This save's player 3 has techs
  0–6, 32, 48 — **EnvEcon locked** (probe: `scripts/m35_gate.py`).
* **Own-base bypass** (same function, 0x5a755c+): for `0xb < mode < 0x13`, if
  `DAT_00985b44 >= 0` and `*(byte*)(0x95da14 + DAT_00985b44*0x130) == player`, the tech
  gate returns true — eco/geo terraforming is tech-free at your own base. We own **no
  base** (67 bases scanned, owners {1,2,4,5,6,7}; `DAT_00985b44` currently 2 = The Hive).
* **Payment path, instruction by instruction:** `0x4d54c3 call 0x5a6330(unit, 9, mode+4,
  −1, −1)` = "does the unit or its cargo chain already carry order byte mode+4" → nonzero
  **skips** payment (`0x4d54cd jne 0x4d5634`); `0x4d54df call 0x4cc7b0(unit, x, y)` = cost,
  0 → skip; `0x4d5572 call 0x5f0583` = **TERRACOST** caption pane; `0x4d558f cmp
  [0x94d650+player*0x82f], cost; jl 0x4d55cb` — **cannot afford ⇒ the picker is never
  shown**, straight to `0x4d55d5`; `0x4d55b3 call 0x5f0583` = **TERRAPAY picker (blocks)**;
  `0x4d55d5 call 0x5f1394` = read the answer (`je 0x4d5689` = declined);
  `0x4d561a mov %edx,(%eax)` = energy −= cost; `0x4d5623 call 0x5843b0` = energy
  broadcast; `0x4d562f call 0x50fc20`; `0x4d5634` = common continuation (NOT a "skip"
  label — the M35 bp name `SKIPPAY` is misleading); then the footprint pass.
* **CORRECTION — the tile array base is a POINTER.** `0x92ae14` holds a heap pointer to the
  tile array (`0x4d5650 mov esi,[ds:0x92ae14]`, `0x4d5260 mov ecx,[0x92ae14]`); live value
  `0x40a5cd0`. M33/M34 computed `0x92ae14 + (40*y + x>>1)*0x2c`, i.e. indexed off the
  *pointer slot region*, which is why "tile content was unstable across snapshots". With
  the pointer: (45,7) `+0=0x80` elev 4, `+8=0x00108002`; (45,11) `+0=0x80`; (41,5)
  `+0=0x60` elev 3 — and 6/6 of our units read as land, which is the sanity control.
  Layout: 40 records/row × 44 B for an 80-wide map = **2 tiles per record** (x>>1); the
  second tile's block sits at +0x16. Whether the setter ever reads the second half is
  **open** (the head reads +0 only).
* **`FUN_005ab320(unit,x,y)` is unit reposition, not a tile writer** (writes unit +0/+2,
  calls `0x582ed0`/`0x582c80`) — retracts the "sole tile writer" label in the standing
  facts.

### Live (evidence/m35v1_*, m35v2_*; pid 914079, year 2266→2270)

Setup that finally worked (all game-owned): turn start auto-selects the first cycle
candidate; a **map click also selects a unit and turns orders-mode on** (`0x91b5b8` 0→1);
HOLDed units (order 2) are **not** cycle candidates, so once every unit is order-2 the
cycle is empty and the game **auto-ends the turn** (year ran 2266→2270 by itself).
`Tab` re-opens the CUSTOMIZE YOUR FACTION modal mid-game — avoid it (CANCEL at 547,289).

1. **v1 (negative control with a pitfall):** picker reached, but the driver sent `Escape`
   at the transient TERRACOST caption pane; it landed on the already-open **TERRAPAY**
   picker → `PAYDECLINED`, energy 40→40, order still 0. The caption pane self-closes in
   ~1–2 s — never press a key at it (M35 pitfall), and `PAYDECLINED` is the signature of
   a cancelled picker, not of a refused order.
2. **v2 (the catch):** after publishing tech bit 59 (one byte, `/proc/pid/mem`, no tracer,
   read back `0x10→0x18`) and arming 25 bps:
   `TERRAF idx=41 mode=0x10` → `TECHCHK unlocked=1` → `PAYPATH` → `ORDERCHK
   already_this_order=0` → **`COST idx=41 cost=9`** (runtime cost, not alpha's 12) →
   `TERRACOSTPANE OPEN`/`PANE #1 id=TERRACOSTUP` (text OCR'd: "It will cost 9 credits to
   raise this area; our current reserves are **49** credits" — the pool reads 40, an
   unresolved 9-credit display discrepancy) → `PAYPANE OPEN`/`PANE #2 id=TERRAPAY` →
   clicked the "Expend 9 credits." row at (265,197) + row+26 → `PAYDECIDE` →
   **`PAYTAKEN`** → **`DEBIT new_energy=31`** (40 − 9, synchronous) → **`ENQ q=11 idx=3
   type=0x2101`** (the energy broadcast is **queued**, idx = player) → `SKIPPAY` (0x4d5634)
   → `PANE #3 id=TERRAFORM` → **no `STORE` (0x4d5bbf), no `BCAST` (0x4d5bc6)**.
3. **Post-state:** energy **31 (not refunded)**, order byte **0**, tile unchanged
   (elev 4, mask `0x108002`), unit still selected, same year. So the picker's answer
   commits the debit but the order is never stored — the setter leaves through one of the
   footprint-pass exits before `0x4d5b0d`. `0x528930` is netplay-only (`if
   DAT_00920434==0 return 0`, solo switch live = 0) and `DAT_0091f718` = 0, so the
   rejecter is one of `0x4d5839 call 0x555030 → jne 0x4d59c7` / `0x4d58a4 call 0x4c2be0 →
   je 0x4d5b0d` / the `0x4d58dc` path — **not yet named** (M36 item).

### Net

The "issue" half of a raise-land order is now fully drivable and **paid**: picker shown,
answer read, debit synchronous, energy broadcast queued. The **store** half is gated by a
footprint check that runs *after* the money is taken and, when it refuses, leaves the
debit in place (no refund bp fired). Next milestone is to name that refuser — then pick a
tile whose footprint it accepts and catch `STORE → BCAST → ENQ(unit) → DRAIN → DISP →
EXEC` for real.

Harness: `scripts/m35_pay.gdb` (25 bps: setter gates, pane shows, answer, debit, store,
bcast, enqueue/drain/dispatch, executor, plus generic `PANE`/`ADVISOR` id logging),
`scripts/m35_paypicker.py` (preflight → tech poke → arm → key → pane servicing → post-state
→ evidence JSON), `scripts/m35_gate.py` (live read of the tech-unlock table and per-mode
bits). Evidence: `evidence/m35v2_paypicker.json`, `m35v2_gdb.log`, `m35v2_paypane0.png`,
`m35v1_paypicker.json`.

---

## §M36 (session 36, 2026-10-21): there was no refuser — the STORE gate is a pass-through in solo, and the order is stored; execution is the new wall

Goal (M35 option 1): name the post-payment footprint refuser and get the order stored.
**Result: the "refuser" was not a refuser.** M35's missing `STORE` was the one-time
TERRAFORM *tutor* pane blocking inside the setter: the harness killed gdb while the pane
was still open, so the setter never resumed. Dismissing it (OK at (400,408)) ran the tail
end-to-end and the order was stored live. The new wall is **execution**: three turn rounds
later the order byte is still `0x14` and the executor is never called for unit 41.

### Static (objdump-pinned 0x4d5634–0x4d5c1c + strings + decompile)

* **Footprint pass geometry.** Raise (`case 0x10`): count = `ladder[height+1]` from
  `0x678e08` = `[-13,-14,-15,1,9,25,49,81]` (clamped at 6) ⇒ **height 4 ⇒ 25 tiles (5×5)**;
  `height+1 ≤ 3` ⇒ 1 tile. Lower (`case 0x11`): fold on `height−1` picking from `0x678e18`
  = `[9,25,49,81,121,169,225,289]`. Offsets from tables `0x67850c` (x) / `0x678990` (y);
  x **wraps horizontally** (ocean wrap, `test cl,1` parity adjust against `DAT_0x92a378`
  = width), out-of-map tiles are **skipped, not refused**.
* **Per-tile ownership/diplomacy rules** (loop 0x4d5763–0x4d5899): `call 0x4e3b50(own, x, y, 0, 0)`
  returns the tile's **border owner**; `−1` or own ⇒ continue. Foreign owner with
  `[0x94d448 + (own*0x82f + owner)*4] & 7 == 0` ⇒ continue (nothing to break). Otherwise:
  netplay `0x528930(unit,2,-1,-1,0)` (solo returns 0), then **`0x555030(own, owner, 7)`**:
  bit 0 (pact) ⇒ shows `s_BREAKINGPACT` pane and **returns true = refuse, no dialog**;
  bit 1 (treaty) / bit 2 (truce) ⇒ yes/no confirm (`BREAKINGTREATY`/`BREAKINGTRUCE`), decline
  = refuse; else `BEGINVENDETTA` confirm. A refuse jumps to `0x4d58dc`/`0x4d59c7`, which
  **refund the cost** (`[0x94d650] += [ebp-0x14]`, energy broadcast, return via 0x4d5add).
  Accepting in solo calls `0x5076d0(own, owner, -1)` (break the diplomacy) and continues.
* **`0x4c2be0(0x800)` at 0x4d58a4 is not a gate — it is the once-per-game tutor latch**:
  solo-only, sets bit `0x800` of `DAT_00985ad4` and returns 1 the first time; the fall-through
  shows the **`'TERRAFORM'` tutor pane** (`tutor.txt:1102`, shown via `call 0x48ef40` at
  0x4d58c6 — a *blocking* pane call: `0x57b570` suspend → `0x62680e` pane runner →
  `0x57b0f0` resume), then `jmp 0x4d5b16`. Both latch outcomes converge at `0x4d5b16`.
* **The store tail (0x4d5b16–0x4d5c1c):** mode ∈ {0xa, 0x10, 0x11} skips the terrain/facility
  mask gate at 0x4d5b16–0x4d5b6f (other modes: record byte0 `& ~0x1f ≥ 0x40` ∧ tile mask ∧
  `*(0x6938f4 + [ebp-0x18]*4)` scanned against table `0x6938f0..0x693b70` → `0x4d5e85`).
  Then `0x4d5b71`: **issue lock** — `[0x91f718] != 0` logs `"I think I've already got my lock"`
  (0x68c4bc) and **skips** the lock call; else `0x528930(unit, 0, -1, -1, 0)` with `ecx=0x91db70`
  — the *solo* behavior is `DAT_00920434 == 0 ⇒ return 0`, i.e. **the store gate is a
  pass-through in solo**; nonzero (netplay) jumps `0x4d5bae → 0x4d5c1c` past the store.
  `0x4d5bb0 STORE: [unit*52 + 0x933289] = mode+4` (order byte +17), `0x4d5bc6 BCAST:
  call 0x584350` → enqueue 0x2101 idx=unit; debug strings `"Issuing Vehicle Orders"` (0x68c4e0) /
  `"Finished issuing orders"` (0x68c4f8) bracket the tail; `[singleton+0x23be4] = 0`.
* **`FUN_00582ed0(x, y, mask, setclr)` = tile mask set/clear** at `record+8` (pointer base,
  `x>>1` — confirms the M35 tile-base correction); 78 callers.

### Live (evidence/m36_*; pid 914079, years 2270→2273)

1. **The parked setter.** At session start the TERRAFORM encyclopedia pane ("Events which
   cause mountains to be raised or torn down…", OK bar (400,408)) was **still open from
   m35v2**, latch bit `0x800` consumed, order byte 0 — the setter parked inside `0x48ef40`
   above `STORE`. M35's "no STORE, no refund, no visible failure pane" is fully explained:
   the harness killed gdb while the pane was open; the game froze mid-setter for the whole
   interval. **There is no post-payment refuser for this tile.**
2. **The store tail, caught live** (`m36v1_gdb.log`, 18 bps): click OK →
   `PANERET 0x4d58cb` → `AFTERLATCH 0x4d5b16 mode=0x10` → `LOCKCHK lock=0` →
   `LOCKRET eax=0` → **`STORE order=0x14`** → **`BCAST`** → **`ENQ q=17 idx=41 type=0x2101`**.
   No `DEBIT` (energy stays 31 — no double-charge), no `EPILOGUE`/unwind. Post: order byte
   **20 (0x14)** at +17, tile (45,7) unchanged (elev 4, mask `0x108002`).
3. **The queue never drains in solo.** Across two more full rounds with bps armed,
   `DRAIN (0x5262e0)` and `DISP (0x52bce0, 0x2101)` **never fire** — neither the energy
   broadcast (idx=player) nor the unit broadcast (idx=41) is ever dequeued. Consistent with
   M7/M8 (solo never drives the netcode dispatcher); the 0x2101 queue is a no-op in solo.
4. **Execution skips unit 41.** Probe round 2272→2273 (unconditional bps on
   `0x529090`/`0x585720`/`0x4d1e90`): executor `0x585720(arg1=unit idx, arg2=dir, arg3=3)`
   fired **183 times for other units, zero times for 41** (`evidence/m36_execprobe_gdb.log`)
   — so the bp shape is right and the turn machinery *filters the unit out*. Prime suspect:
   can-act gate `0x5acc00` (`mp total − +40 > 0`) with **mpused = 3 persisting across turn
   boundaries** (it went 0→3 during the 2270 execution phase — the one unobserved window —
   while the tile stayed at elev 4 and the order survived; type 1 unit, panel said "Move: 1").
5. **ENDOFTURN1** (`Script.txt:8037`) = "Mission Year $NUM0: No units need new orders.
   Press ENTER for next turn." — the auto-end pane; `Return` advances it (not a Yes/No confirm).
   **Escape on a bare HUD opens REALLYQUIT** ("Do you really want to quit?", rows "Oops, no,
   wait!" y≈260 / "Yes, that's an order mister!" y≈281, OK bar ≈307) — hit live by the svc
   loop, recovered by clicking NO + OK.

### Net

The terraform order **issue→pay→store→enqueue** chain is now complete end-to-end in solo,
with every gate named and the one-time tutor pane identified as the thing that ate M35.
What remains is the **execution** half: why the turn machinery filters unit 41 (mp semantics
of +40 after a stored terraform), whether the 0x2101 queue has any consumer in solo, and
whether `Space` on the selected unit still executes it (`SPACEH 0x4d1e90` never had a chance
to fire — no Space was pressed with 41 selected).

Harness: `scripts/m36_store.gdb` (18 bps: pane-return, latch merge, lock check/ret, STORE,
BCAST, epilogue + M35's chain bps) + `scripts/m36_dismiss.py` (preflight → arm → OK click →
store-tail poll → optional Space → evidence JSON); `scripts/m36_exec.gdb` (14 bps incl.
SETMASK on the target tile + re-entry/payment guards) + `scripts/m36_exec.py` (turn-end +
modal servicing); `scratch/m36_probe_exec.gdb` (unconditional executor probe). Evidence:
`m36v1_gdb.log`, `m36v1_dismiss.json`, `m36b_gdb.log`, `m36b_exec.json`,
`m36_execprobe_gdb.log`, `m36_screen0.png` (the parked pane), `m36_after_no.png`.

## §M37 (sessions 37a–c, 2026-10-21): the execution wall falls — terraform is a multi-turn accumulator at `unit+37`; the stored raise completes live (elev 4→5, year 2281)

Goal (M36 option 1): why does the turn machinery "skip" unit 41? **It never skipped it — the
M36 probe was at the wrong door.** `0x585720` is the MOVE executor; terraform-range orders
(4..0x17) execute through an entirely different chain, the action is **multi-turn**, and the
per-turn consume-all made the unit look frozen between turns.

### The execution chain (static + live)

* **Turn-start refresh `FUN_0051f730(player)`** fires **per player per round in solo** (live
  `REFRESH player=N` in every m37 log). Per unit of that player: `watchdog+42 = 0`,
  **`mpused+40 = 0`**, `flags4 &= 0xfbffdffd`, `byte+5 &= 0xef`; Sentry/Hold countdown at
  `+28` decremented, order cleared at 0. Then for units with `byte+16 ≠ 0` it decrements
  `byte+16` by `field45(type)*local_8` with floor `field45*2` (0 when standing on own/
  allied base or for player 0; `local_8` grows with near-base/near-facility conditions).
  Sole caller `FUN_005208f0` (per-player turn-start sequence: `0x5a1830 → 0x51f730 →
  0x520540 → upkeep`), itself called from the round sequencers `FUN_00520c10`/`FUN_00521070`
  — which also drive the solo turn engine `FUN_0051e700`, so this is **not** netplay-only.
* **Our-turn pump `FUN_0050ef60`** (the M29/M30 solo turn driver): gates the tracked unit with
  `FUN_005acc00(unit)` (actionable ⇔ `FUN_005ac650(unit,0) > mpused`; sub-gate `FUN_005accd0`
  only constrains Sentry-with-target, order 1); actionable ∧ order ≠ 0 → `FUN_00529e70(unit,0)`.
* **`FUN_00529e70(unit, flag)` = attempt-unit-action**: solo (`DAT_00920434 == 0`) →
  `return FUN_004d1200(unit)`; netplay → ACTION packet `0x2404` + lock `0x528a60`.
* **`FUN_004d1200(unit)` = solo order dispatcher**: order 4..0x17 → `FUN_004cce50(unit, order−4, 1)`;
  0x18/0x19/0x1a → `FUN_004ce4a0`; 0x1b/0x1c → `FUN_004ce710`; post-run `order & 0x40 ⇒ order = 0`.
* **`FUN_004cce50(unit, k, execute)` = the named-order engine** (M26's `set_named_order` label
  was the `execute = 0` branch: stores `+17 = k+4` and returns an ETA in turns). Execute branch:
  1. `FUN_005acdb0(unit)` — **consume-all**: `mpused := FUN_005ac650(unit,0)` (34 B, one store).
     This is what M36 read as "mpused 3 persists across turn boundaries": REFRESH zeroes it at
     turn start, the pump re-consumes it during our turn; snapshots taken during/after our turn
     always show 3, and the unit panel prints `ALREADY MOVED`.
  2. **Work accumulator `unit+37`** (`DAT_0093329d`): `accum += Σ work` over the tile's unit
     chain (walk `prev@+50` to head, then `next@+48`), same-k members only; per member
     work = **2**, or **4** if ability mask `0x98ada8[type*52] & 1`; ×2 for k∈{10,0xb} when the
     faction owns base `DAT_00985b5c`, ×3/2 when it owns `DAT_00985b44`. On execute, chained
     members' `+37` fold into the head and are zeroed.
  3. **Threshold**: `iVar16 = terrain_table[k].+8` (runtime table at **`0x6938f0 + k*32`**,
     filled from alpha.txt at load — `+8` **== `#TERRAIN` field 5**: raise/lower 12, mine 8,
     sensor 4, mag tube 3, road 1; `+18` == required tech id, 59 = EnvEcon for raise/lower —
     matches M35), adjusted per mode (case 3: `×elev_class/2`; cases 5/6: base swapped to the
     ocean variant if `mask&4`, `+1` swamp (`mask&0x80`), `+2` fungal (`mask&0x20` ∧ elev>3),
     `+ elev_class×base/2`; case 10: `/2` if ability `&0x2000`; difficulty: `−1` if
     `DAT_00985aec > 3` ∧ player ∉ `DAT_00985b10`). **Completion threshold = `2×iVar16`**
     (live: raise 24, mine 16, sensor 8).
  4. **NOTYET** (`accum_new < 2×iVar16`, bp `0x4cd33b`): tile dirty `0x4737e0(x,y,2)`, base
     panel refresh `0x41b710(unit)`, order stays, return 0.
  5. Swamp-cancel (bp `0x4cd319`): tile became passable-land (`tile[8]&1` ∧ elev<8) ⇒ order = 0.
  6. **COMPLETE** (`accum_new ≥ 2×iVar16`, bp `0x4cd35e`): `accum := 0`; chain walk clears
     every same-k order (`+17 = 0`); tile mask swap via `0x582ed0`: **clear `table[k].+4` bits,
     set `table[k].+0` bits**; owner update `0x582fc0`; per mode: k=0x10 → **`FUN_005ad400(x,y)`
     RAISE**, k=0x11 → `FUN_005ad460(x,y)` LOWER, k∈{0xc,0xe} → `0x583570` + `0x5b09b0` +
     `0x4738f0(1)`, k=0xf → mask `0x100` set + …, k=0x12 → mine demote; then `0x5b09b0()`
     (re-erosion/recalc — the SETELEV storm on neighbours) + `0x4738f0(1)` redraw; if
     `table[k].+0 & 0x1208050` ⇒ base `+0x30 |= 0x100` (facility re-eval); `BOREHOLEMINE`
     advisory for k=0xe over own base. Elevation setter: `0x5ad400/0x5ad460 → 0x5ad0a0(x,y,new,flag)`.
  * Road/mag-tube (k=5/6) are not in the switch — completion is just the mask swap; live proof:
    AI `COMPLETE … mode=5` at (10,14) followed by `MASKSET mask=0x4 setclr=1` = `table[5].+0` ✓.

### Live runs (all under `scripts/m37_exec41.gdb`, 11 bps: REFRESH/ORDEREXEC/TERRAFEXEC/CHECK/
NOTYET/CANCEL/COMPLETE/RAISE/LOWER/SETELEV/MASKSET; runner `scripts/m37_exec41.py`)

* **m37a** (22:21, 2273→2274): unit 41 `mode=16 accum 8→10 threshold=24 NOTYET`; runner snaps
  `+37` + tile each round (`evidence/m37a_exec41.json`).
* **m37b** (22:23–22:27): full round of AI terraforms, two COMPLETEs (unit 32 mode 5 12≥6 at
  (67,71); unit 3 mode 5 4≥4 at (34,68)); unit 41 10→12. Session died before checkpointing;
  its svc-loop double-`unknown` Escape opened **REALLYQUIT**, which `answer_confirm` cannot
  handle (`find_yes_row` scans y 160–220; REALLYQUIT rows are 260/281 → default 196 = artwork).
* **This session**: `scripts/m37_recover.py` closed REALLYQUIT (NO row OCR'd at (173,261), OK
  at +47 — M36 geometry re-verified). Runner patched: reallyquit special-case in preflight +
  svc, Escape only when `region_colors((180,60,620,200)) < 130` (pane over map), ENDOFTURN1 →
  Return, and **bare-HUD-on-our-turn stall → TURN COMPLETE click** (m37c stalled at 2276 because
  only the first turn-end was clicked; every subsequent round needs its own end-turn).
* **m37c2** (2276→2281): accum 14→16→18→20→22→**24**, exactly **+2 per our turn** (mid-AI
  snapshots repeat the value — the work lands on our turn); the unit slid 40→39 under compaction,
  tracked by order+ownership. Final: `CHECK accum_new=24 threshold=24 → COMPLETE unit=2028 x=45
  y=7 mode=16 → RAISE x=45 y=7 → SETELEV x=45 y=7 new=5` (+ neighbour re-erosion). Post: order 0,
  work37 0, **tile (45,7) elev 5**, energy 31 unchanged, year 2281. Total 12 turns (2270..2281)
  × 2 work = 24 = 2×12 = 2×`#TERRAIN[16].time` ✓.

### Corrections to M36

* "Executor `0x585720` fired 183×/round, **zero for unit 41** ⇒ machinery filters the ordered
  unit" — **recontexturized**: `0x585720` is the move executor; terraform executes via
  `0x4d1200`/`0x4cce50` and fired for unit 41 every round (m37a/b/c2 logs).
* "mpused = 3 persists across turn boundaries" — **refuted as a persistence**: REFRESH runs per
  player per round in solo; the 3 is re-charged by consume-all each turn.
* "`DRAIN`/`DISP` never fire in solo" — holds, and is now explained: the `0x2101` queue is the
  netplay replication path; solo executes directly from the pump. The M7/M8 "no netcode in solo"
  picture is intact.
* `0x4dde00` (unit info panel) **writes spinner values back** into `+15/+16/+40/+37` on its
  confirm path — a poke target to be careful around (M).

### Files

`scripts/m37_exec41.gdb` (moved from scratch/, durable), `scripts/m37_exec41.py` (patched
multi-round runner), `scripts/m37_recover.py`. Evidence: `m37a_*`, `m37b_*`, `m37c_*`,
`m37c2_*` (completion: 6237 events, post elev 5), `m37_recovered.png`, `m37_screen0.png`.

## §M38 (session 38, 2026-10-21): the driver issues a second raise end-to-end — cost formula decoded live; elevation 6 at year 2293; diplomacy branch armed but clean

* **Issue chain, driver-side, first try** (`scripts/m38_issue.py` + `scripts/m38_issue.gdb`,
  34 bps = m35_pay chain + m36_store tail + new footprint/diplomacy sites): ENDOFTURN1 →
  Return (2281→2282) → **selection recipe**: cycle landed on another unit, so poke
  `+40(mpused)=255` into every other own order-0 unit (TracerPid 0), `Escape` to deselect,
  the pump re-selects the only actionable unit = the Former → `]` → `TERRAF mode=0x10 →
  TECHCHK unlocked=1 → PAYPATH → ORDERCHK already_this_order=0 → **COST 16** (was 9 at
  elev 4) → TERRACOSTUP caption → TERRAPAY picker → click `Expend` row (265,197) + OK →
  `PAYTAKEN` → **`DEBIT 31→15`** (synchronous) → footprint pass → **zero PACTCHK/DIPLO/
  REFUND hits** → tutor latch consumed (predicted): `PANERET` silent, `AFTERLATCH` fired
  directly → `LOCKCHK lock=0 → LOCKRET eax=0 → **STORE +17=0x14** → BCAST → ENQ q=17 idx=39`
  (+ the energy event `ENQ q=11 idx=3` at debit). `evidence/m38a_issue.json`/`m38a_issue_gdb.log`.
* **Diplomacy branch: armed but never fires here.** The elev-5 raise footprint is
  `0x678e08[5+1] = 49` tiles = **7×7** (x 42..48, y 3..11 — the 81-tile/9×9 step is the
  elev-6 one, ladder idx 7; NEXT_PROMPT's "81 at elev 5" was off by one rung). All 49 tiles
  own-or-unclaimed ⇒ the `0x555030` pact/treaty path and the refund blocks `0x4d58dc`/
  `0x4d59c7` stayed silent. Branch remains untested live (bigger footprint needs elev 6 ⇒
  9×9 — and 25 energy, see cost below).
* **Completion** (`m38run2`, same 11-bp runner): work37 4→6→…→22→**24**, +2 per our turn
  2282..2293 (the ISSUE turn executed too — after STORE the pump ran the order immediately:
  consume-all + work 2; a second execution landed in 2283 before the runner armed) →
  `CHECK accum_new=24 threshold=24 → COMPLETE unit=1872 (=idx 36×52) x=45 y=7 mode=16 →
  RAISE x=45 y=7 → **SETELEV x=45 y=7 new=6**`. Post (mem-verified): **tile (45,7) elev 6**,
  order 0, work37 0, energy 15, year 2293, TracerPid 0. 12 executions total (2282..2293),
  24 = 2×12 ✓ — second ladder-verified cycle. The re-erosion (`0x5b09b0`) **lifted the 8
  neighbours to elev 5** ((45,5),(44,6),(46,6),(43,7),(47,7),(44,8),…) — leveling erodes
  terrain *toward* the new plateau.
* **Issue-cost formula decoded (H — asm + both live points).** `FUN_004cc7b0(x, y, player)`
  (call site 0x4d54d3 pushes `[esi+0x23bd4]`=own player, y, x):
  `term = (|elev−3| + 2)²`; `×3` if fungal (`mask&0x20` ∧ elev>3); if a nearest own base is
  found (`FUN_004e3700(x,y,player)`, walks the `DAT_00985af4` bases at `0x95da10`×304,
  matching **byte base+4 == player**, wrapped |dx|+|dy| via `FUN_0064b870` abs + wrap
  correction, `DAT_00692184`=40 half-width, `DAT_0092a378`=80 width, `DAT_0092a394&1`=wrap
  flag): `cost = clamp((|dx|+|dy|)/2, 1, 100) × term × 2`, further scaled by the foreign
  tile-owner's base distance × (base+6 char+2)/3 ratio when at peace; final: `/2` if faction
  trait bit `*(uint*)(0x927a98 + player*0x59c) & 0x2000` (ours: clear), **always `/2`**,
  clamp 1..30000. **For player 3 the base-distance branch is inert**: the 69 live bases carry
  faction bytes {1,2,4,5,6,7} — never 3 (base+4 stores a FACTION ID, not the player index;
  the player↔faction-ID mapping is unresolved — M39 lead), so `0x4e3700(x,y,3) = −1` and
  cost = `term`: elev 4 → (1+2)² = **9 ✓**, elev 5 → (2+2)² = **16 ✓**. Prediction: the next
  raise/lower at elev 6 costs **(3+2)² = 25 > our 15 energy** — unpayable until income builds.
* **Economy observation:** energy is flat between debits — 31@2270 → 31@2282 → (−16) →
  15@2293: income ≈ unit upkeep, ≈ +0/turn (H observed, interpretation M). Measuring the
  rate properly feeds C3 and gates any further terraform (queued M39).
* **Harness notes:** picker `Expend` row click auto-confirms (the follow-up OK at the OCR'd
  `ok` word was harmless; `PAYTAKEN` raced gdb's block-buffered printf so the runner's
  live `wait_for` saw `[]` — the post-kill log is authoritative, M34 buffering pitfall).
  `m37_exec41.py` preflight relaxed: a selected unit panel makes `classify` return `unknown`
  with garbled strip OCR — on our turn that is a fine start state (svc loop ends the turn
  via TURN COMPLETE/TURN_BTN fallback; `svc_hud_clicks=5` this run).
* **Files:** `scripts/m38_issue.gdb` (34 bps), `scripts/m38_issue.py`; evidence
  `m38a_issue.{json,gdb.log}`, `m38a_{pre,terracost_pane,paypane0,after_row,post}.png`,
  `m38run2_{gdb.log,exec41.json,pre,post}.png` (3980 events, post elev 6).

## §M39 (session 39, 2026-10-21): second mode proven — Road issues with NO cost block, completes in 2 executions at elev 6; live threshold table from AI events; harness keys corrected

* **Issue (H, live, `scripts/m39_issue.py` + concatenated 45-bp gdb):** `r` on the selected
  Former at (45,7): `TERRAF idx=36 mode=0x5 → TECHCHK unlocked=1 →` **the whole cost block is
  skipped** — PAYPATH `0x4d5496`, ORDERCHK `0x4d54c8`, cost `0x4cc7b0`, TERRACOST/TERRAPAY,
  SKIPPAY `0x4d5634` all silent (road jumps over `0x4d5496..0x4d5634`; SKIPPAY is the
  already-has-order exit, not the no-pay path) `→ AFTERLATCH → LOCKCHK 0 → LOCKRET eax=0 →
  STORE +17=0x09 → BCAST → ENQ q=17`. No picker, no DEBIT — energy 15 before and after.
  `evidence/m39a_issue.json` / `m39a_gdb.log`.
* **Execution (H, live):** issue turn 2294: pump executes immediately (`ORDEREXEC unit=36
  order=0x9` — third same-turn-execution sighting): `TERRAFEXEC accum_old=0 → CHECK
  accum_new=2 threshold=4 → NOTYET`. Next turn 2295 (after `REFRESH player=3`): `CHECK
  accum_new=4 threshold=4 → COMPLETE unit=1872 x=45 y=7 mode=5`. Post mem-verified: tile
  (45,7) mask **0x00108002 → 0x00108006 (road bit 0x4 set; table `+4` clear-mask 0x0 ✓)**,
  elev 6 untouched — mode 5 COMPLETE = mask swap only, no RAISE/SETELEV (`0x582ed0` write
  proven by the mem change; its MASKSET print was swallowed by the log's 300-print cap),
  order 0, work37 0, energy 15, year 2295, TracerPid 0.
* **Thresholds caught live in the same log (AI + ours) — M37's adjustment formulas
  confirmed:** road (mode 5): threshold **4** at elev-6 tiles (45,7) and (39,49) vs **2** at
  (46,42) ⇒ case-5 adjustment raises base 1→2 by elevation class (int), then ×2. Solar
  (mode 3): 8 at (46,50)/(58,52), **16** at (40,46) — case 3 `×elev-class/2` ✓. Mine
  (mode 4): 8 at (54,36)/(43,57). RemoveFungus (mode 10): 12 at (58,50)/(44,46).
* **AI terraform work = +3 per execution** (units 12/20/51/101/110/129/143/151/166 across
  modes 3/4/5/10) vs **our +2** — cause open (ability bit0 would give 4, so it is not that;
  faction/difficulty modifier suspected, M). The AI road at (46,42) completed on its first
  execution (accum 3 ≥ 2).
* **Harness corrections (H, live — these rewrite the key model):**
  * **`l` is the SENTRY order key** with a unit selected in orders mode (it issued order 1 to
    our Former and the turn auto-ended once every unit had an order) — NOT a cycle key.
    **`Tab` is the cycle / select-next key** (live: sel −1→36, orders mode 0→1). The old
    "L cycles" note in `references/turn-machinery.md` is superseded.
  * **Mid-turn start:** a runner that ends with the turn open (info panel up, mostly-black
    explored map ⇒ `classify()` = `title`/`unknown`) must detect `cur == me` with no end-turn
    pane and go straight to selection — no Return, no pane-wait stall.
  * **A unit that used all its MP (mpused ≥ max) is skipped by the Tab cycle** — poke
    `+40=0` first (our Former's mpused=3 from M38's consume-all blocked selection until
    poked).
  * **`0x91b5c4` order-menu-pending can stick at 1** across turns and selections — poke 0
    before pressing order keys (worked: `r` landed first press after the poke).
  * Empty cycle ⇒ **ENDOFTURN1 pane** ⇒ Return. Order-byte poke (`+17: 1→0`) clears Sentry
    and the unit then accepts a key-issued order.
  * The gdb block-buffering race (M34) worked *for* us here: live polling never saw STORE
    until the buffer flushed during the AI turns, so cleanup ran after the full lifecycle —
    the log captured both executions, COMPLETE, and ~300 AI/fog MASKSET events.
* **Files:** `scripts/m39_issue.py` (m38_issue clone: Tab cycle, poke Former `+40=0`
  pre-cycle, pend-flag clear, picker optional, gdb = `m38_issue.gdb` + `m37_exec41.gdb`
  concatenated, 45 bps); `scripts/m37_exec41.py` gained `--order <hex>`; evidence
  `m39a_{issue.json,gdb.log,chain.gdb,pre.png,post.png,cyc*.png}`.

## §M40 (session 40, 2026-10-22): MagTube remap proven live + first TECHFAIL — the tech-gate advisory is MODE-SPECIFIC; the remap is capability-gated and rewrites the mode arg

* **Live (H, `scripts/m39_issue.py --tag m40a --key r` run as-is, 45/45 bps armed):** `r` on the
  Former at the roaded tile (45,7) (mask 0x108006, elev 6): `TERRAF idx=36 mode=0x5` (the key
  handler still passes 5) → `TECHCHK idx=36 mode=0x6 unlocked=0` → `TECHFAIL idx=36` (branch
  entry `0x4d486e`) → `ADVISOR #1 id=HASROAD` + `PANE #1 id=HASROAD`. **Rejected: no STORE, no
  cost block, no DEBIT** — post mem-verified: order 0, energy 15, tile 0x108006 unchanged, year
  2295, zero side effects. The TECHCHK bp reads `$ebp+0xc` and printed **0x6** ⇒ the rewrite
  writes back into the mode arg slot inside `0x4d44d0`. `evidence/m40a_{issue.json,gdb.log,chain.gdb,pre.png,post.png}`.
* **Remap condition (H, static `0x4d44d0` body shard_012.c + live table read):**
  `mode==5 && (tile.mask & 4) && cap[6 + seafloor] > -2 → mode := 6`, where `cap` = capability
  table `DAT_006938e8` (int entries, index `mode*8 + flag`), `flag = tile.elev < 3` — the
  **tile's** seafloor flag, not the unit's domain; `DAT_006939a8` = the MagTube pair, live
  `(18, −2)` ⇒ remap fires on land tiles only (sea MagTube undefined). Farm rewrites:
  `mask & 0x20 && elev ≥ 4 → 0xa` (RemoveFungus); else `mask & 0x8000 && cap[1+flag] > -2 → 1`
  (SoilEnricher).
* **TECHFAIL advisory dispatch (H, static + live):** fail branch (entry `0x4d486e`, taken when
  `0x5a7520(unit,mode)` returns 0 at bp `0x4d4837`): `mode==6 → s_HASROAD (0x68c300)`,
  `mode==1 → s_HASFARM (0x68c308)`, else `s_NOTUNTILTECH (0x68c310)` → printer `0x483470`.
  ORDERS.md's "NOTUNTILTECH via `0x5a7520`" is the **generic** branch; remap modes get their own
  message. Script.txt `#HASROAD` (caption "Operations Director"): "That square already has a
  road. Roads may not be converted to Magtubes until we discover $TECH0." — the game's own UX
  confirms the remap semantics. **Bypass:** the fail branch is skipped when `mode==0xa &&
  ability & 0x2000` (`0x98ada8[type*52]`) even with gate 0.
* **$TECH0 substitution, live-closed (H):** the fail branch loads the required tech id from the
  cap table (`cap[mode*8+flag]` = 18) → `0x5a69f0(&DAT_00997120, tech_id, 0)` formats the tech
  name from the tech record (`0x92fdb4 + id*44`, name at +0; tech 18 short name "Magnets") →
  `0x626634(slot=0, text)` sets the advisor substitution slot table (text buffers
  `DAT_0099a01c + slot*0x100`; slot values `DAT_00999ff4`/`DAT_00999fcc`). Post-run mem: slot-0
  buffer = **"Monopole Magnets"**; `DAT_00997120` holds the composed pane with the substitution
  applied: *"That square already has a road. Roads may not be converted to Magtubes until we
  discover Monopole Magnets."* (the buffer is reused by the pane printer after the name copy —
  these are scratch buffers, not state).
* **Tech-gate source correction (H):** the terrain-table `+18` "required tech" field is
  **garbage (527) for k ∈ {1, 5, 6}** (live read; only k=16/17 carry 59/EnvEcon) — the gate and
  the advisory both read the **capability table `0x6938e8`** (`mode*8 + tile-seafloor`): value
  ≥ 0 = required tech id, −1/−2 = operation undefined for that tile class (the same table drives
  the NOTATALL/NOTONLAND/NOTATSEA pre-checks).
* **Validator order inside `0x4d44d0(unit, mode)` (H body read; class/TERRASEA/rewrites/cap/tech
  gate/advisory all seen live across M34–M40, the tail checks static-only):** class 9 check
  (NEEDTERRAFORMERS) → TERRASEA (unit domain vs tile) → **mode rewrites** (5→6, 0→1/0xa) →
  domain capability (NOTATALL/NOTONLAND/NOTATSEA) → **pre-gate silent exits**: mode 6 without
  road bit, mode 1 without bit 0x8000 (clean return, **no advisory** — the MagTube key on a
  roadless tile does nothing) → tech gate `0x5a7520` → fail advisory dispatch → NOTBASE
  (`mask&1 && tile+2 low nibble < 8`) → ALREADYBUILT (terrain `+0` maskSET ⊆ tile mask; `$MINE0`
  name from `0x6938e0[mode*8+flag]`) → fungal branch (`mask&0x2000`, modes ∉ {5,6,0xb}) → pay
  path. Road-on-road can never reach ALREADYBUILT — the remap + gate intercept first.
* **Terrain table facts (H, live read):** k=6 MagTube maskSET **0x8** / clear 0 / work 3
  (alpha #TERRAIN mag 3 ✓); k=5 road 0x4 / 0 / 1 ✓; k=1 SoilEnricher 0x80000 / clear 0x200000 /
  work 8. MagTube completion threshold predicted 2×3 = 6 pre-adjustment (case-6 elev bump may
  raise it at elev 6 — unmeasured).
* **Harness (H):** `m39_issue.py` ran unmodified on the reject path — a TECHFAIL order ends in
  the 75 s STORE timeout → cleanup, and that **is** the expected terminal state for a rejected
  order (do not "fix" the runner); the game is left clean. The HASROAD pane is transient
  (auto-dismissed; the service loop never had to answer it). The `poke readback mismatches`
  event line is a false alarm when no other order-0 unit exists (nothing was poked).
* **Open:** live generic NOTUNTILTECH (`n`/`E`/`q`/`B` without tech 60 — Condenser/Echelon/
  Aquifer/Borehole) and live HASFARM; MagTube issue+completion after unlocking tech 18 (poke
  byte `0x985c1c+18` bit 3 → `r` → expect STORE 0x0a, mask 0x108006→0x10800e, threshold from the
  CHECK print); NOTBASE/ALREADYBUILT live.

## §M41 (session 41, 2026-10-22): MagTube unlock→issue→completion proven live — third mode, first completion of a REWRITTEN mode; the case-5/6 elevation bump is +2 FLAT (threshold 8 @ elev 6)

* **Unlock poke (H, live):** tech bit byte `0x985c1c+18`: `0x00 → 0x08` (bit 3 = player 3),
  poked with TracerPid 0, read-verified, gdb armed only after; `scripts/m35_gate.py` then shows
  mode 0x06 `req_tech(land)=18 unlocked=True`. Tech bits persist like order bytes.
* **Issue (H, live, `scripts/m39_issue.py --tag m41a --key r` run as-is, 45/45 bps):** `r` on the
  Former (idx 36) at (45,7) (roaded tile, mask 0x108006, elev 6): `TERRAF idx=36 mode=0x5` →
  remap → `TECHCHK idx=36 mode=0x6 **unlocked=1**` — gate PASSES: no TECHFAIL, no advisory —
  → `AFTERLATCH idx=36 mode=0x6` → `LOCKCHK` → **`STORE idx=36 order=0xa`** → `BCAST idx=36`.
  No picker, no COST/DEBIT — energy 15 flat all milestone (mode 6 ∉ {0x10,0x11} no-pay path).
  `evidence/m41a_{issue.json,gdb.log,chain.gdb,pre.png,post.png}`.
* **Exec lifecycle (H, live):** exec 1 on the issue turn `CHECK unit=1872 mode=6 accum_new=2
  **threshold=8** → NOTYET`; svc loop Return advanced the turn, `REFRESH` ×8 players, exec 2
  `4/8 → NOTYET` (year 2296). `scripts/m37_exec41.py --tag m41b --order 0x0a --rounds 3`: exec 3
  `6/8 → NOTYET` (2297), exec 4 `**8/8 → COMPLETE unit=1872 x=45 y=7 mode=6**` (2298). COMPLETE
  cleared order + work37 (post: order 0, work37 0, mpused 3). 4 executions over 4 turns at +2/turn.
* **Tile writeback (H, live mem):** (45,7) mask `0x108006 → **0x10800e**` (magtube bit 0x8 —
  table k=6 SET 0x8 / CLEAR 0 ✓), elev 6 untouched — mode 6 = mask swap only, like mode 5. The
  MASKSET bp print cap (300 hits; the m41b run logged 299, mostly AI) means our swap printed
  nothing — mem readback is authoritative (known pitfall, now with a second instance).
* **Threshold refinement (H):** MagTube @ elev 6 = **8** = 2×3 + 2 ⇒ the case-5/6 elevation bump
  is **+2 flat**, NOT doubling (road @ elev 6 = 4 = 2×1 + 2 fits the same rule; M40's
  "may double ⇒ 12" prediction is falsified — the CHECK print decided, as designed).
* **Stored order encodes the REWRITTEN mode (H):** the STORE writes `+17 = 0x0a` (mode 6 + 4),
  not 0x09 — the rewrite in the setter mutates the arg that the store tail later writes; first
  completion ever of a rewritten mode.
* **consume-all vs work (H, reconfirmed):** after each exec `mpused = 3` (Former full pool) while
  `+37` only rose +2 — the pool charged ≠ the work credited.
* **AI threshold/accum observations (O, same logs, tile elevations unmeasured):** base 2×`+8`
  holds everywhere seen — sensor 8, bunker 10, condenser (mode 12) 24, raise (16) 24, RemoveFungus
  (10) 12, solar 8 and 12 (two units), road 6 at (54,52) — larger bumps than +2 exist at
  unmeasured elevations, open. AI accum +3/exec on 7 AI formers, **+2 on one** (idx 51,
  RemoveFungus) — the "AI +3" rule is not universal; faction-trait hypothesis still open.
* **Harness (H):** both runners ran unmodified on the new mode — `m39_issue.py` STORE detection
  is order-agnostic; `m37_exec41.py`'s completion regex (`COMPLETE … x=45 y=7`) is mode-agnostic.
  Mid-turn start with sel already on the Former: runner skipped the selection dance, poked
  menu-pend `0x91b5c4`→0, one `r` press → TERRAF hit.
* **Live state left (end of session):** pid 914079, year **2298**, cur=3 (our turn — Former just
  completed, unactionable ⇒ **ENDOFTURN1 pane likely up; Return advances**), Former idx 36 at
  (45,7) order 0 work37 0 mpused 3, tile elev 6 mask **0x10800e**, energy **15**, tech-18 byte
  `0x985c1c+18 = 0x08` (**Monopole Magnets left UNLOCKED for player 3**; undo = clear bit 3),
  tech-60 byte = 0x16 (bits 1/2/4 — players 1/2/4 have it, player 3 does NOT), TracerPid 0, no
  gdb left. Scout Rover (idx 37) exploring; others Hold.
* **Open:** live generic NOTUNTILTECH (`n` Condenser mode 0xc — tech 60 gated for us), live
  HASFARM (needs a Former standing on a `mask&0x8000` tile — scan + multi-turn walk), economy-rate
  idle run, player↔faction-ID mapping, AI +3-vs-+2, NOTBASE/ALREADYBUILT live.

## §M42 (session 41 continued, 2026-10-22): generic NOTUNTILTECH live — the else-branch advisory + both substitution slots close; tech-record +0 = display-name POINTER; terraform op-name table decoded

* **Live branch (H, `scripts/m39_issue.py --tag m42n --key n` run as-is, 45/45 bps):** `n` on the
  Former at (45,7) (Condenser mode 0xc, tech 60 gated for player 3): `TERRAF idx=36 mode=0xc` →
  `TECHCHK idx=36 mode=0xc unlocked=0` → `TECHFAIL idx=36` → `ADVISOR #1 id=NOTUNTILTECH` +
  `PANE #1 id=NOTUNTILTECH`. Rejected cleanly (2nd instance of the pattern): order 0, energy 15,
  tile 0x10800e, year 2298 — zero state change; STORE timeout → cleanup = expected terminal.
  Runner mid-turn dance proven on a fresh turn: poke `+40=255` (order-0 only — here none existed,
  mismatch line = false alarm), poke Former `+40→0` (mpused 3 ⇒ unactionable), Tab cycle →
  sel=36, menu-pend poke 0, one `n` press → TERRAF. `evidence/m42n_*`.
* **Substitution closed live (H):** Script.txt `#NOTUNTILTECH` (caption "Planetary Ecologist"):
  `The "$TERRAFORMTYPE6" operation cannot be performed until we discover $TECH0.` Post-run mem:
  **slot 0 = "Ecological Engineering"** (tech 60 display name — cap-table tech id → `0x5a69f0` →
  `0x626634` slot 0, same flow as HASROAD's $TECH0), **slot 6 = "Construct Condenser"**, composed
  `0x997120` = *"The "Construct Condenser" operation cannot be performed until we discover
  Ecological Engineering."* — matches Script.txt verbatim. So: `$TECH0` is set by BOTH advisory
  branches; `$TERRAFORMTYPE6` = substitution **slot 6** (not a mode index), set via
  `0x6265a2(slot<10, text, v3, v4)` — sibling of `0x626634`: writes `0x999ff4[slot]`/
  `0x999fcc[slot]` (v<0 ⇒ defaults `0x99aa1c`/`0x99aa20`), formats `param_2` through `0x61482f`
  into `0x99a01c + slot*0x100`; 86 callers.
* **Tech-record layout correction (H):** `0x92fdb4 + id*44`: **+0 = POINTER to the display-name
  string** in the heap string arena, **+4 = short token** (M40's "name at +0" corrected). Live:
  18 → `0x20febb6` "Monopole Magnets" (token "Magnets"), 60 → `0x20feee1` "Ecological
  Engineering" (token "EcoEng"), 59 → `0x20feec9` "Environmental Economics" ("EnvEcon"), 17 →
  "MilAlg". Arena neighbors seen: "Bio-Engineering", "Adv. Ecological Engineering",
  "Retroviral Engineering", "Centauri Ecology". Cost/level ints still at +0x10/+0x14.
* **Terraform op-name table `0x94d2f8` (H, live):** 14 triplets `(land name, sea name, menu key
  char)` by mode — 0 Cultivate Farm/Kelp Farm/`f`; 1 Construct Soil Enricher/…/`f`; 2 Construct
  Mine/Construct Mining Platform/`M`; 3 Construct Solar Collector/Construct Tidal Harness/`S`;
  4 Plant Forest/"Plant ..."/`F`; 5 Build Road/Build Road/`R`; 6 Build Mag Tube/Build Mag Tube/
  `R`; 7 Construct Bunker/`K`; 8 Construct Airbase/`.`; 9 Construct Sensor Array/`O`; 10 Remove
  Fungus/Remove Sea Fungus/`F`; 11 Plant Fungus/Plant Sea Fungus/`F`; 12 Construct Condenser/`N`;
  13 Construct Echelon Mirror/`E`. This is the `$TERRAFORMTYPE` name source (and confirms the
  ORDERS.md key map, incl. land/sea variants: Mine→Mining Platform at sea, Solar→Tidal Harness).
* **Live state unchanged from M41 handoff:** year 2298, cur=3 our turn, Former idx 36 @ (45,7)
  order 0 work37 0 mpused 0 (poked), tile 0x10800e, energy 15, tech18 byte 0x08, TracerPid 0.
* **Open:** HASFARM live (mode-1 advisory — needs Former on a `mask&0x8000` tile), economy idle
  run, player↔faction-ID mapping.

## §M43 (session 41 continued, 2026-10-22): player↔"faction-ID" mapping resolved — the base +4/+5 byte IS the owner player index (identity); we own ZERO bases; `0x4e3700` corrected (works fine — short*-pointer math), inert for us because no base byte == 3

* **Identity mapping (H, live):** all 72 base records (`0x95da10` × 304): the `+4` and `+5` bytes
  are **always equal** and equal the **owner player index** — proven by 167/167 units standing on
  their base tile with `unit+14 (owner) == base+4` (zero mismatches), and by per-player home_base
  cross-refs (player2→byte2, player6→byte6, player7→byte7 clean; 1/4/5 noisy only via slid
  indices). There is **no separate faction-ID namespace** in these records. **M38's
  "base+4 = faction ID {1,2,4,5,6,7}, ≠ player index" is RETRACTED**: those values are owner
  player indices; 3 is absent simply because **player 3 (us) owns zero of the 72 bases**.
* **We have no bases (H, live):** every one of our 5 units has `home_base@+46 = 0xffff` (and
  chain `+48 = 0xffff`); zero base records carry byte 3. Our starting bases were gone before the
  save (captured/razed). Bases per owner: {1:10, 2:24, 4:7, 5:6, 6:16, 7:9}; player 0 has NO units
  and NO bases but owns 199 tiles — the destroyed-but-still-visited faction (M30's engine visits
  cur=0).
* **`0x4e3700(x, y, player)` corrected (H, body re-read with Ghidra short* semantics):** iterates
  all `DAT_00985af4` bases, `psVar7 = &0x95da12` (short*): compares **byte at base+4 == player
  arg**, reads x from byte base+0, y from short base+2, stride 0x98 **shorts** = 304 B — the
  "faction-byte quirk" was pointer-typing confusion in the notes, the function is correct. Inert
  for player 3 = no owned bases (⇒ the cost-side base-distance branch in `0x4cc7b0` can never
  fire for us; AI factions use it normally). Writes last distance to `DAT_008f0d34`. 38 callers.
* **Tile ownership (H, live histogram over 3200 records):** `tile+2` **low nibble = owner player
  index**, `0xf` = unowned — {0:199, 1:317, 2:468, 3:45, 4:345, 5:130, 6:261, 7:269, 15:1166}.
  Player 3 owns 45 tiles with zero bases — **orphan borders** (mechanism open: capture vs raze
  border-retention rules); player 0 likewise 199. High nibble is something else (mostly 0/1).
* **Base minerals (H, live):** `+64` u32 differs across bases (43/4/4/78 for bases 0–3) ⇒
  **per-base accumulator**, mirrored at `+152` within the 304 record (M31's mirror claim holds;
  its "equal in all 62 bases" phrasing meant the mirror-pair equality). No third copy at +216.
* **Faction identity (who plays which faction) — open:** alpha `#FACTIONS` = the 7 scenario
  factions (GAIANS, HIVE, UNIV, MORGAN, SPARTANS, BELIEVE, PEACE = def indices 0..6); the faction
  records `0x94d650 + player*0x82f` contain **no byte offset forming a permutation of 0..6 across
  the 7 live players** (scanned 0..0x82e) and no readable name pointers — the def index lives in
  the scenario/save section, not the runtime records. Scratch advisor slot 7 held "Gaians -
  Seething" (a diplomacy-pane leftover, not evidence).
* **Tooling unblocked:** with the identity mapping, owner attribution at any unit-index bp is
  trivial (`unit = idx*52 → owner @+14`) — apply to the AI +3-vs-+2 terraform question next run.
* **Live state unchanged:** pid 914079, year 2298, cur=3 our turn, Former idx 36 @ (45,7), tile
  0x10800e, energy 15, tech18 0x08, TracerPid 0.

## §M44 (session 41 continued, 2026-10-22): economy-rate idle run DONE — 12 zero-order rounds (years 2304→2315): our energy FLAT 0/turn (no bases ⇒ no income; upkeep never debits energy); AI mineral/energy rates measured; the Council-pane OK bar is un-OCR-able and must be found BY COLOUR; mask bit 0x2 = unit-present; type-record base corrected to 0x98ad88

* **The blocker that ate m44a/b/c (H, live):** a Planetary-Council governor-election pane sat on
  the pump at year 2303 for ~2 h. It had ALREADY resolved ("YANG ELECTED" banner + bottom-centre
  `PROPOSAL / ELECT PLANETARY GOVERNOR / Yang: 120  Lal: 94` bar) and only the **OK bar** remained.
  Tesseract reads the pane body but returns NOTHING for the blue bar's label, so vocabulary
  servicing (`strip(w[0])=="ok"`) can never escape it; the old runner preferred an ABSTAIN button
  (7 still on screen), looped 120 s and died on the preflight assert — 3 attempts, zero JSON.
* **Fix = colour, not OCR (H, calibrated live):** `find_ok_bar(png)` scans band x 240-560,
  y 430-520 bottom-up for the LOWEST contiguous wide blue bar (>= 8 rows, >= 60/160 sampled columns
  with `b > r+25 and b > 60`) and clicks its centre. Calibrated on the live pane: contiguous blue
  rows y **488-507**, x **268-532**, sample rgb (103,91,181); live click (400,497) and runner
  clicks (390,497)/(391,497) all dismissed it (year 2303 → 2304 immediately). **The HUD chrome
  draws a 1-px blue line at y 526 in EVERY frame including a bare HUD** — that is why the band
  stops at 520 and why a min-height rule is mandatory (otherwise the bare HUD tests positive and
  the runner clicks the map forever).
* **Servicing priority (H, worked 12 rounds unattended):** REALLYQUIT (oops row) → ENDOFTURN1
  (`Return`) → message-bar OK bar (colour) → ABSTAIN button → confirm pane → dialog/unknown
  (`Return`); bare HUD + our turn + NO ok bar → TURN COMPLETE. Runner events show all six paths
  fired. Runner also hardened: preflight failure is non-fatal, the JSON is rewritten after EVERY
  round, and the HUD economy panel is side-read per round. 12 rounds in ~4 min wall clock
  (08:53→08:57) once panes are serviced. `evidence/m44d_{idle.json,run.log,pre.png,post.png}`.
* **Our economy (H, 12 start-of-our-turn snapshots):** energy **15 at every round 2304..2315 ⇒
  0/turn**, and the HUD panel corroborates from the game's own readout: Commerce Income
  0/turn, Gross Income 0/turn, **Total Costs 0/turn, NET INCOME 0/turn** — but note the
  side-read is best-effort: only rounds 1/3/4 caught the economy panel (rounds 11-12 OCR'd the
  diplomacy strip instead: "Chainnan / Yang / Qusrrelsome / TRUCE"), so the corroboration is
  from the panel-visible rounds; the memory series is the authoritative stream. With zero bases (M43)
  there is no income AND unit upkeep never debits faction energy. Consequence for the project:
  the elev-6 raise/lower issue cost 25 (M38 formula `(|elev-3|+2)^2`) is **unpayable indefinitely**
  under this economy — only founding a base (or a trade/loan) changes it. This closes the
  M38/M39/M40 "income ≈ upkeep ≈ +0/turn, unquantified" lead: income = 0 and upkeep-on-energy = 0.
* **AI economy rates (H, same snapshots, first difference over 11 intervals):**
  energy/round {1:-1.4, 2:-1.3, 3:0.0, 4:+10.9, 5:-0.5, 6:+5.3, 7:-0.9};
  base-minerals/round {1:+2.3, 2:+8.3, 4:-11.2, 5:-1.9, 6:+31.2, 7:+1.1}.
  Player 4 anti-correlates almost exactly (minerals -11.2 vs energy +10.9, sum -0.3) ⇒ the base
  mineral store drains into faction energy at ≈1:1 when not spent on production — **O (inferred
  from one faction)**. Player 6 accumulates BOTH (+31.2 minerals and +5.3 energy/round = the
  industrializer); 1/2/5/7 spend roughly everything they mine. Bases during the run:
  {1:10→10, 2:25→24, 4:8→9, 5:5→4, 6:16→17, 7:9→9}, `0x985af4` 72→73; pops grew 2:123→133,
  6:56→62. Mineral totals oscillate per round (production spends them) — the per-round noise is
  real, not a read error.
* **Attrition (H counts, O cause):** our unit count fell **5 → 2** across the idle rounds (drops
  at 2305, 2308, 2309). Survivors: idx 30 = **Colony Pod** (type 0, class 8) at (45,11) and
  idx 31 = **Laser Squad** (type 195, class 1) at (43,11), both order 2 (Hold), `+16 = 512`
  (2.0 legs), `home_base = 0xffff`. **The Formers unit (type 1, class 9) is dead** — we now have
  NO terraforming capability. Cause not observed directly; hypothesis = unsupported-unit attrition
  with zero bases (O — retest by founding a base and watching whether the survivors stabilise).
* **Autosave rotation (H):** the game rewrites ALL EIGHT autosave slots on a ring — slots
  30/20/10 every 10 years (years 2290/2300/2310) then 5,4,3,2,1 yearly (2311..2315); the file's
  year u16@`0x54` matches the live year. The old load-recipe note "slot 2 = 2198" is STALE (slot 2
  held year 2314 at run end). Recovery points therefore exist: Autosave 30 = 2290, 20 = 2300,
  10 = 2310 (a Former is probably alive in the earlier ones).
* **Tile record == map-file cell PAIR, byte-exact (H):** runtime 0x2c record == the .SAV/.MP
  22-byte cell `(2n,y)` followed by cell `(2n+1,y)` — verified against the LIVE autosave map
  section (dims anchor 79,372 + 2,724 = cells): rec 302 first 22 bytes == file cell (44,7),
  last 22 == file cell (45,7). So the .MP "W*H*22 cell records" are HALVES of runtime records.
* **Accessors are parity-blind (H, code):** `0x582ed0(x,y,bits,set)`, `0x5831a0(x,y)` and the
  elevation readers all compute `40*y + (x>>1)` and touch record+0 (elev = byte0>>5) / record+8
  (mask) with NO parity term ⇒ the pair (2n,y)/(2n+1,y) genuinely shares the elevation byte and
  the +8 mask in the game's own eyes. A SECOND mask-shaped dword lives at record+**0x18** (= odd
  half +2): for our (44,7)/(45,7) pair live +8 = 0x10800c while +0x18 = 0x10800e; elsewhere
  (e.g. record 462 = (44,11)/(45,11)) the two are equal. It tracks +8 but is not written by the
  parity-blind setter — semantics OPEN (snapshot/backup layer? 2951/3200 records differ in at
  least one bit, bit 20 differing 1913×).
* **Mask bit 0x2 = UNIT PRESENT on the tile (H, 3193/3200):** histogram test — `+8` bit 1 agrees
  with "a unit stands on either half of the record" in 3193/3200 records, **0 false negatives**,
  7 stale positives (recently vacated). This explains (45,7) going 0x10800e → 0x10800c during the
  idle run: our Former died/left. Bit vocabulary from the runtime terrain table `0x6938f0+k*32`
  SET/CLEAR × live op-name strings `0x94d2f8`: farm 0x8000, soil enricher 0x80000, mine 0x10,
  solar/tidal 0x40, forest 0x200000, road 0x4, magtube 0x8, bunker 0x800, **airbase 0x40000
  (k=8, work 10, CLEARS bunker 0x800)**, **sensor array 0x80000000 (k=9, work 4)**, fungus 0x20
  (k=10 Remove Fungus CLEARS it / k=11 Plant Fungus SETS it), condenser 0x400000, echelon mirror
  0x8000000, k=14 SET 0x1000000 work 24, k=15 work 18, k=16/17 raise/lower work 12, SET/CLEAR 0.
  Corrections to M42: `0x94d2f8` is 14 × (land name, sea name, **key-char STRING**) stride 12
  (pointers into the heap arena), and **k=8 is Construct Airbase, not Sensor** — sensor is k=9
  (work 4, which is what M41's observed AI threshold 8 already implied).
* **Type-record base corrected (H):** the 52-B type records start at **0x98ad88**: `+0` name[34],
  `+32` ability u32 (= 0x98ada8), `+36` domain byte (= 0x98adac), `+42` class byte (= 0x98adb2).
  The standing ABSOLUTE addresses are all correct; the "record base = 0x98ada8, name at +20"
  phrasing was wrong — that read pairs each class byte with the NEXT record's name. Proof: live
  strings Colony Pod @0x98ad88, Formers @0x98adbc, Scout Patrol @0x98adf0 (stride 52) vs alpha
  `#UNITS` rows 0/1/2 = Colony Pod(class 8) / Formers(class 9) / Scout Patrol(class 3), and
  `0x4d44d0` line 1 gates terraform on `class byte == 9` ✓ (so the harness `cls == 9` Former
  filter was right all along). Runtime table has >= 196 types (variant expansion; alpha ships only
  15 template rows): type 193 = Scout Rover (cls 3), 194 = Synthmetal Garrison (cls 2),
  195 = Laser Squad (cls 1).
* **Live state at handoff:** pid 914079, year **2315**, cur=3 (our turn OPEN, bare HUD),
  Colony Pod idx 30 @ (45,11) + Laser Squad idx 31 @ (43,11) both Hold, energy **15**, tech18
  byte `0x985c1c+18` = 0x08 (ours), tech60 = 0x16 (not ours), tech59 = 0x1e (ours via the old
  poke), TracerPid 0, no gdb attached. Tiles: (45,11) elev 4 owner 3 `+8` 0x108006 (road+magtube
  +unit bit), (45,7) elev 6 owner 3 `+8` 0x10800c (road+magtube, unit gone).
## §M45 (session 42, 2026-10-22): FIRST BASE FOUNDED — `b`/BUILD BASE path live-verified end to end; NEWBASE takes a plain Return; founding claims a bit-0x1000 border but 0x4e3b50 said the tile was UNCLAIMED (-1) so no dispute pane; economy re-measured: faction energy 15→19 ONCE then flat again

* **What ran (H, live):** `scripts/m45_base.py --tag m45a` (new runner + `scripts/m45_base.gdb`,
  15/15 bps armed) pressed `b` on the Colony Pod (unit idx 30, type 0, **class 8**) at (45,11) in
  year 2315 with the turn open. Trace (`evidence/m45a_gdb.log`, 7 lines, verbatim):
  `SETTER unit=30` → `BORDERRET eax=-1` → `LIMITRET eax=12` → `PANE #1 id=NEWBASE` →
  `ALLOCRET base=73 unit=30` → `CREATERET base=73 unit=30` → `PANE #2 id=BASEFOUNDED`.
  Outcome `created`; **n_bases 73→74**, our first base record = idx 73 (now 72 after the array
  compacted when someone else's base died) at (45,11), owner 3, **pop 5**, name
  **"Climactic Research"** (the game's own generated default — we typed nothing), +64 minerals 10.
  The Pod is gone (consumed); the trace's CONSUME/CLAIM/BASEINIT/FC20/NOTIFY bps never fired
  because of the address bug below, so the *unit-removal* callee is static-only evidence.
* **The `b` gate map (H, static from `0x4d1280` + live pre-flight emulation).** In order, each
  ends the handler with an advisory via `0x483470`: class byte (`type+42`) **must be 8** else
  `NEEDCOLONISTS`; then tile gates — `NOTINTRIAD` (`(elev<3) != (domain_table[type+36]==1)`,
  table base `0x92ae81` stride 0x90), `FUNGUSDANGUS` (mask 0x20 ∧ elev>3), `NOTONMONOLITH`
  (mask 0x2000), `NOTONROCKY` (record **+5 & 0xc0 > 0x40** ∧ elev>3), `SIMULNO`
  (`0x5255e0`: false in solo — `0x920434==0`), **can-act `0x5acc00`**, `BASETOONEAR`
  (8-neighbour scan: **mask bit 0x1** = base on the pair ∧ owner nibble < 8 — offsets from
  `0x6784a0`/`0x6784c4` = [(1,-1),(2,0),(1,1),(0,2),(-1,1),(-2,0),(-1,-1),(0,-2)]), border
  dispute via `0x4e3b50` (TERRPACT / TERRTREATY / TERRTRUCE / THISLANDISMYLAND / BULLY panes),
  base limit `0x4e9b40` (returned **12** for us; BUREAUCRACY pane fires only when the count is a
  nonzero multiple of it), default name `0x4e3cf0`, **NEWBASE** name pane
  `0x462d30(s_NEWBASE, 0x17, namebuf, 0)`, then **`0x4cca50(unit, name)`** = slot alloc
  `0x4e47d0` → name → **base+19** → consume unit `0x5abb40` → border claim `0x50bea0` →
  `0x41b780(idx,1)` / `0x50fc20(1)`; then the BASEFOUNDED Script pane (`#BASEFOUNDED` caption
  "Chief Librarian", `$BASENAME0 founded in $NUM0`, art `colfoun_sm.pcx`; slots filled by
  `0x4626634(0, base+19)` + `0x4626581(0, year)`).
* **Can-act rule, sharpened (H, static + live):** `0x5acc00` refuses with `UNITMOVED` when
  `unit+4 & 0x4200 == 0` **and the ORDER BYTE at +17 ∈ {1,2,3}** — so a Hold unit must be poked
  `+17 = 0` before any order key works (both our units sat at +17=2; the poke is what made the
  Pod cycle-selectable and key-able). Owner check there is `unit+14 == 0x91b5b4` (current player),
  MP check is `0x5ac650(unit) - unit+40 > 0` — the M39 `+40=255` rival-disable poke still works
  to steer Tab onto one unit.
* **NEWBASE servicing (H, live):** the name-entry pane accepts the generated default with a plain
  **Return** — `service_pane`'s `dialog → Return` default did it, no typing, no click; the pane's
  Script geometry (`#NEWBASE #x 10 #y 40 #xs 320` + `Name:`) matches FIRSTBASE, whose OK was
  measured at (400,171) — never needed.
* **The pane the founding leaves open (H, live; harness bug fixed):** after BASEFOUNDED the game
  opens the new base's **BASE screen** (top menu EXPLORE/DISCOVER/GOVERNOR/BUILD/CONQUER,
  RESOURCE/SUPPORT/PSYCH tabs, RENAMEd/OK row at y≈365 — OUTSIDE `find_ok_bar`'s 430-520 band).
  `service_pane` had **no branch for kind `base`** (not confirm, not dialog/unknown) so
  `m45b_idle` spun 15 minutes on 1 round until killed. Patched: `kind == "base"` → one Escape
  (M26 rule) in both `m44_idle.service_pane` and `m45_base.py`'s post-create loop.
* **What the new base is (H, live screenshot `evidence/m45a_post.png`):** facilities list
  Headquarters, Recycling Tank, Recreation Commons, Energy Bank, Network Node (the pod's
  starting kit); RESOURCE tab readout **NUTRIENTS 009-010 = −001 (SHORTFALL, panel says
  "Hunger!"), MINERALS 007-000 = +007, ENERGY 003-000 = +003**, INTAKE−CONSUMPTION = SHORTFALL;
  M.Y. 2315 Energy 15 Eco-Damage 0; queue 8 empty slots. Pop then fell 5→4 by 2317 — the
  nutrient shortfall shows up as population attrition, not eco-damage.
* **Border claim (H, statistical, 74/74 bases):** the founding set **mask bit 0x1000** on the tile
  pair (0x108006 → 0x109005; the 0x8000 farm bit cleared in the same write) and every base in the
  game owns a footprint of 0x1000 tiles: assigning each of the 1258 flagged pairs to its nearest
  base gives **12-31 pairs per base with Chebyshev max distance 3-9, mean ≈3.3, and NO pop
  dependence** (pop 1 → mean 18.7, pop 11 → 13.5). So **mask1(+8) bit 0x1000 = "inside a base's
  claimed border", fixed hex radius ≈3, not population-scaled**; it lives in mask1 almost
  exclusively (mask1-only 1238, both 41, mask2-only 1) and appears on ocean pairs too (coastal
  bases). Yet `0x4e3b50` returned **-1** for our tile at founding even though its owner nibble
  was already 3 ⇒ **the nibble layer and the border layer are different things** — the ~45
  nibble-3 "orphan" tiles we inherited (M43) are NOT borders to the game, which is exactly why no
  territory-dispute pane fired. Census after founding: nibble-3 cells 45→101 (parity-corrected
  per-cell read; byte+2 low nibble = even x, high = odd x).
* **Economy re-measure (H, live, 16 start-of-our-turn snapshots over 2315→2329):**
  `evidence/m45c_idle.json` (6 rounds, 2315-2320) + `evidence/m45f_idle.json` (10 rounds,
  2320-2329, ended on its budget at round 10): our faction energy **15 for 2315-2319, then 19 at
  2320, then FLAT 19 through 2329** — one +4 credit in fifteen intervals; `m45f`'s own
  deltas block says **energy3 = 0.0/round over 9 intervals** while the base's own RESOURCE tab
  reads +003. Base +64 minerals oscillate 10→10→6→2→8→4→9→4→8→2→5→8→1→3→5 with no trend while
  pop sits at 4 and `nmine` (our unit count) climbs 1→**6** as the base turns out Scout Patrols. M44's minerals↔energy
  anti-correlation shows up on OUR side in the one moving interval (2319→2320: minerals 8→4,
  energy 15→19, ≈1:1). **Net: founding a pod base does NOT make us solvent** — the 25-cost
  elev-6 raise (M38) is still unpayable after 9 years of owning a base.
* **HUD Gross Income / Total Costs / NET INCOME could NOT be read this session (honest limit):**
  every snapshot frame had either a dialog/base screen up or the bottom-left panel showing unit
  info (`Scout Patrol [1-1-1] / Green / Climactic Research / Moves: 1 / No Orders`), so
  `hud_econ`'s crop OCR'd garbage. The memory series is the only authoritative stream here; the
  panel read is a standing open item.
* **PITFALL (H, cost us 7 of 15 trace lines): Ghidra names callees `FUN_<address>` VERBATIM —
  do not "normalize" them.** The first m45a run armed `0x45abb40 / 0x450bea0 / 0x441b780 /
  0x450fc20 / 0x45355c0 / 0x4551a20 / 0x447f490` for `FUN_005abb40 / 0050bea0 / 0041b780 /
  0050fc20 / 005355c0 / 00551a20 / 0047f490` — a duplicated leading digit (+0x400000). gdb armed
  all 15 (memory is mapped, so a wrong address never complains) and the seven bogus ones never
  fired. `scripts/m45_base.gdb` now carries the corrected addresses + the warning.
* **Also (M44 follow-ups closed/open):** mask bit 0x1 = "base on this pair" is now proven on
  **74/74** base tiles (was 73/73) and is what `0x4e34f0(x,y)` requires before scanning the base
  array (`0x95da10` stride 0x130, compares +0 x / +2 y). Base +64 == +152 in 74/74 (M44's mirror
  claim holds). Base +56 is the constant `0x00dfbe41` in all 74 records (M44's "copied from home
  base" reading is wrong — it never varies). **Open:** the autosave↔runtime cell mapping —
  M44's "record == two 22-byte file cells at +2724, byte-exact" did NOT reproduce today (frozen
  pre-founding `Alpha Centauri Autosave 1.SAV` year-field 2315; locating stable ocean pairs gave
  offsets that fit no row-stride model, e.g. Δy39 for the same pair = 70048 B ≈ 1796 B/row, not
  44·40=1760), so treat the save-map layout as unverified until re-derived.
* **Bonus (H, live):** produced units are homed to their base — the five new Scout Patrols
  (type 2, cls 3) all carry `unit+46 = 0x48` = base idx 72, while the surviving Laser Squad
  (type 195, idx 22) still has `home = 0xffff` ✓ closes M24's "home base idx" field on the write
  side. n_bases is now 75 (someone else built one) and the base array compacts on any death,
  so **never hardcode a base idx across turns**.
* **Live state at handoff:** pid 914079, year **2329**, cur=3 our turn open, TracerPid 0, no gdb
  attached; 1 base (idx 72, "Climactic Research", (45,11), pop 4, +64 minerals 1-10 oscillating),
  **6 units** (Laser Squad idx 22 @ (43,11) Hold + 5 Scout Patrols @ (45,11) order 0), energy
  **19**, tech bytes unchanged (`0x985c1c+18` 0x08 ours), no Former-class (cls 9) unit anywhere —
  **we cannot terraform or build anything new without minerals/production, and we have no colonist
  left to found a second base.** Autosave slots frozen 09:48 in `scratch/auto2315/` (1.SAV = 2315 turn-start, the last
  pre-founding snapshot).
* **Next (M46), pick ONE:** (1) **Where does the +4 come from and who sets the slope** — find the
  HUD economy panel's source values: grep the shards for the code that formats the Gross Income /
  Total Costs rows (panel crop 262,425,132,72), or find the per-faction income/cost fields in the
  faction record (`0x94d650 + p*0x82f*4`, 2111 ints) by correlating against measured energy
  deltas; that is what makes "when is the 25-cost raise payable" answerable. (2) **Unit upkeep
  table**: alpha `#UNITS` columns → type-record offsets (support cost), then verify
  income−upkeep against the measured 0/turn. (3) **Queue a unit deliberately** on our base
  (base screen: click a queue slot, pick, OK) and watch +64 minerals drain per turn — that
  isolates the mineral economy from the energy one. (4) Who writes mask1 bit 0x1000 (the border
  layer) — `0x50bea0` is the candidate callee; arm it with the CORRECTED address.
  (5) Player↔faction NAME mapping from the save faction section (M43 open item, static).


## §M46 (session 43, 2026-10-22): ECONOMY DECOMPOSED — the upkeep pipeline mapped end to end; HUD Gross/Costs/NET = scratch globals recomputed by `FUN_00445900`; our slope reproduced from memory (net 0 ⇔ energy flat); the blocker that ate m46a-d was the OPERATIONS DIRECTOR end-turn pane

* **Static map (H, pseudocode `ghidra_out/` + live scratch reads).** The per-round
  economy runs inside the upkeep-phase driver **`0x521070`** (called from turn
  resolution `0x5214a0`/`0x51e700`; its own progress strings name the stages
  UPKEEP4..7). Stage 1 runs **`0x5208f0(p)`** per live player — the per-player
  upkeep: sub-steps `0x5a1830`, `0x51f730` (known unit refresh), **`0x520540`**
  (the income core, below), `0x51fe90` (recomputes the two allocation sliders at
  faction `+0x104`/`+0x108` from pop/land/eco state), `0x5551e0`, `0x556690`,
  `0x5a1ad0` (attitude-rechange energy penalty `−(Δn³)·X`), Corner-office warning
  check; **tail: `energy −= faction+4; faction+4 = 0; clamp ≥ 0`** — so
  **faction+4 (int[1]) is a within-round spending ledger** debited at upkeep
  (always 0 at start-of-our-turn: verified live, all players, m46a+e rounds).
  Stage 3 is research: while `faction + 2204` (advance queue = lab-team
  count — **byte offset**; the export's `int[2204]` is past the 2095-int
  record and reads the next player's data, corrected at handoff) ticks down,
  **`0x5aaa20(p)`** runs per team ("Earning a Tech" announce;
  completes the tech when `faction+0x1a8` points reach cost); `0x5aa880` picks
  the next tech (writes **faction+0x1ac** = tech-under-research — verified: p2
  completed a tech between rounds and +0x1ac switched 30→77 with +0x1a8 reset).
* **Income core `0x520540(p)` (H):** clears scratch fields; pays scheduled
  gifts out of energy (relation-matrix `+0xcc` pending, `0x520540` loop, pact
  flag exempts); then **for each of p's bases calls `0x4f5a70(base)`**; then
  AI-only stockpile conversion (`energy += faction+0xe0/3` or `×2/3`, gated
  `DAT_00985aec > 3` — we have `DAT_00985aec = 2`, so it never applies to us);
  then faction-trait energy: trait record flag `0x4000` ⇒ either +1 energy per
  base or `energy += trait%·energy/100` (trait record `0x927a7c + p·0x59c`).
* **Per-base round step `0x4f5a70(base)` (H):** sets `DAT_008f0d60` = base
  record ptr (the same global the base UI reads), runs the production pipeline
  `0x4e8d60 → 0x4e78e0 → 0x4e92c0 → 0x4e93f0 → 0x4eaa10 → 0x4ef6d0 → 0x4f26e0`
  (AI surplus spend: reads `energy/10`, `energy/50`) `→ 0x4ee410`, a second pass
  with `DAT_008f0d64 = 1`, then **`energy += *(int *)(base + 0x7e)`** — the
  per-base per-round ENERGY INCOME field — accumulates trade shares into
  faction+0xe8, ticks the pop-growth countdown `base+7`, and (turn > 1) calls
  `0x4f47f0` (below) + `0x4ebef0(0)`. **`base+0x7e` reads 0 for all 75 bases at
  start-of-our-turn** (transient: produced and consumed inside upkeep; its writer
  is not visible anywhere in the export — the only reference in all shards is
  the `+=` read itself; O that it is written via a computed pointer in the
  pipeline).
* **Facility upkeep charge `0x4f47f0` (H):** per completed facility of the base:
  cost = `0x4f4760(item, owner)`; **`energy −= cost`** directly (not via the
  ledger) and `faction+0xe0 += cost`; on **insufficient funds it SELLS a
  facility** (clears its bitmap bit, refunds `FUN_004e40a0 × refund table
  `0x984d44`, POWERSHORT warning pane). `0x4f4760(item, p)`: item 27 special
  (`min((faction−0x218-array+1)/2, 0x572300(p))`); else 0 if the item is on the
  player's **disabled list**, else table `0x984d48 + item·0x30` int0.
* **Item table decoded live (H):** 39 rows × 0x30 B; int0 = **upkeep**, int1 =
  **required-tech id** (tech names read from `0x92fdb4 + id·44`: 44=EthCalc,
  4=Psych, 45=IndEcon, 2=InfNet, 59=EnvEcon …). **Runtime item index = alpha
  `#FACILITIES` line index + 1** (runtime 13 requires EnvEcon = Tree Farm =
  alpha 12 ✓; verified for items 1,2,3,6,7,8 = HQ, Recycling Tanks, Perimeter?,
  Recreation Commons, Energy Bank, Network Node). Completion test
  `0x421fe0(item, base, 0)`: byte bitmap at **base+0x8c**, byte `item>>3`, bit
  `item&7` (`0x507410` = the mapper) — our base: 0x1CA + 0x01 = items
  {1,3,6,7,8} ✓ all five facilities.
* **Disabled list decoded (H, resolved the 3-vs-2 upkeep puzzle):** lives in
  the **player trait record `0x927a7c + p·0x59c`** (stride 0x59c = 1436 B, NOT
  0x167 — 0x167 is the *int-index* Ghidra prints): count int at +0x20, type
  array at +0x24 (8 ints), item array at +0x44; `0x4f4760` walks
  `list[i−8] == 2 && list[i] == item` ⇒ upkeep 0. **Our record: n=4,
  type[2]=2 item[2]=8 ⇒ Network Node upkeep is zeroed for our faction** ⇒
  Σ upkeep = HQ 0 + RecTank 0 + RecCommons 1 + EnergyBank 1 + NN 0 = **2**,
  exactly the live `DAT_00744f28 = 2` and `744f2c[72] = 2` ✓✓.
* **HUD economy panel = recomputed scratch globals (H).** `FUN_00445900(player,
  0)` (called on every faction-display/HUD redraw, e.g. from `FUN_0049fee0`
  case 0 and `FUN_0045a920`) sums over the player's bases:
  `0x745734 = Σ base+0xfc` (Gross Income row), `0x744f28 = Σ item upkeep`
  (Total Costs row), `0x7457d4 = trade net`, **`0x7457dc = Σ (base+0xfc −
  upkeep) ± gifts` (NET INCOME row)**; `0x744f2c[base]` per-base upkeep;
  `0x745738[39]` per-item counts; `0x74572c = Σ base+0x104 × (FUN_00423af0(
  faction+0x54)·10 + 100)` (food), `0x745730 = % self-sufficiency`. The faction
  display pane `0x49fee0` draws rows 0x17d/0x17e/0x17f = these globals verbatim
  (`FUN_00409690` string ids; NET row at its line 2879). The bottom-strip
  "Total Costs" = `7457dc − 745734` (M44-era finding, re-confirmed).
  **Live: our scratch = gross 2, upkeep 2, trade 0, net 0 ⇔ energy 19 flat**
  (M45's 16 rounds + m46e rounds 2330/2331).
* **Production split `0x4eaa10` (H):** `base+0xd4 = base+0xc4 − base+0xf4`;
  buckets by the faction sliders `a = faction+0x104`, `b = faction+0x108`:
  `base+0x100 = (a·prod+4)/10`, `base+0xfc = min(prod − 0x100, ((10−a−b)·prod+4)/10)`,
  `base+0x104 = leftover`, `base+0x108 = ((9−a−b)·prod+4)/10` capped. Our live
  base: c4 3, d4 3, buckets 100=0 fc=2 104=3 108=2 (the bucket formulas don't
  close on c4 alone — facility multipliers feed in earlier; O on the exact
  inputs). `0x445900` treats `base+0xfc` as the income row and `base+0x104` as
  the FOOD bucket (74572c = 3·120 = 360 ✓ live).
* **Corner Market (H):** `0x4e2050` = Corner Market sell (needs the HQ item
  present — bitmap item 1); triggered from `0x5208f0` only when
  `energy > FUN_0058f8b0(p)` where **`58f8b0 = max(Σ rival production, 1000)`**
  ⇒ it is a SURPLUS DUMP, not a low-energy bailout — with energy 19 it can
  never fire for us. (So the 2320 +4 credit is NOT the Corner Market.)
* **Per-round full-record diff, all 7 AI players (H, `evidence/m46e_econ.json`,
  rounds 2330→2331; records are **2095 ints**, stride 0x20bc = 8380 B — the
  earlier 2111 was reading 16 ints into the next record; int[2095] = next
  player's energy, a useful self-check).** Panel-net vs observed Δenergy vs
  research-points gain:
  `p1: 30 / +4 / +40 · p2: 16 / −5 / (tech completed, +0x1a8 reset 485→87,
  +0x1ac 30→77) · p3(US): 0 / 0 / +4 · p4: 29 / +18 / +36 · p5: 7 / +7 / +7 ·
  p6: 10 / −24 / +11 · p7: 25 / +11 / +37`.
  Exact matches for **us** and p5; the gaps are the within-round debits the
  panel does not show (ledger faction+4: research, gifts, AI terraform costs —
  mechanism proven, per-action split open). **Unit upkeep confirmed again as
  never debiting faction energy** (M44 footing holds: our 6 scouts, energy
  flat; the ledger deltas for us are 0).
* **THE STALLER (H, cost m46a/b/c/d): the OPERATIONS DIRECTOR end-turn pane.**
  Clicking TURN COMPLETE with idle units pops a Script confirm pane — "Some of
  our units have not yet moved this turn. DO YOU REALLY WANT TO END THE TURN
  NOW?" — option rows `Cancel.` (DEFAULT) / `Yes, end the turn.` + a **blue OK
  bar at y ≈ 215–350 (pane y drifts with stacking), OUTSIDE `find_ok_bar`'s
  430–520 band**; Return presses OK with Cancel selected ⇒ the turn never ends;
  the orange TURN COMPLETE button stays visible behind the pane so any
  button-visibility check passes and runners re-click into it forever. Fix
  (calibrated live on two frames, both offsets identical): from the OCR
  **Cancel word centre (cx, cy): click (cx, cy+24)** selects "Yes, end the
  turn.", **click (cx, cy+49)** hits the OK bar. Now in `m44_idle.service_pane`
  (priority 2.5, keywords `wanttoendtheturn`/`havenotyetmoved`) and in
  `scripts/m46_econ.py`'s svc block. Also new: **`hud_up(png)`** — orange-pixel
  count (r>180, 60≤g≤160, b<80) > 300 in box (600,395,800,425) — the only
  reliable HUD test (OCR of the busy HUD garbles "TURN COMPLETE" to
  "turngomplete" and the hover-info panel makes `classify()` deny `hud`);
  TURN_BTN (650,410) is inside the button (bbox x 609–791, y 405–426) and
  works once the pane is out of the way.
* **Answers to the standing M46 questions.** (1) Our slope: net = gross 2 −
  upkeep 2 = 0 ⇒ energy stays 19 every round; **25 energy is NOT disposable at
  the current slope — never, without growth** (need +6 with Δ0/round; the
  elev-6 raise stays unpayable). Solvency levers: pop/facility growth raising
  `Σ base+0xfc`, or selling minerals (Corner Market needs energy > 1000, so
  not us). (2) The 2320 +4 credit: one-off mineral→energy-shaped credit
  (minerals −4, energy +4, M44's 1:1 signature); candidates narrowed to the
  Energy Bank "Economy Bonus" effect / pipeline transient `base+0x7e` path —
  NOT the Corner Market (surplus-gated), NOT the AI stockpile line (gated on
  `DAT_00985aec > 3`, ours is 2); **mechanism open (M)**.
* **Harness (H):** `scripts/m46_econ.py` — deep start-of-turn snapshotter:
  full faction records (all live players), scratch globals, per-base production
  buckets, our bases' full 76-int records, item counts; svc loop = pane-keyword
  servicing (incl. ENDTURN) + `hud_up`-gated TURN_BTN clicks + Escape fallback;
  read-only (asserts TracerPid 0). m46e: 2 rounds, 2 HUD clicks, 2 ENDTURN
  services, zero stalls. **Pitfall re-encountered 3× this session: `pkill -f
  <pattern>` matches the killing shell's own cmdline when the pattern text
  appears in your command — kill by PID or use a bracketed pattern.**
* Evidence: `evidence/m46a_econ.json` (+`_run.log`, pre/post png),
  `m46b_*`, `m46c_*` (incl. `m46c_probe.png` = the base-screen trap),
  `m46d_*` (incl. `m46d_confirm.png`/`m46d_yesok.png` = the two OPERATIONS
  DIRECTOR frames with the measured geometry), `m46e_{econ.json,run.log}` =
  the good run. Scripts: `scripts/m46_econ.py`, `scratch/m46_{scan,table,fn,
  fn2,fn3,writers,basewriters,7e,7e2,yearfn,upkeepfn,ledger,ledger2,res,min,
  flag,attr}.py`.

## §M47 (session 44, 2026-10-22): WRITE PROVENANCE — who actually moves our energy; the `base+0x7e` field was a Ghidra pointer-arithmetic artifact (the real addend is `base+0xfc`)

* **Instrument validated first (H).** Hardware watchpoints DO work under this Wine build
  (gdb 17, i386): a watch on the mission year fired exactly once with
  `eip=0x51f554 val=2335` inside **`FUN_0051f320`** (the turn-advance routine) when the
  round rolled 2334→2335 (`evidence/m47_year_watch.log`). Earlier sessions had only ever
  *armed* watchpoints without a known writer, so this is the first positive control.
* **Our income writer (H, live).** Watching our faction energy `0x953884`
  (`= 0x94d650 + 3·0x20bc`) through a full round caught exactly three writes
  (`evidence/m47e_watch.log`):
  `WENERGY n=1 eip=0x4f5c92 val=21 ecx=0x962f90(=our base) esi=0x6234 edi=3` then two
  debits `eip=0x4f4958 val=20 / val=19 esi=6,7`. Disassembly of the site:
  `4f5c7f mov 0xfc(%ecx),%edx · 4f5c85 add %edx,%eax · 4f5c8c mov %eax,0x94d650(%esi)`
  ⇒ **the per-base income added to faction energy is `base+0xfc`**, inside
  **`FUN_004f5a70`**, and it equals the HUD's GROSS row by construction.
* **Correction to M46 (H): `base+0x7e` is never written.** Two armed rounds (including
  the round above) produced **zero** writes to `base+0x7c..0x7f` (`0x96300c` watch), and
  the field reads 0 at every snapshot. Ghidra prints the income line as
  `*(int *)(DAT_008f0d60 + 0x7e)` — but `DAT_008f0d60` is typed **short \***, so `+0x7e`
  is `0x7e·2 = 0xfc` **bytes**. There is no transient income field: M46's "transient
  income field with no visible writer" was pointer arithmetic, not a missing writer.
* **Our upkeep writers (H, live).** The two remaining writes are `eip=0x4f4958`,
  `eax=1` (cost), `esi=6` then `7` (runtime item ids = Recreation Commons, Energy Bank),
  `edi=0x6234` (our faction byte offset), inside **`FUN_004f47f0`**:
  `4f494a mov 0x94d650(%edi),%ecx · 4f4950 sub %eax,%ecx · 4f4952 mov %ecx,0x94d650(%edi)
  · 4f4958 mov 0x94d730(%edi),%edx · 4f4962 mov %edx,0x94d730(%edi)` — i.e.
  **`energy -= cost`** AND **`faction+0xe0 += cost`** per completed facility. Live items
  6 and 7 at 1 each = the 2 we measured; item 8 (Network Node) never fires because our
  trait record disables it (M46).
* **The spending ledger (`faction+4`) was NOT touched** by us in the watched round
  (0 hits on `0x953888`) — consistent with net 0 and no research/gift/terraform spend.
  Its writers are therefore *action-time*, not upkeep-time, and remain **open** (M).
* **AI provenance, one round on Morgan p4 (H, `evidence/m47f_watch.log`, 28 hits).**
  Watching `0x955940` (energy) and `0x955944` (ledger), year 2335→2336:
  - income adds at **0x4f5c92** once per base (ecx = 8 distinct base records);
  - upkeep debits at **0x4f4958** per item (`esi` = item id 2,6,7,8,0x18=24,0x1b=27,
    cost 1 or 2);
  - **a direct per-base debit of −7 twice at `eip=0x4f2dc4`** inside **`FUN_004f26e0`**
    (`4f2dc2 add %eax,(%ecx)` with ecx = the energy address): the base production/rush
    step that reads `energy/10` and `energy/50`. **This never passes through the ledger.**
  - a final whole-faction write `eip=0x506d31 val=905` (`4f506d2b mov %edx,0x94d650(%eax)`,
    eax = `0x82f0` = p4's faction offset) — the end-of-round energy recomputation.
  - **p4's ledger stayed 0 the entire round**, so M46's "AI gaps = ledger debits" is
    **not** supported for an idle AI round: the gap is per-base direct spend
    (`0x4f26e0`) plus the final recomputation (`0x506d2b`). Ledger activity needs a
    player that researches/gifts/terraforms *in that same round*.
* **Operational blockers found and mapped (H, cost most of this session).** Panes that
  block input yet satisfy `classify()=="hud"` because the HUD is visible behind them:
  | pane | text | dismiss |
  |---|---|---|
  | advisor advisory | "PLANETARY ECOLOGIST / Mindworm boil spotted near X!" | `Return` |
  | advisor story page ("Book of Planet") | long narrative body y 180-420 | click **(400,470)** |
  | council convenes page | "PROTOCOL DIRECTOR … convenes the Planetary Council / Agenda:" | `Return` |
  | council ballot | "PROPOSAL … YEA: n NAY: n / ABSTAIN" | click **ABSTAIN** word centre |
  | council result | "MEASURE FAILS / PASSES" | `Return` |
  | faction-info table | "Tech:/Mil:/Pop:/Wealth:/Territory:/Overall:" | click **(400,580)** |
  Servicing rule: if `hud` + TURN COMPLETE visible but the year does not move after a
  click, press `Return` once; if still stuck, click the pane's bottom-centre. The
  old runners had no branch for any of these — that, not the game, is why m46a-d and
  the first two M47 attempts sat still for minutes while `cur` stayed 0 or 4.
* **Harness (H).** `scripts/m47_watch.gdb` (7e+ledger), `m47_watch2.gdb` (minerals+
  7c-window+ledger), `m47_watch3.gdb` (energy+ledger+7e), `m47_watch4.gdb` (p4),
  `m47_watch_year.gdb` (positive control); `scripts/m47_drive.py` =
  end-the-turn driver with the pane rules above (v2 added council/ballot/advisory
  branches). All read-only: TracerPid asserted 0 before pokes, watches armed after,
  `kill -INT gdb` + `kill -CONT` in every cleanup path.
* **Answers.** (1) Income = `Σ base+0xfc` added in `0x4f5a70`; upkeep = per-item
  `0x4f47f0` debits; both reproduce 19 → 21 → 20 → 19 exactly. (2) There is no
  `base+0x7e`; it is `base+0xfc`. (3) Ledger writers still open (action-time).
  (4) AI energy moves by per-base direct spend in `0x4f26e0` and a final recompute at
  `0x506d2b`, not by the ledger.
