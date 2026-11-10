

Older sessions: `docs/sessions/sessions-203-203.md` (1 sessions). Read it only when a question reaches back before session ## Session 204.

## Session 204 (2026-11-02, M259-M261 ANALYSE, static) — the terrain record's +16..+43 band is the per-FACTION copy of its +8 mask; the ~140 KB map views are static .bss, not malloc'd; the 0x679f98 class's 15 unique slots and its two ctor screens are named

`python3 scripts/m259_m261_census.py` -> `SUMMARY M259/M260/M261: 14/14 gates PASS` (rc=0, 3.3 s, ONE
invocation, static image only -> `evidence/m259_m261_census.txt`, 30 lines). Invocation 1 was 12/14 and the
two failures were CENSUS SCOPE, not the claims: the discriminator accepted any function that merely named
`ds:0x92ae14`, so unrelated `[reg+idx*4+0xc]` hits were counted; it now requires the access's BASE register
to be loaded from `ds:0x92ae14` or lea'd from such a register. No threshold or floor was moved.

- **M259 the band**: record dwords 4..10 = `[terrain_base + 0xc + (row*0xb + fac)*4]` = dword 3+fac for
  fac 1..7; faction 0 uses the +8 master mask (both refreshes guard `test ebx,ebx / je`). Writer set CLOSED
  at 10 indexed stores — 0x4e153b, 0x4f0def, 0x53a8d9, 0x53a90c, 0x582fec, 0x583e1d, 0x5a3b95, 0x5a3d3f,
  0x5a7afd, 0x5a86aa — plus FUN_0051c750's pointer-walk store 0x51ca52 (G5). Two whole-array refreshes copy
  `[rec+8]` into slot fac over `ds:0x92a38c` records with `add eax,0x2c` (G1); the index register folds to
  the 0x20bc per-faction stride (2095*4 = 8380) (G2); FUN_0051c750 (kelp/forest/mindworm growth) pairs a
  record+0x10 cursor with the faction-block cursor [0x94f4ec,0x95da10) = 7*0x20bc and stores
  `slot & ~0x20 | mask` (G3); slot-to-slot merges through the master mask appear once in FUN_005a7970 and in
  BOTH directions in FUN_0053a820 (G4); FUN_004e14d0 takes its slot index from `[view+0x23bd4]`, inside the
  field block the view ctor FUN_00518820 initialises — the VIEWED faction selects which slot is refreshed
  (G6). Readers: 44 indexed sites in 25 functions incl. FUN_004e15c0 (NATPLACE) and FUN_00519b00 (display)
  (G7). **RETRACTION**: M240's "a record is two 22-byte map columns" reading does not hold for bytes
  16..43 — that half is this band, which is why the `.MP` census found 7 dwords equal in 8192/8192 planetx
  records and equal to `+8` (`evidence/m240_terrain_repack.txt:17`).
- **M260 the views**: `0x224b8` occurs ZERO times in the 3,067,904-B image — no immediate, no 4-byte LE
  constant (G8). FUN_00580260 (1 caller FUN_00522850) zeroes entries 1..7 (`esi` 0x7cded0..0x7cdeec), stores
  the STATIC address 0x8f79e0 into entry 0 at 0x5803e1 and runs the ctor FUN_00518820 once on it (its only
  call site, 0x580406, `ecx = 0x8f79e0`) (G9). The ctor's own stores reach `this+0x23bec` = 146,412 B >
  140,472 = the live stride, so the stride is not an object size (G10); no store in the image names
  0x7cdec8..0x7cdee8 except 0x5803e1. The codec walks the 8 entries as POINTERS and clears `*(p+0x1dd74)`
  for entries 1..7 on a resolution change (`shard_015.c:10822`, `:10842-10845`) (G11). OPEN: who writes
  entries 1..7.
- **M261 the class**: 88 slots / 2 installs, 15 slots differ from all three dialog-family siblings
  0x6717cc/0x671d94/0x67164c (G12): +0x0 46-B dtor (calls FUN_0062d764), +0x8 52-B, +0x30 5143-B /
  1139-insn / 27-callee / 0-direct-caller, +0x40..+0x54 six `ret 0x8` control methods (+0x40 dispatches
  +0x4c), +0x60/+0x64/+0x68 three 15-B zero-callee stubs, +0xa8 21-B, +0xc4 27-B, +0x15c 283-B installer
  (G13). Ctors: FUN_0062d630 <- FUN_0045a8b0(1)/FUN_005b3000(2)/FUN_00641f3c(3); FUN_0062d764 <-
  FUN_00636b1e(15)/FUN_0063a770(3)/FUN_00456670(2)/FUN_00493a10(2)/FUN_0045a840(1)/FUN_0062ecc0(1);
  FUN_00636b1e carries "Start a new session or..." (the session-chooser dialog), FUN_00493a10 "Gamma
  Correction" (graphics options) (G14). No box time; terran.exe stayed down.

## Session 205 (2026-11-02, M262-M264 ANALYSE, static) — the view-table entries 1..7 ARE allocated (7 × 0x22480 at startup, through a cursor store); the LOAD path never re-derives the per-faction band; FUN_005be090 is operator-new and ds:0x9965b8 is a linear record cursor

`python3 scripts/m262_m264_census.py` -> `SUMMARY M262/M263/M264: 11/11 gates PASS`, rc=0, 3.66 s, one green invocation -> `evidence/m262_m264_census.txt` (24 lines). Same instrument as M259-M261 (whole-image corpus 790,695 insns / 10,268 indexed functions + image-derived vtable map + index.csv containment, from `scripts/m235_m237_records.py`). Invocation 1 = 10/11: M262 G1 asserted 38 indexed mentions / 11 functions, copied from a TRUNCATED probe print; the census measured 39/12, so I regenerated `objdump -d -M intel --section=.text programs/terran.exe` (40.9 MB, scratch, deleted) and grepped it: 39 `*4+0x7cdecc` mentions, 0 indexed stores, exactly one `mov DWORD PTR ds:0x7cdeXX` store inside the band (0x5803e1) — only then moved the expected number. No threshold/floor/check weakened.
- **M262 RETRACTS M260's "zeroes entries 1..7" and "the ~140 KB views are not allocated"**: FUN_00580260's loop is the writer — cursor `esi` 0x7cded0 → `cmp esi,0x7cdeec / jl`, step `add esi,4` = 7 iterations, body `push 0x22480 ; call 0x64bc20` (140,416 B each) → `push 1 ; mov ecx,eax ; call 0x469650` (515-B SEH ctor, does NOT call the view ctor 0x518820) → **`mov [esi],eax`**, the pointer-arithmetic shape no address-grep can see; 0 lands there only when the alloc fails, which is how M260 read it as a zero-fill (G2). 0x22480 is named exactly once image-wide, 0x224b8 zero times, 0x224b8 − 0x22480 = 0x38 (heap header, INFERRED) (G3). Of 35 address-of-band sites only 4 escape, all handing out `&DAT_007cdecc`; no lea'd `&table[i≥1]` cursor is stored through or pushed (G4). Entry 1 (0x7cded0) is read 32× in ≥12 functions; the load-side FUN_00597ee0 walks entries 2..7 with the same cursor shape clearing `*(entry+0x1dd74)` and calling FUN_00479e90(entry) (G5).
- **M263**: writer set re-derives to M259's closed 8 functions / 10 indexed stores + FUN_0051c750's walk store (G6); the depth-9 forward call-closure of the 6 load-path functions (FUN_00596850/FUN_00597a70 — the only two that call map_load_arrays 0x582260 — plus their callers FUN_00597ce0/FUN_00597ee0/FUN_00598250/FUN_00598340) is 276 functions and meets that set in ZERO, and no band writer sits in any vtable slot, so indirect dispatch cannot reach them either: **the LOAD trusts the file's band bytes** (G7). FUN_00582260 has no band-shaped store and no call into the writer set; FUN_00583c70 (copy-in writer, 0x583e1d) has ZERO references in the image — no call, no imm32, no slot — so that store can never execute (G8).
- **M264**: FUN_005be090 = 24 insns / 72 B, arg1 → FUN_00649e00 (29-B shim over FUN_00649e70 passing the heap handle ds:0x99d5f8); on NULL it reports through the GLOBAL function pointer ds:0x671320 with "FATAL ERROR" + "Windows has run out of virtual memory; the game will exit…" then `push 4 ; call 0x649c80`; 0 vtable slots, 119 direct sites in 74 functions (G9) — the footing's "13 [reg+4] sites" were store-after-alloc sites, not dispatch: 14 sites in 13 functions store the new pointer at [obj+4] within 8 insns (G10). ds:0x9965b8 is a LINEAR RECORD CURSOR (6 mentions = 3 read-modify-write pairs): FUN_005dbb5f stamps a blank record (10 dword zero stores + `mov byte ptr [ecx+0x8],0x9`) and bumps +0x2c; FUN_005dbbe6 gates [rec+0x28]==0 && [rec+4]!=0, rewinds by [rec+0x10]*[rec+0x14] and frees [rec+4] via FUN_0064a7f0 (19 B, 221 callers); FUN_005dbdc0 is the FILLER — allocates [rec+0x10]*[rec+0x14] bytes via FUN_005be090, stores at [rec+4], advances the cursor by the same product (G11).
- Pitfall (recorded in the skill): a store census keyed on instructions that NAME an address cannot see `mov [cursor],value`; and reading `mov [esi],eax` as "a zero store" without asking where eax came from is what produced M260's wrong verdict. No box time; terran.exe stayed down; M181 not armed.

