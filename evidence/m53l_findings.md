# M53l findings — production inputs (session 64)

## 1. +0xcc (rate) writer — FUN_004e92c0 (VERIFIED machine + live)
- Writer 0x4e937b `mov [eax+0xcc],ecx`, eax = ds:0x8f0d60 = current base pointer; offsets are RAW BYTES
  (machine disasm == pseudocode here; evidence/m53l_fn4e92c0.txt:19-31, disasm window in session log).
- Formula: `cc = bc − ec`; `bc += DAT_008f0c6c` (0x4e933c-44); `ec = pop(base+6 signed) × DAT_0092a27c +
  DAT_008f0c34` (0x4e9355-62). DAT_0092a27c = 2 live; its only .text store 0x5784f2 (rules-loader area,
  evidence/m53l_upkeep_globals.txt:9).
- Side effects (same fn): DAT_008f0c48 := faction-record+0x2880 (`&DAT_0094d694[f·0x20bc]`), +2 if base
  facility-bitmap bit 2 (HQ) set (0x4e92f5-0x4e932a via 0x507410(2)); progress clamp: cc<0 ∧ +0x3c==0 →
  +0x3c := −1, cc≥0 ∧ +0x3c<0 → +0x3c := 0 (fn4e92c0.txt:22-27); if DAT_008f0d64==1 accumulate
  max(cc,0), cap 99/turn, into `&DAT_0094dc2c[f·0x20bc]` faction production total (fn4e92c0.txt:28-35).
- Callers = exactly 12, all per-base economy passes: 4ef6d0 ×2 (0x4efeba, 0x4f2211), 4ee410 ×2 (0x4ee6d9,
  0x4ee893), 4f5a70 ×3 (0x4f5acd/4f5b41/0x4f5c5a), 4f41f0 ×2 (0x4f44b7/0x4f456d), 4f34b0 (0x4f3f8f) + 3
  more (call grep). Sibling of 4e93f0's caller set (M53k).
- LIVE (pid 2124624, year 2375): Colony bc 28, ec 22, cc 6 → 28−22=6 ✓; 22 = pop 11 × 2 + c34(0) ✓.

## 2. +0xc0 (gross) writer — FUN_004e93f0 (VERIFIED machine)
Exactly 3 stores to base+0xc0 whole-.text (evidence/m53l_stores_disp.txt), all inside 4e93f0:
- 0x4e9437-3f `c0 <<= 1`, gated (0x4e9405-4e9435): DAT_00985ba8 ≥ 0 ∧ base[ba8] owner == my faction ∧
  head ∈ [−37,−34].
- 0x4e944b-59 `c0 += DAT_008f0c70`.
- 0x4e950f-25 `c0 := c0 × (esi+2) >> 1` — esi = bonus count: +1 per true of FUN_00421fe0(mode,
  cur_base_idx, 0) for modes 21 (0x4e946a), 19 (0x4e94ad), 22 (0x4e94c2), 20 (0x4e94da); +1 if
  DAT_00985bac ≥ 0 ∧ base[bac] same faction (0x4e9476-9d); +1 if DAT_00985bb0 ≥ 0 ∧ base[bb0] same
  faction (0x4e94e9-50c). Multiplier ∈ {1.0,1.5,2.0,2.5,3.0,3.5}. Modes 19-22 = INFERRED facility/
  terrain predicates (same helper 5a6e70 used, M53i).
- Live: 0x985ba8/bac/bb0 all −1 → zero bonuses now (evidence/m53l_globals.txt).
- d0 = c0 − (DAT_008f0c38+DAT_008f0c4c) − e0 stands from M53k (stores 0x4e9557/0x4e957f).

