

Older sessions: `docs/sessions/sessions-267-267.md` (1 sessions). Read it only when a question reaches back before session ## Session 268.

## Session 268 (2026-11-16, ANALYSE M308, zero box) - FUN_0056d480/0056d630 ARE the 25-entry SITE list of the 8380-B block record at 0x94f2d8 (inserter-with-eviction + pure probe); ds:0x985aec is a dword ENUM mirroring ds:0x92bde8; ds:0x985b10 is ONE byte bit-mask that one writer rebuilds as OR(1<<BYTE[rec]) over 412-B records
- MODE=ANALYSE (track_mode: analyse_since_build=0, last_build=B21, next_rung=B22) -> took the NEXT_PROMPT pick verbatim ("FUN_0056d480/0056d630 + ds:0x985b10/0x985aec identities", the OPEN row of M303/S9). Branch milestone/m308.
- ACCEPTANCE `python3 -u scripts/m308_site_list.py` -> **32/32 checks OK**, exit 0, `RESULT: PASS M308 site-list identities`; evidence/m308_site_list.txt 15,291 B (`:301-303`); rerun stdout-vs-evidence diff = **0 lines**. Zero box/proc/gdb.
- THE PAIR (`:76,95-96,101,104-113`): both index **0x94f2d8 + 8380*block** - the multiply chain evaluated symbolically from the mnemonics gives 8380 for BOTH (the C text `param_1 * 0x82f` is ELEMENT units; a 2095-B stride is REFUTED, A1-A3). 25 entries (cmp 0x19+jl, step 0x10) = {+0 short KIND, +2 short PRIORITY, +4 dword X, +8 dword Y}. 480 = insert-or-upgrade: (KIND,X,Y) hit -> stores **max(old,+2),param_3** (A9); miss -> scores all 25 as **1000 if KIND<0 (free) else 20-PRIORITY** (only when PRIORITY<param_3), STRICT jle keeps the first index, and **no candidate -> returns without inserting** (A10/A11); on insert writes all 4 fields then broadcasts via FUN_0056d350(b,kind,prio,x,y,-1). 630 = probe (b,kind,x,y)->0/1, **0 stores**, never reads +2 (A5b/A6/A7 - the same regex counts 7 stores in 480, 0 in 630, 2 in 690).
- THE NAME (`:177`): 480's guard `((x^y)&1) && (ds:0x985ae8 & 0x1000)` pushes **0x691508 = "Bad SITE"** read out of the PE -> the entries are SITEs; both guard `je` land on the body head 0x56d4b7, so it cannot suppress the insert (A14/A15). CALLERS (`:181-195`): exactly **12 + 3** sites, all attributed; 10/12 show a contiguous 5-push run (2 split theirs - printed, not assumed, A18b); KIND constants **{0x0,0x3,0x8}** (probes {0x3,0x8}) REFUTE "kind is the constant 3" (A18c); sibling 0x56d690 carries counters **{25,75}** while 480/630 never mention 0x4b -> the 75-entry list at 0x94ee28 is a DIFFERENT list (A13).
- GLOBALS (`:198-232`): 0x985b10 = 544 refs (mov 445/test 96/push 2/add 1), **0 array forms** -> one byte, not a faction array; 12 byte stores, **0 or/and on it** (accumulation happens in a register); 95 `test BYTE ..,<reg8>`. Its rebuild writer 0x57f04c-0x57f071: store 0, loop `movsx ecx,BYTE[eax] / shl dl,cl / or bl,dl` over **stride 0x19c from 0x91e494**, store bl (A21-A24). 0x985aec = 68 refs (mov 44/cmp 24), **0 arithmetic** -> not a counter; only compared with **{1,2,3,4}**; 4 writers, 2 provably mirror **ds:0x92bde8** (0x57c7b0+0x57c7b5 store one eax to both; 0x57c5af loads it), 0x57f006 loads **BYTE ds:0x8f0c11** via movsx (A25-A28).
- IN-PLACE EDITS: M303's S9 OPEN row closed for the pair + both shapes; M303's "callee semantics OPEN" row now points to ## M308. M96's "human-mask" for 0x985b10 is not contradicted but bounded: the bit index is a runtime value (1<<block/1<<row at the M303 dispatch) -> "per-faction" stays INFERRED.
- UNKNOWN: U1 what a SITE IS in game terms (kind 0/3/8 unnamed); U2 who writes the -1 free-slot sentinel (0 writers of +0=-1 among the 17 refs to the window -> a bulk init outside it); U3 which index owns each of the 95 mask tests; U4 which option 0x985aec encodes; U5 save-carry vs rebuild of the site list (M303's question); U6 live (zero box).
- PITFALL (twice, own defects): a `^mov ` regex applied to the OPERANDS field (the mnemonic is a separate field) reported 0 stores for all three functions and made the "pure probe" gate VACUOUS - caught by re-reading the printed table; and `dis.py LO HI` wants hex, so a bash `$((0x..+8))` (decimal) argument silently widened the window. Gates now carry their own counts (A4/A6/A20/A25) so a blind census cannot pass.

## Session 269 (2026-11-16, ANALYSE M308 review round, zero box) - PR #281's four P2s were all correct; the repaired gates are now MEASURED load-bearing (8/8 mutations redden their checks, 36/36), and the 75-entry sibling is adjacent to the site list, not an overflow of it

- WHAT THIS FIRE IS: the review round of the PR #281 that s268 left unmerged because Greptile found
  4 P2s of one shape - an assertion that could PASS ON AN UNMEASURED STATE. All four fixed, none by
  weakening a check.
- ACCEPTANCE: `python3 -u scripts/m308_site_list.py` -> **36/36 checks OK, exit 0**, `evidence/
  m308_site_list.txt:316,318` (22,680 B); rerun stdout-vs-evidence `diff` = **0 lines**. Second
  acceptance `python3 -u scripts/m308_mutate.py` -> **`8/8 mutations reddened their target checks`,
  `RESULT: PASS M308 gates are load-bearing`**, `evidence/m308_mutate.txt`.
- P2a (classifier blind to `mov eax,ds:0x985ae8`): the operand classifier now matches direct
  `ds:`/`fs:` forms as well as bracketed ones. A4 RE-TRACKORED to the honest claim - the only
  out-of-frame, out-of-window memory in the pair is ONE named global READ, `ds:0x985ae8`, 0 stores
  to it (`:90,96`; 480 direct-globals=['0x985ae8'], 630=[]); A4b asserts stack, site AND global all
  classify non-empty in the same run, so a blind classifier cannot pass.
- P2b (bounds pre-filtered to the expected 0x19/0x4b/0x10): S3 is now BACK-EDGE detection (a jcc
  whose target is at or below itself) + an UNFILTERED immediate inventory of each function
  (`:100-111`). A12 fails unless 480/630 have exactly 2/1 back-edges with bound {0x19}, step {0x10}
  AND no cmp bound above 0x19 anywhere AND 0x4b absent from the whole inventory; A32 records that
  21 of 480's immediates (`0x3e8, 0x14, 0x18, 0x673850, 0xffffffff`...) are ones the old regexes
  DISCARDED, which is the proof the scan is really unfiltered.
- P2c (mnemonic presence in place of the rule): A9/A10/A11 read operands + BRANCH TARGETS. A9: the
  +2 short is movsx'd, that register is the cmp's LHS, the `jg` target == the instruction AFTER the
  `mov lhs,rhs` fallback (that is what makes it a max), the store-back is a WORD of the cmp's own
  register, and the cmp's RHS def-walks to `DWORD PTR [ebp+0x10]` (`:128-141`). A10: 1000 is an
  `and r,0x3e8` on the register the setge/dec wrote (the setge fed by the same-kind test), the free
  slot's `jl` skips the priority cmp, the 1000 arm's `jne` skips the `20-prio` sub, the strict guard
  is `jle` and its target is ONE PAST BOTH update stores (a tie therefore keeps the first index),
  and both priority operands def-walk to `movsx WORD PTR` of the same field (`:143-165`). A11: the
  `jl` lands on a store-free epilogue run and passes over exactly the 4 insert stores
  0x56d551/5b/61/6b (`:167-169`).
- P2d (mirror proved by instruction proximity): a real backward def-walk (`def_producer`/
  `def_globals`, sub-register aliases resolved: AL counts as EAX) over the stored register, bounded
  by the function span from ghidra_out/index.csv. 0x57c5af LOADS ds:0x92bde8 (3 instructions
  walked), 0x57c7b5 is a CO-STORE (the same eax stored to ds:0x92bde8 at 0x57c7b0, no write to eax
  between), 0x57f006 closes on `movsx eax,BYTE PTR ds:0x8f0c11` (`:260,265,275`), and 0x4ddcf1 is
  now DECLARED unattributed - the walk hits a call and the previous dumped insn is a `ret`, so the
  value arrives from outside the walk (`:253`, A28c). A28b is the anti-disguise gate: a walk-closed
  writer must resolve to ONE numeric global and the 10-insn window must name STRICTLY MORE
  candidates for every such writer.
- NEW FACT (was a RIVAL, now arithmetic): the 75-entry sibling at 0x94ee28 ends EXACTLY where the
  25-entry site list begins - 0x94ee28 + 75*0x10 == 0x94f2d8 - so the two are adjacent arrays of one
  8380-B block record (100 x 16 B), not one list overflowing (A13, `:293`). 690's two leas
  (0x94ee2a, 0x94f2dc) and its counter inits {25,75} are printed at `:108-111`.
- RETRACTION: NAMED ## M308's "2 provably mirror ds:0x92bde8" row said provably on proximity
  evidence; the proof is now the def-walk, and 1 of the 4 writers is provably NOT attributable in
  function. Row re-grounded in place, evidence cites refreshed to the new line numbers.
- PITFALL (own, found by the harness): 3 of my NEW sub-conditions were themselves decorative -
  mutating them reddened nothing, because I mutated a dict ENTRY that the assert then read as a
  whole. The fix was to mutate a MEASURED fact so it is false on the real bytes (e.g. compare the
  jg target off-by-one), which is what `m308_mutate.py` does. Keep mutation ids OUTSIDE the
  instrument's A-numbers (M1..M8 vs A1..A36) or the check-name parser confuses them.

## Session 270 (2026-11-16, docs cap split, zero box)

- NEXT_PROMPT.md was **11,922 B — 78 B from the 12,000 B warn cap**, so the CAP SPLIT ran BEFORE any
  milestone, per protocol. Moved the §THE PICK **CLOSED enumeration** (M220 .. M308, each with the
  NAMED section to read before re-opening it, and what it settled) + the OPEN-shortlist one-liner
  **VERBATIM** to docs/pick-archive.md §trim-s270. The move is byte-exact by construction: one python
  step sliced lines[64:80] (1,614 B), appended that exact string to pick-archive and wrote the file
  with the 4-line pointer in its place. Result: wc -c NEXT_PROMPT.md = **10,694 B** (1,306 B
  headroom), evidence.py budget -> ok.
- Nothing retracted, no claim moved: zero measurements in this PR, so NAMED.md is untouched and the
  gate warns "address registry: NAMED.md untouched (fine if no addresses changed)".
- PITFALL (own): scripts/gate.py refuses a docs-only PR with "[FAIL] milestone checkpoint:
  SESSION_NOTES.md has no new '## Session' section" — a cap split needs its own session section; the
  milestone that follows closes as Session 271.
- PITFALL (own): shell-quoting a markdown body inside printf breaks on backticks/parens. Append docs
  through a quoted heredoc into python, never through printf.

## Session 271 (2026-11-16, ANALYSE M309 + a cap split, zero box)

- Cap split first, its own PR #282 MERGED: NEXT_PROMPT.md was 11,922 B (78 B from the 12,000 warn
  cap); the CLOSED enumeration moved VERBATIM to pick-archive §trim-s270 -> 10,694 B.
