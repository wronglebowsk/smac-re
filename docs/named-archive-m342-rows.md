# NAMED.md `## M342` - ROTATED VERBATIM (byte-exact) by scripts/m386_named_rotate.py

## M342 (s322-chain1, ANALYSE, static, zero box; ACCEPT `python3 -u scripts/m342_completion_setter.py` -> **`PASS M342: 7/7 gates`**, table digest `2b88df5da5aeafe1` (PINNED, G7), 2 runs identical (`evidence/m342_completion_setter.txt:200,:218`); harness `scripts/m342_mutate.py` -> **9/9**, NO-OP `[]`, baseline green (`evidence/m342_mutate.txt:2,:12`)) — pick (x9) ANSWERED: the `base+0x8c` bit is SET by `or` through the mapper's mask at **11 addresses**, the API `FUN_004e44f0` first; the queue-pop is a NON-writer. (M329 rotated VERBATIM to `docs/named-archive-m329-rows.md:5`, sha1 `ccee72a56f16b4b4`.)

| claim | evidence | conf |
|---|---|---|
| the record array base is DERIVED as `0x95da10` from the owner site `0x440dbc` (`imul r,r,0x130` then a BYTE read of `0x95da14` = field +4), so `0x95da9c` = record+0x8c and is byte-identical to the charge routine's own read at `0x4f4837` (rival `+0x88` fails) | `evidence/m342_completion_setter.txt:4-8` | V MU1 |
| the field has exactly 2 writer idioms: **11 direct constant-form stores** in exactly 2 Ghidra functions (`FUN_0041cf20` 1 whole-byte copy, `FUN_004e47d0` 7 `or` + 3 copies) and **9 pointer-form `lea` sites, 9/9 resolved to a store through that register** (2 copy / 4 `or` / 3 `and`) | `:9-72`,`:86`,`:204` | V MU2/MU8 |
| SET = 11 `or` addresses (`4e4528 4e4b5a 4e4b87 4e4bec 4e4c16 4e4c3d 4e4c83 4e4d81 4f0ec0 4f3ebc 4f3f4c`); CLEAR = 3 `and` (`4e4546 4f38bb 4f49e1`, the last inside the charge routine `FUN_004f47f0`) | `:210-216` | V MU2/MU8 |
| the API `FUN_004e44f0` (92 B) is the first SET address: `or BYTE PTR [eax],cl` @`0x4e4528` after the 304-fold (`0x4e4512-0x4e451e`), index = mapper out1 slot `[ebp+0x8]`, mask = out2 slot `[ebp-0x4]`; its AND twin @`0x4e4546` clears | `:99-113`,`:205` | V MU3 |
| 27 call sites in 8 functions: 16 push set=1, **8 set=0, 3 variable** — M344 re-derived this with a 16-insn push window; the shipped 16/7/4 read `0x40dd3c` as '?' because its `push 0x0` sits 7 instructions back | `:129-158`,`:206`; `evidence/m344_completion_caller.txt:36-38` | V MU4 (M344 MU1/MU2) |
| the queue-pop `FUN_004ef5d0` (244 B, 3 direct callers all inside `FUN_004ef6d0`) has 0 references to `0x95da9c` and 0 API calls: the pop does not stamp | `:160-177`,`:207` | V MU5 |
| inline grant `FUN_004e47d0`: 7 ORs + 3 copies, 7/7 OR masks loaded from a stack slot the mapper filled | `:180-191`,`:208` | V MU6 |
| the printed digest is PINNED by G7 - the ACCEPT anchor cannot drift silently | `:200`,`:209` | V MU7 |
| OPEN: which of the 27 API call sites is the production-completion call; 3 pointer writers (`0x4f38b0`, `0x4f3eb1`, `0x4f3f3e`) sit in regions the Ghidra index does NOT name (semantics unidentified); projects 39..71 unmeasured | - | lead |

