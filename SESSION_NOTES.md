

Older sessions: `docs/sessions/sessions-193-193.md` (1 sessions). Read it only when a question reaches back before session ## Session 194.

## Session 194 (2026-11-01, M243 — the 7 dead write legs of the save codec and their gates; static, zero box time)

- **Acceptance:** `sudo -n python3 scripts/m243_leg_gates.py` → `PASS M243: 4/4 gates` (one
  invocation) → `evidence/m243_leg_gates.txt`.
- **Instrument:** the codec's CFG from `scratch/m574/text.txt` (1500 insns, 359 blocks),
  forward-interpreted under the LIVE state read from `/proc/<pid>/mem` (`ds:0x926a0c`=1 mode,
  `ds:0x926a14`=0 swap, `ds:0x985dbc`=9, `ds:0x985af0`=72 units, `ds:0x985af4`=18 bases,
  `ds:0x985ae8`=0x2). Guards are evaluated, edges the state falsifies are pruned, and each dead leg
  is attributed the pruned edges that are NECESSARY for it (full-CFG reachability with that one edge
  removed). The dead set comes from two COMMITTED box logs — no new box time:
  `evidence/m242_b.gdblog` (a save: 23 of 30 write sites hit) and `evidence/m109c4.log` (a load: 23
  of 30 read sites hit).
- **G1** the two logs agree on the SAME 7 legs — dead write `596927 596976 5969cb 596af5 597203
  597384 59762f`, dead read `59692e 59697d 5969d2 596afc 59720a 59738b 597636` (twins by index) ⇒
  state gates, not mode gates. **G2** the model marks exactly those 7 unreachable and reaches all 23
  measured-hot legs (37 pruned edges). **G4** `242799-149640 = 242539-149380 = 93159` — the codec
  moves 93,159 B less than the file in BOTH directions, so the dead legs are not hidden bytes; the
  7 dead legs' static sizes total 67,716 B, which is why no save is ever that much bigger.
- **G3, 7/7 named gates, 3 families.** (1) `0x5968b6 je 0x5969f0` on `and eax,0x10000000`
  (ds:0x985ae8=0x2, swap bit CLEAR): region 0x5968bc-0x5969d7 is the swap-only region and the three
  PLAIN legs inside it are unreachable in *both* swap states — 0x596927 (0x91f750, 3296 B), 0x596976
  (0x92046c, 4 B), 0x5969cb (0x92fc50, 192 B) are unreachable code either way. (2) version<3 legacy:
  0x596a4a `cmp ds:0x985dbc,3`, 0x597165 `cmp eax,ebx` (eax=9), 0x5972d1 `cmp ds:0x985dbc,ebx`
  (ebx=3, propagated from `mov ebx,0x3` at 0x59715e) — these legs serialize a scratch buffer
  malloc'd by `call 0x5be090` (0x596ab2 push 0xe5e0 = 58,848; 0x59733c push 48·n): 0x596af5 58,848 B,
  0x597203 1,664 B, 0x597384 48·n = 3,456 at n=72. (3) feature bit: 0x5975ed `test ds:0x985ae8,0x10`
  (live 0x2) → 0x59762f writes the 256 B at 0x991698 only when that bit is set.
- **RETRACTION:** the codec has **30** `call 0x64cc00` read sites, not 28 — M242's armed list missed
  `0x5979f8`/`0x597a19`, which the M109 load DID execute. Symmetry restored: 30 write / 30 read, 23
  hot each way, the same 7 dead each way. NAMED's M242 row corrected.
- **Pitfalls (into the skill's instrument-laws.md):** `test reg,reg` + `je` is TAKEN when the result
  is ZERO — opposite polarity to `cmp`, so a model reading `je` as "nonzero" routes every leg wrong;
  `and`/`or`/`add` are flag-SETTERS, not clobbers (as clobbers they make the swap gate unresolvable);
  a call clobbers only eax/ecx/edx — ebx/esi/edi survive it, which is what makes the handle and the
  loop constants resolvable across legs.
- **OPEN:** who writes the 93,159-B tail outside the codec — the codec's handle-carrying callees are
  the only candidates (0x596fb7 `FUN_005821e0`, 0x596fd0 `FUN_00582260`, 0x5972af `FUN_00571380`,
  0x597970/0x597991 `FUN_00596620` push `esi`=handle), since every codec leg is now accounted;
  roles of `FUN_0059a0c0`/`0x59a2b0`/`0x59bec0`. #180 (M241) still open. Box untouched (no gdb, no
  ptrace; `/proc/mem` reads only).

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

## Session 197 (2026-11-01, M245/M246/M247 ANALYSE — the tail's last three legs)

`sudo -n python3 scripts/m245_tail_legs_census.py` -> `PASS M245: 5/5 gates` (rc=0; 3rd invocation:
the 1st was 4/5 because G2 demanded that EXACTLY ONE save match the live 216 B — the box refuted the
premise, 7/17 match because those saves come from one session without scrolling; the byte-for-byte
equality is unchanged, the gate now asks for >=1 match and NOT all 17) -> evidence/m245_tail_legs.txt.
`sudo -n python3 scripts/smac_preflight.py` -> PASS 14 invariants. Box: /proc reads only, terran.exe
319926 TracerPid 0, no gdb.

