

Older sessions: `docs/sessions/sessions-152-168.md` (15 sessions). Read it only when a question reaches back before session ## Session 171.

## Session 171 (2026-10-29) — M111 BLOCKED: the 156-B tail has no named reader, and the census model is VOID (over-counts by 468 B)

Three acceptance invocations, none green, nothing merged.

1. m111b1 `python3 scripts/m109_leg_census.py --tag m111b1 --relaunch --ranges 0x44b000-0x630000`
   (all 221 call sites to the 4 readers) — gdb DETACHED after 3 events on wineserver's SIGUSR1
   (`handle SIGUSR1 nostop noprint pass` + a 400-continue tail were MISSING from this harness; now in it).
   Events logged before the detach: 0x62ae0f dest=0x7cda1c size=128, 0x62aec8 size=16, 0x62af05 size=16.
2. m111b2 same range with the SIGUSR1 handles — the 31 CRT-band sites (0x62b000-0x62d000) are HOT:
   0x62b8f0 and 0x62b935 fired 8,277x each during STARTUP, 25,957 stops in 12 min, ZERO loader hits,
   then the event stream froze for 7 min = the m109g3 starvation shape. Killed by pid.
3. m111b3 `python3 scripts/m109_leg_census.py --tag m111b3 --relaunch --ranges 0x400000-0x62afff`
   (190 sites = 221 minus the CRT band): the load RAN (counts 67/18) and completed —
   0 gdb errors, 90 executed sites, **sum(size*count) = 243,007 vs file 242,539 → OVER by 468 B**.
   So the cumulative "file_off" column is not a statement about the save: the executed set mixes in
   (a) three 160-B CRT reads into 0x7cda1c / 0xbe8c10 / 0xbefd3c, and (b) a 9-iteration per-entity loop
   of 6 x 4-B reads into heap dests 0x3b7d7a8 .. 0x3c4b420 (stride 0x224B8, the M110 pair 0x59666d/0x5966c1).
   The M110 "contiguous 0..242,383" figure is therefore an artifact of UN-ARMED sites, not proof of what is
   unread. Do not repeat it as a closure.

READ-BACK after the load (no gdb, /proc/1573718/mem, 523 MB of readable maps): the save's last 156 B are NOT
present verbatim anywhere; the 12-B row signature `fa ff ff ff 20 00 00 00 20 00 00 00` (6 rows in the save)
appears exactly 6x in ONE region, 0x34f0000. The RECORDS reach memory, the BLOB does not — a per-record
restore, not a bulk 156-B read.

Instrument fixes this session (committed): session_brief.py and accept_ready.py print BLOCKED instead of a
CalledProcessError traceback when terran.exe is down; m109_leg_census.py now sets M54A_LOAD_TIMEOUT=1800,
carries the SIGUSR1/USR2/SIGPIPE handles + 400-continue tail, and prints a CLOSED/PARTIAL verdict (exit 4).
test_accept_ready.py PASS 17/17 after the change.

### Session 171 (cont.) — M112 static pass: the 156-B tail is a fixed TRAILER, almost certainly write-only

No box time, no acceptance invocation spent. Three laws, each with the command that produced it.

1. **It is a trailer, not data.** `programs/saves/*.SAV` + `programs/saves/auto/*.SAV` (9 files, sizes
   242,539 (m54b_clean) and 242,815 / 242,875 / 242,919 / 242,927 / 242,971 / 243,483 / 243,691): the last
   **152 B are byte-identical in all 9**, only the FINAL dword differs (365,402,425 / 766,622,009 /
   746,214,987 ...). Structure: 5 rows of 24 B `[id,0,0,-6,32,32]` for id 3..7, then `[1,1,0x80000080,-14,32,32]`,
   then `[800,387,X]`. A section of game data would vary with the game; this does not, and it sits at EOF at a
   per-save offset — so nothing hard-coded can index it.
2. **No code can size it.** The value 156 (0x9c) occurs as an *immediate* only 13x in the whole executable
   (objdump `scratch/m574/text.txt`, stack-frame displacements `[ebp-0x9c]` excluded) and **never inside the
   save family 0x58xxxx-0x59xxxx**; the only two `push 0x9c` are 0x4b3476 / 0x4b3e3d. The loader's own code has
   no constant that could bound a 156-B read.
3. **It is not restored.** Live read-back (no gdb): memory at the loader's LAST read destinations
   0xbe27b0 / 0xbe27b4 (sites 0x597a19 / 0x5979f8, the end of FUN_00596850) holds unrelated values — no 800, no
   387; the 156 B is absent verbatim from 523 MB of readable memory; its 12-B row signature
   `fa ff ff ff 20 00 00 00 20 00 00 00` appears exactly 6x at heap **0x34f0000** and in **0 of the 24 files**
   in programs/ (so it is not a static table the game carries).

**Read this as:** the M110/M111 "156 B of save data with no reader" framing is wrong. The writer emits a fixed
trailer at save time; the loader's read set does not cover it. The acceptance for closing it (not yet spent):
load an AUTOSAVE (its trailer sits at a DIFFERENT offset) under a FILE*-filtered census and predict
**sum = filesize - 156 again** — two files, two offsets, same shortfall.

**Correction, same session:** the loader DOES push a **152** immediate (`0x597716`), so "no constant can size the
tail" is too strong — the honest statement is that its destination `0x92bf58` holds `[9999,9999,0,0,2100,2600]`,
NOT the trailer rows, so that leg is some other section. What survives: the trailer's offset varies per save, its
rows reach memory only as records (6x at heap 0x34f0000), and the 156 B is absent verbatim from memory.

### Session 171 (cont. 2) — M112 attempt 1 (m112a1): the FILE* filter works, the SUM DOES NOT — and the trailer question needs a poke, not a census

`python3 scripts/m109_leg_census.py --tag m112a1 --relaunch --ranges 0x400000-0x62afff --filter-file --save
m112auto1.SAV` (copy of "Alpha Centauri Autosave 1.SAV", 242,927 B, trailer at 242,771; counts 68/19):
**savefile=0x6a79a0 captured at 0x596850, 83 legs, 0 gdb errors, sum 243,071 vs file 242,927 -> OVER by 144.**
Predictions before the run were H1 structural-trailer sum = 242,771, H2 fixed-read-set 242,383, H3 trailer-read
242,927; the observation matches NONE of them, which is itself the result: **the cumulative offset column is
still invalid after filtering** (unfiltered m111b3 was over by 468; filtered, by 144). Two runs, two different
saves, two different over-runs: the size*count sum cannot decide this question at all.
No (site,dest,size) group repeats, so the 144 B are re-reads at different destinations/sites, not one duplicated
leg. Read-back at the final group's destination (0x62ae0f 128 + 0x62aec8 16 + 0x62af05 16 into 0xbefd3c) shows
[9552352, 839181731, 1, 1, 5, 24592, ...] — NOT the trailer: 0xbefd3c is a shared CRT stdio buffer that later
reads of OTHER files overwrite, so the buffer content is not evidence either.

