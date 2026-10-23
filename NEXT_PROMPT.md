# NEXT_PROMPT — SMAC RE, session 52

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive),
the operational kit, and the queued milestone options. Do ONE milestone, checkpoint to
`SESSION_NOTES.md` (+ rewrite this file), then STOP.

## First actions
1. `skill_view('smac-cvr-format')` — harness pitfalls + code atlas.
2. `tail -70 ~/reverse/smac/SESSION_NOTES.md` — M52a (session 51) is the latest milestone.
3. Check live state (see kit below): game should be up (pid via `pgrep -x terran.exe`),
   year ≥ 2360, our turn open (cur=3), TracerPid 0, no gdb attached.

## Footing — base economy (M49a → M52a, VERIFIED unless marked)

### M52a (session 51): base+0x3c arithmetic is CLOSED, and 0x4ee410 does not own +0x40
- `FUN_004ee410` (0x4ee410, 2076 B, 662 insns, reads/writes ONLY the `0x8f0d60` current-base global) is a
  **production-progress step on `base+0x3c`**. Its complete non-stack store inventory: `[reg+0x3c]` ×6,
  `[reg+0x6]` (pop byte) ×3, `[ecx+0x7]` ×1 — **zero `+0x40` references in the whole body**
  (evidence/m52a_fn4ee410_disasm.txt).
- Threshold: `0x4ee58f call 0x4e40a0(owner, 0, DAT_0068cbb0)` → `0x4ee5aa imul ebx, (pop+1)` ⇒
  **ebx = factor × (pop+1) = 80** for us. `0x4ee71a cmp [edi+0x3c], ebx; jl 0x4ee8ba`: while `+0x3c < 80` the
  function only accrues `0x4ee8c7 [+0x3c] += [+0xcc]` (cc = −3 ⇒ −3/round).
- Reset store: `0x4ee82f mov [ecx+0x3c],eax` with `eax = trunc_div2( 0x4e40a0(owner,0,idx) × (pop+1) )`
  (`movsx edx,[ecx+6]; inc edx; imul eax,edx; cdq; sub eax,edx; sar eax,1`) — i.e. **exactly half the
  threshold**: (10×8)/2 = **40** at pop 7. Live bp print of every input: evidence/m52a_watch.log:329
  (`old=500 new=40 pop=7 scale=10 ada8=2 fac17=0 f30b=0`); reproduced from m51f (evidence/m51f_watch.log:230).
  The `mov esi,0x19` at 0x4ee7fa feeds only the message path (`[0x984d38 + esi·15·16]`), NOT the 40.
- `FUN_004e40a0(p, arg2, idx)` is now decomposed (evidence/m52a_fn4e40a0_disasm.txt): event-owner test
  `(1<<p)&DAT_00985b10` ⇒ base 10; rescale by `DAT_0092a290` (÷10·scale, live 10) and `DAT_0092ada8`
  (1 ⇒ ×0.9, 0 ⇒ ×0.8, else unchanged — live 2 ⇒ unchanged); `score = clamp(faction[p].int[17]
  @0x94d694+p·0x20bc + 2·(base+0x30 byte0 & 4) + 2·(arg2 ∧ byte[base+0x8c+idx-term]), −2, 5)`;
  `return = (base·(10−score)+9)/10`. Ours: score 0 ⇒ **factor 10**. (M50a's "0x4e40a0 = (1<<p)&mask event
  test" was only the first gate — the return is this 0..10 factor.)
- Branch selector between reset and the pop-growth side: `pop − flag + trait[p][0]` vs `DAT_0092a2ac` (7),
  then vs `DAT_0092a2b0` (14); `flag = 2` iff `owner(base[max(DAT_00985b9c,0)]) == owner(ours)`. Live state
  (year 2358): DAT_985b9c = −1 → base[0] "The Rapture" owner 2 → flag 0; 7−0+0 = 7 ≥ 7 → reset path. The
  other branch is `0x4ee869 [+0x3c] := 0` + `0x4ee875 pop++` + the 0x4e8d60/0x4e78e0/0x4e92c0/0x4e93f0/0x4eaa10
  recompute chain. `0x421fe0(kind, base_idx, 0)` = facility-byte test at `base+0x8c+kind` (kind 24/25 = +0xa4/+0xa5).
- **+0x40 writers, exhaustive-net result**: hardware watchpoint on our base's `+0x40` (name-anchored) fired
  **2× in 2 rounds**, both known pipeline stores — `0x4efee0` (SPENDA; store is `0x4efedd sub esi,edi`) and
  `0x4eff23` (CLAMP). Static bps agree: IADD `0x4ef7f6` (d0=0, no-op), SPENDA `edi=10`, CLAMP1 `old=190 new=0
  cap=10 d0=0` (evidence/m52a_watch.log:310, :311, :319, :318, :326; same in m51f :212/:219/:220/:227).
  Session 50's "no +0x40 writer fired" was a **log misread**.
- Clamp re-confirmed statically (0x4efee6-0x4eff20): `edx = min(base+0xd0, cap 0x92a370=10)`; if
  `storage ≤ edx` leave it; else event-owner gate `0x4eff02` then `storage := max(0, min(d0, cap))`.
  ⇒ M50b's "200 → 7" (evidence/m50c_watch.log:117) IS this store with d0 = 7 (INFERRED for that round:
  m50c armed no d0 print). Today d0 = 0 ⇒ clamp pins storage to 0.

