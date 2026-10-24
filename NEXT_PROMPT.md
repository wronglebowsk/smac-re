# NEXT_PROMPT — SMAC RE, session 64

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53k (**M53k done, session 63**); open: **M53l (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 63 (M53k) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state: game up (`pgrep -x terran.exe` → 2124624), year 2375, our turn (`cur == 3`), n_bases 75,
   pid stable across sessions. The Colony = idx **23 @ 0x95f560** (23×0x130 = 0x1b50 — the 0x95f568 used
   once in session 63 was +8 wrong): fac 3 in-mask, minerals +0x40 = 301, d0 = 13, c0 = 13, progress
   +0x3c = 56, rate +0xcc ~6-8 (recomputed mid-turn), head +0x50 = 147 (unit), pending 0. U.N. Disaster
   Relief = idx 8 (fac 7, OUT-mask): m40 32, d0 7, bitmap bit29 SET (Aerospace built). Our base was idx
   70 @ 0x962d30 in session 62 — the array SLIDES, re-locate by name/faction before any poke. Read-only
   state `scripts/smac_state.py --json`; economy snapshot `scripts/m53k_snap.py` (see kit). Session 63
   ran turns 2371→2375 via `scripts/smac_play.py --turns N` + two gdb watch runs; no pokes.

## Footing — the turn economy pipeline (M48d → M53k, VERIFIED unless marked)

### M53k (session 63): the accumulation side — `evidence/m53k_findings.md` (all cites there)
- **+0xd0 (net income) has exactly ONE writer: FUN_004e93f0** — machine 0x4e9557/0x4e957f:
  `eax = ds:0x8f0d60` (cur base); d0 = [eax+0xc0] − [eax+0xf0] (f0 = DAT_008f0c38+DAT_008f0c4c global
  upkeep; [eax+0xe0] zeroed at 0x4e9562 before the −e0 step, so −e0 is a per-turn no-op); mirror
  +0x94 := d0; c0 += DAT_008f0c70; +0x48 normalized `>>3` in place. Pseudocode == machine disps HERE
  (no short* halving in 4e93f0's renderings — verified vs disasm). Called per base from FUN_004ef6d0's
  base loop (shard_012.c:20861, 22171) + from 4ee410 (20029/20067), 4f5a70 (24180), founder 4e47d0,
  4eb6b0, 4f4060/4f41f0. +0x48 = raw accumulator, += at 4e78e0+0x1455 (0x4e8d35; 58 live stores to
  Colony+0x48 in one turn). Live: d0 = c0−f0 on Colony (13) and U.N. (9 = 12−3); 17/75 d0 changes/turn.
- **+0x40 (minerals) per-turn writers, all inside FUN_004ef6d0:** income add 0x4ef7f6 `minerals += d0`
  (gates: d0 < 0 / head == −38 / +0x30 & 2 → skip; LIVE `eip=0x4ef7f9 new=301`); unit spend A 0x4efedd
  + clamp A 0x4eff20 (M48c; unit path gated affordability 0x4efa5e or dtor-return 0x4f0bfa); project/
  facility spend 0x4f0ca1-0x4f0ca6 `minerals −= edi`; queue drain 0x4f1e3f. **Clamp B** 0x4f0cc3-0x4f0ce9:
  if post-pay minerals > min(10, d0) AND faction in mask → minerals := max(0, min(10, d0)); mirror
  +0x98 := +0x40 always (0x4f0cf2/0x4f0cf5). Explains M48's pinned-zero ours (d0 = −1: income skipped,
  clamp → 0). Event (non-turn) +0x40 writers: FUN_004cce50 trio, 4e47d0 founder (inits new record,
  nb++), 585720 (=0), 58fa40, 507ef0, 504400, 537f90, 4f82b0, 516590/517250, 523a60/523c80,
  5437d0/5439c0, 556690, 55f650 (census `evidence/m53k_ptr_stores.txt`).
- **THE ARM RULE (machine-verified):** completion gate 0x4f0a3d `cmp [edx+0x40], edi; jl → dtor return`
  — STOCK minerals must cover the FULL price; **no accumulation gate**: +0x3c (progress) is DISPLAY
  only (announce 0x4efd49 `turns = (price*(pop+1) − [base+0x3c]) / [base+0xcc]`; M53i pane). Progress
  writer: 0x4ee8c7 in FUN_004ee410 `[base+0x3c] += [base+0xcc]` per turn (LIVE 50→56). Price edi =
  FUN_004e40a0(faction,1,−1) × table[idx].cost_factor; **4e40a0 = 10 for IN-mask factions; for OUT-mask
  it is (era table `&DAT_0068cbb8[DAT_00985aec]` − FUN_00531090 adj) − contact adj — CAN BE 0** (then
  difficulty DAT_0092a290/94 ×/10, DAT_0092ada8==1 → ×9/10). Race scan 0x4f0af0-0x4f0b51 runs ONLY when
  the current base's faction is OUT of mask (gate 0x4f0ac6 `and al,ds:0x985b10; jne → skip`); it keeps
  IN-mask bases with head == current head (−71 special via 0x59a9f0) and dtor-returns unpaid if any has
  `[base+0xd0]+[base+0x40] >= price` — out-mask defers to funded in-mask rivals. In-mask bases skip the
  scan. Claim reachability: projects 39-71 need claim slot == −1 (0x4ef925, claimed → abandon 0x4f07c2);
  facilities idx ≤ 34 need bitmap bit clear (0x4ef982 `bt; jae 0x4ef905`); idx 35..38 direct.
- **Mask live:** 0x985b10 = 0xff08 = bits {3, 8..15}: ours (3) IN; factions 0,1,2,4,5,6,7 OUT. Meaning
  + writer OPEN. Case study: U.N. Disaster Relief (fac 7, out-mask) completed Aerospace Complex
  (head −29) turn 2373→2374 with ZERO pay (price 0): bitmap bit29 flipped, minerals 16→25 = +income 9
  only, clamp skipped (out-mask).
### M53j (session 62): claim array + completion writer — `evidence/m53j_findings.md` (+ `m53j_complet.md`)
- **Claim array = 33 dwords @ 0x985b3c, index = project_idx − 0x27** (projects 39..71 only; slots
  0x985aa0..0x985b38 are other globals: 0x985af4 nb, 0x985b00 year, 0x985b10 mask, 0x985ac4 flags).
  Proof trio: gate `m53i_fn5a6e70.txt:58` reads `&DAT_00985aa0 + idx*4` only for `0x26 < idx`; machine
  0x4ef89f-0x4ef8ac `neg ecx; cmp ecx,0x27; lea edx,[ecx-0x27]`; discriminator `shard_001.c:5424-5444`
  walks 0x985aa0..0x985bc0 branching ON ADDRESS. Writers: exactly 3 store sites whole-.text (census
  `m53j_refs_985aa.txt`): **0x4f0d83** in FUN_004ef6d0 (`mov [eax*4+0x985b3c],edx`, edx = DAT_0068cbb0
  = cur base INDEX, guarded `test/jl`) = the completion writer; 0x59d595 FUN_0059ce10 (re-roll `rand &
  0x80000007` while claimed, sole caller FUN_005a0fa0); 0x41cd7d FUN_0041c8b0 (INFERRED debug). No
  pointer-based writer. **THE POP = FUN_004ef5d0(base_idx)**: pending 0 → return; head ≥ 0 →
  `DAT_0094de84[faction*0x20bc+head] −= 1`; shift base+0x50.. left × pending; base+0x4c −= 1; re-arm
  new head via 0x5a6e70/0x5a73f0; head < −0x26 → 0x446250(0x24); 0x473760(x,y,2,2). Queue shift +
  pending-- + head re-arm live HERE (zero such stores in 0x4ef6d0).
### M53i (session 61): project table + gate — `evidence/m53i_findings.md`
- See `evidence/m53i_findings.md` + Session 61 notes: 72x48 B table @ **0x984d38** (alpha `#FACILITIES`
  verbatim, live idx = parsed row + 1; +0xc cost factor, +0x14 prereq tech via 0x92fdd4/0x985c1c, 0x984d44

### Standing from M53h / M53g / M53d-M53b (do not re-derive)
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, owner@4 (low byte =
  faction), pop@6, +0x30 flags (bits 23/31 = completion path; bit 1 gates income add), **+0x3c progress**,
  **+0x40 minerals**, +0x44 active mirror, +0x4c pending (cap 9), queue @0x50..0x74, **+0x8c..0x90 =
  40-bit facility bitmap** (bit i at +0x8c+(i>>3), mask 1<<(i&7); `DAT_0095da9c`), **+0x48 raw production
  accumulator**, +0x94 = d0 mirror, +0x98 = minerals mirror (equal 75/75), **+0xc0 gross production**,
  **+0xcc rate**, **+0xd0 net income**, +0xe0 (zeroed per turn), +0xf0 = upkeep sum, +0xfc,
  f38 = 0x00dfbe41. `FUN_004ef6d0`'s base loop uses `esi = 0x95da14` = base+4.
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, mask 0x985b10 (0xff08 = {3,8..15}), solo
  0x920434, cap 0x92a370 (10), cur base ptr **0x8f0d60**, **cur base INDEX 0x68cbb0**, era price table
  `&DAT_0068cbb8[DAT_00985aec]`, difficulty 0x92a290/0x92a294, ×9/10 flag 0x92ada8, upkeep globals
  0x8f0c38/0x8f0c4c/0x8f0c70, base array 0x95da10/0x130, unit array 0x933278/52, faction records 0x20bc
  (base 0x92ae14), per-type built counters `DAT_0094de84[faction·0x20bc + type]`, faction names
  0x927894+f·0x24, screen width `DAT_00993a00`, string handles `DAT_00997b20`, message buffer 0x997120,
  labels `FUN_00409690/4096c0(id)` → `programs/labels.txt` line = id + 9. Project state: tech table
  0x92fdd4 (stride 0xb dw, rows ≤ 0x57), tech ownership 0x985c1c[tech], **claims 0x985b3c[33]
  (idx−0x27)**, scenario flags 0x985ac4 (bit31 blocks projects > 38; bit 0x800 Ascent),
  0x985aec/985b50/b54/ba8/bb8, 0x927a98[faction·0x59c] bit 0x200, 0x92a368 (4e4350 mode),
  0x94d438[faction·0x82f] perception.
## Static-reading kit
- **Cached whole-`.text` disassembly: `evidence/m53j_text.txt.gz`** (790702 lines, objdump -d -M intel of
  `programs/terran.exe`, session 62, gzipped for the evidence budget). Locate a VA with
  `zgrep -n '  4ef7f6:' evidence/m53j_text.txt.gz`; windows via `sed -n '/  4f0ca1:/,/  4f0cf5:/p'` on
  `zcat` — **sed anchors must be REAL instruction boundaries** (mid-encoding anchors silently print
  nothing, or run to EOF = 25 MB; prefer `grep -B/-A '  4ee8ca:'`). Rebuild (~1.3 s):
  `objdump -d -M intel --section=.text programs/terran.exe > /tmp/f.txt`. Map VA→fn by bisecting
  `ghidra_out/index.csv` — **COMMA-separated** (col 0 addr, col 1 name; whitespace awk yields empty).
  **VA = file offset + 0x400000.**
- **POINTER-TYPE SCALES IN PSEUDOCODE — the trap of session 62.** Ghidra typed the current-base pointer
  `DAT_008f0d60` and its copies `short *`, so every offset added to them is **HALF** the byte offset
  (`psVar22 + 0x28` == machine `[DAT_008f0d60+0x50]`; `* 0x98` == the 0x130 stride). `int *` DATs scale
  **×4** (`(&DAT_0095da5c)[base*0x4c]` == base+0x4c). `FUN_004ef6d0`'s loop pointer is `0x95da14` =
  **base + 4**. But 4e93f0's renderings are UNSCALED (verified vs disasm) — NEVER trust a pseudocode
  field offset: pin it against a machine-code disp or a live pread.
- **Grep store SHAPES** on the linear disassembly, not literal offsets: dest-in-brackets = STORE;
  `lea`/bare imm = ADDR (address-takers may write through a pointer - check them). Script the disp32
  census: keep instructions whose operands hold an address in a range, classify by shape, group by
  function. Session 63's reusable base-field censuses: `evidence/m53k_ptr_stores.txt`,
  `m53k_field_all.txt`, `m53k_direct_stores.txt`, `m53k_disp_census.txt`.
- Pseudocode `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite evidence-file line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c`; enclosing function via
  `grep -n '^// ==== ' ghidra_out/shard_N.c | awk -F: -v L=<line> '$1<L' | tail -1`.
- **Alpha comment headers name the columns** (`alpha.txt` `:348 #CHASSIS`, `:387 #WEAPONS`, `:422
  #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `:590 #FACILITIES`); `scripts/parse_alpha.py` →
  `data/alpha.json` (list index = live project idx − 1).
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
  Read-only state `scripts/smac_state.py --json`; our base was idx **70** @ 0x962d30 (session 62 —
  re-locate by name, the array slides).
- **Turn driver:** `python3 scripts/smac_play.py --turns N` (background OK with notify true). Stop a
  driver ONLY with `scripts/smac_play.py --mode stop` — never signal by name. **Economy snapshot:**
  `python3 scripts/m53k_snap.py > evidence/x.tsv` — read-only `/proc/pid/mem` walk of all 75 bases
  (header `# year= cur= nb= pid=`, TSV idx name fac x pop f30 f3c f40 f44 pending head f98 fcc fd0);
  diff two snapshots by NAME for per-turn deltas. **Watchpoints:** `scripts/m53k_watch2.gdb` pattern —
  bake addresses as LITERALS (command-list expressions on non-numeric convenience vars abort the
  batch), every watch needs a printing `commands … continue end` block, run
  `gdb -batch -nx -q -p PID -x scripts/x.gdb` under `timeout` backgrounded + drive 1 turn + snapshot in
  ONE job. **Watchpoints fire on VALUE CHANGE, not on stores** — a stable recomputation is silent
  (session 63's "zero D0 hits" = Colony's d0 genuinely stable, not a miss).
## Milestone options (pick ONE)
- **M53l — the production inputs (THE PICK).** Who writes **base+0xc0 (gross production)** and
  **base+0xcc (rate)** each turn (they feed 4e93f0's d0; 4e93f0 itself only ADDs DAT_008f0c70 to c0 and
  normalizes +0x48), what events feed the +0x48 accumulator at 4e78e0+0x1455 (facility yields? tiles?),
  and pin the **mask 0x985b10 semantics + writer** (who sets bits {3,8..15}; why factions 0,1,2,4,5,6,7
  are OUT — defeated? neutral? uncontacted?) plus the era price table `&DAT_0068cbb8[DAT_00985aec]`
  (4e40a0 gave out-mask factions price 0 — read the table values + DAT_00985aec's meaning/writer).
  Census stores to +0xc0/+0xcc/+0x48 across `.text` (reuse `m53k_*` census files), read them per-turn
  with `scripts/m53k_snap.py`-style preads (extend the column set), watch 4e78e0/4ef6d0 if needed.
  **Done when** +0xc0/+0xcc writers are pinned to address + rendering with a live per-turn delta and the
  mask + era-table semantics are stated (or the blocker reported after two failed approaches).
- **Later:** pin the 0x984d38 table writer/loader + who fills the 0x2100000 string arena; 4e4350
  return-code semantics + `DAT_0092a368` source + difficulty 0x92a290/94 source; tech table 0x92fdd4
  record layout (research tree); abandon path 0x4f07c2 + Ascent special 0x4f072e; +0x30 bit 1 writer;
  who sets +0xe0 between recomputes (always 0 live so far); does the itemlist cap at capacity (live
  15 == 5×3)?; who draws the bars M53e measured; the 4/5-button variant (`sub+0xb68 == 0` in play);
  `FUN_004fe670` research-scaled table bytes; producers of dispatcher modes 2/3/6; vtable+8
  `FUN_00494c40`; `FUN_0059ce10`'s trigger (sole caller FUN_005a0fa0) and its random claim grant; why
  74/75 bases show pending 0 with a non-empty head; M50c-e, M51b.
- **Retired premises, do not resurrect:** the full chooser-era list lives in SESSION_NOTES
  sessions 55-63; the live set: "0x984d44 is a separate cost table"; "5a6e70's return is a cost
  index" (boolean); "aa0 = completion count" (base index); "5a6e70 param_4 = pending count";
  "project names come from Script.txt/labels" (arena ~0x2100000); "live idx = alpha row" (row + 1);
  "−29 head unresolved" (= Aerospace Complex); "4e4350 consumes/queues"; "5ac950 prices negative
  ids"; "claim table is 0x985aa0[72]" (33 @ 0x985b3c, idx−0x27); "the pay pool is base+0xcc +
  base+0x3c" (real: +0xd0 + +0x40); "base+0x20 unknown" (short* halving of +0x40); "pseudocode
  offsets are byte offsets" (short* ×2, int* ×4, loop ptr base+4); "+0x18 −2 is a trigger";
  "bitmap at base+0x8a" (0x8c..0x90); **"projects accumulate to completion"** (gate is STOCK
  minerals ≥ full price; +0x3c is display); **"the race scan guards the current (our) base"** (runs
  only for OUT-mask currents, protecting in-mask rivals); **"clamp B applies to every payer"**
  (mask-gated); **"the −e0 term is active"** (e0 zeroed before use); **"4e93f0 pseudocode offsets
  are halved"** (there renderings == machine); **"out-mask AIs pay the same prices"** (era table,
  can be 0); **"watchpoint silence means no writer"** (fires on value change only); **"M48's
  pinned-zero is unexplained"** (income gate + clamp B); **"The Colony @ 0x95f568"** (idx 23 =
  0x95f560).
