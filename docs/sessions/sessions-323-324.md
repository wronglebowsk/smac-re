# Session notes archive — sessions 323-324

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-322-323.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

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
