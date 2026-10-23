# SMAC RE — session notes (append one dated line per session; survives context pruning)

> Milestone plan + status board: **`MILESTONES.md`** — read it first, then pick ONE milestone.

- 2026-10-20 (session 6): Game runs + interactive under Wine 10.20-staging-tkg-x86 (Xvfb :99, llvmpipe); audio fixed via `apt install libpulse0:i386`. Input routing mapped (WNDPROC FUN_005d0c33 → FUN_005d1dcf → hit-test FUN_005d711a/FUN_005d6a80; vtable+0x124 drag/scroll eats map clicks). OPEN: turn won't complete via automation (research "Lab 6 turns"/Year 2101/Energy 11 frozen; UI responsive). Hypothesis: turn sync = DirectPlay "jackal" local loopback. Details: UI_MAP.md §Runtime.
- 2026-10-20 (session 7): M1 DONE — single-player DOES use DirectPlay. `FUN_00522850` (startup) calls DP-init `FUN_006309aa` unconditionally; `Net::send FUN_00635407` sends via DP object `DAT_0099d020` (bails if NULL); recv `FUN_00638ddd` same. Turn-freeze consistent with Wine dplayx not pumping the local loopback (unproven → M3). terran.exe is self-modifying: analyzed image (0x5d0000+) lies above packed-file sections (end 0x5e4000), so DAT_ byte-reads from the exe fail. Details: dplay_solo.md. M3 DONE (runtime, WINEDEBUG=+dplayx,+dplay,+loaddll): solo opens NO DirectPlay session and pumps no GetMessages/SendData — only a startup lobby probe ("Application not lobbied"); turn stall is NOT a dplayx pump failure, so DP shims (dgVoodoo2/nGage/glsmac) won't fix it. Redirect M4 to the in-process turn loop / server tick / threading under Wine. Log /tmp/wine_dp.log; shots dp_boot.png, dp_hud.png, dp_afterturn.png. M4 DONE: turn stall is NOT a deadlock/DP — the MAIN game thread busy-loops (top -H ~30% CPU, state R 12/12, utime climbing, mostly user-space with occasional poll/read); all 16 other threads are idle Wine infra; llvmpipe 0% (prior "llvmpipe redraw" CPU attribution was WRONG). Main thread spins waiting on a condition Wine never advances. gdb bt can't unwind past ntdll. Next M5: pin the spin target via gdb $pc sampling + breakpoints on GetTickCount/QueryPerformanceCounter/timeGetTime/GetMessage. See turn_stall.md, /tmp/gdb_bt.txt. M5 DONE (perf 7.0.14, `perf record -t <main-tid>`): main thread is a NORMAL yielding PeekMessage pump (win32u peek_message/get_shared_queue/call_message_hooks + NtYieldExecution + __wine_syscall_dispatcher dominate; game code spread thin, no hot function) — NOT a clock-spin/deadlock/stuck loop. terran.exe runtime base 0x400000 (runtime IP == Ghidra VA). Turn-advance logic simply never fires. Next M6: instrument the turn-advance path (client DONE TURN 0x8301 → dispatcher FUN_0052bce0 case 0x4404) via gdb breakpoint or Wine +winex.win32/+msg trace. perf data /tmp/m5.perf. M6 ATTEMPTED (inconclusive, 2026-10-20): gdb breakpoint on dispatcher FUN_0052bce0 logging *param_1 type (bp validated: "Breakpoint 1 at 0x52bce0"; script /tmp/bp.gdb; dispatcher reads type=*param_1 = ushort at packet+0, param_1=[esp+4]) — but attaching gdb DURING the splash left the game stuck on the title/splash screen (gdb appears to disrupt the intro movie/timers), so no turn was attempted and 0 dispatcher hits is NOT a finding. Fix next session: boot to HUD AND confirm via screenshot, THEN attach gdb, THEN TURN COMPLETE→Yes→OK, then grep log for "T 8301"/"T 4301"/"T 4303"/"T 1501"/"T 2210". Log /tmp/m6_dispatch.log; shots m6_hud/m6_after/m6_b1.png (all title screen). M6b DONE (2026-10-20, confirmed live HUD + gdb bp on FUN_0052bce0): ZERO dispatcher hits across a responsive turn attempt (game ran, Energy 10→11, unit panel populated) ⇒ SOLO BYPASSES the netcode packet dispatcher — consistent with M3; skill's "dispatcher source of truth, solo alike" is likely wrong for solo. Boot pitfall corrected: intro movie is just SLOW under llvmpipe (blind clicks fire too early → looks stuck on title); press Return/Space/Esc to skip intro, then base-naming OK 400,171. Caveat: not yet positive-controlled that 0x52bce0 is the executed solo address. Next M7: control-bp on WNDPROC FUN_005d0c33 (hits on clicks) to validate, then bp solo turn funcs (FUN_00520e70 upkeep / DONE-TURN sender) + instrument year/research counters. Log /tmp/m6b_dispatch.log. M7 DONE (2026-10-20, positive control): control gdb bp on WNDPROC FUN_005d0c33 fired 403× ⇒ gdb breakpoints DO fire on terran.exe unpacked code (base 0x400000, same region as FUN_0052bce0) ⇒ M6b's zero-dispatcher-hits is REAL, not a gdb artifact ⇒ SOLO GENUINELY DOES NOT CALL FUN_0052bce0. Confirms M3. Next M8: bp solo turn funcs (FUN_00520e70 upkeep / DONE-TURN sender) + year/research counters to find the solo turn-advance path and why it stalls. Log /tmp/m7_ctl.log.
- 2026-10-20 (session 9): M8 DONE — 11 auto-continue gdb bps (/tmp/m8b_bp.gdb → /tmp/m8b_hits.log) while playing: **7 turns advanced, Mission Year 2100→2107, Energy 10→17**, so the turn cycle is NOT broken under Wine. ZERO hits on the whole netcode end-turn chain (FUN_00522240 master / FUN_00521ee0 semaphore loop / FUN_00521bc0 / FUN_00527ca0 pump / FUN_00584010 packet builder / FUN_0052bce0 dispatcher / FUN_00520e70 upkeep); **FUN_0051e700 = 47,004 hits, 0 while idle and ~220-560/s during each turn** ⇒ solo advances turns via FUN_0050f420/FUN_0050ef60→FUN_0051e700 (drives the DAT_0091f69x semaphore directly, no packets). The M4-M7 "stall" reproduces as a UI artifact: periodic MODAL dialogs (ABOUT RESEARCH OK≈(400,347), CONFIRM RESEARCH PRIORITIES OK≈(400,270)) block TURN COMPLETE while the game idles in its normal pump. Also: 10 orphaned winedevice.exe (~40% CPU each, load 12/4 cores) from old sessions must be killed or boot crawls; corrected coords TURN COMPLETE (650,410), end-turn "Yes, and the turn." (300,197) OK (400,222); `kill -CONT <pid>` revives terran after killing gdb. Game left live at Year 2107 (pid 3042382). Details: turn_stall.md §M8. **ROADMAP.md added** (retrospective + G1–G4 exit gates + 5 spines + Phase 0 infrastructure: preflight, `/proc/pid/mem` state reader, Script.txt-driven automation, runtime image dump, full Ghidra export, coverage ledger; ~1.9% of ~5,768 functions dumped so far). Next = M9 = roadmap 0.2 (state-reader addresses, game currently live).
- 2026-10-20 (session 10): **M9 DONE — the "turn stall" is solved as a measurement problem, and the game now plays unattended.** (a) Host had rebooted: `/tmp` wiped (all M8 gdb logs/screens gone) and `kernel.yama.ptrace_scope` back to 1, which silently breaks BOTH gdb attach and `/proc/pid/mem` — `sudo sysctl -w kernel.yama.ptrace_scope=0` is now a required preflight step every boot. (b) Wrote `scripts/smac_state.py`: live memory reader, verified addresses — **year `DAT_00985b00`** (2101 at start, +1/turn, matches HUD), year_start 0x92bf68=2100, year_limit 0x92bf6c=2600, turn flags 0x985ae8 (2 mid-end-turn), cur/own player 0x985dcc/0x91b5b4=3 (University), mask 0x985b10=0xff08; **mode_flags `DAT_00985dc8`=0 all run ⇒ bit 0x10 branch in FUN_00522240 never taken in solo (confirms M6b/M8)**; retracted two labels: 0x91f694 is MP-only (0 for 95 solo turns) and 0x985af4 is not a faction count (7→26). (c) `xdotool` keys are dropped unless `windowfocus` is set first — the real reason M8's Return/Escape "did nothing". (d) Wrote `scripts/smac_play.py`: OCR-located widgets + memory-verified turns, servicing the game's interruptions (units-not-moved confirm, OPERATIONS DIRECTOR speeches, NETFLASH, tech-breakthrough screens, base screens, Secret Project movies). **15/15 turns from a cold boot (2101→2116) and 80 turns total (2101→2181) advanced unattended; zero game hangs — every observed stall was a blocking dialog/movie.** Open: Escape-spam can reach the title menu and exit the game (process vanished at 2181), and the driver does not give orders yet. Details: turn_driver.md; traces evidence/trace_*.jsonl, soak3_freshboot.log. Next M10 = roadmap 0.3 (Script.txt-driven unit/base orders) + harden the driver (window-alive check, no Escape on the movie/title class).
- 2026-10-20 (session 11): **Host reconfig + driver speed pass (M9b).** `usermod -aG render,video n100` done, but the iGPU stays unusable: glxinfo on `:99` is llvmpipe even under `sg render` because **Xvfb has no hardware GLX** — real GPU needs Xorg or weston-headless+Xwayland (deferred; buys movie/boot speed only, not turns). Driver: OCR 3×→**2× full frame (1.85 s→0.94 s)**, single pass per decision (region crops were slower: 4 process spawns), in-memory year polling instead of a 2 s sleep ⇒ typical turn **10–16 s → 8–12 s**, 12/12 turns advanced (2101→2112). Three silent bugs fixed: crop args were edges not sizes (ffmpeg clamps silently, coords 2× off); `find(["yes"])` matched the unit panel's `Moves:` OCR'd as **`Moyes:`** (and `ok`⊂`Prokhor`) so the driver clicked the map forever → geometric `find_yes_row()`; OK-bar click must be ≥1.2 s after the row click or it confirms the old "No" selection and the dialog reopens. Boot wizard mapped: Return advances difficulty→planet→random map→ENTER A NAME→start; QUICK START is main-menu only. DESTRUCTIVE: Escape on the title screen → quit dialog → OK exits the game (lost 2 runs); driver now stops on a `title` class and gives dark screens a 20 s grace before one Escape. Game left live at year 2112. Details: turn_driver.md §M9b.

