# NEXT_PROMPT — SMAC RE, session 57

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

## First actions
1. `skill_view('smac-cvr-format')` — harness pitfalls + code atlas.
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — M53b (session 56) is the latest milestone.
3. Live state (kit below): game up (`pgrep -x terran.exe` → 2124624), year 2371, our turn (`cur == 3`),
   n_bases 75, our base idx **70 @ 0x962d30** (head `+0x50` = 3 Transport Foil, `+0x4c` = 0, storage 0),
   `pgrep -x gdb` empty. M53e needs no poke: the QUEUE rows are on the base screen.

## Footing — production economy + the production UI (M48d → M53b, VERIFIED unless marked)

### M53b (session 56): type-record `+41` is a COST FACTOR (1 unit = 10 minerals at 100 %)
Full write-up `evidence/m53b_findings.md`; dump `evidence/m53b_types.tsv`; digest
`evidence/m53b_costcalc_digest.txt`.
- **Single writer:** `shard_015.c:9358` `(&DAT_0098adb1)[type·0x34] = FUN_00595820(chassis, weapon, armor,
  ability, reactor)` inside `FUN_00595b10 @ 0x595b10` (builder, header `:9273`); both Ghidra store
  renderings grepped over 42 shards, every other hit is a read. `FUN_00595820` (`shard_015.c:9124`-`:9258`)
  sums the chassis `+4` / weapon `+3` / armor `+0xa` **cost** fields with triad, reactor (type `+39`) and
  ability-table (`0x98aaf4`, 25 groups × 28 B) adjustments; formula + table layouts in
  `evidence/m53b_findings.md` §2-3.
- **`scripts/m53b_costcalc.py` reproduces 180/188 populated rows.** The only `ability == 0` mismatches are
  the 3 shipped `#UNITS` rows with an explicit non-zero Cost (Mind Worms 5, Isle 8, Locusts 10) ⇒ **explicit
  alpha Cost beats autocalc** (override site unlocated).
- **Price = `FUN_004e40a0(owner,1,−1) × +41`** — the same product at affordability `shard_012.c:20722`, the
  SPENDA debit `shard_012.c:20866`, the pane `shard_001.c:4705-4708`, the printed `__itoa(mult × +41)`
  `shard_014.c:19723-19725`. `FUN_004e40a0` (`shard_012.c:13798`, NAMED.md) = mask owner ⇒ 10, difficulty
  `0x92a290`/`0x92a294`, `0x92ada8`, `switch(faction+0x1c government)`. **Live 10/10/2, mask `&0xff` 0x08,
  government 0 ⇒ 10 = 100 %** ⇒ `+41 = 1` = 10 minerals = M52b's measured debit
  (`evidence/m52b_watch.log:391-392`). Rules tables are NOT pre-scaled (`0x984d48 + item·0x30` int0 ==
  alpha `Maint`).
- **`+43` (`0x98adb3`) = auto-calculated AI role** (ladder `shard_015.c:9366`-`:9441`): noncombat packages
  get `weapon mode + 0x20` (`:9431`) → live 39/40/41/42/43/44 (Transport Foil/Colony Pod/Formers/Supply
  Crawler/Probe Team/Artifact); combat 1…10 (Mind Worms 1, Isle 6 sea, Locusts + Chopper 9 air ∧
  `ability&0x20`, Scout Patrol + Unity Rover 10 via `attack==1 ∧ armor==1`). `+42` = the alpha **Plan**,
  14/14 shipped rows (ladder explains 10; override INFERRED). **`+41` ≠ `+43`:** Scout Patrol 1 vs 10,
  Colony Pod 3 vs 40, Transport Foil 3 vs 39; equal in only 21/193 rows. Turns come from `FUN_005ac8c0`
  (`shard_015.c:23672`, triad rates `0x92a2d0/d4/d8`), never `+41`.

