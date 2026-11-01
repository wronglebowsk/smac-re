# FOOTING — SMAC rebuild model, M48d -> M53s (VERIFIED unless marked)

Moved out of `NEXT_PROMPT.md` in session 75 to keep the always-loaded prompt under its 15,500-byte
budget. This is the footing the next session must NOT re-derive: what is proven about
`FUN_004e78e0`'s production-vector rebuild, the record layouts, and the globals.
Read it once (`~12 KB`), or grep one section: `grep -n '^### \|^- \*\*' FOOTING.md`.
Citations in it resolve against `evidence/*.md`.


### M53s (75): the residual is NOT in the rebuild — `FUN_004eaa10` folds an ALLIANCE ENERGY SHARE into `+0xc4` — `evidence/m53s_findings.md`
- **The leverage (VERIFIED):** `4e78e0`'s exit shifts a history window — asm 0x4e8b39-0x4e8b54
  (`mov eax,0xac / add eax,4 / cmp eax,0xbc / mov edx,[eax+ecx+0xc] / mov [eax+ecx-4],edx / jl`)
  copies `0xac<-0xbc, 0xb0<-0xc0, 0xb4<-0xc4, 0xb8<-0xc8`, so `base+0xac/0xb0/0xb4/0xb8` is the
  vector **at the visit's exit**, immune to later writers. The model equals that snapshot on
  **76/76 rows, all four fields** => the scan/yield/`0x8f0c4c`-divisor theory is CLOSED: the
  rebuild model is complete, it just stops where the game's rebuild stops.
- **Energy-only, post-snapshot (VERIFIED):** `c4_now - c4_prev == -delta` on exactly the 11 rows;
  `+0xbc/+0xc0` change on **0/76** rows visit->visit. No base-record field equals the gain.
- **Writer, caught live (VERIFIED):** hw watchpoints on base46+0xc4 (0x961174) + base3+0xc4
  (0x95de64) over the driven round 2384->2385: base 46's rebuild writes end at **17** (0x4e85c1 =
  model = `base+0xb4`), then **0x4eac68 writes 20 then 22**; base 3 ends at **12**, then
  **0x4eac68 writes 15**. gdb names the instruction after the store, so the site is
  `mov ecx,[eax+0xc4] / add ecx,esi / mov [eax+0xc4],ecx` = **0x4eac57 / 0x4eac5d / 0x4eac62** in
  **FUN_004eaa10** (eax = `DAT_008f0d60`). 4eaa10 runs immediately after 4e78e0 in every pass of
  the per-base turn processor FUN_004f5a70 (0x4f5ac8->0x4f5ad7, 0x4f5b3c->0x4f5b4b,
  0x4f5c55->0x4f5c64). => `stored c4 = snapshot + Sigma(esi)`.
- **Sibling fold is dead weight here (VERIFIED):** `base+0xc4 += DAT_008f0c74` (0x4eaa2e/30) fired
  **211 times over 74 bases with add = 0 on all 211**. `0x8f0c74/78` are written only by
  `4e8d60`'s entry reset (0x4e8d86/0x4e8d92, eax = 0) and accumulate only through the indexed
  sites 0x4e8e82 `inc [eax*4+0x8f0c6c]` / 0x4e8f35 `add [ecx*4+0x8f0c6c],eax`; the bc/c0 consumers
  are 0x4e9336+0x4e9344 and 0x4e944b+0x4e9459 — same slot family, which is why bc/c0 show no
  residual. Whole-.text has **no `add [reg+0xc4]` at all**; only 7 displacement stores to `+0xc4`
  exist (2 in 4eaa10, rest ctor/UI — disproofs in `evidence/m53s_writer_scan.md`), and Ghidra
  renders exactly two record writes: shard_012.c:17952 (`+= DAT_008f0c74`), :18010 (`+= iVar5`).
