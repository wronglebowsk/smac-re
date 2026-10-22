# SMAC turn machinery — static map (M8a, 2026-10-20)

Derived offline from the saved capstone dump `.text_insns.json` + the Ghidra
function table `.func_starts.json` / `.func_names.json` (10 284 procedures, pulled
once via `list_procedures`), plus REA `xrefs` on the game's own debug strings.
Helpers: `callgraph.py` (callers/callees/up, now using exact Ghidra function
bounds), `ptr_xref.py`. All addresses are Ghidra VAs == runtime IPs (terran.exe
runtime base 0x400000).

## Call chain (solo, direct E8 edges only — verified against Ghidra owners)

```
entry 0x64dbe0
  -> FUN_00466400
    -> FUN_00522850            (startup; calls DP-init FUN_006309aa — see dplay_solo.md)
      -> FUN_00520c10          (pre-loop setup; plays ENDOFTURN/ENDOFTURN1 voice clips
                                via FUN_0050f420 x3 at 0x520c82/dfb/e56)
      -> FUN_00522240          *** THE TURN LOOP (do{}while(true), never returns
                                except on the exit path) ***
        -> FUN_00521070        per-turn processing: UPKEEP5/6/7 phases
                                (strings @0x521541/0x5215b0/0x521767), "Enemy turn "
                                (@0x521575), "Writing save file" (@0x521688),
                                "Skipping upkeep phase" (@0x521b8e);
                                calls turn upkeep FUN_00520e70 x8
        -> FUN_00521ee0        *** "Entering 'end of turn' loop" (0x52200c) — the
                                end-turn WAIT + next-turn advance (see below) ***
        -> FUN_00527ca0 x3 / FUN_00527c60   message+netcode PUMP helpers
                                (both are among the 50 callers of the packet
                                dispatcher FUN_0052bce0)
        -> FUN_00584010 x2     packet builder (sends 0x4309 / 0x8301)
        -> FUN_0050f420 x1     end-of-turn voice/handler @0x52260d
```

`FUN_00522240` body = `do { … } while(true)` at 0x522240–0x522a3d-ish; it is
called exactly ONCE from `FUN_00522850` (site 0x522a0f) and returns only via
`FUN_0051e700(1) != 0` (line ~95) or `iVar2 != 0` after the inner loop (line 224).

## The end-of-turn wait loop — FUN_00521ee0 (prime suspect)

Disassembly of the hot part (exact, from .text_insns.json):

```
0x521f91  push 0x8301 ; call 0x584010      ; SEND "DONE TURN" (0x8301) — even in solo
0x521f9b  mov edi,[0x671368]               ; IAT slot -> timeGetTime
0x521fa4  call edi ; mov ebx,eax           ; ebx = start time
0x521fa8  LOOP TOP:
          eax = [0x985b10] & 0xff          ; bitmask of all players
          edx = [0x91f6c4]                ; bitmask of players DONE their turn
          ecx = eax & edx ; if (ecx != eax) goto BODY      ; not everyone done
          if ([0x91f6b8] & eax) != 0      goto BODY
          if ([0x91f698] != 0) { call 0x5815d0; if (eax) goto BODY;
                                if ([0x91f6e4]) goto BODY }
0x521fe8  if ([0x991588] != 0)            goto EXIT      ; quit/abort flag
          if (([0x985ae8] & 2) == 0)      goto EXIT      ; "end-of-turn in progress"
0x521ffa  BODY: if (!done-voice && timeGetTime()-ebx > 1000) play "FINISHINGTURN"
0x522020        mov ecx, 0x91db70 ; call 0x527ca0        ; *** the PUMP ***
0x52202a        jmp 0x521fa8                             ; back to LOOP TOP
0x52202f  EXIT: …
0x52204f        log "Ready to proceed" (args: [0x91f6c4], [0x985b10]&0xff)
0x522079        if (([0x985ae8]&2) && [0x991588]==0) {
                  loop over factions ([0x91e2d0] count, entries @0x91f024 stride 0x1c,
                  per-faction test call 0x581150) -> call 0x5e9b70 ; call 0x527c60
                  call 0x584010(0x4301)      ; EXEC-DONE-ish
                  call 0x527c60 }
0x522104  "--- Proceeding to next turn ---" (call site 0x522107)
0x522107+         … call 0x5d8123; 0x50a550; while (call 0x527c60()) ; 0x521bc0; 0x518f80(0)
                  optional autosave; [0x91f694] += 1 ; ret
```

