# M48d generated instrument (do not hand-edit; driver writes this)
# our base record 0x962e60  min40=0x962ea0 q50=0x962eb0 d0=0x962f30  energy=0x953884
# slide window [0x962d30, 0x9630c0] on the compaction store 0x64bfa3
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $n = 0
set $npipe = 0
set $npane = 0
set $nwp = 0
set $prev_year = -99

break *0x51f554
commands
  silent
  set $y = *(int *)0x985b00
  if $y != $prev_year
    set $prev_year = $y
    set $nb = *(int *)0x985af4
    set $found = 0
    set $i = 0
    while $i < $nb
      if $found == 0
        if *(unsigned char *)(0x95da10 + $i * 0x130 + 4) == 3
          set $found = 1
          set $b = 0x95da10 + $i * 0x130
          printf "ROUND year=%d turn=%d cur=%d nb=%d mask=%#x cap=%d g38=%d g4c=%d nrg3=%d led3=%d\n", $y, *(int *)0x985afc, *(int *)0x985dcc, $nb, *(int *)0x985b10, *(int *)0x92a370, *(int *)0x8f0c38, *(int *)0x8f0c4c, *(int *)0x953884, *(int *)0x953888
          printf "OURBASE idx=%d addr=%#x x=%d y=%d pop=%d f30=%#x 3c=%d min40=%d f44=%d f4c=%d q50=%d mir94=%d mir98=%d c0=%d cc=%d d0=%d e0=%d f0=%d fc=%d f38=%#x\n", $i, $b, *(unsigned short *)$b, *(unsigned short *)($b + 2), *(unsigned char *)($b + 6), *(int *)($b + 0x30), *(int *)($b + 0x3c), *(int *)($b + 0x40), *(int *)($b + 0x44), *(int *)($b + 0x4c), *(int *)($b + 0x50), *(int *)($b + 0x94), *(int *)($b + 0x98), *(int *)($b + 0xc0), *(int *)($b + 0xcc), *(int *)($b + 0xd0), *(int *)($b + 0xe0), *(int *)($b + 0xf0), *(int *)($b + 0xfc), *(int *)($b + 0x38)
        end
      end
      set $i = $i + 1
    end
    if $found == 0
      printf "ROUND year=%d NOBASE owner3 -- our base is GONE (nb=%d)\n", $y, $nb
    end
    set $i = 0
    set $nu = 0
    while $i < 300
      if *(char *)(0x933278 + $i * 52 + 14) == 3
        if *(unsigned short *)(0x933278 + $i * 52) != 0xffff
          set $nu = $nu + 1
          set $u = 0x933278 + $i * 52
          printf "UNIT idx=%d type=%d x=%d y=%d order=%d mpused=%d home=%d\n", $i, *(unsigned char *)($u + 10), *(unsigned short *)$u, *(unsigned short *)($u + 2), *(unsigned char *)($u + 17), *(unsigned char *)($u + 40), *(unsigned short *)($u + 46)
        end
      end
      set $i = $i + 1
    end
    printf "UNITS n=%d\n", $nu
  else
    printf "YEARTORE eip=%#x year=%d\n", $eip, $y
  end
  continue
end

break *0x4ef6d0
commands
  silent
  set $npipe = $npipe + 1
  set $cb = *(int *)0x8f0d60
  printf "PIPE n=%d base=%#x own=%d x=%d y=%d min40=%d 3c=%d cc=%d d0=%d q50=%d ours=%d\n", $npipe, $cb, *(unsigned char *)($cb + 4), *(unsigned short *)$cb, *(unsigned short *)($cb + 2), *(int *)($cb + 0x40), *(int *)($cb + 0x3c), *(int *)($cb + 0xcc), *(int *)($cb + 0xd0), *(int *)($cb + 0x50), $cb == 0x962e60
  if $npipe >= 500
    printf "PIPE-CAP\n"
    detach
    quit
  end
  continue
end

break *0x4ef7db
commands
  silent
  set $n = $n + 1
  printf "SITE %d IGATE base=%#x own=%d d0=%d q50=%d f30=%#x min40=%d ours=%d\n", $n, $eax, *(unsigned char *)($eax + 4), $ecx, *(int *)($eax + 0x50), *(int *)($eax + 0x30), *(int *)($eax + 0x40), $eax == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4ef7f6
commands
  silent
  set $n = $n + 1
  printf "SITE %d IADD base=%#x own=%d added=%d newmin40=%d ours=%d\n", $n, $eax, *(unsigned char *)($eax + 4), $ecx, $edx, $eax == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4ef88b
commands
  silent
  set $n = $n + 1
  printf "SITE %d QGATE base=%#x own=%d q50=%d ours=%d\n", $n, $eax, *(unsigned char *)($eax + 4), $ecx, $eax == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4ef9b3
commands
  silent
  set $n = $n + 1
  printf "SITE %d NOQUEUE base=%#x own=%d min40=%d d0=%d f30=%#x ours=%d\n", $n, $eax, *(unsigned char *)($eax + 4), *(int *)($eax + 0x40), *(int *)($eax + 0xd0), *(int *)($eax + 0x30), $eax == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4efd49
commands
  silent
  set $n = $n + 1
  printf "SITE %d PROGDIV base=%#x own=%d esi=%d 3c=%d cc=%d edi=%d ours=%d\n", $n, $ecx, *(unsigned char *)($ecx + 4), $esi, *(int *)($ecx + 0x3c), *(int *)($ecx + 0xcc), $edi, $ecx == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4efe41
