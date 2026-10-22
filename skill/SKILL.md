---
name: smac-cvr-format
description: "Use for SMAC .cvr Caviar voxel decode/render or SMAC RE."
---

# SMAC .cvr = Caviar voxel models

Sid Meier's Alpha Centauri (1999) `terran.exe` + `programs/*.cvr` live in
`~/reverse/smac/` (durable). Full writeup: `~/reverse/smac/FINDINGS.md`.
**Versioned at `github.com/wronglebowsk/smac-re` (private)**; a copy of this skill is tracked
in-repo under `skill/` — after editing the skill, refresh it there and push. Game binaries,
`programs/`, `smac.iso`, `glsmac/` and regenerable Ghidra/FLIC output are gitignored: never
`git add -f` them.
Decoder + iso renderer: `~/reverse/smac/cvr_decode.py` (validates 113/113).
Master plan / exit gates (G1–G4) / phase list: **`~/reverse/smac/ROADMAP.md`** — read it before picking
a milestone. Phase 0 = harness + state reader + full Ghidra export + coverage ledger; do it before more
RE. Five spines (boot, solo turn, unit orders/combat, research/tech, save/load) drive Phases 1–2.

```bash
cd ~/reverse/smac
python3 cvr_decode.py "programs/*.cvr" "programs/*.CVR"   # validate corpus
python3 cvr_decode.py --list Apsid.cvr                    # voxel/frame listing
python3 cvr_decode.py --render programs/Drop.cvr          # -> Drop.render.png in cwd
```

## Git workflow (2026-10-22)

Repo `github.com/wronglebowsk/smac-re` (private). One milestone per branch, landed as one PR:

```bash
python3 scripts/milestone.py brief     # state, open PRs (with CI verdict), queued options
python3 scripts/milestone.py start M51a
python3 scripts/gate.py --base origin/main   # must be GREEN
python3 scripts/milestone.py submit     # commit, push, open PR (refuses red gate)
python3 scripts/milestone.py merge <n>  # refuses anything but GREEN
```

**Context discipline (262k tokens ≈ 1.05M chars).** Never read a whole `evidence/*.log`:
`python3 scripts/evidence.py show <file>:<line>` prints the cited window, `evidence.py digest
<file>` writes a ~2KB summary to `evidence/digests/`. `evidence.py budget` reports what each doc
costs in context (target: always-loaded ≤6%). `SESSION_NOTES.md` is rotated by
`scripts/session_rotate.py --apply` once it passes 110k chars; `evidence.py prune` removes
uncited screenshots (git keeps history, `.prune_log.jsonl` records them). Policy:
`~/reverse/smac/docs/EVIDENCE.md`.

**Semantic search** (`docs/SEARCH.md`): `python3 scripts/index.py search "<question>"`
returns `file:line` / addresses for notes and named functions; `merge` rebuilds it
(incremental ~1 s, cold ~35 s) and is fail-soft when the embedding endpoint on
192.168.1.213:8000 is down. A hit is a lead, never evidence.

A session that finds an open PR lands it instead of starting new work. Branch protection is
unavailable (GitHub Pro needed for private repos), so `merge` is the enforcement point — never
merge by hand in the web UI without a green `gate` check. After editing this live skill, copy it
to `~/reverse/smac/skill/` and commit: the gate fails on drift. Protocol detail:
`~/reverse/smac/AGENTS.md` and `docs/WORKFLOW.md`.

## Session discipline (this project is context-heavy)

Paul wants SMAC RE broken into **small pieces**: complete ONE milestone, write it to a
file, append one dated line to `~/reverse/smac/SESSION_NOTES.md`, then STOP — ending
after a single milestone is a success, not a shortfall.

Exception: when he says **"keep going until you finish <chapter>"**, that overrides the
stop-after-one rule. Work through that chapter's milestones, writing the doc + evidence
after each, and report once at the end — including what is still open. Do not relabel a
partial result as done to make the chapter look finished (see `MILESTONES.md` F2).

When a session turns heavy he asks for a **paste-ready resume prompt** for the next one.
Write it as a self-contained block, not a chat summary: first actions (skill_view + which
files to read), current footing (what is proven, do not re-derive), in-flight work with the
exact verify/rerun command, ONE-milestone options, the operational kit (launch command,
preflight, coordinates/OCR rules), and the report style. It must work for an agent that has
none of this conversation. Keep every tool result small:
grep the **`ghidra_out/` corpus** or the saved `*.pseudocode.txt` / `*.json` dumps in
`~/reverse/smac/` instead of re-dumping; page Ghidra facets in small slices; reuse saved
screenshots and take a new one only after a real state change.

## Code atlas — read this before opening Ghidra

Every function is already decompiled on disk: `ghidra_out/index.csv` (one row per
function: addr, name, size, insns, callers, callees, string refs) plus 42
`ghidra_out/shard_NNN.c` files, 250 functions each, bodies delimited by
`// ==== NAME @ 0xADDR size=N`. Use it instead of an import+decompile session.

```bash
cd ~/reverse/smac
python3 scripts/fn.py 0x51e700            # decompiled C for one function
python3 scripts/fn.py --grep 'turn'       # find functions by name
python3 scripts/fn.py 0x51e700 --max 60   # top of a big function
python3 scripts/coverage.py               # index.csv -> COVERAGE.md (hubs, monsters, read-next)
python3 scripts/parse_alpha.py            # programs/alpha.txt -> data/alpha.json + ALPHA_RULES.md
```

- **Filter compiler helpers before ranking anything by in-degree.** CRT stubs
  (`__security_check_cookie`, `_ftol2`, …) have 300–2000 callers and a few hundred bytes and
  top every raw caller ranking; `coverage.py` excludes `callers≥300 & size<400` and lists them
  separately. Ghidra's function count also runs ~2× the real body count because of `Unwind@…`
  pseudo-functions (most are <16 B).
- **Naming a function from the corpus:** read the shape first (params, globals touched, which
  fields it writes — `this+0x18`/`+0x1c` as sizes usually means layout/drawing), then follow
  ONE callee to classify the primitive (a callee that saves/restores a graphics global around a
  rect call makes the caller a drawing routine). Ported string literals are the fast path when
  they exist (`grep -oE '"[^"]{4,40}"'` on the body); many hub functions have none, so field
  offsets are the evidence. Record each name with the offsets that justify it in `NAMED.md` so a
  later session can falsify it in one command.
- **Clean 32-bit disassembly without attaching (M49a recipe)**: `gdb -batch -nx -q -ex "set
  architecture i386" -ex "set disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni
  0xADDR"` — gdb maps the PE image (file offset = VA − 0x400000), read-only, TracerPid stays 0.
  objdump also works (`-b binary -m i386:x86-64 -D --adjust-vma=0x400000 --start-address=...`) but
  64-bit decoding MISALIGINS on SEH blocks (garbage/movabs in SEH-heavy regions like the
  0x4efxxx pipeline) — use the gdb recipe for register-level truth; Ghidra lumps edi/esi away.
