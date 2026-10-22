# M32: enumerate the order-menu command table LIVE.
# Static model (ghidra_out FUN_00512b40 -> FUN_00512450):
#   key event -> FUN_00512b40(char, VK|modifier-flags); with orders mode on (DAT_0091b5b8 != 0)
#   and a unit selected (DAT_0091b5bc >= 0) and FUN_004e1f90() == 0, non-directional keys
#   dispatch to FUN_00512450(param_1=char, param_2=tolower(char), param_3=VK|flags/menu code),
#   whose switches call the order setters below.
# 32-bit cdecl: args at $esp+4, $esp+8, $esp+0xc.
set pagination off
set confirm off

break *0x512b40
commands
silent
printf "KEY p1=%#x p2=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x512450
commands
silent
printf "DISP p1=%#x p2=%#x p3=%#x\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4d44d0
commands
silent
printf "TERRAF idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d3770
commands
silent
printf "HOLD idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d6fb0
commands
silent
printf "BASEORD idx=%d code=%#x flag=%#x\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4d9120
commands
silent
printf "CANCEL idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d8b20
commands
silent
printf "JOINBASE idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d8ca0
commands
silent
printf "ABILITY idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d9690
commands
silent
printf "AREA10 idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d94d0
commands
silent
printf "CONVOY idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d3510
commands
silent
printf "SENTRY idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d8c20
commands
silent
printf "ROUTE8 idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d8920
commands
silent
printf "ROADTO idx=%d code=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d8a30
commands
silent
printf "DESIG idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d20f0
commands
silent
printf "UPGRADE idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d3950
commands
silent
printf "GIVE idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d1f20
commands
silent
printf "UNLOAD idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d1280
commands
silent
printf "FUNDBASE idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d6b90
commands
silent
printf "OBLIT idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d1e90
commands
silent
printf "RUNORDER idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d6100
commands
silent
printf "BOMBARD idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d9470
commands
silent
printf "CLEAR idx=%d\n", *(int *)($esp+4)
continue
end

break *0x529090
commands
silent
printf "SOLOWRAP idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x50ba90
commands
silent
printf "PANEMODE idx=%#x v=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x585720
commands
silent
printf "EXEC idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x5ab320
commands
silent
printf "SETTILE idx=%d x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4d3f70
commands
silent
printf "ACT x=%d y=%d flag=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4cffa0
commands
silent
printf "ATTACK idx=%d x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x511960
commands
silent
printf "CURSOR p1=%#x p2=%#x p3=%#x\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

continue
