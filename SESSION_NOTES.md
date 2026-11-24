

Older sessions: `docs/sessions/sessions-330-330.md` (3 sessions: Session 330, Session 331, Session 330-chain2). The split is by FILE POSITION, not by number — a moved id can be numerically newer than the first kept one, so grep the archive for an id before deciding it is still hot. The hot file starts at Session 331-chain3.

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

## Session 333-chain3 (2026-11-24) — M362: the 0x4db1xx sibling = the FACTION RELATIONS page; its +0x15a0 group = 13 ids that ARE the bits

- **PICK** (M360's alternate): "a second dialog with its own radio/flag block" -> the
  relations page (builder FUN_004db480: title = the faction name at 0x927874+f*0x59c, left
  list = every OTHER faction; +0xa1c = faction, +0xa20 = target), flag widget inline at
  dialog+0x15a0.
- **ACCEPT** `python3 -u scripts/m362_sibling.py` -> **`PASS M362: 22/22 gates`**
  `18298ed8d31de144` (`evidence/m362_sibling.txt:100`), re-run identical;
  `m362_mutate.py` -> **23/23 killed, 22/22 gates named**. Review #390's 8 findings fixed:
  G2b counts in-record slots, G4c binds the label call, G6c forbids unresolved forms, R3
  parses the delta, rotation idempotent.
- **13 rows, ids = bits**: 8,10,4,2,1,1000,2000,20,2000000,400,40000 read
  `0x94d448[fac*0x82f+tgt]`; 80000008,80002000 read `0x94d468` — the prefix picks the
  record's SECOND dword (+0x20 = slot +8); the high-id set IS the 0x94d468 row set.
- **INDEX**: all 13 blocks run one identical 6-insn idiom (shl 6/add/lea/shl 4/sub/add)
  = fac*0x82f + tgt; 0x82f dwords = 0x20bc B; the dialog indexes 12 slots, all in-record.
- **BUILDER** adds the same 13 ids in the same ORDER, one label each from
  FUN_0061482f(0x997b28, [0x997b20+off], 0), 13 DISTINCT slots a0c..a18/d90..dac/df8.
- **HANDLERS/WRITERS**: 0x4dabb0 (plain,A) -> 0x5518f0 clear / 0x551a20 set; 0x4dac30
  (high,B) -> 0x5519c0 / 0x551c40; 0x4dacc0 -> 0x551cf0 one-way; 0x4dad40 -> 0x551d70
  one-way. 4 of 6 writers store BOTH (p1,p2)/(p2,p1); 0x5518f0 also clears B's 0xC00.
- **TRAPS**: stores are RMWs via a copied register — census by FORM, not store shape;
  backward def-use must not cross a branch (0x551d70 arm 2).
- **ROTATION**: `scripts/m362_named_rotate.py` moved M250-M254/M277/M326/M246 VERBATIM to
  `docs/named-archive-m362-rows.md` (sha1 4/4, 2nd run a no-op); NAMED 246,262 B.
- **OPEN**: the 13 labels (0x997b20 heap); bit NOUNS (chain-2 lane); 0x94d5dc.

## Session 333-chain1 (2026-11-24) — B34: a FACILITY completion stamps NOTHING (no writer on the leg; the recorded bytes falsify the stamp at 3 discriminating completions)

`python3 -u -m sim.facstamp` -> **`PASS B34: 10/10 gates  5296fdad6d26caa3`** (`evidence/b34_facstamp.txt:99`,
re-run identical); harness 13/13, NO-OP `[]` (`evidence/b34_mutate.txt:16`). Answer to B33's gap: nowhere.
- **21 stores, and M342's 20 is SHORT BY ONE** (`:14,:88`): all 194 bitmap references are classified
  (11 direct + 183 address loads: 9 `lea`, 174 `mov`-imm, 10 feeding a store) -> API 2 / GRANT 11 /
  SET 1 / COPY 7. The miss is the screen's byte COPY at `4f0d60` (`mov [esi+eax*1],dl`); M342's lea-window was too
  short to reach it. COPY is the only LOSS-capable family.
- **Leg is writer-free, measured**: pop `FUN_004ef5d0` 88 insns, 0 bitmap refs, 0 API calls; the base screen
  (its only caller) 0 API calls, its only bitmap store the unit-only OR. API hosts ∩ pop hosts = ∅ (`:87-88`).
- **6 facility completions in the recorded run** (`:54-59`), not B31's 1: Korolev r0, Virgin Soil s1/s9 (head 2),
  New Jerusalem s1/s9 + Training Camp s15 (head 1). PAY = `st+1 >= 9` — testing `st >= price` misses Korolev.
- **3 discriminate, 3 are vacuous (bit already set)**; all 3 discriminating falsify the stamp ON BYTES
  (`:70-76,:92`): model `[8]`→`[2,8]` (Korolev), `[27]`→`[2,27]` (Virgin Soil) vs the recording's no-bit-2.
- **The 5 gains are not completions** (`:61-67`): before-heads 321/-2/-8/-3/-6 (unit-encoded); Virgin Soil s11
  (gain 4 + LOSS 27, no pay) is the COPY signature.
- **B31 QUALIFIED**: its single negative is real but is 3 boundaries, and it did not flag the vacuous rows.
- **Pitfalls**: `lea`-form writers need register-follow (`mov BYTE PTR [eax],cl` has no bitmap constant — a
  constant-only grep finds 11 of 20); `4f49e1` is a `mov` here (M342 said `and`); head 0 = empty queue, not item 0.
- NAMED 247,680 → 245,677 B by rotating `## B22` verbatim (`scripts/b34_named_rotate.py`, sha1 `524f63de`).

## Session 333-chain2 (2026-11-24) — M361: the A/V radio flags — 4 rows' pending state, 4 reader functions, relabel terminal = GENERIC set-label 0x5fa1e8

- **ACCEPT** `python3 -u scripts/m361_radio_flags.py` -> **`PASS  M361: 38/38 gates`
  `b92f1a61c041ae87`** (`evidence/m361_radio_flags.txt:165`), rerun byte-identical;
  `scripts/m361_mutate.py` -> **30/30 RED, NO-OP none** (`evidence/m361_mutate.txt:66`).
  Review #391 (10 findings, 3 P1) reworked the instrument: function-extent windows from
  index.csv, the commit scan is GLOBAL, "both ways" is now measured, census covers every
  addressing form, read mnemonics are broadened, mutant gate names are exact.
- **GEOMETRY**: flags = `widget+0xa18`, widgets `0x12cbc + k*0xb4c` (table 0x493fe0:
  0x4b->0x493f9d 0x136d4/0x12cbc, 0x4c->0x493f1c 0x14220/0x13808, 0x4d->0x493edc
  0x14d6c/0x14354, 0x4e->0x493f5d 0x158b8/0x14ea0). Ctor 0x48fed0 zeroes all four (`:75-85`);
  the 3 children are vtable objects (`call [eax+0xf0]`), master row 0x12cbc is not.
- **RELABEL TERMINAL**: 0x493ec0 -> `FUN_0061482f(0x997b28,id)` -> 0x5fa1e8(widget,text),
  which frees `[ecx+0xa7c]`, allocs strlen+1, strcpy; **10 call sites/4 fns, 0 flag
  displacements** -> generic set-label, not flag-aware.
- **READERS** 17 sites/4 fns: 0x493ec0 (4), 0x493ff0 (4), 0x492940 (3), 0x492030 (1 load +
  2 cmp); WRITERS 38/8 fns; 3 loner 0x14220 sites are BYTE stores in other classes (`:86-92`).
- **COMMIT** 0x492940: 0x14d6c -> `[+0xa50] |= 0x4000`; 0x14220 -> `[+0xa4c] |= 0x400` (ebx
  by def-use); 0x158b8 -> `[+0xa4c] |= 0x800`. Master 0x136d4 is never committed — 0x492030
  recomputes it as OR of the children (store 0, then 1 per cmp!=0).
- **TOGGLE** 0x493ff0: master-off clears all four + `and ch,0xf3`/`and ah,0xbf` (load from and
  store back to 0x985ab8/0x985abc; 0x400|0x800 / 0x4000 = the commit bits). Propagation runs
  BOTH ways: child ON -> master, and the master toggle -> all three children. **SEED**
  0x4930e0 reads `[+0xa50]` bits, writes each child flag + its relabel cmd.
- **RETRACTED**: none — M360's 0x4e/0x4c/0x4d reading holds; cmd 0x4b is the master row.
- **OPEN**: each row's noun (label text is runtime; 0x997b20's table is not in the file);
  0x4b87f0/0x4b8820/0x4b8a60/0x4b8af0 = audio on/off (INFERRED).
- NAMED: `## M360` rotated VERBATIM (docs/named-archive-m360-rows.md, sha1 e504b483); 247,881 B.

