# NEXT_PROMPT — SMAC RE, session 59

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a, M53b, M53c, M53d, M53e (+M53e6) done; **M53f done (session 58)**;
open: **M53g (THE PICK)**, then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you actually need (pitfalls + the code area). **Do NOT `skill_view` the whole file**
   (55 KB, ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 58 (M53f) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state (kit below): game up (`pgrep -x terran.exe` → 2124624), year 2371, our turn (`cur == 3`),
   n_bases 75, our base idx **70 @ 0x962d30**, base pane UP, chooser closed, no gdb, TracerPid 0,
   `ptrace_scope` 0. Base 70: storage `+0x40 = 0`, head `+0x50 = 3` (Transport Foil),
   **`+0x4c = 2` pending — `+0x54 = 2`, `+0x58 = 2` (two Scout Patrols M53e queued; to clean them:
   row 1 → DELETE bar → OK, twice)**. M53g needs ONE armed driving pass (M53e recipe).

## Footing — production economy + the type record (M48d → M53f, VERIFIED unless marked)

### M53f (session 58): the alpha `#UNITS` overrides + the cost formula — write-up `evidence/m53f_findings.md`
- `+41` has **exactly ONE store in the image**: `0x595ce7 mov BYTE PTR [esi+0x98adb1],al` right after
  `call 0x595820` — 30 references / 1 store from a linear `objdump -d -M intel --section=.text`
  (`evidence/m53f_adb1_refs.txt`). The corpus claim (`shard_015.c:9358`, `FUN_00595b10 @ 0x595b10`) holds.
- The overrides are **disp8 stores off `esi = record + 50`** inside the `#UNITS` loader `FUN_00579f40`
  (`shard_014.c:21351`): **+42 Plan 0x57a02d** (guard ≥0), **+41 Cost 0x57a037** (guard: 0 =
  Autocalculate), +40 Carry 0x57a041 (guard ≠0), +46 Icon 0x57a04a (writes −1 too), +50 prereq word
  0x57a001, Name strcpy 0x579fb1; the builder runs first (0x57a021); row cap `0x40` ⇒ designed units
  (id ≥ 0x40) can never be overridden. Ghidra renders them `*(char *)(p + -4)` / `(int)p + -9`
  (`shard_014.c:21402`, `:21405`) — that is why no `DAT_0098adb1` store ever showed in a corpus grep.
  Live: `+42 == alpha Plan 14/14`, `+46 == alpha Icon 14/14`, `+40 == alpha Carry` where non-zero.
- Save/restore pair: `FUN_00596850` copies 48-byte save records into the 52-byte runtime records;
  `0x597464 → +41`, `0x59746a → +42` (`evidence/m53f_disasm_597400.txt`).
- Ability table `0x98aaf4` stride 28 = the 24 `#ABILITIES` rows: `int[0]` = the cost rule (column 1
  verbatim), `int[2]` (**+8**) = the flag string parsed as binary. The rule switch is jump table
  `0x595ab4` indexed `rule + 7`, in exactly Ghidra's case order (`evidence/m53f_jumptable.txt`).
- The cost calculator is **188/188 explained**: 181 formula + 4 alpha-Cost override rows (Alien Artifact
  10, Mind Worms 5, Isle of the Deep 8, Locusts 10) + 3 stale records, **0 unexplained**
  (`evidence/m53f_costcalc_digest.txt`; `python3 scripts/m53b_costcalc.py --legacy` reproduces M53b's
  179+4+3 with exactly 2 unexplained). The M53b gap was the land-chassis loop `0x59597b-0x5959a6`
  (reads `entry+8`, bit **0x400** ⇒ +1 surcharge; Deep Radar bit 1 → Scout Rover/Speeder), not the rule
  table. Stale-record rule: index ≥ 9/21/10 (the shipped `#CHASSIS`/`#WEAPONS`/`#DEFENSES` counts) **or
  reactor == 0** (all 185 real rows have reactor 1 or 2).

### M53e / M53e6 (session 57): the enqueue chooser — write-ups `evidence/m53e_findings.md`, `m53e6_findings.md`
- The dispatch field `pane+0xb194` is the **chooser sub-object's `+0xa778`** (pane = static BSS
  **0x6a9480**, sub-object = `pane+0xa1c` = 0x6a9e9c). All writes are `[sub+0xa778]` inside the chooser
  `FUN_00496ad0`: 0x496993→1, 9a5→2, 9b7→3, **9da→7**, 9e9→4, **a09→5**, a18→6, a27/a36→0, **a52→7**;
  the 1/7/5 stores sit behind `cmp [sub+0xa774],-1` (0x496982/9c9/9f8); CANCEL = `mov [sub+0xa774],-1`
  (0x496a43) → returns −9999 → RESTORE ×10 (0x418636); OK = mode 0 → tail, writes nothing.
