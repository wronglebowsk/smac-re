# Session notes archive — sessions 62-62

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 62 (2026-10-23) — M53j: **THE CLAIM ARRAY IS 33 DWORDS AT 0x985b3c INDEXED BY (project_idx − 0x27) — projects 39..71 ONLY — AND ITS COMPLETION WRITER IS 0x4f0d83 INSIDE THE PRODUCTION PROCESSOR: pay (base+0x40 −= price) → flags → claim → announce → THE POP** — write-up `evidence/m53j_findings.md` (+ `evidence/m53j_complet.md` for the ordered side-effect list)

- **Geometry (VERIFIED, three ways).** M53i's "claim table DAT_00985aa0[72]" is superseded: only projects
  >= 0x27 have a slot, so the array is 0x985b3c..0x985bbf (33 dwords, index = idx − 0x27); the flat
  rendering `*(int *)(&DAT_00985aa0 + idx*4)` (`m53i_fn5a6e70.txt:58`, reachable only for `0x26 < idx`) is
  the compiler folding `0x985b3c + (idx-0x27)*4`. Machine code computes it at 0x4ef89f-0x4ef8ac
  (`neg ecx; cmp ecx,0x27; lea edx,[ecx-0x27]`, else -1). DISCRIMINATOR: `shard_001.c:5424-5444`
  (FUN_00411180) walks 0x985aa0..**0x985bc0** and branches ON ADDRESS: `< 0x985b3c` -> facility bitmap
  `(&DAT_0095da9c)[idx>>3 + base*0x130]` for `< 0x985b29` (= idx < 0x23) else `FUN_005a6de0`;
  `>= 0x985b3c` -> `*piVar7 == DAT_0068cbb0`. Loop end 0x985bc0 = 0x985b3c + 33*4. Slots 0x985aa0..0x985b38
  hold other globals (live: 0x985af4 = 75 = nbases, 0x985b00 = 2371 = year, 0x985b10 = 0xff08 = mask).
  Third confirmation: the AI FUN_004f6030 converts `param_1 + 0x27` (shard_012.c:28613) before calling
  FUN_005a6e70.
- **Writers (VERIFIED whole-.text shape census, `evidence/m53j_refs_985aa.txt`: 3093 refs / 8 stores in
  0x985aa0..0x985bd0, only 3 based inside the array).** (1) **0x4f0d83**
  `mov [eax*4+0x985b3c],edx`, edx = DAT_0068cbb0 (current base INDEX), eax = idx−0x27, guarded
  `test eax,eax; jl` — in FUN_004ef6d0 = `m53i_fn4ef6d0.txt:892` (shard_012.c:21475). (2) 0x59d595
  FUN_0059ce10: `_rand() & 0x80000007` re-rolled while `claim[u] != -1 || u == 4 || (u == 5 && f == 2)`
  then `claim[u] = base_idx` (`m53j_fn59ce10.txt:286-291`), sole caller FUN_005a0fa0. (3) 0x41cd7d
  FUN_0041c8b0 (dtor-heavy handler, value pre-processed by `cmp eax,0x2328 / sub eax,0x2710`), sole caller
  FUN_0041d480 — INFERRED scripted/debug. No pointer-based writer: the address-takers (FUN_00519b00,
  FUN_00535940, FUN_0041c8b0) all read. Other claim-region stores belong to other arrays (0x985adc
  FUN_004cce50 mask array, 0x985b14 FUN_0059aa00, 0x985bc4 FUN_00523b20).
- **Two pointer-shift artifacts (VERIFIED) — these correct M53i.** (a) Ghidra typed DAT_008f0d60 and its
  pseudocode copies `short *`, so pseudocode offsets on them are HALF the byte offset
  (`psVar22 + 0x28` == machine `[DAT_008f0d60+0x50]`; `* 0x98` == the 0x130 stride; int* flavor in THE POP:
  `(&DAT_0095da5c)[base*0x4c]` == base+0x4c). (b) the per-base loop walks `esi = 0x95da14` = base + 4.
  ⇒ M53i's open question "what IS base+0x20?" is answered: `*(int *)(DAT_008f0d60 + 0x20)` is machine code
  0x4ef8fa `cmp [edx+0x40],edi` = **base+0x40 = the mineral store**; and the "pay pool base+0xcc + 0x3c" is
  really **base+0xd0 + base+0x40** (completion test 0x4f0b31-0x4f0b51).
