M109 NOT ACCEPTED, NOT MERGED — branch milestone/m109 (last commit 414910a); main = aad8267 (M108 #115).
m109g4 FAIL 1/6: 5 bps armed clean, but the load NEVER ran under gdb — 0 ENTER at FUN_00596850,
0 reads on the save stream, driver "timeout reaching HUD" at 910 s (it reached the LOAD GAME panel at
329 s and the blind browser step never confirmed). m109g1/g2/g3 died on my instrument (220 s driver
budget, SIGUSR1 detach, 25,957 unfiltered wrapper hits). The GATE ANSWER is static and committed in
scratch/m109/skel_loader.txt. next: drive the load WITHOUT gdb attached during the menu (arm gdb only
after the save's FILE* is open), or bp the 122 in-loader call sites; then gate.py --base main.