- **esi = per-allied-faction energy share (INFERRED, cites in findings F6):** loop over OTHER
  factions (bound `cmp esi,0x1c` 0x4eac7e, stride 0x20bc); gates = stance bit 2 either direction
  (`[0x94d448+owner*0x20bc+other*4] & 2` 0x4eab33 / reverse 0x4eab3b), `faction[other]+0xd54 != 0`
  (0x4eab47), `FUN_004ea940(other,k) >= 0` (0x4eab5a — the k-th nearest base of `other` exists;
  4ea940 walks 0x95dac4 with `add esi,0x130`); then zeroed if `[0x94d4f0+owner*0x20bc] != 0`
  (0x4eac33) or `[faction[other]-0x244] != 0` (0x4eac40). Value
  `n = ceil((base_ally[k]+0xb4 + base+0xb4)/8)` (0x4eab79-9c, doubled when
  `DAT_00985bd4 < DAT_00985bd0`), `esi = ((([0x94d734+owner*0x20bc]+1)*n + ((count-1)>>1)) /
  (DAT_0092a274+1))` (0x4eabe0-ef), halved without stance bit 1 (0x4eabf4/fe), `+1` if
  `DAT_00985bc0 == owner` (0x4eac19); also stored to `DAT_008f0d40[other]` (0x4eac27).
- **Dump-visible confirmation of the gate:** factions with any bit-2 ally in the dump are exactly
  **{1,3,4,7}** = exactly the gain-bearing factions (0,2,5,6 have none); base 46 (fac 1, allies
  {4,7}) took **two** increments (+3,+2), base 3 (fac 4, ally {1}) **one** (+3). Gains reproduce
  across a driven round (same 11 bases, +idx 6, idx 51 3->2) => rule, not drift.

### M53r (74): the 11 fac-2 rows were POP-DRIFT BUDGET rows — census 76 sc / 65 exact — `evidence/m53r_findings.md`
- **Scan-order theory dead (VERIFIED):** the middle-pass selection was fully re-read from the asm
  and the model already matched every gate (loop j=1..20; strict `</>` pair dispatch; swap guards
  COMMIT-require best-add idx > 0 ∧ add score > swap score ∧ swap idx > 0; undo gate
  `bc < (pop+1)*K`; facility gate/score; continuation; exit `0x78 = acc` / `0x7c = budget` RAW).
- **Budget/skip-flag facts (VERIFIED):** `DAT_008f0c68` has exactly 4 stores in `.text`, all in
  4e78e0 (Ghidra shard_012.c:16023/16108/16229/16626 = machine 0x4e7904/0x4e7c36/0x4e7ecd/0x4e85d8);
  sole initializer = **pop+1 AT VISIT TIME** (`movsx BYTE[base+6]+1`; Ghidra `(char)DAT_008f0d60[3]`
  = short*-scaled byte@6). Skip flag = `1 iff NOT((1<<fac)&byte0(0x985b10)) ∨ (byte0(base+0x38)&0x40
  ∧ bit31)` (0x4e790a-33; live 0xff08 ⇒ flag 1 for all facs but 3). Scan-0 special runs iff scan
  ended `budget != c80+c7c` (0x4e7c5e `je 0x4e8a47` skips special+MP); its tile scan self-skips
  WITHOUT budget spend when acc bit 0 already set (A:368).
- **The finding:** the 11 non-sc fac-2 rows fired phantom swaps because dump pop byte@6 is
  POST-visit; stored carry == model budget_end **+1** (`evidence/m53r_sig.py`). `pop_visit =
  dump+1` ends the scan at `budget == c80+c7c` → special+MP skipped → reproduces mask AND carry
  AND vector at once on **22 rows (ALL fac 2**: the 11 + carry-only 28,31,47,48,49,56,63,65,67,68,
  71). INFERRED: those bases lost 1 pop after their rebuild visit (cause open; fac-2 idx 0/23 did
  NOT drift). `recover_pop()` probes pop+1, accepts only on mask+carry reproduction.

