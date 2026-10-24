# NEXT_PROMPT — SMAC RE, session 68

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53o (**M53o done, session 67**); open: **M53p (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 67 (M53o) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state: game up (`pgrep -x terran.exe` -> 2124624), year 2381, cur_player 3, nb 76, era 2, mask
   0xff08, TracerPid 0, pid stable across sessions — **re-verify `scripts/smac_state.py --json` before
   any our-turn assumption.** Our base = idx 70 'Climactic Research' row **0x962d30** (= 0x95da10 +
   70*0x130) — the ONLY base with owner byte@4 == 3. The Colony = idx 23, owner 2 (names NOT unique
   across factions — relocate by owner byte + name). Unit slots SHUFFLE (array compaction): relocate
   units by faction byte@14, never stale indices. Post-66 census: NO crawler-shaped unit remains, so
   `c6c/c70` read 0 and bc/c0 are pure rebuilds; base70's live bc 12 = rebuild 11 + 1 stale crawler add.

## Footing — the turn-economy pipeline (M48d -> M53o, VERIFIED unless marked)

### M53o (session 67): the production vector IS the terrain-yield sum — `evidence/m53o_recon_findings.md`
(all cites there; model `scripts/m53o_recon.py`; chain/income-extra note
`evidence/m53o_chain_findings.txt` — 4eb6b0 re-runs rewrite d0/cc AFTER the income add 0x4ef7f6)
- **`base+0xbc` = NUTRIENT, `+0xc0` = MINERAL, `+0xc4` = ENERGY, `+0xc8` = PSI (seed-only).**
  `FUN_004e75f0(field,fac,bidx,x,y)`: field0->`4e6960`, field1->`4e6d40`, field2->`4e7070`, field3->0
  and clears `DAT_008f0cc8` => 0xc8 has NO tile term (76/76 live). Naming chain: alpha `#RESOURCES`
  (programs/alpha.txt:710) Nutrient/Mineral/Energy/Psi == the `#RESOURCEINFO` column order (:132) ==
  the dispatcher's field order. Per-tile category table = **alpha `#RESOURCEINFO` verbatim, live
  @0x926bd8** (9x4): Ocean 1,0,0 / Base 2,1,1 / Bonus 2,2,2 / Forest 1,2,1 / Recycling 1,1,1 /
  ImpLand 1,0,0 / ImpSea 2,1,3 / Monolith 2,2,2 / Borehole 0,6,6.
- **The vector has exactly 7 add sites**, all `mov [edi+ecx*1-0x4],edx` (edi walks 0xbc step 4) = lines
  249/433/998/1108/1186/1273/1343 of `evidence/m53o_fn4e78e0_asm.txt` (1602 lines; the older
  `m53o_findings.md` cites in that region drift ~10 low): scan loop, scan-0 special, swap -loss, swap
  +gain, undo -gain, undo +loss, non-swap +gain. `grep 'add    DWORD PTR'` = 0 hits => every
  accumulator is a MOV of a computed sum. Seed store 0x4e79a5 from `0x94dc34+(fac*0x82f+field)*4` =
  **live 0 for all 8 factions**. Downstream adds to strip: bc += `DAT_008f0c6c` @0x4e9344; c0 +=
  `DAT_008f0c70` @0x4e9459 (+ x2 / x(esi+2)/2 gates, inactive); **0xc4/0xc8 have NO downstream writers**.
- **Control flow**: entry `base+0x30 &= 0xffff7fff`, `base+0x80 = 0`, **`base+0x78 &= (~DAT_008f0d30|1)`**
  (0x4e7968-72, live 0x8f0d30 = 1 — NOT `~(pop|1)`); skip flag `[ebp-0x30]` = 1 iff out-of-mask OR
  (bit6 **and** bit31 of base+0x38) => only our fac 3 takes flag 0; scan loop s 0..20 (cap `cmp eax,0x15`
  asm:261) over the spiral XOFF@0x67850c / YOFF@0x678990 (80 offsets; mask bits alias 32..79 -> 0..15),
  budget = pop+1 spent per scan INCLUDING out-of-bounds; `if (budget == base+0x80 + base+0x7c) goto
  LAB_004e8a47` skips scan-0 special AND the whole middle pass; middle pass = swap mode iff
  `budget <= c80+c7c` (one attempt then unconditional break) else add-best-gain, else AI-table nibble
  write to `base+0x84[c80]`; continue while `(c80+c7c < budget) || ((pop+1)*2 < base+0xbc)`; exit
  `base+0x78 = processed` (0x4e8b19), `base+0x7c = DAT_008f0c68` (0x4e8b28), `base+0x30 &= ~0xfe00`,
  history shift 0xac<-0xbc.
- **Model state**: exact per field over all 76 live bases bc 56/76, c0 48/76, c4 46/76, c8 76/76;
  **36/76 full matches, factions {2,4,5,6,7}**; pinned idx 0 (fac2) / 4 (fac5) / 10 (fac6) exact, idx 70
  bc/c0/c8 exact with c4 3 vs 4. Residual classes: (a) **c4-only negative, 12 rows (-1..-5, facs 1,3,4,7,
  never 2/5/6)** = a +1 branch inside `4e7070` [INFERRED]; (b) idx 3/23 = stale ENTRY state (the model is
  pure in entry state; idx 23 needs visit-time pop 13, live 12); (c) 28 c0 mismatches concentrated in
  fac 2 (+2..+5 model-high), unattributed.

### M53n (66) / M53m (65) / M53l (64) / M53k-j (63/62) — pointers
- **M53n `evidence/m53n_findings.md`**: `FUN_004f5a70(base_idx)` once per base per round (76/76 live),
  ONE `.text` call site (`0x5206d3` in `FUN_00520540`); visits grouped by owner byte@4 into faction-turn
  order, ours (fac 3, idx 70) LAST before year++; 247 block executions/round = pass1 76 + pass2 76 +
  4f41f0-B 34 + -A 4 + 4eb6b0 55 + 4ee410-B 1 + pass3 1; the bc-add 0x4e9331-0x4e934a is UNGATED;
  `DAT_0068cbb4` freshness marker guards 4f5a70's pass3 and 4ef6d0's two block sites (0 hits).
  **Session-67 corrections: `4ef6d0` itself RUNS once per visit (zero-arg call `0x4f5adc`) — only its
  guarded block sites are dead; and `4e3470`'s 19 watch hits = base SWITCHES, not calls.**

### Standing (do not re-derive)
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, **owner byte@4 =
  faction**, byte@5 usually == @4 (idx 0 differs, OPEN), pop byte@6, +0x30 flags (bits 23/31 completion
  path, bit 1 gates the income add, bit 2 tracks a c4 branch OPEN, 0x8000 set by 4e78e0, `&= ~0xfe00` at
  its exit), +0x34 (0x2000/0x4000 tested by 4e7070), +0x38 = 0x00dfbe41 on every base sampled (bit6 +
  bit31 feed the 4e78e0 skip flag), +0x3c progress, +0x40 minerals, +0x44 active mirror, +0x4c pending
  (cap 9), queue @0x50..0x74 (head clear value 0xffffffda), **+0x78 scan/processed mask**, **+0x7c budget
  carry**, +0x80 counter (0 at entry), **+0x84 16-nibble AI-table array — WRITTEN by 4e78e0 (0x4e7d5a,
  0x4e7d73, 0x4e8497, 0x4e84af, 0x4e8af8)**, +0x8c..0x90 40-bit facility bitmap (`DAT_0095da9c`; bit 0x1d
  gates the seed halve, bits via `FUN_00507410`), +0x94 d0 mirror, +0x98 minerals mirror (equal 75/75),
  **+0xbc nutrient / +0xc0 mineral / +0xc4 energy / +0xc8 psi = the vector 4e78e0 REBUILDS every block
  execution (c8 seed-only)**, +0xcc rate, +0xd0 net income, +0xe0 (zeroed per turn), +0xec upkeep
  (pop*2 + c34), +0xf0 upkeep sum, +0xac history, +0x48 display accumulator. f38 = 0x00dfbe41.
  4ef6d0 loop ptr 0x95da14 = base+4.
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, unit count 0x985af0, mask 0x985b10 (0xff08),
  era 0x985aec (2), era table 0x68cbb8 {13,12,11,10,8,7} (direct dwords), solo 0x920434, cap 0x92a370
  (10), cur base ptr 0x8f0d60, cur base INDEX 0x68cbb0, freshness marker 0x68cbb4 (-1 while idle),
  **0x8f0d30 = 1 (entry-mask source for base+0x78; writers 0x4e6929/0x4e694f)**, economy block
  0x8f0c2c/34/38/48/4c/64/**68**/6c/70/74/78/d38/cc8 (68 = rebuild budget, 6c/70/34/38 = sweep slots,
  cc8 = psi overflow), base array 0x95da10/0x130, unit array 0x933278/52, type records 0x98ad88/52
  (+41 cost factor, +42 plan), faction records 0x92ae14+f*0x20bc (+0x2880 = `&DAT_0094d694`, +0x2e18 =
  0x94dc2c production total, **+0x2e20 = the 4 seed dwords**, 0x94d698 improved-temper, 0x94d744/748/74c
  improved addends, 0x94d67c nutrient support), **terrain array base = the VALUE at 0x92ae14 (live
  0x40a6ba8); record = base + (40*y + (x>>1))*0x2c; category = rec[0]&0xe0 (ocean iff < 0x60); +8 = u9,
  +0xc = uc**, category yield table 0x926bd8 (= alpha #RESOURCEINFO), spiral XOFF 0x67850c / YOFF
  0x678990, tech table 0x92fdd4 stride 0xb + availability bitmap 0x985c1c[fac], tail list 0x926cb4
  (28-byte entries to 0x926d78, count dword @0x926ca8 = -1 = "scan all"), scratch 0x94d684/dc20/dc24/
  **dc34**, map width 0x692184 = 40, 0x92a378/37c = 80, 0x92a394 = 0 (NO wrap), claims 0x985b3c[33],
  scenario flags 0x985ac4 (bit31 blocks projects > 38), special base idxs 0x985ba8/bac/bb0 (-1),
  0x985b48 = 4 and 0x985bc0 = 2 (4e7070 +1 tests), 0x92a2cc = 59 (tech id), 0x92a27c = 2, 0x92a2a4 = 5,
  0x91c628 = 0.
## Static-reading kit
- **Cached whole-`.text` disassembly: `evidence/m53j_text.txt.gz`** (790702 lines, objdump -d -M intel of
  `programs/terran.exe`). Locate a VA: `zgrep -n '  4ef7f6:' evidence/m53j_text.txt.gz`; sed ranges must
  anchor on REAL instruction boundaries. **VA->fn by bisecting `ghidra_out/index.csv` — COMMA-separated**
  (col 0 addr `0x004ddaa0`, col 1 name). **VA = file offset + 0x400000.**
- **POINTER-TYPE SCALES IN PSEUDOCODE — the trap:** Ghidra typed `DAT_008f0d60` copies `short *` in
  4ef6d0 renderings, so offsets there are HALF the byte offset (`psVar22 + 0x28` == machine +0x50;
  `* 0x98` == 0x130 stride); `int *` DATs scale x4. 4e92c0/4e93f0 renderings are UNSCALED. NEVER trust a
  pseudocode field offset: pin against machine disp or live pread. Same trap for `DAT_0092ae14`: the
  RENDERED base is the stored POINTER value, not the DAT address.
- Pseudocode `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite your own evidence-file line numbers);
  corpus `grep -rn <pat> ghidra_out/shard_*.c`; enclosing fn via `grep -n '^// ==== ' ghidra_out/shard_N.c`.
- **Alpha comment headers name the columns** (`alpha.txt` `:96 #TERRAIN`, `:132 #RESOURCEINFO`, `:238
  #TECHNOLOGY`, `:348 #CHASSIS`, `:387 #WEAPONS`, `:422 #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`,
  `:590 #FACILITIES`, `:687 #PLANS`, `:710 #RESOURCES`); `scripts/parse_alpha.py` -> `data/alpha.json`
  (list index = live project idx - 1; UNITS: type idx = json row - 1).
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800x600).
  Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
