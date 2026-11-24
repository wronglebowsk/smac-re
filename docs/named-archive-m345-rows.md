# NAMED.md `## M345` - ROTATED VERBATIM (byte-exact) by scripts/m348_named_rotate.py

rotated by `scripts/m348_named_rotate.py`; sha1 `907d07053aedb079cfd353ed7f7dcfd538f5ba60` of the block below.
<!-- block: every byte below is the original NAMED.md block -->
## M345 (s324-chain2, 12/12) — the dialog family `+0x64` commit slot has no .text dispatcher

| claim | evidence | conf |
|---|---|---|
| slot `0x5f58fa` = 5 data dwords, all a family vt+0x64; 0 `.text` operands (no call/thunk/lea) | `evidence/m345_slot64_dispatch.txt:3-10` | V MU1,MU3,MU2 |
| ctor 0x405ef0: 0x67164c at +0, CPane 0x671644 at +0x444 -> its `+0x6c` IS the primary `+0x64` | `:16,:93` | V MU1,MU4 |
| trio `+0x60`/`+0x64`/`+0x68` = 5f59bf ret8 / 5f58fa ret4 / 5f59e8 | `:12-15` | V MU5 |
| universe = 19 `[r+0x64]` + 18 `[r+0x6c]` calls, 0 jmp, 0 in the dialog module | `:18-57,:86-89` | V MU6,MU10 |
| arity {0:3,1:5,5:8,6:3}: 5 fit ret 4 = 3 MEMBER + 2 self, none a dialog | `:59-65,:100` | V MU8,MU9 |
| module's 4 `[r+0x64]` are movs; 5f49ad/b9 swaps `[this+0x2240]+0x64` | `:67-77,:102` | V MU7,MU10 |
| ACCEPT `m345_slot64_dispatch` -> `PASS M345: 12/12` `833faf38e189ad40` x2; harness 11/11 | `:104` | V MU0 |
| OPEN: MEMBER-receiver classes (+0xf624/+0xd9ec/+0x3870/+0x270c) untyped | - | lead |
