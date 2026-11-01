# NEXT_PROMPT.md — footing for the next session (session 177, 2026-10-31)

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
M172-M174 (#141), M175-M177 (#145), M178-M180 (#147, docs #149/#150), M182-M184 (#151), M185-M187 (#152),
M188-M190 (#154), M191-M193 (#157), M194-M196 (#158), s175 cap triage (#153). UNMERGED: M83/M84 family (-9999 at 0x496ad0 = DIALOG-CANCEL; 0x4d00 post gated at 0x4193b2 on
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
- **Merged-era footing s171-s175 (M163-M190, all PASS) is ARCHIVED:** per-field semantics and the
  milestone lines live in `NAMED.md` (M175-M190) + `docs/pick-archive.md`; census outputs
  `evidence/m175_m177_aggcallers.txt`, `m178_m180_scratchband.txt`, `m182_m184_bandrecord.txt`,
  `m185_m187_visits.txt`, `m188_m190_uses.txt`; field map `docs/field-atlas-faction.md`. Read them there.
- **s175-s177 (M188-M196, all PASS): rows in `NAMED.md` M188-M190 / M191-M193 / M194-M196; census outputs
  `evidence/m188_m190_uses.txt`, `m191_m193_channels.txt`, `m194_m196_channels.txt`.** Short of the three
  newest: `0x626634` is the **10-slot CHANNEL PUBLISH** (guard `arg1<=9`; writes `A[slot]@0x999fcc` /
  `B[slot]@0x999ff4`; zeroes then appends arg2 into `0x99a01c + arg1*0x100`; a negative arg3/arg4 takes the
  staging pair, and `0x99a01c + 10*256 == 0x99aa1c`, so the staging record IS slot 10) — 1584 sites in 190
  functions. Its slots are consumed by POINTER PASSING, not by reads: the window is 113 sites / 31 fns of
  which 93 push the base or a slot address; 16 callees receive it (6 = the C string layer, 2 indirect) and
  FUN_00631afb / FUN_00632cad are the formatters that take slot addresses; live slots 0-4 hold one faction's
  sentence parts ('disciplined'/'Provost'/'Zakharov'/'University'/'Mission Year 2150'), 5-9 empty, and slot 7
  is WRITE-ONLY (7 publishers, 0 address pushes). `ds:0x920700` is a 13-value MODE CODE (2 writers, 12 tested
  values up to 0xd, live 0, ZERO strings in the 4 functions that touch it; FUN_00544530 also writes 0x997120
  x28 and the staging pair x14/x14). `[reg*4+0x94d448]` is NOT a pointer — 365/466 scaled sites carry the
  2095-fold (address = 0x94d448 + 8380*S + 4*C), all 297 tests are `test`+mask (0 cmp, widest 5 bits), 0/139
  loads is dereferenced and 0/66 live dwords lie in the mapped range; **M196 RETRACTS M190's "carriers
  0x55540a/0x55580f store addresses"** (bit ops on the flag word; the 0x5553d2 lea is the store-through alias
  of the 0x5553df store).
- Pick from: what FUN_00544530 IS — its call sites and what the 13 values switch over (it writes 0x997120 x28
  and the staging pair, so it may be the mode the aggregate pass's gate waits on); what 0x631afb / 0x632cad
  substitute (they receive slot addresses; 1076 / 288 insns); the text source behind slot 7's 7 publishes (the
  calls at 0x5808b0, 0x580a60, 0x426680); M181's positive control (box).
## LIVE FACTS / KIT

- **BOX state CARRIED from s174e (s175 spent no box time, so NOT re-verified):** terran.exe 319926, y2153
  r53, University Base (28,42), 6 units HELD, TracerPid 0 — not this session's descendant, so read
  `/proc/mem` with `sudo -n` (yama `ptrace_scope=1`). Run `scripts/smac_preflight.py` before arming.
  Launch recipe + cold-box timing: skill `references/wine-operations.md`.
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
