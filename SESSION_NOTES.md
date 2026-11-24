

Older sessions: `docs/sessions/sessions-334-335.md` (6 sessions: Session 334-chain2, Session 334-chain1, Session 334-chain3, Session 335-chain1, Session 335-chain3, Session 335-chain2). The split is by FILE POSITION, not by number — a moved id can be numerically newer than the first kept one, so grep the archive for an id before deciding it is still hot. The hot file starts at Session 336-chain1.

## Session 336-chain1 (2026-11-24) — M368: 0x2 = TREATY, 0x4 = TRUCE (V); truce < treaty < pact; the classifier is ordered EQUALITY

- **ACCEPT** `python3 -u scripts/m368_peace_ladder.py` -> **`PASS M368: 34/34`** `6f4b692777cc3549`
  (`evidence/m368_peace_ladder.txt:94`) x2; `scripts/m368_mutate.py` ->
  **`RUN PASS 32 mutants, NO-OP []`**, 34/34 gates covered (`evidence/m368_mutate.txt:36`).
- **THE DISCRIMINATING AXIS (behaviour, not labels)**: FUN_005537d0 pushes a bare mask to the writer
  FUN_00551a20 and the POSTER call 0x483470 immediately before it carries the key — 0x553c41/0x4 posts
  0x691144 `ENEMYTRUCE` (`:37`), 0x553f10/0x2 posts 0x691150 `ENEMYTREATY` (`:40`), 0x554165/0x1 has
  no poster (`:43`). A swapped reading needs the keys swapped.
- **LABELS** (`:65-72`): labels.txt element 643/644/645 = Truce/Treaty/Pact, consecutive after
  `Clock`. Bit value runs AGAINST friendship, so behaviour had to pin it.
- **ALGEBRA** (`:47-60`): `test bl,0x1 -> or ebx,0x2` (0x551abc) is the only pact->treaty upgrade in
  781,429 insns (reverse: 0). Both `and` masks are DECODED from bytes: peace `0xffee7faf` (@0x551a88)
  clears exactly {0x10,0x40,0x8000,0x10000,0x100000}, sparing every peace bit; war `0xfaeef378`
  (@0x551b17, under `test bl,0x10`) clears {1,2,4,...}.
- **CLASSIFIER QUALIFIED** (`:74-84`): 0x507975..0x50798f tests 0x1,0x2,0x4; je chains test->test->exit,
  jne 0x5079a1 = match, jmp 0x50799a = the mismatch store; 0 numeric opcodes -> EQUALITY, not the
  numeric rank M366's phrasing suggested. The WORD is retracted, the precedence is not.
- **CENSUS** (`:24-29`): 169 writer call sites; bare peace masks reaching one are exactly {1,2,4} —
  8 sites over exactly 4 hosts (listed in NAMED).
- **REVIEW #399 (3 P1 + 7 P2, all fixed; NAMED 248,819 -> 244,904 by rotation)**: masks now decoded
  from bytes, G1d pins 8/4, G2 ties the key to the POSTER call, PE section table replaces
  `vma-0x400000`, G5c/G6d/G6e added.
- **OPEN**: what FUN_0053f9f0 @0x53fcb3 (mask 0x2) and FUN_00523b20 @0x523f4c (0x1) transact.

## Session 336-chain2 — M369: relations bit 0x8 = COMMLINK (M364's AT WAR RETRACTED)

Static, zero box. ACCEPT `python3 -u scripts/m369_commlink.py` -> **`PASS M369: 23/23 gates digest 475fdceda961ef2d`** (`evidence/m369_commlink.txt:141`), re-run byte-identical; `scripts/m369_mutate.py` -> **39/39 killed** + 1 NO-OP (`evidence/m369_mutate.txt:47`).

