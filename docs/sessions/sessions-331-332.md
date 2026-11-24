# Session notes archive — sessions 331-332

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

Older sessions: `docs/sessions/sessions-330-330.md` — the hot file cites only THIS archive, so
the chain onward lives here; without this line the older archives are orphans (s292).

## Session 331-chain3 (2026-11-24) — M360: the four row-less ids are A/V radio rows + a swapped id in a SEVENTH widget, not a seventh page

- **PICK** (M357's orphans): "a seventh page nobody builds, or a non-preferences dialog?" ->
  **neither**.
- **ACCEPT** `python3 -u scripts/m360_orphans.py` -> **`PASS M360: 25/25 gates`** digest
  `eb9f07df920a75ab` (`evidence/m360_orphans.txt:137`), re-run identical; `m360_mutate.py` ->
  **23/23 killed, coverage 25/25** (`evidence/m360_mutate.txt:26`).
- **SEVEN widgets** +0x5974/649c/6fc4/7aec/8614/913c/9c64; builder 66 rows (8/12/14/8/13/4/7);
  REBUILD 0x492940 queries **70** (8/12/14/**11**/14/4/7); PAINT paints the same 70.
- **Orphans**: +0x7aec queries 0x37/0x38/0x39, builds none; +0x8614 queries an extra 0x30
  (built in +0x913c); +0x913c **built 0x30, queries 0x50** — a swapped id.
- **MISS SEMANTICS (retraction of draft #1)**: `is_checked` 0x6051fa and `set_checked` 0x6050d4
  scan from 0, exit on `jge` at the count, test `1<<[node+0x14]`: a miss resolves to
  **bit<count>**, not 0 — 8/13/4.
- **0x37/0x38/0x39 are RADIO handlers** (dispatch key (id-0x13) MEASURED at 0x4934d4, class bytes
  1/2/3): a4c 0x800/0x400, a50 0x4000; they set a flag and relabel ctrl 0x4e/0x4c/0x4d via
  0x493ec0, never call set-by-id -> A/V bit 8 is written by nothing (inert, not aliasing).
- **0x50 is a checkbox** but its block never reloads a48: it ANDs stale `[ebp-0x8]` = (a48 &
  0x1000, one write 0x49368c) with 0x8000/0x10000/0x20000/0x4000 -> all 0.
- **RIVALS refuted** `:123-127`: R1 0 rows into 0x913c -> 4; R2 79 add_item sites, 0 foreign, no
  `ds:` widget; R3 1 absent-id write exists; R4 miss leaves n-1 -> n. 8 of 24 set-by-id sites
  target the seven widgets, all in PAINT (`:114`).
- **INFERRED**: the 3 unbuilt A/V ids match Script.txt's 3 unconsumed A/V lines (count only).
- **OPEN**: pre-1.0 builds with those rows; readers of flags [0x14d6c]/[0x14220]/[0x158b8].
- **REVIEW #387**: 11 findings triaged (new G2g/G4f/G5c, G4c re-anchored, G4d reads [ebp-0x8]).

## Session 332-chain2 (2026-11-24) — M359: +0x28 = CARRY CAPACITY (V), +0x27 = reactor level (INFERRED); M356's single-writer row RETRACTED

- **ACCEPT** `python3 -u scripts/m359_design_record.py` -> **`PASS M359: 14/14 gates`**,
  digest `7d4a2d1356c9ff41` (`evidence/m359_x1.txt:112,114`); `diff -q evidence/m359_x1.txt
  evidence/m359_x2.txt` empty; `m359_mutate.py` -> **18/18 RED, NO-OP none**
  (`evidence/m359_mutate.txt:41`), incl. two algorithm mutants (arg resolution MU13, a
  def-use insert MU19) and the carry multiply->add MU7.
- **WRITER** 0x595b10 = the design-record builder. Arg->field map computed from the
  stores (`:26-34`): +0x24<-arg0xc, +0x25<-arg0x10, +0x26<-arg0x14, +0x27<-arg0x1c,
  +0x20<-arg0x18, +0x29<-ret(0x595820), +0x28<-ret(0x570860) or 0.
- **LOADER** 0x579f40 = #UNITS parser. Six stack args (`:38-44`): (row band, chassis,
  weapon, armor, ability bits, **constant 1**), call target 0x595b10; then it writes the
  alpha columns Plan/Cost/Carry/Icon at +0x2a/+0x29/+0x28/+0x2e, each guarded
  (`test`+`jl` for plan<0, `test`+`je` for cost==0/carry==0, jump lands after the store)
  (`:47-55`).
- **+0x28 = CARRY CAPACITY** (V): the auto-value is gated `cmp byte [wep+0x02],0x7`
  (`:61`; alpha #WEAPONS Mode 7 = Transport, same base +0x00 == 99 = Planet Buster);
  0x570860 = chassis +0x03 * arg(reactor), /2 on ability 0x800000 and (3v+1)/2 on 0x80000
  (`:64-90`); the loader's Carry column lands in the same byte. **Two writers** by the
  anchored-register census: 0x595d1c and 0x57a041 (`:57-59`).
- **+0x27 = REACTOR LEVEL** (INFERRED, strong): constant 1 for every basic unit; 127
  loads, the only compare band is **{1:53, 3:54} over 52 clamp sites** (`:92-93`); the UI
  health path scales `clamp(v,1,3)*10/3` with the input written only by the clamp (`:95-96`).
- **RETRACTION** (M356 G14): "+0x28 has ONE writer" is FALSE — the literal-form grep sees
  one; the anchored census (absolute-displacement form + literal base advanced by 0x34)
  sees two (`:57`). +0x2a is the PLAN (M354 called it "class"): the loader's Plan token
  lands there, the Planet-Buster branch hard-sets +0x2a=5 = alpha Plan 5, and **49** sites
  (4 base registers) compare it with 12 (`:98-101`).
- **REVIEW #385** 10 findings (3 P1) all fixed: G12 added (conditional guards), G7 now
  gates the ability chain, G5 replaced by an anchored writer census, G11 generalized
  (43->49 across 4 registers), G6 binds index<<4/+0x02 to the 99 compare, G9 pins the
  full divide + clamp input, G3 binds loader args to the callee's +0x27, resolve_arg is
  def-use (MU19 is the counter-example).
- **OPEN**: alpha #REACTORS has 4 rows but the health readers clamp to 1..3 (pre-SMAX
  path or display bucket?); the +0x27 noun still rests on elimination + the constant 1.

## Session 332-chain1 (2026-11-24) — M358: the 52-byte 0x98ad88 row's full layout; 0x9267e4 is a 128-dword slot table (not 64-byte rows)

- **ACCEPT** `python3 -u scripts/m358_row_layout.py` -> **`PASS M358: 10/10 gates`
  `1af1dcb6fcd4a4b6`** (`evidence/m358_row_layout.txt:98`), rerun byte-identical;
  `scripts/m358_mutate.py` -> **12/13 scored, NO-OP ['MU13'], coverage G1-G10**
  (`evidence/m358_mutate.txt:22`); review #386's 10 findings all fixed (G6 reads the
  builders' bound, G7 parsed shift/mask, G8 the full A chain, G9 decoded immediates,
  G10 store-by-store pairing, G5 parsed stride/jl/start, G2 census counts, cites re-lined).
