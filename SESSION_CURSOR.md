M107 merged (#114), M108 merged (#115, main aad8267). Branch milestone/m109 (from main aad8267).
M109 IN FLIGHT: python3 scripts/m109_leg_sizes.py --tag m109l1 --relaunch (bg pid 1383390) — 6 silent bps on the 5 COUNTED legs (0x597319/0x59738b/0x59751f/0x5970e4/0x5979f8) + the malloc (0x596ab7), then one m54b_clean load; gates: sizes == model from live counts, and immediates 204,504 + counted == 242,539 (closure).
next: read evidence/m109l1.log + scratch/m109l1.gdblog; if the closure fails, the numbers ARE the deliverable.
cron 1a88e12bd408 PAUSED 18:41 (single driver) - resume when this session ends.
