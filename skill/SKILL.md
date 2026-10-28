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
reading, and the live write-enumeration acceptance in §9),
`wine-headless-harness.md` (turn automation), `open-leads.md` (unanswered questions with cites),
`screen-read.md` (why ONE OCR pass is not a screen read: the HUD's two rows, their measured read
rates, what N looks mean), `git-workflow.md`, `wine-runnability.md`, `data-formats.md`,
`ghidra-batch-export.md`, `terraforming-order-path.md`. `grep -n '^## \|^- \*\*' SKILL.md` then `sed -n 'A,Bp'` the section you
need. When adding depth, append to the right reference; only new cross-cutting pitfalls belong here.
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
it onto the new branch — never commit a cursor write to `main` just to get the tree clean.
**Verify the named milestone is not already merged before starting it** — a kickoff prompt (re-pasted or
cron-supplied) can lag the repo. `git log --oneline | grep -i <ID>` plus `grep -n '^## <ID>' NAMED.md`
answers in one call; if both hit, the prompt's pick is stale, so run the milestone
`SESSION_CURSOR.md`/`NEXT_PROMPT.md` names and state the swap in the report. Re-running merged work
spends the tool-call budget and re-derives a settled answer.
Cycle: `python3 scripts/milestone.py start <ID>` → work → `gate.py --base main`
(must be GREEN) → `submit --title …` (commit + push + PR) → `gh pr checks <n>` → `merge <n>`.
**A GREEN gate is not permission to merge.** The gate audits docs, evidence and the harness; it says
nothing about whether the milestone's acceptance passed. If the acceptance printed FAIL, keep the
checkpoint commits on the branch, submit nothing (or leave the PR unmerged), and report the FAIL with
its numbers — a branch carrying a documented FAIL is the honest end state, and weakening a threshold
to turn it green is the one thing that is never allowed.
Each milestone ends with a `## Session N` section in `SESSION_NOTES.md` and a rewritten
`NEXT_PROMPT.md` (<=15,500 bytes). `scratch/` is gitignored: scratch probes and one-off tools are
NOT repo products — a checkpoint commit after scratch-only work correctly commits nothing; the
tracked products are `scripts/`, `evidence/`, and the docs. After editing the LIVE skill, run `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`
— the gate compares only `SKILL.md`, so an edited reference, template or script drifts silently
otherwise. Editing this skill therefore leaves the repo copy stale until the next sync; do that
sync in the same session, before the closing commit.

## Session discipline (this project is context-heavy)

Paul wants SMAC RE broken into **small pieces**: complete ONE milestone, write it to a
file, append one dated line to `~/reverse/smac/SESSION_NOTES.md`, then STOP — ending
after a single milestone is a success, not a shortfall.

Exception: when he says **"keep going until you finish <chapter>"**, that overrides the
stop-after-one rule. Work through that chapter's milestones, writing the doc + evidence
after each, and report once at the end — including what is still open. Do not relabel a
partial result as done to make the chapter look finished (see `MILESTONES.md` F2).

### The context ceiling is part of the task, not an accident

Hermes' compressor resolves to the MAIN model (`auxiliary.compression: provider: auto`), and on
2026-10-27 that model could not summarize itself: four attempts, `finish_reason=length`,
`failure_class=summary_truncated_failure`, 132 s each, `commit_status=aborted`; the gateway also
drops hygiene compression after a 10 s turn-hold. Measured outcome: the agent reached
259,232/262,144 tokens and the CLOSING turn was cut mid-sentence twice — the milestone was done
and accepted, the paperwork never landed. Rules that follow:

- Budget by TOOL CALLS, not by feel: brief+accept_ready <= 6, milestone 6-30, **commit a
  checkpoint at ~25**, stop measuring at 30-40, close at 40-50.
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
`templates/session-kickoff.md` — copy it and substitute the milestone id and session number.

