# Session notes archive — sessions 256-257

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 256 (2026-11-15, STATIC, zero box) - M301: the lead "ebx's table 0x51de2c-0x51df1d" is REFUTED - it is a base_array walk, not a table
- THE PICK from the M294 lead list. `python3 scripts/m301_ebxtable.py` -> **PASS M301: 8/8**
  (every quoted number computed+asserted there; `evidence/m301_ebxtable.txt`, 199 ln).
- (a) ENTRIES: ZERO. The range is 0xf3 = 243 B (ends on the last byte of `test ebx,ebx`
  0x51df1d): 60 4-B dword slots + 3 B leftover, and 0 dwords - aligned or at any byte offset -
  resolve to a VA inside .text; the span tiles GAP-FREE as 81 instructions = 68 of ONE loop
  (0x51de27-0x51deef, sole back edge `jl 0x51de27`) + 13 of its straight-line exit block, and
  contains 4 `call 0x64b870`. (`m301_ebxtable.txt:95-104`)
- (b) NATURE: executable CODE - not code addresses, pointers, masks or offsets. 243 B read
  straight out of the PE file image (programs/terran.exe, .text, file off 0x11de2c) are
  BYTE-IDENTICAL to the dump; Ghidra n_insns 386 == the dump's instruction count over the
  function window; 0 indirect jmp/call in all of FUN_0051dcb0; 0 lea/mov/push of any range
  address image-wide; the 4 external edges into the range all target its EXIT BLOCK
  (0x51de05, 0x51de19, 0x51ddc0, 0x51dded -> 0x51defd), none enters the walk. (A3 :115, A7 :191)
- (c) INDEXING: it walks the NAMED base_array 0x95da10 (NAMED.md:74). Base register eax =
  cursor, `mov eax,0x95da12` 0x51de1f = base+2 (row y field), spill/reload [ebp-0x14]; stride
  `add eax,0x130` 0x51dee2 = 304 B = that record size; index = trip counter [ebp-0x18] (0 at
  0x51de10, inc 0x51dee1) bounded by the BSS row count ds:0x985af4 (`test`/`jle` 0x51de17-19
  skip the walk whole, `cmp` 0x51dee7 drives the back edge). The value compared against the
  row's flag byte, ebx = BYTE[304*i + 0x95da14] (0x51ddff) with i = FUN_004e37f0's return
  (call 0x51ddb1): the scale chain 0x51ddf2/0x51ddf7/0x51ddfa evaluates to exactly 304*i. (A4/A5)
- (d) VERDICT: the range is UPSTREAM of 0x51dffd and gates NOTHING the [+4] write depends on.
  Of the 11 branches between the range exit and the call, ZERO land past the call - the
  ebx==0 leg `je 0x51dff5` 0x51dfd1 targets the PRE-CALL block, so the call and `test eax,eax`
  run on every leg, bypassed-walk included. ebx's only post-range consumers are the cell
  stores (0x51dfc9 `test ebx,ebx` / 0x51dfd3-0x51dff3) and the POST-STORE byte read 0x51e02c;
  the counter address is esi, the 28-B fold of [ebp-0xc] (M299), never ebx. FUN_005832b0's eax
  has exactly ONE consumer (`test eax,eax` 0x51e005), is overwritten at 0x51e024, and there are
  0 backward edges from after the call into the range - the predicate's return CANNOT reach it.
- RETRACTION: the "ebx's walked table (0x51de2c-0x51df1d) recorded as a LEAD" phrasing at
  NAMED.md:1009 (M294) is wrong - patched in place, and the resolution registered as ## M301.
- NEW STATIC LAW: before censusing "address X-Y is a table", run 4 falsifiers: (1) does the
  span tile gap-free as instructions from its OWN encoding bytes; (2) does any dword in it
  (aligned and byte-offset) resolve into .text; (3) is any address in it the operand of a
  NON-BRANCH instruction image-wide; (4) does the containing function contain an indirect
  jmp/call at all. 243 B of hand-read disassembly reads like a table until (1) runs.
- OPEN: whose record the exit block's BYTE[edi+0x7] belongs to (edi = [ebp-0x4], sole
  pre-range writer 0x51dd28); the walk's semantic predicate (a tile-class test on the 44-B
  tile view 0x51de5b-0x51de61 + a distance compare vs ds:0x8f0d34 0x51dece-0x51ded0, then 3
  `or ebx,-1` sentinels) - shape VERIFIED, meaning INFERRED.
