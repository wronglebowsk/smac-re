# M53o — the rebuilt production vector (parent-pinned facts)

Scope: `FUN_004e78e0` = per-base per-visit REBUILD of `base+0xbc/0xc0/0xc4/0xc8`.
Sub-results: `evidence/m53o_recon_findings.md` (numeric reconstruction, child A),
`evidence/m53o_chain_findings.txt` (4eb6b0 chain / income-extra anomaly, child B).
Raw asm: `evidence/m53o_fn4e78e0_asm.txt` (1602 lines, VA 4e78e0..4e8d5f — cites below are LINE numbers in it).
Pseudocode: `evidence/m53o_fn{4e75f0,4e6960,4e6d40,4e7070,507410,507440,5a6cd0,4e3c80}.txt`.
Live dumps: `evidence/m53o_bases.txt` (76 rows), `evidence/m53o_seedtable.txt` (8 facs x 24 dwords).

## VERIFIED this session (machine + live)

- **ebx = owner faction** (not item/facility index): prologue `xor ebx; mov bl,[eax+4]` (asm:14-16,
  eax = DAT_008f0d60 cur-base ptr asm:12). Faction saved to `[ebp-0x40]` (asm:19); ebx REUSED as loop
  counter from 4e7bd9 (asm:226).
- **Item budget `DAT_008f0c68` = pop+1** — `movsx ecx,[eax+6]; inc ecx; mov ds:0x8f0c68,ecx` (asm:13-15).
  Dec sites: 0x4e7c36 (asm:244) and 0x4e85d8 (asm:1004). Outer cap 21 groups (`cmp eax,0x15` asm:251).
- **Seed identity resolved**: seed loop (asm:40-117) computes
  `eax = local([ebp-4]) + 2095*fac` via `mov edx,ebx; shl edx,6; add edx,ebx; lea eax,[ebx+edx*2]; shl eax,4; sub eax,ebx`
  (asm:48-54) => store `[0x94dc34 + 4*field + 0x20bc*fac]` into base+0xbc..0xc8 (store 0x4e79a5 asm:59).
  **2095*4 = 0x20bc = faction-record stride — ebx IS the faction.** local = field index 0..3 (asm:34,110-114).
  **LIVE: all seed dwords (local 0..3, all 8 factions) == 0** (seedtable) => seed contributes 0 now; the
  table is a per-faction per-field bonus slot (writer unknown, OPEN).
- Seed post-processing per field: halve `v=(v+1)>>1` iff facility **bit 29** clear (507410(0x1d) = bit-split:
  byte 3 mask 0x20 of base+0x8c bitmap; asm:65-90) AND NOT (special base DAT_00985ba8 owner == fac);
  then clamp `v = min(v, pop)` (asm:100-107).
- **Skip flag `[ebp-0x30]` = 1 iff out-of-mask faction OR (base+0x38 bit6 set AND bit31 clear)**
  (asm:16-33). Mask 0x985b10 low byte live = 0x08 => ONLY fac 3 in-mask => ALL AI bases take flag==1 path.
- **`FUN_004e75f0(field, fac, base_idx, x, y)` = per-field dispatcher** (fn4e75f0.txt): case0 ->
  `FUN_004e6960`, case1 -> `FUN_004e6d40`, case2 -> `FUN_004e7070` (each +trailing 0 arg); case 3 ->
  clears `DAT_008f0cc8`, returns 0 => **+0xc8 gets NO tile contribution** (only seed/clamp).
- **Tile scan loop** (asm:171-260): scan index s 0..20 (`cmp eax,0x15` cap asm:251); tile =
  (base.x + XOFF[s], base.y + YOFF[s]) with **XOFF dwords @0x67850c, YOFF @0x678990 = spiral offset kernel**
  (0,0 1,-1 2,0 1,1 0,2 -1,1 -2,0 ... 42 pairs read live). Wrap flag 0x92a394 = 0 (no wrap live).
  OOB x<0|>=80|y<0|>=80 (0x92a378/0x92a37c = 80) consumes budget, no add (js/jumps asm:215-226).
  Terrain gate: t = y*40 + x>>1 (0x692184=40); **terrain record = *(0x92ae14) + t*0x2c, *(0x92ae14) = 0x40a6ba8
  (POINTER, deref required)** (asm:211-222: `mov ecx,ds:0x92ae14; mov al,[ecx+edx*4]` edx=11t*4=44t);
  rec[0]&0xe0 < 0x60 => base+0x30 |= 0x8000 (both branches add). Per scan: 4 calls 4e75f0 (ebx=0..3) add
  into base[0xbc..0xc8] + running total [ebp-0x48] (asm:230-249, stores 0x4e7c15/0x4e7c19).