- Bars, label-VERIFIED: **HELP 153-233, OK 252-311, REPLACE 364-421, INSERT 472-523, DELETE 556-636,
  CANCEL 659-705**, body y 336-352. INSERT→5 fired live twice (`m53e6:77-92`, `:125-134`): MODEWP 5 →
  `D20_SHIFT` → `D20_STORE +0x54 3→2` → `+0x4c 0→1`.
- **OPEN:** REPLACE never fired (5 attempts; `BAR_IGNORED` tail 0x496a91, `m53e6:63,111`) and
  `[sub+0xa774]` (0x6b4610) read 5/17 while the picker returned 2 ⇒ it is NOT the selection. Modes 2/3/6
  are static-only. One bar click runs the bar handler twice (press + release).
- QUEUE rows 1..8 = pending slots `+0x54..+0x70` (row text y = 439 + 12·(row−1), x 143-248); the 9th slot
  `+0x74` has no row (INFERRED); the head `+0x50` is the LEFT panel. A row click clamps
  `slot = min(row, count+1)` and zeroes `pane+0x3ff60` (`shard_001.c:2133-2140`, `:2193-2197`).

### Standing from M53b / M53d / M53c / M53a-M52b (do not re-derive)
- **M53b:** type-record `+41` is the COST FACTOR; every price is `FUN_004e40a0(owner,1,−1) × +41`, live
  multiplier 10 ⇒ `+41 = 1` = 10 minerals. `+43` = auto-calculated AI role. The formula's inputs are the
  alpha tables: chassis `0x92ae80`/0x90 `+4` cost, `+1` triad, `+5` missile flag; weapons `0x92b950`/16
  `+3` cost, `+2` mode; armor `0x92fd10`/16 `+0xa` cost.
- **M53d:** the pending-queue writer is `FUN_00417d20` (register-indexed): 0x417e04
  `mov [eax+edx*4+0x50], ebx` (slot 1→+0x54 … 9→+0x74), 0x417dd8 insert-shift, 0x417dad delete-shift,
  `+0x4c` cap-9 0x417df6, count+1 0x417e1d. `FUN_00417ee0` dispatches on the mode via **0x419c04**:
  1/2/3→0x418cda re-open, 4/6→0x418703 remove-or-clamp, 5→0x4187a2 push 1 = INSERT, 7→0x4187ad push 0 =
  REPLACE, 0 → tail (writes nothing). Digit keys 1-9 pass a nonzero flag and only PREVIEW.
- **M53c:** THE POP = `FUN_004ef5d0(base_idx)`; `+0x4c` = PENDING-entry count (entries = count+1); pop
  shift 0x4ef628-39, `+0x4c--` 0x4ef642; pop-vs-re-pick fork 0x4f033e-0x4f037b; with `+0x4c == 0` NOTHING
  consumes the head.
- **M53a/M52b:** queue encoding `−38` empty, `≥ 0` item id (unit `< 0x40`, facility `≥ 0x40`), `< 0`
  secret project (`|q| = 39 + idx`). Completion is PAYMENT-DRIVEN: COMPLET 0x4efe41 fires when `storage ≥
  factor × 0x5ac950(id, idx, 0)`; `0x5ac950` (`shard_015.c:23696`, reads `+41` at `:23707`) is the type
  COST accessor; SPENDA debit 0x4efee0. `+0x44` = active-item mirror (`0x4f5a70`).
- Storage writers IADD/SPENDA/CLAMP1/CONVST (`evidence/m47_findings.md`-era addresses in
  SESSION_NOTES). **The sweep never truncates** and the base array SLIDES ⇒ locate our base by NAME.
- Base record: x u16@0, y u16@2, owner@4, pop@6, f18/f1c/f20/f28/f30 flags, +0x3c progress, minerals@0x40,
  44 active-item mirror, **4c pending count (cap 9)**, **queue @0x50..0x74**, 8a/8c facility bitmap, 98
  storage snapshot, c0, cc (−3 for us), d0, fc, f38 = 0x00dfbe41.
