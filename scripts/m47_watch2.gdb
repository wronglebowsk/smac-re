# M47b: validate the watchpoint machinery AND widen the income-field probe.
#   0x962fd0 = our base (idx 72) +0x40 mineral accumulator  -> KNOWN per-round writer
#   0x96300c = base+0x7c..0x7f  (covers the transient income field at +0x7e)
#   0x953888 = our faction +4 spending ledger
# Read-only: no pokes, no calls.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $nmin = 0
set $n7e = 0
set $nled = 0

watch *(int *)0x962fd0
commands
  silent
  set $nmin = $nmin + 1
  printf "WMIN n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x\n", $nmin, $eip, *(int *)0x962fd0, $eax, $ebx, $ecx, $edx
  if $nmin >= 25
    printf "WMIN-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x96300c
commands
  silent
  set $n7e = $n7e + 1
  printf "W7E n=%d eip=%#x v7c=%d v7e=%d eax=%#x ebx=%#x ecx=%#x edx=%#x\n", $n7e, $eip, *(int *)0x96300c, *(int *)0x96300e, $eax, $ebx, $ecx, $edx
  if $n7e >= 30
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
  printf "WLED n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x\n", $nled, $eip, *(int *)0x953888, $eax, $ebx, $ecx, $edx
  if $nled >= 40
    printf "WLED-CAP\n"
    detach
    quit
  end
  continue
end

printf "ARMED min=%#x field=%#x ledger=%#x\n", 0x962fd0, 0x96300c, 0x953888
continue
