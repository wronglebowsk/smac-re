# M53g findings — the chooser guard field `[sub+0xa774]` and REPLACE

Live session: gdb via `scripts/m53g_drive.py --tag m53g --pane 0x6a9480` (BARH/GATE/SELWP/MODEWP probes;
log `evidence/m53g_watch.log`, cited below as `log:N`). Static: full linear `.text` census
(`evidence/m53g_a774_all_refs.txt`), `m53g_fn496950_disasm.txt`, `m53g_fn4954e0_pseudo.txt`.
Game pid 2124624, base idx 70 @ 0x962d30. All VERIFIED unless marked INFERRED.

## 1. What `[chooser_sub+0xa774]` (0x6b4610) IS — VERIFIED live

The chooser widget's **selection cell index** in its item enumeration (`-1` = none). Cell index =
position in a 5-column grid (row0 y~60 = cells 0-4, row1 y~160 = 5-9, row2 y~260 = 10-14; the bar row
y~336-352 overlaps phantom cells 15-19, x-col3 = 17). `sub` = pane(0x6a9480)+0xa1c = 0x6a9e9c;
guard = sub+0xa774 = pane+0xb190; mode = sub+0xa778 = pane+0xb194.

Live evidence (log):
- Chooser open (paint): SELWP#1 pc=0x49554b new=-1 (clear), SELWP#2 pc=0x495b06 new=5 — guard :=
  enumeration index of the item in the selected queue slot (slot 1 held Scout Patrol id 2 -> cell 5)
  (log:68-69).
- Icon click (255,160) Colony Pod: SELWP#3 pc=0x4962f2 new=6 (log:70).
- Click (397,343) = phantom cell 17 under the drawn REPLACE bar: SELWP#4 pc=0x4962f2 new=17 (log:71).
- Click (397,320): SELWP#9 new=12 (row-2 col-3 cell) (log:103); chooser then returned edi=-26
  (POST_PICK, log:107) = item at enumeration index 12 (secret-project-range value; encoding detail
  INFERRED).
- CANCEL: SELWP#5/#11 pc=0x496a4d new=-1 (log:74,167).

## 2. Guard writer set — VERIFIED (complete `.text` census: 43 refs of disp32 0xa774, 13 stores)

| site | fn | writes |
|---|---|---|
| 0x495541 | FUN_004954e0 (chooser paint/enumerate, vtable-owner of paint) | `= -1` on every paint (log:68) |
| 0x495b00, 0x495e6f | FUN_004954e0 | `= +0xa818` (enum counter) when enumerated item == queue-slot item (`local_34 = [curbase]+0x50+slot*4`, `m53g_fn4954e0_pseudo.txt:46,140,205`) (log:69) |
| 0x4962ec | FUN_004962a0 = **vtable+0x48 setter** | `= ecx` (cell index from click) (log:70-71,101-103) |
| 0x496432/542/62b/64e/6cb/6ee/708/777 | FUN_004963b0 = vtable+0x60 mutator (sort/swap with +0xa818) | 8 stores, incl. `= 0` at 0x496777 (static only this session) |
| 0x496a43 | FUN_00496950 (bar handler) CANCEL case | `= -1` (log:74,167) |

Reads/gates: bar handler cmps (0x496982/9c9/9f8), chooser cmp 0x496f6f, cmp -1 0x497683, read 0x497707;
paint highlight cmps in FUN_00494cd0 (row highlight `*10`). `+0xa818` = enum counter / swap temp
(stores 0x495534=0, 0x495b1c/5e8b). No other writer exists in the image (`m53g_a774_all_refs.txt`).

## 3. Bar handler FUN_00496950 = vtable+0xa8 — VERIFIED

