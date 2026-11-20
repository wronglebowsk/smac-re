# SESSION_CURSOR

B27 `milestone/b27` -> PR #344: 10 review findings fixed on top of 10/10 + 17/17; merge on CI.
ACCEPT `python3 -u -m sim.selftest --b27` -> `PASS B27: 10/10 gates` `evidence/b27_selftest.txt:79`; anchors rows/printed/container `b65e8129b67ba67d` `3c134ea70638c12b` `626fec9a35deddba` (`:56`).
HARNESS `python3 -u scripts/b27_mutate.py` -> `PASS 17/17` digest `181d99d9ac000044` + `exact-set check: 0 complaints` (`b27_mutate.txt:20-22`); `--selftest` 4/4.
NEXT FIRE: the (x) OPEN-LEADS list in `NEXT_PROMPT.md`. `m294_gate_rows_raw.txt` = sim parity target, do NOT rm.
