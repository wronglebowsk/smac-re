<!-- Moved verbatim from SKILL.md (M53Q1, 2026-10-24) to keep the always-loaded file small. -->

## Running under Wine

SMAC reaches a **live, interactive single-player game** under a pure 32-bit Wine
(wine-10.20-staging-tkg-x86) on Xvfb :99 + llvmpipe; the Script.txt UI panes
render and respond to clicks. Launch command, i386 prereqs, xdotool click coords,
the i386-libpulse audio fix, the exe-verified input routing (a map click pans the view and cannot order a move until the pane is in destination mode 9, so drive
units with arrow keys),
Script.txt dialog geometry and the DirectPlay hypothesis are in **`references/wine-runnability.md`**.
- **Clean stale Wine before measuring:** orphaned `winedevice.exe` from dead sessions (ppid = systemd
  --user, same WINEPREFIX) burn ~40% CPU each (load 12 on 4 cores) and make the intro crawl so blind
  clicks mistime — `kill -TERM` them first.
- **Preflight every boot — two silent killers.** `kernel.yama.ptrace_scope` resets to 1 on reboot, which
  breaks BOTH `gdb -p` and `/proc/<pid>/mem` with EACCES: run `sudo sysctl -w kernel.yama.ptrace_scope=0`
  before any measurement (a "ptrace ok" note from an earlier session only holds until the next reboot).
  A reboot also wipes `/tmp`, so write evidence under `~/reverse/smac/evidence/`, never `/tmp`.
- **Locate widgets by TEXT, never by remembered pixels.** Capture with `xwd -root -silent -out f.xwd &&
  ffmpeg -i f.xwd -vf crop=800:600:0:0 -y f.png` (no ImageMagick here), then read it with
  `tesseract --psm 6 tsv` on a **2×** nearest-neighbour upscale and click the OCR box centre
  (2× costs 0.94 s where 3× costs 1.85 s and reads nothing extra; region crops are slower still). Fixed coords
  drift between UI states and blind clicks open ABOUT popups or base screens. Working pair:
  `~/reverse/smac/scripts/smac_state.py` (live memory: mission year `DAT_00985b00`, mode flags
  `DAT_00985dc8`) and `scripts/smac_play.py` (turn servicer); depth in
  `references/wine-headless-harness.md`. Fallback coords (800×600 window at 0,0): TURN COMPLETE (650,410),
  base-naming OK (400,171). After a `smac_play.py --turns` run returns, `cur_player` may still sit on an
  AI faction (a driver "turn" is counted as a year tick) — re-read `smac_state.py` and keep driving until
  control is back with the player before assuming our-turn state.
- **`xdotool` keys are dropped unless the window has focus** — call `xdotool windowfocus <win>` first (Xvfb
  has no WM to grant it). Without focus `Return`/`Escape` silently do nothing and every dialog looks
  undismissable, which reads exactly like a game hang.
- **Modal = key sink (M32 mechanism):** while a Script.txt modal is up the pump does not
call the key router at all — every key is silently dropped (looks like dead input). Run
`scripts/smac_probe.py --quiet` and require `screen=hud` before any key sequence; dismiss modals
first (M29 rules: `Return` for DATALINKS/PSI/event pages, one `Escape` for OPERATIONS DIRECTOR).
Advisor panes are TRANSIENT (auto-dismiss 1–2 s, faster than one OCR poll) and while up they
swallow the NEXT input event (echoes as menu code `0x20011`) — a rejected order looks like a
dropped keypress. **Never press a key to dismiss a transient pane:** it is already closing, so
the key lands on whatever replaced it — an `Escape` aimed at a caption pane CANCELS the
picker that opened behind it, and the game reports a plain "declined", which reads as the
option not being offered. Wait for the next pane (poll the tracer log or re-OCR) and answer
that one. gdb attach itself can drop X events: re-press the key after arming.
- **`/proc/<pid>/mem` pokes are ghosts while a tracer (gdb) is attached (M33).** Readbacks
lie: a poke reads back the new value, then shows a different one after attach. Poke only
with TracerPid 0, arm gdb AFTER poking, verify state after `kill -CONT`. M34 reconfirmed:
writes are fully dead under a live tracer (poked sel=46 → setter fired on the cycle's unit
50). Selection globals
(`0x91b5bc`/`0x91b5c4`) are additionally game-owned: the pump revalidates them and reverts
to the cycle's choice within ~1 frame when the poked unit fails the gate — press the key
IMMEDIATELY after the poke (no sleep) or use the game's own select (`FUN_0040c8d0`,
PICKUNIT picker via map click; calibrate clicks via the HUD tile-info panel OCR, not the
48×36 lattice formula). Under a tracer, steer selection only by completing actions
(HOLD-walk, see M34 footing); gdb bp conditions must cast `*(int *)($esp+4)` — bare
`$esp[1]` kills the batch script at the first hit.
- **Stop at a title/menu screen; never click it.** `Escape` there opens `Do you really want to quit?`
  and the next OK exits the game (process vanishes, nothing in the Wine log). Classify
  `SID MEIER'S ALPHA CENTAURI` / `really want to quit?` as a fatal state: save a screenshot and stop.
  Exception: the quit prompt also pops MID-DRIVE after `--turns` runs (session 65) while the game is
  otherwise healthy — Escape back to "Oops, no, wait!", never click OK.
  Dark/unrecognized frames get ~20 s of grace before a single Escape — cinematics end themselves.
