M315 MERGED (#301, main 0ad96af): pick (ii) CLOSED (pick (ii) CLOSED): ds:0x68cbb4 = the
REFRESH MEMO of call 0x4e8d60 + call 0x4e78e0 (22 stores partition exactly
into 10 -1-sentinel clears + 12 memo updates, 8 fed by ds:0x68cbb0, 4 by a
caller slot; local dedup guard at only 4/12). 10/10 gates, digest
3976ca97eedc1e19 (x2 identical), 29/29 mutants (22 expectation + 7 code via
M315_PATCH). Greptile round 1: 6 P2, ALL accepted and fixed at review head.
M311's "19 writers unexplained" closed; its window was FORWARD 0..+32 B
(m311_recidx.py:449), not symmetric. STATUS: MERGED, CI gate pass 15 s on the review head 754b4fa6; 6 P2 all
accepted at review head (single accounting comment). track_mode: MODE=ANALYSE,
analyse_since_build=2, next_rung=B24. NAMED ## M315 +
Session 284 govern. track_mode: MODE=ANALYSE (since_build=1, B24 queued).
NEXT FIRE = ANALYSE pick (iii) GOAL game-meaning / one-char tokens / negative
priority; (iv) NAME the refresh pair (0x4e8d60, 0x4e78e0); (v) who guards the 8
UNGUARDED memo sites (the caller-side claim is OPEN, not measured). Fires
MANUAL (cron paused 2026-11-18).
