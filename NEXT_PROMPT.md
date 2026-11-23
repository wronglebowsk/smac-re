# NEXT_PROMPT.md - footing (B26 TRIAGED 10/10 + harness 19/19+1 NO-OP, #328; old header/CLOSED-enumeration/traps VERBATIM at `docs/nextprompt-archive-m299-b20.md` + `docs/pick-archive.md`. STATE: B1-B27 + M54A-M333 done (energy round executable + carried, `NAMED ## B27`; feeder-slot noun + carried half-unit, `NAMED ## M333`); only (ix) left, box-GATED, and the **(x) OPEN-LEADS** list below is the analysis-only option (x1/x2/x3/x4 answered); #180/#105 pre-existing.)
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
(B25 = #319 main 1556ce9; B26 = #328 main dd704d0; B26's full ACCEPT + THE LAW + the three retractions + the `found_units` 69->0 open question VERBATIM at `docs/pick-archive.md` §trim-s308-chain1 (a) with its sha1, and its per-rung cmds at `NAMED.md` §CHAIN-BUILDS + the per-id `## B<n>` blocks; `NAMED ## B25`/`## B26` govern; earlier build-track detail §trim-s298 (a), §trim-s299 (b)/(d)). **B27 MERGED-BY-THIS-FIRE (s309)**. **Next build B28**: the spine ends at B27 - that fire authors its rung text in `BUILD_SPINE.md` BEFORE probing, as B14-B27 did.

 **DOC CAP (`wc -c` s314 review round): `NAMED.md` 246,245/250,000 FAIL = 3,755 B headroom — UNDER the 5 KB trigger: ROTATE FIRST next fire (rotation-2 landed: M315 → `docs/named-archive-m333-rows.md:54` §rotation-2, sha1 `c70cc525ecbd`, `scripts/m333_named_rotate2.py --verify`; rotation-1 M259-M261 → `:6` sha1 `f78e7ef04359`, `scripts/m333_named_rotate.py --verify` — both re-hash byte-exact; the §rotation-2 NAME collides with m332-rows' older §rotation-2, verify filters on the archive name too). NEXT_PROMPT ~11.7 k/12,000 (regions A+B → `docs/pick-archive.md` §trim-s313-chain1, `scripts/m333_nextprompt_trim.py --verify`). s312 = #346: 9/9 `d2691dc5abb39240`, harness 22/22 `a9a944201849d026`.**

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
  NEVER bp mid-instruction (s213). OPEN shortlist detail: `docs/pick-archive.md` §trim-s269 (b). NAMED cap: see §BUDGET's DOC CAP line (s311).
  CLOSED pick rows + the superseded open-lead census they sat in (v = M319, vi = M321, vii = M327,
  viii = M329, x2 = M332, x3/x4 = M331, B27) VERBATIM at `docs/pick-archive.md` §trim-s313-chain1
  region-A (sha1 `8332dd50ba16`, byte-exact asserted by `scripts/m333_nextprompt_trim.py --verify`); the
  per-id `NAMED ## <id>` blocks GOVERN and carry every ACCEPT/harness digest.
  **NO STATIC PICKS LEFT** except **(ix)** (live-box, operator-GATED), so the analysis-only
  option is this OPEN-LEADS
  list, each with a NAMED question: (x1) ANSWERED by M333 — slot noun = a facility the base HAS
  (bit in base+0x8c), bit5 of block+0 = a CARRIED HALF-UNIT exclusive to FUN_004f47f0;
  (x5) the 'multi' label only (`92bdf8` = the pref `Top Menu`);
  (x6) NEW (M332): the difficulty INDEX->label order (cmps top out at 4, M330's k-table needs k=2
  at >=5); other writers of the 0x92bde8..0x92bf14 pref block; `0x8f0090`'s consumer; callee
  `0x5f1394`; (x7) NEW (M333): the REMOVAL path inside FUN_004f47f0's loop (mapper 0x4f49b6,
  bitmap bit-CLEAR 0x4f49e1, 3 stores to block+0x220, callees 0x4e40a0/0x6265a2/0x48f100) and
  ds:0x985ba0's writer (outside .text). Generate a combat/tech/victory pick before taking one: no footing exists.
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
Result one-liners M320/M323/M324/M325/M326/M330/M331 + the M330 #340 sidecar note:
`docs/pick-archive.md` §trim-s313-chain1 region-B (sha1 `6f2ddbe32478`, `--verify`); the per-id
`NAMED ## <id>` blocks GOVERN.

