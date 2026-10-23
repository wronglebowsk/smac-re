# M53e findings — the enqueue chooser: bar labels, who writes the mode field, mode 5 live

Logs: `evidence/m53e2_watch.log` (bar sweep, empty queue), `m53e3` (build/queue),
`m53e4` (per-bar sweep with a selection), `m53e5` (gdb script aborted), `m53e6` (REPLACE vs
INSERT semantics), `m53e*_timeline.txt` (click timeline + /proc/mem readbacks),
`m53e_grid_pre.txt` (crop-OCR labels + blue-pixel runs + chooser grid),
`m53e_fn496ad0_bars.txt` (the mode-store sites), `m53e_fn496ad0_switch.txt` (the store tail).
Scripts: `scripts/m53e_drive.py` (armed driver + `--pane` mode-field watchpoint),
`scripts/m53e_seq.py` (phases 1/2/2b/3/4).

## 1. The "pane+0xb194 mode field" is really the CHOOSER sub-object's +0xa778  (VERIFIED)
* Pane object (the base-pane UI object, `ecx` of `FUN_00417ee0`, `mov ebx,ecx` @0x417f03) =
  **0x6a9480** — live, `m53e2_watch.log:72` (`MODE pane=0x6a9480`); static BSS (>0x6a9000), so the
  address is fixed for the process lifetime.
* Byte scan of `.text` (file 0x1000..0x2703f4 = VA 0x401000..0x671000) for disp32 `94 b1 00 00`:
  **exactly one hit**, 0x4186ea = the read `mov eax,[ebx+0xb194]` @0x4186ec. No instruction in the
  whole image ever stores through `pane+0xb194` — that is why the corpus has zero `b194` stores.
* The stores are `[reg+0xa778]` **inside the chooser `FUN_00496ad0`**, with `reg = pane+0xa1c`
  (0x6a9e9c): 0x6a9e9c+0xa778 = 0x6b4614 = 0x6a9480+0xb194. Proof = the hardware watchpoint on
  0x6b4614 firing at the pc immediately after each store (see §3).
* Store sites (`m53e_fn496ad0_bars.txt:11-48`): 0x496993→1, 0x4969a5→2, 0x4969b7→3, 0x4969da→**7**,
  0x4969e9→**4**, 0x496a09→**5**, 0x496a18→6, 0x496a27→0, 0x496a36→0, 0x496a43→`[+0xa774]=-1`,
  0x496a52→**7**. Guards at 0x496982 / 0x4969c9 / 0x4969f8:
  `cmp [reg+0xa774],0xffffffff; jne <store>; jmp 0x496a91` (reject tail). After a store the cases
  `jmp 0x496a60` → `call [vtable+0xe0]` then test `[sub+0xb68]` / `param==-1|-2`
  (`m53e_fn496ad0_switch.txt:47-61`).

## 2. Bar labels + hit ranges  (VERIFIED: 6x crop-OCR + blue-pixel run scan)
`m53e_grid_pre.txt`, "bars:" line: `HELP@107 REPLACE@346 INSERT@449 DELETE@553 CANCE!@653`
(OK is 2 chars, unOCRable; vision confirms it sits between HELP and REPLACE). Blue-run scan of
y=343 in `/tmp/m53e_chooser.png` gives the six bars (label text drawn INSIDE the bar, body y 336-352):
**HELP 153-233, OK 252-311, REPLACE 364-421, INSERT 472-523, DELETE 556-636, CANCEL 659-705.**
So M53d's unverified label guess is corrected and its clicks re-map: 160=HELP, 275/285=OK,
390/397=REPLACE, 505/497=INSERT, 618/602=DELETE, 707/692=CANCEL.
Chooser bar fill = RGB (103,91,181); the same pixel is (0,0,0) when the chooser is down →
instant chooser-open detector, no OCR (`scripts/m53e_seq.py:bar_px`).
Chooser grid (same file + vision): icon rows y = 60/160/260, cols x = 128/255/383/510/638;
row 2 = Scout Patrol / Colony Pod / Formers / Probe Team / Children's Creche.

