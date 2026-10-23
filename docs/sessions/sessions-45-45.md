# Session notes archive — sessions 45-45

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 45-46 (2026-10-22) — M48d: MINERAL ECONOMY FULLY TRACED (first queue/growth completion in 26 years)

`scripts/m48d_drive.py` (driver-generated gdb: 16 int3 sites + 4 hw WPs, literal baked addrs,
SELFTEST block, colour-only fast loop + OCR fallback map) + generated `evidence/m48d2_watch.gdb`,
logs `evidence/m48d2_{watch.log,drive.json,run.log}`. 3 rounds 2345-2347 armed, clean detach,
0 OCR passes, zero stalls. Load: relaunch + `Alpha Centauri Autosave 1.SAV` (year 2344) after the
CONFIRM-DISBAND deadlock (below).

**Storage model VERIFIED (corrects M48's "pin" theory)**: between completions `base+0x40 += d0`
per round, UNCLAMPED (Morgan 0x95ef70 111→121 = +d0 10, no clamp hit). AT EVERY PRODUCTION
COMPLETION (unit OR facility), after the spend, storage := **max(0, min(d0, cap))** — the stockpile
is destroyed down to one round's income. Three independent confirmations: ours 200→190(SPENDA)→0
(WP3 store at 0x4eff23, d0=0); Morgan 131→5(shortfall)→10 (MIRA, d0=18 cap=10); m48e 200→0 (d0=-1).
- Sites (all fired on our base, first time ever): IGATE 0x4ef7db (d0 load) → IADD 0x4ef7f6
  (store storage+d0) → QGATE 0x4ef88b (+0x50 carries transient scratch 0xE00001 mid-visit) →
  COMPLET 0x4efe41 (ebx=2 item, edi=10 COST of Scout Patrol, esi=8 budget) → SPENDA 0x4efed8
  (store 0x4efee0 = −cost) → [gate 4efee4: post-spend storage ≥ edi? else shortfall branch] →
  CLAMP1 0x4eff02 (event test (1<<owner)&mask; ours 0x8 ✓ mask 0xff08) → MIRA 0x4eff29
  (store 0x4eff23 := min(d0,cap)).
- PROGDIV 0x4efd49 and QDRAIN 0x4f1e3f: ZERO hits all rounds — not on the solo pipeline path.
- **Pop-growth production**: pop 4→5 next round + new unit idx 297 (type 2, home 71) + COMPLET
  ebx=2/edi=10 + spend 10 ⇒ growth units cost minerals from base storage; 26 years of storage 0
  ⇒ pop grew but units never spawned ⇒ the "builds Scout Patrol" backlog messages. First unit
  ever produced by our base under observation.
- **NOSUPPORT disband condition**: d0 < 0 ⇒ disband one unit per round (2341-2344: units 5→3);
  d0 = 0 ⇒ stable (2345-2347 ✓). Upkeep ≈ 2/unit vs facility income 6-7.
- d0 (base+0xd0) recomputed at 0x4e955d (inside 0x4e93f0) EVERY round before the pipeline visit —
  pokes to d0 are dead on arrival (confirmed 3×). +0x3c and +0xcc survive until the visit but cc
  is re-derived too (came back 0, then −1 with d0=0; cc tracks d0).
- Energy WPs (live M47 model): +2 credit 0x4f5c92 (=base+0xfc) then −1 −1 facility upkeep
  0x4f4958 → 19→21→20→19, net 0 ✓.
- Pipeline sweep: full sweep = 75 visits, ours LAST (n=75); sweeps can end early (21/28 visits)
  when the year store interrupts — visit-order/early-stop mechanism OPEN.
- Pane bp 0x483470: ZERO hits (OPERATIONS DIRECTOR confirm doesn't route through it; advisories do).

**UI lessons (cost a lost game-state; recovery = relaunch+autosave):**
- CONFIRM DISBAND (Script #DISBAND, rows "Never mind."/"Confirmed." + OK) opened from the base
  panel's FORCES SUPPORTED context menu (glyph click (688,462) → menu box y 464-534, Disband row
  y≈529, x 612-700) can cascade BEHIND base-panel widgets: its rows/OK land on chrome hitboxes,
  keys are dead (M32 modal sink) → unreachable modal. Row clicks never moved the highlight.
  Recovery: relaunch + load autosave (saves live in `programs/saves/auto/`, year = u16 @0x54;
  M27 typed-path recipe; `scripts/m48d_boot.py`). Autosaves had captured 2344 — zero progress lost.
- Panes QUEUE: each Disband-menu click queues a CONFIRM DISBAND; each OK click cancels one.
  Identical-looking panes cycling = queue draining, not a frozen pane.
- TOUR hint popup (auto-opens on first view of a screen): Continue (325,585). Social Engineering
  full screen (OK (240,368) commits, CANCEL doesn't close). Comm "put her through?" pane:
  "No, close the channel." row ≈ y 310.
- Colour-only driver (rightmost_blue_run 150-430 row-click bar_y−25 then bar; find_ok_bar 430-520;
  hud_up gate for TURN_BTN) ran 3 rounds unattended 0 OCR 0 stalls ✓.

Next (M49 options): growth-cost/esi=8 formula (disambiguate 2×pop vs cap−fc vs (d0+fc)×4 — pop 5
round); pipeline early-stop mechanism; production-rate cc source function; the 2320 +4 credit;
faction NAME mapping; ledger writers on a spending round.
