# NAMED.md `## M344` - ROTATED VERBATIM (byte-exact) by scripts/m348_named_rotate.py

rotated by `scripts/m348_named_rotate.py`; sha1 `e7b59fa35e2635c8134b97152e7bdcd280b521d6` of the block below.
<!-- block: every byte below is the original NAMED.md block -->
## M344 (s323-chain1, ANALYSE, static; ACCEPT `scripts/m344_completion_caller.py` -> **`PASS M344: 8/8 gates`**, digest `034bf0e1a1606d2c`, 2 runs identical (`evidence/m344_completion_caller.txt:148`); harness `scripts/m344_mutate.py` -> **10/10**, NO-OP `[]` (`evidence/m344_mutate.txt:14`)) — NO API caller completes production: the stamp is the base screen's inline `or` @`0x4f0ec0`.

| claim | evidence | conf |
|---|---|---|
| all 27 item args resolve (imm 18 / callret 3 / clamped 2 / loopctr 2 / param 2); split **16 set=1 / 8 set=0 / 3 variable** — M342's 16/7/4 read `0x40dd3c` as '?' (its `push 0x0` sits 7 insns back); only divergent row of 27 | `:4-38` | V MU1,MU2,MU3 |
| **0/27** items' resolved class is QUEUE (the base record window `+0x4c..+0x77`); **0/8** caller functions calls the pop | `:34`,`:40-49`,`:141`,`:145` | V MU4 |
| the 4 register-item set=1 sites: `0x41c6f8` (modal-runner return + bitmap pre-read = toggle), `0x41d8fc` (loop counter under `0x5a6e70`), `0x508c85`/`0x508cee` (1..0x26 clamp) | `:127-131` | V MU5 |
| stamp = `or BYTE PTR [eax],cl` @`0x4f0ec0` in FUN_004ef6d0: mapper(item=`edi`) -> 304*`ds:0x68cbb0`, 10 pinned insns, **0x86** before the byte-read `call 0x4ef5d0` (pop) @`0x4f0f46` | `:51-70`,`:143`,`:145` | V MU6,MU8 |
| the same block spends `[edx+0x40]` by `edi` (`0x4f0ca4/6`) then reads `[edi*48+0x984d38]` (`0x4f0f65-6f`), `edi` unwritten in between | `:112-124`,`:144` | V MU7 |
| CLOSED by `## M346`: the build-finished ALERT is this same block's two posts (0x6265a2 kind 1 @0x4f0f78, 0x626634 kind 2 @0x4f0f96) into the 10-slot text bank (M348: the consumer is Script.txt `#PRODUCEXQ/G`; FUN_00636b1e is the Create Session dialog, NOT a drainer - `evidence/m348_slot_template.txt:63-69`); `0x985b10` is refuted as the channel | `evidence/m346_alert_raiser.txt:72-84` | V MU12 (M348) |
| the 8 caller ROLES; `edx` at `0x4f0ca1` = the base record; `+0x40` = accumulated minerals; `edi` = the completed item | `:40-50` | INFERRED |