When Paul asks for the loop to be **scheduled** rather than pasted (a cron that keeps advancing every
hour), the job's prompt must NOT bake the milestone id: it reads the id from `NEXT_PROMPT.md`
(`## THE PICK`, else the first open `## STILL OPEN` item), stops rather than inventing a milestone when
nothing is open, and refuses to start a competing measurement while `SESSION_CURSOR.md` says a run is in
flight — the box is one Wine process, so a second gdb attach or mineral poke confounds the first run.
Keep every tool result small:
grep the **`ghidra_out/` corpus** or the saved `*.pseudocode.txt` / `*.json` dumps in
`~/reverse/smac/` instead of re-dumping; page Ghidra facets in small slices; reuse saved
screenshots and take a new one only after a real state change.

### Close before you hand off (the handoff is what overflows)

A one-milestone turn routinely runs 130-150 tool calls and 250 k+ prompt tokens against a 262,144-token
window, so the last ~15 k tokens are the entire margin. Order the ending, every time:

1. gate GREEN
2. `SESSION_NOTES.md` entry (patch, never a full rewrite)
3. **checkpoint commit** (`git commit -am '<ID>: checkpoint'` — this repo already uses those)
4. `NEXT_PROMPT.md` rewrite, then `wc -c NEXT_PROMPT.md`
5. submit/PR, then stop

Never leave the commit until after the handoff docs. The prompt rewrite is the single largest generation
of a turn and its tool-call arguments re-enter the prompt, so an overflow there strands everything on a
dirty branch — `git log main..HEAD` empty, `milestone.py` never closed, the whole milestone uncommitted.

- The `NEXT_PROMPT.md` 15,500-byte cap is a hard budget, not advice (the gate fails at 16,000 chars,
  `scripts/evidence.py`): draft the rewrite to land near **15.2 k on the first write** — trimming a
  finished 15.6 k file costs three follow-up patch calls for 60 characters, more than the overage.
  Patching an over-budget file down costs roughly one call per 100 bytes of net reduction, so when a
  section edit ADDS text, pair it in the same call with a compensating deletion elsewhere (retire the
  oldest ledger paragraph or a stale box-state bullet) instead of chasing the overage afterwards.
  **Trust only `python3 scripts/evidence.py budget` for that number** — it counts CHARS, and chars do
  not equal `wc -c` / `os.path.getsize` (a file measuring 15,988 bytes scored 16,052 chars and failed
  the gate), so trim until the tool's own line says `warn`, then stop. When trimming, DELETE whole
  sentences or bullets: rewording trades characters for characters and the check stays red. Well
  over it, move footing into `FOOTING.md` at the repo root (or a `references/`
  file) and leave a pointer. Session 75 did exactly this with the M48d->M53s rebuild model. An oversized prompt also spends the next session's opening
  context before any work starts, which is how sessions ratchet toward the wall.
- For docs >10 KB `patch` anchored sections instead of `read_file`-then-`write_file`: the write guard
  forces a full read and the rewrite emits the whole file back into context, twice the cost at the exact
  moment the window is tightest. In a HARD-WRAPPED doc, exact multi-line strings miss on the line breaks:
  build the search pattern by joining the tokens with `\s+` in a regex and apply several edits inside one
  `execute_code` cell that prints only the size delta — the file never enters context and a wrapped
  section lands on the first try.
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
the shell, silently deleting those fragments — grep the written region after any shell-embedded write. An
`execute_code` cell is hard-killed on its own timeout and does NOT stop a turn driver it spawned: `ps -p
<pid>` for the orphan and kill that exact pid — this checkout's `smac_play.py` has **no `--mode stop`**
flag (an earlier note here claimed otherwise), and never `pkill -f`/`pgrep|kill` by name: your own argv
matches.

### Verify the OUTCOME, not the mechanism

An acceptance script that counts the loop's own work (year deltas, verified order bytes, landed
walks, STUCK) will happily pass a run that lost the game: a 40-turn run printed `PASS` with
`40/40`, `{1: 40}`, `stuck 0` and 5 landed walks while the faction owned **zero** bases at the end
and its 8 surviving records sat stacked on one limbo tile with `turn_flags` stuck at `0x100002`.
The defeat was invisible because the trace snapshot carried only the map-wide base count, never
"how many bases do WE own".

