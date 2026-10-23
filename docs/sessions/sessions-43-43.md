# Session notes archive — sessions 43-43

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 43 (2026-10-22) — M46: ECONOMY DECOMPOSED — the upkeep pipeline is named end to end (`0x521070` → `0x5208f0` → `0x520540` → `0x4f5a70`, `energy += base+0x7e`; facility upkeep charged directly by `0x4f47f0`); HUD Gross/Costs/NET = `FUN_00445900` scratch globals, live-verified net 0 ⇔ energy flat; `faction+4` = within-round spending ledger; real blocker found: the OPERATIONS DIRECTOR end-turn pane

- **Milestone (H, static + live):** the per-round economy. Driver `0x521070` → per-player
  `0x5208f0(p)` (sub-steps `0x5a1830`, `0x51f730`, **income core `0x520540`**, `0x51fe90` sliders,
  `0x5a1ad0` attitude penalty) → tail **`energy -= faction+4; faction+4 = 0; clamp >= 0`**, i.e.
  faction `int[1]` is a **within-round spending ledger**, 0 at every start-of-turn (all players,
  11 snapshots). `0x520540` pays gifts, calls `0x4f5a70(base)` per base, then the AI-only stockpile
  line (gated `DAT_00985aec > 3`; ours = 2 ⇒ never) and the trait bonus (`0x927a7c + p*0x59c`,
  flag `0x4000`). `0x4f5a70` runs the production pipeline and does **`energy += base+0x7e`** — a
  transient per-base income field that reads 0 at start-of-turn with no visible writer in the whole
  export (O: computed-pointer write). Facility upkeep is separate and DIRECT: **`0x4f47f0` charges
  `energy -= cost`** per completed facility and SELLS one on shortfall (bitmap clear + refund).
- **HUD panel solved without OCR (H):** `FUN_00445900(player,0)` recomputes, per redraw,
  `0x745734 = sum base+0xfc` (GROSS), `0x744f28 = sum upkeep` (TOTAL COSTS), `0x7457d4` trade,
  `0x7457dc = NET`; `0x744f2c[base]` per-base upkeep, `0x745738[39]` item counts, `0x74572c` food,
  `0x745730` self-sufficiency %. Faction display pane `0x49fee0` draws rows 0x17d/0x17e/0x17f from
  these globals verbatim. **Live: gross 2 - upkeep 2 = net 0 ⇔ energy 19 flat** ⇒ the old "HUD rows
  never OCR-able" item is moot; read the globals.
- **Item upkeep table decoded (H):** `0x984d48 + item*0x30`, 39 rows, int0 = upkeep, int1 = required
  tech id (`0x92fdb4 + id*44`); **runtime item = alpha `#FACILITIES` index + 1**; completion bitmap
  at **base+0x8c** (byte `item>>3`, bit `item&7`), mapper `0x507410`. Disabled-list puzzle resolved:
  the list is in the **player trait record `0x927a7c + p*0x59c`** (1436 B; `+0x20` count, `+0x24`
  types, `+0x44` items) and **our faction zeroes Network Node** ⇒ 3 - 1 = 2 = live `744f28`.
- **Per-round full-record diff, all 7 AI (H, `m46e`, 2330→2331):** records are **2095 ints**
  (stride 0x20bc; the old 2111 over-read 16 ints into the next player — `int[2095]` = next energy).
  Panel net vs Δenergy: p1 30/+4, p2 16/−5 (tech completed, `+0x1a8` 485→87, `+0x1ac` 30→77),
  p3 us 0/0, p4 29/+18, p5 7/+7 (exact), p6 10/−24, p7 25/+11. Exact for us and p5; the gaps are
  within-round ledger debits (research, gifts, AI terraform). Unit upkeep again NOT charged to energy.
- **Standing answer (H):** our slope is net 0 ⇒ **25 energy is never disposable** (need +6 at Δ0);
  the elev-6 raise stays unpayable, and Corner Market `0x4e2050` is surplus-gated
  (`energy > max(sum rivals, 1000)`) so it can never save us. Solvency must come from pop/facility
  growth raising `base+0xfc`. The 2320 +4 credit remains a one-off, mechanism **open (M)**.
- **Blocker that ate m46a-d (H, cost ~4 runs):** the **OPERATIONS DIRECTOR end-turn pane** —
  "Some of our units have not yet moved this turn ... end the turn now?" with `Cancel.` as DEFAULT
  and its blue OK bar at **y 215-350, outside `find_ok_bar`'s 430-520 band**; Return picks Cancel so
  the turn never ends while TURN COMPLETE stays visible behind the pane. Fix: from the OCR Cancel
  word centre, click `(cx, cy+24)` then `(cx, cy+49)`. Also added **`hud_up(png)`** (orange-pixel
  count in `(600,395,800,425)` > 300) because `classify()` denies `hud` on the busy frame.
- **Open (M47):** who writes `base+0x7e` and the `faction+4` ledger (hw watchpoints); what
  `faction+0x1b8` is (multiples of 20); the 2320 +4 mechanism; the mineral economy is still
  un-isolated. Detail `turn_driver.md` §M46, `NAMED.md` M46 block, `MILESTONES.md` C3 addendum.
