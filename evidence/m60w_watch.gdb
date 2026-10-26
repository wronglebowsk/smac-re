set pagination off
set confirm off
set height 0
set verbose off
watch *0x8f0d70
commands
silent
printf "GUARDWRITE pc=0x%x new=%d\n", $pc, *(int*)0x8f0d70
continue
end
break *0x4ef6d0
commands
silent
printf "VISIT guard=%d\n", *(int*)0x8f0d70
continue
end
continue
