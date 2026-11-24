# named-archive-b28-rows.md — NAMED rows rotated out of the registry

Rotations append here VERBATIM; each region carries its own `§rotation-N` marker and its own
terminator line, so a later rotation never re-hashes an earlier region (the s312 lesson).
`scripts/b28_named_rotate.py --verify` re-derives the marker line, the archived block's header
line and the full sha1 of the region between marker and terminator.

§rotation-1 (M246, M247, M248/M249, s316-chain1 headroom rotation)

## M246 (s197) — the save's last 4 B are a `timeGetTime()` save-CREATION stamp

| claim | evidence | status |
|---|---|---|
| `FUN_00597ce0` takes `local_8 = timeGetTime()` at entry (body line 15), calls `FUN_00596850(iVar2,1)` (line 42), then `FUN_0064c9a0(&local_8,4,1,iVar2)` (line 44) writes the trailing dword, which the codec never reads | shard_015.c `FUN_00597ce0`; Δ(dword) vs Δ(mtime) ≤ 2.5 s on 5/5 same-session pairs (Autosave 2→1 31 s / 30,989 ms; m241_probe_A→B 16 s / 16,785 ms) | V |
| creation-stamped, not file-write-stamped: `0x15c79939` sits on 3 files 486,979 s apart, `0x2db1b939` on 2 files 71,224 s apart | census G3 over 17 saves | V |

## M247 (s197) — the region map's row stride is `Rw>>1`, not `(Rw+1)/2`

| claim | evidence | status |
|---|---|---|
| `DAT_0092ae18` has 6 referencing functions; the only element accessors `FUN_00582340`/`FUN_00582360` index `(param_1>>1) + DAT_0092ae18 + (DAT_0092ad9c>>1)*param_2` (shard_014.c:27392/27401); `(Rw+1)/2` appears once image-wide (the length, 27266) | census G4 over all shards: stride-6 funcs 2, non-accessor/non-blob funcs 0, `(Rw+1)/2` sites 1 | V |
| builder `FUN_0058ce00` (shard_015.c:4707-4747) walks y < Rh, x = (y&1) step 2 < Rw, so its write set is exactly bytes 0..78 at Rw=Rh=13; slack = Rh−1 when Rw is odd, else 0 | census G5, computed from the loop bounds | V |
| the slack is never written: bytes 79..90 are `0xcd` (uninitialized-heap fill) in 17/17 saves with no `0xcd` in 0..78; both .MP (even Rw) have slack 0 and no `0xcd` | 17 saves + planet.MP + planetx.MP | V |
| what the byte VALUES mean: `FUN_0058ce00` takes terrain record `+3` of the first of 9 sampled tiles whose `+1 & 0xe0 > 0x5f`, else 0 (shard_015.c:4716-4741); values 0x3f/0x01/0x00/0x10 seen, `+3` unnamed | rule V, meaning OPEN | OPEN |

## M248/M249 (s198, PASS 5/5) — the region map's bytes are a per-region copy of terrain record +3, the map's REGION LABEL

| claim | evidence | conf |
|---|---|---|
| region byte = record +3 of the FIRST land tile of a centre-first 9-diamond sample at (x*5+dx, y*5+dy), 0 if no land; x wraps mod DAT_0092a378, y only bounded by DAT_0092a37c | `FUN_0058ce00` shard_015.c:4690-4752; (dx,dy) read from terran.exe 0x67850c/0x678990 = (0,0)(1,-1)(2,0)(1,1)(0,2)(-1,1)(-2,0)(-1,-1)(0,-2); G1 9/9 | V |
| stored region map == recomputed, byte for byte | 19 files (17 saves + 2 .MP), 1809 written cells, 0 mismatches, 38 wrapped samples — G2, `evidence/m248_region_values.txt` | V |
| the region map has exactly 1 reader fn (`FUN_00556690`, shard_014.c:3450/3469) and 1 writer fn (`FUN_0058ce00`, shard_015.c:4739); 17 other refs = alloc/free/file-io/null-guard/clear in shard_014.c | G3 | V |
| record +3's ONLY writer is the byte setter `FUN_00582d00` (shard_014.c:27745); 4 call sites, all map generation: shard_015.c:4862/4892 `FUN_0058d120`, :5086/5097 `FUN_0058d390` | G4 (18 record-array stores, 1 covers byte 3) | V |
| +3 plane identical across 17 saves spanning turns 50,51,52,53,60 | G4 | V |
| +3 < 0x40 on every land tile, >= 0x41 on every water tile, 0x40 unused (0 exceptions, 19 files); land ids 18/25/62 at 64/80/128; used as index into a per-faction array at DAT_0094eda8 (stride 0x20bc) shard_012.c:2681-2683 and split at 0x40 shard_012.c:7336 | G5 | V (census), OPEN (what names the partition; ids repeat across disconnected groups: 25 ids / 47 components, 130/16626 adjacencies differ) |
| instrument: `scripts/m248_region_values_census.py` -> `evidence/m248_region_values.txt` | rc=0 | H |

