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
- On a chat platform (Telegram), every between-tool-call sentence is DELIVERED as its own message: a ~40-call
  fire reads as 40 chat messages. Paul called that "vomit" (s211). Chain tools SILENTLY; the only prose is the
  final report. This does NOT change the checkpoint-commit discipline - commits need no narration.
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
missing `path` was re-emitted ONCE as pure JSON and, on a second identical refusal, abandoned for an
`execute_code`-composed file instead of fragmented or retried again; the box debt was paid or named; and the close ended in
a merged PR with `NEXT_PROMPT.md` under 15,300 B.

**Answer state questions from live state, never from what you did earlier in the session.** "Should we resume the
cron?" is answered by `jobs.json` (`state`, `enabled`, `next_run_at`) plus the newest `executions` row — a job resumed
an hour ago is still running, and offering to resume it reads as not having looked.

**Estimate progress from the repo's ledgers, never from a recalled prior estimate.** Read the BUILD_SPINE rung
ladder (what each rung proved, where it stops), the `sim/` module inventory (what is actually built), `git log`
velocity (merged PRs/day over the last few days), and grep NAMED.md for each candidate subsystem (combat, tech,
victory, AI execution…) — a ZERO-hit grep names the untouched territory that dominates the range. Give
rounds-left ranges per significant milestone and convert at TWO paces (operator-driven continuous chain vs the
autonomous cadence alone); name the unexplored-subsystem risk explicitly. The ladder past the last authored rung
is unwritten by design — estimates are subsystem-gap based, not rung counts. "Runnable" means headless per the
spine's own scope; a human-playable UI is a separate project, not an estimate target.

**Answer meta-questions about the transcript itself by querying the message store, not by searching its text.**
"How many times was context compressed?", "how many calls did this session run?" are exact rows in
`~/.hermes/state.db`: table `messages` (`id, session_id, role, content, tool_name, timestamp`) and table `sessions`
(columns include `message_count`, `tool_call_count`, `rewind_count`, `compression_fallback_streak`,
`compression_ineffective_count`, `parent_session_id`). `session_search` cannot answer them: it returns matches from
OTHER sessions, and once such a result is pasted into this transcript its summary text is stored as a message HERE,
so a later substring search counts that echo as an event. Disambiguate by position —
`select id, role, tool_name, instr(content, '<marker>') from messages where session_id=? and content like '%<marker>%'`
— offset 1 under a user/assistant role is a real event, a large offset under a `tool` role is a quote of one. Then
separate a genuine failure streak from a healthy session by the sessions-row counters rather than by the count of
summaries, and identify the session first (`sessions.id` starts with its creation timestamp).

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

Never leave the commit until after the handoff docs.
- **A docs-patch step and its commit never ride in one chained command.** A multi-line `old_string` on a hard-wrapped
  doc (or one that a `milestone.py submit` prune re-wrapped underneath you) raises or no-ops, and the chained
  `git add -A && git commit` still runs — shipping corrected code beside stale prose, invisible in `git log` and only
  noticed when the next fire greps the registry. Sequence: run the patch script alone, assert the NEW phrase is present
  in the file, `git status --porcelain`, THEN stage and commit. Same for any script editing several docs: one aborting
  `assert` between them makes the commit half-true.
- The prompt rewrite is the single largest generation of a turn
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
  other exists, and land the move as one commit so git records it as a rename rather than a deletion. When the moved
  block is a REGISTRY block the lint still reads, keep a one-line-per-claim stub in NAMED.md carrying the
  SAME gates, mutants and evidence cites (the full rows stay greppable in the archive), and assert sha1
  byte-exactness of the moved text at write time — `review_lint` passes on the stub, and the headroom is
  real instead of a deletion the next fire greps in vain.
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

**A BUILD fire may have to AUTHOR its rung.** `track_mode.py` counts `B<n>` prefixes in merged history, so it can print `next_rung=B<n>` when BUILD_SPINE.md's ladder stops short (B14, s241): the spine records a rung only when a fire ships it. Then the build fire writes the rung text FIRST (from the last build's DECLARED frontier + the laws the intervening ANALYSE fires settled - the ladder is authored from settled census law, never from new decompile claims), appends it to BUILD_SPINE.md, and only then implements it; state the authoring in SESSION_NOTES so the numbering convention stays auditable.

**A BUILD rung may be a FALSIFICATION rung, and that is a success.** The highest-value build unit is often
an ORACLE: replay the model's own composed law against the game's recorded trace/boundary samples and
score it (measured: a "the queue head's id is the bit that appeared" rule scored 0/6 while an independent
raw-XOR delta matched every sample). When the recorded bytes refute the model, the deliverable is the
refutation PLUS an in-place qualification of the registry block that asserted the old mechanism
(`UNVERIFIED against recorded bytes`) — not a weakened instrument and not a deleted claim. Design the
oracle with at least one NON-VACUOUS recorded negative (a case where the rule would fire and the bytes
show it did not); without one, a 0/6 score can mean the window never exercised the rule at all.


