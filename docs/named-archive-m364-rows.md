# NAMED.md blocks ROTATED VERBATIM by `scripts/m364_named_rotate.py`
(byte-exact; each stub in NAMED.md carries the block's sha1 and byte count)


## M247 (s197) — the region map's row stride is `Rw>>1`, not `(Rw+1)/2` — rows in the same archived region; this stub governs.
- 6 referencing functions; the only element accessors `FUN_00582340`/`FUN_00582360` index `(param_1>>1)+DAT_0092ae18+(DAT_0092ad9c>>1)*param_2`; `(Rw+1)/2` occurs once image-wide (the length) | G4 | V
- builder `FUN_0058ce00` (y<Rh, x=(y&1) step 2<Rw) writes exactly bytes 0..78 at Rw=Rh=13; slack = Rh−1 for odd Rw, else 0 | G5 | V
- the slack is never written: bytes 79..90 = `0xcd` in 17/17 saves, none in 0..78; both .MP (even Rw) slack 0 | 17 saves + 2 .MP | V
- the byte VALUES: terrain record `+3` of the first of 9 sampled tiles with `+1 & 0xe0 > 0x5f`, else 0; `+3` unnamed | rule V, meaning OPEN



## M248/M249 (s198, PASS 5/5) — the region map's bytes are a per-region copy of terrain record +3, the map's REGION LABEL — rows in the same archived region; this stub governs.
- region byte = record +3 of the FIRST land tile of a centre-first 9-diamond sample at (x*5+dx, y*5+dy), 0 if no land; x wraps mod DAT_0092a378, y bounded by DAT_0092a37c; the 9 (dx,dy) read from 0x67850c/0x678990 | `FUN_0058ce00` shard_015.c:4690-4752, G1 9/9 | V
- stored == recomputed byte for byte: 19 files, 1809 cells, 0 mismatches, 38 wrapped samples | G2, `evidence/m248_region_values.txt` | V
- exactly 1 reader fn (`FUN_00556690`), 1 writer fn (`FUN_0058ce00`); 17 other refs = alloc/free/file-io/null-guard/clear | G3 | V
- record +3's ONLY writer is `FUN_00582d00`; 4 call sites, all map generation | G4 (18 record-array stores, 1 covers byte 3) | V
- +3 plane identical across 17 saves, turns 50,51,52,53,60 | G4 | V
- +3 < 0x40 on every land tile, >= 0x41 on every water tile, 0x40 unused (19 files); index into DAT_0094eda8 (stride 0x20bc), split at 0x40 | G5 | V (census), OPEN (what names the partition; 25 ids / 47 components, 130/16626 adjacencies differ)
- instrument `scripts/m248_region_values_census.py` -> `evidence/m248_region_values.txt` | rc=0 | H



## M259-M261 (s204, PASS 14/14) — the per-faction mask band, the static map views, the 0x679f98 class — FULL rows VERBATIM at `docs/named-archive-m333-rows.md:6` (§rotation-1, s313-chain1 headroom rotation, sha1 `f78e7ef04359` — the region is bounded by an explicit terminator line, its line number AND full digest re-asserted by `scripts/m333_named_rotate.py --verify`); this stub governs. Pre-mutation-law registry (no MU ids — the harness era starts at `## M308`); the G-ids are the archive rows' own gates, and the byte-reads they printed are `evidence/m259_m261_census.txt` (`:30` SUMMARY 14/14, one invocation, 3.3 s).
- M259 the band: terrain record bytes +16..+43 (dwords 4..10) = the FACTIONS 1..7 per-faction copies of the record's `+8` master mask, `[terrain_base + 0xc + (row*0xb + fac)*4]` (faction 0 uses `+8`; both whole-array refreshes guard `test ebx,ebx / je`); writers CLOSED at 10 indexed + 1 walk store, every site named (G1-G6); 44 indexed reads in 25 functions (G7). **RETRACTS M240's "a record is two 22-byte map columns" for bytes 16..43** — the `.MP` "7 equal dwords == +8" (planetx 8192/8192) IS this band.
- M260 the views: the live 0x224b8 spacing occurs 0 times in the 3,067,904-B image — `immediates naming 0x224b8: 0; 4-byte LE pattern ... offset -1` (G8, `evidence/m259_m261_census.txt:16-17`); view 0 is static .bss at 0x8f79e0 (sole immediate store 0x5803e1, printed by G10 at `evidence/m259_m261_census.txt:21`; ctor FUN_00518820's only call site 0x580406, G9); the ctor's stores reach `this+0x23bec` = 146,412 B > the 140,472 stride, so the stride is not an object size (G10 `evidence/m259_m261_census.txt:20-21`); the save codec walks the 8 entries as POINTERS, clearing `*(p+0x1dd74)` for entries 1..7 only (G11). **CORRECTED IN PLACE by M262 — RETRACTED: "the ~140 KB views are not allocated"**: entries 1..7 ARE allocated at startup, 0x22480 B each, by the pointer-arithmetic `mov [esi],eax` at 0x5803bb (0 only on the alloc-failure path) — M262's own rows: `docs/named-archive-m332-rows.md` (G2), `evidence/m262_m264_census.txt:24` (11/11); 0x224b8 = 0x22480 + 0x38, a 56-B heap header (INFERRED).
- M261 the class: vtable 0x679f98 = 88 slots, 2 installs, 15 slots differ from ALL of 0x6717cc/0x671d94/0x67164c (G12); all 15 named with size + callee count (G13); ctor chains FUN_0062d630 <- FUN_0045a8b0(1)/FUN_005b3000(2)/FUN_00641f3c(3) and FUN_0062d764 <- 6 callers, incl. FUN_00636b1e = "Start a new session or..." (session chooser) and FUN_00493a10 = "Gamma Correction" (G14).



## M283 (s227, PASS 17/17) - decode_save --sections walks 64x64 saves; the coarse-region-map length is dims-derived, not a hardcoded 80x80 128
- The MAP branch hardcoded the coarse region map at 128 B. That map is
  ((W+4)/5+1)/2 * (H+4)/5 bytes (FUN_00582000, shard_014.c:27263-27265; same formula as
  sim/save.py region_len): 128 for 80x80, 91 for 64x64, 338 for 128x128. With 128 hardcoded,
  every 64x64 save mis-read the count-prefixed section 37 B early and --sections died with
  "no 52/304 split of a 0-byte region" (rc=1). walk() now reads W,H from the map header
  struct and computes the length; the section table sums to the file byte on all 17 repo
  saves (all 64x64) and the count u32 sits at 188,299 on all of them (sim/save.py predicted).
- Acceptance: `python3 scripts/m283_sections_64x64.py` -> 17/17 gates
  (`evidence/m283_sections_64x64.txt`). B10's gate that encoded the OLD failure ("rc == rc;
  --sections fails on both") was updated to require rc 0 == rc 0 plus the grown image showing
  exactly one more 304-B record (67x52+19x304 vs 67x52+18x304); B8/B9/B10 regressions green.

