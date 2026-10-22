# M19: catch a genuine unit MOVE.
#
# Four hardware watchpoints on the u16 x field of four un-stacked foreign units,
# one per faction, none near our base (20,50):
#   0x9334b4  i=11  owner 6  (73,63) flags 0x2
#   0x9332e0  i=2   owner 7  (0,76)  flags 0x2
#   0x934730  i=102 owner 2  (53,41) flags 0x0
#   0x933654  i=19  owner 1  (28,26) flags 0x2
#
# Six hits are captured (a purge writes 0xffff and will show up too — read Old/New
# before believing any hit is a move), then detach so the game keeps running.
set pagination off
set confirm off
set can-use-hw-watchpoints 1

watch *(unsigned short*)0x9334b4
watch *(unsigned short*)0x9332e0
watch *(unsigned short*)0x934730
watch *(unsigned short*)0x933654

continue
printf "\n=== HIT 1 pc=%#x\n", $pc
bt 10
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 2 pc=%#x\n", $pc
bt 10
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 3 pc=%#x\n", $pc
bt 10
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 4 pc=%#x\n", $pc
bt 10
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 5 pc=%#x\n", $pc
bt 10
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 6 pc=%#x\n", $pc
bt 10
x/8i $pc-14
info registers eip ecx edx esi edi
detach
quit
