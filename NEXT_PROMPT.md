# NEXT_PROMPT — SMAC RE, session 51

Read this file IN FULL first. It is the complete footing: proven facts (do not re-derive),
the operational kit, and the queued milestone options. Do ONE milestone, checkpoint to
`SESSION_NOTES.md` (+ rewrite this file), then STOP.

## First actions
1. `skill_view('smac-cvr-format')` — harness pitfalls + code atlas.
2. `tail -60 ~/reverse/smac/SESSION_NOTES.md` — M51a (session 50) is the latest milestone.
3. Check live state (see kit below): game should be up (pid via `pgrep -x terran.exe`),
   year ≥ 2350, our turn open (cur=3), no gdb attached.

## Footing — mineral economy (M49a + M50a, VERIFIED)
- **Storage writers (all three known)**: (1) IADD 0x4ef7f6 `storage += d0` per round unclamped;
  (2) SPENDA 0x4efee0 `storage −= edi` at every completion (COMPLET 0x4efe41) where **edi = the
  base's SWEEP-ENTRY INDEX** (0x520540 `push ebx` stack arg → 0x4f5a70 `edi:=index` 0x4f5aa9 →
  pipeline never writes edi on the pop-growth path) — an INDEX QUIRK, not a cost (M49a);
  (3) **CONVST 0x4f2d7d** (inside 0x4f26e0) `storage += ((pool/esi)·45)/trait` — a CREDIT
  (M50a, live deltas +0…+12). After SPENDA, event-owner clamp (gate 0x4eff02
  `(1<<owner)&mask`, stores 0x4eff20/23): `storage := max(0, min(d0, cap))`, mask 0x985b10=0xff08,
  cap 0x92a370=10. esi at COMPLET = path residue ((1<<owner)&mask via 0x4e40a0/0x48ee00, = 8 for
  us; facility path: type-record scratch). Pop at COMPLET is always the PRE-completion value.
- **Production mineral cost: effectively FREE in solo** — no cost debit exists in the per-base
  chain (0x4ee410 never touches base+0x40; the 0x4f2750 "cost" read is the item table's tech-id
  slot). The 26-year backlog = storage clamped to 0 ⇒ the index-subtract always takes the
  shortfall branch 4efee4.
- **0x4f26e0 = mineral↔energy conversion/income step** (runs right after 0x4ef6d0 in 0x4f5a70):
  early-return gates 0x4f2705 (event-owner ∧ `~(base+0x38)` bits 0x1a/0x1c — **our base ALWAYS
  returns here**, f30=0x805000 has bit 0x1c) and 0x4f2729 (storage==0). Amount ebx = f(energy
  pool `0x94d650+p·0x82f·4`, queue `base+0x50`, item int1 `\|q\|·0xF0+0x984d44+0x44`, gov/trait
  `0x927a84+p·0x3c`+0x50 (100 ⇒ ×2), 0x985bb8=−1, 0x985aec), clamped `0..min(derived, pool−
  storage)`; event owners skip the energy-side (0x4f2d85); non-event owners also adjust the pool
  (0x4f2dc4-0x4f2e97). Amount scales with the faction ENERGY POOL (AI 192-1080 vs ours 19).
  M44's "minerals→energy ≈1:1" is NOT this function's storage path (own=4 CONVST never fired).
- Base record fields: re-locate by CONTENT (owner byte `+4==3`, name "Climactic Research" —
  array SLIDES). x u16@0, y u16@2, owner@4, pop@6, f18@0x18, f1c@0x1c, **f20@0x20 (transient
  scratch — wild values live)**, f28@0x28, f30@0x30, 3c@0x3c, minerals@0x40, 44@0x44, 4c@0x4c,
  queue@0x50 (transient scratch mid-visit), 68@0x68, 8a/8c@0x8a/0x8c, c0@0xc0, cc@0xcc,
  d0@0xd0 (recomputed every round at 0x4e955d inside 0x4e93f0 — pokes die), e0@0xe0, f0@0xf0,
  fc@0xfc (+2 energy), f38@0x38 const 0x00dfbe41.
- Pipeline chain: 0x4ef6d0 entry → IGATE 0x4ef7db (d0) → IADD 0x4ef7f6 → QGATE 0x4ef88b →
  [0x4efadc store [ebp−0x1c]] → COMPLET 0x4efe41 → SPENDA 0x4efed8 → shortfall 4efee4 → CLAMP1
  0x4eff02 → MIRA 0x4eff29. Facility branch (ebx≥0x40): 0x4efe4a reads [ebp−0x1c] as type-record
  ptr, calls 0x572800 then 0x4e8d60→0x4e78e0→0x4e92c0→0x4e93f0→0x4eaa10 (clobbers edi/esi).
- **Sweep truncation (3rd observation)**: rounds can end the per-base sweep early (21/28/28
  visits) when the YEAR store 0x51f554 fires mid-sweep — our base (visited LAST) is then
  unprocessed for that round (m50a: PIPE n=1..28 all own≠3, poked storage survived). Mechanism
  OPEN (M50b target: 0x520540 loop body 0x5206c2-0x5206fd + 0x51f320 caller ordering).
