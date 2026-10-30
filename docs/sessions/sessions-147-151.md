# Session notes archive — sessions 147-151

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 147 (2026-10-29) — M93 ACCEPTED: m93post3 PASS 9/9. The POST-tail ladder predicts every traced final

Branch milestone/m93 (s147 continued after s148 closed; the runs interleave — s147 owned post1+post3,
s148 owned post2 and the census-file commits). ACCEPTANCE `python3 scripts/m93_post_census.py --tag
m93post3 --poke-index 7 --poke-extra 2,6 --rounds 4 --timeout 100` (ONE invocation, fresh m54b_clean
load r50->55): **VERDICT PASS 9/9** — G9: 13 candidates predicted, **0 mismatches**, splits vs
final==tailout null 11, vs final==tailout*5 (s146 claim) null 13; G1-G8 green (G3 41/41 tailouts,
div cross-check 41/41 bad=0); 2 qualifying windows: fac2 win=8 E=Mc2 final 186 (= 31 x3 x2, PM+PN),
fac5 win=13 Surface final 56 (= 28 x2, PN), ST/RB true, draws in range.

TRACE (run 1/3, m93post1, census + 22 POST bps, PASS 8/8): 41 ladder passes -> the ladder is a
cascade of apply-if-INSIDE gates; `0x5a9020(a,X,f) != 0` iff a is in the depth-f prereq expansion of
X (f=0 equality, f=1 {X,pr1,pr2}, f=0x270e full closure); era-table legs are constants (x3/x4 then
x2/x3 chosen by ebc&human-mask), the table WORDS are id keys. Model validated 21/21 offline
(scratch/m93/model.py) and 21/21 against the harness function (scratch/m93/dryrun.py).

FIXES after m93post2 FAIL 8/9 (all four post2 mismatches were TIMING, not rules): (1) the ladder's
inputs (0x92adbc, the era table 0x92b954, designed prereq fields, demand dwords) move BETWEEN the
boundary snap (0x51f320) and the ladder — dump the full specials regions AT each TAIL hit
(tailx1 0x927a00-0x933300 + tailx2 0x984f00-0x98b000, 72 KB/hit) and re-read demand at the hit
(d814t/d818t/d81ct); closures read the hit-timed copy. (2) legs K1 x2 (key [0x9851cc]) / K2 x3/2
(key [0x9851fc], ONLY when round > 250) gated on [0x927a80] > 0 — live 0, PT1/PT2/PSX 0 events.
(3) q-add gate also checks 0x98531c/0x98534c. (4) diagnostic bps PT1/PT2/PSX/PX2/PBH: PBH x5 proves
the band region (0x92b076 closure) runs and contributes x1; x2+4 (0x5aa018) never ran (ebx==0).

LAW: a snapshot must be frozen at the SAME timing as the consumer's read — M92's within-round freeze
holds only for the 0x94e488 block; upkeep rewrites 0x92adbc/era-table/designed prereqs mid-round.
NEXT (M94): who writes 0x94e488/0x94e5a8/0x94eda8/0x950664 between rounds (the 8 esi positions are
powers of 4); the human leg (bVar14, FUN_00625af1); pay-site 0x4f0ca6/0x4efedd. Evidence:
evidence/m93post1-3.gdblog; scratch/m93post3.out + _tailx1/2.bin, scratch/m93/{model,dryrun}.py.

## Session 149 (2026-10-29) — M94 ACCEPTED: m94table3 PASS 7/7. FUN_00556690 recomputes the tail divisor every round, in the faction's own upkeep segment; divisor == that faction's BASE COUNT

Branch milestone/m94. ACCEPTANCE `M94_BASE="University Base" python3 scripts/m94_table_watch.py --tag m94table3 --boundaries 2` (fresh m54b_clean load, r52->54 inside, load r50): **PASS 7/7** — G1 4 hw watchpoints armed (DIV1 0x950544/DIV2 0x952600/DIV4 0x956778/DIV5 0x958834), G2 round 52->54 rc=0, G3 32 events, G4 every pc mapped, G5 no gaps, G6 read-back, G7 tracer 0. m94table1/2 measured the same thing and FAILed ONLY on the log-parse gate (gdb attach/SIGINT stop-location lines `0x... in ?? ()` were not whitelisted) — re-run, floor never edited.

