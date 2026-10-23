# NEXT_PROMPT — SMAC RE, session 58

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you actually need (pitfalls + the code area). **Do NOT `skill_view` the whole file**
   (55 KB, ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 57 (M53e) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state (kit below): game up (`pgrep -x terran.exe` → 2124624), year 2371, our turn (`cur == 3`),
   n_bases 75, our base idx **70 @ 0x962d30**, base pane UP, chooser closed, no gdb, TracerPid 0,
   `ptrace_scope` 0. Base 70: storage `+0x40 = 0`, head `+0x50 = 3` (Transport Foil),
   **`+0x4c = 2` pending — `+0x54 = 2`, `+0x58 = 2` (two Scout Patrols M53e queued; to clean them:
   row 1 → DELETE bar → OK, twice)**. M53f needs NO live work at all.

## Footing — production economy + the enqueue UI (M48d → M53e, VERIFIED unless marked)

### M53e (session 57): the enqueue chooser — full write-up `evidence/m53e_findings.md`
- The dispatch field `pane+0xb194` is **not** a pane field anything stores: a byte scan of `.text` for
  disp32 `94 b1 00 00` finds exactly ONE instruction (the read at 0x4186ec, `mov eax,[ebx+0xb194]`).
  It is the **chooser sub-object's `+0xa778`**: pane = static BSS **0x6a9480** (`m53e2_watch.log:72`),
  chooser sub-object = `pane+0xa1c` = 0x6a9e9c, and 0x6a9e9c+0xa778 = 0x6b4614 = 0x6a9480+0xb194.
  All writes are `[sub+0xa778]` inside the chooser `FUN_00496ad0`: 0x496993→1, 0x4969a5→2, 0x4969b7→3,
  0x4969da→**7**, 0x4969e9→**4**, 0x496a09→**5**, 0x496a18→6, 0x496a27/0x496a36→0, 0x496a52→**7**;
  guards `cmp [sub+0xa774],0xffffffff; jne <store>; jmp 0x496a91` at 0x496982/0x4969c9/0x4969f8.
  Kit: `scripts/m53e_drive.py --pane 0x6a9480` bakes a hw watchpoint on 0x6b4614.
- Bars, label-VERIFIED (6x crop-OCR + blue-pixel run scan, `evidence/m53e_grid_pre.txt`):
  **HELP 153-233, OK 252-311, REPLACE 364-421, INSERT 472-523, DELETE 556-636, CANCEL 659-705**, bar
  body y 336-352 (labels drawn inside the bars). Bar→mode, watchpoint-verified: **INSERT→5**
  (store 0x496a09, `$pc` 0x496a13), DELETE→4, HELP→1, entry/OK/CANCEL reset→0.
- **Mode 5 fired live** (`m53e6:77-92`, again at :125-134): INSERT with a selection → MODEWP mode=5 →
  POST_PICK edi=2 → MODE 5 → `D20_SHIFT dst_off 0x74,0x70,0x6c,0x68,0x64,0x60,0x5c,0x58` →
  `D20_STORE +0x54 3→2` → `+0x4c 0→1`; the chooser then re-opens with the slot advanced
  (`m53e6:94` PRESHOW slot=2 mode=5). Confirms M53d: mode 5 → handler 0x4187a2 pushes param_2=1 →
  `FUN_00417d20` insert-with-shift.
- **CANCEL** = `mov [sub+0xa774],-1` (0x496a43) → returns −9999 → RESTORE ×10 (0x418636) rewrites
  `+0x50..+0x74` from the stack snapshot → exits at 0x419967, **mode never consulted**.
  **OK** = selection + mode 0 → tail → writes nothing AND does not restore, so a committed edit
  survives an OK exit. **HELP** = mode 1 → opens the unit-design pane for the selected item (bars at
  y 356: RENAME 290 / OBSOLETE 399 / UPGRADE 507 / CANCEL 614); its CANCEL re-opens the chooser.
- **OPEN threads:** REPLACE never fired (5 attempts: count 0, and count 1 ∧ slot 1 with selections
  returning edi=2 / edi=0) — no mode write, hits the reject tail 0x496a91 (`BAR_IGNORED` probe,
  `m53e6:63,111`); the mode-7 stores are behind `cmp [sub+0xa774],-1` and that field (0x6b4610) is
  **not** the icon selection (live reads 5/17 while POST_PICK returned 2). Modes 2/3/6 are
  static-only. One bar click runs the bar handler twice (press + release).
- QUEUE rows 1..8 = pending slots `+0x54..+0x70` (row text y = 439 + 12·(row−1), x 143-248); the 9th
  pending slot `+0x74` has NO row (INFERRED from the shift range + the 8-row layout); the head
  `+0x50` is the LEFT panel (head 3 ↔ "TRANSPORT FOIL" ↔ `m53b_types.tsv:4`). Row click clamps
  `slot = min(row, count+1)` and zeroes `pane+0x3ff60` (`shard_001.c:2133-2140`, `:2193-2197`).

### Standing from M53b / M53d / M53c / M53a-M52b (do not re-derive)
- **M53b:** type-record `+41` (`0x98adb1`) is the COST FACTOR; one writer `shard_015.c:9358` =
  `FUN_00595820(chassis,weapon,armor,ability,reactor)` summing the alpha tables' cost fields (chassis
  `0x92ae80`/0x90 +4, weapons `0x92b950`/16 +3, armor `0x92fd10`/16 +0xa). Every price is
  `FUN_004e40a0(owner,1,−1) × +41`; live multiplier = 10 ⇒ `+41 = 1` = 10 minerals. `+42` = the alpha
  Plan, `+43` = auto-calculated AI role. `scripts/m53b_costcalc.py` reproduces 180/188 rows; the
  explicit-alpha-Cost override (Mind Worms 5, Isle 8, Locusts 10) is **unlocated** — that is M53f.
