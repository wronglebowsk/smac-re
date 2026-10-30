M112 attempt 1 (m112a1) SPENT: --filter-file armed (savefile=0x6a79a0), 83 legs, 0 gdb errors, counts 68/19, sum 243,071 vs autosave 242,927 = OVER 144 (no site/dest repeat). m111b3 was +468. Byte sums cannot decide it — 1 attempt left of 3.
BOX: terran.exe 1878861, m112auto1 loaded (68/19), TracerPid 0 (gdb 1878864 left attached again, killed by pid). NOT merged, PR #116.
next: copy a save, poke a unique dword pattern into its last 156 B, load, scan /proc/<pid>/mem for the pattern (present = trailer consumed).
