# M45: BUILD BASE ('b') live trace — key router -> 0x4d1280(unit) -> NEWBASE pane
# -> 0x4cca50(unit,name) -> 0x4e47d0 slot alloc -> 0x45abb40 consume colonist.
# __UNIT__ is substituted by scripts/m45_base.py (the selected colonist unit index).
# Call sites objdump-equivalent-pinned (E8 scan of programs/terran.exe, .text file
# offset = VA - 0x400000): CREATE call 0x4d1d9c -> return 0x4d1da1; ALLOC call
# 0x4ccbdd -> return 0x4ccbe2; BORDER call 0x4d14f6 -> return 0x4d14fb; LIMIT call
# 0x4d1945 -> return 0x4d194a.  PANE (0x5f0583) / ADV (0x483470) are the generic
# sites already verified live in m36_store.gdb / m38_issue.gdb.
# All conditions CAST *(int *)($esp+N) (M34 pitfall).
# PITFALL (m45a, live): Ghidra names callees FUN_<address> VERBATIM — do NOT
# normalize them. The first m45a run armed 0x45abb40/0x450bea0/0x441b780/0x450fc20/
# 0x45355c0/0x4551a20/0x447f490 for FUN_005abb40/0050bea0/0041b780/0050fc20/
# 005355c0/00551a20/0047f490: a leading digit duplicated, +0x400000 off, armed fine,
# never hit. The addresses below are corrected; the m45a evidence only proves the
# SETTER/PANE/ADV/ALLOC/CREATE/BORDER/LIMIT sites (which were right).
set pagination off
set confirm off
set height 0
set width 0
set $panecnt = 0
set $advcnt = 0

break *0x4d1280 if *(int *)($esp+4) == __UNIT__
commands
silent
printf "M45 SETTER unit=%d\n", *(int *)($esp+4)
continue
end

break *0x4d1da1
commands
silent
printf "M45 CREATERET base=%d unit=%d\n", $eax, *(int *)($ebp+8)
continue
end

break *0x4ccbe2
commands
silent
printf "M45 ALLOCRET base=%d unit=%d\n", $eax, *(int *)($ebp+8)
continue
end

# generic Script-pane show: arg2 (esp+8) = pointer to the pane-id string
break *0x5f0583
commands
silent
set $panecnt = $panecnt + 1
if $panecnt < 40
  printf "M45 PANE #%d id=%s\n", $panecnt, (char *)*(int *)($esp+8)
end
continue
end

# advisor/message printer: arg1 (esp+4) = pointer to the Script.txt id string
break *0x483470
commands
silent
set $advcnt = $advcnt + 1
if $advcnt < 40
  printf "M45 ADV #%d id=%s\n", $advcnt, (char *)*(int *)($esp+4)
end
continue
end

break *0x4d14fb
commands
silent
printf "M45 BORDERRET eax=%d  (setter's border-owner lookup for the tile)\n", $eax
continue
end

break *0x4d194a
commands
silent
printf "M45 LIMITRET eax=%d  (0x4e9b40 base-limit query)\n", $eax
continue
end

break *0x5abb40
commands
silent
printf "M45 CONSUME unit=%d\n", *(int *)($esp+4)
continue
end

break *0x5abd90 if *(int *)($esp+4) == __UNIT__
commands
silent
printf "M45 REMOVEUNIT unit=%d\n", *(int *)($esp+4)
continue
end

break *0x50bea0
commands
silent
printf "M45 CLAIM x=%d y=%d own=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x41b780
commands
silent
printf "M45 BASEINIT idx=%d a2=%d\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x50fc20
commands
silent
printf "M45 FC20 a=%d\n", *(int *)($esp+4)
continue
end

break *0x5355c0
commands
silent
printf "M45 ANGER a=%d b=%d\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x551a20
commands
silent
printf "M45 RELSET a=%d b=%d c=%#x\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x47f490
commands
silent
printf "M45 NOTIFY a=%d name=%s\n", *(int *)($esp+4), (char *)*(int *)($esp+8)
continue
end

continue
