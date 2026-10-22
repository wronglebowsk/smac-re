# M47a: hardware watchpoints on our base's transient income field (base+0x7e)
# and our faction's within-round spending ledger (94d650 + 3*0x20bc + 4).
# Read-only: no pokes, no calls. Caps on hits so a hot writer cannot flood.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $n7e = 0
set $nled = 0

watch *(int *)0x96300e
commands
  silent
  set $n7e = $n7e + 1
  printf "W7E n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esp=%#x\n", $n7e, $eip, *(int *)0x96300e, $eax, $ebx, $ecx, $edx, $esp
  if $n7e >= 40
    printf "W7E-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x953888
commands
  silent
  set $nled = $nled + 1
  printf "WLED n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esp=%#x\n", $nled, $eip, *(int *)0x953888, $eax, $ebx, $ecx, $edx, $esp
  if $nled >= 80
    printf "WLED-CAP\n"
    detach
    quit
  end
  continue
end

printf "ARMED base7e=%#x ledger=%#x\n", 0x96300e, 0x953888
continue
