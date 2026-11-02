# Session notes archive — sessions 189-189

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 189 (2026-11-01, M235-M237 all PASS, static + read-only /proc; box untouched, M181 still a LEAD)

- **Acceptance:** `sudo -n python3 scripts/m235_m237_records.py > evidence/m235_m237_records.txt` ->
  `SUMMARY M235/M236/M237: 12/12 gates PASS`, rc 0, 7,433 B. Invocations #1 no output (no entrypoint),
  #2 crash (a `%`-format whose argument tuple was unparenthesised), #3 5/13, #5 8/12, #6 11/12, #7
  green. Every failure was an instrument-definition bug (objdump line shape, an absolute-operand blind
  spot, pairwise-instead-of-adjacent gaps, a cluster cursor off-by-one, a whole-window census reported
  as a three-field claim); NO threshold, floor or claim direction was weakened. Two PASS lines were
  RE-WORDED before merge (0x6a75a8 is an indexed table base, not a member disp; the ds:0x9965b8 loaders
  are candidates, not the proven filler). Laws -> skill §16.
- **M235** 0x679f98 = 88 slots (last +0x15c = FUN_0062d78d, next dword 0xfffffffc); 2 installs, both
  `[reg+0]`, by the class's TWO constructors FUN_0062d630 (the 18-dword copy-in, M231) + FUN_0062d764
  (41 B); 0 string literals in the slot functions, so the class is named structurally (72 slots
  implementation-identical to 0x6717cc, 71 to 0x671d94, 70 in all three, 15 unique); 87/88 slots have
  member-scale dispatchers (1920 sites), +0x0 none, +0x15c 28.
- **M236** the +8=9 the grid records / 0x7543d8 entries / 11 trampoline buffers carry has ONE emitter in
  790,695 insns: `mov byte ptr [ecx+0x8],0x9` @0x5dbbd1 in FUN_005dbb5f (33 insns, 0 calls) — a STAMPER
  that zeroes +4..+0x28 and publishes the record pointer into ds:0x9965b8 (3 stores / 3 loads with
  FUN_005dbbe6 + FUN_005dbdc0, M234). +4 is allocated elsewhere: 55 sites store a call result at [reg+4]
  within 8 insns of that call, 25 callees, top FUN_005be090 (13 sites / 13 functions). Live (pid 319926,
  TracerPid 0): the 9 grid +4 pointers form 2 block-strided clusters (6 x step 0x70, 3 x step 0x568),
  all mapped; table entries' +0 step -0x40 (count dword 11).
- **M237** fields 0x2210/0x2224/0x2234: 3 stores, 0 loads / call-through / lea / add, while their own
  block [0x21c0,0x2260) is busy (118 sites, 80 loads, +0x21d0 x62). All 3 installs in ONE installer
  FUN_005f3f5b (6102 B), same pointer thrice. Block-copy falsifier CLOSED: 108 `rep movs` image-wide, 4
  in 2 window-touching functions (FUN_005ee350, FUN_005eede6) naming only +0x21c0..+0x21d0. The handle
  FUN_005f5a11 gates on, ds:0x9977f0: 2 stores (both ABSOLUTE, both in FUN_005f1394), 7 loads, live 0x0
  — no modal object, so the triple cannot be read back without a dialog open.
- **LEAD (command, not a gate):** `awk -F'\t' 'index($0,"call   0x41a8f0")' scratch/m574/text.txt` -> 4
  callers of the GOVOPTIONS pack block: FUN_0041e160, FUN_0049af50, FUN_004a99e0, FUN_00512020 (the last
  also calls the tagged writer 0x6267a5 at 0x512069) — the trigger list for M181's falsifier.
- **Box time still owed:** terran.exe 319926 alive, TracerPid 0; 0 driver calls this fire.
