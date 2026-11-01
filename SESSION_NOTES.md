

Older sessions: `docs/sessions/sessions-171-171.md` (7 sessions). Read it only when a question reaches back before session ## Session 171.

## Session 171 (cont. 9) — M114 CORRECTION: the "two rewritten tails" are a K STRADDLING ARTIFACT. The save is 1:1.

M114's claim is RETRACTED, caught 20 minutes later by checking the addresses before arming a watchpoint on them.
The two "rewrite zones" came from windows that STRADDLE a region boundary but were compared with ONE region's
`k`, so they diffed by construction:
- "block A tail 67,080..67,143" is below block B's base (67,852) and was diffed with block B's k=0x916C84 -> the
  238 "diffs" are block-A-vs-block-B content, and the 16-byte "stride" is just two different arrays lining up.
- "map header tail 81,408..82,100" straddles the grid start (82,088) and was diffed with the GRID's k=0x40925B0.

With per-region k the whole file is CLEAN:
```
block A      66,048..67,840   k=0x94D104   0 byte diffs
block B      67,852..79,328   k=0x916C84   0 byte diffs
map header   79,364..82,088   k=0x916D6C   2 byte diffs, both at the FIRST offset (79,364)
grid         82,088..172,200  k=0x40925B0  10 byte diffs, starting at the FIRST offset (82,088)
```
So the restore is **1:1 for every byte of the four big regions**, and the only divergences are a handful of bytes
at the START of the map header and the START of the grid, plus the 2 dwords already known in the 52-record array
(222,831 cleared, the poked field at 223,152 normalised). Confirmed live before arming anything: file 67,080 ->
0x95D70C holds 65,535 in BOTH the file and memory, i.e. no rewrite there.
LAW: a diff window must lie WHOLLY inside one region — a window across a boundary compared with one region's `k`
manufactures diffs that look exactly like real rewriting.

## Session 171 (cont. 10) — the two systemic fixes, as CODE (not advice)

1. **`scripts/save_diff.py` + `scripts/test_save_diff.py` (PASS 7/7)** — the region guard M114 needed. It derives
   regions from the poke anchors (`k = dest - off`), refuses any range that crosses a KNOWN section boundary
   (67,852 block B / 82,088 grid / 172,200 trailer / 172,291 next section / 222,783 52-records — each derived from
   an anchor plus its documented destination base, not a midpoint), and names the boundary it refused on.
   The two windows M114 merged are now REFUSED BY THE TOOL (`67072-69120` -> boundary 67,072; `81408-82100` ->
   the grid start), so the next session cannot repeat that comparison by accident.
2. **`scripts/m109_leg_census.py` teardown** — after the verdict it SIGTERM/SIGKILLs gdb by pid in a loop, then
   READS `TracerPid` from /proc and records it in the log header; if it is not 0 the harness exits **8** with the
   pid to kill. Two runs today (m111b3, m112a1) printed a verdict while gdb was still attached to the game.
3. **`scripts/m113_save_map.py` now verifies every anchor LOCALLY** (`local_1to1`, ±8 B by default): a hit proves
   the marker landed, the local comparison proves the mapping AROUND it is 1:1, which is the assumption every
   later diff leans on. Checked against the live box: 64,000->0x95CB04, 68,096->0x927684, 81,408->0x92AB6C (±64),
   82,432->0x40A67B0 (±64) and 174,000->0x986501 all return 0 local diffs — which independently confirms that
   M114's "map header tail" was the straddle artifact and nothing else.

## Session 171 (cont. 11) — M116 ACCEPTED (m116flag, PASS): the band-flag gate is a BYTE test, no OR sets 0x40, and "0 for all 8" is FALSE

`python3 scripts/m116_band_flag.py` (static over the image + live read of the 8 faction words) — **PASS**.

- **The gate is a byte test** at **0x5aaf7f**: `test BYTE PTR [esi+0x94d430],0x40`, inside **FUN_005aadf0+0x18f**
  (528 B), three instructions after `mov [esi+0x94d800],eax` (the FUN_005aab70 advance threshold is reloaded and
  stored, then the byte is tested). Exactly ONE such test exists in the image.
