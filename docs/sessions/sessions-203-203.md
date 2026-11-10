# Session notes archive — sessions 203-203

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 203 (2026-11-02, **B4 BUILD** — the round economy is EXECUTABLE: `sim/base.py` + `sim/economy.py` reproduce the 12 idle rounds and the game's own HUD triple)

`python3 -m sim.selftest --replay evidence/m44d_idle.json` → `PASS B4: 9/9 gates on m44d_idle.json`
(rc=0, 1.3 s, ONE invocation → `evidence/b4_economy.txt`; the `:N` below are that file's lines).
B1/B2/B3 re-ran green on the same tree (10/10, 7/7, 6/6): the new `--replay` dispatch keys on the
trace's shape (a JSON object with a `rounds` key = an economy trace, JSONL = the turn trace), so the
B3 path is untouched. Invocation 1 FAILED 8/9 on gate G5 and that failure is the finding below.

- **Idle replay (G1-G3, `:17-19`).** m44d's 12 rounds are a PRE-FOUNDING state: our faction (3) owns
  no base in any round — the trace's own `owners` map has no "3" key (`evidence/m44d_idle.json:138`) —
  so gross = Σ base+0xfc = 0, upkeep = 0, net = 0, and `matched=12/12` states with every per-round
  delta 0 against the recorded energy 15; the harness's own `deltas_per_round.energy3` = 0.0
  (`evidence/m44d_idle.json:811`). The recorded economy-pane OCR agrees: on the 3/12 rounds where the
  panel is legible, Gross Income / Total Costs / NET INCOME all read "0/turn"
  (`evidence/m44d_idle.json:150`).
- **The triple the GAME computed (G6-G7, `:22-23`).** On the recorded post-founding state the engine's
  (gross, upkeep, net) == (2, 2, 0) == the game's own globals `0x745734`/`0x744f28`/`0x7457dc` on both
  recorded rounds (`evidence/m46e_econ.json:56`), energy 19 → 19 == apply(net) with ledger 0, and both
  aggregator detail arrays reproduce byte-for-byte: per-base upkeep 0x744f2c, 75 entries, nonzero only
  at base 72 (`evidence/m46e_econ.json:102`) and the 39-wide item counts 0x745738 (`:61`).
- **Where the money comes from (G8, `:24`).** Our base's completed-facility bitmap — the dword at
  base+0x8c = 458, recorded live at `evidence/m46e_econ.json:16215` — decodes to ids {1,3,6,7,8};
  `data/alpha.json` `#FACILITIES` column 3 (alpha.txt:590's upkeep field) at line id−1 gives
  0,0,1,1,1 AND the names match (Headquarters, Recycling Tanks, Recreation Commons, Energy Bank,
  Network Node); raw Σ 3, and with the recorded disabled list (item 8) 2 == the recorded 0x744f28.
  G9 (`:25`): dropping the disabled list gives (2,3,−1), taking gross from +0x100 gives (0,2,−2), and
  indexing alpha without the +1 gives (2,3,−1) — only the chosen model matches the recorded triple.
- **CORRECTION (G4-G5, `:20-21`).** The base NAME FIELD IS NOT 20 BYTES: 3 of the 18 bases in every
  shipped save ("Morgan Energy Monopoly", "U.N. Court of Justice", "Valley of the Faithful") carry
  names up to 22 chars, and `scripts/m46_econ.py:106` reads `r[19:39]` — the harness truncates them,
  which is why invocation 1's seam gate failed on records 7/8/17 of all 17 saves. The field is
  NUL-terminated inside 32 B (sim/save.py's own window): 0/311 records lack the NUL, longest name 22.
  G4 decodes the recorded 76-dword live read and reproduces 13/13 of the harness's own field values.
- **OPEN (printed at `:14-17`, not graded).** alpha's upkeep column reproduces the five live-pinned
  item costs but NOT the four later values M46 read from the live table: Fusion Lab alpha 3 vs live 4,
  Quantum Lab 4 vs 3, Nanoreplicator 6 vs 4, Quantum Converter 5 vs 6 — the runtime item table's row
  order is not alpha's past id ~8, so `sim/economy.upkeep_table` is ASSUMED beyond the pinned five.
  Also ASSUMED: the bitmap's width (only the 4 bytes at +0x8c are a recorded read — ids 32..38 can
  never be set), the gifts term, and the spending ledger (both 0 on an idle round).
- Pitfall: a harness's own field-read WIDTH is not evidence of the field's width — check the file's
  own NUL padding, or a seam gate catches it 30 minutes later. No box time; terran.exe stayed down.
