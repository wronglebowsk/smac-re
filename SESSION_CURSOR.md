# SESSION_CURSOR

B25 IN REVIEW (milestone/b25, #319 triaged): `python3 -u -m sim.selftest --b25` ->
`PASS B25: 9/9 gates`, ACCEPT anchor 901a286332960a10 now PINNED by G9
(`evidence/b25_selftest.txt:59`, banner `:69`, 2 runs byte-identical, == `-m sim.composedmove`);
harness `python3 -u scripts/b25_mutate.py` -> **13/13 scored + 3 declared NO-OP**
(`evidence/b25_mutate.txt:20`); `--selftest` **5/5** (`..._selftest.txt:11`).
ANSWERED: the move leg IS persistent through the writer - the LAW is byte-level carry (table H);
the CONTAINER (m54b_clean is 64x64), not `planet.MP` (80x80), owns the mover's modulus - NAMED §B7
corrected in place; the decoder coord-checks only 42 of the 67 records (25 carry +10 >= 64).
NEXT: merge #319 on a green CI, then B26, spine text NOT authored. #180 stands.