### M53q (73): the scan pool is RECOMPUTED per base and the entry filter is a NO-OP — `evidence/m53q_findings.md`
- `build_table(idx) -> (table[25], mask21)` transcribes `FUN_004e63b0` (asm 298136-298619): per-step
  reason codes (2 off-map/unseen, 0 scannable, 4 terrain test `tile[8]&1 ∧ 0<=tile[2]&0xf<8`, |=8
  unit order-3/foreign-stack test, |=0x20 foreign territory no-treaty, |=0x10 another base's
  processed step overlapping the spiral), mask = {bit i: table[i]!=0}; the `=1` site 0x4e63e8 is
  dead for 0..20. Computed table matches live `0x8f0ccc` 20/21 slots on cur base 69; the one
  disagreement is **bit 8** (tile (45,9): live 8, computed 0 — pre-move state, INFERRED). Predicate
  details (+50 walk anchor, |=8 gate polarity, `FUN_005ab130` head rules, hex-dist formula) are in
  the findings file + skill reference — do not re-derive. `evidence/m53q_probe.py` dumps reads.
- **THE HEADLINE (VERIFIED 76/76):** `pool(=base+0x78) & fresh_mask == {bit 0}` for every base ⇒
  entry filter `d78 &= (~d30|1)` is a no-op; the game filters with the per-base fresh mask (4e63b0
  at 0x4e78e9 precedes the filter at 0x4e796a); the stale global never filtered anything.

### M53o (67): the rebuilt vector IS the terrain-yield sum — `evidence/m53o_recon_findings.md`
- `base+0xbc` NUTRIENT, `+0xc0` MINERAL, `+0xc4` ENERGY, `+0xc8` PSI (seed-only). `FUN_004e75f0
  (field, fac,bidx,x,y)`: 0->`4e6960`, 1->`4e6d40`, 2->`4e7070`, 3->0 (clears `DAT_008f0cc8`); it
  pushes `0` as the 5th arg to each yield fn (0x4e760b/0x4e7627/0x4e7643) so `extra = 0` on the
  scan path. Per-tile category table = alpha `#RESOURCEINFO` verbatim, live **0x926bd8** (9x4).
  **7 vector add sites** in 4e78e0 (`mov [edi+ecx*1-0x4],edx`): 0x4e7c15 scan, 0x4e7ea3 scan-0,
  0x4e85bd mp-add, 0x4e8739 swap-out, 0x4e883b swap-in, 0x4e8951/0x4e8a32 dead undo pair (asm lines
  249/433/998/1108/1186/1273/1343); the 8th such store, 0x4e8b50, is the history shift. Seed store
  0x4e79a5 from `0x94dc34+(fac*0x82f+field)*4` = live 0 all factions. Downstream: bc +=
  `DAT_008f0c6c` (0x4e9336/0x4e9344), c0 += `DAT_008f0c70` (0x4e944b/59), **c4 += `esi` in
  FUN_004eaa10 (M53s); `+0xc8` still has no downstream writer.**
