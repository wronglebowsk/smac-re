M92 in flight (milestone/m92, sibling commits 4c384e3+061f302 adopted; tree had uncommitted snap fix).
m92tail3 AND m92tail4 both DIED at the CTRL hit: (a) `dump binary memory %s` is invalid, (b) a multi-line
gdb `python` block inside a breakpoint command list aborts the sourced file ("Argument to arithmetic
operation not a number or boolean") -> snapshots never written.  Single-line `python ...` is the fix.
Three instrument defects found by disassembly of 0x5a9500-0x5a9698: (1) windows close at the ENT print
(0x48bae9), which fires BEFORE the scan's BASE events -> candidates=0 every run; (2) the tail's cat-7 gate
[ebp-0x18] is the callee's OWN prologue popcount bc (0x5a90ae/0x5a90d6), not the caller slot; (3) the
band leg's multiplier is byte[0x950664+edi*0x20bc+esi] (a GLOBAL band table, stride 844), not the block.
Merged: NO.  Next: python3 scripts/m92_tail_census.py --tag m92tail5 --poke-index 5 --rounds 4 --timeout 100