- **A stalled round can be a LIVELOCK, not a modal.** Signature: `turn_flags` (`DAT_00985ae8`) bit 1 stuck
  set (0x10002) while `cur_player == player`, main thread `R` at ~60% CPU, screenshots md5-identical,
  drivers STUCK with no pane. Cause: a self/stale link in the `+48`/`+50` unit chains — both chain walks
  exit only on a NEGATIVE link, and the links are INDEX values, so array compaction manufactures them.
  Diagnosis (sample TWICE: clearing one chain reveals the second loop) and the 0xFFFF poke fix:
  `references/wine-headless-harness.md`, unit-array pitfalls.
- **`scripts/smac_play.py` has no `--mode stop`, and `--no-escape N` means "never press Escape during
  the first N seconds".** Set N above the run's `--timeout`: the driver classifies the mid-drive
  `Do you really want to quit?` dialog as a title screen (its banner IS the game title) and its own
  Escape press opens it. Bound a backgrounded driver with `timeout <run>` in the shell rather than
  signalling by name. `xwd` needs `-display :99` on this host (DISPLAY=:0 fails).
- **A PROPOSAL vote pane stalls the AI turn phase (M53n):** `YEA: 2  NAY: 3` is the vote TALLY, not a
  key hint (keys 2/3 do nothing; `smac_play.py --turns 1` returns STUCK while it is up). Click the bottom
  bars (true window coords) YEA (310,495) / NAY (398,495) / ABSTAIN (485,495), then the single OK bar
  (393,495). Find the bars by cropping the ROOT capture (`xwd -root -silent` + ffmpeg
  `crop=420:180:230:370,scale=iw*3:ih*3` + vision) — `xwd -id <win>` reads blank to tesseract. Focus
  (`xdotool windowfocus`), click, wait ≥2 s, re-capture to confirm the pane advanced.
- **Instrumentation lessons (M53n, `scripts/m53n_drive.py`):** a breakpoint at a function ENTRY hands you
  the caller free (`*(int *)$esp`); mid-body hits print 8 stack words in the same printf, post-matched
  against the call sites' return addresses (a fixed 5-byte `call` run makes the set derivable from
  disasm) — caller census with zero breakpoints inside the callee. And an accumulator that nets +1
  despite N accumulation-fires is being REBUILT, not added to: watch the field across the whole block,
  not just the accumulate site (4e78e0 zeroes +0xbc/+0xc0 at 0x4e79a5 and re-adds a per-item vector
  0x4e7be3-0x4e7c28 before 4e92c0/4e93f0 add the crawler terms); watchpoint `new=` sequences (0 then a
  ramp) are the tell. And a value-change watchpoint UNDERCOUNTS calls: a callee that rewrites the same
  value is invisible, so hits are state SWITCHES, not call counts (M53o: `4e3470` 19 hits vs 55 calls,
  every one from `4f6030`).
