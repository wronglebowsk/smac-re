# Session notes archive — sessions 326-327

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-325-326.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 326-chain2 (2026-11-24) — M349: M68/M69 `NEG_TYPE` ANSWERED (milestone/m349)
- QUESTION: the queue stored **-3** for chooser entry 195 and **-6** for 196
  (`evidence/m68_key_run_attempt1.txt:12`, `evidence/m69_cursor2.jsonl:8`) — not one sentinel.
- ANSWER (static, `python3 -u scripts/m349_unit_id.py`): `FUN_004ef6d0` decodes queue slot 0 at
  **0x4ef88b** — `cmp ecx,0xffffffda` (-38) -> sentinel handler; `jge 0x4efa2c` -> FACILITY leg
  (item = head); `neg ecx` @0x4ef89f -> **item = -head = the UNIT TYPE**. Type >= 39 -> a
  2nd-table index (type-39); 34..37 -> the [ebp-0x20] band flag.
- Facility leg `cmp ebx,0x40 / jl 0x4efed1` -> id < 64 stamps; id >= 64 sets bit 2 @0x98adb8 and
  stamps only when that bit was previously clear.
- ONE bitmap, two legs: mapper `FUN_00507410` derived from its 17 insns = masks 7/7, `sar 3`,
  `shl eax,cl` -> byte `(id+(id>>31&7))>>3`, mask `1<<(id&7)`; both sites index 0x95da9c with a
  304 stride (unit leg ANDs @0x4ef97a, facility leg ORs @0x4f0ec0) - a unit type 3 aliases
  facility 3's bit but never writes it. Unit cost = `imul [0x984d44 + 48*type]` (stride 0x30).
- B31's recorded heads ARE 321,-2,-8,2,-3,-6 -> 4 unit types (2,8,3,6), 1 facility (2), 1 >=64.
  "Unit-encoded" is precise for the negatives; **`>31` heads are NOT unit ids**.
- RETRACTIONS: M68's "(195-192) -> -3" is a coincidence (196 would give -4, the trace says -6);
  B11's "-39 head sentinel" is wrong — the constant is **-38**.
- ACCEPT `PASS M349: 13/13 gates`, digest `fa2d81797551dae5`, two runs byte-identical
  (`evidence/m349_unit_id.txt:101-102`); harness `HARNESS PASS M349: 22/22 scored ... (covered
  13/13)` (`evidence/m349_mutate.txt:30`).
- REVIEW #372 (Strata, 10 findings): 9 fixed / 1 dismissed — mapper DERIVED from its own pinned
  insns, G4 pins all 30 rows, G9/G10 pin the 203 calls and the head sequence, R2 reads the traces,
  the facility latch is pinned test-then-set, cost/"per-player" narrowed to what is measured.
- STILL OPEN: which field of a unit DESIGN the chooser negates; which B31 loss is a raze vs a
  record change; whether a completion stamps.

## Session 327-chain3 (2026-11-24) — M350: the pref-block co-writers of 0x92bde8..0x92bf34

- **ACCEPT** `python3 -u scripts/m350_pref_cowriters.py` -> **`PASS M350: 6/6 gates`**, digests
  table `23794d22`, census `f9c2b0cc`, law `1680ba64`; x2 byte-identical (sha1 `44a184e3`,
  `m350_x2.txt:4`; digest `:16`); `m350_mutate.py` -> **15/15**, NO-OP green (`:36`).
