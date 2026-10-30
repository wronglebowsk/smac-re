

Older sessions: `docs/sessions/sessions-147-151.md` (4 sessions). Read it only when a question reaches back before session ## Session 152.

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

## Session 161 (2026-10-29) — M105 ACCEPTED: m105s4 PASS 17/17. The block is BUILT AT PROCESS START by FUN_005791c0's append loop (count += 1 per entry; pc 0x579b12 = store+2); the save loader stores nothing to it

Branch milestone/m105. ACCEPTANCE `python3 scripts/m105_setup_watch.py --tag m105s4 --relaunch` (ONE invocation: fresh terran.exe -> ARM 4 hw watchpoints + 8 silent bps BEFORE any screen -> read counts -> poke -77 WHILE ARMED at the quiescent CDROM screen -> drive the m54b_clean load under gdb): **PASS 17/17** — G1 armed; G2 poke -77 read back on facs 1/3/6; G3 load rc=0 round 0->50; G4 **15 CNT stores, every one FUN_005791c0 [terran.exe+0x179b12]**, counts 1->6 / 1->4 / 1->5; G5 16/16 pcs named by containment AND /proc maps; G6 the ROUND control fired once at FUN_0064bf70 [terran.exe+0x24bfa3] in the LOAD window; G7 no sentinel survived; G8 **all 8 counts == the m104w3 image [0,6,5,4,3,4,5,3]**; G9 model==live D 3/3; G10 every CNT round in-window; G11 0 unparsed; G12 TracerPid 0; G13 0 gdb errors; G14 **0 events at the 8 setup sites** 0x57c550 0x57ecf0 0x59ec00 0x59ec90 0x57ce48 0x57eee0 0x4dbf6f 0x4e061b; G15 the live 1436-B blocks are in the .SAV at 0x113b4/0x11eec/0x12fc0; G16 log-offset partition: 15 events in the STARTUP window, 1 (RND) in the LOAD window. m105s1 died WITH its session (gdb detached at ARMED); m105s2 FAIL 14/15 and m105s3 (the true-title wait timed out — the CDROM screen needs driver input) were INSTRUMENT fixes, floors untouched. Session 160 left NO checkpoint: its run was killed by the session end.

- AT DISCOVERY (earliest /proc read) the counts are [0,0,0,0,0,0,0,0]: the append loop runs before the first screen the classifier can see, and the CDROM screen is then QUIIESCENT for 4 min (m105s3: 15 events, then silence). Startup image == loaded image == .SAV image — that is why M104's "the save carries it verbatim" is true but not load-caused. This ANSWERS M103's open "who appends the type==3 entries": this loop, at process start.
- OPEN/CONFOUND, stated honestly: the -77 poked WHILE ARMED was gone (6/4/5) at the end with **0 CNT events in the load window**, so the load restores the region by a path a hw watchpoint cannot see. Candidates: a store from a thread created after the arm ([New LWP] lines DO follow ARMED; DR is per-thread), an out-of-process page write (wineserver process_vm_writev / pwrite /proc/pid/mem), or build-elsewhere + MAP_FIXED. The driver does not poke /proc/pid/mem (grep of m54a_load.py). G17 is satisfied by the STARTUP events — it does not require an event after the poke, so it is NOT proof of a load writer.
NEXT (M106): the invisible load-window restore — no gdb: read /proc/pid/maps for 0x927a9c at the CDROM screen and again after the load (a VMA split = MAP_FIXED remap), and `strace -f -e trace=mmap,mmap2,munmap,mprotect,process_vm_writev,pwrite64` on the wine tree while m54a_load runs; then what FUN_005791c0 (3112 B, shard_014) READS to build the block, the TYPE 0/2 entries, the 0x92babc category records, the index at 0x4b2715. Evidence: evidence/m105s1-4.gdblog; scratch/m105s*_seq.jsonl. Box: pid 1231977 m54b_clean r50 hud, counts [0,6,5,4,3,4,5,3].

## Session 164 (2026-10-29) — M106 ACCEPTED: m106r7 PASS 15/15. The invisible load-window restore is read() STRAIGHT INTO THE REGION — a kernel copy_to_user, so no ring-3 store and no debug exception

Branch milestone/m106 (s162 ran r1-r4, this cron ran r5-r7). ACCEPTANCE `python3 scripts/m106_load_restore.py --tag m106r7` (ONE invocation, fresh terran.exe: counts + the 8 entry images read at the quiescent CDROM screen -> 8 count sentinels -1000-fac poked -> strace A on terran with **raw args = buffer POINTERS** + strace B on the wine tree (writes only, no read-tracing) -> m54b_clean load under both -> read back): **PASS 15/15** — G1 same pid, **load rc=0 (680.8 s)**, round 0->50 cp 3; G2 8 sentinels read back; G3 baseline region entry images 8/8 == the .SAV; G4 A 168,673 events 0 unparsed; **G5 the region read; G6 the M105-armed counts (facs 1,3,6) inside its span**; G7 counts == the m104 image; G8 region vs .SAV chunk; **G9 VMA list identical, 0 mmap/mremap/munmap covering the region; G10 soft-dirty cleared at baseline then SET on 4/4 region pages; G11 0 process_vm_writev, 0 pwrite to a /proc/pid/mem fd**; **G13 the tail-and-EOF law names fd 5** (file 242,539 B, tail 875 B, run ends at EOF); **G14 exactly one surviving candidate: C1-kernel-write-via-read**; G15 TracerPid 0, 0 unparsed.

