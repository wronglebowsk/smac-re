# SESSION_CURSOR

B27 `milestone/b27` -> PR (this fire): 10/10 gates, harness 16/16; review triage, then merge.
ACCEPT `python3 -u -m sim.selftest --b27` -> `PASS B27: 10/10 gates` `evidence/b27_selftest.txt:77`
(anchor `b65e8129b67ba67d` `:54`, 2 runs identical); harness `python3 -u scripts/b27_mutate.py`
-> `HARNESS PASS 16/16` digest `81d2d9491ec3320d` `evidence/b27_mutate.txt:18-20`; `--selftest`
3/3 `b27_mutate_selftest.txt:1-3`.
NEXT FIRE: pick from the (x) OPEN-LEADS list in `NEXT_PROMPT.md` §THE PICK. `m294_gate_rows_raw.txt` = sim parity target, do NOT rm.
