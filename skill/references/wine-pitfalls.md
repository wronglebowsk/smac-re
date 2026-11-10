# wine pitfalls

Depth reference for `skill/SKILL.md` (smac-cvr-format) - moved whole at s242;
the hot core in SKILL.md keeps the summary and the pointer.

## Running under Wine — top pitfalls (depth: `references/wine-operations.md`)
- **Preflight is one command, and it comes FIRST:** `python3 scripts/smac_preflight.py` (read-only,
  exit 1 on any FAIL) checks the authoritative address table, `terran.exe` alive with `TracerPid: 0`
  and no stray gdb, and prints OUR bases BY NAME with index/coords/pending/head/minerals/income plus
  the unit decode, /tmp room and the evidence budget. `SMAC_PID=<pid>` overrides the pgrep; it is also
  the negative test. Window is 10485761 (800x600). `xwd` needs **`-display :99`** (`DISPLAY=:0` captures blank). `scripts/session_brief.py` and `accept_ready.py` print `BLOCKED: terran.exe not running` (exit 1) when the
box is down — read that as "relaunch first". A `CalledProcessError` traceback from either means the checkout
predates the pid guard (`M.find_pid()` unguarded): fix it there, do not fresh-load blind. It reads the LIVE box, so it runs for
MINUTES: request `timeout 400` (or background it) instead of the default, and read a timeout as slow, not as hung.
- **X input focus is a precondition — but `getactivewindow` is a RED HERRING on this display.**
  `xdotool getactivewindow` ALWAYS fails on :99 (no WM supports `_NET_ACTIVE_WINDOW`; it errors
  "claims not to support" even when focus is perfect). The authoritative check is
  `xdotool getwindowfocus getwindowname` == "Sid Meier's Alpha Centauri", and
  `xdotool windowfocus 10485761` works WITHOUT a WM (windowactivate is the WM-needing verb; s136
  misread this and lost a session). Prove keys land cheaply before blaming the box: one Escape on an
  open base pane flips classify base->hud. A box CAN still swallow turn-end input with focus fine:
  at the s135 state (2150 r50) XTEST Return AND a click on the measured TURN COMPLETE center both
  did nothing (no confirm dialog, round unchanged) — the repair is a fresh save load
  (`SMAC_SAVE=... scripts/m54a_load.py --relaunch`), which restored the boundary immediately.
  `scripts/m44_idle.py` is NOT a driver under gdb: it asserts `TracerPid == 0` at entry (census gdb
  IS the tracer) and its `--rounds 1` snapshot condition `y > last_year - 1 and not rounds` counts
  the CURRENT turn as a completed round, so it exits rc=0 in 0 s having done nothing — use
  `scripts/m55_boundary.py` (no tracer assert, windowfocuses itself) as the boundary driver.
  Corollary for acceptances: any milestone whose PASS needs a boundary must gate on a live year/round
  DELTA read from /proc/pid/mem first, or it will "prove" its sites unreachable from a box that
  could not run them at all.
- **Vision-tool coordinates are SCALE-SHIFTED on 800x600 frames; click targets must come from OCR
  word bboxes or pixel scans.** s137: vision put the TURN COMPLETE bar at y~471 (real y 405-427, OCR
  bbox center 675,416); the click at the vision coord hit the recenter box (y~484) and only scrolled
  the map — it looked like "clicks land but the engine ignores the button".
- **"Do you really want to quit?" is the killer dialog.** Escape returns to "Oops, no, wait!"; never
  click OK (the next OK exits the game and the process vanishes silently). Its banner IS the game title,
  so a classifier can mistake it for the title screen — this is also why the driver's own Escape press
  pops it mid-drive.
