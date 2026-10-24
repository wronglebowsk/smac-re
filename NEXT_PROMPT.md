# NEXT_PROMPT — SMAC RE, session 74

Read IN FULL: footing (facts — do not re-derive), kit, options. Do ONE milestone, checkpoint to
`SESSION_NOTES.md` (+ rewrite this), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53r (**done, session 74**); open: **M53s (THE PICK)** +
"Later" list.

## First actions
1. Skill `smac-cvr-format`: `SKILL.md` ~19 KB (fine whole); depth in `references/` — open ONLY what the
   milestone needs: `production-rebuild.md` (UPDATED session 74: guards polarity, skip-flag formula,
   scan-0 acc-bit-0 gate, budget-at-visit-time), `code-atlas.md` (fields), `wine-operations.md`.
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 74 (M53r) is the latest milestone.
3. `git status`; `git branch` (never commit to main); then `python3 scripts/milestone.py start <ID>`.
4. Live state (re-verify `scripts/smac_state.py --json` first): pid 2124624 (`pgrep -x terran.exe`),
   turn_flags 0x10000, **idle**, TracerPid 0; last dump refresh: cur base idx 69 (fac 3), nb 75,
   nunit 333, mask 0xff08. The Colony = idx 23, owner 2 (relocate by owner byte / faction byte@14,
   NOT by name; unit slots SHUFFLE).
5. **THE MODEL READS A DUMP**: `scripts/m53p_recon_a.py` consumes `evidence/m53o_mem/*.bin`; run
   `python3 scripts/m53o_mem.py` FIRST and name the refresh in every report. `--stale-mask` =
   superseded entry path; `--no-pop-recover` = plain replay view (default runs the drift probe).

## Footing — rebuild model (M48d -> M53r; VERIFIED unless marked)

### M53r (74): the 11 fac-2 rows were POP-DRIFT BUDGET rows — census 76 sc / 65 exact — `evidence/m53r_findings.md`
- **Scan-order theory dead (VERIFIED):** the middle-pass selection was fully re-read from the asm and
  the model already matched every gate (loop j=1..20; strict `</>` pair dispatch; swap guards
  COMMIT-require best-add idx > 0 ∧ add score > swap score ∧ swap idx > 0 — pre-74 ref had guard-1
  polarity flipped; undo gate `bc < (pop+1)*K`; facility gate/score; continuation; exit `0x78 = acc` /
  `0x7c = budget` RAW). Derivations + asm cites: findings file.
- **Budget/skip-flag facts (VERIFIED):** `DAT_008f0c68` has exactly 4 stores in `.text`, all in 4e78e0
  (Ghidra shard_012.c:16023/16108/16229/16626 agree with machine 0x4e7904/0x4e7c36/0x4e7ecd/0x4e85d8);
  sole initializer = **pop+1 AT VISIT TIME** (`movsx BYTE[base+6]+1`; Ghidra `(char)DAT_008f0d60[3]` =
  short*-scaled byte@6). Skip flag = `1 iff NOT((1<<fac)&byte0(0x985b10)) ∨ (byte0(base+0x38)&0x40 ∧
  bit31)` (0x4e790a-33; live 0xff08 ⇒ flag 1 for all facs but 3). Scan-0 special runs iff scan ended
  `budget != c80+c7c` (0x4e7c5e `je 0x4e8a47` skips special+MP); its tile scan self-skips WITHOUT
  budget spend when acc bit 0 already set (A:368).
- **The finding:** the 11 non-sc fac-2 rows fired phantom swaps because dump pop byte@6 is POST-visit;
  stored carry == model budget_end **+1** on them (`evidence/m53r_sig.py`). `pop_visit = dump+1` ends
  the scan at `budget == c80+c7c` → special+MP skipped → reproduces mask AND carry AND vector at once
  on **22 rows (ALL fac 2**: the 11 + carry-only 28,31,47,48,49,56,63,65,67,68,71). INFERRED: those
  bases lost 1 pop after their rebuild visit (cause open; fac-2 idx 0/23 did NOT drift).
  `recover_pop()` probes pop+1, accepts only on mask+carry reproduction; header prints `pop-drift=+1`.
