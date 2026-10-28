# Session notes archive — sessions 109-110

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 109 (2026-10-27) — M69: THE ENQUEUE WRITES AT THE QUEUE WIDGET'S CURSOR. ACCEPTANCE PASS on one real invocation.

**What changed / what is now known.** The BUILD-pane INSERT is not a sort and it does not read a
type-record byte. It is `queue[pos] = item`, `pos = *(int *)(0x6a9480 + 0x3ff5c)` — the widget's
cursor row — with the region shifted up from `pos` and pending bumped (capped 9).

- gdb instrument `scripts/m69_enqueue_gdb.py` (`--arm|--stop|--parse`, TracerPid + ptrace_scope
  guards, drained log). Breakpoints `0x417dbf` / `0x417e04` / the `0x417dd3` shift loop, hw
  watchpoints on slots 1..3, plus the old `0x418a99` dispatch as a control.
- Live log (`evidence/m69_enqueue.gdblog`): **one continuous click flow** produced
  `ENQUEUE obj=0x6a9480 pos=1 pending=2` -> `STORE queue[1]=192` and then
  `ENQUEUE obj=0x6a9480 pos=4 pending=3` -> `STORE queue[4]=193`. Front insert, then end insert,
  same button, same session: the cursor moved.
- The `0x418a99` block (jump table `0x419c20`, case 0 writes `base+0x40`, case 1 shifts+bumps)
  **never fired** in four INSERTs — it is a different handler, and the M67 note that treated the
  `0x418bxx` block as the insert path is superseded.

**Acceptance (one real invocation).**
`python3 scripts/m69_cursor_run.py --cursor 2 --item 193 --trace evidence/m69_cursor3.jsonl`
-> **PASS**, region `[2,192,194]` -> `[2,192,193,194]`, pending 2->3, cursor read back as 2
before the click, `plan_sorted_index 1`. The instrument refuses a shape where the cursor and the
plan index agree (`--cursor 1` -> `FAIL: non-discriminating shape`), so the PASS discriminates.
`python3 scripts/test_m69_cursor.py` -> `PASS 15/15 m69 cursor cases` (offline; pins the store
arithmetic, the plan-vs-cursor disagreement, the M68 appends and both negative stores).

**Correction to session 108.** `-3` was recorded as probably a bad click. It is not: with the
click verified (`guard == cell`) and the cursor poked, item 196 (all-zero record) stored **-6**,
and 195 stored **-3** on a guarded click. A type with no real record is stored as a negative
value; two different negatives, so not one sentinel. Do not use 195/196/197+ in a shape.
Also: the M68 `-3` claim that a poisoned entry makes the next INSERT "append a plan-9 item at the
END" is re-read here as "the cursor had moved to the end", not as a fault.

**Open.**
1. What sets the cursor (`[widget+0x3ff5c]`)? The writers are `0x40b018-0x40b081` (arrow/move
   handler, clamps to `[1, pending]`), `0x4163b6/0x41650e`, `0x417e3b-0x417e7b` (post-insert).
   The chooser click is what a user expects to set it; the log shows it moving on its own
   (2 -> 4 after one insert). An hw watchpoint on the field across ONE insert would name the
   writer and settle whether the widget sorts by plan when it refreshes the list.
2. The widget's LIST order (what M67 measured) — is it recomputed on paint from the plan byte?
   `0x40axxxx` is the queue-widget paint code; that is where the plan comparison should live.
3. `-3 / -6` for recordless types: what is the formula? (two points only.)

**Next pick.** M70 = watch `[0x6a9480+0x3ff5c]` across one INSERT and one queue-list repaint,
then read the widget's paint loop (`0x40axxxx`) for the plan-byte comparison. That closes the
last link: the widget sorts (or not), the user-visible order is that list, and the enqueue just
obeys the cursor.

## Session 110 (2026-10-27) — M70: WHO WRITES THE CURSOR. ACCEPTANCE PASS on one real invocation.

**What changed / what is now known.** The queue widget's cursor field is
`[0x6a9480 + 0x3ff5c] = 0x6e93dc`, and there are exactly **18 instructions in .text that write
it** (`scripts/m70_scan_writers.py` over `scratch/m574/text.txt`). Three of them fired in one
real click flow, and every logged write is now attributed:

- **`0x40aae5`** `mov [edi+0x3ff5c],eax` inside the queue-LIST row handler `FUN_0040a990`
  (read at `0x40aa22`): `cursor = min(clicked_row, [[0x8f0d60]+0x4c] + 1)`. **A click on a queue
  row DOES set the cursor** — the user's cursor-setter is the row click, not the enqueue.
- **`0x417e3b`** `mov [ecx+0x3ff5c],eax` — the enqueue tail: `eax = [[0x8f0d60]+0x4c] + 1`
  (`0x417e2d` load, `0x417e3a` inc), i.e. after an INSERT the cursor parks at rows+1.
