# Session notes archive — sessions 176-176

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 176 (2026-10-31) — M191-M193, all PASS (static batch of three, one instrument)

Acceptance, ONE invocation, rc 0: `python3 scripts/m191_m193_channels.py > evidence/m191_m193_channels.txt`
(15,360 B) -> `SUMMARY M191a=PASS M191b=PASS M191c=PASS M192a=PASS M192b=PASS M192c=PASS M193a=PASS
M193b=PASS M193c=PASS`. Three earlier invocations died on MY instrument, not the game: (1) I eyeballed
0x64b9e0's store count as 6 where the census says 7; (2) a 5-tuple printed with a 2-name unpack; (3) the
fold matcher tested "seed S appears in the add/sub/lea steps" over rows[1:7], which includes the ADD-C
step, so all four chains reported matched=False while the printed S/C were right. No floor weakened.

**M191** 0x626634 (callee at 0x530fc0) is NOT an emitter: 44 insns / 7 stores / 11 loads / 1 callee
(0x64b9e0, 84 insns, all 7 stores through [edi], 0x7efefeff zero-byte scan on both args = append-until-
NUL); guards `cmp [ebp+0xc],0 je` + `cmp [ebp+8],9 jle` -> `mov eax,3`, success `xor eax,eax`; negative
arg3/arg4 fall back to ds:0x99aa1c/0x99aa20. Computed geometry 0x999fcc +10*4= 0x999ff4 +10*4= 0x99a01c
+10*256= 0x99aa1c: the staging record IS slot 10 of a 10-slot channel table (2 dword arrays + 256-byte
text) and `<=9` is the slot bound. 1584 sites / 190 fns (0x6267a5: 18/17); immediates only 0..9
(0:548 1:349 2:251 3:135 4:73 5:59 6:39 7:7 8:18 9:17), 88 register slots; writers 2/2/3 from 3 fns,
text slots read in 26 fns. Site 0x530fc0 = (7, &[ebp-0x100] from the 0x5808b0 call at 0x530fab, -1, -1).
**M192** FUN_0052a720's 2 0x94d448 stores are the PUBLISH half of an 18-load/18-store bracket over 9
fields {0x94d448,468,488,4a8,4c8,4e8,558,55c,57c} (the byte field is captured by MOVSX — a mov-only
census reports 16/8 and the bracket looks asymmetric). [ebp-0x50]/[ebp-0x4c]: 1 writer (the field's own
load 0x52aff5/0x52affe) + 1 reader whose next insn is the store; 0 of 23 direct callees stores the
field; both sides build the base as 8380*S + 4*C (`mov r,S; shl 6; add S; lea [S+r*2]; shl 4; sub S;
add C; shl 2`), capture (edi,ebx)/(ebx,edi), publish (edx,esi)/(esi,edx) reloaded from the single-write
spills [ebp-0x2c]/[ebp-0x30], 0 writes to edi/ebx between -> ADDRESS-EXACT. QUALIFIES M190: 0x10 is
PRESERVED here, not produced (remaining carriers 0x55540a/0x55580f store ADDRESSES).
**M193** FUN_0053a9c0 writes 23 stores to 8 globals {0x99aa1c 6, 0x99aa20 6, 0x997120 5, 0x9206e4 2,
0x920774 1, 0x9204b4 1, 0x920718 1, 0x7a75c8 1}; 0x9204ac (2 stores in the image) / 0x920720 (1) are
written ONLY by 0x531df0 and are READ-ONLY here; 0x9206e4/0x920774 are 2 of the 15 that 0x535940 resets
(8 writers / 10 readers each). Its only site 0x545cfa is gated `ds:0x920700 == 2` (8 stores in 0x544530
x7 + 0x546800 x1), the caller tests the return, and its tail zeroes 0x9204b4/0x920718, calls 0x533e70,
returns 1. Box untouched (state carried from s174e); M181 still has no positive control.
