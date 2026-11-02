# NEXT_PROMPT.md — footing for the next session (session 208, 2026-11-02, **M267-M268 DONE: the 0x6725ac/0x6725a4 "pair" is ONE vtable with entry points 8 B apart, installed by 1 ctor + 4 destructors of 4 variants of the virtual base at [desc+4] (`[vptr-4] = [desc+4] - 0x21a6c`); the 201 x 608 = 122,208-B block is POD, never indexed by computed code, never saved — 14/14 on `evidence/m267_m268_census.txt`; B5 done, numbers `NAMED.md` §B5**)

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
ANALYSE ⇒ pick from this file. **B4 DONE (s203)** 9/9 on `evidence/m44d_idle.json` (`NAMED.md` §B4), **B5 DONE (s207)** 9/9 on the recorded M27 trace via `python3 -m sim.selftest --replay-m27` (`NAMED.md` §B5).
**Next rung B6 = the headless run**: `sim/headless.py --sav <save> --turns 10 --dump sim_state.json`, exit 0, year per B3, two runs → identical sha256.

## THE LEDGER

Merged M54A-M266 + B0-B4 (through #195); B5 is this PR. UNMERGED M83/M84, M86, M101, M103, M109
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
- ANSWERED (do not re-pick): s187-s208 — M227-M237, **B1-B5**, M240-M268 (M241 FAIL 2/5, #180 open;
  the save-codec chain, the region generator + its ORDER, the verdict codes and their guards, the worth
  test's operands, the 12-array per-region family, the economy rung, the per-faction mask band, the
  view table + its startup allocation, the allocator and the record cursor, the 0x679f98 class, what
  the 7 allocated blocks ARE, why FUN_00583c70 is unreferenced, what the 201 608-B elements ARE NOT,
  which variants share the 0x6725ac/0x6725a4 pair). Numbers VERBATIM: `NAMED.md` per-id,
  §s196-§s208; the s205 RESULT block moved VERBATIM to `docs/pick-archive.md` §s206 (+ traps 16-19 at
  §trim-s205). FUN_005f3f5b is NOT open — see M220.
- RESULT (s208): the "pair" 0x6725ac/0x6725a4 is ONE vtable read from two entry points 8 B apart
  (0x6725a4 = 0x6725ac-8, the code run ends 0x672a38, 291 vs 293 slots, heads 0x4222c0/0x405350/
  0x422190 are not function starts); its 5 installers are 1 ctor (FUN_00469650, descriptor 0x675964)
  + 4 DEstructors (FUN_00421950 the base; FUN_00518980 the 0x678458 variant, pair 0x678184/0x67817c at
  +0x23d94; FUN_0059c1e0 and FUN_0059bec0 the 0x67194c/0x671944 variant — the latter a 0x25318-B STACK
  instance that calls the save writer), NONE of them address-taken image-wide; the offsets differ
  because the subobject is a VIRTUAL BASE: `[vptr-4] = [desc+4] - 0x21a6c` (shard_008.c:5869). The
  201 x 608 = **122,208 B** block (+0xc..+0x1dd6c, not 121,600) is POD — ctor 0x62514b and dtor
  0x62516c write the same {dword0=3, dword1=0} — and NO code computes a 608-strided address (all 21
  0x260 immediates are iterator args or their unwind records); the 94 folded (d-0xc)%608==0
  displacements are chance (3.65x uniform, none in a view-loading function) and the per-view codec
  FUN_00596620 saves only +0x1dd70..+0x1dda0. Census `scripts/m267_m268_census.py` -> 14/14,
  `evidence/m267_m268_census.txt`. s206's numbers: `NAMED.md` §M265-§M266, census 12/12.
- RESULT (s207, BUILD): the arrow-key step is executable — `python3 -m sim.selftest --replay-m27` ->
  **PASS B5: 9/9 gates** (rc=0, green on inv 1, `evidence/b5_replay_m27.txt`). Model, parity numbers
  and its 3 OPEN items VERBATIM: `NAMED.md` §B5 (per-terrain move cost ASSUMED uniform 3; the bonus
  behind `moves = 2`; rec118's first step lies outside the trace window).
- Pick from (ANALYSE fires; the next BUILD fire takes **B6** — the headless run — from `BUILD_SPINE.md`):
  WHO dispatches the dialog's +0x4c (466 installs, 0 direct calls, all 12 image-wide `call [reg+0x4c]`
  sites belong to other hierarchies — falsifier = a live vtable read at a click, box); **does
  `FUN_0057ecf0` also run on a LOAD** (new from M255, box: bp the `FUN_005b2970` entry, load a save —
  the box is DOWN, cold relaunch >9 min); **what the row stride 188 means** (new from M257: `esi =
  2*region + 188*fac`, regions 94..127 pass the next row — one live read of both indexings of `0x94eaa8`
  settles it; box); **the virtual-base delta census** (new from M267: all 5 installers compute
  `[vptr-4] = [desc+4] - 0x21a6c` — find every site of that shape image-wide, list the K values and
  the descriptors whose dword[+4] equals each; static); **who constructs the 0x67194c/0x671944 class**
  (new from M267: its destructors are FUN_0059c1e0 + FUN_0059bec0, its vtable has 361 slots and slot 0
  = 0x406130 — find the installer of 0x67194c and the allocation size; static).
## LIVE FACTS / KIT

- **BOX**: DOWN as of s202 (`ps` shows no terran.exe). Cold relaunch >9 min: `SMAC_SAVE='m54b_clean.SAV'
  python3 scripts/m54a_load.py --relaunch` as a TRACKED background job; `sudo -n
  python3 scripts/smac_preflight.py` (yama ptrace_scope=1 ⇒ `/proc/<pid>/mem` needs sudo) before arming.
  Recipe, cold timing, the degraded-box poke facts and the state dumps VERBATIM: skill `references/wine-operations.md`,
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
16-19. objdump prints UPPERCASE (`DWORD PTR`, not `ptr [`); gdb startup/exit chatter must be whitelisted
    (`DEBUGINFOD_URLS=""`, the `^[Inferior `/debuginfod lines); ARM BEFORE ANY SCREEN (the CDROM screen
    quiesces 4 min but only advances on driver input); a `gdb -batch` census needs the SIGUSR1/SIGUSR2/
    SIGPIPE `handle ... nostop noprint pass` tail + a ~400-`continue` tail, and a bp on a game-wide reader
    costs one ptrace stop per read. VERBATIM text: `docs/pick-archive.md` §trim-s205.
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
