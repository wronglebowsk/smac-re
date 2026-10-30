M111 BLOCKED (s171), no merge. `m109_leg_census.py --tag m111b3 --relaunch --ranges 0x400000-0x62afff`: 190 armed, 90 executed, 0 gdb errors, counts 67/18, sum=243,007 vs file 242,539 → OVER by 468 B → sequential model VOID. Tail 156 B unnamed.
BOX LOADED: terran.exe 1573718, 67/18, no gdb, no driver.
next: re-run with FILE* filter ($savefile at 0x596850, cond [esp+0xc]==$savefile); pollution = 3×160-B CRT reads (0x62ae0f, dest 0x7cda1c/0xbe8c10/0xbefd3c) + 9×6-dword loop (dest 0x3b7d7a8..0x3c4b420, stride 0x224B8).
