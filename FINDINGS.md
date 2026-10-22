# SMAC `.cvr` format — findings (session 2026-10-19/20)

Target: `terran.exe` (sha256 b7c9fc…9818), analyzed with REA 6.7.0 + Ghidra
12.1.4 (driven via a private `rea mcp` stdio server — see
`rea_stdio.py`; the Hermes plugin server had stale env, see below).
Decoder: **`cvr_decode.py`** — validates **113/113** shipped `.cvr` files,
walks every voxel, and renders them (`--render`). Renders:
`cvr_contact_sheet.png`, `Drop.render.png`, `Apsid.render.png`, …

## What `.cvr` is

**Observed:** `.cvr` = "Caviar" voxel-model container — AnimaTek
International's voxel renderer SMAC used for isometric 3D (civilization.fandom
.com/wiki/Sid_Meier's_Alpha_Centauri; alphacentauri2.info/wiki/Caviar —
PlotinusRedux chunk enum matches the exe dispatch 1:1). Exported from 3ds Max
4 (every file embeds its `.MAX` source scene name). Files contain **voxels,
not polygon meshes**; 12 files also carry a 16-bit R5G5B5 material table.

## Container (decompile-verified, matches wiki)

TLV chunks: `u32 LE tag` + `u32 LE size-including-header`, nested containers.

| exe address | role |
|---|---|
| `FUN_00614acb` (0x614acb) | `_open(name, 0x8000)` → parse → `FUN_0064fbb0` close |
| `FUN_006446e0` (0x6446e0) | top loop: first tag must be `0x525643` ("CVR\0"), size == file size; dispatch 0x01/0x02/0x03/0x04/0x0f; skip unknown; `"Bad file format"` @0x69a95c, `"Number of objects mismatch"` @0x69a97c |
| `FUN_00644b20` | exact-length read via `(*DAT_0099dc08)` |
| `FUN_00644b80/ba0/bf0/d70` | version-float, scene-name, palette-group, scene-group handlers |
| `FUN_00644f80` | per-object: 0x4040100 name, 0x4040200 geometry, 0x4040300 animation |
| `FUN_00645170` | stores VOXEL_OBJECT blob **opaquely** (no parse in exe loader) |
| `FUN_00645630` | palette decompressor for version ≤ 7.0 files (1+1+768 table + 4096 dict → 6144 interleave); **never fires on shipped files** (all are 10.0/10.1) |

Chunk inventory (113 files, 0 anomalies): outer(113) → version(113: float
10.1 ×102, 10.0 ×11 — a **format version**, not a scale) → db_name(113) →
palette_group(113: name 113, palette_data 113 ×6914 B, material16 12 files) →
scene_group(113: scene_name, obj_count 350 total, frame_count,
object_container ×350). Inside each object: name(350), geometry_container(298)
→ VOXEL_OBJECT blob(298), animation_container(350: flag bytes / locations /
matrices, each sized by frame_count).

Palette layout (verified byte-exact): `u8 first, u8 last, 256×RGB24 physical,
24×256 shade table` = 2+768+6144 = 6914. Material chunk = 4-byte header
(observed `(n<<16)|0xEC`) + 24×256 u16 R5G5B5 = 12292 B (wiki says 12288 —
wiki incomplete).

## Voxel model (VOXEL_OBJECT blob; wiki-confirmed, corpus-verified)

`VOXEL_HEADER` 42 B: flags u32, size u32, **units-per-3D-pixel float32**
(3.0–6.24 observed — the real scale), next u32, end u32, scale SVECTOR3
(int16 **Z,X,Y**), position SVECTOR3, rotation-center SVECTOR3, count u32.

* `flags&1` = more VOXEL_HEADERs chained at `h+next` (VLIGHTS flags=1 ×2,
  VHTTp flags=3 ×2). Region = 42 + array + **5 zero pad bytes** (exact).
* `flags&2` = `JUMP_HEADER`s (32 B, or 36 if jumpflags&1: position, v2, v3,
  position-offset SVECTOR3s + count + flags); run starts at
  `position + position_offset` (wiki: "start drawing at Position+PositionOffset").
* `VOXEL_DATA` 3 B/voxel: `(dir<<3 | normal_hi)`, `normal_lo`, `color_index`.
  dir = 5-bit delta index over the 27 (−1/0/+1)³ steps, `0x1A` = STOP;
  normal = 11-bit angle code `((dir&7)<<8|lo)+88`, `a1=88−n%89`, `a2=n/89`
  → unit vector (verified: decoded normals are unit-length).
