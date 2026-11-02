# NEXT_PROMPT.md — footing for the next session (session 205, 2026-11-02, **M262-M264 DONE: the view-table entries 1..7 are ALLOCATED at startup (7 × 0x22480, stored through a cursor — M260 retracted); the LOAD never re-derives the per-faction band; FUN_005be090 is operator-new and ds:0x9965b8 is a linear record cursor**)

Structure: RULES + live footing. Overflow on disk: `docs/pick-archive.md` (narrative + blocks moved
VERBATIM — read only the section picked), `NAMED.md` (semantics), skill `references/instrument-laws.md`
(laws).

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor, and its summaries die on the output cap (s113/s114 hit 259,232/262,144
mid-sentence). **Whatever is not finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 15 `git add -A && git commit`** (s187: a fire hit 167k
  context at call 25 with zero commits — a fire costs ~7k tokens per call) — the next turn may be the
  truncated one, so every later step must leave a committed file.
- JSON only: no XML tags inside tool arguments. Writes over ~4 KB drift and are rejected as a missing `path` — expect one
  retry, then re-emit the same content as pure JSON (do NOT fragment into many tiny writes). Branch + skeleton commit
  BEFORE probing; s189 measured the skeleton landing at 108k context instead of 167k.
- **30-40** STOP MEASURING: an acceptance that is not green IS the finding — write the blocker and the failing number,
  merge nothing, close.
- **40-50** closing order, TERSE: notes <= 2 KB, NAMED block <= 1 KB, this file patched BY SECTION, never rewritten.

Survivability: cursor <=600 B before any >2-min step; never `rm`/`git checkout --`; doc writes are appends or small
patches. **Batch size (s172/s178, s184: FIVE static milestones through ONE census script fits; box milestones
go 1 per batch). The binding cap is doc headroom, not capability.**

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>` from merged history. BUILD ⇒
build that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a
census claim; no box time, no `/proc`, no gdb; the box-debt pre-step does NOT apply; title commit+PR `B<n>`);
ANALYSE ⇒ pick from this file. **B4 DONE (s203)** 9/9 on `evidence/m44d_idle.json` (`sim/base.py` +
`sim/economy.py`; the base name field is 32 B, not 20; text `NAMED.md` §B4). **B3 DONE (s199)** 6/6 (§s200).
**Next rung B5 = units/movement.**

## THE LEDGER

Merged M54A-M255 + B0-B3 (through #190); UNMERGED M83/M84, M86, M101, M103, M109 and **M241 (#180, 2/5,
PR open)**. Full list with PR numbers and reasons VERBATIM: `docs/pick-archive.md` §trim-s202; per-id
semantics in `NAMED.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it immediately before you arm** (screen fixes live
   in TRAPS).
2. Writer/flag chain — silent bps or hw watchpoints + a prediction from live memory + a read-back:
   `m94_table_watch.py` (4 hw watchpoints on any 4 dwords), `m97_credit_watch.py`, `m100_mult_watch.py`,
   `m102_rebuild_at_hit.py`, `m103_d_rebuild.py`, `m92_tail_census.py`, `m95_pay_sites.py`, `m98_advance_budget.py`, `m117_gate_take.py`; each
   prints pc+new+round+cp and names the writer by containment (ghidra_out/index.csv). `--predict` prints the model
   table without touching the game. Flags via `--help` first.
3. Static-first kit (s171, zero box time): `field_census.py` (a displacement/global's shape from its addressing form
   and index arithmetic), `name_global.py` (every reader/writer of a global + containment), `m118_flag_never_set.py`
   (is a gate even satisfiable: test sites, OR immediates, register-level bit ops, and whether any save carries the
   bit), `fn.py 0xADDR` (decompiled body), `scratch/m71/dis.py LO HI [cap]` (objdump window; import as a module, `dis`
   clashes with stdlib), `evidence.py audit [--delete]|budget`.
4. Self-documenting: `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m65_screen.py --samples 8`.

## THE PICK — index (detail: `docs/pick-archive.md`)

- **Where things live:** map/terrain footing is now `MAP_FORMAT.md` (44-B record table + the loader/allocator
  family) and FOOTING.md's terrain line; faction fields are `docs/field-atlas-faction.md` (20 hottest
  displacements, M143-M162). Start there before re-deriving a field.
