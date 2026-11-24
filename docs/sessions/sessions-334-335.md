# Session notes archive — sessions 334-335

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-333-333.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 334-chain2 (2026-11-24) — M364: the NOUNS of the 13 faction-relations bits — 0x1 = PACT, 0x8 = AT WAR (V); the other 11 are standing flags (INF)
- Lever: `FUN_00426d60(fac,tgt,mask)` = `(rel[fac][tgt] & mask) != 0` — 17 insns, `imul 0x20bc`, 0 stores.
  `python3 -u scripts/m364_bitnouns.py` -> **PASS M364: 24/24 gates** digest `f6d006d0281ac189`
  (`evidence/m364_bitnouns.txt:208`), rerun byte-identical; `scripts/m364_mutate.py` 23/23 (`evidence/m364_mutate.txt:25`).
- 232 call sites, 214 with a constant mask: 19 distinct single bits + 16 composites, each composite an OR of bits
  also asked alone (0x800 is the only bit never asked alone). Bit 0x1 is asked at 53 sites over 14 functions.
- NOUNS (V): 0x1 = PACT — the end-pact case block of the diplomacy menu asks mask 1 and branches to
  "DONTHAVEPACT"/"REALLYENDPACT" -> `FUN_00530af0(...,1)`; 0x8 = AT WAR — the declare-vendetta block asks mask 8,
  a CLEAR bit marks a faction you may declare on, and no candidate yields "DIPLONOVENDETTA". The two blocks
  share 0 literals. The natural rival "0x1 is vendetta" is refuted on that disjointness.
- Geometry: the 13 ids are 11 single bits of dword A (record +0x18) + 2 of dword B (+0x38); the only repeated
  positions (0x8, 0x2000) are A/B DIRECTIONAL copies — 4 of the 6 writers write (fac,tgt) and (tgt,fac).
- Co-set rules (`0x5518f0`): `test 0x7 -> or 0x1100000` (the 3-bit group), `test 0x10 -> or 0x8040`; the page's
  apply handler pushes 4 bulk masks: 0x1f = {1,2,4,8,10}, 0x1f89 = {1,8,0x400,0x1000}, 0x2043c20, 0xdd9bc3c0.
- PITFALL (new): a FUNCTION-level literal set cannot discriminate two bits asked by the same function — both
  rows came out carrying all four keys. The witness must be the enclosing `case` block; ALG2 mutates exactly
  that splitter and reddens G4a/G4b/G4c.
- INF/OPEN: nouns of 0x2, 0x4, 0x10, 0x20, 0x400, 0x1000, 0x2000, 0x40000, 0x2000000 and of dword B's 0x8/0x2000.
- NAMED headroom: rotated two settled blocks VERBATIM to `docs/named-archive-m364-rows.md`
  (`scripts/m364_named_rotate.py --verify` PASS, 2/2 stubs); NAMED 247,217 -> 245,296 B.
- REVIEW #393 (Strata, 10 findings / 3 P1) — all 10 FIXED, none dismissed: G1e now EMULATES the sync
  block's index chain instead of comparing constants; G7d reads the parsed dwords; the 0x1f bulk mask is
  printed (the old `v > 0xFF` cap hid it) and gated with SETS/CLEARS; the 17-insn count, the 53-site
  maximum, G5b, G1c and G6a's residual mnemonic all got named mutants (MU18/19/20 added); G7c now tests
  the rival ON THE KEYS; named_rotate's --verify matches stub headers by text, and the selector refuses
  blocks that are themselves stubs (two such picks were undone and replaced).

## Session 334-chain1 (2026-11-24) — M363: the four A/V audio callees touch the MIXER ONLY (0 pref-cell sites in the closure, 6 in the handler)

- **ACCEPT** `python3 -u scripts/m363_audio_callees.py` -> **`PASS  M363: 18/18 gates`
  `66b923f06f4e8866`** (`evidence/m363_audio_callees.txt:132`), rerun byte-identical;
  `scripts/m363_mutate.py` -> **`RUN PASS 20 mutants, NO-OP []`** (`evidence/m363_mutate.txt:38`).
- **ANSWER**: the four are mixer methods, not preference toggles. Their bodies hold ZERO
  absolute data operands and their 8-function closure (them + 0x4b9330/0x4b9370/0x4b9460/
  0x4b94a0) holds ZERO too; the cells have 121 sites/61 fns (0x985ab8) and 99/33 (0x985abc)
  across .text with 0 in the closure (`:11-53`).
- **SHAPE**: 0x4b8a60 = voice-slot START (byte flag slot+0x24 <- 1, play via buffer vtable
  +0x8c), 0x4b8af0 = STOP (flag <- 0, +0x14); index*0x18, bound `cmp [ebp+0x8],0xf`
  (16 slots), buffer ptr slot+0x2c (`:81-86`). 0x4b87f0/0x4b8820 = ONE guarded vtable call
  each into slot 0x60/0x64 of `[this+0x14]` (`:88-91`); no import-form call in the closure.
