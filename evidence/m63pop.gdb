set pagination off
set confirm off
set height 0
set verbose off
watch *(int*)0x95efc0
commands
silent
printf "HEADW pc=0x%x val=%d pend=%d owner=%d\n", $pc, *(int*)0x95efc0, *(int*)0x95efbc, *(unsigned char*)0x95ef74
continue
end
watch *(int*)0x985b00
commands
silent
printf "YEARW year=%d round=%d cp=%d\n", *(int*)0x985b00, *(int*)0x985afc, *(int*)0x985dcc
continue
end
watch *(int*)0x985dcc
commands
silent
printf "PLAYERW pc=0x%x cp=%d year=%d round=%d\n", $pc, *(int*)0x985dcc, *(int*)0x985b00, *(int*)0x985afc
continue
end
break *0x4ef6d0
commands
silent
printf "VISIT name=%s addr=0x%x owner=%d pend=%d head=%d cp=%d year=%d\\n", (char*)(*(int*)0x8f0d60+19), *(int*)0x8f0d60, *(unsigned char*)(*(int*)0x8f0d60+4), *(int*)(*(int*)0x8f0d60+0x4c), *(int*)(*(int*)0x8f0d60+0x50), *(int*)0x985dcc, *(int*)0x985b00
continue
end
break *0x4ef5d0
commands
silent
printf "POPIN idx=%d addr=0x%x name=%s owner=%d pend=%d s0=%d s1=%d s2=%d cp=%d year=%d visit_addr=0x%x\\n", $ebx, (0x95da10+$ebx*0x130), (char*)((0x95da10+$ebx*0x130)+19), *(unsigned char*)((0x95da10+$ebx*0x130)+4), *(int*)((0x95da10+$ebx*0x130)+0x4c), *(int*)((0x95da10+$ebx*0x130)+0x50), *(int*)((0x95da10+$ebx*0x130)+0x54), *(int*)((0x95da10+$ebx*0x130)+0x58), *(int*)0x985dcc, *(int*)0x985b00, *(int*)0x8f0d60
continue
end
break *0x4ef61a
commands
silent
printf "POPDEC addr=0x%x byte=%d name=%s owner=%d head=%d\\n", $ecx, *(unsigned char*)$ecx, (char*)((0x95da10+$ebx*0x130)+19), *(unsigned char*)((0x95da10+$ebx*0x130)+4), *(int*)((0x95da10+$ebx*0x130)+0x50)
continue
end
break *0x4ef61c
commands
silent
printf "POPAFT addr=0x%x byte=%d sibling_dc=0x%x sibling=%d\\n", $ecx, *(unsigned char*)$ecx, $ecx-0x200, *(unsigned char*)($ecx-0x200)
continue
end
break *0x4ef62c
commands
silent
printf "POPSHIFT slot=%d dest=0x%x val=%d old=%d name=%s pend=%d\\n", ($eax-0x95da10-$ebx*0x130)/4, $eax, $edx, *(int*)$eax, (char*)((0x95da10+$ebx*0x130)+19), *(int*)((0x95da10+$ebx*0x130)+0x4c)
continue
end
break *0x4ef642
commands
silent
printf "POPCNT name=%s newpend=%d s0=%d s1=%d s2=%d s3=%d\\n", (char*)((0x95da10+$ebx*0x130)+19), $edx, *(int*)((0x95da10+$ebx*0x130)+0x50), *(int*)((0x95da10+$ebx*0x130)+0x54), *(int*)((0x95da10+$ebx*0x130)+0x58), *(int*)((0x95da10+$ebx*0x130)+0x5c)
continue
end
break *0x4ef655
commands
silent
printf "POPVAL item=%d owner=%d idx=%d name=%s\\n", $eax, $edi, $ebx, (char*)((0x95da10+$ebx*0x130)+19)
continue
end
break *0x4ef66a
commands
silent
printf "POPVALN negitem=%d owner=%d idx=%d name=%s\\n", $eax, $edi, $ebx, (char*)((0x95da10+$ebx*0x130)+19)
continue
end
break *0x4ef65d
commands
silent
printf "POPRES result=%d name=%s head=%d\\n", $eax, (char*)((0x95da10+$ebx*0x130)+19), *(int*)((0x95da10+$ebx*0x130)+0x50)
continue
end
break *0x4efedd
commands
silent
printf "PAY name=%s before=%d edi=%d after=%d cp=%d year=%d\\n", (char*)(*(int*)0x8f0d60+19), *(int*)(*(int*)0x8f0d60+0x40), $edi, $esi, *(int*)0x985dcc, *(int*)0x985b00
continue
end
break *0x4eff4e
commands
silent
printf "CREATE name=%s guard=%d owner=%d min=%d cp=%d\\n", (char*)(*(int*)0x8f0d60+19), *(int*)0x8f0d70, $eax, *(int*)(*(int*)0x8f0d60+0x40), *(int*)0x985dcc
continue
end
continue

