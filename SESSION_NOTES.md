

Older sessions: `docs/sessions/sessions-308-308.md` (1 sessions: Session 308). The split is by FILE POSITION, not by number — a moved id can be numerically newer than the first kept one, so grep the archive for an id before deciding it is still hot. The hot file starts at Session 307-chain2.

## Session 307-chain2 (2026-11-19, M330 CLOSED, STATIC: block+300 = upkeep spend accumulator)

- milestone/m330 (main 57920b6). +300 = per-faction UPKEEP SPEND ACCUMULATOR: zeroed at entry 52056d (+2fc/+308/+3f8 too); fed by 4f47f0 (ROUND>1, 4f5cc6-cf): slots 1..34 (bits 95da9c) v=[984d48+48*slot]; CONDITIONAL halving (985ba0>=0 AND owner-match: v+=bit5, trunc/2; else FULL); ENERGY-=v @4f4950-52, +300+=v @4f495e-62.
- Refund 520714-78f: ds:985aec>3 (difficulty INFERRED, M308) AND x!=0; r=trunc(k*x/3) k=1(==4)/2(>=5), magic 55555556x4+signfix; E+=r @520743/770; x-=r @52078d-78f (residue KEPT, unlike +224). Mask VACUOUS: cl=[ebp-4]=8 -> dl=0. Ledger @52081a-841: +310:=+2fc; +30c:=+308-+300++2fc. 535c60/546800: (+2fc-+300) credit-like OPEN.
- Census: 25 raw -> 11 FIELD (4W/7R STRIDE) + 2 arg-fed R (54b367 [ebp+8]@54b1e5=8380*esi; 5362f5 2 defs 2095*arg3/8380*edi); 14 excluded (579329=facprofile+300!). Seed 5233d0+sub@5233fe. turnfn 0blk. Carry raw block (M324); m54b_clean vals=[0,1,1,0,1,0,1,1], energy==M325; m112auto1 differs.
- `python3 -u scripts/m330_block300_census.py` -> **13/13** **470d844054b1b101** x2 (`evidence/m330_block300_census.txt:67-68`,`_rerun.txt:67-68`). `python3 -u scripts/m330_mutate.py` -> **31/31 + 1 NO-OP, 0 MISMATCH/CRASH** **cf85092dea6baa93** (`evidence/m330_mutate.txt:36-38`); ST 5/5 (`_selftest.txt:6`). Sweep 1 17/20: MU7 bound-hardcode fixed; MU16 decl +G1; MU21 -> m112auto1 (m113map blocks==m54b_clean, M327).
- Review #340 (Strata): 2 P1 + 8 P2 ALL accepted+fixed (strengthen): G10 input law (MU22-24); G6 gap-liveness/back-edge/snap (MU25-26); G7 eax-liveness/no-mid-branch (MU27={G1,G2,G3,G7}); G12 liveness (MU28-30); G3 operands (MU31); G4 sign-fix tuples (MU32); x3->x2 (3rd overwritten); ST cite. Supersedes 63def04aadb07bcf/730127f586346fa6.
- PITFALLS: disp 0x300 hits profile/ladder/loader/stack siblings (provenance filter!); 546800 overwrites [ebp+8] 13x; 535c60 fold lacks final shl2 on one path.
- OPEN: 34-slot noun (984d48/48); 985aec; +2fc/+308; arg3=4*faction; profile+300.

## Session 309-chain2 (2026-11-19, M330 MERGED + pr340 sidecar fold; docs-only, zero box)

- **#340 merged -> `1b9cb38` on main** (squash; verdict GREEN, CI gate pass 14s on absorbed head 240240d; mergeState CLEAN). Title PATCHed pre-merge with the post-review numbers (470d844054b1b101 x2 / 31/31+1 cf85092dea6baa93). Merged tree == absorbed tree (diff 0).
- Chain 1's M329 (#339) + docs #341 landed mid-fire -> rebase kept BOTH chains' sections; force-push cron-blocked -> absorption **240240d** via commit-tree (tree byte-identical to rebased head). NAMED 240,158 B post-rebase (chain 1 rotated at s308; headroom 9,842). Census re-measured byte-identical at the rebased head.
- **PROCEDURAL DEFECT (own)**: the pr340 JSON sidecar fold #342 (bbdd89a) was merged while its CI gate was FAIL — `milestone checkpoint: SESSION_NOTES/NEXT_PROMPT not updated`; docs-only PRs are NOT exempt (s306's #338 passed because it carried a session section). Content harmless (1 evidence JSON, 18 siblings tracked); this section + the NEXT_PROMPT line are the fix-forward. LESSON: read `gh pr checks` BEFORE `gh pr merge`, even for docs folds.
- Review count for the record: local Strata on #340 = **2 P1 + 8 P2, 10/10 accepted, 0 dismissed** (`evidence/ai_review/pr340_20261120_011440.md`; JSON folded via #342). STATE: (viii) ANSWERED by chain 1's M329; B27 spine still chain 1's next build.

## Session 309 (2026-11-19, BUILD rung B27 CLOSED, zero box) — the ENERGY round executable + carried; two gate defects the mutants caught

- Ownership: the only running row for job 789931d4b621 is this fire (`python3`/sqlite3 over `~/.hermes/cron/executions.db`; the `pid` column is the gateway pid for every row); chain 2's `9a0b613bb1ac` row is the known parallel lane. main was 1 behind (M330 #340) -> ff-pull, then `milestone.py start b27`.
- track_mode said `MODE=BUILD next_rung=B27`: authored `BUILD_SPINE.md` §B27 (file 72,750 -> 78,225 B) BEFORE the instrument, per the B14-B26 pattern. `python3 -u -m sim.selftest --b27` -> **PASS B27: 10/10 gates** `evidence/b27_selftest.txt:77`, anchor/digest **b65e8129b67ba67d** `:54`, 2 runs diff-identical. Harness `python3 -u scripts/b27_mutate.py` -> **HARNESS PASS 16/16** digest **81d2d9491ec3320d** `evidence/b27_mutate.txt:18-20`, NO-OP reddens `[]`; `--selftest` -> **3/3** `evidence/b27_mutate_selftest.txt:1-3`.
- Printed (same run): ENERGY `[10,28,112,69,229,60,102,37]` + `+300 [0,1,1,0,1,0,1,1]` + `+224 0*8` + both offset tables == the M325/M326/M330 census lines PARSED from evidence (`:14-19`); ledger laws **8/8 + 8/8** on the save's own bytes, rivals 1/3/1 (`:20`); refund == M330 G4's 7 samples, sweep 40,002 cases 0 violations (`:23`); k-table `[0,0,0,0,1,2,2,2,2,2]` derived from the switch tuples parsed from the census (`:24-25`); ordering 3/3 discriminating fixtures, save 0/8 (`:32`); B4 in-process 3/3, idle 12/12 flat 15, post-found 19 vs k=2->20 / full-refund->21 (`:34-36`); writer identity True, 40 spans, 9 bytes differ, 0 outside, carry `[0,0,0,0,0,0]` (`:56`); falsifier `[4]`, smuggler blind (`:59`).
- **WRITER EXTENSION**: `savewriter.build_image(..., block_writes=)` + `modeled_spans(extra=)` — block A was a pure lift through B26. `modeled_spans()` called with NO argument is pinned == the pre-B27 span list, so B8-B26's "every differing byte is modeled" gates are NOT loosened by this rung (MU11 reddens exactly that).
- **TWO GATE DEFECTS FOUND BY THE MUTANTS (mine, both fixed by strengthening, not weakening)**: (1) G3 re-typed the ledger formula inline instead of calling `sim.energy.ledger`, so MU1/MU2 reddened NOTHING — an instrument that re-types the law it tests measures the copy; (2) `round_legs` passed `clamp=True` explicitly, shadowing `settle`'s own default, so MU7 (floor-0 dropped) reddened NOTHING — `clamp=None` now means "the module default" (selftest ST1). Then G6 got the defaults-vs-parsed-thresholds cross-check and G5 got the counted sweep width (`sweep_n` is now counted, not a literal `2 * 20001`, which MU16 proves).
- Declared limits, printed not hidden: 48 rows computed / 13 printed (`:53`); `+2fc/+308/+3f8` entry-zeroed but their mid-round writer is OPEN (M330) so they stay pass-through and the ledger law takes them as DECLARED inputs; income-vs-feeder order unpinned (only settle < snapshot < refund is); difficulty dword = 2 read out of the container, noun INFERRED (M308).
- Caps: NAMED 240,158 -> 241,+this block; NEXT_PROMPT 11,348 -> patched by section (retire the B27 pick, add the (x) OPEN-LEADS list); evidence 21.9 MB `[warn]` stands (prune 0 victims, `m294_gate_rows_raw.txt` load-bearing). `skill/` untouched (`diff -rq` clean).

**Review round, PR #344 (Strata, 10 findings: 3 P1 + 7 P2 — ALL accepted, 0 dismissed).** The
local review caught that several B27 gates measured less than their prose claimed. Commands +
numbers, all re-measured after the fixes:
- **F1 (P1)** `scripts/b27_mutate.py` did NOT implement its advertised law: it only required each
  mutant to redden >=1 gate. Fixed: `DECLARED` sets frozen from a `--measure` run, then every run
  compares measured vs declared IN BOTH DIRECTIONS (`decl_complaints`) and requires all 10 gates
  covered. `python3 -u scripts/b27_mutate.py` -> `exact-set check: 17 mutant(s), 0 complaint(s),
  gates reddened 10/10` + `HARNESS PASS 17/17` digest `181d99d9ac000044`
  (`evidence/b27_mutate.txt:20,:22`; 2 runs diff-identical). `--selftest` now 4/4 — **ST4** rejects
  a wrong declaration (`evidence/b27_mutate_selftest.txt:3`).