- **Census (fresh dump 2026-10-24, pid 2124624, `evidence/m53r_run1.txt`):** 76 rows, **76 sc / 65
  exact**, 11 c4-only residuals UNCHANGED (1,3,5,8,30,34,46,51,60,62,69 — facs {1,3,4,7}; model−obs
  −1..−5; cells bc 0 c0 0 c4 11 c8 0; saved c7c == budget_end ⇒ no drift).

### M53q (73): the scan pool is RECOMPUTED per base and the entry filter is a NO-OP — `evidence/m53q_findings.md`
- `build_table(idx) -> (table[25], mask21)` transcribes `FUN_004e63b0` (asm 298136-298619): per-step
  reason codes (2 off-map/unseen, 0 scannable, 4 terrain test `tile[8]&1 ∧ 0<=tile[2]&0xf<8`, |=8 unit
  order-3/foreign-stack test, |=0x20 foreign territory no-treaty, |=0x10 another base's processed step
  overlapping the spiral), mask = {bit i: table[i]!=0}; the `=1` site 0x4e63e8 is dead for 0..20.
  Computed table matches live `0x8f0ccc` 20/21 slots on cur base 69; the one disagreement is **bit 8**
  (tile (45,9) foreign-stack test: live 8, computed 0 — pre-move state, INFERRED). Predicate details
  (+50 walk anchor, |=8 gate polarity, `FUN_005ab130` head rules, hex-dist formula) are in the
  findings file + skill reference — do not re-derive. `evidence/m53q_probe.py` dumps 4e63b0's reads.
- **THE HEADLINE (VERIFIED 76/76):** `pool(=base+0x78) & fresh_mask == {bit 0}` for every base ⇒ entry
  filter `d78 &= (~d30|1)` is a no-op; the game filters with the per-base fresh mask (4e63b0 at
  0x4e78e9 precedes the filter at 0x4e796a); the stale global never filtered anything.

### M53o (67): the rebuilt vector IS the terrain-yield sum — `evidence/m53o_recon_findings.md`
- `base+0xbc` NUTRIENT, `+0xc0` MINERAL, `+0xc4` ENERGY, `+0xc8` PSI (seed-only). `FUN_004e75f0(field,
  fac,bidx,x,y)`: 0->`4e6960`, 1->`4e6d40`, 2->`4e7070`, 3->0 (clears `DAT_008f0cc8`). Per-tile category
  table = alpha `#RESOURCEINFO` verbatim, live **0x926bd8** (9x4, values in findings). **7 vector add
  sites** (`mov [edi+ecx*1-0x4],edx`): 0x4e7c15 scan, 0x4e7ea3 scan-0, 0x4e85bd
  mp-add, 0x4e8739 swap-out, 0x4e883b swap-in, 0x4e8951/0x4e8a32 dead undo pair (asm lines 249/433/998/
  1108/1186/1273/1343). Seed store 0x4e79a5 from `0x94dc34+(fac*0x82f+field)*4` = live 0 all factions.
  Downstream: bc += `DAT_008f0c6c` 0x4e9344, c0 += `DAT_008f0c70` 0x4e9459; **0xc4/0xc8 have NO
  downstream writers**.
