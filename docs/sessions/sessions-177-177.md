# Session notes archive — sessions 177-177

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 177 (2026-10-31) — M194-M196, all PASS (three static milestones, one instrument + one tracerless live read)

Acceptance: `sudo -n python3 scripts/m194_m196_channels.py > evidence/m194_m196_channels.txt` (12,080 B, rc 0)
-> `SUMMARY M194a=PASS M194b=PASS M194c=PASS M195a=PASS M195b=PASS M195c=PASS M196a=PASS M196b=PASS M196c=PASS`.
`sudo -n python3 scripts/smac_preflight.py` PASSed first (terran.exe 319926, 1 base ours, 6 units held 0 actionable).
Two earlier invocations died on my instrument, not the game: I predicted 15 callee targets and the census found 16
(2 reached through `call dword ptr ds:0x671324` / `ds:0x67134c`); and my "address-sized operand" filter was
SIZE-based, so it flagged 0x800000/0x1000000/0x2000000 - each a single bit - while the discriminator is mnemonic +
popcount (0 `cmp` among 297 tests, widest operand 5 bits). A print-only bug (a 7-hex-digit global regex matches none
of the 6-digit 0x9xxxxx globals, so FUN_00544530's store set printed `{}`) was fixed and the gate STRENGTHENED to
require g544["0x920700"]==7 before the accepted run. No floor was lowered.

- **M194** window 0x99a01c..0x99aa1b = 113 sites / 31 fns: 93 PUSH an address (base 50, slot1 15, slot2 8, slot3 6,
  slot5 6, slot4 5, slot6 2, 0x99a01d 1) vs 20 direct memory ops (5 store, 5 movsx, 7 add, 2 load, 1 cmp). 16 callees
  receive the pointer: 6 are the C string layer (0x64b9d0 thunk x32, 0x64c460 thunk x26, _strlen, _strcmp, _strncpy,
  the 0x7efefeff append-copy 0x64b9e0), 2 indirect; FUN_00631afb (1076 insns, 7 sites) and FUN_00632cad (288, 4) take
  slot addresses at 5 and 2 of their sites. Register indexers: FUN_00625b20 4 `shl reg,8` -> `add reg,0x99a01c` pairs
  (77 sites / 23 fns), FUN_005f0583 1 pair (99 / 66). FUN_006265a2 is 0x626634's SIBLING publish (86 sites / 39 fns):
  shares the guard `cmp [ebp+8],9`, `mov [edx*4+0x999ff4],eax`, `shl edx,8`, `mov byte [edx+0x99a01c],0`. Slot 7: 7
  publishers (0x4d10dd 0x5022a6 0x509163 0x530fc0 0x53438d 0x552eb9 0x594e65), ZERO pushes of 0x99a71c (slots 8/9 also
  0). Live pid 319926: slots 0-4 = 'disciplined'/'Provost'/'Zakharov'/'University'/'Mission Year 2150', 5-9 empty;
  A[10]={1,0x9}, B[10]=0x10, staging 0/0.
- **M195** 0x920700: 31 mentions = 8 stores / 17 loads / 6 tests / 0 RMW. Writers FUN_00544530 x7 (ebx/eax) +
  FUN_00546800 x1 (`mov ds:0x920700,0xc` at 0x54ec5c). Tested set {1,2,4,5,6,7,8,9,a,b,c,d} (12 distinct, max 0xd,
  includes the 0x2 that gates 0x545cfa); live 0x0. ZERO string literals in FUN_00544530 / 00546800 / 00540390 /
  00545c50 -> the mode is UNNAMED. FUN_00544530 (1531 insns, 2 tests of [ebp+8]) also stores 0x997120 x28,
  0x99aa1c x14, 0x99aa20 x14, 0x920748/0x92077c/0x920728 x3, 0x9206fc x2, 0x991e24 x2 - it seeds the staging pair.
- **M196** 0x94d448: 653 mentions = 466 scaled `[reg*4+disp]` + 185 `[reg+disp]` + 2 other. 365 scaled sites take
  their index from `add reg,C` after a >=3-op 2095-fold of the SAME register, so the address is
  0x94d448 + 8380*S + 4*C - a block field at +0x344 (+4*C), not an array element. 297 scaled tests, ALL `test`
  (0 cmp), 29 operands, widest 5 bits, none an address candidate; 139 loads, 0 dereferenced (125 arithmetic/compare,
  14 pushed). RMW quad verbatim at 0x5553e1/e7/ed/f3 (`mov edx,[edi+0x94d448] / and edx,0xfffdfbff / or edx,0x840 /
  mov [edi+0x94d448],edx`). RETRACTS M190's "the carriers 0x55540a/0x55580f store ADDRESSES": they follow
  `or eax,0x20000` / `and ah,0xdf` on the flag word, and the lea at 0x5553d2 is the store-through alias of the store
  at 0x5553df. Live: 0 of 33 dwords at +4*i and 0 of 33 fields at +8380*fac lie in 0x400000-0x7fffffe (0,
  0x80008118 x6, 0xffffffff x8, small ints).
Pitfalls: a scaled-4 displacement census is NOT an array census - attribute the index register's def chain;
classify a bit-field test by MNEMONIC + popcount, never by operand magnitude; data globals are 6 hex digits.
