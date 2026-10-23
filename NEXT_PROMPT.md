# NEXT_PROMPT — SMAC RE, session 56

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the
operational kit, and the queued milestone options. Do ONE milestone, checkpoint to `SESSION_NOTES.md`
(+ rewrite this file), then STOP.

## First actions
1. `skill_view('smac-cvr-format')` — harness pitfalls + code atlas.
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — M53d (session 55) is the latest milestone.
3. Live state (kit below): game up (`pgrep -x terran.exe`), our turn open (cur=3), TracerPid 0,
   `kernel.yama.ptrace_scope` = 0, `pgrep -x gdb` empty.

## Footing — base economy + the production UI (M48d → M53d, VERIFIED unless marked)

### M53d (session 55): who WRITES the pending queue — `FUN_00417d20`
- **`FUN_00417d20`** (0x417d20, 302 B, `index.csv:354`, `shard_001.c:8833`, disasm
  `evidence/m53d_fn417d20_disasm.txt`) is the queue-slot editor: `ecx` = base-pane UI object,
  `edi = [ecx+0x3ff5c]` = **UI slot index**, `[ebp+0x8]` = item id → `ebx`, `[ebp+0xc]` =
  insert-vs-replace flag. **0x417e04 `mov [eax+edx*4+0x50], ebx`** writes `queue[ui_slot]` (slot 1 →
  +0x54 … slot 9 → +0x74) (`:75`); **0x417dd8** insert-shift `queue[k] := queue[k−1]`, k = 9 → slot+1,
  only when param_2 ≠ 0 (`:62`); **0x417dad** delete-shift (`:49`); `+0x4c` stores 0x417df6 (cap 9,
  `:72`) and 0x417e1d (`count+1` when slot > count, `:83`). Slot 0 / slot 9 early-return (0x417d2b,
  0x417d33) — the head is never edited here. Only caller: `shard_001.c:9275`, inside `FUN_00417ee0`.
- **Why the census missed it:** every writer is REGISTER-indexed (`[eax+edx*4+0x50]`, or a loop walking
  0x50→0x74) — `DAT_0095da64` / `DAT_008f0d60 + 0x2a` (0 hits) proved nothing. Grep store SHAPES
  (`*4+0x50`, `+eax*1]`, `rep movs`), not literal offsets.
- **`FUN_00417ee0`'s param_1 IS the slot index** (QUEUE row 1 → `param1=1 param2=1`). Chooser =
  `call 0x496ad0` at 0x41860a (`evidence/m53d_fn417ee0_disasm.txt:425`), returns the item id or −9999
  (`cmp edi,0xffffd8f1`, 0x41861b). The answer dispatches on `[pane+0xb194]` (`dec`, `cmp 6`,
  `ja 0x4187be`) via the table **0x419c04** (`evidence/m53d_jumptable.txt`): 1→0x418c51, 2→0x418cc9,
  3→0x418cd8, 4→0x418703, 5→0x4187a2, 6→0x418703, 7→0x4187ad. **Mode 5 pushes 1 / mode 7 pushes 0**
  then 0x4187b6-0x4187b9 `push item; mov ecx,pane; call 0x417d20` (`:550`) = INSERT-with-shift /
  REPLACE-in-place. **Mode 4/6 → 0x418703**: if `slot ≤ [base+0x4c]` shift `queue[k] := queue[k+1]`
  (0x41874d-0x418751, `:514`) and `+0x4c--` (0x418766, `:521`) = REMOVE; else clamp `[ecx+0x3ff5c]` and
  redraw (`call 0x416080` 0x41873a). Modes 1/2/3 converge at 0x418cda → `0x43f470(0x71df20, owner)` →
  `jmp 0x4184d7` re-open. **Mode 0 skips the table** → 0x4187ef (`+0x30 |= 0x800000`,
  `+0x38 &= ~0x40000000`) → 0x418819 `jne 0x418b29` = tail, **writes nothing**; the head store 0x418b57
  (+0x50) fires only on the `param_1 == 0` path.
