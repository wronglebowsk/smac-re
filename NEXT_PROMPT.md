# NEXT_PROMPT — SMAC RE, session 63

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53j (**M53j done, session 62**); open: **M53k (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 62 (M53j) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state (kit below): game up (`pgrep -x terran.exe` → 2124624), year 2371, our turn (`cur == 3`),
   n_bases 75, our base idx **70 @ 0x962d30**, base pane up, chooser closed (guard `sub+0xa774` = −1,
   mode `+0xa778` = 0), no gdb, TracerPid 0, `ptrace_scope` 0. Base 70: `+0x4c = 2` pending = two Scout
   Patrols (`+0x54 = +0x58 = 2`), head `+0x50 = 3`, **minerals `+0x40 = 0`, `+0xd0 = 0`**, bitmap
   `+0x8c..0x90 = ca 01 00 00 00` (bits 1,3,6,7,8). Session 62 was STATIC + read-only preads — nothing in
   the game changed. M53k is STATIC-FIRST (the whole-`.text` dump is already cached, see the kit); arm a
   live probe only if the store census leaves the arm semantics unresolved.

## Footing — production economy + secret projects (M48d → M53j, VERIFIED unless marked)

### M53j (session 62): claim-array geometry + the completion writer — `evidence/m53j_findings.md` (+ the ordered side-effect list `evidence/m53j_complet.md`, CFG `evidence/m53j_cfg.txt`)
- **Claim array = 33 dwords @ 0x985b3c, index = project_idx − 0x27** (projects 39..71 only; slots
  0x985aa0..0x985b38 are other globals: 0x985af4 nb, 0x985b00 year, 0x985b10 mask, 0x985ac4 flags). Proof
  trio: gate `m53i_fn5a6e70.txt:58` reads `&DAT_00985aa0 + idx*4` only for `0x26 < idx`; machine code
  0x4ef89f-0x4ef8ac `neg ecx; cmp ecx,0x27; lea edx,[ecx-0x27]` (else −1); discriminator
  `shard_001.c:5424-5444` (FUN_00411180) walks 0x985aa0..**0x985bc0** branching ON ADDRESS — `< 0x985b3c`
  ⇒ facility bitmap (`< 0x985b29` = idx < 0x23) / `FUN_005a6de0`, `>= 0x985b3c` ⇒ `*piVar7 == DAT_0068cbb0`.
  AI FUN_004f6030 converts `param_1 + 0x27` (shard_012.c:28613) before calling 0x5a6e70.
- **Writers: exactly 3 store sites whole-`.text`** (census `evidence/m53j_refs_985aa.txt`: 3093 refs /
  8 stores in 0x985aa0..0x985bd0, 3 based inside the array): **0x4f0d83** in FUN_004ef6d0
  (`mov [eax*4+0x985b3c],edx`, edx = DAT_0068cbb0 = current base INDEX, eax = idx−0x27, guarded
  `test/jl`) = `m53i_fn4ef6d0.txt:892` = shard_012.c:21475 — the completion writer; 0x59d595 FUN_0059ce10
  (`_rand() & 0x80000007` re-rolled while `claim[u] != -1 || u == 4 || (u == 5 && f == 2)`,
  `m53j_fn59ce10.txt:286-291`, sole caller FUN_005a0fa0); 0x41cd7d FUN_0041c8b0 (dtor-heavy handler,
  sole caller FUN_0041d480; INFERRED debug/scripted). No pointer-based writer (address-takers all read).
- **THE POP = FUN_004ef5d0(base_idx)** (`evidence/m53j_fn4ef5d0.txt`): pending 0 → return 0; head ≥ 0 →
  `DAT_0094de84[faction*0x20bc+head] -= 1`; shift base+0x50.. left `*p = p[1]` × pending; base+0x4c −= 1;
  re-test new head via 0x5a6e70(−head,f,base,0) / 0x5a73f0 until available; head < −0x26 → 0x446250(0x24);
  then 0x473760(x,y,2,2). Queue shift + pending-- + head re-arm live HERE (zero such stores in 0x4ef6d0).
### M53i (session 61): project table + gate — `evidence/m53i_findings.md`
- **Table = alpha `#FACILITIES`** (`alpha.txt:590-665`) verbatim, 72x48 B @ **0x984d38**; **live idx =
  parsed FACILITIES row + 1** ([0] 'Headquarters' = live 1; [38] = live 39 Human Genome; [70] = live 71
  Ascent; dump `m53i_project_table.tsv`). Record: +0 name / +4 effect str ptrs (arena ~0x2100000,
  `FUN_0061482f` resolves), +8 always 0, **+0xc cost factor** (price = `FUN_004e40a0(faction,1,−1)` × it,
  multiplier 10 = masked faction, `m53i_fn4e40a0.txt:14-19`), +0x10 = alpha col 3, **+0x14 prereq tech
  (−1 = None; rendered `&DAT_00984d4c`, indexes `DAT_00985c1c` at shard_012.c:28618-28619)**, +0x18 = −2
  in all 71 rows (alpha "Disable" token: 6 read sites 0x44c694/694/743 + 0x49ea2a/49ea61/0x49eb06, never
  written, never in 0x4ef6d0), +0x1c..+0x2c = 5 trailing alpha cols permuted (c7,c10,c9,c11,c8, open).
  **0x984d44 = dword 3 of the same record, not a second table.** Zero corpus stores; writer open.
- **`FUN_005a6e70(idx, faction, baseidx, n_scan)`** boolean (`m53i_fn5a6e70.txt`, cites = its lines):
  :16 idx 0 false; :19 idx 10 needs `DAT_00985aec ≥ 2`; :25 idx > 0x26 blocked by `0x985ac4 & 0x80000000`;
  :28 idx 71 needs `0x985bb8 ≠ −1` + `ac4 & 0x800`; :36-55 tech gate via record+0x14, tech table 0x92fdd4
  (stride 0xb dw, ≤ 0x57) + `0x985c1c[tech] & (1<<(faction&0x1f))`; :57-58 **idx > 0x26 iff claim slot ==
  −1**; :60 idx 32 `0x59a9f0(f)`; :65 baseidx < 0 ⇒ true; :68-83 idx < 0x23 ⇒ base+0x8c bitmap lacks bit
  idx AND the queue scan (param_4 = length; paint passes chooser+0xb68) lacks −idx; :85-279 per-idx
  terrain/facility cases via 0x46f8e0 / 0x421fe0 / 0x4e4620(x,y,0) + 0x985b50/b54/ba8, 0x927a98 bit 0x200;
  :274 default ≤ 0x26 true. `FUN_00507410` = bit splitter `>>3` / `1<<(x&7)` (203 callers).
- **Head-slot display** (`FUN_004954e0`): remaining = price − base minerals iff `FUN_004e4350(−idx,base) ==
  4e4350(head,base)` (class code; HQ bit + `DAT_0092a368` mode + q < −0x26 split) or perception
  `0x94d438[faction·0x82f] < 2`, else price − minerals/2 (:162-171); generic rows
  `(price−credited+rate−1)/rate` with rate = base+0xd0 (:173-192); project 38 shows `clamp(base+0xd0,0,9999)`.

### Standing from M53h / M53g / M53d-M53b (do not re-derive)
- **M53b/d/c/a/M52b:** type `+41` = COST FACTOR, price = `FUN_004e40a0(owner,1,−1)` × it; queue writer
  `FUN_00417d20` (0x417e04 store slot 1→+0x54 … 9→+0x74, insert 0x417dd8, delete-shift 0x417dad, +0x4c cap
  9 at 0x417df6); dispatcher `FUN_00417ee0` modes 1/2/3→0x418cda, 4/6→0x418703, 5→0x4187a2, 7→0x4187ad;
  THE POP = `FUN_004ef5d0(base_idx)`; `+0x4c` = PENDING, 0 ⇒ nothing consumes head; queue encoding `≥ 0`
  type id, `< 0` secret project = −idx, `−38` empty; storage sweep never truncates; **base array SLIDES ⇒
  locate a base by NAME**.
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, owner@4 (low byte =
  faction), pop@6, +0x30 flags (bits 23/31 touched by the completion path), +0x3c, **+0x40 minerals**,
  +0x44 active mirror, +0x4c pending (cap 9), queue @0x50..0x74, **+0x8c..0x90 = 40-bit facility bitmap**
  (bit i at +0x8c+(i>>3), mask 1<<(i&7); `DAT_0095da9c`), +0x98 = minerals mirror (live equal 75/75),
  +0xcc, **+0xd0**, +0xfc, f38 = 0x00dfbe41. `FUN_004ef6d0`'s base loop uses `esi = 0x95da14` = base+4.
- **Type record** `0x98ad88 + type·52`: name +0[34], ability +32, +36 chassis, +37 weapon, +38 armor,
  +39 reactor, +40 carry, **+41 cost factor**, +42 Plan, +43 auto role, +46 icon, +50 prereq word,
  +0x2c faction mask, +0x30 flags (`bit0` enabled; `&4` gates the `0x5ac950` bump — word at 0x98adb8).
  Cost fn `FUN_005ac950(id, idx, out)` = +41 byte + research bump for designed ids ≥ 0x40
  (`m53i_fn5ac950.txt`); **negative ids unhandled** — projects use the 0x984d38 accessor.
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08), solo 0x920434, cap
  0x92a370 (10), cur base ptr **0x8f0d60**, **cur base INDEX 0x68cbb0**, base array 0x95da10/0x130, unit
  array 0x933278/52, faction records 0x20bc (base 0x92ae14), per-type built counters
  `DAT_0094de84[faction·0x20bc + type]`, faction names 0x927894+f·0x24, screen width `DAT_00993a00`,
  string handles `DAT_00997b20`, message buffer 0x997120, labels `FUN_00409690/4096c0(id)` →
  `programs/labels.txt` line = id + 9. Project state: tech table 0x92fdd4 (stride 0xb dw, rows ≤ 0x57),
  tech ownership 0x985c1c[tech], **claims 0x985b3c[33] (idx−0x27)**, scenario flags 0x985ac4 (bit31 blocks
  projects > 38; bit 0x800 Ascent), 0x985aec/985b50/b54/ba8/bb8, 0x927a98[faction·0x59c] bit 0x200,
  0x92a368 (4e4350 mode), 0x94d438[faction·0x82f] perception.
