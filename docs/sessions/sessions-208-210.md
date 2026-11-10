# Session notes archive — sessions 208-210

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 208 (2026-11-02, ANALYSE, M267 + M268 both PASS) — the 0x6725ac/0x6725a4 pair is ONE vtable with two entry points, shared by 1 ctor + 4 destructors of 4 variants of the virtual base at [desc+4]; the 201 x 608 block is tag-initialized, never indexed, never saved

`python3 scripts/m267_m268_census.py` -> `SUMMARY M267/M268: 14/14 gates PASS` (rc=0, 4.2 s, static;
`evidence/m267_m268_census.txt`). Invocations 1 and 2 were instrument bugs, not evidence changes:
7/14 (the pair-store regex left `v` unbound; the vtable "cap" was built from every stored rdata
imm32, which includes mid-table addresses like 0x6725a8) then 13/14 (G9 compared FULL op sequences,
but the ctor carries one dead `mov eax,[ebp-0x4]` reload the dtor lacks: 6 ops vs 5). No threshold,
floor or check was weakened to get green; G2's `lo_b == lo_a` clause was dropped because that cap is
meaningless, and the claim tested instead is the forward-run identity, which passes uncapped.

**M267, the pick.** 5 pair stores, one per installer: 0x6725ac at {0x42197e, 0x469798, 0x518a92,
0x59c01a, 0x59c25b}, 0x6725a4 at {0x42198e, 0x4697aa, 0x518aa2, 0x59c02e, 0x59c26b} (G1). The pair
is ONE table: 0x6725a4 == 0x6725ac - 8, the code-pointer run ends at 0x672a38 from both, 291 slots
from 0x6725ac and 293 from 0x6725a4, and the three head dwords (0x4222c0, 0x405350, 0x422190) are
none of them a Ghidra function start — thunks/labels (G2). **No installer is address-taken anywhere
in the image** (0 LE dwords over all sections; G3), so these are direct-call ctor/dtor bodies, not
vmethods, and the table's own slot 0 is a different function. FUN_00469650 is the CONSTRUCTOR (3 x
_eh_vector_constructor_iterator_ 0x64bda0, 0 x 0x64bc40); FUN_00421950 / FUN_00518980 / FUN_0059bec0
/ FUN_0059c1e0 are DEstructors (0 ctor-iter; 3/4/3/3 dtor-iter 0x64bc40) (G5) — **corrects M265 G4's
"5 ctors"**. Variant markers (G4): 0x675964 | none | 0x678184+0x67817c (the +0x23d94 subobject, the
0x678458 class whose ctor is FUN_0050aa60) | 0x67194c+0x671944 | 0x67194c+0x671944 written into
stack slots. WHY the offsets differ (G6+G7): the ctor also stores `[vptr-4] = [desc+4] - 0x21a6c`
(shard_008.c:5869) and every installer recomputes the same delta with `sub reg,0x21a6c` or
`lea reg,[eax-0x21a6c]` within 14 insns of its pair store — the subobject is a VIRTUAL BASE whose
runtime offset is read from the class descriptor, which is exactly M265's `[desc+4]` law. FUN_0059bec0
reserves 0x25318 = 152,856 B on the stack (the only 0x25318 in the image, G8), constructs the object
with flag 1 (push 0x1 at 0x59beed, so the descriptor store is skipped), calls the save writer
FUN_00597ce0 at 0x59bf46 and destructs it in the same frame.

## Session 209 (2026-11-02, ANALYSE, docs-only cap triage) — NEXT_PROMPT 15,359 -> 14,506 B: the ANSWERED topic enumeration and the s207 RESULT block moved VERBATIM to docs/pick-archive.md §trim-s209

- Trigger: kickoff `wc -c NEXT_PROMPT.md` = 15,359 > the 15,300 cap-triage trigger;
  `track_mode.py` = ANALYSE (analyse_since_build=1, next rung B6); box DOWN, `grep -c 'box time owed'
  SESSION_CURSOR.md` = 0; tree clean. Per the loop rule the cap triage is the whole fire — no
  milestone was started.
- Split, not shave: the two oldest footing blocks moved VERBATIM into `docs/pick-archive.md`
  §trim-s209 (54,860 -> 56,524 B): the ANSWERED bullet's topic enumeration (756 B) and the
  RESULT (s207, BUILD) block (378 B). Provenance checked by script against
  `git show main:NEXT_PROMPT.md`: both strings present in the archive, absent from the live file.
  The live file keeps the id-range + pointers (`NAMED.md` per-id §s196-§s208; the BUILD TRACK B5
  line already carries `NAMED.md` §B5 with its 3 OPEN items).
