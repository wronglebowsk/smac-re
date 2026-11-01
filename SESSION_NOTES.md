

Older sessions: `docs/sessions/sessions-174-174.md` (3 sessions). Read it only when a question reaches back before session ## Session 174e.

## Session 174e (2026-10-31) — M185-M187, all PASS (second static batch of three, one instrument)

`python3 scripts/m185_m187_visits.py` -> `evidence/m185_m187_visits.txt`, `SUMMARY M185=PASS M186=PASS M187=PASS`.
- **M185 — the visit's two sub-passes are asymmetric in what they touch.** FUN_00530e30 writes exactly three
  globals (`ds:0x920740 = 0xf`, plus the staging payload pair `ds:0x99aa1c` / `ds:0x99aa20` = record fields
  +0x0/+0x4) and makes 10 calls, including `0x626634` (the write-bytes emitter) at 0x530fc0. FUN_00535940 writes
  47 globals — 13 to -1 (`edi`) and 12 to 0 (`ebx`) — i.e. it RESETS the aggregate scratch set (0x9204c0/0x9206f4/
  0x9206e8/0x9206e4/0x920774/0x9204d8/0x9204cc/0x920750 to -1; 0x9204b8/0x920710/0x920770/0x9204e0/0x920490/
  0x9206ec to 0) and calls 0x5a6cd0 x2.
- **M186 — `[fac*4+0x94d448]` is ASSIGNED, never bit-set.** 27 store sites in 8 functions (FUN_005551e0 x15,
  FUN_00552970 x5, FUN_0052a720 x2 + 5 singles), every one a plain `mov [reg+0x94d448],reg`, and ZERO
  `or`/`and`/`add`/`sub` sites at that displacement. Its 653 refs are byte tests with masks 0x1 (150), 0x10 (62),
  0x20 (34), 0x7 (18), 0x2 (16), 0x8 (10), 0x3 (8) plus whole-dword loads; the 0x40030 mask that FUN_00535c60
  tests appears at exactly TWO sites (0x535ccb and 0x4f2bba in FUN_004f26e0). A claim that a visit is gated on
  bits 0x10/0x20/0x40000 therefore needs the ASSIGNED values, not the test.
- **M187 — the record's +0x20 dword (`ds:0x99aa3c`) is a 3-valued SELECTOR.** 5 stores: three (FUN_00626b46 /
  FUN_00626dfc / FUN_00626f19) copy `[[ds:0x99aa40]+0x3100]` into it, two come from FUN_0048ee00 / FUN_0048ef80.
  14 reads, three of them `cmp`: FUN_004d9ae0 branches on ==1 (0x4d9da0 — writes a unit record at
  0x933289/0x93328c/0x933294, clears bits in [rec+0x93327c], calls 0x4d97c0) and on ==2 (0x4d9dff, only while
  `ds:0x985af0 > 0`); FUN_00616b89 tests ==0. ASSEMBLEGROUP is driven by a 3-way mode stored inside the record it
  emits.

## Session 175 (2026-10-31) — cap triage (#153, merged), then M188-M190 all PASS (static batch of three, one instrument)

- **CAP TRIAGE first, as its own PR (#153):** `NEXT_PROMPT.md` measured 15,466 chars (> the 15,300 triage
  line), so the settled era was SPLIT not shaved — the s171-s174e milestone lines moved verbatim to
  `docs/pick-archive.md` §the s171-s174e milestone lines, the footing keeps one archive pointer + the M181
  lead: 15,466 -> 14,003 chars. The same PR fixed the gate's `skill sync` FAIL: the tracked `skill/` copy
  was CONTENT-STALE in 4 files (70,000-BYTE cap wording, NEXT_PROMPT char-vs-byte cap, batch-DOC-cost rule,
  numbers-as-assertions law, bit-leg census + per-site argument-tuple laws). `git log -S<string> -- skill/`
  returns NOTHING for each, proving the live copy was the newer side — it was rsynced INTO the repo, not the
  reverse.
- **Acceptance (ONE invocation, rc 0):** `python3 scripts/m188_m190_uses.py` -> `evidence/m188_m190_uses.txt`
  (11,794 B) -> `SUMMARY M188a=PASS M188b=PASS M188c=PASS M189a=PASS M189b=PASS M190a=PASS M190b=PASS
  M190c=PASS`. Two earlier invocations died on MY parser, not the game: a `%`-format with 7 specs and 2 args
  (traceback rc 1), and `is_store_dest` missing objdump's `dword ptr ds:` spelling (undercounted stores -> 3
  gates FAIL, and 23/27 RMWs invisible until the byte-op bit shift was fixed). No floor was edited.
- **M188 — the entry count is private bookkeeping.** FUN_0053a9c0 entry: `edx=ds:0x920720`, `eax=ds:0x9204ac`,
  `add eax,edx` -> `[ebp-4]` at 0x53a9dc, +1 ONLY when `ds:0x920720 != 0` (test 0x53a9da / je 0x53a9df / inc
  0x53a9e1 / re-store 0x53a9e2). 43 mentions of `[ebp-4]` = 11 reads + 10 re-stores + 8 inc + 11 dec + 2
  reg-arithmetic; ZERO `push [ebp-4]`, ZERO scaled/index forms; 11/11 reads are consumed by arithmetic or
  cmp/test on the register and NONE reaches a call, so the sum is never forwarded; 4 windows name the rank
  field 0x94d434, the round counter 0x985afc or 0x920720 — the ±1 steps are rank/round-conditioned.
- **M189 — FUN_004e0260 writes 3 non-spill places** (staging pair `ds:0x99aa1c`/`ds:0x99aa20`, and
  `[block(fac)+0x0] = ds:0x999fa4` at 0x4e0336) + 1 spill to `[ebp-4]`; everything else leaves through 4
  emitter calls (0x626634 x2, 0x626581, 0x626ec4); its loop walks 7 records at stride 0x59c = 1436 B (359
  dwords) while ebx walks the 0x20bc = 8380 B faction blocks (0x94f70c + i*8380). **FUN_005a2930 writes
  NOTHING**: 0 stores, 5 tests, exactly 5 callees (0x4d9fb0/0x4b6060/0x4b5f90/0x5844f0/0x5a1950), the last
  reached only when `ds:0x920434` reads 0.
- **M190 — 23 of the 27 "plain mov" stores at 0x94d448 are the store half of a REGISTER-level bit RMW of the
  same field**, which qualifies M186's "ZERO bit-setters" (true only of memory-operand `or/and [..+disp],imm`):
  `or al,0x40` (0x552ce4), `or ecx,0x40020` (0x55487f), `or esi,0xc0020` (0x554d42) SET; `and edx,ecx` with
  ecx=0xffffffdf at 4 sites and `and al,0xbf` CLEAR. Sets union 0xe0c60, clears union 0x8513aee7. Of the
  0x40030 mask: 0x20 set at 2 / cleared at 4, 0x40000 set at 2 / cleared at 0, and **0x10 is never set or
  cleared by any of the 27** — it arrives only via the 4 whole-value assignments (0x52b9c7/0x52b9d0 load
  `[ebp-0x50]`/`[ebp-0x4c]` in FUN_0052a720; 0x55540a/0x55580f store `lea`-built ADDRESSES).

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

## Session 177 (2026-10-31) — M194-M196, all PASS (three static milestones, one instrument + one tracerless live read)

