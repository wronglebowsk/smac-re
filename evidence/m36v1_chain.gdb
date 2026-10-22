# M36: catch the tail of FUN_004d44d0 after the TERRAFORM tutor pane (0x48ef40 at
# 0x4d58c6) finally returns: pane-return -> mode gate -> issue-lock -> 0x528930 ->
# STORE(+17=mode+4) -> BCAST -> enqueue 0x2101 -> drain -> dispatch -> exec.
# 41 is substituted by scripts/m36_dismiss.py.
# Sites objdump-pinned from terran.exe 0x4d58a4..0x4d5c1c (see turn_driver.md §M36):
#   0x4d58cb  after `call 0x48ef40` (TERRAFORM tutor pane; the setter parks HERE
#             inside it — m35v2's "missing STORE" was this pane, still open)
#   0x4d5b16  merge point after the 0x4c2be0(0x800) tutor latch; ebx = mode
#   0x4d5b71  issue-lock check: [0x91f718] != 0 -> "I think I've already got my
#             lock" (0x68c4bc) and the 0x528930 call is SKIPPED
#   0x4d5bae  after `call 0x528930(unit,0,-1,-1,0)` (ecx=0x91db70); $eax != 0 ->
#             jne 0x4d5c1c skips STORE. Solo: FUN_00528930 returns 0 (DAT_00920434
#             == 0), so the store gate is pass-through in solo.
#   0x4d5bbf  STORE order byte (unit*52+0x933289 = mode+4)
#   0x4d5bc6  `call 0x584350` broadcast/enqueue 0x2101 idx=unit
#   0x4d5add  early-return epilogue (advisor/decline/unwind path, NO store)
# All conditions CAST *(int *)($esp+N) / *(int *)($ebp+N) (M34 pitfall).
set pagination off
set confirm off
set $panecnt = 0
set $advcnt = 0
set $draincnt = 0

break *0x40c8d0 if *(int *)($esp+4) == 41
commands
silent
printf "NATIVESEL idx=%d arg4=%d\n", *(int *)($esp+4), *(int *)($esp+0xc)
continue
end

break *0x4d44d0 if *(int *)($esp+4) == 41
commands
silent
printf "TERRAF idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d58cb if *(int *)($ebp+8) == 41
commands
silent
printf "PANERET idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d5b16 if *(int *)($ebp+8) == 41
commands
silent
printf "AFTERLATCH idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d5b71 if *(int *)($ebp+8) == 41
commands
silent
printf "LOCKCHK idx=%d lock=%d\n", *(int *)($ebp+8), *(int *)0x91f718
continue
end

break *0x4d5bae if *(int *)($ebp+8) == 41
commands
silent
printf "LOCKRET idx=%d eax=%d\n", *(int *)($ebp+8), $eax
continue
end

break *0x4d5bbf if *(int *)($ebp+8) == 41
commands
silent
printf "STORE idx=%d order=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)+4
continue
end

break *0x4d5bc6 if *(int *)($ebp+8) == 41
commands
silent
printf "BCAST idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d5add if *(int *)($ebp+8) == 41
commands
silent
printf "EPILOGUE idx=%d (early return, no store)\n", *(int *)($ebp+8)
continue
end

# generic Script-pane show: arg2 (esp+8) = pointer to the pane-id string
break *0x5f0583
commands
silent
set $panecnt = $panecnt + 1
if $panecnt < 60
  printf "PANE #%d id=%s\n", $panecnt, (char *)*(int *)($esp+8)
end
continue
end

# advisor/message printer: arg1 (esp+4) = pointer to the Script.txt id string
break *0x483470
commands
silent
set $advcnt = $advcnt + 1
if $advcnt < 60
  printf "ADVISOR #%d id=%s\n", $advcnt, (char *)*(int *)($esp+4)
end
continue
end

break *0x52a720 if *(int *)($esp+0x1c) == 0x2101
commands
silent
printf "ENQ q=%d idx=%d type=0x2101\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x5262e0
commands
silent
set $draincnt = $draincnt + 1
if $draincnt < 40
  printf "DRAIN #%d\n", $draincnt
end
continue
end

break *0x52bce0 if *(int *)($esp+8) == 0x2101
commands
silent
printf "DISP 0x2101\n"
continue
end

break *0x529090 if *(int *)($esp+4) == 41
commands
silent
printf "SOLOWRAP idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x585720 if *(int *)($esp+4) == 41
commands
silent
printf "EXEC idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x5ab320 if *(int *)($esp+4) == 41
commands
silent
printf "MOVEUNIT idx=%d -> (%d,%d)\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4d1e90 if *(int *)($esp+4) == 41
commands
silent
printf "SPACEH idx=%d\n", *(int *)($esp+4)
continue
end

continue