- **`this` = 0x8a7920** at all 6 handler sites (static sound object), 12 call sites total:
  6 in FUN_00493ff0, 6 in 5 mixer internals (`:64-79`). The cells are written by the HANDLER:
  6 sites, master-off = load both, `and ch,0xf3` / `and ah,0xbf`, store both (`:55-62`).
- **JUMP TABLE 0x4941ec** (image): 0x4b->0x494154 (master), 0x4c->0x494068, 0x4d->0x49400e,
  0x4e->0x4940c3. start/stop pair with the turn-ON/OFF row store (`mov edi,0x1` vs
  `xor ebx,ebx`) 4/4 (`:108-114`); the 0x4e row (flag 0x158b8) is NOT wired to the audio
  object — it calls 0x446490 + two vtable slots (`:116`).
- **QUALIFIED**: M361's "audio on/off (INFERRED)" — measured start/stop + enable/disable over
  a 16-slot voice table, no preference state anywhere in the leg.
- **Pitfall**: an `indirect_calls()` filter that keeps only `DWORD PTR [` makes an
  import-form gate unable to fail — MU12 found it (the closure gate was green on a state it
  could not see).
- NAMED: `## B27` rotated VERBATIM (docs/named-archive-b27-rows.md, sha1 `c327508bcd76`,
  `--verify` 10/10 claims), 247,217 -> 244,834 B; NEXT_PROMPT trimmed to the 12,000 fail.
- **Review #392 round (10 findings, 4 P1, all FIXED in place, no threshold moved)**: G2/G4's
  data window is now 0x800000..0xbfffff as the prose says and `absdata()` no longer drops
  memory-indirect call forms; G5's function count EXCLUDES the no-function sentinel (61/33, was
  62/34); G8 walks back to the first ecx KILL (12 insns, stops at a call) instead of 6; G9 pins
  the exact imul/lea register multisets; G10 requires the `,0x0` compare AND a branch PAST the
  call; G12 pins all four jump-table dwords (found by a new image mutant); G13's per-case
  store/load counts are ANDed in instead of overwritten; G13b pins the whole 0x4e call list.
  Four mutants added (MU17/G3, MU18/G9c, MU19/G13b, MU21/G12) — 20/20 RED, `[]`; the rival
  gate R is reddened by MU1. Digest moved `00277b42` -> `66b923f0` (measurement changed, answer
  unchanged).

## Session 334-chain3 (2026-11-24) — M365: 0x94d5dc = the relations record's third slot (block+0x1ac): zeroed by the writer, ticked on contact, consumed as a DEADLINE

- **ACCEPT** `python3 -u scripts/m365_pair_slot.py` -> **`PASS M365: 22/22 gates` `d1d567339ee8c5b2`**
  (`evidence/m365_pair_slot.txt:142`), re-run identical; `m365_mutate.py` -> **26/26 killed, NO-OP 0,
  cov 22/22** (`evidence/m365_mutate.txt:33`). Review #395 (10 findings) reworked the gate set:
  G2b now counts STORES only (11), G3c names fac/tgt (+0xa1c stride, +0xa20 unit), G4a pins the
  carried register and the 2x(signed byte) delta, G6c stops at a clobber/branch, R4 reads the two
  instructions it cites, the rotate verifier checks the NAMED stub, MU8 split MU8a/8.
