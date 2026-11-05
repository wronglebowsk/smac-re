# Session notes archive — sessions 195-195

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 195 (2026-11-01, B2 BUILD fire — `sim/save.py`: a .SAV loads into the state model)

`python3 scripts/track_mode.py` -> `MODE=BUILD next_rung=B2` (no box time, no `/proc`, no gdb;
`grep -c 'box time owed' SESSION_CURSOR.md` printed 0, so nothing was owed).

**Acceptance** — `python3 -m sim.selftest --sav "programs/saves/auto/m242_probe_B.SAV"` ->
`PASS B2: 7/7 gates` (one invocation, 1.5 s) -> `evidence/b2_save_walk.txt` (gate output + a
per-save table of all 17 saves under `programs/saves`). B1 re-run unchanged: `PASS B1: 10/10`.

**The .SAV layout, closed on the byte on 17/17 saves** (`closes=True`): 12 prefix | 796 state
header | 4 own player (808) | 67,040 block A | 11,488 | 32 | 2,724 map header (dims u32 at
79,372/79,376) | W*H*22 grid at 82,096 | **91-B** trailer at 172,208 | 16,000 | **u32 count at
188,299** (176/192/208 = `DAT_00927538`) | 3,584 | 26,624 | 4,096 | **52·n units** | **304·m
bases** | 256+152+10,144+28+220 = 10,800 = EOF.
- The counts are IN the header — `0x985af0` = 72 units, `0x985af4` = 18 bases (file 68/72) — and
  the shape scan finds exactly 72/18 on every save, so no 52/304 Diophantine solve is needed.
- Faction count 8, three agreeing sources: 67,040/8,380 = 8 block-A records (the 8 "Template 1..8"
  groups sit 8,380 B apart and 8·8,380 = 67,040 exactly), mask byte `0x985b11` = 0xff (popcount 8),
  and 8 distinct record owners (0..7).
- Base rec: x u16 +0, y u16 +2, name at +19. **rec+4 != rec+5 on 2 of 18** (Gaia's Landing 2/1,
  U.N. Headquarters 2/7); +5 is the byte that matches the faction the NAME belongs to for all 7
  home bases, so +5 = home/builder, +4 = OPEN (current owner after capture?).

**CORRECTIONS.** (1) M110a's map offsets (79,364 / 82,088 / 172,200) are **8 B low**: at 82,088 no
cell has +7 == 0xff and the terrain set degenerates to {0,1,2,3}; at 82,096 the land markers number
1,426 and the terrain set is {0,1,2,8,9,10} — the set planet.MP gives at its own grid start.
(2) `.MP`'s "map-header word 5 == land cells" does NOT hold in a save: word 5 = 2,048 = (W/2)·H,
the record count. (3) M243's open item closes arithmetically: 93,159 = 92,927 (map block,
`FUN_00582260`) + 220 (reader unnamed) + 12 (magic+version, `FUN_00597ce0`) — exact on 242,539 and
on 242,799. (4) `decode_save.py --sections` RAISES on every 64×64 save (`no 52/304 split of a
0-byte region`): its table is the 80×80 one, so `sim/save.py` is now the working reader.

**Pitfall (cost one re-run).** A 52-B record whose +10 type >= 64 is a production-queue BAND (128/
130/131/256/320-323 here), not a unit: its +0/+2 are not tile coords (m113map rec 12 = 3076/56832),
so a coord check over the whole array rejects 18 of 67. Type-gate the coord test.

**OPEN:** trailer-length formula (91 at 64×64, 128 at 80×80, 338 at 128×128); contents of the
176/192/208-B count-prefixed block; who reads the 220-B block; which base byte is the CURRENT owner;
what band records' +0/+2 are.
