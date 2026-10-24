# M53s — writer of base+0xc4 after FUN_004e78e0's history shift

## Answer
**FUN_004eaa10** is the writer. Two stores to `[DAT_008f0d60 + 0xc4]` (the current base record's energy field):

1. `0x4eaa30` — entry, unconditional: `mov esi,[eax+0xc4]; mov ecx,ds:0x8f0c74; add esi,ecx; mov [eax+0xc4],esi`
   → `base+0xc4 += DAT_008f0c74`. DAT_008f0c74 is zeroed by FUN_004e8d60 (shard_012.c:16773-16778, group 0x8f0c6c..0x8f0c78) and has NO other store anywhere: pseudocode corpus has exactly one write (`= 0`, shard_012.c:16776) and a machine grep of .text for `mov DWORD PTR ds:0x8f0c74` / opcode `89 xx 74 0c 8f 00` / `c7 05 74 0c 8f 00` returns empty. So this addend is normally 0.
2. `0x4eac62` — inside the per-other-faction loop (factions 1..7, `cmp esi,0x1c` at 0x4eac7e): `mov eax,ds:0x8f0d60; mov ecx,[eax+0xc4]; add ecx,esi; mov [eax+0xc4],ecx`
   → `base+0xc4 += esi`, once per qualifying OTHER faction. This is the ENERGY-ONLY residual delta.

## esi formula (allied-faction energy share), read from disasm 0x4eab33-0x4eac4a
Gate per faction `other` (must ALL pass, else skip, esi not added):
- stance bit: `test BYTE [0x94d448 + owner*0x20bc + other*4], 0x2` (0x4eab33) OR reverse `test BYTE [0x94f504 + other*0x20bc + owner], 0x2` (0x4eab3b) — alliance in either direction;
- `faction[other].+0xd54 != 0` (`mov ecx,[eax+0xd54]` 0x4eab47);
- `FUN_004ea940(other, local_10) >= 0` (call 0x4eab5a) — the local_10-th nearest base of `other` exists (4ea940 walks 0x95dac4 with `add esi,0x130` at 0x4ea989, owner byte `[esi-0xb0]` → base array stride 0x130 VERIFIED);
- zero-gate AFTER computing: `[0x94d4f0 + owner*0x20bc] != 0` (0x4eac33) OR `[faction[other]-0x244] != 0` (0x4eac40) → `xor esi,esi` (0x4eac4a).

Value:
- `n = ebx = ((base[k]+0xb4 + base+0xb4 + 7 + (sum&7)) >> 3)` (0x4eab79-0x4eab9c), doubled if `DAT_00985bd4 < DAT_00985bd0` (0x4eab9f-0x4eaba3);
- `esi = ((([0x94d734 + owner*0x20bc] + 1) * n + ((count-1)>>1)) / (DAT_0092a274+1))` (0x4eabe0-0x4eabef; divisor esi=DAT_0092a274+1 at 0x4eabae);
- halved if stance bit 0 absent (`test [stance],0x1` 0x4eabf4 → sar 1 at 0x4eabfe);
- `+1` if `DAT_00985bc0 == owner` (0x4eac19-0x4eac1d);
- stored to `DAT_008f0d40[other]` (0x4eac27) and added to base+0xc4 (0x4eac62). Magnitudes (energy/8, divided by a global share count) match the observed 1..5 gains.

## Why it fits the dump facts
- 4eaa10 runs immediately AFTER 4e78e0 in every pass of the per-base round processor FUN_004f5a70: machine-verified call pairs 4e78e0@0x4f5ac8 → 4eaa10@0x4f5ad7 (pass 1), 0x4f5b3c → 0x4f5b4b (pass 2, DAT_008f0d64=1), 0x4f5c55 → 0x4f5c64 (pass 3, guarded by DAT_0068cbb4 != idx). Pseudocode: shard_012.c:24181, 24199, 24236. 4f5a70 has exactly 1 caller (shard_013.c:11570, per-base turn loop) → 4eaa10 runs per-base per round.
- 4e78e0 STORES (not adds) the 4-field vector, so each 4e78e0 run overwrites +0xc4; the last 4eaa10 add is the only live delta → stored +0xc4 = snapshot(+0xb4) + Σesi. Matches: snapshot matches reimplementation on 76/76; +0xc4 higher on the 11 bases with qualifying allied neighbors.
- 4eaa10 writes only +0xc4 (of the 4 fields); pseudocode for 4eaa10 has no write to +0xbc/+0xc0/+0xc8 (only reads +0xb4, shard_012.c:17967/17987). Matches "+0xbc/+0xc0 never change".
- 4eaa10's own walking store 0x4eafa1 `mov [eax+edx*1-0x4],edi` walks eax 0xfc→0x104 (0x4eaf74 `mov eax,0xfc`, 0x4eaf9c `cmp eax,0x108`), edx=DAT_008f0d60 — touches the bucket fields 0xfc..0x104, NOT 0xc4.

## Tail of 4e78e0 (after shift 0x4e8b50/loop end 0x4e8b54)
Window 0x4e8b56-0x4e8d35 (end = 0x4e78e0+5237): only stores are `[ebp-0x4]`, `[eax+0x48]` (0x4e8b60, 0x4e8d32), `[ebp-0x38]`. Callees: 0x507440 @0x4e8bf4 = popcount (fn.py: no memory writes) and 0x507410 @0x4e8c3e/0x4e8c79/0x4e8cb6/0x4e8cf1 = writes only its two out-params, which the disasm shows are stack slots (`lea edx,[ebp-0x54]; lea eax,[ebp-0x58]` etc., 0x4e8c34-0x4e8c3c). Nothing called after 0x4e8b54 touches base+0xc4.

## Candidates ruled out (record-array proof)
- Walking `[reg+reg*1-0x4]` sites in 4d6fb0(0x4d764c/5b), 4ef6d0(0x4f2442/51), 52bce0(0x52f9b8/c7), 538040(0x53a42a/39), 53cb20(0x53e5ba/c9), 544530(0x545a4b/5a), 57c550(0x57d63f/4e), 585720(0x58a97b/8a), 5a7970(0x5a8ce9/f8): ALL are C++ virtual-inheritance constructor vtable fixups — the `-0x4` store writes the adjustor delta (`lea edx,[eax-0x18]`/`[eax-0xa30]`) into vtable[-1], immediately after stores of .rdata vtable pointers (0x671c1c/0x671c30/0x671c28, e.g. 0x4d763d, 0x4f2417/23/33). Destination is the vtable slot array of a stack-constructed UI object (`lea esi,[ebp-0x32b8]` 0x4d75b0, `lea esi,[ebp-0x325c]` 0x4f23a6), not a game record. Pseudocode of 4ef6d0 has 0 hits for 0xc4.
- 469650(0x4697cd), 48dc20(0x48dcd4), 50aa60(0x50ab84): same vtable-delta pattern with vtables 0x6725ac/0x6725a4, 0x6762a0/0x676298, 0x678184/0x67817c; 469650/48dc20 are constructors (operator-new helper 0x64bda0 @0x469788; 48dc20 calls 469650 @0x48dc7a). Heap/stack UI objects.
- 5ba902(0x5ba9d6): part of a linear zero-clear run `[ecx+0x8c..0xd4]` (0x5ba982-0x5ba9ee) in a function whose pseudocode is a stack scratch builder (`int local_308[192]`); zero references to DAT_008f0d60/0x95da10/0x130/0x20bc in its pseudocode; a zero would also contradict the observed POSITIVE delta.
- 5cad98(0x5caebd): `mov [eax+0xc4],0` amid sibling stores at +0x184/+0x190/+0x194/+0x198 — offsets > 0x130 base stride → object larger than a base record; zeroes c4 (wrong sign).
- 5cb212(0x5cb48d): preceded by destructor helpers 0x5d5605/0x5d542d invoked on `[obj+0xc4]` (0x5cb471-0x5cb477) → +0xc4 is a pointer member being delete+null'd, not energy.
- 5cbcbb(0x5cbf8b): stores `[ebp+0x20]` (a ctor param) into `[obj+0xc4]` of a UI object (siblings +0x98/+0xf0, DAT_00993a04 UI global) — dialog constructor field init.
- 5cc99f(0x5cccbc): `*(int*)(in_ECX+0xc4)=param_1` thiscall setter (shard_016.c:92); sole caller FUN_005cbcbb (shard_016.c:13321) → UI member setter.
- Pipeline siblings 4e8d60, 4e92c0, 4e93f0, 4ef6d0, 4f26e0, 4ee410, 4f2ea0, 4f4a50, 4ebef0, 4f47f0, 4f4060, 4f41f0, 4f33f0, 4f34b0: pseudocode grep for 0xc4 = 0 hits each.
- 4f5a70's own income line `(&DAT_0094d650)[f*0x82f] += *(int*)(DAT_008f0d60+0x7e)` (shard_012.c:24241) targets the FACTION record energy (faction array 0x94d650, stride 0x20bc), not base+0xc4.
- Corpus sweep: `grep '0xc4) ='` over all shards finds writes only at shard_012.c:17952/18010 (4eaa10) and `in_ECX` UI-object thiscall sites (shard_016-020); no folded DAT_008f0e24 (=0x8f0d60+0xc4) references exist.

Status: stores + call order + tail = VERIFIED (read cited lines); semantic naming ("alliance energy share") = INFERRED.