commands
  silent
  set $n = $n + 1
  set $cb = *(int *)0x8f0d60
  printf "SITE %d COMPLET base=%#x own=%d ebx=%d edi=%d esi=%d min40=%d q50=%d ours=%d\n", $n, $cb, *(unsigned char *)($cb + 4), $ebx, $edi, $esi, *(int *)($cb + 0x40), *(int *)($cb + 0x50), $cb == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4efed8
commands
  silent
  set $n = $n + 1
  printf "SITE %d SPENDA base=%#x own=%d cost_edi=%d min40_pre=%d m28=%d m30=%d ours=%d\n", $n, $ecx, *(unsigned char *)($ecx + 4), $edi, *(int *)($ecx + 0x40), *(int *)($ebp - 0x28), *(int *)($ebp - 0x30), $ecx == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4eff02
commands
  silent
  set $n = $n + 1
  printf "SITE %d CLAMP1 base=%#x own=%d accum=%d d0=%d cap=%d min=%d evbit=%#x mask=%#x ours=%d\n", $n, $esi, *(unsigned char *)($esi + 4), *(int *)($esi + 0x40), $eax, $ecx, $edx, $dl, *(int *)0x985b10, $esi == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4eff29
commands
  silent
  set $n = $n + 1
  printf "SITE %d MIRA base=%#x own=%d accum_final=%d mir98_pre=%d ours=%d\n", $n, $esi, *(unsigned char *)($esi + 4), $eax, *(int *)($esi + 0x98), $esi == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f0ca1
commands
  silent
  set $n = $n + 1
  printf "SITE %d SPENDB base=%#x own=%d cost_edi=%d min40_pre=%d m28=%d m30=%d ours=%d\n", $n, $edx, *(unsigned char *)($edx + 4), $edi, *(int *)($edx + 0x40), *(int *)($ebp - 0x28), *(int *)($ebp - 0x30), $edx == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f0ccb
commands
  silent
  set $n = $n + 1
  printf "SITE %d CLAMP2 base=%#x own=%d accum=%d d0=%d cap=%d min=%d evbit=%#x mask=%#x ours=%d\n", $n, $esi, *(unsigned char *)($esi + 4), *(int *)($esi + 0x40), $eax, $ecx, $edx, $dl, *(int *)0x985b10, $esi == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f0cf2
commands
  silent
  set $n = $n + 1
  printf "SITE %d MIRB base=%#x own=%d accum_final=%d mir98_pre=%d ours=%d\n", $n, $esi, *(unsigned char *)($esi + 4), $eax, *(int *)($esi + 0x98), $esi == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x4f1e3f
commands
  silent
  set $n = $n + 1
  printf "SITE %d QDRAIN base=%#x own=%d m30=%d q50_pre=%d pop=%d x=%d y=%d ours=%d\n", $n, $eax, *(unsigned char *)($eax + 4), *(int *)($ebp - 0x30), *(int *)($eax + 0x50), *(unsigned char *)($eax + 6), *(unsigned short *)$eax, *(unsigned short *)($eax + 2), $eax == 0x962e60
  if $n >= 400
    detach
    quit
  end
  continue
end

break *0x483470
commands
  silent
  set $npane = $npane + 1
  if $npane < 80
    printf "PANE n=%d id=%s\n", $npane, (char *)*(int *)($esp + 4)
  end
  if $npane >= 80
    printf "PANE-CAP\n"
    detach
    quit
  end
  continue
end

# no bp on 0x64bfa3: it is a generic dword-copy loop (thousands of hits/frame).
# slide detection = WP identity bytes (own/x/y below) + per-round marker re-scan.
watch *(int *)0x962ea0
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d MIN40 eip=%#x new=%d own=%d x=%d y=%d d0=%d q50=%d eax=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $nwp, $eip, *(int *)0x962ea0, *(unsigned char *)(0x962e60 + 4), *(unsigned short *)0x962e60, *(unsigned short *)(0x962e60 + 2), *(int *)0x962f30, *(int *)0x962eb0, $eax, $ecx, $edx, $esi, $edi
  if $nwp >= 40
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x962eb0
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d QUEUE50 eip=%#x new=%d min40=%d\n", $nwp, $eip, *(int *)0x962eb0, *(int *)0x962ea0
  if $nwp >= 40
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x962f30
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d D0 eip=%#x new=%d c0=%d f0=%d e0=%d min40=%d\n", $nwp, $eip, *(int *)0x962f30, *(int *)(0x962e60 + 0xc0), *(int *)(0x962e60 + 0xf0), *(int *)(0x962e60 + 0xe0), *(int *)0x962ea0
  if $nwp >= 40
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x953884
commands
  silent
  set $nwp = $nwp + 1
  printf "WP %d ENERGY eip=%#x new=%d eax=%#x ecx=%#x esi=%#x edi=%#x\n", $nwp, $eip, *(int *)0x953884, $eax, $ecx, $esi, $edi
  if $nwp >= 40
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

printf "SELFTEST addrs: %#x %#x %#x %#x %#x %#x %#x\n", 0x962e60, 0x962ea0, 0x962eb0, 0x962f30, 0x953884, 0x962d30, 0x9630c0
printf "SELFTEST state: year=%d turn=%d cur=%d nb=%d min40=%d 3c=%d cc=%d q50=%d d0=%d nrg3=%d mask=%#x cap=%d\n", *(int *)0x985b00, *(int *)0x985afc, *(int *)0x985dcc, *(int *)0x985af4, *(int *)0x962ea0, *(int *)(0x962e60 + 0x3c), *(int *)(0x962e60 + 0xcc), *(int *)0x962eb0, *(int *)0x962f30, *(int *)0x953884, *(int *)0x985b10, *(int *)0x92a370
printf "ARMED\n"
continue