- Box: ZERO (s244 state untouched). NEXT_PROMPT rewritten for s257.

## Session 257 (2026-11-15, BUILD B19 10/10, zero box) - the slot [+4] visit counter made EXECUTABLE (sim/visitcounter.py); the rung was UNAUTHORED, this fire wrote it (as B14/B16/B17/B18)
- track_mode BUILD next_rung=B19 -> the rung B18 DECLARED ("the slot [+4] visit
  counter, its ++ gated on call 0x5832b0"), now that M299 (the gate body),
  M300 (the 24 callers) and M301 (the ebx deflection) have landed. ACCEPTANCE:
  `python3 -m sim.selftest --b19 programs/saves/m54b_clean.SAV` -> PASS B19
  10/10, output evidence/b19_visitcounter.txt (table first, then gates; two
  runs byte-identical, report sha256 e161b2f9...).
- HOW IT'S ANCHORED (skill law: constants read out of the bytes, instruments
  that fail differently): the model PARSSES the pinned W1 (44 lines
  0x51dfac-0x51e02c) / W2 (114 lines 0x5832b0-0x5833b7) windows out of
  evidence/m299_visitgate.txt ITSELF and decodes every constant from the
  instruction texts (rung masks, the ds:0x985ac4/0x92a380/0x69220c/0x692210
  globals, the lattice coefs -5/-3 as neg/shl/sub and lea[+*2]/sub chains, the
  counter operand [esi+0x989cec] == the MAX operand +4, the 28-B slot stride as
  (8-1)<<2); adjacency is by ORDERED INSTRUCTIONS, not addr+1 arithmetic
  (instruction lengths differ - the addr+k scan initially missed the sub
  ebx,edx leg). Branch A runs as TWO implementations (the decoded chain vs
  M299's closed rungA) that must agree (0/76960 disagreements) AND reproduce
  the RECORDED 36/36 lattice theorem; the recorded census 481/16/12/5/1087 +
  dump digest 093d10a868da55b2 re-grade through the model's OWN rung readers.
- MEASURED (this fire's anchors, RECORDED population cited): over the 2321
  recorded decision rows (B17 loader + B16 transposition + B18 site_of law,
  sites {1:2253, 9:68} == B18's RECORDED anchor - the counter table and the
  MAX table are the SAME 28-B slots, +4 vs +0): 1222 rows CERTAINLY REFUSE
  (rung1 mask hit - no live state can increment), 0 CERTAINLY ACCEPT (the
  class is pass1 & bits26/27 & bit28: EMPTY in the dump AND in the rows), the
  remaining 1099 are UNDECIDED-but-possible and ALL are branch-A domain
  (census {'branchA':1099,'rung1':1222}); under the DECLARED baseline
  Live(flag2000=False, rand=1): 20 accepts (all eax=2 branch-A parity hits),
  1079 undecided (parity misses falling to the never-recorded branch-B stride
  lattice). The eax=1 return is STRUCTURAL ONLY in this window: 0 graded rows
  and (with sel clear, flag-clear leg) 5 dump records reach the rung3 leg -
  no 'only-2-accepts' rival is gradeable on the rows (DECLARED, G9).
  Save-vs-live record views diverge on 4008 counter-table field deltas over
  the same rows (the B16/B18 drift law, counted not smoothed).
- RETRACTED/CORRECTED: none of prior claims - B18's DECLARED list entry for
  the counter is now CLOSED (module executable); its live-VALUES entry stays
  OPEN and SHARPENS: the next read-only /proc pass that dumps ds:0x92a380,
  ds:0x69220c, ds:0x692210, ds:0x985ac4 + the 0x989ce8/0x94eca8 tables grades
  every B19 number ABSOLUTELY (the LEAD already in NEXT_PROMPT).
- PITFALLS: (1) a rung whose rivals need a POPULATION that the recorded window
  leaves EMPTY must say so (G9's eax=1 note) - do not grade a rival on zero
  witnesses; (2) evidence-file-embedded disassembly is a first-class PIN
  SOURCE: parse it, and keep the window edge honest (M301's 6th eax mention
  0x51e033 lies PAST W1's end 0x51e02c - compare inside-the-window lists,
  say so); (3) sim/selftest acceptance paths must not double-print a verdict -
  the module CLI owns its PASS line, the rung's PASS line belongs to
  sim.selftest (it adds G10).
- Box: ZERO. NEXT_PROMPT rewritten for s258.
