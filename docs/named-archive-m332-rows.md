# NAMED archive — M262-M266 rows, moved VERBATIM out of `NAMED.md` at s311-chain1 (M332 headroom rotation).
sha1 of the moved block: 4dc92495311ef1f0b30b0c16dd5363f5c7d91796 (byte-exact, asserted by `scripts/m332_named_rotate.py`).

## M262-M264 (s205, PASS 11/11) — the view table IS allocated at startup; the LOAD never re-derives the band; the allocator and the record cursor

**M262 the view table** — band 0x7cdecc..0x7cdee8: 426 mentions, exactly 1 store names it (0x5803e1, entry 0
= the static object), and all 39 `[reg*4+0x7cdecc]` mentions in 12 functions are reads/cmps — 0 indexed
stores (G1, cross-checked against a regenerated objdump corpus: 39 mentions / 0 indexed stores / 1 band
store). The writer of entries 1..7 is FUN_00580260's loop at 0x580392: cursor esi 0x7cded0, bound
`cmp esi,0x7cdeec` / `jl 0x580397`, step `add esi,4` = 7 iterations; body `push 0x22480 ; call 0x64bc20`
(140,416 B each) → `push 1 ; mov ecx,eax ; call 0x469650` (515-B SEH ctor; it does NOT call the view ctor
0x518820) → **`mov [esi],eax`** at 0x5803bb, the pointer-arithmetic shape an address-grep cannot see;
`xor eax,eax` feeds it only on the alloc-failure path, which is why M260 read the loop as a zero-fill (G2).
0x22480 is named exactly once image-wide (0x580397), 0x224b8 zero times, delta 0x38 (G3). 35 address-of-band
sites, only 4 escapes and all 4 hand out `&DAT_007cdecc` (push at 0x50ba50/0x50baee/0x50bd98/0x517553); the
4 lea'd `[reg*4+0x7cdecc]` cursors (0x50a68a, 0x50a79e, 0x512ea5, 0x512fd1) are re-read only (G4). Entry 1
(0x7cded0): 32 reads in ≥12 functions (FUN_004412a0 8, FUN_004411b0/FUN_004cb650/004cb6b0/004cb7b0 4 each);
the load-side FUN_00597ee0 walks entries 2..7 from 0x597f6d (esi 0x7cded4 → 0x7cdeec step 4) clearing
`*(entry+0x1dd74)` and calling FUN_00479e90(entry) for every non-null one (G5).

**M263 the band on LOAD** — the writer set re-derives to 8 functions / 10 indexed stores {FUN_004e14d0
0x4e153b; FUN_004ef6d0 0x4f0def; FUN_0053a820 0x53a8d9 + 0x53a90c; FUN_00582fc0 0x582fec; FUN_00583c70
0x583e1d; FUN_005a3470 0x5a3b95 + 0x5a3d3f; FUN_005a7970 0x5a7afd + 0x5a86aa} plus FUN_0051c750's walk
store 0x51ca52 (G6). Only FUN_00596850 (call at 0x596fd0) and FUN_00597a70 (0x597cc0) call map_load_arrays
0x582260; the depth-9 forward closure of those two plus their 4 callers (FUN_00597ce0/FUN_00597ee0/
FUN_00598250/FUN_00598340) is 276 functions and meets the writer set in ZERO, and no band writer sits in
any vtable slot — so neither a direct nor an indirect route reaches them from a load: **the LOAD trusts the
file's band bytes** (G7). FUN_00582260 itself has no band-shaped store and no call into the writer set;
FUN_00583c70 has ZERO references in the image (no call, no imm32, no slot), so 0x583e1d can never execute;
the other writers hang off gameplay passes: FUN_004e14d0 ← FUN_00516b80 ← FUN_005186b0, FUN_004ef6d0 ←
FUN_004f5a70, FUN_0051c750 ← FUN_0051f320, FUN_005a7970 ← 24 callers (G8).

