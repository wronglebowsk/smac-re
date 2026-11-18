

Older sessions: `docs/sessions/sessions-258-259.md` (2 sessions). Read it only when a question reaches back before session ## Session 260.

## Session 260 (2026-11-15, ANALYSE, zero box) - M304: the seven FUN_0055f650 predicate sites are chosen by the [ebp-0x44] CASE LADDER + per-arm loops; 0x56c6de is the hub's COMMON EXIT (7 jmps); M300's predicate frame slots are FOREIGN frames

- `python3 scripts/track_mode.py` -> MODE=ANALYSE (analyse_since_build=2, next_rung=B20); M303 merged as #271.
- `python3 scripts/m304_chooser.py` -> **PASS M304: 12/12** (A1-A12; two runs byte-identical; zero box/proc/gdb) -> `evidence/m304_chooser.txt`. CFG of the entry-window [0x55f650,0x56cb23) (index.csv size 0xd4d3; Ghidra n_insns 16822 vs 16845 parsed): 3017 blocks, 5249 edges, 104 dominance-verified loops, 139 backward branches; the 7 sites recomputed == M300's table.
- Guards (closest pred jcc <- flag-setter <- decider <- producer, S2): 0x56429c `jne 0x5642b1`<-`cmp eax,3`<-`mov eax,[ebp-0x44]` (the CASE selector == 3); 0x56444b `jne 0x5644a8`<-`test dl,al`<-`mov dl,[ebp-0x64]` (+ arrival jne 0x56442c); 0x5645d9 ENTERED via `je 0x5645d0`<-`test eax,eax`<-`mov eax,[ebp-0xc]`; 0x5651e3 `je 0x56526c`<-`test eax,eax`<-`mov eax,[ebp-0x18]`; 0x568567 its ONLY pred is a **VACUOUS jne 0x56855f (target==next insn - jump-to-next artifact)** - unguarded on arrival, the chooser is the 18-leg upstream chain; 0x56b77c OR-arrivals: 3 jccs (`je`[ebp-0x74]==0, `jne`[ebp-0x40]!=0, `je`[ebp-0x6c]==0) + fall-through; 0x56c5f4 OR-arrivals: 4 jccs (`jne`[ebp-0xc]!=0, `jne`[ebp-0x40]!=1, `jl` class&~0x1f vs 0x60, `jne` BYTE[..+0x94e5a8] score-byte set) + fall-through.
- Loop-vs-paths: max sites in ONE loop span = 2 -> rival "ONE loop walks all 7" FAILS; all 7/7 inside loop spans -> rival "7 straight paths, ZERO loops" FAILS. Truth: a case ladder (31 `cmp [ebp-0x44],imm` in-window; slot writers 3, prologue producer 0x55f74a = type-record plan byte M127/B15) AND per-arm loops: X/Y grid walks ([ebp-0x4] +2, [ebp-0x8] +1, tails 0x5649c1/0x5649d3), 21-entry table walk (ebx +4 vs 0x54, tail 0x5645f2), [ebp-0x2c] walk (tail 0x56527b), [ebp-0x30] vs 9 (tail 0x5688a3), and the settle nest [ebp-0x70] vs 9 (0x56b061..0x56c6a0, tails 0x56c6a0; sites 6+7) x direction [ebp-0x4c] vs 8 (0x56c46c..0x56c670) x [ebp-0x54] vs 0x20 32-entry (0x56c4f9..0x56c660, site 7). B18's BRANCH-POLARITY law (evidence/b18_sitegate.txt G1) is the instrument law instantiated: leg semantics decode from branch landing, never address adjacency.
- The 0x56c6de leg: a block HEAD with **8 preds = 7 unconditional `jmp 0x56c6de`** (0x55fc5b, 0x561d8d, 0x563e0d, 0x566419, 0x56678b, 0x56832b, 0x569952 - each skipping 3669..16060 insns of the arms below it) + fall-through 0x56c6d7 (after BYTE[unit+0x2b]=0x78). The leg reads esi=[ebp-0x10], edi=[ebp-0x84] (best-direction; ZERO writers dominate it), `jge 0x56c966` = act, else clear unit flag bit 0x10000 (0x93327c and 0xfffeffff) + order byte 0x933289=0 -> `jmp 0x56cafa`; back edges 0x56c75b/0x56c76c/0x56c7a6 re-enter via 0x56c6d4 - it is the hub arms' COMMON EXIT + unit cleanup, not a per-predicate continue.
- CORRECTION to the M300 lead framing: NO hub site stores predicate eax to a frame slot (0/7 STORED-class; 6 truth-branch + 1 into-ebx sign->0x200 mask). In the hub frame [ebp-0x1c] is hot shared scratch (126 accesses / 79 writers / 43 nest-local, 0 dominating the leg) and [ebp-0x7c] is NEVER written inside the settle nest (25 accesses / 8 writers / 0 nest-local / 0 dominating) - at the leg it holds a STALE other-arm value. The M300 predicate-STORE slots are FOREIGN frames: FUN_004cf4c0 stores its [ebp-0x1c] at 0x4cf920 (21 B past the call) and FUN_00585720 stores its [ebp-0x7c] at 0x5858ff - each with EXACTLY ONE true reader (0x4cfef2, 0x589fe5, both `mov r32,[slot]`) - the M300 "readers of the stored predicate slots" lead is CLOSED.
- Instrument laws (NEW, skill code-atlas): (1) the scratch/m574/text.txt cache TRUNCATES long encoding-byte columns at 20 chars - never compute insn lengths from the byte column; (2) a CFG split must END blocks at every jcc/jmp/ret, not only before branch targets - the first M304 census printed 0 back edges because of target-only splitting; (3) some jcc are jump-to-next VACUOUS artifacts (target == next insn => no skip-leg; e.g. 0x568559) - mark them before calling them guards.

