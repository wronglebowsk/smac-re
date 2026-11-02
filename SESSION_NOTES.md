

Older sessions: `docs/sessions/sessions-186-186.md` (1 sessions). Read it only when a question reaches back before session ## Session 187.

## Session 187 (2026-11-01, M227-M230, static; box re-verified, no box milestone)

`python3 scripts/m227_m230_mirrors.py > evidence/m227_m230_mirrors.txt` -> `SUMMARY M227=PASS M228=PASS M229=PASS M230=PASS (12/12 gates)`, rc 0, 10,083 B (`evidence/m227_m230_mirrors.txt:41`). Invocation #1 11/12: the FUN_0041f450 store census filtered `startswith("mov dword ptr [") and endswith("+0xb24]")`, which misses every store whose VALUE is the last token (`mov dword ptr [ebx+0xb24],0x774c0c`); fixed to `^mov dword ptr \[[a-z]+\+0xb24\],`. No threshold or claim changed. Box RE-VERIFIED (read, not poked): `sudo -n python3 scripts/smac_preflight.py` -> PASS on all 14 invariants (terran.exe 319926 TracerPid 0, year 2153, cur_player 3, mask 0xff08, 18 bases / 72 units, University Base (28,42) pend 0 head 2, 6 ours 0 actionable): the s174e "unverified" flag is CLOSED. M181 got no trigger this fire - still a LEAD, box time owed.

