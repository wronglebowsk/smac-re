# docs/pick-archive.md — the milestone narrative and the FULL trap text

Moved out of `NEXT_PROMPT.md` at s171 so the footing file stays small enough to hold the next batch of milestones.
Nothing here is a live rule by itself: `NEXT_PROMPT.md` carries the RULES as one-liners; this file carries the
numbers, the addresses and the case history behind them. `NAMED.md` carries the semantic registry;
`skill/references/instrument-laws.md` carries the instrument laws.

## THE PICK — milestone narrative, M100-M123 (verbatim from s171's footing)

## THE PICK

**M100-M106 (NAMED.md):** multiplier = block A slot 10 (M100/M102); D = FUN_0059ec00 off the TYPE==3 entries
(M103); the block is BUILT AT PROCESS START by FUN_005791c0 (M105, 17/17); **M106 PASS 15/15: the load restores by
read() INTO the region** (kernel copy_to_user, no ring-3 store, invisible to a hw watchpoint; .SAV fd via
SCM_RIGHTS). Traced loads are ~10x slow: M54A_LOAD_TIMEOUT=1800.
**s171 .SAV map:** the 156-B trailer IS read (6-site loop 0x59666d..0x59683b); block A 0x94D104; block B 67,852 ->
0x927590; header 0x916D6C; grid 0x40925B0; 52 records 222,783 -> 0x933278; restore 1:1.
**Band flag:** `test BYTE PTR [esi+0x94d430],0x40` once at 0x5aaf7f (take 0x5aaf88), reached 17x/turn, never taken;
no dword OR sets 0x40; the only `or al,0x40` reaching a store writes a DERIVED copy (mask 0xfc3fffff -> ds:0x99aa38);
0 of 12 saves carry the bit -> **inert BY CONSTRUCTION**.
**M119-M123 (scripts/field_census.py, all PASS):** 0x984d38 stride **0x30** (52/52 sites; the "x16" is `shl 4` on 3v,
so M67's conflict is a misread); bit 0x20 of [ebx+0x98adb8] set iff faction dword 0x94d448+inner*4 has bit 0 (index
esi*2095+edi); ds:0x98adee = 7 readers / 0 writers of any width = load-only save data; the 0x1c loop COPIES
0x91cb80->0x98aaf8 (24 x 28 B) and never touches 0x984d38; 0x94d78c is ONE dword in two encodings (24/24 array-form
sites 2095-scaled).
**STRIDE LAW: `f*8380` is DECIMAL 8,380 = 0x20BC = 2095 dwords**, never hex 0x8380. Identify bytes by POKING a marker.


## TRAPS — full text (the one-liner rules in NEXT_PROMPT point here)

## TRAPS

- **The `fired=` list on a `LADDER-MISMATCH` line is the MODEL's prediction, not observed events** (s148); a no-event at an apply site is evidence only once the bp is CONFIRMED to exist there. Gates must PREDICT from live memory, then be confirmed by counters; a counter at a site that is BOTH a branch target and a loop-completion fallthrough is NOT a leg proof (0x5a7f9f); a gate may only read a field the harness SETS (m92 G8).
- **Check the instrument before believing a no-event or a wrong field:** an f-string bp condition that emits `if *$ecx==X` is a DEREFERENCE and silently never fires (m95pay1/2); a bp at a `mov eax,[ebp-0xc]` RETURN site prints the OLD eax — break at the NEXT instruction (0x5aa24a; m96human1 read idx=0); `lea edi,[eax+1]` @0x5aa21a makes edi the MODULUS on the rand path, so a bp at 0x5aa232 printing `$edi` gets score+1, not the faction — read `*(int *)($ebp+8)`; name every printed field the way the parser asks (m96human1 G4/G9/G11 were key names, not the game). ZERO CALLS can be the GAME: scan /proc for the function's vptr first (`scratch/m84d/probe3.py`).
- **Register semantics live in the encoding, not the name:** `[reg*4+0x98adb8]` means the register holds `tid*13`, `[reg+0x98adb8]` the BYTE address `tid*52`; a condition testing such a register against the bare tid can NEVER fire. A read-modify-write through a COPIED register (0x4efe60) evades store-shape greps — a HARDWARE watchpoint on the FIELD answers "who writes it".
- **gdb printf/script laws (skill gdb-command-list.md + instrument-laws.md):** no inferior
  strings; template expressions go in printf ARGUMENTS, never the format; a printf ARG-COUNT mismatch
  or a stray `%%` in a TMPL line ABORTS the sourced script and DETACHES at the first hit (m103d1/d2,
  m102hit1) — count the specs against the args in the harness BEFORE the run; a manual call frame needs
  the RETADDR at esp+0 and the arg at esp+4 (reversed = SIGSEGV, box dead, m103d5); gdb ABANDONS an
  inferior `call` as soon as ANY breakpoint hits inside it — arm the store bps first, read the effect
  back from memory (m103d3).
- **A >90 s gdb census NEVER runs in the foreground** (the terminal caps waits at 420 s; killing it mid-run leaves Wine hung, s143): background + `process_manage wait`, or keep `--rounds <= 4`. **Faction upkeep runs in that faction's OWN segment ~1 cycle after your turn-end: a 1-boundary window can close mid-cycle (m95pay2) — use `--boundaries >= 2`.**
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it:** Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt — never OK); run `m78_mark_clear.normalize_screen()` first; vision coords are SCALE-SHIFTED, click from OCR word bboxes (TURN COMPLETE (675,416)). `m44_idle` asserts TracerPid==0 — never a driver under a census gdb, use m55_boundary.
- **A PASS on a non-discriminating shape is no PASS:** compute candidate predictions from the baseline first; refuse the shape if they all agree. RE-RUN on a harness race, never edit the floor.
- **base+0xd0 (`credit`) is RECOMPUTED EVERY ROUND** (M97 FUN_004e93f0 0x4e9557/0x4e957f = [+0xc0] -
  [+0xf0] - [+0xe0]; "init-only" RETRACTED) — a poke there is undone next turn; gate on round movement
  and use the per-boundary storage poke 200.
- **a gdb HARDWARE watchpoint only REPORTS a VALUE CHANGE** (unchanged store logs NOTHING,
  m97credit2) AND reports `pc = store + INSTRUCTION LENGTH` (m98budget2: 0x5aaf67+10 = 0x5aaf71,
  0x5aaf79+6 = 0x5aaf7f, 0x59f0c7+10 = 0x59f0d1) — gate on those, not on the store address. Count
  stores with silent bps AT the store; keep the watchpoint as the "any other writer" check; whitelist
  `[New LWP]`, `[Switching to LWP n]` and `Thread N "terran.exe" received signal SIGINT`.
