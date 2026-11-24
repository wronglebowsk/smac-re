# NEXT_PROMPT.md - footing (B30 MERGED s321: 6/6 print `f26ad69d86d0a319`, harness 10/10 `18aac65a6ac028f4`; old header/CLOSED-enumeration/traps VERBATIM at `docs/nextprompt-archive-m299-b20.md` + `docs/pick-archive.md`. STATE: B1-B30 + M54A-M340 (`NAMED ## B30`, `## M340`); only (ix) left, box-GATED; (x) OPEN-LEADS is the analysis-only option; #180 pre-existing.)
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
box/`/proc`/gdb time; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B30 MERGED** (B26 #328, B27 #344, B28 #351, B29 #356, B30 s321; per-rung cmds `NAMED`
§CHAIN-BUILDS, `## B25`-`## B30` govern; B26's ACCEPT+LAW at `docs/pick-archive.md` §trim-s308-chain1 (a)).
**B30 = the COMPLETION leg** (`## B30`). **Next build B31**: the spine ends at B30 - author its rung
text in `BUILD_SPINE.md` BEFORE probing.

  **DOC CAP (`wc -c` s321): `NAMED.md` 246,098/250,000 = 3,902 B - under the 5 KB trigger: the next fire ROTATES first (M310 VERBATIM to `docs/named-archive-b30-rows.md:5`, sha1 `ca3caf3785c9d6e9`, `scripts/b30_named_rotate.py --verify`). NEXT_PROMPT <=12,000.**

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
- **ISOLATION (s254)**: successor ALWAYS "in 12m"; at fire start check `ps`
  for a live 'bash -l' + `gh pr list` + `git status`; if live, `git
  worktree add ~/reverse/wt-s<N> -b milestone/<id> origin/main` and work ONLY
  there (`ln -sfn ~/reverse/smac/scratch scratch`); NEVER `git add -A` - stage explicit paths.
- **THE PICK: pick from the OPEN shortlist below** (collision check FIRST per ISOLATION). track_mode is AUTHORITATIVE. ANSWERED: M227-M340 + B1-B30 (M241 FAIL 2/5 #180).
  CLOSED enumeration (M220..M308, what each settled, incl. the M308 SITE-list shapes) VERBATIM at
  `docs/pick-archive.md` §trim-s270.
  NEVER bp mid-instruction (s213). NAMED cap: see §BUDGET's DOC CAP line.
  CLOSED pick rows + open-lead census (v..x4, B27) VERBATIM at `docs/pick-archive.md` §trim-s313-chain1
  region-A (sha1 `8332dd50ba16`, `scripts/m333_nextprompt_trim.py --verify`); per-id `NAMED ## <id>` GOVERN.
  **NO STATIC PICKS LEFT** except **(ix)** (live-box, operator-GATED), so the analysis-only
  option is this OPEN-LEADS
  list, each with a NAMED question: (x1) ANSWERED by M333 — slot noun = a facility the base HAS
  (base+0x8c bit), bit5 of block+0 = a CARRIED HALF-UNIT exclusive to FUN_004f47f0;
  (x5) the 'multi' label only (`92bdf8` = pref `Top Menu`);
  (x6) ANSWERED by M335/M336/M340, M339 closed the callee; OPEN: other writers of the
  0x92bde8..0x92bf14 pref block; (x9) the completion SETTER routine (B30's ASSUMED inverse); (x7) ANSWERED by M334 — the REMOVAL path is the difficulty-gated AUTO-SELL
  (ENERGY ASSIGNED, not refunded; `ds:0x985ba0`'s WRITER outside .text is still OPEN);
  (x8) ANSWERED by M337 — the item table IS the +0x10 field of the 72-record array at `0x984d38`,
  row order = alpha `#FACILITIES` file order; B28's +300 parity covers ids 1..38 by construction.
  Lists live in NAMED ## M310-M337 + `## B<n>`. READER LAWS still BIND:
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
Result one-liners M320/M323/M324/M325/M326/M330/M331 + the M330 #340 sidecar note:
`docs/pick-archive.md` §trim-s313-chain1 region-B (sha1 `6f2ddbe32478`, `--verify`); the per-id
`NAMED ## <id>` blocks GOVERN.
M334 (s316-chain2, MERGED fc2569d #350): 0x4f47f0 upkeep-FAILURE = difficulty-gated AUTO-SELL (ENERGY ASSIGNED, not refunded; block+0x8 = effective difficulty) — 7/7 5b5ece39af02baba, harness 45/45 a5a5091e533f7883. NAMED ## M334.
M337 (s318-chain1, x8): item row order = alpha `#FACILITIES` file order (rec i = alpha i-1) — 8/8 `39d82f0771690e15`, 13/13; M53i's +0x20/+0x28 labels superseded. NAMED ## M337.
M335 (s317-chain2): ladder = alpha #DIFF 6 rows @0x94d2ac, indexed by ds:0x985aec; 4=Thinker 5=Transcend; only clamp FUN_00423af0(0,6) is INCLUSIVE. 7/7 fb58bdc3307d6258; 20/20 6e0e05a8ffb388d8. NAMED ## M335.
M336 (s318-chain2): ds:0x8f0090 = DIFFICULTY byte of PLAYER RECORD 1 (8 recs, stride 0x176, frame 0x8eff18); ONE unclamped reader 0x486788 (idx 0x176*(k+1)) so index 6 reads 0x94d2c4 (one past); 6 writers in 3 address forms. 7/7 f4ca00c55c833539; 14/14 3ec4dd172c69e165. NAMED ## M336.
M338 (s319-chain2): last two #DIFF readers — 0x57c606 = loop counter 0..5; 0x44a1c8 = BYTE[HoF rec +0x20] = faction block +8 (effective difficulty); UNCLAMPED. 8/8 1ae1563d47d0039e x2; 16/16 56455db0eadbedd7. NAMED ## M338 (M326 rotated, sha1 a882ee40851d).
M340 (s320-chain1): FUN_0058e7f0 ADMITS a `Difficulty` pref >=6 — no numeric bound in read->parse->store (constants {0,1,0x2b,0x2c,0x2d,0x30,0x31,0x36}); Language IS bounded (cmp 4/ja) = positive control. 7/7 1cc44d0146a8b419; 12/12 a2a1726721114b4d. NAMED ## M340.
- M339 (s320-chain2) MERGED: 0x5f1394 = the modal SCREEN RUNNER; return = the screen object's +0xa40 cell (read once, written 0x), and FUN_004ddaa0 writes it to ds:0x985aec + all 8 faction blocks. 7/7 d76a5e83770b77bb x2, harness 13/13 927a1c66c322709e; (x6) callee CLOSED.
