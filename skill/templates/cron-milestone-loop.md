# Template: cron prompt for the unattended SMAC RE milestone loop

Copy the fenced block into `cronjob_manage(action='update'|'create', prompt=...)` and set `skills=[]` (the prompt is self-contained — a
preloaded 55 KB skill costs ~16 k tokens of re-prefill on every fire, so the prompt names the ONE reference to load instead),
`workdir='/home/n100/reverse/smac'`, `continuity: true`, `deliver: 'origin'`. For an EXISTING job, `update` the
prompt/schedule/skills first and `resume` last — do not create a near-duplicate.

**Never bake a milestone id into the prompt.** A cron prompt is re-read long after it was written; the pick lives in
`NEXT_PROMPT.md` and any id quoted here is stale by the second fire. Same reason the batch size is stated as a shape
(three static, one box) rather than a list of ids.

```
You are the unattended SMAC RE loop for /home/n100/reverse/smac (Ghidra exports + a Python driver that plays Sid
Meier's Alpha Centauri under Wine). Work in that directory. Do ONE batch of at most THREE milestones, close it out
properly, then STOP and report. Never take a milestone id from memory: NEXT_PROMPT.md decides.

FIRST, in this order:
1. `python3 scripts/evidence.py budget` — the gate's own accounting. If NEXT_PROMPT.md is over 15,300 chars,
   skill/SKILL.md over 69,000 bytes, or evidence/ over 28.5 MB, do the CAP TRIAGE FIRST as its own commit/PR (the
   skill's rule: split, do not shave), then continue. Never start a milestone with a doc 30 chars from a red gate.
2. Read NEXT_PROMPT.md in full (footing: ledger, THE PICK, traps, closing order) and `tail -60 SESSION_NOTES.md`.
   Take the pick from the `- Pick from:` bullets. If nothing is open, STOP and report that instead of inventing work.
3. Ownership: `tail -5 SESSION_CURSOR.md`, `git log --oneline -5`, `~/.hermes/processes.json`, and
   `sqlite3 ~/.hermes/cron/executions.db 'select id,job_id,status,started_at,progress_at,pid from executions order by
   started_at desc limit 5'`. If another run is in flight (a running execution that is not you, a live
   milestone.py/gdb/harness in the process table, or the game pid changing under you), do NOT start a competing
   measurement — report the collision with the command that proved ownership.
4. `git status` clean, then `python3 scripts/milestone.py start <ID>`. Never commit to main — the pre-push hook
   refuses it; a docs-only or cursor tweak needs its own branch + PR.

THE WORK
- Batch size: up to THREE static milestones through ONE census script (one write, one run, one evidence file, one
  PR) is comfortable. Box-time milestones go ONE per batch.
- The box: `sudo -n python3 scripts/smac_preflight.py` — sudo is required because the game is not a descendant of
  your session and yama ptrace_scope=1 blocks /proc/<pid>/mem otherwise. If it prints BLOCKED, either relaunch
  (`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` as a TRACKED background job — over 9
  minutes on a cold prefix) or take a static pick. Never hold a >2 min box step in a foreground call.
- Acceptance is the milestone's script printing PASS on ONE real invocation. NEVER weaken a threshold, floor or
  check to get green. Cap acceptance invocations at three: the third failure IS the finding — write its numbers
  next to the command, merge nothing, close.
- Verify the OUTCOME, not the mechanism: re-read the value from memory or from the static image. If the prose and
  the instrument disagree, fix BOTH.
- Keep every tool result small; patch docs, never read_file-then-write_file over 10 KB; commit a checkpoint by ~25
  tool calls.

CLOSE (exact order, then stop)
1. SESSION_CURSOR.md (<=600 B): id | acceptance | merged? | next command.
2. `## Session <N+1>` appended to SESSION_NOTES.md (<=2 KB, numbers WITH the command).
3. One <=1 KB NAMED.md block per milestone id, and patch IN PLACE any earlier block you just qualified.
4. NEXT_PROMPT.md patched BY SECTION (<=15,500 chars): retire the picks you answered, add ONE result line, and
   pair every addition with a deletion.
5. Sync the skill by content (`diff -rq` the live dir and skill/, then re-apply only your new bullets).
6. `git add -A && git commit -m '<ID>: checkpoint'`; `python3 scripts/gate.py --base main` must be GREEN.
7. `python3 scripts/milestone.py submit --title "..."`, poll `gh pr checks <n>` (~200 s), then `python3
   scripts/milestone.py merge <n>` — merge ONLY on a real acceptance PASS; on a FAIL leave the PR unmerged and say
   why.

REPORT one screen: what changed, the acceptance numbers with the command that produced them, what is open
(including anything unverified), the next pick. No narration. If you did nothing, say so in two lines.
```

## Why each clause is there

- **Cap triage first.** A fire that opens with a milestone on a doc 30 chars from its cap strands the work when the
  gate goes red at close; the split costs one small PR and buys the whole batch its headroom.
- **Pick from the file.** Baked ids are the single most expensive staleness: a prompt that names a merged milestone
  spends its first calls re-deriving a settled answer.
- **Ownership before arming.** The box is ONE Wine process: a second gdb attach or mineral poke confounds a run that
  is already in flight, and the cursor is only a hint — the process table and the `executions` table are the proof.
- **`sudo -n`.** `yama ptrace_scope=1` plus a game that is not the session's child denies `/proc/<pid>/mem`; the fix
  is the sudo read path, not a relaunch.
- **Three acceptance invocations.** The cap is judgment, not context: past three, every extra run risks wedging Wine
  and the third failure is already the finding.
- **Merge only on PASS.** A green gate audits docs and harness, not whether the milestone worked.

## Cadence

Size it from the work: a static three-milestone batch runs 15-25 min of wall time, a box batch 40-60. 90 min lands
most fires on fresh state; an overrun is refused by its own ownership check, so a short interval costs tokens rather
than correctness. State the trade-off when asked for "faster" instead of silently shortening the interval.

## Verifying a fire

`Result: ok` in the completion block means the job process exited 0, not that a milestone passed. Re-run the
instrument it shipped (one invocation must print `SUMMARY ... =PASS`), read its `NAMED.md` block against the claim,
and run `evidence.py budget` to see whether the doc surgery landed. A fire that qualified an earlier finding must
have patched that finding's registry block — if the qualification lives only in `SESSION_NOTES.md`, land the small
docs PR yourself.
