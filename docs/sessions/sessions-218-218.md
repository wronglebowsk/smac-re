# Session notes archive — sessions 218-218

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 218 (2026-11-10, ANALYSE static, M277 PASS 6/6) - the two read sites of 0x94eaa8 own different rows; M274's spill landing is refuted by its own max
- Picked the M276 NEW LEAD (static, zero box time): scaled 0x5584aa vs unscaled 0x558452.
  `python3 scripts/m277_scaled_row_ownership.py` -> **SUMMARY M277: 6/6 gates PASS**
  (`evidence/m277_scaled_row.txt`). Imports m276's evaluator; does NOT re-derive the fold.
- ANSWERS: (G1) the two sites are fed by DIFFERENT frame slots - 0x55844b `edi=[ebp-0x18]`
  (the fold) vs 0x5584a5 `edi=[ebp-0x10]` (the region counter). (G5 live replay 7/7:
  2*edi stays in block 0 while s18 walks blocks 1..7 with cp.)
  UNSCALED = block arg's row (arg = the faction function argument); SCALED = the image's
  ONLY +0x94eaa8 referrer with no block term = the permanent **faction-0 (block 0) view**
  of the same row array. (G6) the only two WRITERS image-wide (0x51df61 `inc`, 0x564ab1
  `add -10`) both evaluate to eax = 8380*block + 2*slot, so the row is per-faction live data.
- RETRACTION (M274 G2): claimed regions 94..127 read the sibling verdict array at 0x94eba8,
  band [0..66] = offsets 256..322. The loop's body domain is 1..127 (G3: init 1, one in-loop
  store 0x558b22, tail inc-then-cmp 0x80) so the last byte touched is +255 - **never the
  sibling**. The spill is 68 B of rows 94..127 inside the row's OWN cell. Survives: G1
  single bound, G4 verdict skip, G5 verdict stores (a different array, 0x94eda8).
- OPEN: block 0 vs "no faction" - is block 0 the player/neutral slot or faction 0's real row?
  (static: read the two writers' block index source). Also 0x94e8a8 is written by 0x51df3d
  with the SAME fold shape - the row family is wider than 0x94eaa8.