Scan/budget/middle-pass rules: skill `references/production-rebuild.md`.
### Standing
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, **owner byte@4
  = faction**, byte@5 usually == @4 (idx 0 differs, OPEN), pop byte@6 (POST-dump value — M53r),
  +0x30 flags (bit 0x8000 set by 4e78e0, exit clears **bit 17** via `and ch,0xfe`; bit 2 gates one
  energy test), +0x34 (0x2000/0x4000 tested by 4e7070), +0x38 = 0x00dfbe41, +0x3c progress, +0x40
  minerals, +0x4c pending (cap 9), queue @0x50..0x74 (head clear 0xffffffda), **+0x78 scan/processed
  mask**, **+0x7c budget carry (= budget published at exit — re-measures the game's visit)**, +0x80
  counter (zeroed at 4e78e0 entry), +0x84 16-nibble AI array, +0x8c..0x90 40-bit facility bitmap,
  +0x94 d0 mirror, +0x98 minerals mirror (equal 75/75), **+0xac/0xb0/0xb4/0xb8 = the PREVIOUS
  visit's vector, snapshotted at the rebuild's exit (M53s: the model matches it 76/76)**,
  **+0xbc/0xc0/0xc4/0xc8 the rebuilt vector as amended downstream (c4 only, M53s)**, +0xcc rate,
  +0xd0 net income, +0xe0 (per-turn zeroed), +0xe4/+0xe8 (4eaa10: `e4 = FUN_004e9880(c4 - f4)`),
  +0xec/+0xf0 upkeep, +0xf4 = `DAT_008f0c3c` (written by 4eaa10), +0xfc..0x104 bucket fields
  (4eaa10's walking store 0x4eafa1), +0x48 display acc (zeroed at exit).
- **Unit record (array 0x933278 stride 52, count `0x985af0`):** x u16@0, y u16@2, flags dword@4,
  **type u16@10** (M54f: `shard_012.c:2150` indexes the class table with the SHORT at `+0x0A`;
  the `+4` byte is a flags byte, and the "type byte@4" this line carried was wrong),
  **faction byte@14**, order byte@17, +24/+25 (u16 `w18`, byte `b25`: 0x440 transport-state test +
  the per-faction bit at 0x4e660c — semantics OPEN), +38 sweep slot, +46 u16 base index, **+48 u16
  chain link** (walked by `FUN_005a6330`) and **+50 u16 chain link** (walked by `FUN_005ab130`) —
  both exit only on NEGATIVE, terminators -1, same stack in opposite orders (tile (45,9): +48
  106→147, +50 147→106). Type records 0x98ad88/52 (+41 cost factor, +42 plan, +37 read at 0x5a692a),
  faction records **0x94ae14 + fac*0x20bc** (0x92ae14 is the terrain POINTER, not the record base;
  +0x2880 = `&DAT_0094d694`, +0x2e18 production total, +0x2e20 the 4 seed dwords), terrain array
  base = the DWORD at 0x92ae14 (live 0x40a6ba8), record = base + (40*y + (x>>1))*0x2c, category =
  rec[0]&0xe0 (ocean iff < 0x60), +4 = per-faction seen bits, +7 = **CONSTANT 0xff in every record of
  both maps** (M240 retracts this line's "+7 = owner byte"; the owner is the LOW nibble of +2, live-
  written by `FUN_00582c80`), +8 = mask dword, +16..+43 = 7 copies of that mask dword (M240) (bit
  1 = unit-stack occupancy, bit 0 = the 4e63b0 terrain test, **bit 0x800000 = the unit-presence bit
  4e7070's neighbour loop reads**), +0xc = list head/uc; relation/stance bytes **0x94d448 +
  fac*0x20bc + 4*other** (&3==0 = "no pact/treaty/truce", **bit 2 = alliance — either direction
  counts**, bit 1 halves the 4eaa10 share); tech table 0x92fdd4/0xb + availability bitmap
  0x985c1c[fac]; claims 0x985b3c[33].
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, nunit 0x985af0, mask 0x985b10 (0xff08 —
  its LOW byte drives the 4e78e0 skip flag ⇒ flag 1 for every fac but 3), era 0x985aec (2), era
  table 0x68cbb8, **turn flags 0x985ae8 (0 idle, bit1 = end-turn in flight — 0x10002 = livelock
  signature)**, solo 0x920434 (**live 0**), cap 0x92a370 (10), cur base ptr 0x8f0d60, cur base
  INDEX 0x68cbb0, marker 0x68cbb4, **per-visit block: 0x8f0ccc..0x8f0d1c table + 0x8f0d30 mask
  (rebuilt per base by 4e63b0; 2 stores to 0x8f0d30 in .text) + 0x8f0c4c (score denominators
  0x4e821f-31, live 6, NOT visit-invariant) + 0x8f0c68 (rebuild budget, 4 stores total)**,
  **economy slot family 0x8f0c6c/70/74/78: zeroed by 4e8d60's entry (0x4e8d74-92), accumulated ONLY
  via the indexed `inc [eax*4+0x8f0c6c]` (0x4e8e82) and `add [ecx*4+0x8f0c6c],eax` (0x4e8f35);
  consumers 0x4e9336 (bc), 0x4e944b (c0), 0x4eaa1b (c4); 0x8f0c78 has no reader)**, 0x8f0c34/38/
  3c/40 cleared by the same reset, **0x8f0d40[other] = the per-allied-faction share 4eaa10 stores**,
  cc8 = psi overflow, map width 0x692184 = 40, 0x92a378/37c = 80, 0x92a394 = 0 (x wraps), scenario
  constants 0x985b48 (live -2, only ref `cmp` 0x4e74e9), 0x985bc0 = 2, 0x92a27c = 2 (K), 0x92a2a4
  = 5, 0x92a2cc = 59, **0x91c628 NOT constant (0 → 1 → 0 observed; live 1)**, 0x985afc = 281,
  **4eaa10's share inputs: 0x92a274 (divisor - 1), 0x985bd0/0x985bd4 (whose order doubles `n`),
  faction-record fields 0x94d4f0 (zero-gate), +0xd54 (presence gate), 0x94d734 (share numerator),
  record-0x244 (second zero-gate)**.

## Retired premises (do not resurrect)

- **Retired premises, do not resurrect:** "bc/c0/cc are persistent accumulators written only by
  4e92c0/4e93f0"; "4ef6d0 never runs"/"re-runs the block twice"; "the round walks all bases in index
  order" (grouped by owner, ours LAST); "bc/c0 gain per sweep fire"; "the Colony is fac 3" (owner 2,
  idx 23); "4e40a0 tests the whole mask dword" (LOW byte only); "pseudocode offsets are byte
  offsets" (short* x2, int* x4 — `DAT_008f0d60[3]` = pop byte@6); "claim table 0x985aa0[72]" (33 @
  0x985b3c); "PROPOSAL pane `YEA: 2 NAY: 3` is a key hint"; "4e3470's 19 hits = calls"; "0x4f1e3f
  drains base+0x40"; "base+0x78 entry mask = ~(pop|1)"; "DAT_008f0d30 = 1 is a scenario constant";
  "the freshness marker 0x68cbb4 is -1 while idle"; "the entry filter clears pool bits via the
  stale global d30" (pool∩fresh = {bit 0} on 76/76); "the +50 walk re-anchors to the stack head";
  "the |=8 gate fires when the +25 faction bit is SET"; "FUN_005a5c00 is identity" (only when
  0x920434 != 0); "the middle-pass corrections subtract pop+k2 then halve"; "the model reads live
  memory"; "0x91c628 = 0 is constant"; the session-68 "Class S / Class J" framing; **"the 11 fac-2
  non-sc rows are a scan-ORDER problem"** (M53r: pop-drift budget rows); **"skip flag = tile
  out-of-mask"** (faction-mask test, M53r); **"swap guard: best-add index > 0 exits uncommitted"**
  (it COMMITS only then); **"4e78e0 exit clears bit 8 of +0x30"** (bit 17); **"pop byte@6 is the pop
  the visit used"** (dump value is post-visit — 22 rows drift +1); the session-73 census 65 sc / 54
  exact (session-74 dump: 76 sc / 65 exact); **"the 11 c4-only residuals mean a missing yield
  branch, a drifted 4e7070 input, or `0x8f0c4c` divisors"** (M53s: the model matches the game's own
  visit-time snapshot 76/76 — the delta is downstream of the rebuild); **"0xc4/0xc8 have NO
  downstream writers"** (c4 has two, both in FUN_004eaa10: 0x4eaa30 and 0x4eac62); **"stored
  base+0xc4 == the rebuild's output"** (it is snapshot + alliance share); **"the driver can always
  end a turn with `--turns 1`"** (see Operational kit).
