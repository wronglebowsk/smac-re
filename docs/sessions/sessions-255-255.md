# Session notes archive — sessions 255-255

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 255 (2026-11-15, STATIC, zero box) - M300: the 24 callers of FUN_005832b0 censused; only 0x51dffd gates the [+4] write
- THE PICK from the M299 lead list. `python3 scripts/m300_callers.py` -> **PASS M300:
  12/12** (every quoted number computed+asserted there; `evidence/m300_callers.txt`).
- S1: 24 call sites in scratch/m574/text.txt == Ghidra index.csv n_callers (two
  instruments); 0x5832b0 NEVER appears outside a call rel32 -> no indirect/vtable use.
  24 sites span 13 caller functions (biggest FUN_0055f650: 7 sites, and the OPEN
  0x56c6de continue-leg lead lives INSIDE it).
- Gates supplied: 21/24 truth-branch (test eax,eax + je/jne; 0x50e216 also pushes the
  raw value as an arg - leg-ambiguous); 2 store the raw value to a frame slot (0x4cf907
  ->[ebp-0x1c], 0x5858fa ->[ebp-0x7c]); 1 converts sign to a 0x200 mask bit (0x568567
  mov ebx,eax; neg; sbb; and 0x200).
- Counter-writer uniqueness: whole-dump mentions of 0x989cec live ONLY in FUN_0051dcb0
  (5 lines; lone STORE = M299's 0x51e01b); the only other slot-base materialization is
  0x51dd05 `mov eax,0x989ce8` - same function. No caller function outside FUN_0051dcb0
  writes [+4] unless a pointer were passed in. DECLARED: pointer-passthrough +
  non-literal addressing out of static scope (the live "any other writer" watchpoint
  check remains OPEN).
- Reach to FUN_0051dcb0 (reverse BFS over DIRECT call edges; 11 direct sites in the
  writer): exactly 1 site (0x51dffd) feeds the counter gate; 1 (0x59ddf4, FUN_0059ce10
  M94 walker) reaches it DIRECTLY;  15 sites / 7 fns reach transitively (depth 2-8:
  FUN_0055f650x7@d3, FUN_00585720x3@d2, FUN_0050d140x2@d4, FUN_004c40e0, FUN_004cf4c0,
  FUN_0051c750, FUN_0059e2c0); 6 sites CANNOT-REACH: FUN_0046a610, FUN_004e63b0 (M53q
  scan-pool rebuild), FUN_0058b1b0x3, FUN_005aff90 (B18 value body - sibling consumer
  of the same (x,y) fold, NOT nested in the counter path).
- NEW STATIC LAW: a straight-line post-call classifier must DIE at the next `call`
  (caller-saved eax) and treat conditional branches as both-legs; the raw S3w windows
  are the witness, class strings only labels. (rk-vs-t regex-anchor bug caught 3
  phantom value-arith classes before submit - windows audit clean after.)
- Box: ZERO (s244 state untouched). NEXT_PROMPT rewritten for s256.
