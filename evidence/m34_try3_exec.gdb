# M34: watch the game EXECUTE a stored terraform order (the Space-triggered chain).
# Static model (ghidra_out, session 34):
#   Space -> FUN_00512450 -> FUN_004d1e90(unit):
#       if (FUN_005acc00(unit) /*can-act*/ && FUN_005255e0()==0)
#           FUN_00529090(unit, -1, 0);            // shard_012.c:3206
#   solo: FUN_00529090 -> FUN_00585720(unit, -1, 3)   (DAT_00920434==0, shard_013.c:16870)
#   inside FUN_00585720: dir<0 -> 0x8 = "run your stored order"; it reads order byte
#   (&DAT_00933289)[unit*0x34] (shard_015.c has ~20 readers) and runs the terraform.
#   Farm payment was deferred at issue (M33: no TERRAPAY pane); the debit site is
#   0x4d561a (mov %edx,(%eax), eax = 0x94d650 + player*0x82f*4).
#   SETTILE = FUN_005ab320(unit,x,y), sole tile writer; param_1 = unit INDEX (int).
# 46 is substituted by scripts/m34_run.sh (gdb cannot read env vars in expressions).
set pagination off
set confirm off

break *0x512b40
commands
silent
printf "KEY p1=%#x p2=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

# Space handler: runs the SELECTED unit's stored order if can-act passes.
break *0x4d1e90
commands
silent
printf "SPACEH idx=%d\n", *(int *)($esp+4)
continue
end

break *0x4d44d0
commands
silent
printf "TERRAF idx=%d mode=%#x\n", *(int *)($esp+4), *(int *)($esp+8)
continue
end

break *0x529090
commands
silent
printf "SOLOWRAP idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

break *0x585720
commands
silent
printf "EXEC idx=%d dir=%d mode=%d\n", *(int *)($esp+4), *(int *)($esp+8), *(int *)($esp+0xc)
continue
end

# NOTE: the condition MUST cast — bare `$esp[1]` is a generic-pointer value in gdb
# and throws "Attempt to dereference a generic pointer" at condition-test time
# (m34_try1: this killed the batch script on the first SETTILE hit).
break *0x5ab320 if *(int *)($esp+4) == 46
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

break *0x4d5bc6
commands
silent
printf "BCAST idx=%d\n", *(int *)($esp+4)
continue
end

continue