- Type record `0x98ad88 + type·52` (188 printable rows; ids 0-13 = the 14 alpha `#UNITS` rows; 14-63
  empty; 64+ = designed chassis×weapon×armor built by `FUN_00573a90`, which stores the requested role into
  `+43` at `:17802`): name +0[34], ability int +32, +36 chassis, +37 weapon, +38 armor, +39 reactor (1 or
  2), **+40 carry**, **+41 cost factor**, +42 Plan, +43 auto role, +46 icon, +50 prereq word (INFERRED:
  −1 none, −2 "Disable"), +0x30 word flags (`&4` gates the `0x5ac950` bump). Full dump
  `evidence/m53b_types.tsv`; upkeep and per-player item counts in `SESSION_NOTES.md` (M53b block).
- Globals: year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap 0x92a370
  (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array 0x95da10 stride 0x130, unit array
  0x933278 stride 52, faction records stride 0x20bc, HUD income 0x745734/0x744f28/0x7457dc.
- UI objects: **pane 0x6a9480** (`+0x3ff3c` base index, `+0x3ff5c` selected queue slot, `+0x3ff60` zeroed
  by a row click, `+0xa1c` = the chooser sub-object 0x6a9e9c with `+0xa774` guard/result and `+0xa778`
  mode); `FUN_00416080(this)` = pane redraw; `FUN_00496ad0(pane+0xa1c, base, owner_byte, scratch)` = the
  modal item chooser (returns an item id or −9999); `FUN_00417ee0` = the dispatcher; `FUN_00417d20` = the
  queue writer; `FUN_00579f40` = the `#UNITS` loader; `FUN_00595b10` = the type builder; `FUN_00595820` =
  the cost formula; `FUN_00596850` = load_save_state.

## Static-reading kit
- **A store census belongs on a linear disassembly, not the corpus:** `objdump -d -M intel
  --section=.text programs/terran.exe > evidence/<id>_text_disasm.txt` (~40 MB, regenerable — grep it,
  never commit it, delete it after extracting the windows you cite). Map an address to its function by
  bisecting `ghidra_out/index.csv`. **VA = file offset + 0x400000.**
- Pseudocode `scripts/fn.py 0xADDR`; corpus `grep -rn <pat> ghidra_out/shard_*.c` then
  `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`. **Grep store SHAPES, not offsets**:
  literal `&DAT_…[…] =`, `*(… + 0x98…`, indexed stores, `rep movs`, AND negative pointer arithmetic off a
  register base (`*(char *)(p + -4)`, `(int)p + -9`) — that is how M53f's `+41`/`+42` overrides hid from
  two corpus greps and one disp32 byte-scan (base register = record + 50).
- **When the pseudocode shows no store, byte-scan the image**: `d.find(struct.pack('<I', disp))` over the
  `.text` file range 0x1000..0x2703f4. That is how M53e proved the single `0xb194` reference.
- **Alpha comment headers name the columns** of sections whose rows are bare data (`programs/alpha.txt`
  `:348 #CHASSIS`, `:387 #WEAPONS`, `:422 #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `#FACILITIES`;
  full list in `ALPHA_RULES.md`); `scripts/parse_alpha.py` → `data/alpha.json`. `#UNITS` = `; Name,
  Chassis, Weapon, Armor, Plan, Cost, Carry, Preq, Icon, Abil` (`:532`) with `; Cost = Cost in minerals
  (0 = Autocalculate)` (`:554`). Templates: `scripts/m53b_types.py`, `scripts/m53b_costcalc.py`
  (`--legacy` = the superseded M53b model).
- **A hand-decoded jump table is a trap:** dump the raw table bytes first (`m53f_jumptable.txt` is the
  pattern) before "correcting" Ghidra — a mis-dropped entry once "proved" the case labels were shifted
  and broke 10 live rows.

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command is verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0
  (resets on reboot). Read-only state: `scripts/smac_state.py --json`. Our base = idx **70** @ 0x962d30.
- **Armed UI-driving (M53e recipe)**: `python3 scripts/m53e_drive.py --tag mXX --mode arm --hold 900
  [--pane 0x6a9480]` launched with **`background=true`** (Hermes kills children of a finished foreground
  call; `--hold` is the polling parent that keeps gdb alive), drive with
  `python3 scripts/m53e_seq.py --tag mXX --phase {1|2|2b|3|4}` (or your own `smac_play` clicks:
  `P.WIN = P.find_window()`, `P.click((x,y))`, `P.freeze(tag)`), then
  `python3 scripts/m53e_drive.py --tag mXX --mode stop`. **gdb runs under `stdbuf -o0`** — without it a
  short run loses every buffered breakpoint `printf` at SIGINT. The breakpoint set
  (ENQ/PRESHOW/POST_PICK/MODE/ANSWER/…/D20_STORE/W54/W58 + BAR_IGNORED 0x496a91 + BAR_CANCEL 0x496a43)
  is baked in `scripts/m53e_drive.py` — read it. `evidence/m53e6_drive.py` is the tag-based driver used
  in session 57; stop it with
  `python3 scripts/m53e6_drive.py --mode stop <tag>` (never pkill).
- Chooser geometry: overlay x 60-740 y 8-330; icon cols x 128/255/383/510/638, icon rows y 60/160/260;
  bars y 343, ranges as above. QUEUE rows: click x 185, y = 437 + 12·(row−1) (row TEXT is at 439 + 12·(row−1)); CHANGE
  ≈(185,552), HURRY ≈(185,571). **Chooser-open test = pixel (160,343) == RGB (103,91,181)** — 2x OCR
  cannot read the bar labels at all.
- Pitfalls that bite here (full list in the skill): poke-then-arm (M33), `kill -CONT` after gdb-INT,
  never Escape on title/REALLYQUIT, `$pc` sits PAST the store, **never signal by name** (the driver's own argv matches — stop a driver only
  with `--mode stop <tag>`), **a gdb command-list expression on a non-numeric convenience variable aborts
  the whole batch and detaches silently** (`m53e5_watch.log:50`; the driver bakes the base pointer as a
  literal), gdb's own messages are unbuffered but its `printf` is not (attribute events by CONTENT, read
  the log after `--mode stop`), vision pixels = window coords but tesseract TSV is rescaled, `short*`
  aliasing doubles offsets in Ghidra (`DAT_008f0d60 + 0x28` = byte 0x50) but
  `(&DAT_0098adb1)[type·0x34]` IS byte-indexed, `*(int*)0x68cbb0` == the arg of 0x4e5ae0/0x4e5560.

