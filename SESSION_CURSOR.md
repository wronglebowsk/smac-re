M78 | acceptance m78order2 RUNNING (scripts/m78_mark_clear.py --tag m78order2 --boundaries 4) |
merged? no | in flight: gdb attached to terran.exe, reload+enqueue+4 boundaries, ~4-6 min
| run 1 (tag m78order1) FAILED two gates for INSTRUMENT reasons, not engine reasons: (a) the driver's
census lines were written past gdb's lagging file offset and got overwritten (no BOUNDARY lines in
the log at all) — fixed by opening the log "aw"; (b) PRODFLAG/SWEEPCALL legitimately report array
indices 322-325 (owner 5, ret 0x574203 FUN_00573a90) which my tid<256 test rejected — now only
tracked tags (MARK/CLEAR/SET) must be in range.
| run 1 log evidence/m78order1.gdblog lines 86-94 ALREADY show the answer: PRODFLAG 194 -> SWEEPCALL
ret 0x4efe83 -> MARK 192/193 -> GATE l20=1 -> SWEEPIN -> CLEAR 192/193, ONE visit, no other marker.
| if cut off: read evidence/m78order2.gdblog (census lines are IN it as "BOUNDARY n ... carriers=");
next step is the closing order (SESSION_NOTES -> NAMED.md -> NEXT_PROMPT -> rsync skill -> commit ->
gate.py --base main -> milestone.py submit -> gh pr checks -> merge). Branch milestone/m78.
