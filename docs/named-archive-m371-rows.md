# NAMED.md `## M318` - ROTATED VERBATIM (byte-exact) by scripts/m371_named_rotate.py

<!-- ## M318 sha1 3f2a4dfaf04a31685049d1e5864f516f48435e09 len 2070 -->
## M318 (s289, STATIC, zero box; 12/12+1 NO-OP) - pick (iv) ANSWERED: the selection-REFRESH PAIR = FUN_004e8d60 (selected-base UNIT-SUPPORT CENSUS) then FUN_004e78e0 (selected-base PANE REFRESH); both void(void), driven by the CURRENT selection

| claim | evidence | conf |
|---|---|---|
| PAIR: 12 back-to-back sites (gap 5) in 7 owners = M315's 12 memo sites; each follows a ds:0x68cbb4 store within 17 B of the SECOND call (worst = 17); the REFRESH tuple holds TARGETS | G2/G3 (`evidence/m318_refresh_pair.txt:6-35`) | V |
| A = UNIT-SUPPORT CENSUS: unit walk (count ds:0x985af0, stride 0x34), faction + home-base filter (unit+0x2e == ds:0x68cbb0); yield triad 4e6960/4e6d40/4e7070 switched on unit+0x26; over-capacity bit 0x10 (limit 94d684 clamp 0..7); foreign-tile bits 0x400000/0x200000 (4e3b50 owner, keyed 94d690 ==-3/<-3); 6-store bank 8f0c2c..8f0cc8 | C1/C2 (`:37-53,55-75`) | V (structure) / INFERRED (nouns) |
| B = PANE REFRESH: first call 4e63b0 scan-pool rebuild @4e78e9; rows from faction array 94dc34 into pane+0xbc..; dispatcher 4e75f0 x7; region bits 507410 x5 (first 0x1d); base flags +0x95da9c x5 halve unimproved rows; 15 selection reads; 8f0c68 countdown | C1/C3 (`:37-53,77-86`) | V (structure) / INFERRED (display) |
| KIND LAW SHARED: dispatcher 4e75f0 switch (cmp 3) = same triad + case-3 ds:0x8f0cc8=0, identical to A's inline switch | C4 (`:88-91`) | V |
| ACCEPT: `m318_refresh_pair.py` twice-equal, PRINTED digest 2e81643277e3a23b (`:100`, green `:102`); `m318_mutate.py` 17/17+1 NO-OP 39e6ce9f2334fe87 (`evidence/m318_mutate.txt:21`) | as cited | V |
| REVIEW #311 (3 P2 accepted): condition pins added (home-base cmp/je, 94d684 clamp chain, dispatcher ja + jump-table BYTES from the PE); G3 reach measured store->SECOND call (worst 17, was implicitly 22); digest now computed+printed by the instrument (was an external file hash). MU14-MU18 gate the fixes | `evidence/m318_mutate.txt:15-20` | V |
| OPEN: kinds' game words (resource triad candidate); unit+0x26; the 52-B array 98ada8 indexed by unit+0xa; pane+3 clamp byte | - | lead |

