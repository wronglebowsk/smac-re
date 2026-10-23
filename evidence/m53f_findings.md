# M53f — where the alpha `#UNITS` Cost/Plan land in the type record (session 58)

Method: static only. Full `.text` linear disassembly (`objdump -d -M intel --section=.text
programs/terran.exe` — regenerable, not committed; cited windows are in
`evidence/m53f_disasm_*.txt`), the Ghidra corpus, `programs/alpha.txt` / `data/alpha.json`,
and read-only `/proc/2124624/mem` preads (TracerPid 0, no gdb).

## 1. `+41` has exactly ONE store instruction in the whole image — and it is the formula

`grep 98adb1` over the `.text` disassembly returns **30 references, exactly one of which is a
store** (`evidence/m53f_adb1_refs.txt`, 30 lines):

```
595ce2: e8 39 fb ff ff    call 0x595820                     ; FUN_00595820 (cost formula)
595ce7: 88 86 b1 ad 98 00 mov BYTE PTR [esi+0x98adb1],al    ; THE only +41 store
```
inside `FUN_00595b10 @ 0x595b10` (`shard_015.c:9273`, store rendered `shard_015.c:9358`);
`esi = 52*type` (`0x595cad-0x595cbe`: `lea eax,[edi+edi*2]`; `lea esi,[edi+eax*4]`; `shl esi,2`).
The other 29 references are reads. **VERIFIED** (instruction census, not corpus grep).

## 2. The alpha override is in the `#UNITS` loader, as disp8 stores off a record+50 pointer

`FUN_00579f40 @ 0x579f40` size 293 = `shard_014.c:21351`; it opens the section with
`FUN_005ea431(PTR_s_ALPHA_00693b64, s_UNITS_00691c40)` (`shard_014.c:21369`), clamps the row
count to `0x40` (`0x579f76-0x579f89`), and loops rows with `esi = 0x98adba` (= record + 50)
advancing `add esi,0x34` (`0x57a04e`). Field reads are in alpha column order
(`0x5ea466` = string field, `0x5ea484`/`0x5ea493` = numeric field). Full window:
`evidence/m53f_disasm_fn579f40.txt`.

| alpha `#UNITS` col (`alpha.txt:532`) | record field | store (VERIFIED) | guard |
|---|---|---|---|
| 0 Name | `+0[34]` | `0x579fac lea ecx,[esi-0x32]` + `0x579fb1 call 0x64b9d0` (strcpy) | — |
| 1/2/3 Chassis/Weapon/Armor names | → ids via `0x578170 / 0x578270 / 0x578360` | pushed to the builder `0x57a021 call 0x595b10` | — |
| 4 **Plan** | **+42** | **`0x57a02d mov [esi-0x8],bl`** | `0x57a029 test ebx,ebx / 0x57a02b jl` (only if ≥ 0) |
| 5 **Cost** | **+41** | **`0x57a037 mov [esi-0x9],al`** | `0x57a033 test eax,eax / je` (0 = Autocalculate) |
| 6 Carry | +40 | `0x57a041 mov [esi-0xa],al` | `0x57a03d test / 0x57a03f je` (0 = keep builder value) |
| 7 Preq (tech name) | +50 word | `0x57a001 mov WORD PTR [esi],ax` (via `0x578090`) | — |
| 8 Icon | +46 | `0x57a04a mov [esi-0x4],cl` | none (writes −1 too) |
| 9 Abil (24-bit string) | builder param_5 → `+32` | pushed at `0x57a016` | — |

The builder runs FIRST (`0x57a021`), the overrides AFTER — so a non-zero alpha Cost replaces
the formula byte. Ghidra renders the two override stores as `*(char *)(puVar10 + -4)` /
`*(char *)((int)puVar10 + -9)` (`shard_014.c:21402`, `:21405`): pointer-arithmetic quirks on a
`undefined2 *puVar10 = &DAT_0098adba`. **That is why no `DAT_0098adb1/adb2` store and no disp32
`0x98adb1` write exists: the offsets are disp8 −0x8/−0x9 off a record+50 register.** A disp8
scan of every function touching `0x98adxx` finds only these plus the save-restore pair below
(`evidence/m53f_disp8_stores.txt`).

