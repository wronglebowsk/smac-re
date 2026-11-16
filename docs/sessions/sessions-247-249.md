# Session notes archive — sessions 247-249

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 247 (s247, M296, 2026-11-11)

- M296 THE ARGMAX LEG FITTED, all-static (no box touched): `python3 scripts/
  m296_argmax_fit.py` -> evidence/m296_argmax_fit.txt: **PASS M296: 9/9** over (Greptile #260 round 1: 4 P2s - evidence now saves the REPORT lines, S0 coverage pins 1026/2321/25650/8482, byte9 labels, tie-claim softened below)
  1026 visits / 2321 GDEEP-GACC rows / the 8482 pool. Byte windows: evidence/
  m296_init_window.txt (scripts/m296_init_window.py, 11 pins OK).
- BYTE FACTS: (1) `and eax,0x1000` at 0x46e792 tests dword[rec+8] bit 0x1000 =
  BYTE9 bit4 (NOT byte8 - the M295-era shorthand is corrected here); 1083
  in-window tests, all pool-side (never a row). (2) [ebp-0x24] is zeroed
  unconditionally at 0x563839 EVERY scan; the ONLY override is case==8
  (`cmp esi,8` 0x563836) + order-0x18 (`cmp BYTE[unit+17],0x18` 0x563845 - the
  move-to-base order, NAMED 0x4d3770/0x4d6fb0, +20/+28 = base tile) +
  wrapped-diff gate>2 (0x46e540/0x46e5a0): best_init = value(base tile)-1
  (0x563896-9f). A move-to-base pod accepts candidates >= its base tile's value;
  every other visit starts best=0.
- FIT: S1 val>best 2321/2321; S2 best == max(best_init, prior GACC vals)
  2321/2321; S7 GROW best column replays 25650/25650 slots; S7b case-8 leg 1/1
  nonzero-init, value leg 0 save-gradeable hits (the lone move-to-base init
  u=45 best=5 carries a save-STALE dest: (19,6) byte2=0x05+0x1000 bit, not a
  save base - live closer); S5 rivals miss the val column (low 105, cat 98,
  full/b8hi 0 vs nib 1931/2321); S5b: 0 of 2321 rows has val==best (>= never observed; 5721 static tie candidates corroborate, nogo-unverified); S6
  bypass 61/61 + 0 GDEEP rows at/over the 2*(8-dist) cap. S3 static val
  coverage 1739/2129 AGREED + 192/192 DRIFT; 390 mismatches = LIVE byte2
  mutation (9 tiles carry 2+ machine-attested vals). Pool: 6048/8482
  static-explained as val<=best skips (5721 ties, 904 of the explained via the
  0x1000 zero); 2434 unexplained = mutation/no-go/live class - THE LIVE
  FLAG-MATCHED CENSUS (M295 P1c + this) is the shared closer - LEAD.
- s245/s246 facts held; kickoff M295 re-run first: R4-empty table verbatim
  (evidence/m295_nogo_fit.txt). NEXT_PROMPT regenerated (s247 close).

## Session 248 (s248, B17, 2026-11-11)

- BUILD FIRE (track_mode printed MODE=BUILD next_rung=B17). The rung was not in
  BUILD_SPINE.md, so this fire AUTHORS it (B14/B16 precedent): **B17 - the
  pod-scan loop DECISION CORE made executable**. `sim/scanleg.py` COMPOSES the
  M296 best/argmax chain (best_init law + accept store 0x563caa + winner),
  B15's price_gate (sim.gatetables) and B16's grid law (sim.precheck, read
  TRANSPOSED) into ONE slot-strict replay of the m294 gate-row window.
- ACCEPTANCE `python3 -m sim.selftest --b17` -> evidence/b17_scanleg_chain.txt:1
  **PASS B17: 10/10**: G1 pins 1026 visits / 2321 decision slots / 25650 GROW /
  260 accepts / 61 bypass (m296 S0 + NAMED ## M294); G2 best_init law-vs-machine
  990/1026 (the zero-leg needs NO unit record; 362 scans name post-save units -
  bucketed not_in_save, never graded as saved state); m2b class 36 = 3 save-
  recorded (u=45 machine-5 vs save-dest -1 = the S7b stale-dest class, value leg
  OPEN; 2 save-invisible dests) + 33 unit-not-in-save; case-8 leg 1/1; G3+G4 the
  GROW BEST *and WIN* columns both replay 25650/25650 (the win replay is NEW -
  M296 pinned best only) AND the M296-S2 incoming-best law re-checks all 2321
  decision rows against the REPLAYED best; G5 accepts 260/260 predicted from the REPLAYED best
  (bypass 61 + legs value 4 / bases 192 / mult0 2 / case8open 1), 0 GDEEP rows
  at/over the 2*(8-dist) cap; G6 predicted winner == DISP esi 201/201 (0 drift
  skips); G7 save-view val-law 1931/2321 (lazy 1; 0 tie rows; 0x1000-zero tests
  pool-side only, 1083); G8 pool 6048/8482 explained (5721 ties), 2434 DECLARED
  residue; G9 rivals fail the SAME grid (>=-argmax 5721 tie cells; frozen-best
  diverges 1713/25650; no-bypass +61 GDEEP; no-init-law 24 slots in u=45); G10
  two module runs byte-identical (sha256 pinned in the evidence).
- Kickoff per the fire's shape: M296 re-run FIRST -> **PASS M296: 9/9** verbatim
  (re-run, not re-derived); #180 (M241) re-checked: zero inline comments/reviews,
  still 2/5 gates = no real PASS to merge on, stays open unchanged.
- NO box time (build track: no /proc, no gdb). The live-map flag-matched census
  is UNTOUCHED - it stays s249's pick (THE PICK in NEXT_PROMPT, regenerated).

## Session 249 (s249-m297): M297 - the LIVE-MAP flag-matched census
Open-PR sweep first: B17 re-ran green on main - `python3 -m sim.selftest --b17` ->
evidence/b17_scanleg_chain.txt:1 "PASS B17: 10/10 gates ...". #180 (M241)
re-confirmed the documented-FAIL milestone (2/5 gates, zero review activity since
2026-11-01) - left open, gates NOT weakened. #105 = docs badge, not a milestone.
CENSUS (scripts/s249_livecensus.py --predict then --live; accept_ready.py BLOCKED
on the structural credit-0 (documented, walk/scan kinds run anyway), preflight PASS;
ONE read-only /proc pass, zero gdb, TracerPid 0->0, yama 0 recorded/restored
unchanged, year 2212 cnt 30 pinned before AND after, starttime identical):
tileview base = dword[0x92ae14]=0x40a5cd0, 44 B x 2048 recs dumped
(evidence/s249_live_map.bin), rowmul 32 = W/2, bounds 64/64, byte0/byte3
identity 2100/2321 (90.5%). RESULT: the 8482-cell pool under LIVE bytes closes to
UNEXPLAINED 0 (tie 7518 / lt 287 / live-static-fail 677 / no-go 0); the 2434
residue = tie_live 2146 + lt 35 + static-fail 253. M295 P1c: no-go R4 on LIVE
flags rejects 0/8482 AND 0/2321 - INERT, explains none of the residue. Rivals
fail the live grid: R1 1538 / R2 42 / R3 42 recorded collisions, ge-argmax 7518
ties printed no row. u=45 CLOSED on the dest-moved branch: live unit-45 order
+17=0x00, dest(9,47), owner 6 vs save 0x18/(19,6). S3 strict live row law =
documented FAIL finding: 2102/2321 exact, lazy 0, drift-after-grading 219
(bit4-flips 134 + nibble 85; 201 machine-attested, 18 unattested) - an
end-of-window snapshot grades only the LAST turn's rows. scripts/s249_attestation.py
re-derives the scorecard + taxonomy from shipped evidence (idempotent block).
