# M34 v7: catch the FULL execution chain of a Farm order — from setter store through
# broadcast (FUN_00584350 -> FUN_0052a720(0x2101)) to the dispatcher (FUN_0052bce0)
# and the solo executor (FUN_00529090 -> FUN_00585720 -> FUN_005ab320).
# Question: is execution SYNCHRONOUS with the store+broadcast, or QUEUED?
# 45 substituted by scripts/m34_chase.sh.
# Conditions MUST cast *(int *)($esp+N) — bare $esp[k] is a generic pointer (try1 pitfall).
set pagination off
set confirm off

break *0x40c8d0 if *(int *)($esp+4) == 45
commands
silent
printf "NATIVESEL idx=%d p4=%d\n", *(int *)($esp+4), *(int *)($esp+0xc)
continue
end

break *0x4d44d0 if *(int *)($esp+4) == 45
commands
silent
printf "TERRAF idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x4d5bbf
commands
silent
printf "STORE idx=%d order=%#x\n", *(int *)($esp+4), (int)(unsigned char)*($esp+8)
continue
end

break *0x4d5bc6 if *(int *)($esp+4) == 45
commands
silent
printf "BCAST idx=%d\n", *(int *)($esp+4)
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
printf "DRAIN in-game queues\n"
continue
end

break *0x52bce0 if *(int *)($esp+8) == 0x2101
commands
silent
printf "DISP type=0x2101\n"
continue
end

break *0x529090 if *(int *)($esp+4) == 45
commands
silent
printf "SOLOWRAP idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x585720 if *(int *)($esp+4) == 45
commands
silent
printf "EXEC idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x5ab320 if *(int *)($esp+4) == 45
commands
silent
printf "SETTILE idx=%d x=%d y=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x4d561a
commands
silent
printf "DEBIT newval=%d\n", $edx
continue
end

break *0x4d5908
commands
silent
printf "REFUND hit (terraform aborted/refunded)\n"
continue
end

continue
