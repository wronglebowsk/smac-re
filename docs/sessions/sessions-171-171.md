# Session notes archive — sessions 171-171

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 171 (cont. 19) — M127-M129 (all PASS): the plan byte's 369 readers, the seek pair in code, the three-condition consume

`python3 scripts/m127_m129_fields.py` — SUMMARY M127=PASS M128=PASS M129=PASS (evidence/m127_m129.log).

- **M127 — the open item "zero sites read plan byte `+42`" is RETRACTED: 369 sites read it.** The type-record PLAN byte
  is `0x98adb2` (= `0x98ad88 + type*52 + 42`) and it has **369 references**, of which **149 are the folded
  `[reg*4+0x98adb2]` form** (reg holds `tid*13`, so *4 = tid*52, the record stride) and **0 use a literal `+0x2a]`**.
  M67's earlier search grepped the literal displacement and therefore could not see any of them; the live-verified
  plan-descending order now has static readers behind it (top: FUN_00502cd0 48, FUN_0055f650 33, FUN_004f6030 24,
  FUN_0055c920 23, FUN_00585720 17, FUN_00556690 15, FUN_00595b10 14).
- **M128 — the "cursor read before the seek is the PREVIOUS cursor" trap is in the CODE.** `mov ecx,[eax+0xa774]` at
  0x497707 is pushed BEFORE `call 0x4026b0` (the seek, 0x497717); the object is then re-derived
  (`mov ecx,[ebp-0x10]; add ecx,0xa780`) at 0x49771c/0x49771f and `call 0x495480` + `and eax,0x20` (0x49772a) test the
  first flag bit of the POST-seek query. So 0x497704 shows the old node and 0x49771c is the first instruction that sees
  the new one — the rule is structural, not a log artefact.
- **M129 — FUN_00546800's guard is one unit with a CONSUME.** It proceeds only when the faction dword at `0x94d448` has
  bit `0x8000000`, `ds:0x920434 != ebx`, AND the per-record byte `0x92044c` has bit `0x2` — then it **zeroes** that
  byte at 0x5469d3. So `0x92044c` bit 1 is a consumed marker for this path (which is why it reads 0 in the saves and
  after a pass), not persistent state.
Search-shape law added to the skill (second occurrence after the M116 stride): a literal-displacement grep misses the
folded `[reg*4+disp]` encoding; count BOTH forms before saying "no site reads X".

## Session 171 (cont. 20) — M130-M132 (all PASS): chooser case 7 found and named, the 24-byte gap is not a layout, 0x92077c is a mode code

`python3 scripts/m130_m132_chooser.py` — SUMMARY M130=PASS M131=PASS M132=PASS (evidence/m130_m132.log).

- **M130 — "chooser case 7" now has a definition and an answer.** The dispatch is in **FUN_00546800** at 0x54eaeb-0x54eafc:
  `call 0x542ea0` -> `cmp eax,0x7` -> `ja 0x54ec82` -> `jmp DWORD PTR [eax*4+0x54ef34]`. The 8-entry table at
  **0x54ef34** is `[0x54ed3f, 0x54eb03, 0x54eb03, 0x54eb29, 0x54ec34, 0x54ec40, 0x54ec4c, 0x54ec58]`: cases 1 and 2 share
  0x54eb03, case 3 is 0x54eb29, cases 4/5/6 are 0x54ec34/40/4c, and **case 7 = 0x54ec58** — the only case that writes a
  state PAIR: `ds:0x920700 = 0xc` and `ds:0x92077c = 1`. (My earlier scan missed it because it looked for a switch in
  0x5a6xxx-0x5aaxxx; the dispatch is keyed on the return of FUN_00542ea0, not on a chooser-internal enum.)
- **M131 — the 24-byte gap between 0x920434 and 0x92044c is NOT a record layout.** 0x92044c: 24 refs, **24 folded**
  (`[reg*4+0x92044c]`, reg = tid*13 -> tid*52). 0x920434: 634 refs, **0 folded** — a standalone global (M125's
  reset-published id). Treating 0x920434 as the `+0` field of that record would have fabricated a layout out of two
  neighbouring addresses; the M127 law caught it in one command.
- **M132 — ds:0x92077c is a MODE CODE with a small domain.** 4 writes (two of them the constant 1, one `ebx`, one `eax`),
  9 tests against **1, 3, 7**, plus a copy compared to **6** at the dispatch (0x54eb1b, right after the case-1/2 body).
  Its partner `ds:0x920700` has 8 writes and is set in the same case-7 body, so the two form a (state, mode) pair.
  Meaning NOT named: no string constant sits within 8 instructions of any write — recorded as a bounded unknown.
