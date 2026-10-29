# NEXT_PROMPT.md — footing for the next session (session 153, 2026-10-29)

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

Merged: M54A-M82 (#39-#83), M87-M89 (#90/#93), M90 (#95), M91 (#97), M92-M97 (#98-#103) — full detail in NAMED.md. UNMERGED branches: M83/M84/M84b/M84e/M84f (0x496ad0's -9999 is the DIALOG-CANCEL sentinel, Escape arms [0x6a9e9c+0xa774] = -1; the 0x4d00 queue post is gated at 0x4193b2-0x4193b9 on ds:0x920434 != 0, live 0, so a UI insert posts NOTHING), M86 (0x5a7e73 skips the 64-record band loop unless arg1 == 0x93325c/68/74 = Alloys/SingMec/ConSing; both bit-set tails need ds:0x920434 != 0 AND (1<<arg0)&ds:0x985b10).
**M90-M94 (#95/#97/#98/#99/#100), all in NAMED.md:** the slot IS a tech index 0..88, chosen by the
STRICTEST-largest draw, tail runs only arg2==0; FUN_005a90a0's tail (entered 0x5a9500 iff arg2==0)
EXACTLY predicted — **TAILOUT 0x5a9698 == BASE + the tail simulated from the per-faction block**
(39/39, 2 windows; the block is FROZEN within a round and moves between rounds; a census needs a FRESH
load); the POST cascade 0x5a9747-0x5aa022 EXACTLY predicted (13/13) — `0x5a9020(a,X,f)` = prereq-closure
membership at depth f, stages apply iff idx is INSIDE their set, and **freeze ladder inputs at the TAIL
HIT, not the boundary snap**; DIVISOR `[fac*8380+0x94e488]` is RECOMPUTED every round by FUN_00556690
(upkeep stage, arg=fac; also 0x59dd43): reset 0x5566cf + rebuild 0x556a87 **== faction base count** (8/8).
All legs: skill code-atlas.md.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape, quit-prompt -> Escape (`m78_mark_clear.normalize_screen()` does all three).
2. The price/flag/marker chain — silent breakpoints or hw watchpoints + a prediction from live memory
     + a read-back: `m72_gate_watch.py` (the VISIT GATE), `m90_tech_choice.py`,
     `m92_tail_census.py` (base 0x5a930b, TAIL 0x5a9503, TAILOUT 0x5a9698,
     final 0x5aa159, draw 0x5aa232; simulate EACH candidate LIVE at its BASE hit on a FRESH load),
     `m94_table_watch.py` (4 hw watchpoints on any 4 dwords), `m95_pay_sites.py` (13 cond bps + 2 hw wp on storage/pending of one base row; per-boundary storage poke; names the pay branch + POP caller; `--tag m95payN --boundaries 2`); prints pc+new+round+cur_player, names
     the writer by containment via ghidra_out/index.csv, movement-vs-events self-check, pokes
     storage per boundary; PREDICTIONS, then counters, then the branch bytes named); rest self-doc.
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py`, `evidence.py audit [--delete]`/`budget`,
   `scratch/m71/dis.py LO HI [cap]` (objdump window; import it as a module, `dis` clashes with stdlib).
## THE PICK

**M95 ACCEPTED (s150, `m95pay4` PASS 9/9): pay-site conflict CLOSED** — a UI-queued completion pays
AND activates in branch A (gate 0x4efa5e -> pay 0x4efedd storage +0x40 -= price -> create 0x4eff4e ->
POP 0x4f037b, pending store 0x4ef648); 0x4f0ca6 is branch B's pay, entered ONLY for negative queue
slots (typecode = -q0), mutually exclusive, 0 live events on the UI shape. Stale tail: non-sentinel q0
with pending 0 re-produces phantoms while storage >= price. NAMED.
**M96 ACCEPTED (s151, `m96human2` PASS 12/12): the chooser's human leg is CLOSED** — the score is
scaled `shl eax,8` (0x5aa1e7, gate 0x5aa164 on ds:0x985ac4 & 0x200) and divided by the candidate's
PREREQ-CHAIN DEPTH (`FUN_005a6d40`); 13/13 divisors + quotients, fires for fac2 too — **NOT
human-specific**. The human mask byte 0x985b10 only (a) gates the forced pick
([fac*8380+0x94d810]/[+0x94d818] != 0 -> candidate == WORD ds:0x98adee @0x5aa251; INERT live) and
(b) swaps the DRAW to the LCG at ds:0x999fa0 (7/7 exact; non-human -> rand() % (score+1)). **THE WINNER
IS THE MAX DRAW, NOT THE MAX SCORE** (0x5aa232, best starts -999). NAMED.

**M97 ACCEPTED (s152, `m97credit3` PASS 11/11): base+0xd0 (credit) is RECOMPUTED EVERY ROUND** —
FUN_004e93f0 (eax = ds:0x8f0d60 = the current base record) stores it twice per call: 0x4e9557 `= [+0xc0]
- [+0xf0]`, 0x4e957f `-= [+0xe0]` (zeroed 0x4e9562), mirror 0x4e9590 -> +0x94; callers FUN_004f5a70
(per-base turn stage, 0x4f5ad2 + 0x4f5b46; itself at 0x5206d3) and the recalc helper
FUN_004eb6b0 (0x4eb6db). GROSS [+0xc0] is rebuilt from 0 by FUN_004e78e0; UPKEEP [+0xf0] =
DAT_008f0c38+DAT_008f0c4c (whole-faction, 0x4e9544). 0x4ef7f6/0x4eff20 write [+0x40] STORAGE, not
+0xd0; only 6 stores to `[reg+0xd0]` exist in .text. "Init-only" RETRACTED.

**M98 (THE PICK): what is [fac*8380+0x94d800]?** — the sibling of the work-item slot; live
-1,81,128,86,166,128,77,64 are >= 89, NOT tech indices (M90). Cheapest: read all 8 live, grep .text for
stores with `*8380+0x94d800`-shaped offsets, then silent bps AT those stores (NOT watchpoints — TRAPS)
over `--boundaries 2` in the `m97_credit_watch.py` shape; name the writer by containment, read back.

## STILL OPEN (in priority order)

1. **After M98: band flag [esi+0x94d430] bit 0x40 = 0 for ALL 8 factions at r66
   (dwords 0,2,c,3,9,4,8,1) -> the M89 second-ask is inert, find the setter; ds:0x926bd4 / ds:0x920434
   naming; chooser case 7; cursor print at **0x49771c**; bit 5 (0x531782); WORD ds:0x98adee (the
   forced-pick key, live 6 — record 1's +0x32 or a standalone global?); the negative-queue producer
   that reaches branch B.**

2. **M67's plan-descending LIST order has no code behind it** (zero sites read plan byte `+42`); the
   **`-3 / -6` stride CONFLICT** (`0x984d38 + (-v)*48` vs `+(-v)*16`). Suite: `scripts/gate.py`.

## LIVE FACTS / KIT

- **Box at s152:** m54b_clean r50->56 across fresh reloads; m97 income watch ran (m97credit1-3);
  pending 0, q0 STALE 2, storage 0, credit -1 (= c0 4 - f0 5 - e0 0); ebc 0x1a0e (bit 0x200 SET),
  mask 8 -> ONLY fac3 human, forced short 0x98adee = 6. New instrument: `scripts/m97_credit_watch.py
  --tag t --boundaries 2` (4 hw watchpoints on a base row's income chain + silent bps AT the credit
  stores; `M97_BASE=` picks the row).

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

- **The `fired=` list on a `LADDER-MISMATCH` line is the MODEL's prediction, not observed events** (s148); a no-event at an apply site is evidence only once a breakpoint is CONFIRMED to exist there (4 lacked one until s148). Gates must PREDICT from live memory, then be confirmed by counters; a counter at a site that is BOTH a branch target and a loop-completion fallthrough is NOT a leg proof (0x5a7f9f); a gate may only read a field the harness SETS (m92 G8).
- **Check the instrument before believing a no-event or a wrong field:** an f-string bp condition that emits `if *$ecx==X` is a DEREFERENCE and silently never fires (m95pay1/2); a bp at a `mov eax,[ebp-0xc]` RETURN site prints the OLD eax — break at the NEXT instruction (0x5aa24a; m96human1 read idx=0); `lea edi,[eax+1]` @0x5aa21a makes edi the MODULUS on the rand path, so a bp at 0x5aa232 printing `$edi` gets score+1, not the faction — read `*(int *)($ebp+8)`; name every printed field the way the parser asks (m96human1 G4/G9/G11 were key names, not the game). ZERO CALLS can be the GAME: scan /proc for the function's vptr first (`scratch/m84d/probe3.py`).
- **Register semantics live in the encoding, not the name:** `[reg*4+0x98adb8]` means the register holds `tid*13`, `[reg+0x98adb8]` the BYTE address `tid*52`; a condition testing such a register against the bare tid can NEVER fire. A read-modify-write through a COPIED register (`mov ax,[x]; or al,4; mov [x],ax`, 0x4efe60) evades store-shape greps — a HARDWARE watchpoint on the FIELD answers "who writes it" in one run.
- **gdb printf/script laws:** no inferior strings (aborts the batch and DETACHES mid-window); template expressions go in printf ARGUMENTS, never the format; `%x` prints BARE hex (no 0x); a log tag alternation must be LONGEST-first (`MARK` swallows `MARKSET`); in a two-branch `re` alternation `m.group(1)` is the WHOLE match; a multi-line `python` block in a bp command list aborts the sourced script; `dump/append binary memory` need a LITERAL end address and a snapshot reader must use the region SIZE (m92tail3-7); gdb prints a stop-location line (`0x... in ?? ()`, `__kernel_vsyscall`) at attach AND at the SIGINT stop — a parse gate must whitelist `^0x[0-9a-f]+ in ` lines (m94table1/2).
- **A >90 s gdb census NEVER runs in the foreground** — the terminal tool caps waits at 420 s and killing the census mid-run leaves Wine hung (round frozen, 0 CTRL events even after detach, s143): run background + `process_manage wait` (180 s clamp, loop), or keep `--rounds <= 4`. **Faction upkeep runs in that faction's OWN segment ~1 cycle after your turn-end: a 1-boundary window can close mid-cycle (m95pay2) — use `--boundaries >= 2`.**
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it:** Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt — never OK); run `m78_mark_clear.normalize_screen()` first. `getactivewindow` is a RED HERRING (no WM on :99 — use `getwindowfocus getwindowname`); vision coords are SCALE-SHIFTED, click from OCR word bboxes (TURN COMPLETE (675,416)); `m44_idle` asserts TracerPid==0 — never a driver under a census gdb, use m55_boundary.
- **A PASS on a shape that cannot discriminate is not a PASS:** compute candidate predictions from the baseline first; refuse the shape if they all agree. RE-RUN on a harness race, never edit the floor.
- **base+0xd0 (`credit`) is RECOMPUTED EVERY ROUND** (M97 FUN_004e93f0 0x4e9557/0x4e957f = [+0xc0] -
  [+0xf0] - [+0xe0]; "init-only" RETRACTED) — a poke there is undone next turn; gate on round movement
  and use the per-boundary storage poke 200.
- **a gdb HARDWARE watchpoint only REPORTS a VALUE CHANGE** (it re-evaluates and continues silently):
  unchanged store logs NOTHING (m97credit2: 15 GROSS stores, 0 CREDIT events). Count stores with silent
  bps AT the store instruction; keep the watchpoint as the "any other writer" check only; whitelist
  `[New LWP]` banners (they arrive AFTER an attach printf).
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by "first empty slot" or a stale tail as proof an id IS queued; id 0 is Colony Pod AND the empty marker, the sentinel is -39, a negative belongs to the TYPE (196 -> -6, 195 -> -3). **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (128/322/323/194 = FACTION BANDS, M80): attribute the sweep by its own predecessor; the gate visit arrives in the boundary AFTER the sweep marks (poke window >= 3 boundaries).
- **A list cursor read BEFORE the seek is the PREVIOUS cursor:** the chooser pump seeks with `call 0x4026b0` at 0x497717, so a node print at 0x497704 shows the old node — print at 0x49771c. **`milestone.py start <id>` refuses a dirty tree and resets to main:** stash a carried doc edit, start, pop, THEN re-write `SESSION_CURSOR.md`.
- **Grep objdump case-sensitively** (`DWORD PTR`, not `ptr [`).

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