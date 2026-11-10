# Session notes archive — sessions 197-197

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 197 (2026-11-01, M245/M246/M247 ANALYSE — the tail's last three legs)

`sudo -n python3 scripts/m245_tail_legs_census.py` -> `PASS M245: 5/5 gates` (rc=0; 3rd invocation:
the 1st was 4/5 because G2 demanded that EXACTLY ONE save match the live 216 B — the box refuted the
premise, 7/17 match because those saves come from one session without scrolling; the byte-for-byte
equality is unchanged, the gate now asks for >=1 match and NOT all 17) -> evidence/m245_tail_legs.txt.
`sudo -n python3 scripts/smac_preflight.py` -> PASS 14 invariants. Box: /proc reads only, terran.exe
319926 TracerPid 0, no gdb.

- M245 the 216-B leg (EOF-228..EOF-12) = 9 map-view objects x 6 fields. Codec loop
  (shard_015.c:10807-10822): `puVar18 = &DAT_007cdecc; do FUN_00596620(*puVar18,..) while ((int)
  puVar18 < 0x7cdeec); FUN_00596620(&DAT_008cda4c,..)` = 8 heap pointers (live 0x8f79e0, then
  0x3b5f4e8… spaced 0x224b8) + 1 inline object. Fields (FUN_00596620's order): +0x1dd78 view id
  (rows 0..7 = 0..7 on 17/17 saves, inline row = 1), +0x1dd74 active flag (set FUN_00469860
  shard_008.c:5894; cleared by the codec's load leg shard_015.c:10845 when the [800,387] pair changes
  and by 4 invalidators), +0x1dd70 bit flags (tested shard_008.c:8983/9033/9076/9318), +0x1dd98 = -6
  while DAT_0091c18c < 1000 (5892), +0x1dd9c/+0x1dda0 centre tile (init W/2,H/2 5895-5898; set by
  FUN_004739a0 :10117-10124). The window bounds +0x1ddcc..0x1ddc8 and origins +0x1dda4/+0x1dda8 are
  DERIVED from the centre by FUN_00469860:5949-6017 and read by the click hit test FUN_00422060
  (shard_001.c:14164-14183). Live read-back == 7/17 saves' 216 B byte for byte (10 differ); live
  DAT_0091c188/c18c = 387/800 = the 8-B leg; Autosave 1 rows 0-1 centre (28,42) = University Base.
- M246 the final 4 B = `local_8 = timeGetTime()` (FUN_00597ce0 body line 15) written by
  `FUN_0064c9a0(&local_8,4,1,iVar2)` (line 44) AFTER `FUN_00596850(iVar2,1)` (line 42); the codec
  never reads it. Δ(dword) vs Δ(mtime) ≤ 2.5 s on 5/5 same-session pairs (Autosave 2→1 31 s /
  30,989 ms; m241_probe_A→B 16 s / 16,785 ms); 0x15c79939 sits on 3 files 486,979 s apart and
  0x2db1b939 on 2 files 71,224 s apart -> stamped at save CREATION, not at file write.
- M247 DAT_0092ae18 has 6 referencing functions; the only element accessors FUN_00582340/2360 index
  `(param_1>>1) + DAT_0092ae18 + (DAT_0092ad9c>>1)*param_2` (shard_014.c:27392/27401) and `(Rw+1)/2`
  appears once image-wide (the length, 27266). The builder FUN_0058ce00 (shard_015.c:4707-4747) walks
  y < Rh, x = (y&1) step 2 < Rw, so its write set is exactly bytes 0..78 at 64x64 (Rw=Rh=13): slack =
  Rh-1 when Rw is odd, else 0. The 12 slack bytes are `0xcd` in 17/17 saves (none in 0..78); both .MP
  files have even Rw -> slack 0, no 0xcd.
- OPEN: what the region byte VALUES mean (the builder takes terrain record +3 of the first of 9
  sampled tiles whose +1 & 0xe0 > 0x5f, else 0 — shard_015.c:4716-4741; 0x3f/0x01/0x00/0x10 seen);
  who allocates the ~140 KB view objects; the 7 mask copies at record +16..+43 still stand.
- PITFALL: a byte-for-byte live-vs-file match gate must state what it discriminates. "Exactly one
  file matches" is a premise about the STATE, not about the claim; unchanged state across saves
  breaks it. Require >=1 match AND some files differ.
