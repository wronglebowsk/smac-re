# NEXT_PROMPT.md — footing for the next session (session 173, 2026-10-31)

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

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90-M100 (#95/#97-#104, #106-#107), M102 (#109), M104 (#111), M105
(#112), M106 (#113), M110-M112 (#116), M113 (#121), M116 (#126), M117 (#127), exit-code fix (#128), M118 (#129),
M119-M123 (#130). UNMERGED: M83/M84 family (-9999 at 0x496ad0 = DIALOG-CANCEL; 0x4d00 post gated at 0x4193b2 on
ds:0x920434 != 0, live 0), M86 (0x5a7e73 skips the band loop unless arg1 == 0x93325c/68/74), M101 (#108, superseded by
M102), M103 (#110, never green), M109 (gates answered, model void). **M90-M104's registry summary now lives in
`docs/pick-archive.md`; the semantics themselves in `NAMED.md`, the legs in `skill/references/code-atlas.md`.**

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
- **M166-M168 (m166_m168_roles.py, all PASS):** 0x94d434 is consumed as an ORDER (92 `cmp` vs 2/4/5/6/7) from the
  7-dword table 0x926a7c with the top entry excluded (`-1` at 0x59ac72); the 20-byte struct at 0x94d80c = a HEADER dword
  + a 4-dword PAYLOAD written by a different, shared writer set; 0x94d488 = a DERIVED CACHE (22 writes / 9 functions).
- **M169-M171 (m169_m171_aggregate.py, all PASS):** 0x926a7c is TOTALLED (count ds:0x9204ac, sum ds:0x9204c4) in a
  per-faction loop at stride 0x20bc inside **FUN_00531df0** (6459 B, 1905 insns, 17 call sites) — the aggregator, which
  gates on the M163 rank as `cmp [ebx+0x94d434],0x5`; and **FUN_004dc100 (647 B) is a BIT-DECODER**: one byte in AL ->
  four boolean dwords (+0x94d810/14/18/1c from al&1/2/4/8), header tristate (+0x94d80c = 1/-1/0 from al&0x10/0x20), and
  al&0x40 -> `or [+0x94d430],0x800000`.
- **M172-M174 (m172_m174_savewriter.py, all PASS):** FUN_004dc100 is a **SAVE-SECTION WRITER** — its 2 callers are arg-free dispatch legs (FUN_00512b40 0x51500f, FUN_00516b80 0x517eb6); the byte is the shared scratch **ds:0x99aa38**  a caller argument (M171's "arrives in AL" retracted): PACK leg 0x4dc1a4-0x4dc279 rewrites 22 `or/and al,ah` from the struct + band bits, writes via 0x6267a5, 0x4d9fb0 has exactly 4 callers (0x4dc100/0x4dc390/0x4e0260/0x5a2930). Count/sum 0x9204ac/0x9204c4: consumers 0x53346c (inside FUN_00531df0: count<2 -> table[ebx] >= 3*(sum+table[ecx]) -> rank<6), 0x53a9cc (FUN_0053a9c0), 0x54d30d (FUN_00546800); sum's only reader 0x533478. Header 0x94d80c: 7 tests in 4 fns + 7 arithmetic uses (`sub` x6, `add` x1) = a 1/0/-1 **signed modifier** in scoring; the aggregator reads it as |value|.
- Pick from: FUN_00531df0's 17 call sites (who asks for the aggregate); FUN_0041a8f0's 0x41a9xx block (what UI state builds the byte bit by bit); consumers of ds:0x920720 (the count's partner); the save-band siblings 0x4dc390/0x4e0260/0x5a2930 (what each writes).
  tristate header's 7 test sites (M167); FUN_00531df0's 17 call sites.

## LIVE FACTS / KIT

- **BOX DOWN at s172 close: terran.exe not running** (s172 was fully static). Relaunch before any box pick (~35 s): `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `m54g_prep.py` -> `smac_play.py --turns 1` -> `accept_ready.py`; 
  convert [0x926a14]=0, [0x985af0]=67, [0x985af4]=18, eras ds:0x985b90/0x985b9c = -1 (category-skip leg INERT); no clamp
  entry with key 10. Kill a stale winedbg + wineserver BY PID before a relaunch; rounds are NOT continuous across
  reloads. Recipe (~35 s): `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `m54g_prep.py` ->
  `smac_play.py --turns 1` -> `accept_ready.py`. A traced load is ~10x slow: M54A_LOAD_TIMEOUT=1800.
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
