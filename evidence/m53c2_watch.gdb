# M53c-2: WHICH of the pipeline's three FUN_004ef5d0 ("pop the head item") call sites fires on
# a positive completion? Run 1 (m53c) proved the pop happens on OUR base right after CLAMP1
# (WP50 eip=0x4ef62e: +0x50 2->3; WP4C eip=0x4ef648: +0x4c 1->0) but armed no bp at the call
# sites. This run arms all three (0x4ef992 / 0x4f037b / 0x4f0f46) plus the same NAME-conditioned
# QPIPE/QCOMPLET/CLAMP1 and a single hw watch on +0x50.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $nwp50 = 0
set $nq = 0
set $nc = 0
set $nyear = 0
set $ncl = 0
set $npop = 0

watch *(int *)(0x962d30 + 0x50)
commands
  set $nwp50 = $nwp50 + 1
  printf "WP50 %d eip=%#x new=%d f54=%d f4c=%d f44=%d name_at=%s ours_at=%d\n", $nwp50, $eip, *(int *)(0x962d30 + 0x50), *(int *)(0x962d30 + 0x54), *(int *)(0x962d30 + 0x4c), *(int *)(0x962d30 + 0x44), (char *)(0x962d30 + 19), *(int *)0x8f0d60 == 0x962d30
  continue
end

break *0x51f554
commands
  silent
  set $nyear = $nyear + 1
  printf "YEAR %d year=%d cur=%d nb=%d\n", $nyear, *(int *)0x985b00, *(int *)0x985dcc, *(int *)0x985af4
  continue
end
break *0x4ef6d0 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nq = $nq + 1
  printf "QPIPE %d name=%s f50=%d f54=%d f4c=%d f44=%d st=%d fcc=%d d0=%d\n", $nq, (char *)(*(int *)0x8f0d60 + 19), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x54), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x44), *(int *)(*(int *)0x8f0d60 + 0x40), *(int *)(*(int *)0x8f0d60 + 0xcc), *(int *)(*(int *)0x8f0d60 + 0xd0)
  continue
end
break *0x4efe41 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nc = $nc + 1
  printf "QCOMPLET %d f50=%d f4c=%d st=%d ebx=%d\n", $nc, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x40), $ebx
  continue
end
break *0x4eff20 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $ncl = $ncl + 1
  printf "CLAMP1 %d st=%d f50=%d f4c=%d\n", $ncl, *(int *)($esi + 0x40), *(int *)($esi + 0x50), *(int *)($esi + 0x4c)
  continue
end
break *0x4ef992 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $npop = $npop + 1
  printf "POP_EARLY %d f50=%d f4c=%d m10=%d\n", $npop, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x10)
  continue
end
break *0x4f037b if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $npop = $npop + 1
  printf "POP_MID %d f50=%d f4c=%d\n", $npop, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c)
  continue
end
break *0x4f0f46 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $npop = $npop + 1
  printf "POP_LATE %d f50=%d f4c=%d\n", $npop, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c)
  continue
end

printf "SELFTEST addr=%#x f50=%d f54=%d f4c=%d st=%d name=%s\n", 0x962d30, *(int *)(0x962d30 + 0x50), *(int *)(0x962d30 + 0x54), *(int *)(0x962d30 + 0x4c), *(int *)(0x962d30 + 0x40), (char *)(0x962d30 + 19)
printf "ARMED\n"
continue
