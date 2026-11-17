M311 OPENED, branch not yet created. Pick (a) ds:0x68cbb0 -> ANALYSE, zero box.
PROBE: scratch/m311_probe1.txt (census 340 refs / 6 stores / 4 fns).
KEY FINDING: 0x68cbb0 is a RECORD INDEX. Three sites fold (n+n*8)*2<<4 = n*19*16 = 304n and add
0x95da10 -> ds:0x8f0d60 = current-record POINTER. 0x95da40 = the same array at +48, so PICK (b)
IS PICK (a): one milestone closes both. Setter FUN_004e3470 = 34 B, 11 insns, 57 callers.
TODO: read 0x4f5c36's tail (ds:0x8f0d60 <- [ebp-0x8], not a fold) + FUN_004e47d0's site; then
scripts/m311_recidx.py with gates + _mutate.py; docs; PR #288 (docs close-out) still UNMERGED.
