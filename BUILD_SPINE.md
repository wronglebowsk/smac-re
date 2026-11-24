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

**B9 - the golden-trace pairing (R3's first executable piece).** `sim/parity.py`:
load a .SAV, press the B3 engine the recorded trace's OWN turn count, and require every
recorded per-turn snapshot to appear in the engine's emitted state sequence IN ORDER
(the m30 law: recorded rows may not be skipped, model rows may be extra). Golden trace:
evidence/trace_m54b40b_20261024_212833.jsonl - the ORIGINAL terran.exe's own 40-turn
run on programs/saves/m54b_clean.SAV (per-turn state_before/state_after snapshots of
year / cur_player / turn_flags / n_bases; the sibling m54b40 wedged at 30 rows, m54b40b
carries NO wedge field). The pair chain: before(0) == the save's (year, own, 0) and
before(t) == after(t-1) for every t; year_before == save year + turn on every row.
`python3 -m sim.selftest --b9 programs/saves/m54b_clean.SAV evidence/trace_m54b40b_20261024_212833.jsonl`
must print PASS B9 with: the 40 turn rows consecutive in order; the before/after chain
holds; all 41 recorded snapshots (before(0) + 40 after) found in the emission, 0
missing; year_before == 2150+turn on all 40; the RIVALS FAIL THE SAME FIT (a
reversed-order walk and a year_after=0 edge each miss the (2190,7,2) year-fire witness
- the same snapshot pins both the walk direction and the year edge); the n_bases
frontier is MEASURED and DECLARED (model constant = the save's count, recorded grows to
26: the sim has no AI base-founder - that delta is the finding, not a gate input); two
runs -> identical sha256; `python3 -m sim.parity --sav <sav> --trace <tr> --out <f>`
exits 0 and writes the report. No box time, no /proc, no gdb.

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

**B10 - the base-founder/destroyer leg (R2's new-game leg, first executable piece).**
`sim/basefound.py`: the M282 base-array ledger - founder FUN_004e47d0(faction,x,y)
(guard count less than 0x200; append a 304-B record at array start + old_count*0x130,
x u16 +0, y u16 +2, faction bytes +4/+5; count = count + 1) and destroyer FUN_004e4e10
(count-1 with COMPACTION - the LAST record moves into the freed slot, the m46e
"base array reorders during a watch" law) - plus the golden-curve pairing that presses
the B3 engine the recorded trace's own turn count and applies the trace's OWN per-turn
n_bases delta through the leg (the gate derives the 8 events from the rows: t8 +1,
t9 +1, t17 +1, t22 +2, t23 -1 (a real destruction), t27 +1, t32 +2, t34 +1).
`python3 -m sim.selftest --b10 programs/saves/m54b_clean.SAV` must print PASS B10 with:
(1) founder law - a founding appends one 304-B record at the END, count +1, own4/fac
bytes = the faction, x/y in-bounds, the 0x200 guard refuses a 513th founding;
(2) destroyer compaction - destroying slot k moves the LAST record into k (record
equality), count -1; (3) golden n_bases curve - the recorded 18->26 is recovered on
every one of the trace's 41 snapshots; B9's no-leg shape keeps 18 and the
all-events-on-turn-0 shape diverges at t0 - both rivals fail the same fit;
(4) a WRITTEN founded image - savewriter composes the grown ledger (records above the
original count compose as zero + x/y/faction; records below stay byte-identical), the
only prefix byte that changes is the bases-count dword, the tail is byte-identical,
and the image re-parses (n_bases 19; the zero-named record is invisible to the shape
scan - found 18, declared); (5) decode_save's walk sees the grown image exactly like
the original (its 64x64 limitation is pre-existing, see s226 notes); (6) two runs ->
identical sha256 and `python3 -m sim.basefound --sav <sav> --trace <tr> --out <f>`
exits 0; (7) a flooded 512-cap ledger writes with a byte-identical tail.
No box time, no /proc, no gdb.

**B11 - the production-queue mechanics leg (R2's "build" slice, next after B10's new-game leg).**
`sim/queue.py`: the M68-M72 queue law as an executable model, parity-checked against the
game's OWN recorded queue states. The law (settled, production-queue.md §M68-M72):
INSERT is `queue[pos] = item` with `pos = *(int *)(0x6a9480 + 0x3ff5c)` = the queue
widget's cursor row (M69); the widget's cursor has exactly three writers (M70):
row click `0x40aae5` sets `cursor = min(clicked_row, [[base]+0x4c] + 1)`, the enqueue
tail `0x417e3b` parks it at rows+1, and the `0x4d00` handler `0x4194b3` zeroes it -
so a post-INSERT read-back reads 0, not rows+1. The shift runs from
`min(9, max(pending+1, cursor))` down to `cursor+1`, the store uses the ORIGINAL
cursor, `pending++` only when `pending < 9` (cap 9). A negative slot value is the
TYPE's (196 -> -6, 195 -> -3, recordless ids); the head sentinel is `0xffffffd9`
= -39 (M68, correcting the -38 notes). A completion's POP pops ONE item when the
new head validates, and each iteration shifts only `0..pending-1` with pending
shrinking - K shifts are NOT "shift-left-by-K" (index k is written pending-k times
and `queue[pending]` keeps its STALE id: `[2,193,192,0] -> [193,192,192,0]`); the
completion writes the cursor field ZERO times. Affordability on the visit is the
visitor's OWN cost product at `0x4efa5e` (`cmp [base+0x40],edi`), NOT `price_of`
(M72: head 193 wants 27 where price_of says 18).
`python3 -m sim.selftest --b11 programs/saves/m54b_clean.SAV` must print PASS B11
with: (1) the cursor law - an INSERT lands at the poked cursor (m69: poked 4, wrote
at 4, cursor_after 6 = rows+1; m70: rowclick 3 -> cursor 1, insert at 1, tail 2,
insert at 2, tail 3, 0x4d00 -> 0); (2) the shift composition reproduces the
recorded slot arrays byte-for-byte at every armed event (evidence m69_cursor.jsonl,
m70_cursor_events.jsonl); (3) the negative store (-3 for 195, -6 for 196) and the
-39 sentinel; (4) the POP law - one completion pops one item, stale tail kept:
replays of evidence m71pop_seq.jsonl/m71pop3_seq.jsonl end with `[193,192,192,0]`
pending 1 exactly (the RIVAL shift-left-by-K gives a DIFFERENT read-back and must
fail); (5) the affordability gate - a replay of m72gate4 (storage 18, edi 27)
bails with queue untouched and m72gate5 (storage 27) pays + creates (the RIVAL
using price_of 18 pays at storage 18 and must fail); (6) a written queue state
round-trips through savewriter with a byte-exact tail (no box time, no /proc, no
gdb); (7) two runs -> identical sha256 and `python3 -m sim.queue --sav <sav> --out
<f>` exits 0 and writes the report. The new-game leg's frontier (the M282 G5
found-event scheduling) is DECLARED, not modeled - B11 replays recorded queue
states, it does not predict which turns found/write.

**B12 - the completion CREATE leg (R2's "build lands a unit" slice, next after B11's queue mechanics).**
`sim/production.py`: the M56/M59/M61 completion law as an executable model - when
the visit's gate passes, in the measured order the game RUNS (PAY -> CREATE ->
POP, production-queue.md): (1) GATE storage + income >= price (M56: the add is
inside the same visit; `price` = the recorded per-base price, `edi`, never a
recomputed `price_of`); (2) PAY storage = storage + income - price; (3) CREATE
a NEW 52-B unit record APPENDED at the end of the unit array (unit array at
`units_off`, stride UNIT_LEN, count n_units): x/y = the base tile's x/y,
flag(+4 u32) = 0, type(+10 u16) = the queue head id, owner(+14 u8) = the base
faction, order(+17 u8) = 0, nlegs(+18 u8) = 0 - a produced unit arrives order
0 ON its base tile (M56 accounting law); the record's other bytes are
DECLARED unmodeled (compose as zero + the named fields, test the re-parse);
(4) POP exactly one via B11's law (slots shift pending times, stale tail
kept). The recorded same-array acceptance: `python3 -m sim.selftest --b12
programs/saves/m54b_clean.SAV evidence/trace_m56_build_20261026_145157.jsonl`
must print PASS B12 with: (1) R0 replay - applying the model to the trace's
round_before r0 (base 17 Korolev (29,42) head 2 pending 1 storage 8 income 1
price 9) yields storage 0 AND exactly one new (29,42,2,3,order 0) record at
the array END (new-slot index == n_units-1) and pending 0, matching the
recorded round_after r0 net delta {+1 (29,42,2,3,0)} by (x,y,type,owner,order)
AND the recorded r1 round_before queue [2,2,2,2,0..] pending 0; (2) R1..R9
no-arrive - the gate fails (pending 0 / storage+income < price) on all nine
later boundaries and the recorded after-snapshots contain no (29,42,2,3,0)
arrival (M56's own verdict: net 1 in r0, none after); (3) the RIVALS FAIL THE
SAME FIT - a create at the WRONG tile (28,42) or with order 2 (the idle
order) or WITHOUT the income term (gate 8 >= 9 bails r0) each contradict a
recorded tuple; (4) a WRITTEN image - savewriter composes the grown unit
array: only the units-count dword and the ONE new 52-B record differ (tail
byte-identical, all originals byte-identical), the image re-parses with
n_units 68 reading the new record's modeled fields; (5) two runs -> identical
sha256 and `python3 -m sim.production --sav <sav> --trace <tr> --out <f>`
exits 0 and writes the report. No box time, no /proc, no gdb.

**B13 - the pod-driven founding-dispatch leg (R2's "AI founds a base" slice, next after
B12's completion CREATE; replaces B10's REFUTED (x,y) placeholder).**
`sim/hubfound.py`: the M290 founder-decision law executable: the hub's dispatch is
OWN-TILE-GATED (a distant target takes the msg 0x2408 "Auto-sending BUILD BASE
message" leg and can NEVER found), the founder's args are the POD's unit-record
fields (live vector loads owner +14, y +10, x +8; the sim reads its own save-view
record fields - there is NO channel from a scanned candidate tile to the founder),
and the founder's guard is capacity-only (B10's Ledger leg). Parity ground truth is
the M289 golden record - the first trace with REAL founding events:
`evidence/m289_gdb_raw.log` (7 FOUND ret=0x4ccbe2 fac/x/y/cnt rows + 2 DESTROY cnt
rows; cnt is the ledger count BEFORE the op) and the per-turn curve
`evidence/trace_m289_20261110_071759.jsonl` (m54b_clean, 30 turns, 18 to 23). Site
legality is judged in the 44-B RECORD view (M290 trap: the save's 22-B column byte0
is NOT the live category): rec=(W/2)*y+(x>>1), off=grid_off+44*rec, cat=(byte>>5)%8,
land=3..6. The pod WALK (which pod, which target - the scan's score law at
0x563c00-0x563d40) is DECLARED, not modeled: the leg takes the pod+target press as
input; the walk is the next ANALYSE frontier. The destroy slot is ASSUMED last (the
log rows carry only cnt).
`python3 -m sim.selftest --b13 programs/saves/m54b_clean.SAV` (defaults: the two
m289 evidence files) must print PASS B13 with: (1) constants - msg 0x2408, CAP
0x200, strides 52/304, and the pod record composes via B12's create_record and
reads back through the save-view fields; (2) record - exactly 7 foundings (all
ret=0x4ccbe2) + 2 destroys, the DESTROY rows strictly between F3/F4 and after F7;
(3) dispatch leg - each recorded founding, pressed as its pod record at its own
tile, returns ("found", fac, x, y) == the recorded tuple (7/7); (4) own-tile gate -
the same 7 pods pressed at a DISTANT target yield ZERO foundings and 7 msg 0x2408;
(5) the RIVAL ungated dispatch, founding at the TARGET on the distant leg, yields 7
tuples of which ZERO occur in the record (it fails the same fit); (6)+(7) legality -
all 7 recorded sites are land (cat 3-6, record view) AND none is already a base tile
of m54b_clean; (8) strict ledger - replaying the 9 log rows through the B10 leg from
the save's 18 records, every row's pre-cnt agrees with the model, endpoint 23, peak
24; (9) curve - the jsonl curve ends 23 == the model endpoint, peaks 24, and every
sample sits in the global envelope [18-2, 18+7]; (10) the RIVAL B10 placeholder
(row-major first-unoccupied + fewest-bases faction) reproduces ZERO of the 7
recorded tuples (the refutation restated as a gate); (11) written image - savewriter
composes the grown ledger: the only prefix diff is the bases-count dword, the
original 18 records are byte-identical, the 5 added records equal the surviving
foundings' record_bytes (the 2 destroyed ones ABSENT), the tail is byte-identical,
and the image re-parses with n_bases 23; (12) two runs -> identical sha256 and
`python3 -m sim.hubfound --sav <sav> --out <f>` exits 0 and writes the report.
No box time, no /proc, no gdb.

**B14 - the hub scan + walk dispatch made executable (R2's "AI pod chooses and
walks" slice, next after B13's founding dispatch; written by this fire from
B13's DECLARED frontier plus M291/M292's laws - track_mode counts rung numbers
from merged history, so a build fire whose rung is not yet in the spine authors
it).** `sim/podscan.py`: M291's scan law executable - a STRICT site-value
argmax (score = rec byte2 high nibble) over the literal 25-entry ring table
(transcribed from the recorded file-image dump `evidence/b14_ring_table.txt`,
written by `scripts/b14_ring_dump.py`; sim/ never loads terran.exe),
eligibility = cat-flag equality + rec byte3 owner-equality + rec+9 bit 0x20
clear + unoccupied, ties keep the closer entry - plus M292's dispatch table
keyed on the ring ENTRY INDEX esi: 0 -> founder, or msg 0x2408 under s240's
msg_gate(global != 0 AND owner == human); 1..8 -> continue, NO order; >=9 ->
WALK: issue order 0x62 at the wrapped ring tile (walk_target, FUN_00469010
semantics). ACCEPTANCE `python3 -m sim.selftest --b14 programs/saves/m54b_clean.SAV`
prints PASS B14 with: (1) ring literals == the recorded dump + center/diamond/
ascending laws; (2) the 7 recorded m289 foundings ALL self-argmax through the
sim scan (grown occupancy, 44-B record view) 7/7; (3) rivals fail the same fit
(no owner-gate loses exactly fac1 (27,29); B10 row-major placeholder 0/7);
(4) the m292 census shape (29 DISP / 11 ISS / 9 HUBFOUND / 9 FOUND / 0 MSG,
st==8 on every row, own == (ownrec == curfac) 29/29); (5) the dispatch legs
partition the DISP rows 9 found / 9 continue / 11 walk / 0 msg AND pair every
ISS with its immediately-preceding DISP (same u, same esi, esi>=9) and every
HUBFOUND with an esi==0 DISP on the same tile, every FOUND with the
immediately-preceding HUBFOUND tile; (6) walk-target X == (pod_x + dx[esi])
mod W on 11/11 ISS rows (the instrument printf's the X field only at 0x563e3b -
the target-Y law is static-gated, DECLARED); (7) the table-swap rival (the dy
table read into the X slot) reproduces 0 of 11; (8) the census-window ledger
is count-strict 19->27 over its 10 op rows, endpoint == the recorded POST
count; (9) the msg-gate case table + solo inertness (ds:0x920434=0 AND every
row own=0 - structural per s240); (10) the SELECTION itself, brute-forced
on a fixed sample - scan_esi == max-value/lowest-index argmax everywhere,
and the sample provably discriminates (200 tiles where first-better and
argmax differ; added because Greptile P1 caught a first-better bug the
founding fit could not see, the fit only ever checks esi==0), and the
scan wraps X (0x469010) but BOUNDS-CHECKS Y (0x469060) - Y never wraps;
(11) two runs -> identical sha256 and
`python3 -m sim.podscan --sav <sav> --out <f>` exits 0. DECLARED UNMODELED
(the fits passed without them, as in M291): the 0x94e5a8/0x94eca8 per-site
gate tables, the 0x4e3c00 no-go, the rec+8 bit-0x1000 zero-leg and the lazy
FUN_005aff90 value fallback. No box time, no /proc, no gdb, no game-binary load.

**B16 - the pod-scan loop HEAD PRE-CHECK CHAIN made executable (R2's "which ring entries are even
candidates" slice; written by s245 from B14's DECLARED list + M294's named gates - the rung was not
yet in this file, so the build fire authored it, as B14 did).** `sim/precheck.py`: the 7 tests the
loop applies per slot BEFORE the B15 price gate (byte pins in `PINS`, arbitrated against
`evidence/b16_precheck_window.txt` written by `scripts/b16_pin_window.py` - objdump -M intel from the
function entry, never from an arbitrary address): bounds (`call 0x469060` range-tests BOTH legs, X
pre-wrapped by 0x469010 so only Y bites), class ((byte0&0xe0)<0x60 == [ebp-0x58]), byte8&0x20 needs
cat<2, elevation band (byte5&0xc0)>0x40 needs cat<3, region (byte3 == [ebp-0x34] = the POD tile's
byte3), occ (byte9&0x20), and the UNMODELED no-go `call 0x4e3c00(owner,X,Y)` (M294's (x,y,owner)
order corrected). THEOREM, from 0x563812-0x563817: the scan is entered only when the unit type's
required class ([ebp-0x40]==1) equals the POD tile's own water flag, so required class ==
classflag(pod tile). Parity target = the per-visit SET of slots that printed a decision row
(GDEEP or GACC) in `evidence/m294_gate_rows_raw.txt`, read through the B16 TRANSPOSITION LAW (`x=`
is the Y leg, `y=` the X leg).
`python3 -m sim.selftest --b16 programs/saves/m54b_clean.SAV` must print PASS B16 with: G1 all 31
byte pins resolve; G2 pod recovery consistent on 1026/1026 decision-row visits and 201/201 against
the DISP unit-record x/y (rivals: untransposed reading 638 and 0); G3 zero recorded decision slots
violating bounds/elev/occ; G4 every modelled test excludes >=1 recorded skip slot (fail&skip 110 /
5036 / 9311 / 3304 / 5880 / 389) with the never-sole-excluders (bounds, class) named; G5 one class
flag and one region byte per visit (0 mixed of 1026); G6 the pinned confusion grid 2128 / 193 /
8482 / 14847 plus the per-check and solo tables reproduced; G7 two runs byte-identical. DECLARED
UNMODELED: the no-go (the 8484-pass-without-row population is its measurement - 8482 with the pinned
baseline) and the save-vs-window per-tile drift (class fail&rec 106 / region 192, all-or-nothing per
visit). No box time, no /proc, no gdb.

**B17 - the pod-scan loop DECISION CORE made executable (R2's "the pod picks its
slot" slice; written by s248 from M296's FITTED argmax chain + B15/B16 - the rung
was not yet in this file, so the build fire authored it, as B14/B16 did).**
`sim/scanleg.py`: the chain composed into ONE slot-strict replay - model
best_init (M296 law 0x563836-9f: 0 unless case-8 + order-0x18 move-to-base
beyond wrapped-diff 2, then value(save-view dest tile)-1; save-invisible dest
values and machine-nonzero inits are the DECLARED-live input class) + per-slot
gt.price_gate over the RECORDED machine val/dist/gate bytes + the accept store
(0x563caa) moving best AND winner + the 25-slot trajectory, over the m294 grid
through sim.precheck (B16 transposition law).
`python3 -m sim.selftest --b17 programs/saves/m54b_clean.SAV` must print PASS
B17 10/10 with: G1 pins 1026/2321/25650/260/61; G2 init law 1023/1023 gradeable
+ 3 DECLARED-live, S7b buckets, case-8 leg 1/1; G3+G4 the GROW best AND win
columns replay 25650/25650; G5 accepts 260/260 from the replayed best (bypass
61, gate-legs 199), 0 GDEEP at/over the 2*(8-dist) cap; G6 winner == DISP esi
201/201; G7 save-view val-law 1931/2321 (lazy 1, ties 0, 0x1000 pool-side 1083);
G8 pool 6048/8482 explained, 2434 DECLARED; G9 rivals fail the same grid
(>=-argmax 5721 ties, frozen-best 1713, no-bypass +61, no-init-law 24); G10 two
runs byte-identical. No box time, no /proc, no gdb.
**B18 - the site-gate VALUE SOURCE + MAX STORES made executable (R2's "who caches
a site value and where does it land" slice; written by s252 from M298's CLOSED
FUN_0051dcb0 semantics on top of B17's decision core - the rung was not yet in this
file, so the build fire authored it, as B14/B16/B17 did).** `sim/sitegate.py`: the
three M298 laws executable. (1) the LAZY-NIBBLE CACHE: `edi = BYTE[rec+2]>>4` when
nonzero ELSE the 525-insn FUN_005aff90 result (the recorded machine val column is the
DECLARED input, as in B15/B17) - the pinned branch at 0x51df8d (`jne 0x51dfac`) runs
the lazy call AND the write-back ONLY on a zero nibble; FUN_00582cc0 writes back
`BYTE[rec2+2] = (old&0x0F)|(edi<<4)`, a 4-bit HIGH-nibble overwrite that PRESERVES the
low nibble, on the SAME record byte the pod-scan score getter reads
(rec2 = [0x92ae14] + 0x2c*([0x692184]*Y + sar(X,1))). (2) the SITE BYTE: the store
index `[ebp-0xc]` = zero-extended `BYTE[rec+3]` (sole store 0x51dd57, own frame - the
11 e8-callers REFUTED). (3) the TWO MAX STORES: slot `[0x989ce8 + 28*site] = max(edi,
old)` (UNCONDITIONAL) and cell `[0x94eca8 + 8380*block + site] = max(edi, old)`,
SKIPPED when `block == 0` after the -1 sentinel clamp - `block` = `BYTE[rec+7]`, the
record's owner byte (8380 = the recorded 8-block owner fold; site_gate = block 0x94d448
+ 0x1860, B15). PINS = the 62 instruction windows transcribed from
`evidence/s251_statics_fn51dcb0.txt`, and the LAWS are DECODED from the pinned bytes by
the shipped decoder (the nibble split; no edi/esi/ebx named anywhere in the 19-insn
callee, so edi SURVIVES; both store chains MAX by the `cmp edi,eax` / `jle L` / `mov
eax,edi` / store form with the jump landing over the take and no branch between L and
the store - a MIN store would need `jge`; no cmp/test/branch at all inside 0x582cc0, so
the cache is an overwrite NOT an accumulator; the `(site*8-site)<<2` = 28 B stride and
its +4 counter field, which the RETRACTED 4x-value phrasing would alias onto the next
slot). Parity targets: the recorded m294 window rows (B17's loader, B16's transposition
law) + the recorded s249 end-window live-record dump.
`python3 -m sim.selftest --b18 programs/saves/m54b_clean.SAV` must print PASS B18 10/10
with: G1 62/62 pins + the 10 decoded laws; G2 the write-back target == the score byte on
4096/4096 tiles + the exhaustive 256x32 nibble law (the cache is 4 bits - an edi>15
truncates); G3 the cache state machine over 2321 rows / 101 tiles - 2288 cached-path
hits / 1 lazy write-back / 32 adopted live mutations, tiles re-valued inside the window
9 (RECORDED M296 S3b) carrying 230 rows (RECORDED), replayed end-state nibble == the dump
on 86/101 tiles (the 15 = the declared A5 post-grading drift); G4 the save-seeded read
path 1931 match / 1 lazy / 389 mutation (RECORDED 1931 and 1); G5 the s249 snapshot 2102
match / 134 bit4 / 85 nibble / **0 lazy** (RECORDED M297 S3 verbatim - the cache law's own
observable: a recorded nonzero val never meets a zeroed nibble) + the write-back signature
177 records high-nibble-changed, 103 of them low-nibble-preserved; G6 the nibble moves BOTH
ways (182 down / 31 up) so it is an overwrite, not an accumulator, and the low-nibble getter
rival matches only 76 rows; G7 site = BYTE[rec+3] {1: 2253, 9: 68} with max site under the
128-entry region bound, 1026/1026 single-site visits, the -1 owner sentinel on 277 rows ==
the cell-store skip class, 0 records with a legitimate 0 owner (so the skip class IS exactly
the unowned tiles), rival "site = the 22-B column byte0" diverging 2321/2321, and the pinned
inner walk (x += 2 to ds:0x92a378) covering exactly one 32-record row; G8 the MAX funnel over
2321 walk steps - 2 slot entries, 5 cell entries over 5 owner blocks, 277 cell-store skips,
every table monotone and each slot ending at the recorded MAX, the last-write rival diverging
on 1 slot and the min rival on 1 (the table CONTENTS are DECLARED unrecorded - a read-only
/proc window over 0x989ce8/0x94eca8 grades them absolutely: LEAD); G9 the 10 rivals refuted
by recorded numbers; G10 two runs byte-identical + `python3 -m sim.sitegate --sav <sav> --out
<f>` exits 0. DECLARED UNMODELED: the FUN_005aff90 value body, the slot `[+4]` visit counter
(its ++ is gated on call 0x5832b0), ebx's walked-table provenance beyond the owner-byte reading
(M298 LEAD), the live table contents, and every M297 A5 end-window caveat. No box time, no
/proc, no gdb.