### M53d (session 55): the pending-queue writer is `FUN_00417d20` (register-indexed!)
- **`FUN_00417d20`** (302 B, `shard_001.c:8833`, disasm `evidence/m53d_fn417d20_disasm.txt`): `ecx` =
  base-pane UI object, `edi = [ecx+0x3ff5c]` = **UI slot index**, `[ebp+0x8]` = item id, `[ebp+0xc]` =
  insert-vs-replace. **0x417e04 `mov [eax+edx*4+0x50], ebx`** = `queue[ui_slot]` (slot 1 → +0x54 … 9 →
  +0x74); 0x417dd8 insert-shift (k = 9 → slot+1, only when param_2 ≠ 0); 0x417dad delete-shift; `+0x4c`
  cap-9 store 0x417df6, `count+1` 0x417e1d; slot 0/9 early-return (the head is never edited here). Only
  caller 0x417ee0. **Every queue writer is REGISTER-indexed** — grep store SHAPES (`*4+0x50`, `+eax*1]`,
  `rep movs`), not literal offsets (same trick found M53b's single `+41` writer).
- **`FUN_00417ee0(slot, …)`: param_1 IS the slot index** (row 1 → `param1=1 param2=1`). Chooser =
  `call 0x496ad0` at 0x41860a (`evidence/m53d_fn417ee0_disasm.txt:425`) → item id or −9999 (0x41861b).
  Dispatch on `[pane+0xb194]` via table **0x419c04** (`evidence/m53d_jumptable.txt`): 1→0x418c51,
  2→0x418cc9, 3→0x418cd8, 4→0x418703, 5→0x4187a2, 6→0x418703, 7→0x4187ad. **Mode 5 pushes 1 / mode 7
  pushes 0** → 0x4187b6-0x4187b9 `push item; mov ecx,pane; call 0x417d20` (`:550`) = INSERT-with-shift /
  REPLACE in place. **Mode 4/6 → 0x418703**: `slot ≤ [base+0x4c]` ⇒ shift `queue[k] := queue[k+1]`
  (0x41874d-0x418751) + `+0x4c--` (0x418766) = REMOVE, else clamp the slot field + redraw (0x41873a).
  Modes 1/2/3 → 0x418cda → `0x43f470(0x71df20, owner)` → `jmp 0x4184d7` re-open. **Mode 0 skips the
  table** → 0x4187ef → 0x418819 tail, **writes nothing**; head store 0x418b57 (+0x50) only on the
  `param_1 == 0` path.
- **VERIFIED live** (idx 70, window 10485761, hw-watchpoints 0x962d84/+0x54, 0x962d88/+0x58, ~20 bps): row
  1 → chooser → Scout Patrol (icon 128,160, id 2) → bar x=390 → `MODE mode=7 slotfield=1`,
  `D20_STORE dst_off=0x54 old=3 new=2`, **`W54#1 pc=0x417e08 val_after=2`** (`$pc` PAST the store),
  `/proc/mem` `+0x54 3→2`, `+0x4c 0→1` (`evidence/m53d7_watch.log:47-51`, `m53d5_watch.log:48-51`).
  **Cancel-restore is the 2nd writer (the "phantom refill")**: snapshot 0x41820a-0x418222, then on
  `param_1 ≠ 0` ∧ pick == −9999 0x418623-0x41863f rewrites `+0x50..0x74` from it (`W54#2 pc=0x418639`,
  `evidence/m53d7_watch.log:52-64`).
- **Bar → mode map** (window px, bar row y≈343; labels HELP|OK|REPLACE|INSERT|DELETE|CANCEL are NOT
  label-verified): 275→mode 0 nothing, **390→mode 7 append**, 505→mode 4 remove, 618→−9999 restore,
  160→mode 1 re-open (`evidence/m53d8_watch.log:47-48`), 707/Return nothing. **Digit keys 1-9 are
  preview-only** (`FUN_00512b40` → `FUN_00417ee0(digit, 0)` → mode 0, `evidence/m53d3_watch.log:42-44`).
- **UI geometry** (800×600): QUEUE rows 1-8 x≈185, y = 437 + 14·(row−1); CHANGE ≈(185,552), HURRY ≈(185,571);
  chooser overlay x 60-740 y 8-330, 5×3 grid (cols ≈128/255/383/510/638, icon rows y≈60/160/260), bar row
  y≈343.

### M53c (session 54): the dequeue
- **+0x4c = PENDING-entry COUNT**; entries = `+0x4c + 1`, head at +0x50, pending from +0x54, UI cap 9 ⇒ 10
  dwords `+0x50..0x73`. **THE POP = `FUN_004ef5d0(base_idx)`** (244 B,
  `evidence/m53c_fn4ef5d0_disasm.txt`): 0 if `+0x4c == 0`; `dec BYTE [0x94de84 + owner·0x20bc + head]`;
  shift `slot[i-1] := slot[i]` (0x4ef628-0x4ef639); `+0x4c--` (0x4ef642); re-validates the new head and
  re-pops if unavailable; head ≤ −39 ⇒ `0x446250(0x24)`. Callers 0x4ef992 / **0x4f037b** / 0x4f0f46, all
  inside `FUN_004ef6d0`.
- **Pop vs re-pick fork** (0x4f033e-0x4f037b): `+0x30 |= 0x800000`, `&= 0x7fffffff`, `test (1<<owner),
  [0x985b10]` → in mask ⇒ POP at 0x4f037b else `jmp 0x4f0589 FUN_004e5ae0` (owner 3 ∈ 0xff08). Live
  `WP50 eip=0x4ef62e 2→3`, `WP4C eip=0x4ef648 1→0` (`evidence/m53c_watch.log:144-147, :161`); the six
  re-pick sites + tail clear: **0 hits**.
- With `+0x4c == 0` NOTHING consumes the head ⇒ a payable head re-completes EVERY round (the standing item
  IS the repeat-build state). `FUN_004e5560` (`shard_012.c:14625`) is the only +0x50 setter, reached only
  from `FUN_004e5ae0` (30 KB AI planner, `shard_012.c:24338`): 122 re-picks on 40+ bases, 0 ours; new heads
  are facility ids plus **−29 ×7**.

### M53a / M52b / M52a (sessions 51-53) — with M53b's correction
- `+0x44` = active-item mirror (`0x4f5a70` copies `+0x50 → +0x44`, snapshots `[base+0x98] := storage`,
  `shard_012.c:24184-85`). Queue encoding (`evidence/m53a_qgate_disasm.txt:5-55`): `−38` = empty, `≥ 0` =
  item id (unit `< 0x40`, facility `≥ 0x40`), `< 0` = secret project `|q| = 39 + idx`. **Completion is
  PAYMENT-DRIVEN, no progress counter**: COMPLET 0x4efe41 fires the instant
  `storage ≥ factor × 0x5ac950(id, idx, 0)`; PROGDIV 0x4efd49 only formats an ETA. Dispatch: unit →
  SPENDA; facility → set bit 2 of word `[0x98adb8 + 52·id]`; cls-8 Colony Pod ∧ pop==1 → ABANDONBASE.
- SPENDA `edi` = `0x4e40a0(owner,1,−1) × 0x5ac950(id, idx, 0)` = 10 for our queued Scout Patrol
  (`m52b_watch.log:391-392`) = 100 % × cost-factor 1. `0x5ac950` (`shard_015.c:23696`, reads `+41` at
  `:23707`) is the type **cost** accessor — not the "production weight" M52b called it (NAMED.md
  corrected); for `type ≥ 0x40` it adds `FUN_00595ad0(type) × triad_rate / 100`, zeroed when
  `(&DAT_0095da9c)[base + idx·0x130] & (byte)type`. +0x40 writers = SPENDA 0x4efee0 + CLAMP1 0x4eff23,
  clamp `= max(0, min(base+0xd0, cap 0x92a370=10))`.

### Standing (do not re-derive)
- Storage writers: IADD 0x4ef7f6, SPENDA 0x4efee0, CLAMP1 0x4eff20/23, CONVST 0x4f2d7d (our base always
  early-returns in `0x4f26e0`). **The sweep never truncates** (M50b): `0x520540` reloads n_bases per
  iteration, the year store 0x51f554 fires between passes, the base array SLIDES ⇒ locate by NAME.
- Base record: x u16@0, y u16@2, owner@4, pop@6, f18/f1c/f20/f28/f30 flags, +0x3c progress, minerals@0x40,
  44 item mirror, **4c pending count (cap 9)**, **queue @0x50..0x73**, 8a/8c facility bitmap, 98 storage
  snapshot, c0 (== pop, open), cc (−3 for us), d0, fc, f38 = 0x00dfbe41.
- Type record `0x98ad88 + type·52` (193 populated rows; ids 0-13 = the 14 alpha `#UNITS` rows, 14-63 empty,
  64+ = designed chassis×weapon×armor types built by `FUN_00573a90 @ 0x573a90`, which stores the requested
  role into `+43` at `:17802`): name +0[34], ability int +32, **+36 chassis, +37 weapon, +38 armor,
  +39 reactor**, **+0x29 (41) cost factor**, +0x2a (42) Plan, +0x2b (43) auto role, +0x30 word flags
  (`&4` gates the `0x5ac950` bump). Sample rows + the full 193-row dump: `evidence/m53b_types.tsv`. Upkeep
  `0x984d44/0x984d48 + item·48` (int0 == alpha `Maint`, int1 = tech id); secret-project costs
  `(&DAT_00984d44)[idx·0xc]` (`FUN_004f26e0`); per-player item counts are BYTES at
  `0x94de84 + player·0x20bc + item`.
- Globals: year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap 0x92a370
  (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array 0x95da10 stride 0x130, unit array
  0x933278 stride 52, faction records stride 0x20bc, HUD income 0x745734/0x744f28/0x7457dc, difficulty
  cost 0x92a290/0x92a294 (10/10), 0x92ada8 (2), triad rates 0x92a2d0/d4/d8.
- Pane object fields **+0x3ff5c = selected queue slot**, **+0xb194 = chooser mode**; `FUN_00416080(this)` =
  redraw; `FUN_00496ad0(pane+0xa1c, base, owner_byte, scratch)` = modal item chooser (3,310 B,
  `evidence/m53d_fn496ad0_disasm.txt`).

## Static-reading kit
- Clean 32-bit disasm, no attach: `gdb -batch -nx -q -ex "set architecture i386" -ex "set
  disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` → `evidence/`, grep it, never
  paste a whole function; line 1 is an arch banner; **coverage-check** (`index.csv` size ÷ 3.8 ≈ insn count,
  last address == next function start). Existing dumps: `ls evidence/*disasm*`.
- Pseudocode `scripts/fn.py 0xADDR`; corpus `grep -rn <pat> ghidra_out/shard_*.c` then
  `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`. **Grep store SHAPES, not offsets**, and
  grep BOTH Ghidra renderings (`(&DAT_…)[…] =` and `*(… + 0x98…`) — a single-writer claim needs both.
- **Alpha comment headers name the columns** of sections whose rows are bare data (`programs/alpha.txt`
  `:348 #CHASSIS`, `:387 #WEAPONS`, `:422 #DEFENSES`, `:560 #UNITS`, `#FACILITIES`; full list in
  `ALPHA_RULES.md`); `scripts/parse_alpha.py` → `data/alpha.json`. Templates for cross-checking a runtime
  table against its alpha section: `scripts/m53b_types.py`, `scripts/m53b_costcalc.py`.
- Live `/proc/<pid>/mem` pread (TracerPid 0): read `0x8f0d60`, walk `0x95da10 + i*0x130` for
  `i < *(0x985af4)`, pull fields, recompute, then arm gdb.

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (now 10485761, 800×600);
  launch-if-down command is verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0 (resets
  on reboot). Read-only state: `scripts/smac_state.py --json`. Our base = idx **70** @ 0x962d30.
- **Armed UI-driving (M53d recipe)**: `python3 scripts/m53d_drive.py --tag mXX --mode arm --hold 1200`
  launched with **`background=true`** (Hermes kills children of a finished foreground call; `--hold` is
  the polling parent that keeps gdb alive), then drive with `scripts/smac_play.py`
  (`P.WIN = P.find_window()`, `P.click((x,y))`, `P.key()`, `P.freeze(tag)`), pread `/proc/<pid>/mem`
  between clicks, then `--mode stop` (SIGINTs only the pidfile'd gdb, then `kill -CONT`). The breakpoint
  set (ENQ/D20/POST_PICK/MODE/SNAP/RESTORE/TAIL/HEAD/SHIFT/CNT/QPIPE) is baked into
  `scripts/m53d_drive.py` — read the script, don't re-derive it.
- Pitfalls: the full list is in the skill. The ones that bite here: poke-then-arm (M33), `kill -CONT`
  after gdb-INT, never Escape on title/REALLYQUIT, OCR ≥4 chars, OK-bar ≥1.2 s, transient advisor panes,
  `$pc` sits PAST the store, **never signal by name** (driver argv matches), gdb breakpoint `printf` is
  block-buffered (attribute by CONTENT; read the log only after `--mode stop`), **vision pixels = window
  coords, tesseract TSV is rescaled**, short* aliasing doubles offsets (`DAT_008f0d60 + 0x28` = byte 0x50,
  but `(&DAT_0098adb1)[type·0x34]` IS byte-indexed), `*(int*)0x68cbb0` == the arg of 0x4e5ae0/0x4e5560
  while they run (compare idx 70).
## Milestone options (pick ONE)
- **M53e — finish the enqueue UI (THE PICK, dynamic, cheap).** Make **mode 5** fire so the insert-shift
  0x417dd8 is caught live: build a 2-entry queue (row 1 → bar 390, row 2 → bar 390), re-open row 1 with a
  different item and find the bar/state that sets `[pane+0xb194] = 5`; label-verify the six bars (crop-OCR
  y≈343) and reconcile the 8 visible QUEUE rows with cap 9. Say plainly if mode 5 is unreachable.
- **M53f — the loader overrides (static, cheap).** Find where the alpha `#UNITS` Cost lands in `+41` and
  the Plan in `+42` (neither renders as a `DAT_` store: grep `*(… + 0x98adb1)`, `+ 0x98adb2`, `rep movs`,
  then `FUN_00573a90` / the alpha-section dispatcher), and fix the ability bit-1 off-by-1 in
  `scripts/m53b_costcalc.py` (Scout Rover, Scout Speeder).
- **Later:** secret-project cost table `0x984d44` stride 0xc; the −29 head value; what fires at
  0x4ef992/0x4f0f46 (0 hits); `FUN_0059ce10`'s `+0x4c = pop·10/2` (over cap 9, `shard_015.c:14416`);
  M50c-e, M51b, base+0xc0.
- **Retired premises, do not resurrect:** "edi = the sweep-entry index"; "0x4e40a0 is just the
  `(1<<p)&mask` test"; "PROGDIV accumulates progress"; "base+0x50 is a single dword"; "+0x4c is the last
  used index"; "the pipeline has no +0x50 writer"; "M53a's dump is complete"; "+0x54 is written by nobody";
  "0x417ee0 writes only slot 0"; "digit keys 1-9 queue an item"; "the queue refills itself from the head";
  "the chooser bar at x=503 is OK"; **"`0x5ac950` returns a production WEIGHT"**; **"+41 is the mineral
  price as stored"** (price = `0x4e40a0 × +41`); **"+43 is a cost"**; **"the loader pre-scales ×10"**.

## Report style
Findings → SESSION_NOTES.md (dated section) + this file; evidence under `~/reverse/smac/evidence/`; cite
log line numbers for every claim; mark VERIFIED vs INFERRED; end with the next-prompt pointer.
