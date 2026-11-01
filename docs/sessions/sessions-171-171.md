# Session notes archive — sessions 171-171

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

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
