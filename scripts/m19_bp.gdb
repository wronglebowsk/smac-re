# M19b: log every call to the unit position setter FUN_005ab320(idx, x, y) = 0x5ab320
# with its caller, without stopping the game for long (auto-continue).
# cdecl args live at $esp+4/+8/+12 at function entry.
set pagination off
set confirm off

break *0x5ab320
commands
silent
printf "SETPOS idx=%d x=%d y=%d\n", *(int*)($esp+4), *(int*)($esp+8), *(int*)($esp+12)
bt 4
silent
continue
end

continue
