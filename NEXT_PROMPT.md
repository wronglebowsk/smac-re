# NEXT_PROMPT.md - footing (s259 close: M303 SUBMITTED (branch milestone/m303, PR open - NOT merged per kickoff) - B19's `the 0x51e02c 0x94ed28 post-read downstream` lead CLOSED by the static census `scripts/m303_downstream.py` (`evidence/m303_downstream.txt`): 0x51e02c is the LOAD HALF of a byte RMW ++ (lea 0x51e033 SAME SIB+disp / inc dl / store 0x51e03e; dl then DEAD; je 0x51e040 tests ebx, not the byte) of the per-block visit-CNT byte array 0x94ed28 = 0x94eca8+0x80 - 8 blocks x 8380-B records, 128 x {MAX@+0, CNT@+128}, zeroed per call at 0x51dcb8-0x51dd03 - the BYTE twin keyed by (block,site) of the DWORD slot table 0x989ce8 keyed by site; addr = site + 8380*block + 0x94ed28, the fold 65->131->2095->*4 shadow-verified and 8380 == the init's own block step (stride derived TWICE); B18-28 REFUTED for this expression (the esi fold 0x51dfb1-ba in-window feeds the DWORD twin); family = 11 literal mentions, all consumers cmp/test, no byte feeds the DWORD MAX, no store outside FUN_0051dcb0; name_global --disp "0 writes" is the register-after-lea blind spot. PASS M303 10/10 (A1-A10; byte-identical reruns; zero box). LAND THIS PR FIRST (MERGE RULE: gate green + Greptile reviewed, then `milestone.py merge`). #270 (M302) + #269 (B19) MERGED; pre-existing open PRs #180/#105 are NOT this chain. B1-B19 + M54A-M302 MERGED.)
Overflow: pick-archive (VERBATIM blocks - read only the picked section), NAMED.md
(§CHAIN-BUILDS/§CHAIN-PICKS - grep only), skill instrument-laws.md.

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor; its summaries die on the output cap. **Whatever is not
finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 15 `git add -A && git commit`** (s187: call 25 = 167k,
  zero commits — ~7k tokens/call) — every later step must leave a committed file.
- JSON only: no XML in tool args. Writes over ~4 KB drift -> rejected as missing `path`: retry once, re-emit as pure
  JSON (never fragment). Branch + skeleton commit BEFORE probing (s189: 108k vs 167k).
- **30-40** STOP MEASURING: an ungreen acceptance IS the finding — write blocker + number, merge nothing.
- **40-50** closing order, TERSE (see CLOSING ORDER; the caps there bind).

Survivability: cursor <=600 B before any >2-min step; never `rm`/`git checkout --`; doc writes patch/append.
**Batch: 5 static milestones per census script, 1 box milestone per batch — doc headroom, not capability, is the cap.** Caps (BYTES, what `budget` prints): NEXT_PROMPT warn 12,000/fail 16,000 — CLOSE at <= 12,000; SKILL.md
warn 55,000 (keep near 44 k, always-loaded under the 60 k ritual); SESSION_NOTES warn 110 k. Split rule: settled text
VERBATIM to a reference / `NAMED.md` section; RULES + pointer stay; re-run `budget`.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>` from merged history. BUILD ⇒ build
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a census claim; no
box/`/proc`/gdb time; box-debt pre-step N/A; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B19 MERGED** (per-rung cmds: `NAMED.md` §CHAIN-BUILDS; B19: `python3 -m sim.selftest --b19 <sav>` +
`evidence/b19_visitcounter.txt:20`). Next build rung **B20**, UNAUTHORED - its fire writes it (B14/B16/B17/B18/B19
did). Candidates from the landed frontiers: the FUN_005aff90 value body as a rung (B15/B17/B18 all DECLARED it;
M302 pinned the slot MAX it feeds), or
the FUN_0051dcb0 per-tile pass itself as a rung (M303: it zeroes-then-rebuilds BOTH counter tables per call). Track_mode FIRST, every fire - and LAND the M303 PR before starting B20.

## THE LEDGER

Merged M54A-M302 + B0-B19 (through s258) + hygiene #254/#255/#263/#264/#265/#267/#268/#269/#270; UNMERGED M83/M84, M86, M101, M103, M109, **M303 (this fire, PR open - LAND IT FIRST)** and **M241 (#180, 2/5, PR open - documented-FAIL re-confirmed, gates stand)**.
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
4. Self-documenting: `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m65_screen.py --samples 8`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md` + FOOTING.md's terrain line; faction fields =
  `docs/field-atlas-faction.md` (M143-M162; the atlas 0x94d104 phrasing is WRONG - M297 fixed the
  pair-flagword addressing, read §M297 before using the atlas line).
- **ISOLATION (s254)**: successor ALWAYS "in 12m"; at fire start check `ps`
  for a live 'bash -l' + `gh pr list` + `git status`; if live, `git
  worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY
  there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A` - stage
  explicit paths (the s253 sweep landed via #265; the s254 collision lessons:
  schedule "in 12m", collision-check + worktree FIRST).
