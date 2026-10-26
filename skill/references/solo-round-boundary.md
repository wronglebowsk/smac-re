## Solo round boundary ("the heartbeat") — measured model (M55)

The solo round boundary is `FUN_00520c10` (reached from main loop `FUN_00522850`): on turn-end it runs
`FUN_0051f320` (round++, year = 2100 + round via `FUN_005b2c00`), then walks `cur_player` across the
active factions: per-player upkeep `FUN_005208f0(p)` (income; research advance `FUN_0051fe90` →
`FUN_005aaa20`; debits and zeroes the faction+4 spending ledger), then AI `FUN_0056d0c0(p)` or the
human loop `FUN_0050f420`.

- **The 7-stage machine is multiplayer-only.** The stage counter `DAT_0091c630` never moves in solo
  (measured 0 across every boundary). Floor on the `cur_player` walk, never on stage.
- **The walk order is rotated per round**, not 0..7, and dead factions are skipped (active mask is the
  BYTE at `0x985b11`; eradication clears its bit). Factions with no units pass in milliseconds — a
  2 ms sampler may skip them entirely; do not read a missing value as a skipped turn.
- **Auto-end-turn is real.** With every unit HELD, the "No units need orders Press ENTER" path
  (`DAT_0091f69c & 1` → `FUN_00520c10(2)`) closes our turn on its own 1–2 s after it opens: rounds
  auto-advance with no input, and `cur_player == ours` is a window that reopens every round.
  - Waiting for idle to advance a turn is wrong (it can also stall for minutes); assuming our turn
    persists is wrong too. After the year flip, the settle before the after-snapshot must be a SHORT
    flush delay (~0.3 s), not a seconds-long stability window — a 1.5 s settle straddles the next
    auto-end and the run silently measures two boundaries (year +2).
- **Modal event dialogs freeze the walk mid-round** (eradication / new-tech / contact popups, and the
  planet display some events open). Signature: `cur_player` stuck on an AI faction, all turn
  semaphores zero, `turn_flags & 2` set, CPU hot. `Return` dismisses them and is NOT consumed as
  turn-end while the human loop is not running (`cur_player != ours`) — so press Return every ~2 s
  while waiting for our turn and again mid-walk. One press can be swallowed by the planet display:
  re-press until the year flips. Escape closes a planet display but Escape at the tactical map opens
  the quit confirmation — prefer Return.

## Accounting a boundary diff (what "explained" means)

- **Record identity across a boundary is (x, y, type, owner, order), not bytes.** The boundary
  legitimately rewrites other bytes in HELD records: the u16s at `+28`, `+48`, `+50` decrement by 1
  (index references adjusted by array compaction after deaths — the same links the livelock rule
  names). Byte-identity floors fail on real, correct runs; report the rewrite offsets as a feature.
- **Production = net-new records per (owner, type) class arriving with order 0 on a base tile of that
  faction.** Moves and deaths net out per class. Net-new arrivals with a NONZERO order are transport
  cargo materialising (unload states like order 24), not production. Transient AI orders reset to 0 at
  that player's turn start, which manufactures a removed+added pair on the SAME tile — match
  same-tile pairs out of the production bucket before counting them.
- **Enemy-side attribution is confounded** (moves, per-turn order resets, cargo all produce the same
  multiset diff). Floor only OUR net-new records (must be order 0 on our base tiles); report enemy
  arrivals with attribution labels. Never floor a confounded side.
- **AI conquest is real:** a base tile of ours may flip to another faction in the array (capture —
  report it); the floor is that a base tile never VANISHES from the array. Our units may die on
  foreign turns (garrison attrition): a vanished ours with NO same-class arrival is a reported death,
  not a floor failure; a vanished ours WITH a same-class arrival elsewhere is a move and must fail.
- **Research completes by RESET, not growth:** a tech completion drops rpoints by the tech cost within
  the same boundary (measured −161, −217) and switches rtech — an "our points increased" floor fails
  a correct run at the completion round. Floor = some active faction's rpoints or rtech changed; our
  own flat points is a reported condition. Research fields: faction `+0x1a8` points, `+0x1ac` queued
  tech (−1 = none), `+0x1b4` save-for-later (global gate `DAT_00920434`); per-team countdown lives in
  a parallel dword array at `0x94F8C0 + p*8380` (faction array `0x94D650`, stride 8380 = 2095 dwords;
  the faction array is NOT compacted when a player dies — per-player field reads stay valid).
  The ledger at faction+4 is debited and zeroed by upkeep every round — a nonzero post-upkeep ledger
  is a real bug, worth flooring.

## Measuring it (the `scripts/m55_boundary.py` pattern)

- Sample globals at ~2 ms with ONE blob read per row (`0x985AE4..0x985B11` covers flags, n_units,
  n_bases, counts, round, year, active mask; plus `0x985DC8` for mode/cur_player) — per-field reads
  cannot keep 2 ms cadence.
- Fire the trigger (Enter) from INSIDE the sampler loop (sample, press, keep sampling) so the walk is
  observed, not raced; re-press every 2 s while no flip is seen OR while mid-walk (dialog dismissal).
  Open `/proc/<pid>/mem` `rb+` (poke needs write; never truncate).
- Snapshots are dicts keyed by int player id; a `--fixture` acceptance run round-trips them through
  JSON, which turns int keys into STRINGS — `int()` the keys when loading a fixture. Hand-type a
  fixture that must FAIL (a fixture that passes proves nothing), and keep a `--no-enter --no-poke`
  dry probe as the non-vacuity check: it must honestly FAIL on "no year flip". Guard shared code
  paths (e.g. the press branch) so the dry mode cannot crash on a variable only the armed path
  defines — a crash is not an honest FAIL.
