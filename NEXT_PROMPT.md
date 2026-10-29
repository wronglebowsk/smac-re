# NEXT_PROMPT.md — footing for the next session (session 158, 2026-10-29)

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

Survivability: the kickoff's SESSION_CURSOR rule (<= 600 B, written BEFORE any step that can exceed
2 minutes); never `rm`/`git checkout --`; every doc write is an append or a <= 2 KB patch.
## THE LEDGER

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90-M100 (#95/#97-#104, #106-#107), M102 (#109), M104 (#111) — detail in NAMED.md. UNMERGED branches: M83/M84/M84b/M84e/M84f (0x496ad0's -9999 is the DIALOG-CANCEL sentinel, Escape arms [0x6a9e9c+0xa774] = -1; the 0x4d00 queue post is gated at 0x4193b2-0x4193b9 on ds:0x920434 != 0, live 0, so a UI insert posts NOTHING), M86 (0x5a7e73 skips the 64-record band loop unless arg1 == 0x93325c/68/74 = Alloys/SingMec/ConSing), M101 (#108, superseded by M102), M103 (#110, the D-writer, never green in one invocation).
**M90-M104, all in NAMED.md:** the slot IS a tech index 0..88 (STRICTEST-largest draw, tail only arg2==0); TAILOUT 0x5a9698 == BASE + the tail simulated from the per-faction block (block FROZEN within a round); the POST cascade 0x5a9747-0x5aa022 == the prereq-closure ladder (`0x5a9020(a,X,f)` = membership at depth f; FREEZE LADDER INPUTS AT THE TAIL HIT); DIVISOR [fac*8380+0x94e488] == that faction's BASE COUNT, recomputed every round by FUN_00556690; the UI-queued completion pays AND activates in branch A (gate 0x4efa5e, pay 0x4efedd storage +0x40, POP 0x4f037b), 0x4f0ca6 is branch B's pay; the chooser ranks by the DRAW (score<<8 / prereq depth FUN_005a6d40; human LCG at ds:0x999fa0), NOT by score; base+0xd0 credit is recomputed every round by FUN_004e93f0; [0x94d800] is FUN_005aab70's memoized ADVANCE THRESHOLD vs the accumulator [0x94d7f8]; param_2 has ONE producer, FUN_004f34b0 (M99); the multiplier is block A slot 10 (M100/M102); D [0x94d700] is FUN_0059ec00's rebuild from the record list (M103). the record block 0x927a9c+fac*1436 is LOAD-TIME data, nobody appends it in rounds (M104). All legs: skill code-atlas.md.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` —  **re-read it immediately before you arm** (screen fixes live in TRAPS).
2. The writer/flag chain — silent bps or hw watchpoints + a prediction from live memory + a read-back:
   `m94_table_watch.py` (4 hw watchpoints on any 4 dwords), `m97_credit_watch.py`,
   `m100_mult_watch.py`, `m102_rebuild_at_hit.py`, `m103_d_rebuild.py` (all three take `--predict`,
   which prints the model table without touching the game), `m92_tail_census.py`, `m95_pay_sites.py`,
   `m98_advance_budget.py`; each prints pc+new+round+cp, names the writer by containment
   (ghidra_out/index.csv), PREDICTS from live memory then counts, and checks the branch bytes it
   names. Flags via `--help` before inventing one.
3. Self-documenting: `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m65_screen.py --samples 8`,
   `m70_scan_writers.py`, `evidence.py audit [--delete]`/`budget`, `scratch/m71/dis.py LO HI [cap]`
   (objdump window; import it as a module, `dis` clashes with stdlib).
## THE PICK

**M100-M102 (s155-157): the multiplier IS slot 10 of the 11-dword block `&DAT_0094d67c + fac*0x20bc`,
rebuilt from zero every round by FUN_005a15a0 (caller FUN_005a1830(fac) at 0x4dbf8e + 0x520904, cp ==
fac); `m102hit3` PASS 14/14 proved the model AT the store sites and that the D-accrual is NOT
per-round. NAMED.**
**M103 RUN (s158, PR #110 open, UNMERGED, never green in ONE invocation): THE D-WRITER IS FUN_0059ec00**
— zero the 11 dwords (`rep stos` 0x59ec24) then `add [ecx*4+0x94d700],ebx` 0x59ec68 (ecx = fac*2095+key)
for every TYPE==3 entry of the record block; twin inline in FUN_0059ec90; the ONLY 0x94d700 stores in
.text; 4 callers, all setup/new-fac; 0 live events in round windows; model == live D 8/8 on five loads;
`m103_d_rebuild.py --tag m103d2 --boundaries 2` FAIL 6/13, all instrument-side (s158 TRAPS). NAMED.
**M104 ACCEPTED (s159, m104w3 PASS 12/12): NOBODY APPENDS mid-game** — 0 count-change events for facs
1/3/6 across rounds 57->60 while the CONTROL hw watchpoint on [fac3*8380+0x94d7f8] logged 6 writes at
0x5aaef1 (FUN_005aadf0); counts read back [0,6,5,4,3,4,5,3] unchanged for all 8; 0 events at 0x59ec00
or its 4 callers; and m54b_clean.SAV carries the live 100-byte count+TYPE+KEY+VAL image at 0x113b4 /
0x11eec / 0x12fc0 = consecutive at stride 1436 (fac0 base 0x10e18). The block is LOAD-TIME scenario
data, so D and the multiplier's D leg are FROZEN after setup — M101's +10 drift was M100's POKES.
Layout: count +0x00, TYPE +0x04, KEY +0x24, VAL +0x44, stride 4, 8 slots; no .text store reaches any
of them by displacement (46 mentions, all scan loads/cmps). NAMED.
**M105 (THE PICK): who writes the block AT SETUP** — attach gdb at PROCESS START (before the save
load), 4 hw watchpoints on the counts (fac1 0x928038, fac3 0x928b70, fac6 0x929c44) + the CONTROL on
[fac3*8380+0x94d7f8], then load m54b_clean and name the writer by containment: the save loader vs the
1436-byte template copy at 0x57ce48 (FUN_0057c550) / 0x57eee0 (FUN_0057ecf0). THEN: what the TYPE 0 /
TYPE 2 entries are for (fac3 carries (0,2,0) and (2,8,0)) and who consumes them; the 0x92babc category
records; the record index at 0x4b2715.

## STILL OPEN (in priority order)

1. **After M102: band flag [esi+0x94d430] bit 0x40 = 0 for ALL 8 factions -> the M89 second-ask is
   inert, find the setter; ds:0x926bd4 / ds:0x920434 naming; chooser case 7; cursor print at
   **0x49771c**; bit 5 (0x531782); WORD ds:0x98adee (forced-pick key, live 6); the negative-queue
   producer that reaches branch B; what [+0x94d78c] counts; when 0x59f0c7 runs.**
2. **M67's plan-descending LIST order has no code behind it** (zero sites read plan byte `+42`); the
   **`-3 / -6` stride CONFLICT** (`0x984d38 + (-v)*48` vs `+(-v)*16`). Suite: `scripts/gate.py`.

## LIVE FACTS / KIT

- **Box at s159: LIVE** — m54b_clean r60 cp3 hud, counts [0,6,5,4,3,4,5,3], Korolev Center pending 1
  head 2, University pending 0, mults [0x94d6a4] {1:-2, 3:2, 6:-2}, eras ds:0x985b90/0x985b9c = -1
  (the category-skip leg INERT until an era goes >= 0); no clamp entry with key 10. A stale winedbg +
  wineserver (left by a SIGSEGVed manual call frame) must be killed BY PID before a relaunch; rounds
  are NOT continuous across reloads. Recipe (~35 s): `SMAC_SAVE='m54b_clean.SAV' python3
  scripts/m54a_load.py --relaunch` -> `m54g_prep.py` -> `smac_play.py --turns 1` ->
  `m57_ui_enqueue.py --base-index 18 --cell-item 2 --inserts 1` -> `accept_ready.py`.

  A degraded box cannot be rescued by poking. 0x985ac4 bit 0x200 SET
  (scorer m = 4); mask byte 0x985b10 = 0x08 -> ONLY fac3 human (a dword read there = 65288: mask the
  low byte). X focus law: see TRAPS. **The PANE decides where INSERT lands** (pass the index the pane
  shows: `*(int *)0x6a9480 + 0x3ff3c`).
## TRAPS

- **The `fired=` list on a `LADDER-MISMATCH` line is the MODEL's prediction, not observed events** (s148); a no-event at an apply site is evidence only once a breakpoint is CONFIRMED to exist there (4 lacked one until s148). Gates must PREDICT from live memory, then be confirmed by counters; a counter at a site that is BOTH a branch target and a loop-completion fallthrough is NOT a leg proof (0x5a7f9f); a gate may only read a field the harness SETS (m92 G8).
- **Check the instrument before believing a no-event or a wrong field:** an f-string bp condition that emits `if *$ecx==X` is a DEREFERENCE and silently never fires (m95pay1/2); a bp at a `mov eax,[ebp-0xc]` RETURN site prints the OLD eax — break at the NEXT instruction (0x5aa24a; m96human1 read idx=0); `lea edi,[eax+1]` @0x5aa21a makes edi the MODULUS on the rand path, so a bp at 0x5aa232 printing `$edi` gets score+1, not the faction — read `*(int *)($ebp+8)`; name every printed field the way the parser asks (m96human1 G4/G9/G11 were key names, not the game). ZERO CALLS can be the GAME: scan /proc for the function's vptr first (`scratch/m84d/probe3.py`).
- **Register semantics live in the encoding, not the name:** `[reg*4+0x98adb8]` means the register holds `tid*13`, `[reg+0x98adb8]` the BYTE address `tid*52`; a condition testing such a register against the bare tid can NEVER fire. A read-modify-write through a COPIED register (`mov ax,[x]; or al,4; mov [x],ax`, 0x4efe60) evades store-shape greps — a HARDWARE watchpoint on the FIELD answers "who writes it" in one run.
- **gdb printf/script laws (skill references/gdb-command-list.md + instrument-laws.md):** no inferior
  strings; template expressions go in printf ARGUMENTS, never the format; a printf ARG-COUNT mismatch
  or a stray `%%` in a TMPL line ABORTS the sourced script and DETACHES at the first hit (m103d1/d2,
  m102hit1) — count the specs against the args in the harness BEFORE the run; a manual call frame needs
  the RETADDR at esp+0 and the arg at esp+4 (reversed = SIGSEGV, box dead, m103d5); gdb ABANDONS an
  inferior `call` as soon as ANY breakpoint hits inside it — arm the store bps first, read the effect
  back from memory (m103d3).
- **A >90 s gdb census NEVER runs in the foreground** (the terminal caps waits at 420 s; killing it mid-run leaves Wine hung, round frozen, s143): background + `process_manage wait`, or keep `--rounds <= 4`. **Faction upkeep runs in that faction's OWN segment ~1 cycle after your turn-end: a 1-boundary window can close mid-cycle (m95pay2) — use `--boundaries >= 2`.**
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it:** Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt — never OK); run `m78_mark_clear.normalize_screen()` first; vision coords are SCALE-SHIFTED, click from OCR word bboxes (TURN COMPLETE (675,416)). `m44_idle` asserts TracerPid==0 — never a driver under a census gdb, use m55_boundary.
- **A PASS on a shape that cannot discriminate is not a PASS:** compute candidate predictions from the baseline first; refuse the shape if they all agree. RE-RUN on a harness race, never edit the floor.
- **base+0xd0 (`credit`) is RECOMPUTED EVERY ROUND** (M97 FUN_004e93f0 0x4e9557/0x4e957f = [+0xc0] -
  [+0xf0] - [+0xe0]; "init-only" RETRACTED) — a poke there is undone next turn; gate on round movement
  and use the per-boundary storage poke 200.
- **a gdb HARDWARE watchpoint only REPORTS a VALUE CHANGE** (unchanged store logs NOTHING,
  m97credit2) AND reports `pc = store + INSTRUCTION LENGTH` (m98budget2: 0x5aaf67+10 = 0x5aaf71,
  0x5aaf79+6 = 0x5aaf7f, 0x59f0c7+10 = 0x59f0d1) — gate on those, not on the store address. Count
  stores with silent bps AT the store; keep the watchpoint as the "any other writer" check; whitelist
  `[New LWP]`, `[Switching to LWP n]` and `Thread N "terran.exe" received signal SIGINT`.
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

## CLOSING ORDER (exactly — the kickoff carries the same list)

Terse path past ~35 calls: acceptance numbers verbatim, no new prose, no file opened "to double
check"; closing is PART of the milestone. 0 `SESSION_CURSOR.md` (<= 600 B: `<ID> | acceptance |
merged? | next command`) BEFORE the rest. 1 `## Session <N>` APPENDED to `SESSION_NOTES.md`
(<= 2 KB, numbers WITH the command). 2 the `<ID>` block APPENDED to `NAMED.md` (<= 1 KB). 3 this
file patched BY SECTION, `wc -c NEXT_PROMPT.md` <= 15,500. 4 `rsync -a
~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/`. 5 `git add -A && git commit -m '<ID>:
checkpoint'` then `python3 scripts/gate.py --base main` GREEN. 6 submit/merge ONLY on a real PASS.

## Report

One screen: what changed, acceptance numbers WITH the command, what is open, next pick.