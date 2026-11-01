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

**Building on an UNMERGED milestone: `start` forks `main` and the predecessor's scripts vanish.** When the
previous milestone ended blocked (its branch never merged), the next one needs that branch's harness, and
`start` will not give it to you. Branch from the predecessor instead: `git checkout -B milestone/<new>
milestone/<prev>`. Order matters when the tree carries uncommitted edits: stash them FIRST, then
`checkout -B`, then pop. A pop performed after a `start` (or after any move to `main`) hits
`error: … deleted by us` for every file the predecessor owns and `main` does not, refuses to drop the stash,
and leaves the index needing a merge — recover with `git reset --hard` (the stash is still there, it is only
kept because the pop refused), then `checkout -B <new> <prev>` and pop again. Two consequences to state in
the session entry: the branch is STACKED, so its PR legitimately contains the predecessor's commits, and the
predecessor's unmerged docs on that branch are what you are editing, not the copies `start` checked out.

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
uncited screenshots (git keeps history, `.prune_log.jsonl` records them). `evidence.py audit
--delete` goes further and drops every uncited file, tracked ones included — **a frame saved for a
not-yet-written classifier test is uncited and dies in that sweep**: cite the path in the session
notes before running audit, and recover anything dropped with `git show <commit>:<path> > <path>`. Policy:
`~/reverse/smac/docs/EVIDENCE.md`.

**Budget gotcha that passes locally and goes RED in CI (M53d).** `evidence.py budget` FAILs
`NEXT_PROMPT.md` above **16,000** chars (warn 12,000; SESSION_NOTES 150k, NAMED 250k) and the in-repo
`skill/SKILL.md` above **70,000 BYTES** — the tool prints a char count, but the caps are enforced on bytes
and 3-byte arrows make bytes > chars, so a file the tool shows as 69,558 "chars" can sit at 70,009 bytes and
fail: measure with `python3 -c "print(len(open(p,'rb').read()))"` before pushing a skill trim, and prefer
cutting whole sentences over rewording (rewording trades characters for characters and the check stays red).
and the CI gate runs `scripts/test_loop.py`, whose case 4 appends **7 chars** to `NEXT_PROMPT.md` — a
prompt at 15,99x is GREEN locally, RED in CI. Keep `NEXT_PROMPT.md` at ≤ ~15,500 (working target; 16,000 is the FAIL) and run
`python3 scripts/test_loop.py` on the anchored branch (never detached HEAD) before `submit`.
`submit` also prunes `SESSION_NOTES.md` and adds a `<MILE>: checkpoint` commit; `merge <pr>` rebuilds
the semantic index. Because that prune rewrites the notes file under you, verify after submit that this
session's section survived (`grep -c '^## Session <N>' SESSION_NOTES.md` == 1) and expect one extra
commit in `git log` that is not yours — do not read that as history having been rewritten.
`--message` becomes the commit message `submit` lands (it rewrites your checkpoint commit's message).
**When the PR is already open, `--title` is silently ignored** — the title stays whatever the first
submit gave it, so a resubmit after a FAIL→PASS flip lands a green head under a stale verdict title:
fix it yourself with `gh pr edit <n> --title` before merging.

**If `gh pr create` (or `submit`) dies with `GraphQL: Something went wrong`, open the PR over REST instead of
re-running submit in a loop.** The branch is already pushed, so only the PR object is missing:
`curl -s -X POST -H "Authorization: bearer $(gh auth token)" -H "Accept: application/vnd.github+json"
https://api.github.com/repos/<owner>/<repo>/pulls -d '{"title":"…","head":"<branch>","base":"main","body":"…"}'`
(HTTP 201 = created; check auth and rate limit first — `gh api rate_limit` — so a genuine credential problem is
not mistaken for this). `gh pr checks <n>` and `milestone.py merge <n>` then work normally. Before merging,
confirm exactly ONE open PR for that head (`gh pr list --head <branch> --state open`) — a retried create can
leave a duplicate.

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
keeps it pointing at the right line). (3) **Build that POST body as a FILE, never as a shell-quoted string.** One apostrophe in
`-d '{"body":"… tail's …"}'` makes bash abort the whole command line at PARSE time, so the `git push` chained
ahead of the curl never runs either and the create that finally reaches GitHub answers **422, `field: head, code:
invalid`** — a 422 on `head` means the branch does not exist yet, not that the body is wrong. The same parse-time abort hits `milestone.py submit --title "<text containing an apostrophe>"` (and `--message`): bash closes the quote mid-argument, so NOTHING in the chained line runs — not even the push — and the error prints only the tail of your own command; re-emitting the title double-quoted (or with the apostrophes dropped) is the fix. Write it with
`python3 -c 'import json; json.dump({"title":…,"head":…,"base":"main","body":…}, open("/tmp/pr.json","w"))'`
then `curl … --data @/tmp/pr.json`, and read the http code: 201 = created, 422 = inspect the `errors` list, which
names the offending field. Keep long prose in a Python variable, not in the shell.

