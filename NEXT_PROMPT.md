# NEXT_PROMPT — SMAC RE, session 69

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53p (**M53p done, session 68**); open: **M53q (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (75 KB).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 68 (M53p) is the latest milestone.
3. `git status`; `git branch` (a half-finished session left untracked `evidence/m53p_*` files on
   `milestone/m53p` — they are committed now; never commit to main); then
   `python3 scripts/milestone.py start <ID>`.
4. Live state (re-verify `scripts/smac_state.py --json` before any our-turn assumption): pid 2124624
   (`pgrep -x terran.exe`), **year 2383, cur_player 3, nb 76, era 2, mask 0xff08, turn_flags 0x10000,
   TracerPid 0, 332 units**. Our base = idx 70 (fac 3, row `0x962d30` = 0x95da10+70*0x130, the only row
   with owner byte@4 == 3). The Colony = idx 23, owner 2 (names NOT unique — relocate by owner byte).
   Unit slots SHUFFLE (array compaction on unit death): relocate by faction byte@14, never stale indices.
5. **THE MODEL READS A DUMP, NOT LIVE MEMORY**: `scripts/m53p_recon_a.py` consumes
   `evidence/m53o_mem/*.bin`; run `python3 scripts/m53o_mem.py` FIRST and name the refresh in every
   report — the same script gave 50/76 on the 2381 dump, 18/76 (19 patched) on the 2382 dump, 40/76 on
   the 2383 dump.

## Footing — the rebuild model (M48d -> M53p, VERIFIED unless marked)

### M53p (68): the entry scan mask is PER-VISIT state — `evidence/m53p_mask_findings.md` (+ `m53p_livelock_findings.md`; first half `m53p_findings.md`, `m53p_j_findings.md`)
- **`FUN_004e63b0` is the FIRST call inside `FUN_004e78e0`** (`0x4e78e9`, asm line 7 of
  `evidence/m53o_fn4e78e0_asm.txt`). It writes the 21-entry table `0x8f0ccc..0x8f0d1c` with flag values
  0/1/2/4/8 (`mov [ecx+0x8f0ccc],1` 0x4e63e8; `=2` 0x4e6442/0x4e6518; `=0` 0x4e6533; `=4` 0x4e6563;
  `or [eax+0x8f0ccc],8` 0x4e659f/0x4e6635) and then **0x4e6925-0x4e694f builds
  `DAT_008f0d30 = {bit i : table[i] != 0}`** (loop `cmp [eax],0 / je / mov esi,1 / shl esi,cl /
  or edx,esi / add eax,4 / inc ecx / cmp eax,0x8f0d20 / jl`; live check table {0:0xc, 8:0x8} → derived
  0x101 == live). The entry filter `base+0x78 &= (~DAT_008f0d30|1)` (0x4e796a-72) clears exactly those
  steps from the scan pool and the exit overwrites `base+0x78 = processed` (0x4e8b19) ⇒ **the live
  `0x8f0d30`/`0x8f0ccc`/`0x8f0c4c` values describe ONLY the base in `DAT_0068cbb0` (last processed;
  live 70 = ours)**. Bit-8 proof: idx 6 (d78 0xf2951) and idx 47 (0x9589) carry bit 8 ⇒ step 8 was
  scannable at their rebuild while live table[8] = 8 ⇒ the table changed after those rebuilds.
- **Filter every census by self-consistency (`mask_in == processed`)** — only those rows can hold a rule
  gap; the rest are stale-mask contamination. Year-2383 dump: 46 self-consistent rows, **residuals 7:
  idx 3 (fac4, c4 -3), 30 (fac4, c4 -2), 60 (fac4, c4 -2), 51 (fac1, c4 -3), 62 (fac1, c4 -1), 69
  (fac3, c4 -1) — all c4-ONLY (bc/c0/c8 exact) — plus idx 31 (fac2, bc -1)**. Overall cells: 40/76
  exact, bc 27, c0 23, c4 29, c8 0. The c4-only class and its faction set {1,3,4} survive a DRIVEN
  round (2382→2383); its membership moves round to round.
- **Machine fix already applied** (`scripts/m53p_recon_a.py:796-801`): the middle-pass score
  corrections 0x4e818a-0x4e81b6 are `cdq; sub eax,edx; sar eax,1` = trunc(x/2) of the DOUBLED value —
  `cdq` clobbers the `lea edx,[ecx+edi]` (pop+k2) that 0x4e817f set for the 0x4e8182 `cmp ebx,edx`
  guard (ebx = base+0xbc) only, so the machine never subtracts pop+k2.
- **REFUTED this milestone (do not resurrect):** a missing `FUN_004e7070` +1 branch (an independent
  reimplementation disagrees on 0 of the mask tiles of all 76 bases); "fac-2 c0 class" and "Class J =
  entry-state drift" (both were mask contamination); `DAT_008f0d30 = 1` as a scenario constant;
  "`DAT_0068cbb4` freshness marker is -1 while idle" (it reads 70 on our idle turn); "a swap can add
  (0,0,+1) freely" — every vector write goes through the 4-field 0xbc..0xcc loop via `FUN_004e75f0`, so
  field 2 alone changes only between tiles with equal nutrient AND mineral (Base 2,1,1 vs ImprovedSea
  2,1,3 is the only such category pair).
### M53o (67): the rebuilt vector IS the terrain-yield sum — `evidence/m53o_recon_findings.md`
- `base+0xbc` NUTRIENT, `+0xc0` MINERAL, `+0xc4` ENERGY, `+0xc8` PSI (seed-only). `FUN_004e75f0(field,
  fac,bidx,x,y)`: 0->`4e6960`, 1->`4e6d40`, 2->`4e7070`, 3->0 (clears `DAT_008f0cc8`). Per-tile category
  table = alpha `#RESOURCEINFO` verbatim, live **0x926bd8** (9x4): Ocean 1,0,0 / Base 2,1,1 / Bonus
  2,2,2 / Forest 1,2,1 / Recycling 1,1,1 / ImpLand 1,0,0 / ImpSea 2,1,3 / Monolith 2,2,2 / Borehole
  0,6,6. **7 vector add sites**, all `mov [edi+ecx*1-0x4],edx` (edi 0xbc step 4) = lines 249/433/998/
  1108/1186/1273/1343 of `evidence/m53o_fn4e78e0_asm.txt`: 0x4e7c15 scan, 0x4e7ea3 scan-0 special,
  0x4e85bd mp-add, 0x4e8739 swap-out subtract, 0x4e883b swap-in add, 0x4e8951/0x4e8a32 the (dead) undo
  pair. Seed store 0x4e79a5 from `0x94dc34+(fac*0x82f+field)*4` = live 0 for all 8 factions.
  Downstream: bc += `DAT_008f0c6c` 0x4e9344, c0 += `DAT_008f0c70` 0x4e9459 (x2 / x(esi+2)/2 gates
  inactive); **0xc4/0xc8 have NO downstream writers**.
Scan-loop / budget / middle-pass machine rules (frame map, the two-pair candidate dispatch, the
three swap-commit guards, the nibble bookkeeping) live in the skill at
`references/production-rebuild.md` — read that file, do not re-derive them.
### Standing (do not re-derive)
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, **owner byte@4 =
  faction**, byte@5 usually == @4 (idx 0 differs, OPEN), pop byte@6, +0x30 flags (bit 0x8000 set by
  4e78e0, `&= ~0xfe00` at its exit, bit 2 gates one energy test), +0x34 (0x2000/0x4000 tested by
  4e7070), +0x38 = 0x00dfbe41, +0x3c progress, +0x40 minerals, +0x4c pending (cap 9), queue
  @0x50..0x74 (head clear 0xffffffda), +0x78 scan/processed mask, +0x7c budget carry, +0x80 counter (0
  at entry), +0x84 16-nibble AI array (written by 4e78e0), +0x8c..0x90 40-bit facility bitmap, +0x94
  d0 mirror, +0x98 minerals mirror (equal 75/75), **+0xbc/0xc0/0xc4/0xc8 the rebuilt vector**, +0xcc
  rate, +0xd0 net income, +0xe0 (zeroed per turn), +0xec upkeep (pop*2 + c34), +0xf0 upkeep sum,
  +0xac history, +0x48 display accumulator.
- **Unit record (array 0x933278 stride 52, count `0x985af0`):** x u16@0, y u16@2, type byte@4,
  **faction byte@14**, order byte@17, +38 sweep slot, +46 u16 base index, **+48 u16 chain link (walked
  by `FUN_005a6330` loop 0x5a6945-55, exits only on NEGATIVE)**, **+50 u16 chain link (walked by
  `FUN_005ab130` loop 0x5ab223-37, same sentinel)** — terminators are -1 (201/332 and 203/332). Type
  records 0x98ad88/52 (+41 cost factor, +42 plan, +37 read at 0x5a692a), faction records **0x94ae14 +
  fac*0x20bc** (0x92ae14 is the terrain POINTER, not the record base; +0x2880 = `&DAT_0094d694`,
  +0x2e18 production total, +0x2e20 the 4 seed dwords), terrain array base = the DWORD at 0x92ae14
  (live 0x40a6ba8), record = base + (40*y + (x>>1))*0x2c, category = rec[0]&0xe0 (ocean iff < 0x60),
  +8 = u9, +0xc = uc; tech table 0x92fdd4/0xb + availability bitmap 0x985c1c[fac]; claims 0x985b3c[33].
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, unit count 0x985af0, mask 0x985b10 (0xff08),
  era 0x985aec (2), era table 0x68cbb8, **turn flags 0x985ae8 (0 idle, bit1 = end-turn in flight —
  0x10002 was the livelock signature)**, solo 0x920434, cap 0x92a370 (10), cur base ptr 0x8f0d60, cur
  base INDEX 0x68cbb0, marker 0x68cbb4 (= 70 on our idle turn), **per-visit block: 0x8f0ccc..0x8f0d1c
  table + 0x8f0d30 mask + 0x8f0c4c (score denominators 0x4e821f-31, live 7) + 0x8f0c68 (rebuild
  budget, live 0)**, economy slots 0x8f0c6c/70/34/38, cc8 = psi overflow, map width 0x692184 = 40,
  0x92a378/37c = 80, 0x92a394 = 0 (no wrap), scenario constants 0x985b48 = 4 (only ref: `cmp`
  0x4e74e9), 0x985bc0 = 2 (one store 0x425fc3), 0x985db8/0x985dc4 = 0, 0x92a27c = 2 (K), 0x92a2a4 = 5,
  0x92a2cc = 59, **0x91c628 is NOT constant (0 → 1 observed)**.
## Static-reading kit
- **Cached whole-`.text` disassembly `evidence/m53j_text.txt.gz`** (790702 lines, objdump intel).
  Locate a VA: `zgrep -n '  4e78e9:' evidence/m53j_text.txt.gz`; windows: `gunzip -c … | sed -n 'A,Bp'`
  (plain `sed` on the .gz returns nothing). **VA = file offset + 0x400000.** VA→function:
  `awk -v A=0x005ab223 -F, 'NR>1 && $1<=A {n=$2;p=$1} END{print p,n}' ghidra_out/index.csv` (COMMA
  separated; NOTE awk braces break inside python f-strings).
- **POINTER-TYPE SCALES — the trap:** Ghidra types some DATs `short *` (offsets are HALF the byte
  offset) or `int *` (x4). Never trust a pseudocode field offset; pin against machine disp or live
  pread. `DAT_0092ae14` renders the stored POINTER value, not the record base.
- Pseudocode: `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite your own file's line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c`; alpha headers name the columns (`alpha.txt` :132 #RESOURCEINFO,
  :560 #UNITS, :590 #FACILITIES, :710 #RESOURCES); `scripts/parse_alpha.py` -> `data/alpha.json`.
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800x600).
  Preflight: no gdb, TracerPid 0, `ptrace_scope` 0. `xwd` needs **`-display :99`** (DISPLAY=:0 fails).
- **Turn driver:** `python3 scripts/smac_play.py --turns N --timeout S --no-escape S'` where
  **`--no-escape N` = "never press Escape during the first N seconds" — set N > the run timeout**,
  because the driver classifies the "Do you really want to quit?" dialog as a title screen (its banner
  IS the game title) and its own Escape press opens that dialog; clear it with `xdotool windowfocus
  <win>` + Escape (NEVER click). **This checkout has NO `--mode stop` in `smac_play.py`** (args:
  --turns --timeout --no-escape --verbose --order --unit --turns-after --tag --no-verify --key-only) —
  bound a backgrounded driver with `timeout <run>` from the shell or let it finish; never
  `pkill -f`/`pgrep|kill` by name.
- **Stalled round? Check the livelock signature first:** `turn_flags` (0x985ae8) bit 1 stuck set + main
  thread `R` at ~60% CPU + static screen ⇒ a unit-chain self-link (`unit+48`/`unit+50` walks exit only
  on a NEGATIVE link). Census recipe + the poke fix: `evidence/m53p_livelock_findings.md`. Pokes via
  `/proc/pid/mem` while no tracer, always read back.
- **PROPOSAL vote pane** (stalls the AI phase): bars in TRUE window coords YEA (310,495) / NAY (398,
  495) / ABSTAIN (485,495), then one OK bar (393,495); the `YEA: 2 NAY: 3` line is the TALLY. Capture
  `xwd -display :99 -root -silent` + ffmpeg 2x upscale + tesseract; click after `xdotool windowfocus`.
- **Snapshots:** `python3 scripts/m53l_snap.py > evidence/x.tsv` (read-only walk of all bases; header
  `# year cur nb era mask pid`; after f98 cols bc c0 c4 c8 d0 cc f0) and `python3 scripts/m53o_mem.py`
  (refreshes the dump the model reads). **Model:** `python3 scripts/m53p_recon_a.py $(seq 0 75)` —
  parse with `evidence/m53p_swap_parse.py` (`parse()` has no mask_in; extend the header regex with
  groups 7/8 for `mask_in`/`processed`) or `evidence/m53p_fresh_parse.py`.
- **Watchpoints: x86 DR budget = 4 hw slots** (8-byte windows need 8-alignment = 2 DRs each); pair with
  the 10 Hz `/proc/mem` poller `scripts/m53m_poll.py`. Bake addresses as LITERALS, print `commands …
  continue end` per site, `stdbuf -o0`, `gdb -batch -nx -q -p PID -x scripts/x.gdb` backgrounded +
  drive + snapshot in ONE job (`scripts/m53n_drive.py` = proven template). **Watchpoints fire on VALUE
  CHANGE, not on stores** — a same-value rewrite is INVISIBLE.
## Milestone options (pick ONE)
- **M53q — make the model RECOMPUTE the per-base scan pool (THE PICK).** Decode what sets each entry of
  the 21-entry table `0x8f0ccc` to 1 / 2 / 4 / 8 inside `FUN_004e63b0` (store sites 0x4e63e8, 0x4e6442,
  0x4e6518, 0x4e6533, 0x4e6563, 0x4e659f, 0x4e6635; the function is ~1450 lines per
  `ghidra_out/index.csv`, adjacent `FUN_004e60c0`/`FUN_004e6240`), including how `DAT_008f0c4c` (live 7)
  is produced, then implement the recompute in `scripts/m53p_recon_a.py` so each base's `mask_in` comes
  from decoded inputs instead of one stale global. **Done when** the self-consistent row count is
  materially above 46/76 (target: all 76) AND the residual set is re-measured on a fresh dump — ideally
  the 7 residuals (idx 3/30/60 fac4, 51/62 fac1, 69 fac3 c4-only; idx 31 fac2 bc -1) collapse to a
  named machine rule.
- **Later:** the c4-only rows once the pool is decoded; `unit+48`/`unit+50` chain semantics and whether
  the array compaction leaves stale links by design (a real game bug worth naming); what sets
  `turn_flags` bit 16 (0x10000 persists on our idle turn); unit+38 slot semantics + consumers of
  0x8f0c74/78; who writes the seed dwords (faction+0x2e20); `base+0x84` nibble-array semantics;
  `DAT_008f0cc8` consumer; who sets +0xe0 between recomputes; byte@5 meaning; who first sets c0 at
  founding (4e47d0 never fired in a normal round); the mid-visit 3-point d0 trace (pre / at 0x4ef7f6 /
  post); the 417ee0 UI row-loop identity behind the 13x; M50c-e, M51b.
- **Retired premises, do not resurrect:** "bc/c0/cc are persistent accumulators whose only writers are
  4e92c0/4e93f0" (4e78e0 REBUILDS the vector); "4ef6d0 never runs" / "re-runs the block twice"; "the
  round walks all bases in index order" (grouped by owner, ours LAST); "bc/c0 gain per sweep fire";
  "the Colony is fac 3" (owner 2, idx 23); "4e40a0 tests the whole mask dword" (LOW byte only);
  "pseudocode offsets are byte offsets" (short* x2, int* x4); "claim table 0x985aa0[72]" (33 @
  0x985b3c); "the PROPOSAL pane's `YEA: 2 NAY: 3` is a key hint"; "4e3470's 19 hits = calls";
  "0x4f1e3f drains base+0x40" (it clears the queue head); **"base+0x78 entry mask = ~(pop|1)"** and
  **"DAT_008f0d30 = 1 is a scenario constant"** (4e63b0 rebuilds it per entry from 0x8f0ccc); "the tail
  loop 0x4e8b6f-0x4e8d48 feeds the vector" (writes only +0x48); "c4/c8 have downstream writers" (none);
  **"the middle-pass corrections subtract pop+k2 then halve"** (cdq kills that edx — it is trunc(x/2)
  of the doubled value); **"the model reads live memory"** (it reads `evidence/m53o_mem/*.bin`);
  **"the freshness marker 0x68cbb4 is -1 while idle"**; **"0x91c628 = 0 is constant"**; and the
  session-68 "Class S / Class J" residual framing (mask contamination — see
  `evidence/m53p_mask_findings.md`).
