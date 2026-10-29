# Session notes archive — sessions 135-136

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 135 (2026-10-28) — M84f: the NETGAME gate is LIVE-measured; the poke leg is blocked by BOX STATE (m84fpath1 census, m84fleg4/5 invalid)

Prompt said M74; the repo pick was M84f (make the 0x4d00 POST leg fire). Branch milestone/m84f from main, carrying m84e's footing (instrument + docs + skill).

MEASURED (`python3 scripts/m84f_path_census.py --tag m84fpath1 --base 17 --inserts 1`, ONE invocation, 7 print-only bps + a /proc read-back): the netgame-gated block DOES run on a real UI insert — CHOOSER 2 (the 0x41860a modal call), CASE 1 (0x419355), BUMP 7 (`inc [0x94de84 + item + tid*8380]`, one per queue slot), EXIT 1 (0x4194b1), NETCALL 1 (0x528760 from 0x419368), netgame 0, pend 5 -> 6 read back. So s134's static reading is confirmed live: the block walks the queue, reaches `mov eax,ds:0x920434` at 0x4193b2 and, with the flag 0, takes `je 0x4194b1` = `push 1; mov [ebx+0x3ff5c],0; call 0x4eb6b0` — cursor zero plus a call, NO 0x4d00 post. Gates G1/G2/G3/G5 True, G4 False — G4 was MY wrong prediction ("the case never runs"); the case runs and stops AT the gate.

INSTRUMENT PITFALL (cost two runs): a MEMORY WRITE inside a gdb breakpoint command list — `set {int}0x920434 = 1` or `set var *(int *)0x920434 = 1` — aborts the batch with "Left operand of assignment is not an lvalue" at the FIRST hit and gdb DETACHES (m84fleg1/2/3: 36-line log = ARMED + 9 "Breakpoint at" lines + the error, 0 events; the driver's insert still lands because detaching resumes the inferior). The working poke is python-side: os.pwrite to /proc/pid/mem succeeds WHILE gdb is attached (m84fleg4: 632 writes, 0 errors, print-only bps logged cleanly).

BLOCKED (box state, not bytes): after `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` the game is 2150 r50 — University Base only, pend 0, credit 0, and the chooser's candidate array is EMPTY (`m57_ui_enqueue: FAIL: item 2 not in candidate array []`), so no insert can be driven; ds:0x8f0d60 is 0 until a pane opens, which killed the ARMED printf (`*(int *)($b + 0x4c)` on 0x4c -> EIO). The 2163 r63 state (chooser [192,195,194,193,2,0,1,196], Korolev pend 1) was LOST by that reload. NEXT: get a buildable state (fresh save + turns, or a later save), then `python3 scripts/m84f_post_leg.py --tag m84fleg6 --base <buildable idx> --inserts 2` — poke on odd visits, control on even, 9 print-only bps; the flag-1 arm is the only unmeasured leg.
Evidence: evidence/m84fpath1.gdblog (valid), evidence/m84fleg4.gdblog, evidence/m84fleg5.gdblog; scratch/m84f*.gdb; evidence 27.6 MB.

## Session 136 (2026-10-28) — M85: the tech/upkeep trio splits into "MP-only by design" and "reachable helper"; the live arm is blocked by the TURN TRIGGER (m85cens1 FAIL)

Static (deterministic: `ghidra_out/index.csv` addr/size_bytes + call lines in `scratch/m574/text.txt`): 0x52145e is inside FUN_00521070 (+1006), whose ONLY call site is 0x522376 — and m55_boundary.py's docstring identifies FUN_00521070 as the MULTIPLAYER 7-stage driver (mode_flags & 0x10). So the M67 "zero events" at 0x52145e is BY DESIGN in solo, not a bad breakpoint. 0x5a7d00 (+912) and 0x5a7f67 (+1527) are both inside FUN_005a7970: 47 call sites, one at 0x507e57 inside the human-turn loop FUN_0050f420 — so those zeros are an untaken branch, not unreachable code.

Live (`python3 scripts/m85_tech_census.py --tag m85cens1 --timeout 120`): FAIL — round 50 -> 50, year 2150 -> 2150, driver rc=1 ("no round boundary (year never moved) within 120.0s"), events = {ARMED: 1}. ONE VARIABLE ISOLATED: the same driver without gdb (`python3 scripts/m55_boundary.py --timeout 90`) fails identically, so the instrument is innocent — the box cannot end a turn.

Input probe (measured): game window = X id 10485761 "Sid Meier's Alpha Centauri" inside Wine desktop "smac - Wine Desktop"; state cur_player 3 (us), turn_flags 0, stage 0, round 50 — it IS our turn. Return is inert BOTH ways: XSendEvent (`xdotool key --window 10485761 Return`) and XTEST after focus (`xdotool windowfocus 10485761; xdotool key Return`) leave round/year unchanged. s132/s133 logged "one Enter fires the boundary within 0.2 s" on this box, so the trigger, not the code, changed with state. Next: CLICK the on-screen END TURN control (clicks still land — m57_ui_enqueue's do), or restore a state where Enter is the end-turn key (no unit selected).

CONFLICT recorded, unresolved: ds:0x920434 is "save_later" in m55_boundary.py's G table and "NETGAME" in the M84e/s134-135 docs. Compatible story (a chooser save-for-later mode would explain why FUN_0057ecf0 is the only 1-writer) but unproved.
Evidence: evidence/m85cens1.gdblog; scratch/m85cens1.gdb; scratch/m85diag.png (root grab, unread).

### s136 addendum — the live blocker is BOX-LEVEL INPUT FOCUS, not a driver choice

- `m85cens2` (driver switched to m44_idle, the pane-clicking turn advancer): driver rc=1 in 0 s, round 50 -> 50.
- `m85cens3` printed the child's stderr: a bare traceback, so the census is not the place to debug it.
- Run standalone, `m44_idle.py --tag m85probe --rounds 1 --budget 60` exits rc=0 and reports `reason: "1 rounds"`, but its own snapshot line still reads `[round 1] {"year": 2150 ...}` and `m85cens3_drv` (budget 420) does the same: the driver walks its loop and the YEAR NEVER MOVES.
- `xdotool getactivewindow` returns EMPTY and `windowfocus 10485761` does not change that: this X session has NO input focus at all. The game window is 800x600 at (0,0) (id 10485761, "Sid Meier's Alpha Centauri" inside "smac - Wine Desktop") and it IS rendering — mean luma 19.3, 19% of pixels > 32 in a fresh 800x600 grab — so this is not a blank window.
- Consequence: no keyboard OR pane-click path can end a turn on this box right now (keys: 6x Return inert via XSendEvent and via XTEST; clicks: m44's find_ok_bar route leaves year at 2150). s133's successful boundary runs happened while the window still had focus.
- NEXT (one command, before any boundary work): restore X focus — `xdotool windowactivate --sync 10485761` (needs a WM) or start/attach a WM, then re-check `xdotool getactivewindow` is non-empty; only then `python3 scripts/m85_tech_census.py --tag m85cens4 --rounds 1`.