## s242 retirement: session discipline + budget/closing caps
> Moved VERBATIM out of `skill/SKILL.md` at s242 (context hygiene); the hot core in
> `skill/SKILL.md` carries the rules and points here. Nothing in this block was edited.

## Session discipline (this project is context-heavy)

- `milestone.py start <id>` resets the working tree to main: any footing carried from an unmerged
  branch (docs + scripts via `git checkout <branch> -- ...`) AND `SESSION_CURSOR.md` must be
  re-written AFTER it, or the cursor reverts and a later write is refused as stale. The kickoff ritual
  reads `NEXT_PROMPT.md` BEFORE `start`, but `start` swaps that file for MAIN's copy — when the previous
  session's update sits unmerged on its branch, the pre-start text is NOT what you patch: re-read the
  sections after start and anchor edits on the post-start copy.
- A list cursor read BEFORE the seek is the PREVIOUS cursor: the chooser pump seeks with
  `call 0x4026b0` (0x497717) and only then reads `[[c+0xc]+4]`; a node print at the pump entry
  (0x497704) shows the old node, so a value-vs-node gate fails on the instrument, not the game.
- **The save's 22-B COLUMN view is NOT the live tile record** (s236, M290 run 1): `sim/save.py
  tile()[0]` mixes in the record's byte 22 and misreads the category (5/7 legal land sites read
  cat 0 = water). The live byte-0 category (`& 0xe0`: cat 0-2 water, 3-6 land) lives at
  `grid_off + 44*((W/2)*y + (x>>1))` — the FIRST half of the 44-B record. Any tile-legality fit
  must use the record view or it "proves" the game founded on sea.

Paul wants SMAC RE broken into **small pieces**: complete ONE milestone, write it to a
file, append one dated line to `~/reverse/smac/SESSION_NOTES.md`, then STOP — ending
after a single milestone is a success, not a shortfall.

**On a chat platform (Telegram), chain tools SILENTLY**: every between-tool-call sentence is delivered as
its own message, so a 40-call fire reads as 40 chat messages. The only prose is the final report;
checkpoint commits need no narration. Depth: `references/session-discipline.md`.

Exception: when he says **"keep going until you finish <chapter>"**, that overrides the
stop-after-one rule. Work through that chapter's milestones, writing the doc + evidence
after each, and report once at the end — including what is still open. Do not relabel a
partial result as done to make the chapter look finished (see `MILESTONES.md` F2).

**A bare "keep going" after a report is approval for the recommendation, not a request for more analysis.**
When your report ends by naming the next step (merge PR N, spend the next acceptance, write the plan into the
pick), the go-ahead means DO that step and report in one screen — including `milestone.py merge <n>` on a green
PR. Re-asking or re-summarising costs a turn and reads as stalling; the discipline that still binds is one
milestone per merge and three acceptance invocations, not one question per step.

### Budget, closing order and doc caps — depth: `references/session-discipline.md`

- Budget by TOOL CALLS: brief+accept <= 6, milestone 6-30, **checkpoint commit by ~15**, stop measuring at
  30-40, close at 40-50. Cap ACCEPTANCE INVOCATIONS at three; the third failure IS the finding. The commit
  number is measured, not ceremonial: on this loop a fire costs ~5-7 k tokens per call, so a "commit at ~25"
  rule lands at ~167 k context with NOTHING committed (two fires in a row did exactly that and needed an
  operator steer); branch + commit the census SKELETON before probing and the same fire saves at ~108 k.
- Close order, every time: gate GREEN -> notes entry (`patch`) -> **checkpoint commit** -> `NEXT_PROMPT.md`
  rewrite -> submit/PR. Never leave the commit until after the handoff docs.
- **Every VERIFIED row in the NAMED block names the mutation that reddens it** (s290 law; #309/#311 reviews:
  6 of 8 findings were claims no gate read). The mutation harness proves gates BITE; only a claim->mutant audit
  proves they COVER. A row with no mutant is INFERRED/OPEN until pinned + mutated. Tracers/classifiers also get
  an ALGORITHM mutant (a between-push reload for a def-walk tracer): instruction/data mutants cannot catch a
  wrong trace position. Depth: `references/instrument-laws.md` §Algorithm mutants + the coverage law.
- Review pipeline (external review credits exhausted): `scripts/review_lint.py --id <id>` at close — mechanical
  checks: every V row names a mutant (meta-row exemption needs the ACCEPT/REVIEW prefix AND a harness/digest
  marker in the row), cited mutants exist, cited CODE mutants' patch addresses appear in the instrument source,
  each `digest <hex>` is printed in the SAME ROW's cited evidence, citations carry :line. SCOPE: naming /
  existence / address-contact / digest-presence — the row->gate SEMANTIC relationship stays with the reviewer;
  state that limit, don't oversell the lint. Fixtures `test_review_lint.py` 12/12: every check bites on a bad
  fixture AND passes on a good one. A failing fixture is as likely a FIXTURE bug (mutant-id collision with
  another test, a bypass row that still cites a mutant, the unrelated file cited in the same row) as a checker
  bug — debug the fixture before the checker. Then `scripts/ai_review.py <n>` after submit — a FRESH-CONTEXT
  Strata review, replay-validated against known pre-fix findings (caught the algorithmic + coverage classes;
  the definition-mismatch class is checklist-targeted in the prompt). It flags output-cap truncation (warning
  banner + exit 2) — re-run with a larger cap before triaging a truncated review. Review findings are CLAIMS, not verdicts: a reviewer can miscalculate or miss an existing pin, so
  verify disputed findings with tools (print the arithmetic, grep the pin in the instrument) before
  accepting them OR relaying severity counts as a model-quality verdict; an author's dismissal is
  valid only with measured numbers. The semantic layer's proven unique catches — author gates accordingly:
  CIRCULAR checks whose expected set derives from the check's own input (`w in wins` where `wins` is built
  from `w` — derive expected values from an INDEPENDENT scan), hardcoded offsets a shift mutant bypasses
  while the section parser honors the shift, prose claiming a comparison the code never makes, and
  DOC-level decoration: NAMED rows asserting counts/constants the instrument does not print (retract in
  place and give the retraction facts their own instrument). The mechanical layer reciprocates: L2b
  address-contact flags mutants patching sites the instrument reads only via computed walks — strengthen
  with exact-address pins and re-measure. A truncated review re-run at a larger cap is a COMPLETION of the
  one review (one triage reply covers both runs), not a second opinion. Triage rule unchanged; the human
  owns the merge. Before merge, PATCH the PR title to the post-review numbers (`gh api -X PATCH
  repos/<owner>/<repo>/pulls/<n> -f title=…` — `gh pr edit` can fail on Projects-classic GraphQL errors);
  the squash title snapshots at submit and otherwise ships stale pre-review counts. Evidence +
  constraints: `docs/AI-REVIEW.md`.
- `NEXT_PROMPT.md` <= 12,000 BYTES AT CLOSE (warn; gate FAILs 16,000) — the unattended kickoff's cap-triage trigger. `evidence.py budget`
  prints `os.path.getsize`, i.e. exactly `wc -c` (its column has been labelled `bytes` since s179; the code comment
  used to claim characters while the code compared bytes — the instrument was right, the prose was wrong). The gate
  only FAILs at 16,000, so a fire that closes past the warn hands the NEXT fire a docs-only split: s175 and s179 were
  both such splits (under the old 15,300 cap). `test_loop.py` appends bytes in CI, so keep >100 B of headroom under whatever number you quote.
  `SESSION_CURSOR.md` <= 600 B before any step that can exceed ~2 min.
- Docs > 10 KB: `patch` anchored sections, never `read_file`-then-`write_file` — one whole-doc call must fit the
  model's OUTPUT cap, so an oversized one truncates mid-JSON, the sanitizer drops it (`Unrepairable tool_call
  arguments`, or a `write_file`/`patch` refused as `missing required field 'path'` even though the path was sent),
  and every retry spends a full turn — a second identical re-emission failing the same way means STOP retrying and
  compose the file in an `execute_code` cell (`open(p,"w").write(src)`; stage big files as scratch chunks and `cat`
  them together — and when appending to an existing file, write the NEW chunk to a scratch path and concatenate:
  feeding `read_file` output back into `write_file` is refused, the guard recognises its line-number-prefixed
  display format as not real file content); in hard-wrapped docs anchor by
  regex `\s+` joins or by INDEX, and write in the SAME cell that measured the result.
- Every always-loaded doc has its own cap and the tool prints them. When a cap binds a SECOND session, SPLIT:
  move the settled era into a topical archive, leave the RULES plus a pointer, re-run `budget`. A batch's DOC
  cost is ~350-700 chars of `NEXT_PROMPT.md` per new milestone block, so measure headroom BEFORE choosing the
  batch size — a green three-milestone batch can end a session 30 B from the cap.
- Two sessions can share this repo: commit notes/NAMED/scripts EARLY, keep untracked deliverables outside the
  worktree, and name the owner from the process table before arming a measurement.
- Scheduling the loop to run unattended: copy `templates/cron-milestone-loop.md` — a cron prompt validated end to end
  (takes the pick from `NEXT_PROMPT.md`, triages doc caps first as its own PR, proves ownership before arming, caps
  the batch, merges only on a real PASS). Cadence, the "verify the fire" rules, and the READ-ONLY AUDIT for
  answering "how is the loop doing" (ledger query, failure signatures, the output-cap death, mid-fire model
  capture) ride with it.




## s242 retirement: evidence budget + delegated decodes
> Moved VERBATIM out of `skill/SKILL.md` at s242 (context hygiene); the hot core in
> `skill/SKILL.md` carries the rules and points here. Nothing in this block was edited.


### Evidence budget and delegated decodes (both bite every milestone)

`python3 scripts/evidence.py budget` — `evidence/` warns at 20 MB and **FAILs the gate at 30 MB**, and a
few trace logs and screenshots can eat the whole margin. Before closing a milestone: drop only files
>100 KB whose basename appears in no `.md`/`.txt`/`.py` of the repo, with `git rm` (never plain `rm` —
being in history is what makes deletion safe), and record every kept/dropped file plus size in
`evidence/<id>_prune_manifest.tsv`. Test unreferenced-ness in ONE shell loop —
`find evidence -size +150k -printf '%s %p\n' | while read sz p; do git grep -qF "$(basename "$p")"
-- '*.md' '*.py' || echo "$sz $p"; done` — one tool call per candidate eats dozens. The MB figure
recorded in `NEXT_PROMPT.md` goes stale during the session that writes it; measure with `budget`
at close, never from the footing. `evidence/m53j_text.txt.gz` (~5.7 MB, the disassembly cache the
method runs on) is PRUNED from the worktree when the gate nears 30 MB; it is git-kept — recover with
`git show 733322c6:evidence/m53j_text.txt.gz > evidence/m53j_text.txt.gz` (repo root) before zgrep.

Measured margin: 29.3 MB / 858 files against the 30 MB FAIL, and `prune --dry-run` offered NOTHING (it drops
only uncited images older than 7 days). A 40-turn trace is ~55 KB but one screenshot is 400 KB, and
`check_classes.py` writes a `_3x.png` sibling next to every frame it OCRs (delete those immediately); run
`budget` BEFORE adding frames. When prune offers no victims, free room by gzipping a large *text* file no
markdown cites (`grep -rn <basename> --include=*.md .` first — a cited path must stay readable at its path).
- **A memory sampler is the fastest way to blow the evidence budget, and pruning cannot save it.** A `/proc/<pid>/mem` poll loop with no sleep runs tens of thousands of samples/s — a 150 s run wrote a **1.4 GB** trace and turned the gate RED *after* the milestone work was already done. Sleep the loop (2 ms is the sampling cadence the footing asks for anyway), and downsample before the first commit of the trace: keep the first sample, every sample where a watched field CHANGES, one heartbeat per second, and the last — 1.29M samples collapse to 68 lines / ~10 KB with the boundary sequence intact. `prune` offers no victims here: it drops only uncited images, and a cited trace must survive at its recorded path. A giant blob also stays in the branch's HISTORY once committed, so a later delete does not un-poison a push (see `references/git-workflow.md`).

Delegating a static decode works well (a child can map a 1450-line function in minutes), but a child's
claims are testimony, not evidence. Re-read from the cached disassembly: (1) every store site it cites,
with its immediate; (2) the address arithmetic that lets the value reach the field — a store guarded to
an index past the array is dead code, so check the guard before believing a value exists; (3) the
function boundary (`zgrep` the `ret`) before accepting any "written in the caller, not the callee"
attribution, which is where decodes drift. Write the audit to its own short note
(`evidence/<id>_verify.md`) and label instruction-stream facts VERIFIED and branch semantics INFERRED.


## Two-entry-point rule (s273, B22)
- A rung's gate TEXT must have ONE author. The module composes the `(label, ok)` pairs; the
  `sim/selftest.py --bNN` hook only relays and summarises them, so the two entry points can never print
  different claims. A hook that re-derives or reformats the labels is a second source of truth.
- **After adding a function to a module, grep the module for other `def`s of the same name.** Python lets
  the later definition win: B22's `composedgrowth.py` carried a stale `acceptance()` draft below the good
  one that truncated labels to 64 chars, printed the report itself and recomputed a third time — `--b22`
  silently ran the shadowed copy and still reported `PASS B22: 11/11`. Green output from the wrong code
  path is the worst failure mode this repo has, because nothing downstream complains.
- A duplicate-definition check belongs in the same breath as `ast.parse`: `names=[n.name for n in
  ast.parse(src).body if isinstance(n,ast.FunctionDef)]; assert names.count(f)==1`.

### Parallel chains (N lanes, one repo)

Two or more chains on one repo farm independent ANALYSE picks while the primary drives the
build track. Protocol, validated end to end:

- **One cron job per endpoint**, each in its own worktree: `git worktree add ~/reverse/wt-<chain> -b
  milestone/<id> origin/main`, then symlink the untracked dirs the instruments read (`ghidra_out`,
  `scratch`, `programs`). Pinning quirk (`pinned=true` captures the config default, not the chat
  model) and the jobs.json fix: hermes-agent `references/background-systems.md` §Cron. The live pair
  (2026-11-24 retired): `smac-re-loop` = `789931d4b621` in the main checkout (build track),
  `smac-re-chain2` = `9a0b613bb1ac` in `~/reverse/wt-chain2`, `smac-re-chain3` = `09a25323e05b` in
  `~/reverse/wt-chain3` — every lane pinned to the same metered endpoint with `hermes cron edit`.
- **Name the ownership in BOTH prompts**: which picks each chain owns, and that neither touches the
  other's worktree or `sim/` (the build track). Disjoint picks prevent collisions; the ownership
  check is the backstop.
- **Exempt the parallel job in the ownership check.** A single-chain prompt's collision rule treats ANY
  running execution row as a competitor, so a scheduled tick stands down while the OTHER chain is live —
  an idle hour with a clean `completed` row and no error anywhere. The STORED prompt must name the
  parallel job id and say its running row is NOT a collision; stand down only for own-job live rows or
  live instrument processes in the MAIN checkout. Patch the stored prompt (`cronjob_manage update`), not
  just the transient run override — the scheduled tick reads the stored one.
- **Shared-doc protocol**: one chain owns NEXT_PROMPT/cursor; the other APPENDS exactly one result
  line to NEXT_PROMPT plus its own NAMED block and session section. The append is not optional
  politeness — the gate's checkpoint check requires NEXT_PROMPT updated on every milestone branch,
  so forbidding the second chain from touching it guarantees a RED gate.
- **Worktree `.git` is a FILE**: `milestone.py submit`'s `.git/PR_BODY.md` path fails there — write
  the body to scratch and `gh pr create --body-file` (the merge path is unaffected).
- **Collision rules**: session-rotation archives cut from the same base share one canonical filename
  (no conflict); different content under the same name → rename the incoming one with a chain suffix
  and fix its pointer. Archive-section numbers (`§trim-s<N>`) are a shared namespace — check which
  the other chain took before naming yours; a duplicate block is measured (size + sha1) and deleted,
  never guessed away.
- **Assign each lane's milestone ID from the PARENT, one per lane, in the run context.** Lanes that
  each "take the next number" collide: two lanes both claimed M348 and their branches differed only
  by case (`milestone/m348` vs `milestone/M348`), so both PRs existed and both registry blocks would
  have carried the same `## M348` heading. Put `Your milestone ID is exactly M<n> — do not pick
  another` plus `your branch is milestone/m<n>` in every transient footing, and allocate N+1, N+2,
  N+3 per round. When a collision happens anyway, the FIRST-OPENED PR owns the ID and the other lane
  is a bounded finish unit: commit its pending review edits, `git mv scripts/<id>_* scripts/<newid>_*`
  plus the evidence files, sed the ID inside contents/NAMED heading/session entry/NEXT_PROMPT result
  line, re-run its acceptance from the WORKING TREE (the pre-rename numbers no longer describe the
  tree), push a NEW branch and PR titled with the new ID, close the old PR as superseded, and merge
  only on a verified CI PASS. Never merge the duplicate and promise to fix the numbers later — two
  `## M<n>` headings make every later grep ambiguous.
  **The BUILD lane is the exception**: its ID comes from `track_mode.py` (`B<n>`), so assign M-numbers
  only to the analysis lanes and never let a build fire take an M-number (or an analysis fire take a
  B-number). Read `track_mode.py` immediately before allocating the round's IDs.
