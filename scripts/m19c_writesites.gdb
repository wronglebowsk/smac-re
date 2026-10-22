# M19c: log EVERY write to a unit's x (or y) tile field.
#
# objdump over the runtime .text (0x401000..0x689000) found only 12 instructions
# that store to [reg+0x933278] (x) or [reg+0x93327a] (y); they sit in five
# functions.  Breakpointing the x-stores and logging the record base register
# (== index*52) plus the value register tells us which function performs a move,
# and who calls it.  Sites (x store, value reg, base reg):
#   0x476aa9  cx,   eax   FUN_00476580
#   0x4d728c  dx,   eax   FUN_004d6fb0
#   0x5ab355  bx,   esi   FUN_005ab320  (the setter)
#   0x5ab4bc  cx,   edi
#   0x5ab573  cx,   eax
# The purge (0x5ab2f1, writes 0xffff) is deliberately excluded.
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