**M264 the allocator + the record cursor** — FUN_005be090 (72 B / 24 insns) is operator-new: arg1 →
FUN_00649e00 (29 B) → FUN_00649e70(size, ds:0x99d5f8 = the heap handle, 1, 0, 0); the NULL path reports
through the GLOBAL function pointer ds:0x671320 with 0x698890 "FATAL ERROR" and 0x69889c "Windows has run
out of virtual memory; the game will exit. Recom…", then `push 4 ; call 0x649c80`. No vtable slot holds it;
119 direct sites in 74 functions (G9) — the footing's "13 [reg+4] sites" are store-after-alloc sites, not
dispatch: 14 sites in 13 functions store the new pointer at [obj+4] within 8 insns (0x479647, 0x479da5,
0x47a0d0, 0x58aefc, 0x58af0d, 0x5be208, 0x5be4d8, 0x5be5fc, 0x5becb5, 0x5cca3c, 0x5dc1ed, 0x5e351a,
0x5e361c, 0x62cd28) (G10). ds:0x9965b8 — 6 mentions = 3 read/modify/write pairs, one per function — is a
LINEAR RECORD CURSOR: FUN_005dbb5f (33 insns, ~150 callers) stamps a blank record (10 dword zero stores +
`mov byte ptr [ecx+0x8],0x9`) and `add ecx,0x2c`; FUN_005dbbe6 (63 insns) gates [rec+0x28]==0 and
[rec+4]!=0, `sub edx,ecx` with ecx = [rec+0x10]*[rec+0x14], and frees [rec+4] via FUN_0064a7f0 (19 B,
221 callers); FUN_005dbdc0 (1303 B, ret 0x1c) is the FILLER — allocates [rec+0x10]*[rec+0x14] bytes at
0x5dc1ed, stores the pointer at [rec+4], then advances the cursor by the same product (G11).

## M265-M266 (s206, PASS 12/12) — the 7 view-table blocks are class-0x675964 objects (201 × 608-B elements + a 2,580-B virtual subobject, size proven); FUN_00583c70 is statically unreachable

**M265 the blocks** — ctor FUN_00469650 (515 B), exactly 7 `call` sites {0x40a027, 0x468fc0, 0x48dc7a, 0x4cb5cf, 0x50aaae, 0x5803b2, 0x59befc}; its `[ebp+0x8]` flag gates `mov [this+0],0x675964` (0x469681, the only mention image-wide), so the sites passing 0 keep their own descriptor (G1/G2). Layout: [0] = class descriptor 0x675964, whose dword[+4] = 0x21a6c IS the base-subobject offset — the law holds for all three descriptors found this way (0x675964→0x21a6c, 0x6763fc→0x22050, 0x678458→0x23d94), each matching the `add ecx,K`/`lea ecx,[reg+K]` feeding `call 0x5e3b80` (53 callers) in its installer (G5); [4] = a lazily-freed pointer; +0xc..+0x1dd6c = **201 contiguous 608-B elements** (0x64bda0 constructs 4 at +0xc and 196 at +0x98c with element ctor/dtor 0x62514b/0x62516c, and the same element ctor runs in place at +0x1db0c) — the 201st ends 8 B before the +0x1dd74 the load-side clears (G3); +0x1de28/+0x1e3b0/+0x1e938 via 0x5bee2f, +0x1eec8/+0x1eef4/+0x1ef20 via 0x617060, +0x1ef54 = 4 × 2756-B elements (ctor 0x6251d0 installs vtable 0x679e08); the subobject at +0x21a6c has its vptr pair overwritten to 0x6725ac there and 0x6725a4 at +0x21eb0 (delta 0x444, both vtable bases) — a pair stored at 5 sites in 1 ctor + 4 destructors {ctor FUN_00469650; destructors FUN_00421950, FUN_00518980, FUN_0059bec0, FUN_0059c1e0} (G4; roles corrected by M267). SIZE: FUN_005e3b80's stores top out at +0xa10 and 0x21a6c + 0xa14 = 0x22480 = the allocation exactly (G6). Dispatch goes through [desc+4]: FUN_004412a0 calls slots +4/+8 of 0x6725ac (= FUN_005cdd0a / FUN_005cdf82), the same two it also calls directly on the static instance 0x8cc520; FUN_00479e90 frees [this+4] via 0x4017d0 then `this += [desc+4]` → 0x5e3d74 (G7).
**M266 FUN_00583c70** — dead code, not a split body and not a duplicate: 0 occurrences in .text operands AND 0 as an LE dword anywhere in the file image (all 8 sections) (G8); predecessor FUN_00583c20 rets at 0x583c6b, four 0x90 pad bytes, then a real push ebp/mov ebp,esp prologue (G9); it is 1 of 8 functions in 0x583000..0x584300 with n_callers==0 and all 8 have 0 address-taken dwords (G10); its 159-insn mnemonic signature matches 0 other functions ≥40 insns (G12); it is a terrain-record helper of FUN_00583c20's family — callees {0x582000, 0x5b09b0, 0x625af1, 0x64a7f0}, globals ds:0x92a378/0x92a37c, the stride-0x2c sibling's (G11). M263's band store 0x583e1d can never execute.



