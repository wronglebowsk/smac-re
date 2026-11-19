# Session notes archive — sessions 246-246

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-245-245.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 246 (2026-11-10, s246)

### 246a. #258 (B16) closed per the MERGE RULE and merged (main 9567ec1)

Greptile posted 1 P1 + 2 P2 at 22:20; dispositions (full text in the PR body):
- P1 ACCEPTED: the 8482 pass-6-no-row cells are also the value-vs-best skip
  (0x563c09-0x563c11 after the chain, before GDEEP 0x563c3d). Relabeled
  sim/precheck.py (NOTE + UNMODELED), NAMED.md, NEXT_PROMPT.md; bytes pinned by
  extending evidence/b16_precheck_window.txt to 0x563bf0-0x563c60 (284 insns).
- P2 stride: BYTE[0x92ae81 + 144*BYTE[0x98adac + 52*type]] (lea*9 then shl4,
  0x55f757/0x55f75c) - fixed in precheck.py:37, NAMED.md, SESSION_NOTES.md:671.
- P2 report: report_text counts matched pins now; chain evidence regenerated
  (`python3 -m sim.precheck --out evidence/b16_precheck_chain.txt`).
- s245c self-audit REFUTED, no code change: DISP prints unit-record fields
  0x933278/0x93327a (true X,Y); law orientation 201/201 vs them, the audit's
  untransposed orientation 0/201 (BASE rival_disp_ok) - G2 tests the pair the
  law names; the proposed re-key would install the rival the gate rejects.
`python3 -m sim.selftest --b16 programs/saves/m54b_clean.SAV` PASS 7/7; merged
via `python3 scripts/milestone.py merge 258` (Greptile registered no check run on
the new head inside the 10-min cap - operator amendment 2).

### 246b. M295 - the 0x4e3c00(owner,X,Y) no-go NAMED, pinned, MEASURED INERT

fn.py + dis: FUN_004e3c00 = territory_nogo, calling FUN_004e3b50 =
owner_of_tile_visible: tile7 = signed BYTE[44-B tileview+7] (B16's view/form,
0x4e3b53-0x4e3b76; movsx at evidence/m295_nogo_window.txt:19), visible if
BYTE[0x985ae8] bit 0x80 or pair-flagword bits 3+27 (immediate 0x08000008,
window :45,:46). pair array base = per-faction block 0x94d430 (disasm constant,
170 uses, e.g. [edx+0x94d430] at 0x429ab9) + 0x18 = 0x94d448 (M143 folded
[owner*2095+tile7]*4). c00 blocks
(returns non-negative) iff tile7 >= 1, tile7 differs from the pod owner, the
human-mask BYTE[0x985b10] (NAMED M96; masked 0xff at 0x4e3c34) has the pod or
tile bit, and the flagword bit 4 is CLEAR (alliance, window :120). The return value is
FUN_004e37f0's (nearest-base sweep writing DAT_008f0d34 = M294's dist;
sentinel 9999). MEASURED `python3 scripts/m295_nogo_fit.py` (evidence
m295_nogo_fit.txt): over the m294 window the full rule rejects 0 recorded
slots and 0 pass-6-no-row cells (697 owner-known visits; 329 visits with
unresolvable u above the 67-record units array); t7 dist of the 8482:
255:2490, 4:2058, 6:1822, 5:1190, 2:872, 1:45, 3:4, 7:1; human_mask 0x8,
feature_bits 0x0. Rivals collide with recorded slots: foreign-only 1045,
+mask 124, +not-ally 119. Within the graded subset R4 rejects nothing, so the
8482 are BEST EXPLAINED as the VALUE<=BEST ARGMAX SKIP (0x563c09-0x563c11) -
the next leg. NOT CLOSED (Greptile P1c): grading covers the 697 owner-known
visits vs the y2150 save (window is y2188+); live-flag-matched inputs are the
only closer. Cites: window :19,:45,:46,:104,:120,:122;
fit evidence/m295_nogo_fit.txt:4-8. Window scripts/m295_nogo_window.py -> evidence/
m295_nogo_window.txt (129 insns). Callers 0x5597ea, 0x563963/0x5643e9/0x5647a1
(the last three inside FUN_0055f650) - lead.

### 246c. Greptile round 2 on #259 (3 P1 + 1 P2), dispositions

- P1 "wrong flags" ACCEPTED: block A record base is 0x94d430 (170 disasm uses;
  0x94d104 appears 0 times - the atlas headline phrasing is a fix-lead), so the
  pair-flagwords sit at saved block+0x18. Script fixed, evidence regenerated:
  R3 collisions 91 -> 119; R4 still 0 rejects.
- P1 "wrong bit" ACCEPTED: the recorded immediate is 0x08000008 = bits 3+27
  (not 31); the 0xff-masked human-mask read is at 0x4e3c34 (window :104).
  Model + all descriptions corrected.
- P1 "partial results" ACCEPTED: INERT claim softened everywhere to "0 rejects
  in the graded owner-known subset vs the older save"; live no-go stays OPEN
  and s247's pick carries that.
- P2 (path:line cites) ACCEPTED: window/fit line cites added to 246b and the
  NAMED ## M295 rows.
