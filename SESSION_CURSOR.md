M303 | python3 scripts/m303_downstream.py -> PASS M303 10/10
| (evidence/m303_downstream.txt; A1-A10 at tail; 2 runs byte-identical) - the
| B19 lead CLOSED: 0x51e02c is the LOAD HALF of a byte ++ (lea-same-address
| 0x51e033 / inc dl / store 0x51e03e) of the per-block CNT byte array
| 0x94ed28=0x94eca8+0x80 (8 blocks x 8380 B, 128x{MAX@+0,CNT@+128}), addr =
| site + 8380*block + 0x94ed28; NEVER gates; dl dead after the store.
| state: branch milestone/m303, gate then submit, DO NOT merge (kickoff).
| next s260: LAND the M303 PR first, then track_mode FIRST - at this fire
| track_mode said ANALYSE (analyse_since_build=1, next_rung B20) even though
| the s258 pick claimed a merge flips it to BUILD: track_mode is authoritative.
