M319 on milestone/m319, PR #317: review triaged, re-measured at head.
ACCEPT: `python3 -u scripts/m319_guard_hoist.py` -> `== M319: 7/7 ==`, digest
fb4e802dac1995a2 at m319_guard_hoist.txt:73 (3 runs identical, sha 38a624606a13cfe9); `m319_mutate.py` -> 14/14 scored + 1/1 NO-OP (:17);
`--selftest` 4/4 (mutate_selftest.txt:5).
FINDING: the dedup guard is NOT hoisted into the callers of the 8 unguarded
sites - pick (v) CLOSED.
NEXT: poll `gh pr checks 317`, then `milestone.py merge 317` on green. Then pick
(vi): NAME FUN_004ee410 + FUN_004f41f0. #180 stands.
