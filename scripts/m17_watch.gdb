# M17: catch the function that mutates a unit's tile x-coordinate.
#
# Four hardware watchpoints on the u16 x field (offset +0) of four AI-owned
# unit records in the array at 0x933278 (52 B records).  Chosen from four
# different factions so that whichever faction plays next can trip one:
#   0x93351c  i=13  owner 6  (70,62)
#   0x933584  i=15  owner 7  (77,63)
#   0x9337f4  i=27  owner 5  (54,70)
#   0x934014  i=67  owner 4  (67,7)
#
# Run:  gdb -batch -nx -x scripts/m17_watch.gdb -p $(pgrep -x terran.exe)
set pagination off
set confirm off
set can-use-hw-watchpoints 1

watch *(unsigned short*)0x93351c
watch *(unsigned short*)0x933584
watch *(unsigned short*)0x9337f4
watch *(unsigned short*)0x934014

continue

echo \n===== WATCHPOINT HIT =====\n
printf "pc = %#x\n", $pc
echo --- backtrace ---\n
bt 14
echo --- instructions around pc ---\n
x/10i $pc-18
echo --- registers ---\n
info registers eip eax ebx ecx edx esi edi ebp esp
echo --- hit thread ---\n
info threads
detach
quit
