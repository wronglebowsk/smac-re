S193 M242 (gate green, submitting). `sudo -n python3 scripts/m242_save_write.py` -> `PASS M242: 5/5
gates` (2nd invocation; 1st died in tally() post-measurement) -> evidence/m242_save_write.txt.
FINDING: the save WRITE function is FUN_00597ce0(path) — fopen + TERRAN magic + version 0x56 + body +
fclose (FUN_0064d710 deletes on failure) -> FUN_00596850(handle, 1), ONE codec both ways (mode =
DAT_00926a0c): 23/30 write legs hot, 0/28 read, 796-B DAT_00985ab8 verbatim at file offset 12. UI save
via 0x598c73. Box clean (TracerPid 0). #180 open. NEXT: `track_mode.py` (BUILD rung B2 = save load).
