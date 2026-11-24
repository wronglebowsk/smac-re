# Session notes archive — sessions 329-330

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-328-329.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 329-chain2 (2026-11-24) — M354: section A's identity = the 0x98ad88 row (M351's OPEN closed; leg NOUNS retracted)

- **ACCEPT** `python3 -u scripts/m354_design_row.py` -> **`PASS M354: 11/11 gates`**,
  table digest `dd5e689e8d9af320`; two runs byte-identical (`evidence/m354_design_row.txt`,
  `evidence/m354_x2.txt:91`). `scripts/m354_mutate.py` -> **23/24 scored, NO-OP ['MU25']**,
  measured coverage ALL 11 gates (`evidence/m354_mutate.txt:30`).
- **REVIEW #379 (11 findings, all fixed)**: function extents now PARSED
  (`.func_starts.json` + the last ret) instead of window widths; G4 proves "no data reads"
  by classifying every PTR operand; G9 pins `test/jge/neg` and LOAD-vs-STORE; G6 pins the
  mask+store; G10 gates 4 atlas semantics; harness records ALL reddened gates and adds
  MU19-MU24 so every gate has a killer; rotation stub header is derived from the archived
  block (the hardcoded "neighbour test" vs "neighbourhood" was a real byte mismatch).
- **THE ROW IS A 0x98ad88 RECORD**, stride 0x34, keyed by the A item: three imul sites
  (0x49571b name, 0x4957e2 +0x29 weight, 0x4959be +0x2a class) all read the item from
  [ebp-0x2c], filled from `[ecx*4+0x9267e4]` @0x4956d6. So a +head is a UNIT-TYPE/design
  ROW, not a facility id — M351's OPEN "does A speak designs" is ANSWERED (V).
- **THE FLAGS FNS DIFFER IN KIND**: 0x496050 (A) reads exactly +0x2a and +0x30 and is
  band-guarded (`cmp [ebp+8],0x40`, bit 4 test); 0x4960f0 (B) reads NO memory at all and
  returns {1,2,3}. Two different row spaces, proved by their field sets, not by names.
- **BUILDER**: 0x596000 writes `owner*0x40 | (k&0x3f)` for k>=0x40 (shl 0x6; cmp 0x40) —
  64 shared rows + 64 owner-band rows; the same value is row-indexed (13*i<<2 = 0x34*i).
- **RETRACTION (narrows M349 + M351):** the decoder's legs are identified by their TABLES,
  not by their labels: head<0 reads the 0x984d38/0x30 cost +0x0c (M337 = `#FACILITIES`);
  head>=0 indexes 0x98ad88/0x34 and stamps +0x30 (0x4efe50/60). So M349's per-leg nouns
  (neg=UNIT, +2=FACILITY) and M351's "unit row" label for section B are INVERTED; the
  sign split and all arithmetic stand. Do not re-derive the nouns from trace names.
- **PITFALL (new)**: gate messages that index a parsed list (`v30[0]`) crash *before* the
  FAIL line prints, so the mutant scores MISSED — a gate that can die silently is a defect;
  format parsed sets, then assert. MU11 also caught an AUTHORED constant (the 0x40 split
  was hardcoded); the split is now parsed from 0x596017.
- **DOC CAP**: NAMED 245,796 B was under the 5 KB trigger -> `## M312` rotated VERBATIM to
  `docs/named-archive-m354-rows.md` (sha1 `5e8df0971a3d9bae`, `scripts/m354_named_rotate.py
  --verify` PASS) before `## M354` landed.
- OPEN: game nouns of +0x25..+0x28; bit2 = prototype build INFERRED.

## Session 329-chain3 (2026-11-24) — M355: `Laptop` = the DEFAULT bit-vectors of `Preferences` / `More Preferences`

- **ACCEPT** `python3 -u scripts/m355_laptop_masks.py` -> **`PASS M355: 7/7`**, digest
  `c742bc131105fb25`, sha1 `d3f17cc9` x2 identical (`evidence/m355_x2.txt:3-4`);
  `m355_mutate.py` -> **24/24 killed**, 2 NO-OP green (`evidence/m355_mutate.txt`).
- **`Laptop`** = 4 read sites (0x58e9f3/0x58eb0c loader; 0x58e688/0x58e708 in getters 0x58e640/
  0x58e6c0, one each), 2 VAs both "Laptop"; `neg`/`sbb` -> 0/-1 = `atoi != 0`; absent == explicit 0
  (lpDefault = the zeroed 0x997120, zeroed before the call).