- **Only the PRIMARY checkout may sit on `main`.** A linked worktree left on `main` blocks the
  primary: `git checkout main` there fails with `fatal: 'main' is already used by worktree at
  <primary>`, and the next `milestone.py start` fails with it. Before each round park every
  non-primary lane on `git checkout --detach origin/main` (or its own milestone branch); `git
  worktree list` should show `main` in the branch column exactly once. The lane that owns the primary
  also owns `main` and the `sim/` build track; every other lane works detached/worktree-local.
- **Round prep is an ORDERED checklist, and its steps must not ride one `&&` chain.** Primary: `git checkout main && git pull --ff-only`; move each lane's UNTRACKED review sidecars to `~/reverse/artifacts/pr<N>_review/` and restore any that show as DELETIONS (tracked); `git checkout --detach origin/main` in every non-primary lane; `wc -c NAMED.md NEXT_PROMPT.md` plus `track_mode.py`; allocate IDs; only then fire. A `&&` chain aborts at the checkout while a lane still holds `main`, so the pull, the sidecar move and the cap check never ran while the command still exits 0 via a later `cd` — run the checkout alone first, then the rest, and read `git status --short` + `git worktree list` before trusting it. **Re-run that check after EVERY round, not only the first**: a lane's own landing path (`milestone.py merge`, or a fire's own `git checkout main`) can put its worktree back on `main` while the round closes, so the next prep's checkout aborts exactly as it did at round one — `git worktree list | grep -w main` should print the primary once. **Also sweep stray UNTRACKED `?? evidence/ai_review/pr<N>_*` at prep**: a fire that declines to fabricate a docs-only session section leaves its review record untracked ON PURPOSE, and the files accumulate across rounds; move them out with the tracked ones (`mv` — an untracked file needs no `git checkout --` restore).
- **Budget the shared registry across the WHOLE round, and rotate in the PARENT.** Every lane appends its own `## <ID>` block (0.7-3 KB) to the same `NAMED.md`, so the room a round needs is N blocks, not one: at three lanes and under ~3 KB free, it cannot land without three rotations of the SAME region. Rotate ONCE from the primary checkout BEFORE firing (`python3 scripts/<id>_rotate.py --verify` prints the sha1 tally, then `wc -c NAMED.md`), put the post-rotation size in every lane's footing, and say the rotation is DONE — three lanes each told "rotate first" edit one region and their PRs conflict there, which is where the round loses a lane. Rotate the oldest FULL block, and make the verifier REFUSE a block that is itself a stub: moving a stub archives the pointer while its depth sits two hops away, so a block with no rows left is already archived, not settled.
- **Attribute the gauge per ROUND, not per fire.** Overlapping lanes share cache reads and the meter cannot separate them; a reading taken as each fire reports `ok` still misses that fire's tail (the gauge lags minutes). Pause EVERY lane, refresh the Portal cache, take ONE reading, and put that base → post-round delta on the round's ledger row. **Order, not work, drives most of a per-fire delta:** measured over one three-lane batch, the FIRST fire of a round moved the day window +1.7 to +2.6 pp, while a second lane landing minutes later moved it +0.10 pp — the later fire re-reads a warm cache. So the round's cost lands on whichever fire goes first: fire lanes together (staggering them buys almost nothing back), read the gauge per round, and never extrapolate when a usage ceiling will arrive from per-fire numbers. Depth: hermes-agent `references/subscription-usage.md` §Multi-lane rounds.
- **Landing**: rebase onto origin/main before merge; force-push is blocked in cron → absorption
  merge (hermes-agent background-systems.md §Cron-mode git constraints). Keep BOTH chains' doc
  sections through every conflict.
- **Cross-model review is a feature**: `ai_review.py` resolves the Strata endpoint regardless of the
  author's model, so a second-endpoint author gets genuine reviewer diversity for free.
- **Scaling beyond two lanes is the same recipe, not a new design — but three or four is the ceiling.**
  A third lane = one more worktree (`git worktree add --detach ~/reverse/wt-chain3 origin/main` plus the
  `ghidra_out`/`scratch`/`programs` symlinks) and one more job created with the CLI, because
  `cronjob_manage` cannot set a model pin: `hermes cron create --name <lane> --workdir <wt> --model <id>
  --provider <name> --paused --deliver origin "every 1440m" "$(cat <prompt-file>)"`, then trim its
  toolsets with `cronjob_manage(action='update', enabled_toolsets=['terminal','file'])`. Limits that
  make 3-4 the practical cap: exactly ONE lane may own the main checkout and the `sim/` build track;
  every other lane needs a DISJOINT pick from a finite static list, so past ~4 lanes they overlap
  (a collision, not parallelism) or invent work; and shared-doc merge conflicts grow roughly with the
  number of lane PAIRS. Add a lane at a round boundary, not mid-round, when the shared docs are being
  written. **A worktree whose `ghidra_out`/`scratch`/`programs` are SYMLINKS reads DIRTY**: the repo's
  `.gitignore` entries carry trailing slashes (`ghidra_out/`, `scratch/`, `programs/`), which git does
  not match against symlinks, so `milestone.py start` refuses with `worktree dirty` on a lane that has
  no edits. Add the bare names (`ghidra_out`, `scratch`, `programs`) to `.git/info/exclude` in the
  shared repo — one edit covers every linked worktree — and confirm `git status --short` is empty
  before firing. Every lane's transient footing must name the other lanes' job/row as NOT a collision — the
  stored prompts of older lanes know only the lanes that existed when they were written.
- **Pace**: a free-tier/shared endpoint runs ~2–3× slower per fire (queueing + long generations) but
  completes full milestones including review rounds inside one fire when the unit is bounded. Keep
  it off the critical path; measure the gap with the tok/s recipe in the same hermes-agent reference
  rather than guessing from per-call latency.
- **Re-pointing the lanes at one model ("run some sessions on model X").** The existing paused jobs are
  the right vehicle — do not create a third. `cronjob_manage(pinned=true)` captures the CONFIG default,
  so pin each lane with `hermes cron edit <job_id> --model <served-id> --provider <provider-name>` and
  read the `model`/`provider` pair back from `jobs.json` before firing. Per lane: `resume` → `run` with
  a lane-specific transient footing → `pause`; then confirm BOTH `status='running'` rows in
  `executions.db` and each fire's `on_session_start.model` in the harness-story jsonl (match by
  `turn_id` containing `cron:<job_id>:<execution_id>`; do NOT pick by mtime — the orchestrator's own
  session jsonl is newer). A stored prompt written for the old endpoint now contains a false "different
  model" premise: say the new model in the override, and update the stored prompt when it also names
  wrong picks/ownership. End the turn once both are live; the completion reports re-enter the chat and
  polling only burns calls. Generic cron traps: hermes-agent `references/background-systems.md` §Cron.
