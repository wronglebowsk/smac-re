# Session notes archive — sessions 174-174

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 174e (2026-10-31) — M185-M187, all PASS (second static batch of three, one instrument)

`python3 scripts/m185_m187_visits.py` -> `evidence/m185_m187_visits.txt`, `SUMMARY M185=PASS M186=PASS M187=PASS`.
- **M185 — the visit's two sub-passes are asymmetric in what they touch.** FUN_00530e30 writes exactly three
  globals (`ds:0x920740 = 0xf`, plus the staging payload pair `ds:0x99aa1c` / `ds:0x99aa20` = record fields
  +0x0/+0x4) and makes 10 calls, including `0x626634` (the write-bytes emitter) at 0x530fc0. FUN_00535940 writes
  47 globals — 13 to -1 (`edi`) and 12 to 0 (`ebx`) — i.e. it RESETS the aggregate scratch set (0x9204c0/0x9206f4/
  0x9206e8/0x9206e4/0x920774/0x9204d8/0x9204cc/0x920750 to -1; 0x9204b8/0x920710/0x920770/0x9204e0/0x920490/
  0x9206ec to 0) and calls 0x5a6cd0 x2.
- **M186 — `[fac*4+0x94d448]` is ASSIGNED, never bit-set.** 27 store sites in 8 functions (FUN_005551e0 x15,
  FUN_00552970 x5, FUN_0052a720 x2 + 5 singles), every one a plain `mov [reg+0x94d448],reg`, and ZERO
  `or`/`and`/`add`/`sub` sites at that displacement. Its 653 refs are byte tests with masks 0x1 (150), 0x10 (62),
  0x20 (34), 0x7 (18), 0x2 (16), 0x8 (10), 0x3 (8) plus whole-dword loads; the 0x40030 mask that FUN_00535c60
  tests appears at exactly TWO sites (0x535ccb and 0x4f2bba in FUN_004f26e0). A claim that a visit is gated on
  bits 0x10/0x20/0x40000 therefore needs the ASSIGNED values, not the test.
- **M187 — the record's +0x20 dword (`ds:0x99aa3c`) is a 3-valued SELECTOR.** 5 stores: three (FUN_00626b46 /
  FUN_00626dfc / FUN_00626f19) copy `[[ds:0x99aa40]+0x3100]` into it, two come from FUN_0048ee00 / FUN_0048ef80.
  14 reads, three of them `cmp`: FUN_004d9ae0 branches on ==1 (0x4d9da0 — writes a unit record at
  0x933289/0x93328c/0x933294, clears bits in [rec+0x93327c], calls 0x4d97c0) and on ==2 (0x4d9dff, only while
  `ds:0x985af0 > 0`); FUN_00616b89 tests ==0. ASSEMBLEGROUP is driven by a 3-way mode stored inside the record it
  emits.
