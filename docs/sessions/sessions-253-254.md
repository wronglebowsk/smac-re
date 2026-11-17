# Session notes archive — sessions 253-254

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 253 (2026-11-11, STATIC, zero box) - B18 #264 CLOSED: the review round (10 P1 + 2 P2) fixed IN-BRANCH, MERGED #264
- s252 died mid-close-out; its kickoff claimed no outstanding P1s - WRONG: 10 P1 +
  2 P2 inline comments sat on head 522cdc8. Every finding run to ground against the
  pinned windows; all fixed IN-BRANCH (or dismissed WITH a shipped proof, below).
- The unfinished script = scratch/sitegate.py = shipped sim/sitegate.py + four FOLD
  DECODERS, DEFINED BUT NEVER WIRED. Wired: G1 DECODES the record fold -> (44-B
  stride, byte +2), slot stride 28 from the chain 0x51dfaf-ba, base 0x989ce8 +
  counter +4 off the [esi+disp] operands (0x51dfcb/0x51e00d), cell fold -> 8380*block
  + 0x94eca8 with the site byte UNSCALED (the pinned lea scales the BLOCK term by 4;
  ecx==site via newly pinned mov ecx,eax 0x51dfaf) - arithmetic identities REPLACED
  by byte-read laws. PINS 62 -> 64.
- decode_max_polarity GRADES old loads: slot = full-DWORD 0x51dfbd; cell = newly
  pinned `xor eax,eax` 0x51dfe9 + `mov al,[ecx]` 0x51dfeb IMMEDIATELY before the cmp.
  G2 nibble law = SYMBOLIC run of the four pinned ops (mask/shift parsed from their
  texts) == write_back 8192/8192; rec2_off byte-graded vs the INDEPENDENTLY shipped
  podscan Grid.rb view 4096/4096 (+ Grid.val getter 4096/4096).
- G3 classifier: a ZERO nibble takes the lazy path WHATEVER the val (new lazy_zero
  class) - EMPTY here: 2288/0/1/32, counts unchanged, control flow honest. G5/G6 run
  only AFTER the live-dump length is validated (FAIL, not IndexError). G5 PROVES
  "dword[rec+8] bit 0x1000 == byte9 bit4" on 8192/8192 dwords - that P1 was WRONG
  (same physical bit). G7 GRADES the eight-block owner family ({-1} u 1..8, <=8
  distinct); G8 enforces cell blocks 1..8. acceptance() all() over ITS OWN gates.
- ACCEPTANCE: `python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` -> **PASS
  B18: 10/10** (evidence/b18_sitegate.txt regenerated); `python3 scripts/gate.py
  --base main` -> GATE GREEN (0 warnings). Box: ZERO.

- LANDING: #264 squashed to main as 487f0b4 at 23:52:47Z (owner account; the own
  `gh pr merge` found it already merged and verified main). GREPTILE SILENT on head
  6ce43b5 (no check run, no new comment within the capped wait). Chain: s254
  scheduled at 23:47:57Z (one-shot, deliver local, the 7-tool allowlist).

- SHARED-WORKTREE INCIDENT (s253): `git add -A` at the main landing swept a
  concurrent out-of-chain actor's UNCOMMITTED M299 WIP into 51b9c4b; they then
  self-committed on top (0ff59c7, local, unpushed). My index-withdrawal was
  therefore UN-DONE (it would have reverted THEIR commit and, pushed, published
  their unreviewed work). Left: their WIP in main's 51b9c4b snapshot + their
  local commit for the operator; my docs warning sits UNCOMMITTED here on
  purpose. RULE: stage NAMED paths only on n100; check `git status --short`.

## Session 254 (2026-11-11/12, STATIC, zero box) - #264 LANDED by this fire + M299 CLOSED
- OPEN-PR JOB: on-head `python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` ->
  **PASS 10/10**; `python3 scripts/gate.py --base main` -> GREEN; #264 squashed to main as
  **487f0b4** (23:52:47Z) with a GREPTILE-SILENT body note (no comment AND no check run on
  head 6ce43b5 within the 10-min cap - amendment 3). B1-B18 DONE.
- COLLISION (rule C): the s253 fire stayed LIVE while this s254 fire ran (amendment 7 booked
  s254 "in 1m", overlapping s253's own merge+landing). Sequence: s254 merged #264 first;
  s253's landing `git add -A` (51b9c4b) swept this fire's uncommitted M299 WIP into main,
  then index-withdrew it (12d6ad2), then reset main back to 0ff59c7 (this fire's pinned
  skeleton, adopted). This fire restored the swept files, pinned its work (branch
  `s254-collision-m299`) and finished ALL of it inside an isolated `git worktree`
  (`~/reverse/wt-s254`, scratch/ symlinked). s253's two warnings (NEXT_PROMPT bullet +
  notes line) are ADOPTED into this PR. LESSONS carried to s255: schedule "in 12m";
  collision-check + worktree FIRST; stage NAMED paths, NEVER `add -A`.
- M299 (THE PICK from the B18 leads): the slot [+4] visit counter's FUN_005832b0 gate.
  `python3 scripts/m299_visitgate.py` -> **PASS M299: 7/7** (evidence/m299_visitgate.txt,
  46 pins + windows W1/W2): G2 the call passes the pinned (x,y) push-slot pair shared with
  0x5aff90/0x582cc0; G3 the callee fold DECODES to the shared 44-B tile_record law (4096/
  4096, sar included); G4 `je 0x51e11d` gates the lone `inc`+`mov [esi+0x989cec]` = slot
  base + 4 on the pinned 28*site esi (0 writes to esi in between; callee pops ebx/esi/edi
  on all 6 rets); G5 PURE 4-rung ladder (0x102000 = B16 occ bit5|byte10 bit4 / 0x985ac4
  bit 0x2000 / 0xc000000 / 0x10000000 / 0x92a380==0, 0x92a380 = **rand+1** per
  MAP_FORMAT.md:116); G6 parity lattice (h&3)+4*(d&3), branch A exactly 1/16 classes
  36/36, 13/13 constants cross-tool; G7 the s249 2048-record dump MEETS the inputs:
  rung1-close 481, occ 16, bits26/27 12, rung3-open 5, class>=0x60 1087. DECLARED:
  counter VALUES + 0x92a380/0x692210/0x69220c VALUES never recorded.
- ACCEPTANCE: `python3 scripts/gate.py --base main` -> GREEN on this branch; merge #265
  per the MERGE RULE (Greptile cap 10 min). Box: ZERO.
