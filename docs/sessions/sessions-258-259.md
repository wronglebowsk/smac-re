# Session notes archive — sessions 258-259

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 258 (2026-11-15, BOX-READ read-only /proc) - M302: B19's declared-unmodeled live values pinned; the 1099 undecided branchA rows collapse to 38 accept / 1061 refuse
- ACCEPTANCE `python3 scripts/m302_livepins.py` -> PASS M302 10/10,
  evidence/m302_livepins.txt (table first, then A1..A10; verdict :170). READ-
  ONLY on the box throughout: os.pread on /proc/501182/mem (pid from pgrep -x
  terran.exe), no pwrite/gdb/poke/relaunch; TracerPid printed 0 at start AND
  end; year 2150 + round 50 unchanged across the pass (A10); an unmapped read
  reports UNKNOWN (self-tested via the 0x1000 sentinel, A2), never 0.
- PINNED (y2150, m54b_clean): ds:0x92a380 (rand+1) = 9661 (0x25bd; & 0xf = 13),
  ds:0x69220c = 61, ds:0x692210 = 11, ds:0x985ac4 = 0x1a0e so bit 0x2000 is
  CLEAR - flag2000=False, B19's declared baseline bit-state CONFIRMED live.
  Slot region 0x989ce8+28*site: 128/128 slots readable (3584 B, no UNKNOWNs);
  the recorded sites: site 1 MAX 15 / counter 40, site 9 MAX 3 / counter 2;
  nonzero MAX sites [1,3,4,5,6,7,9,10,13,14,15,16,65,66,69,70], nonzero CNT
  [1,6,9,13,16,63,65,70]. The table is NONZERO at a freshly-loaded idle box ->
  carried by the save or rebuilt at load (OPEN); CNT>MAX occurs at [1,63,65] -
  no landed law relates the two fields (MAX is fed by the 4-bit nibble cache
  or the UNMODELED FUN_005aff90 body), so counter<=MAX is PRINTED, never
  asserted; the two-pass read never decreased any field (MAX store + ++ are
  the only writers, B18 G8 + B19 - A5).
- REPLAY (shipped sim.visitcounter rows/P/grid + the pinned Live): 2321 rows ->
  CERTAIN-accept 38 / CERTAIN-refuse 2283 / still-undecided 0. The 1099
  previously-undecided branchA rows: 38 CERTAIN-accept / 1061 CERTAIN-refuse /
  0 undecided (A8), per-B18-site {1:(38,993), 9:(0,68)} == B18's anchor rows.
  Legs: 37 branchA-hit (eax=2, live residue 13) + 1 branchB (eax=1 - the FIRST
  non-structural eax=1 decision row; B19 had 0 witnesses) + 1062 branchB-refuse;
  all 1222 rung1 rows still refuse (A6); eax in {0,1,2} (A7). B19's 20
  baseline accepts (rand==1) ALL flip - the 38 live accepts are a different row set.
- PITFALL: the `s` field of the m294 graded_rows tuple is the LOG SLOT key, NOT
  B18's site id - per-site splits must go through sgt.site_of(rec); the first
  run printed 25 "sites" (a mislabel caught only by pairing against B18's
  {1,9} anchor).

## Session 259 (2026-11-15, ANALYSE, zero box) - M303: the 0x51e02c "post-counter read" is the LOAD HALF of a byte CNT++ on the per-block twin of the slot table
- ACCEPTANCE `python3 scripts/m303_downstream.py` -> PASS M303 10/10,
  evidence/m303_downstream.txt (S0-S9 tables, then A1..A10; two runs byte-identical).
- MODE: track_mode printed ANALYSE (analyse_since_build=1, next_rung B20) although
  the s258 NEXT_PROMPT pick claimed a merge flips the next fire to BUILD -
  track_mode is authoritative (the kickoff itself said so); B20 stays queued.
- THE ANSWER: 0x51e02c is not a read-for-a-test - it is load++store
  (0x51e02c mov dl / 0x51e033 lea eax,[SAME SIB+disp] / 0x51e03a inc dl /
  0x51e03e mov [eax],dl), entered on the SAME `je 0x51e007` fall-through as the
  dword CNT++ (M299), inside FUN_0051dcb0 (the per-map-tile pass: outer loop
  advances tile records by 0x2c at 0x51e128). Byte addr = site + 8380*block +
  0x94ed28 - shadow-fold 65=64+1 -> 131=1+2*65 -> 2095=131*16-1 -> *4; the two
  6-insn folds (0x51dfd3/0x51e013) are BYTE-IDENTICAL (rematerialized across the
  0x51dffd call). The table: 0x94ed28 = 0x94eca8+0x80, the per-block visit-CNT
  byte array, twin of the MAX byte array at 0x94eca8: 8 blocks x 8380-B records
  (init 0x51dcb8-0x51dd03: byte fields [edx+site] and [edx+site+0x80] zeroed,
  edx steps 0x20bc to 0x95f288 - the SAME 8380 the fold computes, derived twice),
  128 entries x 1 B - the BYTE twin keyed by (block,site) of the DWORD slot
  table 0x989ce8 keyed by site. B18-28-B REFUTED for THIS expression:
  (site*8-site)<<2=28*site is the esi fold 0x51dfb1-ba three insns earlier
  (SIB 8d 34 c5 vs 8d 04 53), feeding the DWORD twin; multipliers 28 and 8380
  coexist in one window.
- CONSUMER CENSUS: 11 literal mentions = the whole corpus (A1); MAX field: 6
  external readers (FUN_0050d140/FUN_00556690/FUN_0055f650x4) + the in-window
  max-store 0x51dff3 (gated ebx!=0 by je 0x51dff5); CNT field: ONE external
  reader FUN_004f6030 0x4f946d -> test al,al/jne (a visited? gate). ALL
  external consumers terminate in cmp/test (A7); NO family byte feeds the DWORD
  0x989ce8 (both MAX stores take the walk candidate edi; loaded bytes appear
  only in the cmp); NO store to family/twin outside FUN_0051dcb0 (A8: 6 init
  zeros + 5 update sites incl. the sibling `inc WORD[0x94e8a8]` @0x51df3d -
  same 8380 block phase, width 2, scale *2: proof the *4 at 0x51e02c is
  multiplier placement, not entry width). The post-store branch 0x51e040 `je`
  tests `test ebx,ebx` flags, never the byte; dl dead after 0x51e03e.
  name_global.py 0x94ed28 --disp says "0 writes" - correct about LITERAL writes
  only; the 0x51e03e store is register-after-lea pointer form (A10) - the
  two-instrument disagreement is the finding's teeth.
- PITFALL: byte-reg->dword-reg naming must be a lookup table, NOT `reg[0]+"ax"`
  (that yields "aax"): three S6 rows printed "no consumer" until fixed - the
  A7 assert (every reader finds a consumer) is what caught it, i.e. the
  table-then-assert shape earns its keep.
