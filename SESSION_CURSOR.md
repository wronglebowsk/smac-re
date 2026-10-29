M105 MERGED (s161, main cc20ae5, PR #112): m105s4 PASS 17/17 — the 1436-B record block is BUILT AT PROCESS START by FUN_005791c0 (count store reports 0x579b12); 0 events at the 8 M103 setup sites; 0 CNT stores in the load window, the -77 sentinel came back unlogged (that gap IS the next question).
NEXT = M106: the invisible load-window restore (maps before/after the load + strace mmap/process_vm_writev, or set can-use-hw-watchpoints 0).
acceptance: PASS 17/17 | merged: YES | next: python3 scripts/milestone.py start M106
