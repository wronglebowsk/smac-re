# COVERAGE — terran.exe

Generated 2026-10-20 18:56 by `scripts/coverage.py` from `ghidra_out/index.csv`.

## Corpus
- functions in database: **10284**
- decompiled cleanly: **10284** (100.0%)
- total decompiled C: **2.48 M bytes of code** (730416 instructions)
- shards: 42 (`ghidra_out/shard_NNN.c`, 250 functions each)
- mentioned in an existing dump/writeup (upper bound, text search): **646** functions

## By name class
- unnamed (FUN_): 5967
- named: 4262
- runtime/CRT: 54
- thunk: 1

## Size distribution
- tiny <16B: 4111
- 16-63B: 2902
- 64-255B: 1694
- 256B-1K: 1063
- 1-4K: 429
- >4K: 85

## Caller distribution (in-degree: how much code depends on it)
- 0 callers: 430
- 1-2: 7960
- 3-9: 1089
- 10-49: 577
- 50-199: 179
- 200+: 49

### Compiler/runtime helpers excluded from rankings (29 found)

- 0x0064b9e0 FUN_0064b9e0 — 1968 callers, 224 B
- 0x00626634 FUN_00626634 — 1580 callers, 141 B
- 0x00404ed0 FUN_00404ed0 — 1441 callers, 21 B
- 0x00406060 FUN_00406060 — 1397 callers, 102 B
- 0x005e3ced FUN_005e3ced — 911 callers, 135 B
- 0x0061482f FUN_0061482f — 788 callers, 56 B
- 0x005f9bfb FUN_005f9bfb — 662 callers, 130 B
- 0x00405220 FUN_00405220 — 655 callers, 33 B
- 0x004053f0 FUN_004053f0 — 596 callers, 27 B
- 0x00407520 FUN_00407520 — 589 callers, 29 B
- 0x005ea448 FUN_005ea448 — 559 callers, 15 B
- 0x00409690 FUN_00409690 — 530 callers, 33 B

## Top 20 hubs by caller count (helpers excluded)

