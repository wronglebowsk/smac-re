# Session notes archive — sessions 275-275

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-274-274.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 275 (2026-11-18, STATIC close-out of s274's M311, zero box) - PR #289 review round, clause audit, merge

Same working chain as Session 274 (the fire hit its iteration cap mid-M311, so the review round and the
merge land here rather than back-dating 274). M311 is now MERGED: `#289`, squash `17e3e2e` on `main`.

- FINAL ROUND (same session): instrument now **8/8 gates** (gate **A8** added: the matcher's per-site output is
  pinned as exact triplets, so a mis-transcribed address reddens it - MU4), digest `625cd5877271cd85`, and the
  harness scores **11/11 load-bearing** with the baseline-green precondition (`python3 -u scripts/m311_mutate.py`).
- NEW FINDING from A8: **5 of the 6 selection sites recompute `REC_BASE + 304n`; `0x4f5c36` does not** - it
  re-stores a SAVED pointer read from `[ebp-0x8]` at `0x4f5c33`. One selection path caches the record pointer.
- RETRACTED IN GATE A8 (my prose again, this time caught by a mutant that could not fail): the matcher's
  register-discipline and 24-B proximity clauses are **NOT load-bearing on this binary** - a register-blind
  matcher returns byte-identical results at all 6 sites across windows -24/+32, -24/+90, -24/+144 B. The
  "proximity" effect is purely the analysis window (at -24/+144 B the 0x4e3476 window also contains the next
  function's fold at 0x4e34cc). Claiming a mechanism is load-bearing without a mutant that can see it is the
  same decoration this repo has now punished four times.
- HARNESS HYGIENE, two more failure modes fixed: a mutant whose anchor drifts after a refactor silently
  becomes a NO-OP or a KeyError crash (`MATCH_TRUTH` looked up a deleted store site) - so gates must degrade
  with `.get(st, 0)` and report a wrong COUNT, never crash; and every anchor must be re-read from the current
  source, never quoted from memory.
- PR #289 GREPTILE, 3 P2s, ALL ACCEPTED, and one of them exposed that my *previous* fix was fake:
  1. **`fold_chain` accepted chains that do not compute 304n** - a chained `a != b != c` is not
     pairwise-disequality, and the first step never required its two operands to be the same register.
  2. My skill/notes said `sorted(xs) == sorted(set(xs))` "can never fail" - WRONG: it rejects duplicates.
     Corrected everywhere to "proves uniqueness only, never completeness or agreement with a source".
  3. **My A8 retraction had never been written.** The `str.replace` anchor spanned a `%`-format break in the
     middle of the literal, so it silently no-opped and the shipped evidence still printed the false claim
     ("both load-bearing"). Anchor edits on a contiguous literal, then VERIFY by grepping the artifact for the
     new words - a retraction that didn't land is worse than none, because it makes the doc look cleaned.
- THEN THE AUDIT ITSELF REDDENED, TWICE, ON MY OWN NEW CLAIMS. With the operand clause and the proximity cap
  switched OFF, `fold_chain` returns byte-identical results at all 6 sites over four window sizes: both clauses
  are INERT. And my first response to P2#1 - demanding the second `lea`'s base register equal the register that
  stored to the index - is FALSE at the setter and broke all six sites (the shape is `lea d,[n+n*8]`: OPERANDS
  equal, DESTINATION free). A8 now asserts the audit's actual content: only the window's right-hand reach is
  load-bearing (0x4e4dd0: 0 folds at -24/+32 B, 1 at -24/+90 B), the two inert clauses are declared inert with no
  mutants aimed at them, and the index operand's VALUE is declared UNPROVEN (register names are only a proxy for
  value identity without intervening-write tracking - which I declined to write).
- FINAL: **8/8 gates, 15/15 mutations load-bearing**, digest 625cd5877271cd85 (unchanged through every rewrite -
  the claims moved, the binary did not).
- **MERGED**: PR #289 -> `17e3e2e`. Gate 11 s. Greptile posted 3 P2s on the first head (`2fe6f4a` carries all
  three fixes); no re-review arrived on the second head, and `milestone.py merge` gated on its own rollup
  verdict (GREEN) - recorded honestly, NOT described as a second review pass.
- NEXT_PROMPT trimmed to 11,989 bytes and the retired s272 pick-list paragraph deleted (it duplicated the new
  OPEN PICKS block); SESSION_CURSOR rewritten for the next ANALYSE fire. `track_mode.py` after the merge reads
  `MODE=ANALYSE analyse_since_build=1 last_build=B22 next_rung=B23`, so the next fire ANALYSES; B23 stays QUEUED.
