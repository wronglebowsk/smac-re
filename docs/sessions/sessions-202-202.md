# Session notes archive — sessions 202-202

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 202 (2026-11-02, M256/M257/M258 ANALYSE — the worth test's operands, and the per-region array family)

Static fire: `ps` showed no terran.exe, so M255's box falsifier (does `FUN_0057ecf0` run on a LOAD) was
not taken. Acceptance: `python3 scripts/m256_worth_operands.py` -> `SUMMARY PASS: 8/8 gates on terran.exe
(static image, no box)`, rc=0, 8.2 s, ONE invocation -> evidence/m256_worth_operands.txt (8,441 B, 144
lines). Two earlier invocations failed on the INSTRUMENT, not the claim: objdump pads the opcode column
to 21 chars and prints at most SEVEN bytes, so a `{1,6}` byte-field quantifier eats the padding, the
optional mnemonic group matches empty and 7 of 13 pinned pcs read as "missing" (the skill's "six opcode
bytes" is a print cap, not a constant — live skill fixed); and 0x950564 is past the file image
(terran.exe = 3,067,904 B, so the image ends at VA 0x6ed000) — a .bss table's row count is not statically
readable.

**M256 — the worth test behind the 7/8 verdict byte.** `cmp edx,ecx` at 0x5584b4, `jle 0x5584e3` ->
boolean 0; the fall-through leg2 is `cmp eax,ecx` at 0x5584d8 (`jge` -> 0, else `mov ecx,0x1`); the legs
are ANDed and OR'd at 0x5584eb with the 4-bit reason word [ebp-0x54], and `test eax,eax` at
0x5584fe/0x558509 is the ZF that `sete dl` (0x55850e) consumes -> `add edx,0x7` -> the M253 store
0x558516. LHS = 2 * ((DWORD[block+0x94d810] - DWORD[block+0x94d818] + [ebp-0x60]) * [ebp-0x3c])
(0x55848f/0x558495/0x55849b/0x55849e/0x5584a2/0x5584a8); [ebp-0x3c] = BYTE[block+region+0x94e5a8], the
M94 multiplier (0x558053 -> 0x55805d); [ebp-0x60] has 4 stores in FUN_00556690 (0x558010 reset,
0x5580b9 fold accumulate, 0x558424, 0x558905) and the live one is 0x558424 = 3 + (ds:0x985afc > 75) +
FUN_00531090(ds:0x985b30, 0), adjusted by ([block+0x94e488] > 4 ? -((ds:0x985ae8>>7)&2) : 0) and by
(BYTE[block+region+0x94eca8] < 4), plus the fold's nonzero count [ebp-0x68]. Reason-word bits: bit3 =
bit3 of WORD[0x94e7a8+row], bit2 = multiplier >= 0x14, bit1 = WORD[0x94eaa8+row] - WORD[0x94eba8+row]
< 4, bit0 = multiplier nonzero with the 0x94eca8 byte < 2 (assembled 0x55842d-0x55848c).

**M257 — the RHS operand.** WORD[0x94eaa8 + 2*region] (0x5584aa, region = [ebp-0x10]) plus
WORD[0x94eaa8 + esi] (0x558452), summed at 0x5584b2; esi = [ebp-0x18] = 2*region + 188*arg1 (fold
0x558002-0x558026, published 0x558038; arg1 = the pushed faction, callers 0x52094f and 0x59dd43). Region
loop: [ebp-0x10] init 1 (0x557f9e), `inc ecx; cmp ecx,0x80; jl 0x557fb8` (0x558b1b-0x558b25) = 128
regions. 0x94eaa8 refs image-wide = 4 (inc 0x51df61 FUN_0051dcb0; -10 0x564ab1 FUN_0055f650; the two
reads here). OPEN: 188-byte rows vs 2 bytes/region — regions 94..127 pass the next row (max offset
188*7 + 254 = 1570); one live read of both indexings settles it.

**M258 — the family.** 0x94e4a8, 0x94e5a8, 0x94e628, 0x94e6a8, 0x94e7a8, 0x94e8a8, 0x94e9a8, 0x94eaa8,
0x94eba8, 0x94eca8, 0x94ed28, 0x94eda8 (end 0x94ee28): 12 per-region arrays, every gap 0x80 (byte per
region — B=97, 10, 6, 2, 79) or 0x100 (word per region — W=23, 22, 13 with 28 refs to the +1 high byte,
2, 2, 4, 5), ZERO DWORD accesses anywhere, 128 entries each. RETRACTS the s201 NAMED row calling
0x94e7a8 "flag bytes": it is a per-region WORD array. The 8-slot fold (0x558075-0x5583ac) walks
WORD[0x950764+2*region] and BYTE[0x950664+region] stepped by 0x20bc, doubling per set bit of
BYTE[block+0x94d44c]; its second row is 0x200 below (0x950564, itself a table base at 0x4f7a0a); both
are .bss, so their extents are OPEN.
