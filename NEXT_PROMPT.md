# NEXT_PROMPT.md - footing (B36 s337 `b20f5818dee2d861`; M373 s338 `162f8833a8a831f0`. STATE: B1-B36 + M54A-M373; (ix) box-GATED; (x) OPEN-LEADS; #180 pre-existing FAIL.)
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
box/`/proc`/gdb time; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B36 MERGED** (per-rung cmds `NAMED` §CHAIN-BUILDS; `## B34`-`## B36` govern).
**B37**: `track_mode.py` decides; author the rung in `BUILD_SPINE.md` BEFORE probing.
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
- **THE PICK: pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE. ANSWERED: M227-M340,M344,M346 + B1-B35 (M241 FAIL 2/5 #180).
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
- M348 (s326) MERGED: slots 1/2 <- Script.txt `#PRODUCEXQ/G`; M346 `drainer` RETRACTED. 12/12 `a3d46c017673526a`.
- B34 (s333) MERGED: a facility completion stamps NOTHING (21 stores: API 2/GRANT 11/SET 1/COPY 6; 6/6 unchanged). 10/10 `5296fdad6d26caa3`.

- M361 (s333-c2) / M364 (s334-c2): A/V radio flags = widget+0xa18 of 4 rows (readers 0x493ec0/0x492940/0x492030/0x4930e0), 38/38; relations nouns 0x1/0x8 (the 0x8 reading RETRACTED by M369), 24/24. Rows in NAMED.
- M365 (s334-c3): 0x94d5dc = relations-record slot block+0x1ac (23 sites, 8W/15R); 0x94d5bc pairs 5/5. 22/22 `d1d567339ee8c5b2`, harness 26/26. Row in NAMED.
- B35 (s335): WHO calls the grant family - 3 sites into the founder (FUN_004cca50/FUN_0059ce10/FUN_0059ec90), 1 into the new-game setup (FUN_005a0fa0); the record EXISTENCE, not the bit value, separates them. 11/11 `fa541d0a2445cacf`, harness 18/18.
- M368 (s336-chain1): 0x2 = TREATY, 0x4 = TRUCE — behaviour keys `ENEMYTRUCE`/`ENEMYTREATY` on the mask writes; truce<treaty<pact (pact IMPLIES treaty); FUN_005076d0's classifier is ordered EQUALITY. 34/34 `6f4b692777cc3549`, harness 32/32. NEXT: the two other peace hosts (0x53fcb3 / 0x523f4c).
- M367 (s335-c3): the 13 labels = `labels.txt` lines; 1/2/4/0x10 = Pact/Treaty/Truce/Vendetta, 8 = Commlink (bit 8's noun SETTLED by M369). 27/27 `a48d5dd630542166`, harness 30/30.
- M366 (s335-chain2): 0x10 = AT WAR/vendetta in force (V: the declare path FUN_00507ce0->FUN_005076d0 writes 0x10 on both exits, fires VENDETTAWARNING/INCITED; its set-rule clears 1|2|4); 0x20 = the human-branch war record (INF). 26/26. NEXT: 0x20's noun.
- M369 (s336-chain2): relations bit 0x8 = COMMLINK (contact), M364's AT WAR RETRACTED — the vendetta block only TESTS 8 both ways as a guard; the war bit is 0x10; the pod (rel&8==0) and the council sweep set 8 alone. 23/23 `475fdceda961ef2d`, harness 39/39. NEXT: 0x2/0x4 (chain 1).
- M370 (s336-c3) MERGED: pref block 0x92bde8..0x92bf14 = 11 cells/43 stores/14 fns; two-sided INI names; 32 non-loader writers mirror 0x985a**; sweep 0x92bf18..0x92bf30. 16/16, harness 22/22.

- B36 (s337-chain1) MERGED: FUN_00551a20 EXTRACTED AND RUN - 5 `test bl` blocks on the CURRENT ebx + an UNCONDITIONAL tail OR; pact=0x3, truce-after-war=0x8000010c, war=0x80000118, combined 0x11=0x8000011b; the ladder ACCUMULATES so the state is the classifier's precedence (1>2>4 EQUALITY). 10/10 `b20f5818dee2d861`, harness 11/11. NEXT BUILD B37.
- M371 (s337-chain2): the war-initiation hosts' 0x8 = COMMLINK — `or ebx,0x80000108`@0x551b11 puts contact into every 0x10 request (16 war-alone vs 4 pure-contact callers, peace keeps 8). 18/18 `4e82206112fe63ad`, harness 27/27, twice-byte-identical. NEXT: 0x88000008 bits 27/31.
- M373 (s338-chain1) MERGED: the PENDING-VENDETTA consumer — FUN_005551e0 clears 0x80000000 both ways (0x555750/0x55578a) ONLY when bit 13 (0x2000) is clear; the skip path scrubs bit 13 (`and ah,0xdf`@0x555809) = a one-shot protector. **bit 27 does NOT gate the pass** (0 sites) — sticky, set only by 0x88000008, read by 4 other fns. Second clearer: caller-mask erasers FUN_005518f0/FUN_00551cf0; only `0x9000ff48`@0x59f176 carries bit 31 (OPEN: 0xdd9bc3c0@0x4da404 flag). 19/19 `162f8833a8a831f0`, harness 16/16. NEXT: bit 13's noun.
- M372 (s337-c3) MERGED: 0x92bf0c = BIT-STRING slot, not packed: the flag=1 writer emits base-2 (min width 8) == the shipped `Semaphore=00000000`; all 4 in-game stores `x&0x1800000` (bits stay 23/24); the name is the INI key only; bit23 read 0x59ef11+0x5a1446, bit24 0x5a1150; 0x92bdf0 unreachable (0 address dwords). 8/8 `b699a30c05573575`, harness 20/20. NEXT: the nouns of those two bits (0x99aa38 bits 16/17).
