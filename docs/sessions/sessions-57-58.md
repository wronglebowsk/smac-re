# Session notes archive — sessions 57-58

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 57 (2026-10-23) — M53e: **MODE 5 IS THE INSERT BAR AND IT FIRES LIVE** (insert-shift 0x417dd8 caught, `+0x4c 0→1`); the dispatch field "pane+0xb194" is really the **chooser sub-object's +0xa778** — the image's only mode stores are `[sub+0xa778]` inside `FUN_00496ad0` (0x496993→1, 9a5→2, 9b7→3, 9da→7, 9e9→4, **9f3/0x496a09→5**, 9a18→6, 9a27+9a36→0, 9a52→7)

- **Why the corpus had no `b194` store.** A byte scan of `.text` for disp32 `94 b1 00 00` finds exactly
  ONE instruction: the read at 0x4186ea (`mov eax,[ebx+0xb194]`, the dispatcher's dispatch). The pane is
  the static BSS object **0x6a9480** (`m53e2_watch.log:72`); the chooser sub-object is `pane+0xa1c` =
  0x6a9e9c and 0x6a9e9c+0xa778 = 0x6b4614 = pane+0xb194. A hw watchpoint on 0x6b4614 caught every mode
  write with its PC inside the chooser. Full write-up `evidence/m53e_findings.md`.
- **Bars label-VERIFIED** (6x crop-OCR + blue-pixel run scan, `m53e_grid_pre.txt`): HELP 153-233,
  OK 252-311, REPLACE 364-421, INSERT 472-523, DELETE 556-636, CANCEL 659-705, bar body y 336-352
  (labels drawn INSIDE the bars). M53d's label guess was wrong; its clicks re-map to 160=HELP,
  285=OK, 397=REPLACE, 497=INSERT, 602=DELETE, 692=CANCEL. Bar fill RGB (103,91,181) at (160,343) is
  the instant chooser-open detector (no OCR).
- **Bar → mode (watchpoint-verified):** INSERT→5 (store 0x496a09, `$pc` 0x496a13), DELETE→4 (0x4969e9),
  HELP→1 (0x496993), entry/OK/CANCEL reset→0 (0x496a27/0x496a36). CANCEL = `mov [sub+0xa774],-1`
  (0x496a43) → returns −9999 → RESTORE ×10 rewrites +0x50..+0x74 from the stack snapshot and exits at
  0x419967 **without consulting the mode**. OK = selection + mode 0 → tail → writes nothing AND does
  not restore, so a committed edit survives an OK exit. HELP = mode 1 → opens the unit-design pane
  (RENAME/OBSOLETE/UPGRADE/CANCEL at y 356, CANCEL x≈614) whose CANCEL re-opens the chooser.
- **Mode 5 live** (`m53e6:77-92`): INSERT with a selection → MODEWP mode=5 → POST_PICK edi=2 → MODE 5
  → D20_SHIFT dst_off 0x74,0x70,0x6c,0x68,0x64,0x60,0x5c,0x58 → D20_STORE +0x54 3→2 → `+0x4c 0→1`;
  a second insert (count 1) shifted +0x58←+0x54 and made count 2. The chooser then re-opens with the
  slot advanced (`m53e6:94` PRESHOW slot=2 mode=5). Exactly M53d's static prediction: mode 5 →
  handler 0x4187a2 pushes param_2=1 → `FUN_00417d20` insert-with-shift.
- **OPEN: REPLACE never fires.** Five REPLACE clicks (count 0; and count 1 ∧ slot 1 with selections
  returning edi=2 / edi=0) wrote no mode and hit the reject tail 0x496a91 (`BAR_IGNORED` probe,
  `m53e6:63,111`); the two mode-7 stores sit behind `cmp [sub+0xa774],-1` and that field (0x6b4610)
  is NOT the icon selection (live reads 5/17 while POST_PICK returned 2). M53d's single mode-7 hit
  (`m53d7_watch.log:47-51`) is therefore still unexplained. Also live: one bar click runs the bar
  handler TWICE (press + release) — mode store, then 0x496a91.
- **8 rows vs cap 9 reconciled:** rows 1..8 = pending slots +0x54..+0x70 (row text y = 439+12·(row−1),
  x 143-248); the 9th pending slot +0x74 has NO row (the insert-shift covers +0x58..+0x74 plus the
  store at +0x54); the head +0x50 is the LEFT panel (head 3 ↔ "TRANSPORT FOIL" ↔ `m53b_types.tsv:4`).
  Row clicks clamp `slot = min(row, count+1)` and zero `pane+0x3ff60` (`shard_001.c:2133-2140`).
- **Harness:** gdb breakpoint `printf` is block-buffered when stdout is a file — m53e1 lost EVERY
  event at SIGINT although the clicks worked; arm through `stdbuf -o0` (`scripts/m53e_drive.py:324`).
  A command-list expression on a non-numeric convenience variable aborts the whole batch and detaches
  silently (`m53e5_watch.log:50`) — bake the base pointer as a literal (`set $b = BASEPTR`). New kit:
  `scripts/m53e_drive.py --pane 0x6a9480` (mode-field watchpoint at 0x6b4614), `scripts/m53e_seq.py`
  phases 1/2/2b/3/4 (pixel-based chooser detection, per-step /proc/mem readback timeline).
- **Next:** `NEXT_PROMPT.md` rewritten for session 58; **THE PICK = M53f** (the alpha Cost→`+41` /
  Plan→`+42` loader overrides + the ability bit-1 off-by-1 in `scripts/m53b_costcalc.py`).

## Session 58 (2026-10-24) — M53f: **THE ALPHA `#UNITS` OVERRIDES ARE DISP8 STORES OFF A record+50 POINTER** — Cost→`+41` at `0x57a037`, Plan→`+42` at `0x57a02d` (inside `FUN_00579f40`, the `#UNITS` loader); `+41` still has exactly ONE store in the image (the formula, `0x595ce7`); the cost calculator is now **188/188 explained, 0 unexplained**

- **Single-writer census redone on a linear disassembly, not the corpus.** `objdump -d -M intel --section=.text programs/terran.exe` (790,702 lines, regenerable; the 40 MB dump is deliberately NOT committed) → 30 references to `0x98adb1`, exactly **one store**: `0x595ce7 mov BYTE PTR [esi+0x98adb1],al` right after `call 0x595820` (`evidence/m53f_adb1_refs.txt`, 30 lines). The other 29 are reads. The corpus claim (`shard_015.c:9358`, `FUN_00595b10 @ 0x595b10`) survives — now instruction-verified.
- **Why no corpus grep ever found the override:** the `#UNITS` loader keeps `undefined2 *puVar10 = &DAT_0098adba` (= record + 50) and writes its tail fields with negative pointer arithmetic — `*(char *)(p + -4)` = +46, `*(char *)((int)p + -9)` = +41 (`shard_014.c:21402`, `:21405`). So neither `&DAT_0098adb1[...] =` nor `*(x + 0x98ad..)` matches. **Grep disp8 stores off a table-base register as well as literal offsets** (`evidence/m53f_disp8_stores.txt` is that scan).
- Loader field map, VERIFIED (`evidence/m53f_disasm_fn579f40.txt`): Plan→+42 `0x57a02d` (guard ≥0) · **Cost→+41 `0x57a037` (guard: 0 = Autocalculate)** · Carry→+40 `0x57a041` (guard ≠0) · Icon→+46 `0x57a04a` (writes −1 too) · Preq→+50 word `0x57a001` · Name→strcpy via `0x64b9d0` at `0x579fb1`; the builder runs first (`0x57a021 call 0x595b10`), the overrides after. Row cap `0x40` (`0x579f76-0x579f89`) ⇒ designed units (id ≥ 0x40) can never be overridden.
- Live cross-check (pread, ids 0-13 vs `data/alpha.json` #UNITS): `+42 == alpha Plan 14/14`, `+46 == alpha Icon 14/14`, `+40 == alpha Carry` where non-zero and the builder's `FUN_00570860` value otherwise (Transport Foil 2, Unity Foil 1 — both the mode-7 `Transport` weapon).
- **Save/restore pair located:** `FUN_00596850` (load_save_state) copies 48-byte save records into the 52-byte runtime records (loop `0x5973bc-0x597495`); `0x597464 → +41`, `0x59746a → +42` (`evidence/m53f_disasm_597400.txt`). A loaded scenario can carry cost/plan bytes the formula never produced.
- **The ability table IS alpha `#ABILITIES`: 24 rows, stride 28** (loop bounds `0x98ad94`/`0x98ad9c` = base + 24·28): `int[0]` = the cost rule = column 1 verbatim (`[1,0,1,1,2,1,1,1,1,-1,1,2,1,1,1,-7,2,1,-1,1,1,1,1,0]`), `int[2]` (+8) = the 11-char flag string parsed as binary (row 1 `10000111111` = 1087 = 0x43f ✓) — `evidence/m53f_ability_table.txt`.
- **The real M53b gap was the land-chassis loop, not the rule table.** For `chassis+1 ∉ {1,2}` the ELSE branch (`0x59597b-0x5959a6`) runs a second loop over `entry + 8` (NOT +16) and adds +1 for every set ability whose flag word has bit **0x400** (the flag string's first character). Deep Radar (bit 1) has it ⇒ Scout Rover (id128) / Scout Speeder (id390) +1. Pitfall: a hand-decoded jump-table read that dropped entry `0x5958e4` "proved" Ghidra's case labels were shifted by one and broke 10 ECM rows; the raw 28-byte table dump (`evidence/m53f_jumptable.txt`) shows 7 distinct entries in exactly Ghidra's order.
- **Check result:** `rows=188  formula==live +41: 181  alpha-Cost override rows: 4/4  stale/out-of-range records: 3  UNEXPLAINED mismatches: 0` (`evidence/m53f_costcalc_digest.txt`); `python3 scripts/m53b_costcalc.py --legacy` reproduces M53b's model (179 + 4 + 3, exactly 2 unexplained = the two bit-1 rows) ⇒ the land loop is the whole fix. Stale-record rule: chassis ≥ 9 / weapon ≥ 21 / armor ≥ 10 (the shipped `#CHASSIS`/`#WEAPONS`/`#DEFENSES` counts) **or reactor == 0** — all 185 real rows have reactor 1 or 2.
- Safety: static-only session, no game driving; `pgrep -x terran.exe` read-only `/proc/pid/mem` preads only (no kill/pkill).
- **Next:** `NEXT_PROMPT.md` rewritten for session 59; **THE PICK = M53g** (the chooser guard field + REPLACE/mode 7).
