M319 on milestone/m319, unsubmitted (s293).
ACCEPT: `python3 -u scripts/m319_guard_hoist.py` -> `== M319: 7/7 ==`,
digest 459f47e3178f439d (evidence/m319_guard_hoist.txt:72; 3rd identical
run); `m319_mutate.py` -> 12/12 scored + 1/1 NO-OP (:15); `--selftest`
3/3 (mutate_selftest.txt:4).
FINDING: the memo dedup guard is NOT hoisted into the callers of the 8
unguarded sites - pick (v) CLOSED.
NEXT: gate -> review_lint -> submit -> ai_review -> triage in ONE reply
-> merge only on green. Then pick (vi): NAME FUN_004ee410 + FUN_004f41f0
(M319's unnamed owners). #180 stands. B25 spine unauthored.