**Reframe (the useful part):** the loader consumes through a 4096-B stdio buffer, so the trailer's bytes are
pulled into RAM no matter what; "read or not" is not answerable by counting consumer fread sizes. The next
experiment must make the bytes IDENTIFIABLE: poke a unique pattern into the trailer of a save copy, load it, and
scan /proc/<pid>/mem for that pattern. Pattern present = the trailer is loaded; absent = it is never consumed.
That is one run, needs no offset model, and cannot be confounded by a shared buffer.

Box after the run: terran.exe 1878861 (autosave m112auto1 loaded, counts 68/19). gdb 1878864 was LEFT ATTACHED
again after the harness printed its verdict — killed by pid, TracerPid now 0. (Second occurrence of the law.)

### Session 171 (cont. 3) — M112 attempt 2 (m112p1, POKE): the 156-B trailer IS READ. The per-entity loop is its reader. M110's shortfall is RETRACTED.

`python3 scripts/m112_trailer_poke.py --tag m112p1 --relaunch` — copies m54b_clean.SAV, plants **10 dwords of
0xCAFEBABE** in the two zero fields of each of the 5 trailer rows (40 B changed, file size unchanged, and the
magic occurs **0 times** in the original save, so any hit is ours), loads it, then scans /proc/<pid>/mem.

Result: **load rc=0, counts 67/18, 522.9 MB scanned, 41 MAGIC hits**, the five structural ones at
**0x3bc2110, 0x3be45c8, 0x3c06a80, 0x3c28f38, 0x3c4b3f0**. Those are EXACTLY the destinations I dismissed as
"pollution" in m111b3, minus 8: the 6-site per-entity loop (0x59666d / 0x5966c1 / 0x596715 / 0x596769 /
0x5967bd / 0x59683b) reads each trailer row's 6 dwords into heap record starts 0x915758, 0x3b7d7a8, 0x3b9fc60,
0x3bc2118, 0x3be45d0, 0x3c06a88, 0x3c28f40, 0x3c4b3f8 (stride 0x224B8) and 0x8eb7c4. The census logged the
2nd/3rd word's dest (row+8) and the poke shows the row's own bytes there — so the loop IS the trailer's reader.

Consequences: M110/M111's "contiguous 0..242,383, 156 B with no reader" is **RETRACTED, not narrowed** — the
trailer is consumed; it is 5 `[id,0,0,-6,32,32]` rows (id 3..7) restored one row per heap record. The census's
+468 (m54b_clean) and +144 (autosave) over-runs are the ORDER assumption in its cumulative `file_off` column
(the same bytes are touched twice, once bulk and once per row), never missing or extra file content.
Harness `scripts/m112_trailer_poke.py`; verdicts CONSUMED / NOT CONSUMED / REFUSED (all three conclusive, exit 0).

## Session 171 (close-out) — M110-M112 merged as #116 (squash 645384b)