- **A census can leave gdb ATTACHED after it prints its verdict** (s171): check `TracerPid` in
  /proc/<game>/status and kill the stale gdb BY PID before calling the box clean.
- **THE TURN DRIVER RETURNS WHILE THE AI UPKEEP IS STILL PLAYING**: rc=0 does NOT mean the round's
  segments are done. Detach gdb before cur_player returns to the human and the LAST recomputes are
  UNLOGGED (m98budget3 G7: fac1 101 logged vs /proc 128) — wait for cp == the human faction.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by "first empty slot" or a stale tail as proof an id IS queued; id 0 is Colony Pod AND the empty marker, the sentinel is -39, a negative belongs to the TYPE (196 -> -6, 195 -> -3). **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (128/322/323/194 = FACTION BANDS, M80): attribute the sweep by its own predecessor; the gate visit arrives in the boundary AFTER the sweep marks (poke window >= 3 boundaries).
- **A list cursor read BEFORE the seek is the PREVIOUS cursor:** the chooser pump seeks with `call 0x4026b0` at 0x497717, so a node print at 0x497704 shows the old node — print at 0x49771c. **`milestone.py start <id>` refuses a dirty tree and resets to main:** stash a carried doc edit, start, pop, THEN re-write `SESSION_CURSOR.md`.
- **Grep objdump case-sensitively** (`DWORD PTR`, not `ptr [`).

- **gdb STARTUP/EXIT CHATTER is not protocol but must be whitelisted**: the debuginfod prompt block (4
  lines) and `[Inferior 1 (process N) detached]` frame the event stream and FAIL a zero-unparsed gate
  (m104w2 11/12 — an INSTRUMENT failure, floors untouched). Set `DEBUGINFOD_URLS=""` in the Popen env and
  whitelist `^\[Inferior `, `This GDB supports`, `Enable debuginfod`, `Debuginfod has`, `To make this setting`.
- **ARM BEFORE ANY SCREEN (s161 law):** the setup writes finish before the first OCR-able screen, and the CDROM screen is QUIIESCENT for 4 min but only advances on driver input — a true-title wait DEADLOCKS. A hw watchpoint can MISS a change entirely (m105s4: the -77 sentinel came back to the save image through the load with NOTHING logged while the control in the same window fired); `[New LWP]` after ARMED = threads gdb may not have re-armed; a background census job DIES with its session (m105s1).

- **A silent bp at the pc a HARDWARE watchpoint REPORTS is EATEN by the watchpoint** (m99p1 G8: 27
  of 37 store read-backs vanished at 0x5aaef1 = 0x5aaeeb+6) — put the read-back bp ONE instruction
  later (0x5aaef3) and read memory, not the register. A poke is only evidence if the CONSUMER reads
  it: [0x94d6a4] poked -5, read back -5, live 0 at 0x4f3558 (recomputed per round, like base+0xd0).


- **A gdb printf FORMAT string passes VERBATIM to C printf:** `"...\n"` (ONE backslash) prints a
  newline; `"...\\n"` (TWO) prints a LITERAL `\n` and collapses the whole event stream into ONE
  unparsed line that reads as ZERO events (m102hit1: 47 events emitted, 0 parsed, floors innocent).
  A bp at the insn AFTER `call X` fires AFTER the callee's events — group per-invocation events
  BACKWARD from it; unwatched factions yield legitimately empty groups: skip, do not fail on them
  (m102hit2 12/14 on perfect data; skill instrument-laws.md).

  - **gdb -batch EXITS the moment a stop has no command left to follow it**: wineserver delivers SIGUSR1
    during a Wine game's startup, so a batch census MUST carry `handle SIGUSR1 nostop noprint pass` (also
    SIGUSR2/SIGPIPE) and a tail of ~400 `continue` lines, or it detaches after 3 events (m109g2). And a
    breakpoint on a function that serves the WHOLE game (the four read wrappers) costs one ptrace stop per
    read: 25,957 stops in 572 s starved the load driver to ZERO loads (m109g3) — filter the bp by the
    FILE* (`set $savefile` at the loader's entry, `if *(int *)($esp+0x10)==$savefile` on the readers).


## M90-M104 registry summary (moved out of the footing's LEDGER at s171)

**M90-M104, all in NAMED.md:** the slot IS a tech index 0..88 (STRICTEST-largest draw, tail only arg2==0);
TAILOUT 0x5a9698 == BASE + the tail simulated from the per-faction block (FROZEN within a round); the POST
cascade 0x5a9747-0x5aa022 == the prereq-closure ladder (0x5a9020(a,X,f) = membership at depth f; FREEZE INPUTS
AT THE TAIL HIT); DIVISOR [fac*8380+0x94e488] == that faction's BASE COUNT, recomputed per round by
FUN_00556690; UI-queued completion pays AND activates in branch A (gate 0x4efa5e, pay 0x4efedd +0x40, POP
0x4f037b), 0x4f0ca6 = branch B's pay; the chooser ranks by the DRAW (FUN_005a6d40; human LCG ds:0x999fa0), NOT
score; base+0xd0 credit recomputed per round (FUN_004e93f0); [0x94d800] = FUN_005aab70's memoized ADVANCE
THRESHOLD vs [0x94d7f8]; param_2's ONE producer FUN_004f34b0 (M99); the multiplier = block A slot 10
(M100/M102); D [0x94d700] = FUN_0059ec00's rebuild (M103); the record block 0x927a9c+fac*1436 is LOAD-TIME,
nobody appends it in rounds (M104). Legs: skill code-atlas.md.


## THE PICK — the s171 milestone lines, verbatim (moved out at cont. 23)

## THE PICK — index (detail: `docs/pick-archive.md`)

- **.SAV is mapped and restores 1:1.** block A k=0x94D104; block B 67,852 -> 0x927590; header 0x916D6C; grid 0x40925B0;
  52 records 222,783 -> 0x933278; the 156-B trailer IS read (6-site loop 0x59666d..0x59683b). The load restores by
  **read() INTO the region** (M106: kernel copy_to_user, invisible to a hw watchpoint; .SAV fd via SCM_RIGHTS).
- **The band flag is inert BY CONSTRUCTION** — `test BYTE PTR [esi+0x94d430],0x40` once at 0x5aaf7f, reached 17x/turn,
  never taken, no setter, 0 of 12 saves. Do not re-open it.
- **M119-M123 (field_census.py, all PASS):** 0x984d38 stride 0x30; bit 0x20 of [ebx+0x98adb8] gated by faction dword
  0x94d448+inner*4 bit 0; ds:0x98adee read-only (load data); the 0x1c loop copies 0x91cb80->0x98aaf8; 0x94d78c = one
  dword in two encodings.
- **STRIDE LAW: `f*8380` is DECIMAL 8,380 = 0x20BC = 2095 dwords**, never hex 0x8380. Identify bytes by POKING a marker.
- **M124-M126 (m124_state_and_memo.py, all PASS):** ds:0x926bd4 = the UPKEEP-SYNCH PHASE CODE {0,1,2} (its `== 1`
  reader at 0x5aafe4 is why the band-flag tail is skipped during upkeep); ds:0x920434 = the id the window-reset entry
  publishes, **not** a faction field (0 faction-scaled refs); 0x59f0c7 = the invalidation of the memoized advance
  threshold `[fab+0x94d800] = -1`, and one of its 3 callers zeroes the DIVISOR first.
- **M127-M129 (m127_m129_fields.py, all PASS):** the PLAN byte `0x98adb2` has **369 readers** (149 folded
  `[reg*4+0x98adb2]`, 0 literal `+0x2a]`) -> the "zero sites" item is RETRACTED; the chooser's pre/post-seek pair is in
  the code (0x497707 / seek 0x497717 / post 0x49771c); FUN_00546800's guard (faction bit 0x8000000 + 0x920434 != ebx +
  0x92044c bit 0x2) **consumes** that byte at 0x5469d3.
