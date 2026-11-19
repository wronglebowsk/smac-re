# Session notes archive — sessions 274-274

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-273-273.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 274 (2026-11-17, STATIC, zero box) - M311: ds:0x68cbb0 is the CURRENT-RECORD INDEX; ds:0x8f0d60 its derived 304-B record pointer
- THE PICK from the s273 handoff, list item (a) `ds:0x68cbb0` (340 xrefs, exactly 6 stores). **It swallowed
  list item (b)**: the "304-B table at `0x95da40`" is `0x95da10 + 48` - the same array, one field in.
- `python3 -u scripts/m311_recidx.py` -> **PASS M311: 8/8 gates**, rc 0, two runs byte-identical,
  `census digest 625cd5877271cd85`; evidence `evidence/m311_recidx.txt`. (The FIRST green run this
  session was 7/7 at digest `dd0ddccb5a1bcad4`; gate **A8** and the matcher's operand clause came after
  the PR #289 review, so those numbers are superseded, not additional.)
- FINDINGS: 6 stores / 16 tests / 318 reads = 340 refs (the field IS compared, so no read-only-cursor story);
  the pointer `ds:0x8f0d60` has exactly 6 stores and pairs 1:1 with the index stores at +6..+25 B; the stride
  is the encoding's own `lea [n+n*8]` ; `lea [n+d*2]` ; `shl 0x4` = 304n over the base `0x95da10`; the setter
  `FUN_004e3470` is 34 B / 11 insns / 57 callers and does store-fold-store; `ds:0x68cbb4` (22 stores, only 3
  in-window) is a SEPARATE field and the pairing invariant is explicitly refused for it.
- FIVE DEFECTS OF MY OWN, all found before submission and all now skill law:
  1. mis-counted the pointer's stores as 5 (the census print scrolled past one) - transcription lists are CLAIMS;
     A2 now requires `sorted(transcribed) == sorted(cache-derived)`, and MU2 (delete one) reddens it;
  2. bad arithmetic - I first wrote the fold as n*9*16 = 144n; it is (n+(n+n*8)*2)<<4 = 304n;
  3. a fold matcher that required adjacency the compiler does not provide (pushes interleave at `0x4f5a85`);
  4. a gate sub-condition of the form `sorted(xs) == sorted(set(xs))` - I called that a tautology that can
     never fail; **review P2 on PR #289 corrected me** - it does reject duplicates, but it proves only
     uniqueness, never completeness or agreement with an independent source, so it guarded nothing here;
     replaced with claim-vs-containment; and MU11 proved the sibling defect: "57 callers" sat in the prose while
     the gate never read `n_callers`, so asserting 58 was inert until the gate read `index.csv`;
  5. a splice of mine deleted its own definition block and a `%`-format argument list drifted out of order -
     nested `%` inside a join is the failure mode; gate messages now build pre-computed strings.
- MUTATION HARNESS `scripts/m311_mutate.py`: baseline-green precondition, traceback mutants rejected, FAIL
  summary searched in stdout+stderr. First score **9/11** - MU2 was a dead anchor (a comment I had added moved
  the literal) and MU4 (relaxing the matcher's scan order) was genuinely WEAK. Fixed by adding a distance-cap
  mutant and a shift-width mutant and by PINNING the three fold triplets in A3 so attribution is falsifiable.
- M311 **MERGED**: PR #289, squash `17e3e2e` on `main` (gate 11 s; 3 Greptile P2s read and all three applied in-commit `2fe6f4a`; no re-review arrived on the second head, so merge.py's rollup verdict GREEN was the precondition - recorded honestly, not claimed as a review pass).
