# Session notes archive — sessions 239-239

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 239 (2026-11-10, ANALYSE, M292 5/5, BOX census) - pod MOVEMENT settled: the hub vector runs per-unit (arg1 = unit index) and dispatches on the m291 RING ENTRY INDEX esi - 0 = found (MSG 0x2408 if human-owned), 1-8 = continue w/o order, >=9 = issue order b (0x62) at the wrapped ring tile (the WALK); 9 FOUNDs / 26 turns, 2 walked pods
- track_mode ANALYSE -> the s238 pick. scripts/m292_pod_movement.py (static
  G1-G3 byte gates + live gdb census + parse + verdict). ACCEPTANCE:
  python3 scripts/m292_pod_movement.py --turns 26 -> PASS M292: 5/5
  (evidence/m292_pod_movement.txt + m292_gdb_raw.log; 2nd invocation - run 1
  at 12 turns scored 4/5 with only 1 FOUND, a window-length artifact not a
  refutation; floors never weakened).
- STATIC (bytes arbiter): hub 0x55f65c mov edi,[ebp+8] = unit index; 13u*4
  fold 0x55f6b8-0x55f6bf -> record 0x933278+52u (x@+0 y@+2 owner@+14); own
  flag = owner vs ds:0x91b5b4 (live value 3 = HUMAN fac). Exactly 2 call
  sites image-wide: 0x50dd84 (FUN_0050d140), 0x56cf12 (FUN_0056cdf0).
  Dispatch 0x563d46 test esi,esi (esi = ring entry): 0, not-own ->
  0x563d82-86 push u, call FUN_004cca50 (FOUND); 0, own -> push 0x2408,
  0x563d75 call FUN_00583fa0 (MSG); 1-8 -> 0x563e06 dec esi, no order;
  >=9 -> tables 0x678990/0x67850c[esi] + own tile, wrap FUN_00469010,
  0x563e3b call FUN_005560f0(u, 0x62, tile) = the walk order.
- LIVE (m54b_clean t0 continued, 26 turns 2150->2188): HUB=2308 (ret
  0x56cf17 x2282 per-unit + 0x50dd89 x26 once-round); DISP=29, st==8 on
  every row, ownflag==(ownrec==3) 29/29 (52u+14 owner arithmetic live);
  legs partition exactly: 9x esi=0 -> HUBFOUND, 9x esi 1-8, 11x esi>=9 ->
  ISS; FOUND=9 ALL ret=0x4ccbe2, cnt 18->27, every one paired
  same-segment with its HUBFOUND (x,y); WALK u=66 (53,47)->(53,49), u=60
  (27,51)->(1,43). FOUND facs {1,2,5,6,7}; golden tiles (20,48)(63,51)
  (1,43) reproduced; (27,29) taken by fac7 here (golden: fac1) - timelines
  diverged once run 1 founded (12,48) at t6.
- Box: pid 4087359 unchanged, TracerPid 0 pre/post, yama restored, no stale
  gdb. Evidence +92 KB (raw log 91,561 B), budget re-measured at close.
- OPEN (unchanged): 5a0aa0 bailing 3x; M247; M70 x2; 188-row cursor caller.
  NEW OPEN: who gates hub VISITS (FUN_0056cdf0/FUN_0050d140 entry tests)
  and the 0x56c6de continue-leg target. Next: ANALYSE - UNMODELED
  0x94e5a8/0x94eca8 per-site gate tables + FUN_004e3c00 no-go (static
  census + fit vs recorded sites); MSG-leg (human pod at best tile) never
  observed live. Next BUILD fire = B14.