- 2026-10-20 (session 12): **Data layer (M10a) + RE tooling for the batch export.** `DATA_INVENTORY.md` — measured the install (618 files / 47 MB): **pcx 378·20.5 MB, cvr 113·7.7 MB, flc 21·5.9 MB, txt 32·0.65 MB, exe 2·3.7 MB, mp 2·0.48 MB**. Verified rather than assumed: PIL opens `Cursor.pcx` 1024×768 P; ffprobe reads a `.flc` as `flic 105x87`; CVR already 113/113 decoded. ⇒ **G2 was never the hard part**: art is PCX/FLIC, the custom container is done, and the content/rules are plain text. `alpha.txt` is the rules file ("reads the rules of the game from this file"): **45 sections / 650 records** parsed to `data/alpha.json` + `data/alpha_schema.json` by `scripts/parse_alpha.py` (field names recoverable from trailing comments for only 4/45 sections — CHASSIS etc. are bare data, semantics must come from the exe's parser). Section map regenerated into `ALPHA_RULES.md`. `Script.txt` (238 K) = "Dialog box scripts"; `maps/planet.MP` (143 K) is the shipped map, still undecoded; faction defs in `FACTION.TXT`/`UNIV.TXT`/etc. New RE tooling: `scripts/fn.py` (grep/print one function from the shards instead of an REA session) and `scripts/coverage.py` (index.csv → `COVERAGE.md`: hubs, monsters, read-next ranking) — both tested against synthetic shards. Ghidra batch export **DONE: 10,284 functions, 100% decompiled, 42 shards, 10.2M chars, 343 s** (`ghidra_out/MANIFEST.txt`); `COVERAGE.md` generated. Original plan text: project `ghidra_proj/SMAC`
- 2026-10-20 (session 13): **First names from the shards.** `NAMED.md` created (append-only, each row carries the field offsets that justify it). `0x5c9fc5` (383 callers) = **UI layout/position of a three-part widget**: takes a rect in `p[0..3]`, walks `obj[0..2]`, subtracts the size fields at `+0x18/+0x1c`, calls `0x5dd09c` per part and repeats the draw via `0x5c1187` when `obj[8]` is set. `0x5dd09c` saves/restores `DAT_00698bec`/`DAT_00698bf0` around `0x5dd0fc` ⇒ graphics-state wrapper (clip origin), which makes the caller a *drawing* routine. `0x64b9e0` (1,968 callers, 224 B) confirmed as a compiler helper — the raw in-degree ranking is dominated by CRT stubs, so `coverage.py` now filters helpers (`callers≥300 & size<400`) out of the hub table and lists them separately. Export notification arrived: exit 0
- 2026-10-20 (session 14): **Map format cracked open (partially).** Traced `maps/planet.MP` to code, not guesswork: `FUN_00598340` is a magic dispatcher (reads 9 chars, `_strcmp` vs `"TERRAN"` / `"TERRANMAP"`, demands a 4-byte version ≥5) and `FUN_00597a70` is the loader: **796-byte (0x31C) header read**, then a 4-byte field, then a **58 848-byte (0xE5E0)** block, with ~80 KB of stack. Header carries the map name + landmark strings (`The Ruins`, `Pholus Ridge`, `Mount Planet`). Width/height NOT claimed: `50 00 00 00 50 00 00 00` sits at odd offsets (80×80 guess) — needs the consumer of the 796-byte buffer or a runtime dump. Two more hub names logged in `NAMED.md` (`0x598340`, `0x597a70`).
- 2026-10-20 (session 15): **`.MP` payload is an encoded grid, not raw.** `FUN_00597a70` alternates a raw read (`FUN_0064cc00`) with a block decoder `FUN_00596540` / `FUN_00596470`: allocates `w*h` bytes, reads that many, then walks pairs XOR-ing each byte with counters starting at `0x80` (delta+XOR obfuscation). Port it from `shard_015.c` ~line 9805 for a reimplementation. Still open: which blocks are encoded (the header read also sits just before a decoder call, but plaintext landmark strings in the file prove the header itself is not encoded) — resolve with a runtime dump, not more reading.
- 2026-10-20 (session 16): **Corrected a wrong claim and nailed the block layout.** `FUN_00596540`'s args are `(dest, nbytes, count=1, file)` — the decompiler's `param_2*param_3` is size×count, **not** w×h (an earlier session-15 note said w*h; fixed in `DATA_INVENTORY.md`/`NAMED.md`). Decoder verified from disassembly: reads nbytes into a temp, XORs pairs with counters from 0x80, **zero bytes pass through** (escape), writes to dest. Map file layout from the `push` immediates: 796 raw header → local (never parsed here) → 4-byte value → decoded blocks of **67 040 / 58 848 / 11 488 / 32** bytes. Separately `FUN_00596850` (4,637 B) loads a *save/state* header of the same 796-byte size into global `DAT_00985ab8` (a flags bitmask) plus 4 bytes into `DAT_0091b5b4` — two formats share the size, do not conflate.


, `MANIFEST.txt` = 10,284 functions / 100% ok / 42 shards / 343 s.
, script `ghidra_scripts/ExportAll.java`, out `ghidra_out/{index.csv,shard_NNN.c,MANIFEST.txt}`; pitfalls found — project dir must pre-exist, `-deleteProject` is a flag not `-deleteProject false`.



- **Session 17 (M11 — data close-out):** map format cracked by *runtime* read trace, not static reading: gdb bp on `FUN_0064cc00` logging caller+size (`>=64` filter; unconditional fired 34k times and starved the game) during "THE MAP OF PLANET" gave `0x5822ac` 2724 / `0x5822f7` 140800 / `0x58231d` 128 from one FILE* = file minus 15-byte prefix ⇒ `.MP` = `15 + 2724 + W*H*22 + trailer`, confirmed on planet.MP (80×80, 143,667 B) and planetx.MP (128×128, 363,525 B), trailer variable 128/338 B; `scripts/decode_map.py` + `MAP_FORMAT.md`; **retracted the "5,459 unaccounted bytes"** — those blocks belong to the save path, `FUN_00597a70` is not the map loader. Save: loaded Autosave 30 through the game's own LOAD screen and traced 16 sections closing to the byte (301,596 + 300 sub-threshold = 301,896); header `TERRAN\0 0x1A v86`, 796 B, year u16 @0x54 (2180 — matches the 80-turn soak); `scripts/decode_save.py` + `SAVE_FORMAT.md`; open: per-section size formulas (they shrink with game progress: 287,564 B at 2108). MILESTONES F1 DONE, F2 PARTIAL, F1b added.

- **Session 18 (M12 — save section sizes):** read all 13 `push` sites in `FUN_00596850`: ten immediate sizes (796, 67,040, 11,488, 16,000, 3,584, 26,624, 4,096, 256, 152, 10,144) and three computed — `0x5970e9` size = `DAT_00927538` raw; `0x59731e` = `lea eax,[edx+edx*2]`/`lea edx,[edx+eax*4]`/`shl edx,2` ⇒ **52 B/record** (6,188 = 52×119); `0x597524` = `lea ecx,[eax+eax*8]`/`lea eax,[eax+ecx*2]`/`shl eax,4` ⇒ **304 B/record** (11,248 = 304×37, count from `DAT_00985af4`); `0x59731e` is gated by `cmp [0x985dbc],ebx` and `0x597524` is skipped when the count is 0 ⇒ conditional section list, which is why older saves are smaller. Layout pinned by two unique content anchors that land identically in **two saves of different ages** (Autosave 30 = 301,896 B/2180, Autosave 5 = 287,564 B/2108): map dims `50 00 00 00 50 00 00 00` at **79,372** and `????????` at **222,896**, gap 143,524 = 2,724+140,800 exactly; ⇒ 48 B of sub-threshold reads interleaved before the map table and 252 after the trailer (48+252 = the 300 measured). `scripts/decode_save.py --anchors` verifies this and passes on both files. **Self-correction:** my first "79.42% of grid bytes identical" test was worthless — the data is mostly zeros so the match rate is flat across wrong offsets; the anchors are the real test. Open: placement of the 300 interleaved bytes (next: caller-scoped bp `if *(void**)$esp >= 0x596850 && *(void**)$esp <= 0x597a6b`).

- **Session 19 (M12b — save layout closed):** caller-scoped gdb trace (`readtrace_save.gdb`, condition on the return address range 0x596850-0x597a6b / 0x582260-0x582330 so 1-4 byte reads are logged without the 34k-hit flood) while loading Autosave 30 in-game → 26 reads in order. Full `.SAV` layout now: 12-byte prefix (magic+0x1A+version 86), 796 state header (year u16 @0x54), **u32 own player at 808 = 3** (matches `smac_state.py`), 67,040, 11,488, 32, map struct/grid/trailer at 79,372 / 82,096 / 222,896, 16,000, **u32 count prefix at 239,024 (=328) that sizes the next section**, 3,584, 26,624, 4,096, **119 × 52 B** records, **37 × 304 B** records, 256, 152, 10,144, 7 × u32, 220 B tail (55 u32 = 5 × 11-dword records, reader unattributed). `scripts/decode_save.py --sections` reproduces the split from the file alone and sums to the byte on **two saves of different ages** (301,896 / 287,564); the 52/304 split is ambiguous arithmetically for the big save (3 solutions) and the content test (304-byte records ~80% zeros vs 52-byte ~40%) picks (119,37) — the same pair the runtime trace reported independently, so the heuristic isn't circular; for the small save the solution is unique (18,8). Caveats recorded: section *semantics* unknown, re-save round-trip untested (writer not run), conditional-section skip path untested. MILESTONES: F2 DONE, F2b added.

- **Session 20 (M13 — units and bases located):** loaded Autosave 30 in-game and read the two record families straight out of `/proc/303349/mem` (`scripts/smac_records.py`; pitfall: `pgrep -f terran.exe` also matches the wine launcher and reading its mem gives a bogus EIO — use `pgrep -x`). **304-byte records at `0x95da10` = BASES**: null-terminated name at +19 (`University Base`, `Gaia's Landing`, `The Hive`, `Morgan Industries`, `Sparta Command`, `New Jerusalem`, `U.N. Headquarters`, … 37 total), **x at +0, y at +2**, every pair inside 0..79 on an 80×80 map, faction at +4 (`0x0303` = University = player 3). So `DAT_00985af4` is a **base count**, not `n_factions` (relabelled in `smac_state.py`). **52-byte records at `0x933278` = UNITS**: no ASCII in any of the 119 (types by index), x at +0, y at +2, owner faction at +14, flags at +10; four of them sit at (20,50) which is exactly `University Base`'s tile — the cross-check that ties the tables together. This is the instrumentation C2 needs: a unit's tile is now observable before and after an order.

- **Session 20b (C2 attempt, failed cleanly):** after loading Autosave 30 the live arrays read fine
  (119/119 unit records placed), but `scripts/smac_play.py --turns 4` printed only its header line and
  the game process then vanished (window gone, no crash line in `evidence/m13_wine.log`; the follow-up
  reader failed with a 0-byte read because the pid was gone). Leading explanation, **inference not
  proof**: on a loaded save the HUD is not the shape the driver's classifier knows, so the screen
  classifies as `unknown`, the 20 s grace expires, one Escape opens the game menu, the next Escape
  reaches the quit dialog and "Yes" exits — the same destructive-Escape failure mode already logged in
  `turn_driver.md`, now triggered on a *loaded* game rather than a title screen. Falsification test for
  the next session (one launch): load a save, OCR the live screen, print `classify()`'s verdict before
  letting the driver touch anything, and disable Escape entirely for the first 60 s.

- **Session 21 (M14 — the loaded-save failure mode is closed; C2 still open on the order path):** fresh boot, no orphans, `ptrace_scope` already 0. Queued falsification test run: loaded `Autosave 30` (Return → LOAD GAME (610,344) → `auto` row (293,264)+Return → double-click (400,374)) and printed `classify()`'s verdict before touching anything — **`unknown`, so session 20b's mis-classification explanation is confirmed, not a Wine crash**. The frame names the pane: `evidence/m15_loaded_words.png` = the LOAD confirm ("DIFFICULTY LEVEL: TALENT" caption y~197, "Provost Zakharov of the University", OK at (290,391)) drawn over the title art — not `title` (OCR can't read the big title letters behind it), not `hud`, not `dialog` (caption outside the 55..180 band). New `scripts/smac_probe.py` (print the verdict without touching the game) and `scripts/check_classes.py` (offline classifier regression on saved frames, **6/6 PASS**). Added classes: `cdrom` (the boot nag wears the game title → was `title`), `loaded-game` (click OK at caption_centre−108, caption_y+194 → (287,390)), and `dialog` now also fires on `region_colors(png,(350,90,630,320))<45` — needed because an **OPERATIONS DIRECTOR pane with ARTWORK** gave 148 colours in the old flat-panel box, so it read as `hud` and the turn stalled **156 s** at 2184; fixed, the same round cleared in **18.6 s**. `--no-escape 60` added: 4/4 turns 2180→2184 on the loaded save with the process alive. New `scripts/smac_unitpos.py` (unit/base snapshot+diff): 119/119 unit records in 0..79, 9 on University Base's tile, 37 named bases; **the array is packed, so record index is not unit identity** (first diff said 108/119 "moved" while also changing owner). Two new pitfalls: **Escape raises "Do you really want to quit?" in-game too** (caught by the `title` stop; OK at (400,305) restores a clean HUD) and a map click at (75,255) with a unit selected left **119/119 records byte-identical** — the order path, not the classifier, is now C2's blocker. Details: `turn_driver.md` §M14.
- **Session 22 (M15–M18 — gdb watchpoints work under Wine; a real ORDER is verified in memory):** `gdb 17.1` attaches to `terran.exe` and **hardware watchpoints fire** (`Hardware watchpoint 1..4`, max 4). Harness: `timeout 300 gdb -batch -nx -x scripts/m17_watch.gdb -p $(pgrep -x terran.exe) > evidence/m17_watch.log 2>&1 &` — the script must end `detach`/`quit` (M14's `kill -TERM` note was for a *killed* gdb; a clean script leaves the game running, verified alive afterwards). **Hit 1** (watch on 4 AI units' x): unit 67 `x 67 → 65535` at `0x5ab2f8` inside **FUN_005ab240** = `unit_remove_from_map(idx)` — writes 0xffff to +0/+2/+48/+50, unlinks the record from the list threaded through **+48/+50** (prev/next indices), stashes old x→`DAT_00991798`, idx→`DAT_009917a0`, old y→`DAT_009917a4`; chain `0x5a6291 ← 0x588e0b ← 0x4ce54f ← 0x4d124f ← 0x56d027 ← 0x56d2be ← 0x520e1e ← 0x522a1b ← 0x64dd06`. This also explains session 21's "108/119 moved": removal sets a sentinel, then a compaction pass slides records down. **Hit 2 (the milestone):** the game's own advisor said *"Perhaps this Scout Patrol unit should 'stay home'… Press the 'H' key to tell it to 'HOLD'"* — pressed `h` via `smac_probe --key h` and the selected unit's record changed **`+17: 00→02`** (order byte = `(&DAT_00933289)[i*0x34]`) and **`+28/+29: ff→00`**. Armed a watch on `+17` of the 4 records on tile (20,50) → hit at `0x4d3888` inside **FUN_004d3770** (`mov %bl,0x933289(%ecx)`, `ecx = 0x9c = 3*52`, `ebx = 2`); its Ghidra body matches instruction-for-instruction, ends `FUN_00584350(idx)` → `FUN_0052a720(0x11, idx, 0,0,0,1, 0x2101)` = the event broadcast. So **orders are: write `+17` (+28 short) then broadcast event 0x2101**. Driver implication: keyboard orders beat map clicks. Also falsified: base record `+80` is **UI tab state** (EXPLORE=6, BUILD/GOVERNOR=0xc2), not production — 3 production attempts (CHANGE→item→OK) changed no candidate field in `0x680000..0x9A0000` (2921 bytes, all palette/DP-object/vertex churn). Over the 3 turns my unit count fell 9→5 (enemy units visible adjacent to University Base); `cur_player` round took 56 s. Still open for C2: a **move** order (x/y change) via click, and the move-exec function. Details: `turn_driver.md` §M15–M18.
- **Session 23 (M19–M23 — the MOVE machinery is named; the player gesture is still open):** footing re-read (skill + MILESTONES + session 22 entry). Found session 22b had left M19 artifacts with no notes entry: `evidence/m19_watch.log` (all 6 x-watchpoint hits were `rep movsl` at `0x64bfa3` ← `0x5abc4b` = the array compaction, i.e. the pitfall, not moves), `evidence/m19_bp.log` + `evidence/m19c_writesites.log` (both aborted on `Undefined command: "silent"` — gdb has no `silent`), and `evidence/m19c_writesites2.log` (4,463 lines, **739 x-writes**) = the working oracle. Game was still live (pid 370597, year 2198, TracerPid 0 after cleanup). **Named the chain from the corpus + those hits**: `FUN_005ab320(idx,x,y)` is the only writer of a unit's tile (writes +0/+2, relinks +48/+50 to the destination tile's head from `FUN_005ab130`, updates the tile record) ← `FUN_005a58e0(idx,x,y)` moves a whole stack ← `FUN_00585720` (per-unit action executor, returns `0x5893a8`); `FUN_005a5a80(idx)` re-stacks via scratch (-3,-3); `FUN_00502c40(idx,dir,parity)` steps one tile from the **8-direction parity-split delta tables** read out of `.rdata` — x `0x6784a0` [+1,+2,+1,0,-1,-2,-1,0] / y `0x6784c4` [-1,0,+1,+2,+1,0,-1,-2] and the parity-0 pair `0x67850c`/`0x678990` — calling `FUN_00502cd0(idx,?,destx,desty)`, whose other callers are `FUN_0055c920` (AI move scoring) and dispatcher `FUN_0052bce0` **case 0x4402**.
  *Live driving* (breakpoint-on-store oracle, `scripts/m23_writesites.gdb`, `evidence/m23_ws.log`/`m23_ws3.log`): `v` (tutor #TOUR1B "switch back to moving pieces") and the **Select unit to activate** dialog (rows y 154..434, OK (307,486)) each fire 8 re-stack writes — activation, not movement. Arrow keys move a **cursor**: the terrain readout went `(41,11) Flat & Arid` → `(43,11) Rocky & Arid` (= Δ(+2,0) = `dir 1` at odd x) with no x-store. `Return`, `Space`, `g`, `f`, `Down`, `Right` and clicks at (396,240)/(480,246)/(428,195) produced **no** x-write with a new coordinate; a tile click only refreshed the centre panel ("Commodities: 1 … NET INCOME: 0/turn"). So C2's remaining unknown is the gesture, not the mechanism.
  New facts: the unit array now holds **166 live records**, not 119 (records 166+ zero) — a fixed 119-record window misses every unit created after the save; our 8 survivors are all stacked at (41,11), owner 3, chain head 118 → 120 → 121 → 123 → 122 → 124 → 117 → 119, HUD calls them "Independent, Moves 1, No Order". **Faction index → name** read off the base array by base name: 1 Gaia's Garden, 2 Hive, 3 University ("The Rapture"), 4 Morgan, 5 Sparta, 6 Circle of Mother, 7 U.N.; no base reports faction 3 any more and "The Rapture" reads `+4 = 0x306` where every other record is `(f<<8)|f` (read as: it changed hands — inference). Unresolved contradiction: the activate dialog prefixes our units **"Green"** while the stored note says own player 3 = University.
  New pitfalls: **two gdb cannot attach** (second prints `already traced by process M` then `The program is not being run` and exits — a zero-hit log that looks like "no writes happened"; check `TracerPid` in `/proc/<pid>/status` before arming and before believing a null result); hardware watchpoints on a unit's x are captured by the compaction's `rep movsd` while a turn resolves, so prefer store-site breakpoints; a map click **pans** the view, so re-measure the unit marker bbox with PIL (`r,g,b>190` in the map band) after every click. Docs: `turn_driver.md` §M19–M23, 9 new `NAMED.md` rows, `MILESTONES.md` C2 rewritten. Game left alive, untraced.
- **Session 24 (started 2026-10-21, C2 player-move gesture):** footing re-read (skill + `references/wine-headless-harness.md` §"What the live game does with input" (updated 2026-10-21) + MILESTONES C2 + session 23 entry). `terran.exe` live at pid 370597, TracerPid 0. Target = the player gesture that issues a MOVE: arm the store-site oracle + entry breakpoints on `FUN_00502cd0`/`FUN_00502c40`, fire gestures only while `cur_player == 3`. **Result (M24):** the order plumbing is named end-to-end. Live `$ecx` at `0x4d3f70`/`0x512450` = **0x8f79e0** and `+0x23bd4 = 0x91b5b4` (own player) is an exact cross-check, so **selected unit index = 0x91b5bc** (live 119), orders-mode flag `0x91b5b8` (live 1), order-menu-pending `0x91b5c4` (live 1), cursor/destination candidate lists `0x91b5f0` (x) / `0x91b670` (y) indexed by `0x91b5e8` (live 13, every entry (41,11)). Two ASCII-keyed dispatchers: `FUN_00512450` acts on the selected unit (`'h'`→`FUN_004d3770(sel,0)` = the proven HOLD, `'H'`→mode 10, `'F'`→4, `'E'`→0xd, `'B'`→0xe, `'g'`→`FUN_004d6fb0(sel,0x18)`, `'a'`→`FUN_004d3f70(sel.x,sel.y,1)`), `FUN_00511960` acts on the cursor tile (`Space`→base at cursor, `'a'`→`FUN_004d3f70(cursor,1)`, `'b'`→`FUN_004e3700`); `FUN_00512b40` routes keys and remaps `b c d f g h i` → `0x28 0x22 0x25 0x27 0x24 0x26 0x21` (the directional cluster). `FUN_004d3f70(x,y,flag)` = **ACTIVATE at a tile**, live-proven (`ACT x=41 y=11 flag=0 sel=119` for a click at pixel (382,212)); when the tile holds a stack it calls `FUN_0048f8b0(idx, s_PICKUNIT, 1)` = the **SELECT UNIT TO ACTIVATE** modal, and after row+OK re-stacks (`FUN_005a5a80`) + `FUN_0050cab0(1)`. `FUN_00476580(pixel_x, pixel_y, flag)` = **map-widget click handler**, live-proven (`MAPH p1=0x1de p2=0xd4` for a click at (478,212)) — it dispatches a chosen order code (`case 10 → FUN_004cffa0` = MOVE) and its direct-write branch sets **order `+17 = 0x18` with destination `+20`/`+24`**, then `FUN_00584350` (0x2101). `FUN_004cffa0(unit,x,y)` = **issue move**: solo (`DAT_00920434 == 0`) → `FUN_004cdc70(unit,0,x,y)`, netplay → `FUN_00528930(&unit,4,x,y,0)` + packet `0x2413`. Live null with positive controls (`scripts/m24c_move.gdb`, 3 hardware watchpoints on record 119 `+16/+20/+24` + entries for `476580/4cffa0/4cdc70/5ab320/4d3f70`): a left-click on a neighbour tile produced 1 `MAPH` and **0** `ISSUE_MOVE`/`SOLO_MOVE`/watchpoint hits; a right-click there raised the picker again. **Blocker for C2:** all 8 survivors are stacked on (41,11), so *every* click on that tile (either button) raises the picker — the game never rests in "one unit selected, awaiting a destination click"; `Script.txt:1103 #UNITCLICK` has **no Move item** while `#GOTO` is a caption-only "Select Destination" pane (inference: move is issued by a destination-picking mode). New pitfalls: **gdb `printf` is block-buffered into a redirected file** (read the log only after killing gdb — "no new line" ≠ "no hit"); `MAPH` logs raw pixels while `ACT` logs the resolved tile, so use that pair as the pixel→tile calibration (the same tile sat at (387,172) then (382,212) after pans); picker OK ≈ (295,483), CANCEL ≈ (500,483). Docs: `turn_driver.md` §M24, 13 new `NAMED.md` rows, `MILESTONES.md` C2 updated. Game left alive (pid 370597, untraced, our turn).
- **Session 25 (M25, 2026-10-21, "keep going"):** **Retraction first — the move destination is `+20`(x) and `+28`(y), not `+24`**: Ghidra's `(&DAT_0093328c)[i*0x1a]` / `(&DAT_00933294)[i*0x1a]` are u16 arrays with 0x1a×2 = the 52 B stride, so the offsets are 0x93328c−0x933278 = **+20** and 0x933294−0x933278 = **+28**; corroborated by a freshly loaded save where other factions' units carry `+17 = 0x18, +20 = 54, +28 = 52` and `+24 = −1` in every record. Live `DAT_00920434 = 0` = the **solo/netgame switch** (gates `FUN_00528930`, routes `FUN_004cffa0` → `FUN_004cdc70`) — the source-level reason for M6b/M7/M8. New tool `scripts/m25_calibrate.py` (click or key, then read the HUD readout + the M24 globals + the selected unit's record, no tracer). **Experiment 1 (poke, no tracer):** wrote `+17 = 0x18, +18/19 = 0, +20 = 43, +28 = 11` into a unit at (41,11) through `/proc/<pid>/mem` (`r+b`, writable); `smac_play.py --turns 1` advanced **2194→2195 in 18.5 s** and the order was still there afterwards — on the record that had **slid 127→124** under compaction — but **no unit moved**: the engine trusts the fields, writing them is not the trigger. **Experiment 2 (gdb `call`):** attempt 1 while the picker modal was up reached `FUN_004cdc70` (`unit+4 |= 0x40` appeared in memory) then **SIGSEGV**; the process survived but the **UI was dead** (CANCEL, row+OK and TURN COMPLETE clicks all inert, main thread R with climbing utime). Attempt 2 on a clean HUD with `$ecx = 0x8f79e0`: the `0x4cdc70` breakpoint fired *inside* the injected call → gdb abandoned the expression and detached → again only `unit+4 |= 0x40`, no move, no order byte. Recovery = kill + relaunch + load: nag `Return` → LOAD GAME (610,344) → LOAD list (single click selects and fills the name box; rows y 264..432 step 24, lexicographic 1/10/2/20/3/**30**/4/5 with 30 at y 384; **OK (343,491)**, CANCEL (511,491)) → confirm OK (290,391) → HUD. **`Autosave 30.SAV` now loads at 2194, not 2180** — autosaves are overwritten in place, so "Autosave N" is not a stable snapshot. Also read live: tile array `DAT_0092ae14` = 0x40a6660 with `DAT_00692184 = 40` (=(80/2)) and 44 B records; no base on (41,11) or (43,11) among the 44 bases. Pitfalls: never gdb-`call` while a modal is up; a gdb `call` into game code is unsafe (breakpoints inside it abort the expression, and the inferior returns to gdb's dummy frame); `smac_probe.py --save` is ignored when `--quiet` is passed. Docs: `turn_driver.md` §M25, `NAMED.md` +3 rows and the `0x476580` row corrected, `MILESTONES.md` C2 updated, `NEXT_PROMPT.md` header updated. Evidence: `evidence/m25_adj.log`, `m25_issue_move.log`, `m25b_call.log`, `m25_wine.log`, `m25_{adj,health,row,t2,t3,t6,t7,after_call,boot}.png`, `trace_20261021_110403.jsonl`. Game left alive: **pid 844650, year 2195, our turn, clean HUD, TracerPid 0, 8 units at (41,11)**.
- **Session 26 (M26, 2026-10-21):** footing re-read (skill + MILESTONES + session 25 entry). `terran.exe` had **died between sessions** → relaunched (pid 882970) and reloaded. **`0x18` in `+17` is THE queued MOVE order** — proven by enumerating every store to `DAT_00933289` across all 42 shards: click-handler direct branch (`FUN_00476580`: `+17=0x18`, dest `+20/+28`, `+4=0`), hotkey issuer `FUN_004d6fb0(unit,code,flag)` (`+17 = code`, cursor tile from `0x91b5f0/0x91b670[0x91b5e8]`, then broadcast `FUN_00584350`), AI hubs `0x55f650`/`0x55c920`, HUD `0x4bd3d0`, dispatcher `0x52bce0` (packet `+0xc`), `FUN_004cce50(unit,k)=k+4`. **Retractions: `FUN_004cffa0` is issue-ATTACK (gate `FUN_005acc00` → `s_UNITMOVED`; empty tile → bombard; enemy tile → step toward), `FUN_004cdc70` is the bombard/arrival resolver** (`ARTYBOMB*`/`HAVEDESTROYED`/`ATEFOREST` strings, `_rand` coin rolls, facility-destroy loop, attack `FUN_0056d350`, tail `FUN_00585720(unit,-1,3)`) — the M25 injected call bombed, it didn't walk. **Solo orders run synchronously via `FUN_00529090(unit,dir,mode)` → `FUN_00585720(unit,dir,3)`** (callers: HOLD setter `0x4d3770`, key router `0x512b40`, `0x4ce4a0/0x4ce710`, dispatcher) — the poke failed because nothing called the wrapper. Movement model: total `FUN_005ac650(unit,0)`, used `+40`, consume-all `FUN_005acdb0`, gate `FUN_005acc00`, idle `FUN_005acab0`; waypoints `+18/+19`, watchdog `+42` (`s_KEEPMOVING`), dir `+41`. **Live:** clicks were dead — pointer grab sits on Wine desktop window `0x400004` (`getmouselocation` symptom); first click breaks it, then `MAPH` fires 2/2; keys reach `KEYROUTE` (h/g/d/Esc logged) but hotkeys swallowed while `b5c4=1 ∧ b5b8=0` (`v` clears `b5b8`); fresh load opens **base screen + OPERATIONS DIRECTOR modal** (dismiss row (400,307)→OK (400,362)→Escape); LOAD pane is a file browser at host root — type `home/n100/reverse/smac/programs/saves/auto` into name box, OK (345,555). **Autosave 30 on disk = year 2110 now** (slots overwritten in place; newest = Autosave 2 @ 2198; year = u16 at file `0x54`). Test A: poked rec0 `order=0x18 dx=19 dy=7 flags4=0 mpused=0` + `call (int)0x529090(0,-1,0)` (`$ecx=0x8f79e0`, no bps) → executor ran (`mpused 0→3`, `b5c4` cleared) then **SIGSEGV at `0xe921da34`** (Wine space, unmapped after detach) before the walk; unit unmoved; game survived healthy. New tools `scripts/m26_{load,poke,arm}.py` (arm generator had a double-`0x` bug — gdb died at script line 3, the zero-hit-log pitfall bit again). Docs: `turn_driver.md` §M26, `NAMED.md` +12 rows, `MILESTONES.md` C2, `NEXT_PROMPT.md` rewritten. Evidence: `evidence/m26_{live,live2,call}.log`, `m26_screen{1..4}.png`, `m26_live.gdb`. Game left alive: **pid 882970, year 2110, our turn, TracerPid 0, responsive; rec0 carries leftover order=0x18/mpused=3** (watchdog will clear).

- **Session 27 (M27, 2026-10-21):** footing re-read (skill + MILESTONES + session 26 entry); `terran.exe` was alive but at the CD-ROM nag (pid 909721, year 0) — killed and relaunched (pid 914079), then loaded **Autosave 2 = 2198** by hand after learning the LOAD dialog's name box must be *backspaced* clear and given a **Windows** path (`Z:\home\n100\…\Alpha Centauri Autosave 2.SAV`, box (400,252), Return, confirm OK (290,391)); the title screen still classifies `unknown` so `m26_load.py` times out and its repeated Returns bounce back to the menu. **M27 = the player MOVE gesture.** Retracted the M23–M26 claim that arrows only move a cursor: with a unit selected ∧ `b5b8 != 0`, **an arrow key moves that unit one tile, synchronously** — one `Right` took rec117 (41,11)→(43,11); static path `FUN_00512b40` `case 0x21..0x28 → dir 0..7` → `FUN_004e1f90`/`FUN_005255e0` pre-gates → `FUN_005acc00(unit)` can-act gate (fail ⇒ advisor `s_UNITMOVED`) → `FUN_00529090(unit,dir,0)`; Shift+arrow instead queues `+17=0x19, +20=dir, +22/+30=unit tile`. Live proof with **no injection**: `scripts/m27_solowrap.gdb` (bps 0x529090/0x585720/0x5ab320) + `scripts/m27_run.sh` (captures gdb PID — `pkill -f <script>` in the same command kills your own shell) → `evidence/m27_solowrap2.log` has three of the game's own `SOLOWRAP idx=117/118/120 dir=1 mode=0` → `EXEC … mode=3` → `SETTILE (45,11)/(45,11)/(43,11)`; records: 117/118 41→45, 120 41→43, **3 MP/tile, 6 MP/turn** (two steps per fresh unit). Turn 2198→2199 stalls in the AI phase on two modals — PSI-COMBAT **DATALINKS** (`Return`) and **OPERATIONS DIRECTOR** (one `Escape`) — after which `cur_player=3`, `tf=0x100000`. Docs: `turn_driver.md` §M27, `NAMED.md` +3 rows, `MILESTONES.md` C2, `NEXT_PROMPT.md` header. Evidence: `m27_after_move.png`, `m27_solowrap{,2}.log`, `m27_{a…x}.png`. Game left alive: **pid 914079, year 2199, our turn, TracerPid 0**; survivors now split 117/118 (45,11) · 119/120 (43,11) · 121–123 (41,11), all `order=0`.

Older sessions: `docs/sessions/sessions-50-51.md` (2 sessions). Read it only when a question reaches back before session ## Session 52.

## Session 52 (2026-10-23) — M52b: edi at the SPENDA store is `0x4e40a0(owner,1,−1) × 0x5ac950(queue_type, idx, 0)` = 10 × 1 — M49a's "sweep-entry index" is FALSE at its first link (0x4f5aa9 loads the OWNER BYTE), and 0x4eaa10 preserves edi

**The provenance chain, measured end to end in one run** (3 rounds, 2360→2363, 0 OCR passes,
`evidence/m52b_run.out`; seven new EDI_* breakpoints added to `scripts/m51a_drive.py`):
1. `EDI_ENTRY 74 eip=0x4f5aa9 idx=70 owner_byte=3 name=Climactic Research` (`m52b_watch.log:386`) — edi is
   assigned at `0x4f5aa9 mov edi,edx`, and edx comes from `0x4f5a9c mov dl,BYTE PTR [ecx+0x4]` after
   `xor edx,edx` (`m52b_fn4f5a70_4eaa10_disasm.txt:17,19`) ⇒ **edi := the base's OWNER BYTE, not the sweep
   index**. Fired 222× (3 rounds × 74 bases) and the printed byte matches every base's owner (Morgan bases 4,
   Sparta 5, Assassin's 6, U.N. 7 — `:62, :94, :109, :139`), so this is a general property of `0x4f5a70`,
   not a one-off. M49a's chain broke here.
2. `EDI_QGATE q50=2 st=200` (`:388`) — `0x4ef88b mov ecx,[eax+0x50]` = 2 ≥ 0 ⇒ the `jge 0x4efa2c` branch.
   The negative-queue branch (which would set `edi = 0x4e40a0(...)` at `0x4ef8e2` and imul the item table at
   `0x4ef8ed`) never ran for us: **0 EDI_NEGPATH / EDI_NEGMUL hits**.
3. `EDI_POSPATH factor_eax=10` (`:389`) — `0x4efa3c call 0x4e40a0(owner=3, 1, −1)` returned **10** and
   `0x4efa4b mov edi,eax` overwrites the owner byte. Statically confirmed: with arg2 == 1 the function jumps
   to the government switch at `0x4e421f` (`m52a_fn4e40a0_disasm.txt:137`), index =
   `faction[p].int[20]@0x94d6a0+p·0x20bc + 7` = 0+7 = 7, and the jump table (`x/12wx 0x4e4318`) sends 7 to
   `0x4e430f = mov eax,esi` — the **×1 case** (cases 0-4 are `(esi·13+9)/10` = ×1.3, case 5 another
   multiplier; the table implements per-government economy scaling).
4. `EDI_POSMUL edi_before=10 ret_5ac950=1` (`:390`) — `0x4efa4d call 0x5ac950(2, 70, 0)` returned **1** and
   `0x4efa52 imul edi,eax` leaves edi = 10. `FUN_005ac950` (`m52b_fn5ac950_disasm.txt:6,12,13,25,26,119,123`):
   `esi = arg1` is a **unit type id** (it indexes the type table at `0x98ad88 + type·52`), it loads
   `bl = byte[type+0x29]` (+41) for every type and only clamps it to [1, 999] when the class byte
   (+0x2a) == 8 and arg2 ≥ 0, then for `type < 0x40` jumps to the tail `mov eax,ebx` — so the return is the
   **+41 byte**. Live type table: Colony Pod +41=3, Formers +41=2, **Scout Patrol +41=1** (class 3),
   Transport Foil +41=3; the neighbouring +0x2b (+43) byte holds 10 for Scout Patrol (40/41/39 for the others).
5. `EDI_SPENDA edi=10 st=200 q50=2 m1c=104 m2c=8` (`:391`) → `0x4efedb sub esi,edi` →
   `W40_SPENDA old=200 new=190 edi=10` (`:392`) → `W40_CLAMP1 old=190 new=0 cap=10 d0=0` (`:400`).

**Verdict on the two competing claims.**
- M49a's "edi = the base's SWEEP-ENTRY INDEX" is **falsified twice**: the index is 70 (not 10) and the
  assignment at 0x4f5aa9 loads the owner byte (3). The value that survives to the store is the queue-path
  product.
- M48d's original reading — "Scout Patrol cost 10" — is **restored in substance**: the subtrahend is the
  queued item's production cost, computed as `economic factor (10 = our government's ×1 case) × a per-type
  byte`. INFERRED label on the byte's meaning: +41 is a per-type production weight, NOT the mineral cost
  itself (the +43 byte is the one that reads 10 for Scout Patrol, and alpha `#UNITS` documents its own Cost
  field as "0 = Autocalculate", i.e. the engine computes it).