- **F3 (P1)** G1 was substring presence. Pins are now `(label, address, FIELD TOKEN, file)` and one
  evidence line must carry both; the bogus control ships INSIDE `LEG_PINS` and must hit nothing.
  G1 prints `22 pins, min line hits 1; control bogus-control hits 0` (`:69`). New mutants MU14
  (a pin on the wrong field) and MU17 (control counted as honest) both redden G1 alone.
- **F2 (P1)** G7 asserted the refund leg was inert without measuring it. It now measures on the
  save's own 8 blocks: `debt 0/8, refund 0/8 at difficulty 2 AND 0/8 at the k=1/k=2 difficulties
  (max +300 = 1) while refund(3,k)=1 at both k (probe 2/2)` — the leg is not a stub, the save is
  small; plus `k_reads_gdiff` binds the switch to the same global (`:36`, `:75`).
- **F4 (P2)** the k-table's branch SHAPE is now gated (mov of `0x985aec`, cmp 0x3/jle-skip,
  cmp 0x4/jne-DIFFERENT, so the k=1 fall-through exists) and BOTH rivals are gated, not just
  printed (`:74`). **F6 (P2)** RETRACTED in the registry: the flat 12-round idle parity is a
  legs-ZERO CONSISTENCY print (cannot fail) — labelled as such, gates nothing; the parity is B4's
  3 in-process gates + the post-found row. **F7** smuggle rival = two counted numbers (honest 1,
  smuggler 0), no cancelling abs(). **F9** G10 now pins the printed-table digest
  `3c134ea70638c12b` and the container `626fec9a35deddba`, not only the row digest (`:56`, `:78`).
  **F10** the outside-span containment is measured per round (`[0,0,0,0,0,0]`, `:55`, `:76`).
  **F8** the spine claimed THREE file-offset tables; only two exist to gate (M325 prints none for
  +220) — spine narrowed. **F5** cites `:20`->`:20-21`, `:53-56`->`:55-59` etc.
- Re-accept after all fixes: `python3 -u -m sim.selftest --b27` -> `PASS B27: 10/10 gates`
  (rows anchor unchanged `b65e8129b67ba67d`), 2 runs diff-identical. NAMED 244,581 B
  (5,419 headroom); NEXT_PROMPT 11,832 B. Lesson for the chain: a gate whose expectation is
  hand-written next to the value it checks, or a rival that is printed but not gated, is the same
  defect the #339 review named at doc level — it lives at gate level too.

## Session 310-chain2 (2026-11-19, M331 CLOSED, STATIC: +2fc/+308 = upkeep INCOME siblings)

- milestone/m331 (main e0b7d0a). **+2fc = per-faction per-turn GROSS ENERGY INCOME accumulator** (noun INFERRED): zeroed 520567; feeder 4eacd9 (FUN_004eaa10) gate ds:8f0d64==1 (phase 1, sole set 4f5b2c): += clamp(base_rec+0xd4, 0, 99999); +0xd4 = +0xc4−+0xf4−4e9880(+0xc4−+0xf4); +0xc4 += 8f0c74, +0xf4 := 8f0c3c (sole stores 4e8d86/97 in 4e8d60). Tail 52080c: +1 per OWNED base in the no-interest fallback. **+308 = secondary income acc**: zeroed 520573; feeder 4f5cb0 (FUN_004f5a70(base_idx), called per owned base @5206d3): += Σ 8f0d40[k−1], k=1..7≠owner, block+0xc0==0 both; ENERGY += base_rec+0xfc @4f5c85-8c.
- Interest lead CLOSED: facprofile+0x4ec = rate%, ENERGY += trunc(E*rate/100) (magic 51eb851f sar5+signfix), gated +0x508 bit14; rate==0 → +1 E AND +1 +2fc per owned base (95da14/985af4 walk).
- Ledger +310:=+2fc, +30c:=+308−300+2fc verified NUMERICALLY 8/8 m54b_clean blocks (v2fc=[0,7,14,4,32,9,9,2], v308=[0,0,0,0,3,0,0,0], v30c=[0,6,13,4,34,9,8,1]); minus-variant dead.
- Caps: 546800 MIN(trunc(E/2), 100×(+2fc−300))≥50 else exit 54b91b (fold DERIVED=100); 535c60 Σ MIN(net, block+1058)×arg3 + trunc(E/5) (66666667). Readers: 522b70 ENERGY+net score; 531df0 920754 meter; 45a920 '{+308}' template; 40e720 via 997b20=HEAP alloc (NONFIELD).
- `python3 -u scripts/m331_ledger_census.py` → **14/14** **442270fd57be2b62** x2 (`evidence/m331_ledger_census.txt:90-91`, `_rerun.txt:90-91`); `python3 -u scripts/m331_mutate.py` → **43/43+1 NO-OP, 0 MISMATCH/CRASH** **29061c567f9132fb** (`evidence/m331_mutate.txt:48-50`); ST 5/5 (`_selftest.txt:6`). Supersedes a9983cddad88fade/75a8749314a13287 (pre-review) + 6b20830198d71116/f69da0b368c0268c (mid-round).
- Review #345 (Strata, `evidence/ai_review/pr345_20261120_022025.md`): **5 P1 + 5 P2, 9 accepted + 1 dismissed** (ACCEPT-row mutant exemption = review_lint L1 meta-rule). ALL fixes STRENGTHEN: owner spill-chain + 8f0d60-context pins (G5); ledger load→store liveness + esi entry→ledger + no-mid-branch (G8); caller loop-index law incl retry-dec (G6); scanners upgraded to ALL store mnemonics + implicit writes (mul/imul/cdq/stos/xchg...) — MU41-43 are the scanner mutants; facprofile id byte-tied to M324 save carry 596ec3/ec8/ed6 (G7); NAMED cites full paths; trim sha1 label fixed (true sha1 429295c00401). MU18/19 first-round + MU36 cascade ({G1,G5}) fixed by pins/declared-set.
- PITFALLS: 8f0d60 = base_rec pointer (M311), NOT a faction profile; 997b20 is heap (5be090) — +308 offset coincidence; 8f0c74's store lacks DWORD PTR prefix; mov-only slot/store scanners miss add/shift writes (review #345).
- OPEN: income nouns; 4e9880 formula; 8f0d40 law; block+0xc0/+304; what the ≥50 cap gates; 920754.

## Session 311 (2026-11-21, M332 CLOSED, STATIC zero box) — `ds:0x985aec` = the runtime MIRROR of the win-INI pref `"Difficulty"`

- m332 off main (B27 `1db42cf`, M331 `aeb02bf`); pick (x2); addresses in `## M332`.
- ANSWER: FUN_0058e7f0 is the private-profile READER (a 6-arg `GetPrivateProfileStringA` per preference) and the `"Difficulty"` window stores exactly ONE key-exclusive field (`ds:0x92bde8`); FUN_0058f0d0 is the WRITER (8 argc-4 pushes == the 8 `WritePrivateProfileStringA`) and pairs that key with the cell's load. All 4 stores of 0x985aec are `a3` moffs: 2 copy the master, 1 `movsx`es the byte cell 0x8f0c11. By-product: the pref table = 11 injective name->field pairs in `0x92bde8..0x92bf14`; `## M328`'s "mode global" `0x92bdf8` = `Top Menu`.
- IN PLACE: `## M308`'s "0x4ddcf1 UNATTRIBUTED" closed: no fall-in (prev = `ret`) but branch-entered by a `jge` whose eax is callee 0x5f1394's return; 0 image-wide LE-dword entries at any site. RIVAL KILLED (G8): the cell is ALSO exactly the end of the 4x0xd4 array at 0x92ba98, so "array sentinel, mirror by coincidence" fails — the cell has 2 stores/6 loads, the sentinel 0.
- ACCEPT `python3 -u scripts/m332_difficulty_census.py` -> `PASS M332: 8/8 gates` digest `c722bc1eca0b6405` (`evidence/m332_difficulty_census.txt:86-87`, 3 runs identical); HARNESS `python3 -u scripts/m332_mutate.py` -> `PASS HARNESS 18/18` (16 scored + 1 NO-OP, 0 MISMATCH/CRASH) digest `f101d888d93c5272` (`evidence/m332_mutate.txt:19-21`); `--selftest` 5/5.
- PITFALLS: (a) objdump prints a jcc target as the WHOLE operand string — `dst,src=split_ops(ops)` puts it in `dst`, so reading `src` finds ZERO branch targets and all 4 live stores looked unreachable. (b) a byte-level `find()` of a LE displacement also hits a `call rel32` whose offset is that value (enc 11 vs text 10 for 0x92bde8) — scanners must be able to DISAGREE. (c) the anchor IS the law: reader's store FOLLOWS its call, writer's load PRECEDES its push (MU15 -> G6+G7). (d) `0x92bde8..0x92bf14` is ONE struct, not 11 globals.