- **Turn driver:** `python3 scripts/smac_play.py --turns N [--timeout S]` (background OK). Stop a driver
  ONLY with `scripts/smac_play.py --mode stop` — never signal by name. After a run cur may sit on an AI
  faction — drive until cur_player == 3. **"Do you really want to quit?" pops mid-drive: Escape onto
  "Oops, no, wait!", NEVER click.** **PROPOSAL vote pane (stalls the AI phase, driver returns STUCK):
  bars in true window coords YEA (310,495) / NAY (398,495) / ABSTAIN (485,495), then one OK bar
  (393,495); the `YEA: 2  NAY: 3` line is the TALLY, not a key hint; capture with `xwd -root -silent` +
  ffmpeg 2x upscale + tesseract (window-id capture OCRs blank), click after `xdotool windowfocus`.**
- **Economy snapshot:** `python3 scripts/m53l_snap.py > evidence/x.tsv` — read-only `/proc/pid/mem` walk
  of all bases (header `# year cur nb era mask pid`; after f98 cols are bc c0 c4 c8 d0 cc f0); diff two
  snapshots by NAME. **Model:** `python3 scripts/m53o_recon.py [idx ...]` (`--legacy`, `-v`) — read-only,
  per-term per-field breakdown + MODEL/OBS/DELTA.
