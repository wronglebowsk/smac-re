# M48 option 1: MINERAL-economy write provenance.
#   0x962fd0 = our base record (idx 72 @ 0x95da10+72*0x130) +0x40 mineral accumulator
#   0x962fe0 = same record +0x50  (the production-queue head: FUN_004ef6d0 loops
#              while *(int*)(base+0x50) != -0x26, so this is the queued item id)
#   0x953884 = our faction record (0x94d650 + 3*0x20bc) +0 ENERGY  (M47 control)
#   break *0x51f554 = the mission-year store proven in M47 (inside FUN_0051f320) --
#              used as the ROUND marker, NOT as a watch (4 DR slots total).
# Read-only: no pokes, no calls.  Every hit prints the base's own identity
# (owner/x/y) so a base-array compaction mid-run cannot masquerade as our data.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $nmin = 0
set $nq = 0
set $ne = 0
set $nr = 0
set $lasty = -99999

break *0x51f554
commands
  silent
  set $nr = $nr + 1
  if *(int *)0x985b00 != $lasty
    set $lasty = *(int *)0x985b00
    printf "ROUND n=%d year=%d turn=%d cur=%d nbases=%d nrg3=%d led3=%d gross=%d upkeep=%d net=%d\n", $nr, *(int *)0x985b00, *(int *)0x985afc, *(int *)0x985dcc, *(int *)0x985af4, *(int *)0x953884, *(int *)0x953888, *(int *)0x745734, *(int *)0x744f28, *(int *)0x7457dc
    set $i = 0
    set $b = 0x95da10
    while $i < *(int *)0x985af4
      if *(char *)($b + 4) == 3
        printf "OURBASE idx=%d addr=%#x x=%d y=%d pop=%d min40=%d f44=%d f50=%d mir98=%d f68=%d f90=%d c4=%d d4=%d fc=%d b104=%d b108=%d\n", $i, $b, *(unsigned short *)$b, *(unsigned short *)($b + 2), *(unsigned char *)($b + 6), *(int *)($b + 0x40), *(int *)($b + 0x44), *(int *)($b + 0x50), *(int *)($b + 0x98), *(int *)($b + 0xd0), *(int *)($b + 0x120), *(int *)($b + 0xc4), *(int *)($b + 0xd4), *(int *)($b + 0xfc), *(int *)($b + 0x104), *(int *)($b + 0x108)
      end
      set $b = $b + 0x130
      set $i = $i + 1
    end
    set $i = 0
    set $u = 0x933278
    set $nu = 0
    while $i < 300
      if *(char *)($u + 14) == 3
        if *(unsigned short *)$u != 0xffff
          set $nu = $nu + 1
          printf "UNIT idx=%d type=%d x=%d y=%d order=%d mpused=%d home=%d\n", $i, *(unsigned char *)($u + 10), *(unsigned short *)$u, *(unsigned short *)($u + 2), *(unsigned char *)($u + 17), *(unsigned char *)($u + 40), *(unsigned short *)($u + 46)
        end
      end
      set $u = $u + 52
      set $i = $i + 1
    end
    printf "UNITS n=%d\n", $nu
  else
    printf "YEARTORE n=%d eip=%#x year=%d\n", $nr, $eip, *(int *)0x985b00
  end
  continue
end

watch *(int *)0x962fd0
commands
  silent
  set $nmin = $nmin + 1
  printf "WMIN n=%d eip=%#x val=%d own=%d x=%d y=%d f50=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $nmin, $eip, *(int *)0x962fd0, *(char *)0x962f94, *(unsigned short *)0x962f90, *(unsigned short *)0x962f92, *(int *)0x962fe0, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $nmin >= 40
    printf "WMIN-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x962fe0
commands
  silent
  set $nq = $nq + 1
  printf "WQUEUE n=%d eip=%#x val=%d own=%d x=%d y=%d min40=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $nq, $eip, *(int *)0x962fe0, *(char *)0x962f94, *(unsigned short *)0x962f90, *(unsigned short *)0x962f92, *(int *)0x962fd0, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $nq >= 40
    printf "WQUEUE-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x953884
commands
  silent
  set $ne = $ne + 1
  printf "WENERGY n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $ne, $eip, *(int *)0x953884, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $ne >= 40
    printf "WENERGY-CAP\n"
    detach
    quit
  end
  continue
end

printf "ARMED min40=%#x queue50=%#x energy=%#x yearbp=%#x\n", 0x962fd0, 0x962fe0, 0x953884, 0x51f554
continue
