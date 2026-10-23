# Session notes archive — sessions 28-42

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 28 (2026-10-21) — M28: the click-to-move gate is a pane mode, not a gesture
- Came in wanting click-to-destination (C2). Answer found instead: `FUN_00476580` writes order `+17 = 0x18`
  **only** when `[this+0x1ef4c] == &DAT_0091cae4` (map-pane mode 9). `this = [0x7cdecc] = 0x8f79e0`; live on the
  HUD that pointer is **0**, so every left click falls into the base/`DESTTRIAD` branch and issues nothing.
- Live proof: bps on the three stores `0x476ac7/0x476bae/0x476c39` + the three early returns
  `0x47674d/0x476778/0x4767ab`; clicks at (480,250) and (470,300) → `MAPH p1=0x1e0 p2=0xfa p3=0 this=0x8f79e0
  wmode=0`, zero store hits, zero early-return hits (`evidence/m28_gates.log`, `m28_gates2.log`).
- Pane mode table is `&DAT_0091c958 + idx*0x2c` set by `FUN_0050ba00/90`; corpus callers pass 8/0xb/10 only,
  so mode 9's setter is unattributed = the next lead.
- Correction logged: `FUN_004d6fb0(unit,0x18,flag)` (order-menu `0x67`; key `j` = case 0x6a) targets a
  **base** tile, not an arbitrary tile. `FUN_00512450` is the order-menu command dispatcher (0x42..0x73).
- Shift+arrow `0x19` needs an order-menu context (`local_28 != 0`), so it can't be driven from a bare HUD.
- Tried and rejected: bottom action-bar clicks (mode stays 0), plain right-click on map centre (no menu; an
  earlier right-click pair opened a DISBAND confirm — Escape cancelled it, no unit lost), 'j' (base move).
- New tools: `scripts/m28_probe.gdb` (gate + store bps), `scripts/m28_order.gdb` (order/watchpoint variant),
  `scripts/m28_click.sh X Y LOG [GDBFILE]`. Evidence: `evidence/m28_clickgate.txt`.
- Left running: pid 914079, year **2201** (advanced during the session's key presses), our turn, HUD clean, TracerPid 0.

## Session 29 (2026-10-21) — M29: state-driven turn driver, 11/11 turns
- Chased the click-to-destination gate one step further: mode 9 is chosen in `FUN_0050a770` (0x50a770) as
  `Ctrl held ∧ 0x91b5b8 == 0 ∧ 0x91b6fc == 0`, then copied to `[this+0x1ef4c]`; live it never fires because
  `DAT_0068d84c` (active pane index) is **-1** — the pointer never registers as "inside a pane" under xdotool.
  Left as the open lead; documented in `turn_driver.md` §M28 + `NAMED.md`.
- Delivered instead: **turn-driver hardening**. `service_turn` now reads `player`/`cur_player`/`turn_flags`
  each loop; during the AI phase it only services modals (`Return` for DATALINKS/PSI/event pages, one
  `Escape` for OPERATIONS DIRECTOR / base panes) and never clicks TURN COMPLETE.
- Proof: `evidence/m29_3turn.log` 2202→2205, `evidence/m29_8turn.log` 2205→2213 — 11/11 turns, 0 stalls,
  7.4–12.9 s each; turn 5 hit an AI-phase CHIEF PLANETOLOGIST popup and still flipped in 12.3 s.
- Also learned: repeated Escape/Space presses can advance the year on their own (2199→2201→2202) — the turn
  loop is not the only way to flip a year; always re-read `year` before attributing an advance to the driver.
- Left running: pid 914079, year 2213, our turn.

## Session 30 (2026-10-21) — M30: the turn loop model, traced for 20 turns
- New tool `scripts/turn_trace.py`: samples year/cur_player/turn_flags/n_bases every 0.2 s while the driver
  runs, logs only changes, prints a per-year player sequence.
- Ran 20 turns, 2213→2233, **20/20 OK**, 201.2 s total. Model: our phase = `tf==0 ∧ cur==player(3)`; TURN
  COMPLETE sets `tf|=2` and the engine walks the AI factions through `cur_player` (observed 0,1,2,4,5,6,7 —
  never 3); year increments once per complete cycle. AI phases = 34.9 s (17 %); the rest is our OCR/click loop.
- Artifacts: `evidence/m30_turn_trace.jsonl` (67 changes), `evidence/m30_summary.txt`,
  `evidence/trace_20261021_131002.jsonl`.
- Side discovery: the base array (51 records now) has **no faction-3 bases** — counts are {1:10, 2:13, 4:5,
  5:8, 6:7, 7:8}. The human faction in this save owns zero bases (units only), so C3 (base economy) cannot use
  the player's own base; it would have to model an AI base. Faction byte is **+4 (byte, not u32)**; +1-based
  "founding order" byte at +5.
- Left running: pid 914079, year 2233.

## Session 31 (2026-10-21) — M31: base record map v1 (pop, growth, minerals)
- New tool `scripts/base_trace.py`: snapshots the whole base array every year-change while the driver runs,
  then diffs u16 lanes of a tracked base. Two runs: 2233→2243 and 2243→2251 (18 turns, all OK).
- **Index is not identity**: base records slide in the array — tracking index 0 silently became a different
  base, index 1 jumped three fields at once. Track by the name at +19.
- **Layout corrected**: faction is the byte at **+5**, flag at +4 (u16 = `flag | faction<<8`); earlier docs
  said "faction at +4". Also named: +6 population (3–7), +7 growth countdown (6→0 one per year), +60 per-base
  turn counter, **+64 mineral accumulator** (mirrored at +152 in all 62 bases).
- **Measured**: Gaia's Landing minerals ≈5–10/turn with resets 54→5 (quarter carryover) and 73→0 (U.N. HQ
  ≈6–8/turn). First live base-economy numbers.
- **Negative result worth keeping**: our own base changed hands at 2239 (faction 3 → 6) and we now own **zero**
  bases; also only 5/152 lanes moved over 11 years for a quiet base → the record is base *state*, not the
  per-tile accounting.
- Left running: pid 914079, year 2251.

## Session 32 (2026-10-21) — M32: the order menu map, live-verified 21/21 keys
- New tool pair: `scripts/m32_keys.gdb` (29 entry breakpoints: key router, order dispatcher, all 20
  order setters, executor/SETTILE/ACT/ATTACK/pane-mode setters) + `scripts/m32_run.sh`
  (`M32_KEYS="…"` presses keys with per-key unit-record snapshots). Deliverable: **`ORDERS.md`**.