Only pointer to it: 0x672340 = vptr(0x672298 live)+0xa8. Jump table 0x496a9a indexed `param+2`
(range-check `ja -> 0x496a91` return). Cases: 0=HELP(gate,mode1) 1=mode2 2=gate,mode7 3=mode3
4=mode4 5=INSERT(gate,mode5) 6=mode6 7=mode7 **ungated** -1=OK(mode0) -2=CANCEL(mode0+guard=-1).
Gate = `cmp [this+0xa774],-1; je 0x496a91` (0x4969c9 for case 2, 0x4969f8 for case 5). After any
case: `call [vtable+0xe0]` repaint (0x5ce6ff), then return — **0x496a91 is the shared epilogue return,
reached by mode-storing paths too** (corrects M53e's "BAR_IGNORED = refusal" reading).
One handler run per click (BARH count == click count, log:72,104,113,134,145,164 — corrects M53e's
"runs twice").

## 4. REPLACE FIRES LIVE — VERIFIED

- Click **(365,343)**: BARH#1 param=7 ecx=6a9e9c guard=12 (log:104) -> case 7 ungated ->
  MODEWP#1 pc=0x496a5c val_after=7 (store 0x496a52, log:105) -> POST_PICK edi=-26 (log:107) ->
  dispatcher REPLACE (mode 7 -> handler 0x4187ad) -> **D20_STORE dst_off=0x54 old=2 new=-26**,
  W54#1 pc=0x417e08. Second hit (345,343): same, dst +0x58 old=3->-26 (log:134-137).
- CANCEL then RESTORE x10 from the entry snapshot -> queue back to f4c=2 f50=3 f54=2 f58=2 (verified
  by /proc/pid/mem readback after detach).
- The lone session-56 mode-7 hit (m53d7_watch.log:47) = same param-7 rect, INFERRED.

## 5. Why REPLACE "never fires" at the drawn bar — pinned to instructions

The clickable REPLACE button rect (param 7) is **left of the drawn REPLACE bar**: fires at x 345/365,
NOT at 397; x 381-421 (drawn bar body, label-verified 364-421) is phantom grid cell 17 -> click there
takes the SETTER path (0x4962ec, guard:=17) and never reaches vtable+0xa8 (log:71 then BARH absent
until the CANCEL at log:72; log:163-164 same). Verified rect map (param <- click): HELP 0 <- 160 (M53e)
· OK -1 <- 285 (M53e) · **REPLACE 7 <- 345/365** · INSERT 5 <- 425/440 (log:113,145) and 497 (M53e) ·
DELETE 4 <- 602 (M53e) · CANCEL -2 <- 692 (log:72,164). Dead/phantom: 336(no event), 352/397 ->
setter(17) (log:163). M53e's five REPLACE clicks at 397 all hit cell 17; their `BAR_IGNORED` events
came from the exit clicks (epilogue, §3). Params 1/2/3/6 (modes 2/7-gated/3/6) are mouse-unreachable
from this widget — consistent with M53e "modes 2/3/6 static-only"; the case-2 gate is never exercised
by mouse (REPLACE = case 7, ungated — guard irrelevant to REPLACE).

## 6. Kit notes

- `scripts/m53g_drive.py` = m53e_drive + BARH(0x496950: param/ecx/guard) + GATE0/2/5 + SELWP on
  pane+0xb190 (4 hw watchpoints total: SELWP+MODEWP+W54+W58). Stop with `--mode stop --tag m53g`
  (positional tag arg is NOT accepted by this driver).
- gdb watchpoint `$pc` sits past the store (0x495541 -> pc 0x49554b etc.).
- Cell grid geometry: 5 cols; col3 x~360-490 explains phantom 17 at x 397; CANCEL x 692 is outside
  the 5-col grid -> no setter event there.
- Queue state preserved exactly (CANCEL-restore pattern makes armed REPLACE probes non-destructive).

## Open threads (for NEXT_PROMPT)
- Exact button rects of param 7/5 (and why REPLACE's rect sits left of its drawn bar) — Script.txt
  widget record for the chooser dialog, or the button-table builder.
- Enumeration order/contents (guard 12 -> item -26; guard 5 -> Scout Patrol): what fills cells 0-19
  (units + facilities + secret projects mix) and the -26 encoding vs M53a's `|q| = 39 + idx`.
- vtable+0x60 mutator (FUN_004963b0, 8 guard stores) — sort/scroll path, never fired live yet.
- vtable+0x8 FUN_00494c40 (called after OK/CANCEL when slot != 0) and vtable+4 FUN_00494bb0.
- Modes 2/3/6 producers (params 1/3/6: keyboard? other screens?).
