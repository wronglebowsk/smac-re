S195 B2 OPEN (PR pending). `python3 -m sim.selftest --sav
"programs/saves/auto/m242_probe_B.SAV"` -> `PASS B2: 7/7 gates`, 17 saves close ->
evidence/b2_save_walk.txt. The .SAV walk closes on the byte: counts at file 68/72, count-prefix
u32@188,299 (176/192/208), map trailer 91 B at 64x64, tail 10,800. 93,159 = 92,927 map + 220 + 12.
Box untouched (no /proc, no gdb). NEXT: `python3 scripts/track_mode.py` (ANALYSE) — who reads the
220-B block, or the 7 mask copies at terrain-record +16..+43.
