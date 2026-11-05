# Session notes archive — sessions 196-196

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 196 (2026-11-01, M244 ANALYSE — save tail: the region-map formula, the count-prefixed
block is the base-site event log, the tail's real legs)

`python3 scripts/m244_save_tail.py` -> `PASS M244: 5/5 gates` (rc=0; 4th invocation — the 3rd was
4/5 because gate 3 built `final` from the record history, which keeps sites a type-2 record
removed: 19-vs-18 on Autosave 1, 20-vs-19 on Autosave 10; replay() now carries each live entry's
own history, no threshold moved) -> `evidence/m244_save_tail.txt`. `python3 -m sim.selftest --sav
"programs/saves/auto/m242_probe_B.SAV"` -> `PASS B2: 7/7` with sim/save.py's TRAILER_LEN table
replaced by the formula. Box: /proc reads only (`sudo -n python3 scripts/m244_tail_legmap.py`), no
gdb, terran.exe 319926 TracerPid 0.

- The map "trailer" IS the coarse region map; its length is code: `FUN_00582000`
  `DAT_0092ada4 = ((DAT_0092ad9c + 1)/2) * DAT_0092ada0`, `DAT_0092ad9c = (W+4)/5`,
  `DAT_0092ada0 = (H+4)/5` (shard_014.c:27263-27265) = 91/128/338 at 64/80/128. Closes planet.MP
  (15+2,724+140,800+128 = 143,667), planetx.MP (15+2,724+360,448+338 = 363,525) and puts the
  count u32 at 188,299 on 17/17 saves.
- The count-prefixed block (176/192/208 B) is an 8-B-record base-site event log: [u8 type {0 add,
  1 re-own, 2 remove}, u8 faction, u16 turn (`DAT_00985afc` = file 80), u16 x, u16 y]. The u32 is
  a BYTE length — `FUN_0059c150` appends 8 B and does `DAT_00927538 += 8` (shard_015.c:13891-13908,
  debug label "Replay Base Info"); `FUN_0059bcb0` (shard_015.c:13657-13708) replays it into a
  (x, y, faction) triple list. Replayed live set == the base records' (x, y, +4) on 17/17 saves;
  0 orphan type-1/2 records; count%8==0, x<W, y<H, turns non-decreasing and <= the header's.
- B2's open item CLOSED: base +4 = the site's current owner (the log's last write), +5 = the
  faction written just before it (previous owner; == +4 where the site was written once); 42 bases
  over 17 saves differ, each one a type-1 record (Autosave 10 (15,11) 2/5: founded 1, 5 at turn
  54, 2 at 55).
- RETRACTED: no 220-B and no 28-B block exists. The tail's codec pushes are 0x100, 0x100, 0x98,
  0x27a0 (shard_015.c:10654/10676/10698/10720); one 0x100 is gated by `(DAT_00985ae8 & 0x10)`
  (file 60) == 0 on all 17 saves. Last 10,800 B = 256 | 152 (the unique [9999,9999,0,0,2100,2600]
  row at tail+256; live `DAT_0092bf58` = file 232,255) | 10,144 (`DAT_0092d4a0`, gated
  `DAT_00985dbc >= 7`; dest-file k = 232,407 on three probes) | 20 (five 4-B globals) | 216 (9
  rows of 24 B, six dwords per row, `FUN_00596620` 0x596620-0x596850 over `DAT_007cdecc..0x7cdeec`
  + `DAT_008cda4c`) | 8 ([800,387]) | 4 (the per-save final dword, outside the codec). s195's
  `93,159 = 92,927 + 220 + 12` was a coincidence of totals, not a split.
