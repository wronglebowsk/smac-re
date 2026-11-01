S191 M240 SUBMITTED (PR pending merge). Acceptance = `python3 scripts/m240_terrain_repack.py` ->
`PASS M240: 6/6 gates on planet.MP, planetx.MP`, rc 0 -> evidence/m240_terrain_repack.txt (3rd invocation
green; G5 rewritten per-function = stricter, nothing weakened). FINDING: the .MP grid IS the live
terrain-record array — FUN_00582260 reads `DAT_0092a38c*0x2c` into DAT_0092ae14 verbatim, count=(W/2)*H,
one record = TWO map columns; +16..+43 = 7 copies of the +8 mask (OPEN). RETRACTED "cell+7 = land marker"
and FOOTING's "+7 = owner byte". Zero box time: M181 debt STILL owed. NEXT: `scripts/track_mode.py`
(expect ANALYSE; BUILD rung B2 must read 44-B records). NEXT_PROMPT ~15.1k B — headroom is thin.
