# NAMED archive: M227-M245 + B1-B2 (moved VERBATIM from NAMED.md at s254, 10 headings, 133 lines; git history is the trail)

## M227-M230 (s187, all PASS) - the +0x3098 stack-mirror; the panel tail field holds a POINTER TO a caller's block; [obj+0xb24] is a collision; FUN_00455c70 is a trampoline
`scripts/m227_m230_mirrors.py`, `evidence/m227_m230_mirrors.txt`. **M227** 0x3098 = 18 refs (8 member / 10 `[ebp-0x3098]`): FUN_0058dfd0/FUN_0058e2b0 hold a stack DIALOG at ebp-0x62c8 (0x6717cc, ctor FUN_00405ef0) whose panel subobject is [ebp-0x3098] (0x671d94) and whose hotspot LIST is [ebp-0x3230]. The 8 member takes call 0x5e7665 (clear, x5 counting the jmp) / 0x5e764f / 0x5e7678 (alloc) / 0x5e7917 (scan), never 0x5e774d or 0x403b00 -> never appended. **M228** +0x2144 = 54 refs / 24 stores (10 zero, 3 sentinel 0xffffffff, 11 register, 0 text imm); provenance frame-slot 8, .rdata 0x689f88 load 1, 0x7543d8 table-slot lea 2; callers FUN_005f86ad = 0x671d94+0x48, FUN_005f882f = +0x60, FUN_005f90d7 = +0xa8 (6 calls / 6 guards). **M229** [obj+0xb24] = 25 refs / 12 stores in 6 fns / 12 loads in 5 fns (0042d2c0, 00488e80, 004893e0, 004894c0, 00612c4c) + 1 test vs 0xffffffff; 0 read 0x774xxx; 1 indexes 0x7543d8 at stride 44; FUN_0041f450 stores 0x774c0c x4 + 0x774a80 x1; grid 0x774c38 = BSS (offset 0x374c38 > file 0x2ed000). **M230** FUN_00455c70 = 33-insn 0-store trampoline to 0x5dbdc0 x1 + 0x5e3412 x2, injecting 0x109/0x107/0x106/0x792a30 with arg1 as `this`; 15 sites (11 distinct BSS buffers, 4 registers); FUN_0045a320..FUN_0045a4a0 = 9 pair publishers (0x99aa9c+4i, 0x99aac0+4i).

## M231-M234 (s188, all PASS) - the pair staging arrays, the writer-free 0x774c38 grid, the 0x7543d8 record table, the trampoline's two callees
`scripts/m231_m234_staging.py`, `evidence/m231_m234_staging.txt` (17/17 gates, static + live reads).

**M231 the 0x99aa9c/0x99aac0 pair staging arrays** 9 publishers FUN_0045a320+0x30*i (15 insns, 2 args, 2 stores, 0 callees, 0 dereferences) publish their ARG VALUES into 0x99aa9c+4i and 0x99aac0+4i (the two slots are 0x24 apart, not adjacent). The 18 dwords [0x99aa9c,0x99aaf4) have 18 writers and their ONLY readers are FUN_0062d630 (6 direct sites) and FUN_0062d78d (0 direct sites, 0 code refs - it is slot +0x15c of vtable 0x679f98, the same slot offset the dialog family uses for its installer, M220). FUN_0062d630 is the CONSTRUCT: it installs 0x679f98 at [this+0] and 0x679f90 at [this+0x444], then both copy the 18 staging dwords verbatim into [this+0xab8..0xafc] (stride 4). Live: 3/9 pairs non-zero (i=2,4,5) and every value is a 0x774c38 grid-entry address.

**M232 the 0x774c38 grid has ZERO writers** of 39 stores naming [0x774a00,0x774e00) ZERO carry a region address in the destination and 39 in the source (FUN_0041f450 installs page bases into [ebx+0xaf0..0xb30]) - the region is written only through pointers. Its 9 entries (stride 0x2c) are handed out 24 times over 9 calls: 6 calls take a TRIPLE (0,3,6)/(1,4,7)/(2,5,8) - 3 to the 0x9978ac setters FUN_0045a530/590/5c0, 3 to the 0x99779c trio FUN_0045a680/6b0/6e0 - and 3 calls take the PAIR (e,e+6) to publishers i=2,4,5. Live every entry = {+0=0, +4=mapped data pointer, +8=9, +0xc=+0x10=+0x18=N, +0x14=+0x1c=0x14, +0x20..+0x28=0}, N=3 x6 / 0x43 x3; every staging slot reads back exactly the pointers its call passed, so the row's group data are POINTERS to grid records.