Live proof the loader ran (pread, ids 0-13 vs `data/alpha.json` #UNITS):
`+42 == alpha Plan 14/14`; `+46 == alpha Icon 14/14` (−1 written as 0xff for the 12 `−1` rows);
`+40 == alpha Carry` where Carry ≠ 0 (Isle of the Deep 4) and the builder's
`FUN_00570860` value where Carry == 0 (Transport Foil 2, Unity Foil 1 — both use the
`Transport` weapon, mode 7). **VERIFIED (live read × alpha × store-site addresses).**

## 3. Second writer pair: the save/scenario loader restores +41/+42 verbatim

`FUN_00596850 @ 0x596850` (`shard_015.c:9971`, "load_save_state") has a record loop
(`0x5973bc`…`0x597495`, `add eax,0x34`, counter `[ebp-0x18]`) copying a **48-byte** source
record (`add ecx,0x30` at `0x597437`) into the 52-byte runtime record with disp8 stores,
including `0x597464 mov BYTE PTR [eax+0x29],dl` (+41) and `0x59746a mov [eax+0x2a],dl` (+42)
(`evidence/m53f_disasm_597400.txt`). So the cost/plan bytes persist across save↔load and a
loaded scenario can carry values the formula never produced. **VERIFIED.**

## 4. The ability table layout, cross-checked against alpha `#ABILITIES`

Table `0x98aaf4` stride 28, **24 rows = the 24 `#ABILITIES` rows** (`data/alpha.json`; the
loops' bounds are `0x98ad94`/`0x98ad9c` = base + 24·28, read at `0x595916`/`0x595998`).
Live dump `evidence/m53f_ability_table.txt`:
* `int[0]` (+0) = the cost rule = `#ABILITIES` column 1, verbatim: live
  `[1,0,1,1,2,1,1,1,1,-1,1,2,1,1,1,-7,2,1,-1,1,1,1,1,0]`.
* `int[2]` (+8) = the 11-char flag string parsed as binary, verbatim: row 0 `00000010111` =
  23 = live 23; row 1 `10000111111` = 1087 = 0x43f = live 1087; row 2 `00001111001` = 121 ✓.
* `int[3]` (+12) ≈ required-tech id, `int[4]` (+16) = name pointer — **INFERRED**.

Rule semantics (`FUN_00595820`, jump table `0x595ab4` indexed `rule + 7`, guard
`0x5958ac-0x5958b2`; `evidence/m53f_jumptable.txt` + `evidence/m53f_disasm_fn595820.txt`):
`≥0` add verbatim (`0x5958a8`); `−7` ccost+armor−2; `−6` ccost+wcost−2; `−5` armor+wcost−2;
`−4` ccost−1; `−3` armor−1 (`0x5958e4 lea ebx,[ebx+edi-1]`); `−2` wcost−1
(`0x5958de lea ebx,[ebx+edx-1]`); `−1` `idiv` wcost/armor, negative→0, cap 2
(`0x5958bb-0x5958da`). Surcharge: `0x59589a-0x59589e` adds +1 to the running sum for every
set bit after the first. Register roles: `edx` = weapon+3 (`0x59582f-0x595847`), `edi` =
armor+0xa (`0x59584d-0x59585b`), `[ebp+0x10]` = chassis+4 (`0x59586c-0x595872`).
**VERIFIED.** Pitfall: a hand-decoded table read that dropped `0x5958e4` "proved" Ghidra's
labels were shifted by one and broke 10 live rows; the raw dump shows 7 distinct entries.

## 5. The land-chassis loop is the real M53b gap (Scout Rover / Scout Speeder)

For `chassis+1 ∉ {1,2}` the ELSE branch (`0x59597b-0x5959a6`) runs a second ability loop:
`0x59597d mov eax,0x98aafc` (cursor = entry **+8**, not +16), `0x595990 mov edx,[eax]`,
`0x595992 test dh,0x4` (= bit **0x400** = the flag string's FIRST character),
`0x595997 inc ebx`. Ability bit 1 = Deep Radar, flag 0x43f ⇒ bit set ⇒ **+1 surcharge**.
Scout Rover (id128, ch1 wp0 ar0 ab0x2 rx2) and Scout Speeder (id390, … rx1) are the only two
live rows affected. **VERIFIED (addresses + live table + the two rows).**

## 6. The 188-row check is now clean

`scripts/m53b_costcalc.py` rewritten to the disasm-true model (flag at +8, 24 entries, land
loop enabled, the located alpha override applied, stale records separated):

`rows=188  formula==live +41: 181  alpha-Cost override rows: 4/4  stale/out-of-range records: 3
UNEXPLAINED mismatches: 0` (`evidence/m53f_costcalc_digest.txt`).
`--legacy` (M53b's model: loop skipped, flag read at +16) still reproduces 179 + 4 + 3 with
exactly 2 unexplained = Scout Rover + Scout Speeder ⇒ the fix is the land loop, nothing else.
Stale-record rule (evidence-backed): chassis ≥ 9 / weapon ≥ 21 / armor ≥ 10 (the shipped
#CHASSIS/#WEAPONS/#DEFENSES row counts) **or reactor == 0** — the 185 real rows all have
reactor 1 or 2, and every reactor-0 row in the table is one of the 7 garbage rows.
Alpha-explicit rows: Alien Artifact 10, Mind Worms 5, Isle of the Deep 8, Locusts 10 — live
+41 equals the alpha Cost in all four while the formula says 10/11/11/11. **VERIFIED.**

## Open threads
* Who calls `FUN_00579f40` (the alpha-rules dispatcher) and whether it re-runs on scenario
  load vs only at boot; `+50` = prereq tech id (−1 none, −2 "Disable") is INFERRED.
* `FUN_00595820`'s `+40` producer `FUN_00570860(chassis, ability, reactor)` is only
  characterised as "non-zero for weapon mode 7".
* Secret-project cost table `0x984d44` stride 0xc; the −29 head value; `0x4ef992`/`0x4f0f46`;
  `FUN_0059ce10` `+0x4c = pop·10/2`; M53g (chooser guard `[sub+0xa774]`, REPLACE/mode 7).

**Next:** `NEXT_PROMPT.md` rewritten for session 59; THE PICK = **M53g**.
