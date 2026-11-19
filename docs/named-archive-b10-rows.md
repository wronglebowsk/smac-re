# NAMED archive — B10 full rows (moved VERBATIM from NAMED.md at s304-chain2, M328 headroom rotation)
# source block sha1[:16] = d298981e8ece0d6e ; byte-exactness asserted at write; the NAMED ## B10 stub governs.

## B10 (s226, BUILD, base-founder/destroyer leg - R2's new-game leg) 18/18

- sim/basefound.py: Ledger = M282 founder FUN_004e47d0(faction,x,y) + destroyer
  FUN_004e4e10, plus the golden-curve pairing (presses the B3 engine the trace's own 40
  turns, applies the trace's own 8 per-turn deltas: t8 +1 t9 +1 t17 +1 t22 +2 t23 -1
  t27 +1 t32 +2 t34 +1 through found/destroy between presses).
- FOUNDER: guard count < 0x200 (512); new 304-B record appended at array start +
  old_count*0x130 (x u16 +0, y u16 +2, faction bytes +4/+5); count +1. DESTROYER: count-1
  with COMPACTION (LAST record moves into the freed slot; record equality).
- CURVE: recorded n_bases 18 -> 26 recovered on all 40 turn snapshots (the B9 declared
  frontier is now modeled - before: model const 18). The t23 -1 is a real base
  DESTRUCTION in the recorded run, through the destroyer.
- WRITE: savewriter's new bases_override/orig_n_bases path composes grown ledgers; the
  only prefix byte that changes is the bases-count dword; the tail stays byte-identical;
  the written image re-parses (n_bases 19) and the founded record (zero name) is
  shape-invisible to sim.save's name scan (found 18, declared: the real game names bases
  later).
- RIVALS: no-leg (B9) shape keeps 18 (32 divergences); all-events-on-turn-0 diverges at t0.
- BOUNDED BY B21 (s267): deriving the event schedule from per-turn DELTAS - this rung's method -
  is provably LOSSY about the op stream. On the m289 run the curve admits a 7-op schedule while
  the op log carries 9 (one turn hides a net-zero +1/-1 pair) and a curve-derived schedule hits
  only 7/9 recorded (kind, pre-cnt) rows (`evidence/b21_composedrun.txt:52-53,74`). The curve
  remains the right parity target for the COUNT; for OPS use the log (B13/B21).
- Command: `python3 -m sim.selftest --b10 programs/saves/m54b_clean.SAV` ->
  `PASS B10: 18/18 gates` (evidence/b10_basefound.txt); `python3 -m sim.basefound` CLI
  exit 0. B8/B9 regressions green. Box untouched.

