M98 (milestone/m98, s153) — [fac*8380+0x94d800] = FUN_005aab70's per-faction ADVANCE-THRESHOLD
cache (accumulator sibling [fac*8380+0x94d7f8]; grant iff threshold <= acc; writers 0x5aaf67
-1, 0x5aaf79 store in FUN_005aadf0, 0x59f0c7 -1 in FUN_0059ec90).
m98budget2 FAIL 9/11 (instrument: wp pc = store+length; SIGINT noise unparsed).
m98budget3 FAIL 10/11: 11/11 stores == model, only-static writers, threshold law, triples;
G7 only because fac1/fac2 recomputed AFTER gdb detached (offline: 7/7 live fields == model).
NEXT: python3 scripts/m98_advance_budget.py --tag m98budget4 --boundaries 2 (settle-wait).
Merged? no. Box r60, fields -1,128,151,112,212,128,144,101.