## 3. Bar → mode map  (hardware watchpoint on 0x6b4614; `$pc` sits PAST the store)
| bar | mode | store site | live MODEWP pcs |
|---|---|---|---|
| INSERT | 5 | 0x496a09 | m53e3:109, m53e4:98, m53e6:78, m53e6:126 |
| DELETE | 4 | 0x4969e9 | m53e3:190, m53e4:141 |
| HELP | 1 | 0x496993 | m53e3:219, m53e4:219(#5), m53e4:#6 |
| (entry/OK/CANCEL reset) | 0 | 0x496a27 / 0x496a36 | m53e3:125,194; m53e4:49,114,145; m53e6:95,142 |
| REPLACE | 7 | 0x4969da / 0x496a52 | **never seen live** (§5) |
Modes 2 (0x4969a5), 3 (0x4969b7), 6 (0x496a18) are static-only.
* **CANCEL** = `mov [sub+0xa774],-1` (0x496a43) → chooser returns −9999 → dispatcher rewrites
  `+0x50..+0x74` from the stack snapshot (RESTORE ×10, bp 0x418633/0x418636) and exits at 0x419967
  **without ever consulting the mode field** (`m53e2:48-59`, `m53e4:60-61`). This is M53d's
  "phantom refill" second writer.
* **OK** returns the selection with mode 0 → dispatcher tail → writes nothing
  (`m53e4:169-171`) and does NOT restore the snapshot, so an already-committed edit survives an OK
  exit (`m53e6` after-OK: `+0x4c` stays 1, then 2).
* **HELP** (mode 1 → 0x418cda) opens the **unit-design pane** for the selected item (bars
  RENAME/OBSOLETE/UPGRADE/CANCEL at y=356, CANCEL x≈614); its CANCEL re-opens the chooser
  (`m53e4:208-210` + the screen OCR).

## 4. MODE 5 FIRES LIVE — the milestone goal  (VERIFIED)
INSERT bar (x 472-523) with a selection, slot 1:
`m53e6:77-92` = PRESHOW slot=1 mode=0 → **MODEWP mode=5 @pc 0x496a13** → POST_PICK edi=2 →
MODE mode=5 → D20#1 item=2 slot=1 → **D20_SHIFT dst_off = 0x74,0x70,0x6c,0x68,0x64,0x60,0x5c,0x58**
(8 shifts; 0x58 old=0 new=3 = the old head value sliding up) → **D20_STORE dst_off=0x54 old=3 new=2**
→ `+0x4c 0→1`. Second insert with count=1 (`m53e6:125-134`): +0x58 ← +0x54 (=2), store 2 at +0x54,
count 1→2 (memory `f54=2 f58=2`). The chooser then **re-opens with the slot advanced**
(`m53e6:94` PRESHOW slot=2 mode=5 f4c=1; `m53e3:124` identical).
⇒ M53d's static prediction is confirmed: mode 5 → handler 0x4187a2 pushes param_2=1 →
`FUN_00417d20` insert-with-shift at 0x417dd8. Mode 5 is the **INSERT** bar; it is reachable.

## 5. REPLACE (mode 7) did NOT fire in five attempts — OPEN
Attempts: m53e4 step 1 (session open at arming), m53e5 steps 1/3/4/8, m53e6 with count=0
(edi=2 returned) and with count=1 ∧ slot=1 (edi=0 = Colony Pod returned). Every one produced
**no mode write** and hit the reject tail 0x496a91 (`BAR_IGNORED` probe, m53e6:63 and :111).
The two mode-7 stores sit behind `cmp [sub+0xa774],-1` guards, and that guard never passed.
`[sub+0xa774]` (0x6b4610) is **not** the icon selection: live reads returned 5 and 17 while
POST_PICK returned 2 (`m53e4` timeline vs `m53e4:99`). INFERRED: it is some other chooser state
(a replace-target / row descriptor) that the QUEUE-row path never fills, which also leaves
M53d's single mode-7 hit at x=390 (`m53d7_watch.log:47-51`) unexplained.
Also live: **a bar click runs the handler twice** (press + release) — the mode store happens on the
first pass and 0x496a91 on the second (`m53e6:78-79` MODEWP then BAR_IGNORED).

## 6. 8 QUEUE rows vs cap 9 — reconciled
* Row click clamps `slot = min(row_index, count+1)` and zeroes `pane+0x3ff60`
  (`shard_001.c:2133-2140`, `:2193-2197`, in `FUN_0040a990`).
* The visible list is **8 rows**, row text at y = 439 + 12·(row−1), x 143-248 (crop OCR of the
  closed base pane; the same crop shows 8 numbered rows).
* Pending capacity is 9 dwords `+0x54..+0x74` (M53c/M53d) and the insert-shift covers exactly
  `+0x58..+0x74` + the store at `+0x54` (`m53e6:83-92`) — 9 slots for 8 rows.
* The head `+0x50` is shown in the LEFT panel, not in the list: live head = 3 while the panel read
  "TRANSPORT FOIL" (screenshot `/tmp/m53e_chooser.png`), and id 3 = Transport Foil
  (`evidence/m53b_types.tsv:4`).
⇒ rows 1..8 = pending slots `+0x54..+0x70`; pending slot 9 (`+0x74`) has **no row**; the head is the
left panel. VERIFIED except the 9th-entry invisibility, which is INFERRED (shift range + 8-row layout).

## 7. Harness fixes paid for in this milestone
* gdb breakpoint `printf` is block-buffered when stdout is a file: m53e1's clicks worked but **all
  events were lost at SIGINT** (0 event lines). gdb is now spawned through `stdbuf -o0`
  (`scripts/m53e_drive.py:324`); every later session logged fully.
* A command-list expression on an unset/non-numeric convenience variable aborts the whole batch
  ("Argument to arithmetic operation not a number or boolean", `m53e5_watch.log:50`, inferior
  detached, run silently uninstrumented). Fix: bake the base pointer as a literal
  (`set $b = BASEPTR`) instead of `*(int *)0x8f0d60` per hit.
* Chooser-open detector = pixel (160,343) == (103,91,181).
* `scripts/m53e_drive.py --pane <addr>` bakes a hw watchpoint on `[pane+0xb194]`; the pane is a
  static object (0x6a9480) so the address is stable across screens/rounds.
