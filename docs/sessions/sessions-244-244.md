# Session notes archive — sessions 244-244

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 244 (M294, box fire) - pod-walk gate-row census RE-ARMED; B15 law predicts every dispatch from printed rows
- Instrument scripts/m294_gate_row_census.py: m292 static gates re-run (never reused blind) + 27 NEW byte-pins
  (S1/S2 PASS) for GDEEP@0x563c3d/GACC@0x563ca7/GROW@0x563cb3 + prologue/fold pins; blk fold identity 8380*o re-derived.
- Box: s241 state was BLOCKED (pending 0, then credit 0 - structural in this save, d0-gated); ran accept_ready FIX
  (relaunch+m54g_prep+drive 1+enqueue), then advanced 37 turns to y2188 (m54b_clean's recorded year), 24-turn census.
  Rows: HUB=2870 (rets exactly {0x50dd89,0x56cf17}), DISP=192, ISS=184, FOUND=4, CTRL=1857. TracerPid 0 post, yama restored to pre (0).
- Run 1 model FAILed 2129/2129 visits with ZERO direction-of-law failures -> static diagnosis (dis 0x5638a9-0x563bf7):
  the loop head has 7 eligibility pre-checks jumping straight to the 0x563cb3 tail (walk 0x469060, mask vs [ebp-0x58]
  0x563917, elev 0x563928/3e, region: BYTE[tileview+3]==[ebp-0x34] AT 0x56394E ([ebp-0x34] stays the POD region through
  the whole loop - the gate's region IS the pod region), 0x563954 dh&0x20, no-go call 0x4e3c00>=0 @0x563963) - on those
  paths tail $esi = slot/x garbage, not value. Fixed replay (decision rows carry exact incoming best; winner = last
  accepted slot; tail win cross-check); selftest scratch/m294_model_test.py 3/3.
- REMODEL over the RECORDED rows (same B15 grading law): G5 parity 2129 visits / 2321 decision slots / 260 accepts /
  0 disagreements / 0 DISP-without-rows; G4/G7/G8 PASS; VERDICT PASS. evidence/m294_gate_rows.txt; raw
  m294_gate_rows_raw.txt; run-1 trail evidence/m294_gate_rows_run1_note.txt (the 2 MB run-1 report was overwritten by
  the rerun rename pre-commit - trail gap recorded, numbers in the note).
- G6: targets (22,14)/(18,2) did NOT recur this window (foundings (6,46),(12,48),(40,14),(62,46)) - recorded, not hidden;
  in-window row-dependent accepts printed (e.g. u=45 slot24 val6 mult7 gate10 verd0 case8 tiles345 -> case8open).
- STEP 2 (static, after green): FUN_0051dcb0 has EXACTLY 11 e8-callers (incl. the founder vector FUN_004e47d0@0x4e4dc8);
  site_gate store 0x51dff3 = max(cell@0x51dfeb, edi); edi = BYTE[rec+2]>>4 (0x51df85) OR call 0x582cc0 result (0x51df9f,
  after 0x5aff90@0x51df97); cell addr = 0x94eca8+[ebp-0xc]+4*min(edi,[esi+0x989ce8]) - VALUE-INDEXED (flagged).
  evidence/m294_sitegate_callers.txt. OPEN: semantics of 0x582cc0 + [ebp-0xc] index.
- Evidence +~2.7 MB -> evidence.py budget printed at close; NAMED ## M294 <=1 KB added.