## Session 334-chain2 (2026-11-24) — M364: the NOUNS of the 13 faction-relations bits — 0x1 = PACT, 0x8 = AT WAR (V); the other 11 are standing flags (INF)
- Lever: `FUN_00426d60(fac,tgt,mask)` = `(rel[fac][tgt] & mask) != 0` — 17 insns, `imul 0x20bc`, 0 stores.
  `python3 -u scripts/m364_bitnouns.py` -> **PASS M364: 24/24 gates** digest `f6d006d0281ac189`
  (`evidence/m364_bitnouns.txt:208`), rerun byte-identical; `scripts/m364_mutate.py` 23/23 (`evidence/m364_mutate.txt:25`).
- 232 call sites, 214 with a constant mask: 19 distinct single bits + 16 composites, each composite an OR of bits
  also asked alone (0x800 is the only bit never asked alone). Bit 0x1 is asked at 53 sites over 14 functions.
- NOUNS (V): 0x1 = PACT — the end-pact case block of the diplomacy menu asks mask 1 and branches to
  "DONTHAVEPACT"/"REALLYENDPACT" -> `FUN_00530af0(...,1)`; 0x8 = AT WAR — the declare-vendetta block asks mask 8,
  a CLEAR bit marks a faction you may declare on, and no candidate yields "DIPLONOVENDETTA". The two blocks
  share 0 literals. The natural rival "0x1 is vendetta" is refuted on that disjointness.
- Geometry: the 13 ids are 11 single bits of dword A (record +0x18) + 2 of dword B (+0x38); the only repeated
  positions (0x8, 0x2000) are A/B DIRECTIONAL copies — 4 of the 6 writers write (fac,tgt) and (tgt,fac).
- Co-set rules (`0x5518f0`): `test 0x7 -> or 0x1100000` (the 3-bit group), `test 0x10 -> or 0x8040`; the page's
  apply handler pushes 4 bulk masks: 0x1f = {1,2,4,8,10}, 0x1f89 = {1,8,0x400,0x1000}, 0x2043c20, 0xdd9bc3c0.
- PITFALL (new): a FUNCTION-level literal set cannot discriminate two bits asked by the same function — both
  rows came out carrying all four keys. The witness must be the enclosing `case` block; ALG2 mutates exactly
  that splitter and reddens G4a/G4b/G4c.
- INF/OPEN: nouns of 0x2, 0x4, 0x10, 0x20, 0x400, 0x1000, 0x2000, 0x40000, 0x2000000 and of dword B's 0x8/0x2000.
- NAMED headroom: rotated two settled blocks VERBATIM to `docs/named-archive-m364-rows.md`
  (`scripts/m364_named_rotate.py --verify` PASS, 2/2 stubs); NAMED 247,217 -> 245,296 B.
- REVIEW #393 (Strata, 10 findings / 3 P1) — all 10 FIXED, none dismissed: G1e now EMULATES the sync
  block's index chain instead of comparing constants; G7d reads the parsed dwords; the 0x1f bulk mask is
  printed (the old `v > 0xFF` cap hid it) and gated with SETS/CLEARS; the 17-insn count, the 53-site
  maximum, G5b, G1c and G6a's residual mnemonic all got named mutants (MU18/19/20 added); G7c now tests
  the rival ON THE KEYS; named_rotate's --verify matches stub headers by text, and the selector refuses
  blocks that are themselves stubs (two such picks were undone and replaced).

## Session 334-chain1 (2026-11-24) — M363: the four A/V audio callees touch the MIXER ONLY (0 pref-cell sites in the closure, 6 in the handler)

- **ACCEPT** `python3 -u scripts/m363_audio_callees.py` -> **`PASS  M363: 18/18 gates`
  `66b923f06f4e8866`** (`evidence/m363_audio_callees.txt:132`), rerun byte-identical;
  `scripts/m363_mutate.py` -> **`RUN PASS 20 mutants, NO-OP []`** (`evidence/m363_mutate.txt:38`).
- **ANSWER**: the four are mixer methods, not preference toggles. Their bodies hold ZERO
  absolute data operands and their 8-function closure (them + 0x4b9330/0x4b9370/0x4b9460/
  0x4b94a0) holds ZERO too; the cells have 121 sites/61 fns (0x985ab8) and 99/33 (0x985abc)
  across .text with 0 in the closure (`:11-53`).
- **SHAPE**: 0x4b8a60 = voice-slot START (byte flag slot+0x24 <- 1, play via buffer vtable
  +0x8c), 0x4b8af0 = STOP (flag <- 0, +0x14); index*0x18, bound `cmp [ebp+0x8],0xf`
  (16 slots), buffer ptr slot+0x2c (`:81-86`). 0x4b87f0/0x4b8820 = ONE guarded vtable call
  each into slot 0x60/0x64 of `[this+0x14]` (`:88-91`); no import-form call in the closure.
- **`this` = 0x8a7920** at all 6 handler sites (static sound object), 12 call sites total:
  6 in FUN_00493ff0, 6 in 5 mixer internals (`:64-79`). The cells are written by the HANDLER:
  6 sites, master-off = load both, `and ch,0xf3` / `and ah,0xbf`, store both (`:55-62`).
- **JUMP TABLE 0x4941ec** (image): 0x4b->0x494154 (master), 0x4c->0x494068, 0x4d->0x49400e,
  0x4e->0x4940c3. start/stop pair with the turn-ON/OFF row store (`mov edi,0x1` vs
  `xor ebx,ebx`) 4/4 (`:108-114`); the 0x4e row (flag 0x158b8) is NOT wired to the audio
  object — it calls 0x446490 + two vtable slots (`:116`).
- **QUALIFIED**: M361's "audio on/off (INFERRED)" — measured start/stop + enable/disable over
  a 16-slot voice table, no preference state anywhere in the leg.
- **Pitfall**: an `indirect_calls()` filter that keeps only `DWORD PTR [` makes an
  import-form gate unable to fail — MU12 found it (the closure gate was green on a state it
  could not see).
- NAMED: `## B27` rotated VERBATIM (docs/named-archive-b27-rows.md, sha1 `c327508bcd76`,
  `--verify` 10/10 claims), 247,217 -> 244,834 B; NEXT_PROMPT trimmed to the 12,000 fail.
- **Review #392 round (10 findings, 4 P1, all FIXED in place, no threshold moved)**: G2/G4's
  data window is now 0x800000..0xbfffff as the prose says and `absdata()` no longer drops
  memory-indirect call forms; G5's function count EXCLUDES the no-function sentinel (61/33, was
  62/34); G8 walks back to the first ecx KILL (12 insns, stops at a call) instead of 6; G9 pins
  the exact imul/lea register multisets; G10 requires the `,0x0` compare AND a branch PAST the
  call; G12 pins all four jump-table dwords (found by a new image mutant); G13's per-case
  store/load counts are ANDed in instead of overwritten; G13b pins the whole 0x4e call list.
  Four mutants added (MU17/G3, MU18/G9c, MU19/G13b, MU21/G12) — 20/20 RED, `[]`; the rival
  gate R is reddened by MU1. Digest moved `00277b42` -> `66b923f0` (measurement changed, answer
  unchanged).

## Session 334-chain3 (2026-11-24) — M365: 0x94d5dc = the relations record's third slot (block+0x1ac): zeroed by the writer, ticked on contact, consumed as a DEADLINE

- **ACCEPT** `python3 -u scripts/m365_pair_slot.py` -> **`PASS M365: 22/22 gates` `d1d567339ee8c5b2`**
  (`evidence/m365_pair_slot.txt:142`), re-run identical; `m365_mutate.py` -> **26/26 killed, NO-OP 0,
  cov 22/22** (`evidence/m365_mutate.txt:33`). Review #395 (10 findings) reworked the gate set:
  G2b now counts STORES only (11), G3c names fac/tgt (+0xa1c stride, +0xa20 unit), G4a pins the
  carried register and the 2x(signed byte) delta, G6c stops at a clobber/branch, R4 reads the two
  instructions it cites, the rotate verifier checks the NAMED stub, MU8 split MU8a/8.