- **M130-M132 (m130_m132_chooser.py, all PASS):** the chooser's 8-way dispatch is `FUN_00546800` 0x54eafc on
  `FUN_00542ea0`'s return (table 0x54ef34, case 7 = 0x54ec58 -> sets 0x920700=0xc, 0x92077c=1); 0x920434 is NOT a record
  field (0 folded refs vs 0x92044c's 24); 0x92077c is a mode code tested vs 1/3/7 (copy vs 6), meaning unnamed.
- **M133-M142 (m133_m142_census.py, all PASS):** the chooser dispatches on FUN_00542ea0 (only call site 0x54eaeb); its
  index arithmetic gives the per-faction stride **1436 BYTES = M104's 0x927a9c+fac*1436** (a decompiler `arr[i*0x167]`
  is an ELEMENT index); 0x920700 = UI state code (6/8/0xc/0xd); 0x94d7fc = per-faction counter, -1 = unset; 0x91c630 =
  upkeep-synch counter; 0x985afc = read-dominant run state (336/5); FUN_00495480 = cached-flag getter; FUN_004026b0 =
  LIST SEEK, cursor stored at [obj+0x14].
- **M143-M162 (m143_m162_atlas.py):** the faction-block FIELD ATLAS is generated into `docs/field-atlas-faction.md` —
  the 20 most-referenced `+0x94dXXX` displacements (150 distinct exist) with refs/writes/consts/tests/functions. Shape
  only; `—` in `in NAMED?` = genuinely unnamed. Start here before re-deriving a field.
- Pick from: 0x94d434 (196 refs, ONE write); 0x94d80c / 0x94d81c / 0x94d818 / 0x94d814 (the 78/62/46/42 cluster in
  FUN_0040b960+FUN_0041f0e0); 0x94d554+0x94d488 (FUN_004da2c0 pair); 0x94d4a8 (26 writes).


## THE PICK — the s171-s174e milestone lines, verbatim (moved out of the footing at the s175 cap triage)

- **Named in s171:** 0x926bd4 upkeep-synch phase {0,1,2}; 0x94d7fc counter (-1=unset); 0x91c630 synch counter;
  0x920434 reset-published id (NOT a record field); 0x920700 UI state {6,8,0xc,0xd}; 0x92077c mode {1,3,7}; 0x94d434
  **rank**, written ONCE at init (M163); 0x94d80c..0x94d81c = ONE 20-byte struct (M164); 0x94d554+0x94d55c = an 8-byte
  pair (M165); FUN_004026b0 = LIST SEEK (cursor -> [obj+0x14]); FUN_00495480 = cached-flag getter.
- **M175-M177 (m175_m177_aggcallers.py, all PASS):** FUN_00531df0's 17 sites live in 13 owners (AI hub
  0x546800 x2, 0x5551e0 x2, 0x4a5eb0 x2, 0x534fa0 x2 + 9 singles: wrapper 0x43ff20 arg1=ds:0x91b5b4, save
  path 0x58fa40, 0x535c60, 0x533e70/0x534180/0x5344c0/0x535700, 0x4282d0, 0x55f650); the convention is
  (faction BLOCK base via the folded *8380 chain, record base, mode) — arg3 reloaded at 5 sites, 0x532194
  `test/je` gates exporting [edx+0x94d4a8] -> ds:0x9204b0; 12/17 sites push mode 0. [block+0x94d4a8] is a
  LAST-RUN STAMP vs the round counter ds:0x985afc: 3 callers prime it pre-call (0x533eec/0x53420e/0x534522),
  6 `sub` age tests consume it, and 0x569401 (`cmp edx,0x10; jl`) SKIPS a call when the stamp is fresh.
- - **s174 band map (M178-M184, all PASS):** `ds:0x99aa38` is field **+0x1c of the 65-byte record at
  `ds:0x99aa1c`**; 33 stores / 14 functions, 9 feed `call 0x6267a5` (name, size 0x41 x7 / 0x1 x2);
  the 13 packers touch only +0, +4, +0x1c, +0x20 and +0xc..+0x18 belong to the emitter FUN_00626b46;
  the four whole-value writers are NOT packers (0x4dc390 = 17-test RESTORER, 0x4d9ae0 = a 12-iteration
  `shl edx,cl` copy, 0x512b40 drives FUN_00518c50 by index); `FUN_00535c60` = per-faction visit wrapper
  (3 sites / 2 owners, calls 0x531df0 -> 0x530e30 -> 0x535940, then `[eax*4+0x94d448] & 0x40030`).
  GOVOPTIONS = FUN_0041a8f0; `ds:0x920720` = bit-25-clear count; `ds:0x9204b0` = stamp export.
  Detail: NAMED.md M178-M184 + evidence/m178_m180_scratchband.txt, m182_m184_bandrecord.txt.
