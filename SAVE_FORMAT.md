# `.SAV` save format — skeleton decoded, section sizes still open

Status: **header parsed, read order established from a runtime trace, per-section size formulas
not yet recovered.** Do not treat the section table below as a general layout: it is the exact
sequence for one save (80×80 map, mission year 2112) and the sizes of the variable sections shrink
in earlier saves (Autosave 5, year 2108, is 287,564 B — smaller than the fixed sections alone).

## Header (796 B at offset 0)

```
0    6 B    b"TERRAN" + NUL
7    1 B    0x1A   (format marker, same byte as .MP)
8    4 B    u32 version = 86   (the loader requires >= 86 for saves, >= 5 for maps)
12   4 B    timestamp-ish (b6 dd e1 bb)
16   ...    clock values (0x3a7168, 0x3c3a9, 0x1a0e)
0x54 2 B    u16 mission year  (2108 in Autosave 5)  <-- verified against the filename's turn
```

In memory this header lives at `DAT_00985ab8` and is tested elsewhere as a flags bitmask
(`&0x400`, `&0x800`, `&0x8000`); the player id sits just after it at `DAT_0091b5b4`.

## Read order (runtime, gdb on `FUN_0064cc00`, caller + size)

Loading `saves/auto/Alpha Centauri Autosave 30.SAV` (301,896 B) produced, in order:

| # | caller | size | belongs to |
|---|---|---|---|
| 1 | `0x59688f` | 796 | save header (`FUN_00596850`) |
| 2 | `0x596a96` | 67,040 | block (`FUN_00596850`) |
| 3 | `0x596edb` | 11,488 | block (`FUN_00596850`) |
| 4 | `0x5822ac` | 2,724 | map header struct (`FUN_00582260`) |
| 5 | `0x5822f7` | 140,800 | map grid, 80×80×22 |
| 6 | `0x58231d` | 128 | map trailer |
| 7 | `0x597032` | 16,000 | section |
| 8 | `0x5970e9` | 328 | section |
| 9 | `0x597146` | 3,584 | section |
| 10 | `0x5971b1` | 26,624 | section |
| 11 | `0x597299` | 4,096 | section |
| 12 | `0x59731e` | 6,188 | section |
| 13 | `0x597524` | 11,248 | section |
| 14 | `0x5976a3` | 256 | section |
| 15 | `0x59771b` | 152 | section |
| 16 | `0x597786` | 10,144 | section |

Sum of logged sections: **301,596**. Plus 300 B of reads under the 64-byte logging threshold
(the 4-byte version read among them) = **301,896**, the exact file size. The arithmetic closing to
the byte is the check that the sequence is complete.

Every caller in rows 1-3 and 7-16 is inside `FUN_00596850` (starts `0x596850`, 4,637 B of code),
so that function is the save loader; rows 4-6 come from the map loader it calls.

## Section sizes — recovered from the call sites

Sizes are `push` immediates at the 13 read sites inside `FUN_00596850`, except three that are
computed. Each site also shows the destination global, which is what makes the sections nameable
later:

| caller | size | dest global | how the size is made |
|---|---|---|---|
| `0x59688f` | 796 | `0x985ab8` | immediate |
| `0x596a96` | 67,040 | `0x94d430` | immediate |
| `0x596edb` | 11,488 | `0x927590` | immediate |
| `0x597032` | 16,000 | `0x985e5c` | immediate |
| `0x5970e9` | **count** | `0x930d7c` | `= DAT_00927538` (raw, no multiplier) — 328 here |
| `0x597146` | 3,584 | `0x989ce0` | immediate |
| `0x5971b1` | 26,624 | `0x98ad88` | immediate |
| `0x597299` | 4,096 | `0x92bff0` | immediate |
| `0x59731e` | **52·n** | `0x933278` | `n=edx`; `lea eax,[edx+edx*2]`, `lea edx,[edx+eax*4]`, `shl edx,2` ⇒ **13·4 = 52 B/record**; 6,188 = 52×**119** |
| `0x597524` | **304·m** | `0x95da10` | `m=DAT_00985af4`; `lea ecx,[eax+eax*8]`, `lea eax,[eax+ecx*2]`, `shl eax,4` ⇒ **19·16 = 304 B/record**; 11,248 = 304×**37** |
| `0x5976a3` | 256 | `0x991598` | immediate |
| `0x59771b` | 152 | `0x92bf58` | immediate |
| `0x597786` | 10,144 | `0x92d4a0` | immediate |

