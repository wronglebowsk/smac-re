# NEXT_PROMPT — SMAC RE, session 62

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53i (**M53i done, session 61**); open: **M53j (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 61 (M53i) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state (kit below): game up (`pgrep -x terran.exe` → 2124624), year 2371, our turn (`cur == 3`),
   n_bases 75, our base idx **70 @ 0x962d30** ("Climactic Research"), base pane up, chooser closed
   (guard `sub+0xa774` = −1, mode `+0xa778` = 0), itemlist 0x6b461c holds the last enumeration
   (count 15), no gdb, TracerPid 0, `ptrace_scope` 0. Base 70: **`+0x4c = 2` pending = two Scout
   Patrols (`+0x54 = +0x58 = 2`)**, head `+0x50 = 3`. Session 61 was STATIC — nothing in the game
   changed. M53j is STATIC-FIRST: `FUN_004ef6d0` pseudocode + disasm windows are already on disk
   (`evidence/m53i_fn4ef6d0.txt`, `evidence/m53i_disasm.txt`); read-only preads suffice; arm only if
   a live COMPLET store must be caught.
## Footing — production economy + secret projects (M48d → M53i, VERIFIED unless marked)

### M53i (session 61): project table + gate + negative-q cost — write-up `evidence/m53i_findings.md`
- **Table = alpha `#FACILITIES`** (`alpha.txt:590-665`) loaded verbatim as 72×48 B @ **0x984d38**;
  **live idx = alpha row + 1** (row 0 null placeholder; row 1 'Headquarters'; 26 'Pressure Dome' =
  alpha:616; 71 'The Ascent to Transcendence' = alpha:661; dump `m53i_project_table.tsv`). Record:
  +0 name str ptr, +4 effect str ptr (arena ~0x2100000, `FUN_0061482f` resolves), +8 always 0,
  **+0xc cost factor** (alpha col 2; price = `FUN_004e40a0(faction,1,−1)` × it, multiplier 10 = masked
  faction, `m53i_fn4e40a0.txt:14-19`), +0x10 = alpha col 3, **+0x14 prereq tech (−1 = None)**,
  +0x18 = −2 constant (alpha "Disable" col), +0x1c..+0x2c = 5 trailing alpha cols permuted
  (+0x1c=c7, +0x20=c10, +0x24=c9, +0x28=c11, +0x2c=c8; semantics open). **0x984d44 = DAT_00984d38+0xc
  = dword 3 of the same record, NOT a second table.** Zero stores in corpus (all 70 refs loads; Ghidra
  hides 7 as `&DAT_00984d4c` — grep the `984d` PREFIX); writer pointer-based (open).
- **`FUN_005a6e70(idx, faction, baseidx, n_scan)`** (pseudocode `m53i_fn5a6e70.txt`; cites = its lines):
  :16 idx 0 false; :19 idx 10 needs `DAT_00985aec ≥ 2`; :25 idx > 0x26 blocked by `DAT_00985ac4 &
  0x80000000`; :28 idx 71 needs `DAT_00985bb8 ≠ −1` + `ac4 & 0x800`; :36-55 tech gate = record+0x14 →
  tech table 0x92fdd4 (stride 0xb dw, ≤ 0x57) + ownership `DAT_00985c1c[tech] & (1<<(faction&0x1f))`;
  :57-58 **idx > 0x26 available iff claim table `DAT_00985aa0[idx] == −1`**; :60 idx 32 `0x59a9f0(f)`;
  :65 baseidx < 0 ⇒ true; :68-83 idx < 0x23 ⇒ base+0x8c bitmap lacks bit idx AND queue scan (param_4 =
  length; paint passes chooser+0xb68 = slot opened on, NOT pending count) lacks −idx; :85-279 per-idx
  terrain/facility cases via 0x46f8e0 / 0x421fe0 / 0x4e4620(base.x, base.y, 0) + globals 0x985b50/b54/
  ba8, 0x927a98[faction·0x59c] bit 0x200; :274 default ≤ 0x26 true. `FUN_00507410` = 39-B bit splitter
  `>>3` / `1<<(x&7)` (203 callers).
- **Negative-q cost accessor (VERIFIED address+line).** q < 0 ⇒ project −q; accessor
  `(&DAT_00984d44)[(−q)·0xc]` × `FUN_004e40a0`. Production processor **`FUN_004ef6d0`** (size 12298;
  holds COMPLET 0x4efe41 = `cmp ebx,0x40; jl 0x4efed1` designed-unit gate): completion test
  `iVar4 * (&DAT_00984d44)[(int)local_34*0xc] <= base+0xcc + base+0x3c` (`m53i_fn4ef6d0.txt:768-769`,
  local_34 = −q :596; iVar4 = 0x4e40a0 :766); affordability branch :601-604 (`≤ cur_base+0x20` — what
  IS base+0x20? → M53j); pane head cost shard_001.c:9814 `[*(DAT_008f0d60+0x50) * -0xc]`; announcements
  dispatcher 0x41890a-0x418919 + 0x56e3f7-0x56e412 (`m53i_disasm.txt`). **Paint does NOT index cost by
  5a6e70's return**: pseudo:149 boolean gate, :159 `iVar2 = local_28` reassigns before the read :161.
- **Claim table `DAT_00985aa0[1..71]`** = base index where project last completed, −1 = nobody
  (gate use VERIFIED; semantics INFERRED via pane counter `*piVar7 == DAT_0068cbb0` shard_001.c:5440
  loop 0x985aa0..0x985b3c + owner lookup shard_012.c:14698). Live 29/71 = −1; aa0[26]=0, aa0[29]=0,
  aa0[38]=3 (base 0 = faction 2, base 3 = faction 4 — pread 0x95da10+b·0x130+4 low byte), aa0[71]=−1.
  **Writer not pinned → M53j.**
- **Carry-over + display.** Head-slot open ⇒ remaining = price − base minerals iff
  `FUN_004e4350(−idx,base) == 4e4350(head,base)` (class code; HQ bit + `DAT_0092a368` mode + q < −0x26
  split; `m53i_fn4e4350.txt`) or perception `0x94d438[faction·0x82f] < 2`, else price − minerals/2
  (paint:162-171). **−29 head = Aerospace Complex** (row 29 live string, cost 8, tech 39 — VERIFIED).
  Project 38 Stockpile Energy (cost 0, tech −1) shows `clamp(base+0xd0,0,9999)`; generic rows
  `(price−credited+rate−1)/rate` turns, **rate = base+0xd0 = production toward head** (paint:173-192;
  units same divisor :116-124).

### Standing from M53h / M53g / M53f / M53b-M53d (do not re-derive)
- **M53h:** producer `FUN_00596000(faction)` → 128 candidates `DAT_009267e4` (count `0x9267e0`),
  Plan-major bubble sort via `0x5a29a0` (unavailable ⇒ 999999999/0x34fb5e38 = last); paint
  `FUN_004954e0` filters units via `FUN_005a73f0` (naval gate `ch_tbl[+1]==1 && 0x4e4620(x,y)==0` drops
  sea units at land bases), projects 1..0x47 via `FUN_005a6e70`, appends to itemlist at chooser+0xa780
  = **0x6b461c** (units flags|0x20, projects |0x10; node +4 item, +8 detail, +0x10 next, circular;
  header +8 head, +0xc cursor, **+0x10 count**); return `FUN_00496ad0` tail: guard −1 ⇒ −9999; else
  `(detail+8&0x20)==0 ⇒ −item` ⇒ **queued project = −project idx**. Six bar buttons = embedded controls
  (vptr 0x67194c) at `0x6a9e9c+0xb74+i·0xb4c` (params −2/7/5/4/−1/0 at +0xa78, rects +0x13c/0x140/0x144),
  built per open by `FUN_00496ad0` (btnW 100, pitch 103, count 6 iff sub+0xb68 ≠ 0); captions NOT in
  Script.txt (`*(DAT_00997b20+off)` + `0x409690(0x3fa)`). 
- **M53b/M53d/M53c/M53a/M52b:** type `+41` = COST FACTOR, price = `FUN_004e40a0(owner,1,−1)` × it;
  queue writer `FUN_00417d20` (0x417e04 store slot 1→+0x54 … 9→+0x74, insert 0x417dd8, delete 0x417dad,
  +0x4c cap 9 at 0x417df6); dispatcher `FUN_00417ee0` modes 1/2/3→0x418cda, 4/6→0x418703, 5→0x4187a2,
  7→0x4187ad; THE POP = `FUN_004ef5d0(base_idx)`; `+0x4c` = PENDING, 0 ⇒ nothing consumes head;
  completion PAYMENT-DRIVEN (COMPLET 0x4efe41 in `FUN_004ef6d0`; SPENDA debit 0x4efee0); queue
  encoding `≥ 0` type id, `< 0` secret project = −idx, `−38` empty; storage sweep never truncates;
  base array SLIDES ⇒ locate base by NAME.
- Base record: x u16@0, y u16@2, owner@4 (low byte = faction), pop@6, flags f18/f1c/f20/f28/f30,
  +0x3c progress, minerals@0x40, 44 active mirror, 4c pending (cap 9), queue @0x50..0x74, **8a/8c
  facility bitmap (bit = facility id via 0x507410)**, 98 storage snapshot, c0, cc (−3 for us;
  **+0xcc + 0x3c = the COMPLET pay pool**), **d0 = per-turn production toward head item**, fc,
  f38 = 0x00dfbe41.
- Type record `0x98ad88 + type·52`: name +0[34], ability int +32, +36 chassis, +37 weapon, +38 armor,
  +39 reactor, +40 carry, **+41 cost factor**, +42 Plan, +43 auto role, +46 icon, +50 prereq word,
  +0x2c faction mask, +0x30 flags (`bit0` enabled; `&4` gates the `0x5ac950` bump — word at 0x98adb8).
  Cost fn `FUN_005ac950(id, idx, out)` = +41 byte + research bump for designed ids ≥ 0x40
  (`m53i_fn5ac950.txt`); **negative ids unhandled** — projects use the 0x984d38 accessor.
- Globals: year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap
  0x92a370 (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array 0x95da10/0x130, unit
  array 0x933278/52, faction records 0x20bc, screen width `DAT_00993a00`, string handles
  `DAT_00997b20`, labels `FUN_00409690/4096c0(id)` → `programs/labels.txt` line = id + 9. Project
  state: tech table 0x92fdd4 (stride 0xb dw, rows ≤ 0x57), tech-ownership bytes 0x985c1c[tech],
  claims 0x985aa0[72], scenario flags 0x985ac4 (bit31 blocks projects >38; bit 0x800 Ascent),
  0x985aec/0x985b50/b54/ba8/bb8, 0x927a98[faction·0x59c] bit 0x200, 0x92a368 (4e4350 mode),
  0x94d438[faction·0x82f] perception.
- UI objects: **pane 0x6a9480** (+0x3ff3c base idx, +0x3ff5c selected slot, +0xa1c chooser sub
  **0x6a9e9c**, +0xb190 guard, +0xb194 mode); chooser 0x6a9e9c (vptr 0x672298): +0xa76c faction,
  +0xa774 guard, +0xa778 mode, +0xa780 itemlist 0x6b461c, +0xa810 cols, +0xa814 rows, +0xa818 enum
  counter, +0xa81c cellw, +0xa824 W 758, +0xb68 slot opened on, +0xb6c button count, +0xb74+i·0xb4c
  bar buttons; vtable +0x4 `FUN_00494bb0`, +0x8 `FUN_00494c40`, +0x48 setter `FUN_004962a0`, +0x60
  `FUN_004963b0`, +0xa8 bar handler `FUN_00496950`, +0xe0 repaint. `FUN_00496ad0(pane+0xa1c, base,
  owner, scratch)` modal chooser; `FUN_00416080` pane redraw; `FUN_00417ee0` dispatcher; `FUN_00417d20`
  queue writer; `FUN_00596000` producer; `FUN_005a73f0` unit availability; `FUN_005a6e70` project
  availability; `FUN_004ef6d0` production processor; `FUN_004e40a0` price multiplier; `FUN_004e4350`
  item class code; `FUN_004026b0/00401940/00495480` list select / item / flags.

## Static-reading kit
- **Store censuses:** `objdump -d -M intel --section=.text programs/terran.exe`; map VA→fn by
  bisecting `ghidra_out/index.csv` (col 0 = addr, col 1 = name). **VA = file offset + 0x400000.**
  Grep store SHAPES (indexed stores, disp8 off table base, `rep movs`, negative pointer arithmetic),
  not literal offsets. No store in pseudocode ⇒ byte-scan `d.find(struct.pack('<I', disp))` (worked
  for 0x984d38: 81 hits, all load shapes like `mov reg,[eax*1+0x984d38]` after `·3·16` index math).
- Pseudocode `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite evidence-file line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c` then `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}'`.
  **Grep the DAT PREFIX** — Ghidra splits one table into DAT_00984d38/44/4c/... by field offset.
- **Alpha comment headers name the columns** (`alpha.txt` `:348 #CHASSIS`, `:387 #WEAPONS`, `:422
  #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `:590 #FACILITIES` = the 71-project table, rows 0-70 →
  live idx +1); `scripts/parse_alpha.py` → `data/alpha.json` (`#UNITS` field order at `:532`).
- Ghidra renders control fields as `obj[0xINDEX]`, INDEX = byte offset / 4. Live list walks take
  count from header **+0x10** (not +0xc = cursor).

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
  Read-only state `scripts/smac_state.py --json`; our base = idx **70** @ 0x962d30.
- Chooser geometry: overlay x 60-740 y 8-330; icon cols x 128/255/383/510/638, rows y 60/160/260; bar
  widgets y 332-352; **clickable (window coords, INFERRED +36): HELP 90-190 · OK 193-293 · REPLACE
  296-396 · INSERT 399-499 · DELETE 502-602 · CANCEL 605-705**; QUEUE rows: click x 185, y = 437 +
  12·(row−1); CHANGE ≈(185,552), HURRY ≈(185,571). Chooser-open test = pixel (160,343) == (103,91,181).
- Pitfalls that bite here (full list in the skill): poke-then-arm (M33), `kill -CONT` after gdb-INT,
  never Escape on title/REALLYQUIT, **never signal by name** (stop drivers with `--mode stop --tag`;
  a python driver's own argv matches `pkill -f`), **a gdb command-list expression on a non-numeric
  convenience variable aborts the batch** (bake base as literal), gdb `printf` needs stdbuf -o0,
  **`/proc/pid/mem` list walks take count from +0x10**, evidence-file line cites are the citation unit
  for pseudocode claims; **`sh`/print truncation can fake a "truncated file"**.

## Milestone options (pick ONE)
- **M53j — completion bookkeeping (THE PICK).** Who writes the claim table `0x985aa0` (pointer-based
  store — census `rep movs`/indexed stores near `FUN_004ef6d0`'s COMPLET tail 0x4efe41→0x4f0bfa and
  `FUN_004ef5d0`'s POP path; readers `FUN_004105b0`/`FUN_00411180` prove it updates per turn). What
  COMPLET does after payment: queue shift (`FUN_00417dad` delete-shift? head re-arm?), SPENDA debit
  0x4efee0 vs the pay pool `+0xcc + 0x3c`, effect application (the 8a/8c facility-bitmap store for
  facilities; project effect dispatch — the −2 "Disable" trigger at record+0x18), and the affordability
  branch `m53i_fn4ef6d0.txt:601-604` (`≤ cur_base+0x20` — what IS base+0x20?). **Done when** the
  0x985aa0 store is pinned to address + rendering AND the COMPLET side-effect list is stated with
  cites, with one live cross-check (e.g. aa0[38]=3's base shows the facility bit / owner consistent).
- **Later:** pin the 0x984d38 table writer/loader + who fills the 0x2100000 string arena; 4e4350
  return-code semantics + `DAT_0092a368` source; tech table 0x92fdd4 record layout (research tree);
  does the itemlist cap at capacity (live 15 == 5×3)?; who draws the bars M53e measured (57-80 px spans
  vs 100 px rects); the 4/5-button variant (params 1/2/3/6, when `sub+0xb68 == 0` occurs in play);
  `FUN_004fe670` research-scaled table bytes; producers of modes 2/3/6; vtable+8 `FUN_00494c40`;
  `FUN_0059ce10`'s `+0x4c = pop·10/2` (over cap 9, `shard_015.c:14416`); M50c-e, M51b, base+0xc0.
- **Retired premises, do not resurrect:** "PROGDIV accumulates progress"; "+0x4c is the last used
  index"; "digit keys 1-9 queue an item"; "the queue refills itself from the head"; "`0x5ac950` returns
  a WEIGHT"; "+41 is the mineral price as stored"; "the loader pre-scales ×10"; "+0xb194 is a pane
  field some bar writes"; "OK commits the queued pick"; "the ability flag word is at +16"; "REPLACE
  needs guard ≠ −1 / is case 2"; "BAR_IGNORED 0x496a91 = bar refusal"; "one bar click runs the handler
  twice"; "secret projects queue as |q| = 39 + idx"; "the chooser bars are Script.txt buttons";
  "enumeration order is arbitrary" (Plan-major); "units and projects interleave" (units first);
  "params 1/2/3/6 are unreachable"; "381-421 is REPLACE's dead area"; **"0x984d44 is a separate cost
  table"** (dword 3 of the same record); **"FUN_005a6e70's return is a cost index"** (boolean; paint
  pseudo:159 reassigns iVar2 = loop idx); **"aa0 = completion count"** (base index); **"5a6e70's
  param_4 = pending count"** (paint passes chooser+0xb68); **"project names come from Script.txt /
  labels"** (arena ~0x2100000 ← alpha #FACILITIES); **"live project idx = alpha row number"** (row + 1;
  row 0 = null placeholder); **"the −29 head value is unresolved"** (= Aerospace Complex);
  **"FUN_004e4350 consumes/queues projects"** (it is the class code for the carry-over compare);
  **"FUN_005ac950 prices queue items with negative ids"** (projects bypass it).
