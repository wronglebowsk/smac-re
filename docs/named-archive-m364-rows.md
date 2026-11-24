# NAMED.md blocks ROTATED VERBATIM by `scripts/m364_named_rotate.py`
(byte-exact; each stub in NAMED.md carries the block's sha1 and byte count)

## M309 (s271, STATIC, zero box; mutation-tested) - FUN_0056d350 is the GOAL-list insert-or-max of the same 8380-B block record; its -1 6th argument is the entry's +0C OWNER dword, and -1 = unbound

| claim | evidence | conf |
|---|---|---|
| FUN_0056d350(rec,kind,prio,A,B,owner) indexes **0x94ee28 + 8380*rec** (chain -> (8380,0); a 2nd `imul r,r,0x20bc` lives outside it at 0x470d50) over **75 x 0x10** entries (2 back-edges, both `cmp r,0x4b`, both `add r,0x10`); fields **+0 short KIND / +2 short PRIO / +4 d / +8 d / +0C d**, derived from the store displacements + the param slot each source register def-walks to | `evidence/m309_goal_sink.txt:9-56` (S2 chain/S3 stores/S4 probe/S5 bounds) | V |
| It is the **GOAL** list because the binary says so: the `(A^B)&1` parity guard + `ds:0x985ae8` bit 0x1000 push **0x6914fc = "Bad GOAL"** (PE .data), while FUN_0056d480 pushes **0x691508 = "Bad SITE"**; the guard CANNOT skip the insert (both je -> 0x56d386, no ret between) | `evidence/m309_goal_sink.txt:95-121` (S8 guard/S9 strings) | V (game meaning of a GOAL: OPEN) |
| Same law as the SITE list: hit -> **+2 = max(old,prio)** and stores NOTHING else; miss -> evict by score (**1000** empty / **prio+100** / **20-prio**), strict `jle` (first index wins), no-candidate -> `jl 0x56d476` over a **store-free** epilogue past exactly the 5 insert stores | `evidence/m309_goal_sink.txt:57-94` (S6 found path/S7 eviction) | V |
| **owner (+0C)**: 1 writer (0x56d470) + 1 reader (0x559b3e) among all **65** operands naming the 100-entry block; reader signed, `jl 0x559b74` guards negatives, scaled **x304** (9x->19x-><<4) -> `test BYTE [edx+0x95da40],0x20`, gated on that entry's **+0 == 9** -> **-1 selects nothing (unbound owner)** | `evidence/m309_goal_sink.txt:196-244` (S12 census/S13 reader) | V (what the 304-B table at 0x95da40 is: OPEN) |
| arg6 census: **40** sites push 0xffffffff, **5** def-walk to **ds:0x68cbb0** (.data, 340 refs, exactly 6 stores, all in 0x4e3000-0x4f6000), **5 DECLARED unattributed**; the mirror (0x56d590) and the rebuild broadcast (0x56d6f8) both pass -1 | `evidence/m309_goal_sink.txt:128-195,245-262` (S11 callers/S14 global) | V (identity of ds:0x68cbb0: OPEN) |
| GOAL **+0 short has exactly 2 writers**: 0x56d45f (insert) and **0x470d5c = `mov WORD PTR [...+0x94ee28],0xffff` in FUN_00470b90** - the -1 free-slot sentinel writer M308 U2 asked for (SITE window still has none) | `evidence/m309_goal_sink.txt:209-211` (2 writers + 15 separate `imul r,r,0x20bc` in FUN_00470b90) | V |
| Gates are load-bearing: `scripts/m309_mutate.py` = **9/9** mutations (arg-reversal, census range, read/write polarity, param-seed loss, forward-jcc-as-loop, chain seed, blind-to-`ds:` stores, wrong window, empty dump) each reddening its named check | `evidence/m309_mutate.txt:23` | V |

## M323 (s295-chain2, STATIC, 13/13, 31/31+1) - ds:0x985afc=ROUND counter; year=round+2100

| claim | evidence | conf |
|---|---|---|
| 336 refs W5/T59/R272/A0; dw333/w1 (mov ax @59c18a)/b2; gaps 4f3a91/51da30 | G1/G6/G9 `evidence/m323_round_census.txt:523,528,531` | V MU1/MU18/MU19/MU23/MU31 |
| writers: 5a0fa0=0; 51f320=+1; 4e0350=max(1,g999fa4-g92bf68)+flow; 59ce10=rand{30,60,80} gated 985ac4.7 | G2/G3/G10 `:524-525,532,340-348` | V MU2/MU3/MU13/MU18/MU20/MU27/MU28/MU30 |
| year sole writer 51f54f=5b2c00(round+1)=arg+g92bf68(2100); chain pinned | G10/R1 `:532-533` | V MU10/MU13/MU17/MU30 |
| M320 ==0@59f1a0; M305 &3==bl(1)@51f711 def-set pinned; M317 >75@55840d; M177 age<16 | G5/G8 `:527,530,438,502` | V MU5/MU14/MU15/MU16/MU21/MU22/MU25/MU29 |
| live round=50/year=2150; rivals dead | G7/R1-R3 `:529,533-535` | V MU7/MU24; R1 MU10/MU17, R2 MU13/MU18/MU23, R3 MU12/MU13/MU23 |
| ACCEPT 13/13 digest 136841406b5bee5b x2 (`evidence/m323_round_census.txt:536`); harness 31/31+1 a25f4b5f2af8bb8a (`evidence/m323_mutate.txt:32`) | as cited | V |
| OPEN: rand-start noun; ~~g999fa4~~ cheat-parsed number (M325; writers M324); ~~save-carry~~ ANSWERED M324 (raw header blob); 4e0350 = EDITORYEAR cheat path (M325); resolver linear-static | - | lead |

