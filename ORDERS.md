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
