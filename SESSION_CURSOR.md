M112 ACCEPTANCE attempt 2 firing (tag m112p1, POKE instrument): scripts/m112_trailer_poke.py --tag m112p1 --relaunch pokes 10 dwords of 0xCAFEBABE into the 5 trailer rows of m54b_clean (40 B changed, size unchanged, magic absent from the file), loads it, scans /proc/<pid>/mem.
PREDICT: hits>0 = trailer CONSUMED; hits=0 + HUD 67/18 = NOT consumed; load refused = VALIDATED. Not merged (PR #116).
Do not touch the box until m112p1 exits; then read evidence/m112p1.log VERDICT.