**B19 - the slot `[+4]` visit counter made executable (R2's "which sites get visited and how
often" slice; written by s257 from B18's DECLARED list + M299/M300/M301's landed laws - the rung
was not yet in this file, so the build fire authored it, as B14/B16/B17/B18 did).**
`sim/visitcounter.py`: the M299 counter law executable. (1) THE GATED INC: after the B18 MAX
stores, FUN_0051dcb0's tail block 0x51e00d-0x51e01b does `ecx=[esi+0x989cec]; ecx++;
[esi+0x989cec]=ecx` - the [+4] field of the SAME 28-B slot (0x989cec == 0x989ce8+4, the SAME
pinned esi = 28*site) - SKIPPED WHOLE when `call 0x5832b0` at 0x51dffd returns 0 (test/je
0x51e005/07, je target 0x51e11d past the store, no branch into the block's interior).
(2) THE LADDER (FUN_005832b0 over the shared 44-B fold): rung1 `dword[rec+8]&0x102000` -> 0;
rung2 `ds:0x985ac4&0x2000` set -> `(dword&0xc000000)?2:0`; rung3 `dword&0x10000000` -> 1;
rung4 `ds:0x92a380`(rand+1)==0 -> 0, else the lattice: branch A `(BYTE[rec+0]&0xe0)>=0x60`
accepts iff `(h&3)+4*(d&3)==(-5*sar(h,2)-3*sar(d,2)+rand)&0xf` for h=sar(x+y,1), d=x-h
(-> 2); branch B accepts iff `(h&3)+4*(d&3)==(rand+8+trunc4(h)*ds:0x692210+trunc4(d)*
ds:0x69220c)&0x1f` (-> 1), trunc4 = the pinned div-by-4-truncated-toward-zero. EVERY model
constant is READ OUT OF the pinned W1/W2 windows INSIDE evidence/m299_visitgate.txt (the module
parses the evidence file as its instruction source); the branch-A lattice runs as TWO
implementations (pin-decoded chain vs the recorded closed form) that must agree. (3) THE LIVE
STATE: `Live(flag2000, rand, s20c, s210)` - all four UNRECORDED (None = the game's real value is
unknown), so the counter reports THREE columns per site: CERTAIN (accepts in EVERY live state =
pass1 & bits26/27 & bit28), the DECLARED baseline `Live(flag2000=False, rand=1)` column, and
POSSIBLE (accepts in SOME live state - every pass1 row, since flag/rand/strides can each be
made to accept). Parity targets: the recorded m294 decision rows (B17 loader + B16 transposition
+ B18 site law) through BOTH record views (save and s249 live), the M299 G7 census, the M300 S2
table, and the M301 A6 witness - all re-derived, not re-asserted.
`python3 -m sim.selftest --b19 programs/saves/m54b_clean.SAV` must print PASS B19 10/10
(evidence/b19_visitcounter.txt, table THEN gates): G1 44+114 pinned instructions parse and
every constant decodes (rung masks, globals, coefs -5/-3, counter field +4, stride 28, 6 rets,
0 callee stores, pops-before-every-ret, eax=1 legs flag-clear-only); G2 fold 44*(W2*y+sar(x,1))
4096/4096 random incl. negative x (RECORDED 4096/4096) and 28*site 2048/2048 (RECORDED); G3 the
s249 dump digest 093d10a868da55b2 + the RECORDED rung census 481/16/12/5/1087 through the
model's OWN readers; G4 the 36 (H,D) x 16 lattice theorem (RECORDED 36/36) + the two branch-A
implementations agree on 76960 draws; G5 outputs stay in {0,1,2} over 2048 records x 32 sampled
live states, the CERTAIN class never refuses under ANY flag state, the flag-set+sel-clear leg
refuses all 1565 such records (pinned neg/sbb/and-2 polarity); G6 the 24-row M300 table
re-parsed: 21/2/1 classes, 17/1/6 reach, the SINGLE IN-WRITER row agrees with the W1 bytes
line-for-line; G7 the M301 A6 eax-witness EQUALS the list re-derived from the W1 bytes (window-
bounded), 0 backward edges, je 0x51dff5 lands BEFORE the call; G8 the 2321-row replay: per-site
rows {1:2253, 9:68} == B18's RECORDED site anchor, census {'branchA':1099,'rung1':1222}
partitions exactly, 1222 CERTAIN-refuse / 0 CERTAIN-accept / 1099 POSSIBLE, baseline 20 accepts
(all eax=2) / 1079 undecided; G9 the four rivals (ungated / MAX-field-alias / je-jumps-only-
the-load / ebx-gates-the-call) each refuted on recorded numbers, with the eax=1 return DECLARED
structural-only in this window (0 graded rows reach it); G10 two runs byte-identical (report
sha256 e161b2f9... committed as evidence/b19_visitcounter.txt) + `python3 -m sim.visitcounter
--sav <sav> --out <f>` exits 0. DECLARED UNMODELED: the live VALUES ds:0x92a380 (rand+1),
ds:0x69220c/0x692210 (branch-B strides) and the ds:0x985ac4 bit-0x2000 (address witnesses
only, m299_visitgate.txt:175-178 - the NEXT /proc window that grades the counts ABSOLUTELY
dumps exactly these four + the 0x989ce8/0x94eca8 tables); the live CONTENTS of the counter
table itself (the B18 LEAD, now covering +0 AND +4); the 0x51e02c post-counter region read
0x94ed28 (NAMED:371) and everything downstream; which loop drives FUN_0051dcb0 visits at
runtime (replay over RECORDED rows, as B17/B18); which of the 17 REACHES callers actually run;
and the save-vs-window record drift (both views replayed, 4008 field deltas COUNTED not
smoothed). No box time, no /proc, no gdb, no game-binary load.

**B20 - the BYTE-twin visit counter made executable (R2's "one gate, two table
widths" slice; written by s261 from M303's byte-family census + M302's pinned state +
B19's gate law - the rung was not yet in this file, so the build fire authored it, as
B14/B16/B17/B18/B19 did).** `sim/bytecounter.py`: the M303 byte law executable. The
post-counter read 0x51e02c is the LOAD HALF of an in-place BYTE `++` (lea 0x51e033 SAME
SIB+disp tail, `inc dl` 0x51e03a, store 0x51e03e, ZERO branches in between, the `je
0x51e040` AFTER the store tests `test ebx,ebx` flags not the byte) on the per-block BYTE
twin 0x94ed28 = 0x94eca8+0x80 {MAX@+0, CNT@+128}, entry width 1 B, 128 entries/field,
8 blocks x 8380 B (fold 65->131->2095 *4 and init `add edx,0x20bc` - the stride derived
TWICE; every constant decoded from the instruction windows embedded in
`evidence/m303_downstream.txt`, the module parses its own evidence file as instruction
source, as B19 does for m299). The `++` rides the SAME gated fall-through as B19's dword
`++` (past `je 0x51e007`), so per visit the byte table and the dword table increment on
IDENTICAL rows; the asymmetry is on the MAX side: the byte MAX store (0x51dfe2-dff3)
keeps B18's `test ebx,ebx` block-0 skip while the byte CNT does NOT. The live state is
the PINNED one parsed from `evidence/m302_livepins.txt` (flag2000=False rand=9661
s20c=61 s210=11), the rows are the recorded 2321 m294 decision rows (B17 loader + B16
transposition + B18 site/block laws), and EVERY replay census is graded against numbers
PARSED from the recorded evidence text (m302_livepins.txt + b18_sitegate.txt) - parsed,
re-derived, asserted equal; the anchor tables' internal coherence is itself a gate.
`python3 -m sim.selftest --b20 programs/saves/m54b_clean.SAV` must print PASS B20 10/10
(evidence/b20_bytecounter.txt, table THEN gates): G1 the pinned windows parse (fold 7/7,
rival-28 law 7/7, init 23/23, RMW block 10/10 insns; S0 corpus 11 = MAX 8 / CNT 3, all
RECORDED); G2 every constant decoded from the BYTES (65/131/2095, scale 4, stride 8380
== init step, CNT-MAX gap 0x80 == init +0x80, 128 entries width 1, 8 blocks rem 0, dword
twin 0x989ce8 stride 28 slots 128, load/lea operand tails identical); G3 the byte++ is
ONE straight line behind the B19 je (zero jumps in the interior, je 0x51e007 rel32
DECODES from its hex to 0x51e11d past the store, the store-unconditional claim parsed
from the recorded full-dump line); G4 the pinned replay reproduces M302's recorded
census exactly (38 accept / 2283 refuse / 0 undecided, eax {0:2283, 1:1, 2:37}, kinds
branchA 1099 -> rung1 1222, branchA-only per-site split {1:[38,993,0], 9:[0,68,0]});
G5 the byte table is a legal byte table (all values <256, no wrap witness, MAX never on
block 0); G6 the byte-MAX funnel == B18's SiteGate replay byte-for-byte AND B18's own
recorded numbers (2 slots, 5 cells over 5 blocks, 277 skips == 277 sentinels); G7 THE
POINT: one accepted-visit set feeds both widths - 38 accepts -> 38 dword increments over
sites [1] AND 38 byte increments over [(0,1),(3,1),(6,1)], per-site
sum_blocks(byte CNT) == dword CNT (both record views); G8 the six rivals each refuted on
recorded numbers (ungated 2283 / eax==2-only 1 - the eax=1 leg is a REAL row here /
28-law index 2/2 keys / CNT-rides-the-MAX-gate 1 - one accepted block-0 row exists /
MAX-un-gated 7-vs-5 cells / pure-read 38); G9 the parsed recorded tables are internally
coherent (sums, the parsed live state == the model's own state string); G10 two runs
byte-identical + `python3 -m sim.bytecounter --sav <sav> --out <f>` exits 0. DECLARED
UNMODELED: the live CONTENTS of the byte MAX/CNT tables (M302 pinned the dword twin
only); the live upper bound of the block byte (fold+init imply <8, no static bound-check;
graded rows carry only -1 or 1..8 - B18 G7); the per-call zero-rebuild CADENCE
(FUN_0051dcb0 zeroes BOTH families at entry - the replay is the window-level accumulation
model, as B18/B19; the function's callers/cadence stay OPEN); the post-store dispatch and
the settle nest (1<<block gates, FUN_0056d480/0056d630, ds:0x985b10/0x985aec, the
byte-field @0x950664 8-row walk - M303 S7/S9, M304's OPEN settle-nest MEANING - the byte
++ never gates them); save-carry vs rebuild of the byte family; the sibling fields of the
8380-B record; the save-vs-live record drift (BOTH views replayed, 3 diverging byte-CNT
entries COUNTED not smoothed). No box time, no /proc, no gdb, no game-binary load.

**B21 - the m289 run as ONE composed state object, written, reloaded and RESUMED
(R2's "the legs run together and the save survives the round trip" slice; written by
s267 from B3+B8+B10+B13 - the rung was not yet in this file, so the build fire
authored it, as B14/B16/B17/B18/B19/B20 did).** `sim/composedrun.py`: ONE state
object - the save's base ledger + the B3 turn engine - pressed once per recorded m289
turn, with the recorded op stream (`evidence/m289_gdb_raw.log`: 7 FOUND + 2 DESTROY,
`cnt` = the ledger count BEFORE the op) applied BETWEEN presses by a DP that
enumerates every placement of the 9 ops into the 30 turn intervals that reproduces the
recorded `n_bases` curve (K = 11 feasible; the run takes the lexicographically earliest,
a declared tie-break). **THE RUNG'S MEASUREMENT: the per-turn curve is strictly coarser
than the op log** - a curve-matching schedule needs only `sum|delta|` = 7 ops, so exactly
one turn hides a net-zero (+1,-1) pair; the curve-only schedule still matches the curve
30/30 but hits only 7 of the 9 recorded (kind, pre-count) rows, the model schedule 9/9.
Then the B8 writer composes BOTH modeled header fields at once (year@84 2150->2180 AND
the bases-count dword 18->23) plus 5 grown 304-B records; `sim.save` RE-PARSES the image;
and the NEW leg presses the reloaded state once more, requiring
(write-then-press) == (press-31-times-then-write) BYTE-FOR-BYTE.
`python3 -m sim.selftest --b21 programs/saves/m54b_clean.SAV` must print PASS B21 12/12
with: G1 anchors re-derived (save year == trace year_before(0), save n_bases == trace
start, the op chain a closed walk 9/9); G2 the turn law (year_before == save_year+turn
30/30; the trace self-chains on 29/29 boundaries for year AND n_bases; the engine
emission supplies all 31 distinct recorded (cur,tf,year) samples IN ORDER - adjacent
samples of one state collapse because the recorder's after(t) IS its before(t+1));
G3 curve 30/30, endpoint 23, peak 24; G4 the coarseness measurement (7 < 9, K = 11);
G5 op fidelity 9/9 vs the rival's 7/9; G6 the 5 grown slots == the surviving recorded
foundings and neither destroyed site is a base any more; G7 the image grows by exactly
1520 B = 5 x 304 with the tail after the grown array byte-identical (10,800 B); G8 the
header diff is 2 bytes, at the bases dword and the year word, both inside modeled spans;
G9 the reload (year 2180, 23 records, record-for-record equality, and the SAVED cur_player /
modeled turn_flags bit / year read back equal to the model's - the resume engine is built from
the FIELDS IN THE IMAGE, never from the model); G10 the RESUME commutation (the resumed image ==
the 31-press image byte-for-byte; img->img2 differs in the 1 changed year byte); G11 five rivals
fail the same fit (no-leg 6/30, all-ops-at-end 7/30, curve-only 30/30 curve but 7/9 ops,
FIFO-destroy keeps a destroyed tile, and a writer that leaves cur_player in an AI slot is
REFUSED a press by the resume leg - the proof the leg can see a broken turn-field write); G12 two
runs -> identical table text and identical written-image sha256. DECLARED UNMODELED: on
WHICH turn each op really fired (the curve admits 11 placements, the log carries no turn
stamp - the earliest is a tie-break, not a measurement); the destroy slot (last, as B13);
everything a founding does to economy/research/units (the run tracks year, cur/tf and the
ledger only); the recorder's mid-cycle sampling law (used as recorded, not modeled).
No box time, no /proc, no gdb, no game-binary load.

**B22 - the save's TWO record arrays grown in ONE write, with the CREATE leg fed by
the RELOADED base record (R2's "records round-trip through the writer in both
directions" slice; s273 authored this rung from main, as B14-B21 did).**
`sim/composedgrowth.py`: B21's composed run (the m289 founding run as ONE state
object) is written once more, now growing BOTH arrays in the SAME call -
`sow.build_image(bases_override=<the 5 grown 304-B records>, append_units=<ONE new
52-B record>)` - and the new part is WHERE THE CREATED UNIT'S INPUTS COME FROM: B12's
CREATE law takes the tile and the faction **from the base's 304-B record as RELOADED
FROM THE WRITTEN IMAGE** (`sosave.parse(img).base(i)`), not from the model's
in-memory founding tuple. That is the first test of the save's INBOUND half (base
fields -> a later leg's args); B21 proved only the OUTBOUND half (the model's fields
survive into the image), and B12 proved CREATE's bytes in memory but never read its
input out of a container.
`python3 -m sim.selftest --b22 programs/saves/m54b_clean.SAV` must print PASS B22
12/12 (authored once, in `sim/composedgrowth.py`, which `--b22` only relays - so the two
entry points cannot print different text) with: **G1** B21's own pipeline re-derives green
(curve 30/30, op fidelity 9/9, 5 grown 304-B records, reload equal), because this rung
builds ON B21, not beside it; **G2** the B21 image alone re-parses (`n_bases` 23 == the
model's, `n_units` 67 unchanged, year 2180) AND the shape locator's own verdict is measured
rather than assumed: it CONFIRMS ONLY the 18 named bases of the 23, because M282's founders
write an EMPTY name span and `sim/save._base_ok` wants `[ -~]{3,30}\x00` at +19; **G3** the
unit record comes from ONE shared producer `record_from_image(image, idx, head)` reading the
image's base[22] (at (27,29) fac 1, queue head 2 VERBATIM per B11/M68) and is byte-equal to
B12's own `soprod.create_record` for those fields - same producer, no re-implementation;
**G4** the ONE write grows BOTH arrays (+1572 B = 5x304 + 52, against B21's bases-only
+1520 B) and fidelity is measured BAND BY BAND at the MEASURED layout `[unit originals
3484][the ONE new unit 52][base originals 5472][the grown bases 1520][tail 10800]` B, each
band byte-equal to its own source (the first draft asserted "units_off..EOF == original
lifted by one amount" - FALSE: only the tail lifts by 1572, the base originals lift by 52);
**G5** count and shape AGREE on all three containers (`bases_pred == bases_off`, `closes`
True on orig/B21/B22; the base array moves +52 B, the unit anchor does not) - this gate
carries an explicit RETRACTION of the "the two methods DISAGREE by the unit growth" claim,
which was the run's arithmetic (a 68-unit count read against a 67-unit image), not the
file's geometry (Greptile P1 on #286); **G6** byte->field round-trip on the base array: all
18 original records byte-identical, all 5 grown records byte-equal to the founder's own
`basefound.record_bytes`, each grown record's parsed (x, y, own4) == the model's tuple;
**G7** the header diff is EXACTLY 3 bytes (`0x44` -> 68, `0x48` -> 23, `0x54` -> 2180), all
inside modeled spans - MEASURED: asserting 4 "one per modeled field" is decoration, since
cur/tf already hold their recorded values in this save; **G8** the doubly-grown image
re-parses (n_units 67->68, n_bases 23): the 67 original unit records byte-identical, the new
record AT THE ARRAY END, `units_off` unmoved / `bases_off` +52 B / tail +1572 B, parsed
x/y/type/owner == the base tile read from the first reload; **G9** THE FALSIFIER, through
that SAME shared producer and corrupting BOTH claimed input sources - tile AND faction IN
THE IMAGE (1447,1448, fac 5A) - asserting the created unit CARRIES the corrupted bytes
(x/y span, owner byte), not merely that it differs; **G10** rivals fail the same fit (grow
only the unit array so the grown bases are lost; the idle order-2 record is not the produced
record; a perturbed unit stride mis-places the tail); **G11** a second independent
`compute()` reproduces the written image sha256 byte-for-byte and the same eleven substantive
verdicts (deliberately excluding G11's own verdict, which is False inside the guarded second
invocation by construction); **G12** THE MUTATION EXPERIMENT, run in-process every time:
rebinding `record_from_image` to read the MODEL instead of the image makes G9's record
collapse back onto G3's (the model's own 27,29 fac 1) while the real leg on the SAME
corrupted image carries the bad bytes - so the falsifier is load-bearing, not a tautology;
G3 is DECLARED blind to that mutation because in this fixture the model tuple EQUALS the
container tuple.
DECLARED UNMODELED: WHICH base actually ran the completion (the m289 run tracks only
year/cur/tf/ledger, the recorded B12 build happened in a different save - so the
base is CHOSEN as the last surviving founding and the choice is a fixture, not a
measurement); the created record's unmodeled bytes (zero + the named fields, as
B12); the founding's economy/research/units and the queue's per-turn progress
(the queue law is B11's, exercised in memory, not composed here); no box time, no
/proc, no gdb, no game-binary load.

**B23 - the queue's PER-TURN progress composed through the WRITER (B11's law in
the written container, not in memory; s280 authored this rung from main, as
B14-B22 did).** `sim/composedturn.py`: the game's own 10-boundary Korolev Center
run (`evidence/trace_m56_build_20261026_145157.jsonl`, head 2, price 9) folds
through a .SAV-shaped image: at EVERY boundary the visit's inputs (storage +0x40,
mirror +0x98, pending +0x4c, the ten slot dwords +0x50, tile/owner) are read out
of the RELOADED image by `sim.save.parse`, the B12 visit law runs (ADD gated
`d0>0 && head!=-39 && !(f30&2)`, gate `storage+add >= price`, PAY, CREATE via
B22's image-fed producer, one B11 pop with the stale tail kept), and the result
is written BACK through `sim.savewriter` - the r0 arrival grows the unit array
by the SAME write path (B12's append). `sim/savewriter.build_image` gains three
backward-compatible `bases_override` keys: `identity` (emit the original
verbatim), `raw` (a recorded seed record - Korolev enters as a GROWN 19th base
slot seeded with the trace's r0-before record, a DECLARED fixture), and `queue`
(the modeled span pack: st/pen/slots always, mirror/d0 optional).
`python3 -m sim.selftest --b23 programs/saves/m54b_clean.SAV` must print
PASS B23 12/12 (authored once in `sim/composedturn.py`, `--b23` only relays) with:
**G1** the seed + 18 originals round-trip the writer (spans equal, n_bases 18->19);
**G2** every boundary's CONTAINER read == the recorded round_before st/pen/slots;
**G3** verdicts pay-at-r0-only (p,b,b,b,b,b,b,b,b,b); **G4** storage+mirror parity
vs the recorded round_afters 10/10 each; **G5** slot parity 100/100 dwords (the
stale [2,2,2,2,...] tail survives every boundary, untouched); **G6** the M58 pop
visibility law (9/9 after-parities + the popped pending visible at the NEXT
before-sample); **G7** the arrival is the array's LAST record, byte-equal to
`soprod.create_record` fed tile/owner read from the IMAGE, n_units 67->68;
**G8** the image grew by exactly 304+52 B, unit originals + tail byte-identical, and the writer REFUSES queue slot-lists of length 9 or 11 (an 11th slot would write +0x78, past the queue, clobbering later fields - Greptile P2 on #297);
**G9** five rivals FAIL the same fit (noadd / price10 each lose the recorded r0
arrival; nopop leaves pending 1 against a recorded 0; zerotail drops the stale
ids; nomirror leaves mirror 8 against a recorded 0); **G10** THE FALSIFIER: poison
st:=20 at ONE boundary IN THE IMAGE BYTES ONLY - the container fold re-reads it
and pays twice more (3 arrivals, verdicts p,p,p,...) because the poisoned value
persists in the written image, while the model-fed fold is BLIND to the same
corruption (1 arrival, recorded table) - load-bearing in both directions;
**G11** THE CREATION SOURCE IS THE CONTAINER (Greptile P2 on #297): tile AND owner poisoned in the seed record BYTES at r0 (1447,1448, owner 0x5a) - the created unit CARRIES the corrupted bytes (locate BY POSITION, not coords, so the poisoned tile cannot hide the record), while a frozen-args rival (creation arguments pinned to the seed-open values - indistinguishable on the uncorrupted run, which is exactly the reviewer's point) FAILS the same fit;
**G12** two runs -> identical FULL table - labels, verdicts AND detail strings (a label/verdict-only comparison was itself a Greptile P2: details carry measured values) + written-image sha256 e685d297e3d246eb.
DECLARED UNMODELED: the visit-time d0 (+0xd0, the game's per-visit recompute -
read from the trace's after-samples as recorded data, M57/M58) and the price
(recorded 9, never a recomputed price_of, M72); the recorder's pop-visibility law
(USED as recorded, per M58); f30 (+0x30) bit evolution and +0xd0 in the container
(never gate a verdict in this fixture: f30&2 is never set in any sample); the
founding's economy/research beyond the visited base; which base ran the completion
is REAL here (the traced one). No box time, no /proc, no gdb, no game-binary load.

**B24 - the queue leg visiting a base the FOUNDER LEG wrote into the container
during the run (the B22/B23 interface made executable; s287 authored this rung
from main, as B14-B23 did).** B22 proved the CREATE leg reads a tile that was
ALREADY in the save; B23 folded a queue on a record the model SEEDED (a declared
fixture). Neither folds a queue on a record WRITTEN INTO THE IMAGE by another
composition leg during the same run. `sim/composedlive.py`: B21's log-driven op
stream and turn schedule (evidence/m289_gdb_raw.log: 7 FOUND + 2 DESTROY) applied
to the BASE ARRAY IN THE IMAGE - FOUND appends M282's record bytes through the
writer (B22's grow), DESTROY applies the last-into-freed-slot compaction (M282) -
and at every later boundary the B23 fold engine reads its queue inputs from the
RELOADED image at the visited record's **position by ledger index**, never by
tile: the falsifier corrupts the visited record's tile/owner **in the image only**
and a tile lookup could not find the corrupted record at all. The visited base is
a founded one (fac=1 (27,29), op6 of the log, ordered BEFORE the last DESTROY in
log order), seeded with B23's queue law; its completions arrive as 52-B units
through the same writer. `python3 -u -m sim.selftest --b24` must print
`PASS B24: 9/9 gates` (authored once in `sim/composedlive.py`, `--b24` only
relays, so the two entry points cannot print different text) with:
**G1** B23's own replay stays green in-process (12/12) - the composition reuses
the fold engine, it does not fork it; **G2** op fidelity: the 9 applied ops hit
9/9 recorded (kind,pre-cnt) rows, and at EVERY turn of the run the IMAGE's parsed
`n_bases` equals the ledger count (the array grew/shrank through the writer);
**G3** every grown record in the image == `basefound.record_bytes` verbatim, and
the VISITED record carries the fold's last-written queue span plus (under the
falsifier) the corrupted identity bytes; final `n_bases` == ledger, size delta ==
grew*304 + arrivals*52; **G4** the DESTROY compaction runs IN THE IMAGE: the victim
is always the array's LAST slot (measured slots 20 and 23, never the visited 22),
the image size at each destroy turn equals the applied-ledger size (and the
skipped-destroy ledger would leave 304/608 B more), the visited record's index is
STABLE across both compactions, and its queue span survives the t=29 shrink;
**G5** the queue fold on the founded record's bytes: container == model at every
visit boundary while uncorrupted (verdicts, spans, arrivals); **G6** each arrival
is the units array's LAST 52 B and carries the tile/owner **read FROM THE IMAGE**,
its head slot from the image's own span, `n_units` 67 -> 70; **G7** THE FALSIFIER,
two shapes: (a) poison the founded record's tile/owner IN THE IMAGE ONLY from visit
6 - the fold re-reads through the POSITION and the THIRD arrival CARRIES the
corrupted tile/owner (and the image's own 3rd unit record agrees), the image's
first two unit records stay clean, while the model-fed fold is BLIND to the same
corruption; the queue SPANS and verdicts are DECLARED equal under this shape (the
poison never touches +0x40/+0x4c/+0x50, so claiming divergence there would be
decoration); (b) poison the record's storage in the image at one read - the
VERDICT TABLE moves and a completion shifts turns, while every visit before the
poison is byte-identical: the read-back loop, measured; **G8** five rivals fail the
same fit (price 100; no arrivals appended; head not popped; arrival identity frozen
at the founding turn's constants; no founding at all; tile lookup instead of
position); **G9** determinism: two runs identical FULL tables - labels, verdicts
AND the per-turn/per-visit rows - plus identical final-image sha256.
`scripts/b24_mutate.py` re-creates eight defects by anchor->replacement in a fresh
subprocess and exits non-zero unless each reddens EXACTLY its declared gate set.
DECLARED UNMODELED: the queue content seeded on the founded record (the log
records fac/x/y/cnt only - the seed is a DECLARED fixture, the LAW is B11/B12's,
exactly as B23 declared its Korolev seed); price/income and the visit-time d0 as
in B23 (the recorded laws, not recomputed); the founded base's economy, research
and garrison; WHICH base the game would really found is not claimed - the schedule
is the recorded log's, not a model of the AI. RETRACTED at the first measurement,
before any gate was written: the draft's claim that the turn-29 compaction MOVES
the slot the fold's visits address. It does not - the compaction removes the
array's LAST slot, which sits after the target (index 22), and the last logged
DESTROY lands at t=29, one turn after the last visit; the slot is stable for all 8
visits (G4). What the window does show is two-sided and load-bearing: the
container's queue SPAN is a weak channel (read back every turn it comes out
byte-identical to the model's chain, so a falsifier cannot bite there), while the
record's IDENTITY bytes are the channel that carries - they reach a new unit record
only if the fold reads them from the container. No box time, no /proc, no gdb, no
game-binary load.

**B25 - the MOVE leg made PERSISTENT: a moved unit's tile travels through the WRITER and
comes back out of the CONTAINER, and the container - not the map file - owns the coordinate
space the press law runs in (sim/composedmove.py; s294 authored this rung from main, as
B14-B24 did).** B7 pressed the recorded M27 gesture (dir=1 east, +2 x, 3 MP per tile, 6 MP per
round, third press refused per FUN_005acc00) on model objects and DECLARED the gap this rung
closes: "save-restore of unit positions is NOT simulated (no writer modeled)". B8 modeled
unit x/y inside the record and proved the identity round-trip; B12/B22 proved a created record
lands at the array end and that the CREATE leg reads its arguments out of the reloaded image.
No rung ever made the MOVER read its own next press's start tile out of the container.
`sim/composedmove.py` composes them: parse the save, press the B3 engine and the B7 gesture
every round on the save's OWN unit array, write the image through `savewriter.build_image`
with the moved tiles, and RE-PARSE the written image for the next round's start tiles. The
wrap modulus is read FROM THE CONTAINER (`sv.width`), and the .MP's width is run as a rival,
not assumed. The falsifier rewrites one unit's tile IN THE IMAGE ONLY, between rounds, never
touching model state.
`python3 -u -m sim.selftest --b25` must print `PASS B25: 9/9 gates` (authored once in
`sim/composedmove.py`; `--b25` only relays, so the two entry points cannot print different
text) with: **G1** B7's own slice re-derives green in-process on the same inputs and its
per-unit accept/refuse pattern equals this run's (the composition reuses the gesture law, it
does not fork it); **G2** identity through THIS call path - a zero-move, zero-append build
equals the original file byte-for-byte, and a round's build differs from its predecessor in
exactly the bytes the move law touched (counted, not described); **G3** write-back fidelity:
after every round the re-parsed image's tile for EVERY unit equals the model's tile, and the
only unit-array bytes that ever differ across the whole run are those units' x-lo bytes
(collateral 0, measured); **G4** the reload law, the rung's core: every round's start tile
equals the tile parsed out of the image the PREVIOUS round wrote (pinned count), and from
that reloaded tile the recorded (+2,0) delta and the 2-accept/1-refuse budget still hold;
**G5** the coordinate space, arbitrated BY THE DECODER: under the container's own width every
record stays shape-valid at every round (`found_units == n_units`), while under the rival
width N units land outside the container's grid and the parser's own `found_units` drops to
K - both numbers measured by RUNNING the rival, neither quoted from prose; **G6** THE
FALSIFIER: poisoning one unit's tile in the image only shifts that unit's whole later
trajectory (the shift reaches the final written bytes and its deltas stay (+2,0)), and the
model-fed mover is blind - its final image equals the clean run's byte-for-byte; **G7** every
differing byte between the final image and the original lies inside a MODELED span (the
writer's own accounting, B8's law); **G8** the rivals fail the same fit, measured - never
written, read-after-write ordering, model-fed, UNIT_LEN+4 stride, lift-everything re-emitter,
a 3-MP budget, the .MP modulus - and a rival that passes, or crashes without a matched
message, is retired as decoration (trap 24); **G9** determinism: two runs -> identical printed
tables AND identical final-image sha256, with a measured digest of the result rows printed.
`scripts/b25_mutate.py` re-creates the defects by anchor->replacement in a fresh subprocess
and exits non-zero unless each reddens EXACTLY its declared (MEASURED) gate set.
DECLARED UNMODELED: the MP/spent word is MODEL state - no rung claims the container carries
it (the per-round refresh at 0x51f730 is B7's declared ASSUMED line, unchanged here);
per-terrain cost and the second move's source (sim/units ASSUMED, queued census picks);
blocking, zone of control and every refusal cause other than exhausted MP; the y coordinate
is never moved by this gesture (dir=1 has dy=0) so the y-wrap/bounds law is NOT exercised
here; WHICH unit the game would really move is not claimed - the gesture is applied to every
unit of the save exactly as B7 declared. No box time, no /proc, no gdb, no game-binary load.


**B26 - the composed run crosses a SAVE/LOAD BOUNDARY: the model is REBUILT FROM THE
WRITTEN BYTES and the founder/arrival/move legs keep running on exactly what the container
carries - and what does NOT carry is MEASURED, not waved at (sim/composedsave.py; s299
authored this rung from main cd6f2f5, as B14-B25 did).** B21 wrote the log-driven run and
resumed it; B24 made the founder leg and the queue leg share one container; B25 made the MOVE
leg read its own start tile out of the container. What none of them did is the operation a
game actually depends on: **throw the model away.** Every rung so far keeps its model objects
alive across the whole run and merely *adds* writes; a value that survives only because the
Python object survived is indistinguishable from a value the container carries. `sim/composedsave.py`
runs phase A (founder ops through the writer, the B12 arrival appended at the array end with its
tile READ FROM THE IMAGE, the B7/B25 gesture pressed on every unit present, the B3 engine
pressed per round), then at the round-aligned BOUNDARY writes the image, **discards every model
object** - ledger, unit list, turn engine, arrival list - and rebuilds them from `parse_image`
over the written bytes alone, then runs phase B with the same laws. Three laws are at stake:
(1) **carry** - every field the resumed run uses equals a FRESH DECODE of the boundary bytes,
never a retained variable; (2) **confluence** - when nothing external intervenes, a run that
crosses a boundary is byte-identical to the uninterrupted run (the boundary is invisible to the
legs, so the legs own no state the container does not); (3) **the non-carry is a number** - at a
MID-GESTURE boundary the per-round MP budget (B25's declared model-only field) cannot cross, so
the resumed run MUST diverge, and the divergence is counted per unit and per byte instead of
being declared away. The falsifier poisons IN THE BOUNDARY IMAGE ONLY, between the write and the
rebuild: a unit's tile, and the founded record's tile/owner bytes that phase B's arrival is
composed from.
`python3 -u -m sim.selftest --b26` must print `PASS B26: 10/10 gates` (authored once in
`sim/composedsave.py`; `--b26` only relays, so the two entry points cannot print different text -
and `scripts/b26_mutate.py` now MEASURES that, comparing both stdout streams and proving the
comparison bites on a relay patched in a temp tree)
with: **G1** engine reuse, not forking - B25's own composed-move run is GREEN in-process on the
same save, and this run's per-round SAVE-unit accepted AND refused press counts equal its
per-round numbers for the rounds the two share (the press law is imported, never re-typed).
HALF-WISE BY MEASUREMENT: the run's TOTAL refusals are B25's plus the units it appends -
67/67/67/68/69/72 against B25's 67/67/67/67 - so the gate compares the SAVE-only half
(67/67/67/67, pinned) and prints both lists (PR #328 F3). **G2** identity through
THIS call path - a zero-op, zero-press, zero-append phase-A build equals the original file
byte-for-byte, so every byte the gates attribute to the boundary machinery is attributable;
**G3** CARRY: at the boundary, each of year, cur_player, n_units, n_bases, every unit record's
x/y, every GROWN base record's full 304 B and the arrival's 52 B equals the same value read out
of a SECOND, independent `parse_image` of the same bytes (counted, divergences pinned at 0), and
the rebuilt ledger is constructed by walking the IMAGE's base array, not by re-seeding from the
model's - checked FIELD-FOR-FIELD (own4/fac/x/y) against a THIRD parse, 20 of 20 records, since a
length equality passes on a ledger allocated from the wrong source entirely (PR #328 F6); **G4** CONFLUENCE: the honest boundary run's FINAL container is byte-identical to the
uninterrupted run's (differing bytes pinned, 0), so the legs hold no state the container lacks;
**G5** THE NON-CARRY MEASURED AND LOCALISED: the mid-gesture boundary diverges from the
uninterrupted run in exactly N units and M unit-bytes (both measured), the divergence is entirely
in the tiles the budget re-allows, and no header byte differs - the declared gap becomes a number -
and now WHERE it sits is a number too: the byte histogram by unit-record offset is 69 at +0 (the
LOW byte of x) / 0 at +1 / 0 at +2+3 / 0 elsewhere in the record / 0 header / 0 outside the array,
pinned, so "the x byte" is a counted statement about the record layout and not an adjective
(PR #328 F4). The mid-gesture reload installs the rebuilt ENGINE for every later round as well as
the ledger, model and arrival list; its state and the pre-split one are printed and pinned equal
(3, 0, 2155), which is the measurement of how much magnitude the defect had - none, on this
fixture (PR #328 F5); **G6** THE
FALSIFIER, both channels: (a) a unit's tile poisoned in the boundary image only shifts that
unit's whole phase-B trajectory INTO the final container (0 of the others move), and (b) the
founded record's tile/owner poisoned in the boundary image only makes PHASE B's arrival carry the
corrupted tile - and (b) is now counted in the BYTES THE RUN LEAVES BEHIND, not only in what the
arrival leg read: 2 final unit records carry the poison's own4 at the unit record's OWNER byte
(sim/production.py:54, UNIT_OWNER = +14) against 0 in the clean run, listed as (index, x, y) in
table E (PR #328 F7: the first probe scanned +4, which is UNIT_FLAG, so the claim had been about
an offset nobody had read).
THE SMUGGLER IS NOT BLIND - RETRACTED HERE, NOT IN A FOOTNOTE: the shipped instrument used to
skip the falsifier's hand for the smuggle run, so "its final container equals the clean run's"
measured OBJECT REUSE (keeping its ledger/engine/writer-base reproduces the honest rebuilt run
byte for byte - still true, still gated) and proved nothing about blindness. Handed the poison,
the smuggler diverges from its own unexposed control (final sha 44c3b8319d55eb64 vs
e8cef60dc765c9b2) on 2 units' final tiles and carries the poisoned owner once, not twice - why
once and not twice is DECLARED OPEN (PR #328 F1); **G7**
every differing byte between the final image and the original lies inside a MODELED span (the
writer's own accounting, B8's law extended to the grown base records and the appended unit);
**G8** the rivals fail the same fit, MEASURED - smuggle, model-fed, nowrite, late-read, no-rebuild
(model objects survive), lift-everything, arrival-frozen-at-founding-constants - and a rival that
passes, or crashes without a matched message, is retired as decoration (trap 24). `uninterrupted`
was REMOVED from this set: it is G4's confluence control, and its signature differs from the
container's only because the container is poisoned - counting it as a defect model proved nothing
(PR #328 F10); **G9**
determinism: two runs -> identical printed tables AND identical final-container sha256, with the
ACCEPT anchor pinned to a literal inside G9 (a labels-only edit must redden G9 and nothing else);
**G10** THE SIZE LAW IS GATED, NOT PRINTED: every round of the honest run grows the container by
exactly `BASE_LEN*(n_bases delta) + UNIT_LEN*(n_units delta)` - measured
`[(304,304), (304,304), (356,356), (-252,-252), (356,356), (356,356)]`, 6/6 equal, the round-3
negative being the recorded DESTROY (one unit in, one base out) - and the list is the same object
table A prints (PR #328 F2: G7 checks byte PROVENANCE, never this arithmetic, so the law was
decoration).
`scripts/b26_mutate.py` re-creates the defects by anchor->replacement in a fresh subprocess and
exits non-zero unless each reddens EXACTLY its declared (MEASURED) gate set.
DECLARED UNMODELED: the per-round MP/spent budget and the queue fold's in-widget bookkeeping never
cross the container (B25's line, unchanged - G5 measures its consequence, it does not claim the
game behaves the same); WHICH base the game would really found and WHEN is the recorded log's
schedule plus a declared fixture placement, not a model of the AI; the arrival record's bytes
beyond x/y/type/owner/order are unmodeled (B12's declaration); the queue span itself is NOT
folded in this rung (B23/B24 own that channel and this rung's G1/G3 keep it out of scope rather
than re-proving it); whether the SHIPPED game carries MP in a .SAV is chain 2's open census
(M324) and is NOT claimed here either way. No box time, no /proc, no gdb, no game-binary load.

**B27 - the ENERGY ledger made EXECUTABLE and CARRIED: one round's energy flow (entry-zero →
upkeep feeder → income → debt settle → SNAPSHOT → hurry refund → ledger stores) runs on the
save's OWN eight faction blocks, the block-A fields the round mutates become the writer's first
MODELED spans inside block A, and the recorded ledger arithmetic is verified against the
container's own bytes (`sim/energy.py` = the law, `sim/composedenergy.py` = the run; s309
authored this rung from main 1b9cb38, as B14-B26 did).** B4 made gross/upkeep/net executable and
B21-B26 made the turn, queue, founder, move and save/load legs composed and persistent. None of
them ever moved ENERGY: `savewriter.build_image` LIFTS block A verbatim (its span list is
header + own-player + map dims + unit x/y), so a round that spends energy could not be written,
and the three chain-2 censuses (M325 +220 = ENERGY, M326 +224 = deferred HURRY debt, M330 +300 =
upkeep spend accumulator) had never been composed into ONE round or checked against the bytes the
game writes back. The laws are the recorded ones, pinned by address in the committed censuses:
entry-zero 52056d (+2fc/+300/+308/+3f8); feeder FUN_004f47f0 `ENERGY -= v` 4f4950-52 /
`+300 += v` 4f495e-62, ROUND>1 only; income add 4f5c8c (B4's Σ base+0xfc); debt settle called
520605, body 520b0e-30 `ENERGY -= +224; +224 = 0`, floor 0; SNAPSHOT 52065d `A := ENERGY`, pinned
AFTER the settle and BEFORE the adds (M328 G1/G2); refund 520714-78f (difficulty>3, field!=0,
mask bit — the mask is VACUOUS, cl=8) `r = trunc(k*x/3)`, k=1 at difficulty 4 / k=2 at ≥5,
`ENERGY += r`, `+300 -= r` with the RESIDUE KEPT (unlike +224, which is zeroed); ledger 52081a-841
`+310 = +2fc`, `+30c = +308 - +300 + +2fc`.
`python3 -u -m sim.selftest --b27` must print `PASS B27: 10/10 gates` (authored once in
`sim/composedenergy.py`; `--b27` only relays, so the two entry points cannot print different text)
with: **G1** transcription integrity — every leg pin is a (label, address, FIELD TOKEN, file) triple and
ONE evidence line must carry BOTH the address and the token it is claimed for (an address that
merely occurs somewhere proves nothing; s309 review F3), counted, and the deliberately-bogus control
pin ships INSIDE the same list so it is measured in the same pass and must hit nothing; **G2** octet parity with the decoders — the eight
ENERGY, eight +224 and eight +300 dwords read out of block A, and the two file-offset tables the censuses print (+300 and +224 - M325 prints no offset table for +220, so there is no third table to gate),
equal the lists the M325/M326/M330 censuses PRINT (parsed out of those evidence lines, never
retyped here); **G3** the ledger laws on the save's own bytes: `+310 == +2fc` and
`+30c == +308 - +300 + +2fc` per faction, 8/8 each, with the sign-flipped and term-swapped rivals
failing at counted factions; **G4** reuse, not forking — `sim.economy` runs in-process and B4's OWN replay
gates are re-run here (counted, all green), and the post-found (2,2,0) row of
`evidence/m44d_idle.json` reproduces through THIS pipeline (net 19 at this save's difficulty, while
the k=2 and full-refund readings predict 20 and 21), the recorded numbers parsed from the trace. The
flat 12-round idle sequence is printed as a LEGS-ZERO CONSISTENCY check only: with every input 0 a
round cannot move energy, so it is not a parity and gates nothing (s309 review F6);
**G5** the refund arithmetic against the game's own printed samples — M330 G4's (x, k=1, k=2,
residue) rows are reproduced exactly and the residue identity `r + residue == x` holds over a
swept x-range, counted; **G6** the k-table derived by walking the pinned branch tuples for difficulties 0..9,
printed, with the branch SHAPE gated too (mov of the same difficulty global, cmp 0x3 / jle skip,
cmp 0x4 / jne to a DIFFERENT target — if both jumps went to one address the k=1 fall-through could
not exist), and BOTH rivals measured (no-thresholding, threshold-2) at counted difficulties; **G7** THE ORDERING AS A NUMBER: with a declared debt fixture the SNAPSHOT
holds the post-settle clamped value, and the "snapshot first" rival differs by exactly the clamped
amount — plus the MEASURED inertness of both legs on this save (+224 is 0 for all eight, and the
difficulty dword read out of the container is ≤3, so the refund never fires: printed, not waved).
The inertness is measured on the save's OWN eight blocks AND shown not to be a stub: the same
blocks stay inert at the k=1/k=2 difficulties too (every nonzero +300 is 1, under the k=1 quantum),
while `refund(3, k)` returns 1 at both k — the leg fires, the save is small (s309 review F2);
**G8** THE WRITER: the round's mutated fields are written into block A through `savewriter` and an
unmutated build is still the identity; every round's re-parse equals the model and every differing
byte lies in a MODELED span — measured PER ROUND against each round's written image, the whole list
printed, not only on the final image (s309 review F10), and `sim.savewriter.modeled_spans()` called WITHOUT block overrides
still returns exactly the pre-B27 list (the older rungs' strictness must not be loosened by this
rung); **G9** THE FALSIFIER: poisoning one faction's ENERGY in the written image only shifts that
faction's later leg arithmetic INTO the final container (the other seven untouched, counted), while
the model-fed smuggler that keeps its own ledger stays byte-identical to the clean run; **G10**
the rivals fail the same fit, MEASURED (the smuggler row is two counted numbers — poisoned
factions carried by the honest run minus those carried by the blind smuggler — not a difference of
counts that can cancel; s309 review F7), and determinism: two runs → identical rows digest,
identical PRINTED-TABLE digest and identical final-container sha256, all three pinned to literals
inside G10 (the rows digest alone would let table text drift unnoticed; s309 review F9).
`scripts/b27_mutate.py` re-creates the defects by anchor->replacement in a fresh subprocess and
exits non-zero unless each reddens EXACTLY its declared (MEASURED) gate set.
DECLARED UNMODELED: the feeder's per-slot `v` (the 34-slot item table's runtime row order is only
pinned for 5 facilities — B4's "table-later" OPEN row — so per-faction upkeep on the AI factions is
alpha-table ASSUMED, exactly as B4 declared it); the relative order of the income add and the
upkeep feeder (only settle < snapshot < refund is pinned by address order, and the two adds are
commutative on this fixture); the nouns of +2fc/+308/+310/+3f8 (M330/M331) and of the difficulty dword
(**ANSWERED by M332**: 0x985aec is the runtime mirror of the win-INI pref "Difficulty",
master 0x92bde8; the index->label order stays open); which factions the game would really charge (the eight blocks are run
uniformly, as B25 applies the gesture to every unit); whether the refund leg ever runs in this
save at all (measured inert here). No box time, no /proc, no gdb, no game-binary load.

---

**B28 - the UPKEEP FEEDER made EXECUTABLE: FUN_004f47f0's per-item charge loop runs on the save's
OWN base records, and the CARRIED HALF-UNIT becomes a field the WRITER owns** (`sim/feeder.py` =
the law, `sim/composedfeeder.py` = the run; s316 authored this rung from main 497d766, as B14-B27
did).** B27 made one round's energy flow executable but took the feeder's per-item `v` as an INPUT
(`sim.economy.base_upkeep` sums alpha rows into `feed`); M333 then pinned the loop's LAW statically
— ids 1..38 VISITED / 1..34 CHARGED, a slot charged only when its bit is set in the 304-B base
record at `+0x8c`, the cost read from the stride-48 item table at `row0+0x10`, the halving gated on
`ds:0x985ba0` (sign + owner-byte compare), and bit5 of `block[own]+0` a CARRIED HALF-UNIT exclusive
to this function. None of that was code: the sim still charged the raw alpha sum, so a round whose
costs are odd silently lost the half-unit and the rung could not say which price path a save took.
B28 executes the law, reads the gate out of the CONTAINER, and persists the carry through the
writer.

`python3 -u -m sim.selftest --b28` must print `PASS B28: 8/8 gates` (authored once in
`sim/composedfeeder.py`; `--b28` only relays, so the two entry points cannot print different text)
with: **G1** transcription integrity — every leg pin is a (label, address, FIELD TOKEN, file) triple
and ONE committed evidence line must carry BOTH the address and the token claimed for it (an address
that merely occurs somewhere proves nothing), counted, with the deliberately-bogus control pin inside
the same list so it is measured in the same pass and must hit nothing; **G2** the bounds are READ,
not retyped — the loop's init and BOTH cmp immediates are parsed out of the committed M333 census
lines and the executable loop's own VISITS/CHARGES ranges are derived from the parsed numbers
(rival: 0-based whole table); **G3** the bitmap gate on the save's OWN bytes — per base, the charged
id set equals the decoded `+0x8c` bits ∩ the charged range, and the width gap is MEASURED: the bytes
beyond the pinned dword (`+0x90..+0x93`, the ids 32..63 window — only ids 32..38 are reachable) are
scanned in every base record of the save and printed, and the SAME scan is run as a CONTROL over the
pinned dword's own window (`+0x8c..+0x8f`, nonzero in 14/18 records), so "ids 32..38 are inert here"
is a count taken by an instrument shown to see bytes, not a wave (rival: charge every table row
regardless of the bitmap, at counted bases); **G4** the price-path gate read out of the CONTAINER —
`ds:0x985ba0` is inside the carried state header, its value is read at `mem2file(0x985ba0)` and the
sign skip is applied, so which path THIS save took is measured (and its inertness printed: the
halving runs 0 times when the dword is negative), shown not to be a stub by sweeping the dword over
the save's own base indices and counting how many flip to the halved path per owner byte (rival:
unconditional halving, at counted cells); **G5** the carry law against the instruction semantics —
over a swept (cost, carry_in) grid the charge is `trunc((cost+carry)/2)` with the SUM's parity
written back into the SAME bit (the `cdq/sub/sar` trunc-toward-zero shape, not a shift), and three
rivals are MEASURED at counted cells: floor-halving, zero-the-carry, round-half-up; **G6** the carry
PERSISTED THROUGH THE WRITER, **on synthetic fixtures only** (this save's own run touches no faction:
the honest pass's touch set `[]` and its rewritten bit5 octet, equal to the container's, are measured
and asserted) — `block[own]+0` joins the modeled spans for this call only, the unmutated build is
still the identity, every differing byte lies in a modeled span, a fixture two-round run with an odd
first-round total leaves bit5 SET in the written image and changes round 2's charge by exactly 1
over the differing set (the zero-carry rival differs at counted factions, and the zero-carry baseline
is licensed by an all-ones carry-seed tie on the full-price path), and `savewriter.modeled_spans()`
called WITHOUT overrides still returns exactly the pre-B27 list (the older rungs' strictness is not
loosened); **G7** parity with the game's own recorded rows — the five live-pinned (id, name, cost)
rows, the raw sum, the disabled-list sum and the recorded HUD `0x744f28` are PARSED out of
`evidence/b4_economy.txt:24` (never retyped here) and the executable feeder on the full-price path
reproduces both sums from the live-pinned costs, while the alpha-derived table is checked against
those same five rows and the mismatch count printed (this is the ONLY part of the 39-row item table
any recorded read pins — the rest stays OPEN and is declared); **G8** rivals + determinism — every
rival FAILS on the printed numbers, and two runs give an identical rows digest, an identical
PRINTED-TABLE digest and an identical final-container sha256, all three pinned to literals inside
G8. `scripts/b28_mutate.py` re-creates the defects by anchor->replacement in a fresh subprocess and
exits non-zero unless each reddens EXACTLY its declared (MEASURED) gate set.

DECLARED UNMODELED: the item table's runtime row order beyond the five live-pinned ids (alpha has 71
`#FACILITIES` rows, the runtime table has 39 — the mapping is pinned only where a recorded live read
pins it); the NOUN of `ds:0x985ba0` (M333: no writer in .text, noun INFERRED — B28 reads its VALUE
out of the container and gates the two paths, it does not name it); which faction `ebx`
(`BYTE[[ds:0x8f0d60]+4]`) is for a non-player feeder call (the carry address uses it; the save's own
`own_player` dword is printed as context only, never equated to it); the REMOVAL path the same loop
takes when energy goes negative (M333's OPEN lead, pick (x7) — B28 stops at the `jge`); the
per-faction disabled list for the AI factions (only the player's recorded one is used, at G7).
No box time, no /proc, no gdb, no game-binary load.

---

**B29 - the ITEM TABLE made DERIVED, not assumed: the feeder's per-slot `v` is computed from alpha
`#FACILITIES` through the M337 LOADER LAW (record i = alpha row i-1), so `sim.economy`'s
`ALPHA_SHIFT = 1` stops being an ASSUMPTION and becomes a measured consequence of the loader**
(`sim/itemtable.py` = the law, its gates in the same file; s319 authors this rung from main
f312c8d, as B14-B28 did).** B28 executed the feeder but took its price table from
`sim.economy.upkeep_table`, whose `ALPHA_SHIFT = 1` row (`runtime id = alpha line index + 1`) is a
B4-era ASSUMPTION inherited from `m32-m84e.md:270`; B4 itself printed four `table-later` rows that
DIFFER under it ("Quantum Converter 5 vs M46 live read 6", "Quantum Lab 4 vs 3") and declared the
runtime row order OPEN. M337 then pinned the order statically: the loader at `0x57a7ef..0x57a899`
opens `FACILITIES`, walks `esi = record+0xc` from record 1 by 0x30 to record 72, reads one line per
iteration and switches to the 11-token path exactly at alpha's first 11-token row (index 38 ->
record 39); the consumer bound is 39 (`cmp esi,0x27` @`0x4f4a35`), not the array size. B29 executes
that loader as a builder over `data/alpha.json`, derives the 72-record table (record 0 the
placeholder the loop never writes), reprices the feeder from the DERIVED table, and settles B4's two
DIFFERS rows as a measured id-convention artifact.

`python3 -u -m sim.selftest --b29` must print `PASS B29: 9/9 gates` (authored once in
`sim/itemtable.py`; `--b29` only relays, so the two entry points cannot print different text) with:
**G1** transcription integrity - every leg pin is a (label, address, FIELD TOKEN, file) triple and
ONE committed evidence line must carry BOTH the address and the token claimed for it, counted, with
the deliberately-bogus control pin inside the same list so it is measured in the same pass and must
hit nothing; **G2** the loader window is READ, not retyped - the census's own record numbers
(start/branch/end/iterations, consumer bound) and its token census (`{6,7,11}` counts) are parsed
out of `evidence/m337_item_order.txt` and the executable builder must REPRODUCE them from
`data/alpha.json` (rival: the array is 39 records); **G3** the derived table must equal the sim's
table for every chargeable id - name and upkeep over ids 1..38, plus the shift-1 identity on all 38,
with the shift-0 rival differing at counted ids (this is what turns `ALPHA_SHIFT` from ASSUMED into
VERIFIED); **G4** the five live-pinned (id, name, upkeep) rows (b4 prints the upkeep column
under a `cost` label), parsed out of
`evidence/b4_economy.txt`, are reproduced by the DERIVED table (0 mismatches), and the recorded raw
sum 3 / disabled sum 2 are recomputed from the derived costs over the recorded facility set, with
the at-alpha-index and reversed-order rivals failing at counted ids by NAME, and the parsed
disabled list pinned (`[8]`, the no-list sum differing by exactly 1); **G5** B4's four
`table-later` DIFFERS rows, parsed out of the same evidence, are MEASURED: read at the ALPHA INDEX
the derived table reproduces all FOUR M46 values exactly (at index+1, zero of four), while by NAME
that convention puts the wrong facility at all five ids B4 pinned - so ONE id convention cannot
explain both sets, and the residue is M46's alpha-line numbering, not a different runtime order
(the rival's value-only score 3/5 is printed at G4 because values alone do NOT discriminate); **G6** the boundary is a NUMBER - the derived
records 39..71 (the 11-token/project rows from the branch on) are built, printed and shown
UNREACHABLE by the feeder's charge bound, i.e. the set of records the consumer can charge is
the set before the branch, counted: the parsed charge bound is 1..34, so ids 35..38 are in-branch
but uncharged and nothing past record 38 is reachable; **G7** reuse, not forking - the feeder
re-run on the save's own container with the DERIVED table reproduces B28's pinned anchors (rows
digest `705a4520c08c4062`, print digest `99c52201f073499d`) and the container's own base totals
are unchanged, so nothing in B28 is loosened or re-derived; **G8** rivals + determinism - every
rival FAILS on the printed numbers, and two passes give an identical rows digest, an identical
PRINTED-TABLE digest and an identical derived-table sha256, all three pinned to literals inside G8;
**G9** the alpha file is read, not typed - names/costs/upkeep come from `data/alpha.json`, the
counts printed (71 rows, 42/2/27 field-widths) equal the census's own counts, and a mutated
`alpha.json` WRITTEN TO DISK and RELOADED through `sim.rules.load` (one row's upkeep +1) moves
exactly that one derived cell and reddens G3 at one id (the save argument is the run's container -
G7 replays B28 on it, so a different SAV is measured, not ignored).

DECLARED UNMODELED: records 39..71's trailing columns (the 12-store order beyond `+0x10` is M337's
decoded `+00,+0c,+10,+14,+18,+04,+18,+1c,+2c,+24,+28,+20`, but only `+0x10` is priced here, since
only it is charged); WHY M46 numbered its two rows by alpha line (a source-side convention, not
re-derivable from the committed bytes - the gate measures the consequence, not the cause); the
6 rows whose tails are commented out in this `alpha.txt` (M337's pitfall) are irrelevant to the
price column but the 11-token path's re-sync is INFERRED, as M337 declared; whether the game's
runtime table is patched by any non-loader writer (no such writer is claimed either way here).
No box time, no /proc, no gdb, no game-binary load.
