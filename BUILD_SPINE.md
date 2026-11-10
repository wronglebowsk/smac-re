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