- **N rounds on one model ("do 10 more rounds, report each time").** Keep the ROUND LEDGER outside the
  repo (`~/reverse/artifacts/<batch>-rounds.md`): one row per round with base gauge -> measured gauge,
  each lane's result/PR/commit, time, calls, tokens, estimate. It survives context compression and the
  repo's doc caps; nothing in it belongs in NAMED.md. Per round: `resume` -> `run` (lane-specific
  transient footing) -> `pause` both jobs, then verify at the destination (`git log`, `gh pr view`, the
  acceptance file AT the merge commit) and report ONE screen per fire as it lands. **The parent's per-notice check is three calls**: `git fetch -q origin && git log --oneline -2 origin/main`, `gh pr list --state open --limit 4`, and the live rows from `~/.hermes/cron/executions.db` (`status='running'`, keyed by job_id, with minutes-since-start) — then `tail -8` the newest `~/.hermes/cron/output/<job_id>/*.md` for the fire's own closing lines (its `Still UNKNOWN` and `Next pick` are what the next round's footing quotes). A PR sitting OPEN with a green `gate` check, `mergeable=MERGEABLE` and a title already patched to post-review numbers is the PARENT's to squash-merge; only a red gate or a `CONFLICTING` state is a lane problem. Fire the next round
  only when BOTH lanes have closed — a lane still mid-review is not a closed round. Before firing,
  clear the worktree: `milestone.py start` refuses on UNTRACKED files too, so move each UNTRACKED PR
  review sidecar to `~/reverse/artifacts/pr<N>_review/` first. If `git status` shows the sidecars as a
  DELETION, they are TRACKED (the fire committed them) — restore with `git checkout -- <paths>` and leave
  them in the repo; moving a tracked file out dirties the tree instead of cleaning it. **In the linked worktree `start` then dies at
  `git checkout main` — `fatal: 'main' is already used by worktree at /home/paul/reverse/smac`; create the
  branch directly instead (`git checkout -b milestone/<ID> origin/main`) and continue.**  A lane's PR showing `CONFLICTING` means main moved under it — report it as a state, not a merge. **But
  the fire can die INSIDE that merge, and the lane is then NOT closed:** `git status` in the lane worktree
  shows `UU NAMED.md / NEXT_PROMPT.md / SESSION_CURSOR.md` with `M SESSION_NOTES.md` already staged and the
  merge commit uncommitted/unpushed. The PARENT finishes it (force-push is blocked, and waiting for the
  lane's next tick is a day out): resolve each hunk keeping BOTH sides (the other lane's block/line first,
  this lane's after it; the single-line `SESSION_CURSOR.md` keeps this lane's row, marked
  `merge pending`), assert `grep -c '<<<<<<<\|>>>>>>>'` is 0 in each file, re-run `gate.py --base
  origin/main` (its `conflict markers: none` line) AND the lane's acceptance (must reprint the pinned
  digest), `git add` the three files, `git commit --no-edit`, push, then wait for `gh pr checks` to print
  `pass` and `gh pr view --json mergeable` to say `MERGEABLE` before `gh pr merge <n> --squash`. Put "if
  main has moved, merge origin/main in keeping BOTH sides and FINISH the merge before reporting" in that
  lane's kickoff — a fire that stops at the conflict is indistinguishable from a clean lane until you
  read its worktree.
  **GitHub also schedules NO PR run while the PR is dirty**, so `no checks reported` on a conflicting
  branch is the conflict, not an outage: merging origin/main in flips it to MERGEABLE and the run appears
  on the push (`references/git-workflow.md` §A dirty PR).
  **A cancelled fire reports as a failure.** `cronjob_manage(action='cancel')` ends the run with
  `status=error` and `FAILED — cancelled on request`, and the completion notice arrives looking like a
  model crash. Cancel at its first check (~5 API calls, no work lost), and say in the report that YOU
  cancelled it and why, or the user reads two failures. **Completion notices are not ordered**: a
  cancelled run's notice can land AFTER its replacement is already running, so match each notice to its
  delegation/execution id and read `executions.db` before reporting a failure — the live rows are the
  state, the notice is a delayed event.
  On a metered endpoint, measure the plan windows per round (hermes-agent
  `references/subscription-usage.md`) and stop early when the binding gauge passes the user's ceiling.
  **Close the batch with a SET SUMMARY, not just the last round**: every unit merged (ID, PR, commit,
  acceptance line), which questions actually closed, what remains OPEN, velocity and failure count,
  doc-cap trajectory, and total tokens/cost/gauge movement from the batch baseline. A per-round table
  is not a set summary — the user asks for the arc, and it is the one item a long batch forgets.

