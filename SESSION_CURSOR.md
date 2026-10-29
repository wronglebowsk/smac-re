M92 in flight (milestone/m92). Acceptance m92_tail_census.py NOT green.
PROVEN: tail == base + sim_tail EXACTLY 5/5 (m92tail12, fac7) and 7/7 across runs, once the DIVISOR is
taken from the TAIL record (live at the score: it moves INSIDE a round) and the arrays from the round
block: cats +0x920, mults +0x120 (from the instruction bytes, NOT +0x1000/+0x1860).
BLOCKED ON THE BOX: Wine hung at round 87 (round never moved, 0 gdb events) -> reload+enqueue+census
job launched (scratch/t13.sh -> evidence/m92tail14.gdblog). Merged: NO.
Next: read scratch/m92tail14.out; if green, close (notes->NAMED->NEXT_PROMPT->skill sync->gate->submit->merge).
