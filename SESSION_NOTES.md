

Older sessions: `docs/sessions/sessions-139-139.md` (1 sessions). Read it only when a question reaches back before session ## Session 140.

## Session 140 (2026-10-28) — M89: the slot value is FUN_005ab000's return; FUN_005aadf0 asks for one the moment the slot is negative (m89alloc1 PASS 8/8, m89alloc2 PASS 8/8)

Prompt said M74 (merged #75); the repo pick was M89. Branch milestone/m89 from main d4b54cc.

BOX: the brief said BLOCKED (pend 0) — the FIX ran first: `python3 scripts/m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1` -> pending 0->1, head=2, slots=[2,2,0,0,0,0]. No relaunch was needed: 5aadf0 -> aaa20 is a per-base upkeep tail (M88's own PASS ran on this box at r64-68).

ACCEPTANCE, two invocations, both green:
`python3 scripts/m89_alloc_census.py --tag m89alloc1 --poke-index 5 --rounds 3 --timeout 100` (pid 262651, round 68, slots(0..7) [-1,44,13,32,5,36,32,48], save 0): **VERDICT PASS 8/8** — poke 36->-1 read back; 2 allocations, both stores 0x5aa9d3 `mov [esi],ebx`: (slot5 0x957ba8 val 36 round 68 ret 0x5aaff3) and (slot2 0x951974 val 36 round 69 ret 0x5aaff3); chooser line for each eax=36; ctrl=3 aaa=1 cons=1 a2st=0; round 68->71; /proc read-back slot5=36, slot2=36 (the only later write to slot2 is aaa20's own -1 at 0x5aaac1, which is in the log).
`python3 scripts/m89_alloc_census.py --tag m89alloc2 --poke-index 5 --rounds 3 --timeout 100` (round 71): **PASS 8/8**, 1 allocation (slot5 val 36 ret 0x5aaff3), chooser `CHR n=1 eax=36 args=(5,0,-1,0) fac=5`, inferior read-back mem=36, round 71->74 (boundary 3 driver rc=1 while the round still moved — the harness race, not a gate).

MECHANISM (scratch/m71/dis.py 5aaf00 5ab000): FUN_005aadf0's tail is the answer to "who and when" — 0x5aafcf `mov eax,[esi+0x94d7f8]; jl 0x5aaffc`, 0x5aafda `mov eax,[esi+0x94d7fc]; test; jge 0x5aaffc` (NO ask while the slot is >= 0), 0x5aafe4 `cmp DWORD PTR ds:0x926bd4,1; je 0x5aaffc`, 0x5aafee `call 0x5aa880` -> 0x5aaff6 `mov [esi+0x94d7fc],eax` (the caller stores it too). It is the SAME invocation whose aaa20 call (0x5aaf46) consumed the slot: run1's faction-2 order AAA(2) ret 0x5aaf4b -> CONS(slot2, kind 13) -> ENT(2) ret 0x5aaff3 -> CHR -> ST(slot2, 36) is that path, in that order. Inside FUN_005aa880 nothing is invented: 0x5aa892 `je 0x5aa9a5` (save 0 -> live leg), pushes 0/-1/0/edi, 0x5aa9ac `call 0x5ab000`, 0x5aa9b3 `mov ebx,eax`, 0x5aa9c5 `lea esi,[eax*4+0x94d7fc]`, 0x5aa9d3 stores. G5 (stored == chooser return) held 3/3.

WHAT THE VALUE IS NOT: `python3 scratch/m89/recname.py 262651 36 44 13 32 5 48 45 192 193 196` — 36, 44, 32, 48, 45 name NOTHING at 0x98ad88+id*52 (empty, cost 0), while 13 Unity Foil, 5 Supply Crawler, 3 Transport Foil, 8 Mind Worms, 10 Locusts of Chiron are real ANY-faction units (owner 0xff00). So 36 is NOT a global type-record id. Every observed value (3,5,8,13,22,32,36,44,45,48,49) is < 50 and 0x5aaf10 compares the slot against 0x59 = 89, so the domain reaches >= 89. FUN_005ab000 reserves a 0xc5c-byte local (0x5ab018 `sub esp,0xc5c`), calls 0x489fd0 on it, then re-pushes its four args to 0x48b9a0 — a candidate scan, not a constant. CONFOUNDED: factions 5 and 2 allocated the SAME 36 in one window, so per-faction uniqueness is NOT established.

INSTRUMENT DEFECT fixed in place: the first m89alloc1 attempt died before arming — my site_line treated the objdump section header `00401000 <.text>:` as an instruction line (ValueError); fixed to require `^[0-9a-f]{6,8}:\t`. Run 1 also printed the chooser args shifted by one (esp+4..esp+16 = arg2..arg4 + the saved edi); labels corrected to esp..esp+12 before run 2, which reads (5,0,-1,0).

OPEN (M90 pick): what FUN_005ab000's scan selects and what the 0..89 domain is (10/25/26 are the values FUN_005a7970's table 0x93325c/68/74 accepts); the SIBLING slot [esi+0x94d800], which 5aadf0 fills from FUN_005aab70 (0x5aaf67 stores -1, 0x5aaf79 stores eax, 0x5aaf02 calls the same provider); and the band flag [esi+0x94d430] bit 0x40, tested at 0x5aaf7f and cleared at 0x5aafb1 before 5aadf0's second aaa20 call at 0x5aafbb.
Evidence: evidence/m89alloc1.gdblog (49 lines), evidence/m89alloc2.gdblog; scratch/m89alloc*.gdb/.out. evidence 27.5 MB.

## Session 141 (2026-10-28) — M90: the slot value is a TECHNOLOGY INDEX into the 89-entry table at 0x92fdd4, chosen by FUN_005aa030(faction) (m90tech1 FAIL on my own slice bug, m90tech2 PASS 8/8)

Prompt said M74; the repo pick was M90. Branch milestone/m90, commit df1acd7 -> acceptance.

BOX: brief BLOCKED twice, both printed FIXes run: (1) screen 'dialog' -> `normalize_screen()` -> hud; (2) `m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1` FAILED — "INSERT 1 never landed", pending stayed 0, because University Base now has minerals 0 / credit 0 (the pane left the screen 'base'; normalized again). M90 needs no queue, only boundaries, so this does not block it.

STATIC (shard_009.c:9288 FUN_0048b9a0 8514 B 1 caller; shard_015.c:22025 FUN_005aa030 554 B 3 callers; scratch/m71/dis.py windows): FUN_005ab000 is a THIN wrapper — 0x5ab047 `call 0x48b9a0` -> 0x5ab04c `mov esi,eax` -> 0x5ab0bf `mov eax,esi` -> ret; its 0xc5c frame is SEH + 4 C++ locals (destructors 0x6170f3), not a candidate array. FUN_0048b9a0's non-human leg (shard_009.c:9359) is `if ((param_2 == 0 && ((round == 0 || !(0x985b10 & (1<<param_1))) || bVar14)) && param_3 < 0) { pcVar2 = FUN_005aa030(); ...; return pcVar2; }` — call site 0x48bae4 `e8 47 e5 11 00`, landing 0x48bae9; bVar14 is NOT decoded. FUN_005aa030(faction) loops `iVar4 < 0x59` (= 89) over `(&DAT_0092fdd4)[iVar4*0xb]` (stride 44), gates candidates with FUN_005a6cd0, scores with FUN_005a90a0, tie-breaks `_rand() % (local_8+1)` (human: FUN_00625af1), keeps the max and returns the INDEX.

THE DOMAIN IS THE TECH TABLE — `python3 scratch/m90/txthex.py 262651 10 13 25 26 36 45`: the 8-byte name at +16 reads 10 Alloys, 13 Surface, 25 SingMec, 26 ConSing, 36 Integ, 45 IndAuto; all 89 names from live memory run Indust InfNet Physic Psych Mobile Ecology Super Chaos E=Mc2 Fusion Alloys ... DigSent ... User0..User9 ... TranT. Corroboration from the same records: Alloys' prereq fields are +0=30 (Solids) and +4=7 (Chaos) = SMAC's Alloy Theory <- Solid State Physics + Chaos Theory. M86's table shorts 10/25/26 are Alloys/SingMec/ConSing.

ACCEPTANCE `python3 scripts/m90_tech_choice.py --tag m90tech2 --poke-index 5 --rounds 3 --timeout 100` -> **VERDICT PASS 8/8**: 4 allocations traced to named entries in 2 rounds — fac5 val 36 'Integ' and fac7 val 32 'DigSent' (round 77), fac2 val 32 'DigSent' and fac6 val 13 'Surface' (round 79); each matched the FUN_005aa030 return printed at its landing 0x48bae9 with param1 == the faction; every store came from FUN_005aadf0 (ret 0x5aaff3); every slot read back from /proc; round 77->80, ctrl 3, a030 calls 4, CONS 3 (aaa20 consumed 48/36/32 first). `--tag m90tech1` FAILed ONE gate (G6) from my own bug — the pairing sliced `events` by the ST event's index inside `st`, so the TECH event was never in range; its data already showed the agreement (CHR printed idx_from_5aa030=22 == eax=22, A030 arg1 = 4 and 5). Fixed in place; the same slice in m89_alloc_census.py's informational column fixed too (no m89 gate used it).

OUTCOME: the per-faction slot IS the faction's next research project (tech index 0..88, -1 = none). M89's "who asks" + this "what" close the loop: aaa20 consumes the INDEX and hands it to FUN_005a7970, whose 3-entry table (Alloys/SingMec/ConSing) is exactly why M86/M87 measured WALK 3, LOOP 0. OPEN (M91): what FUN_005a90a0 scores (the cost/benefit model that picks the winner), the human leg (bVar14 + FUN_00625af1), and where the chosen tech becomes the ACTIVE project (pay-site conflict 0x4f0ca6 vs 0x4efedd still open).
Evidence: evidence/m90tech1.gdblog, evidence/m90tech2.gdblog; scratch/m90/tabscan.py, scratch/m90/txthex.py, scratch/m90tech*.out. evidence 27.6 MB.

## Session 142 (2026-10-28) — M91: scorer BASE = SUM (demand*m+1)*cost, predicted 12/12 EXACT; the pick is max-of-random-DRAWS, not max score (m91score1 FAIL 6/7 on G3)

Prompt said M74 (merged #75); repo pick M91. Branch milestone/m91, commit f078138 -> acceptance -> docs.

BOX: brief BLOCKED (pend 0), its FIX ran first (`m57_ui_enqueue --base-index 0 --cell-item 2 --inserts 1` -> pending 1 head 2); accept_ready then BLOCKED on "credit 0 <= 0" (income add gated on d0>0; printed FIX = clean reload) — M91 needs only boundaries, so the census ran on the live box (pid 262651, round 80) with NO reload.

STATIC (scratch/m71/dis.py): FUN_005a90a0(idx, fac, arg2) 0x5a921d-0x5a92ab: [ebp-0x4] = (Y14*m+1)*T4 + (Y18*m+1)*T8 + (Y10*m+1)*T0 + (Y1c*m+1)*Tc, m = 1 if arg2 != 0 else 4/2 by 0x985ac4 bit 0x200 (live SET). Costs T0/T4/T8/Tc = *(0x92fdc4+idx*44+0,+4,+8,+0xc) — that record's prereq1 is +16 (= 0x92fdd4) and its 8-char name +32 (= 0x92fdd4+16), so M90's "base 0x92fdd4" is the +16 FIELD, not the record start. Demand Y10/Y14/Y18/Y1c = *(fac*8380+0x94d810/14/18/1c). Halved at 0x5a92fd iff all four pairs inert: (Tc==0 or (Y1c==0 and bc==0)) and (T4==0 or Y14==0) and (T8==0 or Y18==0) and (T0==0 or (Y10==0 and [fac*8380+0x94e488]>=4)), bc = bit-0x10 popcount of 0x94d448 dwords 1..7. The level leg 0x5a93b3-0x5a94f2 runs ONLY when arg2 != 0 (0x5a9375 `je 0x5a9500`); a human faction skips it (0x5a931a). Tail 0x5a94fd-0x5a95f8: esi=1..62, adds byte[fac*8380+0x94e5a8+esi]*Tc over divisors keyed by byte[+0x94eda8+esi] in {7,2,0}. In FUN_005aa030: score = score*256/level (0x5aa1e4 `shl eax,8; idiv edi`; level = max FUN_005a6d40(p1,1), FUN_005a6d40(p2,1)); DRAW = _rand() % (score+1) (0x5aa217-0x5aa230, 0 when score <= 0); the scan keeps the STRICTLY greater draw (0x5aa232, best starts -999).

ACCEPTANCE `python3 scripts/m91_scorer_census.py --tag m91score1 --poke-index 5 --rounds 3 --timeout 120` (ONE invocation, 3 boundaries, driver rc=0 each): **VERDICT FAIL 6/7** — G1 poke 36->-1 read back; **G2 TRUE 12/12: predicted BASE == the engine's [ebp-0x4] at 0x5a930b** (fac5 idx 4/22/32/36/45 -> 10/26/24/15/7; fac4 idx 8/13/35/43/48/60/72 -> 4/14/3/15/5/19/11); G4 TRUE 2/2 (winner == strictly-largest draw, every draw in [0, score*256/level]); G5 TRUE (ST 0x5aa9d3 + RB 0x5aa9d5 read back); G6 TRUE (Integ 36, EthCalc 43 read from live memory); G7 TRUE (round 80->83, 2 qualifying windows, >=2 distinct bases each). **G3 FALSE: the fac4 winner 43 had final 16 while candidate 60 had 38 (draws 1838 vs 2)** — max-score is not the game's rule; fac5 agreed only by luck (36 was both max score 112 and max draw 6903).

OPEN: the tail's arithmetic (final != base at fac5 idx36 15->112, fac4 idx60 19->38, +1 at 4/22/32/43/72, unchanged where Tc==0); who writes [fac*8380+0x94e488] and the 0x94e5a8/0x94eda8 category bytes; the human leg (FUN_00625af1, bVar14); where the chosen index becomes the ACTIVE project (pay-site conflict 0x4f0ca6 vs 0x4efedd); SIBLING slot [esi+0x94d800]. NEXT: M92 — decode the tail loop, census final == base + tail on >= 2 windows with the same instrument.
Evidence: evidence/m91score1.gdblog; scratch/m91score1.gdb, scratch/m91/probe.py.

## Session 143 (2026-10-28) — M91 CLOSED: m91score5 PASS 7/7 (one invocation, fresh box, 4 AI windows, 27 candidates, 0 base mismatches)

Same milestone as s142 (branch milestone/m91, commits 95fa804 + fe55c33 + this docs commit). Two gates were MY instrument defects, both fixed in place, each fix justified by instruction bytes or event order, never by weakening a floor:
1. G3 demanded winner == max FINAL — my hypothesis, not a byte rule; 0x5aa232/0x5aa235 `cmp eax,[ebp-0x8]; jle` (esi asc 0..88, best starts -999 at 0x5aa03c) proves the engine keeps the strictly-greatest DRAW and equal draws never replace. G3 became: winner holds the max draw AND no higher-index candidate ties it.
2. G5 read RB from a {addr: last-mem} dict: slot5 was allocated twice in one window (36 then 4), the dict held only 4 -> m91score3 FAIL 6/7. Pairing each ST with the RB that follows it in the event stream (0x5aa9d5 runs right after 0x5aa9d3) is the honest pairing.

ACCEPTANCE `python3 scripts/m91_scorer_census.py --tag m91score5 --poke-index 5 --rounds 4 --timeout 120` (ONE invocation on a fresh m54b_clean load, pid 347970 r50): **VERDICT PASS 7/7** — G1 poke 8->-1 read back; G2 TRUE (every traced BASE == predicted (demand*m+1)*cost sum, m=4 via 0x985ac4 bit 0x200, halving rule; 27 candidates 0 mismatches); G3 TRUE 4/4; G4 TRUE (all draws in [0, final*256/level]); G5 TRUE 4/4 ST/RB pairs; G6 names Integ/AGrav/E=Mc2/PlaEcon/Surface read from 0x92fdd4; G7 TRUE (4 qualifying windows fac5/5/4/6, round 50->55). Windows DISPROVE max-score twice: fac5 win 22 'AGrav' final 31 vs max_final 56; fac6 win 13 'Surface' final 36 vs 63. Prior runs same session: m91score2 6/7 (G7 one AI window — box state, only fac5 had a work item), m91score3 6/7 (G5 dict bug; its 4 windows already showed G3/G4/G6/G7 True), m91score4 5/7 HARNESS DEATH: the tool's 420 s foreground cap killed the census mid-run and left Wine hung at round 92 (CTRL=0, no year move even after detach) — recovered via m54a_load --relaunch.

OPEN (M92): the tail 0x5a94fd-0x5a9698 arithmetic (final != base at 6-8 candidates/window; who writes [fac*8380+0x94e488] + the 0x94e5a8/0x94eda8 category bytes); the human leg (bVar14, FUN_00625af1); where the chosen index becomes the ACTIVE project (pay-site 0x4f0ca6 vs 0x4efedd); SIBLING slot [esi+0x94d800]. Evidence: evidence/m91score2-5.gdblog; scratch/m91score*.gdb/.out. evidence 27.6 MB.

## Session 144 (2026-10-28) — M92: the tail 0x5a9503-0x5a9698 DECODED and validated against the engine's own finals; the census harness is still not green (m92tail2-7 all FAIL)

Prompt said M74 (merged #75); repo pick M92. A sibling session had m92tail3/4 in flight on
milestone/m92; I adopted its commits (6c15d37 mine) instead of competing, then verified the MODEL
offline from committed evidence (scratch/m92/verify7.py reads evidence/m92tail7.gdblog +
scratch/m92tail7_snaps.bin + /proc — no gdb, no poke).

THE TAIL, leg by leg (scratch/m71/dis.py 5a9500 5a96a0): 0x5a9503 `mov ebx,[ecx+0x94e488]` is the
divisor, `je 0x5a9698` skips the whole loop when 0; loop esi=1..62 (0x5a9518 `and eax,0x3f` skips
esi==63, 0x5a9692 `jl 0x5a9516`). Category byte = [fac*8380+0x94eda8+esi], multiplier =
[fac*8380+0x94e5a8+esi], Tc = the tech record's +0xc (0x5a955b `imul eax,[edx+0x92fdd0]`).
CAT 7 (0x5a9536): gate `mov ecx,[ebp-0x18]; je` — [ebp-0x18] is the CALLEE's own prologue counter
(0x5a90ae zeroed, 0x5a90d6 `inc edx` per control dword [0x94d448+4*i] with bit 0x10 set, i=0..7) =
the bc the BASE print already carries, NOT a caller slot (the census never writes caller [ebp-0x18]:
FUN_005aa030 sub esp,0xc, locals -0xc..-0x4); then 0x5a9541 skips when the faction IS human; adds
`idiv mult*Tc, ebx` — divisor NOT doubled. CAT 2: mult*Tc*4 / (div*(1+human)). CAT 0: factor 4 if
[blk+0x94dc44] >= [blk+0x94dc58] else 2, / (div*(1+human)). ELSE (0x5a95fd): 0x5a960e skips the inner
loop when arg2 == the faction; edi=1..7 over GLOBAL band tables 0x950664 + edi*0x20bc (stride 844):
the edi-th table's OWN byte at +esi must be nonzero (0x5a9615 — a SECOND multiplier, not the block
byte); gate on the control dword [0x94d448+(fac+edi)*4] needing bit 0x8 set and NOT (bits 0-1 set with
bit 5 clear) (0x5a9640/45/4a, index 0x5a9628-0x5a9637 = (fac+edi)*13 dwords); adds mult*Tc/(div*2 if
human else div). The tail mutates [ebp-0x4] in place; 0x5aa159 `mov [ebp-0x4],eax` is the FINAL.

THE MODEL DISCRIMINATES, against the engine's own numbers (m92tail5 CAND line, fac7): observed finals
19/32/57/28/24/45 for bases 10/15/28/15/23/41 == base + idiv(16*Tc, 1) = the cat-7 leg with mult
[fac7*8380+0x94eda8+40] = 16 and div 1; the old model (cat-7 gated on a caller slot, band tables read
from [blk+0x2bc0+esi*32]) predicted 12322/24639/18483/6197 — off by >3 orders. m92tail7 fac3 (bc 0,
div 1, cats all 0, mults nz only at esi 0,4,24,36,40,44,48,52): finals are base + 0/1 exactly where
Tc is 0, i.e. the band legs contribute 0 because the control dwords are 0 at that round (snap0 ctrl
[0x94d448..] all zero) — the gate is real, not decorative. cats and mults hold EQUAL nonzero bytes at
the same esi (0,4,24,36,40,44,48,52 = powers of 4), values per faction (fac3 5/18/1/2/1/4/2/2,
fac5 12/10/4/3/2/4/2/1, fac7 1/6/1/1/24/1/255...).

INSTRUMENT DEFECTS found and fixed (all mine/mine-adopted, none a floor): (1) windows closed at the
ENT print 0x48bae9, which fires BEFORE the scan's BASE events -> candidates=0 in m92tail2/3/4; windows
now open at the CALL print (0x5aa030) and close at ENT/TECH (m92tail5/6/7 collect 6-13 BASE per
boundary, G2 TRUE). (2) snapshots: `dump binary memory %s ...` is invalid; a multi-line gdb `python`
block inside a bp command list aborts the sourced file ("Argument to arithmetic operation not a
number or boolean"); read_memory threw OverflowError; and an ARITHMETIC dump range with a substituted
path poisons the address expression — the range must be LITERAL (0x94e488 0xd61c88 = 8*8380), the
reader's SNAPREGION must not conflate offset with range (0x41b80+0x4000-0x94e488 < 0 -> ValueError).
(3) the TAIL print had idx/fac swapped ($esi is arg0 = the tech index, [ebp+0xc] = the faction) and
printed $edi as a mask (at 0x5a9503 edi is esi+0x950664); BASE `human=` printed $edx = 1<<fac.

OPEN (M92 continues): the census has NEVER been green — the next run needs the dump range extended to
0x94d448..0x966000 so the band gate's control dwords are per-round (they move between rounds: snap0
all 0, live at round 63+ nonzero for records 1-7), plus WHO WRITES 0x94e488 / 0x94e5a8 / 0x94eda8 /
the 0x950664 band tables (the 8 esi positions are powers of 4). Human leg (bVar14, FUN_00625af1) and
the pay-site conflict 0x4f0ca6 vs 0x4efedd still open. Evidence: evidence/m92tail2-7.gdblog;
scratch/m92/{tailcheck,verify7}.py; scratch/m92tail*.out.

## Session 145 (2026-10-28) — M92 NOT accepted: the tail is predicted from the live block (38/41 exact), the offsets were the bug and the block MOVES inside a round

Branch milestone/m92, nothing merged. Three instrument truths, each from instruction bytes or measured adds:
1. category byte `[eax+esi+0x94eda8]` and multiplier `[eax+esi+0x94e5a8]` with `eax=fac*8380` are at
   **+0x920 / +0x120** from 0x94e488 — the +0x1000/+0x1860 I used read zeros and produced the 12312 tails.
2. `0x94dc44`/`0x94dc58` are **BEFORE** the block (+0x7fc/+0x810 from 0x94d448) and the cat-0 factor is
   **2 when [0x94dc44] >= [0x94dc58], else 4** (0x5a95be setge / dec / and 2 / add 2) — inverted in the
   s144 note, which is why fac 2 read 16 where the engine added 8.
3. **The divisor moves INSIDE a round** (fac6 snapshot 1 live 6; fac2 8 live 9), and so can the category
   byte: take the divisor from the TAIL record (read at 0x5a9503 for that candidate), the arrays from the
   round snapshot.
MEASURED, not modelled: the four add sites (scratch/m92probe_adds.gdb) show ONE term per candidate,
`mult*Tc*4/div`; `TAILOUT` at 0x5a9698 is the tail output, and `final` (0x5aa159) is a **POST-tail leg**
on top of it (+1, +29 at r76) — gating on `final` conflated two legs.
ACCEPTANCE `scripts/m92_tail_census.py --tag m92tail14 --poke-index 7 --poke-extra 2,6 --rounds 4
--timeout 100` (fresh load, 41 candidates, 6 scans): **FAIL 5/8** — 41/41 divisors and TAILOUTs clean,
**3 wrong** (fac 5: model Tc, engine 2Tc = a category byte that moved after the snapshot). Replaying the
same snapshots offline with the fixed model: **38/41 exact (m92tail14), 5/5 (m92tail12)**.
NEXT: append the two arrays AT the score (0x94e488+fac*8380+0x120 and +0x920, 128 B at the TAIL hit) so
the last 3 go exact; then the post-tail leg 0x5a9698 -> 0x5aa022.
Evidence: evidence/m92tail9-14.gdblog, m92adds1.gdblog; scratch/m92adds.py, m92probe_adds.gdb.

## Session 146 (2026-10-28) — M92 ACCEPTED: m92tail18 PASS 8/8. The tail rule is exact 39/39; the block is FROZEN within a round and the stale reads were WINDOWS, not the block

Branch milestone/m92. ACCEPTANCE `python3 scripts/m92_tail_census.py --tag m92tail18 --poke-index 7
--poke-extra 2,6 --rounds 4 --timeout 100` (ONE invocation on a fresh m54b_clean load, r51->55):
**VERDICT PASS 8/8** — G3: TAILOUT(0x5a9698) == BASE + simulated tail on **39/39 traced candidates, 0
mismatches, 2 qualifying windows (fac2 win=44 IndEcon nz5/splits5, fac5)**; G8: divisor cross-check
39/39 proven, round +4, TAIL events for the scored factions. Naive one-factor model splits on 19
candidates (the shape discriminates).

THREE HARNESS DEFECTS found and fixed (mine, none a floor) — each one had been reported as a game
finding, which it was not:
1. `c["tdiv"]` was NEVER assigned although G8 reads it -> **G8 was structurally False in every run**
   (m92tail14/15/16/17 all failed it regardless of the game).
2. `tailout[(fac,idx)]` was LAST-wins while the model used the FIRST scan: a re-scan in a later round
   has a different block, so m92tail16's 4 "mismatches" (idx8 tailout 29 then 39) were pairing scan-1's
   model with scan-4's output. tailout + tailbyidx are now FIRST-wins.
3. windows are opened by a CALL and can span rounds (no WIN/ENT close), and the census simulated every
   candidate from the WINDOW's CALL-round snapshot. Candidates now carry their OWN live round (the
   BASE print reads *(0x985afc) at the hit) and are simulated from THAT round's snapshot.

RETRACTION (this session, from the new instrument): **the category/multiplier arrays and the divisor do
NOT move inside a round.** The TAIL hit now appends 64 B mults (0x94e5a8+fac*8380) + 64 B cats
(0x94eda8+fac*8380) per candidate (scratch/<tag>_tailarrs.bin, hit-ordered); compared to the
candidate's own round snapshot: **0/39 (m92tail15) and 0/19 (m92tail17) differ**, and
divisor_cross_check_proven == 39/39 bad=0 (m92tail15/18). So s145's "the divisor moves inside a round
(fac6 snapshot 1 live 6)" and "3 misses = a category byte that moved after the snapshot" were defects
2/3 above, not block motion. The block DOES move BETWEEN rounds (m92tail16: fac2 mult(esi1) 4->5 at
r56, dc58 1->2 at r57 and 2->4 at r58 -> the cat-0 factor flipped 2->4) — which is exactly what the
per-candidate round stamp now tracks.

BOX: brief BLOCKED twice (screen 'dialog' -> normalize_screen() -> hud; credit 0 -> the printed reload
recipe m54a_load --relaunch -> m54g_prep -> smac_play --turns 1 -> m57_ui_enqueue --base-index 18
--cell-item 2 --inserts 1 -> READY). m92tail17 (r59, a degraded box) scanned only 3 factions -> 0
qualifying windows -> FAIL 5/8: the census needs a FRESH load (8 factions queued); the acceptance was
re-run as m92tail18 on a reload, not weakened.
NEXT (M93): the POST-tail leg 0x5a9698 -> 0x5aa022 (the SCORE at 0x5aa159 minus TAILOUT: +1/+29 at
r76, +155 for fac2 idx8 in m92tail15/18 — final 186 vs tailout 31). Evidence:
evidence/m92tail15-18.gdblog; scratch/m92tail1[5-8].out, scratch/m92tail18_snaps.bin + _tailarrs.bin.

## Session 148 (2026-10-29) — M93 NOT accepted: the POST ladder predicts 9/13; 4 apply sites have no breakpoint, the specials' within-round freeze is unproven

Branch milestone/m93. ACCEPTANCE `python3 scripts/m93_post_census.py --tag m93post2 --poke-index 7
--poke-extra 2,6 --rounds 4 --timeout 100` (fresh m54b_clean load, r50->55): **FAIL 8/9** — G1-G8 all
green (base 27/27, tail exact on 40 candidates, divisor cross-check 40/40 bad=0, 2 qualifying windows
fac2/fac5, ST/RB + winner name read back), **G9_post_tail_ladder_final False: 13 candidates predicted,
4 mismatches; splits vs the final==tailout null 11, vs the final==tailout*5 null 13.**

THE POST LEG 0x5a9698-0x5aa022, from instruction bytes: ebx = idx reloaded at 0x5a969b; the leg is
SKIPPED (return = tailout) when `[0x985c1c+idx]` carries the faction bit (0x5a96e0); else `call
0x5312d0` — it returned 0 for all 82 traced candidates in both runs — and only if nonzero the
ds:0x985a9c leg may ×4 (0x5a9738 `lea edi,[ecx*4]`). Then a cascade, each stage applying iff idx is IN
its set = {a hard-coded tech} ∪ {prereq-ancestors of a LIVE special}: A(47, 0x9305e8/ec) ×3, B(61,
0x930850/854) ×2, C(64, 0x9308d4/8d8, depth 2) ×2, D(35, 0x9303d8/3dc, depth 1) ×2, E(59, 0x9307f8/7fc)
×2, FIM ((demand[0x94d81c]+1)×2; needs rec+4 bit 1, no faction knowing idx, ac4 bit 0x200 clear), G
(0x98582c) ×2 only when [0x927a8c+fac*1436] > 0, else the 0x93325c/0x933268 legs (×2, ×2, +1 at
0x5a99cc `inc edi`, then ×2 at 0x5a9a21 when ac4 bit 0x200 clear), q = [blk+0x94dc28]/clamp
([blk+0x94e488],1,0x270f) added once when q > demand[0x94d81c] and idx is in the closure of
0x984fec/0x984fbc/0x98531c/0x98534c, **0x5a9c17 ×2 keyed on 0x9851cc and 0x5a9c68 ×3/2 keyed on
0x9851fc (both only when [0x927a80+fac*1436] > 0) — NEITHER is in the model**, the 21-entry era table
0x92b954 (flag byte at -4; idx == id → ×3/×4, idx == pr1/pr2(id) → ×2/×3), 0x5a9df3 ×3 over the
89-tech scan, 0x5a9eb5 ×2 (×4 human) keyed on 0x98adee, then the 0x92b076 exit gate and the band scan
0x5a9f83-0x5aa022 (×3/×6 at 0x5aa004, ×2+4 at 0x5aa01b — 0 events in 82 candidates).
`0x5a9020(a, X, d)` = a == X or a is a prereq-ANCESTOR of X within d levels.

RETRACTION: the s146 ledger line "the 0x5aa022 block makes final = TAILOUT*5" is WRONG — the ×3/×2
epilogues never ran; the ×5-looking deltas are the cascade (×2+1, ×2×2, ×3 then ×2).

MISMATCH CAUSES, both model/instrument and not the game: (1) fac2 idx44 (19->39) and fac5 idx13
(28->56): the engine applied an ×2 the model has no leg for (the missing 0x5a9c17/0x9851cc leg), and 4
apply sites have NO breakpoint — 0x5a9c17, 0x5a9c77, 0x5a9df3, 0x5a9eb5. (2) fac5 idx4 (model 21,
engine 11) and idx45 (model 14, engine 7): the MODEL fires PE2 where the engine did not — and note the
`fired=` list on a LADDER-MISMATCH line is the model's own prediction, not observed events. Likely
cause: the model reads the specials from the candidate's ROUND-BOUNDARY snapshot while the ladder reads
them live mid-round; M92 proved the within-round freeze only for the 0x94e488 block, NOT for the
0x9307xx specials.

NEXT (M93 continues): add the 5 apply-site breakpoints (gdb blocks ready in scratch/m93/apply_patches.py
at 0x5a9c14/0x5a9c74/0x5a9df0/0x5a9eb5/0x5a9f83), add the 0x9851cc/0x9851fc legs and the
0x98531c/0x98534c q-gates, print the specials at the PENTRY hit (live timing) instead of the round
snapshot, re-run. Evidence: evidence/m93post1.gdblog (run-1 trace, 6 scans / 41 candidates),
evidence/m93post2.gdblog (the failing acceptance); scratch/m93post2.out, scratch/m93/{analyze1,
analyze2}.py. Box: fresh load r50->55, census ran, nothing queued at U. Base.

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

## Session 152 (2026-10-29) — M97 ACCEPTED: m97credit3 PASS 11/11. base+0xd0 (credit) is RECOMPUTED EVERY ROUND by FUN_004e93f0; the "written only at record init" trap is RETRACTED

Branch milestone/m97. ACCEPTANCE `python3 scripts/m97_credit_watch.py --tag m97credit3 --boundaries 2` (ONE invocation, m54b_clean, University Base row 0x95da10, rounds 54->56): **PASS 11/11** — G1 4 HARDWARE watchpoints armed (CREDIT +0xd0 0x95dae0, GROSS +0xc0, UPKEEP +0xf0, DISPCOPY +0x94); G2 rounds 54->56, both boundaries rc=0; G3 **12 store executions (6 x S1 0x4e9557 + 6 x S2 0x4e957f)**; G4 every writer and every `*(int*)($ebp+4)` return pc mapped by containment; G5 **12/12 stored values == the prediction computed from the live record AT the hit** (S1 = [+0xc0]-[+0xf0], S2 = old credit - [+0xe0]); G6 read-back credit == last store, +0x94 == credit == c0-f0-e0; G7 no gaps; G8 the +0xd0 watchpoint saw ONLY the two static store pcs; G9 tracer 0; G10 0 unparsed; G11 stores in 3 distinct rounds. m97credit1 FAIL 9/10 (2 `[New LWP]` banners not whitelisted) and m97credit2 FAIL (0 CREDIT events) — INSTRUMENT fixes both times, floors never edited.

- WHO: **FUN_004e93f0** (the base income recompute) writes +0xd0 twice per call: 0x4e9557 `mov [eax+0xd0],edx` (= [eax+0xc0] - [eax+0xf0]), 0x4e9562 zeroes [eax+0xe0], 0x4e957f `mov [eax+0xd0],ebx` (= credit - [eax+0xe0]), then the mirror 0x4e9590 `mov [eax+0x94],edx`. eax = ds:0x8f0d60 = the current BASE RECORD pointer. A scan of all 734,503 .text instructions finds only SIX stores to `[reg+0xd0]` anywhere: these two, 0x5ba9e8 (an ebx-zeroing sweep over +0xa0..+0xe8 = base creation), 0x6310c6/0x631154 (record init) and 0x6315e2 (`= 0`). **The income add 0x4ef7f6 and the clamp 0x4eff20 write [+0x40] STORAGE, never +0xd0** — they only read credit, so the M95 guess is ruled out by the bytes.
- WHEN: **every round, in the current player's own segment** (cp=3 on all 42 events): callers FUN_004f5a70 (the per-base turn stage: call 0x4f5ad2 after 0x4ef6d0/0x4f26e0/0x4ee410, and call 0x4f5b46 after 0x4e8d60/0x4e78e0/0x4e92c0; FUN_004f5a70 is itself called at 0x5206d3) and the recalc helper FUN_004eb6b0 (call 0x4eb6db; it runs 0x4e8d60 -> 0x4e78e0 -> 0x4e92c0 -> 0x4e93f0 whenever arg1 != 0; many UI callers from 0x40b232 on). 2-3 recomputes per round for one base.
- INPUTS: GROSS [+0xc0] is rebuilt from 0 every call by **FUN_004e78e0** (reset 0x4e79a8, +1 per facility 0x4e7c19, +1 at 0x4e85c1); UPKEEP [+0xf0] = DAT_008f0c38 + DAT_008f0c4c (store 0x4e9544) — the WHOLE-FACTION upkeep total, so one facility built anywhere raises every base's upkeep. Observed live: r51 f0 3->4 -> credit 0->-1; r52 c0 3->4 -> **-1->0** — the M95 observation reproduced exactly.
- gdb LAW (new trap): a HARDWARE watchpoint only REPORTS a value CHANGE — gdb re-evaluates the expression and continues silently, so a recompute that lands on the same credit logs NOTHING (m97credit2: 15 GROSS stores, 0 CREDIT events). Count stores with silent breakpoints AT the store instruction (register-only condition `$eax==row`), not with a watchpoint.
NEXT (M98): the sibling slot [esi+0x94d800] (live -1,81,128,86,166,128,77,64 — >= 89, NOT tech indices) and the band flag [esi+0x94d430] bit 0x40 setter; then ds:0x926bd4/0x920434 naming, chooser case 7, cursor print 0x49771c, WORD ds:0x98adee. Evidence: evidence/m97credit1-3.gdblog; scratch/m97credit*_seq.jsonl. Box: m54b_clean r56, credit -1, c0 4 f0 5 e0 0, pending 0, q0 stale 2.

## Session 153 (2026-10-29) — M98 ACCEPTED: m98budget4 PASS 11/11. [fac*8380+0x94d800] is FUN_005aab70's memoized per-faction ADVANCE THRESHOLD, the gate against the accumulator [fac*8380+0x94d7f8]

Branch milestone/m98. ACCEPTANCE `python3 scripts/m98_advance_budget.py --tag m98budget4 --boundaries 2` (ONE invocation, m54b_clean, rounds 60->62, `[fac*8380+0x94d7f8]` poked to field+1 per boundary for facs 1-7 to ARM the grant, gdb detached only after cur_player returned to the human): **PASS 11/11** — G3 13 A0->A1->A2 triples (acc reset -> -1 -> store) on one block; G5 **13/13 stored values == the Python model of FUN_005aab70 computed from the inputs printed AT the hit** (fac1 151,176; fac2 176,203; fac3 135; fac4 241,271; fac5 151,176; fac6 168,194; fac7 128,151); G6 acc >= threshold at every reset; G7 read-back 7/7 == last store; G8 the fac3 HARDWARE watchpoint saw ONLY 0x5aaf71/0x5aaf7f; G9 tracer 0; G10 0 unparsed. m98budget1 ABORTED (the ARMED printf ate the bp blocks: one placeholder used twice), m98budget2 FAIL 9/11 and m98budget3 FAIL 10/11 on INSTRUMENT bugs (watchpoint pcs are store+instruction-length; SIGINT detach lines unparsed; detach happened while the AI upkeep was still playing, so fac1/fac2's last recomputes were unlogged) — floors never edited.

- STATIC: exactly FIVE references to 0x94d800 in all of .text. Reads 0x593483 (FUN_0058fa40, shard_013.c:35399: `FUN_005aab70()/2 <= [fac*8380+0x94d7f8]` — the "halfway to the next advance" test) and 0x5aab8f (inside aab70). Writes 0x59f0c7 `= -1` (FUN_0059ec90, 0 events in these windows) and 0x5aaf67 `= -1` + 0x5aaf79 `= eax` (FUN_005aadf0's grant path, `call 0x5aab70` at 0x5aaf71 between them).
- THE LAW (FUN_005aadf0 C; per-base upkeep tail 0x4f5c2e FUN_004f34b0 <- FUN_004f5a70 <- 0x5206d3): `[+0x94d7f8] += param_2` (AI factions double param_2 on the 0x5aae04-0x5aae71 legs); if (netgame || slot >= 0) { t = aab70(fac); if (t <= acc) { print "Researched Advance"; FUN_005aaa20(fac) consumes the work-item slot; FUN_0047f590(fac,item); acc = 0; field = -1; field = aab70(fac) } }; the `[+0x94d430] & 0x40` leg prints "Secret Advance" and consumes a SECOND item.
- CACHE LAW (live): 63 aab70 ENTRY events, cached >= 0 on 42, and the field never moved outside the grant path — aab70 returns the memo unchanged; only the -1 leg recomputes.
- THE FORMULA (model 13/13 live + 7/7 offline at r60): L = clamp([+0x94d804]*2 - [+0x94d790] + [+0x94d78c], 2, 9999); v5 = L/2; human = (1<<fac)&[0x985b10]: x = [+0x94d438] then 4x+8, mul = 3; AI: x = era (+1 if < 3) then 29-3x, mul = era; v2 = 12-v5 replaced by min(x, v5+12) when it is <= both; cap = ((v2+x2)*mul)/10+1 with x2 = ((ac4&0x20|0x40)>>5 * v2)>>1 clamped by v5 - [0x985afc]/((ac4&0x20|0x40)>>3); m2 = (((max7/2 - mul) - v5)+7)/(8-mul) clamped by cap, max7 = max over facs 1..7 of ([+0x94d78c] + 2*[+0x94d804]); v5b = clamp(v5 - sign([+0x94d728]), 1, 99999); res = clamp([0x92a390]*v5b*((v2+x2)-m2)/56, 1, 99999999) after the [0x92a298] and [0x927a88+fac*1436] percent legs and +50% iff ac4&0x20. GHIDRA REASSIGNS local_8 to 3/era before the cap and the (8-local_8) divisor — using L there cost 3 mismatches (68/101/151 vs live 64/77/166).
- OPEN: what [+0x94d78c] counts (12->14->16 for fac3 while it builds; it drives L and max7); who feeds param_2 (the accumulator's progress source); why FUN_0059ec90's -1 never ran in these windows; what FUN_0058fa40's half-threshold test decides.
NEXT (M99): the param_2 producer — 4 HARDWARE watchpoints on `[fac*8380+0x94d7f8]` x 4 factions over --boundaries 2, name the writers by containment. Evidence: evidence/m98budget1-4.gdblog; scratch/m98budget*_seq.jsonl; scripts/m98_advance_budget.py. Box: m54b_clean r60->62, 13 advances granted across facs 1-7, fields -1,176,203,135,271,176,194,151.

## Session 154 (2026-10-29) — M99 ACCEPTED: m99p3 PASS 13/13. param_2 has ONE producer: FUN_004f34b0 scales base_record+0x104 by the faction research multiplier and pushes (scaled+carry)/100

Branch milestone/m99. ACCEPTANCE `python3 scripts/m99_param2.py --tag m99p3 --boundaries 2` (ONE invocation, m54b_clean r66->68, 4 hw watchpoints on [fac*8380+0x94d7f8] facs 2,3,5,6 + 11 silent bps, fac3 [0x94d808] poked 0 per boundary): **PASS 13/13** — G3 41 calls over 2 rounds; G4 every pc mapped; G5 **41/41 C1 return pcs == 0x4f35d0** (the only call site in .text, inside FUN_004f34b0); G6 **41/41 pushed param_2 == the model**: scaled = (clamp([fac*8380+0x94d6a4],-5,5)+10) * raw * 10, remainder scaled%100 into [fac*8380+0x94d808], +100 to the dividend when the new carry > 99, param_2 = scaled/100 (C trunc, magic 0x51eb851f at 0x4f35b8); G7 carry + c30 41/41 ([fac*8380+0x94dc30] += raw at 0x4f3560; every hit's carry == the previous stored value); G8 acc law 40/40 new == old + ebx AND **ebx == param_2 on 40/40 -> the doubling NEVER runs**; G9 read-back 4/4 == /proc; G10 watchpoints saw only 0x5aaef1 (FUN_005aadf0) and **0x56e024 = FUN_0056df40 `inc [ebx+0x94d7f8]`, a second live accumulator writer**; G13 controlled poke: fac3 carry 0 (raw 3, mult 2) -> param_2 3 where the pre-run carry 60 gives 4. m99p1 FAIL 10/13 + m99p2 FAIL 11/13 were MY instrument/gates, floors never edited.

- WHO/WHEN: FUN_004f34b0 (per-base upkeep tail, called at 0x4f5c2e from FUN_004f5a70) runs once per base per round (19-21 bases/round live). raw = [base_record+0x104] at 0x4f34d9 (DAT_008f0d60); halved 0x4f3513-0x4f351a when the FUN_00507410(0x17) policy leg fires ([0x95da9c + fac*0x130 + idx] & mask); zeroed 0x4f3546 if round < mult*-5, 0x4f3556 if round < 5 && [fac*8380+0x94d438] < 2.
- RETRACT (M98 framing): "the AI legs 0x5aae04-0x5aae71 DOUBLE param_2, the human never" — live, NO faction doubles: 0x5aae1a `call 0x5312d0` returns 0 (single-player) so every path jumps to 0x5aaec7; the doubling block 0x5aaec1 logged 0 events in 3 runs.
- POKED-FIELDS-ARE-UNDONE: [fac*8380+0x94d6a4] poked -5, read back -5, live **0** at 0x4f3558 both boundaries; all five .text references to 0x94d6a4 are LOADS — the per-round writer uses another addressing form (OPEN). base+0x104 too: FUN_004eaa10 (called at 0x4f5ad7, just before the tail) rebuilds it (shard_012.c:18136-18337).
- gdb LAW: a silent bp at the pc a hw WATCHPOINT REPORTS (store+length = 0x5aaef1) is EATEN by the watchpoint — 27 of 37 store read-backs vanished (m99p1 G8). Put the read-back bp one instruction later (0x5aaef3) and read memory, not the register.
NEXT (M100): who writes [fac*8380+0x94d6a4] (the research multiplier) every round — 4 hw watchpoints on it x 4 factions in the m99_param2 shape. OPEN: FUN_0056df40's +1 to the accumulator; what builds base+0x104; the [0x94d430] bit 0x40 setter; WORD ds:0x98adee; the negative-queue producer reaching branch B. Evidence: evidence/m99p1-3.gdblog; scratch/m99p*_seq.jsonl; scripts/m99_param2.py. Box: m54b_clean r68, accs fac2/3/5/6 = 81/23/33/39, University pending 1 head 2 storage 0.

## Session 155 (2026-10-29) — M100 ACCEPTED: m100mult2 PASS 13/13. [fac*8380+0x94d6a4] is the LAST dword of an 11-dword per-faction block that FUN_005a15a0 rebuilds from zero every round; the caller is FUN_005a1830(fac), a stage of the per-player turn sequence

Branch milestone/m100. ACCEPTANCE `M100_WFACS=1,2,3,6 python3 scripts/m100_mult_watch.py --tag m100mult2 --boundaries 2` (ONE invocation, m54b_clean r52->54, 4 hw watchpoints on the multiplier facs 1,2,3,6 + silent bps 0x4f352e (the consumer) and 0x520909 (the insn after `call 0x5a1830`); facs 1-7 poked to live+10 before each boundary): **PASS 13/13** — G4 all 3 store pcs contained in FUN_005a15a0; G5 6/6 (fac,round) pairs = the exact rebuild shape [0x5a15b5 new=0 then 0x5a16db/0x5a17a0 new=final]; G6 all 7 pokes undone; G7 last store == /proc; G8 restored == pre-run (-2,2,-2); G9 16 CALL events = facs 1-7 x 2 rounds, cp==fac 16/16; G10 0 consumer reads saw the sentinel; G12 tracer 0; G13 0 unparsed. m100mult1 FAIL 9/11 was MY instrument (fac2 cannot log — new trap), floor never edited.

- WHO: FUN_005a15a0(param_1, param_2 = the block, param_3 = fac, 0, param_5) zeroes 11 dwords (`rep stos` 0x5a15b3, reported 0x5a15b5), adds 4 category tables (`*(int*)(param_1+cat*4)` = a record index; rows are 11 dwords at &DAT_0092babc + cat*0xd4 + rec*0x2c) at 0x5a16d9 (reported 0x5a16db), and when param_5 == 0 adds the 11-dword array at &DAT_0094d700 + fac*0x20bc at 0x5a179e (reported 0x5a17a0); then the &DAT_00927ac0 legs (type 4 clamp 0..999, type 10 halve-if-negative) and the DAT_00985b70/0x985b98 +1-to-slot-5 / +2-to-slot-2 legs.
- WHERE: FUN_005a1830(fac) passes &DAT_0094d67c + fac*0x20bc, so **0x94d6a4 = block A + 0x28 = slot 10 of 11** — that is why .text mentions 0x94d6a4 only as a LOAD (0x445abf, 0x4aac96, 0x4f352e, 0x4f3566, 0x56dffa): every store goes through the pointer. Blocks A 0x94d67c-0x94d6a7 (mult = slot 10), B 0x94d6a8-0x94d6d3, C 0x94d6d4-0x94d6ff, source 0x94d700-0x94d72b; 1830 also shifts 4 dwords at 0x94d668 and calls 15a0 three times (A, B, C with param_5 = 1).
- WHEN: `call 0x5a1830` exists at TWO sites, 0x4dbf8e and **0x520904 inside FUN_005208f0** (the per-player turn sequence, the family of M94's FUN_00556690 @0x52094f). Live: 16 CALL events at 0x520909, edi = the faction, cp == fac on 16/16, 2 per faction per round.
- VALUES: fac3 +2 and fac6 -2 arrive from the 0x94d700 add (0x5a17a0), fac1 -2 from a category record (0x5a16db); every other slot-10 add wrote 0 (unchanged -> suppressed). r54 mults {0,-2,0,2,0,0,-2,0} == r50's.
NEXT (M101): what writes [fac*8380+0x94d658] (the 4 category record indices) and the source array [fac*8380+0x94d700] (its slot 10 gave fac3 +2 / fac6 -2); what the &DAT_0092babc category records are; FUN_005a1830's other caller 0x4dbf8e. Evidence: evidence/m100mult1-2.gdblog; scratch/m100mult*_seq.jsonl, scratch/m100mult*.out; scripts/m100_mult_watch.py. Box: m54b_clean r52->54, University pending 1 head 2 credit 0, all 7 mults poked and restored.

## Session 157 (2026-10-29) — M102 ACCEPTED: m102hit3 PASS 14/14. The rebuild model evaluated AT the store sites is EXACT; the D-accrual is NOT per-round (0 events, D10 unmoved in 2 full rounds)

Branch milestone/m102. ACCEPTANCE `python3 scripts/m102_rebuild_at_hit.py --tag m102hit3 --boundaries 2` (ONE invocation, m54b_clean r55->57, 15 silent bps — CAT 0x5a16d9 / DADD 0x5a179e / CLAMP 0x5a1807 register-only conditions on A10 facs 1,2,3,6 + ENT 0x59ec00/0x59ec90 + CALL 0x520909; NO pokes — bps fire on execution, so the watchpoint unchanged-store suppression is moot): **PASS 14/14** — G3 9 complete rebuilds (CAT 4/4 + DADD 1/1 every one; rounds per fac {1:[56,57],2:[56,57],3:[55,56,57],6:[55,56]}); G4 36/36 stored == old + src AT the hit; G5 36/36 src is one of the four row10s printed in the same event; G6 every chain 0 -> final (rep-stos reset proven at the first hit); G7 9/9 DADD src == D10 printed at the hit; G8 CLAMP 0 events == predicted from the live table (no type 4/10 entry with key 10); G9 ENT 0 events AND D10 unchanged across the window (consistency law); G10 cp == fac 45/45; G13 negative leg exercised (fac1 -2 from a row, fac6 -2 from D); G14 per-fac last DADD (old+src) == /proc A10 {1:-2,2:0,3:2,6:-2}. m102hit1 FAIL 10/14 and m102hit2 FAIL 12/14 were BOTH my instrument (gdb printf escape + forward grouping — laws written to skill instrument-laws.md), floors never edited; run 2's data was re-verified offline after the fixes and passed every arithmetic gate.

- MODEL AT THE HIT (FUN_005a15a0, block A slot 10): reset 0 (rep stos 0x5a15b3); 4x `block10 += row10(cat)` at 0x5a16d9 (row = 0x92babc + cat*212 + idx(cat)*44, dword at +40; edi and the row pointer advance 4 per slot in the 11-slot loop, so slot 10 gets exactly one add per category); then `block10 += D10` at 0x5a179e (11-dword add loop, source 0x94d700 + fac*8380); clamp loop (count @0x927a9c + fac*1436, types @+0x20, keys @+0x40: type 4 clamp 0..999 ALWAYS stores, type 10 halves only if < 0) can hit slot 10 only via a key-10 entry — this box has none; skip leg 0x5a1601-0x5a1671: a category skips its add iff row10 < 0 AND (cat,idx) in {(3,1) gated on byte[0x95da14+304*ds:0x985b90], (3,3),(2,1) gated on byte[0x95da14+304*ds:0x985b9c]} == fac — era globals are -1 here, inert. Project type 5/6 legs mutate [edi] BEFORE the add, so they are baked into `old` read at the hit.
- **THE ACCRUAL IS NOT PER-ROUND**: 0x59ec00/0x59ec90 (the only displacement stores to 0x94d700, M101 census) ran ZERO times across r55->57 (2 complete rounds + 2 partial) and every D10 held its value — so M101's "+10 for facs 1-7 across r54->56" came from a trigger absent here (auto-advance while the human turn is pending, or a research completion) or from a POINTER-form writer the displacement census cannot see. OPEN: who writes D.
NEXT (M103): the D-accumulator writer — a pointer-form census of 0x94d700 (M97 lesson: RMW through a copied register evades displacement greps) plus a hardware watchpoint on D10 fac3 while the box auto-advances rounds (let it idle 2 rounds, read before/after); then what the 0x92babc category records ARE and who chooses the record index at 0x4b2715. Evidence: evidence/m102hit1-3.gdblog; scratch/m102hit*_seq.jsonl, scratch/m102hit3.out. Box: m54b_clean r57 cp3 hud, mults {1:-2,3:2,6:-2}, University pend 1 head 2.

## Session 158 (2026-10-29) — M103 RUN, NOT ACCEPTED (no green acceptance, no merge): the D-accumulator writer is FUN_0059ec00 — a REBUILD FROM ZERO off the per-faction record list, NOT per-round

Branch milestone/m103. ACCEPTANCE `python3 scripts/m103_d_rebuild.py --tag m103d2 --boundaries 2` (m54b_clean r59->61; 17 silent bps — ENT 0x59ec00/0x59ec90, RESET 0x59ec26+0x5a0440, ADD 0x59ec68+0x5a0471, DADD 0x5a179e, the 4 caller sites, STOP 0x520909; pokes facs 3+6 D = model+77; then a controlled call of the writer at the STOP bp): **FAIL 6/13** — PASS G1 model==live D 8/8, G2 pokes 22/22 landed, G4 pre-call ENT/ADD/RESET=0, G9 CONTROL fac6 KEPT the sentinel [77,77,79,77,77,77,77,76,78,77,75] (src=75 consumed at 0x5a179e), G11 SITE=0 twin=0, G13 tracer 0 / unparsed 0 / rc 0 / restore 22/22; the 7 failing gates all need the controlled call, which gdb aborted. m103d1/d2 died on printf arg-count bugs, m103d3 on the abandon, m103d4/d5 on my reversed call frame (SIGSEGV) — floors never edited.

- WHO/WHAT: [fac*8380+0x94d700] is 11 dwords; a grep of ALL of .text for 0x94d700 finds ONLY two store sites — FUN_0059ec00 `rep stos DWORD PTR es:[edi],eax` 0x59ec24 (0xb dwords, eax=0) + `add DWORD PTR [ecx*4+0x94d700],ebx` 0x59ec68, and the SAME block inline in FUN_0059ec90 (rep stos 0x5a043e, `add [ecx*4+0x94d700],esi` 0x5a0471); ecx = fac*2095+key (2095*4 = 8380). Every other mention is a load (FUN_004b3050/004b47f0/004e47d0/00535c60; FUN_005a15a0 adds D into block A at 0x5a179e).
- LAW: zero the 11, then for each entry of the record block at 0x927a9c+fac*1436 with TYPE==3 do D[KEY] += VAL — count +0x00, TYPE +0x04, KEY +0x24, VAL +0x44, entry stride 4 (parallel arrays; the SAME block M102's clamp loop reads: type 3 = add to D, 4/10 = the clamps). Model == live D 8/8 on FIVE loads: fac3 [...,-2,0,2] from (3,10,2)+(3,8,-2); fac6 from (3,10,-2),(3,8,1),(3,2,2),(3,7,-1).
- WHEN: NOT per round. Four callers — 0x4dbf6f (FUN_004dbf40, the s_RESETALLFAC cheat, UI message 0x30077), 0x4e061b (FUN_004e03d0, message 0x30075), 0x57ce48 (FUN_0057c550), 0x57eee0 (FUN_0057ecf0): the new-fac/setup paths (copy a 1436-byte template per faction, iVar9 < 8). Live: 0 events at all four, at FUN_0059ec90 and at the twin stores across 2-boundary windows, while the consumer 0x5a179e fired on the poked sentinels.
- DECISIVE (m103d3): forcing FUN_0059ec00(3) at 0x520909 EXECUTED the writer — `RESET fac=3 base=0x953934 v0..v10=0`, `ADD fac=3 key=10 old=0 val=2`, `ADD fac=3 key=8 old=0 val=-2` — exactly fac3's two type-3 entries; fac3's D read back == the model afterwards, fac6 (never called) still held the sentinel.
- OPEN: who APPENDS the type==3 entries (the producer behind M101's +10 drift); why FUN_0059ec90's twin never runs here; whether 0x30075/0x30077 are UI-reachable.
- TRAPS: a manual call frame needs the RETURN ADDRESS at esp+0 and the arg at esp+4 (my reversed push made param_1 = 0x520909 -> SIGSEGV at 0x59ec34, box dead); gdb ABANDONS an inferior call when a breakpoint hits inside it; a gdb script's own printf lines are not python-format targets, so `%%d` there is a literal percent -> "Wrong number of arguments"; a printf arg-count error inside a bp command list ABORTS the sourced script and detaches. Box: DEAD. Evidence: evidence/m103d1-5.gdblog; scratch/m103d*_seq.jsonl, scratch/m103/probe.py.

## Session 159 (2026-10-29) — M104 ACCEPTED: m104w3 PASS 12/12. Nobody APPENDS the record entries mid-game — the per-faction 1436-byte record block is LOAD-time data (m54b_clean.SAV holds it verbatim at stride 1436) and no round event writes it

Branch milestone/m104 (ff-merged from milestone/m103 for footing: M103 scripts are not on main). ACCEPTANCE python3 scripts/m104_append_watch.py --tag m104w3 --boundaries 3 (ONE invocation, m54b_clean r57->60, Korolev Center pending 1 head 2 queued first): **PASS 12/12** — G1 4 hw watchpoints armed (count fac1 0x928038, fac3 0x928b70, fac6 0x929c44 + CONTROL fac3 accumulator 0x953a2c); G2 rounds 57->60; G3 6 ACC events, every pc 0x5aaef1 = FUN_005aadf0 (the same machinery logs a value change, so a count write WOULD have logged); G4 126 WALK events at the clamp-loop count read 0x5a1689 (factions 1/2/4 — that leg only reaches the site for those three); G5 0 count-change events; G6 read-back counts [0,6,5,4,3,4,5,3] == baseline for ALL 8 factions; G7 model==live D 3/3 at both ends; G8 0 events at FUN_0059ec00 or its 4 caller sites; G9 the .SAV contains the live 100-byte count+TYPE+KEY+VAL image — fac1 0x113b4, fac3 0x11eec, fac6 0x12fc0, consecutive at stride 1436 (fac0 base 0x10e18); G10 0 unparsed; G11 tracer 0; G12 0 gdb errors. m104w1 raised NameError (json) AFTER the window (events re-parsed offline, laws kept); m104w2 FAILed 11/12 on gdb startup chatter (debuginfod banner + [Inferior 1 ... detached]) not whitelisted — floors never edited, re-run.

- LAYOUT (bytes + live reads): count at 0x927a9c+fac*1436, then THREE parallel stride-4 arrays: TYPE +0x04, KEY +0x24, VAL +0x44, 8 slots each (0x20 spacing; FUN_0059ec00 anchors on +0x24 and reads TYPE at [p-0x20], VAL at [p+0x20]). Live counts: [0,6,5,4,3,4,5,3].
- WHY A DISPLACEMENT GREP CANNOT FIND THE WRITER: every one of the 46 mentions of 0x927a9c/0x927aa0/0x927ac0/0x927ae0 in .text is a load or cmp in a scan loop (0x40d9f4 0x4e4cd9 0x4f37b3 0x4f3e5d 0x4f47ba 0x4fcdf3 0x508c50 0x522ad4 0x589089 0x5a0087 0x5a0443 0x5a1689 0x5a78d0) — not one store. The hardware watchpoint on the count is the instrument.
- ANSWER: no round event appends on this box. The entries arrive with the save, FUN_0059ec00 (the only writer of D) never runs in rounds, so D — and the research multiplier's D leg — is FROZEN from scenario setup onward; M101's +10 drift was M100's poke, not a game write.

NEXT (M105): who writes the block at SETUP — attach gdb at process start (before the save load) with the same 4 watchpoints and name the load-time writer (save loader vs the FUN_0057c550/FUN_0057ecf0 1436-byte template copy); then what the TYPE 0 / TYPE 2 entries are for (fac3 carries (0,2,0) and (2,8,0)) and who consumes them. Evidence: evidence/m104w1-3.gdblog; scratch/m104w*_seq.jsonl, scratch/m104/probe.py. Box: m54b_clean r60, counts [0,6,5,4,3,4,5,3], Korolev Center pending 1.
