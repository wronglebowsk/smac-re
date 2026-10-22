# M33: watch the game ISSUE a terraform order end-to-end (driver presses the hotkey).
# Static model (shard_012 FUN_004d44d0 + objdump of the same bytes):
#   key -> FUN_00512b40 -> FUN_00512450 -> FUN_004d44d0(unit, mode)   [entry]
#   payment: TERRAPAY pane shown at 0x4d55a8 (push 0x68c44c; FUN_005f0583) — the picker
#            BLOCKS inside the setter until the player answers it.
#   debit:   0x4d561a  mov %edx,(%eax)  with eax = 0x94d650 + player*0x82f*4, edx = new value
#   store:   0x4d5bbf  mov %cl,0x933289(,%edx,4)   order byte = mode+4 (cl = bl+4);
#            at this site $esp+4 = unit idx (param_1), $esp+8 = mode (param_2)
#   bcast:   0x4d5bc6  call 0x584350 (0x2101), arg $esp+4 = unit idx
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

break *0x4d55a8
commands
silent
printf "TERRAPAY pane-shown (setter blocked here until answered)\n"
continue
end

break *0x4d561a
commands
silent
printf "DEBIT newval=%d\n", $edx
continue
end

break *0x4d5bbf
commands
silent
printf "STORE idx=%d order=%#x\n", *(int *)($esp+4), (int)(unsigned char)*($esp+8)
continue
end

break *0x4d5bc6
commands
silent
printf "BCAST idx=%d\n", *(int *)($esp+4)
continue
end

continue
