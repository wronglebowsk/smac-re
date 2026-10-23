# M53b — the type-record `+41` byte is the COST FACTOR (not a weight, not turns)

Record: `unit type record = 0x98ad88 + type·52`. `+41` = `0x98adb1`.

## Verdict

`+41` is the unit type's **cost factor**: the alpha rules-file `#UNITS` **Cost** column when the row
supplies one, otherwise the value `FUN_00595820` computes from chassis + weapon + armor + reactor +
ability surcharges. Everything the game charges or prints for a type is
**`FUN_004e40a0(owner, 1, -1) × +41`**, and in the live game that multiplier is exactly **10 = 100 %**,
so **1 unit of `+41` = 10 minerals**. It is not a build-turn count (turns come from `FUN_005ac8c0`,
`shard_015.c:23672`, which returns a triad rate and never touches `+41`) and not an independent AI
weight (the planner reuses the same cost, see §Consumers).

## Chain (VERIFIED unless marked)

1. **Single writer.** `(&DAT_0098adb1)[type·0x34] = FUN_00595820(chassis, weapon, armor, ability,
   reactor)` — `ghidra_out/shard_015.c:9358`, inside `FUN_00595b10 @ 0x595b10` (header
   `shard_015.c:9273`). Grepping BOTH Ghidra renderings of a store (`(&DAT_0098adb1)[…] =` and
   `*(… + 0x98adb1) =`) across all 42 shards returns this one line; every other `98adb1` hit is a read.
2. **The calculator.** `FUN_00595820 @ 0x595820` (`shard_015.c:9124`-`:9258`, return at `:9257`
   `return (iVar7 + 4) * iVar8 + 2 >> 2;`) reads chassis `+4` cost, weapon `+3` cost, armor `+0xa`
   cost, chassis `+1` triad, chassis `+5` missile flag (`:9224 return local_c;` = missile chassis +
   big attack ⇒ warhead only), reactor power (type `+39`, `:9230 iVar8 = 2 << (param_5 & 0x1f)`), and
   the 25-group ability table at `0x98aaf4` (stride 28; `int[0]` = rule −7…−1/≥0, `int[4]` bit 0x400).
3. **The input tables are the alpha rules tables, byte-for-byte** (live dump, pid 2124624):
   chassis `0x92ae80` stride 0x90 → `+0` speed, `+1` triad, `+2` range, `+3` cargo, `+4` cost,
   `+5` missile, `+6` preq-tech (Infantry `1 0 0 1 1 0 13`, Foil `4 1 0 2 4 0 17`, Missile
   `12 2 1 0 12 1 11`); weapon `0x92b950` stride 16 → `+0` attack(s8), `+2` mode, `+3` cost, `+4`
   preq (Gun `1,0,1`, Colony Pod pkg `0,8,10`, Formers pkg `0,9,6`, Artifact pkg `0,12,36`); armor
   `0x92fd10` stride 16 → `+8` rating, `+9` mode, `+0xa` cost (Scout `1,0,1`, Psi `255,2,6`).
   Alpha field docs: `programs/alpha.txt:344-345` (chassis Cargo/Cost "normally equal to speed"),
   `:383` (weapon/package cost factor), `:419` (armor cost factor), `:532`
   `; Name, Chassis, Weapon, Armor, Plan, Cost, Carry, Preq, Icon, Abil`,
   `:554 ; Cost = Cost in minerals (0 = Autocalculate)`.
4. **Reimplementation check.** `scripts/m53b_costcalc.py` (variant 3) reproduces **180 of 188**
   populated rows' `+41` exactly (`evidence/m53b_costcalc_digest.txt`). The 3 mismatches with
   `ability == 0` are *exactly* the 3 shipped `#UNITS` rows carrying an explicit non-zero Cost —
   Mind Worms 5, Isle of the Deep 8, Locusts of Chiron 10 (formula would give 11) — i.e. **the alpha
   Cost overrides autocalculation** (the override store itself is INFERRED: no corpus store to
   `+41` outside `:9358`). The 4th explicit-cost row, Alien Artifact 10, agrees with the formula too.
   The other 2 real mismatches are off by 1 on ability bit 1 (Scout Rover, Scout Speeder) — the
   ability-surcharge loop is the only part of the decompile my transcription does not nail; the
   remaining 3 rows are junk/unpopulated records.
