# NEXT_PROMPT.md - footing (s257 close: B19 SUBMITTED (branch milestone/b19, PR open - NOT merged per kickoff) - the slot [+4] visit counter is EXECUTABLE (`sim/visitcounter.py`): the gated inc [0x989ce8+28*site+4]++ iff FUN_005832b0(x,y)!=0, the full 4-rung ladder ported from the pinned windows embedded IN evidence/m299_visitgate.txt, replayed over the 2321 recorded rows: 1222 CERTAIN-refuse / 0 CERTAIN-accept / 1099 POSSIBLE (branch-A 1099 / rung1 1222; baseline 20 eax=2 accepts, 1079 undecided on the never-recorded branch-B strides); the M300 24-caller + M301 eax-witness censuses re-grade from the SAME bytes. PASS B19 10/10, table-then-asserts, two runs byte-identical, `evidence/b19_visitcounter.txt`, registry `NAMED.md` §B19. THE NEXT FIRE LANDS THIS PR FIRST (AGENTS.md step 2: read diff + SESSION_NOTES section, gate green, `milestone.py merge` - track_mode counts rungs from MERGED history, so until merged next_rung stays B19). #267 (M300) + #268 (M301) MERGED; pre-existing open PRs #180/#105 are NOT this chain. B1-B18 MERGED.)
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
box/`/proc`/gdb time; box-debt pre-step N/A; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B18 MERGED, B19
SUBMITTED (this fire)** (per-rung cmds: `NAMED.md` §CHAIN-BUILDS; B19: `python3 -m sim.selftest --b19 <sav>` +
`evidence/b19_visitcounter.txt:20`). Next build rung **B20**, UNAUTHORED - its fire writes it (B14/B16/B17/B18/B19
did). Candidates from the landed frontiers: the FUN_005aff90 value body as a rung (B15/B17/B18 all DECLARED it), or
the 0x51e02c 0x94ed28 region-read leg. Track_mode FIRST, every fire - and LAND the B19 PR before starting B20.

## THE LEDGER

Merged M54A-M301 + B0-B18 (through s256) + hygiene #254/#255/#263/#264/#265/#267/#268; UNMERGED M83/M84, M86, M101, M103, M109, **B19 (this fire, PR open - LAND IT FIRST)** and **M241 (#180, 2/5, PR open - documented-FAIL re-confirmed, gates stand)**.
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
  `docs/field-atlas-faction.md` (M143-M162; pair-flagword addr fixed by M297: block 0x94d430+8380*fac,
  pair word at +0x18 + 4*(fac*2095+other) - the atlas 0x94d104 phrasing wrong - lead to fix).
- **ISOLATION (s254)**: successor ALWAYS "in 12m"; at fire start check `ps`
  for a live 'bash -l' + `gh pr list` + `git status`; if live, `git
  worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY
  there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A` - stage
  explicit paths (the s253 sweep landed via #265; the s254 collision lessons:
  schedule "in 12m", collision-check + worktree FIRST).
- **THE PICK (s258): LAND THE B19 PR, then ANALYSE from the shortlist**
  (track_mode FIRST; collision check FIRST per ISOLATION). If B19 is already
  merged by the time you start, track_mode may say next_rung=B20 BUILD - the
  rung is UNAUTHORED, write it from the B19/B18 DECLARED frontiers.
  ANSWERED: M227-M301 + B1-B19 (M241 FAIL 2/5 #180). CLOSED: FUN_005f3f5b (M220);
  DIALOG +0x4c (M284-M288, live half INVALID s240); slot [+4] counter GATE (M299)
  AND the counter ITSELF as an executable (B19 - read §B19 BEFORE re-deriving the
  ladder: every constant decodes from the windows embedded in m299_visitgate.txt;
  the ONLY gap is the four live VALUES + table CONTENTS); 0x5832b0's callers
  (M300 - see §M300 BEFORE re-censusing anything of it); ebx's
  "table 0x51de2c-0x51df1d" (M301 REFUTED - it is 243 B of CODE: the base_array
  0x95da10 walk (304-B rows, count ds:0x985af4) + its exit block. Gates NOTHING of
  the 0x51dffd decision; the predicate's eax cannot reach it. Read §M301 BEFORE
  re-opening it; the 4 table-falsifiers are the s256 NEW LAW in SESSION_NOTES).
  NEVER bp mid-instruction (s213). OPEN shortlist + M300/M301/B19 leads (hub-visit gating;
  0x56c6de continue-leg INSIDE FUN_0055f650, the 7-site predicate caller; which loop
  chooses among those 7 sites; readers of the stored predicate slots [ebp-0x7c]/
  [ebp-0x1c]; sibling 0x5831a0 fed (x,y) right after the predicate; 188-row cursor
  caller; whose record the walk's exit block tests as BYTE[edi+0x7] (edi = [ebp-0x4],
  sole pre-range writer 0x51dd28) + what its tile-class/distance legs MEAN; the
  0x51e02c byte[site+8380*block+0x94ed28]
  NAMED:371; **the ONE read-only /proc pass that grades B19 ABSOLUTELY: dump
  ds:0x92a380 (rand+1) + strides ds:0x69220c/0x692210 + ds:0x985ac4 dword + the
  0x989ce8 slot table (28 B x 128: MAX +0 AND counter +4) + the 0x94eca8 cell
  bytes - every CERTAIN/POSSIBLE bracket collapses to a point, and the live
  flag bit decides the 0-certain-accept finding**; the eax=1 leg has 0 witnesses
  in the recorded rows (B19 G9 - a longer/better-paired window may supply one):
  `NAMED.md` §CHAIN-PICKS. READER LAWS still BIND - the FULL
  current set (incl. B18 + B19 + M299 laws) rides EVERY kickoff + skill `instrument-laws.md`
  + §CHAIN-PICKS.
## LIVE FACTS / KIT

- **BOX**: s244 state UP (s245..s257: s249 read-only /proc pass only; s250-s257 ZERO box - state identical)
  (m54b_clean at y2212, cnt 30, TracerPid 0, yama=0; not t0) —
  RE-CHECK `accept_ready.py`; it BLOCKS on credit 0 (d0-gated income, STRUCTURAL here): walk/scan kinds
  run anyway; production kinds need the FIX recipe (relaunch+m54g_prep+drive1+enqueue, ~6 s/turn warm).
   `sudo -n python3 scripts/smac_preflight.py` before arming. **ptrace law (s211): yama back to the
   PRE value after every run, never hardcoded; the harness stays uid 1000 (sudo breaks the prefix) -
   exact commands in skill `wine-operations.md`.**

## TRAPS — rules (FULL s241 text verbatim: `docs/pick-archive.md` §s242-traps; detail §trim-s205/§s198; laws: skill
`instrument-laws.md` + `wine-pitfalls.md`)