- ANSWERED (do not re-pick): s187-s205 — M227-M237, **B1-B4**, M240-M264 (M241 FAIL 2/5, #180 open;
  the save-codec chain, the region generator + its ORDER, the verdict codes and their guards, the worth
  test's operands, the 12-array per-region family, the economy rung, the per-faction mask band, the
  view table + its startup allocation, the allocator and the record cursor, the 0x679f98 class).
  Numbers VERBATIM: `NAMED.md` per-id, §s196-§s205; the s204 RESULT block moved VERBATIM to
  `docs/pick-archive.md` §s205. FUN_005f3f5b is NOT open: M220 has it (slot +0x15c of 0x6717cc, 70
  installs, called directly twice by FUN_00406990); s205 counted 28 image-wide `call [reg+0x15c]` sites.
- RESULT (s205): **the view-table entries 1..7 ARE allocated** — FUN_00580260's loop at 0x580392 walks
  esi 0x7cded0 → `cmp esi,0x7cdeec`/`jl`, step 4 (7 iterations), `push 0x22480 ; call 0x64bc20` then
  `push 1 ; mov ecx,eax ; call 0x469650`, and stores with the POINTER-ARITHMETIC `mov [esi],eax` at
  0x5803bb; 0 lands there only on the alloc-failure path, so M260's "zeroes entries 1..7" and "the
  ~140 KB views are not allocated" are RETRACTED (0x224b8 = 0x22480 + 0x38, heap header, INFERRED).
  Band census: 426 mentions, 1 store naming it, 39 indexed mentions in 12 functions, 0 indexed stores,
  4 of 35 address-of sites escape and all 4 hand out &DAT_007cdecc (G1-G5). **The LOAD trusts the file's
  band bytes**: the writer set re-derives to M259's 8 functions / 10 stores + FUN_0051c750's walk store,
  and the depth-9 forward closure of the 6 load-path functions (FUN_00596850/FUN_00597a70 + their 4
  callers FUN_00597ce0/FUN_00597ee0/FUN_00598250/FUN_00598340) is 276 functions meeting it in ZERO, with
  no writer in any vtable slot (G6-G8); FUN_00583c70 (writer 0x583e1d) has ZERO references image-wide.
  **FUN_005be090 is operator-new** (72 B → FUN_00649e00 → FUN_00649e70 with the heap handle ds:0x99d5f8;
  the NULL path reports "FATAL ERROR" / "Windows has run out of virtual memory; the game will exit…"
  through the global function pointer ds:0x671320): 0 vtable slots, 119 sites in 74 functions, and the
  footing's "13 [reg+4] sites" are store-after-alloc sites — 14 in 13 functions (G9-G10). ds:0x9965b8 is
  a LINEAR RECORD CURSOR: FUN_005dbb5f stamps a blank record (10 zero stores + `mov byte ptr [ecx+0x8],0x9`)
  and bumps +0x2c, FUN_005dbbe6 rewinds −[rec+0x10]*[rec+0x14] and frees [rec+4] via FUN_0064a7f0,
  FUN_005dbdc0 is the filler (mallocs w*h at 0x5dc1ed into [rec+4], then advances by the same product)
  (G11). `python3 scripts/m262_m264_census.py` -> `SUMMARY M262/M263/M264: 11/11 gates PASS` (rc=0,
  3.7 s, one green invocation; inv 1 was 10/11 on a count copied from a truncated probe print — moved
  only after an objdump corpus said 39/12).
- Pick from (ANALYSE fires; the next BUILD fire takes **B5** — units/movement — from `BUILD_SPINE.md`):
  WHO dispatches the dialog's +0x4c (466 installs, 0 direct calls, all 12 image-wide `call [reg+0x4c]`
  sites belong to other hierarchies — falsifier = a live vtable read at a click, box); **does
  `FUN_0057ecf0` also run on a LOAD** (new from M255, box: bp the `FUN_005b2970` entry, load a save —
  the box is DOWN, cold relaunch >9 min); **what the row stride 188 means** (new from M257: `esi =
  2*region + 188*fac`, regions 94..127 pass the next row — one live read of both indexings of `0x94eaa8`
  settles it; box); **what the 7 allocated view blocks are FOR** (new from M262: entries 1..7 hold
  0x22480-B blocks built by FUN_00469650, yet every indexed use only tests them for non-null and only
  entry 0 is used as a field base (+0x1dd70/+0x1dd84/+0x53b4) — static lead: compare FUN_00469650's own
  field writes with the static view ctor FUN_00518820's, and read the 12 entry-1 readers, esp.
  FUN_004412a0 (8) and the teardown callee FUN_00479e90 (69 B)); **why FUN_00583c70 exists with ZERO
  references** (new from M263: it allocates through FUN_00582000 and writes the band at 0x583e1d, but no
  call, imm32 or vtable slot names it — static lead: the PE relocation table, and the target set of every
  computed `call [reg]` whose register could hold it).