- **OCR targets must be ≥4 characters and region-constrained.** `yes` matches `Moyes:` (the unit
  panel's `Moves:`) and `ok` matches `Prokhor`, so a naive matcher clicks the map forever and the
  dialog looks undismissable. Same for dialog phrases: squash the joined OCR text to `a-z` and require
  the question body (`endtheturn`), never a similarity ratio — difflib fires on title/map text.
- **Click the OK bar ≥1.2 s after selecting a dialog row.** Faster and the confirm applies the
  previous selection ("No, let me move them"), the same question reappears, and it reads as a hang.
- `kill -TERM gdb` (batch) leaves terran.exe stopped (state `T`); `kill -CONT <pid>` revives it.
- **Script confirms queued behind a screen's widgets are UNREACHABLE** (M48d): CONFIRM DISBAND
  opened from the base screen slid behind base-panel chrome — rows/OK landed on chrome hitboxes,
  keys dead (M32), row clicks never moved the highlight: a modal that swallows input but whose own
  OK bar is occluded. Each menu-item click QUEUES another identical confirm; each OK click cancels
  one — a cycling look-alike pane is a draining queue, not a frozen pane. Recovery when trapped:
  relaunch + load autosave (saves at `<game>/saves/auto/Alpha Centauri Autosave N.SAV`, mission
  year u16 @ file 0x54 — read before trusting the slot number; slots rotate in place; zero progress
  lost since last round). `xdotool key BackSpace --repeat N` FAILS on this xdotool — loop it.
  TOUR hint popup (auto-opens on a screen's first view): Continue ≈(325,585); Social Engineering
  screen: OK ≈(240,368) commits, CANCEL does not close.
- **A python driver whose argv contains its run tag matches the bracketed `pkill -f [t]ag_...`
  pattern and SIGINTs ITSELF** at startup (the bracket only protects pkill's own cmdline).
  Kill stale copies with pgrep + os.kill skipping os.getpid() (fixed in `scripts/m49a_drive.py`).
- **A gdb watchpoint with no `commands … continue end` block ENDS a `-batch` run**: on the first hit the
  script has nothing left, gdb falls to its prompt and DETACHES — silently un-instrumenting the rest of
  the session (reads as a truncated log, not as an error). Give every watchpoint a printing `continue`
  block. **x86 gives 4 hardware watchpoints total** (8-byte windows need 8-alignment and cost 2 DRs
  each; 4-byte windows cost 1): watch at most 4 globals and cover the remaining addresses with a
  10 Hz `/proc/pid/mem` poller (`scripts/m53m_poll.py` pattern). And gdb's own messages are unbuffered while breakpoint `printf` output is block-buffered: the
  two streams interleave in the log, so attribute events by CONTENT (counters, an `off=0x50..0x74` run),
  never by line order, and read the log only after the driver's `--mode stop` (SIGINT drops the tail). Worse, a SHORT run can lose
  the whole buffered tail silently and read as "no breakpoint ever fired" (m53e1: the clicks clearly
  worked, the log had zero events) — **spawn gdb through `stdbuf -o0`** (fixed in
  `scripts/m53e_drive.py`). Separately: a command-list expression that uses a convenience variable
  which isn't a number aborts the sourced script and DETACHES silently ("Argument to arithmetic
  operation not a number or boolean", `m53e5_watch.log:50`) — bake the base pointer as a literal
  (`set $b = 0x962d30`) instead of reading `*(int *)0x8f0d60` per hit.
- **Vision-tool pixel numbers ARE true window coordinates; tesseract TSV numbers are internally
  rescaled** — never halve TSV values to get click coordinates. Settle any disagreement with
  `ffmpeg -vf crop=W:H:X:Y` + OCR on the crop before driving clicks (M53d wasted three runs on this).
- **Base production UI plumbing (M53d)**: pane-object fields `+0x3ff5c` = selected queue slot and
  `+0xb194` = chooser mode **but nothing stores through `pane+0xb194`** — the pane (static BSS
  0x6a9480) exposes the chooser sub-object at `+0xa1c` (0x6a9e9c) and the mode is stored as
  `[sub+0xa778]` = 0x6b4614 = pane+0xb194 (a byte scan of .text for disp32 `94b10000` finds exactly
  one instruction: the read at 0x4186ec); `FUN_00416080(this)` = pane redraw; `FUN_00496ad0(pane+0xa1c, base, owner,
  scratch)` = the modal item chooser (returns an item id or −9999); `FUN_00417ee0(slot, …)` = the
  dispatcher; `FUN_00417d20(item, insert_flag)` = the queue-slot writer. **Digit keys 1-9 pass a nonzero
  param_1 and only PREVIEW — nothing is written**; a real queue edit needs the QUEUE-row path.
  **Chooser bars (label-verified, M53e)**: HELP 153-233, OK 252-311, REPLACE 364-421, INSERT 472-523,
  DELETE 556-636, CANCEL 659-705 at y 336-352 (labels drawn inside the bars, fill RGB 103,91,181 —
  pixel (160,343) is the instant chooser-open test; 2x OCR cannot read the labels). **M53g corrected
  the handler**: the bar switch is `FUN_00496950` = **vtable+0xa8** of the chooser class (live vptr
  0x672298), jump table 0x496a9a indexes `param+2`; cases 0=HELP(gate)→1, 2=(gate)→7, 5=INSERT(gate)→5,
  **7→7 UNGATED**, −1=OK→0, −2=CANCEL→0+guard−1; gate = `cmp [this+0xa774],-1; je 0x496a91`, and
  **0x496a91 is the shared epilogue return — mode-storing paths reach it too (BAR_IGNORED there is NOT
  a refusal)**; **one handler run per click** (press; release dispatches nothing). `[sub+0xa774]`
  (pane+0xb190) IS the selection: a cell index in a 5-col grid (rows y~60/160/260 = cells 0-14, bar
  row = phantom cells 15-19, col3 = x 381-421); paint `FUN_004954e0` clears it to −1 (0x495541) then
  sets it to the enum index of the selected slot's item (0x495b00); icon/cell click → setter 0x4962ec
  (vtable+0x48). **Clickable rects ≠ drawn bars**: REPLACE = param 7 fires at (345/365,343) — its
  drawn body 381-421 is dead phantom-cell territory (setter path, handler never called); INSERT 5
  fires at 425/440/497. **OK = mode 0: writes
  nothing and does NOT restore the snapshot** (a committed edit survives OK); **CANCEL =
  `[sub+0xa774] = -1`** → returns −9999 → rewrites +0x50..+0x74 from the stack snapshot and exits
  without consulting the mode (makes armed REPLACE probes non-destructive); **HELP** opens the unit-design pane (bars y 356, CANCEL x≈614) whose
  CANCEL re-opens the chooser. QUEUE rows 1..8 = pending slots +0x54..+0x70 (row text y =
  439+12·(row−1)); the 9th pending slot +0x74 has no row; the head +0x50 is the LEFT panel.
- **Type-record `+41` is the COST FACTOR (M53b), not a weight and not turns.** `0x98ad88 + type·52 + 0x29`,
  one writer: `FUN_00595b10` (`ghidra_out/shard_015.c:9358`) = `FUN_00595820(chassis, weapon, armor,
  ability, reactor)` summing the alpha tables' cost fields (chassis `0x92ae80`/0x90 +4, weapons
  `0x92b950`/16 +3, armor `0x92fd10`/16 +0xa). Every price is `FUN_004e40a0(owner,1,-1) * +41` (10 = 100 %;
  printed in `FUN_00577280`, debited at `0x4efee0`), so `+41 = 1` costs 10 minerals; `+42` = the alpha
  Plan, `+43` = auto-calculated AI role (`weapon mode + 0x20` for noncombat packages). Proof pattern:
  `scripts/m53b_costcalc.py` + `scripts/m53b_types.py` re-implement the formula and diff it against live
  memory — every populated row accounted for, none left as "explained elsewhere". **Alpha comment headers name the columns** of sections whose
  rows are bare data (#CHASSIS/#WEAPONS/#DEFENSES/#UNITS) — read them before guessing a table's fields; enum gates decode the same way — index the alpha enum
sections by value (PLANS 10 = "Supply Convoy", ORDERS 3 = "Convoy", only 9 entries: live order
bytes 24/28 are engine-internal) before guessing what a small-int gate in sweep code means.
- **The alpha `#UNITS` loader (`FUN_00579f40`) overrides the type builder AFTER it runs**: Plan→`+42`,
  Cost→`+41` (0 = Autocalculate), Carry→`+40`, Icon→`+46` — all as disp8 stores off a `record + 50`
  register, row-capped at 0x40 so designed units are never overridden; the save loader restores
  `+41`/`+42` verbatim, so a loaded scenario can carry bytes the formula never produced. The ability
  table `0x98aaf4` (stride 28) is the 24 `#ABILITIES` rows: `int[0]` = the cost rule (rule switch = jump
  table indexed `rule + 7`, in Ghidra's case order), `int[2]` (**+8**, not +16) = the flag word whose bit
  0x400 adds a +1 surcharge on land chassis — the classic off-by-one field-offset trap.
- **COMM OFFICER 3-row variant** ("Yes..."/"No, close the channel."/"Display faction leader
  profile."): the colour row-click (bar_y−25) can select profile → UNIVERSITY INTELLIGENCE FILES
  table with CLOSE/DATALINKS bars at y≈345-360, OUTSIDE the 430-520 OK-bar band; the
  rightmost-bar row+bar cycle drains it but slowly (~8 min / 43 OCR passes once). OCR the row y
  and click it directly instead.
- **Colour-only pane driver works** (m48d_drive.py, 3 rounds 0 OCR 0 stalls): for any flat blue bar
  in y 150-430 click (bar_x, bar_y−25) [option row above] wait 1.3 s then click the bar; single OK
  bars live in the 430-520 band (find_ok_bar); TURN_BTN only when hud_up; tesseract only as a ≥35 s
  stuck fallback. A driver-generated gdb script (baked literal watch addrs from a content-based
  base re-scan + SELFTEST printf block) beats hand-edited scripts across process restarts.
- **A gdb `call` into game code is a last resort, never a first move.** Injecting
  `FUN_004cffa0(unit,x,y)` reached the callee twice (its `unit+4 |= 0x40` appeared in memory) but never
  moved a unit; once, fired **while a modal dialog was up**, it SIGSEGV'd and left the process alive with
  a completely dead UI (every click inert, main thread `R` with climbing `utime`) — recoverable only by
  relaunch + reload. If a breakpoint fires *inside* an injected call, gdb abandons the expression,
  detaches, and the inferior returns to gdb's dummy frame.
- **Production vector + middle pass (M53o/M53p):** `base+0xbc/0xc0/0xc4/0xc8` = NUTRIENT/MINERAL/ENERGY/PSI,
  REBUILT IN PLACE on every block execution by `FUN_004e78e0` (seed from faction+0x2e20, live 0; 7 add sites
  0x4e7c15, 0x4e7ea3, 0x4e85bd, 0x4e8739, 0x4e883b, 0x4e8951, 0x4e8a32; per-tile values = alpha
  `#RESOURCEINFO` verbatim @0x926bd8; its tail loop 0x4e8b6f-0x4e8d48 writes only +0x48). The scan and
  middle-pass machine rules — stack frame map, the two-pair candidate dispatch, the three swap-commit guards,
  budget and nibble bookkeeping, and which gating globals are scenario constants that cannot vary per visit —
  are in **`references/production-rebuild.md`**. Live-fit models: `scripts/m53o_recon.py` 36/76,
  `scripts/m53p_recon_a.py`. CAUTION (M53p): the model's entry scan mask comes from `DAT_008f0d30`, which
  `FUN_004e63b0` (FIRST call of `FUN_004e78e0`, 0x4e78e9) rebuilds every entry from the 21-dword table
  `0x8f0ccc..0x8f0d1c` (`DAT_008f0d30 = {bit i : table[i] != 0}`, 0x4e6925-0x4e694f), so a live read is
  valid ONLY for the base in `DAT_0068cbb0` (last processed).  Filter the census to self-consistent rows
  (`mask_in == processed`): on a driven round 46/76 pass and 40/76 are exact; the residual is a c4-only
  (ENERGY) class on fac 1/3/4 bases (`evidence/m53p_mask_findings.md`). The model reads `evidence/m53o_mem/*.bin` (written by
  `scripts/m53o_mem.py`), NOT live memory — refresh before every run and name the refresh: the same
  script gave 50/76 on the year-2381 dump and 18/76 on the year-2382 dump. Middle-pass score
  corrections 0x4e818a-0x4e81b6 are
  `cdq; sub eax,edx; sar eax,1` = trunc(x/2) of the DOUBLED value (cdq clobbers the pop+k2 edx that
  0x4e817f set for the 0x4e8182 guard), NOT subtract-then-sar.
- **Production chooser internals (M53h).** Candidate array `DAT_009267e4` (128 dwords, count `0x9267e0`) is
  built by `FUN_00596000(faction)` — ids = shared 0-63 then `faction<<6` designed units — and ordered by
  `FUN_005a29a0` (lockstep bubble sort, swaps only on strict `<` ⇒ stable) on
  `((ch_tbl[+1] + Plan*0x10)*0x40000) + (0x20 - weapon_power)*0x200 + (8 - chassis_class)*0x40 + (8 - 2*armor)`,
  `ch_tbl = 0x92ae80`/0x90 (`+0` class, `+1` naval flag), Plan = record+42, unavailable ⇒ key 999999999 ⇒
  last: **the order is Plan-major, never icon order**. Per-base filter `FUN_005a73f0(id, faction, base)`
  (record+0x30 bit 0, faction mask +0x2c, naval gate `FUN_004e4620(x,y)==0` when the chassis table says
  naval, prereq word +50 for alpha ids), then secret projects 1..0x47 via `FUN_005a6e70`.
- **Chooser return sign = record kind.** `FUN_00496ad0` returns `+item` when the selected node's detail
  flags (detail+8) have bit 0x20, else **`-item` where item is the index into the secret-project table
  `0x984d38`** (stride 48: +0 name, +4 effect ptr, +12 cost factor) — a queued project is a negative
  index, not an offset into a record.
- **Chooser bars are embedded controls, not Script.txt buttons.** Six children at
  `chooser_sub + 0xb74 + i*0xb4c` (sub = pane+0xb18c), param at control+0xa78, rect at
  +0x13c/+0x140/+0x144; (re)built per open by `FUN_00496ad0` right-to-left with params -2 CANCEL,
  7 REPLACE, 5 INSERT, 4 DELETE, -1 OK, 0; `x = ((W-0x20) - 103*count)/2 + (count-1)*103` (W =
  `sub+0xa824`, pitch 103, width `sub+0xb70` = 100, count = `sub+0xb6c`, y = `rows*cellh+8`). Release
  `FUN_005fab08` forwards control+0xa78 to **owner vtable+0xa8** — that param is the mode selector, and
  the factory `FUN_005f9e85(caption, param, x, y, w, h, owner, 0)` is where any dialog's bar params get
  set (caption `*(DAT_00997b20+off)`, `CharUpperA` — so bar text never appears in Script.txt).
- **Live list walks take count from header+0x10** (+8 head, +0xc cursor): using the cursor as the loop
  bound iterates ~79M times and looks like a hang. The chooser's item list is `sub+0xa780` = 0x6b461c and
  **survives the close**, so a cancelled chooser can still be read to see what was enumerated.
- **Secret-project table (M53i).** `0x984d38` IS the alpha `#FACILITIES` section verbatim (72×48 B;
  **live index = alpha row + 1**, row 0 null placeholder): +0 name / +4 effect string ptrs into a
  ~0x2100000 arena, +0xc cost factor, +0x14 prereq tech (−1 = None), +0x18 = −2 constant. A queue
  value < 0 is **−project index**; its price = `(&DAT_00984d44)[(−q)·0xc] × 0x4e40a0` — `0x5ac950`
  does NOT handle negative ids. `0x984d44` is dword 3 of the SAME record, not a second table.
  **Grep the DAT prefix (`984d`), never just the base**: Ghidra splits one table into
  `DAT_00984d38/44/4c/...` renderings by field offset, so a base-only grep silently misses refs.
  **Claim array (M53j):** the per-project claim table is **33 dwords at `0x985b3c`, index =
  project_idx − 0x27** — only projects ≥ 0x27 have a slot (`< 0x23` ones are tracked in the base
  facility bitmap at base+0x8c instead); value = the base INDEX that completed it, −1 = unclaimed, and
  it is written with the pane-loop's current-base global, not a per-loop index. The flat rendering
  `*(int *)(&DAT_00985aa0 + idx*4)` is the compiler folding that subtraction, and `0x985aa0..0x985b38`
  are unrelated globals (year, `n_bases`, mask) — not early claim slots.
