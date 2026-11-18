# NEXT_PROMPT.md - footing (s274: census picks (a) ds:0x68cbb0 and (b) the 0x95da40 table ANSWERED as ONE milestone - M311, 8/8 gates + 11/11 mutations; B22 is MERGED (#286); historical header + CLOSED enumeration + traps 14-15 VERBATIM at `docs/nextprompt-archive-m299-b20.md` and `docs/pick-archive.md` section trim-s262. STATE: B1-B22 + M54A-M311 done; track ANALYSE, B23 QUEUED; pre-existing #180/#105 NOT this chain.)
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
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a census claim; no
box/`/proc`/gdb time; box-debt pre-step N/A; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B21 MERGED**
(per-rung cmds: `NAMED.md` §CHAIN-BUILDS; B21 acceptance `python3 -m sim.selftest --b21 <sav>` +
`evidence/b21_composedrun.txt:93`). Build rung **B22 MERGED** (#286, `3f645e1`; 12/12 gates, `evidence/b22_composedgrowth.txt`) - and B23 is now **QUEUED, NOT NEXT**: `track_mode.py` flips to `MODE=ANALYSE analyse_since_build=0 last_build=B22` after every build merge, so the fire after B22 ANALYSES. ANALYSE PICKS still open, in order of value: (a) `ds:0x68cbb0` - `.data`, 340 xrefs, exactly 6 stores, all in `0x4e3000-0x4f6000`; (b) the 304-B table at `0x95da40` bit `0x20`; (c) `FUN_00470fe0` / `004715d0` / `00471fd0` (M310's neighbours). B23 = the queue's PER-TURN progress composed through the WRITER (B11's law in the written container, not in memory) - build it when track_mode says BUILD again.
Answered by M311: census pick (a) ds:0x68cbb0 = the CURRENT-RECORD INDEX of the 304-B array at 0x95da10, and (b) the 0x95da40 table = that SAME array at +48 - one milestone. Next ANALYSE picks: (c) FUN_00470fe0 / FUN_004715d0 / FUN_00471fd0, then ds:0x68cbb4's 19 unexplained writers. Build candidates: (i) B21's composed run + the B12 production leg in ONE written image (recorded m56 arrival grows
the unit array while the ledger grows - B21 proved year+counts compose together); (ii) the pod-scan PRECHECK chain
end-to-end (B15+B16+B17 with save-only inputs). Track_mode FIRST, every fire.

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
- **THE PICK (post-M309, s271): pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). M308 is CLOSED — merged in #281 with its review round (Greptile's 4 P2s fixed + mutation-tested). track_mode is AUTHORITATIVE: a merge does
  NOT flip the immediate fire (s259/s260); next_rung B22 stays queued. ANSWERED: M227-M309 + B1-B21 (M241 FAIL 2/5 #180).
  CLOSED enumeration (M220 .. M308, each with the NAMED § to read BEFORE re-opening and what it
  settled - incl. the M308 SITE-list shapes) + the OPEN shortlist one-liner are VERBATIM at
  `docs/pick-archive.md` §trim-s270; era text: `docs/nextprompt-archive-m299-b20.md` §closed-era.
  NEVER bp mid-instruction (s213). OPEN shortlist detail: `docs/pick-archive.md` §trim-s269 (b).
  **CLOSED (s272): FUN_00470b90 = the view object's DEBUG-GATED (this+0x1dd70 bit 0x2000) GOAL
  duplicate-invalidator + one-char-token logger; it owns the GOAL kind<->token map, and Ghidra's
  42-selector/8-handler structure lives ONLY in the table bytes (the case LIST agrees with them -
  0x29 is 41 - so do not re-litigate that; my two overclaims are retracted in Session 272). Read
  ## M310 before re-opening.**
  **NEXT PICK (s272 close), in order: (i) the two sinks M309 left - **ds:0x68cbb0** (.data, 340
  refs, exactly 6 stores, all inside 0x4e3000-0x4f6000, passed as the owner arg at 5 GOAL-insert
  sites) and the **304-B-stride table at 0x95da40** (96 refs) whose bit 0x20 the single +0C reader
  tests - census the bit, do not guess the stride; (ii) WHO fires the check: FUN_00470fe0 (180 B,
  4 callers incl. FUN_004715d0), FUN_004715d0 (1086 B, 1 caller 0x4725e9), FUN_00471fd0 (1338 B,
  5 callers in FUN_00472810) all forward a coordinate pair into FUN_00470b90 under tile-legality
  gates (FUN_00469060 test / FUN_00422060 != 0) - name the event; (iii) still open from M310: the
  game meaning of a GOAL, the one-char tokens, and WHY a GOAL priority can be NEGATIVE (the only
  invalidation trigger). The open list lives in NAMED ## M310 / ## M309, not here.**
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
24. **A PASSING ASSERTION IS NOT A GATE (s269, Greptile #281 on M308).** All 4 P2s were one defect -
   an assert that can pass on an UNMEASURED state (a classifier blind to `mov eax,ds:G`; bounds
   pre-filtered by the expected constants; a rule tested by mnemonic presence; attribution by instruction
   proximity) - and **3 of the sub-conditions I wrote to FIX them were THEMSELVES decorative**. Law: after
   repairing a gate run a MUTATION harness (`scripts/<id>_mutate.py`: copy the instrument, re-create each
   defect by anchor->replacement, exit non-zero unless EVERY mutation reddens its named gate). Mutate a
   MEASURED FACT so it is false on the real bytes (a branch target off-by-one), never a dict ENTRY the assert
   reads as a whole. Keep mutation ids out of the A-number namespace (M1..M8 vs A1..A36). Reference:
   `scripts/m308_mutate.py` -> `8/8 mutations reddened their target checks`.
## CLOSING ORDER (exactly — the kickoff carries the same list, and the full 7-step text lives
VERBATIM at `docs/pick-archive.md` §trim-s269). Order: 1 `SESSION_CURSOR.md` (<=600 B) BEFORE the
rest, in case of compression. 2 `## Session <N+1>` APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers
WITH the command that produced them). 3 the `<ID>` block in `NAMED.md` (<=1 KB) + patch IN PLACE any
earlier block this round qualifies. 4 `NEXT_PROMPT.md` patched BY SECTION to <=12,000 B (budget's
warn), every addition paired with a deletion. 5 sync the skill ONLY if edited (`diff -rq skill/
~/.hermes/skills/smac-cvr-format/` then `rsync`). 6 `git add <explicit paths>` + commit, then
`python3 scripts/gate.py --base main` GREEN. 7 submit/merge ONLY on a real PASS with the Greptile
review on the head commit finished and every P2 triaged in the PR body (fix or one-sentence
dismissal).