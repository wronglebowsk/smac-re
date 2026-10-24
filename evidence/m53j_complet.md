# M53j detail - COMPLET side-effect list + supporting negatives (session 62)

Machine-code cites are VAs in `evidence/m53j_text.txt`; pseudocode cites are
`evidence/<file>:<line>`. CFG walk: `evidence/m53j_cfg.txt` (subagent), parent spot-verified
0x4f0b05, 0x4f0b4f, 0x4f0bfa, 0x4f0ca1, 0x4f0cf2, 0x4ef8c0. MSVC C++ noise in this function = stores of
vtable constants 0x67164c/0x671d94/0x671644/0x671d8c plus calls 0x406720 / 0x406060 / 0x5f6de9 and the
`[ebp-0x4]` exception-state byte; those blocks are scope cleanup, not game logic.

## A. Race/claim scan (FUN_004ef6d0, projects idx >= 0x27 only)
- 0x4f0abb `mov eax,[ebp-0x1c]` (claim index idx-0x27, -1 for idx < 0x27) · 0x4f0abe `test` · 0x4f0ac0
  `jl 0x4f0b7b` -> non-claimable projects skip the scan entirely. 0x4f0ac6-0x4f0ad1 `mov al,[ebp-0x2c];
  mov cl,[ds:0x985b10]; test al,cl; jne 0x4f0b7b` -> also skipped when that byte intersects the faction
  mask. Scan start 0x4f0aeb `mov esi,0x95da14` (= base array + 4), counter `[ebp-0x34]`, bound
  DAT_00985af4, `add esi,0x130` (0x4f0b67), continue head 0x4f0af0.
- Filters inside: 0x4f0af6-0x4f0b03 `mov bl,[0x985b10]; mov cl,[esi]` (candidate owner byte) `; mov eax,1;
  shl eax,cl; test bl,al; je next` -> only bases of a faction in the active mask. 0x4f0b05
  `mov eax,[esi+0x4c]` (candidate base+0x50 head slot) · 0x4f0b08 `mov ebx,[edx+0x50]` (our head slot,
  edx = DAT_008f0d60) · 0x4f0b0b `cmp eax,ebx; jne next` -> only bases queueing the SAME item. 0x4f0b0f
  `cmp eax,0xffffffb9` (-0x47 = project 71, the Ascent) `; jne 0x4f0b21`; when equal,
  0x4f0b15 `call 0x59a9f0(owner)` and `je 0x4f0b57` (skip).
- 0x4f0b21-0x4f0b48 price = FUN_004e40a0([esi], 1, -1) x `[idx*0x30 + 0x984d44]`; 0x4f0b4f
  `cmp ecx,edx; jge 0x4f0c28` with ecx = `[esi+0xcc] + [esi+0x3c]` = candidate base+0xd0 + base+0x40
  (minerals) and edx = price. Taken -> 0x4f0c28 cleanup block -> `jmp 0x4f0bfa` = the function epilogue
  (0x4f0bfa call 0x5e3ced, 0x4f0c12 call 0x405f60, 0x4f0c17-0x4f0c19 pop edi/esi/ebx, 0x4f0c1d fs:0
  restore, `ret` at 0x4f0c27): NO game store on that arm. Fall-through -> 0x4f0b57 next base.
- Loop end -> 0x4f0b78 `mov ebx,[ebp-0x28]` · 0x4f0b7b `mov eax,[ebp-0x30]` (= idx) · 0x4f0b7e `test` ·
  0x4f0b80 `jg 0x4f0ca1`. 0x4f0ca1..0x4f0e00 has no other entry (whole-function jump census: landers in
  that range come only from 0x4f0b51 jge -> 0x4f0c28, 0x4f0b80 jg -> 0x4f0ca1, and internal branches), so
  the pay block is reached ONLY when the scan finished without any candidate passing the price test (or
  when the scan was skipped for idx < 0x27).

