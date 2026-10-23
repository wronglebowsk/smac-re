# NEXT_PROMPT — SMAC RE, session 60

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a, M53b, M53c, M53d, M53e (+e6), M53f, **M53g done (session 59)**;
open: **M53h (THE PICK)**, then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you actually need (pitfalls + the code area). **Do NOT `skill_view` the whole file**
   (55 KB, ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 59 (M53g) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state (kit below): game up (`pgrep -x terran.exe` → 2124624), year 2371, our turn (`cur == 3`),
   n_bases 75, our base idx **70 @ 0x962d30**, base pane UP, chooser closed, no gdb, TracerPid 0,
   `ptrace_scope` 0. Base 70: storage `+0x40 = 0`, head `+0x50 = 3` (Transport Foil), `+0x5c = 3`,
   **`+0x4c = 2` pending — `+0x54 = 2`, `+0x58 = 2` (two Scout Patrols; clean via row → DELETE → OK,
   twice)**. Guard field reads −1, mode 0 (clean). M53h is STATIC-FIRST (Script.txt / button table /
   enumeration); one armed pass only if it needs a live enumeration dump.

## Footing — production economy + the chooser UI (M48d → M53g, VERIFIED unless marked)

### M53g (session 59): the guard field IS the selection cell index; REPLACE = bar param 7 — write-up `evidence/m53g_findings.md`
- `[chooser_sub+0xa774]` (0x6b4610 = pane 0x6a9480 **+0xb190**; sub = pane+0xa1c = 0x6a9e9c) = the
  widget's **selection cell index** (−1 = none). Cell index = position in a 5-col grid: rows y~60/160/
  260 = cells 0-14; the bar row (y~336-352) overlaps phantom cells 15-19 (col3 = 17 — x 381-421).
  Paint (`FUN_004954e0`) clears to −1 (store 0x495541) then sets it to the enum index of the item in
  the selected slot (0x495b00/0x495e6f, via enum counter `+0xa818`); icon/cell click → setter 0x4962ec
  (`FUN_004962a0` = **vtable+0x48**); CANCEL → −1 (0x496a43). Mutator `FUN_004963b0` (vtable+0x60,
  8 stores incl. `=0` at 0x496777, swaps with +0xa818) never fired live. Census: 43 refs / 13 stores,
  whole `.text` (`evidence/m53g_a774_all_refs.txt`) — no other writer exists.
- Bar handler `FUN_00496950` = **vtable+0xa8** (only pointer 0x672340 = live vptr 0x672298 + 0xa8).
  Jump table 0x496a9a indexes `param+2` (range-check `ja` → 0x496a91). Cases: 0=HELP(gate)→1 · 1→2 ·
  2=(gate)→7 · 3→3 · 4→4 · 5=INSERT(gate)→5 · 6→6 · **7→7 UNGATED** · −1=OK→0 · −2=CANCEL→0 + guard −1.
  Gate = `cmp [this+0xa774],-1; je 0x496a91` (0x4969c9/0x4969f8). After any case: `call [vtable+0xe0]`
  (0x5ce6ff repaint) then **0x496a91 = the SHARED EPILOGUE RETURN — mode-storing paths reach it too**
  (BAR_IGNORED ≠ refusal). **One handler run per click.**
- **REPLACE fires live at (365,343)** (also 345): BARH param=7 → mode 7 (store 0x496a52) → POST_PICK
  edi=−26 → dispatcher 0x4187ad → `FUN_00417d20` → D20_STORE +0x54 2→−26 (`m53g_watch.log:104-112`).
  The drawn REPLACE bar body x 381-421 is DEAD (phantom cell 17 → setter, handler never called) —
  M53e's five refused clicks + its "guard 5/17 ≠ selection 2" were all cell indices. Session 56's lone
  mode-7 hit = same param-7 rect (INFERRED).
- **Rect map (param ← click x at y 343, VERIFIED):** HELP 0←160 · OK −1←285 · **REPLACE 7←345/365** ·
  INSERT 5←425/440/497 · DELETE 4←602 · CANCEL −2←692. Params 1/2/3/6 mouse-unreachable here; the
  case-2 gate is never exercised by mouse. CANCEL-restore (RESTORE ×10 from entry snapshot) makes
  armed REPLACE probes non-destructive.
- Chooser returns: selection item id or −9999 (CANCEL). POST_PICK probe printed edi = the return.
  Click (397,320) → guard 12 → return **edi=−26**: enumeration index 12 maps to a secret-project-range
  queue value; the enumeration contents/encoding are THE PICK (M53h).

### M53f (session 58): the alpha `#UNITS` overrides + the cost formula — write-up `evidence/m53f_findings.md`
- `+41` has exactly ONE store in the image: `0x595ce7` (after `call 0x595820`), 30 refs from a linear
  `objdump -d -M intel --section=.text` census. The overrides are **disp8 stores off `esi = record + 50`**
  inside the `#UNITS` loader `FUN_00579f40`: **+42 Plan 0x57a02d**, **+41 Cost 0x57a037** (0 =
  Autocalculate), +40 Carry 0x57a041, +46 Icon 0x57a04a, +50 prereq 0x57a001, Name 0x579fb1; builder
  runs first (0x57a021); row cap `0x40` ⇒ designed units never overridden. Live: `+42 == alpha Plan
  14/14`, `+46 == Icon 14/14`. Save pair `FUN_00596850`: `0x597464 → +41`, `0x59746a → +42`.
- Ability table `0x98aaf4` stride 28 = 24 `#ABILITIES` rows: `int[0]` = cost rule, `int[2]` (**+8**) =
  flag word (bit 0x400 = +1 land surcharge). Rule switch = jump table `0x595ab4` indexed `rule+7`,
  exactly Ghidra's case order. Cost calculator **188/188 explained, 0 unexplained**
  (`scripts/m53b_costcalc.py`; `--legacy` = superseded M53b model). Stale-record rule: chassis ≥ 9 /
  weapon ≥ 21 / armor ≥ 10 or reactor == 0.

### Standing from M53b / M53d / M53c / M53a-M52b (do not re-derive)
- **M53b:** type-record `+41` = COST FACTOR; every price = `FUN_004e40a0(owner,1,−1) × +41`, live
  multiplier 10 ⇒ `+41 = 1` = 10 minerals. `+43` = auto AI role. Formula inputs: chassis `0x92ae80`/0x90
  `+4`, weapons `0x92b950`/16 `+3`/`+2`, armor `0x92fd10`/16 `+0xa`.
- **M53d:** queue writer `FUN_00417d20`: 0x417e04 store (slot 1→+0x54 … 9→+0x74), 0x417dd8 insert-shift,
  0x417dad delete-shift, `+0x4c` cap-9 0x417df6. Dispatcher `FUN_00417ee0` on mode via 0x419c04:
  1/2/3→0x418cda re-open, 4/6→0x418703, 5→0x4187a2 push 1, 7→0x4187ad push 0, 0 → tail. Digit keys
  1-9 only PREVIEW. **M53c:** THE POP = `FUN_004ef5d0(base_idx)`; `+0x4c` = PENDING-entry count; with
  `+0x4c == 0` NOTHING consumes the head. **M53a/M52b:** queue encoding `−38` empty, `≥ 0` item id
  (unit `< 0x40`, facility `≥ 0x40`), `< 0` secret project (`|q| = 39 + idx` — but M53g observed −26;
  reconcile in M53h). Completion is PAYMENT-DRIVEN: COMPLET 0x4efe41 when `storage ≥ factor ×
  `0x5ac950(id, idx, 0)` (type COST accessor, `shard_015.c:23696`); SPENDA debit 0x4efee0. `+0x44` =
  active-item mirror. Storage sweep never truncates; base array SLIDES ⇒ locate base by NAME.
- Base record: x u16@0, y u16@2, owner@4, pop@6, flags f18/f1c/f20/f28/f30, +0x3c progress, minerals@0x40,
  44 active-item mirror, **4c pending count (cap 9)**, **queue @0x50..0x74**, 8a/8c facility bitmap, 98
  storage snapshot, c0, cc (−3 for us), d0, fc, f38 = 0x00dfbe41.
- Type record `0x98ad88 + type·52` (188 printable rows; ids 0-13 = alpha `#UNITS`; 14-63 empty; 64+
  designed via `FUN_00573a90`): name +0[34], ability int +32, +36 chassis, +37 weapon, +38 armor,
  +39 reactor, +40 carry, **+41 cost factor**, +42 Plan, +43 auto role, +46 icon, +50 prereq word,
  +0x30 word flags (`&4` gates the `0x5ac950` bump). Full dump `evidence/m53b_types.tsv`.
