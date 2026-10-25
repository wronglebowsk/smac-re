# ORDERS — the unit order menu map (M32, session 32, 2026-10-21)

Every player order, from keystroke to order byte, **live-verified through the game's own
calls** (no injection, no poke-driven claims). Scripts: `scripts/m32_keys.gdb` (29 entry
breakpoints), `scripts/m32_run.sh` (`M32_KEYS="key1 key2 …"` env var, arms → presses →
stops gdb → flushes). Proof logs: `evidence/m32_keys.log` (run 1), `evidence/m32_keys2.log`
(run 2), per-key unit-record snapshots `evidence/m32_keys{,2}_state.txt`.

## 1. Key routing model (live-proven by the exact DISP args)

A key event reaches `FUN_00512b40(param_1, param_2)` where

* `param_1` = the typed **character** (case-sensitive: 'h' = 0x68, 'H' = 0x48);
* `param_2` = the **VK code with modifier bits**: Shift = bit 16 (0x10000), Ctrl = bit 17
  (0x20000). Letters arrive as VK uppercase (h → VK 0x48), punctuation as OEM VKs
  ('/' → 0xbf, '.' → 0xbe, '[' → 0xdb, ']' → 0xdd, '_' → 0xbd).
* Menu/widget events reuse the same handler with `param_2 = (menu_id<<8)|hotkey_char`
  (e.g. 0x20052 = 'R' in menu 0x20, 0x30041 = 'A' in menu 0x30) — those are the
  `param_3` cases of the dispatcher.

Routing inside `FUN_00512b40`:

1. VK 0x60–0x69 (numpad 0–9) zeroes `param_1` (line 136) — numpad is never a command.
2. Direction keys: arrows VK 0x21–0x28 → dir 0..7 (M27) **and** numpad 2/3/4/6/7/8/9
   (VK 0x62/63/64/0x66/0x67/0x68/0x69) → the same dir cluster (this is what M24 misread
   as "remaps b c d f g h i" — they are numpad VKs, not letters). Shift+direction
   (0x10021–0x10028, 0x10062–0x10068) pans the view instead.
3. Everything else, when orders mode is on (`DAT_0091b5b8 != 0`) ∧ `FUN_004e1f90() == 0`
   (not scenario-editor mode ∧ PgUp not held) ∧ a unit is selected (`DAT_0091b5bc >= 0`):
   **`FUN_00512450(char, FUN_0064d300(char), VK|flags)`** — the order dispatcher.
   Otherwise `FUN_00511960` (cursor-tile handler).
4. `FUN_0064d300` = **tolower normalization** (live: 'M'→0x6d, 'G'→0x67, 'S'→0x73,
   'B'→0x62, 'E'→0x65, 'K'→0x6b).

`FUN_00512450` runs **three sequential dispatch stages** on `(param_1, param_2, param_3)`:
a `param_1` switch on raw chars (0x42–0x72), then a `param_2` switch on the lowercased
char (0x20 0x2e 0x2f 0x5b 0x5d 0x5f 0x64 0x6b 0x6d 0x73), then a `param_3` chain on menu
codes (0x20044–0x30055). Solo (`DAT_00920434 == 0`) skips the head gate entirely.

## 2. The terraform family — `FUN_004d44d0(unit, mode)` = issue_terraform_order

* `mode` = index into alpha.txt **`#TERRAIN`** (20 records; parsed in `data/alpha.json`).
* The issued order byte is **`+17 = mode + 4`** (store at the issue tail: `pppuVar10 =
  param_2; … (+17) = (char)pppuVar10 + 4; FUN_00584350()` — matches the M24/M26 rule
  "order bytes 4..0x17 are indexed `order − 4`" and `FUN_004cce50(unit,k) → +17 = k+4`).
* Gates/validators (advisor messages via `FUN_00483470`): unit class must be **9**
  (`DAT_0098adb2[type*52] == 9` = Former) else `NEEDTERRAFORMERS`; domain/terrain checks
  (`TERRASEA`, `NOTATALL/NOTONLAND/NOTATSEA` via capability table `DAT_006938e8[mode*8 +
  land]` — zeros in the file, loaded from alpha.txt at runtime); tech gate
  `NOTUNTILTECH` via `FUN_005a7520`; per-mode tile checks (`HASROAD` mode 6, `HASFARM`
  mode 1, `TWOBOREHOLES/NOBOREHOLE` mode 0xe scanning the 8 neighbours, `NOAQUIFER` mode
  0xf, `SEATOOLOW/SEATOOHIGH/TOOLOW/TOOHIGH/TOOFLAT` modes 0x10–0x12, `NOTINROCKY`,
  `NOTINFUNGUS/NOTYETFUNGUS`, `LOWTIDAL`, `NOTONVOLCANO`, `NOTONMONOLITH`, `NOTINSCENARIO`,
  `LOWSOLAR`, `NOTATALL`); then the payment path: `Want_to_terraform` dialog +
  `TERRACOST`/`TERRAPAY` — cost `FUN_004cc7b0()`, energy pool **`DAT_0094d650[player*0x82f]`**
  is debited (`−= cost`, refund on failure); footprint iteration over the parity delta
  tables `0x67850c/0x678990` calling `FUN_00555030`/`FUN_00528930` per tile; finally
  `+17 = mode+4` + broadcast `0x2101` + the `TERRAFORM` tutor hint.
* **Mode rewrites before validation** (lines 104–118): mode 5 (Road) → **6 (Mag Tube)**
  when the tile's `+8` bit 4 is set (a road exists) — one key, context upgrade; mode 0
  (Farm) → **1 (Soil Enricher)** or → **0xa (remove Fungus)** by tile bits `0x20`/`0x8000`
  and level.