- The milestone's hypothesis that `0x4eaa10` (called 20 bytes earlier at 0x4efec4) leaves the residue is
  **statically refuted**: it pushes edi at `0x4eaa41` and pops it at `0x4eb672`
  (`m52b_fn4f5a70_4eaa10_disasm.txt:396, 1357`) — callee-saved, restored on the normal path.

**Side results.**
- `base+0x50` is the **queued production item id**, not anonymous scratch: 2 = unit type 2 = "Scout Patrol"
  (name read from the type record at `0x98ad88+2·52`). QGATE decodes it as: `0xffffffda` = empty; ≥ 0 = the
  id; < 0 = `|q|` with `[ebp-0x1c] = |q| − 39` and flags set by the 34/39 thresholds (`0x4ef8a1-0x4ef8c9`).
  `0x5ac950` treats `type ≥ 0x40` as the facility case (checks `byte[type·52+0x30] & 4`, a per-64 group flag
  at `0x927a98`, and `0x94d438`) — consistent with M46's "runtime item = alpha #FACILITIES idx + 1".
- Government economy multipliers live in the `0x4e40a0` switch at `0x4e4318` (12 entries, indexed by
  `faction[p].int[20] + 7`): ours (int[20] = 0) is the ×1 case; case 0-4 = ×1.3, case 5 = another ratio.
