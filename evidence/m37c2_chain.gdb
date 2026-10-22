set pagination off
set confirm off
set $n = 0

# mp refresh per faction (param_1 = player)
break *0x51f730
commands
silent
printf "REFRESH player=%d\n", *(int *)($esp+4)
continue
end

# solo order executor (param_1 = unit) — log only terraform-range orders
break *0x4d1200
commands
silent
set $u = *(int *)($esp+4)
set $o = *(int)(0x933289 + $u * 52) & 0xff
if $u >= 0 && $o >= 4 && $o <= 0x17
  printf "ORDEREXEC unit=%d order=0x%x\n", $u, $o
end
continue
end

# terraform exec-branch entry in FUN_004cce50 (param_3 != 0)
break *0x4cd2c8
commands
silent
printf "TERRAFEXEC unit=%d mode=%d accum_old=%d\n", *(int *)($ebp-0x8), *(int *)($ebp+0xc), *(char *)(0x93329d + *(int *)($ebp-0x8))
continue
end

# the completion decision point: edx = accum+work, eax = threshold
break *0x4cd32e
commands
silent
set $u = *(int *)($ebp-0x8)
printf "CHECK unit=%d mode=%d accum_new=%d threshold=%d iVar16=%d\n", $u, *(int *)($ebp+0xc), $edx & 0xff, *(int *)($ebp-0x2c), $edi
continue
end

# not-yet path (returns 0, order stays)
break *0x4cd33b
commands
silent
printf "NOTYET unit=%d x=%d y=%d\n", *(int *)($ebp-0x8), *(short *)(0x933278 + *(int *)($ebp-0x8)), *(short *)(0x93327a + *(int *)($ebp-0x8))
continue
end

# swamp-cancel path (order=0, return 0)
break *0x4cd319
commands
silent
printf "CANCEL unit=%d\n", *(int *)($ebp-0x8)
continue
end

# completion path entered (+37 zeroed, chain orders cleared, apply)
break *0x4cd35e
commands
silent
printf "COMPLETE unit=%d x=%d y=%d mode=%d\n", *(int *)($ebp-0x8), *(short *)(0x933278 + *(int *)($ebp-0x8)), *(short *)(0x93327a + *(int *)($ebp-0x8)), *(int *)($ebp+0xc)
continue
end

# raise setter
break *0x5ad400
commands
silent
printf "RAISE x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

# lower setter
break *0x5ad460
commands
silent
printf "LOWER x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

# elevation writer
break *0x5ad0a0
commands
silent
printf "SETELEV x=%d y=%d new=%d flag=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10)
continue
end

# tile mask set/clear — log only terraform-relevant tiles (skip spam: cap)
break *0x582ed0
commands
silent
set $n = $n + 1
if $n < 300
  printf "MASKSET x=%d y=%d mask=0x%x setclr=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10)
end
continue
end

continue
