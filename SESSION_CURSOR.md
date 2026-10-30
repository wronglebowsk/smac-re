M109 attempt 3 IN FLIGHT (m109g2), NOT ACCEPTED — branch milestone/m109 (committed bf4b721); main aad8267.
CMD: setsid env M54A_LOAD_TIMEOUT=900 python3 scripts/m109_leg_gates.py --tag m109g2 --relaunch
(5 bps: FUN_00596850 ENTER = the FILE*; the 4 read wrappers 0x596470/596540/64c9a0/64cc00 -> ra,ptr,
size,count,stream). m109g1 FAIL 1/6 was NOT the map: the driver's 220 s budget expired at the CDROM
screen, so FUN_00596850 was NEVER ENTERED (0 ENTER events, header fields still 0).
Result file when it ends: scratch/m109g2.out + evidence/m109g2.log. If PASS: gate.py --base main -> submit -> merge.
