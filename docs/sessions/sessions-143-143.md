# Session notes archive — sessions 143-143

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 143 (2026-10-28) — M91 CLOSED: m91score5 PASS 7/7 (one invocation, fresh box, 4 AI windows, 27 candidates, 0 base mismatches)

Same milestone as s142 (branch milestone/m91, commits 95fa804 + fe55c33 + this docs commit). Two gates were MY instrument defects, both fixed in place, each fix justified by instruction bytes or event order, never by weakening a floor:
1. G3 demanded winner == max FINAL — my hypothesis, not a byte rule; 0x5aa232/0x5aa235 `cmp eax,[ebp-0x8]; jle` (esi asc 0..88, best starts -999 at 0x5aa03c) proves the engine keeps the strictly-greatest DRAW and equal draws never replace. G3 became: winner holds the max draw AND no higher-index candidate ties it.
2. G5 read RB from a {addr: last-mem} dict: slot5 was allocated twice in one window (36 then 4), the dict held only 4 -> m91score3 FAIL 6/7. Pairing each ST with the RB that follows it in the event stream (0x5aa9d5 runs right after 0x5aa9d3) is the honest pairing.

ACCEPTANCE `python3 scripts/m91_scorer_census.py --tag m91score5 --poke-index 5 --rounds 4 --timeout 120` (ONE invocation on a fresh m54b_clean load, pid 347970 r50): **VERDICT PASS 7/7** — G1 poke 8->-1 read back; G2 TRUE (every traced BASE == predicted (demand*m+1)*cost sum, m=4 via 0x985ac4 bit 0x200, halving rule; 27 candidates 0 mismatches); G3 TRUE 4/4; G4 TRUE (all draws in [0, final*256/level]); G5 TRUE 4/4 ST/RB pairs; G6 names Integ/AGrav/E=Mc2/PlaEcon/Surface read from 0x92fdd4; G7 TRUE (4 qualifying windows fac5/5/4/6, round 50->55). Windows DISPROVE max-score twice: fac5 win 22 'AGrav' final 31 vs max_final 56; fac6 win 13 'Surface' final 36 vs 63. Prior runs same session: m91score2 6/7 (G7 one AI window — box state, only fac5 had a work item), m91score3 6/7 (G5 dict bug; its 4 windows already showed G3/G4/G6/G7 True), m91score4 5/7 HARNESS DEATH: the tool's 420 s foreground cap killed the census mid-run and left Wine hung at round 92 (CTRL=0, no year move even after detach) — recovered via m54a_load --relaunch.

OPEN (M92): the tail 0x5a94fd-0x5a9698 arithmetic (final != base at 6-8 candidates/window; who writes [fac*8380+0x94e488] + the 0x94e5a8/0x94eda8 category bytes); the human leg (bVar14, FUN_00625af1); where the chosen index becomes the ACTIVE project (pay-site 0x4f0ca6 vs 0x4efedd); SIBLING slot [esi+0x94d800]. Evidence: evidence/m91score2-5.gdblog; scratch/m91score*.gdb/.out. evidence 27.6 MB.