- **`0x4194b3`** `mov [ebx+0x3ff5c],0x0` — a handler that sends the widget message `0x4d00`
  (`push 0x4d00; call 0x584010` at `0x4194a4`, with `eax = 0xffffffd9 - edi` and
  `edx = 0xffffffd9 - ecx`, the -39 sentinel) and then **zeroes the cursor unconditionally**.
  This is why the cursor read back 0 after the run.
- Reads (not writes) at `0x40aa22` (row handler), `0x41650e`, `0x417d25/417dbf/417ddb/417e0e/
  417e62/417eb3` (the enqueue and the move helper), `0x4185ea/418714/41876e`, `0x41e25f`.

**The enqueue arithmetic, pinned to the M69 log** (`test_m70_cursor.py` reproduces all four real
transitions): the shift runs from `min(9, max(pending+1, cursor))` down to `cursor+1` — so the
slot AT `pending+1` moves and slots above it keep their stale values; the store uses the
ORIGINAL cursor (the clamp at `0x417ddb` feeds only the `cmp` at `0x417e17`/`0x417df3`);
`pending++` only when `pending < 9`; `cursor = pending+1` after an insert.

**The cursor is clamped/advanced against the WIDGET'S OWN row count `[[0x8f0d60]+0x4c]`**
(`0x40aa22`, `0x417e14`), not against the base record's pending that `--stop` reads back.
`DAT_008f0d60` is a POINTER to the base record (`0x40ad6c`/`0x40b00a` load it and index `+0x4c`,
`+0x50+4k`); Ghidra flattens it. Reading base pending after the run is not a model check.

**Acceptance (one real invocation).**
`python3 scripts/m70_cursor_watch.py --arm --base-name "University Base"` (cursor 0, pending 0)
-> `m66_insert_slot.py --base-name "University Base" --item-a 193 --item-b 192 --slots 12`
-> `--stop` -> `--acceptance` -> **PASS**: 4 cursor writes, all attributed
(`0x40aae5`, `0x417e3b` x2, `0x4194b3`), values `[1, 2, 3, 0]` each equal to the model's
prediction (row click on row 3 with widget rows 0 -> `min(3, 1) = 1`; tails -> 2 then 3; the
`0x4194b3` handler -> 0); region `[2,0,0,...] -> [2,193,192,...]`, pending 0 -> 2.
`python3 scripts/test_m70_cursor.py` -> **PASS 23/23** (parser against the measured M69 log
lines, the gate's discriminating power, the pc attribution, and the REAL M70 log).

**A PASS is not an outcome — read back.** The queue region was written ONLY by the two enqueue
stores (`SLOT1WRITE/SLOT2WRITE pc=0x417e08`): no paint-time rewrite of the region happened in
the armed window (arm -> 2 INSERTs -> OK -> Escape -> detach). And the row handler indexes
`[[0x8f0d60] + 4*clicked + 0x54]` at `0x40b041-0x40b04c`, i.e. a list row IS a queue slot —
there is no separate row list to sort.

**CONFLICTS reported, not resolved.**
1. **The negative-id table stride disagrees between sites.** `0x40ada8-0x40adae` and
   `0x4164ef-0x4164f5` compute `0x984d38 + (-v)*48` (`lea [r+r*2]; shl 4`), while
   `0x41890a-0x418914` and `0x418943-0x41894d` compute `0x984d38 + (-v)*16` (`shl 4` alone).
   -3 -> `0x984dc8` or `0x9852b8`; -6 -> `0x984e58` or `0x985348`. Not poked, not resolved.
2. **M67's plan-descending LIST order is still unexplained by code.** No site in .text reads the
   plan byte `+42` (`m70_scan_writers.py` finds zero type-record reads with the 52-byte idiom
   except four that just pass the record pointer to `FUN_00626634`/`FUN_006265a2` for the row's
   string). The four type-address sites are `0x40ad92`, `0x4164dd`, `0x4188f9`, `0x418932`.
3. The brief's three standing CONFLICTs (year store `0x51f554`, the pay site, the faction-3 type
   names) were not touched this session.

**Open.** (1) Who calls the `0x4194b3` handler and what message `0x4d00` is (it zeroes the cursor
after a queue mutation — the cheapest candidate explanation for M67-vs-M68 state differences).
(2) The `-3 / -6` formula (two points, three candidate tables). (3) Whether a POP/completion or a
round boundary rewrites the region — the armed watchpoints see it, this run says a repaint does
not. (4) `m66_insert_slot --rules layout` scored `fit = []` on this shape (both inserts landed in
click order at slots 1,2 — the layout rules need a shape where one rule fits and the others do
not); no layout claim was made, and none was needed for M70.

**Next pick.** M71 = arm `m70_cursor_watch` across ONE POP (unit completion) and one round
boundary: the cursor field plus slots 1..3 watchpoints will show whether the engine rewrites or
reorders the region at completion (the M67/M68 discriminator) and whether the `0x4194b3` handler
fires there. Do not click-hunt for a sort key again.