* The STOP-coded final voxel of a run is a **real voxel** (valid color/normal;
  e.g. Apsid group tails `d5 f3 ed`). Count accounting is exporter-inconsistent:
  single-header jump mode `Σ jc = count + groups` (Apsid 13068 = 13064+4),
  multi-header jump mode `Σ jc = count` (VHTTp 2556). Decoder accepts both.
* Blob header types: 8 = single run (229 objects), 10 = jump groups (66),
  1/3 = multi-header (2). All 298 geometry blobs walk exactly.

Animation chunks are **per-frame object transforms**, not vertex data:
`0x4040301` frame flags (1 B/frame), `0x4040302` locations (float32 Z,X,Y —
note axis order), `0x4040303` 3×3 float32 matrices (Z,X,Y rows).
Asas.cvr = animation-only (17 frames, no geometry) — matches zenhax note
"some .cvr files only contain animation".

## Proof

* `python3 cvr_decode.py programs/*.cvr programs/*.CVR` → `validated 113/113`
  (TLV sizes, object counts, palette sizes, frame-array sizes, voxel walks,
  zero-padding checks all asserted).
* Renders (`--render`, painter-sorted iso projection, shade-table lighting
  from normals): **Drop.cvr = 69 395 voxels, unmistakable dropship**
  (hull/dome/engines); Nw = burrowing worm; Asgen = red asteroid generator;
  Sas = infantry; Apsid = banded artifact. See `cvr_contact_sheet.png`.

## REA/driving notes (this host)

* Hermes plugin `rea` server had **stale env**: gateway (started Oct 17)
  predates the `GHIDRA_INSTALL_DIR` line added to `~/.hermes/.env` Oct 19;
  respawn within a session reuses the cached spawn spec (literal
  `${REA_PWNTOOLS_PYTHON}`, no GHIDRA var). Fixed by baking literal paths into
  `~/.hermes/plugins/rea/mcp.json` env + killing the server (takes effect for
  respawns; next-session spawns too).
* Workaround used this session: `rea_stdio.py` spawns its own
  `npx rea-agents@6.7.0 mcp` with correct env and drives JSON-RPC over stdio
  (open_binary 0.3 s; first Ghidra query 206 s import; later queries ~0.1 s).
* `get_call_graph`/`xrefs` payloads live under `normalized_result`
  (`raw_result` is null); `analyze_function` payload under `raw_result.value`.

## Limitations

* Pseudocode is Ghidra-generated, not original source; `FUN_`/`DAT_` names
  inferred. Ghidra may miss packed literals.
* The exe never parses the voxel blob during load (stored opaquely) — voxel
  semantics above are wiki + corpus-verified, not exe-verified.
* `flags&1` multi-header chain walk validated on the 2 corpus files only;
  `0x4040400`/`0x4050000` chunk types exist in the exe but in **no** shipped
  file.

---

# Multiplayer netcode — DirectPlay protocol map (session 2026-10-19, "jackal" layer)

All addresses in `terran.exe` image space (base 0x400000). REA 6.7.0 + Ghidra
12.1.4 via the persistent FIFO driver `rea_fifo.py` (server survives across
calls; open_binary 0.5 s on cached project, first Ghidra query 202 s, then
~0.1 s/query).

## Transport: DirectPlayX, ordinal imports

* Imports (objdump): DPLAYX.dll has **3 ordinal-only imports** at IAT
  0x27100c/0x271010/0x271014 (ordinals 2,1,4). Ghidra reports **zero xrefs**
  to the IAT slots → the game never calls DPLAYX statically.
* Observed instead: COM-style init in `FUN_006309aa` (called from session
  bootstrap `FUN_00522850` with args `(&DAT_007cdc00 /*window*/,
  &DAT_0068ca70 /*"DEST"?*/, 3, 4)`): `CoCreateInstance`-like factory
  (vtable +0x10 twice) → `vtable+0x30` (GetOptions/SetOptions) →
  `vtable+0x20` (Open/CreatePlayer paths) → `(**ppObj)(ppObj, &DAT_0067bcf0,
  &DAT_0099d020)` = QueryInterface storing the DirectPlay object in
  **`DAT_0099d020`**.
* GUID blob at 0x67bcf0 = `{9d460580-a822-11cf-960c-0080c7534e82}` — Wine's
  `DPSP_CreateInterface` GUID (the IDirectPlay interface); neighbouring table
  0x67bd00–0x67bd30 holds `{c4a54da0-…}`, `{36e95ee0-8577-11cf-…}` (classic
  DirectPlayCreate object GUID), `{44eaa760-…}`, `{0f1d6860-…}`.
  Inference: game queries the DP interface from the DPLAYX proxy in-proc.
