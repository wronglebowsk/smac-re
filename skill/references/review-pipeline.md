# Review pipeline: the lint and the model reviewer

The closing order runs `scripts/review_lint.py --id <id>` BEFORE submit and `scripts/ai_review.py <n>`
AFTER submit; the repo's `docs/AI-REVIEW.md` holds the replay evidence, the scoreboard and the owner
constraints (which endpoint may review, which is backup-only). This file carries the design laws for
both instruments — they are instruments, and every decoration law in `instrument-laws.md` applies.

## Checker design: an exemption is a gate too

Four false-green shapes a review of the checker itself exposes:

- **An exemption keyed on a prose PREFIX is bypassable.** "Rows starting ACCEPT/REVIEW are meta-rows"
  lets any factual claim prefix itself into exemption. Require the prefix AND a structural marker of
  meta-hood in the same row (a harness citation or a digest), and ship a fixture that prefixes a
  factual claim and must still fail.
- **Evidence resolution must be ROW-scoped, not block-wide.** "The digest appears in some cited
  evidence file" passes when the claiming row cites a different file than the one printing it.
  Resolve each digest to the files cited in its own row (plus the last-cited file for bare prose
  mentions), and anchor the matcher on the word `digest` so a stray 16-hex constant is not one.
- **A naming check is not a coverage check.** "The cited mutant id exists in the harness" passes for
  a mutant that reddens an unrelated gate. Add contact: a cited CODE mutant's patch address must
  appear in the instrument source; then DECLARE the semantic remainder (row->gate correspondence)
  in the checker's own docstring as the reviewer's job, so a green lint is never read as full coverage.
- **A citation regex that matches directories crashes the checker.** Require a file suffix in the
  pattern and isfile-guard before opening; ship the directory-shaped citation as a fixture.

Every checker ships fixtures that BITE: one bad fixture per check proving it reddens, plus the
compliant fixture. A checker without biting fixtures is prose. Fixture design has its own trap: a
"bad" fixture that still satisfies the check for an unrelated reason (the bypass row still cites a
valid mutant; the unrelated evidence file happens to be cited in the same row) tests nothing — read
each fixture's failure list and confirm the INTENDED check fired.

## Validating a model reviewer before trusting it

- **Replay known findings against the PRE-FIX diffs before adopting a reviewer.** Take closed review
  rounds with a known finding list, diff the pre-fix heads against their bases, and hand each
  candidate model the diff + repo conventions with NO answer leakage. Score recall per defect CLASS,
  not in total: a reviewer that catches the algorithmic class but misses definition-mismatch (wrong
  measurement endpoint, source-only pins, digest provenance) earns a prompt checklist aimed at that
  class, not rejection. Fresh context matters more than model diversity — the same served model in a
  clean reviewer role catches what the author's own byte-mutants cannot.
- **A thinking model's review can silently truncate at the output cap** (reasoning eats the budget):
  check finish_reason == "length" / completion_tokens >= cap, flag the posted review as TRUNCATED,
  and treat its silences as UNKNOWN, not as clean. Raise the cap for review calls above the chat
  default.
- **Dogfood the reviewer on its own pipeline PR first.** The first production run is the cheapest
  place to find the checker's false-greens; triage every finding it posts about itself before
  trusting it with milestone work.

## Triage

Read EVERY finding body; fix or dismiss each in ONE reply comment; re-measure at head (acceptance
twice + harness); merge only on a real PASS. One review per PR — a re-push buys no second review.
A TRUNCATED review re-run at a higher cap is a COMPLETION of the same review, not a second opinion:
cover both runs' findings in the one reply and say so. A finding about the checker itself (a
false-green path) is fixed by hardening the checker AND adding the biting fixture, never by rewording
the claim. A post-hoc review of an already-merged PR still gets its findings fixed — in the next PR,
with the correction named in the triage comment.

## Arbitrating author-vs-reviewer disputes (the orchestrator's job)

A reviewer is an instrument too, and it errs in both directions: it miscalculates address arithmetic
and it misses pins that exist a few lines away from the one it cited. When an author fire DISMISSES
a P1 with "measured arithmetic" or "the reviewer missed a pin", do not take either side at face value
— re-run the arithmetic yourself and grep the instrument source for the claimed pin before judging.
A dismissal backed by a correct recomputation and an existing pin is legitimate; a quality verdict
built on the review's raw P1 count is wrong when half those P1s are reviewer errors. Report model
quality on the VERIFIED facts, and correct an earlier assessment plainly when the rebuttals check out.
The reverse holds as well: a reviewer P1 the author waves away without numbers is a real defect until
the bytes say otherwise.

## The two layers catch each other's misses

The mechanical lint and the semantic reviewer are complementary, not redundant — each catches a
class the other structurally cannot, observed in both directions on production PRs:
- The semantic reviewer catches CIRCULAR / self-derived gates (a check whose expected set is computed
  from its own input; a hardcoded offset a shift-mutant bypasses so two predicates measure different
  arrays; a "matches" claim that only compares one pair). The lint and the byte-mutant harness pass
  these because the mutants inherit the same wrong constants.
- The mechanical L2b address-contact check catches review-round mutants that patch sites the
  instrument reads only via computed walks — coverage the semantic reviewer missed. Fix by adding
  exact-address pins, then re-measure.
So a green lint is not full coverage and a clean review is not full coverage; the pair is the floor,
and the mutation harness (measured==declared, both directions) is what binds them to the bytes.
