set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = 1200

# M53m: economy-sweep accumulation globals. x86 hw watchpoint budget = 4 DR slots
# (8-byte windows need 8-alignment; all our pairs are only 4-aligned -> 1 DR each),
# so the 4 DRs go to the 4 sweep slots. The 4 base-70 fields (0x962e0c +0xbc,
# 0x962e10 +0xc0, 0x962d90 +0x40 minerals, 0x962e1c +0xcc rate) are covered by the
# value-change log of scripts/m53m_poll.py instead.
#   0x8f0c6c slot0 (b38=0, feeds base+0xbc)   0x8f0c70 slot1 (b38=1, feeds base+0xc0)
#   0x8f0c34 upkeep slot0 (ec)                0x8f0c38 upkeep slot1 (f0)

watch *(int *)0x8f0c6c
commands
  silent
  set $n = $n + 1
  printf "WP %d 8f0c6c new=%d eip=%#x\n", $n, *(int *)0x8f0c6c, $eip
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x8f0c70
commands
  silent
  set $n = $n + 1
  printf "WP %d 8f0c70 new=%d eip=%#x\n", $n, *(int *)0x8f0c70, $eip
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x8f0c34
commands
  silent
  set $n = $n + 1
  printf "WP %d 8f0c34 new=%d eip=%#x\n", $n, *(int *)0x8f0c34, $eip
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x8f0c38
commands
  silent
  set $n = $n + 1
  printf "WP %d 8f0c38 new=%d eip=%#x\n", $n, *(int *)0x8f0c38, $eip
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

printf "SELFTEST %#x %#x %#x %#x %#x %#x %#x %#x\n", 0x8f0c6c, 0x8f0c70, 0x8f0c34, 0x8f0c38, 0x962e0c, 0x962e10, 0x962d90, 0x962e1c
printf "STATE year=%d cur=%d nb=%d g6c=%d g70=%d g34=%d g38=%d bc=%d c0=%d m40=%d cc=%d\n", *(int *)0x985b00, *(int *)0x985dcc, *(int *)0x985af4, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)0x8f0c34, *(int *)0x8f0c38, *(int *)0x962e0c, *(int *)0x962e10, *(int *)0x962d90, *(int *)0x962e1c
continue
