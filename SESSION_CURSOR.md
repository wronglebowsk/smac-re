M80 | acceptance not run yet (planned tag m80band1) | NOT merged | branch milestone/m80
| baseline census DONE (scripts/m80_band_census.py --json): array = 8 bands of 64, each band
| filled contiguously from band_start (b0 0-13 seeds, b1 64, b2 128-131, b3 192-194 ours,
| b4 256, b5 320-325, b6 384-386, b7 448-449); 387 is EMPTY. index = faction*64+slot.
| next: reload clean save (SMAC_SAVE=m54b_clean.SAV scripts/m54a_load.py --relaunch) ->
| enqueue -> gdb cond-bp at 0x5741fe printing esi, ebx, esi*52, [ebp+8], name at ebx+0x98ad88
