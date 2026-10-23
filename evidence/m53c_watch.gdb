# M53c instrument: WHO advances base+0x50 after a POSITIVE completion?
# Static (see evidence/m53c_*): the ONLY +0x50 writers in the corpus are FUN_004e5560 (the setter:
# head := new AND per-player item count old-1 / new+1 at 0x94de84+owner*0x20bc+id), FUN_004e46f0 /
# FUN_004e47d0 (base init autocalc), FUN_00417ee0 (UI enqueue) and the clears 0x4f1e3f (pipeline
# tail, negative-only), FUN_00507ef0, FUN_005437d0. FUN_004e5560 has exactly ONE caller chain:
# FUN_004e5ae0(base,0) = "re-pick via FUN_004f6030", called from the pipeline at 0x4ef87e / 0x4f0589
# / 0x4f08d4 / 0x4f09b6 / 0x4f1e01 / 0x4f21b8 (M53a's disasm dump stopped at 0x4f1d5d, which is why
# the tail sites 0x4f1e01/0x4f1e3f/0x4f21b8 looked absent). Gates: 0x4f1e01 needs (base+0x38 bit0 AND
# bit31 AND [ebp-0x10]==0) OR (1<<owner)&mask==0; 0x4f1e3f needs owner IN mask AND NOT(f38&0x80000001
# ==0x80000001) AND head == -[ebp-0x30] AND +0x4c==0. Our base has f38=0x00dfbe41 (bit31 clear) and
# owner 3 IN mask 0xff08, so the prediction is: NEITHER fires -> the head persists.
# Live test: 2-item queue (+0x50=2 Scout Patrol, +0x54=3 Transport Foil, +0x4c=1), storage 200.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $nwp50 = 0
set $nwp4c = 0
set $nq = 0
set $nc = 0
set $nyear = 0
set $nsp = 0
set $ncl = 0
set $nrp = 0
set $ndrain = 0
set $n5ae0 = 0
set $n5560 = 0
set $n7ef0 = 0
set $n37d0 = 0
set $nenq = 0

# ---- hardware watchpoints FIRST (2 of 4 i386 DR slots; the +0x3c story is closed, so +0x50 and
# +0x4c take the slots). $eip sits just PAST the store; name_at detects an array slide.
watch *(int *)(0x962d30 + 0x50)
commands
  set $nwp50 = $nwp50 + 1
  printf "WP50 %d eip=%#x new=%d f54=%d f4c=%d f44=%d name_at=%s cb=%#x ours_at=%d\n", $nwp50, $eip, *(int *)(0x962d30 + 0x50), *(int *)(0x962d30 + 0x54), *(int *)(0x962d30 + 0x4c), *(int *)(0x962d30 + 0x44), (char *)(0x962d30 + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == 0x962d30
  continue
end
watch *(int *)(0x962d30 + 0x4c)
commands
  set $nwp4c = $nwp4c + 1
  printf "WP4C %d eip=%#x new=%d f50=%d f54=%d name_at=%s cb=%#x ours_at=%d\n", $nwp4c, $eip, *(int *)(0x962d30 + 0x4c), *(int *)(0x962d30 + 0x50), *(int *)(0x962d30 + 0x54), (char *)(0x962d30 + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == 0x962d30
  continue
end

# ---- round marker ----
break *0x51f554
commands
  silent
  set $nyear = $nyear + 1
  printf "YEAR %d year=%d turn=%d cur=%d nb=%d\n", $nyear, *(int *)0x985b00, *(int *)0x985afc, *(int *)0x985dcc, *(int *)0x985af4
  continue
end

# ---- OUR base: pipeline entry + completion (NAME-conditioned, slide-proof) ----
break *0x4ef6d0 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nq = $nq + 1
  printf "QPIPE %d name=%s f50=%d f54=%d f58=%d f5c=%d f4c=%d f44=%d f68=%d st=%d f3c=%d fcc=%d d0=%d f38=%#x\n", $nq, (char *)(*(int *)0x8f0d60 + 19), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x54), *(int *)(*(int *)0x8f0d60 + 0x58), *(int *)(*(int *)0x8f0d60 + 0x5c), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x44), *(int *)(*(int *)0x8f0d60 + 0x68), *(int *)(*(int *)0x8f0d60 + 0x40), *(int *)(*(int *)0x8f0d60 + 0x3c), *(int *)(*(int *)0x8f0d60 + 0xcc), *(int *)(*(int *)0x8f0d60 + 0xd0), *(int *)(*(int *)0x8f0d60 + 0x38)
  continue
