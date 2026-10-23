# NEXT_PROMPT — SMAC RE, session 54

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive),
the operational kit, and the queued milestone options. Do ONE milestone, checkpoint to
`SESSION_NOTES.md` (+ rewrite this file), then STOP.

## First actions
1. `skill_view('smac-cvr-format')` — harness pitfalls + code atlas.
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — M53a (session 53) is the latest milestone.
3. Check live state (kit below): game up (`pgrep -x terran.exe`), year ≥ 2366, our turn open (cur=3),
   TracerPid 0, no gdb attached, `kernel.yama.ptrace_scope` = 0.

## Footing — base economy (M48d → M53a, VERIFIED unless marked)

### M53a (session 53): the queue record decoded end to end
- **`base+0x50..0x73` is a 10-slot dword ITEM ARRAY** (head = +0x50, slot i = +0x50+4i; +0x68 = slot
  6, live 0 = never written). `+0x4c` = **last used index** (UI caps at 9: `case 3: <9 → +1` and `= 9`
  in `FUN_00417ee0`, ghidra_out/shard_001.c:9432-9437; the FUN_004f4060 drain iterates `[+0x4c]+1`
  dwords from +0x50 decrementing per-player item counts at `0x94de84 + owner·0x20bc + id`,
  shard_012.c:23044-23060). `+0x44` = **active-item mirror**: `0x4f5a70` copies `+0x50 → +0x44` every
  visit (shard_012.c:24185) and `[base+0x98] := storage` (shard_012.c:24184); the ownership-transfer
  block in FUN_004f4060 clears BOTH +0x44 and +0x50 to −38 (shard_012.c:23065-23068). Live:
  f44 == f50 == 2 at every QPIPE (evidence/m53a_watch.log:392, :769, :1115).
- **Encoding** (evidence/m53a_qgate_disasm.txt:5-55 = 0x4ef88b-0x4ef938): `−38` = empty → NOQUEUE
  0x4ef9b3; `≥ 0` = item id (unit `< 0x40`, facility `≥ 0x40`); `< 0` = `|q|` with scratch
  `[ebp-0x1c] = |q|−39` if `|q| ≥ 39` else −1, `[ebp-0x20] = [|q| ≥ 34]`; negative cost =
  `0x4e40a0(owner,1,−1) × dword[0x984d44 + 48·|q|]` (M46 upkeep table). On the POSITIVE path
  0x4efae5 overwrites `[ebp-0x1c] := 52·id` (m1c=104 = 52·2 live, :397); `[ebp-0x2c] = 1<<owner`
  unconditionally at 0x4ef815 (m2c=8 = 1<<3 live).
- **Negative values = secret projects** (registry VERIFIED static, project identity INFERRED):
  0x4f0d83 writes `0x985b3c[|q|−39] := base index` (fn_disasm.txt:1480); table = 33 dwords
  (`FUN_005305f0(&DAT_00985b3c, 0x84, …)`, shard_013.c:15670) = 33 secret projects; 0x51f730 reads
  registry[project] → owner(base[...]) (shard_013.c:11119-11120); 0x4f0819+ formats the builder base
  NAME from it. So `|q| = 39 + project_idx`. 0 NEGPATH hits again in m53a — semantics unprobed live.
- **Unit/facility completion is PAYMENT-DRIVEN — there is NO build-progress counter.** COMPLET
  0x4efe41 fires the instant `storage ≥ factor × 0x5ac950(id,idx,0)` (gate `cmp [ecx+0x40],edi; jge`
  0x4efa5e, queue_disasm.txt:39-40): QCOMPLET 1 hit in 3 rounds, only the st=200 round (:397; :769,
  :1115 st=0 → 0 hits). PROGDIV 0x4efd49 is the ETA STRING `(factor×(pop+1) − [base+0x3c]) /
  [base+0xcc]` clamped 0..10007, gated `[base+0xcc] > 0` (ours −3 ⇒ silent in solo — the M48d
  "never fires" mystery), NOT an accumulator (queue_disasm.txt:193-207). PREDICTED: a payable head
  re-completes EVERY round (matches M45 units 1→6); unprobed.