§rotation-2 (M332 headroom): the M267-M268 + M269-M271 rows, moved VERBATIM out of `NAMED.md` at s311-chain1. sha1 of the moved block: fc92a881bd3135454b5f1d64e8ab4ae356855cc0 (byte-exact, asserted by `scripts/m332_named_rotate2.py`).

## M267-M268 (s208, PASS 14/14) — the 0x6725ac/0x6725a4 pair is one vtable (entry points 8 B apart) shared by 1 ctor + 4 destructors of 4 variants of the virtual base at [desc+4]; the 201 x 608 block is tag-initialized, never indexed, never saved

`scripts/m267_m268_census.py` -> `evidence/m267_m268_census.txt` (14/14, 4.2 s, static, no box time).
**M267** — 5 pair stores: 0x6725ac {0x42197e, 0x469798, 0x518a92, 0x59c01a, 0x59c25b} + 0x6725a4
{0x42198e, 0x4697aa, 0x518aa2, 0x59c02e, 0x59c26b}. 0x6725a4 == 0x6725ac - 8: ONE code-pointer run
ending 0x672a38, 291 slots from 0x6725ac / 293 from 0x6725a4; heads 0x4222c0, 0x405350, 0x422190 are
not function starts (thunks). 0 address-taken dwords for any installer -> direct call only, not
vmethods. FUN_00469650 = ctor (3 x 0x64bda0 ctor-iterator, 0 x 0x64bc40); FUN_00421950, FUN_00518980,
FUN_0059bec0, FUN_0059c1e0 = destructors (0 ctor-iter; 3/4/3/3 dtor-iter) — corrects M265 G4 "5
ctors". Variants by what else each writes: 0x675964 | none | 0x678184+0x67817c (+0x23d94 subobject,
class 0x678458, ctor FUN_0050aa60) | 0x67194c+0x671944 | 0x67194c+0x671944 into stack slots
(FUN_0059bec0: 0x25318 = 152,856-B stack frame, flag 1, calls the save writer 0x597ce0 at 0x59bf46).
The pair is the vptr pair of a VIRTUAL BASE: `[vptr-4] = [desc+4] - 0x21a6c` (shard_008.c:5869),
recomputed by all 5 installers within 14 insns (sub/lea with the constant 0x21a6c).
**M268** — element ctor 0x62514b and dtor 0x62516c write the same 2 POD stores {dword0 = 3, dword1 =
0}, no vptr, no callee (dtor 5 ops vs ctor 6, the extra a dead reload). 4 at +0xc + 196 at +0x98c + 1
at +0x1db0c = 201 x 608 = **122,208 B** ending +0x1dd6c (corrects the 121,600 = 200 x 608 figure).
All 21 `0x260` immediates in .text are iterator arguments (10 in the installers) or their EH unwind
records (10) + 1 at 0x44407d; ZERO add/sub/imul/lea/cmp uses 0x260 as an immediate. The 94 folded
displacements with (d-0xc) % 608 == 0 (13 values, 3.65x the uniform 25.8 expected of 15,656) occur in
NO function that loads a view pointer from DAT_007cdecc. The per-view save routine FUN_00596620 (codec
loop shard_015.c:10822-10829 walks the 8 pointers 0x7cdecc..0x7cdeec) touches only +0x1dd70..+0x1dda0.
No alpha.json table has 196 or 201 rows (max 89 TECHNOLOGY). OPEN: what writes the block; what tag 3 means.

