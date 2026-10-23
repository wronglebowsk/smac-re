# NEXT_PROMPT — SMAC RE, session 55

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive),
the operational kit, and the queued milestone options. Do ONE milestone, checkpoint to
`SESSION_NOTES.md` (+ rewrite this file), then STOP.

## First actions
1. `skill_view('smac-cvr-format')` — harness pitfalls + code atlas.
2. `tail -95 ~/reverse/smac/SESSION_NOTES.md` — M53c (session 54) is the latest milestone.
3. Check live state (kit below): game up (`pgrep -x terran.exe`), year ≥ 2371, our turn open (cur=3),
   TracerPid 0, `kernel.yama.ptrace_scope` = 0.

## Footing — base economy (M48d → M53c, VERIFIED unless marked)

### M53c (session 54): the dequeue — `FUN_004ef5d0` pops the head; the pipeline calls it at 0x4f037b
- **+0x4c is the PENDING-entry COUNT, not a "last used index"** (M53a's label, corrected). Entries =
  `+0x4c + 1`: head at `+0x50`, pending at `+0x54 .. +0x54+4·(count−1)`; the UI caps count at 9 ⇒ 10
  entries = the `+0x50..0x73` array ✓. Every drain agrees: the pop shifts `count` slots then
  decrements; `FUN_004f4060` (evidence/m53c_fn4f4060_pseudocode.txt:269-278), `FUN_005437d0` and
  `FUN_00507ef0` (evidence/m53c_setters_pseudocode.txt:176-198, :199-217) each iterate exactly
  `[+0x4c]+1` dwords from +0x50 decrementing item counts.
- **THE POP = `FUN_004ef5d0(base_idx)`** (0x4ef5d0, 244 B; disasm
  `evidence/m53c_fn4ef5d0_disasm.txt`, Ghidra `shard_012.c:20538`): `if ([base+0x4c]==0) return 0`
  (`:12,:16`); if head ≥ 0 `dec BYTE [0x94de84 + owner·0x20bc + head]` (`:20-27`); shift
  `slot[i-1] := slot[i]`, i = 1..count, `+0x50` first (0x4ef628-0x4ef639, `:32-38`); `+0x4c -= 1`
  (0x4ef642, `:41`); validate the NEW head with `0x5a73f0(item, owner, base)` / `0x5a6e70(|q|, owner,
  base, 0)` (`:48,:58`) and if unavailable **pop again** (`jne 0x4ef5fa`, `:64`); new head ≤ −39 ⇒
  `0x446250(0x24)` (`:73`); then `0x473760(x, y, 2, 2)` redraw, return 1 (`:82,:84`). Callers: ONLY
  0x4ef992 / **0x4f037b** / 0x4f0f46, all inside `FUN_004ef6d0` (`evidence/m53a_fn_disasm.txt:195,
  :827, :1611`).
- **The fork choosing pop vs re-pick** (0x4f033e-0x4f037b): `[base+0x30] |=
  0x800000`, `[base+0x30] &= 0x7fffffff`, then `bl = [ebp-0x2c]` (= 1<<owner, set at 0x4ef815) `test
  bl, [0x985b10]` → **owner IN mask ⇒ 0x4f037b `call 0x4ef5d0` (POP); else ⇒ jmp 0x4f0589
  `FUN_004e5ae0(base, edi)` (RE-PICK)**. Our owner 3 ∈ mask 0xff08 ⇒ pop.
- **Live, twice** (pokes `+0x50=2, +0x54=3, +0x4c=1, +0x40=200` = a legal 2-entry queue): QPIPE st=200
  head 2/count 1 → QCOMPLET → SPENDA cost 10 → CLAMP1 st=190 → **WP50 `eip=0x4ef62e` 2→3** → **WP4C
  `eip=0x4ef648` 1→0** (`evidence/m53c_watch.log:144-147, :151-154, :161`); later visits head 3 / count 0
  (`:260, :312`). Run 2 pinned the site: POP @ 0x4f037b fired between CLAMP1 and the shift store,
  POP_EARLY/POP_LATE 0 hits (`evidence/m53c2_watch.log:37, :38, :42-45`). All six re-pick sites and the
  tail clear: **0 hits** in both runs.
- **Consequence (closes M53a open (a)):** with `+0x4c == 0` NOTHING consumes the head — 0x4ef5d0 returns
  0 at its gate — so a payable head re-completes EVERY round (M45's units 1→6 off one standing queue;
  M53a's head 2 unchanged for 3 rounds). The standing item a player sees IS the repeat-build state.
- **+0x50 writer census** (evidence/m53c_setters_pseudocode.txt): `FUN_004e5560` (`shard_012.c:14625`)
  is the only SETTER — head := new, early-return if unchanged, item count old−1 / new+1 — its only
  callers are 3 sites in `FUN_004e5ae0` = "re-pick via `FUN_004f6030`" (30,475 B AI build
  planner, `shard_012.c:24338`). Live: 122 re-picks over 3 rounds on 40+ other bases,
  **0 on ours (idx 70)**; new heads are facility ids (85/153/149/72/84/164) plus **−29 ×7** (outside
  the −(39+project) band, unexplained). `FUN_004e46f0` (base-creation autocalc) and `FUN_004e47d0` (base
  init) seed +0x50. Clears/re-picks that did NOT fire for us (f38 = 0x00dfbe41, owner ∈ mask):
  `0x507ef0` 1 hit but for base 46 (`evidence/m53c_watch.log:247`), `0x5437d0` 0, tail clear 0x4f1e3f 0
  (gate `evidence/m53c_tail_disasm.txt:73-80`), re-pick 0x4f1e01 0 (gate `:61`).
- **Truncation pitfall (cost M53a a whole wrong conclusion):** `evidence/m53a_fn_disasm.txt` ends at
  0x4f1d5d — 2,600 insns ≈ 9,869 of the 12,298-byte function (avg 3.8 B/insn). Size the dump from
  `index.csv` size ÷ 3.8 or bound it by the next function's address; the missing 2.4 KB held the tail
  clear and two re-pick sites (`evidence/m53c_tail_disasm.txt`).

### M53a (session 53): the queue record (labels corrected above)
- `+0x44` = active-item mirror: `0x4f5a70` copies `+0x50 → +0x44` AFTER the pipeline returns
  (`shard_012.c:24185`, short*-alias `+0x22 := +0x28`) and snapshots `[base+0x98] := storage` (`:24184`);
  live f44 == f50 at every QPIPE and tracked the popped head to 3 (`m53c_watch.log:260`).
- **Encoding** (`evidence/m53a_qgate_disasm.txt:5-55` = 0x4ef88b-0x4ef938): `−38 (0xffffffda)` = empty
  → NOQUEUE 0x4ef9b3; `≥ 0` = item id (unit `< 0x40`, facility `≥ 0x40`); `< 0` = `|q|`, a SECRET
  PROJECT with `|q| = 39 + project_idx` (0x4f0d83 writes `0x985b3c[|q|−39] := base index`; 33-dword
  table, `shard_013.c:15670`), cost `0x4e40a0(owner,1,−1) × dword[0x984d44 + 48·|q|]`. Scratch:
  `[ebp-0x2c] = 1<<owner` (0x4ef815, live m2c=8), `[ebp-0x1c] = 52·id` on the positive path (live 104).
- **Completion is PAYMENT-DRIVEN, no progress counter**: COMPLET 0x4efe41 fires the instant
  `storage ≥ factor × 0x5ac950(id, idx, 0)` (`cmp [ecx+0x40],edi; jge` 0x4efa5e-61); PROGDIV 0x4efd49
  formats an ETA string, not an accumulator. Dispatch: unit → SPENDA; facility → set bit 2 of word
  `[0x98adb8 + 52·id]` (built flag; newly-set ⇒ repoint 0x8f0d60 + the 0x4e8d60/0x4e78e0/0x4e92c0/
  0x4e93f0/0x4eaa10 chain); class-8 Colony Pod ∧ pop==1 ∧ `0x94d438[p]>1` → ABANDONBASE confirm
  `0x48ee00`. Downstream of CLAMP: `[+0x98]:=[+0x40]` → `0x5ab650(x, y, [ebp-0x28], ebx)` returns the new
  unit idx (flags `0x93327c + idx·52`) → PRODUCE pane. **IADD gate
  CLOSED**: `storage += d0` iff `d0 ≥ 0 ∧ queue ≠ −38 ∧ (f30 & 2) == 0` (`fn_disasm.txt:65-69`). cc/d0
  recompute PER-VISIT (pokes dead by the first pipeline print).

### M52b / M52a (sessions 51-52, condensed)
- SPENDA `edi` = `0x4e40a0(owner,1,−1) × 0x5ac950(queue_id, idx, 0)` = 10 for our queued Scout Patrol
  (`m52b_watch.log:386-400`); `0x5ac950` returns the type-record **+41 byte** (`0x98ad88 + type·52`,
  clamped [1,999] only for class 8); `0x4e40a0` arg2==1 → government switch ×1 for us. Scout Patrol =
  class 3, +41=1, +43=10 → **M53b open**.
- `0x4ee410` owns only +0x3c/+0x6/+0x7 (threshold `0x4e40a0(owner,0,idx) × (pop+1)` = 80, reset writes
  HALF, accrual `+0x3c += [+0xcc]`); +0x40 writers = SPENDA 0x4efee0 + CLAMP1 0x4eff23 only; clamp =
  `storage := max(0, min(base+0xd0, cap 0x92a370=10))`.

### Standing from earlier sessions (do not re-derive)
- Storage writers: IADD 0x4ef7f6 (gated above), SPENDA 0x4efee0, CLAMP1 0x4eff20/23, CONVST 0x4f2d7d (in
  `0x4f26e0` = mineral↔energy conversion/income, scales with faction energy pool `0x94d650+p·0x20bc`; our
  base ALWAYS early-returns there at 0x4f2705/0x4f271e).
- **The sweep never truncates** (M50b): `0x520540` reloads n_bases per iteration; year store 0x51f554
  fires BETWEEN passes; the base array SLIDES, so locate records by NAME.
- Base record fields: x u16@0, y u16@2, owner@4, pop@6, f18/f1c/f20/f28/f30, **+0x3c progress**,
  minerals@0x40, 44 (active-item mirror), **4c (PENDING count, cap 9)**, **queue array @0x50..0x73**, 68
  (slot 6), 8a/8c (facility bitmap), 98 (storage snapshot), c0 (=7, == pop this run; unresolved),
  cc@0xcc (progress delta, −3 for us, recomputed per-visit), d0@0xd0 (net mineral income, recomputed),
  fc@0xfc (+3 energy for us), f38 const 0x00dfbe41.
- Unit/facility type record `0x98ad88 + type·52`: name +0[34], +0x29 (41) production weight, +0x2a (42)
  class, +0x2b (43) cost-ish, +0x30 word (facility built-flag), ability +32 (`0x98ada8`), domain +36
  (`0x98adac`). Live: 0 Colony Pod (cls 8, +41 3, +43 40), 1 Formers (cls 9, 2/41), 2 Scout Patrol (cls
  3, **1/10**), 3 Transport Foil (cls 7, 3/39).
- Item upkeep table `0x984d44/0x984d48 + item·48` (M46); **per-player item counts are BYTES at
  `0x94de84 + player·0x20bc + item`** (0x4e5560 set / 0x4ef5d0 pop / the three drains maintain them);
  project builder registry `0x985b3c + 4·(0..32)` (33 secret projects).
- Income globals (M46): gross 0x745734, upkeep 0x744f28, net 0x7457dc, trade 0x7457d4, food 0x74572c.
  Verified: year 0x985b00, turn 0x985afc, cur 0x985dcc, nb 0x985af4, mask 0x985b10
  (0xff08), solo 0x920434, cap 0x92a370 (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base
  array 0x95da10 stride 0x130, unit array 0x933278 stride 52, trait record 0x927a7c+p·0x59c, faction
  records 2095 ints (stride 0x20bc), int[17] @0x94d694, int[20] @0x94d6a0.
- Ghidra types `DAT_008f0d60` as `short *`: pseudocode `+0x20` = bytes 0x40, `+0x22` = 0x44, `+0x26` =
  0x4c, `+0x28` = 0x50, `+0x1e` = 0x3c, `+0x66` = 0xcc, `+0x4c` = 0x98 — ALWAYS double offsets there.
  Corollary: `DAT_0095da5c` = base+0x4c, `DAT_0095da60` = base+0x50 (`·0x4c` index = 0x130 B).

## Static-reading kit
- **Clean 32-bit disassembly, no attach**: `gdb -batch -nx -q -ex "set architecture i386" -ex "set
  disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` (PE maps as file target;
  TracerPid stays 0; output line 1 is an arch banner — line N = insn N−1). Redirect to `evidence/` and
  grep it — never paste a whole function. **Check coverage: `index.csv` size ÷ 3.8 ≈ insn count, and
  confirm the last address printed == the next function's start.** Whole-FUN dumps:
  `evidence/m53a_fn_disasm.txt` (FUN_004ef6d0, INCOMPLETE — ends 0x4f1d5d),
  `evidence/m53c_tail_disasm.txt` (0x4f1d50-0x4f299f, the rest), `evidence/m53c_fn4ef5d0_disasm.txt`
  (complete). Ghidra pseudocode: `scripts/fn.py 0xADDR` (copy:
  evidence/m53a_fn4ef6d0_pseudocode.txt). Corpus grep:
  `grep -rn <pat> ghidra_out/shard_*.c`, then the owning function with
  `awk '/^\/\/ ==== /{h=$0} NR==<line>{print h; exit}' <shard>`.
- Live `/proc/PID/mem` pread (TracerPid 0) beats guessing: read `0x8f0d60`, walk `0x95da10 + i*0x130`
  for `i < *(0x985af4)` matching the name at +0x13, pull fields, recompute, then arm gdb.

## Operational kit
- Game: pid via `pgrep -x terran.exe`. Launch-if-down command: the skill's Wine section has it verbatim;
  then `scripts/m48d_boot.py` (BackSpace-loop broken).
- Preflight: `pgrep -x gdb` empty; `TracerPid:` 0 in `/proc/PID/status`; `sysctl kernel.yama.ptrace_scope`
  must be 0 (resets to 1 on reboot). Read-only state: `python3 scripts/smac_state.py --json` or
  `/proc/PID/mem` pread. Our base = idx **70** @ 0x962d30 (idx = (addr − 0x95da10)/0x130).
- **Armed runs**: `python3 scripts/m53c_drive.py --tag mXX --rounds 3 --budget 1100` (m52b, m53a, m53c,
  m53c2 all clean: 0 OCR, clean detach); leaner variant `scripts/m53c2_drive.py`. Locates our base by
  NAME, pokes via `/proc/mem` BEFORE arming, arms gdb after poking (M33), drives colour-only, SIGINTs gdb
  + kill -CONT; the gdb log is block-buffered — read AFTER detach. Launch with a foreground timeout > 600
  s so the runtime promotes it to a tracked background job with notify-on-complete.
- Template sites: GDB_TMPL in `scripts/m53c_drive.py` carries the 17 M48-M52 sites (sweep 0x520540,
  YEAR 0x51f554, QGATE 0x4ef88b, SPENDA 0x4efed8, IADD 0x4ef7f6, CLAMP1 0x4eff20, CLAMP2 0x4f0ce9,
  CONVST 0x4f2d7d, the 0x4ee410 stores, W3C 0x4efb31/0x4f022b, QPIPE 0x4ef6d0, QCOMPLET 0x4efe41, …) —
  QPIPE/QCOMPLET are NAME-conditioned through `*(int*)0x8f0d60`. **NEW M53c: POP 0x4ef992 / 0x4f037b / 0x4f0f46, RE-PICK 0x4ef87e /
  0x4f0589 / 0x4f08d4 / 0x4f09b6 / 0x4f1e01 / 0x4f21b8, tail clear 0x4f1e3f, writer entries 0x4e5ae0 /
  0x4e5560 / 0x507ef0 / 0x5437d0 / 0x417ee0 (print `*(int*)($esp+4)` = base idx)**. HW watchpoints: 2 of
  the 4 i386 DR slots (m53c used +0x50 and +0x4c; gdb prints Old/New itself, `$eip` sits PAST the
  store); a third fails to insert and detaches with 0 hits.
- Pitfalls: the standing list is in the skill (M33 poke-then-arm, `kill -CONT` after gdb-INT, never
  Escape on title/REALLYQUIT, OCR ≥4 chars, OK-bar ≥1.2 s, transient advisor panes, `$eip` past the
  store, grep for writer prefixes before "nothing fired", self-SIGINTing driver argv, dropped X events
  under gdb, `-x` scripts end with `continue`). NEW: **Ghidra short* aliasing doubles offsets**;
  **`*(int*)0x68cbb0` (cur base idx) equals the argument of 0x4e5ae0/0x4e5560 while they run — an
  `ours=` test there is always 1; compare against base INDEX 70**; **coverage-check every dump**.
- **COMM OFFICER 3-row variant** ("I have Colonel X on Channel 9…") and the UNIVERSITY INTELLIGENCE
  FILES detour: both handlers are already in the driver (recipe in the skill).
- Autosaves: `programs/saves/auto/Alpha Centauri Autosave N.SAV`, mission year = u16 @ file 0x54 (READ
  first; slots rotate). `scripts/m48d_boot.py` automates the LOAD GAME recipe (LOAD GAME 610,344 → name
  box 400,252 → path `Z:\home\n100\reverse\smac\programs\saves\auto\...` → OK 290,391 → ops-director
  row 400,307 → OK 400,362 → Escape; BackSpace clear must be LOOPED).

## Milestone options (pick ONE)
- **M53d — who APPENDS to the pending queue (THE PICK)**
  The pop is closed; nobody has been found who WRITES the pending slots. No function writes base+0x54 by
  symbol (`DAT_0095da64`: 0 hits) or by short-alias (`DAT_008f0d60 + 0x2a`: 0 hits); `0x417ee0` writes
  only slot 0 (`shard_001.c:9452`) yet adjusts +0x4c (`:9258` dec, `:9429/:9434` set/inc, cap 9), and
  `FUN_0059ce10` seeds `+0x4c = pop·10/2` (= 35 at pop 7, over the cap — `shard_015.c:14416, 14770`).
  (a) Static: name the owning functions of the enqueue-dispatcher callers
  (`grep -rn "FUN_00417ee0(" ghidra_out/shard_*.c` — shard_001.c:2155, 2204, 8535, 12265 …), read the
  case-3 branch (`shard_001.c:9380-9460`) to see where an appended item lands, and check the command
  recorder `FUN_00446250` (98 B, `shard_003.c:1009`) + the netplay replay path for a walked-pointer store.
  (b) ONE run: poke a THREE-entry queue (+0x50=2, +0x54=3, +0x58=4, +0x4c=2) with +0x40=200, hw-watch
  +0x54/+0x58 (the pop shifts twice ⇒ both must fire inside 0x4ef5d0 — positive control),
  keep the 0x417ee0/0x4e5560 bps; print f50/f54/f58/f4c at QPIPE/QCOMPLET. If a UI append is needed
  to catch the writer, drive the base-production picker (windowfocus first) with the watches armed. Say
  plainly if the append is save-only.
- **M53b — what the +41 byte IS** (production weight vs the autocalculated +43 cost; cross-check the
  alpha `#UNITS` "Cost = 0 ⇒ Autocalculate" rule against live +41/+43 across all 14 rows; static-friendly).
- **Later:** the −29 head value (7 hits, outside the −(39+idx) band); what fires at 0x4ef992/0x4f0f46
  (0 hits); M50c (base+0xcc = −3 source), M50d (the 2320 +4 credit), M50e (player idx → faction name),
  M51b (energy-pool store 0x4f2dc4-0x4f2e97), base+0xc0 (== pop).
- **Retired premises, do not resurrect:** "edi = the sweep-entry index"; "0x4e40a0 is just the
  `(1<<p)&mask` event test"; "no +0x40 writer fired in m51f"; "PROGDIV accumulates build progress" (it
  formats an ETA string); "base+0x50 is a single dword" (10-slot array); **"+0x4c is the last used
  index"** (pending-entry count; entries = +0x4c+1); **"the pipeline has no +0x50 writer"** (it pops
  through a CALL to 0x4ef5d0 at 0x4f037b); **"M53a's whole-function dump is complete"** (ends 0x4f1d5d).

## Report style
Findings → SESSION_NOTES.md (dated section) + this file; evidence under
`~/reverse/smac/evidence/` (never /tmp); cite log line numbers for every claim; mark VERIFIED vs
INFERRED; end with the next-prompt pointer.