- **M309 closes the s268 pick.** FUN_0056d350 (299 B, 50 callers) = **the GOAL-list insert-or-max**
  of the same 8380-B block record whose SITE list M308 named. `python3 -u scripts/m309_goal_sink.py`
  -> **54/54 checks OK**, exit 0, `RESULT: PASS ...` (evidence/m309_goal_sink.txt:278,280, 17,473 B);
  re-run stdout vs committed evidence: diff **0 lines**. `python3 -u scripts/m309_mutate.py` ->
  **9/9 mutations reddened their target checks**.
- The name is the binary's own: 0x56d350's parity guard pushes **0x6914fc = "Bad GOAL"**; FUN_0056d480
  pushes **0x691508 = "Bad SITE"** - 12 B apart in one .data pool (A28). Entry = {+0 short kind, +2
  short prio, +4 d, +8 d, +0C d owner} (A5); both walks bound **0x4b = 75** (A11); stride 8380
  re-derived (A3) plus a **second independent** `imul r,r,0x20bc` at 0x470d50, outside the function.
- **The -1 6th arg** = the entry's +0C owner. Among ALL **65** .text operands naming an address inside
  the 100-entry block, +0C has **1 writer (0x56d470) and 1 reader (0x559b3e)** (A36). The reader is
  signed, `test eax,eax / jl 0x559b74`, scaled 9x -> 19x -> <<4 = **x304** onto **0x95da40**, used as
  `test BYTE [edx+0x95da40],0x20` (A38-A40), gated on the same entry's +0 == 9 (A41). **-1 selects
  nothing - it is the unbound-owner sentinel**, and a duplicate call never refreshes it (found path
  stores ONE WORD, A13).
- Callers: 40/50 push 0xffffffff; 5 push a register the def-walk closes on **ds:0x68cbb0** (340 refs,
  exactly 6 stores, all 0x4e3000-0x4f6000, A42); **5 DECLARED unattributed** (push group crosses a
  branch/call) - printed, not hidden (A32/A33). Identity of ds:0x68cbb0 stays OPEN.
- **M308 U2 partly answered**: the GOAL list's -1 sentinel HAS a writer in .text - `mov WORD PTR
  [ecx+edx+0x94ee28], 0xffff` at **0x470d5c in FUN_00470b90** (1020 B, 5 callers). M308's "0 such
  writers" row patched in place: true for the SITE window, false for the GOAL window.- **P1 (Greptile #283, on the head commit, and it was RIGHT): `open(p,'w').write(open(p).read().
  replace(c,d))` truncates the file BEFORE the argument is evaluated - it wiped all 1,156 lines of
  NAMED.md.** Repaired in the same PR: `git checkout origin/main -- NAMED.md` (170,459 B), then the
  two M308 row patches and the `## M309` block re-applied from in-memory strings; `wc -c NAMED.md` =
  173,332 and `git diff --stat` now shows additions, not a deletion wave. Law: a checkpoint tool must
  read into a variable, then open for write; and `git diff --stat` against main is a required step
  before submit - the gate passed a whole-registry deletion because it only asks whether NAMED.md
  "was updated".

- PITFALL (own, caught by my own harness): `a1..a6 = [x[1] for x in ps]` on a list push_group returns
  CHRONOLOGICAL made "arg6" silently arg1 - the census printed 17 `esi`, zero constants; only M1 of
  m309_mutate caught it. And three new gates CRASHED instead of going red (a None in a print, an
  empty `band[0]`, list-vs-tuple dict compare): **a gate that dies is not a gate either.**

## Session 272 (2026-11-17, ANALYSE M310, zero box)

- `track_mode.py` -> `MODE=ANALYSE analyse_since_build=2 next_rung=B22`; took the s271 pick (b):
  FUN_00470b90. No cap split (NEXT_PROMPT 11,110 B). No sibling (no `bash -l`, empty processes.json,
  box not running) - zero box time, no /proc, no gdb.
- **M310 names FUN_00470b90 = the view object's debug-gated GOAL duplicate-invalidator + token
  logger.** `python3 -u scripts/m310_goal_invalidator.py` -> **PASS 32/32 checks OK**, exit 0, two
  runs byte-identical (table sha `801740e655c01d1a`, `evidence/m310_goal_invalidator.txt:159,160`);
  `python3 -u scripts/m310_mutate.py` -> **11/11 mutations reddened their target checks**
  (`evidence/m310_mutate.txt:13`).
