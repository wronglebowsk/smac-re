# Session notes archive — sessions 60-60

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 60 (2026-10-23) — M53h: **THE CHOOSER ENUMERATION HAS A NAMED PRODUCER — `FUN_00596000` + a lockstep Plan-major sort — AND THE SIX BAR BUTTONS ARE AN EMBEDDED CONTROL TABLE AT `chooser+0xb74 + i·0xb4c`** (params −2/7/5/4/−1/0, rects at control+0x13c/0x140/0x144); a queued secret project = **−(index in the 0x984d38 table)**, so guard 12 → −26 = project 26 *Pressure Dome* — write-up `evidence/m53h_findings.md`

- **Producer + order (VERIFIED).** `FUN_00596000(faction)` (shard_015.c:9459-9518, called by the paint at
  0x495583 with `sub+0xa76c` = 3) rebuilds the 128-entry candidate array `DAT_009267e4` (count
  `DAT_009267e0`): `id = (slot & 0x3f) + (slot < 0x40 ? 0 : faction<<6)` ⇒ slots 0-63 shared/alpha ids,
  64-127 **the querying faction's own designed units** (faction 3 ⇒ 192-255). It then sorts the ids in
  lockstep with a local key array via `FUN_005a29a0(0x80, &DAT_009267e4, local_208)` (shard_015.c:9514) =
  a bubble sort that swaps only on strict `<` ⇒ stable. Key (shard_015.c:9493-9497):
  `((ch_tbl[+1] + Plan·0x10)·0x40000) + (0x20 − FUN_00570710(id,f))·0x200 + (8 − ch_tbl[+0])·0x40 +
  (8 − FUN_00570770(armor,f))`, `ch_tbl = 0x92ae80` stride 0x90; unavailable ⇒ 999999999 (alpha) /
  0x34fb5e38 (designed) ⇒ always last ⇒ **Plan-major**. Live array's first 14 ids 195,196,192,194,193,2,
  197,198,3,0,200,1,199,6 have Plan 0,0,1,2,3,3,6,7,7,8,8,9,9,11 (monotone) and the tie-breaks come out
  of the formula (`evidence/m53h_enum_ids.txt`).
- **Paint = filter + append, and the result is a LIST.** `FUN_004954e0` clears counter `+0xa818`
  (0x495534) and guard `+0xa774` (0x495541), runs the 128 slots through `FUN_005a73f0(id, faction,
  baseidx)` (0x4956f4), then loops **secret projects 1..0x47** filtered by `FUN_005a6e70`
  (pseudo:146-210). Every accepted item is appended to the itemlist widget at **chooser-sub +0xa780** =
  **0x6b461c** (`add ecx,0xa780` 0x495aab → `call 0x42ee20(list, item, flags, 0)`): units get
  `flags |= 0x20`, projects `|= 0x10`. Node 16 B: +4 item, +8 detail ptr, +0x10 next, **circular**;
  detail+8 = flags. Guard := counter when the item equals the queue value being edited
  (`id == local_34` / `-local_34 == local_28`).
- **Return encoding = the −26 answer (VERIFIED code + live).** `FUN_00496ad0` tail (shard_009.c:
  15013-15041): guard −1 ⇒ −9999; else `FUN_004026b0(guard)` selects the node and
  `(detail+8 & 0x20) == 0 ⇒ return −item`, else `+item`. So a queued secret project is
  **−(index in the 0x984d38 project table, stride 0xc dwords)** — M53a's `|q| = 39 + idx` is superseded.
  Live list dump (`evidence/m53h_list_dump.txt`, count 15 = capacity 5×3): idx 0-8 = 195,196,192,194,193,
  2,0,1,6 (bit 0x20 set), idx 9-14 = projects 2,11,13,26,27,38 ascending (bit 0x10, 0x20 clear); the five
  chassis-3 array units (197,198,3,200,199) are absent — `FUN_005a73f0`'s naval gate
  (`ch_tbl[+1] == 1 && FUN_004e4620(base.x, base.y) == 0`) dropped them. **idx 12 = project 26 = Pressure
  Dome** ⇒ −26 = exactly M53g's `POST_PICK edi` at guard 12. The table is the real project list: 71 =
  "The Ascent to Transcendence" (cost 200), 39 Human Genome, 29 Aerospace Complex (`evidence/
  m53h_project_names{,2}.txt`) — so M53c's −29 head value is probably Aerospace Complex (INFERRED).
- **The button table (VERIFIED live + code).** Six embedded button controls (class vptr 0x67194c) at
  `0x6a9e9c + 0xb74 + i·0xb4c` (i 6,7 idle): param at **+0xa78**, rect at **+0x13c/0x140/0x144**
  (mirrored +0x15c/0x160/0x164). Live: i0 −2 CANCEL 569→669 · i1 7 REPLACE 260→360 · i2 5 INSERT 363→463
  · i3 4 DELETE 466→566 · i4 −1 OK 157→257 · i5 0 HELP 54→154, all y 332 h 0x14
  (`evidence/m53h_button_live.txt`). Built each open by `FUN_00496ad0` (shard_009.c:14909-14993):
  btnW `sub+0xb70` = 100, count `sub+0xb6c` = 6 when `sub+0xb68 != 0` else 4/5 (`sub+0xb68` = the queue
  slot opened on; 0 = the head ⇒ no DELETE/INSERT/REPLACE), y = rows·cellh + 8 = 332, first x =
  `((W − 0x20) − 103·count)/2 + (count−1)·103` with W = `sub+0xa824` = 758 ⇒ 569, pitch 103 (⇒ 3 px
  gaps), creation right→left −2,4,5,7,−1,0 via `FUN_005f9e85(caption, param, x, y, w, h, owner, 0)`
  (the factory that stores the param at +0xa78, shard_019.c:2065); release dispatch `FUN_005fab08`
  (shard_019.c:2500-2540) forwards that param to owner-vtable+0xa8. Labels are NOT in Script.txt:
  `*(DAT_00997b20+0x198/0x728/0x72c/0x194/0x19c)` + `FUN_00409690(0x3fa)` for REPLACE, all `CharUpperA`.
- **Click map reconciled (INFERRED):** one origin offset **+36 px** fits every click M53g recorded
  (REPLACE claims 365 but not 397 ⇒ ≤37; DELETE claims 602 ⇒ ≥36): HELP 90-190 · OK 193-293 · REPLACE
  296-396 · INSERT 399-499 · DELETE 502-602 · CANCEL 605-705. The 3 px gaps between rects are where the
  grid hit-test steals the click = M53g's "phantom cell 17"; M53e's "dead zone 381-421" was extrapolated
  from a single 397 click.
- Safety: static + one read-only `/proc/pid/mem` pass (pid 2124624, year 2371, cur 3, nb 75 unchanged);
  no gdb, no clicks, no signals. Pitfall: the itemlist header is +8 head / +0xc cursor / **+0x10 count**
  — reading count as `+0xc` gives a cursor value and a 79-million-iteration walk (2 timeouts).
- **Next:** `NEXT_PROMPT.md` rewritten for session 61; **THE PICK = M53i** (the secret-project table
  0x984d38/0x984d44 + `FUN_005a6e70`'s gate and return + the −29 head value).
