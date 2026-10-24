# NEXT_PROMPT — SMAC RE, session 67

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive), the operational
kit, and the queued options. Do ONE milestone, checkpoint to `SESSION_NOTES.md` (+ rewrite this file), STOP.

Ledger: M48d, M50a-b, M51a, M52a-b, M53a-M53n (**M53n done, session 66**); open: **M53o (THE PICK)**,
then the "Later" list.

## First actions
1. `grep -n '^## \|^- \*\*' ~/.hermes/skills/smac-cvr-format/SKILL.md` then `sed -n 'A,Bp'` on the 1-2
   bullets/sections you need (pitfalls + the code area). **Do NOT `skill_view` the whole file** (55 KB,
   ~90 % irrelevant per milestone).
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — Session 66 (M53n) is the latest milestone.
3. `git status`; then `python3 scripts/milestone.py start <ID>` (never commit to main).
4. Live state: game up (`pgrep -x terran.exe` → 2124624), year 2381, cur_player 3, nb 76, era 2, mask
   0xff08, TracerPid 0, pid stable across sessions — **re-verify `scripts/smac_state.py --json` before
   any our-turn assumption.** Our base = idx 70 'Climactic Research' row **0x962d30** (= 0x95da10 +
   70·0x130) — the ONLY base with owner byte@4 == 3. The Colony = idx 23, owner 2 (names NOT unique
   across factions — re-locate by owner byte + name). Unit slots SHUFFLE (array compaction, sessions
   65/66): re-locate units by faction byte@14, never stale indices. Post-66 census: NO crawler-shaped
   unit remains.

## Footing — the turn economy pipeline (M48d → M53n, VERIFIED unless marked)

### M53n (session 66): the round call schedule — `evidence/m53n_findings.md` (all cites there)
- **`FUN_004f5a70(base_idx)` = once per base per round, ONE call site in `.text`** (`0x5206d3`,
  `FUN_00520540` turn machinery); 76/76 live VISIT hits = nb; visit order grouped by owner byte@4 into
  faction groups, ascending base index within a group (fac 4,5,6,7,1,2,3 this round), **our faction (3,
  idx 70) LAST, immediately before year++** (`evidence/m53n_schedule.tsv`, log:935).
- **The 5-call economy block** `[4e8d60, 4e78e0, 4e92c0, 4e93f0, 4eaa10]` is replicated verbatim at 12
  sites in 7 functions (3x 4f5a70 @4f5ac3/4f5b37/4f5c50, 2x 4ee410 @4ee6cf/4ee889, 2x 4ef6d0
  @4efeb0/4f2207, 2x 4f41f0 @4f44ad/4f4563, 1x each 4e47d0 @4e4de2, 4eb6b0 @4eb6cc, 4f34b0 @4f3f85).
  Live per round: pass1 76 + pass2 76 (both unconditional, every base) + 4f41f0-B 34 + 4f41f0-A 4 +
  4eb6b0 (UI recompute via 4ef6d0→4e5ae0→4f6030→4eb6b0) 55 + 4ee410-B 1 + pass3 1 = **247 block
  executions**; SWEEPIN == RATEIN == BCADD == 247 → **the bc-add 0x4e9331-0x4e934a is ungated**;
  4ef6d0 / 4f34b0 / 4e47d0 fired 0x. 11 distinct per-visit signatures (26 visits = pass1+pass2 only …
  one visit carried 13 extra 4eb6b0 recomputes).
- **`DAT_0068cbb4` = freshness marker (VERIFIED):** 4f5a70 stamps it = idx at entry (`fn4f5a70.txt`:21)
  and again before pass2 (:41); its pass3 AND both 4ef6d0 blocks are guarded `if (DAT_0068cbb4 != idx)`
  → 4ef6d0's nested recomputes are structurally unreachable inside a visit (0 hits live); pass3 fired
  exactly 1x (the visit whose nested UI chain moved the marker). 4f41f0/4ee410 stamp + run
  unconditionally but are gated by their own production/queue conditions (`fn4f41f0`:73-85, `fn4ee410`:82).
