M78 | acceptance m78order3 PASS (g1-g9 all True) | merged? no (closing now) | in flight: none
| finding: the 0x100 mark (0x5729d5) and its clear (0x4ef398) are in ONE production visit; the
boundary census that reads 0x105 is a MID-VISIT snapshot (it sits between the two stores of visit
36). No cross-visit pair, no other marker. Sweep callers live: 0x4efe83 (production, 1) and
0x574203 (FUN_00573a90, 4, indices >= 256, marked nothing).
| next: milestone.py submit -> gh pr checks <n> -> milestone.py merge <n> (branch milestone/m78).
