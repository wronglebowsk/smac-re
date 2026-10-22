# M36b: catch the EXECUTION of the stored terraform order (unit 41, order 0x14 at
# +17, queued 0x2101 idx=41) during turn processing after the ENDOFTURN1 confirm.
# Sites: 0x52a720 enqueue / 0x5262e0 drain / 0x52bce0 dispatcher (type&0xfff==0x2101)
# / 0x529090 solo wrapper / 0x585720 executor / 0x5ab320 unit reposition
# / 0x582ed0 tile-mask set-clear (x=esp+4, y=esp+8, mask=esp+0xc, set=esp+0x10)
# / 0x4d44d0 setter re-entry + payment bps (would mean EXEC re-runs the issue path)
# / 0x4d1e90 Space executor. All conditions cast (M34 pitfall).
set pagination off
set confirm off
set $panecnt = 0
set $advcnt = 0
set $draincnt = 0

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
if $draincnt < 300
  printf "DRAIN #%d\n", $draincnt
end
continue
end

break *0x52bce0 if ( *(int *)($esp+8) & 0xffff ) == 0x2101
commands
silent
printf "DISP type=%#x arg2=%#x\n", *(int *)($esp+8), *(int *)($esp+8)
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

break *0x582ed0 if *(int *)($esp+4) == 45 && *(int *)($esp+8) == 7
commands
silent
printf "SETMASK (%d,%d) mask=%#x %s\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc), ((*(int *)($esp+0x10)) != 0 ? "SET" : "CLR")
continue
end

break *0x4d44d0 if *(int *)($esp+4) == 41
commands
silent
printf "TERRAF-REENTRY idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d5496 if *(int *)($ebp+8) == 41
commands
silent
printf "PAYPATH idx=%d mode=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)
continue
end

break *0x4d561a if *(int *)($ebp+8) == 41
commands
silent
printf "DEBIT idx=%d new_energy=%d\n", *(int *)($ebp+8), $edx
continue
end

break *0x4d5bbf if *(int *)($ebp+8) == 41
commands
silent
printf "STORE idx=%d order=%#x\n", *(int *)($ebp+8), *(int *)($ebp+0xc)+4
continue
end

break *0x4d1e90 if *(int *)($esp+4) == 41
commands
silent
printf "SPACEH idx=%d\n", *(int *)($esp+4)
continue
end

break *0x5f0583
commands
silent
set $panecnt = $panecnt + 1
if $panecnt < 80
  printf "PANE #%d id=%s\n", $panecnt, (char *)*(int *)($esp+8)
end
continue
end

break *0x483470
commands
silent
set $advcnt = $advcnt + 1
if $advcnt < 80
  printf "ADVISOR #%d id=%s\n", $advcnt, (char *)*(int *)($esp+4)
end
continue
end

continue
