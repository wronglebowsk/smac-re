# M53h — the chooser enumeration, its producer, and the bar-button table (session 60)

Static-first; one read-only `/proc/pid/mem` pass (pid 2124624, no gdb, TracerPid 0). VERIFIED =
pseudocode/disassembly or live pread; INFERRED = fitted from those.

## 1. Answer in one line

The icon grid is fed by `FUN_00596000(faction)` (shard_015.c:9459-9518), which rebuilds and sorts the
128-entry candidate array `DAT_009267e4` (count `DAT_009267e0`); the paint (`FUN_004954e0`) filters it
per-base, appends secret projects 1..71, and materialises the result as a circular node list at
**chooser-sub +0xa780**; the chooser returns `+item` when the node detail flags have bit 0x20 and
**`−item`** otherwise ⇒ a queued secret project = **−(index in the 0x984d38 table)**, so −26 = project
26 = **Pressure Dome**. The six bar buttons are embedded button controls (chooser-control children) at
**0x6a9e9c + 0xb74 + i·0xb4c**, param +0xa78, rect +0x13c/0x140/0x144, built right-to-left by
`FUN_00496ad0` (shard_009.c:14909-14993) with pitch 103.

## 2. Producer + sort key (VERIFIED, `evidence/m53h_fn596000.txt`)

`FUN_00596000(faction)` — called by the paint at 0x495583 (`evidence/m53g_fn4954e0_disasm.txt:51`)
with the faction held in chooser-sub+0xa76c (= 3, live):
- slot→id: `id = (slot & 0x3f) + (slot < 0x40 ? 0 : faction<<6)` (shard_015.c:9462-9471, store at
  :9488) ⇒ slots 0-63 = the 64 shared/alpha ids, 64-127 = **the querying faction's own designed
  units**.
- build-time availability: record+0x30 bit 0 (`&DAT_0098adb8`), plus `FUN_005a6cd0(prereq, faction)`
  for id < 0x40. Unavailable ⇒ key `999999999` (alpha) / `0x34fb5e38` (designed) ⇒ always last.
- otherwise the key (shard_015.c:9493-9497):
  `((ch_tbl[+1] + Plan·0x10)·0x40000) + (0x20 − FUN_00570710(id,f))·0x200 + (8 − ch_tbl[+0])·0x40
   + (8 − FUN_00570770(armor,f))` — `ch_tbl = 0x92ae80` stride 0x90 (+0/+1), Plan = record+42, chassis
  = record+36, `FUN_00570710` = weapon byte `0x92b950+w·0x10`, `FUN_00570770` = 2 × armor byte
  `0x92fd18+ar·0x10`; a negative table byte ⇒ research-scaled by `FUN_004fe670`.
  ⇒ **ordering is Plan-major**, then weapon, chassis class, armor.
- `FUN_005a29a0(0x80, &DAT_009267e4, local_208)` (shard_015.c:9514) = **lockstep bubble sort** of the
  id array with the key array, swapping only on strict `<` ⇒ stable (`evidence/m53h_fn5a29a0.txt`).
- Live array (`evidence/m53h_9267e4_dwords.txt`, `evidence/m53h_enum_ids.txt`): first 14 ids
  195,196,192,194,193,2,197,198,3,0,200,1,199,6 then 201+ empty; their Plan column 0,0,1,2,3,3,6,7,7,
  8,8,9,9,11 = monotone ✓. Ties reproduced: 193<2 (ch_tbl[+0] 2 vs 1), 198<3 (armor), 0<200 and
  1<199 (ch_tbl[+1] 0 vs 1 at equal Plan).

## 3. The paint's enumeration + gates (VERIFIED)

`FUN_004954e0` (chooser sub = pane 0x6a9480+0xa1c = 0x6a9e9c): clears counter +0xa818 (0x495534) and
guard +0xa774 to −1 (0x495541); `local_34 = cur_base+0x50 + (sub+0xb68)·4` = the queue slot being
edited; calls the producer (0x495583); then
- loop 128 slots (`evidence/m53g_fn4954e0_pseudo.txt:68-144`) filtered by `FUN_005a73f0(id, faction,
  baseidx)` (0x4956f4); accepted items appended via `add ecx,0xa780` (0x495aab) +
  `call 0x42ee20(list, id, flags, 0)` with `flags = local_10 | FUN_00496050(id) | 0x20`
  (pseudo:134-136); guard := counter if `id == local_34` (pseudo:139-141); counter++ (pseudo:143).
- then loop **secret projects `local_28 = 1..0x47`** (pseudo:146-210), filter `FUN_005a6e70(idx,
  faction, baseidx, slot)`; appended with `flags = FUN_004960f0(idx) | 0x10` (no 0x20, pseudo:199-201);
  guard := counter if `-local_34 == local_28` (pseudo:204-206); project 38 has a special display
  (pseudo:173-180).
- `FUN_005a73f0` gate set (`evidence/m53h_fn5a73f0.txt`): record+0x30 bit 0; record+0x2c per-faction
  exclusion mask; Plan == 8 with `DAT_00985ac4 & 0x400000`; **designed + `ch_tbl[+1] == 1` +
  `FUN_004e4620(base.x, base.y) == 0` ⇒ false** (the naval/sea-access gate); designed ownership
  `id>>6 == faction`; alpha ids go through the prereq word (record+50) and the tech table
  `0x92fdd4` stride 0xb.

