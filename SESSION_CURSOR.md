M110 SORTED to 99.94% (s170) — branch milestone/m109 HEAD 4a7dc5d, gate GREEN, tree clean, NOT merged (Σ 242,383 of 242,539, 156 B short).
MAP NAMED: 0x5822a7 2,724 B header @79,364 + 0x5822f2 grid 90,112 = 64x64x22 @82,088 + 0x582318 91 B trailer @172,200. Coverage contiguous 0..242,383 over 45 read sites. The old 86,016-B heap read = the grid minus its first 4,096 stdio block.
REMAINDER 156 B at 242,383: a 6-dword table [3,0,0,-6,32,32]..[7,..] + 3 dwords; reader NOT in the six ranges (CRT 0x62b000-0x62d000, or an under-counted 0x59666d/0x5966c1 loop).
next: M111 = find that reader; then Σ == 242,539 closes and the branch can merge. cron 1a88e12bd408 RESUMED at the end of s170.