## Milestone options (pick ONE)
- **M53g — the chooser guard field + REPLACE (THE PICK).** `[chooser_sub+0xa774]` (0x6b4610) gates the
  1/7/5 mode stores and is NOT the icon selection (live reads 5/17 while the picker returned 2). Static
  first: in the chooser `0x496ad0`'s 3,310 B disasm (`evidence/m53d_fn496ad0_disasm.txt`) grep every
  store to `[sub+0xa774]` (and a disp32 `0xa774` scan of `.text`), read `0x41924b`'s gate
  (`m53d_fn41924b_disasm.txt`) and name what the field actually holds. Then ONE armed pass (M53e
  recipe): ITEM row → pick a NEW item → REPLACE → read `+0xa778`/`+0xa774`/`+0x4c`/`+0x54`/`+0x58`
  before and after. **Done when** the guard's writer set is named with addresses AND REPLACE either fires
  live or its refusal is pinned to an instruction.
- **Later:** secret-project cost table `0x984d44` stride 0xc; the −29 head value; what fires at
  0x4ef992/0x4f0f46 (0 hits); `FUN_0059ce10`'s `+0x4c = pop·10/2` (over cap 9, `shard_015.c:14416`); who
  calls `FUN_00579f40` and whether the alpha loaders re-run on scenario load; `FUN_00570860` (the `+40`
  carry producer, non-zero for weapon mode 7); M50c-e, M51b, base+0xc0.
- **Retired premises, do not resurrect:** "PROGDIV accumulates progress"; "base+0x50 is a single dword";
  "+0x4c is the last used index"; "+0x54 is written by nobody"; "digit keys 1-9 queue an item"; "the queue refills itself
  from the head"; "`0x5ac950` returns a production WEIGHT"; "+41 is the mineral price as stored"; "+43 is
  a cost"; "the loader pre-scales ×10"; **"+0xb194 is a pane field some bar writes"**; **"mode 5 is
  unreachable / the insert-shift never fires"**; **"the chooser's selection is `[sub+0xa774]`"**; **"OK
  commits the queued pick"** (OK = mode 0, writes nothing); **"CANCEL is the only path that rewrites the
  queue"**; **"M53d's bar labels matched its click x's"** (618 = DELETE, 707 = CANCEL, 275 = OK); **"the
  alpha Cost→`+41` override is unlocated"** (it is 0x57a037); **"Ghidra's cost-rule case labels were
  shifted by one"** (the raw jump table says they are right); **"the ability flag word is at +16"** (it is
  +8); "the 188-row check has unexplained mismatches" (it has none).

## Report style
Findings → `evidence/<id>_findings.md` ONCE; SESSION_NOTES.md (dated section) + this file by
extraction from it; cite log line numbers for every claim; mark VERIFIED vs INFERRED; end with the
next-prompt pointer.