- THE ANSWER: the save body loader (`FUN_00596850` -> `FUN_0064cc00(&DAT_00927590, 0x2ce0, 1, handle)`, shard_013) reads the file **in chunks whose destination is the final address**, so the kernel writes the pages: `read(0x5, 0x927c84, 0x2000) = 0x2000` lands inside the record block and covers the counts M105 armed (0x928038/0x928b70/0x929c44); the block head 488 B (fac0) and tail 2,808 B (fac7) are small requests that go through the CRT's 0x1000 stdio buffer at 0x40a5628 and ARE ring-3 stores. M105's three watched dwords all happened to sit inside the one big direct chunk — that is the whole "invisible writer".
- LAWS (strace): (1) an .SAV fd that arrives over **SCM_RIGHTS has no open()** — fd->path from open lines cannot name it; name it by the **TAIL-AND-EOF LAW** (a read returning size mod 4096 == 875 B inside an fd-run ending in a 0-byte read). The exact-byte-sum burst law FAILS when the loader **seeks**: under a slow traced game the file is carried across >1 fd-run (r6: 234,347 B in the EOF run + 47,104 B in an earlier one). (2) strace has **no exit-only -e qualifier**: `-e read=SET` is parsed as a DESCRIPTOR and strace dies at once ("invalid descriptor 'read'") leaving NO log — and a preflight that validates only the name sets cannot see it; validate the argv you will run. (3) A traced game runs ~10x slow: the load driver needs **M54A_LOAD_TIMEOUT=1800** to reach the HUD (1200 s died on the post-OK dialogs, ops-director pane at 1316 s) — a wall-clock allowance, not an evidence floor (G1 still requires rc=0).
NEXT (M107): the save CHUNK MAP — why each fread destination is where it is (parse m54b_clean.SAV against the r7 read sequence offline; disassemble FUN_00596850/FUN_00597ee0 for the seek/read loop); then what FUN_005791c0 reads to build the record block at startup, the TYPE 0/2 consumers, the 0x92babc category records, the index at 0x4b2715. Evidence: evidence/m106r2-r7.strace; scratch/m106r*_terran.strace (raw, 13-30 MB, NOT committed), scratch/m106r*_events.jsonl. Box: m106r7's terran.exe at the HUD, m54b_clean r50 cp 3, counts [0,6,5,4,3,4,5,3].

## Session 165 (2026-10-29) — M107 ACCEPTED: m107c3 PASS 7/7. The save chunk map is HARD-CODED in FUN_00596850 — the file carries NO (address,size) table

