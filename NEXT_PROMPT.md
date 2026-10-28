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
overwrite `SESSION_CURSOR.md` (<= 600 B) with `<ID> | acceptance | merged? | next command` — YOU
write it, nothing else records what was in flight; if the box is mid-run when you are cut off say so
there, and never `rm`/`git checkout --`. Every doc write is an append or a <= 2 KB patch; never
read-then-rewrite a file over 10 KB; keep tool results small.
## THE LEDGER

Merged: **M54A-M82** (#39-#83). **M82 (s125, m82bit7d PASS) — BITS 6/7 OF THE FLAG WORD HAVE NO TESTER:** every `test` of `0x98ad88+tid*52+0x30` uses 0x1/0x4/0x8/0x10, never 0x40/0x80; the only bit-7 instruction is the clearer 0x577ca8. NAMED M82.
**M83+M84+M84b (s128-s130, UNMERGED milestone/m83, m84 PR #84, m84b) — 0x496ad0's -9999 IS THE DIALOG-CANCEL SENTINEL, NOT A PRICE KEY:** Escape arms `[chooser_sub 0x6a9e9c+0xa774] = -1` (only 0x496a43, object in EAX at 0x496a40, or 0x495541 setup); the gate 0x497683/0x49768f then returns 0xffffd8f1 and the caller restores the queue snapshot (0x418623-0x41863f), leaving via 0x4186d2 `jle 0x419967`; only 0x4187be `cmp edi,0x270f` enters 0x418d7d. m84canc2 G1/G2/G3/G8 True, G4-G7 False -> FAIL. NAMED M84/M84b.
**M84e (s133, `m84edisp1/2/3` FAIL, UNMERGED milestone/m84e) — 0x4d00 IS A QUEUE POST, ITS HANDLER
IS 0x52ed7d:** 0x584010 builds a 32-byte record (+0 code WORD, +0x10..+0x1c args 2-5) and posts it
to queue 0x91db70 via 0x52a260 (guard 0x920438 inc/dec); pumps pop it with 0x6361ff and call
0x52bce0 (`mov ebx,[ebp+0x8]` = record, `mov ax,[ebx]` = code, 53 arms) whose ONLY 0x4d00 arm
0x52eb61/6c `je 0x52ed7d` leads; 0x4194a4 (chooser fn 0x417ee0) is the ONLY sender in .text. Handler
record = 0x984d38 + a2*48 + 1872 (a2 = -39-edi, 1872 = 39*48 cancels the sentinel) = 0x984d38 -
tid*48 — a THIRD stride-48 site for the M67 conflict; record+0x14 (0/1/2) selects sub-behaviours
over 1436-byte records at 0x927590/0x927894. RETRACT M70's mechanism: the handler range writes
nothing at +0x3ff5c; 0x4194b3 is in the SENDER and live ran with ebx=0x6a9480 (the static pane)
writing 0x6aa9dc 15->0 — the cursor is PANE-relative, not the fixed 0x6e93dc; the POST leg is
conditional (0x419464/0x419479/0x41948e/0x419492 jump past 0x4194a9). NAMED M84e.
**M84c+M84d (s131/s132, `m84cprobe1`+`m84dky1` FAIL, UNMERGED milestone/m84c PR #86 + milestone/m84d) — THE 0x270f VOCABULARY IS A DEAD END ON BOTH SIDES:** 0x496ad0 (n_callers=1, 0x41860a) returns only -9999 (armed, mode 0), 0 (armed, mode!=0) or +/- the +4 word of the node seeked at `obj+0xa780` (0x6b461c); 0x4187be `cmp edi,0x270f` is the ONLY branch to 0x418d7d and the list's writers never insert 9999 (live keys 0..0x2a,161,192-194). 0x4a99e0 (`cmp [ebp+0x8],0x270f`; else a per-FACTION context switch over stride-0xb4c records at this+0x80, ds:0x888514 = faction index) is vtable slot 100 of the class whose vptr 0x67658c has ZERO live instances — 0 calls in 8 boundaries. NAMED M84c/M84d. **M80 (s122, m80band1) — 8 FACTION BANDS OF 64:** index = `counter<0x40 ? counter : (counter&0x3f)+faction*64`, record 0x98ad88+idx*52; 0x5741f0 clears flag bit 1, 0x5741fe `call 0x572800(faction, idx, 0)`. NAMED M80.
**M73-M75 (#74-76):** price `edi = A x B` at the gate 0x4efa5e, A = 0x4e40a0(owner,1,-1), B = 0x5ac950(head,...); the markup is skipped when `type < 0x40` OR `type[+0x30] & 4` (0x5ac99c); PRODUCTION sets that bit (0x4efe60) and first calls FUN_00572800 (0x4efe7e). NAMED.
**M68 FAILED** (enqueue appends, no key named); **M63** `m63_pop.py`, `0x94de84` queued-count. Branches hold their scripts.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

`python3 scripts/accept_ready.py` is the readiness oracle (`test_accept_ready.py`): screen,
   running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` —
   **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape,
   quit-prompt -> Escape (`m78_mark_clear.py normalize_screen()` does all three).
2. The price/flag/marker chain — silent breakpoints or hw watchpoints + a prediction from live
   memory + a read-back: `m73_price_split.py`, `m74_flag_hw.py`, `m75_sweep_replay.py`,
   `m76_marker_clear.py`, `m72_gate_watch.py` (the VISIT GATE), `m81_flag_writer.py`,
   `m84_cancel_sentinel.py`, `m84c_item_pump.py`, `m84e_msg_dispatch.py` (POST/dispatch/handler).
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py` (static), `evidence.py audit [--delete]` /
   `budget`, `scratch/m71/dis.py LO HI` (objdump window).
## THE PICK

**M84f: make the 0x4d00 POST leg fire, then read the handler.** The instrument is READY and
byte-verified: `python3 scripts/m84e_msg_dispatch.py --tag m84fdisp1 --base-index <what the PANE
shows>` — 7 silent bps 0x4194a9 POST / 0x4194b3 ZERO / 0x4194bd ZEROAFTER / 0x52bd3e if $ax==0x4d00
DISP / 0x52eb6c if $eax==0x4d00 ARM / 0x52ed7d HND / 0x52eda4 IDX; `--tag selftest` proves the shape
discriminates. s133 proved the cursor-zero leg IS live (ebx=0x6a9480, 15 -> 0 read back) and the
POST leg is CONDITIONAL (0x419464/0x419479/0x41948e/0x419492 jump past 0x4194a9), so the missing
input is a chooser selection that COMPLETES: enqueue `--no-ok`, then close the chooser ON A ROW.
PITFALL (s133): INSERT clicks land on whatever base the PANE shows, not the one you name. Sub-leads: the handler's mode 0/1/2 semantics (0x927590/0x927894, 1436-byte records); FUN_00498e20's single caller; the writer of ds:0x888514.

## STILL OPEN (in priority order)

1. **M84f (the pick): complete a chooser selection so the 0x4d00 POST leg fires** — see THE PICK.
   Chooser residue: which widget message reaches handler case 7 (no direct `call` to 0x496950);
   the instrument fix (print the cursor at **0x49771c**, AFTER the seek at 0x497717); bit 5
   (0x531782); who clears bit 6; upkeep/tech 0x52145e/0x5a7d00/0x5a7f67 (ZERO events); alpha 0x5a6cd0.
2. **M67's plan-descending LIST order has no code behind it**: zero sites read plan byte `+42`; the
   only 52-byte type-address computations (0x40ad92/0x4164dd/0x4188f9/0x418932) hand records to
   string builders.
3. **The `-3 / -6` formula** — stride CONFLICT stands: `0x984d38 + (-v)*48` (0x40adae, 0x4164f5) vs
   `+(-v)*16` (0x418914, 0x41894d).
4. Keep the suite green: `scripts/gate.py` runs every `test_*.py` + `check_classes.py`.

## LIVE FACTS / KIT

- **Box at s133 close:** `terran.exe` UP, `m54b_clean.SAV`, round 63, screen hud READY; University
   Base queue depth 14, Korolev 1. **The PANE decides where INSERT lands:** pass the index the pane
   shows (read `*(int *)0x6a9480 + 0x3ff3c`), else the queue grows on another base while m57 prints
   "INSERT 1 never landed" (s133). A quit-prompt mid-window swallows every click — run
   `m78_mark_clear.normalize_screen()` (it Escapes a quit-prompt; Return QUITS the game) first. Records are re-inited between rounds — a census is a snapshot. **One box, ONE session:** check `git log -1` and `pgrep -a gdb` before arming (s125/s126
 collision); a veilbrowser Chrome window stacked at 0,0 makes `xwd` OCR the browser
 (`DISPLAY=:99 xdotool windowraise 0x400004`). Gate globals: `0x920434`=0, `0x985b10`=0x08 (human mask = player 3), `0x985b11`=0xff, cur_player `0x985dcc`=3; `*DAT_008f0d60` = the base record (+0x40 storage, +0x4c pending, +0x50..+0x74 queue). Screen hygiene BEFORE arming: pane -> Escape, dialog -> Return, quit-prompt -> Escape (`m78_mark_clear.py normalize_screen()`); an Escape on the bare map RAISES the quit prompt. Always read `pending` AND the head back after an enqueue.
- **Prices:** head 2 = 9, 192/193 = 18, 194 = 27 (gate charges `edi`, M73; ) free chooser ids 194/2/1/0; enqueue refuses `pending >= 9` (`0x418b05`).
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py
   --relaunch` -> `accept_ready.py` -> enqueue -> **read `pending` AND the head back** -> the run.
   A misread `movie` screen ~1 in 3: re-run `--relaunch`, never Return on the save browser. An
   `artwork-close` screen is NOT a dialog — click its red CLOSE bar (`smac_play.close_bar`). Kill a
   stuck `winedbg --auto` BY PID when relaunch says `no window after relaunch`.
- gdb: 4 hw watchpoints and 10-12 silent breakpoints work (~35 s per boundary); conditional bps keep
  other records out of the log; PREFER REGISTER-ONLY conditions on hot addresses (a memory-read
  condition there costs seconds per hit — s133). No `si` inside a command list; stdout DRAINED to
  a file (`stdbuf -o0`); a watchpoint reports the pc AFTER the store.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm — and it is a POINTER to the base record. Records are BYTES: a type record (stride 52, base `0x98ad88`, **8 FACTION BANDS OF 64**, M80) has name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0 validator test, bit 2 markup-off, bit 8 sweep marker); a base record has name `+19`, storage `+0x40`, pending `+0x4c`, queue `+0x50..+0x74`, `+0x98` = a storage copy.
- **Evidence budget: the gate FAILs at 30 MB** — prune with `evidence.py audit --delete` BEFORE adding.

## TRAPS

- **Register semantics live in the encoding, not the name:** `[reg*4+0x98adb8]` means the register
  holds `tid*13` (52/4), `[reg+0x98adb8]` the record BYTE address `tid*52`; a conditional bp testing
  such a register against the bare tid can NEVER fire.
- **Grep objdump case-sensitively** (`DWORD PTR`, not `ptr [`), enumerate BOTH the absolute and the
  POINTER store shapes, and remember a read-modify-write through a COPIED register (`mov ax,[x];
  or al,4; mov [x],ax`, 0x4efe60) evades both — HARDWARE watchpoints on the FIELD answer "who
  writes it" in one run. A watchpoint on the flag LOW WORD never reports a BYTE store to +0x31.
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it.**
  Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit
  prompt — never OK). Run `m70_clear_dialog.py` before blaming the chooser map.
- **A census interleaved into a gdb log needs O_APPEND on GDB's own fd** (or the next printf
  overwrites it), and a census snapshots a STOPPED engine: order events by VISIT, not by boundary.
- A gdb-log tag alternation must be LONGEST-first (`MARK` swallows `MARKSET`); a bp printf must NOT
  print inferior strings ("Cannot access memory" aborts the batch and DETACHES mid-window); a
  script TEMPLATE substitutes expressions as printf ARGUMENTS, never into the format string; in a
  two-branch `re` alternation `m.group(1)` is the WHOLE match. Never trust one 3 s read of a gdb
  log for arming.
- **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (m79net1: 128/322/323/194 — FACTION
  BANDS, M80): attribute the sweep by its own predecessor. **The gate visit arrives in the boundary
  AFTER the sweep marks** (m79net2): a poke window needs >= 3 boundaries, 4 overruns the 420 s cap.
- A clean reload does NOT carry records created live last session (M80's 324/325 vanished on reload,
  reappeared between runs): census the watched slots BEFORE arming.
- base+0xd0 (`credit`) is written ONLY at 0x6310c6/0x631154 (player-record init) — income is never
  recomputed per round; University Base income 0 vs 1-6 elsewhere, so accept_ready's credit>0 cannot
  be restored by turns; use the per-boundary storage poke 200.
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