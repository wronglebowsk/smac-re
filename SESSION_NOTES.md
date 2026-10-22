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

## Session 28 (2026-10-21) — M28: the click-to-move gate is a pane mode, not a gesture
- Came in wanting click-to-destination (C2). Answer found instead: `FUN_00476580` writes order `+17 = 0x18`
  **only** when `[this+0x1ef4c] == &DAT_0091cae4` (map-pane mode 9). `this = [0x7cdecc] = 0x8f79e0`; live on the
  HUD that pointer is **0**, so every left click falls into the base/`DESTTRIAD` branch and issues nothing.
- Live proof: bps on the three stores `0x476ac7/0x476bae/0x476c39` + the three early returns
  `0x47674d/0x476778/0x4767ab`; clicks at (480,250) and (470,300) → `MAPH p1=0x1e0 p2=0xfa p3=0 this=0x8f79e0
  wmode=0`, zero store hits, zero early-return hits (`evidence/m28_gates.log`, `m28_gates2.log`).
- Pane mode table is `&DAT_0091c958 + idx*0x2c` set by `FUN_0050ba00/90`; corpus callers pass 8/0xb/10 only,
  so mode 9's setter is unattributed = the next lead.
- Correction logged: `FUN_004d6fb0(unit,0x18,flag)` (order-menu `0x67`; key `j` = case 0x6a) targets a
  **base** tile, not an arbitrary tile. `FUN_00512450` is the order-menu command dispatcher (0x42..0x73).
- Shift+arrow `0x19` needs an order-menu context (`local_28 != 0`), so it can't be driven from a bare HUD.
- Tried and rejected: bottom action-bar clicks (mode stays 0), plain right-click on map centre (no menu; an
  earlier right-click pair opened a DISBAND confirm — Escape cancelled it, no unit lost), 'j' (base move).
- New tools: `scripts/m28_probe.gdb` (gate + store bps), `scripts/m28_order.gdb` (order/watchpoint variant),
  `scripts/m28_click.sh X Y LOG [GDBFILE]`. Evidence: `evidence/m28_clickgate.txt`.
- Left running: pid 914079, year **2201** (advanced during the session's key presses), our turn, HUD clean, TracerPid 0.

## Session 29 (2026-10-21) — M29: state-driven turn driver, 11/11 turns
- Chased the click-to-destination gate one step further: mode 9 is chosen in `FUN_0050a770` (0x50a770) as
  `Ctrl held ∧ 0x91b5b8 == 0 ∧ 0x91b6fc == 0`, then copied to `[this+0x1ef4c]`; live it never fires because
  `DAT_0068d84c` (active pane index) is **-1** — the pointer never registers as "inside a pane" under xdotool.
  Left as the open lead; documented in `turn_driver.md` §M28 + `NAMED.md`.
- Delivered instead: **turn-driver hardening**. `service_turn` now reads `player`/`cur_player`/`turn_flags`
  each loop; during the AI phase it only services modals (`Return` for DATALINKS/PSI/event pages, one
  `Escape` for OPERATIONS DIRECTOR / base panes) and never clicks TURN COMPLETE.
- Proof: `evidence/m29_3turn.log` 2202→2205, `evidence/m29_8turn.log` 2205→2213 — 11/11 turns, 0 stalls,
  7.4–12.9 s each; turn 5 hit an AI-phase CHIEF PLANETOLOGIST popup and still flipped in 12.3 s.
- Also learned: repeated Escape/Space presses can advance the year on their own (2199→2201→2202) — the turn
  loop is not the only way to flip a year; always re-read `year` before attributing an advance to the driver.
- Left running: pid 914079, year 2213, our turn.

## Session 30 (2026-10-21) — M30: the turn loop model, traced for 20 turns
- New tool `scripts/turn_trace.py`: samples year/cur_player/turn_flags/n_bases every 0.2 s while the driver
  runs, logs only changes, prints a per-year player sequence.
- Ran 20 turns, 2213→2233, **20/20 OK**, 201.2 s total. Model: our phase = `tf==0 ∧ cur==player(3)`; TURN
  COMPLETE sets `tf|=2` and the engine walks the AI factions through `cur_player` (observed 0,1,2,4,5,6,7 —
  never 3); year increments once per complete cycle. AI phases = 34.9 s (17 %); the rest is our OCR/click loop.
- Artifacts: `evidence/m30_turn_trace.jsonl` (67 changes), `evidence/m30_summary.txt`,
  `evidence/trace_20261021_131002.jsonl`.
- Side discovery: the base array (51 records now) has **no faction-3 bases** — counts are {1:10, 2:13, 4:5,
  5:8, 6:7, 7:8}. The human faction in this save owns zero bases (units only), so C3 (base economy) cannot use
  the player's own base; it would have to model an AI base. Faction byte is **+4 (byte, not u32)**; +1-based
  "founding order" byte at +5.
- Left running: pid 914079, year 2233.

## Session 31 (2026-10-21) — M31: base record map v1 (pop, growth, minerals)
- New tool `scripts/base_trace.py`: snapshots the whole base array every year-change while the driver runs,
  then diffs u16 lanes of a tracked base. Two runs: 2233→2243 and 2243→2251 (18 turns, all OK).
- **Index is not identity**: base records slide in the array — tracking index 0 silently became a different
  base, index 1 jumped three fields at once. Track by the name at +19.
- **Layout corrected**: faction is the byte at **+5**, flag at +4 (u16 = `flag | faction<<8`); earlier docs
  said "faction at +4". Also named: +6 population (3–7), +7 growth countdown (6→0 one per year), +60 per-base
  turn counter, **+64 mineral accumulator** (mirrored at +152 in all 62 bases).
- **Measured**: Gaia's Landing minerals ≈5–10/turn with resets 54→5 (quarter carryover) and 73→0 (U.N. HQ
  ≈6–8/turn). First live base-economy numbers.
- **Negative result worth keeping**: our own base changed hands at 2239 (faction 3 → 6) and we now own **zero**
  bases; also only 5/152 lanes moved over 11 years for a quiet base → the record is base *state*, not the
  per-tile accounting.
- Left running: pid 914079, year 2251.

## Session 32 (2026-10-21) — M32: the order menu map, live-verified 21/21 keys
- New tool pair: `scripts/m32_keys.gdb` (29 entry breakpoints: key router, order dispatcher, all 20
  order setters, executor/SETTILE/ACT/ATTACK/pane-mode setters) + `scripts/m32_run.sh`
  (`M32_KEYS="…"` presses keys with per-key unit-record snapshots). Deliverable: **`ORDERS.md`**.
