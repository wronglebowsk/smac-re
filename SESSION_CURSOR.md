M311 READY TO MERGE, branch milestone/m311, PR about to open. ACCEPT:
`python3 -u scripts/m311_recidx.py` -> PASS M311: 8/8, digest 625cd5877271cd85, two runs identical;
`python3 -u scripts/m311_mutate.py` -> 11/11 load-bearing (baseline-green precondition).
FINDING: 0x68cbb0 = CURRENT-RECORD INDEX of the 304-B array at 0x95da10; 0x8f0d60 its derived
POINTER (6+6 stores, paired 1:1 at +6..25 B). 5 of 6 sites recompute base+304n; 0x4f5c36 reuses a
SAVED pointer from [ebp-0x8]. Picks (a)+(b) are ONE object: 0x95da40 = 0x95da10+48 (0x4f5aab).
A8 RETRACTS my claim that register-discipline/proximity were load-bearing (register-blind matcher is
byte-identical at all 6 sites). NAMED + Session 274 updated, 17 citations resolved, evidence = green run.
NEXT: submit -> read every Greptile inline -> merge -> cursor handoff; track says ANALYSE, B23 queued.
