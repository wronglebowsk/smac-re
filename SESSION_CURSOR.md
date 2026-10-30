M169-M171 PASS (m169_m171_aggregate.py): 0x926a7c totalled (0x9204ac count, 0x9204c4 sum) in a 0x20bc-stride faction loop of FUN_00531df0 (6459 B/1905 insns/17 callers) which gates on rank<5 (cmp [ebx+0x94d434],0x5); FUN_004dc100 (647 B) = BIT-DECODER: al -> 4 boolean dwords (+0x94d810/14/18/1c = setne(al&1/2/4/8)), header tristate (1/-1/0 from al&0x10/0x20), al&0x40 -> or [+0x94d430],0x800000.
main ebd39df after #116-#139. BOX: terran.exe loaded m54b_clean (67/18), TracerPid 0, idle.
next: FUN_004dc100's 2 callers (source byte owner) | 0x9204c4/0x9204ac consumers | FUN_00531df0's 17 callers.