- IADD fired 2× in 3 rounds (both d0 = 0, no-op writes); SPENDA/CLAMP1 once, on the round a completion ran.
  The clamp story from M52a is unchanged.

Next: **M53a** — the `base+0x50` queue record end to end (id encoding, where the build progress counter
lives, what fires COMPLET 0x4efe41) and whether the charge `factor × type+41` is the whole cost story.
Footing rewritten in NEXT_PROMPT.md (session 53).

## Session 53 (2026-10-23) — M53a: the base+0x50 queue record end to end — it is a 10-slot ITEM ARRAY (+0x4c = last index, +0x44 = mirror), unit/facility completion is PAYMENT-DRIVEN with NO progress counter, negative values are secret projects −(39+idx) registered in the 33-dword table 0x985b3c

**Run:** `scripts/m51a_drive.py --tag m53a --rounds 3 --budget 1100` — 3 rounds 2363→2366, **0 OCR
passes**, clean detach (`evidence/m53a_watch.log:1134`); two new NAME-conditioned sites in GDB_TMPL
(`QPIPE` @ 0x4ef6d0, `QCOMPLET` @ 0x4efe41; identity = dwords "Clim"@+0x13 + "acti"@+0x17 through
`*(int*)0x8f0d60`, slide-proof). Static: `evidence/m53a_queue_disasm.txt` (0x4ef9b3+340i),
`evidence/m53a_qgate_disasm.txt` (0x4ef880+80i), `evidence/m53a_fn_disasm.txt` (whole FUN_004ef6d0,
2600i), `evidence/m53a_fn4ef6d0_pseudocode.txt`.