- M245 the 216-B leg (EOF-228..EOF-12) = 9 map-view objects x 6 fields. Codec loop
  (shard_015.c:10807-10822): `puVar18 = &DAT_007cdecc; do FUN_00596620(*puVar18,..) while ((int)
  puVar18 < 0x7cdeec); FUN_00596620(&DAT_008cda4c,..)` = 8 heap pointers (live 0x8f79e0, then
  0x3b5f4e8… spaced 0x224b8) + 1 inline object. Fields (FUN_00596620's order): +0x1dd78 view id
  (rows 0..7 = 0..7 on 17/17 saves, inline row = 1), +0x1dd74 active flag (set FUN_00469860
  shard_008.c:5894; cleared by the codec's load leg shard_015.c:10845 when the [800,387] pair changes
  and by 4 invalidators), +0x1dd70 bit flags (tested shard_008.c:8983/9033/9076/9318), +0x1dd98 = -6
  while DAT_0091c18c < 1000 (5892), +0x1dd9c/+0x1dda0 centre tile (init W/2,H/2 5895-5898; set by
  FUN_004739a0 :10117-10124). The window bounds +0x1ddcc..0x1ddc8 and origins +0x1dda4/+0x1dda8 are
  DERIVED from the centre by FUN_00469860:5949-6017 and read by the click hit test FUN_00422060
  (shard_001.c:14164-14183). Live read-back == 7/17 saves' 216 B byte for byte (10 differ); live
  DAT_0091c188/c18c = 387/800 = the 8-B leg; Autosave 1 rows 0-1 centre (28,42) = University Base.
- M246 the final 4 B = `local_8 = timeGetTime()` (FUN_00597ce0 body line 15) written by
  `FUN_0064c9a0(&local_8,4,1,iVar2)` (line 44) AFTER `FUN_00596850(iVar2,1)` (line 42); the codec
  never reads it. Δ(dword) vs Δ(mtime) ≤ 2.5 s on 5/5 same-session pairs (Autosave 2→1 31 s /
  30,989 ms; m241_probe_A→B 16 s / 16,785 ms); 0x15c79939 sits on 3 files 486,979 s apart and
  0x2db1b939 on 2 files 71,224 s apart -> stamped at save CREATION, not at file write.
- M247 DAT_0092ae18 has 6 referencing functions; the only element accessors FUN_00582340/2360 index
  `(param_1>>1) + DAT_0092ae18 + (DAT_0092ad9c>>1)*param_2` (shard_014.c:27392/27401) and `(Rw+1)/2`
  appears once image-wide (the length, 27266). The builder FUN_0058ce00 (shard_015.c:4707-4747) walks
  y < Rh, x = (y&1) step 2 < Rw, so its write set is exactly bytes 0..78 at 64x64 (Rw=Rh=13): slack =
  Rh-1 when Rw is odd, else 0. The 12 slack bytes are `0xcd` in 17/17 saves (none in 0..78); both .MP
  files have even Rw -> slack 0, no 0xcd.
- OPEN: what the region byte VALUES mean (the builder takes terrain record +3 of the first of 9
  sampled tiles whose +1 & 0xe0 > 0x5f, else 0 — shard_015.c:4716-4741; 0x3f/0x01/0x00/0x10 seen);
  who allocates the ~140 KB view objects; the 7 mask copies at record +16..+43 still stand.
- PITFALL: a byte-for-byte live-vs-file match gate must state what it discriminates. "Exactly one
  file matches" is a premise about the STATE, not about the claim; unchanged state across saves
  breaks it. Require >=1 match AND some files differ.

## Session 198 (2026-11-01, M248/M249 ANALYSE — the region map's byte VALUES, and terrain record +3)

`python3 scripts/m248_region_values_census.py` -> `PASS M248: 5/5 gates` (2nd invocation, rc=0;
1st 3/5 on TWO instrument bugs, both fixed, no threshold moved) -> `evidence/m248_region_values.txt`.
Corpus = 17 saves + planet.MP + planetx.MP (19 files); zero box time, programs/terran.exe read for
rodata (file offset = VA - 0x400000).

**M248 — what the coarse region-map bytes mean.** `FUN_0058ce00` (shard_015.c:4690-4752) BUILDS the
map: for each region (x = row&1 step 2 < Rw, y < Rh) it samples 9 tiles at (x*5+dx, y*5+dy) with the
(dx,dy) pairs read from the image at 0x67850c/0x678990 = centre (0,0) then the 8 ring neighbours
(1,-1)(2,0)(1,1)(0,2)(-1,1)(-2,0)(-1,-1)(0,-2), x wrapped mod DAT_0092a378, y only bounds-checked
vs DAT_0092a37c, and stores **terrain record +3 of the first sample whose +0 & 0xe0 > 0x5f (land)**,
0 when no sample is land (G1 9/9 checks). The stored bytes are reproducible from the grid by that
rule **byte for byte: 19/19 files, 1809 written cells, 0 mismatches, 38 samples needed the x-wrap**
(G2). The array has exactly ONE reader function and ONE writer function: readers of FUN_00582340 =
`FUN_00556690` (shard_014.c:3450, 3469 — it uses the byte as a coarse label filter, then expands to
the fine grid with the same 9 offsets from 0x6784a0/0x6784c4, ring-first); writer of FUN_00582360 =
`FUN_0058ce00` (shard_015.c:4739); its other 17 direct refs are alloc/free/file-I/O/null-guards/
clears, all in shard_014.c (G3).

**M249 — what terrain record +3 is: the map's REGION LABEL, assigned at generation.** Its only
writer in the image is the byte setter `FUN_00582d00` (shard_014.c:27745,
`*(undefined1 *)(DAT_0092ae14 + 3 + (DAT_00692184*param_2 + (param_1>>1))*0x2c) = param_3`): of the
18 stores into the record array, exactly 1 covers byte 3 and it is that setter; the setter has 4
call sites, all in shard_015.c's map-generation code — :4862/:4892 in `FUN_0058d120`, :5086/:5097 in
`FUN_0058d390` (G4). The +3 plane is IDENTICAL across all 17 saves (1 distinct plane) which span 5
distinct turn values (file 80: 50,51,52,53,60) -> gameplay never rewrites it. Value semantics
(G5, 0 exceptions on 19/19 files): **+3 < 0x40 on every land tile, +3 >= 0x41 on every water tile,
0x40 never appears**; distinct land ids scale with map area — 18 at 64x64, 25 at 80x80 (planet.MP),
62 at 128x128 (planetx.MP); water ids are 6-8 values (41-48, 7f). Readers use it as an INDEX into a
per-faction byte array (`[param_2 * 0x20bc + (uint)*(byte *)(DAT_0092ae14 + 3 + ...)]`,
shard_012.c:2681-2683) and test `a < 0x40 == b < 0x40` (shard_012.c:7336). Ids are reused across
disconnected groups (planet.MP: 25 ids over 47 land components) and 130/16626 land adjacencies
differ, so it is a labelled partition, not a component id.

**RETRACTION:** my own first reading of G4 ("no store lands on +3") was wrong — the width parse
dropped the `*(type *)` cast (leading spaces), so every store got w=0 and `off<=3<off+0` is never
true; the byte setter at +3 was in the output all along. The 1st invocation also failed G1 (my
consumer-table comparison dropped the wrong centre) and G3 (4 `if (DAT_0092ae18 != 0)` null-guards
unclassified). Instrument bugs, not findings; gates re-ran whole.

**OPEN:** who calls the region builder / the two generators (FUN_0058d120, FUN_0058d390) and in what
order at NEW GAME; what the 0x20bc per-faction block at DAT_0094eda8 is (faction-known regions?);
what FUN_00556690's search is FOR (its callers: FUN_005208f0 shard_013.c:11666, FUN_0059ce10
shard_015.c:14862); whether +3 is ever re-assigned by terraforming (no store found outside the
generators, so no); the 7 mask copies at record +16..+43 still unnamed.

## Session 199 (2026-11-01, BUILD fire) — **B3: the C1 turn engine is executable and replays M30's trace 67/67**

**Acceptance.** `python3 -m sim.selftest --replay evidence/m30_turn_trace.jsonl` → `PASS B3:
6/6 gates on m30_turn_trace.jsonl`, rc=0, real 22.3 s, **ONE invocation** (no threshold set or
moved after the run) → `evidence/b3_turn_replay.txt`. New model file `sim/turn.py`, gates in
`sim/selftest.py::run_replay`.

**Why parity is an ORDERED SUBSEQUENCE, not an equality.** The trace is a 0.2 s SAMPLE:
`scripts/turn_trace.py:59` logs a row only when one of (year, cur, tf) differs from the previous
sample, so a run of short AI phases appears as its LAST value only (turn_driver.md §M30 says the
same: 1–5 of the 8 phases are visible per cycle). The engine must reach every recorded row in
order — 67/67, zero tolerance — and the 154 emissions the matcher consumed as "extra" are exactly
the phases the sampler collapsed (220 emissions, 11 per cycle).

**What the trace pins down (G1-G6).**
- The walk is ASCENDING over the 8 faction slots and our slot is 3: `tf == 0` appears in 21/67
  rows and every one of them has `cur == 3`; `own == 3` in all 67.
- **The year counter fires on the 7→0 edge, while `cur` is still 7** — not at the press, not at
  the human landing. Witness row 22 `t=88.631 (cur 7, tf 2, year 2221)` is the only row where a
  new year is visible behind an AI slot. All 8 candidate edges: cur==7 → 66/66, cur 0/1 → 22/66,
  cur 2 → 10/66, cur 6 → 6/66, cur 3/4/5 → 0/66.