## 3. Feeder of the globals: FUN_004e8d60 (VERIFIED pseudocode; per-base sweep)
Zeroes DAT_008f0c2c/34/38/3c/40/4c/6c/70/74/78/b0/d38 (fn4e8d60.txt:26-39), builds local_34[9] from pop
(`(char)DAT_008f0d60[3]` — short* halving: = byte +0x6), then loops while local_10 < DAT_00985af0
(live 339; fn4e8d60.txt:211) over unit records (stride 0x34=52): type record `&DAT_0098ad88 + type*0x34`
(class/domain bytes +0x25/+0x2a), tile = (x × DAT_00692184 + y) >> 1 (0x692184 = 40), terrain record
`DAT_0092ae14 + tile*0x2c`. Accumulates `(&DAT_008f0c6c)[*pbVar9] += …` (fn4e8d60.txt:94, :206), c4c
unit-upkeep += 1 (:147), faction counters `&DAT_0094dc24/0094d684[f·0x20bc]` (:103-107, :139-146).
= worker/crawler yield + unit upkeep sweep (yields' exact per-type constants: OPEN).
Other block writers: 4f2ea0 c4c ×3 (0x4f3110/316d/31a2); 4e8d60 c34/c38/c4c (0x4e8d80/8d8b/8dbc/90e0).

## 4. +0x48 (raw accumulator → display)
- Feed: FUN_004e78e0 loop 0x4e8b6f-0x4e8d48, 21 iters (`cmp edi,0x15`): base offsets
  DAT_0067850c[edi]/DAT_00678990[edi] + walked-table words [edx],[edx+2],[edx+0x78]; wrap gates vs
  DAT_0092a378/0x92a37c (80 live); mult DAT_00692184 (0x4e8bc1); popcount via FUN_00507440 (0x4e8bf4);
  double if walked-record+0x78 bit set (0x4e8c02); facility-bitmap gate (0x4e8d05-17);
  `base+0x48 += |ebx|>>1` (0x4e8d2d-32). Walked table identity: OPEN.
- Normalize (4e93f0, pseudocode evidence/m53k_fn4e93f0.txt:52-134): `48>>=3; −=iVar3; +=(c0−iVar3−iVar5)
  /local_8; += (DAT_0094d608[f]×5)/local_8; clamp≥0; cond ×2 ×2; /6; := (48+50)/100` → ends as rounded
  display value (INFERRED; divisor meanings OPEN). Colony +0x48 = 0 live.

## 5. Mask 0x985b10 (VERIFIED machine; semantics INFERRED)
- TWO BYTES: 0x985b10 = factions 0-7, 0x985b11 = factions 8-15 (byte stores/tests; 4e40a0 tests
  low byte only `and eax,0xff` 0x4e40b5).
- Writers (evidence/m53l_mask_refs.txt + b11 grep): 5a0fa0 0x5a1091 `b11 := 0xff` inside global reset
  (zeros 0x985ae8..0x985afc, 0x5a1061-10a4); 597ee0 0x59814f/59815c loop edi 0..7 clear-or-set bit edi
  of b11; 59ec90 0x5a07a4/0x5a07d3 b11 writes; 4df630 0x4df82e/4df9a3 `b10 := 1<<f` or `:= 0` gated on
  FUN_006266e6 (fn4df630.txt:68-80), alt `b10 := b11 & 0xfe` (:135); 4e0720 0x4e08ca/0x4e08d0
  elimination: `b10 &= ~(1<<f); b11 &= ~(1<<f)` then walks bases nb−1..0 (fn4e0720.txt:56-58).
- Semantics (INFERRED, machine-consistent): mask = "standard-rules factions" = player (b10 := 1<<player)
  + alien factions 8-15 (init 0xff, scenario presence loop); the 7 AI human factions sit OUT. Gates:
  4e40a0 price 10 in-mask vs era-table out; clamp B 4f0cc3; race scan only for out-mask current 4f0ac6.
- Live 0xff08: b10 = 0x08 (bit 3 = ours), b11 = 0xff (aliens all "in", none on map).

## 6. Era price table (VERIFIED live + machine)
- 0x68cbb8 = dword array {13,12,11,10,8,7} = per-era base price multiplier (eras 0-5); followed by
  ASCII junk ("Base in...") — NOT pointers (deref probe, evidence/m53l_globals.txt). Sole .text ref
  0x4e40fe `mov esi,[ecx*4+0x68cbb8]`, ecx = DAT_00985aec.
- 4e40a0 out-mask path (0x4e40c7-4e410b): price = table[era] − (531090(DAT_00985b30,0) != 0) − ebx;
  ebx = 1 iff !solo ∧ bit(DAT_00985b30) in b10. neg/sbb/neg idiom == nonzero boolean (not magnitude).
  Then difficulty DAT_0092a290/0x92a294 (both 10 live → ×1), 0x92ada8==1 → ×9/10 (live 2 → no).
- Live era DAT_00985aec = 2, 0x985b30 = 2 → out-mask multiplier = 11 − nz(adj) − 0.
- DAT_00985aec: ZERO direct stores whole-.text (only loads/cmps; store-shape grep) — writer
  pointer-based or data-init: OPEN.
- Tension (flag, do not re-derive): M53k UN "price 0" case vs era 2 → 11; consistent with race-scan
  unpaid return (pay entry sole `test [ebp-0x30]; jg 0x4f0ca1`) rather than literal price 0.

## 7. LIVE per-turn delta (turn 2375→2376, `evidence/m53l_{pre,post}.tsv`, diff `m53l_delta.txt`)
- **bc 75/75, c0 75/75, cc 75/75 STABLE.** The per-turn 4e93f0 pass is IDEMPOTENT when c70 = 0 and no
  bonuses: `c0 := (c0+0)×2>>1 = c0`. bc/c0 are therefore PERSISTENT values, updated only when an event
  pass runs 4e8d60 (fills c6c/c70 for the current base) — trigger = OPEN (M53m).
- 24/75 bases changed: 21 have min delta == pre d0 exactly; **UN DR min +8 and Hawk of Chiron min +6
  equal the POST-recompute d0 (7→8, 5→6)** — income add reads d0 after 4e93f0 in the same base pass ✓.
  Their f0 dropped −1 (c4c recomputed by 4e8d60 mid-pass) → d0 +1, f94 mirror +1 ✓ formula live again.
- 3 bases got +1..+3 extra minerals beyond d0 (U.N. HQ +3, U.N. Education +2, Morgan Metallurgy +1) —
  unexplained, flag (M53m). Sparta Command min −25 = queue pay event.
- prog += cc in 9/9 changed bases (UN HQ prog +7 = cc 7) ✓ M53k 0x4ee8c7 re-confirmed live.
- c4 changed in 2 bases (−1/−2) — c4 is semi-active (per-base values 5..11), meaning OPEN.
- era/mask unchanged across the turn (era 2, mask 0xff08); cur 3→7 (faction 7 processed after ours).

## 8. Owner field (VERIFIED)
byte@4 = faction: machine (4e92c0 `*(byte*)(base+4)*0x20bc`; 4e93f0 `mov al,[ecx+4]`) + ground truth
(idx 70 'Climactic Research' = 3 = ours; idx 8 U.N. Disaster Relief = 7 out-mask ✓). Census byte@4:
{1:6, 2:44, 3:1, 4:7, 5:3, 6:5, 7:9} = 75. byte@5 differs on some bases (idx 0: 2 vs 6) — meaning OPEN
(founder?). NEXT_PROMPT's "Colony fac 3" superseded: idx 23 byte@4 = 2 (names not unique across
factions; array slides). Colony dump: bc 28 c0 13 c4 11 c8 0 cc 6 d0 13 e0 0 ec 22 f0 0
(evidence/m53l_colony_dump.txt).