- Entry gate: `this+0x1dd70 & 0x2000` (the view bit-flags field, M228-M245) - clear => `je 0x470f83`
  the single epilogue. Outer loop blocks 1..7 filtered by `(ds:0x985ae8 & 0x80) || (block ==
  ds:0x91b5b4)`; two 75-entry scans over the M309 GOAL list (15 `imul 0x20bc` : 15 `shl ...,0x4`).
- Hit = (p1,p2)==(+4,+8) && kind>=0 (skips the -1 free slot) && prio!=0. **prio<0 -> duplicate scan
  j!=i on the same pair AND same KIND (`cmp edx,eax`), and the 0xffff store's fold re-seeds from the
  OUTER index, so it invalidates entry i** (0x470d5c = M308 U2's GOAL sentinel writer). The store is
  followed by a RE-READ + `test/jge`: negative => next entry, non-negative => the log tail.
- Log tail: `FUN_00403a40(buf, unpacked pair, this+0x1ddb4, this+0x1ddb8)` + `FUN_00405220` token
  appends + `FUN_004237f0(|prio|)` (one `neg`) -> `FUN_004081b0(ds:0x997120, buf)`; block name under
  the 0x80 flag clears `BYTE ds:0x997121`. `kind == -1` is unsigned->0x29-above, so an invalidated
  entry NEVER logs.
- The kind->token map is a TWO-TABLE jump: the dword table @0x470f8c holds exactly 8 targets and
  the 42-BYTE index table @0x470fac maps kinds **0,2,3,6,8,9,41** to token blocks and
  **1,4,5,7,10..40** onto the same block 0x470eb7 that the `ja` default uses; tokens are ONE .rdata
  CHAR (0->'a', 2->'d', 3->'s', 6->'n', 8->'c', 9->'f', 41->'^').
- RETRACTION x2 (both MY overclaims, both caught by Greptile on #284, neither is a win over Ghidra):
  (1) "Ghidra's case list (0,2,3,6,8,9,0x29) is REFUTED" is FALSE - 0x29 IS 41, so the list AGREES
  with the bytes; the bytes add the STRUCTURE (42 selectors -> 8 handlers, 35 sharing the default
  that pushes nothing), they do not contradict the C. (2) "the C mis-parses the kind pair as i==i"
  is FALSE - I had not re-read the C; it says `local_10` vs `local_14`, exactly my law. Lesson:
  **never claim a refutation of a tool you can read - re-read it first; agreement is corroboration,
  and manufacturing a win is worse than having none.** The A10 gate itself was also weak in the same
  way Greptile says: it asserted two branch TARGETS while naming a whole predicate; it now pins
  mnemonic AND operand of all 19 instructions in the hit chain plus the branch skeleton (A24), and
  M12/M13/M14 mutate the engine's PARSED INSTRUCTION (not a literal) to prove it.
- Args: 5 call sites in one class cluster (FUN_00470fe0 x4, FUN_004715d0 x3, FUN_00471fd0 x1);
  0x4724bd forwards the 2 output slots of the 29-caller view unpacker FUN_0046a1b0; sites 2/3/4 the
  same `[ebp-0x10],[ebp-0x14]` loop pair; **0 global reads for the compared pair** (A12).
- OPEN: game meaning of a GOAL / of the tokens; WHY a GOAL has negative priority (the only trigger);
  what calls the 3 caller fns; identity of this+0x1ddb4/0x1ddb8; ds:0x68cbb0 and the 304-B table
  0x95da40 bit 0x20 still untouched (deliberate scope).
- PITFALL (own, cost ~8 iterations): a **hand-rolled probe**, not the engine, invented a missing
  instruction - `line.split(None,1)` mangles `movsx` (its bytes field is one column shorter, so the
  remainder starts with a space -> mnemonic parsed as '') and `endswith("0x10")` mis-matches
  `shl ecx,0x4`. Read operands through the engine (`M._INS`) and print `ascii(op)` before claiming
  an instruction is absent. Same class as a decoration: my jump-table "exact set equality" survived a
  `==`->`<=` mutation because the 13/5 counts + 0-overlap already carried the law - the harness found
  it, so it was replaced by a mutation that flips a measured fact (broadening the fold-classifier
  regex), which reddens A8.

## Session 273 (2026-11-17, BUILD, zero box) - B22: both save record arrays grown in ONE writer call, CREATE leg fed by the RELOADED base record
- THE PICK from `track_mode.py` (`MODE=BUILD next_rung=B22`); B22 was UNAUTHORED (no rung in
  `BUILD_SPINE.md`, no NAMED row, no commit) so this fire authored it, the way B14-B21 did.
- MEASURED, three claims of mine were FALSE before the bytes answered:
  1. the rung text asserted "the region `units_off`..EOF is the original lifted by ONE amount" -
     wrong: `savewriter.build_image` emits originals then grown bases and re-anchors the tail there,
     so only the tail lifts by the full 1572 B and the base originals lift by 52. The gate now
     compares FIVE bands (`unit originals 3484 | the ONE new unit 52 | base originals 5472 |
     the grown bases 1520 | tail 10800`), each against its own source.
  2. `r["new_recs"]` are 3-byte `(fac,x,y)` tuples, not 304-B records - a gate comparing them to
     image bytes could never pass. `basefound.record_bytes(led.records[-5+k])` is the right object.
  3. the header diff is 3 bytes, not 4 ("one per modeled field" was decoration; cur/tf already
     hold their recorded values in this save;
  4. and the loudest one, caught by GREPTILE (P1 on #286) rather than by my own gates: the G5 claim that
     the header counts and the shape scan "DISAGREE by exactly the unit growth". It came from applying
     image A's count arithmetic (`units_off + 52*(n_units+1)`) to image B's scan anchor. `sim/save`
     derives `units_off` FROM `bases_off`, so measured per-image (`bases_pred = units_pred + 52*n_units`)
     the two methods AGREE byte-for-byte and `closes` is True on orig/B21/B22. The gate now carries its
     own retraction in its printed text instead of the false claim.
- FOUND: `sim/save`'s shape locator CONFIRMS ONLY THE 18 NAMED bases of the grown container -
  M282's founders write an empty name span and `_base_ok` wants `[ -~]{3,30}\x00` at +19. A grown
  base is locatable by COUNT, never by SHAPE, and on a container that grew only ONE array the
  count position and the shape anchor DISAGREE by exactly that growth (226319 vs 226267).
- ACCEPTANCE: `python3 -m sim.selftest --b22 programs/saves/m54b_clean.SAV` -> **PASS B22: 11/11**;
  `python3 -u -m sim.composedgrowth` prints the same 11 labels; two runs byte-identical
  (digest a7ec6d38ba67cbe9, image sha256 f7d90eb77ca7abac); evidence file == fresh rerun.
- SELF-FOUND DEFECT, kept visible: `sim/composedgrowth.py` carried a STALE `acceptance()` draft
  BELOW the good one (truncating labels to 64 chars, printing the report itself, recomputing a
  third time). Python let the later `def` win, so `--b22` silently ran the shadowed version and
  the PASS line still read 11/11 - a green result from the wrong code path. Duplicate deleted.

- POST-REVIEW on #286 (1 P1 + 3 P2; all four accepted, none argued with):
  * G5 retracted as above (the P1). It is a repeat of s272's lesson in a new costume: a comparison built
    from two different objects, asserted as a property of one.
  * G9's falsifier (P2) re-read the corrupted image at its OWN call site, so a regression that made the
    real leg read the MODEL stayed green. Now: ONE shared producer `record_from_image(image, idx, head)`
    used by both the clean and the corrupted case; the perturbation covers tile AND faction; the gate
    asserts the created unit CARRIES the bad bytes (x/y span + owner byte), not merely that it differs.
  * NEW G12 (P2, my design) runs the MUTATION EXPERIMENT in-process every run: rebind the shared leg to
    read the model, restore in `finally`, and assert the mutant's SIGNATURE - G9's record collapses back
    onto G3's (the model's own (27,29) fac 1) while the real leg carries (1447,1448) fac 5A. G3 is
    DECLARED blind to it (the fixture's model tuple equals the container tuple), so the honest framing
    replaced a gate that could not fail. Acceptance is now **PASS B22: 12/12**, two runs byte-identical
    (report digest 06dd4ac599fd0..., written image sha256 f7d90eb77ca7abac unchanged).
  * NAMED citations (P2) were one line off after the evidence regenerated; the block was rewritten and a
    resolver now checks every cited line actually contains the gate label its row names - CITATIONS_RESOLVED.
  * A skill law I wrote THIS fire was false too: I claimed `milestone.py start` can branch from the
    worktree's stray tip. `cmd_start` does `git checkout main` + `git pull --ff-only` and only THEN
    `git checkout -b`, so it never can. Law rewritten: never assert a stray commit's fate either way
    without `git merge-base --is-ancestor` (its exit code, not my memory).
  * Process slip worth keeping: my docs-patch script aborted on a stale multi-line anchor (the `submit`
    step had re-wrapped SESSION_NOTES.md), and `git add -A && git commit` ran anyway - so commit b2b357d
    shipped corrected code with stale docs. Anchors that span wrapped prose must be matched by line
    number or single unique line, and a commit that follows a failed patch step is a FAILED step, not a
    clean one.
- LANDED: #286 merged as `3f645e1`; cursor handoff #287 merged as `138182c`. `track_mode.py` then reads
  `MODE=ANALYSE analyse_since_build=0 last_build=B22 next_rung=B23` - the flip lands on the fire right after
  a build merge, so the handoff must be written AFTER merging (my first cursor draft told the next fire to
  author B23, which is wrong: B23 is queued behind an ANALYSE fire). Law added to the loop template.
  Final B22 numbers to quote: **12/12 gates**, written image sha256 `f7d90eb77ca7abac`, five-band layout
  3484 + 52 + 5472 + 1520 + 10800 B, header diff 3 B (`0x44`, `0x48`, `0x54`).

## Session 274 (2026-11-17, STATIC, zero box) - M311: ds:0x68cbb0 is the CURRENT-RECORD INDEX; ds:0x8f0d60 its derived 304-B record pointer
- THE PICK from the s273 handoff, list item (a) `ds:0x68cbb0` (340 xrefs, exactly 6 stores). **It swallowed
  list item (b)**: the "304-B table at `0x95da40`" is `0x95da10 + 48` - the same array, one field in.
- `python3 -u scripts/m311_recidx.py` -> **PASS M311: 8/8 gates**, rc 0, two runs byte-identical,
  `census digest 625cd5877271cd85`; evidence `evidence/m311_recidx.txt`. (The FIRST green run this
  session was 7/7 at digest `dd0ddccb5a1bcad4`; gate **A8** and the matcher's operand clause came after
  the PR #289 review, so those numbers are superseded, not additional.)
- FINDINGS: 6 stores / 16 tests / 318 reads = 340 refs (the field IS compared, so no read-only-cursor story);
  the pointer `ds:0x8f0d60` has exactly 6 stores and pairs 1:1 with the index stores at +6..+25 B; the stride
  is the encoding's own `lea [n+n*8]` ; `lea [n+d*2]` ; `shl 0x4` = 304n over the base `0x95da10`; the setter
  `FUN_004e3470` is 34 B / 11 insns / 57 callers and does store-fold-store; `ds:0x68cbb4` (22 stores, only 3
  in-window) is a SEPARATE field and the pairing invariant is explicitly refused for it.
- FIVE DEFECTS OF MY OWN, all found before submission and all now skill law:
  1. mis-counted the pointer's stores as 5 (the census print scrolled past one) - transcription lists are CLAIMS;
     A2 now requires `sorted(transcribed) == sorted(cache-derived)`, and MU2 (delete one) reddens it;
  2. bad arithmetic - I first wrote the fold as n*9*16 = 144n; it is (n+(n+n*8)*2)<<4 = 304n;
  3. a fold matcher that required adjacency the compiler does not provide (pushes interleave at `0x4f5a85`);
  4. a gate sub-condition of the form `sorted(xs) == sorted(set(xs))` - I called that a tautology that can
     never fail; **review P2 on PR #289 corrected me** - it does reject duplicates, but it proves only
     uniqueness, never completeness or agreement with an independent source, so it guarded nothing here;
     replaced with claim-vs-containment; and MU11 proved the sibling defect: "57 callers" sat in the prose while
     the gate never read `n_callers`, so asserting 58 was inert until the gate read `index.csv`;
  5. a splice of mine deleted its own definition block and a `%`-format argument list drifted out of order -
     nested `%` inside a join is the failure mode; gate messages now build pre-computed strings.
- MUTATION HARNESS `scripts/m311_mutate.py`: baseline-green precondition, traceback mutants rejected, FAIL
  summary searched in stdout+stderr. First score **9/11** - MU2 was a dead anchor (a comment I had added moved
  the literal) and MU4 (relaxing the matcher's scan order) was genuinely WEAK. Fixed by adding a distance-cap
  mutant and a shift-width mutant and by PINNING the three fold triplets in A3 so attribution is falsifiable.
- M311 **MERGED**: PR #289, squash `17e3e2e` on `main` (gate 11 s; 3 Greptile P2s read and all three applied in-commit `2fe6f4a`; no re-review arrived on the second head, so merge.py's rollup verdict GREEN was the precondition - recorded honestly, not claimed as a review pass).

## Session 275 (2026-11-18, STATIC close-out of s274's M311, zero box) - PR #289 review round, clause audit, merge

Same working chain as Session 274 (the fire hit its iteration cap mid-M311, so the review round and the
merge land here rather than back-dating 274). M311 is now MERGED: `#289`, squash `17e3e2e` on `main`.

- FINAL ROUND (same session): instrument now **8/8 gates** (gate **A8** added: the matcher's per-site output is
  pinned as exact triplets, so a mis-transcribed address reddens it - MU4), digest `625cd5877271cd85`, and the
  harness scores **11/11 load-bearing** with the baseline-green precondition (`python3 -u scripts/m311_mutate.py`).
- NEW FINDING from A8: **5 of the 6 selection sites recompute `REC_BASE + 304n`; `0x4f5c36` does not** - it
  re-stores a SAVED pointer read from `[ebp-0x8]` at `0x4f5c33`. One selection path caches the record pointer.
- RETRACTED IN GATE A8 (my prose again, this time caught by a mutant that could not fail): the matcher's
  register-discipline and 24-B proximity clauses are **NOT load-bearing on this binary** - a register-blind
  matcher returns byte-identical results at all 6 sites across windows -24/+32, -24/+90, -24/+144 B. The
  "proximity" effect is purely the analysis window (at -24/+144 B the 0x4e3476 window also contains the next
  function's fold at 0x4e34cc). Claiming a mechanism is load-bearing without a mutant that can see it is the
  same decoration this repo has now punished four times.
- HARNESS HYGIENE, two more failure modes fixed: a mutant whose anchor drifts after a refactor silently
  becomes a NO-OP or a KeyError crash (`MATCH_TRUTH` looked up a deleted store site) - so gates must degrade
  with `.get(st, 0)` and report a wrong COUNT, never crash; and every anchor must be re-read from the current
  source, never quoted from memory.
- PR #289 GREPTILE, 3 P2s, ALL ACCEPTED, and one of them exposed that my *previous* fix was fake:
  1. **`fold_chain` accepted chains that do not compute 304n** - a chained `a != b != c` is not
     pairwise-disequality, and the first step never required its two operands to be the same register.
  2. My skill/notes said `sorted(xs) == sorted(set(xs))` "can never fail" - WRONG: it rejects duplicates.
     Corrected everywhere to "proves uniqueness only, never completeness or agreement with a source".
  3. **My A8 retraction had never been written.** The `str.replace` anchor spanned a `%`-format break in the
     middle of the literal, so it silently no-opped and the shipped evidence still printed the false claim
     ("both load-bearing"). Anchor edits on a contiguous literal, then VERIFY by grepping the artifact for the
     new words - a retraction that didn't land is worse than none, because it makes the doc look cleaned.
- THEN THE AUDIT ITSELF REDDENED, TWICE, ON MY OWN NEW CLAIMS. With the operand clause and the proximity cap
  switched OFF, `fold_chain` returns byte-identical results at all 6 sites over four window sizes: both clauses
  are INERT. And my first response to P2#1 - demanding the second `lea`'s base register equal the register that
  stored to the index - is FALSE at the setter and broke all six sites (the shape is `lea d,[n+n*8]`: OPERANDS
  equal, DESTINATION free). A8 now asserts the audit's actual content: only the window's right-hand reach is
  load-bearing (0x4e4dd0: 0 folds at -24/+32 B, 1 at -24/+90 B), the two inert clauses are declared inert with no
  mutants aimed at them, and the index operand's VALUE is declared UNPROVEN (register names are only a proxy for
  value identity without intervening-write tracking - which I declined to write).
- FINAL: **8/8 gates, 15/15 mutations load-bearing**, digest 625cd5877271cd85 (unchanged through every rewrite -
  the claims moved, the binary did not).
- **MERGED**: PR #289 -> `17e3e2e`. Gate 11 s. Greptile posted 3 P2s on the first head (`2fe6f4a` carries all
  three fixes); no re-review arrived on the second head, and `milestone.py merge` gated on its own rollup
  verdict (GREEN) - recorded honestly, NOT described as a second review pass.
- NEXT_PROMPT trimmed to 11,989 bytes and the retired s272 pick-list paragraph deleted (it duplicated the new
  OPEN PICKS block); SESSION_CURSOR rewritten for the next ANALYSE fire. `track_mode.py` after the merge reads
  `MODE=ANALYSE analyse_since_build=1 last_build=B22 next_rung=B23`, so the next fire ANALYSES; B23 stays QUEUED.

## Session 276 (2026-11-18, STATIC, zero box) - M312: the selection check has TWO trunks; every forwarder is unreachable; the pair is the CURSOR TILE sweep
- #105 (badge) verified live (page+svg 200) and squash-merged; #180 stands as documented-FAIL. `track_mode`: MODE=ANALYSE analyse_since_build=1 next_rung=B23 - ANALYSE fire, pick (i) taken.
- Acceptance `python3 -u scripts/m312_goal_callers.py` -> **== M312: 27/27 ==**, exit 0, two runs byte-identical, `digest 8751c5af18c5a8f8` (`evidence/m312_goal_callers.txt`); `python3 -u scripts/m312_mutate.py` -> **23/23 mutations reddened their target checks** (`evidence/m312_mutate.txt`). REVIEW ROUND (same branch): the first head (26/26, digest e25f77bb08585dfe, 17/17) drew 3 Greptile P2s on #292, all fixed at the second head - A9a was decorative (now 16 pinned instructions x 5 arms), the fan-out prose said 0..8 where the encoding visits **0..7** (bound 8 EXCLUSIVE), and A8b's "single store" is ENTRY ZERO only (entries 1..7 are the M262 pointer-arithmetic allocations, invisible to any address grep); new laws A5f (every x store = a 469010 result) + A5b extended to both y-laws.
- THE RETRACTION (A4): FUN_00470fe0 gates its invalidator tail on arg4 != 0 (`cmp [ebp+0x14] / je 0x47108b`) and ALL FOUR forwarder sites (0x47169A/6D6/802 inside 004715d0, 0x472151 inside 00471fd0) push literal `0x0` - so M310's "site 1" (0x471086) is UNREACHABLE from every caller in the binary; only the 4 direct sites fire FUN_00470b90 (all internally gated on `this+0x1dd70 & 0x2000`; 004715d0's three also pre-gated, `je 0x4719d3` at 0x47183e skips all three).
- TRUNK A (cursor): FUN_004736a0 (64 B, single callee, 15 dump call sites) pushes exactly `cursor_x_list[cursor], cursor_y_list[cursor], 2` (globals 0x91b5f0/0x91b670/0x91b5e8, NAMED ledger) -> FUN_004727c0 (valid-tile gate FUN_00469060) -> FUN_004725a0 (computes block `(ds:0x985ae8&0x80)?-1:ds:0x91b5b4` - M310's filter, same encoding) -> sweep FUN_004715d0: y = arg_y-3 (0x47166F/0x47185F), x in {arg_x-1, arg_x+1} clamped through FUN_00469010, every candidate gated FUN_00469060 != 0, the loop site additionally FUN_00422060 != 0 (0x4719b8). Fan-in also from FUN_00473760 (the M262 view table ds:0x7cdecc[0..7] - 8 entries, bound exclusive: element IS this, i != 0 requires element+0x1dd74 == 0; entry zero = the static main view 0x8f79e0 (the band's only direct store, 0x5803e1; entries 1..7 per M262)) and view-move FUN_00473d00 (kind=2, gated view+0x1dd8c bit 4).
- TRUNK B: the 5 hub arms (FUN_00472810, 53 sites / 28 owner functions) pass (block, param<0) into FUN_00471fd0 - NOT a coordinate pair; 00471fd0's invalidator call consumes the view-unpacker outputs (M310 site 5, unchanged).
- KICKOFF-CORRECTION: 0x4725e9 sits in FUN_004725a0 (544 B), not in FUN_00471fd0.

## Session 277 (2026-11-18, STATIC close-out of s276's M312, zero box) - PR #292 merged; the review round stands as the correction record
- `milestone.py merge 292` -> verdict GREEN, `merged #292; main is up to date` (main ec63d7a). CI `gate` pass 16 s on the review head (1b79181); no re-review arrived on the second head (one review per PR, on OPEN) - recorded honestly, NOT a second review pass.
- All 3 Greptile P2s were accepted and fixed at head 1b79181 BEFORE merging (full accounting in the single PR comment https://github.com/wronglebowsk/smac-re/pull/292#issuecomment-6966204794): the A9a arm check was decorative (now 16 literal-pinned instructions x 5 arms, MU16/24/25), my fan-out prose claimed 0..8 where the encoding visits 0..7 (bound exclusive - MU14), and A8b overstated scope (entry-zero census only; entries 1..7 belong to ## M262-M264 pointer-arithmetic - MU15/23). New laws: A5f, extended A5b.
- Final numbers: `python3 -u scripts/m312_goal_callers.py` -> == M312: 27/27 ==, digest 8751c5af18c5a8f8, two runs byte-identical; `python3 -u scripts/m312_mutate.py` -> 23/23.
- `track_mode.py` after the merge: MODE=ANALYSE analyse_since_build=2 last_build=B22 next_rung=B23 - the next fire ANALYSES. Pick (i') NAME THE EVENTS: which UI handlers reach FUN_004736a0's 15 call sites and FUN_00472810's 53 sites / 28 owners. The ds:0x7cdecc question is CLOSED by M262 - do not re-derive.

## Session 278 (2026-11-17/18, M313 - NAME THE EVENTS: pick (i') - the 15 thunk callers and 53 hub sites collapse onto ONE interaction band wired to TWO command pumps; pumpA's door is a data pointer at 0x6724a8 in a multi-table .text run from 0x672290 (post-review narrowing); pumpB's entry installed at startup as a callback)

- Pick (i') from NEXT_PROMPT. Static only, zero box. `scripts/milestone.py start M313` from main 7084e8c.
- RECONCILED-vs-summary: hub owners IN the band = 20 (I first eyeballed 16); pumpA carries 7 hub sites (I guessed 5) at 0x51319E/0x5137CF/0x51562D/0x51567D/0x5163D4/0x5164A5/0x51653A; pumpB 6 at 0x516C3E/0x516D03/0x5172F3/0x51753E/0x5175A9/0x5175FA. All from the byte census (m313_run1/2), never from memory - the digest caught two earlier hand-transcribed values (hub-site list, vtable digest placeholder).
- BAND LAW: 20 of the 28 hub owners AND 9 distinct owners of FUN_004736a0's 15 sites lie in [0x50bb20, 0x5175b4) - one interaction band, not two populations; the 8 off-band hub owners listed exactly in A3c (0x4738f0/960/9a0, 0x48e530, 0x4c40e0, 0x4cbc70, 0x4e10c0, 0x58b1b0).
- PUMPS (direction correction recorded in NAMED): FUN_00512b40 and FUN_00516b80 CALL INTO the band (12 and 10 exact members incl. hotkey_dispatch_cursor FUN_00511960 for pumpA), their own callers are exactly {FUN_0041bda0, FUN_004c5d60} and {FUN_005186b0}. PumpA = menu/toolbar command IDs (0x30041-0x3007a, 23-slot jump table @0x5165cc) + navigation VKs (RETURN 0xd/ESC 0x1b/PgUp 0x21/PgDn 0x22 + LEFT 0x25/RIGHT 0x27 (Greptile P2: 0x25/0x27 are LEFT/RIGHT, NOT END/HOME - 0x23/0x24); 17 table-jmps exact-censused. PumpB = letter order keys 'Q'-'Z' (13-slot table @0x5181d0) + extended bands 0x100s/0x200s/0x300s/0x900-0x912 (the latter -> FUN_004d44d0); 11 table-jmps.
- DISPATCH MECHANISM (pumpA): FUN_0041bda0 has zero static callers - it is slot 134 of a 490-slot vtable at 0x672290 (digest f2e2c9dfae9ba011); the SAME table's slot 415 is FUN_005f6aa3, the M284-M288 chooser row-click dispatcher - so pumpA is reached through the widget class's method dispatch, tying keyboard/menu commands to the same table that delivers mouse chooser clicks.
- MOUSE PROVENANCE: the M28-NAMED map_click_handler FUN_00476580 calls 5 band members directly ({04739a0, 050bde0, 050ca10, 050cab0, 050fb80}) - a mouse click on the map drives the goal-check machinery without either pump.
- PUMPB ENTRY: FUN_005186b0: zero call/jmp refs, exactly ONE stored u32 in the whole file - the imm32 at 0x51892e of `push 0x5186b0` (0x51892d) inside FUN_00518820, itself reached only from init FUN_00580260 -> startup callback installation (census VERIFIED, mechanism INFERRED).
- Acceptance `python3 -u scripts/m313_event_map.py` -> == M313: 19/19 ==, digest 3fee30fcd74735ad, x2 byte-identical (evidence/m313_event_map.txt). Harness `scripts/m313_mutate.py` -> **19/19** (harness bugs MU2 retarget + temp-dir + colon-regex fixed, all recorded above)
- Harness bugs found+fixed during the run (recorded so the next fire doesn't re-hit them): mutant temp files must live under scripts/ (the acceptance script derives REPO from __file__ - root temp broke EXE path); FAIL-name regex must strip the trailing colon (`^FAIL (\S+?):`); MU2's expected-red gate was mine wrong, not the gate's - widening HI to 0x5175C0 correctly reddens A3b (the band-thunk-owners census), NOT A3a (both pumps already in the hub list); retargeted, full green run above.
- NEXT: track_mode after merge will read analyse_since_build=3 (B23 stays queued). Open: FUN_004c5d60's dialog-family callers (0x4c2e90-0x4c3760 thunks) + FUN_004d3f70's 15 band-member calls (largest driver); (ii) ds:0x68cbb4 writers; (iii) GOAL game-meaning.
- REVIEW ROUND #294 (2 P1 + 7 P2, ALL accepted; single PR comment): (1) vtable over-claim - the run from 0x672290 spans MULTIPLE tables (0x67290c = FAMILY +0x4c, base 0x6728c0, already in ## M288 - I re-derived instead of citing, AGAIN); claim narrowed to entries-at-addresses, "slot" retired. (2) "band members" quietly included off-band functions - callee lists now split in-band/off-band exact (8+4 / 5+5 / 4+1). (3) A6c-e were decorative subtractions - the REAL switch shape is pumpA two-stage (byte map 0x5165ec/0x516638 + 8/4-slot jumps) and pumpB one-stage (lea -0x51, cmp 0xc, 13 slots); heads+targets pinned from PE bytes; the byte-map layout law replaced the bogus 23/28/13 slot counts. (4) A7 compared "0x5186B0" against LOWERCASE ops (decorative zero - and the numeric rewrite crashed on a far-call operand `0x43:0x...`, now regex-guarded - latent everywhere direct_callees ran). (5) my inline '#' comment SWALLOWED the push-opcode check onto the same physical line - A7b is now its own gate. (6) 53 hub sites pinned exactly (A2b). (7) digest now hashes detail strings not booleans -> new digest 5e14170de426d127. (8) 0x25/0x27 mislabeled END/HOME (are LEFT/RIGHT). (9) session header undated per AGENTS.md. Harness: 23 mutants, 21/21 gates, all green (MU22 initially CRASHED via a KeyError - crash-rejected per law, retargeted to a value-tuple mutation).

## Session 279 (2026-11-18, close-out: M313 MERGED as #294, docs cursor)
- `milestone.py merge 294` verdict GREEN (gate pass 12 s on the review head), main = `eaf7d54`. No re-review arrived after the review-round head was pushed - recorded honestly as "none", not as a pass.
- KNOWN STALE TEXT on main: the squash merge title reads "pumpA via widget-vtable slot 134" - superseded by NAMED ## M313 + this note's s278 review round (entries-at-addresses only, multi-table run). GitHub titles are immutable here; the docs carry the law.
- `track_mode.py`: MODE=BUILD analyse_since_build=3 last_build=B22 next_rung=B23 -> NEXT FIRE BUILDS B23 from BUILD_SPINE.md (per-turn progress composed through the WRITER; B11's law in the written container, runnable acceptance, parity vs recorded trace, no box).
- Budgets after this close-out: SESSION_NOTES ~63 KB, NEXT_PROMPT <= 12 KB (see footer).

## Session 280 (2026-11-18, B23 BUILD, zero box) - the queue's per-turn progress composed through the writer
- track_mode MODE=BUILD (since_build=3); `milestone.py start B23` from main; this fire AUTHORED the rung into BUILD_SPINE.md (as B14-B22 did).
- `sim/composedturn.py`: the 10-boundary Korolev run of `evidence/trace_m56_build_20261026_145157.jsonl` folds through the WRITER - each boundary re-parses the image (st+0x40, mirror+0x98, pen+0x4c, slots+0x50, tile/owner), runs the B12 visit law, writes the span back; r0 arrival grows the unit array by the same call. `sim/savewriter.py` gained identity/raw/queue override keys (backward-compat).
- Acceptance `python3 -u -m sim.composedturn --sav programs/saves/m54b_clean.SAV` -> `== B23: PASS ==` 12/12 (evidence/b23_composedturn.txt); relay `python3 -m sim.selftest --b23 programs/saves/m54b_clean.SAV` -> `PASS B23: 12/12 gates`, run twice -> byte-identical (`12` ok rows). Shared-writer regression: `--b8` 10/10, `--b12`/`--b21`/`--b22` 12/12 after the savewriter edit.
- Rivals G9 5/5 (noadd/price10 lose the recorded arrival; nopop holds pending 1 vs recorded 0; zerotail drops stale ids; nomirror keeps 8 vs recorded 0). Falsifier G10: st:=20 poisoned in IMAGE bytes at r1 only -> container fold pays r1+r2 (3 arrivals; poison persists via the written image), model-fed fold blind (1 arrival) - both halves asserted.
- REVIEW ROUND #297 (3 P2, ALL accepted; single PR comment): (1) G7's creation source was untested - expected record built from FROZEN constants, so an image-fed producer swapped for seed values stayed green; now G11 poisons tile+owner in the container seed and demands the created record CARRY them, with a frozen-args rival failing the same fit (locate BY POSITION when the tile itself is poisoned - a coord lookup would hide the record). (2) the new `queue` override wrote any slot-list length - an 11th dword lands at +0x78, past the queue; refusal (len != 10) + 9/11 probes now in G8. (3) G11's determinism compared label+verdict only, dropping the DETAIL column that carries measured values; now full-row compare (falsifier detail normalized to '' so the guarded rerun is byte-equal) and renumbered G12.
- Docs: NAMED ## B23; cursor rewritten. NEXT: after merge track_mode flips to ANALYSE (B24 queued, not next); open picks (i'') FUN_004d3f70/FUN_004c5d60 thunks, (ii) ds:0x68cbb4 writers, (iii) GOAL meaning.

## Session 281 (2026-11-18, close-out: B23 MERGED as #297, docs cursor)
- `milestone.py merge 297` verdict GREEN on the review head (gate pass 15 s; no re-review after the fixes - recorded as "none", not a pass). main = `77a170d`. The squash title carries the corrected count (12/12) - patched via REST BEFORE merge, no stale-title note needed.
- `track_mode.py`: MODE=ANALYSE analyse_since_build=0 last_build=B23 next_rung=B24 -> next fire ANALYSES. OPEN PICKS (NEXT_PROMPT, post-M313 order): (i'') what ARE FUN_004d3f70 (15 band-member calls) and the FUN_004c5d60 dialog-family thunks; (ii) ds:0x68cbb4's 19 writers outside an index-store window; (iii) GOAL game-meaning / the one-char tokens / negative priority.

## Session 282 (2026-11-18, STATIC, zero box) — M314 pick (i''): the tour/dialog dispatcher family; the pumpB-direct correction; the lead's "15 band members" refuted
- Opened `milestone/m314` from main e0e95e1. One collision note: the manual-fire protocol was started by a cron fire that I cancelled (user switched the loop to MANUAL fires; job `smac-re-loop` paused with reason) — it had only created the empty branch; M314 collision-checked clean first (log/NAMED/scripts all 0).
- `python3 -u scripts/m314_tour_family.py` -> **== M314: 18/18 ==**, digest 4c9aa4eb4279b70b, two runs byte-identical (`evidence/m314_tour_family.txt`); `python3 -u scripts/m314_mutate.py` -> **20/20** (`evidence/m314_mutate.txt`). Zero box, zero /proc.
- VERIFIED (byte census; instruments print-then-assert, rivals included): FUN_004c5d60 = token-keyed dialog/tour dispatcher, EXACTLY 31 instr call sites all imm32-pinned (A1), 28 distinct tokens / 26 quoted + exactly 2 named s_ strings (A1b). 4 wrappers 0x4c2e90/f00/f70/fe0: one pinned producer {0x4c3f90/3f20/4000/4070} + one dispatcher call each (A2), `this` = DAT_007cdecc + [0][+4] in all 4 (A2b). 3 result handlers 0x4c5c40/ca0/cf0 (the "thunks"): cmp [ebp+0xc],0 / je / add eax,0x444 -> tail {0x4c1220, 0x54f790, 0x5510f0} (A3), 0x4c5cf0 = abs(c+2) on the bytes (A3b), 0x444 delta once per handler (A3c, M269 mechanism — a mid-run misread of 0x444 as a menu id was recorded and rejected, NAMED ## M314 row 4). All 6 registration pushes INSIDE the dispatcher, 2/thunk, two legs same order (A4); no push-immediate of pumpA image-wide (A4b).
- CORRECTIONS: (1) pumpB FUN_00516b80 calls FUN_004d3f70 (activate_at_tile) DIRECTLY at 0x517858 — M313's "off-band = 5" was thunk/hub-sites only; all 5 cited re-verified, 4d3f70 is the 6th; pumpA does NOT (A5/A5b/A5c). (2) The (i'') lead "FUN_004d3f70 calls 15 band members" is REFUTED: exactly ONE band member (FUN_0050cab0 x2 sites), 22 distinct callees off-band (A6); its callers = exactly 5 sites in {4748b0, 476580, 511960, 512450, 516b80} (A6b); 4 debug tokens real at .data: Console ACTIVATE / VEH ORDERS / Activate AWAKEN / Activate AWAKENING (A6c). INFERRED: tour-driver loop semantics (result!=0 continues, 0 ends); 0x95da12 reg = rec*0x130-2 (M311 stride); pane roles of 0x54f790/0x5510f0.
- REVIEW ROUND #299 (5 P2, ALL accepted; single PR comment): (1) the digest hashed LABELS, not measurements (`detail` keyed by short names, loop keyed by full check names -> every lookup empty; two different runs of changed numbers shared one digest) - now name+verdict+detail. (2) A4b pump check was DECORATIVE: `parse_text` keeps the mnemonic in a separate field, so the `^push 0x..$` regex matched no ops and `all([])` passed - a push of pumpA would have stayed green; now a bare-operand push census + pinned pumpA x3 / pumpB x1 call sites. (3) A3 claimed to read a `je` it never examined and A3b inferred abs() from neg/sub COUNTS; both now pinned entry-relative (cmp +0x9/+0x9/+0x29, je +0xD/+0xD/+0x2D, target = add-10, mov = add-3; 11-instruction abs sequence with jl/jmp targets). (4) A6b compared de-duplicated OWNERS while claiming "exactly 5 sites" - a 6th call inside a listed function stayed green; the 5 call-site addresses are now pinned (+ duplicate-owner mutant). (5) My NAMED row said 26 quoted tokens where my own evidence said 24 quoted + 2 named + 5 forwarded: the 2 unexplained entries were `param_1`/`param_2` forwards - the token law is now the exact 24+2+5 breakdown. Harness grew 20 -> 27 mutants, one per repaired fact; final `python3 -u scripts/m314_tour_family.py` -> **18/18**, digest **cf54a7ca907344c6** (x2 identical), `scripts/m314_mutate.py` -> **27/27**. Lesson for the skill (decoration class #4): a census that keeps mnemonic and operand apart must match the OPERAND alone, and any count-style claim ("exactly N sites") must pin the sites, not their deduplicated owners.
- NEXT: manual fires only (cron paused). track_mode unchanged (MODE=ANALYSE, B24 queued). Open picks: (ii) ds:0x68cbb4's 19 writers outside the index-store window; (iii) GOAL game-meaning / one-char tokens / negative priority.

## Session 283 (2026-11-18, close-out: M314 MERGED as #299, docs cursor)
- `milestone.py merge 299` verdict GREEN on the review head (`gate` pass 13 s), main = `e638772`. No re-review arrived after the fixes were pushed (Greptile reviews once, on OPEN) - recorded honestly as "none", not as a second pass. Full P2 accounting: single PR comment https://github.com/wronglebowsk/smac-re/pull/299#issuecomment-6978365896.
- KNOWN STALE TEXT on main: the squash title reads "20/20 mutations load-bearing" - that was the PRE-review harness; the merged head is 27/27 (`evidence/m314_mutate.txt:29`) with digest cf54a7ca907344c6. Titles are immutable after merge; NAMED ## M314 + this note govern.
- FIRE DISCIPLINE (user switch 2026-11-18): the `smac-re-loop` cron (789931d4b621) is PAUSED with reason; its one auto-fire was CANCELLED before it branched (left only an empty `milestone/m314`; M314 collision-checked clean in log/NAMED/scripts). HONEST FLAG: the in-chat fire was cut off by the iteration cap MID-review-round with a red intermediate tree (17/18 - a CMP_OFF I had just mis-written); no commit was made from that state and nothing green was overwritten, but the cursor was left "SUBMITTED" rather than "RED" - a cut-off fire must flag RED in the cursor, not only in the chat summary.
- Skill: 3 new decoration classes in skill/SKILL.md, rsynced to the live copy (operand-vs-mnemonic regex making an `all()` vacuously true; count claims compared on DEDUPLICATED OWNERS; digests that hash LABELS - mutate the numbers, never the labels).
- `track_mode.py` after merge: MODE=ANALYSE analyse_since_build=1 last_build=B23 next_rung=B24 -> NEXT FIRE ANALYSES pick (ii) (ds:0x68cbb4 writers). Budgets: NEXT_PROMPT at cap (see its header) - a later fire may need a docs split; SESSION_NOTES ~66 KB; skill 50.9 KB.

## Session 284 (2026-11-18, M315 fire - pick (ii): what is ds:0x68cbb4?)
- Manual fire (cron paused). `milestone.py start M315` from clean main `fc16cb5`; id collision-checked (log/NAMED/scripts all 0). ZERO box, ZERO /proc, no gdb - static census of the shared parse engine + the image bytes.
- `python3 -u scripts/m315_bb4_census.py` -> **== M315: 9/9 ==**, digest **c2b025b32280d82b**, two runs byte-identical (`evidence/m315_bb4_census.txt`); `python3 -u scripts/m315_bb4_mutate.py` -> **19/19** (`evidence/m315_bb4_mutate.txt`).
- VERIFIED (all numbers printed before being asserted): census A1 = EXACTLY 22 stores / 5 reads / 1 cmp (28 refs, every address pinned). A2: the ONLY immediate ever stored is `0xffffffff` (8 direct) and 2 more reach it via the `or r,0xffffffff` idiom (`0x41b7a7`, `0x5984b4`) -> 10 sentinel-valued. A3 THE LAW: the 22 partition EXACTLY into 12 stores followed within 16 B by `call 0x4e8d60`+`call 0x4e78e0` and 10 clears, the two sets being exact complements. A2b/A9: def-walk of every register store's source inside its own function = 8 x `mov r,ds:0x68cbb0` (the current index) + 4 x a caller stack slot (`[ebp+0x8]`/`[ebp-0x18]`); zero arithmetic, zero other globals -> "second cursor fed from elsewhere" dies on the def-walk (a store fed from a NEIGHBOURING index would have survived A3, so A2b is the refuter, and A9 pins that census: 0 stores read `ds:0x68cbac`/`ds:0x68cbb8`). A4: a LOCAL dedup guard (cmp of bb4 or of its loaded copy + `je` PAST the store) exists at only 4 of the 12 memo sites {`0x4eb6c7`,`0x4efeaa`,`0x4f2201`,`0x4f5c4a`}; the other 8 refresh unconditionally. A6: the two decisive windows pinned instruction-for-instruction incl. the `je` targets. A7: image inits BOTH dwords to `-1`.
- METHOD NOTE (why the answer is a memo, not a cursor): the guard at `0x4efea0` compares the OLD memo against the NEW index and `je`-skips the four calls, then `0x4efeaa` stores the new index - that is the shape of "run the reaction only when the record actually changed". Rival "scratch/temp" dies on the 5 reads + 1 cmp gating 2 calls; rival "paired with the index like the pointer is" dies on 3/22 (M311's own window) and 5/22 (+-96 B).
- CORRECTION TO MY OWN FIRST DRAFT (caught by measurement, recorded rather than deleted): I first asserted M311's "only 3 in an index-store window" was an UNSPECIFIED window and that my +-32 B reading coincidentally matched. Reading `scripts/m311_recidx.py:449` shows it was a FORWARD `0..+32 B` window - and its 3 sites are the same 3. My +-96 B figure (5/22) is a DIFFERENT window, so the closure arithmetic had to move onto M311's window: 19 outside = 10 clears + 9 memo updates (my first version said "9 memo updates outside +-96 B", which the print showed to be 7 - the arithmetic was wrong because all 5 windowed stores are memo sites). A5 now pins the window it uses.
- HARNESS LESSON: single-gate expectations were wrong for facts that propagate - widening the refresh pair's callee or tightening its 16-B reach reddens A3, A4 AND A9 (the memo set feeds all three). The harness now declares the exact SET of gates a mutant must redden and requires SET EQUALITY (extra reds = an undeclared dependency; missing reds = a decorative assert). Two of my first-pass mutants (MU8 `>=` instead of `==`, MU16/MU17 weakenings) stayed GREEN on real bytes - i.e. those specific clauses were decoration; retargeted to mutations that are false on the real bytes.
- UNVERIFIED/OPEN: what `0x4e8d60`/`0x4e78e0` actually do (neither is in NAMED); whether the 4 stack-slot writers carry an index (def-walk stops at the parameter); whether deletion/creation of a record keeps the memo coherent (needs a box run, not attempted).
- NEXT: docs cursor after merge; track_mode unchanged (MODE=ANALYSE, B24 queued). Remaining picks: (iii) GOAL game-meaning / one-char tokens / negative priority; new pick from this fire: NAME the refresh pair (`0x4e8d60`, `0x4e78e0`) and the 8 unguarded memo sites' callers.
- REVIEW ROUND #301 (6 P2, ALL accepted): (1) the provenance classifier keyed on OPERAND TEXT, so `add r,ds:0x68cbb0` would count as "reads-index" and `lea r,[ebp+0x8]` as a stack-slot load - the "never arithmetic" claim was decoration. Now the kind is set by MOVING INSTRUCTION + SOURCE OPERAND. (2) `span()` returned (0,0) for an owner index.csv cannot bound, so the def-walk could run to the TOP OF THE CACHE and borrow a write from another function; now a CLAIMED function bounds the walk at its own start and the one unclaimed store gets an explicit 36-instruction cap, measured and pinned by A10. (3) The 16-B pair reach bounded only the FIRST call - the second was accepted anywhere in the next 4 instructions; now both are bounded, which moved the true worst gap to 17 B (`0x4f5ab7` at +12/+17, not 16) and initially dropped it out of the memo set (memo=11). (4) A4 counted a cmp of the memo against ANY register as a dedup guard (`cmp ds:0x68cbb4,edx` scored as a guard for a store of `eax`); now the cmp must compare against the very register the store writes, with no clobber between cmp and store. (5) A6 claimed to pin windows "instruction-for-instruction" but checked 7 LISTED addresses and skipped the fold between them; now all four windows are pinned as the COMPLETE sequence between the bounds, including `lea ecx,[esi+esi*8]` / `lea ecx,[esi+ecx*2]` / `shl ecx,0x4` / `add ecx,0x95da10`. (6) My NAMED row concluded "the memo's dedup is enforced by the CALLER" from the ABSENCE of a local guard at 8 sites - not established; downgraded to OPEN (pick (v)).
- NEW HARNESS FAMILY (the reviewer asked for parsed-instruction tests, not count tests): the census takes `M315_PATCH="addr|mn ops;..."` which rewrites the PARSED DISASSEMBLY before any measurement, and 7 PC* mutants use it - `add`-instead-of-`mov` on the index load, `lea`-instead-of-load of the slot, a guard cmp against an unrelated register, the pair's second callee deleted, a corrupted fold instruction, an index store turned into `nop`, and a sentinel clear that GAINS a refresh pair. The two provenance mutants are exactly the ones a text-keyed classifier would have survived. **29/29** (22 expectation + 7 code), every one required to redden EXACTLY its declared gate set.
- TWO HARNESS BUGS OF MY OWN, recorded: MU6 (change the pair's second callee) CRASHED the census (`max()` over an empty list) - a crash is not a red gate, so the instrument now degrades safely; MU10 was written as a WEAKENING (`<=`), stayed GREEN, and was retargeted to a false-on-real-bytes claim. Also MU10/MU21 prove the partition claim is sensitive to both the reach and the absence bound.
- TOOLING ANOMALY, recorded honestly: a `patch` op that REPORTED "Could not find a match" had in fact applied a fuzzy rewrite to the NAMED guard row (the OPEN-downgrade text was in the working tree). Verified by `git diff HEAD -- NAMED.md` before committing. Lesson: after a failed patch on a markdown table, diff the file - the report is not the state.
- CORRECTION TO MY OWN NUMBERS in this fire: 12 memo updates stand, but the pair reach is **17 B** (not 16), and the partition is now stated as TWO INDEPENDENT CLASSIFICATIONS that coincide (provenance vs adjacency), which is a stronger claim than either alone. Gates 9 -> **10** (A10 added), digest now **3976ca97eedc1e19**, mutants 19 -> **29**.
