# NEXT_PROMPT.md — footing for the next session (session 131, 2026-10-28)

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
was in flight; never `rm`/`git checkout --`. Every doc write is an append or a <= 2 KB patch; keep tool results small.
## THE LEDGER

Merged: **M54A-M82** (#39-#83). **M82 (s125, m82bit7d PASS): bits 6/7 of the flag word have NO tester.** NAMED.
**M83+M84+M84b (s128-s130, UNMERGED m83 / m84 PR #84 / m84b; m84canc2 FAIL): 0x496ad0's -9999 is the DIALOG-CANCEL SENTINEL, not a price key — Escape arms [chooser_sub 0x6a9e9c+0xa774] = -1, gate 0x497683/0x49768f returns 0xffffd8f1; only 0x4187be `cmp edi,0x270f` enters 0x418d7d. NAMED.
**M84e (s133, `m84edisp1/2/3` FAIL, UNMERGED milestone/m84e) — 0x4d00 IS A QUEUE POST (queue 0x91db70, dispatcher 0x52bce0, handler 0x52ed7d, sender 0x4194a4); the POST is gated at 0x4193b2-0x4193b9 on ds:0x920434 != 0 (live 0) so a loaded game exits at 0x4194b1, NO POST. RETRACT M70 (0x4194b3 is in the SENDER). NAMED.
**M84f (s135, milestone/m84f, `m84fpath1` FAIL): the 0x4d00 block RUNS on a UI insert (CHOOSER 2 / CASE 1 / BUMP 7 / EXIT 1 / NETCALL 1, pend 5->6) and stops at `je 0x4194b1` (cursor zero, NO POST); flag-1 arm unmeasured. NAMED.
**M85 (s136-s137, milestone/m85 PR #90, `m85cens5` PASS): the solo boundary IS live — FUN_00521070 (MP 7-stage driver) 0 visits (0x52145e silence BY DESIGN), 0x51f320 round-inc once/boundary; m44_idle cannot drive under gdb (TracerPid assert) — census drives with m55_boundary. s138 RETRACTS 'FUN_005a7970 entered once/boundary' (m86cens2: 0 hits). NAMED.
**M86 (s138, milestone/m86, `m86cens1`+`m86cens2` FAIL; docs carried by milestone/m87): FUN_005a7970's legs mapped — exits 0x5a7e00/0x5a7e0d -> 0x5a8f7d; 0x5a7e73 `jne 0x5a7f9f` SKIPS the 64-record band loop unless arg1 == the short at 0x93325c/68/74 (live 10/25/26); its tails 0x5a7d00/0x5a7f67 `or BYTE PTR [eax*4+0x98adb9],0x1` (+0x31 bit0) also need 0x573a90 != self AND ds:0x920434!=0 (live 0) AND (1<<arg0)&ds:0x985b10. NAMED.
**M87 (s138, milestone/m87, `m87trig2` PASS 8/8 gates; `m87trig1` FAIL on my own typo 0x5aaccb!=0x5aaacb) — THE CALLER OF FUN_005aaa20 IS FUN_005aadf0, ON THE FIRST BOUNDARY AFTER A FRESH LOAD:** attribution by return site (ret 0x5aaf4b -> site 0x5aaf46 `e8 d5 fa ff ff call 0x5aaa20`); FUN_005aadf0's only call site is 0x4f35cb inside FUN_004f34b0 (298 B, 1 caller). aaa20(5) took the LIVE leg (save=0 -> `je 0x5aaaa0`), read its PER-FACTION SLOT [faction*191+0x94d7fc] = 8 (KIND 0 -> FUN_005aa880 never ran), stored -1 (0x5aaac1), called FUN_005a7970(5,8,0) at 0x5aaacb -> WALK 3, LOOP 0. CONFOUNDED: AAA-hit windows also had driver rc=1 + a 2-round jump. NAMED.
**M84c+M84d (s131/s132, `m84cprobe1`+`m84dky1` FAIL, UNMERGED m84c PR #86 / m84d): the 0x270f vocabulary is a DEAD END on both sides (see NAMED).
**M73-M75 (#74-76):** price `edi = A x B` at the gate 0x4efa5e; markup skipped when `type < 0x40` OR `type[+0x30] & 4` (0x5ac99c); PRODUCTION sets that bit (0x4efe60). **M68 FAILED**; **M63** `m63_pop.py`, `0x94de84` queued-count.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. **accept_ready.py** is the readiness oracle (`test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` — **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape, quit-prompt -> Escape (`m78_mark_clear.normalize_screen()` does all three).
2. The price/flag/marker chain — silent breakpoints or hw watchpoints + a prediction from live memory
   + a read-back: `m73_price_split.py`, `m74_flag_hw.py`, `m72_gate_watch.py` (the VISIT GATE),
   `m81_flag_writer.py`, `m84e_msg_dispatch.py`, `m85_tech_census.py`, `m86_helper_legs.py` and
   `m87_aaa20_trigger.py` (leg/trigger censuses: PREDICTIONS from live memory, then OBSERVED counters,
   then the branch bytes they named); the rest self-document (`m75/m76/m84_cancel_sentinel`).
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py`, `evidence.py audit [--delete]`/`budget`,
   `scratch/m71/dis.py LO HI [cap]` (objdump window; import it as a module, `dis` clashes with stdlib).
## THE PICK

**M88: the per-faction SLOT — what writes `[faction*191*4 + 0x94d7fc]` (the kind FUN_005a7970 then refuses), and who calls FUN_004f34b0?** M87 CLOSED (m87trig2 PASS 8/8): fresh load -> first boundary -> FUN_005aadf0 (site 0x4f35cb in FUN_004f34b0) -> FUN_005aaa20(5) -> slot 8 -> FUN_005a7970(5,8,0) -> table-miss (shorts 10/25/26) -> neither tail ran.
Next: static first — `python3 scratch/m71/dis.py 4f34b0 4f35d0`, the containment of 0x4f35cb's caller, and a Python window over scratch/m574/text.txt for stores to `0x94d7fc` (never grep the 40 MB file raw); then a census with PRINTF-ONLY bps at the slot writers plus 0x5aadf0/0x5aaa20 entries, armed BEFORE the load completes if the write happens during load. FIRST fresh-load (`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch`). PASS iff the store that puts 8 in faction 5's slot is attributed to a pc whose bytes are printed AND the slot is read back before/after.

## STILL OPEN (in priority order)

1. **M88 (the pick): who writes the per-faction slot `[faction*191*4+0x94d7fc]` = 8 and who calls
   FUN_004f34b0** — see THE PICK. Residue: chooser case 7 (no direct `call` 0x496950); cursor print at
   **0x49771c**; bit 5 (0x531782); who clears bit 6; alpha 0x5a6cd0; ds:0x920434 naming conflict.
2. **M67's plan-descending LIST order has no code behind it** (zero sites read plan byte `+42`); the
   **`-3 / -6` stride CONFLICT** stands (`0x984d38 + (-v)*48` at 0x40adae/0x4164f5 vs `+(-v)*16` at
   0x418914/0x41894d). Keep the suite green: `scripts/gate.py` runs every `test_*.py` + `check_classes.py`.

## LIVE FACTS / KIT

- **Box at s138b:** `terran.exe` UP (pid 250234), `m54b_clean.SAV` fresh-loaded, 2150 r50; `m87_aaa20_trigger.py` is the trigger census (relaunch FIRST: the AAA hit only appears on the first boundary after a load). The s135
   state swallowed Enter AND measured bar clicks — fresh load is the repair; chooser candidates were
   EMPTY at 2150, re-check at 2153). X focus law: see TRAPS. **The PANE decides where INSERT lands:** pass the index the pane
   shows (read `*(int *)0x6a9480 + 0x3ff3c`), else the queue grows on another base while m57 prints
   "INSERT 1 never landed" (s133). A quit-prompt mid-window swallows every click — run
   `m78_mark_clear.normalize_screen()` (it Escapes a quit-prompt; Return QUITS the game) first. Records are re-inited between rounds. **One box, ONE session:** check `git log -1` and `pgrep -a gdb` before arming (s125/s126
 collision); a veilbrowser Chrome window stacked at 0,0 makes `xwd` OCR the browser
 (`DISPLAY=:99 xdotool windowraise 0x400004`). Gate globals: `0x920434`=0, `0x985b10`=0x08 (human mask = player 3), `0x985b11`=0xff, cur_player `0x985dcc`=3; `*DAT_008f0d60` = the base record (+0x40 storage, +0x4c pending, +0x50..+0x74 queue).
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> (enqueue) -> **read `pending` AND the head back** -> the run. Misread `movie` ~1 in 3: re-run `--relaunch`, never Return on the save browser. `artwork-close` is NOT a dialog — click its red CLOSE bar (`smac_play.close_bar`).
- gdb: 4 hw watchpoints and 10-16 silent breakpoints work (~35 s per boundary); conditional bps keep other records out of the log; PREFER REGISTER-ONLY conditions on hot addresses (memory-read conditions cost seconds/hit — s133). No `si` in a command list; stdout DRAINED (`stdbuf -o0`); a watchpoint reports the pc AFTER the store.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` (double the offset) and a POINTER to the base record. Records are BYTES: type record (stride 52, base `0x98ad88`, **8 FACTION BANDS OF 64**, M80): name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0 validator, bit 2 markup-off, bit 8 sweep marker); base record: name `+19`, storage `+0x40`, pending `+0x4c`, queue `+0x50..+0x74`, `+0x98` = storage copy.
- **Evidence budget: the gate FAILs at 30 MB** — prune with `evidence.py audit --delete` BEFORE adding.

## TRAPS

- **Register semantics live in the encoding, not the name:** `[reg*4+0x98adb8]` means the register
  holds `tid*13` (52/4), `[reg+0x98adb8]` the BYTE address `tid*52`; a conditional bp testing such
  a register against the bare tid can NEVER fire.
- **Grep objdump case-sensitively** (`DWORD PTR`, not `ptr [`); a read-modify-write through a COPIED
  register (`mov ax,[x]; or al,4; mov [x],ax`, 0x4efe60) evades store-shape greps — HARDWARE
  watchpoints on the FIELD answer "who writes it" in one run (a LOW-WORD watchpoint misses BYTE
  stores to +0x31).
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it.**
  Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit
  prompt — never OK). Run `m78_mark_clear.normalize_screen()` first.
- **A census interleaved into a gdb log needs O_APPEND on GDB's own fd**; a census snapshots a STOPPED engine: order events by VISIT, not by boundary.
- **Gates must PREDICT from live memory, then be confirmed by counters** — cens1 FAILed because it
  demanded hits at sites the taken leg cannot reach (M85's wrong-question trap, new hat). A counter at
  a site that is BOTH a branch target and a loop-completion fallthrough is NOT a leg proof (0x5a7f9f).
- A gdb-log tag alternation must be LONGEST-first (`MARK` swallows `MARKSET`); a bp printf must NOT
  print inferior strings (aborts the batch, DETACHES mid-window); template expressions go in printf
  ARGUMENTS, never the format string; in a two-branch `re` alternation `m.group(1)` is the WHOLE
  match. Never trust one 3 s read of a gdb log for arming.
- **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (m79net1: 128/322/323/194 — FACTION BANDS, M80): attribute the sweep by its own predecessor. **The gate visit arrives in the boundary AFTER the sweep marks** (m79net2): a poke window needs >= 3 boundaries, 4 overruns the 420 s cap.
- **Focus: `getactivewindow` is a RED HERRING (always errors, no WM on :99) — use `getwindowfocus
  getwindowname`.** A box can swallow turn-end input WITH focus fine (s135 state): prove keys land via
  a classify flip before blaming input. **Vision-tool coords are SCALE-SHIFTED** — click targets from
  OCR word bboxes (TURN COMPLETE center (675,416); (685,471) is the recenter box). **m44_idle asserts
  TracerPid==0** — never a driver under a census gdb; use m55_boundary.
- A clean reload does NOT carry records created live last session (M80's 324/325 vanished on reload,
  reappeared between runs): census the watched slots BEFORE arming.
- base+0xd0 (`credit`) is written ONLY at player-record init (0x6310c6/0x631154) — income is never
  recomputed per round; University Base credit>0 cannot be restored by turns; use the per-boundary
  storage poke 200.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by
  "first empty slot", never treat slot 10 (`+0x78`) as an entry, never read a stale tail as proof an
  id IS queued. Id 0 is both Colony Pod and the empty marker; the sentinel is -39; a negative value
  belongs to the TYPE (196 -> -6, 195 -> -3).
- **A PASS on a shape that cannot discriminate is not a PASS:** compute candidate predictions from
  the baseline first; refuse the shape if they all agree. The harness race is real (`player walk
  came home to us after the flip` = the window spans two rounds): RE-RUN, never edit the floor.
- One variable at a time; if two things moved together write "confounded", not "because". Documents
  lose to instruction bytes only after a poke — until then REPORT the conflict.
- **`milestone.py start <id>` resets the working tree to main**, so footing carried from an unmerged
  branch (docs + scripts) AND `SESSION_CURSOR.md` must be re-written AFTER it (mine reverted to
  s127's line and my write was refused as stale).
- **A list cursor read BEFORE the seek is the PREVIOUS cursor:** the chooser pump seeks with
  `call 0x4026b0` at 0x497717, so a node print at 0x497704 shows the old node (m84cprobe1 G3 was
  this, not the game) — print at 0x49771c.
- **ZERO CALLS CAN BE THE GAME, NOT THE INSTRUMENT:** before betting an acceptance on a function
  with no fixed-displacement caller, scan every rw region of terran.exe for its vptr
  (`/proc/pid/mem`, no gdb — `scratch/m84d/probe3.py`) and confirm an instance exists; prove arming
  from the log ("Breakpoint 1 at ..." + a clean "[Inferior 1 ... detached]").
- Never (also in the session prompt): commit to main; kills by name; Escape on the title screen; OK on
  the quit prompt; `--mode stop`; `file://` with `--load`; a clear-prefixed command; backticks in a
  commit message; `skill_manage delete`.


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