- **VERIFIED live** (base idx 70 @ 0x962d30, window 10485761, hw-watchpoints 0x962d84/+0x54 and
  0x962d88/+0x58 + ~20 printing bps): row 1 → chooser → Scout Patrol (icon 128,160, id 2) → bar x=390 →
  `POST_PICK edi=2`, `MODE mode=7 slotfield=1`, `D20_STORE dst_off=0x54 old=3 new=2`, watchpoint
  **`W54#1 pc=0x417e08 val_after=2`** (`$pc` sits one insn past the store), `/proc/mem` `+0x54 3→2`,
  `+0x4c 0→1` (`evidence/m53d7_watch.log:47-51`, `evidence/m53d5_watch.log:48-51, :55-56`).
- **Cancel-restore is the second writer — and the "phantom refill".** Snapshot per call:
  0x41820a-0x418222 `ecx=10; edi=[ebp-0x4c]; esi=base+0x50; rep movs`, `[ebp-0x20] = [base+0x4c]`
  (`:179`). On `param_1 ≠ 0` ∧ pick == −9999, 0x418623-0x41863f walks eax 0x50→0x74 writing
  `[base+eax] := snapshot` (0x418636, `:438`) and restores `+0x4c`. Live: ten `RESTORE off=0x50..0x74`
  lines with `W54#2 pc=0x418639 val_after=3` between `off=0x54 snap=3` and `off=0x58`
  (`evidence/m53d7_watch.log:52-64`).
- **Bar → mode map** (window px, bar row y≈343; labels read HELP|OK|REPLACE|INSERT|DELETE|CANCEL but
  label↔mode is NOT label-verified): 275→mode 0 (nothing), **390→mode 7 = the append**, 505→mode 4 =
  remove (`+0x54 2→0`, `+0x4c 1→0`), 618→−9999→restore, 160→mode 1 (re-opens,
  `evidence/m53d8_watch.log:47-48`), 707 and Return → nothing. **Digit keys 1-9 are preview-only**
  (`FUN_00512b40` → `FUN_00417ee0(digit, 0)` → mode 0, pick dropped, `evidence/m53d3_watch.log:42-44`).
- **Writers of `+0x54..+0x74`:** 0x417e04 (VERIFIED), 0x417dd8 (INFERRED — mode 5 never fired live),
  0x417dad (static), 0x418636 (VERIFIED), 0x418751 (state-change verified), + the pop shift
  0x4ef628-0x4ef639. `+0x4c` writers: 0x417df6, 0x417e1d, 0x418766, 0x418641-0x418649, 0x4ef642.
- **UI geometry** (800×600): QUEUE rows 1-8 at x≈185, y = 437 + 14·(row−1); CHANGE ≈(185,552), HURRY
  ≈(185,571); chooser overlay x 60-740 y 8-330, 5×3 grid (cols ≈128/255/383/510/638, icon rows
  y≈60/160/260), bar row y≈343.

### M53c (session 54): the dequeue
- **+0x4c = PENDING-entry COUNT** (not "last used index"); entries = `+0x4c + 1`, head at +0x50, pending
  from +0x54, UI cap 9 ⇒ the 10-dword `+0x50..0x73` array. **THE POP = `FUN_004ef5d0(base_idx)`**
  (244 B, `evidence/m53c_fn4ef5d0_disasm.txt`, `shard_012.c:20538`): returns 0 if `+0x4c == 0`;
  `dec BYTE [0x94de84 + owner·0x20bc + head]`; shift `slot[i-1] := slot[i]` (0x4ef628-0x4ef639);
  `+0x4c--` (0x4ef642); re-validates the new head (`0x5a73f0` / `0x5a6e70`) and pops again if
  unavailable; head ≤ −39 ⇒ `0x446250(0x24)`; redraw `0x473760(x,y,2,2)`. Only callers 0x4ef992 /
  **0x4f037b** / 0x4f0f46, all inside `FUN_004ef6d0`.
- **Pop vs re-pick fork** (0x4f033e-0x4f037b): `+0x30 |= 0x800000`, `&= 0x7fffffff`, then
  `test (1<<owner), [0x985b10]` → in mask ⇒ POP at 0x4f037b, else `jmp 0x4f0589 FUN_004e5ae0`. Owner 3 ∈
  0xff08 ⇒ pop. Live: `WP50 eip=0x4ef62e 2→3`, `WP4C eip=0x4ef648 1→0` (`evidence/m53c_watch.log:144-147,
  :161`); POP @ 0x4f037b pinned between CLAMP1 and the shift (`evidence/m53c2_watch.log:42-45`); the six
  re-pick sites + tail clear: **0 hits**.
