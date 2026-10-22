# M27: capture the game's OWN synchronous solo-order call while the player moves a unit
# with an arrow key.  Static model (ghidra_out FUN_00512b40 lines ~1774-1815):
#   arrows/keypad -> dir index (0x21..0x28 -> 0..7) -> if DAT_0091b5b8 != 0 and a unit is
#   selected -> FUN_00529090(unit, dir, 0)  [solo wrapper] -> FUN_00585720(unit, dir, 3)
#   which steps the unit through FUN_005ab320(idx, x, y).
set pagination off
set confirm off

break *0x529090
commands
printf "SOLOWRAP idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x585720
commands
printf "EXEC idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x5ab320
commands
printf "SETTILE idx=%d x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

continue
