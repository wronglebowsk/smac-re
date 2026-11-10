# Session notes archive — sessions 226-226

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 226 (2026-11-10, BUILD, B10 PASS 18/18) - the M282 founder/destroyer leg is BUILT: sim/basefound.py recovers the recorded 18->26 n_bases curve and a founded save image round-trips
- track_mode printed BUILD (analyse_since_build=3, next_rung=B10) -> wrote the B10 rung into
  BUILD_SPINE.md FIRST, then built it. ZERO box time; box untouched (pgrep only, per kickoff).
  `python3 -m sim.selftest --b10 programs/saves/m54b_clean.SAV` -> **PASS B10: 18/18 gates**
  (`evidence/b10_basefound.txt`); B8 10/10 and B9 7/7 regressions GREEN after the savewriter
  change (checkpoint fa4b0a7).
- BUILT: `sim/basefound.py` (Ledger = founder FUN_004e47d0 + destroyer FUN_004e4e10 +
  events-from-trace pairing; CLI --sav --trace --out) and a savewriter grown-ledger path
  (`bases_override`/`orig_n_bases`): records below the original count stay byte-identical,
  new records compose as zero + x/y/faction, the tail re-anchors after the ORIGINAL count,
  and the modeled header writes the GROWN count - the only prefix byte that changes.
- THE LEG: founder (M282: guard count<0x200, append at old_count*0x130, x u16 +0, y +2,
  faction +4/+5, count+1) and destroyer (count-1 @4e515d + COMPACTION: LAST record into the
  freed slot). The pairing presses the B3 engine the trace's own 40 turns and applies the
  trace's OWN 8 derived deltas (t8 +1, t9 +1, t17 +1, t22 +2, t23 -1, t27 +1, t32 +2, t34 +1)
  through the leg: recorded 18->26 recovered on ALL 40 turn snapshots (the B9 declared
  frontier is now MODELED), and the t23 -1 runs through the DESTROYER - the recorded run
  really destroyed a base (23->22) mid-window.
- LAWS proven: the 0x200 guard refuses a 513th founding; destroy(k) moves the LAST record
  into k (record equality - the m46e "array reorders" law as code); write-through of a
  founded image is byte-exact except the bases-count dword; the image re-parses (n_bases 19,
  record 18 read back; its zero name makes it shape-invisible: found 18, DECLARED - the real
  game names bases later); a flooded 512-cap image keeps its tail byte-identical;
  determinism (sha256 d8ce1f17).
- RIVALS: no-leg (B9) shape keeps 18 -> 32 divergences; all-events-on-turn-0 diverges at t0;
  both fail the same curve.
- FOUND (pre-existing, NEW OPEN): decode_save --sections hardcodes the 80x80 map-trailer
  count offset and FAILS rc=1 on every 64x64 save ("no 52/304 split of a 0-byte region" -
  on m54b_clean itself); B8's sec() equality never noticed because both sides fail
  identically. Small follow-up: read the count at the 64x64-correct offset.
- ASSUMED (declared in the dump): founding FACTION (fewest-bases AI faction) and COORDS
  (first unoccupied in-bounds tile) - the golden trace records n_bases only; which founder
  vector the recorded AI used per event stays the OPEN box question (M282 G5).
- OPEN: box pick (dialog +0x4c dispatcher, box UP m54b_clean); the 64x64 odd-Rw accessor
  quirk; decode_save's 64x64 section walk. Next fire: ANALYSE (cadence reset by merged B10).