- **M53d:** the pending-queue writer is `FUN_00417d20` (register-indexed!): 0x417e04
  `mov [eax+edx*4+0x50], ebx` (slot 1→+0x54 … 9→+0x74), 0x417dd8 insert-shift, 0x417dad delete-shift,
  `+0x4c` cap-9 store 0x417df6, count+1 0x417e1d. `FUN_00417ee0` dispatches on the mode field via
  table **0x419c04**: 1→0x418c51, 2→0x418cc9, 3→0x418cd8 (all → 0x418cda re-open), 4/6→0x418703
  (slot ≤ count ⇒ shift `queue[k] := queue[k+1]` + `+0x4c--` = REMOVE, else clamp the slot),
  5→0x4187a2 (push 1 = INSERT), 7→0x4187ad (push 0 = REPLACE in place), 0 → tail, writes nothing.
  Digit keys 1-9 pass a nonzero param_1 and only PREVIEW.
- **M53c:** THE POP = `FUN_004ef5d0(base_idx)`; `+0x4c` = PENDING-entry count (entries = count+1);
  pop shift 0x4ef628-39, `+0x4c--` 0x4ef642; pop-vs-re-pick fork 0x4f033e-0x4f037b (in mask ⇒ pop,
  else `FUN_004e5ae0`); with `+0x4c == 0` NOTHING consumes the head.
- **M53a/M52b:** queue encoding `−38` empty, `≥ 0` item id (unit `< 0x40`, facility `≥ 0x40`),
  `< 0` secret project (`|q| = 39 + idx`). Completion is PAYMENT-DRIVEN: COMPLET 0x4efe41 fires when
  `storage ≥ factor × 0x5ac950(id, idx, 0)`; `0x5ac950` (`shard_015.c:23696`, reads `+41` at `:23707`)
  is the type COST accessor; SPENDA debit 0x4efee0. `+0x44` = active-item mirror (`0x4f5a70`).
- Storage writers: IADD 0x4ef7f6, SPENDA 0x4efee0, CLAMP1 0x4eff20/23, CONVST 0x4f2d7d (our base
  always early-returns in `0x4f26e0`). **The sweep never truncates** and the base array SLIDES ⇒
  locate our base by NAME.
- Base record: x u16@0, y u16@2, owner@4, pop@6, f18/f1c/f20/f28/f30 flags, +0x3c progress,
  minerals@0x40, 44 active-item mirror, **4c pending count (cap 9)**, **queue @0x50..0x74**,
  8a/8c facility bitmap, 98 storage snapshot, c0, cc (−3 for us), d0, fc, f38 = 0x00dfbe41.
- Type record `0x98ad88 + type·52` (193 populated rows; ids 0-13 = the 14 alpha `#UNITS` rows — 0 Colony
  Pod, 1 Formers, 2 Scout Patrol, 3 Transport Foil, 6 Probe Team; 14-63 empty; 64+ = designed
  chassis×weapon×armor built by `FUN_00573a90`, which stores the requested role into `+43` at
  `:17802`): name +0[34], ability int +32, +36 chassis, +37 weapon, +38 armor, +39 reactor, **+41 cost
  factor**, +42 Plan, +43 auto role, +0x30 word flags (`&4` gates the `0x5ac950` bump). Full dump
  `evidence/m53b_types.tsv`. Upkeep `0x984d44/0x984d48 + item·48` (int0 == alpha `Maint`);
  secret-project costs `(&DAT_00984d44)[idx·0xc]`; per-player item counts are BYTES at
  `0x94de84 + player·0x20bc + item`.
