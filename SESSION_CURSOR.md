M109 RUN s169, NOT ACCEPTED, NOT MERGED — branch milestone/m109 HEAD bc47a6f (gate GREEN, tree clean); main aad8267.
FINDING: 116 static in-loader read-site bps + ONE load = 23 executed sites, sum(size*count) 149,380 B of 242,539 (61.6%); the other 93,159 B is read by callers OUTSIDE [0x596850,0x597a6b] (105 reader sites; the 86,016-B heap read is one). The chunk map cannot close inside the loader.
Confirmed live: count leg 176, 52n 3,484 (52x67), 304m 5,472 (304x18); 0x59738b and its malloc 0x596ab7 never fire.
next: M110 = enumerate the outside reader calls by containing function, census them, closure sum == 242,539.
Box: terran.exe 1501243 at the HUD, m54b_clean r50, counts 67/18. cron 1a88e12bd408 RESUMED at the end of s169.
