# NEXT_PROMPT.md — footing for the next session (session 142, 2026-10-28)

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

Merged: **M54A-M82** (#39-#83); **M87 (#90)**, **M88**, **M89 (#93)**, **M90 (#95)** — full detail in NAMED.md. UNMERGED branches: M83/M84/M84b/M84e/M84f (0x496ad0's -9999 is the DIALOG-CANCEL sentinel, Escape arms [0x6a9e9c+0xa774] = -1; the 0x4d00 queue post is gated at 0x4193b2-0x4193b9 on ds:0x920434 != 0, live 0, so a UI insert posts NOTHING), M86 (FUN_005a7970's legs: 0x5a7e73 skips the 64-record band loop unless arg1 == the short at 0x93325c/68/74 = Alloys/SingMec/ConSing; both bit-set tails need ds:0x920434 != 0 AND (1<<arg0)&ds:0x985b10), **milestone/m91 (M91, `m91score1` FAIL 6/7)**.
**M90 (s141, #95, `m90tech2` PASS 8/8):** the per-faction slot [0x94d7fc + fac*8380] IS a TECH INDEX 0..88 chosen by FUN_005aa030(faction) (gate FUN_005a6cd0 = "prereq known", tested as [0x985c1c + prereq] & (1<<fac); tie `_rand`), returned verbatim by FUN_005ab000 -> FUN_0048b9a0 (call 0x48bae4, landing 0x48bae9) and stored at 0x5aa9d3. bVar14 in 48b9a0 UNDECODED. NAMED.
**M91 (s142, milestone/m91, `m91score1` FAIL 6/7 — G3 FALSIFIED, nothing merged):** FUN_005a90a0(idx, fac, arg2) SCORES `SUM over four (cost, demand) pairs of (demand*m+1)*cost` — costs *(0x92fdc4 + idx*44 +0,+4,+8,+0xc) (that record's prereq1 is +16 = 0x92fdd4, its name +32: M90's "base 0x92fdd4" is the +16 FIELD, not the record start), demand *(fac*8380 + 0x94d810/14/18/1c), m = 1 if arg2 != 0 else 4/2 by 0x985ac4 bit 0x200 (live SET), halved at 0x5a92fd iff all four pairs inert (bc = bit-0x10 popcount of 0x94d448 dwords 1..7; [fac*8380+0x94e488] >= 4): **predicted == the engine's [ebp-0x4] at 0x5a930b on 12/12 traced candidates.** A 62-iteration tail (0x5a94fd-0x5a95f8) then adds byte[fac*8380+0x94e5a8+esi]*Tc over divisors keyed by byte[+0x94eda8+esi] in {7,2,0} (fac5 idx36 15->112, fac4 idx60 19->38, unchanged where Tc == 0); the level leg 0x5a93b3-0x5a94f2 runs ONLY when arg2 != 0 (0x5a9375 `je 0x5a9500`). FUN_005aa030 then divides (0x5aa1e4 `shl eax,8; idiv edi`, divisor = max(FUN_005a6d40(p1,1), FUN_005a6d40(p2,1))) and **picks the candidate with the strictly-largest draw `_rand() % (score+1)` (0x5aa217-0x5aa230, compare 0x5aa232) — NOT the max score**: fac4 winner idx43 final 16 beat candidate idx60 final 38 (draws 1838 vs 2). NAMED.
**M73-M75 (#74-76):** price `edi = A x B` at the gate 0x4efa5e; markup skipped when `type < 0x40` OR `type[+0x30] & 4` (0x5ac99c); PRODUCTION sets that bit (0x4efe60). **M68 FAILED**; **M63** `m63_pop.py`, `0x94de84` queued-count.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape, quit-prompt -> Escape (`m78_mark_clear.normalize_screen()` does all three).
2. The price/flag/marker chain — silent breakpoints or hw watchpoints + a prediction from live memory
     + a read-back: `m73_price_split.py`, `m74_flag_hw.py`, `m72_gate_watch.py` (the VISIT GATE),
     `m81_flag_writer.py`, `m85_tech_census.py`, `m86_helper_legs.py`, `m87_aaa20_trigger.py`,
     `m88_slot_watch.py`, `m89_alloc_census.py`, `m90_tech_choice.py`, `m91_scorer_census.py` (newest: the scorer's OWN base at 0x5a930b, its final at the 0x5aa159 landing, the draw at 0x5aa232, the winner at 0x5aa247 — predictions computed from the cost/demand fields gdb reads out of live memory at the hit) — also FUN_005aa030's return at
     its landing 0x48bae9, the store at 0x5aa9d3, then the tech NAME read from live memory at
     0x92fdd4+idx*44+16; PREDICTIONS, then counters, then the branch bytes named); rest self-doc.
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py`, `evidence.py audit [--delete]`/`budget`,
   `scratch/m71/dis.py LO HI [cap]` (objdump window; import it as a module, `dis` clashes with stdlib).
## THE PICK

**M92: the scorer's 62-category TAIL (0x5a94fd-0x5a9698) and what [fac*8380+0x94e488], [+0x94e5a8+esi] and [+0x94eda8+esi] are.** M91 CLOSED the base (12/12 exact) and the draw rule; the FINAL score is still unpredicted. `python3 scratch/m71/dis.py 5a95fd 5a96a0` then `5a96a0 5a9720`; census `final == base + tail` on >= 2 windows with the SAME instrument (scripts/m91_scorer_census.py — swap gates G2/G3 for the tail formula and KEEP the base gate). Print the three byte arrays at the 0x5a930b hit so the tail is predicted from live memory, and keep the winner gate on the DRAW (max draw), never on max score.
## STILL OPEN (in priority order)

1. **M92 (the pick): the tail loop 0x5a94fd-0x5a9698 — byte[fac*8380+0x94e5a8+esi] * Tc over divisors keyed
   by byte[+0x94eda8+esi] in {7,2,0}, divided by [fac*8380+0x94e488] — and who WRITES those three arrays.**
   Then: where the chosen index becomes the ACTIVE project (pay-site conflict 0x4f0ca6 vs 0x4efedd); the
   human leg (FUN_00625af1 at 0x5aa20d, bVar14 in FUN_0048b9a0); the SIBLING slot [esi+0x94d800] fed by
   FUN_005aab70; the band flag [esi+0x94d430] bit 0x40; ds:0x926bd4 / ds:0x920434 naming; chooser case 7;
   cursor print at **0x49771c**; bit 5 (0x531782); who clears bit 6.
2. **M67's plan-descending LIST order has no code behind it** (zero sites read plan byte `+42`); the
   **`-3 / -6` stride CONFLICT** (`0x984d38 + (-v)*48` vs `+(-v)*16`). Suite: `scripts/gate.py`.

## LIVE FACTS / KIT

- **Box at s142:** `terran.exe` UP (pid 262651), round 83, University Base minerals 0 credit 0 —
  accept_ready BLOCKS on `credit <= 0` (income add gated on d0 > 0; its printed FIX is a clean reload),
  but a census that needs only BOUNDARIES runs on it: M91's acceptance did 3 boundaries with no reload.
  Slots [0x94d7fc + fac*8380] after that run = [-1, 44, 32, 32, 43, 36, 13, 32]; 0x985ac4 bit 0x200 is
  SET (scorer m = 4), 0x926bd4 = 0, e488 per faction = [0,1,10,1,3,1,9,1]. `scripts/m91_scorer_census.py`
  is the scorer census; NO relaunch is needed (5aadf0 -> aaa20 -> 5aa880 -> 5ab000 -> 48b9a0 -> 5aa030
  runs whenever a faction's slot is negative). X focus law: see TRAPS. **The PANE decides where INSERT
  lands** (pass the index the pane shows: `*(int *)0x6a9480 + 0x3ff3c`). A quit-prompt mid-window swallows
  every click — run `m78_mark_clear.normalize_screen()` first.
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> (enqueue) -> **read `pending` AND the head back** -> the run. Misread `movie` ~1 in 3: re-run `--relaunch`, never Return on the save browser. `artwork-close` is NOT a dialog — click its red CLOSE bar (`smac_play.close_bar`).
- gdb: 4 hw watchpoints and 10-16 silent breakpoints work (~35 s per boundary); conditional bps keep other records out of the log; PREFER REGISTER-ONLY conditions on hot addresses (memory-read conditions cost seconds/hit — s133). No `si` in a command list; stdout DRAINED (`stdbuf -o0`); a watchpoint reports the pc AFTER the store.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros — grep
  `4ef5d0:`, not `004ef5d0:`; only lines matching `^[0-9a-f]{6,8}:\t` are instructions). Ghidra
  pseudocode is `ghidra_out/shard_NNN.c`. Parse with Python (`scratch/m71/dis.py`), never read whole.
  `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` (double the offset) and a POINTER to the base record. Records are BYTES: type record (stride 52, base `0x98ad88`, **8 FACTION BANDS OF 64**, M80): name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0 validator, bit 2 markup-off, bit 8 sweep marker); base record: name `+19`, storage `+0x40`, pending `+0x4c`, queue `+0x50..+0x74`, `+0x98` = storage copy.
- **Evidence budget: the gate FAILs at 30 MB** — prune with `evidence.py audit --delete` BEFORE adding.

## TRAPS

- **Register semantics live in the encoding, not the name:** `[reg*4+0x98adb8]` means the register
  holds `tid*13` (52/4), `[reg+0x98adb8]` the BYTE address `tid*52`; a conditional bp testing such
  a register against the bare tid can NEVER fire.
- **Grep objdump case-sensitively** (`DWORD PTR`, not `ptr [`); a read-modify-write through a COPIED
  register (`mov ax,[x]; or al,4; mov [x],ax`, 0x4efe60) evades store-shape greps — a HARDWARE
  watchpoint on the FIELD answers "who writes it" in one run.
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it.**
  Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit
  prompt — never OK). Run `m78_mark_clear.normalize_screen()` first.
- **Gates must PREDICT from live memory, then be confirmed by counters** — cens1 FAILed because it
  demanded hits at sites the taken leg cannot reach. A counter at
  a site that is BOTH a branch target and a loop-completion fallthrough is NOT a leg proof (0x5a7f9f).
- A gdb-log tag alternation must be LONGEST-first (`MARK` swallows `MARKSET`); a bp printf must NOT
  print inferior strings (aborts the batch, DETACHES mid-window); template expressions go in printf
  ARGUMENTS, never the format string; in a two-branch `re` alternation `m.group(1)` is the WHOLE
  match.
- **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (128/322/323/194 — FACTION BANDS, M80): attribute the sweep by its own predecessor. **The gate visit arrives in the boundary AFTER the sweep marks**: a poke window needs >= 3 boundaries.
- **Focus: `getactivewindow` is a RED HERRING (always errors, no WM on :99) — use `getwindowfocus
 getwindowname`.** A box can swallow turn-end input WITH focus fine: prove keys land via a classify flip
 before blaming input. **Vision-tool coords are SCALE-SHIFTED** — click from OCR word bboxes (TURN
 COMPLETE center (675,416); (685,471) is the recenter box). **m44_idle asserts TracerPid==0** — never a
 driver under a census gdb; use m55_boundary.
- base+0xd0 (`credit`) is written ONLY at player-record init (0x6310c6/0x631154) — income is never
  recomputed per round; University Base credit>0 cannot be restored by turns; use the per-boundary
  storage poke 200.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by
  "first empty slot", never treat slot 10 (`+0x78`) as an entry, never read a stale tail as proof an
  id IS queued. Id 0 is both Colony Pod and the empty marker; the sentinel is -39; a negative value
  belongs to the TYPE (196 -> -6, 195 -> -3).
- **A PASS on a shape that cannot discriminate is not a PASS:** compute candidate predictions from the
  baseline first; refuse the shape if they all agree. The harness race is real (a window spanning two
  rounds): RE-RUN, never edit the floor.
- **`milestone.py start <id>` refuses a dirty tree and resets to main**: stash a carried doc edit,
  start, pop (s140 did exactly that with the skill's code-atlas carrier). `SESSION_CURSOR.md` must be
  re-written AFTER it.
- **A list cursor read BEFORE the seek is the PREVIOUS cursor:** the chooser pump seeks with
  `call 0x4026b0` at 0x497717, so a node print at 0x497704 shows the old node (m84cprobe1 G3 was
  this, not the game) — print at 0x49771c.
- **ZERO CALLS CAN BE THE GAME, NOT THE INSTRUMENT:** before betting an acceptance on a function
  with no fixed-displacement caller, scan every rw region of terran.exe for its vptr
  (`/proc/pid/mem`, no gdb — `scratch/m84d/probe3.py`) and confirm an instance exists; prove arming
  from the log ("Breakpoint 1 at ..." + a clean "[Inferior 1 ... detached]").


- **The research pick is a MAX OF RANDOM DRAWS, not a max score:** FUN_005aa030 draws `_rand() % (score+1)`
  per candidate and keeps the strictly-greater one (0x5aa217/0x5aa232), so a low-score winner IS the rule
  (m91score1 G3: winner final 16 beat a candidate at 38). Never re-gate a census on max-score.
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