## Session 312 (s312-chain1, REVIEW ROUND on PR #346 / M332, STATIC, zero box)
The local Strata review posted 10 findings (3 P1, 7 P2), `evidence/ai_review/pr346_20261121_195950.md` (14,738/16,384 completion tokens, NOT truncated). Every one was triaged by **tightening the instrument, not the prose**: new gate **G9** (six sub-measurements), 4 new mutants MU18-MU21, new selftest row ST6. `python3 -u scripts/m332_difficulty_census.py` -> `PASS M332: 9/9 gates`, digest `d2691dc5abb39240` (`evidence/m332_difficulty_census.txt:110-111`); `python3 -u scripts/m332_mutate.py` -> `PASS HARNESS 22/22` (20 scored + 1 NO-OP inert, 0 MISMATCH, 0 CRASH) digest(rows) `a9a944201849d026` (`evidence/m332_mutate.txt:23-25`); `--selftest` 6/6.
- **RETRACTION (P1, fixed in place in `## M308`)**: "0x57c7b5 is a CO-STORE of the same eax (0x57c7b0, no intervening write)" was FALSE of the master cell — 0x57c7b0 *is* a store to `0x92bde8`, 5 bytes earlier in the same pair. What is true, and now READ by G9.3: the pair is adjacent, both `mov ds:cell,eax`, and there are 0 writes to eax since the `call 0x406720` at 0x57c7a2. A register-level law was written as a memory-level one.
- **CORRECTION (P2)**: the "three independent views" number. The s311 Ghidra map MERGED both function bodies; the writer body contributes **0** exclusive name->field pairs, so the 7th three-way key was merge pollution. Honest count now: **6 three-way names, 6 fully agreeing** (`:68`). That proximity pairing also slips twice — 0x92bf10 keys `Time Controls`, 0x92bf0c keys `00000000` — now pinned by G7 instead of hidden.
- **MEASURED, previously assumed**: API identity — argc-6 call count in FUN_0058e7f0 = **18** = Ghidra's 18 `GetPrivateProfileStringA` there, all through the one indirect callee `edi`; argc-4 through `edi` = **8** = Ghidra's 8 `WritePrivateProfileStringA` (G9.5). The 0x4ddcf1 edge = `call 0x5f1394`@0x4ddb53 + `test eax,eax`, 0 eax-writes before `jge 0x4ddcf1` (G9.2). cmp arms exactly {1,2,3,4} immediate + exactly {ebx}, ebx unique @0x4f9b5a (G9.1). All 6 copy windows: 0 register redefs AND 0 writes to the source cell (G9.4). Both array-end cmps sit in a loop with one `add reg,0xd4` above and one backward `jl` below (G9.6).
- **NARROWED (P1)**: "no undisguised writer exists" -> no writer that *names* 0x985aec; a store through a runtime-computed register pointer is invisible to both scans (said in the G1 detail and the row).
- **PITFALL**: adding a gate moves every pre-existing mutant that touches the same fact — MU1/2/3/7/8/13 all redden G9 too (each reason is a comment; declared sets updated, not the gates weakened). And `scripts/m332_named_rotate.py --verify` (new) exposed that the archive's recorded sha1 `4dc92495311e` was NOT reproducible once rotate2 appended to the same file: the hashed region has to stop at the `§rotation-2` marker.

## Session 313 (s313-chain1, DOCS CAP SPLIT, zero box, zero measurement)

- Ran FIRST because both docs were at the line: `NAMED.md` 246,504/250,000 (3,496 B headroom, UNDER the 5 KB trigger) and `NEXT_PROMPT.md` 11,986/12,000 (14 B — a milestone may not start on the doc it has to write into). Both moves are scripted + hash-asserted, not hand-edited.
- Rotation: `python3 -u scripts/m333_named_rotate.py` moved `## M259-M261` (3,972 B, the oldest still-full pre-mutation-law block) VERBATIM to the NEW `docs/named-archive-m333-rows.md` and left a one-line-per-claim stub; `--verify` -> `PASS rotate-verify: NAMED stub cites sha1 f78e7ef04359, cites the archive, and the region re-hashes byte-exact` (region 3,972 B, re-read BOUNDED BY A TERMINATOR LINE, not to EOF — the s312 defect). NAMED 246,504 -> **244,756 B** (headroom 5,244, still thin: rotate again before the next block).
- NEXT_PROMPT trim: `python3 -u scripts/m333_nextprompt_trim.py` moved region-A (the closed pick rows v/vi/vii/viii/x2/x3/x4 + the B27 row, 1,733 B, sha1 `8332dd50ba16`) and region-B (the result one-liner pointers, 508 B, sha1 `6f2ddbe32478`) VERBATIM into `docs/pick-archive.md` §trim-s313-chain1; `--verify` -> `PASS trim-verify: both regions re-hash byte-exact against the pointers in NEXT_PROMPT.md`. NEXT_PROMPT 11,986 -> **10,789 B**. The OPEN leads ((x1)/(x5)/(x6)) and (ix) were kept ON PURPOSE and the script asserts the tokens `0x984d48 / bit5 halves / 92bdf8 / 0x8f0090 / 0x5f1394 / (ix)` survive the trim — a cap split that hides the next pick is worse than the cap.
- PITFALL: `%`-format arity — two of the appends raised `TypeError: not all arguments converted` (7 args / 6 specifiers). The rotate script died BEFORE writing, so no partial archive; the guard is the `assert` + the append-after-hash ordering.
- Registry kept honest: `## M259-M261`'s retraction of M240's "two 22-byte map columns" AND M262's retraction of M260's "the ~140 KB views are not allocated" stay IN the stub, not only in the archive (AGENTS.md invariant).
- **REVIEW ROUND #347** (local Strata, `evidence/ai_review/pr347_20261121_220218.md`, 10 findings, 15,042/16,384 tok, NOT truncated): **all 10 accepted, none dismissed — 9 were defects in the instruments, 1 in a shipped tool.** `--restub` + `--relabel` were added so the fix is PRODUCED by the scripts, not hand-typed. Re-measured after the last edit: rotate `PASS rotate-verify: stub cites :6 + sha1 f78e7ef04359, the region re-hashes byte-exact, the stub equals the STUB constant and no copy came back`; trim `PASS trim-verify: both regions re-hash byte-exact against the pointers in NEXT_PROMPT.md, both tags unique, every open-lead phrase still in the hot file`. NAMED 245,072 B (headroom 4,928 — STILL under the 5 KB trigger: rotate before the NEXT block), NEXT_PROMPT 11,355/12,000.
  - F1 P1 ACCEPT: the `(ix)` survival assert read the WHOLE hot file while the sentence that explains (ix) had just been archived — a passing assert proving nothing. The hot text now carries `**NO STATIC PICKS LEFT** except **(ix)** (live-box, operator-GATED)` and the asserts name exact phrases (`MUST_KEEP`), so the trim can no longer pass on a file that lost the pick's meaning.
  - F2 P1 ACCEPT: region-B was marker→EOF — exactly the hash-to-EOF class the PR claims to fix; now paragraph-bounded and it REFUSES to run if any non-whitespace follows the marker.
  - F3/F10 ACCEPT: the stub cites the shipped byte-read (`evidence/m259_m261_census.txt:16-17` prints `immediates naming 0x224b8: 0; 4-byte LE pattern ... offset -1`; `:20-21` the 0x23bec-vs-stride compare; `:30` SUMMARY 14/14) instead of pointing at a bare filename.
  - F4 ACCEPT: verify now pins `docs/named-archive-m333-rows.md:6` as a LINE the stub must cite and re-derives it, prints the FULL sha1, and asserts the stub is byte-identical to the STUB constant — re-wrapping the archive above the marker reddens verify.
  - F5 ACCEPT: the M260 correction cites M262's own rows (`docs/named-archive-m332-rows.md` G2, `evidence/m262_m264_census.txt:24`).
  - F6 ACCEPT: region-A holds the closed rows AND the superseded open-lead census; the tags and the hot pointer now say so, and the pointer states the archived census is superseded.
  - F7 ACCEPT — a defect in SHIPPED tooling: `session_rotate.py`'s pointer said "read the archive only for questions before Session 297-chain2" while the archive holds Session 298 (numbers are per-chain; rotation cuts by file position). The wording now comes from one `index_line()` used by both the rotation and the new `--fix-index`, which re-derived the live pointer from the archive headers on disk: `(2 sessions: Session 298, Session 296-chain2) ... The split is by FILE POSITION, not by number`.
  - F8 ACCEPT: `--restub` located the stub by a bare `## M259-M261` prefix (any table row could match); it now anchors on the unique line that is BOTH that header AND carries `§rotation-1`.
  - F9 ACCEPT: rotate refused to append to an archive that already carried `§rotation-1` — a reverted NAMED edit plus a live archive used to double-archive a region that verify then blessed; now asserted on both sides, and verify counts copies.
- PITFALL worth keeping: `%`-format arity. Two appends raised `TypeError: not all arguments converted` (7 args / 6 specifiers). Both died BEFORE the write, so no partial archive — the guard is ordering (hash in memory, then append, then re-read and compare), not luck.

## Session 314 (s314-chain1, M333 CLOSED, STATIC zero box) — the feeder-slot NOUN and the CARRIED HALF-UNIT

