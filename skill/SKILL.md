---
name: smac-cvr-format
description: "Use for SMAC .cvr Caviar voxel decode/render or SMAC RE."
---

# SMAC .cvr = Caviar voxel models

Sid Meier's Alpha Centauri (1999) `terran.exe` + `programs/*.cvr` live in
`~/reverse/smac/` (durable). Full writeup: `~/reverse/smac/FINDINGS.md`.
**Versioned at `github.com/wronglebowsk/smac-re` (private)**; a copy of this skill is tracked
in-repo under `skill/` — after editing the skill, refresh it there and push. Game binaries,
`programs/`, `smac.iso`, `glsmac/` and regenerable Ghidra/FLIC output are gitignored: never
`git add -f` them.
Decoder + iso renderer: `~/reverse/smac/cvr_decode.py` (validates 113/113).

**This file is deliberately small (~18 KB — safe to load whole, and `wc -c` keeps it under the repo's
70,000-char FAIL).** Depth lives in `references/`; open the ONE file you need:
`code-atlas.md` (record/field layouts, VA→function), `wine-operations.md` (driving, dialogs, watchpoints),
`solo-round-boundary.md` (solo heartbeat model, auto-end timing, boundary diff accounting),
`production-rebuild.md` (production-vector machine rules), `production-queue.md` (the build queue: gate,
completion chain, and **the INSERT is not a sort** — it writes `queue[pos]=item` with
`pos = *(int *)(0x6a9480 + 0x3ff5c)`, the QUEUE WIDGET's cursor row, so the plan-byte (`+42`) order
M67 measured is the WIDGET'S LIST order, not an enqueue comparison; **who writes that cursor** (row
click `0x40aae5` -> `min(row, [[0x8f0d60]+0x4c]+1)`, enqueue tail `0x417e3b` -> rows+1, the `0x4d00`
handler `0x4194b3` -> 0; clamp against the WIDGET's row count, not the base's pending); **the
completion's POP pops ONE item when the new head validates and left-shifts only `0..pending-1`
— K shifts are not shift-left-by-K, `queue[pending]` stays stale, and the completion writes the
cursor field ZERO times**; **the visit's OWN affordability test is `0x4efa5e` with `edi` = its cost
product, NOT `price_of` — head 193 wanted 27 where `price_of` said 18 — and its bail is `0x4efa63`,
instrument `scripts/m72_gate_watch.py`**), slots
1..`pending` (never the head slot), the engine refusing a duplicate id, a recordless type stored as a
NEGATIVE (-3/-6), the produced-unit freeze, mock-mem predictor tests), `static-store-census.md` (store census shapes, table
reading, the live write-enumeration acceptance in §9, and §10 (why a site never fires: its gates, the block's common exit, who sets the gate global)),
`ptrace-level-probes.md` (strace raw args = read buffer POINTERS, soft-dirty/pagemap, maps before/after,
one tracer per task, the candidate table for "who wrote these bytes with no store in my window"),
`wine-headless-harness.md` (turn automation), `open-leads.md` (unanswered questions with cites),
`screen-read.md` (why ONE OCR pass is not a screen read: the HUD's two rows, their measured read
rates, what N looks mean), `git-workflow.md`, `wine-runnability.md`, `data-formats.md`,
`ghidra-batch-export.md`, `terraforming-order-path.md`. `grep -n '^## \|^- \*\*' SKILL.md` then `sed -n 'A,Bp'` the section you
need. When adding depth, append to the right reference; only new cross-cutting pitfalls belong here.
**Before statically deriving a field or mechanism a kickoff prompt names, grep the skill's `references/` and the repo docs for that offset/mechanism** — much of the UI plumbing (chooser bars, its cancel sentinel, the handler case map) is already settled in `references/wine-operations.md`; a from-scratch objdump derivation spends ~15 tool calls re-deriving a settled answer, and instruction bytes are the arbiter only for a CONFLICT, not the first move.
The same rule kills NEGATIVE claims: before writing "no code uses constant X", grep the docs' size/offset lists for X AND its near neighbours — a documented 152-B leg is 156 minus a 4-byte field, so an exact-value grep for 156 supports a conclusion that is one subtraction wrong. Then confirm the candidate leg by reading its DESTINATION in `/proc` and comparing content, not by its size (`references/instrument-laws.md` §Proving a read leg).
Master plan / exit gates (G1–G4) / phase list: **`~/reverse/smac/ROADMAP.md`** — read it before picking
a milestone. Phase 0 = harness + state reader + full Ghidra export + coverage ledger; do it before more
RE. Five spines (boot, solo turn, unit orders/combat, research/tech, save/load) drive Phases 1–2.

```bash
cd ~/reverse/smac
python3 cvr_decode.py "programs/*.cvr" "programs/*.CVR"   # validate corpus
python3 cvr_decode.py --list Apsid.cvr                    # voxel/frame listing
python3 cvr_decode.py --render programs/Drop.cvr          # -> Drop.render.png in cwd
```

## Git workflow — `references/git-workflow.md`
Never commit to `main`. `milestone.py start <ID>` branches from **`main`**, so a milestone you must
build on that was never merged (an acceptance FAIL left it on its branch) has NONE of its scripts in
the tree — branch from it instead (`git checkout -B milestone/<ID> milestone/<prev>`) and say so in the
session entry, rather than discovering the missing instrument halfway through the run.
`milestone.py start <ID>` refuses a dirty worktree: stash the `SESSION_CURSOR.md` write, start, then pop
it onto the new branch — never commit a cursor write to `main` just to get the tree clean. That commit is also what breaks a
landing — a squash merge plus any local `main` commit makes `merge <n>` abort its ff-only pull AFTER
GitHub has already merged (recovery in `references/git-workflow.md`) — and `main` cannot be pushed at all
(the pre-push hook refuses), so a post-merge cursor/footing tweak rides its own branch + PR. When the milestone you are re-running already has a branch, `start <ID>` refuses and leaves you on `main`:
check that branch out and `ls scripts/<id>*` before concluding the instrument is missing.
**Verify the named milestone is not already merged before starting it** — a kickoff prompt (re-pasted or
cron-supplied) can lag the repo. `git log --oneline | grep -i <ID>` plus `grep -n '^## <ID>' NAMED.md`
answers in one call; if both hit, the prompt's pick is stale, so run the milestone
`SESSION_CURSOR.md`/`NEXT_PROMPT.md` names and state the swap in the report. Re-running merged work
spends the tool-call budget and re-derives a settled answer.
Cycle: `python3 scripts/milestone.py start <ID>` → work → `gate.py --base main`
(must be GREEN) → `submit --title …` (commit + push + PR) → `gh pr checks <n>` → `merge <n>`.
**Create the PR with a JSON FILE, not an inline `curl -d`:** a body containing an apostrophe (`tail's`,
`decompiler's`) closes the shell's single-quoted payload and the whole command fails to parse, so NOTHING in that
block runs — including the `git push` before it — and the next attempt returns 422 `head invalid` rather than a body
error. Build it with `json.dump({...}, open('/tmp/pr.json','w'))` and post with `curl --data @/tmp/pr.json`.
**Merging several PRs in one session is queue-bound, not build-bound:** `gh pr checks` can sit `pending` for 2-4
minutes with the job merely QUEUED, so poll with a ~200 s sleep instead of re-submitting; `milestone.py merge`
correctly refuses while a check is pending, and a force-merge is never the answer.
**A GREEN gate is not permission to merge.** The gate audits docs, evidence and the harness; it says
nothing about whether the milestone's acceptance passed. If the acceptance printed FAIL, keep the
checkpoint commits on the branch, submit nothing (or leave the PR unmerged), and report the FAIL with
its numbers — a branch carrying a documented FAIL is the honest end state, and weakening a threshold
to turn it green is the one thing that is never allowed.
**A squash-merge TITLE outlives the finding inside it.** `milestone.py submit` titles the PR with the session
headline, and a milestone often opens as "BLOCKED / not accepted" and only resolves later in the same branch —
the merged title then contradicts the merged commits, and the next session reads the title first. When that
happens, land a small docs PR that states the correction (cursor, ledger row, one line saying the title
predates the result) instead of leaving two versions of the truth on `main`.
Each milestone ends with a `## Session N` section in `SESSION_NOTES.md` and a rewritten
`NEXT_PROMPT.md` (<=15,500 bytes). `scratch/` is gitignored: scratch probes and one-off tools are
NOT repo products — a checkpoint commit after scratch-only work correctly commits nothing; the
tracked products are `scripts/`, `evidence/`, and the docs. After editing the LIVE skill, `diff -rq ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/` first, then copy whichever side is NEWER — plain `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/` when the live skill is ahead, `cp -a ~/reverse/smac/skill/. ~/.hermes/skills/smac-cvr-format/` when the repo copy is (a sibling session may have edited it since, and a blind `rsync -a` overwrites its newer references with yours)
— the gate compares only `SKILL.md`, so an edited reference, template or script drifts silently
otherwise. Editing this skill therefore leaves the repo copy stale until the next sync; do that
sync in the same session, before the closing commit.

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

Paul wants SMAC RE broken into **small pieces**: complete ONE milestone, write it to a
file, append one dated line to `~/reverse/smac/SESSION_NOTES.md`, then STOP — ending
after a single milestone is a success, not a shortfall.

Exception: when he says **"keep going until you finish <chapter>"**, that overrides the
stop-after-one rule. Work through that chapter's milestones, writing the doc + evidence
after each, and report once at the end — including what is still open. Do not relabel a
partial result as done to make the chapter look finished (see `MILESTONES.md` F2).

**A bare "keep going" after a report is approval for the recommendation, not a request for more analysis.**
When your report ends by naming the next step (merge PR N, spend the next acceptance, write the plan into the
pick), the go-ahead means DO that step and report in one screen — including `milestone.py merge <n>` on a green
PR. Re-asking or re-summarising costs a turn and reads as stalling; the discipline that still binds is one
milestone per merge and three acceptance invocations, not one question per step.

### The context ceiling is part of the task, not an accident

Hermes' compressor resolves to the MAIN model (`auxiliary.compression: provider: auto`) and cannot
summarize itself: attempts die on the output cap (`finish_reason=length`, aborted, ~132 s each) and the
gateway drops hygiene compression after a 10 s turn-hold. Measured outcome: CLOSING turns were cut
mid-sentence twice — the milestone was done and accepted, the paperwork never landed. Rules that follow:

- The window was DOUBLED to 524,288 tokens (`compression.threshold_tokens: 424,000`).
  Never quote a limit carried in from a prior session — read `~/.hermes/config.yaml`. A bigger window
  does NOT repair the compressor (same model, same cap); every rule here still holds.
- Budget by TOOL CALLS, not by feel: brief+accept_ready <= 6, milestone 6-30, **commit a
  checkpoint at ~25**, stop measuring at 30-40, close at 40-50.
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
  **Trust only `python3 scripts/evidence.py budget`** — it counts CHARS, not `wc -c` (15,988 bytes scored
  16,052 chars and failed). **Leave >100 bytes of headroom**: `scripts/test_loop.py` appends a few bytes to
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

### Verify the OUTCOME, not the mechanism

Depth: `references/verify-outcome.md` — a gate that counts the harness's own work passes a run that lost the
game (a 40-turn `PASS` with zero bases); compute candidate predictions from the baseline before the run, refuse a
shape where your model and the null agree on every candidate, and read the effect back from memory/state.
**Publishing rule (§Publishing rule): one instrument is a lead, never a finding** — pair it with one that can fail
DIFFERENTLY (a byte sum vs a poke-and-scan, a log vs a live read-back), assert the state the run leaves behind
(`TracerPid`, counts, armed count) rather than its exit code, and pre-register the falsifier.
**An exit code is a claim, so make it mean what its reader will assume.** A harness that exits non-zero for a
NEGATIVE result (`the site was reached and never taken`) makes its own finding read as a broken run and costs the
next session a debugging pass on a green answer. Encode the four states explicitly and PRINT which applies:
**0 = measured** (taken or not), **4 = the site was never reached** (inconclusive, not a gate result), **5 = the
driver wedged / produced no orders (NO MEASUREMENT — never file it as evidence the gate is inert)**, **8 = the box
was left dirty** (`TracerPid != 0`). A wedge and a negative result are different facts; conflating them is the same
failure class as a stale-gdb "success".

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

## Code atlas — read `references/code-atlas.md` before opening Ghidra
The address/field atlas (base-record offsets, terrain record formula, faction + unit records, the global
map, pointer-type scale traps, VA→function recipe) lives in `references/code-atlas.md`. Open it when you
need a field offset — do not re-derive one from pseudocode: Ghidra types some DATs `short*`/`int*`, so a
pseudocode offset can be HALF or 4x the real byte offset.
Unit-record type field: the u16 at `+10` (`+4` = flags) — settled from the accessor;
the full story + the two generalizing rules are in `references/code-atlas.md`.
Fast handles: full `.text` disassembly `evidence/m53j_text.txt.gz` (GZIP — `zgrep -n '  4e78e9:'` then
`gunzip -c … | sed -n 'A,Bp'`); owner of a VA `awk -v A=0x… -F, 'NR>1 && strtonum($1)<=strtonum(A){n=$2;p=$1} END{print
p,n}' ghidra_out/index.csv` (commas, no spaces; strtonum REQUIRED — bare `$1<=A` is a STRING compare, every row matches
and you get the file's LAST function, not the owner); pseudocode `scripts/fn.py 0xADDR` (prints the index row as header).
Parse objdump by TAB fields (bytes sit between address and mnemonic); require `^[0-9a-f]{6,8}:\t` before int(x,16) — details in `references/code-atlas.md`.
Two static instruments answer "what IS this field" with no box time: `scripts/name_global.py <addr> [--disp]`
(every referencing instruction, its containing function, and whether it reads, writes or tests — use it before
naming a global from the one reader that mattered) and `scripts/field_census.py [stride|bit5|readonly|copy|dual]`
(the five shape checks: stride unanimity over all sites, a gate's index provenance, a zero-writer proof, a
copy-vs-array discrimination, and dual addressing forms for one address).
**The census family, one shape per script** — reach for these before writing a new probe: `field_census.py` (a
displacement's shape), `name_global.py` (every reader/writer of a global, with containment),
`m118_flag_never_set.py` (is a gate satisfiable AT ALL: test sites, OR immediates, register-level bit ops, and whether
any SAVE carries the bit), `m124_state_and_memo.py` (a state code named from the strings printed around its writers; a
memo-invalidation store), `m127_m129_fields.py` (one field's two addressing encodings, a pre/post-call pair, a guard
that CONSUMES a flag), `m130_m132_chooser.py` (a switch read straight out of the PE jump table), `m133_m142_census.py`
(ten globals in one pass: refs, writes, stored values, containment), `m163_m165_structs.py` (an init-time value, plus
struct-vs-neighbours proved by base-register reuse), `m166_m168_roles.py` (what a rank is compared against, a candidate
struct's writer SETS, a derived cache), `m169_m171_aggregate.py` (a table that is TOTALLED rather than flagged, the
aggregator around it, and a struct written from ONE byte). Ten census questions through one script is a
legit batch; ten that each need their own harness is ten batches. The per-faction FIELD ATLAS is generated, never
hand-written: `scripts/m143_m162_atlas.py` -> `docs/field-atlas-faction.md` (top-20 `+0x94dXXX` displacements by
reference count, with refs/writes/consts/tests/functions) — regenerate it instead of re-censusing a field, and read its
`in NAMED?` dash as "genuinely unnamed", not as a gap to be filled by a guess.
**Three structural laws this family settled** (depth: `references/instrument-laws.md`): (1) a decompiler's `arr[i*N]`
is an ELEMENT index — multiply by the element width before calling it a stride, because `param_1*0x167` was 359
dwords = 1436 BYTES, the stride the record block already had; (2) a `switch` is found by its TABLE, not by the
address range you expect — scan every `jmp DWORD PTR [reg*4+imm]` for the ones behind a bound check on the same
register, since this dispatch sits in the CONSUMER of a helper and keys on that helper's return; (3) count a record
field in BOTH encodings (`[reg+0x2a]` literal AND the folded `[reg*4+abs]` where the register already holds
`index*stride`), because a literal-only grep reported "zero readers" for a field that has 369.
**Three more laws, all about how a field is SHAPED by its readers and writers:** (4) degree asymmetry is evidence — a
displacement with hundreds of readers and ONE writer is an init-time value (a rank/order), so read that single writer
and its loop instead of sampling readers; (5) a candidate struct is proved by (function, base-register) reuse —
several pairs addressing SEVERAL of the offsets off one register — and its parts are then separated by writer SETS,
because equal write COUNTS hide the split (a header dword with its own writers plus a payload quad written together
by a different shared set); (6) read the writer's SOURCE before naming members: `setne`/`shr`/`and` chains mean the
fields are booleans of ONE source bitfield (one byte expanded into four dwords, a tristate header, and an `or` into a
DIFFERENT word as a side-effect), and a displacement with many writes but almost no tests is a recomputed CACHE,
never state a gate may read.
The chooser/dispatch state family (dispatch table, list seek, state+mode pair, the counters around it) is mapped in
`references/ui-chooser-state.md` — read it before re-deriving any of it.

## terran.exe PE layout (verified 2026-10-20 via section table + byte reads)

Image base 0x400000. Sections (RVA): `.text` 0x1000 + vsize 0x26f3f4 ⇒ VA **0x401000–0x671000 with
raw bytes present** (`55 8b ec` prologues verified at 0x520e70, 0x51e700, 0x5d0c33 WNDPROC, 0x62ad73
FLIC, 0x6309aa DP-init); `.data` RVA 0x289000 vsize 0x316284 but **rawsize only 0x20000** ⇒ data above
VA ≈0x6a9000 (`DAT_0091f6c4`, `DAT_00985b10`, `DAT_0099d020`, …) is uninitialized/BSS at runtime and has
**no bytes in the file**; then unnamed/UVA_DATA/_SELFMOD/.rsrc/.reloc, last section ends RVA 0x5e4000
(VA 0x9e4000).

Consequences — this **corrects the earlier "self-modifying, analyzed image ≠ file image" note, which
mixed RVA with VA**: (1) **all game CODE is in the file**; Ghidra's decompile of any `FUN_` (including
0x5dxxxx–0x66xxxx) is authoritative, and runtime breakpoints at those VAs fire (M7/M8 proved it); (2)
only *data* reads above ≈0x6a9000 need a runtime snapshot (`gdb -batch -ex 'dump binary memory …'`);
(3) `_SELFMOD` is a 0x415d-byte section — a small patch area, not a whole-image unpacker, so there is no
"import of the wrong image" problem.

## Map + save container formats

Fully decoded: the repo docs (`MAP_FORMAT.md`, `SAVE_FORMAT.md`) are canonical and the depth lives in
`references/data-formats.md` — the `.MP` size formula, the `.SAV` section list with its two record strides
(52 B / 304 B), the byte-exact anchors, the read-wrapper caller trace that cracked both, and the
zeros-fraction pitfall. **The last 156 B of every save is a fixed TRAILER, not game data** — the final
152 B are identical across nine saves, only the trailing dword varies, and its offset moves with the file
size, so no hard-coded leg can index it; Its reader is the **6-site per-entity loop** that restores each row into per-entity heap records
(stride `0x224B8`), proved by POKING a marker into the rows and finding it in memory — never by a byte sum
(`references/data-formats.md` §`.SAV` trailer; `references/instrument-laws.md` §Identify bytes). The offset->
memory map itself is anchored the same way: `scripts/m113_save_map.py` plants markers at known offsets and
reports where each lands — 1:1 inside a section, a JUMP at a boundary (`references/instrument-laws.md`
§Extract a LAYOUT with anchors, `references/data-formats.md` §anchors).
**Any file-vs-memory diff goes through `scripts/save_diff.py`**, never an ad-hoc window: the mapping constant `k
= dest - off` is PER REGION, so a window that straddles a section boundary and is diffed with one region's `k`
manufactures hundreds of "diffs" that look exactly like rewriting. `save_diff.py` derives the regions from the
anchors, refuses a range crossing a known boundary (67,852 / 82,088 / 172,200 / 172,291 / 222,783) and names the
boundary it refused on; `scripts/test_save_diff.py` is the PASS 7/7 guard. Done properly the restore is 1:1 for
every byte of block A, block B, the map header body and the grid — divergences are only a few leading bytes and
two dwords in the 52-B records, so a "rewritten section" finding needs the guard's agreement first.
Parsers: `scripts/decode_map.py`, `scripts/decode_save.py --sections --anchors`.
`FUN_00597a70` is the save/scenario block loader (NOT the map loader — the grid is read raw by
`FUN_00582260`); the .SAV chain and its two read paths (kernel in-place vs ring-3 scratch) are
`references/ptrace-level-probes.md` §The .SAV chain.

## Format core (verified; details in FINDINGS.md)

- TLV chunks `u32 LE tag + u32 LE size incl. header`; outer tag `0x00525643`
  ("CVR\0"), size == file size. Children: 0x01000000 version float (10.0/10.1 —
  NOT a scale), 0x02000000 .MAX scene name, 0x03000000 palette group
  (0x01010000 name, 0x01020000 palette data 6914 B = u8 first + u8 last +
  256×RGB24 + 24×256 shade table, 0x01030000 material 12292 B = 4-byte header +
  24×256 u16 R5G5B5), 0x04000000 scene group (0x4010000 name, 0x4020000 object
  count, 0x4030000 frame count, 0x4040000 per object).
- Object: 0x4040100 name, 0x4040200→0x4040201 VOXEL blob, 0x4040300 animation
  (0x4040301 frame flags 1B/frame, 0x4040302 float32 locations **Z,X,Y**,
  0x4040303 3×3 float32 matrices) — animation-only files exist (Asas.cvr).
- VOXEL blob: VOXEL_HEADER 42 B (flags, size, units-per-pixel float, next, end,
  int16 ZXY scale/position/rotation-center, count). flags&1 = header chain at
  h+next; flags&2 = JUMP_HEADERs (32/36 B, run starts at position+offset).
  Voxels = 3 B: (dir<<3|normal_hi), normal_lo, color index; dir = 5-bit delta
  over 27 steps, 0x1A STOP (STOP-coded last voxel is real); normal = 11-bit
  angle code `((dir&7)<<8|lo)+88`, a1=88−n%89, a2=n/89 → unit vector.
  Regions end with 5 zero pad bytes. Count quirk: single-header jumps
  Σjc=count+groups, multi-header jumps Σjc=count.
- Chunk parse addresses in terran.exe: loader 0x614acb, top loop 0x6446e0,
  per-object 0x644f80, blob stored opaquely by 0x645170. Voxel semantics are
  wiki (alphacentauri2.info/wiki/Caviar) + corpus verified, not exe-verified.

## Multiplayer netcode (mapped — details in FINDINGS.md)

- Internal netcode codename **"jackal"** (debug strings `jackal` +
  `NET_SENDTIMEDOUT`, title "Message from the Net Underworld").
- DirectPlay via COM-style init `FUN_006309aa` (GUID {9d460580-a822-11cf-…}
  @0x67bcf0); DP object global **`DAT_0099d020`**, vtable +0x14 GetMessages,
  +0x68 SendData, +0x28 CreatePlayer. DPLAYX IAT slots have zero Ghidra xrefs.
- Packet: 12-B header (u8 DP flags, u32 seq, payload u16 type @+0, sender
  u32 @+2); builder `FUN_00584010` → router `FUN_0052a260` (type&0x4000=
  guaranteed broadcast, &0x8000=directed, 0x2000=server-originated) →
  `Net::send FUN_00635407` (16×0x58 slot table @this+0x150, seq
  this+0xe0, adaptive ack/timeout). Anti-replay gate `FUN_00639787`.
- Receive: thread `FUN_00638d5c` → `FUN_00638ddd` (GetMessages + gate +
  queue `FUN_0063af12` + PostThreadMessage 0x402) → main drains
  `FUN_005262e0` (in-game queues)/`FUN_00526e10` (synch queues 0x80–0x8d)
  via `FUN_0052a720`+`FUN_006361ff` → dispatcher **`FUN_0052bce0`**.
- Diplomatic types 0x2440–0x244e = DOUBLE CROSS/TREATY ON/OFF/SET/AGENDA
  ×3/ENERGY/TRADE MAPS/CEDE/WITHDRAWAL/TECH/LOAN, one wrapper each
  FUN_00530640–0x530c40 (asm-verified). AI hub `FUN_00546800` (34 send
  sites). Turn sync: client LOCK(0x2210)/DONE TURN(0x8301) → server
  EXEC DONE/NEXT TURN via 0x1240/0x1501/0x4301/0x4303.
- File-name traps in ~/reverse/smac: `treaty.pseudocode.txt` = FUN_00546800
  (not 54d5f4); `killfaction.pseudocode.txt` = FUN_0047c0e0 (UI pane);
  FUN_0047e846 has no callers/pointers — KILLFACTION is a voice-clip token,
  not a message type. UPPER_CASE tokens 0x68b000–0x691600 are sound/voice
  clip names, not protocol opcodes.

## Goal (Paul's priority)

Play SMAC **single-player with working AI** on modern hardware **and recreate
the full menus + game UI** (reimplementation target). Multiplayer netcode is
mapped but secondary. UI groundwork: CPane/CWidget pane builders (e.g.
`FUN_00444140`, `FUN_0047c0e0`), PCX v3 art (`programs/*.pcx`/`.flc`), `.sc`
scenario files, voice/sound clip token strings 0x68b000–0x691600, UI widget-name
strings (TOUR1*, SOCTOUR*, DRONETOUR*).

## UI / asset pipeline

- **Script.txt IS the UI**: `programs/Script.txt` declaratively defines
  1,357 dialog panes (`parse_script.py` → `script_parsed.json`). Grammar:
  `#NAME` pane start (UPPER id), `#xs` width, `#x/#y`, `#caption`,
  `#button`, `#itemlist`, `#listbox`, `#wave N` sound, `^`/`^^` newline/
  center, `{}` bold `[]` italic, `$NAME123` substitution, `$<n:a:b>` gender.
  Menu trees (TOPMENU/MAPMENU/MULTIMENU/SCENARIOMENU/setup chain/RULES/
  SCENRULES/victory/editor/intro) verified. Spec: `~/reverse/smac/UI_MAP.md`.
- **alpha.txt = the rules file the exe loads** ("reads the rules of the game from this
  file"): 45 `#SECTION`s / 650 comma-separated records (`#RULES`, `#TERRAIN`, `#TECHNOLOGY`,
  `#CHASSIS`, `#WEAPONS`, `#UNITS`, `#FACILITIES`, `#SOC*`, `#DIFF`, `#FACTIONS`…). Parse it
  (`scripts/parse_alpha.py` → `data/alpha.json`, section map in `ALPHA_RULES.md`) rather than
  RE-ing balance constants. Field names are recoverable from the trailing `;` comments for only
  4/45 sections — `#CHASSIS`/`#UNITS` etc. are bare data, so their semantics must come from the
  exe's parser, not from guesswork.
- **`maps/*.MP` = the map format** — now fully decoded, see "Map + save container formats"
  above and `~/reverse/smac/MAP_FORMAT.md`. (This bullet used to claim the loader was
  `FUN_00597a70` and that the 796-byte header's offsets were unresolved; both were wrong —
  that function is the save path and the map header is a 2,724-byte struct at offset 15.)
  `FUN_00598340` is still the magic/version dispatcher.
- **PCX**: SMAC variant starts `0A 05 01 08`; Pillow 12 decodes all 378
  correctly (`assets.py pcx programs png`; sheets in `sheets/`). Hand RLE
  decoder unsolved; glsmac hits same wall (SDL_image + procedural fixes).
- **FLIC format cracked** (not standard Autodesk): 128-B header u16
  words: w2=0xAF12, W=u16@+8, H=u16@+10 (monument.flc 1024×768 ✓),
  w6=8; frame chain @128 = `u32 LE size` + u16 0xF1FA + u16 subchunk
  count, sizes tile to EOF (turn.flc 1081+18×196+16=4473 ✓). Exe:
  loader FUN_0062ad73, dispatch FUN_0062bdeb (chunk=u32 size+u16 type;
  F1FA=container recurse; types 4/0xb/0xc/0x12 no-op stubs incl. the
  772-B color table; 7=16-bit small-brun FUN_0062b68e; 0xf=8-bit brun
  FUN_0062b3da: per row u8 width then s8 packets (>=1 literal, <0 RLE
  w/ next byte, +ref variant); 0x10=raw rows FUN_0062bc1d; 0xd=clear;
  delta table flag|2: 7→FUN_0062c36f (copies unchanged runs from prev
  buffer @this+0x4ac when run color == transparency)). Decoder scripts
  `flc_decode*.py`; type-7 RLE word color semantics + per-object ref/trans
  still being pinned. See UI_MAP.md.
- **glsmac** (afwbkbc/glsmac, cloned at `~/reverse/smac/glsmac`): working
  SDL2/GL SMAC reimplementation; hardcodes UI (does NOT parse Script.txt);
  resource enum names master atlases (palette/interface 750×900/icons/
  units/console_x/moon1-3/S{s}L{l}C{c}/arialn.ttf). Useful reference.

## Running under Wine — top pitfalls (depth: `references/wine-operations.md`)
- **Preflight is one command, and it comes FIRST:** `python3 scripts/smac_preflight.py` (read-only,
  exit 1 on any FAIL) checks the authoritative address table, `terran.exe` alive with `TracerPid: 0`
  and no stray gdb, and prints OUR bases BY NAME with index/coords/pending/head/minerals/income plus
  the unit decode, /tmp room and the evidence budget. `SMAC_PID=<pid>` overrides the pgrep; it is also
  the negative test. Window is 10485761 (800x600). `xwd` needs **`-display :99`** (`DISPLAY=:0` captures blank). `scripts/session_brief.py` and `accept_ready.py` print `BLOCKED: terran.exe not running` (exit 1) when the
box is down — read that as "relaunch first". A `CalledProcessError` traceback from either means the checkout
predates the pid guard (`M.find_pid()` unguarded): fix it there, do not fresh-load blind. It reads the LIVE box, so it runs for
MINUTES: request `timeout 400` (or background it) instead of the default, and read a timeout as slow, not as hung.
- **X input focus is a precondition — but `getactivewindow` is a RED HERRING on this display.**
  `xdotool getactivewindow` ALWAYS fails on :99 (no WM supports `_NET_ACTIVE_WINDOW`; it errors
  "claims not to support" even when focus is perfect). The authoritative check is
  `xdotool getwindowfocus getwindowname` == "Sid Meier's Alpha Centauri", and
  `xdotool windowfocus 10485761` works WITHOUT a WM (windowactivate is the WM-needing verb; s136
  misread this and lost a session). Prove keys land cheaply before blaming the box: one Escape on an
  open base pane flips classify base->hud. A box CAN still swallow turn-end input with focus fine:
  at the s135 state (2150 r50) XTEST Return AND a click on the measured TURN COMPLETE center both
  did nothing (no confirm dialog, round unchanged) — the repair is a fresh save load
  (`SMAC_SAVE=... scripts/m54a_load.py --relaunch`), which restored the boundary immediately.
  `scripts/m44_idle.py` is NOT a driver under gdb: it asserts `TracerPid == 0` at entry (census gdb
  IS the tracer) and its `--rounds 1` snapshot condition `y > last_year - 1 and not rounds` counts
  the CURRENT turn as a completed round, so it exits rc=0 in 0 s having done nothing — use
  `scripts/m55_boundary.py` (no tracer assert, windowfocuses itself) as the boundary driver.
  Corollary for acceptances: any milestone whose PASS needs a boundary must gate on a live year/round
  DELTA read from /proc/pid/mem first, or it will "prove" its sites unreachable from a box that
  could not run them at all.
- **Vision-tool coordinates are SCALE-SHIFTED on 800x600 frames; click targets must come from OCR
  word bboxes or pixel scans.** s137: vision put the TURN COMPLETE bar at y~471 (real y 405-427, OCR
  bbox center 675,416); the click at the vision coord hit the recenter box (y~484) and only scrolled
  the map — it looked like "clicks land but the engine ignores the button".
- **"Do you really want to quit?" is the killer dialog.** Escape returns to "Oops, no, wait!"; never
  click OK (the next OK exits the game and the process vanishes silently). Its banner IS the game title,
  so a classifier can mistake it for the title screen — this is also why the driver's own Escape press
  pops it mid-drive.
- **`scripts/smac_play.py` has no `--mode stop`.** Args: `--turns --timeout --no-escape --verbose
  --order --unit --turns-after --tag --no-verify --key-only` plus the M54c in-loop order flags
  `--orders-per-turn N` (default 2), `--order-budget S` (default 35), `--no-orders`. Ordering is
  ON inside the unattended loop now: each player turn pokes the selection slot, fires one hotkey,
  services the pane, and verifies `unit+17` moved into the byte set that key may produce — an
  order counts only as that memory delta, never as a screenshot. `--no-escape N` = "press no Escape during
  the first N seconds" — set N above `--timeout`. Bound a backgrounded driver with shell `timeout`.
  Launch a long run through the agent's tracked background mode (`exec python3 scripts/smac_play.py
  … > /tmp/<tag>.log 2>&1`), never `nohup … &` — nor ANY `&`-backgrounded chain, `cmd && other &` included — in a foreground call:
the wrapper is refused there (re-send the whole thing through the tracked background mode), and
  a shell that backgrounds and exits hides the driver's own pid — find it with `pgrep -f smac_play.py`
  and `kill <pid>`. Never signal by name (`pkill -f`/`pgrep|kill` matches your own argv).
- **A PROPOSAL vote pane stalls the AI phase.** `YEA: 2  NAY: 3` is the TALLY, not a key hint. Bars in
  TRUE window coords: YEA (310,495) / NAY (398,495) / ABSTAIN (485,495), single OK (393,495); click only
  after `xdotool windowfocus <win>`; OK >= 1.2 s after selecting. Capture with `xwd -display :99 -root
  -silent`, 2x ffmpeg upscale, tesseract (>=4 chars, region-constrained).
- **A round advancing while you watch is AUTO-END, not progress, and a walk frozen on an AI faction is
  a modal event dialog, not a livelock.** With all units HELD the engine closes our turn on its own in
  1–2 s; `cur_player == ours` is a window, not a state. Heartbeat model and dismissal cadence:
  `references/solo-round-boundary.md`.
- **Auto-end does NOT fire while any unit is actionable — and a unit built at the boundary is.** So
  HOLD every record (`+17` = 2, poked with TracerPid 0 and read back) BEFORE arming a multi-boundary
  watch: held units flip a round in 1-2 s, an unheld box sits parked on our turn for the whole budget.
  A produced unit arrives order 0, the cursor parks on it, and Return every 2 s for 150 s changes nothing
  (`cur_player` ours, `turn_flags` 0, year unmoved). ONE `h` on the cursor unit (→ HOLD) closes the turn
  at once, and that `h` needs orders mode `0x91b5b8` = 1 — at 0 every order key is a silent no-op
  (the base-display recipe turns it off, so restore it), which looks exactly like a wedged turn.
  And a popup whose default row is not OK does not close on Return — Return CYCLES its options
  (Operations Director defaults to "Zoom to Base Control"); click its OK instead. The end-turn
  confirm ("SOME OF OUR UNITS HAVE NOT YET MOVED … do you really want to end the turn now?") takes
  NO Return at all: click its YES row and then the OK bar ~26 px below, 1.2 s apart
  (`smac_play.answer_confirm`); a driver that only presses Return sits on it with the year frozen
  until its whole budget is gone. When the year stops moving, take ONE frame and `classify` it
  (it returns `confirm`) before pressing anything else. Cadence, coords, and the queue/gate rules:
  `references/production-queue.md` — including why an arrival round predicted from ROUND-START fields
  is not exact (the visit recomputes `+0xd0`, so the same snapshot produced no arrival and then an
  arrival one round later), and the store-sequence accounting that replaces it.
- **A stalled round can be a LIVELOCK, not a modal:** run `python3 scripts/m53q_livelock.py` (census of
  the `unit+48`/`unit+50` chains; `--fix` repairs). Signature: `turn_flags` bit 1 set + a hot main thread
  + byte-identical screenshots.
- **A turn that never advances can also be a CLASSIFIER miss, with no modal visible.** OCR here is
  unreliable in both directions: a clean HUD reads `unknown` when the TURN COMPLETE row fails to
  render legibly — measured 2026-10-26: 8 freezes of ONE unchanged HUD put `complete` in the button
  row 3 of 8 times while the HUD's bottom status bar (`Mission Year` + the faction score row +
  `Energy:`, y 548-592) read 8 of 8, and the bar fragments differently (`sisson tear zie`,
  `esston 2388`) — which is why `accept_ready.py` re-freezes up to 4 times and believes the BAR
  twice rather than trusting one pass (`smac_play.hud_status_bar`, `accept_ready.verdict`,
  `references/screen-read.md`, `scripts/test_hud_bar.py`) — and with the production line drawn in the message box even the chrome
  (MENU/COMMLINK) goes illegible, so the clean-HUD oracle is MEMORY, not the chrome read:
  `cur_player == player`, `turn_flags & 2` clear, and no bar drawn at y 145-200. Peek one frame
  before running any Escape-on-`unknown` clearing loop — at a garbled-but-clean HUD it raises the
  quit prompt), and an advisor dialog
  reads `hud` when too few of its words land in the dialog band (its caption is the tell: a word of
  6+ characters, or two of 4+, at y 90-118 means something is drawn OVER the HUD). Both idle the
  loop silently: with `--no-escape` the first burns the whole turn budget doing nothing, and in the
  second every TURN COMPLETE click lands BEHIND the modal. Diagnose by reading the state, not the
  class: our phase + `turn_flags` clear + year unmoved = nothing is answering the modal.
- **Label a printed register from the encoding, and read entry arguments from `$esp`, not `$ebp`.** A
  breakpoint on a function's FIRST instruction sits before `push ebp; mov ebp,esp`, so `$ebp` is still
  the CALLER's frame: take the arguments from `*(int *)($esp + 4)`, `*(int *)($esp + 8)`, … and the
  caller from `*(int *)$esp` — the return-address field is the cheapest way to learn a function's caller
  set in the same window. Before printing any register as an index or offset, read the prologue for
  `mov reg,[ebp+8]`-style argument loads and check for a reassignment on the path that reaches the site:
  a callee-saved register holding arg 1 for the whole body is a PARAMETER (faction, owner, mode), not a
  cursor, and a ledger that calls it an index poisons later milestones. Print the raw value AND its
  derived forms (`$ebx`, `$ebx / 52`, `$ebx % 52`) so a mislabel is visible in the log, not discovered
  weeks later in a document.
- **Watchpoints:** x86 gives 4 hardware slots (an 8-byte window needs 8-alignment = 2 slots); pair with
  the 10 Hz poller `scripts/m53m_poll.py`; they fire on VALUE CHANGE, so a same-value rewrite is
  invisible. **Never watch a field the display reads constantly** (`base+0x40` mineral storage): the
  inferior crawls (a round per ~45 s, year apparently frozen) — break on the STORE sites instead and
  condition each on the address the store's OWN encoding computes — `[reg*4+disp]` means the register holds
`(index*stride)/4` and `[reg+disp]` means it holds the byte address, so a condition comparing the register
against the bare index never fires (`references/static-store-census.md` §9.3). At a store site the register side-values
  are not evidence (`$ecx` printed a base INDEX where d0 was expected): read the fields from the baked
  base address. **A bp on a LOAD prints the register's PREVIOUS value; a bp on a skipped loop's body
  never fires (a zero there is the gate); round-mutated values cannot come from a round-start
  snapshot** — `references/instrument-laws.md` §Where a breakpoint prints the wrong thing. Do **not** single-step for the after value — `si` inside a breakpoint commands list makes
  `gdb -batch` stop after the step and DETACH, ending the watch after one hit; for a plain
  `mov [reg+disp],src` the store's own source operand IS the value the field takes, and the sleeping
  `/proc/pid/mem` sampler is what proves it. A hardware watch reports `$pc` PAST the writing
  instruction — the store is the instruction BEFORE the reported address (a hit at `0x417e08` named the
  store at `0x417e04`), so disassemble BACKWARDS from a watch hit before hunting a store site. And when
  the field that governs the behaviour is a UI cursor/selection, POKE it and prove the write lands at
  the poked value: `queue[2]` for a cursor poked to 2 while the sort rule predicted slot 1 turned a
  confounded click observation into a controlled experiment (and refuse the shape when the poked value
  and the rival prediction agree). **A printf ERROR inside a breakpoint's commands block ABORTS the
  whole `gdb -batch` script and detaches the inferior mid-window**: the log truncates at the first hit
  while the turn driver keeps exiting 0, so an aborted window reads as a clean zero-event run.
  **A MEMORY WRITE in a command list fails the same way** — `set {int}ADDR = 1` and
  `set var *(int *)ADDR = 1` both raise `Left operand of assignment is not an lvalue` and detach at the
  FIRST hit; gdb reports the file's LAST sourced line (the trailing `continue`), so the line number names
  nothing useful and the message looks like a syntax problem in a script that armed fine. Signature of
  the whole class: an ARMED line + one `Breakpoint N at` per bp + `Error in sourced command file` + zero
  events, while the driver still exits 0 and its own writes land because the detach resumed the inferior.
  **So put the poke in Python, not in the breakpoint**: `fd = os.open('/proc/<pid>/mem', os.O_RDWR)` then
  `os.pwrite(fd, (1).to_bytes(4, 'little'), ADDR)` succeeds WHILE gdb is attached (a 50 ms thread held a
  gate global for a whole driver window: 632 writes, 0 errors, every printf-only bp logged). Keep the
  command lists print-only and let a thread hold the forced value; restore it after the window.
  **Guard every ARMED-time deref**: the selected-base pointer `ds:0x8f0d60` reads 0 until a pane is
  opened, so `*(int *)($b + 0x4c)` in the arming printf faults on address 0x4c and kills the batch
  before the first event — print `$b` alone or branch on `$b != 0`, and make a `/proc` reader return -1
  on `OSError` (an unmapped page raises EIO, not 0) so a bad pointer cannot abort the harness. gdb's
  printf reads an inferior pointer as a HOST address, so `%.20s` fed `*(char *)(rec+0)` errors
  ("Cannot access memory"); bp printfs emit NUMBERS derived from registers only (raw reg, reg/stride,
  reg%stride, `*(short *)(...)` values), never inferior strings, gate every pointer deref behind
`if $reg != 0 … end` (a null deref faults exactly like a string one and detaches the same way), and
substitute expressions as printf ARGUMENTS — an expression pasted into the
format string prints ITSELF and the log then parses as zero events (`references/static-store-census.md`
§9 point 10) — use `x/s` outside a commands block
  when a name is genuinely wanted. **A `dump binary memory` in a command list is the same class of killer:**
a non-literal target (`%s`, a convenience variable), an ARITHMETIC address range, or a
`python … read_memory … end` block each abort the sourced script at the first hit — the run logs `ARMED`
+ one `Breakpoint N at` per bp + ZERO events while the round keeps advancing, indistinguishable from "the
mechanism never ran". Bake the dump target as a literal absolute path (substitute with `str.replace()` on
a unique token), give the range two LITERAL addresses, and note convenience-variable arithmetic is 32-bit
SIGNED — an `end - start` inside gdb underflows and poisons every offset derived from it, so compute
lengths/offsets in Python and bake them as hex; one dump file per RUN with an `off=` field in the log
beats a per-hit filename (a second dump to the same path overwrites the first); **`append binary
memory` is what makes a per-hit series work** — plus loop-entry-vs-branch-target, the scan-window rule
and the snapshot-cadence law: `references/gdb-command-list.md`.
- **A hardware watchpoint cannot see a KERNEL write**: Linux installs a user DR breakpoint with the
  exclude-kernel bit, so bytes landing via `copy_to_user` inside a `read()` change with zero events —
  that is what a "silent census" means when a file read's destination IS the watched region. The fix is
  a different LAYER, not a re-armed watchpoint: strace `-e raw=` (prints the read's BUFFER POINTER) +
  `clear_refs=4`/pagemap soft-dirty + maps before/after; strace and gdb cannot both ptrace one task.
  Table, invocation and parsing laws:
  `references/ptrace-level-probes.md`.
Never build the gdb command list by running a Python `%`-format over
it: the template is full of `%d`/`%x` printf conversions and Python eats the first ones as its own
arguments, silently rewriting the breakpoints. Bake addresses and constants as literals, or substitute
with `str.replace()` on a uniquely-marked token, and diff the emitted `scratch/<tag>.gdb` before attaching. Bake addresses as literals, `stdbuf -o0`, drain gdb's pipe,
  and drive + snapshot in ONE backgrounded job (`scripts/m53n_drive.py` is the template). A **zero-event log is an instrument verdict until proven
otherwise**: arm one control breakpoint whose hit is guaranteed in the window and require its rows, and
read back BEFORE attaching that the watched event can even happen (queue head is the armed id,
`pending >= 1`, storage above what the gate can demand) — an unusable window is not a negative result
(`references/static-store-census.md` §9.8–9). **A whole subsystem path can be gated on another
subsystem's state**: with every base's production queue empty the research upkeep never runs, so a scorer
census logs zero events across boundaries while the round advances — satisfy the printed readiness FIX
before calling the sites unreachable, and echo the precondition in the harness's output so "gate unmet" is
distinguishable from "mechanism refuted".
- **A leg census gates on PREDICTIONS, not on hits.** Compute each site's expected hit count from live
  memory first (gate globals, args off `$esp`, the table values the branch loads), print the
  predictions, gate on agreement with the counters (`m86_helper_legs.py`, `m87_aaa20_trigger.py`).
  Demanding a hit at a site the TAKEN leg cannot reach FAILs the milestone, not the game — fix the leg
  map, never the floor. Tie every hit to a boundary (round/year at the hit); a window count is not a
  cadence.
**Before blaming a breakpoint for a zero, resolve the SITE's containment and its function's caller
count** from `ghidra_out/index.csv` — one read splits "unreachable BY DESIGN" from "UNTAKEN BRANCH". **To name who writes a field, use a hardware watchpoint on the address PLUS a
control watchpoint on an address you know changes** — a mnemonic grep misses stores made through
pointer-form `lea`. **A gdb census >90 s goes through `terminal(background=true)` + `process_manage
wait` loops: the foreground caps at 420 s and killing a census mid-run leaves Wine hung (round frozen
after detach too) — recover via `m54a_load --relaunch`. Pair store-readback probes by EVENT ORDER
(RB follows ST); a {addr: last-mem} dict mis-pairs an address re-written later in the window; and
**detach only after the window is really over** — the turn driver returns rc=0 while other factions'
upkeep is still executing, so the last stores happen after the detach and log NOTHING, which FAILs a
read-back gate on the instrument while every other gate is green
(`references/instrument-laws.md`).**
`references/instrument-laws.md` carries the header order, the containment recipe, DictReader trap,
the watchpoint laws, the value-census laws, the printf-escape law and the event-grouping law.

When the target is reached only through a vtable or handler table, the pre-arm check is whether an
INSTANCE of its class exists at all: scan the writable `/proc/<pid>/mem` regions for the class's vptr
value — a class with no live instance logs zero hits at every method, whatever the window (recipes:
`references/code-atlas.md`).
Two more pre-arm checks, both cheap, both fatal if skipped:
- **The readiness oracle can print a FIX that stays unsatisfied after you run it.** `credit` is
  `base+0xd0`, RECOMPUTED EVERY ROUND by FUN_004e93f0 (M97: `[+0xc0] - [+0xf0] - [+0xe0]`; the
  "init-only, turns never raise it" claim is RETRACTED) — it holds 0 when upkeep exceeds income, so the
  reload chain restores a runnable box but will not clear the credit-0 line. That line blocks only the
  PAY-SITE family (their gates need storage >= price — take the per-boundary storage poke above the
  price); rebuild/upkeep censuses run green at credit 0 (M100/M102 did). Check the state a printed FIX
  demands is actually reachable before looping it.
- **A clean reload does NOT carry records created live in a previous session** — a prior run's new
  unit/type records are live state that no save holds, so yesterday's census is fiction after a
  reload. Re-census the watched slots from `/proc/pid/mem` in the same invocation that arms the
  harness, and make the harness assert armed == len(designed watch list) rather than a fixed floor:
  arming fewer watchpoints than the design list silently drops half the slots from the window. **Check the save can HOST the experiment before you reload it**: `m54b_clean.SAV` loads at 2150 r50 — University Base only, `credit` 0, and the chooser candidate array is ERA-DEPENDENT: after `m54g_prep` + one turn the INSERT lands even at minerals 0 / credit 0, but the FIRST enqueue attempt right after a turn-end can transiently print `item 2 not in candidate array []` — retry it once before blaming the save; reloading to clear a stray modal costs the later state (2163 r63, candidates `[192,195,194,193,2,0,1,196]`) AND the experiment. Clear the modal itself; gate any reload on `accept_ready.py` READY plus a non-empty candidate array.
The
  census→live-enumeration method (filter the store census by call-graph reachability, condition each
  breakpoint on the address the store's own encoding computes, scale included, accept by replaying the stores against the sampler) is
  `references/static-store-census.md` §9; §1–§3 carry the traps that make the STATIC half of it complete —
**Read §9 before hand-writing a watcher script** — condition arithmetic, log format and scorer gates are
solved there (uppercase-`PTR` greps, pointer-form stores, operand width).
Depth: `references/wine-operations.md`, `references/wine-headless-harness.md`
(turn automation, OCR/dialog state machine), `references/wine-runnability.md` (what runs at all).

## Still open (leads)
`references/open-leads.md`; `NEXT_PROMPT.md` wins if they disagree.
**Band-flag gate — CLOSED, do not re-open** (bit 0x40 of the per-faction flag word is tested but has no setter and no
save carries it): `scripts/m118_flag_never_set.py` re-proves it offline.


