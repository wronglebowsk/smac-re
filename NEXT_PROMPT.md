# NEXT_PROMPT.md — footing for the next session (session 148, 2026-10-29)

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

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90 (#95), M91 (#97, m91score5 PASS 7/7) — full detail in NAMED.md. UNMERGED branches: M83/M84/M84b/M84e/M84f (0x496ad0's -9999 is the DIALOG-CANCEL sentinel, Escape arms [0x6a9e9c+0xa774] = -1; the 0x4d00 queue post is gated at 0x4193b2-0x4193b9 on ds:0x920434 != 0, live 0, so a UI insert posts NOTHING), M86 (FUN_005a7970's legs: 0x5a7e73 skips the 64-record band loop unless arg1 == the short at 0x93325c/68/74 = Alloys/SingMec/ConSing; both bit-set tails need ds:0x920434 != 0 AND (1<<arg0)&ds:0x985b10).
**M90 (s141, #95, `m90tech2` PASS 8/8):** the per-faction slot [0x94d7fc + fac*8380] IS a TECH INDEX
0..88 chosen by FUN_005aa030(faction) (gate FUN_005a6cd0 = "prereq known" = [0x985c1c+prereq]&(1<<fac);
tie `_rand`), returned by FUN_005ab000 -> FUN_0048b9a0 (call 0x48bae4, landing 0x48bae9), stored at
0x5aa9d3. bVar14 in 48b9a0 UNDECODED. NAMED.
**M91 (s142-s143, #97, `m91score5` PASS 7/7):** FUN_005a90a0(idx, fac, arg2) BASE at 0x5a930b = `SUM
over four (cost,demand) pairs of (demand*m+1)*cost` — costs *(0x92fdc4+idx*44 +0,+4,+8,+0xc) (record
prereq1 = +16 = 0x92fdd4), demand *(fac*8380 + 0x94d810/14/18/1c), m = 1 if arg2 != 0 else 4/2 by
0x985ac4 bit 0x200 (live SET), halved iff all four pairs inert (bc = bit-0x10 popcount of 0x94d448
dwords 1..7; [fac*8380+0x94e488] >= 4): predicted == engine 27/27. The tail (M92) runs ONLY when
arg2 == 0 (0x5a9375 je 0x5a9500). FUN_005aa030 divides (0x5aa1e4 shl 8; idiv max(FUN_005a6d40(p1,1),
p2)) and **picks the STRICTLY-largest draw `_rand() % (score+1)` (0x5aa217-0x5aa232, equal draws do
NOT replace, asc 0..88) — NOT max score** (falsified 3x). NAMED.
**M92 (s144-s146, #98, `m92tail18` PASS 8/8, fresh m54b_clean load r51->55):** FUN_005a90a0's tail
(entered 0x5a9500 iff arg2==0) EXACTLY predicted: **TAILOUT at 0x5a9698 == BASE + the tail simulated
from the per-faction block — 39/39 candidates, 0 mismatches, 2 qualifying windows, naive one-factor
splits 19** (cat/mult/div offsets, the cat7/cat2/cat0/band legs and gates: skill code-atlas.md).
**Block FROZEN within a round** (0/39 + 0/19 per-TAIL-hit dumps differ from own-round snapshots;
div cross-check 39/39 bad=0), moves BETWEEN rounds — s145's in-round-motion claim RETRACTED (census defects, see TRAPS). Census needs a FRESH load. NAMED.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape, quit-prompt -> Escape (`m78_mark_clear.normalize_screen()` does all three).
2. The price/flag/marker chain — silent breakpoints or hw watchpoints + a prediction from live memory
     + a read-back: `m73_price_split.py`, `m74_flag_hw.py`, `m72_gate_watch.py` (the VISIT GATE),
     `m81_flag_writer.py`, `m85_tech_census.py`, `m86_helper_legs.py`, `m87_aaa20_trigger.py`,
     `m88_slot_watch.py`, `m89_alloc_census.py`, `m90_tech_choice.py`, `m91_scorer_census.py`,
     `m92_tail_census.py` (newest: base 0x5a930b, TAIL entry 0x5a9503 (div live + 64+64 B mults/cats
     appended per hit to scratch/<tag>_tailarrs.bin), TAILOUT 0x5a9698, final 0x5aa159, draw 0x5aa232,
     winner 0x5aa247; simulate EACH candidate from the round LIVE at its BASE hit; pair tailout
     FIRST-wins; run on a FRESH load) — also FUN_005aa030's return at
     its landing 0x48bae9, the store at 0x5aa9d3, then the tech NAME read from live memory at
     0x92fdd4+idx*44+16; PREDICTIONS, then counters, then the branch bytes named); rest self-doc.
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py`, `evidence.py audit [--delete]`/`budget`,
   `scratch/m71/dis.py LO HI [cap]` (objdump window; import it as a module, `dis` clashes with stdlib).
## THE PICK

**M93 CONTINUES (s148 NOT accepted): make the POST ladder predict every traced final.**
`s148` decoded the whole leg (NAMED.md M93 block; do NOT re-derive) and the census already carries a
ladder model (`ladder_pred`, gate G9) that gets **9/13** on `--tag m93post2 --poke-index 7 --poke-extra
2,6 --rounds 4 --timeout 100` (G1-G8 green). Four fixes, in this order: (1) the model has NO leg for
0x5a9c17 (x2, key 0x9851cc) / 0x5a9c68 (x3/2, key 0x9851fc), both gated on [0x927a80+fac*1436] > 0, and
its q-gate checks only 0x984fec/0x984fbc (engine also 0x98531c/0x98534c); (2) 4 apply sites have no
breakpoint — 0x5a9c14/0x5a9c74/0x5a9df0/0x5a9eb5/0x5a9f83, gdb blocks are in scratch/m93/apply_patches.py
(its anchor `G8_control=g8)` is stale, the dict now ends `G9_post_tail_ladder_final=g9)`); (3) the
specials are read from the candidate's ROUND-BOUNDARY snapshot while the ladder reads them LIVE — print
0x9303xx/0x9305xx/0x9307xx/0x9308xx/0x933xxx/0x984fxx/0x985xxx/0x98adee at the PENTRY hit and prove the
freeze; (4) fac5 idx4/idx45: the model fires PE2 the engine skipped (over-application, same suspect).
## STILL OPEN (in priority order)

1. **After M93 (THE PICK): the pay-site conflict 0x4f0ca6 vs 0x4efedd; the human leg (FUN_00625af1 at
   0x5aa20d, bVar14 in FUN_0048b9a0); who writes 0x94e488/0x94e5a8/0x94eda8/0x950664 between rounds;
   the SIBLING slot [esi+0x94d800] (FUN_005aab70); the band flag [esi+0x94d430] bit 0x40; ds:0x926bd4 /
   ds:0x920434 naming; chooser case 7; cursor print at **0x49771c**; bit 5 (0x531782).**
2. **M67's plan-descending LIST order has no code behind it** (zero sites read plan byte `+42`); the
   **`-3 / -6` stride CONFLICT** (`0x984d38 + (-v)*48` vs `+(-v)*16`). Suite: `scripts/gate.py`.

## LIVE FACTS / KIT

- **Box at s148:** fresh m54b_clean load r50->55 (census ran there); G1-G8 green on that load, G9 fails.
  `scripts/m93_post_census.py` = m92's census + the POST prints + `ladder_pred`/G9 — run on a FRESH load.
  The census pokes slots 7/2/6 to -1; a degraded box cannot be rescued by poking. 0x985ac4 bit 0x200 SET
  (scorer m = 4). The human mask byte at 0x985b10 = 0x08 -> ONLY faction 3 is human (a dword read there
  shows 0x985b10 = 65288, mask the low byte). X focus law: see TRAPS. **The PANE decides where INSERT
  lands** (pass the index the pane shows: `*(int *)0x6a9480 + 0x3ff3c`). A quit-prompt mid-window
  swallows every click — run `m78_mark_clear.normalize_screen()` first.
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> (enqueue) -> **read `pending` AND the head back** -> the run. Misread `movie` ~1 in 3: re-run `--relaunch`, never Return on the save browser. `artwork-close` is NOT a dialog — click its red CLOSE bar (`smac_play.close_bar`).
- gdb: 4 hw watchpoints and 10-16 silent breakpoints work (~35 s per boundary); conditional bps keep other records out of the log; PREFER REGISTER-ONLY conditions on hot addresses (memory-read conditions cost seconds/hit — s133). No `si` in a command list; stdout DRAINED (`stdbuf -o0`); a watchpoint reports the pc AFTER the store.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros — grep
  `4ef5d0:`, not `004ef5d0:`; only lines matching `^[0-9a-f]{6,8}:\t` are instructions). Ghidra
  pseudocode is `ghidra_out/shard_NNN.c`. Parse with Python (`scratch/m71/dis.py`), never read whole.
  `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` (double the offset) and a POINTER to the base record. Records are BYTES: type record (stride 52, base `0x98ad88`, **8 FACTION BANDS OF 64**, M80): name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0 validator, bit 2 markup-off, bit 8 sweep marker); base record: name `+19`, storage `+0x40`, pending `+0x4c`, queue `+0x50..+0x74`, `+0x98` = storage copy.
- **Evidence budget: the gate FAILs at 30 MB** — prune with `evidence.py audit --delete` BEFORE adding.

## TRAPS

- **The `fired=` list on a `LADDER-MISMATCH` line is the MODEL's prediction, not observed events** — a leg listed there that no breakpoint caught is the model over-applying, not the instrument missing it (s148: fac5 idx4/idx45). A no-event at an apply site is only evidence after you have checked a breakpoint EXISTS there (4 did not: 0x5a9c17/0x5a9c77/0x5a9df3/0x5a9eb5).
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
  SETS: m92's G8 read c["tdiv"], a field nothing assigned, so G8 was structurally False for 4 runs
  while the milestone itself was green** (s146). A gdb-log tag alternation must be LONGEST-first
  (`MARK` swallows `MARKSET`); a bp printf must NOT print inferior strings (aborts the batch, DETACHES
  mid-window); template expressions go in printf ARGUMENTS, never the format string; in a two-branch
  `re` alternation `m.group(1)` is the WHOLE match.
- **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (128/322/323/194 — FACTION BANDS, M80): attribute the sweep by its own predecessor. **The gate visit arrives in the boundary AFTER the sweep marks**: a poke window needs >= 3 boundaries.
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