## Taking over a cut-off fire (s287, B24)

- **A cron fire's `ok` status is a SESSION status, not a CLOSE-OUT status.** A fire can exit ok with the
  milestone unfinished: branch commits present, acceptance green, but the harness left UNTRACKED and no
  evidence/PR/notes/cursor write. Before reporting done or taking over, read the repo's end state —
  `git status -sb` + `gh pr list --state open` + the top `## Session` + the cursor.
- **`ok` at the API-call cap almost always means the PR is still OPEN.** The completion block prints the call
  count: a fire at its cap (150) spent the last calls on the review round and exited with the PR
  submitted-but-unmerged — acceptance green, gate green, and its own output ending `To finish: python3
  scripts/milestone.py merge <n>`. The PARENT closes it, not the lane: `gh pr checks <n>` until a real
  `pass` (not `pending`), read the comment BODIES, patch the title if the post-review counts moved, then
  `gh pr merge <n> --squash` and confirm with `gh pr view <n> --json state,mergeCommit` — an unmerged
  round is a blocker, and that lane's next tick is a day out. `--delete-branch` may die on "main is
  already used by worktree"; the server-side merge already landed, so verify the PR, not the exit status.
- To finish it, stay on the fire's branch and re-run ITS acceptance (a green already-earned run is re-confirmed,
  never re-derived), then apply the normal closing order; **commit the untracked harness first** so a second
  cut-off cannot lose it. B24 ran twice this way: fire 1 left the instrument green and the harness untracked;
  fire 2 committed the harness, then discovered its declared gate sets were authored rather than measured - and
  the re-run of the fire-1 acceptance, byte-identical to the committed evidence, is what made that distinction
  safe to publish.
