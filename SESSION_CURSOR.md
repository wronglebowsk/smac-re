S199 B3 submitted (branch milestone/b3). `python3 -m sim.selftest --replay
evidence/m30_turn_trace.jsonl` -> `PASS B3: 6/6 gates`, `matched=67/67` (ONE invocation,
rc=0, 22.3 s) -> evidence/b3_turn_replay.txt. sim/turn.py implements M30's engine: the walk
is ASCENDING over 8 slots (human 3), the year fires on the 7->0 edge while cur is still 7,
and tf clears ONE STEP AFTER cur is written to 3; 48 of 322560 candidate models reproduce
the trace and all 48 agree on those edges. Box untouched: no /proc, no gdb.
NEXT: python3 scripts/track_mode.py (BUILD -> B4 economy; ANALYSE -> a NEXT_PROMPT pick).