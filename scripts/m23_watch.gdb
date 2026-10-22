# M23: catch OUR OWN unit's move — record index 118 (Colony Pod, owner 3 = University,
# tile (41,11), HUD-selected, "Moves: 1 / No Order").
#
# Watchpoints (max 4, DR0-DR3):
#   1. x   u16 @ 0x9359e8  (0x933278 + 118*52 + 0)
#   2. y   u16 @ 0x9359ea  (+2)
#   3. order byte @ 0x935a01 (+17)   -- proves the order landed
#   4. u16 @+28 @ 0x935a12           -- travels with the order (M18)
#
# Every hit prints $pc + backtrace + the instruction window; gdb's own
# "Old value / New value" line above each hit is what makes it semantic.
# Ends detach + quit (a KILLED gdb would leave terran.exe stopped).
set pagination off
set confirm off
set can-use-hw-watchpoints 1

watch *(unsigned short*)0x9359e8
watch *(unsigned short*)0x9359ea
watch *(unsigned char*)0x935a01
watch *(unsigned short*)0x935a12

continue
printf "\n=== HIT 1 pc=%#x\n", $pc
bt 12
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 2 pc=%#x\n", $pc
bt 12
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 3 pc=%#x\n", $pc
bt 12
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 4 pc=%#x\n", $pc
bt 12
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 5 pc=%#x\n", $pc
bt 12
x/8i $pc-14
info registers eip ecx edx esi edi
continue
printf "\n=== HIT 6 pc=%#x\n", $pc
bt 12
x/8i $pc-14
info registers eip ecx edx esi edi
detach
quit