- Builder FUN_004db480: 13 (id, offset) rows; row 1 = id 0x8 -> `DAT_00997b20+0xdac` -> element 875 -> labels.txt line **886 "Commlink"** (line = 11+elem; line 10 is the count 1089 — M367's line numbers are 1 low, its texts right).
- Vendetta block (FUN_00442320, 0x442cd3..0x442e42) READS mask 8 both directions — fac operands 0xa24 / 0xa28 — and every `jne` goes FORWARD to 0x442d7d (build the row); the both-zero fall-through (0x442d78) jumps to 0x442cf5 (next candidate); **0 parsed stores** into 0x94d448/0x94d468. Case 7 (0x442c01/0x442c1f) runs the same guard for a NON-war option.
- FUN_00551a20: `or ebx,0x80000108` (0x551b11) is gated by `test bl,0x10` (0x551abf). **M364 ev `:184` mislabels it `test 0x7`** — the 0x7 peace branch clears exactly 0x10|0x40|0x8000|0x10000|0x100000. All five branch tests enumerated, every `and` mask keeps bit 8, the 0x1f test is after the last store: mask 8 = 2 symmetric ORs (0x551be6/0x551c09, reload 0x551bea).
- 10 explicit bit-8 writes, 8 fns. Plain-8 (3): council FUN_00429950 0x42999d (both loops, pairs 1..7), commit FUN_004dadd0 0x4dae13, goody-pod FUN_0056df40 0x56f5ad (test 0x56f565 + jne past the call = set only when clear: **first contact**). War masks co-set it: 0x18, 0x80000008, 0x80000018, 0x88000008 x4.
- FUN_005076d0 pushes 0x10 on BOTH exits (0x507abc/0x507c6d), 0 push 0x8.

RETRACTION: M364's "0x8 = AT WAR" read a guard as the effect; the war bit is 0x10 (M366 V).
REVIEW #400: 10 findings, all fixed in-gate (clear-mask parse, whole-setter enumeration, exact pinned masks, store classifier, pair/direction, pod dominance, council containment, R4 on case 7, NAMED mutants, NEXT_PROMPT newline).
PITFALLS: shard_001.c has TWO identical `for (local_c = 1; local_c < 8; ...)` headers — match the two-line one; a gate must print FAIL, not crash.

## Session 336-chain3 (2026-11-24) — M370: the pref block's writers — 11 cells, 43 stores, 14 fns

- **ACCEPT** `python3 -u scripts/m370_pref_writers.py` -> **`PASS M370: 19/19`** digest
  `2fa7ea3c1bf74394` (`evidence/m370_pref_writers.txt:197`);
  `scripts/m370_mutate.py` **25/25 killed, NO-OP 0, coverage 19/19**
  (`evidence/m370_mutate.txt:30`).
- **CENSUS** (`:7,:16-20`): 85 refs over 76 dwords = 43 STORE / 39 READ / 3 BOUND. Text ==
  bytes only as (site,cell) PAIRS with a rel32 filter (a call's rel32 false-matches 0x92befc
  at 0x52732e). 5 materialisations, all cmp (2 on 0x92bde8 = M332's array end, 3 on 0x92bdfc
  = never a ds: operand).
- **NAMES, two-sided** (`:105-130`): 11 cells carry an INI key on BOTH the loader
  FUN_0058e7f0 and the writeback FUN_0058f0d0, same TEXT at DIFFERENT VAs: Difficulty,
  Faction, Map Type, Top Menu, Preferences, More Preferences, Announce, Rules, Semaphore,
  Time Controls, Customize.
- **PAIRING BY CALL SHAPE** (`:87-103`): 10x 6-push GetPrivateProfileString (key at call-2)
  + helper 0x58e760; backward the only injective direction (forward 2/11). The naive
  nearest-push law names `Laptop` at 0x92befc — killed (G4c).
- **THE OTHER WRITERS** (`:131-150`): 32 non-loader stores in 13 fns — 12 copy a 0x985a**
  bitmap (b8 x6, bc x3, c0, c4 x2), 5 flip ONE mirror bit, 4 write `x&0x1800000`, 5 are
  call returns, 4 computed, 2 CARRIED. The cell always takes a WHOLE-BITSET mirror; 0x58f0d0 flushes it.
- **NARROWED** M332: 0x92bde8 has TWO stores (0x57c7b0 in FUN_0057c550, also writes
  0x985aec), not one.
- **BOUNDARY** (`:156-160`): 0x92bf18..0x92bf30 is a separate 7-dword `Custom World` group
  (pointer sweep); the span ends at 0x92bf14.
- **OPEN**: 0x92bf0c serialises as `Semaphore` but is always `x&0x1800000` (bits 23/24 of
  0x985ae8) — packed field or reused name, INF; 0x92bdf0 unreferenced; 0x5f1394 chain-2.
- **PITFALL**: ghidra_out/index.csv ends FUN_00510730 at 0x51080b; four handler stores at
  0x510901..0x5109f8 need pad-delimited attribution, not the index (`:30-42`).

## Session 337-chain1 (2026-11-24) — B36: the faction-relations STATE MACHINE (10/10, 14 mutants, zero box)

- **ACCEPT** `python3 -u -m sim.relations` -> **`PASS B36: 10/10 gates  digest b20f5818dee2d861`** (`evidence/b36_relations.txt:82`), rerun byte-identical; `--b36` relays it. **Harness** `python3 -u scripts/b36_mutate.py` -> `RUN PASS 14 mutants, NO-OP []` (`evidence/b36_mutate.txt:16`).
- **FUN_00551a20 EXTRACTED AND RUN**: 161 insns, 8 stores. SIX blocks - five `test bl` predicates (0x7/0x1/0x10/0x17/0x1f) on the CURRENT ebx plus an **unconditional tail OR** at 0x551bc7. Extracting that tail as gated was the first defect: contact (mask 8) became a no-op and 2,369/40,960 parity pairs split.
- **TRANSITIONS** (`:39`): pact -> 0x3; truce after war -> 0x8000010c (commlink 0x8, 0x100 survive); war on 0x7|commlink -> 0x80000118; **combined 0x11 -> 0x8000011b** - the tail OR re-adds the upgraded mask AFTER the war clear. No action site sends a combined mask (M368 census), so it is REPRESENTABLE, not observed: declared, not gated.
- **The ladder ACCUMULATES** (truce then treaty = 0x6), so "the current relation" is the CLASSIFIER's precedence (1 then 2 then 4, ordered EQUALITY) - executable now, 65,536/65,536 byte pairs agree with the dump chain.
- **REVIEW #402** (4 P1 / 6 P2, all fixed in the instrument): G0 pairs stores with stored ops, G1 pins the SIX-block shape against a 10-entry op table, G2 adds a FLAT executor, G3 derives its expectations from the program, G5 counts the war-only class (2,563), G6 pins the 16-insn window + ZF semantics, G7 reads the poster strings from terran.exe via the PE table; 14 mutants. B18 stub carries full `path:line` (`--verify` rejects bare cites).
- **PITFALL**: a pre-state carrying 0x1 without 0x2 is NOT repaired by a write that lacks pact - the first G5 draft asserted the wrong invariant and collected 320 false violations. Scope "pact implies treaty" to the WRITE.
- No new retraction; M364's AT WAR (M369) and M368's ranked ladder stay retracted. NAMED rotated `## B18` (sha1 `da5bb857bde0`, `--verify` PASS).

## Session 337-chain2 (2026-11-24) — M371: the war-initiation hosts' 0x8 is COMMLINK; contact and vendetta are TWO bits

- **ACCEPT** `python3 -u scripts/m371_war_contact.py` -> **`PASS M371: 18/18 gates`** digest
  `4e82206112fe63ad` (`evidence/m371_war_contact.txt:128`); `scripts/m371_twice.py` byte-identical
  (`evidence/m371_twice.txt:4`); `scripts/m371_mutate.py` **27/27 killed** (`evidence/m371_mutate.txt:35`).
- **HOSTS** (`:8-25`): 10 setter calls in the four hosts; the 6 bit-8 rows are exactly
  {0x554389 0x80000008, 0x554426 0x88000008, 0x554e88 0x18, 0x55566e+0x555bb9 0x88000008,
  0x507653 0x80000018}. Roles: FUN_00554d10 MAJORATROCITY, FUN_00507460 AIDSTHEM/AIDSUS,
  FUN_005551e0 -> FUN_00554350 @0x5558cf.
- **SETTER LAW** (`:28-40`): `test bl,0x10`@0x551abf -> measured `or ebx,0x80000108`@0x551b11
  (31,8,0x100): any war request leaves as war+contact, both directions 0x551be6/0x551c09.
  16 callers request war with NO contact bit (14x0x10, 0x8010, 0x50), incl. both FUN_005076d0
  exits (`:64-68`).
- **PEACE** (`:35-40`): of three and-masks x2 sites only the 0x7 mask 0xffee7faf clears 0x10;
  none clears bit 8. Pure-8 writes = 4: new game 0x5a7c0a, council 0x42999d, commit 0x4dae13,
  pod 0x56f5ad (`:69-76`).
- **READS** (`:74-80`): `(rel&0x40018)==8`@0x555491, `(rel&0x18)==8`@0x555502; the atrocity
  host tests `al,0x10`@0x554e6b BEFORE writing 0x18.
- **NOUNS** (`:88-97`): id 8 -> labels.txt:886 "Commlink"; 0x10 -> :657 "Vendetta".
- **DECISION: two bits** — rival "8 = war companion" DEAD on three printed predictions (R1
  `:108-113`); pending masks measured 3x0x88000008 + 1x0x80000008 with no 0x10 (R2 `:115-118`);
  a stored 0x18 is the setter's implication (R3).
- **OPEN**: 0x88000008 bits 27/31 (INF); 24 carried sites (5 register masks, 19 not visible);
  the 0x100. **PITFALL**: pushes split by lea/shl — scan 14 insns back, require a 3-push run
  with one immediate (0x554426; MU21). `## M318` rotated to
  `docs/named-archive-m371-rows.md` (`evidence/m371_named_rotate.txt:1`).

## Session 337-chain3 — M372: 0x92bf0c = BIT-STRING slot, not a packed field

- **ACCEPT** `python3 -u scripts/m372_semaphore_cell.py` -> **`PASS M372: 8/8`** digest
  `b699a30c05573575` (`evidence/m372_semaphore_cell.txt:89`), re-run identical;
  `scripts/m372_mutate.py` **20/20 killed, 8/8 covered** (`evidence/m372_mutate.txt:34`).
- **CENSUS** (`:19`): 8 refs text==byte, 5 STORE/3 READ: loader 0x58ecc9; in-game
  0x4dc77c, 0x4dc8c3, 0x57cb1e, 0x57cc66; reads 0x48882e, 0x57c990 (restore),
  0x58f2fe (writeback).
- **THE KEY IS A BIT STRING** (`:28`): writeback pushes key 0x692848 `Semaphore` + flag=1;
  helper 0x58f030's flag!=0 arm loops bits 31..0, '1' set / '0' when `edi` or `esi<8` (min
  width 8): those constants reproduce the shipped `Semaphore=00000000`; the flag=0 decimal
  arm (0x64f980 radix 10) gives `0` — killed.
- **PARSE IS THE INVERSE** (`:46`): helper per cell from the nearest 0x5ea48x call:
  **5 base-2 (0x5ea493->0x628720), 6 base-16 (0x5ea484->0x62876b)**, counts GATED;
  round-trip exact.
- **NOT PACKED** (`:55`): all four stores mask `0x1800000`; the restore clears
  `~0x1800000` in 0x985ae8 then ORs the WHOLE cell (bits stay 23/24, 0 shifts).
  0x4dc77c/0x57cb1e=provably ZERO; 0x4dc8c3/0x57cc66 carry live 0x99aa38 bits 16/17.
- **NAME** (`:62`): 2 image-wide "Semaphore" strings, each referenced once (a push);
  0 data/table pointers -> no other consumer.
- **OCCUPANTS** (`:71`): bit23 read 0x59ef11+0x5a1446, bit24 0x5a1150; owners
  FUN_0059ec90 / FUN_005a0fa0 (new-game), owners GATED; nouns INF.
- **0x92bdf0** (`:78`): 0 refs, 0 address dwords even byte-unaligned across all sections;
  only sweep starts 0x92bf18.
- **REVIEW #404**: 10 findings fixed in-gate (sha1+size re-checked in G0; G1/G4 rows
  split; G3 counts+MU13; G5 image-wide; G6 owners+4 idioms; G7 scans split; cov=ACTUAL
  reds; cache regenerated).
- **PITFALLS**: objdump prints `DWORD PTR ds:0x..`, so `startswith("ds:")` misses a bitset
  load; a break-test ordered before the hit-test loses the reader.

## Session 338-chain2 (2026-11-24) — M374: Semaphore bits 23/24 = the two #RULES "Randomize" toggles

- **ACCEPT** `python3 -u scripts/m374_semaphore_bits.py` -> **`PASS M374: 23/23`** digest
  `705bd8cd7ed3f705` (`evidence/m374_semaphore_bits.txt:76`), re-run byte-identical;
  `scripts/m374_mutate.py` **20/20 killed, cov G1-G5, 1 declared NO-OP** (`evidence/m374_mutate.txt:23`).
- **CHAIN** (`:9-13,44`): `0x92bf0c` bits 23/24 <- `0x985ae8` <- `FUN_004dc5f0`:
  `test eax,0x10000/0x20000`@0x4dc88b/0x4dc89e -> `or ecx,0x800000/0x1000000`@0x4dc892/0x4dc8a5,
  eax = `ds:0x99aa38` (@0x4dc786); the cell store masks `0x1800000`@0x4dc8b7 -> `0x92bf0c`@0x4dc8c3.
- **RECORD** (`:15-21,47`): an 18-bit RULES word = `0x985ac4` bits 0..15 (16 legs, the `shr eax,0xb` leg
  is bit 11) + stage bits 16/17; the other path clears 23/24 with `0xfe7fffff`@0x4dc604; shipped
  INI `Semaphore=00000000` (loader alone sets neither bit).
- **NOUNS** (`:22-27`): `programs/Script.txt` `#RULES` (line 324) itemlist = 18 items; `#AIEDITOR`
  11 items = its 11 record bits (the item<->bit contract); items 17/18 = "Randomize faction leader
  personalities." / "Randomize faction leader social agendas." = bits 16/17.
