# NAMED.md `## M283` - ROTATED VERBATIM (byte-exact) by scripts/m380_named_rotate.py

## M283 (s227, PASS 17/17) - decode_save --sections walks 64x64 saves; the coarse-region-map length is dims-derived, not a hardcoded 80x80 128
- The MAP branch hardcoded the coarse region map at 128 B. That map is
  ((W+4)/5+1)/2 * (H+4)/5 bytes (FUN_00582000, shard_014.c:27263-27265; same formula as
  sim/save.py region_len): 128 for 80x80, 91 for 64x64, 338 for 128x128. With 128 hardcoded,
  every 64x64 save mis-read the count-prefixed section 37 B early and --sections died with
  "no 52/304 split of a 0-byte region" (rc=1). walk() now reads W,H from the map header
  struct and computes the length; the section table sums to the file byte on all 17 repo
  saves (all 64x64) and the count u32 sits at 188,299 on all of them (sim/save.py predicted).
- Acceptance: `python3 scripts/m283_sections_64x64.py` -> 17/17 gates
  (`evidence/m283_sections_64x64.txt`). B10's gate that encoded the OLD failure ("rc == rc;
  --sections fails on both") was updated to require rc 0 == rc 0 plus the grown image showing
  exactly one more 304-B record (67x52+19x304 vs 67x52+18x304); B8/B9/B10 regressions green.
