set pagination off
set confirm off
set height 0

# Log EVERY read made from inside the save loader (FUN_00596850, 0x596850-0x597a6b) or the
# map loader (FUN_00582260, 0x582260-0x582330), including 1-4 byte reads.
# Caller scoping is what keeps this usable: an unfiltered breakpoint on these wrappers fires
# 30k+ times from unrelated code (audio/movies) and starves the game.
break *0x64cc00 if *(void**)$esp >= 0x596850 && *(void**)$esp <= 0x597a6b
commands
silent
printf "S caller=%#x size=%d count=%d dest=%#x\n", *(void**)$esp, *(int*)($esp+8), *(int*)($esp+12), *(void**)($esp+4)
continue
end

break *0x64cc00 if *(void**)$esp >= 0x582260 && *(void**)$esp <= 0x582330
commands
silent
printf "M caller=%#x size=%d count=%d dest=%#x\n", *(void**)$esp, *(int*)($esp+8), *(int*)($esp+12), *(void**)($esp+4)
continue
end

continue
