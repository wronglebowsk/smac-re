# NEXT_PROMPT.md — footing for the next session (session 116 close, 2026-10-28)

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

Merged: **M54A-M74** (#39-#75)

**M73 (PR #74, merged) — WHAT THE GATE'S `edi` IS MADE OF. ACCEPTANCE PASS, 10/10 gates, tag
`m73split4`: `edi = A x B`; `A = 0x4e40a0(owner,1,-1)` (9 = Python `cost_multiplier`); for a
DESIGNED head `B = 0x5ac950(head,[0x68cbb0],0) = byte(+0x29) + (C*P+50)/100` (measured `C 3`,
`P 50` -> `edi 45` for 194 where `price_of` says 27), and the markup is skipped whole when
`type < 0x40` OR `type[+0x30] & 4` (`0x5ac99c`). Full numbers: NAMED M73 block, notes s114.

**M74 (PR #75, merged) — WHO SETS `type[+0x30] & 4`, AND WHEN. ACCEPTANCE PASS, tag `m74flag3`:**
PRODUCTION sets it: `0x4efe60` in FUN_004ef6d0 (`mov ax,[rec]; or al,4; mov [rec],ax`, designed
only, between gate `0x4efa5e` and pay `0x4efed8`); first production calls FUN_00572800(tid) at
`0x4efe7e` (sweep ORs `0x104` onto matching records; marker cleared by FUN_004ef380 `0x4ef398`).
Instrument `m74_flag_hw.py` (hw watchpoints on flag WORDS); pcs `0x4efe67/0x5729de/0x4ef39f`.
RETRACTED: `0x597487` is a save/load codec (`0x93327a` table). Full text: NAMED M74-RESOLVED, s116.

**M68 (no PR, FAILED):** 212 sort rules, 55 predict an append, the live enqueue DID append — no
key named (M70's cursor mechanics explain the appends). **M63 (no PR):** `m63_pop.py`, the
`0x94de84` queued-count correction, 384/386 identity crossing. Branches hold their scripts.

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
   plus `0x4efa5e` and censuses all 256 records' `+0x30` (M74: FAILED twice); **`m74_flag_hw.py`** —
4 hw watchpoints on the flag WORDS themselves, prints pc+val per store, refuses to drive unless
gdb armed 4 HARDWARE watchpoints (M74 PASS, tag `m74flag3`).
4. `m70_cursor_watch.py --arm|--stop|--acceptance` — cursor instrument, 4 hw watchpoints; FAILs on
   an unmapped writer pc or an enqueue-only shape.
5-9. The rest of the kit is self-documenting (`--help` before inventing a flag):
   `m66_insert_slot.py` (two-id INSERT), `m57_ui_enqueue.py` (one item), `m69_enqueue_gdb.py`
   (enqueue tracer), `test_hud_bar.py` (26 cases), `m65_screen.py --samples 8` (READ-ONLY meter),
   `m70_scan_writers.py` / `m70_type_sites.py` (static), `evidence.py audit [--delete]` / `budget`
   (BEFORE adding), and `scratch/m71/dis.py LO HI` for an objdump window over `scratch/m574/text.txt`.
## WHAT M71/M72 SETTLED (full text: the NAMED.md blocks, sessions 111 + 113)

- Pop: ONE item per completion, shift `0x4ef62c` over `0..pending-1` only, cursor untouched; the
  drain stops at validator `0x5a73f0`. Stale tail: see TRAPS.
- Gate/pay: `cmp [base+0x40], edi` at `0x4efa5e`, bail `0x4efa63`, pay store `0x4efed8`; `edi` =
  A x B, both MEASURED (M73). The visitor runs 2-3x per two boundaries with identical operands —
  repeated bail rows are ONE answer. Facility exits `0x4f0a42/0x4f0b86/0x4f0c28` need a NEGATIVE
  head — no claim.
## STILL OPEN (in priority order)

1. **M75 — the production sweep's MATCH SEMANTICS.** FUN_00572800(param_1, tid, 0), called at
   `0x4efe7e` on a designed unit's FIRST production, ORs `0x104` onto records whose bytes
   `+0x24/+0x25/+0x26` equal the produced unit's, valid (`&1`), unmarked (`!( &4)`), passing
   validator `0x5a6cd0`, rank-compared via `DAT_0092b950`/`0x92fd18` (indexed by those bytes
   times 0x10). Live: 194's production marked 193 but NOT 195/65. Cheap start, NO box: dump
   `+0x24..+0x26` + `+0x2c` for 64/65/128-131/192-195 from live memory or the save blob and
   diff 193/194 vs 195/65; name the three bytes (chassis? level? domain — note `+0x24` indexes
   the M73 markup table) and what the rank tables rank. Also open: other FUN_00572800 callers
   (shard_002 `param_3=1`, shard_012:20852, shard_014:17826), FUN_004ef380 callers
   (shard_013:12093, `DAT_0091b5b4`), the s115 `0x41 -> 0x05` bit-6-LOST write (whole-word —
   likely `0x595f82/91/9c`), facility no-pay exits `0x4f0a42/0x4f0b86/0x4f0c28` (NEGATIVE head).
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

- **Box at session-116 close:** round 53, `terrans.exe` UP (s115's box was DEAD — a stale Xvfb
  frame read as screen `help`; check `ps` for terrans before trusting any screen), University
  Base idx 0 (`0x95da10`) head 194 pending 0, 193/194 flags `0x45` (bit 2 set at production —
  M74). Fresh `m54b_clean.SAV` loads 193/194 at `0x41`. Korolev Center does not exist here.
  Always read `pending` back after an enqueue before arming.
- **Prices (`price_of`, multiplier 9):** head 2 = 9, 192/193 (cost 2) = 18, 194 (cost 3) = 27 —
  but the gate charges `edi` (M73: 45 for 194 while the markup bit is clear; M74: production
  SETS the bit, so later visits charge 27). Never assert arrival from `price_of`. Free chooser
  ids 194/2/1/0; 195 -> -3, 196+ recordless. Enqueue refuses `pending >= 9` (`0x418b05`).
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3
  scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> enqueue (`m57_ui_enqueue.py --base-index
  0 --cell-item 194 --inserts 1`) -> **read `pending` back** -> the acceptance run. The load stalls
  at a misread `movie` screen ~1 in 3 times: re-run `--relaunch`, do NOT press Return on the save
  browser. Head 193 on top (M72's shape): enqueue the pair, poke storage to 9, read it back, then
  ONE boundary lets head 2 complete+pop -> head 193, pending 1.
- gdb: 4 hardware watchpoints and 10-12 clean silent breakpoints work (~35 s per boundary under
  them); conditional breakpoints keep the other bases/records out of the log. No `si` inside a
  breakpoint command list; stdout DRAINED to a file (`stdbuf -o0`); a printf newline in a
  generated gdb script is ONE backslash + `n`; a watchpoint reports the pc AFTER the store (map
  it back, 16-byte window); `os.pread` on `/proc/<pid>/mem` EIOs — `seek`+`read`.
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
  conditional breakpoint testing such a register against the bare tid can NEVER fire — M74's first
  run printed "no writer fired" for exactly that reason, and its POSAFF row printed `f30=0x00`
  because the flag byte is `tid*0x34 + 0x98adb8`, not `tid*4 + 0x98adb8`.
- **Grep objdump case-sensitively.** It prints `DWORD PTR`, not `DWORD ptr`: a lowercase `ptr [`
  pattern reported zero stores to `[reg+0x30]` when there are 101. The flags word is also written
  through a record POINTER (`0x597487 mov WORD PTR [eax+0x30],dx`), which a grep for the absolute
  `0x98adb8` misses — enumerate BOTH forms before claiming a writer set is complete. A
  read-modify-write through a COPIED register (`mov ax,[x]; or al,4; mov [x],ax`) evades BOTH
  shapes — M74's setter `0x4efe60` is exactly that. When the writer set is in doubt, skip the
  grep: `m74_flag_hw.py`-style HARDWARE watchpoints on the FIELD answer "who writes it" in one run.
- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it** (a
  "insufficient minerals to support Scout" dialog made two scripts' chooser clicks no-ops). Return
  clears a dialog; a BUILD/base PANE needs Escape (Escape on the bare map raises the quit prompt —
  never OK). Run `m70_clear_dialog.py` before blaming the chooser map.
- **OCR cost is LOAD, not code:** one `ocr_fast` pass took ~70 s when jellyfin/winedevice were
  busy, ~3 min quiet. Check `uptime` first.
- The base array compacts mid-run: locate bases BY NAME, pair windows by name AND owner byte,
  pair units by `(x,y,type,owner)`. M71's gate 8 guards against watching another base's queue.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue by
  "first empty slot", never treat slot 10 (`+0x78`) as an entry, never plan a duplicate (the engine
  refuses an id already queued), and never read a stale tail as proof an id IS queued
  (`m66_insert_slot` FAILs when the item already appears there). Id 0 is both Colony Pod and the
  empty marker; the sentinel is -39 (`0xffffffd9`), not -38. A negative value belongs to the TYPE
  (196 -> -6, 195 -> -3) — never put 195/196+ in a shape.
- Per-faction count arrays read one LOWER per queued id mid-click, settling at OK;
  `0x94dc84 + 0x20bc*o + (512+tid)` == `0x94de84 + 0x20bc*o + tid`. Diff whole rows.
- **A PASS on a shape that cannot discriminate is not a PASS.** Compute candidate predictions
  from the baseline first; refuse the shape if they all agree. An APPEND engine is consistent
  with ~55 rules — a FAIL there means "no key claim", not "the key is wrong".
- The harness race is real: `player walk came home to us after the flip` = the window spans two
  rounds — RE-RUN, never edit the floor. Reload rather than poke into a UI-queued accrual
  acceptance (a base that just produced has `+0xd0` zeroed); poke minerals and read back BEFORE
  attaching for a completion acceptance.
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