## B. Ordered side effects on the claim path
1. 0x4f0ca1-0x4f0ca6 MINERALS DEBIT: `mov esi,[edx+0x40]; sub esi,edi; mov [edx+0x40],esi` - current
   base+0x40 -= edi. edi = the price computed at 0x4ef8e2 (`mov edi,eax` right after call 0x4e40a0) and
   0x4ef8ed (`imul edi,[edx+0x984d44]`); no write to edi between (INFERRED that it is still the price).
2. 0x4f0ca9-0x4f0ce9 CLAMP: edx = min(DAT_0092a370 (= 10, the cap M53b found), [base+0xd0]); if
   `[base+0x40] > edx` and `(DAT_00985b10 & [ebp-0x2c]) != 0` then base+0x40 := clamp(0, min(cap, d0),
   cap) (0x4f0ce9 `mov [esi+0x40],eax`). Purpose UNCONFIRMED.
3. 0x4f0cf2-0x4f0cf5 `mov eax,[esi+0x40]; mov [esi+0x98],eax` -> base+0x98 := base+0x40. Live: equal for
   75/75 bases, so +0x98 is a mirror/snapshot of minerals, not a second pool.
4. 0x4f0d00-0x4f0d1a flags: base+0x30 |= 0x800000 (bit 23), then base+0x30 &= 0x7fffffff (bit 31 cleared).
5. 0x4f0d1d-0x4f0d23 `cmp [ebp-0x30],1; jne 0x4f0d73`: the facility-bitmap clear loop 0x4f0d35-0x4f0d71
   runs ONLY for idx 1 (= Headquarters, alpha FACILITIES[0]). It calls FUN_00507410(idx, &off@ebp-0x14,
   &mask@ebp-0x18) (off = idx>>3, mask = 1<<(idx&7)), then `mov dl,[esi+off]; not cl; and dl,~mask;
   mov [esi+off],dl` over every base (esi = 0x95da9c + i*0x130 = base+0x8c) whose owner byte == ebx (the
   current faction). No bitmap SET on this path.
6. 0x4f0d73-0x4f0d83 CLAIM STORE `mov [eax*4+0x985b3c],edx`, edx = DAT_0068cbb0 (current base index),
   eax = idx-0x27, guarded `test eax,eax; jl 0x4f0d8f` (skip when idx < 0x27).
7. Post-claim, gated on idx < 0x27 and `[ebp-0x20] != 0` (0x4f0d8f-0x4f0d94): 0x4f0dbf-0x4f0dc0
   `[0x94dbac + i*4] += 1`; 0x4f0de5 `or [eax+0x4],dl` ORs the faction bitmask into every faction record
   `0x92ae14 + 0x2c*i + 4`; 0x4f0e22 `or [eax],dl` ORs a byte into base+6 of every base and 0x4f0e27
   copies base0+6 into each base+6; 0x4f0e44 sets a unit-record flag bit via `[rec+0x94d430]` (`|= 2`).
   Semantics INFERRED (knowledge/talent spread style effects).
8. 0x4f0ed2 clears base+0x30 bits 24-25 when idx == 8, then calls 0x5ab130, 0x5a5c00 and 0x4737e0(x,y,2).
9. Announce: 0x4f0f6f loads the project name `[[idx*0x30] + 0x984d38]` -> 0x4f0f78 call 0x6265a2 (format
   into message buffer DAT_00997120) -> 0x4f0f96 call 0x626634 with the faction name
   (0x927894 + faction*0x24); displayed by FUN_0048f100 at 0x4f122a and 0x4f1319 (the claimed/announce
   chain at 0x4f07c2 has the same shape with the name loaded at 0x4f07ef).
10. 0x4f0f46 **THE POP**: `call FUN_004ef5d0(DAT_0068cbb0)`, result stored `[ebp-0x10]`.
11. The claim path falls through the effects region to the final `ret` at 0x4f26d9 - it does NOT return
    via 0x4f0bfa.

