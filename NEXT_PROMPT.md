# NEXT_PROMPT — SMAC RE, session 53

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive),
the operational kit, and the queued milestone options. Do ONE milestone, checkpoint to
`SESSION_NOTES.md` (+ rewrite this file), then STOP.

## First actions
1. `skill_view('smac-cvr-format')` — harness pitfalls + code atlas.
2. `tail -70 ~/reverse/smac/SESSION_NOTES.md` — M52b (session 52) is the latest milestone.
3. Check live state (kit below): game up (`pgrep -x terran.exe`), year ≥ 2363, our turn open (cur=3),
   TracerPid 0, no gdb attached, `kernel.yama.ptrace_scope` = 0.

## Footing — base economy (M48d → M52b, VERIFIED unless marked)

### M52b (session 52): the SPENDA subtrahend is a COST; the "index quirk" is dead
- `edi` at the SPENDA store `0x4efedb sub esi,edi` = **`0x4e40a0(owner, 1, −1) × 0x5ac950(queue_id, idx, 0)`**
  = 10 × 1 = 10 for our queued Scout Patrol, measured site by site in one run (evidence/m52b_watch.log:386
  EDI_ENTRY → :388 EDI_QGATE → :389 EDI_POSPATH → :390 EDI_POSMUL → :391 EDI_SPENDA → :392 W40_SPENDA
  200→190 → :400 W40_CLAMP1 190→0, cap 10, d0 0).
- **M49a's "edi = sweep-entry index" is falsified**: `0x4f5a70` assigns edi at `0x4f5aa9 mov edi,edx` from
  `0x4f5a9c mov dl,BYTE PTR [ecx+0x4]` (edx zeroed at 0x4f5a7a) ⇒ **edi := the base's OWNER BYTE**. Printed
  222/222 base-visits and it matched every owner (Morgan 4, Sparta 5, Assassin's 6, U.N. 7 —
  evidence/m52b_watch.log:62, :94, :109, :139). Our index is 70, our owner byte 3, the observed value 10.
- `0x4eaa10` is NOT the clobberer: `push edi` 0x4eaa41 / `pop edi` 0x4eb672
  (evidence/m52b_fn4f5a70_4eaa10_disasm.txt:396, :1357) — callee-saved and restored.
- `0x4e40a0(p, 1, −1)` = the **economic/government factor**: event-owner base 10 → rescale by DAT_0092a290
  (10) and DAT_0092ada8 (2 ⇒ neither ×0.9 nor ×0.8) → arg2 == 1 jumps to the switch at `0x4e421f`, index =
  `faction[p].int[20] @0x94d6a0+p·0x20bc + 7`, table `0x4e4318` (12 dwords). Ours (int[20] = 0 → index 7)
  lands on `0x4e430f mov eax,esi` = the **×1 case**; cases 0-4 are `(esi·13+9)/10` (×1.3). The table is the
  government economy ladder.
- `0x5ac950(type, idx, out)` = per-type production helper (evidence/m52b_fn5ac950_disasm.txt:6, :12, :13,
  :25, :26, :119, :123): `esi = arg1` is a **unit/facility type id** indexing `0x98ad88 + type·52`; it loads
  `bl = byte[type+0x29]` (+41) for every type, clamps it to [1, 999] only when class byte `+0x2a` == 8 and
  idx ≥ 0, and for `type < 0x40` returns via the tail `mov eax,ebx`. `type ≥ 0x40` is the facility case
  (checks `byte[type+0x30] & 4`, group flag `0x927a98`, `0x94d438`). Live +41: Colony Pod 3, Formers 2,
  **Scout Patrol 1**, Transport Foil 3; byte +0x2b (+43) is 10 for Scout Patrol (40/41/39 for the others)
  and alpha `#UNITS` documents its own Cost field as "0 = Autocalculate". INFERRED: +41 is a production
  weight, not the mineral cost itself.
- **`base+0x50` is the queued production item id** (live 2 = unit type 2 "Scout Patrol"), not anonymous
  scratch. QGATE `0x4ef88b` decodes it: `0xffffffda` = empty → NOQUEUE `0x4ef9b3`; ≥ 0 = id → `0x4efa2c`;
  < 0 = `|q|` with `[ebp-0x1c] = |q|−39` and `[ebp-0x20]` set by the 34/39 thresholds (0x4ef8a1-0x4ef8c9).
  The negative branch would instead set `edi = 0x4e40a0(owner,1,−1)` at `0x4ef8e2` and
  `imul edi,[edx+0x984d44]` (edx = |q|·48) at `0x4ef8ed` — **never taken for us** (0 EDI_NEGPATH hits).