- **Key model proven live**: `FUN_00512b40(char, VK|modifiers)`; dispatcher receives
  `(char, tolower(char), VK|flags)` — `FUN_0064d300` = tolower (M→0x6d, G→0x67); numpad VKs
  0x60–0x69 are the direction cluster (M24's "b c d f g h i" was a VK misread); Shift = bit 16,
  Ctrl = bit 17; menu rows arrive as `(menu<<8)|char` in param_3.
- **`FUN_004d44d0(unit, mode)` = issue_terraform_order**: mode = alpha.txt `#TERRAIN` index
  (`data/alpha.json` has all 20 rows + hotkey strings), order = **mode+4**; Former-class gate
  (`DAT_0098adb2[type*52] == 9`); payment debits **`DAT_0094d650[player*0x82f]`** (faction
  energy — first live address); rewrites 5→6 (Road→MagTube), 0→1, 0→0xa. Modes 0,2,3,5,7,8,9,
  0xc,0xd,0xe,0xf,0x10,0x11,0x12 all fired with predicted args.
- Named orders: `h` HOLD 2 (end-to-end: rec56 order 0→2), `l` Sentry 1 (`FUN_005ab420`), `o`
  Sensor/Convoy 3, `g` move-to-base 0x18, `G` join-base (`+46` = base idx), `U` unload, `r` Road,
  `d` bombard (`FUN_004d6100`), `p` waypoints+mode 8, menu 'R'/'T' → 0x1b/0x1c road/tube-to-base
  (`+20` = base index), menu 'D' designate (`+4 ^= 0x80`), 0x30055 give-unit, 0x20055 upgrade.
- **`/` = clear + EXPLORE** (walks toward unexplored: `EXEC 56 dir=7 mode=3` → (43,9)); run 1
  unit 57 explored onto an **alien artifact** (42,12) → OPERATIONS DIRECTOR modal.
- **Modal = key sink, mechanism found**: while a modal is up the pump never calls
  `FUN_00512b40` — 19 keys after the modal produced zero hits. Check screen class first.
- Left running: pid 914079, year 2251, our turn, HUD clean, TracerPid 0; rec56 exploring at
  (43,9) (mp=3), rec57 on the artifact (42,12) (order 0x18, done), rec58 selected at (43,11).

## Session 33 (2026-10-21) — M33: the driver issues a real order (C2 closes)

- **C2 gate met**: `smac_play.py --order f` pokes `0x91b5bc`, presses `f`; the game's own
  chain fires (`KEY 0x66/0x46` → `DISP 0x66/0x66/0x46` → `TERRAF idx=53 mode=0` =
  `FUN_004d44d0`) and unit `+17` 0→**4** (Farm). The order byte **persisted across two
  turn advances (2252→2254) and a compaction slide (rec53→52)** — state reader only.
  Proof: `evidence/m33_try5.log`, `m33_turns.jsonl`, `m33_final_pre/post.json`.
- Order-store tail asm-pinned: store `0x4d5bbf` (`+17 = mode+4`), broadcast `0x4d5bc6`,
  TERRAPAY pane `0x4d55a8` (blocks inside the setter), energy debit `0x4d561a`
  (`0x94d650[player*0x82f]`); Farm/Road/Sensor **defer payment** (no pane, energy flat).
  Harness: `scripts/m33_order.gdb` (7 bps) + `scripts/m33_run.sh`; readers
  `scripts/m33_scan.py` (units/classes/energy), `scripts/m33_state.py` (pre/post JSON).
- Tile layout pinned: `0x92ae14 + (40*y + x>>1)*0x2c`, height `+0>>5` (Elev ≈ h*~100),
  mask dword `+8` (base bit 0, road 0x10, farm 0x20, fungus 0x8000).
- **Pitfalls (new)**: (1) /proc/pid/mem pokes are ghosts while gdb is attached — poke
  before arming, verify after CONT; (2) selection is game-owned — pokes get
  re-validated/replaced by the cycle within a frame; press the key immediately after the
  poke (only config that landed); (3) advisor panes are transient (1–2 s) and swallow the
  next input event (echo `0x20011`) — rejections look like dropped keys; (4) pixel↔tile
  mapping ≠ naive lattice — calibrate via the HUD tile-info panel, not formula.
- **Open (M34)**: the Farm order never executed (cycle skips already-moved/order units;
  Space ran the cycle's unit, `SOLOWRAP idx=<cycle>`), so the tile improvement + energy
  debit are still unobserved. Next: get the order onto a unit the cycle selects (fresh
  turn / native PICKUNIT click-select) and watch `+8` + energy.
- Left running: pid 914079, year **2254**, our turn, HUD clean, TracerPid 0; Former rec52
  (45,11) carries the driver's Farm order (byte 4); rec56/57 still exploring.

## Session 34 (2026-10-21) — M34: the execution-trigger hunt (orders cancel at end-of-turn)
- **Headline negative, well-evidenced:** a Farm order issued through the game's own selection
  (HOLD-walked cycle 50→233→46, then `f` → `TERRAF idx=46`, order byte 4) **clears at the
  end-of-turn boundary with no tile improvement and no energy debit** (40→40;
  `evidence/m34v6_run1_watch.json`). C2's "improvement appears" half is still unobserved.
- **Space IS the execute key (static H):** `FUN_00512450 case 0x20 → FUN_004d1e90(sel)` →
  can-act → `FUN_00529090(u,-1,0)` → solo `FUN_00585720(u, 0x8-sentinel, 3)`; never caught live
  (panes swallow the follow-up key; selection unsteerable under a tracer).
- **Eligibility remap explains the (45,11) rejections:** Farm on `tile+8&0x20 ∧ terr≥4` remaps
  mode 0→0xa; mode 0xa needs unit ability `0x2000` (plain Former lacks it) → picker branch →
  HASFARM advisor abort **before the store** (`m34_try2_gdb.log` matches the signature 5/5).
- **Pitfalls paid:** (1) `/proc/pid/mem` WRITES are dead while a tracer is attached (try3 proof:
  poked sel=46, TERRAF hit idx=50); (2) gdb bp **conditions must cast** `*(int *)($esp+4)` —
  bare `$esp[1]` throws "generic pointer" at first hit and kills the batch script (try1, v7_run1);
  (3) selection is fully game-owned: idle pump + Return/plus/Tab never move it; only a completed
  action (HOLD) advances the cycle; (4) **retract** M33's tile-mask reading at (45,11)/(45,7) —
  tile record content proved unstable across snapshots (`0x20ff…` ↔ all-zero at the same address).
- Tools: `scripts/m34_exec.gdb`+`m34_run.sh`, `scripts/m34_chain.gdb`+`m34_chase.sh` (12-bps
  store→bcast→enqueue→drain→dispatch→executor chain watch), `scripts/m34_exec_watch.py`,
  `scripts/m34_cycle_issue.py` (the HOLD-walk that landed the order). Docs: `turn_driver.md`
  §M34, `NAMED.md` M34 block, `MILESTONES.md` C2 addendum.
- Left running: pid 914079, year **2266**, our turn, sel=-1, pending=1, TracerPid 0; Former rec44
  at (45,7) order 2 (HOLD); all survivors HOLDed/explored; energy 40. Next (M35): catch the
  picker answering *inside* the setter (OCR the pane, click "Expend", never blind Return) or the
  Space chain in a pane-free window — `scripts/m34_chain.gdb` is armed for it.

## Session 35 (2026-10-21) — M35: the terraform pay picker caught and answered (backfilled note)

Detail §M35. Pay path live (EnvEcon poked): TERRACOST 9 → picker → DEBIT 40→31 synchronous →
TERRAFORM pane; **no STORE** — the setter left through a footprint-pass exit; tile-base pointer
`0x92ae14` correction landed. Left: pid 914079, pane open, order 0, energy 31.

## Session 36 (2026-10-21) — M36: no refuser — the tutor pane ate M35; the order is STORED; execution is the new wall

- **The "refuser" was the one-time TERRAFORM tutor pane.** `0x4d58a4 call 0x4c2be0(0x800)` is a
  once-per-game solo latch; the first raise attempt shows the tutor via the **blocking**
  `call 0x48ef40` at 0x4d58c6. The setter parks *above* `STORE` until the pane is dismissed
  (OK at (400,408)) — M35's harness killed gdb while it was open, so "no STORE, no refund,
  no failure pane" was just a frozen setter. Preflight screenshot `m36_screen0.png` caught it.
- **Store tail caught live** (`m36v1_gdb.log`): `PANERET → AFTERLATCH(mode 0x10 skips the
  terrain gate) → LOCKCHK(0x91f718=0) → LOCKRET eax=0 (0x528930 = pass-through in solo) →
  STORE +17 = 0x14 → BCAST → ENQ q=17 idx=41`. No double-debit (energy stays 31).
- **Footprint pass decoded**: raise ladder `0x678e08 = [−13,−14,−15,1,9,25,49,81][height+1]`
  (elev 4 ⇒ 5×5 = 25 tiles), lower `0x678e18`; x wraps, off-map tiles skipped; foreign-owned
  tile + relation&7 ⇒ `0x555030` pact = instant refuse / treaty-truce confirm; refuse ⇒ refund
  blocks `0x4d58dc`/`0x4d59c7`. `0x4e3b50` = tile border-owner query. `0x582ed0` = tile mask set/clear.
- **New wall: execution.** `DRAIN 0x5262e0`/`DISP 0x52bce0` never fire in solo (3 rounds — the
  enqueued 0x2101 events have no solo consumer). Probe round 2272→2273: executor `0x585720(unit,
  dir, 3)` fired **183×, zero for unit 41** (`m36_execprobe_gdb.log`) — the turn machinery filters
  the ordered unit out; mpused=3 persists across turns (can-act gate `0x5acc00` suspect).
- UI facts: **ENDOFTURN1** pane = "Press ENTER for next turn" (Return advances, not a confirm);
  **Escape on a bare HUD opens REALLYQUIT** — svc loop hit it live, recovered via "Oops, no,
  wait!" (400,260) + OK (400,307).
- New scripts: `scripts/m36_store.gdb` + `m36_dismiss.py` (store tail, works),
  `scripts/m36_exec.gdb` + `m36_exec.py` (turn-end + modal svc), `scratch/m36_probe_exec.gdb`
  (unconditional executor probe). Docs: §M36, NAMED.md M36 block, MILESTONES.md C2 M36 addendum,
  skill `references/terraforming-order-path.md` updated.
- Left running: pid 914079, year **2273**, our turn, HUD clean, sel=-1, energy 31, TracerPid 0;
  Former rec41 at (45,7) **order 0x14 (stored raise)**, mpused 3, tile elev 4 unchanged.
  Next (M37): why the executor skips unit 41 — mp/+40 semantics after a stored terraform, and
  whether `Space` on the selected unit still executes the stored order.

## Session 37 (2026-10-21) — M37: the execution wall falls — terraform is a multi-turn accumulator; the stored raise completed live (elev 4→5)

- Two sessions contributed: an earlier 37a/37b run (22:21–22:27, died before checkpointing, left
  REALLYQUIT open) and this one (recovery + push to completion). Found `scratch/m37_exec41.gdb`
  + `scripts/m37_exec41.py` + evidence `m37a_*`/`m37b_*` from the earlier run already on disk.
- **Mechanism (H)**: terraform execution = `0x50ef60` pump → gate `0x5acc00` (`0x5ac650(unit,0) >
  mpused`) → `0x529e70(unit,0)` (solo ⇒ direct) → `0x4d1200(unit)` → `0x4cce50(unit, k, 1)`:
  consume-all `0x5acdb0` + `unit+37 += 2`/turn (chain-fold Σ) until `accum ≥ 2×terrain_table[k].+8`
  (runtime table `0x6938f0+k*32`; `+8` == alpha `#TERRAIN` field 5; raise 12 ⇒ 24 work ⇒ 12 turns;
  `+18` = required tech = 59 ✓ M35) → COMPLETE: order+chain cleared, mask swap, `0x5ad400` RAISE →
  `0x5ad0a0` SETELEV new=5. `0x51f730` REFRESH (mpused=0 etc.) fires **per player per round in solo**
  (live REFRESH events) — called by round sequencers `0x520c10`/`0x521070` that also drive `0x51e700`.
- **Completion (H, live)**: `CHECK accum_new=24 threshold=24 → COMPLETE unit=2028 x=45 y=7 mode=16 →
  RAISE x=45 y=7 → SETELEV x=45 y=7 new=5` at year 2281; post: order 0, work37 0, **tile elev 5**,
  energy 31 unchanged, unit slid 41→40→39 (tracked by order). M36 retracts: mpused "persistence"
  (re-charged each turn after REFRESH) and "executor filters the ordered unit" (`0x585720` = wrong
  door). 0x2101 queue = netplay replication, no solo consumer (holds).
- Harness fixes landed in `scripts/m37_exec41.py`: REALLYQUIT special-case (`answer_confirm`
  defaults to y=196 = pane artwork for that pane; rows are 260/281, OK +47 — recovery verified
  live via `scripts/m37_recover.py`); Escape only when `region_colors < 130` (pane-over-map);
  ENDOFTURN1 → Return; **bare-HUD-on-our-turn stall → TURN COMPLETE click every round** (m37c
  stalled at 2276 otherwise). `m37_exec41.gdb` moved scratch→scripts (durable).
- Docs: §M37, NAMED.md M37 block (+3 corrected rows), MILESTONES.md C2 addendum, skill footing +
  `references/terraforming-order-path.md` updated. Evidence: `m37a_*`, `m37b_*`, `m37c_*`,
  `m37c2_*` (completion run), `m37_recovered.png`.
- Left running: pid 914079, year **2281**, our turn, **ENDOFTURN1 pane open** (Return advances),
  TracerPid 0, energy 31; former (45,7) order 0 mpused 3 (already moved this turn), tile elev 5;
  gdb detached clean. Next (M38): re-issue from the driver (second raise at elev 5 = 81-tile
  footprint ⇒ first foreign-border/diplomacy test, or lower back), and/or two-Former chain
  (4 work/turn ⇒ 6 turns), and/or Space-on-Former semantics.

## Session 38 (2026-10-21) — M38: driver issues a second raise end-to-end; cost formula decoded live; tile (45,7) reaches elev 6 at year 2293

- `scripts/m38_issue.py` + `scripts/m38_issue.gdb` (34 bps = m35 pay chain + m36 store tail +
  footprint/diplomacy sites `0x4d5839`/`0x4d58dc`/`0x4d59c7`/`0x4d5add`/`0x555030`) issued a
  second Raise Land from the driver first try: ENDOFTURN1 Return (2281→2282) → **selection
  recipe** (cycle picked another unit → poke `+40=255` on all other own order-0 units →
  `Escape` → pump auto-selected the Former) → `]` → `TERRAF → TECHCHK 1 → ORDERCHK 0 → COST 16
  → TERRACOSTUP → TERRAPAY → PAYTAKEN → DEBIT 31→15 → footprint (49 tiles 7×7, ZERO
  PACTCHK/DIPLO/REFUND) → AFTERLATCH (latch consumed → PANERET silent, M36 predicted) →
  LOCKCHK 0 → LOCKRET 0 → STORE 0x14 → BCAST → ENQ` (`evidence/m38a_*`).
- **Cost formula (H)**: `0x4cc7b0(x,y,player)` = `(|elev−3|+2)²` ×3-fungal, × base-distance
  (inert for player 3: base+4 = faction ID ∈ {1,2,4,5,6,7}, never 3 — mapping open), `/2` if
  trait bit `0x2000` (clear), always `/2`, clamp 1..30000. Fits both points: 9 @ elev 4,
  **16 @ elev 5**. Prediction: elev-6 raise/lower = **25 > 15 energy** ⇒ next terraform gated
  by economy. Energy flat between debits (income ≈ upkeep, ≈ +0/turn) — feeds C3.
- **Completion** (`m38run2`): work37 4→24 (+2/turn; issue turn executes too — pump runs the
  order right after STORE), `CHECK 24/24 → COMPLETE unit=1872 → RAISE → SETELEV new=6`; mem
  verified: **elev 6**, order 0, energy 15, year 2293, tracer 0. 12 executions 2282..2293 =
  24 = 2×12 ✓. Re-erosion lifted 8 neighbours 4→5 (leveling erodes toward the plateau).
- **Diplomacy branch: armed but clean** — elev-5 footprint (49 tiles, x 42..48 y 3..11) hit no
  foreign-owned tiles; pact/treaty/refusal path remains untested (needs elev-6's 9×9 + 25
  energy). NEXT_PROMPT's "81 @ elev 5" corrected: 49 = idx 6, 81 = idx 7.
- Harness: `m37_exec41.py` preflight relaxed (selected-unit panel ⇒ `classify` unknown with
  garbled strip OCR is fine on our turn; svc loop ends the turn — `svc_hud_clicks=5`); picker
  Expend-row click auto-confirms; `wait_for` races gdb's block-buffered printf (post-kill log
  authoritative). Docs: §M38, NAMED M38 block, MILESTONES C2 addendum, skill footing +
  `references/terraforming-order-path.md` updated.
- Left running: pid 914079, year **2293**, our turn (cur=3), screen `unknown` ncolors=150
  (no pane over map; likely unit panel/bare HUD — re-probe on load, ENDOFTURN1→Return),
  TracerPid 0, energy **15**; Former (idx 36 at load-scan-time, slides) at (45,7) order 0
  work37 0; tile elev 6; EnvEcon bit still published; tutor latch consumed. Next (M39):
  cheap-mode completion sweep (road threshold 2 ⇒ 1 turn; check `table[k].+18` tech gates
  first via `scripts/m35_gate.py`), economy-rate idle measurement (gates the 25-cost
  terraform), player↔faction-ID mapping (static), Space-on-terraform semantics.

## Session 39 (2026-10-21) — M39: Road — second mode proven; issues with no cost block; 2-execution completion; live threshold ladder from AI events

- `scripts/m39_issue.py` (clone of m38_issue: Tab cycle, poke Former `+40=0` pre-cycle,
  menu-pending clear, picker optional, gdb = `m38_issue.gdb` + `m37_exec41.gdb` concatenated
  = 45 bps so a same-turn completion is caught) issued **Road** (`r`, mode 5, order 0x09) on
  the (45,7) Former: `TERRAF mode=0x5 → TECHCHK unlocked=1 →` **cost block fully skipped**
  (PAYPATH/ORDERCHK/COST/picker/SKIPPAY all silent) `→ AFTERLATCH → LOCKRET 0 → STORE 0x09 →
  BCAST`. No DEBIT — energy 15 before/after. Exec 1 same turn: `CHECK 2/4 → NOTYET`; exec 2
  next turn (2295): `CHECK 4/4 → COMPLETE unit=1872 x=45 y=7 mode=5`. Mem-verified: tile
  (45,7) **mask 0x108002→0x108006 (road bit 0x4)**, elev 6 untouched (mode 5 = mask swap
  only), order 0, year 2295, TracerPid 0 (`evidence/m39a_*`).
- **Live thresholds (AI + ours) confirm M37's adjustment formulas:** road **4** at elev-6
  tiles vs **2** at low elev (case-5 elev-class bump); solar 8 vs **16** (case 3 ×elev/2);
  mine 8; RemoveFungus 12. **AI terraformers work +3/execution vs our +2** — cause open
  (not ability bit0). Road at (46,42) completed on first execution (3 ≥ 2).
- **Key model corrected (H):** **`l` = SENTRY order key** (accidentally issued order 1 to the
  Former; turn auto-ended when every unit had an order — cleared by poking `+17=0`);
  **`Tab` = cycle/select-next** (sel −1→36, orders mode→1). Cycle **skips MP-exhausted
  units** (poke `+40=0` first — M38's consume-all had mpused=3). `0x91b5c4`
  order-menu-pending sticks at 1 — poke 0 before order keys. Mid-turn start (turn open, info
  panel up, mostly-black map ⇒ classify `title`/`unknown`): detect `cur==me`, go straight to
  selection. Empty cycle ⇒ ENDOFTURN1 ⇒ Return. Buffering race worked FOR us: cleanup fired
  after the full lifecycle, log holds both executions + COMPLETE + ~300 AI MASKSET/fog events.
- Tools: `m37_exec41.py` gained `--order <hex>`. Docs: §M39, NAMED M39 block, MILESTONES C2
  addendum, skill footing + `references/terraforming-order-path.md` updated.

## Session 40 (2026-10-22) — M40: MagTube remap proven live; first TECHFAIL — the tech-gate advisory is mode-specific (HASROAD)

- **Milestone (H, live, `scripts/m39_issue.py --tag m40a --key r` run as-is, 45/45 bps):** `r` on
  the Former at the now-roaded tile (45,7) (mask 0x108006 elev 6): `TERRAF mode=0x5` (key handler
  passes 5) → `TECHCHK mode=0x6 unlocked=0` (the remap inside `0x4d44d0` **rewrites the mode arg
  slot**) → `TECHFAIL 0x4d486e` → `ADVISOR/PANE id=HASROAD`. Rejected: no STORE, no cost block,
  no DEBIT — post mem-verified order 0, energy 15, tile 0x108006 unchanged, zero side effects
  (`evidence/m40a_issue.json`/`m40a_gdb.log`).
- **Static corroboration (shard_012.c body + live table reads):** remap condition
  `mode==5 ∧ tile.mask&4 ∧ cap[6+tile-seafloor]>−2` (cap table `0x6938e8`, idx `mode*8+flag`,
  MagTube land=**18**/sea=−2 live ⇒ land-only); farm rewrites `mask&0x20 ∧ elev≥4 → 0xa`,
  `mask&0x8000 → 1`. TECHFAIL advisory dispatch: 6→HASROAD (0x68c300) / 1→HASFARM (0x68c308) /
  else NOTUNTILTECH (0x68c310); Script.txt `#HASROAD`: "That square already has a road. Roads may
  not be converted to Magtubes until we discover $TECH0." $TECH0 closed live: fail branch →
  `0x5a69f0(&0x997120, tech_id)` (name from tech records `0x92fdb4+id*44`) → `0x626634(slot 0,
  text)` (slot table `0x99a01c`); post-run slot 0 = "Monopole Magnets", composed text in
  `0x997120`. Bypass: mode 0xa ∧ ability `0x2000` skips the fail branch.
- **Corrections:** terrain-table `+18` "required tech" is garbage (527) for k∈{1,5,6} — the cap
  table is the gate AND advisory source. Pre-gate silent exits: mode 6 w/o road bit, mode 1 w/o
  0x8000 (no advisory). NOTBASE/ALREADYBUILT checks named (static). MagTube terrain entry live:
  maskSET **0x8**, clear 0, work 3 (threshold pred. 6 pre-adjustment, unmeasured).
- **Harness:** runner ran unmodified on the reject path — STORE timeout → cleanup IS the expected
  terminal state for rejected orders; HASROAD pane transient (auto-dismissed); `poke readback
  mismatches` event is a false alarm when no other order-0 unit exists.
- Left running: pid 914079, year **2295**, our turn OPEN (cur=3=me), Former (idx 36 at scan-time,
  slides) at (45,7) **selected** (sel=36, orders_mode 1, order 0, work37 0, mpused 0); menu-pend
  `0x91b5c4` = **1 again** (poke 0 before order keys); tile (45,7) elev 6 mask 0x108006; energy
  **15**; tech-18 byte `0x985c1c+18` = 0 (unlocked=False); TracerPid 0; post-screen classifies
  `hud`. Scout Rover exploring; others Hold. EnvEcon bit 59 still published; tutor latch
  consumed. Next (M41): MagTube unlock-poke (`0x985c1c+18 |= 0x08`) + issue + completion (STORE
  0x0a, mask bit 0x8); generic NOTUNTILTECH live (`n` Condenser, tech 60); economy idle run;
  player↔faction mapping; Space-on-terraform. Docs: §M40, NAMED M40 block, MILESTONES C2
  addendum, skill footing updated, NEXT_PROMPT rewritten for session 41.
- Left running: pid 914079, year **2295**, our turn (cur=3), **ENDOFTURN1 pane likely open**
  (Return advances), TracerPid 0, energy **15**; Former (idx 36 at scan-time, slides) at
  (45,7) order 0 work37 0 mpused 3; tile elev 6 mask 0x108006 (road); Scout Rover exploring
  (queued-move order 0x18, damaged 20%, at (48,14)); EnvEcon bit 59 still published; tutor
  latch consumed. Next (M40): economy-rate idle run (gates the 25-cost terraform; feeds C3),
  MagTube remap test (`r` again on the now-roaded tile → mode 5→6 remap → TECHFAIL advisory —
  TECHFAIL bp already armed), player↔faction-ID mapping (static), Space-on-stored-terraform
  (sensor farm = 4 turns of build time).

## Session 41 (2026-10-22) — M41: MagTube unlock→issue→completion live — third mode done; the case-5/6 elev bump is +2 flat (threshold 8 @ elev 6)

- **Unlock (H):** poke tech bit byte `0x985c1c+18` `0x00→0x08` (bit 3 = player 3) with TracerPid 0,
  verified, gdb armed after; `m35_gate.py` shows MagTube land `unlocked=True`. Tech bits persist.
- **Issue (H, `scripts/m39_issue.py --tag m41a --key r` as-is, 45/45 bps):** `r` at (45,7) (roaded):
  `TERRAF mode=0x5 → remap → TECHCHK mode=0x6 unlocked=1` — **no TECHFAIL, no advisory** —
  `AFTERLATCH mode=0x6 → LOCKCHK → STORE order=0xa → BCAST`. No picker, no COST/DEBIT (no-pay
  path), energy 15 flat. **The STORE writes the REWRITTEN mode** (+17 = 0x0a, not 0x09).
- **Completion (H, `scripts/m37_exec41.py --tag m41b --order 0x0a --rounds 3`):** 4 executions over
  4 turns (2295→2298): `CHECK 2/8 → 4/8 → 6/8 NOTYET`, then **`8/8 → COMPLETE mode=6`**; tile
  (45,7) mask **0x108006→0x10800e** (magtube bit 0x8), elev 6 untouched (mask swap only), order +
  work37 cleared. MASKSET print capped at 300 hits — our swap silent, mem readback authoritative.
- **Correction:** MagTube threshold @ elev 6 = **8** = 2×3 **+2** ⇒ case-5/6 elevation bump is
  **+2 flat**, not doubling (road 2→4 @ elev 6 fits the same rule; M40's "may double ⇒ 12"
  falsified by the CHECK print). consume-all reconfirmed: mpused := 3 (full pool) for +2 work.
- **AI side-obs (O):** base 2×`+8` holds across condenser 24, raise 24, bunker 10, sensor 8,
  RemoveFungus 12, solar 8/12, road 6 — bumps >+2 at unmeasured elevations (open); AI accum
  **+3 on 7 formers but +2 on one** (idx 51, RemoveFungus) — "AI +3" not universal.
- **Harness (H):** both runners ran unmodified on the new mode (STORE detection order-agnostic;
  completion regex mode-agnostic). Evidence: `evidence/m41a_{issue.json,gdb.log,chain.gdb,pre,post}`
  + `m41b_{exec41.json,gdb.log,chain.gdb,pre,post}`.
- Left running: pid 914079, year **2298**, cur=3 (our turn — Former just completed ⇒ **ENDOFTURN1
  pane likely up, Return advances**), Former idx 36 at (45,7) order 0 work37 0 mpused 3; tile elev 6
  mask **0x10800e** (road+magtube); energy **15**; tech-18 byte `0x985c1c+18` = **0x08 — Monopole
  Magnets left UNLOCKED for player 3** (undo: clear bit 3); tech-60 byte 0x16 (players 1/2/4 have
  it, we don't); TracerPid 0, no gdb. Scout Rover exploring; others Hold; EnvEcon bit 59 still
  published; tutor latch consumed. Next (M42): generic NOTUNTILTECH live (`n` Condenser mode 0xc,
  tech 60 gated — runner as-is `--key n`); economy idle run; player↔faction mapping; HASFARM live
  (needs Former walked onto a `mask&0x8000` tile). Docs: §M41, NAMED M41 block, MILESTONES C2
  addendum, skill footing updated, NEXT_PROMPT rewritten for session 42.

## Session 41 continued (2026-10-22) — M42: generic NOTUNTILTECH live; $TECH0/$TERRAFORMTYPE6 substitution closed; tech-record +0 = display-name pointer; terraform op-name table decoded

- **Live (H, `scripts/m39_issue.py --tag m42n --key n` as-is, 45/45 bps):** `n` on the Former at
  (45,7): `TERRAF mode=0xc → TECHCHK mode=0xc unlocked=0 → TECHFAIL → ADVISOR #1 id=NOTUNTILTECH
  → PANE #1 id=NOTUNTILTECH`. Rejected cleanly — order 0, energy 15, tile 0x10800e, year 2298 all
  unchanged; STORE timeout → cleanup = expected terminal (2nd instance). Runner mid-turn dance on
  a fresh turn: poke `+40=255` (order-0 only), poke Former `+40→0`, Tab cycle → sel=36, menu-pend
  poke 0, one `n` → TERRAF. `evidence/m42n_*`.
- **Substitution (H):** Script.txt `#NOTUNTILTECH` = `The "$TERRAFORMTYPE6" operation cannot be
  performed until we discover $TECH0.` — post-run mem: slot 0 = "Ecological Engineering" (tech 60),
  slot 6 = "Construct Condenser", composed `0x997120` matches Script.txt verbatim. `$TERRAFORMTYPE6`
  = substitution **slot 6** (not mode index), set via `0x6265a2` (slot<10 setter, formats via
  `0x61482f`; sibling of `0x626634`). `$TECH0` is set by BOTH fail branches.
- **Corrections (H):** tech record `0x92fdb4+id*44`: **+0 = display-name POINTER** (heap arena:
  18→"Monopole Magnets", 60→"Ecological Engineering", 59→"Environmental Economics"), **+4 = short
  token** ("Magnets"/"EcoEng"/"EnvEcon"/"MilAlg") — M40's "name at +0" corrected. Terraform op-name
  table `0x94d2f8` = 14 × (land name, sea name, key char): Farm/Kelp Farm/`f` … Mag Tube/`R`,
  Bunker/`K`, Sensor/`O`, Condenser/`N`, Echelon Mirror/`E`; sea variants Mining Platform/Tidal
  Harness — the `$TERRAFORMTYPE` source; ORDERS.md key map confirmed.
- Left running: unchanged from M41 handoff — pid 914079, year **2298**, cur=3 our turn, Former idx
  36 @ (45,7) order 0 work37 0 mpused 0, tile 0x10800e elev 6, energy 15, tech18 byte 0x08,
  TracerPid 0. Next (M43): player↔faction-ID mapping (static; note MILESTONES C3 says base faction
  byte is **+5**, not +4 — resolve), then economy idle run. Docs: §M42, NAMED M42 block,
  MILESTONES C2 addendum.

## Session 41 continued (2026-10-22) — M43: player↔"faction-ID" mapping RESOLVED — the base +4/+5 byte IS the owner player index; we own ZERO bases; `0x4e3700` corrected

- **Identity mapping (H):** base `+4` == `+5` byte == **owner player index** — 167/167 units
  standing on a base tile match `unit+14 == base+4`, zero mismatches; per-player home_base
  cross-refs clean for players 2/6/7. Bases per owner {1:10, 2:24, 4:7, 5:6, 6:16, 7:9}. **M38's
  "faction ID {1,2,4,5,6,7} ≠ player index" RETRACTED** — those are owner player indices; 3 absent
  because we own **zero** of the 72 bases.
- **We have no bases (H):** all 5 player-3 units `home_base@+46 = 0xffff` (chain `+48` too). Tile
  ownership = `tile+2` **low nibble = player index**, 0xf unowned; hist {0:199, 1:317, 2:468,
  3:45, 4:345, 5:130, 6:261, 7:269, 15:1166} — we hold 45 **orphan-border** tiles with no bases;
  player 0 = destroyed faction (no units, no bases, 199 tiles, engine still visits cur=0).
- **`0x4e3700(x,y,player)` corrected (H):** Ghidra `psVar7` is `short*` ⇒ compares **byte at
  base+4** with the player arg, x from byte base+0, y from short base+2, stride 0x98 shorts = 304
  B — the function is correct; inert for player 3 = no owned bases (⇒ cost base-distance branch
  can never fire for us — data, not code quirk). Sets `DAT_008f0d34` = last distance.
- **Base minerals (H):** `+64` u32 differs across bases (43/4/4/78) ⇒ **per-base** accumulator,
  mirrored at `+152` inside the 304 record (M31 mirror ✓). Faction records `0x94d650+player*0x82f`
  carry **no def-index byte** (no 0..6 permutation offset found) and no name pointers —
  player↔faction-NAME (GAIANS/HIVE/UNIV/MORGAN/SPARTANS/BELIEVE/PEACE) open.
- Left running: unchanged (pid 914079, year 2298, cur=3, Former @ (45,7) tile 0x10800e, energy 15,
  tech18 0x08, TracerPid 0). Next: M44 economy idle run (`scripts/m44_idle.py`, no gdb). Docs:
  §M43, NAMED M43 block, MILESTONES C2 addendum + C3 correction.

## Session 41 continued (2026-10-22) — M44: economy idle run DONE — our income AND upkeep are zero (energy flat over 12 rounds); AI mineral→energy conversion ≈1:1 seen on one faction; the Council-pane OK bar must be found BY COLOUR (tesseract cannot read it); mask bit 0x2 = unit-present; type-record base = 0x98ad88

- **Blocker fixed (H):** a resolved governor-election pane ("YANG ELECTED" + PROPOSAL bar) froze the
  pump at year 2303; only the blue OK bar remained and **tesseract returns nothing for its label**, so
  vocabulary servicing looped and three attempts (m44a/b/c) died on the preflight assert with zero
  JSON. New `find_ok_bar()` colour-detects it (band x 240-560, y 430-520, lowest contiguous blue bar
  ≥8 rows; calibrated rows y 488-507, x 268-532, rgb (103,91,181)); the HUD chrome's 1-px blue line
  at **y 526 exists in every frame** and must be excluded or a bare HUD tests positive. Live click
  (400,497) dismissed the pane; year 2303→2304.
- **Economy (H, 12 rounds 2304→2315, `evidence/m44d_idle.json`):** our energy 15 at every snapshot =
  **0 net/turn**; the HUD panel agrees where it was visible (Gross Income 0/turn, Total Costs 0/turn,
  NET INCOME 0/turn; rounds 1/3/4 — later crops caught the diplomacy strip instead, so trust the
  memory series) ⇒
  zero bases = no income, and **upkeep never debits faction energy**; the 25-cost elev-6 raise is
  unpayable until we found a base. AI per round: Δenergy {1:-1.4 2:-1.3 4:+10.9 5:-0.5 6:+5.3 7:-0.9},
  Δbase-minerals {1:+2.3 2:+8.3 4:-11.2 5:-1.9 6:+31.2 7:+1.1}; player 4 anti-correlates almost
  exactly (minerals -11.2 vs energy +10.9) ⇒ unspent base minerals → energy ≈1:1 (O, one faction);
  player 6 accumulates both (+31.2 / +5.3). Bases 72→73 ({4:8→9, 6:16→17, 5:5→4, 2:25→24}).
- **Attrition (H counts / O cause):** our units 5→2 during the run (drops 2305, 2308, 2309).
  Survivors: idx 30 **Colony Pod** (type 0) @ (45,11) and idx 31 **Laser Squad** (type 195) @ (43,11),
  both Hold. **The Formers unit (type 1, class 9) is dead — no terraformer remains.** Hypothesis:
  unsupported-unit attrition with zero bases (untested).
- **Corrections (H):** (a) autosaves ROTATE over all 8 slots (30/20/10 every 10 y = 2290/2300/2310,
  then 5/4/3/2/1 yearly = 2311..2315) — the "slot 2 = year 2198" load note is stale; recovery points
  exist. (b) the runtime tile record == map-file cells (2n,y)++(2n+1,y) byte-exact (verified against
  the LIVE autosave map section); accessors (`0x582ed0`, `0x5831a0`) are **parity-blind**
  (`40*y + x>>1`, +0 elev / +8 mask) so the tile pair shares elevation and the +8 mask; a second
  mask-shaped dword at +0x18 is open. (c) tile mask bit **0x2 = unit present** (3193/3200 agree,
  0 false negatives, 7 stale positives). (d) mask vocabulary `0x6938f0` × `0x94d2f8`: farm 0x8000,
  soil enricher 0x80000, mine 0x10, solar 0x40, forest 0x200000, road 0x4, magtube 0x8, bunker 0x800,
  airbase 0x40000 (k=8, work 10, clears bunker), sensor 0x80000000 (k=9, work 4), fungus 0x20
  (k=10 clears / k=11 sets), condenser 0x400000, echelon mirror 0x8000000 — **k=8 is Airbase, not
  Sensor** (M42 corrected); `0x94d2f8` = 14 × (land, sea, key-char STRING) stride 12. (e) **type
  record base is 0x98ad88** (name +0, ability +32 = 0x98ada8, domain +36 = 0x98adac, class +42 =
  0x98adb2): the standing ABSOLUTE addresses were right, the "base 0x98ada8 / name at +20" phrasing
  was not — type 0 Colony Pod/cls 8, type 1 Formers/cls 9 (`0x4d44d0` gates terraform on cls 9 ✓),
  193 Scout Rover, 195 Laser Squad; ≥196 runtime types vs 15 alpha `#UNITS` template rows.
- Left running: pid 914079, year **2315**, cur=3 our turn OPEN, Colony Pod @ (45,11) + Laser Squad @
  (43,11) both Hold, energy 15, tech18 0x08, tech60 0x16, TracerPid 0. Next (M45): found a base with
  the Colony Pod (`b` on owned (45,11)), then re-run the idle loop to read the new income/costs.
  Docs: §M44, NAMED M44 block, MILESTONES C3 addendum, NEXT_PROMPT rewritten for session 42.

## Session 42 (2026-10-22) — M45: FIRST BASE FOUNDED — `b` path live-traced end to end (NEWBASE → 0x4cca50 → CREATERET base=73); NEWBASE accepts a plain Return; mask bit 0x1000 = base border (radius ≈3, pop-independent); economy re-measured: 15 → 19 ONCE then flat again; pitfall: Ghidra FUN_ addresses are verbatim (7/15 bps were +0x400000 off and armed silently)

- **Milestone (H, live):** `scripts/m45_base.py --tag m45a` + `scripts/m45_base.gdb` (15/15 armed)
  pressed `b` on the Colony Pod (idx 30, type 0, cls 8) at (45,11), year 2315. Trace:
  `SETTER unit=30` → `BORDERRET eax=-1` → `LIMITRET eax=12` → `PANE #1 id=NEWBASE` →
  `ALLOCRET base=73 unit=30` → `CREATERET base=73 unit=30` → `PANE #2 id=BASEFOUNDED`.
  n_bases 73→74; our base (45,11) owner 3 **pop 5**, name **"Climactic Research"**
  (game-generated default — Return accepted it, nothing typed), +64 minerals 10, kit =
  HQ + Recycling Tank + Recreation Commons + Energy Bank + Network Node (`m45a_post.png`).
  The Pod was consumed. Recipe that worked: poke `+17` 2→0 (can-act `0x5acc00` refuses order
  1..3 when `+4 & 0x4200 == 0`), rival unit `+40`→255, `0x91b5c4`→0, Tab-select (orders mode 1),
  arm gdb, press `b`, Return on the name pane, Return/Escape on the follow-up panes.
- **No territory dispute (H):** `0x4e3b50` returned **−1** for (45,11) even though the tile's owner
  nibble was already 3 ⇒ the ~45 inherited nibble-3 "orphan" tiles (M43) are NOT borders to the
  game, so TERRPACT/THISLANDISMYLAND never fired. Base limit query `0x4e9b40` = **12** (BUREAUCRACY
  only at a nonzero multiple of it).
- **New mask vocabulary (H, statistical):** mask1(+8) bit **0x1000 = "inside a base's claimed
  border"** — 1258 flagged pairs, assigned to nearest base = 12-31 pairs per base, Chebyshev max
  3-9 (mean ≈3.3), **no pop dependence**, mask1-only 1238 vs mask2-only 1, ocean pairs included;
  our tile gained it at founding (0x108006 → 0x109005) while the farm bit 0x8000 cleared. Bit 0x1 =
  base-on-pair now 74/74. Base +64 == +152 still 74/74; **base +56 is the constant `0x00dfbe41`
  in every record** (M44's "copied from home base" reading is wrong).
- **Economy (H, 16 start-of-our-turn snapshots, 2315→2329, `m45c_idle.json` + `m45f_idle.json`):**
  faction energy **15 for 2315-2319 → 19 at 2320 → flat 19 through 2329** — `m45f`'s deltas block
  says **0.0/round over its 9 intervals**, ≈+0.8/round across the whole window, against the
  base screen's own readout (ENERGY 003−000 = +003, MINERALS 007−000 = +007, NUTRIENTS 009−010 =
  −001 SHORTFALL "Hunger!"). Pop 5→4 (shortfall attrition, not eco-damage). Base +64 oscillates
  1-10 with no trend; our units grow 1→**6** (the base turns out Scout Patrols) while energy stays
  flat ⇒ **unit upkeep still never debits faction energy**; the only moving interval
  (2319→2320: minerals 8→4, energy 15→19) matches M44's ≈1:1 mineral→energy signature.
  Base `+64` series 10,10,6,2,8,4,9,4,8,2,5,8,1,3,5.
  **A pod base does not make us solvent** — the 25-cost elev-6 raise (M38) is unpayable 14 years on.
- **Harness fixes (durable):** `service_pane` had **no branch for classify kind `base`** (the BASE
  screen the founding leaves open; its RENAMEd/OK row is at y≈365, outside `find_ok_bar`'s band) →
  `m45b_idle` spun 15 min on 1 round and had to be killed. Added `kind=="base"` → one Escape to
  `m44_idle.service_pane` and to `m45_base.py`'s post-create loop. Also: `objdump` cannot read this
  PE ("invalid bfd target") — pin call sites with a raw E8 scan (`.text` file offset = VA−0x400000;
  the PE header's ImageBase field reads a bogus 0x270000, identity mapping holds).
- **PITFALL (H, cost 7 of 15 trace lines):** Ghidra callee names `FUN_<address>` are the address
  VERBATIM. `FUN_005abb40` = 0x5abb40, `FUN_0041b780` = 0x41b780 … — m45a armed them with a
  duplicated leading digit (+0x400000), gdb armed 15/15 anyway (a wrong-but-mapped address never
  complains) and the seven bogus bps silently never fired. Corrected + warned in
  `scripts/m45_base.gdb`.
- **Open:** HUD Gross Income/Total Costs/NET INCOME never OCR'd (dialog or unit panel every frame)
  → find the panel's source values in memory instead (M46 option 1). M44's "autosave record == two
  22-byte cells at +2724" did NOT reproduce (3200/3200 differ; located ocean pairs fit no stride
  model) → save-map layout unverified; pre-founding map frozen in `scratch/auto2315/` (1.SAV = 2315).
- Left running: pid 914079, year **2329**, cur=3 our turn OPEN, TracerPid 0, no gdb; **1 base**
  (idx 72 "Climactic Research" @ (45,11), pop 4), **6 units** (Laser Squad idx 22 @ (43,11) Hold +
  5 Scout Patrols type 2 @ (45,11), each `+46 = 0x48` = base 72 ✓ produced units home to their
  base), energy **19**, n_bases 75, no cls-8 colonist and no cls-9 Former left. Docs: §M45, NAMED M45 block, MILESTONES C3 addendum,
  NEXT_PROMPT rewritten for session 43.

## Session 43 (2026-10-22) — M46: ECONOMY DECOMPOSED — the upkeep pipeline is named end to end (`0x521070` → `0x5208f0` → `0x520540` → `0x4f5a70`, `energy += base+0x7e`; facility upkeep charged directly by `0x4f47f0`); HUD Gross/Costs/NET = `FUN_00445900` scratch globals, live-verified net 0 ⇔ energy flat; `faction+4` = within-round spending ledger; real blocker found: the OPERATIONS DIRECTOR end-turn pane

- **Milestone (H, static + live):** the per-round economy. Driver `0x521070` → per-player
  `0x5208f0(p)` (sub-steps `0x5a1830`, `0x51f730`, **income core `0x520540`**, `0x51fe90` sliders,
  `0x5a1ad0` attitude penalty) → tail **`energy -= faction+4; faction+4 = 0; clamp >= 0`**, i.e.
  faction `int[1]` is a **within-round spending ledger**, 0 at every start-of-turn (all players,
  11 snapshots). `0x520540` pays gifts, calls `0x4f5a70(base)` per base, then the AI-only stockpile
  line (gated `DAT_00985aec > 3`; ours = 2 ⇒ never) and the trait bonus (`0x927a7c + p*0x59c`,
  flag `0x4000`). `0x4f5a70` runs the production pipeline and does **`energy += base+0x7e`** — a
  transient per-base income field that reads 0 at start-of-turn with no visible writer in the whole
  export (O: computed-pointer write). Facility upkeep is separate and DIRECT: **`0x4f47f0` charges
  `energy -= cost`** per completed facility and SELLS one on shortfall (bitmap clear + refund).
- **HUD panel solved without OCR (H):** `FUN_00445900(player,0)` recomputes, per redraw,
  `0x745734 = sum base+0xfc` (GROSS), `0x744f28 = sum upkeep` (TOTAL COSTS), `0x7457d4` trade,
  `0x7457dc = NET`; `0x744f2c[base]` per-base upkeep, `0x745738[39]` item counts, `0x74572c` food,
  `0x745730` self-sufficiency %. Faction display pane `0x49fee0` draws rows 0x17d/0x17e/0x17f from
  these globals verbatim. **Live: gross 2 - upkeep 2 = net 0 ⇔ energy 19 flat** ⇒ the old "HUD rows
  never OCR-able" item is moot; read the globals.
- **Item upkeep table decoded (H):** `0x984d48 + item*0x30`, 39 rows, int0 = upkeep, int1 = required
  tech id (`0x92fdb4 + id*44`); **runtime item = alpha `#FACILITIES` index + 1**; completion bitmap
  at **base+0x8c** (byte `item>>3`, bit `item&7`), mapper `0x507410`. Disabled-list puzzle resolved:
  the list is in the **player trait record `0x927a7c + p*0x59c`** (1436 B; `+0x20` count, `+0x24`
  types, `+0x44` items) and **our faction zeroes Network Node** ⇒ 3 - 1 = 2 = live `744f28`.
- **Per-round full-record diff, all 7 AI (H, `m46e`, 2330→2331):** records are **2095 ints**
  (stride 0x20bc; the old 2111 over-read 16 ints into the next player — `int[2095]` = next energy).
  Panel net vs Δenergy: p1 30/+4, p2 16/−5 (tech completed, `+0x1a8` 485→87, `+0x1ac` 30→77),
  p3 us 0/0, p4 29/+18, p5 7/+7 (exact), p6 10/−24, p7 25/+11. Exact for us and p5; the gaps are
  within-round ledger debits (research, gifts, AI terraform). Unit upkeep again NOT charged to energy.
- **Standing answer (H):** our slope is net 0 ⇒ **25 energy is never disposable** (need +6 at Δ0);
  the elev-6 raise stays unpayable, and Corner Market `0x4e2050` is surplus-gated
  (`energy > max(sum rivals, 1000)`) so it can never save us. Solvency must come from pop/facility
  growth raising `base+0xfc`. The 2320 +4 credit remains a one-off, mechanism **open (M)**.
- **Blocker that ate m46a-d (H, cost ~4 runs):** the **OPERATIONS DIRECTOR end-turn pane** —
  "Some of our units have not yet moved this turn ... end the turn now?" with `Cancel.` as DEFAULT
  and its blue OK bar at **y 215-350, outside `find_ok_bar`'s 430-520 band**; Return picks Cancel so
  the turn never ends while TURN COMPLETE stays visible behind the pane. Fix: from the OCR Cancel
  word centre, click `(cx, cy+24)` then `(cx, cy+49)`. Also added **`hud_up(png)`** (orange-pixel
  count in `(600,395,800,425)` > 300) because `classify()` denies `hud` on the busy frame.
- **Open (M47):** who writes `base+0x7e` and the `faction+4` ledger (hw watchpoints); what
  `faction+0x1b8` is (multiples of 20); the 2320 +4 mechanism; the mineral economy is still
  un-isolated. Detail `turn_driver.md` §M46, `NAMED.md` M46 block, `MILESTONES.md` C3 addendum.

## Session 44 (2026-10-22) — M47: WRITE PROVENANCE — the exact stores that move faction energy; `base+0x7e` retracted as a Ghidra short*-artifact (the addend is `base+0xfc`); ledger writers are action-time; six input-blocking panes that `classify()` calls `hud`

- **Positive control first (H):** `hw watch` on the mission year fired once, `eip=0x51f554
  val=2335` in `FUN_0051f320` when the round rolled 2334→2335 (`evidence/m47_year_watch.log`).
  Hardware watchpoints DO work under this Wine build; earlier sessions only ever armed them.
- **Income (H):** watching our energy `0x953884` through a round caught
  `eip=0x4f5c92 val=21 ecx=0x962f90(=our base) esi=0x6234 edi=3`; disassembly at the site is
  `4f5c7f mov 0xfc(%ecx),%edx · 4f5c85 add %edx,%eax · 4f5c8c mov %eax,0x94d650(%esi)`
  ⇒ **faction energy += `base+0xfc`**, inside `FUN_004f5a70`. Our 19→21→20→19 reproduced
  exactly (two upkeep debits of 1 for runtime items 6 and 7).
- **Retraction (H):** `base+0x7e` is never written — zero hits on `base+0x7c..0x7f` over two
  armed rounds, and it reads 0 always. Ghidra prints `*(int *)(DAT_008f0d60 + 0x7e)` but
  `DAT_008f0d60` is a **short\***, so `+0x7e` = `0xfc` **bytes**. M46's "transient income field
  with no visible writer" was decompiler pointer maths, not a missing writer.
- **Upkeep (H):** `eip=0x4f4958` in `FUN_004f47f0`: `mov 0x94d650(%edi),%ecx · sub %eax,%ecx ·
  mov %ecx,0x94d650(%edi)` then `faction+0xe0 += cost` at `0x4f4962`; `esi` = runtime item id
  (6 = Recreation Commons, 7 = Energy Bank); item 8 (Network Node) never fires — disabled list.
- **Ledger (M, open):** `faction+4` got **zero** writes for us *and* for Morgan across a full
  idle round ⇒ the ledger is written by player ACTIONS (research/gifts/terraform), not upkeep.
- **AI round (H, `evidence/m47f_watch.log`, 28 hits):** Morgan p4 2335→2336 — income at
  `0x4f5c92` per base; upkeep at `0x4f4958` per item (2,6,7,8,0x18,0x1b; cost 1-2); a **direct
  per-base debit of −7 twice at `eip=0x4f2dc4`** in `FUN_004f26e0` (the production/rush step that
  reads `energy/10` and `energy/50`); and a final whole-faction write at `0x506d2b` (=905).
  ⇒ M46's "AI gaps = ledger debits" is NOT supported for idle rounds.
- **Operational (H, cost the session):** six panes block input while `classify()` says `hud`
  because the HUD is visible behind them — advisor advisory ("PLANETARY ECOLOGIST / Mindworm
  boil spotted") → `Return`; advisor story page ("Book of Planet", long body) → click (400,470);
  council convenes page → `Return`; council ballot → click the **ABSTAIN** word centre; result
  page ("MEASURE FAILS") → `Return`; faction-info table (Tech:/Mil:/Pop:/Wealth:/Territory:/
  Overall:) → click (400,580). Rule of thumb: `hud` + TURN COMPLETE visible but the year will not
  move after a click ⇒ `Return` once, then click the pane's bottom-centre.
- **Harness:** `scripts/m47_watch{,2,3,4,year}.gdb` + `scripts/m47_drive.py` (end-turn driver with
  the pane rules). All read-only: TracerPid 0 before pokes, watches armed after, `kill -INT gdb`
  then `kill -CONT` every time.
- **Open:** ledger writers (needs a round in which we research/gift/terraform); what `faction+
  0x1b8` is; the 2320 +4 credit; mineral economy isolation; name of the `0x506d2b` host function
  (Ghidra lumps it into `FUN_00502cd0`, 18 KB — address is solid, name is not).

## Session 45-46 (2026-10-22) — M48d: MINERAL ECONOMY FULLY TRACED (first queue/growth completion in 26 years)

`scripts/m48d_drive.py` (driver-generated gdb: 16 int3 sites + 4 hw WPs, literal baked addrs,
SELFTEST block, colour-only fast loop + OCR fallback map) + generated `evidence/m48d2_watch.gdb`,
logs `evidence/m48d2_{watch.log,drive.json,run.log}`. 3 rounds 2345-2347 armed, clean detach,
0 OCR passes, zero stalls. Load: relaunch + `Alpha Centauri Autosave 1.SAV` (year 2344) after the
CONFIRM-DISBAND deadlock (below).

**Storage model VERIFIED (corrects M48's "pin" theory)**: between completions `base+0x40 += d0`
per round, UNCLAMPED (Morgan 0x95ef70 111→121 = +d0 10, no clamp hit). AT EVERY PRODUCTION
COMPLETION (unit OR facility), after the spend, storage := **max(0, min(d0, cap))** — the stockpile
is destroyed down to one round's income. Three independent confirmations: ours 200→190(SPENDA)→0
(WP3 store at 0x4eff23, d0=0); Morgan 131→5(shortfall)→10 (MIRA, d0=18 cap=10); m48e 200→0 (d0=-1).
- Sites (all fired on our base, first time ever): IGATE 0x4ef7db (d0 load) → IADD 0x4ef7f6
  (store storage+d0) → QGATE 0x4ef88b (+0x50 carries transient scratch 0xE00001 mid-visit) →
  COMPLET 0x4efe41 (ebx=2 item, edi=10 COST of Scout Patrol, esi=8 budget) → SPENDA 0x4efed8
  (store 0x4efee0 = −cost) → [gate 4efee4: post-spend storage ≥ edi? else shortfall branch] →
  CLAMP1 0x4eff02 (event test (1<<owner)&mask; ours 0x8 ✓ mask 0xff08) → MIRA 0x4eff29
  (store 0x4eff23 := min(d0,cap)).
- PROGDIV 0x4efd49 and QDRAIN 0x4f1e3f: ZERO hits all rounds — not on the solo pipeline path.
- **Pop-growth production**: pop 4→5 next round + new unit idx 297 (type 2, home 71) + COMPLET
  ebx=2/edi=10 + spend 10 ⇒ growth units cost minerals from base storage; 26 years of storage 0
  ⇒ pop grew but units never spawned ⇒ the "builds Scout Patrol" backlog messages. First unit
  ever produced by our base under observation.
- **NOSUPPORT disband condition**: d0 < 0 ⇒ disband one unit per round (2341-2344: units 5→3);
  d0 = 0 ⇒ stable (2345-2347 ✓). Upkeep ≈ 2/unit vs facility income 6-7.
- d0 (base+0xd0) recomputed at 0x4e955d (inside 0x4e93f0) EVERY round before the pipeline visit —
  pokes to d0 are dead on arrival (confirmed 3×). +0x3c and +0xcc survive until the visit but cc
  is re-derived too (came back 0, then −1 with d0=0; cc tracks d0).
- Energy WPs (live M47 model): +2 credit 0x4f5c92 (=base+0xfc) then −1 −1 facility upkeep
  0x4f4958 → 19→21→20→19, net 0 ✓.
- Pipeline sweep: full sweep = 75 visits, ours LAST (n=75); sweeps can end early (21/28 visits)
  when the year store interrupts — visit-order/early-stop mechanism OPEN.
- Pane bp 0x483470: ZERO hits (OPERATIONS DIRECTOR confirm doesn't route through it; advisories do).

**UI lessons (cost a lost game-state; recovery = relaunch+autosave):**
- CONFIRM DISBAND (Script #DISBAND, rows "Never mind."/"Confirmed." + OK) opened from the base
  panel's FORCES SUPPORTED context menu (glyph click (688,462) → menu box y 464-534, Disband row
  y≈529, x 612-700) can cascade BEHIND base-panel widgets: its rows/OK land on chrome hitboxes,
  keys are dead (M32 modal sink) → unreachable modal. Row clicks never moved the highlight.
  Recovery: relaunch + load autosave (saves live in `programs/saves/auto/`, year = u16 @0x54;
  M27 typed-path recipe; `scripts/m48d_boot.py`). Autosaves had captured 2344 — zero progress lost.
- Panes QUEUE: each Disband-menu click queues a CONFIRM DISBAND; each OK click cancels one.
  Identical-looking panes cycling = queue draining, not a frozen pane.
- TOUR hint popup (auto-opens on first view of a screen): Continue (325,585). Social Engineering
  full screen (OK (240,368) commits, CANCEL doesn't close). Comm "put her through?" pane:
  "No, close the channel." row ≈ y 310.
- Colour-only driver (rightmost_blue_run 150-430 row-click bar_y−25 then bar; find_ok_bar 430-520;
  hud_up gate for TURN_BTN) ran 3 rounds unattended 0 OCR 0 stalls ✓.

Next (M49 options): growth-cost/esi=8 formula (disambiguate 2×pop vs cap−fc vs (d0+fc)×4 — pop 5
round); pipeline early-stop mechanism; production-rate cc source function; the 2320 +4 credit;
faction NAME mapping; ledger writers on a spending round.

## Session 47 (2026-10-22) — M49a: THE GROWTH-COST QUESTION DISSOLVES — edi at COMPLET is the base's SWEEP-ENTRY INDEX, not a cost; esi=8 is the event-mask bit-test result; M48d's "Scout Patrol cost 10" RETRACTED

`scripts/m49a_drive.py` (copy of m48d_drive.py: COMPLET print extended with pop/fc/cap/d0/cc/3c/
e0/f0/c0 + stack scratch [ebp−0x1c..−0x2c]; new bp `ST1C` 0x4efae5 with its own `$ns` counter;
self-pkill fix — see pitfalls). Runs: `evidence/m49a_{watch.gdb,watch.log,run.log}` (1 round,
2347→2348, 0 OCR), `evidence/m49c_*` (1 round, 2348→2349, 43 OCR passes — COMM-pane chain, below).
Static: clean 32-bit disasm via `gdb -batch -ex "file programs/terran.exe" -ex "x/Ni ADDR"` (the
PE loads as a mapped target; NO attach, TracerPid stays 0).

**VERIFIED (disasm chain + 3 live runs): the SPENDA subtract operand `edi` is the base record's
SWEEP-ENTRY INDEX, not any cost formula.**
- `0x520540` per-base loop passes the base INDEX as a STACK arg: `push ebx; call 0x4f5a70`
  (0x5206d2-6d3; ebx = index, dec ebx + sub edi,0x130 on compaction slides 0x5206df-e0).
- `0x4f5a70(arg0=index)`: `mov ebx,[ebp+0x8]` → `mov edi,edx` at 0x4f5aa9 (edx = owner byte
  0x4f5a9c) — edi := index just before `call 0x4ef6d0` (0x4f5adc). Ghidra's
  `FUN_004f5a70(iVar1)` confirms arg-in-stack.
- Pipeline `0x4ef6d0`: the pop-growth path (QGATE 0x4ef88b → 0x4efadc store [ebp−0x1c] →
  class≠8 `jne 0x4efe41` / pop≤1 `jne` / `0x4efb0f` event test → ... → `cmp eax,2;
  jge 0x4efe41` 0x4efdb4) contains **NO edi write** (only 0x4ef8e2/0x4efa4b on the negative-queue
  branch). So COMPLET sees edi = the index.
- SPENDA 0x4efed8: `esi = storage − edi; storage := esi` ⇒ **storage −= entry-index** at every
  completion. Live: ours 200→190 three times (m48d2/m49a/m49c; edi=10 = our index-at-entry; the
  CURRENT idx drifts 71→69→60 as the array slides — the invariant is edi == index-at-sweep-entry).
- AI lines fit the same model: edi == their index-at-visit-entry (e.g. 44 recurs across years
  while current idx drifts 25→29→54/60).
- **esi at COMPLET entry is path residue, not a budget**: on the pop-growth path esi = result of
  `0x48ee00` (message/pane formatter, scratch 0x997120) preceded by `0x4e40a0(owner,1,−1)` =
  `(1<<owner)&mask` = **8 for us** — the very value the CLAMP1 gate uses (m2c=0x8 = same bit).
  Facility-path COMPLET lines carry pointer-looking esi (type-record scratch `ebx*60+0x98ad88`)
  because the callee chain 0x4e8d60→…→0x4eaa10 (runs only when ebx≥0x40) clobbers edi/esi.
- **pop at COMPLET is ALWAYS the pre-completion value** (growth lands after; attrition re-drops):
  m49c located pop=5 pre-poke, OURBASE showed pop 4 at 2349 (NOSUPPORT disband), COMPLET printed
  pop=4. ⇒ pop can never disambiguate a formula; the M49a test design was void, and all three
  candidates (2×pop, cap−fc, (d0+fc)×4) were coincidences on pop=4/fc=2/cap=10/d0∈{0,−1}.

**Corrected mineral model (supersedes M48d's cost story)**: per round `storage += d0` unclamped;
at every completion `storage −= entry_index` (0x4efee0), then event-owner clamp
`storage := max(0, min(d0, cap))` (0x4eff20/23). Pop-growth units are effectively FREE (the "cost"
is the index quirk); the 26-year backlog is explained by storage clamped to 0 ⇒ the index-subtract
always takes the shortfall branch (4efee4) — not by unaffordable unit costs. Whether real per-unit
mineral costs exist anywhere in the pipeline is OPEN (M48d's PROGDIV/QDRAIN never fire in solo;
`0x4f26e0` runs right after 0x4ef6d0 in 0x4f5a70 and is the next candidate).

**NOSUPPORT disband live again**: pop 5→4 across 2348 (m49c OURBASE line 178), d0=−1 at the visit
— disband fires while d0<0 (M48d rule holds).

**Pitfalls found (this session):**
- `pkill -INT -f "[m]49a_drive"` matches the DRIVER'S OWN cmdline → the driver SIGINTs itself at
  startup (KeyboardInterrupt inside subprocess.run). The bracket trick only protects pkill's own
  shell, not a python driver whose argv contains the tag. m49a_drive.py now kills stale copies via
  pgrep + os.kill skipping os.getpid().
- COMM OFFICER pane has a 3-row variant ("Yes, switch to main viewscreen." / "No, close the
  channel." / "Display faction leader profile."). The colour row-click (bar_y−25) can land the
  selection on "Display faction leader profile" → UNIVERSITY INTELLIGENCE FILES table whose
  CLOSE/DATALINKS bars sit at y≈345-360 — outside find_ok_bar (430-520) and hit by the
  rightmost_blue_run row-click+bar cycle; chain took ~8 min / 43 OCR passes to drain (DATALINKS →
  diplomacy pane OK bar ≈y 345 → back). Driver did self-recover; faster fix = click the specific
  row by OCR y, or click bar_y−25 twice before the bar.
- objdump CAN disassemble this PE after all: `-b binary -m i386:x86-64 -D --adjust-vma=0x400000
  --start-address/--stop-address` (file offset = VA − 0x400000 identity) — but 64-bit decoding
  MISALIGINS on SEH blocks (the COMPLET region decoded as garbage/movabs). Clean 32-bit recipe:
  `gdb -batch -nx -ex "set architecture i386" -ex "set disassembly-flavor intel" -ex "file
  programs/terran.exe" -ex "x/Ni 0xADDR"` — gdb maps the PE image; read-only, no attach.

Next (M49/M50 options): real unit/facility mineral cost — instrument 0x4f26e0 (runs after the
pipeline in 0x4f5a70) + watch storage across a facility completion on a high-index base; pipeline
early-stop mechanism (sweep caller ordering + year-store interrupt); production-rate cc source
(0x4eaa10 / 0x4e92c0 candidates — note 0x4eaa10 loops 7× over faction stride 0x20bc writing
faction+0xc4 = research pool); the 2320 +4 credit; faction NAME mapping; ledger writers on a
spending round.

## Session 48 (2026-10-22) — M50a: 0x4f26e0 IS NOT A COST STEP — it is the per-base mineral↔energy conversion/income step and a THIRD storage writer (0x4f2d7d); deltas live-observed 0…+12 (storage GAINS); our base early-returns via the base+0x38 flag gate; sweep truncated again at 28 visits (ours unvisited)

`scripts/m50a_drive.py` (copy of m49a_drive.py + 3 bps: F26E0 entry 0x4f26e0, **CONVST 0x4f2d7d**
(the store), RET26E0 0x4f5ae1; own counters $nb26/$ncv/$nre). Run `evidence/m50a_*` (1 round,
2349→2350, 0 OCR, clean detach; sweep PIPE n=1..28, all own≠3 — the YEAR store 0x51f554 fired
mid-sweep, our base never processed; poked min40=200 survived, OURBASE log line 246).
Static: clean 32-bit disasm of 0x4f26e0 (gdb file-target recipe) + Ghidra pseudocode.

**VERIFIED (disasm + live ×1 round, 28 F26E0 hits / 10 CONVST hits): `0x4f26e0` is a mineral
INCOME/CONVERSION step, not a production cost.**
- Early-return gates (0x4f2705-0x4f2729): (a) event-owner ∧ `~(base+0x38)` bits 0x1a/0x1c set
  ⇒ return — **our base takes this path** (f30=0x805000 has bit 0x1c ⇒ 0x4f26e0 never executed
  for us: 0 ours=1 hits, log lines 59-246); (b) `base+0x40 == 0` ⇒ return.
- Reads `base+0x50` (queue) → `|q|×240 + 0x984d44 + 0x44` = the ITEM table (stride 0xF0 — the
  same 0x984d48 rows M46 named; int1 = required-tech id, e.g. 44/43) used as a DIVISOR-ish
  multiplier; amount ebx = f(event mask, energy pool `0x94d650+p·0x82f·4`, queue value, item
  int1, government/trait term `0x927a84+p·0x3c`+0x50 (value 100 doubles), global 0x985bb8=−1,
  `0x985aec`); clamped `0 ≤ ebx ≤ min(energy-derived, energy_pool − storage)`.
- **Third storage writer: 0x4f2d7d `base+0x40 := storage + ((E/esi)·45)/trait`** (the
  (E/esi)·45 = ×5·×9·<<2 formula at 0x4f2d68-71; esi = 0x4e40a0 event result, live edi=4/esi
  values on entry prints). Then event-owner branch (0x4f2d85): event owners SKIP the energy-side
  adjustment (0x4f2dc4-0x4f2e97); non-event owners also add `−(0x985aec·ebx)/((8−gov[+0x50])·2)`
  to the energy pool.
- **Live CONVST deltas (log lines 131-192): storage CHANGES by 0…+12 — GAINS, not debits**:
  own=6 deltas 0,0,0,0,+1,+4 (lines 131-178); own=7 deltas +12,+3,+2,+1 (lines 185-192).
  own=4: CONVST never fired (branch not taken; own=4 bases show min40 unchanged entry→exit,
  lines 59-90). ⇒ M44's "unspent base minerals → energy ≈1:1" anti-correlation is NOT this
  function's storage path (player 4 takes a different branch; its +10.9 energy/round comes from
  elsewhere). The conversion amount scales with the FACTION ENERGY POOL (AI pools 192-1080 vs
  ours 19) — energy-rich factions pump more minerals into base storage per round.
- **Production mineral cost STILL OPEN**: the per-base chain 0x4f26e0 → 0x4ee410 touches
  storage only at 0x4f2d7d (credit); 0x4ee410 has no base+0x40 access (grep-verified); the only
  debits remain the M49a index-quirk at 0x4efee0. ⇒ production appears effectively free of
  mineral costs in solo; the queued-item "cost" read at 0x4f2750 is the item table's tech-id
  slot, not a price.

**Sweep early-stop (M50b data point)**: this round PIPE n=1..28 (all own≠3) then the YEAR store
interrupted — third independent observation of truncation (21/28/28). Consistent with
0x520540's per-base loop aborting mid-array when the round/year advance lands inside the sweep;
exact mechanism still OPEN.

**Pitfall**: none new operational (clean round, 0 OCR). Note the CONVST bp prints pre-store
values ($eax = the NEW value about to be stored; delta = new − current).

Next (options): M50b sweep early-stop (bp 0x520540 loop body + 0x51f320 caller ordering);
M50c cc source; M50d the 2320 +4 credit; M50e faction NAME mapping; NEW: the energy-side of
0x4f26e0 on a non-event AI base (pin the energy pool store in 0x4f2dc4-0x4f2e97, correlate
CONVST delta vs pool delta in one round); NEW: what makes our base take the 0x4f2705 flag gate
(base+0x38 bit 0x1c = ? — likely the "no AI spending/disrupted" flag) and whether clearing it
routes us through the conversion (minerals income!).