- **bc/c0 are REBUILT inside the block (VERIFIED live + machine):** `FUN_004e78e0` (block step 2) seeds
  `base+0xbc..0xc8` from `[eax*4+0x94dc34]` (store `0x4e79a5`; esi walks 0xbc..0xc8 per `mov esi,0xbc`
  /`cmp esi,0xc8`; eax = local(ebp-4) + 2095·ebx → ×4 = +0x20bc·ebx = faction-record stride; live bc→0)
  then adds per-item contributions in loop `0x4e7be3-0x4e7c28` (edi = 0xbc step 4 to 0xcc; args
  `(ebx, ?, 0, DAT_0068cbb0, byte[base+4])` → `FUN_004e75f0`; eax → `base[edi]` (store 0x4e7c15) +
  running total `[ebp-0x48]`; outer repeat counter `DAT_008f0c68` set 0x4e7904, dec 0x4e85d8; live bc
  0→11 in 8 stores) — **only then** does 4e92c0 add `DAT_008f0c6c` once (live 11→12 at 0x4e934a) and
  4e93f0 add `DAT_008f0c70` to c0. ⇒ a crawler adds +1 to the FINAL rebuilt value per VISIT, not per
  block execution (= M53m's "+1 bc per 10 sweep-fires"); "stable 75/75" = idempotent rebuild.
  Post-66 base70: bc 12 c0 7 c4 4 c8 0 d0 1 cc −2 minerals 16.

### M53m (session 65): crawler sweep — pointer `evidence/m53m_findings.md`
- c6c/c70/c34 sole feeders = Supply Crawler (plan(type+42)==10, ONLY plan-10 type = 5) ∧ order(unit+17)
  ==3 ∧ unit+14==base owner; accumulate 0x4e8f35 (c6c), 0x4e8e82 (branch B +1), upkeep 0x4e9009; every
  sweep zeroes c6c (0x4e8d74) / c34 (0x4e8d80). **Slots: c6c[0]→bc, c70→c0, c34[0]→ec, c38→f0; c6c
  slot = unit+38** (slots 2/3 0x8f0c74/78 consumers OPEN). Unit layout: x@0 y@2 type@10 hp@12 fac@14
  order@17 dest@20/28 bidx@46 slot@38.

### M53l (session 64): production inputs — `evidence/m53l_findings.md`
- **+0xcc (rate) sole writer 0x4e937b in `FUN_004e92c0`:** `bc += DAT_008f0c6c` (0x4e9344); `ec =
  pop(base+6) × DAT_0092a27c(=2, store 0x5784f2) + DAT_008f0c34`; `cc = bc − ec`; HQ bump 0x8f0c48 :=
  faction+0x2880, +2 if HQ bit (0x4e92f5-4e932a); progress clamp (cc<0 ∧ prog==0 → −1; cc≥0 ∧ prog<0 →
  0); faction total `&DAT_0094dc2c[f·0x20bc] += max(cc,0)` cap 99 iff DAT_008f0d64 == 1. Live Colony
  28 − 22 = 6 ✓ (22 = pop 11 × 2).
- **+0xc0 exactly 3 stores, all `FUN_004e93f0`:** 0x4e943f `×= 2` gated (0x985ba8 ≥ 0 ∧ same faction ∧
  head ∈ [−37,−34]); 0x4e9459 `+= DAT_008f0c70`; 0x4e9525 `×= (esi+2)/2` (esi = 421fe0(19/20/21/22,
  cur_idx, 0) count + 0x985bac/0x985bb0 same-faction flags, all −1 live → mult 1.0).
- **Mask 0x985b10 = TWO BYTES** (b10 = facs 0-7, b11 = 8-15; 4e40a0 tests LOW byte only 0x4e40b5);
  writers + in-mask/out-mask semantics: `evidence/m53l_findings.md`.

### M53k (63) / M53j (62) — pointers: `evidence/m53k_findings.md`, `evidence/m53j_findings.md`
(d0 sole writer 4e93f0 0x4e9557; per-turn +0x40 writers all in 4ef6d0 — income add 0x4ef7f6, unit spend
0x4efedd, project spend 0x4f0ca1-6, drain 0x4f1e3f; clamp B 0x4f0cc3-e9; ARM gate 0x4f0a3d; claims 33 @
0x985b3c idx = project−0x27; completion 0x4f0d83; THE POP = FUN_004ef5d0; +0x3c display-only 0x4ee8c7).

### Standing (do not re-derive)
- **Base record (REAL byte offsets, array 0x95da10 stride 0x130):** x u16@0, y u16@2, **owner byte@4 =
  faction**, byte@5 usually == byte@4 (idx 0 differs 2/6, OPEN), pop byte@6, +0x30 flags (bits 23/31
  completion path, bit 1 gates income add), +0x3c progress, +0x40 minerals, +0x44 active mirror, +0x4c
  pending (cap 9), queue @0x50..0x74, +0x8c..0x90 40-bit facility bitmap (`DAT_0095da9c`), +0x94 d0
  mirror, +0x98 minerals mirror (equal 75/75), **+0xbc/+0xc0/+0xc4/+0xc8 = the production vector that
  4e78e0 REBUILDS on every block execution (c4/c8 contents OPEN)**, +0xcc rate, +0xd0 net income,
  +0xe0 (zeroed per turn), +0xec upkeep (pop×2 + c34), +0xf0 upkeep sum, +0xfc; f38 = 0x00dfbe41.
  4ef6d0 loop ptr 0x95da14 = base+4.
- **4f5a70 body order (pseudocode `evidence/m53n_fn4f5a70.txt`):** 0x68cbb0 = 0x68cbb4 = idx,
  0x8f0c64 = 0, d60 = base, base+0x30 &= 0xdffffdff → block → 4ef6d0 → 4f26e0 → +0x4c/+0x22 copies →
  4ee410 (return 1 if nonzero) → if 0x985afc>1 4f2ea0 → **0x8f0c64 = 1** → block → 0x94dc20 += →
  0x8f0c64 = 2 → if 0x985afc>1 {4f4060, 4f41f0, 4f33f0, (0x985afc>5 ∨ solo ∨ !(0x985ab8&0x20)) 4f34b0}
  → if 0x68cbb4 != idx {block} → 4f4a50, 4f47f0, 4ebef0(0), founding-anim branch → 0x68cbb4 = −1 →
  0x8f0c64 = 0 → base+7/+4 counters decrement. (NOTE: 0x8f0c64, not d64-as-d60; it gates the faction
  total accumulate.)
- **Globals:** year 0x985b00, cur 0x985dcc, nb 0x985af4, unit count 0x985af0, mask 0x985b10 (0xff08),
  era 0x985aec (2; sole direct store 0x4ddcf1 chooser path), 0x985b30 (2), era table 0x68cbb8
  {13,12,11,10,8,7}, solo 0x920434, cap 0x92a370 (10), **cur base ptr 0x8f0d60 (live store sites:
  4f5a99 pass1, 4f5c41 pass3, 4e3490 UI-path, 4e4dd6, 4efea2/4f21f9)**, **cur base INDEX 0x68cbb0,
  freshness marker 0x68cbb4 (−1 while idle)**, 0x985afc (>1 gates UI passes, >5 gates 4f34b0),
  economy block 0x8f0c2c/34/38/48/4c/64/**68**/6c/70/74/
  78/d38 (6c/70/34/38 = sweep slots per M53m, 68 = 4e78e0 item counter), base array 0x95da10/0x130,
  unit array 0x933278/52, type records 0x98ad88/52 (+41 cost factor, +42 plan), faction records
  0x92ae14+f·0x20bc (+0x2880 = `&DAT_0094d694`, +0x2e18 = 0x94dc2c production total; terrain line
  `DAT_0092ae14 + tile·0x2c` = VALUE not address — verify),  scratch 0x94d684/dc20/dc24/**dc34** (4e78e0 seed table), map width 0x692184 = 40, 0x92a378/37c = 80,
  claims 0x985b3c[33], scenario flags 0x985ac4 (bit31 blocks projects > 38), special base idxs
  0x985ba8/bac/bb0 (−1).
## Static-reading kit
- **Cached whole-`.text` disassembly: `evidence/m53j_text.txt.gz`** (790702 lines, objdump -d -M intel
  of `programs/terran.exe`). Locate VA: `zgrep -n '  4ef7f6:' evidence/m53j_text.txt.gz`; windows via
  `zgrep -A0 -e '  4e7c1' -e '  4e7c2'` — sed range anchors must be REAL instruction boundaries.
  **VA→fn by bisecting `ghidra_out/index.csv` — COMMA-separated** (col 0 addr `0x004ddaa0`, col 1 name).
  **VA = file offset + 0x400000.**
- **POINTER-TYPE SCALES IN PSEUDOCODE — the trap:** Ghidra typed `DAT_008f0d60` copies `short *` in
  4ef6d0 renderings, so offsets there are HALF the byte offset (`psVar22 + 0x28` == machine +0x50;
  `* 0x98` == 0x130 stride); `int *` DATs scale ×4; 4ef6d0's loop pointer = base+4. But 4e92c0/4e93f0
  renderings are UNSCALED. NEVER trust a pseudocode field offset: pin against machine disp or live pread.
- Pseudocode `scripts/fn.py 0xADDR > evidence/<id>_fn.txt` (cite evidence-file line numbers); corpus
  `grep -rn <pat> ghidra_out/shard_*.c`; enclosing fn via `grep -n '^// ==== ' ghidra_out/shard_N.c`.
- **Alpha comment headers name the columns** (`alpha.txt` `:348 #CHASSIS`, `:387 #WEAPONS`, `:422
  #DEFENSES`, `:471 #ABILITIES`, `:560 #UNITS`, `:590 #FACILITIES`); `scripts/parse_alpha.py` →
  `data/alpha.json` (list index = live project idx − 1; UNITS: type idx = json row − 1).
## Operational kit
- pid via `pgrep -x terran.exe`; window via `scripts/smac_play.py find_window()` (10485761, 800×600).
  Preflight: no gdb, TracerPid 0, `ptrace_scope` 0.
- **Turn driver:** `python3 scripts/smac_play.py --turns N [--timeout S]` (background OK). Stop a driver
  ONLY with `scripts/smac_play.py --mode stop` — never signal by name. After a run cur may sit on an AI
  faction — drive until cur_player == 3. **"Do you really want to quit?" pops mid-drive: Escape onto
  "Oops, no, wait!", NEVER click.** **PROPOSAL vote pane (session 66, stalls the AI phase and makes the
  driver return STUCK): the pane's bottom bars in true window coords are YEA (310,495) / NAY (398,495)
  / ABSTAIN (485,495); after voting it collapses to one OK bar (393,495). The `YEA: 2  NAY: 3` line is
  the vote TALLY, not a key hint — keys 2/3 do nothing; capture with `xwd -root -silent` + ffmpeg
  2× upscale + tesseract (window-id capture OCRs blank), click with `xdotool windowfocus` first.**
- **Economy snapshot:** `python3 scripts/m53l_snap.py > evidence/x.tsv` — read-only `/proc/pid/mem` walk
  of all bases (header `# year cur nb era mask pid`; after f98 cols are bc c0 c4 c8 d0 cc f0); diff two
  snapshots by NAME. **Watchpoints: x86 DR budget = 4 hw slots** (8-byte windows need 8-alignment = 2
  DRs each); pair with the 10 Hz /proc-mem poller `scripts/m53m_poll.py` for base rows. Bake addresses
  as LITERALS, print `commands … continue end` per site, `stdbuf -o0`, `gdb -batch -nx -q -p PID -x
  scripts/x.gdb` backgrounded + drive + snapshot in ONE job (`scripts/m53n_drive.py` = proven template:
  entry-int3 caller census + mid-body stack-word return-address matching + cap/detach self-stop).
  **Watchpoints fire on VALUE CHANGE, not stores.** Pokes via /proc/pid/mem while idle (no tracer) +
  readback; unit slots shuffle — restore at the record's NEW home if the array compacted.
## Milestone options (pick ONE)
- **M53o — what the rebuilt production vector IS (THE PICK).** `FUN_004e78e0` seeds `base+0xbc..0xc8`
  from `[eax*4+0x94dc34]` (eax = local(ebp-4) + 2095·ebx → ×4 = +0x20bc·ebx) then adds
  `FUN_004e75f0(ebx, ?, 0, 0x68cbb0, byte[base+4])` per item into those 4 fields (loop 0x4e7be3-0x4e7c28,
  outer counter `DAT_008f0c68` set 0x4e7904 / dec 0x4e85d8). Pin: (a) what `ebx` indexes in the seed
  loop (faction? facility? — resolve by live pread of 0x94dc34 + 0x20bc·ebx vs base rows), (b) what an
  "item" is for 4e75f0 (read it: `scripts/fn.py 0x4e75f0`; its 4 pushed args), (c) the item count source
  0x8f0c68, (d) +0xc4/+0xc8 contents vs the alpha `#FACILITIES`/`#UNITS` columns, (e) why `4eb6b0` fires
  up to 13x on one visit (the 4ef6d0→4e5ae0→4f6030→4eb6b0 chain) and whether the M53l 3-base
  income-extra anomaly is that chain re-writing d0 after the income add. **Done when** bc/c0/c4/c8 are
  each explained as a named sum with machine addresses + a live per-base reconciliation (rebuild value
  == observed value for ≥3 bases of different factions).
- **Later:** unit+38 slot semantics + consumers of 0x8f0c74/78; `FUN_004e3470` (19 cur-base-pointer
  stores) trigger; 0x984d38 table writer/loader + the 0x2100000 string arena; tech table 0x92fdd4 layout;
  +0x30 bit 1 writer; who sets +0xe0 between recomputes; byte@5 meaning; who first sets c0 at founding
  (4e47d0 never fired in a normal round); M50c-e, M51b.
- **Retired premises, do not resurrect:** full chooser-era list lives in SESSION_NOTES sessions 55-66;
  the live set: **"bc/c0/cc are persistent accumulators whose only writers are 4e92c0/4e93f0"** (4e78e0
  SEEDS and ADDS the whole +0xbc..0xc8 vector first — rebuild, idempotent when inputs are unchanged);
  **"the round pipeline walks all bases in index order once per round"** (grouped by owner faction in
  faction-turn order, ours LAST before year++); **"4ef6d0 re-runs the block twice per base"** (its sites
  are `0x68cbb4 != idx`-guarded: 0 hits); **"chain adjacency decides whether c6c lands"** (adjacency is
  guaranteed inside the block; 247/247 adds reached); **"bc/c0 gain per sweep fire"** (see first item);
  **"the Colony is fac 3"** (owner byte@4 = 2 at idx 23); **"era table = pointer array"** (direct dwords
  {13,12,11,10,8,7} @ 0x68cbb8); **"4e40a0 tests the whole mask dword"** (LOW byte only); **"UN price 0
  = literal price"** (race-scan unpaid path INFERRED); **"byte@4 is type/cluster"** (it IS faction);
  **"snap column labels are trustworthy"**; "5a6e70's return is a cost index" (boolean); "aa0 =
  completion count" (base index); "claim table is 0x985aa0[72]" (33 @ 0x985b3c, idx−0x27); "the pay pool
  is base+0xcc + 0x3c" (real: +0xd0 + +0x40); "pseudocode offsets are byte offsets" (short* ×2, int* ×4,
  loop ptr base+4); "projects accumulate to completion" (gate is STOCK ≥ full price; +0x3c display);
  "clamp B applies to every payer" (mask-gated); "base70 row @ 0x962d50" (it is 0x962d30); "era DAT_00985aec has zero
  direct stores" (0x4ddcf1 — an `a3` grep miss); "c34 upkeep reachable from branch B" (0x4e8e89 `jmp
  0x4e9274`); "order pokes are inert for the economy sweep" (the sweep consumes them as inputs);
  **"the PROPOSAL pane's `YEA: 2 NAY: 3` is a key hint"** (it is the tally; click the bars).