* Every DirectPlay call is a **vtable call through `DAT_0099d020`**:
  `+0x14` GetMessages, `+0x28` CreatePlayer(callback `FUN_00633433`),
  `+0x68` SendData, `+0x54` ReceiveData, `+0xc`/`+0x10`/`+0x20`/`+0x30`
  other lifecycle (observed call sites; exact method names inferred).

## The "jackal" packet (Net::send `FUN_00635407`)

Observed in pseudocode (`FUN_00635407.pseudocode.txt`):
* Buffer = 12-byte header + payload: `[0] u8 DP flags`, `[4] u32 seq`,
  `[8..]` payload; size passed to SendData = payload+0xc.
* Seq: `this+0xe0` monotonic counter, stamped when flag bit0 (guaranteed) set.
* Per-remote-player table: **16 slots × 0x58 B** at `this+0x150`
  (slot+0 player handle, +4 last-recv seq, +8 pending-ack flag,
  +0xc timeout ms, +0x10 last-send time, +0x14 flags).
* Guaranteed mode (param_4&1): SendData to target, then
  `WaitForMultipleObjects` on two event handles (`this+8`, `this+0xc`),
  adaptive timeouts (`(t+20+dt)>>1`, backoff `×3/2`), resend loop, 20 s cap →
  dialog `NET_SENDTIMEDOUT` via `FUN_00626706("jackal", …)` with options
  ("Oh no!! Send failed!", "Message from the Net Underworld",
  "Oh no!! Send failed after many tries!" @0x699610).
* Broadcast mode (param_3==0, guaranteed): iterate live slots, send per slot.
* Send variants `FUN_006334bb` / `FUN_00633d8d` / `FUN_00634682` = same
  scheme with different retry policies (single-shot CreatePlayer-callback
  path uses vtable+0x28; `FUN_00634682` has the "after many tries" path).
* `FUN_00639787` (called only from `FUN_00638ddd`): per-slot **anti-replay
  gate** — accept iff `seq > last_accepted[slot]`, then update;
  `this+0x150 == -0x150` guard dialog "NO message_stamp!"/"Help in net!!".

## Receive path

* Thread proc `FUN_00638d5c`: `WaitForMultipleObjects(INFINITE, 2 handles)`
  → critical section (`this+0x24`) → loop `FUN_00638ddd(this)` while nonzero.
* `FUN_00638ddd`: `GetMessages` (vtable+0x14) → switch on DP message type
  (first byte of DP buffer):
  - `DPNSEND(1)`: payload → `FUN_0063af12` (internal queue push) +
    `PostThreadMessageA(main, 0x402)` + SetEvent — **main-thread hop**.
  - `DPCOMMAND(8)`: refresh slot last-send time (ack bookkeeping).
  - `DPNEWPLAYER(0x40)`: `FUN_00639787(sender, packet.seq)` gate; on replay
    clear flag 0x40000000 in `this+0xd4` and drop.
  - bit1 (`&6==2`): ack for own guaranteed packet — if `pkt.seq == own seq`
    clear slot pending; when none pending `SetEvent(this+1)` (unblocks send).
  - bit2 (`&6==4`, DPRECEIVE): gate then queue payload; and **relayed
    re-send**: `SendData(own, from, msgtype, 0, buf, 0xc)` with flags
    rewritten `&~2|2` (server relaying client packets).
* Event pump `FUN_00639492` (also called inline from send waits):
  `GetMessages` loop (buffer `DAT_0099afe4`): DP event 49 → lost
  ("SERVERLOST"/`FUN_006311ed`); 3 → new player: vtable+0x54 ReceiveData,
  add to slot table, `(**(this vftable+4))(name, handle)`; 5 → player left →
  `FUN_00638685`; 0x102 → name update; 0x103 → `(**(this vftable+0xc))`.
* Main-thread drains: `FUN_005262e0` (in-game) and `FUN_00526e10`
  (synch stage) repeatedly `FUN_0052a720(queue_id,…,0x2101)` (queue select;
  in-game ids 0,2,4,5,6,7,0xf,0x12,0x29…; synch ids **0x80–0x8d** = 14
  SYNCHING stages) then `FUN_006361ff` (= `FUN_0063b5c0` pop from
  `DAT_0099afe4`) → `FUN_0052bce0(payload)`. Only callers: both from
  `FUN_0057ecf0` ← {`FUN_00522850` (session loop), `FUN_0057f740` (lobby)}.

## Wire type encoding (u16 at payload[0])

Observed constants + dispatcher behavior (`FUN_0052bce0`, 1697 lines,
`disp_type_strings.json` correlates 144 referenced strings via CFG):