The PR TITLE still reads "M111 BLOCKED: the 156-B tail has no named reader, and the census model is VOID" because
it was opened while that was true; the merge carries the later commits and the resolution above (m112p1: the
trailer IS read, by the per-entity loop; M110's 99.94%/unread claim retracted). Read the commits and NAMED.md,
not the PR title. main = 645384b; branch deleted; local tree clean.

## Session 171 (cont. 4) — the offline "re-derive the .SAV map" attempt is VOID (recorded so nobody spends a run on it)

Two cheap shapes were tried and both are disqualified BEFORE any box time:

1. **decode_save.py --sections cannot run on these saves** — it dies with `no 52/304 split of a 0-byte region`
   on all 9. Its `MAP_SECTIONS = 2724 + 140800` is a 128x128 grid; m54b_clean's map is `2,724 + 90,112 + 91 =
   92,927` (M110: 64x64x22), so the constant alone over-runs the file by ~50 KB and every later offset is wrong.
   A real lead: derive the map size from the header dims per file (data-formats.md has the formula for .MP).
2. **A subset-sum over the candidate legs is UNDERDETERMINED, not a solution.** With the 64x64 map and 52n+304m
   free, m54b_clean admits **181,769** exact decompositions of its 242,539 B (e.g. `maptrailer91` + n=32/m=531);
   auto1 admits 182,718, auto30 184,074. A search whose answer set is that large cannot pick a layout — the same
   "shape that cannot discriminate" trap the kickoff warns about. Content constraints or pokes must filter it.

So the .SAV map stays OPEN, and the next attempt must be poke-driven: plant a marker at a candidate section start
in a save copy, load, and look for it (the m112p1 instrument, one section per run, 2-3 candidates per save).
Nothing merged; no acceptance invocation spent on this.

## Session 171 (cont. 5) — M113 ACCEPTED (m113map1): the .SAV offset->memory map, extracted by pokes (20/20 anchors)

`python3 scripts/m113_save_map.py --tag m113map1 --relaunch --step 16384` — 20 markers `0xC0DE000i` planted at
16 KB offsets + the 6 candidate section starts in a copy of m54b_clean, loaded (rc=0, counts 67/18), and every
marker searched in 522.7 MB of /proc memory: **20/20 found, 0 absent**. Anchor table (file offset -> destination):

```
16,384 0x951104   32,768 0x955104   49,152 0x959104   65,536 0x95d104      <- run 1, slope 1
81,920 0x92ad6c                                                           <- map header
98,304 0x40aa5b0  114,688 0x40ae5b0 131,072 0x40b25b0 147,456 0x40b65b0
163,840 0x40ba5b0                                                         <- run 2 (the 90,112-B grid), slope 1
172,287 0x15e2baf                                                         <- map trailer region
180,224 0x987d51  188,291 0x989cd4  188,467 0x930e20  192,051 0x98aad4
196,608 0x98bf49  212,992 0x98ff49  218,675 0x99157c  222,771 0x92cfe4
229,376 0x95e635
```

What the anchors establish (each independently of any census):
- **Three slope-1 runs** — 16,384..65,536 -> 0x951104..0x95d104; 98,304..163,840 -> 0x40aa5b0..0x40ba5b0;
  196,608..212,992 -> 0x98bf49..0x98ff49. Inside a section, file offset maps to destination 1:1.
- **The 90,112-B grid is at 0x40a6660** — the run-2 anchors sit on it with step 0x4000, confirming M110's map
  from an instrument that cannot over-run anything.
- **Two leg boundaries corroborated to the byte**: 188,291 -> 188,467 is exactly **176 B** apart and lands at
  0x930e20 (the count-prefix leg at 0x930d7c), and 218,675 -> 222,771 is **4,096 B** apart (the 0x92bff0 leg).
- Region boundaries are where the destination JUMPS: block A -> map header between 65,536 and 81,920; map ->
  trailer between 163,840 and 172,287; trailer -> section between 172,287 and 180,224.
Harness `scripts/m113_save_map.py`; it plants markers, loads through `m54a_load.py`, and prints every anchor.

## Session 171 (cont. 6) — M113 attempt 2 (m113map2): boundaries bracketed to 2 KB; one offset is ABSENT

`python3 scripts/m113_save_map.py --tag m113map2 --relaunch --step 2048 --band 64000-82500:2048
--band 163000-174000:2048 --band 174000-182000:2048 --band 221000-231000:2048` — 25 markers inside four named
bands (a full 118-marker sweep is refused by the harness: 60+ pokes mutilate counts and pointers). Load rc=0,
counts 67/18, 523.0 MB scanned, **24/25 found, 1 absent**.

Boundaries, now bracketed by adjacent runs rather than assumed:
- block A -> block B: last A anchor **66,048 -> 0x95d304**, next **68,096 -> 0x927684** (block B = 0x927590). The
  documented 67,840 split falls inside the bracket. Slope-1 continues through block B, the 32-B table and the map
  header: 68,096..80,384 -> 0x927684..0x92a76c, then **82,432 -> 0x40a67b0** (grid).
- grid -> trailer -> next section: 163,000..171,192 -> 0x40ba268..0x40bc268 (grid, step 0x800), then
  **173,240 -> 0x986209** (the 0x985e5c section). So the grid ends and the 91-B map trailer (file 172,200..172,291)
  lives inside the bracket 171,192..173,240 — consistent with run 1's 172,287 -> 0x15e2baf.
- 174,000..180,144 -> 0x986501..0x987d01, step 0x800, all inside the 16,000-B section.
- record area: 221,000 -> 0x92c8f9, **223,048 -> ABSENT**, 225,096 -> 0x933b81, 227,144 -> 0x95dd7d,
  229,192 -> 0x95e57d (step 0x800). The 52-record block starts ~222,783 (0x933278 anchors it), so the absent poke
  sits INSIDE that block: either a gated/unused record or a field the loader rewrites after the copy. Not resolved.

So two of three boundaries are now pinned to the KB, the third (record area) has a specific open question with an
address to chase, and the harness gained `--band lo-hi[:step]` plus a hard cap of 60 markers.

## Session 171 (cont. 7) — M113 attempt 3 (m113map3): the "hole" is not a hole — the 52-record array maps 1:1 and a few FIELDS are rewritten after the copy

`python3 scripts/m113_save_map.py --tag m113map3 --relaunch --step 128 --band 222000-224500:128` — 20 markers at
128-B spacing, load counts 67/18, 522.5 MB scanned, **19/20 found**. (`m54a_load.py` returned rc=4, its HUD
"live" check failing while counts were already correct — the load itself ran; the harness treats rc!=0 as exit 6.)

- The 52-record array maps **1:1 with an odd base**: 222,896 -> 0x9332E9, 223,024 -> 0x933369, 223,280 ->
  0x933469, ..., 224,432 -> 0x9338E9, every step +0x80 for +128 B. The base is **file 222,783 -> 0x933278**
  (0x9332E9 = 0x933278 + 113 = 0x933278 + (222,896 - 222,783)), which pins the block start that the leg list only
  guessed.
- **The absent offset MOVED**: 223,048 in m113map2, 223,152 in m113map3. Expected dests 0x933351 (record 4, byte 9
  of 52) and 0x9333E9 (record 7, byte 5). Different fields in different runs, both with present neighbours 128 B
  away — so this is **not an unread region**; a handful of dwords in the 52-byte records are rewritten by the
  loader's post-processing after the bulk copy. That also explains the census's re-read/over-run pattern.
So M113 closes with: three boundaries bracketed to the KB (attempt 2), the record block's base pinned to the byte
(attempt 3), and one residual class of rewritten fields, named and located, instead of an unexplained 156-B hole.

## Session 171 (cont. 8) — M114 (zero box time): the .SAV is restored 1:1; live rewriting is confined to two zones

Method: with the poked save loaded, diff `/proc/<pid>/mem` against the FILE at the anchor-derived mapping
`dest = off + k`, 1 KB windows at 12 anchors spread over the whole file. **10 of 12 windows are byte-identical**
(k constant within a region: block A 0x94D104, grid 0x40925B0, the post-map section 0x95BD51, 196,608/212,992 ->
0x95BF49, 52-records 0x926635). The two exceptions:
- **map header tail: file 81,408..82,100 differs (665 bytes, contiguous)** — the game rewrites the end of the
  2,724-B map header on load (the grid itself at 82,432 is clean).
- **block A tail: file 67,080..67,143 differs (238 bytes) with a 16-byte STRIDE, 2 bytes per hit** — a per-record
  u16 array the load recomputes (first hits 67,080/67,081, 67,096/67,097, 67,112/67,113 ...).
And the 52-record array (3,484 B, base file 222,783 -> 0x933278) differs in exactly **2 dwords**:
222,831 `0x0003FFFF -> 0x00000000` (the game clears it) and the poked field at 223,152 whose top byte came back
`0xC0 -> 0xD6` (the game normalises that field). That is the whole residual: two zones plus one normalised field,
not an unread region.
Also from the anchors: block B's base is file **67,852** -> 0x927590 (the documented 67,840 is 12 B early), pinned
by 68,096 -> 0x927684.

## Session 171 (cont. 9) — M114 CORRECTION: the "two rewritten tails" are a K STRADDLING ARTIFACT. The save is 1:1.

M114's claim is RETRACTED, caught 20 minutes later by checking the addresses before arming a watchpoint on them.
The two "rewrite zones" came from windows that STRADDLE a region boundary but were compared with ONE region's
`k`, so they diffed by construction:
- "block A tail 67,080..67,143" is below block B's base (67,852) and was diffed with block B's k=0x916C84 -> the
  238 "diffs" are block-A-vs-block-B content, and the 16-byte "stride" is just two different arrays lining up.
- "map header tail 81,408..82,100" straddles the grid start (82,088) and was diffed with the GRID's k=0x40925B0.

With per-region k the whole file is CLEAN:
```
block A      66,048..67,840   k=0x94D104   0 byte diffs
block B      67,852..79,328   k=0x916C84   0 byte diffs
map header   79,364..82,088   k=0x916D6C   2 byte diffs, both at the FIRST offset (79,364)
grid         82,088..172,200  k=0x40925B0  10 byte diffs, starting at the FIRST offset (82,088)
```
So the restore is **1:1 for every byte of the four big regions**, and the only divergences are a handful of bytes
at the START of the map header and the START of the grid, plus the 2 dwords already known in the 52-record array
(222,831 cleared, the poked field at 223,152 normalised). Confirmed live before arming anything: file 67,080 ->
0x95D70C holds 65,535 in BOTH the file and memory, i.e. no rewrite there.
LAW: a diff window must lie WHOLLY inside one region — a window across a boundary compared with one region's `k`
manufactures diffs that look exactly like real rewriting.

## Session 171 (cont. 10) — the two systemic fixes, as CODE (not advice)

1. **`scripts/save_diff.py` + `scripts/test_save_diff.py` (PASS 7/7)** — the region guard M114 needed. It derives
   regions from the poke anchors (`k = dest - off`), refuses any range that crosses a KNOWN section boundary
   (67,852 block B / 82,088 grid / 172,200 trailer / 172,291 next section / 222,783 52-records — each derived from
   an anchor plus its documented destination base, not a midpoint), and names the boundary it refused on.
   The two windows M114 merged are now REFUSED BY THE TOOL (`67072-69120` -> boundary 67,072; `81408-82100` ->
   the grid start), so the next session cannot repeat that comparison by accident.
2. **`scripts/m109_leg_census.py` teardown** — after the verdict it SIGTERM/SIGKILLs gdb by pid in a loop, then
   READS `TracerPid` from /proc and records it in the log header; if it is not 0 the harness exits **8** with the
   pid to kill. Two runs today (m111b3, m112a1) printed a verdict while gdb was still attached to the game.
3. **`scripts/m113_save_map.py` now verifies every anchor LOCALLY** (`local_1to1`, ±8 B by default): a hit proves
   the marker landed, the local comparison proves the mapping AROUND it is 1:1, which is the assumption every
   later diff leans on. Checked against the live box: 64,000->0x95CB04, 68,096->0x927684, 81,408->0x92AB6C (±64),
   82,432->0x40A67B0 (±64) and 174,000->0x986501 all return 0 local diffs — which independently confirms that
   M114's "map header tail" was the straddle artifact and nothing else.

## Session 171 (cont. 11) — M116 ACCEPTED (m116flag, PASS): the band-flag gate is a BYTE test, no OR sets 0x40, and "0 for all 8" is FALSE

`python3 scripts/m116_band_flag.py` (static over the image + live read of the 8 faction words) — **PASS**.

- **The gate is a byte test** at **0x5aaf7f**: `test BYTE PTR [esi+0x94d430],0x40`, inside **FUN_005aadf0+0x18f**
  (528 B), three instructions after `mov [esi+0x94d800],eax` (the FUN_005aab70 advance threshold is reloaded and
  stored, then the byte is tested). Exactly ONE such test exists in the image.
- **Nothing ORs 0x40 into it.** 170 instructions touch disp 0x94d430; the 17 `or` sites set 0x800000, 0x400000,
  0x1000000, 0x2000000, 0x4000000, 0x8000000, 0x10000000, 0x80000000, 0x40000000, 0x20000000, 0x200000 and 0x2 —
  **zero set 0x40**, so the bit can only arrive through a whole-dword store (18 sites).
- **"bit 0x40 = 0 for all 8 factions" is FALSE at the current state**: the eight words read
  0, **0xFFFFFFFF**, 0, 0, 0, 0, 0, 0 — bit 0x40 is SET for faction 1 and zero for the other seven.
- **But the interpretation is NOT established.** Faction 1's whole dword (and 0x94d434) is 0xFFFFFFFF, which is also
  the shape of a -1-filled/uninitialised record. So "the second ask runs for faction 1" is an INFERENCE. The
  controlled test is a poke: clear bit 0x40 for faction 1 and count hits at 0x5aaf88 (the taken branch).
NAMED's row is amended to say exactly that instead of "never ran".

## Session 171 (cont. 12) — M117 (m117g2): the byte test IS reached 17x a round and never taken; and M116's live half is RETRACTED (stride is DECIMAL)

`python3 scripts/m117_gate_take.py --tag m117g2 --turns 1 --relaunch --save m54b_clean.SAV` — two silent bps:
0x5aaf7f (the byte test, logs `esi` + the byte) and 0x5aaf88 (the taken branch), over one real turn on a clean load.

**17 test hits, 0 take hits, 0 gdb errors.** Per faction: 0 -> reached 0; 1 -> 2; 2 -> 4; 3 -> 1; 4 -> 3; 5 -> 3;
6 -> 3; 7 -> 1. So the gate is **live and reachable every round** (factions 1..7; faction 0 never) and **never
taken**: bit 0x40 is clear for all eight in this state, which MATCHES the original NAMED row — the M89 second ask is
inert here, and the open question is what SETS bit 0x40 (no `or` does; the 18 whole-dword stores are the candidates).

**M116's live half is RETRACTED — my own stride bug.** NAMED writes the faction stride as `f*8380`; that is
**DECIMAL 8,380 = 0x20BC**, and I read it as hex 0x8380 (33,664). The M116 table therefore sampled factions
0, 4, 8, 12... and its "0xFFFFFFFF for faction 1" was really 0x94d430 + 0x8380, a different structure. The corrected
read of the true stride gives **0, 0, 0x04000000, 0, 0, 0, 0x10000000, 0** — bit 0x40 clear everywhere. M116's
**static** half stands unchanged (the `test BYTE PTR [esi+0x94d430],0x40` at 0x5aaf7f in FUN_005aadf0+0x18f, and
the 17 `or` sites, none of which sets 0x40). `scripts/m116_band_flag.py` now carries the decimal stride and prints
"matches NAMED" when no faction has the bit.
Also: m117g1 was a WEDGE (`smac_play` rc=5, HUD byte-static 61 s) — the harness now reports a wedge as
**NO MEASUREMENT** instead of "the test was never reached", because those are different facts.

## Session 171 (cont. 13) — the M117 harness called a NEGATIVE RESULT a failure (exit 4)

`m117g2` exited **4** because its code was `rc = 0 if (not tests or takes) else 4` — i.e. "the gate was reached and
never taken" was encoded as a failure. That is the milestone's actual FINDING (17 test hits, 0 takes, bit 0x40 clear
for all eight), so the harness was mislabelling its own result. Fixed:
`rc = 0` whenever the site was reached (take or no take), `4` only when the site was never reached (inconclusive),
`5` for a wedge (no measurement), `8` for a dirty box. Same class as m111b3/m112a1's stale-gdb "success": an exit
code that does not mean what its reader will assume.

## Session 171 (cont. 14) — M118 ACCEPTED (m118flag, PASS): bit 0x40 has NO setter and no save carries it — the second ask is inert BY CONSTRUCTION

`python3 scripts/m118_flag_never_set.py` — four independent checks, no box time:

- **A** exactly one `test BYTE PTR [..+0x94d430],0x40` in the image: **0x5aaf7f** (FUN_005aadf0+0x18f, take 0x5aaf88).
- **B** the 17 dword `or` sites at that displacement set 0x800000..0x80000000 and 0x2 — **none sets 0x40**.
- **C** the byte-bit setters are REGISTER ops (`or al,0x40`), which a dword-immediate scan cannot see: 22 such sites,
  and exactly ONE (0x4dc226) reaches a flag store — 0x4dc296 — but that store takes `eax` **reloaded from the flag**
  and masked `0xfc3fffff`, so the or'd bit never reaches the source; the derived value goes to `ds:0x99aa38` and
  **0 instructions move it back** into a +0x94d430 slot. The block is a bit TRANSLATION (source bit 0x800000 ->
  derived bit 0x40), not a setter.
- **D** bit 0x40 is clear for all 8 factions in **all 12 saves** on disk (m54b_clean + 8 autosaves + the three pokes)
  — and block A is restored 1:1 (M114), so a save carrying the bit would set it.

**Verdict: the M89 second ask cannot fire on this build and this save version.** M117's "inert on this state" is
strengthened to "inert by construction" — while the branch stays live and reachable (17 hits a turn).
Lesson recorded in the skill: a byte-field bit test/set is `test BYTE PTR [x],0x40` / `or al,0x40`; scanning only
`or DWORD PTR [disp],imm` misses every real setter (I nearly concluded "no setter" from exactly that gap).

## Session 171 (cont. 15) — M119-M123, five field questions settled from the static image (all PASS, zero box time)

`python3 scripts/field_census.py` (evidence/fields_m119_m123.log) — SUMMARY stride=PASS bit5=PASS readonly=PASS
copy=PASS dual=PASS.

- **M119 stride conflict RESOLVED.** The array at 0x984d38 is addressed with **0x30 (48 B)** at all 52 indexed sites:
  45 via `lea X,[v+v*2]; shl X,4` and 7 via `imul X,0x30`; **0 standalone `shl 4`** on a bare index. M67's "conflict"
  was a misread: the ×16 in the listing is `shl 4` applied to 3v — the tail of the ×48 computation, not a second stride.
- **M120 bit 0x20 at 0x531782 NAMED.** `test BYTE PTR [eax*4+0x94d448],0x1` at 0x531778, `je 0x5317a2` at 0x531780,
  then `or BYTE PTR [ebx+0x98adb8],0x20`: the entity-status bit is set **iff the faction-block dword at
  0x94d448+inner*4 has bit 0**. The index is `esi*2095 + edi` — 2095 dwords = 8,380 B, so the "array" is the faction
  block with the stride folded in (a second independent confirmation of 8,380 after M117).
- **M121 ds:0x98adee is READ-ONLY.** 7 `movsx` readers (0x4e499d, 0x4eeb35, 0x4f948c, 0x51ff61, 0x5a9e06, 0x5a9e5f,
  0x5aa1a6), **0 writers of any width**, and no access to the enclosing dwords (0x98ade8/0x98adec/0x98adf0). The
  "forced-pick key, live 6" therefore arrives with the LOAD — save/scenario data, not a gameplay counter.
- **M122 the 0x1c loop is a COPY, not a third stride.** 0x52b744-0x52b76a copies **0x91cb80 -> 0x98aaf8**, 28-B
  records, 24 of them ((0x98ad98-0x98aaf8)/0x1c exact), and never references 0x984d38. The two arrays merely sit in
  the same address neighbourhood.
- **M123 ds:0x94d78c is ONE dword, two addressing forms.** 72 refs: 48 `[reg+0x94d78c]`, 24 `[reg*4+0x94d78c]`, 6
  writes. All **24** array-form sites carry a 2095-scaled index (`shl 6 / add / lea *2 / shl 4 / sub`), so the *4 is
  the compiler's folded faction stride — same field, no second array (M116's law applied: read the encoding, not the
  syntax). Third confirmation of 8,380.
Instrument note: `open(p,"w").write(open(p).read()...)` truncated field_census.py to 0 bytes — read BEFORE opening for
write; the file was rebuilt from the conversation, not from a backup.

## Session 171 (cont. 16) — doc restructure: the footing file is now an index, the narrative is archived

`NEXT_PROMPT.md` was 15,305 B against a 15,500 cap — 195 B of headroom, and every milestone needs ~600 B of pick text,
so the next batch could not be recorded without deleting findings (three consolidations today were exactly that).
Split instead of shaved: `docs/pick-archive.md` (10,957 B) now holds the M90-M123 milestone narrative and the FULL trap
text; `NEXT_PROMPT.md` (12,936 B) keeps the RULES as 22 one-liners plus the live footing and the closing order.
Headroom 195 B -> 2,564 B (13x). Verified nothing was lost: 21 identifier tokens checked across both files, all present
(0x5a7e7f/0x94d6a4/probe3.py/0x4efe60/TAILOUT/0x93325c/0x6a9480/0x59666d ...); the only "missing" hits were a typo in my
own check (0x93ff3c vs 0x3ff3c) and a name written as FUN_005a6d40 rather than 0x5a6d40.
Also recorded the batch-size finding in BUDGET: 3 milestones comfortable, 5 max when they share one instrument,
box-time milestones 1 per batch.

## Session 171 (cont. 17) — NAMED.md split: the historical middle is archived, the live registry has headroom again

`NAMED.md` was 249,762 B against a 250,000 budget (238 B free), so the next milestone could not be recorded. The
registry's bulk is HISTORY: blocks M32-M84e (sessions 32-133, 52 blocks) are settled findings nobody re-reads to pick
work. Moved byte-identically to `docs/named-archive-m32-m84e.md` (182,747 B); `NAMED.md` keeps the method, `Not yet
named`, and every block from M89 on, and now carries an ARCHIVED pointer telling the reader to grep both files.
**249,762 -> 68,064 B** (181,936 free). Integrity checked line by line: 0 of the moved lines absent from the archive.
Rules that keep this honest: the move is a rename across files in one commit (git records it, nothing is deleted from
history), and the archive names its block order in its own header.

## Session 171 (cont. 18) — M124-M126, three names settled statically (all PASS, zero box time)

`python3 scripts/m124_state_and_memo.py` — SUMMARY M124=PASS M125=PASS M126=PASS (evidence/m124_m126.log).

- **M124 ds:0x926bd4 = the UPKEEP-SYNCH PHASE CODE.** 4 writes and 2 tests in the whole image. `= 1` at the loop entry
  (0x5210aa, right after 0x744f24 / 0x91c658 / 0x91c630 are zeroed), `= 2` after the message at 0x521297 (0x68ea94 =
  **"Skipping upkeep synch"**), back to `esi`=0 at 0x5213c7 after the second (0x68eacc = the same string) with the
  counter `0x91c630` incremented, and `= setne al` (0/1) at 0x57f8c5. **Both readers are `cmp ...,0x1`**: 0x5aaa6f (in
  FUN_005aaa20, after the "Earning a Tech" print) and **0x5aafe4 inside FUN_005aadf0** — the band-flag function, where
  `phase == 1` OR `[fab+0x94d7fc] < 0` skips the tail. So the reason that tail is skipped during upkeep synch is now
  named, not inferred.
- **M125 ds:0x920434 = the ID the window-reset entry publishes, NOT a faction field.** 15 writes, 619 reads, and **12 of
  the 15 writes sit inside a reset sequence** (`mov ecx,0x91db70; call 0x4e25e0` clears the widget object, preceded by
  `[0x91f738]=0xff`, `[0x91f6e0]=esi`, `rep stos`, `call 0x581280`); the stored value is the caller's id (esi/ebx/edi)
  or a constant; **0 references use a faction-scaled base**; the readers compare it against ids (0x546887:
  `if ([eax+0x94d448] & 0x8000000) && (0x920434 != ebx) && ([esi*4+0x92044c] & 2)`).
- **M126 0x59f0c7 = the INVALIDATION of the memoized advance threshold.** `mov [ebx+0x94d800],-1` inside FUN_0059ec90,
  immediately after `[ebx+0x94d650] += [eax+0x927a78]+ecx+ds:0x985afc` and `[ebx+0x94d654] = 0`. Its 3 call sites are
  0x5a0b39 (FUN_005a0aa0), 0x5a123e and 0x5a1277 (FUN_005a0fa0); the first zeroes the DIVISOR `[edx*4+0x94e488]` just
  before the call — so the memo dies exactly when a faction's base count changes.
Method law added to the skill: a small state code is named by the STRINGS printed around its writers.

## Session 171 (cont. 19) — M127-M129 (all PASS): the plan byte's 369 readers, the seek pair in code, the three-condition consume

`python3 scripts/m127_m129_fields.py` — SUMMARY M127=PASS M128=PASS M129=PASS (evidence/m127_m129.log).

- **M127 — the open item "zero sites read plan byte `+42`" is RETRACTED: 369 sites read it.** The type-record PLAN byte
  is `0x98adb2` (= `0x98ad88 + type*52 + 42`) and it has **369 references**, of which **149 are the folded
  `[reg*4+0x98adb2]` form** (reg holds `tid*13`, so *4 = tid*52, the record stride) and **0 use a literal `+0x2a]`**.
  M67's earlier search grepped the literal displacement and therefore could not see any of them; the live-verified
  plan-descending order now has static readers behind it (top: FUN_00502cd0 48, FUN_0055f650 33, FUN_004f6030 24,
  FUN_0055c920 23, FUN_00585720 17, FUN_00556690 15, FUN_00595b10 14).
- **M128 — the "cursor read before the seek is the PREVIOUS cursor" trap is in the CODE.** `mov ecx,[eax+0xa774]` at
  0x497707 is pushed BEFORE `call 0x4026b0` (the seek, 0x497717); the object is then re-derived
  (`mov ecx,[ebp-0x10]; add ecx,0xa780`) at 0x49771c/0x49771f and `call 0x495480` + `and eax,0x20` (0x49772a) test the
  first flag bit of the POST-seek query. So 0x497704 shows the old node and 0x49771c is the first instruction that sees
  the new one — the rule is structural, not a log artefact.
- **M129 — FUN_00546800's guard is one unit with a CONSUME.** It proceeds only when the faction dword at `0x94d448` has
  bit `0x8000000`, `ds:0x920434 != ebx`, AND the per-record byte `0x92044c` has bit `0x2` — then it **zeroes** that
  byte at 0x5469d3. So `0x92044c` bit 1 is a consumed marker for this path (which is why it reads 0 in the saves and
  after a pass), not persistent state.
Search-shape law added to the skill (second occurrence after the M116 stride): a literal-displacement grep misses the
folded `[reg*4+disp]` encoding; count BOTH forms before saying "no site reads X".

## Session 171 (cont. 20) — M130-M132 (all PASS): chooser case 7 found and named, the 24-byte gap is not a layout, 0x92077c is a mode code

`python3 scripts/m130_m132_chooser.py` — SUMMARY M130=PASS M131=PASS M132=PASS (evidence/m130_m132.log).

- **M130 — "chooser case 7" now has a definition and an answer.** The dispatch is in **FUN_00546800** at 0x54eaeb-0x54eafc:
  `call 0x542ea0` -> `cmp eax,0x7` -> `ja 0x54ec82` -> `jmp DWORD PTR [eax*4+0x54ef34]`. The 8-entry table at
  **0x54ef34** is `[0x54ed3f, 0x54eb03, 0x54eb03, 0x54eb29, 0x54ec34, 0x54ec40, 0x54ec4c, 0x54ec58]`: cases 1 and 2 share
  0x54eb03, case 3 is 0x54eb29, cases 4/5/6 are 0x54ec34/40/4c, and **case 7 = 0x54ec58** — the only case that writes a
  state PAIR: `ds:0x920700 = 0xc` and `ds:0x92077c = 1`. (My earlier scan missed it because it looked for a switch in
  0x5a6xxx-0x5aaxxx; the dispatch is keyed on the return of FUN_00542ea0, not on a chooser-internal enum.)
- **M131 — the 24-byte gap between 0x920434 and 0x92044c is NOT a record layout.** 0x92044c: 24 refs, **24 folded**
  (`[reg*4+0x92044c]`, reg = tid*13 -> tid*52). 0x920434: 634 refs, **0 folded** — a standalone global (M125's
  reset-published id). Treating 0x920434 as the `+0` field of that record would have fabricated a layout out of two
  neighbouring addresses; the M127 law caught it in one command.
- **M132 — ds:0x92077c is a MODE CODE with a small domain.** 4 writes (two of them the constant 1, one `ebx`, one `eax`),
  9 tests against **1, 3, 7**, plus a copy compared to **6** at the dispatch (0x54eb1b, right after the case-1/2 body).
  Its partner `ds:0x920700` has 8 writes and is set in the same case-7 body, so the two form a (state, mode) pair.
  Meaning NOT named: no string constant sits within 8 instructions of any write — recorded as a bounded unknown.

## Session 171 (cont. 21) — M133-M142, ten censuses, all PASS (`scripts/m133_m142_census.py`)

SUMMARY M133=PASS ... M142=PASS (evidence/m133_m142.log). Highlights with numbers:

- **M133** FUN_00542ea0 (1456 B, 341 insns, 28 callees) is the chooser's dispatch key; its ONLY call site is 0x54eaeb.
- **M137** its index arithmetic at 0x542ed9-0x542eed folds to **359 dwords = 1436 BYTES**: `lea [esi+esi*4]` (5v) ->
  `lea [eax+eax*8]` (45v) -> `shl 3` (360v) -> `sub esi` (359v) -> `shl 2` (1436) -> `mov ecx,[eax+0x927590]`.
  **1436 is exactly M104's record-block stride** (0x927a9c+fac*1436) — same per-faction record family, base 0x50c lower.
  The decompiler's `param_1*0x167` is an ELEMENT index, not a byte stride.
- **M134** ds:0x920700 = UI state code: 31 refs / 8 writes, tested vs 6, 8, 0xd, set to 0xc by chooser case 7.
- **M135** ds:0x94d7fc (per-faction) = counter with **-1 = unset** (8 writes incl. 0xffffffff); its `jl` at 0x5aafd8 is
  the OTHER half of the band-flag skip that M124 named.
- **M136** ds:0x927a78: exactly 2 refs, both inside FUN_0059ec90 -> an input of the advance-budget routine (bounded).
- **M138** 0x94d650 / 0x94d654 = accumulator + per-step companion (261/34 vs 13/2 refs/writes).
- **M139** ds:0x91c630 = upkeep-synch counter (27 of 34 refs in FUN_00521070; incremented at 0x5213c6 after the second
  "Skipping upkeep synch").
- **M140** ds:0x985afc = read-dominant (336 refs / 5 writes) -> run state, NOT a counter; meaning unnamed.
- **M141** FUN_00495480 (21 insns) = cached-flag getter with a null guard -> the `and eax,0x20` at 0x49772a tests a
  cached field's bit; 0 means "no cache object", not "flag clear".
- **M142** FUN_004026b0 (201 B, `ret 4`) = the LIST SEEK: rejects index >= [obj+0x10], walks nodes via [node+0xc] /
  [node+0x10], stores the cursor at **[obj+0x14]** — the mechanism behind M128's pre/post-seek pair.
Law added: a decompiler's `arr[i*N]` is an ELEMENT index; multiply by the element width before calling it a stride.

## Session 171 (cont. 22) — M143-M162: the faction-block field atlas (20 rows, one reproducible rule)

`python3 scripts/m143_m162_atlas.py` -> `docs/field-atlas-faction.md` (3,687 B) + `evidence/m143_m162_atlas.log`,
SUMMARY PASS. Selection rule is mechanical, not cherry-picked: count every `+0x94dXXX` displacement in the objdump
(**150 distinct**), take the 20 with the most references, and record per row: refs, writes, shape, constants written,
values tested, top containing functions, and whether the address text appears in NAMED/archives.

Top of the atlas: **0x94d448 653 refs / 27 writes / 139 functions** (the faction flag word M129's bit 0x8000000 lives in),
0x94d650 261/34 (the M138 accumulator), **0x94d434 196 refs but only ONE write** (a nearly-const field — 196 readers of a
value the game sets once), 0x94d430 168/18 (the band-flag word), 0x94dc84 89, 0x94d80c 78, 0x94d468 75, 0x94d438 72,
0x94d78c 72 (M123), 0x94d81c 62, 0x94d554 57, 0x94d734 57, 0x94d758 51 (12 writes, one const 5), 0x94d488 49/22,
0x94d7fc 47 (M135), 0x94d818 46, 0x94d754 44, 0x94d814 42, 0x94d4e8 40, 0x94d4a8 38/26.
Honesty note baked into the artefact: these are SHAPE entries, not meanings — the table's own legend says a `—` in
`in NAMED?` means genuinely unnamed, not a gap to fill by guessing. Six of the 20 (0x94d434, 0x94d80c, 0x94d468,
0x94d81c, 0x94d554, 0x94d734, 0x94d754, 0x94d814, 0x94d4e8, 0x94d4a8) are new to the registry as addresses.

## Session 171 (cont. 23) — archive pass + M163-M165 (all PASS): the once-written rank and two contiguous structs

Footing hygiene first: the s171 pick lines moved verbatim to `docs/pick-archive.md`, so `NEXT_PROMPT.md` is an index
again (was 15,041/15,500 = 459 B free; now 13321 B). Then three structural answers from the atlas's oddest rows
(`scripts/m163_m165_structs.py`, SUMMARY M163=PASS M164=PASS M165=PASS):

- **M163 — 0x94d434 is a per-faction RANK, written exactly once.** The single writer at 0x59ac8a sits in an
  initialisation loop (0x59ac4b-0x59ac94) inside FUN_0059aa00: it scans the 7-dword table 0x926a7c-0x926a98 for the
  largest entry, stores **-1** in the winner's slot (0x926a78+n*4), then writes `[faction*8380+0x94d434] = ebx` and
  **decrements ebx** while looping. 196 readers, 1 writer, tests against 2/4/5/6 — that is a rank, not a counter.
- **M164 — 0x94d80c/10/14/18/1c is ONE 20-byte struct.** **11** (function, base-register) pairs address all five
  displacements off a SINGLE base (FUN_0040b960, 004dc100, 004e78e0, 004f6030, 00522b70, 0055a940, 00574370 x2,
  0059ec90 x2), and every member has >30 refs. Five separate fields would have to explain why 11 call sites address
  them off one register in sequence.
- **M165 — 0x94d554+0x94d55c is an 8-byte pair** (5 (fn,base) pairs, most in FUN_00546800 with three different bases),
  while **0x94d488 is separate** (17 base-pairs, shares a base with 0x94d55c in only one function) — so the atlas's
  neighbouring ref counts are not a layout.

## Session 171 (cont. 24) — M166-M168 (all PASS): what the rank is, how the struct splits, and a derived cache

`python3 scripts/m166_m168_roles.py` — SUMMARY M166=PASS M167=PASS M168=PASS.

- **M166 — the rank is consumed as an ORDERING TEST.** 0x94d434: 196 refs of which **92 are `cmp`**, against small
  constants **2/4/5/6/7**; the ranking INPUT is the 7-entry dword table at **0x926a7c**, read by only two functions (the
  init loop in FUN_0059aa00 and FUN_00531df0 at 0x532150), and the top entry is EXCLUDED by the single `-1` store at
  0x59ac72 into `0x926a78+n*4`. So the shape is: an order among 7 candidates, one discarded, the result compared
  against small thresholds. **What is being ranked stays unnamed** — recorded as bounded.
- **M167 — the 20-byte struct SPLITS into a header + a payload quad.** All five members have exactly 6 writes, but the
  WRITER SETS differ: `+0x00` is written by FUN_004dc100 (x3) and FUN_0059ec90 (x3) with constants 0/1/0xffffffff and
  carries 7 tests, while `+0x04/+0x08/+0x0c/+0x10` share the SAME five writers (FUN_004dc100, FUN_00510230,
  FUN_00512b40, FUN_00516b80, FUN_0059ec90 x2). Uniformity would have shown one writer set for all five; it does not.
- **M168 — 0x94d488 is a DERIVED/CACHED value, not state.** 22 writes spread over **9 functions** against 49 refs and a
  single comparison. That is the write-dominant profile (cf. base+0xd0 credit, M97): many paths recompute it, so a test
  that treats it as authoritative state is reading whichever path ran last.

## Session 171 (cont. 25) — M169-M171 (all PASS): the totalled table, the aggregator, and a bit-decoder dressed as a struct

`python3 scripts/m169_m171_aggregate.py` — SUMMARY M169=PASS M170=PASS M171=PASS.

- **M169 — 0x926a7c is TOTALLED, not flagged.** Its second reader (FUN_00531df0, 0x532150) runs inside a per-faction
  loop that walks the blocks at stride **0x20bc (8,380)** while stepping the table index by 4, doing
  `ds:0x9204ac++` and `ds:0x9204c4 += [eax+0x926a7c]` — a COUNT and a SUM. So the array M163 ranks is a per-faction
  quantity being totalled across factions.
- **M170 — FUN_00531df0 is the per-faction AGGREGATOR** (6459 B, 1905 insns, 17 call sites): it builds a `1<<faction`
  mask (`shl edi,cl`), gates on **`cmp [ebx+0x94d434],0x5`** — the M163 rank used as a `< 5` threshold, exactly what its
  92 comparisons predicted — and accumulates the count/sum above (plus 0x920720 / 0x9204c8 counters).
- **M171 — FUN_004dc100 is a BIT-DECODER, not a copier.** One byte arrives in AL and the "20-byte struct" is filled as
  **four BOOLEAN dwords**: `[esi+0x94d810/14/18/1c] = setne(al & 1/2/4/8)` (four `setne dl`), the header
  `[esi+0x94d80c]` gets the TRISTATE 1 / -1 / 0 from the `al & 0x10` / `al & 0x20` tests, and `al & 0x40` triggers
  `or [esi+0x94d430],0x800000`. M164's "header + payload quad" is the decoded shape of ONE SOURCE BYTE's bits.

## Session 172 (cont. 26) — M172-M174 (all PASS): the "bit-decoder" is a SAVE-SECTION WRITER, and the aggregator's counters have three consumers

`python3 scripts/m172_m174_savewriter.py` — SUMMARY M172=PASS M173=PASS M174=PASS (evidence/m172_m174.log).

- **M172 — FUN_004dc100 is a save-section writer, and M171's "source byte arrives from a caller" is RETRACTED.** Its 2
  call sites (0x51500f in FUN_00512b40, 0x517eb6 in FUN_00516b80) are argument-free dispatch legs (`mov ecx,esi` /
  `lea ecx,[esi-0x23d94]`, zero pushes before the call). The byte is the SHARED scratch global **ds:0x99aa38** (74 refs,
  33 stores; 19 stores in the 0x41a9xx UI-build block FUN_0041a8f0). The function runs BOTH directions: the PACK leg
  (0x4dc1a4-0x4dc279) loads `eax,ds:0x99aa38`, rewrites 22 `or/and al,ah` bits from the struct + `[esi+0x94d430]` flags
  + `[esi+0x94f4b0]` bit 0x20, stores it back and calls the tagged record writer 0x6267a5; the DECODE leg (0x4dc29c on,
  gated on the write's `jl` exit) reloads the SAME global and re-materialises the 4 boolean dwords + tristate + band
  bits. The context opener 0x4d9fb0 is called by EXACTLY 4 writers (0x4dc100, 0x4dc390, 0x4e0260, 0x5a2930); 0x6267a5
  has 18 sites, 12 inside the 0x4d9xxx-0x4e1xxx save band.
- **M173 — the count/sum pair has 3 + 1 consumers.** 0x9204ac: 6 refs = 2 stores (zero 0x532084, RMW 0x53214a) + 1 loop
  load + 3 consumer sites: 0x53346c INSIDE FUN_00531df0 (`count < 2`, then `table[ebx] >= 3*(sum + table[ecx])`, then
  `rank < 6`), 0x53a9cc in FUN_0053a9c0 (`count + ds:0x920720` -> local total), 0x54d30d in FUN_00546800 (`count != 0`).
  0x9204c4: 4 refs, its only consumer is 0x533478 in the same gate.
- **M174 — the tristate header is a SIGNED MODIFIER.** 7 test sites in 4 functions: 2 `cmp vs 0` (0x4a642f/0x4a6450,
  FUN_004a5eb0), 4 `cmp vs 1` (0x55ee48 FUN_0055ec10; 0x576891/0x576bd8/0x576e45 FUN_00574370), 1 `cmp [eax+0x94d80c],ecx`
  (0x5520cd FUN_00551e50) — plus 7 ARITHMETIC reads: `sub reg,[hdr]` x6 (FUN_0053cb20 x2, FUN_00546800 x2, FUN_005551e0,
  FUN_0055f650) + `add ebx,[hdr]` (FUN_005551e0); the aggregator reads it as |value| (0x53206f + neg/jge into [ebp-0x20]).