- **CENSUS 23**: 8 W / 15 R, 7 fns; 4 abs + 19 base+disp; 0 unclassified (`:3-33`).
- **GEOMETRY**: slot = block 0x94d430 + **0x1ac** = mask 0x94d448 + 0x194 (101 dw). FUN_004da2c0's
  11 stores name six displacements: 0x94d554 (M165's "pair head", 8 B before) + five slots 0x20
  apart (0x94d55c..0x94d5dc); this slot is the LAST.
- **INDEX**: 12 folded = 4*(fac*0x82f+tgt) B ({0x20bc,4} = {0x82f,1}); 11 pointer sites.
- **WRITERS**: only constant = **0** (2 sites, bit-0x10 arm of FUN_00551a20, BOTH directions);
  2 carry ebx (4da604/4da6de); 3 `++`; 1 `+= 2*signed byte` (507fa4, before the 5518f0 clear).
- **PAIR / CONSUMERS**: 0x94d5bc (block+0x18c) same delta class + same base 5/5; deadlines =
  `value + round/50 + 1` (magic 0x51eb851f sar 4 = /50 proved on 0..5000; sibling /25 + 2);
  4 distinct cross-direction cmp; 4 add/lea terms.
- **CORRECTED (M165)**: "8-byte pair (5 pairs)" = ONE head dw + five 0x20 slots. **OPEN**: the
  NOUN (AGE is INFERRED); the key at 0x54a373 is the 4-byte string `"a"` in .data's diplomacy
  action-name table, not a label.
- **PITFALL**: a displacement can appear TWICE in one fn (4da2c0's two loops) — one-edit mutants
  leave the family intact; MU8/MU19 need two.
- NAMED 247,217 -> 243,805 B: M299/M300 rotated VERBATIM (sha1 5bde05a3/c74e41cb).

## Session 335-chain1 (2026-11-24) — B35: WHO calls the grant family — the founder + the new-game setup only, and the recorded births carry the FOUNDER's bit-1 signature

- **ACCEPT** `python3 -u -m sim.grantcall` -> **`PASS B35: 11/11 gates` `fa541d0a2445cacf`**
  (`evidence/b35_grantcall.txt:113`), re-run byte-identical; `scripts/b35_mutate.py` ->
  **18/18 killed, NO-OP `[]`** (`evidence/b35_mutate.txt:20`). Zero box.
- **CALLERS (dump, 781,429 insns)**: `call 0x4e47d0` = 3 sites — `0x4ccbdd` FUN_004cca50,
  `0x59d894` FUN_0059ce10, `0x5a01f8` FUN_0059ec90; `call 0x59ce10` = 1 site `0x5a1579`
  FUN_005a0fa0. Hosts agree with the index's `n_callers` 3/1, 0 unattributed (`:5-14`).
- **ITEM SITES**: FUN_0059ce10 = **11** `call 0x4e44f0` grants, items in address order
  `[6,3,7,27,8,4,6,3,6,3,27]`, 10/11 (set 0x1, base register) + ONE arg-order anomaly at
  `0x59d0a2` (base pushed first, flag last; the item is still the last push) (`:16-30`).
  FUN_004e47d0 = **10** `call 0x507410` mapper sites, 8 literal `[1,3,6,7,3,6,7,26]` + 2
  computed (`0x4e4d13`, `0x4e4d73`) (`:32-45`).
- **MAPPER LAW**: FUN_00507410 (17 insns) = byte `item>>3` (`sar eax,0x3`), mask
  `1<<(item&7)` (`and ecx,0x7`, `shl eax,cl`) — so item i IS bit i; the API's stride is
  COMPUTED (`lea [eax+eax*8]`, `lea [eax+ecx*2]`, `shl 4` = base*0x130), stores `or` at
  `0x4e4528` / `and` at `0x4e4546` (`:47-70`).
- **BIRTH SIGNATURE**: founder does `lea eax,[esi+0x95da9c]` -> `xor ecx,ecx` ->
  `mov DWORD PTR [eax],ecx` + `mov BYTE PTR [eax+0x4],cl` (FIVE bytes) then 7 ORs —
  register-indirect, so B34's `95da9c`-operand store census could not see the zero (`:72-80`).
- **PARITY**: 3 mid-run births — idx 19 `[1]` (r2), 20 `[]` (r2), 21 `[1,3]` (r9); founder
  signature `{1,3,6,7,26}` covers 3/3 (2 discriminating), the new-game set `{3,4,6,7,8,27}`
  1/3 (bit 1 unexplained on both non-vacuous rows) -> the FOUNDER fired, the 11-item path did
  not (`:82-96`). Mid-round: 6 changes = 4 OR (+2/+8/+3/+6) + 2 REPLACE ([1]->[4], [27]->[4]);
  0 birth-shaped, so the zero — not the bit value — is the separator (`:98-110`).
- **OPEN**: which of the founder's 3 sites fired per birth; why base 20 was born EMPTY
  (falsifies "item 1 is unconditional"); which of the 27 `0x4e44f0` callers added bits 3/6.
- **PITFALL (hit twice here)**: a comprehension that reuses an OUTER loop variable (`a`) for
  the address silently digests stale addresses — the second-pass digest read `e07b94e9`
  against `f1c53db1` and only G10 caught it; use `ins[i][0]` inside every comprehension.

## Session 335-chain3 (2026-11-24) — M367: the 13 relations labels ARE labels.txt lines (element = off/4, line = 10+element)
- **ACCEPT** `python3 -u scripts/m367_label_index.py` -> **`PASS M367: 27/27 gates` `a48d5dd630542166`**
  (`evidence/m367_label_index.txt:104`, digest `:105`, re-run identical); `m367_mutate.py` ->
  **30/30 killed, NO-OP 0, cov 27/27** (`evidence/m367_mutate.txt:36`).
- **THE INDEX (not an image string table)**: the loader `FUN_00614681` fopens `labels`+`.txt`
  (mode `rt`, 0x5ea673), `atoi`s ONE line into `0x997b24` = 1089, allocs `count*4` and fills
  `arr[i] = 0x5ea457()` (read line + arena strdup 0x6147ec). Each row loads ONE dword element
  through the VALIDATOR 0x61482f (24 insns, argument read by mov/cmp only).
- **THE MAPPING**: element i = labels.txt **line 10+i** (`#LABELS` line 8; line 9 = `1089` = the 1089
  lines that follow; element 0 = `Mission Year`; 3 lines past it unread).
- **THE TABLE** (id == bit; 11 plain / 2 high dword): 0x1 `Pact`, 0x2 `Treaty`, 0x4 `Truce`,
  0x8 `Commlink`, 0x10 `Vendetta`, 0x20 `I want revenge`, 0x400 `I shall betray`,
  0x1000 `I have infiltrator`, 0x2000 `I want to talk`, 0x40000 `I am atrocity victim`,
  0x2000000 `I have surrendered`; high 0x80000008 `Fight to the death`, 0x80002000 `Fix current
  status as permanent` (`:73-87`); title elem 866 = `Diplomacy for`.
- **ANCHOR (independent of file order)**: the status dam `0x4120c4` tests bit 0x1 of the SAME
  0x82f record -> the je fallthrough loads 0xa14 (`Pact`), its target 0xa10 (`Treaty`).
- **QUALIFIED (M364)**: bit 0x8's label reads **Commlink**, not "at war" (M364 read AT WAR off the
  vendetta case keys) -> a QUALIFICATION, not a retraction: both hold only if 0x8 gates contact (INF).
- **PITFALL**: 18 clamp sites, not 13 — split rows from statics on BOTH the trailing call
  (0x604fd2) AND the `ds:0x997b20` base.
- **REVIEW #398 (9 findings)**: added the alloc data-flow gate (G0d), the count's source (G0e),
  the je-branch gate (G4b), the mask equality (G5a), all-13-triples (G5c).

## Session 335-chain2 (2026-11-24) — M366: relation bits 0x10 / 0x20 — 0x10 = AT WAR (V), 0x20 = the human-branch war record (INF)

- **ACCEPT** `python3 -u scripts/m366_bitnouns.py` -> **`PASS M366: 29/29 gates` digest
  `c36db3d154a5ea1b`** (`evidence/m366_bitnouns.txt:597`, digest computed by the instrument),
  re-run byte-identical; `scripts/m366_mutate.py` -> **32/32** (31 named mutants + MU0,
  `evidence/m366_mutate.txt:33`). Static only, 0 box time.
- **CENSUS** (`:23`): 0x10 = 37 bare / 52 total / 16 fns; 0x20 = 18 bare / 30 total / 5 fns;
  0x20's askers are exactly {FUN_004f6030, FUN_00546800, FUN_0058fa40} — the naming MENU
  (FUN_00442320) is NOT among them (`:574`), which is why 0x20 gets no string noun. The decoder
  is gated (`:28`): 214/232 sites are 3-push cdecl, 212 pop `add esp,0xN`>=0xc, 2 inline-result.
- **WRITERS** (`:36-46`): `FUN_00551a20` `test bl,0x10` -> `and edx,0xfaeef378` (clears
  {1,2,4,0x80,0x400,0x800,0x10000,0x100000,0x1000000,0x4000000}) + `or ebx,0x80000108` (sets
  0x8|0x100|0x80000000); `FUN_005518f0` `test dl,0x10` -> `or 0x8040`.
- **WAR PATH** (`:545-561`): FUN_00507ce0 inlines the predicate on 0x7, calls FUN_005076d0,
  then SETs 0x8010; FUN_005076d0 sets 0x10 on both exits (0x507abc/0x507c71) and fires the .data
  keys 0x68d67c/0x68d684 = `INCITED` / `VENDETTAWARNING` (bytes read from the image). Its
  0x551cf0 call is `(_,_,0x20,1)`; FUN_00551cf0's 4th arg picks CLEAR by `je`, so 1 = SET.
- **READ SIDE** (`:566-573`): 0x51ef55 `test [pair],0x40020` + `jne` past the mild load ->
  SET keeps `ECONOMICLOSE2` ("tiny cubicle"), CLEAR `ECONOMICLOSE` ("country estate").
- **ANSWER**: 0x10 = at war / vendetta in force (V); 0x20 = the human-facing war record (INF).
- **RETRACTED mid-fire**: FUN_00551cf0/0x551d70 are 4-arg and the 4th arg selects SET vs CLEAR;
  reading them as clear-writers inverts the 0x20 story (caught before the first commit).
- **OPEN**: the noun WORD for 0x20; the role of 0x80000000 (set with 0x10).

## Session 336-chain1 (2026-11-24) — M368: 0x2 = TREATY, 0x4 = TRUCE (V); truce < treaty < pact; the classifier is ordered EQUALITY

- **ACCEPT** `python3 -u scripts/m368_peace_ladder.py` -> **`PASS M368: 34/34`** `6f4b692777cc3549`
  (`evidence/m368_peace_ladder.txt:94`) x2; `scripts/m368_mutate.py` ->
  **`RUN PASS 32 mutants, NO-OP []`**, 34/34 gates covered (`evidence/m368_mutate.txt:36`).
- **THE DISCRIMINATING AXIS (behaviour, not labels)**: FUN_005537d0 pushes a bare mask to the writer
  FUN_00551a20 and the POSTER call 0x483470 immediately before it carries the key — 0x553c41/0x4 posts
  0x691144 `ENEMYTRUCE` (`:37`), 0x553f10/0x2 posts 0x691150 `ENEMYTREATY` (`:40`), 0x554165/0x1 has
  no poster (`:43`). A swapped reading needs the keys swapped.
- **LABELS** (`:65-72`): labels.txt element 643/644/645 = Truce/Treaty/Pact, consecutive after
  `Clock`. Bit value runs AGAINST friendship, so behaviour had to pin it.
- **ALGEBRA** (`:47-60`): `test bl,0x1 -> or ebx,0x2` (0x551abc) is the only pact->treaty upgrade in
  781,429 insns (reverse: 0). Both `and` masks are DECODED from bytes: peace `0xffee7faf` (@0x551a88)
  clears exactly {0x10,0x40,0x8000,0x10000,0x100000}, sparing every peace bit; war `0xfaeef378`
  (@0x551b17, under `test bl,0x10`) clears {1,2,4,...}.
- **CLASSIFIER QUALIFIED** (`:74-84`): 0x507975..0x50798f tests 0x1,0x2,0x4; je chains test->test->exit,
  jne 0x5079a1 = match, jmp 0x50799a = the mismatch store; 0 numeric opcodes -> EQUALITY, not the
  numeric rank M366's phrasing suggested. The WORD is retracted, the precedence is not.
- **CENSUS** (`:24-29`): 169 writer call sites; bare peace masks reaching one are exactly {1,2,4} —
  8 sites over exactly 4 hosts (listed in NAMED).
- **REVIEW #399 (3 P1 + 7 P2, all fixed; NAMED 248,819 -> 244,904 by rotation)**: masks now decoded
  from bytes, G1d pins 8/4, G2 ties the key to the POSTER call, PE section table replaces
  `vma-0x400000`, G5c/G6d/G6e added.
- **OPEN**: what FUN_0053f9f0 @0x53fcb3 (mask 0x2) and FUN_00523b20 @0x523f4c (0x1) transact.

## Session 336-chain2 — M369: relations bit 0x8 = COMMLINK (M364's AT WAR RETRACTED)

Static, zero box. ACCEPT `python3 -u scripts/m369_commlink.py` -> **`PASS M369: 23/23 gates digest 475fdceda961ef2d`** (`evidence/m369_commlink.txt:141`), re-run byte-identical; `scripts/m369_mutate.py` -> **39/39 killed** + 1 NO-OP (`evidence/m369_mutate.txt:47`).

- Builder FUN_004db480: 13 (id, offset) rows; row 1 = id 0x8 -> `DAT_00997b20+0xdac` -> element 875 -> labels.txt line **886 "Commlink"** (line = 11+elem; line 10 is the count 1089 — M367's line numbers are 1 low, its texts right).
- Vendetta block (FUN_00442320, 0x442cd3..0x442e42) READS mask 8 both directions — fac operands 0xa24 / 0xa28 — and every `jne` goes FORWARD to 0x442d7d (build the row); the both-zero fall-through (0x442d78) jumps to 0x442cf5 (next candidate); **0 parsed stores** into 0x94d448/0x94d468. Case 7 (0x442c01/0x442c1f) runs the same guard for a NON-war option.
- FUN_00551a20: `or ebx,0x80000108` (0x551b11) is gated by `test bl,0x10` (0x551abf). **M364 ev `:184` mislabels it `test 0x7`** — the 0x7 peace branch clears exactly 0x10|0x40|0x8000|0x10000|0x100000. All five branch tests enumerated, every `and` mask keeps bit 8, the 0x1f test is after the last store: mask 8 = 2 symmetric ORs (0x551be6/0x551c09, reload 0x551bea).
- 10 explicit bit-8 writes, 8 fns. Plain-8 (3): council FUN_00429950 0x42999d (both loops, pairs 1..7), commit FUN_004dadd0 0x4dae13, goody-pod FUN_0056df40 0x56f5ad (test 0x56f565 + jne past the call = set only when clear: **first contact**). War masks co-set it: 0x18, 0x80000008, 0x80000018, 0x88000008 x4.
- FUN_005076d0 pushes 0x10 on BOTH exits (0x507abc/0x507c6d), 0 push 0x8.

RETRACTION: M364's "0x8 = AT WAR" read a guard as the effect; the war bit is 0x10 (M366 V).
REVIEW #400: 10 findings, all fixed in-gate (clear-mask parse, whole-setter enumeration, exact pinned masks, store classifier, pair/direction, pod dominance, council containment, R4 on case 7, NAMED mutants, NEXT_PROMPT newline).
PITFALLS: shard_001.c has TWO identical `for (local_c = 1; local_c < 8; ...)` headers — match the two-line one; a gate must print FAIL, not crash.

## Session 336-chain3 (2026-11-24) — M370: the pref block's writers — 11 cells, 43 stores, 14 fns

- **ACCEPT** `python3 -u scripts/m370_pref_writers.py` -> **`PASS M370: 19/19`** digest
  `2fa7ea3c1bf74394` (`evidence/m370_pref_writers.txt:197`);
  `scripts/m370_mutate.py` **25/25 killed, NO-OP 0, coverage 19/19**
  (`evidence/m370_mutate.txt:30`).
- **CENSUS** (`:7,:16-20`): 85 refs over 76 dwords = 43 STORE / 39 READ / 3 BOUND. Text ==
  bytes only as (site,cell) PAIRS with a rel32 filter (a call's rel32 false-matches 0x92befc
  at 0x52732e). 5 materialisations, all cmp (2 on 0x92bde8 = M332's array end, 3 on 0x92bdfc
  = never a ds: operand).
- **NAMES, two-sided** (`:105-130`): 11 cells carry an INI key on BOTH the loader
  FUN_0058e7f0 and the writeback FUN_0058f0d0, same TEXT at DIFFERENT VAs: Difficulty,
  Faction, Map Type, Top Menu, Preferences, More Preferences, Announce, Rules, Semaphore,
  Time Controls, Customize.
- **PAIRING BY CALL SHAPE** (`:87-103`): 10x 6-push GetPrivateProfileString (key at call-2)
  + helper 0x58e760; backward the only injective direction (forward 2/11). The naive
  nearest-push law names `Laptop` at 0x92befc — killed (G4c).
- **THE OTHER WRITERS** (`:131-150`): 32 non-loader stores in 13 fns — 12 copy a 0x985a**
  bitmap (b8 x6, bc x3, c0, c4 x2), 5 flip ONE mirror bit, 4 write `x&0x1800000`, 5 are
  call returns, 4 computed, 2 CARRIED. The cell always takes a WHOLE-BITSET mirror; 0x58f0d0 flushes it.
- **NARROWED** M332: 0x92bde8 has TWO stores (0x57c7b0 in FUN_0057c550, also writes
  0x985aec), not one.
- **BOUNDARY** (`:156-160`): 0x92bf18..0x92bf30 is a separate 7-dword `Custom World` group
  (pointer sweep); the span ends at 0x92bf14.
- **OPEN**: 0x92bf0c serialises as `Semaphore` but is always `x&0x1800000` (bits 23/24 of
  0x985ae8) — packed field or reused name, INF; 0x92bdf0 unreferenced; 0x5f1394 chain-2.
- **PITFALL**: ghidra_out/index.csv ends FUN_00510730 at 0x51080b; four handler stores at
  0x510901..0x5109f8 need pad-delimited attribution, not the index (`:30-42`).

## Session 337-chain1 (2026-11-24) — B36: the faction-relations STATE MACHINE (10/10, 14 mutants, zero box)

- **ACCEPT** `python3 -u -m sim.relations` -> **`PASS B36: 10/10 gates  digest b20f5818dee2d861`** (`evidence/b36_relations.txt:82`), rerun byte-identical; `--b36` relays it. **Harness** `python3 -u scripts/b36_mutate.py` -> `RUN PASS 14 mutants, NO-OP []` (`evidence/b36_mutate.txt:16`).
- **FUN_00551a20 EXTRACTED AND RUN**: 161 insns, 8 stores. SIX blocks - five `test bl` predicates (0x7/0x1/0x10/0x17/0x1f) on the CURRENT ebx plus an **unconditional tail OR** at 0x551bc7. Extracting that tail as gated was the first defect: contact (mask 8) became a no-op and 2,369/40,960 parity pairs split.
- **TRANSITIONS** (`:39`): pact -> 0x3; truce after war -> 0x8000010c (commlink 0x8, 0x100 survive); war on 0x7|commlink -> 0x80000118; **combined 0x11 -> 0x8000011b** - the tail OR re-adds the upgraded mask AFTER the war clear. No action site sends a combined mask (M368 census), so it is REPRESENTABLE, not observed: declared, not gated.
- **The ladder ACCUMULATES** (truce then treaty = 0x6), so "the current relation" is the CLASSIFIER's precedence (1 then 2 then 4, ordered EQUALITY) - executable now, 65,536/65,536 byte pairs agree with the dump chain.
- **REVIEW #402** (4 P1 / 6 P2, all fixed in the instrument): G0 pairs stores with stored ops, G1 pins the SIX-block shape against a 10-entry op table, G2 adds a FLAT executor, G3 derives its expectations from the program, G5 counts the war-only class (2,563), G6 pins the 16-insn window + ZF semantics, G7 reads the poster strings from terran.exe via the PE table; 14 mutants. B18 stub carries full `path:line` (`--verify` rejects bare cites).
- **PITFALL**: a pre-state carrying 0x1 without 0x2 is NOT repaired by a write that lacks pact - the first G5 draft asserted the wrong invariant and collected 320 false violations. Scope "pact implies treaty" to the WRITE.
- No new retraction; M364's AT WAR (M369) and M368's ranked ladder stay retracted. NAMED rotated `## B18` (sha1 `da5bb857bde0`, `--verify` PASS).

## Session 337-chain2 (2026-11-24) — M371: the war-initiation hosts' 0x8 is COMMLINK; contact and vendetta are TWO bits

- **ACCEPT** `python3 -u scripts/m371_war_contact.py` -> **`PASS M371: 18/18 gates`** digest
  `4e82206112fe63ad` (`evidence/m371_war_contact.txt:128`); `scripts/m371_twice.py` byte-identical
  (`evidence/m371_twice.txt:4`); `scripts/m371_mutate.py` **27/27 killed** (`evidence/m371_mutate.txt:35`).
- **HOSTS** (`:8-25`): 10 setter calls in the four hosts; the 6 bit-8 rows are exactly
  {0x554389 0x80000008, 0x554426 0x88000008, 0x554e88 0x18, 0x55566e+0x555bb9 0x88000008,
  0x507653 0x80000018}. Roles: FUN_00554d10 MAJORATROCITY, FUN_00507460 AIDSTHEM/AIDSUS,
  FUN_005551e0 -> FUN_00554350 @0x5558cf.
- **SETTER LAW** (`:28-40`): `test bl,0x10`@0x551abf -> measured `or ebx,0x80000108`@0x551b11
  (31,8,0x100): any war request leaves as war+contact, both directions 0x551be6/0x551c09.
  16 callers request war with NO contact bit (14x0x10, 0x8010, 0x50), incl. both FUN_005076d0
  exits (`:64-68`).
- **PEACE** (`:35-40`): of three and-masks x2 sites only the 0x7 mask 0xffee7faf clears 0x10;
  none clears bit 8. Pure-8 writes = 4: new game 0x5a7c0a, council 0x42999d, commit 0x4dae13,
  pod 0x56f5ad (`:69-76`).
- **READS** (`:74-80`): `(rel&0x40018)==8`@0x555491, `(rel&0x18)==8`@0x555502; the atrocity
  host tests `al,0x10`@0x554e6b BEFORE writing 0x18.
- **NOUNS** (`:88-97`): id 8 -> labels.txt:886 "Commlink"; 0x10 -> :657 "Vendetta".
- **DECISION: two bits** — rival "8 = war companion" DEAD on three printed predictions (R1
  `:108-113`); pending masks measured 3x0x88000008 + 1x0x80000008 with no 0x10 (R2 `:115-118`);
  a stored 0x18 is the setter's implication (R3).
- **OPEN**: 0x88000008 bits 27/31 (INF); 24 carried sites (5 register masks, 19 not visible);
  the 0x100. **PITFALL**: pushes split by lea/shl — scan 14 insns back, require a 3-push run
  with one immediate (0x554426; MU21). `## M318` rotated to
  `docs/named-archive-m371-rows.md` (`evidence/m371_named_rotate.txt:1`).

## Session 337-chain3 — M372: 0x92bf0c = BIT-STRING slot, not a packed field

- **ACCEPT** `python3 -u scripts/m372_semaphore_cell.py` -> **`PASS M372: 8/8`** digest
  `b699a30c05573575` (`evidence/m372_semaphore_cell.txt:89`), re-run identical;
  `scripts/m372_mutate.py` **20/20 killed, 8/8 covered** (`evidence/m372_mutate.txt:34`).
- **CENSUS** (`:19`): 8 refs text==byte, 5 STORE/3 READ: loader 0x58ecc9; in-game
  0x4dc77c, 0x4dc8c3, 0x57cb1e, 0x57cc66; reads 0x48882e, 0x57c990 (restore),
  0x58f2fe (writeback).
- **THE KEY IS A BIT STRING** (`:28`): writeback pushes key 0x692848 `Semaphore` + flag=1;
  helper 0x58f030's flag!=0 arm loops bits 31..0, '1' set / '0' when `edi` or `esi<8` (min
  width 8): those constants reproduce the shipped `Semaphore=00000000`; the flag=0 decimal
  arm (0x64f980 radix 10) gives `0` — killed.
- **PARSE IS THE INVERSE** (`:46`): helper per cell from the nearest 0x5ea48x call:
  **5 base-2 (0x5ea493->0x628720), 6 base-16 (0x5ea484->0x62876b)**, counts GATED;
  round-trip exact.
- **NOT PACKED** (`:55`): all four stores mask `0x1800000`; the restore clears
  `~0x1800000` in 0x985ae8 then ORs the WHOLE cell (bits stay 23/24, 0 shifts).
  0x4dc77c/0x57cb1e=provably ZERO; 0x4dc8c3/0x57cc66 carry live 0x99aa38 bits 16/17.
- **NAME** (`:62`): 2 image-wide "Semaphore" strings, each referenced once (a push);
  0 data/table pointers -> no other consumer.
- **OCCUPANTS** (`:71`): bit23 read 0x59ef11+0x5a1446, bit24 0x5a1150; owners
  FUN_0059ec90 / FUN_005a0fa0 (new-game), owners GATED; nouns INF.
- **0x92bdf0** (`:78`): 0 refs, 0 address dwords even byte-unaligned across all sections;
  only sweep starts 0x92bf18.
- **REVIEW #404**: 10 findings fixed in-gate (sha1+size re-checked in G0; G1/G4 rows
  split; G3 counts+MU13; G5 image-wide; G6 owners+4 idioms; G7 scans split; cov=ACTUAL
  reds; cache regenerated).
