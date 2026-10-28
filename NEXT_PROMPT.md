# NEXT_PROMPT.md — footing for the next session (session 114 close, 2026-10-27)

## BUDGET — read before anything else (compression CANNOT be relied on)

The main model is also Hermes' compressor (`auxiliary.compression: provider: auto` -> the same
262k model). Its summaries hit the output cap: `finish_reason=length`,
`failure_class=summary_truncated_failure`, 132 s, `commit_status=aborted`, 4x on 2026-10-27, and
the gateway drops hygiene compression after a 10 s turn-hold. Measured cost of ignoring this:
session 113/114 reached 259,232 / 262,144 tokens and the closing turn was cut mid-sentence, twice.
**So: whatever is not finished by ~150k tokens is not finished at all.**

Counted in TOOL CALLS (the clock you can see):
- **0-6** brief, this file, notes tail, `accept_ready.py`. No shard reading "for background" —
  the atlas/NAMED blocks are the summary and they are far smaller than the code.
- **6-30** the milestone, one variable at a time (a gdb run ~2 calls, relaunch ~1, enqueue ~1).
  **At call 25: `git add -A && git commit -m "<ID>: checkpoint"`** — after that every step leaves
  a committed file, because the next turn may be the truncated one.
- **30-40** STOP MEASURING. Acceptance not green = that is the finding: write the blocker and the
  failing number, merge nothing, close.
- **40-50** the closing order, and it may be TERSE: notes entry <= 2 KB, NAMED block <= 1 KB,
  this file patched BY SECTION, never rewritten.

Survivability rules:
- Before any step that can exceed 2 minutes (gdb run, relaunch, evidence audit), overwrite
  `SESSION_CURSOR.md` (<= 600 B) with `<ID> | done | in flight | next command` — YOU write it,
  nothing else records what was in flight. If the box is mid-run when you are cut off, say so there;
  never `rm`/`git checkout --`.
- Every doc write is an append or a <= 2 KB patch. Never read-then-rewrite a file over 10 KB.
- Keep tool results small: `grep`/`sed -n` windows, `tail`, `scripts/evidence.py show`. A
  multi-KB result is context that cannot be compressed back.
## THE LEDGER

Merged: **M54A-M73** (#39-#74)
`0x5ac950`), the queue mechanics (enqueue at the cursor, pop pops ONE item, shift
`0..pending-1`), and the gate `cmp [base+0x40], edi` at `0x4efa5e` (M72: `edi` is not `price_of`).

