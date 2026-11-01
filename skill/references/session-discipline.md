# Session discipline: budget, context ceiling, closing and handoff

Moved out of `SKILL.md` when that file bound its 70,000-BYTE cap a second time (2026-10-31). SKILL.md keeps the
RULES; this file keeps the measured detail and the traps. Load it when a session runs heavy, when a doc cap
binds, or when two sessions share the repo.

### The context ceiling is part of the task, not an accident

Hermes' compressor resolves to the MAIN model (`auxiliary.compression: provider: auto`) and cannot
summarize itself: attempts die on the output cap (`finish_reason=length`, aborted, ~132 s each) and the
gateway drops hygiene compression after a 10 s turn-hold. Measured outcome: CLOSING turns were cut
mid-sentence twice — the milestone was done and accepted, the paperwork never landed. Rules that follow:

- The window was DOUBLED to 524,288 tokens (`compression.threshold_tokens: 424,000`).
  Never quote a limit carried in from a prior session — read `~/.hermes/config.yaml`. A bigger window
  does NOT repair the compressor (same model, same cap); every rule here still holds.
- Budget by TOOL CALLS, not by feel: brief+accept_ready <= 6, milestone 6-30, **commit a
  checkpoint by ~15**, stop measuring at 30-40, close at 40-50.
- **Size a batch by instrument, not by ambition.** 3 milestones is comfortable, 5 is the ceiling and only when they
  share ONE instrument and one script (five field probes through a single `field_census`-style tool: one write, one
  run, one evidence file, one PR) — inside that one PR keep ONE commit and ONE registry block per milestone id, since
  the registry rows are what make each finding findable later, and split the PR only when a member needs its own
  acceptance. Unrelated milestones each cost their own harness, so 5 unrelated ones is really 5
  batches. Box-time milestones go **ONE per batch** — each is a 6-10 min window holding a three-invocation cap, and a
  mid-batch wedge strands every milestone queued behind it. State the batch size in the kickoff's BUDGET section so the
  next session does not re-learn it.
- **When he asks for a big number ("do 10", "do 20"), answer with capacity first and then change the ARTEFACT, not the
  quality claim.** Ten means ten homogeneous CENSUSES through one script (one write, one run, one evidence file).
  Twenty means ONE generated artefact with a mechanical, re-derivable selection rule (e.g. the top-20 displacements by
  reference count, emitted as a table), because twenty claimed MEANINGS would be fiction — say so in the artefact's own
  legend, label rows shape-only, and let a dash mean unnamed. State the ceiling out loud: a batch that size buys a map,
  and the next session spends it. Run the archive pass BEFORE such a batch (the pick file's cap binds at exactly that
  size) and expect it to be full again afterwards.
- **Cap ACCEPTANCE INVOCATIONS at three** (this budget is about judgment, not context): read WHY it
  failed, fix the instrument, re-run; the third failure IS the finding — write its numbers next to the
  command that produced them and close. When the failure was a harness PARSE or GROUPING bug, re-run the
  FIXED parser over the failed run's log before spending the next invocation: the events may already
  prove the model, and the fresh run is then only needed to make ONE invocation print PASS. A dozen runs with no number burns evidence AND budget, and
  every extra run risks the box (a mid-run kill hangs Wine).
- Past ~150k tokens the session is finishing something, not starting it — terse closing only.
- Before any step that can exceed ~2 minutes (gdb run, relaunch, evidence audit), overwrite
  `SESSION_CURSOR.md` (<= 600 B: id | acceptance | merged? | next command). Nothing else records
  what was in flight; a cut turn costs the next session one read instead of a re-derivation.
- Write docs by append or by <= 2 KB patch. Never read-then-rewrite a file over 10 KB.