- **PITFALLS**: objdump prints `DWORD PTR ds:0x..`, so `startswith("ds:")` misses a bitset
  load; a break-test ordered before the hit-test loses the reader.

## Session 338-chain2 (2026-11-24) — M374: Semaphore bits 23/24 = the two #RULES "Randomize" toggles

- **ACCEPT** `python3 -u scripts/m374_semaphore_bits.py` -> **`PASS M374: 23/23`** digest
  `705bd8cd7ed3f705` (`evidence/m374_semaphore_bits.txt:76`), re-run byte-identical;
  `scripts/m374_mutate.py` **20/20 killed, cov G1-G5, 1 declared NO-OP** (`evidence/m374_mutate.txt:23`).
- **CHAIN** (`:9-13,44`): `0x92bf0c` bits 23/24 <- `0x985ae8` <- `FUN_004dc5f0`:
  `test eax,0x10000/0x20000`@0x4dc88b/0x4dc89e -> `or ecx,0x800000/0x1000000`@0x4dc892/0x4dc8a5,
  eax = `ds:0x99aa38` (@0x4dc786); the cell store masks `0x1800000`@0x4dc8b7 -> `0x92bf0c`@0x4dc8c3.
- **RECORD** (`:15-21,47`): an 18-bit RULES word = `0x985ac4` bits 0..15 (16 legs, the `shr eax,0xb` leg
  is bit 11) + stage bits 16/17; the other path clears 23/24 with `0xfe7fffff`@0x4dc604; shipped
  INI `Semaphore=00000000` (loader alone sets neither bit).