| addr | name | callers | insns | size | strings |
|---|---|---|---|---|---|
| 0x005c9fc5 | FUN_005c9fc5 * | 383 | 674 | 1925 | 0 |
| 0x005f6de9 | FUN_005f6de9 * | 305 | 118 | 550 | 0 |
| 0x00483470 | FUN_00483470 * | 292 | 141 | 556 | 0 |
| 0x005dbb5f | FUN_005dbb5f | 273 | 33 | 135 | 0 |
| 0x00403fa0 | FUN_00403fa0 * | 258 | 32 | 74 | 0 |
| 0x00584010 | FUN_00584010 * | 249 | 33 | 108 | 0 |
| 0x005a6330 | FUN_005a6330 * | 224 | 442 | 1596 | 0 |
| 0x005c00a8 | FUN_005c00a8 * | 223 | 147 | 466 | 0 |
| 0x004065d0 | FUN_004065d0 * | 183 | 34 | 120 | 0 |
| 0x005e83cb | FUN_005e83cb | 181 | 25 | 72 | 0 |
| 0x0064bda0 | `eh_vector_constructor_iterator' | 175 | 32 | 113 | 0 |
| 0x005d8123 | FUN_005d8123 * | 166 | 25 | 70 | 0 |
| 0x005ca9e8 | FUN_005ca9e8 | 143 | 48 | 149 | 0 |
| 0x005dbbe6 | FUN_005dbbe6 * | 137 | 63 | 222 | 0 |
| 0x0060c555 | FUN_0060c555 * | 133 | 38 | 108 | 0 |
| 0x00403a80 | FUN_00403a80 * | 131 | 32 | 74 | 0 |
| 0x005ab130 | FUN_005ab130 * | 129 | 96 | 270 | 1 |
| 0x0061711c | FUN_0061711c * | 126 | 117 | 387 | 0 |
| 0x005be090 | FUN_005be090 * | 119 | 24 | 72 | 2 |
| 0x00469010 | FUN_00469010 * | 117 | 30 | 75 | 0 |

`*` = already has a dump/writeup in this repo.

## Largest functions

| addr | name | size | insns | callers |
|---|---|---|---|---|
| 0x0055f650 | FUN_0055f650 | 54483 | 16822 | 2 |
| 0x00546800 | FUN_00546800 | 34550 | 10723 | 5 |
| 0x004f6030 | FUN_004f6030 | 30475 | 9594 | 7 |
| 0x0058fa40 | FUN_0058fa40 | 23925 | 6755 | 4 |
| 0x00585720 | FUN_00585720 | 22283 | 6347 | 6 |
| 0x00502cd0 | FUN_00502cd0 | 18238 | 5623 | 4 |
| 0x0052bce0 | FUN_0052bce0 | 16238 | 4558 | 51 |
| 0x0046a610 | FUN_0046a610 | 15991 | 4264 | 3 |
| 0x00512b40 | FUN_00512b40 | 14986 | 3939 | 3 |
| 0x00556690 | FUN_00556690 | 14349 | 4235 | 2 |
| 0x004ef6d0 | FUN_004ef6d0 | 12298 | 3164 | 1 |
| 0x0047c0e0 | FUN_0047c0e0 | 12134 | 3280 | 1 |
| 0x0049c070 | FUN_0049c070 | 11914 | 3034 | 3 |
| 0x00574370 | FUN_00574370 | 11631 | 4004 | 7 |
| 0x00519b00 | FUN_00519b00 | 11249 | 3462 | 1 |
| 0x005f1394 | FUN_005f1394 | 11207 | 2235 | 94 |
| 0x0045ed90 | FUN_0045ed90 | 10782 | 2605 | 1 |
| 0x00538040 | FUN_00538040 | 10193 | 2505 | 4 |
| 0x0045a920 | FUN_0045a920 | 9892 | 2613 | 1 |
| 0x005a3470 | FUN_005a3470 | 9319 | 2803 | 5 |

## Read next (score = 2*callers + insns/40 + 3*string-refs)

| addr | name | score | callers | insns | strings |
|---|---|---|---|---|---|
| 0x0064b9e0 | FUN_0064b9e0 | 3938 | 1968 | 84 | 0 |
| 0x00626634 | FUN_00626634 | 3161 | 1580 | 44 | 0 |
| 0x00404ed0 | FUN_00404ed0 | 2882 | 1441 | 13 | 0 |
| 0x00406060 | FUN_00406060 | 2795 | 1397 | 30 | 0 |
| 0x005e3ced | FUN_005e3ced | 1823 | 911 | 33 | 0 |
| 0x0061482f | FUN_0061482f | 1577 | 788 | 23 | 0 |
| 0x005f9bfb | FUN_005f9bfb | 1325 | 662 | 32 | 0 |
| 0x00405220 | FUN_00405220 | 1310 | 655 | 17 | 0 |
| 0x004053f0 | FUN_004053f0 | 1192 | 596 | 15 | 0 |
| 0x00407520 | FUN_00407520 | 1178 | 589 | 15 | 0 |
| 0x005ea448 | FUN_005ea448 | 1118 | 559 | 6 | 0 |
| 0x00409690 | FUN_00409690 | 1060 | 530 | 17 | 0 |
| 0x00406650 | FUN_00406650 | 1029 | 514 | 38 | 0 |
| 0x00405f60 | FUN_00405f60 | 1018 | 508 | 62 | 0 |
| 0x0064bac0 | _strlen | 999 | 499 | 44 | 0 |
| 0x0064b870 | FUN_0064b870 | 934 | 467 | 15 | 0 |
| 0x005c17d1 | SetBorders | 918 | 459 | 19 | 0 |
| 0x0062732a | FUN_0062732a | 854 | 427 | 15 | 0 |
| 0x00406720 | FUN_00406720 | 794 | 397 | 18 | 0 |
| 0x005c9fc5 | FUN_005c9fc5 | 783 | 383 | 674 | 0 |

## How to read code from here on
```
scripts/fn.py 0x51e700            # decompiled C for one function
scripts/fn.py --grep 'turn'       # find functions by name
scripts/fn.py 0x51e700 --max 80   # just the top of a big function
```
Shards are ordered by address; a function body runs until the next `// ==== ` header.
