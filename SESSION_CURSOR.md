# SESSION_CURSOR

M327 (pick vii) ACCEPTS; s304's 2 lint blockers + PR #337's review (3 P1, 5 P2) ALL FIXED.
`python3 -u scripts/m327_typeband_census.py` -> `== M327: 11/11 ==`
(`evidence/m327_typeband_census.txt:771`; PIN RE-MEASURED `91f58f3de03090c1` `:769` because
T4's row changed; 2 runs byte-identical). `python3 -u scripts/m327_mutate.py` ->
`HARNESS PASS 24/24` (`evidence/m327_mutate.txt:29`; MU23={G3,G10}, MU24={G3,G5,G6,G10}).
review_lint PASS, gate GREEN. NEXT: pick (viii) `FUN_0041a8f0` or the B27 spine.
NAMED 247,028/250k — ROTATE BEFORE ADDING A BLOCK.