- **NOUNS** (`:22-27`): `programs/Script.txt` `#RULES` (line 324) itemlist = 18 items; `#AIEDITOR`
  11 items = its 11 record bits (the item<->bit contract); items 17/18 = "Randomize faction leader
  personalities." / "Randomize faction leader social agendas." = bits 16/17.
- **READERS** (`:29-41`): bit23 0x59ef11 seeds FIVE fields 0x94d80c/10/14/18/1c (5 rand calls,
  5 stores) + the pairing arm 0x5a1446 (4 calls 0x551c40); bit24 0x5a1150 runs the 12-slot random
  assignment (zeroes 0xc dwords, stride 0x59c, 8 iterations).
- **KEYS** (`:43-49`): PE strings RULES/AIEDITOR/AIEDITOR2/SCENRULES at 0x68c824/c80c/c818/c82c;
  FUN_004dc5f0 pushes "RULES"@0x4dc6fb.
- **FOOTING REFINED**: the bits do NOT flow from the 0x41a9xx pack over `[0x8f0d60+0x38]`; both only
  SHARE the 0x99aa38 staging scratch (M179) - the writer's source is the RULES record.
- **OPEN**: what the 12 slots enumerate (INF: a 12-entry SE-choice/agenda grid); why the bits sit at
  23/24 rather than 0/1 of the cell (INF: turn-semaphore bits likely occupy 0..22).

