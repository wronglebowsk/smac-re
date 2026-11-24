# SESSION CURSOR — s320-chain1 / M340
ID: M340 (STATIC) — FUN_0058e7f0 ADMITS a `Difficulty` pref >=6: no bound in the
read->parse->store chain; index 6 -> `0x94d2c4`, one dword past the six-row ladder.
ACCEPT: `python3 -u scripts/m340_pref_admission.py` -> `PASS M340: 7/7`
rows `277483c12bd5cc44` (`evidence/m340_pref_admission.txt:60-71`); harness 9/9
`b25e0bc3a09693f5` (`evidence/m340_mutate.txt:13`).
MERGED? branch `milestone/m340`.
NEXT: ANALYSIS — 0x94d2c4's runtime dword is box-GATED; static: 0x92bde8..0x92bf14
co-writers. M332 rotated -> `docs/named-archive-m340-rows.md:5`.
