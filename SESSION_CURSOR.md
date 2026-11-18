M311 WIP, branch milestone/m311, NOT submitted. Instrument now 8/8 green
(`python3 -u scripts/m311_recidx.py`, digest 625cd5877271cd85) - but docs still say 7/7 (NAMED,
Session 274) and evidence/m311_recidx.txt is the 7-gate run. The mutation harness is STALE:
9/14 (MU3+MU5 crash -> correctly rejected; MU4/MU13/MU14 weak). NEXT FIRE in order: (1) re-anchor
MU3/MU5 to the moved constants and re-scope MU4/MU13/MU14 onto gate A8, which pins fold_chain per
site (MATCH_TRUTH: 5 of 6 index stores fold; 0x4f5c36 reuses the SAVED pointer from [ebp-0x8] via
0x4f5c33); (2) retarget every harness anchor by READING the current source, not from memory;
(3) update NAMED + notes to 8/8, copy the green run to evidence, re-resolve all citations;
(4) only then gate -> submit -> read every Greptile inline -> merge. Zero box time.
