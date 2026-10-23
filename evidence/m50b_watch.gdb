# M50b generated instrument: who truncates the per-base sweep?
set pagination off
set confirm off
set $sw_p = -1
set $sw_i = -1
set $sw_n = 0
set $nsweep = 0
set $nvis = 0
set $nyear = 0

# 0x520540(player): resets the sweep state for this player's pass
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

# 0x5206d3: the call to 0x4f5a70 for a base whose owner byte == player
break *0x5206d3
commands
  silent
  set $sw_n = $sw_n + 1
  set $nvis = $nvis + 1
  printf "VISIT p=%d idx=%d owner=%d nb=%d ours=%d\n", $sw_p, $ebx, *(unsigned char *)(0x95da14 + $ebx * 0x130), *(int *)0x985af4, (0x95da14 + $ebx * 0x130 - 4) == 0x962e60
  continue
end

# 0x5206f9: loop back edge (ebx already incremented) - records how far the pass got
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

# 0x51f554: the year store - the suspected mid-sweep interrupter
break *0x51f554
commands
  silent
  set $nyear = $nyear + 1
  printf "YEAR %d mid_p=%d mid_idx=%d mid_visits=%d nb=%d cur=%d\n", $nyear, $sw_p, $sw_i, $sw_n, *(int *)0x985af4, *(int *)0x985dcc
  continue
end
printf "ARMED\n"
continue
