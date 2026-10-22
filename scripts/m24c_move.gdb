# M24c: catch the MOVE order landing on unit record 119 (our selected survivor).
# Static model (this session, from ghidra_out):
#   FUN_00476580  map-widget click/menu handler; on a menu choice dispatches
#                 case 4 -> FUN_00529a40, 8 -> FUN_004d08b0, 10 -> FUN_004cffa0 (MOVE),
#                 0xb -> FUN_004d9380, then clears DAT_0091b5c4; in its other branch it
#                 writes order byte +17 = 0x18 and destination +20/+24, then FUN_00584350
#                 (broadcast 0x2101) and FUN_0050cab0(1).
#   FUN_004cffa0(unit,x,y)  issue-move: solo (DAT_00920434==0) -> FUN_004cdc70(unit,0,x,y);
#                 netplay -> FUN_00528930(&unit,4,x,y,0) + packet 0x2413.
#   record 119 base = 0x934aa4  (+16..19 order byte, +20 destx, +24 desty)
set pagination off
set confirm off

watch *(int *)0x934ab4
watch *(int *)0x934ab8
watch *(int *)0x934abc

break *0x476580
commands
printf "MAPH p1=%#x p2=%#x p3=%#x sel=%d b5b8=%d b5c4=%d b5e8=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc, *(int *)0x91b5b8, *(int *)0x91b5c4, *(int *)0x91b5e8
continue
end

break *0x4cffa0
commands
printf "ISSUE_MOVE idx=%d x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4cdc70
commands
printf "SOLO_MOVE idx=%d mode=%#x x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10)
continue
end

break *0x5ab355
commands
printf "SETTER idx=%d newx=%d\n", ($esi/52), $bx
continue
end

break *0x4d3f70
commands
printf "ACT x=%d y=%d flag=%d sel=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc
continue
end

continue