When a session turns heavy he asks for a **paste-ready resume prompt** for the next one.
Write it as a self-contained block, not a chat summary: first actions (skill_view + which
files to read), current footing (what is proven, do not re-derive), in-flight work with the
exact verify/rerun command, ONE-milestone options, the operational kit (launch command,
preflight, coordinates/OCR rules), and the report style. It must work for an agent that has
none of this conversation. A reusable, milestone-agnostic version of that block lives in
`templates/session-kickoff.md` — copy it, substitute the session number, and take the milestone id
from `session_brief.py` (a pasted prompt that names one is usually stale).

When Paul asks for the loop to be **scheduled** rather than pasted, the cron prompt must NOT bake the
milestone id: read it from `NEXT_PROMPT.md` (`## THE PICK`, else the first open `## STILL OPEN` item),
stop rather than invent when nothing is open, and refuse a competing measurement while
`SESSION_CURSOR.md` says a run is in flight, and the cursor is only a hint — a cron-supplied kickoff and a pasted one can both be mid-run at once, so prove ownership from `~/.hermes/processes.json` and the cron `executions` table before you refuse (or start) — the box is one Wine process, so a second gdb attach or
mineral poke confounds the first run.
Copy **`templates/cron-milestone-loop.md`** — the working prompt, validated end to end (one fire produced a
cap-triage PR plus a three-milestone batch, all PASS, merged). It front-loads `evidence.py budget` so the cap
triage lands as its own PR, takes the pick from the file, proves ownership, caps the batch, uses
`sudo -n smac_preflight.py`, and ends in the exact closing order with merge-only-on-PASS. **Reuse the existing job
instead of creating a near-duplicate** — `cronjob_manage` action `update` with prompt, schedule, `skills`,
`continuity: true`, `workdir`, then `resume`; a paused job from months ago is the same loop and its history is worth
keeping.
**Size the cadence from the work, then cut the work.** Measured fires: a static three-milestone batch is 26-29 min,
a cap-triage-plus-batch fire 26.5, and a box fire 70-113 — so a 90 m interval lands every fire on fresh state, while a
30 m interval is only sane because the collision path costs ~4 calls and stops. The real lever is the FIRE, not the
interval: **one PR per fire** (a cap-triage fire lands the triage and STOPS — two PRs means two CI waits, 6-10 min of the
fire), **up to five static milestones through ONE census script**, and **`skills: []` on the job** — attaching the 55 KB
skill re-prefills ~16 k tokens before every fire's first tool call while the kickoff prompt already carries the binding
rules; the prompt instead NAMES the one reference to load (`code-atlas`, `static-store-census`, `instrument-laws`,
`wine-operations`, `production-queue`). Say the trade-off out loud instead of silently shortening the interval.
**A fire's completion block is a self-report.** `Result: ok` means the job process exited 0, not that a milestone
passed. Verify it like any delegated decode: re-run the instrument it shipped (ONE invocation must print
`SUMMARY ... =PASS`), read its `NAMED.md` block against the claim, and run `evidence.py budget` to see whether the
doc surgery actually landed. Then check whether it QUALIFIED an earlier finding in `SESSION_NOTES.md` but left that
finding's registry block asserting the old claim — the registry is what the next session greps, so land the small
docs PR yourself if it did.

### Observe the loop by hand (shadow-run a fire)

To answer "is the loop working as intended", run its prompt in a real session rather than waiting for the tick:

1. `cronjob_manage action=pause`. A pause does **not** stop a live fire — read the cron `executions` table for
   `status='running'` and the `external-worker` pids first, or two workers share one repo and one Wine process.
2. Launch a PTY background session in the repo on the loop's own model:
   `terminal(command="cd <repo> && hermes chat --yolo --provider <p> -m <m>", background=true, pty=true)`, then
   `process_manage action=submit` the kickoff. Copy the live prompt OUT of `~/.hermes/cron/jobs.json` and sha256 it
   against the job — a hand-typed copy tests a prompt nobody runs. An explicit `--provider/-m` matters: a `/model`
   switch in the chat is a per-session override and the next fire still takes the config default.
3. Observe the TRACE, not the screen: `select id,role,tool_name,tool_calls,content from messages where session_id=…`
   in `~/.hermes/state.db` prints the clean call list; the PTY log is mostly spinner noise. Per-call context comes
   from `agent.log` (`API call #N … in= out=`), which is what shows a fire running out of window.