- **s174e (M185-M187, all PASS):** 0x530e30 writes only `ds:0x920740=0xf` + the staging +0/+4 pair yet
  makes 10 calls (incl. 0x626634 at 0x530fc0); 0x535940 writes 47 globals (13 x -1, 12 x 0) = the aggregate
  scratch RESET. `[fac*4+0x94d448]` is ASSIGNED by 27 plain movs (8 fns, ZERO bit-setters); the 0x40030 mask
  is tested at 2 sites (0x535ccb + 0x4f2bba). The record's +0x20 (`0x99aa3c`) is a 3-valued SELECTOR (3 of
  5 stores copy `[[0x99aa40]+0x3100]`; FUN_004d9ae0 branches ==1 -> unit placement, ==2 -> `ds:0x985af0`).




## THE PICK — the s175-s178 milestone lines, verbatim (moved out of the footing at the s179 cap triage)

Registry rows: `NAMED.md` M188-M200. Census outputs: `evidence/m188_m190_uses.txt`,
`m191_m193_channels.txt`, `m194_m196_channels.txt`, `m197_m200_proposal.txt`. In the second bullet below,
"the ARCHIVED row above" is the s171-s177 footing bullet that STAYS in `NEXT_PROMPT.md`; its outputs are
`evidence/m175_m177_aggcallers.txt` … `m194_m196_channels.txt`.

- **s178 (M197-M200, all PASS): rows in `NAMED.md` M197-M200; census output `evidence/m197_m200_proposal.txt`.**
  Short of it: FUN_00544530 is the **DIPLOMACY PROPOSAL COMPOSER** for a faction pair — ONE call site in the image
  (0x545c99 in FUN_00545c50, `[ebp+0x10]==0` guard, args [ebp+8]/[ebp+0xc], return tested) — and `ds:0x920700` is
  **ONE FIELD OF A 5-FIELD SELECTOR BLOCK** {0x9206fc,700,728,748,77c} it clears at entry and fills from 6 calls
  to the chooser FUN_005f1394; 6 of its 7 stores there are the constant 0, the image's only immediate store being
  0xc at 0x54ec5c. **M197 RETRACTS M195's "ZERO string literals"**: the body names PROPOSALMENU/REJWARALREADY/
  NOCOMMLINK (Ghidra renders a referenced literal as a named `s_*` symbol — no quote char). Those keys sit in the
  string pool **0x690160..0x69107c** (0xFFFFFFFF-terminated both ends): 311 single-word KEYS + 18 spaced message
  lines, 257 keys with code refs (key→function printed) — the diplomacy vocabulary (full list in `NAMED.md` M198).
  **M199: FUN_00625b20 IS THE SUBSTITUTION ENGINE** — _strstr for '$'
  (0x69911c), switch on the next char over 5 cases (closer '>' 0x699138, '$HEX' 0x699130), kinds M=0/F=1/N=2/#n/
  n→B[n]@0x999ff4+A[n]@0x999fcc, slot text `0x99a01c+n*0x100`, copy the Nth ':'-separated segment; FUN_005808b0
  COMPOSES `$<`+{M,F,N}+{1,2}+`:`+arg+`>` from record dwords +0x2fc/+0x300 and FUN_00580a60 PARSES that head into
  0x99aa1c/0x99aa20 — the staging record IS a parsed tag head. **M200 RETRACTS M194's "formatters 0x631afb/
  0x632cad"**: both are ROW WRITERS on the handle DAT_0099d020 (vtable +0x10/18/38/58/60; alloc 0x5be090, free
  0x64a7f0, append 0x64b9e0) with 0 `0x25` immediates, 0 printf calls and 0 refs to FUN_00625b20 — VERBATIM copies.
- **s175-s177 (M188-M196, all PASS): rows in `NAMED.md`; census outputs: the ARCHIVED row above.** Short of
  the newest: `0x626634` is the 10-slot CHANNEL PUBLISH (guard `arg1<=9`; writes `A[slot]@0x999fcc`/`B[slot]@0x999ff4`;
  appends arg2 into `0x99a01c+arg1*0x100`;
  a negative arg3/arg4 takes the staging pair, `0x99a01c+10*256 == 0x99aa1c`) — its 1584 sites in 190 functions are
  consumed by POINTER PASSING (113 sites/31 fns in the window, 93 push the base or a slot address, 16 callees get it).
  `[reg*4+0x94d448]` is NOT a pointer (the 2095-fold carries 365/466 scaled sites; **M196 RETRACTS M190's
  store-address carriers**).

