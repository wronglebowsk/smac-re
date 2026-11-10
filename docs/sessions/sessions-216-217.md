# Session notes archive — sessions 216-217

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 216 (2026-11-05, BUILD fire, B7 PASS 6/6) - the move slice: R2's move leg is now executable headless
- `track_mode` said MODE=BUILD next_rung=B7 and the ladder was EXHAUSTED - so this fire first WROTE
  the rung into `BUILD_SPINE.md` (move slice: save-loaded units + the M27 gesture + B3/B4/B5/B6
  machinery; parity on GESTURE SEMANTICS because the trace's units 117-120 are not in m54b_clean's
  67-unit array - stated in the rung and the dump, not hidden), then built it.
- NEW `sim/movesim.py` (schema `smac-sim-move/1`). ACCEPTANCE: `python3 -m sim.selftest --b7
  programs/saves/m54b_clean.SAV programs/maps/planet.MP --turns 5` -> **PASS B7: 6/6 gates**
  (`evidence/b7_moveslice.txt`): 67 units, 5 rounds x 3 east presses = **670 accepted / 335
  refused**, every unit exhausts at 2 (6 MP / 3), all accepted deltas == the trace's (+2,0) with
  x wrapped by 80; year 2150 -> 2155 per B3; two runs byte-identical (67,790 B, sha256
  3b62847494b252ad). Direct run `python3 -m sim.movesim --sav ... --turns 5` exits 0, same sha.
- ASSUMED (declared): save-LOAD position restore not modeled (kernel write, M106); gesture applied
  to every unit; uniform 3 MP cost.
- R2 in `MILESTONES.md` todo -> IN PROGRESS (move leg done; new-game + save-write legs todo).
  Next BUILD rung B8: the save WRITE leg (produce a .SAV-shaped image from sim state) or the
  new-game leg - the BUILD fire writes the rung first.

## Session 217 (2026-11-10, ANALYSE static pick, M276 PASS 8/8) - the fold's coefficient IS the faction stride; M275's "irreconcilable" was a midpoint slice

- PICK: M275's queued resolution - who writes the row slot [ebp-0x18] if the fold's `130*arg`
  cannot make M273's live 8380-cursor? Answered STATICALLY, one census, ZERO box time.
- FINDING: `scripts/m276_fold_stride.py` evaluates the chain 0x557ffd-0x558038 symbolically
  (linear forms over two atoms; the 20-insn window writes neither): **esi = 8380*edi + 2*ecx**.
  `mov eax,edi; shl 6; add eax,edi` (65) is only the first third - `lea eax,[edi+eax*2]` (131),
  `shl eax,4; sub eax,edi` (2095), `lea esi,[ecx+eax*2]; shl esi,1` finish it. 2095 dwords x 4
  = 8380 = the per-faction block stride the field atlas already records, so the auto-manager
  indexes these arrays by faction block by construction.
- LIVE FIT: M273's recorded UNSCALED rows replayed offline satisfy `slot = 2*s10 + 8380*cp`
  for **7/7** events (cp = cur_player 1..7; deltas whole 8380, -50280 = -6*8380 at the
  round-52->53 wrap). The rival published coefficients 130 and 188 fit **0/7** each - the
  gate's discriminator.
- INSTRUMENT: `m275_rowslot_defuse.py` G6 hand-wrote `2*(64+1)==130`. G6/G7/G8 now import this
  evaluator, assert (8380,2,0), carry the correction in prose and mark the queued frame-slot
  hw-watchpoint pick CLOSED UNRUNNED; m275 re-runs **8/8**.
- ACCEPTANCE: `python3 scripts/m276_fold_stride.py` -> `ACCEPTANCE M276 PASS 8/8`
  (`evidence/m276_fold.txt`, which also holds the m275 re-run). Registry: `NAMED.md` M276 plus
  correction rows patched IN PLACE inside M274/M275 (not only here).
- OPEN LEAD (new, from the bytes read for this census): the SCALED site 0x5584aa indexes
  0x94eaa8 by `edi*2` with NO faction term while the UNSCALED 0x558452 indexes the same base by
  the fold value WITH 8380*arg - whose row does each own, and does M274's "regions 94..127 spill
  into the sibling verdict array 0x94eba8" survive for the unfactioned one? (static pick)
- LAW -> skill `references/instrument-laws.md`: evaluate a multiplier chain. A hand-written
  expression at a `lea`/`shl`/`sub` chain's midpoint published a coefficient 64x too small and
  manufactured a static-vs-live contradiction that queued a box milestone.
