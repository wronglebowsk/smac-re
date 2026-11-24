# NEXT_PROMPT.md - footing (B37 s339 `5dd4119bd1882d1d`; M375 s338 `34bcef7ab64b9272`. STATE: B1-B37 + M54A-M375; (ix) box-GATED; (x) OPEN-LEADS; #180 pre-existing FAIL.)
Overflow: `docs/nextprompt-archive-m299-b20.md`, `docs/pick-archive.md`, NAMED §CHAIN-BUILDS/PICKS (grep only), skill instrument-laws.md.

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor; its summaries die on the output cap. **Whatever is not
finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time; **commit by call 15** (s187: call 25 = 167k, zero commits).
- JSON only, no XML. A write over ~4 KB that drifts -> `missing path`: retry as pure JSON, never fragment. Branch +
  skeleton commit BEFORE probing (s189).
- **30-40** STOP: an ungreen acceptance IS the finding — number + blocker, merge nothing.
- **40-50** closing order, TERSE (see CLOSING ORDER; the caps there bind).

Survivability: cursor <=600 B before any >2-min step; never `rm`/`git checkout --`; doc writes patch/append.
**Batch: 5 static per census script, 1 box — doc headroom is the cap.** Caps (BYTES, what `budget` prints): NEXT_PROMPT warn 12,000/fail 16,000 — CLOSE at <= 12,000; SKILL.md
warn 55,000 (keep near 44 k, always-loaded under the 60 k ritual); SESSION_NOTES warn 110 k. Split rule: settled text
VERBATIM to a reference / `NAMED.md` section; RULES + pointer stay; re-run `budget`.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>`. BUILD ⇒ build
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a censusim; no
box/`/proc`/gdb time; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B37 MERGED** (per-rung cmds `NAMED` §CHAIN-BUILDS; `## B34`-`## B37` govern).
**B38**: `track_mode.py` decides; author the rung in `BUILD_SPINE.md` BEFORE probing.
**DOC CAP: NAMED 245,047/250,000 (4,953 B — rotate a settled block first).**

## THE LEDGER

Merged M54A-M327 + B0-B26 + hygiene #254-#280. UNMERGED: the six ids in `§trim-s202`, of which **M241 (#180, 2/5, documented FAIL, gates stand)** is live.
Full list + reasons: `docs/pick-archive.md` §trim-s202; per-id semantics in `NAMED.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** = readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it before you arm**.
2. Writer/flag chain (BOX ONLY) - VERBATIM `docs/pick-archive.md` §trim-s295 (b): m94/m97/m100/m102/m103
   + m92/m95/m98/m117, `--predict` = model table.
3. Static-first kit (zero box time): `field_census.py`, `name_global.py`, `m118_flag_never_set.py`
   (gate satisfiability), `fn.py 0xADDR`, `scratch/m71/dis.py LO HI [cap]`, `evidence.py audit|budget|prune`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md`; faction fields =
  `docs/field-atlas-faction.md` (read §M297 first - the 0x94d104 phrasing is WRONG).
- **ISOLATION (s254)**: if a fire is live (`ps` for 'bash -l' + `gh pr list` + `git status`), use `git worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A` - stage explicit paths.
- **THE PICK: pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE.
  B37's own leads (ANALYSE, static, zero box): (a) the noun of **0x800** - set by BOTH `and 0xfffdfbff`+`or 0x840`
  arms (0x5553ed/0x5556e6) with 0x20000/0x400 cleared in the same mask - the first bit B37 could not name;
  (b) **FUN_00552970** (0x552cec arm, `or al,0x40`); (c) bit 13's noun (M373). ANSWERED: M227-M340,M344,M346 + B1-B37 (M241 FAIL 2/5 #180).
  CLOSED enumeration + pick rows + open-lead census (v..x4, B27) VERBATIM at `docs/pick-archive.md`
  §trim-s270 / §trim-s313-chain1 region-A (sha1 `8332dd50ba16`, `scripts/m333_nextprompt_trim.py --verify`).
  NEVER bp mid-instruction (s213).
  **NO STATIC PICKS LEFT** except **(ix)** (box-GATED); the analysis-only option is the OPEN-LEADS
  list, each with a NAMED question. STILL OPEN: (x6) other writers of the 0x92bde8..0x92bf14 pref
  block (chain-3); the two peace writers outside FUN_005537d0 — `0x53fcb3`/`0x523f4c` (chain-1, M368);
  `ds:0x985ba0`'s WRITER (M334). ANSWERED (do not re-derive): x1 M333, x7 M334, x8 M337, x9
  M342+M344+M346+M348, `0x999fa4` M353. Lists live in NAMED ## M310-M368. READER LAWS still BIND:
  every kickoff + skill `instrument-laws.md` + §CHAIN-PICKS.