`0x59731e` is gated by `cmp [0x985dbc], ebx` (a version test) and `0x597524` is skipped entirely when
`DAT_00985af4 == 0` — so the section list is conditional, which is why an older save is smaller.

## Offsets pinned by content anchors, and cross-checked on a second save

Two signatures locate the map sections inside a save **exactly**, in both files:

| anchor | Autosave 30 (301,896 B) | Autosave 5 (287,564 B) |
|---|---|---|
| `50 00 00 00 50 00 00 00` (u32 80, 80 = map dims) | **79,372** — unique hit | **79,372** — unique hit |
| `????????` (map trailer marker) | **222,896** — unique hit | **222,896** — unique hit |
| distance between them | 143,524 = 2,724 + 140,800 ✓ | same ✓ |

The arithmetic closes on the byte, and the two files agree:

* before the map table: `796 + 67,040 + 11,488 = 79,324`, but the table is at 79,372 ⇒ **48 B of
  sub-threshold reads are interleaved** in the first part of the file;
* after the trailer: Autosave 30 has `301,896 − 222,896 − 128 = 78,872`; the remaining logged sections
  sum to 78,620 ⇒ **252 B interleaved**. 48 + 252 = **300**, exactly the sub-threshold total measured
  in the trace;
* Autosave 5 has `287,564 − 222,896 − 128 − 60,856 = 3,684`, i.e. **3,432 B** of computed sections
  against Autosave 30's **17,764 B** — the same 252 B of interleaved reads in both, which is what
  makes the two-file agreement meaningful rather than a coincidence.

## Full section table (verified: sums to the file size on two saves)

`scripts/decode_save.py --sections` reproduces this from the file alone. Offsets below are for a
301,896-byte save with an 80×80 map; the three variable sections shift everything after them.

| offset | size | section | destination |
|---|---|---|---|
| 0 | 8 | `TERRAN\0` + `0x1A` | — |
| 8 | 4 | u32 version = 86 | — |
| 12 | 796 | **state header** (mission year u16 at file `0x54`) | `DAT_00985ab8` |
| 808 | 4 | **own player** (reads 3 = University, matches `smac_state.py`) | `DAT_0091b5b4` |
| 812 | 67,040 | block A | `0x94d430` |
| 67,852 | 11,488 | block B | `0x927590` |
| 79,340 | 32 | small table | `DAT_00926a78` |
| 79,372 | 2,724 | **map header struct** (u32 80, u32 80) | `FUN_00582260` |
| 82,096 | 140,800 | **map grid** W·H·22 | `FUN_00582260` |
| 222,896 | 128 | map trailer (`????????`) | `FUN_00582260` |
| 223,024 | 16,000 | section | `0x985e5c` |
| 239,024 | 4 | **u32 count prefix** (328 here) | `DAT_00927538` |
| 239,028 | =count | count-prefixed section | `0x930d7c` |
| 239,356 | 3,584 | section | `0x989ce0` |
| 242,940 | 26,624 | section | `0x98ad88` |
| 269,564 | 4,096 | section | `0x92bff0` |
| 273,660 | 52·n | **n 52-byte records** (119 here) | `0x933278` |
| 279,848 | 304·m | **m 304-byte records** (37 here) | `0x95da10` |
| 291,096 | 256 | section | `0x991598` |
| 291,352 | 152 | section | `0x92bf58` |
| 291,504 | 10,144 | section | `0x92d4a0` |
| 301,648 | 28 | 7 × u32 tail values | `DAT_0091b5b8`…`DAT_0091b700` |
| 301,676 | 220 | 55 × u32 (looks like 5 × 11-dword records) | reader not yet attributed |

