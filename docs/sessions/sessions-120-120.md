# Session notes archive — sessions 120-120

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 120 (2026-10-28) — M78: SAME-VISIT marks vs clears, and who else calls FUN_00572800/FUN_004ef380. ACCEPTANCE PASS (tag `m78order3`).

`python3 scripts/m78_mark_clear.py --tag m78order3 --boundaries 4 --no-reload` (state from
`SMAC_SAVE='m54b_clean.SAV' python3 scripts/m54a_load.py --relaunch`, round 50): enqueue 194 at
University Base idx 0, storage poked 200 read back 200, 12 silent breakpoints (FUNCIN 0x4ef6d0,
PRODFLAG 0x4efe60, L20FLAG 0x4efe6c, SWEEPCALL 0x572800, MARK 0x5729d5, GATE 0x4f0591, MARKSET
0x4f05bd, SWEEPIN 0x4f05e0, CLEAR 0x4ef398, UPKCLR 0x52145e, TECHSET 0x5a7d00/0x5a7f67) and the
per-boundary census APPENDED into the gdb log, so events and censuses share ONE ordered stream.
Baseline 192=0x001 193=0x041 194=0x041, carriers [].

**ORDERING (unit = VISIT, i.e. one entry of the production function).** visit 36: PRODFLAG tid=194
pre=0x41 -> L20FLAG edx=1 -> SWEEPCALL owner=3 tid=194 mode=0 ret=0x4efe83 -> MARK 192 (pre 0x001)
+ MARK 193 (pre 0x041) -> GATE l20=1 owner=3 rec=10088 (=194*52) -> SWEEPIN -> CLEAR 192 (pre 0x105)
+ CLEAR 193 (pre 0x145), all in the SAME visit. Cross-visit mark->clear pairs = [] and no later
caller re-marks, so H_ACROSS is RULED OUT and M77's paradox is a MEASUREMENT ARTIFACT: the census
that read 192=0x105 193=0x145 at boundary 1 sits BETWEEN the mark and the clear of visit 36 — the
driver reads /proc/pid/mem while the engine is stopped inside the production pass. g9 asserts that
every census which sees 0x100 is inside its tid's mark->clear pair; census 1 is the only one and it
is. Census replay exact at all 4 boundaries (carriers [] / [192,193] / [] / []), so the
instrumented writer set explains every 0x100 change; MARKSET 0, and 0x4ef5b3 / 0x52145e /
0x5a7d00 / 0x5a7f67 printed ZERO events (the upkeep and tech passes still never ran).

**CALLERS.** Static (instruction bytes): `call 0x572800` at 0x4394be (FUN_00438ad0), 0x4efe7e
(FUN_004ef6d0), 0x5741fe (FUN_00573a90), 0x5a7d0e + 0x5a7f75 (FUN_005a7970); `call 0x4ef380` at
0x4ef5ae (FUN_004ef540), 0x4f0626 (production inline), 0x521479 (FUN_00521070), 0x5a8568
(FUN_005a7970). Live here: SWEEPCALL rets {0x4efe83 x1 (tid 194), 0x574203 x4 = FUN_00573a90 on
array indices 324/325/385/387, other owners — those sweeps marked NOTHING}; CLEAR rets {0x4f062b
x2}. Every observed ret is a static call target (g2). Side fact: the production loop also fires
PRODFLAG/L20FLAG at indices 322/323, so it walks PAST the 256-record array the census covers.

**OPEN.** (a) what the >=256 indices are and what FUN_00573a90's sweep does for them; (b)
DAT_00920434 and DAT_00985b10 still unnamed (live 0 / 0x08 = owner 3; every GATE admitted, so the
0x4f05bd else-branch stayed dead); (c) when the upkeep/tech passes run at all. NEXT pick: M79 —
name those two globals and find what turns the MARKSET else-branch on.
Evidence: `evidence/m78order3.gdblog`, `evidence/m78order3_seq.jsonl`, traces `m78order3_r0..r3`;
failed instruments kept: `evidence/m78order1.gdblog` (census lines overwritten — a non-O_APPEND
log fd) and tag m78order2 (a quit prompt raised by an Escape on the bare map swallowed the enqueue).
