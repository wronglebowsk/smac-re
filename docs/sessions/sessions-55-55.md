# Session notes archive — sessions 55-55

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 55 (2026-10-23) — M53d: THE PENDING-QUEUE WRITER IS `FUN_00417d20` — 0x417e04 `mov [base + slot·4 + 0x50], item` (hw-watchpoint: `pc=0x417e08`, +0x54 3→2, +0x4c 0→1); `FUN_00417ee0` itself rewrites ALL TEN slots on chooser-cancel at 0x418636; every writer is REGISTER-indexed, which is exactly why the literal-offset census found nothing

- **The census blind spot (M53d's premise was an artifact, not a fact).** `DAT_0095da64`: 0 hits and
  `DAT_008f0d60 + 0x2a`: 0 hits because NOBODY stores to a literal `+0x54`. The three real writers are
  `mov [eax+edx*4+0x50], ebx` (0x417e04, index in a register), `mov [eax+esi*1], edx` (0x418636, offset
  walked 0x50→0x74 in a loop) and `mov [eax+ecx*1], edx` (0x418751, walked the same way). Grep for the
  *store shape* (`*4+0x50`, `+eax*1]`, `rep movs`) before concluding a field is unwritten.
- **`FUN_00417d20`** (0x417d20, 302 B, `index.csv` row 354, Ghidra `shard_001.c:8833`, disasm
  `evidence/m53d_fn417d20_disasm.txt`) is the queue-slot editor. `edi = [ecx+0x3ff5c]` = the **UI-selected
  slot index** held in the base pane's UI object (`ecx = this`, `:6`); `[ebp+0x8]` = item id (→ `ebx`),
  `[ebp+0xc]` = **insert-vs-replace flag**. Stores: **0x417e04** `mov [eax+edx*4+0x50], ebx` writes
  `queue[ui_slot]` (slot 1 → +0x54 … slot 9 → +0x74) — `:75`; **0x417dd8** insert-shift `queue[k] :=
  queue[k−1]`, k = 9 down to slot+1, only when param_2 ≠ 0 (`test [ebp+0xc],0; je 0x417dfe` 0x417dbb) —
  `:62`; **0x417dad** delete-shift (negative/secret ids) — `:49`; count stores 0x417df6 (cap 9) `:72` and
  0x417e1d (`count := count+1` when slot > count) `:83`. Slot 0 (`edi == 0`) and slot 9 early-return at
  0x417d2b/0x417d33 — the head is not edited here. Its only corpus caller is `shard_001.c:9275`, inside
  `FUN_00417ee0`.
- **The dispatch is a chooser-mode jump table.** `FUN_00417ee0` reads `[pane+0xb194]`, `dec`, `cmp 6`,
  `ja 0x4187be`, then `jmp [eax·4 + 0x419c04]` (`evidence/m53d_jumptable.txt`: modes 1..7 → 0x418c51,
  0x418cc9, 0x418cd8, 0x418703, 0x4187a2, 0x418703, 0x4187ad). **Mode 5 → 0x4187a2** pushes 1 and
  **mode 7 → 0x4187ad** pushes 0, both falling into 0x4187b6-0x4187b9 `push item; mov ecx,pane;
  call 0x417d20` (`evidence/m53d_fn417ee0_disasm.txt:550`) — i.e. mode 7 = REPLACE in place, mode 5 =
  INSERT with the shift. **Mode 4/6 → 0x418703**: if `slot ≤ [base+0x4c]` shift `queue[k] := queue[k+1]`
  (0x41874d-0x418751, `:514`) and `+0x4c--` (0x418766, `:521`) = REMOVE; if `slot > count` clamp the slot
  field and just redraw (0x41873a `call 0x416080`). Modes 1/2/3 (0x418c51/0x418cc9/0x418cd8, `:877, :913,
  :921`) funnel to 0x418cda → `0x43f470(0x71df20, owner)` availability test → `jmp 0x4184d7` = re-open the
  chooser. **Mode 0 skips the table entirely** (`ja 0x4187be`) and reaches only 0x4187ef (set
  `+0x30 |= 0x800000`, clear `+0x38 & 0x40000000`) then 0x418819 `jne 0x418b29` — the tail — **writing
  nothing**.
- **VERIFIED live, three independent ways** (our base idx 70 @ 0x962d30, UI window 10485761, gdb armed
  with hw-watchpoints on 0x962d84/+0x54 and 0x962d88/+0x58 plus ~20 silent printing bps, driver
  `scripts/m53d_drive.py --tag m53dN --mode arm --hold` in a tracked background job, stopped with
  `--mode stop`): clicking QUEUE row 1 (185,437) fires `ENQ param1=1 param2=1` — **param_1 IS the slot
  index** — opening the modal chooser (`call 0x496ad0` at 0x41860a, `:425`). Selecting Scout Patrol
  (icon 128,160) and pressing the bar at x=390 returns `POST_PICK edi=2`, `MODE mode=7 slotfield=1`,
  `D20#1 item=2 slot=1`, `D20_STORE dst_off=0x54 old=3 new=2`, and the watchpoint prints
  **`W54#1 pc=0x417e08 val_after=2`** — `$pc` sits one instruction past 0x417e04 ✓ — with `/proc/mem`
  agreeing: `+0x54 3→2`, `+0x4c 0→1` (`evidence/m53d7_watch.log:47-51`, reproduced identically in
  `evidence/m53d5_watch.log:48-51` with gdb's own `Old value = 3 / New value = 2` at `:55-56`).
- **The cancel-restore is the second writer, and it explains the phantom "refill".** The queue is
  snapshotted per call: 0x41820a-0x418222 `ecx=10; edi=[ebp-0x4c]; esi=[base]+0x50; rep movs` +
  `[ebp-0x20] = [base+0x4c]` (`evidence/m53d_fn417ee0_disasm.txt:179`). If the chooser returns −9999
  (`cmp edi,0xffffd8f1` 0x41861b) **and** param_1 ≠ 0, 0x418623-0x41863f walks eax 0x50→0x74 and writes
  `[base+eax] := snapshot` (0x418636, `:438`), then restores `+0x4c` from `[ebp-0x20]`. Caught live:
  ten `RESTORE off=0x50..0x74` lines with `W54#2 pc=0x418639 val_after=3` landing exactly between
  `off=0x54 snap=3` and `off=0x58`, followed by `POST_PICK edi=-9999` / `BRANCH_EXIT`
  (`evidence/m53d7_watch.log:52-64`). This is what makes +0x54 "come back" to 3 after a remove: it is not
  a refill, it is the rollback of an aborted chooser.
- **Empirical bar → mode map** (x-coords in window space, bar row y≈343; the labels the vision pass reads
  are HELP|OK|REPLACE|INSERT|DELETE|CANCEL but the label↔mode pairing is NOT label-verified): x=275 →
  mode 0 (no write), **x=390 → mode 7 → store in place (the append)**, x=505 → mode 4 → remove-shift +
  count-- (memory: `+0x54 2→0`, `+0x4c 1→0`, `evidence/m53d5_watch.log` after-state), x=618 → −9999 →
  restore, x=160 → mode 1 → chooser re-opens (`evidence/m53d8_watch.log:47-48`), x=707 and Return →
  nothing. **Digit keys 1-9 are preview-only**: `FUN_00512b40` calls `FUN_00417ee0(digit, 0)` so param_1 ≠
  0 → mode 0 → the tail, and the pick is dropped. That is why every digit-key attempt in this session
  looked like a silent failure (`POST_PICK edi=2 / MODE mode=0 slotfield=0`,
  `evidence/m53d3_watch.log:42-44`).
- **Complete writer inventory for `+0x54..+0x74`** (the pending slots): 0x417e04 (slot store, VERIFIED),
  0x417dd8 (insert-shift, INFERRED — mode 5 never triggered live), 0x417dad (delete-shift, static),
  0x418636 (cancel-restore ×10, VERIFIED), 0x418751 (mode-4 remove-shift, VERIFIED by state change, not
  watchpoint-captured), plus the known pop shift 0x4ef628-0x4ef639 (M53c) and the +0x50-only writers
  `FUN_004e5560` / `FUN_004e46f0` / `FUN_004e47d0`. `+0x4c` writers: 0x417df6, 0x417e1d, 0x418766,
  0x418641-0x418649 (restore), 0x4ef642 (pop).
- **Harness pitfalls learned (now in the skill):** (1) a gdb watchpoint with **no `commands … continue`
  block** makes `gdb -batch` reach its prompt, end the script and **detach silently** — the rest of the
  run is uninstrumented and the log looks truncated; always give watchpoints a printing `continue` block.
  (2) gdb's own messages are unbuffered while breakpoint `printf` output is block-buffered, so the two
  streams interleave out of order in the log — attribute events by CONTENT (counters, off= sequences),
  never by line order. (3) the vision pass reports true window pixel coordinates; tesseract TSV
  coordinates are internally rescaled and must not be halved — settle geometry with a crop-and-OCR test.
  (4) arm gdb only from a `background=true` call with the driver's `--hold` polling parent (Hermes kills
  children of a finished foreground call).
- **Open threads.** Mode 5 (the 0x417dd8 insert-shift) is proven reachable in code but was never fired
  live — the bar that sets `[pane+0xb194] = 5` is still unidentified, and the 8 visible QUEUE rows vs the
  cap-9 count is unexplained. The bar-label ↔ mode pairing needs a label-verified pass. The −29 head
  value (M53c), the 0x418cda availability test, and `FUN_0059ce10`'s `+0x4c = pop·10/2` (35 > cap 9) are
  all still open.
- **Next:** `NEXT_PROMPT.md` rewritten for session 56; **THE PICK = M53b** (what the type-record `+41`
  byte actually is, static-friendly).