- **`tf` is cleared ONE STEP AFTER `cur_player` is written to 3**: deleting the (3, tf=2) landing
  state from the model drops parity to 5/66. Four rows are (3,2) — 5, 14, 23, 40 — each following
  an AI slot, never a (3,0) row. **RETRACTION (M30 claim 3):** "cur_player is **never 3** while
  `turn_flags & 2`" is false in its own data — those four rows ARE that state. The correct rule is
  that the walk ENDS on slot 3 with tf still set, and tf is cleared one step later.
- Model space = cyclic walk order (7! orders × 8 positions for the human) × 8 year edges =
  **322,560 candidates, 48 (0.0149 %) reproduce the trace**, forming 6 distinct cyclic orders × 8
  rotations. All 48 share the edges 0→1, 1→2, 2→3, 7→0 and the year edge 7; the ONLY freedom is
  the relative order of slots {4,5,6} — no cycle ever shows two of them in the same leg.
- 20 presses → 20 year bumps → 20 tf clears; year 2213→2233; final state (3, 0, 2233) = last row.

**OPEN.** The press transition (3,0)→(3,2) is never separately sampled — dropping it keeps 66/66
— so whether the engine writes `turn_flags` before `cur_player` at TURN COMPLETE is unsettled;
the internal order of {4,5,6} needs a denser or longer trace. `nb` (base count @0x985AF4) moves
51→58 with one decrease (row 28, 57→56) and is not modelled by B3. No box time: no /proc, no gdb.

## Session 200 (2026-11-01, M250/M251/M252 ANALYSE — who assigns the region labels, in what order, and who reads them)

`python3 scripts/m250_region_generation.py` → `SUMMARY PASS: 7/7 gates on terran.exe (static image,
no box)`, rc=0, 2.7 s, ONE invocation → `evidence/m250_region_generation.txt`. Static only: objdump
of `programs/terran.exe` (regenerated, 40 MB, kept in `scratch/`, not tracked) + `ghidra_out`. No
preflight, no `/proc`, no gdb; terran.exe untouched.

**M250 — the region generator and its ORDER.** `FUN_0058d390` (0x58d390, 1293 B) has exactly 3 call
sites, image-wide (G1): `0x5add8f` in `FUN_005add30`, `0x5af0c7` in `FUN_005af0c0`, `0x5b09e3` in
`FUN_005b09b0`; the generator driver `FUN_005b2970` (shard_015.c:28040-28115) calls the first two
and has 4 call sites (`FUN_004e10c0`, `FUN_004e11b0`, `FUN_0057c550`, `FUN_0057ecf0`). In the driver
the order is `FUN_00582170` (default records) → placement loop (`FUN_005ad970` ×, `FUN_005adbc0(4)`)
→ `FUN_005add30` → **`FUN_0058d390`** → `FUN_005aef40` → the while-condition `FUN_005af0c0()` which
re-runs `FUN_0058d390` and returns "retry" (up to 4 attempts while `DAT_00985ae8 & 0x80 == 0`); the
third caller `FUN_005b09b0` is the "ADJUSTING WORLD CLIMATE" stage (22 call sites) that re-runs the
generator after the climate pass. Inside `FUN_0058d390` (G2/G3/G4): clear `+3` over every record
(store `0x58d3b8`, step `add ecx,0x2c`, back edge `0x58d3c7→0x58d3b8`) → parity-2 tile scan whose
back edges `0x58d5fa→0x58d3f9` and `0x58d60c→0x58d3e2` both enclose the flood-fill call
`0x58d47e` → the two border-ring calls `0x58d649`/`0x58d6c3` → stats + adjacency → and
**`FUN_0058ce00` (the coarse label map) is the LAST call before the free `FUN_005e9e0d`
(`0x58d88c`, `0x58d891`): no back edge encloses it**, so the coarse map is built after every id is
assigned. Id bands from the body's immediates (G4): land `1..0x3e`, water `0x41..0x7e`
(`0x40` never assigned — the counter is pre-incremented), and when a band is exhausted the smallest
region in it is relocated to the overflow slot `0x3f`/`0x7f` (shard_015.c:5007-5073), which is why
M249 saw "25 ids / 47 components". Region table `DAT_00989ce0`, stride `0x1c` = 7 dwords reached
through the `lea [r*8+0]` + `sub r` fold (8 sites), dword 0 = tile count, `+0x14` = an 8-byte bitmap
of adjacent opposite-class regions written by the land/water border pass (`FUN_00507410` bit index).

**M251 — `DAT_0094eda8` is the per-faction, per-REGION category byte** (G5): 79 refs in 18
functions, **6 store sites in 2 writers** (`FUN_00556690` ×5 at 0x557fdf/0x558516/0x558549/0x55855e/
0x55856b, `FUN_0055f650` ×1 at 0x564ad7), values written exactly `{0, 2, 7, 8}`; addressed
`[region + faction*0x20bc]` (shard_014.c:2159/2217/2220 spell it out) and the stage's region loop is
`cmp reg,0x80` at 0x556737/0x558b1c → **128 entries = the whole id space**. Sibling arrays in the
same block, same index: `0x94e4a8` (short ×128, ends exactly at `0x94e5a8`), `0x94e5a8` (the byte
SCORE the pick loop compares), `0x94e628` (cleared per region each pass), `0x94e7a8` (flag bytes).
Effects pinned, NAMES OPEN: `< 2` is a preferred expansion candidate (+1000 bonus,
shard_014.c:3409-3411), `== 7` is accepted at its face score (:3429), `== 8` only when the region is
small (`DAT_00989ce0[region] < 0x96` = 150 tiles, :3439) and it also raises `FUN_00556370`'s divisor
2→4 and decrements `FUN_00556150`'s 1..10 score; `== 2` blocks the pick and forces `FUN_00556370` to
1. At the top of each pass the four reserved ids (`id & 0x3f` ∈ {0, 0x3f} → 0, 0x3f, 0x40, 0x7f) with
score 0 are stamped 8 (:3188-3191) and every water id ends the pass at 7 (:3583).

**M252 — what the coarse label search is FOR** (G6/G7): the coarse accessor `FUN_00582340` is
called at exactly 2 sites in the whole image, both inside `FUN_00556690` (`0x55878a`, `0x558812`) —
the coarse region map has ONE consumer. `FUN_00556690` (14 349 B, called only from `FUN_005208f0`
`0x52094f` and `FUN_0059ce10` `0x59dd43`, G7) walks the coarse grid by its own dimensions
(`DAT_0092ad9c` × `DAT_0092ada0`, 7 refs), keeps the cells whose label equals the candidate region,
turns a coarse cell into terrain coordinates (`x = cell*5`, `local_68 = local_44*5`), scans the
neighbour footprints for land tiles and scores them, then gates the best site by the terraform cost
`FUN_004cc7b0` (2 calls) against the faction's budget and issues
`FUN_0056d350(faction, 0x29, 2, x, y, -1)` — the 2 `push 0x29` sites (`0x556a47`, `0x558ad9`) each
reach a `call 0x56d350` 3 instructions later. So the coarse map is the spatial index by which the AI
finds where a region IS; the per-faction category/score arrays say whether it wants it.