4. Steer with `process_manage action=submit` — the message lands after the next tool call, so a mid-flight "commit
   now" is heard. How the model recovers from a steer is itself the finding worth recording.
5. Verify the outcome off-repo (`git log`, the evidence file, `gh pr view`), then `/exit`; a shadow run leaves no PR
   of its own.

"As intended" for THIS loop, in order: `track_mode.py`'s verdict is the one the fire acted on; the doc cap was
checked before the pick; a branch plus a census-SKELETON commit exist before any probing; a write rejected for a
missing `path` was retried as pure JSON instead of fragmented; the box debt was paid or named; and the close ended in
a merged PR with `NEXT_PROMPT.md` under 15,300 B.

**Answer state questions from live state, never from what you did earlier in the session.** "Should we resume the
cron?" is answered by `jobs.json` (`state`, `enabled`, `next_run_at`) plus the newest `executions` row — a job resumed
an hour ago is still running, and offering to resume it reads as not having looked.

Keep every tool result small:
grep the **`ghidra_out/` corpus** or the saved `*.pseudocode.txt` / `*.json` dumps in
`~/reverse/smac/` instead of re-dumping; page Ghidra facets in small slices; reuse saved
screenshots and take a new one only after a real state change.

### Close before you hand off (the handoff is what overflows)

A one-milestone turn routinely runs 130-150 tool calls. The 524,288-token window is not the binding
constraint — the handoff is: the largest single generation of a turn and the step that strands a
finished milestone on a dirty branch. Order the ending, every time:

1. gate GREEN
2. `SESSION_NOTES.md` entry (patch, never a full rewrite)
3. **checkpoint commit** (`git commit -am '<ID>: checkpoint'` — this repo already uses those)
4. `NEXT_PROMPT.md` rewrite, then `wc -c NEXT_PROMPT.md`
5. submit/PR, then stop

Never leave the commit until after the handoff docs. The prompt rewrite is the single largest generation
of a turn and its tool-call arguments re-enter the prompt, so an overflow there strands everything on a
dirty branch — `git log main..HEAD` empty, `milestone.py` never closed, the whole milestone uncommitted.

- The `NEXT_PROMPT.md` 15,500-byte cap is a hard budget (gate fails at 16,000); draft to ~15.2 k on the FIRST
  write — patching an over-budget file down costs ~1 call per 100 B. When an edit ADDS text, pair it in the
  same call with a compensating deletion (retire the oldest ledger paragraph or a stale box bullet), and
  measure BEFORE the first patch: a file already over the cap makes the edit net-negative.
  **Trust only `python3 scripts/evidence.py budget`** — it prints `os.path.getsize`, i.e. exactly `wc -c` BYTES (the
  column header says `bytes`; an earlier version of this line said "chars" and was wrong — the instrument was right,
  the prose was not, and 14,018 bytes measured 14,018). **Leave >100 bytes of headroom**: `scripts/test_loop.py` appends a few bytes to
  the prompt in a throwaway worktree, so 15,996 makes CI's case 4 FAIL while local `gate.py` is GREEN —
  reproduce with `python3 scripts/test_loop.py` (it prints the failing case) rather than re-running the gate;
  worktrees check out HEAD, so commit an uncommitted trim first. That budget run also names the offending
  doc and its limit, which is faster than guessing. Trim by DELETING whole sentences: rewording and
  re-flowing trade characters for characters (joining wrapped lines saves 1 B/line, not the paragraph width)
  and the check stays red. Well over, move footing into `FOOTING.md` or a `references/` file and leave a
  pointer (session 75 did this with the M48d->M53s rebuild model).
  **Confirm the edit LANDED, not just that it measured well.** Build the replacement AND write it in the SAME
  `execute_code` cell. A cell that computes the new text, prints its size and defers the write loses it — the
  next cell re-reads from disk and rewrites the OLD content. The SILENT half of this trap is `.replace()`: on a
  hard-wrapped target the old string does not match, `.replace` returns its input unchanged, the size check still
  passes (the file really IS under budget) and the write lands the OLD text again. So anchor by INDEX —
  `i = t.index('<heading or first words>')`, `j = t.index('<next heading>')`, `t = t[:i] + new + t[j:]` — and
  `assert '<a phrase from the new text>' in t` BEFORE writing, then `grep` the file afterwards. The checkpoint
  gate names the miss (`not updated: NEXT_PROMPT.md`): read that line as "the write never landed", not as a
  stale-file complaint. Two corollaries that bite repeatedly: a cell that measures OVER budget writes NOTHING, so
  trim inside that SAME cell — the next cell re-reads the OLD text, its `.replace` no-ops, and the size check then
  passes on text you only thought you had replaced; and anchor on a heading you just grepped in the file, not one you
  remember writing — after two rewrites of the same section the remembered heading string no longer exists and
  `t.index()` raises before any edit is attempted.
