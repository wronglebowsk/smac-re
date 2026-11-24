# NAMED.md `## M366` + `## M319` - ROTATED VERBATIM (byte-exact) by scripts/m378_named_rotate.py

## M366 (s335-chain2, STATIC 29/29) — 0x10 = AT WAR / vendetta in force (V); 0x20 = the human-branch war record (INF). ev `evidence/m366_bitnouns.txt:597`
| claim | ev | conf |
|---|---|---|
| asks: 0x10 = 37 bare / 52 total in 16 fns; 0x20 = 18 bare / 30 total in 5 fns; both-bit masks 0x30/0x31/0x40c31; both are dword-A ids (0x8/0x2000 the only B twins) | `:13-23` | V MU1,2,3,4 |
| the ask decoder is sound: 214/232 sites are 3-push cdecl, 212 pop with `add esp,0xN` (N>=0xc), 2 inline-result sites named | `:28` | V MU5 |
| set-writer `FUN_00551a20` `test bl,0x10 -> and 0xfaeef378` clears {1,2,4,0x80,0x400,0x800,0x10000,0x100000,0x1000000,0x4000000} and `or 0x80000108` sets {0x8,0x100,0x80000000}; clear-writer `FUN_005518f0` `test dl,0x10 -> or 0x8040`; 0x20's rules drop B's 0xc00 / B's 0x40 | `:36-46` | V MU6,7,8,9,10,ALG2 |
| 0x10 is what the declare-vendetta path writes: `FUN_00507ce0` tests 0x7 inline -> `FUN_005076d0` -> setter with push 0x8010, and the routine pushes 0x10 on BOTH exits (0x507abc/0x507c71) while firing `VENDETTAWARNING`/`INCITED` (0x68d684/0x68d67c, bytes from the image) | `:545-556` | V MU11,12,13,14,ALG1 |
| 0x20 is SET by that same routine: `FUN_00551cf0`'s 4th arg at [ebp+0x14] selects the CLEAR (not/and) block by `je`, and the call site pushes 4 args with arg3=0x20, arg4=1 (0x507aad/0x507c52) | `:559-561` | V MU15,16 |
| read side: the instruction at 0x51ef55 IS `test <pair dword>,0x40020`; `jne` skips the mild load so SET keeps `ECONOMICLOSE2` ("tiny cubicle") over `ECONOMICLOSE` ("estate"); `FUN_00502cd0` asks 0x10 and carries PACTATTACKED/PACTATTACKING/VENDETTAREPORT; the naming menu is NOT among 0x20's 3 askers | `:566-574` | V MU17,18,19,20,21 |
| direct tests 62 (0x10) / 37 (0x20) / 3 (0x40020) reproduce M364's G6; 0x8010 is never a direct test (write mask); 7 writer calls pass 0x8 alone, 4 to the A-setter | `:579-585` | V MU22,23,24 |
| RIVALS refuted: 0x10 as a peace bit (its set-rule clears 1/2/4); 0x10 == 0x20 (different clear side-effects); 0x10 == 0x8 (20 vs 37 bare, 0x8 settable alone, implication one-way); 0x20 == 0x40000 (18 vs 3 bare) | `:588-596` | V MU25-29 |
| ACCEPT `python3 -u scripts/m366_bitnouns.py` -> 29/29 `c36db3d154a5ea1b` x2; harness 32/32 | `evidence/m366_bitnouns.txt:597`, `evidence/m366_mutate.txt:33` | V MU0 |
| INF: the noun WORD for 0x20 (inferred from the human branch + B-ladder + ending text); 0x80000000's role | - | INF |

## M319 (s293, STATIC, zero box; 7/7 + 14/14 scored + 1 NO-OP + selftest 4/4) - pick (v) CLOSED: the 8 unguarded memo sites are NOT guarded by their callers

| claim | evidence | conf |
|---|---|---|
| MEMO READS FEW + PRIVATE (operand-substring census, mnemonic shape pinned): exactly 6 read/test instrs image-wide (0x4e5155, 0x4eb6bf, 0x4efe83, 0x4f21e9, 0x4f5c41, 0x5ab74d; {mov:5,cmp:1}) in 5 funcs; readers(5) subset writers(15) - no read-only consumer could hold a hoist | `evidence/m319_guard_hoist.txt:67-68` G2/G5 | V (MU3,MU4,MU10,MU11) |
| NOT HOISTED: 8 sites -> 4 nameable owners, 8 distinct direct callers; only 1 caller reads the memo (FUN_004f5a70) and it OWNS a guarded site (0x4f5c4a, pinned), so its read is its OWN guard; non-owner memo-readers 0 | :69 G3 | V (MU2,MU3,MU5,MU10-MU13) |
| NOT DEAD, NO MEMO-GATED ARRIVAL: min 1 call/owner; 9 arrivals, 0/9 under a memo test; the FULL histogram {other-test:8, fallthrough-only:1} is pinned; the flag-setter walk spans EVERY flag-writing class (not cmp/test only); 0x4f3f7f has no range (M315 A10), callers not nameable | :70-71 G4/G6 | V (MU2,MU3,MU5,MU6,MU10-MU12,MU14) |
| CLASSIFIER NOT BLIND, KINDS PINNED PER ADDRESS: memo-direct exactly at 0x4eb6c7, memo-copy at 0x4efeaa/0x4f2201/0x4f5c4a, no memo edge at any of the 7 nameable unguarded stores | :72 G7 | V (MU1-MU3,MU5,MU7,MU9,MU11,MU13,MU15) |
| PAIR LAW IS ORDERED: pair-fed only when `call 0x4e8d60` PRECEDES `call 0x4e78e0` in the 17 B reach (presence alone would accept a reversed pair) | :15 G1 | V (MU1,MU2,MU7) |
| THUNK-FOLLOWING MEASURED INERT HERE: turning it off moves NO printed number (a harness NO-OP, not a bite - the census does not depend on it) | MU8 `evidence/m319_mutate.txt:9` | V (harness measurement) |
| ACCEPT 7/7 digest fb4e802dac1995a2 (hashes T1 partition+guard kinds, T2 refs+mnemonics, T3 callers, T4 per-call arrival, T5 edge labels); 3 accepted runs byte-identical, sha256 5ea00d859bf4503f (`evidence/m319_guard_hoist.txt:73`, `evidence/m319_guard_hoist_rerun2.txt:73`, `evidence/m319_guard_hoist_rerun3.txt:73`; re-derive by re-running the acceptance 3x and `diff`ing each stdout against the committed file); sweep 14/14 scored + 1/1 NO-OP (`evidence/m319_mutate.txt:17`); selftest 4/4 (`evidence/m319_mutate_selftest.txt:5`) | as cited | V |
| REVIEW ROUND #317 + the squash title: the title's 459f47e3178f439d / 12-12+1 are the PRE-REVIEW harness; the ACCEPT row is what held at merge head (same defect as M314's "20/20"). Governance note - adds no byte claim | - | lead |
| OPEN (one lane CLOSED by M321): what gates the 8 - `BYTE PTR [eax+0x38],0x40` x3 is now NAMED (base_array field 56 bit 6, gating the FUN_004f41f0 talent-request leg: `NAMED ## M321`, `evidence/m321_memo_owners.txt:30-34`); still unnamed: al,0x10; eax,0x1; ecx,eax. Also open: 0x4f3f7f callers; never live. Caveat: `guarded()` accepts via-copy on copy-liveness AT THE JCC (over-approximation) - the 4/8 split stands on agreement with M315 + the pinned kinds | - | lead |