## Session 338-chain1 — M373: the pending-vendetta consumer (STATIC 19/19, zero box)

- **ACCEPT**: `python3 -u scripts/m373_pending_vendetta.py` -> `PASS M373: 19/19 gates
  digest 4fd02c603e36c69c` (`evidence/m373_pending_vendetta.txt:165`), rerun byte-identical.
- **THE PICK'S PREMISE IS REFUTED.** `FUN_005551e0` (3,853 B, 1,167 insns) has **ZERO
  immediates of bit 27** (`:54`). Bit 27 is not a decision input there; the gate that
  actually governs the pending-vendetta pass is **bit 13 = 0x2000**.
- **THE CONSUMER** (`:15-19`): six touch points on bit 31 — `test eax,0x80000000`@0x55573c,
  `and eax,0x7fffffff`@0x555750 + store 0x555758 (own), `and ecx,0x7fffffff`@0x55578a +
  store 0x555792 (mirror), and `push 0x80000000`@0x5558da -> setter 0x551a20 @0x5558e1 (the
  ARM). The clear is conditional: `je 0x555809`@0x555741 (not pending) and `jne
  0x555809`@0x55574a (bit13 set) both jump to `and ah,0xdf`@0x555809 — a ONE-SHOT
  protector that scrubs bit13 in the same pass (`:35-43`).
- **BIT 27** is a sticky relations-word bit: 56 exact `0x08000000` immediates image-wide, 5
  of them word-form reads in 4 functions (0x5230f0 FUN_00522b70, 0x532a2c FUN_00531df0,
  0x54687b FUN_00546800, 0x5526ce+0x55278f FUN_005525d0) (`:48-55`).
- **SETTER ARITHMETIC** (`:58-74`): 14 masks, none clears bit 31 AND none clears bit 27;
  0x88000008 is the only mask that SETS bit 27. G4c pins the three sim masks to the dump's
  immediates (0xffee7faf/0xfaeef378/0xff7fffff), so G4a/G4b compute on measured bytes.
- **41 WORD STORES** (`:76-121`): 33 keep bit 31, **2 literal clears** (0x555758/0x555792),
  3 take a caller mask, 3 opaque. `draft claim retracted in-round`: I first read bit 27 as a
  one-write pulse; the executed replay shows it survives 0x80000008, 0x10 and 0x1 (`:139`).
- **THE SECOND CLEARER** (`:124-130`): FUN_005518f0 (`not edx`@0x55196e then AND) clears the
  caller's 3rd arg; FUN_00551cf0 does the same when its 4th arg is 0. 66 call sites, 46 decode a
  contiguous >=3-push run / 35 literal (20 undecoded and disclosed), only TWO carry bit 31: `0x9000ff48`@0x59f176 = a CLEAR inside
  FUN_0059ec90 (faction-elimination sweep), and `0xdd9bc3c0`@0x4da404 whose flag is the
  caller's ebx (`pop ebx`@0x4da3a8) — **OPEN**, not asserted away.
- **HARNESS** `python3 -u scripts/m373_mutate.py`: 16 mutants, each names its gate; MU11/MU12
  target G4c (the dump<->sim literal link), not G4a, because G4a computes on the sim.
- **PITFALLS**: (1) operand fields in the dump EXCLUDE the mnemonic — a regex written as
  `and ah,0xdf` never matches `by[a]`; (2) `push 0x..` has no comma, so a `,imm$` helper
  silently loses every arm; (3) a byte mask on `ah` names bit 13 — `test al,0x20`@0x5556a7 is
  bit 5 and a DIFFERENT guard (R3); (4) a mutation address must be the INSTRUCTION's address,
  not the call site's (`push`@0x59f16f, call@0x59f176).

## Session 338-chain3 — M375: the five unnamed bits are DEAL-PROTOCOL terms; 0x40 owns a 50-tick cell

- **ACCEPT** `python3 -u scripts/m375_relation_bits.py` -> **`PASS M375: 8/8`** `34bcef7ab64b9272`
  (`evidence/m375_relation_bits.txt:88`); re-run byte-identical (`evidence/m375_twice.txt:4`, sha1
  `aef3c85337bb3fe0`); `scripts/m375_mutate.py` **13/13 killed** (`evidence/m375_mutate.txt:16`).
  `:N` = an acceptance-file line. **CENSUS** (`:4-6`): 658 refs = 378 test / 253 load /
  **27 stores**; byte literals only +0/+1.
- **READERS** (`:10-19`): 0x800000 -> 0x53f863 only; 0x40 -> 0x508ebd/0x508ef9/0x547fd0;
  **0x8000 is read ONLY as a byte at +1** (`test BYTE [..+0x94d449],0x80` @0x53bbed; a grep for
  `94d448` misses it); 0x10000 -> 0x547367 + 2; 0x100000 -> 2.
- **SET VOCAB** (`:23-30`): 94 setter calls (76 push-run + 18 via-jcc); 0x800000 arrives ONLY as
  the bare mask 0x800000 (3 sites); 0x8000 only 0x8010; 0x10000 only 0x10004; 0x100000 once.
- **0x40 TIMER LAW** (`:34-43`): the only bit with a counter — 4/4 stores that leave 0x40 set arm
  `0x94d4c8=0x32`; upkeep 0x5552b6 decrements and clears 0x40 at 0 (`and al,0xbf` @0x5552d1); the
  peace mask never touches the cell.
- **0x800000** (`:46-53`): survives only a request with NO 0x17 bit; every status write clears bit
  23 at 0x551b98/0x551bbf and the tail OR cannot restore it. **PITFALL: 0x80000018 is bit 31 +
  war, NOT bit 23** (`& 0x800000 == 0`) — a lookalike.
- **ANCHORS** (`:56-67`): 9 mask+string pairs — 0x800000 'Sending TREATY ON', 0x1000000 'Sending
  TREATY OFF', 0x40 'Sending SET TREATY'. **0x100000** set once at the tail of FUN_0053f9f0 (the
  unit sweep, stride 0x34) that expels b's units from a's tiles.
- **LABELS** (`:70-74`): none of the five is a diplomacy id. **NOUNS**: 0x800000 = 'TREATY ON'
  (V, INF noun); 0x40 = 'SET TREATY' + 50-tick window (V, INF noun); 0x100000 = eviction
  grievance (INF); 0x8000/0x10000 = war/truce companions (OPEN). **OPEN**: 0x53bbed's role;
  0x5526b3 / 0x507d21 hosts; 0x4da404's 4th arg.

## Session 339-chain1 — B37: the treaty lifecycle; peace vs war split (review #408 hardened)

- **ACCEPT** `python3 -u -m sim.treaty` -> **`PASS B37: 8/8`** `5dd4119bd1882d1d` (`evidence/b37_treaty.txt:76`),
  twice byte-identical, same digest (`evidence/b37_twice.txt:2-3`); `scripts/b37_mutate.py`
  **14/14, NO-OP []** (`evidence/b37_mutate.txt:16`).
- **BLOCK** (`:1-14`): 10 insns `0x5552b6..0x5552d4`, `and al,0xbf`@0x5552d1, ONE exit 0x5552d9, so a zero cell stores NOTHING; the 409,000,318-B dump is pinned by sha256 `f67458fa25011f45` (`:13`).
- **ARMS** (`:15-33`): 11 refs = 4 arms + 3 reads + 3 write-backs + 1 lea (partition closed); the caller-mask
  arm's CONTROL FLOW is proved (`test cl,0x40` -> `je 0x551d64` PAST the arm, `:29`), not merely a nearby test.
- **PARITY/REPLAY** (`:35-49`): 2048 pairs 0 disagreements, expiry at tick 50; re-arm t30, status t40, expiry
  ONCE at t79.
