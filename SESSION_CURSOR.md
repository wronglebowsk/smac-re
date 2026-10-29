M92 in flight (milestone/m92 @6c15d37 + uncommitted instrument fixes; sibling work adopted, NOT merged).
m92tail3/4 both died at the CTRL hit (multi-line gdb `python` block inside a bp command list aborts the
sourced file). Fixed: single-line `python ...`. Also fixed by disassembly: windows now open at the CALL
print (0x5aa030) and close at ENT/TECH (0x48bae9) -- the old code closed at ENT, which fires BEFORE the
scan, so candidates=0 every run; the tail's cat-7 gate [ebp-0x18] is the callee's prologue popcount bc
(0x5a90ae/0x5a90d6), not the caller slot; the band leg's multiplier is byte[0x950664+edi*0x20bc+esi]
(GLOBAL band table, stride 844) and its gate is [0x94d448+(fac+edi)*4]. TAIL print fields relabelled
(idx=$esi, fac=[ebp+0xc]); BASE human= now prints the faction. Merged: NO.
Next: python3 scripts/m92_tail_census.py --tag m92tail5 --poke-index 5 --rounds 4 --timeout 100 (BACKGROUND)