- After every unattended run, re-read the position and assert the outcome out loud: bases of our
  faction, where our records stand, `turn_flags`. The plumbing exists — `scripts/smac_state.py
  --json` prints `bases_ours`/`units_ours`, `smac_play.py` carries both in every per-turn
  `state_before`/`state_after`, and `m54a_check_run.py --min-our-bases N` fails a run that loses
  the position. **Use the floor on every run that is supposed to keep what it has**; it fails
  closed, so a trace predating the fields FAILs instead of passing vacuously.
- **A record that vanishes after a position poke was probably parked on an impassable tile, not killed.**
  Read the tile's flag byte (record `+3` for even x, `+7` for odd x; bit `0x40` = impassable) before
  writing "died in the war" — the game deletes records standing on impassable tiles within seconds, and
  the deletion looks exactly like a combat loss in the census. Use the multiset-diff poller
  (`references/wine-operations.md`) to catch the disappearance tick.
- **Never write a handoff sentence about where the game ended up from the plan.** "The garrison is
  back on University Base" was inferred from the pre-run census plus the walk destinations, never
  read back, and was false. Read it, then quote the numbers.
- **Change one variable per prep poke.** Emptying a destination tile and moving the walker off a
  half-tile offset in one poke produced a confident, wrong root cause (that tile's occupancy)
  which the run's own trace later refuted. Split the poke, or label the cause unattributed.
- **Record index is not identity, and the unit array GROWS mid-run** — a base building a unit
  shifts every index after it, so an index carried across a turn (or read a fraction of a second
  after the order lands) can name a different unit's record. It also COMPACTS mid-turn: a queued
  MOVE can execute inside our phase (`turn_flags & 2` set while `cur_player` is ours, the year
  flipping every ~4.6 s), and every flip re-shuffles the slots — so even a byte read taken seconds
  after the keypress can name a different record. During any burst, re-read WHO wears the byte
  (scan all records for the transition against the pre-press snapshot), not who sits at the slot. Snapshot ALL our records (type, x, y,
  `+17`, legs) before the keypress and diff after; take the field from the record that actually
  changed, and report how many changed — two changed means the result is confounded. **Across a round
  boundary even the BYTES are not identity**: upkeep/compaction decrements the u16 index references at
  `+28/+48/+50` inside records that did nothing, so diff record sets on (x, y, type, owner, order) and
  report byte rewrites as a feature (`references/solo-round-boundary.md`).** The 304-byte BASE array
    reorders and compacts too — pair a base across snapshots by NAME (or `(x,y)`), never by remembered
    index, and treat a `--ui-queued <index>`-style argument as a start index only.
- **Attributing a field to one keypress: the through-the-click watcher on the subject's own slot
  is the only proof.** A read taken after the click proves the field changed somewhere, not on
  which record — pair the byte and the field from the SAME sample. Use the post-click snapshot of
  the whole array only to look for RIVALS (the pump may already have consumed the byte, and a
  mid-run unit build shifts every index after it). A destination counts as this order's only when
  `+17` went 0 -> the byte on the watched slot, the leg arrays CHANGED against that record's own
  pre-press value (stale legs survive the pump and name somebody else's trip), and no rival — a
  same-type/same-tile look-alike freshly ordered, a record carrying the watched signature under a
  shifted index, or a subject that left its tile while its old index wears the signature — exists.
  Any of those: report the walk UNATTRIBUTED / CONFOUNDED with the rival records quoted; a guessed
  destination poisons the next session's footing.
- **A position claim needs a DELTA, not a match.** "A record of this type sits on the destination
  tile" is true before the walk starts when look-alike units are parked there. Require the count
  of that type to rise at the destination and fall at the origin against a baseline captured at
  order time, and re-read an unfinished walk on later turns (an ordered move can cost more
  movement than one turn gives it). When the confound is your own decoys, park them FIRST: poke
  `+17` to a standing order (SENTRY) and read it back, so exactly one subject can move.
- **Click a pane button at its measured centre, never at the merged midpoint of the bars in a
  y-range.** A chooser that grows rows drags its button band down and its row bars merge into the
  same y-window; the midpoint of that span is a Sort button, and clicking it re-sorts the pane
  instead of answering it while the loop waits for the order to land. Derive the button band
  (equal-width groups on an even pitch), index it (OK fourth, CANCEL last), and fall back to the
  midpoint only when no button band was measured.
- **Make a test fixture of the 52-byte record match the FORMAT, not just the fields you assert
  on** — pre-fill the leg arrays with the `-1` terminators. A zero-filled fixture decodes as extra
  real legs `(0,0)`, which silently inverts legs-changed comparisons and makes a correct rule look
  broken (or a broken rule look correct).
- **`f.seek(off) or f.read(1)[0]` returns the OFFSET, not the byte.** `seek()` returns the new
  position, so `or` short-circuits for every non-zero offset and a `/proc/<pid>/mem` reader written
  that way silently hands back the address. It cost a run its discriminating check: the "plan byte"
  printed as `10005938` (an address) and the shape gate compared addresses while the milestone's real
  assertion still passed. Read in two statements, and log the value next to the offset it came from so
  a reader bug cannot impersonate a measurement.
- **Grep every consumer call site before changing a helper's sample/return shape** — probe scripts
  and hand-rolled fixtures keep the old shape, and tuple-index bugs surface only in the shard you
  did not re-run (a `(raw, ms, byte)` watcher whose readers still index `s[1]` silently never
  matches). In a comprehension, a variable used in the key or filter must be introduced by an
  earlier `for` clause.
- **Write the attribution/verification rule's CASE LIST before coding it against a unit test**:
  one line per case — before-state, after-state, expected verdict (claimed / confounded /
  unattributed). Semantics designed by repeatedly failing a test rewrite function and test
  together for dozens of tool calls; the checkpoint commit fires at the first green test, not at
  the end of that churn.
- **Pick the box state that makes the rival hypotheses DISAGREE before you run — a PASS on a state
  where they predict the same result proves nothing.** Write every rival rule down first, then choose
  the state that separates them (an empty queue region makes "writes slot `4*pending`" and "inserts by
  a sort key" predict identical slots; a region holding unequal key values does not; two sort keys that
  happen to rank the same ids identically — cost `+41` vs plan `+42` — need an item whose two orders
  DISAGREE), and make the scorer print
  FAIL when more than one rule fits rather than picking one. This is the case-list discipline applied
  to the STATE: a green run on an undiscriminating state is refuted by the next run, and the refutation
  looks like a contradiction in your own ledger.
- **A gate certificate is about the RULES, not about the game.** A pre-click gate can certify "only
  key K predicts this landing sequence" and the run can still come back with a landing that NOTHING
  in your model explains, because the mechanism you modelled was not running at all: five clicks
  wrote consecutive slots (one append per click) where the gate had certified a sort-key sequence,
  and "append in click order" is predicted by dozens of candidate keys at once (every byte constant
  over the involved ids), so the run names no key. Read that FAIL as "no claim", never as "the key
  is wrong", and never let it overwrite a live read-back from another state — record the two states
  side by side and write CONFOUNDED. The next move is not another state or another click order: it
  is a breakpoint at the write site (entry of the enqueue, the index it computes, the value it
  stores) plus a hardware watch on the first element, which answers "sorted scan or append" and
  "where the odd value came from" in one run.
- **Read the structure PLUS ONE SLOT PAST ITS END, and treat the read model as fallible.** A write
  location is only interpretable if you can see where the array stops: SMAC's queue is 10 dwords
  (`base+0x50..+0x74`) and the dword after it is a different field that never moves, so an 8-slot
  read window hid the boundary and a correct insert scored as "no rule explains this" twice. When
  measured bytes fit NO model you wrote, suspect the MODEL (shift bounded by the window? by the
  region? by the array's capacity?), not the game. A read model is not a hypothesis about the game:
  fix it, say which shapes each version predicted, and re-accept on a shape you have not used yet. The same
  applies to a record COUNT carried in from an earlier census: before arming anything, read the whole
  `stride × count` region straight from `/proc/<pid>/mem` (no gdb — the cheapest measurement available)
  and group it by the band the code's own index arithmetic computes. A "256-record" type table was really
  8 × 64, and every index above the assumed bound was an ordinary record of another faction.
- **Make the value you are locating distinguishable from what the structure already holds.** A
  write-location question (which slot did the game write?) is unanswerable when the written value
  equals a value already sitting in the array — enqueue or poke an id the structure does not hold, and
  never trust the empty marker: unused slots can read 0 while the documented empty code is a different
  number, and 0 may itself be a legal item id. Two rules fitting a duplicate-value shape is the signal
  that the experiment, not the rule, needs a different value.
- **Read a widget's backing array only after the widget is open, and confirm the click landed.** A
  paint rebuilds and re-sorts list data (the build chooser's candidate array changed order between a
  pre-open read and the open chooser), so a cell→item map taken before the open is stale; after the
  click read the widget's own selection field, then the array entry at that index, and credit the
  stored value only against the read taken at click time. **Cells past the first row can silently
  not take**: a click can leave the selection field on the PREVIOUS value and the commit button then
  does nothing, so re-assert `selection == intended cell` AND `entry_at_cell == intended item` before
  every commit click. Look for the cause in the WIDGET STATE before blaming the pixel pitch — the same
  cell 4 / cell 6 coordinates that failed three times registered first try once the pane open was
  FORCED: a stale-open check (`if pane_base_idx != idx: open`) passes while the pane is CLOSED whenever
  the index happens to equal 0, so always press the open key, click the row, and confirm the chooser
  populated (candidate count > 0). A NEGATIVE code stored instead of the item id is the TYPE's, not the
  click's: one click whose selection verified stored -6 for an all-zero record and another -3, both
  with `selection == cell` — read a negative as "this id has no real record" and keep such ids out of
  any shape.
- **Before a diff counts as evidence that one of two similar arrays moved, check the addresses are
  disjoint.** Two byte arrays a few hundred bytes apart indexed with the same
  `base + stride*owner + id` formula OVERLAP — at a 512 B separation, `low[512+id]` IS `high[id]` — so
  sampling one index in each can "confirm" the same byte twice. Diff whole rows and subtract addresses.
- A `turn_flags` bit that survives a year flip means the box is wedged mid-round, not that the
  click failed — hand that over explicitly and start the next session from a known-good save.

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

Measured 2026-10-25: 29.3 MB in 858 files (58 images = 13.9 MB of it) against the 30 MB FAIL — and
`prune --dry-run` proposes NOTHING, because the rule only drops *images older than 7 days* and the
whole tree was days old. So the margin is real, not theoretical: a 40-turn trace is ~55 KB, but one
screenshot is 400 KB and `check_classes.py` writes a `_3x.png` sibling next to every frame it OCRs
(delete those immediately). Run `budget` BEFORE adding new frames, and expect to prune in bulk once
the footage ages out. When `prune --dry-run` proposes nothing (it only drops uncited images older than
7 days, and a young tree offers no victims), free the room instead by gzipping a large *text* file that
no markdown cites — `grep -rn <basename> --include=*.md .` first, because a cited path must stay
readable at its recorded path; an uncompressed disassembly dump is worth ~8x its gzipped size.
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
**Unit-record type field — SETTLED: the u16 at `+10`. `+4` is the flags dword.** An earlier
version of this paragraph claimed type@`+4` and `+10`=flags; that was wrong, and `FOOTING.md`
("type byte@4") and `SAVE_FORMAT.md` ("`+10` is a flag word") have been corrected to match.
Proof is the accessor, not a screen correlation: the class table is indexed with
`*(short *)((int)&DAT_00933282 + rec_off) * 0x34` (`shard_012.c:2150`; same shape at `:2117`,
`:2148`, `shard_001.c:4153`, `:4312`, `:9466`) and `DAT_00933282` is `UNIT_ARR + 0x0A`. The
screen agrees — a selected record reads "Scout Patrol" on the panel with `+10 = 2`. `+10`
values of 128/256/320 mark EMPTY STALE SLOTS: filter `type < 24` (and x/y in range) before
counting a record as a unit. Movement/order fields (`+0/+2`, `+17`, `+20..+35`, `+40`) were
never in doubt — pokes the game obeyed validated them.

Two rules that generalise from how this one went wrong:
- **Settle a field's identity from the binary accessor, not from which candidate looks plausible
  on a dump.** Grep the table base (`grep -n '98adb2\|933282' ghidra_out/*.c`), then read the
  cast: `*(short *)((int)&DAT_x + off)` gives the WIDTH and the OFFSET at once, and the code that
  consumes it names the semantics. A correlation over live records only ranks candidates.
- **Never compare candidate offsets on a state you already know is degraded.** The "`+4` wins
  117/119" measurement was taken on records sitting in limbo after the faction lost its bases,
  where the flags byte reads 0 on most records. Re-run layout questions on a freshly loaded,
  healthy save, and do not let a format doc outvote code that demonstrably works.

Fast handles: full `.text` disassembly `evidence/m53j_text.txt.gz` (GZIP — `zgrep -n '  4e78e9:'` then
`gunzip -c … | sed -n 'A,Bp'`); owner of a VA `awk -v A=0x… -F, 'NR>1 && $1<=A {n=$2;p=$1} END{print
p,n}' ghidra_out/index.csv` (commas, no spaces); pseudocode `scripts/fn.py 0xADDR`.

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

## Map + save container formats (verified 2026-10-20 — see MAP_FORMAT.md / SAVE_FORMAT.md)

`.MP` map — `15 + 2724 + W*H*22 + trailer == file size`, checked on both shipped maps:
```
0        15 B   b"TERRANMAP\0" 0x1A u32 version(=5)
15     2724 B   header struct: u32 width, u32 height, ... (word 5 = land cells = W*H/2)
2739    W*H*22  raw cell records, row-major (no XOR)
+      var      trailer, starts b"????????" (128 B @80x80, 338 B @128x128)
```
planet.MP 80x80 143,667 B; planetx.MP 128x128 363,525 B. Parser `scripts/decode_map.py`.

`.SAV` save — `b"TERRAN\0" 0x1A u32 version(=86)`, 796 B header, mission year u16 at **+0x54**;
then sections read in a fixed order (see SAVE_FORMAT.md). Section *sizes* come from header counts
and shrink as the game progresses, so arbitrary saves can't be split yet.

**`FUN_00597a70` is the save/scenario block loader, not the map loader** — an earlier note here
claimed otherwise. The map grid is read raw by `FUN_00582260`.

`.SAV` section sizes (from the `push` sites in `FUN_00596850`): 796, 67,040, 11,488, 16,000, 3,584,
26,624, 4,096, 256, 152, 10,144 are immediates; three are computed — one raw count (`DAT_00927538`),
one **52 B/record** (`edx` records), one **304 B/record** (`DAT_00985af4` records). Two are skipped
outright under version/count conditions, so the section list is conditional.
`.SAV` is fully splittable from the file alone — `scripts/decode_save.py --sections` sums to the byte.
Key facts: u32 **own player at file offset 808**; a **u32 count prefix immediately before** one
variable section; the other two variable sections are `n × 52 B` and `m × 304 B` records, split by
solving `52n + 304m = region` and choosing on zeros-fraction (304 B records ~80% zero, 52 B ~40%).
Caller-scoped gdb condition that makes small reads loggable without flooding:
`break *0x64cc00 if *(void**)$esp >= 0x596850 && *(void**)$esp <= 0x597a6b`.
Anchors that pin a save's layout byte-exact (verified on two saves of different ages): map dims
`50 00 00 00 50 00 00 00` at **79,372** and `????????` at **222,896**; gap 143,524 = 2,724 + 140,800.
`scripts/decode_save.py --anchors` checks it.
**Pitfall:** never validate an offset by "fraction of identical bytes" — these files are mostly
zeros, so the match rate is flat across wrong offsets. Use a unique content signature instead.

### Technique that cracked both: runtime read trace, not static reading
Break on the read wrapper and log the **caller** and size:
```
break *0x64cc00 if *(int*)($esp+8) >= 64      # 0x64c9a0 is the sibling wrapper
commands
silent
printf "R3 caller=%#x size=%d count=%d file=%#x\n", *(void**)$esp, *(int*)($esp+8), *(int*)($esp+12), *(void**)($esp+16)
continue
end
```
- Unconditional breakpoints here fire **34,000+ times** (the game reads 1-2 bytes constantly) and
  slow it to a crawl; the `>= 64` condition is what makes the run usable.
- The caller address maps each read to its function, so the section order falls out in one run.
- Then close the arithmetic against the file size: if `sum(reads) + known_prefix == filesize`, the
  layout is complete. That is the check that distinguishes a real format from a guess.

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
  the negative test. Window is 10485761 (800x600). `xwd` needs **`-display :99`** (`DISPLAY=:0` captures blank).
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
  … > /tmp/<tag>.log 2>&1`), never `nohup … &` in a foreground call: the wrapper is refused there, and
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
  base address. Do **not** single-step for the after value — `si` inside a breakpoint commands list makes
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
  while the turn driver keeps exiting 0, so an aborted window reads as a clean zero-event run. gdb's
  printf reads an inferior pointer as a HOST address, so `%.20s` fed `*(char *)(rec+0)` errors
  ("Cannot access memory"); bp printfs emit NUMBERS derived from registers only (raw reg, reg/stride,
  reg%stride, `*(short *)(...)` values), never inferior strings — use `x/s` outside a commands block
  when a name is genuinely wanted. Bake addresses as literals, `stdbuf -o0`, drain gdb's pipe,
  and drive + snapshot in ONE backgrounded job (`scripts/m53n_drive.py` is the template). A **zero-event log is an instrument verdict until proven
otherwise**: arm one control breakpoint whose hit is guaranteed in the window and require its rows, and
read back from memory BEFORE attaching that the event you watch for can even happen (queue head is the
armed id, `pending >= 1`, storage above the largest value the gate can demand) — a window where the event
never occurred is an unusable window, not a negative result (`references/static-store-census.md` §9.8–9).
Two more pre-arm checks, both cheap and both fatal when skipped:
- **The readiness oracle can print a FIX that is unreachable on the current save.** `credit` is
  `base+0xd0`, a save-LOADED field whose only writers are the player-record init stores — turns never
  raise it on a base whose income the save left at 0, so looping the printed reload chain cannot clear
  that reason. Before re-running a printed FIX, check the state it demands is reachable; when it is
  not, take the per-boundary storage poke above the gate's price (readiness then passes on minerals
  alone) and report the oracle's premise as false instead of reloading a second time.
- **A clean reload does NOT carry records created live in a previous session** — a prior run's new
  unit/type records are live state that no save holds, so yesterday's census is fiction after a
  reload. Re-census the watched slots from `/proc/pid/mem` in the same invocation that arms the
  harness, and make the harness assert armed == len(designed watch list) rather than a fixed floor:
  arming fewer watchpoints than the design list silently drops half the slots from the window.
The
  census→live-enumeration method (filter the store census by call-graph reachability, condition each
  breakpoint on the address the store's own encoding computes, scale included, accept by replaying the stores against the sampler) is
  `references/static-store-census.md` §9; §1–§3 carry the traps that make the STATIC half of it complete —
objdump prints `PTR` UPPERCASE (a lowercase grep reports zero stores), a store through a record pointer
never prints the table's base address (enumerate the absolute form AND the `+disp]` form before naming a
setter set), and the operand width decides whether a bit filter is admissible at all. **Read §9 before
hand-writing a new watcher script** — its condition arithmetic, log format and scorer gates are already
solved, and a from-scratch instrument re-derives them wrong.
Depth: `references/wine-operations.md` (moved verbatim from here), `references/wine-headless-harness.md`
(turn automation, OCR/dialog state machine), `references/wine-runnability.md` (what runs at all).

## Still open (leads) — `references/open-leads.md`
The per-milestone lead list lives in `references/open-leads.md`. `NEXT_PROMPT.md` holds the CURRENT pick
and the authoritative open items; if the two disagree, `NEXT_PROMPT.md` wins.
