# NEXT_PROMPT.md — footing for the next session (session 129, 2026-10-28)

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

Merged: **M54A-M82** (#39-#83). **M82 (s125) — BITS 6/7 OF THE FLAG WORD HAVE NO TESTER.** All 168 accesses to `0x98ad88+tid*52+0x30` enumerated: every `test` uses 0x1/0x4/0x8/0x10, NEVER 0x40/0x80 (both store shapes); markup test is bit 2 only (0x5ac99c), B only from 0x5ac950; the only bit-7 instruction is the CLEARER `and BYTE [...0x98adb8],0x7f` at **0x577ca8**. Census 0..511: bit6 [193,194,324,325,386,449] bit7 [324,325,386,449]; 19 min later 385=0x81, 386=0x1, new 387=0xc1 — a carrier list is a SNAPSHOT. M74's `f30=0x41 edi=45` proves bit 6 is not markup-off. Live bit-7 poke RAN at s127: `m82bit7d` PASS (G1-G7): 194 head storage 20, W1 0x41 edi=45; ONE poke
changed ONLY bit 7 (0x41->0xc1 read back) -> W2 **edi=45 unchanged**; control bit2 on -> edi=27.
VERDICT: bit 7 does NOT gate the price; fresh bit7 census [386,449] = sweep-inited only. NAMED M82.
**M83 (s128, `m83cw2`, UNMERGED branch milestone/m83) — FUN_00577280's ONLY call is 0x418d8a inside FUN_00417ee0, reached only when 0x496ad0 returns 9999 (live edi 2). **M84 (s129, `m84canc1`, UNMERGED branch milestone/m84) — THE +9999 RETURN OF 0x496ad0 IS ITS DIALOG-CANCEL SENTINEL (static, bytes):** gate 0x497683 `cmp [buf+0xa774],-1` + 0x49768f `[buf+0xa778]==0` -> 0x4976ce `0xffffd8f1`; -1 with result != 0 -> 0; else the pump return (call 0x401940, negated iff 0x495480 bit 0x20 clear). -1 is written ONLY at **0x496a43** (FUN_00496950 handler case 7 = CANCEL: result 0 at 0x496a27 + arm at 0x496a43; cases 0/2/5 bail if already -1) and 0x495541 (FUN_004954e0 setup). +0xa774 is also the chooser guard (`0x6A9E9C`): ARM printed buf=0 (ecx is not the buffer there); GATE buf=0x6a9e9c cancel=3 result=5; SENT edi=2; BRANCH/ENTRY 0 (G1 True, G2-G7 False). NAMED M84.
**M79 (s121, m79net5) — THE MARKER GATE IS A NETGAME + HUMAN-PLAYER TEST:** 0x4f0591-0x4f0637 admits the 0x100-clear pass iff `0x920434 == 0 || !(0x985b10 & (1<<owner))`, ELSE 0x4f05bd marks `[tid*52+0x98adb9] |= 1`. `0x920434` netgame, `0x985b10` HUMAN mask keyed 1<<faction (live 0x08), NOT 1<<cur_player. Poke 0x4f05a5: MARKSET 194, replay 3/3. NAMED M79.
**M80 (s122, `m80band1`) — 8 FACTION BANDS OF 64; FUN_00573a90 ARG 1 IS A FACTION:** index = `counter<0x40 ? counter : (counter&0x3f)+faction*64`, record 0x98ad88+idx*52 (0x57417e), 0x5741f0 `and [rec+0x30],0xfd`, 0x5741fe `call 0x572800(faction, idx, 0)`, band base `param_1*0xd00`; 324/325 EMPTY at window start -> 0xc1. NAMED M80.
**M73-M75 (#74-76):** price `edi = A x B` at the gate `0x4efa5e`, `A = 0x4e40a0(owner,1,-1)`, `B = 0x5ac950(head,...)`; markup skipped when `type < 0x40` OR `type[+0x30] & 4` (0x5ac99c); PRODUCTION sets that bit (0x4efe60); first production calls FUN_00572800 (0x4efe7e). NAMED.
**M68 FAILED** (enqueue appends, no key named); **M63** `m63_pop.py`, `0x94de84` queued-count. Branches hold their scripts.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

`python3 scripts/accept_ready.py` is the readiness oracle (`test_accept_ready.py`): screen,
   running gdb, evidence headroom, then per base `pending > 0`, `minerals < price`, `credit > 0` —
   **re-read it immediately before you arm**. Screen fix: dialog -> Return, base PANE -> Escape,
   quit-prompt -> Escape (`m78_mark_clear.py normalize_screen()` does all three).
2. The price/flag/marker chain — each is silent breakpoints or hw watchpoints + a prediction from
   live memory + a read-back: `m73_price_split.py`, `m74_flag_hw.py` (4 hw watchpoints on flag WORDS,
   refuses to drive unless gdb armed them), `m75_sweep_replay.py`, `m76_marker_clear.py`,
   `m77_gate_trace.py`, `m78_mark_clear.py` (census APPENDED into the gdb log), `m79_netgame_poke.py`
  . `m72_gate_watch.py` is the
   VISIT GATE; `m81_flag_writer.py` (`m81write4`: 4 hw watchpoints on the flag WORDS of the next free band-5 slots, fresh reload first so they are EMPTY);
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m69_enqueue_gdb.py`, `m70_cursor_watch.py`, `m65_screen.py --samples 8`, `m70_scan_writers.py`
   (static), `evidence.py audit [--delete]` / `budget`, `scratch/m71/dis.py LO HI` (objdump window).
## STILL OPEN (in priority order)

1. **M83 — NAME FUN_00577280** (shard_014.c:19576, holds the sole bit-7 clearer 0x577ca8; tests bit 0/`&4`/a value > 0x3f, sets 0x200 iff bit 3, clears 3+7) + callers; what bit 5 (`or 0x20` 0x531782) means; who clears bit 6. `m82_bit7_poke.py` (m82bit7d PASS) is the proven price-gate instrument. **Arm only on a quiet box:** no second session on this repo (`git log -1`, `pgrep -a gdb`); if relaunch prints `no window after relaunch`, kill the stuck `winedbg --auto` BY PID first (s127). Still open: why `[ebp-0xc]` != 0 for 324/325 and == 0 for 385; who calls FUN_00573a90 (ret 0x5749a7 x6 / 0x574da9 / 0x575424); `0x985aec` reads as the ERA global (NAMED `0x68cbb8` row, live 2) — its `> 1` test ORs markup-off **M84b (the pick): re-run `scripts/m84_cancel_sentinel.py --escape --no-ok` taking the buffer from the caller (bp 0x41860a reads `[esp+0xc]`) not ecx at 0x496a43, events ORDERED by time; which widget message reaches case 7 (no direct call to 0x496950 in .text); what 0x495541 arms; who owns 0x6a9e9c. onto every record the sweep touches; upkeep/tech 0x52145e/0x5a7d00/0x5a7f67 (ZERO events ever); alpha 0x5a6cd0.
2. **Who calls the `0x4194b3` handler / what widget message `0x4d00` is** (zeroes the cursor
   after a queue mutation; sender `0x584010`, `0x4eb6b0` runs after it; did NOT fire at a
   completion or round boundary).
3. **M67's plan-descending LIST order has no code behind it**: zero sites read plan byte `+42`;
   the only 52-byte type-address computations (`0x40ad92/0x4164dd/0x4188f9/0x418932`) hand
   records to string builders.
4. **The `-3 / -6` formula** — stride CONFLICT stands: `0x984d38 + (-v)*48` (`0x40adae`,
   `0x4164f5`) vs `+(-v)*16` (`0x418914`, `0x41894d`).
5. Keep the suite green: `scripts/gate.py` runs every `test_*.py` + `check_classes.py`.

## LIVE FACTS / KIT

- **Box at session-125 close:** `terran.exe` pid 4141935 UP (the binary is `terran.exe` — `pgrep -x terrans.exe` finds nothing), `m54b_clean.SAV`, round ~53, University Base idx 0 head 194 pending 1 (queued by a direct poke, not the chooser), storage poked 20; 194 = 0x45, 193 = 0x41, 324/325/387 = 0xc1 (faction records are re-inited between rounds — a census is a snapshot). **TWO THINGS ATE SESSION 125:** (a) a concurrent Hermes session (s126) ran the SAME prompt in the SAME worktree — the box is ONE process, check `git log -1` and `pgrep -a gdb` before arming; (b) a veilbrowser Chrome window stacked OVER the Wine window at 0,0, so `xwd -root` cropped 800x600:0:0 OCR'd the BROWSER and every screen read hung — `DISPLAY=:99 xdotool windowraise 0x400004` (the browser job drives CDP, so raising is safe). Gate globals: `0x920434`=0, `0x985b10`=0x08 (human mask = player 3), `0x985b11`=0xff, cur_player `0x985dcc`=3; `*DAT_008f0d60` = the base record (+0x40 storage, +0x4c pending, +0x50..+0x74 queue). **s129 close:** Korolev idx 18 pending 0; `m57_ui_enqueue.py` gained `--no-ok`; a NETFLASH dialog blocked accept_ready -> `m70_clear_dialog.py`.
Screen hygiene BEFORE arming: pane -> Escape, dialog -> Return,
quit-prompt -> Escape (`m78_mark_clear.py normalize_screen()`); an Escape on the bare map RAISES
the quit prompt. Always read `pending` AND the head back after an enqueue.
- **Prices:** head 2 = 9, 192/193 = 18, 194 = 27 (gate charges `edi`, M73; ) free chooser ids 194/2/1/0; enqueue refuses `pending >= 9` (`0x418b05`).
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> enqueue -> **read `pending` AND the head back** -> the run. A misread `movie` screen ~1 in 3: re-run `--relaunch`, never Return on the save browser. An `artwork-close` screen is NOT a dialog — click its red CLOSE bar (`smac_play.close_bar`).
- gdb: 4 hw watchpoints and 10-12 silent breakpoints work (~35 s per boundary); conditional breakpoints keep other records out of the log. No `si` inside a command list; stdout DRAINED to a file (`stdbuf -o0`); a printf newline is ONE backslash + `n`; a watchpoint reports the pc AFTER the store.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm — and it is a POINTER to the base record. Records are BYTES: a type record (stride 52, base `0x98ad88`, **8 FACTION BANDS OF 64**, M80) has name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0 validator test, bit 2 markup-off, bit 8 sweep marker); a base record has name `+19`, storage `+0x40`, pending `+0x4c`, queue `+0x50..+0x74`, `+0x98` = a storage copy.
- **Evidence budget: the gate FAILs at 30 MB** — prune with `evidence.py audit --delete` BEFORE adding.

## TRAPS

- **Register semantics live in the encoding, not the name.** `[reg*4+0x98adb8]` means the register
  holds `tid*13` (52/4); `[reg+0x98adb8]` means it holds the record BYTE address `tid*52`. A
  conditional breakpoint testing such a register against the bare tid can NEVER fire.
- **Grep objdump case-sensitively** (`DWORD PTR`, not `ptr [`), enumerate BOTH the absolute
  (`[reg*4+0x98adb8]`) and POINTER (`[eax+0x30]`) store shapes, and note a read-modify-write through a
  COPIED register (`mov ax,[x]; or al,4; mov [x],ax`, M74's `0x4efe60`) evades both — when the writer
  set is in doubt, HARDWARE watchpoints on the FIELD (`m74_flag_hw.py`) answer "who writes it" in one
  run. A watchpoint on the flag LOW WORD (+0x30..0x31) never reports a BYTE store to +0x31
  (`0x4ef398`) — watch the high byte or census the bit. Check a breakpoint's tid expression against
  the instruction bytes before it goes inside a gate (`0x595f82/91/9c` printed tid 324/325: esi is
  not a record pointer there).
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it.**
  Return clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit
  prompt — never OK). Run `m70_clear_dialog.py` before blaming the chooser map.
- **A census interleaved into a gdb log needs O_APPEND on GDB's own fd** (`open(lpath, "a")`; "aw" is not a Python mode) or the next printf overwrites it (m78order1 lost all four); a census snapshots a **stopped** engine, so order events by VISIT, not by boundary.
- **A gdb-log tag alternation must be LONGEST-first** (`MARK` swallows `MARKSET`; m79net4 KeyError); a census parser must re-read its own match object (m79net2 `int('BOUNDARY')`).
- **PRODFLAG (0x4efe60) fires for EVERY record the pass walks** (m79net1: 128/322/323/194 — those are FACTION BANDS, M80), so attribute the sweep by its own predecessor.
- **The gate visit for a record arrives in the boundary AFTER the sweep marks it**: m79net2 (2 boundaries) saw the 0x104 marks but never reached 0x4f0591, so a poke window needs >= 3 boundaries; 4 boundaries overruns the 420 s foreground cap (m79net1 was cut mid-window).
- A bp-command printf must NOT print inferior strings (`%.20s` on `*(char *)(rec+0)` -> gdb "Cannot access memory", aborts the batch script, DETACHES mid-window; boundaries then run uninstrumented while smac_play exits 0 — the log looks empty). A gdb-script TEMPLATE substitutes expressions as printf ARGUMENTS, never into the format string (`idx=@@I@@` printed the literal `($ebx/52)` and the log parsed as ZERO events). In a two-branch `re` alternation `m.group(1)` is the WHOLE match — branch on a group from inside the taken branch. Never trust one 3 s read of a gdb log for arming: poll.
- A clean reload does NOT carry records created live last session (M80's 324/325 vanished on reload, reappeared between runs): census the watched slots BEFORE arming.
- base+0xd0 (`credit`) is written ONLY at 0x6310c6/0x631154 (player-record init, `call [obj+0x90]`) — income is never recomputed per round; University Base income 0 rate 0 vs 1-6 on the other 17 bases, so accept_ready's credit>0 cannot be restored by turns; use the per-boundary storage poke 200.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by
  "first empty slot", never treat slot 10 (`+0x78`) as an entry, never plan a duplicate, and never
  read a stale tail as proof an id IS queued. Id 0 is both Colony Pod and the empty marker; the
  sentinel is -39 (`0xffffffd9`). A negative value belongs to the TYPE (196 -> -6, 195 -> -3).
- **A PASS on a shape that cannot discriminate is not a PASS.** Compute candidate predictions from
  the baseline first; refuse the shape if they all agree.
- The harness race is real (`player walk came home to us after the flip` = the window spans two
  rounds): RE-RUN, never edit the floor. Poke minerals and read back BEFORE attaching.
- One variable at a time; if two things moved together write "confounded", not "because".
  Documents lose to instruction bytes only after a poke — until then REPORT the conflict.
- Never: commit to main; `pkill -f` / `pgrep|kill` by name; Escape on the title screen; OK on
  the quit prompt; `--mode stop`; `file://` with `--load`; a clear-prefixed command; backticks
  in a commit message; `skill_manage delete`.

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