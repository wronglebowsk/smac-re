# M47: instrument validation — watch the mission year itself, which provably
# changes when a round resolves. If this does not fire, hardware watchpoints
# are not usable on this Wine build and the write-provenance method must change.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $ny = 0
watch *(int *)0x985b00
commands
  silent
  set $ny = $ny + 1
  printf "WYEAR n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esp=%#x\n", $ny, $eip, *(int *)0x985b00, $eax, $ebx, $ecx, $edx, $esp
  if $ny >= 5
    printf "WYEAR-CAP\n"
    detach
    quit
  end
  continue
end
printf "ARMED year=%#x\n", 0x985b00
continue
