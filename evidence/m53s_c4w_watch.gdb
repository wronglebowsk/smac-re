set pagination off
set confirm off
set verbose off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = 4000
set $hit46 = 0
set $hit3 = 0

watch *(int *)0x961174
commands
silent
set $n = $n + 1
set $hit46 = $hit46 + 1
printf "C4W b46 n=%d pc=%#x new=%d esp=%#x\n", $n, $pc, *(int *)0x961174, $esp
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)0x95de64
commands
silent
set $n = $n + 1
set $hit3 = $hit3 + 1
printf "C4W b3 n=%d pc=%#x new=%d esp=%#x\n", $n, $pc, *(int *)0x95de64, $esp
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

continue