5. **Consumers (all multiply `+41` by the same factor).**
   * accessor `FUN_005ac950 @ 0x5ac950` (`shard_015.c:23696`, reads `+41` at `:23707`): returns it
     verbatim for `type < 0x40`, clamping to [1,999] only for class 8 (Colonization) when a base
     index is passed; for `type ≥ 0x40` it adds `FUN_00595ad0(type) × rate / 100` (open).
   * production affordability: `if (base+0x40 < iVar3 * iVar4)` — `shard_012.c:20722` (iVar3 =
     `FUN_004e40a0`, iVar4 = `FUN_005ac950`, `shard_012.c:20718`/`:20720`).
   * the completion debit (SPENDA): `base+0x40 -= iVar3 * iVar4` — `shard_012.c:20866`.
   * base production pane: `shard_001.c:4705-4708` (`FUN_0040f830`) — `cost = mult × +41`, then
     compared against `*(int *)(DAT_008f0d60 + 0x40)` (storage) for the progress bar.
   * the printed price: `__itoa(iVar7 * (byte)(&DAT_0098adb1)[type], …)` — `shard_014.c:19723-19725`
     inside `FUN_00577280 @ 0x577280` (`:19574`), i.e. the UI string literally is `mult × +41`.
   * AI planner `FUN_004e5ae0` seeds a fixed-point value with `(byte)(+41) + 2) * 0x100`
     (`shard_012.c:25696`) — the same byte used AS a value, not a separate weight (INFERRED).
6. **The multiplier is 10 in this game.** `FUN_004e40a0 @ 0x4e40a0` (`shard_012.c:13798`): event-mask
   owner ⇒ 10, then difficulty factor `DAT_0092a290/0x92a294` (÷10 rescale only if ≠ 10), then
   `DAT_0092ada8` (×9/×8 only when 1/0), then `switch(faction+0x1c government)`, case 0 ⇒ unchanged.
   Live readback: `0x92a290 = 10`, `0x92a294 = 10`, `0x92ada8 = 2`, `0x985b10 & 0xff = 0x08`
   (player 3 only), government field `0x94d6a0 + 3·0x20bc = 0` ⇒ **returns 10**.
7. **Scale cross-check.** M52b measured the live SPENDA debit for our queued Scout Patrol as **10
   minerals** — `EDI_SPENDA … edi=10 q50=2` and the watchpoint `old=200 new=190`
   (`evidence/m52b_watch.log:391-392`) — exactly `10 × +41(=1)`; third-party SMAC strategy text says a
   Scout Patrol costs 10 minerals. Facility upkeep proves the loader does NOT scale alpha values
   into the item table (`0x984d48 + item·0x30` int0 == alpha `Maint` verbatim, items 1-11 checked),
   so the ×10 lives in `FUN_004e40a0`'s percent-of-10 convention, not in the tables.

## `+43` — the byte `+41` is often confused with (and the milestone's ≠ row)

`+43` (`0x98adb3`) is the **auto-calculated AI role byte**, written only by the `FUN_00595b10` ladder
(`shard_015.c:9366`-`:9441`) plus `shard_014.c:17802` (type-creation path, stores the requested role
and forces `+42 = 3` when it is 10):

* noncombat packages: `+43 = weapon mode + 0x20` (`shard_015.c:9431`, `+42 = mode` at `:9430`) →
  39/40/41/42/43/44 for Transport/Colonist/Terraformer/Convoy/InfoWar/Artifact — matches all six
  shipped rows live (Transport Foil 39, Colony Pod 40, Formers 41, Supply Crawler 42, Probe Team 43,
  Alien Artifact 44).
* combat chassis: 1…10 from the chassis-triad / weapon-attack / armor ladder (`:9369`-`:9427`),
  which reproduces the live values for Mind Worms (1, `:9405`), Isle of the Deep (6, sea branch
  `:9371`), Locusts of Chiron and Unity Scout Chopper (9, air + `ability & 0x20`, `:9377`), Scout
  Patrol and Unity Rover (10, the `attack == 1 && armor == 1` rule `:9419`).
* `+42` (the Plan/class byte) equals the alpha `#UNITS` Plan column for **14/14** shipped rows; the
  ladder alone explains 10 of them (Scout Patrol 0→3, Mind Worms 0→1, Isle 6→7, Sea Formers 6→9
  require the explicit Plan), so the loader overrides `+42` with the alpha Plan — INFERRED, no
  corpus store visible in either Ghidra rendering.

**Rows where `+41` ≠ `+43`:** Scout Patrol (type 2) `+41 = 1` (= the 10 minerals actually debited)
vs `+43 = 10`; Colony Pod 3 vs 40; Transport Foil 3 vs 39; Formers 2 vs 41. Across the whole live
table `+41 == +43` in only **21 of 193** populated rows (`evidence/m53b_types.tsv`, class histogram
and agreement counts in `scripts/m53b_types.py` output).

## Open threads

* where the loader writes the explicit alpha Cost into `+41` and the Plan into `+42` (Ghidra renders
  neither as a `DAT_` store);
* `+41` off-by-1 on ability bit 1 (Scout Rover / Scout Speeder) — the ability-surcharge loop;
* `FUN_005ac950`'s `type ≥ 0x40` bump (`FUN_00595ad0 × rate / 100`, zeroed when the base already has
  the thing: `(&DAT_0095da9c)[base + idx·0x130] & (byte)type`);
* secret-project costs come from a different table: `(&DAT_00984d44)[idx·0xc]` (`shard_012.c:22336`
  region, `FUN_004f26e0`) — same `mult ×` convention, different table.
