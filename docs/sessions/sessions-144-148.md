# Session notes archive — sessions 144-148

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
