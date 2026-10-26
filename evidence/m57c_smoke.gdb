set pagination off
set confirm off
set height 0
set verbose off
set can-use-hw-watchpoints 1
set $w = 0
set $b = 0x95ef70
watch *(int *)0x95ef70
commands
silent
set $w = $w + 1
shell echo "TS $((`date +%s.%N`))"
printf "WP#%d pc=0x%x val=%d pend=%d head=%d d0=%d\n", $w, $pc, *(int *)$b, *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0xd0)
bt 6
continue
end
continue
