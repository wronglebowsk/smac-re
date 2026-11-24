# NAMED.md `## M364` - ROTATED VERBATIM (byte-exact) by scripts/m385_named_rotate.py

## M364 (s334-chain2, STATIC 24/24) — the faction-relations bits have NOUNS: 0x1 = PACT, 0x8 = AT WAR (V, string-keyed); the other 11 are standing flags (INF). ev `evidence/m364_bitnouns.txt:131`
| claim | ev | conf |
|---|---|---|
| 13 ids = 11 single bits of rel[fac][tgt]+0x18 + 2 of +0x38; only 0x8/0x2000 repeat (directional A/B copies); the sync block's index chain EMULATES to fac*0x82f+tgt, x4 == the predicate's imul 0x20bc | `:3-22` | V MU1,2,3,4,18 |
| `FUN_00426d60(fac,tgt,mask)` = `(rel & mask)!=0`: 17 insns (window count), `imul 0x20bc`, 0 stores; 232 call sites, 214 constant, 18 unresolved | `:24-44,:46-88` | V MU5,6,7,ALG |
| 19 single-bit asks + 16 composites, each composite an OR of bits also asked alone (0x800 alone: never); 0x1 = 53 sites / 14 fns = the maximum | `:52-88,:175` | V MU8,9,12 |
| **0x1 = PACT**: the end-pact case block asks mask 1 -> "DONTHAVEPACT"/"REALLYENDPACT" -> `FUN_00530af0(...,1)`; ~~**0x8 = AT WAR**~~ **RETRACTED by M369: 0x8 = COMMLINK** — the declare-vendetta block only TESTS mask 8 (both directions) as a guard and stores nothing; see `## M369` | `:131-134,:172-174` | V MU10,11,ALG2 / M369 |
| writers: `test 0x7 -> or 0x1100000`, `test 0x10 -> or 0x8040` (`0x5518f0`); apply pushes 4 bulk masks — 0x1f SETS {1,2,4,8,10}, 0x1f89 SETS {1,8,0x400,0x1000}, 0x2043c20 SETS the other 6, 0xdd9bc3c0 CLEARS all 11 | `:177-194` | V MU13,19,14 |
| rivals refuted ON THE NUMBERS: 3-bit enum (16/19 asks outside 0x7), ordinals, "0x1 is vendetta" (0x1's block carries 0 vendetta keys), "one 16-bit field" (the parsed rows read 2 dwords 8 dwords apart) | `:202-206` | V MU16,15,17,20 |
| ACCEPT `python3 -u scripts/m364_bitnouns.py` -> 24/24 `f6d006d0281ac189` x2; harness 23/23 (22 gate mutants + MU0 NO-OP control; every gate mutated) | `evidence/m364_bitnouns.txt:208`, `evidence/m364_mutate.txt:25` | V MU0 |
| INF: nouns of 0x2,0x4,0x10,0x20,0x400,0x1000,0x2000,0x40000,0x2000000 and dword B's 0x8/0x2000 | - | INF |
