M109 attempt 3 RUNNING NOW (m109g1), NOT ACCEPTED — branch milestone/m109; main = aad8267 (M108 #115).
CMD: python3 scripts/m109_leg_gates.py --tag m109g1 --relaunch — 5 bps: FUN_00596850 ENTER (the FILE*)
+ read wrappers 0x596470/596540/64c9a0/64cc00 (ra,ptr,size,count,stream).
STATIC (scratch/m109/skel_loader.txt): those 4 are 2 PAIRS — 596470/596540 = CONVERTING (malloc
size*count), 64c9a0/64cc00 = DIRECT; chosen by [0x926a14]=([0x985ae8]&0x10000000), live 0 -> DIRECT.
count is ALWAYS 1. 105 reader sites exist OUTSIDE FUN_00596850 -> M107's 30-leg table is incomplete.
next if PASS: gate.py --base main -> milestone.py submit -> merge.
