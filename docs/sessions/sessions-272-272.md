# Session notes archive — sessions 272-272

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-270-271.md` (inserted at s292: the hot file cites only the newest archive, so without this line the older archives were orphans).

## Session 272 (2026-11-17, ANALYSE M310, zero box)

- `track_mode.py` -> `MODE=ANALYSE analyse_since_build=2 next_rung=B22`; took the s271 pick (b):
  FUN_00470b90. No cap split (NEXT_PROMPT 11,110 B). No sibling (no `bash -l`, empty processes.json,
  box not running) - zero box time, no /proc, no gdb.
- **M310 names FUN_00470b90 = the view object's debug-gated GOAL duplicate-invalidator + token
  logger.** `python3 -u scripts/m310_goal_invalidator.py` -> **PASS 32/32 checks OK**, exit 0, two
  runs byte-identical (table sha `801740e655c01d1a`, `evidence/m310_goal_invalidator.txt:159,160`);
  `python3 -u scripts/m310_mutate.py` -> **11/11 mutations reddened their target checks**
  (`evidence/m310_mutate.txt:13`).
- Entry gate: `this+0x1dd70 & 0x2000` (the view bit-flags field, M228-M245) - clear => `je 0x470f83`
  the single epilogue. Outer loop blocks 1..7 filtered by `(ds:0x985ae8 & 0x80) || (block ==
  ds:0x91b5b4)`; two 75-entry scans over the M309 GOAL list (15 `imul 0x20bc` : 15 `shl ...,0x4`).
- Hit = (p1,p2)==(+4,+8) && kind>=0 (skips the -1 free slot) && prio!=0. **prio<0 -> duplicate scan
  j!=i on the same pair AND same KIND (`cmp edx,eax`), and the 0xffff store's fold re-seeds from the
  OUTER index, so it invalidates entry i** (0x470d5c = M308 U2's GOAL sentinel writer). The store is
  followed by a RE-READ + `test/jge`: negative => next entry, non-negative => the log tail.
- Log tail: `FUN_00403a40(buf, unpacked pair, this+0x1ddb4, this+0x1ddb8)` + `FUN_00405220` token
  appends + `FUN_004237f0(|prio|)` (one `neg`) -> `FUN_004081b0(ds:0x997120, buf)`; block name under
  the 0x80 flag clears `BYTE ds:0x997121`. `kind == -1` is unsigned->0x29-above, so an invalidated
  entry NEVER logs.
- The kind->token map is a TWO-TABLE jump: the dword table @0x470f8c holds exactly 8 targets and
  the 42-BYTE index table @0x470fac maps kinds **0,2,3,6,8,9,41** to token blocks and
  **1,4,5,7,10..40** onto the same block 0x470eb7 that the `ja` default uses; tokens are ONE .rdata
  CHAR (0->'a', 2->'d', 3->'s', 6->'n', 8->'c', 9->'f', 41->'^').
- RETRACTION x2 (both MY overclaims, both caught by Greptile on #284, neither is a win over Ghidra):
  (1) "Ghidra's case list (0,2,3,6,8,9,0x29) is REFUTED" is FALSE - 0x29 IS 41, so the list AGREES
  with the bytes; the bytes add the STRUCTURE (42 selectors -> 8 handlers, 35 sharing the default
  that pushes nothing), they do not contradict the C. (2) "the C mis-parses the kind pair as i==i"
  is FALSE - I had not re-read the C; it says `local_10` vs `local_14`, exactly my law. Lesson:
  **never claim a refutation of a tool you can read - re-read it first; agreement is corroboration,
  and manufacturing a win is worse than having none.** The A10 gate itself was also weak in the same
  way Greptile says: it asserted two branch TARGETS while naming a whole predicate; it now pins
  mnemonic AND operand of all 19 instructions in the hit chain plus the branch skeleton (A24), and
  M12/M13/M14 mutate the engine's PARSED INSTRUCTION (not a literal) to prove it.
- Args: 5 call sites in one class cluster (FUN_00470fe0 x4, FUN_004715d0 x3, FUN_00471fd0 x1);
  0x4724bd forwards the 2 output slots of the 29-caller view unpacker FUN_0046a1b0; sites 2/3/4 the
  same `[ebp-0x10],[ebp-0x14]` loop pair; **0 global reads for the compared pair** (A12).
- OPEN: game meaning of a GOAL / of the tokens; WHY a GOAL has negative priority (the only trigger);
  what calls the 3 caller fns; identity of this+0x1ddb4/0x1ddb8; ds:0x68cbb0 and the 304-B table
  0x95da40 bit 0x20 still untouched (deliberate scope).
- PITFALL (own, cost ~8 iterations): a **hand-rolled probe**, not the engine, invented a missing
  instruction - `line.split(None,1)` mangles `movsx` (its bytes field is one column shorter, so the
  remainder starts with a space -> mnemonic parsed as '') and `endswith("0x10")` mis-matches
  `shl ecx,0x4`. Read operands through the engine (`M._INS`) and print `ascii(op)` before claiming
  an instruction is absent. Same class as a decoration: my jump-table "exact set equality" survived a
  `==`->`<=` mutation because the 13/5 counts + 0-overlap already carried the law - the harness found
  it, so it was replaced by a mutation that flips a measured fact (broadening the fold-classifier
  regex), which reddens A8.