- **EXTENT (the finding):** the block does NOT end at 0x92bf14. The loader fills 7 more dwords by
  POINTER (`mov esi,0x92bf18 ; call 0x5ea484 ; mov [esi],eax ; add esi,4 ; cmp esi,0x92bf34 ; jl`,
  key `Custom World` 0x6927c4); FUN_0058f0d0 re-reads the loop and joins with `, ` (0x689bbc). Both
  are 0-displacement forms — why a displacement census (M332's method) stopped at the last scalar;
  11 scalar cells, ONE loader store each (`:4-15`).
- **RETRACTION (#374 P1-2):** the earlier "loader 11/11 predecessors" was not a data-flow measure.
  Treating a call as breaking the def: **0/11 loader vs 28/33 co** (5 call-fed, `:160`) — the
  loader's value is the parse RETURN.
- **READS:** loader 18 of the image's 84 `call edi` sites, the 11 co-store fns 0, the writeback 8
  (its write side, INFERRED). 0x92befc's key is `Preferences` (0x69274c); `Laptop` (0x692704) is a
  default string.
- **CO-WRITERS:** 57 co-refs / 32 scalar co-stores in 14 scalar fns (10 store + 4 read-only) + 1
  array co-store; LAW 24 COMMIT / 9 TAIL-NONE (`:131`); 31 outside, 2 self-RMW (0x5a0ff2/6, one
  ALU); publisher = 3 direction- AND register-checked stores -> 0x985ab8/abc/c0.
- **REVIEWS:** #373 (closed, superseded) 10/10 fixed; #374 10/10 triaged — its P1s were real (read
  census image-wide, the pred measurement, publisher store direction); P2s fixed (EXTENT cite
  `:157`, key->parse INFERRED, ALU law at 1 op, writeback `add esi,4`, register-matched publisher).
  MU15 = pred mutant, MU14 = read-probe mutant.
- **Docs:** NAMED 243,972 B (M314 4,399 B VERBATIM -> `docs/named-archive-m350-rows.md`, sha1
  `decdd34b`, `--verify` PASS). OPEN: who sets ds:0x6926ec.

## Session 327 (2026-11-24) — B32: the UNIT leg RUN on the recorded trace (milestone/b32)

- ACCEPT `python3 -u -m sim.unitoracle` -> `PASS B32: 10/10 gates`, rows `e6875c63c8c2f911`,
  score `59b0b5e3647555b7`, leg `26d1c63c2861b182`, map `da981620c0e3ef18`
  (`evidence/b32_unitoracle.txt:54`), two runs byte-identical (same file, re-run `diff` clean);
  harness `python3 -u scripts/b32_mutate.py` -> `PASS HARNESS B32: 13/13` `155781675e5086a1`
  (`evidence/b32_mutate.txt:16`).
- B32 attaches M349's decode to B31's oracle. Heads `[321,-2,-8,2,-3,-6]` = 4 UNIT / 1 FACILITY /
  1 BIGITEM (`:43`). Scored on the BEFORE-sample (pre-pop) head PER LEG: 4/4 unit heads gain
  exactly the mapper bit (-2->bit2, -8->bit8, -3->bit3, -6->bit6); 0/2 facility-range heads do;
  B31's bulk rule reproduces 0/6 on the same rows (`:25`, `:44`). B31's 0 was an undeclared
  decode, not a refutation of the stamp.
- The AFTER-sample (post-pop) head scores 0/6 (`:28`): the stamp reads the head BEFORE the pop,
  so M344's spend->stamp->pop order now holds on all six recorded rows, not only B31's 2-deep
  fixture.
- Write replayed: before window OR mask == the recorded after window at 4/4 unit boundaries and
  only the mapper byte moves (`:35-39`, `:47`). Virgin Soil: facility 2 predicts
  `04 00 00 08 00`, the record holds `10 00 00 00 00`; head 321 maps to byte 40, off the 8-byte
  map (1 refusal) (`:34`, `:37`, `:48`). The 2 losses sit on the 2 non-unit rows only (`:49`).
- QUALIFIES `## B31` (its OPEN "unit-id decoding" is closed by M349 + this run) and `## B30`
  (the facility setter stays UNVERIFIED and is now CONTRASTED: side-by-side unit completions DO
  stamp). Pitfall: a new module's `HEAD_OFF` is dead code if it reads through `fa.head_of` - the
  head-offset mutant scored green until the module unpacked its own constant.