- **COMPLET dispatch** (queue_disasm.txt:250-291): unit (`ebx<0x40`) → `[ebp-0x20]:=0` → SPENDA;
  facility (`ebx≥0x40`) → set bit 2 of word `[0x98adb8 + 52·id]` (built flag), newly-set ⇒ repoint
  0x8f0d60 + rebuild chain 0x4e8d60/0x4e78e0/0x4e92c0/0x4e93f0/0x4eaa10; class-8 Colony Pod ∧ pop==1
  ∧ `0x94d438[p]>1` → ABANDONBASE confirm via `0x48ee00`, answer ≥2 → COMPLET (queue_disasm.txt:215-
  226, pseudocode:204-245). Downstream of CLAMP: `[+0x98]:=[+0x40]` → spawn helper `0x5ab650`
  (returns unit idx, flags in `0x93327c + idx·52`, pseudocode:307-320, INFERRED creation) →
  PRODUCE/PRODUCEPROTO pane w/ unit icon (pseudocode:440-530).
- **IADD gate CLOSED**: `storage += d0` iff `d0 ≥ 0 ∧ queue ≠ −38 ∧ (f30 & 2) == 0`
  (fn_disasm.txt:65-69 + pseudocode:110-113) — M48d's "2 hits in 3 rounds" = queue non-emptiness.
- **cc/d0 recompute PER-VISIT**: pokes (+0xcc=1, +0xd0=200) were already dead at the FIRST pipeline
  print (:392) — 0x4f5a70 runs the recompute chain before calling the pipeline.
- **Open**: dequeue/shift after a POSITIVE completion — the pipeline has NO +0x50 writer (reads only:
  fn_disasm.txt:67,118,200,223,1316); tail clear is negative-only (pseudocode:1476-1478:
  `queue == −|q| ∧ [base+0x4c]==0 → +0x50 := −38`); full-clear writers 0x507ef0 (shard_012.c:34739)
  / 0x5437d0 (shard_013.c:30426); enqueue-side 0x417ee0 writes raw commands incl. `< −38` project
  ids → 0x446250 (shard_001.c:9452). `base+0xc0` = constant 7 == our pop every round — unresolved.

### M52b (session 52): the SPENDA subtrahend is a COST (condensed)
- `edi` at SPENDA `0x4efedb sub esi,edi` = `0x4e40a0(owner,1,−1) × 0x5ac950(queue_id, idx, 0)` = 10 × 1
  = 10 for our queued Scout Patrol (m52b_watch.log:386-400). `0x4f5a70`'s edi := the base's OWNER BYTE
  (0x4f5aa9 loads `[ecx+4]`); M49a's "sweep-entry index" is dead. `0x4e40a0` arg2==1 → government
  switch 0x4e4318 (index `faction[p].int[20]+7`): ours = ×1 case; cases 0-4 = ×1.3. `0x5ac950` returns
  the **type-record +41 byte** (`0x98ad88 + type·52`, clamped [1,999] only for class 8); `type ≥ 0x40`
  = facility case. `0x4eaa10` preserves edi (push 0x4eaa41/pop 0x4eb672).
- Scout Patrol: class 3, +41=1, +43=10; alpha `#UNITS` Cost field "0 = Autocalculate". INFERRED: +41
  is a production weight, not the mineral cost itself → **M53b open**.

### M52a (session 51): base+0x3c arithmetic CLOSED (condensed)
- `0x4ee410` owns only +0x3c/+0x6/+0x7 stores; threshold `ebx = 0x4e40a0(owner,0,idx) × (pop+1)` = 80
  at 0x4ee5aa; reset store 0x4ee82f writes HALF the threshold (40); accrual 0x4ee8c7 `+0x3c += [+0xcc]`.
  Live re-confirmed in m53a: poked 500 → reset 40 → 37 → 34 (−3/round, m53a_watch.log:392, :769, :1115).