### Standing from earlier sessions (do not re-derive)
- **Storage writers**: IADD `0x4ef7f6` (`+= d0`, GATED — fired 1× in 2 rounds with d0=0, so not
  unconditional), SPENDA `0x4efee0` (`−= edi`), CLAMP1 `0x4eff20/23`, CONVST `0x4f2d7d` (inside 0x4f26e0,
  a CREDIT `storage += ((pool/esi)·45)/trait`, live +0…+12). Production mineral cost is effectively FREE
  in solo. esi at COMPLET = path residue; pop at COMPLET = pre-completion value.
- **OPEN (was M49a's "index quirk")**: SPENDA's `edi` printed **10** for a record whose sweep-entry index is
  **70** (evidence/m52a_watch.log:311 vs :307). `0x4eaa10` is called 20 bytes earlier at `0x4efec4`. The
  subtrahend's provenance is unresolved → **M52b**.
- `0x4f26e0` = mineral↔energy conversion/income step: our base ALWAYS early-returns at gate `0x4f2705` +
  flag test `0x4f271e` (`ecx=0x20`) and never reaches PASTFLAG (m52a: 146 PASTFLAG / 148 VISIT / 2 FLAGTEST).
  Amount ebx scales with the faction energy pool `0x94d650+p·0x20bc`. Do not re-derive.
- **The sweep never truncates** (M50b): 0x520540 scans all bases, reloads n_bases each iteration, every base
  is visited once per player pass; the year store 0x51f554 fires BETWEEN passes.
- Record identity: **locate by NAME** ("Climactic Research", string at base+0x13) — the array SLIDES
  (idx 70 now, 71 in m50c) and the owner byte changes. Fields: x u16@0, y u16@2, owner@4, pop@6, f18, f1c,
  f20 (transient), f28, f30, **+0x3c progress**, minerals@0x40, 44, 4c, queue@0x50 (transient), 68, 8a/8c
  (facility bitmap, byte-wide groups), c0, **cc@0xcc (per-round progress delta, −3 for us, recomputed)**,
  d0@0xd0 (net mineral income, recomputed every round at 0x4e955d — pokes die), e0, f0, fc@0xfc (+3 energy
  for us), f38 const 0x00dfbe41.
- Income globals (M46): gross 0x745734, upkeep 0x744f28, net 0x7457dc, trade 0x7457d4, food 0x74572c,
  needpct 0x745730. Verified: year 0x985b00, turn 0x985afc, cur 0x985dcc, nb 0x985af4, mask 0x985b10
  (0xff08), solo 0x920434, cap 0x92a370 (10), curbase ptr 0x8f0d60, base array 0x95da10 stride 0x130,
  unit array 0x933278 stride 52, trait record 0x927a7c+p·0x59c, faction records 2095 ints (stride 0x20bc),
  faction int[17] @0x94d694+p·0x20bc (live: p7=4 p5=2 p2=3, ours 0).
- Pane id-printer bp 0x483470: advisories only.

## Static-reading kit
- **Clean 32-bit disassembly, no attach**: `gdb -batch -nx -q -ex "set architecture i386" -ex
  "set disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` (PE maps as file target;
  TracerPid stays 0). Write the dump to `evidence/` then grep it — never paste a whole function. objdump
  `-b binary -m i386:x86-64 -D --adjust-vma=0x400000` misaligns on SEH blocks. Ghidra pseudocode:
  `scripts/fn.py 0xADDR`; index rows: `grep -m1 004ee410 ghidra_out/index.csv`.
- Live memory reads: `/proc/PID/mem` pread (TracerPid 0). Recipe that settled M52a in one call: read
  `0x8f0d60`, walk `0x95da10 + i*0x130` for `i < *(0x985af4)` matching the name at +0x13, then pull
  pop(+6)/+0x3c/+0x40/+0xcc/+0xd0/+0x30/+0x8c plus DAT_0092a290 / 0x92ada8 / 0x92a2ac / 0x92a2b0 /
  0x985b9c / 0x94d694+p·0x20bc and recompute the formula — a static prediction that matches a later bp
  print is the cheapest verification there is.

## Operational kit
- Game: pid via `pgrep -x terran.exe`. Launch if down:
  `cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine explorer /desktop=smac,800x600 terran.exe >/dev/null 2>&1 &`
  then `scripts/m48d_boot.py` (BackSpace clear broken — loop it) or drive manually.
- Preflight: `pgrep -x gdb` empty; `TracerPid:` 0 in `/proc/PID/status`; `sysctl kernel.yama.ptrace_scope`
  must be 0 (resets to 1 on reboot).
- Read-only state: `python3 scripts/smac_state.py --json` or direct `/proc/PID/mem` pread.
- **Armed runs**: `python3 scripts/m51a_drive.py --tag mXX --rounds 2 --budget 1100` (latest template;
  m52a ran clean: 2 rounds, 0 OCR passes, clean detach). It locates our base by NAME, pokes (+0x3c=500,
  +0xcc=1, +0xd0=200, +0x40=200 — d0 poke dies), arms gdb AFTER poking (M33), drives colour-only, SIGINTs
  gdb + kill -CONT. gdb log is block-buffered — read AFTER detach. Run it with a foreground timeout > 600 s
  so the runtime promotes it to a tracked background job with notify-on-complete.
- Template sites (add/remove in GDB_TMPL): PIPE 0x4ef6d0, IGATE 0x4ef7db, IADD 0x4ef7f6, QGATE 0x4ef88b,
  NOQUEUE 0x4ef9b3, ST1C 0x4efae5, PROGDIV 0x4efd49, COMPLET 0x4efe41, SPENDA 0x4efed8 (store 0x4efedd),
  CLAMP1 0x4eff02 (stores 0x4eff20/23), MIRA 0x4eff29, SPENDB 0x4f0ca1, CLAMP2 0x4f0ccb, MIRB 0x4f0cf2,
  QDRAIN 0x4f1e3f, F26E0 0x4f26e0, GATE 0x4f2705, FLAGTEST 0x4f271e, CONVST 0x4f2d7d, RET26E0 0x4f5ae1,
  E410 sites 0x4ee82f (reset store, prints pop/scale/ada8/fac17/f30b) / 0x4ee869 (zero+pop++) /
  0x4ee8c7 (accrual, prints cc), YEAR 0x51f554, PANE 0x483470; HW watchpoints (2 of 4 DR slots):
  `+0x3c` and `+0x40` with `name_at` printing. NO bp on 0x64bfa3 (generic dword-copy loop — fatal hit rate);
  a third watchpoint fails to insert ("too many hardware breakpoints/watchpoints") and detaches with zero hits.
- Pitfalls in force: M33 (poke only TracerPid 0, arm after), gdb-INT leaves inferior stopped → kill -CONT;
  never Escape on title/REALLYQUIT; OCR words ≥4 chars; OK-bar ≥1.2 s after row select; advisor panes
  transient (never key-dismiss); gdb's `$eip` sits just PAST the store; **grep the watch log for the writer
  prefixes before concluding "nothing fired" — session 50 misread its own WP40 hits**; a python driver whose
  argv contains its run tag SIGINTs itself (fixed: pgrep + os.kill skipping os.getpid()); gdb-attached X
  events can drop — re-press keys after arming.
- **COMM OFFICER 3-row variant** ("I have Colonel X on Channel 9…"): row clicks do nothing useful — close it
  with `windowfocus`, `key Down`, 0.4 s, `key Return` (selection opens on row 1). "Display faction leader
  profile" → UNIVERSITY INTELLIGENCE FILES → Escape. Both handlers are in the driver.
- Autosaves: `programs/saves/auto/Alpha Centauri Autosave N.SAV`, mission year = u16 @ file 0x54 (READ before
  trusting the slot; slots rotate). Load recipe: LOAD GAME (610,344) → name box (400,252) → End → 200×
  BackSpace (loop) → `Z:\home\n100\reverse\smac\programs\saves\auto\...` → Return → OK (290,391) →
  ops-director modal row (400,307) → OK (400,362) → Escape. `scripts/m48d_boot.py` automates most of it.

## Milestone options (pick ONE)
- **M52b — what is `edi` at `0x4efedb`? (THE PICK)**
  SPENDA subtracts edi and it printed **10** on a record whose sweep-entry index is **70**
  (evidence/m52a_watch.log:311 vs :307), so M49a's "edi = sweep-entry index" is wrong on this path.
  (a) disassemble `0x4eaa10` (called at 0x4efec4, 20 bytes before the store) and `0x4f5a70`'s edi set-site
  0x4f5aa9, and name which one wins; (b) arm ONE bp at 0x4efed8 printing edi + the return address chain
  (`*(void**$esp)` and `[ebp-0x2c]`) on every hit for our base. Do NOT re-run the +0x40 watchpoint — it is
  answered.
- **Superseded:** M52a is done (session 51). Do not re-derive the 40, the 80 threshold, or the +0x40 writer
  set — all three are measured.
- **Retired premise, do not resurrect:** "`+0x3c`'s writer and the converter gate must be one code path"
  (they are two), and "no +0x40 writer fired in m51f" (it fired twice).
- Later: M50c (base+0xcc −3 source: 0x4eaa10 / 0x4e92c0 / slider UI), M50d (the 2320 +4 energy credit),
  M50e (player idx → faction name via #FACTIONS), M51b (energy-pool store 0x4f2dc4-0x4f2e97), M52c
  (d0 source at 0x4e955d — why ours is 0 while fc(+0xfc) = 3).

## Report style
Findings → SESSION_NOTES.md (dated section) + rewrite NEXT_PROMPT.md; evidence under
`~/reverse/smac/evidence/` (never /tmp); cite log line numbers for every claim; state VERIFIED vs INFERRED;
end with one dated SESSION_NOTES line + the next-prompt pointer.
