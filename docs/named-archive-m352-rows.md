# NAMED.md `## M350` — ROTATED VERBATIM by `scripts/m352_named_rotate.py`
# (content byte-exact after trailing-newline normalisation; the M352 correction to the
#  OPEN row was made IN NAMED.md before this rotation and is preserved below)
<!-- block: every byte below is the original NAMED.md block -->
sha1=57fc3a064e5044d474055cef54a45ee9d60eb982 bytes=1498 rows=6

## M350 (s326-chain3, ANALYSE, static; ACCEPT `scripts/m350_pref_cowriters.py` -> **`PASS M350: 6/6`** `23794d22`, x2 (`m350_pref_cowriters.txt:16` + `m350_x2.txt:4`); harness 15/15 (`m350_mutate.txt:36`)) — pref block = 11 scalars + a 7-dword `Custom World` list, END **0x92bf34**; co-writes are screen COMMITs. `:N` = a line of the ACCEPT's evidence file.
| claim | ev | conf |
|---|---|---|
| FUN_0058e7f0 = the block's only profile-backed INITIALISER: 11 stores, 1/cell, eax from a 0x5ea484/93 parse with no eax write between; the 11 co-STORE fns make 0 profile reads (loader 18 of 84 image-wide). Parse consumed the PUSHED key = INFERRED | `:3-16,162` | V MU1,2,14,15 |
| EXTENT: 7 dwords by POINTER (`esi=0x92bf18`,`add esi,4`,`cmp 0x92bf34`) under `Custom World`; writeback re-reads the loop; 0 disp refs -> why the old census ended at 0x92bf14 | `:54-69,157` | V MU3-5 |
| 57 co-refs / 32 scalar co-stores in 14 scalar fns (10 store + 4 read-only); +1 at Custom World[0]; byte scan 88 == 82 text + 6 materialisations | `:70-95` | V MU8,11,12,13 |
| LAW: 24 COMMIT / 9 TAIL-NONE of 33; in-function value 0/11 loader vs 28/33 co (5 call-fed); 31 outside, 2 self-RMW | `:96-133,160` | V MU6,7,9,15 |
| publisher 0x58f3d0: 3 direction-checked, register-matched stores 0x92befc/bf00/bf04 -> 0x985ab8/abc/c0 | `:144-155` | V MU10 |
| ANSWERED (M352): `ds:0x6926ec` = the .data literal "Prefs Format"; the writeback's 8 `call edi` = KERNEL32!WritePrivateProfileStringA | `## M352` | V MU10,MU2 |

