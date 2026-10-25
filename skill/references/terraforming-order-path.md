# Terraforming order path: issue → pay → store → execute

How a Former's terraform order travels through `terran.exe`, what is proven, what is still
open, and the harness that drives it. Project docs (authoritative, updated per session):
`~/reverse/smac/turn_driver.md` §M35, `NAMED.md`, `ORDERS.md`.

## The setter `FUN_004d44d0(unit, mode)`

`mode` = alpha.txt `#TERRAIN` index; the stored order byte is `mode + 4`. The function is
reached from the order menu (keymap → `FUN_00512450` → setter) and from the HOLD setter's
siblings.

Stage order:
1. **Tech gate** — `call FUN_005a7520(mode, domain, player)` at `0x4d4837`. Returns
   unlocked. Fails → advisor branches at `0x4d486e` (`HASROAD` / `HASFARM` /
   `NOTUNTILTECH`).
2. **Mode-specific eligibility** — per-mode case blocks. Farm's `0 → 0xa` remap
   (`tile+8 & 0x20 ∧ terr >= 4`, shard_012.c:108-113) plus the ability `0x2000` gate
   (line 182) explain most "eligible-looking tile rejected" cases.
3. **Already-ordered check** — `0x4d54c3 call FUN_005a6330(unit, 9, mode+4, -1, -1)`:
   walks `+17` and the `+50` cargo chain; nonzero **skips the entire payment path**.
4. **Cost** — `0x4d54df call FUN_004cc7b0(unit, x, y)`, dynamic (a raise at elev 4 cost
   **9**, while alpha.txt says 12); 0 means free, skip payment.
5. **Affordability** — `0x4d558f cmp [0x94d650 + player*0x82f], cost; jl 0x4d55cb`: when
   the pool is short the picker is **never shown**, the answer reader runs anyway and
   returns "declined".
6. **Panes** — `0x4d5572 call FUN_005f0583` = `TERRACOST` caption ("It will cost N
   credits…", pane id `TERRACOSTUP`); `0x4d55b3 call FUN_005f0583` = `TERRAPAY` picker
   (`Cancel action.` / `Expend $NUM0 credits.`). Both are Script.txt panes; the picker
   **blocks inside the setter**.
7. **Answer** — `0x4d55d5 call FUN_005f1394`; zero → `0x4d5689` (declined).
8. **Debit** — `0x4d561a` writes the new pool value (synchronous), then `0x4d5623 call
   FUN_005843b0` (energy broadcast → **enqueued** 0x2101 with idx = player), then
   `0x4d562f call FUN_0050fc20`.
9. **Footprint pass** — `0x4d5634` is the common continuation (paid *or* skipped). Height
   comes from `tile+0>>5`; the per-mode level ladder picks a footprint count from
   `0x678e08`, then the tiles are walked with `0x528930` (netplay-only), `0x555030` and
   `0x4c2be0`. Any of them returning nonzero jumps to a failure block
   (`0x4d58dc` / `0x4d59c7` / `0x4d5b0d` region) that shows a pane and returns via
   `0x4d5add` — **after the money was taken, and with no refund observed**.
10. **Store** — `0x4d5bbf mov [edx*4+0x933289], cl` (order byte = mode+4), then
    `0x4d5bc6 call FUN_00584350(unit)` → `FUN_0052a720` enqueue 0x2101(idx=unit) →
    `FUN_005262e0` drain → `FUN_0052bce0` dispatcher → solo executor path. A `TERRAFORM`
    tutor pane follows.

## Proven live

* `]` (raise) on a selected Former with the tech bit published produced, in order:
  `TERRAF mode=0x10`, `TECHCHK unlocked=1`, `PAYPATH`, `ORDERCHK 0`, `COST 9`,
  `TERRACOSTPANE` + `PANE id=TERRACOSTUP`, `PAYPANE` + `PANE id=TERRAPAY`, `PAYTAKEN`,
  `DEBIT 40→31`, `ENQ q=11 idx=3 type=0x2101`, then `PANE id=TERRAFORM` — and **no STORE,
  no BCAST**, order byte still 0, tile unchanged.
* `PAYDECLINED` is what a cancelled picker looks like; it is not evidence the order was
  refused.
* The energy broadcast enqueues with **idx = player**, the order broadcast with idx = unit;
  that is how to tell the two 0x2101 events apart in the log.

## Driving the picker (harness)

`scripts/m35_paypicker.py --tag <tag>`: clean-screen preflight → (optional) publish a tech
bit through `/proc/<pid>/mem` with TracerPid 0 → arm `scripts/m35_pay.gdb` → press the key →
wait for `TERRACOSTPANE` → let the caption pane close itself → wait for `PAYPANE` → OCR the
pane, click the row whose text starts with `expend`, then the OK bar ~26 px below, ≥1.2 s
apart → wait for `PAYTAKEN`/`PAYDECLINED` → record post-state to `evidence/<tag>_paypicker.json`
with screenshots.

Pane ids are readable from a breakpoint on the pane-show function: the id string pointer is
at `$esp+8` when `FUN_005f0583` is entered, so a generic `PANE` breakpoint prints
`TERRACOSTUP` / `TERRAPAY` / `TERRAFORM` and saves guessing which pane is up.

## Publishing a tech (test-only)

Faction tech bits are **one byte per tech id at `0x985c1c`, bit = `player & 0x1f`**. To let a
player use a gated mode: `set bit (player&7) of byte (0x985c1c + tech_id)`. Verify by
re-reading; the game does not rewrite the bit. Clear it the same way when done. Do this
**before** attaching gdb.

## Open

* Which footprint check refuses a nominal raise (candidates above; `0x528930` is ruled out
  by the solo switch), and whether a refusal is supposed to refund the debit.
* Whether a raise's footprint count depends on the level *above* the tile (the ladder reads
  `height+1`), which would make "level 6" tiles and "level 4" tiles reject for different
  reasons.