**M233 the 0x7543d8 record table** 3 writer sites image-wide: 2 folded stores of 0xd7 into +0x18/+0x1c of entry idx (idx=[ebp-0x4], `imul 0x2c`, inside FUN_00459490's loop bound 0x59 = 89 iterations) and 1 count store to 0x7543d4 (FUN_00459bb0). 0x7543d8 itself is never a destination: 13 base-takes = 2 push-as-arg (0x64bda0/0x64bc40), 5 receiver adjustors `add reg,0x7543d8` before a call (0x5dbcc4, 0x403b50 x2, 0x440c90 x2), 6 lea. 2 sites in FUN_005aa310 store `lea reg,[reg*4+0x7543d8]` into the panel's tail field [edi+0x2144] (M228's provenance; stride 4 against the 0xd7 writer's stride 0x2c - the same collision M229 found for [obj+0xb24]). Live: count 11, entries 0..15 = {+0 = 0x15064c0-0x40*i (mapped: entries point BACKWARD at 64-byte blocks), +4=0, +8=9, +0x18=+0x1c=0xd7, rest 0}.

**M234 the trampoline's callees** FUN_00455c70 gives its OWN arg1 to all three callees as `this` and injects (arg1=&0x792a30, arg2=0x109) for FUN_005dbdc0 and (0x107,0x109)/(0x106,0x109) for the two FUN_005e3412 calls. FUN_005dbdc0 (ret 0x1c = 7 args, 408 insns, 59 direct sites, 0 indirect calls) gates arg1 non-null through 0x5ca8d2, requires [ebp+0x18] and [ebp+0x1c] non-zero, returns 3 on 3 paths, reads [arg1+0x80] as the extent it compares arg3+arg5 against, allocates via 0x5be090 - a record consumer, not a formatter. FUN_005e3412 (ret 0x8, 91 insns, 0 callees of any kind, 14 sites) returns 7 when [this+4]==0, clamps both args with `and reg,0xff`, walks the [this+4] data rewriting 5 byte-matches of low(arg1) to low(arg2), length = [this+0xc]*[this+0x14]>>2 truncating (2 of 11 buffers have N*M %% 4 == 1). The 11 buffers FUN_00459bb0 passes are distinct BSS records of the same 11-dword grid shape.

## M235-M237 (s189, all PASS) — the 0x679f98 class, the record stamper, the write-only callback triple

`scripts/m235_m237_records.py` + `evidence/m235_m237_records.txt` (12/12 gates).
**M235** vtable 0x679f98 = 88 slots, +0x15c = FUN_0062d78d, next dword 0xfffffffc. EXACTLY 2 installs,
both `[reg+0]`, by TWO constructors: FUN_0062d630 (the 18-dword staging copy-in, M231) and FUN_0062d764
(41 B). Its 88 slot functions reference 0 string literals: the class is named structurally — 72 slots
implementation-identical to 0x6717cc, 71 to 0x671d94, 70 identical in all three, 15 unique (+0x0, +0x8,
+0x30, +0x40..+0x68). 87/88 have member-scale dispatchers (1920 sites; +0xf0 x301, +0x8 x282, +0x4 x252);
+0x0 none; +0x15c 28 sites. Largest member-scale call disp +0xf3c; larger call-through disps are indexed
function-pointer TABLES in .data (max +0x6a75a8), not slots.
**M236** the 9 at record +8 (grid 0x774c38, table 0x7543d8, the 11 trampoline buffers) has ONE emitter in
the image: `mov byte ptr [ecx+0x8],0x9` @0x5dbbd1 inside FUN_005dbb5f — a 33-insn, 0-call STAMPER that
zeroes +4..+0x28 and publishes the record pointer to ds:0x9965b8 (3 stores / 3 loads with FUN_005dbbe6
and FUN_005dbdc0, M234). +4 is allocated by FUN_005be090 (13 of the image's 55 "[reg+4] = eax within 8
insns of a call" sites, in 13 functions). Live: 9 grid +4 pointers = 2 clusters (6 x 0x70, 3 x 0x568),
all mapped; table entries' +0 step -0x40 (count 11) — block-strided allocations, not per-record mallocs.
**M237** the callback fields 0x2210/0x2224/0x2234 are write-only: 3 stores, 0 loads/calls/lea/add, while
their own block [0x21c0,0x2260) carries 118 sites and 80 loads (+0x21d0 x62). All 3 installs sit in ONE
installer FUN_005f3f5b (6102 B), same pointer into all three fields. No bulk copy reaches them (108
`rep movs` image-wide, 4 in 2 window functions naming only +0x21c0..+0x21d0). ds:0x9977f0 (the handle the
callback gates on): 2 stores, both absolute, both in FUN_005f1394, 7 loads, live 0x0 — no modal object,
so the triple is unverifiable from the box until a dialog is open.

## B1 (s190, PASS) — the `.MP` 22-byte cell is TWO nibbles; the file cell ↔ live 44-byte terrain-record transform is unnamed

| field / artifact | finding | conf | evidence |
|---|---|---|---|
| cell+2 high nibble | terrain type index: both shipped maps use exactly 0..15, contiguous, nothing above 15 | M — cardinality 16 ASSUMED (a nibble cannot exceed 15, so the range gate can only fail on gaps) | `evidence/b1_selftest.txt:6`, `:10` |
| cell+2 low nibble | owner player index, `0xf` = unowned; only {0..7, 0xf} ever appear, never 8..14 — the shape M43 pinned live, now seen in the file image on 22,784 cells | M→H | `evidence/b1_selftest.txt:7`, `:11` |
| cell+7 == 0xff | land marker: the count equals the header's land-cell word (word 5) exactly in both maps, 3200/3200 and 8192/8192 | H (arithmetic identity over two files) | `evidence/b1_selftest.txt:8`, `:12` |
| cell+0 | `(cat<<5) + low5`, cat ∈ 0..6, low5 ∈ {0,1,2,8,9,10,16,17,18} (two 3-valued fields, bit2 always 0); cats 1-6 are 100% land, cat 0 is 59/3259 | LEAD (printed as `info`, not graded) | `evidence/b1_selftest.txt:3-4` |
| file cell → live record | the file's cat field is NOT the live `rec[0]&0xe0` category (FOOTING.md: ocean iff <0x60, yet cats 1 and 2 are all-land). Grid 140,800 B = 3,200 live records × 0x2c, so the sizes match; the transform that repacks a 22-byte cell into the 44-byte record is unnamed | OPEN | `evidence/b1_selftest.txt:3-4` |
| `sim/map.py` `sim/rules.py` `sim/selftest.py` | R1 rung B1: an independent `.MP` decoder whose dims/cells/size/offsets match `scripts/decode_map.py` on both maps + the 45-section alpha.json loader (650 records, none empty) | H (runnable acceptance) | `evidence/b1_selftest.txt:15` |

## M240 (s191, PASS) — the `.MP` grid IS the live terrain-record array (verbatim, no repack)

| field / artifact | finding | conf | evidence |
|---|---|---|---|
| `0x582260` + `0x582000` = `map_load_arrays` / `terrain_alloc_arrays` | reads 0xaa4→`&DAT_0092a378`, `DAT_0092a38c*0x2c`→`DAT_0092ae14`, `DAT_0092ada4`→`DAT_0092ae18`; `DAT_00692184 = W/2`, count = `(W/2)*H`, no loop in either ⇒ the grid lands VERBATIM as (W/2)×H records of 0x2c, index `((W/2)*y + (x>>1))*0x2c` = two map columns per record | V | `shard_014.c:27258-27266`, `:27347-27405`; gates G1-G3 |
| record `+7` | constant 0xff in every record of both maps (11,392/11,392): B1's "land marker" and FOOTING's "+7 = owner byte" are RETRACTED. At 22-byte granularity only the even cells carry it — that is why its count equalled header word 5, which is the RECORD count `(W/2)*H`, not a land count | V | gate G4, `:10-11` |
| record `+0`, `+2` | category = bits 5-7 (`FUN_005823c0` writes `& 0x1f | p<<5`; cats 0..6 only); `+2` high nibble = terrain (`FUN_00582cc0`), low nibble = owner (`FUN_00582c80`) — the file's two nibbles ARE the live fields. cat<3 = water (`shard_001.c:3515`): 1,826/1,374 and 5,143/3,049 water/land | V (layout), M (split) | gates G4-G5 |
| record `+16..+43` | 7 dwords, all seven equal in 3,145/3,200 + 8,192/8,192 records; equal to the record's own `+8` mask in 8,191/8,192 fresh records, a strict subset in 1,100/3,200 planet records (bit 5 814×, 20 344×, 30 101×); `FUN_0051c750` walks slots 4..7 and re-sets those bits in slot 4 and `+8`. Meaning OPEN | V (census), OPEN (meaning) | INFO `:14-17`, `shard_013.c:9451-9465` |

## M242 (s193, PASS 5/5) — the save WRITE function is `FUN_00597ce0`; `FUN_00596850` is ONE codec both ways

| field / artifact | finding | conf | evidence |
|---|---|---|---|
| `0x597ce0` = `save_write_file(path)` | 363 B: `FUN_0063c610(path, ds:0x692fa0)` open (→ return 1 at 0x597dcf), `FUN_00570640(s_TERRAN ds:0x692fa4)` magic, `FUN_0064c9a0(&local_c = 0x56, 4, 1)` version, `FUN_00596850(handle, 1)` body, 4-byte timeGetTime, `FUN_0064c730` fclose; `FUN_0064d710(path)` DELETES the file on any non-zero code; returns 0 = ok | V | `fn.py 0x597ce0` (shard_015), `evidence/m242_save_write.txt` ENT/INT lines |
| `0x596850` = `save_codec(handle, mode)` | **both directions in one function**: 0x59686b stores mode → `DAT_00926a0c`; every leg is `cmp eax,ebx / je` → `call 0x64cc00` (read) else `call 0x64c9a0` (write). 30 write / **30** read sites (M243: the M242 armed list missed `0x5979f8`/`0x597a19`) + 28+28 swap siblings `0x596470`/`0x596540` gated on `DAT_00985ae8 & 0x10000000`. LIVE on a save: mode=1, header leg `dst=0x985ab8 sz=796 n=1`, 23 hits at 23 of 30 write sites, 0 at 28 read, 0 swap; the 7 dead legs and their gates: M243 block below | V | gates G3-G4, `evidence/m242_save_write.txt`, `evidence/m243_leg_gates.txt` |
| save-file prefix | file[0:8] `TERRAN\0\x1a`, file[8:12] version 0x56 (86), the 796-B `DAT_00985ab8` block VERBATIM at file offset **12** (year u16 at 0x54 = block+0x48) — corrects SAVE_FORMAT.md "796 B at offset 0" | V | gate G5, both saves |
| writer's 8 call sites | 0x521697 turn-loop autosave (after the "Writing save file" push 0x521688), 0x52221e end-turn, 0x598c73 UI Save browser (`FUN_005985e0`; prints SAVE FAILED via `FUN_00626634` when the writer returns ≠ 0), 0x59a121/0x59a166/0x59a1bc (`FUN_0059a0c0`), 0x59a372, 0x59bf46. LIVE: a UI save runs 0x598c73 exactly once | V (sites, and the UI route), M (roles of `0x59a0c0/0x59a2b0/0x59bec0`) | `evidence/m242_save_write.txt` CALLER |

## M243 (s194, PASS 4/4) — the 7 dead write legs of `FUN_00596850`, and the 3 gates that kill them

| leg | what it would write | gate (branch + guard, live value) | family | conf |
|---|---|---|---|---|
| `0x596927` / read twin `0x59692e` | 3,296 B at `0x91f750` | `0x5968b6 je 0x5969f0` on `and eax,0x10000000` (ds:0x985ae8=0x2 → swap bit CLEAR) | swap-only region; the PLAIN twin inside it is unreachable in **both** swap states = dead code | V |
| `0x596976` / `0x59697d` | 4 B at `0x92046c` | same `0x5968b6` | same | V |
| `0x5969cb` / `0x5969d2` | 192 B at `0x92fc50` | same `0x5968b6` | same | V |
| `0x596af5` / `0x596afc` | 58,848 B from the malloc'd buffer (`edi`, `call 0x5be090` at `0x596ab2` push `0xe5e0`) | `0x596a4a jl 0x596aad` on `cmp ds:0x985dbc, 3` (live 9) | version < 3 legacy path | V |
| `0x597203` / `0x59720a` | 1,664 B from `edi` | `0x597165` on `cmp eax, ebx` (eax=ds:0x985dbc=9, ebx=3 from `mov ebx,0x3` at 0x59715e) | version < 3 legacy path | V |
| `0x597384` / `0x59738b` | 48·n B from `edi` (n = `ds:0x985af0` = 72 → 3,456; malloc `call 0x5be090` at `0x59733c`) | `0x5972d1 jl 0x597335` on `cmp ds:0x985dbc, ebx` (9 vs 3); `0x597335` has exactly ONE incoming edge | version < 3 legacy path | V |
| `0x59762f` / `0x597636` | 256 B at `0x991698` | `0x5975ed je` on `test ds:0x985ae8, 0x10` (live 0x2 — bit clear) | feature bit in the same header global that holds the swap bit | V |

Dead in BOTH directions (the write sites and their read twins are the same 7 legs) ⇒ these are
state/version gates, not mode gates. Static sizes of the 7 = 67,716 B; the tail the codec does not
move is 93,159 B on a save AND on a load (`242799-149640 = 242539-149380`). Instrument:
`scripts/m243_leg_gates.py` (CFG of 0x596850-0x597a6b, live guards from `/proc/mem`, gates from
`evidence/m242_b.gdblog` + `evidence/m109c4.log`), run output `evidence/m243_leg_gates.txt`.

## B2 (s195, BUILD track) — `sim/save.py`: a .SAV loads into the state model, and the walk closes on the byte

`python3 -m sim.selftest --sav "programs/saves/auto/m242_probe_B.SAV"` -> `PASS B2: 7/7 gates`,
all 17 saves under `programs/saves` close -> `evidence/b2_save_walk.txt` (per-save table).

| field | file offset (mem) | probe_B | status |
|---|---|---|---|
| unit count | 68 (`0x985af0`) | 72 | V: 72 shape-valid 52-B records |
| base count | 72 (`0x985af4`) | 18 | V: 18 records, name at +19 |
| year u16 | 84 (`0x985b00`) | 2153 | V: == decode_save.py |
| faction mask byte | 101 (`0x985b11`) | 0xff -> 8 | V: == 8 distinct owners == 67,040/8,380 |
| count-prefix u32 | 188,299 (`0x927538`) | 176 | V: closes 17/17 saves (176/192/208) |
| map trailer | 172,208 + 91 | 91 B at 64x64, 128 B at 80x80 | V by closure; formula OPEN |
| tail | last 10,800 = 256+152+10,144+28+220 | constant | V |

CORRECTIONS: M110a's map offsets are 8 B LOW — content puts the dims at 79,372, the grid at 82,096
(1,426 land markers `cell+7==0xff` there, 0 at 82,088) and the trailer marker at 172,208. `.MP`'s
"map-header word 5 == land cells" law does NOT hold in a save (word 5 = 2,048 = (W/2)*H records).
The 93,159 B the codec does not move = 92,927 (map block, `FUN_00582260`) + 220 (reader unnamed) +
12 (magic+version, `FUN_00597ce0`) — exact on m54b_clean AND on a 242,799-B save. A 52-B record
whose +10 type >= 64 is a production-queue BAND, not a unit: its +0/+2 are NOT tile coords
(m113map rec 12 = 3076/56832), so coord checks must be type-gated.

## M244 (s196) — save tail: the region-map formula, the count-prefixed block is the base-site log

`python3 scripts/m244_save_tail.py` -> `PASS M244: 5/5 gates` (17 saves + planet.MP + planetx.MP)
-> `evidence/m244_save_tail.txt`.

| claim | evidence | status |
|---|---|---|
| the map "trailer" IS the coarse region map, length `((Rw+1)/2)*Rh`, `Rw=(W+4)/5`, `Rh=(H+4)/5` | `FUN_00582000` shard_014.c:27263-27265; planet.MP 15+2,724+140,800+128 = 143,667 and planetx.MP 15+2,724+360,448+338 = 363,525 close exactly; 91/128/338 | V |
| the count-prefixed block = 8-B records [u8 type {0 add, 1 re-own, 2 remove}, u8 faction, u16 turn (`DAT_00985afc`, file 80), u16 x, u16 y]; the u32 is a BYTE length | `FUN_0059c150` shard_015.c:13891-13908 (logs "Replay Base Info", `DAT_00927538 += 8`); applied by `FUN_0059bcb0` shard_015.c:13657-13708; shape-valid on 17/17 | V |
| replayed live (x,y,faction) == the 304-B base records' (x,y,+4); **+4 = current owner, +5 = the faction written just before it** | 17/17 saves, 0 orphan type-1/2 records; the 42 bases with +4 != +5 are exactly the type-1 moves | V |
| tail = 256 \| 152 \| 10,144 \| 20 \| 216 \| 8 \| 4 = 10,800; **no 220-B and no 28-B leg** | shard_015.c:10654/10676/10698/10720 pushes (one 0x100 gated by `(DAT_00985ae8 & 0x10)`, file 60); unique 9999-row at tail+256; `DAT_0092d4a0` dest-file k = 232,407 (/proc legmap) | V |
| the 9 rows of 24 B are read by `FUN_00596620` (6 dwords/row, `DAT_007cdecc..0x7cdeec` + `DAT_008cda4c`); who reads the final 4 B; what the region-map bytes mean | the rows and the final 4 B CLOSED at M245/M246 (below); the byte VALUES still unnamed | OPEN (part) |

RETRACTS B2's `tail 10,800 = 256+152+10,144+28+220` and its `93,159 = 92,927 + 220 + 12` split.

## M245 (s197) — the 216-B tail leg is 9 map-view objects' display state

`sudo -n python3 scripts/m245_tail_legs_census.py` -> `PASS M245: 5/5 gates` -> `evidence/m245_tail_legs.txt`

| claim | evidence | status |
|---|---|---|
| the 216 B (EOF-228..EOF-12) = the 8 pointers `DAT_007cdecc..0x7cdee8` (loop bound `< 0x7cdeec`) + the inline `&DAT_008cda4c`, each moved as 6 dwords `+0x1dd78 +0x1dd74 +0x1dd70 +0x1dd98 +0x1dd9c +0x1dda0` in that order | shard_015.c:10807-10822 + `FUN_00596620` (shard_015.c:9862-9970); 9*6*4 = 216; live `/proc` (pid 319926, TracerPid 0) == 7/17 saves' 216 B byte for byte, 10 differ | V |
| `+0x1dd78` = view slot id (rows 0..7 carry 0..7 on 17/17, the inline row carries 1); `+0x1dd74` = its active flag (`FUN_00469860` shard_008.c:5894; cleared by the codec load leg shard_015.c:10845 when `[DAT_0091c18c, DAT_0091c188]` = [800, 387] changes, plus 4 invalidators); `+0x1dd70` = bit flags tested shard_008.c:8983/9033/9076/9318; `+0x1dd98` = −6 while `DAT_0091c18c < 1000` | cited sites, 17/17 saves, live pair 387/800 | V |
| `+0x1dd9c`/`+0x1dda0` = CENTRE TILE (init W/2, H/2 shard_008.c:5895-5898; set by `FUN_004739a0` :10117-10124); the window bounds `+0x1ddcc..0x1ddc8` and origins `+0x1dda4`/`+0x1dda8` are DERIVED from it by `FUN_00469860` :5949-6017 and read by the click hit test `FUN_00422060` (shard_001.c:14164-14183) | cited assignments; Autosave 1 rows 0-1 centre (28,42) = University Base | V |
| who allocates the ~140 KB view objects (live slots 1..7 spaced `0x224b8`, slot 0 at `0x8f79e0`) | — | OPEN |