- Rebuild recipe, pitfalls and export stats: `references/ghidra-batch-export.md`.
- What the install ships (rules text, map format, graphics containers) and what to parse vs
  what to RE: `references/data-formats.md`.

## terran.exe PE layout (verified 2026-10-20 via section table + byte reads)

Image base 0x400000. Sections (RVA): `.text` 0x1000 + vsize 0x26f3f4 ⇒ VA **0x401000–0x671000 with
raw bytes present** (`55 8b ec` prologues verified at 0x520e70, 0x51e700, 0x5d0c33 WNDPROC, 0x62ad73
FLIC, 0x6309aa DP-init); `.data` RVA 0x289000 vsize 0x316284 but **rawsize only 0x20000** ⇒ data above
VA ≈0x6a9000 (`DAT_0091f6c4`, `DAT_00985b10`, `DAT_0099d020`, …) is uninitialized/BSS at runtime and has
**no bytes in the file**; then unnamed/UVA_DATA/_SELFMOD/.rsrc/.reloc, last section ends RVA 0x5e4000
(VA 0x9e4000).

Consequences — this **corrects the earlier "self-modifying, analyzed image ≠ file image" note, which
mixed RVA with VA**: (1) **all game CODE is in the file**; Ghidra's decompile of any `FUN_` (including
0x5dxxxx–0x66xxxx) is authoritative, and runtime breakpoints at those VAs fire (M7/M8 proved it); (2)
only *data* reads above ≈0x6a9000 need a runtime snapshot (`gdb -batch -ex 'dump binary memory …'`);
(3) `_SELFMOD` is a 0x415d-byte section — a small patch area, not a whole-image unpacker, so there is no
"import of the wrong image" problem.

## Map + save container formats (verified 2026-10-20 — see MAP_FORMAT.md / SAVE_FORMAT.md)

`.MP` map — `15 + 2724 + W*H*22 + trailer == file size`, checked on both shipped maps:
```
0        15 B   b"TERRANMAP\0" 0x1A u32 version(=5)
15     2724 B   header struct: u32 width, u32 height, ... (word 5 = land cells = W*H/2)
2739    W*H*22  raw cell records, row-major (no XOR)
+      var      trailer, starts b"????????" (128 B @80x80, 338 B @128x128)
```
planet.MP 80x80 143,667 B; planetx.MP 128x128 363,525 B. Parser `scripts/decode_map.py`.

`.SAV` save — `b"TERRAN\0" 0x1A u32 version(=86)`, 796 B header, mission year u16 at **+0x54**;
then sections read in a fixed order (see SAVE_FORMAT.md). Section *sizes* come from header counts
and shrink as the game progresses, so arbitrary saves can't be split yet.

**`FUN_00597a70` is the save/scenario block loader, not the map loader** — an earlier note here
claimed otherwise. The map grid is read raw by `FUN_00582260`.

`.SAV` section sizes (from the `push` sites in `FUN_00596850`): 796, 67,040, 11,488, 16,000, 3,584,
26,624, 4,096, 256, 152, 10,144 are immediates; three are computed — one raw count (`DAT_00927538`),
one **52 B/record** (`edx` records), one **304 B/record** (`DAT_00985af4` records). Two are skipped
outright under version/count conditions, so the section list is conditional.
`.SAV` is fully splittable from the file alone — `scripts/decode_save.py --sections` sums to the byte.
Key facts: u32 **own player at file offset 808**; a **u32 count prefix immediately before** one
variable section; the other two variable sections are `n × 52 B` and `m × 304 B` records, split by
solving `52n + 304m = region` and choosing on zeros-fraction (304 B records ~80% zero, 52 B ~40%).
Caller-scoped gdb condition that makes small reads loggable without flooding:
`break *0x64cc00 if *(void**)$esp >= 0x596850 && *(void**)$esp <= 0x597a6b`.
Anchors that pin a save's layout byte-exact (verified on two saves of different ages): map dims
`50 00 00 00 50 00 00 00` at **79,372** and `????????` at **222,896**; gap 143,524 = 2,724 + 140,800.
`scripts/decode_save.py --anchors` checks it.
**Pitfall:** never validate an offset by "fraction of identical bytes" — these files are mostly
zeros, so the match rate is flat across wrong offsets. Use a unique content signature instead.

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
- Unconditional breakpoints here fire **34,000+ times** (the game reads 1-2 bytes constantly) and
  slow it to a crawl; the `>= 64` condition is what makes the run usable.
- The caller address maps each read to its function, so the section order falls out in one run.
- Then close the arithmetic against the file size: if `sum(reads) + known_prefix == filesize`, the
  layout is complete. That is the check that distinguishes a real format from a guess.

## Format core (verified; details in FINDINGS.md)

- TLV chunks `u32 LE tag + u32 LE size incl. header`; outer tag `0x00525643`
  ("CVR\0"), size == file size. Children: 0x01000000 version float (10.0/10.1 —
  NOT a scale), 0x02000000 .MAX scene name, 0x03000000 palette group
  (0x01010000 name, 0x01020000 palette data 6914 B = u8 first + u8 last +
  256×RGB24 + 24×256 shade table, 0x01030000 material 12292 B = 4-byte header +
  24×256 u16 R5G5B5), 0x04000000 scene group (0x4010000 name, 0x4020000 object
  count, 0x4030000 frame count, 0x4040000 per object).
- Object: 0x4040100 name, 0x4040200→0x4040201 VOXEL blob, 0x4040300 animation
  (0x4040301 frame flags 1B/frame, 0x4040302 float32 locations **Z,X,Y**,
  0x4040303 3×3 float32 matrices) — animation-only files exist (Asas.cvr).
- VOXEL blob: VOXEL_HEADER 42 B (flags, size, units-per-pixel float, next, end,
  int16 ZXY scale/position/rotation-center, count). flags&1 = header chain at
  h+next; flags&2 = JUMP_HEADERs (32/36 B, run starts at position+offset).
  Voxels = 3 B: (dir<<3|normal_hi), normal_lo, color index; dir = 5-bit delta
  over 27 steps, 0x1A STOP (STOP-coded last voxel is real); normal = 11-bit
  angle code `((dir&7)<<8|lo)+88`, a1=88−n%89, a2=n/89 → unit vector.
  Regions end with 5 zero pad bytes. Count quirk: single-header jumps
  Σjc=count+groups, multi-header jumps Σjc=count.
- Chunk parse addresses in terran.exe: loader 0x614acb, top loop 0x6446e0,
  per-object 0x644f80, blob stored opaquely by 0x645170. Voxel semantics are
  wiki (alphacentauri2.info/wiki/Caviar) + corpus verified, not exe-verified.

## Multiplayer netcode (mapped — details in FINDINGS.md)

- Internal netcode codename **"jackal"** (debug strings `jackal` +
  `NET_SENDTIMEDOUT`, title "Message from the Net Underworld").
