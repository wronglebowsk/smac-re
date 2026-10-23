# Session notes archive — sessions 56-56

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 56 (2026-10-24) — M53b: THE TYPE-RECORD `+41` BYTE IS A COST FACTOR — one writer (`shard_015.c:9358` = `FUN_00595820(chassis, weapon, armor, ability, reactor)`), the price the game prints and debits is `FUN_004e40a0(owner,1,−1) × +41` with that multiplier = 10 = 100 % ⇒ **1 unit of `+41` = 10 minerals**; `+43` is the auto-calculated AI role byte (Scout Patrol `+41 = 1` vs `+43 = 10`)

- **Verdict: cost, not weight, not turns.** `+41` (`0x98ad88 + type·52 + 0x29` = `0x98adb1`) has exactly
  ONE writer in the whole corpus — `shard_015.c:9358`, `(&DAT_0098adb1)[type·0x34] = uVar5` inside
  `FUN_00595b10 @ 0x595b10` (header `shard_015.c:9273`) — where `uVar5 = FUN_00595820(chassis, weapon,
  armor, ability, reactor)` (`shard_015.c:9124`-`:9258`, return at `:9257`). Grep covered BOTH Ghidra
  store renderings (`(&DAT_…)[…] =` and `*(… + 0x98adb1) =`); every other `98adb1` hit is a read. Turns
  come from elsewhere: `FUN_005ac8c0` (`shard_015.c:23672`) returns a per-triad rate global
  (`DAT_0092a2d0/d4/d8`) and never touches `+41`.
- **The calculator's inputs are the alpha rules tables, live-verified.** Chassis `0x92ae80` stride 0x90
  = `+0` speed, `+1` triad, `+2` range, `+3` cargo, `+4` cost ("normally equal to speed" — Infantry
  1/1, Speeder 2/2, Foil 4/4, Cruiser 6/6, Missile 12/12), `+5` missile flag (only the Missile chassis
  has it), `+6` preq tech; weapon `0x92b950` stride 16 = `+0` attack(s8), `+2` mode, `+3` cost (Gun
  1/0/1, Colony-Pod package 0/8/10, Formers 0/9/6, Transport 0/7/4, Artifact 0/12/36); armor `0x92fd10`
  stride 16 = `+8` rating, `+9` mode, `+0xa` cost (Scout 1/0/1, Psi 255/2/6). Alpha field names:
  `programs/alpha.txt:344-345`, `:383`, `:419`, and `#UNITS` = `; Name, Chassis, Weapon, Armor, Plan,
  Cost, Carry, Preq, Icon, Abil` (`:532`) with `; Cost = Cost in minerals (0 = Autocalculate)` (`:554`).
  `FUN_00595820`'s missile short-circuit (`:9224`) is why a missile chassis costs only its warhead.
- **Re-implementation check (the proof).** `scripts/m53b_costcalc.py` re-implements the formula
  (variant 3: the land-triad `0x400`-flag loop does NOT feed the surcharge counter) and reproduces
  **180 of 188** populated rows' live `+41` exactly (`evidence/m53b_costcalc_digest.txt`). The only
  mismatches with `ability == 0` are precisely the 3 shipped `#UNITS` rows that carry an explicit
  non-zero Cost — Mind Worms 5, Isle of the Deep 8, Locusts of Chiron 10 (formula says 11) — so
  **the alpha Cost overrides the auto-calculation**; the 4th explicit row (Alien Artifact 10) agrees
  with the formula anyway. Remaining: 2 rows off by 1 on ability bit 1 (Scout Rover, Scout Speeder)
  and 3 junk records. Hand-checks that match live exactly: Scout Patrol 1, Colony Pod 3, Formers 2,
  Transport Foil 3, Sea Formers 4, Probe Team 3, Unity Rover 2.