- +0x40 writers = SPENDA 0x4efee0 + CLAMP1 0x4eff23 only (hw watchpoint net); clamp =
  `storage := max(0, min(base+0xd0, cap 0x92a370=10))` with event-owner gate 0x4eff02.

### Standing from earlier sessions (do not re-derive)
- Storage writers: IADD 0x4ef7f6 (gated — see M53a), SPENDA 0x4efee0, CLAMP1 0x4eff20/23, CONVST
  0x4f2d7d (in 0x4f26e0, `storage += ((pool/esi)·45)/trait`; our base ALWAYS early-returns at
  0x4f2705/0x4f271e). `0x4f26e0` = mineral↔energy conversion/income, scales with faction energy pool
  `0x94d650+p·0x20bc`.
- **The sweep never truncates** (M50b): `0x520540` reloads n_bases per iteration; year store 0x51f554
  fires BETWEEN passes. Locate records by NAME ("Climactic Research") — the array SLIDES (idx 70 in
  m53a, 71 in m50c) and owner bytes change.
- Base record fields: x u16@0, y u16@2, owner@4, pop@6, f18, f1c, f20, f28, f30, **+0x3c progress**,
  minerals@0x40, 44 (queue mirror), 4c (queue last-index), **queue array @0x50..0x73**, 68 (slot 6),
  8a/8c (facility bitmap), 98 (storage snapshot), **c0 (=7, == pop this run; unresolved)**,
  cc@0xcc (progress delta, −3 for us, recomputed per-visit), d0@0xd0 (net mineral income, recomputed),
  e0, f0, fc@0xfc (+3 energy for us), f38 const 0x00dfbe41.
- Unit/facility type record `0x98ad88 + type·52`: name +0[34], +0x29 (41) production weight, +0x2a (42)
  class, +0x2b (43) cost-ish, +0x30 word (facility built-flag lives here), ability +32 (`0x98ada8`),
  domain +36 (`0x98adac`). Live: 0 Colony Pod (cls 8, +41 3, +43 40), 1 Formers (cls 9, 2/41),
  2 Scout Patrol (cls 3, **1/10**), 3 Transport Foil (cls 7, 3/39).
- Item upkeep table `0x984d44/0x984d48 + item·48` (M46); per-player item counts `0x94de84 +
  player·0x20bc + item`; project builder registry `0x985b3c + 4·(0..32)` (33 secret projects).
