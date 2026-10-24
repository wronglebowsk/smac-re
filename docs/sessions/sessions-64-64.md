# Session notes archive — sessions 64-64

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 64 (2026-10-23) — M53l: **+0xc0 HAS EXACTLY 3 WRITERS, ALL INSIDE `FUN_004e93f0` (doubling gate + `+= DAT_008f0c70` + ×(2+bonus)/2 scale); +0xcc IS WRITTEN ONLY AT 0x4e937b IN `FUN_004e92c0` AS `cc = bc − (pop×0x92a27c + 0x8f0c34)`; THE GLOBE-FEEDER IS `FUN_004e8d60` (per-base unit/tile sweep recomputing c6c/c70/c34/c38/c4c); bc/c0/cc ARE PERSISTENT (per-turn recompute is idempotent, 75/75 stable live); MASK = player-byte + alien-byte faction set (4 writers pinned); ERA TABLE 0x68cbb8 = DIRECT dwords {13,12,11,10,8,7}** — write-up `evidence/m53l_findings.md`
- **cc writer (VERIFIED machine+live):** 0x4e937b in FUN_004e92c0 (eax = ds:0x8f0d60 raw byte offsets):
  bc += DAT_008f0c6c (0x4e9344); ec = pop(base+6) × DAT_0092a27c(=2, rules-loader store 0x5784f2) +
  DAT_008f0c34 (0x4e9362); cc = bc − ec. Side fx: 0x8f0c48 := faction+0x2880, +2 if HQ bit (0x4e92f5-
  4e932a); progress clamp cc<0∧prog==0 → −1 (fn4e92c0.txt:22-27); faction total `&DAT_0094dc2c[f·0x20bc]`
  += max(cc,0) cap 99 iff DAT_008f0d64==1. 12 callers = per-base pipeline (4ef6d0 ×2, 4ee410 ×2, 4f5a70
  ×3, 4f41f0 ×2, 4f34b0, 4f2ea0-adjacent). Live: Colony 28 − 22 = 6 ✓ (22 = pop 11 × 2).
- **c0 writer (VERIFIED machine):** only 0x4e943f (×2, gated DAT_00985ba8≥0 ∧ same-faction ∧ head ∈
  [−37,−34]), 0x4e9459 (+= DAT_008f0c70), 0x4e9525 (×(esi+2)>>1; esi = count of 421fe0(19/20/21/22,
  cur_idx,0) true + DAT_00985bac/bb0 same-faction flags → mult 1.0-3.5). Live ba8/bac/bb0 = −1 → no
  bonuses. d0 = c0 − (c38+c4c) − e0 stands (M53k).
- **Feeder (VERIFIED pseudocode):** FUN_004e8d60 zeroes c2c/34/38/4c/6c/70/74/78/d38 block, builds
  local_34[9] from pop, loops units (< DAT_00985af0 = 339): type record 0x98ad88+type·0x34, tile =
  (x×40+y)>>1 → terrain 0x92ae14+tile·0x2c; accumulates c6c[·] += yield, c4c += 1 unit upkeep, faction
  counters 0x94dc24/0094d684. = worker-yield + unit-upkeep sweep; exact per-type yield constants OPEN.
- **+0x48:** += |ebx|>>1 per facility-bitmap hit in FUN_004e78e0 21-iter loop 0x4e8b6f-0x4e8d48 (popcount
  0x507440, mult 0x692184, gates 0x92a378/37c=80); normalized in 4e93f0 to (x+50)/100 display
  (m53k_fn4e93f0.txt:52-134). Walked table identity OPEN.
- **Mask 0x985b10 (VERIFIED writers):** two bytes (b10 = facs 0-7, b11 = 8-15). 5a0fa0 0x5a1091 b11 :=
  0xff (global reset); 597ee0 0x59814f/15c presence loop; 59ec90 0x5a07a4/7d3; 4df630 0x4df82e/9a3 b10
  := 1<<player or 0 (gated 6266e6), alt b11&0xfe; 4e0720 0x4e08ca/8d0 elimination clears bit from both
  then walks bases. Semantics INFERRED: standard-rules set = player + aliens; AIs OUT → era prices,
  clamp B + race-scan protection apply to in-mask only. 4e40a0 tests LOW BYTE ONLY (0x4e40b5 and 0xff).
- **Era table (VERIFIED live):** 0x68cbb8 = direct dwords {13,12,11,10,8,7} (eras 0-5, ASCII follows —
  NOT pointers); sole ref 0x4e40fe. 4e40a0 out-mask: price = table[era] − (531090(0x985b30,0) != 0) −
  ebx(!solo ∧ bit(0x985b30) in b10); neg/sbb/neg = nonzero-boolean idiom. Live era 0x985aec = 2 → 11;
  difficulty 0x92a290/94 = 10/10 (×1), 0x92ada8 = 2. DAT_00985aec has ZERO direct stores whole-.text →
  writer pointer-based/data-init OPEN. M53k "UN price 0" re-flagged: consistent with race-scan unpaid
  path rather than literal 0.
- **LIVE delta (turn 2375→2376, m53l_pre/post.tsv + m53l_delta.txt):** bc/c0/cc stable 75/75 (idempotent
  when c70 = c6c = 0); 24 bases changed: 21 min delta == d0 exactly, 2 (UN DR, Hawk) == POST-recompute
  d0 (income reads d0 after 4e93f0 same pass; their f0 −1 via sweep upkeep, d0 +1, f94 mirror ✓); 3 bases
  +1..+3 extra unexplained; Sparta −25 queue pay; prog += cc 9/9 ✓ (0x4ee8c7). era/mask unchanged.
- **Owner (VERIFIED):** byte@4 = faction (4e92c0/4e93f0 machine + idx 70 ours=3, idx 8 UN=7); census
  {1:6,2:44,3:1,4:7,5:3,6:5,7:9}; byte@5 usually == byte@5 (idx 0 differs 2/6, OPEN). "Colony fac 3"
  SUPERSEDED: idx 23 byte@4 = 2 (names not unique). NAMED.md 4f5a70 row already lists this exact
  per-base pipeline — this milestone pinned the semantics of 4 of its stages.
- Safety: read-only preads + one driven turn (`smac_play.py --turns 1`, 2375→2376, cur 3→7); no pokes,
  no gdb, no signals. Pitfall: my first snap unpack skipped gaps 0xc4/0xc8 — unpack CONTIGUOUS ranges
  and label from the true offsets, never from a field-name wish list.
- **Next:** `NEXT_PROMPT.md` rewritten for session 65; **THE PICK = M53m** (what makes c6c/c70 nonzero —
  the 4e8d60 unit filter (mining orders? tile yield table?); DAT_00985aec era writer; +0xc4/+0xc8 field
  meanings; the 3-base extra-income anomaly; who first sets c0 at founding via 4e47d0→4e93f0).