- **Everything the game charges or prints is `multiplier × +41`.** Affordability
  `if (base+0x40 < iVar3·iVar4)` at `shard_012.c:20722`; the SPENDA debit `base+0x40 −= iVar3·iVar4`
  at `shard_012.c:20866`; the base pane computes `cost = mult × +41` and compares it to storage for
  the progress bar (`shard_001.c:4705-4708`); the UI string is literally
  `__itoa(iVar7 × (byte)(&DAT_0098adb1)[type])` (`shard_014.c:19723-19725`, `FUN_00577280`).
  `iVar3 = FUN_004e40a0(owner, 1, −1)` (`shard_012.c:13798`) = event-mask owner ⇒ 10, rescaled by
  difficulty `DAT_0092a290/0x92a294` and `DAT_0092ada8`, then `switch(faction+0x1c government)`.
  **Live: 0x92a290 = 10, 0x92a294 = 10, 0x92ada8 = 2, mask `& 0xff` = 0x08 (player 3 only), government
  field 0 ⇒ the multiplier is exactly 10 = 100 %**, so the alpha cost unit is 10 minerals. M52b's
  measured debit (10 minerals for Scout Patrol with `+41 = 1`, `evidence/m52b_watch.log:391-392`)
  matches, and so does independent SMAC strategy text ("a Scout Patrol costs you 10 minerals").
  Facility upkeep proves the loader does NOT pre-scale alpha values into tables (`0x984d48 + item·0x30`
  int0 == alpha `Maint` verbatim for items 1-11), so the ×10 is the percent-of-10 convention.
- **What `+43` is (the ≠ row the milestone asked for).** `+43` (`0x98adb3`) is the auto-calculated AI
  role byte from the same builder's ladder (`shard_015.c:9366`-`:9441`): noncombat packages get
  `weapon mode + 0x20` (`:9431`) → 39/40/41/42/43/44 = the live values for Transport Foil / Colony Pod
  / Formers / Supply Crawler / Probe Team / Alien Artifact; combat chassis get 1…10 — the ladder
  reproduces Mind Worms 1, Isle of the Deep 6 (sea branch), Locusts and Unity Scout Chopper 9 (air ∧
  `ability & 0x20`), Scout Patrol and Unity Rover 10 (the `attack == 1 && armor == 1` rule at `:9419`).
  `+42` is the Plan/class byte: it equals the alpha `#UNITS` Plan column for **14/14** shipped rows,
  which the ladder alone explains for only 10 of them (Scout Patrol 0→3, Mind Worms 0→1, Isle 6→7,
  Sea Formers 6→9 need the explicit Plan), so the loader overrides `+42` — INFERRED, no corpus store
  visible in either Ghidra rendering. **Named ≠ rows:** Scout Patrol `+41 = 1` (= the 10 minerals
  actually debited) vs `+43 = 10`; Colony Pod 3 vs 40; Transport Foil 3 vs 39. `+41 == +43` in only
  21 of 193 populated rows (`evidence/m53b_types.tsv`).
- **M52b's "PER-TYPE PRODUCTION WEIGHT" label is corrected** in `NAMED.md`: `0x5ac950` is the type
  COST accessor (returns `+41` verbatim for `type < 0x40`, clamps [1,999] only for class 8 with a base
  index, `shard_015.c:23707`); the ×10 belongs to `0x4e40a0`. The AI planner reads the same byte as
  `(cost + 2) << 8` (`shard_012.c:25696`) — cost reused AS a value, not a second weight (INFERRED).
- **Method notes.** This milestone needed no live driving: `/proc/<pid>/mem` preads (TracerPid 0,
  ptrace_scope 0, no gdb) + the Ghidra corpus + `programs/alpha.txt` were enough. Two grep shapes
  carried it: the store-shape grep (which found the single `+41` writer) and reading the alpha
  COMMENT headers, which name the columns of tables whose rows are bare data — `#UNITS` is unlabelled
  but `#FACILITIES`' sibling comment block and the chassis/weapon/armor headers give every field name.
- **Open threads.** Where the loader writes the explicit alpha Cost into `+41` and the Plan into `+42`
  (neither renders as a `DAT_` store); `+41` off-by-1 for ability bit 1; `0x5ac950`'s `type ≥ 0x40`
  bump (`FUN_00595ad0(type) × rate / 100`, zeroed when the base already owns it); secret-project costs
  come from a different table (`(&DAT_00984d44)[idx·0xc]`, `FUN_004f26e0`) under the same multiplier
  convention; M53e (mode-5 insert-shift), the −29 head value, `FUN_0059ce10`'s `+0x4c = pop·10/2`.
- **Next:** `NEXT_PROMPT.md` rewritten for session 57; **THE PICK = M53e** (finish the enqueue UI:
  make mode 5 fire, label-verify the six chooser bars, reconcile 8 visible rows vs cap 9).
