# NAMED.md `## B30` - ROTATED VERBATIM (byte-exact) by scripts/b32_named_rotate.py
# sha1 7a11114cc0b2ee78ef113acdb95260b5228cffa0  bytes 2408

## B30 (s321 BUILD, zero box) — the COMPLETION leg EXECUTABLE: a paid queue item becomes a facility the base HAS (`sim/composedfacility.py`; spine §B30; M310 rotated VERBATIM to `docs/named-archive-b30-rows.md:5`, sha1 `ca3caf3785c9d6e9`). ACCEPT `python3 -u -m sim.selftest --b30` -> **`PASS B30: 6/6 gates`** rows `234ab3d83a88dbea` print `29f408c79329a5a8` img `3a503c638ba45330` (`evidence/b30_facility_completion.txt:35-36`), 2 runs + relay identical; harness `python3 -u scripts/b30_mutate.py` -> **`PASS HARNESS B30: 10/10`** digest `76a481b5d8a7d8b0`, every gate G1-G6 reddened, NO-OP `[]`, ST 4/4, baseline tree green, no crash accepted (`evidence/b30_mutate.txt:12`).

| claim | evidence | conf |
|---|---|---|
| the container's own queue drives the run: 18 base records, own player 3, 2 eligible (`1<=head<=31` AND inside the parsed charge window; heads 32..38 ineligible `[]`), target base 0 'University Base' item 2 = 'Children's Creche', rule delta 1 | `evidence/b30_facility_completion.txt:2`, `:22` | V MU6 |
| the SETTER is the reader's inverse over the whole 32-id window (32/32 round-trip, 0 stray bits, id 39 REFUSED); the swapped-orientation rival lands on only 4/32 ids | `:23` | V MU1/MU2 |
| the write is ONE byte: diff `[140]`, delta 4 = `1<<(item&7)`, inside `+0x8c..+0x8f` | `:24` | V MU1 |
| writer round-trip: identity build byte-identical, file diff = 1 offset, reload owns `[1,2,8]`, shape/tail equal, 17/17 other records byte-identical, wrong-base rival misses THROUGH THE RELOAD | `:25-26` | V MU3/MU5 |
| the bill moves by the DERIVED table under M46's disabled rule (0 -> 1, delta 1 == rule 1, 0 per-id mismatches), priced off the RELOADED record; the 'table value' rival differs at exactly `[8]`; G6 runs the instrument twice, so determinism is a gate | `:27` | V MU4/ME3/ME4 |
| the completion ROUTINE that stamps the bit was ASSUMED (reader-inverse) in this rung - **QUALIFIED by `## M342`** (the setter is `FUN_004e44f0`'s inline `or` @`0x4f0ec0`, the pop `FUN_004ef5d0` a non-writer) **and by `## B31`**: the game's own run has NO positive completion case and one NEGATIVE at a facility-range head, so the assumption is UNVERIFIED against recorded bytes | `evidence/m342_completion_setter.txt:190` | V (M342) |
| OPEN: every other real-completion effect (queue-pop order beyond B11, storage/mineral reset, messages); ids 39..71's shared-field question | - | lead |
