# NEXT_PROMPT.md — footing for the next session (session 151, 2026-10-29)

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

Survivability: before any step that can exceed 2 minutes (gdb run, relaunch, evidence audit) overwrite
`SESSION_CURSOR.md` (<= 600 B) with `<ID> | acceptance | merged? | next command` — only you record what
was in flight; never `rm`/`git checkout --`. Every doc write is an append or a <= 2 KB patch.
## THE LEDGER

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90 (#95), M91 (#97), M92-M94 (#98-#100), M95 (#101) — full detail in NAMED.md. UNMERGED branches: M83/M84/M84b/M84e/M84f (0x496ad0's -9999 is the DIALOG-CANCEL sentinel, Escape arms [0x6a9e9c+0xa774] = -1; the 0x4d00 queue post is gated at 0x4193b2-0x4193b9 on ds:0x920434 != 0, live 0, so a UI insert posts NOTHING), M86 (0x5a7e73 skips the 64-record band loop unless arg1 == 0x93325c/68/74 = Alloys/SingMec/ConSing; both bit-set tails need ds:0x920434 != 0 AND (1<<arg0)&ds:0x985b10).
**M90/M91 (s141-s143, #95/#97):** the slot IS a tech index 0..88 chosen by the STRICTEST-largest
draw; BASE = SUM of four (demand*m+1)*cost pairs (m=4 live); tail runs only arg2==0. NAMED.
**M92 (s144-s146, #98, `m92tail18` PASS 8/8, fresh m54b_clean load r51->55):** FUN_005a90a0's tail
(entered 0x5a9500 iff arg2==0) EXACTLY predicted: **TAILOUT at 0x5a9698 == BASE + the tail simulated
from the per-faction block — 39/39 candidates, 0 mismatches, 2 qualifying windows, naive one-factor
splits 19** (cat/mult/div offsets, the cat7/cat2/cat0/band legs and gates: skill code-atlas.md).
**Block FROZEN within a round** (0/39 + 0/19 dumps differ), moves BETWEEN rounds — s145's in-round-motion claim RETRACTED (census defects, see TRAPS). Census needs a FRESH load. NAMED. **M92 MERGED (#98).**
**M93 (s147-s148, #99, `m93post3` PASS 9/9):** the POST cascade 0x5a9747-0x5aa022 EXACTLY predicted
(13/13 finals): `0x5a9020(a,X,f)` = prereq-closure membership at depth f; stages apply iff idx is
INSIDE their set (legs in skill code-atlas.md); TIMING LAW: ladder inputs move mid-round — freeze at
the TAIL HIT, not the boundary snap. NAMED.

**M94 (s149, #100, `m94table3` PASS 7/7):** DIVISOR `[fac*8380+0x94e488]` RECOMPUTED every round by
FUN_00556690 (upkeep stage, arg=fac; also 0x59dd43): reset 0x94e484/488/48c<-0 (0x5566cf) then
rebuild (0x556a87) — **== faction base count** (8/8); mults/cats rewritten in-stage; 0-base fac ->
no events. NAMED.
## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape, quit-prompt -> Escape (`m78_mark_clear.normalize_screen()` does all three).
2. The price/flag/marker chain — silent breakpoints or hw watchpoints + a prediction from live memory
     + a read-back: `m73_price_split.py`, `m74_flag_hw.py`, `m72_gate_watch.py` (the VISIT GATE),
     `m81_flag_writer.py`, `m85_tech_census.py`, `m88_slot_watch.py`, `m90_tech_choice.py`,
     `m91_scorer_census.py`, `m92_tail_census.py` (base 0x5a930b, TAIL 0x5a9503, TAILOUT 0x5a9698,
     final 0x5aa159, draw 0x5aa232; simulate EACH candidate LIVE at its BASE hit on a FRESH load),
     `m94_table_watch.py` (4 hw watchpoints on any 4 dwords), `m95_pay_sites.py` (13 cond bps + 2 hw wp on storage/pending of one base row; per-boundary storage poke; names the pay branch + POP caller; `--tag m95payN --boundaries 2`); prints pc+new+round+cur_player, names
     the writer by containment via ghidra_out/index.csv, movement-vs-events self-check, pokes
     storage per boundary; PREDICTIONS, then counters, then the branch bytes named); rest self-doc.
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py`, `evidence.py audit [--delete]`/`budget`,
   `scratch/m71/dis.py LO HI [cap]` (objdump window; import it as a module, `dis` clashes with stdlib).
## THE PICK

**M95 ACCEPTED (s150, `m95pay4` PASS 9/9): the pay-site conflict is CLOSED** — a UI-queued completion
pays AND activates in branch A: gate 0x4efa5e -> pay 0x4efedd (storage +0x40 -= price; credit +0xd0
feeds ONLY the income add 0x4ef7f6 + the clamp) -> create 0x4eff4e -> POP 0x4f037b -> 0x4ef5d0
(pending store 0x4ef648). 0x4f0ca6 is branch B's pay — B is entered ONLY for negative queue slots
(typecode = -q0: >=39 unclaimed / >34 / 0x507410-mask-fail), same field, mutually exclusive, 0 live
events on the UI shape. Stale-tail law: a non-sentinel q0 with pending 0 re-produces phantoms while
storage >= price. NAMED.
**M96 (THE PICK): the human leg** — FUN_00625af1 @0x5aa20d, bVar14 in FUN_0048b9a0, [esi+0x94d800]
sibling slot, [esi+0x94d430] bit 0x40: what the human key multiplies before the draw; census bps for
0x5aa159/0x5aa232 already exist in `m92_tail_census.py`/skill code-atlas — human mask 0x985b10 byte
= 0x08 (fac3 only). Do NOT re-derive M92/M93/M94/M95.
## STILL OPEN (in priority order)

1. **After M96: the sibling slot [esi+0x94d800] (FUN_005aab70); band flag [esi+0x94d430] bit 0x40;
   ds:0x926bd4 / ds:0x920434 naming; chooser case 7; cursor print at **0x49771c**; bit 5 (0x531782);
   WHO writes base+0xd0 (credit) mid-game (-1->0 seen r58/59, untraced); the negative-queue producer
   that reaches branch B.**
2. **M67's plan-descending LIST order has no code behind it** (zero sites read plan byte `+42`); the
   **`-3 / -6` stride CONFLICT** (`0x984d38 + (-v)*48` vs `+(-v)*16`). Suite: `scripts/gate.py`.

## LIVE FACTS / KIT

- **Box at s150:** m54b_clean r59->61, m95 census ran (m95pay1-4); pending 0, q0 STALE 2 (phantom
  Scout Patrols created — do not trust the head slot), storage 0, credit -1.
  `scripts/m93_post_census.py` = m92's census + POST prints + `ladder_pred`/G9 + hit-timed
  tailx1/tailx2 specials dumps — run on a FRESH load.
  The census pokes slots 7/2/6 to -1; a degraded box cannot be rescued by poking. 0x985ac4 bit 0x200 SET
  (scorer m = 4). The human mask byte at 0x985b10 = 0x08 -> ONLY faction 3 is human (a dword read there
  shows 0x985b10 = 65288, mask the low byte). X focus law: see TRAPS. **The PANE decides where INSERT
  lands** (pass the index the pane shows: `*(int *)0x6a9480 + 0x3ff3c`).
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> (enqueue) -> **read `pending` AND the head back** -> the run. Misread `movie` ~1 in 3: re-run `--relaunch`, never Return on the save browser.
- gdb: 4 hw watchpoints and 10-16 silent breakpoints work (~35 s per boundary); conditional bps keep other records out of the log; PREFER REGISTER-ONLY conditions on hot addresses (memory-read conditions cost seconds/hit — s133). No `si` in a command list; stdout DRAINED (`stdbuf -o0`); a watchpoint reports the pc AFTER the store.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros — grep
  `4ef5d0:`, not `004ef5d0:`; only lines matching `^[0-9a-f]{6,8}:\t` are instructions). Ghidra
  pseudocode is `ghidra_out/shard_NNN.c`. Parse with Python (`scratch/m71/dis.py`), never read whole.
  `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` (double the offset) and a POINTER to the base record. Records are BYTES: type record (stride 52, base `0x98ad88`, **8 FACTION BANDS OF 64**, M80): name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0 validator, bit 2 markup-off, bit 8 sweep marker); base record: name `+19`, storage `+0x40`, pending `+0x4c`, queue `+0x50..+0x74`, `+0x98` = storage copy.
- **Evidence budget: the gate FAILs at 30 MB** — prune with `evidence.py audit --delete` BEFORE adding.

## TRAPS

- **The `fired=` list on a `LADDER-MISMATCH` line is the MODEL's prediction, not observed events** — a leg listed there that no breakpoint caught is the model over-applying, not the instrument missing it (s148). A no-event at an apply site is only evidence once a breakpoint is confirmed to EXIST there (4 lacked one until s148).
- **Register semantics live in the encoding, not the name:** `[reg*4+0x98adb8]` means the register
  holds `tid*13` (52/4), `[reg+0x98adb8]` the BYTE address `tid*52`; a conditional bp testing such
  a register against the bare tid can NEVER fire.
- **Grep objdump case-sensitively** (`DWORD PTR`, not `ptr [`); a read-modify-write through a COPIED
  register (`mov ax,[x]; or al,4; mov [x],ax`, 0x4efe60) evades store-shape greps — a HARDWARE
  watchpoint on the FIELD answers "who writes it" in one run.
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it.**
  Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit
  prompt — never OK). Run `m78_mark_clear.normalize_screen()` first.
- **Gates must PREDICT from live memory, then be confirmed by counters** — cens1 FAILed demanding hits
  at sites the taken leg cannot reach; a counter at a site that is BOTH a branch target and a
  loop-completion fallthrough is NOT a leg proof (0x5a7f9f). **A gate may only read a field the harness
  SETS** (m92 G8 read an unassigned field: False 4 runs, s146). A gdb-log tag alternation must be LONGEST-first
  (`MARK` swallows `MARKSET`); a bp printf must NOT print inferior strings (aborts the batch, DETACHES
  mid-window); template expressions go in printf ARGUMENTS, never the format string; in a two-branch
  `re` alternation `m.group(1)` is the WHOLE match.
- **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (128/322/323/194 — FACTION BANDS, M80): attribute the sweep by its own predecessor; the gate visit arrives in the boundary AFTER the sweep marks (poke window >= 3 boundaries).
- **`getactivewindow` is a RED HERRING (always errors, no WM on :99) — use `getwindowfocus
 getwindowname`; prove keys land via a classify flip before blaming input.** **Vision-tool coords are
 SCALE-SHIFTED** — click from OCR word bboxes (TURN COMPLETE center (675,416)). **m44_idle asserts
 TracerPid==0** — never a driver under a census gdb; use m55_boundary.
- base+0xd0 (`credit`) is written ONLY at player-record init (0x6310c6/0x631154) — income is never
  recomputed per round; University Base credit>0 cannot be restored by turns; use the per-boundary
  storage poke 200.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by
  "first empty slot" or a stale tail as proof an id IS queued. Id 0 is Colony Pod AND the empty marker;
  the sentinel is -39; a negative belongs to the TYPE (196 -> -6, 195 -> -3).
- **A PASS on a shape that cannot discriminate is not a PASS:** compute candidate predictions from the
  baseline first; refuse the shape if they all agree. RE-RUN on a harness race, never edit the floor.
- **`milestone.py start <id>` refuses a dirty tree and resets to main**: stash a carried doc edit,
  start, pop (s140 did exactly that with the skill's code-atlas carrier). `SESSION_CURSOR.md` must be
  re-written AFTER it.
- **A list cursor read BEFORE the seek is the PREVIOUS cursor:** the chooser pump seeks with
  `call 0x4026b0` at 0x497717, so a node print at 0x497704 shows the old node (m84cprobe1 G3 was
  this, not the game) — print at 0x49771c.
- **`dump binary memory`/`append binary memory` need a LITERAL end address:** an arithmetic range (worse
  with a substituted path) aborts the sourced script at the first hit; a multi-line `python` block in a
  breakpoint command list aborts too. A snapshot reader must use the region SIZE, not an offset.
  Proven the hard way: m92tail3-7.
- **ZERO CALLS CAN BE THE GAME, NOT THE INSTRUMENT:** before betting an acceptance on a function
  with no fixed-displacement caller, scan terran.exe rw regions for its vptr (`/proc/pid/mem`, no gdb —
  `scratch/m84d/probe3.py`), confirm an instance exists; prove arming from the log.
- **A >90 s gdb census NEVER runs in the foreground: the terminal tool caps waits at 420 s and KILLING
  the census mid-run leaves Wine hung (round frozen, CTRL watchpoint 0 events even after detach) — costs
  a ~15 min detour + a reload (s143: m91score4).** Run background + `process_manage wait` (clamped 180 s,
  loop), or keep `--rounds <= 4`.
- **In a gdb printf, `*(int *)($ebp-0x10)+0x92fdc4` prints an ADDRESS, not what is there:** a local that
  holds an offset needs double indirection — `*(int *)(*(int *)($ebp-0x10)+0x92fdc4)`.

- **A bp condition built by f-string: a stray `*` turns `if $ecx==X` into a DEREFERENCE `if *$ecx==X`
  — the bp silently never fires while hw watchpoints still carry the truth (s150: m95pay1 FAILed 4/9,
  m95pay2 3/9 this way). Check the EMITTED script text before believing a no-event.** gdb printf `%x`
  prints BARE hex (no 0x) — parse regexes accordingly.
- **Faction upkeep runs in the faction's own turn segment ~1 cycle AFTER your turn-end: a 1-boundary
  window can close mid-cycle (cur_player 2, ZERO events — m95pay2); use --boundaries >= 2.**
- **gdb prints a stop-location line (`0x... in ?? ()` / `__kernel_vsyscall`) at attach AND at the SIGINT stop — a parse gate must whitelist `^0x[0-9a-f]+ in ` lines or the acceptance FAILs on chatter (s149: m94table1/2 FAILed 7/7-gates on this).**

## CLOSING ORDER (exactly)

Terse path past ~35 calls or ~150k tokens: acceptance numbers verbatim, one short notes
paragraph, no new prose, no file opened "to double check". Closing is PART of the milestone.
0. Overwrite `SESSION_CURSOR.md` (<= 600 B): `<ID> | acceptance <tag> PASS/FAIL | merged? |
   next command` — BEFORE anything else below, so a cut turn resumes here.
1. `## Session <N>` APPENDED to `SESSION_NOTES.md` (what changed, numbers WITH the command,
   open, next pick), <= 2 KB; never rewrite the file.
2. `NAMED.md`: append the `<ID> block` (<= 1 KB) with the numbers and the evidence filename.
3. This file, patched BY SECTION (ledger, open, box, traps); `wc -c NEXT_PROMPT.md` <= 15,500.
4. `rsync -a ~/.hermes/skills/smac-cvr-format/ ~/reverse/smac/skill/` (the gate checks the sync).
5. `git add -A && git commit -m '<ID>: checkpoint'`; `python3 scripts/gate.py --base main` GREEN.
6. Submit/merge ONLY on a real PASS: `milestone.py submit --title "..."` -> `gh pr checks <n>` ->
   `milestone.py merge <n>`. Otherwise say so and merge nothing.

## Report

One screen: what changed, acceptance numbers WITH the command, what is open, next pick.