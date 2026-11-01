# Session notes archive — sessions 173-174

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 173 (cont. 27) — M175-M177 (all PASS): the aggregator's 17 demand sites, its calling convention, and the stamp callers prime

`python3 scripts/m175_m177_aggcallers.py` — SUMMARY M175=PASS M176=PASS M177=PASS (evidence/m175_m177.log, full census in evidence/m175_m177_full.txt).

- **M175 — 17 sites, 13 owners.** FUN_00546800 (AI hub) x2 (0x5469be, 0x54ebb1), FUN_005551e0 x2, FUN_004a5eb0 x2,
  FUN_00534fa0 x2, + singles in FUN_004282d0, FUN_0043ff20 (a 244-insn wrapper whose arg1 is `ds:0x91b5b4`, the
  current-faction global), FUN_00533e70, FUN_00534180, FUN_005344c0, FUN_00535700, FUN_00535c60 (re-arms the SEH/context
  globals first), FUN_0055f650, FUN_0058fa40 (the SAVE path — the site sits ~40 insns from a 0x626634 staging call).
- **M176 — the convention is (faction BLOCK base, record base, mode).** Prologue `mov esi,[ebp+8]`; arg1 is dereferenced
  as a 0x20bc-stride block base through 6 registers, and 10 of 13 callers compute it with the SAME folded *8380 chain
  (shl 6, lea [i+i*2], shl 4, sub i) M169's loop uses. Arg3 (pushed LAST, read at [ebp+0x10]) is reloaded at 5 sites;
  the decisive one is 0x532194 AFTER the per-faction loop: `test eax,eax; je 0x5321a9` skips, else
  `mov edx,[ebp-0x10]; mov eax,[edx+0x94d4a8]; mov ds:0x9204b0,eax` — mode != 0 EXPORTS the stamped value. 12 of 17
  sites push 0x0, one pushes 0x1 (0x5469be in the AI hub).
- **M177 — callers prime a last-run stamp before asking.** 3 sites store `ds:0x985afc` into `[block+0x94d4a8]` within
  15 insns of the call (0x533eec, 0x53420e, 0x534522); a 4th (0x569401, FUN_0055f650) CONSUMES it instead:
  `sub edx,[eax*4+0x94d4a8]; cmp edx,0x10; jl 0x5696fd` SKIPS the call when the stamp is fresher than 16. The field has
  38 refs = 26 stores + 5 loads + 1 lea + 6 `sub` age tests (FUN_005551e0 x3, FUN_0055f650 x3); the aggregator reads it
  only under mode != 0 (0x53219e). So 0x94d4a8 is a per-faction last-run stamp compared against the round counter
  ds:0x985afc (336 refs, read-dominant).

## Session 174 (2026-10-31) — M178-M180, all PASS (static; the box stayed down)

Instrument: `python3 scripts/m178_m180_scratchband.py` -> `evidence/m178_m180_scratchband.txt` (leg parser over
the static .text dump + index.csv containment + terran.exe's own section table for the name strings).
- **M178 — FUN_0041a8f0's 0x41a9xx block is a 19-bit LOSSY FILTER, and its output lands in a faction block.**
  20 stores to ds:0x99aa38 (the image-wide zero-init 0x41a9b7 + one after each of 19 legs); the pack legs feed
  scratch bits 0..18 from source bits [0,5,6,7,9,10,11,12,13,15,16,17,18,19,20,21,22,23,31] of
  [ds:0x8f0d60+0x38]; the unpack legs restore EXACTLY the inverse permutation (19/19 agree, 19/19 destinations
  are that same field) after `mov ecx,[eax+0x38]; and ecx,0xf000000; mov [eax+0x38],ecx` (0x41abdc) keeps only
  bits 24-27 — so 9 source bits (1,2,3,4,8,14,28,29,30) are cleared and never restored. The rebuilt dword is
  published at 0x41ad94 `mov DWORD PTR [edx*4+0x94d600],ecx`, edx = fac*2095 dwords folded from the byte [ctx+4].
- **M179 — ds:0x99aa38 is the save band's STAGING slot, not a record's flag.** 33 stores in 14 functions (my
  first hand census said 28/10: objdump prints `DWORD PTR`/`DS:` in caps, so a `[0-9a-f]+` class stops at the
  `x` of `0x…` and a case-sensitive `^mov dword ptr` misses stores). 9 of the 13 stores outside FUN_0041a8f0 sit
  directly before `call 0x6267a5`, whose args are (name, size, extra) and whose SIZE IS NOT UNIFORM — 7 pass
  0x41, the TECHRANDOM pair passes 0x1 (0x510289 / 0x5170ae) — and those name pointers read out of
  terran.exe as ASSEMBLEGROUP 0x68c774, AIEDITOR 0x68c80c, AIEDITOR2 0x68c818, RULES 0x68c824 AND 0x691e30,
  SCENRULES 0x68c82c, SCENVICTORY 0x68c838, TECHRANDOM 0x68db28 (x3), GOVOPTIONS 0x6899ec, and EDITVEH 0x68c87c (a SECOND record write in FUN_004dde00,
  not the call after its store) —
  the exe's record-type NAME table (none of them appears as ASCII in the save file, which stores numeric tags).
  Neighbours ds:0x99aa1c / ds:0x99aa20 carry 637 stores each (the 0x626634 write-bytes args), so this is one field of that
  staging record. FUN_00518c50 is a set/clear-scratch-BIT helper (`shl 1,cl; or ds:0x99aa38,eax` /
  `not edx; and eax,edx; mov ds:0x99aa38,eax`) indexed by arg1. All 6 writers with >= 12 legs read the scratch in
  ascending order; FUN_004dc5f0 and FUN_0057c550 share their 18-leg unpack sequence LEG FOR LEG (18/18 identical
  destination operand+bit pairs) while packing from ds:0x985ac4's low band + ds:0x985ae8 bits 23/24;
  FUN_004dc8d0 / FUN_004dcc10 feed the same positions from the HIGH band of ds:0x985ac4 plus ds:0x985ae8 /
  ds:0x985dc8; FUN_004dc100 feeds them from the M164 struct [esi+0x94d80c..0x94d81c] (esi = fac*8380 folded at
  0x4dc1a9-0x4dc1b6), serializing 0x94d80c as a SIGN PAIR (scratch4 = `jle`>0, scratch5 = `jge`<0).
- **M180 — consumers of the aggregator's two globals.** ds:0x920720: 13 refs, ONE writer function (FUN_00531df0
  zeroes at 0x53207e, incs at 0x53210c under `test [ecx],0x2000000; jne` — counts records whose flag bit 25 is
  CLEAR); 11 reads in 4 consumers (FUN_0053a9c0 x4 incl. the entry read paired with ds:0x9204ac; FUN_0053bb90
  equality under the rank<5 test; FUN_0053cb20 zero test under `cmp ds:0x985afc,0x32` = round >= 50; FUN_00546800
  x5 = 2 zero tests falling back to ds:0x9204c8, a loop bound, and TWO `cmp ,0x2; jl` gates at 0x548b1e/0x548f6b).
  ds:0x9204b0: 5 refs, 2 writers (0x5321a4 exports [block+0x94d4a8]; 0x54d121 re-primes it with ds:0x985afc) and
  3 readers — 0x5406b4 computes the AGE as round - stamp, 0x546d44 tests `jl`, 0x54bf5f tests `jle`.
