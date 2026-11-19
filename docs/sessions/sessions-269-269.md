# Session notes archive — sessions 269-269

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-268-268.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 269 (2026-11-16, ANALYSE M308 review round, zero box) - PR #281's four P2s were all correct; the repaired gates are now MEASURED load-bearing (8/8 mutations redden their checks, 36/36), and the 75-entry sibling is adjacent to the site list, not an overflow of it

- WHAT THIS FIRE IS: the review round of the PR #281 that s268 left unmerged because Greptile found
  4 P2s of one shape - an assertion that could PASS ON AN UNMEASURED STATE. All four fixed, none by
  weakening a check.
- ACCEPTANCE: `python3 -u scripts/m308_site_list.py` -> **36/36 checks OK, exit 0**, `evidence/
  m308_site_list.txt:316,318` (22,680 B); rerun stdout-vs-evidence `diff` = **0 lines**. Second
  acceptance `python3 -u scripts/m308_mutate.py` -> **`8/8 mutations reddened their target checks`,
  `RESULT: PASS M308 gates are load-bearing`**, `evidence/m308_mutate.txt`.
- P2a (classifier blind to `mov eax,ds:0x985ae8`): the operand classifier now matches direct
  `ds:`/`fs:` forms as well as bracketed ones. A4 RE-TRACKORED to the honest claim - the only
  out-of-frame, out-of-window memory in the pair is ONE named global READ, `ds:0x985ae8`, 0 stores
  to it (`:90,96`; 480 direct-globals=['0x985ae8'], 630=[]); A4b asserts stack, site AND global all
  classify non-empty in the same run, so a blind classifier cannot pass.
- P2b (bounds pre-filtered to the expected 0x19/0x4b/0x10): S3 is now BACK-EDGE detection (a jcc
  whose target is at or below itself) + an UNFILTERED immediate inventory of each function
  (`:100-111`). A12 fails unless 480/630 have exactly 2/1 back-edges with bound {0x19}, step {0x10}
  AND no cmp bound above 0x19 anywhere AND 0x4b absent from the whole inventory; A32 records that
  21 of 480's immediates (`0x3e8, 0x14, 0x18, 0x673850, 0xffffffff`...) are ones the old regexes
  DISCARDED, which is the proof the scan is really unfiltered.
- P2c (mnemonic presence in place of the rule): A9/A10/A11 read operands + BRANCH TARGETS. A9: the
  +2 short is movsx'd, that register is the cmp's LHS, the `jg` target == the instruction AFTER the
  `mov lhs,rhs` fallback (that is what makes it a max), the store-back is a WORD of the cmp's own
  register, and the cmp's RHS def-walks to `DWORD PTR [ebp+0x10]` (`:128-141`). A10: 1000 is an
  `and r,0x3e8` on the register the setge/dec wrote (the setge fed by the same-kind test), the free
  slot's `jl` skips the priority cmp, the 1000 arm's `jne` skips the `20-prio` sub, the strict guard
  is `jle` and its target is ONE PAST BOTH update stores (a tie therefore keeps the first index),
  and both priority operands def-walk to `movsx WORD PTR` of the same field (`:143-165`). A11: the
  `jl` lands on a store-free epilogue run and passes over exactly the 4 insert stores
  0x56d551/5b/61/6b (`:167-169`).
- P2d (mirror proved by instruction proximity): a real backward def-walk (`def_producer`/
  `def_globals`, sub-register aliases resolved: AL counts as EAX) over the stored register, bounded
  by the function span from ghidra_out/index.csv. 0x57c5af LOADS ds:0x92bde8 (3 instructions
  walked), 0x57c7b5 is a CO-STORE (the same eax stored to ds:0x92bde8 at 0x57c7b0, no write to eax
  between), 0x57f006 closes on `movsx eax,BYTE PTR ds:0x8f0c11` (`:260,265,275`), and 0x4ddcf1 is
  now DECLARED unattributed - the walk hits a call and the previous dumped insn is a `ret`, so the
  value arrives from outside the walk (`:253`, A28c). A28b is the anti-disguise gate: a walk-closed
  writer must resolve to ONE numeric global and the 10-insn window must name STRICTLY MORE
  candidates for every such writer.
- NEW FACT (was a RIVAL, now arithmetic): the 75-entry sibling at 0x94ee28 ends EXACTLY where the
  25-entry site list begins - 0x94ee28 + 75*0x10 == 0x94f2d8 - so the two are adjacent arrays of one
  8380-B block record (100 x 16 B), not one list overflowing (A13, `:293`). 690's two leas
  (0x94ee2a, 0x94f2dc) and its counter inits {25,75} are printed at `:108-111`.
- RETRACTION: NAMED ## M308's "2 provably mirror ds:0x92bde8" row said provably on proximity
  evidence; the proof is now the def-walk, and 1 of the 4 writers is provably NOT attributable in
  function. Row re-grounded in place, evidence cites refreshed to the new line numbers.
- PITFALL (own, found by the harness): 3 of my NEW sub-conditions were themselves decorative -
  mutating them reddened nothing, because I mutated a dict ENTRY that the assert then read as a
  whole. The fix was to mutate a MEASURED fact so it is false on the real bytes (e.g. compare the
  jg target off-by-one), which is what `m308_mutate.py` does. Keep mutation ids OUTSIDE the
  instrument's A-numbers (M1..M8 vs A1..A36) or the check-name parser confuses them.
