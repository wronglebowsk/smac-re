# Turn-completion stall — M4 diagnosis (2026-10-20)

Method: live `/proc/<pid>/task/` thread-state sampling + gdb 17.1 read-only attach to terran.exe
after attempting a turn (TURN COMPLETE→Yes→OK) at Mission Year 2101. gdb output: /tmp/gdb_bt.txt.

## Observed
- 17 threads. Every non-main thread is **Wine infra, idle-blocked**: llvmpipe-0..3 (futex), Wine
  thread-pool workers (futex), `:disk$0`, `wined3d_cs`, `audio_client_*`, wineserver pipe readers
  (`anon_pipe_read`). None is a "game turn" worker → **SMAC turn logic runs on the MAIN thread.**
- **MAIN thread (tid==pid): state=R in 12/12 samples over 5 s; `top -H` ~30% CPU; utime grows ~8
  jiffies/0.4 s.** syscall mostly "running" (pure user-space), occasional `read`(3)/`poll`(168).
  → a **busy compute/poll loop**, NOT a blocking wait, NOT a deadlock.
- gdb bt of main thread: `#0 __kernel_vsyscall`, `#1` libc poll/select-family wrapper (0xee5fe4ec),
  `#2 0x0` — Wine's stack won't unwind past ntdll (no frame info), so bt yields no game-level frames.
- llvmpipe threads 0% CPU here → the prior-session attribution of "~60% CPU = llvmpipe redraw" was
  **WRONG**; the burn is the MAIN terran.exe thread spinning.

## Conclusion
- The turn stall is **NOT a thread deadlock** and **NOT DirectPlay** (M3). The main game thread
  **spins in a busy-wait loop** waiting for a condition that never becomes true (a flag / clock value /
  message that Wine never advances).

## Next (M5) — pin the spin target
Wine blocks gdb `bt` past ntdll, but gdb CAN read `$pc`/`$esp`/stack and set breakpoints. Pick ONE:
1. **Poor-man's profiler**: gdb attach, sample `info registers eip` ×N (proc eip reads 0, so use gdb),
   find the hot terran.exe address, map to a Ghidra `FUN_` by subtracting terran.exe's runtime load base
   (from `info proc mappings` in /tmp/gdb_bt.txt).
2. **Break on the likely spin source** — Win32 clock/message functions the loop probably polls:
   `GetTickCount`, `QueryPerformanceCounter`, `timeGetTime` (winmm), `GetMessage`/`PeekMessage` (user32) —
   inspect how the loop consumes the returned value. (A `while (now < deadline)` on a clock Wine doesn't
   advance would spin forever.)
3. **Wine trace that actually emits**: `+win32`/`+msg`/`+winex.win32` around the turn (NOT `+timer`, which
   emitted zero lines here) to see if a WM_TIMER/message the loop waits for is missing.

## Caveats
- Addresses 0xee… = libc/vdso. Game code is at terran.exe's runtime base (see `info proc mappings`);
  subtract that base to map a hot `$pc` to a Ghidra `FUN_`.
- The busy loop might be SMAC's normal per-frame render/animation (it animates continuously). Distinguish
  a STUCK tight loop (hot `$pc` sits in one function) from normal animation (hot `$pc` cycles) before
  concluding "stuck." Confirm via M5 step 1.
## M5 perf profile (2026-10-20) — refines M4: it's a message pump, not a clock-spin

perf 7.0.14: `perf record -t <main-tid> -F 250 -o /tmp/m5.perf -- sleep 3` at the stall (Year 2101
unchanged). terran.exe runtime base = **0x400000** (so a runtime IP == its Ghidra VA directly). The
profile is **FLAT across Wine message-pump machinery**, not a single hot game function:
- `__wine_syscall_dispatcher` 8.2%, **`NtYieldExecution` 2.2%** (a YIELD inside the loop),
  `server_call_unlocked`, `read_reply_data`, `pthread_mutex_lock`/`pthread_sigmask` (Wine server + threading).
- win32u **`peek_message` + `get_shared_queue` + `call_message_hooks`** → a live PeekMessage/DispatchMessage pump.
- terran.exe game code spread thin: 8+ distinct functions at ~1–2% each, **none dominant** (top ~1.9%).

**Conclusion:** the main thread is NOT stuck in one hot game function and NOT busy-waiting on a clock —
it is a healthy, continuously-yielding Windows message loop. The turn simply is not advanced by the game's
own turn logic. (M4's "spinning on a condition" was right that it's CPU-bound, but perf shows it's the
normal pump, not a stuck compute spin.)

**Next (M6):** instrument the game's turn-ADVANCE path. After TURN COMPLETE, does the client DONE TURN
(0x8301) → server EXEC DONE/NEXT TURN path (dispatcher `FUN_0052bce0`, case 0x4404) ever run? gdb
breakpoint on `FUN_0052bce0` / the 0x8301 handler, or a Wine `+winex.win32`/`+msg` message trace, to see
whether the turn-advance message is posted/dispatched at all. perf data: `/tmp/m5.perf`.


