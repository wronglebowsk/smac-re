# NEXT_PROMPT.md - footing (s251 close: M298 SMALL STATICS pair landed (zero box) -
0x582cc0 = lazy-nibble CACHE WRITE-BACK into BYTE[rec+2] high nibble, edi survives
the call (discarded eax = rec base); [ebp-0xc] = BYTE[rec+3] site byte, sole store
0x51dd57 - 11-callers REFUTED; M294 cell-addr phrasing FIXED (slot store = max ->
28B slot 0x989ce8; addr = 0x94eca8+8380*ebx+site). s250 landed M297 (NAMED §M297). B17 10/10.)
Overflow: pick-archive (VERBATIM blocks - read only the picked section), NAMED.md
(§CHAIN-BUILDS/§CHAIN-PICKS - grep only), skill instrument-laws.md.

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor; its summaries die on the output cap. **Whatever is not
finished by ~150k tokens is not finished at all.** Counted in TOOL CALLS:
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 15 `git add -A && git commit`** (s187: call 25 = 167k,
  zero commits — ~7k tokens/call) — every later step must leave a committed file.
- JSON only: no XML in tool args. Writes over ~4 KB drift -> rejected as missing `path`: retry once, re-emit as pure
  JSON (never fragment). Branch + skeleton commit BEFORE probing (s189: 108k vs 167k).
- **30-40** STOP MEASURING: an ungreen acceptance IS the finding — write blocker + number, merge nothing.
- **40-50** closing order, TERSE (see CLOSING ORDER; the caps there bind).

Survivability: cursor <=600 B before any >2-min step; never `rm`/`git checkout --`; doc writes patch/append.
**Batch: 5 static milestones per census script, 1 box milestone per batch — doc headroom, not capability, is the cap.** Caps (BYTES, what `budget` prints): NEXT_PROMPT warn 12,000/fail 16,000 — CLOSE at <= 12,000; SKILL.md
warn 55,000 (keep near 44 k, always-loaded under the 60 k ritual); SESSION_NOTES warn 110 k. Split rule: settled text
VERBATIM to a reference / `NAMED.md` section; RULES + pointer stay; re-run `budget`.

## BUILD TRACK — every 4th fire builds (full text VERBATIM: `docs/pick-archive.md` §s194)

`python3 scripts/track_mode.py` prints `MODE=BUILD|ANALYSE` + `next_rung=B<n>` from merged history. BUILD ⇒ build
that rung from `BUILD_SPINE.md` in `sim/` (runnable acceptance, parity vs a recorded trace, never a census claim; no
box/`/proc`/gdb time; box-debt pre-step N/A; PR titled `B<n>`); ANALYSE ⇒ pick from this file. **B1-B17 DONE** (per-rung cmds: `NAMED.md` §CHAIN-BUILDS; B17: `python3 -m sim.selftest --b17 <sav>` +
`evidence/b17_scanleg_chain.txt:1`). Next = **B18**, unauthored - its BUILD fire
writes it (B14/B16/B17); s251 ANALYSE landed M298; s252 = B18 BUILD fire. Track_mode FIRST.

## THE LEDGER

Merged M54A-M298 + B0-B17 (through s251) + hygiene #254/#255; UNMERGED M83/M84, M86, M101, M103, M109 and **M241 (#180, 2/5, PR open - documented-FAIL re-confirmed, gates stand)**.
Full list + reasons: `docs/pick-archive.md` §trim-s202; per-id semantics `NAMED.md` + `docs/named-archive-*.md`.

## THE INSTRUMENTS (run FIRST)

1. **accept_ready.py** = readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per
   base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it before you arm** (screen fixes in TRAPS).
2. Writer/flag chain - silent bps or hw watchpoints + a live-memory prediction + a read-back: the
   m94/m97/m100/m102/m103 + m92/m95/m98/m117 family (full text: pick-archive §s244-trim; writer
   named by containment in ghidra_out/index.csv; `--predict` = model table, no touch).
