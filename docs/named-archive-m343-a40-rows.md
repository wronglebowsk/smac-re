# NAMED.md `## M343` - ROTATED VERBATIM (byte-exact) by scripts/m348_named_rotate.py

rotated by `scripts/m348_named_rotate.py`; sha1 `a7f9573ef60c5314cc322bb625301778e42f15e5` of the block below.
<!-- block: every byte below is the original NAMED.md block -->
## M343 (s323-chain2, STATIC 9/9, review #365 hardened) — the M339 OPEN `[obj+0xa40]` writer: THREE dialog-family methods publish the SELECTED item there; the runner only reads it

| claim | evidence | conf |
|---|---|---|
| census: 97 refs name displacement 0xa40 = 25 indexed (12 fns) + 72 field, all dword (47 stores / 25 reads); 0 `lea reg,[..+0xa40]` and 0 `,0xa40` immediate -> both pointer-form store evasions absent | `evidence/m343_a40_writer.txt:5-22` | V MU1 |
| writers: `FUN_005f5759` (+0xa8 of 0x67164c/0x6717cc/0x6728c0, +0xb0 of 0x671644) x4, `FUN_005f58fa` (+0x64 of the five class vtables; 0x671644 carries it at +0x6c) x3, `FUN_005f5a11` (receiver `ds:0x9977f0`) x2; runner `FUN_005f1394` = 1 READ 0x5f3f45, 0 stores; ctor `FUN_00405ef0` = 0 refs | `:66-77`, `:24-26` | V MU4,MU5,MU2 |
| receiver fingerprint = the PAIR {[+0x21d0] container, [+0x2350] state}: exactly 4 functions carry it (runner + 3 writers); ">=3 of {21d0,2350,30a8,3100}" wrongly admits `FUN_005ee350` + `FUN_005eede6` | `:28-64` | V MU3,MU9 |
| identity: 0x5f13b2 [ebp-0x394]=ecx -> 0x5f3d6a reload -> 0x5f3d70 `ds:0x9977f0` -> 0x5f3e02 restore -> 0x5f3f45 `[ebp-0x394]+0xa40`; 5a11 loads `ds:0x9977f0` into its own local and both stores reload it (10-link chain, adjacency asserted) | `:79-88` | V MU7,MU10 |
| value law: each writer publishes {0 reset, the `[this+0x2228]` -> `[+8]` -> `+0xec` member, `FUN_005fdcf7` on the `+0x21d0` container}; 5a11 has no reset; the -1 at 0x5f581c is reached only from arg == -2 with `[this+0x30a8] & 0x40` | `:66-77`, `:89-99` | V MU6,MU8,MU11 |
| ACCEPT `python3 -u scripts/m343_a40_writer.py` -> `PASS M343: 9/9` `digest=bcdace84a0352b4a` x2; harness `m343_mutate.py` 12/12, NO-OP `[]` | `:118`, `evidence/m343_mutate.txt:25` | V MU0 |
| OPEN: dispatcher of the +0x64 slot (19 `call [reg+0x64]` sites image-wide, 0 direct); the container's item record past +0xec; any consumer of `[this+0x3100]` (5759 stages the arg) | - | lead |