- **Scan-skip state `base+0x78`** (bit s set => scan s skipped, no budget cost, asm:171-178):
  entry clear `& (~pop|1)` (asm:42-45); rewritten at **4e8b19** (asm:1411) at function end; scan gate
  `pop+1 < popcount(0x78)` skips ENTIRE scan (507440 = popcount, asm:159-168).
- **AI-only nibble blocks** (flag==1): pre-scan (asm:118-158, gated DAT_0091c628==0 live AND base+0x7c>0;
  ends `base+0x7c -= base+0x80` asm:155-157) and post-scan (asm:267-330) walk **16-nibble array @base+0x84**
  (nibble i = (dword[i>>3] >> ((i&7)*4)) & 0xf, asm:281-289); index >= 16 uses `4e3c80()+1` chooser
  (asm:126-131, 283-287). Nibble value*8 feeds contribution (asm:290+).
- **Middle pass** (both flags, asm:368-1010): scan-0 special case if processed-mask bit0 clear (asm:368);
  loop 4e7ed2..4e85f1 with DIRECT yield calls 4e6960@asm:582, 4e6d40@asm:594, 4e7070@asm:605 and
  **idiv formulas `(a*b*64)/clamp(base+0xc4,1,99)`** (divisor read asm:756 4e828c; formula asm:582-620 region
  incl. `imul; imul; shl 6; idiv` pairs asm:625-635) => **+0xc4 feeds back as a divisor of later adds**;
  second add loop asm:989 (4e75f0 pattern); continue iff budget > base+0x7c+base+0x80 (asm:1004-1013)
  AND `base+0xbc > 2*(pop+1)` (DAT_0092a27c=2, asm:1013-1019); exact-equality shortcut to 4e8a47 (asm:245-250).
- **Tail faction-effect region** (asm:1348+): list @**0x926cb4** (28-byte entries, walk to 0x926d78, count
  dword @-0xc = -1 live = "scan all"), filter `5a6cd0(id, owner)` (tech table 0x92fdd4 stride 0xb +
  availability bitmap 0x985c1c[fac]; -1 => true), `4e3c80` = max-entry chooser (`val*3 + (pop>=5 ? +neighbors)`,
  DAT_0092a2a4=5). 4e75f0 add calls at asm:1099/1177/1264/1334; four 507410 facility-bit tests asm:1470-1560.
- Helper semantics: 507410(x) = (x/8, 1<<(x%8)); 507440 = popcount; live globals 0x91c628=0, 0x92a27c=2,
  0x92a2a4=5, 0x92a394=0, 0x985ba8/bac/bb0=-1.
- **c8/case3 marker `DAT_008f0cc8`**: cleared by 4e75f0 case 3 every scan; consumer OPEN.

## Live reconciliation inputs
6 candidates with expected rebuild values + 0x74..0x94 raw rows: in `evidence/m53o_bases.txt` +
delegation spec (base0 fac2, base3 fac4, base4 fac5, base6 fac7, base10 fac6, base70 fac3-ours;
base70 observed bc 12 = rebuild 11 + crawler c6c from last visit, c0 7 c4 4 c8 0).

## INFERRED / OPEN
- Field identities: bc/c0/c4 = the three yield-function sums (minerals/energy/?) — names pending child A
  terrain-column mapping; c8 = seed-only + case3 marker.
- Seed-table writer; base+0x7c/0x80 producers; 0x84 nibble-array semantics (facility counts?);
  what eax is at asm:1411 (0x78 writeback value); DAT_008f0cc8 consumer.
- 13x 4eb6b0 chain + M53l income-extra anomaly: child B (evidence/m53o_chain_findings.txt).
