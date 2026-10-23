# NEXT_PROMPT — SMAC RE, session 61

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53h (**M53h done, session 60**); open: **M53i (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 60 (M53h) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state (kit below): game up (`pgrep -x terran.exe` → 2124624), year 2371, our turn (`cur == 3`),
   n_bases 75, our base idx **70 @ 0x962d30** ("Climactic Research"), base pane up, chooser closed
   (guard `sub+0xa774` = −1, mode `+0xa778` = 0), its itemlist at 0x6b461c still holding the last
   enumeration (count 15), no gdb, TracerPid 0, `ptrace_scope` 0. Base 70: **`+0x4c = 2` pending =
   two Scout Patrols (`+0x54 = +0x58 = 2`)**, head `+0x50 = 3`. M53i is STATIC-FIRST (project table
   + `FUN_005a6e70` + the −29 head value); read-only preads suffice; arm only if a live head-write
   must be caught.
## Footing — production economy + the chooser UI (M48d → M53h, VERIFIED unless marked)

### M53h (session 60): enumeration producer + bar-button table — write-up `evidence/m53h_findings.md`
- **Producer** `FUN_00596000(faction)` (shard_015.c:9459-9518; paint calls it at 0x495583, faction from
  `sub+0xa76c` = 3) rebuilds the 128-entry array `DAT_009267e4` (count `DAT_009267e0`): `id = (slot &
  0x3f) + (slot < 0x40 ? 0 : faction<<6)` ⇒ slots 0-63 shared/alpha ids, 64-127 **that faction's own
  designed units** (faction 3 ⇒ 192-255); then lockstep-sorts ids with a key array via `FUN_005a29a0`
  (:9514; bubble sort, swaps only on strict `<` ⇒ stable). Key (:9493-9497) `((ch_tbl[+1] + Plan·0x10)·
  0x40000) + (0x20 − FUN_00570710(id,f))·0x200 + (8 − ch_tbl[+0])·0x40 + (8 − FUN_00570770(armor,f))`,
  `ch_tbl = 0x92ae80`/0x90, Plan = record+42; unavailable ⇒ 999999999 (alpha) / 0x34fb5e38 (designed) ⇒
  always last ⇒ **Plan-major**.
- **Paint** `FUN_004954e0` clears counter `+0xa818` (0x495534) + guard `+0xa774` (0x495541); runs the 128
  slots through `FUN_005a73f0(id, faction, baseidx)` (0x4956f4); then **secret projects 1..0x47**
  filtered by `FUN_005a6e70(idx, faction, baseidx, slot)` (pseudo:146-210). Accepted items append to the
  itemlist at **chooser-sub +0xa780 = 0x6b461c** (`add ecx,0xa780` 0x495aab → `call 0x42ee20(list, item,
  flags, 0)`): units `flags |= 0x20`, projects `|= 0x10`. Guard := counter when
  the item equals the queue value edited (`id == local_34` / `-local_34 == local_28`), `local_34 =
  cur_base+0x50 + (sub+0xb68)·4`.
- **Return encoding:** `FUN_00496ad0` tail (shard_009.c:15013-15041): guard −1 ⇒ −9999; else
  `FUN_004026b0(guard)` then `(detail+8 & 0x20) == 0 ⇒ −item` else `+item`. ⇒ **a queued secret project
  = −(index in the 0x984d38 table, stride 0xc dwords)** (26 Pressure Dome, 71 The Ascent to Transcendence — `evidence/m53h_project_names{,2}.txt`).
  **M53a's `|q| = 39 + idx` is dead.** Live list
  (`evidence/m53h_list_dump.txt`): idx 0-8 = 195,196,192,194,193,2,0,1,6 (bit 0x20); idx 9-14 = projects
  2,11,13,26,27,38 ascending ⇒ **idx 12 = project 26 ⇒ −26 = M53g's POST_PICK at guard 12 ✓**. The five
  chassis-3 array units (197,198,3,200,199) are absent: `FUN_005a73f0`'s naval gate `ch_tbl[+1] == 1 &&
  FUN_004e4620(base.x, base.y) == 0` (also record+0x2c faction mask; Plan == 8 with `DAT_00985ac4 &
  0x400000`; designed ownership `id>>6 == faction`).
- **Bar buttons:** six embedded controls (class vptr 0x67194c) at `0x6a9e9c + 0xb74 + i·0xb4c` (i 6/7
  idle), param **+0xa78**, rect **+0x13c/0x140/0x144** (mirror +0x15c/0x160/0x164); live
  (`evidence/m53h_button_live.txt`) i0 −2 CANCEL 569→669 · i1 7 REPLACE 260→360 · i2 5 INSERT 363→463 ·
  i3 4 DELETE 466→566 · i4 −1 OK 157→257 · i5 0 HELP 54→154, all y 332 h 0x14. Built per open by
  `FUN_00496ad0` (shard_009.c:14909-14993): btnW `sub+0xb70` = 100, count `sub+0xb6c` = **6 when
  `sub+0xb68 != 0`** else 4/5 (`sub+0xb68` = queue slot opened on; 0 = head ⇒ no DELETE/INSERT/REPLACE),
  first x = `((W − 0x20) − 103·count)/2 + (count−1)·103`, W = `sub+0xa824` = 758 ⇒
  569, pitch 103 (3 px gaps), created right→left −2,4,5,7,−1,0 via `FUN_005f9e85(caption, param, x, y,
  w, h, owner, 0)` (stores the param at +0xa78, shard_019.c:2065); release `FUN_005fab08`
  (shard_019.c:2500-2540) forwards it to owner-vtable+0xa8. Captions `*(DAT_00997b20+off)` +
  `FUN_00409690(0x3fa)` (REPLACE), `CharUpperA` — **never in Script.txt**.
- **Click map (INFERRED):** origin offset **+36 px** fits every M53g click (REPLACE claims 365 not 397 ⇒
  ≤37; DELETE claims 602 ⇒ ≥36): HELP 90-190 · OK 193-293 · REPLACE 296-396 · INSERT 399-499 · DELETE
  502-602 · CANCEL 605-705; the 3 px inter-rect gaps are where the grid hit-test steals the click
  (= "phantom cell 17"). Grid live: cols 5, rows 3 (= 3 + (screen width > 800), `DAT_00993a00`), cellw
  `+0xa81c` 135 = (758−0x51)/5, cellh 108, capacity `+0xa82c` 15.

### M53g (session 59): guard = selection cell index; REPLACE = bar param 7 — `evidence/m53g_findings.md`
- Bar handler `FUN_00496950` = **vtable+0xa8** (only pointer 0x672340 = vptr 0x672298+0xa8); jump
  table 0x496a9a indexes `param+2`; gate `cmp [this+0xa774],-1` guards cases 0/2/5, **case 7
  ungated**; −1=OK→mode 0; −2=CANCEL→mode 0 + guard −1; **0x496a91 = the shared epilogue return**;
  one handler run per click. REPLACE live at (365,343): param 7 → mode 7 → POST_PICK edi=−26 →
  +0x54 2→−26 (`m53g_watch.log:104-112`). CANCEL-restore (RESTORE ×10) makes armed REPLACE probes
  non-destructive.

### M53f (session 58): the alpha `#UNITS` overrides + the cost formula — `evidence/m53f_findings.md`
`+41` has ONE store (`0x595ce7` after `call 0x595820`); the alpha overrides are **disp8 stores off
`esi = record + 50`** in the `#UNITS` loader `FUN_00579f40` (**+42 Plan 0x57a02d, +41 Cost 0x57a037**
(0 = Autocalculate), +40 0x57a041, +46 0x57a04a, +50 0x57a001; builder `0x595b10` first, row cap
`0x40`). Cost calculator
**188/188 explained** (`scripts/m53b_costcalc.py`; `--legacy` = superseded).

### Standing from M53b / M53d / M53c / M53a-M52b (do not re-derive)
- **M53b:** `+41` = COST FACTOR; price = `FUN_004e40a0(owner,1,−1) × +41`, live multiplier 10 ⇒ `+41 = 1`
  = 10 minerals; `+43` = auto AI role.
- **M53d:** queue writer `FUN_00417d20`: 0x417e04 store (slot 1→+0x54 … 9→+0x74), 0x417dd8 insert-shift,
  0x417dad delete-shift, `+0x4c` cap-9 0x417df6. Dispatcher `FUN_00417ee0` on mode via 0x419c04: 1/2/3 →
  0x418cda re-open, 4/6→0x418703, 5→0x4187a2 push 1, 7→0x4187ad push 0, 0 → tail; **M53c:** THE POP = `FUN_004ef5d0(base_idx)`; `+0x4c` = PENDING count; `+0x4c == 0` ⇒ nothing
  consumes the head. **M53a/M52b:** queue encoding `−38` empty, `≥ 0` type id, `< 0` secret project =
  **−project index** (M53h). Completion is PAYMENT-DRIVEN: COMPLET 0x4efe41 when `storage ≥ factor ×
  `0x5ac950(id, idx, 0)`; SPENDA debit 0x4efee0. `+0x44` = active-item mirror. Storage sweep never
  truncates; base array SLIDES ⇒ locate base by NAME.
- Base record: x u16@0, y u16@2, owner@4, pop@6, flags f18/f1c/f20/f28/f30, +0x3c progress, minerals@0x40,
  44 active mirror, **4c pending count (cap 9)**, **queue @0x50..0x74**, 8a/8c facility bitmap, 98 storage
  snapshot, c0, cc (−3 for us), d0, fc, f38 = 0x00dfbe41.
- Type record `0x98ad88 + type·52`: name +0[34], ability int +32, +36 chassis, +37 weapon, +38 armor,
  +39 reactor, +40 carry, **+41 cost factor**, +42 Plan, +43 auto role, +46 icon, +50 prereq word, +0x2c
  faction mask, +0x30 flags (`bit0` enabled; `&4` gates the `0x5ac950` bump). Dump `m53b_types.tsv`.
- Globals: year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap 0x92a370
  (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array 0x95da10/0x130, unit array
  0x933278/52, faction records 0x20bc, screen width
  `DAT_00993a00`, string-handle table `DAT_00997b20` (dword-indexed), labels `FUN_00409690/4096c0(id)` →
  `programs/labels.txt` line = id + 9 (461 Insert, 1020 Replace).
- UI objects: **pane 0x6a9480** (`+0x3ff3c` base index, `+0x3ff5c` selected queue slot, `+0x3ff60` zeroed
  by row click, `+0xa1c` chooser sub 0x6a9e9c, **+0xb190 guard, +0xb194 mode**); chooser control
  **0x6a9e9c** (vptr 0x672298 live): +0xa76c faction, +0xa774 guard, +0xa778 mode, **+0xa780 itemlist
  0x6b461c**, +0xa810 cols, +0xa814 rows, +0xa818 enum counter, +0xa81c cellw, +0xa820 cellh, +0xa824 W
  (758), **+0xb68 slot opened on, +0xb6c button count, +0xb70 btnW,
  +0xb74 + i·0xb4c the six bar buttons**; vtable +0x4 `FUN_00494bb0`, +0x8 `FUN_00494c40`, +0x48 `FUN_004962a0` setter, +0x60 `FUN_004963b0` mutator, +0xa8 `FUN_00496950`
  bar handler, +0xe0 0x5ce6ff repaint.  `FUN_00416080(this)` = pane redraw; `FUN_00496ad0(
  pane+0xa1c, base, owner, scratch)` = modal chooser (returns ±item or −9999); `FUN_00417ee0`
  dispatcher; `FUN_00417d20` queue writer; `FUN_00596000` unit-list producer; `FUN_005a73f0` unit
  availability; `FUN_005a6e70` project availability; `FUN_004026b0/00401940/00495480` list select /
  item / flags.

## Static-reading kit
- **Store censuses on a linear disassembly:** `objdump -d -M intel --section=.text programs/terran.exe`. Map VA→function by bisecting
  `ghidra_out/index.csv`. **VA = file offset + 0x400000.** Grep store SHAPES (indexed stores, disp8 off a
  table-base register, `rep movs`, negative pointer arithmetic), not literal offsets.
- Pseudocode `scripts/fn.py 0xADDR`; corpus `grep -rn <pat> ghidra_out/shard_*.c` then
  `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`. No store in pseudocode ⇒ byte-scan the
  image (`d.find(struct.pack('<I', disp))` over .text).
- **Alpha comment headers name the columns** of bare-data sections (`programs/alpha.txt` `:348 #CHASSIS`,
  `:387 #WEAPONS`, `:422 #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `#FACILITIES`; list in
  `ALPHA_RULES.md`); `scripts/parse_alpha.py` → `data/alpha.json` (`#UNITS` field order at `:532`).