* Tile records carry **two tiles** (`x>>1`); all observed reads use the first half only.

## Walking: the queued MOVE (`0x18`) and when it runs (M54d/e, session 82)

`g` = `FUN_004d6fb0(sel, 0x18, 0)`: destination is always one of OUR base tiles (the branch
copies `base[piVar21].x/y` into the leg arrays `+20`(x, 4 shorts)/`+28`(y), `-1`-terminated,
`+17` = 0x18) after a `SELECT DESTINATION` chooser pane. What the docs never said:

* **The chooser's OK click is the trigger.** The click handler stores the byte; the game's own
  order pump (`FUN_004ce4a0` → `FUN_00529e70` → `FUN_004d1200`) consumes it on the next tick.
  Sampled live at 100 ms: `+0 ms order 24 xy(4,12) mp 0 legs 6,12` → `+100 ms order 0 xy(6,12)
  mp 3`. The **year flip is not the pump** — a hand-parked `0x18` survived three TURN COMPLETEs
  without moving. So `order_final 0` after EXEC proves nothing; watch `+17` *through* the OK.
* **The window is tens of ms.** A read after the click lands either side of the consumption;
  `smac_play.order_byte_watcher` samples `+17` at ~5 ms from a second `/proc/pid/mem` handle
  across the click (a single read is a coin flip).
* **Legs survive execution** (`order 0`, legs still name the destination), so the route is the
  post-hoc evidence: verify the record sits ON the tile its own last leg names.
* **The walker must stand on a real neighbour of the named base tile.** Standing at
  `(bx+1, by)` — a half-tile offset, not in the delta tables — the walker oscillated between
  two neighbours across three EXECs; the same order from `(bx-2, by)` landed on the first tick.
  Occupancy is NOT the blocker (a trace shows two units walking onto a tile where two others
  already stood); an earlier version of this note blamed it and was wrong. A walk needs: a real
  neighbour start tile, `+17`/`+40`/legs cleared, `mp` 0, and our own base tile as the target.
* **`(base.x+1, base.y)` is NOT a neighbour** — two columns live in one tile record
  (`(mapw/2*y + x>>1)*0x2c`, even x `+0`, odd `+3`) and `FUN_00502c40`'s even-x delta tables
  (`0x67850c` dx / `0x678990` dy) step `(±2,0)` and `(±1,±1)`. Proven live both ways: `Left`
  moved a Scout (6,12)→(4,12); one `g` walked a Formers record (4,12)→(6,12). Standing a unit
  at `base+1` looks adjacent and is not.
* **Arrows queue no order** on this build (`+17` unchanged for Left/Right/Up/Down plain and
  Shift, five records, with and without the `0x10000` moved-bit cleared). §"0x19 = Shift+arrow"
  is a static note, not a reachable keyboard path here.
* **The type is the u16 at `+10`; `+4` is a flags dword.** Settled from the binary in M54f:
  `shard_012.c:2150` does `iVar8 = *(short *)((int)&DAT_00933282 + rec_off) * 0x34;` and then
  reads the class byte from `0x98ADAF[iVar8]` — `DAT_00933282` is `UNIT_ARR + 0x0A`, and the
  element is a SHORT. Cross-checks: a selected record reads "Scout Patrol" on the panel with
  `+10 = 2`, and alpha type 2 / class row 2 both say Scout Patrol. `+10` values of 128/256/320
  belong to EMPTY STALE SLOTS (`type < 24` before counting a record as a unit).
