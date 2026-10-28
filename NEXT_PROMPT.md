# NEXT_PROMPT.md — footing for the next session (session 119 close, 2026-10-28)

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor (`auxiliary.compression: auto` -> the same 262k model);
its summaries die on the output cap (4x `finish_reason=length`, 2026-10-27; sessions 113/114 hit
259,232/262,144 and were cut mid-sentence). **Whatever is not finished by ~150k tokens is not
finished at all.**

Counted in TOOL CALLS (the clock you can see):
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background".
- **6-30** the milestone, one variable at a time. **At call 25: `git add -A && git commit -m
  "<ID>: checkpoint"`** — the next turn may be the truncated one, so every step after it must leave a
  committed file.
- **30-40** STOP MEASURING. Acceptance not green = that IS the finding: write the blocker and the
  failing number, merge nothing, close.
- **40-50** the closing order, TERSE: notes <= 2 KB, NAMED block <= 1 KB, this file patched BY
  SECTION (budget FAILs at 16,000 chars — stay <= 15,500), never rewritten.

Survivability rules:
- Before any step that can exceed 2 minutes (gdb run, relaunch, evidence audit), overwrite
  `SESSION_CURSOR.md` (<= 600 B) with `<ID> | done | in flight | next command` — YOU write it,
  nothing else records what was in flight. If the box is mid-run when you are cut off, say so there;
  never `rm`/`git checkout --`.
- Every doc write is an append or a <= 2 KB patch; never read-then-rewrite a file over 10 KB.
  Keep tool results small — a multi-KB result is context that cannot be compressed back.
## THE LEDGER