- DirectPlay via COM-style init `FUN_006309aa` (GUID {9d460580-a822-11cf-…}
  @0x67bcf0); DP object global **`DAT_0099d020`**, vtable +0x14 GetMessages,
  +0x68 SendData, +0x28 CreatePlayer. DPLAYX IAT slots have zero Ghidra xrefs.
- Packet: 12-B header (u8 DP flags, u32 seq, payload u16 type @+0, sender
  u32 @+2); builder `FUN_00584010` → router `FUN_0052a260` (type&0x4000=
  guaranteed broadcast, &0x8000=directed, 0x2000=server-originated) →
  `Net::send FUN_00635407` (16×0x58 slot table @this+0x150, seq
  this+0xe0, adaptive ack/timeout). Anti-replay gate `FUN_00639787`.
- Receive: thread `FUN_00638d5c` → `FUN_00638ddd` (GetMessages + gate +
  queue `FUN_0063af12` + PostThreadMessage 0x402) → main drains
  `FUN_005262e0` (in-game queues)/`FUN_00526e10` (synch queues 0x80–0x8d)
  via `FUN_0052a720`+`FUN_006361ff` → dispatcher **`FUN_0052bce0`**.
- Diplomatic types 0x2440–0x244e = DOUBLE CROSS/TREATY ON/OFF/SET/AGENDA
  ×3/ENERGY/TRADE MAPS/CEDE/WITHDRAWAL/TECH/LOAN, one wrapper each
  FUN_00530640–0x530c40 (asm-verified). AI hub `FUN_00546800` (34 send
  sites). Turn sync: client LOCK(0x2210)/DONE TURN(0x8301) → server
  EXEC DONE/NEXT TURN via 0x1240/0x1501/0x4301/0x4303.
- File-name traps in ~/reverse/smac: `treaty.pseudocode.txt` = FUN_00546800
  (not 54d5f4); `killfaction.pseudocode.txt` = FUN_0047c0e0 (UI pane);
  FUN_0047e846 has no callers/pointers — KILLFACTION is a voice-clip token,
  not a message type. UPPER_CASE tokens 0x68b000–0x691600 are sound/voice
  clip names, not protocol opcodes.

## Goal (Paul's priority)

Play SMAC **single-player with working AI** on modern hardware **and recreate
the full menus + game UI** (reimplementation target). Multiplayer netcode is
mapped but secondary. UI groundwork: CPane/CWidget pane builders (e.g.
`FUN_00444140`, `FUN_0047c0e0`), PCX v3 art (`programs/*.pcx`/`.flc`), `.sc`
scenario files, voice/sound clip token strings 0x68b000–0x691600, UI widget-name
strings (TOUR1*, SOCTOUR*, DRONETOUR*).

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

## Running under Wine

SMAC reaches a **live, interactive single-player game** under a pure 32-bit Wine
(wine-10.20-staging-tkg-x86) on Xvfb :99 + llvmpipe; the Script.txt UI panes
render and respond to clicks. Launch command, i386 prereqs, xdotool click coords,
the i386-libpulse audio fix, the exe-verified input routing (a map click pans the view and cannot order a move until the pane is in destination mode 9, so drive
units with arrow keys),
Script.txt dialog geometry and the DirectPlay hypothesis are in **`references/wine-runnability.md`**.
- **Clean stale Wine before measuring:** orphaned `winedevice.exe` from dead sessions (ppid = systemd
  --user, same WINEPREFIX) burn ~40% CPU each (load 12 on 4 cores) and make the intro crawl so blind
  clicks mistime — `kill -TERM` them first.
- **Preflight every boot — two silent killers.** `kernel.yama.ptrace_scope` resets to 1 on reboot, which
  breaks BOTH `gdb -p` and `/proc/<pid>/mem` with EACCES: run `sudo sysctl -w kernel.yama.ptrace_scope=0`
  before any measurement (a "ptrace ok" note from an earlier session only holds until the next reboot).
  A reboot also wipes `/tmp`, so write evidence under `~/reverse/smac/evidence/`, never `/tmp`.
- **Locate widgets by TEXT, never by remembered pixels.** Capture with `xwd -root -silent -out f.xwd &&
  ffmpeg -i f.xwd -vf crop=800:600:0:0 -y f.png` (no ImageMagick here), then read it with
  `tesseract --psm 6 tsv` on a **2×** nearest-neighbour upscale and click the OCR box centre
  (2× costs 0.94 s where 3× costs 1.85 s and reads nothing extra; region crops are slower still). Fixed coords
  drift between UI states and blind clicks open ABOUT popups or base screens. Working pair:
  `~/reverse/smac/scripts/smac_state.py` (live memory: mission year `DAT_00985b00`, mode flags
  `DAT_00985dc8`) and `scripts/smac_play.py` (turn servicer); depth in
  `references/wine-headless-harness.md`. Fallback coords (800×600 window at 0,0): TURN COMPLETE (650,410),
  base-naming OK (400,171).
- **`xdotool` keys are dropped unless the window has focus** — call `xdotool windowfocus <win>` first (Xvfb
  has no WM to grant it). Without focus `Return`/`Escape` silently do nothing and every dialog looks
  undismissable, which reads exactly like a game hang.
- **Modal = key sink (M32 mechanism):** while a Script.txt modal is up the pump does not
call the key router at all — every key is silently dropped (looks like dead input). Run
`scripts/smac_probe.py --quiet` and require `screen=hud` before any key sequence; dismiss modals
first (M29 rules: `Return` for DATALINKS/PSI/event pages, one `Escape` for OPERATIONS DIRECTOR).
Advisor panes are TRANSIENT (auto-dismiss 1–2 s, faster than one OCR poll) and while up they
swallow the NEXT input event (echoes as menu code `0x20011`) — a rejected order looks like a
dropped keypress. **Never press a key to dismiss a transient pane:** it is already closing, so
the key lands on whatever replaced it — an `Escape` aimed at a caption pane CANCELS the
picker that opened behind it, and the game reports a plain "declined", which reads as the
option not being offered. Wait for the next pane (poll the tracer log or re-OCR) and answer
that one. gdb attach itself can drop X events: re-press the key after arming.
- **`/proc/<pid>/mem` pokes are ghosts while a tracer (gdb) is attached (M33).** Readbacks
lie: a poke reads back the new value, then shows a different one after attach. Poke only
with TracerPid 0, arm gdb AFTER poking, verify state after `kill -CONT`. M34 reconfirmed:
writes are fully dead under a live tracer (poked sel=46 → setter fired on the cycle's unit
50). Selection globals
(`0x91b5bc`/`0x91b5c4`) are additionally game-owned: the pump revalidates them and reverts
to the cycle's choice within ~1 frame when the poked unit fails the gate — press the key
IMMEDIATELY after the poke (no sleep) or use the game's own select (`FUN_0040c8d0`,
PICKUNIT picker via map click; calibrate clicks via the HUD tile-info panel OCR, not the
48×36 lattice formula). Under a tracer, steer selection only by completing actions
(HOLD-walk, see M34 footing); gdb bp conditions must cast `*(int *)($esp+4)` — bare
`$esp[1]` kills the batch script at the first hit.
- **Stop at a title/menu screen; never click it.** `Escape` there opens `Do you really want to quit?`
  and the next OK exits the game (process vanishes, nothing in the Wine log). Classify
  `SID MEIER'S ALPHA CENTAURI` / `really want to quit?` as a fatal state: save a screenshot and stop.
  Dark/unrecognized frames get ~20 s of grace before a single Escape — cinematics end themselves.
