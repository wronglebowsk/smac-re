<!-- Moved verbatim from SKILL.md (M53Q1, 2026-10-24) to keep the always-loaded file small. -->

## Git workflow (2026-10-22)

Repo `github.com/wronglebowsk/smac-re` (private). One milestone per branch, landed as one PR:

```bash
python3 scripts/milestone.py brief     # state, open PRs (with CI verdict), queued options
python3 scripts/milestone.py start M51a
python3 scripts/gate.py --base origin/main   # must be GREEN
python3 scripts/milestone.py submit     # commit, push, open PR (refuses red gate)
python3 scripts/milestone.py merge <n>  # refuses anything but GREEN
```

**`submit` commits before it checks the branch.** Run it on `main` and it writes a
`main: checkpoint` commit into the tree, then refuses. Undo with `git reset --soft HEAD~1`, branch,
and commit with a real message; always `start <ID>` (or `git checkout -b`) first — but `start` refuses a
dirty tree and an existing branch, so a crashed session's milestone (its branch + untracked `evidence/`)
is resumed by checking it out and finishing that work, never by re-running `start`.

A crashed session usually leaves its parent findings note written while the children's notes were never
produced: grep that note for the `evidence/` files it promises and confirm each one exists before calling
the milestone done. Re-derive inherited line-cites by grepping the instruction address they name — the
gate only checks that the cited line EXISTS, so a cite that drifted to a valid-but-wrong line passes the
gate and misleads the next session.

**Context discipline (262k tokens ≈ 1.05M chars).** Never read a whole `evidence/*.log`:
`python3 scripts/evidence.py show <file>:<line>` prints the cited window, `evidence.py digest
<file>` writes a ~2KB summary to `evidence/digests/`. `evidence.py budget` reports what each doc
costs in context (target: always-loaded ≤6%). `SESSION_NOTES.md` is rotated by
`scripts/session_rotate.py --apply` once it passes 110k chars; `evidence.py prune` removes
uncited screenshots (git keeps history, `.prune_log.jsonl` records them). Policy:
`~/reverse/smac/docs/EVIDENCE.md`.

**Budget gotcha that passes locally and goes RED in CI (M53d).** `evidence.py budget` FAILs
`NEXT_PROMPT.md` above **16,000** chars (warn 12,000; SKILL.md 70k, SESSION_NOTES 150k, NAMED 250k),
and the CI gate runs `scripts/test_loop.py`, whose case 4 appends **7 chars** to `NEXT_PROMPT.md` — a
prompt at 15,99x is GREEN locally, RED in CI. Keep `NEXT_PROMPT.md` at ≤ ~15,500 (working target; 16,000 is the FAIL) and run
`python3 scripts/test_loop.py` on the anchored branch (never detached HEAD) before `submit`.
`submit` also prunes `SESSION_NOTES.md` and adds a `<MILE>: checkpoint` commit; `merge <pr>` rebuilds
the semantic index. Because that prune rewrites the notes file under you, verify after submit that this
session's section survived (`grep -c '^## Session <N>' SESSION_NOTES.md` == 1) and expect one extra
commit in `git log` that is not yours — do not read that as history having been rewritten.

**The gate has two more checks that silently cost a run.** (1) *Address registry*: a milestone that names
a function or pins an address must add `NAMED.md` rows in the same commit, otherwise the gate prints
`[WARN] address registry: NAMED.md untouched` — the verdict stays GREEN and merge still proceeds, so a
WARN is easy to shrug off; the milestone protocol wants 0 warnings, so treat every WARN as an artifact
missing from the same commit.
`NAMED.md` is append-only and too big to rewrite — write the rows to a scratch file and
`cat scratch.md >> NAMED.md` (`write_file` refuses to overwrite a file it has not fully read in the current task — for a whole-file
rewrite write the new text to a scratch path and `mv` it over the target, or do the rewrite in one python
pass; `patch` needs a unique anchor);
rows are `| addr | proposed name | conf | evidence-with-file:line |` and the row is what makes the
function searchable in the semantic index. (2) *Evidence citations*: every `evidence/<file>` cited in the
findings doc must exist on disk, or the citation check drops it (the regex covers only
`.log/.txt/.gdb/.json/.png/.csv`, so an `evidence/x.md:NN` cite is never checked and only your own care
keeps it pointing at the right line). (3) **Poll CI by SHA**: after a follow-up
push (skill sync, `NAMED.md` rows) `gh pr checks <n>` can still report the earlier run — use
`gh pr view <n> --json headRefOid,statusCheckRollup` and merge only when SUCCESS is on the current head
commit.

When a doc is over budget, **delete whole bullets/blocks** (cut from the offending line to the next
`- ` or `## `) — rewording saves ~0 bytes — and re-measure with `python3 scripts/evidence.py budget` — it counts CHARS, and chars do not equal `wc -c` bytes (a file at 15,988 bytes scored 16,052 chars and failed the gate). These docs
**wrap mid-clause**, so an `old_string` copied from a rendered view misses the line break and the edit
fails: do the trim in ONE python pass that either splices whole line ranges (process ranges in
DESCENDING order so earlier line numbers stay valid) or regex-matches with `\s*\n\s*` wherever a wrap can
sit, and assert each pattern matched exactly once (`subn(..., count=1)`, check `n == 1`) rather than
assuming it did.