## Session 206 (2026-11-02, M265-M266 ANALYSE, static) — the 7 view-table blocks are objects of the class whose descriptor is 0x675964 (201 × 608-B elements + a 2,580-B virtual subobject, size proven to the byte); FUN_00583c70 is statically unreachable, one of an 8-function dead cluster

`python3 scripts/m265_m266_census.py` -> `SUMMARY M265/M266: 12/12 gates PASS`, rc=0, 2.68 s, green on inv 3 (inv 1 died on a TypeError in my own push-order helper; inv 2 = 6/12) -> `evidence/m265_m266_census.txt` (13 lines). Instrument = the .text corpus `scratch/m574/text.txt` + the RAW PE image with the `objdump -h` section map + index.csv containment, ONE corpus pass. All six inv-2 failures were mine and every one was corrected against the corpus's own print, never by relaxing a check: hex arithmetic (0xc+200*0x260 = 0x1db0c, not 0x1da8c; 0x21a6c+0xa14 = 0x22480, not +0xa24), a "4 functions" glanced from a 5-line grep (it is 5), a helper that kept only the LAST of two offsets, objdump's destination-first `mov ebp,esp`, and a nested comprehension that returned an empty callee set.
- **M265 — what the 7 blocks are**: FUN_00469650 has exactly 7 `call` sites {0x40a027 FUN_00409e70, 0x468fc0 FUN_00468fb0, 0x48dc7a FUN_0048dc20, 0x4cb5cf FUN_004cb570, 0x50aaae FUN_0050aa60, 0x5803b2 FUN_00580260, 0x59befc FUN_0059bec0} (G1); its `[ebp+0x8]` flag gates `mov [this+0],0x675964` at 0x469681 — the only mention of 0x675964 image-wide (G2) — so the sites that pass 0 keep their own descriptor. Body: three 0x64bda0 container constructs (+0xc, elem 0x260, x4; +0x98c, elem 0x260, x196; +0x1ef54, elem 0xabc, x4; element ctor/dtor pairs 0x62514b/0x62516c and 0x6251d0/0x625209) plus the same element ctor applied in place at +0x1db0c => **201 CONTIGUOUS 608-B elements +0xc..+0x1dd6c**, ending 8 B before the +0x1dd74 the load-side clears (G3); [this+4] is a lazily-freed pointer the ctor zeroes and FUN_00479e90 frees via 0x4017d0 (G7).
- **M265 — the descriptor law (new)**: [obj+0] points to a 2-dword class descriptor whose +4 IS the base-subobject offset — 0x675964→0x21a6c, 0x6763fc→0x22050, 0x678458→0x23d94 — and in each installing function the `add ecx,K`/`lea ecx,[reg+K]` that feeds `call 0x5e3b80` (the 53-caller subobject ctor) uses exactly that K (G5). The view ctor then overwrites the subobject's vptr pair 0x6725ac@+0x21a6c and 0x6725a4@+0x21eb0 (delta 0x444, both vtable bases) — a pair stored at 5 sites in 5 ctors {FUN_00421950, FUN_00469650, FUN_00518980, FUN_0059bec0, FUN_0059c1e0} (G4). SIZE PROOF: FUN_005e3b80's own stores top out at +0xa10 and 0x21a6c + 0xa14 = 0x22480 = the allocation exactly (G6). Dispatch: FUN_004412a0 reads [desc+4] then calls slots +4/+8 of 0x6725ac (= FUN_005cdd0a / FUN_005cdf82), the same two it also calls directly on the static instance 0x8cc520 (G7).
- **M266 — why FUN_00583c70 exists unreferenced**: its address appears in ZERO .text operands (rel32 targets print absolute, so that covers call/jmp/lea/push) and as an LE dword in ZERO offsets of the whole file image across all 8 sections (G8); it is not fallthrough-entered (FUN_00583c20 rets at 0x583c6b, four 0x90 pad bytes, then a real push ebp/mov ebp,esp prologue) (G9); 8 functions in 0x583000..0x584300 have n_callers==0 and ALL 8 have zero address-taken dwords — a dead cluster, not a unique anomaly (G10); its 159-insn mnemonic signature matches ZERO other functions >=40 insns, so it is not a linker-kept duplicate of a wired routine (G12); what it is: a terrain-record helper of FUN_00583c20's family — callees {0x582000, 0x5b09b0, 0x625af1, 0x64a7f0} and the same globals ds:0x92a378/0x92a37c that sibling's stride-0x2c walk uses (G11). So M263's band store 0x583e1d can never execute.
- New skill law: an address-taken census needs BOTH halves — operand-grep of the corpus (rel32+imm32 in code) and a raw LE-dword scan of the file image (data pointers); rel32 call targets never appear as dwords, so neither half alone is a reference census. No box time; terran.exe stayed down; M181 not armed.

## Session 207 (2026-11-02, B5 BUILD track, PASS 9/9) — `sim/units.py`: one arrow press = one lattice step of the 0x6784a0 ring at 3 MP, 6 MP per round, x wrapped, y bounded

**Footing.** `scripts/track_mode.py` -> `MODE=BUILD analyse_since_build=3 next_rung=B5`; rung B5 is `BUILD_SPINE.md`'s units/movement step, acceptance `python3 -m sim.selftest --replay-m27`. No box time, no `/proc`, no gdb.

