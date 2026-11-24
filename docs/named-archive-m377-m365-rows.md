# NAMED.md `## M365` - ROTATED VERBATIM (byte-exact) by scripts/m377_named_rotate*.py

## M365 (s334-c3) — `0x94d5dc` = per-(fac,tgt) dword at record **+0x1ac**: zeroed by the writer, ++ on contact, read as a DEADLINE. ev `evidence/m365_pair_slot.txt:142`
| claim | ev | conf |
|---|---|---|
| 23 sites (8W/15R), 7 fns; 4 abs + 19 disp; 0 unclassified | `evidence/m365_pair_slot.txt:3-33` | V MU1,16,17,18 |
| FUN_004da2c0's 11 stores: 0x94d554 (head) + 5 slots 0x20 apart ending 0x94d5dc = block+0x1ac = mask+0x194 | `:35-41` | V MU8a,8,19 |
| 12 folded = 4*(fac*0x82f+tgt) B {0x20bc,4}={0x82f,1}; +0xa1c stride/+0xa20 unit swapped; 11 pointer | `:43-76` | V MU9,15,20,22,23,25 |
| writers: 2 zeros (only constant 0), 2 carried ebx, 3 `++`, 1 `+=2*byte` | `:78-89` | V MU2,24 |
| 0x94d5bc (+0x18c) moves with it 5/5 | `:91-105` | V MU3,4,21 |
| consumers: +round/50+1; 4 cmp; 4 add/lea | `:107-129` | V MU5,6,7 |
| RIVALS refuted: faction scalar, mask array, -1, aliased row | `:132-140` | V MU10,11,12,13 |
| INFERRED noun (treaty/contact AGE); key 0x54a373 = 4-byte `"a"` | `:130` | INF |