end
break *0x4efe41 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nc = $nc + 1
  printf "QCOMPLET %d name=%s f50=%d f54=%d f4c=%d f44=%d st=%d ebx=%d m1c=%d m30=%d m10=%d\n", $nc, (char *)(*(int *)0x8f0d60 + 19), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x54), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x44), *(int *)(*(int *)0x8f0d60 + 0x40), $ebx, *(int *)($ebp - 0x1c), *(int *)($ebp - 0x30), *(int *)($ebp - 0x10)
  continue
end
break *0x4efed8 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nsp = $nsp + 1
  printf "SPENDA %d st=%d cost_edi=%d f50=%d f4c=%d\n", $nsp, *(int *)(*(int *)0x8f0d60 + 0x40), $edi, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c)
  continue
end
break *0x4eff20 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $ncl = $ncl + 1
  printf "CLAMP1 %d esi=%#x st=%d f50=%d f4c=%d\n", $ncl, $esi, *(int *)($esi + 0x40), *(int *)($esi + 0x50), *(int *)($esi + 0x4c)
  continue
end

# ---- the six pipeline re-pick call sites (0x4e5ae0) + the tail clear (0x4f1e3f) ----
break *0x4ef87e if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_EARLY %d f50=%d f4c=%d f38=%#x m10=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x38), *(int *)($ebp - 0x10)
  continue
end
break *0x4f0589 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_A %d f50=%d f4c=%d f38=%#x edi=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x38), $edi
  continue
end
break *0x4f08d4 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_B %d f50=%d f4c=%d m30=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end
break *0x4f09b6 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_C %d f50=%d f4c=%d m30=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end
break *0x4f1e01 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_TAIL %d f50=%d f4c=%d f38=%#x m10=%d m2c=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x38), *(int *)($ebp - 0x10), *(int *)($ebp - 0x2c)
  continue
end
break *0x4f21b8 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nrp = $nrp + 1
  printf "REPICK_PROJ %d f50=%d f4c=%d m30=%d\n", $nrp, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end
break *0x4f1e3f if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $ndrain = $ndrain + 1
  printf "QDRAIN %d f50=%d f54=%d f4c=%d m30=%d\n", $ndrain, *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x54), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)($ebp - 0x30)
  continue
end

# ---- the writers themselves (any base; ours=1 marks OUR record) ----
break *0x4e5ae0
commands
  silent
  set $n5ae0 = $n5ae0 + 1
  printf "SET_REPICK %d base_idx=%d param2=%d ours=%d head=%d f4c=%d cb_idx=%d\n", $n5ae0, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c), *(int *)0x68cbb0
  continue
end
break *0x4e5560
commands
  silent
  set $n5560 = $n5560 + 1
  printf "SET_HEAD %d base_idx=%d new=%d ours=%d OLD_head=%d OLD_f4c=%d cb_idx=%d\n", $n5560, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c), *(int *)0x68cbb0
  continue
end
break *0x507ef0
commands
  silent
  set $n7ef0 = $n7ef0 + 1
  printf "CLR_507EF0 %d p1=%d p2=%#x ours=%d head=%d f4c=%d\n", $n7ef0, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c)
  continue
end
break *0x5437d0
commands
  silent
  set $n37d0 = $n37d0 + 1
  printf "CLR_5437D0 %d p1=%d p2=%#x ours=%d head=%d f4c=%d\n", $n37d0, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 4) == *(int *)0x68cbb0, *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x50), *(int *)(0x95da10 + *(int *)($esp + 4) * 0x130 + 0x4c)
  continue
end
break *0x417ee0
commands
  silent
  set $nenq = $nenq + 1
  printf "ENQ_417EE0 %d p1=%#x p2=%#x p3=%#x\n", $nenq, *(int *)($esp + 4), *(int *)($esp + 8), *(int *)($esp + 0xc)
  continue
end

# SELFTEST: touch every literal address + the name pointer at script time, pre-continue.
printf "SELFTEST addr=%#x owner=%d f38=%#x f3c=%d st=%d f50=%d f54=%d f4c=%d name=%s\n", 0x962d30, *(unsigned char *)(0x962d30 + 4), *(int *)(0x962d30 + 0x38), *(int *)(0x962d30 + 0x3c), *(int *)(0x962d30 + 0x40), *(int *)(0x962d30 + 0x50), *(int *)(0x962d30 + 0x54), *(int *)(0x962d30 + 0x4c), (char *)(0x962d30 + 19)
printf "ARMED\n"
continue
