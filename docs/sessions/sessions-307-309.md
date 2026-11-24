# Session notes archive — sessions 307-309

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-307-307.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

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
