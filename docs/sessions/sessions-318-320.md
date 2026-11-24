# Session notes archive — sessions 318-320

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-317-318.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 318-chain2 (2026-11-24) — M336: ds:0x8f0090 = difficulty byte of PLAYER RECORD 1; one UNCLAMPED #DIFF reader

- **ANSWER (pick (x6)):** record 1, byte +2 of an 8-record array at FRAME `0x8eff18`, stride
  `0x176` (end `0x8f0ac8`; rec-1 ptr `0x8f008e`). The ADDRESS census finds ONE reader: `movsx edx,BYTE [ecx+0x8eff1a]` at **0x486788** (FUN_004865c0), ecx = 0x176*(k+1), k =
  `[ebp-0x8]` (0x4865dc/5f5/77c), bound `BYTE ds:0x8f0c10` (4 at
  reset, 0x4e2444) => k=0 is row 0, address == TARGET; the byte feeds `[b*4+0x94d2ac]` (0x48678f)
  (0 gap).
- **6 write sites, 3 forms:** direct 0x48884d; record-indexed 0x487e87/0x525b83 (const=target-1
  rec); walk +2 0x4e24a2/0x525cb9/0x525d28. Sources 0x8f0c11 x3 + lit 0 -- M332's "1 ref, 1
  write" was form-limited.
- **INDEX 6 ADMISSIBLE:** all 6 writers of 0x8f0c11 store unclamped values (pref copies 0x488828/0x484efe, int->byte, literals 2/1); the only clamp on any read is 0x486f30
  `FUN_00423af0(diff,0,6)`, INCLUSIVE (jl/jge/jle), arg = its own register =>
  clamp(6,0,6)=6 => `[6*4+0x94d2ac]` = **0x94d2c4**, the loader's END pointer. OPEN: does FUN_0058e7f0
  (INI reader) admit >=6?
- ACCEPT `python3 -u scripts/m336_cell090_consumer.py` -> **PASS M336: 7/7**, digest
  `f4ca00c55c833539`, 2 runs diff-identical (sha256 bfd16dae81b25723); `python3 -u
  scripts/m336_mutate.py` -> **HARNESS 14/14** `3ec4dd172c69e165`, `--selftest` 4/4.