- **CENSUS**: 1,991 refs (1,907 memory) in 227 functions over the 0x98ad88 span
  (64 rows x 0x34); 756 `imul reg,reg,0x34` sites. 17 field offsets: name
  char[0x20] at +0x00 (the only +0x1f ref is its NUL store), dword +0x20
  (ability mask; dword tests like 0x10000 + byte bit tests), bytes +0x24..+0x2e,
  word +0x30 (byte bit ops on 0x30/0x31), word +0x32 (pre-req); 0x2f and 0x33 are
  never addressed. M356's "46 writes to +0x30" = 25 movs + 21 RMWs.
- **PROTOTYPE**: row 63 (base 0x98ba54) is written whole by FUN_00435610 from a
  source record: +0x141fc->+0x24, +0x14200->+0x25, +0x14204->+0x26,
  +0x14208(dword)->+0x20, +0x1420c->+0x27, and 0xff->+0x2e.
- **0x9267e4**: 10 refs total, 7 memory, ALL `[reg*4+base]`; 128 dwords, two
  64-slot banks (0x40 shared / owner<<6): entry = (slot<0x40 ? 0 : owner<<6) +
  (slot&0x3f), masked by 0x8000003f with a sign repair; the 14-instruction band
  sequence is matched in BOTH builders (0x596000 ecx/ebx, 0x596160 edx/esi).
  The kickoff's "64-byte design row at 0x9267e4" is REFUTED — 64 is the bank
  size, not a record stride.
- **SENTINELS**: the 16 cmp-immediates in the row window (0x98ad90 x12, +0x0c
  x2, +0x10 x1, +0x14 x1) are loop END checks of 0x1c-stride scans; the four
  static loops (0x98aaf0..0xad90 etc.) are exactly 24 iterations. They are NOT
  row fields at +0x08/+0x0c/+0x10/+0x14.
- **flags bit8**: one clearer (`and [+0x31],0xfe` @0x4ef398) and three setters
  (`or [+0x31],0x1` @0x4f05bd/0x5a7d00/0x5a7f67) -> bit 0x100 is a real state
  flag; its noun is OPEN.
- CROSS-REF M359 (chain2, same row): +0x27 = reactor level, +0x28 = carry capacity, +0x2a = plan.
- OPEN: +0x2b/+0x2d/+0x2e nouns; the 24-record 0x1c table's identity
  (it ends at 0x98ad90..0x98ad9c); bit8 noun. NEXT: (x6) pref-block writers;
  B34 = facility +0x8c.