- **Every always-loaded doc has its OWN cap, and the registry is the one that surprises you.** `evidence.py
  budget` prints a per-file verdict: `NEXT_PROMPT.md` fails at 16,000 chars, `NAMED.md` warns at 150,000 and
  FAILs at 250,000, the in-repo `skill/SKILL.md` has a hard cap of its own. A milestone that appends four
  registry blocks turns the gate RED on a file nobody edited by hand. When the registry is tight, CONSOLIDATE
  YOUR OWN same-session blocks (newest, most redundant, and yours to merge) into one shorter block that keeps
  every number; never trim an older session's rows — that history is not reconstructible. Then re-run `budget`,
  because the gate's budget check reads only that tool's output. Consolidation buys a few hundred bytes; when a cap
  binds for a SECOND session, **SPLIT instead of shaving**: move the settled era into a topical archive
  (`docs/pick-archive.md` = the milestone narrative + the full trap text, `docs/named-archive-<era>.md` = the settled
  registry blocks) and leave the live file holding the RULES plus a pointer to it. A split turns 195 B of headroom
  into ~2.5 kB and 238 B into ~180 kB. Rules that keep a move honest: verify it LINE BY LINE against the archive
  (count of moved lines missing must be 0), make both files name each other so a reader grepping one is told the
  other exists, and land the move as one commit so git records it as a rename rather than a deletion.
- For docs >10 KB `patch` anchored sections instead of `read_file`-then-`write_file`: the write guard
  forces a full read and the rewrite emits the whole file back into context, twice the cost at the exact
  moment the window is tightest. In a HARD-WRAPPED doc, exact multi-line strings miss on the line breaks:
  build the search pattern by joining the tokens with `\s+` in a regex and apply several edits inside one
  `execute_code` cell that prints only the size delta — the file never enters context and a wrapped
  section lands on the first try. **Never write a file through `open(p,"w").write(open(p).read()…)`:** the
  write-open truncates the file BEFORE the read is evaluated, so that one-liner replaces any file with 0 bytes and
  reports success — read into a variable first, then open for write (a fresh 10 KB harness died this way
  mid-session and had to be rebuilt from the conversation). It recurred after this rule was already written, so add the
  cheap detector rather than trusting care: after ANY such one-liner, `assert os.path.getsize(p) > 0` in the same cell.
  An untracked file cannot be recovered from git — only from the conversation — so create new harnesses with `write_file`
  and patch them with `patch`, using a Python one-liner only for edits to a file git already tracks.
