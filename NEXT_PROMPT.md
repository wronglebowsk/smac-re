# NEXT_PROMPT.md - footing (M316 MERGED #305 (5 P2 all accepted); M315 #301; M314 #299; old header/CLOSED-enumeration/traps VERBATIM at `docs/nextprompt-archive-m299-b20.md` + `docs/pick-archive.md`. STATE: B1-B23 + M54A-M316 done; track: B24 IS NEXT (track_mode flipped to BUILD at the M316 merge - 3 analyses since B23; the OPEN picks wait until after the build); #180/#105 pre-existing.)
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
`evidence/b21_composedrun.txt:93`). BUILDS **B1-B22 MERGED**; B23 MERGED as #297 (main 77a170d): 12/12 + falsifiers G10/G11 + 5 rivals, 3 P2 ALL accepted at review head (s280); next build B24 **BUILD-NEXT as of s286** (M314/M315/M316 landed since B23; track_mode flips to ANALYSE only after the NEXT build merge). OLD picks (a)(b) answered by M311 (#289, 8/8, digest 625cd5877271cd85); (c) retracted by M312's A4.

M316 MERGED as #305 (main see git log): 18/18 + 32/32, digest dcc6ce82fc98aec4;
5 P2 ALL accepted; the review's window-scope P2 BROKE THE SITE-TWIN LAW (0x94f2d8 = same
5-field/16 B record shape; REMOVER 0056d780 12 sites = goal-cancel; INITIALIZER 0056d710
fills both arrays). NAMED ## M316 governs.
M315 MERGED as #301 (main 0ad96af): 10/10 + 29/29 (22 expectation + 7 CODE mutants via
M315_PATCH), digest 3976ca97eedc1e19; 6 P2 ALL accepted at review head 754b4fa6; the
caller-guard claim DOWNGRADED to OPEN; pair reach 16 B -> 17 B; blind re-verify records
`evidence/s285_reverify_*` (#304). NAMED ## M315 governs.

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
  **CLOSED (s278): pick (i') NAME THE EVENTS - ONE interaction band
  [0x50bb20,0x5175b4) carries 20 of 28 hub owners + 9 thunk owners; pumps 00512b40 (menu-ID + nav-VK two-stage switches; its door FUN_0041bda0
  is a data pointer at 0x6724a8 in the multi-table run @0x672290) and 00516b80 (Q-Z order keys,
  startup callback push@0x51892d) call INTO it; map_click_handler (M28) reaches it directly.
  Full law NAMED ## M313.
  OPEN PICKS after M316, in order: (iii') the engine FUN_00556690 (14.3 kB: what it DECIDES; its
  callers FUN_005208f0/FUN_0059ce10); (iv) NAME the selection-REFRESH PAIR
  (call 0x4e8d60 + call 0x4e78e0) - M315 proved the pair is the memo's reaction but neither
  callee is in NAMED; (v) the 8 memo sites with NO local dedup guard - census their callers and
  ask whether the guard is hoisted there (M315 pinned 4/12 guarded, 8/12 unguarded).
  Lists live in NAMED ## M310 / ## M313 / ## M314 / ## M315 / ## M316, not here.**
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