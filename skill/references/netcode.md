# netcode

Depth reference for `skill/SKILL.md` (smac-cvr-format) - moved whole at s242;
the hot core in SKILL.md keeps the summary and the pointer.

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