- Income globals (M46): gross 0x745734, upkeep 0x744f28, net 0x7457dc, trade 0x7457d4, food
  0x74572c, needpct 0x745730. Verified globals: year 0x985b00, turn 0x985afc, cur 0x985dcc,
  nb 0x985af4, mask 0x985b10, solo 0x920434, nrg3 0x953884 (faction stride 0x20bc), led3
  0x953888, cap 0x92a370, curbase ptr 0x8f0d60, base array 0x95da10 stride 0x130, unit array
  0x933278 stride 52. Energy pools: `0x94d650 + p·0x20bc` (live: p4=1080 p7=353 p5=197 p1=192
  p2=45 p6=42 ours=19 p0=10). 0x4e40a0(p,1,−1) = (1<<p)&mask event test (ours=8, live edi/esi
  prints). 0x4eaa10 loops 7× factions writing faction+0xc4 = research pool.
- Pane id-printer bp 0x483470: advisories only (Script confirms don't route through it).

### M50b (session 49): THE SWEEP NEVER TRUNCATES
- `0x520540(player)` scans **all** bases: `edi = 0x95da14` (owner byte at base+4); skip when
  `owner != player`, else `call 0x4f5a70(ebx)`. The tail **reloads eax from `0x985af4` (n_bases)
  every iteration**, so the bound is live.
- Measured (1 round + 2 rounds, 110 visits; `evidence/m50b_watch.log`, `evidence/m50c_watch.log`):
  every pass ends at `last_idx = n_bases-1` (73/74), `nb_entry == nb_now` on all 15 passes, and the
  per-player visit counts sum to exactly `n_bases` (1+7+3+7+9+0+10+37 = 74). **No truncation exists.**
- The old "21/28/28" pattern is a **per-player base count** (p=2 owns 37, p=1 owns 10), not an early stop.
- The year store `0x51f554` fires **between** passes: `mid_p=7`, `mid_idx=73/74` — after the last
  player's pass completes, before p=0 of the next year. It never interrupts a pass.
- Our base (idx 71, "Climactic Research") **is visited** every round, as p=2's base (`ours=1` at
  `0x5206d3`). Between poke and visit `+0x40` went 200→7 and `+0x3c` 500→1 ⇒ per-base work DID run
  on it. M50a's "poke survived / ours unvisited" does **not** reproduce in this ownership state.
- OPEN: the owner byte read 3 in M50a, 2 in M50b (capture? record reuse?). Resolve before trusting
  either round's ownership claim.

### M51a (session 50): the writer has a name — FUN_004ee410
- `FUN_004ee410` (0x4ee410, 2076 bytes) owns our base's `+0x3c`: `0x4ee82f` sets it to **40** and
  `0x4ee8c7` (`mov [edi+0x3c],esi`) drops it by `cc` each round — observed 500 → 40 → 37 → 34 → 31.
- The converter gate is NOT our path: our base hits `0x4f2705` and the flag test `0x4f271e`
  (`ecx=0x20`) and never reaches PASTFLAG (197 gates vs 194 past-flag, zero PASTFLAG with `ours=1`).
  M50a was right about the early return; M50b was right that the field still changes. Different code.
- Record identity: VISIT prints the base NAME every time (idx moved 71 → 70 between sessions). Never
  key a conclusion on a bare index; the array slides.
- Still unknown: what makes 40 at `0x4ee82f` (disassemble from the function entry 0x4ee410, not from
  a mid-instruction address), and who writes `+0x40` (200 → 7 seen in M50b; no writer fired here).

## Static-reading kit
- **Clean 32-bit disassembly, no attach**: `gdb -batch -nx -q -ex "set architecture i386" -ex
  "set disassembly-flavor intel" -ex "file programs/terran.exe" -ex "x/Ni 0xADDR"` (PE maps as
  file target; TracerPid stays 0). objdump `-b binary -m i386:x86-64 -D --adjust-vma=0x400000`
  works but misaligns on SEH blocks. Ghidra corpus `scripts/fn.py 0xADDR` for pseudocode;
  register-level truth needs the gdb disasm.
- Live memory reads: `/proc/PID/mem` pread (TracerPid 0), e.g. item table 0x984d48 stride 0xF0,
  trait record `0x927a7c + p·0x59c`, energy pools above.

## Operational kit
- Game: pid via `pgrep -x terran.exe`. Launch if down:
  `cd ~/reverse/smac/programs && WINEPREFIX=$HOME/.wine-smac32 DISPLAY=:99 WINEDLLOVERRIDES='mscoree,msxml=' nohup ~/tools/wine-10.20-staging-tkg-x86/bin/wine explorer /desktop=smac,800x600 terran.exe >/dev/null 2>&1 &`
  then `scripts/m48d_boot.py` (BackSpace clear broken — loop it) or drive manually.
- Preflight: `pgrep -x gdb` empty; `TracerPid:` 0 in `/proc/PID/status`; `sysctl
  kernel.yama.ptrace_scope` must be 0.
