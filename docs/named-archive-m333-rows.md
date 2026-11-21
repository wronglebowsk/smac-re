# named-archive-m333-rows.md — `NAMED.md` rows rotated out for headroom, VERBATIM.
`NAMED.md` keeps one line per claim with the same gates and cites; this file is the
full text. The registry (NAMED) governs; this is the detail.


§rotation-1 (M259-M261, s313-chain1 headroom rotation)

## M259-M261 (s204, PASS 14/14) — the per-faction mask band, the static map views, the 0x679f98 class

`scripts/m259_m261_census.py` + `evidence/m259_m261_census.txt` (14/14 gates, 3.3 s, one invocation, static).

**M259 the band** — terrain record bytes +16..+43 (dwords 4..10) are `[terrain_base + 0xc + (row*0xb +
fac)*4]` = dword 3+fac for **FACTIONS 1..7**: per-faction copies of the record's `+8` master mask. Faction 0
uses `+8` itself — both whole-array refreshes guard `test ebx,ebx / je` before the store. WRITERS, closed at
10 indexed stores + 1 walk store (G5): `0x4f0def` (FUN_004ef6d0, the turn/production pass) and `0x5a86aa`
(FUN_005a7970, the faction-event pass) are `for rec in 0..ds:0x92a38c: rec[4*fac+0xc] = rec[8]; add eax,0x2c`
(G1) with the index folded to the 0x20bc per-faction stride 2095*4 = 8380 (G2); `0x5a7afd` and
`0x53a8d9`/`0x53a90c` (FUN_0053a820) are slot→slot merges through the mask — read slot A, AND `[rec+8]`, OR
into slot B, both directions in FUN_0053a820 (G4); `0x582fec` is a tile accessor in the FUN_00582fxx family;
`0x583e1d` copies slot ecx from the parallel 0x2c-stride array at 0x926780 into the terrain record;
`0x5a3b95`/`0x5a3d3f` (FUN_005a3470); `0x4e153b` (FUN_004e14d0) takes its slot index from `[view+0x23bd4]` —
inside the field block the view ctor FUN_00518820 initialises (0x23bcc..0x23bec), so the VIEWED faction
selects which slot is refreshed (G6); FUN_0051c750 (kelp/forest/mindworm growth) walks record+0x10 by 4
beside the faction-block cursor [0x94f4ec,0x95da10) = 7×0x20bc and stores `slot & ~0x20 | mask` (`0x51ca52`,
G3). Readers: 44 indexed sites in 25 functions, incl. FUN_004e15c0 (NATPLACE, 3) and FUN_00519b00 (display,
7) (G7). RETRACTS M240's "a record is two 22-byte map columns" for bytes 16..43; the `.MP` "7 equal dwords
== +8" (planetx 8192/8192) is this band.

**M260 the views** — the live 0x224b8 spacing is NOT an allocation: the token occurs 0 times in the
3,067,904-B image, as an immediate and as a 4-byte LE constant (G8). View 0 is a **static .bss object at
0x8f79e0**: the startup init FUN_00580260 (1 caller FUN_00522850) — **CORRECTED by M262: the esi
0x7cded0..0x7cdeec loop does NOT zero entries 1..7, it ALLOCATES them** (0x22480 B each via FUN_0064bc20,
stored by the pointer-arithmetic `mov [esi],eax` at 0x5803bb) — stores the immediate 0x8f79e0 into DAT_007cdecc at 0x5803e1, then calls the ctor
FUN_00518820 once on it (its only call site 0x580406) (G9). The ctor's own stores reach `this+0x23bec` =
146,412 B > 140,472 = the live stride, so the stride is not an object size (G10); no store in the image
names 0x7cdec8..0x7cdee8 except 0x5803e1. The save codec walks the 8 entries as POINTERS to per-view state
rows and clears `*(p+0x1dd74)` for entries 1..7 (never 0) when DAT_0091c18c/0091c188 changes
(shard_015.c:10822, :10842-10845) (G11). ANSWERED by M262: entries 1..7 are allocated at startup, 0x22480 B
each, through the cursor store — "the ~140 KB views are not allocated" is RETRACTED (0x224b8 = 0x22480 +
0x38, a 56-B heap header, INFERRED).

**M261 the class** — vtable 0x679f98: 88 slots, 2 installs, 15 slots differ from ALL of
0x6717cc/0x671d94/0x67164c (G12): +0x0 FUN_0062ecc0 (46-B dtor, calls FUN_0062d764), +0x8 FUN_004060f0
(52 B), +0x30 FUN_0062d8a8 (5143 B, 1139 insns, 27 callees, 0 direct callers — dispatch only), +0x40
FUN_005fa7f5 (752 B, dispatches slot +0x4c), +0x44/+0x48/+0x4c/+0x50/+0x54 (97/383/682/369/35 B, all
`ret 0x8`), +0x60/+0x64/+0x68 three 15-B zero-callee stubs, +0xa8 FUN_00402120 (21 B), +0xc4 FUN_005fac87
(27 B), +0x15c FUN_0062d78d (283-B installer) (G13). Constructors: FUN_0062d630 ← FUN_0045a8b0(1)/
FUN_005b3000(2)/FUN_00641f3c(3); FUN_0062d764 ← FUN_00636b1e(15)/FUN_0063a770(3)/FUN_00456670(2)/
FUN_00493a10(2)/FUN_0045a840(1)/FUN_0062ecc0(1); FUN_00636b1e = "Start a new session or..." the
session-chooser dialog, FUN_00493a10 = "Gamma Correction" the graphics-options screen (G14).

(§rotation-1 ends; anything below belongs to a later rotation.)
