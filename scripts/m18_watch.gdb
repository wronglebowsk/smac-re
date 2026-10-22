# M18: name the function that writes a unit's ORDER byte.
#
# Verified order oracle (M17, same session): pressing 'h' (HOLD, the game's own
# advisor hotkey) on the selected Scout Patrol changed
#   unit 0 @ 0x933278:  +17 0x00 -> 0x02   and  +28/+29 0xff -> 0x00
# So +17 is the order byte and +28..29 a destination/path pair (0xffff = none).
#
# Watch +17 of the four unit records that share tile (20,50) with our own faction:
#   0x933289 (i=0)  0x933325 (i=3)  0x933359 (i=4)  0x9333c1 (i=6)
# Run: gdb -batch -nx -x scripts/m18_watch.gdb -p $(pgrep -x terran.exe)
set pagination off
set confirm off
set can-use-hw-watchpoints 1

watch *(unsigned char*)0x933289
watch *(unsigned char*)0x933325
watch *(unsigned char*)0x933359
watch *(unsigned char*)0x9333c1

continue

echo \n===== ORDER-BYTE WRITE =====\n
printf "pc = %#x\n", $pc
echo --- backtrace ---\n
bt 14
echo --- instructions around pc ---\n
x/14i $pc-20
echo --- registers ---\n
info registers eip eax ebx ecx edx esi edi ebp esp
detach
quit
