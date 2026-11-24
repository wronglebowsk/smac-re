# NAMED.md `## M335` - ROTATED VERBATIM (byte-exact) by scripts/m387_named_rotate.py

## M335 (s317-chain2, pick (x6), STATIC 7/7) — the difficulty LADDER: `ds:0x985aec` indexes alpha.txt's six `#DIFF` names at `0x94d2ac` in file order; 4 = Thinker, 5 = Transcend

| claim | evidence | conf |
|---|---|---|
| alpha.txt has ONE `#DIFF` section, 6 rows in file order Citizen/Specialist/Talent/Librarian/Thinker/Transcend | `evidence/m335_difficulty_ladder.txt:2` | V MU4,5 |
| loader `push "DIFF"`@0x57ac56 -> `call 0x5ea431` -> fill `0x94d2ac`, `add esi,4`, `cmp 0x94d2c4`/`jl` = 6 iterations == 6 file rows (the count is the immediate, never read from the file) | `:3` | V MU1,2,3 |
| census with token-boundary matching over all addressing forms (7 scaled): exactly 11 sites on `0x94d2ac..0x94d2c4`, 0 literal-address STORES; scope: a register-indirect store elsewhere is NOT excluded | `:4` | V MU1,6,13,20 |
| ORDER: in 0x4ddaf8..0x4ddb60 the 11 fragments occur in the order base-load, `[esi]`, resolve, `push edi`, append, `add esi,4`, `inc edi`, `cmp 0x94d2c4`, `jl 0x4ddaff`; `edi` starts at 0 and the seed `ds:0x985aec`->`[ebp-0x494c]` precedes `call 0x5f1394` | `:5` | V MU10,11,14,15 |
| INDEX: `0x599405` `mov ecx,ds:0x985aec; mov edx,[ecx*4+0x94d2ac]`; both other readers are COUNTING loops 0..5 over the table (`cmp [slot],6` + `add eax,1`->same slot + `jmp` back) at `0x484cb3`,`0x485410` | `:6` | V MU7,12,19 |
| DOMAIN (geometry READ from the bytes, not from the script): base 0x94d2ac, bound 0x94d2c4 and clamp hi=6 with `hi*4 == end-base`, so the INCLUSIVE hi is the array LENGTH = one past the last row; of 169 `call 0x423af0` sites exactly 1 (`0x486f38`) is fed by an `0x8f0c11` load; cmp immediates on `0x985aec` = {1,2,3,4}+ebx (M332 reproduced); refund 3/jle + 4/jne => k=1 at 4, k=2 at >=5 = TRANSCEND (M330 refined) | `:7` | V MU8,9,16,17 |
| RIVAL killed: "0x94d2ac is not the difficulty names" — section string + row count + iteration count agree | `:8` | V MU3,4,5,13 |
| ACCEPT `7/7` digest `fb58bdc3307d6258` x2 (`:9-10`,`_rerun.txt`); harness `20/20` `6e0e05a8ffb388d8` incl. an ALGORITHM mutant (`--selftest` 3/3, `evidence/m335_mutate_selftest.txt:4`) | `evidence/m335_mutate.txt:22-23` | V |
| OPEN: a non-UI writer putting 6+ into `0x8f0c11`/`0x985aec` (the inclusive clamp would index `0x94d2c4`, outside the table); FUN_0060c555's API; index provenance of 0x44a1c8 / 0x48678f / 0x57c606 | - | lead |

