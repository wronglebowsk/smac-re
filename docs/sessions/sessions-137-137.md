# Session notes archive — sessions 137-137

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 137 (2026-10-28) — M85 CLOSED: the solo boundary IS live and DOES enter the helper; the M67 zeros split into "MP-only by design" + "branch not taken" (m85cens5 PASS)

Prompt said M74; the repo pick was M85 (PR #90 open, m85cens1-3 FAIL, blocker named as "no X focus").

BOX REPAIR (measured): s136's focus diagnosis was a red herring — `getactivewindow` ALWAYS errors on :99 (no WM supports _NET_ACTIVE_WINDOW); `xdotool windowfocus 10485761` sticks (`getwindowfocus getwindowname` returns the game window) and keys DO reach the game (one Escape flipped classify base->hud). But the s135-state box (2150 r50) swallowed every turn-end input: XTEST Return for 90 s did nothing, and a click on the MEASURED TURN COMPLETE center (OCR bbox (675,416); the vision tool's coords are scale-shifted — real bar y 405-427, the white box at y 484 is the recenter button) produced no confirm dialog and no round change. Cause NOT isolated (confounded: s135's 0x920434 /proc pokes, repeated gdb attach/detach, or a load artifact are all candidates). `SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch` restored the boundary immediately (m55_boundary fired, round 50->52).

INSTRUMENT DEFECT (why m85cens1/2/3 died): census's driver m44_idle asserts `TracerPid == 0` at entry — it cannot run under census's own gdb (m85cens4: driver rc=1 in 0 s, "AssertionError: tracer attached"); and its `--rounds 1` snapshot condition `y > last_year - 1 and not rounds` counts the CURRENT turn as a completed round, so it exits rc=0 in 0 s never having clicked. Census now drives with m55_boundary.py (no tracer assert, windowfocuses itself).

ACCEPTANCE PASS — `python3 scripts/m85_tech_census.py --tag m85cens5 --timeout 240` (ONE invocation): all six gates True; round 52->53, year 2152->2153 read back from /proc/201960/mem; EVENT COUNTS {ARMED:1, HELPER:1, ROUNDINC:1, STAGE:0, MP45E:0, H1:0, H2:0}; driver rc=0 "PASS boundary 2152->2153: player walk observed (cur_player [0,1,2,3,5,6,7])".

OUTCOME: (1) FUN_00521070 (MP 7-stage driver) never entered in a solo boundary — 0x52145e silence is BY DESIGN (G2/G3). (2) FUN_005a7970 IS entered once per boundary, eax=0, return site 0x569948 = inside FUN_0055f650 (0x55f650, 54483 B, call sites 0x50dd84/0x56cf12) — NOT the human-loop site 0x507e57 — so the M67 zeros at 0x5a7d00 (+912) / 0x5a7f67 (+1527) are UNTAKEN BRANCHES inside a live helper, not dead code (G4). (3) The round increment 0x51f320 fired once per boundary.

OPEN: which leg eax=0 takes inside FUN_005a7970 and what gates the two tails; who calls FUN_0055f650 at 0x50dd84 (round driver?); ds:0x920434 save_later-vs-NETGAME conflict still recorded (G6). NEXT pick: M86 — the helper's boundary visit: disassemble 0x5a7970 entry + the branches to 0x5a7d00/0x5a7f67, add a bp printing eax and the branch inputs, re-run census unchanged on a fresh-loaded box.
Evidence: evidence/m85cens5.gdblog (975 B), evidence/m85cens4.gdblog, scratch/m85cens5_bnd.jsonl; evidence 27.9 MB.
