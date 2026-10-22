set pagination off
set confirm off
watch *(int *)0x933288
commands
printf "WP_ORDER pc=%#x\n", $pc
continue
end
watch *(int *)0x93328c
commands
printf "WP_DX pc=%#x\n", $pc
continue
end
watch *(int *)0x933294
commands
printf "WP_DY pc=%#x\n", $pc
continue
end
break *0x476580
commands
printf "MAPH p1=%#x p2=%#x p3=%#x sel=%d b5b8=%d b5c4=%d b5e8=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc, *(int *)0x91b5b8, *(int *)0x91b5c4, *(int *)0x91b5e8
continue
end
break *0x4d3f70
commands
printf "ACT x=%d y=%d flag=%d sel=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc
continue
end
break *0x4d6fb0
commands
printf "ORDERGIVER unit=%d p2=%#x p3=%#x\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end
break *0x512450
commands
printf "KEYSEL a1=%#x a2=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end
break *0x512b40
commands
printf "KEYROUTE a1=%#x\n", *(int *)($esp+4)
continue
end
break *0x529090
commands
printf "SOLOWRAP idx=%d dir=%#x mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end
break *0x585720
commands
printf "EXEC idx=%d p2=%#x p3=%#x order=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(unsigned char*)(0x933278 + 52**(int*)($esp+4) + 17)
continue
end
break *0x502c40
commands
printf "STEP idx=%d dir=%d parity=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+12)
continue
end
break *0x4cffa0
commands
printf "ATTACK idx=%d x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end
break *0x4cdc70
commands
printf "BOMB idx=%d mode=%#x x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10)
continue
end
break *0x5ab355
commands
printf "SETTER idx=%d newx=%d\n", ($esi/52), $bx
continue
end
continue
