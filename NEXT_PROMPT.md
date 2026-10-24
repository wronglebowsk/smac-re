# NEXT_PROMPT — SMAC RE, session 70

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53q (**M53q done, session 73**); open: **M53r (THE PICK)**,
then the "Later" list.

## First actions
1. Skill `smac-cvr-format`: `SKILL.md` is now ~19 KB (fine to load whole) and the depth is split into
   `references/` — open ONLY what the milestone needs: `production-rebuild.md` (vector machine rules),
   `code-atlas.md` (fields/structs), `wine-operations.md` (driving/dialogs). Grep the section first.
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 73 (M53q) is the latest milestone.
3. `git status`; `git branch` (never commit to main); then `python3 scripts/milestone.py start <ID>`.
4. Live state (re-verify `scripts/smac_state.py --json` before any our-turn assumption): pid 2124624
   (`pgrep -x terran.exe`), **cur base idx 69 (fac 3, ptr 0x962c00), nb 75, nunit 333, mask 0xff08,
   turn_flags 0x10000, TracerPid 0, idle**. The Colony = idx 23, owner 2 (names NOT unique — relocate by
   owner byte; unit slots SHUFFLE — relocate by faction byte@14).
5. **THE MODEL READS A DUMP, NOT LIVE MEMORY**: `scripts/m53p_recon_a.py` consumes
   `evidence/m53o_mem/*.bin`; run `python3 scripts/m53o_mem.py` FIRST and name the refresh in every
   report. The dump now carries the FULL unit array (blob 0x4600) + `nunit` (0x985af0) — M53q added
   them. `--stale-mask` on the model = the superseded global-d30 entry path.

## Footing — the rebuild model (M48d -> M53q, VERIFIED unless marked)

