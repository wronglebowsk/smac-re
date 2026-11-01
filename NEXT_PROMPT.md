# NEXT_PROMPT.md — footing for the next session (session 185, 2026-11-02, M217-M221 all PASS)

Structure: RULES + live footing. Detail on disk: `docs/pick-archive.md` (narrative M90-M123, the s171-s183
milestone lines VERBATIM, + FULL trap text), `NAMED.md` (semantics), `skill/references/instrument-laws.md` (laws).
Read the archive only for the section picked.

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor, and its summaries die on the output cap (s113/s114 hit 259,232/262,144
mid-sentence). **Whatever is not finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 25 `git add -A && git commit`** — the next turn may be the
  truncated one, so every later step must leave a committed file.
- **30-40** STOP MEASURING: an acceptance that is not green IS the finding — write the blocker and the failing number,
  merge nothing, close.
- **40-50** closing order, TERSE: notes <= 2 KB, NAMED block <= 1 KB, this file patched BY SECTION, never rewritten.

Survivability: cursor <=600 B before any >2-min step; never `rm`/`git checkout --`; doc writes are appends or small
patches. **Batch size (s172/s178, s184: FIVE static milestones through ONE census script fits; box milestones
go 1 per batch). The binding cap is doc headroom, not capability.**

## THE LEDGER

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90-M100 (#95/#97-#104, #106-#107), M102 (#109), M104 (#111),
M105-M106 (#112/#113), M110-M113 (#116/#121), M116-M118 (#126-#129), M119-M123 (#130), M163-M171 (#138-#140),
M172-M174 (#141), M175-M177 (#145), M178-M180 (#147, docs #149/#150), M182-M184 (#151),
M185-M187 (#152), M188-M190 (#154), M191-M193 (#157), M194-M196 (#158), M197-M200 (#159),
M201-M204 (#161), M205-M208 (#162), M209-M212 (#163), M213-M216 (#164), M217-M221 (#165), s175 cap triage (#153).
UNMERGED: M83/M84 family (-9999 = FUN_00496ad0's 'unset' return per M212; 0x4d00 post gated at 0x4193b2 on
ds:0x920434 != 0, live 0), M86 (0x5a7e73 skips the band loop unless arg1 == 0x93325c/68/74), M101 (#108,
superseded), M103 (#110, never green), M109 (gates answered, model void). Summaries: `docs/pick-archive.md`,
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
4. Self-documenting: `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m65_screen.py --samples 8`.

## THE PICK — index (detail: `docs/pick-archive.md`)

- **Laws that decide field questions:** `f*8380` is DECIMAL 8,380 = 0x20BC = 2095 dwords; a decompiler `arr[i*N]` is
  an ELEMENT index (x4 for bytes); a record field may appear as `[reg+disp]` OR the folded `[reg*4+abs]` - count BOTH
  before saying "no site reads X"; a hw watchpoint only reports a CHANGE; a gate may only read a field the harness SETS.
- **Where the map lives now:** `docs/field-atlas-faction.md` = the 20 most-referenced faction-block displacements with
  refs/writes/consts/tests/functions (M143-M162). Start there before re-deriving a field.
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
- Pick from: WHO dispatches the dialog's +0x4c (466 installs, 0 direct calls; all 12 image-wide
  `call [reg+0x4c]` sites belong to other hierarchies - falsifier = a live vtable read at a click, box);
  who FILLS the dialog's this+0x3098 list (0 add-sites carry that displacement: the 6 add-sites that
  take the list from a loaded value are FUN_00403b00/0040f830/004105b0/00411840/00415d10/00607eca -
  census their callers and what list pointer each passes); who CALLS FUN_005f5a11 if its 3 fields are
  write-only (the FUN_005f3f5b switch cases + any block copy/`rep movs` spanning 0x21d0..0x2260); what
  FUN_00459bb0 is (1722 B, 1 callsite, 0 slots: who calls it, what reads the 0x774c38 table); the
  panel's row pipeline (FUN_005f90d7's 7 indirect calls - which slots it dispatches on the rows at
  +0xaac/+0x15f8 - and what row-vmethod +0x30 FUN_005fb1a5 does with the 9 groups); M181's control
  (box).
## LIVE FACTS / KIT

- **BOX state CARRIED from s174e (s175/s178 spent no box time, so NOT re-verified):** terran.exe 319926, y2153 r53,
  University Base (28,42), 6 units HELD, TracerPid 0 — not this session's descendant, so read `/proc/mem` with
  `sudo -n` (yama `ptrace_scope=1`). Run `scripts/smac_preflight.py` before arming. Launch recipe + cold-box
  timing: skill `references/wine-operations.md`.
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
file patched BY SECTION, `wc -c NEXT_PROMPT.md` <= 15,300 BYTES (what `evidence.py budget` prints; the kickoff's
cap-triage trigger — closing at the gate's 16,000 FAIL or at 15,500 hands the next fire a docs-only split).
4 `rsync -a ~/.hermes/skills/smac-cvr-format/
~/reverse/smac/skill/`. 5 `git add -A && git commit -m '<ID>: checkpoint'` then `python3 scripts/gate.py --base main`
GREEN. 6 submit/merge ONLY on a real PASS.