- **OCR targets must be ≥4 characters and region-constrained.** `yes` matches `Moyes:` (the unit
  panel's `Moves:`) and `ok` matches `Prokhor`, so a naive matcher clicks the map forever and the
  dialog looks undismissable. Same for dialog phrases: squash the joined OCR text to `a-z` and require
  the question body (`endtheturn`), never a similarity ratio — difflib fires on title/map text.
- **Click the OK bar ≥1.2 s after selecting a dialog row.** Faster and the confirm applies the
  previous selection ("No, let me move them"), the same question reappears, and it reads as a hang.
- `kill -TERM gdb` (batch) leaves terran.exe stopped (state `T`); `kill -CONT <pid>` revives it.
- **Script confirms queued behind a screen's widgets are UNREACHABLE** (M48d): CONFIRM DISBAND
  opened from the base screen slid behind base-panel chrome — rows/OK landed on chrome hitboxes,
  keys dead (M32), row clicks never moved the highlight: a modal that swallows input but whose own
  OK bar is occluded. Each menu-item click QUEUES another identical confirm; each OK click cancels
  one — a cycling look-alike pane is a draining queue, not a frozen pane. Recovery when trapped:
  relaunch + load autosave (saves at `<game>/saves/auto/Alpha Centauri Autosave N.SAV`, mission
  year u16 @ file 0x54 — read before trusting the slot number; slots rotate in place; zero progress
  lost since last round). `xdotool key BackSpace --repeat N` FAILS on this xdotool — loop it.
  TOUR hint popup (auto-opens on a screen's first view): Continue ≈(325,585); Social Engineering
  screen: OK ≈(240,368) commits, CANCEL does not close.
- **A python driver whose argv contains its run tag matches the bracketed `pkill -f [t]ag_...`
  pattern and SIGINTs ITSELF** at startup (the bracket only protects pkill's own cmdline).
  Kill stale copies with pgrep + os.kill skipping os.getpid() (fixed in `scripts/m49a_drive.py`).
- **COMM OFFICER 3-row variant** ("Yes..."/"No, close the channel."/"Display faction leader
  profile."): the colour row-click (bar_y−25) can select profile → UNIVERSITY INTELLIGENCE FILES
  table with CLOSE/DATALINKS bars at y≈345-360, OUTSIDE the 430-520 OK-bar band; the
  rightmost-bar row+bar cycle drains it but slowly (~8 min / 43 OCR passes once). OCR the row y
  and click it directly instead.
- **Colour-only pane driver works** (m48d_drive.py, 3 rounds 0 OCR 0 stalls): for any flat blue bar
  in y 150-430 click (bar_x, bar_y−25) [option row above] wait 1.3 s then click the bar; single OK
  bars live in the 430-520 band (find_ok_bar); TURN_BTN only when hud_up; tesseract only as a ≥35 s
  stuck fallback. A driver-generated gdb script (baked literal watch addrs from a content-based
  base re-scan + SELFTEST printf block) beats hand-edited scripts across process restarts.
- **A gdb `call` into game code is a last resort, never a first move.** Injecting
  `FUN_004cffa0(unit,x,y)` reached the callee twice (its `unit+4 |= 0x40` appeared in memory) but never
  moved a unit; once, fired **while a modal dialog was up**, it SIGSEGV'd and left the process alive with
  a completely dead UI (every click inert, main thread `R` with climbing `utime`) — recoverable only by
  relaunch + reload. If a breakpoint fires *inside* an injected call, gdb abandons the expression,
  detaches, and the inferior returns to gdb's dummy frame.

## Still open (leads)

Current footing (M39, 2026-10-21): **second terraform mode proven — Road (`r`) issues with
the whole cost block skipped (no picker, no debit; no-pay modes jump `0x4d5496..0x4d5634`)
and completed in 2 executions at elev 6: tile (45,7) mask 0x108002→**0x108006** (road bit
0x4), year 2295 (`scripts/m39_issue.py`, 45-bp concatenated gdb).** Live threshold ladder
(ours + AI) confirms M37's formulas: road 4 at elev-6 vs 2 low-elev; solar 8 vs 16; mine 8;
RemoveFungus 12. **AI terraformers +3/execution vs our +2 — open.** **Key model corrected:
`Tab` = cycle (empty cycle ⇒ ENDOFTURN1), `l` = SENTRY order key** (oops-proof); cycle skips
MP-exhausted units (poke `+40=0` first); menu-pending `0x91b5c4` sticks — poke 0; mid-turn
start (cur==me, panel up, black map ⇒ classify lies) ⇒ go straight to selection. M38 core
(still true): issue cost `0x4cc7b0` = `(|elev−3|+2)²` (9@elev4, 16@elev5, 25@elev6 > our 15
energy; economy-gated); M37 core: execute chain + multi-turn accumulator. Tile (45,7) elev 6
with road; `0x2101` queue still no solo consumer. Open: MagTube remap/TECHFAIL test (`r` on
roaded tile), economy-rate idle run, player↔faction-ID mapping (may explain AI +3),
Space-on-terraform. `~/reverse/smac/` is durable; `NEXT_PROMPT.md` rewritten for session 40. Execution chain: pump `0x50ef60` (solo turn driver) → gate `0x5acc00(unit)`
(actionable ⇔ `0x5ac650(unit,0) > mpused`) → `0x529e70(unit,0)` (solo ⇒ direct call; netplay ⇒
packet `0x2404`) → `0x4d1200(unit)` solo order dispatcher (4..0x17 → `0x4cce50(unit, order−4, 1)`;
0x18/0x19/0x1a → move chain `0x4ce4a0`; 0x1b/0x1c → `0x4ce710`) → terraform engine: `0x5acdb0`
**consume-all** (`mpused := 0x5ac650(unit,0)` — M36's "mpused 3 persists" is re-charged each
turn; `0x51f730(player)` REFRESH zeroes `+40`/`+42` **per player per round in solo** — live —
and decrements the `+16` reserve pool), then `unit+37 += Σ chain work` (2 per Former; 4 if
ability bit0 `0x98ada8[type*52]&1`; chain `+48/+50` same-k members fold into the head) until
`accum ≥ threshold = 2 × terrain_table[order−4].+8` — runtime table **`0x6938f0 + k*32`**:
`+0` mask bits SET / `+4` bits CLEARED / `+8` == alpha `#TERRAIN` field 5 (raise/lower 12, mine
8, sensor 4, mag 3, road 1) / `+18` required tech (59 = EnvEcon ✓); raise ⇒ 24 ⇒ **12 turns at
+2/turn**; NOTYET (`0x4cd33b`) keeps the order; swamp-cancel `0x4cd319`; COMPLETE (`0x4cd35e`):
order+chain cleared, owner `0x582fc0`, mask swap (`+4` clear/`+0` set — road COMPLETE ⇒
`MASKSET mask=0x4` live), `0x5ad400` RAISE / `0x5ad460` LOWER → `0x5ad0a0` SETELEV, then
`0x5b09b0` re-erosion (SETELEV storm) + `0x4738f0(1)` redraw. **Live: the stored raise completed
year 2281 — tile (45,7) elev 4→5 after 12 turns (2270→2281), energy 31 untouched**
(`evidence/m37c2_*`; the 9 went at issue — issue cost `0x4cc7b0` ≠ work cost 12). M36's "mpused
persists" and "executor filters the ordered unit" retracted; the 0x2101 queue = netplay
replication, no solo consumer (reconfirmed). M36 facts that HOLD: tutor-pane latch
`0x4c2be0(0x800)`/`DAT_00985ad4` + blocking `0x48ef40` at `0x4d58c6`; footprint ladder
`0x678e08[height+1]` (5×5 at elev 4, x wraps, off-map skip; `0x4e3b50` border-owner; `0x555030`
pact instant-refuse / treaty-confirm; refusal ⇒ refund `0x4d58dc`/`0x4d59c7`); tech gate
`0x5a7520` = bit test on byte `0x985c1c + tech_id` (table `0x6938e8 + (mode*8+domain)*4`);
tile array base = **pointer at `0x92ae14`**, tile = `*(int*)0x92ae14 + (40*y + x>>1)*0x2c`,
height `+0>>5`, mask `+8`, **2 tiles/record**; `0x5a7520` is the unlock TEST not a picker;
`0x5ab320` = unit reposition; unit class = LOW BYTE of `0x98adb2[type*52]`.
Selection rules hold: HOLDed (order 2) units are not cycle candidates; empty cycle
**auto-ends the turn**; a map click selects a unit **and** sets orders mode `0x91b5b8=1`;
`Tab` re-opens CUSTOMIZE mid-game. UI: **ENDOFTURN1** pane → **Return** (never Escape); Escape
on a bare HUD opens **REALLYQUIT** (oops row y≈260, OK ≈307) — `answer_confirm` CANNOT service
it (`find_yes_row` scans y 160–220, defaults to 196 = pane artwork); use
`scripts/m37_recover.py` (oops row then OK +47 px). Harnesses: `scripts/m37_exec41.gdb` (11 bps:
REFRESH/ORDEREXEC/TERRAFEXEC/CHECK/NOTYET/CANCEL/COMPLETE/RAISE/LOWER/SETELEV/MASKSET) +
`scripts/m37_exec41.py` (multi-round completion runner — **must click TURN COMPLETE every round**
on a bare HUD, else stalls; snapshots `+37`/elev; REALLYQUIT special-case),
`scripts/m37_recover.py`, plus the M35/M36 set (`m36_store.gdb`/`m36_dismiss.py`,
`m36_exec.gdb`/`m36_exec.py`, `m35_pay.gdb`/`m35_paypicker.py`, `m35_gate.py`,
`m33_scan.py`/`m33_state.py`); **M38: `scripts/m38_issue.gdb` (34 bps, full issue chain incl.
PACTCHK/REFUND/DIPLO/EPILOGUE) + `scripts/m38_issue.py`** — selection recipe (poke `+40=255`
on other own order-0 units → `Escape` → pump auto-selects the Former), `]`, pane servicing,
`COST 16 → DEBIT 31→15 → STORE 0x14 → BCAST` live; elev-5 footprint = **49 tiles 7×7** (81 =
elev-6's 9×9), diplomacy branch armed **silent** (no foreign tiles); completion `m38run2` →
`SETELEV new=6` year 2293, re-erosion lifted 8 neighbours 4→5; energy 15, income ≈ upkeep ≈
+0/turn ⇒ next terraform (25) economy-gated. Next (M39): cheap-mode completion sweep (road
k=5 threshold 2 ⇒ **1 turn**; check `table[k].+18` tech gates via `scripts/m35_gate.py`),
economy-rate idle run, player↔faction-ID mapping (base+4 faction IDs {1,2,4,5,6,7} vs players
{0..7}), `Space` on a stored terraform (`0x4d1e90` routes to the MOVE chain — probably
move-only, untested). Depth:
`references/terraforming-order-path.md`. **M39 (live, 2026-10-21): Road = second mode proven**
(`scripts/m39_issue.py`; gdb = m38_issue.gdb + m37_exec41.gdb concatenated, 45 bps): `r` →
`TERRAF mode=0x5 → TECHCHK 1 → cost block FULLY skipped (PAYPATH/COST/picker/SKIPPAY silent)
→ STORE 0x09 → BCAST`, no DEBIT; exec 1 `CHECK 2/4 → NOTYET`, exec 2 `CHECK 4/4 → COMPLETE
x=45 y=7 mode=5` — mask 0x108002→**0x108006** (road bit), elev untouched (mode 5 = mask swap
only), year 2295. Live thresholds confirm M37's adjustments (road 4 vs 2 by elevation; solar
8 vs 16; mine 8; RemoveFungus 12); **AI terraformers +3/turn vs our +2 (open)**. Keys:
**`Tab` = cycle, `l` = SENTRY**; cycle skips MP-exhausted units (poke `+40=0`); menu-pend
`0x91b5c4` poke 0; mid-turn start ⇒ act on `cur==me` (classify lies on black maps). Next
(M40 DONE, live 2026-10-22): MagTube remap + first TECHFAIL — `r` on a roaded tile: TERRAF 0x5
→ remap rewrites the mode arg inside `0x4d44d0` (TECHCHK sees 0x6; gated on cap table `0x6938e8`
idx `mode*8+tile-seafloor`, MagTube land 18/sea −2 ⇒ land-only) → gate 0 → TECHFAIL `0x4d486e` →
**mode-specific advisory dispatch 6→HASROAD / 1→HASFARM / else NOTUNTILTECH** (HASROAD text
substitutes $TECH0 → tech 18 "Monopole Magnets" live via `0x5a69f0` (tech names at
`0x92fdb4+id*44`) + `0x626634` slot table `0x99a01c`; scratch buffers `0x997120`/`0x99a01c` are
NOT state); rejected cleanly — the runner's STORE timeout IS the expected reject terminal state.
Cap table is the gate source (terrain `+18` garbage 527 for cheap modes); MagTube table k=6:
maskSET 0x8, work 3. **As of M41 (live, 2026-10-22): MagTube third mode proven end-to-end**
(`evidence/m41a_*`, `m41b_*`): unlock poke byte `0x985c1c+18 |= 0x08` (TracerPid 0 first) → `r` on
the roaded (45,7) → `TECHCHK mode=0x6 unlocked=1` (gate-pass path = NO advisory, straight to
AFTERLATCH/STORE) → **STORE 0x0a — the STORE writes the REWRITTEN mode** → 4 execs 2295→2298
(`CHECK 2/8→4/8→6/8→8/8`) → `COMPLETE mode=6` → tile mask **0x108006→0x10800e** (magtube bit
0x8), elev untouched (mask swap only), energy 15 flat. **Threshold @ elev 6 = 8 = 2×3+2 ⇒ case-5/6
elev bump is +2 FLAT, not ×2** (road 2→4 fits the same rule). AI side-obs: base 2×`+8` holds
(condenser 24, raise 24, bunker 10, sensor 8, RemoveFungus 12); AI accum +3 on 7 formers, **+2 on
one (idx 51) — not universal**. MASKSET print cap (300) hit for real in m41b (299 prints, our swap
silent — mem readback authoritative). Both runners ran unmodified on the new mode. Left running:
pid 914079, year 2298, our turn (cur=3, ENDOFTURN1 pane likely up — Return), Former idx 36 @
(45,7) order 0 work37 0 mpused 3, tile 0x10800e elev 6, energy 15, **tech 18 left unlocked for
player 3** (byte 0x08; undo = clear bit 3), tech 60 byte 0x16 (players 1/2/4 only — Condenser
still gated for us). M42–M44 (same session, 2026-10-22): generic NOTUNTILTECH proven live (`n` →
TECHFAIL → ADVISOR/PANE NOTUNTILTECH; $TECH0 + $TERRAFORMTYPE6 slots closed; tech record +0 =
display-name POINTER, +4 = short token; op-name table `0x94d2f8` = 14 × (land, sea, key-char STRING)
stride 12 — k=8 is **Airbase**, k=9 Sensor Array). M43: base `+4`/`+5` IS the owner player index
(identity, 167/167) — **we own ZERO bases**, all our units `home_base=0xffff`, ~45 orphan-border
tiles; `0x4e3700` works fine (Ghidra short* math), inert for us. M44 (economy idle run,
`scripts/m44_idle.py` v2 + `scripts/m44_probe.py`, evidence `m44d_*`): **our income is 0 AND upkeep is
never charged to energy — energy flat 15 over 12 rounds (2304→2315)**, the HUD agrees (Gross
Income/Total Costs/NET INCOME all 0/turn) ⇒ the 25-cost elev-6 raise is unpayable until a base
exists; AI rates/round Δenergy {1:-1.4 2:-1.3 4:+10.9 5:-0.5 6:+5.3 7:-0.9}, Δminerals {1:+2.3
2:+8.3 4:-11.2 5:-1.9 6:+31.2 7:+1.1} (player 4's near-exact anti-correlation ⇒ unspent base minerals
→ energy ≈1:1, O); **our units 5→2 in that window — the Formers unit (type 1, cls 9) is DEAD**,
survivors = Colony Pod (type 0) @ (45,11) + Laser Squad (type 195) @ (43,11). Four reusable
corrections: (1) **Council/PROPOSAL panes block the pump and their bottom-centre blue OK bar is
unreadable to tesseract** — find it BY COLOUR (band x 240-560, y 430-520, lowest contiguous blue bar
≥8 rows; calibrated rows 488-507 × 268-532, rgb (103,91,181)); the HUD chrome's 1-px blue line at
y 526 exists in EVERY frame, so cap the band at 520. (2) **runtime tile record == the map file's two
22-B cells (2n,y)++(2n+1,y)** byte-exact, and every accessor (`0x582ed0`, `0x5831a0`, elev readers)
is **parity-blind** (`40*y + x>>1`, +0 elev / +8 mask) ⇒ the tile pair shares elevation + the +8 mask;
a second mask-shaped dword at **+0x18** is open. (3) tile **mask bit 0x2 = a unit standing on the
record** (3193/3200, 0 false negatives); full vocabulary from table × op names (farm 0x8000, enricher
0x80000, mine 0x10, solar 0x40, forest 0x200000, road 0x4, magtube 0x8, bunker 0x800, airbase 0x40000,
sensor 0x80000000, fungus 0x20, condenser 0x400000, echelon 0x8000000). (4) **unit type-record base
is 0x98ad88** (name +0[34], ability +32 = 0x98ada8, domain +36 = 0x98adac, class +42 = 0x98adb2) — the
standing ABSOLUTE addresses are right, but treating 0x98ada8 as the record base pairs each class byte
with the NEXT record's name; type 0 Colony Pod (cls 8), 1 Formers (cls 9), 193 Scout Rover, 195 Laser
Squad; ≥196 runtime types vs 15 alpha `#UNITS` rows. Also **autosaves rotate over all 8 slots**
(30/20/10 every 10 y, then 5/4/3/2/1 yearly) — the "slot 2 = 2198" load note is stale; read the u16 at
file `0x54`. M45 (session 42, 2026-10-22, `scripts/m45_base.py` + `scripts/m45_base.gdb`, evidence
`m45a_*`/`m45c_idle.json`/`m45f_idle.json`): **FIRST BASE FOUNDED** — `b` on the Colony Pod (cls 8)
@ (45,11): `SETTER 0x4d1280` → `BORDERRET -1` → `LIMITRET 12` → `PANE NEWBASE` → `0x4cca50` →
`CREATERET base=73` → `PANE BASEFOUNDED`; n_bases 73→74, our base pop 5→4 (nutrient shortfall =
attrition, not eco-damage), name auto-generated, kit HQ/RecyclingTank/RecreationCommons/EnergyBank/
NetworkNode. Five reusable rules: (1) **Ghidra callee names `FUN_<addr>` are VERBATIM** —
`FUN_005abb40` is 0x5abb40, not 0x45abb40; a +0x400000-shifted bp still ARMS (memory is mapped) and
just never fires, so a silent missing trace line means check the address. (2) **can-act `0x5acc00`
refuses when `unit+4 & 0x4200 == 0` AND order byte `+17` ∈ {1,2,3}** ⇒ poke `+17 = 0` to make a Hold
unit key-able; owner check is `unit+14 == 0x91b5b4`, MP is `0x5ac650(unit) − unit+40`. (3) the
**NEWBASE name pane accepts the generated default with a plain Return** (no typing/click). (4) after
founding the game opens the **BASE screen** (classify kind `base`; RENAMEd/OK row y≈365, outside the
430-520 OK-bar band) — `service_pane` needs a `kind=="base"` → Escape branch (patched; without it a
run spins forever). (5) **`objdump` cannot read this PE** ("invalid bfd target") — pin call sites
with a raw E8 rel32 scan, `.text` file offset = VA − 0x400000 (identity mapping; the header's
ImageBase field is a bogus 0x270000). Also: **mask1(+8) bit 0x1000 = "inside a base's claimed
border"** (12-31 pairs per base, hex radius ≈3, pop-independent, 74/74 bases, ocean included) while
the tile owner NIBBLE is a different layer — `0x4e3b50` returned −1 for our nibble-3 tile, i.e. the
~45 inherited orphan nibble-3 tiles are NOT borders; mask bit 0x1 = base-on-pair (74/74, it is what
`0x4e34f0` requires); base `+56` is the constant `0x00dfbe41` (M44's "copied from home base" was
wrong). Economy after founding (16 snapshots 2315→2329): energy 15 ×5 → **19 once at 2320** → flat
19 (0.0/round over the last 9), ≈+0.8/round vs the base screen's own +003 energy/+007 minerals/−001
nutrients; units 1→6 (produced units carry `unit+46` = home base idx ✓) while
energy stays flat ⇒ **unit upkeep never debits faction energy**; a pod base does not make us solvent.
Open: HUD Gross Income/Total Costs/NET INCOME never OCR-able when dialogs/unit panel are up — find
the panel's source fields in memory; and M44's "autosave record == two 22-B cells at +2724" did NOT
reproduce (3200/3200 differ, located pairs fit no stride model) — save-map layout unverified.
M46 (session 43, 2026-10-22): **ECONOMY DECOMPOSED** — upkeep pipeline `0x521070` → `0x5208f0(p)`
(tail `energy -= faction+4; faction+4 = 0` ⇒ **faction `int[1]` is a within-round spending ledger**)
→ income core `0x520540` (gifts, per-base `0x4f5a70`, AI stockpile gated `DAT_00985aec > 3`, trait
bonus) → `0x4f5a70` does `energy += base+0x7e` (transient field, reader only in export, writer = O
computed pointer); facility upkeep is charged DIRECTLY by `0x4f47f0` (auto-sells on shortfall). HUD
Gross/Costs/NET are scratch globals recomputed per redraw by `FUN_00445900` (`0x745734 = Σ base+0xfc`,
`0x744f28 = Σ upkeep`, `0x7457dc` net) and the faction pane `0x49fee0` prints them verbatim ⇒ read
the globals, never OCR those rows. Item upkeep table `0x984d48 + item·0x30` (int0 upkeep, int1 tech),
runtime item = alpha `#FACILITIES` idx + 1, bitmap base+0x8c; the disabled list lives in the player
trait record `0x927a7c + p·0x59c` (+0x20 count/+0x24 types/+0x44 items) and ours zeroes Network Node
(3 − 1 = 2 ✓). Faction records are **2095 ints**, not 2111 (int[2095] = next player's energy). Our
net 0 ⇒ 25 energy never disposable; Corner Market is surplus-gated (energy > max(Σ rivals,1000)).
Blocker that cost 4 runs: the **OPERATIONS DIRECTOR end-turn pane** (Cancel default, OK bar y 215-350,
outside the 430-520 band) — click `(cx,cy+24)` then `(cx,cy+49)` from the OCR Cancel centre; HUD test
is `hud_up` (orange pixels in 600,395,800,425 > 300), not `classify()`. `pkill -f <pat>` matches the
killing shell's own cmdline — bracket the pattern.
M47 (session 44, 2026-10-22): **ENERGY WRITE PROVENANCE** — hw watchpoints DO work here; the
positive control is the year store `0x51f554` in `FUN_0051f320`. Income = `energy += base+0xfc` at
`0x4f5c8c` in `FUN_004f5a70`; facility upkeep = `0x4f4952` in `FUN_004f47f0` (`energy -= cost`, then
`faction+0xe0 += cost`); AI per-base spend = `0x4f2dc2` in `FUN_004f26e0` (direct `add %eax,(%ecx)`,
bypasses the ledger) + a final recompute at `0x506d2b`. **`base+0x7e` does not exist** — Ghidra's
`*(int *)(DAT_008f0d60 + 0x7e)` is typed `short *`, so `+0x7e` = `0xfc` bytes; nothing ever wrote
that region (2 armed rounds, 0 hits). `faction+4` ledger = ACTION-time writers (zero writes over an
idle round for us and for Morgan) — still open. Two hard-won operational rules: (1) six panes block
input while `classify()` still says `hud` — advisor advisory ("Mindworm boil spotted") → Return,
story page / "Book of Planet" → click (400,470), council convenes page → Return, ballot → click the
ABSTAIN word, "MEASURE FAILS" → Return, faction-info table (Tech:/Population:/… ) → click (400,580);
(2) gdb's stdout to a file is block-buffered — never conclude "no writes" from an empty log while gdb
is attached; `kill -INT` first, and remember a watchpoint's `$eip` sits just PAST the store.
Next (M48): mineral economy (queue a build, watch `base+0x40`); ledger writers on a spending round;
`faction+0x1b8` + research points; player↔faction NAME mapping; the 2320 +4 credit.
**M48d (session 45-46, `scripts/m48d_drive.py`, evidence `m48d2_*`): MINERAL ECONOMY TRACED** —
storage `base+0x40` grows `+= d0` per round UNCLAMPED between completions (AI stockpiles 111→121);
at EVERY production completion (unit or facility, `0x4efe41→SPENDA 0x4efed8 store 0x4efee0`) storage
is then pinned to `max(0, min(d0, cap))` (store `0x4eff23`, gate CLAMP1 `0x4eff02` =
`(1<<owner)&mask` event test) — the stockpile is destroyed to one round's income at completion.
Scout Patrol cost 10; pop-growth units go through the SAME completion path and need storage ≥ cost
(26 years of storage 0 ⇒ pop grew, unit never spawned); NOSUPPORT disband fires while `d0<0`,
one unit/round, stable at d0=0; `d0=base+0xd0` recomputed every round at `0x4e955d` (pokes die);
`+0x50` carries transient scratch mid-visit; PROGDIV `0x4efd49`/QDRAIN `0x4f1e3f` never fire in
solo; sweep = 75 visits ours LAST, can end early on the year store (open: truncations observed at
21/28/28 visits — the last-visited base, ours, can skip a whole round). Pane printer
`0x483470` = advisories only (Script confirms don't route through it).

**M49a (session 47) CORRECTS M48d's cost story**: at every completion SPENDA `storage −= edi`
where edi = the base's SWEEP-ENTRY INDEX (0x520540 `push ebx` stack arg → 0x4f5a70 `edi:=index`
0x4f5aa9 → the pipeline never writes edi on the pop-growth path), NOT a unit cost — "Scout
Patrol cost 10" retracted (10 = our base index); esi at COMPLET is path residue (pop-growth:
(1<<owner)&mask via 0x4e40a0/0x48ee00; facility: type-record scratch); pop at COMPLET is always
the pre-completion value. **M50a (session 48) closes the mineral-cost question**: `0x4f26e0` is
the mineral↔energy CONVERSION/INCOME step, not a cost, and holds the THIRD storage writer —
store `0x4f2d7d storage += ((energy_pool/esi)·45)/trait` (CREDIT, live deltas +0…+12; scales
with faction energy pool `0x94d650+p·0x20bc`). It early-returns for our base via gate 0x4f2705
(event-owner ∧ `~(base+0x38)` bits 0x1a/0x1c; f30=0x805000 bit 0x1c) ⇒ we get no conversion
income. Production is effectively free of mineral costs in solo: only debit is the index quirk
0x4efee0, and 0x4ee410 never touches base+0x40. Current footing: `~/reverse/smac/NEXT_PROMPT.md`
(session 49).

As of M24 the whole order path is **named**
(`~/reverse/smac/turn_driver.md` §M19–M24 + 13 new `NAMED.md` rows): the tile setter `FUN_004d44d0(unit,mode)` (with `FUN_005ab320(unit,x,y)` as unit
reposition only, not a tile writer),
the stack mover `FUN_005a58e0`, the re-stacker `FUN_005a5a80`, the 8-direction step
`FUN_00502c40(unit,dir,parity)` (parity-split delta tables at `0x6784a0/0x6784c4/0x67850c/0x678990`),
the executor `FUN_00502cd0(unit,?,destx,desty)` and dispatcher `FUN_0052bce0` case `0x4402`; plus
**issue-move `FUN_004cffa0(unit,destx,desty)`** → solo (`DAT_00920434 == 0`) `FUN_004cdc70(unit,0,x,y)`,
netplay `FUN_00528930(&unit,4,x,y,0)` + packet `0x2413`; the map click handler
**`FUN_00476580(pixel_x,pixel_y,flag)`** dispatches order code `case 10` → issue-move and its direct
branch writes order `+17 = 0x18` with destination `+20`(x)/`+28`(y) — NOT `+24` — then
`FUN_00584350` (0x2101); the
**selected unit is `DAT_0091b5bc`** (singleton base `0x8f79e0`, cross-checked `+0x23bd4 = 0x91b5b4` =
own player), cursor/destination tiles live in `0x91b5f0`/`0x91b670` (index `0x91b5e8`), and keys go to
`FUN_00512450` (selected unit) or `FUN_00511960` (cursor tile).

**Correction (M28): a plain map click never issues a move.** `FUN_00476580` writes `+17 = 0x18` only when
the map pane's mode is 9 (`[0x8f79e0+0x1ef4c] == &DAT_0091cae4`), which is 0 on the HUD; live clicks
fire `MAPH` and nothing else. Mode 9 is chosen in `FUN_0050a770` as Ctrl held ∧ `0x91b5b8 == 0` ∧
`0x91b6fc == 0`; it stays unreachable under xdotool because `DAT_0068d84c` (active pane index) is −1 —
the pointer never registers as inside a pane even though clicks arrive. That hit-test is the next
cheap test. Clicking a stacked tile still only raises SELECT UNIT TO ACTIVATE.

**As of M25 (session 25): writing the order fields is not the
trigger** — poking `+17 = 0x18, +20 = dest_x, +28 = dest_y` into a unit through `/proc/<pid>/mem`
(writable, no tracer) survived a full turn and a compaction slide, yet the unit never moved; a gdb
`call` to `FUN_004cffa0` reached `FUN_004cdc70` (wrote `unit+4 |= 0x40`) twice and still produced no
move. `maps/planet.MP` field offsets are unresolved
(`references/data-formats.md`); hub functions `0x5f6de9` (writes ~60 fields of a >8 KB object,
then calls a vtable method at `this+0x15f8`) and `0x483470` (SEH frame + 21 KB stack buffer +
UI callees) are still unnamed.

- **Turn cycle: solved as a harness problem (~100 turns unattended; `references/wine-headless-harness.md`).**
  It was never a game hang — every observed stall was a blocking UI element (units-not-moved confirm,
  OPERATIONS DIRECTOR speech, NETFLASH, tech-breakthrough screen, base screen, Secret Project movie) that a
  one-shot click-then-wait loop cannot answer. Chain of netcode findings:
  (`~/reverse/smac/dplay_solo.md`, `turn_stall.md`): (M3) solo opens NO DirectPlay session, so DP shims
  (dgVoodoo2/nGage/glsmac) can't fix anything; (M5) the idle main thread is a normal yielding PeekMessage
  pump, not a clock-spin or deadlock; (M6b/M7/M8) solo never calls the netcode packet builder `FUN_00584010`
  nor dispatcher `FUN_0052bce0`, **nor the MP end-turn machinery** `FUN_00522240` ("Clearing turn semaphore",
  DONE TURN 0x8301) → `FUN_00521ee0` (end-of-turn semaphore wait loop) → `FUN_00527ca0` (its in-loop pump):
  zero hits across 7 completed turns. **Solo's turn advance runs under `FUN_0050f420`/`FUN_0050ef60` →
  `FUN_0051e700`** (hot: 0 hits idle, ~220–560/s while a turn resolves; drives the `DAT_0091f69x` turn
  semaphore directly, no packets). The old "turn stall" = periodic MODAL dialogs and full-screen interruptions (ABOUT RESEARCH, OPERATIONS
  DIRECTOR speech, NETFLASH, tech breakthrough, base screen, Secret Project movie) blocking the TURN
  COMPLETE click while the game idles in its pump. Next: make the driver give unit/base orders
  (Script.txt-driven) so the AI actually plays; decompile `FUN_0051e700` only if the counters it drives
  stop tracking.
- **Diagnosing a Wine game stall (reusable method)**: sample per-thread wait-state via
  `/proc/<pid>/task/<tid>/{stat,syscall,wchan}` (state=R + climbing utime ⇒ busy-loop, not blocked);
  `gdb -batch -p <pid> -ex 'thread apply all bt' -ex 'info proc mappings'` — but **Wine's stack won't
  unwind past ntdll** (bt stops at ~2 frames: `__kernel_vsyscall` → a libc poll/select wrapper), so use
  gdb `info registers eip` sampling as a poor-man's profiler and map a hot terran.exe `$pc` to a Ghidra
  `FUN_` by subtracting terran.exe's runtime base from `info proc mappings`. Breakpoints on
  `GetTickCount`/`QueryPerformanceCounter`/`timeGetTime`/`GetMessage` reveal what the loop polls.
  `WINEDEBUG=+<dll>` trace helps for some DLLs (`+dplayx` works; `+timer` emitted nothing here). Detail:
  `references/wine-runnability.md`, `~/reverse/smac/turn_stall.md`.
- AI decision logic: diplomacy hub `FUN_00546800` (3924 lines) vs UI plumbing;
  psi-meter gate `FUN_004d6fb0`; turn upkeep `FUN_00520e70`; the host-side
  action-exec branch of dispatcher `FUN_0052bce0` (case 0x4404) is the single
  source of truth for action rules — server and solo alike.
- 0x4040400/0x4050000 cvr chunk handlers exist in exe but in no shipped file.
- Caviar voxel rasterizer exe-verification (27-dir table, normal decoder,
  shade-table light levels) still wiki/corpus-level.
