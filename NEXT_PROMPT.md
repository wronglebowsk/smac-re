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

Survivability: before any step that can exceed 2 minutes (gdb run, relaunch, evidence audit)
overwrite `SESSION_CURSOR.md` (<= 600 B) with `<ID> | acceptance | merged? | next command` — only
you record what was in flight; never `rm`/`git checkout --`. Every doc write is an append or a <= 2 KB patch; never
read-then-rewrite a file over 10 KB; keep tool results small.
## THE LEDGER

Merged: **M54A-M82** (#39-#83). **M82 (s125, m82bit7d PASS): bits 6/7 of the flag word have NO tester** (every `test` of `0x98ad88+tid*52+0x30` uses 0x1/0x4/0x8/0x10; only bit-7 instruction is the clearer 0x577ca8). NAMED M82.
**M83+M84+M84b (s128-s130, UNMERGED milestone/m83, m84 PR #84, m84b) — 0x496ad0's -9999 IS THE DIALOG-CANCEL SENTINEL, NOT A PRICE KEY:** Escape arms `[chooser_sub 0x6a9e9c+0xa774] = -1`; the gate 0x497683/0x49768f returns 0xffffd8f1, the caller restores the queue snapshot (0x418623-0x41863f) and leaves via 0x4186d2 `jle 0x419967`; only 0x4187be `cmp edi,0x270f` enters 0x418d7d. m84canc2 G4-G7 False -> FAIL. NAMED M84/M84b.
**M84e (s133, `m84edisp1/2/3` FAIL, UNMERGED milestone/m84e) — 0x4d00 IS A QUEUE POST, ITS HANDLER
IS 0x52ed7d:** 0x584010 posts a 32-byte record to queue 0x91db70; pumps pop it into dispatcher
0x52bce0 (only 0x4d00 arm 0x52eb61/6c -> 0x52ed7d); 0x4194a4 (chooser fn 0x417ee0) is the only
sender. Handler record = 0x984d38 - tid*48 (a THIRD stride-48 site for the M67 conflict);
record+0x14 (0/1/2) selects sub-behaviours over 1436-byte records at 0x927590/0x927894. RETRACT
M70's mechanism: 0x4194b3 is in the SENDER; the cursor is PANE-relative (+0x3ff5c). The POST is
gated at 0x4193b2-0x4193b9 on ds:0x920434 != 0 (1 only from the opening-menu loop FUN_0057ecf0;
live 0) so a loaded game exits at 0x4194b1 (cursor zero, NO POST). NAMED M84e.
**M84f (s135, milestone/m84f, `m84fpath1` FAIL on my own G4; leg4/5 invalid) — THE GATE IS MEASURED
LIVE:** on a real UI insert the block RUNS (CHOOSER 2 / CASE 1 / BUMP 7 / EXIT 1 / NETCALL 1, pend
5->6) and stops at `mov eax,ds:0x920434` / `je 0x4194b1` — cursor zero + 0x4eb6b0, NO POST. gdb bp
lists must be PRINTF-ONLY (a memory write aborts the batch, 'not an lvalue', then DETACH); poke
0x920434 via python /proc/pid/mem. Flag-1 arm unmeasured. NAMED M84f.
**M85 (s136-s137, milestone/m85 PR #90, `m85cens5` PASS) — THE SOLO BOUNDARY IS LIVE AND ENTERS THE HELPER:** FUN_00521070 (MP 7-stage driver) 0 visits -> 0x52145e silence by design; FUN_005a7970 entered once/boundary (eax=0, ret 0x569948 inside FUN_0055f650, NOT the human-loop 0x507e57); tails 0x5a7d00/0x5a7f67 UNTAKEN branches; 0x51f320 fires once. m44_idle cannot drive under gdb (asserts TracerPid==0; rounds=1 snapshot degenerate) — census drives with m55_boundary. The s135 box state swallowed Enter AND measured bar clicks (cause not isolated; fresh load repairs). NAMED M85.
**M84c+M84d (s131/s132, `m84cprobe1`+`m84dky1` FAIL, UNMERGED milestone/m84c PR #86 + milestone/m84d) — THE 0x270f VOCABULARY IS A DEAD END ON BOTH SIDES:** 0x496ad0 never sees a 9999 key; 0x4a99e0 has ZERO live instances. NAMED M84c/M84d.
**M73-M75 (#74-76):** price `edi = A x B` at the gate 0x4efa5e; markup skipped when `type < 0x40` OR `type[+0x30] & 4` (0x5ac99c); PRODUCTION sets that bit (0x4efe60). NAMED. **M68 FAILED** (enqueue appends, no key named); **M63** `m63_pop.py`, `0x94de84` queued-count.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

`python3 scripts/accept_ready.py` is the readiness oracle (`test_accept_ready.py`): screen,
   running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` —
   **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape,
   quit-prompt -> Escape (`m78_mark_clear.py normalize_screen()` does all three).
2. The price/flag/marker chain — silent breakpoints or hw watchpoints + a prediction from live
   memory + a read-back: `m73_price_split.py`, `m74_flag_hw.py`, `m72_gate_watch.py` (the VISIT
   GATE), `m81_flag_writer.py`, `m84e_msg_dispatch.py` (POST/dispatch/handler), `m85_tech_census.py`
   (boundary+helper); the rest self-document (`m75/m76/m84_cancel_sentinel/m84c_item_pump`).
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py` (static), `evidence.py audit [--delete]` /
   `budget`, `scratch/m71/dis.py LO HI` (objdump window).
## THE PICK

**M86: the helper's boundary visit — which leg does eax=0 take, and what gates 0x5a7d00 / 0x5a7f67?** M85 CLOSED (m85cens5 PASS, #90): FUN_00521070 never entered in solo (0x52145e silence BY DESIGN); FUN_005a7970 entered ONCE per boundary, eax=0, return site 0x569948 = inside FUN_0055f650 (54483 B, call sites 0x50dd84 / 0x56cf12), NEITHER tail ran; 0x51f320 round-inc fires once/boundary.
Next: `python3 scratch/m71/dis.py 5a7970 5a7d20` and `5a7f40 5a7f80` (entry + tail branch bytes); identify the function containing 0x50dd84 (index.csv containment — the boundary's real path into the helper); then extend m85_tech_census's gdb template with PRINTF-ONLY bps at the branch decision points and re-run `scripts/m85_tech_census.py --tag m86cens1`. FIRST fresh-load the box (`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch`) — the s135 state swallows turn-end input. PASS iff the taken leg is named by its own branch bytes AND the two tails' gate operands are read back. Residue: chooser case 7 (no direct call 0x496950); cursor print at 0x49771c; bit 5 (0x531782); who clears bit 6; alpha 0x5a6cd0; ds:0x920434 save_later-vs-NETGAME.

## STILL OPEN (in priority order)

1. **M86 (the pick): the helper's boundary visit** — see THE PICK. Residue: chooser case 7 (no direct
   `call` 0x496950); cursor print at **0x49771c**; bit 5 (0x531782); who clears bit 6; alpha 0x5a6cd0;
   **0x4d00 = CLOSED**; ds:0x920434 naming conflict recorded.
2. **M67's plan-descending LIST order has no code behind it**: zero sites read plan byte `+42`; the
   only 52-byte type-address computations (0x40ad92/0x4164dd/0x4188f9/0x418932) hand records to
   string builders.
3. **The `-3 / -6` formula** — stride CONFLICT stands: `0x984d38 + (-v)*48` (0x40adae, 0x4164f5) vs
   `+(-v)*16` (0x418914, 0x41894d).
4. Keep the suite green: `scripts/gate.py` runs every `test_*.py` + `check_classes.py`.

## LIVE FACTS / KIT

- **Box at s137:** `terran.exe` UP, `m54b_clean.SAV` FRESH-LOADED (boundaries live, 2153 r53; the s135
   state swallowed Enter AND measured bar clicks — fresh load is the repair; chooser candidates were
   EMPTY at 2150, re-check at 2153). X focus: `windowfocus 10485761` works WITHOUT a WM;
   `getactivewindow` ALWAYS errors (:99 has no WM) — trust `getwindowfocus getwindowname`; keys land
   (one Escape flips classify base->hud). **The PANE decides where INSERT lands:** pass the index the pane
   shows (read `*(int *)0x6a9480 + 0x3ff3c`), else the queue grows on another base while m57 prints
   "INSERT 1 never landed" (s133). A quit-prompt mid-window swallows every click — run
   `m78_mark_clear.normalize_screen()` (it Escapes a quit-prompt; Return QUITS the game) first. Records are re-inited between rounds — a census is a snapshot. **One box, ONE session:** check `git log -1` and `pgrep -a gdb` before arming (s125/s126
 collision); a veilbrowser Chrome window stacked at 0,0 makes `xwd` OCR the browser
 (`DISPLAY=:99 xdotool windowraise 0x400004`). Gate globals: `0x920434`=0, `0x985b10`=0x08 (human mask = player 3), `0x985b11`=0xff, cur_player `0x985dcc`=3; `*DAT_008f0d60` = the base record (+0x40 storage, +0x4c pending, +0x50..+0x74 queue). Always read `pending` AND the head back after an enqueue.
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py
   --relaunch` -> `accept_ready.py` -> (enqueue) -> **read `pending` AND the head back** -> the run.
   Misread `movie` ~1 in 3: re-run `--relaunch`, never Return on the save browser. `artwork-close`
   is NOT a dialog — click its red CLOSE bar (`smac_play.close_bar`). Kill a stuck `winedbg --auto`
   BY PID when relaunch says `no window after relaunch`.
- gdb: 4 hw watchpoints and 10-12 silent breakpoints work (~35 s per boundary); conditional bps keep
  other records out of the log; PREFER REGISTER-ONLY conditions on hot addresses (a memory-read
  condition there costs seconds per hit — s133). No `si` inside a command list; stdout DRAINED to
  a file (`stdbuf -o0`); a watchpoint reports the pc AFTER the store.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` (double the offset, check disasm) and a POINTER to the base record. Records are BYTES: type record (stride 52, base `0x98ad88`, **8 FACTION BANDS OF 64**, M80): name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0 validator, bit 2 markup-off, bit 8 sweep marker); base record: name `+19`, storage `+0x40`, pending `+0x4c`, queue `+0x50..+0x74`, `+0x98` = storage copy.
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
- **A census interleaved into a gdb log needs O_APPEND on GDB's own fd**; a census snapshots a
  STOPPED engine: order events by VISIT, not by boundary.
- A gdb-log tag alternation must be LONGEST-first (`MARK` swallows `MARKSET`); a bp printf must NOT
  print inferior strings (aborts the batch, DETACHES mid-window); template expressions go in printf
  ARGUMENTS, never the format string; in a two-branch `re` alternation `m.group(1)` is the WHOLE
  match. Never trust one 3 s read of a gdb log for arming.
- **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (m79net1: 128/322/323/194 — FACTION
  BANDS, M80): attribute the sweep by its own predecessor. **The gate visit arrives in the boundary
  AFTER the sweep marks** (m79net2): a poke window needs >= 3 boundaries, 4 overruns the 420 s cap.
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
- Never: commit to main; `pkill -f` / `pgrep|kill` by name; Escape on the title screen; OK on the
  quit prompt; `--mode stop`; `file://` with `--load`; a clear-prefixed command; backticks in a
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