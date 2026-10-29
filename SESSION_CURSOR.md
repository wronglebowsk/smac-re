M106 RUNNING (s162, milestone/m106): the invisible load-window restore.
scripts/m106_load_restore.py — no gdb: two straces (raw args = read BUFFER POINTERS) + maps before/after
+ clear_refs/pagemap soft-dirty + sentinels in all 8 count dwords. m106r1 crashed PRE-POKE on my own
entry_image offset bug; box left ALIVE at the CDROM screen, counts [0,6,5,4,3,4,5,3] round 0 cp 0.
STATIC while it ran: FUN_00596850 (the .SAV body loader, called by FUN_00597ee0 after the "TERRAN"
magic check) calls FUN_0064cc00(&DAT_00927590, 0x2ce0 = 11488, 1, handle) — fread straight into the
region -> kernel copy_to_user, no debug exception; the sibling FUN_00596540 (used when DAT_00926a14
!= 0) mallocs a scratch buffer and stores into the region in ring 3.
acceptance: m106r2 RUNNING (--no-relaunch) | merged: NO |
next: python3 scripts/m106_load_restore.py --tag m106r2 --no-relaunch
