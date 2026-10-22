# M25: issue a REAL move order by calling the game's own order-issuer, then read the effect.
#   FUN_004cffa0(unit, dest_x, dest_y) -- with DAT_00920434 == 0 (verified live: solo) it takes the
#   `FUN_004cdc70(unit, 0, dest_x, dest_y)` branch, i.e. the same code the player's click reaches.
#   Unit record 119 base = 0x933278 + 119*52 = 0x934aa4;  x +0, y +2, flags +4, order +17,
#   dest_x +20, dest_y +24, +28 order param.  Selected unit (0x91b5bc) is already 119.
# Target (43,11) is a legal 1-step neighbour of (41,11): delta table dir 1 = (+2, 0).
# Ends with detach + quit.  If gdb is killed instead: kill -CONT <terran pid>.
set pagination off
set confirm off
thread 1

printf "BEFORE unit119 x=%d y=%d flags=%#x ord17=%d d20=%d d24=%d v28=%#x\n", *(short *)0x934aa4, *(short *)0x934aa6, *(int *)0x934aa8, *(unsigned char *)0x934ab5, *(short *)0x934ab8, *(short *)0x934abc, *(int *)0x934ac0
call ((void (*)(int, int, int))0x4cffa0)(119, 43, 11)
printf "AFTER  unit119 x=%d y=%d flags=%#x ord17=%d d20=%d d24=%d v28=%#x\n", *(short *)0x934aa4, *(short *)0x934aa6, *(int *)0x934aa8, *(unsigned char *)0x934ab5, *(short *)0x934ab8, *(short *)0x934abc, *(int *)0x934ac0

detach
quit