(§rotation-1 ends; anything below belongs to a later rotation.)

§rotation-2 (M250-M254, s316-chain1 review-round headroom rotation)
## M250 (s200, PASS 7/7) — the region generator: 3 callers, and the coarse map is built LAST inside it

| claim | evidence | conf |
|---|---|---|
| `FUN_0058d390` (0x58d390, 1293 B) has exactly 3 call sites image-wide: `0x5add8f` `FUN_005add30`, `0x5af0c7` `FUN_005af0c0`, `0x5b09e3` `FUN_005b09b0` | G1, `evidence/m250_region_generation.txt:1` | V |
| the new-game driver is `FUN_005b2970` (shard_015.c:28040-28115, 4 call sites `FUN_004e10c0`/`FUN_004e11b0`/`FUN_0057c550`/`FUN_0057ecf0`): `FUN_00582170` → placement loop → `FUN_005add30`→`FUN_0058d390`, then the loop condition `FUN_005af0c0()` re-runs the generator and votes retry (≤4, while `DAT_00985ae8 & 0x80 == 0`); `FUN_005b09b0` = the "ADJUSTING WORLD CLIMATE" stage (22 sites) re-runs it | G1 + shard_015.c:24616/25519/26549/28102-28108 | V (static), OPEN (which driver site is NEW GAME) |
| inside `FUN_0058d390` the flood-fill `call 0x58d120` @`0x58d47e` is enclosed by BOTH scan back edges (`0x58d5fa→0x58d3f9`, `0x58d60c→0x58d3e2`); `FUN_0058ce00` @`0x58d88c` is enclosed by NONE and is the last call but one (`0x58d891` = `FUN_005e9e0d`, the free) | G3 | V |
| id bands: land `1..0x3e`, water `0x41..0x7e` (`0x40` never assigned — counter pre-incremented), overflow `0x3f`/`0x7f` for the border rings (`and ..,0x40; add ..,0x3f`, 2 sites) and for the band-exhaustion merge (smallest region relocated, shard_015.c:5007-5073) — explains M249's "25 ids / 47 components" | G4 (immediates 0x3e/0x7e/0x3f = 1/1/2), shard_015.c:4976-5101 | V |
| region table `DAT_00989ce0`, stride `0x1c` (7 dwords via `lea [r*8+0]`+`sub`, 8 folds, 13 refs in d390 / 4 in d120): dword 0 = tile count, `+0x14` = 8-byte bitmap of adjacent opposite-class regions (`FUN_00507410` bit index, shard_015.c:5119-5160) | G4 | V |
| instrument: `python3 scripts/m250_region_generation.py` → `SUMMARY PASS: 7/7` | rc=0, 2.7 s, one invocation, static image | V |

## M251 (s200, PASS 7/7) — `DAT_0094eda8` = the per-faction, per-REGION category byte (128 ids, 4 values)