* **The unit panel is not an oracle on demand**: writing `SEL_G` does not redraw it (three
  different selections read byte-identically), and a mouse nudge does not either. Trust the
  panel only at load or after a real in-game selection.
* **Founding a base IS keyed: `b`, and only with orders mode on** (M54g, session 84).
  With `0x91b5b8 == 0` the key never reaches the order dispatcher — it opens the BASE screen
  of the base near the cursor (measured: same unit, same tile, one variable). The dispatcher
  (`shard_013.c:4384` case 0x62) sends class-9 units to the borehole mode and everything
  else to `FUN_004d1280`, which gates class 8 (`NEEDCOLONISTS`) then the tile. On a legal
  tile it raises NEWBASE — caption "ENTER A NAME FOR YOUR NEW BASE." at y 102 with the
  generated name already in the field and the HUD's TURN COMPLETE row still drawn under it,
  so classify() says `hud` unless the caption is tested (`name-pane` class, frame
  `evidence/m54g/newbase_pane.png`). **Return accepts the generated name; the base record
  exists 0.1 s later.** The founding writes NO order byte and CONSUMES the unit — the record
  list compacts, so a record index is not an id.
* **Founding tile gates** (`founding_gate()` in `scripts/smac_play.py` mirrors them live):
  NOTINTRIAD, FUNGUSDANGUS (fungus + elev>3), NOTONMONOLITH, NOTONROCKY ((b5&0xc0)>0x40 and
  elev>4), BASETOONEAR. BASETOONEAR reads ONLY the 8 delta-table neighbours (mask1 bit 0x1,
  owner nibble < 8): the tile a unit stands ON may keep bit 1 and still be a legal founding
  site, and the delta tables are parity-shifted, so "adjacent" is not the Moore 8-neighbourhood.
* **The tile array is behind a POINTER and the row pitch is LIVE**:
  `*(u32*)0x92ae14 + (DAT_00692184*y + x>>1)*0x2c`. On this 64x64 world DAT_00692184 is 32 —
  the old hard-coded 40 was an 80-wide map. Indexing 0x92ae14 itself reads pointer slots and
  returns all-zero "tiles" under a base that visibly exists.

## The `g` chooser's ROWS and what a walk's evidence has to be (session 85, 2026-10-25)

* `g` on a unit GARRISONED on our own base opens the chooser and it lists **every base we own**
  (two rows for two bases): rows are full-width periwinkle bars (fill 159..638) on bands
  y 125-139 and 144-158, a 19 px pitch; the five-button row Sort: Name / Sort: Size / Sort: Dist
  / OK / CANCEL sits at centres 209/305/401/497/593 and **moves down with the row count** (y 162
  with one row, y 181 with two). `bar_bands`/`chooser_rows`/`chooser_buttons` in `smac_play.py`
  tell them apart by uniform width + even pitch, never by merged span (five buttons span
  163..638 exactly like a row).
* Clicking a row only HIGHLIGHTS it (no `+17`, no legs). OK lands the order (byte 0x18 ~90 ms
  after the click) and hands the unit to the pump; CANCEL (last button) closes the pane and
  writes nothing. The `Distance:` column is the CURSOR's, not the unit's — it read 0 for both
  rows, so it cannot drive a pick. Whether the list is Sort: Name or nearest-first is UNMEASURED.
* **Record index is not identity and the array GROWS mid-run** (a base building a unit shifts
  every later index; `units_ours 9 -> 10` inside one 6-turn run). Snapshot all our records before
  the keypress and diff; never carry an index across a turn.
* "A record of this type sits on the destination tile" proves nothing when identical units were
  parked there — require the DELTA (same-type count UP at the destination, DOWN at the origin)
  against the baseline the order itself recorded, and re-read an unfinished walk on later turns.
* **Two wedges, both silent**: (1) a clean HUD whose TURN COMPLETE row fails to OCR classifies
  `unknown` (MENU/COMMLINK read, `region_colors` ~167) and with `--no-escape` the loop idles a
  whole turn budget; (2) an advisor dialog wearing the HUD chrome (OPERATIONS DIRECTOR)
  classifies `hud` and swallows TURN COMPLETE clicks landing BEHIND it. Fixes: click the button
  at its measured coordinates when it is our phase, the chrome is present and no bar band exists
  at y 145-200; and answer any `hud` frame that has a caption-band line (one word >= 6 chars, or
  >= 2 words >= 4 chars at y 90-118) with Return before anything else.

## The step table and (x+y) parity (M54i2, session 87, 2026-10-25, PASS)

