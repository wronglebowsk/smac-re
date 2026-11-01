S180 M201-M204: acceptance = `python3 scripts/m201_m204_dialog.py` rc 0 -> M201/202/203/204 all PASS,
15/15 gates; the 1st invocation was 12/15 on 3 INSTRUMENT bugs (slot-offset regex printed decimal for
+0x30/+0xdc, a 40-byte lookahead that missed the +0xdc dispatch, a char-literal repr set) - fixed, no
threshold weakened. evidence/m201_m204_dialog.txt. NOT MERGED: next `python3 scripts/gate.py --base main`
then `milestone.py submit`. No box time: s174e box state STILL unverified; M181 STILL a lead - arm
scratch/m181/pair.py, trigger a save or a governor-options OK.
