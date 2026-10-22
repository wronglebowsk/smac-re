# M48b: MINERAL-ECONOMY WRITE PROVENANCE, second instrument.
# Preamble + command-list style mirror scripts/m48_watch.gdb (the m48a script that
# worked) because this gdb build has two traps found the hard way during m48b:
#   * "set print frame-verbosity" does not exist here -> sourcing dies at line 3.
#   * `loop_break` inside an `if` inside a `while` inside a breakpoint `commands`
#     list makes gdb segfault AT DEFINITION TIME (bisected on variants C1..C4:
#     plain while = ok, while+if+loop_break = SIGSEGV in gdb, while+if+`set $i=$nb`
#     = ok).  So every early exit here is done with a counter, never loop_break.
#   * every commands list must end with an explicit `continue` (m48a's pattern).
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $ourbase = 0x962f90
set $nrg = 0x953884
set $wp_hits = 0
set $sp_hits = 0
set $qc_hits = 0
set $pipe_hits = 0
set $wp_cap = 30
set $sp_cap = 200
set $prev_year = -99

# ---------------------------------------------------------------------------
# m48a armed two hw watchpoints -- our base's mineral accumulator (+0x40) and
# production-queue head (+0x50) -- and saw a full round in which the ENERGY
# accumulator was written 3x (income 0x4f5c92, upkeep 0x4f4958 x2: exactly M47's
# signature) while base+0x40 and base+0x50 were NEVER written.  The mineral half of
# the turn pipeline is inert for our base.  Why (disassembly of programs/terran.exe
# = ground truth; Ghidra's DAT_008f0d60 typing is inconsistent between functions,
# so the byte offsets below come from the asm only):
#   FUN_004e93f0 0x4e950f-0x4e9596  (mineral income field recompute)
#       base+0xc0 = (facil_count + 2) * base+0xc0 / 2      ; 0x4e9525
#       base+0xf0 = *(int*)0x8f0c38 + *(int*)0x8f0c4c      ; 0x4e953e
#       base+0xd0 = base+0xc0 - base+0xf0                  ; 0x4e9557
#       base+0xe0 = 0; base+0xd0 -= base+0xe0; base+0x94 = base+0xd0
#       (live check: our base c0=5, f0=5, e0=0 -> d0=0, and d0 indeed reads 0.)
#   The caller block 0x4efe41-0x4efecf sets DAT_0068cbb0 = base index,
#   DAT_008f0d60 = 0x95da10 + index*0x130 (the 304-byte record stride, confirmed in
#   asm here for the first time), calls 0x4e8d60, 0x4e78e0, 0x4e92c0, 0x4e93f0,
#   0x4eaa10 -- the five pipeline steps -- then falls into the spend.
#   FUN_004ef6d0 writes the mineral accumulator at exactly four sites -- two spend
#   blocks of identical shape and two clamps behind the
#   (1 << (owner & 0x1f)) & *(int*)0x985b10 event-bit test:
#       0x4ef7f1-0x4ef7f6  INCOME: if (base+0xd0 >= 0 && base+0x50 != -38
#                                     && (byte base+0x30 & 2) == 0)
#                                    base+0x40 += base+0xd0
#       0x4efed5-0x4efedd  SPEND A: base+0x40 -= %edi   (%ebx = item id, < 0x40)
#       0x4eff20           CLAMP A: base+0x40 = min(base+0xd0, cap)
#       0x4eff2c           MIRROR A: base+0x98 = base+0x40
#       0x4f0ca1-0x4f0ca6  SPEND B: base+0x40 -= %edi
#       0x4f0cc3-0x4f0ce9  CLAMP B: cap = min(base+0xd0, *(int*)0x92a370)
#       0x4f0cf5           MIRROR B
#       0x4f1e3f           QUEUE DRAIN: base+0x50 = -38, reached only when the
#                          popped item matches (cmp %ecx,%edx at 0x4f1e34) AND
#                          base+0x4c == 0 (0x4f1e38)
# Our base (idx 72) has base+0xd0 = 0 while every AI base sampled has 2..10, so
# mineral income is 0, the accumulator sat at 2, and the queued item (type 2) could
# never complete -- which is why m48a saw no mineral write at all.  This run POKED
# base+0x40 up to 200 first (TracerPid 0, pitfall 3) so a completion is forced and
# the spend sites have to execute.
#
# DR budget: exactly 4 hardware watchpoints (minerals +0x40, queue +0x50, income
# field +0xd0, faction energy).  Everything else is an int3 breakpoint -- memory
# based on x86-linux gdb, unlimited, no DR slot -- which is why the mission-year
# ROUND marker and four pipeline sites coexist with all four watchpoints.
# Read-only: no pokes, no calls here (pitfall 7).  Pitfall 15: gdb's stdout to a
# file is block-buffered -- read the log only after "[Inferior 1 ... detached]".
# ---------------------------------------------------------------------------

