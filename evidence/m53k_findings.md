# M53k findings — accumulation side: base+0xd0 / +0x40 writers + the arm rule

## A. base+0xd0 (net income) — writer = FUN_004e93f0, VERIFIED (machine + live)
- Machine stores (whole-.text census: the ONLY stores to [reg+0xd0]): 0x4e9557
  `mov [eax+0xd0],edx` where 0x4e9544-0x4e9555 `eax=ds:0x8f0d60; edx=[eax+0xc0];
  ecx=[eax+0xf0]; sub edx,ecx` => **d0 = c0 - f0**; then 0x4e9562 `[eax+0xe0]=0`,
  0x4e9577-0x4e957f `ebx=[eax+0xd0]-ecx; [eax+0xd0]=ebx` => d0 -= e0 (e0 zeroed
  first, so no-op per turn). Pseudocode evidence/m53k_fn4e93f0.txt:47-51:
  f0 = DAT_008f0c38 + DAT_008f0c4c (global upkeep, assembled 0x4e953c); :51 mirror
  +0x94 := d0; :24 c0 += DAT_008f0c70 (global bonus); :52 `+0x48 >>= 3` in place.
  NO pointer-scaling trap here: pseudocode renderings == machine disps (verified vs
  disasm). eax = cur base ptr 0x8f0d60 = byte offsets.
- 4e93f0 called per base INSIDE turn processor FUN_004ef6d0's base loop:
  shard_012.c:20861, 22171 (enclosing header 20585 `==== FUN_004ef6d0 size=12298`);
  also called by FUN_004ee410 (20029/20067), FUN_004f5a70 (24180), founder
  FUN_004e47d0 (14325), FUN_004eb6b0 (18367), FUN_004f4060/4f41f0 (23235/23355/23428).
- +0x48 = raw production accumulator: += at FUN_004e78e0+0x1455 (0x4e8d35), normalized
  `>>3` by 4e93f0 (eips 0x4e95a4/0x4e95db/0x4e9736/0x4e9772). LIVE: 58 stores to
  Colony+0x48 in 1 turn (evidence/m53k_watch.log, m53k_watch2.log).
- Live formula checks (pread): Colony idx 23 @ 0x95f560: d0 13 = c0 13 - f0 0 - e0 0;
  U.N. Disaster Relief idx 8 fac 7: d0 9 = 12 - 3 - 0. d0 changed 17/75 bases in 1
  turn, 32/75 in 2 (pre/post tsv diffs). Colony D0 watchpoint: 0 hits = value stable,
  NOT a negative (watchpoints fire on VALUE change only).

## B. base+0x40 (minerals) — per-turn writers all inside FUN_004ef6d0, VERIFIED
1. Income add 0x4ef7f6 `mov [eax+0x40],edx` (edx = minerals + [eax+0xd0]); gates
   0x4ef7db-0x4ef7f9: skip if d0 < 0, head == -38, or +0x30 & 2. LIVE:
   m53k_watch2.log WP21 `M40 eip=0x4ef7f9 new=301` Colony 288->301 = +d0 13; post3
   tsv 301. Only +0x40 hit that turn (head 147 unit, pending 0).
2. Unit spend A 0x4efedd + clamp A 0x4eff20 (M48c); unit path gated affordability
   0x4efa5e `cmp [ecx+0x40],edi; jge 0x4efadc` else dtor return 0x4f0bfa.
3. Facility/project spend 0x4f0ca1-0x4f0ca6 `ebx=minerals-edii; [edx+0x40]=ebx` (edi
   = price, section D).
4. Queue drain 0x4f1e3f (= 4ef6d0+0x276f, M48c).
- Clamp B after project spend, 0x4f0cc3-0x4f0ce9: edx = min(10, d0) (10 = DAT_0092a370);
  if post-pay minerals > edx AND faction in mask (`test dl,al; je 0x4f0cf2`, mask byte
  ds:0x985b10) -> minerals := max(0, min(10, d0)) (0x4f0ce9). Mirror +0x98 := +0x40
  unconditional (0x4f0cf2/0x4f0cf5).
- Event (non-turn) writers (census evidence/m53k_ptr_stores.txt): FUN_004cce50 trio
  (+0x40/+0x44/+0x98), FUN_004e47d0 founder (inits new record incl. +0x40; nb++),
  FUN_00585720 (=0), FUN_0058fa40, FUN_00507ef0, FUN_00504400, FUN_00537f90,
  FUN_004f82b0, FUN_00516590/517250, FUN_00523a60/523c80, FUN_005437d0/5439c0,
  FUN_00556690, FUN_0055f650.