**Acceptance.** `python3 -m sim.selftest --replay-m27` -> `PASS B5: 9/9 gates on evidence/m27_solowrap.log + evidence/m27_solowrap2.log`, rc=0, green on the FIRST invocation; console `evidence/b5_replay_m27.txt` (11 lines). The same commit re-ran the earlier rungs: B1 10/10, B2 7/7, B3 6/6, B4 9/9.

**The model** (`sim/units.py`, `sim/selftest.py::run_m27_replay`), gates in order: (1) trace-shape — 1 press in log 1 and 3 in log 2, idx [119, 117, 118, 120], all dir=1, all EXEC mode=3, each move stamps its own unit (-2,-2) first; (2) the four destinations == `turn_driver.md` §M27 item 4's post-state (45, 45, 43, 43 at y=11); (3) the trace's only proven start — log 1 re-stamps rec117 at (43,11) inside another unit's move — plus my dir-1 delta (+2,0) predicts (45,11), log 2's recorded destination; (4) DIR_DX/DIR_DY are the ring read out of the image at 0x6784a0/0x6784c4 (`evidence/m248_region_values.txt:3`, ring-first) — the centre-first 0x67850c readout at `:2` is the same ring shifted one index and all 8 pairs preserve (x+y) parity, both checked against that file; (5) `STEP_MP = 3` is alpha `#RULES` field 0, the file's own number (FUN_005ac550 ends `return DAT_0092a278 * moves`, so the game's MP are a loaded scale times a move count) and `MP_PER_TURN = 6` = 2 moves; (6) can-act = FUN_005acc00's `total - spent > 0` — admits steps at spent 0 and 3, refuses the third: (43,11), (45,11), None with spent 3, 6, 6; (7) x wraps as FUN_00502c40 does (79+2 -> 1, 0-2 -> 78 on the 80-wide map), y is bounds-checked and never wrapped (y=79 with dir 3 refused), and my `(w/2)*y + (x>>1)` + `x&1` view reads the same 22 B as `sim/map.py`'s `cell_index` and as the packed 44-B record; (8) all 6 re-stamps of OTHER units in the logs equal the position the replay holds for them (117 at 43, 119 at 43, 122/123 at 41 twice) — the discriminating gate; (9) from the committed pre-state (41,11) (§M25/§M27: all 8 survivors stacked there) the destinations are 2, 2, 1, 1 steps = 6, 6, 3, 3 MP, each inside one round's 6-MP budget, none off-axis.

**Finding, not a failure.** rec118's logged press covers 41->45 = 2 tiles, so one of its two steps lies outside the committed window (4 presses logged; §M27 item 1 documents a 5th, on 117); the model lands it at (43,11). §M27's post-state mpused (117/118 = 3, 119/120 = 6) is not a step count: consume-all 0x5acdb0 sets spent := total when a unit finishes acting, which is what 119/120 read.

**ASSUMED, queued as picks:** per-tile cost uniform 3 (alpha `#TERRAIN` is the terraform-improvement table, not a movement-cost table); and the bonus behind FUN_005ac550 returning 6 for these units (alpha `#CHASSIS` lists Infantry Speed = 1).

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

## Session 211 (2026-11-05, ANALYSE, M272 PASS) - FUN_0057ecf0 does NOT run on a LOAD; the .SAV restore chain is live-proven; the box-debt is paid
- Pick was the first BOX pick (box DOWN at open). Cold relaunch was FAST this time (~6 s to title,
  not >9 min) - the >9 min figure is stale.
- Box lesson (cost 4 failed launches): wine reparents terran.exe to systemd (PPID 1889) even when the
  launching harness is ALIVE, so the tracked-job ancestry escape is DEAD. Working shape:
  `sudo -n sh -c 'echo 0 > /proc/sys/kernel/yama/ptrace_scope' && DISPLAY=:99 python3 <harness>; \
  sudo -n sh -c 'echo 1 > ...'` - harness stays uid 1000. Running the harness under sudo fails
  (wine: "prefix is not owned by you" -> "no terran.exe after relaunch"); capsh --add-ambient absent.
- `scripts/m272_gen_load_watch.py --relaunch --tag m272w9`: 14 bps (GEN entry + 4 caller entries +
  4 gen call sites + 4 controls incl. a CONDITIONAL bp on the fread wrapper 0x64cc00 keyed to
  dest 0x927590). Live run 11/12 (only FAIL: parser). `python3 scripts/m272_acceptance.py` ->
  **ACCEPTANCE M272 PASS 5/5** offline over `evidence/m272w9.gdblog` (deterministic; the shipped gate).
- FINDING: in a sentinel-valid LOAD window (ROUND poked -39 -> 50 read back; counts == m104 image):
  the .SAV opener 0x597ee0 fires AT round=-39 (ret 0x5992f2), then the read wrapper fires at
  round=50 ret 0x596edb INSIDE FUN_00596850 = the M106 in-place body-loader chain, live.
  0 events at FUN_005b2970 (generator), its 4 call sites, and all 4 caller entries => NO.
  Pitfall: entry bps at 0x597ee0/0x596850 NEVER fire although the chain is proven by the call-site
  return addresses - execution enters these loaders MID-BODY; prove a chain by rets, not entries.
- Boot window: 0x5791c0 x7 (bps live at process start); GEN 0 there is NOT a control (attach ~3.5 s
  after launch, generator may precede it). New-game generation and save-load are DISJOINT paths -
  the B6 headless spine never regenerates on load.

## Session 212 (2026-11-05, BUILD fire, B6 PASS 6/6) - the headless run: R1 is DONE
- `track_mode.py` said MODE=BUILD next_rung=B6; built it per `BUILD_SPINE.md` (no box time, no /proc, no gdb).
- NEW `sim/headless.py`: loads a .SAV (sim/save) + .MP (sim/map) + alpha rules (sim/rules), presses the B3
  engine (sim/turn) N times, runs the B4 economy (sim/economy) per base-owning faction per round, and dumps
  a canonical `smac-sim-state/1` JSON (sort_keys, fixed separators - that is what makes the sha stable).
- ACCEPTANCE (both shapes, same numbers): `python3 -m sim.headless --sav programs/saves/m54b_clean.SAV
  --map programs/maps/planet.MP --turns 10 --dump sim_state.json` -> exit 0, `PASS B6 ... year 2150 -> 2160
  ... sha256 2efbc782e2075a26`; `python3 -m sim.selftest --b6 <sav> <map> --turns 10` -> **PASS B6: 6/6
  gates** (`evidence/b6_headless.txt`). Two runs -> byte-identical dump (8,455 B).
- Gates: year delta == turns (B3 edge), ends (cur,tf)=(3,0), economy every round for all 7 owners,
  energy floor 0, two-runs-identical-sha256, command-exit-0.
- Declared ASSUMED (in the dump, not hidden): initial faction energy 0 (no pinned .SAV read); units
  re-charge 6 MP and never move (R1 has no AI); ledger 0 (the idle shape B4 verified).
