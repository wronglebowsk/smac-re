# M51a instrument: does 0x4f26e0's gate early-return for OUR base, and WHICH instruction writes
# base+0x3c (production progress) and base+0x40 (mineral storage)?
# Identity anchor = the base NAME string at base+0x13 (0x4f5a70 passes DAT_008f0d60+0x13 to the
# rename/announce panes), printed at EVERY hit: the base array SLIDES (compaction moves records)
# and owner bytes change, so a bare index or a bare owner test is not a stable identity.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $sw_p = -1
set $sw_i = -1
set $sw_n = 0
set $nsweep = 0
set $nvis = 0
set $nyear = 0
set $ngate = 0
set $nflag = 0
set $npast = 0
set $nconv = 0
set $nwp = 0
set $n40 = 0
set $n3c = 0
set $nedi = 0
set $nq = 0
set $nc = 0

# ---- hardware watchpoints on OUR located record FIRST (the exhaustive net; literal addrs, armed
# after the pokes per M33). gdb prints Old/New itself; $eip sits just PAST the store. name_at is
# printed so a SLIDE of the array (another record moving into this slot) is visible in the log.
# ORDER MATTERS: gdb 17.1 on this i386-under-Wine target has a small debug-register budget and the
# 24 breakpoints below eat it, so watchpoints must claim their DR slots before the bps are inserted
# (m51a attempt 1 died with "Could not insert hardware watchpoint 26 / too many hardware
# breakpoints/watchpoints" and detached with zero hits).
watch *(int *)(0x962d30 + 0x3c)
commands
  set $nwp = $nwp + 1
  printf "WP3C %d eip=%#x new=%d name_at=%s curbase=%#x ours_at=%d\n", $nwp, $eip, *(int *)(0x962d30 + 0x3c), (char *)(0x962d30 + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == 0x962d30
  continue
end
watch *(int *)(0x962d30 + 0x40)
commands
  set $nwp = $nwp + 1
  printf "WP40 %d eip=%#x new=%d name_at=%s curbase=%#x ours_at=%d\n", $nwp, $eip, *(int *)(0x962d30 + 0x40), (char *)(0x962d30 + 19), *(int *)0x8f0d60, *(int *)0x8f0d60 == 0x962d30
  continue
end
# (m51a attempts 1-2: THREE hw watchpoints registered fine but gdb failed to insert one at the
# first resume -- "Could not insert hardware watchpoint 2 / too many hardware breakpoints/watchpoints"
# -- and the name watch at +19 was unaligned anyway; name= is printed at every bp hit, so the slide
# detector does not need a DR slot. TWO watchpoints = 2 of the 4 i386 DR slots.)

# ---- sweep identification (M50b instrument, kept) ----
# 0x520540(player): per-player sweep entry
break *0x520540
commands
  silent
  set $nsweep = $nsweep + 1
  set $sw_p = *(int *)($esp + 4)
  set $sw_i = 0
  set $sw_n = 0
  printf "SWEEP %d p=%d nb_entry=%d\n", $nsweep, $sw_p, *(int *)0x985af4
  continue
end

# 0x5206d3: call 0x4f5a70 for a base whose owner byte == player (ebx = base index)
break *0x5206d3
commands
  silent
  set $sw_n = $sw_n + 1
  set $nvis = $nvis + 1
  set $b = 0x95da10 + $ebx * 0x130
  printf "VISIT %d p=%d idx=%d owner=%d nb=%d ours=%d f3c=%d st=%d f38=%#x name=%s\n", $nvis, $sw_p, $ebx, *(unsigned char *)($b + 4), *(int *)0x985af4, $b == 0x962d30, *(int *)($b + 0x3c), *(int *)($b + 0x40), *(int *)($b + 0x38), (char *)($b + 19)
  if $b == 0x962d30
    bt 2
  end
  continue
end

# 0x5206f9: loop back edge (records how far the pass got)
break *0x5206f9
commands
  silent
  set $sw_i = $ebx - 1
  continue
end

# 0x5206fd: loop exit (or the n_bases<=0 fast path)
break *0x5206fd
commands
  silent
  printf "SWEEPEND p=%d last_idx=%d visits=%d nb_now=%d\n", $sw_p, $sw_i, $sw_n, *(int *)0x985af4
  continue
end

# 0x51f554: the year store - fires BETWEEN passes (M50b)
break *0x51f554
commands
  silent
  set $nyear = $nyear + 1
  printf "YEAR %d mid_p=%d mid_idx=%d mid_visits=%d nb=%d cur=%d\n", $nyear, $sw_p, $sw_i, $sw_n, *(int *)0x985af4, *(int *)0x985dcc
  continue
end

# ---- inside 0x4f26e0 (mineral<->energy conversion step, called from 0x4f5a70 at 0x4f5ae1) ----
# 0x4f2705 is the instruction AFTER the event-owner test 0x4f26ff (test BYTE ds:0x985b10, 1<<owner)
# and BEFORE the je at 0x4f2708, so it executes on EVERY call: owner==3 (mask low byte 0x08) falls
# through to the flag test, every other owner je's straight to the storage check 0x4f2724.
# edx = curbase = *(int*)0x8f0d60, loaded at 0x4f26e6 by the callee itself.
break *0x4f2705
commands
  silent
  set $ngate = $ngate + 1
  printf "GATE %d eip=%#x ebp=%#x curbase=%#x idx=%d owner=%d f38=%#x f3c=%d st=%d ours=%d name=%s\n", $ngate, $eip, $ebp, $edx, ($edx - 0x95da10) / 0x130, *(unsigned char *)($edx + 4), *(int *)($edx + 0x38), *(int *)($edx + 0x3c), *(int *)($edx + 0x40), $edx == 0x962d30, (char *)($edx + 19)
  continue
end

# 0x4f271e: jne 0x4f2e97 - REACHED ONLY BY EVENT OWNERS (everyone else je'd at 0x4f2708).
# ecx != 0 means the branch IS taken = 0x4f26e0 returns before any store. ecx = ((~f38>>0x1a)&0x20)
# | (~f38 & 0x20); f38 is the constant 0x00dfbe41 in every record, so ecx = 0x20 here always.
break *0x4f271e
commands
  silent
  set $nflag = $nflag + 1
  printf "FLAGTEST %d eip=%#x ebp=%#x ecx=%#x curbase=%#x owner=%d ours=%d name=%s\n", $nflag, $eip, $ebp, $ecx, $edx, *(unsigned char *)($edx + 4), $edx == 0x962d30, (char *)($edx + 19)
  continue
end

# 0x4f2724: the storage check, the ONLY way to reach the conversion body. A FLAGTEST line for frame
# ebp=X with NO PASTFLAG line for ebp=X proves the early return by execution (site absent), not by
# reading memory afterwards.
break *0x4f2724
commands
  silent
  set $npast = $npast + 1
  printf "PASTFLAG %d eip=%#x ebp=%#x curbase=%#x owner=%d st=%d ours=%d name=%s\n", $npast, $eip, $ebp, $edx, *(unsigned char *)($edx + 4), *(int *)($edx + 0x40), $edx == 0x962d30, (char *)($edx + 19)
  continue
end

# 0x4f2d7d: CONVST store [edi+0x40]=eax (edi = curbase set at 0x4f2d30, eax = NEW value).
break *0x4f2d7d
commands
  silent
  set $nconv = $nconv + 1
  printf "CONVST %d eip=%#x ebp=%#x store_to=%#x idx=%d owner=%d f38=%#x f3c=%d old40=%d new=%d ours=%d name=%s\n", $nconv, $eip, $ebp, $edi, ($edi - 0x95da10) / 0x130, *(unsigned char *)($edi + 4), *(int *)($edi + 0x38), *(int *)($edi + 0x3c), *(int *)($edi + 0x40), $eax, $edi == 0x962d30, (char *)($edi + 19)
  continue
end

# ---- EVERY static writer of base+0x40 in the per-base chain (0x4f5a70 and its callees) ----
# Conditional on the store's target register being OUR located record, so the print is identity-
# anchored by the name at the target and immune to a mid-round slide of the array.
break *0x4ef7f6 if $eax == 0x962d30
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_IADD %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d d0=%d cb=%#x\n", $n40, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x40), $edx, *(int *)($eax + 0xd0), *(int *)0x8f0d60
  continue
end
# ---- M52b: edi PROVENANCE chain. edi is the SPENDA subtrahend (0x4efedb `sub esi,edi`), and M49a's
# "edi = sweep-entry index" is statically FALSE: 0x4f5aa9 `mov edi,edx` takes edx from
# `mov dl,BYTE PTR [ecx+0x4]` at 0x4f5a9c = the OWNER BYTE. These bps trace every candidate writer of
# edi on the per-base path so one run pins where the observed 10 comes from. Conditioned on the
# current-base global (0x8f0d60) because edi/eax are already clobbered at several of these sites.
break *0x4f5aa9
commands
  silent
  set $nedi = $nedi + 1
  printf "EDI_ENTRY %d eip=%#x idx=%d owner_byte=%d cb=%#x name=%s\n", $nedi, $eip, *(int *)0x68cbb0, $edx, *(int *)0x8f0d60, (char *)(*(int *)0x8f0d60 + 19)
  continue
end
break *0x4ef88b if *(int *)0x8f0d60 == 0x962d30
commands
  silent
  set $nedi = $nedi + 1
  printf "EDI_QGATE %d eip=%#x q50=%d st=%d name=%s\n", $nedi, $eip, *(int *)($eax + 0x50), *(int *)($eax + 0x40), (char *)($eax + 19)
  continue
end
break *0x4ef8e2 if *(int *)0x8f0d60 == 0x962d30
commands
  silent
  set $nedi = $nedi + 1
  printf "EDI_NEGPATH %d eip=%#x factor_eax=%d qabs=%d name=%s\n", $nedi, $eip, $eax, *(int *)($ebp - 0x30), (char *)(*(int *)0x8f0d60 + 19)
  continue
end
break *0x4ef8ed if *(int *)0x8f0d60 == 0x962d30
commands
  silent
  set $nedi = $nedi + 1
  printf "EDI_NEGMUL %d eip=%#x edi_before=%d edx=%d tbl=%d name=%s\n", $nedi, $eip, $edi, $edx, *(int *)($edx + 0x984d44), (char *)(*(int *)0x8f0d60 + 19)
  continue
end
break *0x4efa4b if *(int *)0x8f0d60 == 0x962d30
commands
  silent
  set $nedi = $nedi + 1
  printf "EDI_POSPATH %d eip=%#x factor_eax=%d q50_m18=%d name=%s\n", $nedi, $eip, $eax, *(int *)($ebp - 0x18), (char *)(*(int *)0x8f0d60 + 19)
  continue
end
break *0x4efa52 if *(int *)0x8f0d60 == 0x962d30
commands
  silent
  set $nedi = $nedi + 1
  printf "EDI_POSMUL %d eip=%#x edi_before=%d ret_5ac950=%d name=%s\n", $nedi, $eip, $edi, $eax, (char *)(*(int *)0x8f0d60 + 19)
  continue
end
break *0x4efed8 if *(int *)0x8f0d60 == 0x962d30
commands
  silent
  set $nedi = $nedi + 1
  printf "EDI_SPENDA %d eip=%#x edi=%d st=%d q50=%d m1c=%d m2c=%d retaddr=%#x name=%s\n", $nedi, $eip, $edi, *(int *)($ecx + 0x40), *(int *)($ecx + 0x50), *(int *)($ebp - 0x1c), *(int *)($ebp - 0x2c), *(void **)$esp, (char *)($ecx + 19)
  continue
end
break *0x4efedd if $ecx == 0x962d30
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_SPENDA %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d edi=%d cb=%#x\n", $n40, $eip, $ebp, $ecx, (char *)($ecx + 19), *(int *)($ecx + 0x40), $esi, $edi, *(int *)0x8f0d60
  continue
end
break *0x4eff20 if $esi == 0x962d30
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_CLAMP1 %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cap=%d ownmask=%d d0=%d cb=%#x\n", $n40, $eip, $ebp, $esi, (char *)($esi + 19), *(int *)($esi + 0x40), $eax, *(int *)0x92a370, *(unsigned char *)($esi + 4), *(int *)($esi + 0xd0), *(int *)0x8f0d60
  continue
end
break *0x4f0ca6 if $edx == 0x962d30
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_SPENDB %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d edi=%d cb=%#x\n", $n40, $eip, $ebp, $edx, (char *)($edx + 19), *(int *)($edx + 0x40), $esi, $edi, *(int *)0x8f0d60
  continue
end
break *0x4f0ce9 if $esi == 0x962d30
commands
  silent
  set $n40 = $n40 + 1
  printf "W40_CLAMP2 %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cap=%d cb=%#x\n", $n40, $eip, $ebp, $esi, (char *)($esi + 19), *(int *)($esi + 0x40), $eax, *(int *)0x92a370, *(int *)0x8f0d60
  continue
end

# ---- EVERY static writer of base+0x3c in the per-base chain ----
# 0x4e92c0 tail: +0x3c clamped to 0 (rate>=0) or -1 (rate<0); +0xcc (rate) is computed at 0x4e937b
break *0x4e9397 if $eax == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_SET0 %d eip=%#x ebp=%#x target=%#x name=%s old=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), *(int *)($eax + 0xcc), *(int *)0x8f0d60
  continue
end
break *0x4e93a4 if $eax == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_SETM1 %d eip=%#x ebp=%#x target=%#x name=%s old=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), *(int *)($eax + 0xcc), *(int *)0x8f0d60
  continue
end
# 0x4ee410 (called by 0x4f5a70 right AFTER 0x4f26e0): the production-progress accumulator
break *0x4ee56b if $eax == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410A %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), $ecx, *(int *)($eax + 0xcc), *(int *)0x8f0d60
  continue