- Globals: year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap
  0x92a370 (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array 0x95da10 stride 0x130,
  unit array 0x933278 stride 52, faction records stride 0x20bc, HUD income 0x745734/0x744f28/0x7457dc,
  difficulty cost 0x92a290/94 (10/10), 0x92ada8 (2), triad rates 0x92a2d0/d4/d8.
- UI objects: **pane 0x6a9480** (fields `+0x3ff3c` base index, `+0x3ff5c` selected queue slot,
  `+0x3ff60` zeroed by a row click, `+0xa1c` = the chooser sub-object 0x6a9e9c with `+0xa774`
  guard/result and `+0xa778` mode); `FUN_00416080(this)` = pane redraw; `FUN_00496ad0(pane+0xa1c,
  base, owner_byte, scratch)` = the modal item chooser (returns an item id or −9999);
  `FUN_00417ee0(slot, …)` = the dispatcher; `FUN_00417d20(item, insert_flag)` = the queue writer.

## Static-reading kit
- Clean 32-bit disasm, no attach: `gdb -batch -nx -q -ex "set architecture i386" -ex "set
  disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` → `evidence/`, grep it,
  never paste a whole function; line 1 is an arch banner; **coverage-check** (`index.csv` size ÷ 3.8 ≈
  insn count). Existing dumps: `ls evidence/*disasm* evidence/m53e_fn496ad0*`.
- Pseudocode `scripts/fn.py 0xADDR`; corpus `grep -rn <pat> ghidra_out/shard_*.c` then
  `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`. **Grep store SHAPES, not offsets**,
  and grep BOTH Ghidra renderings (`(&DAT_…)[…] =` and `*(… + 0x98…`).
- **When the pseudocode shows no store, byte-scan the image**: `d.find(struct.pack('<I', disp))` over
  the `.text` file range 0x1000..0x2703f4, **VA = file offset + 0x400000**. That is how M53e proved the
  single `0xb194` reference and located the `+0xa778` stores the corpus never showed.
- **Alpha comment headers name the columns** of sections whose rows are bare data
  (`programs/alpha.txt` `:348 #CHASSIS`, `:387 #WEAPONS`, `:422 #DEFENSES`, `:560 #UNITS`,
  `#FACILITIES`; full list in `ALPHA_RULES.md`); `scripts/parse_alpha.py` → `data/alpha.json`.
  `#UNITS` = `; Name, Chassis, Weapon, Armor, Plan, Cost, Carry, Preq, Icon, Abil` (`:532`) with
  `; Cost = Cost in minerals (0 = Autocalculate)` (`:554`). Cross-check templates:
  `scripts/m53b_types.py`, `scripts/m53b_costcalc.py`.
- Live `/proc/<pid>/mem` pread (TracerPid 0): read `0x8f0d60`, walk `0x95da10 + i*0x130` for
  `i < *(0x985af4)`, pull fields, recompute, then arm gdb.

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command is verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0
  (resets on reboot). Read-only state: `scripts/smac_state.py --json`. Our base = idx **70** @ 0x962d30.
- **Armed UI-driving (M53e recipe)**: `python3 scripts/m53e_drive.py --tag mXX --mode arm --hold 900
  [--pane 0x6a9480]` launched with **`background=true`** (Hermes kills children of a finished
  foreground call; `--hold` is the polling parent that keeps gdb alive), drive with
  `python3 scripts/m53e_seq.py --tag mXX --phase {1|2|2b|3|4}` (or your own `smac_play` clicks:
  `P.WIN = P.find_window()`, `P.click((x,y))`, `P.freeze(tag)`), then
  `python3 scripts/m53e_drive.py --tag mXX --mode stop`. **gdb runs under `stdbuf -o0`** — without it
  a short run loses every buffered breakpoint `printf` at SIGINT (m53e1 looked like "nothing fired"
  while the clicks worked). The breakpoint set (ENQ/PRESHOW/POST_PICK/MODE/ANSWER/SHIFTUP/SHIFTDN/
  HEAD/TAIL/CNT_*/SNAP/RESTORE/D20/D20_SHIFT/D20_STORE/BRANCH_*/QPIPE/W54/W58 + BAR_IGNORED at
  0x496a91 + BAR_CANCEL at 0x496a43) is baked in `scripts/m53e_drive.py` — read the script.
- Chooser geometry: overlay x 60-740 y 8-330; icon cols x 128/255/383/510/638, icon rows y 60/160/260
  (row 2 = Scout Patrol / Colony Pod / Formers / Probe Team / Children's Creche); bars y 343, ranges
  as above. QUEUE rows: click x 185, y = 437 + 12·(row−1) (row TEXT is at 439 + 12·(row−1)); CHANGE
  ≈(185,552), HURRY ≈(185,571). **Chooser-open test = pixel (160,343) == RGB (103,91,181)** — 2x OCR
  cannot read the bar labels at all.
- Pitfalls that bite here (full list in the skill): poke-then-arm (M33), `kill -CONT` after gdb-INT,
  never Escape on title/REALLYQUIT, OCR targets ≥4 chars, transient advisor panes swallow the next
  event, `$pc` sits PAST the store, **never signal by name** (the driver's own argv matches — stop a
  driver only with `--mode stop <tag>`), **a gdb command-list expression on a non-numeric convenience
  variable aborts the whole batch and detaches silently** (`m53e5_watch.log:50`; the driver now bakes
  the base pointer as a literal), gdb's own messages are unbuffered but its `printf` is not (attribute
  events by CONTENT, read the log after `--mode stop`), vision pixels = window coords but tesseract TSV
  is rescaled, `short*` aliasing doubles offsets in Ghidra (`DAT_008f0d60 + 0x28` = byte 0x50) but
  `(&DAT_0098adb1)[type·0x34]` IS byte-indexed, `*(int*)0x68cbb0` == the arg of 0x4e5ae0/0x4e5560.

## Milestone options (pick ONE)
- **M53f — the loader overrides (THE PICK, static, cheap).** Find where the alpha `#UNITS` **Cost**
  lands in `+41` and the **Plan** in `+42` (neither renders as a `DAT_` store: grep `*(… + 0x98adb1)`,
  `*(… + 0x98adb2`, `rep movs`, `FUN_00573a90` and the alpha-section dispatcher, and byte-scan for
  stores whose base is `0x98adb1`/`0x98adb2` reached through a register). Then fix the ability bit-1
  off-by-1 in `scripts/m53b_costcalc.py` (Scout Rover, Scout Speeder) so the 188-row check is clean.
- **M53g — the chooser guard field.** `[chooser_sub+0xa774]` (0x6b4610) gates the 1/7/5 mode stores
  and is NOT the icon selection; byte-scan for disp32 `0xa774` (and for stores through
  `[sub+0xa774]`), find its writer, then make **REPLACE / mode 7** fire live (and modes 2/3/6).
- **Later:** secret-project cost table `0x984d44` stride 0xc; the −29 head value; what fires at
  0x4ef992/0x4f0f46 (0 hits); `FUN_0059ce10`'s `+0x4c = pop·10/2` (over cap 9, `shard_015.c:14416`);
  M50c-e, M51b, base+0xc0.
- **Retired premises, do not resurrect:** "edi = the sweep-entry index"; "0x4e40a0 is just the
  `(1<<p)&mask` test"; "PROGDIV accumulates progress"; "base+0x50 is a single dword"; "+0x4c is the
  last used index"; "+0x54 is written by nobody"; "digit keys 1-9 queue an item"; "the queue refills
  itself from the head"; "`0x5ac950` returns a production WEIGHT"; "+41 is the mineral price as
  stored"; "+43 is a cost"; "the loader pre-scales ×10"; **"+0xb194 is a pane field some bar writes"**
  (it is `[chooser_sub+0xa778]`; the image has exactly one `0xb194` reference, a read); **"mode 5 is
  unreachable / the insert-shift never fires"**; **"the chooser's selection is `[sub+0xa774]`"**;
  **"OK commits the queued pick"** (OK = mode 0, writes nothing); **"CANCEL is the only path that
  rewrites the queue"** (its restore is the snapshot rewrite; DELETE/mode 4 removes); **"M53d's bar
  labels matched its click x's"** (618 = DELETE, 707 = CANCEL, 275 = OK).

## Report style
Findings → `evidence/<id>_findings.md` ONCE; SESSION_NOTES.md (dated section) + this file by
extraction from it; cite log line numbers for every claim; mark VERIFIED vs INFERRED; end with the
next-prompt pointer.