## M6 dispatcher instrumentation (2026-10-20) — solo bypasses the netcode dispatcher

Confirmed live HUD (Year 2101, no dialog), game responsive, then TURN COMPLETE→Yes→OK. gdb breakpoint on
`FUN_0052bce0` logging the message type `*param_1` (auto-continue; "Breakpoint 1 at 0x52bce0"):
**ZERO dispatcher hits** across the whole turn attempt. The game kept running (main thread state R) and its
state visibly changed (Energy 10→11, unit panel populated), so clicks registered and the game was processing.

⇒ **Single-player does NOT route turn/action processing through the netcode packet dispatcher
`FUN_0052bce0`** — consistent with M3 (no DirectPlay session in solo). Solo applies game logic via direct
in-process calls, not the packet dispatcher. (The skill's "action-exec dispatcher is the source of truth —
server and solo alike" is likely WRONG for solo.)

Caveats: (1) not yet positive-controlled that 0x52bce0 is the exact executed address in solo — add a control
bp on the WNDPROC `FUN_005d0c33` (hits on mouse clicks) to validate the bp mechanism. (2) Whether a turn
actually advanced is ambiguous (Energy 10→11 could be the initial tick or income; research counter not captured).

**Boot pitfall corrected:** the earlier "gdb disrupts the splash" theory was WRONG — the intro movie renders
slowly under llvmpipe, so blind clicks fire too early and the game looks stuck on the title. **Press
Return/Space/Esc to skip the intro**, then base-naming OK (400,171). Boot is just slow, not gdb-dependent.

**Next (M7):** control-bp on WNDPROC `FUN_005d0c33` to validate the bp mechanism; then bp candidate solo turn
functions (turn upkeep `FUN_00520e70`, the DONE-TURN sender) to find where solo's turn logic actually runs;
instrument the year/research counters to confirm whether a turn advances. gdb log: /tmp/m6b_dispatch.log.


## M7 positive control (2026-10-20) — gdb breakpoints DO fire on terran.exe code ⇒ M6b is valid

Control gdb breakpoint on the WNDPROC `FUN_005d0c33` (auto-continue, log "HIT"), attached at the splash/menu.
It fired **403 times** (the window proc handles all WM_PAINT/mouse traffic). ⇒ gdb breakpoints work reliably
on the self-modifying/unpacked terran.exe code region (runtime base 0x400000 — the same region as `FUN_0052bce0`).

⇒ **M6b's zero dispatcher hits is REAL, not a gdb artifact: single-player genuinely does NOT call the netcode
packet dispatcher `FUN_0052bce0`.** Solo turn/action logic runs via direct in-process calls, not the packet
dispatcher. (Confirms M3: solo doesn't use the netcode transport.)

**Next (M8):** locate the solo turn-advance path directly — breakpoint candidate solo turn functions
(`FUN_00520e70` upkeep, the DONE-TURN sender path) and instrument the year/research counters; trace what TURN
COMPLETE triggers in solo and why it stalls. Log: /tmp/m7_ctl.log.


## M8 solo turn-advance instrumentation (2026-10-20, session 9) — turns DO advance; netcode end-turn chain is NOT used

**Setup.** Fresh boot (title→live HUD Year 2100/Energy 10 in ~2 min after cleaning stale
Wine processes, see confound below). gdb 17.1 `-batch -p <terran pid> -x /tmp/m8b_bp.gdb`
with 11 auto-continue logging breakpoints, log `/tmp/m8b_hits.log`:
`0x522240`→ET_MASTER, `0x521ee0`→ET_LOOP, `0x521bc0`→ET_PROCEED, `0x527ca0`→PUMP,
`0x520e70`→UPKEEP, `0x521070`→P1070, `0x51e700`→F1E700, `0x5815d0`→PEND,
`0x584010`→SEND <arg1>, `0x52bce0`→DISP <arg1>, control `0x5d0c33`→CTL.
(Ctrl bp is cdecl-verified: `push 0x8301` is the LAST push before `call 0x584010`, and
`0x584010` reads `ax` from `[ebp+8]`, so arg1 == `*(u32*)($sp+4)` at entry.)

### Observed (counts from /tmp/m8b_hits.log)
- Control CTL: **23,544 hits** (~59/s while idle) ⇒ breakpoints fire; M7 re-confirmed.
- **7 turns advanced**: Mission Year **2100 → 2107**, Energy **10 → 17** (screenshots
  `/tmp/m8_6.png`, `/tmp/m8_10.png`, year crops `/tmp/m8_t1..t7.png`, `/tmp/m8_15_yr.png`).
  The turn cycle is NOT inherently broken under Wine automation.
- **ZERO hits** (total 0/70,583 log lines) on ET_MASTER `FUN_00522240`, ET_LOOP
  `FUN_00521ee0`, ET_PROCEED `FUN_00521bc0`, PUMP `FUN_00527ca0`, UPKEEP `FUN_00520e70`,
  P1070 `FUN_00521070`, PEND `FUN_005815d0`, SEND `FUN_00584010` (packet builder),
  DISP `FUN_0052bce0` — across all 7 completed turns.
- **`FUN_0051e700` is the hot function of the solo turn advance: 47,004 hits.** Pattern is
  clean: 0 hits while the game is idle, ~220–560/s while a turn resolves (one turn = +6,752
  hits in ~12 s), back to 0 when idle.

### Inferred
- `FUN_00522240` ("Clearing turn semaphore", sends DONE TURN `0x8301`, waits on the
  `DAT_0091f6c4`/`_DAT_00985b10` player semaphore, then `FUN_00521ee0` "Entering 'end of
  turn' loop" → "Proceeding to next turn") never runs in solo ⇒ **that whole
  semaphore/packet end-turn machinery is the multiplayer/host path**, not solo. Consistent
  with M3 (no DirectPlay) and M6b/M7 (dispatcher never fires): solo also skips the packet
  *builder* `FUN_00584010`, not just the dispatcher.
- Solo's per-turn work runs under **`FUN_0050f420` / `FUN_0050ef60` → `FUN_0051e700`**
  (local E8 scan + prologue-heuristic containment: callers of `0x51e700` = `FUN_0050ef60`,
  `FUN_0050f420`, `FUN_00520c10`, `FUN_00522240`). `FUN_0051e700` (0x51e700–~0x51f730)
  gates on `DAT_00985ae8` bits 0/3 and touches the same turn-semaphore globals the MP path
  uses (`DAT_0091f698`,`0x91f6a0`,`0x91f6b8`,`0x91f6c4`,`0x91f6c8`,`0x91f6d0`…) — i.e. it
  drives the semaphore directly instead of via packets.

### The M4–M7 "stall" reproduces as a UI/automation artifact (observed)
- Periodic **modal dialogs block TURN COMPLETE**: seen this run — "ABOUT RESEARCH" (OK bar
  ≈(400,347)) and "CONFIRM RESEARCH PRIORITIES" (EXPLORE/DISCOVER/BUILD/CONQUER rows, OK bar
  ≈(400,270); blind clicks toggled BUILD). While one is open: CTL ~59/s, F1E700 0/s, main
  thread state R, no year change for 45+ s — **exactly the M4/M5 signature** (busy normal
  message pump, no turn-advance code running).
- Blind clicks at the end-turn-dialog coords land on the map/info panel when no dialog is
  open and can open those ABOUT popups.
- **System confound (must clean before any measurement):** 10 orphaned `winedevice.exe`
  processes from earlier sessions (ppid = systemd --user, `WINEPREFIX=/home/n100/.wine-smac32`)
  were each burning ~40% CPU — load average 12.0 on 4 cores. The title/intro crawled and
  blind clicks mistimed. `kill -TERM` on them dropped the load; boot then reached the live
  HUD in ~2 min.

### Corrected live geometry (window at 0,0, 800×600, screenshot px == click px)
- TURN COMPLETE button ≈ **(650,410)**. OPERATIONS DIRECTOR end-turn confirm: Cancel
  (300,171), **"Yes, and the turn." (300,197)**, OK bar **(400,222)** — NOT the previously
  recorded (300,231)/(400,257). Base-naming OK (400,171). ABOUT RESEARCH OK ≈(400,347);
  CONFIRM RESEARCH PRIORITIES OK ≈(400,270).
- Screenshot pipeline (no ImageMagick on this box): `xwd -root -silent -out f.xwd &&
  ffmpeg -i f.xwd -vf crop=800:600:0:0 -y f.png`; year/energy crop for cheap vision:
  `-vf crop=250:60:555:550`; stack several crops with `-filter_complex vstack=inputs=N`.
- After `kill -TERM gdb` (batch mode, inferior stopped at the time) terran.exe is left
  state `T`; **`kill -CONT <pid>` revives it** (state R, utime climbing).

### Next (M9)
1. Dialog-aware play loop (screenshot → if a modal is open click its OK → TURN COMPLETE) for
   15–20 turns; if a genuine stall still appears, capture which bp fires/hangs at that year.
2. Decompile `FUN_0051e700` (0x51e700–0x51f730) + `FUN_0050f420` + `FUN_0050ef60` via REA
   Ghidra to map solo's per-turn sequence (upkeep / production / AI) and its exit gates.
3. gdb backtrace at a `FUN_0051e700` hit — the trap stops *inside* terran.exe code, so the
   EBP chain may unwind within the game even though bt won't unwind past ntdll (M4).

### Caveats
- Breakpoint trap overhead (~300–560 hits/s) slowed the game but did not stop turns from
  advancing; all bp commands auto-continue.
- Year/energy read from HUD screenshots (crops), not from game memory.
- Caller attribution for `FUN_0051e700` uses local capstone E8-scan + `push ebp/mov ebp,esp`
  heuristic containment (agrees with Ghidra names on every known pair checked), not Ghidra
  `procedure_callers` (whose direction can be inverted).
- Game left RUNNING at Year 2107 (terran.exe pid 3042382, WINEPREFIX ~/.wine-smac32,
  Xvfb :99); kill with `pkill -f '[t]erran.exe'; pkill -f '[w]ineserver'`.
