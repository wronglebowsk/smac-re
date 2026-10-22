# M47: watch OUR FACTION ENERGY itself (0x953884) — every income add and every
# upkeep debit must touch it, so the writers are the provenance we want — plus
# the within-round ledger (0x953888) and our base's transient income field
# (base+0x7c..0x7f at 0x96300c).
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $ne = 0
set $nled = 0
set $n7e = 0

watch *(int *)0x953884
commands
  silent
  set $ne = $ne + 1
  printf "WENERGY n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x esp=%#x\n", $ne, $eip, *(int *)0x953884, $eax, $ebx, $ecx, $edx, $esi, $edi, $esp
  if $ne >= 40
    printf "WENERGY-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x953888
commands
  silent
  set $nled = $nled + 1
  printf "WLED n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x\n", $nled, $eip, *(int *)0x953888, $eax, $ebx, $ecx, $edx
  if $nled >= 40
    printf "WLED-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x96300c
commands
  silent
  set $n7e = $n7e + 1
  printf "W7E n=%d eip=%#x v7c=%d v7e=%d eax=%#x ebx=%#x\n", $n7e, $eip, *(int *)0x96300c, *(int *)0x96300e, $eax, $ebx
  if $n7e >= 40
    printf "W7E-CAP\n"
    detach
    quit
  end
  continue
end

printf "ARMED energy=%#x ledger=%#x field=%#x\n", 0x953884, 0x953888, 0x96300c
continue
