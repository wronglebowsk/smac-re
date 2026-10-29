# Session notes archive — sessions 139-139

Rotated out of `SESSION_NOTES.md` by `scripts/session_rotate.py` to keep the hot
file readable in one context window. Same evidence file paths apply.

## Session 139 (2026-10-28) — M88: the per-record slot IS written by FUN_005aa880 through a pointer; a mnemonic grep and a store-list census both miss it (m88slot6 PASS 7/7)

Same Hermes session as s138 (M86/M87) continued; branch milestone/m88, commits 0cef077 -> 554deab -> cb25a0d -> e8e900b -> da4de47.

ACCEPTANCE `python3 scripts/m88_slot_watch.py --tag m88slot6 --poke-index 5 --rounds 4 --timeout 120` (ONE invocation): **VERDICT PASS 7/7** — poke slot(5)=0x957ba8 13 -> -1 (read back); STORE EVENTS on the watched address: n=1 val=-1 in FUN_005aaa20 (aaa20's own consumption, instruction 0x5aaac1 `c7 87 fc d7 94 00 ff...`), n=2 pc=**0x5aa9d3 `mov DWORD PTR [esi],ebx` in FUN_005aa880 val=36**; read-back slots(0..7)=[-1,44,13,32,5,36,32,48], final slot(5)=36 == the last attributed store's value; control watchpoint on the ROUND counter fired 4x, writer 0x51f53c `a3 fc 5a 98 00 mov ds:0x985afc,eax` in FUN_0051f320; AAA 4 hits, CALL 4 hits with kind==slot every time (idx 4 kind 3 slot 3 etc.); round 64->68.

HOW IT DIED BEFORE IT PASSED (three instrument defects, all mine, all fixed in place):
1. `m88slot1` (scripts/m88_slot_writer.py) enumerated writers by grepping the mnemonic text for `0x94d7fc` and got only the DIRECT forms (0x51038c, 0x59cfce, the -1 stores). The slot is also written through pointers built by `lea esi,[eax*4+0x94d7fc]` (0x5aa9c5 in FUN_005aa880, 0x52ae09 in FUN_0052a720 - a 4859-B field accessor with 64 callers) and stored as `mov [esi],ebx` — invisible to that grep. It poked slot(5) 8 -> -1 and read 13 back with ZERO events: outcome UNEXPLAINED. It also carried my second typo of the s138 session (0x5aacc1 for 0x5aaac1) and printed `$esi` at aaa20's entry, where esi is not arg0 yet (the load is at 0x5aaa25) - so it reported idx=41900 (= 5*8380, the caller's byte offset).
2. `m88slot2`/`m88slot3` armed `watch *(int *)0x957ba8` (and 0x94f8b8): gdb confirmed "Hardware watchpoint 4", CTRL fired, the value visibly changed - and zero events. `m88slot4` added a control watchpoint on ds:0x985afc and the mechanism fired there (writer 0x51f53c), so the watchpoints are NOT broken; what they miss is a write that happens while gdb is stopped between my poke and the game's next access - see 3.
3. `m88slot5` PASSed 6/7 and died only on my own G6, which demanded that aaa20 process THE POKED record in the window. aaa20 rotates records (slot2: 4, 6, 1; slot4: 3; slot5: none; slot6: 4 of them), so that was an assumption about the game, not a game requirement; G6 became the invariant that WAS observed - every CALL event has kind == the slot value it read (4/4 in slot2, 4/4 in slot6).

LIVE FACTS: the eight slots [0x94d7fc + idx*8380] right after a fresh m54b_clean load are [-1,3,8,22,49,8,5,48] - record 5 holds 8, which is the kind M86/M87 measured being handed to FUN_005a7970. A poke to -1 is refilled within one boundary by FUN_005aa880 (0x5aa9d3), and aaa20 stores -1 there itself at 0x5aaac1 just before it calls the helper. So the slot is a WORK ITEM ALLOCATION, not a constant: 45, 13, 36 were allocated in three consecutive windows.

OPEN (M89 pick): FUN_005aa880 has 4 callers - name them (containment of the call sites), and decide what the allocated value indexes (the 1436-byte record at 0x9275c4 + idx*1436 and the 3-entry table 0x93325c/68/74 with shorts 10/25/26 are the two candidates FUN_005a7970 reads). Evidence: evidence/m88slot1.gdblog ... m88slot6.gdblog; scratch/m88slot*.gdb.
