# Reusable kickoff prompt — ~/reverse/smac

Substitute `<N>` (the session number), never `<MILESTONE-ID>` from memory: the id is whatever
`python3 scripts/session_brief.py` prints as NEXT. Everything else is per-project constant and
lives in `NEXT_PROMPT.md`; this block is only the discipline, so it stays reusable across
milestones.

---

You are working in `~/reverse/smac` (SMAC reverse-engineering: Ghidra exports plus a Python
driver that plays the game under Wine). Do exactly ONE milestone, then stop. The milestone is NOT
named in this prompt — `python3 scripts/session_brief.py` names it, and the repo wins over any id
carried in from outside (a kickoff that named an already-merged milestone has cost four sessions
in a row their first calls).

FIRST, in this order, before anything else:
1. Read `NEXT_PROMPT.md` in full — it is the footing: the ledger, the pick, the traps, the
   closing order.
2. `tail -80 SESSION_NOTES.md` — the last few sessions only; never read the whole file.
3. `git status`; `git branch --show-current` (must not be `main`);
   `python3 scripts/milestone.py start <MILESTONE-ID>` — it creates the branch off `origin/main`.
   Then `git log --oneline -8`: a commit you did not write means a SIBLING is on this branch —
   reconcile before you measure (never silently adopt a file that changed under you, never repeat
   a claim a foreign commit makes), and keep any untracked deliverable OUTSIDE the worktree, where
   a sibling's `git clean` cannot delete it.
4. `python3 scripts/smac_state.py --json` — read what the box actually holds before touching it.
   Do not trust the footing's description of the state: it can be stale, and it has been.
5. If the state reads impossibly (nonsense types, flags that never clear, zero bases of ours,
   arrays that decode as garbage), do NOT build on it. Report it and reload a known-good save
   first.

NON-NEGOTIABLES
- Acceptance is a script printing `PASS` on ONE real invocation. Never weaken a threshold, a
  floor or a check to make a run pass. If it cannot pass, say so and merge nothing.
- A `PASS` is not an outcome. Before closing, ask whether the thing the milestone cares about
  actually HAPPENED, read back from memory/state — not inferred from the commands you sent.
- Verify in memory, never in screenshots. Write, then read back. Poke, then read the record.
  Press a key, then read the field it should have changed.
- Change ONE variable at a time. If two things changed together (a position AND a tile emptied,
  a setting AND a code path), you have not isolated a cause — write "confounded", not "because".
- When docs and code disagree about a field, offset or constant, settle it from the binary
  accessor (the `*(short *)((int)&DAT_x + off)` cast names width and offset) on a HEALTHY load —
  never from a plausibility score over a degraded state.
- New screen classes / panes go into the classifier tests (with saved frames) BEFORE the driver
  uses them.
- **A gate you have not shown to discriminate is not a gate.** Compute the candidate predictions
  from the baseline BEFORE the run; if your model and your null agree on every candidate, the
  shape is void — fix the shape, do not spend the run.
- **Cap ACCEPTANCE INVOCATIONS at three.** Run it, read WHY it failed, fix the instrument, run it
  again; the third failure IS the finding — write its numbers next to the command, merge nothing,
  close. A dozen invocations with no number burns the evidence along with the budget, and every
  extra run risks the box (a mid-run kill hangs Wine).

CONTEXT DISCIPLINE (this is what kills sessions)
- The window is 524,288 tokens with compaction at 424,000 (doubled 2026-10-28) — verify, do not
  quote: `grep -nE 'context_length|threshold_tokens' ~/.hermes/config.yaml`. A bigger window does
  not repair the compressor (same model, output cap unchanged), so compaction is still not a
  safety net: what runs out is ATTEMPTS.
- Every tool result small: `grep`/`sed` windows, `tail`, `scripts/evidence.py show <f>:<line>`.
  Never `cat` a log or a 40-turn trace — parse it with a short Python snippet.
- No `delegate_task` and no subagents: their reports land mid-turn and cost more than they save.
- Patch documents; never read_file-then-write_file anything over 10 KB.
- Check `python3 scripts/evidence.py budget` BEFORE adding screenshots (the gate FAILs at 30 MB),
  and delete the `*_3x.png` siblings right after running the classifier tests.
- COMMIT EARLY: once a checkpoint is green — and no later than ~60 tool calls —
  `git add -A && git commit -m "<ID>: checkpoint"`. A commit on the branch is the only thing
  that survives an overflow.

CLOSING ORDER (exactly)
1. `## Session <N>` entry in `SESSION_NOTES.md`: what changed, the acceptance numbers WITH the
   command that produced them, what is still open, the next pick.
2. Rewrite `NEXT_PROMPT.md` for the next session — including anything you learned that
   contradicts the old footing — then `wc -c NEXT_PROMPT.md` (must be <= 15,500).
3. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/` (the gate checks the sync).
4. `git add -A && git commit -m "<ID>: checkpoint"`.
5. `python3 scripts/gate.py --base main` — must be GREEN.
6. `python3 scripts/milestone.py submit --title "..."`; note the PR number; `gh pr checks <n>`;
   `python3 scripts/milestone.py merge <n>`.
Then STOP and report.

IF THE CONTEXT WINDOW RUNS OUT
In your very next tool call run `git add -A && git commit -m "<ID>: checkpoint"`, then reply
with what is done and what is not. Do not try to compress and do not rewrite docs to recover.

NEVER
- commit to `main`; `pkill -f` / `pgrep|kill` by name (it matches your own shell); `Escape` on
  the title screen; click OK on "Do you really want to quit?"; `--mode stop`; `file://` with
  `--load`; a `clear`-prefixed command; backticks in a commit message (the shell eats them).
- Report a claim you did not read back. "I verified" means a tool output showed it.

REPORT (one screen)
What changed · the acceptance numbers with the command that produced them · what is open
(including anything you could not verify) · the next pick. No narration of the journey.
