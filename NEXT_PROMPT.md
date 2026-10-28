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
  `SESSION_CURSOR.md` (<= 600 B) with `<ID> | done | in flight | next command`. A cut turn then
  costs the next session one read instead of a re-derivation.
- Every doc write is an append or a <= 2 KB patch. Never read-then-rewrite a file over 10 KB.
- Keep tool results small: `grep`/`sed -n` windows, `tail`, `scripts/evidence.py show`. A
  multi-KB result is context that cannot be compressed back.
- If the box is mid-run when you are cut off, say so in the cursor; never `rm`/`git checkout --`.
- The cursor is written by YOU, not by the harness: nothing else records what was in flight.

## THE LEDGER

Merged: **M54A-M72** (#39-#73): the load/boundary harness, the price chain (`0x4e40a0` x
`0x5ac950`), the queue mechanics (enqueue at the cursor, pop pops ONE item, shift
`0..pending-1`), and the gate `cmp [base+0x40], edi` at `0x4efa5e` (M72: `edi` is not `price_of`).

**M73 (this branch's PR) — WHAT THE GATE'S `edi` IS MADE OF. ACCEPTANCE PASS on one real
invocation** (`evidence/m73split4.gdblog`, 10/10 gates, tag `m73split4`): `edi = A x B`,
`A = 0x4e40a0(owner,1,-1)` (measured 9 = Python `cost_multiplier`), and
`B = 0x5ac950(head,[0x68cbb0],0)` which for a DESIGNED head is NOT the cost byte: `B =
byte(+0x29) + (C*P+50)/100`, measured `C 3`, `P 50` -> markup 2 -> `B 5` -> `edi 45` for head 194
where `price_of` says 27. The markup is skipped whole when `type < 0x40` OR `type[+0x30] & 4`
(`0x5ac99c`), and that flag is live STATE: 193 read `0x41` at arm and `0x45` at its first visit in
the same window — M72's 27 and this run's 18 are one id in two states. 28/28 unit cases,
instrument `m73_price_split.py`; details in the NAMED M73 block and notes s114.

**M68 (no PR, acceptance FAILED):** 212 candidate sort rules, 55 predict an append, and the live
enqueue DID append at round 51 — no key named; M70's cursor mechanics explain the appends.
**M63 (no PR):** `m63_pop.py`, the `0x94de84` queued-count correction, 384/386 identity crossing.
Both branches hold their scripts; neither is needed to move forward.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB: verdict, both bases, tagged CONFLICTs, the pick,
   the first commands. BLOCKED means do the FIX it prints before anything else.
2. `python3 scripts/accept_ready.py` — the readiness oracle (17 unit cases:
   `scripts/test_accept_ready.py`). Screen, running gdb, evidence headroom, then per base
   `pending > 0`, `minerals < price`, `credit > 0`. **Re-read it immediately before you arm.**
   `--no-screen` skips the OCR. If the screen reads `dialog`, run
   `python3 scripts/m70_clear_dialog.py` (it presses Return until the dialog is gone and
   prints each look); a BUILD/base PANE needs Escape, not Return.
3. `m71_pop_watch.py` (reproduce M71 only) and **`m72_gate_watch.py`** — the VISIT GATE: 12
   conditional breakpoints (`0x4ef6d0`, `0x4ef88e`, `0x4efa5e`, `0x4efa63`, `0x4efe41`,
   `0x4efed8`, `0x4eff4e`, `0x4f0a3d`, `0x4f0a42`, `0x4f0b4f`, `0x4f0b86`, `0x4f0c28`,
   `0x4f5a93`), storage poked and READ BACK before attaching, drives boundaries, 8 gates,
   one-line PASS/FAIL. Its `edi` is the visit's requirement, not `price_of` (M72).
   `m73_price_split.py` splits `edi` and is the M73 acceptance (10 gates, 28 unit cases).
4. `m70_cursor_watch.py --arm|--stop|--acceptance` — cursor instrument, 4 hw watchpoints; its
   `--acceptance` FAILs on an unmapped writer pc or an enqueue-only shape.
5. `m66_insert_slot.py --base-name NAME --item-a 194 --item-b 193` — the two-id INSERT (chooser
   read with it open, queue after each click; its "layout rules that fit = []" line is NOT our
   acceptance). `m57_ui_enqueue.py --base-index 0 --cell-item 2 --inserts 1` = one item.
6. `m69_enqueue_gdb.py --arm|--stop|--parse` — the enqueue tracer.
7. `test_hud_bar.py` 26 cases (~45 s quiet, 20+ min loaded); `m65_screen.py --samples 8` is a
   READ-ONLY screen meter; `m70_scan_writers.py`/`m70_type_sites.py` are static.
8. `evidence.py audit [--delete]` / `budget` BEFORE adding (gate FAILs at 30 MB; 27.2 MB now).
9. `scratch/m71/dis.py 4ef5d0 4ef6c8` — an objdump window over `scratch/m574/text.txt`; never
   read the whole dump.

## WHAT M71/M72 SETTLED (NAMED.md blocks, sessions 111 + 113)

- Pop: ONE item per completion, shift `0x4ef62c` over `0..pending-1` only, cursor untouched;
  the drain stops at validator `0x5a73f0`. Stale tail: see TRAPS.
- Gate/pay: `cmp [base+0x40], edi` at `0x4efa5e`, turn-around `0x4efa63` (`POSAFF` -> `BAILAFF`,
  nothing paid, queue untouched), pay store `0x4efed8`; `edi` = A x B, both factors MEASURED.
- The visitor runs 2-3x per two boundaries with identical operands: repeated bail rows are ONE
  answer, two bail KINDS in one window is the refusal case. Facility exits
  `0x4f0a42`/`0x4f0b86`/`0x4f0c28` are armed, never fired (need a NEGATIVE head) — no claim.

## STILL OPEN (in priority order)

1. **M74 pick — WHO SETS `type[+0x30] & 4`, and when.** M73 proved the bit is what turns the 50 %
   markup off (and that it flips mid-window: 193 `0x41` at arm -> `0x45` at its first visit after
   a designed unit completed). Two writers are known statically (`0x4eec30`, `0x4d20f0`, both
   unit-transformation paths) and neither is correlated with the observed flip; 8 of 256 records
   carry the bit after the run. Cheap shape: a conditional breakpoint on both writers plus a read
   of the 8 flagged ids before/after ONE designed completion. Second, still unexercised: the
   facility path's three no-pay exits `0x4f0a42`/`0x4f0b86`/`0x4f0c28` need a NEGATIVE head.
2. **Who calls the `0x4194b3` handler and what widget message `0x4d00` is** (it zeroes the
   cursor after a queue mutation; `0x584010` is the message sender, `0x4eb6b0` runs after it;
   it did NOT fire at a completion or a round boundary).
3. **M67's plan-descending LIST order still has no code behind it**: zero sites read the plan
   byte `+42`; the only 52-byte type-address computations (`0x40ad92`, `0x4164dd`, `0x4188f9`,
   `0x418932`) hand the record to the row's string builders `FUN_00626634` / `FUN_006265a2`.
4. **The `-3 / -6` formula** — the stride CONFLICT stands: `0x984d38 + (-v)*48` (`0x40adae`,
   `0x4164f5`) vs `+(-v)*16` (`0x418914`, `0x41894d`).
5. Open from 104/105: the `income 1` accrual case (every M64 PASS window had `gap_delta = 0`):
   `python3 scripts/m56_build.py --ui-queued <fresh idx> --boundaries 10 --timeout 400
   --no-poke-hold`.
6. Keep the suite green: `scripts/gate.py` runs every `test_*.py` plus `check_classes.py`;
   `test_m73_split.py` is 28/28. Latest counts belong in the gate output, not in this file.

## LIVE FACTS / KIT

- **Box at session-114 close:** round 54 → 58 across the four m73 runs; `terran.exe` still up,
  University Base idx 0 (`0x95da10`) head 193, pending 0, storage 0 after the last pay+create;
  units 2, 194, 193 built. Type records 64/128/129/192/193/194 now carry `+0x30` bit 2
  (0x41 -> 0x45 for 192-194) — a FRESH `m54b_clean.SAV` load has 193/194 at `0x41`. RELOAD before
  any acceptance that needs the markup path (`m73_price_split.py` pokes the bit and reads it back).
  Korolev Center does not exist in this instance (a fresh `m54g_prep`-style founding is needed).
- **Prices (`price_of`, multiplier 9):** head 2 = 9, 192/193 (cost 2) = 18, 194 (cost 3) = 27.
  The gate charges `edi`, which for a designed head is ABOVE `price_of` (M73) — never assert
  arrival from `price_of`. Free chooser ids 194/2/1/0; 195 -> -3, 196+ recordless. The enqueue
  refuses `pending >= 9` (`0x418b05`); both gdb instruments FAIL rather than arm at `pending+2 > 9`.
- **Reload recipe (~35 s, bare filename):** `SMAC_SAVE='m54b_clean.SAV' python3
  scripts/m54a_load.py --relaunch` -> `accept_ready.py` -> `m66_insert_slot.py --base-name
  "University Base" --item-a 194 --item-b 193` (or `m57_ui_enqueue.py --base-index 0
  --cell-item 2 --inserts 1`) -> the acceptance run. The load stalls at a misread `movie` screen
  about 1 in 3 times: re-run `--relaunch`, do NOT press Return on the save browser.
  **Head 193 on top** (M72's shape): enqueue the pair, poke storage to 9 and read it back, then
  ONE boundary lets head 2 complete+pop -> head 193, pending 1.
- gdb: 4 hardware watchpoints and **10 clean silent breakpoints worked** (M71's arm; ~35 s per
  boundary under them). Conditional breakpoints (`if $esi+0x95da10 == $b`, `if $ecx == $b`)
  keep every other base out of the log. No `si` inside a breakpoint command list; stdout must
  be DRAINED to a file (`stdbuf -o0`, `stdout=<file>`); a printf newline in a generated gdb
  script is exactly TWO backslashes + `n`; **a watchpoint reports the pc AFTER the store**
  (map it back, window 16 bytes); `os.pread` on `/proc/<pid>/mem` EIOs — `seek`+`read`.
- `scratch/m574/text.txt` = whole `.text` objdump (40.9 MB; addresses WITHOUT leading zeros —
  grep `4ef5d0:`, not `004ef5d0:`); Ghidra pseudocode is `ghidra_out/shard_NNN.c`. Parse with
  Python (`scratch/m71/dis.py`), never read whole. `scratch/` is gitignored.
- Ghidra's `DAT_008f0d60 + 0xNN` is a `short *` — double the offset, then check the disasm —
  and it is a POINTER to the base record. Records are BYTES: a type record (stride 52, base
  `0x98ad88`) has name `+0`, owner mask `+0x2c`, cost `+41`, plan `+42`, flags `+0x30` (bit 0
  is the validator's first test); a base record has name `+19`, storage `+0x40`, pending
  `+0x4c`, queue `+0x50..+0x74`, `+0x98` = a copy of storage written by the pay epilogues.
- **Evidence 27.2 MB of the 30 MB FAIL line** (59 images = 12.0 MB); a gdb run is ~2 GB of log
  only if you forget `stdbuf`. Prune with `evidence.py audit --delete` BEFORE adding more.

## TRAPS

- **A dialog swallows every click and every turn-end key while the HUD bar reads THROUGH it.**
  A "minerals output not sufficient to support Scout" dialog made two scripts' chooser clicks
  no-ops (guard 0, pending unchanged); after `m70_clear_dialog.py` the same clicks worked. Run
  it before blaming the chooser map. Return clears a dialog; a BUILD/base PANE needs Escape
  (Escape on the bare map raises the quit prompt — never OK).
- **OCR cost is LOAD, not code:** one `ocr_fast` pass took ~70 s and a suite >20 min when
  jellyfin/winedevice were busy, ~3 min quiet. Check `uptime` first.
- The base array compacts mid-run: locate bases BY NAME, pair windows by name AND owner byte,
  pair units by `(x,y,type,owner)`. M71's gate 8 guards against watching another base's queue.
- **The queue tail holds STALE ids** (the shift reaches only `0..pending-1`): never read a queue
  by "first empty slot", never treat slot 10 (`+0x78`) as an entry, never plan a duplicate (the
  engine refuses an id already queued). Id 0 is both Colony Pod and the empty marker; the
  sentinel is -39 (`0xffffffd9`), not -38. A negative value belongs to the TYPE (196 -> -6,
  195 -> -3) — never put 195/196+ in a shape.
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
