# NAMED.md `## M352`, `## M353`, `## M355` — ROTATED VERBATIM
(byte-exact, by `scripts/m368_named_rotate.py`)

<!-- ## M352 sha1 f6cc962a472e93bd len 1262 -->
## M352 (s328-c3, static; ACCEPT `scripts/m352_persist_writeback.py` -> **`PASS M352: 7/7`** `d553194a`, x2 `c8bbfda4` (`evidence/m352_x2.txt:4`); harness 13/13; `:N` = a line of `evidence/m352_persist_writeback.txt:1-140`)
| claim | ev | conf |
|---|---|---|
| 8 `call edi` = 1 target: edi@0x58f106 from `ds:0x6710fc` = KERNEL32!WritePrivateProfileStringA (.rdata import slot; its own dword names it); 0 mem-indirect | `:18-25` | V MU1,MU2,MU13 |
| 13 write keys = 8 direct + 5 via FUN_0058f030; 12 blocks LOAD a block cell (11/11 scalars + Custom World array; window presence), `Prefs Format` = itoa(0xb) stamp | `:27-45` | V MU3-MU7 |
| read = 5 fns / 5 refs / 35 keys; 13/13 written keys read; `Laptop`+`Language` read, written NOWHERE (33 write sites) | `:47-122` | V MU8,MU9,MU12 |
| RETRACT M350: `ds:0x6926ec` = the .data literal "Prefs Format"; lpKeyName at 7 push sites; no store names the VA, 0 materialisations | `:124-131` | V MU10,MU11 |
| rivals R1 vtable / R2 write-only / R3 read==write / R4 mutable pointer all refuted | `:133-140` | V MU1,MU13 |
| ~~OPEN: what `Laptop` selects (masks @0x58ea12/0x58eb2b)~~ ANSWERED by `## M355`: the DEFAULT bit-vectors of `Preferences`/`More Preferences`; twins return 0x3a7168/0x327168 | `:97` | V (M355) |

<!-- ## M353 sha1 80b9d14fbf760ad5 len 1914 -->
## M353 (s329-chain1, ANALYSE, STATIC 11/11 + harness 13/13, zero box) — the `0x999fa4` numeric band: ONE indexed filler + four `$`-token consumers

ACCEPT `python3 -u scripts/m353_numeric_band.py` -> **`PASS M353: 11/11 gates`** digest `367fdae1d78979e5`, two renders identical (`evidence/m353_numeric_band.txt:87`); harness `python3 -u scripts/m353_mutate.py` -> **`HARNESS PASS 14/14`** digest `fd143532b283b01b` (`evidence/m353_mutate.txt:17`). `:N` = a line of the ACCEPT evidence (`evidence/m353_numeric_band.txt:75-87`).

| claim | evidence | conf / mutant |
|---|---|---|
| band = 10 dwords `[0x999fa4,0x999fcc)`: own/pay/txt bases + stride DERIVED from the writer body (0x28 apart, `shl 8` -> 0x100, 10*0x100 -> 0x99aa1c) | `:77` | V MU3/MU14 |
| 16 refs = 11 absolute + 5 `[reg*4+0x999fa4]`; stores = 3, all `mov` (no xchg/movnti form) — SCALED `0x626597`, absolute `0x442642`, absolute `0x626fd7` | `:75,76` | V MU1/MU2 |
| FILLER = `FUN_00626581` (33 B): `k>9` returns 3, else `numeric[k]=v` and returns 0; 260 call sites, 242 literal k, histogram `0:131,1:75,2:23,3:7,4:3,5:2,6:1`, ZERO above 9 | `:38,39,78,79` | V MU4/MU5 |
| M325/M324's `W={442642,626fd7}` was an ABSOLUTE-address census: SUPERSEDED here (the scaled store `0x626597` was invisible to it) | `:76,84` | V MU2/MU10 |
| CONSUMERS pinned per ADDRESS: `$NUMBER`@625c2c, `$NUM`@625cec, `$HEX`@625e4b, each `itoa(v,buf,10)`; the 0xa is ARG3 (3 pushes before the call, forwarded by `0x64f980`) -> `$HEX` prints DECIMAL | `:80,81` | V MU6/MU7/MU12/MU13 |
| the 4th read is the `$#k` PREDICATE (`cmp numeric[k],1` -> `setne`), k = char-0x30 with NO bound — the `$k` path does bound (`cmp k,0xa`) | `:82` | V MU8 |
| `$#` at k>=10 leaves the band: k=10 = owner[0], 20 = payload[0], 30 = text[0] | `:83,70` | V MU9 |
| OPEN: what the `$#` flag gates; numeric[0] is DUAL-USE (the 0x442642 cheat clamp and the ENERGY read @0x4e032c) | - | lead |

<!-- ## M355 sha1 55fb00f1153bf459 len 1004 -->
## M355 (s329-c3, 7/7) — `Laptop` = the DEFAULT bit-vectors of `Preferences`/`More Preferences`
| `Laptop` = 4 read sites, 2 VAs (0x58e9f3/0x58eb0c loader, 0x58e688/0x58e708 getters); `neg`/`sbb` -> 0/-1; absent==0 | `evidence/m355_laptop_masks.txt:17,31` | V MU5,MU14,MU19 |
| masks from the `and`/`add` immediates: Preferences 0xbbe1dd96/0xa3e1dd16, More Preferences 0x3a7168/0x327168; reg = the read's atoi return | `:43,50` | V MU1,MU8,MU10,MU20 |
| `Laptop`!=0 CLEARS Preferences {7,27,28}, More Preferences {19}; nothing added | `:48-51` | V MU15 |
| default = '1'/'0' over bits 31..0 (leading zeros >8 dropped), re-parsed by 0x628720 `v=v*2+(c-'0')` | `:66-77` | V MU12,MU13,MU22,MU24 |
| `Difficulty`<2 (0x92bde8) ORs Preferences bit 5 in the LOADER default only, guarded | `:59-60` | V MU2,MU3,MU21 |
| APPLY 0x492464/0x49246f ORs +0xa30 -> ds:0x92befc, +0xa34 -> ds:0x92bf00 (11 sites) | `:92-100` | V MU6,MU7,MU9,MU11,MU16,MU17,MU23 |
| OPEN: bit->option NAMES; other re-derivers | - | lead |

