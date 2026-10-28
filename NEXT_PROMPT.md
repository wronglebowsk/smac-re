# NEXT_PROMPT.md — footing for the next session (session 119 close, 2026-10-28)

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

Merged: **M54A-M77** (#39-#78); M78 lands on this branch.

**M78 (s120, acceptance `m78order3`) — THE 0x100 MARK AND ITS CLEAR ARE IN ONE PRODUCTION VISIT;
THE CENSUS THAT READS 0x105 IS A MID-VISIT SNAPSHOT.** visit 36: PRODFLAG 194 (pre 0x41) ->
L20FLAG edx=1 -> SWEEPCALL ret `0x4efe83` -> MARK 192/193 (`0x5729d5`) -> GATE l20=1 rec=10088 ->
SWEEPIN -> CLEAR 192/193 (`0x4ef398`, pre 0x105/0x145). Cross-visit mark->clear pairs = [] — nothing
re-marks, so M77's "carriers survive a boundary" is a MEASUREMENT ARTIFACT: the driver reads
`/proc/pid/mem` while the engine sits between the two stores. Census replay exact at 4/4 boundaries.
Callers live: SWEEPCALL {0x4efe83 x1, 0x574203 x4 = FUN_00573a90 on indices 324/325/385/387, zero
MARKs}, CLEAR {0x4f062b x2}; `0x4ef5b3`/`0x52145e`/`0x5a7d00`/`0x5a7f67`/MARKSET printed ZERO.
Static: `call 0x572800` at 0x4394be/0x4efe7e/0x5741fe/0x5a7d0e/0x5a7f75; `call 0x4ef380` at
0x4ef5ae/0x4f0626/0x521479/0x5a8568. RETRACTED (M77 open (a)): the re-marking alternative. NAMED
M78, s120. Instrument `scripts/m78_mark_clear.py` (9 gates; census APPENDED into the gdb log).

**M77 (PR #78, `m77gate1`) — WHAT REACHES THE CLEAR PASS, AND ITS GATE:** `0x4f05e2` is entered only
by fall-through `0x4f05e0` from the gate block `0x4f0591-0x4f05de`, which BAILS at `0x4f0599` when
`[ebp-0x20]==0`, admits iff `DAT_00920434 == 0 || !(DAT_00985b10 & (1 << BYTE [base+4]))`
(`0x4ef804-0x4ef815`), sweeps iff the owner bit is clear else iff `DAT_00985abc & 0x100000`, and its
ELSE SETS the marker at `0x4f05bd`. Live 11 gate visits: 10 bail, 1 sweeps (`194*52`), MARKSET 0, and
its eligibility local was last written at `0x4efe6c` (`edx=1` = FIRST production). NAMED M77, s119.

**M76 (PR #77, `m76marker1`) — WHO CLEARS THE 0x100 MARKER:** `0x4ef398 and BYTE
[ebx+0x98adb9],0xfe` is the FIRST statement of FUN_004ef380(owner, tid) (ebx = tid*52) so it lands on
the record PASSED IN; in a designed window the caller is the production inline selector (test
`0x4f060f`, call `0x4f0626`, ret `0x4f062b`) and both selectors admit iff `flags & 0x105 == 0x105`.
NAMED M76, s118.

**M73-M75 (PR #74-#76) — price formula, the `+0x30 & 4` bit, what the sweep marks.** `edi = A x B` at
the gate `0x4efa5e`, `A = 0x4e40a0(owner,1,-1)` (9 = Python `cost_multiplier`), designed head
`B = byte(+0x29) + (C*P+50)/100` with the markup skipped whole when `type < 0x40` OR
`type[+0x30] & 4` (`0x5ac99c`); PRODUCTION sets that bit (`0x4efe60`, designed only) and first
production calls FUN_00572800 at `0x4efe7e`, whose loop marks EVERY valid UNMARKED designed record
(`0x5729d5`, live {192,193}); the `+0x24/25/26` triple + tier tables + category gate are ALPHA-PATH
only (validator `0x5a6cd0`), UNTESTED live. NAMED M73/M74-RESOLVED/M75, s114-s117.
**M68 FAILED** (enqueue appends, no key named); **M63** `m63_pop.py`, `0x94de84` queued-count,
384/386 identity crossing. Branches hold their scripts.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB: verdict, both bases, tagged CONFLICTs, the pick,
   the first commands. BLOCKED means do the FIX it prints before anything else.
   `python3 scripts/accept_ready.py` is the readiness oracle (17 unit cases in
   `test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`,
   `minerals < price`, `credit > 0` — **re-read it immediately before you arm**. Screen fix:
   dialog -> Return, base PANE -> Escape, quit-prompt -> Escape (`m78_mark_clear.py
   normalize_screen()` does all three).
2. The acceptances of the price/flag chain — each is silent breakpoints or hw watchpoints + a
   prediction from live memory + a read-back: `m73_price_split.py` (splits `edi`),
   `m74_flag_hw.py` (4 hw watchpoints on flag WORDS, refuses to drive unless gdb armed them),
   `m75_sweep_replay.py` (`m75sweep1`), `m76_marker_clear.py` (`m76marker1`),
   `m77_gate_trace.py` (`m77gate1`), `m78_mark_clear.py` (`m78order3`: 12 breakpoints over the
   sweep entry `0x572800`, the mark `0x5729d5`, the clear `0x4ef398`/`0x52145e`, the setters
   `0x4f05bd`/`0x5a7d00`/`0x5a7f67`, plus the census APPENDED into the gdb log).
   `m72_gate_watch.py` is the VISIT GATE; `m74_flag_watch.py` FAILED twice; `m71_pop_watch.py`
   reproduces M71 only.
3. The rest is self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`,
   `m57_ui_enqueue.py`, `m69_enqueue_gdb.py`, `m70_cursor_watch.py`, `test_hud_bar.py`,
   `m65_screen.py --samples 8`, `m70_scan_writers.py` / `m70_type_sites.py` (static),
   `evidence.py audit [--delete]` / `budget` (BEFORE adding), `scratch/m71/dis.py LO HI` for an
   objdump window over `scratch/m574/text.txt`.
## STILL OPEN (in priority order)

1. **M79 — NAME `DAT_00920434` and `DAT_00985b10`, and find what turns the `0x4f05bd` MARKSET
else-branch on.** M78 settled the ordering (mark + clear in ONE visit, the census races the pass),
so the ONLY thing keeping the ELSE branch dead is `DAT_00920434 == 0`. Writers: `DAT_00920434` at
`0x50fe70/0x510196/0x515ad8/0x516f30/0x51f267/0x52280c/0x57ed04/0x598db9/0x5a09ad` (reads 0 in a
normal game); `DAT_00985b10` at `0x4df82e/0x4e08ca/0x512bf6 (imm 0x10)/0x525eed/0x57f051/0x57f2da`
(live 0x08 = owner 3, a per-player mask). Both feed the SAME condition in the production gate
(`0x4f05a5`/`0x4f05af`) and in FUN_005a7970 (`0x5a7ce3`/`0x5a7cf0`, `0x5a7f50`/`0x5a7f57`), where
the admitted branch sweeps and the else branch SETS 0x100 at `0x5a7d00`/`0x5a7f67`. Cheap shape:
read the writer windows statically (`scratch/m71/dis.py` ±10 instructions), then one live window
that pokes `DAT_00920434 = 1` before a production visit and reads whether MARKSET fires and what the
census does to bit 8. Other threads: what the indices >= 256 (322-325, 385/387) ARE and what
FUN_00573a90's sweep does for them; when the upkeep (FUN_00521070) / tech (FUN_005a7970) passes run
at all; the alpha validator+tier path; the s115 `0x41 -> 0x05` writer.
2. **Who calls the `0x4194b3` handler / what widget message `0x4d00` is** (zeroes the cursor
   after a queue mutation; sender `0x584010`, `0x4eb6b0` runs after it; did NOT fire at a
   completion or round boundary).
3. **M67's plan-descending LIST order has no code behind it**: zero sites read plan byte `+42`;
   the only 52-byte type-address computations (`0x40ad92/0x4164dd/0x4188f9/0x418932`) hand
   records to string builders.
4. **The `-3 / -6` formula** — stride CONFLICT stands: `0x984d38 + (-v)*48` (`0x40adae`,
   `0x4164f5`) vs `+(-v)*16` (`0x418914`, `0x41894d`).
5. Open from 104/105: the `income 1` accrual case (every M64 PASS window had `gap_delta = 0`):
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`. Keep the suite green: `scripts/gate.py` runs every `test_*.py` + `check_classes.py`.

## LIVE FACTS / KIT

- **Box at session-120 close:** `terran.exe` UP (the binary is `terran.exe` — pgrep -x terrans.exe
finds nothing), round ~54 after m78order3, University Base idx 0; 192=0x005 193=0x045 194=0x045, no
record carries 0x100. Gate globals `DAT_00920434=0`, `DAT_00985b10=0x08` (owner 3),
`DAT_00985abc` bit20 set; `*DAT_008f0d60` = the base record the production visit is in (+4 owner,
+0x40 storage, +0x50 queue head). Screen hygiene BEFORE arming: pane -> Escape, dialog -> Return,
**quit-prompt -> Escape** (Return/OK quits the game) — `scripts/m78_mark_clear.py
normalize_screen()` does all three; a quit prompt left up swallows every enqueue click (m78order2
failed three times on exactly that) and an Escape on the bare map is what RAISES it.
Fresh `m54b_clean.SAV` loads 192/193/194 at `0x01/0x41/0x41` (193/194 carry bit 6, NOT bit 2 —
s116's "0x41 = bit 2 set" was wrong: bit 2 = 0x4, 0x41 has it CLEAR). Korolev Center does not
exist here. Always read `pending` back after an enqueue before arming.
- **Prices (`price_of`, multiplier 9):** head 2 = 9, 192/193 = 18, 194 = 27 — the gate charges `edi`
  (M73); never assert arrival from `price_of`. Free chooser ids 194/2/1/0; 195 -> -3, 196+ recordless;
  enqueue refuses `pending >= 9` (`0x418b05`).
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py
   --relaunch` -> `accept_ready.py` -> enqueue (`m57_ui_enqueue.py --base-index 0 --cell-item 194
   --inserts 1`) -> **read `pending` back** -> the acceptance run. The load stalls at a misread
   `movie` screen ~1 in 3: re-run `--relaunch`, never Return on the save browser. An `artwork-close`
   screen is NOT a dialog — click its red CLOSE bar (`smac_play.close_bar`;
   `scratch/m76_close_artwork.py` does it).
- gdb: 4 hardware watchpoints and 10-12 clean silent breakpoints work (~35 s per boundary under
  them); conditional breakpoints keep the other bases/records out of the log. No `si` inside a
  breakpoint command list; stdout DRAINED to a file (`stdbuf -o0`); a printf newline in a
  generated gdb script is ONE backslash + `n`; a watchpoint reports the pc AFTER the store (map
  it back, 16-byte window).
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm —
  and it is a POINTER to the base record. Records are BYTES: a type record (stride 52, base
  `0x98ad88`) has name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0
  is the validator's first test); a base record has name `+19`, storage `+0x40`, pending
  `+0x4c`, queue `+0x50..+0x74`, `+0x98` = a copy of storage written by the pay epilogues.
- **Evidence budget: the gate FAILs at 30 MB** — prune with `evidence.py audit --delete` BEFORE adding.

## TRAPS

- **Register semantics live in the encoding, not the name.** `[reg*4+0x98adb8]` means the register
  holds `tid*13` (52/4); `[reg+0x98adb8]` means it holds the record BYTE address `tid*52`. A
  conditional breakpoint testing such a register against the bare tid can NEVER fire (M74 run 1
  printed "no writer fired" for exactly that reason; the flag WORD is at `tid*52 + 0x98adb8`).
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
- **A census interleaved into a gdb log needs O_APPEND on GDB's own fd** (`open(lpath, "a")`;
"aw" is not a Python mode): with "w" the driver writes past gdb's lagging offset and the next gdb
printf OVERWRITES the census lines (m78order1 lost all four). And a census is a snapshot of a
**stopped** engine: order events by VISIT (function entry), not by boundary, before saying a mark
"survived a turn" — M78 showed the survivor was a mid-visit read.
- The base array compacts mid-run: locate bases BY NAME, pair windows by name AND owner byte,
  pair units by `(x,y,type,owner)`. M71's gate 8 guards against watching another base's queue.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by
  "first empty slot", never treat slot 10 (`+0x78`) as an entry, never plan a duplicate (the engine
  refuses an id already queued), and never read a stale tail as proof an id IS queued
  (`m66_insert_slot` FAILs when the item already appears there). Id 0 is both Colony Pod and the
  empty marker; the sentinel is -39 (`0xffffffd9`), not -38. A negative value belongs to the TYPE
  (196 -> -6, 195 -> -3) — never put 195/196+ in a shape.
- **A PASS on a shape that cannot discriminate is not a PASS.** Compute candidate predictions
  from the baseline first; refuse the shape if they all agree. An APPEND engine is consistent
  with ~55 rules — a FAIL there means "no key claim", not "the key is wrong".
- The harness race is real (`player walk came home to us after the flip` = the window spans two
  rounds): RE-RUN, never edit the floor. Reload rather than poke into a UI-queued accrual; poke
  minerals and read back BEFORE attaching for a completion acceptance.
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

One screen: what changed, the acceptance numbers WITH the command, what is open, the next pick.