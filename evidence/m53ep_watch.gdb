set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $enq = 0
set $qp = 0
set $su = 0
set $sd = 0
set $hd = 0
set $d2 = 0
set $w54 = 0
set $w58 = 0
set $mw = 0
set $sv = 0
break *0x417ee0
commands
silent
set $b = *(int *)0x8f0d60
set $enq = $enq + 1
printf "ENQ#%d pane=0x%x param1=%d param2=%d f40=%d f44=%d f4c=%d f50=%d f54=%d f58=%d f5c=%d\n", $enq, $ebx, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($b + 0x40), *(int *)($b + 0x44), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x5c)
continue
end
break *0x41860a
commands
silent
printf "PRESHOW slot=%d mode=%d f4c=%d f54=%d\n", *(int *)($ebx + 0x3ff5c), *(int *)($ebx + 0xb194), *(int *)($b + 0x4c), *(int *)($b + 0x54)
continue
end
break *0x418aa2
commands
silent
printf "ANSWER eax=%d\n", $eax
continue
end
break *0x418ac7
commands
silent
set $b = *(int *)0x8f0d60
set $su = $su + 1
printf "SHIFTUP#%d dst_off=0x%x old=%d new=%d\n", $su, $eax + 4, *(int *)($b + $eax + 4), $edx
continue
end
break *0x418751
commands
silent
set $b = *(int *)0x8f0d60
set $sd = $sd + 1
printf "SHIFTDN#%d dst_off=0x%x old=%d new=%d\n", $sd, $eax, *(int *)($b + $eax), $edx
continue
end
break *0x418b57
commands
silent
set $b = *(int *)0x8f0d60
set $hd = $hd + 1
printf "HEAD#%d slot0_old=%d new=%d esi=%d f4c=%d\n", $hd, *(int *)($b + 0x50), *(int *)($ebp - 0x10), $esi, *(int *)($b + 0x4c)
continue
end
break *0x418b24
commands
silent
set $b = *(int *)0x8f0d60
printf "TAIL esi=%d slot[esi]=%d f4c=%d f50=%d f54=%d\n", $esi, *(int *)($b + $esi * 4 + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54)
continue
end
break *0x418ad3
commands
silent
printf "CNT_INC_PRE f4c=%d\n", *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418b02
commands
silent
printf "CNT3_PRE f4c=%d\n", *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418762
commands
silent
printf "CNT_DEC_PRE f4c=%d\n", *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x41821a
commands
silent
set $b = *(int *)0x8f0d60
set $sv = $sv + 1
printf "SNAP#%d snap_f50=%d snap_f54=%d snap_f58=%d cur_f54=%d f4c=%d\n", $sv, *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x54), *(int *)($b + 0x4c)
continue
end
break *0x418633
commands
silent
printf "RESTORE off=0x%x snap=%d\n", $eax, *(int *)($ecx + $eax)
continue
end
break *0x417d20
commands
silent
set $b = *(int *)0x8f0d60
set $d2 = $d2 + 1
printf "D20#%d item=%d slot=%d f4c=%d f50=%d f54=%d f58=%d\n", $d2, *(int *)($esp + 4), *(int *)($ecx + 0x3ff5c), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58)
continue
end
break *0x417dd8
commands
silent
set $b = *(int *)0x8f0d60
printf "D20_SHIFT dst_off=0x%x old=%d new=%d\n", $edx, *(int *)($b + $edx), $edi
continue
end
break *0x417e04
commands
silent
set $b = *(int *)0x8f0d60
printf "D20_STORE dst_off=0x%x old=%d new=%d item=%d\n", $edx * 4 + 0x50, *(int *)($b + $edx * 4 + 0x50), $ebx, $ebx
continue
end
break *0x4186d2
commands
silent
printf "POST_PICK edi=%d\n", $edi
continue
end
break *0x4186ec
commands
silent
set $b = *(int *)0x8f0d60
printf "MODE pane=0x%x mode=%d slotfield=%d f4c=%d f50=%d f54=%d f58=%d\n", $ebx, *(int *)($ebx + 0xb194), *(int *)($ebx + 0x3ff5c), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58)
continue
end
break *0x418e1d
commands
silent
printf "BRANCH_E1D (param1==0) edi=%d\n", $edi
continue
end
break *0x418cc9
commands
silent
printf "BRANCH_MODE2 edi=%d\n", $edi
continue
end
break *0x418cd8
commands
silent
printf "BRANCH_MODE3 edi=%d\n", $edi
continue
end
break *0x419967
commands
silent
printf "BRANCH_EXIT edi=%d\n", $edi
continue
end
break *0x4ef6d0 if *(int *)0x8f0d60 == 0x962d30
commands
silent
set $b = *(int *)0x8f0d60
set $qp = $qp + 1
printf "QPIPE#%d f40=%d f44=%d f4c=%d f50=%d f54=%d f58=%d f5c=%d\n", $qp, *(int *)($b + 0x40), *(int *)($b + 0x44), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x54), *(int *)($b + 0x58), *(int *)($b + 0x5c)
continue
end

watch *(int *)(0x962d84)
commands
silent
set $w54 = $w54 + 1
printf "W54#%d pc=0x%x val_after=%d\n", $w54, $pc, *(int *)0x962d84
continue
end
watch *(int *)(0x962d88)
commands
silent
set $w58 = $w58 + 1
printf "W58#%d pc=0x%x val_after=%d\n", $w58, $pc, *(int *)0x962d88
continue
end
continue
