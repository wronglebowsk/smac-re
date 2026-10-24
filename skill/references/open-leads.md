<!-- Moved verbatim from SKILL.md (M53Q1, 2026-10-24) to keep the always-loaded file small. -->

## Still open (leads)

M38 core
(still true): issue cost `0x4cc7b0` = `(|elev−3|+2)²` (9@elev4, 16@elev5, 25@elev6 > our 15
energy; economy-gated); M37 core: execute chain + multi-turn accumulator. `0x2101` queue still no solo consumer. `~/reverse/smac/` is durable. Execution chain + terraform engine + tile/tech-gate facts: `references/terraforming-order-path.md`.
Selection rules hold: HOLDed (order 2) units are not cycle candidates; empty cycle
**auto-ends the turn**; a map click selects a unit **and** sets orders mode `0x91b5b8=1`;
`Tab` re-opens CUSTOMIZE mid-game. UI: **ENDOFTURN1** pane → **Return** (never Escape); Escape
on a bare HUD opens **REALLYQUIT** (oops row y≈260, OK ≈307) — `answer_confirm` CANNOT service
it (`find_yes_row` scans y 160–220, defaults to 196 = pane artwork); use
`scripts/m37_recover.py` (oops row then OK +47 px). Harnesses: `scripts/m37_exec41.gdb` (11 bps:
REFRESH/ORDEREXEC/TERRAFEXEC/CHECK/NOTYET/CANCEL/COMPLETE/RAISE/LOWER/SETELEV/MASKSET) +
`scripts/m37_exec41.py` (multi-round completion runner — **must click TURN COMPLETE every round**
on a bare HUD, else stalls; snapshots `+37`/elev; REALLYQUIT special-case),
`scripts/m37_recover.py`, plus the M35/M36 set (`m36_store.gdb`/`m36_dismiss.py`,
`m36_exec.gdb`/`m36_exec.py`, `m35_pay.gdb`/`m35_paypicker.py`, `m35_gate.py`,
`m33_scan.py`/`m33_state.py`); **M38: `scripts/m38_issue.gdb` (34 bps, full issue chain incl.
PACTCHK/REFUND/DIPLO/EPILOGUE) + `scripts/m38_issue.py`** — selection recipe (poke `+40=255`
on other own order-0 units → `Escape` → pump auto-selects the Former), `]`, pane servicing,
`COST 16 → DEBIT 31→15 → STORE 0x14 → BCAST` live; elev-5 footprint = **49 tiles 7×7** (81 =
elev-6's 9×9), diplomacy branch armed **silent** (no foreign tiles); completion `m38run2` →
`SETELEV new=6` year 2293, re-erosion lifted 8 neighbours 4→5; energy 15, income ≈ upkeep ≈
+0/turn ⇒ next terraform (25) economy-gated. Depth:
`references/terraforming-order-path.md` (the M39 Road-mode proof, thresholds and keys duplicate the footing paragraph above). Next
(M40 DONE, live 2026-10-22): MagTube remap + first TECHFAIL — `r` on a roaded tile: TERRAF 0x5
→ remap rewrites the mode arg inside `0x4d44d0` (TECHCHK sees 0x6; gated on cap table `0x6938e8`
idx `mode*8+tile-seafloor`, MagTube land 18/sea −2 ⇒ land-only) → gate 0 → TECHFAIL `0x4d486e` →
**mode-specific advisory dispatch 6→HASROAD / 1→HASFARM / else NOTUNTILTECH** (HASROAD text
substitutes $TECH0 → tech 18 "Monopole Magnets" live via `0x5a69f0` (tech names at
`0x92fdb4+id*44`) + `0x626634` slot table `0x99a01c`; scratch buffers `0x997120`/`0x99a01c` are
NOT state); rejected cleanly — the runner's STORE timeout IS the expected reject terminal state.
Cap table is the gate source (terrain `+18` garbage 527 for cheap modes); MagTube table k=6:
maskSET 0x8, work 3. **As of M41 (live, 2026-10-22): MagTube third mode proven end-to-end**
(`evidence/m41a_*`, `m41b_*`): unlock poke byte `0x985c1c+18 |= 0x08` (TracerPid 0 first) → `r` on
the roaded (45,7) → `TECHCHK mode=0x6 unlocked=1` (gate-pass path = NO advisory, straight to
AFTERLATCH/STORE) → **STORE 0x0a — the STORE writes the REWRITTEN mode** → 4 execs 2295→2298
(`CHECK 2/8→4/8→6/8→8/8`) → `COMPLETE mode=6` → tile mask **0x108006→0x10800e** (magtube bit
0x8), elev untouched (mask swap only), energy 15 flat. **Threshold @ elev 6 = 8 = 2×3+2 ⇒ case-5/6
elev bump is +2 FLAT, not ×2** (road 2→4 fits the same rule).
M42–M44 (same session, 2026-10-22): generic NOTUNTILTECH proven live (`n` →
TECHFAIL → ADVISOR/PANE NOTUNTILTECH; $TECH0 + $TERRAFORMTYPE6 slots closed; tech record +0 =
display-name POINTER, +4 = short token; op-name table `0x94d2f8` = 14 × (land, sea, key-char STRING)
stride 12 — k=8 is **Airbase**, k=9 Sensor Array). M43: base `+4`/`+5` IS the owner player index
(identity, 167/167) — **we own ZERO bases**, all our units `home_base=0xffff`, ~45 orphan-border
tiles; `0x4e3700` works fine (Ghidra short* math), inert for us. M44 (economy idle run): **our income is 0 AND upkeep is
never charged to energy — energy flat 15 over 12 rounds (2304→2315)**, the HUD agrees (Gross
Income/Total Costs/NET INCOME all 0/turn) ⇒ the 25-cost elev-6 raise is unpayable until a base
exists; AI rates/round Δenergy {1:-1.4 2:-1.3 4:+10.9 5:-0.5 6:+5.3 7:-0.9}, Δminerals {1:+2.3
2:+8.3 4:-11.2 5:-1.9 6:+31.2 7:+1.1} (player 4's near-exact anti-correlation ⇒ unspent base minerals
→ energy ≈1:1, O); Four reusable
corrections: (1) **Council/PROPOSAL panes block the pump** (bar-finding: see the PROPOSAL-pane and
colour-driver bullets above). (2) runtime tile record == the map file's two 22-B cells byte-exact; accessors (`0x582ed0`,
`0x5831a0`) are parity-blind on `*(int*)0x92ae14 + (40*y + x>>1)*0x2c` (+0 elev, +8 mask shared by
the pair); a second mask-shaped dword at +0x18 is open. (3) tile **mask bit 0x2 = a unit standing on the
record** (3193/3200, 0 false negatives); full vocabulary from table × op names (farm 0x8000, enricher
0x80000, mine 0x10, solar 0x40, forest 0x200000, road 0x4, magtube 0x8, bunker 0x800, airbase 0x40000,
sensor 0x80000000, fungus 0x20, condenser 0x400000, echelon 0x8000000). (4) **unit type-record base
is 0x98ad88** (name +0[34], ability +32 = 0x98ada8, domain +36 = 0x98adac, plan +42 = 0x98adb2 (the alpha Plan byte — see the M53b type-record bullet; "class" was a misnomer) — the
standing ABSOLUTE addresses are right, but treating 0x98ada8 as the record base pairs each class byte
with the NEXT record's name; type 0 Colony Pod (cls 8), 1 Formers (cls 9), 193 Scout Rover, 195 Laser
Squad; ≥196 runtime types vs 15 alpha `#UNITS` rows. Also **autosaves rotate over all 8 slots**
(30/20/10 every 10 y, then 5/4/3/2/1 yearly) — the "slot 2 = 2198" load note is stale; read the u16 at
file `0x54`. 

- **Poking a unit's order fields does not issue the order.** `+17 = 0x18, +20 = dest_x, +28 = dest_y`
poked via `/proc/<pid>/mem` (writable, no tracer) survives a full turn with the unit unmoved: the
executor consumes orders through its own dispatch path, so order fields are outputs, not inputs (a gdb
`call` into the issuer behaves the same — see the last-resort rule above). M53m refinement: order fields
ARE inputs to the ECONOMY sweep — a poked order 3 (Convoy) on a plan-10 type persisted 4 rounds and
drove production accumulation while the movement executor ignored the route-less convoy. Unit slots
SHUFFLE (array compaction) mid-run: locate records by content (faction byte@14), restore pokes at the
record's NEW home.

- **Turn cycle: solved as a harness problem (~100 turns unattended; `references/wine-headless-harness.md`).**
  It was never a game hang — every observed stall was a blocking UI element (units-not-moved confirm,
  OPERATIONS DIRECTOR speech, NETFLASH, tech-breakthrough screen, base screen, Secret Project movie) that a
  one-shot click-then-wait loop cannot answer. Chain of netcode findings:
  (`~/reverse/smac/dplay_solo.md`, `turn_stall.md`): (M3) solo opens NO DirectPlay session, so DP shims
  (dgVoodoo2/nGage/glsmac) can't fix anything; (M5) the idle main thread is a normal yielding PeekMessage
  pump, not a clock-spin or deadlock; (M6b/M7/M8) solo never calls the netcode packet builder `FUN_00584010`
  nor dispatcher `FUN_0052bce0`, **nor the MP end-turn machinery** `FUN_00522240` ("Clearing turn semaphore",
  DONE TURN 0x8301) → `FUN_00521ee0` (end-of-turn semaphore wait loop) → `FUN_00527ca0` (its in-loop pump):
  zero hits across 7 completed turns. **Solo's turn advance runs under `FUN_0050f420`/`FUN_0050ef60` →
  `FUN_0051e700`** (hot: 0 hits idle, ~220–560/s while a turn resolves; drives the `DAT_0091f69x` turn
  semaphore directly, no packets). The old "turn stall" = periodic MODAL dialogs and full-screen interruptions (ABOUT RESEARCH, OPERATIONS
  DIRECTOR speech, NETFLASH, tech breakthrough, base screen, Secret Project movie) blocking the TURN
  COMPLETE click while the game idles in its pump. Next: make the driver give unit/base orders
  (Script.txt-driven) so the AI actually plays; decompile `FUN_0051e700` only if the counters it drives
  stop tracking.
- **Diagnosing a Wine game stall (reusable method)**: sample per-thread wait-state via
  `/proc/<pid>/task/<tid>/{stat,syscall,wchan}` (state=R + climbing utime ⇒ busy-loop, not blocked);
  `gdb -batch -p <pid> -ex 'thread apply all bt' -ex 'info proc mappings'` — but **Wine's stack won't
  unwind past ntdll** (bt stops at ~2 frames: `__kernel_vsyscall` → a libc poll/select wrapper), so use
  gdb `info registers eip` sampling as a poor-man's profiler and map a hot terran.exe `$pc` to a Ghidra
  `FUN_` by subtracting terran.exe's runtime base from `info proc mappings`. Breakpoints on
  `GetTickCount`/`QueryPerformanceCounter`/`timeGetTime`/`GetMessage` reveal what the loop polls.
  `WINEDEBUG=+<dll>` trace helps for some DLLs (`+dplayx` works; `+timer` emitted nothing here). Detail:
  `references/wine-runnability.md`, `~/reverse/smac/turn_stall.md`.
- AI decision logic: diplomacy hub `FUN_00546800` (3924 lines) vs UI plumbing;
  psi-meter gate `FUN_004d6fb0`; turn upkeep `FUN_00520e70`; the host-side
  action-exec branch of dispatcher `FUN_0052bce0` (case 0x4404) is the single
  source of truth for action rules — server and solo alike.
- 0x4040400/0x4050000 cvr chunk handlers exist in exe but in no shipped file.
- Caviar voxel rasterizer exe-verification (27-dir table, normal decoder,
  shade-table light levels) still wiki/corpus-level.

### Parked (background probes, NOT a queue) — M53 production-vector leftovers
Closed as a model in M53t (`~/reverse/smac/evidence/m53t_fold.md`, 74/76 exact on the pre-drive
dump). Reopen only if a milestone needs the bit-exact vector; each item is a probe, not a milestone:
- idx 6 (+2 over) and idx 51 (1 short): the two-pass `FUN_004f5a70` path (`[0x985afc] > 1` →
  `4e8d60/4e78e0/4e92c0/4e93f0/4eaa10` run twice with `[0x8f0d64]=1`). Probe: hw watchpoint at
  `0x4eac57` logging (idx, other, k, s) + a pass counter at `0x4f5b2c`, over one driven turn.
- consumers of `DAT_008f0d40` (written UNGATED at 0x4eac27) and of the mirror share `0x8f0c94`.
- `unit+24/25` + `unit+38` semantics; `base+0x84` nibble meaning; `DAT_008f0cc8` consumer; who sets
  `+0xe0`; byte@5 meaning; `turn_flags` bit 16; the bit-8 live-table disagreement at tile (45,9);
  `c80_end != stored d80` on idx 24/35; why pop-drift is fac-2-only; who writes the seed dwords
  (`faction+0x2e20`); the 417ee0 UI row-loop behind the 13x; M50c-e, M51b.