## Static-reading kit
- **Cached whole-`.text` disassembly: `evidence/m53j_text.txt.gz`** (790702 lines, objdump -d -M intel of
  `programs/terran.exe`, session 62, gzipped for the evidence budget). Locate a VA with
  `zgrep -n '  4f0b4f:' evidence/m53j_text.txt.gz` then `sed -n 'A,Bp'` on `zcat` output. Rebuild (~1.3 s):
  `objdump -d -M intel --section=.text programs/terran.exe > /tmp/f.txt`.
  Map VA→fn by bisecting `ghidra_out/index.csv` (col 0 addr, col 1 name). **VA = file offset + 0x400000.**
- **POINTER-TYPE SCALES IN PSEUDOCODE — the trap of session 62.** Ghidra typed the current-base pointer
  `DAT_008f0d60` and its copies `short *`, so every offset added to them is **HALF** the byte offset
  (`psVar22 + 0x28` == machine `[DAT_008f0d60+0x50]`; `* 0x98` == the 0x130 stride). `int *` DATs scale
  **×4** (`(&DAT_0095da5c)[base*0x4c]` == base+0x4c). And `FUN_004ef6d0`'s loop pointer is `0x95da14` =
  **base + 4**. NEVER trust a pseudocode field offset: pin it against a machine-code disp or a live pread.