- **A fire that dies mid-REVIEW-REMEDIATION leaves edits uncommitted and UNRUN.** The acceptance
  numbers in its report describe the pre-edit head only. The finishing fire re-runs the instrument
  FIRST and re-pins every digest/acceptance pin from the PRINTED rows before touching docs; a digest
  scope (SIGKEYS-style) stays unchanged unless the run itself changed, so a print-format edit does
  not move a pinned digest. The dead fire's harness subprocess died with it — check `ps` and the
  evidence file's existence before assuming a pass is still running, and re-run from the corrected
  working-tree state. Pass the dead fire's owed list verbatim into the continuation override.
- **A footing file's "MERGED" claim is not state — measure it.** A fire cut off after `submit` can leave
  `NEXT_PROMPT.md` asserting "MERGED-BY-THIS-FIRE" while `track_mode.py` still names that rung and
  `gh pr list` shows the PR OPEN. Before firing a continuation, resolve the milestone from `track_mode.py`,
  `gh pr list --state open`, and `git ls-tree origin/main -- <module>`; then put the contradiction in the
  transient override verbatim ("the NEXT_PROMPT MERGED line is WRONG — PR <n> is OPEN"), because the fire
  reads NEXT_PROMPT before any tool call and will otherwise start the next pick.
- **A continuation fire into a dirty worktree must be told not to clean it.** The stored prompt's first
  step expects `main` clean; when the dead fire left uncommitted remediation on `milestone/<id>`, the
  override says: do NOT `checkout`/`reset`/`stash`/`clean`; re-run the acceptance from the WORKING TREE,
  commit the remediation, then `git fetch && git rebase origin/main` (name the current trunk hash — the
  stored prompt carries none). Name the review findings' file path as well; a fire left to find it spends
  calls it does not have.


