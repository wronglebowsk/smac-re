# NEXT_PROMPT.md - footing (B33 MERGED s330 `8cb969b` (`b89b9e6bd940e8d3`); M355 MERGED s329-c3. Old header/enumerations/traps VERBATIM at `docs/nextprompt-archive-m299-b20.md` + `docs/pick-archive.md`. STATE: B1-B33 + M54A-M355; only (ix) left, box-GATED; (x) OPEN-LEADS is the analysis-only option; #180 pre-existing FAIL.)
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
box/`/proc`/gdb time; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B33 MERGED** (per-rung cmds `NAMED` §CHAIN-BUILDS; `## B30`-`## B33` govern).
**B33 MERGED = the FACILITY leg WALKED** (`sim/facilityleg.py`: the OR `0x4f0ec0` is unit-only -
its block's only door is `0x4f0b80 jg` on `[ebp-0x30]`, written at one site, the unit branch's
`0x4ef8a4`; facility heads spend at `0x4efed8` and never stamp - `## B33`). **Next build B34**:
author its rung text in `BUILD_SPINE.md` BEFORE probing - whether a facility completion stamps
`+0x8c` ANYWHERE: the other OR sites `0x4f3ebc`/`0x4f3f4c` and the 52-byte `0x98adb8 + 0x34*i` row.

  **DOC CAP (s330): NAMED 244,109/250,000; M333 rotated VERBATIM.**

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
  CLOSED enumeration + pick rows + open-lead census (v..x4, B27) VERBATIM at `docs/pick-archive.md`
  §trim-s270 / §trim-s313-chain1 region-A (sha1 `8332dd50ba16`, `scripts/m333_nextprompt_trim.py --verify`).
  NEVER bp mid-instruction (s213).
  **NO STATIC PICKS LEFT** except **(ix)** (box-GATED); the analysis-only option is this OPEN-LEADS
  list, each with a NAMED question: (x1) ANSWERED by M333 (rotated VERBATIM to
  `docs/named-archive-b33-rows.md`);
    (x6) OPEN: other writers of the 0x92bde8..0x92bf14 pref block; (x9) CLOSED M342+M344+M346+M348
  (alert = Script.txt `#PRODUCEXQ/G`; `0x985b10` REFUTED; FUN_00636b1e = Create Session dialog);
  ~~writers of 0x999fa4~~ ANSWERED M353 - filler `FUN_00626581` (260 sites, k<=9), consumers
  `$NUMBER`/`$NUM`/`$HEX` (`itoa(v,10)`) + UNBOUNDED `$#k`; (x7) ANSWERED by M334 - the REMOVAL
  path is the difficulty-gated AUTO-SELL (ENERGY ASSIGNED; `ds:0x985ba0`'s WRITER still OPEN);
  (x8) ANSWERED by M337 - the item table IS `0x984d38`'s +0x10, row order = `#FACILITIES`.
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
- M348 (s326) MERGED: slots 1/2 -> Script.txt `#PRODUCEXQ/G`; M346 `drainer` RETRACTED (Create Session dialog). 12/12 `a3d46c017673526a`, harness 13/13.
- M353 (s329) MERGED: `0x999fa4` = 10-dword band; filler `FUN_00626581` (k>9 -> ret 3), consumers `$NUMBER`/`$NUM`/`$HEX` (base 10) + `$#k` (no bound). 11/11 `367fdae1d78979e5`, harness 11/11. NEXT: (x6) pref-block writers.
- B33 (s330) MERGED: the facility leg WALKED - the OR `0x4f0ec0` is unit-only (door `0x4f0b80 jg` on `[ebp-0x30]` = the unit branch's `0x4ef8a4`); recorded 4/4 unit stamps, 0/2 facility. 12/12 `b89b9e6bd940e8d3`, harness 11/11. NEXT BUILD B34 = where a facility stamps `+0x8c`.
- M334-M340 + M339 MERGED: upkeep AUTO-SELL, #DIFF ladder, PLAYER RECORD 1 difficulty, item order, the modal SCREEN RUNNER (0x5f1394, `+0xa40` cell), pref>=6 - rows in `NAMED ## M334`-`## M340`.
- M349 (s326-c2) MERGED: a negative queue head is the NEGATED UNIT TYPE (`neg` @0x4ef89f; `>=0` facility, `-38` sentinel, `>=0x40` gated by 0x98adb8 bit2); 13/13 `4d3c2e4ded19d620`, 18/18
- M351 (s328-chain2): the negative head's producer = the chooser row ITEM, negated when flags&0x20==0; unit rows' item = the TYPE ORDINAL (0x984d38+0x30*i) stored to base+0x50 @0x418b57. 15/15 `504c7342fb16273b`, harness 20/20.
- M352 (s328-c3): `ds:0x6710fc`=WritePrivateProfileStringA; 13 keys, 12 cell-backed+stamp; Laptop/Language read-only; `0x6926ec` literal; M350 OPEN closed. 7/7 `d553194a` 13/13.
- M354 (s329-chain2): section A's item IS the 0x98ad88 unit-type/design row (name +0x00, weight +0x29, class +0x2a read off the item); A rows +, B rows -; M349/M351 leg NOUNS swapped. 11/11 `dd5e689e8d9af320`, harness 23/24.
- M355 (s329-c3): `Laptop` = the DEFAULT bit-vectors of `Preferences` (0xbbe1dd96/0xa3e1dd16 -> 0x92befc) / `More Preferences` (0x3a7168/0x327168 -> 0x92bf00); Laptop!=0 clears {7,27,28}/{19}. 7/7 `c742bc13`, 24/24. NEXT: bit->option labels.
- M357 (s330-c3): pref checkbox LABELS — 6 Script.txt sections -> 66 rows (id->cell bit, 1:1); Laptop delta = movies/interludes/SFX/monuments. 18/18 `095258c8b40d0e23`, harness 23/23.