- **COMPLET path (machine-code shapes VERIFIED; arm meaning partly INFERRED).** Race scan (idx >= 0x27
  only; 0x4f0abb `jl` skips it): loop 0x4f0af0 over bases (esi = base+4, +0x130/iter), keep only bases of a
  masked faction and whose head slot `[esi+0x4c]` == our head `[DAT_008f0d60+0x50]` (0x4f0b05-0x4f0b0d); a
  shared head of −0x47 (project 71) calls FUN_0059a9f0; **0x4f0b4f `cmp [esi+0xcc]+[esi+0x3c], price;
  jge 0x4f0c28` -> dtor -> 0x4f0bfa epilogue (`ret` 0x4f0c27), no store**; loop end -> 0x4f0b78
  `test [ebp-0x30]; jg 0x4f0ca1` = SOLE entry to the pay block: 0x4f0ca1-0x4f0ca6 `base+0x40 −= edi`
  (edi = price, 0x4ef8e2/0x4ef8ed), clamp 0x4f0ca9-0x4f0ce9, `base+0x98 := base+0x40` (0x4f0cf5; live equal
  75/75 => mirror), base+0x30 |= 0x800000 then &= 0x7fffffff (0x4f0d00-0x4f0d1a), then the FUN_00507410
  bit-clear loop 0x4f0d35-0x4f0d71 which runs ONLY for idx 1 (Headquarters) and only on the current
  faction's bases; claim store 0x4f0d83; post-claim 0x4f0dc0-0x4f0e44 (`[0x94dbac+i*4]++`, OR the faction
  bit into every `0x92ae14+0x2c*i+4`, OR a byte into base+6, unit-record flag `|= 2`); announce
  0x4f0f6f name -> 0x4f0f78 0x6265a2 -> DAT_00997120, faction name 0x927894+f*0x24 at 0x4f0f96, displayed
  by FUN_0048f100 (0x4f122a/0x4f1319); **THE POP at 0x4f0f46** `call FUN_004ef5d0(DAT_0068cbb0)`; the claim
  path exits via `ret` 0x4f26d9. Record +0x18 (alpha "Disable" = −2) is never read here (6 read sites all
  elsewhere) => not a trigger.
- **THE POP = the queue work (VERIFIED pseudocode `evidence/m53j_fn4ef5d0.txt`).** pending 0 -> return 0;
  head >= 0 -> `DAT_0094de84[faction*0x20bc+head] -= 1`; shift base+0x50.. left `*p = p[1]` × pending;
  base+0x4c -= 1; re-test the new head with FUN_005a6e70(−head,f,base,0) / FUN_005a73f0 until available;
  head < −0x26 -> FUN_00446250(0x24); then FUN_00473760(x,y,2,2). Explains the zero stores to
  base+0x4c/0x50/0xd0 inside FUN_004ef6d0.
- **Live cross-check (read-only preads, pid 2124624, year 2371, cur 3, nb 75 unchanged).**
  claim[39]=base 8, [41]=2, [42]=4, [45]=3, every other slot −1; those bases are alive (pop 7/7/3/4) and
  owned by four DIFFERENT factions (7,2,5,4); base 8's bitmap has bit 39 clear (>= 39 projects have no
  facility bit, exactly as the pane branch predicts); base 8's head is −29 = Aerospace Complex. Whole
  array: base+0x40 in 0..243 (none negative), base+0xd0 in 0..19, base+0x98 == base+0x40 for 75/75, and
  74/75 bases have pending 0 with a NON-empty head.
- **Next:** `NEXT_PROMPT.md` rewritten for session 63; **THE PICK = M53k** (the accumulation side: who
  writes base+0xd0 / base+0x40 / base+0x30 bits 23+31 each turn, and what the 0x4f0b4f arm really means).
