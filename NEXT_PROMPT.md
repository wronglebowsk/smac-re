# NEXT_PROMPT.md - footing (s228, M284 MEASURED-NEGATIVE: the family +0x4c dispatch forms are
# exhaustive - 12 call [reg+0x4c] sites, 0 load-then-call pairs, 0 direct, 5 vtables/466 installs; a
# live wndproc-verified click window on the base display dispatched it through NO site (CPane, not
# Script.txt). Next: ANALYSE; BUILD=B11 when due***)
Structure: RULES + live footing. Overflow on disk: `docs/pick-archive.md` (narrative + blocks moved
VERBATIM — read only the section picked), `NAMED.md` (semantics), skill `references/instrument-laws.md`
(laws).

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor; its summaries die on the output cap. **Whatever is not
finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
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
ANALYSE ⇒ pick from this file. **B4 DONE (s203)** 9/9, **B5 DONE (s207)** 9/9, **B6 DONE (s212)** = R1 DONE (6/6), **B7 DONE (s216)** = R2's move leg (6/6) - commands per-id in `NAMED.md` §B4-§B7.
**B8 DONE (s220)** = R2's save-WRITE leg: `python3 -m sim.selftest --b8 <sav> <map> --turns 5` 10/10 (`evidence/b8_savewrite.txt`, `NAMED.md` §B8). **B9 DONE (s223)** = R3's golden-trace pairing: `python3 -m sim.selftest --b9 <sav>` 7/7 (`evidence/b9_golden_parity.txt`, `NAMED.md` §B9). **B10 DONE (s226)** 18/18: `python3 -m sim.selftest --b10 <sav>` (`evidence/b10_basefound.txt`, `NAMED.md` §B10). **B1-B10 DONE.** A BUILD fire must first WRITE the next rung (B11, per `MILESTONES.md` chapter R) into `BUILD_SPINE.md`, then build it; an ANALYSE fire picks from below.

## THE LEDGER

Merged M54A-M271 + B0-B5 (through #199); M276 #214, M277 #217, M278 #219, M279 #223, M280 #224, B8 #221, B9 #227, M281 (s224, 7/7), M282 (s225, 7/7), B10 #231 (s226, 18/18), M283 (s227, 17/17). UNMERGED M83/M84, M86, M101, M103, M109
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
- ANSWERED (do not re-pick): s187-s215 - M227-M237, **B1-B6**, M240-M275 (M241 FAIL 2/5, #180 open), s217-19: M276-M278, s220: B8, s221: M279, s222: M280, s223: B9, s224: M281, s225: M282, s226: B10, s227: M283.
  Full topic enumeration VERBATIM: `docs/pick-archive.md` §trim-s209; numbers VERBATIM: `NAMED.md`
  per-id §s196-§s215 (+ archive §s206, §trim-s205, §trim-s210). FUN_005f3f5b is NOT open - see M220.
- RESULT blocks s208/210, s211 (M272), s211/213, s213/215 VERBATIM in `docs/pick-archive.md`
  (trim-s211/213/216/217); per-id numbers in `NAMED.md` (M267-M273).

- Pick from (ANALYSE fires; the next BUILD fire takes **B10** = R2's new-game leg - write the rung into `BUILD_SPINE.md` FIRST, then build it):
  ANSWERED s228=M284 (family +0x4c dispatch forms EXHAUSTIVE: 12 call [reg+0x4c] sites, 0
  load-then-call, 0 direct; live base-display clicks (wndproc control, 3 sent) dispatched it
  through NONE - the dispatcher sits on the Script.txt chooser/menu path, unopened here).
  ANSWERED s227=M283 (decode_save --sections: the 64x64 crash was the hardcoded 80x80
  coarse-region-map length - now dims-derived, 17/17). ANSWERED s225=M282 (AI bases use the SAME
  founder FUN_004e47d0 as the player; callers 4cca50 live via 'b' + dispatcher 0x4408 + AI hub
  5f650, 59ce10/59ec90 placement; +1 writers only 4e484a + 59b830 load loop; built as
  sim/basefound.py in B10). NEW (M282 frontier): WHICH founder vector
  the recorded AI used per founding - 0x4408 vs 5f650 vs the 5a0aa0 chain (live question).
  STATIC PICKS (no box time): (c) ANSWERED s224=M281 (no region id >=128: generator bands cap at 0x7f; 338 = the coarse-map CELL count; region table 3584 B @0x1c = 128 slots; M251 stands).
  BOX PICKS, box UP and loaded: (M284 re-scoped) the family +0x4c dispatcher on the Script.txt
  chooser/menu path - open a real chooser (m54g_prep + one turn) and re-run m284 --live. all 12 image-wide `call [reg+0x4c]` sites belong to other hierarchies - falsifier = a live vtable read at a click). The row-stride-188 pick is DONE (s213); region-cap CLOSED (M274+M281); the 188-row cursor's caller stays OPEN (8380 strides; 188*fac = 44.5 block strides). NEVER bp mid-instruction: a bp at store+1 of an 8-B load crash-boxed the game (s213).

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