## M269-M271 (s210, PASS 10/10) — the `[vptr-4] = [desc+4] - K` virtual-base delta is an IMAGE-WIDE mechanism (41 stores / 8 K / 31 functions; 177 vptr installs through a vbptr of 33 tables; 9 primary+0x444-secondary pairs 8 B apart); 32 vbtable descriptors close the K census; the 0x67194c "variant" is M215's row inside the 0x678e40 class, a 0x25318-B stack local of FUN_0059bec0

**M269 the virtual-base delta census** a 3-level symbolic shadow over the whole `.text` (field load -> `[desc+4]` -> `lea [r-K]`/`sub r,K` -> store) accepts a store only when its address resolves to `field + [desc+4] - 4`, i.e. exactly 4 below the virtual base the same field expression computes: 41 delta stores in 31 functions at 8 K (0x18 x11, 0x1c x2, 0x48 x2, 0x8c x4, 0x188 x14, 0x21a6c x5, 0x22050 x1, 0x23d94 x2). The 5 K=0x21a6c functions are EXACTLY M267's 5 installers (G1/G2: two independent detectors agree). The same pass finds 177 vptr installs made THROUGH a vbptr of 33 distinct rdata tables and 9 secondary-view tables whose primary sits 8 B above with the identical install count (0x671ab8/0x671ac0 14/14, 0x671c28/0x671c30 11/11, 0x6725a4/0x6725ac 5/5, 0x676298/0x6762a0 1/1, 0x67817c/0x678184 2/2, 0x6797b8/0x6797c0 2/2, 0x679934/0x67993c 2/2, 0x679ab0/0x679ab8 2/2, 0x679c40/0x679c48 2/2) — M267's pair is the rule, not a curiosity; biggest family 0x6713a0, 52 installs. 21 further lineage-matched stores of a delta value are `sub reg,1` arithmetic (reported, not gated). `scripts/m269_m271_census.py` -> 10/10, `evidence/m269_m271_census.txt`.

**M271 the vbtable descriptor census** 32 of the 247 distinct rdata immediates that code stores through a register are virtual-base tables (dword[0] and dword[+4] both |v| < 0x40000, neither a code pointer); their dword[+4] values are 21 distinct virtual-base offsets, and every K the delta census found is one of them: 0x18->0x6713ac/0x6713f4/0x671408/0x67141c/0x671430, 0x1c->0x679a98, 0x48->0x67991c, 0x8c->0x679c28/0x679da4, 0x188->0x679de0, 0x21a6c->0x675964, 0x22050->0x6763fc, 0x23d94->0x678458. Every candidate has at least one installer; [0x675964]=0,[+4]=0x21a6c is installed only by FUN_00469650 and [0x678458+4]=0x23d94 only by FUN_0050aa60, and both installers carry a delta store at their own K (G3/G9/G10).

**M270 the 0x678e40 class (one 152,856-B stack instance)** 0x678e40 and its secondary 0x678e38 (+0x2444) are each stored EXACTLY once image-wide (0x59bf1c, 0x59bf26, both inside FUN_0059bec0): never heap-allocated, one instance site. Slot 0 of each is its deleting-dtor wrapper (0x59c380 at 0x678e40, 0x59c3b0 at 0x678e38; 0x59c380 calls FUN_0059c1e0 then 0x64bb70). Neither FUN_0059c1e0 nor FUN_0059bec0 is address-taken; callers(0x59bec0) = FUN_0050fea0/0x512b40/0x516b80/0x51e700. Layout (G7/G8): +0 the 0x5e3b80/0x5e3ced class, +0x2320 the 0x675964 class (0x2320+0x22480 = 0x247a0), +0x247a0 M215's 0xb4c row (0x247a0+0xb4c = 0x252ec = where FUN_0059bec0 calls the 0x614150 ctor AND where FUN_0059c1e0 calls 0x6141c1), virtual base at +0x23d8c = 0x2320+0x21a6c (both destroy it via 0x5e3ced, so it is the same type as the +0 object), size 0x25318 = the only 0x25318 immediate in the image (the `_alloca_probe` value at 0x59bed1) = the span [ebp-0x25324, ebp-0xc). RETRACT part of M267: FUN_0059bec0 is NOT a destructor (four constructors run before it installs 0x678e40; the same objects die at its tail) and 0x67194c/0x671944 in it are the ROW subobject at +0x247a0/+0x247a0+0x444, never [this+0] — the installer of 0x67194c at [this+0] is FUN_005faec0 (M215).