## LIVE FACTS / KIT

- **BOX**: DOWN as of s202 (`ps` shows no terran.exe). Cold relaunch >9 min: `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` as a TRACKED background job; `sudo -n
  python3 scripts/smac_preflight.py` (yama ptrace_scope=1 ⇒ `/proc/<pid>/mem` needs sudo) before arming.
  Recipe, cold timing, the degraded-box poke facts (0x985ac4 bit 0x200, mask byte 0x985b10, the PANE
  decides where INSERT lands) and the full state dumps VERBATIM: skill `references/wine-operations.md`,
  `docs/pick-archive.md` §s198 + §s199 + §trim-s202.

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
4-5. gdb printf/script laws — VERBATIM text moved to `docs/pick-archive.md` at s191 (also in the skill's
   instrument-laws.md): no inferior strings; expressions go in printf ARGUMENTS and specs must match them (a
   mismatch ABORTS the sourced script and DETACHES at the first hit); a manual call frame needs the RETADDR at
   esp+0 and the arg at esp+4; gdb ABANDONS an inferior `call` once any bp hits inside it; ONE `\n` prints a
   newline, TWO prints a literal one and the stream reads as ZERO events; a bp at the insn AFTER `call X` fires
   AFTER the callee's events — group backward, and unwatched factions legitimately yield empty groups.
6. A >90 s gdb census NEVER runs in the foreground (waits cap at 420 s; killing it leaves Wine hung): background + wait,
   or `--rounds <= 4`. Faction upkeep runs in its OWN segment ~1 cycle after turn-end, so a 1-boundary window can close
   mid-cycle — use `--boundaries >= 2`.
7. Dialogs swallow every click and turn-end key while the HUD bar reads THROUGH them: Return clears a dialog, a
   BUILD/base PANE needs Escape (bare-map Escape raises the quit prompt — never OK); normalize first
   (`m78_mark_clear.normalize_screen()`), click from OCR word bboxes; `m44_idle` asserts TracerPid==0 — never a
   driver under a census gdb (use m55_boundary). Verbatim: `docs/pick-archive.md`, s191 block.
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
20-22. byte-field BIT OPS vs dword scans; a "stride conflict" is ONE multiply read in two pieces; a global
    with ZERO writers is LOAD-TIME data — verbatim: `docs/pick-archive.md` §s198.
23. A VALUE SAMPLER IS NOT A STORE CENSUS (a same-value store leaves no trace) and a census PARSER is not a
    log — VERBATIM laws: skill `references/instrument-laws.md` (M241/M242, s192-s193).

## CLOSING ORDER (exactly — the kickoff carries the same list)

Terse path past ~35 calls: acceptance numbers verbatim, no new prose, no file opened "to double check"; closing is PART
of the milestone. 0 `SESSION_CURSOR.md` (<=600 B: id | acceptance | merged? | next) BEFORE the rest. 1 `## Session <N>`
APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers WITH the command). 2 the `<ID>` block to `NAMED.md` (<=1 KB). 3 this
file patched BY SECTION, `wc -c NEXT_PROMPT.md` <= 15,300 BYTES (what `evidence.py budget` prints; the kickoff's
cap-triage trigger — closing at the gate's 16,000 FAIL or at 15,500 hands the next fire a docs-only split).
4 `rsync -a ~/.hermes/skills/smac-cvr-format/
~/reverse/smac/skill/`. 5 `git add -A && git commit -m '<ID>: checkpoint'` then `python3 scripts/gate.py --base main`
GREEN. 6 submit/merge ONLY on a real PASS.
