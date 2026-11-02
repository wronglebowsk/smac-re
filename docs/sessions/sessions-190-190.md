# Session notes archive — sessions 190-190

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 190 (2026-11-01, B1 build rung — `sim/` exists; static, zero box time)

- `python3 scripts/track_mode.py` -> `MODE=BUILD analyse_since_build=3 last_build=B0 next_rung=B1`, so this fire
  built BUILD_SPINE.md rung B1 instead of taking a census pick. Branch `milestone/b1`; the three files were
  committed (`ed020bc`) before any probing, per the s188/s189 law.
- **Acceptance (green on the FIRST invocation, nothing weakened):**
  `python3 -m sim.selftest --map programs/maps/planet.MP --rules data/alpha.json` ->
  `PASS B1: 10/10 gates on planet.MP, planetx.MP`, rc 0 (`evidence/b1_selftest.txt:15-16`). Gates and numbers:
  sim's own .MP parser vs `scripts/decode_map.py` on the same bytes — parity tuples
  `(80,80,6400,143667,2739,128,5)` / `(128,128,16384,363525,2739,338,5)` (`:5`, `:9`); terrain-index set
  contiguous 0..15 with 0 out of range, both maps (`:6`, `:10`); owner nibble ∈ {0..7,0xf}, 0 invalid —
  planet `[3197,1,6,3,3,2,3,3,3182]`, planetx `[8192, …, 8192]` (`:7`, `:11`); cells with `+7==0xff` == header
  word 5 (3200/3200 and 8192/8192) (`:8`, `:12`); both dimensions checked (`:13`); 45 sections / 650 records,
  none empty (`:14`). `--map` self-expands to the sibling map (`:2`) because the rung demands 80×80 AND
  128×128 parity — an expansion, never a narrowing.
- **Cell structure MEASURED over both maps (corrects MAP_FORMAT.md):** cell+2 is **two nibbles** — high = a
  16-valued enum (all 16 used in both maps), low = the owner player index, `0xf` unowned, never 8..14.
  `+7 == 0xff` marks exactly the header's land-cell count in both maps. planetx.MP (fresh random map): every
  land cell is `0xf`, every sea cell `0x0`; planet.MP has 18 owned land tiles and 4 owned sea tiles.
- **LEAD (printed as `info`, not a gate):** cell+0 = `(cat<<5) | low5`, cat ∈ {0..6}, low5 ∈ {0,1,2,8,9,10,16,
  17,18} (9 values = two 3-valued fields, bit2 always 0); cats 1-6 are **100% land**, cat 0 is 59/3259 land
  (`evidence/b1_selftest.txt:3-4`). That is NOT the live `rec[0]&0xe0` category (FOOTING.md:119: ocean iff
  <0x60 would make cats 0-2 ocean, but 1 and 2 are all-land here), so the 22-byte file cell and the 44-byte
  live record at `*(0x92ae14)+(40y+(x>>1))*0x2c` are related by a transform nobody has named. Census pick.
- **Open:** terrain cardinality 16 is ASSUMED (a nibble cannot exceed 15, so gate 3 can only fail on GAPS);
  B2-B6 unbuilt; M181 box debt unpaid — a build fire builds (BUILD CADENCE), box debt is not a build rung.
