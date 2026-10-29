M99 RUNNING: scripts/m99_param2.py --tag m99p1 --boundaries 2 (gdb: 4 hw watchpoints on
[fac*8380+0x94d7f8] facs 2,3,5,6 + 11 silent bps at FUN_004f34b0 0x4f34df/51c/558/566/5b8/5c9,
FUN_005aadf0 entry 0x5aadf0, acc store 0x5aaee1/5aaef1, second add 0x5aaf1b, reset 0x5aaf5c;
poke fac2 mult -5 before each boundary). Static: EXACTLY ONE call to 0x5aadf0 in .text,
0x4f35cb inside FUN_004f34b0. Branch milestone/m99. Not merged.
Next: tail evidence/m99p1.gdblog + the ACCEPTANCE line; PASS -> closing order; FAIL -> fix the
INSTRUMENT (never the floor) and re-run. Box m54b_clean r62; accept_ready BLOCKED (minerals 0 <
price 9, credit 0) - M99 gates need round movement + upkeep, not a completion.
