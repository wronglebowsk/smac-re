M315 SUBMITTED as #301 on milestone/m315 (pick (ii) CLOSED): ds:0x68cbb4 = the
REFRESH MEMO of call 0x4e8d60 + call 0x4e78e0 (22 stores partition exactly
into 10 -1-sentinel clears + 12 memo updates, 8 fed by ds:0x68cbb0, 4 by a
caller slot; local dedup guard at only 4/12). 9/9 gates, digest
c2b025b32280d82b (x2 identical), 19/19 mutants on declared gate SETS.
M311's "19 writers unexplained" closed; its window was FORWARD 0..+32 B
(m311_recidx.py:449), not symmetric. STATUS: awaiting CI + Greptile on the PR
- do NOT merge until gate.py is GREEN on the review head. NAMED ## M315 +
Session 284 govern. track_mode: MODE=ANALYSE (since_build=1, B24 queued).
NEXT FIRE = ANALYSE pick (iii) (GOAL game-meaning / one-char tokens / negative
priority) or the new pick: NAME the refresh pair (0x4e8d60, 0x4e78e0). Fires
MANUAL (cron paused 2026-11-18).
