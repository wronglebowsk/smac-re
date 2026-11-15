# Session notes archive — sessions 243-243

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 243 (2026-11-10, BUILD B15, PASS 7/7, zero box contact) - gate tables 0x94e5a8/0x94eca8 NAMED; pod-scan price gate EXECUTABLE (sim/gatetables.py)

- ACCEPTANCE: `python3 -m sim.selftest --b15 programs/saves/m54b_clean.SAV` -> **PASS B15: 7/7**
  (`evidence/b15_gate_tables.txt:1`). Authority = RECORDED objdump windows `evidence/b15_gate_window.txt`
  (210 lines, 6 windows, terran.exe sha256 header; `scripts/b15_gate_window.py`).
- LAY CENSUS (`name_global.py --disp`, saved to evidence): `0x94e5a8 = site_score` byte x128 per
  faction block (blk+0x120): 99 refs / 24 funcs / 5 stores (M94 pair 0x556721/0x556b5a); FUN_0055f650
  22 refs 0 writes. `0x94eca8 = site_gate` byte x128 (blk+0x1860): 7 refs / 4 funcs, **0 direct
  stores** - the only writer is FUN_0051dcb0 (zero sweep 0x51dcd1/0x51dce7 + ADDRESS-COPIED store
  lea 0x51dfe2 -> `mov BYTE PTR [ecx],al` 0x51dff3; value source via 0x582cc0 OPEN). The bare-ds grep
  found 0/1 refs - the [reg+disp] scaling trap; `--disp` answers it.
- `ds:0x920434 = published_window_id`: name_global reconfirms M125 - 634 refs, exactly 15 stores
  (pcs == the M125 set, asserted in G2); solo live = 0 (M293 D1b); it is the msg gate at 0x55f6b0.
- GATE LAW executable, every branch byte-verified: argmax-skip; bypass `value >= 2*(8-dist)`;
  site_score==0 accept; `[blk+0x94e488]<2` accept; thr=(pod-region verdict==8)?1:4, max(site_gate);
  value>=thr accept; then skip legs `case!=8`, `byte[unit+0x11]==0x18`,
  `dword[0x989ce4+28*region] >= 6*(site_score+1)` (edx at 0x563c8e carries the dl from 0x563c3d -
  NOT a ring index).
- GATES: G1 73 pins == recorded window, table-swap rival 0; G2 census re-check vs shipped evidence;
  G3 closed form == recorded-byte INTERPRETER on 14,520 decision-grid cases; G4 the 4 rivals each
  disagree with the recorded bytes (81/146/236/2851); G5 27 recorded winner events modelled -
  24 bypass-accepted / 3 row-dependent (the exact print list for the box follow-up); G6 gated-scan ==
  podscan.scan_esi under permissive rows 7/7; G7 determinism, window sha256 685892fd4c2837df.
- THE INTERPRETER caught 2 real bugs pre-merge (the tiles ceiling is 6*(site_score+1) via the dl
  copy into edx; the unit byte is RAW ==0x18, not a bool) that a closed-form-only rung would have
  shipped - LAW: when the recorded bytes are window-able, grade the closed form against a byte
  interpreter, not only against events.
- Box: ZERO contact (build fire). Evidence +~10 KB. `evidence.py budget` at close under 60 k;
  NAMED.md 234.5 k (warn 250 k) - archive split stays a hygiene lead.
- OPEN/leads (recorded, not pursued): the al source for 0x51dff3 in FUN_0051dcb0; callers of
  FUN_0051dcb0 uncensused; the 0x94e5a8 readers in FUN_004f6030 (15 refs) / FUN_0050d140 0x50e4fb
  and the 0x564xxx-0x56c8xx band inside FUN_0055f650 uncensused; live table rows for the 3
  row-dependent winners -> the re-armed pod-walk census prints them (guard re-derivation law M293).
- GREPTILE ROUND 1 (#256, 2 P1 + 4 P2, ALL FIXED pre-merge): scan_esi_gated put UNIT_BASE in the
  [ebp-0x10] slot while the interpreter adds the absolute 0x933289 (double base - G6's permissive
  rows never reached that leg; a deep-leg row regime now walks FULL chain incl. unit+tiles before
  accept); scan_esi_gated silently needed acceptance() to pre-load the window (now lazy-loads
  evidence/b15_gate_window.txt); FAM_STRIDE published 0x8380 where the fold is DECIMAL 8380 =
  0x20BC; site_score blk-offset wording (0x94d448+0x1160, M92 view +0x120 from 0x94e488); the
  window recorder hashed terran.exe but trusted the text cache (now every window line's bytes are
  verified against the exe at the single anchor-derived VA->file delta -0x400000, ambiguous or
  missing -> refuse); G7's len==64 hash tautology replaced by a pinned digest (window sha256 now
  c1b3712b6be6f5d3). Re-run after fixes: PASS B15 7/7, 14,520-case grid green.
  Next: ANALYSE/box (pod-walk census re-arm); next BUILD = B16.
