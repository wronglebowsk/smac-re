# Session notes archive — sessions 180-180

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 180 (2026-11-01) — M201-M204 all PASS: FUN_005f1394 IS the OK/CANCEL DIALOG RUNNER; its return is a result code; $-tags resolve by FIRST DIGIT; the key pool is an emitter list

One static instrument: `scripts/m201_m204_dialog.py` -> `evidence/m201_m204_dialog.txt`. Acceptance
`python3 scripts/m201_m204_dialog.py` -> `SUMMARY M201=PASS M202=PASS M203=PASS M204=PASS (15/15 gates)`,
rc 0. Invocation 1 was 12/15 on 3 INSTRUMENT bugs (a slot pattern built with `str(off)` so `+ 0x30` and
`+ 0xdc` matched nothing; a 40-BYTE lookahead for the +0xdc dispatch when the bool prologue is ~45; a
char-literal regex that also caught the `'\0'` escape) — fixed, every threshold kept.
- M201 ctor FUN_00405ef0 stores `mov [eax],0x67164c` 0x405f31 + `mov [ecx+0x444],0x671644` 0x405f3a (the
  CPane subobject, after ctors 0x5ee350 and 0x5f6b8c(this+0x3230)); 99 ctor sites in 90 fns, 53 of the 67
  pump callers construct it. The dword 0x5f1394 appears 0 times as data image-wide (no vtable or switch
  holds it): 94 direct calls, ONE exit `ret 0x8` at 0x5f3f58, 90/94 sites load ECX from the caller's own
  frame. The pump is the only reader of 0x698e40 'OK', 0x698e44 'OK', 0x698e48 'Cancel', 0x698e50 'OK' (1
  site each, pool alternates). +0xdc is dispatched twice, on *this and on *[this+0x285].
- M202 domain {0,-1,[this+0x290],pass-through}: 0 `mov eax,imm` in 11,207 B, 5 `xor eax,eax`, 2
  `or eax,0xffffffff`, `mov eax,ds:0x698d0c` 0x5f3f38 (that dword IS 0xffffffff; 1 reader image-wide), and
  the lone `[reg+0xa40]` read 0x5f3f45 with 0 stores — the pump reports a result, never computes one.
  arg2 IS A CALLBACK: [ebp+0xc] at 2 sites (0x5f3d87, 0x5f3dcb), both feeding a +0xdc dispatch, and
  vtable+0xdc FUN_005ce5bd (`ret 0xc`) does `cmp [ebp+0xc],0` 0x5ce6bd + `call dword ptr [ebp+0xc]`
  0x5ce6c3. 17/94 sites pass a code pointer (16x 0x530d70, 1x 0x530db0): unnamed islands in the
  0x530d45-0x530df0 gap that read ds:0x920434, then ds:0x991588, set ds:0x920790=1 (its only 4 stores),
  call FUN_00519a20, clear it, return 1/0. All 6 composer sites store the return into a selector global
  within 4 insns; 0x920700 = 31 sites in 4 fns, tested {4,6,8,9,d}. **M197's "chooser" is RETRACTED — it
  is a dialog RESULT CODE, not a mode.**
- M203 FUN_0062898e is a first-DIGIT scanner (61 B, 0 callees, only '0'/'9' bounds + the NUL test), 5/5
  sites inside FUN_00625b20. $H: strncmp 4 vs 0x699130 '$HEX' -> `__itoa([0x999fa4][n])`; else digit ->
  slot text 0x99a01c+n*0x100. $L's exception is 0x69913c '$LINK<' (strncmp 6); $N gotos
  switchD_00625bb6_caseD_4e, the same tail as the unnamed default. Only returns: 0xe x6 (behind 8
  `9 < local_1c` guards) and uVar2 = 3 (null args).
- M204 313 key sites / 255 keys / 29 referrers, ALL inside 0x5316b0..0x54f1d0; FUN_00546800 owns 111 sites
  / 97 keys; 313/313 are `push <key VA>`; sinks FUN_00626a17 x149, FUN_0064b9e0 x76, FUN_00405220 x33 =
  258. Only 11 of 29 referrers call the pump and 56 of 67 pump callers name no key; the paths meet only as
  0x530d70 -> FUN_00519a20 -> FUN_00546800.
- Pitfall: Ghidra prints small vtable offsets as `+ 4`/`+ 8` and larger as `+ 0x15c` — a pattern must
  accept BOTH forms or it silently matches nothing. No box time: s174e state still unverified, M181 still
  has no positive control.