- **Nothing ORs 0x40 into it.** 170 instructions touch disp 0x94d430; the 17 `or` sites set 0x800000, 0x400000,
  0x1000000, 0x2000000, 0x4000000, 0x8000000, 0x10000000, 0x80000000, 0x40000000, 0x20000000, 0x200000 and 0x2 —
  **zero set 0x40**, so the bit can only arrive through a whole-dword store (18 sites).
- **"bit 0x40 = 0 for all 8 factions" is FALSE at the current state**: the eight words read
  0, **0xFFFFFFFF**, 0, 0, 0, 0, 0, 0 — bit 0x40 is SET for faction 1 and zero for the other seven.
- **But the interpretation is NOT established.** Faction 1's whole dword (and 0x94d434) is 0xFFFFFFFF, which is also
  the shape of a -1-filled/uninitialised record. So "the second ask runs for faction 1" is an INFERENCE. The
  controlled test is a poke: clear bit 0x40 for faction 1 and count hits at 0x5aaf88 (the taken branch).
NAMED's row is amended to say exactly that instead of "never ran".

## Session 171 (cont. 12) — M117 (m117g2): the byte test IS reached 17x a round and never taken; and M116's live half is RETRACTED (stride is DECIMAL)

`python3 scripts/m117_gate_take.py --tag m117g2 --turns 1 --relaunch --save m54b_clean.SAV` — two silent bps:
0x5aaf7f (the byte test, logs `esi` + the byte) and 0x5aaf88 (the taken branch), over one real turn on a clean load.

**17 test hits, 0 take hits, 0 gdb errors.** Per faction: 0 -> reached 0; 1 -> 2; 2 -> 4; 3 -> 1; 4 -> 3; 5 -> 3;
6 -> 3; 7 -> 1. So the gate is **live and reachable every round** (factions 1..7; faction 0 never) and **never
taken**: bit 0x40 is clear for all eight in this state, which MATCHES the original NAMED row — the M89 second ask is
inert here, and the open question is what SETS bit 0x40 (no `or` does; the 18 whole-dword stores are the candidates).

**M116's live half is RETRACTED — my own stride bug.** NAMED writes the faction stride as `f*8380`; that is
**DECIMAL 8,380 = 0x20BC**, and I read it as hex 0x8380 (33,664). The M116 table therefore sampled factions
0, 4, 8, 12... and its "0xFFFFFFFF for faction 1" was really 0x94d430 + 0x8380, a different structure. The corrected
read of the true stride gives **0, 0, 0x04000000, 0, 0, 0, 0x10000000, 0** — bit 0x40 clear everywhere. M116's
**static** half stands unchanged (the `test BYTE PTR [esi+0x94d430],0x40` at 0x5aaf7f in FUN_005aadf0+0x18f, and
the 17 `or` sites, none of which sets 0x40). `scripts/m116_band_flag.py` now carries the decimal stride and prints
"matches NAMED" when no faction has the bit.
Also: m117g1 was a WEDGE (`smac_play` rc=5, HUD byte-static 61 s) — the harness now reports a wedge as
**NO MEASUREMENT** instead of "the test was never reached", because those are different facts.

## Session 171 (cont. 13) — the M117 harness called a NEGATIVE RESULT a failure (exit 4)

`m117g2` exited **4** because its code was `rc = 0 if (not tests or takes) else 4` — i.e. "the gate was reached and
never taken" was encoded as a failure. That is the milestone's actual FINDING (17 test hits, 0 takes, bit 0x40 clear
for all eight), so the harness was mislabelling its own result. Fixed:
`rc = 0` whenever the site was reached (take or no take), `4` only when the site was never reached (inconclusive),
`5` for a wedge (no measurement), `8` for a dirty box. Same class as m111b3/m112a1's stale-gdb "success": an exit
code that does not mean what its reader will assume.

## Session 171 (cont. 14) — M118 ACCEPTED (m118flag, PASS): bit 0x40 has NO setter and no save carries it — the second ask is inert BY CONSTRUCTION

`python3 scripts/m118_flag_never_set.py` — four independent checks, no box time:

- **A** exactly one `test BYTE PTR [..+0x94d430],0x40` in the image: **0x5aaf7f** (FUN_005aadf0+0x18f, take 0x5aaf88).
- **B** the 17 dword `or` sites at that displacement set 0x800000..0x80000000 and 0x2 — **none sets 0x40**.
- **C** the byte-bit setters are REGISTER ops (`or al,0x40`), which a dword-immediate scan cannot see: 22 such sites,
  and exactly ONE (0x4dc226) reaches a flag store — 0x4dc296 — but that store takes `eax` **reloaded from the flag**
  and masked `0xfc3fffff`, so the or'd bit never reaches the source; the derived value goes to `ds:0x99aa38` and
  **0 instructions move it back** into a +0x94d430 slot. The block is a bit TRANSLATION (source bit 0x800000 ->
  derived bit 0x40), not a setter.
- **D** bit 0x40 is clear for all 8 factions in **all 12 saves** on disk (m54b_clean + 8 autosaves + the three pokes)
  — and block A is restored 1:1 (M114), so a save carrying the bit would set it.

**Verdict: the M89 second ask cannot fire on this build and this save version.** M117's "inert on this state" is
strengthened to "inert by construction" — while the branch stays live and reachable (17 hits a turn).
Lesson recorded in the skill: a byte-field bit test/set is `test BYTE PTR [x],0x40` / `or al,0x40`; scanning only
`or DWORD PTR [disp],imm` misses every real setter (I nearly concluded "no setter" from exactly that gap).

## Session 171 (cont. 15) — M119-M123, five field questions settled from the static image (all PASS, zero box time)

`python3 scripts/field_census.py` (evidence/fields_m119_m123.log) — SUMMARY stride=PASS bit5=PASS readonly=PASS
copy=PASS dual=PASS.

- **M119 stride conflict RESOLVED.** The array at 0x984d38 is addressed with **0x30 (48 B)** at all 52 indexed sites:
  45 via `lea X,[v+v*2]; shl X,4` and 7 via `imul X,0x30`; **0 standalone `shl 4`** on a bare index. M67's "conflict"
  was a misread: the ×16 in the listing is `shl 4` applied to 3v — the tail of the ×48 computation, not a second stride.
- **M120 bit 0x20 at 0x531782 NAMED.** `test BYTE PTR [eax*4+0x94d448],0x1` at 0x531778, `je 0x5317a2` at 0x531780,
  then `or BYTE PTR [ebx+0x98adb8],0x20`: the entity-status bit is set **iff the faction-block dword at
  0x94d448+inner*4 has bit 0**. The index is `esi*2095 + edi` — 2095 dwords = 8,380 B, so the "array" is the faction
  block with the stride folded in (a second independent confirmation of 8,380 after M117).
- **M121 ds:0x98adee is READ-ONLY.** 7 `movsx` readers (0x4e499d, 0x4eeb35, 0x4f948c, 0x51ff61, 0x5a9e06, 0x5a9e5f,
  0x5aa1a6), **0 writers of any width**, and no access to the enclosing dwords (0x98ade8/0x98adec/0x98adf0). The
  "forced-pick key, live 6" therefore arrives with the LOAD — save/scenario data, not a gameplay counter.
- **M122 the 0x1c loop is a COPY, not a third stride.** 0x52b744-0x52b76a copies **0x91cb80 -> 0x98aaf8**, 28-B
  records, 24 of them ((0x98ad98-0x98aaf8)/0x1c exact), and never references 0x984d38. The two arrays merely sit in
  the same address neighbourhood.
- **M123 ds:0x94d78c is ONE dword, two addressing forms.** 72 refs: 48 `[reg+0x94d78c]`, 24 `[reg*4+0x94d78c]`, 6
  writes. All **24** array-form sites carry a 2095-scaled index (`shl 6 / add / lea *2 / shl 4 / sub`), so the *4 is
  the compiler's folded faction stride — same field, no second array (M116's law applied: read the encoding, not the
  syntax). Third confirmation of 8,380.
Instrument note: `open(p,"w").write(open(p).read()...)` truncated field_census.py to 0 bytes — read BEFORE opening for
write; the file was rebuilt from the conversation, not from a backup.

## Session 171 (cont. 16) — doc restructure: the footing file is now an index, the narrative is archived