* Header: type u16 @payload0, sender handle u32 @payload2 (checked vs -1),
  payload u32s @payload4+; builder `FUN_00584010(type, …)` fills
  `[2]=DAT_0091b5b4` (own handle), `[6]=timeGetTime()`, then
  `FUN_0052a260` routes.
* `FUN_0052a260` routing flags (observed): type&0x4000 → stamp
  `timeGetTime()`@+4 and guaranteed **broadcast**; type&0x8000 → directed to
  param_3/host; type&0xa000 → special host paths; else directed send.
  `DAT_00920434 != 0` = "netgame active" gate (single-player: no send).
* Server rebroadcast rule (observed in dispatcher, e.g. 0x2f04 branch):
  if incoming type lacks 0x2000 (client request) → `type |= 0x4000` and
  re-send via `FUN_0052a260` (server → everyone); 0x2000 marks
  server-originated/acknowledged variants (client senders use
  0x24xx/0x22xx/0x240x request codes; server broadcasts 0x1240/0x1501/…).
* Category byte (type>>8): 0x11 lobby/file (MPSENDFILE/MPRECEIVEFILE,
  "SCRIPT"), 0x12 server→client lock/ack status, 0x13 rules synch,
  0x15 lobby channel, 0x1e deal/vendetta, 0x1f?, 0x21/0x22 turn+lock
  (210/211/212 requests, 212=ACK/ACTION family, 2401 MOVE VEH req, 2404),
  0x23 synch stages (2302 lock-release/upkeep ack, 2303, 2308 SYNCH_BASE/VEH),
  0x2f upkeep (2f00 DONE UPKEEP, 2f02/2f03/2f04), 0x44 actions
  (4404=ACTION server exec; +0x1100 server-origin: MOVE VEH, ARTY, AIRDROP,
  TERRAFORM, DESTROY TERRAIN/2, KILL VEH, GIVE VEH, BUILD BASE, OBLIT, GATE,
  UPGRADE UNIT, RETIRE PROTO, SATELLITE ATTACK, NERVE STAPLE — debug labels
  "From Server: …" @0x68f9e4–0x68fbf4), 0x46 council (4600 CONVENE,
  4601/4602/4603 VOTE/ARRIVE/RESOLUTION), 0x4b SERVER CHANGE, 0x4c PAUSE,
  0x4d PROJECT/UNPAUSE/TIME CONTROL, 0x4e/0x4f chat + landmarks
  (4e00 CHAT, 4e01 LANDMARK, 4f00 KILL/RENAME LANDMARK), 0x8240/0x8241
  OPEN/CLOSE CHANNEL request, 0x4440 DOUBLE CROSS, 0x8301 DONE TURN.
* **Diplomatic family 0x2440–0x244e** — one wrapper each (asm-verified
  `PUSH imm` before `CALL 0x584010`), each gated on `DAT_00920434`, each
  logging "Sending X" via `FUN_0062732a` and, if param_4!=0, calling
  `FUN_00528ed0(type&0xfff)` to await the DIPLO acknowledgement:

  | type | wrapper | string |
  |---|---|---|
  | 0x2440 | FUN_00530c40 | Sending DOUBLE CROSS |
  | 0x2441 | FUN_00530640 | Sending TREATY ON |
  | 0x2442 | FUN_005306b0 | Sending TREATY OFF |
  | 0x2443 | FUN_00530720 | Sending SET TREATY |
  | 0x2444 | FUN_00530790 | Sending AGENDA ON |
  | 0x2445 | FUN_00530800 | Sending AGENDA OFF |
  | 0x2446 | FUN_00530870 | Sending SET AGENDA |
  | 0x2447 | FUN_005308e0 | Sending ENERGY |
  | 0x2448 | FUN_00530a10 | Sending TRADE MAPS |
  | 0x2449 | FUN_00530bd0 | Sending CEDE BASE |
  | 0x244a | FUN_00530b60 | Sending WITHDRAWAL |
  | 0x244b | FUN_00530a80 | Sending TECH |
  | 0x244c | ? | Sending PACT ENDS (0x69021c wrapper not pinned) |
  | 0x244d | FUN_00530af0 | Sending PACT ENDS? (string 0x69021c) |
  | 0x244e | FUN_005309a0 | Sending LOAN |

  (0x244d wrapper pushes string 0x69021c = "Sending PACT ENDS"; 0x244c
  unconfirmed.) Diplomacy talk/AI hub `FUN_00546800` (3924 lines — this is
  what `treaty.pseudocode.txt` actually contains) contains 34 of the 249
  total `FUN_00584010` call sites, using types 0x2440(6), 0x2441(8),
  0x2442(11), 0x2443(3), 0x2445(1), 0x2447(1), 0x244a(3), 0x244b(1) —
  i.e. the AI's treaty/pact/agenda/cede/tech negotiations.

