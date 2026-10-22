# M28: click-to-destination.  Log the map click, the activate handler, the order issuer, the
# solo wrapper and the executor, plus order-byte writes on the three fresh units 121/122/123
# (all at (41,11), full movement).  Record base = 0x933278 + i*52; +16..19 covers the order byte.
set pagination off
set confirm off

break *0x476580
commands
printf "MAPH px=%d py=%d\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d3f70
commands
printf "ACT x=%d y=%d flag=%d sel=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc
continue
end

break *0x4d6fb0
commands
printf "ORDER unit=%d code=%#x flag=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

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

watch *(int *)0x934b1c
commands
printf "W121 order-int -> %#x\n", *(int *)0x934b1c
continue
end

watch *(int *)0x934b50
commands
printf "W122 order-int -> %#x\n", *(int *)0x934b50
continue
end

watch *(int *)0x934b84
commands
printf "W123 order-int -> %#x\n", *(int *)0x934b84
continue
end

continue