**OPEN.** The names of categories 0/2/7/8 (only their effects are pinned); the internal order of the
M249 {4,5,6} question and every earlier pick's OPEN item stand. `FUN_005b2970`'s 4 call sites are
counted but not attributed to modes. No retraction.

## Session 201 (2026-11-01, M253/M254/M255 ANALYSE — what the region verdict codes MEAN, and who calls the generator for a NEW GAME)

Acceptance: `python3 scripts/m253_region_categories.py` -> `SUMMARY PASS: 8/8 gates on terran.exe (static image, no box)`, rc=0, 4.6 s, ONE invocation -> `evidence/m253_region_categories.txt` (2,249 B). Static only (objdump of the image + `ghidra_out`): no box, no `/proc`, no gdb. New instrument `scripts/m253_region_categories.py`, 8 gates.

**M253 — the four values are verdict codes named by the guard that writes each.** G4 reads the guards from machine code: `0x557fdf` stores 8 only after `and eax,0x3f` + (`cmp eax,0x3f` or `test eax,eax` zero) + `test al,[..0x94e5a8]` zero, then `jmp 0x558b18` — the reserved-id/zero-score region is SKIPPED. `0x558516` stores `dl` produced by `sete dl; add dl,0x7` — 7 or 8 is the worth-test boolean + 7. `0x558549` stores 0 under `test BYTE PTR [ebp-0x40],0x2`; `0x55855e` stores 2 under `test [ebp-0x40],0x1` — the 2-store comes AFTER the 0-store, so contested beats open. `0x55856b` sits between `cmp edi,0x40`/`jl 0x558578` and `jmp 0x558b18`: the WATER band always ends at 7 and the region is done. G3 re-pins the effects to pcs: `+1000` at `0x55863d`, `cmp al,0x7` at `0x5586f9`, and the 8-arm size gate `cmp DWORD PTR [edx*4+0x989ce0],0x96` with `edx = region*7` (the M250 stride-0x1c table, dword 0 = tile count) at `0x55870e`. G2: 33 `cmp BYTE PTR [..],imm` and 21 `cmp <reg>,imm` right after a load test exactly {2,7,8}; 39 plain loads; nothing tests 0/1/3/4/5/6 directly — and 1 is never written by either writer.

**M254 — what sets the two bits.** The accumulator `[ebp-0x40]` has exactly one computed write: `test ecx,ecx; mov eax,0x1; jne 0x558349; mov eax,0x2; or DWORD PTR [ebp-0x40],eax` — only {1,2} are ever OR'd in and only masks {1,2} are ever tested. `ecx` is the result of `FUN_00531bf0(facA, facB, region, mode)` (505 B, 10 call sites, 2 inside the stage): it walks the unit array over terrain records at `DAT_0092ae14`, keeps a facA unit whose record byte +3 (the region label, M249) equals the region, then looks for a facB unit in the same region and calls `FUN_0058b1b0` (route) / `FUN_0058cfc0`, returning 1 iff a route is found. So bit 1 = contact -> **2 = CONTESTED**; bit 2 = no contact -> **0 = OPEN** (the +1000 candidate). `FUN_0055f650`'s only store promotes 8 -> 7 (`0x564ad7`, guarded by `cmp DWORD PTR [ebp-0x8c],0x8`) in the same window as `add WORD PTR [eax+0x94eaa8],0xfff6` (-10) and `or BYTE PTR [eax+0x94e7a8],0x9`.

**M255 — the NEW GAME caller.** `FUN_005b2970`'s four sites are `0x4e1151`, `0x4e122b`, `0x57d2a0`, `0x57f1ec`. Only `FUN_0057ecf0` is ungated AND writes 6 world-dimension globals (`ds:0x92ad??`) before the call AND reads alpha sections through `FUN_005ea431` (FACTIONS, WORLDSIZE) AND carries the {SCENARIO, INTRO} literals. `FUN_0057c550`'s call is skipped by 2 branches targeting the return point on `ds:0x9264d8` (written only at `0x57e495`=1 / `0x57e900`=0) and its literals are {RULES, USERULES, RELOADFAC, DIFFICULTY, CUSTOMNAMES} with 0 alpha-section calls; its other caller is `FUN_0057e890` = MAPMENU + maps\planet.mp. The set/clear-`0x80` pair `FUN_004e10c0`/`FUN_004e11b0` has NO literals and is called only by `FUN_00512b40` (CHECKSUMS/EDITINTERLUDE) and `FUN_00516b80` (MENUDETAIL/REALLYQUIT/TECHRANDOM).

**No retraction.** OPEN: the four NAMES are INFERRED from guard + effect, not from a literal; the worth test's operands (`[0x94d810]-[0x94d818]` vs `[0x94eaa8][region]+…`) are unnamed; whether `FUN_0057ecf0` also runs on loading a saved game is untested (box falsifier: bp the driver entry, then load a save). M249's {4,5,6} item and every M248-and-earlier OPEN item stand. M181 stays a LEAD; nothing was owed and nothing was measured on the box this fire.

## Session 202 (2026-11-02, M256/M257/M258 ANALYSE — the worth test's operands, and the per-region array family)