- Cost story: M48d's "Scout Patrol cost 10" is restored in substance (subtrahend = factor × per-type byte);
  M49a's retraction ("10 = our base index") is gone.

### M52a (session 51): base+0x3c arithmetic CLOSED; 0x4ee410 does not own +0x40
- `FUN_004ee410` (0x4ee410, 2076 B) reads/writes only the `0x8f0d60` current-base global; its whole store
  inventory is `[reg+0x3c]` ×6, `[reg+0x6]` (pop) ×3, `[ecx+0x7]` ×1 — **zero `+0x40` references**
  (evidence/m52a_fn4ee410_disasm.txt).
- Threshold `ebx = 0x4e40a0(owner,0,idx) × (pop+1)` at `0x4ee5aa` (= 80 for us); `0x4ee71a jl 0x4ee8ba` sends
  progress below the threshold straight to the accrual tail `0x4ee8c7 [+0x3c] += [+0xcc]` (cc = −3/round).
  The reset store `0x4ee82f` writes **half the threshold**: `trunc_div2(factor × (pop+1))` = (10×8)/2 = **40**
  at pop 7 (all inputs printed live: evidence/m52a_watch.log:329; m51f:230). The `mov esi,0x19` at 0x4ee7fa
  feeds only the message path `[0x984d38 + esi·15·16]`.
- Reset-vs-pop++ selector: `pop − flag + trait[p][0]` vs `DAT_0092a2ac` (7) then `DAT_0092a2b0` (14);
  `flag = 2` iff `owner(base[max(DAT_00985b9c,0)]) == owner(ours)` (live flag 0: DAT_985b9c = −1 → base[0]
  "The Rapture" owner 2). The pop-growth branch is `0x4ee869 [+0x3c] := 0` + `0x4ee875 pop++` + the
  0x4e8d60/0x4e78e0/0x4e92c0/0x4e93f0/0x4eaa10 chain. `0x421fe0(kind, idx, 0)` = facility-byte test at
  `base+0x8c+kind` (24/25 = +0xa4/+0xa5, both 0 for us).