- With `+0x4c == 0` NOTHING consumes the head ⇒ a payable head re-completes EVERY round (the standing
  item IS the repeat-build state). `FUN_004e5560` (`shard_012.c:14625`) is the only +0x50 setter, reached
  only from `FUN_004e5ae0` (30 KB AI planner, `shard_012.c:24338`): 122 re-picks on 40+ other bases, 0 on
  ours; new heads are facility ids plus **−29 ×7** (outside the −(39+idx) band, unexplained).
  `FUN_004e46f0` / `FUN_004e47d0` seed +0x50 at base creation.

### M53a / M52b / M52a (sessions 51-53)
- `+0x44` = active-item mirror (`0x4f5a70` copies `+0x50 → +0x44` after the pipeline and snapshots
  `[base+0x98] := storage`, `shard_012.c:24184-85`). Queue encoding
  (`evidence/m53a_qgate_disasm.txt:5-55`): `−38` = empty, `≥ 0` = item id (unit `< 0x40`, facility
  `≥ 0x40`), `< 0` = secret project `|q| = 39 + idx` (registry `0x985b3c`, 33 dwords, written by
  0x4f0d83). **Completion is PAYMENT-DRIVEN, no progress counter**: COMPLET 0x4efe41 fires the instant
  `storage ≥ factor × 0x5ac950(id, idx, 0)`; PROGDIV 0x4efd49 formats an ETA. Dispatch: unit → SPENDA;
  facility → set bit 2 of word `[0x98adb8 + 52·id]`; cls-8 Colony Pod ∧ pop==1 → ABANDONBASE `0x48ee00`.
  IADD gate: `storage += d0` iff `d0 ≥ 0 ∧ queue ≠ −38 ∧ (f30 & 2) == 0`.
- SPENDA `edi` = `0x4e40a0(owner,1,−1) × 0x5ac950(id, idx, 0)` = 10 for our queued Scout Patrol
  (`m52b_watch.log:386-400`); `0x5ac950` returns the type-record **+41 byte** (`0x98ad88 + type·52`,
  clamped [1,999] only for class 8); `0x4e40a0` arg2==1 → government multiplier (×1 for us). Scout
  Patrol = class 3, **+41 = 1, +43 = 10** → M53b open. `0x4ee410` owns only +0x3c/+0x6/+0x7; +0x40
  writers = SPENDA 0x4efee0 + CLAMP1 0x4eff23; clamp `= max(0, min(base+0xd0, cap 0x92a370=10))`.

### Standing (do not re-derive)
- Storage writers: IADD 0x4ef7f6, SPENDA 0x4efee0, CLAMP1 0x4eff20/23, CONVST 0x4f2d7d (our base always
  early-returns in `0x4f26e0`). **The sweep never truncates** (M50b): `0x520540` reloads n_bases per
  iteration, year store 0x51f554 fires between passes, the base array SLIDES ⇒ locate by NAME.
- Base record: x u16@0, y u16@2, owner@4, pop@6, f18/f1c/f20/f28/f30, +0x3c progress, minerals@0x40, 44
  (item mirror), **4c (pending count, cap 9)**, **queue @0x50..0x73**, 8a/8c facility bitmap, 98 (storage
  snapshot), c0 (== pop, unresolved), cc@0xcc (−3 for us), d0@0xd0, fc@0xfc, f38 = 0x00dfbe41.
- Type record `0x98ad88 + type·52`: name +0[34], **+0x29 (41)**, +0x2a (42) class, **+0x2b (43)**, +0x30
  word facility built-flag, ability +32, domain +36. Live: 0 Colony Pod (cls 8, 3/40), 1 Formers (cls 9,
  2/41), 2 Scout Patrol (cls 3, **1/10**), 3 Transport Foil (cls 7, 3/39). Upkeep table
  `0x984d44/0x984d48 + item·48`; per-player item counts are BYTES at `0x94de84 + player·0x20bc + item`;
  secret-project registry `0x985b3c + 4·(0..32)`.