- **PEACE vs WAR** (`:51-55`): `0xffee7faf & 0x40 = 0` but **`0xfaeef378 & 0x40 = 0x40`** (0x78 keeps bit 6):
  PEACE clears 0x40 so its lease expires as a **NULL write (49/49)**; WAR keeps it so its expiry is a **real
  clear (0/49)**; 0 of 11 cell refs inside FUN_00551a20. **CORRECTS M375's `evidence/m375_relation_bits.txt:41`
  presentation (a list, not a claim): 0xfaeef378 clears 0x10/0x1, NOT 0x40.**
- **TREATY ON** (`:57-61`): an exhaustive 256-mask sweep - 240/240 masks carrying a 0x17 bit clear 0x800000,
  the 16 that do not keep it; `0xbf & 0x800000 = 0`, so expiry cannot restore it.
- **REVIEW #408** (P1 was REAL) - R3's rival ran 1 tick so `arm_at=30` never fired; now the
  whole 120-turn horizon is replayed and scored per turn. Also fixed: G1 proves the guard DIRECTION, G5 swept
  all 256 masks, the census prints the measured arm count, MU1/MU2 mutate the parsed window, the dump's sha256 is pinned.
- **PITFALLS**: (1) `and al,0xbf` is a BYTE op; (2) a rival scored on END STATE can tie the truth - score the
  per-tick digest (first version 0/49); (3) "event then tick, one per turn" is policy, declared UNMODELED.

## Session 339-chain3 — M377: 0x8000 rides the WAR stamp, 0x10000 the first-contact truce

- **ACCEPT** `python3 -u scripts/m377_companion_bits.py` -> **`PASS M377: 8/8`** `c9e99e3b7e9f0a31`
  (`evidence/m377_companion_bits.txt:98`); re-run byte-identical (`evidence/m377_twice.txt`);
  `scripts/m377_mutate.py` **18/18 killed** (`evidence/m377_mutate.txt:20`). `:N` = a line of
  that evidence.
- **CARRIERS** (`:4-34`): 0x8000 <- the single mask 0x8010 @0x507d1a; 0x10000 <- 0x10004 at
  0x54d2e5 + 0x552680 (into FUN_00530640) and 0x5526b3 (the setter). 24 bare pushes of exactly
  0x8000/0x10000 image-wide, ALL into other callees.
- **HOSTS** (`:38-55`): FUN_00507ce0 is 80 B and only clears status&7 (FUN_005076d0(a,b,-1)
  @0x507d0d) then stamps 0x8010 — 0 essential edges AND `no entry->ret path skips the stamp` (a
  real unconditional test, not the zero-edge proxy). FUN_005525d0 stamps 0x10004 twice,
  FUN_00546800 once; its 4 essential edges are player-bit(a), 0x920434!=0, player-bit(b) and
  rel&0x8==0 (`and edx,0x8`@0x55261a, asserted by def-use); a bypass path DOES exist.
- **READERS** (`:56-61`): 0x8000 has THREE — `test DWORD,0x8020` @0x5380f2/0x541c5c and the byte
  test @0x53bbed. **M375's "0x8000 -> 1 reader" is RETRACTED** (its census took the imm from the
  whole operand, so a register test matched the `0x94d448` displacement). Lift readers require no
  clobbering write between load and test.
- **0x53bbed's ROLE** (`:62-63`): host FUN_0053bb90, only caller FUN_00545c50@0x545d4a. On the
  bit-set path it compares the pair scalar at 0x94e48c for (a,b) vs (b,a) @0x53bc1c; the skip path
  zeroes the flag. 0x547367 skips 'Sending TREATY OFF' x2 + NOPATIENCE(FRIEND) = "no treaty to
  cancel". All 27 direct stores are register-sourced: 0 provable clearer (`:90`).
- **HARDENED** by ai_review #410: +7 checks, MU15-MU18, 6 `sed`-repointed stubs restored.
- **PITFALLS**: (1) an objdump continuation line has NO third column; dropping it invents a
  phantom fall-through (0x507d06) and kills reachability; (2) `last_imm(whole operand)` matches the
  displacement — take the imm from the SOURCE; (3) a setter call's mask is push[-3].

## Session 339-chain2 — M376: the 0x92babc "12 slots" are alpha `#SOCIO`'s SE-effect matrix

- **ACCEPT** `python3 -u scripts/m376_socio_grid.py` -> **`PASS M376: 29/29`** `f22d2b46cc7e9507`
  (`evidence/m376_socio_grid.txt:115`; re-run byte-identical, `evidence/m376_twice.txt` sha1
  `ac23fc9540f77151`); `scripts/m376_mutate.py` **33/33 killed, cov G1-G4**
  (`evidence/m376_mutate.txt:36`). Static only, zero box.
- **REVIEW #409 (10 findings / 5 P1, all fixed in-gate)**: every constant is now read from an
  instruction or a file — header 0x24 = lea-disp - `mov esi,0x92ba98`; keyword capacity =
  `(0x927538-0x9270c0)/0x68`; record base = `mov esi,0x927b2c` - 0x59c (walk end 0x92a270);
  the BSS claim computes .data's file-backed VA end (0x6a9000) and MU26 patches a copy of the PE
  header to redden it; the rand noun is gated on both `call 0x64c6f0`/`cdq` legs; the reader's
  "same buffer" is gated on `push 0x997120` inside formatter 0x4237c0 plus the two call
  addresses; "8 records hit" reworded to the measured "8 records walked, 9 possible pairs". One
  dismissal: the cited `sha1 ac23fc9540f77151` is `sha1sum` of the FILE; the reviewer compared git
  blob ids (a different hash).
- **GEOMETRY** (a tiny insn emulator over 0x5a11ca..f3): cell = `0x92babc + 0xd4*a + 0x2c*b`;
  cell = **11 dwords**; 4 rows / 4 cells; row header 0x24 (name, 4 tech, 4 names).
- **SOURCE** `FUN_0057a070` parses alpha.txt `#SOCIO` (line 746 = the 11 keywords
  ECONOMY..RESEARCH, 748 = 4 categories, 749-764 = 16 choices): keywords -> 0x9270c0
  (0x68 B, count 0x927538, capacity 11), row names -> 0x92ba98+0xd4*o, the +/- tokens ->
  0x92babc. Column i = `strcmp(token,0x9270c0+i*0x68)`, count ADDED.
