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

Merged: **M54A-M79** (#39-#80); M80 lands on this branch.

**M79 (s121, `m79net5`) — THE MARKER GATE IS A NETGAME + HUMAN-PLAYER TEST; POKING THE NETGAME
FLAG ON FIRES THE ELSE AND THE MARKERS SURVIVE.** Gate 0x4f0591-0x4f0637 admits the 0x100-clear
pass iff `0x920434 == 0 || !(0x985b10 & (1<<owner))`, ELSE 0x4f05bd `or BYTE [tid*52+0x98adb9],1`
and `jmp 0x4f0637` skips it. Live poke at 0x4f05a5 (pre 0 -> post 1, restored at 0x4f0637):
MARKSET tid=194, SWEEPIN/CLEAR/UPKCLR 0, end census 192=0x105 193=0x145 194=0x145 = the
NETGAME-ON prediction, replay exact 3/3, globals restored. NAMES: 0x920434 = netgame flag; 0x985b10 = HUMAN-PLAYER mask keyed 1<<faction (live {3});
sibling 0x985b11 = 0xff; NOT 1<<cur_player. NAMED M79, s121.

**M80 (s122, `m80band1`) — THE RECORD ARRAY IS 8 FACTION BANDS OF 64; FUN_00573a90 ARG 1 IS A FACTION.** esi = `[ebp+8]` = faction (0x573aa3); counter
`[ebp-0x18]` 0..0x80; index = `counter<0x40 ? counter : (counter&0x3f)+faction*64`;
0x574167-0x574176 rejects unless `index/64 in {0, faction}`; record = 0x98ad88+index*52 (0x57417e);
32 B copied INTO the record at 0x5741e1; 0x5741f0 `and BYTE [rec+0x30],0xfd`; 0x5741fe
`call 0x572800(faction, index, 0)`, whose band base is `param_1*0xd00`. LIVE: SW573 fac=5 idx=324/325 (ebx=324*52), SWENTER owner=5 tid=324/325 mode=0, CLR4 pre=0xc1 (bit 2 already clear), MARKHIGH(tid>=256) 0; census slots 324/325 `0 -> 0xc1` = "Impact Squad"/"Impact Rover", EMPTY at window start (`scripts/m80_band_census.py`). NAMED M80, s122.

**M78 (s120, `m78order3`) — THE 0x100 MARK AND ITS CLEAR ARE IN ONE PRODUCTION VISIT; THE CENSUS
THAT READS 0x105 IS A MID-VISIT SNAPSHOT.** visit 36: PRODFLAG 194 (pre 0x41) -> SWEEPCALL ret
`0x4efe83` -> MARK 192/193 (`0x5729d5`) -> GATE -> SWEEPIN -> CLEAR 192/193 (`0x4ef398`, pre
0x105/0x145); cross-visit pairs = [], so nothing re-marks and M77's "carriers survive a boundary"
is a MEASUREMENT ARTIFACT (the driver reads `/proc/pid/mem` while the engine sits between the two
stores). Census replay exact 4/4. (M80: the "indices 324/325/385/387" seen
at those sites are the sweep's TID argument — esi at 0x5741fe/0x574203 is the FACTION.)
NAMED M78, s120.

**M77 (PR #78, `m77gate1`):** the clear pass `0x4f05e2` is entered only through the gate block above (bail `[ebp-0x20]==0` at 0x4f0599; eligibility local last written at 0x4efe6c = FIRST production); live 10/11 visits bail, 1 sweeps, MARKSET 0. **M76 (PR #77, `m76marker1`):** the clear 0x4ef398 `and BYTE [tid*52+0x98adb9],0xfe` is FUN_004ef380's first statement (it lands on the record PASSED IN); in a designed window the caller is the production inline selector (test 0x4f060f, call 0x4f0626, ret 0x4f062b), which admits iff `flags & 0x105 == 0x105`. NAMED M77/M76, s118-s119.

**M73-M75 (PR #74-#76) — price, the `+0x30 & 4` bit, what the sweep marks.** price `edi = A x B` at
the gate `0x4efa5e`, `A = 0x4e40a0(owner,1,-1)` (9), designed head `B = byte(+0x29) + (C*P+50)/100`
with the markup skipped whole when `type < 0x40` OR `type[+0x30] & 4` (`0x5ac99c`); PRODUCTION sets
that bit (`0x4efe60`) and first production calls FUN_00572800 (`0x4efe7e`), whose loop marks EVERY
valid UNMARKED designed record (`0x5729d5`, live {192,193}); the `+0x24/25/26` triple + tier tables
are ALPHA-PATH only (validator `0x5a6cd0`), UNTESTED live. NAMED M73/M74/M75, s114-s117.
**M68 FAILED** (enqueue appends, no key named); **M63** `m63_pop.py`, `0x94de84` queued-count. Branches hold their scripts.

## THE INSTRUMENTS (run these FIRST, they replace reading prose)

1. `python3 scripts/session_brief.py` — <=4 KB: verdict, both bases, tagged CONFLICTs, the pick,
   the first commands. BLOCKED means do the FIX it prints before anything else.
   `python3 scripts/accept_ready.py` is the readiness oracle (17 unit cases in
   `test_accept_ready.py`): screen, running gdb, evidence headroom, then per base `pending > 0`,
   `minerals < price`, `credit > 0` — **re-read it immediately before you arm**. Screen fix:
   dialog -> Return, base PANE -> Escape, quit-prompt -> Escape (`m78_mark_clear.py
   normalize_screen()` does all three).
2. The price/flag/marker chain — each is silent breakpoints or hw watchpoints + a prediction from
   live memory + a read-back: `m73_price_split.py`, `m74_flag_hw.py` (4 hw watchpoints on flag WORDS,
   refuses to drive unless gdb armed them), `m75_sweep_replay.py`, `m76_marker_clear.py`,
   `m77_gate_trace.py`, `m78_mark_clear.py` (census APPENDED into the gdb log), `m79_netgame_poke.py`
   (`m79net5`: POKE 0x4f05a5 + RESTORE 0x4f0637, needs >= 3 boundaries). `m72_gate_watch.py` is the
   VISIT GATE; `m74_flag_watch.py` FAILED twice; `m71_pop_watch.py` reproduces M71 only.
3. Self-documenting (`--help` before inventing a flag): `m66_insert_slot.py`, `m57_ui_enqueue.py`,
   `m69_enqueue_gdb.py`, `m70_cursor_watch.py`, `m65_screen.py --samples 8`, `m70_scan_writers.py`
   (static), `evidence.py audit [--delete]` / `budget`, `scratch/m71/dis.py LO HI` (objdump window).
## STILL OPEN (in priority order)

1. **M81 — the record-creation writer and the `+0x30` bits 6/7.** M80: slots 324/325 were EMPTY at
window start and read "Impact Squad"/"Impact Rover" with `+0x30 = 0xc1` by the time FUN_00573a90
reached 0x5741f0 (CLR4 pre=0xc1, so the `and ~4` was a NO-OP); the 32 B copy at 0x5741e1 covers
bytes 0..0x1f, so NOTHING named writes `+0x30` on the create path. Cheap shape: 4 hw watchpoints
on the flag WORDS of the next free slots (326/327) + a breakpoint at 0x5741e1, one window. Then:
what bits 6/7 mean (ours 192=0x105 193/194=0x145, AI 324/325/386=0xc1, 449=0x1c5); who calls
FUN_00573a90 (ret 0x5749a7 x6 / 0x574da9 / 0x575424); why the sweep's band-walk guard
`tid<0x40 || flags&4` never engages on a fresh record; the upkeep/tech passes (0x52145e /
0x5a7d00 / 0x5a7f67, ZERO events in every window); the alpha path (`0x5a6cd0`).
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

- **Box at session-122 close:** `terran.exe` UP (the binary is `terran.exe` — pgrep -x terrans.exe
finds nothing), fresh `m54b_clean.SAV`, round ~52, University Base idx 0 pending 1 head 2 price 9;
slots 324/325 now EXIST as faction 5's "Impact Squad"/"Impact Rover" (flags 0xc1); our 192=0x105
193=0x145 194=0x145 still CARRY 0x100 because the M79 netgame poke let MARKSET run. Gate globals
at baseline: `0x920434`=0, `0x985b10`=0x08 (human mask = player 3), `0x985b11`=0xff, cur_player
`0x985dcc`=3; `*DAT_008f0d60` = the base record (+4 owner, +0x40 storage, +0x4c pending, +0x50
queue head, +0x98 storage copy). Screen hygiene BEFORE arming: pane -> Escape, dialog -> Return,
quit-prompt -> Escape (`m78_mark_clear.py normalize_screen()`); an Escape on the bare map RAISES
the quit prompt. Always read `pending` AND the head back after an enqueue.
- **Prices (`price_of`, multiplier 9):** head 2 = 9, 192/193 = 18, 194 = 27 — the gate charges `edi`
  (M73); never assert arrival from `price_of`. Free chooser ids 194/2/1/0; 195 -> -3, 196+ recordless;
  enqueue refuses `pending >= 9` (`0x418b05`).
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
- The base array compacts mid-run: locate bases BY NAME, pair windows by name AND owner byte, pair units by `(x,y,type,owner)`.
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

One screen: what changed, the acceptance numbers WITH the command, what is open, the next pick.