- **READERS** (`:29-41`): bit23 0x59ef11 seeds FIVE fields 0x94d80c/10/14/18/1c (5 rand calls,
  5 stores) + the pairing arm 0x5a1446 (4 calls 0x551c40); bit24 0x5a1150 runs the 12-slot random
  assignment (zeroes 0xc dwords, stride 0x59c, 8 iterations).
- **KEYS** (`:43-49`): PE strings RULES/AIEDITOR/AIEDITOR2/SCENRULES at 0x68c824/c80c/c818/c82c;
  FUN_004dc5f0 pushes "RULES"@0x4dc6fb.
- **FOOTING REFINED**: the bits do NOT flow from the 0x41a9xx pack over `[0x8f0d60+0x38]`; both only
  SHARE the 0x99aa38 staging scratch (M179) - the writer's source is the RULES record.
- **OPEN**: what the 12 slots enumerate (INF: a 12-entry SE-choice/agenda grid); why the bits sit at
  23/24 rather than 0/1 of the cell (INF: turn-semaphore bits likely occupy 0..22).

## Session 338-chain1 — M373: the pending-vendetta consumer (STATIC 19/19, zero box)

- **ACCEPT**: `python3 -u scripts/m373_pending_vendetta.py` -> `PASS M373: 19/19 gates
  digest 4fd02c603e36c69c` (`evidence/m373_pending_vendetta.txt:165`), rerun byte-identical.
- **THE PICK'S PREMISE IS REFUTED.** `FUN_005551e0` (3,853 B, 1,167 insns) has **ZERO
  immediates of bit 27** (`:54`). Bit 27 is not a decision input there; the gate that
  actually governs the pending-vendetta pass is **bit 13 = 0x2000**.
- **THE CONSUMER** (`:15-19`): six touch points on bit 31 — `test eax,0x80000000`@0x55573c,
  `and eax,0x7fffffff`@0x555750 + store 0x555758 (own), `and ecx,0x7fffffff`@0x55578a +
  store 0x555792 (mirror), and `push 0x80000000`@0x5558da -> setter 0x551a20 @0x5558e1 (the
  ARM). The clear is conditional: `je 0x555809`@0x555741 (not pending) and `jne
  0x555809`@0x55574a (bit13 set) both jump to `and ah,0xdf`@0x555809 — a ONE-SHOT
  protector that scrubs bit13 in the same pass (`:35-43`).
- **BIT 27** is a sticky relations-word bit: 56 exact `0x08000000` immediates image-wide, 5
  of them word-form reads in 4 functions (0x5230f0 FUN_00522b70, 0x532a2c FUN_00531df0,
  0x54687b FUN_00546800, 0x5526ce+0x55278f FUN_005525d0) (`:48-55`).
- **SETTER ARITHMETIC** (`:58-74`): 14 masks, none clears bit 31 AND none clears bit 27;
  0x88000008 is the only mask that SETS bit 27. G4c pins the three sim masks to the dump's
  immediates (0xffee7faf/0xfaeef378/0xff7fffff), so G4a/G4b compute on measured bytes.
- **41 WORD STORES** (`:76-121`): 33 keep bit 31, **2 literal clears** (0x555758/0x555792),
  3 take a caller mask, 3 opaque. `draft claim retracted in-round`: I first read bit 27 as a
  one-write pulse; the executed replay shows it survives 0x80000008, 0x10 and 0x1 (`:139`).
- **THE SECOND CLEARER** (`:124-130`): FUN_005518f0 (`not edx`@0x55196e then AND) clears the
  caller's 3rd arg; FUN_00551cf0 does the same when its 4th arg is 0. 66 call sites, 46 decode a
  contiguous >=3-push run / 35 literal (20 undecoded and disclosed), only TWO carry bit 31: `0x9000ff48`@0x59f176 = a CLEAR inside
  FUN_0059ec90 (faction-elimination sweep), and `0xdd9bc3c0`@0x4da404 whose flag is the
  caller's ebx (`pop ebx`@0x4da3a8) — **OPEN**, not asserted away.
- **HARNESS** `python3 -u scripts/m373_mutate.py`: 16 mutants, each names its gate; MU11/MU12
  target G4c (the dump<->sim literal link), not G4a, because G4a computes on the sim.
- **PITFALLS**: (1) operand fields in the dump EXCLUDE the mnemonic — a regex written as
  `and ah,0xdf` never matches `by[a]`; (2) `push 0x..` has no comma, so a `,imm$` helper
  silently loses every arm; (3) a byte mask on `ah` names bit 13 — `test al,0x20`@0x5556a7 is
  bit 5 and a DIFFERENT guard (R3); (4) a mutation address must be the INSTRUCTION's address,
  not the call site's (`push`@0x59f16f, call@0x59f176).

## Session 338-chain3 — M375: the five unnamed bits are DEAL-PROTOCOL terms; 0x40 owns a 50-tick cell

- **ACCEPT** `python3 -u scripts/m375_relation_bits.py` -> **`PASS M375: 8/8`** `34bcef7ab64b9272`
  (`evidence/m375_relation_bits.txt:88`); re-run byte-identical (`evidence/m375_twice.txt:4`, sha1
  `aef3c85337bb3fe0`); `scripts/m375_mutate.py` **13/13 killed** (`evidence/m375_mutate.txt:16`).
  `:N` = an acceptance-file line. **CENSUS** (`:4-6`): 658 refs = 378 test / 253 load /
  **27 stores**; byte literals only +0/+1.
- **READERS** (`:10-19`): 0x800000 -> 0x53f863 only; 0x40 -> 0x508ebd/0x508ef9/0x547fd0;
  **0x8000 is read ONLY as a byte at +1** (`test BYTE [..+0x94d449],0x80` @0x53bbed; a grep for
  `94d448` misses it); 0x10000 -> 0x547367 + 2; 0x100000 -> 2.
- **SET VOCAB** (`:23-30`): 94 setter calls (76 push-run + 18 via-jcc); 0x800000 arrives ONLY as
  the bare mask 0x800000 (3 sites); 0x8000 only 0x8010; 0x10000 only 0x10004; 0x100000 once.
- **0x40 TIMER LAW** (`:34-43`): the only bit with a counter — 4/4 stores that leave 0x40 set arm
  `0x94d4c8=0x32`; upkeep 0x5552b6 decrements and clears 0x40 at 0 (`and al,0xbf` @0x5552d1); the
  peace mask never touches the cell.
- **0x800000** (`:46-53`): survives only a request with NO 0x17 bit; every status write clears bit
  23 at 0x551b98/0x551bbf and the tail OR cannot restore it. **PITFALL: 0x80000018 is bit 31 +
  war, NOT bit 23** (`& 0x800000 == 0`) — a lookalike.
- **ANCHORS** (`:56-67`): 9 mask+string pairs — 0x800000 'Sending TREATY ON', 0x1000000 'Sending
  TREATY OFF', 0x40 'Sending SET TREATY'. **0x100000** set once at the tail of FUN_0053f9f0 (the
  unit sweep, stride 0x34) that expels b's units from a's tiles.
- **LABELS** (`:70-74`): none of the five is a diplomacy id. **NOUNS**: 0x800000 = 'TREATY ON'
  (V, INF noun); 0x40 = 'SET TREATY' + 50-tick window (V, INF noun); 0x100000 = eviction
  grievance (INF); 0x8000/0x10000 = war/truce companions (OPEN). **OPEN**: 0x53bbed's role;
  0x5526b3 / 0x507d21 hosts; 0x4da404's 4th arg.

## Session 339-chain1 — B37: the treaty lifecycle; peace vs war split (review #408 hardened)

- **ACCEPT** `python3 -u -m sim.treaty` -> **`PASS B37: 8/8`** `5dd4119bd1882d1d` (`evidence/b37_treaty.txt:76`),
  twice byte-identical, same digest (`evidence/b37_twice.txt:2-3`); `scripts/b37_mutate.py`
  **14/14, NO-OP []** (`evidence/b37_mutate.txt:16`).
- **BLOCK** (`:1-14`): 10 insns `0x5552b6..0x5552d4`, `and al,0xbf`@0x5552d1, ONE exit 0x5552d9, so a zero cell stores NOTHING; the 409,000,318-B dump is pinned by sha256 `f67458fa25011f45` (`:13`).
- **ARMS** (`:15-33`): 11 refs = 4 arms + 3 reads + 3 write-backs + 1 lea (partition closed); the caller-mask
  arm's CONTROL FLOW is proved (`test cl,0x40` -> `je 0x551d64` PAST the arm, `:29`), not merely a nearby test.
- **PARITY/REPLAY** (`:35-49`): 2048 pairs 0 disagreements, expiry at tick 50; re-arm t30, status t40, expiry
  ONCE at t79.
- **PEACE vs WAR** (`:51-55`): `0xffee7faf & 0x40 = 0` but **`0xfaeef378 & 0x40 = 0x40`** (0x78 keeps bit 6):
  PEACE clears 0x40 so its lease expires as a **NULL write (49/49)**; WAR keeps it so its expiry is a **real
  clear (0/49)**; 0 of 11 cell refs inside FUN_00551a20. **CORRECTS M375's `evidence/m375_relation_bits.txt:41`
  presentation (a list, not a claim): 0xfaeef378 clears 0x10/0x1, NOT 0x40.**