## Session 261 (2026-11-15, BUILD B20 10/10, zero box) - the BYTE-twin visit counter made EXECUTABLE (sim/bytecounter.py); the rung was UNAUTHORED, this fire wrote it (as B14/B16/B17/B18/B19)
- `python3 -m sim.selftest --b20 programs/saves/m54b_clean.SAV` -> **PASS B20: 10/10** (G1-G10; two selftest runs byte-identical, module report sha 156aaa4cac5a916b, module CLI twice sha eea4a6406ffa272c; zero box/proc/gdb) -> `evidence/b20_bytecounter.txt` (verdict :39, parity :35, pinned census :32, B18 funnel match :34).
- The M303 byte law is now EXECUTED: index = site + 8380*block + 0x94ed28, {MAX@+0,CNT@+128}, width 1 B, 128 entries/field, 8 blocks - every constant DECODED from the instruction windows embedded in evidence/m303_downstream.txt (fold 65->131->2095, *4 placement == init add edx,0x20bc, stride derived twice; init cmp ecx,0x80; (0x95f288-0x94eca8)/8380 = 8 rem 0; dword twin 0x989ce8 stride 0x1c slots 128). The byte `++` rides the SAME gated fall-through as B19's dword `++`: ZERO jumps inside [0x51e007,0x51e03e), je 0x51e007 rel32 decodes from its pinned hex to 0x51e11d (past the store), and je 0x51e040 tests the flags of `test ebx,ebx` 0x51e03c, not the byte.
- PARITY (the rung's point): under the M302 pinned state (parsed from evidence, flag2000=False rand=9661 s20c=61 s210=11) the 2321 recorded rows give 38 accepts -> 38 dword increments over sites [1] AND 38 byte increments over (block,site) keys {(0,1):1,(3,1):17,(6,1):20}; per-site sum_blocks(byte CNT) == dword CNT on BOTH record views; the accepted-row set is identical row-for-row (fires_equal 2321/2321).
- MEASURED facts this window: exactly ONE accepted visit is on block 0 (byte CNT lands, byte MAX never can - B18's cell skip stays 277 == the sentinel rows); byte values stay under 256 (no wrap: max byte MAX 7, max byte CNT 20); live-view (s249) replay accepts 7 vs save-view 38 -> byte-CNT tables diverge on 3 entries (COUNTED, declared - same record drift as B18/B19); byte MAX cells {(2,1):4,(3,1):7,(4,1):3,(5,1):2,(6,1):6} == B18's SiteGate funnel byte-for-byte AND vs B18's own recorded numbers parsed from b18_sitegate.txt (5 cells/5 blocks/277 skips).
- 6 rivals all refuted on recorded numbers: ungated ++ (2321 vs 38), ++ on eax==2 only (1 - the eax=1 leg IS a graded row here), 28-law byte index (2/2 keys), CNT riding the MAX block-gate (1 - the accepted block-0 row exists), MAX ungated (7 vs 5 cells), pure-read (38 vs 0). Anchor-coherence gate G9: the parsed m302/b18 recorded tables sum-check AND the parsed live-state string == the model's own.
- PITFALLS (new): (1) evidence-file instruction windows are NOT all objdump-verbatim: m303 uses 0x-prefixed addresses, NO colon after the address, and the S4 init window has NO hex-byte column - a parser copied from m299's shape silently matches ZERO instructions; assert the pinned-address COUNT, not just "parsed something". (2) a recorded per-site split column may cover a SUBPOPULATION: m302's {1:(38,993,0)} is the 1099 branchA rows ONLY - comparing it against per-site counts over all 2321 rows (2215 refuses) gives a bogus FAIL; read what population a recorded column covers before grading against it.
- DECLARED UNMODELED (in the module docstring + spine block): live byte-table CONTENTS; live block upper bound (<8 implied, graded rows carry only -1 or 1..8); the per-call zero-rebuild CADENCE of FUN_0051dcb0 (window-level accumulation model, as B18/B19); the post-store dispatch/settle nest (M303 S7, M304's OPEN meaning); save-carry vs rebuild of the byte family; sibling fields of the 8380-B record. No retractions; M303's laws all re-used unchanged.

## Session 262 (2026-11-15, HYGIENE H262, zero box) - NEXT_PROMPT.md docs-only split: the settled count/byte-counter era relocated

- WHY: NEXT_PROMPT.md sat at 11,999 B (1 B under the 12,000 warn; CLOSING ORDER step 3 - "past it the next fire starts as a docs split"). Doctrine: a cap that binds a SECOND session gets a docs-only split as its own PR.
- MOVED VERBATIM (3 blocks, byte-identity verified - each block asserted `in` the archive and `not in` the new footing, per-block wc -c printed):
  1. the s261-close header line (1,048 B) -> NEW `docs/nextprompt-archive-m299-b20.md` §s261-header;
  2. the full CLOSED enumeration of the count/byte-counter era (816 B, M220..M301/B19/B20/M302-M304) -> same file §closed-era;
  3. TRAPS 14-15 (646 B) -> `docs/pick-archive.md` §trim-s262 (the s245/s256 pattern for settled trap text).
- LEFT IN PLACE: the RULE + POINTER for each moved block (CLOSED re-open gate w/ per-id NAMED cites + era-archive pointer; traps 14-15 one-liners); §THE PICK (OPEN shortlist untouched), §BUDGET, §BUILD TRACK, §THE LEDGER, §INSTRUMENTS, §LIVE FACTS, §CLOSING ORDER, all standing rules. Nothing binding dropped.
- BEFORE/AFTER: NEXT_PROMPT.md 11,999 -> 10,833 B (`wc -c NEXT_PROMPT.md`); SESSION_NOTES 57,878 B (under its 110 k warn - NOT split this fire); docs/nextprompt-archive-m299-b20.md created 2,874 B; pick-archive 74,846 -> 75,561 B.
- STATE (NOT findings): #273 (B20) MERGED into main 119b691 (mergedAt 2026-11-15T22:26:50Z, `gh pr view 273 --json state`) - the footing's "PR open / LAND THIS PR FIRST" markers were stale and now read LANDED; the archived header keeps the s261 bytes untouched with a dated correction note above them.
- NO finding retracted, re-worded or re-derived; NO script or instrument touched. skill/ untouched (diff -rq clean, gate's SKILL.md check holds by non-touch).
- HONEST NOTE: 10,833 is under the 12,000 CLOSE cap but above the 9,500 ASPIRE target; the remaining settled material (TRAPS 1-3 + BUILD TRACK full text) already lives verbatim in pick-archive with pointers, so a further squeeze would mean dropping live rule text - not allowed this fire. Next fire may fold §LIVE FACTS' box-debt history (s245..s260 tally) the same way.

## Session 263 (2026-11-15, ANALYSE, zero box) - M305: FUN_0051dcb0 IDENTIFIED as the zero-rebuild owner; 11 single-site callers (1 loop-enclosed), a round-mod-4 gate

- RESUMED a mid-flight branch, not a new pick: `milestone/m305` held a skeleton commit (e8c8e5f) + an UNCOMMITTED 330-line script whose S2 walk hung forever (`while x < W:` never advanced x) - every run died on its own timeout with 0 B of buffered output, which reads exactly like a crash and is not one. Fixed at `scripts/m305_identity.py:285`, plus a `JCC_RX.match` group-1/group-2 bug at the loop-membership scan. Lesson: a 0-byte evidence file + exit -15 = an infinite loop, not a missing instrument.
- ACCEPTANCE `python3 scripts/m305_identity.py` -> **19/19 checks OK, exit 0**; `evidence/m305_identity.txt` 12,242 B, `diff <(rerun) evidence` = 0 lines (checked twice, before and after the review fixes).
- GREPTILE TRIAGE (PR #275, all 6 findings fixed, none dismissed): P1 "loop check always passes" was CORRECT - the scan carried both `ai <= a` and `a <= ai`, satisfiable only at the call itself, so A14 ruled out repeated rebuilds over an unmeasured state. Fixed by scanning the whole function for a back-jump spanning the call; it then FOUND one (0x59dd3a), so the "no caller loops the pass" claim is retracted. P2s: (i) "unconditional" was inferred from one preceding instruction -> now counted three ways (branch-skipped 2, decompiled-conditional 5, top-level 4); (ii) A11 could not see a stored pointer -> now scans terran.exe bytes for the LE dword 0x0051dcb0 (0 occurrences; a rel32 call never stores it); (iii) rec_stride was decoded but unused -> A18 asserts the cursor step IS the 44-B stride over 2048 gapless byte offsets; (iv) bl_writes counted only `mov ebx,0x1` -> now every ebx/bx/bl write plus an exit-path test (the rival `pop ebx` at 0x51f5a2 is followed by `inc; ret`), and the jcc direction is checked; (v) NAMED citations were off by ~60 lines -> repointed.
- (a) IDENTITY CONFIRMED: the zero-build window zeroes the BYTE family base 0x94eca8 stride 8380 (=0x20bc, B20's own constant) 8 blocks x 128 entries (term 0x95f288) AND the DWORD family 0x989ce8 128 slots x 28 B {MAX@+0,CNT@+4} (term 0x98aae8); residual 0 on both. The rebuild walk re-visits all 2048 tile records exactly once (32/row uniform on W=H=64,mult=32, parity start x=(y&1), x+=2, shared cursor, stride 0x2c) with **0 fold mismatches** against the NAMED.md:1025 record fold `base+0x2c*(32*y + (x>>1))`.
- (b) CALLERS: 11 direct call sites == index.csv n_callers=11, in **11 DISTINCT functions, each calling exactly once** (0x41dc7e/0x4e145e/0x4e4dc8/0x4e5540/0x4f3e08/0x508b48/0x51f71e/0x543bc6/0x59b8ce/0x59dd3a/0x5b09f6); zero stored-dword occurrences of the VA in terran.exe -> no vtable/callback entry exists. RIVAL "one hub caller invokes it repeatedly" FAILS (max multiplicity 1). Loop enclosure: **exactly 1 of 11** (0x59dd3a in FUN_0059ce10, back-jump 0x59e2a6 -> 0x59ce92) - this caller re-runs the pass once per iteration.
- (c) CADENCE: one call per caller invocation in 10 of 11; 5/11 sites sit under a DECOMPILED conditional, 2 are skipped by the immediately-preceding branch, 4 are top-level. 0x51f71e gated on `(round & 3) == bl` - the only ebx write that can REACH the gate is `mov ebx,0x1` at 0x51f32b (the competing `pop ebx` at 0x51f5a2 is an exit path: `inc; ret` follows), so the call fires when round%4==1; 0x5b09f6 gated on `ds:0x99180c == 0`. 3 sites (0x4f3e08/0x508b48/0x543bc6) share the verbatim triad `call 0x5a2ae0 / add esp,8 / call 0x51dcb0`. The row-table builder runs first: the loop at 0x59b8ce writes `ds:0x985af4` (row count) each iteration then falls into the call.
- EXPORT HOLE (new, repo-level): call site 0x4f3e08 is OUTSIDE its index.csv owner FUN_004f34b0 (0x4f34b0+298 ends 0x4f35da). A prologue at 0x4f35e0 - the only one in the gap - starts a function the Ghidra export NEVER modelled; its span is [0x4f35e0,0x4f4060), ~2688 B, no body, no guard chain. index.csv is not a total function map.
- UNKNOWN (stated, not closed): U1 the 0x4f35e0 owner's guards/preds (no decompiled body); U2 what the 8 blocks / 128 slots per-block MEAN (M302/M303 scope); U3 live per-turn cadence unmeasured (zero box) - only the static bound.
- ZERO box time, zero /proc, zero gdb, no box debt incurred.

## Session 264 (2026-11-15, ANALYSE, zero box) - M306: the export hole at 0x4f35e0 is a REAL complete function — bounds, identity, one fold-edge entry, and WHY the export never modelled it

- (a) BOUNDS from CODE, not from the next index entry: entry 0x4f35e0 `push ebp; mov ebp,esp; sub esp,0x34` after 6 aligner nops at 0x4f35da (end of FUN_004f34b0); CFG from the entry = 846 reachable insns, contiguous (no >16B hole), 3 rets each ending a pop ebx/esi/edi + mov esp,ebp epilogue, last ret 0x4f4050, then 15 nops to 0x4f405f. Function = [0x4f35e0, 0x4f4051), 2673 B (evidence/m306_owner.txt:9-13, A1-A7).
- (b) IDENTITY: 23 distinct callees / 36 call sites (FUN_00507410 x6, FUN_0064b870 x4, _rand x3, ...); 16 distinct ds: globals incl. the object ptr ds:0x8f0d60 x17, map bounds ds:0x92a378, row-table count ds:0x985af4 x4. The FUN_0051dcb0 call at 0x4f3e08 has ZERO branch preds — a fall-through from the 21-iteration loop's exit (`add eax,4; cmp eax,0x54; jl 0x4f3c0a`), NOT a branch target; and it is NOT unconditional at function level: all 3 of 3 rets are reachable without executing it, so early exits skip the rebuild (A23) and the M305 triad `call 0x5a2ae0/add esp,8` (`evidence/m306_owner.txt:31-52, A8-A9`).
- (c) CALLERS: dump-wide `call 0x4f35e0` = 0; the ONLY branch edge in all of .text is the backward jmp 0x4f4133 inside FUN_004f4060 (reachable from its entry, no jump-table entry); stored-LE-dword scan of terran.exe = 0 hits (positive controls live: 164 string-VA hits) -> no indirect entry (A10-A13).
- (d) WHY MISSED (V): Ghidra FOLDED the region into FUN_004f4060 — the decompiled body contains the region verbatim (triad `FUN_005a2ae0(...); FUN_0051dcb0();` at body-line 388, `< 0x54` exit, DAT_00985af0 x5, _rand x3) while index.csv gives FUN_004f4060 size=3058 ending 0x4f4c52; no row and zero export mentions of 0x4f35e0 (A14-A17). The fold edge is backward and cross-span -> the branch edge was absorbed instead of seeding a function at the target.
- ACCEPTANCE `python3 scripts/m306_owner.py` -> **23/23 OK**, exit 0; rerun diff 0 lines. Zero box, zero /proc, zero gdb.
- GREPTILE TRIAGE (PR #277, 3 findings): P1 "earlier guards are missed" was CORRECT and is the second time this failure class landed - `preds==0` at a call proves only that no branch TARGETS it, and `RIVAL4` went on to say "the only gate is the loop's jl", which closes a guard question over an unmeasured state. Measured properly (CFG walked with the call as a WALL): **3 of 3 rets are reachable without executing 0x4f3e08** (0x4f36b9/0x4f38ef/0x4f4050). New A23; the "unconditional" wording is retracted in the identity row and here. P2 "citations point elsewhere": bounds row repointed to :2-8 + A1-A7 :64-70, absorption to :55-63 + A21 :85. P2 "old body claim stays active": fixed by patching M305's own NAMED block in place (its "no body" phrasing was wrong - the body exists, folded into FUN_004f4060).
- CORRECTION TO THE PERMANENT RECORD (H264): the squash-merge title of #277 reads "... triad unguarded ... (22/22)". Both parts are superseded by the review fixes on that same branch: the shipped acceptance is **23/23** (A23 added), and the guard claim is NOT "unguarded" but "no branch targets the call 0x4f3e08 (preds=0); 3 of 3 rets are reachable without executing it". `git log --oneline` cannot be edited; this line is the correction of record. The NAMED.md M306 row and the triage comment on #277 already carry the accurate wording.

## Session 265 (2026-11-16, HYGIENE H264, zero box)
- docs-only: the correction line above. No findings changed, no script touched.
- STATE: M306 #277 MERGED (main f9fca53); B1-B20 + M54A-M306 MERGED; #180/#105 pre-existing and untouched.

## Session 266 (2026-11-16, ANALYSE, zero box) - M307: the folded body's 21x loop walks two 21-pair EVEN-PARITY neighborhood tables; the triad's FUN_005a2ae0 takes (record-index, faction-bit-index); _rand x3 = 2 probability gates + 1 rand%39 draw

- PICK (NEXT_PROMPT OPEN shortlist, collision-checked): "the folded body's MEANING - the 21x(0x54) loop cap + FUN_005a2ae0 args + _rand x3". M306 had settled bounds/entry only.
- ACCEPTANCE `python3 scripts/m307_folded_body.py` -> **20/20 OK**, exit 0; evidence/m307_folded_body.txt 8,115 B; rerun diff stdout-vs-evidence = 0 lines. Zero box, zero /proc, zero gdb.
- (a) THE 21x LOOP @0x4f3c0a: cap is the immediate `cmp eax,0x54` (exactly 1 in span), index [ebp-0xc] zeroed EVERY entry at 0x4f3bf1 (no branch target lands between), sole back-edge jl -> 21 passes/call (`ceil(84/4)=21`, idx 0..80 step 4). It indexes two dword tables T_x=0x67850c / T_y=0x678990 (1 read each in loop). Tile conversion inside the loop = 44-B stride over ds:0x92ae14 (lea chain 5x/11x/44x @0x4f3c8b/8e/93); inner row-walk stride 0x34 over 0x933282, count ds:0x985af0.
- (b) THE TABLES, read from terran.exe .rdata (VA->off 0x27850c/0x278990, file-backed not BSS): the 21 (dx,dy) pairs = **{even-parity (dx+dy)%2==0, |dx|,|dy|<=3} minus the 4 (+-3,+-3) corners** (set equality A9), D4-closed under negate+swap (A10), ordered center(0,0) -> 8-ring {(1,-1),(2,0),(1,1),(0,2),(-1,1),(-2,0),(-1,-1),(0,-2)} -> 4 corners (+-2,+-2) -> 8 far {(1,-3),(3,-1),(3,1),(1,3),(-1,3),(-3,1),(-3,-1),(-1,-3)} (A11). NOT a Moore 3x3/5x5 neighborhood (RIVAL-2 fails: no (+-1,0)/(0,+-1)).
- (c) TRIAD @0x4f3e00..0x4f3e08 `call FUN_005a2ae0 / add esp,8 / call FUN_0051dcb0`: callee reads ONLY [ebp+0x8]/[ebp+0xc] (2 int args). arg1=[ebp-0x14] = RECORD INDEX (callee scales *304 into 0x95da10 slots; the coords are read from WORD[rec+0/+2] and those are what get bounds-checked vs ds:0x92a378/7c); its producers in the body: imm 0 @0x4f3902, walk-counter @0x4f3a06, FUN_00507410 out-param @0x4f37f8 - never a coordinate (A14/A15). arg2=[ebp-0x4] = BYTE[ds:0x8f0d60+4], single store @0x4f3604 - used by callee as a BIT position (`shl dl,cl`). FUN_00507410 (17 insns) PROVEN = div-8 decomposition (out1=n//8, out2=1<<(n&7)) (A16). Dump-wide triad shape holds at exactly 3 of 11 FUN_0051dcb0 sites: 0x4f3e08/0x508b48/0x543bc6 (A20, re-confirms M305).
- (d) _rand@0x64c6f0 x3 sites = {0x4f36df, 0x4f3750, 0x4f379f} (A17): TWO probability GATES (remainder tested+jne to epilogue 0x4f404a; moduli = dynamic `idiv edi`, edi=[8380*idx+0x94d690]+7, and `idiv 3`) + ONE VALUE draw (rand%39 kept in esi, consumed via the (1,0x22] range gate and FUN_00507410) (A18/A19). RIVAL "all three are data draws" FAILS.
- HONEST NOTE: my first pass claimed 22 iterations from `(0x54-0)/4+1` - off-by-one; the printed `ceil((0x54-0)/4)=21` + table length 21 is the checked number. A gate that can't fail on an unmeasured state is a defect - both the 22 and the rival checks now bind.
- UNKNOWN (stated, not closed): U1 branch-A/B per-branch semantics (the two seed producers for [ebp-0x1c]/[ebp-0x18]: {0x4f3771,0x4f3833-loop,0x4f3863=1<<[ebp-0x4]} vs {0x4f3a48/54 = WORD[ds:0x8f0d60+0/+2]}); U2 what the 52-B row-walk records ARE; U3 the function's game-level identity (name kept INFERRED); U4 live execution (zero box).
- RETRACTION: none. M306's NAMED UNKNOWN row ("0x54-cap meaning; FUN_005a2ae0 args") is now answered - patched in place.
- GREPTILE TRIAGE (PR #279, 3 P2s, NO P1s — ALL THREE CORRECT, ALL FIXED, none dismissed): (i) A4/A6 asserted constants/addresses, not operands — a cap 0x54->0x58 or inc 4->8 would still have PASSED; now inc/cap/jl-target and the three lea scale factors are PARSED from the mnemonics. The re-gate immediately caught a real bug in MY parse formula ((1+2*4)*4=36 vs the true 5->11->44) that the old address-check could never see. (ii) the triad window printed NOTHING — I sliced the 846-entry `span` with a whole-dump index (out of range); fixed to `addrs`, evidence now prints the pushes at :33-34. (iii) "n//8" was wrong for negative n — the code is (n + (n>>31&7))>>3, truncation TOWARD ZERO (-1 -> 0); wording fixed in script+evidence+registry. Post-fix ACCEPTANCE `python3 -u scripts/m307_folded_body.py`: **20/20 OK**, exit 0, evidence 8,489 B, rerun diff 0 (twice).

## Session 267 (2026-11-16, BUILD B21, zero box) - the recorded m289 run executes as ONE state object (B3 presses + the 9-op founder ledger), is written with BOTH year and the bases count modeled, reloads, and RESUMES byte-identically; the per-turn curve is MEASURED strictly coarser than the op log
- MODE=BUILD (track_mode: analyse_since_build=3, last B20) -> took the queued rung B21, UNAUTHORED: authored it into BUILD_SPINE.md from B3+B8+B10+B13 (as B14-B20 did). The two NEXT_PROMPT candidates were NOT taken: the FUN_005aff90 value body has exactly 1 recorded lazy row to grade (no discriminating parity), and the B15+B16+B17 end-to-end would trade recorded inputs for the declared live-drift class with no new witness.
- ACCEPTANCE `python3 -u -m sim.selftest --b21 programs/saves/m54b_clean.SAV` -> **PASS B21: 12/12**, exit 0; evidence/b21_composedrun.txt 9,142 B; rerun stdout-vs-evidence diff 0 lines (re-run identical after the review fixes too). Zero box / /proc / gdb. CLI `python3 -m sim.composedrun --sav <sav> --out <f>` exit 0.
- THE FINDING (`:52-53,74`): the curve and the op log record the SAME run at different granularity. sum|delta| = 7 ops reproduce the n_bases curve; the log has 9 -> exactly one turn hides a net-zero (+1,-1) pair; a DP over (interval x prefix) counts K=11 feasible placements (the run takes the lexicographically earliest - a declared tie-break, NOT a measurement). Falsifier: the curve-only schedule (B10's method) still matches the curve 30/30 but hits only 7/9 recorded (kind, pre-cnt) rows; the log schedule 9/9.
- COMPOSITION (new capability): ONE state object (save ledger + B3 engine); savewriter composes year@84 2150->2180 AND the bases dword 18->23 in one image (grew exactly 1520 B = 5x304, header diff 2 bytes at 72/84, both modeled, tail 10,800 B identical); sim.save reloads it (year 2180, 23 records record-for-record equal); the NEW resume leg: reload + 1 press == 31 presses then write, BYTE-FOR-BYTE (img->img2 = the single changed year byte @84) (`:63-69`).
- The recorder's own law, measured: after(t) IS before(t+1) (self-chain 29/29 on year, n_bases AND (cur,tf)) so 60 samples collapse to 31, all supplied IN ORDER by the 331-state emission (`:54-55`) - B9's "model rows may be extra" under a 2-samples-per-turn recorder.
- RIVALS fail the same fit (`:72-78`): no founder leg 6/30 (endpoint 18), all-9-ops-in-the-last-interval 7/30, curve-only 30/30 curve / 7/9 ops, FIFO-destroy keeps (6,1,43) - a site the record says was destroyed - and a writer that leaves cur_player in an AI slot is REFUSED a press by the resume leg (`:78`). G12: two runs -> table sha e877d7e1... and image sha 791a0d54... identical.
- GREPTILE TRIAGE (PR #280, 3 P2s, NO P1s - ALL THREE CORRECT, ALL FIXED, none dismissed): (i) the resumed engine was built from a hardcoded (cur=3, tf=0) instead of the fields IN THE IMAGE, so a broken turn-field write could not be caught - the resume now reads cur_player/tf-bit/year back out of the written bytes and a corrupted-cur rival (R7) is REFUSED a press (`:78`); (ii) mkdtemp'd saves leaked (2 per acceptance) - now a TemporaryDirectory with the Save kept in memory; (iii) the miss report used `i // 2` on a COLLAPSED sample list, naming the wrong turn - each retained sample now carries its own turn labels. The first post-fix run died on a print TypeError (not enough format args) - fixed, and the re-gate is 12/12 with the rerun diff 0 (twice).
- RETRACTION/QUALIFIER: no prior claim was wrong, but B10's schedule-derivation METHOD is now BOUNDED (a per-turn-delta schedule is provably lossy about the op stream) - patched into the B10 NAMED block in place and into NEXT_PROMPT's CLOSED law list.
- STATE: B21 UNMERGED (this PR); B1-B20 + M54A-M307 MERGED; #180/#105 pre-existing, not this chain.

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
- Acceptance `python3 -u scripts/m312_goal_callers.py` -> **== M312: 26/26 ==**, exit 0, two runs byte-identical, `digest e25f77bb08585dfe` (`evidence/m312_goal_callers.txt`); `python3 -u scripts/m312_mutate.py` -> **17/17 mutations reddened their target checks** (`evidence/m312_mutate.txt`).
- THE RETRACTION (A4): FUN_00470fe0 gates its invalidator tail on arg4 != 0 (`cmp [ebp+0x14] / je 0x47108b`) and ALL FOUR forwarder sites (0x47169A/6D6/802 inside 004715d0, 0x472151 inside 00471fd0) push literal `0x0` - so M310's "site 1" (0x471086) is UNREACHABLE from every caller in the binary; only the 4 direct sites fire FUN_00470b90 (all internally gated on `this+0x1dd70 & 0x2000`; 004715d0's three also pre-gated, `je 0x4719d3` at 0x47183e skips all three).
- TRUNK A (cursor): FUN_004736a0 (64 B, single callee, 15 dump call sites) pushes exactly `cursor_x_list[cursor], cursor_y_list[cursor], 2` (globals 0x91b5f0/0x91b670/0x91b5e8, NAMED ledger) -> FUN_004727c0 (valid-tile gate FUN_00469060) -> FUN_004725a0 (computes block `(ds:0x985ae8&0x80)?-1:ds:0x91b5b4` - M310's filter, same encoding) -> sweep FUN_004715d0: y = arg_y-3 (0x47166F/0x47185F), x in {arg_x-1, arg_x+1} clamped through FUN_00469010, every candidate gated FUN_00469060 != 0, the loop site additionally FUN_00422060 != 0 (0x4719b8). Fan-in also from FUN_00473760 (over the view-instance table ds:0x7cdecc[0..8]: element IS this, i != 0 requires element+0x1dd74 == 0; array pointer written by the single cache-wide store 0x5803e1 <- 0x8f79e0) and view-move FUN_00473d00 (kind=2, gated view+0x1dd8c bit 4).
- TRUNK B: the 5 hub arms (FUN_00472810, 53 sites / 28 owner functions) pass (block, param<0) into FUN_00471fd0 - NOT a coordinate pair; 00471fd0's invalidator call consumes the view-unpacker outputs (M310 site 5, unchanged).
- KICKOFF-CORRECTION: 0x4725e9 sits in FUN_004725a0 (544 B), not in FUN_00471fd0.
