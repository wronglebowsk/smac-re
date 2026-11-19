# M325 merged — post-merge note (s300-chain2)

MERGED 2026-11-19: #329 squash **fb6e6c4** on main. Review 2 P1 + 8 P2 triaged in
ONE reply, 10/10 accepted (MIN hardcoded→derived from cmp/jle-skip geometry + MU25;
ENERGY row gated via G5 handler relation + MU26/27; P/U totals gated — reviewer's
40/34 was a miscount, 41/33 stood pre-fix, LIFO-sound pops then upgraded 4 sites to
45/29; 29/29+1 notation; itoa pins MU28; seed-count + BLKCONST-target pins MU29;
LIFO pop pairing MU30; call-crossings enumerated T9; S4 strengthened).

Post-review acceptance 8/8 digest **a623181d7fb68263** x2 + at-head re-measure
byte-identical (`evidence/m325_block220_census.txt:297-298`); harness 30/30
(29 scored + 1 NO-OP) digest **97c193e12593c95e** (`evidence/m325_mutate.txt:33-35`);
selftest 4/4. CI gate pass 13 s, mergeState CLEAN. Main did NOT move under review
(chain 1's B26 still in flight) — no rebase needed.

Governance: the squash title's "24/24+1" is the PRE-review harness count — the
`NAMED ## M325` ACCEPT row governs (30/30, digest 97c193e12593c95e). Digest history:
12e8c53d (initial) → 7b1f0a2b (review_lint L2b site-set pins) → a623181d (review
round). Housekeeping: pr329 ai_review .json sidecar folded into this note's commit.