Scan/budget/middle-pass rules: skill `references/production-rebuild.md`.
### Standing
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, **owner byte@4 =
  faction**, byte@5 usually == @4 (idx 0 differs, OPEN), pop byte@6 (POST-dump value — see M53r), +0x30
  flags (bit 0x8000 set by 4e78e0, exit clears **bit 17** via `and ch,0xfe`; bit 2 gates one energy
  test), +0x34 (0x2000/0x4000 tested by 4e7070), +0x38 = 0x00dfbe41, +0x3c progress, +0x40 minerals,
  +0x4c pending (cap 9), queue @0x50..0x74 (head clear 0xffffffda), **+0x78 scan/processed mask**,
  **+0x7c budget carry (= budget published at exit — re-measures the game's visit)**, +0x80 counter
  (zeroed at 4e78e0 entry), +0x84 16-nibble AI array, +0x8c..0x90 40-bit facility bitmap, +0x94 d0
  mirror, +0x98 minerals mirror (equal 75/75), **+0xbc/0xc0/0xc4/0xc8 the rebuilt vector**, +0xcc rate,
  +0xd0 net income, +0xe0 (per-turn zeroed), +0xec/+0xf0 upkeep, +0xac history, +0x48 display acc.
- **Unit record (array 0x933278 stride 52, count `0x985af0`):** x u16@0, y u16@2, type byte@4,
  **faction byte@14**, order byte@17, +24/+25 (u16 `w18`, byte `b25`: 0x440 transport-state test + the
  per-faction bit at 0x4e660c — semantics OPEN), +38 sweep slot, +46 u16 base index, **+48 u16 chain
  link** (walked by `FUN_005a6330`) and **+50 u16 chain link** (walked by `FUN_005ab130`) — both exit
  only on NEGATIVE, terminators -1 (201/332, 203/332), same stack in opposite orders (tile (45,9): +48
  106→147, +50 147→106). Type records 0x98ad88/52 (+41 cost factor, +42 plan, +37 read at 0x5a692a),
  faction records **0x94ae14 + fac*0x20bc** (0x92ae14 is the terrain POINTER, not the record base;
  +0x2880 = `&DAT_0094d694`, +0x2e18 production total, +0x2e20 the 4 seed dwords), terrain array base
  = the DWORD at 0x92ae14 (live 0x40a6ba8), record = base + (40*y + (x>>1))*0x2c, category = rec[0]&0xe0
  (ocean iff < 0x60), +4 = per-faction seen bits, +7 = owner byte, +8 = mask dword (bit 1 = unit-stack
  occupancy, bit 0 = the 4e63b0 terrain test), +0xc = list head/uc; relation bytes 0x94d448 +
  fac*0x20bc + 4*other (&3==0 = "no pact/treaty/truce"); tech table 0x92fdd4/0xb + availability bitmap
  0x985c1c[fac]; claims 0x985b3c[33].
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, nunit 0x985af0, mask 0x985b10 (0xff08 — its
  LOW byte drives the 4e78e0 skip flag ⇒ flag 1 for every fac but 3), era 0x985aec (2), era table
  0x68cbb8, **turn flags 0x985ae8 (0 idle, bit1 = end-turn in flight — 0x10002 = livelock
  signature)**, solo 0x920434 (**live 0**), cap 0x92a370 (10), cur base ptr 0x8f0d60, cur base INDEX
  0x68cbb0, marker 0x68cbb4, **per-visit block: 0x8f0ccc..0x8f0d1c table + 0x8f0d30 mask (rebuilt per
  base by 4e63b0; 2 stores to 0x8f0d30 in .text) + 0x8f0c4c (score denominators 0x4e821f-31, live 6,
  NOT visit-invariant) + 0x8f0c68 (rebuild budget, 4 stores total)**, economy slots 0x8f0c6c/70/34/38,
  cc8 = psi overflow, map width 0x692184 = 40, 0x92a378/37c = 80, 0x92a394 = 0 (x wraps), scenario
  constants 0x985b48 (live -2, only ref `cmp` 0x4e74e9), 0x985bc0 = 2, 0x92a27c = 2 (K), 0x92a2a4 = 5,
  0x92a2cc = 59, **0x91c628 NOT constant (0 → 1 observed)**, 0x985afc = 281.
## Static-reading kit
- **Look-up before grep:** `python3 scripts/index.py search "<question>"` — indexes evidence/*.md +
  skill/references/*.md + NAMED.md (3,465 chunks); returns file:line leads; cite the file, not the hit.
- **Cached whole-`.text` disassembly `evidence/m53j_text.txt.gz`** (objdump intel). Locate a VA:
  `zgrep -n '  4e78e9:' evidence/m53j_text.txt.gz`; windows `gunzip -c … | sed -n 'A,Bp'` (plain `sed`
  on .gz returns nothing). **VA = file offset + 0x400000.** VA→function: `awk -v A=0x005ab223 -F,
  'NR>1 && $1<=A {n=$2;p=$1} END{print p,n}' ghidra_out/index.csv` (COMMA separated; no braces inside
  python f-strings). FUN_004e78e0 window with A:NNN numbering: `evidence/m53o_fn4e78e0_asm.txt`.
- POINTER-TYPE SCALES — the trap: Ghidra types some DATs `short *` (offsets HALF) or `int *` (x4).
  Never trust a pseudocode field offset; pin against machine disp or live pread (`frec()` in
  m53p_recon_a.py takes ABSOLUTE addrs). x86 `test/je` fires when the tested bits ARE set; read the
  machine branch before believing pseudocode cmp/jle polarity (M53r tripped on guard-1).
- Pseudocode: `scripts/fn.py 0xADDR > evidence/<id>_fn.txt`; corpus `grep -rn <pat> ghidra_out/shard_*.c`;
  alpha headers name the columns (`alpha.txt` :132 #RESOURCEINFO, :560 #UNITS, :590 #FACILITIES, :710
  #RESOURCES); `scripts/parse_alpha.py` -> `data/alpha.json`.
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800x600).
  Preflight: no gdb, TracerPid 0, `ptrace_scope` 0. `xwd` needs **`-display :99`** (DISPLAY=:0 fails).
- **Turn driver:** `python3 scripts/smac_play.py --turns N --timeout S --no-escape S'` where
  **`--no-escape N` = "never press Escape during the first N seconds" — set N > the run timeout** (the
  driver classifies the "Do you really want to quit?" dialog as a title screen; clear it with
  `xdotool windowfocus <win>` + Escape, NEVER click). **This checkout has NO `--mode stop`** — bound a
  backgrounded driver with shell `timeout`; never `pkill -f`/`pgrep|kill` by name.
- **Stalled round? Run `python3 scripts/m53q_livelock.py`** (turn_flags + `+48`/`+50` chain census;
  `--fix` pokes the offending link to 0xFFFF). Signature: turn_flags bit 1 + hot main + static screen.
- **PROPOSAL pane** (stalls AI phase): TRUE window coords YEA (310,495) / NAY (398,495) / ABSTAIN
  (485,495), one OK (393,495); `YEA: 2 NAY: 3` = tally. Capture `xwd -display :99 -root -silent` +
  2x upscale + tesseract; click after `xdotool windowfocus`.
- **Snapshots:** `python3 scripts/m53l_snap.py > evidence/x.tsv` (read-only walk of all bases) and
  `python3 scripts/m53o_mem.py` (refreshes the dump the model reads). **Model:**
  `python3 scripts/m53p_recon_a.py $(seq 0 75)` — parse with `evidence/m53p_swap_parse.py` (`--sc`) or
  `evidence/m53p_fresh_parse.py`. Per-row probes: `evidence/m53q_maskcmp.py`, `m53q_nonsc.py`,
  `m53r_sig.py` (saved-carry vs replay-budget signature), live probe `m53q_probe.py`. `--no-pop-recover`
  = plain replay view; the default prints `pop-drift=+1(pop a->b)` on recovered rows.
- **Watchpoints: x86 DR budget = 4 hw slots** (8-byte windows need 8-alignment = 2 DRs each); pair with
  the 10 Hz `/proc/mem` poller `scripts/m53m_poll.py`. Bake addresses as LITERALS, `stdbuf -o0`,
  `gdb -batch -nx -q -p PID -x scripts/x.gdb` backgrounded + drive + snapshot in ONE job
  (`scripts/m53n_drive.py` = template). **Watchpoints fire on VALUE CHANGE, not on stores.**
## Milestone options (pick ONE)
- **M53s — the 11 c4-only residuals (THE PICK).** idx 1(f1),3(f4),5(f7),8(f1),30(f4),34(f4),46(f1),
  51(f1),60(f4),62(f1),69(f3): masks right, carries right (no pop drift), model ENERGY short −1..−5
  (model−obs). The per-tile `FUN_004e7070` reimplementation agrees on 0/76-base tiles *of the same
  dump state*, so suspect inputs that DRIFTED between visit and dump: 4e7070's neighbour loop reads
  unit-presence-dependent `rec+8 & 0x800000` + `rec+7 == owner` + `uc` bit patterns + `FUN_005831a0`;
  also `0x8f0c4c` (score denominators, NOT visit-invariant) feeds the mp divisors. Check whether the
  short tiles sit adjacent to units that moved after the base's visit (driven round, or the M53n
  watchpoint template on `0x8f0c68` + `+0xc4` on a fac-1/4 base). Done when the residuals are
  explained (rule or drift, honestly labelled) or a reproducible subset collapses.
- **Then (Later):** why pop-drift is fac-2-only (idx 0/23 didn't drift; a driven round catching
  `+0x7c` publication might settle it); the bit-8 live-table disagreement at tile (45,9);
  `c80_end != stored d80` on idx 24/35 (internal, unpublished); `unit+24/25` + `unit+38` semantics +
  consumers of 0x8f0c74/78; who writes the seed dwords (faction+0x2e20); `base+0x84` nibble semantics;
  `DAT_008f0cc8` consumer; who sets +0xe0; byte@5 meaning; `turn_flags` bit 16; the 417ee0 UI row-loop
  behind the 13x; M50c-e, M51b.
- **Retired premises, do not resurrect:** "bc/c0/cc are persistent accumulators written only by
  4e92c0/4e93f0"; "4ef6d0 never runs"/"re-runs the block twice"; "the round walks all bases in index
  order" (grouped by owner, ours LAST); "bc/c0 gain per sweep fire"; "the Colony is fac 3" (owner 2,
  idx 23); "4e40a0 tests the whole mask dword" (LOW byte only); "pseudocode offsets are byte offsets"
  (short* x2, int* x4 — `DAT_008f0d60[3]` = pop byte@6); "claim table 0x985aa0[72]" (33 @ 0x985b3c);
  "PROPOSAL pane `YEA: 2 NAY: 3` is a key hint"; "4e3470's 19 hits = calls"; "0x4f1e3f drains
  base+0x40"; "base+0x78 entry mask = ~(pop|1)"; "DAT_008f0d30 = 1 is a scenario constant"; "the
  freshness marker 0x68cbb4 is -1 while idle"; "the entry filter clears pool bits via the stale global
  d30" (pool∩fresh = {bit 0} on 76/76); "the +50 walk re-anchors to the stack head"; "the |=8 gate
  fires when the +25 faction bit is SET"; "FUN_005a5c00 is identity" (only when 0x920434 != 0); "the
  middle-pass corrections subtract pop+k2 then halve"; "the model reads live memory"; "0x91c628 = 0 is
  constant"; the session-68 "Class S / Class J" framing; **"the 11 fac-2 non-sc rows are a scan-ORDER
  problem"** (M53r: pop-drift budget rows); **"skip flag = tile out-of-mask"** (it is the faction-mask
  test, M53r); **"swap guard: best-add index > 0 exits uncommitted"** (it COMMITS only then); **"4e78e0
  exit clears bit 8 of +0x30"** (bit 17); **"pop byte@6 is the pop the visit used"** (dump value is
  post-visit — 22 rows drift +1); and the session-73 census 65 sc / 54 exact (today: 76 sc / 65 exact).