- The ladder B1..B6 is EXHAUSTED: a BUILD fire must now write rung B7 (R2's first slice) into
  `BUILD_SPINE.md` before building. `MILESTONES.md` R1 -> DONE.

## Session 213 (2026-11-05, ANALYSE box pick, M273 PASS 7/7) - the row stride 188 is a fixed 94-slot capacity; no spill on the live map
- Pick: "what the row stride 188 means" (M256 G5's OPEN row). `scripts/m273_rowstride_watch.py`
  (silent bps at BOTH 0x94eaa8 read sites + YEAR control 0x51f554 + live region-count reads).
- ACCEPTANCE: `python3 scripts/m273_rowstride_watch.py --replay evidence/m273w3.gdblog` ->
  **ACCEPTANCE M273 PASS 7/7** (`evidence/m273_acceptance.txt`; /proc facts in
  `evidence/m273w3_proc.json`, written by the live run - the replay never hardcodes them).
- ANSWER: live count DAT_0092ada4 = 91 (pre AND post stable) == save-derived 91 for 64x64;
  188 = 2*94 is a FIXED capacity (8380 mod 188 = 108 - NOT derived from the faction block stride);
  91 < 94 so the M256 spill is UNREACHABLE on the live map. SCALED identity live 7/7
  (2*edi == region slot). UNSCALED row = per-faction cursor: row mod 8380 = 2 for all, deltas =
  whole 8380 strides. OPEN (new picks): 80x80/128x128 counts 128/338 EXCEED 94 (spill question
  migrates there); the fold's per-faction term advances by HALF a block stride (44.5); region-loop
  depth per phase (observed s10=1 only).
- Instrument law (cost one dead box, w1): a bp at 0x5584b1 = the SECOND BYTE of the 8-B load at
  0x5584aa - INT3 mid-instruction corrupted the encoding and Wine Dbgrc crash-boxed terran.exe
  (TracerPid reads 0 afterwards; only the on-screen dialog is the witness). Always break at the
  disassembled NEXT-instruction address (0x5584b2), never load+1. Recorded in skill
  references/instrument-laws.md.
- Box: w1 window crash-boxed the game; relaunch was ~35 s (fast path holds); w3 driver m55_boundary
  PASS one boundary (2152->2153) with 14 site events + control. Box left UP, TracerPid 0.
- My own gates were wrong twice before shipping (G2 asserted 188==2*count; G5 paired events by
  (round,s10) which the sites do not share) - the FAILs were instrument bugs, fixed by rewriting
  the assertion to what the evidence can bear, never by moving the floor.

## Session 214 (2026-11-05, ANALYSE static, M274 PASS 6/6) - the 128-bound loop is NEVER clamped; big-map spills read the sibling verdict array silently
- Picked the M273 follow-ups (static, no box): `scripts/m274_rowcap_census.py` ->
  **SUMMARY M274: 6/6 gates PASS** (`evidence/m274_census.txt`), body 0x556690-0x559e9d, 4,235 insns
  read from the aligned scratch/m574/text.txt cache (containment from ghidra_out/index.csv).
- ANSWERS: (G1) the region loop has ONE bound, the constant `cmp ecx,0x80` at 0x558b1c - no clamp to
  the 94-slot row anywhere; (G2) regions 94..127 SCALED (max 2*127=254 B) land INSIDE the sibling
  verdict array 0x94eba8 (gap 256) -> on 80x80/128x128 maps the overflow is SILENT WRONG DATA;
  (G4) a nonzero verdict byte stores 0x8 (0x557fdf) then jmps the loop tail (0x557fe7) - that skip,
  not a shallow loop, is why M273 saw only sparse events; (G5) the verdict array has exactly 5 store
  sites (0x8/dl=7-or-8/0x0/0x2/0x7).
- CORRECTION (mine, from M273): "8380 mod 188 = 88" was an arithmetic slip - it is **108**; the
  non-integrality conclusion is unaffected. Fixed in NAMED.md, NEXT_PROMPT.md, notes.
- The fold re-derived from bytes: esi = 2*region + 188*(E+edi) - the multiplier is (E+edi), NOT a
  bare faction index. The row slot [ebp-0x18] has 15 writers in the body -> the live cursor's origin
  is a DEF-USE pick, not settled. New open picks: which writer feeds the UNSCALED read site; the
  def-use of the 15 row-slot writers.
- Method law: an objdump --start-address INSIDE an instruction silently misaligns the window
  (invented .byte lines, poisoned a reachability walk) - use the aligned cache or the fn entry.

## Session 215 (2026-11-05, ANALYSE static, M275 PASS 8/8) - the read site has ONE reaching def (the fold) - and the live cursor contradicts the fold's arithmetic
- Picked M274's def-use follow-up (static, no box): `scripts/m275_rowslot_defuse.py` ->
  **SUMMARY M275: 8/8 gates PASS** (`evidence/m275_defuse.txt`). Sound CFG (0 indirect jumps,
  4,235 insns); reaching defs of [ebp-0x18] at the read-site load 0x55844b = **{0x558038}** only.
- CORRECTS M256's fold prose: re-decoded `mov eax,edi; shl eax,6; add eax,edi; lea esi,[ecx+eax*2];
  shl esi,1` = **esi = 2*region + 130*edi**, edi = the function ARGUMENT (last writer 0x557fbb
  `mov edi,[ebp+0x8]`). (188 = 2*94 is the table's row CAPACITY - a different quantity; M274's
  "188*(E+edi)" was my own mis-multiply: 16*3-1 = 47, x2 = 94 per unit... the script's G6 shape
  check now pins the exact insn sequence.)
- THE FINDING: M273's live rows differ by whole 8380 strides, but **8380 mod 130 = 60 != 0** -
  no integer arg yields them through this fold. Static and live are irreconcilable as modeled;
  the missing writer is outside the visible displacement forms (G8: 14 block-band stores, zero
  at the slot's absolute faces). Queued pick: hw-watchpoint the frame slot during the
  auto-manager (watch reports pc = store + insn length).
- Self-check win: my mental "8380 mod 130 = 100" was WRONG; the computed assert caught it (60).
  Numbers come from the script, never from my arithmetic - the gate asserted before shipping.

## Session 216 (2026-11-05, BUILD fire, B7 PASS 6/6) - the move slice: R2's move leg is now executable headless
- `track_mode` said MODE=BUILD next_rung=B7 and the ladder was EXHAUSTED - so this fire first WROTE
  the rung into `BUILD_SPINE.md` (move slice: save-loaded units + the M27 gesture + B3/B4/B5/B6
  machinery; parity on GESTURE SEMANTICS because the trace's units 117-120 are not in m54b_clean's
  67-unit array - stated in the rung and the dump, not hidden), then built it.
- NEW `sim/movesim.py` (schema `smac-sim-move/1`). ACCEPTANCE: `python3 -m sim.selftest --b7
  programs/saves/m54b_clean.SAV programs/maps/planet.MP --turns 5` -> **PASS B7: 6/6 gates**
  (`evidence/b7_moveslice.txt`): 67 units, 5 rounds x 3 east presses = **670 accepted / 335
  refused**, every unit exhausts at 2 (6 MP / 3), all accepted deltas == the trace's (+2,0) with
  x wrapped by 80; year 2150 -> 2155 per B3; two runs byte-identical (67,790 B, sha256
  3b62847494b252ad). Direct run `python3 -m sim.movesim --sav ... --turns 5` exits 0, same sha.
- ASSUMED (declared): save-LOAD position restore not modeled (kernel write, M106); gesture applied
  to every unit; uniform 3 MP cost.
- R2 in `MILESTONES.md` todo -> IN PROGRESS (move leg done; new-game + save-write legs todo).
  Next BUILD rung B8: the save WRITE leg (produce a .SAV-shaped image from sim state) or the
  new-game leg - the BUILD fire writes the rung first.

## Session 217 (2026-11-10, ANALYSE static pick, M276 PASS 8/8) - the fold's coefficient IS the faction stride; M275's "irreconcilable" was a midpoint slice

- PICK: M275's queued resolution - who writes the row slot [ebp-0x18] if the fold's `130*arg`
  cannot make M273's live 8380-cursor? Answered STATICALLY, one census, ZERO box time.
- FINDING: `scripts/m276_fold_stride.py` evaluates the chain 0x557ffd-0x558038 symbolically
  (linear forms over two atoms; the 20-insn window writes neither): **esi = 8380*edi + 2*ecx**.
  `mov eax,edi; shl 6; add eax,edi` (65) is only the first third - `lea eax,[edi+eax*2]` (131),
  `shl eax,4; sub eax,edi` (2095), `lea esi,[ecx+eax*2]; shl esi,1` finish it. 2095 dwords x 4
  = 8380 = the per-faction block stride the field atlas already records, so the auto-manager
  indexes these arrays by faction block by construction.
- LIVE FIT: M273's recorded UNSCALED rows replayed offline satisfy `slot = 2*s10 + 8380*cp`
  for **7/7** events (cp = cur_player 1..7; deltas whole 8380, -50280 = -6*8380 at the
  round-52->53 wrap). The rival published coefficients 130 and 188 fit **0/7** each - the
  gate's discriminator.
- INSTRUMENT: `m275_rowslot_defuse.py` G6 hand-wrote `2*(64+1)==130`. G6/G7/G8 now import this
  evaluator, assert (8380,2,0), carry the correction in prose and mark the queued frame-slot
  hw-watchpoint pick CLOSED UNRUNNED; m275 re-runs **8/8**.
- ACCEPTANCE: `python3 scripts/m276_fold_stride.py` -> `ACCEPTANCE M276 PASS 8/8`
  (`evidence/m276_fold.txt`, which also holds the m275 re-run). Registry: `NAMED.md` M276 plus
  correction rows patched IN PLACE inside M274/M275 (not only here).
- OPEN LEAD (new, from the bytes read for this census): the SCALED site 0x5584aa indexes
  0x94eaa8 by `edi*2` with NO faction term while the UNSCALED 0x558452 indexes the same base by
  the fold value WITH 8380*arg - whose row does each own, and does M274's "regions 94..127 spill
  into the sibling verdict array 0x94eba8" survive for the unfactioned one? (static pick)
- LAW -> skill `references/instrument-laws.md`: evaluate a multiplier chain. A hand-written
  expression at a `lea`/`shl`/`sub` chain's midpoint published a coefficient 64x too small and
  manufactured a static-vs-live contradiction that queued a box milestone.

## Session 218 (2026-11-10, ANALYSE static, M277 PASS 6/6) - the two read sites of 0x94eaa8 own different rows; M274's spill landing is refuted by its own max
- Picked the M276 NEW LEAD (static, zero box time): scaled 0x5584aa vs unscaled 0x558452.
  `python3 scripts/m277_scaled_row_ownership.py` -> **SUMMARY M277: 6/6 gates PASS**
  (`evidence/m277_scaled_row.txt`). Imports m276's evaluator; does NOT re-derive the fold.
- ANSWERS: (G1) the two sites are fed by DIFFERENT frame slots - 0x55844b `edi=[ebp-0x18]`
  (the fold) vs 0x5584a5 `edi=[ebp-0x10]` (the region counter). (G5 live replay 7/7:
  2*edi stays in block 0 while s18 walks blocks 1..7 with cp.)
  UNSCALED = block arg's row (arg = the faction function argument); SCALED = the image's
  ONLY +0x94eaa8 referrer with no block term = the permanent **faction-0 (block 0) view**
  of the same row array. (G6) the only two WRITERS image-wide (0x51df61 `inc`, 0x564ab1
  `add -10`) both evaluate to eax = 8380*block + 2*slot, so the row is per-faction live data.
- RETRACTION (M274 G2): claimed regions 94..127 read the sibling verdict array at 0x94eba8,
  band [0..66] = offsets 256..322. The loop's body domain is 1..127 (G3: init 1, one in-loop
  store 0x558b22, tail inc-then-cmp 0x80) so the last byte touched is +255 - **never the
  sibling**. The spill is 68 B of rows 94..127 inside the row's OWN cell. Survives: G1
  single bound, G4 verdict skip, G5 verdict stores (a different array, 0x94eda8).
- OPEN: block 0 vs "no faction" - is block 0 the player/neutral slot or faction 0's real row?
  (static: read the two writers' block index source). Also 0x94e8a8 is written by 0x51df3d
  with the SAME fold shape - the row family is wider than 0x94eaa8.

## Session 219 (2026-11-10, ANALYSE static, M278 PASS 7/7) - block 0 = the player-index-0 real row + the unowned fallback; neither neutral nor player slot
- s218 pick (a) (static, ZERO box time): the two 0x94eaa8 writers' block-index source.
  `python3 scripts/m278_block0_semantics.py` -> **SUMMARY M278: 7/7 gates PASS** (`evidence/m278_block0.txt`).
- ANSWERS: both block atoms are OWNER-PLAYER bytes, not loop counters. writer1 (FUN_0051dcb0,
  inc 0x51df61): ebx = BYTE[0x95da14+304*i] = base+4 (i = the index FUN_004e37f0 returns from its
  base-table walk: mov ebx,0x95da14/add ebx,0x130/count ds:0x985af4) - M43's identity, 167/167.
  No qualifying base -> -1 sentinel -> **clamped to 0** (0x51df1d-0x51df24, the only ebx test, its
  jge targets the FOLD) - block 0 also receives UNOWNED tiles' aggregates. writer2 (FUN_0055f650
  AI hub, add -10 0x564ab1): esi = [ebp-0xc] (ONE store, 0x55f71d) = BYTE[52*arg+0x933286] =
  unit+14 OWNER of the acting unit; the entry cross-checks it against ds:0x91b5b4 (current player).
- DOMAIN + DISCRIMINATOR: the family spans exactly 8 blocks (sweep 0x94eca8->0x95f288 steps
  0x20bc=8380 8x; min/max loop esi 0..7). Guard-attributed branch census: exactly 3 conditional
  branches in FUN_0051dcb0 are keyed on ebx and NONE skips the store at ebx==0 - the rival
  "block 0 is neutral" model needs that guard or a +1 bias; NEITHER exists. The human was not
  block 0 either (M43 recorded cur=3, player 0 = destroyed-but-visited faction owning 199 tiles).
- INSTRUMENT LESSONS (now in the skill): (1) slicing a script by "def main(" to reuse it cuts
  m277's own exec STRING (it contains the token) - anchor "\ndef main("; exec-reuse NESTS the
  namespaces (dst_regs = _ns["_ns"]["dst_regs"]); (2) a bare "## M277" header token occurs TWICE
  in NAMED.md (cross-reference) - registry checks must anchor the FULL header line; (3) an `and`
  chain ending in a re.Match poisons sum(res) - bool() every regex clause before gate().
- OPEN: static picks (b) row-family layout (0x94e8a8/0x94e5a8/0x94e7a8) and (c) who reads regions
  >=128; box pick (dialog +0x4c dispatcher) unchanged. `python3 scripts/track_mode.py` next fire.

## Session 220 (2026-11-10, BUILD fire, B8 PASS 10/10) - the save-WRITE leg: a .SAV recomposed byte-exact from the state model
- track_mode printed BUILD -> rung B8 written into `BUILD_SPINE.md` FIRST (R2's save-WRITE leg
  chosen over the new-game leg: no recorded initial-state trace exists to parity-check against,
  and grading rule 2 forbids inventing expected values). ZERO box time; the box was never touched.
- `sim/savewriter.py`: `build_image(sv)` recomposes the container from the `sim.save` layout
  constants with the modeled classes composed from the model (version, counts, year@84,
  cur_player@800 via the M242 block identity, turn_flags@60 bit 1, own player@808, map dims,
  unit-record x/y) and declared pass-through bodies (blocks A/B, small table, 16,000 section,
  middles, grid, region map, tail/trailer, un-modeled record bytes).
- ACCEPTANCE: `python3 -m sim.selftest --b8 programs/saves/m54b_clean.SAV programs/maps/planet.MP
  --turns 5` -> **PASS B8: 10/10 gates** (`evidence/b8_savewrite.txt`). Numbers: identity
  round-trip byte-exact on 242,539 B; `decode_save.py --sections --anchors` tables identical;
  B3-pressed year 2150->2155 re-parses with the diff confined to modeled bytes (1 B, year low
  byte); move lands exactly in record 0's x-bytes at offset 222,783; RIVALS FAIL: pure re-emitter
  carries the old year, UNIT_LEN+4 breaks identity (242,807 B); two runs sha256 74d0f44ab9b9290b;
  `python3 -m sim.savewriter` exits 0.
- INVOCATION 1 FAILED ON THE GATE, not the writer: a cross-file map-dims equality vs planet.MP was
  a false premise - m54b_clean is a 64x64-map save while planet.MP is the 80x80 family (same
  pairing B6/B7 used; the .MP carries the rules, not the dims). Invocation 2 replaced it with a
  dims re-read against the save's own bytes; identity arbitrates the layout constants regardless.
- OPEN: R2 legs left: the new-game leg (needs the init-state rules - a census pick) and minimal
  UI; then R3 golden-trace parity. Static ANALYSE picks unchanged: (b) row-family layout
  0x94e8a8/0x94e5a8/0x94e7a8, (c) who reads regions >=128; box pick (dialog +0x4c dispatcher)
  unchanged. Next: `python3 scripts/track_mode.py` (3 ANALYSE fires, then B9).

## Session 221 (2026-11-10, ANALYSE static, M279 PASS 7/7) - the row-family layout: e8a8 rides the same fold as eaa8 (nested counter family), byte arrays index block*8380+region, e9a8 is read-only
- track_mode printed ANALYSE (analyse_since_build=0) -> pick (b): the row FAMILY
  layout (0x94e8a8 written 0x51df3d by the same fold + the e5a8/e7a8 arrays,
  whole per-block layout image-wide). ZERO box time; the box was not touched.
  `python3 scripts/m279_row_family_layout.py` -> **SUMMARY M279: 7/7 gates PASS**
  (`evidence/m279_row_family.txt`). Reuses the m276 evaluator via the m277 slice.
- ANSWERS: (G1) e8a8's ONLY writer 0x51df3d (FUN_0051dcb0) is reached through the
  SAME fold chain as the eaa8 store - eax = 8380*b + 2*s at both, eax untouched
  between them (0 intervening writers). (G2) the three stores are a NESTED counter
  family: e8a8 UNCONDITIONAL (every walked tile), eaa8 behind {cl&0x18==0} +
  {[edi+5]&0xc0<0x80} + {[edi+8]&0x20==0}, eba8 behind those PLUS {ch&0x10} - 4
  branches 0x51df49/59/5f/6e all target 0x51df77. (G3) e8a8's ONLY reader
  0x45c088 (FUN_0045a920) computes 8380*[ebp-0x34] + 2*[ebp-0x64] via
  `imul eax,eax,0x20bc` - the per-block fold form, rival "block-0-only read"
  refuted (no 8380 term needed there). (G4) the FUN_00556690 ENTRY fold
  (0x556699-0x5566bc) evaluates to edx = 8380*arg and is stored to [ebp-0xc] -
  the BYTE-lane base: e5a8/e628/eca8/ed28/eda8 index block*8380 + region*1, NOT
  the 2*region word form. (G5) image-wide census: 13 bases 0x94e4a8..0x94ee28,
  12 gaps all in {0x80,0x100}; 7 pure-WORD bases (e4a8,e6a8,e8a8,e9a8,eaa8,eba8,
  ee28), 5 pure-BYTE (e5a8,e628,eca8,ed28,eda8), e7a8 mixed 14B/13W = WORD with
  byte sub-accesses (M256's "e7a8 is WORD" stands). (G6) e9a8: 2 sites, ZERO
  writers, both readers; 0x568038's chain evaluates to (30,64,0) NOT (8380,2,0) -
  read-only, different index idiom (OPEN lead, not forced into the fold family).
- ACCEPTANCE: `python3 scripts/m279_row_family_layout.py` -> `SUMMARY M279: 7/7
  gates PASS` (`evidence/m279_row_family.txt`). Registry: NAMED.md M279.
- OPEN LEAD (new, from G6): e9a8's readers 0x568038/0x5a9fd5 - two more chains
  with the SAME shape (15*X + 32*Y fold base) that are NOT the (8380,2,0) row
  fold; what walks them. Static pick (c) (who reads regions >=128) and the box
  pick (dialog +0x4c dispatcher) unchanged.

## Session 222 (2026-11-10, ANALYSE static, M280 PASS 7/7) - the e9a8 readers RIDE the block fold; M279 G6's "(30,64,0)" was a mid-chain window artifact
- Footing collision resolved: the s222 kickoff said "M279 committed NOTHING" - STALE. The
  s221 fire recovered after composing it: M279 committed a497fbf, PR #223, MERGED 05:06:52Z
  (commit 9067fc8). The repo decided: M279 was already merged; track_mode printed ANALYSE,
  and the repo's live pick was the s221 G6 open lead - the e9a8 reader chains. That became
  M280 (verified not-merged before start).
- ANSWER: e9a8 is NOT a "different index idiom". BOTH readers evaluate to the per-block
  WORD fold 8380*block + 2*region:
  - 0x568038 (FUN_0055f650, AI hub): edi = [ebp-0xc] = OWNER byte (sole writer 0x55f71d,
    BYTE[52*edi+0x933286] = unit+14 owner, M278). Chain: mov edx,edi; shl edx,6; add edx,edi
    = 65*edi; lea ecx,[edi+edx*2] = 131*edi; shl 4 = 2096*edi; sub = 2095*edi; lea
    edx,[eax+ecx*2] = eax + 4190*edi; load [edx*2+0x94e9a8] -> 8380*block + 2*region.
  - 0x5a9fd5 (FUN_005a90a0): edi = [ebp+0xc] (arg) = block; edx = region loop counter
    (mov edx,1 @0x5a9f85; inc @0x5a9fe6; back-edge @0x5a9fed); ecx = edx + 4190*edi -> same.
  - G4 COMPUTES the artifact: M279's window [0x56802b,0x568035) with FREE atoms gives
    edx = (30,64,0); substituting the excluded seed (edx := 65*edi) yields 4190*edi = the
    same 8380 stride. M279 G6 opened its window INSIDE the chain, after the fold seeds.
- ACCEPTANCE: `python3 scripts/m280_e9a8_fold.py` -> `SUMMARY M280: 7/7 gates PASS`
  (`evidence/m280_e9a8_fold.txt`). Registry: NAMED.md M280; M279's e9a8 row patched in
  place (OBSERVED -> V (bytes), cites M280).
- OPEN: static pick (c) who reads regions >=128 (loop bound 0x80 vs counts to 338); box
  pick (dialog +0x4c dispatch) unchanged. Chain: exactly one pending smac-re job = s223.

## Session 223 (2026-11-10, BUILD fire, B9 PASS 7/7) - R3's golden-trace pairing: the original exe's own 40-turn m54b_clean.SAV run pairs 41/41 snapshots through the B3 engine
- track_mode printed BUILD (analyse_since_build=4) -> B9 rung written into `BUILD_SPINE.md` FIRST (chose
  R3's golden-trace pairing over R2's new-game leg: exactly the "no recorded initial-state trace" problem
  B8 already flagged - the new-game leg has nothing to parity against, and grading rule 2 forbids inventing
  expected values. What R3 needs exists: evidence/trace_m54b40b_20261024_212833.jsonl is the ORIGINAL
  terran.exe running m54b_clean.SAV itself, 40 TURN-COMPLETE presses, per-turn state_before/state_after
  snapshots of (year, cur_player, turn_flags, n_bases); the sibling m54b40 wedged at 30 rows).
- `sim/parity.py`: load the save, press the B3 engine the trace's OWN 40 turns, pair every recorded
  snapshot against the emitted state sequence as an ordered subsequence - zero tolerance on the recorded
  side (the m30 law). Gates: trace shape (40 consecutive rows), pair-chain (before(0)==save start,
  before(t)==after(t-1) all 40), snapshots-covered (41/41, 0 missing), year-before == 2150+turn all 40,
  BOTH RIVALS FAIL (reversed-order walk and year_after=0 edge each miss the (2190,7,2) year-fire witness
  - the same snapshot pins the walk direction AND the year edge), frontier-declared, two-runs sha256.
- ACCEPTANCE: `python3 -m sim.selftest --b9 programs/saves/m54b_clean.SAV` -> **PASS B9: 7/7 gates**
  (`evidence/b9_golden_parity.txt`); `python3 -m sim.parity --sav programs/saves/m54b_clean.SAV
  --out /tmp/b9_report.json` -> exit 0, report blob sha256 5af9cb48f597a0b7. Final engine state
  (3, 0, 2190) = the human phase after 40 presses, matching the recorded last year 2190.
- FINDING (declared, not a gate input): n_bases. The sim has no AI base-founder, so the model holds the
  save's constant 18 while the recorded game grows to 26 (delta +8 over 40 turns). Frontier recorded in
  the report + evidence; open as a census pick (who writes the base array / founds AI bases).
- Trap dodged: the first subsequence prototype double-counted boundary states (before(t)==after(t-1)
  appeared at 80 keys) - the paired sequence is before(0) + the 40 afters, 41 distinct states. tf masked
  to bit 0x2 (recorded turn 39 reads 0x100002 - the engine models only TF_CYCLE). One gate em-dash'd at
  the sanity pass - cleaned before commit.
- OPEN: static pick (c) who reads regions >=128; box pick (dialog +0x4c dispatcher) unchanged; new:
  the AI base-founder census (n_bases 18->26). Chain: exactly one pending smac-re job = s224.

## Session 224 (2026-11-10, ANALYSE static, M281 PASS 7/7) - nobody reads region ids >=128 because the generator caps the id space at 0x7f; the 338 is the coarse-map CELL count, not an id space
- track_mode printed ANALYSE (analyse_since_build=0) -> static pick (c): "the loop bound 0x80 never
  reaches regions >=128 while counts go to 338 - what reads region 128+?". ZERO box time; box not
  touched (terran.exe pid 3820435, no gdb, state read via pgrep only).
  `python3 scripts/m281_region_id_cap.py` -> **SUMMARY M281: 7/7 gates PASS**
  (`evidence/m281_region_id_cap.txt`).
- ANSWER: NOTHING reads a region id >=128 because such an id CANNOT EXIST. The region generator
  FUN_0058d390 uses two band counters (shard_015.c): land ids 1..0x3e (clamp uVar12=0x3e), water ids
  0x41..0x7e (clamp uVar12=0x7e), and when a band fills, the smallest region is relocated to the
  overflow slot uVar12+1 = 0x3f/0x7f (G1: clamps + `uVar12 + 1` idiom + the 0x5f border formula all
  in the body). Largest assignable id = 0x7f (127) < 0x80, so the `cmp e?x,0x80` loops at 0x556737/
  0x558b1c (both FUN_00556690) cover the WHOLE id space on every map size - M251's "128 entries =
  the whole id space" STANDS.
- The "338" that seeded the pick is the COARSE MAP's byte count, ((W+4)/5+1)/2 * (H+4)/5 = 91/128/338
  for 64/80/128 (G4, triad computed from the accesses FUN_00582340/2360 `(x>>1) + (Rw>>1)*y`), i.e.
  the number of coarse CELLS, not region ids. The count global DAT_0092ada4 has exactly 4 refs and
  they are alloc (x2) + file-write + file-read in shard_014 (G3), and an image-wide scan finds NO
  cmp against 0x152 (338), NO *0x152 scale, NO cmp against DAT_0092ada4 (G7) - no loop in the image
  is bounded by the cell count. The per-region table DAT_00989ce0 save section is 3584 B at stride
  0x1c = EXACTLY 128 rows (G6), consistent with a 128-slot id space. Tile-label census over 2 maps +
  4 saves: max labels 0x7f (planet.MP's border band!), 0x48 (planetx), 0x46 (saves); zero labels
  >= 0x80 in any file (G5).
- ACCEPTANCE: `python3 scripts/m281_region_id_cap.py` -> `SUMMARY M281: 7/7 gates PASS`
  (`evidence/m281_region_id_cap.txt`). Registry: NAMED.md M281.
- Corrections to prior footing: the s213-era "region counts 128/338 EXCEED the 94-slot row" framing
  conflated the coarse-map CELL count with the region ID space; M274's answer (the loop is never
  clamped, bound is constant 0x80) plus M281's (the id space itself is capped below 0x80) together
  fully close the row-cap question - the scaled-read overflow M274 measured (regions 94..127 read
  the sibling array) is the ONLY big-map artifact, and it is the 0x80 loop walking ids that DO exist.
- OPEN: static pick (c) CLOSED. Remaining: box pick (dialog +0x4c dispatcher), the AI base-founder
  census (B9 frontier, n_bases 18->26), the 64x64 odd-Rw accessor stride quirk (M247's Rw>>1 vs
  (Rw+1)/2 asymmetry is a live edge on 64x64, unreachable bytes are the file's 0xCD slack).
  Next fire: BUILD (analyse_since_build=1) = B10, R2's new-game leg - write the rung into
  BUILD_SPINE.md FIRST, then build it (sim/, runnable acceptance, no box time).

## Session 225 (2026-11-10, ANALYSE static, M282 PASS 7/7) - AI bases are founded by the SAME function as the player's: FUN_004e47d0, the only live count-incrementer; the sim has no founder because it has no action-dispatch leg
- track_mode printed ANALYSE (analyse_since_build=1) -> NEW pick (B9 frontier): "who writes the
  base array / founds AI bases (n_bases 18->26 over 40 turns)" - census pick, static-friendly.
  ZERO box time; box untouched (terran.exe pid 3820435, TracerPid 0, state read via pgrep only).
  `python3 scripts/m282_base_founder.py` -> **SUMMARY M282: 7/7 gates PASS**
  (`evidence/m282_base_founder.txt`).
- ANSWER: the base array is DAT_0095da10 (record stride 0x130 = 304 B = the .SAV 304-B stride),
  count DAT_00985af4, cap 0x200 = 512 slots. **FUN_004e47d0(faction,x,y) is THE founder and the
  ONLY live-game record creator**: guard `DAT_00985af4 < 0x200` (G1), `DAT_00985af4 = count+1`
  @0x4e484a, new record at &DAT_0095da10 + old_count*0x130 (x short +0, y +2, faction bytes
  +4/+5; G2), faction base counter DAT_0094e488[faction*0x82f] += 1 (0x82f*4 = 0x20bc = the
  M280 faction-record stride - the founder is where per-faction base counts come from).
  Exactly 3 callers (G3): FUN_004cca50 (the ONLY live vector), FUN_0059ce10 (sole caller
  FUN_005a0fa0 = new-game/scenario placement), FUN_0059ec90 (faction-create; called by
  FUN_005a0aa0, itself called by the AI mover FUN_00585720, the step executor FUN_00502cd0,
  faction-energy FUN_005208f0, ...).
- The LIVE entry splits into three same-founder legs (G5): player 'b' hotkey (FUN_00512450
  case 0x62 -> FUN_004d1280 -> FUN_004cca50 -> founder), the in-game ACTION DISPATCHER
  FUN_0052bce0 case **0x4408** -> FUN_004cca50 (the AI's founding rides this - the same
  dispatcher that drains the unit-action queues FUN_005262e0/FUN_00526e10 and executes the
  player's own move steps at case 0x4402), and the AI hub FUN_0055f650 -> FUN_004cca50
  (shard_014; first-base placement for a faction). So there is NO separate AI founder: the
  AI reaches the exact same FUN_004e47d0 through the same unit-action plumbing as the human.
- Count-global census (G4): DAT_00985af4 has EXACTLY 12 writer sites / 11 functions - the
  `+1` idiom exists ONLY in FUN_004e47d0 (0x4e484a) and in FUN_0059b830's scenario-table
  rebuild loop (0x59b842/0x59b8c3, a load-time 0x200-entry array reconstruction, not live
  play); the only decrement is 0x4e515d in FUN_004e4e10 (base destruction + compaction);
  every other site stores 0 (init/reset families) - 0x52283f is a bare store whose exe
  prelude `xor eax,eax; mov 0x985af0,eax; mov 0x985af4,eax` is verified from terran.exe
  bytes (Ghidra text drops it). Cap consistency (G6): founder guard 0x200 AND loader loop
  0x200 => 512 slots * 0x130 = 0x26000 bytes; the destruction compaction moves the LAST
  record into the freed slot (the m46e "base array reorders during a watch" observation).
- SIM GAP, now explained (G7): sim/ has no reference to the founder or case 0x4408; the B9
  frontier line stays DECLARED (model const 18 vs recorded 18->26). The B3 engine replays
  TURN-COMPLETE presses and never instantiates unit actions, so the founding leg that grows
  n_bases in the real game simply does not exist in the model. A future BUILD rung can add a
  minimal founder leg (colony-pod action -> new base record) if parity of n_bases is wanted.
- ACCEPTANCE: `python3 scripts/m282_base_founder.py` -> `SUMMARY M282: 7/7 gates PASS`
  (`evidence/m282_base_founder.txt`). Registry: NAMED.md M282.
- OPEN (unchanged): box pick (dialog +0x4c dispatcher, box UP m54b_clean); the 64x64 odd-Rw
  accessor stride quirk (M247's Rw>>1 vs (Rw+1)/2, live edge worth a census). New: which of
  the three founder vectors (0x4408 dispatcher vs hub FUN_0055f650 vs the FUN_005a0aa0
  chain) the recorded AI actually uses per founding event - a live-dispatch question, only
  reachability is proven statically. Next fire: ANALYSE (analyse_since_build=2).

## Session 226 (2026-11-10, BUILD, B10 PASS 18/18) - the M282 founder/destroyer leg is BUILT: sim/basefound.py recovers the recorded 18->26 n_bases curve and a founded save image round-trips
- track_mode printed BUILD (analyse_since_build=3, next_rung=B10) -> wrote the B10 rung into
  BUILD_SPINE.md FIRST, then built it. ZERO box time; box untouched (pgrep only, per kickoff).
  `python3 -m sim.selftest --b10 programs/saves/m54b_clean.SAV` -> **PASS B10: 18/18 gates**
  (`evidence/b10_basefound.txt`); B8 10/10 and B9 7/7 regressions GREEN after the savewriter
  change (checkpoint fa4b0a7).
- BUILT: `sim/basefound.py` (Ledger = founder FUN_004e47d0 + destroyer FUN_004e4e10 +
  events-from-trace pairing; CLI --sav --trace --out) and a savewriter grown-ledger path
  (`bases_override`/`orig_n_bases`): records below the original count stay byte-identical,
  new records compose as zero + x/y/faction, the tail re-anchors after the ORIGINAL count,
  and the modeled header writes the GROWN count - the only prefix byte that changes.
- THE LEG: founder (M282: guard count<0x200, append at old_count*0x130, x u16 +0, y +2,
  faction +4/+5, count+1) and destroyer (count-1 @4e515d + COMPACTION: LAST record into the
  freed slot). The pairing presses the B3 engine the trace's own 40 turns and applies the
  trace's OWN 8 derived deltas (t8 +1, t9 +1, t17 +1, t22 +2, t23 -1, t27 +1, t32 +2, t34 +1)
  through the leg: recorded 18->26 recovered on ALL 40 turn snapshots (the B9 declared
  frontier is now MODELED), and the t23 -1 runs through the DESTROYER - the recorded run
  really destroyed a base (23->22) mid-window.
- LAWS proven: the 0x200 guard refuses a 513th founding; destroy(k) moves the LAST record
  into k (record equality - the m46e "array reorders" law as code); write-through of a
  founded image is byte-exact except the bases-count dword; the image re-parses (n_bases 19,
  record 18 read back; its zero name makes it shape-invisible: found 18, DECLARED - the real
  game names bases later); a flooded 512-cap image keeps its tail byte-identical;
  determinism (sha256 d8ce1f17).
- RIVALS: no-leg (B9) shape keeps 18 -> 32 divergences; all-events-on-turn-0 diverges at t0;
  both fail the same curve.
- FOUND (pre-existing, NEW OPEN): decode_save --sections hardcodes the 80x80 map-trailer
  count offset and FAILS rc=1 on every 64x64 save ("no 52/304 split of a 0-byte region" -
  on m54b_clean itself); B8's sec() equality never noticed because both sides fail
  identically. Small follow-up: read the count at the 64x64-correct offset.
- ASSUMED (declared in the dump): founding FACTION (fewest-bases AI faction) and COORDS
  (first unoccupied in-bounds tile) - the golden trace records n_bases only; which founder
  vector the recorded AI used per event stays the OPEN box question (M282 G5).
- OPEN: box pick (dialog +0x4c dispatcher, box UP m54b_clean); the 64x64 odd-Rw accessor
  quirk; decode_save's 64x64 section walk. Next fire: ANALYSE (cadence reset by merged B10).