Static fire: `ps` showed no terran.exe, so M255's box falsifier (does `FUN_0057ecf0` run on a LOAD) was
not taken. Acceptance: `python3 scripts/m256_worth_operands.py` -> `SUMMARY PASS: 8/8 gates on terran.exe
(static image, no box)`, rc=0, 8.2 s, ONE invocation -> evidence/m256_worth_operands.txt (8,441 B, 144
lines). Two earlier invocations failed on the INSTRUMENT, not the claim: objdump pads the opcode column
to 21 chars and prints at most SEVEN bytes, so a `{1,6}` byte-field quantifier eats the padding, the
optional mnemonic group matches empty and 7 of 13 pinned pcs read as "missing" (the skill's "six opcode
bytes" is a print cap, not a constant — live skill fixed); and 0x950564 is past the file image
(terran.exe = 3,067,904 B, so the image ends at VA 0x6ed000) — a .bss table's row count is not statically
readable.

**M256 — the worth test behind the 7/8 verdict byte.** `cmp edx,ecx` at 0x5584b4, `jle 0x5584e3` ->
boolean 0; the fall-through leg2 is `cmp eax,ecx` at 0x5584d8 (`jge` -> 0, else `mov ecx,0x1`); the legs
are ANDed and OR'd at 0x5584eb with the 4-bit reason word [ebp-0x54], and `test eax,eax` at
0x5584fe/0x558509 is the ZF that `sete dl` (0x55850e) consumes -> `add edx,0x7` -> the M253 store
0x558516. LHS = 2 * ((DWORD[block+0x94d810] - DWORD[block+0x94d818] + [ebp-0x60]) * [ebp-0x3c])
(0x55848f/0x558495/0x55849b/0x55849e/0x5584a2/0x5584a8); [ebp-0x3c] = BYTE[block+region+0x94e5a8], the
M94 multiplier (0x558053 -> 0x55805d); [ebp-0x60] has 4 stores in FUN_00556690 (0x558010 reset,
0x5580b9 fold accumulate, 0x558424, 0x558905) and the live one is 0x558424 = 3 + (ds:0x985afc > 75) +
FUN_00531090(ds:0x985b30, 0), adjusted by ([block+0x94e488] > 4 ? -((ds:0x985ae8>>7)&2) : 0) and by
(BYTE[block+region+0x94eca8] < 4), plus the fold's nonzero count [ebp-0x68]. Reason-word bits: bit3 =
bit3 of WORD[0x94e7a8+row], bit2 = multiplier >= 0x14, bit1 = WORD[0x94eaa8+row] - WORD[0x94eba8+row]
< 4, bit0 = multiplier nonzero with the 0x94eca8 byte < 2 (assembled 0x55842d-0x55848c).

**M257 — the RHS operand.** WORD[0x94eaa8 + 2*region] (0x5584aa, region = [ebp-0x10]) plus
WORD[0x94eaa8 + esi] (0x558452), summed at 0x5584b2; esi = [ebp-0x18] = 2*region + 188*arg1 (fold
0x558002-0x558026, published 0x558038; arg1 = the pushed faction, callers 0x52094f and 0x59dd43). Region
loop: [ebp-0x10] init 1 (0x557f9e), `inc ecx; cmp ecx,0x80; jl 0x557fb8` (0x558b1b-0x558b25) = 128
regions. 0x94eaa8 refs image-wide = 4 (inc 0x51df61 FUN_0051dcb0; -10 0x564ab1 FUN_0055f650; the two
reads here). OPEN: 188-byte rows vs 2 bytes/region — regions 94..127 pass the next row (max offset
188*7 + 254 = 1570); one live read of both indexings settles it.

**M258 — the family.** 0x94e4a8, 0x94e5a8, 0x94e628, 0x94e6a8, 0x94e7a8, 0x94e8a8, 0x94e9a8, 0x94eaa8,
0x94eba8, 0x94eca8, 0x94ed28, 0x94eda8 (end 0x94ee28): 12 per-region arrays, every gap 0x80 (byte per
region — B=97, 10, 6, 2, 79) or 0x100 (word per region — W=23, 22, 13 with 28 refs to the +1 high byte,
2, 2, 4, 5), ZERO DWORD accesses anywhere, 128 entries each. RETRACTS the s201 NAMED row calling
0x94e7a8 "flag bytes": it is a per-region WORD array. The 8-slot fold (0x558075-0x5583ac) walks
WORD[0x950764+2*region] and BYTE[0x950664+region] stepped by 0x20bc, doubling per set bit of
BYTE[block+0x94d44c]; its second row is 0x200 below (0x950564, itself a table base at 0x4f7a0a); both
are .bss, so their extents are OPEN.

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

## Session 204 (2026-11-02, M259-M261 ANALYSE, static) — the terrain record's +16..+43 band is the per-FACTION copy of its +8 mask; the ~140 KB map views are static .bss, not malloc'd; the 0x679f98 class's 15 unique slots and its two ctor screens are named

`python3 scripts/m259_m261_census.py` -> `SUMMARY M259/M260/M261: 14/14 gates PASS` (rc=0, 3.3 s, ONE
invocation, static image only -> `evidence/m259_m261_census.txt`, 30 lines). Invocation 1 was 12/14 and the
two failures were CENSUS SCOPE, not the claims: the discriminator accepted any function that merely named
`ds:0x92ae14`, so unrelated `[reg+idx*4+0xc]` hits were counted; it now requires the access's BASE register
to be loaded from `ds:0x92ae14` or lea'd from such a register. No threshold or floor was moved.

- **M259 the band**: record dwords 4..10 = `[terrain_base + 0xc + (row*0xb + fac)*4]` = dword 3+fac for
  fac 1..7; faction 0 uses the +8 master mask (both refreshes guard `test ebx,ebx / je`). Writer set CLOSED
  at 10 indexed stores — 0x4e153b, 0x4f0def, 0x53a8d9, 0x53a90c, 0x582fec, 0x583e1d, 0x5a3b95, 0x5a3d3f,
  0x5a7afd, 0x5a86aa — plus FUN_0051c750's pointer-walk store 0x51ca52 (G5). Two whole-array refreshes copy
  `[rec+8]` into slot fac over `ds:0x92a38c` records with `add eax,0x2c` (G1); the index register folds to
  the 0x20bc per-faction stride (2095*4 = 8380) (G2); FUN_0051c750 (kelp/forest/mindworm growth) pairs a
  record+0x10 cursor with the faction-block cursor [0x94f4ec,0x95da10) = 7*0x20bc and stores
  `slot & ~0x20 | mask` (G3); slot-to-slot merges through the master mask appear once in FUN_005a7970 and in
  BOTH directions in FUN_0053a820 (G4); FUN_004e14d0 takes its slot index from `[view+0x23bd4]`, inside the
  field block the view ctor FUN_00518820 initialises — the VIEWED faction selects which slot is refreshed
  (G6). Readers: 44 indexed sites in 25 functions incl. FUN_004e15c0 (NATPLACE) and FUN_00519b00 (display)
  (G7). **RETRACTION**: M240's "a record is two 22-byte map columns" reading does not hold for bytes
  16..43 — that half is this band, which is why the `.MP` census found 7 dwords equal in 8192/8192 planetx
  records and equal to `+8` (`evidence/m240_terrain_repack.txt:17`).
- **M260 the views**: `0x224b8` occurs ZERO times in the 3,067,904-B image — no immediate, no 4-byte LE
  constant (G8). FUN_00580260 (1 caller FUN_00522850) zeroes entries 1..7 (`esi` 0x7cded0..0x7cdeec), stores
  the STATIC address 0x8f79e0 into entry 0 at 0x5803e1 and runs the ctor FUN_00518820 once on it (its only
  call site, 0x580406, `ecx = 0x8f79e0`) (G9). The ctor's own stores reach `this+0x23bec` = 146,412 B >
  140,472 = the live stride, so the stride is not an object size (G10); no store in the image names
  0x7cdec8..0x7cdee8 except 0x5803e1. The codec walks the 8 entries as POINTERS and clears `*(p+0x1dd74)`
  for entries 1..7 on a resolution change (`shard_015.c:10822`, `:10842-10845`) (G11). OPEN: who writes
  entries 1..7.
- **M261 the class**: 88 slots / 2 installs, 15 slots differ from all three dialog-family siblings
  0x6717cc/0x671d94/0x67164c (G12): +0x0 46-B dtor (calls FUN_0062d764), +0x8 52-B, +0x30 5143-B /
  1139-insn / 27-callee / 0-direct-caller, +0x40..+0x54 six `ret 0x8` control methods (+0x40 dispatches
  +0x4c), +0x60/+0x64/+0x68 three 15-B zero-callee stubs, +0xa8 21-B, +0xc4 27-B, +0x15c 283-B installer
  (G13). Ctors: FUN_0062d630 <- FUN_0045a8b0(1)/FUN_005b3000(2)/FUN_00641f3c(3); FUN_0062d764 <-
  FUN_00636b1e(15)/FUN_0063a770(3)/FUN_00456670(2)/FUN_00493a10(2)/FUN_0045a840(1)/FUN_0062ecc0(1);
  FUN_00636b1e carries "Start a new session or..." (the session-chooser dialog), FUN_00493a10 "Gamma
  Correction" (graphics options) (G14). No box time; terran.exe stayed down.

## Session 205 (2026-11-02, M262-M264 ANALYSE, static) — the view-table entries 1..7 ARE allocated (7 × 0x22480 at startup, through a cursor store); the LOAD path never re-derives the per-faction band; FUN_005be090 is operator-new and ds:0x9965b8 is a linear record cursor

`python3 scripts/m262_m264_census.py` -> `SUMMARY M262/M263/M264: 11/11 gates PASS`, rc=0, 3.66 s, one green invocation -> `evidence/m262_m264_census.txt` (24 lines). Same instrument as M259-M261 (whole-image corpus 790,695 insns / 10,268 indexed functions + image-derived vtable map + index.csv containment, from `scripts/m235_m237_records.py`). Invocation 1 = 10/11: M262 G1 asserted 38 indexed mentions / 11 functions, copied from a TRUNCATED probe print; the census measured 39/12, so I regenerated `objdump -d -M intel --section=.text programs/terran.exe` (40.9 MB, scratch, deleted) and grepped it: 39 `*4+0x7cdecc` mentions, 0 indexed stores, exactly one `mov DWORD PTR ds:0x7cdeXX` store inside the band (0x5803e1) — only then moved the expected number. No threshold/floor/check weakened.
- **M262 RETRACTS M260's "zeroes entries 1..7" and "the ~140 KB views are not allocated"**: FUN_00580260's loop is the writer — cursor `esi` 0x7cded0 → `cmp esi,0x7cdeec / jl`, step `add esi,4` = 7 iterations, body `push 0x22480 ; call 0x64bc20` (140,416 B each) → `push 1 ; mov ecx,eax ; call 0x469650` (515-B SEH ctor, does NOT call the view ctor 0x518820) → **`mov [esi],eax`**, the pointer-arithmetic shape no address-grep can see; 0 lands there only when the alloc fails, which is how M260 read it as a zero-fill (G2). 0x22480 is named exactly once image-wide, 0x224b8 zero times, 0x224b8 − 0x22480 = 0x38 (heap header, INFERRED) (G3). Of 35 address-of-band sites only 4 escape, all handing out `&DAT_007cdecc`; no lea'd `&table[i≥1]` cursor is stored through or pushed (G4). Entry 1 (0x7cded0) is read 32× in ≥12 functions; the load-side FUN_00597ee0 walks entries 2..7 with the same cursor shape clearing `*(entry+0x1dd74)` and calling FUN_00479e90(entry) (G5).
- **M263**: writer set re-derives to M259's closed 8 functions / 10 indexed stores + FUN_0051c750's walk store (G6); the depth-9 forward call-closure of the 6 load-path functions (FUN_00596850/FUN_00597a70 — the only two that call map_load_arrays 0x582260 — plus their callers FUN_00597ce0/FUN_00597ee0/FUN_00598250/FUN_00598340) is 276 functions and meets that set in ZERO, and no band writer sits in any vtable slot, so indirect dispatch cannot reach them either: **the LOAD trusts the file's band bytes** (G7). FUN_00582260 has no band-shaped store and no call into the writer set; FUN_00583c70 (copy-in writer, 0x583e1d) has ZERO references in the image — no call, no imm32, no slot — so that store can never execute (G8).
- **M264**: FUN_005be090 = 24 insns / 72 B, arg1 → FUN_00649e00 (29-B shim over FUN_00649e70 passing the heap handle ds:0x99d5f8); on NULL it reports through the GLOBAL function pointer ds:0x671320 with "FATAL ERROR" + "Windows has run out of virtual memory; the game will exit…" then `push 4 ; call 0x649c80`; 0 vtable slots, 119 direct sites in 74 functions (G9) — the footing's "13 [reg+4] sites" were store-after-alloc sites, not dispatch: 14 sites in 13 functions store the new pointer at [obj+4] within 8 insns (G10). ds:0x9965b8 is a LINEAR RECORD CURSOR (6 mentions = 3 read-modify-write pairs): FUN_005dbb5f stamps a blank record (10 dword zero stores + `mov byte ptr [ecx+0x8],0x9`) and bumps +0x2c; FUN_005dbbe6 gates [rec+0x28]==0 && [rec+4]!=0, rewinds by [rec+0x10]*[rec+0x14] and frees [rec+4] via FUN_0064a7f0 (19 B, 221 callers); FUN_005dbdc0 is the FILLER — allocates [rec+0x10]*[rec+0x14] bytes via FUN_005be090, stores at [rec+4], advances the cursor by the same product (G11).
- Pitfall (recorded in the skill): a store census keyed on instructions that NAME an address cannot see `mov [cursor],value`; and reading `mov [esi],eax` as "a zero store" without asking where eax came from is what produced M260's wrong verdict. No box time; terran.exe stayed down; M181 not armed.

## Session 206 (2026-11-02, M265-M266 ANALYSE, static) — the 7 view-table blocks are objects of the class whose descriptor is 0x675964 (201 × 608-B elements + a 2,580-B virtual subobject, size proven to the byte); FUN_00583c70 is statically unreachable, one of an 8-function dead cluster

`python3 scripts/m265_m266_census.py` -> `SUMMARY M265/M266: 12/12 gates PASS`, rc=0, 2.68 s, green on inv 3 (inv 1 died on a TypeError in my own push-order helper; inv 2 = 6/12) -> `evidence/m265_m266_census.txt` (13 lines). Instrument = the .text corpus `scratch/m574/text.txt` + the RAW PE image with the `objdump -h` section map + index.csv containment, ONE corpus pass. All six inv-2 failures were mine and every one was corrected against the corpus's own print, never by relaxing a check: hex arithmetic (0xc+200*0x260 = 0x1db0c, not 0x1da8c; 0x21a6c+0xa14 = 0x22480, not +0xa24), a "4 functions" glanced from a 5-line grep (it is 5), a helper that kept only the LAST of two offsets, objdump's destination-first `mov ebp,esp`, and a nested comprehension that returned an empty callee set.
- **M265 — what the 7 blocks are**: FUN_00469650 has exactly 7 `call` sites {0x40a027 FUN_00409e70, 0x468fc0 FUN_00468fb0, 0x48dc7a FUN_0048dc20, 0x4cb5cf FUN_004cb570, 0x50aaae FUN_0050aa60, 0x5803b2 FUN_00580260, 0x59befc FUN_0059bec0} (G1); its `[ebp+0x8]` flag gates `mov [this+0],0x675964` at 0x469681 — the only mention of 0x675964 image-wide (G2) — so the sites that pass 0 keep their own descriptor. Body: three 0x64bda0 container constructs (+0xc, elem 0x260, x4; +0x98c, elem 0x260, x196; +0x1ef54, elem 0xabc, x4; element ctor/dtor pairs 0x62514b/0x62516c and 0x6251d0/0x625209) plus the same element ctor applied in place at +0x1db0c => **201 CONTIGUOUS 608-B elements +0xc..+0x1dd6c**, ending 8 B before the +0x1dd74 the load-side clears (G3); [this+4] is a lazily-freed pointer the ctor zeroes and FUN_00479e90 frees via 0x4017d0 (G7).
- **M265 — the descriptor law (new)**: [obj+0] points to a 2-dword class descriptor whose +4 IS the base-subobject offset — 0x675964→0x21a6c, 0x6763fc→0x22050, 0x678458→0x23d94 — and in each installing function the `add ecx,K`/`lea ecx,[reg+K]` that feeds `call 0x5e3b80` (the 53-caller subobject ctor) uses exactly that K (G5). The view ctor then overwrites the subobject's vptr pair 0x6725ac@+0x21a6c and 0x6725a4@+0x21eb0 (delta 0x444, both vtable bases) — a pair stored at 5 sites in 5 ctors {FUN_00421950, FUN_00469650, FUN_00518980, FUN_0059bec0, FUN_0059c1e0} (G4). SIZE PROOF: FUN_005e3b80's own stores top out at +0xa10 and 0x21a6c + 0xa14 = 0x22480 = the allocation exactly (G6). Dispatch: FUN_004412a0 reads [desc+4] then calls slots +4/+8 of 0x6725ac (= FUN_005cdd0a / FUN_005cdf82), the same two it also calls directly on the static instance 0x8cc520 (G7).
- **M266 — why FUN_00583c70 exists unreferenced**: its address appears in ZERO .text operands (rel32 targets print absolute, so that covers call/jmp/lea/push) and as an LE dword in ZERO offsets of the whole file image across all 8 sections (G8); it is not fallthrough-entered (FUN_00583c20 rets at 0x583c6b, four 0x90 pad bytes, then a real push ebp/mov ebp,esp prologue) (G9); 8 functions in 0x583000..0x584300 have n_callers==0 and ALL 8 have zero address-taken dwords — a dead cluster, not a unique anomaly (G10); its 159-insn mnemonic signature matches ZERO other functions >=40 insns, so it is not a linker-kept duplicate of a wired routine (G12); what it is: a terrain-record helper of FUN_00583c20's family — callees {0x582000, 0x5b09b0, 0x625af1, 0x64a7f0} and the same globals ds:0x92a378/0x92a37c that sibling's stride-0x2c walk uses (G11). So M263's band store 0x583e1d can never execute.
- New skill law: an address-taken census needs BOTH halves — operand-grep of the corpus (rel32+imm32 in code) and a raw LE-dword scan of the file image (data pointers); rel32 call targets never appear as dwords, so neither half alone is a reference census. No box time; terran.exe stayed down; M181 not armed.

## Session 207 (2026-11-02, B5 BUILD track, PASS 9/9) — `sim/units.py`: one arrow press = one lattice step of the 0x6784a0 ring at 3 MP, 6 MP per round, x wrapped, y bounded

**Footing.** `scripts/track_mode.py` -> `MODE=BUILD analyse_since_build=3 next_rung=B5`; rung B5 is `BUILD_SPINE.md`'s units/movement step, acceptance `python3 -m sim.selftest --replay-m27`. No box time, no `/proc`, no gdb.

**Acceptance.** `python3 -m sim.selftest --replay-m27` -> `PASS B5: 9/9 gates on evidence/m27_solowrap.log + evidence/m27_solowrap2.log`, rc=0, green on the FIRST invocation; console `evidence/b5_replay_m27.txt` (11 lines). The same commit re-ran the earlier rungs: B1 10/10, B2 7/7, B3 6/6, B4 9/9.

**The model** (`sim/units.py`, `sim/selftest.py::run_m27_replay`), gates in order: (1) trace-shape — 1 press in log 1 and 3 in log 2, idx [119, 117, 118, 120], all dir=1, all EXEC mode=3, each move stamps its own unit (-2,-2) first; (2) the four destinations == `turn_driver.md` §M27 item 4's post-state (45, 45, 43, 43 at y=11); (3) the trace's only proven start — log 1 re-stamps rec117 at (43,11) inside another unit's move — plus my dir-1 delta (+2,0) predicts (45,11), log 2's recorded destination; (4) DIR_DX/DIR_DY are the ring read out of the image at 0x6784a0/0x6784c4 (`evidence/m248_region_values.txt:3`, ring-first) — the centre-first 0x67850c readout at `:2` is the same ring shifted one index and all 8 pairs preserve (x+y) parity, both checked against that file; (5) `STEP_MP = 3` is alpha `#RULES` field 0, the file's own number (FUN_005ac550 ends `return DAT_0092a278 * moves`, so the game's MP are a loaded scale times a move count) and `MP_PER_TURN = 6` = 2 moves; (6) can-act = FUN_005acc00's `total - spent > 0` — admits steps at spent 0 and 3, refuses the third: (43,11), (45,11), None with spent 3, 6, 6; (7) x wraps as FUN_00502c40 does (79+2 -> 1, 0-2 -> 78 on the 80-wide map), y is bounds-checked and never wrapped (y=79 with dir 3 refused), and my `(w/2)*y + (x>>1)` + `x&1` view reads the same 22 B as `sim/map.py`'s `cell_index` and as the packed 44-B record; (8) all 6 re-stamps of OTHER units in the logs equal the position the replay holds for them (117 at 43, 119 at 43, 122/123 at 41 twice) — the discriminating gate; (9) from the committed pre-state (41,11) (§M25/§M27: all 8 survivors stacked there) the destinations are 2, 2, 1, 1 steps = 6, 6, 3, 3 MP, each inside one round's 6-MP budget, none off-axis.