## C. THE POP = FUN_004ef5d0(base_idx), 244 B (`evidence/m53j_fn4ef5d0.txt`, shard_012.c:20536)
`iVar2 = (&DAT_0095da5c)[base*0x4c]` = base+0x4c (pending; int* index math, 0x4c*4 = 0x130 stride);
faction = `(&DAT_0095da14)[base*0x130]` = base+4. Loop: pending == 0 -> return 0; if head
`(&DAT_0095da60)[base*0x4c]` (= base+0x50) >= 0 -> `DAT_0094de84[faction*0x20bc + head] -= 1` (the
faction's per-type built counter); shift the queue left `*p = p[1]` for `pending` slots starting at
base+0x50; base+0x4c -= 1; then test the NEW head for availability - negative -> FUN_005a6e70(-head,
faction, base, 0), else FUN_005a73f0(head, faction, base) - and pop again until it is available. After
the loop: if the new head < -0x26 -> FUN_00446250(0x24); then FUN_00473760(base.x, base.y, 2, 2); return 1.
=> pending decrement, queue shift and head re-arm all live in the POP, which is why a whole-function store
census of FUN_004ef6d0 finds ZERO stores to base+0x4c, base+0x50 or base+0xd0 (the only base+0x50 store in
the function is 0x4f1e3f writing -38, in a region the claim path never reaches).

## D. Supporting negatives
- Record +0x14 (rendered `&DAT_00984d4c`) is the prereq tech: shard_012.c:28618-28619 uses it to index
  the tech-ownership bytes `DAT_00985c1c`.
- Record +0x18 (rendered `0x984d50`, the alpha "Disable" column = -2 in all 71 rows) is read at only 6
  sites in .text (0x44c694/0x44c6ea/0x44c743 in FUN_0044bf40, 0x49ea2a/0x49ea61/0x49eb06; corpus
  shard_003.c:4214-4236, shard_010.c:2229-2255), always compared against a tech/id value, never written,
  and never read inside FUN_004ef6d0 => not a completion trigger.
- Claim-array DAT census (`evidence/m53j_refs_claim.txt`, 2927 lines): DAT_00985aa0 = 8 refs, ALL loads;
  DAT_00985b3c = 44 refs.
- The 5 claim-region stores that are NOT the claim array: 0x4cd8a8/0x4cd9d8 `[.+0x985adc]` (FUN_004cce50,
  bit-OR mask array - shard_012.c:998-999 `| uVar8`), 0x59acc1 `[.+0x985b14]` (FUN_0059aa00), 0x523b32
  `[.+0x985bc4]` (FUN_00523b20, past the array end; `+ 1` increment at shard_013.c:13584).
- Pointer-based (no-disp32) claim writers: none. Address-takers all read: FUN_00519b00
  (`mov esi,ds:0x985b3c`), FUN_00535940 (`m53j_fn535940.txt:84` `local_8 = &DAT_00985b3c` walked against
  `&DAT_0098549c` testing `*claim == -1 && *0x98549c == local_10`), FUN_0041c8b0:29.
- Live state (read-only preads, pid 2124624, year 2371, cur 3, nb 75, cur base idx 70): base+0x40 range
  0..243 with NO negative value; base+0xd0 range 0..19; base+0x98 == base+0x40 for 75/75; 74/75 bases have
  pending 0 with a NON-empty head (only base 70 has pending 2 / head 3 = Scout Patrol). Base 8 (holds the
  project-39 claim) has head -29 = Aerospace Complex, minerals 78, +0xd0 9.
- Third confirmation of the -0x27 mapping: the AI FUN_004f6030 (header shard_012.c:24338, size 30475)
  enumerates advanced projects with a 0-based `param_1` and converts - shard_012.c:28613
  `local_20 = (byte *)((int)param_1 + 0x27);` immediately before `iVar9 = FUN_005a6e70();` (:28614), and
  `:28618` re-reads the record at `((param_1 + 0x27) * 0x30)`. Projects 39..71 are slots 0..32 in AI/UI
  code - exactly the 33 claim slots.
