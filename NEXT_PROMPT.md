# NEXT_PROMPT.md - footing (B26 TRIAGED 10/10 + harness 19/19+1 NO-OP, #328; old header/CLOSED-enumeration/traps VERBATIM at `docs/nextprompt-archive-m299-b20.md` + `docs/pick-archive.md`. STATE: B1-B26 + M54A-M329 done; (v)-(viii) ANSWERED (M328 chain2 / M321 / M327 / **M329 s307**); only (ix) left, box-GATED; next BUILD rung **B27, spine text NOT authored** (track_mode s307: MODE=BUILD, analyse_since_build=3); #180/#105 pre-existing.)
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
C1/C2 of `scripts/s292_cap_check.py` fail BY DESIGN (its STATUS note); only C3 stands.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>` from merged history. BUILD ⇒ build
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a censusim; no
box/`/proc`/gdb time; box-debt pre-step N/A; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B26 MERGED**
(B25 = #319 main 1556ce9; B26 = #328 main dd704d0; B26's full ACCEPT + THE LAW + the three retractions + the `found_units` 69->0 open question VERBATIM at `docs/pick-archive.md` §trim-s308-chain1 (a) with its sha1, and its per-rung cmds at `NAMED.md` §CHAIN-BUILDS + the per-id `## B<n>` blocks; `NAMED ## B25`/`## B26` govern; earlier build-track detail §trim-s298 (a), §trim-s299 (b)/(d)). **Next build B27, NOT YET AUTHORED** (`BUILD_SPINE.md` ends at B26): write its rung text BEFORE probing (one milestone = spine section + instrument).

 **DOC CAP: `NAMED.md` 239,090 B / 250,000 B FAIL (10,910 B headroom; `wc -c`; the s307 rotation note's 240,534 predates the M321 in-place refinement). LAW (s307): rotate VERBATIM to a `docs/named-archive-*.md` BEFORE writing your block — M329's block pushed it to 250,214 and two rotations (M255-M258, Method-that-worked) had to dig it back. Archive sha1s asserted by the rotate scripts.**

## THE LEDGER

Merged M54A-M327 + B0-B26 + hygiene #254-#280. UNMERGED: the six ids in `§trim-s202`, of which **M241 (#180, 2/5, PR open - documented-FAIL re-confirmed, gates stand)** is live.
Full list + reasons: `docs/pick-archive.md` §trim-s202; per-id semantics `NAMED.md` + `docs/named-archive-*.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** = readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it before you arm** (screen fixes in TRAPS).
2. Writer/flag chain (BOX ONLY, the chain is zero-box now) - VERBATIM at `docs/pick-archive.md`
   §trim-s295 (b): the m94/m97/m100/m102/m103 + m92/m95/m98/m117 family, `--predict` = model table.
3. Static-first kit (zero box time): `field_census.py` (a global's shape from its addressing form + index math),
   `name_global.py` (every reader/writer + containment), `m118_flag_never_set.py` (gate satisfiability: test sites, OR
   immediates, register bit ops, save-carry), `fn.py 0xADDR`, `scratch/m71/dis.py LO HI [cap]` (objdump window;
   import as a module), `evidence.py audit|budget|prune|log`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md`; faction fields =
  `docs/field-atlas-faction.md` (read §M297 first - the 0x94d104 phrasing is WRONG).
- **ISOLATION (s254)**: successor ALWAYS "in 12m"; at fire start check `ps`
  for a live 'bash -l' + `gh pr list` + `git status`; if live, `git
  worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY
  there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A` - stage explicit paths.
- **THE PICK: pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE. ANSWERED: M227-M327 + B1-B26 (M241 FAIL 2/5 #180).
  CLOSED enumeration (M220 .. M308, each with the NAMED § to read BEFORE re-opening and what it
  settled - incl. the M308 SITE-list shapes) + the OPEN shortlist one-liner are VERBATIM at
  `docs/pick-archive.md` §trim-s270.
  NEVER bp mid-instruction (s213). OPEN shortlist detail: `docs/pick-archive.md` §trim-s269 (b). NAMED **240,773**/250k FAIL (9,227 B headroom, `wc -c`) — ROTATE BEFORE ADDING A BLOCK (`scripts/m329_named_rotate.py`/`..._rotate2.py` did two at s307; s307 crossed 250,214 mid-fire and had to dig itself back).
  CLOSED pick rows (v = M319, vi = M321) VERBATIM at §trim-s300-chain1 (b) (sha1 b0e7c1d2614f2312); `NAMED ## M319` / `## M321` govern.
  CLOSED pick row (vii = M327) VERBATIM at §trim-s305-chain1 (a) (sha1 cfa455cbefd4); `NAMED ## M327` governs (harness 24/24, digest 91f58f3de03090c1, since the s305 review round).
  CLOSED pick row (viii = **M329**, s307) VERBATIM at §trim-s308-chain1 (b) with its sha1; `NAMED ## M329` governs (`ui_governor_options_pane(widget, page)`; the `ds:0x99aa38` 19-bit pack staging; publish `0x1c-0x1f` only, bit-disjoint from both faction-create defaults => REFINES `## M321`); ACCEPT 13/13 + harness 26/26 numbers are IN that block. **NO PICKS LEFT except (ix)** (live-box, GATED on operator authorization) — so the next fire is the **BUILD rung B27**: author its `BUILD_SPINE.md` section FIRST, then instrument it.
  Lists live in NAMED ## M310-M325 + the `## B<n>` blocks. READER LAWS still BIND:
  every kickoff + skill `instrument-laws.md` + §CHAIN-PICKS.

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
24. **A PASSING ASSERTION IS NOT A GATE** — an assert that can pass on an UNMEASURED state is a defect, not a
   gate; every gate needs a NAMED mutant that reddens it, and the fixes get mutated too. FULL text + the
   `m308_mutate.py` 8/8 reference: `docs/pick-archive.md` §trim-s296 (a); worked defect list, skill mechanics:
   §trim-s292 (b) at `docs/pick-archive.md:996`.
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
M320/M323/M324 result one-liners VERBATIM at `docs/pick-archive.md` §trim-s300-chain1 (a); `NAMED` governs.
M325 VERBATIM: §trim-s301-chain2 (a); NAMED ## M325.
M326 VERBATIM: §trim-s304-chain2 (a); NAMED ## M326.
M328 (s304-chain2): 91c64c=turn-start ENERGY snapshot; 920434='multi' session flag (noun INFERRED, lifecycle V). HURRY story closed. 14/14 030a6fc12e4a7cd7 x2; 38/38 (37+1 NO-OP) 36259eee0736d9c1; ST 5/5. NAMED ## M328.
M330 (s307-chain2): block+300=UPKEEP SPEND ACCUMULATOR — entry-zeroed, feeder 4f47f0 (ROUND>1, conditional halving), refund trunc(kx/3) k=1 diff4/2 diff>=5, mask gate VACUOUS (cl=8). 13/13 470d844054b1b101 x2; 31/31+1 NO-OP cf85092dea6baa93. NAMED ## M330.
