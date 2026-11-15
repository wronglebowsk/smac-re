# Session notes archive — sessions 237-238

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 237 (2026-11-10, BUILD, B13 12/12) - M290's founder dispatch is EXECUTABLE: sim/hubfound.py - own-tile-gated (distant target = msg 0x2408, never founds), founder args = the POD's record fields, capacity-only guard; 7/7 recorded founding tuples replay exact, strict ledger 18+7-2=23 peak 24 vs the m289 curve, both rivals fail the same fit
- track_mode BUILD (3 ANALYSE fires since B12) -> the rung went into
  BUILD_SPINE.md FIRST (pod-driven founding-dispatch leg, replacing B10's
  REFUTED (x,y) placeholder), then sim/hubfound.py + run_b13 in sim.selftest.
- ACCEPTANCE: python3 -m sim.selftest --b13 programs/saves/m54b_clean.SAV
  -> PASS B13: 12/12 (evidence/b13_hubfound.txt; 3rd invocation; runs 1-2
  were instrument bugs - python3.14 argparse refuses a 3-tuple metavar with
  nargs='+', and a 6-tuple event unpack - floors never weakened).
- MEASURED: every one of the 9 recorded rows' PRE-op cnt agrees with the
  ledger replay through B10's leg (destroy slot ASSUMED last, declared);
  survivors (6,20,48)(6,63,51)(5,27,19)(7,23,33)(1,27,29), destroyed
  (6,12,48) and (6,1,43) ABSENT from the final 23; written image: only the
  bases-count dword (offset 72) differs in the prefix, originals + tail
  byte-identical, re-parses n_bases 23; cat44 (44-B record view) puts all 7
  sites on land (cat 3) and none on a base tile; G12 CLI two runs sha256
  6dfbd810a1b6013f. RIVALS: ungated distant dispatch invents 7 tuples of
  which 0 occur in the record; the B10 placeholder reproduces 0/7.
- REGRESSION: B10 18/18 and B12 12/12 still green (basefound._tile marked
  REFUTED, comment-only edit).
- OPEN (unchanged): why the 5a0aa0 chain bailed 3x; M247; M70 x2. The pod
  WALK stays the only unmodeled link between a pod and a founding.
  Next: ANALYSE - the pod-walk target rule (the scan's score law at
  0x563c00-0x563d40 vs the recorded founding TURNS).

## Session 238 (2026-11-10, ANALYSE, M291 10/10, no box time) - the hub's founding SCAN is a STRICT site-value argmax over a 25-entry even-manhattan ring, NOT a (dist*10000)/(value+1) score (that immediate is absent from the 54,483-B body); the record falsifies dropping the owner byte3 gate
- track_mode ANALYSE -> the s237 pick: the pod-walk target rule, static+model.
  scripts/m291_pod_scan.py, 10 gates. ACCEPTANCE: python3 scripts/m291_pod_scan.py
  -> PASS M291: 10/10 (evidence/m291_pod_scan.txt; 6th invocation - runs 1-5 were
  all instrument bugs of mine, floors never weakened: three x86 encoding mis-
  transcriptions (imm8-vs-imm32 for cmp eax,0x19; ModRM for cmp esi,[ebp-0x24])
  plus the heredoc transport that unescapes backslashes INSIDE heredoc content
  (byte literals landed on disk as raw bytes; the shipped script uses bytes([...])
  lists and no backslash classes, and an & even in a comment is refused by the wrapper).
- MEASURED (bytes from the terran.exe file image): ring tables 0x67850c/0x678990
  (.rdata, 25 dwords): entry 0 = own tile, 1-8 = the manhattan-2 diamond, 9-24 =
  manhattan-4, ascending; wrap 0x469010/0x469060. Value = FUN_0046e770: and-eax-
  0x1000 -> 0, else mov dl,[rec+2] + sar 4 (lazy FUN_005aff90 when the cache is 0).
  Strict max: cmp esi,eax then jle 0x563cb3 (ties keep the closer ring entry);
  best-store 0x563caa. Nearest-location distance FUN_004e3620 (9999 sentinel
  0x4e3631, store DAT_008f0d34 0x4e36f5, 152-B-stride location list, map-wrapped
  max-min octant formula); value >= 2*(8-DAT_008f0d34) bypasses the per-site
  0x94e5a8/0x94eca8 gates.
- FIT vs the 7 recorded tuples: 7/7 self-argmax over their own ring (grown
  occupancy, 44-B record view); the no-owngate variant loses EXACTLY fac1 (27,29)
  (byte3 14 vs a rival - owner-equality is required by the record); B10 first-
  unoccupied 0/7; seeded null self-argmax rate 27/88 = 0.307, binom p(7/7|null) 2.6e-4.
- Box: only the recon pass did a READ-ONLY /proc ring-table probe; the acceptance
  reads the .rdata file image. pid 4087359 untouched, TracerPid 0.
- OPEN (unchanged): the 5a0aa0 chain bailing 3x; M247; M70 x2. UNMODELED: the
  0x94e5a8/0x94eca8 gate tables and the 0x4e3c00 no-go (the 7/7 fit passed without
  modeling them). NEW frontier: POD MOVEMENT - which pod (callers of FUN_0055f650,
  unit id) and the per-turn walk vs the recorded founding turns (rise turns
  6,9,18,19,22,23); needs a unit-position census (box). Next: ANALYSE - the
  pod-movement leg.
