# BUILD_SPINE.md — the R1 build track (added 2026-11-01, session 187)

**Why this file exists.** After 226 milestones, `sim/` does not exist: every acceptance in this repo proves a
claim about `terran.exe`, and none proves the thing we actually want — a game that runs. Analysis is not the
bottleneck any more; nothing has ever been built. This track makes "distance to something runnable" a measured
quantity instead of a feeling.

**Cadence.** `python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` and `next_rung=B<n>`, derived from merged
history (3 analyse milestones between build fires). On `MODE=BUILD` the fire takes the rung below instead of a
census pick. Same rules otherwise: one PR per fire, closing order, gate GREEN, no box time needed (the build
track never touches the Wine process).

**What R1 is / is not.** R1 is a headless turn loop driven by parsed data — no UI, no graphics, no netcode, no
audio. It is Python in `sim/`, importing nothing from `scripts/` except the decoders it reuses. It must never
read `/proc`, never spawn gdb, and never load a game binary.

---

## Inputs already decoded (use these; do not re-derive)

| need | file | producer |
|---|---|---|
| rules tables (45 sections: RULES, TERRAIN, TECHNOLOGY, CHASSIS, WEAPONS, ...) | `data/alpha.json`, `data/alpha_schema.json` | `scripts/rules_parse.py` |
| maps, byte-exact | `data/planet_map.json`, `data/planetx_map.json` from `programs/maps/planet.MP` (143,667 B), `planetx.MP` (363,525 B) | `scripts/decode_map.py` |
| saves, split to the byte | `programs/saves/auto/*.SAV` | `scripts/decode_save.py --sections` |
| base records (pop, minerals, owner) | `evidence/m31_bases.json` | M31 |
| turn-engine ground truth | `evidence/m30_turn_trace.jsonl` — `{t, year, cur, tf, nb, own}` per transition | M30 |
| idle-economy ground truth | `evidence/m44d_idle.json` — 12 zero-order rounds, energy flat 15 | M44 |
| movement ground truth | M27 (units 117/118/120, 41→45/43, 3 MP per tile, 6 MP/turn) | `evidence/m27_solowrap2.log` |
| terraform ladder | M37–M41 (2 work/Former/turn, threshold 2× table `+8`, road/magtube mask swaps) | `evidence/m37c2_*`, `m41a_*` |

## Module layout (grow it rung by rung; one file per concern)

```
sim/__init__.py      sim/map.py       sim/rules.py    sim/save.py
sim/units.py         sim/base.py      sim/economy.py  sim/turn.py
sim/headless.py      sim/selftest.py  (tests/ optional, not required by the gate)
```

## The ladder — each rung has a RUNNABLE acceptance

A rung is done only when its command prints PASS. Record the numbers in `SESSION_NOTES.md` **with the command**
and put the console output under `evidence/` (cite it `evidence/<file>:<line>` — the gate checks citations).

**B1 — map + rules load.** `sim/map.py`, `sim/rules.py`, `sim/selftest.py`.
`python3 -m sim.selftest --map programs/maps/planet.MP --rules data/alpha.json`
must print PASS with: 80×80 and 128×128 tile counts equal to `decode_map.py`'s own counts for the same file,
terrain index in range for every tile, and every `alpha.json` section loaded with a non-zero count.

**B2 — save load into the same state model.** `sim/save.py`.
`python3 -m sim.selftest --sav "programs/saves/auto/<newest>.SAV"` must print PASS with the save's year, faction
count, base count and unit count matching `decode_save.py --sections` and `evidence/m31_bases.json` for the same
file (any mismatch is a finding: say which field and which side is wrong).

**B3 — turn engine.** `sim/turn.py`.
`python3 -m sim.selftest --replay evidence/m30_turn_trace.jsonl` must reproduce the recorded `(cur, tf, year)`
sequence for all transitions in the file, printing `matched=N/N` — N/N required, no tolerance.

**B4 — economy.** `sim/economy.py`, `sim/base.py`.
`python3 -m sim.selftest --replay evidence/m44d_idle.json` must reproduce the 12 idle rounds: our faction energy
flat at 15 (net 0), and the HUD scratch triple (gross, upkeep, net) equal to M46's `Σ base+0xfc`, `Σ upkeep`,
difference. Print per-round deltas; a non-zero net on an idle round is a FAIL, not a rounding note.

**B5 — units and movement.** `sim/units.py`.
`python3 -m sim.selftest --replay-m27` must replay the three recorded moves (117/118/120 off (41,11)) with the
same 3 MP cost per tile from `alpha.json` `#TERRAIN` movement, and leave 6 MP/turn. Tolerance: exact integers.

