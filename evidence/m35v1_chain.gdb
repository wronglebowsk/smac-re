# M35: catch the terraform PAYMENT path end to end, including the TERRAPAY picker
# ("Cancel action." / "Expend $NUM0 credits.") blocking INSIDE FUN_004d44d0.
# 41 is substituted by scripts/m35_paypicker.py.
# Every condition CASTS: `*(int *)($esp+N)` / `*(int *)($ebp+N)` — bare $esp[k] throws
# "Attempt to dereference a generic pointer" on first hit and kills the batch script (M34).
# Sites are objdump-pinned from terran.exe (see NAMED.md M35 block):
#   0x4d4837  after `call 0x5a7520` (tech-unlock check; $eax = unlocked)
#   0x4d486e  tech-fail advisor branch (HASROAD / HASFARM / NOTUNTILTECH)
#   0x4d5496  LAB_004d5496 = payment-path entry (reached ONLY from case 0x10/0x11)
#   0x4d54c8  after `call 0x5a6330(unit,9,mode+4,-1,-1)`; $eax != 0 -> skip payment
#   0x4d54e4  after `call 0x4cc7b0`; $eax = cost (0 -> skip payment)
#   0x4d5572  `call 0x5f0583` TERRACOST message pane (blocks)
#   0x4d55b3  `call 0x5f0583` TERRAPAY picker (BLOCKS until answered)
#   0x4d55d5  `call 0x5f1394` = read the player's answer
#   0x4d55e8  "Took option to pay"  /  0x4d5689 "Didn't or couldn't pay"
#   0x4d561a  `mov %edx,(%eax)` energy debit (new value in $edx)
#   0x4d5634  payment skipped -> footprint/store path
#   0x4d5bbf  store order byte (+17 = mode+4)   0x4d5bc6 `call 0x584350` broadcast 0x2101
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

break *0x4d4837 if *(int *)($ebp+8) == 41
commands
silent
printf "TECHCHK idx=%d mode=%#x unlocked=%d\n", *(int *)($ebp+8), *(int *)($ebp+0xc), $eax
continue
end

break *0x4d486e if *(int *)($ebp+8) == 41
commands
silent
printf "TECHFAIL idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d5496 if *(int *)($ebp+8) == 41
commands
silent
printf "PAYPATH idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d54c8 if *(int *)($ebp+8) == 41
commands
silent
printf "ORDERCHK idx=%d already_this_order=%d\n", *(int *)($ebp+8), $eax
continue
end

break *0x4d54e4 if *(int *)($ebp+8) == 41
commands
silent
printf "COST idx=%d cost=%d\n", *(int *)($ebp+8), $eax
continue
end

break *0x4d5572 if *(int *)($ebp+8) == 41
commands
silent
printf "TERRACOSTPANE OPEN idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d55b3 if *(int *)($ebp+8) == 41
commands
silent
printf "PAYPANE OPEN idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d55d5 if *(int *)($ebp+8) == 41
commands
silent
printf "PAYDECIDE idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d55e8 if *(int *)($ebp+8) == 41
commands
silent
printf "PAYTAKEN idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d561a if *(int *)($ebp+8) == 41
commands
silent
printf "DEBIT idx=%d new_energy=%d\n", *(int *)($ebp+8), $edx
continue
end

break *0x4d5689 if *(int *)($ebp+8) == 41
commands
silent
printf "PAYDECLINED idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d5634 if *(int *)($ebp+8) == 41
commands
silent
printf "SKIPPAY idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d5bbf if *(int *)($ebp+8) == 41
commands
silent
printf "STORE idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d5bc6 if *(int *)($ebp+8) == 41
commands
silent
printf "BCAST idx=%d\n", *(int *)($ebp+8)
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