`FUN_00521ee0` line 28: `if (([0x985dc8] & 0x10) != 0) goto LAB_00522104;` — when
bit 0x10 of the mode word `[0x985dc8]` is SET, the whole send+wait is SKIPPED
(that role does its waiting earlier, inside `FUN_00522240` at 0x52260d-ish, where
it sends 0x8301 and pumps `FUN_00527ca0` until `[0x991588]`/turn-owner changes).
In the solo role the wait happens here.

## Why this explains everything measured so far

Solo sends **0x8301 DONE TURN through the netcode packet builder `FUN_00584010`**
and then sits in `while (not-all-done) { pump via FUN_00527ca0(); }`.
- M5 perf: the main thread is a yielding PeekMessage pump with game code spread
  thin ⇒ exactly what `FUN_00527ca0()` (pump) looks like from a profiler.
- M6b/M7: dispatcher `FUN_0052bce0` gets ZERO hits ⇒ the pump finds no packets,
  so nothing ever marks the remaining players done in `[0x91f6c4]`, so the
  condition at 0x521fa8 never becomes false.
- M3: no DirectPlay session ⇒ whatever is supposed to answer DONE TURN (the
  "server" side, per the debug strings "From Server: NEXT TURN" @0x68f814,
  "From Server: EXEC DONE" @0x68f5bc, both inside dispatcher FUN_0052bce0)
  never produces a packet.

**Hypothesis (runtime-testable):** the loop is alive and spinning at 0x521fa8 /
0x522025 with `[0x91f6c4]` missing at least one bit of `[0x985b10]&0xff` (or
`[0x91f6b8]`/`[0x91f698]`+`[0x91f6e4]` keeping it alive), and 0x522107
("Proceeding to next turn") is never reached.

## Instrumentation points chosen for the live run

| addr | meaning |
|---|---|
| 0x5d0c33 | control bp (WNDPROC, fires on paint/mouse) — validates gdb |
| 0x521ee0 | entered end-of-turn function |
| 0x521f96 | sent DONE TURN 0x8301 |
| 0x521fa8 | wait-loop TOP (hit count = spin rate) + dump masks |
| 0x52202f | wait-loop EXIT reached |
| 0x522107 | "--- Proceeding to next turn ---" |
| 0x584010 | packet builder (log type = *(esp+4)) |
| 0x52bce0 | netcode dispatcher (expect 0 hits, re-confirm) |

Globals to read at the stall: `[0x985b10]` all-player mask, `[0x91f6c4]` done mask,
`[0x91f6b8]`, `[0x91f698]`, `[0x91f6e4]`, `[0x991588]` quit, `[0x985ae8]` flags,
`[0x985dc8]` mode (bit 0x10 = role), `[0x91b5b4]` current player, `[0x985dcc]`
turn owner, `[0x91e2d0]` faction count, `[0x991590]`, `[0x91c644]`,
`[0x99d020]` **DirectPlay object pointer** (NULL ⇒ Net::send FUN_00635407 bails).

## Caveats
- Only DIRECT `call rel32` edges are in this graph. Widget/button dispatch is
  virtual (vtable+0x138 per UI_MAP.md), so how the TURN COMPLETE *button* reaches
  `FUN_00522240` is still unmapped — the UI almost certainly just sets a flag /
  posts a message and the turn loop notices.
- `.text_insns.json` is one linear capstone pass from 0x401000; per the REA skill a
  linear pass can desync mid-section. The 0x521fxx–0x5222xx region cross-checks
  against Ghidra pseudocode line-for-line, so it is trustworthy here.
- `procedure_callers`/`callees` from REA are unreliable (inverted); this map uses
  the byte-level call sites + Ghidra function bounds instead.