- **TREATY ON** (`:57-61`): an exhaustive 256-mask sweep - 240/240 masks carrying a 0x17 bit clear 0x800000,
  the 16 that do not keep it; `0xbf & 0x800000 = 0`, so expiry cannot restore it.
- **REVIEW #408** (P1 was REAL) - R3's rival ran 1 tick so `arm_at=30` never fired; now the
  whole 120-turn horizon is replayed and scored per turn. Also fixed: G1 proves the guard DIRECTION, G5 swept
  all 256 masks, the census prints the measured arm count, MU1/MU2 mutate the parsed window, the dump's sha256 is pinned.
- **PITFALLS**: (1) `and al,0xbf` is a BYTE op; (2) a rival scored on END STATE can tie the truth - score the
  per-tick digest (first version 0/49); (3) "event then tick, one per turn" is policy, declared UNMODELED.

## Session 339-chain3 — M377: 0x8000 rides the WAR stamp, 0x10000 the first-contact truce

- **ACCEPT** `python3 -u scripts/m377_companion_bits.py` -> **`PASS M377: 8/8`** `c9e99e3b7e9f0a31`
  (`evidence/m377_companion_bits.txt:98`); re-run byte-identical (`evidence/m377_twice.txt`);
  `scripts/m377_mutate.py` **18/18 killed** (`evidence/m377_mutate.txt:20`). `:N` = a line of
  that evidence.
- **CARRIERS** (`:4-34`): 0x8000 <- the single mask 0x8010 @0x507d1a; 0x10000 <- 0x10004 at
  0x54d2e5 + 0x552680 (into FUN_00530640) and 0x5526b3 (the setter). 24 bare pushes of exactly
  0x8000/0x10000 image-wide, ALL into other callees.
- **HOSTS** (`:38-55`): FUN_00507ce0 is 80 B and only clears status&7 (FUN_005076d0(a,b,-1)
  @0x507d0d) then stamps 0x8010 — 0 essential edges AND `no entry->ret path skips the stamp` (a
  real unconditional test, not the zero-edge proxy). FUN_005525d0 stamps 0x10004 twice,
  FUN_00546800 once; its 4 essential edges are player-bit(a), 0x920434!=0, player-bit(b) and
  rel&0x8==0 (`and edx,0x8`@0x55261a, asserted by def-use); a bypass path DOES exist.
- **READERS** (`:56-61`): 0x8000 has THREE — `test DWORD,0x8020` @0x5380f2/0x541c5c and the byte
  test @0x53bbed. **M375's "0x8000 -> 1 reader" is RETRACTED** (its census took the imm from the
  whole operand, so a register test matched the `0x94d448` displacement). Lift readers require no
  clobbering write between load and test.
- **0x53bbed's ROLE** (`:62-63`): host FUN_0053bb90, only caller FUN_00545c50@0x545d4a. On the
  bit-set path it compares the pair scalar at 0x94e48c for (a,b) vs (b,a) @0x53bc1c; the skip path
  zeroes the flag. 0x547367 skips 'Sending TREATY OFF' x2 + NOPATIENCE(FRIEND) = "no treaty to
  cancel". All 27 direct stores are register-sourced: 0 provable clearer (`:90`).
- **HARDENED** by ai_review #410: +7 checks, MU15-MU18, 6 `sed`-repointed stubs restored.
- **PITFALLS**: (1) an objdump continuation line has NO third column; dropping it invents a
  phantom fall-through (0x507d06) and kills reachability; (2) `last_imm(whole operand)` matches the
  displacement — take the imm from the SOURCE; (3) a setter call's mask is push[-3].

## Session 339-chain2 — M376: the 0x92babc "12 slots" are alpha `#SOCIO`'s SE-effect matrix

- **ACCEPT** `python3 -u scripts/m376_socio_grid.py` -> **`PASS M376: 29/29`** `f22d2b46cc7e9507`
  (`evidence/m376_socio_grid.txt:115`; re-run byte-identical, `evidence/m376_twice.txt` sha1
  `ac23fc9540f77151`); `scripts/m376_mutate.py` **33/33 killed, cov G1-G4**
  (`evidence/m376_mutate.txt:36`). Static only, zero box.
- **REVIEW #409 (10 findings / 5 P1, all fixed in-gate)**: every constant is now read from an
  instruction or a file — header 0x24 = lea-disp - `mov esi,0x92ba98`; keyword capacity =
  `(0x927538-0x9270c0)/0x68`; record base = `mov esi,0x927b2c` - 0x59c (walk end 0x92a270);
  the BSS claim computes .data's file-backed VA end (0x6a9000) and MU26 patches a copy of the PE
  header to redden it; the rand noun is gated on both `call 0x64c6f0`/`cdq` legs; the reader's
  "same buffer" is gated on `push 0x997120` inside formatter 0x4237c0 plus the two call
  addresses; "8 records hit" reworded to the measured "8 records walked, 9 possible pairs". One
  dismissal: the cited `sha1 ac23fc9540f77151` is `sha1sum` of the FILE; the reviewer compared git
  blob ids (a different hash).
- **GEOMETRY** (a tiny insn emulator over 0x5a11ca..f3): cell = `0x92babc + 0xd4*a + 0x2c*b`;
  cell = **11 dwords**; 4 rows / 4 cells; row header 0x24 (name, 4 tech, 4 names).
- **SOURCE** `FUN_0057a070` parses alpha.txt `#SOCIO` (line 746 = the 11 keywords
  ECONOMY..RESEARCH, 748 = 4 categories, 749-764 = 16 choices): keywords -> 0x9270c0
  (0x68 B, count 0x927538, capacity 11), row names -> 0x92ba98+0xd4*o, the +/- tokens ->
  0x92babc. Column i = `strcmp(token,0x9270c0+i*0x68)`, count ADDED.