| claim | evidence | conf |
|---|---|---|
| shape `[region + faction*0x20bc]` byte array, base exactly `0x94eda8`; 128 entries (the stage's region loop `cmp reg,0x80` @`0x556737`/`0x558b1c`) | shard_014.c:2159/2217/2220, G5 | V |
| 79 refs in 18 functions; **6 store sites in 2 writers**: `FUN_00556690` ×5 (`0x557fdf`=8, `0x558516`=dl, `0x558549`=0, `0x55855e`=2, `0x55856b`=7), `FUN_0055f650` ×1 (`0x564ad7`=7); values written exactly {0,2,7,8} | G5, `evidence/m250_region_generation.txt:5` | V |
| effects: `< 2` preferred candidate (+1000, shard_014.c:3409-3411); `== 7` accepted at face score (:3429); `== 8` accepted only if `DAT_00989ce0[region] < 0x96` (150 tiles, :3439), raises `FUN_00556370`'s divisor 2→4 and decrements `FUN_00556150`'s 1..10 score; `== 2` blocks the pick and forces `FUN_00556370` to 1 | :3409-3440, :2159-2224 | V (effects), OPEN (which value NAMES which state) |
| reset per pass: the 4 reserved ids (`id & 0x3f` ∈ {0,0x3f} → 0, 0x3f, 0x40, 0x7f) with score 0 are stamped 8 (:3188-3191); every water id ends at 7 (:3583) | :3188-3191, :3583 | V |
| siblings in the same block, same index: `0x94e4a8` short ×128 (ends exactly at `0x94e5a8`), `0x94e5a8` byte SCORE, `0x94e628` (cleared per region), `0x94e7a8` flag bytes | G5 + shard_014.c:3188-3300 | V (addressing), OPEN (meanings) |

## M252 (s200, PASS 7/7) — the coarse region map has ONE consumer: `FUN_00556690`'s site search

| claim | evidence | conf |
|---|---|---|
| the coarse accessor `FUN_00582340` is called at exactly 2 sites in the image, both inside `FUN_00556690` (`0x55878a`, `0x558812`) | G6/G7, `evidence/m250_region_generation.txt:6-7` | V |
| `FUN_00556690` (14 349 B) is called only from `FUN_005208f0` `0x52094f` and `FUN_0059ce10` `0x59dd43` (M94's per-player upkeep sequence) | G7 | V |
| the search walks the coarse grid by its own dims (`DAT_0092ad9c` × `DAT_0092ada0`, 7 refs), keeps cells whose label == the candidate region, converts cell → terrain `x = cell*5`, scans neighbour footprints for land tiles, scores them | shard_014.c:3443-3556 | V |
| the winner is gated by the terraform cost `FUN_004cc7b0` (2 calls in the stage) against the faction's budget, then issued as `FUN_0056d350(faction, 0x29, 2, x, y, -1)`; both `push 0x29` sites (`0x556a47`, `0x558ad9`) reach a `call 0x56d350` 3 insns later | G6 | V |
| so the coarse map is the SPATIAL INDEX for "where is region R", not a minimap layer | G6/G7 + the 2-site census | V |
## M253 (s201, PASS 8/8) — the four region verdict codes are named by the guard that writes each

| claim | evidence | conf |
|---|---|---|
| `DAT_0094eda8[region + fac*0x20bc]` is a verdict code, not a category label: **8 = the reserved ids with nothing scored** — `0x557fdf` is reached only after `and eax,0x3f` + (`cmp eax,0x3f` or `test eax,eax` zero) + `test al,[..0x94e5a8]` zero, and is followed by `jmp 0x558b18` (the region loop tail: the region is skipped) | G4, `evidence/m253_region_categories.txt:4` | V |
| **7 vs 8 = the worth test's boolean + 7**: `sete dl; add dl,0x7` -> `mov BYTE PTR [esi+edi*1+0x94eda8],dl` at `0x558516` | G4, `:4` | V |
| **the water band always ends at 7**: `0x55856b` lies between `cmp edi,0x40` / `jl 0x558578` and `jmp 0x558b18` — id >= 0x40 stores 7 and the region is done (M251's "every water id ends at 7", now pinned to the band test) | G4, `:4` | V |
| **0 = cleared-open** under `test BYTE PTR [ebp-0x40],0x2` (`0x558549`); **2 = contested** under `test [ebp-0x40],0x1` (`0x55855e`) — the 2-store comes AFTER the 0-store, so a single contact verdict wins | G4, `:4`; names from M254 | V (guards), INFERRED (names) |
| consumer domain: 33 `cmp BYTE PTR [..],imm` and 21 `cmp <reg>,imm` right after a load test **exactly {2,7,8}**; 39 plain loads; 0 unclassified; nothing tests 0/1/3/4/5/6 and 1 is never written | G1/G2, `:1-2` | V |
| effects re-pinned: `+1000` at `0x55863d`; `cmp al,0x7` at `0x5586f9`; the 8-arm size gate `cmp DWORD PTR [edx*4+0x989ce0],0x96` with `edx = region*7` (`lea [r*8]`+`sub` fold of the M250 stride-0x1c table, dword 0 = tile count) at `0x55870e` | G3, `:3` | V |

## M254 (s201, PASS 8/8) — the two bits come from FUN_00531bf0: contact between two factions inside one region

| claim | evidence | conf |
|---|---|---|
| the stage's accumulator `[ebp-0x40]` has exactly ONE computed write: `test ecx,ecx; mov eax,0x1; jne 0x558349; mov eax,0x2; or DWORD PTR [ebp-0x40],eax` — only {1,2} are ever OR'd in, only masks {1,2} are ever tested | G5, `evidence/m253_region_categories.txt:5` | V |
| `FUN_00531bf0(facA, facB, region, mode)` (505 B, 10 call sites, 2 inside `FUN_00556690`) walks the unit array over terrain records at `DAT_0092ae14`, keeps a facA unit whose record byte +3 (the region label, M249) == the region, then seeks a facB unit in the same region and calls `FUN_0058b1b0` (route) / `FUN_0058cfc0`; returns 1 iff a route is found | G5, `:5` + shard_013 body | V (shape), INFERRED (route) |
| so **bit 1 = contact -> 2 = CONTESTED (blocks the pick)**, **bit 2 = no contact -> 0 = OPEN (the +1000 candidate)** | G4+G5 pairing | INFERRED (named) |
| `FUN_0055f650`'s only store promotes **8 -> 7** at `0x564ad7` under `cmp DWORD PTR [ebp-0x8c],0x8`, in the same window as `add WORD PTR [eax+0x94eaa8],0xfff6` (-10) and `or BYTE PTR [eax+0x94e7a8],0x9` — the auto-manager clears the not-worth verdict when it acts in the region | G4, `:4` | V (code), INFERRED (why) |

(§rotation-2 ends; anything above belongs to §rotation-1.)