- **A gdb breakpoint that reads the WRONG register prints garbage and can kill the whole run**: the printf fault (`Cannot access memory at address 0xa774`) aborts the breakpoint's commands block and gdb DETACHES the inferior, so the run dies mid-window. Read the store's own bytes first — `mov eax,[ebp-0x4]` followed by `mov [eax+0xa774],-1` means the object is in EAX at that address, whatever the pseudo-code called it. The same trap applies to SIGNS: a 32-bit sentinel printed with `%d` prints NEGATIVE (0xffffd8f1 -> -9999), so print it as `0x%x` and gate on the unsigned constant, never on the positive decimal.
- **Two Hermes sessions can work the same repo at once** (a cron dispatch plus a sibling or a duplicate): a doc you just patched can be rewritten under you (the write tool names the sibling session id and its timestamp). Commit your own notes/NAMED/scripts EARLY so a sibling cannot bury them — and keep an untracked deliverable OUTSIDE the worktree, because a sibling's `git clean`/`git checkout` deletes untracked files with no warning (a prompt file written into the repo root vanished mid-turn) — re-read a doc immediately before patching it, and never start a competing measurement before `tail -5 SESSION_CURSOR.md` + `ls -lt evidence/*.gdblog | head`. **Name the owner before arming:** `ps -eo pid,etime,cmd | grep -E '<instrument>.py|<driver>.py'` prints a sibling's live command line (its argv carries the whole pipeline it is running) and `stat -c '%y %n' SESSION_CURSOR.md evidence/<recent>.gdblog` shows who wrote last; every shell the agent spawns carries `hermes-snap-<session-hash>.sh` in its own argv, so a hash that is not yours names a LIVE sibling even while it sits between commands and before it has committed anything — `git log` shows nothing foreign in exactly that window, so the process table, not the commit log, is the early warning.
  Cron-sibling ownership + collision etiquette: `references/git-workflow.md` §Sibling ownership.
- The guard also **refuses** a wholesale `write_file` of a doc the session only ever saw through a
  shell dump (a terminal print of the file) rather than a real `read_file` — which is exactly how the
  footing ritual reads `NEXT_PROMPT.md` before rewriting it. Don't re-read 15 KB to satisfy it: write
  the new text to a scratch path and `mv` it over (atomic, no re-read), or confirm the file is
  untouched (`git diff --stat HEAD -- NEXT_PROMPT.md` empty), then `rm` it and write, or patch in
  place. A `git checkout` of another branch rewrites tracked docs under your feet and invalidates an
  earlier `read_file` the same way — take the scratch+mv route instead of re-reading the file.
Delegated decodes belong to PARENT/static sessions: fire `delegate_task` before the milestone, never
mid-way — a child's completion report is injected into the live turn at an arbitrary point and can
exceed 10 KB. A milestone session that drives the live box runs no children at all.

If a turn does die, the signature is the 400 `prompt (...) leaves no room to answer`, compression
reporting `summary_truncated_failure` (aux summary `finish_reason=length`, retries paused ~15 min), then
`Cannot compress further` and `end_reason: session_reset` with the transcript not persisted. Recover from
disk only — `git log --oneline main..HEAD` (empty means nothing was committed), `git status --short` —
and checkpoint that tree BEFORE `milestone.py start <next>`, or the next milestone's commit sweeps it in.
Aux compression runs on the main reasoning model (`auxiliary.compression.provider: auto`); its thinking
consumes the summary's output budget, which is why the summary truncates instead of compressing.

**Append to evidence/notes docs with the `patch` tool, not a shell heredoc.** The command blocklist scans
HEREDOC BODY TEXT as well as the command (a sentence containing `init 0` trips the `init 0|6` shutdown rule
and the whole append is refused), and backticks inside a `python3 -c "…"` payload are command-substituted by
the shell, silently deleting those fragments — grep the written region after any shell-embedded write.
Never CHAIN commands after a heredoc delimiter in one command block: if the delimiter does not land on its
own line the shell swallows the delimiter text and every later command in the block silently becomes file
content (a `cat >> NOTES` ate the `cat >> NAMED` that should have carried the registry block). Run an
append in its own call, then read back the tail of BOTH files. An
`execute_code` cell is hard-killed on its own timeout and does NOT stop a turn driver it spawned: `ps -p
<pid>` for the orphan and kill that exact pid — this checkout's `smac_play.py` has **no `--mode stop`**
flag (an earlier note here claimed otherwise), and never `pkill -f`/`pgrep|kill` by name: your own argv
matches.