end
break *0x4ee709 if $eax == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410B %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), $ebx, *(int *)0x8f0d60
  continue
end
break *0x4ee72c if $edi == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410C %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cb=%#x\n", $n3c, $eip, $ebp, $edi, (char *)($edi + 19), *(int *)($edi + 0x3c), $ebx, *(int *)0x8f0d60
  continue
end
break *0x4ee82f if $ecx == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410D %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d pop=%d scale=%d ada8=%d fac17=%d f30b=%d cb=%#x\n", $n3c, $eip, $ebp, $ecx, (char *)($ecx + 19), *(int *)($ecx + 0x3c), $eax, *(unsigned char *)($ecx + 6), *(int *)0x92a290, *(int *)0x92ada8, *(int *)(0x94d694 + 0x20bc * (unsigned int)(*(unsigned char *)($ecx + 4))), *(unsigned char *)($ecx + 0x30), *(int *)0x8f0d60
  continue
end
break *0x4ee869 if $edi == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410ZERO %d eip=%#x ebp=%#x target=%#x name=%s old=%d cb=%#x\n", $n3c, $eip, $ebp, $edi, (char *)($edi + 19), *(int *)($edi + 0x3c), *(int *)0x8f0d60
  continue
end
break *0x4ee8c7 if $edi == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_E410ACCR %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d cc=%d cb=%#x\n", $n3c, $eip, $ebp, $edi, (char *)($edi + 19), *(int *)($edi + 0x3c), $esi, *(int *)($edi + 0xcc), *(int *)0x8f0d60
  continue