1. A `fired=` list is the MODEL's prediction, not events; a no-event is evidence only once the bp is CONFIRMED to
   exist there. Gates PREDICT from live memory, then confirm with counters; a counter at a site that is BOTH branch
   target and loop-completion fallthrough is NOT a leg proof (0x5a7f9f); a gate may only read a field the harness SETS.
2. Check the instrument before believing a no-event: `if *$ecx==X` DEREFERENCES and silently never fires; a bp at a
   return-site `mov eax,[ebp-0xc]` prints the OLD eax (break at the NEXT insn, 0x5aa24a); `lea edi,[eax+1]` makes edi
   the MODULUS (read the arg); ZERO CALLS can be the GAME — scan /proc for the vptr first.
3. Register semantics live in the ENCODING: `[reg*4+disp]` vs `[reg+disp]` differ by scaling — a condition testing one
   against the other never fires; a RMW through a COPIED register evades store-shape greps — a hw watchpoint on the
   FIELD answers "who writes it".
4-11. (MOVED VERBATIM to `docs/pick-archive.md` §trim-s256, s256, to hold the 12 k cap: gdb
   printf/script laws + the manual-call-frame and ONE-vs-TWO-`\n` rules; a >90 s census is
   never foreground; dialogs swallow keys while the HUD bar reads THROUGH them; a PASS on a
   non-discriminating shape is no PASS; `credit` is recomputed every round; a hw watchpoint
   REPORTS only a VALUE CHANGE with pc past the store; a silent bp AT that reported pc is
   EATEN - read memory one insn later.)
12-13. Both gdb-detach laws (skill Wine core): a census can leave gdb ATTACHED — check `TracerPid`,
    kill the stale gdb BY PID before calling the box clean; the TURN DRIVER returns rc=0 WHILE AI UPKEEP PLAYS —
    detach only after cp == human faction returns or the last recomputes go UNLOGGED.
14. The queue tail holds STALE ids (shift reaches only `0..pending-1`): never treat "first empty slot" or a
    stale tail as proof an id IS queued; id 0 = Colony Pod AND the empty marker, sentinel -39; negatives belong to
    the TYPE (196 -> -6, 195 -> -3). PRODFLAG (0x4efe60) fires for EVERY record the pass walks (128/322/323/194 =
    FACTION BANDS) — attribute the sweep by its own predecessor; the gate visit arrives a boundary AFTER the sweep.
15. A list cursor read BEFORE the seek is the PREVIOUS cursor (pump seeks at 0x497717 — print at 0x49771c).
    `milestone.py start` on a dirty tree: stash, start, pop (skill Git workflow).
16-23. (MOVED VERBATIM to `docs/pick-archive.md` §trim-s245, s245, to hold the 12 k cap: objdump
   prints UPPERCASE; gdb startup/exit chatter whitelist; ARM BEFORE ANY SCREEN; the SIGUSR1/
   SIGPIPE `handle` + ~400-`continue` tails; a bp on a game-wide reader; byte-field BIT OPS vs
   dword scans; a stride conflict is ONE multiply read twice; a zero-writer global is LOAD-TIME
   data; a VALUE SAMPLER is NOT a STORE CENSUS; a census PARSER is not a log.)
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
