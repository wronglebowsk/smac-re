# SESSION_CURSOR

B26 PR #328, landing. Accept `python3 -u -m sim.selftest --b26` -> `PASS B26: 10/10 gates`
(`b26_selftest.txt:63`; anchor ae43e0ab9c8cfc3d `:52`). Harness `python3 -u
scripts/b26_mutate.py` -> **19/19 + 1 declared NO-OP** (`b26_mutate.txt:24`) + ENTRY-POINT
IDENTITY 2/2 scored by MU21 (`:25-30`); `--selftest` 8/8 (`:14`).
Merged? NOT YET — pushed this fire; merge only on a real CI PASS. DOC DEBT: NAMED 246,259 B
vs the 250,000 FAIL line — rotate before adding (§B26 rows -> `docs/named-archive-b26-rows.md`).
Then picks (vii)/(viii); B27 UNAUTHORED. #180 stands.
