M106 RUNNING (cron, milestone/m106): the invisible load-window restore.
acceptance: m106r4 RUNNING (scripts/m106_load_restore.py --tag m106r4, stdout -> scratch/m106r4.out).
vs r3 (FAIL 11/15): G13 now finds the .SAV fd by the BYTE-SUM LAW (sequential read() returns total == 242539 B;
the fd arrives over SCM_RIGHTS so there is no open()); coincidental region overlaps excluded; G6 uses
WFACS [1,3,6]; driver budget M54A_LOAD_TIMEOUT=1200.
merged: NO | next: tail -25 scratch/m106r4.out
