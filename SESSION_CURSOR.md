S189 M235-M237 MERGED #176: acceptance = `sudo -n python3 scripts/m235_m237_records.py > evidence/m235_m237_records.txt`
-> `SUMMARY M235/M236/M237: 12/12 gates PASS`, rc 0, 7,433 B (runs #1-#6 were instrument bugs - objdump line shape,
absolute-operand blind spot, pairwise gaps, cluster cursor; no threshold or claim direction weakened). Static +
read-only /proc; box untouched (terran.exe 319926 TracerPid 0). M181 STILL a LEAD, box time owed. Next:
`python3 scripts/track_mode.py` -> 0x679f98's 15 unique slots, or FUN_005be090's 13 [reg+4] callers + ds:0x9965b8's
3 loaders, or M181's falsifier (box; trigger = the 4 callers of FUN_0041a8f0).