- **REVIEW (PR #355: 3 P1/7 P2) — 10 accepted, 0 dismissed.** v1's census saw one address form;
  rebuilt as an ADDRESS census (per-block linear-expression eval: base=const+sum(coeff*sym); a site
  counts only if const is field+2 mod stride and all coeffs are stride multiples; unresolved bases
  print as residue, and "only reader" needs residue@+2 EMPTY). New: MU9 algorithm, MU11 walk step,
  MU12 table base, MU13 chain slot, MU14 SECOND alias load INSERTED; the digest hashes PASS bits.
- PITFALL: displacement-keyed censuses miss strength-reduced forms; an O(n) replay per site needs
  a bisect index (180 s).

## Session 319-chain2 (2026-11-24) — M338: the last two #DIFF readers' index provenance

- **ANSWER (pick (x6), final clause):** the seven scaled loads of `0x94d2ac` are now all
  sourced. `0x57c606` (`mov eax,[esi*4+0x94d2ac]`, FUN_0057c550) is a UI list builder: the
  index is the loop counter `esi` — `xor esi,esi` at 0x57c604, the body's only esi write is
  `inc esi` 0x57c6ca, `cmp esi,6`/`jl 0x57c606` -> 0..5, one label per row.
- `0x44a1c8` (FUN_004495e0) indexes with `dl = BYTE[eax+0x20]` (`xor edx,edx` + `mov dl`,
  0 instructions between the load and the index). `eax = [ebp-0x1c]` is a record of the
  **35 x 0x8c buffer at `0x983a10`**, which is **`hallfame.jhh`**: PE strings `rb`@0x689f3c /
  `hallfame.jhh`@0x689f40, `push 0x1324` read, zero-init `5 x 0x8c` per `0x2bc` to `0x984d34`;
  (0x984d34-0x983a10)/0x8c = 35 and 35*0x8c = 0x1324. The record index decodes as
  `(8-1)*(1+4)*4 = 0x8c`.
- **field +0x20 has exactly two writers** in the module: 0x44b15b fills it from
  `BYTE[0x94d438 + 8380*faction]` (fold `shl 6/add/lea*2/shl 4/sub` decoded = 0x20bc; cell =
  faction base 0x94d430 + 8) and 0x44b612 copies it struct-to-struct. `block+8` is the faction's
  **EFFECTIVE DIFFICULTY**: creation 0x59eed6 = `ds:0x985aec` unless the `ds:0x985b10` bit
  selects imm 3; save-load 0x57ef57 stores the save's byte through the same 8380 fold. So the
  reader prints the difficulty NAME of a hall-of-fame entry.
- ACCEPT `python3 -u scripts/m338_diff_readers.py` -> `PASS M338: 8/8 gates`, digest
  `1ae1563d47d0039e`, 2 runs `diff`-identical (sha256 `288a0edc`; `evidence/m338_diff_readers.txt`
  + `_rerun.txt`, 67 lines). Harness `python3 -u scripts/m338_mutate.py` -> **16/16 scored, 0
  MISMATCH, 0 CRASH**, digest `56455db0eadbedd7` (now hashes the MEASURED rows, not the label
  map), incl. REMOVAL/INSERTION/ALGORITHM and the review's MU13-MU15; `--selftest` 3/3
  (`evidence/m338_mutate_selftest.txt:4`).
- **REVIEW (#357, Strata): 10 findings (3 P1/7 P2), all accepted, none dismissed — fixed IN the
  gates**: G4 now asserts the store's SOURCE is eax and no eax clobber before it (MU13); G6's
  module is MEASURED as the 7 functions addressing 0x983a10 (not a typed window); G7 asserts the
  exact 6-instruction branch incl. `jne 0x59eed6` (MU14); G2 reads the loader's base/step/bound
  instead of constants; G5 asserts the fopen/read windows and the exact zero-init sequence; G3
  asserts the full window and no eax clobber (MU15); the esi write classifier is broad
  (lea/pop/xchg/cmov); the harness digest hashes measured outcomes.
- **OPEN:** the +0x20 index is UNCLAMPED (unlike 0x486f40's `FUN_00423af0(0,6)`) — a HoF record
  byte >=6 would read past `0x94d2c4`; whether the INI reader admits a pref >=6 is still open
  (M336). Also OPEN: is 0x44a1c8's big function the HoF screen itself or another list view.
- **Docs:** NAMED cap 247,758 -> **245,265** by rotating `## M326` VERBATIM to
  `docs/named-archive-m338-rows.md:7` (sha1 `a882ee40851d`, pinned in
  `scripts/m338_named_rotate.py --verify`), then +M338 -> 248,542. NEXT_PROMPT got one appended
  result line (chain 1's file is append-only for chain 2).
- PITFALL: a fold decoder keyed on the exact disassembly string crashes on the mutant that
  changes one immediate — decode the immediates and let the gate FAIL instead of asserting the
  text shape.

## Session 319-chain1 (2026-11-24) — B29: the item table DERIVED through M337's loader law

- **ANSWER:** `sim/itemtable.py` replays `0x57a7ef..0x57a899` over `data/alpha.json`: 72 records,
  branch rec 39, 71 iterations, token widths 42/2/27 — all four parsed out of the M337 census and
  REPRODUCED from the file (G2). The derived table equals `sim.economy.upkeep_table` on 38/38 ids
  by name AND upkeep, so `ALPHA_SHIFT = 1` is now a CONSEQUENCE of the loader, not B4's assumption
  (G3; the shift-0 rival differs 22 ids by value and 38/38 by name).
- **B4's four `table-later` DIFFERS rows CLOSED as a convention artifact:** read at the ALPHA
  INDEX the derived table reproduces all four M46 values (Fusion Lab 4, Nanoreplicator 4, Quantum
  Converter 6, Quantum Lab 3), at index+1 zero of four — M46 numbered its rows by alpha line (G5).
  The same convention puts the wrong NAME at all five ids B4 pinned, so one convention cannot
  explain both sets.
- **BOUNDARY:** records 39..71 (33 past the branch) are built and unreachable — the feeder's
  bounds 1..34 charge 0 of them; consumer bound 39 == the branch (G6).
- ACCEPT `python3 -u -m sim.selftest --b29` -> **PASS B29: 9/9**, rows `e4b1c98e68ff8685`,
  print `377094bc16aa8f27`, table `fa829fcd87cf43d5`, alpha sha `bac04f33eb692085`, 2 runs
  byte-identical and the direct entry prints the same text (`evidence/b29_item_table.txt:85-86`);
  `scripts/b29_mutate.py` -> **HARNESS PASS 9/9** `ae1f8e0292a59ed3`, NO-OP `[]`, ST 4/4
  (`evidence/b29_mutate.txt:10`).
- **REUSE:** B28's whole run fed the DERIVED table reproduces its anchors `705a4520c08c4062` /
  `99c52201f073499d` / `38bba29ab857654b` with honest touch `[]` (G7) — nothing loosened.
- NAMED headroom: M334 block rotated VERBATIM to `docs/named-archive-b29-rows.md:5`
  (sha1 `579f90da7d8c`, `scripts/b29_named_rotate.py --verify`); B4's OPEN row and B27's UNMODELED
  row patched in place (the row order is alpha's).
- PITFALL: a value-only rival does NOT discriminate on the five pinned rows (upkeeps 0,0,1,1,1);
  the NAME is the discriminator and G4 prints the rival's 3/5 so the gap is measured, not hidden.

## Session 320-chain1 (2026-11-24) — M340: FUN_0058e7f0 ADMITS a `Difficulty` pref >= 6

- **ANSWER:** the Difficulty path in FUN_0058e7f0 clamps NOTHING. Of its 18 six-arg profile
  reads exactly one carries key 0x692718 = PE `"Difficulty"` (0x58e8a1), default = the itoa(0)
  buffer (push 0x0 @0x58e865), value stored `ds:0x92bde8,eax` @0x58e8c6 — the only store to
  that cell in the function. Insns 0x58e8a9..0x58e8c6 are straight line and eax there IS
  0x6287e2's return (wrappers 0x5ea484/0x5eaa53: 0 jcc, 0 eax write after their call).
- **The chain compares CHARACTER CLASSES only** (atoi 0x64c360, tokeniser 0x5ea985, radix
  0x6287e2/0x628720/0x62876b): constants {0x0,0x1,0x2b,0x2c,0x2d,0x30,0x31,0x36}, and the
  intersection with the value space {2..6} is EMPTY (G4).
- **POSITIVE CONTROL:** the SAME function's `Language` consumer 0x628130 IS bounded —
  `cmp [ebp-0x4],0x4` + `ja` + jump table. Same classifier: bound 4 there, none here (G5).
- **CONSEQUENCE:** 6 rows measured from the ladder's loop bound (0x57c6cb `cmp esi,0x6`);
  k=5 -> 0x94d2c0 last legal, k=6 -> 0x94d2c4 == TABLE_END; the three pref-fed readers
  0x48678f / 0x44a1c8 / 0x599405 index TABLE at scale 4 from MEMORY loads, no clamp (G7).
- ACCEPT `python3 -u scripts/m340_pref_admission.py` -> **PASS M340: 7/7**, rows
  `1cc44d0146a8b419`, census `a7bb50fde374ddca`, window `1ff9a31080ec2e22`, 2nd run
  diff-identical (`evidence/m340_pref_admission.txt:79-90`); `scripts/m340_mutate.py` ->
  **PASS HARNESS M340: 12/12**, 7/7 gates covered, NO-OP `[]` `a2a1726721114b4d`
  (`evidence/m340_mutate.txt:16`), `--selftest` OK.
- **REVIEW #358 (local Strata, 10 findings: 3 P1 / 7 P2), ALL fixed in the gates:** G1 now
  measures the argc-6 push window + the 0x997120 lpDefault (MU10/MU11); G2 pins the cursor
  store cell; G3 proves the call chain 0x58e8b9 -> 0x5ea484 -> 0x5eaa53 -> {0x5ea985,
  0x6287e2} (MU9); G5 reads the whole Language switch shape (argument -> slot -> cmp 4 -> ja
  -> table), not just a stray cmp; G6 MEASURES both endpoints from 0x57ac74/0x57ac88; G7
  proves a def-use gap with no branch/call/compare/rewrite; `m340_named_rotate.py --verify`
  also asserts the full block is gone from NAMED; the M332 stub cites both evidence files and
  says 9/9; the sessions-304-305 archive pointer is repaired.
- **ID:** `milestone/m339` is chain 2's worktree branch (~/reverse/wt-chain2), so this fire
  took M340. NAMED headroom: M332 rotated VERBATIM to `docs/named-archive-m340-rows.md:5`
  (sha1 `3ef265e11aca`, `scripts/m340_named_rotate.py --verify`); M335/M338 OPEN rows
  patched IN PLACE.
- PITFALL: a sub-register write (`mov dl,BYTE PTR [eax+0x20]`) is not "a write to edx" to a
  first-operand test — widen to the register family or the def-use gate finds the earlier
  `xor edx,edx` and reads a bounded index as unclamped for the wrong reason.
