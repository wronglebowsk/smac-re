# M23d: log EVERY write to a unit's x tile field (u16 @ 0x933278 + idx*52) while a
# keyboard order is issued — the general oracle, no need to know which unit moves.
# Sites found by objdump over the runtime .text (see scripts/m19c_writesites.gdb header):
#   0x476aa9  cx,   eax   FUN_00476580
#   0x4d728c  dx,   eax   FUN_004d6fb0
#   0x5ab355  bx,   esi   FUN_005ab320  (the position setter)
#   0x5ab4bc  cx,   edi
#   0x5ab573  cx,   eax
# NO `silent` command (gdb has none — that aborted session 22b's first two attempts).
# Ends with detach + quit so terran.exe is never left stopped.
set pagination off
set confirm off

break *0x476aa9
commands
printf "W@0x476aa9 idx=%d newx=%d\n", ($eax/52), $cx
bt 3
continue
end
break *0x4d728c
commands
printf "W@0x4d728c idx=%d newx=%d\n", ($eax/52), $dx
bt 3
continue
end
break *0x5ab355
commands
printf "W@0x5ab355 idx=%d newx=%d\n", ($esi/52), $bx
bt 3
continue
end
break *0x5ab4bc
commands
printf "W@0x5ab4bc idx=%d newx=%d\n", ($edi/52), $cx
bt 3
continue
end
break *0x5ab573
commands
printf "W@0x5ab573 idx=%d newx=%d\n", ($eax/52), $cx
bt 3
continue
end

continue
