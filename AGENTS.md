# AGENTS.md — how to work in this repo

Reverse engineering of Sid Meier's Alpha Centauri. Work happens in **one milestone per
branch, landed as one PR**. Full protocol and rationale: `docs/WORKFLOW.md`.

## Every session starts here

```bash
python3 scripts/milestone.py brief
```

That prints the last checkpoint, any open PRs, and the queued milestone options. Then read
`NEXT_PROMPT.md` in full — it carries the current footing, the queued test, verified globals
and the operational pitfalls. Load the project skill: `skill_view('smac-cvr-format')`.

## The loop

1. **Assess the repo.** `milestone.py brief`. If it lists an open PR, that PR is the work.
2. **Land the PR.** Read its diff and its `SESSION_NOTES.md` section. Check that claims are
   marked VERIFIED or OPEN, that every `evidence/<file>:<line>` citation resolves, and that
   `NEXT_PROMPT.md` is rewritten for the next session. Run `python3 scripts/gate.py --base
   origin/main`. If the work is incomplete, check the branch out, finish it, push, and let CI
   rerun. When the gate is green and the checkpoint is honest: `milestone.py merge <n>`.
3. **Start the next milestone.** `milestone.py start M51a` (the next queued option). Do exactly
   one milestone — one question answered, one checkpoint written.
4. **Checkpoint.** Add a dated `## Session` section to `SESSION_NOTES.md` (findings, evidence
   line cites, what was retracted, pitfalls), add or correct rows in `NAMED.md`, rewrite
   `NEXT_PROMPT.md` for the next session, refresh `skill/SKILL.md` if the skill changed.
5. **Submit.** `milestone.py submit`. It refuses a red gate, commits, pushes, and opens the PR
   with the evidence list. Then stop — the session's job is done.

## Definition of done

A milestone is done when a different agent could continue from the repo alone:

- the question is answered, or explicitly narrowed with what was ruled out and why;
- every claim carries VERIFIED (disassembly and/or live log lines) or OPEN/INFERRED;
- evidence files are committed and cited as `path:line`;
- `NEXT_PROMPT.md` names the next 3–6 options with enough footing to start any of them;
- the gate is green.

## Invariants

- One milestone per PR. A PR that mixes two answers gets split, not merged.
- Retractions are findings: when new evidence kills an old claim, say so in the section and
  fix the old row in `NAMED.md`.
- `evidence/` is written under `~/reverse/smac/evidence/`, never `/tmp` — it must survive a reboot.
- Game binaries (`programs/`, `*.exe`, `*.iso`, `*.cvr`, `*.flc`, saves) stay out of git. The
  repo is notes, harness and evidence; point the harness at a local install.
- The live agent skill lives in `~/.hermes/skills/smac-cvr-format`; the tracked copy is
  `skill/`. Edit the live one, then copy it in — the gate fails on drift.