- **CONSUMER** (M374's bit24): unique (a,b) per faction in a 12-dword registry (`3a+b`), then
  the first weight > 0; stores category/choice at record **+0x584/+0x58c** (+ first-positive
  at +0x594). Derived: `0x9280b8-0x927590 = 0xB28 = 1*0x59c + 0x58c`, cross-checked against
  the reader's own 0x927b14/0x927b1c.
- **READER** 0x4a66d9 prints the pair: `[0x92ba98+d*0xd4]` category name,
  `[0x92baac+d*0xd4+e*4]` choice name (row+0x14), both appended — the agenda is TEXT.
- **NEGATIVES**: 0x92babc is BSS (raw .data ends 0x6a9000) => parser-built, not a .data table;
  rows 0..2 only, so Future Society (row 3) can never be an agenda; the 8th write 0x92a7fc is
  0x58c past the 8-record block end 0x92a270 (OPEN: 9-slot intent vs slack).
- **PITFALL**: per-faction field arrays are written `record[1] + field_off + i*0x59c`, so a
  "+0x584" field appears as the literal 0x927b14; 0x9280b8 looks like a base but is
  record[1]+0x58c. Do not read those literals as record bases.
- Rotated `## M286`/`## M287` VERBATIM -> `docs/named-archive-m376-rows{,2}.md` (sha1
  `25eb67cd987ee782`/`723e6eebf7c77ff8`) for the NAMED cap; both `--verify` PASS.

## Session 340-chain1 — M378: 0x800 = TREATY IN FORCE, 0x20000 = an outstanding treaty request

- **ACCEPT** `python3 -u scripts/m378_bit_nouns.py` -> **`PASS M378: 45/45`**
  `b841021cb7b0f4b8` (`evidence/m378_bit_nouns.txt:115`; re-run identical, sha1
  `da5742aa99cac132` both runs, `evidence/m378_twice.txt:2-3`); `scripts/m378_mutate.py`
  **17/17, NO-OP `[]`** (`evidence/m378_mutate.txt:19`). Zero box.
- **THE ARM B37 COULD NOT NAME** (0x5553e1..0x5553f9, FUN_005551e0): `and edx,0xfffdfbff` then
  `or edx,0x840` = **sets {0x800,0x40}, clears {0x20000,0x400}**, and the next instruction arms the
  50-tick lease `[pair+0x94d4c8]=0x32`. B37 proved 0x40 = "SET TREATY", so **0x800 is the durable
  TREATY-IN-FORCE flag**: this sign arm is its only setter; the PACT path (`test al,0x1`@0x555371,
  `and 0x20c00`) clears it, and M366's war mask `0xfaeef378` clears it.
- **0x20000, the other leg**: `jge 0x555405` on `[pair+0x94d820] >= 0` reaches a 2-insn arm that
  only `or eax,0x20000` on the SAME load (0x55536b); that field takes a **-1 sentinel** (0x55fce0)
  => INFERRED "a treaty request is OUTSTANDING" (both solve arms clear it).
- **0x400 is never asked alone**: all 5 field-inline tests carrying it (`0xc10 0xc11 0xc30 0x40c30`)
  carry 0x800 too; register-form readers `test ah,0x4`@0x5552ff (gates RNG 0x64c6f0) + 0x5468c7.
  **0x20000 has 0 direct readers** (MU13).
- **FUN_00552970 is NOT a 0x800 setter** (B37's lead): its `or al,0x40`@0x552ce4 sets 0x40, and the
  preceding store 0x552cca clears only 0x20. The window's two `and 0xfffff3ff` (0xc00) land on the
  **sibling field +0x94d468** - which has its own 0x400/0x800 bits.
- **CAP**: NAMED 247,824 -> 245,647 B; `## M366`+`## M319` rotated VERBATIM into
  `docs/named-archive-m378-rows.md` (19 rows=19 bullets, `--verify` PASS).
- **PITFALL**: a jcc's operand is one field, so `src()` (splits on comma) returns "" and a
  branch-target scan finds zero predecessors; use `imm2(i.ops)` for one-operand mnemonics.

## Session 340-chain2 — M379: record +0x594 has two AI readers; M376's "8th agenda write" is a pointer, not a store

- **ACCEPT** `python3 -u scripts/m379_field594.py` -> **`PASS M379: 31/31`** `256603d5fb70d2ad`
  (`evidence/m379_field594.txt:85`; x2 cmp-identical); harness
  **22/22** (`evidence/m379_mutate.txt:27`). Static only, zero box.
- **READERS** (positive-displacement sweep): exactly 2 loads of `[k*0x59c+0x927b24]` —
  `0x5a1eac` FUN_005a1ad0 (skip <0, index the local 11-effect vector, >0 adds the weight
  `[0x94e488+k*0x82f*4]`, <0 rejects) and `0x54696c` FUN_00546800 (eax spills to `[ebp+0xc]`,
  `[0x94d67c+..]`, negative -> message block 0x546983).
- **NO static +0x594 store** (mnemonic-complete classifier); the lone
  `[reg+0x594]` (0x4ffff2) is a `malloc(count*4)` heap array (`ds:0x997b20`, store 0x6146c7).
- **RETRACTION (M376 OPEN):** a control-flow interpreter runs the block's own bytes
  (0x5a1160..0x5a121c): **7 bodies, 6 back-edges, 35 stores in 0x9280b0..0x92a268, terminal
  edi 0x92a7fc**, terminated after 1413 steps. `ebx` starts at 1, is inc'd in the body and
  `cmp ebx,8 / jl` tests after it — **0x92a7fc is the terminal POINTER** (seed+7*0x59c),
  never an immediate, never stored. M376 used the bound constant as an iteration count.
- **EXTENT:** 8 records (8*0x59c = 0x2ce0 B): save/load pushes `0x2ce0`+`0x927590` twice;
  8 walks bound at 0x92a270; no static operand addresses a rec-8 field; 0x92a270 is itself a
  scalar global (`mov ds:0x92a270,eax`) -> no 9th slot; slot 0 (human) never seeded.
- **REVIEW #412 (10 findings / 2 P1 / 8 P2, all fixed in-gate):** printed digest + cmp instead
  of a file sha1; complete store classifier; CFG interpreter (+MU19/MU21 algorithm mutants);
  register/branch-target gates; enumerated extent; exe sha1 gated; rotate refuses stubs.
- **LIMIT (OPEN):** stack/heap-copy readers, split displacements (+0x400/+0x194) not excluded.
- Rotated `## M311`/`## M305` VERBATIM -> `docs/named-archive-m379-m311-m305-rows.md`
  (`--verify` PASS).

## Session 340-chain3 — M380: 0x94e48c is the MIGHTY/MEEK strength scalar; 2 of 27 rel rewrites DO drop a stamp

- **ACCEPT** `python3 -u scripts/m380_diplo_power.py` -> **`PASS M380: 7/7`** `5dfd436fe4093015`
  (`evidence/m380_diplo_power.txt:135`; re-run same, `evidence/m380_twice.txt` sha1
  `7455c8e2b5767fc9`); `scripts/m380_mutate.py` **19/19 killed** (`evidence/m380_mutate.txt:23`).
  All 3 M377 OPENs answered.
- **NOUN (OPEN #1)**: per-faction dword at block+0x105c (70 operands, 67R/3W; stride 0x82f dwords,
  base 0x94d430). Its one two-faction compare picks a string: `cmp
  field[a],field[b]`@0x54dcf0, `jle` -> 'MEEK' 0x690f20, else 'MIGHTY' 0x690f18 — a strength
  rating; composition OPEN. WRONGED/ENEMY next door gate on 0x426d60(rel,0x10).
- **BRANCH (OPEN #2)**: FUN_00545c50 is the hub on ds:0x920700; mode 2 -> 0x53a9c0
  (REJPACTMEEK), 3 -> 0x53bb90 (REJTREATYMEEK) = PACT/TREATY validators. Mode-3 arm @0x545d43:
  `call validator / test eax / jne tail / test edi / je tail / call 0x540390`, edi set once at
  0x545ce9 as `sete(ds:0x92077c==3)` — a refusal reaches 0x540390 only when status is 3;
  otherwise NO action, straight to the SEH tail.
- **ERASURE (OPEN #3) + RETRACTION**: M377's "0 provable clearer" was shape algebra over the
  store (opaque source register), not lineage. Def-use behind the 27 finds **2 provable
  droppers**: 0x551b1d `and edx,0xfaeef378` clears **0x10000** on the war mask (load @0x551b0b);
  0x555430 `and ah,0x7f` clears **0x8000** under `(0x985afc&0xf)==2p+1` (load @0x555427). Both
  RMW one pair dword, so the stamps are erasable. Other 25: 11 PRESERVE, 14 unknown.
- **PITFALLS**: (1) `[reg*4+0x94e48c]` is NOT a 4-byte array — all 19 carry the ×2095 scaler
  across several registers; a per-register marker match fails 10/19.
  (2) only `and` clears bit 15 and `or` never does — an `ah` blind spot invents 3 droppers.
  (3) a linear backward walk crosses blocks; stop at a `jmp`.
- Rotated `## M283` VERBATIM -> `docs/named-archive-m380-m283-rows.md` (sha1 `884865b3`).

## Session 341-chain2 — M382: the 0xc00 cluster has 15 readers, not seven; 0x5468c7 asks bits 2|16

- ACCEPT `python3 -u scripts/m382_treaty_readers.py` -> **`PASS M382: 31/31`** `90cb89f84ce7feeb`
  (`evidence/m382_treaty_readers.txt:125`; re-run cmp-identical, `evidence/m382_twice.txt`); harness
  **18/18 killed** (`evidence/m382_mutate.txt:23`). Static only, zero box.
- **CENSUS** (`:9`,`:22`): 36 immediate-mask inline `test [..+0x94d448],imm` + 9 dynamic-mask; **5 pair**
  (0xc30, 0x40c30, 0xc30, 0xc10, 0xc11) and 2 that ask 0x800 alone (0x558cbd/0x56c153, mask 0x810).
  Register readers: 144 loads def-use walked, **8 meet 0xc00** (0x503727 0x546cde 0x5552ff 0x5567bb
  0x558b9d 0x559d04 0x560b77 0x56b652). Population = **15**; the shortlist named 7, of which 6 are readers.
- **RETRACTION (shortlist premise):** 0x5468c7 does NOT ask 0xc00 — `test al,0x4` (bit 2) then
  `test eax,0x10000` -> `[ebp-0x50]` at-war flag. The cluster reader in FUN_00546800 is 0x546cde
  (`test ah,0x8` = 0x800). The census, not the list, is the population.
- **THE ASK** (`:94`): every inline site asks `(pair_dword & mask) != 0` with mask ⊇ 0xc00 and per-caller
  extras {0x30, 0x40030, 0x10, 0x11}. Nonzero = "an accord standing exists" -> **veto on hostile action**
  (0x4ec9c3 bails 0x4ed94e; 0x5859ae clears 0x933289 and jumps 0x58a748 only when it is ABSENT) or a
  **cooperative selector** (0x563165 unit target, 0x56a8a2 nearest-unit counter, 0x523a7c accept the choice).
- 0x5552ff is the **sole 0x400-only** reader and it gates M378's proposal roll (0x840 arm / 0x20000 arm /
  pact clear); 0x560b77 is the sole 0xc00-only (both bits) reader. 5 host functions; AI hub FUN_0055f650
  hosts 5 of 15 (`:101`).
- **LIMIT (OPEN):** the 9 dynamic-mask inline sites (`test [mem],reg`) are unread — a runtime mask could
  name 0xc00; register-through-copy and stack-copy readers are not walked.
