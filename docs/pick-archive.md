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
