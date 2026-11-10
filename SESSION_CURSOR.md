B16 | scan-loop head pre-check chain NAMED+EXECUTABLE: `python3 -m sim.selftest --b16 programs/saves/m54b_clean.SAV` -> PASS B16 7/7 (evidence/b16_precheck_chain.txt) | merged? NO (branch milestone/b16) | next: 0x4e3c00 no-go (the 8482 pass-static-no-row population) or the 0x51dfe2 cell addr / 0x582cc0 side-effects

## chain status (s245 close)

- PR #258 (`milestone/b16`, B16) is OPEN, gate CI GREEN (`gate` pass 12s),
  Greptile Review PENDING at close-out. This fire hit its tool-iteration cap in
  the audit, so the MERGE RULE's review read did NOT happen and NOTHING was
  merged by it.
- s246's first actions, in order: (1) `gh pr checks 258` until Greptile is not
  pending, then `gh api repos/wronglebowsk/smac-re/pulls/258/comments`; fix every
  P1 or dismiss it in the PR body with one sentence; (2) fix the `load_visits`
  transpose audit finding (SESSION_NOTES Session 245 §245c) and re-run
  `python3 -m sim.selftest --b16 programs/saves/m54b_clean.SAV` (expect 7/7);
  (3) `python3 scripts/milestone.py merge 258`; (4) regenerate this cursor and
  the chain-status section (merged: B0-M294 + B16).
- If #258 is already merged when you read this, re-run the `--b16` selftest to
  confirm 7/7 on main before moving on.