**1. The queue is an ARRAY, not a dword** (VERIFIED static + live). 10 item slots at
`base+0x50 .. +0x73`; **+0x4c = last used index** (UI caps it at 9 → 10 entries: `case 3: <9 → +1`
and `= 9`, `ghidra_out/shard_001.c:9432-9437`; the FUN_004f4060 drain iterates `[+0x4c]+1` dwords
from +0x50 and decrements the per-player item counts at `0x94de84 + owner·0x20bc + id` —
`shard_012.c:23044-23060`). Live: **f4c=0 = one entry**, f68=0 = slot 6 never written
(`m53a_watch.log:392`). The pipeline only ever processes slot 0 (+0x50); grep of the whole-function
disassembly finds **no +0x50 writer** — reads only (`fn_disasm.txt:67,118,200,223,1316`).
**+0x44 = active-item mirror**: `FUN_004f5a70` copies `+0x50 → +0x44` on every visit
(`shard_012.c:24185`, short*-alias `+0x22 := +0x28`), and the ownership-transfer block clears BOTH
to −38 (`shard_012.c:23065-23068`). Live: f44 == f50 == 2 at every QPIPE
(`m53a_watch.log:392,769,1115`). Also `[base+0x98] := storage` snapshot at the same sites
(`shard_012.c:24184`; in-pipeline `pseudocode:302,823`).

