# M53j — completion bookkeeping (session 62)

Cite unit: `evidence/<file>:<line>` for pseudocode dumps; machine-code claims cite the VA in
`evidence/m53j_text.txt` (objdump -M intel of terran.exe .text, cached this session, 790702 lines).

## 1. The claim array is 33 dwords at 0x985b3c, index = project_idx − 0x27  (VERIFIED)
M53i's "claim table DAT_00985aa0[72]" is superseded: only projects >= 0x27 have a slot.
- Gate rendering: `m53i_fn5a6e70.txt:58` `return *(int *)(&DAT_00985aa0 + param_1 * 4) == -1;`, reached
  only under `0x26 < param_1` (`:25`, `:57`) — the flat disp is the compiler folding
  `0x985b3c + (idx-0x27)*4` into `0x985aa0 + idx*4`. 0x985aa0 + 0x9c = 0x985b3c.
- Machine code proves the index (FUN_004ef6d0): 0x4ef88b `mov ecx,[eax+0x50]` (head slot) · 0x4ef88e
  `cmp ecx,0xffffffda` (−38 = empty) · 0x4ef899 `jge 0x4efa2c` (>= 0 ⇒ unit) · 0x4ef89f `neg ecx` ·
  0x4ef8a1 `cmp ecx,0x27` · 0x4ef8a4 `mov [ebp-0x30],ecx` (= idx) · 0x4ef8a7 `jl` → 0x4ef8b1
  `mov [ebp-0x1c],0xffffffff` else 0x4ef8a9 `lea edx,[ecx-0x27]` · 0x4ef8ac `mov [ebp-0x1c],edx`.
  All claim accesses then use that value: 0x4ef928 `cmp [eax*4+0x985b3c],-1` (pseudocode
  `m53i_fn5a6e70`-equivalent read `m53i_fn4ef6d0.txt:625`), 0x4f0d83 store.
- DISCRIMINATOR (VERIFIED, corpus): `ghidra_out/shard_001.c:5424-5444` (FUN_00411180, the base-pane
  "projects finished here" counter, header at shard_001.c:5310) walks `piVar7 = &DAT_00985aa0` with
  `while ((int)piVar7 < 0x985bc0)` (72 slots) and BRANCHES ON THE ADDRESS, not on the value:
  `if (piVar7 < 0x985b3c)` → for `piVar7 < 0x985b29` test the facility bitmap
  `(&DAT_0095da9c)[idx>>3 + base*0x130] & (1<<(idx&7))` (0x985b29 ⇒ idx < 0x23, exactly the
  `iVar4 < 0x23` threshold at `m53i_fn5a6e70.txt:68`), else `FUN_005a6de0(idx, owner)`;
  `else` (`>= 0x985b3c`) → `*piVar7 == DAT_0068cbb0` (current base INDEX). Loop end 0x985bc0 =
  0x985b3c + 33*4 = the array's exact end ⇒ claim array = 0x985b3c..0x985bbf, projects 39..71.
- Slots 0x985aa0..0x985b38 are OTHER globals, not claims: live pread (pid 2124624) gives
  0x985af4 = 75 = n_bases, 0x985b00 = 2371 = year, 0x985b10 = 0x0ff08 = faction mask,
  0x985ac4 = 0x1a0e = scenario flags (`evidence/m53j_claim_live.txt`) — values no claim entry has.
## 2. Claim-array writers: 3 store sites in the whole .text  (VERIFIED census)
Whole-.text census of every instruction with a disp32 in 0x985aa0..0x985bd0, classified by operand
SHAPE (dest-in-brackets = STORE; `lea`/bare-imm = ADDR): 3093 refs, 8 stores
(`evidence/m53j_refs_985aa.txt`). Only 3 of the 8 have their base inside 0x985b3c..0x985bbf:
1. **0x4f0d83 `mov [eax*4+0x985b3c],edx`** — edx = `DAT_0068cbb0` (current base index, loaded 0x4f0d7a),
   eax = `[ebp-0x1c]` = idx−0x27, guarded `test eax,eax; jl 0x4f0d8f` (0x4f0d73-0x4f0d78) ⇒ writes only
   when idx >= 0x27. In FUN_004ef6d0 (production processor) = pseudocode `m53i_fn4ef6d0.txt:892`
   `(&DAT_00985b3c)[(int)psVar23] = DAT_0068cbb0;` (shard_012.c:21475; FUN_004ef6d0 body starts at
   shard_012.c:20584). **THE completion writer.**
2. 0x59d595 `mov [eax*4+0x985b3c],ecx` in FUN_0059ce10 — `do { uVar14 = _rand() & 0x80000007; ...
   } while (claim[uVar14] != -1 || uVar14 == 4 || (uVar14 == 5 && local_8 == 2)); claim[uVar14] =
   iVar9;` (`m53j_fn59ce10.txt:286-291`) = random grant of an unclaimed project to base iVar9; its only
   caller is FUN_005a0fa0 (shard_015.c:17023).
3. 0x41cd7d `mov [esi*4+0x985b3c],eax` in FUN_0041c8b0 — dialog/handler frame (dtor calls 0x406060,
   vtable-const stores), value pre-processed 0x41cd6e-0x41cd75 `cmp eax,0x2328; jl; sub eax,0x2710`;
   pseudocode `m53j_fn41c8b0.txt:139-143`; only caller FUN_0041d480 (shard_001.c:11782).
   INFERRED: scripted/debug assignment, not the turn loop.