### M53q (73): the scan pool is RECOMPUTED per base and the entry filter is a NO-OP — `evidence/m53q_findings.md`
- `scripts/m53p_recon_a.py::build_table(idx) -> (table[25], mask21)` implements `FUN_004e63b0` (asm
  298136-298619): per-step reason codes (2 = off-map/unseen, 0 = scannable, 4 = terrain test
  `tile[8]&1 ∧ 0<=tile[2]&0xf<8`, |=8 = unit order-3 or the foreign-stack test, |=0x20 = foreign
  territory no-treaty, |=0x10 = another base's processed step overlapping the spiral), mask =
  {bit i: table[i]!=0}. The `=1` site 0x4e63e8 is dead for 0..20 (guard `cmp ecx,0x54`).
- **Ground truth:** on the live cur base 69 the computed table matches live `0x8f0ccc` on 20/21 slots;
  the mask rule is VERIFIED (computed-from-live == live `DAT_008f0d30` = 0x101; 0x8f0d30 has exactly 2
  stores in .text, 0x4e6929/0x4e694f, both inside 4e63b0). **The one disagreement is bit 8** (step 8,
  tile (45,9), foreign-stack test): live 8, computed 0 — the (45,9) transit stack (units 106,110,137,
  138,144,146,147; fac 2; order 0; `w18=0xffff`; `b25=0xff`) passes the |=8 test only in a pre-move
  state (INFERRED). `evidence/m53q_probe.py` dumps everything 4e63b0 reads, live.
- **Predicate rules (VERIFIED by re-reading branch bodies):** the +50 stack walk at 0x4e663c starts
  from the **+48 terminus** (esi carries over, asm 298346-52); the |=8 gate fires iff foreign ∧
  ¬(w18&0x440==0x440) ∧ **+25-bit-CLEAR** (x86 `test/je` fires when the bit IS set, 0x4e6612) ∧
  stance&3==0; `FUN_005a5c00` is identity only when `0x920434 != 0` (live 0 → full body: rescan same-tile
  units, return the +50 head); `FUN_005ab130(x,y)` = tile record `+8` bit 1 → the record's list head,
  else linear scan `+0==x ∧ +2==y` then +50-walk to head; hex dist = `mx − ((manhattan>>1 − mn + 1)>>1)`
  over wrapped deltas (`FUN_0064b870` = abs, NAMED.md:218).
- **THE HEADLINE (VERIFIED 76/76):** `pool(=base+0x78) & fresh_mask == {bit 0}` for every base ⇒ the
  entry filter `d78 &= (~d30|1)` is a no-op in practice; the fresh mask differs from the stale global on
  76/76 rows yet the two census paths are byte-identical. Stored processed KEEPS bit 8 where the fresh
  mask allows it ⇒ the game filters with the per-base fresh mask (4e63b0 at 0x4e78e9 runs BEFORE the
  filter at 0x4e796a). "Stale-global contamination" (M53p) is superseded: the filter never bit.
- **Census on the 2026-10-24 dump (`evidence/m53q_dump4.txt`, pid 2124624):** 76 rows, **65
  self-consistent, 54 exact, 11 residual**; cells bc 11 c0 9 c4 21 c8 0. Residuals all c4-only: idx
  1(f1) 3(f4) 5(f7) 8(f1) 30(f4) 34(f4) 46(f1) 51(f1) 60(f4) 62(f1) 69(f3) — faction set {1,3,4,7}.
  Session 68's idx-31 "fac2 bc −1" residual COLLAPSED to exact. The 11 non-self-consistent rows are ALL
  fac 2 (37,40,42,44,52,55,58,61,64,70,72): same-cardinality step-SET mismatches — idx 44 pool 0x1d,
  model processed 0x1b (drops step 4), stored 0x1d (game kept step 4, dropped step 2).

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
  @0x50..0x74 (head clear 0xffffffda), **+0x78 scan/processed mask (= the scan pool; the entry filter
  against the per-base fresh mask is a no-op in practice — M53q)**, +0x7c budget carry, +0x80 counter
  (0 at entry), +0x84 16-nibble AI array (written by 4e78e0), +0x8c..0x90 40-bit facility bitmap, +0x94
  d0 mirror, +0x98 minerals mirror (equal 75/75), **+0xbc/0xc0/0xc4/0xc8 the rebuilt vector**, +0xcc
  rate, +0xd0 net income, +0xe0 (zeroed per turn), +0xec upkeep (pop*2 + c34), +0xf0 upkeep sum,
  +0xac history, +0x48 display accumulator.
- **Unit record (array 0x933278 stride 52, count `0x985af0`):** x u16@0, y u16@2, type byte@4,
  **faction byte@14**, order byte@17, +24/+25 (u16 `w18`, byte `b25`: the 0x440 transport-state test +
  the per-faction bit at 0x4e660c — semantics OPEN), +38 sweep slot, +46 u16 base index, **+48 u16
  chain link (walked by `FUN_005a6330` loop 0x5a6945-55, exits only on NEGATIVE)**, **+50 u16 chain
  link (walked by `FUN_005ab130` loop 0x5ab223-37, same sentinel)** — terminators -1 (201/332, 203/332);
  the two links are the same stack in opposite orders (tile (45,9): +48 106→147, +50 147→106, M53q).
  Type records 0x98ad88/52 (+41 cost factor, +42 plan, +37 read at 0x5a692a), faction records **0x94ae14
  + fac*0x20bc** (0x92ae14 is the terrain POINTER, not the record base; +0x2880 = `&DAT_0094d694`,
  +0x2e18 production total, +0x2e20 the 4 seed dwords), terrain array base = the DWORD at 0x92ae14
  (live 0x40a6ba8), record = base + (40*y + (x>>1))*0x2c, category = rec[0]&0xe0 (ocean iff < 0x60),
  +4 = per-faction seen bits, +7 = owner byte, +8 = mask dword (bit 1 = unit-stack occupancy, bit 0 =
  the 4e63b0 terrain test), +0xc = list head/uc; relation bytes 0x94d448 + fac*0x20bc + 4*other (&3==0
  = "no pact/treaty/truce"); tech table 0x92fdd4/0xb + availability bitmap 0x985c1c[fac]; claims
  0x985b3c[33].
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, unit count 0x985af0, mask 0x985b10 (0xff08),
  era 0x985aec (2), era table 0x68cbb8, **turn flags 0x985ae8 (0 idle, bit1 = end-turn in flight —
  0x10002 was the livelock signature)**, solo 0x920434 (**live 0** — `FUN_005a5c00` runs its full body),
  cap 0x92a370 (10), cur base ptr 0x8f0d60, cur base INDEX 0x68cbb0, marker 0x68cbb4, **per-visit block:
  0x8f0ccc..0x8f0d1c table + 0x8f0d30 mask (both rebuilt per base by 4e63b0; only 2 stores to 0x8f0d30
  in .text) + 0x8f0c4c (score denominators 0x4e821f-31, live 6) + 0x8f0c68 (rebuild budget, live 0)**,
  economy slots 0x8f0c6c/70/34/38, cc8 = psi overflow, map width 0x692184 = 40, 0x92a378/37c = 80,
  0x92a394 = 0 (x wraps), scenario constants 0x985b48 (live -2, only ref `cmp` 0x4e74e9), 0x985bc0 = 2,
  0x92a27c = 2 (K), 0x92a2a4 = 5, 0x92a2cc = 59, **0x91c628 is NOT constant (0 → 1 observed)**.
## Static-reading kit
- **Look-up before grep:** `python3 scripts/index.py search "<question>"` — indexes `evidence/*.md`, `skill/references/*.md` and `NAMED.md` (3,465 chunks); returns file:line leads, cite the file, not the hit.
- **Cached whole-`.text` disassembly `evidence/m53j_text.txt.gz`** (790702 lines, objdump intel).
  Locate a VA: `zgrep -n '  4e78e9:' evidence/m53j_text.txt.gz`; windows: `gunzip -c … | sed -n 'A,Bp'`
  (plain `sed` on the .gz returns nothing). **VA = file offset + 0x400000.** VA→function:
  `awk -v A=0x005ab223 -F, 'NR>1 && $1<=A {n=$2;p=$1} END{print p,n}' ghidra_out/index.csv` (COMMA
  separated; NOTE awk braces break inside python f-strings).
- POINTER-TYPE SCALES — the trap: Ghidra types some DATs `short *` (offsets HALF) or `int *` (x4).
  Never trust a pseudocode field offset; pin against machine disp or live pread. `frec()` in
  m53p_recon_a.py takes ABSOLUTE addrs (M53q tripped on this). x86 `test/je` polarity: `je` fires when
  the tested bits ARE set (M53q tripped on this at 0x4e6612).
- Pseudocode: `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite your own file's line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c`; alpha headers name the columns (`alpha.txt` :132 #RESOURCEINFO,
  :560 #UNITS, :590 #FACILITIES, :710 #RESOURCES); `scripts/parse_alpha.py` -> `data/alpha.json`.
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800x600).
  Preflight: no gdb, TracerPid 0, `ptrace_scope` 0. `xwd` needs **`-display :99`** (DISPLAY=:0 fails).
- **Turn driver:** `python3 scripts/smac_play.py --turns N --timeout S --no-escape S'` where
  **`--no-escape N` = "never press Escape during the first N seconds" — set N > the run timeout** (the
  driver classifies the "Do you really want to quit?" dialog as a title screen; clear it with
  `xdotool windowfocus <win>` + Escape, NEVER click). **This checkout has NO `--mode stop`** — bound a
  backgrounded driver with `timeout <run>` from the shell; never `pkill -f`/`pgrep|kill` by name.
- **Stalled round? Run `python3 scripts/m53q_livelock.py`** — prints `turn_flags` + a `+48`/`+50` chain
  census (terminators / self-links / out-of-range / cycles), exits 2 on a cycle; `--fix` pokes the
  offending link to 0xFFFF and re-censuses. Signature: turn_flags bit 1 + hot main thread + static screen.
- **PROPOSAL vote pane** (stalls the AI phase): bars in TRUE window coords YEA (310,495) / NAY (398,
  495) / ABSTAIN (485,495), then one OK bar (393,495); the `YEA: 2 NAY: 3` line is the TALLY. Capture
  `xwd -display :99 -root -silent` + ffmpeg 2x upscale + tesseract; click after `xdotool windowfocus`.
- **Snapshots:** `python3 scripts/m53l_snap.py > evidence/x.tsv` (read-only walk of all bases) and
  `python3 scripts/m53o_mem.py` (refreshes the dump the model reads; now includes the full unit array).
  **Model:** `python3 scripts/m53p_recon_a.py $(seq 0 75)` — parse with `evidence/m53p_swap_parse.py`
  (`--sc` = self-consistent rows + residuals) or `evidence/m53p_fresh_parse.py`. Per-row mask/scan-order
  probes: `evidence/m53q_maskcmp.py`, `evidence/m53q_nonsc.py`, live probe `evidence/m53q_probe.py`.
- **Watchpoints: x86 DR budget = 4 hw slots** (8-byte windows need 8-alignment = 2 DRs each); pair with
  the 10 Hz `/proc/mem` poller `scripts/m53m_poll.py`. Bake addresses as LITERALS, `stdbuf -o0`,
  `gdb -batch -nx -q -p PID -x scripts/x.gdb` backgrounded + drive + snapshot in ONE job
  (`scripts/m53n_drive.py` = proven template). **Watchpoints fire on VALUE CHANGE, not on stores.**
## Milestone options (pick ONE)
- **M53r — the fac-2 scan-ORDER rule (THE PICK).** 11 rows (37,40,42,44,52,55,58,61,64,70,72 — ALL fac
  2) are self-inconsistent with budget-correct but position-wrong processed masks (idx 44: model drops
  step 4, game kept it and dropped step 2). Find the game's scan iteration order / which step survives
  budget exhaustion (`evidence/m53q_nonsc.py` lists the bit-set diffs; the scan loop itself is in
  `references/production-rebuild.md`). Fix in `scripts/m53p_recon_a.py::scan_pass` (and the middle-pass
  candidate loop if the order feeds it). Done when those 11 rows are self-consistent on a fresh dump.
- **Then:** the 11 c4-only residuals (idx 1,3,5,8,30,34,46,51,60,62,69 — pools right, energy wrong);
  the bit-8 live-table disagreement at tile (45,9) (a driven round may catch the pre-move state);
  `unit+24/25` + `unit+38` semantics + consumers of 0x8f0c74/78; who writes the seed dwords
  (faction+0x2e20); `base+0x84` nibble semantics; `DAT_008f0cc8` consumer; who sets +0xe0; byte@5
  meaning; `turn_flags` bit 16; the 417ee0 UI row-loop behind the 13x; M50c-e, M51b.
- **Retired premises, do not resurrect:** "bc/c0/cc are persistent accumulators whose only writers are
  4e92c0/4e93f0" (4e78e0 REBUILDS the vector); "4ef6d0 never runs" / "re-runs the block twice"; "the
  round walks all bases in index order" (grouped by owner, ours LAST); "bc/c0 gain per sweep fire";
  "the Colony is fac 3" (owner 2, idx 23); "4e40a0 tests the whole mask dword" (LOW byte only);
  "pseudocode offsets are byte offsets" (short* x2, int* x4); "claim table 0x985aa0[72]" (33 @
  0x985b3c); "the PROPOSAL pane's `YEA: 2 NAY: 3` is a key hint"; "4e3470's 19 hits = calls";
  "0x4f1e3f drains base+0x40" (it clears the queue head); **"base+0x78 entry mask = ~(pop|1)"**;
  **"DAT_008f0d30 = 1 is a scenario constant"** and **"the freshness marker 0x68cbb4 is -1 while
  idle"**; **"the entry filter clears pool bits via the stale global d30"** (M53q: pool∩fresh = {bit 0}
  on 76/76 — the filter is a no-op; the game filters with the per-base fresh mask); **"the +50 walk
  re-anchors to the stack head"** (esi carries over from the +48 walk, 0x4e663c); **"the |=8 gate fires
  when the +25 faction bit is SET"** (je skips when set); **"FUN_005a5c00 is identity"** (only when
  0x920434 != 0; live 0); "the middle-pass corrections subtract pop+k2 then halve" (cdq kills that
  edx); "the model reads live memory" (it reads `evidence/m53o_mem/*.bin`); "0x91c628 = 0 is constant";
  the session-68 "Class S / Class J" framing; and the session-72 caveat that the 2383 census was
  46/7 — today's dump measures 65 sc / 54 exact / 11 residual.