**Semantic search** (`docs/SEARCH.md`): `python3 scripts/index.py search "<question>"`
returns `file:line` / addresses for notes and named functions; `merge` rebuilds it
(incremental ~1 s, cold ~35 s) and is fail-soft when the embedding endpoint
(`$EMBEDDING_URL`) is down. A hit is a lead, never evidence.
Only **2,786 of 10,284** functions are indexed — those carrying a `NAMED.md` row, string refs,
data refs or ≥6 callees. Boilerplate bodies (`FUN_x calls FUN_x`) embed to near-identical vectors
and are excluded; `--all` adds them back and makes results worse. **Naming a function in
`NAMED.md` is what makes it findable** — the build folds the row into the chunk. Scores run
0.65–0.81 for anything, so read the rank, not the absolute number. Build/index design rules:
> skill `semantic-search-index`. Unnamed functions are labelled once by the local 125B
> (`scripts/summarize.py`, cache `index/summaries.jsonl`, ~1.7 h for 2,786, resumable); rerun
> only when bodies change.

**A checkpoint branch is not reliably pushable by hand.** `git push origin milestone/<id>` on a branch that has no PR can be declined by the remote's pre-receive hook — the commonest cause is a blob over GitHub's 100 MB per-file limit sitting in the branch's HISTORY, which a later delete commit does not remove. So: downsample/throttle big generated files BEFORE their first commit, treat the local checkpoint commit (not the push) as the durability mechanism for an unmerged milestone, and expect `milestone.py submit` to be the path that lands the branch.

**When a push IS declined for oversized blobs, strip them from the branch's own history rather than
re-committing.** First list what is actually being pushed — the local gate's tracked-size check inspects
the tree and PASSes while the push fails, so this scan is the only thing that sees history blobs:
`git rev-list --objects --no-merges origin/main..HEAD | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1=="blob" && $3>20000000 {printf "%.1f MB %s\n", $3/1048576, $4}' | sort -rn`.
Then `FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --force --index-filter 'git rm -q --cached --ignore-unmatch <path> [<path> …]' -- origin/main..HEAD`
(only the branch's own commits are rewritten, so the new SHAs are safe while unpushed). Two traps:
(1) an `--index-filter` removes EVERY version of a path, including a small stub of the same path that
HEAD still needs — filter-branch then drops it from the worktree too, so restore it
(`git show refs/original/refs/heads/<branch>:<path> > <path>`) and commit it; a small blob re-added in a
later commit does not resurrect the giant one. (2) Re-run the blob scan and confirm it is empty before
re-submitting, otherwise the same hook rejects the push again.

**A squash merge makes local `main` a liability if it carries any local-only commit.** `merge <n>` runs
`gh pr merge --squash --delete-branch` (which LANDS the PR) and only THEN `git checkout main && git pull
--ff-only`; a `main` holding a commit the squash folded in — a stray cursor or checkpoint commit — makes
that pull print `Not possible to fast-forward, aborting`, so the command exits non-zero AFTER the work is
already merged and never rebuilds the index. Do not re-merge: confirm with `gh pr view <n> --json
state,mergedAt,mergeCommit`, keep the local tip reachable (`git branch keep/<label> <old-tip>`), then
`git checkout main && git reset --hard origin/main` and finish the tail yourself (`python3
scripts/index.py build`). Prevention is the rule that counts: keep `main` free of local commits so the
pull fast-forwards. Because the squash's parent is the previous `main` tip, ANY local `main` commit
is guaranteed divergence, not a race.

**A close written but never committed is the next session's first job, not new work.** When `git status` shows a prior session's closing set uncommitted (a new `SESSION_NOTES.md` section, `NAMED.md` rows, a `NEXT_PROMPT.md` edit, an acceptance's `evidence/*.gdblog`), the milestone is DONE — adopt that close: finish the remaining closing steps (sync the skill, commit, `gate --base main`) and do NOT re-run the acceptance: a second invocation of a one-shot live acceptance confounds or supersedes the recorded verdict, and `milestone.py start` refuses the dirty tree anyway. When a sibling session commits the same close WHILE you are editing it (its commit lands between your reads — `git log` timestamps move mid-turn, the write tool names the sibling), do not re-apply your edits: `git diff HEAD` and commit only the residual delta on top, and never duplicate the sibling's `submit` — one submit per milestone; verify with `gh pr view <n> --json state,headRefOid` before opening another PR.

A session that finds an open PR lands it instead of starting new work. Branch protection is
unavailable (GitHub Pro needed for private repos), so `merge` is the enforcement point — never
merge by hand in the web UI without a green `gate` check. After editing this live skill, copy the whole
dir — `SKILL.md` **and** `references/` — to `~/reverse/smac/skill/` and commit: the gate compares only
`SKILL.md`, so an edited reference drifts silently. Protocol detail:
`~/reverse/smac/AGENTS.md` and `docs/WORKFLOW.md`.
