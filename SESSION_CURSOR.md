B24 CLOSED OUT s287 (milestone/b24, main a190079). Acceptance:
`python3 -u -m sim.selftest --b24` -> `PASS B24: 9/9 gates` (stdout ==
committed evidence/b24_selftest.txt); `python3 -u
scripts/b24_mutate.py` -> `8/8 mutations matched their declared effect`
exit 0 (evidence/b24_mutate.txt:11). Harness: MU4/MU7 re-declared to
MEASURED wide sets; MU8 `pos=False` was the WRONG mutant (Korolev
locator fallback) - tile law = `mode="locate"`, now EXPECTED_CRASH on
"tile (27, 29) not located". NEXT: merge green+review -> flips ANALYSE
-> (iii') FUN_00556690. BUILD_SPINE ends at B24. #180 CONFLICT.