end
# 0x4ef6d0 pipeline: stockpile-gated progress bump (non-event owners, 0x985aec>3) and pod clamp
break *0x4efb31 if $ecx == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_PIPE %d eip=%#x ebp=%#x target=%#x name=%s old=%d new=%d stock=%d cb=%#x\n", $n3c, $eip, $ebp, $ecx, (char *)($ecx + 19), *(int *)($ecx + 0x3c), $edx, *(int *)0x985aec, *(int *)0x8f0d60
  continue
end
break *0x4f022b if $eax == 0x962d30
commands
  silent
  set $n3c = $n3c + 1
  printf "W3C_PODCLAMP %d eip=%#x ebp=%#x target=%#x name=%s old=%d cb=%#x\n", $n3c, $eip, $ebp, $eax, (char *)($eax + 19), *(int *)($eax + 0x3c), *(int *)0x8f0d60
  continue
end

# ---- M53a: the base+0x50 queue record, OURS only. PIPE entry 0x4ef6d0 and COMPLET 0x4efe41.
# Identity = NAME test through the current-base global (the array SLIDES; a literal addr is not
# stable across rounds). "Climactic Research" = dword@+0x13 0x6d696c43 + dword@+0x17 0x69746361.
# Prints the six queue-block fields the milestone asks for; QCOMPLET adds the ebp scratch locals.
break *0x4ef6d0 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nq = $nq + 1
  printf "QPIPE %d name=%s f50=%d f44=%d f4c=%d f68=%d fc0=%d fcc=%d st=%d f3c=%d d0=%d\n", $nq, (char *)(*(int *)0x8f0d60 + 19), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x44), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x68), *(int *)(*(int *)0x8f0d60 + 0xc0), *(int *)(*(int *)0x8f0d60 + 0xcc), *(int *)(*(int *)0x8f0d60 + 0x40), *(int *)(*(int *)0x8f0d60 + 0x3c), *(int *)(*(int *)0x8f0d60 + 0xd0)
  continue
