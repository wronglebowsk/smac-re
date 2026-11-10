# Session notes archive — sessions 212-212

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 212 (2026-11-05, BUILD fire, B6 PASS 6/6) - the headless run: R1 is DONE
- `track_mode.py` said MODE=BUILD next_rung=B6; built it per `BUILD_SPINE.md` (no box time, no /proc, no gdb).
- NEW `sim/headless.py`: loads a .SAV (sim/save) + .MP (sim/map) + alpha rules (sim/rules), presses the B3
  engine (sim/turn) N times, runs the B4 economy (sim/economy) per base-owning faction per round, and dumps
  a canonical `smac-sim-state/1` JSON (sort_keys, fixed separators - that is what makes the sha stable).
- ACCEPTANCE (both shapes, same numbers): `python3 -m sim.headless --sav programs/saves/m54b_clean.SAV
  --map programs/maps/planet.MP --turns 10 --dump sim_state.json` -> exit 0, `PASS B6 ... year 2150 -> 2160
  ... sha256 2efbc782e2075a26`; `python3 -m sim.selftest --b6 <sav> <map> --turns 10` -> **PASS B6: 6/6
  gates** (`evidence/b6_headless.txt`). Two runs -> byte-identical dump (8,455 B).
- Gates: year delta == turns (B3 edge), ends (cur,tf)=(3,0), economy every round for all 7 owners,
  energy floor 0, two-runs-identical-sha256, command-exit-0.
- Declared ASSUMED (in the dump, not hidden): initial faction energy 0 (no pinned .SAV read); units
  re-charge 6 MP and never move (R1 has no AI); ledger 0 (the idle shape B4 verified).
- The ladder B1..B6 is EXHAUSTED: a BUILD fire must now write rung B7 (R2's first slice) into
  `BUILD_SPINE.md` before building. `MILESTONES.md` R1 -> DONE.
