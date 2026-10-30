M114 DONE (zero box time): restore is 1:1 — 12 windows of diff vs the poked save, 10 byte-identical. Rewriting only in the map header TAIL (81,408..82,100) and block A TAIL (67,080..67,143, 16-B stride); 52-record array has 2 differing dwords (222,831 cleared; poked field 223,152 normalised C0->D6). Block B base = file 67,852 -> 0x927590 (doc said 67,840, 12 B early).
main 0219ff5 after #116-#122. BOX: terran.exe loaded (67/18), TracerPid 0.
next: name the writers of the two tails (hw watchpoint on 0x9277xx / map-header tail) or move to the STILL OPEN band-flag setter.