- Stale footing fixed in passing: ledger now `Merged M54A-M268 + B0-B5 (through #197)` (was
  `M54A-M266 + B0-B4 ... B5 is this PR`).
- Headroom: 14,506 + a ~1,000 B RESULT append lands under 15,300; the next close must move the
  s208 RESULT block (1,274 B) VERBATIM to keep the cycle.
- Not triggered: skill/SKILL.md 59,419 B (<69,000); evidence/ 28.3 MB (warn, trigger 28.5 not
  reached); no new evidence files this fire.

## Session 210 (2026-11-02, ANALYSE, M269+M270+M271 through ONE instrument, PASS 10/10) — the virtual-base delta is image-wide (41 stores / 8 K / 31 functions); the 0x678e40 class is a 152,856-B stack object with ONE instance site; 32 vbtable descriptors close the K census

- ONE script `scripts/m269_m271_census.py` (whole-image `.text` shadow + PE image + `ghidra_out/index.csv`;
  no box, no `/proc`, no gdb) -> `SUMMARY M269/M270/M271: 10/10 gates PASS`; evidence
  `evidence/m269_m271_census.txt`. Acceptance invocations used: 2 (the first printed 7/10 — three offsets I
  had transcribed from a disassembly window into MY gate texts were wrong: the 0x614150 ctor is called at
  +0x252ec not +0x24fec; M215's row ends at 0x247a0+0xb4c = 0x252ec; the dword 0x59c380 appears only at
  0x678e40 because dw(0x678e3c) = 0x405350). No gate, floor or check was weakened.
- M269: the geometric test (a store counts only if its address resolves to `field + [desc+4] - 4`) matches
  41 delta stores in 31 functions at 8 distinct K: 0x18 x11, 0x1c x2, 0x48 x2, 0x8c x4, 0x188 x14,
  0x21a6c x5, 0x22050 x1, 0x23d94 x2. G1/G2: the 5 K=0x21a6c functions ARE M267's 5 installers — the delta
  detector and the install detector name the same 5. Same pass: 177 vptr installs made THROUGH a vbptr of 33
  distinct tables; 9 secondary-view tables each have their primary 8 B above with the identical count;
  biggest family 0x6713a0 (52 installs). 21 lineage-matched stores of a delta value are `sub reg,1`
  arithmetic — reported, not gated.
- M271: 32 of the 247 rdata immediates stored through a register are vbtables (dword[0] and dword[+4] both
  |v| < 0x40000, neither a code pointer), 21 distinct [+4] offsets, and every K M269 found is one of them
  (0x21a6c->0x675964, 0x23d94->0x678458, 0x22050->0x6763fc, 0x188->0x679de0, 0x8c->0x679c28/0x679da4,
  0x48->0x67991c, 0x1c->0x679a98, 0x18->0x6713ac/0x6713f4/0x671408). [0x675964]=0,[+4]=0x21a6c is installed
  only by FUN_00469650 and [0x678458+4]=0x23d94 only by FUN_0050aa60, and both installers carry a delta
  store at their own K.
- M270: 0x678e40 (secondary 0x678e38 at +0x2444) stored exactly once image-wide each, both inside
  FUN_0059bec0 (0x59bf1c/0x59bf26). Slot 0 of each is its deleting-dtor wrapper (0x59c380 -> FUN_0059c1e0 ->
  0x64bb70). Layout closes on itself: +0 the 0x5e3b80/0x5e3ced class, +0x2320 the 0x675964 class
  (0x2320+0x22480 = 0x247a0), +0x247a0 M215's 0xb4c row (= +0x252ec, exactly where the 0x614150 ctor is
  called AND where the dtor calls 0x6141c1), virtual base +0x23d8c = 0x2320+0x21a6c (destroyed via 0x5e3ced
  in both, so it is the same type as the +0 object), size 0x25318 = the only 0x25318 immediate image-wide
  (the alloca probe at 0x59bed1) = the span [ebp-0x25324, ebp-0xc). RETRACT part of M267: FUN_0059bec0 is
  not a destructor (four ctor calls precede its 0x678e40 install; the same objects die at its tail) and its
  0x67194c/0x671944 are M215's ROW at +0x247a0, never [this+0] — the installer of 0x67194c at [this+0] is
  FUN_005faec0 (M215). Callers of FUN_0059bec0: FUN_0050fea0, FUN_00512b40, FUN_00516b80, FUN_0051e700.
- Pitfall (mine, cost one acceptance): offsets read off a head/tail window and typed into a gate are not
  evidence. Let the instrument print them (hex AND decimal) first, then write the sentence.
- Box DOWN (`ps` shows no terran.exe), nothing owed (`grep -c 'box time owed' SESSION_CURSOR.md` = 0); M181
  still unarmed (no box, no positive control). M241 (#180, 2/5) still open by design.
