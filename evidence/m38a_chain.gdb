# M38: issue a SECOND raise at elev 5 — full issue chain: tech gate -> pay path ->
# TERRACOST/TERRAPAY panes -> DEBIT -> footprint pass (DIPLO branch!) -> tutor latch
# (consumed) -> AFTERLATCH -> LOCKCHK/LOCKRET -> STORE -> BCAST -> ENQ.
# 39 is substituted by scripts/m38_issue.py.
# Sites objdump-pinned: see turn_driver.md §M35/§M36 (m35_pay.gdb + m36_store.gdb).
# New for M38: 0x4d5839 (footprint foreign-tile -> call 0x555030), 0x4d58dc/0x4d59c7
# (refund blocks — refusal evidence), 0x4d5add (epilogue = early return, NO store),
# 0x555030 entry (diplomacy break check: own/owner/req).
# All conditions CAST *(int *)($esp+N) / *(int *)($ebp+N) (M34 pitfall).
set pagination off
set confirm off
set $panecnt = 0
set $advcnt = 0
set $draincnt = 0

break *0x40c8d0 if *(int *)($esp+4) == 39
commands
silent
printf "NATIVESEL idx=%d arg4=%d\n", *(int *)($esp+4), *(int *)($esp+0xc)
continue
end

break *0x4d44d0 if *(int *)($esp+4) == 39
commands
silent
printf "TERRAF idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d4837 if *(int *)($ebp+8) == 39
commands
silent
printf "TECHCHK idx=%d mode=%#x unlocked=%d\n", *(int *)($ebp+8), *(int *)($ebp+0xc), $eax
continue
end

break *0x4d486e if *(int *)($ebp+8) == 39
commands
silent
printf "TECHFAIL idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d5496 if *(int *)($ebp+8) == 39
commands
silent
printf "PAYPATH idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d54c8 if *(int *)($ebp+8) == 39
commands
silent
printf "ORDERCHK idx=%d already_this_order=%d\n", *(int *)($ebp+8), $eax
continue
end

break *0x4d54e4 if *(int *)($ebp+8) == 39
commands
silent
printf "COST idx=%d cost=%d\n", *(int *)($ebp+8), $eax
continue
end

break *0x4d5572 if *(int *)($ebp+8) == 39
commands
silent
printf "TERRACOSTPANE OPEN idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d55b3 if *(int *)($ebp+8) == 39
commands
silent
printf "PAYPANE OPEN idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d55d5 if *(int *)($ebp+8) == 39
commands
silent
printf "PAYDECIDE idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d55e8 if *(int *)($ebp+8) == 39
commands
silent
printf "PAYTAKEN idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d561a if *(int *)($ebp+8) == 39
commands
silent
printf "DEBIT idx=%d new_energy=%d\n", *(int *)($ebp+8), $edx
continue
end

break *0x4d5689 if *(int *)($ebp+8) == 39
commands
silent
printf "PAYDECLINED idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d5634 if *(int *)($ebp+8) == 39
commands
silent
printf "SKIPPAY idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

# --- M38 new: footprint / diplomacy / refund sites (inside 0x4d44d0 frame) ---
break *0x4d5839 if *(int *)($ebp+8) == 39
commands
silent
printf "PACTCHK idx=%d (foreign tile in footprint -> 0x555030)\n", *(int *)($ebp+8)
continue
end

break *0x4d58dc if *(int *)($ebp+8) == 39
commands
silent
printf "REFUND1 idx=%d (refusal refund block)\n", *(int *)($ebp+8)
continue
end

break *0x4d59c7 if *(int *)($ebp+8) == 39
commands
silent
printf "REFUND2 idx=%d (refusal refund block)\n", *(int *)($ebp+8)
continue
end

break *0x555030
commands
silent
printf "DIPLO own=%d owner=%d req=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

# --- M36 store tail ---
break *0x4d58cb if *(int *)($ebp+8) == 39
commands
silent
printf "PANERET idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d5b16 if *(int *)($ebp+8) == 39
commands
silent
printf "AFTERLATCH idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d5b71 if *(int *)($ebp+8) == 39
commands
silent
printf "LOCKCHK idx=%d lock=%d\n", *(int *)($ebp+8), *(int *)0x91f718
continue
end

break *0x4d5bae if *(int *)($ebp+8) == 39
commands
silent
printf "LOCKRET idx=%d eax=%d\n", *(int *)($ebp+8), $eax
continue
end

break *0x4d5bbf if *(int *)($ebp+8) == 39
commands
silent
printf "STORE idx=%d order=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)+4
continue
end

break *0x4d5bc6 if *(int *)($ebp+8) == 39
commands
silent
printf "BCAST idx=%d\n", *(int *)($ebp+8)
continue
end

break *0x4d5add if *(int *)($ebp+8) == 39
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

break *0x529090 if *(int *)($esp+4) == 39
commands
silent
printf "SOLOWRAP idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x585720 if *(int *)($esp+4) == 39
commands
silent
printf "EXEC idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x5ab320 if *(int *)($esp+4) == 39
commands
silent
printf "MOVEUNIT idx=%d -> (%d,%d)\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4d1e90 if *(int *)($esp+4) == 39
commands
silent
printf "SPACEH idx=%d\n", *(int *)($esp+4)
continue
end

continue