- Read-only state: `python3 scripts/smac_state.py --json` or direct `/proc/PID/mem` pread.
- **Armed runs**: `python3 scripts/m50a_drive.py --tag mXX --rounds 1 --budget 1100` (latest
  template: m49a's extended COMPLET print + ST1C + self-pkill fix, PLUS F26E0 entry 0x4f26e0 /
  CONVST store 0x4f2d7d / RET26E0 0x4f5ae1 bps with own counters). It re-locates our base by
  content, pokes (+0x3c=500, +0xcc=1, +0xd0=200, +0x40=200 — skip d0, it dies), arms gdb AFTER
  poking (M33), drives colour-only, SIGINT gdb + kill -CONT. gdb log is block-buffered — read
  AFTER detach. A round takes ~1-10 min (AI pane chains; COMM 3-row variant below).
- Sites available in the template (add/remove in GDB_TMPL): PIPE 0x4ef6d0, IGATE 0x4ef7db,
  IADD 0x4ef7f6, QGATE 0x4ef88b, NOQUEUE 0x4ef9b3, ST1C 0x4efae5, PROGDIV 0x4efd49,
  COMPLET 0x4efe41, SPENDA 0x4efed8, CLAMP1 0x4eff02, MIRA 0x4eff29, SPENDB 0x4f0ca1,
  CLAMP2 0x4f0ccb, MIRB 0x4f0cf2, QDRAIN 0x4f1e3f, F26E0 0x4f26e0, CONVST 0x4f2d7d,
  RET26E0 0x4f5ae1, YEAR 0x51f554, PANE 0x483470; WPs: minerals, queue, d0, energy3. NO bp on
  0x64bfa3 (generic dword-copy loop — fatal hit rate).
- Pitfalls in force: M33 (poke only TracerPid 0, arm after), gdb-INT leaves inferior stopped →
  kill -CONT; never Escape on title/REALLYQUIT; OCR words ≥4 chars; OK-bar ≥1.2 s after row
  select; advisor panes transient (never key-dismiss); `pkill -f` bracket the pattern AND
  exclude your own pid (python driver whose argv contains the tag SIGINTs itself — fixed in
  m49a/m50a drivers); gdb-attached X events can drop — re-press keys after arming.
- **COMM OFFICER 3-row variant** ("Yes, switch to main viewscreen." / "No, close the channel."
  / "Display faction leader profile."): row-click (bar_y−25) can select profile → UNIVERSITY
  INTELLIGENCE FILES table, CLOSE/DATALINKS bars y≈345-360 (outside find_ok_bar 430-520); drains
  via rightmost-bar row+bar cycle but slowly (~8 min / 43 OCR passes once). Faster: OCR the row
  y and click directly, or click bar_y−25 twice before the bar. TOUR hint: Continue (325,585).
  Social Engineering: OK (240,368) commits.
- Autosaves: `~/reverse/smac/programs/saves/auto/Alpha Centauri Autosave N.SAV`, mission year =
  u16 @ file 0x54 (READ before trusting slot number; slots rotate in place). Load: LOAD GAME
  (610,344) → name box (400,252) → End → 200×BackSpace (loop; `--repeat` fails) → type
  `Z:\home\n100\reverse\smac\programs\saves\auto\...` → Return → confirm OK (290,391) →
  ops-director modal on base screen: row (400,307) → OK (400,362) → Escape. `scripts/m48d_boot.py`
  automates most of it; verify "Mission Year" in the confirm pane OCR.

## Milestone options (pick ONE)
- **M52a — what makes 40, and who owns +0x40? (THE PICK)**
  Two concrete measurements in one round: (a) disassemble `FUN_004ee410` **from 0x4ee410** and name
  the expression behind `esi` at `0x4ee82f` (the `mov esi,0x19` / `[base+6]` pop arithmetic is the
  thread to pull); (b) put ONE hardware watchpoint on our base's `+0x40` and print eip + name on every
  hit, to find the 200 → 7 writer that M50b saw but M51a missed. Budget the four DR registers: one
  watchpoint on +0x40, keep `0x4ee8c7`/`0x4ee82f` as software breakpoints.
- **Superseded:** M51a is done (session 50). Do not re-derive the gate early-return — it is measured.
- **Retired premise, do not resurrect:** "the gate and the field rewrite must be the same code path,
  so one of them is wrong." They are different code (`FUN_004ee410` vs `FUN_004f26e0`) and both are
  correct; the contradiction was an artifact of assuming a single writer.
- **Do not re-run M50b** (done, session 49) and do not re-derive M50a's truncation premise — it is
  falsified; the sweep is complete every round.
- Later: M50c (base+0xcc production-rate source: 0x4eaa10 / 0x4e92c0 / slider UI), M50d (the 2320
  +4 energy credit), M50e (player idx → faction name via #FACTIONS), M51b (energy-pool store on
  0x4f2dc4-0x4f2e97, closes M44's anti-correlation).

## Report style
Findings → SESSION_NOTES.md (dated section) + rewrite NEXT_PROMPT.md; evidence under
`~/reverse/smac/evidence/` (never /tmp); cite log line numbers for every claim; state
VERIFIED vs INFERRED; end with one dated SESSION_NOTES line + the next-prompt pointer.