## 4. The materialised list + the −26 encoding (VERIFIED live + code)

List object = chooser-sub+0xa780 = **0x6b461c** (vtable 0x67333c): +8 head, +0xc cursor, +0x10 count.
Node (16 B, vtable 0x67143c): +4 item number, +8 detail pointer, +0x10 next, **circular**. Detail+8 =
flags. `FUN_004026b0(index)` walks head→index and sets the cursor; `FUN_00401940()` = node+4;
`FUN_00495480()` = detail+8.
Return (`FUN_00496ad0` tail, shard_009.c:15013-15041): guard == −1 ⇒ −9999 (or 0 when sub+0xa778 ≠ 0);
else `FUN_004026b0(guard)`; `if ((flags & 0x20) == 0) return −item; else return item`.

Live dump (`evidence/m53h_list_dump.txt`, count 15 = capacity 5×3): idx 0-8 = items 195,196,192,194,
193,2,0,1,6 (flags a1,a1,a1,a1,20,20,20,22,21 — bit 0x20 set); idx 9-14 = items 2,11,13,26,27,38
(flags 12,12,12,12,13,12 — bit 0x10, 0x20 clear), projects ascending. The five chassis-3 array units
(197,198,3,200,199) are **absent** — the sea gate dropped them, their chassis-0/1 twins survived.
**idx 12 = project 26** (`evidence/m53h_project_names.txt`: Pressure Dome, cost 8) ⇒ return −26 =
exactly M53g's `POST_PICK edi = −26` at guard 12.
Names: `evidence/m53h_project_names.txt`. **M53a's `|q| = 39 + idx` is superseded: |q| IS the
project-table index.**

## 5. The bar-button table (VERIFIED live + code)

`FUN_00496ad0` (the modal chooser) builds the row each open:
- `sub+0xb70 = 100` button width (:14886); count = `sub+0xb6c` = **6 when `sub+0xb68 != 0`** (:14917)
  else 4 (+1 under a faction/base flag, :14909-14912). `sub+0xb68` = the queue slot the chooser was
  opened on (0 = the head ⇒ no DELETE/INSERT/REPLACE).
- row y = `rows·cellh + 8` (:14919) = 3·108+8 = **332**; first x = `((W − 0x20) − 103·count)/2 +
  (count−1)·103` (:14921) with W = `sub+0xa824` = 758 ⇒ **569** at count 6; each later x −= 103.
- creation order right→left, each `FUN_005f9e85(caption, param, x, y, w, h, owner, 0)`: −2 :14931 ·
  4 :14963 · 5 :14970 · 7 :14972 (`FUN_00409690(0x3fa)`) · −1 :14985 · 0 :14993; other captions
  `*(DAT_00997b20+0x198/0x728/0x72c/0x194/0x19c)`, all via `CharUpperA`; raw window
  `evidence/m53h_bar_creation.txt`.
  `FUN_005f9e85` = the control factory storing the param at +0xa78 (shard_019.c:2065); release
  dispatch `FUN_005fab08` (shard_019.c:2500-2540) calls owner-vtable+0xa8 with it (params 1/2/3/6
  exist only in the 4/5-button variant).
- Live control table (`evidence/m53h_button_live.txt`; children at 0x6a9e9c+0xb74+i·0xb4c, class vptr
  0x67194c, param +0xa78, rect +0x13c/0x140/0x144, mirrored +0x15c/0x160/0x164):

      i0 0x6aaa10 −2 CANCEL  569→669   i1 0x6ab55c  7 REPLACE 260→360   i2 0x6ac0a8  5 INSERT 363→463
      i3 0x6acbf4  4 DELETE  466→566   i4 0x6ad740 −1 OK      157→257   i5 0x6ae28c  0 HELP    54→154
      (all y = 332, h = 0x14; i6/i7 0x6aedd8/0x6af924 idle).

  Grid live: cols `+0xa810` 5, rows `+0xa814` 3 (= 3 + (screen width > 800), `DAT_00993a00`), cellw
  `+0xa81c` 135 = (758−0x51)/5, cellh `+0xa820` 108, capacity `+0xa82c` 15.
- Click reconciliation (**INFERRED**): the coords above are control-local; one origin offset of
  **+36 px** fits every click M53g recorded (REPLACE claims 365 not 397 ⇒ ≤37; DELETE claims 602 ⇒
  ≥36): HELP 90-190 · OK 193-293 · REPLACE 296-396 · INSERT 399-499 · DELETE 502-602 · CANCEL 605-705.
  The 3 px gaps between rects (397-398 …) are where the grid hit-test steals the click = M53g's
  "phantom cell 17"; M53e's "dead zone 381-421" was extrapolated from one 397 click.

## 6. Open

`FUN_004fe670` key terms (108 empty/disabled rows); `FUN_005a6e70`'s return (indexes the cost table);
does the itemlist cap at capacity (live = 15)?; who draws the bars M53e measured (57-80 px vs 100 px
rects); 4/5-variant labels/params 1·2·3·6; −29 head value; sibling builder `FUN_00596160`.
