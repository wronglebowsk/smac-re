# Session notes archive — sessions 142-142

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 142 (2026-10-28) — M91: scorer BASE = SUM (demand*m+1)*cost, predicted 12/12 EXACT; the pick is max-of-random-DRAWS, not max score (m91score1 FAIL 6/7 on G3)

Prompt said M74 (merged #75); repo pick M91. Branch milestone/m91, commit f078138 -> acceptance -> docs.

BOX: brief BLOCKED (pend 0), its FIX ran first (`m57_ui_enqueue --base-index 0 --cell-item 2 --inserts 1` -> pending 1 head 2); accept_ready then BLOCKED on "credit 0 <= 0" (income add gated on d0>0; printed FIX = clean reload) — M91 needs only boundaries, so the census ran on the live box (pid 262651, round 80) with NO reload.

STATIC (scratch/m71/dis.py): FUN_005a90a0(idx, fac, arg2) 0x5a921d-0x5a92ab: [ebp-0x4] = (Y14*m+1)*T4 + (Y18*m+1)*T8 + (Y10*m+1)*T0 + (Y1c*m+1)*Tc, m = 1 if arg2 != 0 else 4/2 by 0x985ac4 bit 0x200 (live SET). Costs T0/T4/T8/Tc = *(0x92fdc4+idx*44+0,+4,+8,+0xc) — that record's prereq1 is +16 (= 0x92fdd4) and its 8-char name +32 (= 0x92fdd4+16), so M90's "base 0x92fdd4" is the +16 FIELD, not the record start. Demand Y10/Y14/Y18/Y1c = *(fac*8380+0x94d810/14/18/1c). Halved at 0x5a92fd iff all four pairs inert: (Tc==0 or (Y1c==0 and bc==0)) and (T4==0 or Y14==0) and (T8==0 or Y18==0) and (T0==0 or (Y10==0 and [fac*8380+0x94e488]>=4)), bc = bit-0x10 popcount of 0x94d448 dwords 1..7. The level leg 0x5a93b3-0x5a94f2 runs ONLY when arg2 != 0 (0x5a9375 `je 0x5a9500`); a human faction skips it (0x5a931a). Tail 0x5a94fd-0x5a95f8: esi=1..62, adds byte[fac*8380+0x94e5a8+esi]*Tc over divisors keyed by byte[+0x94eda8+esi] in {7,2,0}. In FUN_005aa030: score = score*256/level (0x5aa1e4 `shl eax,8; idiv edi`; level = max FUN_005a6d40(p1,1), FUN_005a6d40(p2,1)); DRAW = _rand() % (score+1) (0x5aa217-0x5aa230, 0 when score <= 0); the scan keeps the STRICTLY greater draw (0x5aa232, best starts -999).

ACCEPTANCE `python3 scripts/m91_scorer_census.py --tag m91score1 --poke-index 5 --rounds 3 --timeout 120` (ONE invocation, 3 boundaries, driver rc=0 each): **VERDICT FAIL 6/7** — G1 poke 36->-1 read back; **G2 TRUE 12/12: predicted BASE == the engine's [ebp-0x4] at 0x5a930b** (fac5 idx 4/22/32/36/45 -> 10/26/24/15/7; fac4 idx 8/13/35/43/48/60/72 -> 4/14/3/15/5/19/11); G4 TRUE 2/2 (winner == strictly-largest draw, every draw in [0, score*256/level]); G5 TRUE (ST 0x5aa9d3 + RB 0x5aa9d5 read back); G6 TRUE (Integ 36, EthCalc 43 read from live memory); G7 TRUE (round 80->83, 2 qualifying windows, >=2 distinct bases each). **G3 FALSE: the fac4 winner 43 had final 16 while candidate 60 had 38 (draws 1838 vs 2)** — max-score is not the game's rule; fac5 agreed only by luck (36 was both max score 112 and max draw 6903).

OPEN: the tail's arithmetic (final != base at fac5 idx36 15->112, fac4 idx60 19->38, +1 at 4/22/32/43/72, unchanged where Tc==0); who writes [fac*8380+0x94e488] and the 0x94e5a8/0x94eda8 category bytes; the human leg (FUN_00625af1, bVar14); where the chosen index becomes the ACTIVE project (pay-site conflict 0x4f0ca6 vs 0x4efedd); SIBLING slot [esi+0x94d800]. NEXT: M92 — decode the tail loop, census final == base + tail on >= 2 windows with the same instrument.
Evidence: evidence/m91score1.gdblog; scratch/m91score1.gdb, scratch/m91/probe.py.
