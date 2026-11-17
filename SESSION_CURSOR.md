B22 GREEN on `milestone/b22` (commit 501a3be, NOT YET SUBMITTED). ACCEPT CONFIRMED:
`python3 -m sim.selftest --b22 programs/saves/m54b_clean.SAV` -> PASS B22: 11/11;
`python3 -u -m sim.composedgrowth` -> same 11 labels, two runs byte-identical
(report digest a7ec6d38ba67cbe9, written image sha256 f7d90eb77ca7abac);
`evidence/b22_composedgrowth.txt` verified equal to a fresh rerun.

NEXT FOR THIS FIRE (in order, budget-tight - commit before anything else):
1. `python3 scripts/gate.py --base main` -> pass; `python3 scripts/milestone.py submit`;
   then WAIT for Greptile on the new PR and READ every inline comment before merging
   (`gh api repos/wronglebowsk/smac-re/pulls/<N>/comments`) - s272 lost a round to two of my
   own false claims, and a gate must pin every instruction/band it NAMES.
2. `python3 scripts/milestone.py merge <N>` (main rejects direct pushes).
3. Cursor handoff commit to main via a PR (`milestone.py start <label>`), then author **B23**:
   the queue's PER-TURN progress composed through the WRITER (B11's law exercised in the written
   container, not in memory). Rung text goes in BUILD_SPINE.md first, module second.

Laws this fire re-earned: (a) never assert a lift/shift amount for a grown container - print the
band map; (b) `--b22`-style hooks must RELAY the module's claims, never re-author them, and after
adding a function to a module GREP for a duplicate `def` of the same name (the later one wins and
the test stays green on the wrong path); (c) a claim about what a locator does is a claim about
bytes - measure its `found_*` count, do not assume it equals the header count.