- **Ghidra renders control fields as `obj[0xINDEX]`, INDEX = byte offset / 4** (`in_ECX[0x29e]` = +0xa78,
  `local_14[0x29dd]` = +0xa774, `local_14[0x2da]` = +0xb68). Grep the /4 index, not the offset.
- **A live enumeration dump needs no gdb:** the chooser itemlist 0x6b461c and the six bar controls
  survive close (static objects). Walk +8 head with **+0x10 = count** (not +0xc = cursor); node +4 item /
  +8 detail / +0x10 next; bar rects/params at `0x6a9e9c + 0xb74 + i·0xb4c`.

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
  Read-only state `scripts/smac_state.py --json`; our base = idx **70** @ 0x962d30.
- **Armed UI-driving:** `python3 scripts/m53g_drive.py --tag mXX --mode arm --hold 900 --pane 0x6a9480`
  under **background=true** (Hermes kills children of a finished foreground call), drive with your
  own `smac_play` clicks (`P.WIN = P.find_window()`, `P.focus()`, `P.click((x,y))`; `m53e_seq.py`
  helpers `chooser_fields(pid)`, `bar_px()`, `base_fields(pid)`), then `python3 scripts/
  m53g_drive.py --mode stop --tag mXX` (positional tag NOT accepted). m53g_drive adds BARH(0x496950:
  param/ecx/guard) + GATE0/2/5 + SELWP on pane+0xb190. gdb under `stdbuf -o0`; watchpoint `$pc` sits
  PAST the store; read the log after stop.