end
break *0x4efe41 if *(int *)(*(int *)0x8f0d60 + 0x13) == 0x6d696c43 && *(int *)(*(int *)0x8f0d60 + 0x17) == 0x69746361
commands
  silent
  set $nc = $nc + 1
  printf "QCOMPLET %d name=%s f50=%d f44=%d f4c=%d f68=%d fc0=%d fcc=%d st=%d ebx=%d m1c=%d m2c=%d m18=%d m30=%d\n", $nc, (char *)(*(int *)0x8f0d60 + 19), *(int *)(*(int *)0x8f0d60 + 0x50), *(int *)(*(int *)0x8f0d60 + 0x44), *(int *)(*(int *)0x8f0d60 + 0x4c), *(int *)(*(int *)0x8f0d60 + 0x68), *(int *)(*(int *)0x8f0d60 + 0xc0), *(int *)(*(int *)0x8f0d60 + 0xcc), *(int *)(*(int *)0x8f0d60 + 0x40), $ebx, *(int *)($ebp - 0x1c), *(int *)($ebp - 0x2c), *(int *)($ebp - 0x18), *(int *)($ebp - 0x30)
  continue
end

# SELFTEST: touch every literal address + the name pointer at script time, pre-continue.
printf "SELFTEST addr=%#x owner=%d f38=%#x f3c=%d st=%d name=%s\n", 0x962d30, *(unsigned char *)(0x962d30 + 4), *(int *)(0x962d30 + 0x38), *(int *)(0x962d30 + 0x3c), *(int *)(0x962d30 + 0x40), (char *)(0x962d30 + 19)
printf "ARMED\n"
continue