- **CONSUMER** (M374's bit24): unique (a,b) per faction in a 12-dword registry (`3a+b`), then
  the first weight > 0; stores category/choice at record **+0x584/+0x58c** (+ first-positive
  at +0x594). Derived: `0x9280b8-0x927590 = 0xB28 = 1*0x59c + 0x58c`, cross-checked against
  the reader's own 0x927b14/0x927b1c.
- **READER** 0x4a66d9 prints the pair: `[0x92ba98+d*0xd4]` category name,
  `[0x92baac+d*0xd4+e*4]` choice name (row+0x14), both appended — the agenda is TEXT.
- **NEGATIVES**: 0x92babc is BSS (raw .data ends 0x6a9000) => parser-built, not a .data table;
  rows 0..2 only, so Future Society (row 3) can never be an agenda; the 8th write 0x92a7fc is
  0x58c past the 8-record block end 0x92a270 (OPEN: 9-slot intent vs slack).
- **PITFALL**: per-faction field arrays are written `record[1] + field_off + i*0x59c`, so a
  "+0x584" field appears as the literal 0x927b14; 0x9280b8 looks like a base but is
  record[1]+0x58c. Do not read those literals as record bases.
- Rotated `## M286`/`## M287` VERBATIM -> `docs/named-archive-m376-rows{,2}.md` (sha1
  `25eb67cd987ee782`/`723e6eebf7c77ff8`) for the NAMED cap; both `--verify` PASS.

## Session 340-chain1 — M378: 0x800 = TREATY IN FORCE, 0x20000 = an outstanding treaty request

- **ACCEPT** `python3 -u scripts/m378_bit_nouns.py` -> **`PASS M378: 45/45`**
  `b841021cb7b0f4b8` (`evidence/m378_bit_nouns.txt:115`; re-run identical, sha1
  `da5742aa99cac132` both runs, `evidence/m378_twice.txt:2-3`); `scripts/m378_mutate.py`
  **17/17, NO-OP `[]`** (`evidence/m378_mutate.txt:19`). Zero box.
- **THE ARM B37 COULD NOT NAME** (0x5553e1..0x5553f9, FUN_005551e0): `and edx,0xfffdfbff` then
  `or edx,0x840` = **sets {0x800,0x40}, clears {0x20000,0x400}**, and the next instruction arms the
  50-tick lease `[pair+0x94d4c8]=0x32`. B37 proved 0x40 = "SET TREATY", so **0x800 is the durable
  TREATY-IN-FORCE flag**: this sign arm is its only setter; the PACT path (`test al,0x1`@0x555371,
  `and 0x20c00`) clears it, and M366's war mask `0xfaeef378` clears it.
- **0x20000, the other leg**: `jge 0x555405` on `[pair+0x94d820] >= 0` reaches a 2-insn arm that
  only `or eax,0x20000` on the SAME load (0x55536b); that field takes a **-1 sentinel** (0x55fce0)
  => INFERRED "a treaty request is OUTSTANDING" (both solve arms clear it).
- **0x400 is never asked alone**: all 5 field-inline tests carrying it (`0xc10 0xc11 0xc30 0x40c30`)
  carry 0x800 too; register-form readers `test ah,0x4`@0x5552ff (gates RNG 0x64c6f0) + 0x5468c7.
  **0x20000 has 0 direct readers** (MU13).
- **FUN_00552970 is NOT a 0x800 setter** (B37's lead): its `or al,0x40`@0x552ce4 sets 0x40, and the
  preceding store 0x552cca clears only 0x20. The window's two `and 0xfffff3ff` (0xc00) land on the
  **sibling field +0x94d468** - which has its own 0x400/0x800 bits.
- **CAP**: NAMED 247,824 -> 245,647 B; `## M366`+`## M319` rotated VERBATIM into
  `docs/named-archive-m378-rows.md` (19 rows=19 bullets, `--verify` PASS).
- **PITFALL**: a jcc's operand is one field, so `src()` (splits on comma) returns "" and a
  branch-target scan finds zero predecessors; use `imm2(i.ops)` for one-operand mnemonics.

## Session 340-chain2 — M379: record +0x594 has two AI readers; M376's "8th agenda write" is a pointer, not a store

- **ACCEPT** `python3 -u scripts/m379_field594.py` -> **`PASS M379: 31/31`** `256603d5fb70d2ad`
  (`evidence/m379_field594.txt:85`; x2 cmp-identical); harness
  **22/22** (`evidence/m379_mutate.txt:27`). Static only, zero box.
- **READERS** (positive-displacement sweep): exactly 2 loads of `[k*0x59c+0x927b24]` —
  `0x5a1eac` FUN_005a1ad0 (skip <0, index the local 11-effect vector, >0 adds the weight
  `[0x94e488+k*0x82f*4]`, <0 rejects) and `0x54696c` FUN_00546800 (eax spills to `[ebp+0xc]`,
  `[0x94d67c+..]`, negative -> message block 0x546983).
- **NO static +0x594 store** (mnemonic-complete classifier); the lone
  `[reg+0x594]` (0x4ffff2) is a `malloc(count*4)` heap array (`ds:0x997b20`, store 0x6146c7).
- **RETRACTION (M376 OPEN):** a control-flow interpreter runs the block's own bytes
  (0x5a1160..0x5a121c): **7 bodies, 6 back-edges, 35 stores in 0x9280b0..0x92a268, terminal
  edi 0x92a7fc**, terminated after 1413 steps. `ebx` starts at 1, is inc'd in the body and
  `cmp ebx,8 / jl` tests after it — **0x92a7fc is the terminal POINTER** (seed+7*0x59c),
  never an immediate, never stored. M376 used the bound constant as an iteration count.
- **EXTENT:** 8 records (8*0x59c = 0x2ce0 B): save/load pushes `0x2ce0`+`0x927590` twice;
  8 walks bound at 0x92a270; no static operand addresses a rec-8 field; 0x92a270 is itself a
  scalar global (`mov ds:0x92a270,eax`) -> no 9th slot; slot 0 (human) never seeded.
- **REVIEW #412 (10 findings / 2 P1 / 8 P2, all fixed in-gate):** printed digest + cmp instead
  of a file sha1; complete store classifier; CFG interpreter (+MU19/MU21 algorithm mutants);
  register/branch-target gates; enumerated extent; exe sha1 gated; rotate refuses stubs.
- **LIMIT (OPEN):** stack/heap-copy readers, split displacements (+0x400/+0x194) not excluded.
- Rotated `## M311`/`## M305` VERBATIM -> `docs/named-archive-m379-m311-m305-rows.md`
  (`--verify` PASS).

## Session 340-chain3 — M380: 0x94e48c is the MIGHTY/MEEK strength scalar; 2 of 27 rel rewrites DO drop a stamp

- **ACCEPT** `python3 -u scripts/m380_diplo_power.py` -> **`PASS M380: 7/7`** `5dfd436fe4093015`
  (`evidence/m380_diplo_power.txt:135`; re-run same, `evidence/m380_twice.txt` sha1
  `7455c8e2b5767fc9`); `scripts/m380_mutate.py` **23/23 killed** (`evidence/m380_mutate.txt:23`).
  All 3 M377 OPENs answered.
- **NOUN (OPEN #1)**: per-faction dword at block+0x105c (70 operands, 67R/3W; stride 0x82f dwords,
  base 0x94d430). Its one two-faction compare picks a string: `cmp
  field[a],field[b]`@0x54dcf0, `jle` -> 'MEEK' 0x690f20, else 'MIGHTY' 0x690f18 — a strength
  rating; composition OPEN. WRONGED/ENEMY next door gate on 0x426d60(rel,0x10).
- **BRANCH (OPEN #2)**: FUN_00545c50 is the hub on ds:0x920700; mode 2 -> 0x53a9c0
  (REJPACTMEEK), 3 -> 0x53bb90 (REJTREATYMEEK) = PACT/TREATY validators. Mode-3 arm @0x545d43:
  `call validator / test eax / jne tail / test edi / je tail / call 0x540390`, edi set once at
  0x545ce9 as `sete(ds:0x92077c==3)` — a refusal reaches 0x540390 only when status is 3;
  otherwise NO action, straight to the SEH tail.
- **ERASURE (OPEN #3) + RETRACTION**: M377's "0 provable clearer" was shape algebra over the
  store (opaque source register), not lineage. Def-use behind the 27 finds **2 provable
  droppers**: 0x551b1d `and edx,0xfaeef378` clears **0x10000** on the war mask (load @0x551b0b);
  0x555430 `and ah,0x7f` clears **0x8000** under `(0x985afc&0xf)==2p+1` (load @0x555427). Both
  RMW one pair dword, so the stamps are erasable. Other 25: 11 PRESERVE, 14 unknown.
- **PITFALLS**: (1) `[reg*4+0x94e48c]` is NOT a 4-byte array — all 19 carry the ×2095 scaler
  across several registers; a per-register marker match fails 10/19.
  (2) only `and` clears bit 15 and `or` never does — an `ah` blind spot invents 3 droppers.
  (3) a linear backward walk crosses blocks; stop at a `jmp`.
- Rotated `## M283` VERBATIM -> `docs/named-archive-m380-m283-rows.md` (sha1 `884865b3`).

## Session 341-chain3 — M381: bit 13 (0x2000) is a PEACE stamp with TWO setters; the strength one is strict > vs the peer's own scalar

`python3 -u scripts/m381_bit13_noun.py` -> **`PASS M381: 9/9 gates digest 2fa1a4100ec6f4f6`**
(`evidence/m381_bit13_noun.txt:149`), second run byte-identical; harness `scripts/m381_mutate.py` ->
**`RUN PASS 20 mutants, 0 unexpected`** (`evidence/m381_mutate.txt:22`). Static, zero box.

- **The comparison M380 left open is confirmed and asymmetric in the right way**: at 0x50392f the
  chain folds to 2095*ecx with **no `add esi`** (`:22`), the load is faction ecx's OWN
  `0x94e48c`, and `cmp eax,DWORD PTR [edi]` @0x503936/`jle 0x50396a` @0x503938 is a **strict `>`**
  against faction esi's own value (`:25-30`). The threshold is therefore **the peer's live
  MIGHTY/MEEK scalar** - no constant, no scale, no fraction; equality does NOT stamp.
- **The `+esi` contrast proves the reading**: +esi appears only in the two relations chains
  (0x5038f4 row edx, 0x50390f row ecx); the strength chain has none (`:24`). A pair-index reading
  (R4) dies on that measurement.
- **`[edi]` walks the field, one faction per iteration**: edi0 = 0x950548 = field(1), +0x20bc, stop
  0x95ea6c = field(8) -> **factions 1..7** (`:36-38`).
- **Guard**: two factions are skipped (`cmp esi,[ebp-8]/[ebp-4]`), a per-faction table byte at +7
  must equal esi, row([ebp-8],esi) must carry **PACT (0x1)**, row([ebp-4],esi) must be
  **peace+commlink (0x10 clear, 0x8 set)**, then the strict strength test -> `push 0x2000` ->
  `FUN_00551a20(esi,[ebp-4],0x2000)` (`:7-11`).
- **RETRACTION of the fuel for a "MEEK" noun**: FUN_00502cd0 stamps 0x2000 at a **second** site,
  0x506cf1, whose only guard is `test BYTE [row(edi,esi)],0x10 / jne` - **not at war** - with no
  0x94e48c operand in its 8-instruction window (`:12-13`). A strength-gap-only noun (R6) is refuted
  by that site. The flag is a standing **PEACE** marker; 0x50393d is the strength-conditioned leg.
- Both legs write **both rows**: all 6 dword AND masks in FUN_00551a20 preserve bit 13 and the
  unconditional tail ORs the mask at 0x551be6/0x551c09 (`:44-47`). "Weaker row only" (R5) dies.
- Follow-on: if esi's stat at +0x94f504+4*[ebp-4] has 0x800000, `FUN_00531b0([ebp-4],esi,+3)` - the
  **attitude delta** (adds to [a,b]+0x94d488, clamps to 0x14) (`:50-54`).
- Readers: **5 byte-form** `test ah,0x20` sites (0x54820d 0x5555a0 0x55563b 0x55572d 0x555747) and
  **1 dword-form** 0x4db30b (`and eax,0x2000` -> `FUN_006050d4`); 0x555747 guards the bit-31 clear
  `and eax,0x7fffffff` @0x555750, which **pins M373's protector to an instruction pair** (`:57-60`).
- Pitfall re-confirmed: a `94d448` dword grep cannot see bit 13 - it is read in the **byte +1**
  (`0x94d449`? no: `ah` = bits 8-15 of the loaded dword) form. `push 0x2000` also collides with
  0x200000 in flat greps; the census must read the immediate exactly.
- Host correction: the stamp lives in **FUN_00502cd0** (nearest `push ebp/mov ebp,esp`), not
  FUN_005024a0 - the 0x502a51/0x502a82 blocks have no frame and mislead a "last call site" read.

## Session 341-chain2 — M382: the 0xc00 cluster has 15 readers, not seven; 0x5468c7 asks bits 2|16

- ACCEPT `python3 -u scripts/m382_treaty_readers.py` -> **`PASS M382: 35/35`** `90cb89f84ce7feeb`
  (`evidence/m382_treaty_readers.txt:125`; re-run cmp-identical, `evidence/m382_twice.txt`); harness
  **24/24 killed** (`evidence/m382_mutate.txt:23`). Static only, zero box.
- **CENSUS** (`:9`,`:22`): 36 immediate-mask inline `test [..+0x94d448],imm` + 9 dynamic-mask; **5 pair**
  (0xc30, 0x40c30, 0xc30, 0xc10, 0xc11) and 2 that ask 0x800 alone (0x558cbd/0x56c153, mask 0x810).
  Register readers: 144 loads scanned (bounded 8-insn scan,
  stops on any write to the base reg), **8 meet 0xc00** (0x503727 0x546cde 0x5552ff 0x5567bb
  0x558b9d 0x559d04 0x560b77 0x56b652). Population = **15**; the shortlist named 7, of which 6 are readers.
- **RETRACTION (shortlist premise):** 0x5468c7 does NOT ask 0xc00 — `test al,0x4` (bit 2) then
  `test eax,0x10000` -> `[ebp-0x50]` at-war flag. The cluster reader in FUN_00546800 is 0x546cde
  (`test ah,0x8` = 0x800). The census, not the list, is the population.
- **THE ASK** (`:100`): every inline site asks `(pair_dword & mask) != 0` with mask ⊇ 0xc00 and per-caller
  extras {0x30, 0x40030, 0x10, 0x11}. Nonzero = "an accord standing exists" -> **veto on hostile action**
  (0x4ec9c3 bails 0x4ed94e; 0x5859ae bails 0x587078 only when it is ABSENT) or a
  **cooperative selector** (0x563165 unit target, 0x56a8a2 nearest-unit counter, 0x523a7c accept the choice).
- 0x5552ff is the **sole 0x400-only** reader and it gates M378's proposal roll (0x840 arm / 0x20000 arm /
  pact clear); 0x560b77 is the sole 0xc00-only (both bits) reader. The 15 span **8 host functions** (5 for the
  6 named cluster sites); AI hub FUN_0055f650 hosts 5 of 15 (`:107`).
- **LIMIT (OPEN):** the 9 dynamic-mask inline sites (`test [mem],reg`) are unread — a runtime mask could
  name 0xc00; register-through-copy and stack-copy readers are not walked.

## Session 341-chain3 — M383: 0x94e48c is a per-UNIT (offense+armor) sum; 12 of M380's 14 rewrites resolve

- **ACCEPT** `python3 -u scripts/m383_composition.py` -> **`PASS M383: 9/9`** `1d419b65323aec6c`
  (`evidence/m383_composition.txt:156`), two re-runs identical (`evidence/m383_twice.txt:4`);
  `scripts/m383_mutate.py` **29/29 killed** (`evidence/m383_mutate.txt:33`).
- **COMPOSITION (M380 OPEN #1 closed)**: the one ADDer 0x5579ea stores
  `field + ((A+B)*(C+6))>>3`, the term PARSED not inferred: A = FUN_005706c0, B =
  FUN_00570670, each `(byte[0x98ad88+0x25/0x26 + 52*type], faction)`; type =
  word[52*unit+0x933282] (`[ebp-8]` = 52*u, 13*4 measured); C = FUN_005ac0a0(unit,0,0).
  The scalar is the sum over the faction's units of (offense+armor) x rate — NOT a
  per-turn counter; the sibling +0x1060 takes A alone at the same rate. Bases
  0x92b950/0x92fd18 + the +0x25/+0x26 fields are M356's (nouns INFERRED); each indexes
  16*id, a negative entry falling back to a faction stat (0x94dc58 x 0x92a2e8/0x92a2dc).
- **THE 14 (M380 OPEN #2 closed to 12/14)**: must-dataflow over the function CFG resolves
  **12/14 to PRESERVE, 0 new droppers** (`:136`); totals 23 PRESERVE / 2 DROP / 2 unknown.
  The last 2 copy stack slots -0x50/-0x4c written from the field at 0x52affb/0x52b004,
  but over a CLOSED CFG (5 jump tables resolved from their `cmp/ja` bounds, 0x52ba1c:
  0x2a entries) the writer does NOT dominate the store.
- **PITFALLS**: (1) cdecl — the LAST push is arg0; reversing swaps table id with faction
  silently. (2) a `mov` to memory must route to the slot store BEFORE the register branch.
  (3) `or r,reg` preserves an IN bit but turns a provable 0 into unknown. (4) seed every
  register UNKNOWN at entry, or a join inherits another path's value.

## Session 342-chain6 — M388: slot 0's agenda pair has NO writer; the SE dialog stops at the live grid

- **ACCEPT** `python3 -u scripts/m388_agenda_slot0.py` -> **`PASS M388: 39/39`** `e03bfb351d33c64e`
  (`evidence/m388_agenda_slot0.txt:164`), two runs identical (`evidence/m388_twice.txt:3`);
  `scripts/m388_mutate.py` **23/23 killed** (`evidence/m388_mutate.txt:22`), kill = the gate's own FAIL line. Static only, zero box.
- **GEOMETRY** (`:12`,`:20`): the bit-24 randomizer's own imms — seed 0x9280b8, stride 0x59c,
  `mov ebx,0x1` / `cmp ebx,0x8` — give **7** records, bases 0x927b2c..0x929cd4, end 0x92a270;
  slot 0 = 0x927590 and its pair 0x927b14 (CAT +0x584) / 0x927b1c (CHOICE +0x58c) fall out of that
  arithmetic (`:21`), never authored. Block = 8*0x59c = the 0x2ce0 pushed at 0x596ea4 (`:19`).
- **WRITER = NONE** (`:23-34`), four censuses over 64,494 stores: (a) the five agenda displacements
  sit in exactly 3 stores (0x5bee99/0x5bf5cd/0x5c6173), all C++ ctors (vtable 0x67902c), none in a
  0x59c/0x927 context; (b) only 2 stores carry a disp32 inside the block (0x4dd996/0x57efe4, rec+0);
  (c) the folded form `[i*0x59c+0x927b14..20]` has 33 operands and **0 stores**; (d) 39 pointer
  seeds, none on the pair — the one naming slot 0 (0x579e9c) is skip-guarded (`:109`).
- **SE PATH STOPS AT THE GRID** (`:115-139`): dialog key handlers FUN_4b5530/FUN_4b55d0 (Enter 0xd /
  ESC 0x1b) call commit FUN_004b2570 — store `[eax+ecx*4+0x94d658]`, eax = faction*0x20bc, source
  `[faction_obj+0xcf8+cat*4]`; 19 body stores: **1** grid dword, 1 at the block's +0x20 counter, **0** in the agenda block. The grid is what the scorers
  COMPARE the agenda to (0x522df1/0x531fd8/0x555dd5), never copied from.
- **SENTINEL** (`:148-149`): choice = `rand%3 + 1` (1..3, never 0) and all 9 loads of +0x58c are
  0-tested (5) or name-formatted (4) => slot 0's (0,0) is a designed "no agenda" row, not a
  placeholder for anyone's SE choices. The pick's premise is REFUTED.
- **OPEN**: slot 0's OWNER (human vs unused id 0) — M43: the human is not block 0 in the 0x20bc
  family; the 0x2ce0 block is pushed to the save/load helpers 4x (2 name the block, 2 a stack twin, `:110`).
- **PITFALL**: the compiler folds `rec(i)+field` into `[i*0x59c+0x927b14]`, so a 0x584 displacement
  grep misses every reader; and 0x927b14 is ALSO a 4-stride base in two `lea`s. Derive from the walk.

## Session 342 — B38: the `#SOCIO` SE-effect matrix is executable (9/9, 12 mutants, zero box)
- **The grid.** `data/alpha.json` `#SOCIO` (19 records) -> 4 categories x 4 choices x 11 keyword
  columns; each entry = the signed count of the token's `+`/`-` prefix. Geometry recomputed from
  the dump: 0x350/0xd4 = 4 rows, 0xb0/0x2c = 4 cells, 0x2c/4 = 11 dwords, row = 0x24 header + 0xb0 (`evidence/b38_socio.txt:17-18`); 16 cells / 39 tokens / max |v| 5
  (`:39`). `python3 -u -m sim.socio` -> `PASS B38: 9/9 gates  digest e0bb2deb53ecb96c` (`:78`),
  re-run byte-identical.
- **Parity.** Both vectors M376 measured off its emulated parser are re-read from
  `evidence/m376_socio_grid.txt:42-43` and reproduced field for field — Police State
  `[0,-2,2,0,0,2,0,0,0,0,0]`, Free Market `[2,0,0,0,0,-5,0,-3,0,0,0]` (`evidence/b38_socio.txt:42`);
  4 empty cells at choice 0, 12 first-positive, Police State -> 2 (`:44`).
- **Application.** Police State/Planned/Power/Thought Control -> `[0,-4,1,0,4,4,2,0,2,-1,0]`
  (`:50`); all 256 settings agree with a dict reference; a category's delta = its choice's vector.
- **Consumer.** The bit-24 agenda triple (category, choice, signature): 12 add / 4 reject, the 4
  empty cells store -1 — M379's reader polarity reproduced (`:57-61`).
- **FINDING (negative, measured).** `0x92babc` is NOT an input to `0x94e48c`: 0 matrix operands in
  the 36-insn M383 chain around the store `0x5579ea` (`:65`); no SE->military wiring is modelled.
- **Harness.** `scripts/b38_mutate.py` -> `RUN PASS 12 mutants, NO-OP []`
  (`evidence/b38_mutate.txt:14`); per-gate mutant map in `## B38`.
- **PITFALLS**: (1) `#SOCIO` carries NO numbers — the effect is the PREFIX LENGTH ('-----' is -5),
  so a sign-only reading is silently wrong. (2) `mov edx,[ebx+0x94e48c]`@0x5579da is a LOAD; a
  store classifier keyed on "the address appears" counted two. (3) NAMED was 2.7 KB from FAIL, so
  B3+B4 were rotated verbatim first.
- **NEXT**: chain-1 pick (a) — the two peace writers outside `FUN_005537d0` (0x53fcb3 / 0x523f4c).

## Session 342-chain4 — M386: +0x94d820 is the X of a per-faction coordinate PAIR (+0x94d824 = Y), not a deadline/counter

- **ACCEPT** `python3 -u scripts/m386_marker_pair.py` -> **`PASS M386: 55/55`** `3e6d87261b7fe88e`
  (`evidence/m386_marker_pair.txt:146`; pinned table `401580f3c8ad292e` `:143`), re-run identical
  (`evidence/m386_twice.txt:2`); `scripts/m386_mutate.py` **15/15 killed** (`evidence/m386_mutate.txt:19`).
  Static only, zero box; round-1 review hardened G2-G7.
- **ANSWER**: the X half of a (x,y) PAIR at `0x94d448 + 0x20bc*f + 0x3d8` (Y at +0x3dc). 6 writers move both
  halves: 5 write -1 to BOTH (`or reg,-1`), 1 copies a UNIT x,y (0x558e0c/12 <- `movsx
  [..+0x95da10]`/`[..+0x95da12]`, stride 0x130); 1 lone X=-1 (0x55fce0) disables the marker (`:35-51`).
- **READERS = MAP ARITHMETIC** (`:69-75`): 0x557d29-4d computes `(Y*ds:0x692184 + (X>>1))*11*4+3` and reads
  byte +3 of the 0x2c tile array 0x92ae14; FUN_004e34f0 cmp's x/y vs ds:0x92a378/0x92a37c.
- **R1 DEADLINE refuted** (`:108-112`): 0 RMW on either half, 0 loads meeting ds:0x985afc within 6 insns; the
  real per-turn cell +0x80 (0x94d4c8) is load/dec/store 5 insns away. **R2/R3 refuted** (`:120`): 0 inc/dec/add,
  0 absolute forms, all 54 references base-register-relative.
- **M378 CORRECTION** (`:98`): the guard's base at 0x5553a4 is `ebx = 0x20bc*esi`, the PARTNER row, and a CFG cut
  proves 0x55531d DOMINATES it - jge 0x5553ac tests the partner's marker X, not the pair's. 0x20000
  stays an OUTSTANDING request INFERRED: 0 readers ON THE RELATIONS DWORD (`:125`, scanner control 373 tests),
  cleared by the exact `and 0xfffdfbff` (`:127`); its gate is the partner's marker.
- **INFERRED**: the marker = the faction's "unit-of-interest" tile (best unit by distance 0x8f0d34; HUD
  highlights the unit there; 0x5a5776 clears it). Which unit, and why the arm reads the PARTNER's, stay OPEN.
- **NAMED**: rotated settled `## M342` VERBATIM to `docs/named-archive-m342-rows.md` (verify PASS 9/9).

## Session 342-chain3 — M385: nine dynamic-mask sites resolved; no 0xc00, 0x400 at two (M382's sole-0x400 reader RETRACTED)

- **ACCEPT** `python3 -u scripts/m385_mask_walk.py` -> **`PASS M385: 44/44`** `0103209f070e60f7`
  (`evidence/m385_mask_walk.txt:140`), re-run identical (`evidence/m385_twice.txt`, cmp);
  `scripts/m385_mutate.py` **33/33 killed** (`evidence/m385_mutate.txt:36`). Static only.
- **DEF-USE** (`:17-26`): 4 LITERAL sites - 0x1000 @0x4dafcf (0x4db003/0x4db01f), 0x2000
  @0x4db035 (0x4db063/0x4db07f); the nearest def DOMINATES each site (no branch enters the
  def-site gap, `:35`).
- **STACK-COPY** (`:18-21`,`:37-52`): 4 sites take edi = `[ebp+8]` (`ret 0x4`, one literal
  push each). FUN_004dacc0: 4 callers push {0x20,0x2000000,0x400,0x40000}; FUN_004dabb0:
  0 call insns + 0 dword refs of 0x4dabb0 in 3,067,904 B -> **DEAD-INF** (2 sites excluded
  from the proven set).
- **REGISTER SITE** (`:59-82`): 0x574a66 masks `(0x0|0x10)|0x20` = **{0x20,0x30}**.
- **VERDICT** (`:86-95`): 7 PROVEN + 2 DEAD-INF; 0x800 at no PROVEN site; the 0xc00 pair at no
  PROVEN site; **0x400 asked ALONE at 0x4dacf7/0x4dad22** (push 0x400 @0x4db0aa, one test,
  two je paths). M382's "0x5552ff = sole 0x400 reader" is **RETRACTED**, counted against
  M382's own PASS evidence: 1+2 = 3, population 15 -> 17 (`:124-131`).
- **PITFALLS**: (1) arg = `[ebp+8]` for a `ret 0x4` callee. (2) A flat-dump boundary is
  neither the ebp prologue nor the last `ret` (0x4dad40 ends 0x4dadc2;
  FUN_004dadd0 is frameless). Entry = call-target UNION prologue,
  checked vs index.csv (`:112-120`). (3) `or al,imm` is a partial write: map al->eax.
  (4) M382's 0x94d448 count (653) calibrates the dword census.
- **REVIEW (10 findings)**: dominance-gated def tracer; caller decoder requires `ret 0x4`
  + one literal push; exe size asserted; "0x400 alone" == mask 0x400; population COUNTED
  from M382's evidence; second-derivation digest; rotate `--verify` full sha1.
- **OPEN**: FUN_004dabb0's entry mechanism (INF) and 0x551cf0's boolean-arg noun.

## Session 342-chain2 — M384: 0x400 has 7 setters; 5 of them hide behind a mask ARGUMENT

- **ACCEPT** `python3 -u scripts/m384_bit400_writer.py` -> **`PASS M384: 39/39`** `2c2e226fe292f0f6`
  (`evidence/m384_bit400_writer.txt:280`; re-run `cmp`-identical, `evidence/m384_twice.txt`);
  `scripts/m384_mutate.py` -> **23/23 killed**, baseline green (`evidence/m384_mutate.txt:26`). Static, zero box.
- **CENSUS** (`:10` `:16`): the pair dword has **42 writers** = 27 whole-dword `mov` at the
  displacement + 15 through a `lea r,[idx*4+0x94d448]` pointer (found by a 2-pass CFG
  dataflow, tags intersected at joins). **Zero** `and/or/xor/add` at the displacement --
  which is why every mask grep missed the writers.
- **THE SETTERS (7 sites, 7 functions)**: 2 hardcoded ORs -- `0x5534ae or ch,0x4`
  (FUN_00553350) and `0x555a6b or ah,0x4` -> store `0x555a6e` (FUN_005551e0) -- plus
  **5 mask-API callers**. `0x555a6e` sets 0x400 only when `(pair & 0xc00)==0` and bit 5 is
  clear (bits 1/5 select the 0x800 arm instead); FUN_00553350 sets it when P1 bit4 is
  clear and (531090()!=0 or bit5 of either side).
- **THE API (new)**: `FUN_00551a20(owner, other, mask)` ORs `mask` into the pair after
  `and 0xfaeef378` on its clear arm (complement `0x05110c87` carries bit 10 -> **0x400 is
  wiped there**) and always ORs `mask|0x80000108`; `FUN_00551cf0(owner, other, mask, set?)` sets or clears `~mask` on the same
  dword. Of **106** call sites (70 + 36) **95 masks resolve**: 5 pass 0x400 with set=1
  (0x41b2d2 0x4cd6f6 0x5470d6 0x59aef0 mask 0x400; 0x594cf7 0x420) and 2 clear it
  (0x4db11b 0xc20, 0x519bb5 0xc00). So the bit is written by **argument**, not by an
  inline constant -- the run context's "writer unfound" is now a population, and the
  M378 arms are the clear half of the same API.
- **PITFALLS**: (1) `mov [ebp+0x8]` vs `[ebp+8]` breaks a naive slot key -- normalise the
  offset. (2) Backward walks must follow `preds[i]`, not `i-1`: the next instruction in
  address order after a `jmp` is another path's code and leaked `or ah,0x8` into the
  0x555a6e set-mask (0xc00) until fixed. (3) `0x40020`/`0xc0020` are bits 18/19, NOT bit
  10 -- the grep that "found" them was an arithmetic error the instrument refuted.
- **OPEN / INTERSECTED**: 7 call-site masks are runtime (5 in the 0x4dadxx family, 2 load
  `[ebx+0x18]`), 4 passthrough. One of those is now concrete: `FUN_004dacc0` is a
  caller-mask SET/CLEAR gate (`test [pair],edi` -> `FUN_00551cf0(...,edi,1)` at 0x4dad05
  or `(...,edi,0)` at 0x4dad30) and M385 `:55` pushes **0x400** into it at 0x4db0aa -- so
  an 8th live 0x400 setter exists behind that argument. `0x52b9c7/0x52b9d0` remain M383's
  two stack-copy slots.

## Session 342-chain5 — M387: M380's last two rewrites split on an arg7 guard the store does not carry

- **ACCEPT** `python3 -u scripts/m387_last_two.py` -> **`PASS M387: 11/11`** `c0e46fd18f2fc313`
  (`evidence/m387_last_two.txt:111`), twice identical (`evidence/m387_twice.txt:10`);
  harness **20/20** (`evidence/m387_mutate.txt:24`); static, zero box.
- **BLOCKER, measured**: FUN_0052a720 (4859 B) closes over 5 jump tables, 0
  unresolved edges (`:12`); slots -0x50/-0x4c have ONE writer each (52affb/52b004, from the
  pair dword) and ONE reader (`:21-25`) - a verbatim dword copy.
- **GUARD 1 [ebp+0x8]**: 7 reads / 0 writes (`:43`), indexing BOTH 42-entry tables (`:13`).
  M383's non-dominance witness is predicate-INFEASIBLE (0x52a759 `jg` msg>0x30 AND 0x52b904
  msg==0x16 on one value, `:32`). Pinned: 1 of 53 messages reaches the store
  (`:49`); T1[0x16]=0x52a9e7, T2[0x16]=0x52af1b = the snapshot case.
- **GUARD 2 [ebp+0x1c]**: the snapshot sits behind `test eax,eax / je 0x52b1ee`
  (0x52af1b-0x52af30) and the store block reads [ebp+0x1c] 0 times (`:78-80`). The
  writer-skipping paths are exactly arg7==0 (0x52b1ee) or count==0 (0x52b88c, `:66-69`);
  count = (0x48+0x7ff)>>11 = 1 -> that leg is dead (`:74-75`).
- **VERDICT**: arg7!=0 -> PRESERVE (the stored dword IS the pair dword read); arg7==0 ->
  UNWRITTEN frame dword written into +0x94d448 (`:82-85`) - not a stamp drop. M383's 23/2/2
  becomes 23 PRESERVE + 2 DROP + 2 CONDITIONAL (preserve / uninit by leg), not 25/2.
- **RETRACTION**: M383's "the writer does NOT dominate" is not an instrument limit - the
  writer is genuinely skipped on a feasible path.
- **0x20 (M366)**: carried by the copy, tested 0 times here (`:89-91`) -> the noun stays INF.
- **PITFALLS**: `test X,X` compares with ZERO (folding X as its own second operand inverts
  every `jne`); keep the tracked set closed (eax/ax/[ebp-0x28]) or the loop state space
  explodes (3.3M steps); cdecl arg7 = [ebp+0x1c].
- **NEXT**: caller census for arg7==0 with msg 0x16 (is the UNINIT leg live?).

## Session 343-chain1 (2026-11-24) — B39: the relations API FAMILY — four entry points, TWO words

`python3 -u -m sim.relapi` -> **`PASS B39: 12/12 gates  digest 1c0a06e178521ef3`**
(`evidence/b39_relapi.txt:48`), re-run byte-identical; `python3 -u scripts/b39_mutate.py` ->
**`RUN PASS 12 mutants, NO-OP MU9`** (`evidence/b39_mutate.txt:13`). Static, zero box.

Pick (a) from B38 answered half: the peace host **`0x523f4c`** executes, and it is a three-call block
over TWO words. Field homes (`:29`): `0x551a20` -> A (`0x94d448`, 8 stores), `0x551cf0` -> A + the B37
lease `0x94d4c8`, `0x551c40` -> **B (`0x94d468`)**, `0x551d70` -> B. All four carry the `f*2095` row
scale and `0x94d468-0x94d448 = 0x20` = 8 dwords — B is a second slot of the same per-faction block,
not a mirror: `0x551c40`'s two OR stores take DIFFERENT partner registers (`eax`/`ecx`), i.e. both
directions in one call, while A is untouched.

The block (`:38`): `0x551a20(esi,edx,0x50)`, `0x551a20(esi,edi,0x1)`, `0x551c40(esi,edi,0x2000)`.
Guards read from the bytes (`:39`): `test al,0x1 / je 0x523f38`, `test eax,0x2000000 / jne 0x523f7a`,
`cmp esi,edi / je 0x523f60`. **Corrected in review:** `0x2000000` skips the block only when A-row bit0
is SET; bit0 CLEAR runs the writes and never consults it (`:42`). A self-pair skips only the `0x1` and
`0x2000` writes. The `test bl,0x20` arm of `0x551c40` ANDs `0xffffffbf` — it clears `0x40` and does
not set `0x20` (`:32`). The lease immediate `0x32` is read out of the dump, not hardcoded (`:32`).

New: M381's `0x2000` PEACE also lands on word B via `0x551c40`; PEACE is carried in BOTH words.
OPEN: the noun of the `0x1` write on A (M364's PACT candidate), every noun on B, B's readers.
Review: 11 findings (6 real gate defects — 2 vacuous rivals, hardcoded 0x32, uncensused symmetry,
unpinned extents, host guards not read from bytes) all fixed at head `1c0a06e1`, 12 mutants.
Pitfall: the dump's store operand usually has NO displacement — the field is folded into a register
by the preceding `lea`; a displacement grep alone reports zero stores for `0x551c40`/`0x551d70`.

## Session 343-chain4 — M391: `and 0xfaeef378` is 3 gated masks x 2 rows, not a blanket; the 0xc00 clears use the other API half

- **ACCEPT** `python3 -u scripts/m391_blanket_clear.py` -> **`PASS M391: 51/51`** `76148839fd85b66e`
  (`evidence/m391_blanket_clear.txt:134`, `cmp`-identical `evidence/m391_twice.txt`); harness
  **12/12** (`evidence/m391_mutate.txt:18`). Static, zero box.
- **M384 CORRECTED, not retracted**: "one arm ANDs 0xfaeef378" is **3 masks x 2 rows = 6 ANDs**
  (`:12-28`): 0x551a88/af `0xffee7faf`, 0x551b17/42 `0xfaeef378`, 0x551b98/bf `0xff7fffff`; each
  arm sits under a DIFFERENT mask-argument guard (`test bl,0x7` / `0x10` / `0x17`, `:29-40`). Only
  the WAR arm touches 0xc00; the treaty/truce arm PRESERVES it.
- **NOT EVERY 0xc00 CLEAR IS THERE** (`:41-50`): bit10 has **5** immediate-mask clearers in **2**
  functions -- 0x551b17 0x551b42 (FUN_00551a20) + 0x55538c `0xfffdf3ff`, 0x5553e7 0x5556e1
  `0xfffdfbff` (FUN_005551e0, M378's arm); bit11 has 3. All register RMWs off a `mov` load.
- **THE EXPLICIT CLEARS ARE THE OTHER HALF** (`:59-73`): both 0xc00-mask clears are
  `FUN_00551cf0(...,set=0)` -- 0x4db11b (0xc20), 0x519bb5 (0xc00) -- a `not`+`and reg,reg` with
  **zero immediates**. 0 of **65** resolved masks to FUN_00551a20 carry 0xc00, so all **24**
  WAR-arm callers drop the pair; the 5 setters use FUN_00551cf0 set=1.
- **SURVIVAL** (`:74-119`): WAR net `0xfa6e7328`, TRUCE net `0xff6e7faf` (0xc00 kept). Vectors
  (0x80000f18,0x10)->0x80000318, (,0x4)->0x80000f0c, (,0x11)->0x80000319; 0x80000108 survives.
- **PITFALLS**: the +0x20 sibling `0x94d468` has its own 2 ANDs in FUN_00551c40 (a field-blind scan
  reads them as pair clears); a whole-binary census over-counts (46 vs 6), scope to the body;
  `and r,imm` KEEPS every bit set in imm, so cleared = complement.
- **OPEN**: 3 opaque set=0 masks to FUN_00551cf0 (0x4dad30/0x4db02d/0x4db08d) could still name
  0xc00; 0x400/0x800 nouns stay INFERRED.
