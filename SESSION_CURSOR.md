M109 RUN, NOT ACCEPTED (m109l2 FAIL 2/5; 2 of 3 attempts used) — branch milestone/m109 committed 3ae87fd, NOT merged. main = aad8267 (M107 #114, M108 #115 merged).
MEASURED: count leg 176; 52n=3,484 (52x67); 304m=5,472 (304x18). 0x59738b (48p) never runs; 0x5979f8 is a 4-byte read. Remainder 28,899 B of 242,539 — the 30 legs are GATED (0x596a43 ds:0x985dbc,3; 0x5974b7 ds:0x985dbc,0; 0x5974d3 [0x985af4]).
next: M109 continued = read every gate 0x596a43-0x597a00, emit an if/then leg list, then ONE confirming load. Read a fread size from *(int*)($esp+4).
cron 1a88e12bd408 RESUMED at the end of s167 (next fire 20:13) - it owns the repo from here.
