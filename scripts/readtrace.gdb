set pagination off
set confirm off
set height 0

# Logs every read of 64+ bytes: caller, size, count, FILE*.
# Caller == *(void**)$esp at function entry (the return address).
# Unconditional breakpoints here fire 30k+ times (1-2 byte reads), which starves the game.
#
# Signature: FUN_0064cc00(dest, size, count, FILE*)  [cdecl, args at esp+4, +8, +12, +16]
break *0x64cc00 if *(int*)($esp+8) >= 64
commands
silent
printf "R3 caller=%#x size=%d count=%d file=%#x\n", *(void**)$esp, *(int*)($esp+8), *(int*)($esp+12), *(void**)($esp+16)
continue
end

break *0x64c9a0 if *(int*)($esp+8) >= 64
commands
silent
printf "R4 caller=%#x size=%d count=%d file=%#x\n", *(void**)$esp, *(int*)($esp+8), *(int*)($esp+12), *(void**)($esp+16)
continue
end

continue