**An amended commit needs a force-push before CI is worth watching.** `git commit --amend` after the branch is
pushed leaves the remote on the OLD sha, so the next `git push origin <branch>` prints a non-fast-forward hint (and
the chain continues, so the PR then gets created from the pre-amend tree); push with `-f` and confirm the PR's
`headRefOid` equals your local `HEAD` before interpreting a check result.

**Poll CI by SHA**: after a follow-up
push (skill sync, `NAMED.md` rows) `gh pr checks <n>` can still report the earlier run — use
`gh pr view <n> --json headRefOid,statusCheckRollup` and merge only when SUCCESS is on the current head
commit. Immediately after a push the same command can print `no checks reported` while the run is
still queueing — wait ~30 s and re-run before concluding CI never triggered.

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
state,mergedAt,mergeCommit`, keep the local tip reachable (`git branch keep/<label> <old-tip>`) — or,
when the stray is a single-file tweak the squash already supersedes, prove that with `git show <stray>
--stat` plus `git cherry main origin/main` and skip the keeper — then
`git checkout main && git reset --hard origin/main` and finish the tail yourself (`python3
scripts/index.py build`; a hard reset also rewrites `SESSION_CURSOR.md` on disk, so re-read it before
rewriting). Prevention is the rule that counts: keep `main` free of local commits so the
pull fast-forwards. Because the squash's parent is the previous `main` tip, ANY local `main` commit
is guaranteed divergence, not a race.

**`main` cannot be pushed at all.** The repo's pre-push hook refuses with `refusing to push to main /
main only moves by squash-merge of a pull request`, so commit-to-main is caught at the push, not only at
`milestone.py`. Do not take the printed `--no-verify` override. A post-merge footing tweak (the
`SESSION_CURSOR.md` line that records `MERGED <n> | next pick`) therefore needs its own branch and PR:
`git checkout -b milestone/<id>cursor` from main, commit, `milestone.py submit --title …`,
`gh pr checks <n>`, `milestone.py merge <n>` — a docs-only PR passes the gate (no SESSION_NOTES/NEXT_PROMPT
change is a WARN, not a FAIL). Leave the content COMMITTED before the first push: pushing an empty branch
(one that equals `main`) and creating the PR afterwards returns 422 `Validation Failed` — there is no diff
to review — and the dangling remote branch must be deleted. Order: write -> commit -> push -> create. Keep the cursor itself to `id | acceptance | merged? | next command`: a cursor that carries the finding text blows the 600 B cap, and every rewrite of the too-long file is another call — name the artefact that holds the detail (`NAMED.md <ID>`, `evidence/<id>_….txt`) instead of quoting it. Leaving it uncommitted instead transfers the cost to the next session,
whose `milestone.py start` refuses the dirty tree; the cheapest option is to write the cursor line BEFORE
the milestone's own commit and let it say what the closing steps are.

**A close written but never committed is the next session's first job, not new work.** When `git status` shows a prior session's closing set uncommitted (a new `SESSION_NOTES.md` section, `NAMED.md` rows, a `NEXT_PROMPT.md` edit, an acceptance's `evidence/*.gdblog`), the milestone is DONE — adopt that close: finish the remaining closing steps (sync the skill, commit, `gate --base main`) and do NOT re-run the acceptance: a second invocation of a one-shot live acceptance confounds or supersedes the recorded verdict, and `milestone.py start` refuses the dirty tree anyway. When a sibling session commits the same close WHILE you are editing it (its commit lands between your reads — `git log` timestamps move mid-turn, the write tool names the sibling), do not re-apply your edits: `git diff HEAD` and commit only the residual delta on top, and never duplicate the sibling's `submit` — one submit per milestone; verify with `gh pr view <n> --json state,headRefOid` before opening another PR.

A session that finds an open PR lands it instead of starting new work. Branch protection is
unavailable (GitHub Pro needed for private repos), so `merge` is the enforcement point — never
merge by hand in the web UI without a green `gate` check. After editing this live skill, sync `SKILL.md` **and** `references/`
with `~/reverse/smac/skill/` and commit: the gate compares only `SKILL.md`, so an edited reference drifts
silently. **Resolve that drift by CONTENT, never by mtime and never by a wholesale copy:** every `git checkout`
(a `milestone.py start`, a `merge`, a hard reset) rewrites the repo copy's mtimes to the checkout time, and a
merged PR can leave the repo copy holding a rule the live skill never received — so the newer-mtime side is
often the content-stale side, and copying it over the other silently reverts tracked findings while the gate's
`skill sync` check still PASSes. Go file by file: `diff -rq` the two dirs; for each differing file restore the
repo side with `git checkout HEAD -- <path>` (git history, not mtime, is the arbiter of what the repo copy is
supposed to contain), re-apply only your own new bullets into it, then copy that file repo -> live so both
sides match byte for byte; finish with `diff -rq` (must be clean) and `git diff --stat HEAD -- skill/` (must
show only your intended additions). If `python3 scripts/evidence.py budget` reports `skill/SKILL.md … FAIL`
(70,000 BYTES — see the budget gotcha above), compress PROSE inside that file until it passes — never raise the
limit; and when it sits within ~50 B of the cap, put the new rule in the reference file SKILL.md already points
at instead of into SKILL.md. Protocol detail: `~/reverse/smac/AGENTS.md` and `docs/WORKFLOW.md`.

## Sibling ownership (a cron dispatch colliding with a live session)

**A cron-dispatched sibling is invisible to those greps**: its shells are children of the gateway process and its
tracked background run shows only as `/bin/bash -lic …` (systemd unit `hermes-worker-proc_<proc-id>.scope`), so read
the files that NAME the owner — `~/.hermes/processes.json` (one record per tracked background run: `command`, `pid`,
`owner_task_id`, `session_key`, `parent_session_id`; an `owner_task_id` of the form `cron:<job>:<exec>` that is not
your session key means the harness running right now is the sibling's) and `~/.hermes/cron/executions.db` (`select
id,job_id,status,started_at,progress_at,pid from executions order by started_at desc limit 5` — `running` with
`progress_at` inside the last minute or two is alive and working NOW). A mtime on `scripts/<harness>.py` or on
`SESSION_CURSOR.md` newer than the last commit is the same verdict, and the game's Wine pid changing under you means
the sibling already relaunched the box. `SESSION_CURSOR.md` records what a session BELIEVED was in flight and is
written by whoever touched it last, so it goes stale in both directions — a finished run still marked RUNNING, or the
next run queued for the sibling while the cursor names yours — so trust the owner files over the cursor, and do not
overwrite a cursor another session wrote.

**When another session owns the box mid-acceptance, the collision report IS the deliverable**: spend ZERO acceptance
invocations, skip the readiness oracle's printed FIX (an enqueue/pane poke lands on THEIR box and confounds their
run), touch no shared doc, commit nothing, and quote the command that produced the ownership verdict. In that state
`gate.py --base main` reads RED on `milestone checkpoint: not updated: SESSION_NOTES.md, NEXT_PROMPT.md` plus
`skill sync` — that is the sibling's unwritten closing order, not a defect to repair by writing their docs for them.

When a sibling owns a mid-run acceptance, serialize — a bounded foreground wait loop on
`pgrep -f '<instrument> --tag <tag>'` — then contribute a **box-free** delta (bytes only, no gdb, no poke) instead of
a second measurement, and push it onto the SIBLING's branch: its open PR picks the new commit up, so never submit a
second PR for one branch. Re-derive the target text from the live file (a terminal `awk NR`/`grep -n` printing only
the matched window) or do the edits in an `execute_code` cell that opens the file fresh, edits by line index and
prints only the byte delta — that route also keeps the file out of context. If the sibling committed the whole close
while you were editing, commit only your residual delta and do not re-submit or re-run the acceptance.