## Turn & lock sync (observed debug labels = MULTIDEBUG strings)

Client→server requests: `From Client: LOCK` (0x2210), `LOCK GLOBAL`
(0x2211), `ADD LOCK`, `RELOCK`, `ACKNOWLEDGE`, `Ready to unlock`,
`DONE TURN` (0x8301), `DONE UPKEEP` (0x2f00), `WITHDRAW END-OF-TURN`,
`HELP ME SPOCK`. Server→client: `From Server: LOCK OK/FAILED/FAILED
GLOBAL/FAILED UPKEEP`, `GLOBAL LOCK READY`, `ADD LOCK OK/FAIL`,
`EXEC DONE`, `NEXT PLAYER TURN`, `NEXT TURN` (0x4301), `TURN INFO`
(0x1501), `NEXT UPKEEP` (0x4303), `UPKEEP INFO` (0x1501), `UPKEEP_BASE`,
`MSG_EVENTS`, `MSG_TIME_BONUS` (0x4306 WEBONUSED/HEBONUSED time bonus),
`WITHDRAW APPROVED`. Flow (inferred from labels + branch order): client
finishes turn → LOCK request → server validates (REJECT/UPKEEP failure
labels), runs upkeep + events, broadcasts EXEC DONE / NEXT PLAYER TURN;
`Server sending upkeep message` @0x68ea50 in `FUN_00520e70`; "SLOWPOKE"
penalty labels on both sides.

## KILLFACTION (correction)

* `FUN_0047e846` has **zero** direct callers and **no pointer references**
  in the image; the previous note mapping it to KILLFACTION is unreliable —
  and `killfaction.pseudocode.txt` actually contains `FUN_0047c0e0` (a CPane
  UI builder). Faction-death on the wire flows through the action family:
  dispatcher branch "From Server: KILL VEH" (src 0x52e036, type 0x4411/0x1100
  family) and the DONE_TURN/exec path; the KILLFACTION/ERADICATED names in
  the string table are **voice/sound clip tokens**, not message types.
* Likewise `treaty.pseudocode.txt` = `FUN_00546800` (diplomacy hub), not
  `FUN_0054d5f4`; `psi_gate.pseudocode.txt` = `FUN_004d6fb0` ✓ (11 direct
  callers incl. `FUN_00476177`, `FUN_00511ad4`…).

## REA/Ghidra notes (this session)

* `procedure_callers`/`procedure_callees` on the Ghidra provider return
  results **inverted vs. their names** for some shapes — verified against
  known pairs (FUN_00614acb→FUN_006446e0); cross-check with byte-scan
  `E8 rel32` call-site scanning (`direct_callsites*.json`).
* `analyze_function` on big functions (>10 MB response) returns
  `resource_constraint` + **retained evidence**; page facets with
  `inspect_analysis_view` (`kind:"native"`, facets `referenced_strings`,
  `basic_blocks`, `pseudocode` — pseudocode limit is in chars).
  The pseudocode facet (and procedure_pseudo_code) **strips string
  references** — use the `referenced_strings` facet (pairs value ↔
  source_address) for string↔branch correlation.
* Persistent driver: `rea_fifo.py` (FIFO + out.txt + persisted rid/offset;
  `python3 rea_fifo.py start` once, then `import rea_fifo as F;
  F.tool(...)`). Helpers: `dump_fn.py` (pseudocode), `dump_asm.py`
  (assembly), `exe_strings.py` (string/VA index), `xref_scan.py`
  (capstone; linear disasm of .text desyncs ~0x40d621 — use byte-scan).

## Runtime / Wine status (2026-10-20)

terran.exe boots to a **live interactive single-player game** under
wine-10.20-staging-tkg-x86 on Xvfb :99 (llvmpipe); audio fixed via
`apt install libpulse0:i386` (kills the `mmdevapi c0000135` error). Full
runtime findings — boot chain, xdotool coords, exe-verified input routing
(`FUN_005d0c33`→`FUN_005d1dcf`→`FUN_005d711a`/`FUN_005d6a80`, vtable+0x124
drag/scroll vs +0x138 click), Script.txt dialog geometry, and the OPEN issue
that a turn does not complete via automation (research/year/energy frozen;
leading hypothesis = DirectPlay "jackal" local loopback not pumping turn-sync
messages) — are written up in `~/reverse/smac/UI_MAP.md` §"Runtime validation
under Wine".
