# Workflow — agent loop, git discipline, merge gate

The repo is the memory. A session may end at any moment; anything not committed is lost, and
anything committed must be true. This document is the detailed protocol behind the short
instructions in `AGENTS.md`.

## First thing in a fresh clone

```bash
sh scripts/install_hooks.sh      # blocks direct pushes to main
python3 scripts/index.py build   # search index (needs 192.168.1.213:8000)
python3 scripts/test_loop.py     # proves the gate still fires
```

git does not version `.git/hooks`, so a new clone is unprotected until the first line runs.
GitHub branch protection needs a paid plan for private repos, which makes this hook the only
thing standing between a stray `git push` and an unverified `main`.

## Model

One **milestone** = one question answered (or explicitly narrowed) with evidence, documented in
`SESSION_NOTES.md`, and landed as one squash-merged PR. The loop is:

```
        ┌──────────────────────────────────────────────┐
        │  milestone.py brief                          │
        │   ├─ open PR?  → assess → finish → merge     │
        │   └─ no PR?    → start next queued milestone │
        │                 → one milestone of work      │
        │                 → checkpoint docs            │
        │                 → submit (PR) → stop         │
        └──────────────────────────────────────────────┘
```

Each session performs **one** iteration. Landing a previously opened PR counts as the
iteration — do not land a PR and then start new RE work in the same session.

## Session start

```bash
cd ~/reverse/smac
git fetch origin && git status --short
python3 scripts/milestone.py brief
```

Then read `NEXT_PROMPT.md` in full and `skill_view('smac-cvr-format')`. `NEXT_PROMPT.md` is the
footing: proven facts, verified globals, operational kit, pitfalls. Never re-derive it; if it
contradicts the code, the code wins and the doc gets fixed in the PR.

## Step 2 — assess an open PR

`milestone.py brief` lists open PRs with a verdict derived from CI. The verdict is necessary,
not sufficient: CI checks mechanics, a human/agent judges substance.

Judge against these, in order:

1. **Scope** — does the diff answer exactly one milestone? Two answers ⇒ split.
2. **Honesty** — are claims labelled VERIFIED (disassembly and/or live log lines) vs OPEN /
   INFERRED? A confident claim with no citation is a defect.
3. **Citations** — every `evidence/<file>:<line>` resolves to a line that actually shows what
   is claimed. Spot-check the two or three load-bearing ones by reading the log.
4. **Retractions** — if the milestone killed an earlier claim (see `NAMED.md`), is the old row
   corrected and is the retraction stated? Silent contradictions are the worst failure mode.
5. **Handoff** — could the next agent start from `NEXT_PROMPT.md` alone? Options named,
   footing current, pitfalls added.
6. **Gate** — `python3 scripts/gate.py --base origin/main` is green.

If everything holds: `python3 scripts/milestone.py merge <number>`.
If not, `git checkout <branch>`, finish the work, push; CI reruns. If the PR is unsalvageable
(stale footing, wrong question), close it with a one-line reason and start a fresh milestone —
do not build on a bad base.

## Step 3 — run a milestone

```bash
python3 scripts/milestone.py start M51a
```

Rules that have earned their place:

- **One question.** If the milestone opens two, write the second into `NEXT_PROMPT.md` options.
- **Prove, don't infer.** Static reading narrows the hypothesis; a live watchpoint/breakpoint
  with log lines is the proof. Say which you have.
- **Record the disproof.** Rules out is progress; write what was ruled out and how.
- **Keep evidence.** Logs under `evidence/`, named for the milestone (`m51a_watch.log`), plus
  the generated `.gdb` script when a driver produced it.
- **Stop at one.** Ending after a checkpoint is success, not a shortfall.

## Step 4 — checkpoint

`SESSION_NOTES.md` gets a dated section:

```markdown
## Session 49 (2026-10-22) — M51a: <the claim in one line>

`scripts/m51a_drive.py`, evidence `m51a_*` (round 2350→2351, N OCR).

**VERIFIED (disasm + live):** ...
- cites: `evidence/m51a_watch.log:131`, `:185-192`

**OPEN:** ...
**Pitfall:** ...
Next (options): ...
```

Also: add/correct `NAMED.md` rows; rewrite `NEXT_PROMPT.md` (footing, kit, 3–6 options);
refresh `skill/` if the agent skill changed. Evidence hygiene at checkpoint: cite lines, not
files; digest any log you had to read end-to-end; run `evidence.py prune` if the budget warns.
Full policy: `docs/EVIDENCE.md`.

## Step 5 — submit

```bash
python3 scripts/milestone.py submit --title "M51a: what gates conversion income"
```

The script refuses a red gate, commits, pushes the branch, and opens the PR with the evidence
list. Then the session stops. CI runs the same gate; a human or the next session merges.

## Repo invariants

- `main` is always mergeable and always has a current `NEXT_PROMPT.md`.
- Squash merge only; the PR title becomes the commit message, so it must name the milestone.
- Never commit game binaries, saves, ISOs, or regenerable Ghidra/FLIC output. The gate fails on
  them; `.gitignore` lists them.
- Evidence is append-only. Correcting an old log means adding a new file, not rewriting history.
- `skill/SKILL.md` mirrors `~/.hermes/skills/smac-cvr-format/SKILL.md`; edit live, copy in, gate
  verifies (local runs only — CI cannot see the live skill).

## CI and branch protection

`.github/workflows/gate.yml` runs `scripts/gate.py` on every PR, then `scripts/test_loop.py` —
the gate's own four-case test, so a change that weakens the gate cannot slip through on the
gate's own verdict alone. A red check is visible on the PR and blocks `milestone.py merge`.

GitHub branch protection and rulesets are unavailable on this account: they require GitHub Pro
for private repos. So enforcement is **client-side**: `milestone.py merge` refuses anything but
a GREEN verdict, and `submit` refuses to open a PR from a red gate. That holds for the agent
loop; a human merging in the web UI can still bypass it by intent. Two ways to make it
server-side if ever needed: upgrade the account to Pro, or make the repo public (it holds
reverse-engineering notes, so private is the default choice).

## Failure handling

- **Gate red on main itself** — fix forward with a small `fix/` PR; do not merge feature work on
  top of a broken gate.
- **Game/harness wedged** — the milestone is still submittable if the finding is written and the
  evidence captured; note the harness state in `NEXT_PROMPT.md` so the next session starts clean.
- **PR conflicting** — rebase on `main`, rerun the gate, push (`--force-with-lease` on your own
  branch only).
- **Actions minutes exhausted** — the gate is local-first: run it by hand, state in the PR that
  CI was unavailable, merge only with a green local gate.
