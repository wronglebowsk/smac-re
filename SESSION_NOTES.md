

Older sessions: `docs/sessions/sessions-320-321.md` (3 sessions: Session 320-chain2, Session 321-chain2, Session 321-chain1). The split is by FILE POSITION, not by number — a moved id can be numerically newer than the first kept one, so grep the archive for an id before deciding it is still hot. The hot file starts at Session 322-chain2.

## Session 322-chain2 (2026-11-24) — M341 merge land (PR #361)

- **UNBLOCKED, MERGED:** the "zero CI runs" blocker was the PR, not the workflow —
  GitHub schedules no `pull_request` run while `mergeable_state=dirty`. `git merge origin/main`
  (a0aa8fc, #362's 34 restored NAMED blocks) kept BOTH 321 sections and auto-merged
  NAMED/NEXT_PROMPT; one conflict (SESSION_NOTES, both appended at EOF) resolved keep-both.
- **VERIFIED at the branch head `179fef5`:** `gate.py --base origin/main` -> `GATE GREEN` (11 passes,
  1 branch-name warning — the documented `milestone/M341` vs `milestone/<id>` warn line, noise);
  `review_lint --id M341` -> PASS (8 V rows); `m341_hof_window.py` -> `PASS M341: 11/11 gates`,
  `digest=1cfdea39295dadce`, `table_sha256=b5820ac99801f8c4`, stdout byte-identical to
  `evidence/m341_hof_window.txt:45-58` (gates `:1-44`, harness `evidence/m341_mutate.txt:21`);
  `git diff 446958b 179fef5 -- scripts/m341_* evidence/m341_*` empty (same instrument bytes
  as the measured head). NOTE both printed names are **truncated sha256** — `m341_hof_window.py:520,524`
  take `.hexdigest()[:16]`, so "sha256" here means the first 16 hex of it, not a 64-char digest.
- **CI:** `gate` PASS 18 s, run 45324343569 (job 138210194052) on 179fef5 — the first run for a
  head newer than 03:38Z. The squash commit's tree IS the gated tree:
  `git rev-parse 179fef5^{tree} 185c394^{tree}` -> both `702938a3f8bef770f822c2c0e2db157deeb12276`.
  Merged `--squash` as **185c394**.
- **MAIN CHECK** (`git show origin/main:NAMED.md | grep -c '^## '` / `grep -c '^## M341'` / `wc -c`):
  NAMED 111 blocks (110 pre-merge + `## M341`), 248,127 B, `## M338` stub intact, no block lost
  (`comm -23` of main's block titles vs the merged file -> empty).
- PITFALL: `milestone.py merge` ends with `gh pr merge --delete-branch`, which dies on
  `'main' is already used by worktree at /home/paul/reverse/smac` — the merge itself SUCCEEDS
  server-side; verify with `gh pr view <n> --json mergeCommit,mergedAt` and leave the branch
  (older milestone/* branches linger anyway).
- **ABSENCE CLAIM is a LEAD, not a gate result:** `0x59f4 has NO named writer` is NAMED M341's
  OPEN row (kind `lead`, no mutant); the V half — "the only direct ref in 781,379 insns is the load
  0x44970f, 12 indexed hits are a different array" — names MU8. Byte-identity above is asserted
  against the committed file (`diff <(...) evidence/m341_hof_window.txt` -> empty), so it is
  reproducible from the repo, not from a transcript.

## Session 322-chain1 (2026-11-24) — M342: pick (x9) the COMPLETION SETTER, answered statically (milestone/m342)
- **Answer:** the `base+0x8c` bit is SET by `or` through mapper `FUN_00507410`'s mask at exactly **11 addresses** (`4e4528` = the API `FUN_004e44f0`, `4f0ec0` = base screen `FUN_004ef6d0`, `4f3ebc`/`4f3f4c` = regions the Ghidra index does not name, + `FUN_004e47d0`'s 7); CLEAR = 3 `and` (`4e4546`, `4f38bb`, `4f49e1` — the last inside the charge routine `FUN_004f47f0`).
- **Accept:** `python3 -u scripts/m342_completion_setter.py` -> `PASS M342: 7/7 gates`, digest `2b88df5da5aeafe1` (`evidence/m342_completion_setter.txt:200`), PASS `:218`, 2 runs byte-identical. Harness `scripts/m342_mutate.py` -> `PASS HARNESS M342: 9/9`, NO-OP `[]`, baseline green (`evidence/m342_mutate.txt:2,:12`).
- **Writer census (the pick's question):** the field has exactly 2 idioms — 11 direct constant-form stores in exactly 2 indexed functions, and 9 pointer-form `lea` sites, 9/9 resolved to a store through that register (2 copy / 4 `or` / 3 `and`) (`:86`). The API `FUN_004e44f0(item, base, set)` is a 92-B set/clear: `or BYTE PTR [eax],cl` @`0x4e4528`, `and` @`0x4e4546`, index = mapper out1 `[ebp+0x8]`, mask = out2 `[ebp-0x4]`, 27 call sites in 8 functions (16 set=1 / 7 set=0 / 4 variable).
- **The pop is a NON-writer:** `FUN_004ef5d0` (244 B) shifts slots (`0x4ef62c`), decrements pending (`0x4ef642`) and calls only `0x5a73f0`/`0x5a6e70`/`0x446250`/`0x473760`; 0 refs to the bitmap, 0 API calls, 3 callers all in `FUN_004ef6d0`. So B30's completion leg does not stamp the bit — the stamp belongs to whoever CALLS the API. OPEN next: which of the 27 sites is the production-completion call.
- **PITFALL (field arithmetic):** the array base is `0x95da10`, NOT `0x95da14` — `0x95da14` is the OWNER byte (+4). Reading the base as 0x95da14 makes the bitmap look like +0x88, a 4-byte error no count catches; G1 DERIVES the base from the owner site (MU1 reddens it).
- **PITFALL (RMW through a pointer):** `or BYTE PTR [..+0x95da9c]` only catches the *constant-form* stores; the pointer-form ones are `lea r,[base+0x95da9c]` then `or cl,dl; mov [r],cl`, so a store-mnemonic census counts them as copies. G2 classifies by the RMW in the 4 instructions before the store; MU8 turns that off and reddens G2.
- **NAMED headroom:** 248,127 B (1,873 under cap) -> M329 rotated VERBATIM to `docs/named-archive-m329-rows.md:5` (sha1 `ccee72a56f16b4b4`, `scripts/m342_named_rotate.py --verify` PASS, idempotent) -> 241,089 B before this block.

## Session 323-chain1 (2026-11-24) — M344: the COMPLETION CALLER (milestone/m344)
- **Answer:** NO API caller completes production. The `base+0x8c` stamp for a finished item is the **inline `or` at `0x4f0ec0`** inside `FUN_004ef6d0` (the base screen), in the same block that spends the base's `+0x40` counter by `edi` (`0x4f0ca4/6`) and then reads the item-table row `[edi*48+0x984d38]` (`0x4f0f6f`) and **pops the queue 0x86 bytes later** at `0x4f0f46` (`push ds:0x68cbb0`). `edi`/`[ebp-0x30]` = the completed item, `esi`/`ds:0x68cbb0` = the current base, 304-fold `0x4f0eaa-0x4f0eb6`.
- **Accept:** `python3 -u scripts/m344_completion_caller.py` -> `PASS M344: 8/8 gates`, digest `034bf0e1a1606d2c` (`evidence/m344_completion_caller.txt:148`), 2 runs byte-identical. Harness `python3 -u scripts/m344_mutate.py` -> `PASS HARNESS M344: 10/10`, NO-OP `[]`, gates G1-G8 all covered (`evidence/m344_mutate.txt:14`).
- **The 27 sites, resolved:** every item argument resolves (0 unresolved) to imm 18 / callret 3 / clamped 2 / loopctr 2 / param 2; **0/27 take the item from the queue window `+0x4c..+0x77`**, and **0 of the 8 caller functions calls the pop** (`:74-80`). The four set=1 sites with a REGISTER item are exactly `0x41c6f8` (call-ret from the modal runner `0x5f1394` + a bitmap pre-read = toggle), `0x41d8fc` (loop counter under the `0x5a6e70` predicate), `0x508c85`/`0x508cee` (the `1..0x26` clamp of a type-2 entry). Rivals RIV1-RIV3 all FAIL on printed numbers (`:84-88`).
- **RETRACTION (M342 row):** M342's "16 set=1 / 7 set=0 / 4 variable" is **16/8/3** — its 6-instruction push window stops one push short at `0x40dd3c`, where the `push 0x0` sits 7 instructions back (`:36-38`). G1 now gates both the re-derived split and that single divergence row.
- **PITFALL:** arg order is `push set; push base; push item; call` — the ITEM is the push NEAREST the call (M342's mapping). A "reversed to program order" reconstruction silently reads the set flag as the item.

## Session 323-chain2 (2026-11-24) — M343: the `[obj+0xa40]` writer (M339's last OPEN)

- **ANSWER:** the modal runner's result cell is written by THREE functions, all publishing the SELECTED item: `FUN_005f5759` (+0xa8 CLICK-RESULT vmethod of 0x67164c/0x6717cc/0x6728c0, +0xb0 of the 0x671644 subobject) 4 stores; `FUN_005f58fa` (+0x64 of the five class vtables; the 0x671644 subobject carries it at +0x6c) 3; `FUN_005f5a11` (installed callback, receiver `ds:0x9977f0`) 2. Runner `FUN_005f1394`: exactly 1 ref, a READ at 0x5f3f45. Dialog ctor `FUN_00405ef0`: 0 refs.
- **ACCEPT** `python3 -u scripts/m343_a40_writer.py` -> `PASS M343: 9/9 gates`, `digest=bcdace84a0352b4a`, `table_sha256=06577d5fbab8d657`, 2 runs byte-identical (table `evidence/m343_a40_writer.txt:1-99`, gates `:101-115`, PASS `:118`); harness `python3 -u scripts/m343_mutate.py` -> `HARNESS PASS M343: 12/12 scored, NO-OP [], uncovered []` (`evidence/m343_mutate.txt:25`).
- **CENSUS (the trap):** 97 refs name displacement 0xa40: 25 INDEXED (`[x+y*1+0xa40]`, 12 functions) + 72 FIELD, all dword (47 stores / 25 reads). ZERO `lea reg,[...+0xa40]` sites, so the displacement census is COMPLETE for stores (trap 3's copied-register evasion does not exist at this field).
- **DISCRIMINATOR:** the dialog receiver's pair {[+0x21d0] container, [+0x2350] state} — exactly 4 functions carry it (runner + 3 writers). A ">=3 of {21d0,2350,30a8,3100}" filter wrongly admits `FUN_005ee350` (panel ctor) and `FUN_005eede6` (MU3/MU9).
- **IDENTITY:** 0x5f13b2 saves `ecx` to [ebp-0x394]; 0x5f3d70 stores that local to `ds:0x9977f0`; 0x5f3e02 restores; 0x5f3f45 reads `[ebp-0x394]+0xa40`; `FUN_005f5a11` loads `ds:0x9977f0` -> the SAME object (G7).
- **VALUE LAW:** each writer publishes {reset 0, `[container+0xec]` direct, `FUN_005fdcf7(container)` (17 call sites / 12 fns)}; 5a11 has no reset; the -1 store (0x5f581c) is reached only from arg == -2 AND `[this+0x30a8] & 0x40`.
- **REVIEW #365 (10 findings, all P1/P2 accepted into the instrument or the docs):** gates raised so each row is MEASURED, not labelled — G1 now counts the indexed functions (12) and `,0xa40` immediate forms (0); G4/G5 count ALL 97 refs (not the field subset); G3 asserts the pair set is exactly 4 names; G6 asserts the `[this+0x2228]` -> `[+8]` -> `+0xec` chain and the `call` adjacency for every store; G7 walks a 10-link identity chain including 0x5f3d6a. New MU10/MU11 redden the two new chain clauses; the doc wording "+0x64 of all six vtables" is CORRECTED (0x671644 is +0x6c).
- **PITFALL:** `"DWORD PTR"` CONTAINS `"WORD PTR"` — a width test that checks WORD first read all 72 refs as 2-byte (first run: dword 0, G1 red). PITFALL 2: the CPane subobject vtable 0x671644 carries the same two functions at +0xb0/+0x6c, not at the class offsets +0xa8/+0x64.
- **UNKNOWN:** who dispatches the +0x64 slot (19 `call [reg+0x64]` sites image-wide, none direct); the container's item record past +0xec; any consumer of `[this+0x3100]` (5759 stages the arg there).

## Session 324-chain2 (2026-11-24) — M345: the `+0x64` slot DISPATCH, answered NEGATIVE (milestone/m345)

- **SLOT:** `0x5f58fa` occurs **5x** as data, all `.rdata` at vtable+0x64 (0x6716b0/0x671830/0x672924/0x675d28/0x67772c); **0** `.text` operands (no call/thunk/lea). G1,G2.
- **ALIAS LAW:** ctor `FUN_00405ef0` installs 0x67164c at +0 and CPane 0x671644 at +0x444; 0x671644 sits 8 lower, so its `+0x6c` IS the primary `+0x64` — hence the census must include `+0x6c`. G3,G4.
- **TRIO:** `+0x60` 0x5f59bf `ret 8` (refuses on `[this+0x30a8]&0x4000`), `+0x64` 0x5f58fa `ret 4` (arg never read), `+0x68` 0x5f59e8. G5.
- **UNIVERSE:** 19 `call [r+0x64]` + 18 `call [r+0x6c]`, 0 jmp; **0 of 37** in 0x5f0000-0x600000; evasions absent (0 cached-slot->`call reg`, 0 `lea`+`call [r]`). G6,G7,G9.
- **ARITY:** {0:3,1:5,5:8,6:3}; 5 sites fit `ret 4` = 3 MEMBER + 2 self: `+0xf624` array elem, `+0xd9ec`, `+0x3870` (in FUN_00488ac0, a 13/27 key handler at +0x1e4 of family vt 0x675cc4), `[this+0x14]` (forwarder at +0x188 of class 0x676f70 whose `+0x64` is 0x4b8430), self in FUN_005cf43a. None is a dialog. G10.
- **TRAP:** the module's 4 `[r+0x64]` are all `mov`; 0x5f49ad/b9 swaps `[this+0x2240]+0x64` (read, then `[this+0x3168]` back) — a mnemonic-blind census calls it a dispatch. G8,G12 (swap measured).
- **ACCEPT** `m345_slot64_dispatch.py` -> `PASS M345: 12/12` `833faf38e189ad40` x2 (`evidence/m345_slot64_dispatch.txt:104`); `m345_mutate.py` 11/11, NO-OP [] (`evidence/m345_mutate.txt:17`). NAMED 245,927 B; M339 rotated VERBATIM to `docs/named-archive-m339-rows.md` (`9a93e8acca0a99ac`, `--verify` ok).
- **REVIEW #368:** 10 findings, all fixed in the instrument — dynamic gate count + G12, TABLE 3 prints all 37, G7/G10 full-set with a pinned kind set, G4 asserts `[eax]`, digest widened to the whole universe, M339 stub cites named.
- **UNKNOWN:** classes of the three MEMBER receivers and of FUN_00409a40's `+0x270c` member (no vptr install for it image-wide) — if one is a dialog the slot is live; consumer of `[this+0x3100]`.

## Session 324 — B31 BUILD (round 5/10): the recorded run as the completion ORACLE

Command: `python3 -u -m sim.facoracle` -> `PASS B31: 16/16 gates` (`evidence/b31_facoracle.txt:63`),
rows `ce7688c0cb3b5f9d` / oracle `7afda4dd49566fb4` / score `9a4f2c466f3d18b7` / img `fb0bc0caa186b766`,
re-run byte-identical. `python3 -u -m sim.selftest --b31` relays the same text. Harness
`python3 -u scripts/b31_mutate.py` -> `PASS HARNESS B31: 12/12`, digest `087e1d0228debbe9`
(`evidence/b31_mutate.txt:14`); NO-OP `[]`, every gate G1-G7 covered, MU5 forced a NEW gate (G4e) when
it reddened nothing; review #367 then forced G2's accounting (decoded delta vs RAW XOR popcount,
MU11) and the r0 anchor pin (G4f, MU12) - both had been printed, not gated.

What B31 measured (from `evidence/trace_m56_build_20261026_145157.jsonl`, the full 304-B record hex at
20 samples): 6 facility-bit gains and 2 losses — the recorded bitmap is NOT monotonic, so a completion
cannot explain every change. The rule "the queue head id is the bit that appeared" scores 0/6: 5 heads
are unit-encoded (-2, -3, -6, -8, 321) and the single in-window head (Virgin Soil, 2) did not stamp.
Korolev r0 replayed with the stamp attached: spend `8+1-9=0` matches B23's recorded after, head id 2 is
inside the facility window, and the recorded bitmap stays `[8]` — so the recorded negative is not
vacuous. The pop-first rival (read the head after the pop) stamps the next item (6 vs 2 on the declared
2-deep fixture), so M344's spend→stamp→pop order is load-bearing.

QUALIFIES `## B30` in place: B30's reader-inverse setter was ASSUMED and this round finds no positive
completion case in the game's own run, plus one negative at a facility-range head. B30's table row was
patched to say so; nothing in B30's own gates is retracted (they ran on a declared fixture).

Docs: NAMED 245,757 B (B24 4,772 B rotated VERBATIM to `docs/named-archive-b31-rows.md`, sha1
`6bb8d2c5c2114bbc6e333ff2665bda8c50cfa1d6`, `--verify` ok). NEXT_PROMPT patched by section.
STILL OPEN: the unit-id decoding (M68/M69 NEG_TYPE); which loss is a raze vs a record identity change;
whether a facility completion stamps at all.

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

## Session 328-chain2 (2026-11-24) — M351: the CHOOSER-side producer — a unit row IS the negated TYPE ORDINAL (milestone/m351)
- ANSWER (`python3 -u scripts/m351_type_producer.py`): the modal 0x496ad0 returns **+item when
  (flags & 0x20) != 0**, **-item when clear** (`and eax,0x20` @0x49772a, `je` @0x49772f,
  `neg eax` @0x49777c); item = row+4 (0x401940), flags = row payload+8 (0x495480); same law in
  9 insns at 0x494e61-0x494e8f.
- THE ROW LIST IS TWO SECTIONS. A: idx 0..0x7f, item = cand[idx] @0x9267e4 (k<0x40 -> k,
  k>=0x40 -> owner*0x40|(k&0x3f)), flags |0x20 -> +item. B: i = 1..0x47,
  item = **i**, flags = 0x4960f0(i)|0x10 -> -i; 0x4960f0 returns only {0,1,2,3}, so 0x20 is
  ALWAYS clear on a B row — every B row negates unconditionally.
- WHICH FIELD: i is the **TYPE ORDINAL** — the same counter indexes `0x984d38 + 0x30*i` (name)
  and `0x984d44 + 0x30*i` (cost, M349's array; G10 cross-checks both parses). The design-id
  space (cand 192+, owner 3) is section A and returns POSITIVE.
- CHOOSER ALREADY SPEAKS -i: affordability asked with -i (`neg ecx`/`call 0x4e4350` @0x495c2f),
  and the base queue slot ds:0x8f0d60+0x50+4*[sub+0xb68] is tested against -i
  (`neg edx`/`cmp edx,[ebp-0x30]` @0x495e5c) while A tests +item @0x495aef. 0x418b54-0x418b57
  writes the return to base+0x50 when pos==0; 0 negs in the 381-insn path → sign made upstream.
- **RETRACTION (narrows M349):** M68's "cell 6 = item 195 -> -3" is a STALE cell read —
  the trace's verdict says "the candidate array re-sorted between the read and the click". The
  cell is a ROW counter (sub+0xa818 -> sub+0xa774 @0x495b00) and rows are FILTERED (0x5a6e70,
  `jne` skip @0x495b69), so cell != item. -3/-6 stand as type ordinals; 195/196 does not.
- ACCEPT `PASS M351: 15/15` `504c7342fb16273b`, x2 identical (`evidence/m351_x2.txt:2-4`,
  sha1 `6f53b29d`); harness 20/20 NO-OP ['MU20'] (`evidence/m351_mutate.txt:27`).
- OPEN: section A = "designs" is INFERRED (trace names only); which B31 loss is a raze;
  whether a completion stamps.

## Session 328-chain3 (2026-11-24) — M352: the writeback — its target, the key matrix, and `ds:0x6926ec` RETRACTED

- **ACCEPT** `python3 -u scripts/m352_persist_writeback.py` -> **`PASS M352: 7/7 gates`**,
  tables digest `d553194a9f6ddce9`; x2 byte-identical (sha1 `c8bbfda4`,
  `evidence/m352_x2.txt:4`, `evidence/m352_persist_writeback.txt:140`); `m352_mutate.py` -> **13/13** killed, NO-OP green
  (`evidence/m352_mutate.txt`).
- **THE 8 `call edi`** (0x58f11b..0x58f3a8) are ONE target: edi loaded once @0x58f106 from
  `ds:0x6710fc` = KERNEL32!WritePrivateProfileStringA (import dir; slot in .rdata, not writable;
  the slot's own dword is a .rdata RVA naming the same function). 0 mem-indirect calls; 20 direct.
- **WRITE keys = 13**: Prefs Format, Difficulty, Map Type, Top Menu, Faction, Preferences,
  More Preferences, Custom World (8 direct) + Semaphore/Announce/Rules/Customize/Time Controls
  (5 via FUN_0058f030). 12 write blocks LOAD a block cell (11/11 scalars + the 7-dword array;
  window presence, not value provenance); `Prefs Format` is `__itoa(0xb)` — a hardcoded stamp, NOT a cell. **The persist
  writes no cell it never read.**
- **READ asymmetry (image-wide, total):** 5 `GetPrivateProfileStringA` refs in 5 fns (0x58e5a0,
  0x58e640, 0x58e6c0, 0x58e760, 0x58e7f0); 52 attributed sites -> 35 keys. 13/13 written keys are
  read (0 write-only). Read but written NOWHERE (33 write sites / 28 keys): **`Laptop`**
  (0x6926fc/0x692704; twins + 2 loader sites) and **`Language`** (0x69270c).
- **RETRACTION (M350 OPEN "who sets ds:0x6926ec")**: nobody — it is not a variable. No store names the
  VA (moffs/mem-dest forms) and nothing materialises it as data; 7 uses all `push 0x6926ec` in the lpKeyName
  slot (the 7 four-byte VA occurrences are all push imm32, so nothing even materialises
  the address as data); the VA holds the literal `Prefs Format` (0x6926e8 = the `"0"` default of the same call).
  M350's "first read takes its key pointer from ds:0x6926ec" restated: the read's KEY IS it.
- **PROTOCOL**: `Prefs Format`=11 written once, read at 7 sites; `cmp eax,0xb` gates the 6 inline
  loader reads and all of FUN_0058e5a0 (mismatch -> caller's default); FUN_0058e760 (23 callers)
  reads ints with NO gate.
- **OPEN**: what `Laptop` selects (its atoi feeds masks @0x58ea12/0x58eb2b); the twins'
  0x3a7168/0x327168 return; whether any completion path re-persists.

## Session 329-chain1 (2026-11-24) — M353: the `0x999fa4` numeric band — its ONE indexed filler and four `$` consumers (milestone/m353)

- RUN `python3 -u scripts/m353_numeric_band.py` -> **PASS M353: 11/11 gates** digest `367fdae1d78979e5` (`evidence/m353_numeric_band.txt:87`), two renders byte-identical, stdout == committed evidence; harness `scripts/m353_mutate.py` -> **HARNESS PASS 14/14** `fd143532b283b01b` (`evidence/m353_mutate.txt:14`).
- GEOMETRY (V): numeric `0x999fa4` / owner `0x999fcc` / payload `0x999ff4` are 0x28 apart (10 dwords each); text `0x99a01c` stride 0x100 x10 -> `0x99aa1c` (`:77`).
- REFS (V): 16 = 11 absolute + 5 `[reg*4+0x999fa4]`; stores exactly 3 — `0x626597` SCALED (FUN_00626581), `0x442642` abs (cheat clamp, FUN_00442320), `0x626fd7` abs (FUN_00626f19 stores `0x64c460(0x99a01c)`'s return) (`:75-76`).
- FILLER (V): `FUN_00626581`, 33 B: `cmp [ebp+8],9; jle` else `mov eax,3`; store `[eax*4+0x999fa4]`; `xor eax,eax`; ret. 260 call sites, 242 with a literal k in 0..6, NONE above 9 (`:38-39,:78-79`).
- RETRACTION (V): M325/M324's `g999fa4 W={442642,626fd7}` was an ABSOLUTE-address census — the scaled store was invisible to it. Both rows patched in place in `NAMED.md`.
- CONSUMERS (V): in FUN_00625b20 — `$NUMBER`@625c2c, `$NUM`@625cec, `$HEX`@625e4b, each `__itoa(v,buf,10)`; arg3 of `0x64f980` IS the radix (`cmp [ebp+0x10],0xa`, then forwards it), so **`$HEX` prints DECIMAL** (`:80-81`).
- The 4th read `0x626091` is the `$#k` PREDICATE: k = char-0x30, `cmp numeric[k],1`, `setne`; that path has NO k bound while `$k` does (`cmp k,0xa`) (`:82`). Arithmetic: k=10 -> owner[0], 20 -> payload[0], 30 -> text[0] (`:83,:70`).
- OPEN: what the `$#` flag gates; numeric[0] is DUAL-USE (cheat clamp `0x442642` vs ENERGY read `0x4e032c`/`0x4e0336`); `0x64c460`'s semantic.
- CAP: NAMED headroom was 4,204 B (<5 KB trigger) -> `## B25` rotated VERBATIM to `docs/named-archive-m353-rows.md`, sha1 `dd4991b77b2528c9d3bf011d226165c14277c19d`, verify 8/8 (`evidence/m353_named_rotate.txt:9`); review #378: 10 findings (4 P1/6 P2) all fixed - geometry DERIVED from the writer body, G5 histogram pinned, G6 per-address mapping, G7 arg3 position, store-form census, RETRACT preserved through the rotation.
- PITFALLS: (a) a rotation stub gate written as `... or True` is vacuous — replaced with a real set-intersection check; (b) a PE section walk must read ImageBase at `pe+24+28`, not at the section-table base.

## Session 329-chain2 (2026-11-24) — M354: section A's identity = the 0x98ad88 row (M351's OPEN closed; leg NOUNS retracted)

- **ACCEPT** `python3 -u scripts/m354_design_row.py` -> **`PASS M354: 11/11 gates`**,
  table digest `dd5e689e8d9af320`; two runs byte-identical (`evidence/m354_design_row.txt`,
  `evidence/m354_x2.txt:91`). `scripts/m354_mutate.py` -> **23/24 scored, NO-OP ['MU25']**,
  measured coverage ALL 11 gates (`evidence/m354_mutate.txt:30`).
- **REVIEW #379 (11 findings, all fixed)**: function extents now PARSED
  (`.func_starts.json` + the last ret) instead of window widths; G4 proves "no data reads"
  by classifying every PTR operand; G9 pins `test/jge/neg` and LOAD-vs-STORE; G6 pins the
  mask+store; G10 gates 4 atlas semantics; harness records ALL reddened gates and adds
  MU19-MU24 so every gate has a killer; rotation stub header is derived from the archived
  block (the hardcoded "neighbour test" vs "neighbourhood" was a real byte mismatch).
- **THE ROW IS A 0x98ad88 RECORD**, stride 0x34, keyed by the A item: three imul sites
  (0x49571b name, 0x4957e2 +0x29 weight, 0x4959be +0x2a class) all read the item from
  [ebp-0x2c], filled from `[ecx*4+0x9267e4]` @0x4956d6. So a +head is a UNIT-TYPE/design
  ROW, not a facility id — M351's OPEN "does A speak designs" is ANSWERED (V).
- **THE FLAGS FNS DIFFER IN KIND**: 0x496050 (A) reads exactly +0x2a and +0x30 and is
  band-guarded (`cmp [ebp+8],0x40`, bit 4 test); 0x4960f0 (B) reads NO memory at all and
  returns {1,2,3}. Two different row spaces, proved by their field sets, not by names.
- **BUILDER**: 0x596000 writes `owner*0x40 | (k&0x3f)` for k>=0x40 (shl 0x6; cmp 0x40) —
  64 shared rows + 64 owner-band rows; the same value is row-indexed (13*i<<2 = 0x34*i).
- **RETRACTION (narrows M349 + M351):** the decoder's legs are identified by their TABLES,
  not by their labels: head<0 reads the 0x984d38/0x30 cost +0x0c (M337 = `#FACILITIES`);
  head>=0 indexes 0x98ad88/0x34 and stamps +0x30 (0x4efe50/60). So M349's per-leg nouns
  (neg=UNIT, +2=FACILITY) and M351's "unit row" label for section B are INVERTED; the
  sign split and all arithmetic stand. Do not re-derive the nouns from trace names.
- **PITFALL (new)**: gate messages that index a parsed list (`v30[0]`) crash *before* the
  FAIL line prints, so the mutant scores MISSED — a gate that can die silently is a defect;
  format parsed sets, then assert. MU11 also caught an AUTHORED constant (the 0x40 split
  was hardcoded); the split is now parsed from 0x596017.
- **DOC CAP**: NAMED 245,796 B was under the 5 KB trigger -> `## M312` rotated VERBATIM to
  `docs/named-archive-m354-rows.md` (sha1 `5e8df0971a3d9bae`, `scripts/m354_named_rotate.py
  --verify` PASS) before `## M354` landed.
- OPEN: game nouns of +0x25..+0x28; bit2 = prototype build INFERRED.

## Session 329-chain3 (2026-11-24) — M355: `Laptop` = the DEFAULT bit-vectors of `Preferences` / `More Preferences`

- **ACCEPT** `python3 -u scripts/m355_laptop_masks.py` -> **`PASS M355: 7/7`**, digest
  `c742bc131105fb25`, sha1 `d3f17cc9` x2 identical (`evidence/m355_x2.txt:3-4`);
  `m355_mutate.py` -> **24/24 killed**, 2 NO-OP green (`evidence/m355_mutate.txt`).
- **`Laptop`** = 4 read sites (0x58e9f3/0x58eb0c loader; 0x58e688/0x58e708 in getters 0x58e640/
  0x58e6c0, one each), 2 VAs both "Laptop"; `neg`/`sbb` -> 0/-1 = `atoi != 0`; absent == explicit 0
  (lpDefault = the zeroed 0x997120, zeroed before the call).
- **MASKS** (from the encoded `and`/`add` immediates; the register is proven to be the read's atoi
  return, G2e): Preferences 0xbbe1dd96 / 0xa3e1dd16; More Preferences 0x3a7168 / 0x327168.
  Laptop!=0 CLEARS bits {7,27,28} resp. {19} — it removes options, never adds.
- **ROLE**: the mask is the lpDefault of two bit-string reads (0x58eaf7 `Preferences`, 0x58ec0d
  `More Preferences`), emitted as '1'/'0' over bits 31..0 by a downward loop (`shl edx,cl`, `test
  <mask>,edx`, leading zeros >bit 8 dropped); parser 0x628720 (`v=v*2+(c-0x30)`) gives the dword.
- **GATE**: `Difficulty` (ds:0x92bde8) < 2 ORs Preferences bit 5 — LOADER default only, on the jcc
  fall-through; B block and both getters hold 0 refs.
- **CONSUMER**: getters feed one dialog block (0x493b0b..0x493b79, 5+5 sites, 11-field order
  measured both ways) storing +0xa30..+0xa58; APPLY 0x4923d0 ORs +0xa30 into ds:0x92befc @0x492464
  and +0xa34 into ds:0x92bf00 @0x49246f. `Laptop` changes DEFAULTS only.
- **REVIEW (PR #380)**: 10 findings closed by tightening G1a/G1b/G1d/G2e/G3a/G4a/G4b/G5b/G5c and
  the rotate guard; 8 new mutants (MU17-24), no check weakened.
- **PROTOCOL**: NAMED headroom 4,204 B (< 5 KB trigger) -> `m355_named_rotate.py` rotated `## M293`
  VERBATIM (block sha1 `e548f949`) to `docs/named-archive-m355-rows.md`.
- **OPEN**: the option NAME of each set bit; whether another path re-derives 0x92befc/0x92bf00.

## Session 330-chain3 (2026-11-24) - M357: bit -> option LABELS of the two `Laptop` bitmaps

- **ACCEPT** `python3 -u scripts/m357_pref_bits.py` -> **`PASS M357: 18/18`**, digest
  `095258c8b40d0e23`, sha1 `bb36f237` x2 identical (`evidence/m357_x2.txt:1-3`);
  `m357_mutate.py` -> **23/23 killed**, 1 NO-OP (`evidence/m357_mutate.txt`) — every gate
  named in `## M357` is reddened by its own mutant (MU1-MU23).
- **PAIRING**: six builders read a Script.txt section by name (0x5ea431: BASICPREFS
  0x49043b, ADVANCED 0x4906d2, AUTOMATION 0x490a67, AUDIOVISUAL 0x490e70,
  BASEWARNINGS 0x49112a, MAPPREFS 0x4916b8) and per row take the next line
  (0x5ea448) -> strcpy into the page's static slot (0x68b678.., +4/dword) -> add_item
  0x604fd2 (text, id). Rows 8/12/14/8/17/7 = 66; ids are NOT positional
  (BASIC = 5,6,64,7,8,9,10,11).
- **BITS**: rebuild 0x492940 maps all 70 ids to one (field,bit) each (imm + ebx
  decoded); APPLY merges A fields -> 0x92befc, B -> 0x92bf00, a28|a48 -> **0x92bf04**
  (my first hand read put a48 in 0x92befc; sim + M355 refute it, RETRACTED). 1:1 66/66.
- **ANSWER**: befc bit1 Autosave, 2 move-enemy-quickly, 5 Tutorial (M355's
  Difficulty<2 bit), 7 Secret Project movies, 8 map grid, 12 mouse-at-edge,
  14 design units, 15 move-allied-quickly, 16 air units return home, 21/22/23 cancel
  on Treaty/Truce/Vendetta, 24 formers plant forests, 25 condensers, 27 Interludes,
  28 Sound effects, 29 radio-buttons, 31 wake passengers; bf00 bit13 base names,
  17 Background music, 19 Monuments, 20 auto-prune, 21 detailed main menus.
- **LAPTOP DELTA** = A{7,27,28} + B{19} = "Secret Project movies." "Interludes."
  "Sound effects." "Monuments." — every laptop-cleared bit is an A/V row.
- **DIVERGENCE**: #AUDIOVISUALPREFS offers 11 lines, the exe builds 8 ("Sliding
  windows.", "Sliding scrollbars.", "Whole unit blinks." unused).
- **DOC CAP**: NAMED 245,616 B -> `## M272`+`## M273` rotated VERBATIM (sha1
  `aa685936`/`22154fba`, `scripts/m357_named_rotate.py --verify` PASS).
- **OPEN**: ids 0x37/0x38/0x39/0x50; bits no dialog row writes (A 4,6,10,11,13,26;
  B 1,14,25-31).

## Session 330 (2026-11-24) — B33: the OR at `0x4f0ec0` is UNIT-ONLY — the facility leg spends and never stamps

- **ACCEPT** `python3 -u -m sim.facilityleg` -> **`PASS B33: 12/12 gates`** `b89b9e6bd940e8d3`
  (`evidence/b33_facilityleg.txt:65`), rerun byte-identical; relay `--b33` identical;
  `scripts/b33_mutate.py` 11/11 (`evidence/b33_mutate.txt:13`).
- **CENSUS** FUN_004ef6d0 = 3,164 insns, 12,298 B CONTIGUOUS (lengths summed), `0x4ef6d0..0x4f26da`
  == Ghidra `size=12298` read from `ghidra_out/index.csv`; CFG 3,482 edges, 0 external, 0 indirect.
  Fixture: `scripts/b33_extract.py --check` (objdump wrap lines folded into lengths).
- **REACH** entry + unit branch `0x4ef8a4` reach the stamp block `0x4f0e90` (3,045 insns);
  facility branch `0x4efa2c` reaches 886 and does NOT.
- **DOOR** `preds(0x4f0e90)={0x4f0d94}`, `preds(0x4f0ca1)={0x4f0b80}`, `0x4f0b80` = `jg` on
  `[ebp-0x30]`; that local is written at ONE site, `0x4ef8a4` (unit branch), never facility-reached.
- **SPEND** facility `0x4efed8/db/dd` (`[ecx+0x40]`), unit `0x4f0ca1/a4/a6` (`[edx+0x40]`).
- **SCORE** recorded: 4/4 unit heads gain the mapper bit, 0/2 facility-range; Virgin Soil head 2,
  bitmap `00000008..` -> `10000000..` (bit 2 absent, 4 gained, 27 lost), `st` 2 -> 0.
- **RIVALS** shared-OR 4/6 windows (predicts `0400000800000000`), off-map refusal 1/6, after-pop 0/6.
- **RETRACTION (declared gap)** B32's "why a facility head does not stamp" is ANSWERED: the `jg`.
- **PROTOCOL** `scripts/b33_named_rotate.py` rotated `## M333` VERBATIM (sha1 `be87f76187588fde
  4268db6355ba93f44eacc0cd`, 26 tokens) to `docs/named-archive-b33-rows.md`.
- **REVIEW (#381, 7 findings)**: all fixed - MU11 reddens G6; G1 sums byte lengths and reads
  Ghidra's size; G2 pins 3,482 edges; G3 pins the three sets as nested; G4 reads the local from the
  census; G11 asserts the `cmp ebx,0x40`/`jl` split; the parser folds wrapped bytes and marks
  indirect calls `ind`; cites repointed (`:65`).
- **MERGED** #381 as `8cb969b` (squash) after the #381 triage; CI gate pass.
- **OPEN** facility stamp elsewhere (`0x4e4528`/`0x4f3ebc`/`0x4f3f4c`); the `0x98adb8` row; loss 27.

## Session 331 (docs, 2026-11-24) — record the B33 merge; no new milestone taken

- B33 merged as `8cb969b` (#381 squash) on a GREEN verdict after the local review triage; the
  cursor said "PR pending" when it was committed pre-merge, which would send the next fire looking
  for an open PR - it now records the squash hash.
- Archived the #381 review artifacts under `evidence/ai_review/` (they were untracked).

## Session 330-chain2 (2026-11-24) — M356: +0x30 bit 2 = state bit (11 setters, 1 toggler); +0x24/+0x25/+0x26 feed three rule tables

- **ACCEPT** `scripts/m356_prototype_stamp.py` -> **`PASS M356: 17/17 gates`**,
  digest `c1a2beb794cec9f8`, x2 same (`evidence/m356_x2.txt:103`); `m356_mutate.py` ->
  **27/27, NO-OP ['MU29'], coverage ALL 17 gates** (`evidence/m356_mutate.txt:32`).
- **CENSUS** (instruction shapes; last write to the stored register + flags-word load
  provenance): 46 writes to +0x30 (= 0x98adb8); **11 bit-2 setters**, **0 AND-clears**,
  **1 XOR-toggler 0x4396f6** (`xor dx,0x4` @0x4396e6), 0 unresolved register masks, 16 ANDs
  all carrying immediates. First draft said "one-way latch" — the toggler REFUTES it.
- **TWO 0->1 GUARDS**: 0x4d2ff9 load->test->jne-skips-store->OR->store->`call 0x584520`;
  0x4efe60 stores `al|4` then tests the OLD bit, `call 0x572800` only on 0->1; both behind
  `cmp idx,0x40 / jl` (owner band).
- **FEEDS** (`trace_base`): **+0x24 -> 0x92ae80** chassis, stride 0x90, 188 chains; **+0x25 ->
  0x92b950** 21 recs, 181 chains; **+0x26 -> 0x92fd18** 10 recs, 47 chains — exclusive; extents
  DERIVED from each loop (init/stride/bound). Reference census 238/227/11, 94/88/6: every
  non-load reference is a `cmp`, none names a table base.
- **FINALIZER 0x595e80** compares weapon `[0x92b950][+0x25]` with armor `[0x92fd18][+0x26]`
  (`cmp al,bl`) and assigns the +0x2b mode (3/1/4/5/10); flags init 1/0x105/0x115.
- **RIVAL REFUTED**: "+0x27/+0x28 are 0x10-stride ordinals" — 0 table chains either; +0x28 has
  ONE writer (0x595d1c).
- **RETRACTIONS**: (M354) +0x24 is the CHASSIS ORDINAL, not "domain"; (this draft) bit 2 is
  not monotone. A fixed backwards window had attributed a guard `and` to a later store —
  classify by the LAST write to the register (0x4399c5 vs the 0x4399d8 reload).
- **DOC CAP**: `scripts/m356_named_rotate.py` rotated `## M298` VERBATIM ->
  `docs/named-archive-m356-rows.md` (sha1 `a7e25e64`).
- OPEN: +0x27/+0x28 nouns; bit2 UI reading INFERRED.

## Session 331-chain3 (2026-11-24) — M360: the four row-less ids are A/V radio rows + a swapped id in a SEVENTH widget, not a seventh page

- **PICK** (M357's orphans): "a seventh page nobody builds, or a non-preferences dialog?" ->
  **neither**.
- **ACCEPT** `python3 -u scripts/m360_orphans.py` -> **`PASS M360: 25/25 gates`** digest
  `eb9f07df920a75ab` (`evidence/m360_orphans.txt:137`), re-run identical; `m360_mutate.py` ->
  **23/23 killed, coverage 25/25** (`evidence/m360_mutate.txt:26`).
- **SEVEN widgets** +0x5974/649c/6fc4/7aec/8614/913c/9c64; builder 66 rows (8/12/14/8/13/4/7);
  REBUILD 0x492940 queries **70** (8/12/14/**11**/14/4/7); PAINT paints the same 70.
- **Orphans**: +0x7aec queries 0x37/0x38/0x39, builds none; +0x8614 queries an extra 0x30
  (built in +0x913c); +0x913c **built 0x30, queries 0x50** — a swapped id.
- **MISS SEMANTICS (retraction of draft #1)**: `is_checked` 0x6051fa and `set_checked` 0x6050d4
  scan from 0, exit on `jge` at the count, test `1<<[node+0x14]`: a miss resolves to
  **bit<count>**, not 0 — 8/13/4.
- **0x37/0x38/0x39 are RADIO handlers** (dispatch key (id-0x13) MEASURED at 0x4934d4, class bytes
  1/2/3): a4c 0x800/0x400, a50 0x4000; they set a flag and relabel ctrl 0x4e/0x4c/0x4d via
  0x493ec0, never call set-by-id -> A/V bit 8 is written by nothing (inert, not aliasing).
- **0x50 is a checkbox** but its block never reloads a48: it ANDs stale `[ebp-0x8]` = (a48 &
  0x1000, one write 0x49368c) with 0x8000/0x10000/0x20000/0x4000 -> all 0.
- **RIVALS refuted** `:123-127`: R1 0 rows into 0x913c -> 4; R2 79 add_item sites, 0 foreign, no
  `ds:` widget; R3 1 absent-id write exists; R4 miss leaves n-1 -> n. 8 of 24 set-by-id sites
  target the seven widgets, all in PAINT (`:114`).
- **INFERRED**: the 3 unbuilt A/V ids match Script.txt's 3 unconsumed A/V lines (count only).
- **OPEN**: pre-1.0 builds with those rows; readers of flags [0x14d6c]/[0x14220]/[0x158b8].
- **REVIEW #387**: 11 findings triaged (new G2g/G4f/G5c, G4c re-anchored, G4d reads [ebp-0x8]).

## Session 332-chain2 (2026-11-24) — M359: +0x28 = CARRY CAPACITY (V), +0x27 = reactor level (INFERRED); M356's single-writer row RETRACTED

- **ACCEPT** `python3 -u scripts/m359_design_record.py` -> **`PASS M359: 14/14 gates`**,
  digest `7d4a2d1356c9ff41` (`evidence/m359_x1.txt:112,114`); `diff -q evidence/m359_x1.txt
  evidence/m359_x2.txt` empty; `m359_mutate.py` -> **18/18 RED, NO-OP none**
  (`evidence/m359_mutate.txt:41`), incl. two algorithm mutants (arg resolution MU13, a
  def-use insert MU19) and the carry multiply->add MU7.
- **WRITER** 0x595b10 = the design-record builder. Arg->field map computed from the
  stores (`:26-34`): +0x24<-arg0xc, +0x25<-arg0x10, +0x26<-arg0x14, +0x27<-arg0x1c,
  +0x20<-arg0x18, +0x29<-ret(0x595820), +0x28<-ret(0x570860) or 0.
- **LOADER** 0x579f40 = #UNITS parser. Six stack args (`:38-44`): (row band, chassis,
  weapon, armor, ability bits, **constant 1**), call target 0x595b10; then it writes the
  alpha columns Plan/Cost/Carry/Icon at +0x2a/+0x29/+0x28/+0x2e, each guarded
  (`test`+`jl` for plan<0, `test`+`je` for cost==0/carry==0, jump lands after the store)
  (`:47-55`).
- **+0x28 = CARRY CAPACITY** (V): the auto-value is gated `cmp byte [wep+0x02],0x7`
  (`:61`; alpha #WEAPONS Mode 7 = Transport, same base +0x00 == 99 = Planet Buster);
  0x570860 = chassis +0x03 * arg(reactor), /2 on ability 0x800000 and (3v+1)/2 on 0x80000
  (`:64-90`); the loader's Carry column lands in the same byte. **Two writers** by the
  anchored-register census: 0x595d1c and 0x57a041 (`:57-59`).
- **+0x27 = REACTOR LEVEL** (INFERRED, strong): constant 1 for every basic unit; 127
  loads, the only compare band is **{1:53, 3:54} over 52 clamp sites** (`:92-93`); the UI
  health path scales `clamp(v,1,3)*10/3` with the input written only by the clamp (`:95-96`).
- **RETRACTION** (M356 G14): "+0x28 has ONE writer" is FALSE — the literal-form grep sees
  one; the anchored census (absolute-displacement form + literal base advanced by 0x34)
  sees two (`:57`). +0x2a is the PLAN (M354 called it "class"): the loader's Plan token
  lands there, the Planet-Buster branch hard-sets +0x2a=5 = alpha Plan 5, and **49** sites
  (4 base registers) compare it with 12 (`:98-101`).
- **REVIEW #385** 10 findings (3 P1) all fixed: G12 added (conditional guards), G7 now
  gates the ability chain, G5 replaced by an anchored writer census, G11 generalized
  (43->49 across 4 registers), G6 binds index<<4/+0x02 to the 99 compare, G9 pins the
  full divide + clamp input, G3 binds loader args to the callee's +0x27, resolve_arg is
  def-use (MU19 is the counter-example).
- **OPEN**: alpha #REACTORS has 4 rows but the health readers clamp to 1..3 (pre-SMAX
  path or display bucket?); the +0x27 noun still rests on elimination + the constant 1.

## Session 332-chain1 (2026-11-24) — M358: the 52-byte 0x98ad88 row's full layout; 0x9267e4 is a 128-dword slot table (not 64-byte rows)

- **ACCEPT** `python3 -u scripts/m358_row_layout.py` -> **`PASS M358: 10/10 gates`
  `1af1dcb6fcd4a4b6`** (`evidence/m358_row_layout.txt:98`), rerun byte-identical;
  `scripts/m358_mutate.py` -> **12/13 scored, NO-OP ['MU13'], coverage G1-G10**
  (`evidence/m358_mutate.txt:22`); review #386's 10 findings all fixed (G6 reads the
  builders' bound, G7 parsed shift/mask, G8 the full A chain, G9 decoded immediates,
  G10 store-by-store pairing, G5 parsed stride/jl/start, G2 census counts, cites re-lined).
- **CENSUS**: 1,991 refs (1,907 memory) in 227 functions over the 0x98ad88 span
  (64 rows x 0x34); 756 `imul reg,reg,0x34` sites. 17 field offsets: name
  char[0x20] at +0x00 (the only +0x1f ref is its NUL store), dword +0x20
  (ability mask; dword tests like 0x10000 + byte bit tests), bytes +0x24..+0x2e,
  word +0x30 (byte bit ops on 0x30/0x31), word +0x32 (pre-req); 0x2f and 0x33 are
  never addressed. M356's "46 writes to +0x30" = 25 movs + 21 RMWs.
- **PROTOTYPE**: row 63 (base 0x98ba54) is written whole by FUN_00435610 from a
  source record: +0x141fc->+0x24, +0x14200->+0x25, +0x14204->+0x26,
  +0x14208(dword)->+0x20, +0x1420c->+0x27, and 0xff->+0x2e.
- **0x9267e4**: 10 refs total, 7 memory, ALL `[reg*4+base]`; 128 dwords, two
  64-slot banks (0x40 shared / owner<<6): entry = (slot<0x40 ? 0 : owner<<6) +
  (slot&0x3f), masked by 0x8000003f with a sign repair; the 14-instruction band
  sequence is matched in BOTH builders (0x596000 ecx/ebx, 0x596160 edx/esi).
  The kickoff's "64-byte design row at 0x9267e4" is REFUTED — 64 is the bank
  size, not a record stride.
- **SENTINELS**: the 16 cmp-immediates in the row window (0x98ad90 x12, +0x0c
  x2, +0x10 x1, +0x14 x1) are loop END checks of 0x1c-stride scans; the four
  static loops (0x98aaf0..0xad90 etc.) are exactly 24 iterations. They are NOT
  row fields at +0x08/+0x0c/+0x10/+0x14.
- **flags bit8**: one clearer (`and [+0x31],0xfe` @0x4ef398) and three setters
  (`or [+0x31],0x1` @0x4f05bd/0x5a7d00/0x5a7f67) -> bit 0x100 is a real state
  flag; its noun is OPEN.
- CROSS-REF M359 (chain2, same row): +0x27 = reactor level, +0x28 = carry capacity, +0x2a = plan.
- OPEN: +0x2b/+0x2d/+0x2e nouns; the 24-record 0x1c table's identity
  (it ends at 0x98ad90..0x98ad9c); bit8 noun. NEXT: (x6) pref-block writers;
  B34 = facility +0x8c.

## Session 333-chain3 (2026-11-24) — M362: the 0x4db1xx sibling = the FACTION RELATIONS page; its +0x15a0 group = 13 ids that ARE the bits

- **PICK** (M360's alternate): "a second dialog with its own radio/flag block" -> the
  relations page (builder FUN_004db480: title = the faction name at 0x927874+f*0x59c, left
  list = every OTHER faction; +0xa1c = faction, +0xa20 = target), flag widget inline at
  dialog+0x15a0.
- **ACCEPT** `python3 -u scripts/m362_sibling.py` -> **`PASS M362: 22/22 gates`**
  `18298ed8d31de144` (`evidence/m362_sibling.txt:100`), re-run identical;
  `m362_mutate.py` -> **23/23 killed, 22/22 gates named**. Review #390's 8 findings fixed:
  G2b counts in-record slots, G4c binds the label call, G6c forbids unresolved forms, R3
  parses the delta, rotation idempotent.
- **13 rows, ids = bits**: 8,10,4,2,1,1000,2000,20,2000000,400,40000 read
  `0x94d448[fac*0x82f+tgt]`; 80000008,80002000 read `0x94d468` — the prefix picks the
  record's SECOND dword (+0x20 = slot +8); the high-id set IS the 0x94d468 row set.
- **INDEX**: all 13 blocks run one identical 6-insn idiom (shl 6/add/lea/shl 4/sub/add)
  = fac*0x82f + tgt; 0x82f dwords = 0x20bc B; the dialog indexes 12 slots, all in-record.
- **BUILDER** adds the same 13 ids in the same ORDER, one label each from
  FUN_0061482f(0x997b28, [0x997b20+off], 0), 13 DISTINCT slots a0c..a18/d90..dac/df8.
- **HANDLERS/WRITERS**: 0x4dabb0 (plain,A) -> 0x5518f0 clear / 0x551a20 set; 0x4dac30
  (high,B) -> 0x5519c0 / 0x551c40; 0x4dacc0 -> 0x551cf0 one-way; 0x4dad40 -> 0x551d70
  one-way. 4 of 6 writers store BOTH (p1,p2)/(p2,p1); 0x5518f0 also clears B's 0xC00.
- **TRAPS**: stores are RMWs via a copied register — census by FORM, not store shape;
  backward def-use must not cross a branch (0x551d70 arm 2).
- **ROTATION**: `scripts/m362_named_rotate.py` moved M250-M254/M277/M326/M246 VERBATIM to
  `docs/named-archive-m362-rows.md` (sha1 4/4, 2nd run a no-op); NAMED 246,262 B.
- **OPEN**: the 13 labels (0x997b20 heap); bit NOUNS (chain-2 lane); 0x94d5dc.
## Session 333-chain1 (2026-11-24) — B34: a FACILITY completion stamps NOTHING (no writer on the leg; the recorded bytes falsify the stamp at 3 discriminating completions)

`python3 -u -m sim.facstamp` -> **`PASS B34: 10/10 gates  5296fdad6d26caa3`** (`evidence/b34_facstamp.txt:99`,
re-run identical); harness 13/13, NO-OP `[]` (`evidence/b34_mutate.txt:16`). Answer to B33's gap: nowhere.
- **21 stores, and M342's 20 is SHORT BY ONE** (`:14,:88`): all 194 bitmap references are classified
  (11 direct + 183 address loads: 9 `lea`, 174 `mov`-imm, 10 feeding a store) -> API 2 / GRANT 11 /
  SET 1 / COPY 7. The miss is the screen's byte COPY at `4f0d60` (`mov [esi+eax*1],dl`); M342's lea-window was too
  short to reach it. COPY is the only LOSS-capable family.
- **Leg is writer-free, measured**: pop `FUN_004ef5d0` 88 insns, 0 bitmap refs, 0 API calls; the base screen
  (its only caller) 0 API calls, its only bitmap store the unit-only OR. API hosts ∩ pop hosts = ∅ (`:87-88`).
- **6 facility completions in the recorded run** (`:54-59`), not B31's 1: Korolev r0, Virgin Soil s1/s9 (head 2),
  New Jerusalem s1/s9 + Training Camp s15 (head 1). PAY = `st+1 >= 9` — testing `st >= price` misses Korolev.
- **3 discriminate, 3 are vacuous (bit already set)**; all 3 discriminating falsify the stamp ON BYTES
  (`:70-76,:92`): model `[8]`→`[2,8]` (Korolev), `[27]`→`[2,27]` (Virgin Soil) vs the recording's no-bit-2.
- **The 5 gains are not completions** (`:61-67`): before-heads 321/-2/-8/-3/-6 (unit-encoded); Virgin Soil s11
  (gain 4 + LOSS 27, no pay) is the COPY signature.
- **B31 QUALIFIED**: its single negative is real but is 3 boundaries, and it did not flag the vacuous rows.
- **Pitfalls**: `lea`-form writers need register-follow (`mov BYTE PTR [eax],cl` has no bitmap constant — a
  constant-only grep finds 11 of 20); `4f49e1` is a `mov` here (M342 said `and`); head 0 = empty queue, not item 0.
- NAMED 247,680 → 245,677 B by rotating `## B22` verbatim (`scripts/b34_named_rotate.py`, sha1 `524f63de`).
