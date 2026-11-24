# NEXT_PROMPT.md - footing (B32 MERGED s327: 10/10 print `e6875c63c8c2f911`, harness 13/13 `155781675e5086a1`; old header/CLOSED-enumeration/traps VERBATIM at `docs/nextprompt-archive-m299-b20.md` + `docs/pick-archive.md`. STATE: B1-B32 + M54A-M350 (`## B32`, `## M349`, `## M350`); only (ix) left, box-GATED; (x) OPEN-LEADS is the analysis-only option; #180 pre-existing.)
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
**Batch: 5 static per census script, 1 box — doc headroom is the cap.** Caps (BYTES, what `budget` prints): NEXT_PROMPT warn 12,000/fail 16,000 — CLOSE at <= 12,000; SKILL.md
warn 55,000 (keep near 44 k, always-loaded under the 60 k ritual); SESSION_NOTES warn 110 k. Split rule: settled text
VERBATIM to a reference / `NAMED.md` section; RULES + pointer stay; re-run `budget`.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>`. BUILD ⇒ build
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a censusim; no
box/`/proc`/gdb time; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B32 MERGED** (per-rung cmds `NAMED` §CHAIN-BUILDS; `## B29`-`## B32` govern).
**B31 = the recorded-run ORACLE** (6 gains/2 losses; bulk head->bit 0/6) and **B32 MERGED = the UNIT
leg** (M349's decode attached: 4/4 unit heads stamp the mapper bit, facility-range 0/2, post-pop 0/6 -
`## B32`). **Next build B33**: author its rung text in `BUILD_SPINE.md` BEFORE probing - walk the
facility leg's own branch to the shared OR at `0x4f0ec0` (WHY facility 2 at Virgin Soil does not
stamp), or a fresh recorded facility completion.

  **DOC CAP (s328): NAMED 244,044/250,000; M350 rotated; NEXT_PROMPT <=12,000.**

## THE LEDGER

Merged M54A-M327 + B0-B26 + hygiene #254-#280. UNMERGED: the six ids in `§trim-s202`, of which **M241 (#180, 2/5, documented FAIL, gates stand)** is live.
Full list + reasons: `docs/pick-archive.md` §trim-s202; per-id semantics in `NAMED.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** = readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it before you arm**.
2. Writer/flag chain (BOX ONLY) - VERBATIM `docs/pick-archive.md` §trim-s295 (b): m94/m97/m100/m102/m103
   + m92/m95/m98/m117, `--predict` = model table.
3. Static-first kit (zero box time): `field_census.py` (a global's shape from its addressing form + index math),
   `name_global.py` (every reader/writer + containment), `m118_flag_never_set.py` (gate satisfiability: test sites, OR
   immediates, register bit ops, save-carry), `fn.py 0xADDR`, `scratch/m71/dis.py LO HI [cap]` (objdump window;
   import as a module), `evidence.py audit|budget|prune|log`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md`; faction fields =
  `docs/field-atlas-faction.md` (read §M297 first - the 0x94d104 phrasing is WRONG).