**B7 — the move slice (R2's first executable piece).** `sim/movesim.py`: load a .SAV, build
`sim/units` records from the save's OWN unit array, press the recorded M27 gesture (dir=1 east, the
trace's only direction) N times per unit, run the B3 turn engine, dump. The slice is R2's
"move a unit" leg replayed on save-loaded state - the trace's unit indices (117-120) live in a
different save's record array (m54b_clean has 67 units), so parity is on the GESTURE SEMANTICS,
not on those indices (stated, not hidden).
`python3 -m sim.selftest --b7 programs/saves/m54b_clean.SAV programs/maps/planet.MP --turns 5`
must print PASS with: units built from the save's array (count + owner set from the records);
every accepted east-press == the trace's (+2,0) delta at 3 MP; a third press REFUSED per unit
(FUN_005acc00 total-spent>0) with spent frozen at 6; year delta == turns per B3; two runs ->
identical sha256. Save-restore of unit positions is NOT simulated (no writer modeled) - ASSUMED,
declared in the dump.

**B6 — the headless run.** `sim/headless.py`. **DONE (s212)**: `python3 -m sim.headless --sav
programs/saves/m54b_clean.SAV --map programs/maps/planet.MP --turns 10 --dump sim_state.json` -> exit 0,
year 2150->2160, dump 8,455 B sha256 2efbc782e2075a26 (two runs identical); `python3 -m sim.selftest
--b6 <sav> <map> --turns 10` -> PASS B6 6/6, `evidence/b6_headless.txt`. R1 DONE in `MILESTONES.md`.
`python3 -m sim.headless --sav <save> --map programs/maps/planet.MP --turns 10 --dump sim_state.json` must exit 0,
write a stable dump, increment the year per the B3 model, and be deterministic (two runs → identical sha256).
This is R1 marked DONE in `MILESTONES.md`.

**B8 - the save WRITE (R2's save leg, first executable piece).** `sim/savewriter.py`: recompose
a `.SAV` container image from the parsed `sim.save` state model. Every layout constant is
recomputed by the writer (imported from `sim.save` but independently applied: prefix 12 | state
header 796 | own player 4 | block A 67,040 | block B 11,488 | small 32 | map header 2,724 | grid
W*H*22 | region map ((W+4)/5 rule) | 16,000 | u32 count + bytes | 3,584+26,624+4,096 | units 52n |
bases 304m | tail-to-EOF). Each byte is MODELED - composed from the model (version, counts,
year@84, cur_player@800 (0x985DCC via the M242 block identity), turn_flags@60 (bit 1 only; the rest
of the dword is declared pass-through), own player@808, map dims, each unit record's x/y) - or a
DECLARED PASS-THROUGH (block A/B, small table, the 16,000 section, middles, tail/trailer, the grid,
the region map, and the un-modeled bytes inside modeled records). The new-game leg was NOT chosen:
no recorded initial-state trace exists to parity-check against, and the spine forbids inventing
expected values.
`python3 -m sim.selftest --b8 programs/saves/m54b_clean.SAV programs/maps/planet.MP --turns 5`
must print PASS with: (1) identity round-trip - an unmutated written image == the original file,
byte-for-byte (the layout constants arbitrated on the real bytes); (2) `scripts/decode_save.py
--sections --anchors` on the written image prints the same section table as on the original;
(3) mutation - the B3 engine pressed N times, the written file re-parses with year == year+N and
every differing byte inside a MODELED span taking exactly the model value; a move of one unit's x
lands in exactly that record's two x-bytes; (4) the RIVALS FAIL THE SAME FIT - a pure re-emitter
(lift everything) fails the year mutation, a writer with UNIT_LEN perturbed by 4 fails the identity;
(5) two runs -> identical sha256, and `python3 -m sim.savewriter --sav <sav> --out <f>` exits 0.
No box time, no /proc, no gdb.

## Grading rules for a build fire

1. **Runnable or it did not happen.** The acceptance is the command's output, not a description of the code.
2. **Parity beats prose.** Every rung compares against a recorded trace or a decoder's own numbers. Do not
   invent expected values from the decompiled source when a trace exists.
3. **A mismatch is the milestone's finding**, exactly like a failed census gate: record both sides, name which
   one is wrong, do not edit the trace to pass.
4. **Never import the harness.** `sim/` may import `scripts/decode_map.py` / `decode_save.py` / rules parsing;
   it must not import gdb/Wine tooling or read `/proc`.
5. **No census detours.** If a rung needs a rule the decompile has not settled, take the smallest defensible
   value from `alpha.json`, mark it `ASSUMED` in the dump, and open a census pick for it — do not spend the
   build fire re-deriving it.
6. **B<n> in the commit and PR title**, so `track_mode.py` can count the cadence.

## Where this leaves the finish line

| chapter | state |
|---|---|
| D1–D4, F1, F2, C2 | DONE (proven live or byte-exact) |
| C1 turn engine | **DONE** — model written (M30) and executable (B3, s199: `sim/turn.py`, 67/67 on the recorded trace) |
| C3 economy | **DONE** — pipeline named (M46/M47) and executable (B4, s203: `sim/base.py` + `sim/economy.py`, 9/9 on the recorded idle trace, HUD triple 2/2/0 reproduced from the game's own globals) |
| C4 research, C5 combat, C6 AI | todo; the data tables are decoded, the rules are the census work |
| U1/U2 UI | todo; asset decoders exist (`cvr_decode.py`, `flc_decode*.py`, rendered frames in repo root) |
| R1 | **this track** — B1..B6 |
| R2 | IN PROGRESS - B8 save-WRITE leg DONE (s220); new-game leg todo |
| R3 | needs the R2 legs; golden-trace parity |
