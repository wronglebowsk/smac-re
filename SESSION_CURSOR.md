S194 M243 `PASS M243: 4/4 gates` (`sudo -n python3 scripts/m243_leg_gates.py`) ->
evidence/m243_leg_gates.txt; merged? submitting now. FINDING: the 7 dead write legs of FUN_00596850
are its 7 dead read twins too, in 3 families: swap bit (0x596927 3296 @0x91f750, 0x596976 4, 0x5969cb
192 — plain twins, dead in BOTH swap states); `ds:0x985dbc < 3` legacy scratch buffer (0x596af5
58,848, 0x597203 1,664, 0x597384 48n); `ds:0x985ae8 & 0x10` (0x59762f 256 @0x991698). RETRACT: 30
read sites, not 28. Box untouched. NEXT: `track_mode.py` (ANALYSE; B2 = save load) or "who writes
the 93,159-B tail".