- Pick (x1) (feeder slots `0x984d48+48*item`, the OPEN row of `## M330` G10). ACCEPT `python3 -u scripts/m333_feeder_slot_census.py` -> **`PASS M333: 8/8 gates`** digest `b1ca12715e833cc7`, 2 runs byte-identical (`evidence/m333_feeder_slot_census.txt`); harness `python3 -u scripts/m333_mutate.py` -> **`PASS HARNESS 14/14`** digest `1d36c4eefd86391e`, `--selftest` 6/6 (`evidence/m333_mutate.txt`, `evidence/m333_mutate_selftest.txt`).
- THE SLOT NOUN: a feeder slot is a FACILITY THE BASE HAS — the charge loop takes the cost from the stride-48 item table only when the item's bit is set in the 304-B base record at `base+0x8c` (G3). The loop VISITS ids 1..38 and CHARGES 1..34: the top `cmp esi,0x22 / jg` is a SKIP for 35..38, not the exit; the back-edge is the bottom `inc esi / cmp esi,0x27 / jl` (G1+G7).
- THE BIT5 LAW: block+0 bit5 is a CARRIED HALF-UNIT dedicated to FUN_004f47f0 — read (shr5+and1), added to the cost, `sar 1` charges the quotient, the sum's PARITY is written back into the SAME bit5 (odd remainder survives the round). G5 def-use census: FUN_004f47f0 is the ONLY function image-wide that reads AND writes bit5 of a block+0 value; FUN_004dc390's `or ecx,0x20` is a DERIVED mirror dword (block+0 bits 30/29/20 -> bits 4/5/6) — rival R2 ("shared faction flag") dies on that distinction.
- `ds:0x985ba0` is READ-ONLY in .text (2 loads, 0 stores image-wide) — the G6 gate asserts the measured fact (0 stores), not the wishful `>=1` the first draft carried; writer outside .text, noun INFERRED.
- NEW FINDING (printed, not gated): a REMOVAL path inside the same loop (mapper `0x4f49b6`, bitmap bit-CLEAR `0x4f49e1`, 3 stores to `block+0x220`) — became pick (x7).
- PITFALL (the fold-checker defect this milestone was created to fix): the linear backward value-walker answers `('const',48)` for the item-table read because it finds `mov esi,0x1` and never sees the loop-bottom `inc esi` — it OVER-PROVES `48*1`. The fold is now SHAPE-pinned (`lea r,[i+i*2]` + `shl r,4`, dest/base/index cross-checked against the bound test and the disabled-list cmp). A `value_of` PASS on a loop-carried counter is a PASS on an unmeasured state.
- PITFALL: three regex classes burned rounds — `\b` after `]` never matches at end-of-string (`\[eax\+0x4\]\b`); the lea shape check must compare BASE==INDEX (not dest==base); and a broad `0x20`-anywhere filter inflates a "dedicated field" claim 1->18 (the immediate 0x20 is also the value 32 and a stride step — bit claims need def-use provenance, not text search).
- DOCS: NAMED rotation-2 (`scripts/m333_named_rotate2.py`, M315 5,223 B -> `docs/named-archive-m333-rows.md:54` sha1 `c70cc525ecbd`, own terminator, both rotations verify byte-exact); NAMED 242,113 B (7,887 headroom) after adding `## M333`; NEXT_PROMPT 11,648 B (x1 answered, x7 opened, DOC CAP line re-measured). PITFALL: `§rotation-2` collides with m332-rows' older `§rotation-2` — verify filters on the archive filename too. PITFALL: patch-anchoring on a LINE PREFIX splices the tail of the matched line into the new block — anchor on whole lines.

## Session 315 (s314-chain2, REVIEW ROUND on PR #348 / M333, STATIC, zero box)

- All 10 findings ACCEPTED (3 P1 / 7 P2), none weakened — every fix ADDS a measurement, and each new tie got a mutant (MU11-MU14). Re-acceptance 8/8 digest `70376694feec5815` (pre-review `b1ca12715e833cc7`), 2 runs byte-identical; harness 18/18 digest `dee04978a5b5dd09`, `--selftest` 6/6.
- The three P1s were the project's dominant class in new dress: a claim word ("image-wide") the scan did not cover (F1 — now ALL operand-text mentions of `0x985ba0`: 2 loads, 0 stores, no lea-absolute; the computed-address hole is STATED, noun INFERRED); constants asserted instead of parsed from bytes (F2 — G7 now reads both cmp immediates, `0x750` demoted to context); a shape-pin that checked the fold but never tied it to the read it explained (F3 — shl-dest == read-base, mutant MU14).
- The P2s were all "counted but not connected": the tie rows (tested-bit -> mapper out-slots `[ebp-0x8]`/`[ebp-0xc]` MU12; `own_src`->`xor ebx,ebx`->`mov bl`->fold leaf MU13; `xor edx,edx`->`mov dl`->`cmp edx,ebx` MU11) turn existence proofs into identity proofs. The remaining identity `ebx`==charged-base owner is now stated INFERRED, not claimed.
- F6: the def-walk stops at ADDRESS DISCONTINUITIES too, and the gate prints the measured gap per the M315 law: 2 of 168 block+0 sites (`51da8e`/`51da95`) sit in unclaimed regions.
- PITFALL: an adjacency check ("immediately before") is too strict when the compiler interleaves (`shl ecx,0x4` sits between `xor edx,edx` and `mov dl,...`) — assert "no write to the register in between" instead.
- PITFALL: a restub placeholder mapping inverted ARC_LINE/MARKLINE — verify's `cite == marker+2` assertion caught it on the first run. A verifier that pins the cite earns its keep; one that pins only the marker does not (F10).
- rotate2 gained `--restub`; the pre-existing hardcoded ROOT in rotation-1 got the same derive-from-`__file__` fix (F8); both verifiers re-run green.

## Session 316-chain2 (2026-11-23, M334 CLOSED, STATIC zero box) — the upkeep-FAILURE branch is a difficulty-gated AUTO-SELL

- milestone/m334 (main 497d766). Pick (x7) = the REMOVAL path M333 printed but did not gate. `python3 -u scripts/m334_powershort_census.py` → **`PASS M334: 7/7 gates`** digest **5b5ece39af02baba**, 2 runs byte-identical (`evidence/m334_powershort_census.txt:56-57`, `_rerun.txt:56-57`); harness `python3 -u scripts/m334_mutate.py` → **`PASS HARNESS 45/45`** digest **a5a5091e533f7883** + coverage 10/10 items (`evidence/m334_mutate.txt:47-49`, `_rerun.txt` identical); `--selftest` **6/6** (`_selftest.txt:8`).
- LAW: after `ENERGY -= cost` (0x4f4952) / `+300 += cost` (0x4f4962) through one derived 8380*owner fold, FUN_004f47f0 RE-READS ENERGY and tests vs 0 (`xor eax,eax`@0x4f4960 = the zero source, `jge`→next item). Negative side = 3-way dispatch: A `cmp [block+0x8],1` → `ENERGY:=0`@0x4f497f; B `cmp [base_rec+0x50], neg(item)` → `ENERGY:=0`@0x4f4999; C = the SELL: clear the item's bit in the CURRENT base's facility map (0x4f49e1), `ENERGY := FUN_004e40a0(owner,1,-1) × row[item]+12` @0x4f4a0b, `FUN_006265a2(1,row+0,-1,-1)`, `FUN_0048f100('POWERSHORT',0x10000,0xe,'genwarning_sm.pcx',0)`; loop CONTINUES (back-edge 0x4f4a3b→0x4f480b) ⇒ several facilities can go in one round.
- **RETRACTION**: the s-era row `docs/named-archive-m32-m84e.md:268` said "refund = 0x4e40a0 × refund table 0x984d44" — the multiplication is right, the WORD is wrong: the store is a MOV with **0 reads of block+0x220** on that path (`:28-29`, `:40`) — an ASSIGNMENT, not a refund. Row patched in place; RIVAL1 + MU16 (turning it into `add` reddens G5+RIVAL1).
- **NEW NOUN**: `block+0x8` = the faction's EFFECTIVE DIFFICULTY — 2 destination-named writers + **0** folded-pointer stores (60-step def walk, MU26 proves the scan): create 0x59eed6 stores `ds:0x985aec` for a human / imm 3 for the AI (gated `test dl,ds:0x985b10`), save-load 0x57ef57 stores a movsx byte through 2095*4=8380 ⇒ **difficulty < 2 never sells** (M332's difficulty mirror finally has a per-faction consumer).
- PITFALL: an operand-text grep for an absolute VA misses stores through a FOLDED block pointer (`lea R,[k*4+0x94d430]` then `mov [R+8]`) — the census now runs both scans; PITFALL: the affine tracker's coefficient is `a` in `a*seed+b` (printed 0 once when `[1]` was read instead of `[0]`), and `shl` scales by `1<<imm`, not by the immediate.
- OPEN: `row[item]+12` runtime value (the 39×48 table is .bss — no .text store names it) ⇒ the numeric ENERGY outcome; `base_rec+0x50` = queue head is INFERRED (archived live H :312; 51 .text sites read [R+0x50] with R:=ds:0x8f0d60 incl. 0x4f4994); FUN_004e40a0 = ECONOMIC FACTOR (archived H); why the price is assigned rather than added.

**Review round, PR #350 (Strata, 10 findings: 4 P1 + 6 P2 — ALL accepted, 0 dismissed).** The same
class as #345: prose that claimed more than the gate read. Every fix ADDS a measurement + a mutant:
F1 mapper-item identity (`push esi` / `push ecx`←`[ebp-0x4]`, the slot the loop bottom writes from
esi) → MU27/MU28; F2 the factor's args + owner-byte source → MU29/MU30; F3 the full cdecl arg lists
of both announcement calls + the row+0 edx tie → MU31/MU32; F4 the human/AI gate
(`mov al,ds:0x985b10` + `test dl,al` + `jne 0x59eed6`) is now measured and printed (`:17`) → MU33;
F5 the "0 reads" window is now stated exactly (sell path AND from the negative test, both 0, `:29`);
F6 a FOLDED-pointer read census (`folded_refs_to`, dest-normalized def walk) — 0 folded refs to
block+0x220 in-fn and image-wide, with a **non-zero control**: 10 folded refs to block+0, so the
scan is not vacuous (`:38`) → MU34; F7 the clamp stores' source register + 0 intervening eax writes
(`:10`) → MU35; F8 fold→imul-base→dest→store-source dataflow (`:25-28`) → MU36/MU37; F9 the save/load
fold is tied to the actual `[ecx*4+0x94d438]` store and its edx source (`:18`) → MU38; F10 the
address-register write scan now normalizes partial regs and `xchg` (`:37`) → MU39. Re-measured at
head: **7/7 digest `5b5ece39af02baba`** x2, **harness 45/45 `a5a5091e533f7883`**, ST 6/6. Two
declared sets corrected to the MEASURED truth, not weakened: MU25 GREW to {G6,RIVAL3} (pinning the
full memo arg list made it a G6 mutant too) and ME3 to {G4,G7,RIVAL2}. PITFALL: a mutant that
empties a list crashed the printer (`load_fold[0]` on None) — a CRASH is a harness failure, so
printers of measured values need the same None-guard as the gate.