- **`scripts/smac_play.py` has no `--mode stop`.** Args: `--turns --timeout --no-escape --verbose
  --order --unit --turns-after --tag --no-verify --key-only` plus the M54c in-loop order flags
  `--orders-per-turn N` (default 2), `--order-budget S` (default 35), `--no-orders`. Ordering is
  ON inside the unattended loop now: each player turn pokes the selection slot, fires one hotkey,
  services the pane, and verifies `unit+17` moved into the byte set that key may produce — an
  order counts only as that memory delta, never as a screenshot. `--no-escape N` = "press no Escape during
  the first N seconds" — set N above `--timeout`. Bound a backgrounded driver with shell `timeout`.
  Launch a long run through the agent's tracked background mode (`exec python3 scripts/smac_play.py
  … > /tmp/<tag>.log 2>&1`), never `nohup … &` — nor ANY `&`-backgrounded chain, `cmd && other &` included — in a foreground call:
the wrapper is refused there (re-send the whole thing through the tracked background mode), and
  a shell that backgrounds and exits hides the driver's own pid — find it with `pgrep -f smac_play.py`
  and `kill <pid>`. Never signal by name (`pkill -f`/`pgrep|kill` matches your own argv).
- **A PROPOSAL vote pane stalls the AI phase.** `YEA: 2  NAY: 3` is the TALLY, not a key hint. Bars in
  TRUE window coords: YEA (310,495) / NAY (398,495) / ABSTAIN (485,495), single OK (393,495); click only
  after `xdotool windowfocus <win>`; OK >= 1.2 s after selecting. Capture with `xwd -display :99 -root
  -silent`, 2x ffmpeg upscale, tesseract (>=4 chars, region-constrained).
- **A round advancing while you watch is AUTO-END, not progress, and a walk frozen on an AI faction is
  a modal event dialog, not a livelock.** With all units HELD the engine closes our turn on its own in
  1–2 s; `cur_player == ours` is a window, not a state. Heartbeat model and dismissal cadence:
  `references/solo-round-boundary.md`.
- **Auto-end does NOT fire while any unit is actionable — and a unit built at the boundary is.** So
  HOLD every record (`+17` = 2, poked with TracerPid 0 and read back) BEFORE arming a multi-boundary
  watch: held units flip a round in 1-2 s, an unheld box sits parked on our turn for the whole budget.
  A produced unit arrives order 0, the cursor parks on it, and Return every 2 s for 150 s changes nothing
  (`cur_player` ours, `turn_flags` 0, year unmoved). ONE `h` on the cursor unit (→ HOLD) closes the turn
  at once, and that `h` needs orders mode `0x91b5b8` = 1 — at 0 every order key is a silent no-op
  (the base-display recipe turns it off, so restore it), which looks exactly like a wedged turn.
  And a popup whose default row is not OK does not close on Return — Return CYCLES its options
  (Operations Director defaults to "Zoom to Base Control"); click its OK instead. The end-turn
  confirm ("SOME OF OUR UNITS HAVE NOT YET MOVED … do you really want to end the turn now?") takes
  NO Return at all: click its YES row and then the OK bar ~26 px below, 1.2 s apart
  (`smac_play.answer_confirm`); a driver that only presses Return sits on it with the year frozen
  until its whole budget is gone. When the year stops moving, take ONE frame and `classify` it
  (it returns `confirm`) before pressing anything else. Cadence, coords, and the queue/gate rules:
  `references/production-queue.md` — including why an arrival round predicted from ROUND-START fields
  is not exact (the visit recomputes `+0xd0`, so the same snapshot produced no arrival and then an
  arrival one round later), and the store-sequence accounting that replaces it.
- **A stalled round can be a LIVELOCK, not a modal:** run `python3 scripts/m53q_livelock.py` (census of
  the `unit+48`/`unit+50` chains; `--fix` repairs). Signature: `turn_flags` bit 1 set + a hot main thread
  + byte-identical screenshots.
- **A turn that never advances can also be a CLASSIFIER miss, with no modal visible.** OCR here is
  unreliable in both directions: a clean HUD reads `unknown` when the TURN COMPLETE row fails to
  render legibly — measured 2026-10-26: 8 freezes of ONE unchanged HUD put `complete` in the button
  row 3 of 8 times while the HUD's bottom status bar (`Mission Year` + the faction score row +
  `Energy:`, y 548-592) read 8 of 8, and the bar fragments differently (`sisson tear zie`,
  `esston 2388`) — which is why `accept_ready.py` re-freezes up to 4 times and believes the BAR
  twice rather than trusting one pass (`smac_play.hud_status_bar`, `accept_ready.verdict`,
  `references/screen-read.md`, `scripts/test_hud_bar.py`) — and with the production line drawn in the message box even the chrome
  (MENU/COMMLINK) goes illegible, so the clean-HUD oracle is MEMORY, not the chrome read:
  `cur_player == player`, `turn_flags & 2` clear, and no bar drawn at y 145-200. Peek one frame
  before running any Escape-on-`unknown` clearing loop — at a garbled-but-clean HUD it raises the
  quit prompt), and an advisor dialog
  reads `hud` when too few of its words land in the dialog band (its caption is the tell: a word of
  6+ characters, or two of 4+, at y 90-118 means something is drawn OVER the HUD). Both idle the
  loop silently: with `--no-escape` the first burns the whole turn budget doing nothing, and in the
  second every TURN COMPLETE click lands BEHIND the modal. Diagnose by reading the state, not the
  class: our phase + `turn_flags` clear + year unmoved = nothing is answering the modal.
- **Label a printed register from the encoding, and read entry arguments from `$esp`, not `$ebp`.** A
  breakpoint on a function's FIRST instruction sits before `push ebp; mov ebp,esp`, so `$ebp` is still
  the CALLER's frame: take the arguments from `*(int *)($esp + 4)`, `*(int *)($esp + 8)`, … and the
  caller from `*(int *)$esp` — the return-address field is the cheapest way to learn a function's caller
  set in the same window. Before printing any register as an index or offset, read the prologue for
  `mov reg,[ebp+8]`-style argument loads and check for a reassignment on the path that reaches the site:
  a callee-saved register holding arg 1 for the whole body is a PARAMETER (faction, owner, mode), not a
  cursor, and a ledger that calls it an index poisons later milestones. Print the raw value AND its
  derived forms (`$ebx`, `$ebx / 52`, `$ebx % 52`) so a mislabel is visible in the log, not discovered
  weeks later in a document.
- **Watchpoints:** x86 gives 4 hardware slots (an 8-byte window needs 8-alignment = 2 slots); pair with
  the 10 Hz poller `scripts/m53m_poll.py`; they fire on VALUE CHANGE, so a same-value rewrite is
  invisible. **Never watch a field the display reads constantly** (`base+0x40` mineral storage): the
  inferior crawls (a round per ~45 s, year apparently frozen) — break on the STORE sites instead and
  condition each on the address the store's OWN encoding computes — `[reg*4+disp]` means the register holds
`(index*stride)/4` and `[reg+disp]` means it holds the byte address, so a condition comparing the register
against the bare index never fires (`references/static-store-census.md` §9.3). At a store site the register side-values
  are not evidence (`$ecx` printed a base INDEX where d0 was expected): read the fields from the baked
  base address. **A bp on a LOAD prints the register's PREVIOUS value; a bp on a skipped loop's body
  never fires (a zero there is the gate); round-mutated values cannot come from a round-start
  snapshot** — `references/instrument-laws.md` §Where a breakpoint prints the wrong thing. Do **not** single-step for the after value — `si` inside a breakpoint commands list makes
  `gdb -batch` stop after the step and DETACH, ending the watch after one hit; for a plain
  `mov [reg+disp],src` the store's own source operand IS the value the field takes, and the sleeping
  `/proc/pid/mem` sampler is what proves it. A hardware watch reports `$pc` PAST the writing
  instruction — the store is the instruction BEFORE the reported address (a hit at `0x417e08` named the
  store at `0x417e04`), so disassemble BACKWARDS from a watch hit before hunting a store site. And when
  the field that governs the behaviour is a UI cursor/selection, POKE it and prove the write lands at
  the poked value: `queue[2]` for a cursor poked to 2 while the sort rule predicted slot 1 turned a
  confounded click observation into a controlled experiment (and refuse the shape when the poked value
  and the rival prediction agree). **A printf ERROR inside a breakpoint's commands block ABORTS the
  whole `gdb -batch` script and detaches the inferior mid-window**: the log truncates at the first hit
  while the turn driver keeps exiting 0, so an aborted window reads as a clean zero-event run.
  **A MEMORY WRITE in a command list fails the same way** — `set {int}ADDR = 1` and
  `set var *(int *)ADDR = 1` both raise `Left operand of assignment is not an lvalue` and detach at the
  FIRST hit; gdb reports the file's LAST sourced line (the trailing `continue`), so the line number names
  nothing useful and the message looks like a syntax problem in a script that armed fine. Signature of
  the whole class: an ARMED line + one `Breakpoint N at` per bp + `Error in sourced command file` + zero
  events, while the driver still exits 0 and its own writes land because the detach resumed the inferior.
  **So put the poke in Python, not in the breakpoint**: `fd = os.open('/proc/<pid>/mem', os.O_RDWR)` then
  `os.pwrite(fd, (1).to_bytes(4, 'little'), ADDR)` succeeds WHILE gdb is attached (a 50 ms thread held a
  gate global for a whole driver window: 632 writes, 0 errors, every printf-only bp logged). Keep the
  command lists print-only and let a thread hold the forced value; restore it after the window.
  **Guard every ARMED-time deref**: the selected-base pointer `ds:0x8f0d60` reads 0 until a pane is
  opened, so `*(int *)($b + 0x4c)` in the arming printf faults on address 0x4c and kills the batch
  before the first event — print `$b` alone or branch on `$b != 0`, and make a `/proc` reader return -1
  on `OSError` (an unmapped page raises EIO, not 0) so a bad pointer cannot abort the harness. gdb's
  printf reads an inferior pointer as a HOST address, so `%.20s` fed `*(char *)(rec+0)` errors
  ("Cannot access memory"); bp printfs emit NUMBERS derived from registers only (raw reg, reg/stride,
  reg%stride, `*(short *)(...)` values), never inferior strings, gate every pointer deref behind
`if $reg != 0 … end` (a null deref faults exactly like a string one and detaches the same way), and
substitute expressions as printf ARGUMENTS — an expression pasted into the
format string prints ITSELF and the log then parses as zero events (`references/static-store-census.md`
§9 point 10) — use `x/s` outside a commands block
  when a name is genuinely wanted. **A `dump binary memory` in a command list is the same class of killer:**
a non-literal target (`%s`, a convenience variable), an ARITHMETIC address range, or a
`python … read_memory … end` block each abort the sourced script at the first hit — the run logs `ARMED`
+ one `Breakpoint N at` per bp + ZERO events while the round keeps advancing, indistinguishable from "the
mechanism never ran". Bake the dump target as a literal absolute path (substitute with `str.replace()` on
a unique token), give the range two LITERAL addresses, and note convenience-variable arithmetic is 32-bit
SIGNED — an `end - start` inside gdb underflows and poisons every offset derived from it, so compute
lengths/offsets in Python and bake them as hex; one dump file per RUN with an `off=` field in the log
beats a per-hit filename (a second dump to the same path overwrites the first); **`append binary
memory` is what makes a per-hit series work** — plus loop-entry-vs-branch-target, the scan-window rule
and the snapshot-cadence law: `references/gdb-command-list.md`.
- **A hardware watchpoint cannot see a KERNEL write**: Linux installs a user DR breakpoint with the
  exclude-kernel bit, so bytes landing via `copy_to_user` inside a `read()` change with zero events —
  that is what a "silent census" means when a file read's destination IS the watched region. The fix is
  a different LAYER, not a re-armed watchpoint: strace `-e raw=` (prints the read's BUFFER POINTER) +
  `clear_refs=4`/pagemap soft-dirty + maps before/after; strace and gdb cannot both ptrace one task.
  Table, invocation and parsing laws:
  `references/ptrace-level-probes.md`.
Never build the gdb command list by running a Python `%`-format over
it: the template is full of `%d`/`%x` printf conversions and Python eats the first ones as its own
arguments, silently rewriting the breakpoints. Bake addresses and constants as literals, or substitute
with `str.replace()` on a uniquely-marked token, and diff the emitted `scratch/<tag>.gdb` before attaching. Bake addresses as literals, `stdbuf -o0`, drain gdb's pipe,
  and drive + snapshot in ONE backgrounded job (`scripts/m53n_drive.py` is the template). A **zero-event log is an instrument verdict until proven
otherwise**: arm one control breakpoint whose hit is guaranteed in the window and require its rows, and
read back BEFORE attaching that the watched event can even happen (queue head is the armed id,
`pending >= 1`, storage above what the gate can demand) — an unusable window is not a negative result
(`references/static-store-census.md` §9.8–9). **A whole subsystem path can be gated on another
subsystem's state**: with every base's production queue empty the research upkeep never runs, so a scorer
census logs zero events across boundaries while the round advances — satisfy the printed readiness FIX
before calling the sites unreachable, and echo the precondition in the harness's output so "gate unmet" is
distinguishable from "mechanism refuted".
- **A leg census gates on PREDICTIONS, not on hits.** Compute each site's expected hit count from live
  memory first (gate globals, args off `$esp`, the table values the branch loads), print the
  predictions, gate on agreement with the counters (`m86_helper_legs.py`, `m87_aaa20_trigger.py`).
  Demanding a hit at a site the TAKEN leg cannot reach FAILs the milestone, not the game — fix the leg
  map, never the floor. Tie every hit to a boundary (round/year at the hit); a window count is not a
  cadence.
**Before blaming a breakpoint for a zero, resolve the SITE's containment and its function's caller
count** from `ghidra_out/index.csv` — one read splits "unreachable BY DESIGN" from "UNTAKEN BRANCH". **To name who writes a field, use a hardware watchpoint on the address PLUS a
control watchpoint on an address you know changes** — a mnemonic grep misses stores made through
pointer-form `lea`; the static half of the same trap is to **classify each store by how its SOURCE register was
computed** — scan back for `or`/`and`/`lea` on that register before writing "assigned, never bit-set". Twenty-three
of twenty-seven memory-form `mov [reg+0x94d448],reg` stores were the write half of a register-level bit RMW, so the
field IS bit-set and only the four whole-value assignments (one a `lea`) can deliver an untouched bit: a store-shape
census sees the operand, never the provenance. **A gdb census >90 s goes through `terminal(background=true)` + `process_manage
wait` loops: the foreground caps at 420 s and killing a census mid-run leaves Wine hung (round frozen
after detach too) — recover via `m54a_load --relaunch`. Pair store-readback probes by EVENT ORDER
(RB follows ST); a {addr: last-mem} dict mis-pairs an address re-written later in the window; and
**detach only after the window is really over** — the turn driver returns rc=0 while other factions'
upkeep is still executing, so the last stores happen after the detach and log NOTHING, which FAILs a
read-back gate on the instrument while every other gate is green
(`references/instrument-laws.md`).**
`references/instrument-laws.md` carries the header order, the containment recipe, DictReader trap,
the watchpoint laws, the value-census laws, the printf-escape law, the event-grouping law, and the bit-leg
census / per-site argument-tuple parse rules.

When the target is reached only through a vtable or handler table, the pre-arm check is whether an
INSTANCE of its class exists at all: scan the writable `/proc/<pid>/mem` regions for the class's vptr
value — a class with no live instance logs zero hits at every method, whatever the window (recipes:
`references/code-atlas.md`).
Two more pre-arm checks, both cheap, both fatal if skipped:
- **The readiness oracle can print a FIX that stays unsatisfied after you run it.** `credit` is
  `base+0xd0`, RECOMPUTED EVERY ROUND by FUN_004e93f0 (M97: `[+0xc0] - [+0xf0] - [+0xe0]`; the
  "init-only, turns never raise it" claim is RETRACTED) — it holds 0 when upkeep exceeds income, so the
  reload chain restores a runnable box but will not clear the credit-0 line. That line blocks only the
  PAY-SITE family (their gates need storage >= price — take the per-boundary storage poke above the
  price); rebuild/upkeep censuses run green at credit 0 (M100/M102 did). Check the state a printed FIX
  demands is actually reachable before looping it.
- **A clean reload does NOT carry records created live in a previous session** — a prior run's new
  unit/type records are live state that no save holds, so yesterday's census is fiction after a
  reload. Re-census the watched slots from `/proc/pid/mem` in the same invocation that arms the
  harness, and make the harness assert armed == len(designed watch list) rather than a fixed floor:
  arming fewer watchpoints than the design list silently drops half the slots from the window. **Check the save can HOST the experiment before you reload it**: `m54b_clean.SAV` loads at 2150 r50 — University Base only, `credit` 0, and the chooser candidate array is ERA-DEPENDENT: after `m54g_prep` + one turn the INSERT lands even at minerals 0 / credit 0, but the FIRST enqueue attempt right after a turn-end can transiently print `item 2 not in candidate array []` — retry it once before blaming the save; reloading to clear a stray modal costs the later state (2163 r63, candidates `[192,195,194,193,2,0,1,196]`) AND the experiment. Clear the modal itself; gate any reload on `accept_ready.py` READY plus a non-empty candidate array.
The
  census→live-enumeration method (filter the store census by call-graph reachability, condition each
  breakpoint on the address the store's own encoding computes, scale included, accept by replaying the stores against the sampler) is
  `references/static-store-census.md` §9; §1–§3 carry the traps that make the STATIC half of it complete —
**Read §9 before hand-writing a watcher script** — condition arithmetic, log format and scorer gates are
solved there (uppercase-`PTR` greps, pointer-form stores, operand width).
Depth: `references/wine-operations.md`, `references/wine-headless-harness.md`
(turn automation, OCR/dialog state machine), `references/wine-runnability.md` (what runs at all).