- **ISOLATION (s254)**: if a fire is live (`ps` for 'bash -l' + `gh pr list` + `git status`), use `git worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A` - stage explicit paths.
- **THE PICK: pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE. ANSWERED: M227-M340,M344,M346 + B1-B31 (M241 FAIL 2/5 #180).
  CLOSED enumeration (M220..M308, what each settled, incl. the M308 SITE-list shapes) VERBATIM at
  `docs/pick-archive.md` §trim-s270.
  NEVER bp mid-instruction (s213). NAMED cap: see §BUDGET's DOC CAP line.
  CLOSED pick rows + open-lead census (v..x4, B27) VERBATIM at `docs/pick-archive.md` §trim-s313-chain1
  region-A (sha1 `8332dd50ba16`, `scripts/m333_nextprompt_trim.py --verify`); per-id `NAMED ## <id>` GOVERN.
  **NO STATIC PICKS LEFT** except **(ix)** (live-box, operator-GATED), so the analysis-only
  option is this OPEN-LEADS
  list, each with a NAMED question: (x1) ANSWERED by M333 — slot noun = a facility the base HAS
  (base+0x8c bit), bit5 of block+0 = a CARRIED HALF-UNIT exclusive to FUN_004f47f0;
    (x6) OPEN: other writers of the 0x92bde8..0x92bf14 pref block; (x9) CLOSED by M342+M344+M346: no API caller completes
  production (inline `or` @`0x4f0ec0`) and the ALERT is the same block's 2 posts into the
  10-slot text bank (`## M346`; `0x985b10` REFUTED) and (M348) consumed by Script.txt `#PRODUCEXQ/G`;
  FUN_00636b1e = Create Session dialog (not a drainer); OPEN = writers of 0x999fa4; (x7) ANSWERED by M334 — the REMOVAL path is the difficulty-gated AUTO-SELL
  (ENERGY ASSIGNED, not refunded; `ds:0x985ba0`'s WRITER outside .text is still OPEN);
  (x8) ANSWERED by M337 — the item table IS the +0x10 field of the 72-record array at `0x984d38`,
  row order = alpha `#FACILITIES` file order; B28's +300 parity covers ids 1..38 by construction.
  Lists live in NAMED ## M310-M350. READER LAWS still BIND:
  every kickoff + skill `instrument-laws.md` + §CHAIN-PICKS.

## LIVE FACTS / KIT

- **BOX**: state UP, last touch s258 (TracerPid 0, yama=0; pid via `pgrep -x terran.exe`,
  never hardcoded) —
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
Results: `docs/pick-archive.md` §trim-s313-chain1 region-B (sha1 `6f2ddbe32478`); per-id `NAMED ## <id>` GOVERN.
- M348 (s326) MERGED: slots 1/2 -> Script.txt `#PRODUCEXQ/G`; M346 `drainer` RETRACTED (Create Session dialog). 12/12 `a3d46c017673526a`, harness 13/13. NEXT: writers of 0x999fa4.
- B32 (s327) MERGED: the UNIT leg on the recorded trace - 4/4 unit heads stamp the M349 mapper bit, facility-range 0/2, post-pop head 0/6. 10/10 `e6875c63c8c2f911`, harness 13/13 `155781675e5086a1`. NEXT BUILD B33 = the facility leg's branch to the shared OR.
- M334-M340: upkeep AUTO-SELL, #DIFF ladder, PLAYER RECORD 1 difficulty byte, item order, the last #DIFF readers, the modal screen runner, pref>=6 - per-id rows + digests in `NAMED ## M334`-`## M340`.
- M339 MERGED: 0x5f1394 = the modal SCREEN RUNNER; return = the screen obj's +0xa40 cell; FUN_004ddaa0 writes it to ds:0x985aec + 8 faction blocks. 7/7 d76a5e83770b77bb, harness 13/13.
- M345 (s324-chain2): dialog `+0x64` slot has NO .text dispatcher (5 slot dwords, 0 refs, 37 sites); 12/12 `833faf38e189ad40`, harness 11/11
- M347 (s324-chain2): HoF page writer = the +0x5970 child selector, ids 1..7 (page bound 7); 12/12 `3fadfd6e6d26e64c`, 20/20
- M349 (s326-chain2) MERGED: M68/M69 `NEG_TYPE` ANSWERED — a negative queue head is the NEGATED UNIT TYPE (`neg` @0x4ef89f; `>=0` = facility id, `-38` = sentinel, id<0x40 stamps, `>=0x40` gated by 0x98adb8 bit2, one 0x95da9c+304*p bitmap); 13/13 `4d3c2e4ded19d620`, harness 18/18
- M350 (s327-c3): pref END 0x92bf34; loader = sole init; co-writes = commits. 6/6 `23794d22`, 15/15.
- M352 (s328-c3): `ds:0x6710fc`=WritePrivateProfileStringA; 13 keys, 12 cell-backed+stamp; Laptop/Language read-only; `0x6926ec` literal; M350 OPEN closed. 7/7 `d553194a` 13/13.