- **M227** 0x3098 = 18 insns: 8 MEMBER + 10 frame slots `[ebp-0x3098]`. In FUN_0058dfd0/FUN_0058e2b0 the slots ARE the members through a stack base: each stores PANEL vtable 0x671d94 at [ebp-0x3098], DIALOG vtable 0x6717cc at [ebp-0x62c8] and calls ctor FUN_00405ef0, so base = ebp-0x62c8, +0x3230 = ebp-0x3098 (panel, M221) and +0x3098 = ebp-0x3230 (THE LIST), where each frame does `lea ecx,[ebp-0x3230]` -> `call 0x5e7665`. All 8 member takes reach {call 0x5e7665 x4, jmp 0x5e7665 x1, call 0x5e764f x1, call 0x5e7678 x1, call 0x5e7917 x1}, 0 an appender: the dialog's 10-item list is allocated, cleared, reset, scanned and NEVER appended image-wide.
- **M228** +0x2144: 54 refs, 24 stores = 10 zero + 3 sentinel 0xffffffff + 11 register, 0 with a text-range immediate; provenance {frame-slot 8, .rdata 0x689f88 table load 1, 0x7543d8 table-slot lea 2}. Exactly 3 callers, 6 `cmp ,0x0`-guarded calls: FUN_005f86ad = 0x671d94+0x48, FUN_005f882f = +0x60, FUN_005f90d7 = +0xa8 - all panel vmethods. The 3 sentinel writers load first (4/1/1): read-and-invalidate.
- **M229** [obj+0xb24]: 25 refs = 12 stores in 6 fns + 12 loads in 5 fns + 1 `cmp ,0xffffffff`. **RETRACTS M224's "9 other functions load [obj+0xb24]" -> 5** (FUN_0042d2c0, 00488e80 x5, 004893e0 x2, 004894c0 x3, 00612c4c). 0 reference 0x774xxx; 1 load indexes the 0x2c-stride table at 0x7543d8 (index*44), 10 are pushed to callees. FUN_0041f450's 5 stores = {0x774c0c:4, 0x774a80:1}; grid file offset 0x374c38 > len(terran.exe) 0x2ed000 = BSS, 99 dwords 0. 0xb24 is a COLLISION: a page address for one owner, a slot index for the loaders' owner.
- **M230** FUN_00455c70 (88 B, 33 insns, 0 stores) is a trampoline: {0x5dbdc0:1, 0x5e3412:2}, each preceded by `mov ecx,[ebp+0x8]` (arg1 = the callee's this), injecting {0x109:3, 0x107, 0x106, 0x792a30, 0x0}; 15 sites in FUN_00459bb0 pass 11 distinct BSS buffers + 4 registers, 0 inside the grid. The 0x45a320..0x45a6e0 run = 21 functions, 9 pair publishers writing (0x99aa9c+4i, +0x24), i=0..8.
OPEN: who dispatches +0x4c (box); who calls FUN_005f5a11; what the 9 grid entries hold, who writes the 0x7543d8 table and the 0x99aa9c..0x99aae0 pairs; M181's control (box).

## Session 188 (2026-11-01, M231-M234, static + read-only /proc; box untouched, M181 still a lead)

`sudo -n python3 scripts/m231_m234_staging.py > evidence/m231_m234_staging.txt` -> rc 0, **17/17 gates PASS on one invocation**, 8,862 B. Invocations 1-4 gave no verdict (instrument bugs; no threshold, floor or check changed): a format string missing its `%`; `p_["dests"]` indexing a list with a string; a read-back that assumed 0x99aa9c+4i and 0x99aac0+4i were adjacent (they are 0x24 apart) and compared the wrong dword; a push list not truncated to the callee's own cleaned arg count, so FUN_00455c70's prologue pushes read as arguments; `pend` reset only at the tracked call, so the first trampoline call inherited 2 pushes from an earlier one.

TWO CLAIMS REWRITTEN FROM THE DATA, NOT LOOSENED: (1) M232's "4 stores name the region" is 39 stores - every one carries the region address in its SOURCE (FUN_0041f450 installing page bases into [ebx+0xaf0..0xb30]) and ZERO in its DESTINATION, so the grid has NO in-image writer; (2) M231's "FUN_0062d78d is not a vtable slot" is FALSE - it is slot +0x15c of 0x679f98, the very vtable FUN_0062d630 installs.

HEADLINES (all from the command above; semantics in NAMED.md). M231: publishers 0x45a320+0x30*i = 15 insns / 2 arg-loads / 2 stores / 0 callees, publishing ARG VALUES; 18 staging dwords, 18 writers, readers ONLY FUN_0062d630 (6 sites, installs 0x679f98/[+0x444]=0x679f90) and FUN_0062d78d (0 direct sites, 0 code refs); both copy the 18 dwords to [this+0xab8..0xafc]; live 3/9 pairs non-zero, every value a grid address. M232: 24 grid pushes over 9 calls (triples (0,3,6)/(1,4,7)/(2,5,8) to 6 functions, pairs (e,e+6) to 3); live entry {0, mapped ptr, 9, N, N, 0x14, N, 0x14, 0,0,0}, N=3 x6 / 0x43 x3; staging reads back exactly the pointers passed. M233: 3 writer sites (2 folded 0xd7 at +0x18/+0x1c in FUN_00459490's 89-iteration bound-0x59 loop, idx*0x2c; 1 count store to 0x7543d4), 13 base-takes (2 push / 5 add-adjustor / 6 lea), 0 to the base, 2 FUN_005aa310 sites storing &table[4*idx] into [edi+0x2144]; live count 11, entries 0..15 {0x15064c0-0x40*i mapped, 0, 9, 0,0,0, 0xd7, 0xd7, 0,0,0}. M234: FUN_005dbdc0 (ret 0x1c, 408 insns, 59 sites, 0 indirect) gates arg1=&0x792a30 via 0x5ca8d2 and reads [arg1+0x80]; FUN_005e3412 (ret 0x8, 91 insns, 0 callees, 14 sites) clamps args with `and reg,0xff` and rewrites 5 byte-matches of low(arg1) to low(arg2) over [this+4], length [this+0xc]*[this+0x14]>>2 truncating (2/11 buffers N*M %% 4 == 1); the 11 buffers are BSS records of the same grid shape.

PITFALLS: a staging pair spread over two arrays is not contiguous - read each slot; a callee's arg vector is its own `ret imm`/4 pushes counted back from the call; box time still owed (scratch/m181/pair.py never armed).

## Session 189 (2026-11-01, M235-M237 all PASS, static + read-only /proc; box untouched, M181 still a LEAD)

- **Acceptance:** `sudo -n python3 scripts/m235_m237_records.py > evidence/m235_m237_records.txt` ->
  `SUMMARY M235/M236/M237: 12/12 gates PASS`, rc 0, 7,433 B. Invocations #1 no output (no entrypoint),
  #2 crash (a `%`-format whose argument tuple was unparenthesised), #3 5/13, #5 8/12, #6 11/12, #7
  green. Every failure was an instrument-definition bug (objdump line shape, an absolute-operand blind
  spot, pairwise-instead-of-adjacent gaps, a cluster cursor off-by-one, a whole-window census reported
  as a three-field claim); NO threshold, floor or claim direction was weakened. Two PASS lines were
  RE-WORDED before merge (0x6a75a8 is an indexed table base, not a member disp; the ds:0x9965b8 loaders
  are candidates, not the proven filler). Laws -> skill §16.
- **M235** 0x679f98 = 88 slots (last +0x15c = FUN_0062d78d, next dword 0xfffffffc); 2 installs, both
  `[reg+0]`, by the class's TWO constructors FUN_0062d630 (the 18-dword copy-in, M231) + FUN_0062d764
  (41 B); 0 string literals in the slot functions, so the class is named structurally (72 slots
  implementation-identical to 0x6717cc, 71 to 0x671d94, 70 in all three, 15 unique); 87/88 slots have
  member-scale dispatchers (1920 sites), +0x0 none, +0x15c 28.
- **M236** the +8=9 the grid records / 0x7543d8 entries / 11 trampoline buffers carry has ONE emitter in
  790,695 insns: `mov byte ptr [ecx+0x8],0x9` @0x5dbbd1 in FUN_005dbb5f (33 insns, 0 calls) — a STAMPER
  that zeroes +4..+0x28 and publishes the record pointer into ds:0x9965b8 (3 stores / 3 loads with
  FUN_005dbbe6 + FUN_005dbdc0, M234). +4 is allocated elsewhere: 55 sites store a call result at [reg+4]
  within 8 insns of that call, 25 callees, top FUN_005be090 (13 sites / 13 functions). Live (pid 319926,
  TracerPid 0): the 9 grid +4 pointers form 2 block-strided clusters (6 x step 0x70, 3 x step 0x568),
  all mapped; table entries' +0 step -0x40 (count dword 11).
- **M237** fields 0x2210/0x2224/0x2234: 3 stores, 0 loads / call-through / lea / add, while their own
  block [0x21c0,0x2260) is busy (118 sites, 80 loads, +0x21d0 x62). All 3 installs in ONE installer
  FUN_005f3f5b (6102 B), same pointer thrice. Block-copy falsifier CLOSED: 108 `rep movs` image-wide, 4
  in 2 window-touching functions (FUN_005ee350, FUN_005eede6) naming only +0x21c0..+0x21d0. The handle
  FUN_005f5a11 gates on, ds:0x9977f0: 2 stores (both ABSOLUTE, both in FUN_005f1394), 7 loads, live 0x0
  — no modal object, so the triple cannot be read back without a dialog open.
- **LEAD (command, not a gate):** `awk -F'\t' 'index($0,"call   0x41a8f0")' scratch/m574/text.txt` -> 4
  callers of the GOVOPTIONS pack block: FUN_0041e160, FUN_0049af50, FUN_004a99e0, FUN_00512020 (the last
  also calls the tagged writer 0x6267a5 at 0x512069) — the trigger list for M181's falsifier.
- **Box time still owed:** terran.exe 319926 alive, TracerPid 0; 0 driver calls this fire.

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

## Session 191 (2026-11-01, M240 static — the `.MP` grid IS the live terrain-record array)

- **Footing.** Cursor said S190 B1 merged, no harness running (`ps`: no milestone.py/gdb/smac_play), tree
  clean; `track_mode.py` → `MODE=ANALYSE last_build=B1 next_rung=B2`, so this fire analysed and took the
  first ANALYSE pick (the 22-B cell → 44-B record transform). Zero box time; M181 debt still owed.
- **Acceptance.** `python3 scripts/m240_terrain_repack.py` → `PASS M240: 6/6 gates on planet.MP,
  planetx.MP`, rc 0 → `evidence/m240_terrain_repack.txt`. Invocation 1 crashed on a shard-filename slice
  bug (`n[-6:-3]` → `n[6:9]`); invocation 2 was 5/6 because G5 demanded each setter pattern occur ≥2×
  image-wide when it legitimately occurs ONCE per accessor — rewritten as per-function presence (stricter,
  not weaker); invocation 3 green. No gate, threshold or map was removed.
- **THE FINDING — no repack exists.** `FUN_00582260` (`shard_014.c:27347`) reads 0xaa4 → `&DAT_0092a378`,
  calls `FUN_00582000`, then reads `DAT_0092a38c*0x2c` bytes into `DAT_0092ae14` and `DAT_0092ada4` into
  `DAT_0092ae18`; neither body has a loop. `FUN_00582000` sets `DAT_00692184 = W/2`,
  `DAT_0092a38c = (W/2)*H`, allocates `count*0x2c` and `((W+4)/5 + 1)/2 * ((H+4)/5)`. The file grid IS the
  record array: 3,200 / 8,192 records of 44 B at `((W/2)*y + (x>>1))*0x2c`, one record per TWO map
  columns; the "22-byte cell" is half a record and only bytes 0..21 are the tile's fields. Accounting
  closes on both maps (gate G1): 15+2724+140800+128 = 143,667 and 15+2724+360448+338 = 363,525.
- **Two RETRACTIONS.** (1) record `+7` is the constant 0xff in all 11,392 records of both maps — B1's
  "land marker" and FOOTING.md's "+7 = owner byte" were reading a constant; at 22-byte granularity only
  the even cells carry it, which is exactly why its count equalled header word 5 (gate G4). (2) B1's
  category census mixed halves: record byte 22 (third byte of the mask copy at +20) has cat 0 in 100 % of
  records, so "cat 0 = 59/3259" was 3,200 artifacts plus 59 real tiles. Real split under the live rule
  (cat<3 = water, `shard_001.c:3515-3517`): planet.MP 1,826 water / 1,374 land, planetx.MP 5,143 / 3,049.
- **NEW, measured.** record `+16..+43` = 7 dwords, all seven equal in 3,145/3,200 (planet) and 8,192/8,192
  (planetx) records; each equals the record's own `+8` mask in 8,191/8,192 fresh records, and in planet.MP
  1,100/3,200 records it is a strict SUBSET of that mask (bit 5 cleared 814×, bit 20 344×, bit 30 101×).
  Direct offsets on `DAT_0092ae14` top out at 0xe (492 refs); record-pointer offsets top out at 0x10
  (one hit: `FUN_0051c750`, `shard_013.c:9451-9465`, kelp/forest growth spawn, which walks dword slots
  4..7). Header word 5 = `(W/2)*H` = the record count, unread by the loader; the 128/338 B "trailer" is
  the coarse region map `DAT_0092ae18`, sized from the dimensions by the loader itself.
- **Open:** what the seven mask copies mean and who fills them at map GENERATION (the load path only
  reads them in); record bytes 1, 3, 4-7 and 12-15 unnamed; `decode_map.py` and `sim/map.py` still split
  the grid into 22-byte cells — their B1 gates are position parity so they stay valid, but their "cells"
  are record halves; M181 box debt  unpaid (terran.exe alive, TracerPid 0 — this fire took a static pick).

## Session 193 (2026-11-01, M242 — the save WRITE function; static first, then ONE box lifecycle; S192/M241's notes live on the open PR #180)

- **Static, zero box time** (`scripts/fn.py`, `scripts/name_global.py`, `scratch/m71/dis.py` windows on
  `ghidra_out/shard_015.c`): `FUN_00597ce0` (363 B) IS the writer — `FUN_0063c610(path, ds:0x692fa0)`
  open (return 1 at 0x597dcf), `FUN_00570640(s_TERRAN ds:0x692fa4)` magic, `FUN_0064c9a0(&local_c=0x56,
  4,1)` version, `FUN_00596850(handle, 1)` body, 4-byte timeGetTime, `FUN_0064c730` fclose, and
  `FUN_0064d710(path)` DELETES the file on any failure code. `FUN_00596850` is ONE codec both ways:
  0x59686b stores param_2 to `DAT_00926a0c`, every leg is `cmp/je` → `call 0x64cc00` (read) else
  `call 0x64c9a0` (write) — 30 write / 28 read sites, plus 28+28 swap siblings `0x596470`/`0x596540`
  gated on `DAT_00985ae8 & 0x10000000`. The writer's 8 call sites: 0x521697 (turn-loop autosave, 10
  insns after the "Writing save file" push at 0x521688), 0x52221e, 0x598c73 (UI Save browser),
  0x59a121/0x59a166/0x59a1bc, 0x59a372, 0x59bf46.
- **Acceptance** `sudo -n python3 scripts/m242_save_write.py` → `PASS M242: 5/5 gates`, rc 0, invocation
  2 (invocation 1 filled every gate then died in `tally()`: the ENCODEC line had no address token —
  fixed in 60a2afb, nothing weakened). `evidence/m242_save_write.txt` has both invocations. G1
  host-statted saves A 242,799 B mtime +11.2 s / B 242,799 B +4.5 s, each inside its own window; G2 131
  bps armed, zero insert warnings, TracerPid 0 after detach; G3 `ENT 597ce0 p=00bef174
  path16='Z:\home\n100\rev'` ×1 reached through exactly one armed site, `0x598c73`; G4 codec entry
  mode=1 swap=0, header leg `W 596883 dir=1 dst=0x985ab8 sz=796 n=1`, **23 hits at 23 of 30 write sites
  vs 0 at 28 read sites, 0 swap** (M109 measured 23 of 28 read sites on a load — the same legs are
  conditional both ways); G5 TERRAN + version 86 at file 8 + the live 796-B block verbatim at offset 12
  + year 2153 mem==file, on BOTH saves.
- **Corrections:** SAVE_FORMAT.md's "796 B at offset 0" → the block is at file offset **12** (8-byte
  `TERRAN\0\x1a` + 4-byte version 0x56 precede it), so its read-order table is also the write-order
  table. M241's premise is dead: the writer never touches 0x99aa38 — though `FUN_005985e0` does store
  +1c/+20 (advisor-text substitution) on the UI route.
- **Open:** which 7 write legs are dead and by which gate; the write-side sites OUTSIDE 0x596850 (M109:
  93,159 B of a load is issued by 105 sites outside it); `FUN_0059a0c0`/`0x59a2b0`/`0x59bec0` unnamed.
  #180 (M241) stays open, superseded by this answer. Box: one lifecycle, no relaunch, TracerPid 0.
- **Pitfall:** a census parser must give EVERY logged line an address token — mine crashed in tally()
  after the measurement was already complete, wasting an acceptance invocation.

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