3. Static-first kit (zero box time): `field_census.py` (a global's shape from its addressing form + index math),
   `name_global.py` (every reader/writer + containment), `m118_flag_never_set.py` (gate satisfiability: test sites, OR
   immediates, register bit ops, save-carry), `fn.py 0xADDR`, `scratch/m71/dis.py LO HI [cap]` (objdump window;
   import as a module), `evidence.py audit|budget|prune|log`.
4. Self-documenting: `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m65_screen.py --samples 8`.

## THE PICK — index (detail: `docs/pick-archive.md`, `NAMED.md` §CHAIN-PICKS)

- **Where things live:** map/terrain = `MAP_FORMAT.md` + FOOTING.md's terrain line; faction fields =
  `docs/field-atlas-faction.md` (M143-M162; pair-flagword addr fixed by M297: block 0x94d430+8380*fac,
  pair word at +0x18 + 4*(fac*2095+other) - the atlas 0x94d104 phrasing was wrong, lead to fix it there).
- **THE PICK (s252): B18 BUILD fire** (track_mode says so - run it FIRST). B18 is
  UNAUTHORED: its BUILD fire writes it from BUILD_SPINE.md (B14/B16/B17 pattern) -
  runnable acceptance in sim/, parity vs a recorded trace, never a census claim, no
  box. s251 landed M298 (SMALL STATICS pair CLOSED - 0x582cc0 = lazy cache write-back,
  [ebp-0xc] = BYTE[rec+3]; NAMED §M298). Hygiene: NAMED split DONE at s251
  (docs/named-archive-m89-m221.md, gate now green at ~176 kB).
  ANSWERED: M227-M298 + B1-B17 (M241 FAIL 2/5, #180; s249 pick:
  pick-archive §s250-trim). CLOSED: FUN_005f3f5b (M220), DIALOG +0x4c (M284-M288, live
  half INVALID s240); NEVER bp mid-instruction (s213). OPEN shortlist (hub-visit gating,
  0x56c6de continue-leg, 188-row cursor caller): `NAMED.md` §CHAIN-PICKS.
  READER LAWS bind: GDEEP/GACC x=/y= TRANSPOSED (use load_visits/recover_pod);
  tail-$esi VAL garbage (GROW BEST is meaningful, M296 S7); M293 guards re-derive;
  NEW (M297): end-window /proc snapshot = LAST-TURN witness (bit4 flips val-invisible)
  - skill `instrument-laws.md` §LIVE-SNAPSHOT.
## LIVE FACTS / KIT

- **BOX**: s244 state UP (s245..s251: s249 read-only /proc pass; s251 ZERO box - state identical)
  (m54b_clean at y2212, cnt 30, TracerPid 0, yama=0; not t0) —
  RE-CHECK `accept_ready.py`; it BLOCKS on credit 0 (d0-gated income, STRUCTURAL here): walk/scan kinds
  run anyway; production kinds need the FIX recipe (relaunch+m54g_prep+drive1+enqueue, ~6 s/turn warm).
   `sudo -n python3 scripts/smac_preflight.py` before arming. **ptrace law (s211): yama back to the
   PRE value after every run, never hardcoded; the harness stays uid 1000 (sudo breaks the prefix) -
   exact commands in skill `wine-operations.md`.**

## TRAPS — rules (FULL s241 text verbatim: `docs/pick-archive.md` §s242-traps; detail §trim-s205/§s198; laws: skill
`instrument-laws.md` + `wine-pitfalls.md`)

1. A `fired=` list is the MODEL's prediction, not events; a no-event is evidence only once the bp is CONFIRMED to
   exist there. Gates PREDICT from live memory, then confirm with counters; a counter at a site that is BOTH branch
   target and loop-completion fallthrough is NOT a leg proof (0x5a7f9f); a gate may only read a field the harness SETS.
2. Check the instrument before believing a no-event: `if *$ecx==X` DEREFERENCES and silently never fires; a bp at a
   return-site `mov eax,[ebp-0xc]` prints the OLD eax (break at the NEXT insn, 0x5aa24a); `lea edi,[eax+1]` makes edi
   the MODULUS (read the arg); ZERO CALLS can be the GAME — scan /proc for the vptr first.
3. Register semantics live in the ENCODING: `[reg*4+disp]` vs `[reg+disp]` differ by scaling — a condition testing one
   against the other never fires; a RMW through a COPIED register evades store-shape greps — a hw watchpoint on the
   FIELD answers "who writes it".
4-5. gdb printf/script laws: no inferior strings; expressions go in printf ARGUMENTS with matching specs (a mismatch
   ABORTS the sourced script and DETACHES at the first hit); a manual call frame needs the RETADDR at esp+0 and the arg
   at esp+4; gdb ABANDONS an inferior `call` once any bp hits inside it; ONE `\n` prints a newline, TWO reads as ZERO
   events; a bp at the insn AFTER `call X` fires AFTER the callee's events — group backward; unwatched factions
   legitimately yield empty groups.