- Chooser geometry: overlay x 60-740 y 8-330; icon cols x 128/255/383/510/638, rows y 60/160/260; bar
  widgets y 332-352 (blue fill measured 336-352); **clickable (window coords, INFERRED +36): HELP 90-190
  · OK 193-293 · REPLACE 296-396 · INSERT 399-499 · DELETE 502-602 · CANCEL 605-705**; QUEUE rows: click x 185, y = 437 + 12·(row−1); CHANGE ≈(185,552),
  HURRY ≈(185,571). **Chooser-open test = pixel (160,343) == RGB (103,91,181)** (`m53e_seq.bar_px()`).
- Pitfalls that bite here (full list in the skill): poke-then-arm (M33), `kill -CONT` after gdb-INT,
  never Escape on title/REALLYQUIT, **never signal by name** (stop drivers with `--mode stop --tag`;
  a python driver's own argv matches `pkill -f`), **a gdb command-list expression on a non-numeric
  convenience variable aborts the batch and detaches silently** (bake base as literal), gdb `printf`
  needs stdbuf -o0, **`/proc/pid/mem` list walks take count from +0x10 (a cursor value as a loop bound = a 79
  M-iteration hang)**.
## Milestone options (pick ONE)
- **M53i — the secret-project table + `FUN_005a6e70` (THE PICK).** The 72-row table at `0x984d38` (stride
  0xc dwords): what `FUN_005a6e70(idx, faction, baseidx, slot)` gates on and **why its return indexes
  the cost table `0x984d44` instead of being the loop index** (paint pseudo:147-161); the rest of the 48-byte record layout (+0 name, +4 effect, +12 cost factor; check `alpha.txt`); how a queued project is consumed (`FUN_004e4350(q, baseidx)` for negative q; is M53c's −29
  head value Aerospace Complex?); project 38's special display (base+0xd0, pseudo:173-180). **Done
  when** `FUN_005a6e70`'s predicate is stated with its data source AND the cost accessor for a negative
  queue value is pinned to address + line, with one live cross-check.
- **Later:** does the itemlist cap at capacity (live 15 == 5×3)?; who draws the bars M53e measured
  (57-80 px spans vs 100 px rects); the 4/5-button variant (params 1/2/3/6, captions +0x9b4/+0x4f4) and
  when `sub+0xb68 == 0` occurs in play; `FUN_004fe670` research-scaled
  table bytes; vtable+8 `FUN_00494c40`; producers of modes 2/3/6; `FUN_0059ce10`'s `+0x4c = pop·10/2`
  (over cap 9, `shard_015.c:14416`); M50c-e, M51b, base+0xc0.
- **Retired premises, do not resurrect:** "PROGDIV accumulates progress"; "+0x4c is the last used
  index"; "digit keys 1-9 queue an item"; "the queue refills itself from the head"; "`0x5ac950`
  returns a WEIGHT"; "+41 is the mineral price as stored"; "the loader pre-scales ×10"; "+0xb194 is
  a pane field some bar writes"; "OK commits the queued pick"; "the ability flag word is at +16";
  "REPLACE needs guard ≠ −1 / is case 2"; "BAR_IGNORED 0x496a91 = bar refusal"; "one bar click runs
  the handler twice"; **"secret projects queue as |q| = 39 + idx" (q = −project index, VERIFIED at
  −26)**; **"the chooser bars are Script.txt buttons" (embedded controls built by `FUN_00496ad0`)**;
  **"enumeration order is arbitrary / icon order" (Plan-major, `FUN_00596000`)**; **"units and
  projects interleave" (units first, then projects ascending)**; **"params 1/2/3/6 are unreachable"
  (they exist in the 4/5-button head variant)**; **"381-421 is REPLACE's dead area" (only the 3 px
  inter-rect gaps are dead)**.
## Report style
Findings → `evidence/<id>_findings.md` ONCE; SESSION_NOTES.md + this file by extraction
from it; cite log line numbers for every claim; mark VERIFIED vs INFERRED; end with the next-prompt
pointer.