- **s180 (M201-M204, all PASS): rows in `NAMED.md`; census output `evidence/m201_m204_dialog.txt`;
  instrument `scripts/m201_m204_dialog.py`** (acceptance `python3 scripts/m201_m204_dialog.py` ->
  `M201=PASS M202=PASS M203=PASS M204=PASS (15/15 gates)`, rc 0; invocation 1 was 12/15 on 3 instrument
  bugs, fixed without weakening a threshold). **M201** FUN_005f1394 (11,207 B) is a thiscall member of
  the dialog class whose ctor FUN_00405ef0 installs vtable 0x67164c at this+0 (0x405f31) and 0x671644 at
  this+0x444 (0x405f3a, the CPane subobject), after subobject ctors 0x5ee350 and 0x5f6b8c(this+0x3230);
  99 ctor sites in 90 functions, 53 of the 67 pump-caller functions construct it. 0 data occurrences of
  0x5f1394 image-wide (no vtable or switch holds it); 94 direct calls; one exit `ret 0x8` at 0x5f3f58;
  90/94 sites load ECX from the caller's own frame. It is the ONLY reader of 0x698e40 'OK', 0x698e44 'OK',
  0x698e48 'Cancel', 0x698e50 'OK' (1 site each; the pool alternates). It dispatches 9 resolvable slots
  of 0x67164c (+0x4=0x406750, +0x8=0x4068a0, +0x30=0x406970, +0xdc=0x5ce5bd, +0x15c=0x406990,
  +0x160=0x404e70, +0x164=0x407060, +0x16c=0x407280, +0x170=0x407660) and dispatches +0xdc twice, on
  *this and on *[this+0x285]. **M202** return domain {0 (5 `xor eax,eax`), -1 (2 `or eax,0xffffffff` +
  `mov eax,ds:0x698d0c` at 0x5f3f38, that dword IS 0xffffffff), [this+0x290] (the single `[reg+0xa40]`
  read at 0x5f3f45, 0 stores), pass-through}: 0 `mov eax,imm` in the whole body. arg2 IS A CALLBACK: its
  2 uses (0x5f3d87, 0x5f3dcb) both feed a +0xdc dispatch and vtable+0xdc FUN_005ce5bd (`ret 0xc`, 3 args)
  tests it at 0x5ce6bd and `call dword ptr [ebp+0xc]` at 0x5ce6c3. 17/94 sites pass a code pointer, 16x
  0x530d70 + 1x 0x530db0, unnamed islands in the 0x530d45-0x530df0 gap: gate on ds:0x920434 then
  ds:0x991588, set ds:0x920790=1 (its only 4 stores image-wide), call FUN_00519a20, clear, return 1/0.
  **M202 RETRACTS M197's "chooser"**: all 6 composer calls store the return into
  {0x9206fc,0x920700,0x920728,0x920748,0x92077c} within 4 instructions and test it against a small
  integer; 0x920700 is touched at 31 sites in 4 functions and compared with {4,6,8,9,d} - a dialog RESULT
  CODE, not a mode. **M203** FUN_0062898e is a first-DIGIT scanner (61 B, 0 callees, only '0'/'9' bounds
  plus the NUL test), 5/5 call sites inside FUN_00625b20; $H compares 4 bytes with 0x699130 '$HEX' ->
  `__itoa([0x999fa4][n])`, else digit -> slot text `0x99a01c+n*0x100`; $L's exception is 0x69913c
  '$LINK<'; $N gotos switchD_00625bb6_caseD_4e, the same tail as the unnamed default; the engine returns
  only 14 (x6, behind 8 `9 < local_1c` guards) and 3 (null args). **M204** the key pool is an EMITTER
  LIST: 313 `push <key VA>` sites / 255 distinct keys / 29 functions, all inside 0x5316b0..0x54f1d0,
  FUN_00546800 owning 111 sites / 97 keys; the sinks are FUN_00626a17 x149 (thunk to FUN_00626b19
  (&DAT_00997528, key, -1, 0, ...)), FUN_0064b9e0 x76 and FUN_00405220 x33 (thunk to
  FUN_00404010(&DAT_00997120, key)) = 258/313; only 11 of the 29 referrers call the pump and 56 of the 67
  pump callers name no key - the paths join only as 0x530d70 -> FUN_00519a20 -> FUN_00546800.

- **s181 (M205-M208, all PASS): rows in `NAMED.md`; full detail in `SESSION_NOTES.md` Session 181; census
  output `evidence/m205_m208_fields.txt`; instrument `scripts/m205_m208_fields.py`** (acceptance
  `python3 scripts/m205_m208_fields.py` -> `M205=PASS M206=PASS M207=PASS M208=PASS (14/14 gates)`, rc 0 on
  the FIRST acceptance invocation; two `--probe` runs first fixed 5 gate expectations - [ebp-0x30] has 3
  stores (0x5f13d8 init), the +0xa40 census spans 30 fns, +0xa14 needs a DIRECTION-aware load/store split
  (10 loads + 1 store), the 2nd +0xe0 dispatch is 0x5f5893, `ds:0x9939c4,edx` is 0x5ce60e - no threshold
  weakened). **M205** the pump returns `[this+0xa40]` (`this[0x290]`) on the ONE leg gated by
  `[ebp-0x30]==0`; writers = the class vmethods FUN_005f5759 (+0xa8/+0x228, 4 stores) and FUN_005f58fa
  (+0x64/+0x1e4, 3 stores), 0 direct call sites each, value = `[node+[node+8]+0xec]` or `call 0x5fdcf7`
  or 0 / 0xffffffff; FUN_005f5759 also parks its arg in [this+0x3100]; forwarders FUN_005ce4a9/0x5ce4dc
  write through [this+0x43c]/[this+0x440]; base ctor FUN_005ee350 zeroes it (0x5ee7a5). **M206**
  `this[0x285]` = +0xa14, a slot of the 7-pointer link block 0xa14..0xa2c spliced by FUN_005ee350/0x5eede6
  (9 stores each) and FUN_005f6b8c (6, seeded from the global ds:0x997850, vtable 0x671d94 installed at
  0x5f6bdc); the pump's 0x5f3d7c test delegates +0xdc to the child (0x5f3dbe) or to self (0x5f3df6) with
  identical args; +0xdc = FUN_005ce5bd, a modal loop over a 4-deep dialog stack (guard `cmp ds:0x9939c8,4`,
  [d*4+0x992db8]/[d*4+0x992dc8], current ds:0x9939c4, suspend +0x10, activate +0x4, events +0xe4,
  `call [ebp+0xc]`, close +0xe0, `ret 0xc`). **M207** FUN_00546800: switches 12/5/8 at
  0x54eef8/0x54ef14/0x54ef34 (guards cmp 6 / cmp 0xa + byte-permute 0x54ef28 / cmp 7 on `call 0x542ea0`,
  the last behind ds:0x920434 and ds:0x985ae8 bit 0x800); builds a dialog on its 0x5534-byte frame, 0 pump
  calls; 111 single-word key sites = 109 addresses = 97 texts; 29 in the prologue, 68 from 0x54ad65, 7
  across the 8 result-code regions. **M208** ds:0x997528: 103 address-pushes + 1 byte clear (0x5f58de) +
  1 arg-slot store, 0 absolute loads; drain = FUN_005f0583 (79/103, defaults its text arg to the buffer,
  calls the tag engine 0x625b20, writes [this+0x2350] 7x, attaches via FUN_005eede6); FUN_00626a17 is a
  38-B thunk to the writer FUN_00626b19 and FUN_0064b9e0 is the SWAR strlen - M204's "76-site sink"
  measures the key text, it does not emit it.

## s181 footing moved out of NEXT_PROMPT at s182 close (verbatim)

