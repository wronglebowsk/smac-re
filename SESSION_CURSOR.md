# SESSION_CURSOR

B28 (s316-chain1, BUILD, zero box) IN PROGRESS, branch `milestone/b28` from main 497d766.
ACCEPT `python3 -u -m sim.selftest --b28` -> `PASS B28: 8/8 gates` (`evidence/b28_feeder_exec.txt:18`).
Law `sim/feeder.py`, run+gates `sim/composedfeeder.py`, spine §B28.
NAMED rotated: M246/M247/M248-M249 -> `docs/named-archive-b28-rows.md:10` (§rotation-1 sha1
`fcd4989fdf15`), `scripts/b28_named_rotate.py --verify` PASS, NAMED 245,488 B.
NEXT: `scripts/b28_mutate.py --measure` -> fill DECLARED -> HARNESS PASS; then close out.
`m294_gate_rows_raw.txt` = sim parity target, do NOT rm.