## C. base+0x3c (progress) — writer = FUN_004ee410, VERIFIED live + machine
- 0x4ee8b4-0x4ee8c7: `edi=ds:0x8f0d60; edx=[edi+0xcc]; esi=[edi+0x3c]; add esi,edx;
  mov [edi+0x3c],esi` — progress += rate every turn. LIVE WP22 `C3C eip=0x4ee8ca
  new=56` Colony 50->56 (+cc 6 at store time); post3 f3c = 56.
- 4ee410 calls 4e93f0 (20029/20067); 4ee410 called by FUN_004f5a70 (24186), called
  from shard_013.c:11570 (turn-driver layer). +0xcc (rate) recomputed per turn (it
  changed mid-turn, 6 -> 8 Colony).

## D. The arm rule (facility/project completion), VERIFIED machine
- Price edi = FUN_004e40a0(faction,1,-1) x table[idx].cost_factor (0x4ef8e2-0x4ef8ed;
  0x984d38+idx*48+0xc; idx = -head). NEW: FUN_004e40a0 (m53k_fn4e40a0.txt:14-19) —
  in-mask faction -> base 10; OUT-of-mask -> (era table `&DAT_0068cbb8[DAT_00985aec]`
  - FUN_00531090 adj) - contact adj, CAN BE 0 -> out-of-mask factions complete free.
  Then DAT_0092a290/0092a294 (by param_2) difficulty x/10; DAT_0092ada8==1 -> x9/10.
- Gate 0x4f0a3d `cmp [edx+0x40],edi; jl -> dtor return`: completion needs STOCK
  minerals >= FULL price. No accumulation gate: +0x3c/+0xcc are display only
  (announce 0x4efd49: turns = (price*(pop+1) - [base+0x3c]) / [base+0xcc]; M53i pane).
- Race scan 0x4f0af0-0x4f0b51 runs ONLY if current base's faction NOT in mask
  (gate 0x4f0ac6: `movzx eax,[ebp-0x2c]; and al,ds:0x985b10; jne -> 0x4f0b7b skip`).
  Scan iterates ALL bases (esi=0x95da14, stride 0x130, count nb); keeps owner-in-mask
  (0x4f0b05) AND head == current head (0x4f0b0d; head == -71 special via 0x59a9f0);
  if any kept base has `[base+0xd0]+[base+0x40] >= price` -> 0x4f0c28 dtor return:
  out-of-mask base DEFERS while a funded in-mask rival races the same item.
  In-mask bases skip the scan entirely: gate + claim availability -> pay.
- Reachability (0x4ef88b-0x4ef987): head >= 0 -> unit path; head < 0 -> idx = -head;
  projects 39-71: claim slot must be -1 (`0x4ef925 cmp [eax*4+0x985b3c],-1;
  jne 0x4f07c2` abandon path); facilities idx <= 34: bitmap bit idx clear
  (`0x4ef982 bt; jae 0x4ef905 -> esi=edi; jmp 0x4f0a37`); idx 35..38 direct
  (0x4ef94a); head == -38 skip (0x4ef896). Then pay 0x4f0ca1 + clamp B + mirror +
  claim store 0x4f0d83 + +0x30 bits 23/31 + THE POP (M53j sequence).
- Mask live: 0x985b10 = 0xff08 = bits {3,8..15}: faction 3 (ours) IN; 0,1,2,4,5,6,7
  OUT. Mask semantics open.

## E. Case studies, VERIFIED live
- U.N. Disaster Relief (idx 8, fac 7, OUT-mask): completed Aerospace Complex (head
  -29) during turn 2373->2374: bitmap bit29 flipped (1000000000 -> 1000002000 direct
  read), minerals 16->25 = +income 9 ONLY, zero pay -> price 0 (4e40a0 out-mask
  branch), clamp B skipped (out-mask je 0x4f0cf2), mirror f98 = 25. Resolves M53j's
  "debits full price" tension: in-mask pay full price, out-mask pay era price (0).
- The Colony (idx 23, fac 3, IN-mask): 2374->2375 minerals 288->301 (+d0 only),
  progress 50->56 (+cc), d0 stable 13.
- M48 pinning explained: ours d0 = -1 < 0 -> income add skipped (gate 0x4ef7db) AND
  clamp B would set := max(0,min(10,d0)) = 0 at any completion. Minerals stay 0.

## F. Open
- Writers of +0xc0 (gross production) / +0xcc (rate) inputs; what feeds 4e78e0's +0x48.
- Mask 0x985b10 semantics + writer; era table DAT_0068cbb8 + DAT_00985aec semantics.
- Abandon path 0x4f07c2; Ascent special 0x4f072e; +0x30 bit 1 writer; +0xe0 setter.
- +0xcc rate formula (facility/terrain sum?).