- **Key model proven live**: `FUN_00512b40(char, VK|modifiers)`; dispatcher receives
  `(char, tolower(char), VK|flags)` — `FUN_0064d300` = tolower (M→0x6d, G→0x67); numpad VKs
  0x60–0x69 are the direction cluster (M24's "b c d f g h i" was a VK misread); Shift = bit 16,
  Ctrl = bit 17; menu rows arrive as `(menu<<8)|char` in param_3.
- **`FUN_004d44d0(unit, mode)` = issue_terraform_order**: mode = alpha.txt `#TERRAIN` index
  (`data/alpha.json` has all 20 rows + hotkey strings), order = **mode+4**; Former-class gate
  (`DAT_0098adb2[type*52] == 9`); payment debits **`DAT_0094d650[player*0x82f]`** (faction
  energy — first live address); rewrites 5→6 (Road→MagTube), 0→1, 0→0xa. Modes 0,2,3,5,7,8,9,
  0xc,0xd,0xe,0xf,0x10,0x11,0x12 all fired with predicted args.
- Named orders: `h` HOLD 2 (end-to-end: rec56 order 0→2), `l` Sentry 1 (`FUN_005ab420`), `o`
  Sensor/Convoy 3, `g` move-to-base 0x18, `G` join-base (`+46` = base idx), `U` unload, `r` Road,
  `d` bombard (`FUN_004d6100`), `p` waypoints+mode 8, menu 'R'/'T' → 0x1b/0x1c road/tube-to-base
  (`+20` = base index), menu 'D' designate (`+4 ^= 0x80`), 0x30055 give-unit, 0x20055 upgrade.
- **`/` = clear + EXPLORE** (walks toward unexplored: `EXEC 56 dir=7 mode=3` → (43,9)); run 1
  unit 57 explored onto an **alien artifact** (42,12) → OPERATIONS DIRECTOR modal.
- **Modal = key sink, mechanism found**: while a modal is up the pump never calls
  `FUN_00512b40` — 19 keys after the modal produced zero hits. Check screen class first.
- Left running: pid 914079, year 2251, our turn, HUD clean, TracerPid 0; rec56 exploring at
  (43,9) (mp=3), rec57 on the artifact (42,12) (order 0x18, done), rec58 selected at (43,11).

## Session 33 (2026-10-21) — M33: the driver issues a real order (C2 closes)

- **C2 gate met**: `smac_play.py --order f` pokes `0x91b5bc`, presses `f`; the game's own
  chain fires (`KEY 0x66/0x46` → `DISP 0x66/0x66/0x46` → `TERRAF idx=53 mode=0` =
  `FUN_004d44d0`) and unit `+17` 0→**4** (Farm). The order byte **persisted across two
  turn advances (2252→2254) and a compaction slide (rec53→52)** — state reader only.
  Proof: `evidence/m33_try5.log`, `m33_turns.jsonl`, `m33_final_pre/post.json`.
- Order-store tail asm-pinned: store `0x4d5bbf` (`+17 = mode+4`), broadcast `0x4d5bc6`,
  TERRAPAY pane `0x4d55a8` (blocks inside the setter), energy debit `0x4d561a`
  (`0x94d650[player*0x82f]`); Farm/Road/Sensor **defer payment** (no pane, energy flat).
  Harness: `scripts/m33_order.gdb` (7 bps) + `scripts/m33_run.sh`; readers
  `scripts/m33_scan.py` (units/classes/energy), `scripts/m33_state.py` (pre/post JSON).
- Tile layout pinned: `0x92ae14 + (40*y + x>>1)*0x2c`, height `+0>>5` (Elev ≈ h*~100),
  mask dword `+8` (base bit 0, road 0x10, farm 0x20, fungus 0x8000).
- **Pitfalls (new)**: (1) /proc/pid/mem pokes are ghosts while gdb is attached — poke
  before arming, verify after CONT; (2) selection is game-owned — pokes get
  re-validated/replaced by the cycle within a frame; press the key immediately after the
  poke (only config that landed); (3) advisor panes are transient (1–2 s) and swallow the
  next input event (echo `0x20011`) — rejections look like dropped keys; (4) pixel↔tile
  mapping ≠ naive lattice — calibrate via the HUD tile-info panel, not formula.
- **Open (M34)**: the Farm order never executed (cycle skips already-moved/order units;
  Space ran the cycle's unit, `SOLOWRAP idx=<cycle>`), so the tile improvement + energy
  debit are still unobserved. Next: get the order onto a unit the cycle selects (fresh
  turn / native PICKUNIT click-select) and watch `+8` + energy.
- Left running: pid 914079, year **2254**, our turn, HUD clean, TracerPid 0; Former rec52
  (45,11) carries the driver's Farm order (byte 4); rec56/57 still exploring.

## Session 34 (2026-10-21) — M34: the execution-trigger hunt (orders cancel at end-of-turn)
- **Headline negative, well-evidenced:** a Farm order issued through the game's own selection
  (HOLD-walked cycle 50→233→46, then `f` → `TERRAF idx=46`, order byte 4) **clears at the
  end-of-turn boundary with no tile improvement and no energy debit** (40→40;
  `evidence/m34v6_run1_watch.json`). C2's "improvement appears" half is still unobserved.
- **Space IS the execute key (static H):** `FUN_00512450 case 0x20 → FUN_004d1e90(sel)` →
  can-act → `FUN_00529090(u,-1,0)` → solo `FUN_00585720(u, 0x8-sentinel, 3)`; never caught live
  (panes swallow the follow-up key; selection unsteerable under a tracer).
- **Eligibility remap explains the (45,11) rejections:** Farm on `tile+8&0x20 ∧ terr≥4` remaps
  mode 0→0xa; mode 0xa needs unit ability `0x2000` (plain Former lacks it) → picker branch →
  HASFARM advisor abort **before the store** (`m34_try2_gdb.log` matches the signature 5/5).
- **Pitfalls paid:** (1) `/proc/pid/mem` WRITES are dead while a tracer is attached (try3 proof:
  poked sel=46, TERRAF hit idx=50); (2) gdb bp **conditions must cast** `*(int *)($esp+4)` —
  bare `$esp[1]` throws "generic pointer" at first hit and kills the batch script (try1, v7_run1);
  (3) selection is fully game-owned: idle pump + Return/plus/Tab never move it; only a completed
  action (HOLD) advances the cycle; (4) **retract** M33's tile-mask reading at (45,11)/(45,7) —
  tile record content proved unstable across snapshots (`0x20ff…` ↔ all-zero at the same address).
- Tools: `scripts/m34_exec.gdb`+`m34_run.sh`, `scripts/m34_chain.gdb`+`m34_chase.sh` (12-bps
  store→bcast→enqueue→drain→dispatch→executor chain watch), `scripts/m34_exec_watch.py`,
  `scripts/m34_cycle_issue.py` (the HOLD-walk that landed the order). Docs: `turn_driver.md`
  §M34, `NAMED.md` M34 block, `MILESTONES.md` C2 addendum.
- Left running: pid 914079, year **2266**, our turn, sel=-1, pending=1, TracerPid 0; Former rec44
  at (45,7) order 2 (HOLD); all survivors HOLDed/explored; energy 40. Next (M35): catch the
  picker answering *inside* the setter (OCR the pane, click "Expend", never blind Return) or the
  Space chain in a pane-free window — `scripts/m34_chain.gdb` is armed for it.

## Session 35 (2026-10-21) — M35: the terraform pay picker caught and answered (backfilled note)

Detail §M35. Pay path live (EnvEcon poked): TERRACOST 9 → picker → DEBIT 40→31 synchronous →
TERRAFORM pane; **no STORE** — the setter left through a footprint-pass exit; tile-base pointer
`0x92ae14` correction landed. Left: pid 914079, pane open, order 0, energy 31.

## Session 36 (2026-10-21) — M36: no refuser — the tutor pane ate M35; the order is STORED; execution is the new wall

- **The "refuser" was the one-time TERRAFORM tutor pane.** `0x4d58a4 call 0x4c2be0(0x800)` is a
  once-per-game solo latch; the first raise attempt shows the tutor via the **blocking**
  `call 0x48ef40` at 0x4d58c6. The setter parks *above* `STORE` until the pane is dismissed
  (OK at (400,408)) — M35's harness killed gdb while it was open, so "no STORE, no refund,
  no failure pane" was just a frozen setter. Preflight screenshot `m36_screen0.png` caught it.
- **Store tail caught live** (`m36v1_gdb.log`): `PANERET → AFTERLATCH(mode 0x10 skips the
  terrain gate) → LOCKCHK(0x91f718=0) → LOCKRET eax=0 (0x528930 = pass-through in solo) →
  STORE +17 = 0x14 → BCAST → ENQ q=17 idx=41`. No double-debit (energy stays 31).
- **Footprint pass decoded**: raise ladder `0x678e08 = [−13,−14,−15,1,9,25,49,81][height+1]`
  (elev 4 ⇒ 5×5 = 25 tiles), lower `0x678e18`; x wraps, off-map tiles skipped; foreign-owned
  tile + relation&7 ⇒ `0x555030` pact = instant refuse / treaty-truce confirm; refuse ⇒ refund
  blocks `0x4d58dc`/`0x4d59c7`. `0x4e3b50` = tile border-owner query. `0x582ed0` = tile mask set/clear.
- **New wall: execution.** `DRAIN 0x5262e0`/`DISP 0x52bce0` never fire in solo (3 rounds — the
  enqueued 0x2101 events have no solo consumer). Probe round 2272→2273: executor `0x585720(unit,
  dir, 3)` fired **183×, zero for unit 41** (`m36_execprobe_gdb.log`) — the turn machinery filters
  the ordered unit out; mpused=3 persists across turns (can-act gate `0x5acc00` suspect).
- UI facts: **ENDOFTURN1** pane = "Press ENTER for next turn" (Return advances, not a confirm);
  **Escape on a bare HUD opens REALLYQUIT** — svc loop hit it live, recovered via "Oops, no,
  wait!" (400,260) + OK (400,307).
- New scripts: `scripts/m36_store.gdb` + `m36_dismiss.py` (store tail, works),
  `scripts/m36_exec.gdb` + `m36_exec.py` (turn-end + modal svc), `scratch/m36_probe_exec.gdb`
  (unconditional executor probe). Docs: §M36, NAMED.md M36 block, MILESTONES.md C2 M36 addendum,
  skill `references/terraforming-order-path.md` updated.
- Left running: pid 914079, year **2273**, our turn, HUD clean, sel=-1, energy 31, TracerPid 0;
  Former rec41 at (45,7) **order 0x14 (stored raise)**, mpused 3, tile elev 4 unchanged.
  Next (M37): why the executor skips unit 41 — mp/+40 semantics after a stored terraform, and
  whether `Space` on the selected unit still executes the stored order.

## Session 37 (2026-10-21) — M37: the execution wall falls — terraform is a multi-turn accumulator; the stored raise completed live (elev 4→5)

- Two sessions contributed: an earlier 37a/37b run (22:21–22:27, died before checkpointing, left
  REALLYQUIT open) and this one (recovery + push to completion). Found `scratch/m37_exec41.gdb`
  + `scripts/m37_exec41.py` + evidence `m37a_*`/`m37b_*` from the earlier run already on disk.
- **Mechanism (H)**: terraform execution = `0x50ef60` pump → gate `0x5acc00` (`0x5ac650(unit,0) >
  mpused`) → `0x529e70(unit,0)` (solo ⇒ direct) → `0x4d1200(unit)` → `0x4cce50(unit, k, 1)`:
  consume-all `0x5acdb0` + `unit+37 += 2`/turn (chain-fold Σ) until `accum ≥ 2×terrain_table[k].+8`
  (runtime table `0x6938f0+k*32`; `+8` == alpha `#TERRAIN` field 5; raise 12 ⇒ 24 work ⇒ 12 turns;
  `+18` = required tech = 59 ✓ M35) → COMPLETE: order+chain cleared, mask swap, `0x5ad400` RAISE →
  `0x5ad0a0` SETELEV new=5. `0x51f730` REFRESH (mpused=0 etc.) fires **per player per round in solo**
  (live REFRESH events) — called by round sequencers `0x520c10`/`0x521070` that also drive `0x51e700`.
- **Completion (H, live)**: `CHECK accum_new=24 threshold=24 → COMPLETE unit=2028 x=45 y=7 mode=16 →
  RAISE x=45 y=7 → SETELEV x=45 y=7 new=5` at year 2281; post: order 0, work37 0, **tile elev 5**,
  energy 31 unchanged, unit slid 41→40→39 (tracked by order). M36 retracts: mpused "persistence"
  (re-charged each turn after REFRESH) and "executor filters the ordered unit" (`0x585720` = wrong
  door). 0x2101 queue = netplay replication, no solo consumer (holds).
- Harness fixes landed in `scripts/m37_exec41.py`: REALLYQUIT special-case (`answer_confirm`
  defaults to y=196 = pane artwork for that pane; rows are 260/281, OK +47 — recovery verified
  live via `scripts/m37_recover.py`); Escape only when `region_colors < 130` (pane-over-map);
  ENDOFTURN1 → Return; **bare-HUD-on-our-turn stall → TURN COMPLETE click every round** (m37c
  stalled at 2276 otherwise). `m37_exec41.gdb` moved scratch→scripts (durable).
- Docs: §M37, NAMED.md M37 block (+3 corrected rows), MILESTONES.md C2 addendum, skill footing +
  `references/terraforming-order-path.md` updated. Evidence: `m37a_*`, `m37b_*`, `m37c_*`,
  `m37c2_*` (completion run), `m37_recovered.png`.
- Left running: pid 914079, year **2281**, our turn, **ENDOFTURN1 pane open** (Return advances),
  TracerPid 0, energy 31; former (45,7) order 0 mpused 3 (already moved this turn), tile elev 5;
  gdb detached clean. Next (M38): re-issue from the driver (second raise at elev 5 = 81-tile
  footprint ⇒ first foreign-border/diplomacy test, or lower back), and/or two-Former chain
  (4 work/turn ⇒ 6 turns), and/or Space-on-Former semantics.

## Session 38 (2026-10-21) — M38: driver issues a second raise end-to-end; cost formula decoded live; tile (45,7) reaches elev 6 at year 2293

- `scripts/m38_issue.py` + `scripts/m38_issue.gdb` (34 bps = m35 pay chain + m36 store tail +
  footprint/diplomacy sites `0x4d5839`/`0x4d58dc`/`0x4d59c7`/`0x4d5add`/`0x555030`) issued a
  second Raise Land from the driver first try: ENDOFTURN1 Return (2281→2282) → **selection
  recipe** (cycle picked another unit → poke `+40=255` on all other own order-0 units →
  `Escape` → pump auto-selected the Former) → `]` → `TERRAF → TECHCHK 1 → ORDERCHK 0 → COST 16
  → TERRACOSTUP → TERRAPAY → PAYTAKEN → DEBIT 31→15 → footprint (49 tiles 7×7, ZERO
  PACTCHK/DIPLO/REFUND) → AFTERLATCH (latch consumed → PANERET silent, M36 predicted) →
  LOCKCHK 0 → LOCKRET 0 → STORE 0x14 → BCAST → ENQ` (`evidence/m38a_*`).
- **Cost formula (H)**: `0x4cc7b0(x,y,player)` = `(|elev−3|+2)²` ×3-fungal, × base-distance
  (inert for player 3: base+4 = faction ID ∈ {1,2,4,5,6,7}, never 3 — mapping open), `/2` if
  trait bit `0x2000` (clear), always `/2`, clamp 1..30000. Fits both points: 9 @ elev 4,
  **16 @ elev 5**. Prediction: elev-6 raise/lower = **25 > 15 energy** ⇒ next terraform gated
  by economy. Energy flat between debits (income ≈ upkeep, ≈ +0/turn) — feeds C3.
- **Completion** (`m38run2`): work37 4→24 (+2/turn; issue turn executes too — pump runs the
  order right after STORE), `CHECK 24/24 → COMPLETE unit=1872 → RAISE → SETELEV new=6`; mem
  verified: **elev 6**, order 0, energy 15, year 2293, tracer 0. 12 executions 2282..2293 =
  24 = 2×12 ✓. Re-erosion lifted 8 neighbours 4→5 (leveling erodes toward the plateau).
- **Diplomacy branch: armed but clean** — elev-5 footprint (49 tiles, x 42..48 y 3..11) hit no
  foreign-owned tiles; pact/treaty/refusal path remains untested (needs elev-6's 9×9 + 25
  energy). NEXT_PROMPT's "81 @ elev 5" corrected: 49 = idx 6, 81 = idx 7.
- Harness: `m37_exec41.py` preflight relaxed (selected-unit panel ⇒ `classify` unknown with
  garbled strip OCR is fine on our turn; svc loop ends the turn — `svc_hud_clicks=5`); picker
  Expend-row click auto-confirms; `wait_for` races gdb's block-buffered printf (post-kill log
  authoritative). Docs: §M38, NAMED M38 block, MILESTONES C2 addendum, skill footing +
  `references/terraforming-order-path.md` updated.
- Left running: pid 914079, year **2293**, our turn (cur=3), screen `unknown` ncolors=150
  (no pane over map; likely unit panel/bare HUD — re-probe on load, ENDOFTURN1→Return),
  TracerPid 0, energy **15**; Former (idx 36 at load-scan-time, slides) at (45,7) order 0
  work37 0; tile elev 6; EnvEcon bit still published; tutor latch consumed. Next (M39):
  cheap-mode completion sweep (road threshold 2 ⇒ 1 turn; check `table[k].+18` tech gates
  first via `scripts/m35_gate.py`), economy-rate idle measurement (gates the 25-cost
  terraform), player↔faction-ID mapping (static), Space-on-terraform semantics.

## Session 39 (2026-10-21) — M39: Road — second mode proven; issues with no cost block; 2-execution completion; live threshold ladder from AI events

- `scripts/m39_issue.py` (clone of m38_issue: Tab cycle, poke Former `+40=0` pre-cycle,
  menu-pending clear, picker optional, gdb = `m38_issue.gdb` + `m37_exec41.gdb` concatenated
  = 45 bps so a same-turn completion is caught) issued **Road** (`r`, mode 5, order 0x09) on
  the (45,7) Former: `TERRAF mode=0x5 → TECHCHK unlocked=1 →` **cost block fully skipped**
  (PAYPATH/ORDERCHK/COST/picker/SKIPPAY all silent) `→ AFTERLATCH → LOCKRET 0 → STORE 0x09 →
  BCAST`. No DEBIT — energy 15 before/after. Exec 1 same turn: `CHECK 2/4 → NOTYET`; exec 2
  next turn (2295): `CHECK 4/4 → COMPLETE unit=1872 x=45 y=7 mode=5`. Mem-verified: tile
  (45,7) **mask 0x108002→0x108006 (road bit 0x4)**, elev 6 untouched (mode 5 = mask swap
  only), order 0, year 2295, TracerPid 0 (`evidence/m39a_*`).
- **Live thresholds (AI + ours) confirm M37's adjustment formulas:** road **4** at elev-6
  tiles vs **2** at low elev (case-5 elev-class bump); solar 8 vs **16** (case 3 ×elev/2);
  mine 8; RemoveFungus 12. **AI terraformers work +3/execution vs our +2** — cause open
  (not ability bit0). Road at (46,42) completed on first execution (3 ≥ 2).
- **Key model corrected (H):** **`l` = SENTRY order key** (accidentally issued order 1 to the
  Former; turn auto-ended when every unit had an order — cleared by poking `+17=0`);
  **`Tab` = cycle/select-next** (sel −1→36, orders mode→1). Cycle **skips MP-exhausted
  units** (poke `+40=0` first — M38's consume-all had mpused=3). `0x91b5c4`
  order-menu-pending sticks at 1 — poke 0 before order keys. Mid-turn start (turn open, info
  panel up, mostly-black map ⇒ classify `title`/`unknown`): detect `cur==me`, go straight to
  selection. Empty cycle ⇒ ENDOFTURN1 ⇒ Return. Buffering race worked FOR us: cleanup fired
  after the full lifecycle, log holds both executions + COMPLETE + ~300 AI MASKSET/fog events.
- Tools: `m37_exec41.py` gained `--order <hex>`. Docs: §M39, NAMED M39 block, MILESTONES C2
  addendum, skill footing + `references/terraforming-order-path.md` updated.

## Session 40 (2026-10-22) — M40: MagTube remap proven live; first TECHFAIL — the tech-gate advisory is mode-specific (HASROAD)

- **Milestone (H, live, `scripts/m39_issue.py --tag m40a --key r` run as-is, 45/45 bps):** `r` on
  the Former at the now-roaded tile (45,7) (mask 0x108006 elev 6): `TERRAF mode=0x5` (key handler
  passes 5) → `TECHCHK mode=0x6 unlocked=0` (the remap inside `0x4d44d0` **rewrites the mode arg
  slot**) → `TECHFAIL 0x4d486e` → `ADVISOR/PANE id=HASROAD`. Rejected: no STORE, no cost block,
  no DEBIT — post mem-verified order 0, energy 15, tile 0x108006 unchanged, zero side effects
  (`evidence/m40a_issue.json`/`m40a_gdb.log`).
- **Static corroboration (shard_012.c body + live table reads):** remap condition
  `mode==5 ∧ tile.mask&4 ∧ cap[6+tile-seafloor]>−2` (cap table `0x6938e8`, idx `mode*8+flag`,
  MagTube land=**18**/sea=−2 live ⇒ land-only); farm rewrites `mask&0x20 ∧ elev≥4 → 0xa`,
  `mask&0x8000 → 1`. TECHFAIL advisory dispatch: 6→HASROAD (0x68c300) / 1→HASFARM (0x68c308) /
  else NOTUNTILTECH (0x68c310); Script.txt `#HASROAD`: "That square already has a road. Roads may
  not be converted to Magtubes until we discover $TECH0." $TECH0 closed live: fail branch →
  `0x5a69f0(&0x997120, tech_id)` (name from tech records `0x92fdb4+id*44`) → `0x626634(slot 0,
  text)` (slot table `0x99a01c`); post-run slot 0 = "Monopole Magnets", composed text in
  `0x997120`. Bypass: mode 0xa ∧ ability `0x2000` skips the fail branch.
- **Corrections:** terrain-table `+18` "required tech" is garbage (527) for k∈{1,5,6} — the cap
  table is the gate AND advisory source. Pre-gate silent exits: mode 6 w/o road bit, mode 1 w/o
  0x8000 (no advisory). NOTBASE/ALREADYBUILT checks named (static). MagTube terrain entry live:
  maskSET **0x8**, clear 0, work 3 (threshold pred. 6 pre-adjustment, unmeasured).
- **Harness:** runner ran unmodified on the reject path — STORE timeout → cleanup IS the expected
  terminal state for rejected orders; HASROAD pane transient (auto-dismissed); `poke readback
  mismatches` event is a false alarm when no other order-0 unit exists.
- Left running: pid 914079, year **2295**, our turn OPEN (cur=3=me), Former (idx 36 at scan-time,
  slides) at (45,7) **selected** (sel=36, orders_mode 1, order 0, work37 0, mpused 0); menu-pend
  `0x91b5c4` = **1 again** (poke 0 before order keys); tile (45,7) elev 6 mask 0x108006; energy
  **15**; tech-18 byte `0x985c1c+18` = 0 (unlocked=False); TracerPid 0; post-screen classifies
  `hud`. Scout Rover exploring; others Hold. EnvEcon bit 59 still published; tutor latch
  consumed. Next (M41): MagTube unlock-poke (`0x985c1c+18 |= 0x08`) + issue + completion (STORE
  0x0a, mask bit 0x8); generic NOTUNTILTECH live (`n` Condenser, tech 60); economy idle run;
  player↔faction mapping; Space-on-terraform. Docs: §M40, NAMED M40 block, MILESTONES C2
  addendum, skill footing updated, NEXT_PROMPT rewritten for session 41.
- Left running: pid 914079, year **2295**, our turn (cur=3), **ENDOFTURN1 pane likely open**
  (Return advances), TracerPid 0, energy **15**; Former (idx 36 at scan-time, slides) at
  (45,7) order 0 work37 0 mpused 3; tile elev 6 mask 0x108006 (road); Scout Rover exploring
  (queued-move order 0x18, damaged 20%, at (48,14)); EnvEcon bit 59 still published; tutor
  latch consumed. Next (M40): economy-rate idle run (gates the 25-cost terraform; feeds C3),
  MagTube remap test (`r` again on the now-roaded tile → mode 5→6 remap → TECHFAIL advisory —
  TECHFAIL bp already armed), player↔faction-ID mapping (static), Space-on-stored-terraform
  (sensor farm = 4 turns of build time).

## Session 41 (2026-10-22) — M41: MagTube unlock→issue→completion live — third mode done; the case-5/6 elev bump is +2 flat (threshold 8 @ elev 6)

- **Unlock (H):** poke tech bit byte `0x985c1c+18` `0x00→0x08` (bit 3 = player 3) with TracerPid 0,
  verified, gdb armed after; `m35_gate.py` shows MagTube land `unlocked=True`. Tech bits persist.
- **Issue (H, `scripts/m39_issue.py --tag m41a --key r` as-is, 45/45 bps):** `r` at (45,7) (roaded):
  `TERRAF mode=0x5 → remap → TECHCHK mode=0x6 unlocked=1` — **no TECHFAIL, no advisory** —
  `AFTERLATCH mode=0x6 → LOCKCHK → STORE order=0xa → BCAST`. No picker, no COST/DEBIT (no-pay
  path), energy 15 flat. **The STORE writes the REWRITTEN mode** (+17 = 0x0a, not 0x09).
- **Completion (H, `scripts/m37_exec41.py --tag m41b --order 0x0a --rounds 3`):** 4 executions over
  4 turns (2295→2298): `CHECK 2/8 → 4/8 → 6/8 NOTYET`, then **`8/8 → COMPLETE mode=6`**; tile
  (45,7) mask **0x108006→0x10800e** (magtube bit 0x8), elev 6 untouched (mask swap only), order +
  work37 cleared. MASKSET print capped at 300 hits — our swap silent, mem readback authoritative.
- **Correction:** MagTube threshold @ elev 6 = **8** = 2×3 **+2** ⇒ case-5/6 elevation bump is
  **+2 flat**, not doubling (road 2→4 @ elev 6 fits the same rule; M40's "may double ⇒ 12"
  falsified by the CHECK print). consume-all reconfirmed: mpused := 3 (full pool) for +2 work.
- **AI side-obs (O):** base 2×`+8` holds across condenser 24, raise 24, bunker 10, sensor 8,
  RemoveFungus 12, solar 8/12, road 6 — bumps >+2 at unmeasured elevations (open); AI accum
  **+3 on 7 formers but +2 on one** (idx 51, RemoveFungus) — "AI +3" not universal.
- **Harness (H):** both runners ran unmodified on the new mode (STORE detection order-agnostic;
  completion regex mode-agnostic). Evidence: `evidence/m41a_{issue.json,gdb.log,chain.gdb,pre,post}`
  + `m41b_{exec41.json,gdb.log,chain.gdb,pre,post}`.
- Left running: pid 914079, year **2298**, cur=3 (our turn — Former just completed ⇒ **ENDOFTURN1
  pane likely up, Return advances**), Former idx 36 at (45,7) order 0 work37 0 mpused 3; tile elev 6
  mask **0x10800e** (road+magtube); energy **15**; tech-18 byte `0x985c1c+18` = **0x08 — Monopole
  Magnets left UNLOCKED for player 3** (undo: clear bit 3); tech-60 byte 0x16 (players 1/2/4 have
  it, we don't); TracerPid 0, no gdb. Scout Rover exploring; others Hold; EnvEcon bit 59 still
  published; tutor latch consumed. Next (M42): generic NOTUNTILTECH live (`n` Condenser mode 0xc,
  tech 60 gated — runner as-is `--key n`); economy idle run; player↔faction mapping; HASFARM live
  (needs Former walked onto a `mask&0x8000` tile). Docs: §M41, NAMED M41 block, MILESTONES C2
  addendum, skill footing updated, NEXT_PROMPT rewritten for session 42.

## Session 41 continued (2026-10-22) — M42: generic NOTUNTILTECH live; $TECH0/$TERRAFORMTYPE6 substitution closed; tech-record +0 = display-name pointer; terraform op-name table decoded

- **Live (H, `scripts/m39_issue.py --tag m42n --key n` as-is, 45/45 bps):** `n` on the Former at
  (45,7): `TERRAF mode=0xc → TECHCHK mode=0xc unlocked=0 → TECHFAIL → ADVISOR #1 id=NOTUNTILTECH
  → PANE #1 id=NOTUNTILTECH`. Rejected cleanly — order 0, energy 15, tile 0x10800e, year 2298 all
  unchanged; STORE timeout → cleanup = expected terminal (2nd instance). Runner mid-turn dance on
  a fresh turn: poke `+40=255` (order-0 only), poke Former `+40→0`, Tab cycle → sel=36, menu-pend
  poke 0, one `n` → TERRAF. `evidence/m42n_*`.
- **Substitution (H):** Script.txt `#NOTUNTILTECH` = `The "$TERRAFORMTYPE6" operation cannot be
  performed until we discover $TECH0.` — post-run mem: slot 0 = "Ecological Engineering" (tech 60),
  slot 6 = "Construct Condenser", composed `0x997120` matches Script.txt verbatim. `$TERRAFORMTYPE6`
  = substitution **slot 6** (not mode index), set via `0x6265a2` (slot<10 setter, formats via
  `0x61482f`; sibling of `0x626634`). `$TECH0` is set by BOTH fail branches.
- **Corrections (H):** tech record `0x92fdb4+id*44`: **+0 = display-name POINTER** (heap arena:
  18→"Monopole Magnets", 60→"Ecological Engineering", 59→"Environmental Economics"), **+4 = short
  token** ("Magnets"/"EcoEng"/"EnvEcon"/"MilAlg") — M40's "name at +0" corrected. Terraform op-name
  table `0x94d2f8` = 14 × (land name, sea name, key char): Farm/Kelp Farm/`f` … Mag Tube/`R`,
  Bunker/`K`, Sensor/`O`, Condenser/`N`, Echelon Mirror/`E`; sea variants Mining Platform/Tidal
  Harness — the `$TERRAFORMTYPE` source; ORDERS.md key map confirmed.
- Left running: unchanged from M41 handoff — pid 914079, year **2298**, cur=3 our turn, Former idx
  36 @ (45,7) order 0 work37 0 mpused 0, tile 0x10800e elev 6, energy 15, tech18 byte 0x08,
  TracerPid 0. Next (M43): player↔faction-ID mapping (static; note MILESTONES C3 says base faction
  byte is **+5**, not +4 — resolve), then economy idle run. Docs: §M42, NAMED M42 block,
  MILESTONES C2 addendum.

## Session 41 continued (2026-10-22) — M43: player↔"faction-ID" mapping RESOLVED — the base +4/+5 byte IS the owner player index; we own ZERO bases; `0x4e3700` corrected

- **Identity mapping (H):** base `+4` == `+5` byte == **owner player index** — 167/167 units
  standing on a base tile match `unit+14 == base+4`, zero mismatches; per-player home_base
  cross-refs clean for players 2/6/7. Bases per owner {1:10, 2:24, 4:7, 5:6, 6:16, 7:9}. **M38's
  "faction ID {1,2,4,5,6,7} ≠ player index" RETRACTED** — those are owner player indices; 3 absent
  because we own **zero** of the 72 bases.
- **We have no bases (H):** all 5 player-3 units `home_base@+46 = 0xffff` (chain `+48` too). Tile
  ownership = `tile+2` **low nibble = player index**, 0xf unowned; hist {0:199, 1:317, 2:468,
  3:45, 4:345, 5:130, 6:261, 7:269, 15:1166} — we hold 45 **orphan-border** tiles with no bases;
  player 0 = destroyed faction (no units, no bases, 199 tiles, engine still visits cur=0).
- **`0x4e3700(x,y,player)` corrected (H):** Ghidra `psVar7` is `short*` ⇒ compares **byte at
  base+4** with the player arg, x from byte base+0, y from short base+2, stride 0x98 shorts = 304
  B — the function is correct; inert for player 3 = no owned bases (⇒ cost base-distance branch
  can never fire for us — data, not code quirk). Sets `DAT_008f0d34` = last distance.
- **Base minerals (H):** `+64` u32 differs across bases (43/4/4/78) ⇒ **per-base** accumulator,
  mirrored at `+152` inside the 304 record (M31 mirror ✓). Faction records `0x94d650+player*0x82f`
  carry **no def-index byte** (no 0..6 permutation offset found) and no name pointers —
  player↔faction-NAME (GAIANS/HIVE/UNIV/MORGAN/SPARTANS/BELIEVE/PEACE) open.
- Left running: unchanged (pid 914079, year 2298, cur=3, Former @ (45,7) tile 0x10800e, energy 15,
  tech18 0x08, TracerPid 0). Next: M44 economy idle run (`scripts/m44_idle.py`, no gdb). Docs:
  §M43, NAMED M43 block, MILESTONES C2 addendum + C3 correction.

## Session 41 continued (2026-10-22) — M44: economy idle run DONE — our income AND upkeep are zero (energy flat over 12 rounds); AI mineral→energy conversion ≈1:1 seen on one faction; the Council-pane OK bar must be found BY COLOUR (tesseract cannot read it); mask bit 0x2 = unit-present; type-record base = 0x98ad88

- **Blocker fixed (H):** a resolved governor-election pane ("YANG ELECTED" + PROPOSAL bar) froze the
  pump at year 2303; only the blue OK bar remained and **tesseract returns nothing for its label**, so
  vocabulary servicing looped and three attempts (m44a/b/c) died on the preflight assert with zero
  JSON. New `find_ok_bar()` colour-detects it (band x 240-560, y 430-520, lowest contiguous blue bar
  ≥8 rows; calibrated rows y 488-507, x 268-532, rgb (103,91,181)); the HUD chrome's 1-px blue line
  at **y 526 exists in every frame** and must be excluded or a bare HUD tests positive. Live click
  (400,497) dismissed the pane; year 2303→2304.
- **Economy (H, 12 rounds 2304→2315, `evidence/m44d_idle.json`):** our energy 15 at every snapshot =
  **0 net/turn**; the HUD panel agrees where it was visible (Gross Income 0/turn, Total Costs 0/turn,
  NET INCOME 0/turn; rounds 1/3/4 — later crops caught the diplomacy strip instead, so trust the
  memory series) ⇒
  zero bases = no income, and **upkeep never debits faction energy**; the 25-cost elev-6 raise is
  unpayable until we found a base. AI per round: Δenergy {1:-1.4 2:-1.3 4:+10.9 5:-0.5 6:+5.3 7:-0.9},
  Δbase-minerals {1:+2.3 2:+8.3 4:-11.2 5:-1.9 6:+31.2 7:+1.1}; player 4 anti-correlates almost
  exactly (minerals -11.2 vs energy +10.9) ⇒ unspent base minerals → energy ≈1:1 (O, one faction);
  player 6 accumulates both (+31.2 / +5.3). Bases 72→73 ({4:8→9, 6:16→17, 5:5→4, 2:25→24}).
- **Attrition (H counts / O cause):** our units 5→2 during the run (drops 2305, 2308, 2309).
  Survivors: idx 30 **Colony Pod** (type 0) @ (45,11) and idx 31 **Laser Squad** (type 195) @ (43,11),
  both Hold. **The Formers unit (type 1, class 9) is dead — no terraformer remains.** Hypothesis:
  unsupported-unit attrition with zero bases (untested).
- **Corrections (H):** (a) autosaves ROTATE over all 8 slots (30/20/10 every 10 y = 2290/2300/2310,
  then 5/4/3/2/1 yearly = 2311..2315) — the "slot 2 = year 2198" load note is stale; recovery points
  exist. (b) the runtime tile record == map-file cells (2n,y)++(2n+1,y) byte-exact (verified against
  the LIVE autosave map section); accessors (`0x582ed0`, `0x5831a0`) are **parity-blind**
  (`40*y + x>>1`, +0 elev / +8 mask) so the tile pair shares elevation and the +8 mask; a second
  mask-shaped dword at +0x18 is open. (c) tile mask bit **0x2 = unit present** (3193/3200 agree,
  0 false negatives, 7 stale positives). (d) mask vocabulary `0x6938f0` × `0x94d2f8`: farm 0x8000,
  soil enricher 0x80000, mine 0x10, solar 0x40, forest 0x200000, road 0x4, magtube 0x8, bunker 0x800,
  airbase 0x40000 (k=8, work 10, clears bunker), sensor 0x80000000 (k=9, work 4), fungus 0x20
  (k=10 clears / k=11 sets), condenser 0x400000, echelon mirror 0x8000000 — **k=8 is Airbase, not
  Sensor** (M42 corrected); `0x94d2f8` = 14 × (land, sea, key-char STRING) stride 12. (e) **type
  record base is 0x98ad88** (name +0, ability +32 = 0x98ada8, domain +36 = 0x98adac, class +42 =
  0x98adb2): the standing ABSOLUTE addresses were right, the "base 0x98ada8 / name at +20" phrasing
  was not — type 0 Colony Pod/cls 8, type 1 Formers/cls 9 (`0x4d44d0` gates terraform on cls 9 ✓),
  193 Scout Rover, 195 Laser Squad; ≥196 runtime types vs 15 alpha `#UNITS` template rows.
- Left running: pid 914079, year **2315**, cur=3 our turn OPEN, Colony Pod @ (45,11) + Laser Squad @
  (43,11) both Hold, energy 15, tech18 0x08, tech60 0x16, TracerPid 0. Next (M45): found a base with
  the Colony Pod (`b` on owned (45,11)), then re-run the idle loop to read the new income/costs.
  Docs: §M44, NAMED M44 block, MILESTONES C3 addendum, NEXT_PROMPT rewritten for session 42.

## Session 42 (2026-10-22) — M45: FIRST BASE FOUNDED — `b` path live-traced end to end (NEWBASE → 0x4cca50 → CREATERET base=73); NEWBASE accepts a plain Return; mask bit 0x1000 = base border (radius ≈3, pop-independent); economy re-measured: 15 → 19 ONCE then flat again; pitfall: Ghidra FUN_ addresses are verbatim (7/15 bps were +0x400000 off and armed silently)

- **Milestone (H, live):** `scripts/m45_base.py --tag m45a` + `scripts/m45_base.gdb` (15/15 armed)
  pressed `b` on the Colony Pod (idx 30, type 0, cls 8) at (45,11), year 2315. Trace:
  `SETTER unit=30` → `BORDERRET eax=-1` → `LIMITRET eax=12` → `PANE #1 id=NEWBASE` →
  `ALLOCRET base=73 unit=30` → `CREATERET base=73 unit=30` → `PANE #2 id=BASEFOUNDED`.
  n_bases 73→74; our base (45,11) owner 3 **pop 5**, name **"Climactic Research"**
  (game-generated default — Return accepted it, nothing typed), +64 minerals 10, kit =
  HQ + Recycling Tank + Recreation Commons + Energy Bank + Network Node (`m45a_post.png`).
  The Pod was consumed. Recipe that worked: poke `+17` 2→0 (can-act `0x5acc00` refuses order
  1..3 when `+4 & 0x4200 == 0`), rival unit `+40`→255, `0x91b5c4`→0, Tab-select (orders mode 1),
  arm gdb, press `b`, Return on the name pane, Return/Escape on the follow-up panes.
- **No territory dispute (H):** `0x4e3b50` returned **−1** for (45,11) even though the tile's owner
  nibble was already 3 ⇒ the ~45 inherited nibble-3 "orphan" tiles (M43) are NOT borders to the
  game, so TERRPACT/THISLANDISMYLAND never fired. Base limit query `0x4e9b40` = **12** (BUREAUCRACY
  only at a nonzero multiple of it).
- **New mask vocabulary (H, statistical):** mask1(+8) bit **0x1000 = "inside a base's claimed
  border"** — 1258 flagged pairs, assigned to nearest base = 12-31 pairs per base, Chebyshev max
  3-9 (mean ≈3.3), **no pop dependence**, mask1-only 1238 vs mask2-only 1, ocean pairs included;
  our tile gained it at founding (0x108006 → 0x109005) while the farm bit 0x8000 cleared. Bit 0x1 =
  base-on-pair now 74/74. Base +64 == +152 still 74/74; **base +56 is the constant `0x00dfbe41`
  in every record** (M44's "copied from home base" reading is wrong).
- **Economy (H, 16 start-of-our-turn snapshots, 2315→2329, `m45c_idle.json` + `m45f_idle.json`):**
  faction energy **15 for 2315-2319 → 19 at 2320 → flat 19 through 2329** — `m45f`'s deltas block
  says **0.0/round over its 9 intervals**, ≈+0.8/round across the whole window, against the
  base screen's own readout (ENERGY 003−000 = +003, MINERALS 007−000 = +007, NUTRIENTS 009−010 =
  −001 SHORTFALL "Hunger!"). Pop 5→4 (shortfall attrition, not eco-damage). Base +64 oscillates
  1-10 with no trend; our units grow 1→**6** (the base turns out Scout Patrols) while energy stays
  flat ⇒ **unit upkeep still never debits faction energy**; the only moving interval
  (2319→2320: minerals 8→4, energy 15→19) matches M44's ≈1:1 mineral→energy signature.
  Base `+64` series 10,10,6,2,8,4,9,4,8,2,5,8,1,3,5.
  **A pod base does not make us solvent** — the 25-cost elev-6 raise (M38) is unpayable 14 years on.
- **Harness fixes (durable):** `service_pane` had **no branch for classify kind `base`** (the BASE
  screen the founding leaves open; its RENAMEd/OK row is at y≈365, outside `find_ok_bar`'s band) →
  `m45b_idle` spun 15 min on 1 round and had to be killed. Added `kind=="base"` → one Escape to
  `m44_idle.service_pane` and to `m45_base.py`'s post-create loop. Also: `objdump` cannot read this
  PE ("invalid bfd target") — pin call sites with a raw E8 scan (`.text` file offset = VA−0x400000;
  the PE header's ImageBase field reads a bogus 0x270000, identity mapping holds).
- **PITFALL (H, cost 7 of 15 trace lines):** Ghidra callee names `FUN_<address>` are the address
  VERBATIM. `FUN_005abb40` = 0x5abb40, `FUN_0041b780` = 0x41b780 … — m45a armed them with a
  duplicated leading digit (+0x400000), gdb armed 15/15 anyway (a wrong-but-mapped address never
  complains) and the seven bogus bps silently never fired. Corrected + warned in
  `scripts/m45_base.gdb`.
- **Open:** HUD Gross Income/Total Costs/NET INCOME never OCR'd (dialog or unit panel every frame)
  → find the panel's source values in memory instead (M46 option 1). M44's "autosave record == two
  22-byte cells at +2724" did NOT reproduce (3200/3200 differ; located ocean pairs fit no stride
  model) → save-map layout unverified; pre-founding map frozen in `scratch/auto2315/` (1.SAV = 2315).
- Left running: pid 914079, year **2329**, cur=3 our turn OPEN, TracerPid 0, no gdb; **1 base**
  (idx 72 "Climactic Research" @ (45,11), pop 4), **6 units** (Laser Squad idx 22 @ (43,11) Hold +
  5 Scout Patrols type 2 @ (45,11), each `+46 = 0x48` = base 72 ✓ produced units home to their
  base), energy **19**, n_bases 75, no cls-8 colonist and no cls-9 Former left. Docs: §M45, NAMED M45 block, MILESTONES C3 addendum,
  NEXT_PROMPT rewritten for session 43.
