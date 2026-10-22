# M47: catch the SPENDING-LEDGER writers on a player that actually spends.
# Player 4 (Morgan) showed panel-net 29 vs observed Δenergy +18 in m46e, i.e.
# an 11-unit within-round debit. Watch its ledger (0x955944 = 0x955940 + 4) and
# its energy (0x955940) for one round.
set pagination off
set confirm off
set can-use-hw-watchpoints 1
set $nled = 0
set $ne = 0

watch *(int *)0x955944
commands
  silent
  set $nled = $nled + 1
  printf "P4LED n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $nled, $eip, *(int *)0x955944, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $nled >= 30
    printf "P4LED-CAP\n"
    detach
    quit
  end
  continue
end

watch *(int *)0x955940
commands
  silent
  set $ne = $ne + 1
  printf "P4ENERGY n=%d eip=%#x val=%d eax=%#x ebx=%#x ecx=%#x edx=%#x esi=%#x edi=%#x\n", $ne, $eip, *(int *)0x955940, $eax, $ebx, $ecx, $edx, $esi, $edi
  if $ne >= 40
    printf "P4ENERGY-CAP\n"
    detach
    quit
  end
  continue
end

printf "ARMED p4ledger=%#x p4energy=%#x\n", 0x955944, 0x955940
continue