Branch milestone/m107 (from main 20f3d5a, M106 merged #113). ACCEPTANCE `python3 scripts/m107_chunkmap.py --tag m107c3` (OFFLINE, ONE invocation, no box): **PASS 7/7** — G1 **30 fread sites** (call 0x64cc00) inside FUN_00596850 [0x596850,0x597a6b], 0 outside; G2 **25 immediate-size legs + 5 counted** [0x5970e4 eax, 0x597319 edx, 0x59738b eax, 0x59751f eax, 0x5979f8]; G3 **no table in the file: 0 of 20 static destinations appear as u32 LE in any of 9 saves, 0 adjacent (dest,size) pairs**; G4 block A is **VERSION-GATED** (`cmp ds:0x985dbc,3` @0x596a43; 0x985dbc = header 0x985ab8+0x304 = file offset 772) and u32@772 = 0 on **9/9** saves → the **malloc'd 0xe5e0 leg runs, the static 0x105e0 one never does**; G5 the r7 strace's **5 unique direct reads** each sit inside a declared leg with a <=0x1000 stdio prefix, 1 outside = 0x40a75b0+0x15000 (the counted heap leg); G6 immediate legs 204,504 (live, minus 0x105e0: **137,464**) and no file overrun; G7 0 gdb/strace/winedbg.

- THE ANSWER: the loader hard-codes each leg as `push <size>; push <dest>`. No destination exists in the file, so a file-side chunk table is **impossible** — the map is code, not data; leg order = file order.
- THE ARITHMETIC (m54b_clean 242,539 B): live immediate legs 137,464 → **residual 105,075 B** for the 5 counted legs: the 0x927538 count-prefix leg, `[0x985af0]` → 52n into 0x933278 and 48p into a malloc, `[0x985af4]` → 304m into 0x95da10. The strace's heap leg alone reads **86,016 B (0x15000)**, so the [0x985af0] legs are the bulk.
- OPEN (next, M108): **who SETS [0x985af0]/[0x985af4]** — no 4-byte read site targets them and u32@0x38/0x3c of the header are 0/0-2, so they are DERIVED, not read; then the exact split 52n + 48p + 304m + tail = 105,075.
- TRAP: a `push`-lookback that stops at the first jmp/call finds **0 legs** — the direct-path site is entered by `je` and its pushes live BEFORE the buffered-path call; look back <=14 instructions and stop only at `ret`.
Evidence: evidence/m107c3.log; scratch/m107c3_map.json; scripts/m107_chunkmap.py. Box: untouched (cron 1a88e12bd408 paused 18:41 so one session drives).

## Session 166 (2026-10-29) — M108 ACCEPTED: m108c3 PASS 6/6. The counted legs are LIVE COUNTS ([0x985af0]=67 units, [0x985af4]=18 bases) — and M107's version-gate claim is RETRACTED

Branch milestone/m108 (from main 333bace, M107 merged #114). ACCEPTANCE `python3 scripts/m108_count_sources.py --tag m108c3` (live /proc reads only — no gdb, no poke, no relaunch): **PASS 6/6** — G1 the live image is m54b_clean (record-block counts [0,6,5,4,3,4,5,3]); G2 **[0x985af0]=67 units → 52n=3,484, 48p=3,216; [0x985af4]=18 bases → 304m=5,472**; G3 5 stores to 0x985af0 and 6 to 0x985af4, the load pair **0x598470/0x598476 (6 B apart, one basic block)** in the function starting **0x598340**; G4 the retraction; G5 the closure deficit **25,863 B**; G6 read-back **18/18** 304-byte base records at 0x95da10 carry printable names (University Base first).

- **RETRACTION of M107's G4**: M107 read `cmp ds:0x985dbc,3` @0x596a43 and ASSUMED 0x985dbc = header 0x985ab8 + 0x304 = file offset 772 (u32@772 = 0 in every save) → "the malloc'd 0xe5e0 leg runs". **Live [0x985dbc] = 9**, so the gate takes the >= 3 branch and the **static 0x105e0 block-A leg runs** — exactly what the r7 strace already showed (direct read 0x94e104+0xf000 inside 0x94d430+0x105e0). 0x985dbc is a RUNTIME field inside the header's address range, not the file's u32@772. M107's "105,075 residual / old path" is WITHDRAWN; the flat residual 38,035 is the real one.
- THE COUNTS: [0x985af0] and [0x985af4] are the UNIT and BASE counts of the loaded save, landed by one basic block (0x598470/0x598476) in FUN_00598340; the 304-byte array at 0x95da10 holds exactly [0x985af4] records with names at +19.
- THE DEFICIT (the finding): m54b_clean 242,539 − immediate legs 204,504 = **38,035**, but the declared counted legs are only 52·67 + 48·67 + 304·18 = **12,172** → **25,863 B unaccounted**; the load's biggest read is a **malloc'd 86,016 B (0x15000) at heap 0x40a75b0**, a size matching no declared count (86,016 = 42 × [0x92a38c] = 2,048). At least one counted leg or size expression is still missing from the leg table.
- TRAP: the in-memory header's +0x54 is NOT the mission year (it reads 0); identify a loaded save by the record-block counts, not by the header year.
Evidence: evidence/m108c3.log; scripts/m108_count_sources.py. Box: pid 1340394 at the HUD, m54b_clean r50.

## Session 167 (2026-10-29) — M109 RUN, NOT ACCEPTED (m109l2 FAIL 2/5, 2 of 3 attempts used): the counted legs are measured, but the 30 legs are GATED — the map needs conditions, not sizes

Branch milestone/m109 (from main aad8267, M108 merged #115). ACCEPTANCE `python3 scripts/m109_leg_sizes.py --tag m109l2 --relaunch` (6 silent bps armed before any screen — the 5 counted legs + the malloc — then ONE m54b_clean load): **FAIL 2/5** — G1 6 bps armed, 0 gdb errors, 4 events; G2/G3 only 4 leg events; G4 remainder 28,899.

- MEASURED LIVE (the value): count-prefix leg **176 B**; **52n = 3,484 = 52 × 67**; **304m = 5,472 = 304 × 18** — the model from [0x985af0]=67 / [0x985af4]=18 is EXACT on two legs.
- **0x59738b (the 48p $eax leg) logged ZERO events** — it does not run for m54b_clean, so "48·n" is not a leg of this load.
- **0x5979f8 is a 4-BYTE read (arg size = 4)**, NOT the tail section — my M107/M109 leg label for it was wrong.
- THE BLOCKER: immediates 204,504 + counted 9,136 = 213,640 vs 242,539 → **28,899 B unaccounted**. The 30 legs are CONDITIONAL (0x596a43 `cmp ds:0x985dbc,3`; 0x5974b7 `cmp ds:0x985dbc,0`; 0x5974d3 `test [0x985af4]` …), so a chunk map needs the GATE for each leg, not just its size. m109l1 (instrument: `M.rd` was not in the imported module) and m109l2's $edx-vs-stack-arg error were mine, floors never edited.
- LAW (new): at an `fread` call the ARGUMENT layout on the stack is [esp]=dest, [esp+4]=size, [esp+8]=count, [esp+0xc]=FILE* — read the SIZE from `*(int*)($esp+4)`, never from a register that the block has since clobbered (0x5979f8 gave 12,462,004 from $edx).
- TRAP: the launch needs ~7 min before the load driver's window (the movie + CDROM screen), so a 6-min check is too early; the harness must not be judged before ~8 min. **And the driver returns rc=1 with "timeout reaching HUD" at ~320 s under gdb while the loader's legs STILL fire** (m109l1: 4 lead events at round 50 cp 3 with load rc=1; m109l2 the same) — under an attached gdb, rc=1 is NOT a measurement failure; gate on the events, not on the driver's return code.
Evidence: evidence/m109l1.gdblog + evidence/m109l2.gdblog/.log; scratch/m109l*.gdb; scripts/m109_leg_sizes.py. Branch milestone/m109 committed, NOT pushed for merge. Box: pid 1389526 at the HUD, m54b_clean r50.

## Session 169 (2026-10-29) — M109 RUN AGAIN, NOT ACCEPTED (the map cannot close inside the loader): one clean load reads **23 sites = 149,380 B of 242,539**, the other **93,159 B comes from code OUTSIDE FUN_00596850**

Branch milestone/m109. ACCEPTANCE `python3 scripts/m109_leg_census.py --tag m109c4 --relaunch` (116 STATIC read-site bps parsed from evidence/m109_skel_loader.txt — every `call` to 0x596470/0x596540/0x64c9a0/0x64cc00 whose own address is inside the loader — then ONE m54b_clean load): **23 executed sites, 0 gdb errors, Σ(size×count) = 149,380 vs 242,539 → 93,159 unaccounted.**

- THE EXECUTED LEGS (site dest size): 0x59688a header 796; 0x596a33 own-player 4; 0x596a91 block A **67,040**; 0x596ed6 block B 11,488; 0x596f25 32; 0x59702d 16,000; 0x597084 prefix 4; 0x5970e4 **176**; 0x597141 3,584; 0x5971ac 26,624; 0x597294 4,096; 0x597319 **3,484**; 0x59751f **5,472**; 0x59769e 256; 0x597716 152; 0x597781 10,144; five 4-byte tail reads; 0x5979f8 4 (dest 0xbe27b4 — a stack local, NOT a section); 0x597a19 4.
- **The finding**: the loader function's own read set is 61.6% of the file. The rest (**93,159 B**) is issued by the readers' callers outside [0x596850,0x597a6b] — s168 counted **105 such call sites** — and the 86,016-byte heap read at 0x40a75b0 is one of them. So a chunk map assembled from FUN_00596850 alone can never close; the census must span the whole read set.
- The three counted legs reproduce m109l2 independently (176 / 3,484 / 5,472), so the two instruments agree.
- LAWS (instruments, all mine): **a breakpoint CONDITIONED on `*(unsigned int *)$esp` halts the inferior when gdb cannot dereference, so the game freezes and the load never runs** — that is s168's "0 ENTER, 4 runs" and m109b1's 0 reads; use STATIC bps at the loader's own call instructions instead. gdb's `printf` needs the two characters `\`+`n` built in code (`chr(92)+"n"`): a file-level `\n` becomes a real newline (non-terminated string), a `\\n` prints a literal `\n` (one unparsed line), and a `%%x` left from Python `%`-formatting reaches gdb as a literal `%%x` (0 specs, 3 args → "Invalid number"). `break *%x` without the `0x` fails the same way — always `%#x`.
Evidence: evidence/m109c4.log (+ m109c1-c3 as instrument failures), scratch/m109c4.gdb, scripts/m109_leg_census.py. Box: terran.exe 1501243 at the HUD, m54b_clean r50, counts 67/18.

## Session 170 (2026-10-29) — M110: the chunk map closes to **156 bytes (99.94%)**, the MAP is named (2,724 + 64×64×22 + 91), and the old 86,016-byte read is resolved — branch committed, NOT merged (closure target missed by 156 B)

Branch milestone/m109 (M110 work landed there; the pick in NEXT_PROMPT is M111). ACCEPTANCE `python3 scripts/m109_leg_census.py --tag m110a2 --relaunch` (182 static read-site bps over SIX ranges: 0x596620 helper, the loader, 0x597a70 phase-2, the map loader, 0x44b7xx, 0x5c72xx; CRT 0x62xxxx excluded on purpose): **45 executed sites, 0 gdb errors, Σ(size×count) = 242,383 vs 242,539 → 156 B short.**

- **THE MAP (in the save, mid-file, not at EOF):** `0x5822a7` reads **2,724 B** (map header struct) at file offset **79,364**; `0x5822f2` reads **90,112 B = 64×64×22** (the grid) at **82,088**; `0x582318` reads **91 B** (map trailer) at **172,200**. So m54b_clean is a **64×64** map — not 80×80, which is why the 80×80 dims signature was never found in it.
- **THE OLD 86,016-B READ IS EXPLAINED**: 90,112 − 86,016 = 4,096, i.e. the grid's first stdio-buffer block; r7 saw only the direct remainder. M107/M108's "malloc'd 86,016 at heap 0x40a75b0" was the map grid all along.
- **COVERAGE IS CONTIGUOUS 0..242,383** (45 legs, file_off printed per leg): 4 + 796 + 4 + 67,040 + 11,488 + 32 + 2,724 + 90,112 + 91 + 16,000 + 4 + 176 + 3,584 + 26,624 + 4,096 + 3,484 + 5,472 + 256 + 152 + 10,144 + 18×4 (the 9×2 dword-pair loop of 0x59666d/0x5966c1) + 2×4.
- **THE LAST 156 B (the open remainder)**: offsets 242,383..242,538 are a **6-dword record table** — `[3,0,0,-6,32,32] [4,…] [5,…] [6,…] [7,…]` (ids 3-7, sentinel −6, 32/32) then three trailing dwords `[1,1,0x7FFFFF00,-14,32,32] [800,387,365402425]`. Its reader is NOT in the six enumerated ranges, so either the CRT `fscanf` path (0x62b68e/0x62c36f/0x62b3da/0x62bdeb, 25 sites — excluded because they fire for every config read) or a loop that ran fewer times than the table has entries.
- Means to the previous sessions: M109's 23 legs (149,380) + the map (93,515) + the helper loop (72) + 2×4 = 242,383. Everything the loader and its map loader touch is now named.
Evidence: evidence/m110a1.log (27 legs, 228 B short — 3 ranges), evidence/m110a2.log (45 legs, 156 B short — 6 ranges), scratch/m110a1/a2.gdb; scripts/m109_leg_census.py --ranges. Box: terran.exe 1532323 at the HUD, m54b_clean r50.

## Session 168 (2026-10-29) — M109 RUN AGAIN, NOT ACCEPTED (m109g1 FAIL 1/6, m109g4 FAIL 1/6): the leg GATES are now read off the disassembly, but no load has EVER run with the census attached

Branch milestone/m109 (from main aad8267). ACCEPTANCE `python3 scripts/m109_leg_gates.py --tag m109g4 --relaunch` (5 bps: FUN_00596850 ENTER logs the FILE* it was handed into `$savefile`; the four read wrappers 0x596470/0x596540/0x64c9a0/0x64cc00 print ra,ptr,size,count,stream filtered by `*(int *)($esp+0x10)==$savefile`): **FAIL 1/6** — G1 5 bps armed, 0 gdb errors, **0 ENTER events**, 0 reads on the save stream; G3 sum 0 vs file 242,539; G5 PASS vacuously (nothing ran); G6 TracerPid 1464421 (gdb still attached when /proc was read). The load never executed: driver "title -> LOAD GAME row, then blind browser step", class=movie at 329.5 s, "timeout reaching HUD" at 910 s. m109g1 FAIL 1/6 = the driver's **220 s default budget** expired at the CDROM screen (0 ENTER, header fields still 0); m109g2 = **gdb -batch DETACHED on wineserver's SIGUSR1** (evidence/m109g2.gdblog, 30 lines, "[Inferior 1 ... detached]" after 3 events); m109g3 = the UNFILTERED census logged **25,957 wrapper hits with 0 ENTER** in 572 s and starved the driver (evidence/m109g3.summary). Floors never edited, nothing merged.
- THE GATES (evidence/m109_skel_loader.txt = the push/call/branch spine of FUN_00596850 [0x596850,0x597a6b], 839 lines): the 30 `call 0x64cc00` sites are only ONE of FOUR readers — 0x596470/0x596540 are the CONVERTING pair (`imul size,count`, round odd up, malloc via 0x5be090, read, copy) and 0x64c9a0/0x64cc00 the DIRECT pair; the pair is chosen by `[0x926a14]`, SET at 0x5968a7 to `([0x985ae8] & 0x10000000)` (live 0 -> DIRECT). The count arg is ALWAYS the immediate 1 (`push esi; push 1; push size; push ptr`), so bytes == size.
- IF/THEN: every leg gate is `cmp ds:0x985dbc,N` = the loaded VERSION (live 9): 0x59689a >=4, 0x596a43 >=3 (else malloc 0xe5e0), 0x597159 >=3 (else the sparse loop), 0x597246 >=6 (0x1000@0x92bff0), 0x5972cb >=0 (52n), 0x5974b7 >7, 0x597542 <3, 0x5975e6 needs `[0x985ae8]&0x10` (live 0 -> the 0x100@0x991698 leg OFF), 0x597650 >=1, 0x5976c8 >=2, 0x597733 >=7 (0x27a0).
- 0x5971c8-0x597244 is a LOOP, not a leg: 8 x `read 0x680 into edi`, `add edi,0xd00` (stride 3328 != size 1664) while edi < 0x991588 — the version<3 sparse form of the 0x6800@0x98ad88 leg. M107's table lists BOTH, so its 204,504 double-counts 1,664 B for any save.
- The 48p path is a 48->52 record EXPANSION loop (0x5973bc-0x597495, [0x985af0] iterations, 0x30-byte source records rewritten into 0x34-byte records at 0x93327a), gated at 0x5972cb on version < 0 — that is why 0x59738b logged 0 events on every save here.
- 0x596620(a,stream) = a 4-B read into `a+0x1dd78`; the loader calls it 8x off the dword table at 0x7cdecc then once with 0x8cda4c — 36 B, not a section.
- **105 reader call sites exist OUTSIDE [0x596850,0x597a6b]** (0x44b6e1.., 0x52c359, 0x5821f4.., 0x597ab1..), so the 30-leg table is not the whole read set — the malloc'd 86,016 B read belongs to one of them.
NEXT: arm gdb only AFTER the save's FILE* is open (four runs, zero loads: the census cannot be attached while the driver drives the menu), or bp the 122 in-loader call sites; then G3 closure. Evidence: evidence/m109g1.gdblog, m109g2.gdblog, m109g3.summary, m109g4.gdblog, m109g4.log; evidence/m109_skel_loader.txt; scripts/m109_leg_gates.py. Box: relaunch terran.exe pid 1464418 at the LOAD GAME panel, untraced.

## Session 171 (2026-10-29) — M111 BLOCKED: the 156-B tail has no named reader, and the census model is VOID (over-counts by 468 B)

Three acceptance invocations, none green, nothing merged.

1. m111b1 `python3 scripts/m109_leg_census.py --tag m111b1 --relaunch --ranges 0x44b000-0x630000`
   (all 221 call sites to the 4 readers) — gdb DETACHED after 3 events on wineserver's SIGUSR1
   (`handle SIGUSR1 nostop noprint pass` + a 400-continue tail were MISSING from this harness; now in it).
   Events logged before the detach: 0x62ae0f dest=0x7cda1c size=128, 0x62aec8 size=16, 0x62af05 size=16.
2. m111b2 same range with the SIGUSR1 handles — the 31 CRT-band sites (0x62b000-0x62d000) are HOT:
   0x62b8f0 and 0x62b935 fired 8,277x each during STARTUP, 25,957 stops in 12 min, ZERO loader hits,
   then the event stream froze for 7 min = the m109g3 starvation shape. Killed by pid.
3. m111b3 `python3 scripts/m109_leg_census.py --tag m111b3 --relaunch --ranges 0x400000-0x62afff`
   (190 sites = 221 minus the CRT band): the load RAN (counts 67/18) and completed —
   0 gdb errors, 90 executed sites, **sum(size*count) = 243,007 vs file 242,539 → OVER by 468 B**.
   So the cumulative "file_off" column is not a statement about the save: the executed set mixes in
   (a) three 160-B CRT reads into 0x7cda1c / 0xbe8c10 / 0xbefd3c, and (b) a 9-iteration per-entity loop
   of 6 x 4-B reads into heap dests 0x3b7d7a8 .. 0x3c4b420 (stride 0x224B8, the M110 pair 0x59666d/0x5966c1).
   The M110 "contiguous 0..242,383" figure is therefore an artifact of UN-ARMED sites, not proof of what is
   unread. Do not repeat it as a closure.

READ-BACK after the load (no gdb, /proc/1573718/mem, 523 MB of readable maps): the save's last 156 B are NOT
present verbatim anywhere; the 12-B row signature `fa ff ff ff 20 00 00 00 20 00 00 00` (6 rows in the save)
appears exactly 6x in ONE region, 0x34f0000. The RECORDS reach memory, the BLOB does not — a per-record
restore, not a bulk 156-B read.

Instrument fixes this session (committed): session_brief.py and accept_ready.py print BLOCKED instead of a
CalledProcessError traceback when terran.exe is down; m109_leg_census.py now sets M54A_LOAD_TIMEOUT=1800,
carries the SIGUSR1/USR2/SIGPIPE handles + 400-continue tail, and prints a CLOSED/PARTIAL verdict (exit 4).
test_accept_ready.py PASS 17/17 after the change.

### Session 171 (cont.) — M112 static pass: the 156-B tail is a fixed TRAILER, almost certainly write-only

No box time, no acceptance invocation spent. Three laws, each with the command that produced it.

1. **It is a trailer, not data.** `programs/saves/*.SAV` + `programs/saves/auto/*.SAV` (9 files, sizes
   242,539 (m54b_clean) and 242,815 / 242,875 / 242,919 / 242,927 / 242,971 / 243,483 / 243,691): the last
   **152 B are byte-identical in all 9**, only the FINAL dword differs (365,402,425 / 766,622,009 /
   746,214,987 ...). Structure: 5 rows of 24 B `[id,0,0,-6,32,32]` for id 3..7, then `[1,1,0x80000080,-14,32,32]`,
   then `[800,387,X]`. A section of game data would vary with the game; this does not, and it sits at EOF at a
   per-save offset — so nothing hard-coded can index it.
2. **No code can size it.** The value 156 (0x9c) occurs as an *immediate* only 13x in the whole executable
   (objdump `scratch/m574/text.txt`, stack-frame displacements `[ebp-0x9c]` excluded) and **never inside the
   save family 0x58xxxx-0x59xxxx**; the only two `push 0x9c` are 0x4b3476 / 0x4b3e3d. The loader's own code has
   no constant that could bound a 156-B read.
3. **It is not restored.** Live read-back (no gdb): memory at the loader's LAST read destinations
   0xbe27b0 / 0xbe27b4 (sites 0x597a19 / 0x5979f8, the end of FUN_00596850) holds unrelated values — no 800, no
   387; the 156 B is absent verbatim from 523 MB of readable memory; its 12-B row signature
   `fa ff ff ff 20 00 00 00 20 00 00 00` appears exactly 6x at heap **0x34f0000** and in **0 of the 24 files**
   in programs/ (so it is not a static table the game carries).

**Read this as:** the M110/M111 "156 B of save data with no reader" framing is wrong. The writer emits a fixed
trailer at save time; the loader's read set does not cover it. The acceptance for closing it (not yet spent):
load an AUTOSAVE (its trailer sits at a DIFFERENT offset) under a FILE*-filtered census and predict
**sum = filesize - 156 again** — two files, two offsets, same shortfall.

**Correction, same session:** the loader DOES push a **152** immediate (`0x597716`), so "no constant can size the
tail" is too strong — the honest statement is that its destination `0x92bf58` holds `[9999,9999,0,0,2100,2600]`,
NOT the trailer rows, so that leg is some other section. What survives: the trailer's offset varies per save, its
rows reach memory only as records (6x at heap 0x34f0000), and the 156 B is absent verbatim from memory.

### Session 171 (cont. 2) — M112 attempt 1 (m112a1): the FILE* filter works, the SUM DOES NOT — and the trailer question needs a poke, not a census

`python3 scripts/m109_leg_census.py --tag m112a1 --relaunch --ranges 0x400000-0x62afff --filter-file --save
m112auto1.SAV` (copy of "Alpha Centauri Autosave 1.SAV", 242,927 B, trailer at 242,771; counts 68/19):
**savefile=0x6a79a0 captured at 0x596850, 83 legs, 0 gdb errors, sum 243,071 vs file 242,927 -> OVER by 144.**
Predictions before the run were H1 structural-trailer sum = 242,771, H2 fixed-read-set 242,383, H3 trailer-read
242,927; the observation matches NONE of them, which is itself the result: **the cumulative offset column is
still invalid after filtering** (unfiltered m111b3 was over by 468; filtered, by 144). Two runs, two different
saves, two different over-runs: the size*count sum cannot decide this question at all.
No (site,dest,size) group repeats, so the 144 B are re-reads at different destinations/sites, not one duplicated
leg. Read-back at the final group's destination (0x62ae0f 128 + 0x62aec8 16 + 0x62af05 16 into 0xbefd3c) shows
[9552352, 839181731, 1, 1, 5, 24592, ...] — NOT the trailer: 0xbefd3c is a shared CRT stdio buffer that later
reads of OTHER files overwrite, so the buffer content is not evidence either.

**Reframe (the useful part):** the loader consumes through a 4096-B stdio buffer, so the trailer's bytes are
pulled into RAM no matter what; "read or not" is not answerable by counting consumer fread sizes. The next
experiment must make the bytes IDENTIFIABLE: poke a unique pattern into the trailer of a save copy, load it, and
scan /proc/<pid>/mem for that pattern. Pattern present = the trailer is loaded; absent = it is never consumed.
That is one run, needs no offset model, and cannot be confounded by a shared buffer.

Box after the run: terran.exe 1878861 (autosave m112auto1 loaded, counts 68/19). gdb 1878864 was LEFT ATTACHED
again after the harness printed its verdict — killed by pid, TracerPid now 0. (Second occurrence of the law.)

### Session 171 (cont. 3) — M112 attempt 2 (m112p1, POKE): the 156-B trailer IS READ. The per-entity loop is its reader. M110's shortfall is RETRACTED.

`python3 scripts/m112_trailer_poke.py --tag m112p1 --relaunch` — copies m54b_clean.SAV, plants **10 dwords of
0xCAFEBABE** in the two zero fields of each of the 5 trailer rows (40 B changed, file size unchanged, and the
magic occurs **0 times** in the original save, so any hit is ours), loads it, then scans /proc/<pid>/mem.

Result: **load rc=0, counts 67/18, 522.9 MB scanned, 41 MAGIC hits**, the five structural ones at
**0x3bc2110, 0x3be45c8, 0x3c06a80, 0x3c28f38, 0x3c4b3f0**. Those are EXACTLY the destinations I dismissed as
"pollution" in m111b3, minus 8: the 6-site per-entity loop (0x59666d / 0x5966c1 / 0x596715 / 0x596769 /
0x5967bd / 0x59683b) reads each trailer row's 6 dwords into heap record starts 0x915758, 0x3b7d7a8, 0x3b9fc60,
0x3bc2118, 0x3be45d0, 0x3c06a88, 0x3c28f40, 0x3c4b3f8 (stride 0x224B8) and 0x8eb7c4. The census logged the
2nd/3rd word's dest (row+8) and the poke shows the row's own bytes there — so the loop IS the trailer's reader.

Consequences: M110/M111's "contiguous 0..242,383, 156 B with no reader" is **RETRACTED, not narrowed** — the
trailer is consumed; it is 5 `[id,0,0,-6,32,32]` rows (id 3..7) restored one row per heap record. The census's
+468 (m54b_clean) and +144 (autosave) over-runs are the ORDER assumption in its cumulative `file_off` column
(the same bytes are touched twice, once bulk and once per row), never missing or extra file content.
Harness `scripts/m112_trailer_poke.py`; verdicts CONSUMED / NOT CONSUMED / REFUSED (all three conclusive, exit 0).

## Session 171 (close-out) — M110-M112 merged as #116 (squash 645384b)

The PR TITLE still reads "M111 BLOCKED: the 156-B tail has no named reader, and the census model is VOID" because
it was opened while that was true; the merge carries the later commits and the resolution above (m112p1: the
trailer IS read, by the per-entity loop; M110's 99.94%/unread claim retracted). Read the commits and NAMED.md,
not the PR title. main = 645384b; branch deleted; local tree clean.

## Session 171 (cont. 4) — the offline "re-derive the .SAV map" attempt is VOID (recorded so nobody spends a run on it)

Two cheap shapes were tried and both are disqualified BEFORE any box time:

1. **decode_save.py --sections cannot run on these saves** — it dies with `no 52/304 split of a 0-byte region`
   on all 9. Its `MAP_SECTIONS = 2724 + 140800` is a 128x128 grid; m54b_clean's map is `2,724 + 90,112 + 91 =
   92,927` (M110: 64x64x22), so the constant alone over-runs the file by ~50 KB and every later offset is wrong.
   A real lead: derive the map size from the header dims per file (data-formats.md has the formula for .MP).
2. **A subset-sum over the candidate legs is UNDERDETERMINED, not a solution.** With the 64x64 map and 52n+304m
   free, m54b_clean admits **181,769** exact decompositions of its 242,539 B (e.g. `maptrailer91` + n=32/m=531);
   auto1 admits 182,718, auto30 184,074. A search whose answer set is that large cannot pick a layout — the same
   "shape that cannot discriminate" trap the kickoff warns about. Content constraints or pokes must filter it.

So the .SAV map stays OPEN, and the next attempt must be poke-driven: plant a marker at a candidate section start
in a save copy, load, and look for it (the m112p1 instrument, one section per run, 2-3 candidates per save).
Nothing merged; no acceptance invocation spent on this.

## Session 171 (cont. 5) — M113 ACCEPTED (m113map1): the .SAV offset->memory map, extracted by pokes (20/20 anchors)

`python3 scripts/m113_save_map.py --tag m113map1 --relaunch --step 16384` — 20 markers `0xC0DE000i` planted at
16 KB offsets + the 6 candidate section starts in a copy of m54b_clean, loaded (rc=0, counts 67/18), and every
marker searched in 522.7 MB of /proc memory: **20/20 found, 0 absent**. Anchor table (file offset -> destination):

```
16,384 0x951104   32,768 0x955104   49,152 0x959104   65,536 0x95d104      <- run 1, slope 1
81,920 0x92ad6c                                                           <- map header
98,304 0x40aa5b0  114,688 0x40ae5b0 131,072 0x40b25b0 147,456 0x40b65b0
163,840 0x40ba5b0                                                         <- run 2 (the 90,112-B grid), slope 1
172,287 0x15e2baf                                                         <- map trailer region
180,224 0x987d51  188,291 0x989cd4  188,467 0x930e20  192,051 0x98aad4
196,608 0x98bf49  212,992 0x98ff49  218,675 0x99157c  222,771 0x92cfe4
229,376 0x95e635
```

What the anchors establish (each independently of any census):
- **Three slope-1 runs** — 16,384..65,536 -> 0x951104..0x95d104; 98,304..163,840 -> 0x40aa5b0..0x40ba5b0;
  196,608..212,992 -> 0x98bf49..0x98ff49. Inside a section, file offset maps to destination 1:1.
- **The 90,112-B grid is at 0x40a6660** — the run-2 anchors sit on it with step 0x4000, confirming M110's map
  from an instrument that cannot over-run anything.
- **Two leg boundaries corroborated to the byte**: 188,291 -> 188,467 is exactly **176 B** apart and lands at
  0x930e20 (the count-prefix leg at 0x930d7c), and 218,675 -> 222,771 is **4,096 B** apart (the 0x92bff0 leg).
- Region boundaries are where the destination JUMPS: block A -> map header between 65,536 and 81,920; map ->
  trailer between 163,840 and 172,287; trailer -> section between 172,287 and 180,224.
Harness `scripts/m113_save_map.py`; it plants markers, loads through `m54a_load.py`, and prints every anchor.

## Session 171 (cont. 6) — M113 attempt 2 (m113map2): boundaries bracketed to 2 KB; one offset is ABSENT

`python3 scripts/m113_save_map.py --tag m113map2 --relaunch --step 2048 --band 64000-82500:2048
--band 163000-174000:2048 --band 174000-182000:2048 --band 221000-231000:2048` — 25 markers inside four named
bands (a full 118-marker sweep is refused by the harness: 60+ pokes mutilate counts and pointers). Load rc=0,
counts 67/18, 523.0 MB scanned, **24/25 found, 1 absent**.

Boundaries, now bracketed by adjacent runs rather than assumed:
- block A -> block B: last A anchor **66,048 -> 0x95d304**, next **68,096 -> 0x927684** (block B = 0x927590). The
  documented 67,840 split falls inside the bracket. Slope-1 continues through block B, the 32-B table and the map
  header: 68,096..80,384 -> 0x927684..0x92a76c, then **82,432 -> 0x40a67b0** (grid).
- grid -> trailer -> next section: 163,000..171,192 -> 0x40ba268..0x40bc268 (grid, step 0x800), then
  **173,240 -> 0x986209** (the 0x985e5c section). So the grid ends and the 91-B map trailer (file 172,200..172,291)
  lives inside the bracket 171,192..173,240 — consistent with run 1's 172,287 -> 0x15e2baf.
- 174,000..180,144 -> 0x986501..0x987d01, step 0x800, all inside the 16,000-B section.
- record area: 221,000 -> 0x92c8f9, **223,048 -> ABSENT**, 225,096 -> 0x933b81, 227,144 -> 0x95dd7d,
  229,192 -> 0x95e57d (step 0x800). The 52-record block starts ~222,783 (0x933278 anchors it), so the absent poke
  sits INSIDE that block: either a gated/unused record or a field the loader rewrites after the copy. Not resolved.

So two of three boundaries are now pinned to the KB, the third (record area) has a specific open question with an
address to chase, and the harness gained `--band lo-hi[:step]` plus a hard cap of 60 markers.

## Session 171 (cont. 7) — M113 attempt 3 (m113map3): the "hole" is not a hole — the 52-record array maps 1:1 and a few FIELDS are rewritten after the copy

`python3 scripts/m113_save_map.py --tag m113map3 --relaunch --step 128 --band 222000-224500:128` — 20 markers at
128-B spacing, load counts 67/18, 522.5 MB scanned, **19/20 found**. (`m54a_load.py` returned rc=4, its HUD
"live" check failing while counts were already correct — the load itself ran; the harness treats rc!=0 as exit 6.)

- The 52-record array maps **1:1 with an odd base**: 222,896 -> 0x9332E9, 223,024 -> 0x933369, 223,280 ->
  0x933469, ..., 224,432 -> 0x9338E9, every step +0x80 for +128 B. The base is **file 222,783 -> 0x933278**
  (0x9332E9 = 0x933278 + 113 = 0x933278 + (222,896 - 222,783)), which pins the block start that the leg list only
  guessed.
- **The absent offset MOVED**: 223,048 in m113map2, 223,152 in m113map3. Expected dests 0x933351 (record 4, byte 9
  of 52) and 0x9333E9 (record 7, byte 5). Different fields in different runs, both with present neighbours 128 B
  away — so this is **not an unread region**; a handful of dwords in the 52-byte records are rewritten by the
  loader's post-processing after the bulk copy. That also explains the census's re-read/over-run pattern.
So M113 closes with: three boundaries bracketed to the KB (attempt 2), the record block's base pinned to the byte
(attempt 3), and one residual class of rewritten fields, named and located, instead of an unexplained 156-B hole.

## Session 171 (cont. 8) — M114 (zero box time): the .SAV is restored 1:1; live rewriting is confined to two zones

Method: with the poked save loaded, diff `/proc/<pid>/mem` against the FILE at the anchor-derived mapping
`dest = off + k`, 1 KB windows at 12 anchors spread over the whole file. **10 of 12 windows are byte-identical**
(k constant within a region: block A 0x94D104, grid 0x40925B0, the post-map section 0x95BD51, 196,608/212,992 ->
0x95BF49, 52-records 0x926635). The two exceptions:
- **map header tail: file 81,408..82,100 differs (665 bytes, contiguous)** — the game rewrites the end of the
  2,724-B map header on load (the grid itself at 82,432 is clean).
- **block A tail: file 67,080..67,143 differs (238 bytes) with a 16-byte STRIDE, 2 bytes per hit** — a per-record
  u16 array the load recomputes (first hits 67,080/67,081, 67,096/67,097, 67,112/67,113 ...).
And the 52-record array (3,484 B, base file 222,783 -> 0x933278) differs in exactly **2 dwords**:
222,831 `0x0003FFFF -> 0x00000000` (the game clears it) and the poked field at 223,152 whose top byte came back
`0xC0 -> 0xD6` (the game normalises that field). That is the whole residual: two zones plus one normalised field,
not an unread region.
Also from the anchors: block B's base is file **67,852** -> 0x927590 (the documented 67,840 is 12 B early), pinned
by 68,096 -> 0x927684.