- **Watchpoints: x86 DR budget = 4 hw slots** (8-byte windows need 8-alignment = 2 DRs each); pair with
  the 10 Hz /proc-mem poller `scripts/m53m_poll.py`. Bake addresses as LITERALS, print `commands …
  continue end` per site, `stdbuf -o0`, `gdb -batch -nx -q -p PID -x scripts/x.gdb` backgrounded + drive
  + snapshot in ONE job (`scripts/m53n_drive.py` = proven template: entry-int3 caller census + mid-body
  stack-word return-address matching + cap/detach self-stop). **Watchpoints fire on VALUE CHANGE, not on
  stores — a same-value rewrite is INVISIBLE (that is how 4e3470's 19 "hits" undercounted its calls).**
  Pokes via /proc/pid/mem while idle (no tracer) + readback; unit slots shuffle — restore at the
  record's NEW home if the array compacted.
## Milestone options (pick ONE)
- **M53p — take the rebuild model to 76/76 (THE PICK).** Three residual classes from
  `evidence/m53o_recon_findings.md` §5: (a) **c4-only negative, 12 rows (-1..-5, facs 1,3,4,7, never
  2/5/6)** — a +1 branch inside `FUN_004e7070`; read its uc bit tests (0x4e711a-58, incl. `(uc>>24)<9`
  via `sar edi,0x18` @0x4e70b1), the `DAT_00985b48 == bidx` test (live 4), `1 < facrec[0x94d67c] +
  (base+0x30&4 ? 1:0)` @0x4e7215, the cap-2 spill to `DAT_008f0cc8`, and the LAB_004e7586 modifiers
  (+1 if +0x34&0x2000, -1 if &0x4000, -1 if DAT_00985db8, x3 if DAT_00985dc4 & (0x91c628?2:1)); base 70
  needs exactly +1 on its forced 8-tile set. (b) the **fac-2 c0 class** (28 rows, model high +2..+5) —
  first check whether the c0 multipliers (0x4e943f x2, 0x4e9525 x(esi+2)/2) are LIVE for some bases.
  (c) **visit-time ENTRY state** (pop, base+0x30 bit2, base+0x34, facility bitmap, input mask): the model
  is pure in entry state, so post-visit mutations surface as residuals (idx 3/23). **Done when** 76/76,
  or every remaining class has a named machine-addressed rule, plus a model re-run on a fresh round
  snapshot (`scripts/m53l_snap.py` before/after a driven turn).
- **Later:** unit+38 slot semantics + consumers of 0x8f0c74/78; who writes the seed dwords
  (faction+0x2e20); `base+0x84` nibble-array semantics and the flag==1 else-branch nibble blocks (0/76
  rows exercise that path); `DAT_008f0cc8` consumer; who sets +0xe0 between recomputes; byte@5 meaning;
  who first sets c0 at founding (4e47d0 never fired in a normal round); the mid-visit 3-point d0 trace
  (pre / at 0x4ef7f6 / post) to upgrade the income-extra verdict; the 417ee0 UI row-loop identity behind
  the 13x; M50c-e, M51b.
- **Retired premises, do not resurrect:** full chooser-era list lives in SESSION_NOTES sessions 55-67;
  the live set: **"bc/c0/cc are persistent accumulators whose only writers are 4e92c0/4e93f0"** (4e78e0
  REBUILDS the whole +0xbc..0xc8 vector first — idempotent when inputs are unchanged); **"4ef6d0 never
  runs"** / **"4ef6d0 re-runs the block twice per base"** (it runs once per visit at 0x4f5adc; only its
  two `0x68cbb4`-guarded block sites are dead); **"the round pipeline walks all bases in index order"**
  (grouped by owner faction in faction-turn order, ours LAST); **"bc/c0 gain per sweep fire"**; **"the
  Colony is fac 3"** (owner 2 at idx 23); **"4e40a0 tests the whole mask
  dword"** (LOW byte only); **"pseudocode offsets are byte
  offsets"** (short* x2, int* x4, loop ptr base+4; `DAT_0092ae14` renders the stored pointer); **"claim
  table is 0x985aa0[72]"** (33 @ 0x985b3c, idx-0x27); **"the PROPOSAL pane's
  `YEA: 2 NAY: 3` is a key hint"** (it is the tally); **NEW: "4e3470's 19 watch hits = calls"** (they are
  base SWITCHES); **"0x4f1e3f drains base+0x40"** (it clears the queue head [eax+0x50]); **"base+0x78
  entry mask = ~(pop|1)"** (it is `~(DAT_008f0d30|1)`, live 1); **"the tail loop 0x4e8b6f-0x4e8d48 feeds
  the production vector"** (it writes only base+0x48); **"c4/c8 have downstream writers"** (none);
  **"the m53o_findings asm line cites past 0x4e7c00 are exact"** (drift ~10 low — use 249/433/998/1108/
  1186/1273/1343).
