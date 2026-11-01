S198 M248/M249 submitted (branch milestone/m248). `python3 scripts/m248_region_values_census.py`
-> `PASS M248: 5/5 gates` (2nd invocation; 1st 3/5 on three instrument bugs, fixed, no threshold
moved) -> evidence/m248_region_values.txt. Region bytes = terrain record +3 (the map REGION LABEL:
<0x40 land, >=0x41 water) of the first land tile of a centre-first 9-diamond sample; recomputed ==
stored 19/19 files; +3's only writer = FUN_00582d00 (4 sites, all map generation). Box untouched.
NEXT: python3 scripts/track_mode.py (the next BUILD fire takes B3 — turn engine).
