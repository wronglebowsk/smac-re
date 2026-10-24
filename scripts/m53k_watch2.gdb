set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = 60

# The Colony idx 23 = 0x95f560: +0x3c=0x95f59c +0x40=0x95f5a0 +0x48=0x95f5a8 +0xd0=0x95f630

watch *(int *)0x95f630
commands
  silent
  set $n = $n + 1
  printf "WP %d D0 eip=%#x new=%d c0=%d f0=%d e0=%d m40=%d m94=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $n, $eip, *(int *)0x95f630, *(int *)0x95f5d0, *(int *)0x95f600, *(int *)0x95f610, *(int *)0x95f5a0, *(int *)0x95f5f4, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x95f5a0
commands
  silent
  set $n = $n + 1
  printf "WP %d M40 eip=%#x new=%d d0=%d c3c=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $n, $eip, *(int *)0x95f5a0, *(int *)0x95f630, *(int *)0x95f59c, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x95f59c
commands
  silent
  set $n = $n + 1
  printf "WP %d C3C eip=%#x new=%d m40=%d d0=%d cc=%d eax=%#x ebx=%#x ecx=%#x edx=%#x\n", $n, $eip, *(int *)0x95f59c, *(int *)0x95f5a0, *(int *)0x95f630, *(int *)0x95f634, $eax, $ebx, $ecx, $edx
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x95f5a8
commands
  silent
  set $n = $n + 1
  printf "WP %d C48 eip=%#x new=%d m40=%d d0=%d eax=%#x ebx=%#x ecx=%#x edx=%#x\n", $n, $eip, *(int *)0x95f5a8, *(int *)0x95f5a0, *(int *)0x95f630, $eax, $ebx, $ecx, $edx
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

printf "SELFTEST %#x %#x %#x %#x\n", 0x95f630, 0x95f5a0, 0x95f59c, 0x95f5a8
printf "STATE year=%d cur=%d nb=%d col_name_at_23=%s c3c=%d m40=%d c48=%d d0=%d\n", *(int *)0x985b00, *(int *)0x985dcc, *(int *)0x985af4, (char*)(0x95f560+19), *(int *)0x95f59c, *(int *)0x95f5a0, *(int *)0x95f5a8, *(int *)0x95f630
continue