**2. Encoding** (VERIFIED static, `m53a_qgate_disasm.txt:5-55` = 0x4ef88b-0x4ef938): `−38
(0xffffffda)` = empty → NOQUEUE; `≥ 0` = item id (unit `< 0x40`, facility `≥ 0x40`); `< 0` = `|q|`
with scratch `[ebp-0x1c] = |q|−39` if `|q| ≥ 39` else −1 (`:12-17`), `[ebp-0x20] = [|q| ≥ 34]`
(`:18-23`); negative cost = `0x4e40a0(owner,1,−1) × dword[0x984d44 + 48·|q|]` (M46 upkeep table)
(`:30-35`). M52b's "`[ebp-0x1c] = |q|−39`" is the NEGATIVE branch only; on the positive path
0x4efae5 overwrites it with `52·id` (`m53a_queue_disasm.txt:61-64`) — live m1c=104 = 52·2 ✓
(`m53a_watch.log:397`). `[ebp-0x2c] = 1<<owner` set unconditionally at 0x4ef815
(`fn_disasm.txt:81`) — live m2c=8 = 1<<3 ✓.

**3. Negative values are SECRET PROJECTS** (registry VERIFIED static; project identity INFERRED).
`0x4f0d83: 0x985b3c[|q|−39] := base index` (`fn_disasm.txt:1480`); the table is **33 dwords**
(`FUN_005305f0(&DAT_00985b3c, 0x84, …)` — `shard_013.c:15670`) = 33 secret projects;
`FUN_0051f730` (per-player refresh) reads `registry[project]` → owner(base[registry])
(`shard_013.c:11119-11120`); 0x4f0819-0x4f0837 formats the builder's base NAME from the registry
(`fn_disasm.txt:1146`). So `|q| = 39 + project_idx`; the "another base already queues this" check
compares `other+0x50 == our+0x50` (`fn_disasm.txt:1315-1316`, esi = base+4).

**4. No build-progress counter for units/facilities — completion IS payment** (VERIFIED live).
QCOMPLET fired exactly once in 3 rounds — only the round with storage 200 ≥ cost 10
(`m53a_watch.log:397`); rounds 2-3 st=0 → 0 hits (`:769,1115`). Gate: `cmp [ecx+0x40],edi; jge`
0x4efa5e-61 (`queue_disasm.txt:39-40`). PROGDIV 0x4efd49 is NOT an accumulator: it is the ETA
string `(factor×(pop+1) − [base+0x3c]) / [base+0xcc]` clamped 0..10007, gated `[base+0xcc] > 0` —
ours is −3, hence "PROGDIV never fires in solo" (`queue_disasm.txt:193-207`). Consequence,
PREDICTED: a payable head re-completes every round (matches M45's units 1→6 from one standing
queue). The only per-base progress accumulator remains +0x3c/+0xcc (pop-growth, M52a; and per
`fn_disasm.txt:1334-1343` the project path compares `other[+0xcc]+other[+0x3c]` vs the project
cost — projects also accrue in +0x3c).

**5. COMPLET 0x4efe41 dispatch** (VERIFIED static, `queue_disasm.txt:250-291`): `ebx < 0x40` unit →
`[ebp-0x20] := 0` → SPENDA (`:288-291`); `ebx ≥ 0x40` facility → set bit 2 of word
`[0x98adb8 + 52·id]` (built flag) and if newly set → repoint `0x8f0d60` + the rebuild chain
0x4e8d60/0x4e78e0/0x4e92c0/0x4e93f0/0x4eaa10 (`:252-287`). Third trigger: class-8 Colony Pod ∧
pop==1 ∧ `0x94d438[p] > 1` → ABANDONBASE confirm via `0x48ee00(SCRIPT,…)`, answer ≥ 2 → COMPLET
(`queue_disasm.txt:215-226`, `pseudocode:204-245`). Downstream of CLAMP: `[+0x98]:=[+0x40]`
(`pseudocode:302`) → spawn helper `0x5ab650` returns the new unit index, unit flags set in
`0x93327c + idx·52` (`pseudocode:307-320`; INFERRED unit creation — bp not armed) → PRODUCE /
PRODUCEPROTO announcement pane with per-domain unit icon (`pseudocode:440-530`).

**6. IADD gate CLOSED** (VERIFIED): `storage += d0` iff `d0 ≥ 0 ∧ queue ≠ −38 ∧ (f30 & 2) == 0`
(`fn_disasm.txt:65-69` + `pseudocode:110-113`) — explains M48d's "2 hits in 3 rounds": the gate is
queue non-emptiness, not randomness. Live both hits d0=0 no-ops (`m53a_watch.log:393,1116`).

**7. cc recomputes PER-VISIT, not per-round**: the +0xcc=1 poke was already −3 at the first
pipeline print (`m53a_watch.log:392`) — 0x4f5a70 runs the recompute chain before calling the
pipeline. d0 likewise (poke 200 → live 0/−1/0, `:392,769,1115`).

**8. Opens.** (a) **Dequeue/shift after a POSITIVE completion is not done by the pipeline** — tail
clear is negative-only (`pseudocode:1476-1478`: `queue == −|q| ∧ [base+0x4c]==0 → +0x50 := −38`);
full-clear writers that zero BOTH +0x44 and +0x50: `FUN_00507ef0` (`shard_012.c:34739-34740`) and
`FUN_005437d0` (`shard_013.c:30426-30427`), plus enqueue-side `FUN_00417ee0`
(`shard_001.c:9452`, writes the raw command incl. `< −38` project ids → `0x446250`). Live: f50
stayed 2 all run. (b) `base+0xc0` printed a constant 7 == our pop every round — semantics unresolved.
(c) Negative-value semantics beyond the registry (34/38 band) unprobed — 0 NEGPATH hits again.

Next: **M53b** (unchanged queue: +41 production weight vs +43 autocalculated cost across all
`#UNITS` rows), or **M53c** (the dequeue writer: arm 0x507ef0/0x5437d0/0x417ee0 and complete a
payable round with a 2-item queue). Footing rewritten in NEXT_PROMPT.md (session 54).

## Session 54 (2026-10-23) — M53c: the dequeue IS A CALL, NOT A STORE — FUN_004ef5d0 pops the head; the pipeline calls it at 0x4f037b whenever the base's owner is in the event mask (otherwise it re-picks via 0x4e5ae0); +0x4c is the PENDING-entry count (entries = +0x4c + 1), and with +0x4c == 0 NOTHING consumes the head — a payable head re-completes every round

