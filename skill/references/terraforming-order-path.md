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