# bp 1 -- ROUND marker: the mission-year store proven in M47 (inside FUN_0051f320).
break *0x51f554
commands
  silent
  set $y = *(int *)0x985b00
  if $y != $prev_year
    set $prev_year = $y
    set $nb = *(int *)0x985af4
    set $gross = $ourbase + 0xfc
    set $found = 0
    set $i = 0
    while $i < $nb
      set $b = 0x95da10 + $i * 0x130
      if $found == 0
        if *(unsigned char *)($b + 4) == 3
          set $gross = $b + 0xfc
          set $found = 1
        end
      end
      set $i = $i + 1
    end
    # NB: no upkeep term here.  m48e died on exactly that: the M46 upkeep ADDRESS
    # formula is  *(int*)0x92a36c + <ledger ADDRESS> - *(int*)0x92a370 , and a
    # commands-list expression error aborts the whole sourced script -- gdb printed
    # "Cannot access memory at address 0x28" at the trailing `continue` and detached.
    # (50 + *(int*)($nrg+4)=0 - 10 = 40 = 0x28, an address nobody can read.)  So the
    # marker only reads fields whose addresses are plain arithmetic on known bases.
    printf "ROUND year=%d turn=%d cur=%d n_bases=%d gross=%d nrg3=%d led3=%d nrg1=%d ourmin=%d ourq=%d ourd0=%d ourc0=%d ourf0=%d oure0=%d ourf4c=%d mask=%#x\n", \
      $y, *(int *)0x985afc, *(int *)0x985dcc, $nb, *(int *)$gross, \
      *(int *)$nrg, *(int *)($nrg + 4), *(int *)0x953468, \
      *(int *)($ourbase + 0x40), *(int *)($ourbase + 0x50), *(int *)($ourbase + 0xd0), \
      *(int *)($ourbase + 0xc0), *(int *)($ourbase + 0xf0), *(int *)($ourbase + 0xe0), \
      *(int *)($ourbase + 0x4c), *(int *)0x985b10
    set $i = 0
    while $i < 300
      set $u = 0x929b90 + $i * 0x150
      if *(int *)($u + 0xa0) == 72
        printf "UNIT idx=%d type=%d x=%d y=%d order=%d mpused=%d home=%d\n", \
          $i, *(int *)$u, *(int *)($u + 4), *(int *)($u + 8), *(int *)($u + 0xc), \
          *(int *)($u + 0x10), *(int *)($u + 0x14)
      end
      set $i = $i + 1
    end
  else
    printf "YEARTORE eip=%#x year=%d\n", $eip, $y
  end
  continue
end

# bp 2 -- pipeline entry: FUN_004ef6d0 is called once per base per round (75x), so
# print the FIRST 12 bases it visits (proves the breakpoint is live and shows which
# bases the turn pipeline actually processes), flag OURS on every hit, and emit a
# heartbeat every 75 hits so a run that never reaches our base is distinguishable
# from a run where the pipeline never ran at all.
break *0x4ef6d0
commands
  silent
  set $pipe_hits = $pipe_hits + 1
  set $cb = *(int *)0x8f0d60
  if $pipe_hits <= 12
    printf "PIPE n=%d cur_base=%#x own=%d min40=%d d0=%d q50=%d ours=%d\n", \
      $pipe_hits, $cb, *(unsigned char *)($cb + 4), *(int *)($cb + 0x40), \
      *(int *)($cb + 0xd0), *(int *)($cb + 0x50), $cb == $ourbase
  end
  if $pipe_hits % 75 == 0
    printf "PIPE-HEARTBEAT n=%d\n", $pipe_hits
  end
  if $cb == $ourbase
    printf "PIPE4ef6d0 OURS n=%d: min40=%d d0=%d q50=%d f30=%d c0=%d f0=%d e0=%d fc=%d f4c=%d\n", \
      $pipe_hits, *(int *)($ourbase + 0x40), *(int *)($ourbase + 0xd0), \
      *(int *)($ourbase + 0x50), *(int *)($ourbase + 0x30), *(int *)($ourbase + 0xc0), \
      *(int *)($ourbase + 0xf0), *(int *)($ourbase + 0xe0), *(int *)($ourbase + 0xfc), \
      *(int *)($ourbase + 0x4c)
  end
  if $pipe_hits >= 400
    printf "PIPE-CAP\n"
    detach
    quit
  end
  continue
end

# bp 3 -- SPEND A site (base+0x40 -= %edi).  Fires for any base that completes an
# item, so it doubles as a live unit/facility COST table: edi = cost charged.
break *0x4efed5
commands
  silent
  set $sp_hits = $sp_hits + 1
  set $b = $ecx
  printf "SPEND_A n=%d base=%#x own=%d min40=%d cost_edi=%d item=%d q50=%d pop=%d\n", \
    $sp_hits, $b, *(unsigned char *)($b + 4), *(int *)($b + 0x40), $edi, \
    *(int *)($ebp - 0x28), *(int *)($b + 0x50), *(unsigned char *)($b + 6)
  if $sp_hits >= $sp_cap
    printf "SPEND-CAP\n"
    detach
    quit
  end
  continue