- WHO: the divisor `[fac*8380+0x94e488]` is written by **FUN_00556690**: reset `mov [edx+0x94e484/488/48c],esi(0)` (reported pc 0x5566d5, store 0x5566cf) then rebuild `inc edx; mov [eax+0x94e488],edx` (reported 0x556a8d, store 0x556a87) — recomputed 0..N EVERY round, not incremented. The multiplier `[+0x94e5a8+edi]` and category `[+0x94eda8+edi]` arrays are rewritten in the same stage (m94table1 pcs 0x556721/0x556b5a/0x55851d/0x558551; 0x950664 IS fac1's multiplier array).
- WHEN: inside the faction's OWN upkeep segment — the printed cur_player (0x985dcc) equals the faction of every dword written (cp=2 events hit DIV2 etc.), once per round. FUN_00556690(arg=fac) is the 6th stage of FUN_005208f0's per-player turn sequence (call 0x52094f, after 0x5551e0); second caller FUN_0059ce10 @0x59dd43.
- WHAT: **divisor == bases owned** — read back at r54: divisors [0,2,4,1,3,3,4,1] == bases/fac {1:2,2:4,3:1,4:3,5:3,6:4,7:1}. Count 0 -> the whole reset+rebuild block skips -> explains m94table1: fac0 (0 bases) watchpoint on the pick's 0x94e488 caught ZERO stores in 2 boundaries, value 0->0.
- accept_ready BLOCKED (credit 0, income gated d0>0) on the fresh load; the m94 harness pokes storage 200 per boundary (documented recipe) and gates on round movement, not on completion — reported, not hidden.
- STATIC grep: 10 absolute store sites for 0x94e488 in 7 functions (0x4e4861 FUN_004e47d0, 0x4e4f79 FUN_004e4e10, 0x4f3b16/0x4f3b26 UNMAPPED, 0x5088ad/0x5088ba, 0x5566cf+0x556a87 FUN_00556690, 0x59efab, 0x5a0b2e `mov [edx*4+0x94e488],0x0`); only the FUN_00556690 pair fired in these windows — the production-path writers are OPEN (likely base-capture/loss paths).
- OPEN: what the sibling dwords 0x94e484/0x94e48c count (live 9/37, 20/66 for fac0/fac2); the mult/cat inputs; human leg (bVar14, FUN_00625af1); pay-site 0x4f0ca6/0x4efedd.
NEXT (M95): the pay-site conflict 0x4f0ca6 vs 0x4efedd. Evidence: evidence/m94table1-3.gdblog; scratch/m94table*_seq.jsonl. Box: fresh m54b_clean r50->54, University enqueued, no census.

## Session 150 (2026-10-29) — M95 ACCEPTED: m95pay4 PASS 9/9. The pay-site conflict CLOSED: branch A 0x4efedd pays AND activates a UI-queued completion, from storage base+0x40

Branch milestone/m95. ACCEPTANCE `python3 scripts/m95_pay_sites.py --tag m95pay4 --boundaries 2` (ONE invocation, m54b_clean r59->61, University Base row 0x95da10, tid 2 Scout Patrol, credit -1, storage poked 200/boundary): **PASS 9/9** — GATEA base=0x95da10 price=9 storage=200 pending=1 q0=2 -> PAYA price=9 storage=200 -> STOR pc 0x4efee0 new=191 (store 0x4efedd `sub esi,edi; mov [ecx+0x40],esi`) -> STOR pc 0x4eff23 new=0 (clamp 0x4eff20 = min(cap 0x92a370, credit d0) or 0, human owner) -> POSTA storage 0 mirror 0 -> CREATE tid 2 (0x4eff4e -> 0x5ab650) -> POP idx 0 retn 0x4f0380 (call 0x4ef5d0 at 0x4f037b, A-tail) -> PEND store pc 0x4ef648 new 0 (pending 1->0 read back); GATEB/PAYB/DEFERB/BRET/CLAIMED/DISP 0 events, no store at 0x4f0ca9. m95pay3 PASSed 8/9 on identical data (only my G9 expression was wrong); m95pay1 FAILed 4/9 + m95pay2 3/9 on instrument bugs (see traps) — floors never edited.

DISPATCH (instruction bytes, scratch/m95/cfg.py): FUN_004ef6d0 loops the queue at 0x4ef88b: q0==-38 -> return; **q0 >= 0 -> branch A** (price 0x4efa4d/0x4efa52, gate 0x4efa5e cmp [base+0x40],edi, tid<0x40 skips the M74 mark block, pay 0x4efedd, clamp, mirror +0x98, create 0x4eff4e, POP 0x4f037b, loop). **q0 < 0 -> typecode = -q0** (0x4ef89f); branch B entered only when tc>=39 && claim[tc-39](0x985b3c)==-1 (0x4f0a3d gate), or tc>34 (0x4ef94a), or the 0x507410 mask test fails (0x4ef985); race scan 0x4f0af0-0x4f0b72 (+4-shifted: [esi+0x4c]=queue0, [esi+0xcc]+[esi+0x3c]=credit+storage) defers to a competing base that can pay (jge 0x4f0c28, no store); 0x4f0b80 `jg 0x4f0ca1` is the SOLE entry to B's pay — **0x4f0ca6 pays the SAME field** (`sub esi,edi; mov [edx+0x40],esi`), claim store 0x4f0d83, POP 0x4f0f46. NO back-edge from B's region into A's (cfg.py): the two pays are mutually exclusive shapes. ANSWER: the NAMED "completion path" B is the negative-queue/claim branch; the UI-queued designed completion pays AND activates in A.

STALE-TAIL LAW (live x3): after pending 1->0 q0 stays 2 (shift never clears the tail): the next visit re-enters A — gate fails while storage 0 < price (GATEAF, no side effect); with storage poked >= price it PAYS + CREATEs a phantom unit and calls POP with pending 0 (no pending store) — m95pay3 r59. base+0xd0 -1->0 between r58/r59, writer untraced (+0xd0 unwatched).

NEXT (M96): the human leg — FUN_00625af1 @0x5aa20d, bVar14 in FUN_0048b9a0, [esi+0x94d800] sibling, [esi+0x94d430] bit 0x40; census bps ready in skill code-atlas. OPEN: base+0xd0 writer; the negative-queue producer that reaches B. Evidence: evidence/m95pay1-4.gdblog; scratch/m95pay*_seq.jsonl, scratch/m95/cfg.py. Box: m54b_clean r59->61 census ran, pending 0, q0 stale 2.

## Session 151 (2026-10-29) — M96 ACCEPTED: m96human2 PASS 12/12. The chooser's human leg decoded: the x256 / prereq-depth scaling is gated on ds:0x985ac4&0x200 (NOT the human mask); the human bit only swaps the DRAW stream and arms a forced pick; the ranking key is the DRAW, not the score

Branch milestone/m96. ACCEPTANCE `python3 scripts/m96_human_leg.py --tag m96human2 --rounds 2 --timeout 100` (ONE invocation, m54b_clean r64->66, fac3+fac2 slots poked -1 at arm): **PASS 12/12** — G1 round moved; G2 both pokes landed; G3 both legs seen; G4 the chooser ran for fac3 (human, mask 0x08) AND for fac2; G5 leg == mask on 13/13 candidates (7 human / 6 rand); G6 divisor 13/13 == max(FUN_005a6d40(prereq1,1), FUN_005a6d40(prereq2,1)) computed from the live prereq table; G7 quotient 13/13 == (score<<8)/div; G8 7/7 human draws predicted EXACTLY from the state read before the call; G9 winners 2/2 == the max-draw candidate; G10 forced-pick consistent (0 events); G11 landing == return 2/2; G12 detached. m96human1 FAILed 9/12 on three INSTRUMENT bugs (traps) — floors never edited, re-run.

- **bVar14** (shard_009.c:9343-9347) = `((ds:0x985ac4 & 0x200) != 0 && param_3 <= 0)`: live ebc 0x1a0e -> TRUE, so FUN_0048b9a0's chooser leg runs for the HUMAN faction too (A030 fac=3, landing 0x48bae9 observed).
- **THE MULTIPLY**: gate 0x5aa164 `test ah,0x2`; 0x5aa1e7 `shl eax,8` then 0x5aa1eb `idiv edi`, edi = the candidate's PREREQ-CHAIN DEPTH (FUN_005a6d40(a,b): b if a<0||a>=89, else max of the two prereqs at b+1). DIV events fire for fac2 as well (n=1-6) -> **the scaling is NOT human-specific**; the "human key" framing is RETRACTED.
- **THE HUMAN BIT does two things only**: (1) 0x5aa17e gates the FORCED pick — reads [fac*8380+0x94d810] / [+0x94d818]; if either != 0, the candidate == WORD ds:0x98adee (live 6) returns at 0x5aa251 with NO draw. Live flags fac1 (1,0), fac2 (0,1), fac4 (0,1), fac6 (1,0), fac7 (1,0), human fac3 (0,0) -> inert here, 0 events. (2) 0x5aa204 picks the DRAW source: human -> FUN_00625af1(0,score+1) = thiscall FUN_00625a0f(&ds:0x999fa0): state = state*0x19660d+0x3c6ef35f mod 2^32, val = ((state&0xffff)*(hi-lo))>>16 + lo; non-human -> rand() (0x64c6f0) % (score+1), 0 when score <= 0.
- The 0x999fa0 stream advances EXACTLY one step per human candidate: 911923404 -> 7 steps -> 296222889 == the state printed at RETV (scratch/m96/chain.py, output scratch/m96/chain.out).
- **THE RANKING KEY IS THE DRAW** (0x5aa232 `cmp eax,[ebp-0x8]`, best starts -999, strictly-greater wins, ties keep the earlier): fac3's highest-scaled candidate idx 72 (IndRob, score 2133) drew 5 and LOST to idx 13 (Surface, score 1408) draw 835; RETV idx 13 read back, slot(/proc) = 13 for both fac2 and fac3. A score-WEIGHTED LOTTERY, not max-score.
- [f*8380+0x94d430] bit 0x40 = 0 for ALL 8 factions at r66 (dwords 0,2,c,3,9,4,8,1) -> the M89 second-ask / sibling-fill path never ran; [f*8380+0x94d800] live = -1,81,128,86,166,128,77,64 (>= 89 -> NOT tech indices, OPEN).
NEXT (M97): WHO writes base+0xd0 (credit) mid-game (-1->0 seen r58/59 against the "init-only" trap) — hw watchpoint on one base row's +0xd0, 2-3 boundaries, name the writer by containment via ghidra_out/index.csv. OPEN: what [esi+0x94d800] holds; whether WORD ds:0x98adee is record 1's +0x32 or a standalone global; the negative-queue producer that reaches branch B. Evidence: evidence/m96human1-2.gdblog; scratch/m96human2.out, scratch/m96/chain.{py,out}. Box: m54b_clean r64->66, census ran, both poked slots filled 13.