## LIVE FACTS / KIT

- **BOX**: UP, last touch s258 (TracerPid 0, yama=0; pid via `pgrep -x terran.exe`). RE-CHECK
  `accept_ready.py`: it BLOCKS on credit 0 (d0-gated, STRUCTURAL); walk/scan kinds run anyway,
  production kinds need the FIX recipe (relaunch+m54g_prep+drive1+enqueue, ~6 s/turn warm).
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
4-11. (VERBATIM `docs/pick-archive.md` §trim-s256: gdb printf/script + call-frame; >90 s census never
   foreground; a PASS on a non-discriminating shape is no PASS; hw-watchpoint read-back.)
12-13. Both gdb-detach laws (a census can leave gdb ATTACHED; the turn driver returns rc=0 while AI
    upkeep plays). FULL VERBATIM: `docs/pick-archive.md` §trim-s268.
14-23. (VERBATIM `§trim-s262`: queue-tail STALE ids + id-0 sentinel + negatives-belong-to-TYPE; PRODFLAG
   0x4efe60 attribute the sweep by its predecessor; list cursor read BEFORE seek = PREVIOUS cursor;
   dirty-tree start = stash/start/pop. `§trim-s245`: objdump UPPERCASE; ARM BEFORE ANY SCREEN; SIGUSR1/
   SIGPIPE `handle` tails; byte-field BIT OPS vs dword scans; a VALUE SAMPLER is NOT a STORE CENSUS.)
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
Results: `docs/pick-archive.md` §trim-s313-chain1 region-B (sha1 `6f2ddbe32478`); per-id `NAMED ## <id>` GOVERN.
- M348/B34/B35 MERGED (slots <- Script.txt `#PRODUCEXQ/G`; a facility completion stamps NOTHING, 21 stores).
- M368/M369/M371/M373 MERGED: 0x2 TREATY, 0x4 TRUCE, 0x8 COMMLINK, 0x10 AT WAR; FUN_005551e0 clears 0x80000000 only when bit 13 is clear (one-shot protector); bit 27 does NOT gate that pass.
- B36 (s337) MERGED: FUN_00551a20 EXTRACTED AND RUN - 5 `test bl` blocks + an UNCONDITIONAL tail OR; pact=0x3, truce-after-war=0x8000010c, war=0x80000118; the ladder ACCUMULATES, so the state is the classifier's precedence (1>2>4 EQUALITY). 10/10.
- M375 (s338-c3) MERGED: 0x800000 = TREATY ON (any 0x17 write clears), 0x40 = SET TREATY + a 50-tick cell, 0x100000 = eviction tail; 0x80000018 is bit31+war, NOT bit23. 8/8.
- B37 (s339-c1) MERGED: the lifecycle RUN - `0x40` arms `0x94d4c8=0x32`; 10-insn countdown 0x5552b6..0x5552d4 (`and al,0xbf`@0x5552d1) with ONE exit; PEACE clears 0x40 so its expiry is a NULL write, WAR keeps it (0x78) so its expiry is real. 8/8 `5dd4119bd1882d1d`, 13 mutants.
- OPEN LEADS (ANALYSE lanes): bit 13 (0x2000) noun (M373); `0x4da404`'s 4th-arg flag; 0x800/0x20000/0x400 nouns (B37's arms); FUN_00552970's role (0x552cec arm); the 12-slot 0x92babc table (M374).
