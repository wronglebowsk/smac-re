set pagination off
set confirm off
set verbose off
set can-use-hw-watchpoints 1
set $n = 0
set $cap = 4000

break *0x4f5a70
commands
silent
set $n = $n + 1
printf "VISIT n=%d idx=%d d64=%d c6c0=%d c70=%d ret=%#x\n", $n, *(int *)($esp+4), *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

break *0x4e8d60
commands
silent
set $n = $n + 1
printf "SWEEPIN n=%d cur=%d d64=%d c6c0pre=%d c70pre=%d ret=%#x\n", $n, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

break *0x4e92c0
commands
silent
set $n = $n + 1
printf "RATEIN n=%d cur=%d d64=%d c6c0=%d bc=%d ret=%#x\n", $n, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)(*(int *)0x8f0d60 + 0xbc), *(int *)($esp)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

hbreak *0x4e9331
commands
silent
set $n = $n + 1
printf "BCADD n=%d cur=%d d64=%d c6c0=%d bc_old=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x w6=%#x w7=%#x\n", $n, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x962dec, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14), *(int *)($esp+0x18), *(int *)($esp+0x1c)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)0x962dec
commands
silent
set $n = $n + 1
printf "BCCHG n=%d new=%d eip=%#x cur=%d d64=%d c6c0=%d c70=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x w6=%#x w7=%#x\n", $n, *(int *)0x962dec, $eip, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14), *(int *)($esp+0x18), *(int *)($esp+0x1c)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)0x962df0
commands
silent
set $n = $n + 1
printf "C0CHG n=%d new=%d eip=%#x cur=%d d64=%d c70=%d c6c0=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x w6=%#x w7=%#x\n", $n, *(int *)0x962df0, $eip, *(int *)0x68cbb0, *(int *)0x8f0d64, *(int *)0x8f0c70, *(int *)0x8f0c6c, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14), *(int *)($esp+0x18), *(int *)($esp+0x1c)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

watch *(int *)0x8f0d60
commands
silent
set $n = $n + 1
printf "BASEPTR n=%d new=%#x idx=%d eip=%#x d64=%d c6c0=%d c70=%d w0=%#x w1=%#x w2=%#x w3=%#x w4=%#x w5=%#x\n", $n, *(int *)0x8f0d60, ((int)*(int *)0x8f0d60 - 0x95da10) / 0x130, $eip, *(int *)0x8f0d64, *(int *)0x8f0c6c, *(int *)0x8f0c70, *(int *)($esp+0), *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), *(int *)($esp+0x10), *(int *)($esp+0x14)
if $n >= $cap
  printf "CAP\n"
  detach
  quit
end
continue
end

continue
