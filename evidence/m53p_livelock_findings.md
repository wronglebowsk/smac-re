# M53p addendum — the end-of-turn pipeline was LIVELOCKED; root cause found and cleared (VERIFIED)

Game pid 2124624, year 2382, cur_player 3, `turn_flags` 0x10002 (bit 1 = "end-turn in flight" per
`scripts/smac_state.py` / `references/wine-headless-harness.md:34` — 0 idle, 2 while end-turn runs).
Symptom: driver returns STUCK forever, main thread pegged ~60-65% CPU in state R, screen static.

## 1. Where it spun (VERIFIED by gdb attach + cached disassembly)
- Sample 1: `0x005ab223` in **`FUN_005ab130`**, backtrace 0x5ab223 <- 0x5ab333 <- `FUN_005a5a80`
  (0x5a5beb) <- `FUN_004bf1e0` (0x4c0e0a) <- `FUN_004c1260` (0x4c1288/0x4c12f6).
  Loop 0x5ab223-0x5ab237: `movsx eax,cx / lea edx,[eax+eax*2] / lea ecx,[eax+edx*4]` (= 13*eax =
  52-byte unit stride) `mov cx,[ecx*4+0x9332aa]` (= **unit[i]+50**, u16) `test cx,cx / jge 0x5ab223`
  — walks the unit-index chain in `unit+50` and **exits only when the link is NEGATIVE**.
- After clearing that chain: sample at `0x005a6945` in **`FUN_005a6330`**; loop 0x5a6945-0x5a6955 does
  the same 13*index math and `movsx esi,[eax*4+0x9332a8]` (= **unit[i]+48**, u16) `test esi,esi /
  jge 0x5a637b` — a second chain walk with the same negative-sentinel exit.

## 2. The corrupt state (VERIFIED by /proc pread of the unit array 0x933278, stride 52, count 0x985af0)
- 333 units at first read. Chain census: **unit 113 (fac 2, type 4, tile 45,11) had `+50 = 113` AND
  `+48 = 113` — self-links**, the ONLY cycles in either chain (unit 109 -> +48 113, unit 110 -> +50 113).
  Terminator census before the fix: `+48 == -1` on 201/332, `+50 == -1` on 203/332 — so **-1 is the
  chain terminator** and a self-link is corruption.
- INFERRED root cause: the unit array compacts when a unit dies (observed 333 -> 332 during this very
  window) and the `+48`/`+50` links are INDEX values, so a compaction leaves stale links; a stale link
  pointing at the record's own new index turns either walk into an infinite loop (the walk cannot exit
  because the sentinel is never reached). M53n already recorded that slots shuffle/compact.

## 3. The fix (VERIFIED live, pokes via /proc/pid/mem, no tracer)
- `0x933278+113*52+50` (0x93499e): 0x006d -> **0xFFFF**; readback 0xFFFF, stable.
- `0x933278+113*52+48` (0x93499c): 0x0071 -> **0xFFFF**; readback 0xFFFF, stable.
- Immediately after the second poke `turn_flags` 0x10002 -> **0x10000** (end-turn flag cleared), main
  thread left the spin (gdb sample at `__kernel_vsyscall`), screen began redrawing, and
  `smac_play.py --turns 2 --timeout 190 --no-escape 240` completed **2382 -> 2383 in 57.9 s**.
  Game left idle on our turn, year 2383, TracerPid 0.

## 4. Driving-kit corrections found on the way (VERIFIED)
- `scripts/smac_play.py` has **no `--mode stop`** in this checkout (arg list: --turns --timeout
  --no-escape --verbose --order --unit --turns-after --tag --no-verify --key-only); `--no-escape N`
  means "never press Escape during the first N seconds". Run it with N > the run timeout: the driver
  classified the **"Do you really want to quit?" dialog as a title screen** (its banner text is
  "SID MEIER'S ALPHA CENTAURI") and pressed Escape, which opened that dialog; with `--no-escape 240`
  the run is clean. Clearing the dialog: `xdotool windowfocus <win>` + Escape (never click) — verified
  it returns to the HUD.
- `xwd` needs `-display :99` (DISPLAY=:0 fails on this host).
