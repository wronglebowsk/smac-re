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

**B6 — the headless run.** `sim/headless.py`.
`python3 -m sim.headless --sav <save> --map programs/maps/planet.MP --turns 10 --dump sim_state.json` must exit 0,
write a stable dump, increment the year per the B3 model, and be deterministic (two runs → identical sha256).
This is R1 marked DONE in `MILESTONES.md`.

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
| C3 economy | pipeline named (M46/M47) — B4 makes it executable |
| C4 research, C5 combat, C6 AI | todo; the data tables are decoded, the rules are the census work |
| U1/U2 UI | todo; asset decoders exist (`cvr_decode.py`, `flc_decode*.py`, rendered frames in repo root) |
| R1 | **this track** — B1..B6 |
| R2/R3 | need R1 first |
