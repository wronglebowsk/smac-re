set pagination off
set confirm off
set verbose off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = 300

break *0x4eaa2e
commands
silent
set $n = $n + 1
printf "C74ADD n=%d idx=%d c4pre=%d add=%d c74=%d curidx=%d ret=%#x\n", $n, ((int)$eax - 0x95da10)/0x130, $esi, $ecx, *(int *)0x8f0c74, *(int *)0x68cbb0, *(int *)($esp)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

continue