`NEXT_PROMPT.md` was 15,305 B against a 15,500 cap — 195 B of headroom, and every milestone needs ~600 B of pick text,
so the next batch could not be recorded without deleting findings (three consolidations today were exactly that).
Split instead of shaved: `docs/pick-archive.md` (10,957 B) now holds the M90-M123 milestone narrative and the FULL trap
text; `NEXT_PROMPT.md` (12,936 B) keeps the RULES as 22 one-liners plus the live footing and the closing order.
Headroom 195 B -> 2,564 B (13x). Verified nothing was lost: 21 identifier tokens checked across both files, all present
(0x5a7e7f/0x94d6a4/probe3.py/0x4efe60/TAILOUT/0x93325c/0x6a9480/0x59666d ...); the only "missing" hits were a typo in my
own check (0x93ff3c vs 0x3ff3c) and a name written as FUN_005a6d40 rather than 0x5a6d40.
Also recorded the batch-size finding in BUDGET: 3 milestones comfortable, 5 max when they share one instrument,
box-time milestones 1 per batch.

## Session 171 (cont. 17) — NAMED.md split: the historical middle is archived, the live registry has headroom again

`NAMED.md` was 249,762 B against a 250,000 budget (238 B free), so the next milestone could not be recorded. The
registry's bulk is HISTORY: blocks M32-M84e (sessions 32-133, 52 blocks) are settled findings nobody re-reads to pick
work. Moved byte-identically to `docs/named-archive-m32-m84e.md` (182,747 B); `NAMED.md` keeps the method, `Not yet
named`, and every block from M89 on, and now carries an ARCHIVED pointer telling the reader to grep both files.
**249,762 -> 68,064 B** (181,936 free). Integrity checked line by line: 0 of the moved lines absent from the archive.
Rules that keep this honest: the move is a rename across files in one commit (git records it, nothing is deleted from
history), and the archive names its block order in its own header.

## Session 171 (cont. 18) — M124-M126, three names settled statically (all PASS, zero box time)

`python3 scripts/m124_state_and_memo.py` — SUMMARY M124=PASS M125=PASS M126=PASS (evidence/m124_m126.log).

- **M124 ds:0x926bd4 = the UPKEEP-SYNCH PHASE CODE.** 4 writes and 2 tests in the whole image. `= 1` at the loop entry
  (0x5210aa, right after 0x744f24 / 0x91c658 / 0x91c630 are zeroed), `= 2` after the message at 0x521297 (0x68ea94 =
  **"Skipping upkeep synch"**), back to `esi`=0 at 0x5213c7 after the second (0x68eacc = the same string) with the
  counter `0x91c630` incremented, and `= setne al` (0/1) at 0x57f8c5. **Both readers are `cmp ...,0x1`**: 0x5aaa6f (in
  FUN_005aaa20, after the "Earning a Tech" print) and **0x5aafe4 inside FUN_005aadf0** — the band-flag function, where
  `phase == 1` OR `[fab+0x94d7fc] < 0` skips the tail. So the reason that tail is skipped during upkeep synch is now
  named, not inferred.
- **M125 ds:0x920434 = the ID the window-reset entry publishes, NOT a faction field.** 15 writes, 619 reads, and **12 of
  the 15 writes sit inside a reset sequence** (`mov ecx,0x91db70; call 0x4e25e0` clears the widget object, preceded by
  `[0x91f738]=0xff`, `[0x91f6e0]=esi`, `rep stos`, `call 0x581280`); the stored value is the caller's id (esi/ebx/edi)
  or a constant; **0 references use a faction-scaled base**; the readers compare it against ids (0x546887:
  `if ([eax+0x94d448] & 0x8000000) && (0x920434 != ebx) && ([esi*4+0x92044c] & 2)`).
- **M126 0x59f0c7 = the INVALIDATION of the memoized advance threshold.** `mov [ebx+0x94d800],-1` inside FUN_0059ec90,
  immediately after `[ebx+0x94d650] += [eax+0x927a78]+ecx+ds:0x985afc` and `[ebx+0x94d654] = 0`. Its 3 call sites are
  0x5a0b39 (FUN_005a0aa0), 0x5a123e and 0x5a1277 (FUN_005a0fa0); the first zeroes the DIVISOR `[edx*4+0x94e488]` just
  before the call — so the memo dies exactly when a faction's base count changes.
