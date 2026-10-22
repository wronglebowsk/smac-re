# M48c: MINIMAL mineral-accumulator write probe -- no driver, no OCR.
#
# m48a/m48e/m48f all showed base+0x40 going 200 -> 0 across the round boundary while
# the game itself announced "The minerals output of Climactic Research is not
# sufficient to support Scout Patrol unit. The unit has been disbanded."  This script
# exists to catch WHICH store does it.  Static candidates inside FUN_004ef6d0 (asm,
# byte displacements): income add 0x4ef7f6 (needs base+0xd0 >= 0 -- ours is -1, so it
# must be skipped), spend A 0x4efedd, clamp A 0x4eff20, spend B 0x4f0ca6, clamp B
# 0x4f0ce9, queue drain 0x4f1e3f.  Both clamps are behind
# (1 << (owner & 0x1f)) & *(int*)0x985b10 -- live mask 0xff08 has bit 3 (our player)
# SET and bits 4-7 clear, which is exactly why AI bases hold 15-51 minerals while ours
# is pinned.  Every site below prints unconditionally for OUR base only, keyed on
# *(int*)0x8f0d60 (the pipeline's current-base global), so the 74 AI bases stay quiet.
#
# This gdb build (Ubuntu 17.1): `set print frame-verbosity` does not exist; a
# convenience-variable expression in a `watch` expression dies at definition time with
# "No symbol table is loaded" (watch locations resolve at parse time); `loop_break`
# inside if-inside-while inside a commands list SEGFAULTS gdb at definition time; an
# expression error inside a commands list aborts the whole sourced script and detaches.
# Hence: literal watch addresses, counter-based loop exits, and a SELFTEST block that
# touches every address at script time.  Pitfall 15: stdout to a file is block-buffered
# -- read the log only after "[Inferior 1 ... detached]".
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = 60
set $b = 0x962f90

# --- 4 hardware watchpoints (the whole DR budget) ---
watch *(int *)0x962fd0
commands
  silent
  set $n = $n + 1
  printf "WP %d MIN40 eip=%#x new=%d d0=%d q50=%d c0=%d f0=%d e0=%d eax=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", \
    $n, $eip, *(int *)0x962fd0, *(int *)0x963060, *(int *)0x962fe0, *(int *)0x963050, \
    *(int *)0x963080, *(int *)0x963070, $eax, $ecx, $edx, $esi, $edi
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x962fe0
commands
  silent
  set $n = $n + 1
  printf "WP %d QUEUE50 eip=%#x new=%d min40=%d\n", $n, $eip, *(int *)0x962fe0, *(int *)0x962fd0
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x963060
commands
  silent
  set $n = $n + 1
  printf "WP %d INCOME_D0 eip=%#x new=%d c0=%d f0=%d e0=%d min40=%d\n", \
    $n, $eip, *(int *)0x963060, *(int *)0x963050, *(int *)0x963080, *(int *)0x963070, \
    *(int *)0x962fd0
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x963028
commands
  silent
  set $n = $n + 1
  printf "WP %d MIRROR98 eip=%#x new=%d min40=%d\n", $n, $eip, *(int *)0x963028, *(int *)0x962fd0
  if $n >= $cap
    printf "CAP\n"
    detach
    quit
  end
  continue
end

# --- int3 sites inside FUN_004ef6d0, OUR base only (0x8f0d60 = current base record) ---
break *0x4ef7f1
commands
  silent
  set $n = $n + 1
  if *(int *)0x8f0d60 == $b
    printf "SITE %d INCOME-ADD eip=0x4ef7f1 min40=%d d0=%d q50=%d\n", \
      $n, *(int *)0x962fd0, *(int *)0x963060, *(int *)0x962fe0
  end
  if $n >= $cap
    detach
    quit
  end
  continue
end

break *0x4efed5
commands
  silent
  set $n = $n + 1
  if *(int *)0x8f0d60 == $b
    printf "SITE %d SPEND-A eip=0x4efed5 min40=%d edi=%d ebx=%d item=%d q50=%d\n", \
      $n, *(int *)0x962fd0, $edi, $ebx, *(int *)($ebp - 0x28), *(int *)0x962fe0
  end
  if $n >= $cap
    detach
    quit
  end
  continue
end

break *0x4efee0
commands
  silent
  set $n = $n + 1
  if *(int *)0x8f0d60 == $b
    printf "SITE %d CLAMP-A-GATE eip=0x4efee0 min40=%d d0=%d cap=%d mask=%#x ourbit=%#x\n", \
      $n, *(int *)0x962fd0, *(int *)0x963060, *(int *)0x92a370, *(int *)0x985b10, \
      *(int *)0x985b10 & 0x8
  end
  if $n >= $cap
    detach
    quit
  end
  continue
end

break *0x4f0ca1
commands
  silent
  set $n = $n + 1
  if *(int *)0x8f0d60 == $b
    printf "SITE %d SPEND-B eip=0x4f0ca1 min40=%d edi=%d ebx=%d item=%d q50=%d\n", \
      $n, *(int *)0x962fd0, $edi, $ebx, *(int *)($ebp - 0x28), *(int *)0x962fe0
  end
  if $n >= $cap
    detach
    quit
  end
  continue
end

break *0x4f1e3f
commands
  silent
  set $n = $n + 1
  if *(int *)0x8f0d60 == $b
    printf "SITE %d QUEUE-DRAIN eip=0x4f1e3f min40=%d item=%d q50=%d\n", \
      $n, *(int *)0x962fd0, *(int *)($ebp - 0x28), *(int *)0x962fe0
  end
  if $n >= $cap
    detach
    quit
  end
  continue
end

# touched once here so a bad address fails now, not 3 minutes into the round
printf "SELFTEST %#x %#x %#x %#x %#x %#x %#x %#x\n", \
  0x962fd0, 0x963060, 0x962fe0, 0x963028, 0x963050, 0x963080, 0x963070, 0x92a370
printf "STATE year=%d cur=%d min40=%d d0=%d q50=%d c0=%d f0=%d e0=%d mask=%#x\n", \
  *(int *)0x985b00, *(int *)0x985dcc, *(int *)0x962fd0, *(int *)0x963060, \
  *(int *)0x962fe0, *(int *)0x963050, *(int *)0x963080, *(int *)0x963070, *(int *)0x985b10
continue
