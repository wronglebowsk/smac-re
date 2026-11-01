# Session notes archive — sessions 172-172

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 172 (cont. 26) — M172-M174 (all PASS): the "bit-decoder" is a SAVE-SECTION WRITER, and the aggregator's counters have three consumers

`python3 scripts/m172_m174_savewriter.py` — SUMMARY M172=PASS M173=PASS M174=PASS (evidence/m172_m174.log).

- **M172 — FUN_004dc100 is a save-section writer, and M171's "source byte arrives from a caller" is RETRACTED.** Its 2
  call sites (0x51500f in FUN_00512b40, 0x517eb6 in FUN_00516b80) are argument-free dispatch legs (`mov ecx,esi` /
  `lea ecx,[esi-0x23d94]`, zero pushes before the call). The byte is the SHARED scratch global **ds:0x99aa38** (74 refs,
  33 stores; 19 stores in the 0x41a9xx UI-build block FUN_0041a8f0). The function runs BOTH directions: the PACK leg
  (0x4dc1a4-0x4dc279) loads `eax,ds:0x99aa38`, rewrites 22 `or/and al,ah` bits from the struct + `[esi+0x94d430]` flags
  + `[esi+0x94f4b0]` bit 0x20, stores it back and calls the tagged record writer 0x6267a5; the DECODE leg (0x4dc29c on,
  gated on the write's `jl` exit) reloads the SAME global and re-materialises the 4 boolean dwords + tristate + band
  bits. The context opener 0x4d9fb0 is called by EXACTLY 4 writers (0x4dc100, 0x4dc390, 0x4e0260, 0x5a2930); 0x6267a5
  has 18 sites, 12 inside the 0x4d9xxx-0x4e1xxx save band.
- **M173 — the count/sum pair has 3 + 1 consumers.** 0x9204ac: 6 refs = 2 stores (zero 0x532084, RMW 0x53214a) + 1 loop
  load + 3 consumer sites: 0x53346c INSIDE FUN_00531df0 (`count < 2`, then `table[ebx] >= 3*(sum + table[ecx])`, then
  `rank < 6`), 0x53a9cc in FUN_0053a9c0 (`count + ds:0x920720` -> local total), 0x54d30d in FUN_00546800 (`count != 0`).
  0x9204c4: 4 refs, its only consumer is 0x533478 in the same gate.
- **M174 — the tristate header is a SIGNED MODIFIER.** 7 test sites in 4 functions: 2 `cmp vs 0` (0x4a642f/0x4a6450,
  FUN_004a5eb0), 4 `cmp vs 1` (0x55ee48 FUN_0055ec10; 0x576891/0x576bd8/0x576e45 FUN_00574370), 1 `cmp [eax+0x94d80c],ecx`
  (0x5520cd FUN_00551e50) — plus 7 ARITHMETIC reads: `sub reg,[hdr]` x6 (FUN_0053cb20 x2, FUN_00546800 x2, FUN_005551e0,
  FUN_0055f650) + `add ebx,[hdr]` (FUN_005551e0); the aggregator reads it as |value| (0x53206f + neg/jge into [ebp-0x20]).
