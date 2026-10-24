# NEXT_PROMPT — SMAC RE, session 65

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53l (**M53l done, session 64**); open: **M53m (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 64 (M53l) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state: game up (`pgrep -x terran.exe` → 2124624), year 2376, **cur_player = 7 — NOT our turn;
   drive `scripts/smac_play.py --turns N` until `scripts/smac_state.py --json` shows cur_player == 3
   before any our-turn assumption**, nb 75, pid stable across sessions. Era 2, mask 0xff08. Our base =
   idx 70 'Climactic Research' — the ONLY base with owner byte@4 == 3 (census {1:6,2:44,3:1,4:7,5:3,
   6:5,7:9}). The Colony = idx 23, owner byte 2 (old "fac 3" note dead — names are NOT unique across
   factions; re-locate by owner byte + name). Economy snapshot `scripts/m53l_snap.py` (cols after f98
   are bc c0 c4 c8 d0 cc f0 — header labels stale). Read-only state `scripts/smac_state.py --json`.

## Footing — the turn economy pipeline (M48d → M53l, VERIFIED unless marked)

### M53l (session 64): production inputs — `evidence/m53l_findings.md` (all cites there)
- **+0xcc (rate) sole writer 0x4e937b in FUN_004e92c0** (per-base; 12 callers = pipeline passes):
  `bc += DAT_008f0c6c` (0x4e9344); `ec = pop(base+6) × DAT_0092a27c(=2, store 0x5784f2) + DAT_008f0c34`
  (0x4e9362); `cc = bc − ec`; HQ-bit bump 0x8f0c48 := faction+0x2880 +2 (0x4e92f5-32a); progress clamp
  (cc<0 ∧ prog==0 → −1; cc≥0 ∧ prog<0 → 0); faction total `&DAT_0094dc2c[f·0x20bc] += max(cc,0)` cap 99
  iff DAT_008f0d64 == 1. Live Colony: 28 − 22 = 6 ✓ (22 = pop 11 × 2).
- **+0xc0 (gross) exactly 3 stores, all FUN_004e93f0:** 0x4e943f `×= 2` gated (DAT_00985ba8 ≥ 0 ∧
  base[ba8] same faction ∧ head ∈ [−37,−34]); 0x4e9459 `+= DAT_008f0c70`; 0x4e9525 `×= (esi+2)/2` where
  esi = count of FUN_00421fe0(19/20/21/22, cur_idx, 0) true + same-faction flags on bases DAT_00985bac
  /0x985bb0 (all −1 live → mult 1.0). d0 = c0 − (c38+c4c) − e0 and its stores stand from M53k.
- **bc/c0/cc PERSISTENT**: per-turn recompute is idempotent when c6c = c70 = 0 — live 75/75 stable over
  turn 2375→2376 (`evidence/m53l_delta.txt`). Income: 21/24 changed bases min += d0 exactly; 2 (UN DR,
  Hawk) += POST-recompute d0 → **income add reads d0 AFTER 4e93f0 in the same base pass**; 3 bases got
  +1..+3 EXTRA beyond d0 (UN HQ +3, UN Education +2, Morgan Metallurgy +1) — unexplained; prog += cc
  9/9 ✓ (0x4ee8c7).
- **Feeder FUN_004e8d60** (pipeline stage 1, NAMED.md 4f5a70 row): zeroes 0x8f0c2c/34/38/4c/6c/70/74/78
  /d38; pop-scaled table local_34[9]; loops units (`< DAT_00985af0` = 339) over type records
  0x98ad88+type·0x34, tile = (x×0x692184(40)+y)>>1 → terrain `DAT_0092ae14 + tile·0x2c` (VALUE-vs-addr
  rendering OPEN); accumulates c6c[·] += yield, c4c += 1 per unit upkeep, counters 0x94dc24/0094d684.
  **What makes c6c/c70 nonzero = M53m.**
- **+0x48** = display value: += |ebx|>>1 per facility-bitmap hit in 4e78e0 21-iter loop 0x4e8b6f-4e8d48
  (popcount 0x507440, mult 0x692184, gates 0x92a378/37c = 80), then normalized in 4e93f0 to (x+50)/100
  (m53k_fn4e93f0.txt:52-134). Walked table identity OPEN.
- **Mask 0x985b10 = TWO BYTES** (b10 = facs 0-7, b11 = 8-15; 4e40a0 tests LOW byte only 0x4e40b5).
  Writers pinned: 5a0fa0 0x5a1091 `b11 := 0xff` (global reset, zeros 0x985ae8..afc); 597ee0 0x59814f
  /15c alien-presence loop (edi 0..7); 59ec90 0x5a07a4/7d3; 4df630 0x4df82e/9a3 `b10 := 1<<player | 0`
  (gated FUN_006266e6; alt path `b10 := b11 & 0xfe`); 4e0720 0x4e08ca/8d0 elimination (clear bit both
  bytes, then walks bases nb−1..0). INFERRED semantics: standard-rules set = player + aliens 8-15; the
  7 AI human factions sit OUT (era prices, no clamp B, race-scan targets them).
- **Era price table 0x68cbb8 = DIRECT dwords {13,12,11,10,8,7}** (eras 0-5, ASCII junk after — NOT
  pointers; sole .text ref 0x4e40fe). 4e40a0 out-mask: `table[DAT_00985aec] − (531090(0x985b30,0) != 0)
  − ebx(!solo ∧ bit(0x985b30) in b10)`; neg/sbb/neg = nonzero-BOOLEAN idiom (not magnitude); then
  ×0x92a290/94÷10 (both 10 → ×1), ×9/10 iff 0x92ada8 == 1 (live 2). Live era 2 → 11. **DAT_00985aec:
  ZERO direct stores whole-.text** — writer pointer-based/data-init OPEN. M53k's "UN price 0" re-flag:
  consistent with the race-scan unpaid return, not literal price 0.
### M53k (session 63): accumulation side — `evidence/m53k_findings.md`
- d0 single writer 4e93f0 (0x4e9557/57f; mirror +0x94; e0 zeroed before use; called per base from
  4ef6d0's loop 20861/22171 + 4ee410, 4f5a70, founder 4e47d0, 4eb6b0, 4f4060/4f41f0). +0x40 per-turn
  writers all in 4ef6d0: income add 0x4ef7f6 (gates d0<0 / head==−38 / +0x30&2), unit spend 0x4efedd +
  clamp A 0x4eff20, project spend 0x4f0ca1-0x4f0ca6, drain 0x4f1e3f; clamp B 0x4f0cc3-0x4f0ce9 (in-mask
  payers → max(0,min(10,d0))); mirror +0x98 := +0x40 always. Arm: gate 0x4f0a3d STOCK minerals ≥ FULL
  price (edi = 4e40a0 × table +0xc cost factor); race scan 0x4f0af0 only for OUT-mask current (gate
  0x4f0ac6) defers to funded in-mask rivals; +0x3c progress DISPLAY-only (+= [base+0xcc] at 0x4ee8c7;
  announce 0x4efd49 turns = (price·(pop+1) − prog)/cc). Claim reachability: projects 39-71 need claim
  slot −1 (0x4ef925, claimed → abandon 0x4f07c2); facilities ≤ 34 need bitmap bit clear (0x4ef982).
  Event +0x40 writers census `m53k_ptr_stores.txt`. Case: UN DR (out-mask) completed Aerospace Complex
  turn 2373→2374 with ZERO pay (bitmap bit29 flipped, minerals +income only, clamp skipped).
### M53j (session 62): claim array + completion — `evidence/m53j_findings.md`
- Claims = 33 dwords @ 0x985b3c, index = project_idx − 0x27 (projects 39..71). Completion writer
  0x4f0d83 in 4ef6d0 (edx = DAT_0068cbb0 cur base INDEX). THE POP = FUN_004ef5d0(base_idx): pending 0 →
  return; built-counter −= 1; queue shift base+0x50.. left; +0x4c −= 1; re-arm head via 5a6e70/5a73f0.
  Other claim writers 0x59d595 (rand re-roll, caller 5a0fa0), 0x41cd7d (debug INFERRED). Slots
  0x985aa0..0x985b38 = other globals (af4 nb, b00 year, b10 mask, ac4 flags).
### Standing (do not re-derive)
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, **owner byte@4 =
  faction** (machine: 4e92c0/4e93f0 use it as `f·0x20bc` record index; ground truth idx 70 ours = 3,
  idx 8 UN = 7; byte@5 usually == byte@4, idx 0 differs 2/6 — OPEN), pop byte@6, +0x30 flags (bits 23
  /31 completion path, bit 1 gates income add), +0x3c progress, +0x40 minerals, +0x44 active mirror,
  +0x4c pending (cap 9), queue @0x50..0x74, +0x8c..0x90 40-bit facility bitmap (bit i at +0x8c+(i>>3),
  `DAT_0095da9c`), +0x94 d0 mirror, +0x98 minerals mirror (equal 75/75), +0xbc bc accumulator, +0xc0
  gross, +0xc4/+0xc8 semi-active (values 5..11; 2 changed −1/−2 in one turn — OPEN), +0xcc rate, +0xd0
  net income, +0xe0 (zeroed per turn), +0xec upkeep (pop×2 + c34), +0xf0 upkeep sum, +0xfc; f38 =
  0x00dfbe41. 4ef6d0 loop ptr 0x95da14 = base+4. **Per-base pipeline:** FUN_004f5a70(base_idx) runs
  4e8d60 → 4e78e0 → 4e92c0 → 4e93f0 → 4eaa10 → 4ef6d0 → 4f26e0 → 4ee410 per base per round (+ second
  pass with DAT_008f0d64 = 1; NAMED.md 4f5a70 row).
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, unit count 0x985af0 (339), mask 0x985b10
  (0xff08), era 0x985aec (2), 0x985b30 (2), era table 0x68cbb8 {13,12,11,10,8,7}, solo 0x920434, cap
  0x92a370 (10), cur base ptr 0x8f0d60, cur base INDEX 0x68cbb0, difficulty 0x92a290/94 (10/10),
  0x92ada8 (2), economy block 0x8f0c2c/34/38/48/4c/6c/70/d38 (recomputed per base by 4e8d60), upkeep
  into d0 = 0x8f0c38+c4c, base array 0x95da10/0x130, unit array 0x933278/52, type records 0x98ad88/52
  (+41 cost factor), faction records 0x92ae14+f·0x20bc (+0x2880 = `&DAT_0094d694`, +0x2e18 = 0x94dc2c
  production total; terrain line `DAT_0092ae14 + tile·0x2c` = VALUE not address — verify), built
  counters 0x94de84[f·0x20bc+t], scratch 0x94d684/dc24, map width 0x692184 = 40, 0x92a378/37c = 80,
  claims 0x985b3c[33], scenario flags 0x985ac4 (bit31 blocks projects > 38; 0x800 Ascent), special
  base idxs 0x985ba8/bac/bb0 (−1), 0x985ae8 flags (0x10000), 0x927a98[f·0x59c] bit 0x200, 0x92a368
  (4e4350 mode), 0x94d438[f·0x82f] perception, faction names 0x927894+f·0x24 (mostly empty live),
  labels `FUN_00409690/4096c0(id)` → `programs/labels.txt` line = id + 9.
## Static-reading kit
- **Cached whole-`.text` disassembly: `evidence/m53j_text.txt.gz`** (790702 lines, objdump -d -M intel
  of `programs/terran.exe`). Locate VA: `zgrep -n '  4ef7f6:' evidence/m53j_text.txt.gz`; windows via
  `grep -B/-A '  4ee8ca:'` — sed range anchors must be REAL instruction boundaries (mid-encoding anchors
  silently print nothing or run to EOF = 25 MB). Rebuild (~1.3 s): `objdump -d -M intel
  --section=.text programs/terran.exe > /tmp/f.txt`. VA→fn by bisecting `ghidra_out/index.csv` —
  **COMMA-separated** (col 0 addr, col 1 name). **VA = file offset + 0x400000.** Session 64 censuses:
  `m53l_stores_disp.txt` (base-disp stores), `m53l_mask_refs.txt`, `m53l_era_refs.txt`,
  `m53l_upkeep_globals.txt`; session 63: `m53k_ptr_stores.txt`, `m53k_direct_stores.txt`.
- **POINTER-TYPE SCALES IN PSEUDOCODE — the trap:** Ghidra typed `DAT_008f0d60` copies `short *` in
  4ef6d0 renderings, so offsets there are HALF the byte offset (`psVar22 + 0x28` == machine +0x50;
  `* 0x98` == 0x130 stride); `int *` DATs scale ×4; 4ef6d0's loop pointer = base+4. But 4e92c0/4e93f0
  renderings are UNSCALED (verified vs disasm twice). `DAT_008f0d60[3]` = byte +0x6 (pop). NEVER trust
  a pseudocode field offset: pin against machine disp or live pread.
- **Grep store SHAPES**, not literal offsets: dest-in-brackets = STORE; for `ds:` stores use the
  mnemonic-comma test but FILTER `test/cmp` (they carry commas too). `lea`/bare imm = ADDR
  (address-takers may write through a pointer — check them). Skip ebp/esp-dest frame noise.
- Pseudocode `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite evidence-file line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c`; enclosing fn via `grep -n '^// ==== ' ghidra_out/shard_N.c |
  awk -F: -v L=<line> '$1<L' | tail -1`.
- **Alpha comment headers name the columns** (`alpha.txt` `:348 #CHASSIS`, `:387 #WEAPONS`, `:422
  #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `:590 #FACILITIES`); `scripts/parse_alpha.py` →
  `data/alpha.json` (list index = live project idx − 1).
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600);
  launch-if-down command verbatim in the skill. Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
- **Turn driver:** `python3 scripts/smac_play.py --turns N` (background OK with notify true). Stop a
  driver ONLY with `scripts/smac_play.py --mode stop` — never signal by name. After a run cur may sit
  on an AI faction — drive until cur_player == 3. **Economy snapshot:** `python3 scripts/m53l_snap.py >
  evidence/x.tsv` — read-only `/proc/pid/mem` walk of all bases (header `# year cur nb era mask pid`;
  after f98 the cols are bc c0 c4 c8 d0 cc f0 — stale labels); diff two snapshots by NAME. **Watch-
  points:** `scripts/m53k_watch2.gdb` pattern — bake addresses as LITERALS, printing `commands …
  continue end` per watch, `gdb -batch -nx -q -p PID -x scripts/x.gdb` under `timeout` backgrounded +
  drive 1 turn + snapshot in ONE job. **Watchpoints fire on VALUE CHANGE, not stores** — stable
  recomputation is silent.
## Milestone options (pick ONE)
- **M53m — what makes c6c/c70 nonzero (THE PICK).** The 4e8d60 unit filter: read the sweep body fully
  (`evidence/m53l_fn4e8d60.txt`, 216 lines — mining/worker order check? tile yield table? facility
  multipliers?) and confirm live: census unit records (0x933278/52) for an order/worker field, find or
  issue a mining order, watch `0x8f0c6c`/`0x8f0c70` + one producing base's `+0xbc/+0xc0` across one
  pipeline pass (watchpoints + 1 turn, m53k_watch2 pattern). Close ≥1 small open too: DAT_00985aec era
  writer (zero direct stores — grep `0x985aec` lea/address-takers + save/load paths); +0xc4/+0xc8
  meanings; the 3-base extra-income anomaly (other +0x40 writers, e.g. 4cce50 trio, firing on those
  bases?); who first sets c0 at founding (4e47d0 → 4e93f0 with what c70). **Done when** the
  nonzero-trigger is pinned to address + live delta (or blocker reported after two failed approaches).
- **Later:** 0x984d38 table writer/loader + who fills the 0x2100000 string arena; 4e4350 return-code
  semantics + `DAT_0092a368` source; tech table 0x92fdd4 record layout (research tree); abandon path
  0x4f07c2 + Ascent special 0x4f072e; +0x30 bit 1 writer; who sets +0xe0 between recomputes (always 0
  live); does the itemlist cap at capacity (live 15 == 5×3)?; who draws the bars M53e measured; the
  4/5-button variant (`sub+0xb68 == 0` in play); `FUN_004fe670` research-scaled table bytes; producers
  of dispatcher modes 2/3/6; vtable+8 `FUN_00494c40`; `FUN_0059ce10`'s trigger + random claim grant;
  why 74/75 bases show pending 0 with a non-empty head; byte@5 meaning; M50c-e, M51b.
- **Retired premises, do not resurrect:** the full chooser-era list lives in SESSION_NOTES sessions
  55-64; the live set: **"bc/c0/cc are recomputed from scratch each turn"** (PERSISTENT; per-turn pass
  idempotent when c6c = c70 = 0); **"Colony fac 3"** (owner byte@4 = 2 at idx 23); **"era table =
  pointer array"** (direct dwords {13,12,11,10,8,7} @ 0x68cbb8); **"4e40a0 tests the whole mask
  dword"** (LOW byte only); **"UN price 0 = literal price"** (race-scan unpaid path INFERRED);
  **"byte@4 is type/cluster"** (it IS faction); **"snap column labels are trustworthy"** (unpack
  contiguous ranges, label from true offsets); "0x984d44 is a separate cost table"; "5a6e70's return
  is a cost index" (boolean); "aa0 = completion count" (base index); "live idx = alpha row" (row + 1);
  "claim table is 0x985aa0[72]" (33 @ 0x985b3c, idx−0x27); "the pay pool is base+0xcc + 0x3c" (real:
  +0xd0 + +0x40); "pseudocode offsets are byte offsets" (short* ×2, int* ×4, loop ptr base+4);
  "bitmap at base+0x8a" (0x8c..0x90); "projects accumulate to completion" (gate is STOCK ≥ full price;
  +0x3c display); "the race scan guards the current (our) base" (runs only for OUT-mask currents);
  "clamp B applies to every payer" (mask-gated); "the −e0 term is active" (e0 zeroed before use);
  "watchpoint silence means no writer" (fires on value change only); "M48's pinned-zero is
  unexplained" (income gate + clamp B); "The Colony @ 0x95f568" (idx 23 = 0x95f560).