**Runs:** `scripts/m53c_drive.py --tag m53c --rounds 3 --budget 1100` — 3 rounds 2366→2369, **0 OCR
passes**, clean detach (`evidence/m53c_watch.log` last line, `evidence/m53c_drive.json`
`detached:true, ocr_passes:0`); confirmatory `scripts/m53c2_drive.py --tag m53c2 --rounds 2 --budget
700` — 2 rounds 2369→2371, 0 OCR, clean detach. Both poked (TracerPid 0, pre-arm) `+0x50=2` (Scout
Patrol), `+0x54=3` (Transport Foil), `+0x4c=1` (a legal TWO-entry queue), `+0x3c=500, +0xcc=1,
+0xd0=200, +0x40=200` (`evidence/m53c_drive.json` poke events). Our base = idx **70** @ 0x962d30
(`(0x962d30-0x95da10)/0x130 = 70`, `evidence/m53c_drive.json` final.base).

**0. M53a's "no +0x50 writer in the pipeline" was an artifact of a TRUNCATED dump** (VERIFIED).
`evidence/m53a_fn_disasm.txt` has 2601 lines and its last instruction is 0x4f1d5d — 2,600 insns cover
only 9,869 of the 12,298-byte function (avg 3.8 B/insn), so 0x4f1d5d-0x4f26da was never disassembled.
Re-dumped: `evidence/m53c_tail_disasm.txt` (0x4f1d50 → 0x4f299f, past the function end at 0x4f26da).
It exposes the tail re-pick call 0x4f1e01 (`evidence/m53c_tail_disasm.txt:61`), the tail clear
`mov DWORD PTR [eax+0x50],0xffffffda` @ **0x4f1e3f** (`:73-80`) and a third re-pick 0x4f21b8 (`:277`).
Pitfall: size the dump from `index.csv` size ÷ 3.8, or bound it by the NEXT function's address.

**1. THE POP PRIMITIVE = `FUN_004ef5d0(base_idx)`** (0x4ef5d0, 244 B, `evidence/m53c_fn4ef5d0_disasm.txt`,
Ghidra `shard_012.c:20538`), register-level:
- `esi = idx·0x130`; gate `eax = [base+0x4c]; test; je 0x4ef684 → return 0` (`:12,:16`) — **nothing
  pending ⇒ the head is NOT consumed**.
- if head ≥ 0: `dec BYTE PTR [0x94de84 + owner·0x20bc + head]` (`:20-27`) — the consumed item's
  per-player item count (the same count `0x4e5560` maintains).
- **the shift** `0x4ef628-0x4ef639`: `edx = [slot+4]; ++i; [slot] = edx; slot += 4; cmp i, count; jl`
  → runs `count` iterations, i.e. `slot[i-1] := slot[i]` for i = 1..count, writing **+0x50 first**
  (`:32,:34,:38`).
- `base+0x4c -= 1` @ 0x4ef642 (`:41`).
- validate the NEW head: `0x5a73f0(item, owner, base)` for items ≥ 0 (`:48`) / `0x5a6e70(|q|, owner,
  base, 0)` for negatives (`:58`); if unavailable → `jne 0x4ef5fa` (`:64`) **pop again** (discards
  stale/unavailable pending entries until one validates or the count hits 0).
- new head ≤ −39 → `0x446250(0x24)` (project command recorder, `:73`); then redraw
  `0x473760(base_x, base_y, 2, 2)` (`:82`) and `return 1` (`:84`).
Its callers are ONLY three sites inside the pipeline: **0x4ef992, 0x4f037b, 0x4f0f46**
(`evidence/m53a_fn_disasm.txt:195, :827, :1611`; Ghidra `shard_012.c:21026, 21283, 21493`).

