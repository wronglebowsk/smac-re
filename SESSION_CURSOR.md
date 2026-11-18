M315 MERGED (#301, main 0ad96af) - pick (ii) CLOSED: ds:0x68cbb4 is the REFRESH
MEMO of the selection pair call 0x4e8d60 + call 0x4e78e0. The 22 stores split
two independent ways that COINCIDE: by PROVENANCE (12 fed by the current index
or a caller [ebp] slot vs 10 fed by -1) and by ADJACENCY (the same 12 followed
by the pair within 5..17 B vs the 10 clears with no call to either callee in the
next 60 instructions). M311's "19 writers unexplained" closes as 10 clears + 9
memo updates; its window was FORWARD 0..+32 B (m311_recidx.py:449), not
symmetric. 10/10 gates, digest 3976ca97eedc1e19 (x2 identical), 29/29 mutants
(22 expectation + 7 CODE mutants via M315_PATCH). Greptile round 1: 6 P2, ALL
accepted at review head 754b4fa6 - the "callers enforce the dedup" claim was
DOWNGRADED to OPEN, and the pair reach moved 16 B -> 17 B (at 0x4f5ab7).
NAMED ## M315 + Session 284 govern. track_mode: MODE=ANALYSE,
analyse_since_build=2, next_rung=B24. NEXT FIRE = pick (iii) GOAL game-meaning /
one-char tokens / negative priority; (iv) NAME the refresh pair (0x4e8d60,
0x4e78e0); (v) who guards the 8 UNGUARDED memo sites. Fires MANUAL (cron paused
2026-11-18).