Method law added to the skill: a small state code is named by the STRINGS printed around its writers.

## Session 171 (cont. 19) — M127-M129 (all PASS): the plan byte's 369 readers, the seek pair in code, the three-condition consume

`python3 scripts/m127_m129_fields.py` — SUMMARY M127=PASS M128=PASS M129=PASS (evidence/m127_m129.log).

- **M127 — the open item "zero sites read plan byte `+42`" is RETRACTED: 369 sites read it.** The type-record PLAN byte
  is `0x98adb2` (= `0x98ad88 + type*52 + 42`) and it has **369 references**, of which **149 are the folded
  `[reg*4+0x98adb2]` form** (reg holds `tid*13`, so *4 = tid*52, the record stride) and **0 use a literal `+0x2a]`**.
  M67's earlier search grepped the literal displacement and therefore could not see any of them; the live-verified
  plan-descending order now has static readers behind it (top: FUN_00502cd0 48, FUN_0055f650 33, FUN_004f6030 24,
  FUN_0055c920 23, FUN_00585720 17, FUN_00556690 15, FUN_00595b10 14).
- **M128 — the "cursor read before the seek is the PREVIOUS cursor" trap is in the CODE.** `mov ecx,[eax+0xa774]` at
  0x497707 is pushed BEFORE `call 0x4026b0` (the seek, 0x497717); the object is then re-derived
  (`mov ecx,[ebp-0x10]; add ecx,0xa780`) at 0x49771c/0x49771f and `call 0x495480` + `and eax,0x20` (0x49772a) test the
  first flag bit of the POST-seek query. So 0x497704 shows the old node and 0x49771c is the first instruction that sees
  the new one — the rule is structural, not a log artefact.
- **M129 — FUN_00546800's guard is one unit with a CONSUME.** It proceeds only when the faction dword at `0x94d448` has
  bit `0x8000000`, `ds:0x920434 != ebx`, AND the per-record byte `0x92044c` has bit `0x2` — then it **zeroes** that
  byte at 0x5469d3. So `0x92044c` bit 1 is a consumed marker for this path (which is why it reads 0 in the saves and
  after a pass), not persistent state.
Search-shape law added to the skill (second occurrence after the M116 stride): a literal-displacement grep misses the
folded `[reg*4+disp]` encoding; count BOTH forms before saying "no site reads X".

## Session 171 (cont. 20) — M130-M132 (all PASS): chooser case 7 found and named, the 24-byte gap is not a layout, 0x92077c is a mode code

`python3 scripts/m130_m132_chooser.py` — SUMMARY M130=PASS M131=PASS M132=PASS (evidence/m130_m132.log).

- **M130 — "chooser case 7" now has a definition and an answer.** The dispatch is in **FUN_00546800** at 0x54eaeb-0x54eafc:
  `call 0x542ea0` -> `cmp eax,0x7` -> `ja 0x54ec82` -> `jmp DWORD PTR [eax*4+0x54ef34]`. The 8-entry table at
  **0x54ef34** is `[0x54ed3f, 0x54eb03, 0x54eb03, 0x54eb29, 0x54ec34, 0x54ec40, 0x54ec4c, 0x54ec58]`: cases 1 and 2 share
  0x54eb03, case 3 is 0x54eb29, cases 4/5/6 are 0x54ec34/40/4c, and **case 7 = 0x54ec58** — the only case that writes a
  state PAIR: `ds:0x920700 = 0xc` and `ds:0x92077c = 1`. (My earlier scan missed it because it looked for a switch in
  0x5a6xxx-0x5aaxxx; the dispatch is keyed on the return of FUN_00542ea0, not on a chooser-internal enum.)
- **M131 — the 24-byte gap between 0x920434 and 0x92044c is NOT a record layout.** 0x92044c: 24 refs, **24 folded**
  (`[reg*4+0x92044c]`, reg = tid*13 -> tid*52). 0x920434: 634 refs, **0 folded** — a standalone global (M125's
  reset-published id). Treating 0x920434 as the `+0` field of that record would have fabricated a layout out of two
  neighbouring addresses; the M127 law caught it in one command.