- **THE PICK (s260): LAND THE M303 PR, then track_mode decides**
  (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE: s259 ran
  ANALYSE although B19+#270 had merged - a merge does NOT flip the immediate
  fire; next_rung B20 stays queued (BUILD candidates: FUN_005aff90 body, or the
  FUN_0051dcb0 per-tile pass). ANSWERED: M227-M303 + B1-B19 (M241 FAIL 2/5 #180).
  CLOSED - read the named NAMED § BEFORE re-opening: FUN_005f3f5b (M220); DIALOG
  +0x4c (M284-M288, live half INVALID s240); slot [+4] GATE (M299); the counter
  as executable (B19); the four live VALUES + slot-table CONTENTS pinned - the
  live side is PINNED, no re-dump of the four scalars without a reason (M302);
  the 0x51e02c post-counter read + the WHOLE 0x94eca8/0x94ed28 byte family
  (M303); 0x5832b0's callers (M300); ebx's "table 0x51de2c-0x51df1d" (M301
  REFUTED - code not a table; the 4 table-falsifiers are the s256 NEW LAW in
  SESSION_NOTES). NEVER bp mid-instruction (s213). OPEN shortlist: the
  0x56c6de continue-leg inside FUN_0055f650 + which loop chooses among its 7
  predicate sites; readers of [ebp-0x7c]/[ebp-0x1c]; sibling 0x5831a0 fed (x,y)
  right after the predicate; 188-row cursor caller; whose record BYTE[edi+0x7]
  is + the walk's tile-class/distance legs' MEANING; FUN_0051dcb0's IDENTITY
  (the per-tile pass that zeroes-then-rebuilds BOTH counter tables; outer loop =
  tile records stride 0x2c vs ds:0x92a378/0x92a37c - callers + cadence); the
  sibling fields of the 8380-B block record (byte field 0x950664, word 0x94e8a8
  ++'d pre-predicate, dword 0x94f4ec + word 0x950a64 preamble - all INDEXED by
  M303, semantics OPEN); FUN_0056d480/0056d630 + ds:0x985b10/0x985aec
  identities; the 0x94eca8 byte-table DUMP (2048 B: MAX@+8380k, CNT@+8380k+128,
  8 blocks; m302_livepins.py template); save-carried vs rebuild for BOTH tables
  (M302 OPEN + the byte family same question); the eax=1 leg: ONE model-decided
  row (M302 branchB), still NO live gdb witness (B19 G9): `NAMED.md`
  §CHAIN-PICKS. READER LAWS
  still BIND (incl. B18/B19/M299/M302/M303): every kickoff + skill
  `instrument-laws.md` + §CHAIN-PICKS.
## LIVE FACTS / KIT

- **BOX**: state UP, last box touch MEASURED s258 (ONE read-only /proc pass;
  s245..s257 + s259 ZERO box) (m54b_clean at y2150 r50, TracerPid 0, yama=0;
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
12-13. Both gdb-detach laws (skill Wine core): a census can leave gdb ATTACHED — check `TracerPid`,
    kill the stale gdb BY PID before calling the box clean; the TURN DRIVER returns rc=0 WHILE AI UPKEEP PLAYS —
    detach only after cp == human faction returns or the last recomputes go UNLOGGED.
14. The queue tail holds STALE ids (shift reaches only `0..pending-1`): never treat "first empty slot" or a
    stale tail as proof an id IS queued; id 0 = Colony Pod AND the empty marker, sentinel -39; negatives belong to
    the TYPE (196 -> -6, 195 -> -3). PRODFLAG (0x4efe60) fires for EVERY record the pass walks (128/322/323/194 =
    FACTION BANDS) — attribute the sweep by its own predecessor; the gate visit arrives a boundary AFTER the sweep.
15. A list cursor read BEFORE the seek is the PREVIOUS cursor (pump seeks at 0x497717 — print at 0x49771c).
    `milestone.py start` on a dirty tree: stash, start, pop (skill Git workflow).
16-23. (MOVED VERBATIM to `docs/pick-archive.md` §trim-s245: objdump prints UPPERCASE; ARM BEFORE ANY
   SCREEN; the SIGUSR1/SIGPIPE `handle` tails; byte-field BIT OPS vs dword scans; a VALUE SAMPLER is NOT
   a STORE CENSUS.)
## CLOSING ORDER (exactly — the kickoff carries the same list)

Terse past ~35 calls: acceptance numbers verbatim, no new prose, no "double check" reads; closing is PART of the
milestone. 0 `SESSION_CURSOR.md` (<=600 B: id | acceptance | merged? | next) BEFORE the rest. 1 `## Session <N>`
APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers WITH the command). 2 the `<ID>` block to `NAMED.md` (<=1 KB). 3 this
file patched BY SECTION to <= 12,000 B (`budget`'s warn; past it the next fire starts as a docs split). 4
`diff -rq skill/ ~/.hermes/skills/smac-cvr-format/`, reconcile, `rsync -a skill/ ~/.hermes/skills/smac-cvr-format/`
(content-identical; gate checks SKILL.md only). 5 `git add -A && git commit -m '<ID>: checkpoint'` then
`python3 scripts/gate.py --base main` GREEN. 6 submit/merge ONLY on a real PASS — and per the MERGE RULE only after
the Greptile review on the head commit finished (`gh pr checks` until nothing pending), its inline comments read, and
every P1 fixed or dismissed in the PR body in one sentence.