**s180 (M201-M204) and s181 (M205-M208) footing is ARCHIVED:** milestone lines in `docs/pick-archive.md`,
  semantics rows in `NAMED.md`, census outputs `evidence/m201_m204_dialog.txt` + `m205_m208_fields.txt`,
  instruments `scripts/m201_m204_dialog.py` + `m205_m208_fields.py`. Short of it: FUN_005f1394 is the
  OK/CANCEL DIALOG RUNNER (class ctor FUN_00405ef0, vtable 0x67164c) and it RETURNS `[this+0xa40]` =
  Ghidra `this[0x290]`, written only by the class vmethods FUN_005f5759 (+0xa8/+0x228) and FUN_005f58fa
  (+0x64/+0x1e4) - each with 0 direct call sites - from the item list, or 0 / 0xffffffff; `this[0x285]` =
  byte +0xa14, a slot of a 7-pointer link block (0xa14..0xa2c), is the CHILD the +0xdc dispatch delegates
  to (0x5f3dbe child / 0x5f3df6 self, identical args); +0xdc = FUN_005ce5bd, a modal loop over a 4-deep
  dialog stack (guard `cmp ds:0x9939c8,4`, [d*4+0x992db8], current ds:0x9939c4); FUN_00546800 switches
  12/5/8 at 0x54eef8/0x54ef14/0x54ef34 and builds a dialog on its own frame without calling the pump;
  ds:0x997528 is a write-only staging buffer (103 address-passes, 0 absolute loads) drained by
  FUN_005f0583 (79 of them).
- Pick from: WHO DISPATCHES dialog slot +0xa8 (the result-field writer): 29 `call [reg+0xa8]` sites in 17
  fns image-wide, NONE of them in a pump-caller or ctor-caller function - read FUN_0043a4e0 (6 sites) and
  FUN_00478080 (4) and say whether either dispatches a 0x67164c object and with what argument; the DIALOG
  STACK FUN_005ce5bd keeps - what its arg3 (stored to [depth*4+0x992dc8]) is, who else reads
  0x992db8/0x992dc8/0x9939c4/0x9939a0, and what slot +0xe4 (the event pump) returns; the 0xb4c-byte ROW
  object (ctor FUN_005faec0 - now also known to be called twice by FUN_005f6b8c, on this+0xaac and
  this+0x15f8 - layout FUN_005f9e85, 90 sites / 23 fns) and where its label text comes from;
  FUN_00542ea0's return domain (the 8-entry switch 0x54ef34, gated on ds:0x920434 and ds:0x985ae8 bit
  0x800); the pump's -1 vs the UNMERGED M83/M84 "-9999 at 0x496ad0 = DIALOG-CANCEL"; M181's control (box).

## s182+s183 footing moved out of NEXT_PROMPT at s183 close (verbatim)

Short of it (s182, M209-M212): slot +0xa8 has 33 implementations over the 188 vtables the model finds; 3
(0x67164c/0x6717cc/0x6728c0, 464 installs, 457 at `[ebp-disp]` - dialogs are stack locals) map it to
FUN_005f5759, the writer of `[this+0xa40]`. Its dispatchers: the family's own +0x4c vmethod FUN_005f6aa3
(FUN_005e7917 walks a 24-B list from `[obj+8]-1` and publishes item[+0x14]/[+0x10]; the call runs when the
index != -1 and the 2nd out-param == 0) and FUN_0043fee0 (+0xa8 of 0x6738e4, 0 direct calls) via the handle
ds:0x9977f0, which ONLY the pump writes (0x5f3d70/0x5f3e02). Dialog stack = dialogs[] 0x992db8 (4 stores/2
loads) + WRITE-ONLY arg3[] 0x992dc8; current 0x9939c4 / depth 0x9939c8 written only by FUN_005ce5bd +
FUN_005ce6ff; slot +0xe4 is a bool (`ds:0x997770 == 0`; sibling `return 1`), not an event pump. FUN_00542ea0
wraps the pump (ctor FUN_00405ef0 + 1 pump call + `return uVar2`), so the 8-case switch at 0x54ef34 keys on
the PUMP's result code. -9999 = FUN_00496ad0's "unset" return (init 0x4976ce, read-back 0x4976f9, 1 caller
FUN_00417ee0), disjoint from the pump's -1.

The pick s183 answered (verbatim): the 0xb4c-byte ROW object (ctor FUN_005faec0, called twice by
FUN_005f6b8c on this+0xaac and this+0x15f8; layout FUN_005f9e85, 90 sites / 23 fns) and where its label
text comes from; the object FUN_005e7917 walks (`[obj+8]` = item count, 24-byte items, item[+0x10]/[+0x14]
= the pair FUN_005f6aa3 publishes) and what FUN_005e75a0 tests per item - FUN_00478080 retries it 4x, then
dispatches +0xa8 with 0..3; who dispatches +0x4c (12 sites) = FUN_005f6aa3's 5 callers; the class whose
+0xa8 IS FUN_0043fee0 (vtable 0x6738e4: installs, frame displacement, other slots) and what the other two
readers of ds:0x9977f0 do (FUN_005f5a11 0x5f5a17, FUN_005d69fa 0x5d6a17); the SIBLING dialog family
0x671d94 (275 installs, +0xa8 = FUN_005f90d7, +0x64 = FUN_0043fb00, +0xe4 = `return 1`) vs 0x67164c;
M181's control (box). ANSWERED by M213-M216 - see `evidence/m213_m216_hotspot.txt` + `NAMED.md`.

## s184 footing moved out of NEXT_PROMPT at s184 close (verbatim)

- **s181-s183 footing is ARCHIVED** (M205-M216): milestone lines in `docs/pick-archive.md`, semantics rows
  in `NAMED.md`, census outputs `evidence/m205_m208_fields.txt`, `m209_m212_dispatch.txt`,
  `m213_m216_hotspot.txt`, instruments `scripts/m205_m208_fields.py`, `m209_m212_dispatch.py`,
  `m213_m216_hotspot.py`. The dialog model in one line: the pump FUN_005f1394 returns `[this+0xa40]`,
  written only by vmethods +0xa8 (FUN_005f5759) / +0x64; +0xa8 (33 impls / 188 vtables) IS THE
  CLICK-RESULT SLOT - its dispatcher is the family's own +0x4c vmethod FUN_005f6aa3 (5 vtables, 466
  installs, 0 direct calls), which hit-tests (x,y) against the hotspot list AT this+0x3098 (FUN_005e7917:
  24-B items {x0,y0,x1,y1,gate@0x14,payload@0x10}; FUN_005e75a0 = half-open point-in-rect; reverse scan,
  highest hit wins) and dispatches +0xa8 with item[+0x10] when item[+0x14]==0; the row class 0x67194c is
  0xb4c (2 embedded in 0x671d94 at +0xaac/+0x15f8), FUN_005f9e85 builds its labelled controls and its
  label is the global scratch text buffer ds:0x997120 (1425 of 3232 pushes hand that buffer to the emitter
  FUN_0064b9e0); ds:0x9977f0 = 2 stores (the pump) + 7 loads in 4 fns (the forwarder FUN_0043fee0, the
  current-object picker FUN_005d69fa -> its [+0xa8] DELEGATE, the callback FUN_005f5a11 installed at
  [reg+0x2210/2224/2234]). Stack = dialogs[] 0x992db8 + WRITE-ONLY arg3[] 0x992dc8; +0xe4 is a bool;
  FUN_00542ea0 wraps the pump; -9999 = FUN_00496ad0's unset sentinel.
