# Session notes archive — sessions 300-305

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-300-300.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 300-chain2 (2026-11-19, M325 MERGED, post-merge note; docs-only, zero box)

- MERGED #329 squash **fb6e6c4**. Review 2P1+8P2 10/10 accepted in one reply; post-review 8/8 a623181d7fb68263 x2 + at-head identical; harness 30/30 (29+1) 97c193e12593c95e; CI 13 s CLEAN; main did not move (no rebase). Squash title "24/24+1" = PRE-review harness; NAMED ## M325 ACCEPT governs. Note: docs/m325-merged; pr329 .json sidecar folded in.

## Session 301 (2026-11-19, B26 MERGED, post-merge note; docs-only, zero box)

- MERGED #328 squash **dd704d0** (head d5ec615), CI `gate` pass 15 s, mergeState CLEAN. The fire
  was mechanical: commit the owed MU21 work, re-verify, land it. Accept re-run before push:
  `python3 -u -m sim.selftest --b26` -> **PASS B26: 10/10 gates** re-diffed 0 against
  `evidence/b26_selftest.txt:63` (anchor ae43e0ab9c8cfc3d `:52`), and
  `python3 -u scripts/b26_mutate.py --entrypoints` reproduced `evidence/b26_mutate.txt:25-30`
  verbatim (MU21 OK, IDENTITY 2/2) without re-running the 20-mutant sweep.
  `gate.py --base main` GREEN 0 warnings; `review_lint.py --id b26` PASS (11 V rows).
- main moved under the PR (chain 2 #326/#329): absorbed via a merge commit (force-push blocked in
  cron), both chains' sections kept; NEXT_PROMPT 12,750 -> under cap by rotating the two CLOSED
  pick rows to §trim-s300-chain1 (b) (sha1 b0e7c1d2614f2312) with M325's row kept LIVE.
- The squash title carries the POST-review numbers because `gh pr edit` ran BEFORE the merge; it
  fails on the Projects-classic GraphQL error, so use `gh api -X PATCH repos/<r>/pulls/<n>`.
  ONE triage reply posted, all 10 findings, no re-review (one per PR).