- Income globals: gross 0x745734, upkeep 0x744f28, net 0x7457dc, trade 0x7457d4, food 0x74572c. Year
  0x985b00, turn 0x985afc, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap
  0x92a370 (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array 0x95da10 stride 0x130,
  unit array 0x933278 stride 52, faction records stride 0x20bc.
- Pane object fields **+0x3ff5c = selected queue slot**, **+0xb194 = chooser mode**; `FUN_00416080(this)`
  = redraw; `FUN_00496ad0(pane+0xa1c, base, owner_byte, scratch)` = modal item chooser (3,310 B,
  `evidence/m53d_fn496ad0_disasm.txt`).
- Ghidra types `DAT_008f0d60` as `short *` → pseudocode offsets are DOUBLED (`+0x22` = 0x44, `+0x26` =
  0x4c, `+0x28` = 0x50); `DAT_0095da5c` = +0x4c, `DAT_0095da60` = +0x50.

## Static-reading kit
- Clean 32-bit disasm, no attach: `gdb -batch -nx -q -ex "set architecture i386" -ex "set
  disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` — redirect to `evidence/`,
  grep it, never paste a whole function; line 1 is an arch banner (line N = insn N−1); **coverage-check**
  (`index.csv` size ÷ 3.8 ≈ insn count, last address printed == next function start). Dumps:
  `m53d_fn417d20_disasm.txt` (complete), `m53d_fn417ee0_disasm.txt` (ends 0x419ef1),
  `m53d_fn496ad0_disasm.txt`, `m53d_jumptable.txt`, `m53a_fn_disasm.txt` (INCOMPLETE),
  `m53c_tail_disasm.txt`, `m53c_fn4ef5d0_disasm.txt`. Pseudocode: `scripts/fn.py 0xADDR`. Corpus: `grep -rn <pat> ghidra_out/shard_*.c` then
  `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`. **Grep store SHAPES, not offsets.**
- Live `/proc/<pid>/mem` pread (TracerPid 0): read `0x8f0d60`, walk `0x95da10 + i*0x130` for
  `i < *(0x985af4)`, pull fields, recompute, then arm gdb.

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (now 10485761, 800×600,
  `xdotool getwindowgeometry` confirms). Launch-if-down command is verbatim in the skill. Preflight: no
  gdb, TracerPid 0, `ptrace_scope` 0 (resets on reboot). Read-only state: `scripts/smac_state.py --json`.
  Our base = idx **70** @ 0x962d30 (idx = (addr − 0x95da10)/0x130).
- **Armed UI-driving (M53d recipe)**: `python3 scripts/m53d_drive.py --tag mXX --mode arm --hold 1200`
  launched with **`background=true`** (Hermes kills children of a finished foreground call; `--hold` is
  the polling parent that keeps gdb alive), then drive with `scripts/smac_play.py`
  (`P.WIN = P.find_window()`, `P.click((x,y))`, `P.key()`, `P.freeze(tag)`), pread `/proc/<pid>/mem`
  between clicks, then `--mode stop` (SIGINTs only the pidfile'd gdb, then `kill -CONT`). Sites: ENQ
  0x417ee0, D20 0x417d20/0x417dd8/0x417e04, POST_PICK 0x4186d2, MODE 0x4186ec, SNAP 0x41821a, RESTORE
  0x418633, TAIL 0x418b24, HEAD 0x418b57, SHIFT 0x418751/0x418ac7, CNT 0x418766, probes
  0x418e1d/0x418cc9/0x418cd8/0x419967, QPIPE 0x4ef6d0; hw-watchpoints +0x54/+0x58 (2 of 4 DR slots).
  **A watchpoint MUST carry `commands … continue end`** or `gdb -batch` detaches on the first hit.
- **Round-driving**: `python3 scripts/m53c_drive.py --tag mXX --rounds 3 --budget 1100` (m52b/m53a/m53c/
  m53c2 clean); leaner `scripts/m53c2_drive.py`. Its GDB_TMPL carries sweep 0x520540, YEAR 0x51f554,
  QGATE 0x4ef88b, SPENDA 0x4efed8, IADD 0x4ef7f6, CLAMP1 0x4eff20, CLAMP2 0x4f0ce9, CONVST 0x4f2d7d,
  W3C 0x4efb31/0x4f022b, QPIPE 0x4ef6d0, QCOMPLET 0x4efe41, POP 0x4ef992/0x4f037b/0x4f0f46, the six
  RE-PICK sites, tail clear 0x4f1e3f, writer entries 0x4e5ae0/0x4e5560/0x507ef0/0x5437d0/0x417ee0;
  QPIPE/QCOMPLET are NAME-conditioned via `*(int*)0x8f0d60`.
- Pitfalls (full list in the skill): poke-then-arm (M33), `kill -CONT` after gdb-INT, never Escape on
  title/REALLYQUIT, OCR ≥4 chars, OK-bar ≥1.2 s, transient advisor panes, `$pc` sits PAST the store,
  grep writer prefixes before "nothing fired", **never signal by name** (driver argv matches), `-x`
  scripts end with `continue`. NEW: **gdb messages are unbuffered but breakpoint `printf` is
  block-buffered** — the streams interleave, so attribute by CONTENT, never line order, and read the log
  only after `--mode stop`; **vision-tool pixels are true window coords, tesseract TSV is rescaled** —
  settle with `ffmpeg -vf crop=W:H:X:Y` + OCR on the crop; short* aliasing doubles offsets;
  `*(int*)0x68cbb0` equals the arg of 0x4e5ae0/0x4e5560 while they run (compare to idx 70).
- COMM OFFICER 3-row panes + UNIVERSITY INTELLIGENCE FILES detour: handlers already in the driver.
  Autosaves `programs/saves/auto/Alpha Centauri Autosave N.SAV`, mission year u16 @ file 0x54;
  `scripts/m48d_boot.py` automates LOAD GAME (BackSpace clear must be LOOPED).

## Milestone options (pick ONE)
- **M53b — what the type-record `+41` byte IS (THE PICK).** `0x5ac950` hands SPENDA the `+41` byte and
  Scout Patrol cost 10 only because `0x4e40a0` returned 10, so `+41` (=1) is not the cost. Plan: (a)
  pread `+41`/`+42`/`+43` for every id from `0x98ad88 + type·52` and tabulate by class; (b) read the alpha
  `#UNITS` / `#FACILITIES` blocks in `programs/Script.txt` for the "Cost = 0 ⇒ Autocalculate" rule; (c)
  find what WRITES `+43` (`FUN_004e46f0` is the candidate) and test whether `+41` is the production
  weight used by `FUN_004e5ae0` and the pickers `0x4e4350` / `0x4f5a70`. Name which of weight / cost /
  turns `+41` is, naming a row where `+41` ≠ `+43`.
- **M53e — finish the enqueue UI (dynamic, cheap).** Make **mode 5** fire so the insert-shift 0x417dd8 is
  caught live: build a 2-entry queue (row 1 → bar 390, row 2 → bar 390), re-open row 1 with a different
  item and find the bar/state setting `[pane+0xb194] = 5`; label-verify the six bars (crop-OCR the row at
  y≈343) and reconcile the 8 visible rows with the cap-9 count. Say plainly if mode 5 is unreachable.
- **Later:** the −29 head value; what fires at 0x4ef992/0x4f0f46 (0 hits); `FUN_0059ce10`'s
  `+0x4c = pop·10/2` (35 at pop 7, over cap 9, `shard_015.c:14416`); M50c (base+0xcc = −3), M50d, M50e,
  M51b, base+0xc0.
- **Retired premises, do not resurrect:** "edi = the sweep-entry index"; "0x4e40a0 is just the
  `(1<<p)&mask` test"; "PROGDIV accumulates progress"; "base+0x50 is a single dword"; "+0x4c is the last
  used index"; "the pipeline has no +0x50 writer"; "M53a's dump is complete"; **"+0x54 is written by
  nobody"** (register-indexed writers 0x417e04 / 0x418636 / 0x418751); **"0x417ee0 writes only slot 0"**
  (rewrites all ten on cancel, shifts on mode 4); **"digit keys 1-9 queue an item"** (preview only);
  **"the queue refills itself from the head"** (that is the cancel-restore); **"the chooser bar at x=503
  is OK"**.

## Report style
Findings → SESSION_NOTES.md (dated section) + this file; evidence under `~/reverse/smac/evidence/`; cite
log line numbers for every claim; mark VERIFIED vs INFERRED; end with the next-prompt pointer.
