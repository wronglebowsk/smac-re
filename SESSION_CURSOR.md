M113 attempt 2 firing (tag m113map2, BAND refinement): bands 64000-82500, 163000-174000, 174000-182000, 221000-231000 at step 2048 = 25 markers in m113map.SAV; load, scan. Pins the block-A->map-header, grid->trailer, trailer->section boundaries and the record area to ~2 KB.
PREDICT: anchors step 1:1 inside a run and JUMP across a boundary, so each boundary is bracketed by the last-and-first anchor of adjacent runs.
Main = da69b48 (M113 merged #119). Do not touch the box until m113map2 exits; then read evidence/m113map2.log.