6. A >90 s gdb census NEVER runs in the foreground (waits cap 420 s; killing it leaves Wine hung): background + wait,
   or `--rounds <= 4`. Faction upkeep runs in its OWN segment ~1 cycle after turn-end — use `--boundaries >= 2`.
7. Dialogs swallow every click/turn-end key while the HUD bar reads THROUGH them: Return clears a dialog, a BUILD/base
   PANE needs Escape (bare-map Escape raises the quit prompt — never OK); normalize first
   (`m78_mark_clear.normalize_screen()`), click from OCR bboxes; `m44_idle` asserts TracerPid==0 — use m55_boundary.
8. A PASS on a non-discriminating shape is no PASS: compute candidate predictions from the baseline first; refuse the
   shape if they all agree. RE-RUN on a harness race, never edit the floor.
9. base+0xd0 (`credit`) is RECOMPUTED EVERY ROUND (FUN_004e93f0 0x4e9557/0x4e957f = [+0xc0]-[+0xf0]-[+0xe0]) — a poke
   there is undone next turn; gate on round movement, use the per-boundary storage poke 200.
10. A hw watchpoint REPORTS ONLY A VALUE CHANGE AND `pc = store + INSTRUCTION LENGTH` — gate on those, never the store
    address; silent bps AT the store count stores, the watchpoint is the "any other writer" check; whitelist
    `[New LWP]`/`[Switching to LWP n]`/SIGINT chatter (skill Wine Watchpoints + instrument-laws).
11. A silent bp at the pc a hw watchpoint REPORTS is EATEN by it — put the read-back ONE instruction later and read
    memory, not the register. A poke is evidence only if the CONSUMER reads it.
12-13. Both gdb-detach laws (skill Wine core): a census can leave gdb ATTACHED — check `TracerPid`,
    kill the stale gdb BY PID before calling the box clean; the TURN DRIVER returns rc=0 WHILE AI UPKEEP PLAYS —
    detach only after cp == human faction returns or the last recomputes go UNLOGGED.
14. The queue tail holds STALE ids (shift reaches only `0..pending-1`): never treat "first empty slot" or a
    stale tail as proof an id IS queued; id 0 = Colony Pod AND the empty marker, sentinel -39; negatives belong to
    the TYPE (196 -> -6, 195 -> -3). PRODFLAG (0x4efe60) fires for EVERY record the pass walks (128/322/323/194 =
    FACTION BANDS) — attribute the sweep by its own predecessor; the gate visit arrives a boundary AFTER the sweep.
15. A list cursor read BEFORE the seek is the PREVIOUS cursor (pump seeks at 0x497717 — print at 0x49771c).
    `milestone.py start` on a dirty tree: stash, start, pop (skill Git workflow).
16-23. (MOVED VERBATIM to `docs/pick-archive.md` §trim-s245, s245, to hold the 12 k cap: objdump
   prints UPPERCASE; gdb startup/exit chatter whitelist; ARM BEFORE ANY SCREEN; the SIGUSR1/
   SIGPIPE `handle` + ~400-`continue` tails; a bp on a game-wide reader; byte-field BIT OPS vs
   dword scans; a stride conflict is ONE multiply read twice; a zero-writer global is LOAD-TIME
   data; a VALUE SAMPLER is NOT a STORE CENSUS; a census PARSER is not a log.)
## CLOSING ORDER (exactly — the kickoff carries the same list)

Terse past ~35 calls: acceptance numbers verbatim, no new prose, no "double check" reads; closing is PART of the
milestone. 0 `SESSION_CURSOR.md` (<=600 B: id | acceptance | merged? | next) BEFORE the rest. 1 `## Session <N>`
APPENDED to `SESSION_NOTES.md` (<=2 KB, numbers WITH the command). 2 the `<ID>` block to `NAMED.md` (<=1 KB). 3 this
file patched BY SECTION to <= 12,000 B (`budget`'s warn; past it the next fire starts as a docs split). 4
`diff -rq skill/ ~/.hermes/skills/smac-cvr-format/`, reconcile, `rsync -a skill/ ~/.hermes/skills/smac-cvr-format/`
(content-identical; gate checks SKILL.md only). 5 `git add -A && git commit -m '<ID>: checkpoint'` then
`python3 scripts/gate.py --base main` GREEN. 6 submit/merge ONLY on a real PASS — and per the MERGE RULE only after
the Greptile review on the head commit finished (`gh pr checks` until nothing pending), its inline comments read, and
every P1 fixed or dismissed in the PR body in one sentence.