Acceptance: `sudo -n python3 scripts/m194_m196_channels.py > evidence/m194_m196_channels.txt` (12,080 B, rc 0)
-> `SUMMARY M194a=PASS M194b=PASS M194c=PASS M195a=PASS M195b=PASS M195c=PASS M196a=PASS M196b=PASS M196c=PASS`.
`sudo -n python3 scripts/smac_preflight.py` PASSed first (terran.exe 319926, 1 base ours, 6 units held 0 actionable).
Two earlier invocations died on my instrument, not the game: I predicted 15 callee targets and the census found 16
(2 reached through `call dword ptr ds:0x671324` / `ds:0x67134c`); and my "address-sized operand" filter was
SIZE-based, so it flagged 0x800000/0x1000000/0x2000000 - each a single bit - while the discriminator is mnemonic +
popcount (0 `cmp` among 297 tests, widest operand 5 bits). A print-only bug (a 7-hex-digit global regex matches none
of the 6-digit 0x9xxxxx globals, so FUN_00544530's store set printed `{}`) was fixed and the gate STRENGTHENED to
require g544["0x920700"]==7 before the accepted run. No floor was lowered.

- **M194** window 0x99a01c..0x99aa1b = 113 sites / 31 fns: 93 PUSH an address (base 50, slot1 15, slot2 8, slot3 6,
  slot5 6, slot4 5, slot6 2, 0x99a01d 1) vs 20 direct memory ops (5 store, 5 movsx, 7 add, 2 load, 1 cmp). 16 callees
  receive the pointer: 6 are the C string layer (0x64b9d0 thunk x32, 0x64c460 thunk x26, _strlen, _strcmp, _strncpy,
  the 0x7efefeff append-copy 0x64b9e0), 2 indirect; FUN_00631afb (1076 insns, 7 sites) and FUN_00632cad (288, 4) take
  slot addresses at 5 and 2 of their sites. Register indexers: FUN_00625b20 4 `shl reg,8` -> `add reg,0x99a01c` pairs
  (77 sites / 23 fns), FUN_005f0583 1 pair (99 / 66). FUN_006265a2 is 0x626634's SIBLING publish (86 sites / 39 fns):
  shares the guard `cmp [ebp+8],9`, `mov [edx*4+0x999ff4],eax`, `shl edx,8`, `mov byte [edx+0x99a01c],0`. Slot 7: 7
  publishers (0x4d10dd 0x5022a6 0x509163 0x530fc0 0x53438d 0x552eb9 0x594e65), ZERO pushes of 0x99a71c (slots 8/9 also
  0). Live pid 319926: slots 0-4 = 'disciplined'/'Provost'/'Zakharov'/'University'/'Mission Year 2150', 5-9 empty;
  A[10]={1,0x9}, B[10]=0x10, staging 0/0.
- **M195** 0x920700: 31 mentions = 8 stores / 17 loads / 6 tests / 0 RMW. Writers FUN_00544530 x7 (ebx/eax) +
  FUN_00546800 x1 (`mov ds:0x920700,0xc` at 0x54ec5c). Tested set {1,2,4,5,6,7,8,9,a,b,c,d} (12 distinct, max 0xd,
  includes the 0x2 that gates 0x545cfa); live 0x0. ZERO string literals in FUN_00544530 / 00546800 / 00540390 /
  00545c50 -> the mode is UNNAMED. FUN_00544530 (1531 insns, 2 tests of [ebp+8]) also stores 0x997120 x28,
  0x99aa1c x14, 0x99aa20 x14, 0x920748/0x92077c/0x920728 x3, 0x9206fc x2, 0x991e24 x2 - it seeds the staging pair.
- **M196** 0x94d448: 653 mentions = 466 scaled `[reg*4+disp]` + 185 `[reg+disp]` + 2 other. 365 scaled sites take
  their index from `add reg,C` after a >=3-op 2095-fold of the SAME register, so the address is
  0x94d448 + 8380*S + 4*C - a block field at +0x344 (+4*C), not an array element. 297 scaled tests, ALL `test`
  (0 cmp), 29 operands, widest 5 bits, none an address candidate; 139 loads, 0 dereferenced (125 arithmetic/compare,
  14 pushed). RMW quad verbatim at 0x5553e1/e7/ed/f3 (`mov edx,[edi+0x94d448] / and edx,0xfffdfbff / or edx,0x840 /
  mov [edi+0x94d448],edx`). RETRACTS M190's "the carriers 0x55540a/0x55580f store ADDRESSES": they follow
  `or eax,0x20000` / `and ah,0xdf` on the flag word, and the lea at 0x5553d2 is the store-through alias of the store
  at 0x5553df. Live: 0 of 33 dwords at +4*i and 0 of 33 fields at +8380*fac lie in 0x400000-0x7fffffe (0,
  0x80008118 x6, 0xffffffff x8, small ints).
Pitfalls: a scaled-4 displacement census is NOT an array census - attribute the index register's def chain;
classify a bit-field test by MNEMONIC + popcount, never by operand magnitude; data globals are 6 hex digits.

## Session 178 (2026-11-01) — M197-M200: the proposal composer, the diplomacy key pool, the tag engine, the row writers

Static-only fire, NO box time: one census script, one evidence file.
`python3 scripts/m197_m200_proposal.py > evidence/m197_m200_proposal.txt` (23,988 B, rc 0) ->
`SUMMARY M197=PASS M198=PASS M199=PASS M200=PASS (15/15 gates)` (evidence/m197_m200_proposal.txt:290; every
number below is cited to a line of that file); `--probe` prints the same lines
without verdicts. Two earlier invocations died on MY instrument, not the game: `for s in post` iterated
(pc,text) tuples -> TypeError; and I first gated M198a on an 0xFFFFFFFF terminator at the last KEY's end,
but the pool interleaves 18 spaced message lines, so the walk must accept multi-word entries - the fix
RAISED the floor (>=25 keys -> >=200), it did not lower it.

**M197** FUN_00544530 (1502 insns) has EXACTLY ONE call site: `call 0x544530` at 0x545c99 in FUN_00545c50,
and the operand text "544530" occurs 1x in 790,695 instructions (:2-3). Guarded `[ebp+0x10]==0` /
`jne 0x545cd4`, 2 args (esi=[ebp+8], ebx=[ebp+0xc] - the faction pair), return cleaned `add esp,0x8` +
`test eax,eax` (:5). Of the 8 stores to ds:0x920700, 7 are inside it and its own body says 6 are the
constant 0 while 1 is `FUN_005f1394()`'s return; the only immediate store in the image is 0xc at 0x54ec5c
(:8). It calls FUN_005f1394 6x and assigns the return to 5 distinct globals {0x9206fc,700,728,748,77c},
all cleared in its first 112 bytes (:10). RETRACTS M195's "ZERO string literals": the body names 3 string
globals whose bytes read PROPOSALMENU / REJWARALREADY / NOCOMMLINK (:12). **M198** those 3 sit in a string
pool at 0x690160..0x69107c bounded by 0xFFFFFFFF at BOTH ends: 329 entries = 311 single-word KEYS + 18
spaced message lines, and 257 of the 311 keys have code references, printed as key->function (:13-16, :275).
**M199** the substitution engine is FUN_00625b20: _strstr for the needle whose byte at 0x69911c is '$',
switch on the char after it over 5 cases (closer 0x699138 = '>'; 'H' compares 4 bytes at 0x699130 =
'$HEX'), index `&DAT_0099a01c + n*0x100`, metadata A[]@0x999fcc / B[]@0x999ff4 / 0x999fa4, then copy the
Nth ':'-separated segment of the slot (:277-278). FUN_005808b0 COMPOSES `$<`+{M,F,N}+{1,2}+`:`+arg+`>`
from the record dwords +0x2fc/+0x300 (the bytes at 0x692144..0x692160, :280); FUN_00580a60 PARSES that
head back into 0x99aa1c (F->1, N->2, else 0) and 0x99aa20 (2nd char=='2') - inverse-consistent, so the
staging pair IS a parsed tag head (:282). **M200** FUN_00631afb / FUN_00632cad are row WRITERS through
the handle DAT_0099d020 (vtable +0x10/+0x18/+0x38/+0x58/+0x60; alloc FUN_005be090, free FUN_0064a7f0,
append FUN_0064b9e0, :286): 0 `0x25` immediates, 0 printf-family calls, 0 references to FUN_00625b20, and
each copies the buffer it is handed VERBATIM - RETRACTS M194's "the formatters" (:287); its 16-byte
memcmp keys 0x67bd20/0x67bd30 are GUIDs, not table names (:288). (Pitfalls written to the skill,
`references/static-store-census.md` §12: Ghidra renders a referenced literal as a named `s_NAME_…` symbol, so a `"`
grep finds ZERO strings in a function that references three; a string pool is 4-aligned, NUL-padded and INTERLEAVES
keys with message lines - walk it by "the longest padded entry ENDING at va", never by a fixed stride.)

## Session 179 (2026-11-01) — CAP TRIAGE ONLY: NEXT_PROMPT.md 15,496 -> 14,052 BYTES (split, never shave)

**No milestone this fire.** `python3 scripts/evidence.py budget` opened the fire with NEXT_PROMPT.md at 15,496
BYTES, over the kickoff's 15,300 cap-triage trigger: s178 had closed at the gate-side 15,500 target, which is
the WRONG target (it consumed a whole fire). The skill's two cap bullets now say close at <=15,300 BYTES.

- The split: `python3 scratch/s179_split.py` moved footing lines 60-82 — the s178 (M197-M200) block and the
  s175-s177 (M188-M196) block, 23 lines / 2,406 chars — VERBATIM into `docs/pick-archive.md` (16,797 -> 19,671
  chars) under a header naming the registry rows and the four census outputs, and left a 7-line archived pointer
  in their place. The script asserts the moved blob is byte-identically present in the archive and prints
  `moved_lines=23 moved_chars=2406 verbatim_in_archive=True lost=0` on rc 0 — no line was shaved.
- Result after the header/wording edits: `python3 scripts/evidence.py budget` prints NEXT_PROMPT.md **14,052**
  (= `wc -c`; the file is 13,988 CHARS, 64 less) — 1,248 B under the 15,300 trigger, 1,948 B under the gate's
  16,000 FAIL. `python3 scripts/evidence.py prune`: "uncited images older than 7d: 0 (0 KB)" — nothing to apply;
  evidence/ 28.2 MB (warn, FAIL 30).
- **Instrument-vs-prose fix found on the way:** `cmd_budget` compares `os.path.getsize` (BYTES) while its column
  header said `chars` and its `DOC_BUDGETS` comment said "characters" — the skill even asserted "budget counts
  chars, `wc -c` disagrees", which is false (budget == wc -c, verified 14,018 = 14,018). Header now prints
  `bytes`, the comment says BYTES, `docs/EVIDENCE.md` and both skill bullets say BYTES. Thresholds unchanged, so
  the byte reading is the stricter (safer) one.
- Nothing was measured: no census, no box time, the Wine process untouched, so the s174e BOX STATE IS STILL
  UNVERIFIED and M181 is still a LEAD with no positive control. All four picks are untouched and re-queued
  verbatim (the "Pick from:" bullet was not moved).
- Docs: header + CLOSING ORDER re-aimed at 15,300; live skill patched (2 bullets) and `skill/` rsynced. NAMED.md
  untouched — no address changed meaning this fire.

## Session 180 (2026-11-01) — M201-M204 all PASS: FUN_005f1394 IS the OK/CANCEL DIALOG RUNNER; its return is a result code; $-tags resolve by FIRST DIGIT; the key pool is an emitter list

One static instrument: `scripts/m201_m204_dialog.py` -> `evidence/m201_m204_dialog.txt`. Acceptance
`python3 scripts/m201_m204_dialog.py` -> `SUMMARY M201=PASS M202=PASS M203=PASS M204=PASS (15/15 gates)`,
rc 0. Invocation 1 was 12/15 on 3 INSTRUMENT bugs (a slot pattern built with `str(off)` so `+ 0x30` and
`+ 0xdc` matched nothing; a 40-BYTE lookahead for the +0xdc dispatch when the bool prologue is ~45; a
char-literal regex that also caught the `'\0'` escape) — fixed, every threshold kept.
- M201 ctor FUN_00405ef0 stores `mov [eax],0x67164c` 0x405f31 + `mov [ecx+0x444],0x671644` 0x405f3a (the
  CPane subobject, after ctors 0x5ee350 and 0x5f6b8c(this+0x3230)); 99 ctor sites in 90 fns, 53 of the 67
  pump callers construct it. The dword 0x5f1394 appears 0 times as data image-wide (no vtable or switch
  holds it): 94 direct calls, ONE exit `ret 0x8` at 0x5f3f58, 90/94 sites load ECX from the caller's own
  frame. The pump is the only reader of 0x698e40 'OK', 0x698e44 'OK', 0x698e48 'Cancel', 0x698e50 'OK' (1
  site each, pool alternates). +0xdc is dispatched twice, on *this and on *[this+0x285].
- M202 domain {0,-1,[this+0x290],pass-through}: 0 `mov eax,imm` in 11,207 B, 5 `xor eax,eax`, 2
  `or eax,0xffffffff`, `mov eax,ds:0x698d0c` 0x5f3f38 (that dword IS 0xffffffff; 1 reader image-wide), and
  the lone `[reg+0xa40]` read 0x5f3f45 with 0 stores — the pump reports a result, never computes one.
  arg2 IS A CALLBACK: [ebp+0xc] at 2 sites (0x5f3d87, 0x5f3dcb), both feeding a +0xdc dispatch, and
  vtable+0xdc FUN_005ce5bd (`ret 0xc`) does `cmp [ebp+0xc],0` 0x5ce6bd + `call dword ptr [ebp+0xc]`
  0x5ce6c3. 17/94 sites pass a code pointer (16x 0x530d70, 1x 0x530db0): unnamed islands in the
  0x530d45-0x530df0 gap that read ds:0x920434, then ds:0x991588, set ds:0x920790=1 (its only 4 stores),
  call FUN_00519a20, clear it, return 1/0. All 6 composer sites store the return into a selector global
  within 4 insns; 0x920700 = 31 sites in 4 fns, tested {4,6,8,9,d}. **M197's "chooser" is RETRACTED — it
  is a dialog RESULT CODE, not a mode.**
- M203 FUN_0062898e is a first-DIGIT scanner (61 B, 0 callees, only '0'/'9' bounds + the NUL test), 5/5
  sites inside FUN_00625b20. $H: strncmp 4 vs 0x699130 '$HEX' -> `__itoa([0x999fa4][n])`; else digit ->
  slot text 0x99a01c+n*0x100. $L's exception is 0x69913c '$LINK<' (strncmp 6); $N gotos
  switchD_00625bb6_caseD_4e, the same tail as the unnamed default. Only returns: 0xe x6 (behind 8
  `9 < local_1c` guards) and uVar2 = 3 (null args).
- M204 313 key sites / 255 keys / 29 referrers, ALL inside 0x5316b0..0x54f1d0; FUN_00546800 owns 111 sites
  / 97 keys; 313/313 are `push <key VA>`; sinks FUN_00626a17 x149, FUN_0064b9e0 x76, FUN_00405220 x33 =
  258. Only 11 of 29 referrers call the pump and 56 of 67 pump callers name no key; the paths meet only as
  0x530d70 -> FUN_00519a20 -> FUN_00546800.
- Pitfall: Ghidra prints small vtable offsets as `+ 4`/`+ 8` and larger as `+ 0x15c` — a pattern must
  accept BOTH forms or it silently matches nothing. No box time: s174e state still unverified, M181 still
  has no positive control.

## Session 181 (2026-11-02) — M205-M208 all PASS: who writes the dialog RESULT field; [this+0x285] is a child-dialog link slot; FUN_00546800's three switches; ds:0x997528 is a write-only staging buffer drained by FUN_005f0583

Acceptance: `python3 scripts/m205_m208_fields.py` -> `SUMMARY M205=PASS M206=PASS M207=PASS M208=PASS (14/14 gates)`, rc 0, `evidence/m205_m208_fields.txt` (14,015 B) — GREEN ON THE FIRST ACCEPTANCE INVOCATION. Two `--probe` runs first fixed five gate expectations that were INSTRUMENT/typo errors, not thresholds: `[ebp-0x30]` has 3 stores in the pump (0x5f13d8 inits it to 0), the +0xa40 census spans 30 functions not 31, the pump's +0xa14 sites are 10 loads + 1 store once the classifier is DIRECTION-aware (`mov ecx,[edx+0xa14]` is a LOAD), the second +0xe0 dispatch is 0x5f5893 not 0x5f5890, and `ds:0x9939c4,edx` is at 0x5ce60e not 0x5ce60b. No threshold, floor or check was weakened.

**M205** the pump returns `[this+0xa40]` = Ghidra `this[0x290]`: 0x5f3f3f `mov eax,[ebp-0x394]` -> 0x5f3f45 `mov eax,[eax+0xa40]`, reached only when `[ebp-0x30]==0` (0x5f3f1a/1e); [ebp-0x394] has exactly 1 store in 11,207 B (0x5f13b2 = entry ECX). The other two legs both give -1: `or eax,0xffffffff` (0x5f3f33) behind `[this+0x30a8]&0x40`, else `mov eax,ds:0x698d0c` (0x5f3f38; that dword IS 0xffffffff). Writer census: 56 store-shaped +0xa40 sites in 30 functions; exactly TWO are dialog vmethods — FUN_005f5759 (slots +0xa8,+0x228; 4 stores: 0, `[node+[node+8]+0xec]`, the `call 0x5fdcf7` result, 0xffffffff) and FUN_005f58fa (+0x64,+0x1e4; 3 stores) — each with **0 direct call sites image-wide**. FUN_005f5759 also keeps its ARG in a second slot [this+0x3100] (0x5f584a) testing sentinels 0xfffffffe/0xffffffff. Two 51-B forwarders FUN_005ce4a9/FUN_005ce4dc write `[this+0x43c]+0xa40` / `[this+0x440]+0xa40` (2 call sites each, both in FUN_005ff462/FUN_00603fec); the base ctor FUN_005ee350 zeroes the field at 0x5ee7a5 (dialog ctor calls it with ecx=this, 0x405f14). WHO dispatches slot +0xa8 stays OPEN: 29 `call [reg+0xa8]` sites in 17 fns, 0 of them in a pump-caller or ctor-caller function.

**M206** [this+0x285] = byte +0xa14: 10 loads + 1 store (0x5f1561, value 0) in the pump. 0x5f3d7c `cmp [edx+0xa14],0` selects `call [[this+0xa14]-vtable+0xdc]` (0x5f3dbe) over `call [*this+0xdc]` (0x5f3df6) with IDENTICAL args (0, the pump's arg2 callback, boolean of `[this+0x30a8]&0x200000`); the result is the [ebp-0x30] that picks the return leg. FUN_005f5759 dispatches +0xe0 the same way (0x5f5883 / 0x5f5893), so the child shares the class's vtable shape. The field is one slot of a 7-pointer link block 0xa14..0xa2c spliced in triples by FUN_005ee350 (9 stores), FUN_005eede6 (9), FUN_005f6b8c (6); the latter seeds it from the GLOBAL ds:0x997850 (0x5f6bf2-0x5f6bf7) and installs vtable 0x671d94 (0x5f6bdc) + 0x671d8c at +0x444 (0x5f6be5) on the object it constructs. The +0xdc target FUN_005ce5bd is a MODAL LOOP over a 4-deep dialog stack: guard `cmp ds:0x9939c8,4` (0x5ce5cd), push `[depth*4+0x992db8]`/`[depth*4+0x992dc8]`, current = ds:0x9939c4 (0x5ce60e), suspend the previous modal via slot +0x10, activate via +0x4, pump events via +0xe4, `call [ebp+0xc]` (the callback), close via +0xe0, `ret 0xc`, 1 direct call site (FUN_004413b0 @0x4413cf).

**M207** FUN_00546800 (34,550 B): THREE jump tables, 12/5/8 entries at 0x54eef8/0x54ef14/0x54ef34, all 19 targets inside the function; guards `cmp eax,0x6; ja 0x54a3cf` (arg2), `cmp ebx,0xa` + a BYTE-PERMUTATION table at 0x54ef28, and `cmp eax,0x7; ja` on the return of `call 0x542ea0` — the last reached only when ds:0x920434 != 0 and ds:0x985ae8 bit 0x800 is clear (0x54ead2/0x54eae0). Its args are the canonical faction-block fold (shl 6 / add / lea [s+e*2] / shl 4 / sub / add edi / shl 2) feeding `test [eax+0x94d448],0x8000000`; it builds a dialog on its own 0x5534-byte frame (`lea ecx,[ebp-0x5534]` -> `call 0x405ef0`) and calls the pump 0 times. Of 162 .rdata pushes, 111 name single-word keys = 109 distinct addresses = **97 distinct texts** (M204's 97 is the TEXT count), + 50 message lines + 1 SEH cookie. Partitioned by switch region: 29 key sites before the first target (prologue), 68 in the region starting at 0x54ad65, and the 8 result-code regions hold 0-3 each (7 total) — the result code picks a SHORT branch, the vocabulary lives elsewhere. 5 call sites: FUN_00519a20, FUN_0054f1d0, FUN_005525d0, FUN_005551e0 x2.

**M208** ds:0x997528: 105 references = 103 `push <addr>` + 1 absolute byte clear (0x5f58de, in FUN_005f58bd, which strlen's its arg first and returns 3 when len > 0xc) + 1 store of the address into a stack arg slot; **ZERO absolute loads**. 79/103 pushes feed FUN_005f0583 (3,601 B, 99 call sites): it substitutes 0x997528 for a null text arg (0x5f06f8-0x5f06fe), runs it through the tag engine 0x625b20 (0x5f0779), writes [this+0x2350] 7 times with 1/2/4/0x10 from arg5 bits, and calls the attach FUN_005eede6 (0x5f05bf) unless arg5 & 0x80. FUN_00626a17 (M204's 149-site "sink") is a 38-B thunk whose only call is to the writer FUN_00626b19 with (buffer, key, -1, 0, ...); FUN_0064b9e0 is the SWAR strlen (0x7efefeff/0x81010100, reads [esp+0x4], never touches the buffer) — M204's "76-site sink" is a MEASUREMENT of the key text, not an emit.

**Pitfalls recorded.** (1) A store census keyed on MNEMONIC alone is direction-blind: `mov reg,[reg+disp]` is a load. Classify by which operand carries the displacement. (2) A displacement is shared by unrelated structs — scope a field census to a class by testing whether the containing function is a member of that class's vtable (here 56 stores / 30 functions collapse to 2 class functions). (3) "N distinct keys" must say WHICH identity: 111 sites / 109 addresses / 97 texts. (4) `call ebx`/`call ecx` indirect sites break any `int(ops[1],16)` census — filter `startswith("0x")`.

No box time again: the s174e box state is STILL unverified and M181 is STILL a LEAD (no positive control).

## Session 182 (2026-11-02) — M209-M212 all PASS: who dispatches dialog slot +0xa8; the dialog stack = two parallel arrays (arg3 write-only); +0xe4 is a bool; FUN_00542ea0 wraps the pump; -9999 is FUN_00496ad0's sentinel

Instrument `scripts/m209_m212_dispatch.py`: whole-image disasm + image bytes + a vtable model (bases = the imm32
of `mov dword ptr [reg+disp],imm`, extent = code-pointer dwords capped at the next base -> 188 bases). Acceptance
`python3 scripts/m209_m212_dispatch.py` -> `SUMMARY M209=PASS M210=PASS M211=PASS M212=PASS (18/18 gates)`, rc 0,
FIRST acceptance invocation; 3 `--probe` runs fixed 6 expectation errors (457/7 install split, 3 not 4
`[this+0x3c]` sites, INSTALLS displacement carries no `]`, read the guard off the call site's next 3 insns,
`cmp eax,esi` is a REG compare, arg_of must start one insn before the call); no threshold weakened.
`evidence/m209_m212_dispatch.txt` (5,859 B). Zero box time. Semantics: NAMED.md `## M209-M212`.

- **M209** +0xa8 = 33 implementations over 188 vtables; exactly 3 map it to FUN_005f5759 (0x67164c 390 / 0x6717cc
70 / 0x6728c0 4 installs, 70 ctor fns, 457 at `[ebp-disp]` — dialogs are stack locals). Dispatchers: FUN_005f6aa3
(the family's own +0x4c, 5 vtables, 0 direct calls) via FUN_005e7917 (24-B list walk from `[obj+8]-1`, publishes
item[+0x14]/item[+0x10], -1 on failure) and FUN_0043fee0 (+0xa8 of 0x6738e4, 0 direct calls) via ds:0x9977f0 (9
refs, 2 stores, both inside the pump at 0x5f3d70/0x5f3e02). RETRACTED: FUN_0043a4e0 (+0x60 of 0x673498 ->
FUN_004394e0) and the -0xa14 thunks (0x6723f4/0x672bfc/0x673444 installed at `[reg+0xa14]`) — 0 of 13 outer
targets is FUN_005f5759. FUN_004bb900 = +0xa8 of 8 vtables, forwards to [this+0x3c], 0x14 if null. Args: 19
immediates (5x -1, 1x -2) + 10 registers.
- **M210** dialogs[] 0x992db8 6 refs (4 stores / 2 loads, 3 fns); arg3[] 0x992dc8 3 stores, 0 LOADS = write-only;
current 0x9939c4 22/3, depth 0x9939c8 21/3, writers only FUN_005ce5bd + FUN_005ce6ff. +0xe4: 2 dispatch sites;
dialog family = FUN_005f6056 `return ds:0x997770 == 0`, sibling = FUN_004060d0 `return 1`; ds:0x997770 3 refs = 2
stores (0x5f3e6e = 0, 0x5f6081 = 1) + 1 read; the runner gates its arg2 callback on it (`test eax,eax; je
0x5ce6f6`). M206's "+0xe4 = events" RETRACTED.
- **M211** FUN_00542ea0 (1456 B, 1 caller = FUN_00546800 at 0x54eaeb) calls FUN_00405ef0 (0x542ecb) and the pump
ONCE (0x54322b), returns its eax; table 0x54ef34 = 8 entries (9th dword 0x90909090), guard `add esp,0x8; cmp
eax,0x7; ja 0x54ec82`; cases 0..7 -> FUN_005306b0 / FUN_00545c50 (1,2) / FUN_00626a17 (key 0x690fc0, stub
0x530d70) / FUN_0053fce0 / FUN_00541bb0 / FUN_00542810 / ds:0x920700=0xc + ds:0x92077c=1 then FUN_00545c50. M207's
"0 pump calls" is direct-only.
- **M212** -9999 (0xffffd8f1) 14 sites / 10 fns (3 cmp, 11 mov): 0x4976ce init + 0x4976f9 read-back inside
FUN_00496ad0, which has 1 caller (FUN_00417ee0 at 0x41860a `call 0x496ad0; mov edi,eax`) and its 2 tests read
edi; 0 pump sites test -9999 and 0 of the 56 +0xa40 stores write it. Pump's 94 consumers: 49 mov / 22 test
eax,eax / 4 cmp-imm (0x8 x2, 0x3, 0x1) / 6 cmp-reg / 5 pop / 3 push / 2 lea / 2 jmp / 1 dec; 1 tests -1 within 12
insns.
OPEN: s174e box state unverified; M181 still a LEAD (no positive control).

## Session 183 (2026-11-02) — M213-M216 all PASS: point-in-rect hotspots; the dialog's +0x4c is a CLICK DISPATCHER over the list at this+0x3098; the 0xb4c row class and its label buffer; 0x6738e4 and the modal handle's readers

Acceptance `python3 scripts/m213_m216_hotspot.py` -> `SUMMARY M213=PASS M214=PASS M215=PASS M216=PASS (17/17 gates)`, rc 0, `evidence/m213_m216_hotspot.txt` (8,352 B). Invocation #1 was 15/17 on two EXPECTATION errors of mine, not data: my store census demanded `[` in the destination operand, so it missed the BARE no-`ptr` forms `mov ds:0x9977f0,eax` / `mov ds:0x9978ac,eax` (a3) — ds:0x9977f0 has 2 stores not 1, and each layout triple has 1 writer not 0 — and I asserted one writer function where index.csv resolves 9 distinct one-store functions. 3 `--probe` runs fixed 5 earlier ones (half-open window = 53 insns; read publish offsets off the SOURCE operand; FUN_00403a80's stores are mov/add/mov triples and FUN_00478080 calls it 4x not 3x; a `call dword ptr ds:imm` target and a pc outside any indexed function both crash an `int()`/`IDXMAP[]` census; a scaled `[X+idx*4+0xb40]` store's last field is disp+8, not disp+4). No threshold weakened. Zero box time.

- **M213** FUN_005e75a0 (29 insns, 0 callees) = POINT-IN-RECT over a 16-B {l,t,r,b} box, half-open: 4 cmp at +0/4/8/c, 4 `xor eax,eax`, 1 `mov eax,1`, 0 stores, bare `ret`. FUN_005e7917 = reverse scan of 24-B items (count `[obj+8]`, start count-1, 3 `imul ,0x18`, base `[obj+0]`) publishing item[+0x14]->param_3 / item[+0x10]->param_4, `or eax,-1` on no match, `ret 0x10`: HIGHEST hit wins (last drawn). 61 sites/25 fns vs 44/43. FUN_00478080 (143 insns, 0 direct call sites) builds one stack rect via FUN_00403a40 + 4x FUN_00403a80 and dispatches +0xa8 4x with 0/1/2/3 = the ZONE NUMBER.
- **M214** FUN_005f6aa3 = +0x4c of 5 vtables (466 installs), 0 direct calls; the insn before `call 0x5e7917` is `add ecx,0x3098` — the hotspot list is a MEMBER AT this+0x3098, not the object (Ghidra's `in_ECX` reuse reads it wrong); gate `cmp [ebp-0x4],0` = item[+0x14]==0, arg = item[+0x10], `call [eax+0xa8]` self-dispatch, `ret 0x8` (x,y). Lists are reusable: 44 scan sites -> 19 distinct this-displacements (34 sites) + global 0x8a9108 + 9 stack locals; `[reg+0x3098/9c/a0]` = 1/0/0. All 12 image-wide `call [reg+0x4c]` sites belong to OTHER hierarchies (3 inside +0x4c vmethods of 0x676fc0/0x673ca8-family/0x67275c, 2 inside +0x40/+0x58 vmethods, 7 in non-vmethods, 2 not in any indexed fn) -> the family's +0x4c dispatcher is OPEN.
- **M215** row 0xb4c verified twice (`add ecx,0xaac`/`0x15f8` before 2 `call 0x5faec0`; top store `[X+idx*4+0xb40]`, idx 0..2, ends 0xb4c). Ctor installs 0x67194c + subobject 0x671944 at [ecx+0x444], 20 stores; its 27-dword 0xae0..0xb48 block copies 9 stride-0xc triples 0x9978ac..0x99790c that are read 3x and written ONCE each by a bare `mov ds:imm,eax` in 9 distinct one-store fns FUN_0045a4d0..FUN_0045a650 (0x30 apart) = runtime setter state, not load-time data. FUN_005f9e85 (0 slots, 90 sites/23 fns) = labelled-control creator (id->[this+0xa78], malloc'd label->[this+0xa7c], rect = param_3..6, parent = param_7). Label census: 44 x the global scratch text buffer ds:0x997120 (4089 refs / 668 stores, ZERO indexed, 466 base-clears `mov byte ptr ds:0x997120,0x0`; 1425 of 3232 pushes hand it to the emitter FUN_0064b9e0), 15 NULL, 30 reg/field, 1 literal ("Create Session (Translate)" @0x69a7bc).
- **M216** 0x6738e4: 87 slots, 2 installs (0x43fa14, 0x43fc3e), +0xa8 = FUN_0043fee0 (1 slot, 0 direct calls); shares 75/87 slots with 0x6717cc, 73 with 0x671d94, 66 with 0x67164c, 70 with 0x67194c — every differing set contains 0x0/0x4c/0xa8. ds:0x9977f0 = 9 refs, 2 stores (0x5f3d70/0x5f3e02, both in the pump FUN_005f1394), 7 loads in 4 fns: the forwarder, FUN_005d69fa (current-object picker -> publishes ds:0x9939ac, returns the object's [+0xa8] DELEGATE, 3 callers dispatch +0x12c/+0x130/+0x134) and FUN_005f5a11 (0 slots, 0 direct calls; installed 3x as an immediate into [reg+0x2210/0x2224/0x2234] = a callback FIELD; dispatches +0xe0 on [handle+0xa14] or the handle, writes [handle+0xa40]).
OPEN: who dispatches +0x4c (box falsifier); who builds the this+0x3098 list (`call 0x5e7665` on `[esi+0x3098]` at 0x421ea0 in the dialog ctor FUN_00421da0); s174e box state unverified; M181 still a LEAD (no positive control).

## Session 184 (2026-11-02) — M217-M221 all PASS: the hotspot list is a 3-dword CONTAINER {array@+0, capacity@+4, count@+8} of 24-B items with an 8-member API; the dialog's list is a MEMBER allocated 10 items; the 9 row triples have THREE-store setters (M215's "one-store" RETRACTED); the +0x15c method installs the modal callback into three WRITE-ONLY fields; the 0x671d94 panel is 0x214c and its +0xa8 is a DETACH

`python3 scripts/m217_m221_panel.py` -> `SUMMARY M217=PASS M218=PASS M219=PASS M220=PASS M221=PASS (31/31 gates)`, rc 0; `evidence/m217_m221_panel.txt` 11,571 B; zero box time. Invocations #1 22/31 + crash, #2 28/31, #3 29/31, #4 green: every failure was an INSTRUMENT-definition bug, no threshold or claim was changed — (a) the store census counted `[ebp-0xNN]` frame spills as field writes (FUN_005e75e5 read 4 stores, disps [-4,0,4,8]); (b) `txt.index()` took the FIRST textual match and `mov [ecx+0x8],eax` occurs twice in the adder (count++ and item+8); (c) `census()`'s store half tests whether the DEST carries the token — for a stored VALUE (`mov [eax+0x2210],0x5f5a11`) the token is the SOURCE, so 3 refs reported 0 stores; (d) index.csv DOES name the SEH unwind stubs (`Unwind@00661ef2`), so "in the index" does not exclude them (+0x3098 has 4 clear sites, 2 of them stubs); (e) x87 `fsub qword ptr [reg+edx*1+0x10]` reuses the 24-B index form and inflated the item-field reader set.

M217 FUN_005e75e5 3 zero stores [0,4,8]; FUN_005e7678 `ret 0x4`, callees {0x5be090,0x5e760d}, `imul eax,eax,0x18`; FUN_005e774d `ret 0x18`, 7 stores [0,4,8,8,c,10,14], +0x14<-arg1 (gate), +0x10<-arg2 (payload), x=arg3, y=arg4, x1=x+arg5, y1=y+arg6, guard `cmp count,[+4]`/`jl` + `or eax,0xffffffff`; FUN_005e7917 publishes +0x14->arg3/+0x10->arg4; image-wide FUN_005e774d is the ONLY writer of +0x10/+0x14 (2 stores), readers 0x5e76be/861/8c7/917/9a3/a5f (all in 0x5e7300-0x5e7d00); FUN_005e78c7 removes by payload (32 sites) via FUN_005e77e7; FUN_005e7665 = 9 insns, callee 0x5e760d, 130 sites.
M218 clear receivers member=47 / stack=81 / loaded=2 over 21 distinct member displacements 0x10..0x402f0; 21 alloc sites, 13 immediate capacities 0x1..0x100; 32 add sites member=26 / loaded=6, gate immediates {0,1..8,0x45}; the +0x3098 list is cleared at 0x405fb3 (FUN_00405f60) + 0x421eaa (FUN_00421da0) + 2 unwind stubs, allocated 10 items at 0x5eff25 (FUN_005ef957), reset at 0x5ee5fe (FUN_005ee350), scanned at 0x5f6ac5 (FUN_005f6aa3), and has 0 add-sites: it is filled through a register-passed list pointer (6 add-sites take the list from a loaded value; FUN_00403b00 is one such wrapper).
M219 9 setters 42 B / 18 insns / 3 stores rel [0,4,8] / 1 site / 0 slots; 27 stores = 9 bare a3 + 18 `mov dword ptr ds:`; all 9 sites inside FUN_00459bb0 (1722 B, 450 insns, 1 site, 0 slots), each followed by `add esp,0xc`; 3 calls pass 0x774c38+0x2c*i (i 0..8, one entry each), 6 pass (0,0,0); both ranges above FILEMAP_END 0x6ed000; FUN_005fb1a5 = 0x67194c+0x30 reads the 0xae0..0xb48 groups on the 4-byte grid.
M220 FUN_005f3f5b = 0x6717cc+0x15c (95 slots, 70 installs), `cmp [ebp-0xf4],0x9` + `jmp [ecx*4+0x5f5731]` (10 targets, all inside); the only 3 refs to 0x5f5a11 are its stores to +0x2210/+0x2224/+0x2234; those disps have 2/1/1 refs image-wide, 0 loads, and 0 indirect calls carry any displacement in 0x21c0..0x2260; FUN_00406990 = +0x15c of 4 vtables (396 installs) calls it twice (0x406c24, 0x406f26); FUN_005f5a11 has 0 direct calls and 0 slots.
M221 0x671d94 = 87 slots / 275 installs, identical 74/87 to 0x6717cc, 63/87 to 0x67164c, 71/87 to the row 0x67194c; +0x4c = FUN_005f84ff (no click dispatcher), +0xa8 = FUN_005f90d7; ctor FUN_005f6b8c 605 B / 136 insns / 16 sites, callees {0x5faec0 x2, 0x5e3b80 x1}, 0x671d8c (3 slots, 268 installs) at +0x444, block stores 0xa14..0xaa0; size 0x214c uniform in FUN_00409e70 (3 panels) and FUN_004947c0 (4), highest ctor store 0x2148, row 2 ends 0x2144; FUN_005f90d7 stores 0xa38 x1 + 0xa2c x2, 0xa40 x0, 7 indirect calls, dispatches [edx+0xb8]; FUN_005f5759 stores 0xa40 x4, 0xa38/0xa2c x0, 3 indirect; FUN_00405ef0 embeds one panel at +0x3230 (site 0x405f29).
OPEN: who dispatches the dialog's +0x4c (box falsifier, unchanged); who calls FUN_005f5a11 if its 3 fields are write-only; who fills the dialog's +0x3098 list (the register-passed adders, e.g. FUN_00403b00, and their callers); what FUN_00459bb0 is (1 callsite, 0 slots) and who reads the 9 triples' table; s174e box state unverified; M181 still a LEAD.

## Session 186 (2026-11-01, M222-M226, static, zero box time)

`python3 scripts/m222_m226_rows.py` -> `SUMMARY M222=PASS M223=PASS M224=PASS M225=PASS M226=PASS (26/26 gates)`, rc 0; `evidence/m222_m226_rows.txt` 10,130 B. Invocations #1 crash (a gate unpacked a tuple), #2 10/14 + crash, #3 22/26, #4 25/26, #5 green — every failure an INSTRUMENT-definition bug: provenance resolved at the CALL pc instead of each push's own pc; `\[ebp(0x..)\]` missing the `\+`; a str-vs-int set comparison; a `0x774c|0x774d` filter that missed 0x774a80 and, widened, over-matched 39 region refs; expected counts read off the wrong probe window. No threshold, floor or claim direction was changed to get green.

M222 the adder's own body maps item+0x14=arg1, +0x10=arg2, +0=arg3, +4=arg4, +8=arg3+arg5, +0xc=arg4+arg6 (ret 0x18; only failure path count>=capacity -> -1, 0 allocator calls). FUN_00403b00 (75 B, ret 0xc) spills ecx to [ebp-0x4] and pushes (arg1, arg2, rect+0, rect+4, rect+8-rect+0, rect+0xc-rect+4): a (gate, payload, RECT) wrapper. 23 sites / 16 functions: 22 pass the container as their own ecx plus one of 8 member disps {a48:1, cc4:5, e40:1, 15e0:5, 28ac:4, 5994:3, 12758:2, 12764:1}, 1 forwards ecx bare (FUN_00403ad0). 0 wrapper sites and 0 direct add-sites carry +0x3098: the dialog's 10-item list is never appended. The +0x14 slot is an immediate at 4/23 sites (0,0,3,0x64) and a register/loaded value at 19/23; the +0x10 slot is an immediate at 19/23 with values {0,1,2,3,4,0xa,0xb} — 0xa/0xb lie outside M218's {0,1..8,0x45}. FUN_0041f310 = slot +0x30 of 0x672448, all 3 sites `mov ecx,0x6a9480`; 8 of the 15 sites of FUN_0040f830/004105b0/00411840/00415d10 pass the same immediate; FUN_004105b0's container is this+0x402f0.
M223 FUN_005f5a11: 0 direct calls, 0 vtable slots, and the dword 0x5f5a11 occurs in the image only as the imm32 of the 3 installing stores (hits 0x5f48bc/0x5f4915/0x5f4a76 = stores 0x5f48b6/0x5f490f/0x5f4a70 + 6). The 3 fields have 4 bracket refs, ALL stores (3 installs + FUN_00406990's zero loop), 0 reads, 0 lea-address-takes, 0 indirect calls with a disp in 0x21c0..0x2260. Its body reads ds:0x9977f0, gates [h+0x2350] against 1 and -1, reads 0x21d0/0x229c/0x30a8, dispatches +0x8/+0xe0: a method of the MODAL object. The window IS live through its other members: FUN_005f1394@0x5f1e33 calls FUN_0060c436 with ecx = obj+0x21d0 and arg1 = [obj+0x2350]; FUN_0060c436 passes this+0xb14 to FUN_00607eca, which does `sub ecx,0xa94` before `call 0x5e774d` (0x60820b) -> container = this+0x80 = obj+0x2250.

M224 FUN_00459bb0 (1722 B): 1 call site 0x45a755 (in FUN_0045a740, 56 B, 1 caller FUN_00580260), 0 slots. The 27 globals 0x9978ac..0x997914 are written by exactly 9 functions of 42 B (3 refs each), each called once and only from FUN_00459bb0 — M219's split CONFIRMED: 3 receive grid pointers, 6 receive (0,0,0). The grid = 0x774c38+0x2c*i (i=0..8): 24 pushes over 15 calls, per-entry counts [2,2,2,3,3,3,3,3,3]; its 99 dwords all read 0 and the block lies past the file image (ends 0x6ec8c0) = BSS. FUN_0041f450 (8250 B, 1 caller) references the 0x774xxx region 39 times and its 5 stores all go to [obj+0xb24]: 0x774c0c x4 (grid base - 0x2c) and 0x774a80 x1 (grid base - 0x18c = 9 entries); 9 other functions load [obj+0xb24].
M225 FUN_005f90d7 (slot +0xa8 of exactly 0x671d94) dispatches 7x: [reg+0xb8] x2 on the link neighbours it unlinks (2 `mov [eax+0xa2c],edx` relinks, `mov [eax+0xa38],0x0`, `mov [eax+0xa3c],0xffffffff`), [reg+0x5c] then [reg+0x1c], [reg+0xf0], and [reg+0x2144] x2 — the max vtable slot over 188 vtables is 0x178, so +0x2144 is the panel's own last FIELD: 54 sites, 17 writer functions, 7 reader/caller functions.
M226 FUN_005fb1a5 = row vtable 0x67194c slot +0x30 (4202 B, 1000 insns): 14 `add ecx,0x444` receiver switches to the CPane subobject, exactly 1 indirect call `call [edx+0x14]`, reads the groups as indexed arrays `[reg+reg*4+0xabc]`/`+0xac8` plus 0x98/0xa7c/0xa88/0xa8c, and calls the text/label emitters FUN_005dd09c x5 / FUN_005c153f x5 / FUN_005ca7c3 x4.
OPEN: who dispatches the dialog's +0x4c (box, unchanged); whether the dialog's +0x3098 list is dead or filled through a field-held pointer (the live container in that block is obj+0x2250, a DIFFERENT member); who calls FUN_005f5a11; what the 0x774xxx grid holds and who reads it via [obj+0xb24]; the 17 writers of the panel's +0x2144 callback; s174e box state unverified; M181 still a LEAD.

## Session 187 (2026-11-01, M227-M230, static; box re-verified, no box milestone)

`python3 scripts/m227_m230_mirrors.py > evidence/m227_m230_mirrors.txt` -> `SUMMARY M227=PASS M228=PASS M229=PASS M230=PASS (12/12 gates)`, rc 0, 10,083 B (`evidence/m227_m230_mirrors.txt:41`). Invocation #1 11/12: the FUN_0041f450 store census filtered `startswith("mov dword ptr [") and endswith("+0xb24]")`, which misses every store whose VALUE is the last token (`mov dword ptr [ebx+0xb24],0x774c0c`); fixed to `^mov dword ptr \[[a-z]+\+0xb24\],`. No threshold or claim changed. Box RE-VERIFIED (read, not poked): `sudo -n python3 scripts/smac_preflight.py` -> PASS on all 14 invariants (terran.exe 319926 TracerPid 0, year 2153, cur_player 3, mask 0xff08, 18 bases / 72 units, University Base (28,42) pend 0 head 2, 6 ours 0 actionable): the s174e "unverified" flag is CLOSED. M181 got no trigger this fire - still a LEAD, box time owed.

- **M227** 0x3098 = 18 insns: 8 MEMBER + 10 frame slots `[ebp-0x3098]`. In FUN_0058dfd0/FUN_0058e2b0 the slots ARE the members through a stack base: each stores PANEL vtable 0x671d94 at [ebp-0x3098], DIALOG vtable 0x6717cc at [ebp-0x62c8] and calls ctor FUN_00405ef0, so base = ebp-0x62c8, +0x3230 = ebp-0x3098 (panel, M221) and +0x3098 = ebp-0x3230 (THE LIST), where each frame does `lea ecx,[ebp-0x3230]` -> `call 0x5e7665`. All 8 member takes reach {call 0x5e7665 x4, jmp 0x5e7665 x1, call 0x5e764f x1, call 0x5e7678 x1, call 0x5e7917 x1}, 0 an appender: the dialog's 10-item list is allocated, cleared, reset, scanned and NEVER appended image-wide.
- **M228** +0x2144: 54 refs, 24 stores = 10 zero + 3 sentinel 0xffffffff + 11 register, 0 with a text-range immediate; provenance {frame-slot 8, .rdata 0x689f88 table load 1, 0x7543d8 table-slot lea 2}. Exactly 3 callers, 6 `cmp ,0x0`-guarded calls: FUN_005f86ad = 0x671d94+0x48, FUN_005f882f = +0x60, FUN_005f90d7 = +0xa8 - all panel vmethods. The 3 sentinel writers load first (4/1/1): read-and-invalidate.
- **M229** [obj+0xb24]: 25 refs = 12 stores in 6 fns + 12 loads in 5 fns + 1 `cmp ,0xffffffff`. **RETRACTS M224's "9 other functions load [obj+0xb24]" -> 5** (FUN_0042d2c0, 00488e80 x5, 004893e0 x2, 004894c0 x3, 00612c4c). 0 reference 0x774xxx; 1 load indexes the 0x2c-stride table at 0x7543d8 (index*44), 10 are pushed to callees. FUN_0041f450's 5 stores = {0x774c0c:4, 0x774a80:1}; grid file offset 0x374c38 > len(terran.exe) 0x2ed000 = BSS, 99 dwords 0. 0xb24 is a COLLISION: a page address for one owner, a slot index for the loaders' owner.
- **M230** FUN_00455c70 (88 B, 33 insns, 0 stores) is a trampoline: {0x5dbdc0:1, 0x5e3412:2}, each preceded by `mov ecx,[ebp+0x8]` (arg1 = the callee's this), injecting {0x109:3, 0x107, 0x106, 0x792a30, 0x0}; 15 sites in FUN_00459bb0 pass 11 distinct BSS buffers + 4 registers, 0 inside the grid. The 0x45a320..0x45a6e0 run = 21 functions, 9 pair publishers writing (0x99aa9c+4i, +0x24), i=0..8.
OPEN: who dispatches +0x4c (box); who calls FUN_005f5a11; what the 9 grid entries hold, who writes the 0x7543d8 table and the 0x99aa9c..0x99aae0 pairs; M181's control (box).

## Session 188 (2026-11-01, M231-M234, static + read-only /proc; box untouched, M181 still a lead)

`sudo -n python3 scripts/m231_m234_staging.py > evidence/m231_m234_staging.txt` -> rc 0, **17/17 gates PASS on one invocation**, 8,862 B. Invocations 1-4 gave no verdict (instrument bugs; no threshold, floor or check changed): a format string missing its `%`; `p_["dests"]` indexing a list with a string; a read-back that assumed 0x99aa9c+4i and 0x99aac0+4i were adjacent (they are 0x24 apart) and compared the wrong dword; a push list not truncated to the callee's own cleaned arg count, so FUN_00455c70's prologue pushes read as arguments; `pend` reset only at the tracked call, so the first trampoline call inherited 2 pushes from an earlier one.

TWO CLAIMS REWRITTEN FROM THE DATA, NOT LOOSENED: (1) M232's "4 stores name the region" is 39 stores - every one carries the region address in its SOURCE (FUN_0041f450 installing page bases into [ebx+0xaf0..0xb30]) and ZERO in its DESTINATION, so the grid has NO in-image writer; (2) M231's "FUN_0062d78d is not a vtable slot" is FALSE - it is slot +0x15c of 0x679f98, the very vtable FUN_0062d630 installs.

HEADLINES (all from the command above; semantics in NAMED.md). M231: publishers 0x45a320+0x30*i = 15 insns / 2 arg-loads / 2 stores / 0 callees, publishing ARG VALUES; 18 staging dwords, 18 writers, readers ONLY FUN_0062d630 (6 sites, installs 0x679f98/[+0x444]=0x679f90) and FUN_0062d78d (0 direct sites, 0 code refs); both copy the 18 dwords to [this+0xab8..0xafc]; live 3/9 pairs non-zero, every value a grid address. M232: 24 grid pushes over 9 calls (triples (0,3,6)/(1,4,7)/(2,5,8) to 6 functions, pairs (e,e+6) to 3); live entry {0, mapped ptr, 9, N, N, 0x14, N, 0x14, 0,0,0}, N=3 x6 / 0x43 x3; staging reads back exactly the pointers passed. M233: 3 writer sites (2 folded 0xd7 at +0x18/+0x1c in FUN_00459490's 89-iteration bound-0x59 loop, idx*0x2c; 1 count store to 0x7543d4), 13 base-takes (2 push / 5 add-adjustor / 6 lea), 0 to the base, 2 FUN_005aa310 sites storing &table[4*idx] into [edi+0x2144]; live count 11, entries 0..15 {0x15064c0-0x40*i mapped, 0, 9, 0,0,0, 0xd7, 0xd7, 0,0,0}. M234: FUN_005dbdc0 (ret 0x1c, 408 insns, 59 sites, 0 indirect) gates arg1=&0x792a30 via 0x5ca8d2 and reads [arg1+0x80]; FUN_005e3412 (ret 0x8, 91 insns, 0 callees, 14 sites) clamps args with `and reg,0xff` and rewrites 5 byte-matches of low(arg1) to low(arg2) over [this+4], length [this+0xc]*[this+0x14]>>2 truncating (2/11 buffers N*M %% 4 == 1); the 11 buffers are BSS records of the same grid shape.

PITFALLS: a staging pair spread over two arrays is not contiguous - read each slot; a callee's arg vector is its own `ret imm`/4 pushes counted back from the call; box time still owed (scratch/m181/pair.py never armed).

## Session 189 (2026-11-01, M235-M237 all PASS, static + read-only /proc; box untouched, M181 still a LEAD)

- **Acceptance:** `sudo -n python3 scripts/m235_m237_records.py > evidence/m235_m237_records.txt` ->
  `SUMMARY M235/M236/M237: 12/12 gates PASS`, rc 0, 7,433 B. Invocations #1 no output (no entrypoint),
  #2 crash (a `%`-format whose argument tuple was unparenthesised), #3 5/13, #5 8/12, #6 11/12, #7
  green. Every failure was an instrument-definition bug (objdump line shape, an absolute-operand blind
  spot, pairwise-instead-of-adjacent gaps, a cluster cursor off-by-one, a whole-window census reported
  as a three-field claim); NO threshold, floor or claim direction was weakened. Two PASS lines were
  RE-WORDED before merge (0x6a75a8 is an indexed table base, not a member disp; the ds:0x9965b8 loaders
  are candidates, not the proven filler). Laws -> skill §16.
- **M235** 0x679f98 = 88 slots (last +0x15c = FUN_0062d78d, next dword 0xfffffffc); 2 installs, both
  `[reg+0]`, by the class's TWO constructors FUN_0062d630 (the 18-dword copy-in, M231) + FUN_0062d764
  (41 B); 0 string literals in the slot functions, so the class is named structurally (72 slots
  implementation-identical to 0x6717cc, 71 to 0x671d94, 70 in all three, 15 unique); 87/88 slots have
  member-scale dispatchers (1920 sites), +0x0 none, +0x15c 28.
- **M236** the +8=9 the grid records / 0x7543d8 entries / 11 trampoline buffers carry has ONE emitter in
  790,695 insns: `mov byte ptr [ecx+0x8],0x9` @0x5dbbd1 in FUN_005dbb5f (33 insns, 0 calls) — a STAMPER
  that zeroes +4..+0x28 and publishes the record pointer into ds:0x9965b8 (3 stores / 3 loads with
  FUN_005dbbe6 + FUN_005dbdc0, M234). +4 is allocated elsewhere: 55 sites store a call result at [reg+4]
  within 8 insns of that call, 25 callees, top FUN_005be090 (13 sites / 13 functions). Live (pid 319926,
  TracerPid 0): the 9 grid +4 pointers form 2 block-strided clusters (6 x step 0x70, 3 x step 0x568),
  all mapped; table entries' +0 step -0x40 (count dword 11).
- **M237** fields 0x2210/0x2224/0x2234: 3 stores, 0 loads / call-through / lea / add, while their own
  block [0x21c0,0x2260) is busy (118 sites, 80 loads, +0x21d0 x62). All 3 installs in ONE installer
  FUN_005f3f5b (6102 B), same pointer thrice. Block-copy falsifier CLOSED: 108 `rep movs` image-wide, 4
  in 2 window-touching functions (FUN_005ee350, FUN_005eede6) naming only +0x21c0..+0x21d0. The handle
  FUN_005f5a11 gates on, ds:0x9977f0: 2 stores (both ABSOLUTE, both in FUN_005f1394), 7 loads, live 0x0
  — no modal object, so the triple cannot be read back without a dialog open.
- **LEAD (command, not a gate):** `awk -F'\t' 'index($0,"call   0x41a8f0")' scratch/m574/text.txt` -> 4
  callers of the GOVOPTIONS pack block: FUN_0041e160, FUN_0049af50, FUN_004a99e0, FUN_00512020 (the last
  also calls the tagged writer 0x6267a5 at 0x512069) — the trigger list for M181's falsifier.
- **Box time still owed:** terran.exe 319926 alive, TracerPid 0; 0 driver calls this fire.

## Session 190 (2026-11-01, B1 build rung — `sim/` exists; static, zero box time)

- `python3 scripts/track_mode.py` -> `MODE=BUILD analyse_since_build=3 last_build=B0 next_rung=B1`, so this fire
  built BUILD_SPINE.md rung B1 instead of taking a census pick. Branch `milestone/b1`; the three files were
  committed (`ed020bc`) before any probing, per the s188/s189 law.
- **Acceptance (green on the FIRST invocation, nothing weakened):**
  `python3 -m sim.selftest --map programs/maps/planet.MP --rules data/alpha.json` ->
  `PASS B1: 10/10 gates on planet.MP, planetx.MP`, rc 0 (`evidence/b1_selftest.txt:15-16`). Gates and numbers:
  sim's own .MP parser vs `scripts/decode_map.py` on the same bytes — parity tuples
  `(80,80,6400,143667,2739,128,5)` / `(128,128,16384,363525,2739,338,5)` (`:5`, `:9`); terrain-index set
  contiguous 0..15 with 0 out of range, both maps (`:6`, `:10`); owner nibble ∈ {0..7,0xf}, 0 invalid —
  planet `[3197,1,6,3,3,2,3,3,3182]`, planetx `[8192, …, 8192]` (`:7`, `:11`); cells with `+7==0xff` == header
  word 5 (3200/3200 and 8192/8192) (`:8`, `:12`); both dimensions checked (`:13`); 45 sections / 650 records,
  none empty (`:14`). `--map` self-expands to the sibling map (`:2`) because the rung demands 80×80 AND
  128×128 parity — an expansion, never a narrowing.
- **Cell structure MEASURED over both maps (corrects MAP_FORMAT.md):** cell+2 is **two nibbles** — high = a
  16-valued enum (all 16 used in both maps), low = the owner player index, `0xf` unowned, never 8..14.
  `+7 == 0xff` marks exactly the header's land-cell count in both maps. planetx.MP (fresh random map): every
  land cell is `0xf`, every sea cell `0x0`; planet.MP has 18 owned land tiles and 4 owned sea tiles.
- **LEAD (printed as `info`, not a gate):** cell+0 = `(cat<<5) | low5`, cat ∈ {0..6}, low5 ∈ {0,1,2,8,9,10,16,
  17,18} (9 values = two 3-valued fields, bit2 always 0); cats 1-6 are **100% land**, cat 0 is 59/3259 land
  (`evidence/b1_selftest.txt:3-4`). That is NOT the live `rec[0]&0xe0` category (FOOTING.md:119: ocean iff
  <0x60 would make cats 0-2 ocean, but 1 and 2 are all-land here), so the 22-byte file cell and the 44-byte
  live record at `*(0x92ae14)+(40y+(x>>1))*0x2c` are related by a transform nobody has named. Census pick.
- **Open:** terrain cardinality 16 is ASSUMED (a nibble cannot exceed 15, so gate 3 can only fail on GAPS);
  B2-B6 unbuilt; M181 box debt unpaid — a build fire builds (BUILD CADENCE), box debt is not a build rung.

## Session 191 (2026-11-01, M240 static — the `.MP` grid IS the live terrain-record array)

- **Footing.** Cursor said S190 B1 merged, no harness running (`ps`: no milestone.py/gdb/smac_play), tree
  clean; `track_mode.py` → `MODE=ANALYSE last_build=B1 next_rung=B2`, so this fire analysed and took the
  first ANALYSE pick (the 22-B cell → 44-B record transform). Zero box time; M181 debt still owed.
- **Acceptance.** `python3 scripts/m240_terrain_repack.py` → `PASS M240: 6/6 gates on planet.MP,
  planetx.MP`, rc 0 → `evidence/m240_terrain_repack.txt`. Invocation 1 crashed on a shard-filename slice
  bug (`n[-6:-3]` → `n[6:9]`); invocation 2 was 5/6 because G5 demanded each setter pattern occur ≥2×
  image-wide when it legitimately occurs ONCE per accessor — rewritten as per-function presence (stricter,
  not weaker); invocation 3 green. No gate, threshold or map was removed.
- **THE FINDING — no repack exists.** `FUN_00582260` (`shard_014.c:27347`) reads 0xaa4 → `&DAT_0092a378`,
  calls `FUN_00582000`, then reads `DAT_0092a38c*0x2c` bytes into `DAT_0092ae14` and `DAT_0092ada4` into
  `DAT_0092ae18`; neither body has a loop. `FUN_00582000` sets `DAT_00692184 = W/2`,
  `DAT_0092a38c = (W/2)*H`, allocates `count*0x2c` and `((W+4)/5 + 1)/2 * ((H+4)/5)`. The file grid IS the
  record array: 3,200 / 8,192 records of 44 B at `((W/2)*y + (x>>1))*0x2c`, one record per TWO map
  columns; the "22-byte cell" is half a record and only bytes 0..21 are the tile's fields. Accounting
  closes on both maps (gate G1): 15+2724+140800+128 = 143,667 and 15+2724+360448+338 = 363,525.
- **Two RETRACTIONS.** (1) record `+7` is the constant 0xff in all 11,392 records of both maps — B1's
  "land marker" and FOOTING.md's "+7 = owner byte" were reading a constant; at 22-byte granularity only
  the even cells carry it, which is exactly why its count equalled header word 5 (gate G4). (2) B1's
  category census mixed halves: record byte 22 (third byte of the mask copy at +20) has cat 0 in 100 % of
  records, so "cat 0 = 59/3259" was 3,200 artifacts plus 59 real tiles. Real split under the live rule
  (cat<3 = water, `shard_001.c:3515-3517`): planet.MP 1,826 water / 1,374 land, planetx.MP 5,143 / 3,049.
- **NEW, measured.** record `+16..+43` = 7 dwords, all seven equal in 3,145/3,200 (planet) and 8,192/8,192
  (planetx) records; each equals the record's own `+8` mask in 8,191/8,192 fresh records, and in planet.MP
  1,100/3,200 records it is a strict SUBSET of that mask (bit 5 cleared 814×, bit 20 344×, bit 30 101×).
  Direct offsets on `DAT_0092ae14` top out at 0xe (492 refs); record-pointer offsets top out at 0x10
  (one hit: `FUN_0051c750`, `shard_013.c:9451-9465`, kelp/forest growth spawn, which walks dword slots
  4..7). Header word 5 = `(W/2)*H` = the record count, unread by the loader; the 128/338 B "trailer" is
  the coarse region map `DAT_0092ae18`, sized from the dimensions by the loader itself.
- **Open:** what the seven mask copies mean and who fills them at map GENERATION (the load path only
  reads them in); record bytes 1, 3, 4-7 and 12-15 unnamed; `decode_map.py` and `sim/map.py` still split
  the grid into 22-byte cells — their B1 gates are position parity so they stay valid, but their "cells"
  are record halves; M181 box debt unpaid (terran.exe alive, TracerPid 0 — this fire took a static pick).
