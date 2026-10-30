# NEXT_PROMPT.md — footing for the next session (session 171, 2026-10-29)

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor (`auxiliary.compression: auto` -> the same 262k model)
and its summaries die on the output cap (sessions 113/114 hit 259,232/262,144 mid-sentence).
**Whatever is not finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 25 `git add -A && git commit`** — the
  next turn may be the truncated one, so every later step must leave a committed file.
- **30-40** STOP MEASURING: an acceptance that is not green IS the finding — write the blocker and
  the failing number, merge nothing, close.
- **40-50** closing order, TERSE: notes <= 2 KB, NAMED block <= 1 KB, this file patched BY SECTION
  (budget FAILs at 16,000 chars — stay <= 15,500), never rewritten.

Survivability: cursor <= 600 B before any >2-min step; never `rm`/`git checkout --`; doc writes are
appends or <= 2 KB patches.
## THE LEDGER

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90-M100 (#95/#97-#104, #106-#107), M102 (#109), M104 (#111), M105 (#112), M106 (#113), M110-M112 (#116, includes the M110 map) — detail in NAMED.md. UNMERGED: M83/M84 family (-9999 at 0x496ad0 = DIALOG-CANCEL; 0x4d00 post gated at 0x4193b2 on ds:0x920434 != 0, live 0), M86 (0x5a7e73 skips the band loop unless arg1 == 0x93325c/68/74), M101 (#108, superseded by M102), M103 (#110, never green), M109 (gates answered, model void).
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

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` —  **re-read it immediately before you arm** (screen fixes live in TRAPS).
2. The writer/flag chain — silent bps or hw watchpoints + a prediction from live memory + a read-back:
   `m94_table_watch.py` (4 hw watchpoints on any 4 dwords), `m97_credit_watch.py`,
   `m100_mult_watch.py`, `m102_rebuild_at_hit.py`, `m103_d_rebuild.py` (all three take `--predict`,
   which prints the model table without touching the game), `m92_tail_census.py`, `m95_pay_sites.py`,
   `m98_advance_budget.py`; each prints pc+new+round+cp, names the writer by containment
   (ghidra_out/index.csv), PREDICTS from live memory then counts. Flags via `--help` first.
3. Self-documenting: `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m65_screen.py --samples 8`,
   `m70_scan_writers.py`, `evidence.py audit [--delete]`/`budget`, `scratch/m71/dis.py LO HI [cap]`
   (objdump window; import it as a module, `dis` clashes with stdlib).
## THE PICK

**M100-M106, in NAMED.md:** multiplier = block A slot 10, rebuilt per round (M100/M102); D = FUN_0059ec00 off
the block's TYPE==3 entries (M103); nobody appends the block in rounds (M104); it is BUILT AT PROCESS START by
FUN_005791c0 (M105, 17/17). **M106 ACCEPTED (m106r7 PASS 15/15): the load restores by read() INTO the region** — kernel copy_to_user, no
ring-3 store, invisible to a hw watchpoint; the .SAV fd arrives via SCM_RIGHTS (TAIL-AND-EOF LAW).
Harness `scripts/m106_load_restore.py`; a traced game is ~10x slow, so pass M54A_LOAD_TIMEOUT=1800.
**M111/M112 RESOLVED; M113 CLOSED; M114 DONE (s171) — the .SAV map is anchored and the restore is 1:1.**
Trailer: the last 156 B ARE read — the 6-site per-entity loop (0x59666d/0x5966c1/0x596715/0x596769/0x5967bd/
0x59683b) -> heap 0x915758..0x3c4b3f8. **M110's "0..242,383 / 156 B unread" RETRACTED.**
Map (poke anchors, `k = dest - off` constant inside a region): block A k=0x94D104; block B base **file 67,852** ->
0x927590 (not 67,840); grid k=0x40925B0 (90,112 B at 0x40a6660); post-map section k=0x95BD51;
196,608/212,992 k=0x95BF49; **52 records: file 222,783 -> 0x933278** (k=0x926635). Boundaries bracketed 66,048 ->
0x95d304 / 68,096 -> 0x927684 and 171,192 -> 0x40bc268 / 173,240 -> 0x986209.
Restore fidelity (diff vs file, 12 windows): **10/12 byte-identical**; rewriting is confined to the map header TAIL
(81,408..82,100, 665 B) and the block A TAIL (67,080..67,143, 16-B stride, 2 B per hit); the 52-record array has
exactly 2 differing dwords (222,831 cleared, the poked field at 223,152 normalised 0xC0->0xD6).
LAW: identify bytes by POKING a marker and finding it in memory (a census over-runs, a subset-sum is
underdetermined); cap at 60 markers.

## STILL OPEN

1. **After M102: band flag [esi+0x94d430] bit 0x40 = 0 for ALL 8 factions -> the M89 second-ask is
   inert, find the setter; ds:0x926bd4 / ds:0x920434 naming; chooser case 7; cursor print 0x49771c;
   bit 5 (0x531782); WORD ds:0x98adee (forced-pick key, live 6); the negative-queue producer reaching
   branch B; what [+0x94d78c] counts; when 0x59f0c7 runs.**
2. **M67's plan-descending LIST order has no code behind it** (zero sites read plan byte `+42`); the
   **`-3 / -6` stride CONFLICT** (`0x984d38 + (-v)*48` vs `+(-v)*16`).

## LIVE FACTS / KIT

- **Box at s171: terran.exe pid 1573718, m54b_clean LOADED (counts 67/18), no gdb, no driver**,
  version [0x985dbc]=9, convert
  [0x926a14]=0, [0x985af0]=67, [0x985af4]=18, eras ds:0x985b90/0x985b9c = -1 (category-skip leg INERT);
  no clamp entry with key 10. A stale winedbg + wineserver must be killed BY PID
  before a relaunch; rounds are NOT continuous across reloads. Recipe (~35 s): `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` -> `m54g_prep.py` -> `smac_play.py --turns 1` -> `accept_ready.py`.

  A degraded box cannot be rescued by poking. 0x985ac4 bit 0x200 SET
  (scorer m = 4); mask byte 0x985b10 = 0x08 -> ONLY fac3 human (a dword read there = 65288: mask the
  low byte). X focus law: see TRAPS. **The PANE decides where INSERT lands** (pass the index the pane
  shows: `*(int *)0x6a9480 + 0x3ff3c`).
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

## CLOSING ORDER (exactly — the kickoff carries the same list)

Terse path past ~35 calls: acceptance numbers verbatim, no new prose, no file opened "to double
check"; closing is PART of the milestone. 0 `SESSION_CURSOR.md` (<=600 B: id | acceptance | merged?
| next) BEFORE the rest. 1 `## Session <N>` APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers WITH
the command). 2 the `<ID>` block to `NAMED.md` (<=1 KB). 3 this
file patched BY SECTION, `wc -c NEXT_PROMPT.md` <= 15,500. 4 `rsync -a
~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`. 5 `git add -A && git commit -m '<ID>:
checkpoint'` then `python3 scripts/gate.py --base main` GREEN. 6 submit/merge ONLY on a real PASS.

## Report

One screen: what changed, acceptance numbers WITH the command, what is open, next.