* `dx` at `0x67850c`, `dy` at `0x678990`, **21 int32 pairs** (`while ((int)local_2c < 0x54)`,
  shard_013.c:21868). Live read: `(1,-1) (2,0) (1,1) (0,2) (-1,1) (-2,0) (-1,-1) (0,-2)
  (±2,±2) (3,±1) (1,±3) (-3,±1) (-1,-3)` + `(0,0)`. **Every step preserves (x+y) parity** — a
  queued MOVE can only arrive at tiles of its START tile's parity. Walkers stood at (29,42)/
  (28,43) (sum 71) ordered to University Base (28,42) (sum 70) oscillate forever; sessions
  84-87's "walks don't land" were geometry, not cursors, occupancy, or pump timing. Order `g`
  only when a same-parity own base (other than the unit's tile) exists; prefer candidates on a
  table-neighbour tile — they land on the pump's next visit.
* A **chooser-queued** 0x18 executes on the game's own TURN COMPLETE cycle (poked bytes never
  do): one actionable record at (28,43) with leg (28,42) came back at (29,42), order still 24,
  `+40` = 3 spent, while HELD records sat put at `+40` = 0. `+40` = mp SPENT this round,
  re-zeroed at the next phase start for units that did not move.
* The cursor is GAME-OWNED: three cursor variables, no poke sticks (window fields
  `*(u32*)0x7cdecc+0x1dd9c/+0x1dda0`; `DAT_0091b5f0/670`; `DAT_0091b5e8` is an append-counter).
  `g` is an order only via the dispatcher pokes (SEL_G + `0x91b5b8`); else it falls to the
  cursor-tile handler (base tile -> base screen, else nothing). A poke-MOVED unit stops being
  found at its new tile by the game's own occupancy. `sp.focus()` is a silent NO-OP while
  `sp.WIN` is None — scratch scripts must `sp.WIN = sp.find_window()` first.
* `mp_after` for a landing must be read as the MAX mp over same-type records on the destination
  tile, never `hits[0]` (index order): garrison/HELD units and base-PRODUCED units sit at mp 0
  there, so a nonzero max is the arrival's own spent movement. The leg array is a waypoint —
  the chooser's named base is the ordered destination.

## Multi-leg walks, the auto-sentry, and who may answer the turn (M54j, session 88, 2026-10-25)

* **The game AUTO-SENTRIES an order-0 unit that waits across the round boundary** (`+17` 0 -> 1,
  then it patrols on its own): a setup that leaves the chosen walker actionable BEFORE the run is
  gone by our phase (`scratch/m54j_setup.py` + run1). Byte 2 (HOLD) survives the round; an
  order-0 unit poked DURING the AI round is still byte 0 and unmoved when our phase opens
  (`scratch/m54j_probe2.py`). So: pre-arm the walker mid-AI-round (driver `PRE_ARM` hook) or
  re-activate a held walker in-phase (`pick_reactivation`), never leave 0s waiting between rounds.
* **An all-HELD human phase auto-advances unseen**: with nothing actionable the game draws
  "Year NNNN: No units need new orders. Press ENTER" and ends the turn in seconds — TURN COMPLETE
  stops OCR-ing, the frame classifies `unknown`, and 4-6 of 6 turns can burn with the order step
  never running. The order step must fire on the FIRST memory-verified our-phase frame (blind-HUD
  gate), not after the 25 s blind-click delay.
* **A queued 0x18 walks MULTI-LEG on its own**: run4 watched one record (49,33) -> (47,33) ->
  (43,35), order still 24, legs still [(28,42)] — ~2 tiles/round, terrain-willing. The order byte
  stays 24 until arrival; the unit is NOT actionable mid-walk and needs no new orders.
* **Arrival = THE WALKER on the destination, identified by its ROUTE** (the record wearing the
  ordered leg array), plus mp spent, plus the origin tile empty of that type. A same-type
  headcount is worthless when the destination is our base — six identical garrisons made
  `verify_moves` print ARRIVED for a unit 2 tiles into a 21-tile walk. For carried (multi-turn)
  walks the pre-press count baseline is stale by design: do not require the dest count to rise
  against the press.
* **LOAD browser path typing can mangle** (`m54a_load.py --relaunch`, wine 10.20-staging): the
  LOADING ERROR echoed `\h`->`Eh`, `\n`->`in` — backslashes dropped, following chars swapped —
  and "unable to find file" repeated. The browser OPENS IN THE SAVES DIR: dismiss the error
  (Return), clear the NAME field, type just the FILENAME (`m54b_clean.SAV`), OK — the file is in
  the visible list. Then the difficulty confirm at (290,391).