**Finding, not a failure.** rec118's logged press covers 41->45 = 2 tiles, so one of its two steps lies outside the committed window (4 presses logged; §M27 item 1 documents a 5th, on 117); the model lands it at (43,11). §M27's post-state mpused (117/118 = 3, 119/120 = 6) is not a step count: consume-all 0x5acdb0 sets spent := total when a unit finishes acting, which is what 119/120 read.

**ASSUMED, queued as picks:** per-tile cost uniform 3 (alpha `#TERRAIN` is the terraform-improvement table, not a movement-cost table); and the bonus behind FUN_005ac550 returning 6 for these units (alpha `#CHASSIS` lists Infantry Speed = 1).

## Session 208 (2026-11-02, ANALYSE, M267 + M268 both PASS) — the 0x6725ac/0x6725a4 pair is ONE vtable with two entry points, shared by 1 ctor + 4 destructors of 4 variants of the virtual base at [desc+4]; the 201 x 608 block is tag-initialized, never indexed, never saved

`python3 scripts/m267_m268_census.py` -> `SUMMARY M267/M268: 14/14 gates PASS` (rc=0, 4.2 s, static;
`evidence/m267_m268_census.txt`). Invocations 1 and 2 were instrument bugs, not evidence changes:
7/14 (the pair-store regex left `v` unbound; the vtable "cap" was built from every stored rdata
imm32, which includes mid-table addresses like 0x6725a8) then 13/14 (G9 compared FULL op sequences,
but the ctor carries one dead `mov eax,[ebp-0x4]` reload the dtor lacks: 6 ops vs 5). No threshold,
floor or check was weakened to get green; G2's `lo_b == lo_a` clause was dropped because that cap is
meaningless, and the claim tested instead is the forward-run identity, which passes uncapped.