- Pick from: WHO dispatches the dialog's +0x4c (466 installs, 0 direct calls; all 12 image-wide
  `call [reg+0x4c]` sites belong to other hierarchies - falsifier = a live vtable read at a click, box);
  who BUILDS the this+0x3098 list (`call 0x5e7665` on `[esi+0x3098]` at 0x421ea0 of the dialog ctor
  FUN_00421da0 - census `call 0x5e7665` sites + their owner displacements, and what writes `[list+0]` /
  `[list+8]`); FUN_005f5a11's host (who stores 0x5f5a11 into [reg+0x2210/0x2224/0x2234] and who calls
  those fields); the 9 one-store setters FUN_0045a4d0..FUN_0045a650 (what the triples 0x9978ac..0x99790c
  hold, who reads the row's 0xae0..0xb48 copy); the 0x671d94 sibling panel (ctor FUN_005f6b8c, 275
  installs, fields 0xa1c..0xaa0, 2 embedded rows) and its +0xa8 FUN_005f90d7 vs FUN_005f5759; M181's
  control (box).

## s184: the .SAV restore bullet and the s171-s180 pointer moved out of NEXT_PROMPT (verbatim)

- **.SAV is mapped and restores 1:1** (block A 0x94D104, B 67,852->0x927590, grid 0x40925B0, 52 records 222,783->
  0x933278; the 156-B trailer IS read); the load restores by **read() into the region** (M106).

- **s171-s180 footing is ARCHIVED** (M163-M204): semantics + milestone lines in `NAMED.md` +
  `docs/pick-archive.md`; census outputs `evidence/m175_m177_aggcallers.txt` … `m201_m204_dialog.txt`.

## s185 footing moved out of NEXT_PROMPT at the post-s185 cap triage (verbatim)

- **s181-s184 footing is ARCHIVED** (M205-M221): milestone lines in `docs/pick-archive.md`, semantics
  rows in `NAMED.md` (M163-M221), census outputs `evidence/m175_m177_aggcallers.txt` .. `m217_m221_panel.txt`,
  instruments `scripts/m205_m208_fields.py`, `m209_m212_dispatch.py`, `m213_m216_hotspot.py`,
  `m217_m221_panel.py`. The dialog model in one line: the hotspot list is a CONTAINER {array@+0,
  capacity@+4, count@+8} of 24-B items - FUN_005e7665 clear (130 sites, a wrapper over the free+reset
  FUN_005e760d) / FUN_005e7678 alloc n (21 sites, capacities 1..0x100) / FUN_005e774d ADD(gate,
  payload, x, y, w, h) (32 sites, the ONLY writer of item+0x10/+0x14, -1 when full) / FUN_005e78c7
  remove-by-payload (32) / FUN_005e7917 hit-test publishing +0x14->arg3 and +0x10->arg4 - and it is a
  MEMBER (47 member sites over 21 displacements 0x10..0x402f0 + 81 stack locals); the dialog's at
  this+0x3098 is allocated 10 items by FUN_005ef957, reset by FUN_005ee350, scanned by FUN_005f6aa3
  (which gates on item[+0x14]==0 and dispatches +0xa8 with item[+0x10]) and has 0 add-sites. The row
  class 0x67194c (0xb4c) copies 9 triples 0x9978ac..0x997914 written by 9 THREE-store setters, all
  called once by FUN_00459bb0 (3 pass 0x774c38+0x2c*i, 6 pass 0,0,0). FUN_005f3f5b (+0x15c of 0x6717cc,
  10-case switch at 0x5f5731, called twice by FUN_00406990 = +0x15c of the 0x67164c family) is the ONLY
  writer of +0x2210/+0x2224/+0x2234 (3 stores of FUN_005f5a11) and those fields have 0 LOADS. The panel
  0x671d94 (87 slots, 275 installs, size 0x214c, ctor FUN_005f6b8c, 2 rows at +0xaac/+0x15f8, CPane
  subobject 0x671d8c at +0x444, embedded by the dialog ctor at +0x3230) has no click dispatcher; its
  +0xa8 FUN_005f90d7 is a DETACH (clears +0xa38, unlinks via +0xa20/+0xa24/+0xa2c, dispatches +0xb8) vs
  the dialog's FUN_005f5759, which writes the result field +0xa40 (4 stores).

## s186 footing moved out of NEXT_PROMPT at the post-s186 close (verbatim)

