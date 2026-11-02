# Session notes archive — sessions 182-182

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 182 (2026-11-02) — M209-M212 all PASS: who dispatches dialog slot +0xa8; the dialog stack = two parallel arrays (arg3 write-only); +0xe4 is a bool; FUN_00542ea0 wraps the pump; -9999 is FUN_00496ad0's sentinel

Instrument `scripts/m209_m212_dispatch.py`: whole-image disasm + image bytes + a vtable model (bases = the imm32
of `mov dword ptr [reg+disp],imm`, extent = code-pointer dwords capped at the next base -> 188 bases). Acceptance
`python3 scripts/m209_m212_dispatch.py` -> `SUMMARY M209=PASS M210=PASS M211=PASS M212=PASS (18/18 gates)`, rc 0,
FIRST acceptance invocation; 3 `--probe` runs fixed 6 expectation errors (457/7 install split, 3 not 4
`[this+0x3c]` sites, INSTALLS displacement carries no `]`, read the guard off the call site's next 3 insns,
`cmp eax,esi` is a REG compare, arg_of must start one insn before the call); no threshold weakened.
`evidence/m209_m212_dispatch.txt` (5,859 B). Zero box time. Semantics: NAMED.md `## M209-M212`.

- **M209** +0xa8 = 33 implementations over 188 vtables; exactly 3 map it to FUN_005f5759 (0x67164c 390 / 0x6717cc
70 / 0x6728c0 4 installs, 70 ctor fns, 457 at `[ebp-disp]` — dialogs are stack locals). Dispatchers: FUN_005f6aa3
(the family's own +0x4c, 5 vtables, 0 direct calls) via FUN_005e7917 (24-B list walk from `[obj+8]-1`, publishes
item[+0x14]/item[+0x10], -1 on failure) and FUN_0043fee0 (+0xa8 of 0x6738e4, 0 direct calls) via ds:0x9977f0 (9
refs, 2 stores, both inside the pump at 0x5f3d70/0x5f3e02). RETRACTED: FUN_0043a4e0 (+0x60 of 0x673498 ->
FUN_004394e0) and the -0xa14 thunks (0x6723f4/0x672bfc/0x673444 installed at `[reg+0xa14]`) — 0 of 13 outer
targets is FUN_005f5759. FUN_004bb900 = +0xa8 of 8 vtables, forwards to [this+0x3c], 0x14 if null. Args: 19
immediates (5x -1, 1x -2) + 10 registers.
- **M210** dialogs[] 0x992db8 6 refs (4 stores / 2 loads, 3 fns); arg3[] 0x992dc8 3 stores, 0 LOADS = write-only;
current 0x9939c4 22/3, depth 0x9939c8 21/3, writers only FUN_005ce5bd + FUN_005ce6ff. +0xe4: 2 dispatch sites;
dialog family = FUN_005f6056 `return ds:0x997770 == 0`, sibling = FUN_004060d0 `return 1`; ds:0x997770 3 refs = 2
stores (0x5f3e6e = 0, 0x5f6081 = 1) + 1 read; the runner gates its arg2 callback on it (`test eax,eax; je
0x5ce6f6`). M206's "+0xe4 = events" RETRACTED.
- **M211** FUN_00542ea0 (1456 B, 1 caller = FUN_00546800 at 0x54eaeb) calls FUN_00405ef0 (0x542ecb) and the pump
ONCE (0x54322b), returns its eax; table 0x54ef34 = 8 entries (9th dword 0x90909090), guard `add esp,0x8; cmp
eax,0x7; ja 0x54ec82`; cases 0..7 -> FUN_005306b0 / FUN_00545c50 (1,2) / FUN_00626a17 (key 0x690fc0, stub
0x530d70) / FUN_0053fce0 / FUN_00541bb0 / FUN_00542810 / ds:0x920700=0xc + ds:0x92077c=1 then FUN_00545c50. M207's
"0 pump calls" is direct-only.
- **M212** -9999 (0xffffd8f1) 14 sites / 10 fns (3 cmp, 11 mov): 0x4976ce init + 0x4976f9 read-back inside
FUN_00496ad0, which has 1 caller (FUN_00417ee0 at 0x41860a `call 0x496ad0; mov edi,eax`) and its 2 tests read
edi; 0 pump sites test -9999 and 0 of the 56 +0xa40 stores write it. Pump's 94 consumers: 49 mov / 22 test
eax,eax / 4 cmp-imm (0x8 x2, 0x3, 0x1) / 6 cmp-reg / 5 pop / 3 push / 2 lea / 2 jmp / 1 dec; 1 tests -1 within 12
insns.
OPEN: s174e box state unverified; M181 still a LEAD (no positive control).
