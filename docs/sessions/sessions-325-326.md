# Session notes archive — sessions 325-326

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-323-324.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 325-chain2 (2026-11-24) — M347: the HoF page WRITER (M341's OPEN), answered (milestone/m346)

- **ANSWER:** `[screen+0x59f4]` is `+0x84` of the child container the HoF ctor
  0x44ba40 builds at screen+0x5970 (static singleton 0x748600 -> 0x74df70).
  Selector 0x62921c matches a child id (+0xa78) and stores it at this+0x84,
  else -1; init 0x629169 writes -2; the ctor never touches +0x84.
- **UPPER BOUND = 7** (M341's missing bound): the 7 children at screen+0xa5c
  get ids 1..7 — the loop counter is stored back AFTER `inc` (0x4493e1) and
  only then reloaded as the Init arg (0x4493f8); 0x5f9e85 writes arg2 to
  +0xa78. Both writers pass 1..7: block handler 0x44adc0 scans 7 blocks
  (0x983a10..0x984d34 / 0x2bc) and sends block+1; the open path 0x44b690 sends
  ds:0x91b5b4 = the SITE B cell [screen+0xa4c] (M312: block == player, 1..7).
- **SENTINEL:** -1/-2 are unconditional stores, unreachable from these two
  callers; the reader 0x44970f..0x449793 has 0 guards, so a sentinel would
  index BEFORE 0x983a10 (n=-1 -> 0x983498.., n=-2 -> 0x9831dc..).
- ACCEPT `python3 -u scripts/m347_page_writer.py` -> **`PASS M347: 12/12`**
  `3fadfd6e6d26e64c`, 2 runs diff-identical; `m347_mutate.py` **20/20**,
  NO-OP `[]`, uncovered `[]` (measured) (`evidence/m347_mutate.txt:22`).
- RIVALS: ctor-zero DEAD (0 stores); textual census 13 refs = 1 plain + 12
  `[r+r*4+0x59f4]` in 0x49xxxx (another array) DEAD; 0-based ids DEAD (pre-inc);
  capacity-32 DEAD (7 registered); receiver-blind DEAD (2 of 35 call sites).
- REVIEW #370 (10 findings, all fixed): rotation scope is B26 ONLY (the first
  version also moved `## M327`/`## M329`; both restored and `--verify` checks
  them), stub carries B26's own OPEN row; G4 gates the call SET, G5 pins
  inc/add/cmp, G6 the pushes, G7 the not-found branch, R2 the 0x44xxxx
  absence, the digest hashes MEASURED literals, harness computes coverage.
- UNKNOWN: which ids the other 33 callers of 0x6291e3 pass (other screens);
  whether a player value 0 can reach 0x44b71e.

## Session 325 (2026-11-24) — M346: who raises the build-finished ALERT (milestone/m346)

- **ACCEPT** `python3 -u scripts/m346_alert_raiser.py` -> **`PASS M346: 18/18 gates`** digest
  `ab4f0ca8123245bb`, two runs byte-identical (`evidence/m346_alert_raiser.txt:110`);
  `scripts/m346_mutate.py` -> **22/22**, NO-OP `[]` (`evidence/m346_mutate.txt:25`).
- **POST:** in FUN_004ef6d0 the block after the queue pop (`call 0x4ef5d0` @0x4f0f46) makes
  exactly 2 alert posts — `0x6265a2` kind 1 @0x4f0f78 with payload `[edi*48+0x984d38]`, and
  `0x626634` kind 2 @0x4f0f96 with payload `0x927894+1436*idx` (base record, stride 0x59c).
  The function holds 14 posts total, so the pair is the completion block's, not the function's.
  (First draft claimed "exactly 2 in the function"; G1 caught it and the gate was rewritten to
  the pop-anchored window instead of the threshold being loosened.)
- **TABLE:** both posters store payload -> `0x999ff4+4k`, owner -> `0x999fcc+4k`, zero the first
  byte of `0x99a01c+0x100k`, and bound `k<=9` — TEN fixed slots.
- **EXPANDER:** FUN_00625b20 reads 0x999fa4 (4x) and adds `0x99a01c+(k<<8)` (4x); the literal
  block at 0x69911c is `$` / `$NUMBER` / `$NUM` / `$HEX` / `$LINK<`.
- **DRAINER:** FUN_00636b1e clears slots 0/1/2 @0x63730e,15,1c, calls the modal runner 0x5f1394
  @0x63732d, then re-loops while `strlen(slot1) > 0x10`; 0 direct .text callers.
- **RETRACTION:** the footing's "0x985b10 = the alert channel/event queue" is WRONG — 0 refs in
  the five alert functions and in the post window, 0 stores in FUN_004ef6d0; it is the M96/M308
  player mask. No head/tail/count exists: the only first-byte writers are the 2 posters and the
  drainer.
- **Docs:** NAMED 247,825 B = 2,175 B headroom (M313 4,132 B rotated VERBATIM to
  `docs/named-archive-m313-rows.md`, sha1 `b674876b9a743893`, `scripts/m346_named_rotate.py
  --verify` PASS); M344 patched in place. SESSION_NOTES's earlier 247,182 was the pre-patch size.
- **REVIEW #369 (local Strata, 10 findings — 5 P1 / 5 P2):** all fixed, none dismissed. The
  P1s were real instrument defects: MU15 was a `PATCH_ALGO` hook that forced the gate red (now a
  real clear-base mutation, MU20), G1's post window was an arbitrary 0x4f0f40 anchor and did not
  verify the pop (now measured: `call 0x4ef5d0` @0x4f0f46, end 0x4f0f9b), and G13/G16 claimed
  more than they read (per-slot 5/2 read split with read-vs-store kinds; the "no queue" claim
  narrowed to the measured first-byte writer census, with 0x999f90's counters declared OPEN).
  G9 now also requires the `shl` register to be the `add` register (MU13), G7 reads the `jle`
  (MU9), G13 reads the backward jump (MU16), and fourth-round mutants MU1/MU2/MU7/MU8 pin the
  pop identity, the post count, the owner array and the poster's text base. The rotate script's
  idempotence check moved from the header line to the archive/stub body (finding 9).
- **STILL OPEN:** which .rdata template consumes slots 1/2 (and whether a facility completion
  ever reaches a template); the unit-id decoding (M68/M69 NEG_TYPE).

## Session 326 (2026-11-24) — M348: the template that consumes slots 1/2 is Script.txt, not .rdata

- **Question (from M346's OPEN):** which .rdata template consumes the completion block's slots
  1/2? **Answer:** none — the block registers the item label id and base name, then assembles a
  *script key* and hands it to the script-text dispatcher:
  `PRODUCEX` (0x68cfc4) + `Q` (0x68cfd0) / `G` (0x68cfd4) into 0x997120 (fallback `PRODUCE`
  0x68cfe8), then `call 0x48f100` @0x4f122a. `FUN_0048f100` sets slot 0 = `[0x8f0d60]+0x13`
  @0x48f20f and looks the key up in `programs/Script.txt`: `#PRODUCEXQ/XG` bodies read `$ITEM1`
  (slot 1) + `$NUM1`; `#PRODUCE2/3` read `$<M1:$FACTIONADJ2>` (slot 2). `.rdata` holds **0**
  `$<` templates (only the vocabulary `$LINK<` @0x673330).
- **Setters measured:** `FUN_006265a2(index, LABEL-ID)` resolves through table 0x997b28
  (`call 0x61482f`) then strcats; `FUN_00626634(index, LITERAL)` strcats directly; both clear the
  slot byte, `cmp k,0x9` + `jle`, return 3 above. (0x64b9e0 is **strcat**, not strcpy — it walks
  the destination to its NUL first.)
- **RETRACTION:** M346's "drainer" `FUN_00636b1e` is the multiplayer **Create Session** dialog —
  it draws `Session Name:` / `Maximum Players:` / `Session Password (Optional:)`
  (0x6998b0/c0/d4) and re-loops while `strlen(slot1) > 0x10` (session-name bound). The slot 0/1/2
  first-byte clears @0x63730e,15,1c are that dialog's field init. The bank itself is general:
  63 sites in 30 functions reference 0x99a01c, 7 sites build `k<<8+0x99a01c` (4 expander, 2
  setters, 1 modal @0x5f12ee).
- **Acceptance:** `python3 -u scripts/m348_slot_template.py` -> **`PASS M348: 12/12 gates`**
  digest `a3d46c017673526a`, two runs byte-identical (`evidence/m348_slot_template.txt:87`);
  harness `scripts/m348_mutate.py` -> **13/13**, NO-OP `[]` (`evidence/m348_mutate.txt:14`).
  Pitfall: the instrument originally wrote its evidence on EVERY run, including mutants — a
  mutant clobbered the acceptance file; it now refuses to write when `M348_PATCH_*` is set.
- **Docs:** NAMED 249,052 B = 948 B headroom; B28 (2,955 B), M343 (1,963 B), M345 (1,021 B),
  M344 (1,991 B) rotated VERBATIM (`scripts/m348_named_rotate.py --verify` PASS: sha1 bd196a95 /
  a7f9573e / 907d0705 / e7b59fa3). M346 + M344 patched in place (alert framing / drainer retraction). NEXT_PROMPT
  11.9 KB. Archive-name collisions hit twice (b28-rows, m343-rows already held other blocks) —
  check `docs/` before naming a rotation target.
- **Review #371 (local Strata, 10 findings — 3 P1 / 7 P2):** all fixed, none dismissed. The P1s
  were registry debt: the B28/M343/M345/M344 stubs carried `V` without their mutants (now each row
  names MU/ME), and M344's row cited M346 evidence for an M348 retraction (now cites
  `evidence/m348_slot_template.txt:63-69`). The P2s were gates claiming more than they read: G10 is
  no longer vacuous (exactly one `$` literal, `$LINK<` @0x673330), G7 asserts the five
  literal->0x997120 strcat triples, G5/G6 assert the edi/ebx roots, G9 gates XG and PRODUCE3, G11
  asserts the per-function distribution, G12 reads push 0x99a11c -> call 0x64c460 -> cmp eax,0x10,
  and the .rdata scan now reads the PE section table instead of hardcoded offsets.