**M73 (PR #74, merged) — WHAT THE GATE'S `edi` IS MADE OF. ACCEPTANCE PASS, 10/10 gates, tag
`m73split4`: `edi = A x B`; `A = 0x4e40a0(owner,1,-1)` (9 = Python `cost_multiplier`); for a
DESIGNED head `B = 0x5ac950(head,[0x68cbb0],0) = byte(+0x29) + (C*P+50)/100` (measured `C 3`,
`P 50` -> `edi 45` for 194 where `price_of` says 27), and the markup is skipped whole when
`type < 0x40` OR `type[+0x30] & 4` (`0x5ac99c`). Full numbers: NAMED M73 block, notes s114.

**M74 (branch `milestone/m74`, NO PR — acceptance FAILED twice, tags `m74flag` / `m74flag2`):**
the bit-2 setter is NOT one of the eleven absolute-address writers — 0 of 11 conditional
breakpoints fired while 193 and 194 gained the bit. The run DID re-measure M73's switch live: at
`0x4efa5e` head 194 read `f30=0x41 edi=45`, then in the same window `f30=0x45 edi=27`. New
candidate: the sweep store `0x597487 mov WORD PTR [eax+0x30],dx` in FUN_00596850 (a stride-52 copy
of a source table into `+0x23..+0x30`). `m74_flag_watch.py` + `test_m74_flag.py` (37/37) sit on
the branch; details in the NAMED M74 block and notes s115.

**M68 (no PR, acceptance FAILED):** 212 candidate sort rules, 55 predict an append, the live
enqueue DID append at round 51 — no key named (M70's cursor mechanics explain the appends).
**M63 (no PR):** `m63_pop.py`, the `0x94de84` queued-count correction, 384/386 identity crossing.
Both branches hold their scripts.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB: verdict, both bases, tagged CONFLICTs, the pick,
   the first commands. BLOCKED means do the FIX it prints before anything else.
2. `python3 scripts/accept_ready.py` — the readiness oracle (17 unit cases:
   `scripts/test_accept_ready.py`): screen, running gdb, evidence headroom, then per base
   `pending > 0`, `minerals < price`, `credit > 0`. **Re-read it immediately before you arm.**
   `--no-screen` skips the OCR. Screen `dialog` -> `scripts/m70_clear_dialog.py` (presses Return
   until it clears, printing each look); a BUILD/base PANE needs Escape, not Return.3. `m71_pop_watch.py` (reproduce M71 only) and **`m72_gate_watch.py`** — the VISIT GATE: 12
   conditional breakpoints from `0x4ef6d0` to `0x4f5a93` (the list lives in the script), storage
   poked and READ BACK before attaching, drives boundaries, 8 gates, one-line PASS/FAIL. Its `edi`
   is the visit's requirement, not `price_of` (M72). `m73_price_split.py` splits `edi` (M73's
   acceptance, 10 gates, 28 unit cases); `m74_flag_watch.py` watches the eleven `+0x30` writers
   plus `0x4efa5e` and censuses all 256 records' `+0x30` (M74: acceptance FAILED twice).
4. `m70_cursor_watch.py --arm|--stop|--acceptance` — cursor instrument, 4 hw watchpoints; FAILs on
   an unmapped writer pc or an enqueue-only shape.
5-9. The rest of the kit is self-documenting: `m66_insert_slot.py` (two-id INSERT),
   `m57_ui_enqueue.py` (one item), `m69_enqueue_gdb.py` (enqueue tracer), `test_hud_bar.py`
   (26 cases, ~45 s quiet / 20+ min loaded), `m65_screen.py --samples 8` (READ-ONLY meter),
   `m70_scan_writers.py` / `m70_type_sites.py` (static), `evidence.py audit [--delete]` /
   `budget` (BEFORE adding), and `scratch/m71/dis.py LO HI` for an objdump window over
   `scratch/m574/text.txt`. Run `--help` before inventing a flag.
## WHAT M71/M72 SETTLED (full text: the NAMED.md blocks, sessions 111 + 113)

- Pop: ONE item per completion, shift `0x4ef62c` over `0..pending-1` only, cursor untouched; the
  drain stops at validator `0x5a73f0`. Stale tail: see TRAPS.
- Gate/pay: `cmp [base+0x40], edi` at `0x4efa5e`, bail `0x4efa63`, pay store `0x4efed8`; `edi` =
  A x B, both MEASURED (M73). The visitor runs 2-3x per two boundaries with identical operands, so
  repeated bail rows are ONE answer. Facility exits `0x4f0a42`/`0x4f0b86`/`0x4f0c28` are armed and
  never fired (they need a NEGATIVE head) — no claim.
## STILL OPEN (in priority order)

1. **M74 (still open, branch `milestone/m74`) — WHO SETS `type[+0x30] & 4`, and WHEN.** The eleven
   absolute-address bit-2 writers are known (`0x4eed18` in FUN_004eec30, guarded `0x3f < param_2`;
   `0x573fed`/`0x574107`/`0x574117` in FUN_00573a90; whole-word `= 1`/`0x105`/`0x115` at
   `0x595f82`/`0x595f91`/`0x595f9c` in FUN_00595b10; `0x59d273`/`0x59d375`/`0x59d432`/`0x59db65` in
   FUN_0059ce10) and `scripts/m74_flag_watch.py` arms a conditional breakpoint on every one: ZERO
   fired while 193 and 194 went `0x41 -> 0x05` and 65/195 gained the bit in the same window
   (`m74flag2`, FAIL — `pending 0 -> 0`, no completion, so `when` is unproven). Leading candidate
   now: **`0x597487 mov WORD PTR [eax+0x30],dx` in FUN_00596850**, a stride-52 sweep
   (`add eax,0x34` ... `jne 0x5973bc`) copying a SOURCE TABLE into `+0x23..+0x30`, called only from
   FUN_00597ce0 and FUN_00597ee0. Next: read those two callers (mid-game reload or load-only?),
   breakpoint `0x597487` printing `tid = ($eax - 0x98ad88) / 52`, and arm only after reading
   `pending >= 1` back from memory. Second, still unexercised: the facility path's three no-pay
   exits `0x4f0a42`/`0x4f0b86`/`0x4f0c28` need a NEGATIVE head.
2. **Who calls the `0x4194b3` handler and what widget message `0x4d00` is** (it zeroes the
   cursor after a queue mutation; `0x584010` is the message sender, `0x4eb6b0` runs after it;
   it did NOT fire at a completion or a round boundary).
3. **M67's plan-descending LIST order still has no code behind it**: zero sites read the plan byte
   `+42`; the only 52-byte type-address computations (`0x40ad92`, `0x4164dd`, `0x4188f9`,
   `0x418932`) hand the record to the row's string builders.
4. **The `-3 / -6` formula** — stride CONFLICT stands: `0x984d38 + (-v)*48` (`0x40adae`,
   `0x4164f5`) vs `+(-v)*16` (`0x418914`, `0x41894d`).
5. Open from 104/105: the `income 1` accrual case (every M64 PASS window had `gap_delta = 0`):
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`.
6. Keep the suite green: `scripts/gate.py` runs every `test_*.py` plus `check_classes.py`; the
   current counts belong in the gate output, not in this file.

## LIVE FACTS / KIT

- **Box at session-115 close:** round 60, `terran.exe` up, University Base idx 0 (`0x95da10`)
  head 194, **pending 0**, storage 200 (poked, left there), stale queue tail `[194,194,193,193]`.
  `m57_ui_enqueue.py --cell-item 194` did NOT land on the second try (pending stayed 0) — always
  read `pending` back after an enqueue before arming. Records carrying `+0x30` bit 2: 64, 65, 128,
  129, 130, 131, 192, 193, 194, 195 (193/194 now `0x05` — bit 6 gone, bit 2 set); a fresh
  `m54b_clean.SAV` load has 193/194 at `0x41`. Korolev Center does not exist in this instance.
- **Prices (`price_of`, multiplier 9):** head 2 = 9, 192/193 (cost 2) = 18, 194 (cost 3) = 27 —
  but the gate charges `edi`, which for a designed head is ABOVE `price_of` while the markup bit is
  clear (M73: 45 for 194). Never assert arrival from `price_of`. Free chooser ids 194/2/1/0;
  195 -> -3, 196+ recordless. Enqueue refuses `pending >= 9` (`0x418b05`).
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3
  scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> enqueue (`m57_ui_enqueue.py --base-index
  0 --cell-item 194 --inserts 1`) -> **read `pending` back** -> the acceptance run. The load stalls
  at a misread `movie` screen ~1 in 3 times: re-run `--relaunch`, do NOT press Return on the save
  browser. Head 193 on top (M72's shape): enqueue the pair, poke storage to 9, read it back, then
  ONE boundary lets head 2 complete+pop -> head 193, pending 1.
- gdb: 4 hardware watchpoints and 10-12 clean silent breakpoints work (M71's arm; ~35 s per
  boundary under them, slower when the box is loaded); conditional breakpoints keep the other
  bases/records out of the log. No `si` inside a breakpoint command list; stdout DRAINED to a file
  (`stdbuf -o0`); a printf newline in a generated gdb script is ONE backslash + `n`; a watchpoint
  reports the pc AFTER the store (map it back, 16-byte window); `os.pread` on `/proc/<pid>/mem`
  EIOs — `seek`+`read`.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm —
  and it is a POINTER to the base record. Records are BYTES: a type record (stride 52, base
  `0x98ad88`) has name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0
  is the validator's first test); a base record has name `+19`, storage `+0x40`, pending
  `+0x4c`, queue `+0x50..+0x74`, `+0x98` = a copy of storage written by the pay epilogues.
- **Evidence budget: the gate FAILs at 30 MB.** Prune with `evidence.py audit --delete` BEFORE
  adding; a gdb run only balloons if you forget `stdbuf -o0`.

## TRAPS

- **Register semantics live in the encoding, not the name.** `[reg*4+0x98adb8]` means the register
  holds `tid*13` (52/4); `[reg+0x98adb8]` means it holds the record BYTE address `tid*52`. A
  conditional breakpoint testing such a register against the bare tid can NEVER fire — M74's first
  run printed "no writer fired" for exactly that reason, and its POSAFF row printed `f30=0x00`
  because the flag byte is `tid*0x34 + 0x98adb8`, not `tid*4 + 0x98adb8`.
- **Grep objdump case-sensitively.** It prints `DWORD PTR`, not `DWORD ptr`: a lowercase `ptr [`
  pattern reported zero stores to `[reg+0x30]` when there are 101. The flags word is also written
  through a record POINTER (`0x597487 mov WORD PTR [eax+0x30],dx`), which a grep for the absolute
  `0x98adb8` misses — enumerate BOTH forms before claiming a writer set is complete.
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it** (a
  "insufficient minerals to support Scout" dialog made two scripts' chooser clicks no-ops). Return
  clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt —
  never OK). Run `m70_clear_dialog.py` before blaming the chooser map.
- **OCR cost is LOAD, not code:** one `ocr_fast` pass took ~70 s and a suite >20 min when
  jellyfin/winedevice were busy, ~3 min quiet. Check `uptime` first.
- The base array compacts mid-run: locate bases BY NAME, pair windows by name AND owner byte,
  pair units by `(x,y,type,owner)`. M71's gate 8 guards against watching another base's queue.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by
  "first empty slot", never treat slot 10 (`+0x78`) as an entry, never plan a duplicate (the engine
  refuses an id already queued), and never read a stale tail as proof an id IS queued
  (`m66_insert_slot` FAILs when the item already appears there). Id 0 is both Colony Pod and the
  empty marker; the sentinel is -39 (`0xffffffd9`), not -38. A negative value belongs to the TYPE
  (196 -> -6, 195 -> -3) — never put 195/196+ in a shape.
- Per-faction count arrays read one LOWER per queued id mid-click, settling at OK;
  `0x94dc84 + 0x20bc*owner + (512+tid)` IS `0x94de84 + 0x20bc*owner + tid`. Diff whole rows.
- **A PASS on a shape that cannot discriminate is not a PASS.** Compute candidate predictions
  from the baseline first; refuse the shape if they all agree. An APPEND engine is consistent
  with ~55 rules — a FAIL there means "no key claim", not "the key is wrong".
- The harness race is real: `rN boundary: player walk came home to us after the flip` means the
  next window spans two rounds — RE-RUN, never edit the floor. Reload rather than poke into a
  UI-queued accrual acceptance (a base that just produced has `+0xd0` zeroed); poking minerals
  and reading back BEFORE attaching is right for a completion acceptance.
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
