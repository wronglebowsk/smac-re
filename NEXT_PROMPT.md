# NEXT_PROMPT.md - footing (B24 MERGED 9/9+8/8; M316 #305; M315 #301; old header/CLOSED-enumeration/traps VERBATIM at `docs/nextprompt-archive-m299-b20.md` + `docs/pick-archive.md`. STATE: B1-B24 + M54A-M319 done; track ANALYSE (since B24) - pick (vi) next; the next BUILD is B25, whose spine text is NOT authored yet; #180/#105 pre-existing.)
Overflow: pick-archive + nextprompt-archive-m299-b20 (VERBATIM blocks - read only the picked section); NAMED.md
(§CHAIN-BUILDS/§CHAIN-PICKS - grep only); skill instrument-laws.md.

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor; its summaries die on the output cap. **Whatever is not
finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 15 `git add -A && git commit`** (s187: call 25 = 167k,
  zero commits) — every later step must leave a committed file.
- JSON only: no XML in tool args. Writes over ~4 KB drift -> rejected as missing `path`: retry once, re-emit as pure
  JSON (never fragment). Branch + skeleton commit BEFORE probing (s189: 108k vs 167k).
- **30-40** STOP MEASURING: an ungreen acceptance IS the finding — write blocker + number, merge nothing.
- **40-50** closing order, TERSE (see CLOSING ORDER; the caps there bind).

