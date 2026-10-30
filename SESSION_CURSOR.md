M113b (m113map2) 24/25: boundaries bracketed to 2 KB — block A->B at 66,048/68,096 (split 67,840 inside), grid->next at 171,192/173,240 (91-B map trailer inside), 174,000..180,144 -> 0x986501..0x987d01. OPEN: 223,048 ABSENT between 221,000 (0x92c8f9) and 225,096 (0x933b81) = a hole inside the 52-record block (~222,783).
M113 merged #119 (main da69b48); this branch milestone/m113b is NOT merged. BOX: terran.exe loaded (67/18), TracerPid 0.
next: --band 222000-224500:128 to resolve the 223,048 hole.
