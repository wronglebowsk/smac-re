# M24b: after the SELECT UNIT TO ACTIVATE picker resolves, does a second tile click MOVE the unit?
# Selected-unit global located this session: ECX base 0x8f79e0 (verified: 0x8f79e0+0x23bd4 =
# 0x91b5b4 = the known own-player global), so
#   0x91b5bc = selected unit index   (+0x23bdc)
#   0x91b5c0 = secondary/last        (+0x23be0)
#   0x91b5c4 = flag                  (+0x23be4)
#   0x91b5cc = flag set to 1 by FUN_004d3f70 with FUN_0050cab0(1)  (+0x23bec)
# Oracle = watchpoint on the selected-unit global + the unit-x store sites from m23
# (0x5ab355 is the position setter FUN_005ab320's store; 0x4d728c is FUN_004d6fb0's).
# NO `silent` command. End with detach+quit; if killed, `kill -CONT <pid>` revives the game.
set pagination off
set confirm off

watch *(int *)0x91b5bc

break *0x4d3f70
commands
printf "ACT x=%d y=%d flag=%d sel=%d f23bec=%d f23be4=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc, *(int *)0x91b5cc, *(int *)0x91b5c4
continue
end

break *0x512450
commands
printf "KEY code=%d sel=%d\n", *(int *)($esp+4), *(int *)0x91b5bc
continue
end

break *0x50cab0
commands
printf "50cab0 arg=%#x\n", *(int *)($esp+4)
continue
end

break *0x5ab355
commands
printf "SETTER idx=%d newx=%d\n", ($esi/52), $bx
continue
end

break *0x4d728c
commands
printf "W4d728c idx=%d newx=%d\n", ($eax/52), $dx
continue
end

continue
