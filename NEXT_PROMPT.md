# NEXT_PROMPT.md - footing (B34 s333 `5296fdad`; M363 s334 `66b923f06f4e8866`; B35 s335 `fa541d0a2445cacf`. STATE: B1-B35 + M54A-M368; only (ix) left, box-GATED; (x) OPEN-LEADS is the analysis-only option; #180 pre-existing FAIL.)
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
box/`/proc`/gdb time; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B35 MERGED** (per-rung cmds `NAMED` §CHAIN-BUILDS; `## B30`-`## B34` govern).
**B36**: `track_mode.py` decides; the spine now ends at B35 (who calls the grant family). Author the
next rung in `BUILD_SPINE.md` BEFORE probing. **DOC CAP: NAMED 247,373/250,000.**

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
- B33 (s330) MERGED: the facility leg WALKED - the OR `0x4f0ec0` is unit-only (door `0x4f0b80 jg` on `[ebp-0x30]` = the unit branch's `0x4ef8a4`); 12/12 `b89b9e6bd940e8d3`, harness 11/11. NEXT BUILD B34 = where a facility stamps `+0x8c`.
- M358 (s332) MERGED: `0x98ad88` = 52 B (name[0x20], dword +0x20, bytes +0x24..2e, word +0x30, word +0x32); `0x9267e4` = 128 dwords, NOT 64-byte rows. 10/10 `1af1dcb6fcd4a4b6`, harness 15/16.
- B34 (s333) MERGED: a facility completion stamps NOTHING (21 stores: API 2/GRANT 11/SET 1/COPY 6; 6/6 unchanged). 10/10 `5296fdad6d26caa3`.

- M359 (s332-chain2): +0x28 = CARRY CAPACITY (V, Mode 7=Transport gates it; TWO writers, M356 G14 retracted); +0x27 = reactor level (INF); +0x2a = PLAN (M354's "class" retracted). 14/14 `7d4a2d1356c9ff41`, harness 18/18. NEXT: #REACTORS=4 vs the 1..3 clamp.
- M362 (s333-c3): the 0x4db1xx sibling = the FACTION RELATIONS page; its +0x15a0 group = 13 checkboxes whose ids ARE the bits (11 from 0x94d448, 2 from 0x94d468 = slot +8; 0x80000000 selects it). 6 writers, 4 symmetric. 20/20 `3b30baa33ea67fcb`, harness 19/19. NEXT: the 13 label strings (0x997b20 heap); bit nouns.
- M361 (s333-c2): A/V radio flags = widget+0xa18 of 4 rows (0x12cbc+k*0xb4c); readers 0x493ec0/0x492940/0x492030/0x4930e0; relabel ends in generic 0x5fa1e8; master never commits; propagation both ways. 38/38 `b92f1a61c041ae87`, harness 30/30. NEXT: what 0x4b87f0/0x4b8820/0x4b8a60/0x4b8af0 toggle.
- M364 (s334-chain2): the relations bits have NOUNS — 0x1 = PACT, 0x8 = AT WAR (V: the end-pact and declare-vendetta case blocks ask those masks); the other 11 INF. 24/24 `f6d006d0281ac189`, harness 23/23. NEXT: 0x10 (37 asks, co-sets 0x8000|0x40) and 0x20 (18 asks, clears dword B's 0xc00).
- M365 (s334-c3): 0x94d5dc = relations-record slot block+0x1ac (23 sites, 8W/15R): only 0 stored, 3 `++`, 1 `+=2*byte`; 0x94d5bc pairs 5/5; deadlines value+round/50+1, 4 cross-direction cmp. 22/22 `d1d567339ee8c5b2`, harness 26/26.
- B35 (s335): WHO calls the grant family - 3 sites into the founder (FUN_004cca50/FUN_0059ce10/FUN_0059ec90), 1 into the new-game setup (FUN_005a0fa0); 11 API grants `[6,3,7,27,8,4,6,3,6,3,27]` + 10 mapper grants `[1,3,6,7,3,6,7,26]`; births 3/3 founder vs 1/3 new-game; the record EXISTENCE, not the bit value, is the separator. 11/11 `fa541d0a2445cacf`, harness 18/18. NEXT BUILD B36.
- M368 (s336-chain1): 0x2 = TREATY, 0x4 = TRUCE — behaviour keys `ENEMYTRUCE`/`ENEMYTREATY` on the mask writes; truce<treaty<pact (pact IMPLIES treaty); FUN_005076d0's classifier is ordered EQUALITY. 34/34 `6f4b692777cc3549`, harness 32/32. NEXT: the two other peace hosts (0x53fcb3 / 0x523f4c).
- M367 (s335-c3): the 13 labels = `labels.txt` lines (element=off/4, line=10+element): 1/2/4/0x10 = Pact/Treaty/Truce/Vendetta, 8 = Commlink, 8 more stance strings, 2 high-dw; title `Diplomacy for`. 27/27 `a48d5dd630542166`, harness 30/30. NEXT: bit 8's noun (Commlink vs M364 AT WAR).
- M366 (s335-chain2): 0x10 = AT WAR/vendetta in force (V: the declare path FUN_00507ce0->FUN_005076d0 writes 0x10 on both exits, fires VENDETTAWARNING/INCITED; its set-rule clears 1|2|4); 0x20 = the human-branch war record (INF). 26/26 `bc58f707128a8b15`, harness 29/29. NEXT: the noun WORD for 0x20; role of 0x80000000.
- M369 (s336-chain2): relations bit 0x8 = COMMLINK (contact), M364's AT WAR RETRACTED — the vendetta block only TESTS 8 both ways as a guard; the war bit is 0x10; the pod (rel&8==0) and the council sweep set 8 alone. 23/23 `475fdceda961ef2d`, harness 39/39. NEXT: 0x2/0x4 (chain 1).