- DEBT for the next fire, whoever's chain it is: `NAMED.md` **246,259 B vs the 250,000 B FAIL
  line**; `evidence.py budget` exits 1 on FAIL and that alone reddens the gate. Rotate VERBATIM
  into a `docs/named-archive-*.md` BEFORE adding (§B26's 11,151 B rows -> `docs/named-archive-b26-rows.md`).
  Note: `evidence/` is 21.2 MB/20 MB warn - `evidence.py prune` finds NO victims, so the prune
  lever is not what the warn line wants; only the FAIL lines gate.

## Session 301-chain2 (2026-11-19, M326 CLOSED+REVIEWED, STATIC: block+0x224 = deferred HURRY payment)

- milestone/m326 (main 6ee41a8), PR #332. ANSWER: per-faction DEFERRED HURRY-PRODUCTION PAYMENT ("energy debt"). `python3 -u scripts/m326_block224_census.py`: 13 hits (3W/10R dw, 0 seeds224, 27 accesses/0 sibling-into-224). Sole add-writer 41a543 in FUN_00419c30 = HURRY dialog (HURRY/HURRYOPTIONS/HURRYPAYMENT pushed ONLY there): defer cost iff 920434&91c62c!=0 (phase: 91c62c:=1 around turnfn/upkeep calls 520c99/520cf8), else pay ENERGY+91c64c now. All 10 readers = 220-224 AVAILABLE (structural; itoa 1 site); cheat-cap MIN(g999fa4,avail)@41a4e0-f9 (M325 OPEN consumer). Upkeep 5208f0: ENERGY-=224, 224:=0 (esi=0 proven), floor0; x8380 fold DERIVED. RESET 59ec90 zeroes. turnfn 16st/0blk.
- RESOLVER FIX (self-found): partial-reg writes skipped by def-walk -> over-proved const-0 (xor eax,eax; mov al,[rec+4]); both skeleton BLKCONST tags artifacts. Fix BOTH directions (review: full write opaque for queried partial; seed scan breaks on partial redef; ALGO7=old, S5). 13/13 STRIDE; leaf=byte[rec+4] via sole slot stores 419d94/41690d (noun INFERRED). M325 crosscheck now GATE G10: 29 labels BLKCONST->STRIDE +4 det; pins/totals unchanged; M325 own 8 gates RE-RUN under fix = 8/8 -> NAMED M325 row qualified in place.
- Save [0]*8, foffs=550+k*20bc pinned, raw block carry (596a91); gap@328=own-player 3. No DEBT str; LOAN pushes in 6 non-writer owners. R1-R6 DEAD.
- REVIEW #332 (4P1+6P2) 10/10 accepted: mutant-map corrected (MU4->G5 row; NO-OPs uncited), roles->G1, G6 structural (MU25/26), G3 count pin (MU27), G10 gate (MU24 algo8), ACCEPT path:line, foffs pin, 10/10 regex fix.
- ACCEPT 10/10 **f0f31c3daa26b601** (`evidence/m326_block224_census.txt:45-46`) x2 (`_rerun.txt`; pre-review 9/9 66595e09a651a94d). HARNESS **27/27 (25+2 NO-OP)** **07326ba5d23a2dbe** (`m326_mutate.txt:30-32`); sweeps corrected MU13/23/26 sets; ST 5/5 (`_selftest.txt:7`).
- OPEN: 920434/91c64c nouns; 419c30 callers; branch caveat 419de9/419e1f.

## Session 302-chain2 (2026-11-19, M326 MERGED, post-merge note; docs-only, zero box)

- MERGED #332 squash **7cd4732**. Review 4P1+6P2 10/10 accepted in ONE reply; post-review 10/10 f0f31c3daa26b601 x2 + at-head + post-rebase byte-identical; harness 27/27 (25+2 NO-OP) 07326ba5d23a2dbe; ST 5/5; CI gate 14 s CLEAN, mergeState CLEAN.
- Main moved under review (chain 1 B26 #331 -> 4a03182): rebased keeping BOTH chains' sections; force-push blocked in cron -> absorption merge 0a3aff1 (`git merge -s ours` of pre-rebase tip 6581627; tree == rebased bb5ad0a, empty diff verified, ff push). NEXT_PROMPT 12,420 -> 11,997 B (M325 one-liner VERBATIM -> pick-archive §trim-s301-chain2 (a), sha1 a5d8e0a402bc; M326 line compressed).
- Squash title carried the PRE-review numbers (9/9, 23/23); PATCHed via `gh api -X PATCH repos/.../pulls/332` to post-review (gh pr edit fails on Projects-classic GraphQL). NAMED ## M326 ACCEPT governs (10/10, 27/27).
- NAMED headroom DEBT: 248,242 B vs the 250,000 B FAIL line (1,758 B left) - rotate VERBATIM into docs/named-archive-* BEFORE adding (chain 1's B26 note).
- `gh pr merge` local cleanup fails ('main' checked out in chain 1's worktree) - remote merge unaffected; this worktree cannot checkout main while chain 1 holds it.

## Session 303-chain2 (2026-11-19, sidecar-fold remediation; docs-only, zero box)

- #334 (pr332 review sidecar .md/.json fold, squash **81e1e02**) was merged with a RED checkpoint
  gate: my batched poll+merge command did not condition on PASS, and the sidecar-only PR diff
  lacked the SESSION_NOTES+NEXT_PROMPT updates the mechanical gate requires. MY ERROR - recorded,
  not hidden. All content checks (blobs/endpoints/citations/skill) passed; only the checkpoint failed.
- This PR is the remediation: this note + the M326 line update (harness digest 07326ba5d23a2dbe
  stays in NAMED ## M326 / s301-chain2; the line keeps 27/27). Gate verified GREEN BEFORE merge.
- Worktree rests detached at origin/main afterwards (chain 1 holds the main checkout).

## Session 304 (2026-11-19, M327 CLOSED, STATIC pick (vii), zero box) — `+10` is a TYPE INDEX; `NAMED ## M327` governs

- **`python3 -u scripts/m327_typeband_census.py` → `PASS M327: 11/11 gates`** (`evidence/m327_typeband_census.txt:771`, digest **`ee77ddb39e8ec202`** `:769` pinned as `PIN`; 3 runs, 2 byte-identical to the committed file). Harness **`python3 -u scripts/m327_mutate.py` → `HARNESS PASS 22/22`** (`evidence/m327_mutate.txt:26`): 21 mutants scored against sets MEASURED with `M327_MUT_MEASURE=1`, every gate reddened by ≥1 mutant, plus **MU21 declared NO-OP** (out-of-scope `.text` byte at 0x5ab345 reddens NOTHING — the proof no gate is decoration on prose).
- ANSWER: `+10` = signed index into the save's own type array, **512×52 B = 26,624 B** at `count_off+4+count_len+3584`, ending **4,096 B** before the unit array (`:2-5`; 26,624 is `sim/save.py`'s own MIDDLE_SECTIONS term). `.text`: **659** chains `movsx [+0x933282]` → `imul 0x34` → `add 0x98ad88` (774 word refs, 116 funcs), pinned `0x4bdec4-0x4bded4` and `0x5ab3a2` in `unit_set_position` (`:9`, `:669-671`). `+10`//64 = faction band, **25/25** owner(+14) == band; **32/512** slots named (14 band-0 + 18 faction); **67/67** records name a slot = 10^-80.7 by chance (`:767`).
- **The exemption is ours, and its evidence was our own poke.** 0/67 records of `m54b_clean` are out-of-grid (`:739`) and `unit_set_position` (90 insns, 9 jumps) has **0 branches between entry and its +0/+2 stores** (`:756`). It bites on **1 of 4** saves (`m113map`, found_units 67 → **49**, `:763`) — and `m113map` = `m54b_clean` + **20 markers `0xc0de0001..0xc0de0014`, stride 128 from 222000** (74 B differ, `:741-752`). 13 windows in-array touch 14 records; the grid is FILE-aligned so `223664` straddles rec16+49..51/rec17+0 (`:753`). Out-of-grid **[12 (3076,56832), 17 (192)] ⊆ struck** (`:755`); recs 2 and 52 are struck yet stay in-grid — why the old trap-14 story saw only two.
- Rivals dead (`:768`): not-units False; flag-word False (**AND of the 8 band values = 0**); "a real state needs it" False; "store guarded" False. Bonus: the saved array == M80's live census minus 324/325, M80's own creations (`:766`); type byte `+0x2d==0xff` exactly on the 14 band-0 slots (meaning OPEN); `+0x30` bit 2 NOT a band marker (12/20); **`m112poke` is a byte-copy of `m54b_clean`** (`:4-5`) → 4 saves = 3 states; replicates on `m112auto1` (68 recs, 25 band, 25/25).
- RETRACTED IN PLACE (`scripts/m327_registry_patch.py`, 3 edits, count=1): `0x933278` "flags at +10"; M26 `unit_can_act` bits 0x40&0x400 (bit 6 = index bit 6, 6/67; 0x400 is bit 10 of the word at **+12**, 0 in all 67, `:757`); `## B25` "INFERRED that the .exe shares the rule". `sim/save.py`+`composedmove.py` comments corrected, behaviour unchanged (`--b26` 10/10 `ae43e0ab9c8cfc3d`, `--b25` 9/9 `901a286332960a10`, re-run after).
- DOC CAP (NAMED 248,242 B, 1,758 from FAIL): `scripts/m327_named_rotate.py` moved `## M316` (6,699 B, sha1 `d3dffc67fcb5`) + `## M311` (5,247 B, sha1 `0b12d45d08a4`) VERBATIM to `docs/named-archive-m31{6,1}-rows.md` with cite-preserving stubs → **246,504 B**.
- PITFALLS: the chain walk needs a WINDOW around the read, not the function (whole-function: 659 → 736 sites, MU17 reddens G2+G10). Attribute a poke per CHANGED BYTE — a 4-B window can straddle a 52-B record.

## Session 305 (2026-11-19, M327 LANDING + Strata review round, zero box) — `NAMED ## M327` governs

- s304's two lint blockers cleared (`review_lint --id m327` → PASS, 7 V rows): the RETRACTED row names its falsifiers (MU4/MU19, MU6/MU16/MU18, MU11, MU13, MU23/MU24); the mutate cite carries `:line`.
- **PR #337 review (local Strata; `evidence/ai_review/pr337_20261119_235407.md`) = 3 P1 + 5 P2, ALL ACCEPTED, none dismissed.** P1-1: `type_off_of` hardcoded `+3584` while `type_section` honoured the ALGO=9 shift, so under MU20 the census and predicate C measured two DIFFERENT arrays — now ONE law (the offset is passed in). P1-2: G5's detail claimed "C matches B on 4/4" but the condition only tested A==B — now a clause. P1-3: `cover_ok` was `w in wins` where `wins` is derived from `w` (an identity) — now the real law: the 20 diff windows == the 20 marker dwords an INDEPENDENT value scan of `m113map` finds (`:741` prints `windows=20 marker-scan=20`).
- P2: `+12 zero on 67/67` PRINTED→ASSERTED (G3 `n12 == 0`) + **MU23** `M327_ALGO=10` (same census at `+10`: `nonzero=64`), measured **{G3,G10}**; T6's bit-counts gated (`bit40==6/bit400==0/both==0`) + **MU24** (`+10:=1024`) measured **{G3,G5,G6,G10}**; G1's X==X offset clause now cross-checks `off+26,624+4,096 == SV.units_pred`; registry_patch `/home/paul/...` → ROOT; the double `type_section(PRIMARY)` parse → `parsed[]`; header `pick-archive.md` → `docs/pick-archive.md`.
- **PIN RE-MEASURED `ee77ddb39e8ec202` → `91f58f3de03090c1`** (T4's printed row legitimately changed; no threshold moved). `python3 -u scripts/m327_typeband_census.py` → `== M327: 11/11 ==` (`evidence/m327_typeband_census.txt:771`, digest `:769`), 2 re-runs byte-identical. `python3 -u scripts/m327_mutate.py` → **`HARNESS PASS 24/24`** (`evidence/m327_mutate.txt:29`; base `reddened=[] ('11','11')` `:2`; coverage True `:27`; MU21 the only NO-OP `:28`) — and a reproducibility defect died with it: the header used to print its random `mkdtemp` path, so the file could never diff clean; the path now goes to stderr.
- **Skill drift, not mine**: `skill sync` failed because the LIVE skill was 2 additions ahead of the tracked copy (chain 2's registry-stub rule + the parallel-job ownership exemption); `rsync -a --delete` live→`skill/`.
- PITFALLS: a parameterised format string must print byte-identically at the unmutated value or the digest pin moves (`word@+%d` with 12 == `word@+12`); `milestone.py submit` PREPENDS `<id>:` to `--title`; `gh pr edit` dies on the projects-classic GraphQL error — use `gh api -X PATCH repos/.../pulls/<n>`.
- NAMED 246,504 → **247,028 B** (headroom 2,972 — the NEXT fire rotates BEFORE adding a block).