- **s186 result (M222-M226, 26/26 gates on one invocation, `scripts/m222_m226_rows.py`)**: the hotspot
  adder FUN_005e774d maps arg1->item+0x14, arg2->item+0x10, arg3->item+0, arg4->item+4, item+8=arg3+arg5,
  item+0xc=arg4+arg6 and returns -1 when count>=capacity (no allocator, a full list DROPS the item).
  FUN_00403b00 (75 B, ret 0xc) is the image's only ADD WRAPPER: container = its own ecx (spilled to
  [ebp-0x4]), args (gate, payload, RECT); 23 sites in 16 functions, container = own ecx plus one of 8
  member disps {a48, cc4, e40, 15e0, 28ac, 5994, 12758, 12764}; 0 wrapper and 0 direct add-sites carry
  the dialog's +0x3098 (its 10-item list is never appended). At those sites the +0x14 slot is an
  immediate 4/23 times and a loaded value 19/23, the +0x10 slot an immediate 19/23 with values
  {0,1,2,3,4,0xa,0xb} (0xa/0xb outside M218's {0,1..8,0x45}). FUN_0041f310 = +0x30 of 0x672448 with all
  3 sites `ecx=0x6a9480`; 8 of the 15 sites of FUN_0040f830/004105b0/00411840/00415d10 pass the same
  immediate (the pane object); FUN_004105b0's container = this+0x402f0. FUN_005f5a11: 0 direct calls, 0
  slots, 0 data copies outside its 3 install immediates, 0 reads / 0 lea-takes / 0 indirect calls in
  0x21c0..0x2260; its body reads ds:0x9977f0 and gates [h+0x2350] in {1,-1} -> a method of the MODAL
  object. The block IS live: FUN_005f1394@0x5f1e33 calls FUN_0060c436 with ecx = obj+0x21d0 (arg1 =
  [obj+0x2350]); FUN_0060c436 -> FUN_00607eca (this+0xb14, which subtracts 0xa94) fills the container at
  obj+0x2250. FUN_00459bb0: 1 call site (0x45a755 in FUN_0045a740, 56 B, 1 caller FUN_00580260), 9 42-B
  triple setters each called once from it (M219 CONFIRMED: 3 receive grid pointers, 6 receive (0,0,0));
  grid = 0x774c38+0x2c*i (i=0..8), 24 pushes over 15 calls, all-zero BSS; FUN_0041f450 installs 0x774c0c
  x4 + 0x774a80 x1 at [obj+0xb24] and 9 functions load it. FUN_005f90d7 (panel +0xa8) dispatches
  [reg+0xb8] x2, [reg+0x5c], [reg+0x1c], [reg+0xf0] and [reg+0x2144] x2 — max vtable slot in the image =
  0x178, so +0x2144 is the panel's own last field (54 sites, 17 writers, 7 readers/callers). FUN_005fb1a5
  = row 0x67194c slot +0x30: 14 `add ecx,0x444` receiver switches, 1 indirect `call [edx+0x14]`, groups
  read as [reg+reg*4+0xabc]/+0xac8 indexed arrays, emitters 0x5dd09c x5 / 0x5c153f x5 / 0x5ca7c3 x4.

### Moved VERBATIM out of NEXT_PROMPT.md at s191 (headroom; the same laws live in `skill/references/instrument-laws.md`)

4. gdb printf/script laws: no inferior strings; expressions go in printf ARGUMENTS; an arg-count or `%%` mismatch
   ABORTS the sourced script and DETACHES at the first hit — count specs against args BEFORE the run; a manual call
   frame needs the RETADDR at esp+0 and the arg at esp+4 (reversed = SIGSEGV, box dead); gdb ABANDONS an inferior
   `call` as soon as any bp hits inside it (arm the store bps first, read the effect back from memory).
5. `printf "...\\n"` (ONE backslash) prints a newline; TWO prints a LITERAL `\n` and collapses the stream into ONE
   unparsed line that reads as ZERO events. A bp at the insn AFTER `call X` fires AFTER the callee's events — group
   backward; unwatched factions yield legitimately empty groups: skip, do not fail on them.
7. A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it: Return clears a dialog, a
   BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt — never OK), run
   `m78_mark_clear.normalize_screen()` first, click from OCR word bboxes (TURN COMPLETE (675,416)). `m44_idle` asserts
   TracerPid==0 — never a driver under a census gdb, use m55_boundary.

## s194 overflow (moved VERBATIM from NEXT_PROMPT.md's ANSWERED bullet at M243)

- ANSWERED (do not re-pick): s187 M227/M228; s188 M231-M234; s189 M235-M237 (0x679f98 = 88 slots, TWO ctors;
  the +8=9 stamper FUN_005dbb5f + ds:0x9965b8; FUN_005be090's +4 blocks; FUN_005f5a11's write-only triple) —
  detail in `NAMED.md`. s190 **B1**: `sim.selftest` -> `PASS B1: 10/10 gates` on BOTH maps. s191 **M240**
  (6/6): the `.MP` grid IS the live terrain-record array (44-B records = TWO map columns; "cell+7 = land
  marker" / "+7 = owner byte" RETRACTED; +16..+43 = 7 copies of the +8 mask, OPEN). s192 **M241** (`FAIL
  2/5`, PR #180 open): a SAVE ran ZERO of the 42 armed 0x99aa38-band sites — not the write path. s193
  **M242** (`PASS 5/5`, `sudo -n python3 scripts/m242_save_write.py`): the save WRITE function is
  **`FUN_00597ce0(path)`** -> **`FUN_00596850(handle, 1)`**, ONE codec both ways (mode → `DAT_00926a0c`;
  30 write / 28 read sites; a save ran 23/30 write, ZERO read); the 796-B `DAT_00985ab8` block sits
  verbatim at **file offset 12** (corrects SAVE_FORMAT.md). Full text: `NAMED.md` M240/M242 blocks.
  (s194 note: the "28 read sites" figure was corrected to 30 by M243.)

## BUILD TRACK block moved VERBATIM out of NEXT_PROMPT.md at s194 (headroom)

## BUILD TRACK — every 4th fire builds (added s187)

`python3 scripts/track_mode.py` prints the verdict from merged history: `MODE=BUILD|ANALYSE`, `next_rung=B<n>`.
**MODE=BUILD ⇒ this fire is a build fire**: take that rung from `BUILD_SPINE.md` and build it in `sim/` — runnable
acceptance command, parity against a recorded trace, never a census claim, no box time, no `/proc`, no gdb. The
other three fires analyse exactly as before, and a build fire does NOT pay the box debt (it never touches Wine).
Build rungs are `B<n>` in the commit and PR title so the cadence can be counted.

## s195 overflow (moved VERBATIM out of NEXT_PROMPT.md's ANSWERED bullet at B2, headroom)

- ANSWERED (do not re-pick; `NAMED.md` carries the full text, `docs/pick-archive.md` the s187-s193 detail
  VERBATIM): s187-s189 M227-M237 (0x679f98 = 88 slots, TWO ctors); s190 **B1** 10/10 on BOTH maps; s191
  **M240** 6/6 (`.MP` grid IS the live terrain-record array; "+7 = land/owner byte" RETRACTED; +16..+43 =
  7 mask copies OPEN); s192 **M241** FAIL 2/5, #180 open; s193 **M242** PASS 5/5 (the save WRITE function
  is **`FUN_00597ce0(path)`** → **`FUN_00596850(handle, 1)`**, ONE codec both ways; the 796-B
  `DAT_00985ab8` block verbatim at **file offset 12**); s194 **M243** PASS 4/4 (`sudo -n python3 scripts/m243_leg_gates.py`, static,
  zero box time): the codec's 7 dead write legs ARE its 7 dead read twins (state gates, not mode
  gates), killed by 3 families — the swap bit (3 plain twins inside the swap-only region, unreachable
  in BOTH swap states = dead code), `ds:0x985dbc < 3` legacy scratch-buffer legs (58,848 + 1,664 +
  48n B, malloc'd via `call 0x5be090`), and the feature bit `ds:0x985ae8 & 0x10` (256 B at 0x991698).
  The codec has **30** read sites, not 28 (`0x5979f8`/`0x597a19`).
