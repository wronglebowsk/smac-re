# M24: who handles a map click / a hotkey, and what is the UI singleton base (ECX)?
#   0x4d3f70  FUN_004d3f70(x, y, flag)  -- tile ACTIVATE handler (logs s_Console_ACTIVATE,
#             resolves the tile via FUN_005ab130, writes *(ECX+0x23bdc) = selected unit idx,
#             calls FUN_0050cab0(1) + sets *(ECX+0x23bec)=1 when it selects one of our units)
#   0x512450  FUN_00512450(code, ?, ?)  -- hotkey dispatcher, switch on the stack arg
#   0x50cab0  called with 1 on select / 0 otherwise (suspected move-targeting mode flag)
# thiscall: ECX = the singleton, stack args at esp+4/+8/+0xc.
# NO `silent` command (gdb has none). Ends with detach+quit; if killed instead,
# `kill -CONT <terran pid>` revives the game.
set pagination off
set confirm off

break *0x4d3f70
commands
printf "ACT x=%d y=%d flag=%d ecx=%#x sel=%d\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+0xc), $ecx, *(int*)($ecx+0x23bdc)
continue
end

break *0x512450
commands
printf "KEY code=%d ecx=%#x sel=%d\n", *(int*)($esp+4), $ecx, *(int*)($ecx+0x23bdc)
continue
end

break *0x50cab0
commands
printf "50cab0 arg=%#x ecx=%#x\n", *(int*)($esp+4), $ecx
continue
end

continue
