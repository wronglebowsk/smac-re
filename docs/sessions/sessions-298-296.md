# Session notes archive — sessions 298-296

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-296-295.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 298 (2026-11-19, M321 review #324 hardening, STATIC, zero box; 7/7 + 22/22)

- Review #324 (10 findings, 5 P1) accepted 1-10. The P1s were decoration defects: G2 accepted the
  refresh pair by SET-ITERATION order and never measured its own 25 B; "zeroes +0x78/7c/80" was a
  shape match - the writes are `mov [eax+0x78],esi`, a REGISTER, so the zero was unproved; G2's site
  list iterated `ownersites.values()`, which after adding the image-wide census held 8 stores in 6
  fns, not the 2+2 owner rows -> gate reddened 1/7 at that head; fixed to `ownrows`.
- Hardening: order pinned by the PAIR tuple (`hits[0][0]==PAIR[0] and hits[1][0]==PAIR[1]`); pair
  completion MEASURED as byte distances 10-11 (`m321_memo_owners.txt:20`); encodings split per owner
  (`:21`); `je` pinned exactly (targets + call on fall-through); a real `is_zero()` proof (xor-self /
  sub-self / `mov r,0x0`) + base identity resolved FROM EACH WRITE's own address (`:34-36`);
  `back_def`'s vestigial `limit` removed, def locality printed (8 B back 3/3); G1's rival now derived
  from the printed histogram (top non-304 multiplier == 52, 646 vs 565, `:2`); G3 pins 7 emitter
  sites + exact label sets + `EMITTER==0x48f100`; G6 pins `0x4f43a0`/`cl,0x40`/chain text.
- RETRACTED in `NAMED ## M321` row 2: "2 are the a3 form" -> measured **1** (0x4f44a8; the 2nd owner
  store 0x4f455d is DWORD). NEW CROSS-CHECK: image-wide 8 index-fed memo stores in 6 functions, 4
  held by these owners (`:22`) - agrees with M319's 4.
- ACCEPT `python3 -u scripts/m321_memo_owners.py` -> `PASS m321: 7/7 gates` digest
  **f304cf871a971a3d** (`evidence/m321_memo_owners.txt:84,:92`), x2 byte-identical (supersedes
  s297's 562dcbbd12c27c8a, whose G2 was the unscoped version). HARNESS `python3 -u
  scripts/m321_mutate.py` -> **PASS 22/22** (`evidence/m321_mutate.txt:24`), x2 identical; MU4 NO-OP
  at `:5` (the cursor's `:15` cite was stale). MU14-MU22 added, sets MEASURED then declared:
  MU14/15/21->G2, MU16/17/22->G4, MU18->G6 (the F7 tripwire: the old "callee tests cl,0x40
  somewhere" gate stays GREEN on it, the pinned one reddens), MU19->G3, MU20->G1.
- Reconciled with main (M323 9c716f8): merge kept BOTH chains' sections; evidence/ at 20.8 MB [warn]
  - prune candidates next fire. NEXT: merge #324 on CI PASS; picks (vii)/(viii), B26 queued.

## Session 296-chain2 (2026-11-19, M324 CLOSED, STATIC: ROUND carried RAW)

- wt-chain2 @ milestone/m324 (main 9b09161); chain 1 owns main/sim/(vi)/(vii), #324 live.
- ANSWER: ROUND (0x985afc) carried RAW, NOT re-derived from YEAR. Codec FUN_00596850 header leg (R 59688a/W 596883) freads 0x31c=796B into 0x985ab8; blob+44=ROUND,+48=YEAR. m54b_clean.SAV: 12-B prefix (TERRAN\0+1a+ver86); @50=50 @54=2150 @44=67 @48=18 @310=9 (=live[985dbc] M108; M107 off-772 -> 784). sha16 74d0f44ab9b9290b==M302 live save; M106 kernel-copy law = M323's missing loader writer.
- block+220 carried: leg 596a91 dst 94d430 sz 105e0=8*20bc 8/8 (+sibs 596a6b/72); M320's whole block raw-carried too (rebuild untested). fac1436 leg 596ed6 dst 927590 sz 2ce0. g999fa4 NOT carried; W={442642,626fd7}: feed FUN_00442320 MAX-updates g999fa4=block[[this+0xa24]]+0x220 (imul 20bc, [ecx+94d650], cmp/jle 442625/2b); 2nd=64c460(0x99a01c)->64c360; feed 0 callers/0 AT (data-ptr OPEN).
- FALSIFIED re-derive: direct closure (opener+codec) 440, 0 writers; 4e0350 callers={514ecf@512b40,517e3a@516b80} pumps, outside; header entry-first (window branch-free); mode0 chain (xor 597efb->push 597f98->cmp/je); M272 inv9: -39 opener -> 50 faction fread. R1 RE-DERIVE/R2 REBUILD DEAD.
- ACCEPT `python3 -u scripts/m324_save_carry.py` -> **8/8** digest **700b4133f62bd714** (`evidence/m324_save_carry.txt:100`), rerun identical (`_rerun.txt:100`). HARNESS `python3 -u scripts/m324_mutate.py` -> **28/28+1 NO-OP** 5c3fa2bceb490009 (`evidence/m324_mutate.txt:29-30`); selftest 4/4 (`_selftest.txt:5`). REVIEW #326: 10/10 accepted (2P1+8P2); scope/pins strengthened, harness digest hashes payloads, MU19-27.
- TRAP: leg diamond pushes;je;call WR;jmp;call RD - walker skips jcc/jmp/twins, stops at add esp/foreign call (naive broke on je); ebx def-walk hit pop on EARLY-RET path; moffs32 mov lacks DWORD PTR.
- OPEN: g999fa4 noun/64c360; block+220 noun (year-like); feed arrival; byte-swap path. NEXT_PROMPT 12,188->11,999 B (M323 line VERBATIM -> §trim-s299 (a); M324 appended).
