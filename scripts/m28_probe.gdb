# M28: why does a map click not write the 0x18 move order?  Break every early-return gate of
# FUN_00476580 and the three order-store sites.
set pagination off
set confirm off

break *0x476580
commands
printf "MAPH p1=%#x p2=%#x p3=%#x sel=%d mode=%d pend=%d this=%#x wmode=%#x\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)0x91b5bc, *(int *)0x91b5b8, *(int *)0x91b5c4, $ecx, *(int *)($ecx+0x1ef4c)
continue
end

break *0x47674d
commands
printf "RET_A (FUN_0046a310 != 0)\n"
continue
end

break *0x476778
commands
printf "RET_B (FUN_00469060 == 0)\n"
continue
end

break *0x4767ab
commands
printf "RET_C (panel 0x1dd8c != 0)\n"
continue
end

break *0x476ac7
commands
printf "STORE_18_a esi-tile=%d edi-tile=%d eax=%#x\n", *(short *)$esi, *(short *)$edi, $eax
continue
end

break *0x476bae
commands
printf "STORE_18_b esi-tile=%d edi-tile=%d edx=%#x\n", *(short *)$esi, *(short *)$edi, $edx
continue
end

break *0x476c39
commands
printf "STORE_18_c esi-tile=%d edi-tile=%d ecx=%#x\n", *(short *)$esi, *(short *)$edi, $ecx
continue
end

continue
