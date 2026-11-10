# NEXT_PROMPT.md - footing for the next session (session 219, 2026-11-10, **M278 DONE (static): `scripts/m278_block0_semantics.py` 7/7 gates PASS (`evidence/m278_block0.txt`) - both 0x94eaa8 WRITERS' block atoms are OWNER-PLAYER bytes (base+4 0x95da14 via FUN_004e37f0's base-table walk, -1->0 CLAMP 0x51df1d-24: block 0 = player-index-0 REAL row + the unowned fallback - not neutral, not the player slot; AI hub esi = unit+14 owner of the acting unit; 8 blocks by arithmetic; G6: guard-attributed branch census, no ebx-guarded skip)***)
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
patches. **Batch size: FIVE static milestones fit through ONE census script; box milestones 1 per batch. The
binding cap is doc headroom, not capability.**

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>` from merged history. BUILD ⇒
build that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a
census claim; no box time, no `/proc`, no gdb; the box-debt pre-step does NOT apply; title commit+PR `B<n>`);
ANALYSE ⇒ pick from this file. **B4 DONE (s203)** 9/9 on `evidence/m44d_idle.json` (`NAMED.md` §B4), **B5 DONE (s207)** 9/9 on the recorded M27 trace via `python3 -m sim.selftest --replay-m27` (`NAMED.md` §B5), **B6 DONE (s212)** = R1 DONE: headless run, `python3 -m sim.selftest --b6 programs/saves/m54b_clean.SAV programs/maps/planet.MP --turns 10` 6/6 (`evidence/b6_headless.txt`, `NAMED.md` §B6), **B7 DONE (s216)** = R2's move leg: `python3 -m sim.selftest --b7 programs/saves/m54b_clean.SAV programs/maps/planet.MP --turns 5` 6/6 (`evidence/b7_moveslice.txt`, `NAMED.md` §B7).
**B1-B7 DONE.** A BUILD fire must first WRITE the next rung (B8 = R2's next leg: the save WRITE or the new-game path, per `MILESTONES.md` chapter R) into `BUILD_SPINE.md`, then build it; an ANALYSE fire picks from below.

## THE LEDGER

Merged M54A-M271 + B0-B5 (through #199); M276 #214, M277 #217, M278 #<n>. UNMERGED M83/M84, M86, M101, M103, M109
and **M241 (#180, 2/5, PR open)**. Full list with PR numbers and reasons VERBATIM:
`docs/pick-archive.md` §trim-s202; per-id semantics in `NAMED.md`.

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

- **Where things live:** map/terrain footing is `MAP_FORMAT.md` (44-B record table + the loader/allocator
  family) + FOOTING.md's terrain line; faction fields are `docs/field-atlas-faction.md` (M143-M162).
- ANSWERED (do not re-pick): s187-s215 - M227-M237, **B1-B6**, M240-M275 (M241 FAIL 2/5, #180 open), s217-219: M276-M278.
  Full topic enumeration VERBATIM: `docs/pick-archive.md` §trim-s209; numbers VERBATIM: `NAMED.md`
  per-id §s196-§s215 (+ archive §s206, §trim-s205, §trim-s210). FUN_005f3f5b is NOT open - see M220.
- RESULT (s208/s210), (s211, M272), (s211/s213) and (s213/s215) blocks moved VERBATIM to
  `docs/pick-archive.md` (sections trim-s211, trim-s213, trim-s216, trim-s217); per-id numbers
  in `NAMED.md` (M267-M273). Nothing here summarises them - open the archive section you need.

- Pick from (ANALYSE fires; the next BUILD fire takes **B8** - write the rung into `BUILD_SPINE.md` FIRST (R2's save-WRITE leg or the new-game leg), then build it):
  STATIC PICKS (no box time): (b) the row FAMILY: 0x94e8a8 (written 0x51df3d by the same fold) + the 0x94e5a8/0x94e7a8 byte arrays - map the whole per-block layout (census the fold-shaped chains image-wide); (c) 128x128 maps: the loop bound 0x80 never reaches regions >=128 while counts go to 338 - what reads region 128+ (another loop? another function?). (a) ANSWERED s219=M278.
  BOX PICKS, box UP and loaded: WHO dispatches the dialog s +0x4c (466 installs, 0 direct calls, all 12 image-wide `call [reg+0x4c]` sites belong to other hierarchies - falsifier = a live vtable read at a click). The row-stride-188 pick is DONE (s213) - see RESULT (s213); its follow-ups (static, no box): the 80x80/128x128 region counts 128/338 EXCEED the 94-slot row - who clamps the loop, and the 188-row cursor's caller (advances by whole 8380 strides; the fold's 188*fac term = 44.5 block strides). NEVER bp mid-instruction: a bp at store+1 of an 8-B load crash-boxed the game (s213) - break at the disassembled next insn.

## LIVE FACTS / KIT

- **BOX**: UP as of s211 (m54b_clean r50 loaded, TracerPid 0, gdb detached). Cold relaunch was ~6 s to title at s211 (the >9 min figure is stale). `sudo -n python3 scripts/smac_preflight.py` before arming. **ptrace law (s211): wine reparents terran.exe to systemd even when your launcher is alive - the tracked-job ancestry escape is DEAD; wrap harness runs in `sudo -n sh -c 'echo 0 > /proc/sys/kernel/yama/ptrace_scope' && <run>; sudo -n sh -c 'echo 1 > ...'` and keep the harness itself uid 1000 (under sudo wine refuses the prefix).** Recipe + state dumps VERBATIM: skill `references/wine-operations.md`, `docs/pick-archive.md` §s198 + §s199 + §trim-s202.

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
16-19. objdump prints UPPERCASE (`DWORD PTR`, not `ptr [`); gdb startup/exit chatter must be whitelisted
    (`DEBUGINFOD_URLS=""`, the `^[Inferior `/debuginfod lines); ARM BEFORE ANY SCREEN (the CDROM screen
    quiesces 4 min but only advances on driver input); a `gdb -batch` census needs the SIGUSR1/SIGUSR2/
    SIGPIPE `handle ... nostop noprint pass` tail + a ~400-`continue` tail, and a bp on a game-wide reader
    costs one ptrace stop per read. VERBATIM text: `docs/pick-archive.md` §trim-s205.
20-22. byte-field BIT OPS vs dword scans; a "stride conflict" is ONE multiply read in two pieces; a global
    with ZERO writers is LOAD-TIME data — verbatim: `docs/pick-archive.md` §s198.
23. A VALUE SAMPLER IS NOT A STORE CENSUS (a same-value store leaves no trace) and a census PARSER is not a
    log — VERBATIM laws: skill `references/instrument-laws.md` (M241/M242, s192-s193).
24. EVALUATE a multiplier chain, never SLICE it: a hand-written expression at the midpoint of a
    `mov/shl/add/lea/sub` chain published a coefficient 64x wrong (s215's 130 where the chain says
    8380) and manufactured a static-vs-live contradiction that queued a box pick. Symbolic
    linear-form evaluation over the window, then fit it to the RECORDED live log AND show the rival
    coefficients FAIL the same fit (M276 G3/G6/G7).

25. SCRIPT REUSE + REGISTRY (s219): slice a sibling's defs with `"\ndef main("` - m277's own exec
line carries the token inside a STRING, so a bare slice cuts mid-string (SyntaxError cites the OTHER file's lines); exec'd names sit NESTED at `_ns["_ns"]["dst_regs"]`. `## M277` occurs
TWICE in NAMED.md (a cross-ref) - registry gates anchor the FULL header. `x and re.search(...)`
puts a Match in res; sum() dies - `bool()` regex clauses.

## CLOSING ORDER (exactly — the kickoff carries the same list)

Terse path past ~35 calls: acceptance numbers verbatim, no new prose, no file opened "to double check"; closing is PART
of the milestone. 0 `SESSION_CURSOR.md` (<=600 B: id | acceptance | merged? | next) BEFORE the rest. 1 `## Session <N>`
APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers WITH the command). 2 the `<ID>` block to `NAMED.md` (<=1 KB). 3 this
file patched BY SECTION, `wc -c NEXT_PROMPT.md` <= 15,300 BYTES (what `evidence.py budget` prints; the kickoff's
cap-triage trigger — closing at the gate's 16,000 FAIL or at 15,500 hands the next fire a docs-only split).
4 `rsync -a ~/.hermes/skills/smac-cvr-format/
~/reverse/smac/skill/`. 5 `git add -A && git commit -m '<ID>: checkpoint'` then `python3 scripts/gate.py --base main`
GREEN. 6 submit/merge ONLY on a real PASS.