- Income globals (M46): gross 0x745734, upkeep 0x744f28, net 0x7457dc, trade 0x7457d4, food 0x74572c,
  needpct 0x745730. Verified: year 0x985b00, turn 0x985afc, cur 0x985dcc, nb 0x985af4, mask 0x985b10
  (0xff08), solo 0x920434, cap 0x92a370 (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base
  array 0x95da10 stride 0x130, unit array 0x933278 stride 52, trait record 0x927a7c+p·0x59c, faction
  records 2095 ints (stride 0x20bc), int[17] @0x94d694, int[20] @0x94d6a0, DAT_0092a290 = 10,
  DAT_0092ada8 = 2, DAT_0092a2ac = 7, DAT_0092a2b0 = 14, DAT_0092a27c = 2, DAT_00985b9c = −1.
- Ghidra types `DAT_008f0d60` as `short *`: pseudocode `+0x20` = bytes 0x40, `+0x22` = 0x44, `+0x26` =
  0x4c, `+0x28` = 0x50, `+0x1e` = 0x3c, `+0x66` = 0xcc, `+0x4c` = 0x98 — ALWAYS double offsets there.
- Pane id-printer bp 0x483470: advisories only.

## Static-reading kit
- **Clean 32-bit disassembly, no attach**: `gdb -batch -nx -q -ex "set architecture i386" -ex "set
  disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` (PE maps as file target;
  TracerPid stays 0; output line 1 is an arch banner — line N = insn N−1). Redirect to `evidence/` and
  grep it — never paste a whole function. Whole-FUN dumps exist: `evidence/m53a_fn_disasm.txt` =
  FUN_004ef6d0 (0x4ef6d0, 12298 B). Sizes: `grep -m1 004ef6d0 ghidra_out/index.csv`. Ghidra
  pseudocode: `scripts/fn.py 0xADDR` (m53a copy: evidence/m53a_fn4ef6d0_pseudocode.txt). objdump
  misaligns on SEH blocks. Corpus grep: `grep -rn <pat> ghidra_out/shard_*.c` then find the owning
  function with `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`.
- Live `/proc/PID/mem` pread (TracerPid 0) beats guessing: read `0x8f0d60`, walk
  `0x95da10 + i*0x130` for `i < *(0x985af4)` matching the name at +0x13, pull fields, recompute, then
  arm gdb. A static prediction that later matches a bp print is the cheapest verification there is.

## Operational kit
- Game: pid via `pgrep -x terran.exe`. Launch if down:
  `cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine explorer /desktop=smac,800x600 terran.exe >/dev/null 2>&1 &`
  then `scripts/m48d_boot.py` (BackSpace clear broken — loop it) or drive manually.
- Preflight: `pgrep -x gdb` empty; `TracerPid:` 0 in `/proc/PID/status`; `sysctl kernel.yama.ptrace_scope`
  must be 0 (resets to 1 on reboot).
- Read-only state: `python3 scripts/smac_state.py --json` or direct `/proc/PID/mem` pread.
- **Armed runs**: `python3 scripts/m51a_drive.py --tag mXX --rounds 3 --budget 1100` (m52b AND m53a ran
  clean: 3 rounds, 0 OCR, clean detach). Locates our base by NAME, pokes (+0x3c=500, +0xcc=1,
  +0xd0=200, +0x40=200 — cc AND d0 pokes die per-VISIT now, +0x3c/+0x40 survive to the pipeline),
  arms gdb AFTER poking (M33), drives colour-only, SIGINTs gdb + kill -CONT. gdb log is
  block-buffered — read AFTER detach. Launch with a foreground timeout > 600 s so the runtime
  promotes it to a tracked background job with notify-on-complete (keep budget < timeout).
- Template sites (GDB_TMPL in `scripts/m51a_drive.py`): sweep 0x520540 / 0x5206d3 / 0x5206f9 /
  0x5206fd, YEAR 0x51f554, `0x4f5aa9` (EDI_ENTRY), QGATE 0x4ef88b, 0x4ef8e2 / 0x4ef8ed (NEGPATH, 0
  hits twice now), 0x4efa4b / 0x4efa52 (POSPATH/POSMUL), SPENDA 0x4efed8 + 0x4efedd (W40_SPENDA),
  IADD 0x4ef7f6, CLAMP1 0x4eff20, SPENDB 0x4f0ca6, CLAMP2 0x4f0ce9, F26E0 gate sites, CONVST
  0x4f2d7d, 0x4e9397/0x4e93a4, E410 sites 0x4ee56b/0x4ee709/0x4ee72c/0x4ee82f/0x4ee869/0x4ee8c7,
  W3C_PIPE 0x4efb31, W3C_PODCLAMP 0x4f022b, **NEW M53a: QPIPE 0x4ef6d0 + QCOMPLET 0x4efe41 (both
  NAME-conditioned through `*(int*)0x8f0d60` — dwords 0x6d696c43@+0x13 + 0x69746361@+0x17; slide-
  proof; print f50/f44/f4c/f68/fc0/fcc/st/f3c/d0, QCOMPLET adds ebx + [ebp-0x1c/-0x2c/-0x18/-0x30])**,
  HW watchpoints (2 of 4 DR slots) `+0x3c` and `+0x40`. A third watchpoint fails to insert and
  detaches with zero hits. Sites NOT armed: PIPE internals 0x4ef7db/0x4ef9b3/0x4efae5/0x4efd49/
  0x4f1e3f, spawn 0x4eff4e (0x5ab650 call), dequeue candidates 0x507ef0/0x5437d0/0x417ee0, PANE
  0x483470.
- Pitfalls in force: M33 (poke only TracerPid 0, arm after), gdb-INT leaves inferior stopped →
  kill -CONT; never Escape on title/REALLYQUIT; OCR words ≥4 chars; OK-bar ≥1.2 s after row select;
  advisor panes transient (never key-dismiss); gdb's `$eip` sits just PAST the store; grep the watch
  log for writer prefixes before concluding "nothing fired"; a python driver whose argv contains its
  run tag SIGINTs itself (fixed: pgrep + os.kill skipping os.getpid()); gdb-attached X events can
  drop — re-press keys after arming; a gdb `-x` script must end with `continue`; **Ghidra short*
  aliasing on DAT_008f0d60 doubles offsets** (see Footing).
- **COMM OFFICER 3-row variant** ("I have Colonel X on Channel 9…"): close with `windowfocus`,
  `key Down`, 0.4 s, `key Return`. "Display faction leader profile" → UNIVERSITY INTELLIGENCE FILES
  → Escape. Both handlers are in the driver.
- Autosaves: `programs/saves/auto/Alpha Centauri Autosave N.SAV`, mission year = u16 @ file 0x54 (READ
  before trusting the slot; slots rotate). Load recipe: LOAD GAME (610,344) → name box (400,252) → End
  → 200× BackSpace (loop) → `Z:\home\n100\reverse\smac\programs\saves\auto\...` → Return → OK (290,391)
  → ops-director modal row (400,307) → OK (400,362) → Escape. `scripts/m48d_boot.py` automates most.

## Milestone options (pick ONE)
- **M53c — who dequeues after a positive completion (THE PICK)**
  The pipeline never writes +0x50; the tail clear is negative-only. Open: after the head item pays
  and completes, WHO advances the array (shift slots 1..n → 0..n−1, decrement +0x4c, or clear slot 0
  when +0x4c==0)? Candidates: 0x507ef0 / 0x5437d0 (both clear +0x44 AND +0x50 — full-clear events?),
  the enqueue path 0x417ee0 (overwrite/shift on insert?), or 0x4ee410/0x4f26e0 downstream in 0x4f5a70.
  (a) Disassemble the 0x4f5a70 tail after `FUN_004ef6d0` returns (shard_012.c:24186+: the
  `iVar2 = FUN_004ee410()` block) and the two clear functions' callers (`grep -rn "FUN_00507ef0(\|
  FUN_005437d0(" ghidra_out/shard_*.c`); (b) ONE run: poke +0x40=200 AND set a second queue slot
  (+0x54 = 3, +0x4c = 1) via /proc/mem BEFORE arming, arm hw watchpoints on +0x50 (replace the +0x3c
  watch — the +0x3c story is closed), plus bps at 0x507ef0/0x5437d0 entry printing the target base;
  print f50[0..3]/f4c/f44 at QPIPE/QCOMPLET. If the second slot never surfaces, the queue may be
  head-only in solo — say so. Do NOT re-run the edi chain or the +0x40 watchpoint.
- **M53b — what the +41 byte IS** (production weight vs the autocalculated +43 cost; cross-check the
  alpha `#UNITS` "Cost = 0 ⇒ Autocalculate" rule against live +41/+43 across all 14 `#UNITS` rows +
  the runtime item table `0x984d44`; static-friendly).
- **Later:** M50c (base+0xcc = −3 source: 0x4eaa10 / 0x4e92c0 / slider UI), M50d (the 2320 +4 energy
  credit), M50e (player idx → faction name via #FACTIONS), M51b (energy-pool store 0x4f2dc4-0x4f2e97),
  what base+0xc0 is (constant 7 == pop in m53a).
- **Retired premises, do not resurrect:** "edi = the sweep-entry index"; "0x4e40a0 is just the
  `(1<<p)&mask` event test"; "no +0x40 writer fired in m51f"; "PROGDIV accumulates build progress"
  (it formats an ETA string); "base+0x50 is a single dword" (it is a 10-slot array head).

## Report style
Findings → SESSION_NOTES.md (dated section) + rewrite NEXT_PROMPT.md; evidence under
`~/reverse/smac/evidence/` (never /tmp); cite log line numbers for every claim; state VERIFIED vs
INFERRED; end with one dated SESSION_NOTES line + the next-prompt pointer.
