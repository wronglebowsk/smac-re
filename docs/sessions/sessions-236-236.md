# Session notes archive — sessions 236-236

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 236 (2026-11-10, ANALYSE, M290 9/9, no box time) - the hub's FOUNDING DECISION fitted to the m289 record: the dispatch is OWN-TILE-GATED (a distant target takes the 0x2408 auto-build message and can NEVER found); founder args are the POD RECORD's owner@+14/y@+10/x@+8, so the tile choice is entirely the pod's walk; B10's first-unoccupied rule REFUTED (recorded ranks 542-1691 of 2146)
- track_mode ANALYSE -> the s235 frontier pick: fit the hub founder decision
  to the m289 record, static+model, no box.  scripts/m290_hub_decision.py,
  9 byte-level/fit gates.  ACCEPTANCE: python3 scripts/m290_hub_decision.py
  programs/saves/m54b_clean.SAV evidence/m289_gdb_raw.log
  evidence/trace_m289_20261110_071759.jsonl -> PASS M290: 9/9 (3rd
  invocation; runs 1-2 were instrument bugs, floors never weakened).
- MEASURED (bytes are the arbiter): hub dispatch 0x563d3c-0x563d8b - cmp
  [ebp-0x44],8 (settle case), test esi,esi / jne 0x563dfa: esi = the scan's
  CHOSEN target offset, ZERO = the unit's own tile -> 0x563d86 call
  FUN_004cca50; nonzero -> 0x563d4e leg push 0x2408 + call FUN_00583fa0
  ("Auto-sending BUILD BASE message") and NO founder call.  Vector
  prologue 0x4cca57-0x4cca74 folds 52*u then loads cl=owner[+14],
  eax=y[+10], edi=x[+8]; 0x4ccbda-dc push edx/edi/esi, 0x4ccbdd call
  founder - the FOUND ret=0x4ccbe2 of all 7 recorded foundings.  Founder
  FUN_004e47d0: capacity guard ONLY (count<0x200), no tile-legality bail.
- FIT to the 7 sites: ALL land (cat 3-6 via the 44-B RECORD view:
  rec=(W/2)*y+(x>>1), byte 0 of the record's first half) AND none already
  a base tile; ledger FOUND cnt=18,19,20,20,21,22,23 + 2 DESTROY rows
  (between F3/F4 and after F7) replay to endpoint 23 with peak 24,
  matching the jsonl per-turn curve (same-turn found+destroy nets are
  invisible per-turn - the M289 +3->20 accounting).
- RIVAL REFUTED: sim/basefound.py:118 "ASSUMED: first in-bounds tile no
  base occupies (row-major)" - the recorded sites rank 542-1691 of 2146
  unoccupied-land tiles in that order (mean 1202): B10's TILE rule explains
  NO real founding's coords (its record/curve machinery stays valid; only
  the (x,y) choice was a placeholder).
- NEW TRAP (fired on run 1): the save's 22-B COLUMN view (sim/save.py
  tile()[0]) does NOT reproduce the live byte-0 category - 5/7 legal sites
  misread cat 0.  Read the 44-B record view instead (record =
  grid_off + 44*((W/2)*y + (x>>1)), byte 0 = the live category).
- OPEN (unchanged): why the 5a0aa0 chain bailed 3x; M247; M70 x2.  NEW
  OPEN: which pod the hub picks and the walk TARGET (the scan's score
  law at 0x563c00-0x563d40, (dist*10000)/(value+1) shape) vs the recorded
  founding TURNS - the decision is now reduced to POD MOVEMENT.
  Next: ANALYSE - the pod-walk target rule.