**M267, the pick.** 5 pair stores, one per installer: 0x6725ac at {0x42197e, 0x469798, 0x518a92,
0x59c01a, 0x59c25b}, 0x6725a4 at {0x42198e, 0x4697aa, 0x518aa2, 0x59c02e, 0x59c26b} (G1). The pair
is ONE table: 0x6725a4 == 0x6725ac - 8, the code-pointer run ends at 0x672a38 from both, 291 slots
from 0x6725ac and 293 from 0x6725a4, and the three head dwords (0x4222c0, 0x405350, 0x422190) are
none of them a Ghidra function start — thunks/labels (G2). **No installer is address-taken anywhere
in the image** (0 LE dwords over all sections; G3), so these are direct-call ctor/dtor bodies, not
vmethods, and the table's own slot 0 is a different function. FUN_00469650 is the CONSTRUCTOR (3 x
_eh_vector_constructor_iterator_ 0x64bda0, 0 x 0x64bc40); FUN_00421950 / FUN_00518980 / FUN_0059bec0
/ FUN_0059c1e0 are DEstructors (0 ctor-iter; 3/4/3/3 dtor-iter 0x64bc40) (G5) — **corrects M265 G4's
"5 ctors"**. Variant markers (G4): 0x675964 | none | 0x678184+0x67817c (the +0x23d94 subobject, the
0x678458 class whose ctor is FUN_0050aa60) | 0x67194c+0x671944 | 0x67194c+0x671944 written into
stack slots. WHY the offsets differ (G6+G7): the ctor also stores `[vptr-4] = [desc+4] - 0x21a6c`
(shard_008.c:5869) and every installer recomputes the same delta with `sub reg,0x21a6c` or
`lea reg,[eax-0x21a6c]` within 14 insns of its pair store — the subobject is a VIRTUAL BASE whose
runtime offset is read from the class descriptor, which is exactly M265's `[desc+4]` law. FUN_0059bec0
reserves 0x25318 = 152,856 B on the stack (the only 0x25318 in the image, G8), constructs the object
with flag 1 (push 0x1 at 0x59beed, so the descriptor store is skipped), calls the save writer
FUN_00597ce0 at 0x59bf46 and destructs it in the same frame.