- **CENSUS 23**: 8 W / 15 R, 7 fns; 4 abs + 19 base+disp; 0 unclassified (`:3-33`).
- **GEOMETRY**: slot = block 0x94d430 + **0x1ac** = mask 0x94d448 + 0x194 (101 dw). FUN_004da2c0's
  11 stores name six displacements: 0x94d554 (M165's "pair head", 8 B before) + five slots 0x20
  apart (0x94d55c..0x94d5dc); this slot is the LAST.
- **INDEX**: 12 folded = 4*(fac*0x82f+tgt) B ({0x20bc,4} = {0x82f,1}); 11 pointer sites.
- **WRITERS**: only constant = **0** (2 sites, bit-0x10 arm of FUN_00551a20, BOTH directions);
  2 carry ebx (4da604/4da6de); 3 `++`; 1 `+= 2*signed byte` (507fa4, before the 5518f0 clear).
- **PAIR / CONSUMERS**: 0x94d5bc (block+0x18c) same delta class + same base 5/5; deadlines =
  `value + round/50 + 1` (magic 0x51eb851f sar 4 = /50 proved on 0..5000; sibling /25 + 2);
  4 distinct cross-direction cmp; 4 add/lea terms.
- **CORRECTED (M165)**: "8-byte pair (5 pairs)" = ONE head dw + five 0x20 slots. **OPEN**: the
  NOUN (AGE is INFERRED); the key at 0x54a373 is the 4-byte string `"a"` in .data's diplomacy
  action-name table, not a label.
- **PITFALL**: a displacement can appear TWICE in one fn (4da2c0's two loops) — one-edit mutants
  leave the family intact; MU8/MU19 need two.
- NAMED 247,217 -> 243,805 B: M299/M300 rotated VERBATIM (sha1 5bde05a3/c74e41cb).

## Session 335-chain1 (2026-11-24) — B35: WHO calls the grant family — the founder + the new-game setup only, and the recorded births carry the FOUNDER's bit-1 signature

- **ACCEPT** `python3 -u -m sim.grantcall` -> **`PASS B35: 11/11 gates` `fa541d0a2445cacf`**
  (`evidence/b35_grantcall.txt:113`), re-run byte-identical; `scripts/b35_mutate.py` ->
  **18/18 killed, NO-OP `[]`** (`evidence/b35_mutate.txt:20`). Zero box.
- **CALLERS (dump, 781,429 insns)**: `call 0x4e47d0` = 3 sites — `0x4ccbdd` FUN_004cca50,
  `0x59d894` FUN_0059ce10, `0x5a01f8` FUN_0059ec90; `call 0x59ce10` = 1 site `0x5a1579`
  FUN_005a0fa0. Hosts agree with the index's `n_callers` 3/1, 0 unattributed (`:5-14`).
- **ITEM SITES**: FUN_0059ce10 = **11** `call 0x4e44f0` grants, items in address order
  `[6,3,7,27,8,4,6,3,6,3,27]`, 10/11 (set 0x1, base register) + ONE arg-order anomaly at
  `0x59d0a2` (base pushed first, flag last; the item is still the last push) (`:16-30`).
  FUN_004e47d0 = **10** `call 0x507410` mapper sites, 8 literal `[1,3,6,7,3,6,7,26]` + 2
  computed (`0x4e4d13`, `0x4e4d73`) (`:32-45`).
- **MAPPER LAW**: FUN_00507410 (17 insns) = byte `item>>3` (`sar eax,0x3`), mask
  `1<<(item&7)` (`and ecx,0x7`, `shl eax,cl`) — so item i IS bit i; the API's stride is
  COMPUTED (`lea [eax+eax*8]`, `lea [eax+ecx*2]`, `shl 4` = base*0x130), stores `or` at
  `0x4e4528` / `and` at `0x4e4546` (`:47-70`).
- **BIRTH SIGNATURE**: founder does `lea eax,[esi+0x95da9c]` -> `xor ecx,ecx` ->
  `mov DWORD PTR [eax],ecx` + `mov BYTE PTR [eax+0x4],cl` (FIVE bytes) then 7 ORs —
  register-indirect, so B34's `95da9c`-operand store census could not see the zero (`:72-80`).
- **PARITY**: 3 mid-run births — idx 19 `[1]` (r2), 20 `[]` (r2), 21 `[1,3]` (r9); founder
  signature `{1,3,6,7,26}` covers 3/3 (2 discriminating), the new-game set `{3,4,6,7,8,27}`
  1/3 (bit 1 unexplained on both non-vacuous rows) -> the FOUNDER fired, the 11-item path did
  not (`:82-96`). Mid-round: 6 changes = 4 OR (+2/+8/+3/+6) + 2 REPLACE ([1]->[4], [27]->[4]);
  0 birth-shaped, so the zero — not the bit value — is the separator (`:98-110`).
- **OPEN**: which of the founder's 3 sites fired per birth; why base 20 was born EMPTY
  (falsifies "item 1 is unconditional"); which of the 27 `0x4e44f0` callers added bits 3/6.
- **PITFALL (hit twice here)**: a comprehension that reuses an OUTER loop variable (`a`) for
  the address silently digests stale addresses — the second-pass digest read `e07b94e9`
  against `f1c53db1` and only G10 caught it; use `ins[i][0]` inside every comprehension.

## Session 335-chain3 (2026-11-24) — M367: the 13 relations labels ARE labels.txt lines (element = off/4, line = 10+element)
- **ACCEPT** `python3 -u scripts/m367_label_index.py` -> **`PASS M367: 27/27 gates` `a48d5dd630542166`**
  (`evidence/m367_label_index.txt:104`, digest `:105`, re-run identical); `m367_mutate.py` ->
  **30/30 killed, NO-OP 0, cov 27/27** (`evidence/m367_mutate.txt:36`).
- **THE INDEX (not an image string table)**: the loader `FUN_00614681` fopens `labels`+`.txt`
  (mode `rt`, 0x5ea673), `atoi`s ONE line into `0x997b24` = 1089, allocs `count*4` and fills
  `arr[i] = 0x5ea457()` (read line + arena strdup 0x6147ec). Each row loads ONE dword element
  through the VALIDATOR 0x61482f (24 insns, argument read by mov/cmp only).
- **THE MAPPING**: element i = labels.txt **line 10+i** (`#LABELS` line 8; line 9 = `1089` = the 1089
  lines that follow; element 0 = `Mission Year`; 3 lines past it unread).
- **THE TABLE** (id == bit; 11 plain / 2 high dword): 0x1 `Pact`, 0x2 `Treaty`, 0x4 `Truce`,
  0x8 `Commlink`, 0x10 `Vendetta`, 0x20 `I want revenge`, 0x400 `I shall betray`,
  0x1000 `I have infiltrator`, 0x2000 `I want to talk`, 0x40000 `I am atrocity victim`,
  0x2000000 `I have surrendered`; high 0x80000008 `Fight to the death`, 0x80002000 `Fix current
  status as permanent` (`:73-87`); title elem 866 = `Diplomacy for`.
- **ANCHOR (independent of file order)**: the status dam `0x4120c4` tests bit 0x1 of the SAME
  0x82f record -> the je fallthrough loads 0xa14 (`Pact`), its target 0xa10 (`Treaty`).
- **QUALIFIED (M364)**: bit 0x8's label reads **Commlink**, not "at war" (M364 read AT WAR off the
  vendetta case keys) -> a QUALIFICATION, not a retraction: both hold only if 0x8 gates contact (INF).
- **PITFALL**: 18 clamp sites, not 13 — split rows from statics on BOTH the trailing call
  (0x604fd2) AND the `ds:0x997b20` base.
- **REVIEW #398 (9 findings)**: added the alloc data-flow gate (G0d), the count's source (G0e),
  the je-branch gate (G4b), the mask equality (G5a), all-13-triples (G5c).

## Session 335-chain2 (2026-11-24) — M366: relation bits 0x10 / 0x20 — 0x10 = AT WAR (V), 0x20 = the human-branch war record (INF)

- **ACCEPT** `python3 -u scripts/m366_bitnouns.py` -> **`PASS M366: 29/29 gates` digest
  `c36db3d154a5ea1b`** (`evidence/m366_bitnouns.txt:597`, digest computed by the instrument),
  re-run byte-identical; `scripts/m366_mutate.py` -> **32/32** (31 named mutants + MU0,
  `evidence/m366_mutate.txt:33`). Static only, 0 box time.
- **CENSUS** (`:23`): 0x10 = 37 bare / 52 total / 16 fns; 0x20 = 18 bare / 30 total / 5 fns;
  0x20's askers are exactly {FUN_004f6030, FUN_00546800, FUN_0058fa40} — the naming MENU
  (FUN_00442320) is NOT among them (`:574`), which is why 0x20 gets no string noun. The decoder
  is gated (`:28`): 214/232 sites are 3-push cdecl, 212 pop `add esp,0xN`>=0xc, 2 inline-result.
- **WRITERS** (`:36-46`): `FUN_00551a20` `test bl,0x10` -> `and edx,0xfaeef378` (clears
  {1,2,4,0x80,0x400,0x800,0x10000,0x100000,0x1000000,0x4000000}) + `or ebx,0x80000108` (sets
  0x8|0x100|0x80000000); `FUN_005518f0` `test dl,0x10` -> `or 0x8040`.
- **WAR PATH** (`:545-561`): FUN_00507ce0 inlines the predicate on 0x7, calls FUN_005076d0,
  then SETs 0x8010; FUN_005076d0 sets 0x10 on both exits (0x507abc/0x507c71) and fires the .data
  keys 0x68d67c/0x68d684 = `INCITED` / `VENDETTAWARNING` (bytes read from the image). Its
  0x551cf0 call is `(_,_,0x20,1)`; FUN_00551cf0's 4th arg picks CLEAR by `je`, so 1 = SET.
- **READ SIDE** (`:566-573`): 0x51ef55 `test [pair],0x40020` + `jne` past the mild load ->
  SET keeps `ECONOMICLOSE2` ("tiny cubicle"), CLEAR `ECONOMICLOSE` ("country estate").
- **ANSWER**: 0x10 = at war / vendetta in force (V); 0x20 = the human-facing war record (INF).
- **RETRACTED mid-fire**: FUN_00551cf0/0x551d70 are 4-arg and the 4th arg selects SET vs CLEAR;
  reading them as clear-writers inverts the 0x20 story (caught before the first commit).
- **OPEN**: the noun WORD for 0x20; the role of 0x80000000 (set with 0x10).