- **Grep store SHAPES** on the linear disassembly, not literal offsets: dest-in-brackets = STORE;
  `lea`/bare imm = ADDR (address-takers may write through a pointer - check them). Script the disp32
  census: keep instructions whose operands hold an address in a range, classify by shape, group by
  function (that is how the 3-writer claim was pinned, `evidence/m53j_refs_985aa.txt`).
- **Grep the DAT PREFIX** — Ghidra splits one array into `DAT_…38/44/4c/50/9c` renderings by field offset,
  and names a mid-array DAT when code indexes it with a constant (`0x985b3c` = claim[39] relative to the
  flat `0x985aa0 + idx*4` rendering). A base-only grep misses refs and invents tables.
- Pseudocode `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite evidence-file line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c`; enclosing function via
  `grep -n '^// ==== ' ghidra_out/shard_N.c | awk -F: -v L=<line> '$1<L' | tail -1`.
- **Alpha comment headers name the columns** (`alpha.txt` `:348 #CHASSIS`, `:387 #WEAPONS`, `:422
  #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `:590 #FACILITIES`); `scripts/parse_alpha.py` →
  `data/alpha.json` (list index = live project idx − 1).
- Jump tables: dump the raw dwords (`struct.unpack_from('<I', img, va-0x400000)`) before "correcting" case
  labels. MSVC C++ noise in big functions = stores of vtable constants + calls 0x406720/0x406060/0x5f6de9
  + the `[ebp-0x4]` state byte: scope cleanup, not logic (it made 0x4ef6d0 look branchy).

## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
  Read-only state `scripts/smac_state.py --json`; our base = idx **70** @ 0x962d30.
- Chooser geometry: overlay x 60-740 y 8-330; icon cols x 128/255/383/510/638, rows y 60/160/260; bar
  widgets y 332-352; **clickable (window coords, INFERRED +36): HELP 90-190 · OK 193-293 · REPLACE
  296-396 · INSERT 399-499 · DELETE 502-602 · CANCEL 605-705**; QUEUE rows: click x 185, y = 437 +
  12·(row−1); CHANGE ≈(185,552), HURRY ≈(185,571). Chooser-open test = pixel (160,343) == (103,91,181).
- Pitfalls that bite here (full list in the skill): **pseudocode field offsets are scaled (see the kit)**;
  poke-then-arm (M33), `kill -CONT` after gdb-INT, never Escape on title/REALLYQUIT, **never signal by
  name** (stop drivers with `--mode stop --tag`; a python driver's own argv matches `pkill -f`), **a gdb
  command-list expression on a non-numeric convenience variable aborts the batch** (bake base as a
  literal), **every watchpoint needs a printing `commands … continue end` block**, gdb `printf` needs
  `stdbuf -o0`, **`/proc/pid/mem` list walks take count from +0x10**, evidence-file line cites are the
  citation unit for pseudocode claims, **`sh`/print truncation can fake a "truncated file"**.

## Milestone options (pick ONE)
- **M53k — the accumulation side (THE PICK).** Who writes **base+0xd0** (the field the completion test adds
  to minerals) and base+0x40 (minerals) each turn, and what the `0x4f0b4f cmp [esi+0xcc]+[esi+0x3c],
  price; jge → return` arm direction really means: the pay block is entered when NO base racing the same
  head item reaches the price, yet it debits the full price (`m53j_complet.md` §A-B). Census stores to
  base+0xd0 / +0x40 / +0x30 (bits 23, 31) across `.text` with the cached dump + the store-shape script,
  read base+0xd0/+0x40 across 2-3 turns by pread (no gdb), and pin the writers to address + rendering.
  **Done when** the +0xd0 and +0x40 writers are pinned with a per-turn live delta and the completion arm
  is stated as a rule (or the blocker reported after two failed approaches).
- **Later:** pin the 0x984d38 table writer/loader + who fills the 0x2100000 string arena; 4e4350
  return-code semantics + `DAT_0092a368` source; tech table 0x92fdd4 record layout (research tree); does
  the itemlist cap at capacity (live 15 == 5×3)?; who draws the bars M53e measured; the 4/5-button variant
  (`sub+0xb68 == 0` in play); `FUN_004fe670` research-scaled table bytes; producers of dispatcher modes
  2/3/6; vtable+8 `FUN_00494c40`; `FUN_0059ce10`'s trigger (sole caller FUN_005a0fa0) and its random claim
  grant; why 74/75 bases show pending 0 with a non-empty head; M50c-e, M51b, base+0xc0.
- **Retired premises, do not resurrect:** "+0x4c is the last used index";
  "digit keys 1-9 queue an item"; "the queue refills itself from the head"; "`0x5ac950` returns a WEIGHT";
  "+41 is the mineral price as stored"; "the loader pre-scales ×10"; "OK commits the queued pick";
  "REPLACE needs guard ≠ −1 / is case 2"; "BAR_IGNORED 0x496a91 = bar refusal"; "one bar click runs the
  handler twice"; "secret projects queue as |q| = 39 + idx"; "the chooser bars are Script.txt buttons";
  "enumeration order is arbitrary" (Plan-major); "units and projects interleave" (units first);
  "params 1/2/3/6 are unreachable"; **"0x984d44 is a separate cost table"**; **"FUN_005a6e70's return is a
  cost index"** (boolean); **"aa0 = completion count"** (base index); **"5a6e70's param_4 = pending
  count"**; **"project names come from Script.txt / labels"** (arena ~0x2100000 ← #FACILITIES); **"live
  project idx = alpha row number"** (parsed row + 1); **"the −29 head value is unresolved"** (= Aerospace
  Complex); **"FUN_004e4350 consumes/queues projects"** (class code only); **"FUN_005ac950 prices negative
  queue ids"**; **"the claim table is DAT_00985aa0[72]"** (33 slots @ 0x985b3c, idx−0x27; 0x985aa0..0x985b38
  are other globals); **"the pay pool is base+0xcc + base+0x3c"** (real base+0xd0 + base+0x40);
  **"base+0x20 is an unknown field"** (`short *` halving of base+0x40 = minerals); **"pseudocode field
  offsets are byte offsets"** (short* ⇒ ×2, int* ⇒ ×4, 0x4ef6d0's loop pointer is base+4); **"the record
  +0x18 'Disable' −2 is a completion trigger"**; **"the facility bitmap is at base+0x8a"** (0x8c..0x90).