## s290 retirement from SKILL.md (VERBATIM)

*(Historical text moved verbatim at s290; internal "full text" pointers reflect the pre-split layout and may be self-referential — this file is the canonical location now.)*

- **A memory sampler is the fastest way to blow the evidence budget, and pruning cannot save it.** A
  `/proc/<pid>/mem` poll loop with no sleep runs tens of thousands of samples/s — a 150 s run wrote a
  **1.4 GB** trace and turned the gate RED *after* the milestone work was already done. Sleep the loop (2 ms
  is the sampling cadence the footing asks for anyway), and downsample before the first commit: keep the first
  sample, every sample where a watched field CHANGES, one heartbeat per second, and the last — 1.29M samples
  collapse to 68 lines / ~10 KB with the boundary sequence intact. A giant blob also stays in the branch's
  HISTORY once committed, so a later delete does not un-poison a push (see `references/git-workflow.md`).
- The full-disassembly cache `evidence/m53j_text.txt.gz` (~5.7 MB, what the zgrep method runs on) is PRUNED
  from the worktree when the gate nears 30 MB; it is git-kept — recover with
  `git show 733322c6:evidence/m53j_text.txt.gz > evidence/m53j_text.txt.gz` (repo root) before zgrep.
- **Delegated decodes: a child's claims are TESTIMONY, not evidence.** A child can map a 1450-line function in
  minutes; re-read from the cached disassembly: (1) every store site it cites, with its immediate; (2) the
  address arithmetic that lets the value REACH the field — a store guarded to an index past the array is dead
  code, so check the guard before believing the value exists; (3) the function boundary (`zgrep` the `ret`)
  before accepting any "written in the caller, not the callee" attribution, where decodes drift. Write the
  audit to `evidence/<id>_verify.md`; label instruction-stream facts VERIFIED and branch semantics INFERRED.
