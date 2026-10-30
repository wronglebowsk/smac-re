M110 SORTED to 99.94% (s170) — branch milestone/m109 HEAD 5b2f704, gate GREEN, tree clean, NOT merged (Σ 242,383 of 242,539, 156 B short). main aad8267 (M107 #114, M108 #115).
MAP NAMED: 0x5822a7 2,724 B header @79,364 + 0x5822f2 grid 90,112 = 64x64x22 @82,088 + 0x582318 91 B trailer @172,200; coverage contiguous 0..242,383 over 45 read sites; the old 86,016-B read = the grid minus its first 4,096 stdio block.
REMAINDER 156 B at 242,383: 6-dword table [3,0,0,-6,32,32]..[7,..] + 3 dwords; no `push 0x9c` near a reader, so read in pieces. Only un-armed reader sites left = 31 CRT ones in 0x62b000-0x62d000; the attempt with that range (m111a1) was SIGTERMed at a session boundary after arming, 0 hits, no evidence file.
next: M111 = run the CRT-armed census (persist_on_release=true so a release cannot kill it) and name the reader; then Σ == 242,539 closes and the branch can merge.
cron 1a88e12bd408 is PAUSED ON PURPOSE — do not resume it.
