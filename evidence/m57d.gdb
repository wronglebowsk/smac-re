set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $b = 0x95ef70
set $enq = 0
set $hd = 0
set $pi = 0
set $pr = 0
set $sh = 0
set $tl = 0
set $add = 0
break *0x417ee0
commands
silent
set $enq = $enq + 1
printf "ENQ#%d param1=%d param2=%d curbase=0x%x\n", $enq, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)0x8f0d60
continue
end
break *0x418b57
commands
silent
set $hd = $hd + 1
printf "HEADSTORE#%d curbase=0x%x writes=[base+0x50]=%d base40=%d base4c=%d\n", $hd, *(int *)0x8f0d60, $eax, *(int *)(*(int *)0x8f0d60 + 0x40), *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418ad3
commands
silent
set $pi = $pi + 1
printf "PEND_INC#%d curbase=0x%x base4c=%d\n", $pi, *(int *)0x8f0d60, *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418762
commands
silent
set $pr = $pr + 1
printf "PEND_DEC#%d curbase=0x%x base4c=%d\n", $pr, *(int *)0x8f0d60, *(int *)(*(int *)0x8f0d60 + 0x4c)
continue
end
break *0x418ac7
commands
silent
set $sh = $sh + 1
printf "SHIFT#%d curbase=0x%x\n", $sh, *(int *)0x8f0d60
continue
end
break *0x418b24
commands
silent
set $tl = $tl + 1
printf "TAIL#%d curbase=0x%x slot=%d\n", $tl, *(int *)0x8f0d60, $esi
continue
end
break *0x4ef7db if $eax == 0x95ef70
commands
silent
set $add = $add + 1
printf "ADD#%d storage=%d d0=%d head=%d pend=%d flag30=0x%x\n", $add, *(int *)($b + 0x40), $ecx, *(int *)($b + 0x50), *(int *)($b + 0x4c), *(int *)($b + 0x30)
continue
end
continue