## Session 209 (2026-11-02, ANALYSE, docs-only cap triage) — NEXT_PROMPT 15,359 -> 14,506 B: the ANSWERED topic enumeration and the s207 RESULT block moved VERBATIM to docs/pick-archive.md §trim-s209

- Trigger: kickoff `wc -c NEXT_PROMPT.md` = 15,359 > the 15,300 cap-triage trigger;
  `track_mode.py` = ANALYSE (analyse_since_build=1, next rung B6); box DOWN, `grep -c 'box time owed'
  SESSION_CURSOR.md` = 0; tree clean. Per the loop rule the cap triage is the whole fire — no
  milestone was started.
- Split, not shave: the two oldest footing blocks moved VERBATIM into `docs/pick-archive.md`
  §trim-s209 (54,860 -> 56,524 B): the ANSWERED bullet's topic enumeration (756 B) and the
  RESULT (s207, BUILD) block (378 B). Provenance checked by script against
  `git show main:NEXT_PROMPT.md`: both strings present in the archive, absent from the live file.
  The live file keeps the id-range + pointers (`NAMED.md` per-id §s196-§s208; the BUILD TRACK B5
  line already carries `NAMED.md` §B5 with its 3 OPEN items).
- Stale footing fixed in passing: ledger now `Merged M54A-M268 + B0-B5 (through #197)` (was
  `M54A-M266 + B0-B4 ... B5 is this PR`).
- Headroom: 14,506 + a ~1,000 B RESULT append lands under 15,300; the next close must move the
  s208 RESULT block (1,274 B) VERBATIM to keep the cycle.
- Not triggered: skill/SKILL.md 59,419 B (<69,000); evidence/ 28.3 MB (warn, trigger 28.5 not
  reached); no new evidence files this fire.

## Session 210 (2026-11-02, ANALYSE, M269+M270+M271 through ONE instrument, PASS 10/10) — the virtual-base delta is image-wide (41 stores / 8 K / 31 functions); the 0x678e40 class is a 152,856-B stack object with ONE instance site; 32 vbtable descriptors close the K census

- ONE script `scripts/m269_m271_census.py` (whole-image `.text` shadow + PE image + `ghidra_out/index.csv`;
  no box, no `/proc`, no gdb) -> `SUMMARY M269/M270/M271: 10/10 gates PASS`; evidence
  `evidence/m269_m271_census.txt`. Acceptance invocations used: 2 (the first printed 7/10 — three offsets I
  had transcribed from a disassembly window into MY gate texts were wrong: the 0x614150 ctor is called at
  +0x252ec not +0x24fec; M215's row ends at 0x247a0+0xb4c = 0x252ec; the dword 0x59c380 appears only at
  0x678e40 because dw(0x678e3c) = 0x405350). No gate, floor or check was weakened.
- M269: the geometric test (a store counts only if its address resolves to `field + [desc+4] - 4`) matches
  41 delta stores in 31 functions at 8 distinct K: 0x18 x11, 0x1c x2, 0x48 x2, 0x8c x4, 0x188 x14,
  0x21a6c x5, 0x22050 x1, 0x23d94 x2. G1/G2: the 5 K=0x21a6c functions ARE M267's 5 installers — the delta
  detector and the install detector name the same 5. Same pass: 177 vptr installs made THROUGH a vbptr of 33
  distinct tables; 9 secondary-view tables each have their primary 8 B above with the identical count;
  biggest family 0x6713a0 (52 installs). 21 lineage-matched stores of a delta value are `sub reg,1`
  arithmetic — reported, not gated.
- M271: 32 of the 247 rdata immediates stored through a register are vbtables (dword[0] and dword[+4] both
  |v| < 0x40000, neither a code pointer), 21 distinct [+4] offsets, and every K M269 found is one of them
  (0x21a6c->0x675964, 0x23d94->0x678458, 0x22050->0x6763fc, 0x188->0x679de0, 0x8c->0x679c28/0x679da4,
  0x48->0x67991c, 0x1c->0x679a98, 0x18->0x6713ac/0x6713f4/0x671408). [0x675964]=0,[+4]=0x21a6c is installed
  only by FUN_00469650 and [0x678458+4]=0x23d94 only by FUN_0050aa60, and both installers carry a delta
  store at their own K.
- M270: 0x678e40 (secondary 0x678e38 at +0x2444) stored exactly once image-wide each, both inside
  FUN_0059bec0 (0x59bf1c/0x59bf26). Slot 0 of each is its deleting-dtor wrapper (0x59c380 -> FUN_0059c1e0 ->
  0x64bb70). Layout closes on itself: +0 the 0x5e3b80/0x5e3ced class, +0x2320 the 0x675964 class
  (0x2320+0x22480 = 0x247a0), +0x247a0 M215's 0xb4c row (= +0x252ec, exactly where the 0x614150 ctor is
  called AND where the dtor calls 0x6141c1), virtual base +0x23d8c = 0x2320+0x21a6c (destroyed via 0x5e3ced
  in both, so it is the same type as the +0 object), size 0x25318 = the only 0x25318 immediate image-wide
  (the alloca probe at 0x59bed1) = the span [ebp-0x25324, ebp-0xc). RETRACT part of M267: FUN_0059bec0 is
  not a destructor (four ctor calls precede its 0x678e40 install; the same objects die at its tail) and its
  0x67194c/0x671944 are M215's ROW at +0x247a0, never [this+0] — the installer of 0x67194c at [this+0] is
  FUN_005faec0 (M215). Callers of FUN_0059bec0: FUN_0050fea0, FUN_00512b40, FUN_00516b80, FUN_0051e700.
- Pitfall (mine, cost one acceptance): offsets read off a head/tail window and typed into a gate are not
  evidence. Let the instrument print them (hex AND decimal) first, then write the sentence.
- Box DOWN (`ps` shows no terran.exe), nothing owed (`grep -c 'box time owed' SESSION_CURSOR.md` = 0); M181
  still unarmed (no box, no positive control). M241 (#180, 2/5) still open by design.
