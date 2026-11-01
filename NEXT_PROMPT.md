# NEXT_PROMPT.md — footing for the next session (session 174, 2026-10-31)

Structure: this file = RULES + live footing. Detail is on disk: `docs/pick-archive.md` (milestone narrative M90-M123
+ the FULL trap text), `NAMED.md` (semantic registry), `skill/references/instrument-laws.md` (instrument laws). Read
the archive only for the section you are picking.

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor (`auxiliary.compression: auto` -> the same 262k model) and its summaries die
on the output cap (s113/s114 hit 259,232/262,144 mid-sentence). **Whatever is not finished by ~150k tokens is not
finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 25 `git add -A && git commit`** — the next turn may be the
  truncated one, so every later step must leave a committed file.
- **30-40** STOP MEASURING: an acceptance that is not green IS the finding — write the blocker and the failing number,
  merge nothing, close.
- **40-50** closing order, TERSE: notes <= 2 KB, NAMED block <= 1 KB, this file patched BY SECTION, never rewritten.

Survivability: cursor <= 600 B before any >2-min step; never `rm`/`git checkout --`; doc writes are appends or small
patches. **Batch size (s172): 3 static milestones through ONE census script is comfortable; box-time milestones go 1 per batch.
milestones go 1 per batch.** The binding cap is doc headroom, not capability.