## Session 316-chain2 sidecar (2026-11-23) — M334 merged + evidence completion

- **M334 MERGED as `fc2569d`** (PR #350, squash; CI `gate pass 15s` verified on the post-review head
  BEFORE merge; review triaged 10/10 accepted, 0 dismissed, one reply comment
  `#issuecomment-7102934036`; title REST-patched to the post-review numbers and read back). Merged
  tree == the reviewed head (`git diff --stat HEAD origin/main` empty).
- Evidence completion: `evidence/ai_review/pr350_20261123_131041.json` (the raw review payload) was
  left untracked when #350 merged — the repo convention is both `.md` and `.json` per review
  (24 json / 25 md before this). Added here; no claim changes, no re-measure needed (the instrument
  and its digests `5b5ece39af02baba` / `a5a5091e533f7883` are untouched).

## Session 316 (s316-chain1, B28 BUILD rung, zero box) — the UPKEEP FEEDER made EXECUTABLE; the container's own `+300` octet IS its full-price total

- track_mode said MODE=BUILD next_rung=B28 and the spine ended at B27, so §B28 was authored in `BUILD_SPINE.md` BEFORE implementation (commit de6a0ee), then built: `sim/feeder.py` = the law, `sim/composedfeeder.py` = the run + gates, `--b28` relays.
- ACCEPT `python3 -u -m sim.selftest --b28` -> **`PASS B28: 8/8 gates`** digest(rows) `705a4520c08c4062`, print_digest `8c87e05ffa2b80cc`, final container `38bba29ab857654b`, 2 runs byte-identical (`evidence/b28_feeder_exec.txt:18-19`); harness `python3 -u scripts/b28_mutate.py` -> **`HARNESS PASS 16/16`** digest `a2ba49fb9dd1056b` (12 CODE + 4 EXPECT, exact-set check 0 complaints, gates reddened 8/8, dead mutants [], NO-OP `[]`), `--selftest` 4/4 (`evidence/b28_mutate.txt:19-21`).
- THE FINDING: `ds:0x985ba0` is not a loose runtime pointer — it is CARRIED in the save's state header (`mem2file` → file offset 244) and reads **-1** in `m54b_clean.SAV`, so the 4f48dc sign skip fires and the halving runs 0 times. Executing the loop over the save's own 18 base records reproduces the container's own `+300` octet `[0,1,1,0,1,0,1,1]` **8/8** — but only once the own faction's recorded disabled id (8, parsed out of `docs/named-archive-m32-m84e.md:272`, never retyped) is applied: **7/8 without it**, and the single miss is faction 3 = `own_player`, whose only cost-1 facility IS item 8. Rivals measured: forced-halved 3/8, charge-every-row differs at 18/18 bases.
- The carry is live here: 6 of 8 factions have an odd full-price total; with the gate dword pointed at a base the charged faction owns, bit5 survives round 1 at 5 of 7 fixture factions and moves round 2's charge by exactly 1 at those and only those (`:7`). `block+0` is now a modeled span for this call; `savewriter.modeled_spans()` with no overrides still returns exactly the pre-B27 list and the unmutated build stays the identity.
- PITFALL (the rung's own defect class, caught by the harness): the first G4/G7 computed the price path and the totals with INLINE re-typings of the law (`sel >= 0 and owners[sel] == f`), so MU6/MU7/MU10 reddened ONLY the digest gate — a gate that re-derives the law instead of CALLING it measures nothing. Fixed by routing every number through `feeder.price_path` and adding two ties: run-vs-law (8/8) and "in a one-base fixture every OTHER faction stays at full price" (0 pairs).
- PITFALL: `owner_bytes[-1]` is Python's LAST element, not "nothing selected" — a dropped sign skip silently reads the last base's owner instead of failing (now measured, MU6).
- PITFALL: a printed-table digest that hashes the line printing its own anchor can never be re-pinned — the G8 line is excluded from the hashed region.
- DOCS: NAMED rotation `scripts/b28_named_rotate.py` (M246+M247+M248/M249, 3,507 B → `docs/named-archive-b28-rows.md:10` §rotation-1, sha1 `fcd4989fdf15`, own terminator, `--verify` byte-exact); NAMED 246,245 → 245,488 B BEFORE the `## B28` add — still under the 5 KB trigger, rotate again next fire. NEXT_PROMPT 11,798/12,000 (added (x8) = the item-table row-order lead; paid by trimming the stale §trim-s269(b) pointer, the CLOSED-enumeration sentence and the BOX last-touch parenthetical).

## Session 317 (s316-chain1, REVIEW ROUND on PR #351 / B28, zero box)

- All 10 findings (3 P1 / 7 P2) answered IN THE GATES; no threshold weakened, none dismissed. P1(a)'s premise was half wrong (the full-price path never reads the carry) — the zero-carry baseline is now MEASURED by an all-ones carry-seed tie.
- ACCEPT `python3 -u -m sim.selftest --b28` → **PASS B28: 8/8 gates**, digest(rows) `705a4520c08c4062`, print `99c52201f073499d` (pre-review `8c87e05ffa2b80cc`), container `38bba29ab857654b`, 2 runs byte-identical (`evidence/b28_feeder_exec.txt:9`); harness `python3 -u scripts/b28_mutate.py` → **HARNESS PASS 18/18** digest `3974d739da3af55f`, 8/8 gates, NO-OP `[]`, dead `[]` (`evidence/b28_mutate.txt:20-23`); `--selftest` 4/4; both evidence files re-captured, diffed byte-identical.
- G4 ASSERTS the dword from container bytes (offset 244, value -1, offset < block A), not a derived path property; G3 asserts the inert window and runs the SAME scan as a CONTROL over `+0x8c..+0x8f` (nonzero 14/18); G7 asserts the no-list rival at exactly 7/8 with miss `[own_player=3]`; G6 measures exactness over the differing set and measures the HONEST run (touch set `[]`, bit5 unchanged).
- RETRACTION in place: "the carry persists through the writer" is **FIXTURE-ONLY** (`NAMED ## B28` row + spine §B28 qualified); this save's run writes no carry.
- New mutants ME5 (full-price reads the carry-in → G6,G8), ME6 (control window moved → G3,G8); MU6 grew to {G4,G6,G7,G8}. PITFALL: every prose edit re-pins the print digest (`434b…` then `99c5…`).
- Merge: origin/main `c0f5e2a` (M334) merged; BOTH chains' sections kept; main did not touch `sim/feeder.py`, digests unchanged post-merge.
- DOCS: NAMED **248,734 B** (1,266 under the fail line) — headroom UNDER 5 KB: next fire ROTATES M250-M254 before adding a block.

## Session 317-chain2 (2026-11-23) — M335: the difficulty ladder's INDEX->LABEL order

- **ANSWER (pick (x6), first clause):** the six difficulty names are alpha.txt's `#DIFF` rows,
  loaded at `0x57ac56` (`push "DIFF"` -> `call 0x5ea431`) into `0x94d2ac`, one dword per row,
  `add esi,4` up to the hard-coded `cmp esi,0x94d2c4` => 6 rows, file order
  Citizen/Specialist/Talent/Librarian/Thinker/Transcend. `ds:0x985aec` is that index: at
  `0x599405` it loads the label (`mov ecx,ds:0x985aec; mov edx,[ecx*4+0x94d2ac]`), and the
  chooser `0x4ddaf8` walks the table forward passing `push edi` (=k) as the item index, after
  seeding the dialog with `ds:0x985aec` before `call 0x5f1394`.
- **M330 refined, not retracted:** the refund's cmps are `cmp eax,3/jle` (none at <=3) and
  `cmp eax,4/jne` => k=1 at exactly 4 (Thinker), k=2 at >=5 -- with six rows that arm is
  TRANSCEND (index 5), i.e. live, not a hypothetical.
- **New measured oddity:** the only `0x8f0c11`-fed clamp on the index is `FUN_00423af0(lo=0,hi=6)`
  at `0x486f30-0x486f40` (1 of the 169 `call 0x423af0` sites); its hi is INCLUSIVE and equals the
  array LENGTH (`hi*4 == end-base` read out of the bytes), so a difficulty of 6 would read
  `0x94d2c4`, one row past the table. Reachability is OPEN.
- ACCEPT `python3 -u scripts/m335_difficulty_ladder.py` -> `PASS M335: 7/7 gates`, digest
  `fb58bdc3307d6258`; re-run diff-identical (`evidence/m335_difficulty_ladder.txt:9-10`).
  Harness `python3 -u scripts/m335_mutate.py` -> `PASS HARNESS 20/20`, digest `6e0e05a8ffb388d8`
  (includes an ALGORITHM mutant); `--selftest` 3/3 (`evidence/m335_mutate_selftest.txt:4`).
- **REVIEW ROUND (Strata, PR #353): 10 findings (3 P1 / 7 P2), 10 accepted, 0 dismissed.** Fixes:
  G4 became an ORDERED fragment walk (edi starts at 0, seed before `call 0x5f1394`); G2 reads the
  loader's actual store; G3 uses token-boundary matching (+ MU20 algorithm mutant); G5 proves both
  readers are counting loops; G6 READS base/bound/clamp-hi out of the code instead of comparing to
  the script's constants and censuses all 169 clamp sites. MU1's declared set corrected to
  {G2,G3,G6}. Two P2s were about MY doc-cap rotation -- **which is now moot: chain 1 landed the
  same M246-M254 rotation on main as `docs/named-archive-b28-rows.md` (sha1 fcd4989fdf15)**, so the
  duplicate archive and `scripts/m335_named_rotate.py` were dropped in the merge; the P1 rotation
  cite bug it exposed (a key that ate a digit on `## M248/M249`) is recorded above as a finding.
- PITFALL: this census's `gates()` originally wrapped all seven checks in ONE try/except, so a
  vanished site reddened every gate (MU6 measured {G1..G7} instead of {G3,G5}). Per-gate
  try/except is what makes a declared mutant SET measurable at all.

## Session 318-chain1 (2026-11-24) — M337: item table row order = alpha `#FACILITIES` file order, record i = alpha row i-1 (pick x8)

- **ANSWER (x8):** the "39-row item table" at `0x984d48` is the `+0x10` dword of the 72-record array
  at `0x984d38` (M53i). Loader `0x57a7ef..0x57a899` pushes `FACILITIES` (`0x691ccc`) and
  walks `esi = record+0xc`: start `0x984d74` (rec 1), branch `cmp esi,0x985494` (rec 39), `+0x30`,
  end `cmp esi,0x985ac4` (rec 72) => recs 1..71 written, rec 0 untouched; 1 line-read + 1 record step
  per iter => k-th line -> rec k. Recs 1..38 take 6 tokens, 39..71 take 11,
  and alpha's FIRST 11-token row is idx 38 (`The Human Genome Project`, alpha.txt:629).
- **'39' is the consumers' bound** (`cmp esi,0x27` @`0x4f4a35`), not the array size; recs 39..71
  (projects) keep the same order, so B28's +300 parity covers ids 1..38 by construction.
- **Column order (V):** `0x5ea985` takes one comma token per call; all three converters call it, so
  the decoded store seq `+00,+0c,+10,+14,+18,+04,+18,+1c,+2c,+24,+28,+20` is column order =>
  **M53i's `+0x20`/`+0x28` labels are swapped**.
- ACCEPT `python3 -u scripts/m337_item_order.py` -> `PASS M337: 8/8`, digest `39d82f0771690e15`,
  diff-identical (`m337_item_order.txt:90-91`); `scripts/m337_mutate.py` `HARNESS PASS 13/13` incl. NO-OP MU10
  (`evidence/m337_mutate.txt:14`), `--selftest` 3/3.
- **REVIEW (#354, Strata): 10 findings (3 P1/7 P2), all answered IN THE GATES, none dismissed.** G5
  DECODES the 12 stores from the bytes (no hand list); G2 reads the consumer bound (39 != 72); G4
  proves the k-th-line->k-th-record mapping; G7's R2 is a decoded control-flow read and R4 prints a
  computed offset; the table build is input-safe.
- **PITFALL:** `;` starts a comment, so 6 later rows carry tails as text; the loader still reads 11
  tokens and re-syncs per row (`0x5ea448` -> fgets).
- Chain 2 owns `milestone/m336` (wt-chain2); NAMED rotation = M277 ->
  `docs/named-archive-m337-rows.md:8` (sha1 `653c93cda817`, pinned in `m337_named_rotate.py`).

## Session 318-chain2 (2026-11-24) — M336: ds:0x8f0090 = difficulty byte of PLAYER RECORD 1; one UNCLAMPED #DIFF reader

- **ANSWER (pick (x6)):** record 1, byte +2 of an 8-record array at FRAME `0x8eff18`, stride
  `0x176` (end `0x8f0ac8`; rec-1 ptr `0x8f008e`). The ADDRESS census finds ONE reader: `movsx edx,BYTE [ecx+0x8eff1a]` at **0x486788** (FUN_004865c0), ecx = 0x176*(k+1), k =
  `[ebp-0x8]` (0x4865dc/5f5/77c), bound `BYTE ds:0x8f0c10` (4 at
  reset, 0x4e2444) => k=0 is row 0, address == TARGET; the byte feeds `[b*4+0x94d2ac]` (0x48678f)
  (0 gap).
- **6 write sites, 3 forms:** direct 0x48884d; record-indexed 0x487e87/0x525b83 (const=target-1
  rec); walk +2 0x4e24a2/0x525cb9/0x525d28. Sources 0x8f0c11 x3 + lit 0 -- M332's "1 ref, 1
  write" was form-limited.
- **INDEX 6 ADMISSIBLE:** all 6 writers of 0x8f0c11 store unclamped values (pref copies 0x488828/0x484efe, int->byte, literals 2/1); the only clamp on any read is 0x486f30
  `FUN_00423af0(diff,0,6)`, INCLUSIVE (jl/jge/jle), arg = its own register =>
  clamp(6,0,6)=6 => `[6*4+0x94d2ac]` = **0x94d2c4**, the loader's END pointer. OPEN: does FUN_0058e7f0
  (INI reader) admit >=6?
- ACCEPT `python3 -u scripts/m336_cell090_consumer.py` -> **PASS M336: 7/7**, digest
  `f4ca00c55c833539`, 2 runs diff-identical (sha256 bfd16dae81b25723); `python3 -u
  scripts/m336_mutate.py` -> **HARNESS 14/14** `3ec4dd172c69e165`, `--selftest` 4/4.
- **REVIEW (PR #355: 3 P1/7 P2) — 10 accepted, 0 dismissed.** v1's census saw one address form;
  rebuilt as an ADDRESS census (per-block linear-expression eval: base=const+sum(coeff*sym); a site
  counts only if const is field+2 mod stride and all coeffs are stride multiples; unresolved bases
  print as residue, and "only reader" needs residue@+2 EMPTY). New: MU9 algorithm, MU11 walk step,
  MU12 table base, MU13 chain slot, MU14 SECOND alias load INSERTED; the digest hashes PASS bits.
- PITFALL: displacement-keyed censuses miss strength-reduced forms; an O(n) replay per site needs
  a bisect index (180 s).

## Session 319-chain2 (2026-11-24) — M338: the last two #DIFF readers' index provenance

- **ANSWER (pick (x6), final clause):** the seven scaled loads of `0x94d2ac` are now all
  sourced. `0x57c606` (`mov eax,[esi*4+0x94d2ac]`, FUN_0057c550) is a UI list builder: the
  index is the loop counter `esi` — `xor esi,esi` at 0x57c604, the body's only esi write is
  `inc esi` 0x57c6ca, `cmp esi,6`/`jl 0x57c606` -> 0..5, one label per row.
- `0x44a1c8` (FUN_004495e0) indexes with `dl = BYTE[eax+0x20]` (`xor edx,edx` + `mov dl`,
  0 instructions between the load and the index). `eax = [ebp-0x1c]` is a record of the
  **35 x 0x8c buffer at `0x983a10`**, which is **`hallfame.jhh`**: PE strings `rb`@0x689f3c /
  `hallfame.jhh`@0x689f40, `push 0x1324` read, zero-init `5 x 0x8c` per `0x2bc` to `0x984d34`;
  (0x984d34-0x983a10)/0x8c = 35 and 35*0x8c = 0x1324. The record index decodes as
  `(8-1)*(1+4)*4 = 0x8c`.
- **field +0x20 has exactly two writers** in the module: 0x44b15b fills it from
  `BYTE[0x94d438 + 8380*faction]` (fold `shl 6/add/lea*2/shl 4/sub` decoded = 0x20bc; cell =
  faction base 0x94d430 + 8) and 0x44b612 copies it struct-to-struct. `block+8` is the faction's
  **EFFECTIVE DIFFICULTY**: creation 0x59eed6 = `ds:0x985aec` unless the `ds:0x985b10` bit
  selects imm 3; save-load 0x57ef57 stores the save's byte through the same 8380 fold. So the
  reader prints the difficulty NAME of a hall-of-fame entry.
- ACCEPT `python3 -u scripts/m338_diff_readers.py` -> `PASS M338: 8/8 gates`, digest
  `1ae1563d47d0039e`, 2 runs `diff`-identical (sha256 `288a0edc`; `evidence/m338_diff_readers.txt`
  + `_rerun.txt`, 67 lines). Harness `python3 -u scripts/m338_mutate.py` -> **16/16 scored, 0
  MISMATCH, 0 CRASH**, digest `56455db0eadbedd7` (now hashes the MEASURED rows, not the label
  map), incl. REMOVAL/INSERTION/ALGORITHM and the review's MU13-MU15; `--selftest` 3/3
  (`evidence/m338_mutate_selftest.txt:4`).
- **REVIEW (#357, Strata): 10 findings (3 P1/7 P2), all accepted, none dismissed — fixed IN the
  gates**: G4 now asserts the store's SOURCE is eax and no eax clobber before it (MU13); G6's
  module is MEASURED as the 7 functions addressing 0x983a10 (not a typed window); G7 asserts the
  exact 6-instruction branch incl. `jne 0x59eed6` (MU14); G2 reads the loader's base/step/bound
  instead of constants; G5 asserts the fopen/read windows and the exact zero-init sequence; G3
  asserts the full window and no eax clobber (MU15); the esi write classifier is broad
  (lea/pop/xchg/cmov); the harness digest hashes measured outcomes.
- **OPEN:** the +0x20 index is UNCLAMPED (unlike 0x486f40's `FUN_00423af0(0,6)`) — a HoF record
  byte >=6 would read past `0x94d2c4`; whether the INI reader admits a pref >=6 is still open
  (M336). Also OPEN: is 0x44a1c8's big function the HoF screen itself or another list view.
- **Docs:** NAMED cap 247,758 -> **245,265** by rotating `## M326` VERBATIM to
  `docs/named-archive-m338-rows.md:7` (sha1 `a882ee40851d`, pinned in
  `scripts/m338_named_rotate.py --verify`), then +M338 -> 248,542. NEXT_PROMPT got one appended
  result line (chain 1's file is append-only for chain 2).
- PITFALL: a fold decoder keyed on the exact disassembly string crashes on the mutant that
  changes one immediate — decode the immediates and let the gate FAIL instead of asserting the
  text shape.

## Session 319-chain1 (2026-11-24) — B29: the item table DERIVED through M337's loader law

- **ANSWER:** `sim/itemtable.py` replays `0x57a7ef..0x57a899` over `data/alpha.json`: 72 records,
  branch rec 39, 71 iterations, token widths 42/2/27 — all four parsed out of the M337 census and
  REPRODUCED from the file (G2). The derived table equals `sim.economy.upkeep_table` on 38/38 ids
  by name AND upkeep, so `ALPHA_SHIFT = 1` is now a CONSEQUENCE of the loader, not B4's assumption
  (G3; the shift-0 rival differs 22 ids by value and 38/38 by name).
- **B4's four `table-later` DIFFERS rows CLOSED as a convention artifact:** read at the ALPHA
  INDEX the derived table reproduces all four M46 values (Fusion Lab 4, Nanoreplicator 4, Quantum
  Converter 6, Quantum Lab 3), at index+1 zero of four — M46 numbered its rows by alpha line (G5).
  The same convention puts the wrong NAME at all five ids B4 pinned, so one convention cannot
  explain both sets.
- **BOUNDARY:** records 39..71 (33 past the branch) are built and unreachable — the feeder's
  bounds 1..34 charge 0 of them; consumer bound 39 == the branch (G6).
- ACCEPT `python3 -u -m sim.selftest --b29` -> **PASS B29: 9/9**, rows `e4b1c98e68ff8685`,
  print `377094bc16aa8f27`, table `fa829fcd87cf43d5`, alpha sha `bac04f33eb692085`, 2 runs
  byte-identical and the direct entry prints the same text (`evidence/b29_item_table.txt:85-86`);
  `scripts/b29_mutate.py` -> **HARNESS PASS 9/9** `ae1f8e0292a59ed3`, NO-OP `[]`, ST 4/4
  (`evidence/b29_mutate.txt:10`).
- **REUSE:** B28's whole run fed the DERIVED table reproduces its anchors `705a4520c08c4062` /
  `99c52201f073499d` / `38bba29ab857654b` with honest touch `[]` (G7) — nothing loosened.
- NAMED headroom: M334 block rotated VERBATIM to `docs/named-archive-b29-rows.md:5`
  (sha1 `579f90da7d8c`, `scripts/b29_named_rotate.py --verify`); B4's OPEN row and B27's UNMODELED
  row patched in place (the row order is alpha's).
- PITFALL: a value-only rival does NOT discriminate on the five pinned rows (upkeeps 0,0,1,1,1);
  the NAME is the discriminator and G4 prints the rival's 3/5 so the gap is measured, not hidden.

## Session 320-chain1 (2026-11-24) — M340: FUN_0058e7f0 ADMITS a `Difficulty` pref >= 6

- **ANSWER:** the Difficulty path in FUN_0058e7f0 clamps NOTHING. Of its 18 six-arg profile
  reads exactly one carries key 0x692718 = PE `"Difficulty"` (0x58e8a1), default = the itoa(0)
  buffer (push 0x0 @0x58e865), value stored `ds:0x92bde8,eax` @0x58e8c6 — the only store to
  that cell in the function. Insns 0x58e8a9..0x58e8c6 are straight line and eax there IS
  0x6287e2's return (wrappers 0x5ea484/0x5eaa53: 0 jcc, 0 eax write after their call).
- **The chain compares CHARACTER CLASSES only** (atoi 0x64c360, tokeniser 0x5ea985, radix
  0x6287e2/0x628720/0x62876b): constants {0x0,0x1,0x2b,0x2c,0x2d,0x30,0x31,0x36}, and the
  intersection with the value space {2..6} is EMPTY (G4).
- **POSITIVE CONTROL:** the SAME function's `Language` consumer 0x628130 IS bounded —
  `cmp [ebp-0x4],0x4` + `ja` + jump table. Same classifier: bound 4 there, none here (G5).
- **CONSEQUENCE:** 6 rows measured from the ladder's loop bound (0x57c6cb `cmp esi,0x6`);
  k=5 -> 0x94d2c0 last legal, k=6 -> 0x94d2c4 == TABLE_END; the three pref-fed readers
  0x48678f / 0x44a1c8 / 0x599405 index TABLE at scale 4 from MEMORY loads, no clamp (G7).
- ACCEPT `python3 -u scripts/m340_pref_admission.py` -> **PASS M340: 7/7**, rows
  `1cc44d0146a8b419`, census `a7bb50fde374ddca`, window `1ff9a31080ec2e22`, 2nd run
  diff-identical (`evidence/m340_pref_admission.txt:79-90`); `scripts/m340_mutate.py` ->
  **PASS HARNESS M340: 12/12**, 7/7 gates covered, NO-OP `[]` `a2a1726721114b4d`
  (`evidence/m340_mutate.txt:16`), `--selftest` OK.
- **REVIEW #358 (local Strata, 10 findings: 3 P1 / 7 P2), ALL fixed in the gates:** G1 now
  measures the argc-6 push window + the 0x997120 lpDefault (MU10/MU11); G2 pins the cursor
  store cell; G3 proves the call chain 0x58e8b9 -> 0x5ea484 -> 0x5eaa53 -> {0x5ea985,
  0x6287e2} (MU9); G5 reads the whole Language switch shape (argument -> slot -> cmp 4 -> ja
  -> table), not just a stray cmp; G6 MEASURES both endpoints from 0x57ac74/0x57ac88; G7
  proves a def-use gap with no branch/call/compare/rewrite; `m340_named_rotate.py --verify`
  also asserts the full block is gone from NAMED; the M332 stub cites both evidence files and
  says 9/9; the sessions-304-305 archive pointer is repaired.
- **ID:** `milestone/m339` is chain 2's worktree branch (~/reverse/wt-chain2), so this fire
  took M340. NAMED headroom: M332 rotated VERBATIM to `docs/named-archive-m340-rows.md:5`
  (sha1 `3ef265e11aca`, `scripts/m340_named_rotate.py --verify`); M335/M338 OPEN rows
  patched IN PLACE.
- PITFALL: a sub-register write (`mov dl,BYTE PTR [eax+0x20]`) is not "a write to edx" to a
  first-operand test — widen to the register family or the def-use gate finds the earlier
  `xor edx,edx` and reads a bounded index as unclamped for the wrong reason.

## Session 320-chain2 (2026-11-24) — pick (x6): `0x5f1394` = the modal SCREEN RUNNER

- **ANSWER:** `FUN_005f1394` (11,207 B / 2,235 insns, `ret 0x8`, args = only
  `[ebp+0x8]`/`[ebp+0xc]`) is a modal-screen runner: SEH `0x66f786`, `sub esp,0x38c`, first
  `call [vtbl+0x170]`@0x5f13c6 with 0 -> `or eax,-1`; then CREATESTRUCT + `0x5e3ed9`, error
  returned VERBATIM.
- **RETURN (7 exits, one `ret 0x8`):** -1 x2, 0 x1, passthrough x2 (traced to their feeders
  `[vtbl+0x15c]` and `0x5e3ed9`), `ds:0x698d0c` x1, and **`[obj+0xa40]` x1** (0x5f3f45) — the
  only value-carrying exit; `+0xa40` is READ once and WRITTEN 0x in the body.
- **PAYOFF (closes M308's `0x4ddcf1` UNATTRIBUTED / M332's row):** `FUN_004ddaa0` stores
  `ds:0x985aec` into obj+0xa44 (0x4ddb3e/4d; the store is adjacent to the call, receiver = the
  same lea 0x4ddb47), calls the runner (0x4ddb53), and on `jge 0x4ddcf1` writes the return to
  `ds:0x985aec` + `[ecx]` each `add ecx,0x20bc` from 0x94d438 to 0x95da18 = 8 factions.
- **CENSUS:** 94 thiscall sites — 76 `lea ecx,[ebp-…]`, 14 pointer, 3 register, 1 global
  0x9210a8. **RIVAL killed:** "chooser" — 0 refs to 0x94d2ac/0x985aec inside vs 3 in the caller.
- ACCEPT `m339_modal_runner.py` -> **`PASS M339: 7/7`** `d76a5e83770b77bb` x2, `text_sha256`
  `eb9f463e…`; `m339_mutate.py` **13/13** `927a1c66c322709e`, ST 3/3.
- **Review #359 (10/10 fixed in the gates):** G0 extent (MU9), G2 exits = jumps to the ONE
  SEH-restore label + feeders traced, G4 exact census, G5 faction store/back-edge/receiver,
  G6 caller extent from the index; ALG_A1 fallthrough-only; the run prints `text_sha256`.
- **OPEN:** who writes `[screen+0xa40]`; 0x57dd45 pushes ONE dword vs `ret 0x8`; `DoModal`
  INFERRED.
- NAMED: `## M308` rotated VERBATIM to `docs/named-archive-m339-rows.md:8` (sha1
  `07cec1770614`, `m339_named_rotate.py --verify`): 249,287 -> 243,834 -> 246,196.
- PITFALL: objdump prints `[ebp-0x4]` and `DWORD PTR [ebp-0x4]` alike; long immediates
  leave 3 trailing bytes on their own line (14 gaps) — normalise both.

## Session 321-chain2 (2026-11-24) — pick (1): the HoF record-window page arithmetic (PR #361)

- **ANSWER:** the 0x983a10 record index is `5*n - 5 + s` at THREE .text sites:
  SITE A 0x449793/96 (n=[obj+0x59f4] @0x44970f, s=[obj+0xa918] @0x449715), SITE B
  0x44af9b/9e (n=[obj+0xa4c] <- ds:0x91b5b4 @0x44aeb9/0x44aed9, s from the 5-probe
  rank scan), SITE C 0x44b5a7..b9 insert-shift (src 5n+k-5 -> dst 5n+k-4, k in 0..3).
- **BOUND:** five zero-init/fault sites all measure base 0x983a10, stride 0x8c,
  inner 5, term 0x984d34 => 0x1324 = 35*0x8c = 7*0x2bc; {1..7}x{0..4} is a
  bijection onto 0..34 and index 35 lands ON the terminator: the buffer is
  7 blocks x 5 rows, not a flat 35-list.
- **NO CLAMP:** over 781,379 parsed insns the only direct 0x59f4 ref is the load
  0x44970f; all 12 further hits print as `[reg+reg*4+0x59f4]` (a different array);
  0 cmp/test on ebx between the load and the lea => the page's legality is its
  writer's job, and no named .text store to it exists (OPEN).
- **6 IS NOT ROWS:** six probes {1,2,4,8,0x10,0x20} at {0x449915,0x449985,
  0x4499f1,0x449a5c,0x449ac8,0x449b34} on byte +1 of ONE record (one ebx def:
  `mov ebx,[ebp-0x1c]` @0x449982).
- ACCEPT `m341_hof_window.py` -> **`PASS M341: 11/11`** `1cfdea39295dadce`, two runs
  diff-identical (`evidence/m341_hof_window.txt:45-58`); `m341_mutate.py` **19/19**
  `e1c003e81552f53f`, ST 4/4 (`evidence/m341_mutate.txt:21`).
- RIVALS (review-round fixed): R1 0-based page covers 0..34 as well, so bounds do
  NOT discriminate — it dies on the decoded const -5 (MU2); R2 a coherent 6-row
  page (step 6, 6 pages) reaches index 35 = terminator (MU3); R3 flat list needs
  coef_n == 1, all three sites decode (5,-5) (MU11); R4 base 0x983984 ends at
  0x984ca8 (MU4).
- NAMED: `## M338` rotated VERBATIM to `docs/named-archive-m341-rows.md:5`
  (sha1 `b82cddad74c8`, `m341_named_rotate.py --verify`).
- PITFALL: decode chains must track EVERY lea destination AND `sub reg,reg` —
  SITE B is a two-register chain (edx=slot+4n, then esi=n+edx-5), SITE C's source
  lands in edx (not ecx) and its address chains are formed by *8/sub/*5/*4. The
  address-chain eval must use the INDEX symbols (edx/ecx), not the (n,k) symbols.
- MERGE STATUS: PR #361 is OPEN with a green LOCAL gate at head; GitHub created ZERO
  workflow runs after 03:40Z (empty commit + PR close/reopen did not fire `gate`), so
  the standing "gh pr checks PASS" rule cannot be met. Left unmerged on purpose.
- PITFALL: `690k` insn counts are parser-dependent — the count is len(image()),
  printed, never hardcoded from an earlier session (790,695 vs 781,379).
- MERGE RESOLUTION (2026-11-24, round 3): the zero-runs blocker was the PR state, not the
  workflow — GitHub does not schedule `pull_request` runs while `mergeable_state=dirty`.
  Merged origin/main (a0aa8fc, #362 restores the 34 NAMED blocks) into the branch keeping
  BOTH chains' sections; push re-arms the run.

## Session 321-chain1 (2026-11-24) — B30: the COMPLETION leg executable (queue item -> +0x8c -> writer -> reload -> bill)

- **ANSWER:** a paid queue item becomes a facility the base HAS. `sim/composedfacility.py`
  reads the completion from the container's OWN queue (18 records, own player 3, 2 eligible;
  target base 0 'University Base', item 2 'Children's Creche', rule delta 1), applies the
  reader's inverse (byte `item>>3`, bit `1<<(item&7)`), and the write is ONE byte: diff
  `[140]` = `0x8c+0`, delta 4. The writer carries it (`base_writes=`, B30's byte-granular
  companion to B27's `block_writes`), 1 file byte differs, the RELOAD owns `[1,2,8]`, 17/17
  other records byte-identical, identity build byte-identical (hook inert). B29's DERIVED
  table reprices the bill 0 -> 1 (delta == rule); the "table value always" rival differs at
  exactly `[8]` (M46's disabled list), the no-write rival at 26 ids, the swapped-orientation
  setter lands on only 4/32 ids, id 39 is REFUSED.
- ACCEPT `python3 -u -m sim.selftest --b30` -> **`PASS B30: 6/6`** rows `234ab3d83a88dbea`
  print `29f408c79329a5a8` img `3a503c638ba45330` (`evidence/b30_facility_completion.txt:35-36`),
  2 runs + relay byte-identical. Harness `scripts/b30_mutate.py` -> **`10/10`**
  `76a481b5d8a7d8b0` (`evidence/b30_mutate.txt:12`), every gate G1-G6 reddened, NO-OP `[]`, ST 4/4, baseline tree green.
- **ASSUMED / census pick:** the game routine that SETS the bit is not in this rung's evidence;
  the setter is the mapper's inverse (`FUN_00507410` = the one 39-bit splitter). G2 measures the
  bijection (32/32) that makes it the only candidate.
- NAMED: M310 rotated VERBATIM to `docs/named-archive-b30-rows.md:5` (sha1
  `ca3caf3785c9d6e9`, `scripts/b30_named_rotate.py --verify`): 246,635 -> 244,146 -> 246,098.
- PITFALL: measuring the bit law on the TARGET record is confounded when the base already owns
  the id (base 0 owns 1 and 8) — the first run read 2/32; measure on a zeroed-window reference.
- PITFALL: a cross-record check must compare each record to ITS OWN original bytes (my first G3
  compared every other record to the target's and read 0/17 — a false red); and a digest must
  never hash a placeholder line appended for context, or it can never be re-pinned.

## Session 322-chain1 (2026-11-24) — M342: pick (x9) the COMPLETION SETTER, answered statically (PR for milestone/m342)
- **Question:** B30 inverted the reader's bijection but left the game routine that SETS `base+0x8c` ASSUMED. Answered: the setter is `FUN_004e44f0(item, base, set)`, a 92-B set/clear API — mapper `FUN_00507410`'s out1 (`[ebp+0x8]`, after the call) is the BYTE INDEX and out2 (`[ebp-0x4]`) the MASK, and the store is ONE `or BYTE PTR [304*base+idx+0x95da9c], mask` at `0x4e4528` (AND twin `0x4e4546` clears). 27 call sites in 8 functions: 16 literal set=1, 7 literal set=0, 4 variable (`evidence/m342_completion_setter.txt:161`, `:190`).
- **Accept:** `python3 -u scripts/m342_completion_setter.py` -> `PASS M342: 6/6 gates`, table digest `2b88df5da5aeafe1` (`:190`), PASS `:207`, 2 runs byte-identical. Harness `scripts/m342_mutate.py` -> `PASS HARNESS M342: 7/7`, NO-OP `[]`, baseline green (`evidence/m342_mutate.txt:2,10`).
- **The pop is a NON-writer:** `FUN_004ef5d0` (244 B) shifts the slots (`0x4ef62c`), decrements pending (`0x4ef642`) and calls only `0x5a73f0`/`0x5a6e70`/`0x446250`/`0x473760`; its body has **0** references to `0x95da9c` and 0 API calls. So B30's completion leg does NOT stamp the bit: the stamp belongs to whoever CALLS the API. OPEN next: which of the 27 sites is the production-completion call (the pop's caller is the base screen `FUN_004ef6d0`, 3/3 sites).
- **Second, inline family:** `FUN_004e47d0` (1600 B) ORs the same field at 7 sites + 3 whole-byte copies, `7/7` OR masks filled by the mapper within 12 insns — so "one setter function" is FALSE as stated; the field has exactly 2 writer functions + the screen's 1-byte copy in `FUN_0041cf20` (11 direct `+0x8c` stores total, `:120-130`).
- **PITFALL (field arithmetic):** the record array base is `0x95da10`, NOT `0x95da14`. `0x95da14` is the OWNER byte (+4) — `0x48f2be` reads it as a byte after `imul edx,edx,0x130`. Reading the array base as 0x95da14 makes the bitmap look like +0x88, a 4-byte error that no count would catch; G1 derives the offset instead of asserting the constant (MU1 reddens it).
- **PITFALL (index vs mask):** the two mapper out-slots are NOT interchangeable — for ids 0..39 the mask stays inside the 5-byte window for only 15/40 while `item>>3` is inside 40/40, so a swapped-out-slot reader looks plausible until counted (RIV3).
- **NAMED headroom:** 248,127 B (1,873 under cap) -> rotated M329 VERBATIM to `docs/named-archive-m329-rows.md:5` (sha1 `ccee72a56f16b4b4`, `scripts/m342_named_rotate.py --verify` PASS, idempotent) -> 241,089 B.
