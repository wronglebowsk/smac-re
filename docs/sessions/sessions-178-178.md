# Session notes archive — sessions 178-178

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 178 (2026-11-01) — M197-M200: the proposal composer, the diplomacy key pool, the tag engine, the row writers

Static-only fire, NO box time: one census script, one evidence file.
`python3 scripts/m197_m200_proposal.py > evidence/m197_m200_proposal.txt` (23,988 B, rc 0) ->
`SUMMARY M197=PASS M198=PASS M199=PASS M200=PASS (15/15 gates)` (evidence/m197_m200_proposal.txt:290; every
number below is cited to a line of that file); `--probe` prints the same lines
without verdicts. Two earlier invocations died on MY instrument, not the game: `for s in post` iterated
(pc,text) tuples -> TypeError; and I first gated M198a on an 0xFFFFFFFF terminator at the last KEY's end,
but the pool interleaves 18 spaced message lines, so the walk must accept multi-word entries - the fix
RAISED the floor (>=25 keys -> >=200), it did not lower it.

**M197** FUN_00544530 (1502 insns) has EXACTLY ONE call site: `call 0x544530` at 0x545c99 in FUN_00545c50,
and the operand text "544530" occurs 1x in 790,695 instructions (:2-3). Guarded `[ebp+0x10]==0` /
`jne 0x545cd4`, 2 args (esi=[ebp+8], ebx=[ebp+0xc] - the faction pair), return cleaned `add esp,0x8` +
`test eax,eax` (:5). Of the 8 stores to ds:0x920700, 7 are inside it and its own body says 6 are the
constant 0 while 1 is `FUN_005f1394()`'s return; the only immediate store in the image is 0xc at 0x54ec5c
(:8). It calls FUN_005f1394 6x and assigns the return to 5 distinct globals {0x9206fc,700,728,748,77c},
all cleared in its first 112 bytes (:10). RETRACTS M195's "ZERO string literals": the body names 3 string
globals whose bytes read PROPOSALMENU / REJWARALREADY / NOCOMMLINK (:12). **M198** those 3 sit in a string
pool at 0x690160..0x69107c bounded by 0xFFFFFFFF at BOTH ends: 329 entries = 311 single-word KEYS + 18
spaced message lines, and 257 of the 311 keys have code references, printed as key->function (:13-16, :275).
**M199** the substitution engine is FUN_00625b20: _strstr for the needle whose byte at 0x69911c is '$',
switch on the char after it over 5 cases (closer 0x699138 = '>'; 'H' compares 4 bytes at 0x699130 =
'$HEX'), index `&DAT_0099a01c + n*0x100`, metadata A[]@0x999fcc / B[]@0x999ff4 / 0x999fa4, then copy the
Nth ':'-separated segment of the slot (:277-278). FUN_005808b0 COMPOSES `$<`+{M,F,N}+{1,2}+`:`+arg+`>`
from the record dwords +0x2fc/+0x300 (the bytes at 0x692144..0x692160, :280); FUN_00580a60 PARSES that
head back into 0x99aa1c (F->1, N->2, else 0) and 0x99aa20 (2nd char=='2') - inverse-consistent, so the
staging pair IS a parsed tag head (:282). **M200** FUN_00631afb / FUN_00632cad are row WRITERS through
the handle DAT_0099d020 (vtable +0x10/+0x18/+0x38/+0x58/+0x60; alloc FUN_005be090, free FUN_0064a7f0,
append FUN_0064b9e0, :286): 0 `0x25` immediates, 0 printf-family calls, 0 references to FUN_00625b20, and
each copies the buffer it is handed VERBATIM - RETRACTS M194's "the formatters" (:287); its 16-byte
memcmp keys 0x67bd20/0x67bd30 are GUIDs, not table names (:288). (Pitfalls written to the skill,
`references/static-store-census.md` §12: Ghidra renders a referenced literal as a named `s_NAME_…` symbol, so a `"`
grep finds ZERO strings in a function that references three; a string pool is 4-aligned, NUL-padded and INTERLEAVES
keys with message lines - walk it by "the longest padded entry ENDING at va", never by a fixed stride.)
