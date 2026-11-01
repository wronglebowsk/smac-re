# Session notes archive — sessions 171-171

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 171 (cont. 21) — M133-M142, ten censuses, all PASS (`scripts/m133_m142_census.py`)

SUMMARY M133=PASS ... M142=PASS (evidence/m133_m142.log). Highlights with numbers:

- **M133** FUN_00542ea0 (1456 B, 341 insns, 28 callees) is the chooser's dispatch key; its ONLY call site is 0x54eaeb.
- **M137** its index arithmetic at 0x542ed9-0x542eed folds to **359 dwords = 1436 BYTES**: `lea [esi+esi*4]` (5v) ->
  `lea [eax+eax*8]` (45v) -> `shl 3` (360v) -> `sub esi` (359v) -> `shl 2` (1436) -> `mov ecx,[eax+0x927590]`.
  **1436 is exactly M104's record-block stride** (0x927a9c+fac*1436) — same per-faction record family, base 0x50c lower.
  The decompiler's `param_1*0x167` is an ELEMENT index, not a byte stride.
- **M134** ds:0x920700 = UI state code: 31 refs / 8 writes, tested vs 6, 8, 0xd, set to 0xc by chooser case 7.
- **M135** ds:0x94d7fc (per-faction) = counter with **-1 = unset** (8 writes incl. 0xffffffff); its `jl` at 0x5aafd8 is
  the OTHER half of the band-flag skip that M124 named.
- **M136** ds:0x927a78: exactly 2 refs, both inside FUN_0059ec90 -> an input of the advance-budget routine (bounded).
- **M138** 0x94d650 / 0x94d654 = accumulator + per-step companion (261/34 vs 13/2 refs/writes).
- **M139** ds:0x91c630 = upkeep-synch counter (27 of 34 refs in FUN_00521070; incremented at 0x5213c6 after the second
  "Skipping upkeep synch").
- **M140** ds:0x985afc = read-dominant (336 refs / 5 writes) -> run state, NOT a counter; meaning unnamed.
- **M141** FUN_00495480 (21 insns) = cached-flag getter with a null guard -> the `and eax,0x20` at 0x49772a tests a
  cached field's bit; 0 means "no cache object", not "flag clear".
- **M142** FUN_004026b0 (201 B, `ret 4`) = the LIST SEEK: rejects index >= [obj+0x10], walks nodes via [node+0xc] /
  [node+0x10], stores the cursor at **[obj+0x14]** — the mechanism behind M128's pre/post-seek pair.
Law added: a decompiler's `arr[i*N]` is an ELEMENT index; multiply by the element width before calling it a stride.

## Session 171 (cont. 22) — M143-M162: the faction-block field atlas (20 rows, one reproducible rule)

`python3 scripts/m143_m162_atlas.py` -> `docs/field-atlas-faction.md` (3,687 B) + `evidence/m143_m162_atlas.log`,
SUMMARY PASS. Selection rule is mechanical, not cherry-picked: count every `+0x94dXXX` displacement in the objdump
(**150 distinct**), take the 20 with the most references, and record per row: refs, writes, shape, constants written,
values tested, top containing functions, and whether the address text appears in NAMED/archives.

Top of the atlas: **0x94d448 653 refs / 27 writes / 139 functions** (the faction flag word M129's bit 0x8000000 lives in),
0x94d650 261/34 (the M138 accumulator), **0x94d434 196 refs but only ONE write** (a nearly-const field — 196 readers of a
value the game sets once), 0x94d430 168/18 (the band-flag word), 0x94dc84 89, 0x94d80c 78, 0x94d468 75, 0x94d438 72,
0x94d78c 72 (M123), 0x94d81c 62, 0x94d554 57, 0x94d734 57, 0x94d758 51 (12 writes, one const 5), 0x94d488 49/22,
0x94d7fc 47 (M135), 0x94d818 46, 0x94d754 44, 0x94d814 42, 0x94d4e8 40, 0x94d4a8 38/26.
Honesty note baked into the artefact: these are SHAPE entries, not meanings — the table's own legend says a `—` in
`in NAMED?` means genuinely unnamed, not a gap to fill by guessing. Six of the 20 (0x94d434, 0x94d80c, 0x94d468,
0x94d81c, 0x94d554, 0x94d734, 0x94d754, 0x94d814, 0x94d4e8, 0x94d4a8) are new to the registry as addresses.

## Session 171 (cont. 23) — archive pass + M163-M165 (all PASS): the once-written rank and two contiguous structs

Footing hygiene first: the s171 pick lines moved verbatim to `docs/pick-archive.md`, so `NEXT_PROMPT.md` is an index
again (was 15,041/15,500 = 459 B free; now 13321 B). Then three structural answers from the atlas's oddest rows
(`scripts/m163_m165_structs.py`, SUMMARY M163=PASS M164=PASS M165=PASS):

- **M163 — 0x94d434 is a per-faction RANK, written exactly once.** The single writer at 0x59ac8a sits in an
  initialisation loop (0x59ac4b-0x59ac94) inside FUN_0059aa00: it scans the 7-dword table 0x926a7c-0x926a98 for the
  largest entry, stores **-1** in the winner's slot (0x926a78+n*4), then writes `[faction*8380+0x94d434] = ebx` and
  **decrements ebx** while looping. 196 readers, 1 writer, tests against 2/4/5/6 — that is a rank, not a counter.
- **M164 — 0x94d80c/10/14/18/1c is ONE 20-byte struct.** **11** (function, base-register) pairs address all five
  displacements off a SINGLE base (FUN_0040b960, 004dc100, 004e78e0, 004f6030, 00522b70, 0055a940, 00574370 x2,
  0059ec90 x2), and every member has >30 refs. Five separate fields would have to explain why 11 call sites address
  them off one register in sequence.
- **M165 — 0x94d554+0x94d55c is an 8-byte pair** (5 (fn,base) pairs, most in FUN_00546800 with three different bases),
  while **0x94d488 is separate** (17 base-pairs, shares a base with 0x94d55c in only one function) — so the atlas's
  neighbouring ref counts are not a layout.
