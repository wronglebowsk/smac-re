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