- **M132 — ds:0x92077c is a MODE CODE with a small domain.** 4 writes (two of them the constant 1, one `ebx`, one `eax`),
  9 tests against **1, 3, 7**, plus a copy compared to **6** at the dispatch (0x54eb1b, right after the case-1/2 body).
  Its partner `ds:0x920700` has 8 writes and is set in the same case-7 body, so the two form a (state, mode) pair.
  Meaning NOT named: no string constant sits within 8 instructions of any write — recorded as a bounded unknown.

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

## Session 171 (cont. 24) — M166-M168 (all PASS): what the rank is, how the struct splits, and a derived cache

`python3 scripts/m166_m168_roles.py` — SUMMARY M166=PASS M167=PASS M168=PASS.

- **M166 — the rank is consumed as an ORDERING TEST.** 0x94d434: 196 refs of which **92 are `cmp`**, against small
  constants **2/4/5/6/7**; the ranking INPUT is the 7-entry dword table at **0x926a7c**, read by only two functions (the
  init loop in FUN_0059aa00 and FUN_00531df0 at 0x532150), and the top entry is EXCLUDED by the single `-1` store at
  0x59ac72 into `0x926a78+n*4`. So the shape is: an order among 7 candidates, one discarded, the result compared
  against small thresholds. **What is being ranked stays unnamed** — recorded as bounded.
- **M167 — the 20-byte struct SPLITS into a header + a payload quad.** All five members have exactly 6 writes, but the
  WRITER SETS differ: `+0x00` is written by FUN_004dc100 (x3) and FUN_0059ec90 (x3) with constants 0/1/0xffffffff and
  carries 7 tests, while `+0x04/+0x08/+0x0c/+0x10` share the SAME five writers (FUN_004dc100, FUN_00510230,
  FUN_00512b40, FUN_00516b80, FUN_0059ec90 x2). Uniformity would have shown one writer set for all five; it does not.
- **M168 — 0x94d488 is a DERIVED/CACHED value, not state.** 22 writes spread over **9 functions** against 49 refs and a
  single comparison. That is the write-dominant profile (cf. base+0xd0 credit, M97): many paths recompute it, so a test
  that treats it as authoritative state is reading whichever path ran last.

## Session 171 (cont. 25) — M169-M171 (all PASS): the totalled table, the aggregator, and a bit-decoder dressed as a struct

`python3 scripts/m169_m171_aggregate.py` — SUMMARY M169=PASS M170=PASS M171=PASS.

- **M169 — 0x926a7c is TOTALLED, not flagged.** Its second reader (FUN_00531df0, 0x532150) runs inside a per-faction
  loop that walks the blocks at stride **0x20bc (8,380)** while stepping the table index by 4, doing
  `ds:0x9204ac++` and `ds:0x9204c4 += [eax+0x926a7c]` — a COUNT and a SUM. So the array M163 ranks is a per-faction
  quantity being totalled across factions.
- **M170 — FUN_00531df0 is the per-faction AGGREGATOR** (6459 B, 1905 insns, 17 call sites): it builds a `1<<faction`
  mask (`shl edi,cl`), gates on **`cmp [ebx+0x94d434],0x5`** — the M163 rank used as a `< 5` threshold, exactly what its
  92 comparisons predicted — and accumulates the count/sum above (plus 0x920720 / 0x9204c8 counters).
- **M171 — FUN_004dc100 is a BIT-DECODER, not a copier.** One byte arrives in AL and the "20-byte struct" is filled as
  **four BOOLEAN dwords**: `[esi+0x94d810/14/18/1c] = setne(al & 1/2/4/8)` (four `setne dl`), the header
  `[esi+0x94d80c]` gets the TRISTATE 1 / -1 / 0 from the `al & 0x10` / `al & 0x20` tests, and `al & 0x40` triggers
  `or [esi+0x94d430],0x800000`. M164's "header + payload quad" is the decoded shape of ONE SOURCE BYTE's bits.

## Session 172 (cont. 26) — M172-M174 (all PASS): the "bit-decoder" is a SAVE-SECTION WRITER, and the aggregator's counters have three consumers

`python3 scripts/m172_m174_savewriter.py` — SUMMARY M172=PASS M173=PASS M174=PASS (evidence/m172_m174.log).

