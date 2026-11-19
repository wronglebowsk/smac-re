# B26 MERGED — post-merge note (Session 301, docs-only, zero box)

**MERGED 2026-11-19**: PR **#328** squash **`dd704d0`** on `main`, branch `milestone/b26`
(head `d5ec615`), CI `gate` **pass 15 s**, `mergeStateStatus CLEAN`.

The landing was mechanical, not scientific: the previous fire had re-measured everything on the
working tree and never committed it (its first attempt did not even run — a 18-arg/17-specifier
`TypeError` in table A's format string). This fire committed the owed edits, verified them again
before pushing, and closed the PR.

- Acceptance, re-run before push: `python3 -u -m sim.selftest --b26` -> **`PASS B26: 10/10
  gates`**, re-run `diff` 0 against `evidence/b26_selftest.txt` (`:63`; run-set anchor
  `ae43e0ab9c8cfc3d` `:52`). Cheap re-verification of the identity block only:
  `python3 -u scripts/b26_mutate.py --entrypoints` -> the committed
  `evidence/b26_mutate.txt:25-30` verbatim, `MU21 ... OK`,
  `PASS B26 ENTRY-POINT IDENTITY: 2/2 checks (MU21 scored)`.
- `python3 scripts/gate.py --base main` -> **GREEN, 0 warnings**;
  `python3 scripts/review_lint.py --id b26` -> **PASS (11 V rows)**.
- `main` had moved under the PR (chain 2's #326 / #329). Force-push is blocked in cron mode, so
  the branch absorbed `origin/main` with a normal merge commit instead of rebasing — push stayed
  a fast-forward. Both chains' doc sections were kept; the two merge conflicts (NEXT_PROMPT.md,
  SESSION_NOTES.md) were resolved by union, and `NEXT_PROMPT.md` was brought back under the
  12,000 B warn cap by rotating its two CLOSED pick rows VERBATIM to `docs/pick-archive.md`
  §trim-s300-chain1 (b) (sha1 `b0e7c1d2614f2312`) while chain 2's fresh M325 row stayed LIVE.
- The squash title carries the POST-review numbers (10/10, 19/19+1, 8/8, 2/2 + MU21) because
  `gh pr edit` was run before the merge — unlike #326/#329, whose titles still carry pre-review
  counts. `gh pr edit` failed on the Projects-classic GraphQL error; `gh api -X PATCH
  repos/<repo>/pulls/328 -f title=...` works.
- One review existed (the local Strata run at `evidence/ai_review/pr328_20261119_200706.md`);
  all 10 findings were triaged in ONE reply
  (`https://github.com/wronglebowsk/smac-re/pull/328#issuecomment-7023033549`), each with the
  re-measured numbers. No re-review: one review per PR.
- Standing debt, stated in `NEXT_PROMPT.md` and `SESSION_CURSOR.md`: **`NAMED.md` is 246,259 B
  against the 250,000 B FAIL line** — `evidence.py budget` exits 1 on a FAIL and that alone
  reddens the gate for whichever fire next grows the registry. Rotate a block VERBATIM into a
  `docs/named-archive-*.md` BEFORE adding (the §B26 precedent: 11,151 B of full-length rows ->
  `docs/named-archive-b26-rows.md`, sha1 `45c2cad67c663308`, one-line rows with the same gates,
  mutants and cites left in the registry).
