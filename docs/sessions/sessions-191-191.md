# Session notes archive — sessions 191-191

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 191 (2026-11-01, M240 static — the `.MP` grid IS the live terrain-record array)

- **Footing.** Cursor said S190 B1 merged, no harness running (`ps`: no milestone.py/gdb/smac_play), tree
  clean; `track_mode.py` → `MODE=ANALYSE last_build=B1 next_rung=B2`, so this fire analysed and took the
  first ANALYSE pick (the 22-B cell → 44-B record transform). Zero box time; M181 debt still owed.
- **Acceptance.** `python3 scripts/m240_terrain_repack.py` → `PASS M240: 6/6 gates on planet.MP,
  planetx.MP`, rc 0 → `evidence/m240_terrain_repack.txt`. Invocation 1 crashed on a shard-filename slice
  bug (`n[-6:-3]` → `n[6:9]`); invocation 2 was 5/6 because G5 demanded each setter pattern occur ≥2×
  image-wide when it legitimately occurs ONCE per accessor — rewritten as per-function presence (stricter,
  not weaker); invocation 3 green. No gate, threshold or map was removed.
- **THE FINDING — no repack exists.** `FUN_00582260` (`shard_014.c:27347`) reads 0xaa4 → `&DAT_0092a378`,
  calls `FUN_00582000`, then reads `DAT_0092a38c*0x2c` bytes into `DAT_0092ae14` and `DAT_0092ada4` into
  `DAT_0092ae18`; neither body has a loop. `FUN_00582000` sets `DAT_00692184 = W/2`,
  `DAT_0092a38c = (W/2)*H`, allocates `count*0x2c` and `((W+4)/5 + 1)/2 * ((H+4)/5)`. The file grid IS the
  record array: 3,200 / 8,192 records of 44 B at `((W/2)*y + (x>>1))*0x2c`, one record per TWO map
  columns; the "22-byte cell" is half a record and only bytes 0..21 are the tile's fields. Accounting
  closes on both maps (gate G1): 15+2724+140800+128 = 143,667 and 15+2724+360448+338 = 363,525.
- **Two RETRACTIONS.** (1) record `+7` is the constant 0xff in all 11,392 records of both maps — B1's
  "land marker" and FOOTING.md's "+7 = owner byte" were reading a constant; at 22-byte granularity only
  the even cells carry it, which is exactly why its count equalled header word 5 (gate G4). (2) B1's
  category census mixed halves: record byte 22 (third byte of the mask copy at +20) has cat 0 in 100 % of
  records, so "cat 0 = 59/3259" was 3,200 artifacts plus 59 real tiles. Real split under the live rule
  (cat<3 = water, `shard_001.c:3515-3517`): planet.MP 1,826 water / 1,374 land, planetx.MP 5,143 / 3,049.
- **NEW, measured.** record `+16..+43` = 7 dwords, all seven equal in 3,145/3,200 (planet) and 8,192/8,192
  (planetx) records; each equals the record's own `+8` mask in 8,191/8,192 fresh records, and in planet.MP
  1,100/3,200 records it is a strict SUBSET of that mask (bit 5 cleared 814×, bit 20 344×, bit 30 101×).
  Direct offsets on `DAT_0092ae14` top out at 0xe (492 refs); record-pointer offsets top out at 0x10
  (one hit: `FUN_0051c750`, `shard_013.c:9451-9465`, kelp/forest growth spawn, which walks dword slots
  4..7). Header word 5 = `(W/2)*H` = the record count, unread by the loader; the 128/338 B "trailer" is
  the coarse region map `DAT_0092ae18`, sized from the dimensions by the loader itself.
- **Open:** what the seven mask copies mean and who fills them at map GENERATION (the load path only
  reads them in); record bytes 1, 3, 4-7 and 12-15 unnamed; `decode_map.py` and `sim/map.py` still split
  the grid into 22-byte cells — their B1 gates are position parity so they stay valid, but their "cells"
  are record halves; M181 box debt  unpaid (terran.exe alive, TracerPid 0 — this fire took a static pick).