## THE LEDGER

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90-M100 (#95/#97-#104, #106-#107), M102 (#109), M104 (#111),
M105-M106 (#112/#113), M110-M113 (#116/#121), M116-M118 (#126-#129), M119-M123 (#130), M163-M171 (#138-#140),
M172-M174 (#141), M175-M177 (#145), M178-M180 (#147). UNMERGED: M83/M84 family (-9999 at 0x496ad0 = DIALOG-CANCEL; 0x4d00 post gated at 0x4193b2 on
ds:0x920434 != 0, live 0), M86 (0x5a7e73 skips the band loop unless arg1 == 0x93325c/68/74), M101 (#108, superseded),
M103 (#110, never green), M109 (gates answered, model void). Registry summaries: `docs/pick-archive.md` (M90-M104),
`NAMED.md` (semantics), `skill/references/code-atlas.md` (legs).

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it immediately before you arm** (screen fixes live
   in TRAPS).
2. Writer/flag chain — silent bps or hw watchpoints + a prediction from live memory + a read-back:
   `m94_table_watch.py` (4 hw watchpoints on any 4 dwords), `m97_credit_watch.py`, `m100_mult_watch.py`,
   `m102_rebuild_at_hit.py`, `m103_d_rebuild.py` (all three take `--predict`, which prints the model table without
   touching the game), `m92_tail_census.py`, `m95_pay_sites.py`, `m98_advance_budget.py`, `m117_gate_take.py`; each
   prints pc+new+round+cp and names the writer by containment (ghidra_out/index.csv). Flags via `--help` first.
3. Static-first kit (s171, zero box time): `field_census.py` (a displacement/global's shape from its addressing form
   and index arithmetic), `name_global.py` (every reader/writer of a global + containment), `m118_flag_never_set.py`
   (is a gate even satisfiable: test sites, OR immediates, register-level bit ops, and whether any save carries the
   bit), `fn.py 0xADDR` (decompiled body), `scratch/m71/dis.py LO HI [cap]` (objdump window; import as a module, `dis`
   clashes with stdlib), `evidence.py audit [--delete]|budget`.
4. Self-documenting: `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m65_screen.py --samples 8`, `m70_scan_writers.py`.

## THE PICK — index (detail: `docs/pick-archive.md`)

- **.SAV is mapped and restores 1:1** (block A 0x94D104, B 67,852->0x927590, grid 0x40925B0, 52 records 222,783->
  0x933278; the 156-B trailer IS read); the load restores by **read() into the region** (M106).
- **Laws that decide field questions:** `f*8380` is DECIMAL 8,380 = 0x20BC = 2095 dwords; a decompiler `arr[i*N]` is
  an ELEMENT index (x4 for bytes); a record field may appear as `[reg+disp]` OR the folded `[reg*4+abs]` - count BOTH
  before saying "no site reads X"; a hw watchpoint only reports a CHANGE; a gate may only read a field the harness SETS.
- **Where the map lives now:** `docs/field-atlas-faction.md` = the 20 most-referenced faction-block displacements with
  refs/writes/consts/tests/functions (M143-M162). Start there before re-deriving a field.
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
- - **s174 (M178-M180, all PASS) named the staging slot.** ds:0x99aa38 is the tagged-record STAGING dword (third
  field of the ds:0x99aa1c/0x99aa20 pair, 637 stores each): 33 stores in 14 functions, 9 of the 13 outside
  FUN_0041a8f0 sit directly before `call 0x6267a5` (args: name, size, extra — 7 pass 0x41, TECHRANDOM 0x1) and those names read out of
  terran.exe as GOVOPTIONS 0x6899ec, ASSEMBLEGROUP 0x68c774, AIEDITOR 0x68c80c, AIEDITOR2 0x68c818, RULES
  0x68c824 + 0x691e30, SCENRULES 0x68c82c, SCENVICTORY 0x68c838, TECHRANDOM 0x68db28, EDITVEH 0x68c87c (the
  exe's record-type NAME table - not file bytes). FUN_00518c50 = set/clear scratch BIT (arg1 index). Band =
  scratch bits 0..17 (FUN_0041a8f0 18); FUN_004dc5f0 == FUN_0057c550 unpack leg-for-leg 18/18; FUN_004dc100
  packs the M164 struct with 0x94d80c as a SIGN PAIR. ds:0x920720 = the aggregator's bit-25-CLEAR count (AI-hub
  loop bound + two `cmp ,0x2` gates); ds:0x9204b0 = the stamp export, age-tested as ds:0x985afc - stamp.
  Detail: NAMED.md M178-M180 + evidence/m178_m180_scratchband.txt.
- Pick from: what the SAME writer calls put in ds:0x99aa1c / ds:0x99aa20 (the staging pair's other two fields);
  the whole-value writers (FUN_004d9ae0 12-iteration bit loop, FUN_004dc390 12-leg RESTORER, FUN_004dde00,
  FUN_00512b40) vs the leg packers; FUN_0053a9c0's use of the count (it reads 0x9204ac and 0x920720 together at
  entry); who calls FUN_00535c60; the save-band siblings 0x4e0260 / 0x5a2930 (what each writes).
## LIVE FACTS / KIT

- **BOX DOWN at s174 close (s172-s174 were all static): terran.exe not running** (s172 was fully static). Relaunch before any box pick (~35 s): `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `m54g_prep.py` -> `smac_play.py --turns 1` -> `accept_ready.py`; 
  convert [0x926a14]=0, [0x985af0]=67, [0x985af4]=18, eras ds:0x985b90/0x985b9c = -1 (category-skip leg INERT); no clamp
  entry with key 10. Kill a stale winedbg + wineserver BY PID before a relaunch; rounds are NOT continuous across
  reloads.  A traced load is ~10x slow: M54A_LOAD_TIMEOUT=1800.
- A degraded box cannot be rescued by poking. 0x985ac4 bit 0x200 SET (scorer m = 4); mask byte 0x985b10 = 0x08 ->
  ONLY fac3 human (a dword read there = 65288: mask the low byte). **The PANE decides where INSERT lands** (pass the
  index the pane shows: `*(int *)0x6a9480 + 0x3ff3c`).

## TRAPS — the rules (full text: `docs/pick-archive.md`, laws: skill instrument-laws.md)

1. A `fired=` list is the MODEL's prediction, not events; a no-event is evidence only once the bp is CONFIRMED to exist
   there. Gates PREDICT from live memory then confirm with counters; a counter at a site that is BOTH a branch target
   and a loop-completion fallthrough is NOT a leg proof (0x5a7f9f); a gate may only read a field the harness SETS.
2. Check the instrument before believing a no-event: `if *$ecx==X` is a DEREFERENCE and silently never fires; a bp at a
   return-site `mov eax,[ebp-0xc]` prints the OLD eax (break at the NEXT insn, 0x5aa24a); `lea edi,[eax+1]` makes edi
   the MODULUS (read the arg, not $edi); ZERO CALLS can be the GAME — scan /proc for the vptr first.
3. Register semantics live in the ENCODING: `[reg*4+disp]` vs `[reg+disp]` differ by the register's scaling, so a
   condition testing one against the other can never fire; a read-modify-write through a COPIED register evades
   store-shape greps — a hw watchpoint on the FIELD answers "who writes it".
4. gdb printf/script laws: no inferior strings; expressions go in printf ARGUMENTS; an arg-count or `%%` mismatch
   ABORTS the sourced script and DETACHES at the first hit — count specs against args BEFORE the run; a manual call
   frame needs the RETADDR at esp+0 and the arg at esp+4 (reversed = SIGSEGV, box dead); gdb ABANDONS an inferior
   `call` as soon as any bp hits inside it (arm the store bps first, read the effect back from memory).
5. `printf "...\n"` (ONE backslash) prints a newline; TWO prints a LITERAL `\n` and collapses the stream into ONE
   unparsed line that reads as ZERO events. A bp at the insn AFTER `call X` fires AFTER the callee's events — group
   backward; unwatched factions yield legitimately empty groups: skip, do not fail on them.
6. A >90 s gdb census NEVER runs in the foreground (waits cap at 420 s; killing it leaves Wine hung): background + wait,
   or `--rounds <= 4`. Faction upkeep runs in its OWN segment ~1 cycle after turn-end, so a 1-boundary window can close
   mid-cycle — use `--boundaries >= 2`.
7. A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it: Return clears a dialog, a
   BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt — never OK), run
   `m78_mark_clear.normalize_screen()` first, click from OCR word bboxes (TURN COMPLETE (675,416)). `m44_idle` asserts
   TracerPid==0 — never a driver under a census gdb, use m55_boundary.
8. A PASS on a non-discriminating shape is no PASS: compute candidate predictions from the baseline first; refuse the
   shape if they all agree. RE-RUN on a harness race, never edit the floor.
9. base+0xd0 (`credit`) is RECOMPUTED EVERY ROUND (FUN_004e93f0 0x4e9557/0x4e957f = [+0xc0]-[+0xf0]-[+0xe0]) — a poke
   there is undone next turn; gate on round movement and use the per-boundary storage poke 200.
10. A hw watchpoint only REPORTS A VALUE CHANGE (an unchanged store logs NOTHING) AND reports `pc = store + INSTRUCTION
    LENGTH` (0x5aaf67+10 = 0x5aaf71, 0x5aaf79+6 = 0x5aaf7f, 0x59f0c7+10 = 0x59f0d1) — gate on those, never on the store
    address. Count stores with silent bps AT the store; keep the watchpoint as the "any other writer" check; whitelist
    `[New LWP]`, `[Switching to LWP n]`, `Thread N "terran.exe" received signal SIGINT`.
11. A silent bp at the pc a hw watchpoint REPORTS is EATEN by the watchpoint — put the read-back ONE instruction later
    and read memory, not the register. A poke is evidence only if the CONSUMER reads it.
12. A census can leave gdb ATTACHED after it prints its verdict: check `TracerPid` in /proc/<game>/status and kill the
    stale gdb BY PID before calling the box clean.
13. THE TURN DRIVER RETURNS WHILE THE AI UPKEEP IS STILL PLAYING: rc=0 does NOT mean the round's segments are done —
    detach gdb before cur_player returns to the human or the last recomputes go UNLOGGED; wait for cp == human faction.
14. The queue tail holds STALE ids (the shift reaches only `0..pending-1`): never read a queue by "first empty slot" or a
    stale tail as proof an id IS queued; id 0 is Colony Pod AND the empty marker, the sentinel is -39, a negative
    belongs to the TYPE (196 -> -6, 195 -> -3). PRODFLAG (0x4efe60) fires for EVERY record the pass walks (128/322/323/
    194 = FACTION BANDS) — attribute the sweep by its own predecessor; the gate visit arrives a boundary AFTER the sweep.
15. A list cursor read BEFORE the seek is the PREVIOUS cursor (the pump seeks at 0x497717 — print at 0x49771c).
    `milestone.py start <id>` refuses a dirty tree and resets to main: stash, start, pop, THEN rewrite the cursor.
16. Grep objdump case-sensitively (`DWORD PTR`, not `ptr [`).
17. gdb startup/exit chatter must be whitelisted (`DEBUGINFOD_URLS=""`; `^\[Inferior `, `This GDB supports`, `Enable
    debuginfod`, `Debuginfod has`, `To make this setting`) or a zero-unparsed gate FAILs on a clean run.
18. ARM BEFORE ANY SCREEN: setup writes finish before the first OCR-able screen and the CDROM screen is QUIESCENT for
    4 min but only advances on driver input — a true-title wait DEADLOCKS. A hw watchpoint can MISS a change entirely;
    `[New LWP]` after ARMED = threads gdb may not have re-armed; a background census job DIES with its session.
19. `gdb -batch` EXITS the moment a stop has no command left: wineserver sends SIGUSR1 during startup, so a batch census
    MUST carry `handle SIGUSR1 nostop noprint pass` (SIGUSR2/SIGPIPE too) and a ~400-`continue` tail. A bp on a function
    that serves the whole game (the four read wrappers) costs one ptrace stop per read: 25,957 stops starved the load
    driver to ZERO loads — filter by FILE* (`set $savefile` at the loader's entry).
20. A byte-field bit is tested/set with BYTE/register ops (`or al,0x40`), which a dword-immediate scan cannot see —
    scanning `or DWORD PTR [disp],imm` alone finds zero setters and invites the false conclusion that none exists.
21. A "stride conflict" is usually ONE multiply read in two pieces (`lea X,[v+v*2]; shl X,4` = v*48): count the SITES.
    `[reg*4+disp]` beside `[reg+disp]` is usually the same field with the stride folded into the register.
22. A global with readers and ZERO writers of any width is LOAD-TIME data, not a gameplay counter — check the enclosing
    dwords before concluding.

## CLOSING ORDER (exactly — the kickoff carries the same list)

Terse path past ~35 calls: acceptance numbers verbatim, no new prose, no file opened "to double check"; closing is PART
of the milestone. 0 `SESSION_CURSOR.md` (<=600 B: id | acceptance | merged? | next) BEFORE the rest. 1 `## Session <N>`
APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers WITH the command). 2 the `<ID>` block to `NAMED.md` (<=1 KB). 3 this
file patched BY SECTION, `wc -c NEXT_PROMPT.md` <= 15,500. 4 `rsync -a ~/.hermes/skills/smac-cvr-format/
~/reverse/smac/skill/`. 5 `git add -A && git commit -m '<ID>: checkpoint'` then `python3 scripts/gate.py --base main`
GREEN. 6 submit/merge ONLY on a real PASS.

## Report

One screen: what changed, acceptance numbers WITH the command, what is open, next.