- Globals: year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap 0x92a370
  (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array 0x95da10 stride 0x130, unit array
  0x933278 stride 52, faction records stride 0x20bc, HUD income 0x745734/0x744f28/0x7457dc.
- UI objects: **pane 0x6a9480** (`+0x3ff3c` base index, `+0x3ff5c` selected queue slot, `+0x3ff60` zeroed
  by row click, `+0xa1c` chooser sub-object 0x6a9e9c, **+0xb190 guard, +0xb194 mode**); chooser class
  **vptr 0x672298** (live): +0x4 `FUN_00494bb0`, +0x8 `FUN_00494c40` (runs after OK/CANCEL when slot≠0),
  +0x48 `FUN_004962a0` guard setter, +0x60 `FUN_004963b0` mutator, +0xa8 `FUN_00496950` bar handler,
  +0xe0 0x5ce6ff repaint. `FUN_00416080(this)` = pane redraw; `FUN_00496ad0(pane+0xa1c, base, owner,
  scratch)` = the modal chooser (returns item id or −9999); `FUN_00417ee0` dispatcher; `FUN_00417d20`
  queue writer; `FUN_00579f40` `#UNITS` loader; `FUN_00595b10` type builder; `FUN_00595820` cost formula;
  `FUN_00596850` load_save_state.

## Static-reading kit
- **Store censuses on a linear disassembly:** `objdump -d -M intel --section=.text programs/terran.exe`
  (~40 MB, regenerable, grep then delete — never commit). Map VA→function by bisecting
  `ghidra_out/index.csv`. **VA = file offset + 0x400000.** Grep store SHAPES (indexed stores, disp8
  off a table-base register, `rep movs`, negative pointer arithmetic), not literal offsets.
- Pseudocode `scripts/fn.py 0xADDR`; corpus `grep -rn <pat> ghidra_out/shard_*.c` then
  `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`. When pseudocode shows no store,
  byte-scan the image (`d.find(struct.pack('<I', disp))` over .text 0x1000..0x2703f4).
- **Alpha comment headers name the columns** of bare-data sections (`programs/alpha.txt` `:348 #CHASSIS`,
  `:387 #WEAPONS`, `:422 #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `#FACILITIES`; list in
  `ALPHA_RULES.md`); `scripts/parse_alpha.py` → `data/alpha.json`. `#UNITS` = `; Name, Chassis, Weapon,
  Armor, Plan, Cost, Carry, Preq, Icon, Abil` (`:532`). Templates: `scripts/m53b_types.py`,
  `scripts/m53b_costcalc.py`.
- **A hand-decoded jump table is a trap:** dump raw table bytes first (`m53f_jumptable.txt` pattern).
  Bar-handler table pattern: `jmp [edx*4+T]` after `add param,+2` + `ja` range check (m53g §3).
- **Script.txt has no REPLACE/INSERT bar labels** (grep found none) — the chooser bars are drawn by
  code (`FUN_004954e0` paint); the button table feeding vtable+0xa8 params is elsewhere (M53h target).

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
  Read-only state: `scripts/smac_state.py --json`; our base = idx **70** @ 0x962d30 ("Climactic Research").
- **Armed UI-driving:** `python3 scripts/m53g_drive.py --tag mXX --mode arm --hold 900 --pane 0x6a9480`
  under **background=true** (Hermes kills children of a finished foreground call), drive with your own
  `smac_play` clicks (`P.WIN = P.find_window()`, `P.focus()`, `P.click((x,y))`; `m53e_seq.py` helpers:
  `chooser_fields(pid)`, `bar_px()`, `base_fields(pid)`), then `python3 scripts/m53g_drive.py --mode
  stop --tag mXX` (positional tag NOT accepted). m53g_drive = m53e_drive + BARH(0x496950:
  param/ecx/guard) + GATE0/2/5 + SELWP on pane+0xb190 (4 hw watchpoints total: SELWP+MODEWP+W54+W58).
  gdb runs under `stdbuf -o0`; watchpoint `$pc` sits PAST the store; read the log after stop.
- Chooser geometry: overlay x 60-740 y 8-330; icon cols x 128/255/383/510/638, rows y 60/160/260;
  bars y 343 (drawn: HELP 153-233, OK 252-311, REPLACE 364-421, INSERT 472-523, DELETE 556-636,
  CANCEL 659-705); **clickable buttons: REPLACE ~340-380, INSERT ~411-523** (rect map above). QUEUE
  rows: click x 185, y = 437 + 12·(row−1); CHANGE ≈(185,552), HURRY ≈(185,571). **Chooser-open test =
  pixel (160,343) == RGB (103,91,181)** (`m53e_seq.bar_px()`).
- Pitfalls that bite here (full list in the skill): poke-then-arm (M33), `kill -CONT` after gdb-INT,
  never Escape on title/REALLYQUIT, **never signal by name** (stop drivers with `--mode stop --tag`),
  **a gdb command-list expression on a non-numeric convenience variable aborts the batch and detaches
  silently** (bake base as literal), gdb `printf` needs stdbuf -o0, vision pixels = window coords but
  tesseract TSV is rescaled, `short*` aliasing doubles offsets in Ghidra (`DAT_008f0d60 + 0x28` = byte
  0x50), pane sub-object relays subtract 0xa14 (`[ecx-0xa14]` = chooser sub), `*(int*)0x68cbb0` == the
  arg of 0x4e5ae0/0x4e5560.

## Milestone options (pick ONE)
- **M53h — the chooser enumeration + the button table (THE PICK).** What fills cells 0-19 in
  `FUN_004954e0`'s enumeration (units? facilities? secret projects? availability filter — guard 5 =
  Scout Patrol id 2, guard 12 → returned **−26**, reconcile with M53a's `|q| = 39 + idx`), and where
  the bar-button table lives (params 0/−1/7/5/4/−2 + the rect that puts REPLACE left of its drawn bar;
  the mouse-unreachable params 1/2/3/6). Static first: read `FUN_004954e0` fully (818-line disasm
  `evidence/m53g_fn4954e0_disasm.txt` + pseudocode), find the item-list builder feeding it, and grep
  the button table (vtable+0xa8 relays: 0x41f090/0x428140/0x43dc00/0x43fee0 forward `[ebp+8]`).
  **Done when** the enumeration order is named with its producer address AND the param→rect table is
  located (or the −26 encoding is cracked with a live cross-check).
- **Later:** secret-project cost table `0x984d44` stride 0xc; the −29 head value; what fires at
  0x4ef992/0x4f0f46 (0 hits); `FUN_0059ce10`'s `+0x4c = pop·10/2` (over cap 9, `shard_015.c:14416`);
  who calls `FUN_00579f40`; `FUN_00570860` (the `+40` carry producer); vtable+8 `FUN_00494c40`
  (post-OK/CANCEL when slot≠0); vtable+0x60 mutator path; producers of modes 2/3/6; M50c-e, M51b,
  base+0xc0.
- **Retired premises, do not resurrect:** "PROGDIV accumulates progress"; "base+0x50 is a single dword";
  "+0x4c is the last used index"; "+0x54 is written by nobody"; "digit keys 1-9 queue an item"; "the
  queue refills itself from the head"; "`0x5ac950` returns a production WEIGHT"; "+41 is the mineral
  price as stored"; "+43 is a cost"; "the loader pre-scales ×10"; "+0xb194 is a pane field some bar
  writes"; "mode 5 is unreachable"; "OK commits the queued pick"; "CANCEL is the only path that
  rewrites the queue"; "M53d's bar labels matched its click x's"; "the alpha Cost→`+41` override is
  unlocated"; "Ghidra's cost-rule case labels were shifted"; "the ability flag word is at +16"; "the
  188-row check has unexplained mismatches"; **"[sub+0xa774] is not the selection" (it IS — the cell
  index; 5/17 were cell indices)**; **"REPLACE needs guard ≠ −1 / is case 2" (mouse REPLACE = param 7,
  UNGATED)**; **"BAR_IGNORED 0x496a91 = bar refusal" (shared epilogue return — mode stores reach it
  too)**; **"one bar click runs the handler twice" (once)**; **"REPLACE's clickable area = its drawn
  bar" (drawn body 381-421 is phantom cell 17 → setter path)**.

## Report style
Findings → `evidence/<id>_findings.md` ONCE; SESSION_NOTES.md (dated section) + this file by
extraction from it; cite log line numbers for every claim; mark VERIFIED vs INFERRED; end with the
next-prompt pointer.