- **M172 — FUN_004dc100 is a save-section writer, and M171's "source byte arrives from a caller" is RETRACTED.** Its 2
  call sites (0x51500f in FUN_00512b40, 0x517eb6 in FUN_00516b80) are argument-free dispatch legs (`mov ecx,esi` /
  `lea ecx,[esi-0x23d94]`, zero pushes before the call). The byte is the SHARED scratch global **ds:0x99aa38** (74 refs,
  33 stores; 19 stores in the 0x41a9xx UI-build block FUN_0041a8f0). The function runs BOTH directions: the PACK leg
  (0x4dc1a4-0x4dc279) loads `eax,ds:0x99aa38`, rewrites 22 `or/and al,ah` bits from the struct + `[esi+0x94d430]` flags
  + `[esi+0x94f4b0]` bit 0x20, stores it back and calls the tagged record writer 0x6267a5; the DECODE leg (0x4dc29c on,
  gated on the write's `jl` exit) reloads the SAME global and re-materialises the 4 boolean dwords + tristate + band
  bits. The context opener 0x4d9fb0 is called by EXACTLY 4 writers (0x4dc100, 0x4dc390, 0x4e0260, 0x5a2930); 0x6267a5
  has 18 sites, 12 inside the 0x4d9xxx-0x4e1xxx save band.
- **M173 — the count/sum pair has 3 + 1 consumers.** 0x9204ac: 6 refs = 2 stores (zero 0x532084, RMW 0x53214a) + 1 loop
  load + 3 consumer sites: 0x53346c INSIDE FUN_00531df0 (`count < 2`, then `table[ebx] >= 3*(sum + table[ecx])`, then
  `rank < 6`), 0x53a9cc in FUN_0053a9c0 (`count + ds:0x920720` -> local total), 0x54d30d in FUN_00546800 (`count != 0`).
  0x9204c4: 4 refs, its only consumer is 0x533478 in the same gate.
- **M174 — the tristate header is a SIGNED MODIFIER.** 7 test sites in 4 functions: 2 `cmp vs 0` (0x4a642f/0x4a6450,
  FUN_004a5eb0), 4 `cmp vs 1` (0x55ee48 FUN_0055ec10; 0x576891/0x576bd8/0x576e45 FUN_00574370), 1 `cmp [eax+0x94d80c],ecx`
  (0x5520cd FUN_00551e50) — plus 7 ARITHMETIC reads: `sub reg,[hdr]` x6 (FUN_0053cb20 x2, FUN_00546800 x2, FUN_005551e0,
  FUN_0055f650) + `add ebx,[hdr]` (FUN_005551e0); the aggregator reads it as |value| (0x53206f + neg/jge into [ebp-0x20]).

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

## Session 174b (2026-10-31) — process pass (no new findings; one claim corrected)

- **SKILL.md cap triage (it sat 36 B under its 70,000-BYTE hard cap).** Split, not shaved: the two procedural
  subsections "The context ceiling is part of the task" and "Close before you hand off" moved VERBATIM into
  `references/session-discipline.md`; SKILL.md keeps a 6-bullet RULES digest (budget bands, 3-invocation cap,
  close order, doc-write laws, split-dont-shave, sibling sessions) plus the pointer. 69,964 -> 54,902 bytes,
  ~15.1 KB of headroom; the reference carries the full trap text. Skill synced to `skill/` (gate: skill sync PASS).
- **The s174 writer-call claim was overdrawn and is now corrected + asserted.** The call is `(name, size, extra)`
  and the sizes are NOT uniform: of the 9 stores that feed `0x6267a5`, 7 pass size **0x41** and the TECHRANDOM
  pair passes **0x1** (0x510289 / 0x5170ae), all with extra=0; EDITVEH is a SECOND record write in FUN_004dde00,
  not the call that follows its store (that store's next call is 0x64b9e0). `m178_m180_scratchband.py` now prints
  the triple table and gates `0x41 x7, 0x1 x2` — re-run: `SUMMARY M178=PASS M179=PASS M180=PASS`, rc 0.
  SESSION_NOTES/NAMED.md M178-M180 and NEXT_PROMPT's pick paragraph carry the corrected text.

## Session 174c (2026-10-31) — box relaunched, first live probe of the M178 staging dword (inconclusive)

- **Box up** after a relaunch that took >9 min on a cold prefix: terran.exe pid 319926, year 2153 round 53,
  University Base (28,42), 6 units HELD, TracerPid 0; `sudo -n python3 scripts/smac_preflight.py` PASSes every
  invariant.
- **New operational law:** the relaunch was killed at a tool timeout and the game came up parented to wineserver,
  not to this session; `yama ptrace_scope=1` then refuses `/proc/<pid>/mem` to the SAME uid
  (`PermissionError` at `smac_preflight.py:56`). Read under `sudo -n`, or relaunch from a tracked background job.
  Written into skill `references/wine-operations.md` ("A relaunched game is NOT your child").
- **M181 probe (live, NOT a finding):** a 2 ms sampler (`scratch/m181/pair.py`: `ds:0x99aa38`, `ds:0x920720`,
  `ds:0x9204b0`, `[0x94d600+3*8380]`, `ds:0x8f0d60`, round/year/cur_player) ran across one boundary driven by
  `m55_boundary.py --settle 0.4`: round 52->53 (+1 exactly), year 2152->2153, cur_player walked the whole player
  loop 3->4->5->6->7->0->...->3, `selobj` churned 11 values. `ds:0x99aa38` stayed **00000000** the whole window —
  consistent with M178's static reading (a UI/scenario writer) — but `ds:0x920720` and `ds:0x9204b0` were also 0
  and static, so the aggregate pass had nothing to aggregate and the probe has NO positive control.
  `m55_boundary.py` itself exited rc=1 on its accounting gates. Falsifier for the next run: arm the sampler, then
  trigger a save or a governor-options OK — a staging change there confirms the writer's trigger; no change
  anywhere means the address or the sampler is wrong.

## Session 174d (2026-10-31) — M182-M184, all PASS (static batch of three, one instrument)

`python3 scripts/m182_m184_bandrecord.py` -> `evidence/m182_m184_bandrecord.txt`, `SUMMARY M182=PASS M183=PASS
M184=PASS`, rc 0.
- **M182 — ds:0x99aa1c is the BASE of the record 0x6267a5 emits.** 14 dwords are referenced in
  [0x99aa1c, 0x99aa5c]; the 13 packers touch exactly FOUR (+0x0 0x99aa1c 637 stores = the generic write-bytes
  argument, +0x4 0x99aa20 637, +0x1c 0x99aa38 33 = the flag dword M178/M179 mapped, +0x20 0x99aa3c 5) and
  +0xc..+0x18 (0x99aa28/2c/30/34) are written ONLY by the emitter FUN_00626b46 (+0x24 by it plus the 0x626xxx
  siblings; +0x30..+0x40 by the 0x627xxx serializers). The 0x41 size pushed with GOVOPTIONS equals the span
  0x99aa1c..0x99aa5c — INFERRED alignment, not proven.
- **M183 — the four whole-value writers are not packers** (each stores the scratch once, vs 9-19 legs): 0x4dc390
  is a RESTORER (17 `test al/ah,imm` scratch-bit tests, 1 mask op) — the mirror of 0x4dc100's 24 pack ops;
  0x4d9ae0 copies bits 0..11 of 0x58e760's return through `shl edx,cl / test eax,edx / or|and esi,edx / inc
  ecx / cmp ecx,0xc` (12 iterations); 0x512b40 computes a `setne` boolean and asks FUN_00518c50 with indices
  1/2/3 (3 call sites) instead of building a mask; 0x4dde00 builds from [esi+0x93327c] tests and pushes EDITVEH.
- **M184 — FUN_00535c60 is a per-faction VISIT wrapper**: 3 call sites in 2 owners (FUN_004266c0 x2 passing
  ds:0x91b5b4 + [ebp-0x14] + eax; FUN_00545c50 x1 with (esi, 0, ebx, eax)); its first 40 insns call 0x531df0 ->
  0x530e30 -> 0x535940 IN THAT ORDER, then fold arg1 with the 2095-dword chain into [ebp-0x14] and test
  `[eax*4+0x94d448] & 0x40030`.

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