## 3. Two pointer-shift artifacts in FUN_004ef6d0 (VERIFIED) — corrects M53i offsets
- **(a) `short *` scaling.** Ghidra typed DAT_008f0d60 (current-base ptr) and its pseudocode copies
  (psVar20/psVar22/psVar23/local_34) as `short *`, so every offset added to them is HALF the byte
  offset. Proofs: `m53i_fn4ef6d0.txt:130` `psVar22 + 0x28` ↔ 0x4ef883 `mov eax,ds:0x8f0d60` +
  0x4ef88b `mov ecx,[eax+0x50]` (head queue slot, 0x28×2 = 0x50); `:270`
  `DAT_008f0d60 = &DAT_0095da10 + psVar23 * 0x98` ↔ the 0x130-stride base array (0x98×2 = 0x130).
- **(b) base+4 walk.** The per-base loop uses `esi = 0x95da14` (0x4f0aeb) = base + 4, `add esi,0x130`
  (0x4f0b67): `[esi]` = base+4 owner byte, used AS THE FACTION (0x4f0af6-0x4f0b03
  `mov cl,[esi]; mov eax,1; shl eax,cl; test bl,al` against the mask DAT_00985b10);
  `[esi+0x4c]` = base+0x50 head slot, `[esi+0x3c]` = base+0x40 minerals, `[esi+0xcc]` = base+0xd0.
- ⇒ **the affordability question from M53i is answered**: `m53i_fn4ef6d0.txt:601-604`
  `iVar3 <= *(int *)(DAT_008f0d60 + 0x20)` is machine code 0x4ef8f4 `mov edx,ds:0x8f0d60` +
  0x4ef8fa `cmp [edx+0x40],edi` ⇒ **base+0x40 = the base's MINERAL store**; the same branch's
  `psVar23 == 0x20` is claim-index 32 ⇒ project 71 = The Ascent to Transcendence, and that arm calls
  FUN_0059a9f0 (0x4ef906). No unknown field.
- ⇒ **M53i's "pay pool = base+0xcc + base+0x3c" is really base+0xd0 + base+0x40 (minerals)**:
  0x4f0b31-0x4f0b51 `mov eax,[ebp-0x30]` (idx) · `mov ecx,[esi+0xcc]` · `mov ebx,[esi+0x3c]` ·
  `add ecx,ebx` · `lea eax,[eax+eax*2]; shl eax,4` (= idx*0x30) · `imul edx,[eax+0x984d44]` (price) ·
  `cmp ecx,edx; jge 0x4f0c28` ⇒ **completion test = price <= base+0xd0 + base+0x40**.

## 4. Live cross-check (read-only preads, pid 2124624; year 2371, cur 3, nb 75, cur base idx 70 — unchanged)
`evidence/m53j_claim_live.txt`. Claim slots live: 39→base 8, 41→base 2, 42→base 4, 45→base 3; every
other slot 40, 43, 44, 46..71 = −1. Those bases are alive (pop 7/7/3/4) and owned by four DIFFERENT
factions (owner bytes 7, 2, 5, 4) ⇒ one faction per project, first completion keeps it.
Projects >= 39 have no facility bit: base 8's bitmap bytes 0x8c..0x91 = `10 00 00 00 00 00`, bit 39

## 5. COMPLET = pay -> flags -> claim -> announce -> POP  (VERIFIED shapes; the full ordered list, the POP
body and the supporting negatives are in `evidence/m53j_complet.md`)
- Scan (idx >= 0x27 only; 0x4f0abb `jl 0x4f0b7b` skips it): 0x4f0af0 loop over bases (esi = base+4), skip
  unless `(1<<[esi]) & DAT_00985b10` and candidate head `[esi+0x4c]` == `[DAT_008f0d60+0x50]`
  (0x4f0b05-0x4f0b0d); price = 0x4e40a0([esi],1,-1) x `[idx*0x30+0x984d44]`; **0x4f0b4f cmp
  [esi+0xcc]+[esi+0x3c] vs price, `jge 0x4f0c28` -> dtor -> 0x4f0bfa epilogue (`ret` 0x4f0c27)**; loop end
  -> 0x4f0b78 `test [ebp-0x30]; jg 0x4f0ca1` = SOLE entry to the pay block.
- Pay 0x4f0ca1-0x4f0ca6 `base+0x40 -= edi` (edi = price, 0x4ef8e2/0x4ef8ed); clamp 0x4f0ca9-0x4f0ce9;
  0x4f0cf5 `base+0x98 := base+0x40`; 0x4f0d00-0x4f0d1a base+0x30 |= 0x800000 then &= 0x7fffffff; the
  FUN_00507410 bit-clear loop 0x4f0d35-0x4f0d71 runs only for idx 1 (Headquarters), current faction only.
- THE POP at 0x4f0f46 `call FUN_004ef5d0(DAT_0068cbb0)` performs the queue shift, base+0x4c-- and the head
  re-arm => FUN_004ef6d0 has zero stores to base+0x4c/0x50/0xd0. Announce 0x4f0f6f/0x4f0f78/0x4f0f96 ->
  DAT_00997120, displayed by FUN_0048f100 (0x4f122a/0x4f1319). Claim path exits via `ret` 0x4f26d9.
- OPEN (arm direction VERIFIED, meaning INFERRED): the pay block is the arm taken when NO racing base has
  progress+minerals >= price, yet it debits the full price - needs a live probe (0x4f0b4f/0x4f0ca1/0x4f0d83).
