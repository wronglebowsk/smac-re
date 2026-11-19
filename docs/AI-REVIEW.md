# AI-REVIEW.md — the local review pipeline (s291)

**Why this exists.** Greptile ran out of review credits at #314 ("Your organization has run out of
review credits") — milestone PRs no longer get an external review. Rather than buy credits or merge
unreviewed, the loop now runs a two-layer local pipeline, validated by a replay experiment against
the 8 known findings of #309/#311 before adoption.

## The replay experiment (evidence, not opinion)

Setup: the PRE-FIX heads of #309 (`pr309^`) and #311 (`pr311^`) were diffed against their bases and
handed to two candidate reviewers with a generic adversarial prompt + the repo conventions (as
Greptile had AGENTS.md). The known-finding list was NOT in the prompt. Script + raw outputs:
`evidence/ai_review_replay/replay.py`, `run.log`, `{strata,qwen36}_m31{7,8}.{md,json}`.

Scoreboard (✅ caught, ❌ missed, ⚠️ output truncated at the 8192-token cap):

| finding (Greptile caught all 8) | Strata qwen3.8-flash-next | Qwen3.6-35B (258v) |
|---|---|---|
| F1 per-push trace algorithm bug (#309) | ✅ `strata_m317.md:27-29` | ❌ |
| F2 M250 source-only pin (#309) | ❌ | ❌ |
| F3 constant-compare caller gate (#309) | ✅ `strata_m317.md:7-9,23-25` | ❌ |
| F4 shared harness scratch file (#309) | ⚠️ truncated tail | ❌ |
| F5 citations lack line numbers (#309) | ⚠️ truncated tail | ❌ |
| F6 claimed conditions unpinned (#311) | ✅ `strata_m318.md:3-19` (4 findings) | ❌ |
| F7 reach measured to wrong call (#311) | ❌ | ❌ |
| F8 digest not computed by instrument (#311) | ❌ | ❌ |

What the data says:
- **Fresh-context same-model review catches the algorithmic AND coverage classes** — including the
  deepest finding (F1), which the author's own byte-mutants could not catch. Role separation (read
  backward, no ownership of the prose) does real work; the correlated-blind-spot worry was half wrong.
- **The residual gap is definition-mismatch scrutiny** (F2/F7/F8): wrong endpoint, source-only
  comparison, digest provenance. The production prompt carries an explicit checklist for exactly
  this class (`scripts/ai_review.py` PROMPT).
- Strata also found ~10 genuine defects Greptile missed (ungated `1 ret`, a/s coordinate sites,
  n6 block-scaling, abs identity, cost-gate ordering, memo-store set identity, the docstring's
  "8 owners" vs measured 7, dispatcher window coverage, G3's hidden instruction cap).
- **Qwen3.6-35B is not a viable reviewer**: 0/8, generic fragility padding, misread gates, and a
  repetition collapse on the larger diff (`qwen36_m317.md:148-452` — the same block ~50× to the
  token cap). The 258v endpoint is for light backup tasks only (owner decision, s291).
- Caveats: n=2 PRs / 8 findings, one run per model, substance-matching scored by the closing agent.
  Strata's m317 review hit the 8192 cap (thinking ate the budget) — production uses 16384.

## The pipeline

1. **Mechanical layer — `scripts/review_lint.py --id <id>`** at close, BEFORE submit. Model-independent:
   L1 every VERIFIED claim row names a mutant (ACCEPT/REVIEW meta-rows exempt); L2 cited mutants exist
   in the harness; L3 every quoted digest is printed in a cited evidence file; L4 evidence citations
   carry :line. Fixtures: `scripts/test_review_lint.py` (7/7, each check bites). Pre-law blocks
   (M317/M318) are NOT retroactively rewritten; the law binds from s291 milestones.
2. **Semantic layer — `scripts/ai_review.py <pr>`** after submit. Raw API call to the primary local
   endpoint (Strata, served alias `qwen3.8-flash-next-iq3_xxs`, thinking xhigh, 16384 output cap) —
   fresh context, no session history. Endpoint resolves from `$STRATA_URL` or
   `providers.qwen125b.base_url` in `~/.hermes/config.yaml` (no endpoint committed — gate law).
   Posts findings as a PR comment, saves raw review under `evidence/ai_review/`. `--dry-run` prints
   without posting.
3. **Triage rule unchanged**: read EVERY finding body, fix or dismiss each in ONE reply comment,
   re-measure at head (acceptance twice + harness), merge only on a real PASS. The human owns the
   merge decision.

## Constraints (owner, s291)

- Strata hosts ONLY Qwen-Flash-Next — no model swaps for review diversity; the reviewer is the same
  served model in a fresh context, which the replay validated.
- The 258v (OpenVINO) box is light-backup only; a different OpenVINO-supported model there is a
  FUTURE diversity option for the definition-mismatch class, not part of this pipeline.
- If Greptile credits return, its review runs alongside; the local pipeline stays as the floor.