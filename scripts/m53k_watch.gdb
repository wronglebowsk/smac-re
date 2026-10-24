set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = 50

# The Colony = record idx 23 = 0x95f568; fields +0x40=0x95f5a8, +0xd0=0x95f638
# ours (idx 64) = 0x962d30; +0x40=0x962d70, +0xd0=0x962e00

watch *(int *)0x95f5a8
commands
  silent
  set $n = $n + 1
  printf "WP %d COL40 eip=%#x new=%d col_d0=%d col_cc=%d col_q50=%d eax=%#x ecx=%#x edx=%#x ebx=%#x esi=%#x edi=%#x ebp=%#x\n", $n, $eip, *(int *)0x95f5a8, *(int *)0x95f638, *(int *)0x95f634, *(int *)0x95f5b8, $eax, $ecx, $edx, $ebx, $esi, $edi, $ebp
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x95f638
commands
  silent
  set $n = $n + 1
  printf "WP %d COLD0 eip=%#x new=%d col40=%d col_cc=%d eax=%#x ecx=%#x edx=%#x ebx=%#x esi=%#x edi=%#x ebp=%#x\n", $n, $eip, *(int *)0x95f638, *(int *)0x95f5a8, *(int *)0x95f634, $eax, $ecx, $edx, $ebx, $esi, $edi, $ebp
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x962d70
commands
  silent
  set $n = $n + 1
  printf "WP %d OUR40 eip=%#x new=%d our_d0=%d our_q50=%d eax=%#x ecx=%#x edx=%#x esi=%#x\n", $n, $eip, *(int *)0x962d70, *(int *)0x962e00, *(int *)0x962d80, $eax, $ecx, $edx, $esi
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x962e00
commands
  silent
  set $n = $n + 1
  printf "WP %d OURD0 eip=%#x new=%d our40=%d eax=%#x ecx=%#x edx=%#x esi=%#x\n", $n, $eip, *(int *)0x962e00, *(int *)0x962d70, $eax, $ecx, $edx, $esi
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

# selftest: touch every address now
printf "SELFTEST %#x %#x %#x %#x\n", 0x95f5a8, 0x95f638, 0x962d70, 0x962e00
printf "STATE year=%d cur=%d nb=%d col40=%d cold0=%d our40=%d ourd0=%d\n", *(int *)0x985b00, *(int *)0x985dcc, *(int *)0x985af4, *(int *)0x95f5a8, *(int *)0x95f638, *(int *)0x962d70, *(int *)0x962e00
continue
python
import gdb
gdb.execute("detach")
gdb.execute("quit")
end
