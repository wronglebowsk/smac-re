set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = 0x95ef70
set $add = 0
set $gate = 0
set $pay = 0
set $cl = 0
break *0x4ef7f1
commands
silent
set $add = $add + 1
printf "ADD#%d before=%d d0=%d head=%d pend=%d\n", $add, *(int *)($b + 0x40), *(int *)($b + 0xd0), *(int *)($b + 0x50), *(int *)($b + 0x4c)
continue
end
break *0x4f0a3d
commands
silent
set $gate = $gate + 1
printf "GATE#%d storage=%d price=%d pend=%d\n", $gate, *(int *)($b + 0x40), $edi, *(int *)($b + 0x4c)
continue
end
break *0x4efed8
commands
silent
set $pay = $pay + 1
printf "PAY#%d before=%d edi=%d\n", $pay, *(int *)($b + 0x40), $edi
continue
end
break *0x4efeec
commands
silent
set $cl = $cl + 1
printf "CLMP#%d storage=%d cap=%d d0=%d\n", $cl, *(int *)($b + 0x40), $ecx, $eax
continue
end
continue