end

# bp 4 -- SPEND B site (same shape, other branch of the same function).
break *0x4f0ca1
commands
  silent
  set $sp_hits = $sp_hits + 1
  set $b = $edx
  printf "SPEND_B n=%d base=%#x own=%d min40=%d cost_edi=%d item=%d q50=%d pop=%d\n", \
    $sp_hits, $b, *(unsigned char *)($b + 4), *(int *)($b + 0x40), $edi, \
    *(int *)($ebp - 0x28), *(int *)($b + 0x50), *(unsigned char *)($b + 6)
  if $sp_hits >= $sp_cap
    printf "SPEND-CAP\n"
    detach
    quit
  end
  continue
end

# bp 5 -- QUEUE DRAIN site: base+0x50 = -38 => the queue is now empty.
break *0x4f1e3f
commands
  silent
  set $qc_hits = $qc_hits + 1
  set $b = $eax
  printf "QDRAIN n=%d base=%#x own=%d item=%d min40=%d pop=%d x=%d y=%d\n", \
    $qc_hits, $b, *(unsigned char *)($b + 4), *(int *)($ebp - 0x28), \
    *(int *)($b + 0x40), *(unsigned char *)($b + 6), *(int *)($b + 8), *(int *)($b + 0xc)
  continue
end

# --- exactly 4 hardware watchpoints = the 4 DR slots -----------------------
# NB: the watch EXPRESSIONS must be literal addresses -- `watch -force *(int *)($ourbase
# + 0x40)` dies at definition time with "No symbol table is loaded" because gdb resolves a
# watchpoint's location when the command is parsed (no objfile here), while the same
# convenience-variable arithmetic inside a commands list is only evaluated at hit time and
# is fine.  Plain `watch` (no -force) is what m48a proved works on this build.
watch *(int *)0x962fd0
commands
  silent
  set $wp_hits = $wp_hits + 1
  printf "WP n=%d MIN40 eip=%#x newval=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", \
    $wp_hits, $eip, *(int *)0x962fd0, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $wp_hits >= $wp_cap
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x962fe0
commands
  silent
  set $wp_hits = $wp_hits + 1
  printf "WP n=%d QUEUE50 eip=%#x newval=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", \
    $wp_hits, $eip, *(int *)0x962fe0, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $wp_hits >= $wp_cap
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x963060
commands
  silent
  set $wp_hits = $wp_hits + 1
  printf "WP n=%d INCOME_D0 eip=%#x newval=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", \
    $wp_hits, $eip, *(int *)0x963060, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $wp_hits >= $wp_cap
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x953884
commands
  silent
  set $wp_hits = $wp_hits + 1
  printf "WP n=%d ENERGY eip=%#x newval=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", \
    $wp_hits, $eip, *(int *)0x953884, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $wp_hits >= $wp_cap
    printf "WP-CAP\n"
    detach
    quit
  end
  continue
end

printf "ARMED min40=%#x queue50=%#x income_d0=%#x energy=%#x yearbp=%#x spendA=%#x spendB=%#x qdrain=%#x pipe=%#x\n", \
  0x962fd0, 0x962fe0, 0x963060, 0x953884, 0x51f554, 0x4efed5, 0x4f0ca1, 0x4f1e3f, 0x4ef6d0

# SELFTEST: a commands-list expression error aborts the WHOLE sourced script and gdb
# detaches mid-run (that is how m48e died), so evaluate every address the marker and
# the pipeline sites will touch, once, at script time -- highest index first -- and
# bail loudly here instead of minutes into the run.
printf "SELFTEST marker: %#x %#x %#x %#x %#x %#x %#x %#x %#x %#x %#x %#x %#x\n", \
  0x985b00, 0x985afc, 0x985dcc, 0x985af4, 0x985b10, 0x953468, $nrg, $nrg + 4, \
  0x95da10 + 74 * 0x130 + 4, $ourbase + 0x40, $ourbase + 0x50, $ourbase + 0xd0, $ourbase + 0x4c
printf "SELFTEST marker values: year=%d turn=%d cur=%d nb=%d mask=%#x min40=%d q50=%d d0=%d c0=%d f0=%d e0=%d\n", \
  *(int *)0x985b00, *(int *)0x985afc, *(int *)0x985dcc, *(int *)0x985af4, \
  *(int *)0x985b10, *(int *)($ourbase + 0x40), *(int *)($ourbase + 0x50), \
  *(int *)($ourbase + 0xd0), *(int *)($ourbase + 0xc0), *(int *)($ourbase + 0xf0), \
  *(int *)($ourbase + 0xe0)
printf "SELFTEST unit scan top slot: %#x %#x\n", 0x929b90 + 299 * 0x150 + 0xa0, \
  *(int *)(0x929b90 + 299 * 0x150 + 0xa0)
continue