- **MASKS** (from the encoded `and`/`add` immediates; the register is proven to be the read's atoi
  return, G2e): Preferences 0xbbe1dd96 / 0xa3e1dd16; More Preferences 0x3a7168 / 0x327168.
  Laptop!=0 CLEARS bits {7,27,28} resp. {19} — it removes options, never adds.
- **ROLE**: the mask is the lpDefault of two bit-string reads (0x58eaf7 `Preferences`, 0x58ec0d
  `More Preferences`), emitted as '1'/'0' over bits 31..0 by a downward loop (`shl edx,cl`, `test
  <mask>,edx`, leading zeros >bit 8 dropped); parser 0x628720 (`v=v*2+(c-0x30)`) gives the dword.
- **GATE**: `Difficulty` (ds:0x92bde8) < 2 ORs Preferences bit 5 — LOADER default only, on the jcc
  fall-through; B block and both getters hold 0 refs.
- **CONSUMER**: getters feed one dialog block (0x493b0b..0x493b79, 5+5 sites, 11-field order
  measured both ways) storing +0xa30..+0xa58; APPLY 0x4923d0 ORs +0xa30 into ds:0x92befc @0x492464
  and +0xa34 into ds:0x92bf00 @0x49246f. `Laptop` changes DEFAULTS only.
- **REVIEW (PR #380)**: 10 findings closed by tightening G1a/G1b/G1d/G2e/G3a/G4a/G4b/G5b/G5c and
  the rotate guard; 8 new mutants (MU17-24), no check weakened.
- **PROTOCOL**: NAMED headroom 4,204 B (< 5 KB trigger) -> `m355_named_rotate.py` rotated `## M293`
  VERBATIM (block sha1 `e548f949`) to `docs/named-archive-m355-rows.md`.
- **OPEN**: the option NAME of each set bit; whether another path re-derives 0x92befc/0x92bf00.

## Session 330-chain3 (2026-11-24) - M357: bit -> option LABELS of the two `Laptop` bitmaps

- **ACCEPT** `python3 -u scripts/m357_pref_bits.py` -> **`PASS M357: 18/18`**, digest
  `095258c8b40d0e23`, sha1 `bb36f237` x2 identical (`evidence/m357_x2.txt:1-3`);
  `m357_mutate.py` -> **23/23 killed**, 1 NO-OP (`evidence/m357_mutate.txt`) — every gate
  named in `## M357` is reddened by its own mutant (MU1-MU23).
- **PAIRING**: six builders read a Script.txt section by name (0x5ea431: BASICPREFS
  0x49043b, ADVANCED 0x4906d2, AUTOMATION 0x490a67, AUDIOVISUAL 0x490e70,
  BASEWARNINGS 0x49112a, MAPPREFS 0x4916b8) and per row take the next line
  (0x5ea448) -> strcpy into the page's static slot (0x68b678.., +4/dword) -> add_item
  0x604fd2 (text, id). Rows 8/12/14/8/17/7 = 66; ids are NOT positional
  (BASIC = 5,6,64,7,8,9,10,11).
- **BITS**: rebuild 0x492940 maps all 70 ids to one (field,bit) each (imm + ebx
  decoded); APPLY merges A fields -> 0x92befc, B -> 0x92bf00, a28|a48 -> **0x92bf04**
  (my first hand read put a48 in 0x92befc; sim + M355 refute it, RETRACTED). 1:1 66/66.
- **ANSWER**: befc bit1 Autosave, 2 move-enemy-quickly, 5 Tutorial (M355's
  Difficulty<2 bit), 7 Secret Project movies, 8 map grid, 12 mouse-at-edge,
  14 design units, 15 move-allied-quickly, 16 air units return home, 21/22/23 cancel
  on Treaty/Truce/Vendetta, 24 formers plant forests, 25 condensers, 27 Interludes,
  28 Sound effects, 29 radio-buttons, 31 wake passengers; bf00 bit13 base names,
  17 Background music, 19 Monuments, 20 auto-prune, 21 detailed main menus.
- **LAPTOP DELTA** = A{7,27,28} + B{19} = "Secret Project movies." "Interludes."
  "Sound effects." "Monuments." — every laptop-cleared bit is an A/V row.
- **DIVERGENCE**: #AUDIOVISUALPREFS offers 11 lines, the exe builds 8 ("Sliding
  windows.", "Sliding scrollbars.", "Whole unit blinks." unused).
- **DOC CAP**: NAMED 245,616 B -> `## M272`+`## M273` rotated VERBATIM (sha1
  `aa685936`/`22154fba`, `scripts/m357_named_rotate.py --verify` PASS).
- **OPEN**: ids 0x37/0x38/0x39/0x50; bits no dialog row writes (A 4,6,10,11,13,26;
  B 1,14,25-31).