* Live-verified (unit 56, a Colony Pod — every key entered `FUN_004d44d0` with the exact
  predicted mode; the class gate then printed `NEEDTERRAFORMERS`): modes **0**('f'),
  **2**('M','m'), **3**('S','s'), **5**('r'), **7**('K','k'), **8**('.'), **9**('o'),
  **0xb**-via-menu, **0xc**('n'), **0xd**('E'), **0xe**('B'), **0xf**('q'), **0x10**(']'),
  **0x11**('['), **0x12**('_').

### The #TERRAIN table (alpha.txt, with the game's own hotkey strings)

| mode | order=mode+4 | name (land/sea) | tech | hotkey | live key | cost |
|---|---|---|---|---|---|---|
| 0 | 0x04 | Farm / Kelp Farm | — | f | `f` ✓ | 4 |
| 1 | 0x05 | Soil Enricher | EcoEng2 | (mode-0 rewrite) | — | 8 |
| 2 | 0x06 | Mine / Mining Platform | — | M | `M`,`m` ✓ | 8 |
| 3 | 0x07 | Solar Collector / Tidal Harness | — | S | `S`,`s` ✓ | 4 |
| 4 | 0x08 | Forest | — | Shift+F | `F` (static) | 4 |
| 5 | 0x09 | Road | — | R | `r` ✓ | 1 |
| 6 | 0x0a | Mag Tube | Magnets | R (mode-5 rewrite) | — | 3 |
| 7 | 0x0b | Bunker | MilAlg | K | `K`,`k` ✓ | 5 |
| 8 | 0x0c | Airbase | DocAir | . | `.` ✓ | 10 |
| 9 | 0x0d | Sensor Array | — | O | `o` ✓ | 4 |
| 10 | 0x0e | Remove Fungus | — | F | (mode-0 rewrite) | 6 |
| 11 | 0x0f | Plant Fungus | EcoEng | Ctrl+F | — | 6 |
| 12 | 0x10 | Condenser | EcoEng | N | `n` ✓ | 12 |
| 13 | 0x11 | Echelon Mirror | EcoEng | Shift+E | `E` ✓ | 12 |
| 14 | 0x12 | Thermal Borehole | EcoEng | Shift+B | `B` ✓ | 24 |
| 15 | 0x13 | Aquifer | EcoEng | Q | `q` ✓ | 18 |
| 16 | 0x14 | Raise Land / Sea Floor | EnvEcon | ]] | `]` ✓ | 12 |
| 17 | 0x15 | Lower Land / Sea Floor | EnvEcon | [[ | `[` ✓ | 12 |
| 18 | 0x16 | Level Terrain | — | _ | `_` ✓ | 8 |
| 19 | 0x17 | Monolith (editor) | — | ? | — | 8 |

## 3. The named orders (`FUN_00512450` param_1 switch)

| key (param_1) | callee | what it does | order written |
|---|---|---|---|
| `h` 0x68 | `FUN_004d3770(sel,0)` | **HOLD** mode 0 (cancel first; tile gate; `+28`=0) | `+17 = 2` ✓ live (M18 + M32 end-to-end: rec56 order 0→2) |
| `H` 0x48 | `FUN_004d3770(sel,10)` | HOLD sub-mode 10 (freeze) | `+17 = 2`, `+28 = 10` |
| `l` 0x6c | `FUN_004d3510(sel,0)` | **SENTRY / board transport**: cancel; air-load picker (`AIRLOAD` pane) when a class-7 carrier is in the chain; else `FUN_005ab420` → **`+17 = 1`**, `+20 = −1`, `+28 = 0`; clears `b5c4` | 1 (Sentry, `#ORDERS` 1) |
| `o` 0x6f | `FUN_004d44d0(sel,9)` on land units; `FUN_004d94d0` when class 10 | **Sensor Array**; on sea units **CONVOY**: `+17 = 3`, `+38` = requisition flag (`s_SUPPLYEXTRACT`) | 9+4 = 0xd / 3 ✓ live |
| `g` 0x67 | `FUN_004d6fb0(sel,0x18,0)` | **queued MOVE to own BASE** (`+20/+28` = base x/y, `+4 &= ~0x10000`) — M28 | 0x18 |
| `G` 0x47 | `FUN_004d8b20` | **join base garrison**: cancel order; if standing on a same-faction base, `+46` = base idx + roster re-count (`FUN_0041b600` old+new) | (clears) ✓ live |
| `I` 0x49 | `FUN_004d6fb0(sel,−3,0)` | route to base (solo → `FUN_004d0e60`) — static | 0xfd path |
| `i` 0x69 | `FUN_004d8ca0` | special ability action, gated by ability bit `DAT_0098ada8[type*13] & 0x10` + energy `FUN_005f1394` + tile checks — static | ? |
| `U` 0x55 | `FUN_004d1f20` | **unload toggle**: `+17 == 1` → clear (unboard); else `UNLOADNO/UNLOADNEXT` | 1→0 |
| `a` 0x61 | `FUN_004d3f70(sel.x, sel.y, 1)` | ACTIVATE at own tile (stack picker) | — |
| `b` 0x62 | `FUN_004d1280` / `FUN_004d6b90` / mode-0xe branch | **BUILD BASE** (`NEEDCOLONISTS`/`NEWBASE`/`BASEFOUNDED`); sea domain → `OBLIT*` (obliterate); engineer branch → borehole mode | — |
| `f` 0x66 | `FUN_005ac030(type,1)==0 ? FUN_004d44d0(sel,0) : FUN_004d9690` | **Farm**; area-formers instead enter **pane mode 10** destination-pick (`FUN_0050ba90(10,…)`) | 4 ✓ live |
| `F` 0x46 | `FUN_004d44d0(sel,4)` | **Plant Forest** (Shift+F) | 8 (static) |
| `n` 0x6e | `FUN_004d44d0(sel,0xc)` | **Condenser** | 0x10 ✓ live |
| `p` 0x70 | `FUN_004d8c20` | clear waypoints `+18 = 0` + enter **pane mode 8** (route destination) or exit it if already 8 | — |
| `P` 0x50 | (inline) | UI flag toggle: sets pane flag `0x400000` on all widgets + `FUN_0046fa10/00472810` — not an order | — |
| `q` 0x71 | `FUN_004d44d0(sel,0xf)` | **Aquifer** | 0x13 ✓ live |
| `r` 0x72 | `FUN_004d44d0(sel,5)` | **Road** (→ Mag Tube when the tile already has a road) | 9 ✓ live |
| `L` 0x4c | `FUN_004d9120(sel,0xb)` | cancel order + reset queued dest (`+22/+30` = current pos) | 0 |
| `B` 0x42 | `FUN_004d44d0(sel,0xe)` | **Thermal Borehole** | 0x12 ✓ live |
| `E` 0x45 | `FUN_004d44d0(sel,0xd)` | **Echelon Mirror** | 0x11 ✓ live |

### param_2 (lowercased-char) switch — live-verified too

| key | callee | order |
|---|---|---|
| `Space` 0x20 | `FUN_004d1e90` → `FUN_00529090(unit, −1, 0)` | **run the current order now** (solo synchronous executor, dir −1) |
| `.` | `FUN_004d44d0(sel,8)` | **Airbase** ✓ live |
| `/` | `FUN_004d9470` | **clear + EXPLORE**: cancel; `+17 = 0`; `+4 \|= 0x4000`; broadcast → the dispatcher walks the unit toward the nearest unexplored tile — live `EXEC idx=56 dir=7 mode=3` → `SETTILE (43,9)`; in run 1 unit 57 explored onto an **alien artifact** at (42,12) and the OPERATIONS DIRECTOR modal opened ✓ live |
| `[` / `]` | `FUN_004d44d0(sel,0x11 / 0x10)` | **Lower/Raise Land** ✓ live |
| `_` | `FUN_004d44d0(sel,0x12)` | **Level Terrain** ✓ live |
| `d` | `FUN_004d6100` | **bombard family**: gates + a scan over the 19 improvement types against the tile `+8` mask (`DAT_006938f0[i*8]`), solo tail → `FUN_004cdc70` (the M26 bombard resolver) / netplay `FUN_00583f40` ✓ live entry |
| `m` / `s` / `k` | `FUN_004d44d0(sel,2 / 3 / 7)` | Mine / Solar / Bunker ✓ live (same modes as `M`/`S`/`K` — these keys dispatch via param_2) |

### param_3 (menu-code) chain — static (needs the unit menu pane open)

| menu code | callee | action |
|---|---|---|
| 0x20052 'R' | `FUN_004d8920(sel,0x1b)` | **ROAD TO base**: Former + ocean-domain gates → `FUN_004d6fb0` → `+17 = 0x1b`, `+20 = base index`; opens `#ROADTO` "Pick Road Termination Point" |
| 0x20054 'T' | `FUN_004d8920(sel,0x1c)` | **TUBE TO base** (same, order 0x1c; `#TUBETO`) |
| 0x20046 'F' | `FUN_004d44d0(sel,0xb)` | terraform mode 0xb |
| 0x20048 'H' | `FUN_004d8b20` | join base garrison |
| 0x20044 'D' | `FUN_004d8a30` | **designate toggle**: `+4 ^= 0x80` + broadcast + `s_DESIGNATED/UNDESIGNATED` |
| 0x20055 'U' | `FUN_004d20f0` | **which-upgrade** chooser (`s_WHICHUPGRADE`) |
| 0x30041 'A' | `FUN_004d9120(sel, 3 or 0xc)` | cancel/merge variant by terrain |
| 0x30046/0x3004d/0x3004f/0x30052/0x30053/0x30054 | `FUN_004d9120(sel, 6/5/7/1/4/2)` | the cancel/route-edit family (24 callers — group merge/own/split/transfer menu rows; engineer-gated modes 1/2 check `DAT_006939a8`) |
| 0x30055 'U' | `FUN_004d3950` | **give unit** to another faction (`CANGIVE`/`CANTGIVE`/`CANTGIVEAIR`) |

## 4. Order byte enum (accumulated, `+17`)

| byte | meaning | issuer |
|---|---|---|
| 0 | no orders | `FUN_004d9470` ('/'), `FUN_004d9120` |
| 1 | Sentry / boarding | `FUN_005ab420` (via 'l'), cleared by 'U' |
| 2 | Hold (`+28` = sub-mode 0/10) | `FUN_004d3770` ✓ |
| 3 | Convoy | `FUN_004d94d0` |
| 4..0x17 | terraform/improvement family = **#TERRAIN index + 4** | `FUN_004d44d0`, `FUN_004cce50(unit,k)` |
| 0x18 | queued MOVE (legs at `+20`(x)/`+28`(y) arrays, `+18`/`+19` cursors) | click handler (mode-9 gated, M28), `FUN_004d6fb0('g')`, AI hubs |
| 0x19 | directional/waypoint order (`+20` = dir, `+22/+30` = origin) | Shift+arrow (M27) |
| 0x1b / 0x1c | Road-to / Tube-to base (`+20` = **base index**, not a tile) | `FUN_004d8920` via menu 'R'/'T' |
| 0x200 flag path | support-from-base (`+4 = …|0x200`, `+38 = 10`, `+22/+30` = base coords) | `FUN_004d6fb0(unit, 0x80, …)` |
| 0xfd (−3) | route to home base | `FUN_004d6fb0(unit, −3, …)` via 'I' |

`#ORDERS` (alpha.txt, 9 rows) is the **menu display + hotkey table**, not the enum:
`No Orders -`, `Sentry/Board L`, `Hold H`, `Convoy O`, `Move to G`, `Move >`, `Explore /`,
`Road to r`, `Tube to t`.

## 5. Consequences for the driver (C2)

* **Orders are drivable with plain `xdotool key`** after `windowfocus` — the terraform
  family, HOLD, SENTRY, CONVOY, explore, unload, join-base, road all issue through the
  game's own handlers. A driver can now make the AI face an opponent that builds roads,
  mines, sensors and fortifies.
* Terraform keys on a non-Former print `NEEDTERRAFORMERS` — a useful negative control;
  on a Former they open the `Want_to_terraform`/`TERRAPAY` dialog sequence (modal! —
  service it like M29 services other modals).
* **`/` = explore is a walk, not just a clear** — it can step a unit onto goodies and pop
  modals (artifact → OPERATIONS DIRECTOR). Do not use `/` as a harmless "cancel" key.
* **Modal = key sink (mechanism found)**: while a Script.txt modal is up the pump does not
  call `FUN_00512b40` at all — 19 consecutive keys produced **zero** `KEY` hits in run 1.
  Always check `smac_probe` screen class before a key sequence.
* Live state left as found (then M32-modified): year 2251, our turn, TracerPid 0, HUD
  clean. rec56 explored to (43,9) `flags 0x4014004` mp=3; rec57 sits on the alien artifact
  (42,12) with a completed `0x18`; rec58 (43,11) clean, selected. The artifact modal was
  dismissed with one `Escape` (M29 rule).

## 6. Orders INSIDE the unattended loop (M54c, session 80)

`scripts/smac_play.py --turns N` now ORDERS units itself instead of only ending turns.
`order_step_in_loop()` runs once per player turn, inside `service_turn`'s `hud` branch —
which the `cur_player` / `turn_flags & 2` gate has already established is OUR phase, the
only window where a hotkey is an order and not a key sink (§1 rule 3, §5 "modal = key
sink"). Per candidate unit it pokes the selection slot (`0x91b5bc`), fires ONE real
hotkey, services whatever pane the setter raises, and verifies by the record delta:
**`+17` moving into the byte set that key may produce (§4)**. A screenshot is never the
oracle — §2 says a dropped keypress and a rejected order are indistinguishable from
outside.

What the live probe found on this build (`evidence/m54c_probe.txt`, position
`programs/saves/m54b_clean.SAV` lineage, year 2153, our turn, `orders_mode 1`):

* the six units our faction owns there all decode `type 2` = `Scout Patrol` (class 3) —
  the HUD's own unit panel reads `Scout Patrol`, and NO class-9 record exists for us, so
  `find_former()`'s class-9 filter had nothing to order and the loop silently ordered
  zero. The picker is now `find_actionable()`: the game's own select gate (owner, `+9`
  not frozen, `+40` movement unspent) with `cls` carried for ordering candidates, not for
  filtering them.
* `f` on records 0 and 20 changed neither `+17` nor faction energy — the `NEEDTERRAFORMERS`
  negative control, exactly as §2 predicts for a non-Former.
* `l` took `+17` 0→1 (SENTRY, `FUN_005ab420`) on records 0 AND 3, no pane, no energy:
  a verified order that works on ANY selected unit. So the loop's non-terraform plan is
  `g` (queued MOVE to own base, `0x18`), `l` (1), `h` (2).
* arrows are NOT orders: `Up` and `Right` left `+17` 0 (they drive the map cursor —
  `Right` opened the base pane) and `shift+Up` raised a pane. §1 rule 2 is the cursor
  path; only `§4 0x19` (Shift+arrow, M27) was ever logged as a keyboard move order.
* **Escape at a clean HUD raises "Do you really want to quit?"** — that is how the probe
  poisoned its own first run (every keypress then went into the quit dialog, and every
  capture classified `quit-prompt`). Inside the order step the quit prompt is answered
  with Escape ("Oops, no, wait!"); `Return` there is "Yes, that's an order, mister!" and
  the process is gone.

Cost control (measured): a landing order verifies in ~0.0 s (the byte is read before any
OCR), a dud costs one OCR + pane service. A turn's step is capped by `--order-budget`
(default 35 s) and `ORDER_MAX_ATTEMPTS` (8 keypresses); a key that produces no delta
three times is retired for the rest of the run, and a unit type that refuses every key is
deprioritised, so a Formerless position costs a few keypresses on turn one and nothing
after. `--orders-per-turn` (default 2) and `--no-orders` bound the ambition.

## 7. When the queued MOVE actually runs (M54e, session 82, 2026-10-25)

`g` lands `0x18` and the record carries the route; what M54d could not show is the walk
executing. Measured on this build with `scripts/m54e_probe.py` (pid 484088, base = University
(6,12)); every number below is a `/proc/<pid>/mem` read, reproducible with
`python3 scripts/m54e_probe.py chooser <idx>`:

* **The `SELECT DESTINATION` chooser's OK is the trigger, not EXEC.** Sampling `+17` and
  the whole record live at 100 ms resolution across the OK click: `+0 ms order 24 xy
  (4,12) mp 0 legs 6,12`; `+100 ms order 0 xy (6,12) mp 3`. The byte is written by the
  click handler and consumed by the game's own order pump (`FUN_004ce4a0` → `FUN_00529e70`
  → `FUN_004d1200`, `ghidra_out/shard_012.c:1364`, `shard_013.c:17276`) on the next tick.
  Three TURN COMPLETEs with a hand-parked `0x18` aimed at an empty tile moved nothing, so
  the year flip is not the pump and an `order_final 0` after EXEC proves nothing.
* **The byte window is tens of milliseconds wide.** One read after the click lands on
  either side of it — session 81 recorded `order_after 0` on a walk that had already
  happened. `order_byte_watcher` samples `+17` at ~5 ms from a second `/proc/pid/mem`
  handle *through* the click, so the delta the milestone asks for is the byte itself.
* **The leg arrays survive the pump** (`order 0`, legs still `6/12` after the arrival), so
  the route is still readable after the walk — that is how the loop names the tile to
  verify against, and why it parses legs even when the byte was already consumed.
* **`g` can only name a BASE tile** (§1, §4: the 0x18 branch copies `base[piVar21].x/y` into
  `+20/+28`), and the walker has to stand on a tile the delta tables call a neighbour of it.
  M54d's walker stood at (7,12) — a HALF-tile offset from (6,12), absent from the even-x tables
  `0x67850c`/`0x678990` — and oscillated (6,13)<->(7,12) across three EXECs; every M54e walker
  stood at (4,12) and landed on the first tick. **Occupancy is NOT the blocker** — an earlier
  version of this bullet said it was, which the run's own trace refutes: at turn 9 records 5
  and 8 walked onto (6,12) while records 0 and 2 stood there, so units do stack on a
  destination tile. `m54e_prep.py` changed both variables at once (empty tile, walker moved to
  a real neighbour) and the note blamed the wrong one.
* **`(base.x+1, base.y)` is not a neighbour.** The map packs two columns per tile record
  (`DAT_0092ae14 + (mapw/2*y + x>>1)*0x2c`, even x at `+0`, odd at `+3`) and
  `FUN_00502c40`'s even-x delta tables (`0x67850c` dx, `0x678990` dy) step `(±2,0)` and
  `(±1,±1)`. Live in both directions: a Scout Patrol took (6,12)→(4,12) on one `Left` and
  the made Formers record walked (4,12)→(6,12) on one `g`. M54d's prep stood its unit at the
  non-neighbour, which is most of why its walk line was unmet.
* **Arrows queue nothing on this build.** `Left`/`Right`/`Up`/`Down` (plain and Shift) left
  `+17` at 0 on five different records, with and without the `0x10000` "has moved" bit
  cleared — so §4's `0x19` (Shift+arrow, M27) is not reachable from this save's keyboard
  path, and the cursor path (§1 rule 2) is not an order.

## 8. The colonist FOUNDING (`b`), keyed at last — M54g, session 84, 2026-10-25

* **`b` reaches the order dispatcher only with orders mode on** (`0x91b5b8 != 0`). With it
  off, the same keypress at the same unit on the same tile opens the BASE screen of the base
  near the map cursor and the dispatcher never sees it
  (`evidence/m54g/probe_c_control.json` vs `evidence/m54g/probe_omode.json` — one variable,
  two different panes).
* The dispatcher (`shard_013.c:4384`, `case 0x62`) sends class-9 units to terraform mode 0xe
  and everything else to `FUN_004d1280`, which gates class == 8 (`NEEDCOLONISTS`), then
  domain/elevation (NOTINTRIAD), fungus (FUNGUSDANGUS), monolith, rock (NOTONROCKY:
  `(tile[5] & 0xc0) > 0x40` with elevation > 4), can-act, then BASETOONEAR — a scan of the 8
  delta-table neighbours (`0x6784a0` dx / `0x6784c4` dy, parity-shifted, NOT the Moore
  neighbourhood) for tile mask1 bit 0x1 with an owner nibble < 8. **The tile the unit stands
  ON may itself carry bit 1 and still be a legal site.** `founding_gate()` in
  `scripts/smac_play.py` mirrors all of it live; it predicted every refusal seen and the one
  acceptance.
* On a legal tile the handler raises **#NEWBASE** — "ENTER A NAME FOR YOUR NEW BASE." at y 102,
  the generated name already in the field at y 135, and the HUD's TURN COMPLETE row still drawn
  underneath, so the frame reads `hud` unless the caption band is tested: that is the
  `name-pane` class (frame `evidence/m54g/newbase_pane.png`). **Return accepts the generated
  name; the base record exists 0.1 s later** (`evidence/m54g/probe_found1.json`).
* **The founding writes NO order byte and CONSUMES the unit** — the record list compacts (the
  founding record read x4,y4,type320 immediately after). Its oracle is the BASE ARRAY
  (`0x95DA10`, stride 304, name at +19..51, count `0x985AF4`), not `+17`. The loop issues it in
  `issue_found_for_unit()` and verifies a same-faction base record at the tile the unit stood
  on; `m54a_check_run.py` labels such an order `b->founded` because there is no byte to print.
* Live: `b` at (26,42) (rocky, `tile[5] = 0x83`) did nothing; at (26,43) NEWBASE appeared; in
  the loop at (29,42) the run founded **"Korolev Center"** — `bases_ours 1 -> 2`, energy delta
  0 (`evidence/trace_m54g_20261025_084554.jsonl` turn 0).
* The tile math these gates use is `*(u32*)0x92ae14 + (DAT_00692184*y + x>>1)*0x2c`: **0x92ae14
  is a POINTER and the row pitch is live** — 32 on this 64x64 world (the hard-coded 40 in old
  scripts was an 80-wide map). Indexing the slot itself returns all-zero "tiles".

## 9. The `g` chooser's ROWS, and what a walk's evidence has to be (M54h, session 85, 2026-10-25)

**Geometry** (`evidence/m54h/chooser_g60b.png` — a unit garrisoned on Korolev Center (29,42)
while we own two bases; `scripts/m54h_probe.py` produced it):

* Caption `SELECT DESTINATION` at y 102. The destination rows are **full-width periwinkle
  bars** (fill 159..638) on the bands y 125-139 and 144-158 — a 19 px pitch. OCR reads the
  HIGHLIGHTED row's text reliably and the other row's text only sometimes (the same frame
  read "University Base" in one capture and nothing in another), so text alone cannot drive
  the pick.
* The button band is **five 92-px bars on one pitch** — Sort: Name / Sort: Size / Sort: Dist /
  OK / CANCEL at centres 209/305/401/497/593 — and it **moves down with the row count** (y 162
  with one row, y 181 with two), so any hard-coded OK y is wrong for a two-row pane.
  `bar_bands()` / `chooser_rows()` / `chooser_buttons()` in `smac_play.py` tell the two apart:
  a row band's groups merge into a ~480 px span, a button band is >= 4 groups of one width on
  an even pitch. The merged span alone cannot do it — five buttons span 163..638, exactly like
  a row.
* **Clicking a row only HIGHLIGHTS it**: 0.9 s after the click `+17` and the legs were
  unchanged (`evidence/m54h/probe_chooser_walk1.json`, stage `row_click`).
* **OK (the 4th button) is what lands the order**: `+17` went 0 -> 0x18 87 ms after the click,
  the record carried legs `[28,42]`, and the pump stepped the unit (29,42) -> (28,43) with
  `+40` = 3 spent (stage `ok_click`).
* **CANCEL (the 5th) closes the pane and writes nothing**: 60 samples of `+17`, all 0, and the
  pane was gone (`evidence/m54h/probe_chooser_cancel67.json`).
* **The pane lists BOTH own bases even when the unit stands on one of them.** M54c's rule
  "`g` refuses a unit on our base" is RETRACTED (the M54c evidence was a one-base position:
  the only row it could list was the unit's own tile). What the pane cannot do is name the
  tile under the unit's feet and mean anything.
* The `Distance:` column reads 0 for both rows — it is the CURSOR's distance (M54d), not the
  unit's, and carries nothing usable for choosing.

**What a walk's evidence has to be:**

* **Index is not identity**: the record array reshuffled between turns twice in one session
  (the unit ordered at (29,42) was index 67 at order time and index 52 a turn later). Match on
  (type, tile) or on counts, never on an index carried across a turn.
* "A record of this type sits on the destination tile" is **worthless when identical units were
  already parked there** — five Scout Patrols sit on University Base. `verify_moves` now
  requires the DELTA against the baseline the order itself recorded (`order_counts`): the
  same-type count at the destination goes UP and at the origin goes DOWN.
* **A queued MOVE can outlive the turn that ordered it** (3 MP spent on the first step, the
  last leg left in the record for a later turn), so `PENDING_WALKS` /
  `verify_pending_walks()` re-read the same evidence on later turns and report an arrival once,
  on the turn it lands.

**UNRESOLVED (measured, not explained):**

* The legs' last point is **not always the ordered base**. In the loop, two `g` orders whose
  row click was recorded against the University Base row put legs `(14,56)` — House of Martyrs,
  a BELIEVER base — and `(17,55)` (not a base at all; the base count fell 19 -> 18 during the
  same run) into the records (`evidence/trace_m54h_20261025_093424.jsonl` turns 0-1), while the
  identical click in a probe put `(28,42)` = University Base in the same field. Either the
  pane's list is not one-row-per-own-base in every state, or the leg array holds something
  other than the destination. The row<->base mapping (default Sort: Name) is an **assumption**:
  both frames seen so far are equally consistent with nearest-first.
* `l` (SENTRY) pressed on a unit carrying a pending 0x18 landed nothing (`+17` stayed 24,
  `panes ['unknown']`) — cause unresolved: an `unknown`-classifying HUD frame swallowed the key,
  or the game refuses the key on an ordered unit. Not isolated (two variables changed).
* **A clean HUD whose TURN COMPLETE row fails to OCR classifies `unknown`** (MENU read at
  (61,369), COMMLINK read, `region_colors 167`, `complete` absent) and with `--no-escape` the
  loop idled a whole turn budget at it while the year sat unmoved in OUR phase. Fallback added:
  in our phase, chrome present, no bar band at y 145-200, `HUD_BLIND_S` elapsed -> click the
  button at its measured coordinates. Proven on one turn (2160 -> 2161,
  `evidence/trace_m54h2_20261025_094339.jsonl`); not yet exercised across a multi-turn run.

## 10. Attribution, the SENTRY byte, and the count baseline (M54i, session 86, 2026-10-25)

**`+17 = 1` is SENTRY, not "no order" — a sentry PATROLS ON ITS OWN every round.**
Sessions 84-85 "parked" decoys by poking `+17 = 1` and called them parked because the
DRIVER skips order bytes != 0; the game was giving them orders the whole time. Measured in
`evidence/trace_m54i_run3_*.jsonl`'s rounds: the five "parked" records migrated from
(28,42) to (28,43) and their leg arrays were rewritten turn after turn
((17,26) -> (17,24) -> (13,17)...) — patrol paths. `scratch/m54i_park.py` parks with 1 and
is therefore a SENTRY-ify, not a park. The inert byte is **2 (HOLD)**: the pump leaves it,
`find_actionable` skips it, a held unit sits put (`scratch/m54i_hold.py`, read back on a
second handle).

**The count baseline must be the PRE-PRESS snapshot** (`snap_before`), not a read after the
chooser's OK: the pump runs as the OK is answered (section 7), so a post-OK read sees the
origin ALREADY vacated — `evidence/trace_m54i_run4_*.jsonl` turn 0 carries
`order_counts {dest 4, src 0}` — and "origin count falls" (`still < s_before`) can then
never fire no matter how cleanly the walk lands. Fixed in `issue_order_for_unit`.

**Which record a keypress ordered is answered by DIFF, never by an index**
(`diff_order_records`, `scripts/test_walk_diff.py` 13 cases): the proof of a FRESH order is
a 0 -> byte transition with CHANGED legs on the watched record slot (watcher samples, or —
when the chooser was answered by its default button, e.g. Return on an `unknown`-classifying
pane — the two reads bracketing the press). A rival makes it confounded:
* stale legs (the arrays survive the pump) claim nothing;
* a row at ANOTHER index wearing the byte + route we watched is a TWIN -> confounded;
* a signature row on our OWN slot is our record only if the start tile is VACATED of our
  pre-press record — if our unit is still parked on its start tile, the slot's signature
  belongs to a look-alike (session 85's "legs naming bases nobody ordered" is exactly this);
* when confounded, `dest` stays None — the trace says so instead of guessing.

Live (run4 turns 0-2, `evidence/trace_m54i_run4_*.jsonl`): `g` verified with
`walk_diff.attributed True, confounded False`, dest read from the changed legs of the
record the press changed — attribution WORKS in the loop.

**The war is a variable too:** from 2167 to 2187 (runs 3-4) other factions founded 7 bases,
TOOK University Base (bases_ours 2 -> 1) and killed 5 of our 10 units — while the checker's
`--min-our-bases 2` floor was still reading 2 at the run's start. A 6-turn acceptance run
needs a position that quiet to start with.

## 11. Who owns the map cursor, and why a `g` falls through (M54i2, session 87, 2026-10-25)

Measured live at 2158 (pid 1053556) with `scratch/m54i2_cursor.py` / `m54i2_scan.py` /
`m54i2_om.py`; every claim below is a `/proc/<pid>/mem` read-back, not a screenshot.

* **There are (at least) three cursor variables and the pokes do NOT stick on any of them.**
  - `*(u32*)0x7cdecc + 0x1dd9c / +0x1dda0` — the map WINDOW's cursor fields (the tile the
    info panel reads: poking them changed the panel's `(29,41)` readout). A poke here was
    read back correct on a second handle, yet the game rewrote it to its own value within
    ~3 s (`cursor end` lines in the probe); `FUN_005a071e` (shard_015.c:16585) writes them
    when one of our units MOVES.
  - `DAT_0091b5f0 / DAT_0091b670` at byte offset `DAT_0091b5e8` — the array the tile
    handlers read (`FUN_00511960`, shard_013.c:4017). Poking the cell the index selects
    (both the `index*4` int reading of m54e_probe and the `+index` u16 reading of
    shard_012.c:6463) was likewise re-synced by the game within 1.5 s.
  - `DAT_0091b5e8` / `+0x91b5ec` are counters that climb on their own (20 -> 21 -> 22
    across two `Right` presses in the differential scan); the array cells are a history
    the game appends to, not a slot the driver can park.
  **Conclusion: the cursor is GAME-OWNED. Do not try to position it by poke.** It moves on
  the game's own events (a unit arriving — `FUN_005a071e` — the AI/chooser cycling). The
  only durable cursor placement is the game's own: order a unit somewhere and the cursor
  follows the arrival.
* **What decides whether `g` is an ORDER at all is §1 rule 3, not the cursor.** With
  orders mode off (`0x91b5b8 == 0`) or the game's selection unset (`SEL < 0`), the key
  falls to `FUN_00511960` (the cursor-tile handler): cursor on a base tile -> the BASE
  SCREEN / "will automatically forward" dialog; cursor elsewhere -> nothing. That is
  session 86 run5 turn 0's "cursor placement" failure re-attributed: the dispatcher never
  saw the key. The driver's recipe (poke `SEL_G`, poke `0x91b5b8` like line 2224 does for
  founding, THEN press) is the working path; the poke sticks because the keypress follows
  within the same frame the game takes to re-sync.
* **`sp.focus()` is a silent NO-OP while `sp.WIN` is None.** Scratch scripts must do
  `sp.WIN = sp.find_window()` first or every `sp.key()` lands on whatever X thinks is
  focused (this ate the first hour of session 87: "keys don't land" was a focus bug, and
  the arrow presses that DID land were the game's own cycling, not mine).
* **Poke-moved units are invisible to the cursor-tile finder.** A record poked to a new
  x,y stops being found at its new tile (`g` at a cursor on the tile found nothing for a
  poked unit; the untouched garrison units still open their base screen). Content-identity
  survives a poke; the game's tile occupancy does not. Prep pokes are fine for FOUNDING
  (the loop orders the poked record via the dispatcher); they are NOT fine for making a
  unit "stand" somewhere the game must then find it.
* **Driver policy for the two fall-through shapes** (`move_order_needs_retry`, tested by
  `scripts/test_walk_diff.py` cases 14-18): a MOVE whose OK landed the byte with NO route
  (`verified` and `dest is None`), or whose pane list contains `base` (the key fell to the
  cursor handler), is RE-RAISED, at most `MOVE_ORDER_RETRIES = 2` times, every attempt
  recorded in the trace's `attempts` list. Non-MOVE keys never retry.

## 12. The step table preserves (x+y) parity — why every walk before M54i2 failed (session 87, 2026-10-25)

* **The table.** `dx` at `0x67850c`, `dy` at `0x678990`, 21 int32 pairs; the adjacency
  loop runs `do { ... } while ((int)local_2c < 0x54)` in 4-byte steps
  (`ghidra_out/shard_013.c:21829-21868`). Live read at 2159 (pid 1110005):
  `(0,0) (1,-1) (2,0) (1,1) (0,2) (-1,1) (-2,0) (-1,-1) (0,-2) (2,-2) (2,2) (-2,2)
  (-2,-2) (1,-3) (3,-1) (3,1) (1,3) (-1,3) (-3,1) (-3,-1) (-1,-3)`. §7's "(±2,0) and
  (±1,±1)" is the short subset; the long steps exist too. **Every pair preserves
  (x+y) parity**, so a queued MOVE can only ever arrive at tiles of its start tile's
  parity. University Base (28,42) sums 70 (even): every walker sessions 84-87 stood
  at (29,42) or (28,43) (71, odd) could not reach it — the "oscillation" was
  geometry, not the cursor, not occupancy, not pump timing. The real neighbours of
  (28,42) include (29,41), (27,41), (27,43), (29,43), (26,42), (30,42), (28,40), (28,44).
* **A chooser-queued order executes on the game's own TURN COMPLETE cycle.**
  `scratch/m54i2_pump.py` (2158, one actionable record, everything else HELD, read
  back on second handles): the record at (28,43) with order 24 and leg (28,42) was at
  (29,42) with order 24 and `+40` = 3 spent at the next phase start; every HELD record
  sat put with `+40` = 0. §7's "three TURN COMPLETEs moved nothing" holds for a
  HAND-POKED byte only — the pump runs orders the chooser's OK registered, and the OK
  is only the pump's nearest visit. `+40` = mp SPENT this round, re-zeroed at the next
  phase start for units that did not move again.
* **The driver's contract (session 87, proven by run3/run4):** only order `g` when a
  same-parity own base other than the unit's tile exists (`walk_parity_ok` gate in
  `can_walk` and in `answer_dest_chooser`'s target pick); prefer candidates standing
  on a `table_neighbors` tile of such a base — they land on the pump's next visit.
  `verify_moves`/`verify_pending_walks` read `mp_after` as the MAX mp over same-type
  records on the destination tile: garrison/HELD units and base-produced units sit at
  0 there (run3 census), so a nonzero max is the arrival's own spent movement.
* **The proof runs.** run3 (2159→2164): rec at (29,41) ordered to University Base —
  attributed True, legs [(28,42)], census 2165: that record on (28,42), order 0,
  moved bit set — landed in memory while the checker scored it false (the old
  `hits[0]["mp"]` read a held garrison). run4 (2165→2171): rec at (28,43) ordered to
  Korolev Center (29,42) — `m54a_check_run.py ... --min-our-bases 2 --min-moves 1
  --min-own-base-arrivals 1` -> `PASS`, `moves 1 LANDED of 1 ordered walks`,
  `t[28,43]->[29,42] mp+3`, dest_count [2,3], src_count [1,0].

## 13. The game AUTO-SENTRIES an order-0 unit across the round boundary (M54j, session 88, 2026-10-25)

**A unit left waiting at `+17 = 0` between rounds comes back a SENTRY (`+17 = 1`) and
patrols on its own** — the setup that leaves the loop's chosen walker actionable before
the run does not survive to the loop's ordering window. Measured (run1,
`evidence/trace_m54j_run1_20261025_155011.jsonl`): `scratch/m54j_setup.py` read back on
a second handle exactly ONE actionable record, rec 37 at (20,42), order 0, legs cleared;
turn 1's order step found its candidate wearing byte 1 (`g`/`l`/`h` all pressed on a
byte that was already 1), and by the census after the run no record stood at (20,42) —
the sentry had patrolled away. `scratch/m54j_probe.py` reproduced the same drift with a
single poked record. Byte 2 (HOLD) is the only order that survives the round (§10: the
pump leaves it), so:

* **The driver's contract (M54j):** when `find_actionable` returns nothing, the order
  step re-activates a HELD walker **in-phase** — `held_walk_records` (our `+17 = 2`,
  not frozen, mp 0) filtered by `pick_reactivation`: off our own base tiles (there `g`
  raises the BASE SCREEN, §11), with a same-parity own base that is not the tile under
  its feet (§12), sorted so a unit already standing on a legal step of such a base
  (a one-step arrival) goes LAST — the point of the exercise is a multi-leg route. The
  re-activation poke (`+17` 2 -> 0) happens in the same window as the keypress, before
  any round boundary can eat it. Tests: `scripts/test_walk_diff.py` cases 25-28.
* **Our two bases are OPPOSITE parity** (University 28+42 = 70 even, Korolev 29+42 = 71
  odd), so with both alive EVERY tile matches exactly one base's parity — "wrong parity
  for every own base" only happens when a base is gone. The records `pick_reactivation`
  actually drops are own-base garrisons (case 27). Do not hand-compute these sums under
  pressure; three fixtures were wrong before the arithmetic was checked mechanically.

## 14. THE IN-PHASE PUMP BURST + READING A QUEUED MOVE OFF MEMORY (M54k2, session 90)

* **A queued MOVE can execute INSIDE our phase.** run1 (trace_m54k2_run1, turn 1):
  the chooser OK handed the unit to the pump, `turn_flags & 2` stayed set on OUR side
  (`cur_player 3`), and the game ran the whole 4-step route as back-to-back tf2 rounds
  (~4.6 s/flip, 2182->2187) *inside one driver turn record* — the year deltas went
  {1:5, 5:1}. The driver treats tf&2 as an AI round (the turn loop never clicks during
  it), so the burst is invisible to the turn boundary; only the order step's own window
  made turn 1 swallow it.
* **The candidate slot goes stale DURING the burst.** Each flip compacts the array, so
  the modal loop's byte oracle (`UNIT_ARR + idx*52 + 17`) can read a DIFFERENT record
  (run1: byte 2) while the walker wears 0x18 the whole route. `queued_rescan`
  (`scripts/smac_play.py`) reads the queue off content instead: exactly ONE of our
  records wears a wanted byte that NONE wore in the pre-press snapshot, AND its leg
  array names one of OUR bases (queue-time legs are the ordered destination; a
  mid-walk rewrite names a waypoint — (61,9)/(61,10 — waypoint garbage is NOT
  evidence). Unique + fresh + base leg = verified queue, attributed, not confounded;
  anything else says nothing. Tests: `scripts/test_walk_diff.py` cases 34-37. run3's
  `g` landed through exactly this path (pane classified `dialog`, `n_samples 0`).
* **After the turn's order budget is spent, the game AUTO-ADVANCES at ~8 s/round**
  when nothing is left actionable — and the turn loop's next iteration costs a
  freeze+OCR (2-15 s), so TWO rounds can flip between its year checks (run2 turn 5:
  {1:5, 2:1} -> checker `FAIL year did not move +1 on turns [5]`). Both order-step
  exits now poll `year() != y0` at 0.2 s (capped 20 s) before continuing: the flip is
  cheap to watch from memory, and the turn closes on it. run3: {1: 6}.
* **`turn_flags` gained a persistent 0x100000 bit around 2196** (1048578 = 0x100002
  at run1's end, still set at run3's end at 2204). The driver's `tf & 2` AI test and
  the blind gates' `& 2` mask are unaffected (run3 passed with it set); nobody has
  found what sets it. Do not treat it as nonsense state.