Survivability: cursor <=600 B before any >2-min step; never `rm`/`git checkout --`; doc writes patch/append.
**Batch: 5 static milestones per census script, 1 box per batch — doc headroom is the cap.** Caps (BYTES, what `budget` prints): NEXT_PROMPT warn 12,000/fail 16,000 — CLOSE at <= 12,000; SKILL.md
warn 55,000 (keep near 44 k, always-loaded under the 60 k ritual); SESSION_NOTES warn 110 k. Split rule: settled text
VERBATIM to a reference / `NAMED.md` section; RULES + pointer stay; re-run `budget`.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>` from merged history. BUILD ⇒ build
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a censusim; no
box/`/proc`/gdb time; box-debt pre-step N/A; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B24 MERGED**
(per-rung cmds: `NAMED.md` §CHAIN-BUILDS). Next build **B25, queued and NOT YET AUTHORED**: `BUILD_SPINE.md` ends at
B24, so B25's rung text must be written BEFORE probing (one milestone = spine section + instrument).
B24 MERGED as #307 (main af38858; `NAMED ## B24` governs): instrument 9/9 (`python3 -u -m sim.selftest --b24`) + harness
**9/9 scored + 1 declared NO-OP** (MU9 labels-only = decoration). Its spine text (the compaction RETRACT, the
LEDGER-POSITION addressing law, the s287 harness laws, the two retired degenerate rivals) is VERBATIM at
`docs/pick-archive.md:963` §trim-s292 (a) — that copy is the ONLY place the sentence "declared gate-sets are
MEASURED, not authored" survives; the sibling laws are independently in the skill at `skill/SKILL.md:319-320`,
`skill/references/instrument-laws.md:1031` (§four outcomes, s287/B24), `skill/references/verify-outcome.md:237`.
`pos=False` in `composedturn.fold` is NOT tile-addressing. M316 (#305) + M315 (#301) summaries: same archive
section; `NAMED ## M316` / `## M315` govern.

## THE LEDGER

Merged M54A-M309 + B0-B21 (through s271) + hygiene #254-#280. UNMERGED M83/M84, M86, M101, M103, M109, and **M241 (#180, 2/5, PR open - documented-FAIL re-confirmed, gates stand)**.
Full list + reasons: `docs/pick-archive.md` §trim-s202; per-id semantics `NAMED.md` + `docs/named-archive-*.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** = readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it before you arm** (screen fixes in TRAPS).
2. Writer/flag chain - silent bps or hw watchpoints + a live-memory prediction + a read-back: the
   m94/m97/m100/m102/m103 + m92/m95/m98/m117 family (full text: pick-archive §s244-trim; writer
   named by containment in ghidra_out/index.csv; `--predict` = model table, no touch).
3. Static-first kit (zero box time): `field_census.py` (a global's shape from its addressing form + index math),
   `name_global.py` (every reader/writer + containment), `m118_flag_never_set.py` (gate satisfiability: test sites, OR
   immediates, register bit ops, save-carry), `fn.py 0xADDR`, `scratch/m71/dis.py LO HI [cap]` (objdump window;
   import as a module), `evidence.py audit|budget|prune|log`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md` + FOOTING terrain line; faction fields =
  `docs/field-atlas-faction.md` (M143-M162; atlas line: read §M297 first - the
  0x94d104 phrasing is WRONG).
- **ISOLATION (s254)**: successor ALWAYS "in 12m"; at fire start check `ps`
  for a live 'bash -l' + `gh pr list` + `git status`; if live, `git
  worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY
  there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A` - stage explicit paths (s254 collision lesson:
collision-check + worktree FIRST).
- **THE PICK (post-M309, s271): pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE. ANSWERED: M227-M319 + B1-B24 (M241 FAIL 2/5 #180).
  CLOSED enumeration (M220 .. M308, each with the NAMED § to read BEFORE re-opening and what it
  settled - incl. the M308 SITE-list shapes) + the OPEN shortlist one-liner are VERBATIM at
  `docs/pick-archive.md` §trim-s270.
  NEVER bp mid-instruction (s213). OPEN shortlist detail: `docs/pick-archive.md` §trim-s269 (b).
  CLOSED (s293): pick (v) = M319 - the guard is NOT hoisted. Memo has 6 read/test instrs
  image-wide in 5 funcs, readers(5) subset writers(15); the 8 unguarded sites have 4 nameable
  owners + 8 direct callers, 0/9 CFG arrivals memo-tested, and the only memo-reading caller
  (FUN_004f5a70) is itself an owner, so its read is its OWN guard; G7 is the classifier's
  positive control. NAMED ## M319 (7/7, digest 459f47e3178f439d, 12/12+1 NO-OP, selftest 4/4).
  OPEN PICK after M319: (vi) NAME the two still-unnamed memo-site owners FUN_004ee410 (sites
  0x4ee6c9/0x4ee883, caller FUN_004f5a70) and FUN_004f41f0 (sites 0x4f44a8/0x4f455d, callers
  FUN_00416ef0/FUN_00416f60/FUN_0041a8f0/FUN_004f5a70): what each DOES, and what the shared
  arrival test `BYTE PTR [eax+0x38],0x40` (3 of the 9) gates. Sites/owners/callers/arrivals
  are printed at `evidence/m319_guard_hoist.txt:24-52`; the 3rd owner FUN_004e47d0 is already
  the FOUNDER (NAMED ## M282). No box time.
  Lists live in NAMED ## M310-M319, not here.**
    READER LAWS still BIND (incl. B18/B19/B20/M299/M302/M303/M304): every kickoff + skill
  `instrument-laws.md` + §CHAIN-PICKS.
## LIVE FACTS / KIT

- **BOX**: state UP, last touch MEASURED s258 (one read-only /proc pass;
  s245..s257 + s259/s260 ZERO) (m54b_clean at y2150 r50, TracerPid 0, yama=0;
  pid via `pgrep -x terran.exe`, NEVER hardcoded) —
  RE-CHECK `accept_ready.py`; it BLOCKS on credit 0 (d0-gated income, STRUCTURAL here): walk/scan kinds
  run anyway; production kinds need the FIX recipe (relaunch+m54g_prep+drive1+enqueue, ~6 s/turn warm).
   `sudo -n python3 scripts/smac_preflight.py` before arming. **ptrace law (s211): yama back to the
   PRE value after every run, never hardcoded; the harness stays uid 1000 (sudo breaks the prefix) -
   exact commands in skill `wine-operations.md`.**

## TRAPS — rules (FULL s241 text verbatim: `docs/pick-archive.md` §s242-traps; detail §trim-s205/§s198; laws: skill
`instrument-laws.md` + `wine-pitfalls.md`)

1. A `fired=` list is the MODEL's prediction, not events; a no-event is evidence only once the bp is CONFIRMED
   to exist there; a gate may only read a field the harness SETS. (FULL: pick-archive §s242-traps)
2. Check the instrument before believing a no-event: deref-conditions silently never fire; a return-site bp
   prints the OLD eax; ZERO CALLS can be the GAME - scan /proc for the vptr first. (FULL: §s242-traps)
3. Register semantics live in the ENCODING (scaled vs byte addressing never compare equal; an RMW through a
   COPIED register evades store-shape greps - a hw watchpoint on the FIELD answers "who writes it"). (FULL: §s242-traps)
4-11. (MOVED VERBATIM to `docs/pick-archive.md` §trim-s256: gdb printf/script + call-frame rules; a >90 s
   census is never foreground; a PASS on a non-discriminating shape is no PASS; hw-watchpoint read-back rules.)
12-13. Both gdb-detach laws (a census can leave gdb ATTACHED; the turn driver returns rc=0 while AI
    upkeep plays). FULL VERBATIM: `docs/pick-archive.md` §trim-s268.
14-15. (MOVED VERBATIM to `docs/pick-archive.md` §trim-s262: queue-tail STALE ids + id-0 sentinel +
   negatives-belong-to-TYPE; PRODFLAG 0x4efe60 fires for EVERY record walked (FACTION BANDS) - attribute the
   sweep by its own predecessor; list cursor read BEFORE the seek = PREVIOUS cursor; dirty-tree
   `milestone.py start` = stash, start, pop.)
16-23. (MOVED VERBATIM to `docs/pick-archive.md` §trim-s245: objdump prints UPPERCASE; ARM BEFORE ANY
   SCREEN; the SIGUSR1/SIGPIPE `handle` tails; byte-field BIT OPS vs dword scans; a VALUE SAMPLER is NOT
   a STORE CENSUS.)
24. **A PASSING ASSERTION IS NOT A GATE (s269, #281 on M308; all 4 P2s were one defect: an assert that can pass
   on an UNMEASURED state — and 3 of the sub-conditions written to FIX them were THEMSELVES decorative).** Law: after
   repairing a gate run a MUTATION harness (`scripts/<id>_mutate.py`), exit non-zero unless EVERY mutation reddens its
   named gate; mutate a MEASURED FACT, never a dict ENTRY the assert reads as a whole; keep mutation ids out of the
   A-number namespace. Worked defect list + the `m308_mutate.py` 8/8 reference VERBATIM:
   `docs/pick-archive.md:996` §trim-s292 (b); mechanics: skill `references/instrument-laws.md:975`
   (§harness is STATE) and `:1031` (§four outcomes).
## CLOSING ORDER (exactly — the kickoff carries the same list, and the full 7-step text lives
VERBATIM at `docs/pick-archive.md` §trim-s269). Order: 1 `SESSION_CURSOR.md` (<=600 B) BEFORE the
rest, in case of compression. 2 `## Session <N+1>` APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers
WITH the command that produced them). 3 the `<ID>` block in `NAMED.md` (<=1 KB) + patch IN PLACE any
earlier block this round qualifies; every VERIFIED row names the mutation that reddens it
(no mutant = INFERRED/OPEN, or pin it + mutate it before submit). 4 `NEXT_PROMPT.md` patched BY SECTION to <=12,000 B (budget's
warn), every addition paired with a deletion. 5 sync the skill ONLY if edited (`diff -rq skill/
~/.hermes/skills/smac-cvr-format/` then `rsync`). 6 `git add <explicit paths>` + commit, then
`python3 scripts/gate.py --base main` GREEN + `python3 scripts/review_lint.py --id <id>` PASS.
7 submit -> `python3 scripts/ai_review.py <n>` (Strata local review; Greptile if credits return) ->
triage ALL findings in one reply, re-measure at head -> merge ONLY on a real PASS (docs/AI-REVIEW.md).