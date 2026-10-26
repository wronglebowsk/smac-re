set pagination off
set confirm off
set height 0
set verbose off
watch *0x8f0d70
commands
silent
printf "GUARDWRITE pc=0x%x new=%d\n", $pc, *(int*)0x8f0d70
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
printf "VISIT guard=%d year=%d round=%d cp=%d base=%s owner=%d xy=%d,%d min=%d pend=%d head=%d\n", *(int*)0x8f0d70, *(int*)0x985b00, *(int*)0x985afc, *(int*)0x985dcc, (char*)(*(int*)0x8f0d60+19), *(unsigned char*)(*(int*)0x8f0d60+4), *(short*)(*(int*)0x8f0d60), *(short*)(*(int*)0x8f0d60+2), *(int*)(*(int*)0x8f0d60+0x40), *(int*)(*(int*)0x8f0d60+0x4c), *(int*)(*(int*)0x8f0d60+0x50)
continue
end
break *0x4efedd
commands
silent
printf "PAY year=%d round=%d cp=%d base=%s before=%d edi=%d after=%d\n", *(int*)0x985b00, *(int*)0x985afc, *(int*)0x985dcc, (char*)(*(int*)0x8f0d60+19), *(int*)(*(int*)0x8f0d60+0x40), $edi, $esi
continue
end
break *0x4eff4e
commands
silent
printf "CREATE year=%d round=%d cp=%d guard=%d base=%s min=%d\n", *(int*)0x985b00, *(int*)0x985afc, *(int*)0x985dcc, $eax, (char*)(*(int*)0x8f0d60+19), *(int*)(*(int*)0x8f0d60+0x40)
continue
end
continue