How the variable pieces are resolved without guessing:
* the count-prefixed section's size is **stored in the file** as the u32 immediately before it;
* the 52/304 region is split by solving `52n + 304m = len(region)` and choosing the solution on
  record content (304-byte records run ~80% zero, 52-byte records ~40%). For the 301,896-byte save
  three splits are arithmetically possible — `(119,37) (43,50) (195,24)` — and the content test picks
  **(119,37)**, which is exactly what the runtime read trace reported independently. That is the check
  that the heuristic is not circular. For the 287,564-byte save the solution is unique: `(18,8)`.

## The two record families are named: units and bases

Read live out of `/proc/<pid>/mem` (script `scripts/smac_records.py`) while Autosave 30 was loaded:

**304-byte records at `0x95da10`, count = `DAT_00985af4` (37 here) — BASES.** Each record carries a
null-terminated base name at **+19** and a position:

| rec | +0 (x) | +2 (y) | +4 (faction<<8\|flag) | +6 | name |
|---|---|---|---|---|---|
| 0 | 20 | 50 | 0x0303 (faction 3) | 5 | `University Base` |
| 1 | 24 | 34 | 0x0101 (faction 1) | 4 | `Gaia's Landing` |
| 2 | 53 | 51 | 0x0202 (faction 2) | 3 | `The Hive` |
| 3 | 77 | 13 | 0x0404 (faction 4) | 4 | `Morgan Industries` |
| 4 | 76 | 72 | 0x0505 (faction 5) | 4 | `Sparta Command` |
| 5 | 34 | 50 | 0x0606 (faction 6) | 3 | `New Jerusalem` |
| 6 | 8 | 64 | 0x0707 (faction 7) | 5 | `U.N. Headquarters` |

All 37 records have `+0` and `+2` inside `[0, 79]` — the map is 80×80 — and the faction nibble at +4
matches the faction the name belongs to. `DAT_00985af4`, which `smac_state.py` still labels
`n_factions`, is really the **base count** (37 bases in an 8-faction game at 2180 is right; a faction
count of 37 is not).

**52-byte records at `0x933278`, 119 of them — UNITS.** No ASCII in any record (so they reference
types by index, not name). `+0`/`+2` are x/y in the same 0..79 range, `+14` is the owning faction,
`+10` is a flag word. Four unit records sit at (20, 50) — exactly the coordinates of `University
Base` — which is the cross-check that ties the two tables together: garrison units share their base's
tile.

## What is still unknown

* **What each section holds.** The record sizes and destinations are the handle; the 52- and
  304-byte record families are the obvious candidates for units and bases, and the shape repeats
  identically in both saves (`+10..+13 = 02 00 00 00` in the 52-byte records, a matched small pair at
  `+4/+5` in the 304-byte ones). Naming them needs a field-to-effect check in the running game.
* The reader of the trailing **220 bytes**.
* Saves that take the conditional branches (`0x59731e` behind the `DAT_00985dbc` version test,
  `0x597524` skipped when `DAT_00985af4 == 0`) — neither of the two saves tested skipped anything,
  so the skip-path layout is untested.

## Consequence for the plan

A save now splits into named-size sections with no guesswork, and the split is verified on two saves
of different ages — that satisfies F2's proof bar for *parsing*. Re-saving byte-identically is a
different claim and has **not** been tested: it needs the writer (`FUN_00596xxx` counterpart) and the
encoder for the compressed blocks, neither of which has been run. `scripts/decode_save.py` states
exactly which of the two it does.