- **+0x40 writers (exhaustive net)**: hw watchpoint on our base's `+0x40` fired only at `0x4efee0` (SPENDA)
  and `0x4eff23` (CLAMP) — nothing outside the pipeline set (evidence/m52a_watch.log:310, :311, :318, :319,
  :326; identical in m51f :212/:219/:220/:227 — session 50's "no writer fired" was a **log misread**).
- Clamp (static 0x4efee6-0x4eff20): `edx = min(base+0xd0, cap 0x92a370=10)`; if `storage ≤ edx` leave it;
  else event-owner gate `0x4eff02`, then `storage := max(0, min(d0, cap))`. ⇒ M50b's "200 → 7"
  (evidence/m50c_watch.log:117) IS that store with d0 = 7 (INFERRED — m50c printed no d0). d0 = 0 today ⇒
  the clamp pins storage to 0 every completion.

### Standing from earlier sessions (do not re-derive)
- **Storage writers**: IADD `0x4ef7f6` (`+= d0`; GATED — 2 hits in 3 rounds, both d0 = 0, so not
  unconditional), SPENDA `0x4efee0` (store `0x4efedd`; subtrahend = the cost above), CLAMP1 `0x4eff20/23`,
  CONVST `0x4f2d7d` (inside 0x4f26e0, a CREDIT `storage += ((pool/esi)·45)/trait`, live +0…+12). esi at
  COMPLET = path residue; pop at COMPLET = pre-completion value.
- `0x4f26e0` = mineral↔energy conversion/income step: our base ALWAYS early-returns at gate `0x4f2705` +
  flag test `0x4f271e` (`ecx=0x20`), never reaches PASTFLAG (m52b: 219 PASTFLAG / 222 VISIT / 3 FLAGTEST).
  Amount scales with the faction energy pool `0x94d650+p·0x20bc`.
- **The sweep never truncates** (M50b): `0x520540` scans all bases and reloads n_bases each iteration; the
  year store `0x51f554` fires BETWEEN passes. Locate records by NAME ("Climactic Research", string at
  base+0x13) — the array slides (idx 70 now, 71 in m50c) and the owner byte changes.
- Base record fields: x u16@0, y u16@2, owner@4, pop@6, f18, f1c, f20 (transient), f28, f30, **+0x3c
  progress**, minerals@0x40, 44, 4c, **+0x50 queue item id**, 68, 8a/8c (facility bitmap, byte groups), c0,
  **cc@0xcc (progress delta, −3 for us, recomputed)**, d0@0xd0 (net mineral income, recomputed every round
  at 0x4e955d — pokes die), e0, f0, fc@0xfc (+3 energy for us), f38 const 0x00dfbe41.
- Unit type record `0x98ad88 + type·52`: name +0[34], **+0x29 (41) production weight**, +0x2a (42) class,
  +0x2b (43) cost-ish, ability +32 (`0x98ada8`), domain +36 (`0x98adac`); class == alpha `#UNITS` field 5.
  Live: 0 Colony Pod (cls 8, +41 3, +43 40), 1 Formers (cls 9, 2/41), 2 Scout Patrol (cls 3, **1/10**),
  3 Transport Foil (cls 7, 3/39).
- Income globals (M46): gross 0x745734, upkeep 0x744f28, net 0x7457dc, trade 0x7457d4, food 0x74572c,
  needpct 0x745730. Verified: year 0x985b00, turn 0x985afc, cur 0x985dcc, nb 0x985af4, mask 0x985b10
  (0xff08), solo 0x920434, cap 0x92a370 (10), curbase ptr 0x8f0d60, **cur base INDEX 0x68cbb0**, base array
  0x95da10 stride 0x130, unit array 0x933278 stride 52, trait record 0x927a7c+p·0x59c, faction records
  2095 ints (stride 0x20bc), faction int[17] @0x94d694, int[20] @0x94d6a0, DAT_0092a290 = 10,
  DAT_0092ada8 = 2, DAT_0092a2ac = 7, DAT_0092a2b0 = 14, DAT_0092a27c = 2, DAT_00985b9c = −1.
- Pane id-printer bp 0x483470: advisories only.

## Static-reading kit
- **Clean 32-bit disassembly, no attach**: `gdb -batch -nx -q -ex "set architecture i386" -ex "set
  disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` (PE maps as file target;
  TracerPid stays 0). Redirect to `evidence/` and grep it — never paste a whole function. Jump tables need
  `x/12wx 0xADDR` (gdb otherwise disassembles the data). Sizes/insn counts: `grep -m1 004ef6d0
  ghidra_out/index.csv`. Ghidra pseudocode: `scripts/fn.py 0xADDR`. objdump misaligns on SEH blocks.
- Live `/proc/PID/mem` pread (TracerPid 0) beats guessing: read `0x8f0d60`, walk
  `0x95da10 + i*0x130` for `i < *(0x985af4)` matching the name at +0x13, pull the fields
  (pop/+0x3c/+0x40/+0x50/+0xcc/+0xd0/+0x30/+0x8c) plus the DAT_ globals, recompute the formula, and only
  then arm gdb. A static prediction that later matches a bp print is the cheapest verification there is
  (it settled M52a and predicted M52b's factor).

## Operational kit
- Game: pid via `pgrep -x terran.exe`. Launch if down:
  `cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine explorer /desktop=smac,800x600 terran.exe >/dev/null 2>&1 &`
  then `scripts/m48d_boot.py` (BackSpace clear broken — loop it) or drive manually.
- Preflight: `pgrep -x gdb` empty; `TracerPid:` 0 in `/proc/PID/status`; `sysctl kernel.yama.ptrace_scope`
  must be 0 (resets to 1 on reboot).
- Read-only state: `python3 scripts/smac_state.py --json` or direct `/proc/PID/mem` pread.
- **Armed runs**: `python3 scripts/m51a_drive.py --tag mXX --rounds 3 --budget 1100` (m52b ran clean: 3
  rounds, 0 OCR passes, clean detach). It locates our base by NAME, pokes (+0x3c=500, +0xcc=1, +0xd0=200,
  +0x40=200 — the d0 poke dies), arms gdb AFTER poking (M33), drives colour-only, SIGINTs gdb + kill -CONT.
  gdb log is block-buffered — read AFTER detach. Launch with a foreground timeout > 600 s so the runtime
  promotes it to a tracked background job with notify-on-complete (keep budget < timeout).
- Template sites (GDB_TMPL in `scripts/m51a_drive.py`): sweep 0x520540 / 0x5206d3 / 0x5206f9 / 0x5206fd,
  YEAR 0x51f554, `0x4f5aa9` (EDI_ENTRY, unconditional — 74 hits/round, prints the owner byte),
  QGATE 0x4ef88b (EDI_QGATE), 0x4ef8e2 / 0x4ef8ed (negative-queue edi path, 0 hits so far),
  0x4efa4b / 0x4efa52 (positive-queue edi path), SPENDA 0x4efed8 (EDI_SPENDA) + 0x4efedd (W40_SPENDA),
  IADD 0x4ef7f6 (W40_IADD, prints d0), CLAMP1 0x4eff20, SPENDB 0x4f0ca6, CLAMP2 0x4f0ce9,
  F26E0 gate 0x4f2705 / 0x4f271e / 0x4f2724, CONVST 0x4f2d7d, E410 sites 0x4ee56b / 0x4ee709 / 0x4ee72c /
  0x4ee82f (reset store; prints pop/scale/ada8/fac17/f30b) / 0x4ee869 (zero+pop++) / 0x4ee8c7 (accrual;
  prints cc), 0x4e9397 / 0x4e93a4; HW watchpoints (2 of 4 DR slots) `+0x3c` and `+0x40` with `name_at`.
  A third watchpoint fails to insert ("too many hardware breakpoints/watchpoints") and detaches with zero
  hits. NO bp on 0x64bfa3 (generic dword-copy loop — fatal hit rate). Sites that exist in the function but
  are NOT armed in the current template: PIPE 0x4ef6d0, IGATE 0x4ef7db, NOQUEUE 0x4ef9b3, ST1C 0x4efae5,
  PROGDIV 0x4efd49, COMPLET 0x4efe41, MIRA 0x4eff29, QDRAIN 0x4f1e3f, PANE 0x483470.
- Pitfalls in force: M33 (poke only TracerPid 0, arm after), gdb-INT leaves inferior stopped → kill -CONT;
  never Escape on title/REALLYQUIT; OCR words ≥4 chars; OK-bar ≥1.2 s after row select; advisor panes
  transient (never key-dismiss); gdb's `$eip` sits just PAST the store; **grep the watch log for the writer
  prefixes before concluding "nothing fired" — session 50 misread its own WP40 hits**; a python driver whose
  argv contains its run tag SIGINTs itself (fixed: pgrep + os.kill skipping os.getpid()); gdb-attached X
  events can drop — re-press keys after arming; a gdb `-x` script must end with `continue`.
- **COMM OFFICER 3-row variant** ("I have Colonel X on Channel 9…"): row clicks do nothing useful — close it
  with `windowfocus`, `key Down`, 0.4 s, `key Return` (selection opens on row 1). "Display faction leader
  profile" → UNIVERSITY INTELLIGENCE FILES → Escape. Both handlers are in the driver.
- Autosaves: `programs/saves/auto/Alpha Centauri Autosave N.SAV`, mission year = u16 @ file 0x54 (READ before
  trusting the slot; slots rotate). Load recipe: LOAD GAME (610,344) → name box (400,252) → End → 200×
  BackSpace (loop) → `Z:\home\n100\reverse\smac\programs\saves\auto\...` → Return → OK (290,391) →
  ops-director modal row (400,307) → OK (400,362) → Escape. `scripts/m48d_boot.py` automates most of it.

## Milestone options (pick ONE)
- **M53a — the `base+0x50` queue record end to end (THE PICK)**
  The id is known (2 = Scout Patrol) and so is the charge at completion (`factor × type+41`). Still open:
  where the build **progress** counter lives (which base/queue field advances toward completion), what
  exactly fires COMPLET `0x4efe41`, and how the id flips sign (QGATE's `< 0` branch, the 34/39 thresholds,
  `[ebp-0x1c] = |q|−39`). (a) disassemble the queue block from `0x4ef9b3` (NOQUEUE) through PROGDIV
  `0x4efd49` to COMPLET `0x4efe41` and name the progress field; (b) ONE run printing, for our base only,
  `+0x50 +0x44 +0x4c +0x68 +0xc0 +0xcc` at PIPE entry and at COMPLET, plus a bp at 0x4efe41 printing
  `[ebp-0x1c]` and `[ebp-0x2c]`. Do NOT re-run the +0x40 watchpoint or the edi chain — both are answered.
- **Superseded:** M52a and M52b are done (sessions 51, 52). Do not re-derive the 40/80 threshold pair, the
  +0x40 writer set, the clamp formula, or the edi provenance.
- **Retired premises, do not resurrect:** "edi = the sweep-entry index" (it is the owner byte, then the cost
  product); "`0x4e40a0` is just the `(1<<p)&mask` event test" (that is only its first gate); "no +0x40
  writer fired in m51f" (it fired twice).
- Later: M53b (what the +41 byte IS — production weight vs the autocalculated cost in +43; cross-check the
  alpha `#UNITS` "Cost = 0 ⇒ Autocalculate" rule against live +41/+43 bytes across all 14 `#UNITS` rows),
  M50c (base+0xcc = −3 source: 0x4eaa10 / 0x4e92c0 / slider UI), M50d (the 2320 +4 energy credit),
  M50e (player idx → faction name via #FACTIONS), M51b (energy-pool store 0x4f2dc4-0x4f2e97).

## Report style
Findings → SESSION_NOTES.md (dated section) + rewrite NEXT_PROMPT.md; evidence under
`~/reverse/smac/evidence/` (never /tmp); cite log line numbers for every claim; state VERIFIED vs INFERRED;
end with one dated SESSION_NOTES line + the next-prompt pointer.
