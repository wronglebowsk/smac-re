set pagination off
set confirm off
set height 0
set verbose off
set $b = 0x95ef70
set $n = 0
set $v = 0
break *0x4f5a99 if $ecx == $b
commands
silent
set $v = $v + 1
printf "VISIT#%d storage=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $v, *(int*)($b + 0x40), *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
continue
end
break *0x4ef7f6 if $eax == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4ef7f6 site=visit.income-add before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $edx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4ef7f6 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4efedd if $ecx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4efedd site=visit.pay(sub edi) before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $esi, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4efedd after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4eff20 if $esi == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4eff20 site=visit.clampB(post-pay) before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $eax, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4eff20 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4f0ca6 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4f0ca6 site=visit2.pay(sub edi) before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $esi, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4f0ca6 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4f0ce9 if $esi == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4f0ce9 site=visit2.clampB(post-pay) before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $eax, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4f0ce9 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4f2d7d if $edi == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4f2d7d site=postvisit.distribution before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $eax, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4f2d7d after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x418aae if $eax == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x418aae site=queue-edit.store1 before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $esi, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x418aae after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x418b21 if $eax == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x418b21 site=queue-edit.store2 before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $edx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x418b21 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x41a596 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x41a596 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $eax, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x41a596 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x41dac4 if $eax == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x41dac4 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $ecx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x41dac4 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4b9df5 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4b9df5 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $ecx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4b9df5 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4b9e30 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4b9e30 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $ecx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4b9e30 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x4badb0 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x4badb0 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $ecx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x4badb0 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x5b5ba9 if $esi == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x5b5ba9 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $edi, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x5b5ba9 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x5fc695 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x5fc695 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $eax, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x5fc695 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x5fcbce if $eax == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x5fcbce site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $ecx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x5fcbce after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x5fe34e if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x5fe34e site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), 0, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x5fe34e after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x5fe4f7 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x5fe4f7 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), 0, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x5fe4f7 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x6150a5 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x6150a5 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), 0, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x6150a5 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x615625 if $eax == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x615625 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $edx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x615625 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x615693 if $edx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x615693 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), 0, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x615693 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x62edc8 if $ecx == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x62edc8 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $edx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x62edc8 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
break *0x62ef98 if $eax == $b
commands
silent
set $n = $n + 1
printf "STORE#%d pc=0x62ef98 site=reachable before=%d src=%d pend=%d head=%d d0=%d f30=0x%x f3c=%d fcc=%d\n", $n, *(int*)($b + 0x40), $ecx, *(int*)($b + 0x4c), *(int*)($b + 0x50), *(int*)($b + 0xd0), *(int*)($b + 0x30), *(int*)($b + 0x3c), *(int*)($b + 0xcc)
si
printf "AFTER#%d pc=0x62ef98 after_si=%d\n", $n, *(int*)($b + 0x40)
continue
end
continue
