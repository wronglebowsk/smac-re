# DirectPlay in SMAC — is SINGLE-PLAYER DirectPlay-based?  (M1, 2026-10-20)

## OBSERVED (from analyzed/unpacked-image pseudocode — see image note)
- Startup/main routine **FUN_00522850** calls DirectPlay init **FUN_006309aa(&DAT_007cdc00, &DAT_0068ca70, 3, 4)**
  (pseudocode line 17) **unconditionally**, right before the intro/opening/main loop. The return value only
  picks a follow-up (`FUN_0057f740(0)` on success vs `FUN_0057ecf0(1)`); DP init is NOT gated behind a
  multiplayer-only branch.
- Init `FUN_006309aa`: `DirectPlayCreate` (Ordinal_4, line 198) → enumerate/connect (vtable +0x20/+0x30) →
  `QueryInterface` GUID **@0x67bcf0** `{9d460580-a822-11cf-…}` (DirectPlay-family GUID, tail 0080C747C965)
  stores the DP object in global **DAT_0099d020** (lines 221–222).
- Transport send `Net::send FUN_00635407`: `if (param_1==0 || DAT_0099d020==0) return` (line 30), then
  `DAT_0099d020->vtable+0x68` (SendData). Same DP-object dependency in `FUN_00634682`, `FUN_006334bb`
  (CreatePlayer via +0x28), and receive thread `FUN_00638ddd` (bails if `DAT_0099d020==0`).

## CONCLUSION
- **YES — single-player uses DirectPlay.** The DP object `DAT_0099d020` is created at startup for every game
  and every send/recv goes through it. Solo = client + server in one process over DirectPlay's local session.
- The turn-completion freeze is therefore **consistent with Wine's dplayx not pumping the local
  client/server message loop** (GetMessages/SendData never complete the turn-done handshake). Not yet proven
  at runtime — that is M3.

## UNVERIFIED / NEXT (M3)
- Exact provider used for the local session (GUID @0x67bcf0; enumerate GUIDs @0x67bd00, @0x67bd10) not resolved.
- Confirm messages actually flow (or stall) at runtime: relaunch with `WINEDEBUG=+dplayx,+dplay 2>>/tmp/wine_dp.log`,
  end one turn, grep for GetMessages/SendData.

## IMAGE NOTE (durable pitfall)
On-disk terran.exe sections: `.text 0x1000–0x271000`, `.rdata`, `.data …–0x59f284`, unnamed/`UVA_DATA`/`_SELFMOD`
`0x5a0000–0x5ac000`, `.rsrc`, `.reloc …–0x5e4000`. But the analyzed `FUN_`/`DAT_` addresses (WNDPROC 0x5d0c33,
`FUN_006309aa`, `DAT_0067bcf0`, …) all sit **above 0x5e4000**, i.e. outside the packed file image. terran.exe is
**self-modifying / unpacks-and-relocates at runtime**; REA/Ghidra analyzed the unpacked image. So its pseudocode is
authoritative, but raw byte-reads of these `DAT_` addresses from terran.exe FAIL (region not in the file). Don't
waste a session trying to read GUID bytes from the packed exe.

## M3 RUNTIME RESULT (2026-10-20, `WINEDEBUG=+dplayx,+dplay,+loaddll` → /tmp/wine_dp.log)
Drove boot chain to a live match, then attempted a full turn (TURN COMPLETE→Yes→OK).
- dplayx loads + works at startup: `DPLAYX_ConstructData` (shared-mem/semaphore) → `DirectPlayLobbyCreateA`
  → `IDirectPlayLobby3A` (lobby GUID {26c66a70-b367-11cf-a024-00aa006157ac}) → `GetConnectionSettings` →
  **"Application 0x00000000 is not lobbied."** (log lines 130–171).
- After startup, through reaching the live HUD AND a full turn attempt, the log stayed frozen at 171 lines:
  **no EnumerateApplications / Connect / CreatePlayer / GetMessages / SendData / ProcessMessage at all.**
  Wine traces every dplayx entry point, so absence of a line = the game never made that call.
- Turn still did not advance: Mission Year 2101 / Energy 11 unchanged (dp_afterturn.png).

### CONCLUSION — refines/refutes the M1 hypothesis
- **Single-player does NOT open a DirectPlay session or pump DirectPlay messages at runtime.** It probes the
  lobby once at startup and finds it unlobbied, then runs with no further dplayx calls. Turn sync in solo is
  NOT riding the DirectPlay loopback.
- Therefore the turn-completion stall is **not** a Wine-dplayx message-pump failure. DirectPlay shims
  (dgVoodoo2 / nGage / glsmac) are NOT the fix for the stall.
- Redirect (M4): investigate the in-process turn loop / "server" tick / threading under Wine — likely a timer,
  Win32 message-loop, or thread-sync dependency Wine handles differently. Not DirectPlay.

### Caveats
- Only +dplayx,+dplay,+loaddll channels enabled, so non-DP activity (timers/threads/win32 msgs) is not visible
  here. The negative is scoped exactly to "no DirectPlay calls," which is what M3 tested.
- On real Windows, SMAC solo likely also skips opening a DP session (DirectPlay is mainly multiplayer), so
  lobby-only startup is probably normal solo behavior — the stall is a Wine-specific issue in the local turn loop.
