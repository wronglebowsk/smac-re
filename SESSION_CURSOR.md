# SESSION_CURSOR

B25 MERGED (#319 -> main 1556ce9; 10 review findings, all accepted). `python3 -u -m
sim.selftest --b25` -> `PASS B25: 9/9 gates`, ACCEPT anchor 901a286332960a10 PINNED by G9
(`b25_selftest.txt:59`, banner `:69`); harness `scripts/b25_mutate.py` -> **13/13 + 3 NO-OP**
(`b25_mutate.txt:20`), `--selftest` **5/5** (`:11`). Law: **byte-level carry** (table H); the
CONTAINER (64x64) owns the mover's modulus, not `planet.MP` (80x80) - NAMED §B7 corrected;
the decoder coord-checks **42 of 67** records (25 carry +10 >= 64) -> pick (vii). NEXT: B26
(spine NOT authored) or pick (vi)/(vii). #180 stands.