Merged: **M54A-M77** (#39-#78)

**M77 (PR #78, merged) — WHAT REACHES THE MARKER-CLEAR PASS, AND ITS GATE (tag `m77gate1`):**
`0x4f05e2` is entered ONLY by fall-through `0x4f05e0 xor esi,esi`, whose two in-edges come from the
gate block `0x4f0591-0x4f05de`: that block BAILS at `0x4f0599 je 0x4f0637` when `[ebp-0x20] == 0`,
admits iff `DAT_00920434 == 0 || !(DAT_00985b10 & (1 << BYTE [base+4]))` (`0x4ef804-0x4ef815` builds
that bit), and inside it sweeps iff the owner bit is clear else iff `DAT_00985abc & 0x100000`; the
ELSE SETS the marker `0x4f05bd` and skips the sweep. Live `0x920434=0` / `0x985b10=0x08` (owner 3) /
bit20=1: 11 gate visits, 10 bail on `[ebp-0x20]==0`, the one with `1` swept (owner 3, record
`194*52`) and cleared 192/193, MARKSET 0 (ELSE dead while `0x920434==0`), and its eligibility local
was last written at `0x4efe6c` (`edx=1` = flag bit 2 clear before the `or al,4` store = FIRST
production of 194). NAMED M77, s119. Instrument `scripts/m77_gate_trace.py` (8 gates).

**M76 (PR #77, merged) — WHO CLEARS THE 0x100 SWEEP MARKER:** the clear `0x4ef398 and BYTE
[ebx+0x98adb9],0xfe` is the FIRST statement of FUN_004ef380(owner, tid) (ebx = tid*52) — it lands on
the record PASSED IN; in a designed window the caller is the production function's inline selector
(test `0x4f060f`, call `0x4f0626`, ret `0x4f062b`); both selectors walk `{0..63} U {owner*64..+63}`,
call iff `flags & 0x105 == 0x105`. The upkeep inline clear and the tech setters printed ZERO events.
RETRACTED by M77: "the clear pass fired on a visit that printed NO production setter" — that
instrument's PRODSET cond is `*(int *)0x8f0d60 == $b`. NAMED M76, s118.

**M73-M75 (PR #74-#76, merged) — price formula, the `+0x30 & 4` bit, what the sweep marks.**
`edi = A x B` at the gate `0x4efa5e`: `A = 0x4e40a0(owner,1,-1)` (9 = Python `cost_multiplier`);
designed head `B = 0x5ac950(head,[0x68cbb0],0) = byte(+0x29) + (C*P+50)/100`, markup skipped whole
when `type < 0x40` OR `type[+0x30] & 4` (`0x5ac99c`). PRODUCTION sets that bit (`0x4efe60`, designed
only, between gate and pay `0x4efed8`) and first production calls FUN_00572800 at `0x4efe7e`, whose
loop stores `or [rec+0x30],0x104` (`0x5729d5`) on EVERY valid UNMARKED designed record — live
{192,193}, nothing else; the `+0x24/25/26` triple + tier tables + category gate are ALPHA-PATH only
(validator `0x5a6cd0`) and UNTESTED live (NAMED M75). RETRACTED: `0x597487` is a save/load codec
(`0x93327a` table). NAMED M73/M74-RESOLVED/M75, s114-s117. Instruments `m73_price_split.py`,
`m74_flag_hw.py`, `m75_sweep_replay.py`.
**M68 FAILED** (enqueue appends, no key named); **M63** `m63_pop.py`, `0x94de84` queued-count,
384/386 identity crossing. Branches hold their scripts.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB: verdict, both bases, tagged CONFLICTs, the pick,
   the first commands. BLOCKED means do the FIX it prints before anything else.
2. `python3 scripts/accept_ready.py` — the readiness oracle (17 unit cases:
   `scripts/test_accept_ready.py`): screen, running gdb, evidence headroom, then per base
   `pending > 0`, `minerals < price`, `credit > 0`. **Re-read it immediately before you arm.**
   `--no-screen` skips the OCR. Screen `dialog` -> `scripts/m70_clear_dialog.py` (presses Return
   until it clears); a BUILD/base PANE needs Escape, not Return.
3. `m74_flag_hw.py` — 4 hw watchpoints on flag WORDS, prints pc+val per store, refuses to drive
   unless gdb armed them (M74 tag `m74flag3`); `m72_gate_watch.py` — the VISIT GATE (12
   conditional breakpoints, storage poked+read back); `m73_price_split.py` splits `edi`;
   `m74_flag_watch.py` (FAILED twice); `m71_pop_watch.py` (reproduce M71 only).
4. `m75_sweep_replay.py --tag m75sweep1` — M75's acceptance (predicts FUN_00572800(194,0)'s marked
set from live memory, 4 hw watchpoints, early-stop, 5 gates). `m76_marker_clear.py --tag
m76marker1` — M76's: 12 silent breakpoints over the clear `0x4ef398` (prints tid/owner/flags/return
addr), both selectors, the upkeep inline clear, the marker setters, then replays the observed
stores onto the before-census and reads the 0x100 bit back.
5-9. The rest of the kit is self-documenting (`--help` before inventing a flag):
   `m66_insert_slot.py`, `m57_ui_enqueue.py`, `m69_enqueue_gdb.py`, `m70_cursor_watch.py`
   (cursor instrument), `test_hud_bar.py`, `m65_screen.py --samples 8` (READ-ONLY meter),
   `m70_scan_writers.py` / `m70_type_sites.py` (static), `evidence.py audit [--delete]` /
   `budget` (BEFORE adding), `scratch/m71/dis.py LO HI` for an objdump window over
   `scratch/m574/text.txt`.
## STILL OPEN (in priority order)

1. **M78 — same-visit marks vs clears, and who else calls FUN_00572800.** The sweep ran ONCE in 4
boundaries and its visit's eligibility local came from the FIRST-production route (`0x4efe6c`,
`edx=1 tid=194`), yet the census still read 192=0x105 / 193=0x145 after that boundary and clean two
later — either another FUN_00572800 caller re-marks later in the same turn (M76: FUN_004ef540 is
called only at `0x5a7d14`/`0x5a7f7b`, right after a sweep call) or the census races the pass. Cheap:
add the mark store `0x5729d5` and the clear `0x4ef398` to `scripts/m77_gate_trace.py` (both print
tid/flags); the driver prints one line per boundary, so no timestamps are needed. Also NAME
`DAT_00920434` (writers `0x50fe70/0x510196/0x515ad8/0x516f30/0x51f267/0x52280c/0x57ed04/0x598db9/
0x5a09ad`; reads 0 in a normal game) and `DAT_00985b10` (writers `0x4df82e/0x4e08ca/0x512bf6`
(imm 0x10)`/0x525eed/0x57f051/0x57f2da`; live 0x08 = owner 3). Other threads: alpha validator+tier
path, s115 `0x41 -> 0x05` writer, when the upkeep (FUN_00521070) / tech (FUN_005a7970) passes run.
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

- **Box at session-119 close:** `terran.exe` UP (the binary is `terran.exe` — pgrep -x terrans.exe
finds nothing), round ~50 after m77gate1, University Base idx 0; flags 192=0x005, 193=0x045,
194=0x045 — NO record carries 0x100. Gate globals: `DAT_00920434=0`, `DAT_00985b10=0x08` (per-player
mask, owner 3), `DAT_00985abc=0x003a7168` (bit20 set); `*DAT_008f0d60` = the base record the
production function is visiting (+4 owner, +0x40 storage, +0x50 queue head). A base PANE needs
Escape (`scratch/m77_close_pane.py`): `m70_clear_dialog.py` prints "READS hud" on a base pane
because its stop test accepts `bar && look>0` — re-read `accept_ready.py` before arming.
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