**2. LIVE, run 1 (m53c):** QPIPE st=200 head=2 count=1 (`evidence/m53c_watch.log:144`) → QCOMPLET
(`:145`) → SPENDA cost_edi=10 (`:146`) → CLAMP1 st=190 (`:147`) → **WP50 `eip=0x4ef62e` Old 2 → New
3** (`:154`, gdb's own Old/New block at `:151-153`) → **WP4C `eip=0x4ef648` Old 1 → New 0** (`:161`).
Later visits of the same run: head **3**, count 0, st 0 (`:260`, `:312`) — the promoted slot-1 item is
what the base now builds, and `+0x44` mirrors it (`f44=3`). ZERO hits at all six re-pick sites and at
the tail clear 0x4f1e3f (counts in the log: REPICK_* 0, QDRAIN 0).

**3. LIVE, run 2 (m53c2) pinned the call site:** `POP_MID 1 f50=2 f4c=1` at **0x4f037b**
(`evidence/m53c2_watch.log:38`) fires immediately after CLAMP1 (`:37`) and immediately before the
shift store (`Old value = 2 / New value = 3 / 0x004ef62e`, `:42-45`); `POP_EARLY` (0x4ef992) and
`POP_LATE` (0x4f0f46): 0 hits. Year 2370→2371, next visit head 3 / count 0 (`:47`).
**The fork that chooses pop vs re-pick** (file-target gdb disasm, 0x4f033e-0x4f037b):
`[base+0x30] |= 0x800000`, `[base+0x30] &= 0x7fffffff`, then `mov bl,[ebp-0x2c]` (= 1<<owner, set at
0x4ef815) `mov al,[0x985b10]` `test bl,al` → **nonzero (owner IN the event mask) → 0x4f0375 `push
base_idx; call 0x4ef5d0` (POP); zero → 0x4f0367 `push 0; push base_idx; jmp 0x4f0589` → `FUN_004e5ae0`
(RE-PICK)**. Our owner 3 ∈ mask 0xff08 ⇒ pop path ✓ (and REPICK_A @ 0x4f0589 = 0 hits in run 1).

**4. +0x4c REINTERPRETED — it is the PENDING-entry count, not a "last used index"** (M53a's label,
corrected). Total entries = **+0x4c + 1**: head at +0x50, pending at +0x54 … +0x54+4·(count−1); the UI
caps count at 9 ⇒ 10 entries = the +0x50..+0x73 array ✓. Every drain agrees: `0x4ef5d0` shifts
`count` slots then decrements; `FUN_004f4060` iterates `[+0x4c]+1` dwords from +0x50
(`evidence/m53c_fn4f4060_pseudocode.txt:269-278`), and `FUN_005437d0` (`evidence/m53c_setters_pseudocode.txt:176-198`)
and `FUN_00507ef0` (`:199-217`) both loop `base+0x4c + 1` times over the same window decrementing item
counts. Consequence, **closes M53a open (a)**: with `+0x4c == 0` nothing consumes the head — 0x4ef5d0
returns 0 at its gate — so a payable head re-completes EVERY round (M45's units 1→6 off one standing
queue; M53a's head=2 unchanged over 3 rounds). The standing item a player sees IS the repeat-build
state; the queue only advances when the player has appended pending entries.

**5. Census of +0x50 writers** (static, `evidence/m53c_setters_pseudocode.txt`; live counts from
`evidence/m53c_watch.log`):
- `FUN_004e5560` (`shard_012.c:14625`, excerpt `evidence/m53c_setters_pseudocode.txt:1-44`) = the ONLY
  setter: head := new, early-return if unchanged, item count old−1 / new+1; its only callers are the
  3 sites inside `FUN_004e5ae0`.
- `FUN_004e5ae0(base, param2)` = "re-pick the head" via `FUN_004f6030` (the 30,475-byte AI build
  planner, `shard_012.c:24338`) — excerpt `:45-129`. Live: 122 SET_REPICK + 122 SET_HEAD hits in 3
  rounds over 40+ bases (idx 47 ×29, 46 ×9, 74 ×6 …), **0 for idx 70 (ours)**. New heads observed:
  85/153/149/72/84/164/152 (facility ids ≥ 0x40) and **−29 ×7** — a negative outside the −(39+project)
  band, unexplained.
- `FUN_004e46f0` (base-creation autocalc: writes 2, then scans the 52-B type records for the best
  pick, excerpt `:130-175`) and `FUN_004e47d0` (base init) seed +0x50.
- Clears/re-picks that did NOT fire for us: `0x507ef0` 1 hit, base 46, not ours
  (`evidence/m53c_watch.log:247`); `0x5437d0` 0 hits; tail clear 0x4f1e3f 0 hits (needs head == −|q|
  ∧ +0x4c == 0); pipeline re-pick sites 0x4ef87e / 0x4f0589 / 0x4f08d4 / 0x4f09b6 / 0x4f1e01 /
  0x4f21b8 all 0 hits (0x4f1e01 needs (f38&1 ∧ f38 sign) ∨ owner ∉ mask; ours f38 = 0x00dfbe41).
- UI enqueue `FUN_00417ee0` (0 live hits — no base-screen interaction this run) writes ONLY slot 0
  (`shard_001.c:9452`, excerpt `:218-251`) and adjusts +0x4c (`:9258` dec, `:9429/:9434` set/inc, cap 9).

**6. Ops lessons.** (i) The `ours=` flag printed at the 0x4e5ae0/0x4e5560 entries is USELESS: while
those run, `*(int*)0x68cbb0` (cur base index) IS their param_1, so it is always 1 — compare against
the located base INDEX (ours = 70). (ii) Both drivers ran clean with 2 hw watchpoints + 17 soft bps
(`scripts/m53c_drive.py`, `scripts/m53c2_drive.py`); the +0x50/+0x4c watches replaced +0x3c/+0x40 and
gave gdb's own Old/New pairs, which is the cheapest possible writer proof.

**7. Opens.** (a) **Who writes the PENDING slots +0x54..+0x73?** No function in the corpus writes
base+0x54 by symbol (`DAT_0095da64`: 0 hits) or by short-alias (`DAT_008f0d60 + 0x2a`: 0 hits); the
append must come through a walked pointer. Leads: `FUN_00417ee0`'s pane callers
(`shard_001.c:2155, 2204, 8535, 12265`) and `FUN_0059ce10` (`shard_015.c:14416, 14770`), which seeds
`+0x4c = pop·10/2` (= 35 at pop 7 — over the UI cap 9, so either that path is scenario/load setup or
the cap means something else). (b) the −29 head value. (c) the branches at 0x4ef992 / 0x4f0f46 (never
fired in either run). (d) base+0xc0 = 7 == pop, still unresolved.

Next: **M53d** (the queue APPEND: who writes the pending slots, via the base-production pane callers of
`FUN_00417ee0`), or **M53b** (the +41 byte: production weight vs the autocalculated +43 cost). Footing
rewritten in NEXT_PROMPT.md (session 55).

## Session 55 (2026-10-23) — M53d: THE PENDING-QUEUE WRITER IS `FUN_00417d20` — 0x417e04 `mov [base + slot·4 + 0x50], item` (hw-watchpoint: `pc=0x417e08`, +0x54 3→2, +0x4c 0→1); `FUN_00417ee0` itself rewrites ALL TEN slots on chooser-cancel at 0x418636; every writer is REGISTER-indexed, which is exactly why the literal-offset census found nothing

- **The census blind spot (M53d's premise was an artifact, not a fact).** `DAT_0095da64`: 0 hits and
  `DAT_008f0d60 + 0x2a`: 0 hits because NOBODY stores to a literal `+0x54`. The three real writers are
  `mov [eax+edx*4+0x50], ebx` (0x417e04, index in a register), `mov [eax+esi*1], edx` (0x418636, offset
  walked 0x50→0x74 in a loop) and `mov [eax+ecx*1], edx` (0x418751, walked the same way). Grep for the
  *store shape* (`*4+0x50`, `+eax*1]`, `rep movs`) before concluding a field is unwritten.
- **`FUN_00417d20`** (0x417d20, 302 B, `index.csv` row 354, Ghidra `shard_001.c:8833`, disasm
  `evidence/m53d_fn417d20_disasm.txt`) is the queue-slot editor. `edi = [ecx+0x3ff5c]` = the **UI-selected
  slot index** held in the base pane's UI object (`ecx = this`, `:6`); `[ebp+0x8]` = item id (→ `ebx`),
  `[ebp+0xc]` = **insert-vs-replace flag**. Stores: **0x417e04** `mov [eax+edx*4+0x50], ebx` writes
  `queue[ui_slot]` (slot 1 → +0x54 … slot 9 → +0x74) — `:75`; **0x417dd8** insert-shift `queue[k] :=
  queue[k−1]`, k = 9 down to slot+1, only when param_2 ≠ 0 (`test [ebp+0xc],0; je 0x417dfe` 0x417dbb) —
  `:62`; **0x417dad** delete-shift (negative/secret ids) — `:49`; count stores 0x417df6 (cap 9) `:72` and
  0x417e1d (`count := count+1` when slot > count) `:83`. Slot 0 (`edi == 0`) and slot 9 early-return at
  0x417d2b/0x417d33 — the head is not edited here. Its only corpus caller is `shard_001.c:9275`, inside
  `FUN_00417ee0`.
- **The dispatch is a chooser-mode jump table.** `FUN_00417ee0` reads `[pane+0xb194]`, `dec`, `cmp 6`,
  `ja 0x4187be`, then `jmp [eax·4 + 0x419c04]` (`evidence/m53d_jumptable.txt`: modes 1..7 → 0x418c51,
  0x418cc9, 0x418cd8, 0x418703, 0x4187a2, 0x418703, 0x4187ad). **Mode 5 → 0x4187a2** pushes 1 and
  **mode 7 → 0x4187ad** pushes 0, both falling into 0x4187b6-0x4187b9 `push item; mov ecx,pane;
  call 0x417d20` (`evidence/m53d_fn417ee0_disasm.txt:550`) — i.e. mode 7 = REPLACE in place, mode 5 =
  INSERT with the shift. **Mode 4/6 → 0x418703**: if `slot ≤ [base+0x4c]` shift `queue[k] := queue[k+1]`
  (0x41874d-0x418751, `:514`) and `+0x4c--` (0x418766, `:521`) = REMOVE; if `slot > count` clamp the slot
  field and just redraw (0x41873a `call 0x416080`). Modes 1/2/3 (0x418c51/0x418cc9/0x418cd8, `:877, :913,
  :921`) funnel to 0x418cda → `0x43f470(0x71df20, owner)` availability test → `jmp 0x4184d7` = re-open the
  chooser. **Mode 0 skips the table entirely** (`ja 0x4187be`) and reaches only 0x4187ef (set
  `+0x30 |= 0x800000`, clear `+0x38 & 0x40000000`) then 0x418819 `jne 0x418b29` — the tail — **writing
  nothing**.
- **VERIFIED live, three independent ways** (our base idx 70 @ 0x962d30, UI window 10485761, gdb armed
  with hw-watchpoints on 0x962d84/+0x54 and 0x962d88/+0x58 plus ~20 silent printing bps, driver
  `scripts/m53d_drive.py --tag m53dN --mode arm --hold` in a tracked background job, stopped with
  `--mode stop`): clicking QUEUE row 1 (185,437) fires `ENQ param1=1 param2=1` — **param_1 IS the slot
  index** — opening the modal chooser (`call 0x496ad0` at 0x41860a, `:425`). Selecting Scout Patrol
  (icon 128,160) and pressing the bar at x=390 returns `POST_PICK edi=2`, `MODE mode=7 slotfield=1`,
  `D20#1 item=2 slot=1`, `D20_STORE dst_off=0x54 old=3 new=2`, and the watchpoint prints
  **`W54#1 pc=0x417e08 val_after=2`** — `$pc` sits one instruction past 0x417e04 ✓ — with `/proc/mem`
  agreeing: `+0x54 3→2`, `+0x4c 0→1` (`evidence/m53d7_watch.log:47-51`, reproduced identically in
  `evidence/m53d5_watch.log:48-51` with gdb's own `Old value = 3 / New value = 2` at `:55-56`).
- **The cancel-restore is the second writer, and it explains the phantom "refill".** The queue is
  snapshotted per call: 0x41820a-0x418222 `ecx=10; edi=[ebp-0x4c]; esi=[base]+0x50; rep movs` +
  `[ebp-0x20] = [base+0x4c]` (`evidence/m53d_fn417ee0_disasm.txt:179`). If the chooser returns −9999
  (`cmp edi,0xffffd8f1` 0x41861b) **and** param_1 ≠ 0, 0x418623-0x41863f walks eax 0x50→0x74 and writes
  `[base+eax] := snapshot` (0x418636, `:438`), then restores `+0x4c` from `[ebp-0x20]`. Caught live:
  ten `RESTORE off=0x50..0x74` lines with `W54#2 pc=0x418639 val_after=3` landing exactly between
  `off=0x54 snap=3` and `off=0x58`, followed by `POST_PICK edi=-9999` / `BRANCH_EXIT`
  (`evidence/m53d7_watch.log:52-64`). This is what makes +0x54 "come back" to 3 after a remove: it is not
  a refill, it is the rollback of an aborted chooser.
- **Empirical bar → mode map** (x-coords in window space, bar row y≈343; the labels the vision pass reads
  are HELP|OK|REPLACE|INSERT|DELETE|CANCEL but the label↔mode pairing is NOT label-verified): x=275 →
  mode 0 (no write), **x=390 → mode 7 → store in place (the append)**, x=505 → mode 4 → remove-shift +
  count-- (memory: `+0x54 2→0`, `+0x4c 1→0`, `evidence/m53d5_watch.log` after-state), x=618 → −9999 →
  restore, x=160 → mode 1 → chooser re-opens (`evidence/m53d8_watch.log:47-48`), x=707 and Return →
  nothing. **Digit keys 1-9 are preview-only**: `FUN_00512b40` calls `FUN_00417ee0(digit, 0)` so param_1 ≠
  0 → mode 0 → the tail, and the pick is dropped. That is why every digit-key attempt in this session
  looked like a silent failure (`POST_PICK edi=2 / MODE mode=0 slotfield=0`,
  `evidence/m53d3_watch.log:42-44`).
- **Complete writer inventory for `+0x54..+0x74`** (the pending slots): 0x417e04 (slot store, VERIFIED),
  0x417dd8 (insert-shift, INFERRED — mode 5 never triggered live), 0x417dad (delete-shift, static),
  0x418636 (cancel-restore ×10, VERIFIED), 0x418751 (mode-4 remove-shift, VERIFIED by state change, not
  watchpoint-captured), plus the known pop shift 0x4ef628-0x4ef639 (M53c) and the +0x50-only writers
  `FUN_004e5560` / `FUN_004e46f0` / `FUN_004e47d0`. `+0x4c` writers: 0x417df6, 0x417e1d, 0x418766,
  0x418641-0x418649 (restore), 0x4ef642 (pop).
- **Harness pitfalls learned (now in the skill):** (1) a gdb watchpoint with **no `commands … continue`
  block** makes `gdb -batch` reach its prompt, end the script and **detach silently** — the rest of the
  run is uninstrumented and the log looks truncated; always give watchpoints a printing `continue` block.
  (2) gdb's own messages are unbuffered while breakpoint `printf` output is block-buffered, so the two
  streams interleave out of order in the log — attribute events by CONTENT (counters, off= sequences),
  never by line order. (3) the vision pass reports true window pixel coordinates; tesseract TSV
  coordinates are internally rescaled and must not be halved — settle geometry with a crop-and-OCR test.
  (4) arm gdb only from a `background=true` call with the driver's `--hold` polling parent (Hermes kills
  children of a finished foreground call).
- **Open threads.** Mode 5 (the 0x417dd8 insert-shift) is proven reachable in code but was never fired
  live — the bar that sets `[pane+0xb194] = 5` is still unidentified, and the 8 visible QUEUE rows vs the
  cap-9 count is unexplained. The bar-label ↔ mode pairing needs a label-verified pass. The −29 head
  value (M53c), the 0x418cda availability test, and `FUN_0059ce10`'s `+0x4c = pop·10/2` (35 > cap 9) are
  all still open.
- **Next:** `NEXT_PROMPT.md` rewritten for session 56; **THE PICK = M53b** (what the type-record `+41`
  byte actually is, static-friendly).
