# Session notes archive — sessions 213-213

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 213 (2026-11-05, ANALYSE box pick, M273 PASS 7/7) - the row stride 188 is a fixed 94-slot capacity; no spill on the live map
- Pick: "what the row stride 188 means" (M256 G5's OPEN row). `scripts/m273_rowstride_watch.py`
  (silent bps at BOTH 0x94eaa8 read sites + YEAR control 0x51f554 + live region-count reads).
- ACCEPTANCE: `python3 scripts/m273_rowstride_watch.py --replay evidence/m273w3.gdblog` ->
  **ACCEPTANCE M273 PASS 7/7** (`evidence/m273_acceptance.txt`; /proc facts in
  `evidence/m273w3_proc.json`, written by the live run - the replay never hardcodes them).
- ANSWER: live count DAT_0092ada4 = 91 (pre AND post stable) == save-derived 91 for 64x64;
  188 = 2*94 is a FIXED capacity (8380 mod 188 = 108 - NOT derived from the faction block stride);
  91 < 94 so the M256 spill is UNREACHABLE on the live map. SCALED identity live 7/7
  (2*edi == region slot). UNSCALED row = per-faction cursor: row mod 8380 = 2 for all, deltas =
  whole 8380 strides. OPEN (new picks): 80x80/128x128 counts 128/338 EXCEED 94 (spill question
  migrates there); the fold's per-faction term advances by HALF a block stride (44.5); region-loop
  depth per phase (observed s10=1 only).
- Instrument law (cost one dead box, w1): a bp at 0x5584b1 = the SECOND BYTE of the 8-B load at
  0x5584aa - INT3 mid-instruction corrupted the encoding and Wine Dbgrc crash-boxed terran.exe
  (TracerPid reads 0 afterwards; only the on-screen dialog is the witness). Always break at the
  disassembled NEXT-instruction address (0x5584b2), never load+1. Recorded in skill
  references/instrument-laws.md.
- Box: w1 window crash-boxed the game; relaunch was ~35 s (fast path holds); w3 driver m55_boundary
  PASS one boundary (2152->2153) with 14 site events + control. Box left UP, TracerPid 0.
- My own gates were wrong twice before shipping (G2 asserted 188==2*count; G5 paired events by
  (round,s10) which the sites do not share) - the FAILs were instrument bugs, fixed by rewriting
  the assertion to what the evidence can bear, never by moving the floor.
